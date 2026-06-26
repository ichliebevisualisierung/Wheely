"""
main.py — Minimaler KI-Agent ohne Kamera/Feedback.

Start:
    cd laptop
    python -m brain.main

Voraussetzung:
    Auf dem Pi läuft:
    sudo python3 robot_api.py
"""

import sys
import time
from pathlib import Path
import requests
import cv2
import numpy as np

# Add laptop directory to path
laptop_dir = Path(__file__).parent.parent
sys.path.insert(0, str(laptop_dir))

from ultralytics import YOLO
from body.rover import Rover
from brain.llm import Brain
from brain.actions import AVAILABLE_ACTIONS, execute
import config

yolo_model = YOLO("yolov8n.pt")
def take_picture_and_analyze():
    url = f"http://{config.PI_IP}:{config.PI_PORT}/camera"

    print("[look] Mache Bild...")
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    with open("camera_latest.jpg", "wb") as f:
        f.write(response.content)

    image_array = np.frombuffer(response.content, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    results = yolo_model(image, verbose=False)

    seen = []

    for result in results:
        for box in result.boxes:
            confidence = float(box.conf[0])
            if confidence < 0.4:
                continue

            cls_id = int(box.cls[0])
            label = yolo_model.names[cls_id]
            seen.append((label, confidence))

    annotated = results[0].plot()
    cv2.imwrite("camera_latest_yolo.jpg", annotated)

    if not seen:
        print("[look] Ich sehe nichts eindeutig.")
    else:
        print("[look] Ich sehe:")
        for label, confidence in seen:
            print(f"  - {label} ({confidence:.2f})")

    print("[look] Originalbild: camera_latest.jpg")
    print("[look] YOLO-Bild: camera_latest_yolo.jpg")

    return seen

def run():
    rover = Rover(config.PI_IP, config.PI_PORT)
    brain = Brain(config.LLM_MODEL)

    print("Wheely KI-Agent gestartet.")
    print("Die KI wählt pro Befehl genau EINE Aktion aus actions.py.")
    print("Beispiele:")
    print("  fahr ein kleines stück vorwärts")
    print("  fahr zurück")
    print("  dreh dich nach links")
    print("  stop")
    print("Beispiele:")
    print("  mache ein Bild")
    print("  mach ein Foto")
    print("  starte die Kamera")
    print("  was siehst du")
    print("Beenden mit q")
    

    while True:
        goal = input("\nBefehl> ").strip()

        if goal.lower() in ("q", "quit", "exit"):
            print("Stoppe Rover...")
            print(rover.stop())
            break

        # Keine Wahrnehmung, weil Kamera/YOLO noch nicht aktiv sind
        # kommmt später noch dazu
        perception = []
        history = []
        max_steps = 10  # Sicherheitslimit

        print(f"[Ziel] {goal}")

        for step in range(max_steps):
            # PLAN: LLM wählt aus AVAILABLE_ACTIONS, kennt bisherige Schritte
            action = brain.decide(goal, perception, AVAILABLE_ACTIONS, history)
            print(f"[plan {step + 1}] {action}")

            # Safety: ungültige oder fehlerhafte LLM-Antwort
            if action.get("error"):
                print("[error]", action)
                rover.stop()
                break

            if action.get("name") == "done":
                print("[fertig] Ziel erreicht.")
                break
            if action.get("name") == "look":
                seen = take_picture_and_analyze()
                history.append({
                    "name": "look",
                    "seen": seen
                })
                break

            # ACT: vorhandene execute()-Funktion aus brain/actions.py nutzen
            try:
                result = execute(action, rover)
                print(f"[result] {result}")
                history.append(action)
                rover.stop()
            except Exception as e:
                print("[exception]", e)
                rover.stop()
                break

            time.sleep(0.3)
        else:
            print(f"[abbruch] Maximale Schritte ({max_steps}) erreicht.")


if __name__ == "__main__":
    run()