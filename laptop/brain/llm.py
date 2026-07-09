"""
llm.py — Die Denk-Schnittstelle (Schicht 3)

Methoden:
  make_plan()    — erstellt einen strategischen Plan
  revise_plan()  — überprüft/aktualisiert den Plan nach jedem look
  decide()       — wählt die nächste Aktion (folgt dem Plan Schritt für Schritt)
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

    # ------------------------------------------------------------------ #
    #  1. Plan erstellen
    # ------------------------------------------------------------------ #
    def make_plan(self, goal, available_actions, memory_context=None):
        system = (
            "Du steuerst einen autonomen Rover mit Kamera und Ultraschall "
            "in einem Innenraum. Du kannst dich NICHT umschauen ohne dich "
            "zu drehen — die Kamera zeigt nur geradeaus.\n\n"
            "WICHTIGE STRATEGIEN die du kennen musst:\n"
            "- Um etwas im Raum zu SUCHEN: erst 'look', dann systematisch "
            "drehen (right_90 + look, 4x = 360°-Scan). Erst NACHDEM du "
            "das Objekt gesehen hast, darfst du dich dorthin bewegen.\n"
            "- NIEMALS blind vorwärts fahren ohne vorher geschaut zu haben.\n"
            "- 'look' zeigt dir NUR was direkt vor dir ist. Um den ganzen "
            "Raum zu sehen, musst du dich drehen.\n"
            "- Ultraschall misst nur Distanz geradeaus, nicht was dort ist.\n\n"
            "Erstelle einen Plan in 3-7 nummerierten Schritten. "
            "Jeder Schritt muss eine konkrete Aktion sein, kein vager Text. "
            "Antworte NUR mit der nummerierten Liste."
        )

        memory_part = ""
        if memory_context:
            memory_part = (
                f"\nWas du aus früheren Schritten schon weißt: "
                f"{json.dumps(memory_context, ensure_ascii=False)}"
            )

        user = (
            f"Ziel: {goal}\n"
            f"Verfügbare Aktionen: {', '.join(available_actions.keys())}"
            f"{memory_part}\n"
            "Erstelle deinen Plan:"
        )
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()

    # ------------------------------------------------------------------ #
    #  2. Plan dynamisch überarbeiten
    # ------------------------------------------------------------------ #
    def revise_plan(self, goal, current_plan, perception, history):
        system = (
            "Du steuerst einen autonomen Rover. Du hast gerade geschaut "
            "und neue Informationen. Überprüfe ob dein Plan noch sinnvoll ist.\n\n"
            "REGELN:\n"
            "- Wenn du das gesuchte Objekt GESEHEN hast: Plan anpassen, "
            "damit du dich dorthin bewegst.\n"
            "- Wenn du es NICHT gesehen hast und noch nicht 360° gescannt "
            "hast: weiter drehen und schauen.\n"
            "- Wenn du 360° gescannt hast ohne Erfolg: vorwärts bewegen "
            "und erneut scannen.\n"
            "- NIEMALS blind vorwärts fahren wenn du das Ziel noch nicht "
            "gesehen hast.\n\n"
            "Antworte NUR mit dem aktualisierten Plan als nummerierte Liste."
        )
        user = (
            f"Ziel: {goal}\n"
            f"Aktueller Plan:\n{current_plan}\n\n"
            f"Was ich gerade sehe: {json.dumps(perception, ensure_ascii=False)}\n"
            f"Bereits ausgeführt: {json.dumps(history, ensure_ascii=False)}\n"
            "Gib den aktualisierten Plan zurück:"
        )
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.2,
        )
        return resp.choices[0].message.content.strip()

    # ------------------------------------------------------------------ #
    #  3. Nächste Aktion wählen
    # ------------------------------------------------------------------ #
    def decide(self, goal, perception, available_actions, history=None,
               memory_context=None, plan=None):
        system = (
            "Du steuerst einen Roboter-Rover. Du MUSST dem Plan folgen.\n\n"
            "STRIKTE REGELN:\n"
            "1. Arbeite den Plan Schritt für Schritt ab. Überspringe keine "
            "Schritte.\n"
            "2. Wenn der Plan sagt 'look': wähle 'look'. Nicht 'forward'.\n"
            "3. NIEMALS 'forward' wählen, wenn du das Zielobjekt nicht "
            "gesehen hast — erst scannen (look + drehen).\n"
            "4. Nach einem 'look' der nichts Relevantes zeigt: drehe dich "
            "(right_90) und schaue erneut.\n"
            "5. 'forward' NUR wenn du weißt was vor dir ist.\n"
            "6. Wenn das Ziel erreicht ist: {\"name\": \"done\"}.\n\n"
            "Antworte NUR mit JSON: {\"name\": ..., \"speed\": ..., \"duration_ms\": ...}."
        )

        plan_part = ""
        if plan:
            # Zähle wie viele Schritte schon ausgeführt wurden
            actions_done = len([h for h in (history or [])
                                if h.get("name") not in ("reflex_stop",)])
            plan_part = (
                f"\nDein Plan:\n{plan}\n"
                f"Du bist bei ungefähr Schritt {actions_done + 1}.\n"
            )

        history_part = ""
        if history:
            history_part = f"\nBereits ausgeführt: {json.dumps(history, ensure_ascii=False)}"

        memory_part = ""
        if memory_context:
            memory_part = f"\nSession-Memory: {json.dumps(memory_context, ensure_ascii=False)}"

        user = (
            f"Ziel: {goal}"
            f"{plan_part}\n"
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
        text = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"name": "stop", "error": "LLM-Antwort nicht lesbar", "raw": text}
