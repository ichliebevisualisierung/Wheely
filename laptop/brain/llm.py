"""
llm.py — Die Denk-Schnittstelle (Schicht 3, Woche 2)

Kapselt die LLM-Aufrufe. decide() bekommt Ziel + Wahrnehmung + Karte
und gibt die nächste Aktion als JSON zurück.

Austauschbar: heute Uni-Modell (OpenAI-kompatibel), später stärkeres Modell.
"""
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class Brain:
    def __init__(self, model):
        self.client = OpenAI(
            base_url=os.getenv("LLM_BASE_URL"),
            api_key=os.getenv("LLM_API_KEY"),
        )
        self.model = model

    def plan_goal(self, goal, available_actions, memory_context=None):
        """
        Fragt das LLM vor dem ersten Aktionsschritt nach einer groben Strategie.

        Dies ist nur Planung, keine auszufuehrende Aktion.
        """
        system = (
            "Du planst fuer einen Roboter-Rover. Erstelle vor dem Handeln einen kurzen "
            "Strategie-Hinweis, der die Chance auf Zielerreichung maximiert. "
            "Plane NICHT die konkreten naechsten Aktionen voraus und gib KEINE "
            "Sequenz aus Action-Namen wie look, right_90, forward aus. "
            "Beschreibe nur die Entscheidungslogik. Beispiel: Wenn etwas gesucht "
            "wird, erst lokal rundum in mehrere Richtungen schauen und drehen, "
            "auch hinter den Rover, bevor gefahren wird. "
            "Fuer feineres Suchen koennen 45-Grad-Drehungen sinnvoll sein. "
            "Ein Rundumblick besteht aus Paaren: ein Drehschritt, dann ein Bild. "
            "Dabei eine Drehrichtung beibehalten, bis der Rundumblick fertig ist. "
            "Ein kurzer Rundumblick ist bei Suchzielen wichtiger als Zeit sparen. "
            "Dies ist nur ein Plan, keine Aktion. "
            "Antworte NUR mit JSON: {\"strategy\": \"...\", \"rules\": [\"...\"]}."
        )

        memory_part = ""
        if memory_context:
            memory_part = f"\nSession-Memory: {json.dumps(memory_context, ensure_ascii=False)}"

        user = (
            f"Ziel: {goal}\n"
            f"Erlaubte Aktionen: {json.dumps(available_actions, ensure_ascii=False)}"
            f"{memory_part}\n"
            "Welche grobe Strategie/Logik ist sinnvoll?"
        )
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.2,
        )
        text = resp.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"error": "LLM-Plan nicht lesbar", "raw": text}

    def decide(self, goal, perception, available_actions, history=None, memory_context=None):
        """
        Fragt das LLM nach der nächsten Aktion.

        Rückgabe-Beispiel:
            {"name": "forward", "speed": 1200, "duration_ms": 800}

        history = Aktionen/Wahrnehmungen im aktuellen Ziel-Loop.
        memory_context = kompakter Kontext aus session_memory.json.
        """
        system = (
            "Du steuerst einen Roboter-Rover. Du bekommst ein Ziel, eine Liste "
            "sichtbarer Objekte und bereits ausgeführte Aktionen. "
            "Hoechste Prioritaet: Wenn das gesuchte Objekt in der aktuellen "
            "Wahrnehmung oder Bildbeschreibung sichtbar/erwaehnt ist, ist das "
            "Ziel erreicht. Dann antworte sofort mit {\"name\": \"done\"}; "
            "fahre oder drehe nicht weiter. Erkenne dabei auch Pluralformen und "
            "offensichtliche Tippfehler im Ziel. "
            "Nutze den gespeicherten Plan aus dem Session-Memory als Orientierung. "
            "Bei Suchzielen gilt: Fahre nicht nach nur einem Blick los. "
            "Pruefe am aktuellen Standort erst rundum: look, dann mit right_45/right_90 "
            "oder left_45/left_90 weiterdrehen, dann wieder look. Nutze bevorzugt die "
            "vordefinierten 45/90/180-Grad-Aktionen statt freiem left/right. "
            "Behalte fuer den Rundumblick eine Drehrichtung bei, statt links/rechts "
            "zu pendeln. "
            "Drehe nicht sofort wieder zurueck in die alte Richtung; decke neue "
            "Blickrichtungen ab, besonders auch hinter dem Rover. "
            "Mehrere Drehaktionen direkt hintereinander sind falsch. "
            "Wenn die letzte Aktion in der History left_45, right_45, left_90, "
            "right_90, left_180, right_180, left oder right war, muss deine "
            "naechste Antwort exakt {\"name\": \"look\"} sein. "
            "Wähle GENAU EINE nächste Aktion aus den erlaubten Aktionen. "
            "Wenn das Ziel erreicht ist, antworte mit {\"name\": \"done\"}. "
            "Antworte NUR mit JSON: {\"name\": ..., \"speed\": ..., \"duration_ms\": ...}."
        )
        history_part = ""
        if history:
            history_part = f"\nBereits im aktuellen Ziel-Loop ausgeführt: {json.dumps(history, ensure_ascii=False)}"

        memory_part = ""
        if memory_context:
            memory_part = f"\nSession-Memory: {json.dumps(memory_context, ensure_ascii=False)}"

        user = (
            f"Ziel: {goal}\n"
            f"Aktuelle Wahrnehmung: {json.dumps(perception, ensure_ascii=False)}\n"
            f"Erlaubte Aktionen: {json.dumps(available_actions, ensure_ascii=False)}"
            f"{history_part}"
            f"{memory_part}\n"
            "Welche Aktion als Nächstes?"
        )
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.2,
        )
        text = resp.choices[0].message.content.strip()
        # JSON aus der Antwort holen (robust gegen ```-Blöcke)
        text = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"name": "stop", "error": "LLM-Antwort nicht lesbar", "raw": text}

    def goal_reached(self, goal, perception):
        """
        Fragt das LLM fokussiert, ob die aktuelle Wahrnehmung das Ziel erfuellt.
        """
        system = (
            "Du entscheidest nur, ob ein Roboter-Ziel bereits erreicht ist. "
            "Wenn das Ziel ein Suchziel ist und das gesuchte Objekt in der "
            "aktuellen Wahrnehmung oder Bildbeschreibung sichtbar/erwaehnt ist, "
            "ist das Ziel erreicht. Beruecksichtige Pluralformen und offensichtliche "
            "Tippfehler im Ziel. "
            "Antworte NUR mit JSON: {\"done\": true/false, \"reason\": \"...\"}."
        )
        user = (
            f"Ziel: {goal}\n"
            f"Aktuelle Wahrnehmung: {json.dumps(perception, ensure_ascii=False)}\n"
            "Ist das Ziel erreicht?"
        )
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.0,
        )
        text = resp.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"done": False, "error": "LLM-Zielcheck nicht lesbar", "raw": text}
