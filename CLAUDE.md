# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Run the app

```bash
streamlit run app.py
```

## Install dependencies

```bash
pip install -r requirements.txt
```

## Architecture

This is a Streamlit trading dashboard called **Xavier AI Trader**.

- **app.py** — UI layer. Streamlit interface where the user selects an asset, enters a capital amount, and triggers analysis. Calls trading logic and displays results.
- **trading_logic.py** — Trading strategy logic. Implements the "buy Monday / sell Tuesday" strategy using `ccxt` to interface with Binance (testnet for simulation).
- **config.py** — API keys, exchange settings, trading pairs, and strategy parameters (e.g. Binance testnet URLs, default symbol).

## Trading strategy

The core strategy is **buy on Monday open / sell on Tuesday close**. All live execution uses Binance Testnet (`https://testnet.binance.vision`) to avoid real funds. The `ccxt` library is used for all exchange interactions — never raw HTTP calls.

## Key dependencies

| Package | Purpose |
|---|---|
| `ccxt` | Exchange connectivity (Binance testnet) |
| `streamlit` | UI |
| `pandas` | Data manipulation |
| `anthropic` | Claude API for AI signal analysis |
| `yfinance` | Historical price data for non-crypto assets |
