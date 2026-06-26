import requests
import cv2
import numpy as np
from ultralytics import YOLO

URL = "http://wheely.local:8080/camera"

print("Lade YOLO-Modell...")
model = YOLO("yolov8n.pt")

print("Hole Bild vom Rover...")
response = requests.get(URL)
response.raise_for_status()

image_array = np.frombuffer(response.content, dtype=np.uint8)
image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

print("Erkenne Objekte...")
results = model(image)

for result in results:
    for box in result.boxes:
        cls_id = int(box.cls[0])
        label = model.names[cls_id]
        confidence = float(box.conf[0])
        print(f"{label}: {confidence:.2f}")

annotated = results[0].plot()
cv2.imwrite("yolo_result.jpg", annotated)

print("Fertig. Ergebnis gespeichert als yolo_result.jpg")