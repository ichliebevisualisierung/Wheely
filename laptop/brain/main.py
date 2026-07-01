"""
main.py — Der Agent-Loop (Schicht 3, Einstiegspunkt)

Verbindet Körper (Rover), Augen (Perceiver) und Verstand (Brain) zu einem
agentischen Sense-Plan-Act-Loop.

Start:
    cd laptop
    python -m brain.main

Voraussetzung:
    Auf dem Pi läuft api_server.py.
    .env-Datei mit LLM_BASE_URL und LLM_API_KEY existiert.
"""

import sys
import time
from pathlib import Path

import cv2

# laptop/ in den Python-Pfad hängen, damit die Geschwister-Ordner importierbar sind
laptop_dir = Path(__file__).parent.parent
sys.path.insert(0, str(laptop_dir))

from body.rover import Rover
from perception.perceiver import YoloPerceiver
from brain.llm import Brain
from brain.actions import AVAILABLE_ACTIONS, execute
import config

# Ultraschall-Schwellenwert: ab hier greift der Reflex (in cm).
# Alles darunter = zu nah, sofort stoppen, nicht ans LLM delegieren.
OBSTACLE_THRESHOLD_CM = 30


# ---------------------------------------------------------------------- #
#  Hilfsfunktion: "look" — Bild + Wahrnehmung + Distanz + Debug-Speichern
# ---------------------------------------------------------------------- #
def do_look(rover, perceiver):
    """Macht ein Foto, lässt es durch YOLO laufen, liest Ultraschall,
    speichert Debug-Bilder.

    Gibt ein Tuple zurück: (objekte, distanz_cm)
    - objekte: Liste erkannter Objekte (Format aus Perceiver-Schnittstelle)
    - distanz_cm: Ultraschall-Abstand (oder -1 bei Fehler)
    """
    print("[look] Mache Bild...")
    image = rover.get_camera_image()
    distance = rover.get_distance()

    if distance >= 0:
        print(f"[look] Ultraschall: {distance} cm voraus")
    else:
        print("[look] Ultraschall: kein Messwert")

    if image is None:
        print("[look] Kein Bild bekommen — leere Wahrnehmung.")
        return [], distance

    cv2.imwrite("camera_latest.jpg", image)

    objects = perceiver.perceive(image)

    if not objects:
        print("[look] Ich sehe nichts eindeutig.")
    else:
        print("[look] Ich sehe:")
        for obj in objects:
            print(f"  - {obj['label']} (confidence {obj['confidence']:.2f})")

    # Optional: annotiertes Bild speichern (mit Boxen drumrum)
    try:
        annotated = image.copy()
        for obj in objects:
            x1, y1, x2, y2 = [int(v) for v in obj["box"]]
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(annotated, f"{obj['label']} {obj['confidence']:.2f}",
                        (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX,
                        0.5, (0, 255, 0), 1)
        cv2.imwrite("camera_latest_yolo.jpg", annotated)
    except Exception as e:
        print(f"[look] Annotierung fehlgeschlagen: {e}")

    return objects, distance


def build_perception_for_llm(objects, distance_cm):
    """Baut die Wahrnehmung zusammen, die ans LLM geht.

    Das LLM bekommt nicht nur die erkannten Objekte, sondern auch die
    Ultraschall-Distanz als Text — so kann es informierte Entscheidungen
    treffen (z.B. "Hindernis 12 cm voraus → erst drehen, dann fahren").
    """
    perception = []

    # Ultraschall-Info als eigener Eintrag
    if distance_cm >= 0:
        perception.append({
            "type": "ultrasonic",
            "info": f"Hindernis {distance_cm} cm voraus"
        })

    # Erkannte Objekte
    for obj in objects:
        perception.append({
            "type": "object",
            "label": obj["label"],
            "confidence": round(obj["confidence"], 2),
        })

    return perception


# ---------------------------------------------------------------------- #
#  Hauptschleife
# ---------------------------------------------------------------------- #
def run():
    rover = Rover(config.PI_IP, config.PI_PORT)
    perceiver = YoloPerceiver(config.YOLO_MODEL, config.YOLO_MIN_CONFIDENCE)
    brain = Brain(config.LLM_MODEL)

    print("Wheely KI-Agent gestartet.")
    print("Die KI wählt pro Schritt genau EINE Aktion aus actions.py.")
    print()
    print("Beispiele für Bewegung:")
    print("  fahr ein kleines stück vorwärts")
    print("  dreh dich nach links")
    print("  fahr zurück und stop")
    print()
    print("Beispiele für Wahrnehmung:")
    print("  was siehst du")
    print("  finde die flasche")
    print("  mach ein foto")
    print()
    print("Beenden mit q")

    while True:
        goal = input("\nBefehl> ").strip()
        if goal.lower() in ("q", "quit", "exit"):
            print("Stoppe Rover...")
            rover.stop()
            break
        if not goal:
            continue

        # Pro Befehl: frische Wahrnehmung & History, Sicherheitslimit für Schritte
        perception = []
        last_distance = -1
        history = []
        max_steps = 10
        print(f"[Ziel] {goal}")

        for step in range(max_steps):
            # ---- SENSE (Ultraschall, jeder Schritt) ---------------------
            # Billig (ein HTTP-Call, paar ms), gibt dem LLM ständige
            # Raumwahrnehmung — ohne dass jemand "schau" sagen muss.
            last_distance = rover.get_distance()
            if last_distance >= 0:
                # Distanz in die bestehende Wahrnehmung einpflegen/aktualisieren
                # (entferne alten Ultraschall-Eintrag, füge neuen hinzu)
                perception = [p for p in perception if p.get("type") != "ultrasonic"]
                perception.insert(0, {
                    "type": "ultrasonic",
                    "info": f"Hindernis {last_distance} cm voraus"
                })
                print(f"[sense] Ultraschall: {last_distance} cm")

            # ---- PLAN ---------------------------------------------------
            action = brain.decide(goal, perception, AVAILABLE_ACTIONS, history)
            print(f"[plan {step + 1}] {action}")

            # Sicherheitsnetz: unlesbare/fehlerhafte LLM-Antwort
            if action.get("error"):
                print("[error]", action)
                rover.stop()
                break

            name = action.get("name")

            # Ziel erreicht
            if name == "done":
                print("[fertig] Ziel erreicht.")
                break

            # ---- SENSE (look) ------------------------------------------
            if name == "look":
                objects, last_distance = do_look(rover, perceiver)
                perception = build_perception_for_llm(objects, last_distance)
                history.append({"name": "look",
                                "seen": [{"label": o["label"],
                                          "confidence": round(o["confidence"], 2)}
                                         for o in objects],
                                "distance_cm": last_distance})
                continue

            # ---- REFLEX: Hindernis-Check vor Vorwärtsbewegung ----------
            # Das ist harter Code, KEIN LLM-Aufruf — muss schnell gehen.
            if name in ("forward",):
                dist = rover.get_distance()
                if dist != -1 and dist < OBSTACLE_THRESHOLD_CM:
                    print(f"[reflex] Hindernis bei {dist} cm — zu nah! Stoppe.")
                    rover.stop()
                    # Dem LLM mitteilen, was passiert ist
                    history.append({
                        "name": "reflex_stop",
                        "reason": f"Hindernis bei {dist} cm erkannt, Vorwärtsbewegung abgebrochen"
                    })
                    # Wahrnehmung aktualisieren, damit LLM beim nächsten Plan Bescheid weiß
                    perception = build_perception_for_llm([], dist)
                    continue

            # ---- ACT ---------------------------------------------------
            try:
                result = execute(action, rover)
                print(f"[result] {result}")
                history.append(action)
            except Exception as e:
                print("[exception]", e)
                rover.stop()
                break

            time.sleep(0.3)
        else:
            print(f"[abbruch] Maximale Schritte ({max_steps}) erreicht.")
            rover.stop()


if __name__ == "__main__":
    run()
