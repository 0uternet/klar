"""2.4.6 Headings and Labels, level AA. ACT rules b49b2e (heading is descriptive) and
cc0f0a (form field label is descriptive).

Understanding 2.4.6: the criterion does not require headings or labels, and they may be
short ("a word, or even a single character, may suffice"). What matters is whether the
text describes the topic of its section, or the purpose of its field.

Facts in code
  * Candidates: every visible heading (h1–h6, role=heading) with non-empty text and a
    non-empty section, and every <label> bound to a visible field. Empty headings and
    unlabelled fields are axe-core's (empty-heading, label) and not repeated here.
  * Section of a heading (static DOM, capture of the rendered page): the text that follows
    it in document order until the next heading of the same or a higher level
    (sub-headings included), first ~250 characters.
  * Deterministic pass (no model), only when unambiguous:
      heading  every content word of the heading (1–4 words of ≥ 4 letters, compared on a
               5-letter stem) occurs in the first two sentences of its section, and the
               heading has no number and no generic or placeholder word (GENERIC_HEADING:
               a generic heading that the text repeats is exactly PROTOCOL 2.4.6/F1)
                                                                  → passed (heuristic, medium)
      label    an e-mail field whose label contains "mail", or a telephone field whose
               label names a telephone                            → passed (heuristic, medium)
  * No candidate at all (no headings, no labels)                   → no finding (inapplicable)

Asked to Apertus (one question per remaining heading or label; at most 10 headings, the
shortest first, and 8 labels per page: CPU inference is slow)
  Heading + the first lines of its section (+ up to 4 neighbouring headings of the same
  level, to show whether topic headings are used). CATEGORICAL, mapped in code
  (data/testset/PROTOCOL.md §2.4.6):
      describes         → passed
      generic           → cantTell  (a broad category word over content that partly fits,
                                     or genuinely miscellaneous content: judgement call)
      placeholder       → failed    (numbering, editor placeholder, content-free word)
      different_topic   → failed
      unsure            → cantTell
  Label + field facts (type, placeholder, autocomplete, fieldset legend, the form's
  heading, the other labels of the form). CATEGORICAL:
      describes         → passed    (short or conventional abbreviations count)
      vague             → cantTell  (vague, but the purpose can be inferred from the form)
      non_descriptive   → failed
      wrong             → failed    (names other data than the field asks for)
      unsure            → cantTell
  The quote must be the heading or label text, verbatim (evidence guard).

Known limits: the section is judged from its first lines; visually styled pseudo-headings
without heading markup are 1.3.1, not here; labels made with aria-label/aria-labelledby
only are not judged.
"""

from __future__ import annotations

import re
import unicodedata

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema
from klar.checks.c_2_4_5 import CONTROLS, NO_TEXT, Document, Node, norm_text, page_doc
from klar.i18n import register, t
from klar.langid import WORD_RE
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "2.4.6/v1"
SECTION_CHARS = 250
MAX_HEADINGS = 10  # model questions are expensive on CPU: short headings first (see heading_candidates)
MAX_LABELS = 8

HEADING_CATEGORIES = ["describes", "generic", "placeholder", "different_topic", "unsure"]
LABEL_CATEGORIES = ["describes", "vague", "non_descriptive", "wrong", "unsure"]
CATEGORY_OUTCOME = {"describes": "passed", "generic": "cantTell", "placeholder": "failed",
                    "different_topic": "failed", "vague": "cantTell", "non_descriptive": "failed",
                    "wrong": "failed", "unsure": "cantTell"}

_HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_SENTENCE = re.compile(r"(?<=[.!?:])\s")
_TEL = re.compile(r"tel|phon|fon", re.IGNORECASE)
# Word stems of generic, placeholder or category headings (DE · FR · IT · EN; PROTOCOL
# 2.4.6 F1/C1): a heading built on one of them is never passed in code, even when its
# words reappear in the text below (the text may repeat a generic word).
GENERIC_HEADING = re.compile(
    r"\b(?:allgemein|information|informazion|weitere|divers|verschieden|sonstig|abschnitt|titel|inhalt|testo\b|"
    r"überschrift|text|rubrik|rubrique|übersicht|aktuell|neuigkeit|general|général|autre|altr[eoia]|"
    r"sezion|section|contenu|contenut|content|bloc|actualit|nouvel|notizi|attualit|novit|vari[ae]\b|misc|"
    r"other|more\b|heading|detail|news\b|overview|various|additional|platzhalter|placeholder|"
    r"untitled|ohne\s+titel|sans\s+titre|senza\s+titolo)", re.IGNORECASE)
_DIGIT = re.compile(r"\d")

register({
    "c246.heading_words": {
        "en": "The heading “{text}” repeats the words of its section's first sentence.",
        "de": "Die Überschrift «{text}» nimmt die Wörter des ersten Satzes ihres Abschnitts auf.",
        "fr": "Le titre « {text} » reprend les mots de la première phrase de sa section.",
        "it": "Il titolo «{text}» riprende le parole della prima frase della sua sezione.",
    },
    "c246.label_type": {
        "en": "The label “{text}” names what the {type} field asks for.",
        "de": "Die Beschriftung «{text}» nennt, was das Feld ({type}) verlangt.",
        "fr": "L'étiquette « {text} » nomme ce que le champ ({type}) demande.",
        "it": "L'etichetta «{text}» indica ciò che il campo ({type}) richiede.",
    },
    "c246.apertus_describes": {
        "en": "Apertus judged that “{text}” describes its {what}.",
        "de": "Apertus beurteilt, dass «{text}» {what_de} beschreibt.",
        "fr": "Apertus juge que « {text} » décrit {what_fr}.",
        "it": "Apertus giudica che «{text}» descriva {what_it}.",
    },
    "c246.apertus_generic": {
        "en": "“{text}” is a broad category over content that only partly fits it. Experts disagree whether that is descriptive: a person must decide.",
        "de": "«{text}» ist ein Oberbegriff über einem Inhalt, der nur teilweise dazu passt. Ob das beschreibend ist, ist umstritten: Eine Person muss entscheiden.",
        "fr": "« {text} » est une catégorie générale pour un contenu qui n'y correspond qu'en partie. Les avis divergent : une personne doit trancher.",
        "it": "«{text}» è una categoria generica per un contenuto che vi corrisponde solo in parte. Gli esperti non concordano: una persona deve decidere.",
    },
    "c246.apertus_vague": {
        "en": "The label “{text}” is vague; the purpose of the field can only be guessed from the form. A person must decide.",
        "de": "Die Beschriftung «{text}» ist vage; den Zweck des Feldes erahnt man nur aus dem Formular. Eine Person muss entscheiden.",
        "fr": "L'étiquette « {text} » est vague ; le but du champ ne se devine qu'à partir du formulaire. Une personne doit trancher.",
        "it": "L'etichetta «{text}» è vaga; lo scopo del campo si intuisce solo dal modulo. Una persona deve decidere.",
    },
    "c246.apertus_placeholder": {
        "en": "Apertus judged that the heading “{text}” is a placeholder or a content-free word that does not name the topic of its section.",
        "de": "Apertus beurteilt die Überschrift «{text}» als Platzhalter oder inhaltsleeres Wort, das das Thema des Abschnitts nicht nennt.",
        "fr": "Apertus juge que le titre « {text} » est un texte provisoire ou un mot vide qui ne nomme pas le sujet de sa section.",
        "it": "Apertus giudica che il titolo «{text}» sia un segnaposto o una parola vuota che non indica l'argomento della sezione.",
    },
    "c246.apertus_different_topic": {
        "en": "Apertus judged that the heading “{text}” names another topic than its section contains.",
        "de": "Apertus beurteilt, dass die Überschrift «{text}» ein anderes Thema nennt, als der Abschnitt enthält.",
        "fr": "Apertus juge que le titre « {text} » nomme un autre sujet que le contenu de sa section.",
        "it": "Apertus giudica che il titolo «{text}» indichi un argomento diverso da quello della sezione.",
    },
    "c246.apertus_non_descriptive": {
        "en": "Apertus judged that the label “{text}” does not say what to enter.",
        "de": "Apertus beurteilt, dass die Beschriftung «{text}» nicht sagt, was einzugeben ist.",
        "fr": "Apertus juge que l'étiquette « {text} » n'indique pas ce qu'il faut saisir.",
        "it": "Apertus giudica che l'etichetta «{text}» non dica cosa inserire.",
    },
    "c246.apertus_wrong": {
        "en": "Apertus judged that the label “{text}” names other data than the field asks for.",
        "de": "Apertus beurteilt, dass die Beschriftung «{text}» andere Angaben nennt, als das Feld verlangt.",
        "fr": "Apertus juge que l'étiquette « {text} » nomme d'autres données que celles demandées par le champ.",
        "it": "Apertus giudica che l'etichetta «{text}» indichi dati diversi da quelli richiesti dal campo.",
    },
    "c246.apertus_unsure": {
        "en": "Apertus could not decide whether “{text}” is descriptive. A person must check.",
        "de": "Apertus konnte nicht entscheiden, ob «{text}» beschreibend ist. Eine Person muss prüfen.",
        "fr": "Apertus n'a pas pu décider si « {text} » est descriptif. Une personne doit vérifier.",
        "it": "Apertus non ha potuto decidere se «{text}» sia descrittivo. Una persona deve verificare.",
    },
    "c246.impact_heading": {
        "en": "Screen-reader users who jump from heading to heading cannot tell what this section is about.",
        "de": "Screenreader-Nutzende, die von Überschrift zu Überschrift springen, erkennen nicht, worum es in diesem Abschnitt geht.",
        "fr": "Les utilisateurs de lecteurs d'écran qui naviguent de titre en titre ne savent pas de quoi traite cette section.",
        "it": "Chi usa un lettore di schermo e salta da un titolo all'altro non capisce di cosa tratti questa sezione.",
    },
    "c246.impact_label": {
        "en": "People do not know what to enter in this field, especially when they hear the label without seeing the form.",
        "de": "Man weiss nicht, was in dieses Feld gehört, besonders wenn man die Beschriftung hört, ohne das Formular zu sehen.",
        "fr": "On ne sait pas quoi saisir dans ce champ, surtout quand on entend l'étiquette sans voir le formulaire.",
        "it": "Non si sa cosa inserire in questo campo, soprattutto quando si sente l'etichetta senza vedere il modulo.",
    },
    "c246.impact_ok": {
        "en": "People can tell from the text alone what follows or what to enter.",
        "de": "Man erkennt schon am Text, was folgt oder was einzugeben ist.",
        "fr": "Le texte seul suffit pour savoir ce qui suit ou ce qu'il faut saisir.",
        "it": "Il solo testo basta per capire cosa segue o cosa inserire.",
    },
    "c246.fix_heading": {
        "en": "In your CMS, change the heading so that it names the topic of its section.",
        "de": "Ändern Sie im CMS die Überschrift so, dass sie das Thema ihres Abschnitts nennt.",
        "fr": "Dans votre CMS, modifiez le titre pour qu'il nomme le sujet de sa section.",
        "it": "Nel CMS, modificate il titolo in modo che indichi l'argomento della sua sezione.",
    },
    "c246.fix_label": {
        "en": "In your CMS or form builder, change the label so that it says what to enter.",
        "de": "Ändern Sie im CMS oder Formular-Editor die Beschriftung so, dass sie sagt, was einzugeben ist.",
        "fr": "Dans votre CMS ou éditeur de formulaires, modifiez l'étiquette pour qu'elle dise quoi saisir.",
        "it": "Nel CMS o nell'editor di moduli, modificate l'etichetta in modo che dica cosa inserire.",
    },
    "c246.what.heading": {"en": "section", "de": "ihren Abschnitt", "fr": "sa section", "it": "la sua sezione"},
    "c246.what.label": {"en": "field", "de": "ihr Feld", "fr": "son champ", "it": "il suo campo"},
})


def _stem_words(s: str) -> list[str]:
    return [w.lower()[:5] for w in WORD_RE.findall(unicodedata.normalize("NFKC", s or "")) if len(w) >= 4]


def first_sentences(text: str, n: int = 2) -> str:
    return " ".join(_SENTENCE.split(text, maxsplit=n)[:n])[:250]


def heading_level(n: Node) -> int:
    if n.attrs.get("aria-level", "").isdigit():
        return int(n.attrs["aria-level"])
    return int(n.tag[1]) if n.tag in _HEADING_TAGS else 2


def is_heading(n: Node) -> bool:
    return n.tag in _HEADING_TAGS or n.role == "heading"


def sections(doc: Document) -> dict[int, str]:
    """id(heading node) → text of its section (until the next heading of level ≤ its own)."""
    events: list[tuple[str, object]] = []

    def walk(n: Node) -> None:
        for c in n.children:
            if isinstance(c, str):
                if c.strip():
                    events.append(("text", c))
                continue
            if c.tag in NO_TEXT or c.hidden() or c.attrs.get("aria-hidden", "").lower() == "true":
                continue
            if is_heading(c):
                events.append(("heading", c))
                events.append(("text", " " + c.text() + " "))  # a sub-heading is part of the parent section
                continue
            block = c.tag not in ("a", "span", "strong", "em", "b", "i", "abbr", "code", "small", "label")
            if block:
                events.append(("text", " "))
            walk(c)
            if block:
                events.append(("text", " "))

    walk(doc.body)
    out: dict[int, str] = {}
    for i, (kind, h) in enumerate(events):
        if kind != "heading":
            continue
        level = heading_level(h)  # type: ignore[arg-type]
        parts: list[str] = []
        size = 0
        for kind2, v in events[i + 2:]:
            if kind2 == "heading" and heading_level(v) <= level:  # type: ignore[arg-type]
                break
            if kind2 == "text":
                parts.append(v)  # type: ignore[arg-type]
                size += len(v)  # type: ignore[arg-type]
                if size > SECTION_CHARS * 2:
                    break
        out[id(h)] = norm_text("".join(parts))[:SECTION_CHARS]
    return out


class HeadingsAndLabels(BaseCheck):
    criterion = "2.4.6"
    prompt_version = PROMPT_VERSION
    max_candidates = 200  # the caps apply to model questions, not to code decisions

    def candidates(self, page: CapturedPage) -> list[Candidate]:
        doc = page_doc(page)
        out = self.heading_candidates(page, doc) + self.label_candidates(page, doc)
        return out

    def heading_candidates(self, page: CapturedPage, doc: Document) -> list[Candidate]:
        visible = {h["selector"] for h in page.headings} if page.headings else None
        texts = sections(doc)
        nodes = [n for n in doc.body.iter() if is_heading(n)]
        out: list[Candidate] = []
        for n in nodes:
            text = n.text()
            sel = n.css_path()
            if not text or (visible is not None and sel not in visible):
                continue
            section = texts.get(id(n), "")
            if not section:
                continue  # nothing to describe (a heading at the end, an empty block)
            level = heading_level(n)
            siblings = [s.text() for s in nodes if s is not n and heading_level(s) == level and s.text()][:4]
            context = {"section_start": section}
            if siblings:
                context["other_headings_same_level"] = " | ".join(siblings)
            words = _stem_words(text)
            first = {w for w in _stem_words(first_sentences(section))}
            generic = bool(GENERIC_HEADING.search(text) or _DIGIT.search(text))  # → always the model
            # A one-word heading must be the section's recurring subject (≥ 2 mentions), not a
            # word the text merely mentions once (a fee list may mention opening hours).
            repeated = len(words) > 1 or (len(words) == 1 and _stem_words(section).count(words[0]) >= 2)
            kind = "heading_words" if (words and len(words) <= 4 and not generic and repeated
                                       and all(w in first for w in words)) else "heading"
            out.append(self.candidate(page, selector=sel, html=n.outer(400), text=text, lang=self._lang(n, page),
                                      context=context, kind=kind, target="heading", level=level))
        # Code-decided headings cost nothing; of the others, ask about the shortest first (placeholders,
        # numbering and generic words are short), at most MAX_HEADINGS, then restore document order.
        decided = [c for c in out if c.extra["kind"] != "heading"]
        asked = sorted((c for c in out if c.extra["kind"] == "heading"), key=lambda c: len(c.text.split()))[:MAX_HEADINGS]
        keep = {id(c) for c in decided + asked}
        return [c for c in out if id(c) in keep]

    def label_candidates(self, page: CapturedPage, doc: Document) -> list[Candidate]:
        visible_fields = {f["selector"] for f in page.fields} if page.fields else None
        out: list[Candidate] = []
        for lb in doc.find_all(lambda n: n.tag == "label"):
            field = doc.control_of(lb)
            if field is None or field.hidden():
                continue
            if visible_fields is not None and field.css_path() not in visible_fields:
                continue
            text = lb.text(skip=lambda n: n.tag in CONTROLS)
            if not text:
                continue
            ftype = (field.attrs.get("type") or field.tag).lower() if field.tag == "input" else field.tag
            form = field.closest(lambda a: a.tag in ("form", "fieldset")) or doc.body
            legend = field.closest(lambda a: a.tag == "fieldset")
            legend_el = legend.find(lambda x: x.tag == "legend") if legend is not None else None
            others = [o.text(skip=lambda n: n.tag in CONTROLS) for o in form.find_all(lambda x: x.tag == "label")
                      if o is not lb][:6]
            context = {"field_type": ftype}
            for attr in ("placeholder", "autocomplete", "inputmode"):
                if field.attrs.get(attr):
                    context[attr] = field.attrs[attr]
            if field.tag == "select":
                opts = [o.text() for o in field.find_all(lambda x: x.tag == "option")][:5]
                if opts:
                    context["options"] = " | ".join(o for o in opts if o)
            if legend_el is not None and legend_el.text():
                context["fieldset_legend"] = legend_el.text()
            if others:
                context["other_labels_in_form"] = " | ".join(o for o in others if o)
            kind = "label"
            if (ftype == "email" and "mail" in text.lower()) or (ftype == "tel" and _TEL.search(text)):
                kind = "label_type"
            out.append(self.candidate(page, selector=lb.css_path(), html=lb.outer(300) + field.outer(300), text=text,
                                      lang=self._lang(lb, page), context=context, kind=kind, target="label",
                                      field_type=ftype))
            if len([c for c in out if c.extra["kind"] == "label"]) >= MAX_LABELS:
                break
        return out

    @staticmethod
    def _lang(n: Node, page: CapturedPage) -> str | None:
        holder = n.closest(lambda a: "lang" in a.attrs)
        return holder.attrs["lang"] if holder is not None else page.lang

    # -- decisions (code) -------------------------------------------------------------------
    def decide(self, c: Candidate) -> Finding | None:
        ui = self.ui_lang
        kind = c.extra.get("kind")
        if kind == "heading_words":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", act_rule="b49b2e",
                                excerpt=c.text, explanation=t("c246.heading_words", ui, text=c.text),
                                user_impact=t("c246.impact_ok", ui))
        if kind == "label_type":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", act_rule="cc0f0a",
                                excerpt=c.text, explanation=t("c246.label_type", ui, text=c.text,
                                                              type=c.extra.get("field_type", "")),
                                user_impact=t("c246.impact_ok", ui))
        return None

    # -- the closed (categorical) questions ---------------------------------------------------
    SYSTEM_HEADING = (
        "You check WCAG 2.1 success criterion 2.4.6 Headings and Labels for ONE heading. A heading is descriptive "
        "when it names the topic or purpose of the section it introduces. It may be very short: one word, or a "
        "single letter in an index, can be enough.\n"
        "- describes: the heading names the topic or purpose of its section\n"
        "- generic: a broad category word over content that only partly fits it, or over genuinely mixed content\n"
        "- placeholder: a number, an editor placeholder or a content-free word over specific content\n"
        "- different_topic: the heading names a different topic than the section contains\n"
        "- unsure: none of these\n"
        "quote: the heading text, copied exactly."
    )
    SYSTEM_LABEL = (
        "You check WCAG 2.1 success criterion 2.4.6 Headings and Labels for ONE form field label. A label is "
        "descriptive when it says what to enter in the field. Short labels and abbreviations that are usual in "
        "this kind of form are enough.\n"
        "- describes: the label says what to enter\n"
        "- vague: the label is vague, but the purpose can be inferred from the rest of the form\n"
        "- non_descriptive: the label does not say what to enter (a number, a placeholder or a content-free word)\n"
        "- wrong: the label names other data than the field asks for\n"
        "- unsure: none of these\n"
        "quote: the label text, copied exactly."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        if c.extra.get("target") == "label":
            return self.task(system=self.system_prompt(self.SYSTEM_LABEL, c), element={"label": c.text},
                             context=c.context, question="Does this label say what to enter in its field?",
                             schema=category_schema(LABEL_CATEGORIES), max_tokens=120)
        return self.task(system=self.system_prompt(self.SYSTEM_HEADING, c), element={"heading": c.text},
                         context=c.context, question="Does this heading describe the topic of its section?",
                         schema=category_schema(HEADING_CATEGORIES), max_tokens=120)

    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        is_label = c.extra.get("target") == "label"
        allowed = LABEL_CATEGORIES if is_label else HEADING_CATEGORIES
        category = answer.get("category", "unsure")
        if category not in allowed:
            category = "unsure"
        outcome = CATEGORY_OUTCOME[category]
        key = f"c246.apertus_{category}"
        what = "label" if is_label else "heading"
        whats = {f"what_{lg}": t(f"c246.what.{what}", lg) for lg in ("de", "fr", "it")}
        if outcome == "failed":
            impact = t("c246.impact_label" if is_label else "c246.impact_heading", ui)
        elif outcome == "passed":
            impact = t("c246.impact_ok", ui)
        else:
            impact = t("impact.review", ui)
        quote = (answer.get("quote") or "").strip()
        return self.finding(c, outcome=outcome, source="apertus", act_rule="cc0f0a" if is_label else "b49b2e",
                            confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
                            excerpt=quote or (c.text if outcome != "failed" else ""),
                            explanation=t(key, ui, text=c.text, what=t(f"c246.what.{what}", "en"), **whats),
                            user_impact=impact, reason=answer.get("reason"), reason_code=f"apertus_{category}",
                            fix_hint=t("c246.fix_label" if is_label else "c246.fix_heading", ui)
                            if outcome == "failed" else None)


CHECK = HeadingsAndLabels
