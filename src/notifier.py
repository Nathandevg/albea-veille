"""
Notifier via Bark.

Envoie des push notifications sur iPhone via l'API Bark
(open source, gratuite, app iOS disponible sur l'App Store).
"""

from __future__ import annotations

import logging
import os
import urllib.parse

import httpx

from analyzer import AnalysisResult

logger = logging.getLogger(__name__)

BARK_DEVICE_KEY = os.environ.get("BARK_DEVICE_KEY", "")
BARK_BASE_URL = "https://api.day.app"

MAX_NOTIFICATIONS_PER_RUN = 10  # Pour éviter le spam


async def send_notifications(results: list[AnalysisResult]) -> int:
    """
    Envoie les notifications push pour les articles à impact.

    Returns:
        Nombre de notifications envoyées avec succès.
    """
    if not BARK_DEVICE_KEY:
        logger.error("BARK_DEVICE_KEY not set. Cannot send notifications.")
        return 0

    if not results:
        logger.info("No impactful articles to notify.")
        return 0

    # Limiter le nombre de notifs par run
    to_notify = results[:MAX_NOTIFICATIONS_PER_RUN]
    if len(results) > MAX_NOTIFICATIONS_PER_RUN:
        logger.warning(
            f"Limiting to {MAX_NOTIFICATIONS_PER_RUN} notifications "
            f"(had {len(results)} impactful articles)"
        )

    sent = 0
    async with httpx.AsyncClient(timeout=10) as client:
        for result in to_notify:
            try:
                success = await _send_one(client, result)
                if success:
                    sent += 1
            except Exception as e:
                logger.error(f"Failed to notify for '{result.article.title[:60]}': {e}")

    logger.info(f"Sent {sent}/{len(to_notify)} push notifications")
    return sent


async def _send_one(client: httpx.AsyncClient, result: AnalysisResult) -> bool:
    """Envoie une notification pour un article."""
    niveau_emoji = {"faible": "ℹ️", "moyen": "⚠️", "fort": "🔴"}

    title = f"{niveau_emoji.get(result.niveau, '📰')} [{result.niveau.upper()}] {result.resume}"

    # Corps : analyse + source
    body = result.analyse
    if len(body) > 500:
        body = body[:497] + "..."

    # URL encodée pour le titre et le corps
    url = f"{BARK_BASE_URL}/{BARK_DEVICE_KEY}/{urllib.parse.quote(title)}/{urllib.parse.quote(body)}"

    # Ajouter l'URL de l'article comme paramètre
    if result.article.url:
        url += f"?url={urllib.parse.quote(result.article.url)}"

    # Grouper par catégorie pour éviter le bruit dans les notifs
    url += "&group=AlbeaVeille"

    response = await client.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("code") == 200:
            logger.info(f"Notified: {result.article.title[:80]}")
            return True
        else:
            logger.warning(f"Bark API error: {data.get('message', 'unknown')}")
            return False
    else:
        logger.warning(f"Bark HTTP {response.status_code}: {response.text[:200]}")
        return False