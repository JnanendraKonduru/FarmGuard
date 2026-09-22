# detector.py
from ultralytics import YOLO
import config
import os

model = None  # loaded once, reused

def load_model():
    global model
    weights_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "models", "farmguard_yolov8n.pt"
    )
    model = YOLO(weights_path)
    print(f"✅ Fine-tuned FarmGuard model loaded! Classes: {model.names}")

def detect(frame):
    """Run inference. Returns list of (label, confidence, bbox) tuples."""
    results = model(frame, verbose=False)
    detections = []
    for result in results:
        for box in result.boxes:
            conf  = float(box.conf[0])
            label = model.names[int(box.cls[0])]
            bbox  = list(map(int, box.xyxy[0]))  # [x1, y1, x2, y2]
            if conf >= config.CONFIDENCE_THRESHOLD:
                detections.append((label, conf, bbox))
    return detections
