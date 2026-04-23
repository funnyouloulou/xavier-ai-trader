import os

# Binance Testnet credentials
BINANCE_API_KEY = os.getenv("BINANCE_TESTNET_API_KEY", "")
BINANCE_SECRET = os.getenv("BINANCE_TESTNET_SECRET", "")

# Anthropic Claude API key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Exchange settings
EXCHANGE_ID = "binance"
TESTNET = True
TESTNET_URLS = {
    "private": "https://testnet.binance.vision/api",
}

# Trading pairs
DEFAULT_SYMBOL = "BTC/USDT"
SUPPORTED_SYMBOLS = {
    "Bitcoin (BTC)": "BTC/USDT",
    "Ethereum (ETH)": "ETH/USDT",
    "Solana (SOL)": "SOL/USDT",
}

# Indicators
RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
EMA_SHORT = 20
EMA_LONG = 50
OHLCV_TIMEFRAME = "1h"
OHLCV_LIMIT = 100

# Risk management
STOP_LOSS_PCT = 0.02    # 2% stop loss
TAKE_PROFIT_PCT = 0.03  # 3% take profit

# Auto-refresh interval (seconds)
AUTO_REFRESH_SECONDS = 300  # 5 minutes
