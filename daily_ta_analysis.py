"""
Analyse marché via TradingAgents (TauricResearch/TradingAgents).
Intégration dans le digest quotidien Albea Veille.

TradingAgents déploie 4 équipes d'agents LLM qui débattent du marché :
- Analystes (fondamental, technique, sentiment, news)
- Chercheurs bull/bear
- Trader (synthèse et décision)
- Risk Manager + Portfolio Manager (validation)

Ce script exécute l'analyse pour des tickers fixés et exporte le résultat
dans un format que le digest daily.py peut ingérer.

Installation préalable (à faire une fois) :
    pip install tradingagents
    # Configurer les clés API dans .env

Utilisation :
    python daily_ta_analysis.py                      # Analyse complète
    python daily_ta_analysis.py --tickers CAC40,OR    # Tickers personnalisés
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("albea_ta")

# Tickers par défaut — grandes capitalisations et ETF suivis par un CGP français.
# Les tickers ETF sont listes (code ISIN ou code bourse selon le marche).
# Les ETF "symbol" peut varier selon le broker ; on utilise les codes Yahoo Finance
# (ce que TradingAgents supporte nativement).
DEFAULT_TICKERS = [
    # === Indices ===
    "^FCHI",  # CAC 40
    "^GSPC",  # S&P 500
    "^FTSE",  # FTSE 100
    "^N225",  # Nikkei 225
    "^STOXX50E",  # Euro Stoxx 50

    # === Grandes capitalisations françaises (CAC 40) ===
    "MC.PA",  # LVMH
    "OR.PA",  # L'Oréal
    "AI.PA",  # Air Liquide
    "BNP.PA",  # BNP Paribas
    "SAN.PA",  # Sanofi
    "TTE.PA",  # TotalEnergies

    # === ETF Actions Monde / US / Europe (Euronext Paris) ===
    "CW8.PA",  # Amundi MSCI World (capitalisation)
    "EWLD.PA",  # Amundi MSCI World (accumulation)
    "SP5.PA",  # Amundi S&P 500
    "ESE.PA",  # Amundi MSCI Emerging Markets
    "500.PA",  # iShares Core MSCI World (IE00B4L5Y983)
    "EUNL.PA",  # iShares Core MSCI World (IE00B0M62Q58)

    # === ETF Thématiques / Obligations (Euronext Paris) ===
    "IB01.PA",  # iShares $ Treasury Bond 1-3yr
    "IEAC.PA",  # iShares € Govt Bond 1-3yr
    "IEAG.PA",  # iShares € Govt Bond 7-10yr
    "SX3E.PA",  # Amundi Stoxx Europe 600
    "IQQH.PA",  # iShares MSCI World Quality Dividend

    # === Crypto ===
    "BTC-USD",  # Bitcoin
    "ETH-USD",  # Ethereum
]

# Fichier de sortie : le digest le lira
OUTPUT_FILE = Path(__file__).parent.parent / "docs" / "trading_agents.json"


def run_ta_analysis(tickers: list[str] | None = None) -> dict:
    """
    Exécute l'analyse TradingAgents pour les tickers donnés.

    Args:
        tickers: Liste de tickers (ex: ["^FCHI", "^GSPC"]).
                 Si None, utilise DEFAULT_TICKERS.

    Returns:
        Dict structuré pour le digest (champ "trading_agents").
    """
    if tickers is None:
        tickers = DEFAULT_TICKERS

    logger.info(f"=== TradingAgents analyse pour {tickers} ===")

    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
    except ImportError:
        logger.warning(
            "tradingagents non installe — simulation d'analyse. "
            "Pour activer: pip install tradingagents"
        )
        return _simulate_analysis(tickers)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    results = {"analyses": [], "tickers": tickers, "date": date_str}

    for ticker in tickers:
        try:
            config = DEFAULT_CONFIG.copy()
            config["deep_think_llm"] = "claude-opus-4-8"
            config["quick_think_llm"] = "claude-3-5-sonnet-20241022"
            config["max_debate_rounds"] = 2

            ta = TradingAgentsGraph(debug=False, config=config)
            _, decision = ta.propagate(ticker, date_str)

            analysis = {
                "ticker": ticker,
                "decision": decision.get("decision", "HOLD"),
                "confidence": str(decision.get("confidence", "N/A")),
                "reasoning": decision.get("reasoning", ""),
                "sentiment": decision.get("sentiment", "NEUTRAL"),
                "risk": decision.get("risk_level", "MEDIUM"),
            }
            logger.info(f"  {ticker}: {analysis['decision']} (confiance: {analysis['confidence']})")
            results["analyses"].append(analysis)

        except Exception as e:
            logger.error(f"  {ticker}: echec — {e}")
            results["analyses"].append({
                "ticker": ticker,
                "decision": "ERROR",
                "confidence": "N/A",
                "reasoning": f"Erreur: {e}",
                "sentiment": "NEUTRAL",
                "risk": "N/A",
            })

    return {"trading_agents": results, "trading_agents_date": date_str}


def _simulate_analysis(tickers: list[str]) -> dict:
    """Analyse simulée quand TradingAgents n'est pas installé."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    results = {"analyses": [], "tickers": tickers, "date": date_str}

    for ticker in tickers:
        results["analyses"].append({
            "ticker": ticker,
            "decision": "HOLD",
            "confidence": "Moyenne",
            "reasoning": "Analyse désactivée — installer tradingagents pour activer l'analyse multi-agents.",
            "sentiment": "NEUTRAL",
            "risk": "N/A",
        })

    return {"trading_agents": results, "trading_agents_date": date_str}


def save_analysis(data: dict) -> str:
    """Sauvegarde l'analyse pour que le digest la lise."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    logger.info(f"Analyse sauvegardee dans {OUTPUT_FILE}")
    return str(OUTPUT_FILE)


def load_analysis() -> dict:
    """Charge l'analyse depuis le fichier (utilisé par daily.py)."""
    if not OUTPUT_FILE.exists():
        return {}
    return json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    tickers = DEFAULT_TICKERS
    if "--tickers" in sys.argv:
        idx = sys.argv.index("--tickers")
        tickers = sys.argv[idx + 1].split(",")

    result = run_ta_analysis(tickers)
    path = save_analysis(result)

    print(f"Analyse TradingAgents sauvegardee dans {path}")
    for a in result.get("trading_agents", {}).get("analyses", []):
        print(f"  {a['ticker']}: {a['decision']} (confiance: {a['confidence']})")