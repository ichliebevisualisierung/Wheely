#!/usr/bin/env python3
"""
api_server.py — KÖRPER (läuft auf dem Raspberry Pi)

HTTP/JSON-API, die den Rover steuert.
Basiert auf der robot_api.py des Teams, erweitert um Sensor-Endpunkte.

WICHTIG: Es darf immer nur DIESES Programm die Hardware steuern.
         Freenoves server.py NICHT gleichzeitig laufen lassen!

Endpunkte:
    POST /move       {"direction": "forward", "distance_cm": 30, "speed": 700}
                     oder: {"direction": "forward", "duration_ms": 500, "speed": 700}
    POST /stop       -> Motoren aus
    GET  /distance   -> {"ok": true, "distance_cm": 42.0}     (Ultraschall)
    GET  /line       -> {"ok": true, "raw": ...}              (Infrarot)
    GET  /camera     -> JPEG-Bild (single frame, für YOLO)
    GET  /health     -> {"ok": true}                          (Lebenszeichen)

Start auf dem Pi:
    python api_server.py
"""

import json
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

# Hardware-Treiber von Freenove (liegen in pi/hardware/ daneben)
from hardware.motor import tankMotor
from hardware.camera import Camera
from hardware.ultrasonic import gpiozero_ultrasonic
from hardware.infrared import Infrared


HOST = "0.0.0.0"
PORT = 8080

# Sicherheitslimits (am Rover empirisch ermittelt)
MIN_SPEED = 300
MAX_SPEED = 2000
MIN_DURATION_MS = 80
MAX_DURATION_MS = 5000

# Grobe Kalibrierung: wie viele Millisekunden pro cm?
# TODO: am echten Rover ausmessen und anpassen
MS_PER_CM = 80


# ---------------------------------------------------------------------- #
#  Hardware-Locks & Lazy-Singletons
#  (Kamera + Sensoren werden bei erstem Zugriff EINMAL erstellt)
# ---------------------------------------------------------------------- #
hardware_lock = threading.Lock()
camera_lock = threading.Lock()
sensor_lock = threading.Lock()

_camera = None
_ultrasonic = None
_infrared = None


def get_camera():
    global _camera
    if _camera is None:
        _camera = Camera()
        _camera.start_stream()
    return _camera


def get_ultrasonic():
    global _ultrasonic
    if _ultrasonic is None:
        _ultrasonic = gpiozero_ultrasonic()
    return _ultrasonic


def get_infrared():
    global _infrared
    if _infrared is None:
        _infrared = Infrared()
    return _infrared


# ---------------------------------------------------------------------- #
#  Hilfsfunktionen
# ---------------------------------------------------------------------- #
def clamp(value, min_value, max_value):
    value = int(value)
    return max(min_value, min(max_value, value))


def motor_values(direction, speed):
    if direction == "forward":
        return speed, speed
    if direction == "backward":
        return -speed, -speed
    if direction == "left":
        return -speed, speed
    if direction == "right":
        return speed, -speed
    raise ValueError("direction must be: forward, backward, left, right")


def stop_motors():
    motor = tankMotor()
    try:
        motor.setMotorModel(0, 0)
    finally:
        try:
            motor.close()
        except Exception:
            pass


def move(direction, speed=700, duration_ms=None, distance_cm=None):
    speed = clamp(speed, MIN_SPEED, MAX_SPEED)

    if duration_ms is None:
        if distance_cm is not None:
            duration_ms = int(float(distance_cm) * MS_PER_CM)
        else:
            duration_ms = 300

    duration_ms = clamp(duration_ms, MIN_DURATION_MS, MAX_DURATION_MS)

    left, right = motor_values(direction, speed)
    motor = tankMotor()

    try:
        motor.setMotorModel(left, right)
        time.sleep(duration_ms / 1000)
        motor.setMotorModel(0, 0)
    finally:
        try:
            motor.setMotorModel(0, 0)
            motor.close()
        except Exception:
            pass

    return {
        "direction": direction,
        "speed": speed,
        "duration_ms": duration_ms,
        "left_motor": left,
        "right_motor": right,
    }


# ---------------------------------------------------------------------- #
#  HTTP-Handler
# ---------------------------------------------------------------------- #
class RobotAPI(BaseHTTPRequestHandler):
    def send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    # ---- GET-Endpunkte ------------------------------------------------ #
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/health":
            self.send_json(200, {"ok": True})
            return

        if path == "/camera":
            try:
                with camera_lock:
                    frame = get_camera().get_frame()
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(frame)))
                self.end_headers()
                self.wfile.write(frame)
            except Exception as e:
                self.send_json(500, {"ok": False, "error": str(e)})
            return

        if path == "/distance":
            try:
                with sensor_lock:
                    dist = get_ultrasonic().get_distance()
                self.send_json(200, {"ok": True, "distance_cm": dist})
            except Exception as e:
                self.send_json(500, {"ok": False, "error": str(e)})
            return

        if path == "/line":
            try:
                with sensor_lock:
                    ir = get_infrared()
                    # TODO: Methodennamen an echte infrared.py anpassen
                    # Häufige Varianten: read_all(), read(), get_values()
                    if hasattr(ir, "read_all"):
                        raw = ir.read_all()
                    elif hasattr(ir, "read"):
                        raw = ir.read()
                    else:
                        raw = None
                self.send_json(200, {"ok": True, "raw": raw})
            except Exception as e:
                self.send_json(500, {"ok": False, "error": str(e)})
            return

        self.send_json(404, {"ok": False, "error": "unknown endpoint"})

    # ---- POST-Endpunkte ----------------------------------------------- #
    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/move":
            try:
                body = self.read_json()
                direction = body.get("direction")
                speed = body.get("speed", 700)
                duration_ms = body.get("duration_ms")
                distance_cm = body.get("distance_cm")

                with hardware_lock:
                    result = move(
                        direction=direction,
                        speed=speed,
                        duration_ms=duration_ms,
                        distance_cm=distance_cm,
                    )
                self.send_json(200, {"ok": True, "result": result})
            except Exception as e:
                try:
                    stop_motors()
                except Exception:
                    pass
                self.send_json(400, {"ok": False, "error": str(e)})
            return

        if path == "/stop":
            try:
                with hardware_lock:
                    stop_motors()
                self.send_json(200, {"ok": True, "result": "stopped"})
            except Exception as e:
                self.send_json(500, {"ok": False, "error": str(e)})
            return

        self.send_json(404, {"ok": False, "error": "unknown endpoint"})


# ---------------------------------------------------------------------- #
#  Start
# ---------------------------------------------------------------------- #
def main():
    print(f"Robot API läuft auf Port {PORT}")
    print("Endpunkte: POST /move, POST /stop,")
    print("           GET  /distance, GET /line, GET /camera, GET /health")
    print("Beenden mit Ctrl+C")

    server = ThreadingHTTPServer((HOST, PORT), RobotAPI)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stoppe API...")
        stop_motors()


if __name__ == "__main__":
    main()
