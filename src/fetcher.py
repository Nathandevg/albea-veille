"""
Fetcher RSS parallèle.

Récupère tous les flux RSS définis dans sources.py en parallèle,
avec timeout et gestion d'erreur par flux.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import feedparser
import httpx

from sources import SOURCES

logger = logging.getLogger(__name__)

TIMEOUT = 15  # secondes par flux
MAX_CONCURRENT = 20  # requêtes simultanées max


@dataclass
class Article:
    """Un article normalisé après parsing RSS."""

    title: str
    url: str
    source_name: str
    source_url: str
    category: str
    published: Optional[datetime] = None
    summary: str = ""
    content: str = ""

    @property
    def identifier(self) -> str:
        """Identifiant unique pour déduplication."""
        return self.url or self.title


def _clean_html(raw: str) -> str:
    """Nettoie les balises HTML basiques d'un texte."""
    import re

    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", "", raw)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " ")
    return text.strip()


async def _fetch_one(
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
    source: dict,
) -> list[Article]:
    """Fetch un flux RSS et retourne les articles parsés."""
    articles: list[Article] = []
    url = source["url"]
    category = source["category"]

    async with sem:
        try:
            response = await client.get(url, timeout=TIMEOUT, follow_redirects=True)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error for {url}: {e}")
            return articles
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return articles

    # feedparser est synchrone, on l'exécute dans un thread
    loop = asyncio.get_running_loop()
    feed = await loop.run_in_executor(None, feedparser.parse, response.text)

    if feed.bozo and not feed.entries:
        logger.warning(f"Invalid feed {url}: {feed.bozo_exception}")
        return articles

    source_name = feed.feed.get("title", url)

    for entry in feed.entries:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()

        if not title:
            continue

        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published = datetime(*entry.published_parsed[:6])
            except (TypeError, ValueError):
                pass
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            try:
                published = datetime(*entry.updated_parsed[:6])
            except (TypeError, ValueError):
                pass

        summary = _clean_html(entry.get("summary", "") or entry.get("description", ""))
        content_raw = ""
        if hasattr(entry, "content"):
            for c in entry.content:
                content_raw += c.get("value", "")
        content = _clean_html(content_raw) or summary

        articles.append(
            Article(
                title=title,
                url=link or "",
                source_name=source_name,
                source_url=url,
                category=category,
                published=published,
                summary=summary,
                content=content,
            )
        )

    logger.debug(f"Fetched {len(articles)} articles from {source_name}")
    return articles


async def fetch_all() -> list[Article]:
    """Fetch tous les flux RSS en parallèle, retourne la liste complète d'articles."""
    sem = asyncio.Semaphore(MAX_CONCURRENT)

    async with httpx.AsyncClient(
        headers={
            "User-Agent": "AlbeaVeille/1.0 (CGP news monitor; +https://albea-patrimoine.fr)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
        timeout=TIMEOUT,
    ) as client:
        tasks = [_fetch_one(client, sem, src) for src in SOURCES]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_articles: list[Article] = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Unexpected error in fetch task: {result}")
        else:
            all_articles.extend(result)

    logger.info(f"Total articles fetched: {len(all_articles)}")
    return all_articles