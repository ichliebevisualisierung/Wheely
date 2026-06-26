"""
actions.py — Die erlaubten Aktionen des Agenten (Schicht 3).

Definiert, WAS der Agent tun darf. Das LLM wählt aus genau diesen Aktionen.
Klar begrenzte Liste = sicherer und vorhersehbarer.
"""

# Diese Liste bekommt das LLM beschrieben, daraus wählt es:
# speed: 300 (langsam) – 2000 (max). duration_ms: 100 (kurz) – 5000 (lang).
AVAILABLE_ACTIONS = {
    "forward":  "Fahre vorwärts. Parameter: speed (300-2000), duration_ms (100-5000)",
    "backward": "Fahre rückwärts. Parameter: speed (300-2000), duration_ms (100-5000)",
    "left":     "Drehe nach links (auf der Stelle). Parameter: speed (300-2000), duration_ms (100-5000)",
    "right":    "Drehe nach rechts (auf der Stelle). Parameter: speed (300-2000), duration_ms (100-5000)",
    "left_90":  "Drehe 90 Grad nach links (auf der Stelle) — vordefiniert.",
    "left_180": "Drehe 180 Grad nach links (auf der Stelle) — vordefiniert.",
    "right_90": "Drehe 90 Grad nach rechts (auf der Stelle) — vordefiniert.",
    "right_180": "Drehe 180 Grad nach rechts (auf der Stelle) — vordefiniert.",
    "stop":     "Halte an.",
    "look":     "Mache ein Kamerabild und beschreibe, was zu sehen ist.",
    "done":     "Ziel erreicht — Aufgabe beenden.",
}


def execute(action, rover):
    """Führt eine vom LLM gewählte Aktion auf dem Rover aus."""

    name = action.get("name")
    speed = int(action.get("speed", 700))
    duration_ms = int(action.get("duration_ms", 500))

    speed = max(300, min(speed, 1200))
    duration_ms = max(100, min(duration_ms, 1500))

    # Vordefinierte Drehungen
    if name == "left_90":
        return rover.left(speed=1200, duration_ms=600)

    if name == "left_180":
        return rover.left(speed=1200, duration_ms=1100)

    if name == "right_90":
        return rover.right(speed=1200, duration_ms=600)

    if name == "right_180":
        return rover.right(speed=1200, duration_ms=1100)

    # Variable Bewegungen
    if name == "forward":
        return rover.forward(speed=speed, duration_ms=duration_ms)

    if name == "backward":
        return rover.backward(speed=speed, duration_ms=duration_ms)

    if name == "left":
        return rover.left(speed=speed, duration_ms=duration_ms)

    if name == "right":
        return rover.right(speed=speed, duration_ms=duration_ms)

    if name == "stop":
        return rover.stop()

    # Diese Aktionen behandelt main.py selbst
    if name in ("look", "done"):
        return {"note": f"Aktion '{name}' wird im Loop behandelt"}

    return {"error": f"Unbekannte Aktion: {name}"}
