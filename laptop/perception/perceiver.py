#!/usr/bin/env python3
"""
perceiver.py — WAHRNEHMUNG (Schicht 2, läuft auf dem Laptop)

Die austauschbare Schnittstelle zwischen "Sehen" und "Denken".
Heute: YOLO. Später kann hier ein Vision-LLM rein, ohne dass der Agent sich ändert.

Schnittstelle (das verspricht jedes Wahrnehmungs-Modul):
    perceive(image) -> list[DetectedObject]

DetectedObject = {
    "label": "bottle",      # was
    "x": 320,               # Bildmitte-x des Objekts (Pixel)
    "y": 200,               # Bildmitte-y
    "confidence": 0.87,     # wie sicher (0..1)
    "box": [x1, y1, x2, y2] # Begrenzungsrahmen
}
"""

from abc import ABC, abstractmethod


class Perceiver(ABC):
    """Basisklasse. Jede Wahrnehmung implementiert perceive()."""

    @abstractmethod
    def perceive(self, image):
        """image: numpy BGR -> Liste erkannter Objekte (siehe oben)."""
        ...


class YoloPerceiver(Perceiver):
    """Objekterkennung mit YOLO (ultralytics). Kostenlos, lokal."""

    def __init__(self, model_name="yolov8n.pt", min_confidence=0.4):
        # yolov8n = "nano" = das kleinste/schnellste Modell. Gut für den Start.
        from ultralytics import YOLO
        self.model = YOLO(model_name)
        self.min_confidence = min_confidence

    def perceive(self, image):
        if image is None:
            return []
        results = self.model(image, verbose=False)
        objects = []
        for r in results:
            for box in r.boxes:
                conf = float(box.conf[0])
                if conf < self.min_confidence:
                    continue
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]
                x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
                objects.append({
                    "label": label,
                    "x": (x1 + x2) / 2,
                    "y": (y1 + y2) / 2,
                    "confidence": conf,
                    "box": [x1, y1, x2, y2],
                })
        return objects


# --- Platzhalter für später: hier könnte ein Vision-LLM andocken ---------
# class VisionLLMPerceiver(Perceiver):
#     def perceive(self, image):
#         # Bild an Claude/GPT-4o schicken, Objektliste zurückbekommen
#         ...


if __name__ == "__main__":
    import sys, cv2
    p = YoloPerceiver()
    img = cv2.imread(sys.argv[1] if len(sys.argv) > 1 else "test_frame.jpg")
    for obj in p.perceive(img):
        print(f"{obj['label']:15s} conf={obj['confidence']:.2f} x={obj['x']:.0f}")
