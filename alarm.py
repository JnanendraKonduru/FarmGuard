# ─── FarmGuard Alarm Generator ───────────────────────────────────────────────
import requests
import config
import os

ALARM_FILE = "alarm.mp3"

def create_alarm():
    """Downloads a loud beep alarm file if it doesn't exist"""
    if not os.path.exists(ALARM_FILE):
        # Download a free alarm beep sound
        url = "https://www.soundjay.com/buttons/sounds/beep-07.mp3"
        try:
            response = requests.get(url, timeout=10)
            with open(ALARM_FILE, "wb") as f:
                f.write(response.content)
            print("✅ Alarm sound ready!")
        except Exception as e:
            print(f"❌ Could not download alarm: {e}")

def send_alarm():
    """Sends alarm audio to Telegram — plays loudly on phone"""
    if not os.path.exists(ALARM_FILE):
        create_alarm()

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendAudio"
    try:
        with open(ALARM_FILE, "rb") as audio:
            payload = {
                "chat_id": config.TELEGRAM_CHAT_ID,
                "title": "🚨 FARMGUARD ALARM",
                "performer": "FarmGuard Security"
            }
            response = requests.post(url, data=payload,
                                     files={"audio": audio}, timeout=10)
            if response.status_code == 200:
                print("🔔 Alarm sent to phone!")
            else:
                print(f"❌ Alarm failed: {response.text}")
    except Exception as e:
        print(f"❌ Alarm error: {e}")