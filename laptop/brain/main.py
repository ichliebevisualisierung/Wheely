"""
main.py — Der Agent-Loop (Schicht 3, Einstiegspunkt)

Verbindet alles: Chat-Eingabe -> Wahrnehmung -> LLM -> Aktion -> wiederholen.
Das ist der "Sense-Plan-Act"-Kern (Woche 2-3).

Start:  python -m brain.main
"""
import sys
import time

# Pfad-Setup, damit die Schwester-Ordner importierbar sind
sys.path.append("..")

from body.rover import Rover
from perception.perceiver import YoloPerceiver
from brain.llm import Brain
from brain.actions import AVAILABLE_ACTIONS, execute
import config


def run():
    rover = Rover(config.PI_IP, config.PI_PORT)
    if not rover.is_alive():
        print("Pi nicht erreichbar. Läuft api_server.py? Stimmt die IP in config.py?")
        return

    perceiver = YoloPerceiver(config.YOLO_MODEL, config.YOLO_MIN_CONFIDENCE)
    brain = Brain(config.LLM_MODEL)

    print("Rover bereit. Gib einen Befehl (z.B. 'finde die Flasche'), 'q' zum Beenden.")
    while True:
        goal = input("\nBefehl> ").strip()
        if goal.lower() in ("q", "quit", "exit"):
            rover.stop()
            break

        # --- Sense-Plan-Act-Schleife für dieses Ziel ---
        for step in range(15):  # max. 15 Schritte pro Befehl (Sicherheitsgrenze)
            # SENSE
            image = rover.get_camera_image()
            perception = perceiver.perceive(image)
            labels = [o["label"] for o in perception]
            print(f"  [sehe] {labels}")

            # Reflex: Hindernis sehr nah -> stoppen (Code, nicht LLM)
            if rover.get_distance() != -1 and rover.get_distance() < 15:
                print("  [reflex] Hindernis nah — stoppe")
                rover.stop()

            # PLAN
            action = brain.decide(goal, perception, AVAILABLE_ACTIONS)
            print(f"  [plan] {action}")

            if action.get("name") == "done":
                print("  [fertig] Ziel erreicht.")
                break

            # ACT
            execute(action, rover)
            time.sleep(0.3)
        else:
            print("  [stop] max. Schritte erreicht.")
            rover.stop()


if __name__ == "__main__":
    run()
