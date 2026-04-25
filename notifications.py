import json
import os
import requests
from datetime import datetime, timezone, timedelta
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

_NOTIFIED_FILE = "notified_signals.json"
_COOLDOWN_HOURS = 4


def _load_notified() -> dict:
    if os.path.exists(_NOTIFIED_FILE):
        with open(_NOTIFIED_FILE) as f:
            return json.load(f)
    return {}


def _save_notified(data: dict) -> None:
    with open(_NOTIFIED_FILE, "w") as f:
        json.dump(data, f)


def should_notify(ticker: str, signal: str) -> bool:
    """Return True if this signal hasn't been sent in the last COOLDOWN_HOURS."""
    notified = _load_notified()
    key = f"{signal}_{ticker}"
    if key not in notified:
        return True
    last_sent = datetime.fromisoformat(notified[key])
    return datetime.now(timezone.utc) - last_sent > timedelta(hours=_COOLDOWN_HOURS)


def mark_notified(ticker: str, signal: str) -> None:
    notified = _load_notified()
    notified[f"{signal}_{ticker}"] = datetime.now(timezone.utc).isoformat()
    _save_notified(notified)


def send_telegram(message: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=5,
        )
        return r.status_code == 200
    except Exception:
        return False


def notify_signal(result: dict) -> bool:
    """Send a Telegram notification for a new signal if cooldown allows."""
    ticker = result["ticker"]
    signal = result["signal"]
    if not should_notify(ticker, signal):
        return False

    emoji = "🟢" if signal == "BUY" else "🔴"
    action = "ACHÈTE MAINTENANT" if signal == "BUY" else "VENDS MAINTENANT"
    tf = result.get("tf_label", "")
    tf_line = f"\nConfirmation : <b>{tf}</b>" if tf else ""

    message = (
        f"{emoji} <b>Xavier AI Trader — {signal}</b>\n\n"
        f"<b>{result['name']}</b> ({ticker})\n"
        f"Prix : {result['close']:,.2f}\n"
        f"RSI : {result['rsi']}{tf_line}\n"
        f"Confiance : <b>{result['confidence']}%</b>\n\n"
        f"➡️ {action} sur eToro !"
    )

    sent = send_telegram(message)
    if sent:
        mark_notified(ticker, signal)
    return sent
