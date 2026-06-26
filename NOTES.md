# Wheely — Projektfortschritt

## 26.06.2026 — Fortschritt Dokumentation



### API (`robot_api.py`)
- Neue Methode zum Auslesen von Kamerabildern hinzugefügt
- Min/Max-Werte für Speed und Duration angepasst
- Timeouts auf 5 Sekunden erhöht (für längere Bewegungen)

### Kamerasystem (`test_camera.py`)
- Laptop kann Bilder vom Pi abrufen und speichern
- Bild wird über den API-Endpunkt `/camera` vom Raspberry Pi abgerufen
- Test erfolgreich: Bild wird als `camera_test.jpg` auf dem Laptop gespeichert

### YOLO
- YOLO (`yolov8n.pt`) auf dem Laptop installiert
- `test_yolo_camera.py` lädt ein Bild über die API (`/camera`)
- Das Bild wird direkt an YOLO übergeben
- YOLO erkennt Objekte und gibt diese mit Wahrscheinlichkeit im Terminal aus
- Das erkannte Bild wird als `yolo_result.jpg` gespeichert

**Nächster Schritt:** Die YOLO-Ergebnisse werden direkt an den KI-Agenten (LLM) übergeben, damit der Roboter auf Basis der Objekterkennung Entscheidungen treffen kann.


### KI-Agent Loop (`main.py`)
- YOLO-Features integriert
- LLM-Anbindung mit **Aktions-Loop** getestet
- Aktion `look` hinzugefügt
- Der Agent kann ein Kamerabild aufnehmen, mit YOLO analysieren und die erkannten Objekte als Text ausgeben
- Bilder werden als `camera_latest.jpg` und `camera_latest_yolo.jpg` gespeichert
- 
- **Nächste Schritte:**
  - Sensordaten (Ultraschall, Infrarot) in Wahrnehmung einbinden
  - YOLO-Ergebnisse als Wahrnehmung (`perception`) an das LLM übergeben
  - Eventuell Methode aus main woanders hin verschieben

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
   Befehl> mache ein Bild
   Befehl> mach ein Foto
   Befehl> was siehst du

### 🔄 Nächste Schritte

- [ ] YOLO-Integration in `perceiver.py` (kI geben)
- [ ] Sensordaten (Ultraschall, Infrarot) auslesen und KI geben
- [ ] Sensor-Feedback in Agent-Loop integrieren
- [ ] Weiterführender LLM-Prompt für Wahrnehmung optimieren 

