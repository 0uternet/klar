"""3.1.2 Language of Parts, level AA. ACT rules off6ek (language subtag matches
the language) and de46e4 (valid language tag).

WCAG Understanding 3.1.2 exempts proper names, technical terms, words of
indeterminate language and words or phrases that have become part of the
vernacular of the surrounding text (loanwords, helvetisms, Latin expressions).
Swiss public sites add names of institutions in another national language and
addresses. A language detector cannot tell those apart from a real
foreign-language passage; Apertus can, if asked the right question.
(No concrete examples here or in the prompt: tests/test_leakage.py keeps every
string of this module out of the test set.)

Cascade
  1. lang attribute with an invalid value ("francais", "de_CH")   → failed (rule, de46e4)
  2. language-switcher entry written in its own language
     ("Français" in a German page) without matching lang            → failed (heuristic); with it → passed
  3. tagged passage whose text matches its lang                   → passed (heuristic, off6ek)
  4. tagged passage whose full sentence is clearly another language → failed (heuristic, off6ek)
  5. untagged passage whose WHOLE text is running text in another language → failed
     (heuristic, no LLM). All of these must hold (see `fails_in_code`):
       - the whole passage is foreign: never a sub-span of a mixed passage;
       - full sentence: ≥ 6 words and sentence-final punctuation;
       - detector confidence for the declared language ≤ 0.10;
       - running text: at least one finite-verb / pronoun / negation marker of the
         detected language (`RUNNING_TEXT_MARKERS`): titles and names have none;
       - not quoted: quotation marks or q/cite/i/em/dfn cover < 50 % of the text
         (titles of works, citations → judgement call C3);
       - not address-like: no postcode + place, street + number, phone number or
         comma-separated contact line (institutions and addresses → exception T1).
     (real-model finding: the 8B model wrongly exempted a full French paragraph,
      so clear running text never goes to the model.)
  6. everything else in another language (spans, titles, quotes, addresses, names)
                                                                   → Apertus, CATEGORICAL question:
     proper_name | institution | place_or_address | technical_term | loanword_in_vernacular |
     greeting_or_formula | title_of_work | foreign_language_passage | other
     mapped in code (data/testset/PROTOCOL.md §3.1.2): foreign_language_passage → failed,
     exceptions → passed, greeting/title (judgement calls) and other → cantTell.

Passages whose declared language the detector cannot verify (e.g. Romansh) are skipped.
"""

from __future__ import annotations

import re

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema, norm_ws, set_attr, unified_diff, wrap_text
from klar.i18n import lang_kwargs, t, voice_sentence
from klar.langid import (ENDONYMS, ISO_639_1, WORD_RE, Detection, LanguageDetector, endonym,  # noqa: F401
                         get_detector, word_count)
from klar.models import Candidate, Finding, LLMTask

# v2: complete quote. v3: greeting_or_formula, title_of_work.
# v4: page data block, generic category descriptions (no examples), English reason.
PROMPT_VERSION = "3.1.2/v4"

# Thresholds (tune on data/testset; they are not part of the cache key because
# they only decide WHICH candidates reach the model, not WHAT it is asked).
# lingua confidences are relative (they sum to 1 over the loaded languages). Measured
# on DE/FR/IT/EN samples: a foreign full sentence gives the declared language ≤ 0.08,
# even when a proper name drags the top language down to ~0.55.
SENTENCE_MIN_WORDS = 6  # "full sentence": ≥ 6 words AND sentence-final punctuation
DECLARED_MAX_CONF = 0.10  # deterministic fail: the text is clearly NOT the declared language
WHOLE_MIN_CONF = 0.60  # whole-passage detection that differs from the declared language
SPAN_MIN_WORDS = 2  # shorter spans are ignored (single words are usually exceptions)
SPAN_MIN_CHARS = 8
SPAN_MIN_CONF = 0.35
SPAN_DECLARED_MAX_CONF = 0.30
TAGGED_OK_MIN_CONF = 0.50

BCP47 = re.compile(
    r"^[a-z]{2,3}(?:-[a-z]{3}){0,3}(?:-[a-z]{4})?(?:-(?:[a-z]{2}|\d{3}))?(?:-(?:[a-z\d]{5,8}|\d[a-z\d]{3}))*"
    r"(?:-[a-wyz\d](?:-[a-z\d]{2,8})+)*(?:-x(?:-[a-z\d]{1,8})+)?$",
    re.IGNORECASE,
)
# Comparison classes: Swiss German counts as German, Serbo-Croatian variants as one.
EQUIVALENT = {"gsw": "de", "sh": "hr", "bs": "hr", "sr": "hr", "nb": "no", "nn": "no"}

CATEGORIES = ["proper_name", "institution", "place_or_address", "technical_term", "loanword_in_vernacular",
              "greeting_or_formula", "title_of_work", "foreign_language_passage", "other"]
# Mapping fixed by data/testset/PROTOCOL.md §3.1.2 (T1–T4 passed, C2/C3 cantTell, F1 failed).
CATEGORY_OUTCOME = {
    "foreign_language_passage": "failed",
    "proper_name": "passed",
    "institution": "passed",
    "place_or_address": "passed",
    "technical_term": "passed",
    "loanword_in_vernacular": "passed",
    "greeting_or_formula": "cantTell",  # a short formula from another national language: vernacular or not? (C2)
    "title_of_work": "cantTell",  # a title made of ordinary foreign words: name-like, yet a foreign phrase (C3)
    "other": "cantTell",
}
_SKIP_TEXT = re.compile(r"^(?:[\d\s.,:;/()+%'’-]+|\S+@\S+|https?://\S+|www\.\S+)$")
_SENTENCE_END = re.compile(r"[.!?…]\s*[\"'»”)]?\s*$")


def primary(code: str | None) -> str:
    p = (code or "").strip().lower().replace("_", "-").split("-")[0]
    return EQUIVALENT.get(p, p)


def is_valid_lang(value: str) -> bool:
    v = value.strip()
    if not BCP47.match(v):
        return False
    p = v.split("-")[0].lower()
    return p in ISO_639_1 if len(p) == 2 else True


def sentence_like(text: str) -> bool:
    """≥ 6 words ending with sentence punctuation. Long names of institutions have no
    final period, so they are never failed without asking the model."""
    return word_count(text) >= SENTENCE_MIN_WORDS and bool(_SENTENCE_END.search(text.strip()))


# Running-text markers per language: finite auxiliaries/modals, subject pronouns,
# negation, politeness imperatives. Titles, names and addresses rarely contain one.
RUNNING_TEXT_MARKERS = {
    "fr": set("est sont était étaient sera seront a ont avait peut peuvent doit doivent faut sommes êtes "
              "fait font va vont vous nous il elle ils elles on ne pas veuillez merci".split()),
    "it": set("è sono era erano sarà saranno ha hanno può possono deve devono bisogna siamo siete fa fanno "
              "va vanno si non vi ci grazie preghiamo".split()),
    "en": set("is are was were will be been has have had can could must should would do does did "
              "you we they it not please thank".split()),
    "de": set("ist sind war waren wird werden hat haben kann können muss müssen soll sollen darf "
              "sie wir ihr es nicht bitte danke".split()),
    "es": set("es son está están fue ha han puede pueden debe usted nosotros no gracias".split()),
    "pt": set("é são está estão foi tem têm pode podem deve você nós não obrigado".split()),
}
_QUOTED = re.compile(r"[«‹„“\"‚‘]([^«»‹›„“”\"‚‘’]{3,})[»›“”\"‘’]")
_ADDRESS = (
    re.compile(r"\b(?:CH-)?\d{4,5}\s+[A-ZÀ-Ý][\w'’.-]+"),  # postcode + place
    re.compile(r"\b(?:rue|route|chemin|ch\.|avenue|av\.|place|quai|boulevard|impasse|ruelle|allée|via|viale|"
               r"piazza|vicolo|corso|strada|largo|street|road|lane)\b[^,\n]{0,40}?\b\d{1,4}[a-z]?\b",
               re.IGNORECASE),  # street keyword … number
    re.compile(r"\b[\wäöüÄÖÜß-]+(?:strasse|straße|gasse|weg|platz|allee)\s+\d{1,4}[a-z]?\b", re.IGNORECASE),
    re.compile(r"\+?\d{2,3}[\s/.-]\d{2,3}[\s/.-]\d{2,3}[\s/.-]\d{2}\b"),  # phone number
)


def running_text(text: str, lang: str) -> bool:
    """Does the text read as a sentence (not a title, name or address) in `lang`?
    Unknown languages count as not verified (→ Apertus)."""
    markers = RUNNING_TEXT_MARKERS.get(primary(lang))
    if not markers:
        return False
    return any(w in markers for w in re.findall(r"[^\W\d_]+", text.lower()))


def quoted_share(text: str, quoted_elements: list[str] | tuple[str, ...] = ()) -> float:
    """Share of the text inside quotation marks or quote-like elements (q, cite, i, em, dfn)."""
    if not text:
        return 0.0
    segments = [m.group(1) for m in _QUOTED.finditer(text)] + [q for q in quoted_elements if q and q in text]
    return min(1.0, sum(len(x) for x in segments) / len(text))


def address_like(text: str) -> bool:
    return any(rx.search(text) for rx in _ADDRESS) or (text.count(",") >= 2 and bool(re.search(r"\d", text)))


# Function words that segment-boundary noise leaves at a span's edges ("… am", "en …").
EDGE_WORDS = {
    "de": set("am an im in zu um der die das den dem des und mit von vom zum zur auf".split()),
    "fr": set("en de du la le les et à au aux des un une sur par".split()),
    "it": set("e il la le lo di da in al del per con a su".split()),
    "en": set("in at on of and the to a an by".split()),
}
_EDGE_PUNCT = " \n\t*·•|,;:–—-()[]"
_CONTACT_LABEL = re.compile(r"^(?:t[ée]l(?:[ée]phone|efono|efon)?|t|fax|e-?mail|mail|courriel|web|internet|postfach|"
                            r"case postale|casella postale)\.?\s*:?\s*", re.IGNORECASE)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_WEB = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
_PHONE_ONLY = re.compile(r"\+?\d[\d\s/.()-]{6,}\d")
_POSTCODE_LINE = re.compile(r"^(?:CH-)?\d{4,5}\s+[A-ZÀ-Ý][\w'’ .-]{1,40}$")
_STREET_LINE = re.compile(r"^[A-ZÀ-Ý][\w'’ .-]{1,40}\s\d{1,4}[a-z]?$")
# A span carries language only with ≥ 3 alphabetic words of ≥ 3 letters when it contains
# digits ("Di 14.00–17.00 Uhr" carries none), and with ≥ 50 % letters among its characters.
MIN_ALPHA_WORDS_WITH_DIGITS = 3
MIN_ALPHA_RATIO = 0.5


def contact_line(line: str) -> bool:
    """A line that is only contact data: street + number, postcode + place, phone,
    e-mail, web address, or several of these separated by · | , ; (exception T1)."""
    text = line.strip().strip(_EDGE_PUNCT)
    if not text:
        return True
    bare = _CONTACT_LABEL.sub("", text).strip()
    if any(rx.fullmatch(bare) for rx in (_EMAIL, _WEB, _PHONE_ONLY)):
        return True
    if _POSTCODE_LINE.match(bare) or _STREET_LINE.match(bare):
        return True
    parts = [x for x in re.split(r"\s*[·•|,;]\s*", text) if x.strip()]
    return len(parts) > 1 and all(contact_line(x) for x in parts)


def language_bearing(text: str) -> bool:
    """Enough words to tell a language: number- and abbreviation-heavy text is not."""
    chars = [ch for ch in text if not ch.isspace()]
    if not chars:
        return False
    if sum(ch.isalpha() for ch in chars) / len(chars) < MIN_ALPHA_RATIO:
        return False
    long_words = [w for w in WORD_RE.findall(text) if len(w) >= 3]
    return not (any(ch.isdigit() for ch in text) and len(long_words) < MIN_ALPHA_WORDS_WITH_DIGITS)


def trim_span(span: str, declared: str) -> str:
    """Remove segmentation noise at the edges of a detected span: punctuation, asterisks
    and short function words of the declared language. Only the ends are cut, so the
    result stays a verbatim substring."""
    edge = EDGE_WORDS.get(primary(declared), set())
    out = span.strip()
    while True:
        cur = out.strip(_EDGE_PUNCT)
        first = re.match(r"^(\S+)\s+", cur)
        if first and len(first.group(1)) <= 3 and first.group(1).lower() in edge:
            cur = cur[first.end():]
        last = re.search(r"\s+(\S+)$", cur)
        if last and len(last.group(1).rstrip(".,;:!?")) <= 3 and last.group(1).rstrip(".,;:!?").lower() in edge:
            cur = cur[: last.start()]
        if cur == out:
            return out
        out = cur


def askable(span: str) -> bool:
    """Worth a question: ≥ 2 words, ≥ 8 characters, language-bearing; a single
    capitalised token is a name or a loanword (never asked, never failed)."""
    words = WORD_RE.findall(span)
    return (len(words) >= SPAN_MIN_WORDS and len(span) >= SPAN_MIN_CHARS and language_bearing(span))


def fails_in_code(text: str, lang: str, declared_conf: float, quoted_elements=()) -> bool:
    """The deterministic 3.1.2 failure: a whole passage of clear running text in another
    language. Anything that may be an exception (title, quote, name, address) is asked."""
    return (sentence_like(text) and declared_conf <= DECLARED_MAX_CONF and running_text(text, lang)
            and quoted_share(text, quoted_elements) < 0.5 and not address_like(text))


class LanguageOfParts(BaseCheck):
    criterion = "3.1.2"
    prompt_version = PROMPT_VERSION
    max_candidates = 200

    # -- 1. candidates ------------------------------------------------------------------
    def candidates(self, page: CapturedPage) -> list[Candidate]:
        det = get_detector(self.settings.detect_langs)
        supported = {primary(c) for c in self.settings.detect_langs}
        out: list[Candidate] = []
        invalid: set[str] = set()

        # (a) syntactically invalid lang values (ACT de46e4)
        for el in page.lang_elements:
            value = el.get("lang") or ""
            if not value.strip() or is_valid_lang(value):
                continue
            invalid.add(el["selector"])
            fixed = value.strip().replace("_", "-")
            if is_valid_lang(fixed):
                suggestion = fixed
            else:
                d = det.detect(el.get("text", "")) if word_count(el.get("text", "")) >= 3 else None
                suggestion = d.lang if d else None
            out.append(self.candidate(page, selector=el["selector"], html=el.get("html", ""), text=el.get("text", ""),
                                      lang=value, key="#invalid", kind="invalid_tag", value=value,
                                      suggestion=suggestion))

        # (b) the page's main text is in another language than <html lang>: that is a 3.1.1
        # problem. Asking about every part would be noise (and the model calls them loanwords).
        mismatch = self.page_language_mismatch(page, det)
        page_decl = primary(page.lang)
        if mismatch is not None:
            lang, share, sample = mismatch
            out.append(self.candidate(page, selector="html", html=f'<html lang="{page.lang}">', text=sample,
                                      lang=page.lang, key="#page", kind="page_language_mismatch", detected=lang,
                                      main_share=round(share, 4), langs=sorted({page_decl, lang})))

        # (c) passages
        for p in page.passages:
            if len(out) >= self.max_candidates:
                break
            text = p.get("text", "")
            declared = p.get("lang")
            if not declared or p["selector"] in invalid or _SKIP_TEXT.match(text) or word_count(text) < 1:
                continue
            decl = primary(declared)
            code = endonym(text)
            if code is not None:  # language switcher entry
                if primary(code) != decl:
                    out.append(self._make(page, p, "switcher", code, 0.0, text, None))
                elif p.get("own_lang") is not None:
                    out.append(self._make(page, p, "tagged_ok", code, 1.0, text, None))
                continue
            if p.get("own_lang") is not None and text.strip().lower() == decl and len(decl) in (2, 3):
                out.append(self._make(page, p, "tagged_ok", decl, 1.0, text, None))  # switcher code "FR" lang="fr"
                continue
            if decl not in supported:
                continue  # the detector cannot verify this language (e.g. Romansh)
            if p.get("own_lang") is not None:
                c = self._tagged(page, p, det, decl)
            elif mismatch is not None and decl == page_decl:
                continue  # inherits the wrong page language: reported once, above
            else:
                c = self._untagged(page, p, det, decl)
            if c is not None:
                out.append(c)
        return out

    def _tagged(self, page: CapturedPage, p: dict, det: LanguageDetector, decl: str) -> Candidate | None:
        """A passage carrying its own lang attribute: verify it (off6ek)."""
        text = p["text"]
        if word_count(text) < 2:
            return None
        d = det.detect(text)
        if d is None:
            return None
        decl_conf = det.confidence(text, decl)
        if primary(d.lang) == decl and d.confidence >= TAGGED_OK_MIN_CONF:
            return self._make(page, p, "tagged_ok", d.lang, decl_conf, text, d)
        if primary(d.lang) != decl and sentence_like(text) and decl_conf <= DECLARED_MAX_CONF:
            return self._make(page, p, "tagged_mismatch", d.lang, decl_conf, text, d)
        return None

    def page_language_mismatch(self, page: CapturedPage, det: LanguageDetector) -> tuple[str, float, str] | None:
        """(language, share, sample) when the page's main text is clearly in another language
        than <html lang>, by EXACTLY the rule of 3.1.1 (c_3_1_1.main_language and
        MAIN_MIN_SHARE): 3.1.1 then reports one page-level failure and 3.1.2 asks nothing
        about the parts. None otherwise."""
        decl = primary(page.lang)
        if not decl or decl not in {primary(c) for c in self.settings.detect_langs}:
            return None
        texts = [p["text"] for p in page.passages if p.get("own_lang") is None and primary(p.get("lang")) == decl
                 and not all(contact_line(line) for line in p["text"].split("\n"))]
        try:  # imported lazily: registry discovery imports check modules in any order
            from klar.checks import c_3_1_1

            lang, share = c_3_1_1.main_language(page, langs=self.settings.detect_langs)
            threshold = c_3_1_1.MAIN_MIN_SHARE
        except (ImportError, AttributeError):  # fallback when 3.1.1 is absent: same idea, on passages
            joined = "\n".join(texts)[:6000]
            d = det.detect(joined) if word_count(joined) >= 40 else None
            lang, share, threshold = (d.lang, d.confidence, 0.8) if d else (None, 0.0, 0.8)
        if lang is None or share < threshold or primary(lang) == decl:
            return None
        return lang, share, ((texts[0] if texts else page.text) or "")[:300]

    def _untagged(self, page: CapturedPage, p: dict, det: LanguageDetector, decl: str) -> Candidate | None:
        """A passage inheriting its language: is (part of) it in another language?

        Lines that are only contact data are set aside first (an address block in another
        language is exception T1, decided in code). Number-heavy text carries no
        language. Only a whole passage of running text may fail in code; every other
        foreign part is trimmed of segmentation noise and asked."""
        text = p["text"]
        lines = [line for line in text.split("\n") if line.strip()]
        non_contact = [line for line in lines if not contact_line(line)]
        if not non_contact:  # an address / contact block
            d = det.detect(text)
            if d and primary(d.lang) != decl:
                return self._make(page, p, "contact_line", d.lang, det.confidence(text, decl), text, d)
            return None
        # number-heavy lines (opening hours, prices) carry no language
        content_lines = [line for line in non_contact if language_bearing(line)]
        if not content_lines:
            return None
        content = "\n".join(content_lines)
        contiguous = norm_ws(content) in norm_ws(text)
        d = det.detect(content)
        if d and primary(d.lang) != decl:
            decl_conf = det.confidence(content, decl)
            if contiguous and fails_in_code(content, d.lang, decl_conf, p.get("quoted") or ()):
                return self._make(page, p, "untagged_sentence", d.lang, decl_conf, content, d)
            whole_foreign = (sentence_like(content) and decl_conf <= DECLARED_MAX_CONF) or d.confidence >= WHOLE_MIN_CONF
            if whole_foreign and decl_conf <= SPAN_DECLARED_MAX_CONF:
                span = trim_span(content if contiguous else max(content_lines, key=len), decl)
                return self._make(page, p, "ask", d.lang, decl_conf, span, d) if askable(span) else None
        spans: list[tuple[str, str, float]] = []
        for s in det.spans(content):
            if primary(s.lang) == decl or s.confidence < SPAN_MIN_CONF:
                continue
            chunk = trim_span(s.text, decl)
            if "\n" in chunk:  # never across a line boundary
                chunk = trim_span(max(chunk.split("\n"), key=len), decl)
            if not askable(chunk):
                continue
            decl_conf = det.confidence(chunk, decl)
            if decl_conf <= SPAN_DECLARED_MAX_CONF:
                spans.append((chunk, s.lang, decl_conf))
        if not spans:
            return None
        span, lang, decl_conf = max(spans, key=lambda x: len(x[0]))
        # A foreign span inside a mixed passage is never failed in code: it may be a title,
        # a quote, a name or an address. Apertus classifies it.
        return self._make(page, p, "ask", lang, decl_conf, span, d)

    def _make(self, page: CapturedPage, p: dict, kind: str, lang: str, declared_conf: float, span: str,
              d: Detection | None) -> Candidate:
        """`declared_conf` = detector confidence that the text IS in the declared
        language (low = clearly foreign)."""
        declared = p.get("own_lang") or p.get("lang")
        langs = sorted({primary(declared), lang, *([d.lang] if d else []), *([d.runner_up] if d and d.runner_up else [])})
        context = {"declared_language": f'lang="{declared}"'}
        if kind == "ask":
            context["detector"] = f'"{span[:120]}" looks like {lang}'
            if not p.get("is_container") and p.get("container_text"):
                context["surrounding_text"] = p["container_text"]
        return self.candidate(page, selector=p["selector"], html=p.get("html", ""), text=p["text"], lang=declared,
                              context=context, kind=kind, detected=lang, declared_confidence=round(declared_conf, 4),
                              span=span, langs=langs, is_container=p.get("is_container", True))

    # -- 2. deterministic decisions ----------------------------------------------------------
    def decide(self, c: Candidate) -> Finding | None:
        kind = c.extra.get("kind")
        ui = self.ui_lang
        if kind == "invalid_tag":
            value, sugg = c.extra["value"], c.extra.get("suggestion")
            diff = unified_diff(c.html, set_attr(c.html, "lang", sugg), c.selector) if sugg else None
            return self.finding(c, outcome="failed", source="rule", confidence="high", act_rule="de46e4",
                                excerpt=f'lang="{value}"' if f'lang="{value}"' in c.html else None,
                                explanation=t("c312.invalid", ui, value=value),
                                user_impact=t("c312.impact_invalid", ui, value=value), fix_diff=diff,
                                fix_hint=t("c312.fix_hint_invalid", ui, value=value, code=sugg or "de"))
        detected = c.extra.get("detected", "")
        kw = lang_kwargs(detected, c.lang_declared, ui)
        if kind == "tagged_ok":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium",
                                explanation=t("c312.tagged_ok", ui, code=c.lang_declared),
                                user_impact=t("c312.impact_ok", ui, **lang_kwargs(detected, detected, ui)))
        if kind == "page_language_mismatch":
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="high", act_rule=None,
                                explanation=t("c312.page_mismatch", ui, **kw),
                                user_impact=voice_sentence(detected, c.lang_declared or "", ui))
        if kind == "contact_line":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium",
                                explanation=t("c312.contact_line", ui), user_impact=t("c312.impact_exception", ui))
        if kind == "switcher":
            return self.finding(c, outcome="failed", source="heuristic", confidence="medium",
                                excerpt=c.text[:300], explanation=t("c312.switcher", ui, text=c.text, code=detected),
                                user_impact=voice_sentence(detected, c.lang_declared or "", ui),
                                fix_diff=self.fix_diff(c, c.text, detected), fix_hint=t("c312.fix_hint", ui, **kw))
        if kind == "tagged_mismatch":
            return self.finding(c, outcome="failed", source="heuristic", confidence=self._conf(c),
                                explanation=t("c312.mismatch", ui, **kw),
                                user_impact=voice_sentence(detected, c.lang_declared or "", ui),
                                fix_diff=unified_diff(c.html, set_attr(c.html, "lang", detected), c.selector),
                                fix_hint=t("c312.fix_hint", ui, **kw))
        if kind == "untagged_sentence":
            span = c.extra.get("span", c.text)
            return self.finding(c, outcome="failed", source="heuristic", confidence=self._conf(c),
                                excerpt=span[:300], explanation=t("c312.untagged", ui, **kw),
                                user_impact=voice_sentence(detected, c.lang_declared or "", ui),
                                fix_diff=self.fix_diff(c, span, detected), fix_hint=t("c312.fix_hint", ui, **kw))
        return None  # "ask" → Apertus

    @staticmethod
    def _conf(c: Candidate) -> str:
        return "high" if c.extra.get("declared_confidence", 1.0) <= 0.02 else "medium"

    # -- 3. the closed (categorical) question -------------------------------------------------
    # Prompt tuning happens on the dev split only. The categories are described generically,
    # without examples: no example may come from the test set or the demo site
    # (tests/test_leakage.py). Bump PROMPT_VERSION on any change.
    SYSTEM = (
        "You check WCAG 2.1 success criterion 3.1.2 Language of Parts. A language detector flagged a part of "
        "a passage as a language different from the declared language. Classify the flagged part:\n"
        "- proper_name: the name of a person, product, venue or event\n"
        "- institution: the official name of an organisation, authority or company\n"
        "- place_or_address: a place name or a postal address\n"
        "- technical_term: a technical term, or a word of indeterminate language\n"
        "- loanword_in_vernacular: a word from another language that has become part of everyday speech "
        "in the declared language\n"
        "- greeting_or_formula: a short greeting or polite formula (1 to 3 words) from another language\n"
        "- title_of_work: the title of a book, exhibition, song or similar work in another language\n"
        "- foreign_language_passage: a phrase or sentence written in another language\n"
        "- other: none of these, or unsure\n"
        "language: the language code of the flagged part (ISO 639-1). "
        "quote: the complete name or phrase in the other language, copied exactly from the passage."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        # ui_lang is deliberately unused: prompts are identical for every UI language.
        return self.task(
            system=self.system_prompt(self.SYSTEM, c),
            element={"passage": c.text[:400]},
            context=c.context,
            question="Which category is the flagged part?",
            schema=category_schema(CATEGORIES, extra={"language": {"type": "string", "maxLength": 12}}),
            max_tokens=140,
        )

    # -- 4. interpretation ----------------------------------------------------------------------
    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        category = answer["category"]
        lang = primary(answer.get("language")) or c.extra.get("detected", "")
        outcome = CATEGORY_OUTCOME.get(category, "cantTell")
        if outcome == "failed" and primary(lang) == primary(c.lang_declared):
            outcome = "cantTell"  # self-contradictory answer: "foreign" but same language
        quote = (answer.get("quote") or "").strip() or c.extra.get("span", "")
        reason = answer.get("reason")
        kw = lang_kwargs(lang, c.lang_declared, ui)
        code = f"apertus_{category}" if CATEGORY_OUTCOME.get(category) == outcome else "apertus_contradiction"
        common = dict(source="apertus", excerpt=quote, reason=reason, reason_code=code,
                      content_lang=lang or c.lang_declared)
        if outcome == "failed":
            return self.finding(c, outcome="failed", confidence=answer.get("confidence", "low"),
                                explanation=t("c312.foreign", ui, quote=quote, **kw),
                                user_impact=voice_sentence(lang, c.lang_declared or "", ui),
                                fix_diff=self.fix_diff(c, quote, lang), fix_hint=t("c312.fix_hint", ui, **kw), **common)
        if outcome == "passed":
            label = t(f"c312.cat.{category}", ui)
            return self.finding(c, outcome="passed", confidence=answer.get("confidence", "low"),
                                explanation=t("c312.exception", ui, quote=quote, category=label),
                                user_impact=t("c312.impact_exception", ui), **common)
        if category in ("greeting_or_formula", "title_of_work"):
            explanation = t("c312.boundary", ui, quote=quote, category=t(f"c312.cat.{category}", ui))
        else:
            explanation = t("c312.other", ui, quote=quote)
        return self.finding(c, outcome="cantTell", confidence="low", explanation=explanation,
                            user_impact=t("impact.review", ui), **common)

    @staticmethod
    def fix_diff(c: Candidate, part: str, lang: str) -> str | None:
        """lang on the element when the part is its whole text, else a <span lang>."""
        if " ".join(part.split()) == " ".join(c.text.split()) and c.extra.get("is_container", True):
            after = set_attr(c.html, "lang", lang)
        else:
            after = wrap_text(c.html, part, f'<span lang="{lang}">', "</span>")
            if after is None:
                return None
        return unified_diff(c.html, after, c.selector)



CHECK = LanguageOfParts
