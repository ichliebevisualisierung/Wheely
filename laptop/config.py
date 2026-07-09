"""Zentrale Einstellungen. Hier IP & Co. anpassen, nicht im Code verstreut."""

# IP des Raspberry Pi (im Hotspot/WLAN). Mit Advanced IP Scanner finden.
PI_IP = "192.168.137.69"
PI_PORT = 8080

# LLM (Uni-Zugang). base_url + key kommen aus der .env-Datei.
LLM_MODEL = "Mistral Small 3-2-24b Instruct KI:Inferenz.nrw"  # Beispiel — euer Uni-Modell eintragen
MISTRAL_VISION_MODEL= "Mistral Small 3-2-24b Instruct KI:Inferenz.nrw"
# YOLO
YOLO_MODEL = "yolov8n.pt"
YOLO_MIN_CONFIDENCE = 0.4

# Fahr-Kalibrierung (am Rover ausmessen!)
MS_PER_CM = 80

# Mindest-Fahrwerte geradeaus
MIN_SPEED = 500
MIN_DURATION_MS = 200

# Mindest-Drehwerte (höher, damit Kurven spürbar sind)
MIN_TURN_SPEED = 500
MIN_TURN_DURATION_MS = 200
