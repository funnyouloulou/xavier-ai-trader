import streamlit as st
from datetime import datetime, timezone
from config import SUPPORTED_SYMBOLS, TESTNET
from trading_logic import run_strategy, get_current_price, get_balance, get_today_signal

st.set_page_config(page_title="Xavier AI Trader", layout="centered")
st.title("Xavier AI Trader")
st.caption("Stratégie : Achat Lundi / Vente Mardi — " + ("Testnet Binance" if TESTNET else "Binance Live"))
st.write("---")

# --- CONFIGURATION ---
col1, col2 = st.columns(2)
with col1:
    choix = st.selectbox("Actif", list(SUPPORTED_SYMBOLS.keys()))
with col2:
    montant = st.number_input("Capital USDT", min_value=10.0, value=100.0, step=10.0)

symbol = SUPPORTED_SYMBOLS[choix]

# --- SIGNAL DU JOUR ---
signal = get_today_signal()
signal_colors = {"BUY": "green", "SELL": "orange", "HOLD": "gray"}
st.markdown(
    f"**Signal du jour ({datetime.now(timezone.utc).strftime('%A %d/%m/%Y UTC')}) :** "
    f":{signal_colors[signal]}[{signal}]"
)

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

if st.button(f"Lancer la stratégie — {signal} {symbol}", type="primary"):
    with st.spinner("Envoi de l'ordre..."):
        try:
            result = run_strategy(symbol, montant)

            st.success(f"Action exécutée : **{result.get('action', signal)}**")

            if result.get("action") == "BUY":
                st.metric("Quantité achetée", f"{result['qty']} {symbol.split('/')[0]}")
                st.metric("Prix estimé", f"{result['estimated_price']:,.2f} USDT")
                st.metric("Order ID", result.get("order_id", "N/A"))
                st.metric("Statut", result.get("status", "N/A"))

            elif result.get("action") == "SELL":
                if result.get("status") == "skipped — no balance":
                    st.warning("Aucun actif à vendre dans le portefeuille Testnet.")
                else:
                    st.metric("Quantité vendue", f"{result['qty']} {symbol.split('/')[0]}")
                    st.metric("Order ID", result.get("order_id", "N/A"))
                    st.metric("Statut", result.get("status", "N/A"))

            else:
                st.info(result.get("message", "Pas d'action aujourd'hui."))

        except Exception as e:
            st.error(f"Erreur lors de l'exécution : {e}")
            st.info(
                "Vérifiez que vos variables d'environnement sont configurées :\n"
                "`BINANCE_TESTNET_API_KEY` et `BINANCE_TESTNET_SECRET`"
            )

# --- PARAMETRES TECHNIQUES ---
st.write("---")
with st.expander("Paramètres techniques"):
    st.write(f"Mode : **{'Testnet (simulation)' if TESTNET else 'Live'}**")
    st.write(f"Paire tradée : `{symbol}`")
    st.write("Dépôt GitHub : `funnyouloulou/xavier-ai-trader`")
    st.write("Variable d'env requises :")
    st.code("BINANCE_TESTNET_API_KEY\nBINANCE_TESTNET_SECRET")
    st.write("Obtenir des clés Testnet : https://testnet.binance.vision")
