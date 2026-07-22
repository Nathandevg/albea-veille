"""
Rendu HTML du digest quotidien.

Génère un document HTML5 mobile-first, avec palette sobre,
badges par niveau d'impact, et liens cliquables vers les sources.
Pas de dépendance externe (template string-based, pas de Jinja).
"""

from __future__ import annotations

import html
from datetime import datetime


def render_digest(digest: dict, page_url: str = "") -> str:
    """
    Rend le digest en HTML5 complet.

    Args:
        digest: Dict produit par synthesizer.synthesize_digest().
        page_url: URL canonique de la page (pour les balises meta).
    """
    date_fr = digest.get("date_fr", datetime.now().strftime("%A %d %B %Y"))
    compte_articles = digest.get("compte_articles", 0)
    compte_forts = digest.get("compte_forts", 0)
    compte_moyens = digest.get("compte_moyens", 0)
    synthese = digest.get("synthese_jour", "")
    chiffres = digest.get("chiffres_cles", [])
    sections = digest.get("sections", [])
    a_surveiller = digest.get("a_surveiller", [])
    fallback = digest.get("fallback", False)
    marches_calmes = digest.get("marches_calmes", False)

    title = f"Albea Veille — {date_fr}"
    desc = f"Briefing patrimonial quotidien : {compte_articles} articles, {compte_forts} impacts forts."

    body_parts = [
        _header(date_fr, compte_articles, compte_forts, compte_moyens),
        _bandeau_marches_calmes() if marches_calmes else "",
        _bandeau_fallback() if fallback else "",
        _synthese(synthese) if synthese else "",
        _chiffres_cles(chiffres) if chiffres else "",
        '<main class="sections">',
    ]
    for section in sections:
        body_parts.append(_section(section))
    body_parts.append("</main>")
    if a_surveiller:
        body_parts.append(_a_surveiller(a_surveiller))
    body_parts.append(_footer(date_fr, fallback))

    body = "\n".join(p for p in body_parts if p)

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{html.escape(page_url)}">
<link rel="stylesheet" href="assets/digest.css">
</head>
<body>
{body}
</body>
</html>"""


def _header(date_fr: str, total: int, forts: int, moyens: int) -> str:
    return f"""<header>
<div class="brand">📊 ALBEA VEILLE</div>
<h1>Briefing patrimonial — {html.escape(date_fr)}</h1>
<div class="counters">
  <span class="counter"><b>{total}</b> articles</span>
  <span class="counter fort"><b>{forts}</b> forts</span>
  <span class="counter moyen"><b>{moyens}</b> moyens</span>
</div>
</header>"""


def _bandeau_marches_calmes() -> str:
    return '<div class="banner calme">🤷 Aucune actualite patrimoniale notable detectee dans les dernieres 24h.</div>'


def _bandeau_fallback() -> str:
    return '<div class="banner fallback">⚠️ Synthese IA indisponible (mode degrade) — liste brute des articles.</div>'


def _synthese(synthese: str) -> str:
    return f"""<section class="synthese">
<h2>Synthese du jour</h2>
<p>{html.escape(synthese)}</p>
</section>"""


def _chiffres_cles(chiffres: list[str]) -> str:
    items = "".join(f'<li>{html.escape(c)}</li>' for c in chiffres)
    return f"""<section class="chiffres">
<h2>📈 Chiffres cles</h2>
<ul>{items}</ul>
</section>"""


def _section(section) -> str:
    # Tolérant : les modèles IA peuvent renvoyer une section sous forme
    # de string au lieu d'un dict (variations entre modèles).
    if isinstance(section, str):
        return ""
    titre = section.get("titre", "Section")
    icone = section.get("icone", "📰")
    niveau_global = section.get("niveau_global", "")
    items = section.get("items", [])

    if not items:
        return ""

    items_html = "".join(_item(it) for it in items)
    badge = _badge_html(niveau_global) if niveau_global else ""

    return f"""<section class="section {html.escape(niveau_global)}">
<h2>{icone} {html.escape(titre)} {badge}</h2>
<div class="items">{items_html}</div>
</section>"""


def _item(item) -> str:
    if isinstance(item, str):
        return ""
    titre = html.escape(item.get("titre", ""))
    analyse = html.escape(item.get("analyse", ""))
    source = html.escape(item.get("source", ""))
    url = html.escape(item.get("url", "#"))
    niveau = item.get("niveau", "")

    analyse_html = f'<p class="analyse">{analyse}</p>' if analyse else ""
    badge = _badge_html(niveau)

    return f"""<a href="{url}" class="item {html.escape(niveau)}" target="_blank" rel="noopener">
  <div class="item-header">
    <span class="item-title">{titre}</span> {badge}
  </div>
  {analyse_html}
  <div class="item-source">— {source}</div>
</a>"""


def _badge_html(niveau: str) -> str:
    if not niveau:
        return ""
    return f'<span class="badge {html.escape(niveau)}">{html.escape(niveau.upper())}</span>'


def _a_surveiller(items: list[str]) -> str:
    lis = "".join(f"<li>{html.escape(s)}</li>" for s in items)
    return f"""<section class="a-surveiller">
<h2>👀 A surveiller dans les prochains jours</h2>
<ol>{lis}</ol>
</section>"""


def _footer(date_fr: str, fallback: bool) -> str:
    note = (
        "Synthese generee par IA (Opus 4.8)"
        if not fallback
        else "Mode degrade (IA indisponible)"
    )
    return f"""<footer>
<p>{html.escape(note)} • <a href="https://github.com/Nathandevg/albea-veille">Albea Veille</a> • Briefing du {html.escape(date_fr)}</p>
</footer>"""