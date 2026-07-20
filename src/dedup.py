"""
Déduplication des articles.

Élimine les doublons par URL exacte, puis par similarité de titre
(Levenshtein ratio > 90%). La similarité est calculée par bucket
(catégorie) pour éviter une explosion O(n²) sur des volumes élevés.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from difflib import SequenceMatcher

from fetcher import Article

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.90  # 90% de similarité = doublon


def _normalize(title: str) -> str:
    """Normalise un titre pour comparaison."""
    return title.lower().strip().rstrip(".")


def deduplicate(articles: list[Article]) -> list[Article]:
    """
    Déduplique une liste d'articles.

    Étape 1 : dédoublonnage par URL exacte.
    Étape 2 : dédoublonnage par similarité de titre (> 90%), par bucket catégorie.
    """
    if not articles:
        return []

    # Étape 1 : URL exacte
    seen_urls: set[str] = set()
    unique_by_url: list[Article] = []
    for article in articles:
        url = article.url.strip().lower()
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_by_url.append(article)
        elif not url:
            unique_by_url.append(article)

    logger.info(
        f"After URL dedup: {len(unique_by_url)} (removed {len(articles) - len(unique_by_url)})"
    )

    # Étape 2 : similarité de titre, par bucket catégorie
    buckets: dict[str, list[Article]] = defaultdict(list)
    for article in unique_by_url:
        buckets[article.category].append(article)

    result: list[Article] = []
    total_dup = 0
    for category, bucket in buckets.items():
        seen_titles: list[str] = []
        for article in bucket:
            norm_title = _normalize(article.title)
            is_duplicate = False
            for seen in seen_titles:
                if SequenceMatcher(None, norm_title, seen).ratio() >= SIMILARITY_THRESHOLD:
                    is_duplicate = True
                    total_dup += 1
                    break
            if not is_duplicate:
                result.append(article)
                seen_titles.append(norm_title)

    logger.info(f"After title dedup: {len(result)} (removed {total_dup})")

    return result