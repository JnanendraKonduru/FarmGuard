# ─── FarmGuard Alert Handler ─────────────────────────────────────────────────
import requests
from alarm import send_alarm, send_phone_call, send_urgent_ping
import config
from datetime import datetime
import os

def send_telegram_message(text):
    """Sends a text message via Telegram bot"""
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram message sent!")
        else:
            print(f"❌ Telegram message failed: {response.text}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

def send_telegram_photo(snapshot_path, caption):
    """Sends a photo with caption via Telegram bot"""
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(snapshot_path, "rb") as photo:
            payload = {
                "chat_id": config.TELEGRAM_CHAT_ID,
                "caption": caption,
                "parse_mode": "HTML"
            }
            response = requests.post(url, data=payload, 
                                     files={"photo": photo}, timeout=10)
            if response.status_code == 200:
                print("✅ Telegram photo sent!")
            else:
                print(f"❌ Telegram photo failed: {response.text}")
    except Exception as e:
        print(f"❌ Telegram photo error: {e}")

def trigger_alert(label, confidence, snapshot_path):
    """Main alert function — called when detection happens"""
    time_now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    
    
    # Build alert message
    if label == "person":
        emoji = "🚨"
        threat = "INTRUDER DETECTED"
    else:
        emoji = "🐾"
        threat = f"ANIMAL DETECTED — {label.upper()}"

    message = (
        f"{emoji} <b>FarmGuard Alert</b>\n\n"
        f"⚠️ <b>{threat}</b>\n"
        f"🎯 Confidence: {round(confidence * 100)}%\n"
        f"🕐 Time: {time_now}\n\n"
        f"Check your field immediately!"
    )

    # Send photo + message + alarm
    send_telegram_photo(snapshot_path, message)

    from alarm import send_alarm 
    send_alarm()
    send_phone_call(label)
    send_urgent_ping()

    # In trigger_alert(), after send_telegram_photo():
    # If photo fails (e.g. file not saved yet), send text as backup
    if not os.path.exists(snapshot_path):
        send_telegram_message(message)