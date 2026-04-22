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

# Strategy parameters
DEFAULT_SYMBOL = "BTC/USDT"
SUPPORTED_SYMBOLS = {
    "Bitcoin (BTC)": "BTC/USDT",
    "Ethereum (ETH)": "ETH/USDT",
    "Solana (SOL)": "SOL/USDT",
}

BUY_DAY = 0   # Monday (weekday index: 0=Mon … 6=Sun)
SELL_DAY = 1  # Tuesday
