from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

WATCHLIST: dict[str, dict[str, str]] = {
    "🇺🇸 Tech US": dict(sorted({
        "Adobe": "ADBE",
        "Airbnb": "ABNB",
        "AMD": "AMD",
        "Amazon": "AMZN",
        "Apple": "AAPL",
        "Block (Square)": "SQ",
        "Broadcom": "AVGO",
        "Coinbase": "COIN",
        "CrowdStrike": "CRWD",
        "DataDog": "DDOG",
        "Google": "GOOGL",
        "Intel": "INTC",
        "Meta": "META",
        "Microsoft": "MSFT",
        "Netflix": "NFLX",
        "Nvidia": "NVDA",
        "Oracle": "ORCL",
        "Palantir": "PLTR",
        "Palo Alto": "PANW",
        "PayPal": "PYPL",
        "Qualcomm": "QCOM",
        "Salesforce": "CRM",
        "Shopify": "SHOP",
        "Snap": "SNAP",
        "Snowflake": "SNOW",
        "Spotify": "SPOT",
        "Tesla": "TSLA",
        "Uber": "UBER",
        "Zoom": "ZM",
    }.items())),
    "🏦 Finance & Industrie US": dict(sorted({
        "Bank of America": "BAC",
        "BlackRock": "BLK",
        "Chevron": "CVX",
        "Disney": "DIS",
        "ExxonMobil": "XOM",
        "Ford": "F",
        "General Motors": "GM",
        "Goldman Sachs": "GS",
        "Johnson & Johnson": "JNJ",
        "JPMorgan": "JPM",
        "Lucid": "LCID",
        "Mastercard": "MA",
        "Pfizer": "PFE",
        "Rivian": "RIVN",
        "Visa": "V",
    }.items())),
    "🎮 Gaming": dict(sorted({
        "Activision Blizzard": "ATVI",
        "Electronic Arts": "EA",
        "Nintendo": "NTDOY",
        "Roblox": "RBLX",
        "Square Enix": "SQNNY",
        "Take-Two Interactive": "TTWO",
        "Ubisoft": "UBI.PA",
    }.items())),
    "🇫🇷 France": dict(sorted({
        "Airbus": "AIR.PA",
        "BNP Paribas": "BNP.PA",
        "Capgemini": "CAP.PA",
        "Danone": "BN.PA",
        "Hermès": "RMS.PA",
        "Kering": "KER.PA",
        "L'Oréal": "OR.PA",
        "LVMH": "MC.PA",
        "Pernod Ricard": "RI.PA",
        "Sanofi": "SAN.PA",
        "Société Générale": "GLE.PA",
        "Stellantis": "STLAM.MI",
        "TotalEnergies": "TTE.PA",
    }.items())),
    "🇩🇪 Allemagne": dict(sorted({
        "Adidas": "ADDYY",
        "Allianz": "ALIZY",
        "BASF": "BASFY",
        "BMW": "BMWYY",
        "Deutsche Bank": "DB",
        "SAP": "SAP",
        "Siemens": "SIEGY",
        "Volkswagen": "VWAGY",
    }.items())),
    "🇬🇧 Royaume-Uni": dict(sorted({
        "AstraZeneca": "AZN",
        "Barclays": "BCS",
        "BP": "BP",
        "GSK": "GSK",
        "HSBC": "HSBC",
        "Shell": "SHEL",
        "Unilever": "UL",
    }.items())),
    "🇨🇳 Asie": dict(sorted({
        "Alibaba": "BABA",
        "ASML": "ASML",
        "Baidu": "BIDU",
        "BYD": "BYDDY",
        "JD.com": "JD",
        "NIO": "NIO",
        "Tencent": "TCEHY",
    }.items())),
    "₿ Crypto Top": dict(sorted({
        "Avalanche": "AVAX-USD",
        "BNB": "BNB-USD",
        "Bitcoin": "BTC-USD",
        "Chainlink": "LINK-USD",
        "Cosmos": "ATOM-USD",
        "Ethereum": "ETH-USD",
        "Litecoin": "LTC-USD",
        "Solana": "SOL-USD",
        "Uniswap": "UNI-USD",
        "XRP": "XRP-USD",
    }.items())),
    "🐕 Crypto < 1$": dict(sorted({
        "Algo": "ALGO-USD",
        "Bonk": "BONK-USD",
        "Cardano": "ADA-USD",
        "Dogecoin": "DOGE-USD",
        "Floki": "FLOKI-USD",
        "Gala": "GALA-USD",
        "Hbar": "HBAR-USD",
        "Jasmy": "JASMY-USD",
        "Mana": "MANA-USD",
        "Pepe": "PEPE-USD",
        "Polkadot": "DOT-USD",
        "Sand": "SAND-USD",
        "Shiba Inu": "SHIB-USD",
        "Stellar": "XLM-USD",
        "Vechain": "VET-USD",
    }.items())),
    "🏅 Matières premières": dict(sorted({
        "Argent": "SI=F",
        "Cuivre": "HG=F",
        "Gaz naturel": "NG=F",
        "Or": "GC=F",
        "Pétrole (WTI)": "CL=F",
        "Platine": "PL=F",
    }.items())),
    "📊 ETFs": dict(sorted({
        "ARK Innovation": "ARKK",
        "Chine": "FXI",
        "Dividendes": "VYM",
        "Europe": "VGK",
        "Immobilier (REIT)": "VNQ",
        "Marchés émergents": "EEM",
        "Nasdaq 100": "QQQ",
        "Obligations longues": "TLT",
        "Or (ETF)": "GLD",
        "Russell 2000": "IWM",
        "S&P 500": "SPY",
    }.items())),
}

TOTAL_ASSETS = sum(len(v) for v in WATCHLIST.values())


def _rsi_ema_signal(closes) -> tuple[float, float, float, bool]:
    """Returns (rsi, ema20, ema50, ema_bullish)."""
    delta = closes.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rsi = float((100 - 100 / (1 + gain / loss)).iloc[-1])
    ema20 = float(closes.ewm(span=20, adjust=False).mean().iloc[-1])
    ema50 = float(closes.ewm(span=50, adjust=False).mean().iloc[-1])
    return rsi, ema20, ema50, ema20 > ema50


def _tf_agrees(ticker: str, interval: str, signal: str) -> bool:
    """Check if a given timeframe agrees with the primary signal."""
    try:
        hist = yf.Ticker(ticker).history(period="5d", interval=interval)
        if hist.empty or len(hist) < 20:
            return False
        rsi, ema20, ema50, bullish = _rsi_ema_signal(hist["Close"])
        if signal == "BUY":
            return rsi < 35 and bullish
        return rsi > 65 and not bullish
    except Exception:
        return False


def _analyse(name: str, ticker: str, category: str) -> dict | None:
    try:
        hist = yf.Ticker(ticker).history(period="7d", interval="1h")
        if hist.empty or len(hist) < 50:
            return None

        rsi, ema20, ema50, ema_bullish = _rsi_ema_signal(hist["Close"])
        close = float(hist["Close"].iloc[-1])

        if rsi < 30 and ema_bullish:
            signal = "BUY"
            base_conf = min(95, int(70 + (30 - rsi) * 2))
        elif rsi > 70 and not ema_bullish:
            signal = "SELL"
            base_conf = min(95, int(70 + (rsi - 70) * 2))
        else:
            return None

        # Multi-timeframe confirmation
        tf15 = _tf_agrees(ticker, "15m", signal)
        tf4h = _tf_agrees(ticker, "4h", signal)
        tf_count = 1 + int(tf15) + int(tf4h)
        tf_label = f"{tf_count}/3 TF ({'15m ✓' if tf15 else '15m ✗'} · {'4h ✓' if tf4h else '4h ✗'})"

        # Boost confidence based on timeframe agreement
        confidence = min(98, base_conf + (tf_count - 1) * 5)

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
            "tf_label": tf_label,
            "tf_count": tf_count,
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


def build_chart(ticker: str, name: str, signal: str) -> go.Figure:
    """Price + EMA20/50 + RSI chart for the last 30 days."""
    hist = yf.Ticker(ticker).history(period="30d", interval="1h")
    if hist.empty:
        return None

    closes = hist["Close"]
    dates = hist.index

    delta = closes.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rsi_series = 100 - 100 / (1 + gain / loss)
    ema20_series = closes.ewm(span=20, adjust=False).mean()
    ema50_series = closes.ewm(span=50, adjust=False).mean()

    signal_color = {"BUY": "#00c853", "SELL": "#e53935", "HOLD": "#546e7a"}[signal]

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.68, 0.32],
        vertical_spacing=0.06,
    )

    # Price line
    fig.add_trace(go.Scatter(
        x=dates, y=closes,
        name="Prix", line=dict(color="#ffffff", width=1.5),
    ), row=1, col=1)

    # EMA 20
    fig.add_trace(go.Scatter(
        x=dates, y=ema20_series,
        name="EMA 20", line=dict(color="#00c853", width=1, dash="dot"),
    ), row=1, col=1)

    # EMA 50
    fig.add_trace(go.Scatter(
        x=dates, y=ema50_series,
        name="EMA 50", line=dict(color="#e53935", width=1, dash="dot"),
    ), row=1, col=1)

    # Signal marker on last candle
    fig.add_trace(go.Scatter(
        x=[dates[-1]], y=[float(closes.iloc[-1])],
        mode="markers",
        marker=dict(color=signal_color, size=10, symbol="circle"),
        name=signal, showlegend=True,
    ), row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(
        x=dates, y=rsi_series,
        name="RSI", line=dict(color="#7c4dff", width=1.5),
        fill="tozeroy", fillcolor="rgba(124,77,255,0.08)",
    ), row=2, col=1)

    fig.add_hline(y=70, line=dict(color="#e53935", dash="dash", width=1), row=2, col=1)
    fig.add_hline(y=30, line=dict(color="#00c853", dash="dash", width=1), row=2, col=1)
    fig.add_hrect(y0=30, y1=70, fillcolor="rgba(255,255,255,0.03)", line_width=0, row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        title=dict(text=f"{name} — 30 jours", font=dict(size=14)),
        paper_bgcolor="#0e1117",
        plot_bgcolor="#0e1117",
        legend=dict(orientation="h", y=1.08, x=0),
        margin=dict(l=8, r=8, t=50, b=8),
        height=420,
        xaxis2=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#1e1e2e"),
        yaxis2=dict(range=[0, 100], showgrid=True, gridcolor="#1e1e2e", title="RSI"),
    )
    fig.update_xaxes(showspikes=True, spikecolor="#444", spikethickness=1)

    return fig
