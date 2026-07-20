"""
Analyse IA via FantasyAI.cloud.

Envoie chaque article à l'API FantasyAI.cloud avec un prompt spécialisé
CGP. Retourne une évaluation d'impact structurée en JSON.
"""

import json
import logging
import os
from dataclasses import dataclass

import httpx

from fetcher import Article

logger = logging.getLogger(__name__)

FANTASYAI_API_KEY = os.environ.get("FANTASYAI_API_KEY", "")
FANTASYAI_BASE_URL = "https://api.fantasyai.cloud/v1"

# Prompt système pour l'analyse d'impact CGP
SYSTEM_PROMPT = """Tu es un analyste patrimonial expert travaillant pour un CGP (Conseiller en Gestion de Patrimoine) chez Albea Patrimoine.

Ton rôle : analyser des articles d'actualité financière et déterminer leur impact concret pour le métier de CGP.

Domaines d'activité du CGP :
- SCPI (Sociétés Civiles de Placement Immobilier)
- Assurance-vie (fonds euros, unités de compte, multisupport)
- Private equity (FIP, FCPI, FPCI, capital investissement)
- Immobilier (LMNP, Pinel, Denormandie, Malraux, déficit foncier)
- Fiscalité (IFI, flat tax, plus-values, donation, succession, transmission)
- Épargne salariale (PEE, intéressement, participation)
- Retraite (PER, Madelin, réformes)
- Marchés financiers (actions, obligations, taux)
- Réglementation (AMF, ACPR, MiFID, DDA)

Pour chaque article, évalue :
1. S'il a un impact direct ou indirect sur l'activité de CGP
2. Le niveau d'impact (faible/moyen/fort)
3. Un résumé en une phrase
4. Une analyse de 2-3 phrases expliquant l'impact concret pour le CGP et ses clients

Réponds UNIQUEMENT en JSON valide, sans markdown, sans texte avant ou après :
{"impact": true/false, "niveau": "faible/moyen/fort", "resume": "...", "analyse": "..."}"""


@dataclass
class AnalysisResult:
    """Résultat d'analyse IA d'un article."""

    article: Article
    impact: bool
    niveau: str  # "faible", "moyen", "fort"
    resume: str
    analyse: str
    raw_response: str = ""


async def analyze_articles(
    articles: list[Article],
    max_concurrent: int = 5,
    timeout: int = 30,
) -> list[AnalysisResult]:
    """
    Analyse une liste d'articles via FantasyAI.cloud.

    Args:
        articles: Liste d'articles à analyser.
        max_concurrent: Nombre max d'appels API simultanés.
        timeout: Timeout par appel API en secondes.
    """
    if not FANTASYAI_API_KEY:
        logger.error("FANTASYAI_API_KEY not set. Cannot analyze articles.")
        return []

    if not articles:
        return []

    import asyncio

    results: list[AnalysisResult] = []
    sem = asyncio.Semaphore(max_concurrent)

    async def _analyze_one(article: Article) -> AnalysisResult | None:
        async with sem:
            return await _call_fantasyai(article, timeout)

    tasks = [_analyze_one(a) for a in articles]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(raw_results):
        if isinstance(result, Exception):
            logger.error(f"Analysis failed for '{articles[i].title[:80]}': {result}")
        elif result is not None:
            results.append(result)

    logger.info(f"IA analysis: {len(results)} results from {len(articles)} articles")
    return results


async def _call_fantasyai(article: Article, timeout: int) -> AnalysisResult | None:
    """Appelle FantasyAI.cloud pour un article."""
    user_message = f"""Article :
Titre : {article.title}
Source : {article.source_name}
Date : {article.published.isoformat() if article.published else 'Non spécifiée'}
Catégorie : {article.category}
Contenu : {article.summary[:1500]}

{article.content[:1500] if article.content else ''}"""

    payload = {
        "model": "claude-opus-4-8",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.1,
        "max_tokens": 300,
    }

    headers = {
        "Authorization": f"Bearer {FANTASYAI_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.post(
                f"{FANTASYAI_BASE_URL}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            logger.warning(f"FantasyAI HTTP error for '{article.title[:60]}': {e}")
            return None
        except Exception as e:
            logger.warning(f"FantasyAI call failed for '{article.title[:60]}': {e}")
            return None

    try:
        content = data["choices"][0]["message"]["content"].strip()
        # Nettoie le markdown éventuel (```json ... ```)
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        parsed = json.loads(content)
        return AnalysisResult(
            article=article,
            impact=parsed.get("impact", False),
            niveau=parsed.get("niveau", "faible"),
            resume=parsed.get("resume", ""),
            analyse=parsed.get("analyse", ""),
            raw_response=content,
        )
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.warning(f"Failed to parse FantasyAI response for '{article.title[:60]}': {e}")
        logger.debug(f"Raw response: {data.get('choices', [{}])[0].get('message', {}).get('content', '')[:200]}")
        return None


def filter_impactful(results: list[AnalysisResult]) -> list[AnalysisResult]:
    """Ne garde que les articles avec impact moyen ou fort."""
    return [r for r in results if r.impact and r.niveau in ("moyen", "fort")]