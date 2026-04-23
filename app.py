import streamlit as st
from datetime import datetime, timezone
from config import (
    SUPPORTED_SYMBOLS, TESTNET,
    RSI_OVERSOLD, RSI_OVERBOUGHT,
    EMA_SHORT, EMA_LONG,
    STOP_LOSS_PCT, TAKE_PROFIT_PCT,
    AUTO_REFRESH_SECONDS, OHLCV_TIMEFRAME,
)
from trading_logic import get_signal, get_current_price, get_balance, place_market_buy, place_market_sell_all

st.set_page_config(
    page_title="Xavier AI Trader",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* Mobile-first global */
.block-container { padding: 1rem 1rem 2rem; max-width: 480px; }

/* Signal card */
.signal-card {
    border-radius: 20px;
    padding: 28px 20px 20px;
    text-align: center;
    margin: 12px 0 8px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.18);
}
.signal-card.buy  { background: linear-gradient(135deg, #00c853 0%, #1b5e20 100%); }
.signal-card.sell { background: linear-gradient(135deg, #e53935 0%, #7f0000 100%); }
.signal-card.hold { background: linear-gradient(135deg, #455a64 0%, #1c313a 100%); }
.signal-label { font-size: 2.2rem; font-weight: 900; color: #fff; letter-spacing: 3px; }
.signal-conf  { font-size: 1rem; color: rgba(255,255,255,0.85); margin-top: 4px; }
.signal-meta  { font-size: 0.82rem; color: rgba(255,255,255,0.7); margin-top: 10px; }
.signal-price { font-size: 1.4rem; font-weight: 700; color: #fff; margin-top: 6px; }

/* AI reasoning box */
.ai-box {
    background: #0f0f1a;
    border-left: 4px solid #7c4dff;
    border-radius: 10px;
    padding: 14px 16px;
    color: #d0d0e8;
    font-size: 0.92rem;
    line-height: 1.55;
    margin: 12px 0;
}

/* Alert banners */
.alert-sl { background:#7f0000; color:#fff; border-radius:10px; padding:12px 16px; font-weight:700; }
.alert-tp { background:#1b5e20; color:#fff; border-radius:10px; padding:12px 16px; font-weight:700; }

/* Utility */
.small-grey { font-size: 0.78rem; color: #888; text-align: center; margin-top: 4px; }
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 📈 Xavier AI Trader")
mode_badge = "🔴 TESTNET — simulation" if TESTNET else "🟢 LIVE — Binance"
st.caption(mode_badge)
st.divider()

# ── Asset & Capital ───────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 2])
with col1:
    choix = st.selectbox("Actif", list(SUPPORTED_SYMBOLS.keys()), label_visibility="collapsed")
with col2:
    montant = st.number_input("Capital USDT", min_value=10.0, value=100.0, step=10.0, label_visibility="collapsed")

symbol = SUPPORTED_SYMBOLS[choix]

# ── Live Signal Panel (auto-refresh every 5 min) ──────────────────────────────
@st.fragment(run_every=AUTO_REFRESH_SECONDS)
def live_signal_panel(symbol: str) -> None:
    st.markdown("### Signal IA")

    with st.spinner("Analyse multi-facteurs en cours…"):
        try:
            data = get_signal(symbol)
        except Exception as e:
            st.error(f"Erreur analyse : {e}")
            return

    signal = data["signal"]
    confidence = data.get("confidence")
    ai_powered = data.get("ai_powered", False)

    # Signal card
    css = {"BUY": "buy", "SELL": "sell", "HOLD": "hold"}[signal]
    label = {"BUY": "🟢 ACHÈTE MAINTENANT", "SELL": "🔴 VENDS TOUT", "HOLD": "⏸ ATTENDS"}[signal]
    conf_html = f'<div class="signal-conf">Confiance IA : <b>{confidence}%</b></div>' if confidence is not None else ""
    rsi_icon = "🔴" if data["rsi"] < 30 or data["rsi"] > 70 else "⚪"
    ema_arrow = "↑" if data["ema_short"] > data["ema_long"] else "↓"

    st.markdown(f"""
<div class="signal-card {css}">
  <div class="signal-label">{label}</div>
  {conf_html}
  <div class="signal-price">{data['close']:,.2f} USD</div>
  <div class="signal-meta">
    RSI {data['rsi']:.1f} {rsi_icon} &nbsp;·&nbsp;
    EMA{EMA_SHORT} {data['ema_short']:,.0f} &nbsp;·&nbsp;
    EMA{EMA_LONG} {data['ema_long']:,.0f} {ema_arrow}
  </div>
</div>
""", unsafe_allow_html=True)

    # AI reasoning
    if data.get("reason"):
        icon = "🤖 IA" if ai_powered else "📊 Règles"
        st.markdown(f'<div class="ai-box"><b>{icon} :</b> {data["reason"]}</div>', unsafe_allow_html=True)

    # SL / TP badges
    if data.get("stop_loss_price") or data.get("take_profit_price"):
        c1, c2 = st.columns(2)
        if data.get("stop_loss_price"):
            c1.metric("🛡 Stop Loss", f"{data['stop_loss_price']:,.2f}", f"-{STOP_LOSS_PCT*100:.0f}%", delta_color="inverse")
        if data.get("take_profit_price"):
            c2.metric("🎯 Take Profit", f"{data['take_profit_price']:,.2f}", f"+{TAKE_PROFIT_PCT*100:.0f}%")

    # Triggered alerts
    if data.get("stop_loss_triggered"):
        st.markdown('<div class="alert-sl">🚨 STOP LOSS DÉCLENCHÉ — vends maintenant !</div>', unsafe_allow_html=True)
    if data.get("take_profit_triggered"):
        st.markdown('<div class="alert-tp">🎉 TAKE PROFIT ATTEINT — profits sécurisés !</div>', unsafe_allow_html=True)

    now_utc = datetime.now(timezone.utc).strftime("%H:%M UTC")
    st.markdown(f'<div class="small-grey">Bougie {OHLCV_TIMEFRAME} · {data["candle_time"][:16].replace("T"," ")} · Scan auto toutes les 5 min · {now_utc}</div>', unsafe_allow_html=True)


live_signal_panel(symbol)

st.divider()

# ── 1-Click Execution ─────────────────────────────────────────────────────────
st.markdown("### ⚡ Exécution en 1 clic")
if TESTNET:
    st.caption("Simulation Testnet — aucun argent réel engagé.")

col_buy, col_sell = st.columns(2)

with col_buy:
    if st.button(f"🟢 ACHETER\n{symbol.split('/')[0]}", use_container_width=True, type="primary"):
        with st.spinner("Exécution ordre d'achat…"):
            try:
                r = place_market_buy(symbol, montant)
                st.success(f"✅ Acheté **{r['qty']} {symbol.split('/')[0]}** @ {r['estimated_price']:,.2f} USD")
                c1, c2 = st.columns(2)
                c1.metric("🛡 Stop Loss", f"{r['stop_loss_price']:,.2f}")
                c2.metric("🎯 Take Profit", f"{r['take_profit_price']:,.2f}")
                st.caption(f"Order ID : {r.get('order_id', 'N/A')} · {r.get('status', '')}")
            except Exception as e:
                st.error(f"Erreur : {e}")

with col_sell:
    if st.button("🔴 VENDRE\nTOUT", use_container_width=True):
        with st.spinner("Exécution de la vente…"):
            try:
                r = place_market_sell_all(symbol)
                if r.get("status") == "skipped — no balance":
                    st.warning("Aucun actif à vendre dans le portefeuille.")
                else:
                    st.success(f"✅ Vendu **{r['qty']} {symbol.split('/')[0]}**")
                    st.caption(f"Order ID : {r.get('order_id', 'N/A')} · {r.get('status', '')}")
            except Exception as e:
                st.error(f"Erreur : {e}")

st.divider()

# ── Utilities ─────────────────────────────────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    if st.button("💰 Solde Testnet", use_container_width=True):
        try:
            usdt = get_balance("USDT")
            base = symbol.split("/")[0]
            base_bal = get_balance(base)
            st.info(f"USDT : **{usdt:,.2f}** | {base} : **{base_bal:.6f}**")
        except Exception as e:
            st.error(f"Erreur solde : {e}")

with col_b:
    if st.button("🔄 Prix live", use_container_width=True):
        try:
            price = get_current_price(symbol)
            st.info(f"**{symbol}** : {price:,.2f} USD")
        except Exception as e:
            st.error(f"Erreur : {e}")

# ── Settings ──────────────────────────────────────────────────────────────────
with st.expander("⚙️ Paramètres de la stratégie"):
    c1, c2, c3 = st.columns(3)
    c1.metric("RSI Buy", f"< {RSI_OVERSOLD}")
    c2.metric("RSI Sell", f"> {RSI_OVERBOUGHT}")
    c3.metric("Stop Loss", f"{STOP_LOSS_PCT*100:.0f}%")
    c1.metric("Take Profit", f"{TAKE_PROFIT_PCT*100:.0f}%")
    c2.metric("EMA", f"{EMA_SHORT}/{EMA_LONG}")
    c3.metric("Scan auto", "5 min")
    st.caption("Variables d'environnement requises :")
    st.code("BINANCE_TESTNET_API_KEY\nBINANCE_TESTNET_SECRET\nANTHROPIC_API_KEY")
