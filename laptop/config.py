"""Zentrale Einstellungen. Hier IP & Co. anpassen, nicht im Code verstreut."""

# IP des Raspberry Pi (im Hotspot/WLAN). Mit Advanced IP Scanner finden.
PI_IP = "172.20.10.11"
PI_PORT = 8080

# LLM (Uni-Zugang). base_url + key kommen aus der .env-Datei.
LLM_MODEL = "mistral-small-3.2-24b-instruct"  # Beispiel — euer Uni-Modell eintragen

# YOLO
YOLO_MODEL = "yolov8n.pt"
YOLO_MIN_CONFIDENCE = 0.4

# Fahr-Kalibrierung (am Rover ausmessen!)
MS_PER_CM = 80
