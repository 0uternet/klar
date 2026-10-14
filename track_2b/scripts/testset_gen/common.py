"""Shared API for the Klar. evaluation-set generator (stdlib only).

Every criterion module ``c_<criterion with _>.py`` (e.g. ``c_2_4_4.py``) exposes::

    CRITERION = "2.4.4"
    def build(rng: random.Random) -> list[Case]: ...

``build`` must be deterministic given ``rng`` (never use ``random`` module-level
functions, ``time``, ``uuid``, ``hash()`` of str, or set iteration order).

Labels are assigned BY CONSTRUCTION, following ``data/testset/PROTOCOL.md``.
Construction rules that every case must respect (checked in part by the driver):

1. One case = one self-contained page (or a mini site for site-level criteria).
2. Exactly one element under test (``target``), or ``target=None`` for page-level
   criteria. Every OTHER candidate for the same criterion on the page must clearly
   pass, so the page-level outcome equals the case's ``expected``.
3. No label leakage: ids, classes, data-* values, file names, titles and comments
   must not reveal the verdict (no "fail", "pass", "trap", "bad", "good",
   "correct", "wrong", "expected", "cantTell", "issue"). No HTML comments at all.
4. All non-void elements are explicitly closed (the validator parses strictly).
5. Images are generated SVGs registered through :func:`asset` and referenced with
   the returned path (a placeholder the driver rewrites to a relative URL).
6. No external resources (no http(s) URLs in src/href of resources). Links to
   other sites may use ``https://….example`` hosts only.
"""
from __future__ import annotations

import html as _html
import math
import random
from dataclasses import dataclass, field

OUTCOMES = ("failed", "passed", "cantTell", "inapplicable")
LANGS = ("de", "fr", "it", "en", "rm")   # rm = Romansh (Rumantsch Grischun), add-on cases only

CRITERIA = {
    # code: (name, level)
    "1.1.1": ("Non-text Content", "A"),
    "1.3.1": ("Info and Relationships", "A"),
    "1.3.2": ("Meaningful Sequence", "A"),
    "1.3.3": ("Sensory Characteristics", "A"),
    "1.3.5": ("Identify Input Purpose", "AA"),
    "1.4.1": ("Use of Color", "A"),
    "1.4.3": ("Contrast (Minimum)", "AA"),
    "1.4.5": ("Images of Text", "AA"),
    "1.4.11": ("Non-text Contrast", "AA"),
    "2.2.2": ("Pause, Stop, Hide", "A"),
    "2.4.2": ("Page Titled", "A"),
    "2.4.3": ("Focus Order", "A"),
    "2.4.4": ("Link Purpose (In Context)", "A"),
    "2.4.5": ("Multiple Ways", "AA"),
    "2.4.6": ("Headings and Labels", "AA"),
    "2.5.3": ("Label in Name", "A"),
    "3.1.1": ("Language of Page", "A"),
    "3.1.2": ("Language of Parts", "AA"),
    "3.2.2": ("On Input", "A"),
    "3.2.3": ("Consistent Navigation", "AA"),
    "3.2.4": ("Consistent Identification", "AA"),
    "3.3.1": ("Error Identification", "A"),
    "3.3.2": ("Labels or Instructions", "A"),
    "3.3.3": ("Error Suggestion", "AA"),
    "3.3.4": ("Error Prevention (Legal, Financial, Data)", "AA"),
    "4.1.2": ("Name, Role, Value", "A"),
}

ASSET_PLACEHOLDER = "@@ASSETS@@"


@dataclass
class Case:
    """One labelled test case.

    criterion : "2.4.4"
    lang      : primary language of the page content: "de" | "fr" | "it" | "en"
    expected  : "failed" | "passed" | "cantTell" | "inapplicable"
    html      : full HTML document (single-page case), or None if ``pages`` is used
    pages     : multi-page mini site {"index.html": html, "kontakt.html": html, ...};
                the entry page MUST be "index.html"; sub-folders allowed ("a/b.html")
    target    : CSS selector of the element under test (must match exactly ONE element
                in the entry page), or None for page-/site-level criteria
    rule      : PROTOCOL decision-rule id, e.g. "2.4.4/C1"
    notes     : one-line rationale (English), e.g. "Only the preceding card heading
                disambiguates 'Mehr'; heading is not programmatic context."
    trap      : True if the case is a look-alike that must NOT be flagged because an
                exception or a legitimate pattern applies (proper name, logotype, ...)
    alt_expected : outcome under the strict ACT reading where PROTOCOL deliberately
                differs (e.g. heading-only link context: expected cantTell,
                alt_expected failed); None otherwise
    difficulty : "easy" | "medium" | "hard"
    template  : scenario family (content source) shared by near-identical cases; cases with the
                same template always land in the same split (group split). If None, the driver
                groups cases automatically by near-duplicate text (Jaccard >= 0.6).
    surface   : key surface forms of the case (e.g. the exception words of a 3.1.2 trap); dev and
                test must not share them and they must not occur in src/klar (check_leakage.py)
    tags      : free subset labels, e.g. ("injection", "sr-only")
    split     : force "dev" or "test" (only for small designed subsets such as injection cases)
    """
    criterion: str
    lang: str
    expected: str
    html: str | None = None
    pages: dict | None = None
    target: str | None = None
    rule: str = ""
    notes: str = ""
    trap: bool = False
    alt_expected: str | None = None
    difficulty: str = "medium"
    template: str | None = None
    surface: tuple = ()
    tags: tuple = ()
    split: str | None = None

    def __post_init__(self):
        assert self.expected in OUTCOMES, self.expected
        assert self.lang in LANGS, self.lang
        assert (self.html is None) != (self.pages is None), "give html XOR pages"
        if self.pages is not None:
            assert "index.html" in self.pages, "multi-page case needs index.html"
        assert self.difficulty in ("easy", "medium", "hard")
        if self.alt_expected is not None:
            assert self.alt_expected in OUTCOMES
        assert self.split in (None, "dev", "test")
        self.surface = tuple(self.surface)
        self.tags = tuple(self.tags)


# ---------------------------------------------------------------------------
# Escaping / small helpers
# ---------------------------------------------------------------------------

def esc(s: str) -> str:
    return _html.escape(s, quote=True)


def attrs(**kw) -> str:
    """attrs(class_="x", aria_label="y", data_k="1") -> ' class="x" aria-label="y" data-k="1"'"""
    out = []
    for k, v in kw.items():
        if v is None or v is False:
            continue
        name = k.rstrip("_").replace("_", "-")
        if v is True:
            out.append(f" {name}")
        else:
            out.append(f' {name}="{esc(str(v))}"')
    return "".join(out)


def pick(rng: random.Random, seq):
    return seq[rng.randrange(len(seq))]


def sample(rng: random.Random, seq, k):
    seq = list(seq)
    return [seq[i] for i in sorted(rng.sample(range(len(seq)), k))] if k < len(seq) else seq[:]


def shuffled(rng: random.Random, seq):
    seq = list(seq)
    rng.shuffle(seq)
    return seq


# ---------------------------------------------------------------------------
# Colour contrast (WCAG 2.x relative luminance)
# ---------------------------------------------------------------------------

def _lin(c: float) -> float:
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ---------------------------------------------------------------------------
# Fictional content pools (everything is invented; no real municipality/people)
# ---------------------------------------------------------------------------

ORGS = {
    "de": ["Gemeinde Beispielwil", "Gemeinde Beispielberg", "Stadt Mustersee", "Gemeinde Fiktal",
           "Gemeinde Ober-Beispielwil", "Schule Beispielberg", "Bibliothek Mustersee",
           "Wasserversorgung Fiktal", "Beispielwiler Verkehrsbetriebe", "Sportverein Beispielberg",
           "Museum im Kornhaus Mustersee", "Spitex Fiktal-Beispielwil"],
    "fr": ["Commune de Valfictif", "Ville de Bourg-Modèle", "Commune de Beispielwil",
           "Commune d'Exempleval", "École de Valfictif", "Bibliothèque de Bourg-Modèle",
           "Service des eaux d'Exempleval", "Transports publics de Valfictif",
           "Musée du Moulin, Bourg-Modèle", "Club sportif d'Exempleval"],
    "it": ["Comune di Esempiano", "Città di Modellina", "Comune di Valfittizia",
           "Comune di Beispielwil", "Scuola di Esempiano", "Biblioteca di Modellina",
           "Azienda acqua potabile Valfittizia", "Trasporti pubblici di Modellina",
           "Museo della Filanda, Esempiano", "Società sportiva Valfittizia"],
    "en": ["Example Valley Tourism", "Beispielwil Visitor Centre", "Lake Fictal Hostel",
           "Example Valley Hiking Association"],
}

PEOPLE = {
    "de": ["Anna Beispiel", "Reto Muster", "Corinne Probst", "Urs Exempel", "Lea Testmann", "Beat Vorlage"],
    "fr": ["Claire Exemple", "Marc Modèle", "Sophie Fictif", "Luc Témoin", "Nadia Spécimen"],
    "it": ["Lucia Esempio", "Marco Modello", "Giulia Fittizi", "Paolo Campione", "Sara Prova"],
    "en": ["Jane Sample", "Tom Example"],
}

STREETS = {   # invented; deliberately disjoint from the demo site and from 3.1.2 trap vocabulary
    "de": ["Lindenweg 14", "Obere Gasse 7", "Erlenstrasse 22", "Rosenweg 9", "Hofmattweg 3", "Sonnhalde 11"],
    "fr": ["Rue des Tilleuls 6", "Chemin du Crêt 12", "Route de la Fontaine 3", "Rue des Artisans 18", "Place de la Fontaine 1"],
    "it": ["Via ai Ronchi 5", "Strada del Bosco 8", "Via ai Grotti 2", "Contrada Mulino 4", "Via Lago 17"],
    "en": ["Lakeside Path 3", "Old Mill Lane 5"],
}

MONTHS = {
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
    "it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
}
MONTHS_SHORT = {
    "de": ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"],
    "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
    "it": ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}
WEEKDAYS = {
    "de": ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
    "fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
    "it": ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}

# Typical navigation labels per language (home, news, administration, leisure, contact)
NAV = {
    "de": ["Startseite", "Aktuelles", "Verwaltung", "Leben & Wohnen", "Freizeit", "Kontakt"],
    "fr": ["Accueil", "Actualités", "Administration", "Vie pratique", "Loisirs", "Contact"],
    "it": ["Home", "Attualità", "Amministrazione", "Vita quotidiana", "Tempo libero", "Contatti"],
    "en": ["Home", "News", "Plan your visit", "Hiking", "Accommodation", "Contact"],
}

SITE_LANG_TAG = {"de": "de-CH", "fr": "fr-CH", "it": "it-CH", "en": "en"}


# ---------------------------------------------------------------------------
# Themes (all text colours verified >= 4.5:1 by :func:`_check_themes`)
# ---------------------------------------------------------------------------

THEMES = [
    dict(name="teal", bg="#ffffff", ink="#1d2327", muted="#4f5b62", brand="#0b4f6c", brand_ink="#ffffff",
         link="#0b5394", accent="#e8f1f5", line="#c9d3d8", font="system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"),
    dict(name="forest", bg="#fbfaf6", ink="#22241f", muted="#55594f", brand="#2f5d34", brand_ink="#ffffff",
         link="#1e5a8c", accent="#eef3e8", line="#cfd6c6", font="'Segoe UI', Tahoma, Verdana, sans-serif"),
    dict(name="slate", bg="#ffffff", ink="#16181d", muted="#50555e", brand="#2b2f3a", brand_ink="#ffffff",
         link="#1f4fd8", accent="#f1f2f5", line="#d4d7de", font="Arial, Helvetica, sans-serif"),
    dict(name="wine", bg="#fffdfb", ink="#241c1c", muted="#5d5050", brand="#7a1f2b", brand_ink="#ffffff",
         link="#7a1f2b", accent="#f7eeee", line="#e0d2d2", font="Georgia, 'Times New Roman', serif"),
    dict(name="lake", bg="#f7fafc", ink="#102a43", muted="#486581", brand="#1f6f8b", brand_ink="#ffffff",
         link="#0a558c", accent="#e3eef6", line="#c5d5e4", font="Verdana, Geneva, sans-serif"),
]


def _check_themes():
    for t in THEMES:
        assert contrast(t["ink"], t["bg"]) >= 7, t["name"]
        assert contrast(t["muted"], t["bg"]) >= 4.5, t["name"]
        assert contrast(t["brand_ink"], t["brand"]) >= 4.5, t["name"]
        assert contrast(t["link"], t["bg"]) >= 4.5, t["name"]
        assert contrast(t["link"], t["accent"]) >= 4.5, t["name"]
        assert contrast(t["ink"], t["accent"]) >= 4.5, t["name"]


_check_themes()


def theme_css(t: dict) -> str:
    return (
        f"body{{margin:0;font-family:{t['font']};color:{t['ink']};background:{t['bg']};line-height:1.5}}"
        f"a{{color:{t['link']}}}"
        f".site-header{{background:{t['brand']};color:{t['brand_ink']};padding:12px 24px;display:flex;flex-wrap:wrap;gap:16px;align-items:center;justify-content:space-between}}"
        f".site-header a{{color:{t['brand_ink']}}}"
        f".site-name{{font-weight:700;font-size:1.15rem;text-decoration:none}}"
        f".site-nav ul{{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:14px}}"
        f".site-nav a{{text-decoration:none}}"
        f"main{{max-width:960px;margin:0 auto;padding:24px}}"
        f".site-footer{{border-top:1px solid {t['line']};color:{t['muted']};padding:16px 24px;font-size:.9rem}}"
        f".box{{background:{t['accent']};padding:16px;border-radius:8px}}"
        f".muted{{color:{t['muted']}}}"
        f"img{{max-width:100%;height:auto}}"
        f"label{{display:block;font-weight:600;margin-top:12px}}"
        f"input,select,textarea{{font:inherit;padding:6px 8px;border:1px solid #6b7280;border-radius:6px}}"
        f"button{{font:inherit;padding:8px 16px;border-radius:6px;border:1px solid {t['brand']};background:{t['brand']};color:{t['brand_ink']};cursor:pointer}}"
        f"table{{border-collapse:collapse}}th,td{{border:1px solid {t['line']};padding:6px 10px;text-align:left}}"
        f".cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px}}"
        f".card{{border:1px solid {t['line']};border-radius:10px;padding:12px;background:#ffffff}}"
    )


def pick_theme(rng: random.Random) -> dict:
    return pick(rng, THEMES)


# ---------------------------------------------------------------------------
# Page builders
# ---------------------------------------------------------------------------

def page(lang: str | None, title: str | None, body: str, *, head: str = "",
         theme: dict | None = None, rng: random.Random | None = None,
         css: str = "", html_attrs: str = "", body_attrs: str = "") -> str:
    """Return a full HTML5 document.

    lang  : value of <html lang> (e.g. "de-CH"); None omits the attribute
    title : <title> text; None omits the element (use only for 2.4.2 cases)
    body  : inner HTML of <body>
    head  : extra markup for <head> (scripts, meta)
    theme : a THEMES entry (default: chosen with rng, else THEMES[0])
    css   : extra CSS appended after the theme
    """
    if theme is None:
        theme = pick_theme(rng) if rng is not None else THEMES[0]
    lang_attr = f' lang="{esc(lang)}"' if lang is not None else ""
    title_el = f"<title>{esc(title)}</title>" if title is not None else ""
    return (
        "<!DOCTYPE html>\n"
        f"<html{lang_attr}{html_attrs}>\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"{title_el}\n<style>{theme_css(theme)}{css}</style>\n{head}</head>\n"
        f"<body{body_attrs}>\n{body}\n</body>\n</html>\n"
    )


def header(lang: str, org: str, nav: list[str] | None = None, *, home_href: str = "index.html",
           hrefs: list[str] | None = None, nav_label: str | None = None) -> str:
    """Site header with organisation name and a main navigation."""
    nav = nav if nav is not None else NAV[lang][:5]
    hrefs = hrefs or [_slug(x) + ".html" for x in nav]
    label = nav_label or {"de": "Hauptnavigation", "fr": "Navigation principale",
                          "it": "Navigazione principale", "en": "Main navigation"}[lang]
    items = "".join(f'<li><a href="{esc(h)}">{esc(n)}</a></li>' for n, h in zip(nav, hrefs))
    return (f'<header class="site-header"><a class="site-name" href="{esc(home_href)}">{esc(org)}</a>'
            f'<nav class="site-nav" aria-label="{esc(label)}"><ul>{items}</ul></nav></header>')


def footer(lang: str, org: str, street: str | None = None) -> str:
    street = street or STREETS[lang][0]
    contact = {"de": "Kontakt", "fr": "Contact", "it": "Contatto", "en": "Contact"}[lang]
    return (f'<footer class="site-footer"><p>{esc(org)} · {esc(street)} · '
            f'<a href="kontakt.html">{contact}</a></p></footer>')


def wrap(lang: str, org: str, main_html: str, *, nav: list[str] | None = None,
         street: str | None = None, chrome: bool = True) -> str:
    """header + <main> + footer (chrome=False returns just <main>)."""
    main = f"<main>\n{main_html}\n</main>"
    if not chrome:
        return main
    return header(lang, org, nav) + "\n" + main + "\n" + footer(lang, org, street)


def _slug(s: str) -> str:
    tr = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "é": "e", "è": "e", "à": "a", "ì": "i",
                        "ò": "o", "ù": "u", "ç": "c", "&": "", "…": "", "'": "", "ô": "o", "â": "a"})
    out = []
    for ch in s.lower().translate(tr):
        out.append(ch if ch.isalnum() else "-")
    slug = "-".join(p for p in "".join(out).split("-") if p)
    return slug or "seite"


slug = _slug


# ---------------------------------------------------------------------------
# Assets (SVG files written to generated/_assets/, deduplicated by name)
# ---------------------------------------------------------------------------

ASSETS: dict[str, str] = {}


def asset(name: str, svg: str) -> str:
    """Register an SVG asset and return the URL to use in src/href.

    ``name`` must be a neutral file name without extension (e.g. "chart-waste-2025",
    "pic-bin", "banner-concert-de"). Never encode the verdict in the name.
    The same name must always map to identical content.
    """
    assert all(c.isalnum() or c in "-_" for c in name), name
    if name in ASSETS:
        assert ASSETS[name] == svg, f"asset {name} registered twice with different content"
    ASSETS[name] = svg
    return f"{ASSET_PLACEHOLDER}/{name}.svg"


def _svg(w, h, inner, *, title=None):
    t = f"<title>{esc(title)}</title>" if title else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f"{t}{inner}</svg>")


PALETTE = ["#1f6f8b", "#e07a2e", "#3c8d4f", "#8e5ea2", "#c2453b", "#d4a017", "#4b6584", "#2d9cdb"]


def bar_chart(title: str, labels: list[str], values: list[float], *, unit: str = "",
              color: str = "#1f6f8b", w: int = 640, h: int = 360, show_values: bool = True,
              colors: list[str] | None = None, font: str = "Arial, sans-serif") -> str:
    """Vertical bar chart with axis, grid, category labels and value labels."""
    left, right, top, bottom = 56, 16, 48, 48
    pw, ph = w - left - right, h - top - bottom
    vmax = max(values) if values else 1
    step = _nice_step(vmax)
    ymax = step * math.ceil(vmax / step)
    parts = [f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
             f'<text x="{left}" y="28" font-family="{font}" font-size="18" font-weight="700" fill="#1d2327">{esc(title)}</text>']
    n = int(round(ymax / step))
    for i in range(n + 1):
        y = top + ph - ph * i / n
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{w - right}" y2="{y:.1f}" stroke="#d9dee2" stroke-width="1"/>')
        parts.append(f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" font-family="{font}" font-size="12" fill="#3d464d">{_fmt(step * i)}</text>')
    bw = pw / max(1, len(values))
    for i, (lab, v) in enumerate(zip(labels, values)):
        bh = ph * v / ymax if ymax else 0
        x = left + i * bw + bw * 0.15
        y = top + ph - bh
        c = colors[i % len(colors)] if colors else color
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw * 0.7:.1f}" height="{bh:.1f}" fill="{c}"/>')
        parts.append(f'<text x="{x + bw * 0.35:.1f}" y="{top + ph + 18}" text-anchor="middle" font-family="{font}" font-size="12" fill="#3d464d">{esc(lab)}</text>')
        if show_values:
            parts.append(f'<text x="{x + bw * 0.35:.1f}" y="{y - 6:.1f}" text-anchor="middle" font-family="{font}" font-size="11" fill="#1d2327">{_fmt(v)}</text>')
    if unit:
        parts.append(f'<text x="{left}" y="{h - 10}" font-family="{font}" font-size="12" fill="#3d464d">{esc(unit)}</text>')
    parts.append(f'<line x1="{left}" y1="{top + ph}" x2="{w - right}" y2="{top + ph}" stroke="#3d464d" stroke-width="1.5"/>')
    return _svg(w, h, "".join(parts))


def line_chart(title: str, labels: list[str], series: dict[str, list[float]], *, unit: str = "",
               w: int = 640, h: int = 360, colors: list[str] | None = None,
               legend: bool = True, markers: bool = True, font: str = "Arial, sans-serif") -> str:
    """Multi-series line chart. ``series`` = {"name": [values...]}; legend by colour + name."""
    colors = colors or PALETTE
    left, right, top, bottom = 56, 16, 56, 56
    pw, ph = w - left - right, h - top - bottom
    vmax = max(max(v) for v in series.values())
    step = _nice_step(vmax)
    ymax = step * math.ceil(vmax / step)
    parts = [f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
             f'<text x="{left}" y="26" font-family="{font}" font-size="18" font-weight="700" fill="#1d2327">{esc(title)}</text>']
    n = int(round(ymax / step))
    for i in range(n + 1):
        y = top + ph - ph * i / n
        parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{w - right}" y2="{y:.1f}" stroke="#d9dee2"/>')
        parts.append(f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" font-family="{font}" font-size="12" fill="#3d464d">{_fmt(step * i)}</text>')
    k = len(labels)
    for i, lab in enumerate(labels):
        x = left + pw * (i / max(1, k - 1))
        parts.append(f'<text x="{x:.1f}" y="{top + ph + 18}" text-anchor="middle" font-family="{font}" font-size="12" fill="#3d464d">{esc(lab)}</text>')
    lx = left
    for si, (name, vals) in enumerate(series.items()):
        c = colors[si % len(colors)]
        pts = " ".join(f"{left + pw * (i / max(1, k - 1)):.1f},{top + ph - ph * v / ymax:.1f}" for i, v in enumerate(vals))
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="2.5"/>')
        if markers:
            for i, v in enumerate(vals):
                parts.append(f'<circle cx="{left + pw * (i / max(1, k - 1)):.1f}" cy="{top + ph - ph * v / ymax:.1f}" r="3" fill="{c}"/>')
        if legend:
            parts.append(f'<rect x="{lx}" y="{h - 22}" width="14" height="4" fill="{c}"/>'
                         f'<text x="{lx + 20}" y="{h - 16}" font-family="{font}" font-size="12" fill="#1d2327">{esc(name)}</text>')
            lx += 30 + 7 * len(name)
    if unit:
        parts.append(f'<text x="{w - right}" y="{top - 10}" text-anchor="end" font-family="{font}" font-size="12" fill="#3d464d">{esc(unit)}</text>')
    return _svg(w, h, "".join(parts))


def pie_chart(title: str, labels: list[str], values: list[float], *, w: int = 520, h: int = 320,
              colors: list[str] | None = None, legend_values: bool = True,
              font: str = "Arial, sans-serif") -> str:
    colors = colors or PALETTE
    total = sum(values)
    cx, cy, r = 150, 175, 110
    parts = [f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
             f'<text x="20" y="30" font-family="{font}" font-size="18" font-weight="700" fill="#1d2327">{esc(title)}</text>']
    a0 = -math.pi / 2
    for i, v in enumerate(values):
        a1 = a0 + 2 * math.pi * v / total
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        large = 1 if a1 - a0 > math.pi else 0
        parts.append(f'<path d="M{cx},{cy} L{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f} Z" fill="{colors[i % len(colors)]}" stroke="#ffffff" stroke-width="2"/>')
        a0 = a1
    for i, (lab, v) in enumerate(zip(labels, values)):
        y = 80 + i * 26
        pct = 100 * v / total
        txt = f"{lab} – {pct:.0f} %" if legend_values else lab
        parts.append(f'<rect x="290" y="{y - 12}" width="14" height="14" fill="{colors[i % len(colors)]}"/>'
                     f'<text x="312" y="{y}" font-family="{font}" font-size="13" fill="#1d2327">{esc(txt)}</text>')
    return _svg(w, h, "".join(parts))


def _nice_step(vmax: float) -> float:
    if vmax <= 0:
        return 1
    raw = vmax / 5
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


def _fmt(v: float) -> str:
    if abs(v - round(v)) < 1e-9:
        s = f"{int(round(v)):,}".replace(",", " ")
        return s
    return f"{v:.1f}"


# Pictograms: 24x24 stroke icons (own drawings)
ICONS = {
    "bin": '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6"/>',
    "bus": '<rect x="4" y="3" width="16" height="14" rx="2"/><path d="M4 11h16M8 17v3M16 17v3"/><circle cx="8" cy="14" r="1"/><circle cx="16" cy="14" r="1"/>',
    "bike": '<circle cx="6" cy="16" r="4"/><circle cx="18" cy="16" r="4"/><path d="M6 16l4-8h5l3 8M10 8l4 8M13 5h3"/>',
    "phone": '<path d="M5 3h4l2 5-3 2a12 12 0 0 0 6 6l2-3 5 2v4a2 2 0 0 1-2 2A17 17 0 0 1 3 5a2 2 0 0 1 2-2z"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
    "warning": '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.5"/>',
    "home": '<path d="M3 11l9-8 9 8M5 9v12h14V9"/><path d="M10 21v-6h4v6"/>',
    "search": '<circle cx="10" cy="10" r="6"/><path d="M15 15l6 6"/>',
    "printer": '<path d="M7 9V3h10v6M7 17H4v-8h16v8h-3"/><rect x="7" y="14" width="10" height="7"/>',
    "download": '<path d="M12 3v12M7 10l5 5 5-5M4 21h16"/>',
    "leaf": '<path d="M4 20c0-9 6-15 16-16-1 10-7 16-16 16zM4 20l8-8"/>',
    "drop": '<path d="M12 3c4 6 6 9 6 12a6 6 0 0 1-12 0c0-3 2-6 6-12z"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/>',
    "pin": '<path d="M12 21s7-6 7-12a7 7 0 0 0-14 0c0 6 7 12 7 12z"/><circle cx="12" cy="9" r="2.5"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-7 8-7s8 3 8 7"/>',
    "arrow-right": '<path d="M4 12h16M14 6l6 6-6 6"/>',
    "arrow-left": '<path d="M20 12H4M10 6l-6 6 6 6"/>',
    "chevron-right": '<path d="M9 5l7 7-7 7"/>',
    "chevron-left": '<path d="M15 5l-7 7 7 7"/>',
    "close": '<path d="M5 5l14 14M19 5L5 19"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "play": '<path d="M7 4l13 8-13 8z"/>',
    "pause": '<path d="M8 4v16M16 4v16"/>',
    "star": '<path d="M12 3l2.8 5.8 6.2.9-4.5 4.4 1 6.2L12 17.4 6.5 20.3l1-6.2L3 9.7l6.2-.9z"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "minus": '<path d="M5 12h14"/>',
    "check": '<path d="M4 12l5 5 11-11"/>',
    "doc": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>',
    "share": '<circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="M8.2 11l7.6-4M8.2 13l7.6 4"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>',
    "lock": '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
    "tree": '<path d="M12 3l6 9h-3l4 6H5l4-6H6z"/><path d="M12 18v3"/>',
}


def pictogram(name: str, *, color: str = "#1d2327", size: int = 48, bg: str | None = None,
              stroke: float = 2) -> str:
    inner = ICONS[name]
    bgrect = f'<rect width="24" height="24" rx="5" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24">'
            f'{bgrect}<g fill="none" stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">{inner}</g></svg>')


def banner(lines: list[str], *, bg: str = "#0b4f6c", fg: str = "#ffffff", w: int = 800, h: int = 220,
           accent: str | None = "#e07a2e", sizes: list[int] | None = None,
           font: str = "Arial, sans-serif", bg2: str | None = None) -> str:
    """Banner with text drawn into the image (image of text)."""
    sizes = sizes or [44] + [24] * (len(lines) - 1)
    grad = ""
    fill = bg
    if bg2:
        grad = (f'<defs><linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="{bg}"/>'
                f'<stop offset="1" stop-color="{bg2}"/></linearGradient></defs>')
        fill = "url(#g)"
    parts = [grad, f'<rect width="{w}" height="{h}" fill="{fill}"/>']
    if accent:
        parts.append(f'<circle cx="{w - 90}" cy="{h // 2}" r="{h // 2 - 20}" fill="{accent}" opacity="0.85"/>')
    y = 30
    for line, s in zip(lines, sizes):
        y += s + 10
        parts.append(f'<text x="40" y="{y}" font-family="{font}" font-size="{s}" font-weight="{700 if s >= 30 else 400}" fill="{fg}">{esc(line)}</text>')
    return _svg(w, h, "".join(parts))


def ornament(kind: str = "dots", *, color: str = "#c9d3d8", w: int = 600, h: int = 24) -> str:
    """Purely decorative divider ("dots", "wave", "line", "leaves")."""
    if kind == "dots":
        inner = "".join(f'<circle cx="{x}" cy="{h // 2}" r="3" fill="{color}"/>' for x in range(12, w, 24))
    elif kind == "wave":
        d = "M0 12 " + " ".join(f"Q{x + 15} {2 if (x // 30) % 2 == 0 else 22} {x + 30} 12" for x in range(0, w, 30))
        inner = f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2"/>'
    elif kind == "leaves":
        inner = "".join(f'<path d="M{x} 18 q6 -14 14 -12 q-2 10 -14 12z" fill="{color}"/>' for x in range(10, w, 40))
    else:
        inner = f'<line x1="0" y1="{h // 2}" x2="{w}" y2="{h // 2}" stroke="{color}" stroke-width="2"/>'
    return _svg(w, h, inner)


SCENES = ("townhall", "lake", "forest", "bike", "bus", "market", "school", "mountain", "library",
          "playground", "recycling", "concert", "snow", "bridge")


def scene(kind: str, *, w: int = 480, h: int = 300, seed: int = 0) -> str:
    """Flat illustration standing in for a photo (no text inside)."""
    rng = random.Random(f"scene-{kind}-{seed}")
    sky = pick(rng, ["#bfe3f2", "#cde8f6", "#f6dcc4", "#d7e9d2", "#e4ddf2"])
    ground = pick(rng, ["#7fb069", "#8fbc8f", "#a3c585", "#6a994e"])
    p = [f'<rect width="{w}" height="{h}" fill="{sky}"/>',
         f'<circle cx="{rng.randint(60, w - 60)}" cy="{rng.randint(40, 80)}" r="26" fill="#ffd166"/>',
         f'<rect y="{h * 0.7:.0f}" width="{w}" height="{h * 0.3:.0f}" fill="{ground}"/>']
    if kind in ("mountain", "snow", "lake", "bridge"):
        p.append(f'<path d="M0 {h * .7:.0f} L{w * .25:.0f} {h * .25:.0f} L{w * .45:.0f} {h * .55:.0f} L{w * .65:.0f} {h * .2:.0f} L{w} {h * .7:.0f}Z" fill="#7d8597"/>')
        p.append(f'<path d="M{w * .58:.0f} {h * .3:.0f} L{w * .65:.0f} {h * .2:.0f} L{w * .72:.0f} {h * .3:.0f}Z" fill="#ffffff"/>')
    if kind in ("lake", "bridge"):
        p.append(f'<rect y="{h * .72:.0f}" width="{w}" height="{h * .18:.0f}" fill="#4d9de0" opacity="0.85"/>')
    if kind == "bridge":
        p.append(f'<path d="M40 {h * .72:.0f} Q{w / 2:.0f} {h * .45:.0f} {w - 40} {h * .72:.0f}" fill="none" stroke="#5c4033" stroke-width="10"/>')
    if kind == "snow":
        p.append(f'<rect y="{h * .7:.0f}" width="{w}" height="{h * .3:.0f}" fill="#f4f7fb"/>')
        p += [f'<circle cx="{rng.randint(0, w)}" cy="{rng.randint(0, int(h * .7))}" r="3" fill="#ffffff"/>' for _ in range(25)]
    if kind in ("townhall", "school", "library"):
        bx, bw_, bh = w * .3, w * .4, h * .42
        col = {"townhall": "#e9c46a", "school": "#f4a261", "library": "#b5838d"}[kind]
        p.append(f'<rect x="{bx:.0f}" y="{h * .7 - bh:.0f}" width="{bw_:.0f}" height="{bh:.0f}" fill="{col}"/>')
        p.append(f'<path d="M{bx - 10:.0f} {h * .7 - bh:.0f} L{w / 2:.0f} {h * .7 - bh - 50:.0f} L{bx + bw_ + 10:.0f} {h * .7 - bh:.0f}Z" fill="#9c4f3c"/>')
        for i in range(4):
            p.append(f'<rect x="{bx + 14 + i * bw_ / 4:.0f}" y="{h * .7 - bh + 20:.0f}" width="{bw_ / 8:.0f}" height="26" fill="#ffffff" opacity="0.8"/>')
        p.append(f'<rect x="{w / 2 - 14:.0f}" y="{h * .7 - 48:.0f}" width="28" height="48" fill="#6d4c41"/>')
        if kind == "townhall":
            p.append(f'<rect x="{w / 2 - 12:.0f}" y="{h * .7 - bh - 95:.0f}" width="24" height="50" fill="#e9c46a"/>'
                     f'<circle cx="{w / 2:.0f}" cy="{h * .7 - bh - 75:.0f}" r="8" fill="#ffffff"/>')
    if kind in ("forest", "playground", "concert", "market"):
        for i in range(rng.randint(4, 8)):
            x = rng.randint(10, w - 30)
            p.append(f'<path d="M{x} {h * .72:.0f} l18 -60 l18 60z" fill="{pick(rng, ["#2d6a4f", "#40916c", "#1b4332"])}"/>')
    if kind == "bike":
        p.append(f'<g fill="none" stroke="#264653" stroke-width="6"><circle cx="{w * .35:.0f}" cy="{h * .75:.0f}" r="40"/>'
                 f'<circle cx="{w * .65:.0f}" cy="{h * .75:.0f}" r="40"/><path d="M{w * .35:.0f} {h * .75:.0f} L{w * .45:.0f} {h * .55:.0f} L{w * .6:.0f} {h * .55:.0f} L{w * .65:.0f} {h * .75:.0f} M{w * .45:.0f} {h * .55:.0f} L{w * .5:.0f} {h * .75:.0f}"/></g>')
    if kind == "bus":
        p.append(f'<rect x="{w * .2:.0f}" y="{h * .42:.0f}" width="{w * .6:.0f}" height="{h * .28:.0f}" rx="16" fill="#e63946"/>')
        for i in range(5):
            p.append(f'<rect x="{w * .23 + i * w * .11:.0f}" y="{h * .46:.0f}" width="{w * .08:.0f}" height="{h * .1:.0f}" fill="#f1faee"/>')
        p.append(f'<circle cx="{w * .3:.0f}" cy="{h * .71:.0f}" r="16" fill="#1d3557"/><circle cx="{w * .7:.0f}" cy="{h * .71:.0f}" r="16" fill="#1d3557"/>')
    if kind == "market":
        for i in range(3):
            x = w * .12 + i * w * .28
            p.append(f'<rect x="{x:.0f}" y="{h * .5:.0f}" width="{w * .22:.0f}" height="{h * .2:.0f}" fill="#f4a261"/>'
                     f'<path d="M{x - 6:.0f} {h * .5:.0f} h{w * .22 + 12:.0f} l-12 -24 h{-(w * .22 - 12):.0f}z" fill="{pick(rng, ["#e76f51", "#2a9d8f", "#e9c46a"])}"/>')
    if kind == "recycling":
        for i, c in enumerate(["#2a9d8f", "#e9c46a", "#264653", "#e76f51"]):
            x = w * .15 + i * w * .19
            p.append(f'<rect x="{x:.0f}" y="{h * .45:.0f}" width="{w * .14:.0f}" height="{h * .27:.0f}" rx="6" fill="{c}"/>')
    if kind == "concert":
        p.append(f'<rect x="{w * .25:.0f}" y="{h * .38:.0f}" width="{w * .5:.0f}" height="{h * .32:.0f}" fill="#3d405b"/>'
                 f'<path d="M{w * .2:.0f} {h * .38:.0f} h{w * .6:.0f} l-20 -30 h{-(w * .6 - 40):.0f}z" fill="#81b29a"/>')
    if kind == "playground":
        p.append(f'<path d="M{w * .3:.0f} {h * .72:.0f} L{w * .4:.0f} {h * .35:.0f} L{w * .5:.0f} {h * .72:.0f}" fill="none" stroke="#e76f51" stroke-width="8"/>'
                 f'<path d="M{w * .5:.0f} {h * .45:.0f} L{w * .75:.0f} {h * .72:.0f}" stroke="#2a9d8f" stroke-width="10"/>')
    return _svg(w, h, "".join(p))
