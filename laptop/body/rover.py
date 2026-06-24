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


class Rover:
    def __init__(self, ip, port=8080, timeout=5.0):
        self.base = f"http://{ip}:{port}"
        self.timeout = timeout

    # ---- Bewegung ---------------------------------------------------- #
    def _move(self, direction, distance_cm=None, speed=700, duration_ms=None):
        payload = {"direction": direction, "speed": speed}
        if distance_cm is not None:
            payload["distance_cm"] = distance_cm
        if duration_ms is not None:
            payload["duration_ms"] = duration_ms
        r = requests.post(f"{self.base}/move", json=payload, timeout=self.timeout)
        return r.json()

    def forward(self, distance_cm=None, speed=700, duration_ms=None):
        return self._move("forward", distance_cm, speed, duration_ms)

    def backward(self, distance_cm=None, speed=700, duration_ms=None):
        return self._move("backward", distance_cm, speed, duration_ms)

    def left(self, distance_cm=None, speed=700, duration_ms=None):
        return self._move("left", distance_cm, speed, duration_ms)

    def right(self, distance_cm=None, speed=700, duration_ms=None):
        return self._move("right", distance_cm, speed, duration_ms)

    def stop(self):
        r = requests.post(f"{self.base}/stop", timeout=self.timeout)
        return r.json()

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
                return None
            arr = np.frombuffer(r.content, dtype=np.uint8)
            return cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception:
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
        cv2.imwrite("test_frame.jpg", img)
        print("Bild gespeichert: test_frame.jpg", img.shape)
    else:
        print("kein Bild bekommen")
