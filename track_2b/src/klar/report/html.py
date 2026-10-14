"""Standalone HTML report: one file, inline CSS (Klar. colour tokens, light + dark),
no external requests, screenshots embedded as data URIs. It starts with the
mandatory disclaimer and is itself accessible (landmarks, skip link, lang,
headings, status = shape + text, never colour alone)."""

from __future__ import annotations

import base64
import html
import re
from pathlib import Path

from klar import __version__
from klar.checks import registry
from klar.models import Finding, Scan

L = {
    "title": {"en": "Accessibility pre-check", "de": "Barrierefreiheits-Vorprüfung", "fr": "Pré-contrôle d'accessibilité", "it": "Pre-verifica dell'accessibilità"},
    "skip": {"en": "Skip to findings", "de": "Zu den Befunden springen", "fr": "Aller aux constats", "it": "Vai ai risultati"},
    "page": {"en": "Page", "de": "Seite", "fr": "Page", "it": "Pagina"},
    "date": {"en": "Date", "de": "Datum", "fr": "Date", "it": "Data"},
    "mode": {"en": "Where your page went", "de": "Wohin Ihre Seite ging", "fr": "Où votre page est allée", "it": "Dove è andata la pagina"},
    "model": {"en": "Model", "de": "Modell", "fr": "Modèle", "it": "Modello"},
    "ext": {"en": "AI requests that left this network", "de": "KI-Anfragen, die dieses Netz verlassen haben", "fr": "Requêtes IA sorties de ce réseau", "it": "Richieste IA uscite da questa rete"},
    "summary": {"en": "Summary", "de": "Übersicht", "fr": "Résumé", "it": "Riepilogo"},
    "findings": {"en": "Findings to review", "de": "Zu prüfende Befunde", "fr": "Constats à vérifier", "it": "Risultati da verificare"},
    "passed_list": {"en": "Passed elements", "de": "Bestandene Elemente", "fr": "Éléments réussis", "it": "Elementi superati"},
    "none": {"en": "Nothing to review.", "de": "Nichts zu prüfen.", "fr": "Rien à vérifier.", "it": "Niente da verificare."},
    "element": {"en": "Element", "de": "Element", "fr": "Élément", "it": "Elemento"},
    "evidence": {"en": "Evidence", "de": "Beleg", "fr": "Preuve", "it": "Prova"},
    "explanation": {"en": "Explanation", "de": "Erklärung", "fr": "Explication", "it": "Spiegazione"},
    "fix": {"en": "Fix", "de": "Korrektur", "fr": "Correction", "it": "Correzione"},
    "decided": {"en": "Decided by", "de": "Entschieden durch", "fr": "Décidé par", "it": "Deciso da"},
    "context": {"en": "Context shown to the model", "de": "Kontext, den das Modell sah", "fr": "Contexte montré au modèle", "it": "Contesto mostrato al modello"},
    "screenshot": {"en": "Screenshot of the element", "de": "Bildschirmfoto des Elements", "fr": "Capture de l'élément", "it": "Schermata dell'elemento"},
    "coverage": {"en": "Coverage of the 50 WCAG 2.1 A/AA criteria", "de": "Abdeckung der 50 Kriterien WCAG 2.1 A/AA", "fr": "Couverture des 50 critères WCAG 2.1 A/AA", "it": "Copertura dei 50 criteri WCAG 2.1 A/AA"},
    "criterion": {"en": "Criterion", "de": "Kriterium", "fr": "Critère", "it": "Criterio"},
    "level": {"en": "Level", "de": "Stufe", "fr": "Niveau", "it": "Livello"},
    "method": {"en": "Method", "de": "Methode", "fr": "Méthode", "it": "Metodo"},
    "this_scan": {"en": "Pre-checked in this scan", "de": "In diesem Scan vorgeprüft", "fr": "Pré-contrôlé dans cette analyse", "it": "Pre-verificato in questa scansione"},
    "yes": {"en": "yes", "de": "ja", "fr": "oui", "it": "sì"},
    "no": {"en": "no", "de": "nein", "fr": "non", "it": "no"},
    "count": {"en": "Count", "de": "Anzahl", "fr": "Nombre", "it": "Numero"},
    "verdict": {"en": "Verdict", "de": "Ergebnis", "fr": "Verdict", "it": "Esito"},
}
OUTCOME = {
    "failed": ("■", {"en": "Failed", "de": "Nicht bestanden", "fr": "Échec", "it": "Non superato"}),
    "cantTell": ("◆", {"en": "Needs review", "de": "Zu prüfen", "fr": "À vérifier", "it": "Da verificare"}),
    "passed": ("●", {"en": "Passed", "de": "Bestanden", "fr": "Réussi", "it": "Superato"}),
    "inapplicable": ("○", {"en": "N/A", "de": "N/A", "fr": "N/A", "it": "N/A"}),
}
SOURCE = {
    "rule": {"en": "rule (axe-core / code)", "de": "Regel (axe-core / Code)", "fr": "règle (axe-core / code)", "it": "regola (axe-core / codice)"},
    "heuristic": {"en": "code heuristic", "de": "Code-Heuristik", "fr": "heuristique de code", "it": "euristica di codice"},
    "apertus": {"en": "Apertus, guarded", "de": "Apertus, geprüft", "fr": "Apertus, vérifié", "it": "Apertus, verificato"},
}
CONFIDENCE = {"high": {"en": "high", "de": "hoch", "fr": "élevée", "it": "alta"},
              "medium": {"en": "medium", "de": "mittel", "fr": "moyenne", "it": "media"},
              "low": {"en": "low", "de": "niedrig", "fr": "faible", "it": "bassa"}}
STATUS = {"to_review": {"en": "to review", "de": "offen", "fr": "à vérifier", "it": "da verificare"},
          "accepted": {"en": "accepted", "de": "akzeptiert", "fr": "accepté", "it": "accettato"},
          "rejected": {"en": "rejected", "de": "abgelehnt", "fr": "rejeté", "it": "respinto"}}
METHOD = {"rule": {"en": "rule", "de": "Regel", "fr": "règle", "it": "regola"},
          "apertus_text": {"en": "Apertus text", "de": "Apertus Text", "fr": "Apertus texte", "it": "Apertus testo"},
          "apertus_vision": {"en": "Apertus vision", "de": "Apertus Bild", "fr": "Apertus image", "it": "Apertus immagine"},
          "human": {"en": "human", "de": "Mensch", "fr": "humain", "it": "umano"},
          "experimental": {"en": "experimental", "de": "experimentell", "fr": "expérimental", "it": "sperimentale"}}
MODE = {"local": {"en": "On-premise · data stays on this machine", "de": "On-Premise · Daten bleiben auf diesem Rechner", "fr": "Sur site · les données restent sur cette machine", "it": "On-premise · i dati restano su questa macchina"},
        "swiss_cloud": {"en": "Swiss cloud · processed in Switzerland", "de": "Schweizer Cloud · Verarbeitung in der Schweiz", "fr": "Cloud suisse · traité en Suisse", "it": "Cloud svizzero · elaborato in Svizzera"},
        "external": {"en": "External provider · not sovereign: pages leave Switzerland", "de": "Externer Anbieter · nicht souverän: Seiten verlassen die Schweiz", "fr": "Fournisseur externe · non souverain : les pages quittent la Suisse", "it": "Fornitore esterno · non sovrano: le pagine lasciano la Svizzera"},
        "replay": {"en": "Replay · recorded Apertus answers, no network", "de": "Replay · aufgezeichnete Apertus-Antworten, kein Netz", "fr": "Replay · réponses Apertus enregistrées, sans réseau", "it": "Replay · risposte Apertus registrate, nessuna rete"}}

CSS = """
:root{--bg:#FAFAF7;--surface:#FFFFFF;--ink:#0F1115;--muted:#565B66;--line:#E4E2DC;--klar-red:#D0021B;--red-text:#B00016;--green:#13703A;--amber:#8A4B00;--blue:#1F4FD8;
--sans:Inter,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;--mono:"JetBrains Mono",ui-monospace,SFMono-Regular,Consolas,monospace}
@media (prefers-color-scheme:dark){:root{--bg:#0B0C0F;--surface:#15171C;--ink:#F2F1EC;--muted:#A3A8B3;--line:#2A2D35;--klar-red:#FF4D4F;--red-text:#FF4D4F;--green:#3DD47A;--amber:#F2A93B;--blue:#7FA2FF}}
*{box-sizing:border-box}html{background:var(--bg);color:var(--ink);font:16px/1.5 var(--sans)}body{margin:0}
.wrap{max-width:1200px;margin:0 auto;padding:24px 16px}
a{color:var(--blue)}a:focus-visible,summary:focus-visible{outline:2px solid var(--blue);outline-offset:2px}
.skip{position:absolute;left:-9999px}.skip:focus{left:16px;top:16px;background:var(--surface);padding:8px}
.wordmark{font-weight:700;font-size:32px;letter-spacing:-.02em;margin:0;line-height:1.1}
.wordmark .dot{display:inline-block;width:.18em;height:.18em;background:var(--klar-red);margin-left:.03em}
h1{font-size:24px;margin:8px 0 24px}h2{font-size:20px;margin:48px 0 16px}h3{font-size:16px;margin:0 0 8px}
.disclaimer{border-left:4px solid var(--klar-red);padding:12px 16px;background:var(--surface);margin:0 0 24px}
dl.meta{display:grid;grid-template-columns:max-content 1fr;gap:4px 16px;margin:0}dl.meta dt{color:var(--muted)}dl.meta dd{margin:0;overflow-wrap:anywhere}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:16px;margin:0 0 16px}
.card dl{display:grid;grid-template-columns:max-content 1fr;gap:6px 16px;margin:12px 0 0}.card dt{color:var(--muted)}.card dd{margin:0;min-width:0}
.chip{display:inline-flex;gap:6px;align-items:center;border-radius:999px;padding:2px 10px;border:1px solid currentColor;font-size:14px;font-weight:600;margin-right:8px}
.o-failed{color:var(--red-text)}.o-cantTell{color:var(--amber)}.o-passed{color:var(--green)}.o-inapplicable{color:var(--muted)}
code,pre{font-family:var(--mono);font-size:14px}pre{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:8px;white-space:pre-wrap;overflow-wrap:anywhere;margin:0}
.impact{font-size:18px;margin:4px 0}.shot{max-width:100%;max-height:240px;border:1px solid var(--line);border-radius:8px}
footer{color:var(--muted);font-size:14px;margin-top:48px;border-top:1px solid var(--line);padding-top:16px}
@media (max-width:640px){.card dl,dl.meta{grid-template-columns:1fr}}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
"""


def model_line(model: str) -> str:
    """Computed, never hard-coded: only Apertus models get the licence line."""
    if re.match(r"^swiss-ai/Apertus", model or "", re.IGNORECASE):
        return f"{model} · open weights · Apache-2.0"
    return model or "—"


def _l(key: str, lang: str) -> str:
    return L[key].get(lang) or L[key]["en"]


def _e(s: object) -> str:
    return html.escape("" if s is None else str(s))


def _chip(outcome: str, lang: str) -> str:
    shape, labels = OUTCOME[outcome]
    return f'<span class="chip o-{outcome}"><span aria-hidden="true">{shape}</span>{_e(labels.get(lang, labels["en"]))}</span>'


def _shot(f: Finding, assets_dir: Path | None, lang: str) -> str:
    if not f.screenshot or not assets_dir:
        return ""
    p = assets_dir / "crops" / f.screenshot
    if not p.is_file():
        return ""
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return f'<dt>{_e(_l("screenshot", lang))}</dt><dd><img class="shot" src="data:image/png;base64,{data}" alt="{_e(_l("screenshot", lang))}"></dd>'


def _card(f: Finding, lang: str, assets_dir: Path | None) -> str:
    rows = [
        f'<dt>{_e(_l("element", lang))}</dt><dd><code>{_e(f.selector)}</code></dd>',
        f'<dt>{_e(_l("evidence", lang))}</dt><dd><pre><code>{_e(f.excerpt)}</code></pre></dd>',
        _shot(f, assets_dir, lang),
        f'<dt>{_e(_l("explanation", lang))}</dt><dd>{_e(f.explanation)}</dd>',
    ]
    if f.fix_hint or f.fix_diff:
        fix = _e(f.fix_hint or "")
        if f.fix_diff:
            fix += f'<pre><code>{_e(f.fix_diff)}</code></pre>'
        rows.append(f'<dt>{_e(_l("fix", lang))}</dt><dd>{fix}</dd>')
    decided = SOURCE[f.source].get(lang, SOURCE[f.source]["en"])
    if f.model:
        decided += f" ({_e(f.model)})"
    rows.append(f'<dt>{_e(_l("decided", lang))}</dt><dd>{_e(decided)} · '
                f'{_e(CONFIDENCE[f.confidence][lang])} · {_e(STATUS[f.status][lang])}</dd>')
    ctx = ""
    if f.context_shown:
        items = "".join(f"<dt>{_e(k)}</dt><dd><pre><code>{_e(v)}</code></pre></dd>" for k, v in f.context_shown.items())
        ctx = f'<details><summary>{_e(_l("context", lang))}</summary><dl>{items}</dl></details>'
    crit = registry.get(f.criterion)
    return (f'<article class="card" id="f-{_e(f.id)}" aria-labelledby="h-{_e(f.id)}">'
            f'<h3 id="h-{_e(f.id)}">{_chip(f.outcome, lang)}<code>{_e(f.criterion)}</code> {_e(crit.name)}</h3>'
            f'<p class="impact">{_e(f.user_impact)}</p><dl>{"".join(rows)}</dl>{ctx}</article>')


def to_html(scan: Scan, assets_dir: Path | None = None) -> str:
    from klar.report import disclaimer

    lang = scan.ui_lang
    review = [f for f in scan.findings if f.outcome in ("failed", "cantTell")]
    passed = [f for f in scan.findings if f.outcome in ("passed", "inapplicable")]
    counts = scan.stats
    checked = set(scan.stats.get("criteria_list") or [])
    ai = scan.stats.get("ai_requests") or {}

    summary_rows = "".join(f"<tr><td>{_chip(o, lang)}</td><td>{int(counts.get(o, 0))}</td></tr>" for o in OUTCOME)
    cards = "".join(_card(f, lang, assets_dir) for f in review) or f"<p>{_e(_l('none', lang))}</p>"
    passed_rows = "".join(
        f"<tr><td><code>{_e(f.criterion)}</code></td><td>{_chip(f.outcome, lang)}</td>"
        f"<td><code>{_e(f.selector)}</code></td><td>{_e(f.excerpt[:120])}</td></tr>" for f in passed)
    passed_html = (f'<details><summary>{_e(_l("passed_list", lang))} ({len(passed)})</summary>'
                   f'<table><thead><tr><th scope="col">{_e(_l("criterion", lang))}</th><th scope="col">{_e(_l("verdict", lang))}</th>'
                   f'<th scope="col">{_e(_l("element", lang))}</th><th scope="col">{_e(_l("evidence", lang))}</th></tr></thead>'
                   f'<tbody>{passed_rows}</tbody></table></details>') if passed else ""
    cov_rows = "".join(
        f"<tr><td><code>{_e(c.number)}</code></td><td>{_e(c.name)}</td><td>{_e(c.level)}</td>"
        f"<td>{_e(METHOD[c.method][lang])}</td><td>{_e(_l('yes' if c.number in checked else 'no', lang))}</td></tr>"
        for c in registry.CRITERIA)
    mode = MODE[scan.mode].get(lang, MODE[scan.mode]["en"])

    return f"""<!doctype html>
<html lang="{_e(lang)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'">
<title>Klar. · {_e(_l("title", lang))} · {_e(scan.url)}</title>
<style>{CSS}</style>
</head>
<body>
<a class="skip" href="#findings">{_e(_l("skip", lang))}</a>
<div class="wrap">
<header>
<p class="wordmark">Klar<span class="dot" aria-hidden="true"></span><span class="skip">.</span></p>
<h1>{_e(_l("title", lang))}</h1>
</header>
<main>
<p class="disclaimer"><strong>{_e(disclaimer(scan))}</strong></p>
<dl class="meta">
<dt>{_e(_l("page", lang))}</dt><dd><a href="{_e(scan.url)}">{_e(scan.url)}</a></dd>
<dt>{_e(_l("date", lang))}</dt><dd>{_e(scan.created_at.strftime("%Y-%m-%d %H:%M UTC"))}</dd>
<dt>{_e(_l("mode", lang))}</dt><dd>{_e(mode)}</dd>
<dt>{_e(_l("model", lang))}</dt><dd>{_e(model_line(scan.model))}</dd>
<dt>{_e(_l("ext", lang))}</dt><dd>{int(ai.get("swiss_cloud", 0)) + int(ai.get("external", 0))}
(Swiss cloud {int(ai.get("swiss_cloud", 0))} · external {int(ai.get("external", 0))} · local {int(ai.get("local", 0))})</dd>
</dl>
<section aria-labelledby="h-summary">
<h2 id="h-summary">{_e(_l("summary", lang))}</h2>
<table><thead><tr><th scope="col">{_e(_l("verdict", lang))}</th><th scope="col">{_e(_l("count", lang))}</th></tr></thead>
<tbody>{summary_rows}</tbody></table>
</section>
<section id="findings" aria-labelledby="h-findings" tabindex="-1">
<h2 id="h-findings">{_e(_l("findings", lang))} ({len(review)})</h2>
{cards}
{passed_html}
</section>
<section aria-labelledby="h-coverage">
<h2 id="h-coverage">{_e(_l("coverage", lang))}</h2>
<table><thead><tr><th scope="col">{_e(_l("criterion", lang))}</th><th scope="col">WCAG 2.1</th><th scope="col">{_e(_l("level", lang))}</th>
<th scope="col">{_e(_l("method", lang))}</th><th scope="col">{_e(_l("this_scan", lang))}</th></tr></thead>
<tbody>{cov_rows}</tbody></table>
</section>
</main>
<footer><p>Klar. {_e(__version__)} · Apertus (swiss-ai) · axe-core (MPL-2.0)</p></footer>
</div>
</body>
</html>
"""
