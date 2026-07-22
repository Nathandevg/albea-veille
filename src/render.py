"""
Rendu HTML du digest quotidien.

Génère un document HTML5 mobile-first, avec palette sobre,
badges par niveau d'impact, et liens cliquables vers les sources.
Pas de dépendance externe (template string-based, pas de Jinja).
"""

from __future__ import annotations

import html
from datetime import datetime


def render_digest(digest: dict, page_url: str = "", embed_css: bool = True) -> str:
    """
    Rend le digest en HTML5 complet.

    Args:
        digest: Dict produit par synthesizer.synthesize_digest().
        page_url: URL canonique de la page (pour les balises meta).
        embed_css: Si True, incorpore le CSS dans une balise <style>.
                   Permet au fichier d'etre autonome et correctement rendu
                   meme heberge sur paste.rs ou autre serveur de fichiers bruts.
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
        _trading_agents_section(digest),
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
{_embedded_css() if embed_css else ''}
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


def _trading_agents_section(digest: dict) -> str:
    """Section TradingAgents Intelligence de Marché.
    Affichée dans le digest, donne au CGP une vue marché multi-agent
    générée par l'IA en complément des actualités patrimoniales.
    """
    ta = digest.get("trading_agents", {})
    if not ta:
        # Si pas de donnée TradingAgents, on affiche un lien vers le projet
        return """<section class="section trading-agents">
<h2>🤖 TradingAgents Intelligence de Marché</h2>
<div class="items"><a href="https://github.com/Nathandevg/albea-veille/blob/main/daily_ta_analysis.py" class="item" target="_blank" rel="noopener">
<div class="item-header"><span class="item-title">Activer l'analyse marché multi-agents</span></div>
<p class="analyse">Analyse multi-agents (TradingAgents) : débat entre analystes fondamentaux, techniques, sentiment et risque pour les marchés suivis. Configuration dans daily_ta_analysis.py</p>
<div class="item-source">— <a href="https://github.com/TauricResearch/TradingAgents">TauricResearch/TradingAgents</a></div>
</a></div>
</section>"""

    tickers = ta.get("tickers", ["CAC40", "S&P500", "BTC-USD"])
    sections_html = ""

    for ticker_data in ta.get("analyses", []):
        ticker = ticker_data.get("ticker", "—")
        decision = ticker_data.get("decision", "HOLD")
        confidence = ticker_data.get("confidence", "N/A")
        reasoning = ticker_data.get("reasoning", "")
        sentiment = ticker_data.get("sentiment", "")
        risk = ticker_data.get("risk", "")

        decision_badge = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪"}.get(decision.upper(), "⚪")

        items_html = f"""<a href="#" class="item {sentiment.lower() if sentiment in ('FORT','MOYEN','FAIBLE') else ''}" onclick="return false">
  <div class="item-header">
    <span class="item-title"><b>{ticker}</b> {decision_badge} {decision} (confiance: {confidence})</span>
  </div>
  <p class="analyse"><b>Raisonnement :</b> {html.escape(reasoning[:300])}</p>
  <p class="analyse"><b>Sentiment :</b> {html.escape(sentiment)} &nbsp;|&nbsp; <b>Risque :</b> {html.escape(risk)}</p>
  <div class="item-source">Analyse multi-agents TradingAgents</div>
</a>"""

        sections_html += f"""<div class="items">{items_html}</div>"""

    return f"""<section class="section trading-agents">
<h2>🤖 TradingAgents — Intelligence de Marché</h2>
{sections_html}
<div class="item-source" style="padding: 8px 20px; font-size: 12px;">
Analyse générée par <a href="https://github.com/TauricResearch/TradingAgents" target="_blank" rel="noopener">TradingAgents</a> —
débat multi-agents (fondamental, technique, sentiment, risque)
| <a href="https://github.com/Nathandevg/albea-veille/blob/main/daily_ta_analysis.py" target="_blank">Configurer les tickers</a>
</div>
</section>"""


def _chiffres_cles(chiffres: list) -> str:
    items = "".join(
        f"<li>{html.escape(str(c))}</li>" for c in chiffres
    )
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


def _embedded_css() -> str:
    """Renvoie le CSS inline dans une balise <style>.
    Le fichier HTML devient autonome : rendu correct meme heberge
    sur paste.rs ou autre serveur de fichiers bruts.
    """
    return """<style>
:root {
  --bg: #f8f9fb;
  --surface: #ffffff;
  --text: #1a1f2e;
  --text-soft: #5a6175;
  --border: #e3e7ef;
  --brand: #1c3a5e;
  --brand-soft: #e8eef7;
  --fort: #c0392b;
  --fort-bg: #fde9e7;
  --moyen: #d68910;
  --moyen-bg: #fdf2dd;
  --faible: #7f8c8d;
  --faible-bg: #f0f1f3;
  --link: #2c5282;
  --shadow: 0 1px 3px rgba(0,0,0,0.06);
  --radius: 8px;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0f1419; --surface: #1a2129; --text: #e6eaf0;
    --text-soft: #9aa3b2; --border: #2a3441; --brand: #6b9bd6;
    --brand-soft: #1e2a3a; --fort: #ff6b5b; --fort-bg: #3a1f1c;
    --moyen: #f4b740; --moyen-bg: #3a2f1a; --faible: #7a8693;
    --faible-bg: #2a2f36; --link: #7ab3e0;
    --shadow: 0 1px 3px rgba(0,0,0,0.3);
  }
}
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;background:var(--bg);color:var(--text);line-height:1.5;font-size:16px;-webkit-font-smoothing:antialiased}
a{color:var(--link);text-decoration:none}
a:hover{text-decoration:underline}
header{background:var(--brand);color:#fff;padding:24px 20px 28px;text-align:center}
.brand{font-size:13px;letter-spacing:0.18em;font-weight:600;opacity:0.85;margin-bottom:8px}
header h1{font-size:22px;font-weight:600;margin:0 0 16px;line-height:1.3}
.counters{display:flex;justify-content:center;gap:8px;flex-wrap:wrap}
.counter{background:rgba(255,255,255,0.15);padding:4px 12px;border-radius:999px;font-size:13px}
.counter b{font-size:16px}
.counter.fort{background:rgba(192,57,43,0.85)}
.counter.moyen{background:rgba(214,137,16,0.85)}
.banner{margin:16px 20px;padding:12px 16px;border-radius:var(--radius);text-align:center;font-size:14px}
.banner.calme{background:var(--faible-bg);color:var(--text-soft)}
.banner.fallback{background:var(--moyen-bg);color:var(--moyen)}
section{margin:24px 20px;background:var(--surface);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow)}
section h2{font-size:18px;font-weight:600;margin:0 0 14px;color:var(--brand)}
.synthese p{margin:0;font-size:16px;color:var(--text);font-style:italic}
.chiffres ul{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:8px}
.chiffres li{background:var(--brand-soft);color:var(--brand);padding:6px 12px;border-radius:var(--radius);font-size:14px;font-weight:500}
.section{padding:0;overflow:hidden}
.section h2{padding:16px 20px;margin:0;background:var(--brand-soft);border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px;font-size:16px}
.items{display:grid;gap:1px;background:var(--border)}
.item{display:block;background:var(--surface);padding:14px 20px;color:var(--text);border-left:3px solid transparent;transition:background 0.1s}
.item:hover{background:var(--brand-soft);text-decoration:none}
.item-header{display:flex;justify-content:space-between;align-items:flex-start;gap:8px;margin-bottom:6px}
.item-title{font-weight:600;font-size:15px;line-height:1.4;flex:1}
.analyse{margin:6px 0;font-size:14px;color:var(--text-soft);line-height:1.5}
.item-source{font-size:12px;color:var(--text-soft);opacity:0.8;margin-top:4px}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;letter-spacing:0.05em;flex-shrink:0}
.badge.fort{background:var(--fort-bg);color:var(--fort)}
.badge.moyen{background:var(--moyen-bg);color:var(--moyen)}
.badge.faible{background:var(--faible-bg);color:var(--faible)}
.a-surveiller ol{margin:0;padding-left:20px}
.a-surveiller li{margin:8px 0;font-size:15px;color:var(--text)}
footer{text-align:center;padding:30px 20px 40px;font-size:12px;color:var(--text-soft)}
footer a{color:var(--text-soft);text-decoration:underline}
@media(min-width:768px){
.sections{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:0 20px}
.sections .section{margin:0}
header h1{font-size:26px}
}
</style>"""