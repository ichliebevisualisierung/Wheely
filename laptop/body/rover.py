#!/usr/bin/env python3
"""
rover.py — BRÜCKE (läuft auf dem Laptop)

Python-Schnittstelle zur HTTP-API des Pi. Der Agent ruft NUR diese Klasse auf
und muss nichts über HTTP/JSON wissen.

Beispiel:
    from body.rover import Rover
    rover = Rover("172.20.10.11")
    rover.forward(distance_cm=30)
    d = rover.get_distance()
    img = rover.get_camera_image()   # numpy BGR (für YOLO) oder None
"""

import requests
import numpy as np
import cv2
try:
    import config
    _MIN_SPEED = config.MIN_SPEED
    _MIN_DURATION_MS = config.MIN_DURATION_MS
    _MIN_TURN_SPEED = config.MIN_TURN_SPEED
    _MIN_TURN_DURATION_MS = config.MIN_TURN_DURATION_MS
except (ImportError, AttributeError):
    _MIN_SPEED = 500
    _MIN_DURATION_MS = 1000
    _MIN_TURN_SPEED = 700
    _MIN_TURN_DURATION_MS = 1500
#import numpy as np
#import cv2


class Rover:
    def __init__(self, ip, port=8080, timeout=5.0):
        self.base = f"http://{ip}:{port}"
        self.timeout = timeout

    # ---- Bewegung ---------------------------------------------------- #
    def _move(self, direction, distance_cm=None, speed=700, duration_ms=None):
        speed = max(speed, _MIN_SPEED)
        duration_ms = max(duration_ms if duration_ms is not None else 0, _MIN_DURATION_MS)
        payload = {"direction": direction, "speed": speed, "duration_ms": duration_ms}
        if distance_cm is not None:
            payload["distance_cm"] = distance_cm
        r = requests.post(f"{self.base}/move", json=payload, timeout=self.timeout)
        return r.json()

    def forward(self, distance_cm=None, speed=700, duration_ms=None):
        return self._move("forward", distance_cm, speed, duration_ms)

    def backward(self, distance_cm=None, speed=700, duration_ms=None):
        return self._move("backward", distance_cm, speed, duration_ms)

    def left(self, distance_cm=None, speed=700, duration_ms=None):
        speed = max(speed, _MIN_TURN_SPEED)
        duration_ms = max(duration_ms if duration_ms is not None else 0, _MIN_TURN_DURATION_MS)
        return self._move("left", distance_cm, speed, duration_ms)

    def right(self, distance_cm=None, speed=700, duration_ms=None):
        speed = max(speed, _MIN_TURN_SPEED)
        duration_ms = max(duration_ms if duration_ms is not None else 0, _MIN_TURN_DURATION_MS)
        return self._move("right", distance_cm, speed, duration_ms)

    def stop(self):
        try:
            r = requests.post(f"{self.base}/stop", timeout=2)
            return r.json()
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ---- Sensoren ---------------------------------------------------- #
    def get_distance(self):
        """Ultraschall-Abstand in cm (oder -1 bei Fehler)."""
        try:
            r = requests.get(f"{self.base}/distance", timeout=self.timeout)
            return r.json().get("distance_cm", -1)
        except Exception:
            return -1

    def get_line(self):
        """Infrarot-Linienfolger (Rohwerte)."""
        try:
            r = requests.get(f"{self.base}/line", timeout=self.timeout)
            return r.json()
        except Exception:
            return None

    # ---- Kamera ------------------------------------------------------ #
    def get_camera_image(self):
        """Holt EIN Kamerabild als numpy BGR-Array (für OpenCV/YOLO). None bei Fehler."""
        try:
            r = requests.get(f"{self.base}/camera", timeout=self.timeout)
            if r.status_code != 200:
                print("HTTP:", r.status_code)
                return None
            arr = np.frombuffer(r.content, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                print("OpenCV konnte das JPEG nicht dekodieren.")
                return None
            return img
        except Exception as e:
            print("Camera Exception:", e)
            return None

    # ---- Health ------------------------------------------------------ #
    def is_alive(self):
        try:
            r = requests.get(f"{self.base}/health", timeout=2.0)
            return r.json().get("ok", False)
        except Exception:
            return False


if __name__ == "__main__":
    import sys
    ip = sys.argv[1] if len(sys.argv) > 1 else "172.20.10.11"
    rover = Rover(ip)
    print("Pi erreichbar?", rover.is_alive())
    print("Abstand:", rover.get_distance(), "cm")
    img = rover.get_camera_image()
    if img is not None:
        # cv2.imwrite("test_frame.jpg", img)
        print("Bild gespeichert: test_frame.jpg", img.shape)
    else:
        print("kein Bild bekommen")
