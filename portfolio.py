import json
import os
from datetime import datetime, timezone
import yfinance as yf

_FILE = "portfolio.json"


def load() -> list[dict]:
    if os.path.exists(_FILE):
        with open(_FILE) as f:
            return json.load(f)
    return []


def _save(data: list[dict]) -> None:
    with open(_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_position(name: str, ticker: str, buy_price: float, amount: float) -> None:
    portfolio = load()
    quantity = round(amount / buy_price, 6)
    portfolio.append({
        "name": name,
        "ticker": ticker,
        "buy_price": buy_price,
        "quantity": quantity,
        "amount_invested": amount,
        "stop_loss": round(buy_price * 0.98, 4),
        "take_profit": round(buy_price * 1.03, 4),
        "opened_at": datetime.now(timezone.utc).isoformat(),
    })
    _save(portfolio)


def remove_position(ticker: str) -> None:
    _save([p for p in load() if p["ticker"] != ticker])


def get_current_price(ticker: str) -> float | None:
    try:
        hist = yf.Ticker(ticker).history(period="1d", interval="5m")
        if hist.empty:
            return None
        return round(float(hist["Close"].iloc[-1]), 4)
    except Exception:
        return None


def enrich(portfolio: list[dict]) -> list[dict]:
    """Add current price and P&L to each position."""
    enriched = []
    for p in portfolio:
        current = get_current_price(p["ticker"])
        entry = dict(p)
        if current:
            pnl_pct = (current - p["buy_price"]) / p["buy_price"] * 100
            pnl_eur = (current - p["buy_price"]) * p["quantity"]
            entry["current_price"] = current
            entry["pnl_pct"] = round(pnl_pct, 2)
            entry["pnl_eur"] = round(pnl_eur, 2)
            entry["sl_hit"] = current <= p["stop_loss"]
            entry["tp_hit"] = current >= p["take_profit"]
        enriched.append(entry)
    return enriched
