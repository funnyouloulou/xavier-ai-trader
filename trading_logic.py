import ccxt
from datetime import datetime, timezone
from config import (
    BINANCE_API_KEY, BINANCE_SECRET,
    TESTNET, TESTNET_URLS,
    BUY_DAY, SELL_DAY,
)


def get_exchange() -> ccxt.binance:
    exchange = ccxt.binance({
        "apiKey": BINANCE_API_KEY,
        "secret": BINANCE_SECRET,
        "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    })
    if TESTNET:
        exchange.set_sandbox_mode(True)
        exchange.urls["api"] = TESTNET_URLS["api"]
    return exchange


def get_current_price(symbol: str) -> float:
    exchange = get_exchange()
    ticker = exchange.fetch_ticker(symbol)
    return ticker["last"]


def get_balance(currency: str = "USDT") -> float:
    exchange = get_exchange()
    balance = exchange.fetch_balance()
    return balance["free"].get(currency, 0.0)


def get_today_signal() -> str:
    """Return 'BUY', 'SELL', or 'HOLD' based on the weekday."""
    weekday = datetime.now(timezone.utc).weekday()
    if weekday == BUY_DAY:
        return "BUY"
    if weekday == SELL_DAY:
        return "SELL"
    return "HOLD"


def place_market_buy(symbol: str, amount_usdt: float) -> dict:
    """Buy `amount_usdt` worth of `symbol` at market price."""
    exchange = get_exchange()
    price = get_current_price(symbol)
    qty = exchange.amount_to_precision(symbol, amount_usdt / price)
    order = exchange.create_market_buy_order(symbol, float(qty))
    return {
        "action": "BUY",
        "symbol": symbol,
        "qty": qty,
        "estimated_price": price,
        "order_id": order.get("id"),
        "status": order.get("status"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "testnet": TESTNET,
    }


def place_market_sell_all(symbol: str) -> dict:
    """Sell the entire available balance of the base asset."""
    exchange = get_exchange()
    base_currency = symbol.split("/")[0]
    balance = get_balance(base_currency)
    if balance <= 0:
        return {
            "action": "SELL",
            "symbol": symbol,
            "qty": 0,
            "status": "skipped — no balance",
            "testnet": TESTNET,
        }
    qty = exchange.amount_to_precision(symbol, balance)
    order = exchange.create_market_sell_order(symbol, float(qty))
    return {
        "action": "SELL",
        "symbol": symbol,
        "qty": qty,
        "order_id": order.get("id"),
        "status": order.get("status"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "testnet": TESTNET,
    }


def run_strategy(symbol: str, amount_usdt: float) -> dict:
    """
    Execute the Monday-buy / Tuesday-sell strategy.
    Returns a result dict with signal, action taken, and order details.
    """
    signal = get_today_signal()
    price = get_current_price(symbol)
    result = {"signal": signal, "price": price, "symbol": symbol, "testnet": TESTNET}

    if signal == "BUY":
        order = place_market_buy(symbol, amount_usdt)
        result.update(order)
    elif signal == "SELL":
        order = place_market_sell_all(symbol)
        result.update(order)
    else:
        result["action"] = "HOLD"
        result["message"] = "No trade today. Strategy only acts on Monday (buy) and Tuesday (sell)."

    return result
