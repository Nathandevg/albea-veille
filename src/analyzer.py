"""
Analyse IA via FantasyAI.cloud.

Envoie chaque article à l'API FantasyAI.cloud avec un prompt spécialisé
CGP. Retourne une évaluation d'impact structurée en JSON.

Système de fallback : si un modèle échoue (HTTP error, timeout, JSON cassé),
on bascule automatiquement sur le modèle suivant de la liste.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass

import httpx

from fetcher import Article

logger = logging.getLogger(__name__)

FANTASYAI_API_KEY = os.environ.get("FANTASYAI_API_KEY", "")
FANTASYAI_BASE_URL = "https://fantasyai.cloud/api/v1"
MAX_TOKENS = 100000  # Budget illimité : laisse le modèle développer une analyse complète

# Modèles testés dans l'ordre. Si l'un échoue (erreur/timeout/JSON cassé),
# on bascule sur le suivant. Opus 4.8 d'abord (meilleure analyse), puis
# Sonnet 3.5 (rapide/fiable), puis fallbacks OpenAI/DeepSeek.
FALLBACK_MODELS = [
    "claude-opus-4-8",
    "claude-3-5-sonnet-20241022",
    "gpt-4o",
    "deepseek-v4",
]

# Prompt système pour l'analyse d'impact CGP (qualité maximale)
SYSTEM_PROMPT = """Tu es un analyste patrimonial senior travaillant pour un CGP (Conseiller en Gestion de Patrimoine) chez Albea Patrimoine. Ton analyse doit être experte, concrète et directement actionnable.

Domaines d'activité du CGP :
- SCPI (Sociétés Civiles de Placement Immobilier, pierre papier)
- Assurance-vie (fonds euros, unités de compte, multisupport, rachat)
- Private equity (FIP, FCPI, FPCI, capital investissement, non-coté)
- Immobilier (LMNP, Pinel, Denormandie, Malraux, déficit foncier, crédit)
- Fiscalité (IFI, flat tax/PFU, plus-values, donation, succession, transmission, pacte Dutreil)
- Épargne salariale (PEE, PERCO, intéressement, participation)
- Retraite (PER, Madelin, réformes, âge de départ)
- Marchés financiers (actions, obligations, taux, devises, matières premières)
- Réglementation (AMF, ACPR, MiFID II, DDA, conformité, démarchage)
- Placements alternatifs (or, vin, art, crowdfunding immo)

Pour chaque article, fournis une analyse approfondie :

1. "impact" : true si l'article a un impact direct ou indirect sur l'activité du CGP ou les portefeuilles clients, false sinon.
2. "niveau" : "faible" (contexte macro sans action immédiate), "moyen" (à surveiller, impact partiel), "fort" (action recommandée rapidement).
3. "resume" : résumé factuel de l'actualité en 1-2 phrases.
4. "analyse" : analyse détaillée de l'impact concret (4-6 phrases) — mécanismes en jeu, qui est impacté (quels profils clients / quels produits), sens et ampleur de l'impact, horizon temporel.
5. "recommandation" : action concrète et immédiate recommandée au CGP (2-3 phrases) — que faire, pour quels clients, sur quels produits. Sois opérationnel, pas générique.
6. "secteurs" : liste des secteurs impactés parmi : SCPI, assurance-vie, private-equity, immobilier, fiscalite, epargne-salariale, retraite, marches, reglementation, alternatifs.

Réponds UNIQUEMENT en JSON valide, sans markdown, sans texte avant ou après :
{"impact": true/false, "niveau": "faible/moyen/fort", "resume": "...", "analyse": "...", "recommandation": "...", "secteurs": ["..."]}"""


@dataclass
class AnalysisResult:
    """Résultat d'analyse IA d'un article."""

    article: Article
    impact: bool
    niveau: str  # "faible", "moyen", "fort"
    resume: str
    analyse: str
    recommandation: str = ""
    secteurs: list = None
    model: str = ""
    raw_response: str = ""


async def analyze_articles(
    articles: list[Article],
    max_concurrent: int = 8,
    timeout: int = 60,
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
            return await _analyze_with_fallback(article, timeout)

    tasks = [_analyze_one(a) for a in articles]
    raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(raw_results):
        if isinstance(result, Exception):
            logger.error(f"Analysis failed for '{articles[i].title[:80]}': {result}")
        elif result is not None:
            results.append(result)

    logger.info(f"IA analysis: {len(results)} results from {len(articles)} articles")
    return results


async def _analyze_with_fallback(article: Article, timeout: int) -> AnalysisResult | None:
    """
    Essaie chaque modèle de FALLBACK_MODELS jusqu'à obtenir une analyse valide.
    Bascule au suivant si : HTTP error, timeout, ou JSON cassé.
    """
    for model in FALLBACK_MODELS:
        result = await _call_fantasyai(article, model, timeout)
        if result is not None:
            return result
        # Sinon on essaie le modèle suivant
    logger.warning(
        f"All models failed for '{article.title[:60]}' (tried {len(FALLBACK_MODELS)})"
    )
    return None


async def _call_fantasyai(
    article: Article, model: str, timeout: int
) -> AnalysisResult | None:
    """Appelle FantasyAI.cloud pour un article avec un modèle donné. Retourne
    None si l'appel ou le parsing échoue (pour déclencher le fallback)."""
    user_message = f"""Article :
Titre : {article.title}
Source : {article.source_name}
Date : {article.published.isoformat() if article.published else 'Non spécifiée'}
Catégorie : {article.category}
Contenu : {article.summary[:1500]}

{article.content[:1500] if article.content else ''}"""

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.1,
        "max_tokens": MAX_TOKENS,
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
            if response.status_code != 200:
                body = response.text[:200]
                logger.warning(
                    f"FantasyAI HTTP {response.status_code} ({model}) "
                    f"for '{article.title[:60]}': {body}"
                )
                return None
            data = response.json()
        except Exception as e:
            logger.warning(
                f"FantasyAI call failed ({model}) for '{article.title[:60]}': {e}"
            )
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
        result = AnalysisResult(
            article=article,
            impact=parsed.get("impact", False),
            niveau=parsed.get("niveau", "faible"),
            resume=parsed.get("resume", ""),
            analyse=parsed.get("analyse", ""),
            recommandation=parsed.get("recommandation", ""),
            secteurs=parsed.get("secteurs", []) or [],
            model=model,
            raw_response=content,
        )
        if model != FALLBACK_MODELS[0]:
            logger.info(
                f"Analyzed via fallback model {model}: '{article.title[:60]}'"
            )
        return result
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.warning(
            f"Failed to parse response ({model}) for '{article.title[:60]}': {e}"
        )
        return None


def filter_impactful(results: list[AnalysisResult]) -> list[AnalysisResult]:
    """Ne garde que les articles avec impact moyen ou fort."""
    return [r for r in results if r.impact and r.niveau in ("moyen", "fort")]