# Spec : Flux d'actualité patrimoniale — CGP Albea Patrimoine

**Date** : 2026-07-14
**Statut** : Validé
**Auteur** : Nathan Bauduin

---

## 1. Objectif

Fournir un radar d'actualité financière et patrimoniale sur iPhone, avec push notifications en temps réel, destiné à un Conseiller en Gestion de Patrimoine (CGP) chez Albea Patrimoine.

L'IA (FantasyAI.cloud) filtre et analyse les actualités pour ne notifier que celles ayant un **impact concret** sur l'activité de CGP : SCPI, assurance-vie, private equity, immobilier, fiscalité, transmission, réglementation.

---

## 2. Architecture

```
~100 flux RSS → GitHub Actions (cron 10 min) → Script Python → FantasyAI.cloud → Bark → iPhone
```

### Composants

| Composant | Rôle | Technologie |
|-----------|------|-------------|
| **Fetcher** | Récupère ~100 flux RSS en parallèle | Python `feedparser` + `httpx` |
| **Dedup** | Dédoublonne par URL + similarité de titre | Python `difflib` |
| **Pre-filter** | Filtre rapide par mots-clés patrimoniaux | Python, liste de mots-clés |
| **Analyzer** | Analyse IA de l'impact pour le CGP | FantasyAI.cloud API |
| **Notifier** | Push notification sur iPhone | Bark API |
| **History** | Stocke les articles déjà traités | Fichier JSON dans le repo |
| **Scheduler** | Lance le script toutes les 10 minutes | GitHub Actions cron |

### Flux de données

```
1. GitHub Actions déclenche le cron
2. main.py s'exécute
3. fetcher.py → fetch parallèle de tous les flux RSS
4. Déduplication (URL + titre)
5. Filtrage mots-clés (premier filtre gratuit)
6. Articles restants → analyzer.py → FantasyAI.cloud
7. Si impact=true ET niveau=moyen/fort → notifier.py → Bark
8. Mise à jour de history.json
```

---

## 3. Sources RSS (~100 flux)

### Banques Centrales & Institutions (6)
- BCE, Banque de France, Fed, FMI, BRI, OCDE

### Institutions Françaises (9)
- AMF, ACPR, Ministère Économie, DGFiP, Sénat, Assemblée Nationale, Légifrance, INSEE, Cour des Comptes

### Europe & Réglementation (5)
- ESMA, EIOPA, Commission Européenne, Parlement Européen, EUR-Lex

### Marchés & Macroéconomie (21)
- Boursorama (3 flux), Investir (2), Les Échos (3), La Tribune (2), BFM Business (2), Le Revenu, Zone Bourse (2), ABC Bourse, Boursier.com, TradingSat, Euronext, Morningstar FR, Cercle des Épargnants

### Immobilier & SCPI (15)
- MeilleureSCPI, Immo Matin, MySweetImmo, SeLoger, Boursorama Immo, Le Figaro Immo, Les Échos Immo, Batiactu, Business Immo, Pierrepapier.fr, SCPI-Online, France SCPI, PAP, MeilleursAgents, ORIE

### Fiscalité & Patrimoine (15)
- Le Figaro Patrimoine, Les Échos Patrimoine, Capital, Le Particulier (2), MoneyVox (2), Dossier Familial, Notre Temps Argent, Boursorama Fiscalité, La Finance Pour Tous, Corbeille, Gestion Patrimoine, Patrimoine 24, NetPME

### Finance Pro & Gestion d'Actifs (13)
- L'Agefi (2), Option Finance, Gestion de Fortune, NewsManagers, H24 Finance, Citywire France, Funds Magazine, Investissement Conseils, Profession CGP, Le Monde du Chiffre, Décideurs Magazine, Finascope

### Assurance-Vie & Retraite (9)
- News Assurances Pro, L'Argus de l'Assurance, Previssima, Assurance Retraite, AG2R La Mondiale, Retraite.com, La Retraite en Clair, Réassurez-moi, Good Value for Money

### Private Equity & Épargne (10)
- CFNEWS, Private Equity Magazine, Épargne Salariale, Épargnant 3.0, Next Finance, Finyear, Crowdfunding Immo, ClubFunding, Anaxago, WiSEED

### Réglementation & Droit (7)
- Village de la Justice, Éditions Législatives, Actu-Juridique, Dalloz Actualité, Lexbase, Le Monde du Droit, JSS

### International (8)
- Financial Times, Reuters Business, Bloomberg, CNBC, WSJ Markets, The Economist, MarketWatch, Investing.com

### ESG / Finance Durable (4)
- Novethic, GreenUnivers, Youmatter, ID L'Info Durable

### Fintech & Innovation (5)
- Maddyness, FrenchWeb, Journal du Net, Siècle Digital, Mind Fintech

### Think Tanks & Recherche (6)
- Institut Montaigne, Fondation iFRAP, Fondapol, Terra Nova, Institut de l'Épargne, Cercle de l'Épargne

### Placements Alternatifs (4)
- Boursorama Matières Premières, Le Figaro Vin, Artprice, Le Quotidien de l'Art

**Total : ~100 sources.** La liste exacte des URLs est dans `src/sources.py`.

---

## 4. Logique IA

### Prompt FantasyAI.cloud

```
Tu es un analyste patrimonial expert. Analyse cet article et détermine son impact pour un CGP (Conseiller en Gestion de Patrimoine) chez Albea Patrimoine.

Domaines d'activité du CGP : SCPI, assurance-vie, private equity, immobilier, fiscalité, transmission, épargne salariale, retraite, marchés financiers, réglementation financière.

Réponds UNIQUEMENT en JSON valide, sans markdown, sans texte avant ou après :
{
  "impact": true/false,
  "niveau": "faible/moyen/fort",
  "resume": "1 phrase de résumé",
  "analyse": "2-3 phrases sur l'impact concret pour le CGP et ses clients"
}

Article :
Titre : {title}
Source : {source}
Date : {date}
Contenu : {content}
```

### Règles de notification

- `impact: false` → ignoré
- `impact: true` + `niveau: faible` → ignoré (pas de push)
- `impact: true` + `niveau: moyen` → push
- `impact: true` + `niveau: fort` → push

### Coût FantasyAI.cloud

Estimé à ~500-1000 appels/jour après filtrage (sur ~2000-3000 articles bruts). À calibrer selon le plan tarifaire.

---

## 5. Notification Push (Bark)

### Format

```
Titre : [niveau] résumé de l'IA
Corps : analyse de l'IA
URL : lien vers l'article original
```

### Exemple

```
🔔 [FORT] La BCE baisse ses taux de 0,25 point
Les SCPI devraient voir leur valorisation remonter. À anticiper avec les clients exposés à l'immobilier papier. Bon moment pour renforcer les SCPI.
→ https://lesechos.fr/...
```

### Configuration

- App Bark installée sur iPhone
- Device key stockée dans les secrets GitHub (`BARK_DEVICE_KEY`)
- API endpoint : `https://api.day.app/{device_key}/{title}/{body}?url={article_url}`

---

## 6. Structure du projet

```
actu/
├── .github/
│   └── workflows/
│       └── check-news.yml        # Cron toutes les 10 min
├── src/
│   ├── main.py                   # Point d'entrée, orchestre tout
│   ├── sources.py                # Liste des ~100 URLs RSS
│   ├── fetcher.py                # Fetch parallèle des flux RSS
│   ├── dedup.py                  # Déduplication articles
│   ├── prefilter.py              # Filtrage mots-clés
│   ├── analyzer.py               # Appel FantasyAI.cloud
│   ├── notifier.py               # Push Bark
│   └── history.json              # Articles déjà traités (généré)
├── requirements.txt              # feedparser, httpx
└── README.md
```

---

## 7. GitHub Actions Workflow

```yaml
name: Check News
on:
  schedule:
    - cron: '*/10 * * * *'   # Toutes les 10 minutes
  workflow_dispatch:          # Déclenchement manuel possible

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: python src/main.py
        env:
          FANTASYAI_API_KEY: ${{ secrets.FANTASYAI_API_KEY }}
          BARK_DEVICE_KEY: ${{ secrets.BARK_DEVICE_KEY }}
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "Update history.json"
          file_pattern: 'src/history.json'
```

---

## 8. Pré-filtrage par mots-clés

Avant d'appeler l'IA, un filtre rapide vérifie la présence d'au moins un mot-clé dans le titre ou le résumé de l'article. Cela réduit le volume d'appels IA de ~70%.

### Catégories de mots-clés

- **SCPI** : SCPI, société civile de placement immobilier, pierre papier, rendement SCPI, parts de SCPI
- **Assurance-vie** : assurance vie, assurance-vie, fonds euros, UC, unités de compte, rachat, contrat assurance
- **Fiscalité** : impôt, IFI, ISF, flat tax, PFU, prélèvement forfaitaire, plus-value, abattement, niche fiscale, PLF, loi de finances, DMTG, droits de succession, donation, transmission
- **Immobilier** : immobilier, prix m2, taux crédit, PTZ, Pinel, Denormandie, LMNP, Malraux, déficit foncier
- **Retraite** : retraite, PER, PERP, PERCO, Madelin, loi Pacte, réforme retraite, âge départ
- **Private Equity** : private equity, capital investissement, FPCI, FIP, FCPI, non coté
- **Marchés** : CAC 40, SBF 120, bourse, krach, correction, volatilité, taux BCE, inflation, PIB, croissance, récession
- **Réglementation** : AMF, ACPR, directive, règlement, conformité, MIFID, DDA, LCB-FT
- **Épargne** : livret A, LDDS, LEP, PEA, CTO, épargne salariale, PEE, intéressement, participation
- **Transmission** : succession, donation, démembrement, usufruit, nue-propriété, pacte Dutreil

---

## 9. Gestion des erreurs

- **Timeout RSS** : 10 secondes par flux, skip si pas de réponse
- **Rate limit FantasyAI** : retry avec backoff exponentiel (1s, 2s, 4s, 8s)
- **Bark down** : log l'erreur, ne pas bloquer le reste
- **history.json corrompu** : recréer un fichier vide
- **GitHub Actions limit** : 2000 min/mois gratuites. À 2 min par run × 6 runs/h × 24h × 30j = ~144 min/mois → large

---

## 10. Évolutions futures (hors MVP)

- App iOS native SwiftUI (remplace Bark)
- Dashboard web simple
- Filtrage par client/portefeuille
- Synthèse hebdomadaire automatique
- Intégration avec les outils Albea
- Support multi-utilisateurs (autres CGP)

---

## 11. Déploiement

1. Créer un repo GitHub (public ou privé)
2. Configurer les secrets : `FANTASYAI_API_KEY`, `BARK_DEVICE_KEY`
3. Installer l'app Bark sur iPhone, récupérer la device key
4. Pousser le code → le workflow se déclenche automatiquement
5. Vérifier les premières notifications
