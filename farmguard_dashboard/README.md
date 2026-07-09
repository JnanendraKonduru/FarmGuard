# FarmGuard Web Dashboard

A dark-themed Flask web dashboard for the FarmGuard detection system.

## Features

| Tab | What it does |
|---|---|
| 📡 Live Feed | Streams camera in real-time with timestamp overlay |
| 🕒 History | Browse + filter all SQLite detection records, paginated |
| 📸 Snapshots | Gallery of saved detection images with lightbox |
| ⚙️ Settings | Change camera source, confidence, cooldowns, alert toggles |

## Setup

### 1. Copy into your FarmGuard project

Place the `dashboard/` folder inside your existing FarmGuard directory:

```
FarmGuard/
├── main.py
├── detector.py
├── alert.py
├── alarm.py
├── camera.py
├── database.py
├── config.py
├── .env
├── snapshots/
├── dashboard/          ← paste here
│   ├── app.py
│   ├── templates/
│   │   └── dashboard.html
│   ├── static/
│   │   ├── css/dashboard.css
│   │   └── js/dashboard.js
│   └── requirements.txt
└── README.md
```

### 2. Install dependencies

```bash
# Make sure your venv is active
venv\Scripts\activate

pip install flask flask-cors
```

(opencv-python and python-dotenv are already installed from FarmGuard)

### 3. Update the DB and snapshot paths in app.py

By default `app.py` looks for `detections.db` and `snapshots/` in **its own directory**.
If your database is one level up, change:

```python
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
DB_PATH      = os.path.join(BASE_DIR, "..", "detections.db")   # one level up
SNAPSHOTS_DIR = os.path.join(BASE_DIR, "..", "snapshots")
```

### 4. Run

```bash
cd dashboard
python app.py
```

Open **http://localhost:5000** in your browser.

You can run `main.py` (the detector) and `app.py` (the dashboard) **at the same time** in two terminals — they share the same SQLite database.

## Settings persistence

Settings changed via the dashboard are saved to `dashboard_settings.json`.
These are separate from your `.env` — they don't override secrets.

## Tips

- **Phone camera**: paste the IP Webcam app URL (e.g. `http://192.168.1.5:8080/video`) into Settings → Camera Source and save.
- **Port conflict**: change `port=5000` in `app.py` to any free port.
- **Production**: for a public-facing setup, run behind `gunicorn` + `nginx`.
