import os

import requests

TELEGRAM_TIMEOUT_SECONDS = 10


def send_telegram(message: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        requests.post(url, data={"chat_id": chat_id, "text": message}, timeout=TELEGRAM_TIMEOUT_SECONDS)
        print("[telegram] message sent")
    except Exception as exc:
        print(f"[telegram] error: {exc}")
