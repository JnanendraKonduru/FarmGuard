# main.py
import cv2, os, time
from datetime import datetime
import config, camera, detector, alert, database

os.makedirs(config.SNAPSHOT_DIR, exist_ok=True)
database.init_db()
detector.load_model()

cap = camera.get_camera()
if not cap:
    exit()

last_alert_time = {}  # label → last alert timestamp
TARGETS = set(config.ANIMAL_CLASSES) | {config.INTRUDER_CLASS}

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

        # Draw box on frame
        color = (0, 0, 220) if label == "person" else (0, 200, 80)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{label} {conf:.0%}",
                    (x1, y1 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Cooldown check (per label)
        if now - last_alert_time.get(label, 0) < config.COOLDOWN_SECONDS:
            continue

        # Save snapshot
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(config.SNAPSHOT_DIR, f"{label}_{ts}.jpg")
        cv2.imwrite(path, frame)

        # Alert + log
        alert.trigger_alert(label, conf, path)
        database.log_detection(label, conf, path)
        last_alert_time[label] = now

    cv2.imshow("FarmGuard", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:  # Q or Escape
        break

camera.release_camera(cap)