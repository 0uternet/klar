"""Language identification for 3.1.2 (and any check that needs it).

Backend: lingua-language-detector (Apache-2.0). We restrict it to the languages
that realistically occur on Swiss public-sector sites (KLAR_DETECT_LANGS); a
small set makes short-text detection much more reliable.

The detector only PROPOSES. It never decides alone whether a span is an
exception (proper name, loanword…): that is Apertus' job, or a deterministic
rule for long, confidently detected passages.

If lingua is not installed (slim image), a crude stop-word scorer for DE/FR/IT/EN
keeps the pipeline working with lower recall.
"""

from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass

log = logging.getLogger(__name__)

WORD_RE = re.compile(r"[^\W\d_]+(?:[-'’][^\W\d_]+)*", re.UNICODE)

# Language names written in their own language (language switchers, technique H58).
ENDONYMS = {
    "deutsch": "de", "français": "fr", "francais": "fr", "italiano": "it", "english": "en", "rumantsch": "rm",
    "romontsch": "rm", "rumantsch grischun": "rm", "español": "es", "espanol": "es", "português": "pt",
    "portugues": "pt", "nederlands": "nl", "shqip": "sq", "türkçe": "tr", "turkce": "tr", "hrvatski": "hr",
    "srpski": "sr", "српски": "sr", "bosanski": "bs", "svenska": "sv", "polski": "pl", "українська": "uk",
    "русский": "ru", "العربية": "ar", "tiếng việt": "vi", "தமிழ்": "ta", "ትግርኛ": "ti", "فارسی": "fa",
    "magyar": "hu", "čeština": "cs", "slovenčina": "sk", "slovenščina": "sl", "română": "ro", "български": "bg",
    "ελληνικά": "el", "dansk": "da", "norsk": "no", "suomi": "fi", "lëtzebuergesch": "lb", "kurdî": "ku",
    "soomaali": "so", "中文": "zh", "日本語": "ja", "한국어": "ko", "eesti": "et", "latviešu": "lv",
    "lietuvių": "lt", "македонски": "mk", "català": "ca", "galego": "gl", "euskara": "eu",
}

ISO_639_1 = set(
    "aa ab ae af ak am an ar as av ay az ba be bg bh bi bm bn bo br bs ca ce ch co cr cs cu cv cy da de dv dz "
    "ee el en eo es et eu fa ff fi fj fo fr fy ga gd gl gn gu gv ha he hi ho hr ht hu hy hz ia id ie ig ii ik "
    "io is it iu ja jv ka kg ki kj kk kl km kn ko kr ks ku kv kw ky la lb lg li ln lo lt lu lv mg mh mi mk ml "
    "mn mr ms mt my na nb nd ne ng nl nn no nr nv ny oc oj om or os pa pi pl ps pt qu rm rn ro ru rw sa sc sd "
    "se sg si sk sl sm sn so sq sr ss st su sv sw ta te tg th ti tk tl tn to tr ts tt tw ty ug uk ur uz ve vi "
    "vo wa wo xh yi yo za zh zu".split()
)
_LANG_TAG = re.compile(r"^([a-z]{2})(?:[-_][a-z]{2})?$")
_NAME_SEP = re.compile(r"[|·•/()\[\]:.,–—-]+")


def endonym(text: str) -> str | None:
    key = " ".join(re.sub(r"[|·•/()\[\]:.,]+", " ", text.lower()).split())
    return ENDONYMS.get(key)


def language_named(text: str) -> str | None:
    """The language a short label names: an ISO 639-1 code ("FR", "de-CH"), an
    endonym ("Italiano") or both ("EN – English"). None for anything else."""
    low = " ".join((text or "").lower().split())
    m = _LANG_TAG.match(low)
    if m and m.group(1) in ISO_639_1:
        return m.group(1)
    whole = endonym(low)
    if whole:
        return whole
    codes = set()
    for token in _NAME_SEP.sub(" ", low).split():
        code = token if token in ISO_639_1 else ENDONYMS.get(token)
        if code is None:
            return None
        codes.add(code)
    return codes.pop() if len(codes) == 1 else None


@dataclass(frozen=True)
class Detection:
    lang: str  # ISO 639-1 code, e.g. "fr"
    confidence: float  # 0..1 (lingua's relative confidence)
    runner_up: str | None = None


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    text: str
    lang: str
    confidence: float


def word_count(text: str) -> int:
    return len(WORD_RE.findall(text))


class _LinguaBackend:
    def __init__(self, codes: tuple[str, ...]):
        from lingua import IsoCode639_1, LanguageDetectorBuilder, Language

        langs = []
        for code in codes:
            try:
                langs.append(Language.from_iso_code_639_1(getattr(IsoCode639_1, code.upper())))
            except AttributeError:
                log.warning("lingua does not know language %r; ignored", code)
        if len(langs) < 2:
            raise ValueError("need at least two languages")
        self._d = LanguageDetectorBuilder.from_languages(*langs).with_preloaded_language_models().build()

    @staticmethod
    def _code(language) -> str:
        return language.iso_code_639_1.name.lower()

    def detect(self, text: str) -> Detection | None:
        values = self._d.compute_language_confidence_values(text)
        if not values or values[0].value <= 0:
            return None
        runner = self._code(values[1].language) if len(values) > 1 else None
        return Detection(self._code(values[0].language), float(values[0].value), runner)

    def confidence(self, text: str, code: str) -> float:
        from lingua import IsoCode639_1, Language

        try:
            lang = Language.from_iso_code_639_1(getattr(IsoCode639_1, code.upper()))
        except AttributeError:
            return 0.0
        return float(self._d.compute_language_confidence(text, lang))

    def spans(self, text: str) -> list[Span]:
        out = []
        for r in self._d.detect_multiple_languages_of(text):
            chunk = text[r.start_index : r.end_index]
            code = self._code(r.language)
            out.append(Span(r.start_index, r.end_index, chunk, code, self.confidence(chunk, code)))
        return out


class _StopwordBackend:
    """Fallback only. Good enough to flag whole sentences, useless for short spans."""

    STOP = {
        "de": "der die das und ist nicht mit sie ich zu den von auf für ein eine im dem des sich auch wir bei oder wenn über ihre unsere".split(),
        "fr": "le la les et est pas avec vous je de des du un une pour dans sur au aux nous ce cette qui que ou leur votre".split(),
        "it": "il lo la gli le e è non con lei io di del della un una per in su al alla noi che questo questa chi o sono".split(),
        "en": "the and is not with you i to of on for a an in at we this that who or are be your our from".split(),
    }

    def detect(self, text: str) -> Detection | None:
        words = [w.lower() for w in WORD_RE.findall(text)]
        if not words:
            return None
        scores = {k: sum(w in set(v) for w in words) for k, v in self.STOP.items()}
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])
        total = sum(scores.values())
        if total == 0:
            return None
        return Detection(ranked[0][0], ranked[0][1] / total, ranked[1][0])

    def confidence(self, text: str, code: str) -> float:
        d = self.detect(text)
        return d.confidence if d and d.lang == code else 0.0

    def spans(self, text: str) -> list[Span]:
        out, pos = [], 0
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            start = text.find(sentence, pos)
            pos = start + len(sentence)
            d = self.detect(sentence)
            if d:
                out.append(Span(start, pos, sentence, d.lang, d.confidence))
        return out


class LanguageDetector:
    def __init__(self, codes: tuple[str, ...]):
        try:
            self._b = _LinguaBackend(codes)
            self.backend = "lingua"
        except Exception as exc:  # ImportError or a broken wheel
            log.warning("lingua unavailable (%s); using the stop-word fallback", exc)
            self._b = _StopwordBackend()
            self.backend = "stopwords"

    def detect(self, text: str) -> Detection | None:
        text = text.strip()
        return self._b.detect(text) if text else None

    def confidence(self, text: str, code: str) -> float:
        return self._b.confidence(text, code) if text.strip() else 0.0

    def spans(self, text: str) -> list[Span]:
        return self._b.spans(text) if text.strip() else []


_lock = threading.Lock()
_cache: dict[tuple[str, ...], LanguageDetector] = {}


def get_detector(codes: tuple[str, ...]) -> LanguageDetector:
    key = tuple(sorted(set(codes)))
    with _lock:
        if key not in _cache:
            _cache[key] = LanguageDetector(key)
        return _cache[key]
