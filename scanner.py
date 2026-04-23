from concurrent.futures import ThreadPoolExecutor, as_completed
import yfinance as yf

WATCHLIST: dict[str, dict[str, str]] = {
    "🇺🇸 Tech US": {
        "Apple": "AAPL",
        "Microsoft": "MSFT",
        "Nvidia": "NVDA",
        "Amazon": "AMZN",
        "Google": "GOOGL",
        "Meta": "META",
        "Tesla": "TSLA",
        "AMD": "AMD",
        "Netflix": "NFLX",
        "Palantir": "PLTR",
        "Coinbase": "COIN",
        "Broadcom": "AVGO",
        "Intel": "INTC",
        "Qualcomm": "QCOM",
        "Adobe": "ADBE",
        "Salesforce": "CRM",
        "Oracle": "ORCL",
        "Uber": "UBER",
        "Airbnb": "ABNB",
        "Spotify": "SPOT",
        "Snap": "SNAP",
        "PayPal": "PYPL",
        "Block (Square)": "SQ",
        "Shopify": "SHOP",
        "Snowflake": "SNOW",
        "CrowdStrike": "CRWD",
        "Palo Alto": "PANW",
        "Zoom": "ZM",
        "DataDog": "DDOG",
    },
    "🏦 Finance & Industrie US": {
        "JPMorgan": "JPM",
        "Goldman Sachs": "GS",
        "Bank of America": "BAC",
        "Visa": "V",
        "Mastercard": "MA",
        "BlackRock": "BLK",
        "ExxonMobil": "XOM",
        "Chevron": "CVX",
        "Disney": "DIS",
        "Pfizer": "PFE",
        "Johnson & Johnson": "JNJ",
        "Ford": "F",
        "General Motors": "GM",
        "Rivian": "RIVN",
        "Lucid": "LCID",
    },
    "🎮 Gaming": {
        "Ubisoft": "UBI.PA",
        "Electronic Arts": "EA",
        "Take-Two Interactive": "TTWO",
        "Roblox": "RBLX",
        "Nintendo": "NTDOY",
        "Activision Blizzard": "ATVI",
        "Square Enix": "SQNNY",
    },
    "🇫🇷 France": {
        "LVMH": "MC.PA",
        "L'Oréal": "OR.PA",
        "TotalEnergies": "TTE.PA",
        "BNP Paribas": "BNP.PA",
        "Airbus": "AIR.PA",
        "Hermès": "RMS.PA",
        "Société Générale": "GLE.PA",
        "Sanofi": "SAN.PA",
        "Danone": "BN.PA",
        "Kering": "KER.PA",
        "Pernod Ricard": "RI.PA",
        "Capgemini": "CAP.PA",
        "Stellantis": "STLAM.MI",
    },
    "🇩🇪 Allemagne": {
        "SAP": "SAP",
        "Volkswagen": "VWAGY",
        "BMW": "BMWYY",
        "Siemens": "SIEGY",
        "Adidas": "ADDYY",
        "Allianz": "ALIZY",
        "Deutsche Bank": "DB",
        "BASF": "BASFY",
    },
    "🇬🇧 Royaume-Uni": {
        "AstraZeneca": "AZN",
        "Shell": "SHEL",
        "BP": "BP",
        "HSBC": "HSBC",
        "Unilever": "UL",
        "GSK": "GSK",
        "Barclays": "BCS",
    },
    "🇨🇳 Asie": {
        "Alibaba": "BABA",
        "Tencent": "TCEHY",
        "Baidu": "BIDU",
        "JD.com": "JD",
        "NIO": "NIO",
        "BYD": "BYDDY",
        "ASML": "ASML",
    },
    "₿ Crypto Top": {
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Solana": "SOL-USD",
        "BNB": "BNB-USD",
        "XRP": "XRP-USD",
        "Avalanche": "AVAX-USD",
        "Chainlink": "LINK-USD",
        "Litecoin": "LTC-USD",
        "Uniswap": "UNI-USD",
        "Cosmos": "ATOM-USD",
    },
    "🐕 Crypto < 1$": {
        "Dogecoin": "DOGE-USD",
        "Cardano": "ADA-USD",
        "Stellar": "XLM-USD",
        "Shiba Inu": "SHIB-USD",
        "Polkadot": "DOT-USD",
        "Pepe": "PEPE-USD",
        "Floki": "FLOKI-USD",
        "Bonk": "BONK-USD",
        "Jasmy": "JASMY-USD",
        "Vechain": "VET-USD",
        "Hbar": "HBAR-USD",
        "Algo": "ALGO-USD",
        "Gala": "GALA-USD",
        "Sand": "SAND-USD",
        "Mana": "MANA-USD",
    },
    "🏅 Matières premières": {
        "Or": "GC=F",
        "Pétrole (WTI)": "CL=F",
        "Argent": "SI=F",
        "Cuivre": "HG=F",
        "Gaz naturel": "NG=F",
        "Platine": "PL=F",
    },
    "📊 ETFs": {
        "S&P 500": "SPY",
        "Nasdaq 100": "QQQ",
        "ARK Innovation": "ARKK",
        "Russell 2000": "IWM",
        "Marchés émergents": "EEM",
        "Or (ETF)": "GLD",
        "Immobilier (REIT)": "VNQ",
        "Obligations longues": "TLT",
        "Europe": "VGK",
        "Chine": "FXI",
        "Dividendes": "VYM",
    },
}

TOTAL_ASSETS = sum(len(v) for v in WATCHLIST.values())


def _analyse(name: str, ticker: str, category: str) -> dict | None:
    try:
        hist = yf.Ticker(ticker).history(period="7d", interval="1h")
        if hist.empty or len(hist) < 50:
            return None

        closes = hist["Close"]

        delta = closes.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rsi = float((100 - 100 / (1 + gain / loss)).iloc[-1])

        ema20 = float(closes.ewm(span=20, adjust=False).mean().iloc[-1])
        ema50 = float(closes.ewm(span=50, adjust=False).mean().iloc[-1])
        close = float(closes.iloc[-1])
        ema_bullish = ema20 > ema50

        if rsi < 30 and ema_bullish:
            signal = "BUY"
            confidence = min(95, int(70 + (30 - rsi) * 2))
        elif rsi > 70 and not ema_bullish:
            signal = "SELL"
            confidence = min(95, int(70 + (rsi - 70) * 2))
        else:
            return None

        return {
            "name": name,
            "ticker": ticker,
            "category": category,
            "signal": signal,
            "confidence": confidence,
            "rsi": round(rsi, 1),
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "close": round(close, 2),
            "ema_trend": "↑" if ema_bullish else "↓",
        }
    except Exception:
        return None


def scan_markets() -> list[dict]:
    """Scan all WATCHLIST assets in parallel. Returns signals sorted by confidence."""
    tasks = [
        (name, ticker, category)
        for category, assets in WATCHLIST.items()
        for name, ticker in assets.items()
    ]
    results = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {executor.submit(_analyse, n, t, c): (n, t) for n, t, c in tasks}
        for future in as_completed(futures):
            r = future.result()
            if r:
                results.append(r)

    buy = sorted([r for r in results if r["signal"] == "BUY"], key=lambda x: -x["confidence"])
    sell = sorted([r for r in results if r["signal"] == "SELL"], key=lambda x: -x["confidence"])
    return buy + sell


def get_ticker_signal(ticker: str, name: str) -> dict:
    """Detailed signal analysis for a single ticker."""
    hist = yf.Ticker(ticker).history(period="7d", interval="1h")
    if hist.empty:
        raise ValueError(f"Pas de données pour {ticker}")

    closes = hist["Close"]
    delta = closes.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rsi = float((100 - 100 / (1 + gain / loss)).iloc[-1])
    ema20 = float(closes.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = float(closes.ewm(span=50, adjust=False).mean().iloc[-1])
    close = float(closes.iloc[-1])
    ema_bullish = ema20 > ema50

    indicators = {
        "rsi": round(rsi, 2),
        "ema_short": round(ema20, 4),
        "ema_long": round(ema50, 4),
        "close": round(close, 4),
        "candle_time": str(hist.index[-1])[:16],
    }

    ai_result = None
    try:
        from ai_analysis import get_ai_signal
        ai_result = get_ai_signal(name, indicators)
    except Exception:
        pass

    if ai_result:
        signal = ai_result["signal"]
        reason = ai_result["reasoning"]
        confidence = ai_result.get("confidence")
        ai_powered = True
    else:
        if rsi < 30 and ema_bullish:
            signal, reason = "BUY", f"RSI survendu ({rsi:.1f}) + EMA20 au-dessus EMA50"
        elif rsi > 70 and not ema_bullish:
            signal, reason = "SELL", f"RSI suracheté ({rsi:.1f}) + EMA20 sous EMA50"
        else:
            trend = "haussière" if ema_bullish else "baissière"
            signal, reason = "HOLD", f"RSI neutre ({rsi:.1f}), tendance {trend}"
        confidence = None
        ai_powered = False

    return {
        **indicators,
        "signal": signal,
        "reason": reason,
        "confidence": confidence,
        "ai_powered": ai_powered,
    }
