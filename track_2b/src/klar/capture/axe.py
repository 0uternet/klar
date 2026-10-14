"""axe-core (vendored, MPL-2.0, unmodified) injection and mapping to Findings.

axe runs the WCAG 2.0/2.1 A/AA rules only. Each violation node becomes a
`failed` finding with source="rule" for every WCAG criterion in the rule's tags
(e.g. link-name → 2.4.4 and 4.1.2). `incomplete` results are kept in
page.axe["incomplete"] for checks that want them as candidates (e.g. 1.4.3).
Messages are localised with axe's own DE/FR/IT locale files.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from functools import lru_cache
from pathlib import Path

from klar.checks import registry
from klar.i18n import t
from klar.models import Finding

log = logging.getLogger(__name__)

VENDOR = Path(__file__).resolve().parent / "vendor"
WCAG_TAG = re.compile(r"^wcag(\d)(\d)(\d{1,2})$")
MAX_NODES_PER_RULE = 50

_RUN_JS = """async () => {
  const r = await axe.run(document, {
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
    resultTypes: ['violations', 'incomplete'],
    iframes: false,
  });
  const slim = (rules) => rules.map(x => ({ id: x.id, impact: x.impact, tags: x.tags, help: x.help,
    description: x.description, helpUrl: x.helpUrl,
    nodes: x.nodes.map(n => ({ target: n.target, html: n.html, failureSummary: n.failureSummary || '', impact: n.impact })) }));
  const acts = {};
  for (const rule of (axe.getRules ? axe.getRules() : [])) { if (rule.actIds && rule.actIds.length) acts[rule.ruleId] = rule.actIds; }
  return { version: axe.version, act_ids: acts, violations: slim(r.violations), incomplete: slim(r.incomplete),
           passes: r.passes.map(x => ({ id: x.id, tags: x.tags })),
           inapplicable: r.inapplicable.map(x => ({ id: x.id, tags: x.tags })) };
}"""

# Plain-language user impact for frequent rules; anything else gets impact.generic.
RULE_IMPACT: dict[str, dict[str, str]] = {
    "image-alt": {
        "en": "Screen-reader users do not learn what this image shows.",
        "de": "Screenreader-Nutzende erfahren nicht, was dieses Bild zeigt.",
        "fr": "Les utilisateurs de lecteurs d'écran ne savent pas ce que montre cette image.",
        "it": "Chi usa un lettore di schermo non sa cosa mostra questa immagine.",
    },
    "link-name": {
        "en": "Screen-reader users hear a link without a name and cannot tell where it leads.",
        "de": "Screenreader-Nutzende hören einen Link ohne Namen und wissen nicht, wohin er führt.",
        "fr": "Les utilisateurs de lecteurs d'écran entendent un lien sans nom et ne savent pas où il mène.",
        "it": "Chi usa un lettore di schermo sente un link senza nome e non sa dove porta.",
    },
    "button-name": {
        "en": "Screen-reader users hear a button without a name and cannot tell what it does.",
        "de": "Screenreader-Nutzende hören eine Schaltfläche ohne Namen und wissen nicht, was sie bewirkt.",
        "fr": "Les utilisateurs de lecteurs d'écran entendent un bouton sans nom et ne savent pas à quoi il sert.",
        "it": "Chi usa un lettore di schermo sente un pulsante senza nome e non sa cosa fa.",
    },
    "label": {
        "en": "Screen-reader users do not know what to enter in this field.",
        "de": "Screenreader-Nutzende wissen nicht, was sie in dieses Feld eingeben sollen.",
        "fr": "Les utilisateurs de lecteurs d'écran ne savent pas quoi saisir dans ce champ.",
        "it": "Chi usa un lettore di schermo non sa cosa inserire in questo campo.",
    },
    "color-contrast": {
        "en": "People with low vision may not be able to read this text.",
        "de": "Menschen mit Sehbehinderung können diesen Text eventuell nicht lesen.",
        "fr": "Les personnes malvoyantes risquent de ne pas pouvoir lire ce texte.",
        "it": "Le persone ipovedenti potrebbero non riuscire a leggere questo testo.",
    },
    "html-has-lang": {
        "en": "Screen readers may read the whole page with the wrong voice.",
        "de": "Screenreader lesen die ganze Seite eventuell mit der falschen Stimme vor.",
        "fr": "Les lecteurs d'écran risquent de lire toute la page avec la mauvaise voix.",
        "it": "I lettori di schermo potrebbero leggere tutta la pagina con la voce sbagliata.",
    },
    "valid-lang": {
        "en": "Screen readers cannot pick the right voice for this text.",
        "de": "Screenreader finden für diesen Text nicht die richtige Stimme.",
        "fr": "Les lecteurs d'écran ne trouvent pas la bonne voix pour ce texte.",
        "it": "I lettori di schermo non trovano la voce giusta per questo testo.",
    },
    "document-title": {
        "en": "People who switch between tabs or windows cannot tell what this page is.",
        "de": "Wer zwischen Tabs oder Fenstern wechselt, erkennt nicht, um welche Seite es sich handelt.",
        "fr": "Les personnes qui passent d'un onglet à l'autre ne savent pas de quelle page il s'agit.",
        "it": "Chi passa da una scheda all'altra non capisce di quale pagina si tratta.",
    },
}
RULE_IMPACT["html-lang-valid"] = RULE_IMPACT["valid-lang"]
RULE_IMPACT["input-image-alt"] = RULE_IMPACT["image-alt"]
RULE_IMPACT["role-img-alt"] = RULE_IMPACT["image-alt"]
RULE_IMPACT["svg-img-alt"] = RULE_IMPACT["image-alt"]
RULE_IMPACT["area-alt"] = RULE_IMPACT["link-name"]
RULE_IMPACT["select-name"] = RULE_IMPACT["label"]


@lru_cache(maxsize=1)
def axe_source() -> str:
    return (VENDOR / "axe.min.js").read_text(encoding="utf-8")


@lru_cache(maxsize=4)
def axe_locale(lang: str) -> dict | None:
    p = VENDOR / "axe-locales" / f"{lang}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def criteria_of(tags: list[str]) -> list[str]:
    out = []
    for tag in tags:
        m = WCAG_TAG.match(tag)
        if m:
            number = ".".join(m.groups())
            if number in registry.BY_NUMBER and number not in out:
                out.append(number)
    return out


def run_axe(live_page, ui_lang: str = "en") -> dict:
    """Inject axe-core into the live page and run it. Returns a JSON-able dict."""
    live_page.evaluate(axe_source())
    locale = axe_locale(ui_lang) if ui_lang != "en" else None
    if locale:
        live_page.evaluate("l => axe.configure({ locale: l })", locale)
    result = live_page.evaluate(_RUN_JS)
    # Rewrite axe's selectors in our canonical form (klar_extract.js cssPath) so that
    # findings about one element share one selector across axe and our checks.
    nodes = [n for group in ("violations", "incomplete") for rule in result.get(group, []) for n in rule["nodes"]]
    raw = [_selector(n.get("target") or []) for n in nodes]
    from klar.capture.browser import js

    try:
        canon = live_page.evaluate(js(
            "sels => sels.map(s => { if (!s) return null; try { const el = document.querySelector(s);"
            " return el && window.__klar ? window.__klar.cssPath(el) : s; } catch (e) { return s; } })"), raw)
    except Exception:
        canon = raw
    for n, sel in zip(nodes, canon):
        n["selector"] = sel
    tested: set[str] = set()
    for group in ("violations", "incomplete", "passes"):
        for rule in result.get(group, []):
            tested.update(criteria_of(rule.get("tags", [])))
    result["criteria_tested"] = sorted(tested, key=registry.sort_key)
    return result


def _selector(target: list) -> str | None:
    """axe target → CSS selector in the main document (iframe/shadow targets skipped)."""
    if len(target) == 1 and isinstance(target[0], str):
        return target[0]
    return None


def axe_findings(axe: dict, page_url: str, criteria: set[str] | None, ui_lang: str) -> list[Finding]:
    out: list[Finding] = []
    act_ids = axe.get("act_ids") or {}
    for rule in axe.get("violations", []):
        crits = [c for c in criteria_of(rule.get("tags", [])) if criteria is None or c in criteria]
        if not crits:
            continue
        impact = RULE_IMPACT.get(rule["id"], {})
        for node in rule.get("nodes", [])[:MAX_NODES_PER_RULE]:
            selector = node.get("selector") or _selector(node.get("target") or [])
            if not selector:
                continue
            for crit in crits:
                c = registry.get(crit)
                fid = hashlib.sha1(f"{page_url}{selector}{crit}{rule['id']}".encode("utf-8")).hexdigest()[:12]
                out.append(Finding(
                    id=fid, criterion=crit, criterion_name=c.name, level=c.level,
                    act_rule=(act_ids.get(rule["id"]) or [None])[0],  # only the ACT rule axe implements
                    en301549=c.en301549, outcome="failed", source="rule", confidence="high",
                    page_url=page_url, selector=selector, excerpt=node.get("html", "")[:2000], context_shown={},
                    explanation=t("axe.explanation", ui_lang, rule=rule["id"], help=rule.get("help", "")),
                    user_impact=impact.get(ui_lang) or impact.get("en") or t("impact.generic", ui_lang),
                    fix_diff=None,
                    fix_hint=(node.get("failureSummary") or rule.get("description") or "").strip() or None,
                    screenshot=None, model=None, axe_rule=rule["id"], reason_code="axe", reason=None,
                ))
    return out
