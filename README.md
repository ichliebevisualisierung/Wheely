# Autonomous Rover 🤖

KI-gestützter autonomer Rover auf Basis des Freenove Tank Robot Kits.
Der Rover navigiert selbstständig durch Räume, erkennt Objekte und findet sie auf Text-Befehl.

> **Architektur in einem Satz:** Der **Pi** ist der Körper (HTTP-API steuert Motoren,
> Kamera, Sensoren), der **Laptop** ist das Gehirn (Objekterkennung + LLM-Agent).
> Sie reden über HTTP/JSON.

---

## Schnellüberblick: Wer macht was?

```
┌──────────────────────────────────────────────────────────┐
│  laptop/brain/      GEHIRN — Agent-Loop, LLM, Karte       │  ← Schicht 3
├──────────────────────────────────────────────────────────┤
│  laptop/perception/ WAHRNEHMUNG — YOLO erkennt Objekte    │  ← Schicht 2
├──────────────────────────────────────────────────────────┤
│  laptop/body/       BRÜCKE — spricht mit der Pi-API       │  ← Client
└──────────────────────────────────────────────────────────┘
                          │ HTTP/JSON über WLAN
┌──────────────────────────────────────────────────────────┐
│  pi/                KÖRPER — HTTP-API, Hardware-Treiber   │  ← Schicht 1
└──────────────────────────────────────────────────────────┘
```

---

## Ordnerstruktur

| Ordner | Läuft auf | Inhalt |
|---|---|---|
| `pi/` | Raspberry Pi | HTTP-API-Server + Hardware-Treiber (Freenove) |
| `pi/hardware/` | Raspberry Pi | Freenoves Treiber-Dateien (motor, camera, ultrasonic …) |
| `laptop/body/` | Laptop | `rover.py` — Python-Brücke, ruft die Pi-API auf |
| `laptop/perception/` | Laptop | `perceiver.py` — YOLO-Objekterkennung (austauschbar) |
| `laptop/brain/` | Laptop | Agent-Loop, LLM-Anbindung, Karte, Wegfindung |
| `tests/` | Laptop/Pi | kleine Testskripte je Modul |
| `docs/` | — | Blueprint, Notizen |

---

## Setup-Kurzfassung

### Auf dem Pi (einmalig)
```bash
# Freenove-Treiber müssen vorhanden sein (sind sie schon, via setup.py)
cd pi
pip install flask picamera2   # falls noch nicht da
python api_server.py          # startet die HTTP-API auf Port 8080
```

### Auf dem Laptop (einmalig)
```bash
cd laptop
pip install -r requirements.txt
# IP des Pi in config.py eintragen, dann:
python -m brain.main
```

Details in `docs/PROJECT_BLUEPRINT.md` und `docs/SETUP.md`.

---

## Status / Roadmap

- [x] Hardware aufgebaut & Modultests bestanden
- [x] Architektur entschieden (HTTP/JSON, Option A)
- [ ] **Woche 1:** HTTP-API auf dem Pi (Bewegung + Kamera + Sensoren) + Laptop-Brücke
- [ ] **Woche 2:** YOLO-Wahrnehmung + LLM-Agent (erste Befehle)
- [ ] **Woche 3:** Karte + Wegfindung + Demo

---

## Team-Konventionen

- Jede Schicht hat eine **klare Schnittstelle** — andere Schichten rufen nur diese auf, nie interne Details.
- Hardware-Zugriff passiert **nur** auf dem Pi, **nur** über die API. Nie zwei Programme gleichzeitig auf die Motoren!
- Branch pro Feature, dann Merge-Request — niemand pusht direkt auf `main`.

## Zum Testen einer API auf dem Server:
1. In ...Code/Server:
python robot_api.py

 2. Auf persönlichem Laptop (powershell):
Invoke-RestMethod -Method Post `
  -Uri http://wheely.local:8080/move `
  -ContentType "application/json" `
  -Body '{"direction":"backward","speed":7000,"duration_ms":3000}'

This can also be tested with Postman or another request-App.

direction can be backward, forward, left, right.

Idea:
The Robot recieves API requests with things it should do.
In a next step these requests (forward, backward, usw...) should be executed by a LLM with a prompt. This can then run on the local laptop, instead of on the RaspberryPi.


