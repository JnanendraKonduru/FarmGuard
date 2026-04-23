# 🌾 FarmGuard
> AI-powered animal intrusion detection system for farmers


## What it does
Detects animals and intruders near farm fields using a live camera feed.
Sends instant alerts via Telegram message, alarm sound, and voice call
when a threat is detected. Built to solve real crop damage faced by
Indian farmers during harvest season.

## Alert System
- 📸 Telegram photo with bounding box snapshot
- 🔔 Loud alarm sound on phone  
- 📞 Voice call alert via CallMeBot
- 🚨 Rapid ping messages

## Tech Stack
- Python 3.11
- YOLOv8 (Ultralytics)
- OpenCV
- Telegram Bot API
- CallMeBot API
- SQLite

## Setup
```bash
git clone https://github.com/JnanendraKonduru/FarmGuard.git
cd FarmGuard
py -3.11 -m venv venv
venv\Scripts\activate
pip install ultralytics opencv-python requests python-telegram-bot python-dotenv
```
Create a `.env` file with your credentials:
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_USERNAME=your_username

Then run:
```bash
python main.py
```

## Author
[Jnanendra Konduru](https://JnanendraKonduru.github.io)
