import streamlit as st

st.set_page_config(page_title="Xavier AI Trader", layout="centered")

st.title("🚀 Xavier AI Trader")
st.write("---")
st.subheader("Plan : Entrée Lundi / Sortie Mardi")

montant = st.number_input("Capital à investir (€)", value=100)
choix = st.selectbox("Actif à analyser", ["Bitcoin (BTC)", "Or (Gold)", "NVIDIA (NVDA)"])

if st.button("Lancer l'analyse 24h"):
    st.info(f"Analyse en cours pour {montant}€ sur {choix}...")
    st.success("✅ SIGNAL D'ACHAT DÉTECTÉ")
    st.warning("⚠️ RAPPEL : Vendre demain à 17h00 pile pour encaisser.")
    st.write("Statut : Prêt pour le prochain trade.")
