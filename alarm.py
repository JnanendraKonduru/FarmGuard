# ─── FarmGuard Alarm Generator ───────────────────────────────────────────────
import requests
import config
import os
import time

_last_call_time = 0
CALL_COOLDOWN = 300  # only call once every 5 minutes

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

def send_phone_call(threat_label="animal"):
    """Makes your phone ring via CallMeBot Telegram call"""
    import urllib.parse

    username = os.getenv("TELEGRAM_USERNAME")

    if not username:
        print("❌ TELEGRAM_USERNAME missing in .env")
        return

    message = f"Alert from FarmGuard. {threat_label} detected near your farm field. Please check immediately."
    text = urllib.parse.quote(message)

    url = f"https://api.callmebot.com/start.php?source=web&user=@{username}&text={text}&lang=en-US-Standard-B"

    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            print("📞 Phone call triggered!")
        else:
            print(f"❌ Call failed: {response.text}")
    except Exception as e:
        print(f"❌ Call error: {e}")

def send_urgent_ping():
    """Sends 3 rapid Telegram pings to buzz the phone repeatedly"""
    import time
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    for i in range(3):
        payload = {
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": "🚨🚨🚨 FARMGUARD ALERT 🚨🚨🚨\n\nANIMAL/INTRUDER DETECTED!\nCHECK YOUR FIELD NOW!",
        }
        requests.post(url, data=payload, timeout=10)
        time.sleep(1)
    print("🚨 Urgent pings sent!")