"""
Sources RSS pour la veille patrimoniale CGP.

URLs vérifiées fonctionnelles le 2026-07-20 (retournent du vrai RSS, 200 OK).
Couvre : marchés, fiscalité, immobilier, SCPI, assurance-vie, private equity,
réglementation, ESG, fintech, think tanks, presse économique générale.

Les sites qui bloquent les requêtes automatisées (Les Échos, Figaro, Boursorama,
BFM, Le Point, Capital…) sont exclus — leurs RSS renvoient 403/404 aux scripts.
La liste peut être étendue ; chaque entrée est testée au démarrage et les
échecs sont simplement ignorés (log WARNING).
"""

SOURCES = [
    # ========================
    # Presse économique générale
    # ========================
    {"url": "https://www.lemonde.fr/rss/une.xml", "category": "general"},
    {"url": "https://www.lexpress.fr/rss/une.xml", "category": "general"},
    {"url": "https://www.lexpress.fr/rss/economie.xml", "category": "general"},
    {"url": "https://www.latribune.fr/feed.xml", "category": "general"},
    {"url": "https://www.challenges.fr/rss.xml", "category": "general"},
    {"url": "https://www.lerevenu.com/rss.xml", "category": "general"},
    {"url": "https://www.alternatives-economiques.fr/rss.xml", "category": "general"},

    # ========================
    # Marchés & finance internationale
    # ========================
    {"url": "https://www.economist.com/finance-and-economics/rss.xml", "category": "markets"},
    {"url": "https://www.economist.com/business/rss.xml", "category": "markets"},
    {"url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "category": "markets"},
    {"url": "https://feeds.a.dj.com/rss/RSSWorldNews.xml", "category": "markets"},
    {"url": "https://www.marketwatch.com/rss/topstories", "category": "markets"},
    {"url": "https://www.investing.com/rss/news.rss", "category": "markets"},
    {"url": "https://www.investing.com/rss/news_1.rss", "category": "markets"},

    # ========================
    # Institutions
    # ========================
    {"url": "https://www.ecb.europa.eu/rss/press.html", "category": "institutions"},

    # ========================
    # Immobilier & SCPI
    # ========================
    {"url": "https://www.meilleurescpi.com/rss", "category": "realestate"},
    {"url": "https://www.pierrepapier.fr/feed/", "category": "realestate"},
    {"url": "https://www.mysweetimmo.com/feed/", "category": "realestate"},
    {"url": "https://www.scpi-online.com/feed/", "category": "realestate"},
    {"url": "https://www.crowdfundingimmo.fr/feed/", "category": "realestate"},

    # ========================
    # Fiscalité & patrimoine
    # ========================
    {"url": "https://www.notretemps.com/rss", "category": "fiscalite"},
    {"url": "https://www.notretemps.com/argent/rss", "category": "fiscalite"},
    {"url": "https://www.dossierfamilial.com/rss.xml", "category": "fiscalite"},
    {"url": "https://www.lafinancepourtous.com/feed/", "category": "fiscalite"},

    # ========================
    # Finance pro & private equity
    # ========================
    {"url": "https://www.finyear.com/feed/", "category": "finance_pro"},
    {"url": "https://www.pemagazine.fr/feed/", "category": "finance_pro"},
    {"url": "https://www.epargnant30.fr/feed/", "category": "finance_pro"},

    # ========================
    # Droit & réglementation
    # ========================
    {"url": "https://www.actu-juridique.fr/feed/", "category": "legal"},

    # ========================
    # ESG / finance durable
    # ========================
    {"url": "https://www.novethic.fr/feed/", "category": "esg"},
    {"url": "https://www.greenunivers.com/feed/", "category": "esg"},

    # ========================
    # Fintech & innovation
    # ========================
    {"url": "https://www.frenchweb.fr/feed/", "category": "fintech"},
    {"url": "https://www.journaldunet.com/rss/", "category": "fintech"},
    {"url": "https://siecledigital.fr/feed/", "category": "fintech"},
    {"url": "https://www.maddyness.com/feed/", "category": "fintech"},
    {"url": "https://www.mind.eu.com/fintech/feed/", "category": "fintech"},

    # ========================
    # Think tanks
    # ========================
    {"url": "https://www.institutmontaigne.org/rss.xml", "category": "thinktank"},
    {"url": "https://tnova.fr/rss/", "category": "thinktank"},
]