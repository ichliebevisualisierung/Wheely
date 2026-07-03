"""Zentrale Einstellungen. Hier IP & Co. anpassen, nicht im Code verstreut."""

# Raspberry Pi
PI_IP = "172.20.10.10"
PI_PORT = 8080

# ---------------- LLM ----------------

LLM_MODEL_KI = "Mistral Small 3-2-24b Instruct KI:Inferenz.nrw"

# Standard-LLM
LLM_MODEL = LLM_MODEL_KI

# ---------------- Vision ----------------

VISION_MODE = "yolo"      # "yolo" oder "mistral"

YOLO_MODEL = "yolov8n.pt"
YOLO_MIN_CONFIDENCE = 0.4

MISTRAL_VISION_MODEL = "Mistral Small 3-2-24b Instruct KI:Inferenz.nrw"

# ---------------- Fahr-Kalibrierung ----------------

MS_PER_CM = 80

MIN_SPEED = 500
MIN_DURATION_MS = 200

MIN_TURN_SPEED = 500
MIN_TURN_DURATION_MS = 200