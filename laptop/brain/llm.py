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

    def decide(self, goal, perception, available_actions, history=None):
        """Fragt das LLM nach der nächsten Aktion.
        Gibt ein dict zurück wie {"name": "forward", "distance_cm": 30}.
        history = Liste bereits ausgeführter Aktionen für dieses Ziel.
        """
        system = (
            "Du steuerst einen Roboter-Rover. Du bekommst ein Ziel, eine Liste "
            "sichtbarer Objekte und bereits ausgeführte Aktionen. "
            "Wähle GENAU EINE nächste Aktion aus den erlaubten Aktionen. "
            "Wenn das Ziel erreicht ist, antworte mit {\"name\": \"done\"}. "
            "Antworte NUR mit JSON: {\"name\": ..., \"speed\": ..., \"duration_ms\": ...}."
        )
        history_part = ""
        if history:
            history_part = f"\nBereits ausgeführt: {json.dumps(history, ensure_ascii=False)}"
        user = (
            f"Ziel: {goal}\n"
            f"Sichtbare Objekte: {json.dumps(perception, ensure_ascii=False)}\n"
            f"Erlaubte Aktionen: {json.dumps(available_actions, ensure_ascii=False)}"
            f"{history_part}\n"
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
