# Source https://raw.githubusercontent.com/unl1k3ly/AnchorHODL/main/send_notification.py

import os, requests, json
import distutils.util
from dotenv import load_dotenv

load_dotenv(override=True)


def slack_webhook(msg):
    slack_data = {
        "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": msg}}]
    }

    try:
        response = requests.post(
            os.getenv("SLACK_WEBHOOK_URL"),
            data=json.dumps(slack_data),
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        if response.status_code != 200:
            raise ValueError(
                "Request to slack returned an error %s, the response is:\n%s"
                % (response.status_code, response.text)
            )
    except Exception:
        pass


def telegram_notification(msg):
    tg_data = {
        "chat_id": str(os.getenv("TELEGRAM_CHAT_ID")),
        "text": msg,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(
            "https://api.telegram.org/bot"
            + os.getenv("TELEGRAM_TOKEN")
            + "/sendMessage",
            data=json.dumps(tg_data),
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        if response.status_code != 200:
            raise ValueError(
                "Request to slack returned an error %s, the response is:\n%s"
                % (response.status_code, response.text)
            )
    except Exception:
        pass


def notify(message: str):
    print(message)

    if bool(distutils.util.strtobool(os.getenv("NOTIFY_TELEGRAM"))):
        telegram_notification(message)
    if bool(distutils.util.strtobool(os.getenv("NOTIFY_SLACK"))):
        slack_webhook(message)


def notify_swap(amount: float, token_from: str, price: float):
    message = f"Sold {amount} {token_from} at a ratio of {price}"
    notify(message)
