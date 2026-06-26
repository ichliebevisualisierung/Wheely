# Wheely — Projektfortschritt

---

## 26.06.2026 — Fortschritt Dokumentation



### API (`robot_api.py`)
- Neue Methode zum Auslesen von Kamerabildern hinzugefügt
- Min/Max-Werte für Speed und Duration angepasst
- Timeouts auf 5 Sekunden erhöht (für längere Bewegungen)

### Kamerasystem (`test_camera.py`)
- Laptop kann Bilder vom Pi abrufen und speichern
- **Nächster Schritt:** Bilder direkt an YOLO übergeben statt zu speichern

### KI-Agent Loop (`main.py`)
- YOLO-Features vorerst entfernt (noch nicht implementiert)
- LLM-Anbindung mit **Aktions-Loop** getestet
- **Nächste Schritte:**
  - YOLO-Objekterkennung integrieren
  - Sensordaten (Ultraschall, Infrarot) in Wahrnehmung einbinden

### Motorsteuerung & Drehungen
- Variable Speed/Duration für flexible Bewegungen
- **4 Preset-Drehungen hinzugefügt:**
  - `left_90` (600ms @ 2000 speed)
  - `left_180` (1100ms @ 2000 speed)
  - `right_90` (600ms @ 2000 speed)
  - `right_180` (1100ms @ 2000 speed)



###  Quick Start zum testen

#### Setup
1. `.env`-Datei erstellen und mit LLM-Credentials füllen
2. IP des Raspberry Pi überprüfen und in `config.py` eintragen

#### Starten
1. **Auf dem Pi:**
   ```bash
   cd ~/Freenove_Tank_Robot_Kit_for_Raspberry_Pi-main/Code/Server
   python api_server.py
   ```

2. **Auf dem Laptop:**
   ```bash
   cd laptop
   python -m brain.main
   ```

3. **Befehle eingeben:**
   ```
   Befehl> fahr gerade aus, dann rechts, dann vollgas und 180 drehen
   ```

### 🔄 Nächste Schritte

- [ ] YOLO-Integration in `perceiver.py` (kI geben)
- [ ] Sensordaten (Ultraschall, Infrarot) auslesen und KI geben
- [ ] Sensor-Feedback in Agent-Loop integrieren
- [ ] Weiterführender LLM-Prompt für Wahrnehmung optimieren 
