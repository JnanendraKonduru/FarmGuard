# ─── FarmGuard Configuration ─────────────────────────────────────────────────
import os
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

