# FarmGuard

An AI-powered farm security system that detects intruders and animals in a live camera feed, confirms detections over multiple frames to suppress false positives, and pushes real-time alerts to a web dashboard.

Built as a capstone project, targeting deployment on a Raspberry Pi 4 with a PIR sensor and Pi Camera Module, with a laptop-webcam development setup for rapid iteration.

---

## What it does

- Watches a live camera feed and runs YOLOv8n object detection on every frame
- Filters detections down to a configurable set of classes relevant to farm security (people, dogs, cats, cattle, horses, sheep, birds, bears)
- Requires an object to be seen for **N consecutive frames** before it counts as a confirmed alert, which eliminates the single-frame flicker false positives that a naive "alert on any detection" approach produces (shadows, motion blur, momentary misclassification)
- Logs every confirmed detection to a local SQLite database
- Streams the live annotated feed and real-time alerts to a browser dashboard, with no page refresh needed
- Lets you tune confidence threshold, target classes, consecutive-frame requirement, and alert cooldown from the dashboard itself, with changes taking effect within one frame — no restart required

---

## Architecture

FarmGuard runs as **two independent processes** that never import from or call into each other directly:

```
┌─────────────────┐         ┌──────────────────┐
│    main.py       │         │      app.py       │
│                   │         │                    │
│  Camera capture   │  writes │  Flask dashboard   │
│  YOLOv8n inference│ ──────▶ │  MJPEG video feed   │
│  Temporal confirm │  files  │  SSE alert stream   │
│  DB logging       │         │  Settings API       │
└─────────────────┘         └──────────────────┘
        │                              │
        └──────────► detections.db ◄───┘
```

The only contact between them is:
1. `farmguard_dashboard/static/live.jpg` — the current annotated frame
2. `pending_alert.json` — the most recent confirmed alert
3. `detections.db` — the shared SQLite database
4. `dashboard_settings.json` — user-configured settings, written by the dashboard, read by the detection engine

This decoupling is deliberate, not incidental. `main.py` can crash, restart, or be swapped for a completely different detection backend, and `app.py` never needs to know — it only ever reads files and a database. It's also what makes the Raspberry Pi migration low-risk: only the camera-facing code needs to change, because nothing downstream talks to the camera or model directly.

### Why atomic file writes matter

Both `live.jpg` and `pending_alert.json` are written by one process while being continuously read by another, dozens of times a second. A naive `write()` directly to the final filename creates a race condition: the dashboard can read the file mid-write and get a truncated, corrupt JPEG or a half-written JSON payload. On a live video feed, this shows up as the browser's `<img>` tag failing to decode a frame and going blank — permanently, until the next full page reload, because most browsers don't retry a broken multipart stream frame.

The fix is to never write to the real filename directly:

```python
cv2.imwrite(LIVE_FRAME_TMP_PATH, frame)   # write to a temp file first
os.replace(LIVE_FRAME_TMP_PATH, LIVE_FRAME_PATH)  # atomic rename
```

`os.replace()` is atomic at the filesystem level on both POSIX and Windows — a reader opening `live.jpg` at any point in time gets either the complete old file or the complete new file, never a partial one.

**Windows-specific wrinkle:** `os.replace()` can raise `PermissionError` if another process (the Flask reader, or Windows Defender's real-time scanner) has the destination file open at that exact instant — a lock that doesn't exist on Linux/Mac. `main.py` wraps every atomic replace in a short retry loop to absorb these transient locks without crashing the detection loop.

### Temporal confirmation

Requiring `N` consecutive frames of the same class before firing an alert is a cheap, pre-fine-tuning fix for the most common source of false positives: a moving shadow or a leaf blowing across frame gets misclassified for one frame and then disappears. A real intruder or animal, by contrast, persists across many consecutive frames. This logic lives in `main.py`'s `TemporalConfirmer` class and is fully decoupled from the detection model itself — it would work identically regardless of which YOLO version is behind it.

### GPU / CPU auto-detection

`detector.py` checks `torch.cuda.is_available()` at startup and automatically targets CUDA with fp16 inference if a GPU is present, or falls back to CPU/fp32 otherwise. This means the exact same code runs unmodified on a development laptop with a discrete GPU and on a Raspberry Pi 4 with no GPU at all — the only difference is inference speed, not correctness or code path.

---

## Tech stack

| Component | Choice | Why |
|---|---|---|
| Detection model | YOLOv8n (Ultralytics) | Small enough for real-time inference on constrained hardware, well-documented, easy to fine-tune |
| Backend | Flask | Lightweight, sufficient for a local dashboard, easy SSE support |
| Camera capture | OpenCV | Standard for both USB webcams (dev) and eventual `picamera2` interop (Pi) |
| Live feed delivery | MJPEG over HTTP multipart | Works in a plain `<img>` tag with zero client-side JS, no WebSocket infrastructure needed |
| Real-time alerts | Server-Sent Events (SSE) | Simpler than WebSockets for one-directional server→browser push; native browser reconnect handling |
| Alert sound | Web Audio API (synthesized) | No external dependency, no audio file assets to manage |
| Database | SQLite | Zero-config, file-based, more than sufficient for this write volume |
| Settings persistence | JSON file | Simple, human-readable, no schema migration overhead for a handful of tunable values |

---

## Project structure

```
FarmGuard/
├── main.py              # Detection engine: camera + YOLO + temporal confirmation + DB logging
├── config.py             # All settings, paths, and the dashboard-settings loader
├── camera.py              # Webcam capture wrapper
├── detector.py             # YOLOv8n loading, inference, GPU/CPU targeting
├── database.py              # SQLite schema, insert, and query functions
├── requirements.txt           # Python dependencies
├── .gitignore                   # Excludes model weights, DB, runtime state, venv
├── yolov8n.pt                     # Model weights (gitignored, downloaded on first run)
└── farmguard_dashboard/
    ├── app.py             # Flask app: MJPEG feed, SSE alerts, settings/detections API
    ├── templates/
    │   └── dashboard.html  # Dashboard page
    └── static/
        ├── dashboard.css    # Styling
        └── dashboard.js       # SSE client, settings form, history polling
```

---

## Setup

### 1. Clone and create a virtual environment

```
git clone https://github.com/JnanendraKonduru/FarmGuard.git
cd FarmGuard
python -m venv venv
venv\Scripts\activate.bat        # Windows
source venv/bin/activate          # Linux/Mac
```

### 2. Install dependencies

```
pip install -r requirements.txt
```

This installs the CPU-only build of PyTorch by default. **If you have an NVIDIA GPU** and want GPU-accelerated inference, install the CUDA build instead:

```
pip uninstall torch torchvision torchaudio
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

`detector.py` automatically detects and uses the GPU if this is installed — no code changes needed.

### 3. Run both processes

The detection engine and the dashboard are independent processes and must both be running simultaneously, in separate terminals:

```
# Terminal 1
python main.py

# Terminal 2
python farmguard_dashboard/app.py
```

Then open `http://127.0.0.1:5000` in a browser.

---

## Roadmap

- **Fine-tuning**: custom-trained weights on farm-specific data (300–800 images, hard negatives for shadow false positives), labeled via Roboflow, trained on Colab
- **Raspberry Pi migration**: swap `camera.py` to use `picamera2` for the CSI camera module, add GPIO handling for the PIR sensor, switch to `opencv-python-headless`
- **Wokwi hardware simulation**: GPIO circuit (buzzer, LED, relay) simulating the physical alert path from detection to hardware output
- **Mobile app** (long-term): React Native app with Firebase Cloud Messaging replacing/supplementing the browser dashboard

---

## Known limitations

- Currently targets a single camera source; no multi-camera support
- Alert delivery is SSE to the dashboard only — no SMS/push notification integration yet
- Temporal confirmation reduces but doesn't eliminate false positives; fine-tuning on farm-specific data is the planned longer-term fix
- Not yet tested on Raspberry Pi hardware — camera and GPIO code for that target is still pending
