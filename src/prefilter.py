"""
Pré-filtrage par mots-clés patrimoniaux.

Filtre gratuit qui élimine ~70% des articles non pertinents
avant d'appeler l'IA, en vérifiant la présence d'au moins un
mot-clé dans le titre ou le résumé.
"""

import logging

from fetcher import Article

logger = logging.getLogger(__name__)

# Mots-clés regroupés par thématique patrimoniale
KEYWORDS: dict[str, list[str]] = {
    "scpi": [
        "SCPI", "société civile de placement immobilier", "pierre papier",
        "rendement SCPI", "parts de SCPI", "sociétés civiles de placement",
    ],
    "assurance_vie": [
        "assurance vie", "assurance-vie", "fonds euros", "fonds en euros",
        "unités de compte", "UC", "rachat", "contrat assurance",
        "contrat d'assurance", "assureur", "multisupport",
    ],
    "fiscalite": [
        "impôt", "IFI", "ISF", "flat tax", "PFU", "prélèvement forfaitaire",
        "plus-value", "plus value", "abattement", "niche fiscale", "PLF",
        "loi de finances", "DMTG", "droits de succession", "donation",
        "transmission", "fiscalité", "fiscal", "défiscalisation",
        "exonération", "crédit d'impôt", "réduction d'impôt",
        "taxe foncière", "taxe d'habitation", "TVA", "IS", "CSG", "CRDS",
    ],
    "immobilier": [
        "immobilier", "prix m2", "taux crédit", "taux d'intérêt",
        "PTZ", "Pinel", "Denormandie", "LMNP", "Malraux", "déficit foncier",
        "logement", "marché immobilier", "construction", "promoteur",
        "notaire", "frais de notaire",
    ],
    "retraite": [
        "retraite", "PER", "PERP", "PERCO", "Madelin", "loi Pacte",
        "réforme retraite", "âge départ", "pension", "régime retraite",
        "épargne retraite", "rente", "rente viagère",
    ],
    "private_equity": [
        "private equity", "capital investissement", "FPCI", "FIP", "FCPI",
        "non coté", "non-coté", "capital risque", "capital innovation",
        "capital développement", "LBO", "fonds d'investissement",
    ],
    "marches": [
        "CAC 40", "SBF 120", "bourse", "krach", "correction", "volatilité",
        "taux BCE", "inflation", "PIB", "croissance", "récession",
        "marchés financiers", "actions", "obligations", "dividendes",
        "rendement", "indice", "cotation", "IPO", "introduction en bourse",
    ],
    "reglementation": [
        "AMF", "ACPR", "directive", "règlement", "conformité", "MIFID",
        "MIF", "DDA", "LCB-FT", "RGPD", "ESMA", "EIOPA", "ABE",
        "conseiller en gestion", "CGPI", "démarchage", "devoir de conseil",
    ],
    "epargne": [
        "livret A", "LDDS", "LEP", "PEA", "CTO", "compte titre",
        "épargne salariale", "PEE", "intéressement", "participation",
        "épargne", "placement", "rendement", "taux livret",
    ],
    "transmission": [
        "succession", "donation", "démembrement", "usufruit", "nue-propriété",
        "nue propriété", "pacte Dutreil", "holding", "SCI",
        "société civile", "testament", "héritage", "héritier",
        "partage", "indivision",
    ],
}


def _normalize(text: str) -> str:
    return text.lower().strip()


def prefilter(articles: list[Article]) -> list[Article]:
    """
    Filtre les articles : ne garde que ceux contenant au moins un mot-clé
    patrimonial dans le titre ou le résumé.
    """
    if not articles:
        return []

    # Aplatir tous les mots-clés en minuscule
    all_keywords: list[str] = []
    for kw_list in KEYWORDS.values():
        all_keywords.extend(_normalize(k) for k in kw_list)

    filtered: list[Article] = []
    for article in articles:
        text = _normalize(article.title + " " + article.summary)
        if any(kw in text for kw in all_keywords):
            filtered.append(article)

    removed = len(articles) - len(filtered)
    logger.info(
        f"Prefilter: kept {len(filtered)}/{len(articles)} articles "
        f"({removed} removed, {len(filtered) / max(len(articles), 1) * 100:.0f}% kept)"
    )

    return filtered