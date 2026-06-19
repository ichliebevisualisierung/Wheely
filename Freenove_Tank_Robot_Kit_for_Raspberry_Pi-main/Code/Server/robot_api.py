#!/usr/bin/env python3
import json
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from motor import tankMotor

HOST = "0.0.0.0"
PORT = 8080

# Sicherheitslimits
MIN_SPEED = 300
MAX_SPEED = 1200
MIN_DURATION_MS = 80
MAX_DURATION_MS = 1500

# Grobe Kalibrierung:
# Wie viele Millisekunden braucht der Rover ungefähr pro cm?
# Muss später getestet/angepasst werden.
MS_PER_CM = 80

hardware_lock = threading.Lock()


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
        "right_motor": right
    }


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
                        distance_cm=distance_cm
                    )

                self.send_json(200, {
                    "ok": True,
                    "result": result
                })

            except Exception as e:
                try:
                    stop_motors()
                except Exception:
                    pass

                self.send_json(400, {
                    "ok": False,
                    "error": str(e)
                })

            return

        if path == "/stop":
            try:
                with hardware_lock:
                    stop_motors()

                self.send_json(200, {
                    "ok": True,
                    "result": "stopped"
                })

            except Exception as e:
                self.send_json(500, {
                    "ok": False,
                    "error": str(e)
                })

            return

        self.send_json(404, {
            "ok": False,
            "error": "unknown endpoint"
        })


def main():
    print(f"Robot API läuft auf Port {PORT}")
    print("POST /move")
    print("POST /stop")
    print("Beenden mit Ctrl+C")

    server = ThreadingHTTPServer((HOST, PORT), RobotAPI)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stoppe API...")
        stop_motors()


if __name__ == "__main__":
    main()