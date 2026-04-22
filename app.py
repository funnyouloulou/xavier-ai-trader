import streamlit as st
from datetime import datetime, timezone
from config import SUPPORTED_SYMBOLS, TESTNET, RSI_OVERSOLD, RSI_OVERBOUGHT, EMA_SHORT, EMA_LONG, STOP_LOSS_PCT
from trading_logic import run_strategy, get_current_price, get_balance, get_signal, compute_indicators

st.set_page_config(page_title="Xavier AI Trader", layout="centered")
st.title("Xavier AI Trader")
st.caption("Stratégie : RSI + EMA {}/{} — {}".format(
    EMA_SHORT, EMA_LONG,
    "Testnet Binance" if TESTNET else "Binance Live"
))
st.write("---")

# --- CONFIGURATION ---
col1, col2 = st.columns(2)
with col1:
    choix = st.selectbox("Actif", list(SUPPORTED_SYMBOLS.keys()))
with col2:
    montant = st.number_input("Capital USDT", min_value=10.0, value=100.0, step=10.0)

symbol = SUPPORTED_SYMBOLS[choix]

# --- INDICATEURS & SIGNAL ---
st.subheader("Signal technique")
if st.button("Analyser les indicateurs"):
    with st.spinner("Calcul RSI + EMA..."):
        try:
            data = get_signal(symbol)
            signal = data["signal"]
            signal_colors = {"BUY": "green", "SELL": "red", "HOLD": "gray"}
            color = signal_colors[signal]

            st.markdown(
                f"**Signal ({datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M UTC')}) :** "
                f":{color}[**{signal}**]"
            )
            st.caption(f"Raison : {data['reason']}")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("RSI (14)", f"{data['rsi']}", delta="survendu" if data['rsi'] < RSI_OVERSOLD else ("suracheté" if data['rsi'] > RSI_OVERBOUGHT else "neutre"))
            c2.metric(f"EMA {EMA_SHORT}", f"{data['ema_short']:,.2f}")
            c3.metric(f"EMA {EMA_LONG}", f"{data['ema_long']:,.2f}")
            c4.metric("Prix actuel", f"{data['close']:,.2f} USDT")

            if data.get("stop_loss_price"):
                st.warning(
                    f"Stop Loss actif : **{data['stop_loss_price']:,.4f} USDT** "
                    f"(entrée à {data.get('entry_price', '?')})"
                )
            if data.get("stop_loss_triggered"):
                st.error("Stop Loss déclenché — vente recommandée.")

        except Exception as e:
            st.error(f"Erreur indicateurs : {e}")

st.write("---")

# --- PRIX EN DIRECT ---
if st.button("Rafraîchir le prix"):
    try:
        price = get_current_price(symbol)
        st.info(f"Prix actuel {symbol} : **{price:,.2f} USDT**")
    except Exception as e:
        st.error(f"Erreur lors de la récupération du prix : {e}")

# --- SOLDE TESTNET ---
if st.button("Voir le solde Testnet"):
    try:
        usdt_balance = get_balance("USDT")
        base = symbol.split("/")[0]
        base_balance = get_balance(base)
        st.info(f"USDT disponible : **{usdt_balance:,.2f}** | {base} disponible : **{base_balance:.6f}**")
    except Exception as e:
        st.error(f"Erreur solde : {e}")

st.write("---")

# --- EXECUTION DE LA STRATEGIE ---
st.subheader("Exécuter la stratégie")
st.warning(
    "En cliquant sur ce bouton, un ordre de marché réel sera passé **sur le Testnet Binance**. "
    "Aucun argent réel n'est engagé."
)

if st.button(f"Lancer la stratégie — {symbol}", type="primary"):
    with st.spinner("Analyse + exécution de l'ordre..."):
        try:
            result = run_strategy(symbol, montant)
            action = result.get("action", result.get("signal"))
            st.success(f"Action exécutée : **{action}**")
            st.caption(f"Raison : {result.get('reason', '')}")

            if action == "BUY":
                c1, c2, c3 = st.columns(3)
                c1.metric("Quantité achetée", f"{result['qty']} {symbol.split('/')[0]}")
                c2.metric("Prix d'entrée", f"{result['estimated_price']:,.2f} USDT")
                c3.metric("Stop Loss", f"{result['stop_loss_price']:,.4f} USDT")
                st.metric("Order ID", result.get("order_id", "N/A"))
                st.metric("Statut", result.get("status", "N/A"))

            elif action == "SELL":
                if result.get("status") == "skipped — no balance":
                    st.warning("Aucun actif à vendre dans le portefeuille Testnet.")
                else:
                    st.metric("Quantité vendue", f"{result['qty']} {symbol.split('/')[0]}")
                    st.metric("Order ID", result.get("order_id", "N/A"))
                    st.metric("Statut", result.get("status", "N/A"))

            else:
                st.info(f"Pas d'action. {result.get('reason', '')}")

        except Exception as e:
            st.error(f"Erreur lors de l'exécution : {e}")
            st.info(
                "Vérifiez que vos variables d'environnement sont configurées :\n"
                "`BINANCE_TESTNET_API_KEY` et `BINANCE_TESTNET_SECRET`"
            )

# --- PARAMETRES TECHNIQUES ---
st.write("---")
with st.expander("Paramètres de la stratégie"):
    st.write(f"Mode : **{'Testnet (simulation)' if TESTNET else 'Live'}**")
    st.write(f"Paire tradée : `{symbol}`")
    col1, col2, col3 = st.columns(3)
    col1.metric("RSI survendu (BUY)", f"< {RSI_OVERSOLD}")
    col2.metric("RSI suracheté (SELL)", f"> {RSI_OVERBOUGHT}")
    col3.metric("Stop Loss", f"{STOP_LOSS_PCT * 100:.0f}%")
    st.write(f"EMA courte / longue : **{EMA_SHORT} / {EMA_LONG}**")
    st.write("Variable d'env requises :")
    st.code("BINANCE_TESTNET_API_KEY\nBINANCE_TESTNET_SECRET")
    st.write("Obtenir des clés Testnet : https://testnet.binance.vision")
