import streamlit as st
from datetime import datetime, timezone
from config import (
    SUPPORTED_SYMBOLS, TESTNET,
    EMA_SHORT, EMA_LONG,
    STOP_LOSS_PCT, TAKE_PROFIT_PCT,
    AUTO_REFRESH_SECONDS,
)
from trading_logic import get_current_price, get_balance, place_market_buy, place_market_sell_all
from scanner import scan_markets, get_ticker_signal, build_chart, WATCHLIST, TOTAL_ASSETS

st.set_page_config(
    page_title="Xavier AI Trader",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.block-container { padding: 1rem 1rem 2rem; max-width: 500px; }

.signal-card {
    border-radius: 18px; padding: 24px 20px 18px;
    text-align: center; margin: 10px 0 6px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}
.signal-card.buy  { background: linear-gradient(135deg,#00c853,#1b5e20); }
.signal-card.sell { background: linear-gradient(135deg,#e53935,#7f0000); }
.signal-card.hold { background: linear-gradient(135deg,#455a64,#1c313a); }
.signal-label { font-size:2rem; font-weight:900; color:#fff; letter-spacing:3px; }
.signal-conf  { font-size:.95rem; color:rgba(255,255,255,.85); margin-top:4px; }
.signal-meta  { font-size:.8rem; color:rgba(255,255,255,.65); margin-top:8px; }
.signal-price { font-size:1.3rem; font-weight:700; color:#fff; margin-top:6px; }

.opp-buy  { background:#0a1f0a; border-left:4px solid #00c853; border-radius:10px; padding:12px 16px; margin:6px 0; }
.opp-sell { background:#1f0a0a; border-left:4px solid #e53935; border-radius:10px; padding:12px 16px; margin:6px 0; }
.opp-name { font-size:1rem; font-weight:700; color:#fff; }
.opp-ticker { font-size:.78rem; color:#888; margin-left:8px; }
.opp-conf-buy  { font-size:1.1rem; font-weight:900; color:#00c853; }
.opp-conf-sell { font-size:1.1rem; font-weight:900; color:#e53935; }
.opp-meta { font-size:.8rem; color:#aaa; margin-top:4px; }

.ai-box {
    background:#0f0f1a; border-left:4px solid #7c4dff;
    border-radius:10px; padding:12px 16px; color:#d0d0e8;
    font-size:.9rem; line-height:1.55; margin:10px 0;
}
.ts { font-size:.75rem; color:#666; text-align:center; margin-top:6px; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 📈 Xavier AI Trader")
st.caption("🔴 TESTNET — simulation" if TESTNET else "🟢 LIVE — Binance")

tab1, tab2, tab3 = st.tabs(["🔍 Scanner", "📊 Analyser", "⚡ Exécuter"])


# ── TAB 1 : SCANNER ───────────────────────────────────────────────────────────
with tab1:
    @st.fragment(run_every=AUTO_REFRESH_SECONDS)
    def scanner_panel() -> None:
        now = datetime.now(timezone.utc).strftime("%H:%M UTC")
        with st.spinner(f"Scan de {TOTAL_ASSETS} actifs en cours…"):
            results = scan_markets()

        st.markdown(f'<div class="ts">Scan auto toutes les 5 min · {now}</div>', unsafe_allow_html=True)

        if not results:
            st.info("Aucune opportunité forte en ce moment — marchés en consolidation. Revenez dans 5 min.")
            return

        buys = [r for r in results if r["signal"] == "BUY"]
        sells = [r for r in results if r["signal"] == "SELL"]

        if buys:
            st.markdown(f"### 🟢 À ACHETER ({len(buys)})")
            for r in buys:
                st.markdown(f"""
<div class="opp-buy">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <span class="opp-name">{r['name']}</span>
      <span class="opp-ticker">{r['ticker']} · {r['category']}</span>
    </div>
    <span class="opp-conf-buy">{r['confidence']}%</span>
  </div>
  <div class="opp-meta">Prix <b>{r['close']:,.2f}</b> &nbsp;·&nbsp; RSI <b>{r['rsi']}</b> &nbsp;·&nbsp; EMA {r['ema_trend']}</div>
</div>""", unsafe_allow_html=True)

        if sells:
            st.markdown(f"### 🔴 À VENDRE ({len(sells)})")
            for r in sells:
                st.markdown(f"""
<div class="opp-sell">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <span class="opp-name">{r['name']}</span>
      <span class="opp-ticker">{r['ticker']} · {r['category']}</span>
    </div>
    <span class="opp-conf-sell">{r['confidence']}%</span>
  </div>
  <div class="opp-meta">Prix <b>{r['close']:,.2f}</b> &nbsp;·&nbsp; RSI <b>{r['rsi']}</b> &nbsp;·&nbsp; EMA {r['ema_trend']}</div>
</div>""", unsafe_allow_html=True)

    scanner_panel()


# ── TAB 2 : ANALYSER ──────────────────────────────────────────────────────────
with tab2:
    asset_options: dict[str, tuple[str, str]] = {}
    for category, assets in WATCHLIST.items():
        for name, ticker in assets.items():
            asset_options[f"{name}  ({ticker})"] = (ticker, name)

    selected_label = st.selectbox("Choisir un actif", list(asset_options.keys()))
    ticker, asset_name = asset_options[selected_label]

    if st.button("Analyser", type="primary", use_container_width=True):
        with st.spinner(f"Analyse de {asset_name}…"):
            try:
                data = get_ticker_signal(ticker, asset_name)
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()

        signal = data["signal"]
        confidence = data.get("confidence")
        ai_powered = data.get("ai_powered", False)

        css = {"BUY": "buy", "SELL": "sell", "HOLD": "hold"}[signal]
        label = {"BUY": "🟢 ACHÈTE MAINTENANT", "SELL": "🔴 VENDS TOUT", "HOLD": "⏸ ATTENDS"}[signal]
        conf_html = f'<div class="signal-conf">Confiance : <b>{confidence}%</b></div>' if confidence else ""
        ema_arrow = "↑" if data["ema_short"] > data["ema_long"] else "↓"

        st.markdown(f"""
<div class="signal-card {css}">
  <div class="signal-label">{label}</div>
  {conf_html}
  <div class="signal-price">{data['close']:,.2f}</div>
  <div class="signal-meta">RSI {data['rsi']:.1f} &nbsp;·&nbsp; EMA{EMA_SHORT} {data['ema_short']:,.2f} &nbsp;·&nbsp; EMA{EMA_LONG} {data['ema_long']:,.2f} {ema_arrow}</div>
</div>""", unsafe_allow_html=True)

        if data.get("reason"):
            icon = "🤖 IA" if ai_powered else "📊 Règles"
            st.markdown(f'<div class="ai-box"><b>{icon} :</b> {data["reason"]}</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="ts">Bougie 1h · {data["candle_time"]}</div>', unsafe_allow_html=True)

        if signal == "BUY":
            st.success("➡️ Va acheter cet actif sur eToro maintenant.")
        elif signal == "SELL":
            st.error("➡️ Va vendre cet actif sur eToro maintenant.")

        # Chart
        with st.spinner("Chargement du graphique…"):
            fig = build_chart(ticker, asset_name, signal)
        if fig:
            st.plotly_chart(fig, use_container_width=True)


# ── TAB 3 : EXÉCUTER (crypto testnet) ────────────────────────────────────────
with tab3:
    st.markdown("### ⚡ Exécution crypto")
    st.caption("Ordres sur Binance Testnet — simulation, aucun argent réel.")

    col1, col2 = st.columns([3, 2])
    with col1:
        choix = st.selectbox("Actif crypto", list(SUPPORTED_SYMBOLS.keys()))
    with col2:
        montant = st.number_input("Capital USDT", min_value=10.0, value=100.0, step=10.0)
    symbol = SUPPORTED_SYMBOLS[choix]

    col_buy, col_sell = st.columns(2)
    with col_buy:
        if st.button("🟢 ACHETER", use_container_width=True, type="primary"):
            with st.spinner("Exécution…"):
                try:
                    r = place_market_buy(symbol, montant)
                    st.success(f"✅ Acheté {r['qty']} {symbol.split('/')[0]} @ {r['estimated_price']:,.2f}")
                    c1, c2 = st.columns(2)
                    c1.metric("🛡 Stop Loss", f"{r['stop_loss_price']:,.2f}")
                    c2.metric("🎯 Take Profit", f"{r['take_profit_price']:,.2f}")
                except Exception as e:
                    st.error(f"Erreur : {e}")

    with col_sell:
        if st.button("🔴 VENDRE TOUT", use_container_width=True):
            with st.spinner("Exécution…"):
                try:
                    r = place_market_sell_all(symbol)
                    if r.get("status") == "skipped — no balance":
                        st.warning("Aucun actif à vendre.")
                    else:
                        st.success(f"✅ Vendu {r['qty']} {symbol.split('/')[0]}")
                except Exception as e:
                    st.error(f"Erreur : {e}")

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💰 Solde", use_container_width=True):
            try:
                usdt = get_balance("USDT")
                base = symbol.split("/")[0]
                st.info(f"USDT : **{usdt:,.2f}** | {base} : **{get_balance(base):.6f}**")
            except Exception as e:
                st.error(f"Erreur : {e}")
    with col_b:
        if st.button("🔄 Prix live", use_container_width=True):
            try:
                st.info(f"**{symbol}** : {get_current_price(symbol):,.2f} USD")
            except Exception as e:
                st.error(f"Erreur : {e}")

    with st.expander("⚙️ Paramètres"):
        c1, c2, c3 = st.columns(3)
        c1.metric("Stop Loss", f"{STOP_LOSS_PCT*100:.0f}%")
        c2.metric("Take Profit", f"{TAKE_PROFIT_PCT*100:.0f}%")
        c3.metric("EMA", f"{EMA_SHORT}/{EMA_LONG}")
        st.code("BINANCE_TESTNET_API_KEY\nBINANCE_TESTNET_SECRET\nANTHROPIC_API_KEY")
