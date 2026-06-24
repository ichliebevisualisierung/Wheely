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

    def decide(self, goal, perception, available_actions):
        """Fragt das LLM nach der nächsten Aktion.
        Gibt ein dict zurück wie {"name": "forward", "distance_cm": 30}.
        """
        system = (
            "Du steuerst einen Roboter-Rover. Du bekommst ein Ziel und eine Liste "
            "sichtbarer Objekte. Wähle GENAU EINE nächste Aktion aus den erlaubten "
            "Aktionen. Antworte NUR mit JSON: {\"name\": ..., \"distance_cm\": ...}."
        )
        user = (
            f"Ziel: {goal}\n"
            f"Sichtbare Objekte: {json.dumps(perception, ensure_ascii=False)}\n"
            f"Erlaubte Aktionen: {json.dumps(available_actions, ensure_ascii=False)}\n"
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
