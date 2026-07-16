"""
FarmGuard Web Dashboard — Flask Backend
Run with: python app.py  (this also starts the detector automatically)
Requires: pip install flask flask-cors opencv-python
"""

from flask import Flask, render_template, jsonify, Response, request, send_from_directory
from flask_cors import CORS
import sqlite3
import os
import json
import time
import threading
import subprocess
import sys
import cv2
from datetime import datetime
from dotenv import load_dotenv
import numpy as np

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)
CORS(app)

# ─── Config ────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR      = os.path.join(BASE_DIR, "..")          # D:\GIT\FarmGuard\
DB_PATH       = os.path.join(ROOT_DIR, "detections.db")
SNAPSHOTS_DIR = os.path.join(ROOT_DIR, "snapshots")
LIVE_FRAME    = os.path.join(ROOT_DIR, "snapshots", "live.jpg")   # written by main.py
SETTINGS_FILE = os.path.join(BASE_DIR, "dashboard_settings.json")
MAIN_PY       = os.path.join(ROOT_DIR, "main.py")

os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

DEFAULT_SETTINGS = {
    "camera_source": "0",
    "confidence_threshold": 0.5,
    "alert_cooldown_minutes": 2,
    "call_cooldown_minutes": 5,
    "telegram_alerts": True,
    "voice_calls": True,
    "sound_alarm": True,
    "detection_classes": ["person", "dog", "cat", "bird", "cow", "horse", "sheep"],
}

# ─── Settings helpers ──────────────────────────────────────────────────────────

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE) as f:
            saved = json.load(f)
            return {**DEFAULT_SETTINGS, **saved}
    return DEFAULT_SETTINGS.copy()

def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─── DB helpers ────────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS detections (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT    NOT NULL,
            label     TEXT    NOT NULL,
            confidence REAL   NOT NULL,
            snapshot  TEXT,
            alerted   INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    return conn

# ─── Live frame stream — reads live.jpg written by main.py ────────────────────

def generate_frames():
    """Stream live.jpg that main.py writes every frame. No camera conflict."""
    while True:
        if os.path.exists(LIVE_FRAME):
            try:
                with open(LIVE_FRAME, "rb") as f:
                    frame_bytes = f.read()
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
            except Exception:
                pass
        else:
            frame = np.zeros((360, 640, 3), dtype="uint8")
            cv2.putText(frame, "Waiting for detector...", (120, 180),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 200, 100), 2)
            placeholder = cv2.imencode(".jpg", frame)[1].tobytes()
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + placeholder + b"\r\n")
        time.sleep(1 / 20)  # ~20 fps

# ─── Launch main.py in background ─────────────────────────────────────────────

def run_detector():
    """Runs main.py as a subprocess. Output appears in the same terminal."""
    print("🌿 Starting FarmGuard detector (main.py)...")
    try:
        subprocess.run([sys.executable, MAIN_PY], cwd=ROOT_DIR)
    except Exception as e:
        print(f"❌ Detector error: {e}")

# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/api/detections")
def api_detections():
    page   = int(request.args.get("page", 1))
    limit  = int(request.args.get("limit", 50))
    label  = request.args.get("label", "")
    offset = (page - 1) * limit

    conn   = get_db()
    where  = "WHERE label LIKE ?" if label else ""
    params = [f"%{label}%"] if label else []

    rows = conn.execute(
        f"SELECT * FROM detections {where} ORDER BY id DESC LIMIT ? OFFSET ?",
        params + [limit, offset]
    ).fetchall()
    total = conn.execute(
        f"SELECT COUNT(*) FROM detections {where}", params
    ).fetchone()[0]
    conn.close()

    return jsonify({"total": total, "page": page, "data": [dict(r) for r in rows]})

@app.route("/api/stats")
def api_stats():
    conn      = get_db()
    total     = conn.execute("SELECT COUNT(*) FROM detections").fetchone()[0]
    today_str = datetime.now().strftime("%Y-%m-%d")
    today     = conn.execute(
        "SELECT COUNT(*) FROM detections WHERE timestamp LIKE ?", (f"{today_str}%",)
    ).fetchone()[0]
    alerted   = conn.execute("SELECT COUNT(*) FROM detections WHERE alerted=1").fetchone()[0]
    labels    = conn.execute(
        "SELECT label, COUNT(*) as cnt FROM detections GROUP BY label ORDER BY cnt DESC LIMIT 5"
    ).fetchall()
    recent    = conn.execute(
        "SELECT timestamp FROM detections ORDER BY id DESC LIMIT 1"
    ).fetchone()
    conn.close()

    return jsonify({
        "total_detections": total,
        "today_detections": today,
        "alerts_sent":      alerted,
        "top_threats":      [{"label": r["label"], "count": r["cnt"]} for r in labels],
        "last_detection":   recent["timestamp"] if recent else None,
    })

@app.route("/api/snapshots")
def api_snapshots():
    files = []
    if os.path.isdir(SNAPSHOTS_DIR):
        for fname in sorted(os.listdir(SNAPSHOTS_DIR), reverse=True):
            if fname.lower().endswith((".jpg", ".jpeg", ".png")) and fname != "live.jpg":
                files.append({
                    "filename": fname,
                    "url": f"/snapshots/{fname}",
                    "modified": os.path.getmtime(os.path.join(SNAPSHOTS_DIR, fname))
                })
    return jsonify({"snapshots": files[:100]})

@app.route("/snapshots/<path:filename>")
def serve_snapshot(filename):
    return send_from_directory(SNAPSHOTS_DIR, filename)

@app.route("/api/settings", methods=["GET"])
def get_settings():
    return jsonify(load_settings())

@app.route("/api/settings", methods=["POST"])
def update_settings():
    data    = request.get_json()
    current = load_settings()
    current.update(data)
    save_settings(current)
    return jsonify({"status": "ok", "settings": current})

@app.route("/api/clear_detections", methods=["POST"])
def clear_detections():
    conn = get_db()
    conn.execute("DELETE FROM detections")
    conn.commit()
    conn.close()
    return jsonify({"status": "cleared"})

# ─── Entry ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n🌿 FarmGuard Dashboard starting...")

    # Launch detector in background thread
    t = threading.Thread(target=run_detector, daemon=True)
    t.start()

    print("   Open: http://localhost:5000\n")
    # debug=False is required — debug mode forks the process and runs detector twice
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)