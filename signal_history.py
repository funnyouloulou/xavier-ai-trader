import json
import os
from datetime import datetime, timezone

_FILE = "signal_history.json"
_MAX = 300


def log(results: list[dict]) -> None:
    """Append scanner results to history (newest first, max _MAX entries)."""
    if not results:
        return
    history = load()
    now = datetime.now(timezone.utc).isoformat()
    for r in results:
        history.insert(0, {
            "ts": now,
            "name": r["name"],
            "ticker": r["ticker"],
            "signal": r["signal"],
            "confidence": r.get("confidence"),
            "rsi": r.get("rsi"),
            "close": r.get("close"),
            "tf_label": r.get("tf_label", ""),
        })
    with open(_FILE, "w") as f:
        json.dump(history[:_MAX], f, indent=2)


def load() -> list[dict]:
    if os.path.exists(_FILE):
        with open(_FILE) as f:
            return json.load(f)
    return []
