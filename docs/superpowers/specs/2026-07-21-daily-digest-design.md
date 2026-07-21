# Spec : Résumé Quotidien 8h (Paris)

**Date** : 2026-07-21
**Statut** : Validé
**Auteur** : Nathan Bauduin

---

## 1. Objectif

Chaque matin à 8h (heure de Paris), générer automatiquement un **résumé élégant de l'actualité patrimoniale** des dernières 24h, hébergé sur **GitHub Pages**, avec notification push sur iPhone via Bark.

Le résumé est conçu pour une **lecture de 5 minutes** : sections thématiques, liens vers les sources originales, ton adapté CGP.

## 2. Architecture

```
GitHub Actions (cron 0 7 * * * UTC ≈ 8h Paris hiver / 9h été)
  ├── fetch RSS 24h
  ├── filtre mots-clés
  ├── IA synthèse (Opus 4.8) → JSON structuré
  ├── rendu HTML élégant
  ├── sauvegarde archive + index
  ├── commit + push (déclenche GitHub Pages)
  └── notif Bark groupante

GitHub Pages (branche gh-pages OU dossier docs/ sur main)
  └── /index.html (jour J) + /resumes/YYYY-MM-DD.html (archive)
```

## 3. Composants ajoutés

| Fichier | Rôle |
|---------|------|
| `src/daily.py` | Orchestration du résumé quotidien (entrée CLI) |
| `src/synthesizer.py` | Appel IA pour produire le JSON de synthèse |
| `src/render.py` | Génération HTML (template string-based, pas de Jinja) |
| `src/notify_digest.py` | Envoi notif Bark groupante |
| `src/prompts/digest_prompt.py` | Prompt système de synthèse |
| `.github/workflows/daily-digest.yml` | Cron quotidien |
| `docs/index.html` (généré) | Page du jour |
| `docs/resumes/YYYY-MM-DD.html` (généré) | Archives |
| `docs/assets/digest.css` | CSS partagé pour les pages |

## 4. Pipeline d'exécution

### 4.1 Fetch 24h

Re-utilise `fetcher.py.fetch_all()`. Filtre les articles avec `published >= now - 24h` (ou `published is None` = garder). L'heure Paris n'est pas critique (on prend 24h glissant UTC).

### 4.2 Filtre mots-clés

Re-utilise `prefilter.prefilter()`. Si **0 article** → branche "cas vide" (voir 4.7).

### 4.3 Synthèse IA

`src/synthesizer.py.synthesize_digest(articles)` envoie un seul appel à FantasyAI.cloud (Opus 4.8) avec prompt système dédié.

**Modèle primaire** : `claude-opus-4-8` (le seul — pas de fallback pour le digest, car la qualité prime). Si échoue, on retente 2 fois, puis on log et on passe en mode dégradé (page HTML = simple liste sans synthèse).

**Entrée** : titre + résumé + source + date pour chaque article, groupés par catégorie.
**Sortie attendue** : JSON structuré (voir 4.4).
**`max_tokens`** : 100000 (idem principal).

### 4.4 Format JSON de synthèse

```json
{
  "date_fr": "mardi 22 juillet 2026",
  "compte_articles": 142,
  "compte_forts": 8,
  "compte_moyens": 23,
  "synthese_jour": "3 phrases de contexte macro/journalier",
  "chiffres_cles": [
    "CAC 40 : +0,82 % à 7 894 pts",
    "OAT 10 ans : 3,21 % (-4 pbs)",
    "Brent : 82,4 $/baril"
  ],
  "sections": [
    {
      "titre": "Marchés financiers",
      "icone": "📈",
      "niveau_global": "moyen",
      "items": [
        {
          "titre": "La BCE abaisse ses taux directeurs de 25 pbs",
          "analyse": "3-4 phrases d'analyse pour le CGP et ses clients",
          "source": "Les Échos",
          "url": "https://..."
        }
      ]
    }
  ]
}
```

Ordre des sections : Marchés, Fiscalité, SCPI & Immobilier, Assurance-vie, Private equity, Retraite & Épargne salariale, Réglementation, ESG, À surveiller.

### 4.5 Rendu HTML

`src/render.py.render_digest(digest_json, articles_count)` produit un document HTML5 complet avec :
- `<head>` : meta charset UTF-8, viewport mobile, CSS inline + lien vers `assets/digest.css`
- En-tête : date, compteurs (X articles / Y forts / Z moyens)
- Bandeau de synthèse
- Chiffres clés (badges)
- Sections en grille responsive (1 col mobile, 2 col desktop)
- Chaque item = carte cliquable (article original)
- Footer : "Généré par Albea Veille • Opus 4.8 • lien GitHub"

CSS (`docs/assets/digest.css`) : palette sobre (bleu nuit Albea, accents par niveau d'impact), mobile-first, dark mode via `prefers-color-scheme`.

### 4.6 Sauvegarde

- Page du jour : `docs/index.html` (toujours écrasée, c'est la dernière)
- Archive : `docs/resumes/2026-07-22.html` (par date locale Paris)
- Garde les 30 dernières archives (rotation si > 30)

### 4.7 Cas vide

Si 0 article patrimonial dans les 24h :
- `docs/index.html` affiche un bandeau "Marchés calmes aujourd'hui"
- `docs/resumes/2026-07-22.html` archivée pareil
- Notif Bark : `🤷 [RÉSUMÉ] 22 juillet — Aucune actualité patrimoniale notable. À demain.`

### 4.8 Notification Bark

`src/notify_digest.send_digest_notification(digest, page_url)` envoie **une notif groupante** :

```
📊 [RÉSUMÉ QUOTIDIEN] mardi 22 juillet

142 articles analysés • 8 impacts forts • 23 moyens
• 3 alertes fiscales (PLF 2027)
• 2 nouvelles SCPI (Comète 7,3% / Eden Finlande)
• 1 mouvement majeur BCE
Lire le résumé → https://Nathandevg.github.io/albea-veille/
```

Si la synthèse détecte au moins 1 impact **fort** dans le digest, on envoie en parallèle des notifs prioritaires individuelles (`timeSensitive` + son `alarm`) pour chaque impact fort détecté dans la nuit par les runs 10 min — uniquement si elles n'ont pas déjà été notifiées (flag dans `history.json`).

### 4.9 GitHub Pages

Deux options équivalentes, on choisit la plus simple : **dossier `docs/` sur `main`** activable en 1 clic dans Settings → Pages. Pas besoin de créer une branche `gh-pages`.

URL : `https://Nathandevg.github.io/albea-veille/`

## 5. Workflow GitHub Actions

`.github/workflows/daily-digest.yml` :

```yaml
name: Daily Digest
on:
  schedule:
    - cron: '0 7 * * *'   # 8h Paris hiver, 9h Paris été
  workflow_dispatch:

permissions:
  contents: write

jobs:
  digest:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt
      - run: mkdir -p docs/resumes docs/assets
      - run: touch src/history.json && [ -s src/history.json ] || echo '{}' > src/history.json
      - run: python src/daily.py
        env:
          FANTASYAI_API_KEY: ${{ secrets.FANTASYAI_API_KEY }}
          BARK_DEVICE_KEY: ${{ secrets.BARK_DEVICE_KEY }}
      # Push avec le même step rebase+retry que check-news
      - name: Commit & push digest
        if: always()
        continue-on-error: true
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add docs/ src/history.json
          git commit -m "chore: digest YYYY-MM-DD" --no-verify || true
          for i in 1 2 3; do
            git fetch origin main
            if ! git rebase origin/main; then
              git checkout --theirs src/history.json docs/index.html 2>/dev/null || true
              git add src/history.json docs/index.html
              git rebase --continue --no-verify || { git rebase --abort; }
            fi
            if git push origin main; then
              echo "Push OK"; exit 0
            fi
          done
          echo "Push échoué (non bloquant)"
```

## 6. Setup GitHub Pages

À faire **une seule fois** par l'utilisateur (pas automatisé) :

1. Repo → Settings → Pages
2. Source : **Deploy from a branch**
3. Branch : **main**, dossier **/docs**
4. Save

GitHub sert automatiquement `docs/index.html` à l'URL `https://<user>.github.io/<repo>/`.

## 7. Évolution future (hors MVP)

- Résumé hebdo (samedi 8h) : synthèse des 7 derniers jours
- Résumé mensuel : 1er du mois
- Push vers email / Slack en plus de Bark
- Tableau de bord de tous les digests (page d'accueil avec index cliquable par jour)

## 8. Tests manuels (MVP)

- Workflow manuel (`workflow_dispatch`) pour générer un digest de test
- Vérifier que la page HTML s'affiche bien sur `https://Nathandevg.github.io/albea-veille/`
- Vérifier la notif Bark
- Vérifier l'archive du lendemain
