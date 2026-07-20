"""
Main — Orchestration du flux de veille patrimoniale.

Étapes :
1. Fetch parallèle de ~100 flux RSS
2. Déduplication
3. Pré-filtrage par mots-clés
4. Analyse IA (FantasyAI.cloud)
5. Push notifications (Bark) pour les articles à impact
6. Sauvegarde de l'historique
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fetcher import fetch_all
from dedup import deduplicate
from prefilter import prefilter
from analyzer import analyze_articles, filter_impactful
from notifier import send_notifications

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Couper le bruit : httpx log chaque requête HTTP en INFO
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("albea_veille")

HISTORY_FILE = Path(__file__).parent / "history.json"
HISTORY_MAX_AGE_DAYS = 3  # Garder l'historique 3 jours
MAX_ARTICLES_TO_ANALYZE = 30  # Max d'articles envoyés à l'IA par run (maîtrise des coûts)


def load_history() -> set[str]:
    """Charge les URLs/articles déjà traités."""
    if not HISTORY_FILE.exists():
        return set()

    try:
        data = json.loads(HISTORY_FILE.read_text())
        # Nettoyer les entrées trop vieilles
        cutoff = datetime.now(timezone.utc) - timedelta(days=HISTORY_MAX_AGE_DAYS)
        fresh = {
            url
            for url, ts in data.items()
            if datetime.fromisoformat(ts) > cutoff
        }
        return fresh
    except (json.JSONDecodeError, KeyError, ValueError):
        logger.warning("Corrupted history.json, resetting.")
        return set()


def save_history(history: set[str]) -> None:
    """Sauvegarde l'historique avec timestamps."""
    now = datetime.now(timezone.utc).isoformat()
    data = {url: now for url in history}
    HISTORY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


async def main() -> None:
    """Point d'entrée principal."""
    logger.info("=== Démarrage veille patrimoniale Albea ===")

    # Vérification des secrets
    if not os.environ.get("FANTASYAI_API_KEY"):
        logger.error("FANTASYAI_API_KEY manquant. Arrêt.")
        sys.exit(1)
    if not os.environ.get("BARK_DEVICE_KEY"):
        logger.error("BARK_DEVICE_KEY manquant. Arrêt.")
        sys.exit(1)

    # 1. Charger l'historique
    history = load_history()
    logger.info(f"Historique chargé : {len(history)} articles récents")

    # 2. Fetch
    logger.info("Fetching RSS feeds...")
    articles = await fetch_all()
    logger.info(f"Articles bruts : {len(articles)}")

    # 3. Filtrer les articles déjà vus
    new_articles = [a for a in articles if a.identifier not in history]
    logger.info(f"Nouveaux articles (après historique) : {len(new_articles)}")

    if not new_articles:
        logger.info("Aucun nouvel article. Fin.")
        return

    # 4. Déduplication
    unique_articles = deduplicate(new_articles)

    # 5. Pré-filtrage mots-clés
    relevant_articles = prefilter(unique_articles)
    logger.info(f"Articles après pré-filtrage : {len(relevant_articles)}")

    if not relevant_articles:
        logger.info("Aucun article pertinent après pré-filtrage.")
        # Mettre à jour l'historique même si rien à analyser
        for a in new_articles:
            history.add(a.identifier)
        save_history(history)
        return

    # 6. Analyse IA (limiter le volume)
    to_analyze = relevant_articles[:MAX_ARTICLES_TO_ANALYZE]
    if len(relevant_articles) > MAX_ARTICLES_TO_ANALYZE:
        logger.warning(
            f"Limiting IA analysis to {MAX_ARTICLES_TO_ANALYZE} articles "
            f"(had {len(relevant_articles)})"
        )

    logger.info(f"Analyse IA de {len(to_analyze)} articles...")
    analysis_results = await analyze_articles(to_analyze)

    # 7. Filtrer les articles à impact
    impactful = filter_impactful(analysis_results)
    logger.info(f"Articles à impact (moyen/fort) : {len(impactful)}")

    for r in impactful:
        logger.info(f"  [{r.niveau.upper()}] {r.resume}")

    # 8. Envoyer les notifications
    if impactful:
        sent = await send_notifications(impactful)
        logger.info(f"Notifications envoyées : {sent}")
    else:
        logger.info("Aucune notification à envoyer.")

    # 9. Mettre à jour l'historique
    for a in new_articles:
        history.add(a.identifier)
    save_history(history)
    logger.info(f"Historique sauvegardé : {len(history)} entrées")

    logger.info("=== Fin veille patrimoniale ===")


if __name__ == "__main__":
    asyncio.run(main())