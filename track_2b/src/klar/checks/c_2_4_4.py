"""2.4.4 Link Purpose (In Context), level A. ACT rule 5effbb.

A link passes when its purpose can be determined from its accessible name alone
or together with its *programmatically determined link context* (ACT 5effbb):
the same sentence, the closest ancestor that generates a block container, list
item, table cell with its header cells, or aria-describedby text. A preceding
heading is NOT programmatic context (computed in capture/js/klar_extract.js,
never by the model).

Cascade
  1. empty accessible name            → not ours: axe-core `link-name` reports it (2.4.4 + 4.1.2)
  2. language switch                  → passed (heuristic, `language_switcher`): the name is a
                                        language code or endonym ("FR", "Italiano") AND hreflang /
                                        lang on the link agree with it, or the target carries that
                                        language (/fr/, ?lang=fr, fr.example.ch) or is the same
                                        page in another language version
     phone number                     → passed (heuristic, `phone_number`): a tel: link whose
                                        text is that number
     name is a URL or e-mail address  → passed (heuristic): the text names the destination
     (also a mailto: link whose text is that address)
  3. clearly descriptive name         → passed (heuristic), only when unambiguous:
                                        not generic, enough content words, and no other link
                                        with the same name pointing elsewhere
  4. generic or meaningless name ("mehr", "ici", "qui", "read more", "icon", "IMG_12.jpg"…)
     and NO programmatic context      → failed (heuristic), except:
       - every link with that name goes to the same target (no ambiguity) → ask Apertus;
       - the only disambiguation is a heading before the link in its own card
         (protocol 2.4.4/C1, technique H80) → cantTell (heuristic), the model is not asked;
       - the only disambiguation is the title attribute (2.4.4/C2, H33) → cantTell (heuristic).
  5. everything else                 → Apertus, with ONLY the link and its ACT context (no href,
                                        no destination: users do not see them), CATEGORICAL
                                        question "where does the user learn the purpose?":
                                        link_text | context | nowhere  → passed | passed | failed.
  Fix suggestions are deterministic: the same-origin destination page title, when known.
     (real-model finding, v1: asked "is the purpose clear?", the 8B model ignored a clear
      sentence context and failed "hier"; the "where" question forces it to read the context)
"""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from urllib.parse import parse_qsl, unquote, urldefrag, urlparse

from klar.capture.page import CapturedPage
from klar.checks.base import (BaseCheck, category_schema, in_element, replace_text, set_attr, unified_diff,
                              useful_fix)
from klar.i18n import lang_noun, primary_subtag, t
from klar.langid import ISO_639_1, WORD_RE, language_named
from klar.models import Candidate, Finding, LLMTask

# v2: categorical "where" question. v3: page data block, no destination, English reason.
PROMPT_VERSION = "2.4.4/v3"

CATEGORIES = ["link_text", "context", "nowhere"]
CATEGORY_OUTCOME = {"link_text": "passed", "context": "passed", "nowhere": "failed"}

# Normalised link texts that say nothing about the destination (DE · FR · IT · EN),
# including "type only" words (PDF, Download, Formular…).
GENERIC_TEXTS = {
    # de
    "mehr", "weiter", "hier", "klicken sie hier", "hier klicken", "mehr erfahren", "weiterlesen", "mehr lesen",
    "lesen sie mehr", "mehr dazu", "mehr informationen", "weitere informationen", "mehr infos", "details",
    "zum artikel", "zum beitrag", "jetzt lesen", "link", "download", "herunterladen", "öffnen", "seite",
    "zur seite", "dokument", "datei", "formular", "pdf", "video", "bild", "info", "infos", "mehr anzeigen",
    "alle anzeigen", "anzeigen", "ansehen", "hier lesen",
    # fr
    "plus", "en savoir plus", "cliquez ici", "cliquer ici", "ici", "lire la suite", "la suite", "suite",
    "lire plus", "en lire plus", "voir plus", "plus d'informations", "plus d'infos", "détails", "lien",
    "télécharger", "ouvrir", "cette page", "page", "document", "fichier", "formulaire", "voir", "continuer",
    "afficher", "tout afficher",
    # it
    "di più", "qui", "clicca qui", "cliccare qui", "leggi tutto", "leggi di più", "leggi", "scopri di più",
    "dettagli", "altro", "maggiori informazioni", "più informazioni", "continua", "continua a leggere",
    "scarica", "apri", "questa pagina", "pagina", "documento", "modulo", "vedi", "vedi tutto", "mostra",
    # en
    "more", "read more", "click here", "here", "learn more", "find out more", "more info", "more information",
    "continue", "continue reading", "this link", "go", "see more", "view more", "view", "open", "this page",
    "website", "file", "form", "image", "show more", "see all", "view all",
    # meaningless names of icon links (protocol 2.4.4/F3)
    "icon", "icône", "icona", "pfeil", "arrow", "flèche", "freccia", "symbol", "symbole", "simbolo",
    # symbols-only links normalise to ""
    "",
}
_FILENAME = re.compile(r"^\S+\.(?:jpe?g|png|gif|webp|svg|bmp|pdf|docx?|xlsx?)$|^(?:img|dsc|image|icon)[-_ ]?\d+", re.I)

# Words that carry no destination on their own; removed before counting content words.
FILLER_WORDS = {
    w for text in GENERIC_TEXTS for w in text.split()
} | {
    "für", "über", "zum", "zur", "zu", "der", "die", "das", "den", "dem", "des", "und", "oder", "ein", "eine",
    "unsere", "unser", "ihre", "ihr", "alle", "jetzt", "informationen", "information",
    "pour", "sur", "de", "du", "des", "le", "la", "les", "un", "une", "et", "ou", "en", "à", "au", "aux", "nos",
    "notre", "votre", "tous", "toutes", "informations",
    "per", "su", "di", "del", "della", "dei", "il", "lo", "gli", "le", "un", "una", "e", "o", "a", "al", "alla",
    "nostro", "nostra", "tutti", "informazioni",
    "for", "about", "to", "of", "the", "a", "an", "and", "or", "on", "our", "your", "all", "now", "info",
}

URL_OR_EMAIL = re.compile(
    r"^(?:(?:https?://|www\.)\S+|[\w.+-]+@[\w-]+(?:\.[\w-]+)+|[\w-]+(?:\.[\w-]+)*\.[a-z]{2,}(?:/\S*)?)$",
    re.IGNORECASE,
)
_STRIP = re.compile(r"[»«›‹>→←↗…:.!?()\[\]\"'“”„‚‘’|/\\+*#-]+")

# The link address is hidden from the verdict prompt: screen-reader users do not hear it.
_HREF = re.compile(r"""\shref\s*=\s*("[^"]*"|'[^']*'|[^\s>]+)""", re.IGNORECASE)

CONTEXT_KEYS = ("sentence", "block", "list_item", "table_cell", "table_headers", "described_by")

# A phone number as link text, optionally after a short label ("Tel.", "Tél. :", "Phone").
_PHONE_TEXT = re.compile(
    r"^(?:(?:tel|tél|telefon|téléphone|telefono|phone)\.?\s*:?\s*)?\+?[\d\s().\-/]+$", re.IGNORECASE)
_MAIL_LABEL = re.compile(r"^(?:e-?mail|mail|courriel|posta|kontakt|contact)\s*:\s*", re.IGNORECASE)
_LANG_PARAMS = {"lang", "language", "locale", "hl", "lng", "sprache", "langue", "lingua"}
_LANG_SEGMENT = re.compile(r"^([a-z]{2})(?:[-_][a-z]{2})?$")


def phone_link(name: str, href: str) -> bool:
    """A tel: link whose text is that number (same last 7 digits: +41 32… = 032…)."""
    if not (href or "").lower().startswith("tel:") or not _PHONE_TEXT.match(name.strip()):
        return False
    text_digits = re.sub(r"\D", "", name)
    href_digits = re.sub(r"\D", "", unquote(href))
    return 6 <= len(text_digits) <= 15 and len(href_digits) >= 6 and text_digits[-7:] == href_digits[-7:]


def mail_link(name: str, href: str) -> bool:
    """A mailto: link whose text is that address (an optional "E-Mail:" label aside)."""
    if not (href or "").lower().startswith("mailto:"):
        return False
    address = unquote(href[7:].split("?", 1)[0]).strip().lower()
    return bool(address) and _MAIL_LABEL.sub("", name.strip()).lower() == address


def _lang_code(value: str) -> str | None:
    m = _LANG_SEGMENT.match((value or "").lower())
    return m.group(1) if m and m.group(1) in ISO_639_1 else None


def url_languages(href: str) -> set[str]:
    """Languages a URL names: a path segment (/fr/, /de-ch/), a query parameter
    (?lang=it) or the first host label (fr.example.ch)."""
    u = urlparse(href or "")
    found = {_lang_code(seg) for seg in u.path.split("/")}
    found |= {_lang_code(v) for k, v in parse_qsl(u.query) if k.lower() in _LANG_PARAMS}
    labels = (u.hostname or "").split(".")
    if len(labels) > 2:
        found.add(_lang_code(labels[0]))
    return {c for c in found if c}


def _without_language(href: str) -> tuple:
    u = urlparse(urldefrag(href or "")[0])
    labels = (u.hostname or "").split(".")
    host = ".".join(labels[1:] if len(labels) > 2 and _lang_code(labels[0]) else labels)
    segs = [seg for seg in u.path.split("/") if seg and not _lang_code(seg)]
    if segs and segs[-1] in ("index.html", "index.htm", "index.php"):
        segs.pop()
    query = tuple(sorted((k, v) for k, v in parse_qsl(u.query) if k.lower() not in _LANG_PARAMS))
    return u.scheme, host, u.port, "/".join(segs), query


_SECOND_LEVEL = {"co", "com", "org", "net", "gov", "ac", "edu"}  # co.uk, com.au … (no public-suffix list)


def site_of(url: str) -> str:
    """Approximate registrable domain: the last two host labels (three under
    co.uk-style suffixes); an IP address or a single label stays as is."""
    host = (urlparse(url or "").hostname or "").lower().rstrip(".")
    labels = host.split(".")
    if len(labels) < 3 or all(x.isdigit() for x in labels) or ":" in host:
        return host
    if len(labels[-1]) == 2 and labels[-2] in _SECOND_LEVEL:
        return ".".join(labels[-3:])
    return ".".join(labels[-2:])


def same_site(href: str, page_url: str) -> bool:
    a, b = urlparse(href or ""), urlparse(page_url or "")
    if a.scheme == "file" and b.scheme == "file":
        return True
    return (a.scheme in ("http", "https") and b.scheme in ("http", "https")
            and bool(site_of(href)) and site_of(href) == site_of(page_url))


def language_switch(name: str, *, href: str, hreflang: str | None, own_lang: str | None, page_url: str) -> bool:
    """A link that names a language and leads to that language version of the site:
    its purpose is conventional and announced by its own language markup. Without
    hreflang/lang, the evidence is the URL, and then only on the same site (an "EN"
    link to an English encyclopaedia article is not a language switch)."""
    code = language_named(name)
    if code is None or not href or href.lower().startswith(("tel:", "mailto:", "javascript:")):
        return False
    marks = {primary_subtag(m) for m in (hreflang, own_lang) if m}
    if marks:
        return marks == {code}
    if not same_site(href, page_url):
        return False
    return code in url_languages(href) or _without_language(href) == _without_language(page_url)


def normalize_name(name: str) -> str:
    s = unicodedata.normalize("NFKC", name or "").lower().replace("’", "'")
    s = _STRIP.sub(" ", s)
    return " ".join(s.split())


def content_words(name: str) -> list[str]:
    words = [w.lower() for w in WORD_RE.findall(name or "")]
    return [w for w in words if w not in FILLER_WORDS and len(w) > 1]


def normalize_target(href: str) -> str:
    return urldefrag(href or "")[0].rstrip("/")


def act_context(raw: dict[str, str], name: str) -> dict[str, str]:
    """Keep only ACT context keys, drop empty values, values equal to the link
    text and values repeated by a broader key (sentence ⊂ block ⊂ list item…)."""
    out: dict[str, str] = {}
    seen: set[str] = set()
    norm_name = " ".join((name or "").split())
    for key in CONTEXT_KEYS:
        v = " ".join((raw or {}).get(key, "").split())
        if not v or v == norm_name or v in seen:
            continue
        seen.add(v)
        out[key] = v
    return out


class LinkPurpose(BaseCheck):
    criterion = "2.4.4"
    prompt_version = PROMPT_VERSION
    max_candidates = 300

    # -- 1. candidates ------------------------------------------------------------------
    def candidates(self, page: CapturedPage) -> list[Candidate]:
        links = [link for link in page.links if (link.get("name") or "").strip()]  # empty name → axe link-name
        targets_by_name: dict[str, set[str]] = defaultdict(set)
        count_by_name: dict[str, int] = defaultdict(int)
        for link in links:
            n = normalize_name(link["name"])
            targets_by_name[n].add(normalize_target(link.get("href", "")))
            count_by_name[n] += 1

        out: list[Candidate] = []
        for link in links[: self.max_candidates]:
            name = " ".join(link["name"].split())
            norm = normalize_name(name)
            context = act_context(link.get("context") or {}, link.get("text") or name)
            same_targets = len(targets_by_name[norm])
            kind = self.classify(name, context, same_name_count=count_by_name[norm], same_name_targets=same_targets,
                                 heading_hint=link.get("heading_hint", ""), title=link.get("title", ""),
                                 href=link.get("href", ""), hreflang=link.get("hreflang"),
                                 own_lang=link.get("own_lang"), page_url=page.url)
            extra = {
                "kind": kind,
                "href": link.get("href", ""),
                "same_name_count": count_by_name[norm],
                "same_name_targets": same_targets,
                "plain_text": "<" not in _inner_html(link.get("html", "")),
                # NOT context (never shown to the model): used only for the cantTell explanation.
                "heading_hint": link.get("heading_hint", ""),
            }
            if kind in ("ask", "generic_no_context", "generic_heading_only", "generic_title_only"):
                # Destination title: ONLY for the deterministic fix suggestion. It is never
                # shown to the model (users do not see it either).
                title = page.fetch_title(link.get("href", ""))
                if title:
                    extra["destination_title"] = title
            out.append(self.candidate(page, selector=link["selector"], html=link.get("html", ""),
                                      text=link.get("text", ""), accessible_name=name, context=context,
                                      lang=link.get("lang"), **extra))
        return out

    @staticmethod
    def classify(name: str, context: dict[str, str], *, same_name_count: int, same_name_targets: int,
                 heading_hint: str = "", title: str = "", href: str = "", hreflang: str | None = None,
                 own_lang: str | None = None, page_url: str = "") -> str:
        norm = normalize_name(name)
        if language_switch(name, href=href, hreflang=hreflang, own_lang=own_lang, page_url=page_url):
            return "language_switcher"
        if phone_link(name, href):
            return "phone_number"
        if mail_link(name, href) or (URL_OR_EMAIL.match(name.strip()) and not _FILENAME.match(name.strip())):
            return "url_or_email"
        generic = norm in GENERIC_TEXTS or bool(_FILENAME.match(name.strip()))
        same_target_duplicates = same_name_count > 1 and same_name_targets == 1
        ambiguous_duplicates = same_name_targets > 1
        if generic:
            if context or same_target_duplicates:
                return "ask"
            if heading_hint:
                return "generic_heading_only"
            if title and normalize_name(title) not in GENERIC_TEXTS and normalize_name(title) != norm:
                return "generic_title_only"
            return "generic_no_context"
        words = content_words(name)
        if not ambiguous_duplicates and (len(words) >= 2 or (len(words) == 1 and len(words[0]) >= 4)):
            return "descriptive"
        return "ask"

    # -- 2. deterministic decisions ----------------------------------------------------------
    def decide(self, c: Candidate) -> Finding | None:
        kind = c.extra.get("kind")
        name = c.accessible_name or ""
        excerpt = name if in_element(c, name) else None
        if kind == "language_switcher":
            language = lang_noun(language_named(name) or "", self.ui_lang)
            return self.finding(c, outcome="passed", source="heuristic", confidence="high", excerpt=excerpt,
                                explanation=t("c244.language_switcher", self.ui_lang, name=name, language=language),
                                user_impact=t("c244.impact_ok", self.ui_lang, name=name))
        if kind in ("url_or_email", "phone_number"):
            key = "c244.url_text" if kind == "url_or_email" else "c244.phone_number"
            return self.finding(c, outcome="passed", source="heuristic", confidence="high", excerpt=excerpt,
                                explanation=t(key, self.ui_lang),
                                user_impact=t("c244.impact_ok", self.ui_lang, name=name))
        if kind == "descriptive":
            confidence = "medium" if len(content_words(name)) >= 2 else "low"
            return self.finding(c, outcome="passed", source="heuristic", confidence=confidence, excerpt=excerpt,
                                explanation=t("c244.descriptive", self.ui_lang, name=name),
                                user_impact=t("c244.impact_ok", self.ui_lang, name=name))
        if kind == "generic_no_context":
            return self.finding(c, outcome="failed", source="heuristic", confidence="high", excerpt=excerpt,
                                explanation=t("c244.no_context", self.ui_lang, name=name),
                                user_impact=t("c244.impact", self.ui_lang, name=name), **self.fix(c))
        if kind in ("generic_heading_only", "generic_title_only"):
            key = "c244.heading_only" if kind == "generic_heading_only" else "c244.title_only"
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="medium", excerpt=excerpt,
                                explanation=t(key, self.ui_lang, name=name, heading=c.extra.get("heading_hint", "")),
                                user_impact=t("c244.impact_maybe", self.ui_lang, name=name), **self.fix(c))
        return None

    # -- 3. the closed (categorical) question -----------------------------------------------
    # Prompt tuning happens on the dev split only; bump PROMPT_VERSION on any change
    # to SYSTEM or the user template (it is part of the cache key).
    SYSTEM = (
        "You check WCAG 2.1 success criterion 2.4.4 Link Purpose (In Context) for ONE link.\n"
        "A screen-reader user hears the link text and can also read its programmatic context: the same "
        "sentence, the enclosing block, list item, table cell and its headers, or aria-describedby text, "
        "as given in `context`. Nothing else: no headings, no other page text, no link address.\n"
        "Where does the user learn what the link leads to?\n"
        "- link_text: the link text alone says it (a URL or an e-mail address counts)\n"
        "- context: the link text is vague, but the context says it\n"
        "- nowhere: neither the link text nor the context says it\n"
        "quote: the link text."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        # ui_lang is deliberately unused: prompts are identical for every UI language.
        return self.task(
            system=self.system_prompt(self.SYSTEM, c),
            element={"link_text": c.accessible_name or "", "html": _HREF.sub(' href="…"', self.prompt_html(c))},
            context=c.context,
            question="Where does the user learn what this link leads to?",
            schema=category_schema(CATEGORIES),
        )

    # -- 4. interpretation ----------------------------------------------------------------------
    def interpret(self, c: Candidate, answer: dict) -> Finding:
        category = answer["category"]
        outcome = CATEGORY_OUTCOME.get(category, "cantTell")
        if category == "context" and not c.context:
            outcome = "cantTell"  # "the context says it" but there is no context: contradiction
        name = c.accessible_name or ""
        fix: dict = {}
        if outcome == "failed":
            impact = t("c244.impact", self.ui_lang, name=name)
            fix = self.fix(c)
        elif outcome == "passed":
            impact = t("c244.impact_ok", self.ui_lang, name=name)
        else:
            impact = t("impact.review", self.ui_lang)
        key = {"link_text": "c244.apertus_link_text", "context": "c244.apertus_context",
               "nowhere": "c244.apertus_nowhere"}.get(category, "c244.apertus_unsure")
        if outcome == "cantTell":
            key = "c244.apertus_unsure"
        return self.finding(
            c, outcome=outcome, source="apertus",
            confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
            excerpt=self.model_excerpt(c, answer, outcome), explanation=t(key, self.ui_lang, name=name),
            user_impact=impact, reason=answer.get("reason"), reason_code=key.split(".")[-1], **fix,
        )

    def fix(self, c: Candidate) -> dict:
        """Deterministic fix: name the destination with its (same-origin) page title."""
        title = useful_fix(c.extra.get("destination_title"), c.accessible_name or c.text)
        if not title or title.casefold() == c.text.strip().casefold():
            return {"fix_hint": t("c244.fix_hint_plain", self.ui_lang)}
        return {"fix_diff": self.fix_diff(c, title), "fix_hint": t("c244.fix_hint", self.ui_lang, proposal=title)}

    @staticmethod
    def fix_diff(c: Candidate, proposal: str) -> str | None:
        visible = c.text.strip()
        after = replace_text(c.html, visible, proposal) if visible else None
        if after is None:
            # Complex content: name the link with aria-label, keeping the visible
            # text inside it (2.5.3 Label in Name).
            label = proposal if (not visible or visible.lower() in proposal.lower()) else f"{visible}: {proposal}"
            after = set_attr(c.html, "aria-label", label)
        return unified_diff(c.html, after, c.selector)


def _inner_html(outer: str) -> str:
    start = outer.find(">")
    end = outer.rfind("</")
    return outer[start + 1 : end] if start != -1 and end > start else ""


CHECK = LinkPurpose
