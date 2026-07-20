"""
Sources RSS pour la veille patrimoniale CGP.
~100 flux couvrant tout le spectre : marchés, fiscalité, immobilier,
SCPI, assurance-vie, private equity, réglementation, etc.

Toutes les URLs sont gratuites et accessibles sans authentification.
"""

SOURCES = [
    # ========================
    # Banques Centrales & Institutions
    # ========================
    {"url": "https://www.ecb.europa.eu/rss/press.html", "category": "institutions"},
    {"url": "https://www.banque-france.fr/rss", "category": "institutions"},
    {"url": "https://www.federalreserve.gov/feeds/press.xml", "category": "institutions"},
    {"url": "https://www.imf.org/en/News/RSS", "category": "institutions"},
    {"url": "https://www.bis.org/rss/index.htm", "category": "institutions"},
    {"url": "https://www.oecd.org/fr/rss.xml", "category": "institutions"},

    # ========================
    # Institutions Françaises
    # ========================
    {"url": "https://www.amf-france.org/fr/rss", "category": "institutions_fr"},
    {"url": "https://acpr.banque-france.fr/rss", "category": "institutions_fr"},
    {"url": "https://www.economie.gouv.fr/rss", "category": "institutions_fr"},
    {"url": "https://www.impots.gouv.fr/rss", "category": "institutions_fr"},
    {"url": "https://www.senat.fr/rss.html", "category": "institutions_fr"},
    {"url": "https://www.assemblee-nationale.fr/rss.xml", "category": "institutions_fr"},
    {"url": "https://www.legifrance.gouv.fr/rss", "category": "institutions_fr"},
    {"url": "https://www.insee.fr/fr/rss", "category": "institutions_fr"},
    {"url": "https://www.ccomptes.fr/rss", "category": "institutions_fr"},

    # ========================
    # Europe & Réglementation
    # ========================
    {"url": "https://www.esma.europa.eu/rss", "category": "europe"},
    {"url": "https://www.eiopa.europa.eu/rss", "category": "europe"},
    {"url": "https://ec.europa.eu/commission/presscorner/rss", "category": "europe"},
    {"url": "https://www.europarl.europa.eu/rss", "category": "europe"},
    {"url": "https://eur-lex.europa.eu/rss", "category": "europe"},

    # ========================
    # Marchés & Macroéconomie
    # ========================
    {"url": "https://www.boursorama.com/actualites/rss", "category": "markets"},
    {"url": "https://www.boursorama.com/bourse/rss", "category": "markets"},
    {"url": "https://www.boursorama.com/bourse/taux/rss", "category": "markets"},
    {"url": "https://www.investir.fr/rss", "category": "markets"},
    {"url": "https://www.investir.fr/matieres-premieres/rss", "category": "markets"},
    {"url": "https://www.lesechos.fr/finance-marches/feed.xml", "category": "markets"},
    {"url": "https://www.lesechos.fr/economie-france/feed.xml", "category": "markets"},
    {"url": "https://www.lesechos.fr/monde/feed.xml", "category": "markets"},
    {"url": "https://www.latribune.fr/economie/feed.xml", "category": "markets"},
    {"url": "https://www.latribune.fr/economie/international/feed.xml", "category": "markets"},
    {"url": "https://www.bfmtv.com/rss/economie.xml", "category": "markets"},
    {"url": "https://www.bfmtv.com/rss/bourse.xml", "category": "markets"},
    {"url": "https://www.lerevenu.com/rss", "category": "markets"},
    {"url": "https://www.zonebourse.com/rss", "category": "markets"},
    {"url": "https://www.zonebourse.com/actualite-bourse/rss", "category": "markets"},
    {"url": "https://www.abcbourse.com/rss", "category": "markets"},
    {"url": "https://www.boursier.com/rss", "category": "markets"},
    {"url": "https://www.tradingsat.com/rss", "category": "markets"},
    {"url": "https://www.euronext.com/fr/rss", "category": "markets"},
    {"url": "https://www.morningstar.fr/fr/rss", "category": "markets"},
    {"url": "https://www.cercledelepargne.com/rss", "category": "markets"},

    # ========================
    # Immobilier & SCPI
    # ========================
    {"url": "https://www.meilleurescpi.com/actualites/rss", "category": "realestate"},
    {"url": "https://www.immomatin.com/feed", "category": "realestate"},
    {"url": "https://www.mysweetimmo.com/feed", "category": "realestate"},
    {"url": "https://www.seloger.com/actualites/feed", "category": "realestate"},
    {"url": "https://www.boursorama.com/actualites/immobilier/rss", "category": "realestate"},
    {"url": "https://www.lefigaro.fr/immobilier/feed.xml", "category": "realestate"},
    {"url": "https://www.lesechos.fr/industrie-services/immobilier-btp/feed.xml", "category": "realestate"},
    {"url": "https://www.batiactu.com/rss", "category": "realestate"},
    {"url": "https://www.businessimmo.com/rss", "category": "realestate"},
    {"url": "https://www.pierrepapier.fr/rss", "category": "realestate"},
    {"url": "https://www.scpi-online.com/rss", "category": "realestate"},
    {"url": "https://www.france-scpi.com/rss", "category": "realestate"},
    {"url": "https://www.pap.fr/rss", "category": "realestate"},
    {"url": "https://www.meilleursagents.com/rss", "category": "realestate"},
    {"url": "https://www.orie.asso.fr/rss", "category": "realestate"},

    # ========================
    # Fiscalité & Patrimoine
    # ========================
    {"url": "https://www.lefigaro.fr/patrimoine/feed.xml", "category": "fiscalite"},
    {"url": "https://www.lesechos.fr/patrimoine/feed.xml", "category": "fiscalite"},
    {"url": "https://www.capital.fr/rss", "category": "fiscalite"},
    {"url": "https://www.leparticulier.fr/feed", "category": "fiscalite"},
    {"url": "https://www.leparticulier.fr/impots/feed", "category": "fiscalite"},
    {"url": "https://www.moneyvox.fr/feed", "category": "fiscalite"},
    {"url": "https://www.moneyvox.fr/impots/feed", "category": "fiscalite"},
    {"url": "https://www.dossierfamilial.com/feed", "category": "fiscalite"},
    {"url": "https://www.notretemps.com/argent/feed", "category": "fiscalite"},
    {"url": "https://www.boursorama.com/patrimoine/fiscalite/rss", "category": "fiscalite"},
    {"url": "https://www.lafinancepourtous.com/feed", "category": "fiscalite"},
    {"url": "https://www.lacorbeille.fr/feed", "category": "fiscalite"},
    {"url": "https://www.gestiondepatrimoine.com/feed", "category": "fiscalite"},
    {"url": "https://www.patrimoine24.com/rss", "category": "fiscalite"},
    {"url": "https://www.netpme.fr/rss", "category": "fiscalite"},

    # ========================
    # Finance Pro & Gestion d'Actifs
    # ========================
    {"url": "https://www.agefi.fr/feed", "category": "finance_pro"},
    {"url": "https://www.agefi.fr/asset-management/feed", "category": "finance_pro"},
    {"url": "https://www.optionfinance.fr/feed", "category": "finance_pro"},
    {"url": "https://www.gestiondefortune.com/feed", "category": "finance_pro"},
    {"url": "https://www.newsmanagers.com/feed", "category": "finance_pro"},
    {"url": "https://www.h24finance.com/feed", "category": "finance_pro"},
    {"url": "https://citywire.com/fr/feed", "category": "finance_pro"},
    {"url": "https://www.funds-magazine.com/feed", "category": "finance_pro"},
    {"url": "https://www.investissement-conseils.com/feed", "category": "finance_pro"},
    {"url": "https://www.professioncgp.com/feed", "category": "finance_pro"},
    {"url": "https://www.lemondeduchiffre.fr/rss", "category": "finance_pro"},
    {"url": "https://www.magazine-decideurs.com/rss", "category": "finance_pro"},
    {"url": "https://www.finascope.com/rss", "category": "finance_pro"},

    # ========================
    # Assurance-Vie & Retraite
    # ========================
    {"url": "https://www.newsassurancespro.com/feed", "category": "assurance"},
    {"url": "https://www.argusdelassurance.com/feed", "category": "assurance"},
    {"url": "https://www.previssima.fr/feed", "category": "assurance"},
    {"url": "https://www.lassuranceretraite.fr/rss", "category": "assurance"},
    {"url": "https://www.ag2rlamondiale.fr/rss", "category": "assurance"},
    {"url": "https://www.retraite.com/rss", "category": "assurance"},
    {"url": "https://www.la-retraite-en-clair.fr/rss", "category": "assurance"},
    {"url": "https://www.reassurez-moi.fr/rss", "category": "assurance"},
    {"url": "https://www.goodvalueformoney.com/feed", "category": "assurance"},

    # ========================
    # Private Equity & Épargne
    # ========================
    {"url": "https://www.cfnews.net/feed", "category": "private_equity"},
    {"url": "https://www.pemagazine.fr/feed", "category": "private_equity"},
    {"url": "https://www.epargne-salariale.com/feed", "category": "private_equity"},
    {"url": "https://www.epargnant30.fr/feed", "category": "private_equity"},
    {"url": "https://www.next-finance.net/rss", "category": "private_equity"},
    {"url": "https://www.finyear.com/rss", "category": "private_equity"},
    {"url": "https://www.crowdfundingimmo.fr/rss", "category": "private_equity"},
    {"url": "https://blog.clubfunding.fr/feed", "category": "private_equity"},
    {"url": "https://www.anaxago.com/rss", "category": "private_equity"},
    {"url": "https://www.wiseed.com/rss", "category": "private_equity"},

    # ========================
    # Réglementation & Droit
    # ========================
    {"url": "https://www.village-justice.com/feed", "category": "legal"},
    {"url": "https://www.editions-legislatives.fr/feed", "category": "legal"},
    {"url": "https://www.actu-juridique.fr/feed", "category": "legal"},
    {"url": "https://www.dalloz-actualite.fr/rss", "category": "legal"},
    {"url": "https://www.lexbase.fr/rss", "category": "legal"},
    {"url": "https://www.lemondedudroit.fr/rss", "category": "legal"},
    {"url": "https://www.jss.fr/rss", "category": "legal"},

    # ========================
    # International
    # ========================
    {"url": "https://www.ft.com/rss", "category": "international"},
    {"url": "https://www.reuters.com/business/rss", "category": "international"},
    {"url": "https://www.cnbc.com/id/10001147/device/rss", "category": "international"},
    {"url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "category": "international"},
    {"url": "https://www.economist.com/finance-and-economics/rss.xml", "category": "international"},
    {"url": "https://www.marketwatch.com/rss", "category": "international"},
    {"url": "https://www.investing.com/rss", "category": "international"},
    {"url": "https://www.bloomberg.com/feed", "category": "international"},

    # ========================
    # ESG / Finance Durable
    # ========================
    {"url": "https://www.novethic.fr/feed", "category": "esg"},
    {"url": "https://www.greenunivers.com/feed", "category": "esg"},
    {"url": "https://youmatter.world/fr/feed", "category": "esg"},
    {"url": "https://www.linfodurable.fr/rss", "category": "esg"},

    # ========================
    # Fintech & Innovation
    # ========================
    {"url": "https://www.maddyness.com/feed", "category": "fintech"},
    {"url": "https://www.frenchweb.fr/feed", "category": "fintech"},
    {"url": "https://www.journaldunet.com/rss", "category": "fintech"},
    {"url": "https://siecledigital.fr/feed", "category": "fintech"},
    {"url": "https://www.mind.eu.com/fintech/feed", "category": "fintech"},

    # ========================
    # Think Tanks & Recherche
    # ========================
    {"url": "https://www.institutmontaigne.org/rss", "category": "thinktank"},
    {"url": "https://www.ifrap.org/rss", "category": "thinktank"},
    {"url": "https://www.fondapol.org/rss", "category": "thinktank"},
    {"url": "https://tnova.fr/rss", "category": "thinktank"},
    {"url": "https://www.institut-epargne.fr/rss", "category": "thinktank"},

    # ========================
    # Placements Alternatifs
    # ========================
    {"url": "https://www.boursorama.com/bourse/matieres-premieres/rss", "category": "alternatifs"},
    {"url": "https://www.lefigaro.fr/vin/feed.xml", "category": "alternatifs"},
    {"url": "https://www.artprice.com/rss", "category": "alternatifs"},
    {"url": "https://www.lequotidiendelart.com/rss", "category": "alternatifs"},
]