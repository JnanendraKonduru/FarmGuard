# main.py
import cv2, os, time, json
from datetime import datetime
import config, camera, detector, database

os.makedirs(config.SNAPSHOT_DIR, exist_ok=True)
database.init_db()
detector.load_model()

cap = camera.get_camera()
if not cap:
    exit()

last_alert_time = {}  # label → last alert timestamp
TARGETS   = set(config.ANIMAL_CLASSES) | {config.INTRUDER_CLASS}
LIVE_PATH = os.path.join(config.SNAPSHOT_DIR, "live.jpg")  # dashboard reads this
PENDING_ALERT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "pending_alert.json"
)

def write_pending_alert(label, conf, snapshot_path):
    """Writes a pending alert for app.py's file-watcher to pick up and push via SSE."""
    payload = {
        "label": label,
        "confidence": round(conf, 3),
        "snapshot": os.path.basename(snapshot_path),
        "timestamp": datetime.now().isoformat(),
    }
    try:
        # write to a temp file then rename — avoids the watcher reading a half-written file
        tmp_path = PENDING_ALERT_PATH + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(payload, f)
        os.replace(tmp_path, PENDING_ALERT_PATH)
    except Exception as e:
        print(f"❌ Could not write pending alert: {e}")

print("🌾 FarmGuard is watching... Press Q to quit.")

while True:
    frame = camera.read_frame(cap)
    if frame is None:
        continue

    detections = detector.detect(frame)
    now = time.time()

    for label, conf, (x1, y1, x2, y2) in detections:
        if label not in TARGETS:
            continue

        # Draw bounding box
        color = (0, 0, 220) if label == "person" else (0, 200, 80)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{label} {conf:.0%}",
                    (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Cooldown check (per label)
        if now - last_alert_time.get(label, 0) < config.COOLDOWN_SECONDS:
            continue

        # Save detection snapshot
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(config.SNAPSHOT_DIR, f"{label}_{ts}.jpg")
        cv2.imwrite(path, frame)

        # Alert (browser-native, via pending_alert.json) + log
        write_pending_alert(label, conf, path)
        database.log_detection(label, conf, path)
        last_alert_time[label] = now

    # ── Write live frame for dashboard (every frame, no cooldown) ──
    ts_overlay = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    cv2.putText(frame, ts_overlay, (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 180), 2)
    cv2.putText(frame, "FarmGuard Live", (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 100), 1)
    cv2.imwrite(LIVE_PATH, frame)

    cv2.imshow("FarmGuard", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:
        break

camera.release_camera(cap)