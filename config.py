import os

# Binance Testnet credentials (set via environment variables)
BINANCE_API_KEY = os.getenv("BINANCE_TESTNET_API_KEY", "")
BINANCE_SECRET = os.getenv("BINANCE_TESTNET_SECRET", "")

# Exchange settings
EXCHANGE_ID = "binance"
TESTNET = True
TESTNET_URLS = {
    "api": "https://testnet.binance.vision/api",
    "fapiPublic": "https://testnet.binancefuture.com/fapi/v1",
    "fapiPrivate": "https://testnet.binancefuture.com/fapi/v1",
}

# Trading pairs
DEFAULT_SYMBOL = "BTC/USDT"
SUPPORTED_SYMBOLS = {
    "Bitcoin (BTC)": "BTC/USDT",
    "Ethereum (ETH)": "ETH/USDT",
    "Solana (SOL)": "SOL/USDT",
}

# RSI + EMA strategy parameters
RSI_PERIOD = 14
RSI_OVERSOLD = 30       # BUY threshold
RSI_OVERBOUGHT = 70     # SELL threshold
EMA_SHORT = 20
EMA_LONG = 50
OHLCV_TIMEFRAME = "1h"
OHLCV_LIMIT = 100

# Risk management
STOP_LOSS_PCT = 0.02    # 2% stop loss below entry price
