import streamlit as st
from datetime import datetime, timezone
from config import (
    SUPPORTED_SYMBOLS, TESTNET,
    EMA_SHORT, EMA_LONG,
    STOP_LOSS_PCT, TAKE_PROFIT_PCT,
    AUTO_REFRESH_SECONDS,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
)
from trading_logic import get_current_price, get_balance, place_market_buy, place_market_sell_all
from scanner import scan_markets, get_ticker_signal, build_chart, WATCHLIST, TOTAL_ASSETS
import portfolio as pf
import signal_history as sh
from notifications import notify_signal

st.set_page_config(
    page_title="Xavier AI Trader",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.block-container { padding: 1rem 1rem 2rem; max-width: 500px; }

.signal-card { border-radius:18px; padding:24px 20px 18px; text-align:center; margin:10px 0 6px; box-shadow:0 4px 20px rgba(0,0,0,.2); }
.signal-card.buy  { background:linear-gradient(135deg,#00c853,#1b5e20); }
.signal-card.sell { background:linear-gradient(135deg,#e53935,#7f0000); }
.signal-card.hold { background:linear-gradient(135deg,#455a64,#1c313a); }
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
.opp-tf   { font-size:.75rem; color:#666; margin-top:2px; }

.pnl-pos { color:#00c853; font-weight:700; }
.pnl-neg { color:#e53935; font-weight:700; }
.pos-card { background:#111827; border-radius:12px; padding:14px 16px; margin:8px 0; }

.ai-box { background:#0f0f1a; border-left:4px solid #7c4dff; border-radius:10px; padding:12px 16px; color:#d0d0e8; font-size:.9rem; line-height:1.55; margin:10px 0; }
.ts { font-size:.75rem; color:#666; text-align:center; margin-top:6px; }
.tg-box { background:#0a1929; border:1px solid #1565c0; border-radius:10px; padding:12px 16px; font-size:.85rem; color:#90caf9; margin:8px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 📈 Xavier AI Trader")
st.caption("🔴 TESTNET — simulation" if TESTNET else "🟢 LIVE — Binance")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 Scanner", "📊 Analyser", "💼 Portefeuille", "📋 Historique", "⚡ Exécuter"])


# ── TAB 1 : SCANNER ───────────────────────────────────────────────────────────
with tab1:
    tg_active = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
    if tg_active:
        st.markdown('<div class="tg-box">🔔 Notifications Telegram actives — tu recevras un message dès qu\'un signal fort apparaît.</div>', unsafe_allow_html=True)
    else:
        st.caption("💡 Active les notifications Telegram dans les paramètres pour être alerté sur ton iPhone.")

    @st.fragment(run_every=AUTO_REFRESH_SECONDS)
    def scanner_panel() -> None:
        now = datetime.now(timezone.utc).strftime("%H:%M UTC")
        with st.spinner(f"Scan de {TOTAL_ASSETS} actifs · 3 timeframes…"):
            results = scan_markets()

        # Log history + send notifications
        sh.log(results)
        for r in results:
            notify_signal(r)

        st.markdown(f'<div class="ts">Scan auto toutes les 5 min · {now}</div>', unsafe_allow_html=True)

        if not results:
            st.info("Aucune opportunité forte en ce moment — marchés en consolidation.")
            return

        buys = [r for r in results if r["signal"] == "BUY"]
        sells = [r for r in results if r["signal"] == "SELL"]

        if buys:
            st.markdown(f"### 🟢 À ACHETER ({len(buys)})")
            for r in buys:
                tf_color = "#00c853" if r["tf_count"] == 3 else ("#f9a825" if r["tf_count"] == 2 else "#666")
                st.markdown(f"""
<div class="opp-buy">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div><span class="opp-name">{r['name']}</span><span class="opp-ticker">{r['ticker']} · {r['category']}</span></div>
    <span class="opp-conf-buy">{r['confidence']}%</span>
  </div>
  <div class="opp-meta">Prix <b>{r['close']:,.2f}</b> &nbsp;·&nbsp; RSI <b>{r['rsi']}</b> &nbsp;·&nbsp; EMA {r['ema_trend']}</div>
  <div class="opp-tf" style="color:{tf_color}">⏱ {r['tf_label']}</div>
</div>""", unsafe_allow_html=True)

        if sells:
            st.markdown(f"### 🔴 À VENDRE ({len(sells)})")
            for r in sells:
                tf_color = "#e53935" if r["tf_count"] == 3 else ("#f9a825" if r["tf_count"] == 2 else "#666")
                st.markdown(f"""
<div class="opp-sell">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div><span class="opp-name">{r['name']}</span><span class="opp-ticker">{r['ticker']} · {r['category']}</span></div>
    <span class="opp-conf-sell">{r['confidence']}%</span>
  </div>
  <div class="opp-meta">Prix <b>{r['close']:,.2f}</b> &nbsp;·&nbsp; RSI <b>{r['rsi']}</b> &nbsp;·&nbsp; EMA {r['ema_trend']}</div>
  <div class="opp-tf" style="color:{tf_color}">⏱ {r['tf_label']}</div>
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
        with st.spinner(f"Analyse de {asset_name} sur 3 timeframes…"):
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
  <div class="signal-price">{data['close']:,.4f}</div>
  <div class="signal-meta">RSI {data['rsi']:.1f} &nbsp;·&nbsp; EMA{EMA_SHORT} {data['ema_short']:,.2f} &nbsp;·&nbsp; EMA{EMA_LONG} {data['ema_long']:,.2f} {ema_arrow}</div>
</div>""", unsafe_allow_html=True)

        if data.get("tf_label"):
            st.markdown(f'<div class="opp-tf" style="text-align:center;font-size:.85rem;margin:4px 0">⏱ {data["tf_label"]}</div>', unsafe_allow_html=True)

        if data.get("reason"):
            icon = "🤖 IA" if ai_powered else "📊 Règles"
            st.markdown(f'<div class="ai-box"><b>{icon} :</b> {data["reason"]}</div>', unsafe_allow_html=True)

        if signal == "BUY":
            st.success("➡️ Va acheter cet actif sur eToro maintenant.")
        elif signal == "SELL":
            st.error("➡️ Va vendre cet actif sur eToro maintenant.")

        with st.spinner("Chargement du graphique…"):
            fig = build_chart(ticker, asset_name, signal)
        if fig:
            st.plotly_chart(fig, use_container_width=True)


# ── TAB 3 : PORTEFEUILLE ──────────────────────────────────────────────────────
with tab3:
    st.markdown("### 💼 Mon portefeuille eToro")
    st.caption("Enregistre ici tes positions eToro pour suivre tes P&L en temps réel.")

    portfolio = pf.enrich(pf.load())

    if portfolio:
        total_invested = sum(p["amount_invested"] for p in portfolio)
        total_pnl = sum(p.get("pnl_eur", 0) for p in portfolio)
        pnl_class = "pnl-pos" if total_pnl >= 0 else "pnl-neg"
        pnl_sign = "+" if total_pnl >= 0 else ""

        c1, c2 = st.columns(2)
        c1.metric("Investi", f"{total_invested:.2f}€")
        c2.metric("P&L total", f"{pnl_sign}{total_pnl:.2f}€")

        for p in portfolio:
            pnl_eur = p.get("pnl_eur", 0)
            pnl_pct = p.get("pnl_pct", 0)
            current = p.get("current_price", "—")
            sign = "+" if pnl_eur >= 0 else ""
            pnl_col = "#00c853" if pnl_eur >= 0 else "#e53935"
            sl_alert = " 🚨 STOP LOSS ATTEINT" if p.get("sl_hit") else ""
            tp_alert = " 🎉 TAKE PROFIT ATTEINT" if p.get("tp_hit") else ""

            st.markdown(f"""
<div class="pos-card">
  <div style="display:flex;justify-content:space-between">
    <div><b style="color:#fff">{p['name']}</b> <span style="color:#888;font-size:.8rem">{p['ticker']}</span></div>
    <span style="color:{pnl_col};font-weight:700">{sign}{pnl_eur:.2f}€ ({sign}{pnl_pct:.1f}%)</span>
  </div>
  <div style="color:#aaa;font-size:.82rem;margin-top:6px">
    Acheté à <b>{p['buy_price']}</b> · Actuel <b>{current}</b> · Investi <b>{p['amount_invested']:.2f}€</b>
  </div>
  <div style="color:#666;font-size:.78rem;margin-top:4px">
    🛡 SL {p['stop_loss']} · 🎯 TP {p['take_profit']}{sl_alert}{tp_alert}
  </div>
</div>""", unsafe_allow_html=True)

            if st.button(f"Clôturer {p['name']}", key=f"close_{p['ticker']}"):
                pf.remove_position(p["ticker"])
                st.success(f"Position {p['name']} clôturée.")
                st.rerun()

        st.divider()

    st.markdown("#### Ajouter une position")
    all_assets = {f"{n} ({t})": (t, n) for cat in WATCHLIST.values() for n, t in cat.items()}
    sel = st.selectbox("Actif acheté sur eToro", list(all_assets.keys()), key="pf_sel")
    p_ticker, p_name = all_assets[sel]
    col1, col2 = st.columns(2)
    with col1:
        buy_price = st.number_input("Prix d'achat (€/$)", min_value=0.0001, format="%.4f")
    with col2:
        amount = st.number_input("Montant investi (€)", min_value=1.0, value=10.0)

    if st.button("➕ Ajouter au portefeuille", use_container_width=True, type="primary"):
        pf.add_position(p_name, p_ticker, buy_price, amount)
        st.success(f"Position {p_name} ajoutée !")
        st.rerun()


# ── TAB 4 : HISTORIQUE ────────────────────────────────────────────────────────
with tab4:
    st.markdown("### 📋 Historique des signaux")
    history = sh.load()

    if not history:
        st.info("Aucun signal enregistré encore. Lance le scanner pour commencer.")
    else:
        buys_h = sum(1 for h in history if h["signal"] == "BUY")
        sells_h = sum(1 for h in history if h["signal"] == "SELL")
        c1, c2, c3 = st.columns(3)
        c1.metric("Signaux total", len(history))
        c2.metric("🟢 BUY", buys_h)
        c3.metric("🔴 SELL", sells_h)

        st.divider()
        for h in history[:50]:
            emoji = "🟢" if h["signal"] == "BUY" else "🔴"
            ts = h["ts"][:16].replace("T", " ")
            tf = f" · {h['tf_label']}" if h.get("tf_label") else ""
            conf = f" · {h['confidence']}%" if h.get("confidence") else ""
            rsi = f" · RSI {h['rsi']}" if h.get("rsi") else ""
            price = f" · {h['close']:,.2f}" if h.get("close") else ""
            st.markdown(
                f"{emoji} **{h['name']}** `{h['ticker']}` — {ts}{price}{rsi}{conf}{tf}",
                help=h.get("tf_label", "")
            )


# ── TAB 5 : EXÉCUTER ──────────────────────────────────────────────────────────
with tab5:
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

    st.divider()
    with st.expander("⚙️ Paramètres & configuration"):
        c1, c2, c3 = st.columns(3)
        c1.metric("Stop Loss", f"{STOP_LOSS_PCT*100:.0f}%")
        c2.metric("Take Profit", f"{TAKE_PROFIT_PCT*100:.0f}%")
        c3.metric("EMA", f"{EMA_SHORT}/{EMA_LONG}")

        st.markdown("**Variables Streamlit Secrets :**")
        st.code("BINANCE_TESTNET_API_KEY\nBINANCE_TESTNET_SECRET\nANTHROPIC_API_KEY\nTELEGRAM_BOT_TOKEN\nTELEGRAM_CHAT_ID")

        st.markdown("**Configurer Telegram :**")
        st.markdown("""
1. Ouvre Telegram → cherche **@BotFather** → `/newbot`
2. Copie le token → ajoute `TELEGRAM_BOT_TOKEN` dans Secrets
3. Cherche **@userinfobot** → copie ton ID → ajoute `TELEGRAM_CHAT_ID`
4. Redémarre l'app → les notifications s'activent
""")
        tg_status = "✅ Actif" if tg_active else "❌ Non configuré"
        st.info(f"Statut Telegram : {tg_status}")

        if tg_active:
            if st.button("🔔 Envoyer un message de test", use_container_width=True):
                import requests as _req
                from config import TELEGRAM_BOT_TOKEN as _tok, TELEGRAM_CHAT_ID as _cid
                try:
                    resp = _req.post(
                        f"https://api.telegram.org/bot{_tok}/sendMessage",
                        json={"chat_id": _cid, "text": "🔔 Test Xavier AI Trader — notifications OK ✅", "parse_mode": "HTML"},
                        timeout=8,
                    )
                    if resp.status_code == 200:
                        st.success("Message envoyé ! Vérifie ton Telegram.")
                    else:
                        st.error(f"Erreur {resp.status_code} : {resp.json().get('description', resp.text)}")
                except Exception as e:
                    st.error(f"Erreur réseau : {e}")
