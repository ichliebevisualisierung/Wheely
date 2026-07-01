# Wheely — Projektfortschritt & Dokumentation

---

## Aktueller Stand (29.06.2026)

**Der Rover ist voll funktionsfähig.** Bewegung, Kamera, Ultraschall, YOLO-Objekterkennung und LLM-Anbindung laufen. Der Agent nimmt Text-Befehle entgegen, erkennt Objekte per Kamera, misst Abstände per Ultraschall und navigiert selbstständig durch den Raum.

### Was funktioniert
- ✅ Bewegung (vorwärts, rückwärts, Drehungen inkl. Presets für 90°/180°)
- ✅ Kamera (JPEG-Bild über HTTP abrufbar, YOLO-Erkennung auf dem Laptop)
- ✅ Ultraschall (Distanzmessung, wird bei jedem Agent-Schritt gelesen)
- ✅ Ultraschall-Reflex (Hindernis < 15 cm → automatischer Stopp, ohne LLM)
- ✅ LLM-Agent-Loop (Sense-Plan-Act mit Uni-Modell über OpenAI-kompatible API)
- ✅ Saubere Repo-Struktur (pi/ für Rover, laptop/ für Gehirn, klare Schichten)

### Was noch offen ist
- [ ] Infrarot-Linienfolger ins LLM einbinden (Endpunkt `/line` existiert, Methode in `infrared.py` prüfen)
- [ ] MS_PER_CM kalibrieren (aktuell geschätzt: 80 — am Rover ausmessen!)
- [ ] Preset-Drehungen kalibrieren (90°/180° overshootet teilweise)
- [ ] YOLO-Erkennung verbessern (funktioniert, aber nicht optimal)
- [ ] Topologische Karte (`world_map.py`) real implementieren
- [ ] LLM-Prompt für Navigation weiter optimieren

---

## Quick Start — Rover starten und Befehle geben

### Voraussetzungen (einmalig)

**Auf dem Laptop:**
```bash
cd Wheely/laptop
pip install -r requirements.txt
```

**`.env`-Datei** in `Wheely/laptop/` erstellen (siehe `.env.example`):
```
LLM_BASE_URL=https://euer-uni-endpunkt/v1
LLM_API_KEY=euer-key
```

**`config.py`** prüfen — `PI_IP` muss die aktuelle IP des Pi sein (mit Advanced IP Scanner finden).

### Starten (jedes Mal)

**1. Pi — API-Server starten (per SSH oder Pi Connect):**
```bash
cd ~/Wheely/pi
sudo python3 api_server.py
```
Erwartete Ausgabe:
```
Robot API läuft auf Port 8080
Endpunkte: POST /move, POST /stop, GET /distance, GET /line, GET /camera, GET /health
```

**2. Laptop — Agent starten:**
```bash
cd Wheely/laptop
python -m brain.main
```

**3. Befehle eingeben:**
```
Befehl> was siehst du
Befehl> fahr ein kleines stück vorwärts
Befehl> dreh dich nach rechts
Befehl> finde die flasche
Befehl> schau dich um
Befehl> q                          (beenden)
```

### Häufige Probleme

| Problem | Lösung |
|---|---|
| `Connection timed out` | VPN aus? IP korrekt? Pi und Laptop im selben WLAN? |
| Rover bewegt sich nicht | `sudo` beim Starten von `api_server.py` vergessen? Speed zu niedrig (MIN_SPEED=1000)? |
| `Kein Bild bekommen` | Kamera-Kabel prüfen, `api_server.py` neu starten |
| `ModuleNotFoundError` | `pip install -r requirements.txt` auf dem Laptop, `sudo apt install python3-picamera2` auf dem Pi |
| VPN blockiert Verbindung | Cisco-Uni-VPN trennen — lokales Netz reicht |

---

## Was bisher gemacht wurde (chronologisch)

### Phase 1 — Hardware-Aufbau & Freenove-Tutorial
- Freenove Tank Robot Kit zusammengebaut (Board V2.0, RPi Zero 2 W)
- Raspberry Pi OS Lite (32-bit, headless) aufgesetzt
- Zugang per SSH und Pi Connect eingerichtet
- Freenove-Libraries installiert (setup.py, numpy, pip, setuptools)
- Alle Modultests bestanden: Motor, Servo/Greifarm, Ultraschall, Infrarot, Kamera
- Servo-Kalibrierung gelöst (servo.py auf 150°/90° → dann Klaue/Arm montieren)

### Phase 2 — Erste Eigenentwicklung (Team, vor Migration)
- **`robot_api.py`** geschrieben: eigener HTTP-Server statt Freenoves TCP-System
  - `POST /move` mit `distance_cm`-basiertem Fahren und Sicherheitslimits
  - `POST /stop`
  - `GET /camera` (Kamerabild als JPEG)
  - `GET /health`
- **Kamera-Test:** Laptop ruft erfolgreich Bilder über HTTP ab
- **YOLO:** `yolov8n.pt` auf dem Laptop, erkennt Objekte im Kamerabild
- **Agent-Loop:** LLM-Anbindung (Uni-Modell, OpenAI-kompatible API), Aktions-Loop
  - `look`-Aktion hinzugefügt
  - History-Tracking für LLM-Kontext
- **Motorsteuerung:** Preset-Drehungen kalibriert (90°/180° links/rechts)

### Phase 3 — Migration zur sauberen Repo-Struktur (29.06.2026)

**Architektur-Entscheidung:** Alles über eigene HTTP-API, Freenoves `server.py` fällt komplett weg. Freenoves Treiber-Dateien werden nur noch als Hardware-Abstraktionsschicht genutzt.

**Repo-Struktur eingeführt:**
```
Wheely/
├── pi/                          ← Raspberry Pi
│   ├── api_server.py            ← HTTP-API (Bewegung, Kamera, Sensoren)
│   └── hardware/                ← Freenove-Treiber (motor, camera, ultrasonic, infrared)
│
├── laptop/                      ← Laptop
│   ├── config.py                ← Zentrale Einstellungen (IP, Modelle, Limits)
│   ├── body/rover.py            ← Brücke zur Pi-API
│   ├── perception/perceiver.py  ← YOLO-Objekterkennung (austauschbar)
│   └── brain/                   ← Agent-Loop, LLM, Aktionen, Karte
│       ├── main.py              ← Einstiegspunkt, Sense-Plan-Act-Loop
│       ├── llm.py               ← LLM-Anbindung
│       ├── actions.py           ← Erlaubte Aktionen + Dispatcher
│       └── world_map.py         ← Topologische Karte (Stub, Woche 3)
```

**Konkrete Änderungen bei der Migration:**
- `api_server.py`: Sensor-Endpunkte `/distance` und `/line` ergänzt, Lazy-Singletons für Hardware
- Imports auf `from hardware.motor import tankMotor` etc. umgestellt + `__init__.py` in hardware/
- `main.py`: YOLO aus dem Agent rausgezogen in `perceiver.py` (saubere Schicht-Trennung)
- Bug gefixt: `look`-Aktion hatte `break` statt `continue` (Agent konnte nach Foto nicht weiterhandeln)
- Bug gefixt: `perception` war immer leer — LLM bekam nie YOLO-Ergebnisse
- Bug gefixt: Bilddekodierung in `rover.py` war auskommentiert
- MIN_SPEED auf 1000 gesetzt, DEFAULT_SPEED auf 1500 (Motoren liefen bei 700 nicht an)
- Ultraschall bei jedem Agent-Schritt gelesen (nicht nur bei `look`)
- Reflex-Stopp bei Hindernis < 15 cm (harter Code, kein LLM-Aufruf)

---

## Wichtige technische Details fürs Team

### Architektur in einem Satz
Der Pi ist der Körper (HTTP-API steuert Hardware), der Laptop ist das Gehirn (YOLO + LLM). Sie reden über HTTP/JSON im lokalen WLAN.

### Niemals vergessen
- **`sudo`** beim Starten von `api_server.py` — ohne Root-Rechte drehen die Motoren nicht
- **Nie zwei Programme gleichzeitig** auf dem Pi, die die Hardware steuern (kein Freenove `server.py` parallel!)
- **VPN aus** wenn ihr den Rover ansteuert — Cisco-VPN routet am lokalen Netz vorbei
- **Schnittstellen sind austauschbar:** `perceiver.py` kann später ein Vision-LLM statt YOLO nutzen, ohne dass der Agent sich ändert

### Motor-Kalibrierung (empirisch ermittelt)
- MIN_SPEED = 1000 (darunter laufen Motoren nicht zuverlässig an)
- DEFAULT_SPEED = 1500
- MAX_SPEED = 2000
- Preset-Drehungen: 90° = 600ms @ 2000, 180° = 1100ms @ 2000 (overshootet noch leicht)

### Ultraschall-Verhalten
- Wird bei JEDEM Agent-Schritt gelesen, nicht nur bei `look`
- Wert geht als `{"type": "ultrasonic", "info": "Hindernis XX cm voraus"}` ans LLM
- Reflex-Schwelle: 15 cm → automatischer Stopp bei `forward`, ohne LLM zu fragen