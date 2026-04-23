import json
import os
import ccxt
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone
from config import (
    BINANCE_API_KEY, BINANCE_SECRET,
    TESTNET, TESTNET_URLS,
    RSI_PERIOD, RSI_OVERSOLD, RSI_OVERBOUGHT,
    EMA_SHORT, EMA_LONG,
    STOP_LOSS_PCT,
    OHLCV_TIMEFRAME, OHLCV_LIMIT,
)


def get_exchange() -> ccxt.binance:
    """Testnet exchange for private endpoints (orders, balance)."""
    config: dict = {
        "apiKey": BINANCE_API_KEY,
        "secret": BINANCE_SECRET,
        "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    }
    if TESTNET:
        config["urls"] = {
            "api": {
                "public": TESTNET_URLS["private"],
                "private": TESTNET_URLS["private"],
            }
        }
    return ccxt.binance(config)


def _ccxt_to_yf(symbol: str) -> str:
    # Yahoo Finance uses BTC-USD not BTC-USDT
    base, quote = symbol.split("/")
    if quote == "USDT":
        quote = "USD"
    return f"{base}-{quote}"


def get_current_price(symbol: str) -> float:
    hist = yf.Ticker(_ccxt_to_yf(symbol)).history(period="1d", interval="1m")
    return float(hist["Close"].iloc[-1])


def get_balance(currency: str = "USDT") -> float:
    exchange = get_exchange()
    balance = exchange.fetch_balance()
    return balance["free"].get(currency, 0.0)


def _load_ohlcv(symbol: str) -> pd.DataFrame:
    hist = yf.Ticker(_ccxt_to_yf(symbol)).history(period="7d", interval=OHLCV_TIMEFRAME)
    hist = hist.reset_index()
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(hist["Datetime"], utc=True),
        "open": hist["Open"],
        "high": hist["High"],
        "low": hist["Low"],
        "close": hist["Close"],
        "volume": hist["Volume"],
    })
    return df.tail(OHLCV_LIMIT).reset_index(drop=True)


def _compute_rsi(series: pd.Series, period: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - 100 / (1 + rs)


def compute_indicators(symbol: str) -> dict:
    """Fetch OHLCV candles and compute RSI + EMA indicators."""
    df = _load_ohlcv(symbol)
    df["ema_short"] = df["close"].ewm(span=EMA_SHORT, adjust=False).mean()
    df["ema_long"] = df["close"].ewm(span=EMA_LONG, adjust=False).mean()
    df["rsi"] = _compute_rsi(df["close"], RSI_PERIOD)
    last = df.iloc[-1]
    return {
        "rsi": round(float(last["rsi"]), 2),
        "ema_short": round(float(last["ema_short"]), 4),
        "ema_long": round(float(last["ema_long"]), 4),
        "close": round(float(last["close"]), 4),
        "candle_time": last["timestamp"].isoformat(),
    }


# --- Position tracking (entry price + stop loss) ---

def _position_path(symbol: str) -> str:
    return f"position_{symbol.replace('/', '_')}.json"


def _load_position(symbol: str) -> dict | None:
    path = _position_path(symbol)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


def _save_position(symbol: str, entry_price: float) -> None:
    data = {
        "symbol": symbol,
        "entry_price": entry_price,
        "stop_loss_price": round(entry_price * (1 - STOP_LOSS_PCT), 4),
        "opened_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(_position_path(symbol), "w") as f:
        json.dump(data, f)


def _clear_position(symbol: str) -> None:
    path = _position_path(symbol)
    if os.path.exists(path):
        os.remove(path)


# --- Signal logic ---

def get_signal(symbol: str) -> dict:
    """
    Compute RSI + EMA signal for `symbol`.
    BUY  : RSI < RSI_OVERSOLD  AND  EMA_SHORT > EMA_LONG
    SELL : RSI > RSI_OVERBOUGHT OR  stop loss triggered
    HOLD : everything else
    """
    indicators = compute_indicators(symbol)
    rsi = indicators["rsi"]
    ema_short = indicators["ema_short"]
    ema_long = indicators["ema_long"]
    current_price = indicators["close"]

    # Stop loss takes priority
    position = _load_position(symbol)
    if position and current_price <= position["stop_loss_price"]:
        return {
            **indicators,
            "signal": "SELL",
            "reason": f"Stop loss déclenché (prix {current_price} <= seuil {position['stop_loss_price']})",
            "stop_loss_triggered": True,
            "entry_price": position["entry_price"],
            "stop_loss_price": position["stop_loss_price"],
        }

    if rsi < RSI_OVERSOLD and ema_short > ema_long:
        signal, reason = "BUY", f"RSI survendu ({rsi}) + EMA{EMA_SHORT} au-dessus de EMA{EMA_LONG}"
    elif rsi > RSI_OVERBOUGHT:
        signal, reason = "SELL", f"RSI suracheté ({rsi})"
    else:
        trend = "haussière" if ema_short > ema_long else "baissière"
        signal, reason = "HOLD", f"RSI neutre ({rsi}), tendance {trend}"

    result = {**indicators, "signal": signal, "reason": reason, "stop_loss_triggered": False}
    if position:
        result["entry_price"] = position["entry_price"]
        result["stop_loss_price"] = position["stop_loss_price"]
    return result


# --- Order execution ---

def place_market_buy(symbol: str, amount_usdt: float) -> dict:
    exchange = get_exchange()
    price = get_current_price(symbol)
    qty = exchange.amount_to_precision(symbol, amount_usdt / price)
    order = exchange.create_market_buy_order(symbol, float(qty))
    _save_position(symbol, price)
    return {
        "action": "BUY",
        "symbol": symbol,
        "qty": qty,
        "estimated_price": price,
        "stop_loss_price": round(price * (1 - STOP_LOSS_PCT), 4),
        "order_id": order.get("id"),
        "status": order.get("status"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "testnet": TESTNET,
    }


def place_market_sell_all(symbol: str) -> dict:
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
    _clear_position(symbol)
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
    signal_data = get_signal(symbol)
    signal = signal_data["signal"]
    result = {**signal_data, "symbol": symbol, "testnet": TESTNET}

    if signal == "BUY":
        order = place_market_buy(symbol, amount_usdt)
        result.update(order)
    elif signal == "SELL":
        order = place_market_sell_all(symbol)
        result.update(order)
    else:
        result["action"] = "HOLD"

    return result
