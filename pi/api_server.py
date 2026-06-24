#!/usr/bin/env python3
"""
api_server.py — KÖRPER (läuft auf dem Raspberry Pi)

HTTP/JSON-API, die den Rover steuert. Baut auf der ursprünglichen Idee
des Teammitglieds (robot_api.py) auf und erweitert sie um Kamera und Sensoren,
sodass Freenoves server.py komplett wegfallen kann.

WICHTIG: Es darf immer nur DIESES Programm die Hardware steuern.
         Freenoves server.py NICHT gleichzeitig laufen lassen!

Endpunkte:
    POST /move      {"direction": "forward", "distance_cm": 30, "speed": 700}
    POST /stop      -> Motoren aus
    GET  /distance  -> {"distance_cm": 42.0}        (Ultraschall)
    GET  /line      -> {"left": 0, "middle": 1, "right": 0}  (Infrarot)
    GET  /camera     -> JPEG-Bild (single frame, für YOLO)
    GET  /health    -> {"ok": true}                 (Lebenszeichen)

Start auf dem Pi:
    pip install flask picamera2
    python api_server.py
"""

import time
import threading

from flask import Flask, request, jsonify, Response

# --- Freenove-Treiber (liegen in pi/hardware/, Klassennamen wie im Repo) ---
# Hinweis: Diese Imports funktionieren nur AUF dem Pi mit angeschlossener Hardware.
from hardware.motor import tankMotor
from hardware.ultrasonic import gpiozero_ultrasonic
from hardware.infrared import Infrared
from hardware.camera import Camera


# ---------------------------------------------------------------------- #
#  Konfiguration & Sicherheitslimits  (aus robot_api.py übernommen)
# ---------------------------------------------------------------------- #
HOST = "0.0.0.0"
PORT = 8080

MIN_SPEED = 300
MAX_SPEED = 1200
MIN_DURATION_MS = 80
MAX_DURATION_MS = 1500

# Grobe Kalibrierung — MUSS am echten Rover ausgemessen werden!
# "Wie viele Millisekunden fährt der Rover pro cm?"
MS_PER_CM = 80

# Ein Lock, damit nie zwei Befehle gleichzeitig die Hardware anfassen.
hardware_lock = threading.Lock()


# ---------------------------------------------------------------------- #
#  Hardware-Singletons
#  Wir erstellen jeden Treiber EINMAL und halten ihn offen, statt ihn
#  (wie im Prototyp) bei jedem Move neu zu erzeugen. Das ist schneller
#  und stabiler.
# ---------------------------------------------------------------------- #
motor = tankMotor()
ultrasonic = gpiozero_ultrasonic()
infrared = Infrared()
camera = Camera()
camera.start_stream()   # JPEG-Stream starten -> get_frame() liefert dann Bilder


# ---------------------------------------------------------------------- #
#  Hilfsfunktionen
# ---------------------------------------------------------------------- #
def clamp(value, lo, hi):
    return max(lo, min(hi, int(value)))


def motor_values(direction, speed):
    """Übersetzt Richtung + Tempo in (links, rechts) Kettenwerte."""
    if direction == "forward":
        return speed, speed
    if direction == "backward":
        return -speed, -speed
    if direction == "left":
        return -speed, speed
    if direction == "right":
        return speed, -speed
    raise ValueError("direction muss sein: forward, backward, left, right")


def stop_motors():
    motor.setMotorModel(0, 0)


def do_move(direction, speed=700, duration_ms=None, distance_cm=None):
    """Führt eine Bewegung aus. Zeit ODER Distanz (Distanz hat Vorrang)."""
    speed = clamp(speed, MIN_SPEED, MAX_SPEED)

    if duration_ms is None:
        if distance_cm is not None:
            duration_ms = int(float(distance_cm) * MS_PER_CM)
        else:
            duration_ms = 300
    duration_ms = clamp(duration_ms, MIN_DURATION_MS, MAX_DURATION_MS)

    left, right = motor_values(direction, speed)

    motor.setMotorModel(left, right)
    time.sleep(duration_ms / 1000)
    motor.setMotorModel(0, 0)

    return {
        "direction": direction,
        "speed": speed,
        "duration_ms": duration_ms,
        "left_motor": left,
        "right_motor": right,
    }


# ---------------------------------------------------------------------- #
#  Flask-App + Endpunkte
# ---------------------------------------------------------------------- #
app = Flask(__name__)


@app.post("/move")
def move_endpoint():
    body = request.get_json(silent=True) or {}
    direction = body.get("direction")
    speed = body.get("speed", 700)
    duration_ms = body.get("duration_ms")
    distance_cm = body.get("distance_cm")

    if direction not in ("forward", "backward", "left", "right"):
        return jsonify(ok=False, error="ungültige direction"), 400

    try:
        with hardware_lock:
            result = do_move(direction, speed, duration_ms, distance_cm)
        return jsonify(ok=True, result=result)
    except Exception as e:
        with hardware_lock:
            stop_motors()
        return jsonify(ok=False, error=str(e)), 400


@app.post("/stop")
def stop_endpoint():
    try:
        with hardware_lock:
            stop_motors()
        return jsonify(ok=True, result="stopped")
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


@app.get("/distance")
def distance_endpoint():
    """Ultraschall-Abstand in cm."""
    try:
        with hardware_lock:
            dist = ultrasonic.get_distance()
        return jsonify(ok=True, distance_cm=dist)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


@app.get("/line")
def line_endpoint():
    """Infrarot-Linienfolger: drei Sensoren (links, mitte, rechts).
    Hinweis: genaue Methode in infrared.py prüfen — ggf. anpassen."""
    try:
        with hardware_lock:
            # Annahme: Infrared hat eine read_all()-artige Methode.
            # MUSS am Rover gegen die echte infrared.py verifiziert werden.
            values = infrared.read_all() if hasattr(infrared, "read_all") else None
        return jsonify(ok=True, raw=values)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


@app.get("/camera")
def camera_endpoint():
    """Liefert EIN aktuelles JPEG-Bild — ideal für YOLO auf dem Laptop."""
    try:
        frame = camera.get_frame()   # JPEG-Bytes (aus camera.py)
        return Response(frame, mimetype="image/jpeg")
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


@app.get("/health")
def health_endpoint():
    return jsonify(ok=True, message="rover api up")


# ---------------------------------------------------------------------- #
#  Start
# ---------------------------------------------------------------------- #
def main():
    print(f"Rover-API läuft auf http://{HOST}:{PORT}")
    print("Endpunkte: POST /move, POST /stop, GET /distance, GET /line, GET /camera, GET /health")
    print("Beenden mit Ctrl+C")
    try:
        # threaded=True: mehrere Anfragen gleichzeitig (z.B. Kamera + Move)
        app.run(host=HOST, port=PORT, threaded=True)
    except KeyboardInterrupt:
        pass
    finally:
        print("Stoppe Rover, räume auf …")
        try:
            stop_motors()
            camera.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
