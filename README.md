# Albea Veille — Radar Patrimonial Intelligent

Flux d'actualité patrimoniale pour CGP avec filtrage IA et notifications push iPhone.

## Architecture

```
~100 flux RSS → GitHub Actions (cron) → Python → FantasyAI.cloud → Bark → iPhone
```

## Stack

- **Sources** : ~35 flux RSS gratuits vérifiés fonctionnels (marchés, fiscalité, immobilier, SCPI, assurance-vie, private equity…) — voir `src/sources.py`. Les sites qui bloquent les scripts (Les Échos, Figaro, Boursorama, BFM…) sont exclus car leurs RSS renvoient 403/404.
- **Orchestration** : GitHub Actions (cron toutes les 10 min)
- **Analyse IA** : FantasyAI.cloud (Claude Opus 4.8)
- **Push** : [Bark](https://github.com/Finb/Bark) (open source, gratuit, app iOS)

## Coût

- GitHub Actions : **0€** (2000 min/mois gratuites)
- Hébergement : **0€** (serverless)
- Push notifications : **0€** (Bark open source)
- IA : via clé FantasyAI.cloud

**Coût total hors IA : 0€**

## Configuration

### 1. Secrets GitHub

Dans `Settings > Secrets and variables > Actions` :

| Secret | Valeur |
|--------|--------|
| `FANTASYAI_API_KEY` | Ta clé API FantasyAI.cloud |
| `BARK_DEVICE_KEY` | Ta device key Bark (depuis l'app iOS) |

### 2. App Bark sur iPhone

1. Télécharger [Bark](https://apps.apple.com/app/bark-customed-notifications/id1403753865) sur l'App Store
2. Ouvrir l'app → la device key s'affiche en haut
3. Copier la device key dans le secret GitHub `BARK_DEVICE_KEY`

### 3. Premier run

Le workflow se déclenche automatiquement au prochain créneau cron. Pour tester immédiatement : aller dans `Actions > Albea Veille > Run workflow`.

## Sources

Voir `src/sources.py` pour la liste complète des ~100 flux RSS organisés par catégorie.

## Structure

```
actu/
├── .github/workflows/check-news.yml   # Cron GitHub Actions
├── src/
│   ├── main.py        # Orchestration
│   ├── sources.py     # ~100 URLs RSS
│   ├── fetcher.py     # Fetch RSS parallèle
│   ├── dedup.py       # Déduplication
│   ├── prefilter.py   # Filtrage mots-clés
│   ├── analyzer.py    # Analyse IA FantasyAI.cloud
│   ├── notifier.py    # Push notifications Bark
│   └── history.json   # Articles traités (auto-généré)
└── requirements.txt   # feedparser, httpx
```

## Personnalisation

- **Mots-clés** : modifier `prefilter.py` → `KEYWORDS`
- **Seuil de notification** : `main.py` → `filter_impactful()` (par défaut : moyen/fort)
- **Fréquence** : `.github/workflows/check-news.yml` → `cron`
- **Sources** : `sources.py` → `SOURCES`