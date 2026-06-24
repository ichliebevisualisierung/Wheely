"""
actions.py — Die erlaubten Aktionen des Agenten (Schicht 3).

Definiert, WAS der Agent tun darf. Das LLM wählt aus genau diesen Aktionen.
Klar begrenzte Liste = sicherer und vorhersehbarer.
"""

# Diese Liste bekommt das LLM beschrieben, daraus wählt es:
AVAILABLE_ACTIONS = {
    "forward":  "Fahre vorwärts. Parameter: distance_cm",
    "backward": "Fahre rückwärts. Parameter: distance_cm",
    "left":     "Drehe nach links. Parameter: distance_cm (Drehbogen)",
    "right":    "Drehe nach rechts. Parameter: distance_cm",
    "stop":     "Halte an.",
    "look":     "Mache ein Kamerabild und beschreibe, was zu sehen ist.",
    "done":     "Ziel erreicht — Aufgabe beenden.",
}


def execute(action, rover):
    """Führt eine vom LLM gewählte Aktion auf dem Rover aus.
    action = {"name": "forward", "distance_cm": 30}
    """
    name = action.get("name")
    dist = action.get("distance_cm")

    if name == "forward":
        return rover.forward(distance_cm=dist)
    if name == "backward":
        return rover.backward(distance_cm=dist)
    if name == "left":
        return rover.left(distance_cm=dist)
    if name == "right":
        return rover.right(distance_cm=dist)
    if name == "stop":
        return rover.stop()
    # "look" und "done" werden im Agent-Loop selbst behandelt
    return {"note": f"Aktion '{name}' wird im Loop behandelt"}
