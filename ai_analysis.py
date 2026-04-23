import json
import anthropic
from config import ANTHROPIC_API_KEY

_SYSTEM = """Tu es XAVIER, un expert en trading algorithmique et analyse technique avec 15 ans d'expérience sur les marchés crypto et financiers. Tu es également expert en copy trading et gestion du risque.

Tu analyses des indicateurs techniques et tu donnes des signaux de trading précis et motivés.

Règles d'analyse que tu appliques :
- RSI < 30 : zone de sur-vente → signal d'achat potentiel
- RSI > 70 : zone de sur-achat → signal de vente potentiel
- RSI 30-70 : zone neutre, contexte EMA déterminant
- EMA20 > EMA50 : tendance haussière court terme → favorable à l'achat
- EMA20 < EMA50 : tendance baissière → prudence ou vente
- La confluence RSI survendu + tendance EMA haussière = signal BUY fort
- La confluence RSI suracheté + tendance EMA baissière = signal SELL fort

Tu réponds UNIQUEMENT en JSON valide, sans markdown, sans texte avant ou après."""


def get_ai_signal(symbol: str, indicators: dict) -> dict:
    """Call Claude to get an AI-powered multi-factor trading signal."""
    if not ANTHROPIC_API_KEY:
        return None

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    trend = "HAUSSIÈRE ↑" if indicators["ema_short"] > indicators["ema_long"] else "BAISSIÈRE ↓"
    ema_gap_pct = abs(indicators["ema_short"] - indicators["ema_long"]) / indicators["ema_long"] * 100
    rsi = indicators["rsi"]
    rsi_zone = "SURVENDU 🔴" if rsi < 30 else ("SURACHETÉ 🔴" if rsi > 70 else "NEUTRE ⚪")

    user_msg = f"""Analyse de marché — {symbol} — {indicators['candle_time']}

DONNÉES DE MARCHÉ :
• Prix actuel  : {indicators['close']:.4f} USD
• RSI (14)     : {rsi:.2f}  [{rsi_zone}]
• EMA 20       : {indicators['ema_short']:.4f}
• EMA 50       : {indicators['ema_long']:.4f}
• Tendance EMA : {trend}  (écart {ema_gap_pct:.3f}%)

Génère ton signal en JSON strict :
{{
  "signal": "BUY" | "SELL" | "HOLD",
  "confidence": <entier 0 à 100>,
  "reasoning": "<analyse en 2-3 phrases claires en français, cite les chiffres>"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system=[{
            "type": "text",
            "text": _SYSTEM,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1].lstrip("json").strip() if len(parts) > 1 else raw
    return json.loads(raw)
