"""3.1.2 candidate extraction, from the first live run on the demo: separated lines,
number-heavy text, span-boundary noise, page-language mismatch, contact lines.
All strings are fresh (fictional town "Rebenau"), never copied from data/."""

import pytest

from klar.capture.page import CapturedPage
from klar.checks.c_3_1_2 import LanguageOfParts, askable, contact_line, language_bearing, trim_span
from klar.config import Settings


def _page(texts, page_lang="fr", **extra):
    passages = []
    for i, t in enumerate(texts):
        passages.append({"selector": f"p.n{i}", "tag": "p", "html": f"<p>{t}</p>", "text": t, "lang": page_lang,
                         "own_lang": None, "container_selector": f"p.n{i}", "container_text": t.replace("\n", " "),
                         "is_container": True, "quoted": [], **extra})
    return CapturedPage.from_elements(lang=page_lang, passages=passages)


def _kinds(texts, page_lang="fr"):
    check = LanguageOfParts("en", Settings())
    return [c.extra["kind"] for c in check.candidates(_page(texts, page_lang))]


# 1. line boundaries ---------------------------------------------------------------------------

@pytest.mark.browser
def test_passages_keep_line_boundaries(render_html):
    page = render_html("""<html lang="fr"><body>
      <address>Weinbergstrasse 7<br>7777 Rebenau<br>Téléphone 021 555 44 33</address>
      <ul class="days"><li style="display:inline">Lu 08.00–11.30</li><li style="display:inline">Ma 13.30–17.00</li></ul>
      <p><span style="display:inline-block">Bibliothèque</span><span style="display:inline-block">Ludothèque</span></p>
    </body></html>""")
    texts = {p["text"] for p in page.passages}
    assert "Weinbergstrasse 7\n7777 Rebenau\nTéléphone 021 555 44 33" in texts
    assert "Lu 08.00–11.30\nMa 13.30–17.00" in texts
    assert "Bibliothèque\nLudothèque" in texts


# 2. number- and abbreviation-heavy text -----------------------------------------------------------

@pytest.mark.parametrize("text, ok", [
    ("Mo 08.00–11.30 Uhr", False), ("Lu–Ve 08.00–11.30", False), ("12.– pro Stück", False),
    ("Gli sportelli restano chiusi il lunedì", True), ("Die Abteilung hat neue Öffnungszeiten ab 2027", True),
])
def test_language_bearing(text, ok):
    assert language_bearing(text) is ok


def test_opening_hours_are_never_asked():
    """Lines like "Mo 08.00–11.30 Uhr" fooled the detector on every German page."""
    assert _kinds(["Mo 08.00–11.30 Uhr\nDi 13.30–17.00 Uhr\nFr 08.00–11.30 Uhr"], page_lang="de") == []
    assert _kinds(["Lu 08.00–11.30\nMa 13.30–17.00"], page_lang="de") == []


# 3. span boundaries ------------------------------------------------------------------------------

@pytest.mark.parametrize("span, declared, expected", [
    ("Rebenauer Herbstfest am", "de", "Rebenauer Herbstfest"),
    ("en Weinbergstrasse", "fr", "Weinbergstrasse"),
    ("Sentiero del lago e", "it", "Sentiero del lago"),
    ("Cognome *", "it", "Cognome"),
    ("(la vieille ville)", "de", "la vieille ville"),
])
def test_trim_span(span, declared, expected):
    assert trim_span(span, declared) == expected


def test_single_capitalised_token_is_not_asked():
    assert not askable("Rebenau") and not askable(trim_span("Rebenau en", "fr"))
    assert askable("la vieille ville de Rebenau")


# 4. page language ≠ declared language --------------------------------------------------------

def test_page_in_another_language_defers_to_3_1_1():
    italian = [
        "Gli sportelli comunali restano chiusi durante le festività natalizie.",
        "Per informazioni potete chiamare la cancelleria oppure scrivere una e-mail.",
        "Il servizio di raccolta dei rifiuti verdi riprende a marzo con nuovi orari.",
        "Le iscrizioni ai corsi estivi per bambini si aprono il primo di maggio.",
        "Vai al contenuto", "Pagina iniziale", "Avvisi", "Tutti gli orari",
    ]
    check = LanguageOfParts("en", Settings())
    page = _page(italian, page_lang="de")
    page.html = '<html lang="de"><body><main>' + "".join(f"<p>{t}</p>" for t in italian) + "</main></body></html>"
    cands = check.candidates(page)
    assert [c.extra["kind"] for c in cands] == ["page_language_mismatch"]  # one note, no per-part questions
    f = check.decide(cands[0])
    assert f.outcome == "cantTell" and f.reason_code == "page_language_mismatch" and "3.1.1" in f.explanation
    assert f.excerpt in cands[0].text


# 5. address and contact lines -------------------------------------------------------------------

@pytest.mark.parametrize("line, ok", [
    ("Weinbergstrasse 7", True), ("7777 Rebenau", True), ("Téléphone 021 555 44 33", True),
    ("Telefono: 091 555 66 77", True), ("kanzlei@rebenau.example", True),
    ("Weinbergstrasse 7 · 7777 Rebenau · Tél. 021 555 44 33", True),
    ("Amministrazione comunale di Rebenau", False), ("Les guichets sont fermés.", False),
])
def test_contact_line(line, ok):
    assert contact_line(line) is ok


def test_foreign_address_block_passes_in_code():
    check = LanguageOfParts("en", Settings())
    cands = check.candidates(_page(["Weinbergstrasse 7\n7777 Rebenau\nTelefon 021 555 44 33"], page_lang="fr"))
    assert [c.extra["kind"] for c in cands] == ["contact_line"]
    f = check.decide(cands[0])
    assert f.outcome == "passed" and f.source == "heuristic" and f.reason_code == "contact_line"


def test_contact_lines_are_set_aside_before_detection():
    """An institution name above an address: only the name may be asked about."""
    kinds = _kinds(["Kantonales Amt für Wald und Landschaft\nWeinbergstrasse 7\n7777 Rebenau"], page_lang="fr")
    assert kinds in ([], ["ask"])
    check = LanguageOfParts("en", Settings())
    for c in check.candidates(_page(["Kantonales Amt für Wald und Landschaft\nWeinbergstrasse 7\n7777 Rebenau"])):
        assert "Weinbergstrasse" not in c.extra["span"]
