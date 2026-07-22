"""
Daily — Génération du briefing quotidien patrimonial.

Tourne à 8h heure de Paris (cron 7h UTC hiver / 6h UTC été).
Étapes :
1. Fetch RSS 24h
2. Pré-filtrage mots-clés
3. Synthèse IA (Opus 4.8)
4. Rendu HTML élégant
5. Sauvegarde : docs/index.html + docs/resumes/YYYY-MM-DD.html (rotation 30 jours)
6. Notification Bark groupante
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
from prefilter import prefilter
from synthesizer import synthesize_digest
from render import render_digest
from notify_digest import send_digest_notification

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("albea_daily")

PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
RESUMES_DIR = DOCS_DIR / "resumes"
ASSETS_DIR = DOCS_DIR / "assets"

LOOKBACK_HOURS = 24
MAX_ARCHIVE_DAYS = 30
# URL publique du digest. Definie par le workflow (0x0.st), peut etre vide
# en local (la notif Bark ne sera pas envoyee dans ce cas).
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").strip()


def get_date_paris() -> datetime:
    """Date courante en heure de Paris (approximation via offset +1/+2)."""
    # Approximation simple : on évite d'ajouter une dépendance à pytz/zoneinfo.
    # Heure d'été (dernier dim mars → dernier dim oct) : UTC+2, sinon UTC+1.
    now_utc = datetime.now(timezone.utc)
    # Heuristique : mois 4-9 (avril à septembre) = +2, sinon +1
    offset = 2 if 4 <= now_utc.month <= 9 else 1
    return now_utc.astimezone(timezone(timedelta(hours=offset)))


async def main() -> int:
    """Point d'entrée principal. Retourne 0 si OK, 1 si erreur."""
    # Mode --notify : re-render avec PUBLIC_URL + envoi notif (pas d'appel IA)
    if "--notify" in sys.argv:
        return await _notify_only()

    logger.info("=== Demarrage briefing quotidien Albea ===")

    if not os.environ.get("FANTASYAI_API_KEY"):
        logger.error("FANTASYAI_API_KEY manquant. Arret.")
        return 1
    if not os.environ.get("BARK_DEVICE_KEY"):
        logger.error("BARK_DEVICE_KEY manquant. Arret.")
        return 1

    date_paris = get_date_paris()
    date_str = date_paris.strftime("%Y-%m-%d")
    logger.info(f"Date Paris : {date_paris.strftime('%A %d %B %Y')}")

    # 1. Fetch RSS
    logger.info("Fetching RSS feeds...")
    all_articles = await fetch_all()
    logger.info(f"Articles bruts : {len(all_articles)}")

    # 2. Filtre 24h
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    recent = [
        a for a in all_articles if a.published is None or a.published >= cutoff
    ]
    logger.info(f"Articles 24h : {len(recent)}")

    # 3. Pré-filtrage patrimonial
    relevant = prefilter(recent)
    logger.info(f"Articles patrimoniaux : {len(relevant)}")

    # 4. Synthèse IA
    logger.info("Synthese IA en cours...")
    digest = await synthesize_digest(relevant, date_paris)
    logger.info(
        f"Digest: {digest.get('compte_articles', 0)} articles, "
        f"{digest.get('compte_forts', 0)} forts, "
        f"{len(digest.get('sections', []))} sections"
    )

    # 5. Rendu HTML
    archive_filename = f"{date_str}.html"
    # L'URL publique est injectee par le workflow (apres upload 0x0.st).
    # Si vide (test local), on met un placeholder pour le rendu HTML.
    page_url = PUBLIC_URL or f"https://0x0.st/local-{date_str}.html"
    html_content = render_digest(digest, page_url)

    # 6. Sauvegarde
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    RESUMES_DIR.mkdir(parents=True, exist_ok=True)

    # Sauvegarde le digest JSON (pour le step notif du workflow, evite un 2e appel IA)
    (DOCS_DIR / "digest.json").write_text(
        json.dumps(digest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Index = la page du jour
    (DOCS_DIR / "index.html").write_text(html_content, encoding="utf-8")
    # Archive datée
    (RESUMES_DIR / archive_filename).write_text(html_content, encoding="utf-8")
    logger.info(f"HTML ecrit : docs/index.html + docs/resumes/{archive_filename}")

    # 7. Rotation archives (garde MAX_ARCHIVE_DAYS plus recentes)
    _rotate_archives(RESUMES_DIR, MAX_ARCHIVE_DAYS)

    # 8. Notification Bark
    if not PUBLIC_URL:
        logger.warning(
            "PUBLIC_URL non defini (workflow n'a pas uploade le HTML) "
            "-> notif non envoyee"
        )
    elif relevant or digest.get("marches_calmes"):
        sent = await send_digest_notification(digest, PUBLIC_URL)
        logger.info(f"Notif digest envoyee : {sent}")
    else:
        logger.info("Pas de notif (rien a signaler)")

    # 9. Met a jour un petit meta fichier (utile pour debug GitHub Pages)
    meta = {
        "derniere_maj": date_paris.isoformat(),
        "compte_articles": digest.get("compte_articles", 0),
        "compte_forts": digest.get("compte_forts", 0),
        "compte_moyens": digest.get("compte_moyens", 0),
        "url": page_url,
    }
    (DOCS_DIR / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    logger.info("=== Fin briefing quotidien ===")
    return 0


async def _notify_only() -> int:
    """Mode --notify : re-render avec PUBLIC_URL + envoi notif. Pas d'appel IA."""
    if not PUBLIC_URL:
        logger.error("--notify: PUBLIC_URL non defini")
        return 1

    digest_file = DOCS_DIR / "digest.json"
    if not digest_file.exists():
        logger.error("--notify: digest.json introuvable (le step IA a echoue ?)")
        return 1

    digest = json.loads(digest_file.read_text(encoding="utf-8"))
    html_content = render_digest(digest, PUBLIC_URL)

    # Re-ecrit index.html avec la vraie URL
    (DOCS_DIR / "index.html").write_text(html_content, encoding="utf-8")

    # Notif Bark
    if digest.get("marches_calmes"):
        sent = await send_digest_notification(digest, PUBLIC_URL)
    else:
        sent = await send_digest_notification(digest, PUBLIC_URL)

    logger.info(f"Notif digest envoyee : {sent}")
    return 0 if sent else 1


def _rotate_archives(resumes_dir: Path, keep: int) -> None:
    """Supprime les archives plus vieilles que `keep` jours."""
    files = sorted(resumes_dir.glob("????-??-??.html"))
    if len(files) <= keep:
        return
    for old in files[: len(files) - keep]:
        try:
            old.unlink()
            logger.info(f"Archive rotationnee : {old.name}")
        except OSError as e:
            logger.warning(f"Impossible de supprimer {old}: {e}")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))