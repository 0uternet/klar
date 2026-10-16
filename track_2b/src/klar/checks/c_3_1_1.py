"""3.1.1 Language of Page, level A. ACT rules b5c3f8 (page has lang), bf051a (valid
language tag) and ucwvc8 (language subtag matches the default language).

The default human language is the language used most on the page, or the first one
if two are used equally (Understanding 3.1.1). Only the primary subtag of <html lang>
counts (case-insensitive); region and variant subtags are ignored. xml:lang has no
effect in an HTML document, so only `lang` is read.

Facts in code
  1. <html> has no lang, or an empty one                → failed (rule, b5c3f8; axe html-has-lang)
  2. lang is not a valid tag (BCP 47 syntax, two-letter primary subtag in ISO 639-1,
     and a three-letter primary subtag that merely repeats a language that has a
     two-letter code is not in the IANA registry)         → failed (rule, bf051a; axe html-lang-valid)
  3. the MAIN running text (<main>, else <body>; parts with their own lang, table cells,
     address and contact lines and lists of names left out: sentences only) has ≥ 20
     words and ≥ 80 % of them are in one language other than the declared one
                                                         → failed (heuristic, ucwvc8), reason_code
     `page_lang_mismatch`, fix lang="<detected>", content_lang = detected. This is the
     ONLY code-level mismatch. `main_language(page)` is the pure helper (no model, no
     network) that 3.1.2 imports to defer consistently. No code decision at all when the
     declared language is outside KLAR_DETECT_LANGS (Romansh: lingua has no model for
     it) or when the detector's top language is Latin (what it reports for Romansh).
  4. word count per language (lingua, see klar/langid.py) over the page title and every
     visible text block that inherits the page language (blocks with their own lang are
     language-of-parts, 3.1.2, and do not change the default):
       declared language ≥ 60 % of the words and the most used one → passed (heuristic)
       two languages within a 0.70–1.43 word ratio (BALANCE), the declared one among them
                                                         → cantTell (heuristic): "used most"
         (ACT counts words) and "first if used equally" (Understanding) disagree, and
         a model cannot settle a definitional dispute
  5. short (< 20 words) and every recognised block is in the declared language
                                                         → passed (heuristic, low confidence)
  6. short, mixed, a declared language the detector cannot verify, or a page whose other
     language is only names, addresses or lists     → Apertus

Asked to Apertus: the declared language, the title and a sample of the text, with the
detector's word shares as context. CATEGORICAL question "In which language is the page
text mainly written?" (names, terms and loanwords count as part of the surrounding
language), mapped in code:
      declared  → passed     other → failed (with the language code, guard-checked)
      balanced  → cantTell   unclear → cantTell
An "other" answer naming the declared language is a contradiction → cantTell.

Known limits: lingua is unreliable on very short pages (hence the model); a page whose
text is only images cannot be checked; Romansh and other languages outside
KLAR_DETECT_LANGS are never decided in code (→ Apertus); "running text" is recognised by
sentence punctuation or function words (DE/FR/IT/EN), other languages' lists of names
go to Apertus.
"""

from __future__ import annotations

import re
from collections import Counter

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema, set_attr, unified_diff
from klar.checks.c_2_4_5 import INLINE, NO_TEXT, Node, page_doc
from klar.config import Settings
from klar.checks.c_3_1_2 import address_like, contact_line, is_valid_lang, primary, running_text, sentence_like
from klar.i18n import lang_forms, register, t
from klar.langid import get_detector, word_count
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "3.1.1/v1"

MIN_WORDS = 20  # below: "short" → the model decides
DOMINANT = 0.60
BALANCE = 0.70  # second language ≥ 70 % of the first: "used equally" (top share ≤ 0.59 < DOMINANT)
MIN_BLOCK_WORDS = 4  # shorter blocks count only when the detector is confident
SHORT_MIN_CONF = 0.60
MAIN_MIN_WORDS = 20  # main text long enough to decide the page language on its own
MAIN_MIN_SHARE = 0.80  # "high confidence": ≥ 80 % of the main running-text words in one language
RUNNING_MIN_WORDS = 5  # shorter blocks are labels, names or menu items, not running text
ADDRESS_MAX_WORDS = 12  # an address or contact line is short
# The detector reports Latin for Romansh (no model for it): never a code decision.
NOT_DECIDABLE = frozenset({"la"})
ROMANSH_FOR_LATIN = ("rm",)  # the code Apertus may name for such text (guard: allowed language codes)
SAMPLE_CHARS = 600

CATEGORIES = ["declared", "other", "balanced", "unclear"]
CATEGORY_OUTCOME = {"declared": "passed", "other": "failed", "balanced": "cantTell", "unclear": "cantTell"}

register({
    "c311.missing": {
        "en": "The page does not declare its language (no lang attribute on the html element).",
        "de": "Die Seite gibt ihre Sprache nicht an (kein lang-Attribut am html-Element).",
        "fr": "La page n'indique pas sa langue (pas d'attribut lang sur l'élément html).",
        "it": "La pagina non dichiara la sua lingua (nessun attributo lang sull'elemento html).",
    },
    "c311.invalid": {
        "en": "lang=\"{value}\" is not a valid language code.",
        "de": "lang=\"{value}\" ist kein gültiger Sprachcode.",
        "fr": "lang=\"{value}\" n'est pas un code de langue valide.",
        "it": "lang=\"{value}\" non è un codice di lingua valido.",
    },
    "c311.mismatch": {
        "en": "The page declares lang=\"{value}\" ({declared}), but almost all of its text is {actual}.",
        "de": "Die Seite gibt lang=\"{value}\" ({declared}) an, doch fast der ganze Text ist auf {actual}.",
        "fr": "La page déclare lang=\"{value}\" ({declared}), mais presque tout le texte est en {actual}.",
        "it": "La pagina dichiara lang=\"{value}\" ({declared}), ma quasi tutto il testo è in {actual}.",
    },
    "c311.matches": {
        "en": "The declared language ({declared}) is the main language of the text.",
        "de": "Die angegebene Sprache ({declared}) ist die Hauptsprache des Textes.",
        "fr": "La langue déclarée ({declared}) est la langue principale du texte.",
        "it": "La lingua dichiarata ({declared}) è la lingua principale del testo.",
    },
    "c311.balanced": {
        "en": "The page uses {declared} and {other} in about equal amounts. Whether the declared language counts as the default depends on the definition used (most words or first used): a person must decide.",
        "de": "Die Seite verwendet zwei Sprachen etwa gleich viel ({declared} und {other}). Ob die angegebene Sprache als Standardsprache gilt, hängt von der verwendeten Definition ab (meiste Wörter oder zuerst verwendet): Eine Person muss entscheiden.",
        "fr": "La page utilise deux langues à parts à peu près égales ({declared} et {other}). Savoir si la langue déclarée compte comme langue par défaut dépend de la définition retenue (langue la plus présente ou première utilisée) : une personne doit trancher.",
        "it": "La pagina usa due lingue in misura simile ({declared} e {other}). Se la lingua dichiarata valga come predefinita dipende dalla definizione adottata (più parole o prima usata): una persona deve decidere.",
    },
    "c311.too_little": {
        "en": "The page has too little text to verify its declared language. A person must check.",
        "de": "Die Seite hat zu wenig Text, um die angegebene Sprache zu prüfen. Eine Person muss prüfen.",
        "fr": "La page a trop peu de texte pour vérifier sa langue déclarée. Une personne doit vérifier.",
        "it": "La pagina ha troppo poco testo per verificare la lingua dichiarata. Una persona deve verificare.",
    },
    "c311.apertus_declared": {
        "en": "Apertus judged that the text is mainly written in the declared language ({declared}).",
        "de": "Apertus beurteilt, dass der Text hauptsächlich in der angegebenen Sprache ({declared}) geschrieben ist.",
        "fr": "Apertus juge que le texte est principalement rédigé dans la langue déclarée ({declared}).",
        "it": "Apertus giudica che il testo sia scritto soprattutto nella lingua dichiarata ({declared}).",
    },
    "c311.apertus_other": {
        "en": "Apertus judged that the text is mainly written in {actual}, not in the declared {declared}.",
        "de": "Apertus beurteilt, dass der Text hauptsächlich auf {actual} geschrieben ist, nicht auf {declared} wie angegeben.",
        "fr": "Apertus juge que le texte est principalement en {actual}, et non en {declared} comme déclaré.",
        "it": "Apertus giudica che il testo sia soprattutto in {actual}, non in {declared} come dichiarato.",
    },
    "c311.apertus_unsure": {
        "en": "Apertus could not tell which language the page mainly uses. A person must check.",
        "de": "Apertus konnte nicht erkennen, welche Sprache die Seite hauptsächlich verwendet. Eine Person muss prüfen.",
        "fr": "Apertus n'a pas pu dire quelle langue la page utilise principalement. Une personne doit vérifier.",
        "it": "Apertus non ha potuto stabilire quale lingua usi soprattutto la pagina. Una persona deve verificare.",
    },
    "c311.impact": {
        "en": "Screen readers read the whole page with the wrong voice and pronunciation, which makes it hard to understand.",
        "de": "Screenreader lesen die ganze Seite mit falscher Stimme und Aussprache vor; dadurch ist die Seite schwer zu verstehen.",
        "fr": "Les lecteurs d'écran lisent toute la page avec une mauvaise voix et une mauvaise prononciation, ce qui la rend difficile à comprendre.",
        "it": "I lettori di schermo leggono tutta la pagina con la voce e la pronuncia sbagliate, rendendola difficile da capire.",
    },
    "c311.impact_ok": {
        "en": "Screen readers pick the right voice for this page.",
        "de": "Screenreader wählen für diese Seite die richtige Stimme.",
        "fr": "Les lecteurs d'écran choisissent la bonne voix pour cette page.",
        "it": "I lettori di schermo scelgono la voce giusta per questa pagina.",
    },
    "c311.fix_hint": {
        "en": "Set the page language to lang=\"{code}\" in your CMS or page template.",
        "de": "Setzen Sie die Seitensprache im CMS oder in der Seitenvorlage auf lang=\"{code}\".",
        "fr": "Définissez la langue de la page sur lang=\"{code}\" dans votre CMS ou le gabarit de page.",
        "it": "Impostate la lingua della pagina su lang=\"{code}\" nel CMS o nel modello di pagina.",
    },
    "c311.fix_hint_plain": {
        "en": "Set the page language (lang attribute of the html element) in your CMS or page template.",
        "de": "Setzen Sie die Seitensprache (lang-Attribut des html-Elements) im CMS oder in der Seitenvorlage.",
        "fr": "Définissez la langue de la page (attribut lang de l'élément html) dans votre CMS ou le gabarit de page.",
        "it": "Impostate la lingua della pagina (attributo lang dell'elemento html) nel CMS o nel modello di pagina.",
    },
})


def _redundant_three_letter() -> frozenset[str]:
    """ISO 639-3 codes of languages that have a two-letter code: IANA registers only
    the two-letter form, so e.g. a three-letter code for French is not a valid primary
    subtag (ACT bf051a). Computed from lingua's language table, not listed by hand."""
    try:
        from lingua import Language

        return frozenset(lang.iso_code_639_3.name.lower() for lang in Language.all())
    except Exception:
        return frozenset()


REDUNDANT_3 = _redundant_three_letter()


def valid_page_lang(value: str) -> bool:
    p = value.strip().lower().replace("_", "-").split("-")[0]
    return is_valid_lang(value) and p not in REDUNDANT_3


def _static_blocks(root: Node, root_lang: str) -> list[tuple[str, str]]:
    """(tag of the block, text) for each block of `root` (static DOM), leaving out parts
    that carry their own lang in another language (3.1.2 parts, which do not change the
    page default)."""
    out: list[tuple[str, str]] = []

    def other_lang(n: Node) -> bool:
        return "lang" in n.attrs and primary(n.attrs["lang"]) != root_lang

    def walk(n: Node) -> None:
        buf: list[str] = []
        for c in n.children:
            if isinstance(c, str):
                buf.append(c)
            elif c.tag in NO_TEXT or c.hidden() or other_lang(c):
                continue
            elif c.tag in INLINE:
                buf.append(" " + c.text(skip=other_lang) + " ")
            else:
                out.append((n.tag, " ".join("".join(buf).split())))
                buf = []
                walk(c)
        out.append((n.tag, " ".join("".join(buf).split())))

    walk(root)
    return [(tag, text) for tag, text in out if text]


def running_block(tag: str, text: str, lang: str) -> bool:
    """A block of running text: a sentence, not a table cell, an address or contact
    line, or a list of names (names of places and people belong to the surrounding
    language, PROTOCOL 3.1.1/T1)."""
    words = word_count(text)
    if tag in ("td", "th", "address") or words < RUNNING_MIN_WORDS:
        return False
    if all(contact_line(line) for line in text.split("\n")) or (words <= ADDRESS_MAX_WORDS and address_like(text)):
        return False  # a long paragraph with commas and dates is not an address line
    return sentence_like(text) or running_text(text, lang)


def main_language(page: CapturedPage, *, langs: tuple[str, ...] | None = None) -> tuple[str | None, float]:
    """(primary language code, share) of the page's MAIN running text, or (None, 0.0)
    when no code decision is possible.

    Pure: static DOM of the captured page + lingua (klar/langid.py), block by block; no
    model call, no network, no state. The main text is <main> / role=main (else <body>)
    without the parts that carry their own lang. Only blocks of running text count
    (sentences: no table cells, addresses, contact lines or lists of names). `share` is
    the fraction of those words in the top language; ≥ MAIN_MIN_SHARE is a confident
    detection. Abstains (None, 0.0) when the declared language is outside
    KLAR_DETECT_LANGS (e.g. Romansh: the detector has no model for it), when the top
    language is Latin (what the detector reports for Romansh), or below MAIN_MIN_WORDS
    words of running text. Shared with 3.1.2 (backend), which defers to 3.1.1 when the
    whole page is mislabelled."""
    doc = page_doc(page)
    langs = langs or Settings().detect_langs
    declared = primary(page.lang if page.lang is not None else doc.lang)
    if not declared or declared not in {primary(c) for c in langs}:
        return None, 0.0
    det = get_detector(langs)
    counts: Counter = Counter()
    for tag, text in _static_blocks(doc.main or doc.body, declared):
        d = det.detect(text)
        if d is None:
            continue
        lang = primary(d.lang)
        if running_block(tag, text, lang):
            counts[lang] += word_count(text)
    total = sum(counts.values())
    if total < MAIN_MIN_WORDS:
        return None, 0.0
    lang, n = counts.most_common(1)[0]
    if lang in NOT_DECIDABLE:
        return None, 0.0
    return lang, round(n / total, 3)


def lang_name(code: str, ui: str) -> str:
    f = lang_forms(code)
    return {"de": f["de_noun"], "fr": f["fr_noun"], "it": f["it_noun"]}.get(ui, f["en"])


class LanguageOfPage(BaseCheck):
    criterion = "3.1.1"
    prompt_version = PROMPT_VERSION
    max_candidates = 1

    # -- facts (code) --------------------------------------------------------------------
    def blocks(self, page: CapturedPage) -> list[str]:
        """Title + visible text blocks that inherit the page language."""
        declared = primary(page.lang) if page.lang else ""
        out = [page.title] if page.title else []
        if page.passages:
            for p in page.passages:
                if not declared or primary(p.get("lang")) == declared or not p.get("lang"):
                    out.append(p.get("text", ""))
        else:  # no extraction (tests, pasted fragments): static text blocks of the body
            doc = page_doc(page)
            out.extend(text for _, text in _static_blocks(doc.body, primary(page.lang if page.lang is not None
                                                                         else doc.lang)))
        return [" ".join(b.split()) for b in out if b and b.strip()]

    def word_shares(self, blocks: list[str]) -> Counter:
        """Words per detected language, block by block (a heading, a menu item and a
        paragraph are each detected on their own, so neighbouring blocks in different
        languages are never pooled). Short blocks the detector is unsure about count
        as "und" (unknown)."""
        det = get_detector(self.settings.detect_langs)
        counts: Counter = Counter()
        for b in blocks:
            n = word_count(b)
            if not n:
                continue
            d = det.detect(b)
            if d is None or (n < MIN_BLOCK_WORDS and d.confidence < SHORT_MIN_CONF):
                counts["und"] += n
            else:
                counts[primary(d.lang)] += n
        return counts

    def candidates(self, page: CapturedPage) -> list[Candidate]:
        doc = page_doc(page)
        html_el = doc.html_el
        m = re.match(r"\s*<html\b[^>]*>", page.html or "", re.IGNORECASE)
        if m:
            snippet = m.group(0).strip()
        elif html_el is not None:
            snippet = "<html" + "".join(f' {k}="{v}"' for k, v in html_el.attrs.items()) + ">"
        else:
            snippet = "<html>"
        value = page.lang
        if value is None and html_el is not None and "lang" in html_el.attrs:
            value = html_el.attrs["lang"]
        extra: dict = {"value": value or ""}
        if value is None or not value.strip():
            extra["kind"] = "missing"
            return [self.candidate(page, selector="html", html=snippet, lang=None, key="#lang", **extra)]
        if not valid_page_lang(value):
            extra["kind"] = "invalid"
            return [self.candidate(page, selector="html", html=snippet, lang=value, key="#lang", **extra)]
        declared = primary(value)
        blocks = self.blocks(page)
        counts = self.word_shares(blocks)
        unknown = counts.pop("und", 0)
        total = sum(counts.values())  # words in a recognised language
        ranked = counts.most_common()
        top, top_n = ranked[0] if ranked else ("und", 0)
        second, second_n = ranked[1] if len(ranked) > 1 else ("", 0)
        share = counts.get(declared, 0) / total if total else 0.0
        extra.update(declared=declared, total=total, unknown=unknown,
                     shares={k: round(v / total, 3) for k, v in ranked} if total else {},
                     langs=sorted({declared, *counts.keys(), *(ROMANSH_FOR_LATIN if "la" in counts else ())}),
                     detected=top if top != "und" else declared)
        supported = {primary(code) for code in self.settings.detect_langs}
        main_lang, main_share = main_language(page, langs=self.settings.detect_langs)
        extra.update(main_lang=main_lang, main_share=main_share)
        if main_lang and main_share >= MAIN_MIN_SHARE and main_lang != declared:
            # The main text is clearly in another language: one page-level failure (3.1.2
            # defers to this finding and asks no per-span questions).
            extra["kind"] = "mismatch"
            extra["detected"] = main_lang
            extra["langs"] = sorted({declared, main_lang, *counts.keys()})
        elif total + unknown < 3:
            extra["kind"] = "too_little"
        elif declared not in supported or top in NOT_DECIDABLE:
            extra["kind"] = "ask"  # the detector cannot verify this language (e.g. Romansh): no code decision
        elif total >= MIN_WORDS and top == declared and share >= DOMINANT:
            extra["kind"] = "matches"
        elif total < MIN_WORDS and share == 1.0 and total >= unknown:
            extra["kind"] = "matches_short"  # short, but every recognised block is the declared language
        elif total >= MIN_WORDS and second and declared in (top, second) and second_n / top_n >= BALANCE:
            extra["kind"] = "balanced"
            extra["other"] = second if top == declared else top
        else:
            extra["kind"] = "ask"
        sample = self.sample(blocks)
        context = {"declared_language": f'lang="{value}"'}
        if total:
            context["detector_word_shares"] = ", ".join(f"{k} {round(100 * v / total)} %" for k, v in ranked[:3])
        return [self.candidate(page, selector="html", html=snippet, text=sample, lang=value, context=context,
                               key="#lang", **extra)]

    @staticmethod
    def sample(blocks: list[str]) -> str:
        out, n = [], 0
        for b in blocks:
            if n + len(b) > SAMPLE_CHARS:
                out.append(b[: max(0, SAMPLE_CHARS - n)])
                break
            out.append(b)
            n += len(b) + 3
        return " / ".join(x for x in out if x)

    # -- decisions (code) -------------------------------------------------------------------
    def decide(self, c: Candidate) -> Finding | None:
        ui = self.ui_lang
        kind = c.extra.get("kind")
        value = c.extra.get("value", "")
        if kind == "missing":
            f = self.finding(c, outcome="failed", source="rule", confidence="high", act_rule="b5c3f8",
                             excerpt=c.html, explanation=t("c311.missing", ui), user_impact=t("c311.impact", ui),
                             fix_hint=t("c311.fix_hint_plain", ui), content_lang=None)
            return f.model_copy(update={"axe_rule": "html-has-lang"})
        if kind == "invalid":
            f = self.finding(c, outcome="failed", source="rule", confidence="high", act_rule="bf051a",
                             excerpt=f'lang="{value}"' if f'lang="{value}"' in c.html else c.html,
                             explanation=t("c311.invalid", ui, value=value), user_impact=t("c311.impact", ui),
                             fix_hint=t("c311.fix_hint_plain", ui), content_lang=None)
            return f.model_copy(update={"axe_rule": "html-lang-valid"})
        declared = c.extra.get("declared", "")
        shares = c.extra.get("shares") or {}
        if kind == "too_little":
            return self.note(c, "c311.too_little", source="heuristic")
        if kind in ("matches", "matches_short"):
            return self.finding(c, outcome="passed", source="heuristic", reason_code=kind,
                                confidence="low" if kind == "matches_short" else
                                "high" if shares.get(declared, 0) >= 0.8 else "medium",
                                excerpt=c.html, act_rule="ucwvc8",
                                explanation=t("c311.matches", ui, declared=lang_name(declared, ui),
                                              share=round(100 * shares.get(declared, 0))),
                                user_impact=t("c311.impact_ok", ui))
        if kind == "mismatch":
            actual = c.extra.get("detected", "")
            return self.finding(c, outcome="failed", source="heuristic", confidence="high", act_rule="ucwvc8",
                                excerpt=c.html, content_lang=actual, reason_code="page_lang_mismatch",
                                explanation=t("c311.mismatch", ui, value=value, declared=lang_name(declared, ui),
                                              actual=lang_name(actual, ui), share=round(100 * shares.get(actual, 0))),
                                user_impact=t("c311.impact", ui),
                                fix_diff=unified_diff(c.html, set_attr(c.html, "lang", actual), "html"),
                                fix_hint=t("c311.fix_hint", ui, code=actual))
        if kind == "balanced":
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="low", excerpt=c.html,
                                act_rule="ucwvc8",
                                explanation=t("c311.balanced", ui, declared=lang_name(declared, ui),
                                              other=lang_name(c.extra.get("other", ""), ui)),
                                user_impact=t("impact.review", ui))
        return None  # short or mixed → Apertus

    # -- the closed (categorical) question ----------------------------------------------------
    SYSTEM = (
        "You check WCAG 2.1 success criterion 3.1.1 Language of Page. The page declares a default language. "
        "Decide in which language the page text is mainly written. Names of people, places, organisations, "
        "products and events, technical terms and loanwords count as part of the language around them. Text "
        "that is only a list of links to other language versions does not count.\n"
        "- declared: mainly the declared language\n"
        "- other: mainly another language\n"
        "- balanced: two languages in about equal amounts\n"
        "- unclear: too little text, or unsure\n"
        "language: ISO 639-1 code of the main language. quote: a short span of the text in that language, "
        "copied exactly."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        return self.task(
            system=self.system_prompt(self.SYSTEM, c),
            element={"text": c.text},
            context=c.context,
            question="In which language is the page text mainly written?",
            schema=category_schema(CATEGORIES, extra={"language": {"type": "string", "maxLength": 12}}),
            max_tokens=120,
        )

    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        category = answer.get("category", "unclear")
        outcome = CATEGORY_OUTCOME.get(category, "cantTell")
        declared = c.extra.get("declared", "")
        lang = primary(answer.get("language")) or ""
        if outcome == "failed" and (not lang or lang == declared):
            outcome = "cantTell"  # "another language" that is the declared one, or none: contradiction
        key = {"passed": "c311.apertus_declared", "failed": "c311.apertus_other"}.get(outcome, "c311.apertus_unsure")
        code = f"apertus_{category}" if CATEGORY_OUTCOME.get(category) == outcome else "apertus_contradiction"
        fix: dict = {}
        if outcome == "failed":
            fix = {"fix_diff": unified_diff(c.html, set_attr(c.html, "lang", lang), "html"),
                   "fix_hint": t("c311.fix_hint", ui, code=lang)}
        impact = {"failed": t("c311.impact", ui), "passed": t("c311.impact_ok", ui)}.get(outcome, t("impact.review", ui))
        quote = (answer.get("quote") or "").strip()
        return self.finding(c, outcome=outcome, source="apertus", act_rule="ucwvc8",
                            confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
                            excerpt=quote or (c.text[:120] if outcome != "failed" else ""),
                            explanation=t(key, ui, declared=lang_name(declared, ui), actual=lang_name(lang, ui)),
                            user_impact=impact, reason=answer.get("reason"), reason_code=code,
                            content_lang=lang or declared, **fix)


CHECK = LanguageOfPage
