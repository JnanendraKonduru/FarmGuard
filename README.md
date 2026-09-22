# 🌾 FarmGuard

**An AI-powered farm security system** that watches a live camera feed, detects intruders and animals with YOLOv8n, filters out false positives, logs every confirmed event, and streams everything to a live web dashboard — no page refresh required.

Built as a capstone project. Developed and tested on a laptop webcam, deployed for real-world use on a Raspberry Pi 4 with a Camera Module v2.

---

## ✨ What it does

- Watches a live camera feed and runs **YOLOv8n** object detection on every frame
- Filters detections down to farm-relevant classes — people, dogs, cats, cows, horses, sheep, and more, configurable from the dashboard
- Applies a **per-class alert cooldown** so the same animal or person lingering in frame doesn't spam repeated alerts
- Logs every confirmed detection (timestamp, label, confidence, snapshot) to a local **SQLite** database
- Saves an annotated snapshot image for every confirmed detection
- Streams the live annotated feed to a browser dashboard as MJPEG — works in a plain `<img>` tag, zero client-side video setup
- Dashboard polls the backend every few seconds for new detections, stats, and system status, so the UI stays current without manual refreshing
- Lets you tune camera source, confidence threshold, alert cooldowns, alert channels, and which classes trigger alerts — all from the dashboard, saved to a JSON file the detector re-reads on its next loop, so most changes apply without a restart

---

## 🖥️ Dashboard

A dark-themed, multi-page Flask dashboard:

| Page | What it shows |
|---|---|
| **Overview** | Live feed preview, key stats (total / today / alerts), recent detections, threat breakdown |
| **Live Camera** | Full-size live feed with a threat banner overlay, fullscreen toggle, today's stats and live event list |
| **Snapshots** | Searchable gallery of every saved detection image, with a lightbox viewer |
| **Analytics** | Full, paginated, filterable detection history table, top-threat breakdown, active-class legend |
| **Settings** | Camera source, confidence threshold, cooldowns, alert channel toggles, and per-class detection toggles |

---

## 🏗️ Architecture

FarmGuard runs as **two independent processes** that never import from or call into each other directly:

```
┌───────────────────┐                  ┌──────────────────────┐
│      main.py        │                  │        app.py         │
│                       │                  │                        │
│  Camera capture        │   writes files   │   Flask dashboard       │
│  YOLOv8n inference       │ ───────────────▶ │   MJPEG live feed         │
│  Cooldown-based alerts     │                  │   REST API (polled)        │
│  DB logging                  │                  │   Settings API                │
└───────────────────┘                  └──────────────────────┘
            │                                          │
            └────────────────▶ detections.db ◀─────────┘
```

The only contact between them is:

1. **`snapshots/live.jpg`** — the current annotated frame, written by `main.py`, streamed by `app.py`
2. **`detections.db`** — the shared SQLite database, written by `main.py`, read by `app.py`
3. **`dashboard_settings.json`** — user-configured settings, written by the dashboard, read by `config.py` on the detector's next loop

This decoupling is deliberate, not incidental. `main.py` can crash, restart, or be swapped for a completely different detection backend, and `app.py` never needs to know — it only ever reads files and a database. It's also what made the Raspberry Pi migration low-risk: only the camera-facing code needed to change, since nothing downstream talks to the camera or model directly.

### Why atomic file writes matter

`live.jpg` is written by one process while being continuously read by another, roughly 20 times a second. A naive `write()` straight to the final filename creates a race condition: the dashboard can read the file mid-write and get a truncated, corrupt JPEG. On a live feed, this shows up as the browser's `<img>` tag failing to decode a frame and going blank — permanently, until a full page reload.

The fix is to never write to the real filename directly:

```python
cv2.imwrite(tmp_path, frame)       # write to a temp file first
os.replace(tmp_path, LIVE_PATH)    # atomic rename
```

`os.replace()` is atomic at the filesystem level on both POSIX and Windows — a reader opening `live.jpg` at any point gets either the complete old file or the complete new file, never a partial one.

**Windows-specific wrinkle:** `os.replace()` can raise `PermissionError` if another process (the Flask reader, or an antivirus real-time scanner) has the destination file open at that exact instant — a transient lock that doesn't occur on Linux/Mac. Wrapping the replace in a short retry loop absorbs this without crashing the detection loop.

---

## 🧰 Tech stack

| Component | Choice | Why |
|---|---|---|
| Detection model | YOLOv8n (Ultralytics) | Small enough for real-time inference on constrained hardware, well-documented |
| Backend | Flask | Lightweight, sufficient for a local dashboard |
| Camera capture | OpenCV | Standard for USB webcams; swapped for `picamera2` on the Raspberry Pi build |
| Live feed delivery | MJPEG over HTTP multipart | Works in a plain `<img>` tag, no WebSocket infrastructure needed |
| Database | SQLite | Zero-config, file-based, more than sufficient for this write volume |
| Settings persistence | JSON file | Simple, human-readable, no schema migration overhead for a handful of tunable values |

---

## 📁 Project structure

```
FarmGuard/
├── main.py                        # Detection engine: camera capture + YOLO inference + cooldown alerts + DB logging
├── camera.py                       # Webcam/camera capture wrapper
├── detector.py                      # YOLOv8n loading and inference
├── database.py                       # SQLite schema, insert, and query functions
├── config.py                          # Settings, paths, and the dashboard-settings loader
├── requirements.txt                    # Python dependencies
├── .gitignore                           # Excludes model weights, DB, snapshots, venv, secrets
├── yolov8n.pt                            # Model weights (gitignored, downloaded on first run)
└── farmguard_dashboard/
    ├── app.py                              # Flask app: MJPEG feed, REST API, settings API
    ├── dashboard_settings.json               # Current dashboard-configured settings
    ├── templates/
    │   └── dashboard.html                      # Dashboard markup (multi-page SPA-style)
    └── static/
        ├── css/dashboard.css                     # Styling
        └── js/dashboard.js                         # Page routing, polling, settings form, charts
```

---

## ⚙️ Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/JnanendraKonduru/FarmGuard.git
cd FarmGuard
python -m venv venv
venv\Scripts\activate.bat        # Windows
source venv/bin/activate          # Linux/Mac
```

### 2. Install dependencies

```bash
pip install -r farmguard_dashboard/requirements.txt
```

This installs the CPU-only build of PyTorch by default. **If you have an NVIDIA GPU** and want GPU-accelerated inference, install the CUDA build instead:

```bash
pip uninstall torch torchvision torchaudio
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

Ultralytics automatically detects and uses a CUDA GPU when available and falls back to CPU otherwise — no code changes needed either way.

### 3. Run both processes

The detection engine and the dashboard are independent and must both be running, in separate terminals:

```bash
# Terminal 1
python main.py

# Terminal 2
python farmguard_dashboard/app.py
```

Then open **http://127.0.0.1:5000** in a browser.

> Tip: `app.py` can also launch `main.py` for you as a background subprocess — see the entry point at the bottom of `app.py`.

### 4. Phone camera (optional)

Install the **IP Webcam** app on an Android phone, then paste its stream URL (e.g. `http://192.168.1.5:8080/video`) into **Settings → Camera Source** on the dashboard and save.

---

## 🍓 Raspberry Pi deployment

FarmGuard is designed to run headless on a Raspberry Pi 4 with a Camera Module, with only the camera-facing code needing to change:

- Swap `camera.py`'s `cv2.VideoCapture` for `picamera2` to talk to the CSI camera module
- Use `opencv-python-headless` instead of `opencv-python` — no GUI backend needed on a headless device
- Install the CPU-only PyTorch build explicitly (`pip` defaults to a CUDA build on some platforms, which won't work on the Pi's ARM CPU)
- Run both processes inside `tmux` (or as systemd services) so they survive an SSH session dropping
- Access the dashboard from any device on the same network at `http://<pi-ip-address>:5000`

---

## 🗺️ Roadmap

- Fine-tune the detection model on farm-specific images for more reliable intruder and livestock detection
- Extend detection to additional livestock classes not covered by the stock COCO model (e.g. goats, pigs)
- Push-style alert delivery (SMS / mobile push) alongside the in-browser dashboard
- Multi-camera support

## ⚠️ Known limitations

- Currently targets a single camera source; no multi-camera support yet
- Alert delivery is limited to the browser dashboard — no SMS/push notification integration yet
- Cooldown-based deduplication reduces repeat alerts from a lingering subject but doesn't do frame-level false-positive suppression; further model fine-tuning is the planned fix for misclassifications
