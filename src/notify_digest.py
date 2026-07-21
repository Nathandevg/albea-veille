"""
Notifier digest : envoie la notification Bark du briefing quotidien 8h.

Une seule notif groupante avec aperçu du digest + lien vers GitHub Pages.
"""

from __future__ import annotations

import logging
import os
import urllib.parse

import httpx

logger = logging.getLogger(__name__)

BARK_DEVICE_KEY = os.environ.get("BARK_DEVICE_KEY", "")
BARK_BASE_URL = "https://api.day.app"


async def send_digest_notification(
    digest: dict,
    page_url: str,
) -> bool:
    """
    Envoie la notif Bark du briefing quotidien.

    Args:
        digest: Dict produit par synthesizer.synthesize_digest().
        page_url: URL canonique de la page HTML (GitHub Pages).

    Returns:
        True si la notif a été envoyée avec succès.
    """
    if not BARK_DEVICE_KEY:
        logger.error("BARK_DEVICE_KEY not set")
        return False

    marches_calmes = digest.get("marches_calmes", False)
    if marches_calmes:
        return await _send_calmes(digest)

    compte_articles = digest.get("compte_articles", 0)
    compte_forts = digest.get("compte_forts", 0)
    compte_moyens = digest.get("compte_moyens", 0)
    sections = digest.get("sections", [])

    # Construit le top 3 des alertes les plus marquantes (sections + 1er item fort)
    top_lines = []
    for sec in sections:
        if sec.get("niveau_global") == "fort":
            for it in sec.get("items", [])[:1]:
                top_lines.append(
                    f"🔴 {sec.get('icone', '')} {it.get('titre', '')[:60]}"
                )
                break
        if len(top_lines) >= 3:
            break

    if not top_lines:
        # sinon, prends les 3 premiers items de n'importe quelle section
        for sec in sections:
            for it in sec.get("items", [])[:1]:
                top_lines.append(
                    f"• {sec.get('icone', '')} {it.get('titre', '')[:60]}"
                )
                break
            if len(top_lines) >= 3:
                break

    title = f"📊 [RESUME QUOTIDIEN] {digest.get('date_fr', 'Aujourd hui')[:30]}"
    body_lines = [
        f"{compte_articles} articles analyses — {compte_forts} forts — {compte_moyens} moyens",
    ]
    if top_lines:
        body_lines.append("")
        body_lines.extend(top_lines[:3])
    body_lines.append("")
    body_lines.append(f"Lire le resume → {page_url}")

    body = "\n".join(body_lines)

    # Encodage safe='' pour éviter les 404 Bark (mêmes leçons que notifier.py)
    url = (
        f"{BARK_BASE_URL}/{BARK_DEVICE_KEY}"
        f"/{urllib.parse.quote(title, safe='')}"
        f"/{urllib.parse.quote(body, safe='')}"
        f"?url={urllib.parse.quote(page_url, safe='')}"
        f"&group=AlbeaVeilleDigest"
        f"&icon=https://raw.githubusercontent.com/Nathandevg/albea-veille/main/docs/assets/icon.png"
        f"&sound=bell"
    )

    # Priorité timeSensitive si au moins 1 impact fort
    if compte_forts > 0:
        url += "&level=timeSensitive"

    return await _send(url, "digest")


async def _send_calmes(digest: dict) -> bool:
    """Notif minimale si aucun article."""
    title = f"🤷 [RESUME] {digest.get('date_fr', 'Aujourd hui')[:30]}"
    body = "Aucune actualite patrimoniale notable. A demain."

    url = (
        f"{BARK_BASE_URL}/{BARK_DEVICE_KEY}"
        f"/{urllib.parse.quote(title, safe='')}"
        f"/{urllib.parse.quote(body, safe='')}"
        f"&group=AlbeaVeilleDigest"
        f"&sound=bird"
    )
    return await _send(url, "calmes")


async def _send(url: str, kind: str) -> bool:
    """Envoi générique avec log."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 200:
                logger.info(f"Notif digest envoyee ({kind})")
                return True
            else:
                logger.warning(f"Bark API error ({kind}): {data.get('message')}")
        else:
            logger.warning(
                f"Bark HTTP {response.status_code} ({kind}): {response.text[:200]}"
            )
    except Exception as e:
        logger.error(f"Bark send failed ({kind}): {e}")
    return False