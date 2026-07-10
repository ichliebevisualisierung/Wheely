"""
memory.py — Session-Memory für den Agenten.

Speichert nur die aktuelle Nutzeraufgabe / Programmsession.
Bei jedem neuen Goal wird die Datei neu angelegt.
"""

import json
from pathlib import Path


class SessionMemory:
    def __init__(self, path="data/session_memory.json", keep_last=20):
        self.path = Path(path)
        self.keep_last = keep_last
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Datei beim Programmstart initialisieren
        self.write_data({
            "goal": None,
            "plan": None,
            "events": []
        })

    def read_data(self):
        if not self.path.exists():
            return {
                "goal": None,
                "plan": None,
                "events": []
            }

        try:
            with self.path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "goal": None,
                "plan": None,
                "events": []
            }

    def write_data(self, data):
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def start_goal(self, goal):
        """
        Neue Nutzeraufgabe starten.
        Alte Events werden gelöscht, weil wir nur Memory für den aktuellen Prompt wollen.
        """
        self.write_data({
            "goal": goal,
            "plan": None,
            "events": []
        })

    def set_plan(self, plan):
        """Speichert den Startplan als Top-Level-Feld fuer das aktuelle Goal."""
        data = self.read_data()
        data["plan"] = plan
        self.write_data(data)
        return plan

    def remember(self, event):
        """
        Fügt ein Event zur aktuellen Goal-Session hinzu.
        Kein Timestamp, kein Goal pro Event — das Goal steht oben in der Datei.
        """
        data = self.read_data()
        events = data.get("events", [])
        events.append(event)
        data["events"] = events
        self.write_data(data)
        return event

    def recent(self):
        """Letzte keep_last Events für den Prompt."""
        data = self.read_data()
        return data.get("events", [])[-self.keep_last:]

    def prompt_context(self):
        """Kompakter Memory-Kontext für das LLM."""
        data = self.read_data()
        return {
            "goal": data.get("goal"),
            "plan": data.get("plan"),
            "recent_events": self.recent()
        }
