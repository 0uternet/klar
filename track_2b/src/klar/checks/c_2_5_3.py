"""2.5.3 Label in Name, level A. ACT rule 2ee8b8 (visible label is part of accessible name).
Techniques G208 / G211, failure F96.

Candidates: links, buttons, role widgets and form fields whose accessible name is set by
aria-label or aria-labelledby (otherwise the name is the visible text and the criterion
holds by construction). capture/js/c_2_5_3_controls.js returns the visible label: the
rendered text for widgets, the visible <label> for fields, the value of input buttons.
The accessible name is Chromium's (DevTools protocol) where the extractor has it.

Decided in code (matching ignores case, punctuation and symbols, as ACT 2ee8b8)
  * no visible text label (icon, symbol only, image only)          → not a candidate
  * the visible label's words appear contiguously in the name       → passed (G208/G211)
  * all label words appear in the name, but not in that order      → failed (F96, ACT 2ee8b8)
  * the control holds several text blocks (heading + sentence + call to action) and the
    name is one of them                                             → cantTell (which text is the label?)
  * a field without a visible <label>, only a placeholder           → cantTell (label vs nearby text)
  * otherwise                                                       → failed (F96)
Asked to Apertus (one categorical question) only when the visible "label" is a single short
token that may be an icon glyph or a symbol rather than a word:
  "Is the visible text a word label, or an icon or symbol?"  word_label | icon_or_symbol | unsure
  mapped in code: icon_or_symbol → passed (symbols are not text labels), word_label → failed, unsure → cantTell.

Known limits: text inside images of text is not read (vision); visible labels placed next to a
widget without <label> are not paired; the name of buttons outside the shared extractor comes
from the JS fallback (aria-labelledby, aria-label), not from Chromium.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema, norm_ws, set_attr, unified_diff
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "2.5.3/v1"
JS_PATH = Path(__file__).resolve().parents[1] / "capture" / "js" / "c_2_5_3_controls.js"
_WORD = re.compile(r"\w+", re.UNICODE)
_LIGATURE = re.compile(r"^[a-z]+(?:_[a-z]+)+$")

CATEGORIES = ["word_label", "icon_or_symbol", "unsure"]


@lru_cache(maxsize=1)
def controls_js() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def words(s: str) -> list[str]:
    s = unicodedata.normalize("NFKC", s or "").casefold().replace("_", " ")
    return _WORD.findall(s)


def contains_seq(name: list[str], label: list[str]) -> bool:
    if not label or len(label) > len(name):
        return False
    return any(name[i:i + len(label)] == label for i in range(len(name) - len(label) + 1))


def classify(label: str, name: str, blocks: list[str], *, is_field: bool, label_source: str,
             placeholder: str) -> str:
    lw, nw = words(label), words(name)
    if is_field and label_source == "none":
        if placeholder and contains_seq(nw, words(placeholder)):
            return "match"
        return "unclear_label" if placeholder or nw else "skip"
    if not lw:
        return "skip"  # symbol / icon only: no text label (Understanding 2.5.3)
    if not nw:
        return "skip"  # no name at all: 4.1.2 / axe territory
    if contains_seq(nw, lw):
        return "match"
    if set(lw) <= set(nw):
        return "reordered"
    if len(blocks) >= 2 and any(contains_seq(nw, words(b)) or contains_seq(words(b), nw) for b in blocks):
        return "several_blocks"
    raw = label.strip()
    if " " not in raw and (len(raw) <= 3 or _LIGATURE.match(raw)):
        return "ask"
    return "mismatch"


class _Fallback(HTMLParser):
    """Static fallback (no live page): <a>/<button> with an id and aria-label, plain text content."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: list[dict] = []
        self.out: list[dict] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("a", "button") and a.get("id") and a.get("aria-label") is not None:
            self.stack.append({"tag": tag, "id": a["id"], "aria_label": a["aria-label"], "text": ""})

    def handle_data(self, data):
        for item in self.stack:
            item["text"] += data

    def handle_endtag(self, tag):
        if self.stack and self.stack[-1]["tag"] == tag:
            item = self.stack.pop()
            self.out.append(item)


register({
    "c253.match": {
        "en": "The accessible name “{name}” contains the visible label “{label}”.",
        "de": "Der zugängliche Name «{name}» enthält die sichtbare Beschriftung «{label}».",
        "fr": "Le nom accessible « {name} » contient l'étiquette visible « {label} ».",
        "it": "Il nome accessibile «{name}» contiene l'etichetta visibile «{label}».",
    },
    "c253.reordered": {
        "en": "The accessible name “{name}” uses the words of the visible label “{label}” in a different order, so the label is not contained in the name.",
        "de": "Der zugängliche Name «{name}» verwendet die Wörter der sichtbaren Beschriftung «{label}» in anderer Reihenfolge; die Beschriftung ist nicht im Namen enthalten.",
        "fr": "Le nom accessible « {name} » reprend les mots de l'étiquette visible « {label} » dans un autre ordre : l'étiquette n'y est pas contenue.",
        "it": "Il nome accessibile «{name}» usa le parole dell'etichetta visibile «{label}» in un altro ordine: l'etichetta non è contenuta nel nome.",
    },
    "c253.mismatch": {
        "en": "The accessible name “{name}” does not contain the visible label “{label}”.",
        "de": "Der zugängliche Name «{name}» enthält die sichtbare Beschriftung «{label}» nicht.",
        "fr": "Le nom accessible « {name} » ne contient pas l'étiquette visible « {label} ».",
        "it": "Il nome accessibile «{name}» non contiene l'etichetta visibile «{label}».",
    },
    "c253.several_blocks": {
        "en": "The control shows several texts (“{label}”) and its name “{name}” repeats only one of them. Which text is the label is a judgement: a person must decide.",
        "de": "Das Element zeigt mehrere Texte («{label}»), sein Name «{name}» wiederholt nur einen davon. Welcher Text die Beschriftung ist, muss eine Person entscheiden.",
        "fr": "Le contrôle affiche plusieurs textes (« {label} ») et son nom « {name} » n'en reprend qu'un. Quel texte est l'étiquette relève du jugement : une personne doit trancher.",
        "it": "Il controllo mostra più testi («{label}») e il suo nome «{name}» ne riprende solo uno. Quale testo sia l'etichetta va giudicato: una persona deve decidere.",
    },
    "c253.unclear_label": {
        "en": "This field has no visible label element, only nearby text or a placeholder; its name is “{name}”. A person must decide which text is its label.",
        "de": "Dieses Feld hat kein sichtbares Label, nur Text in der Nähe oder einen Platzhalter; sein Name ist «{name}». Eine Person muss entscheiden, welcher Text die Beschriftung ist.",
        "fr": "Ce champ n'a pas d'étiquette visible, seulement un texte proche ou un placeholder ; son nom est « {name} ». Une personne doit décider quel texte est son étiquette.",
        "it": "Questo campo non ha un'etichetta visibile, solo testo vicino o un placeholder; il suo nome è «{name}». Una persona deve decidere quale testo sia l'etichetta.",
    },
    "c253.apertus_icon": {
        "en": "Apertus judged that the visible “{label}” is an icon or symbol, not a word label; any descriptive name is fine.",
        "de": "Apertus beurteilt, dass das sichtbare «{label}» ein Symbol ist, keine Wortbeschriftung; jeder beschreibende Name ist zulässig.",
        "fr": "Apertus juge que le « {label} » visible est une icône ou un symbole, pas une étiquette textuelle ; tout nom descriptif convient.",
        "it": "Apertus giudica che «{label}» visibile sia un'icona o un simbolo, non un'etichetta testuale; qualsiasi nome descrittivo va bene.",
    },
    "c253.apertus_unsure": {
        "en": "Apertus could not decide whether “{label}” is a word label. A person must check that the name “{name}” contains it.",
        "de": "Apertus konnte nicht entscheiden, ob «{label}» eine Wortbeschriftung ist. Eine Person muss prüfen, ob der Name «{name}» sie enthält.",
        "fr": "Apertus n'a pas pu décider si « {label} » est une étiquette textuelle. Une personne doit vérifier que le nom « {name} » la contient.",
        "it": "Apertus non ha potuto decidere se «{label}» sia un'etichetta testuale. Una persona deve verificare che il nome «{name}» la contenga.",
    },
    "c253.fix_hint": {
        "en": "Start the aria-label with the visible text “{label}”, or remove the aria-label so the visible text becomes the name.",
        "de": "Beginnen Sie das aria-label mit dem sichtbaren Text «{label}» oder entfernen Sie das aria-label, damit der sichtbare Text der Name wird.",
        "fr": "Commencez l'aria-label par le texte visible « {label} », ou supprimez l'aria-label pour que le texte visible devienne le nom.",
        "it": "Iniziate l'aria-label con il testo visibile «{label}», oppure rimuovete l'aria-label perché il testo visibile diventi il nome.",
    },
    "c253.impact": {
        "en": "Speech-input users who say “{label}” cannot activate this control, and screen-reader users hear a different name than what is shown.",
        "de": "Wer per Sprache «{label}» sagt, kann dieses Element nicht auslösen, und Screenreader-Nutzende hören einen anderen Namen als den angezeigten.",
        "fr": "Les personnes qui disent « {label} » en commande vocale ne peuvent pas activer ce contrôle, et les lecteurs d'écran annoncent un autre nom que celui affiché.",
        "it": "Chi usa la voce e dice «{label}» non può attivare questo controllo, e chi usa un lettore di schermo sente un nome diverso da quello mostrato.",
    },
    "c253.impact_ok": {
        "en": "Speech-input users can activate this control by saying its visible label.",
        "de": "Wer per Sprache steuert, kann dieses Element mit seiner sichtbaren Beschriftung auslösen.",
        "fr": "Les personnes en commande vocale peuvent activer ce contrôle en disant son étiquette visible.",
        "it": "Chi usa la voce può attivare questo controllo pronunciando la sua etichetta visibile.",
    },
})


class LabelInName(BaseCheck):
    criterion = "2.5.3"
    prompt_version = PROMPT_VERSION
    max_candidates = 150

    def candidates(self, page: CapturedPage) -> list[Candidate]:
        names = {r["selector"]: r.get("name") for r in [*page.links, *page.fields] if r.get("name")}
        records = self._controls(page)
        out: list[Candidate] = []
        for r in records:
            name = norm_ws(names.get(r["selector"]) or r.get("name_js") or r.get("aria_label") or "")
            label = norm_ws(r.get("label") or "")
            kind = classify(label, name, r.get("blocks") or [], is_field=bool(r.get("is_field")),
                            label_source=r.get("label_source", "content"), placeholder=r.get("placeholder") or "")
            if kind == "skip":
                continue
            text = label if label else norm_ws(r.get("placeholder") or "")
            out.append(self.candidate(page, selector=r["selector"], html=r.get("html", ""), text=text,
                                      accessible_name=name, lang=r.get("lang"), kind=kind, label=label,
                                      context={"visible_label": label, "accessible_name": name}))
        return out[: self.max_candidates]

    @staticmethod
    def _controls(page: CapturedPage) -> list[dict]:
        if page.live is not None:
            try:
                return page.evaluate(controls_js(), 300) or []
            except Exception:
                pass
        p = _Fallback()
        try:
            p.feed(page.html or "")
        except Exception:
            return []
        return [{"selector": f"#{x['id']}", "tag": x["tag"], "label": norm_ws(x["text"]), "label_source": "content",
                 "aria_label": x["aria_label"], "name_js": x["aria_label"], "blocks": [], "is_field": False,
                 "html": ""} for x in p.out]

    def decide(self, c: Candidate) -> Finding | None:
        kind, ui = c.extra.get("kind"), self.ui_lang
        label, name = c.extra.get("label", ""), c.accessible_name or ""
        kw = {"label": label[:120], "name": name[:120]}
        if kind == "match":
            return self.finding(c, outcome="passed", source="heuristic", confidence="high", act_rule="2ee8b8",
                                explanation=t("c253.match", ui, **kw), user_impact=t("c253.impact_ok", ui))
        if kind in ("reordered", "mismatch"):
            after = set_attr(c.html, "aria-label", label) if c.html.lstrip().startswith("<") else c.html
            return self.finding(c, outcome="failed", source="heuristic", confidence="high" if kind == "reordered" else "medium",
                                act_rule="2ee8b8", explanation=t(f"c253.{kind}", ui, **kw),
                                user_impact=t("c253.impact", ui, label=label[:80]),
                                fix_diff=unified_diff(c.html, after, c.selector) if label else None,
                                fix_hint=t("c253.fix_hint", ui, label=label[:80]))
        if kind in ("several_blocks", "unclear_label"):
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="low",
                                explanation=t(f"c253.{kind}", ui, **kw), user_impact=t("impact.review", ui))
        return None

    SYSTEM = (
        "You check WCAG 2.1 success criterion 2.5.3 Label in Name for ONE control. Its visible text is very short "
        "and its accessible name does not contain it. Symbols and icon glyphs (an arrow, a cross, a ligature name "
        "rendered by an icon font) are not text labels; words and abbreviations are. Classify the visible text:\n"
        "- word_label: a word or abbreviation that users read as the control's label\n"
        "- icon_or_symbol: an icon glyph or a symbol, not a word\n"
        "- unsure: cannot tell\n"
        "quote: the visible text, copied exactly."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        return self.task(system=self.system_prompt(self.SYSTEM, c),
                         element={"visible_text": c.extra.get("label", ""), "accessible_name": c.accessible_name or ""},
                         context={}, question="Is the visible text a word label, or an icon or symbol?",
                         schema=category_schema(CATEGORIES), max_tokens=100)

    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        category = answer.get("category")
        label, name = c.extra.get("label", ""), c.accessible_name or ""
        kw = {"label": label[:120], "name": name[:120]}
        if category == "icon_or_symbol":
            outcome, key, impact = "passed", "c253.apertus_icon", t("c253.impact_ok", ui)
        elif category == "word_label":
            outcome, key, impact = "failed", "c253.mismatch", t("c253.impact", ui, label=label[:80])
        else:
            outcome, key, impact = "cantTell", "c253.apertus_unsure", t("impact.review", ui)
        return self.finding(c, outcome=outcome, source="apertus",
                            confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
                            excerpt=self.model_excerpt(c, answer, outcome), explanation=t(key, ui, **kw),
                            user_impact=impact, reason=answer.get("reason"),
                            reason_code=f"apertus_{category}" if category in CATEGORIES else "apertus_unsure",
                            act_rule="2ee8b8" if outcome == "failed" else ...)


CHECK = LabelInName
