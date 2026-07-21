"""
Synthèse quotidienne via FantasyAI.cloud.

Envoie tous les articles patrimoniaux des dernières 24h à Opus 4.8
qui produit un JSON structuré de synthèse pour le CGP.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any

import httpx

from fetcher import Article
from prompts.digest_prompt import DIGEST_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

FANTASYAI_API_KEY = os.environ.get("FANTASYAI_API_KEY", "")
FANTASYAI_BASE_URL = "https://fantasyai.cloud/api/v1"
DIGEST_MODEL = "claude-opus-4-8"
# Fallback en cascade si Opus est surcharge (HTTP 503 "at capacity")
DIGEST_FALLBACK_MODELS = [
    "claude-opus-4-8",
    "claude-3-5-sonnet-20241022",
    "gpt-4o",
    "deepseek-v4",
]
MAX_TOKENS_DIGEST = 100000
MAX_INPUT_ARTICLES = 250  # Cap pour éviter des inputs trop longs
REQUEST_TIMEOUT = 120  # secondes — synthèse = appel long


async def synthesize_digest(
    articles: list[Article],
    date_paris: datetime | None = None,
    max_retries: int = 2,
) -> dict[str, Any]:
    """
    Synthèse quotidienne d'une liste d'articles par Opus 4.8.

    Args:
        articles: Articles patrimoniaux détectés sur 24h.
        date_paris: Date du jour (timezone Paris) pour le header.
        max_retries: Nombre de retries en cas d'échec.

    Returns:
        Dict JSON structuré du digest (cf. DIGEST_SYSTEM_PROMPT).
        En cas d'échec total, retourne un dict minimal {compte_articles: N, synthese_jour: "..."}
    """
    if not FANTASYAI_API_KEY:
        logger.error("FANTASYAI_API_KEY not set")
        return _empty_digest(articles)

    if not articles:
        return _empty_digest(articles)

    if date_paris is None:
        date_paris = datetime.now()

    # Tronque si trop d'articles pour éviter un input > 100k tokens
    if len(articles) > MAX_INPUT_ARTICLES:
        logger.warning(
            f"Digest: tronque a {MAX_INPUT_ARTICLES} articles (sur {len(articles)})"
        )
        articles = articles[:MAX_INPUT_ARTICLES]

    user_message = _build_user_message(articles, date_paris)

    headers = {
        "Authorization": f"Bearer {FANTASYAI_API_KEY}",
        "Content-Type": "application/json",
    }

    # Essaie chaque modele de la liste. Pour chaque modele, on retente
    # `max_retries` fois avant de basculer au suivant. Gere le cas Opus 4.8
    # surcharge (HTTP 503 "temporarily at capacity").
    for model in DIGEST_FALLBACK_MODELS:
        for attempt in range(1, max_retries + 1):
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": DIGEST_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                "temperature": 0.1,
                "max_tokens": MAX_TOKENS_DIGEST,
            }
            try:
                async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                    response = await client.post(
                        f"{FANTASYAI_BASE_URL}/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                    if response.status_code == 200:
                        data = response.json()
                        content = data["choices"][0]["message"]["content"].strip()
                        if content.startswith("```"):
                            content = content.split("\n", 1)[1]
                            if content.endswith("```"):
                                content = content[:-3]
                            content = content.strip()
                        parsed = json.loads(content)
                        if model != DIGEST_MODEL:
                            logger.info(
                                f"Digest synthese OK via fallback {model} "
                                f"(tentative {attempt})"
                            )
                        else:
                            logger.info(
                                f"Digest synthese OK ({model}, "
                                f"tentative {attempt}, "
                                f"{len(parsed.get('sections', []))} sections)"
                            )
                        return parsed
                    # 503 = surcharge : retente
                    if response.status_code == 503:
                        body = response.text[:200]
                        logger.warning(
                            f"Digest IA {model} 503 surcharge "
                            f"(tentative {attempt}/{max_retries}): {body}"
                        )
                        await asyncio.sleep(3 * attempt)
                        continue
                    # Autre erreur : pas la peine de retenter, on bascule
                    body = response.text[:200]
                    logger.warning(
                        f"Digest IA {model} HTTP {response.status_code} "
                        f"-> bascule au modele suivant: {body}"
                    )
                    break
            except Exception as e:
                logger.warning(
                    f"Digest IA {model} echec "
                    f"(tentative {attempt}/{max_retries}): {e}"
                )
                await asyncio.sleep(2 * attempt)
        else:
            # Toutes les tentatives sur ce modele ont echoue, on bascule
            continue

    logger.error(
        f"Digest IA: tous les modeles ont echoue "
        f"(tried {DIGEST_FALLBACK_MODELS})"
    )
    return _minimal_fallback_digest(articles, date_paris)


def _build_user_message(articles: list[Article], date_paris: datetime) -> str:
    """Construit le prompt utilisateur : liste d'articles groupés par catégorie."""
    from collections import defaultdict

    by_cat: dict[str, list[Article]] = defaultdict(list)
    for a in articles:
        by_cat[a.category].append(a)

    parts = [f"Date : {date_paris.strftime('%A %d %B %Y')}", ""]
    parts.append(f"Nombre d'articles a analyser : {len(articles)}")
    parts.append("")
    parts.append("ARTICLES PAR CATEGORIE :")
    parts.append("=" * 60)

    for cat, items in sorted(by_cat.items()):
        parts.append(f"\n## {cat.upper()} ({len(items)} articles)")
        for i, a in enumerate(items, 1):
            parts.append(
                f"\n[{i}] {a.title}\n"
                f"    Source: {a.source_name}\n"
                f"    Date: {a.published.isoformat() if a.published else 'N/A'}\n"
                f"    URL: {a.url}\n"
                f"    Resume: {(a.summary or a.content or '')[:500]}"
            )

    parts.append("")
    parts.append("=" * 60)
    parts.append("Produis maintenant le JSON de synthese du briefing quotidien CGP.")

    return "\n".join(parts)


def _empty_digest(articles: list[Article]) -> dict[str, Any]:
    """Digest vide (aucun article)."""
    return {
        "date_fr": datetime.now().strftime("%A %d %B %Y"),
        "compte_articles": 0,
        "compte_forts": 0,
        "compte_moyens": 0,
        "synthese_jour": "Aucune actualite patrimoniale notable detectee dans les dernieres 24h.",
        "chiffres_cles": [],
        "sections": [],
        "a_surveiller": [],
        "marches_calmes": True,
    }


def _minimal_fallback_digest(
    articles: list[Article], date_paris: datetime
) -> dict[str, Any]:
    """Fallback degrade quand l'IA echoue : liste simple sans analyse."""
    # Grouper par catégorie
    from collections import defaultdict

    by_cat: dict[str, list[Article]] = defaultdict(list)
    for a in articles:
        by_cat[a.category].append(a)

    cat_to_section = {
        "markets": ("Marches financiers", "📈"),
        "institutions": ("Marches financiers", "🏛️"),
        "fiscalite": ("Fiscalite", "⚖️"),
        "realestate": ("SCPI & Immobilier", "🏠"),
        "assurance": ("Assurance-vie", "🛡️"),
        "private_equity": ("Private equity", "🚀"),
        "retraite": ("Retraite & Epargne salariale", "👴"),
        "reglementation": ("Reglementation", "📋"),
        "esg": ("ESG", "🌱"),
    }

    sections = []
    for cat, items in by_cat.items():
        titre, icone = cat_to_section.get(cat, (cat.title(), "📰"))
        sections.append(
            {
                "titre": titre,
                "icone": icone,
                "niveau_global": "moyen",
                "items": [
                    {
                        "titre": a.title[:80],
                        "analyse": a.summary[:300] if a.summary else "",
                        "source": a.source_name,
                        "url": a.url,
                        "niveau": "moyen",
                    }
                    for a in items[:8]
                ],
            }
        )

    return {
        "date_fr": date_paris.strftime("%A %d %B %Y"),
        "compte_articles": len(articles),
        "compte_forts": 0,
        "compte_moyens": len(articles),
        "synthese_jour": "Synthese IA non disponible (fallback). Consultez les articles ci-dessous.",
        "chiffres_cles": [],
        "sections": sections,
        "a_surveiller": [],
        "fallback": True,
    }