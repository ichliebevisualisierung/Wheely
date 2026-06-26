
from body.rover import Rover
import config


def text_to_action(text):
    text = text.lower()

    if "vor" in text or "forward" in text:
        return {"direction": "forward", "speed": 1200, "duration_ms": 1000}

    if "zurück" in text or "back" in text:
        return {"direction": "backward", "speed": 1200, "duration_ms": 1000}

    if "links" in text or "left" in text:
        return {"direction": "left", "speed": 1200, "duration_ms": 700}

    if "rechts" in text or "right" in text:
        return {"direction": "right", "speed": 1200, "duration_ms": 700}

    return None


def run():
    rover = Rover(config.PI_IP, config.PI_PORT)

    print("Teste Verbindung zum Rover...")
    if not rover.is_alive():
        print("Pi nicht erreichbar. Läuft robot_api.py? Stimmt die IP in config.py?")
        return

    print("Rover bereit. Befehle: vor, zurück, links, rechts, q")

    while True:
        text = input("\nBefehl> ").strip()

        if text.lower() in ("q", "quit", "exit", "stop"):
            rover.stop()
            print("Beendet.")
            break

        action = text_to_action(text)

        if action is None:
            print("Befehl nicht verstanden.")
            continue

        print("Sende:", action)
        result = rover.move(**action)
        print("Antwort:", result)


if __name__ == "__main__":
    run()
    