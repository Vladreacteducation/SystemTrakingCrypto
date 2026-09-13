import os

import requests

TELEGRAM_TIMEOUT_SECONDS = 10


def send_telegram(message: str) -> bool:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        response = requests.post(
            url, data={"chat_id": chat_id, "text": message}, timeout=TELEGRAM_TIMEOUT_SECONDS
        )
        payload = response.json()
        if not response.ok or not payload.get("ok"):
            print(f"[telegram] API rejected message: status={response.status_code} body={payload}")
            return False
        print("[telegram] message sent")
        return True
    except Exception as exc:
        print(f"[telegram] error: {exc}")
        return False
