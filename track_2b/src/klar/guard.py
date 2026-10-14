"""Evidence guard and prompt-injection pre-filter.

Pre-filter (`suspicious`): a candidate whose page text looks like instructions
to an AI ("ignore previous instructions", "system prompt", a JSON verdict, "answer
passed"… in EN/DE/FR/IT) is never sent to the model and never passed by a
heuristic: it becomes cantTell "suspicious content", unless the check's own code
already found a failure (that stands: an injected "passed" cannot cause it).
Together with the <page_data> JSON block and the untrusted-data system prompt
(checks/base.py), an injected "passed" cannot reach a finding.

An Apertus finding is DISCARDED (→ cantTell "model answer not grounded", counted
in stats.guard_rejected) when:

  1. its excerpt is not a verbatim substring of the candidate's html or text
     (after whitespace / entity / quote-mark normalisation), or a `failed`
     verdict comes without any quote;
  2. its selector does not resolve in the captured DOM;
  3. the model's own words cite a language code, a number or a URL that does not
     appear in the candidate.

Rule 3 inspects what the model *claims*: the structured `language` field and
`lang="…"` mentions, plus numbers (≥ 2 digits) and URLs in `reason`. Proposed
replacement text (`fix`) is new text by nature and is not inspected. Checks that
read numbers off an image set `guard_numbers = False`.
"""

from __future__ import annotations

import html as htmllib
import json
import re
import unicodedata
from dataclasses import dataclass

from klar.i18n import t
from klar.models import Candidate, Finding

_QUOTES = str.maketrans({"’": "'", "‘": "'", "‚": "'", "“": '"', "”": '"', "„": '"', "«": '"', "»": '"', " ": " "})
_LANG_ATTR = re.compile(r"""\blang\s*=\s*["']?([A-Za-z]{2,3}(?:-[A-Za-z0-9]+)*)""")
_NUMBER = re.compile(r"\d[\d'’.,]*\d")
_WCAG_REF = re.compile(r"\b(?:WCAG\s*)?[1-4]\.[0-9](?:\.[0-9]{1,2})?\b", re.IGNORECASE)
_URL = re.compile(r"(?:https?://|www\.)[^\s\"'<>)\]]+", re.IGNORECASE)


# Instruction-like page text. Every alternative needs a cue that the text addresses an
# AI judge: "ignore previous instructions", "system prompt", "you are an AI / a model",
# chat-template role markers, a JSON verdict, an answer/output imperative followed by
# one of OUR answer tokens, or "mark … as passed". Ordinary page text that merely uses
# verdict words ("Ergebnis: bestanden", "Résultat : réussi", "Esito: superato", "Mark
# the box if you passed") or staff labels ("Assistant: …", "System: maintenance") is
# NOT flagged: a hit turns the candidate into cantTell, so false hits hide findings.
_ANSWER_TOKENS = r"(passed|failed|canttell|link_text|nowhere|proper_name|institution|decorative" \
                 r"|foreign_language_passage|loanword_in_vernacular)"
INJECTION = re.compile(
    r"""(
      \b(ignore|disregard|forget)\s+(all\s+|any\s+)?(the\s+|your\s+)?(previous|prior|above|earlier|preceding)\s+
        (instructions?|prompts?|rules|messages?)
    | \bignorier(e|en|t)?\s+(sie\s+)?(alle\s+)?(die\s+)?(vorherigen|bisherigen|obigen|vorangehenden)\s+(anweisungen|instruktionen|regeln)
    | \bignore[zr]?\s+(toutes\s+)?(les\s+)?(instructions|consignes|règles)\s+(précédentes|ci-dessus|antérieures)
    | \bignora(re|te)?\s+(tutte\s+)?(le\s+)?(istruzioni|regole)\s+(precedenti|sopra)
    | \bsystem\s*prompt\b | \bsystemprompt\b | \bprompt\s+(système|systeme|di\s+sistema)\b
    | \byou\s+are\s+(now\s+)?(an?\s+)?(ai|assistant|language\s+model|llm|chatbot|judge|evaluator|grader|classifier)\b
    | \bdu\s+bist\s+(jetzt\s+|nun\s+)?(ein(e)?\s+)?(ki|assistent|sprachmodell|chatbot|prüfer)\b
    | \btu\s+es\s+(maintenant\s+|désormais\s+)?(une?\s+)?(ia|assistant|modèle\s+de\s+langage|chatbot|évaluateur)\b
    | \bsei\s+(ora\s+|adesso\s+)?(una?\s+|un'\s*)?(ia|assistente|modello\s+linguistico|chatbot|valutatore)\b
    | <\|\s*[a-z_]{2,20}\s*\|> | \[/?inst\] | <</?sys>>
    | (^|\n)\s*\#{2,}\s*(system|assistant|instructions?)\b
    | \b(system|assistant)\s*:\s*(you\s+are|ignore|answer|respond|reply|output)\b
    | "(outcome|category|image_type|confidence)"\s*:
    | \b(answer|respond|reply|output)\b(\s+(only|just|with|using|as|the|word|value|outcome|verdict|category|label)){0,4}
        \s*[:"'“«]?\s*["'“«]?"""
    + _ANSWER_TOKENS + r"""\b
    | \b(output|return|respond|answer|reply)\b.{0,20}?\bjson\b
    | \b(mark|set|classify|label|report|rate|judge|flag|treat|consider|evaluate)\b.{0,40}?\bas\s+["'“«]?"""
    + _ANSWER_TOKENS + r"""\b
    | \b(outcome|verdict)\b\s*(is|=|:|should\s+be|must\s+be)\s*["'“«]?(passed|failed|canttell)\b
    | \b(antwort\w*|gib|setze|markiere\w*|bewerte\w*|ergebnis\w*|urteil\w*|réponds|répondez|répondre|indique[zr]?
         |marque[zr]?|résultat|verdict|rispondi|rispondete|rispondere|indica|segna|esito|verdetto)\b
        .{0,30}?["'„“«»]?\b(passed|failed|canttell)\b
    | \bantworte(n|t)?(\s+sie)?\s+(nur\s+|ausschliesslich\s+|ausschließlich\s+)?mit\s*[:"'„«]?\s*["'„«]?
        (bestanden|nicht\s+bestanden)\b
    | \b(markiere|bewerte|setze)\w*(\s+\w+){0,4}?\s+als\s+["'„«]?(bestanden|nicht\s+bestanden)\b
    | \br[ée]pond(s|ez|re)\s+(uniquement\s+|seulement\s+)?(par\s+|avec\s+)?[:"'«]?\s*["'«]?\s*(réussi|échoué|échec)\b
    | \b(indique[zr]?|marque[zr]?|note[zr]?)\s+(comme\s+|:\s*)?["'«]?\s*(réussi|échoué)\b
    | \b(marque[zr]?|note[zr]?|évalue[zr]?)(\s+\w+){0,3}?\s+comme\s+["'«]?\s*(réussi|échoué)\b
    | \brispond(i|ete|ere)\s+(solo\s+|soltanto\s+)?(con\s+)?[:"'«]?\s*["'«]?\s*(superato|non\s+superato|fallito)\b
    | \b(segna|indica|marca|valuta)(\s+\w+){0,3}?\s+come\s+["'«]?\s*(superato|non\s+superato|fallito)\b
    | </?\s*page_data
    )""",
    re.IGNORECASE | re.VERBOSE,
)


def suspicious(c: Candidate) -> str | None:
    """The matched instruction-like text, or None. Looks at everything that could
    reach a prompt or a heuristic: text, accessible name, HTML, context."""
    for part in (c.text, c.accessible_name or "", c.html, *c.context.values()):
        m = INJECTION.search(part or "")
        if m:
            return " ".join(m.group(0).split())[:60]
    return None


@dataclass(frozen=True)
class Verdict:
    ok: bool
    reason: str | None = None


def normalize(s: str | None) -> str:
    s = unicodedata.normalize("NFC", htmllib.unescape(s or "")).translate(_QUOTES)
    return " ".join(s.split())


def _primary(code: str) -> str:
    return code.strip().lower().replace("_", "-").split("-")[0]


def _haystack(c: Candidate) -> str:
    parts = [c.html, c.text, c.accessible_name or "", c.lang_declared or "", *c.context.values(),
             json.dumps(c.extra, ensure_ascii=False, default=str)]
    return normalize(" ".join(parts))


def allowed_lang_codes(c: Candidate) -> set[str]:
    codes = {_primary(c.lang_declared)} if c.lang_declared else set()
    codes |= {_primary(m) for m in _LANG_ATTR.findall(c.html)}
    for v in c.context.values():
        codes |= {_primary(m) for m in _LANG_ATTR.findall(v)}
    for key in ("langs", "detected", "suggestion"):
        v = c.extra.get(key)
        if isinstance(v, str):
            codes.add(_primary(v))
        elif isinstance(v, (list, tuple)):
            codes |= {_primary(x) for x in v if isinstance(x, str)}
    return {x for x in codes if x}


def check(finding: Finding, c: Candidate, answer: dict | None, *, selector_exists=None,
          check_numbers: bool = True) -> Verdict:
    """Return Verdict(ok=False, reason) when the finding must be discarded."""
    # Rule 1 — verbatim evidence
    excerpt = normalize(finding.excerpt)
    if not excerpt:
        if finding.outcome == "failed":
            return Verdict(False, "no quote")
    elif excerpt not in normalize(c.html) and excerpt not in normalize(c.text):
        return Verdict(False, "quote not found in the element")

    # Rule 2 — the selector resolves
    if selector_exists is not None and not selector_exists(finding.selector):
        return Verdict(False, "selector does not resolve")

    # Rule 3 — cited language codes, numbers, URLs
    answer = answer or {}
    claims = " ".join(str(answer.get(k) or "") for k in ("reason", "quote"))
    codes = [answer["language"]] if isinstance(answer.get("language"), str) and answer["language"].strip() else []
    codes += _LANG_ATTR.findall(claims)
    if codes:
        allowed = allowed_lang_codes(c)
        for code in codes:
            if _primary(code) not in allowed:
                return Verdict(False, f"language code {code!r} not in the element")
    hay = _haystack(c)
    if check_numbers:
        # "2025" matches "31.12.2025"; "1'200" matches "1200" and "1 200" does not.
        hay_numbers = set(re.findall(r"\d+", hay)) | {re.sub(r"\D", "", m) for m in _NUMBER.findall(hay)}
        # WCAG references ("WCAG 2.1", "3.1.2") are not claims about the page.
        plain = _WCAG_REF.sub(" ", normalize(claims))
        for num in _NUMBER.findall(plain):
            digits = re.sub(r"\D", "", num)
            if len(digits) >= 2 and digits not in hay_numbers:
                return Verdict(False, f"number {num!r} not in the element")
    low = hay.lower()
    for url in _URL.findall(claims):
        u = url.rstrip(".,;:!?").lower()
        if u not in low and u.split("://", 1)[-1] not in low:
            return Verdict(False, f"URL {url!r} not in the element")
    return Verdict(True)


def downgrade(finding: Finding, c: Candidate, reason: str, ui_lang: str) -> Finding:
    """The grounded-or-nothing fallback: cantTell, verbatim excerpt chosen by code."""
    return finding.model_copy(update={
        "outcome": "cantTell",
        "confidence": "low",
        "excerpt": (c.text or c.html)[:300],
        "explanation": t("note.not_grounded", ui_lang, reason=reason),
        "user_impact": t("impact.review", ui_lang),
        "fix_diff": None,
        "fix_hint": None,
        "reason_code": "not_grounded",
    })
