"""
Synthèse quotidienne via FantasyAI.cloud.

Envoie les articles patrimoniaux des dernières 24h par **lots de 40** à l'IA,
puis fusionne les résultats. Chaque lot fait un prompt de ~10k tokens (stable
pour tous les modèles, y compris Opus). L'appel de fusion final produit la
synthèse structurée complète.

En cas d'échec total, retourne un digest minimal (liste brute par catégorie).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from typing import Any

import httpx

from fetcher import Article
from prompts.digest_prompt import DIGEST_BATCH_PROMPT, DIGEST_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

FANTASYAI_API_KEY = os.environ.get("FANTASYAI_API_KEY", "")
FANTASYAI_BASE_URL = "https://fantasyai.cloud/api/v1"
DIGEST_FALLBACK_MODELS = [
    "claude-opus-4-8",
    "claude-3-5-sonnet-20241022",
    "gpt-4o",
    "deepseek-v4",
]
MAX_TOKENS_DIGEST = 100000
MAX_INPUT_ARTICLES = 250
REQUEST_TIMEOUT = 120
BATCH_SIZE = 40
MAX_CONCURRENT = 5


async def synthesize_digest(
    articles: list[Article],
    date_paris: datetime | None = None,
    max_retries: int = 2,
) -> dict[str, Any]:
    """
    Synthèse quotidienne par lots parallèles + fusion finale.

    Phase 1 : découpe les articles en lots de BATCH_SIZE (∼10k tokens chacun).
              Appels parallèles avec fallback multi-modèles.
    Phase 2 : fusion des lots par un seul appel de synthèse finale.
    """
    if not FANTASYAI_API_KEY:
        logger.error("FANTASYAI_API_KEY not set")
        return _empty_digest(articles)

    if not articles:
        return _empty_digest(articles)

    if date_paris is None:
        date_paris = datetime.now()

    if len(articles) > MAX_INPUT_ARTICLES:
        logger.warning(
            f"Digest: tronque a {MAX_INPUT_ARTICLES} articles (sur {len(articles)})"
        )
        articles = articles[:MAX_INPUT_ARTICLES]

    # Phase 1 : lots parallèles
    batches = [
        articles[i : i + BATCH_SIZE] for i in range(0, len(articles), BATCH_SIZE)
    ]
    logger.info(
        f"Digest: {len(articles)} articles en {len(batches)} lots de {BATCH_SIZE}"
    )

    sem = asyncio.Semaphore(MAX_CONCURRENT)

    async def process_batch(
        batch: list[Article], idx: int
    ) -> dict[str, Any] | None:
        async with sem:
            return await _analyze_batch_via_fallback(batch, idx, max_retries)

    tasks = [process_batch(batch, i) for i, batch in enumerate(batches)]
    batch_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Collecte les items valides
    all_items: list[dict] = []
    batch_syntheses: list[str] = []
    for i, result in enumerate(batch_results):
        if isinstance(result, Exception):
            logger.error(f"Lot {i} echoue: {result}")
            continue
        if result is None:
            continue
        items = result.get("items", [])
        all_items.extend(items)
        if result.get("synthese_lot"):
            batch_syntheses.append(result["synthese_lot"][:200])

    if not all_items:
        logger.error("Digest: aucun item valide dans les lots")
        return _minimal_fallback_digest(articles, date_paris)

    logger.info(
        f"Digest lots: {len(all_items)} items bruts depuis {len(batches)} lots"
    )

    # Phase 2 : fusion finale
    return await _final_fusion(
        articles, all_items, batch_syntheses, date_paris, max_retries
    )


async def _analyze_batch_via_fallback(
    batch: list[Article], idx: int, max_retries: int
) -> dict[str, Any] | None:
    """Analyse un lot d'articles avec fallback multi-modèles."""
    batch_msg = _build_batch_message(batch)

    for model in DIGEST_FALLBACK_MODELS:
        for attempt in range(1, max_retries + 1):
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": DIGEST_BATCH_PROMPT},
                    {"role": "user", "content": batch_msg},
                ],
                "temperature": 0.1,
                "max_tokens": 4000,
            }
            headers = {
                "Authorization": f"Bearer {FANTASYAI_API_KEY}",
                "Content-Type": "application/json",
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
                        if model != DIGEST_FALLBACK_MODELS[0]:
                            logger.info(
                                f"Lot {idx} via fallback {model} "
                                f"(tentative {attempt})"
                            )
                        return parsed
                    if response.status_code == 503:
                        logger.warning(
                            f"Lot {idx} {model} 503 surcharge "
                            f"(tentative {attempt}/{max_retries})"
                        )
                        await asyncio.sleep(3 * attempt)
                        continue
                    logger.warning(
                        f"Lot {idx} {model} HTTP {response.status_code} "
                        f"-> bascule"
                    )
                    break
            except Exception as e:
                logger.warning(
                    f"Lot {idx} {model} echec "
                    f"(tentative {attempt}/{max_retries}): {e}"
                )
                await asyncio.sleep(2 * attempt)
    return None


async def _final_fusion(
    articles: list[Article],
    all_items: list[dict],
    batch_syntheses: list[str],
    date_paris: datetime,
    max_retries: int,
) -> dict[str, Any]:
    """Fusion finale : envoie les items collectés à l'IA pour produire le digest structuré."""

    fusion_msg = _build_fusion_message(all_items, batch_syntheses, articles, date_paris)

    for model in DIGEST_FALLBACK_MODELS:
        for attempt in range(1, max_retries + 1):
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": DIGEST_SYSTEM_PROMPT},
                    {"role": "user", "content": fusion_msg},
                ],
                "temperature": 0.1,
                "max_tokens": MAX_TOKENS_DIGEST,
            }
            headers = {
                "Authorization": f"Bearer {FANTASYAI_API_KEY}",
                "Content-Type": "application/json",
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
                        parsed["compte_articles"] = len(articles)
                        logger.info(
                            f"Digest fusion OK ({model}): "
                            f"{len(parsed.get('sections', []))} sections, "
                            f"{len(all_items)} items"
                        )
                        return parsed
                    if response.status_code == 503:
                        logger.warning(
                            f"Fusion {model} 503 surcharge "
                            f"(tentative {attempt}/{max_retries})"
                        )
                        await asyncio.sleep(3 * attempt)
                        continue
                    logger.warning(
                        f"Fusion {model} HTTP {response.status_code}"
                        f"-> bascule"
                    )
                    break
            except Exception as e:
                logger.warning(
                    f"Fusion {model} echec "
                    f"(tentative {attempt}/{max_retries}): {e}"
                )
                await asyncio.sleep(2 * attempt)

    # Fallback si fusion echoue : digest basé sur all_items
    logger.error("Fusion IA: tous les modeles ont echoue")
    return _item_list_digest(articles, all_items, date_paris)


def _build_batch_message(batch: list[Article]) -> str:
    """Message pour l'analyse d'un lot d'articles."""
    parts = [
        f"Lot de {len(batch)} articles financiers a analyser :",
        "=" * 50,
    ]
    for i, a in enumerate(batch, 1):
        parts.append(
            f"\n[{i}] {a.title}\n"
            f"    Source: {a.source_name}\n"
            f"    Resume: {(a.summary or a.content or '')[:300]}"
        )
    parts.append("\n" + "=" * 50)
    parts.append("Produis le JSON des items les plus pertinents pour un CGP.")
    return "\n".join(parts)


def _build_fusion_message(
    all_items: list[dict],
    batch_syntheses: list[str],
    articles: list[Article],
    date_paris: datetime,
) -> str:
    """Message pour la fusion finale : synthèse structurée à partir des items."""
    items_json = json.dumps(all_items[:50], ensure_ascii=False, indent=2)
    syntheses = " | ".join(batch_syntheses[:5]) if batch_syntheses else ""

    return f"""Date : {date_paris.strftime('%A %d %B %Y')}
Nombre total d'articles : {len(articles)}
Nombre d'items extraits : {len(all_items)}

Syntheses des lots : {syntheses}

Items extraits par lots :
{items_json}

Structure le briefing quotidien CGP complet a partir de ces items. Trie par section
thematique, deduplique, et classe par niveau d'impact. Ajoute les chiffres cles et
la synthese de jour. N'invente pas de sources/urls qui ne sont pas dans les items."""


def _item_list_digest(
    articles: list[Article], items: list[dict], date_paris: datetime
) -> dict[str, Any]:
    """Fallback quand la fusion echoue : digest basé sur les items collectés."""
    from collections import defaultdict

    by_niveau: dict[str, list] = defaultdict(list)
    for item in items:
        by_niveau[item.get("niveau", "faible")].append(item)

    return {
        "date_fr": date_paris.strftime("%A %d %B %Y"),
        "compte_articles": len(articles),
        "compte_forts": len(by_niveau.get("fort", [])),
        "compte_moyens": len(by_niveau.get("moyen", [])),
        "synthese_jour": "Synthese IA partielle (fusion indisponible). Consultez les items ci-dessous.",
        "chiffres_cles": [],
        "sections": [
            {
                "titre": "Articles du jour",
                "icone": "📰",
                "niveau_global": "moyen",
                "items": items[:30],
            }
        ],
        "a_surveiller": [],
        "fallback": True,
    }


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
    """Fallback degrade quand l'IA echoue completement."""
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
        "general": ("General", "📰"),
        "legal": ("Reglementation", "📋"),
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
                        "analyse": (a.summary or a.content or "")[:300],
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