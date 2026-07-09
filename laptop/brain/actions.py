"""
actions.py — Die erlaubten Aktionen des Agenten (Schicht 3).

Definiert, WAS der Agent tun darf. Das LLM wählt aus genau diesen Aktionen.
Klar begrenzte Liste = sicherer und vorhersehbarer.
"""

# ---------------------------------------------------------------------- #
#  Empfohlene Werte (empirisch am Rover ermittelt).
#  Werden ans LLM kommuniziert UND clampen dessen Antworten.
# ---------------------------------------------------------------------- #

# Speed
SPEED_MIN = 1000       # darunter laufen die Motoren nicht zuverlässig an
SPEED_NORMAL = 1500    # Standard-Empfehlung
SPEED_MAX = 2000       # Maximum

# Duration (ms) — Richtwerte für "wie lange fahren/drehen"
DURATION_SHORT = 300   # kurzer Ruck / kleines Stück
DURATION_NORMAL = 800  # normale Bewegung
DURATION_LONG = 2000   # längeres Fahren
DURATION_MIN = 100
DURATION_MAX = 5000

# Beschreibungstext für das LLM — direkt einbetten, damit es die
# konkreten Zahlen sieht statt abstrakter Grenzen.
_SPEED_HINT = (
    f"speed: {SPEED_MIN}-{SPEED_MAX}, Standard {SPEED_NORMAL} "
    f"(unter {SPEED_MIN} bewegen sich die Motoren nicht)"
)
_DURATION_HINT = (
    f"duration_ms: kurz={DURATION_SHORT}, normal={DURATION_NORMAL}, "
    f"lang={DURATION_LONG} (Bereich {DURATION_MIN}-{DURATION_MAX})"
)

AVAILABLE_ACTIONS = {
    "forward":   f"Fahre vorwärts. {_SPEED_HINT}. {_DURATION_HINT}",
    "backward":  f"Fahre rückwärts. {_SPEED_HINT}. {_DURATION_HINT}",
    "left":      f"Drehe nach links (auf der Stelle). {_SPEED_HINT}. {_DURATION_HINT}",
    "right":     f"Drehe nach rechts (auf der Stelle). {_SPEED_HINT}. {_DURATION_HINT}",
    "left_90":   "Drehe 90 Grad nach links (auf der Stelle) — vordefinierte Drehung.",
    "left_180":  "Drehe 180 Grad nach links (auf der Stelle) — vordefinierte Drehung.",
    "right_90":  "Drehe 90 Grad nach rechts (auf der Stelle) — vordefinierte Drehung.",
    "right_180": "Drehe 180 Grad nach rechts (auf der Stelle) — vordefinierte Drehung.",
    "stop":      "Halte an.",
    "look":      "Mache ein Kamerabild und beschreibe, was zu sehen ist.",
    "done":      "Ziel erreicht — Aufgabe beenden.",
}


# ---------------------------------------------------------------------- #
#  Hilfsfunktionen: Werte vom LLM defensiv absichern
# ---------------------------------------------------------------------- #
def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _sanitize_speed(value):
    """LLM-Wert in gültigen Bereich zwingen. None/ungültig -> Standard."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        return SPEED_NORMAL
    return _clamp(v, SPEED_MIN, SPEED_MAX)


def _sanitize_duration(value):
    """LLM-Wert in gültigen Bereich zwingen. None/ungültig -> Standard."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        return DURATION_NORMAL
    return _clamp(v, DURATION_MIN, DURATION_MAX)


# ---------------------------------------------------------------------- #
#  Dispatcher: LLM-Aktion -> Rover-Methode
# ---------------------------------------------------------------------- #
def execute(action, rover):
    """Führt eine vom LLM gewählte Aktion auf dem Rover aus.
    action = {"name": "forward", "speed": 1500, "duration_ms": 800}
    oder:    {"name": "right_90"} für vordefinierte Drehungen
    """
    name = action.get("name")
    raw_speed = action.get("speed")
    raw_duration = action.get("duration_ms")

    # Vordefinierte Drehungen — feste, kalibrierte Werte
    if name == "left_90":
        return rover.left(speed=2000, duration_ms=450)
    if name == "left_180":
        return rover.left(speed=2000, duration_ms=900)
    if name == "right_90":
        return rover.right(speed=2000, duration_ms=450)
    if name == "right_180":
        return rover.right(speed=2000, duration_ms=900)

    # Variable Bewegungen — Werte defensiv absichern
    if name in ("forward", "backward", "left", "right"):
        speed = _sanitize_speed(raw_speed)
        duration_ms = _sanitize_duration(raw_duration)

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
