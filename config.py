# ─── FarmGuard Configuration ─────────────────────────────────────────────────
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Camera settings
CAMERA_SOURCE = 0

# Detection settings
CONFIDENCE_THRESHOLD = 0.5
COOLDOWN_SECONDS = 60

# What to detect
ANIMAL_CLASSES = [
    "bird", "cat", "dog", "horse",
    "sheep", "cow", "elephant", "bear",
    "zebra", "giraffe"
]
INTRUDER_CLASS = "person"

# Snapshot folder
SNAPSHOT_DIR = "snapshots"

# Set True only for local desktop debugging with a monitor attached.
# Keep False for headless runs (Flask subprocess, Raspberry Pi later).
SHOW_PREVIEW_WINDOW = False

# ── Pull overrides from the dashboard's saved settings, if present ──────────
_SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_settings.json")
if os.path.exists(_SETTINGS_FILE):
    try:
        with open(_SETTINGS_FILE) as f:
            _s = json.load(f)

        _cam = _s.get("camera_source", CAMERA_SOURCE)
        # Webcam index comes through as a numeric string ("0") — keep it an int.
        CAMERA_SOURCE = int(_cam) if isinstance(_cam, str) and _cam.isdigit() else _cam

        CONFIDENCE_THRESHOLD = float(_s.get("confidence_threshold", CONFIDENCE_THRESHOLD))
        COOLDOWN_SECONDS = int(_s.get("alert_cooldown_minutes", COOLDOWN_SECONDS / 60)) * 60
    except Exception as e:
        print(f"⚠️ Could not read dashboard_settings.json, using config.py defaults: {e}")