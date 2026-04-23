# ─── FarmGuard Database Handler ─────────────────────────────────────────────
import sqlite3
import os
from datetime import datetime

DB_PATH = "farmguard.db"

def init_db():
    """Creates the database and table if they don't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL,
            label       TEXT NOT NULL,
            confidence  REAL NOT NULL,
            snapshot    TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Database ready!")

def log_detection(label, confidence, snapshot_path):
    """Saves a detection event to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO detections (timestamp, label, confidence, snapshot)
        VALUES (?, ?, ?, ?)
    ''', (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        label,
        round(confidence, 3),
        snapshot_path
    ))
    conn.commit()
    conn.close()

def get_recent_detections(limit=10):
    """Returns the last N detections"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, label, confidence, snapshot
        FROM detections
        ORDER BY id DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows