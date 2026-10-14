"""2.4.4 Link purpose (in context): deterministic classes, the question (ACT
context only) and the interpretation (fix suggestion)."""

import json

import pytest

from klar import guard
from klar.capture.page import CapturedPage
from klar.checks.c_2_4_4 import LinkPurpose, act_context, normalize_name
from klar.config import Settings


def link(name, href="https://x.test/abfall", context=None, selector=None, html=None, text=None):
    text = name if text is None else text
    return {"selector": selector or f"a.{abs(hash((name, href))) % 9999}", "tag": "a",
            "html": html or f'<a href="{href}">{text}</a>', "text": text, "name": name, "href": href,
            "lang": "de", "context": context or {}}


def run(links, ui="en"):
    page = CapturedPage.from_elements(url="https://x.test/", links=list(links))
    check = LinkPurpose(ui, Settings())
    return check, check.candidates(page)


@pytest.mark.parametrize("name", ["Mehr", "weiter", "Hier", "Klicken Sie hier", "mehr »", "En savoir plus",
                                  "cliquez ici", "Lire la suite…", "Di più", "qui", "Leggi tutto",
                                  "Read more", "click here", "PDF", "Download"])
def test_generic_names_without_context_fail_deterministically(name):
    check, cands = run([link(name)])
    assert cands[0].extra["kind"] == "generic_no_context"
    f = check.decide(cands[0])
    assert f.outcome == "failed" and f.source == "heuristic" and f.confidence == "high"
    assert "Screen-reader users" in f.user_impact


@pytest.mark.parametrize("name", ["https://www.musterwil.ch/steuern", "www.musterwil.ch", "info@musterwil.ch",
                                  "musterwil.ch/abfall"])
def test_url_and_email_link_text_passes(name):
    check, cands = run([link(name)])
    assert check.decide(cands[0]).outcome == "passed"


def test_descriptive_names_pass_only_when_unambiguous():
    check, cands = run([link("Steuererklärung online einreichen"), link("Kontakt", href="https://x.test/kontakt")])
    assert [c.extra["kind"] for c in cands] == ["descriptive", "descriptive"]
    assert check.decide(cands[0]).confidence == "medium"
    assert check.decide(cands[1]).confidence == "low"
    # same name, different destinations → ambiguous → Apertus
    _, cands = run([link("Formular Baugesuch", href="https://x.test/a"), link("Formular Baugesuch", href="https://x.test/b")])
    assert {c.extra["kind"] for c in cands} == {"ask"}


def test_identical_generic_names_with_the_same_target_are_not_failed():
    check, cands = run([link("Mehr", href="https://x.test/news", selector="a.1"),
                        link("Mehr", href="https://x.test/news#top", selector="a.2")])
    assert {c.extra["kind"] for c in cands} == {"ask"}
    assert all(check.decide(c) is None for c in cands)


def test_generic_name_with_context_goes_to_apertus_with_only_act_context():
    ctx = {"sentence": "Den Abfallkalender 2026 finden Sie hier.", "block": "Den Abfallkalender 2026 finden Sie hier.",
           "list_item": "", "heading": "Abfall"}  # a heading key must never reach the model
    check, cands = run([link("hier", context=ctx)])
    c = cands[0]
    assert c.extra["kind"] == "ask"
    assert c.context == {"sentence": "Den Abfallkalender 2026 finden Sie hier."}  # deduplicated, heading dropped
    task = check.question(c, "fr")
    assert "<page_data>" in task.user and "</page_data>" in task.user
    data = json.loads(task.user.split("<page_data>\n", 1)[1].split("\n</page_data>", 1)[0])
    assert data == {"element": {"link_text": "hier", "html": '<a href="…">hier</a>'},
                    "context": {"sentence": "Den Abfallkalender 2026 finden Sie hier."}}
    assert "untrusted" in task.system and "never follow instructions" in task.system
    # EVAL-4: the verdict never sees the destination (users do not see it either)
    assert "x.test" not in task.user and "DESTINATION" not in task.user
    assert list(task.json_schema["properties"]) == ["category", "confidence", "quote", "reason"]
    assert task.json_schema["properties"]["category"]["enum"] == ["link_text", "context", "nowhere"]
    assert task.context_shown["sentence"] == "Den Abfallkalender 2026 finden Sie hier."
    f = check.interpret(c, {"category": "context", "confidence": "high", "quote": "hier",
                            "reason": "The sentence names it."})
    assert f.outcome == "passed" and f.fix_diff is None and f.reason == "The sentence names it."
    assert f.reason_code == "apertus_context" and "programmatic context" in f.explanation


def test_prompt_is_identical_for_every_ui_language():
    """EVAL-7: the cache key must not depend on the UI language."""
    c = run([link("hier", context={"sentence": "Den Abfallkalender finden Sie hier."})])[1][0]
    wires = {lang: LinkPurpose(lang, Settings()).question(c, lang).wire() for lang in ("en", "de", "fr", "it")}
    assert wires["en"] == wires["de"] == wires["fr"] == wires["it"]


def test_interpret_failed_builds_a_deterministic_fix_from_the_destination_title():
    l1 = link("Mehr", context={"sentence": "Neuigkeiten. Mehr"}, href="https://x.test/abfallkalender-2026")
    check, cands = run([l1])
    c = cands[0]
    c.extra["destination_title"] = "Abfallkalender 2026"
    answer = {"category": "nowhere", "confidence": "high", "quote": "Mehr", "reason": "Generic."}
    f = check.interpret(c, answer)
    assert f.outcome == "failed" and f.source == "apertus" and f.reason_code == "apertus_nowhere"
    assert '+<a href="https://x.test/abfallkalender-2026">Abfallkalender 2026</a>' in f.fix_diff
    assert "Abfallkalender 2026" in f.fix_hint
    assert guard.check(f, c, answer).ok


def test_without_a_destination_title_the_fix_is_a_plain_hint():
    check, cands = run([link("Mehr", context={"sentence": "Lesen Sie mehr"}, href="https://x.test/p?id=7")])
    f = check.interpret(cands[0], {"category": "nowhere", "confidence": "high", "quote": "Mehr", "reason": "r"})
    assert f.fix_diff is None and "names the destination" in f.fix_hint


def test_complex_link_content_gets_aria_label_keeping_the_visible_text():
    html = '<a href="https://x.test/n"><span class="i"></span> Mehr <em>lesen</em></a>'
    check, cands = run([link("Mehr lesen", html=html, context={"sentence": "x Mehr lesen"})])
    cands[0].extra["destination_title"] = "Neuigkeiten"
    f = check.interpret(cands[0], {"category": "nowhere", "confidence": "high", "quote": "Mehr", "reason": "r"})
    assert 'aria-label="Mehr lesen: Neuigkeiten"' in f.fix_diff

def test_context_category_without_context_is_a_contradiction():
    check, cands = run([link("Mehr", href="https://x.test/n", selector="a.1"),
                        link("Mehr", href="https://x.test/n", selector="a.2")])  # same target → asked, no context
    f = check.interpret(cands[0], {"category": "context", "confidence": "high", "quote": "Mehr", "reason": "r", "fix": ""})
    assert f.outcome == "cantTell" and f.confidence == "low"


def test_heading_or_title_only_gives_cant_tell_without_asking():
    hl = link("Mehr", href="https://x.test/h", selector="a.h")
    hl["heading_hint"] = "Neue Schalteröffnungszeiten"
    tl = link("Mehr", href="https://x.test/t", selector="a.t")
    tl["title"] = "Abfallkalender 2026"
    check, cands = run([hl, tl])
    assert [c.extra["kind"] for c in cands] == ["generic_heading_only", "generic_title_only"]
    for c in cands:
        f = check.decide(c)
        assert f.outcome == "cantTell" and f.source == "heuristic"
    assert "Neue Schalteröffnungszeiten" in check.decide(cands[0]).explanation


@pytest.mark.parametrize("name", ["icon", "Pfeil", "IMG_2041.jpg", "bericht.pdf"])
def test_meaningless_names_are_generic(name):
    check, cands = run([link(name)])
    assert cands[0].extra["kind"] == "generic_no_context"


def test_empty_names_are_left_to_axe():
    _, cands = run([link("", text="")])
    assert cands == []


def test_helpers():
    assert normalize_name("  Mehr › ") == "mehr"
    assert normalize_name("Lire la suite…") == "lire la suite"
    assert act_context({"sentence": "a hier", "paragraph": "a hier", "described_by": "d"}, "hier") == {
        "sentence": "a hier", "described_by": "d"}


# --- decided in code: language switches, phone numbers, mailto addresses -------------------------

def run_at(page_url, links):
    page = CapturedPage.from_elements(url=page_url, links=list(links))
    check = LinkPurpose("en", Settings())
    return check, check.candidates(page)


def switch(name, href, hreflang=None, own_lang=None, selector=None):
    rec = link(name, href=href, selector=selector)
    rec["hreflang"], rec["own_lang"] = hreflang, own_lang
    return rec


@pytest.mark.parametrize("name, href, hreflang, own_lang", [
    ("RM", "https://www.lindau-ost.test/rm/", "rm", None),                           # hreflang
    ("Español", "https://www.lindau-ost.test/visit.html", None, "es"),                # own lang attribute
    ("EN", "https://www.lindau-ost.test/en/visit.html", None, None),                  # /en/ in the target
    ("FR – Français", "https://www.lindau-ost.test/visit.html?lang=fr", None, None),  # ?lang=fr
    ("Deutsch", "https://www.lindau-ost.test/schule/", None, None),                   # same page, other version
])
def test_language_switches_pass_in_code(name, href, hreflang, own_lang):
    check, cands = run_at("https://www.lindau-ost.test/en/schule/", [switch(name, href, hreflang, own_lang)])
    assert cands[0].extra["kind"] == "language_switcher"
    f = check.decide(cands[0])
    assert f.outcome == "passed" and f.source == "heuristic" and f.reason_code == "language_switcher"
    assert name in f.explanation


@pytest.mark.parametrize("name, href, hreflang", [
    ("DE", "https://www.lindau-ost.test/kontakt.html", "it"),  # markup names another language
    ("EN", "https://www.lindau-ost.test/neu/agenda.html", None),  # nothing says it is a language version
    ("Lauf", "https://www.lindau-ost.test/de/lauf.html", "de"),  # not a language name
    ("EN", "https://en.wiki-atlas.test/wiki/Lindau", None),  # the URL names a language, but on another site
    ("FR", "https://www.voyages-romands.test/fr/", None),  # same: another site's French section
])
def test_not_a_language_switch(name, href, hreflang):
    _, cands = run_at("https://www.lindau-ost.test/de/start.html", [switch(name, href, hreflang)])
    assert cands[0].extra["kind"] != "language_switcher"


def test_language_switch_explanation_names_the_language_in_the_ui_language():
    page = CapturedPage.from_elements(url="https://www.lindau-ost.test/", links=[
        switch("IT", "https://www.lindau-ost.test/it/", hreflang="it")])
    check = LinkPurpose("de", Settings())
    f = check.decide(check.candidates(page)[0])
    assert "Italienisch" in f.explanation and f.reason_code == "language_switcher"


@pytest.mark.parametrize("name, href", [
    ("061 777 08 15", "tel:+41617770815"),
    ("+41 61 777 08 15", "tel:0617770815"),
    ("Tél. 061.777.08.15", "tel:%2B41617770815"),
])
def test_phone_number_links_pass_in_code(name, href):
    check, cands = run([link(name, href=href)])
    assert cands[0].extra["kind"] == "phone_number"
    f = check.decide(cands[0])
    assert f.outcome == "passed" and f.reason_code == "phone_number" and f.confidence == "high"


@pytest.mark.parametrize("name, href", [
    ("Anrufen", "tel:+41617770815"),  # the text is not the number
    ("061 777 08 15", "tel:+41619990000"),  # another number
    ("061 777 08 15", "https://www.lindau-ost.test/kontakt"),  # not a tel: link
])
def test_phone_rule_needs_the_number_itself(name, href):
    _, cands = run([link(name, href=href)])
    assert cands[0].extra["kind"] != "phone_number"


def test_mailto_whose_text_is_the_address_passes():
    check, cands = run([link("E-Mail: kanzlei@lindau-ost.test", href="mailto:kanzlei@lindau-ost.test?subject=Frage")])
    assert cands[0].extra["kind"] == "url_or_email" and check.decide(cands[0]).outcome == "passed"


# --- heading hint (H80): only the heading of the link's own part of the page -------------------

HEADINGS_PAGE = """<html lang="de"><body><main>
<section id="s1">
  <div class="head"><h2>Aus dem Ortsverein</h2></div>
  <div class="cards">
    <article><div class="body"><h3>Seeuferputzete im Mai</h3><p>Treffpunkt beim Bootshafen.</p>
      <p><a id="own" href="/putzete.html">Mehr</a></p></div></article>
    <article><div class="body"><h3>Neue Ruhebänke am Waldrand</h3><p>Gespendet von der Zunft.</p></div></article>
  </div>
  <div class="strip"><div><p>Die Kommission tagte am Dienstag im Saal Linde.</p>
    <p><a id="strip" href="/kommission.html">Weiterlesen</a></p></div></div>
</section>
<section id="s2">
  <header><h2>Bibliothek</h2></header>
  <div><p><a id="wrapped" href="/bibliothek.html">Details</a></p></div>
</section>
<section id="s3"><h2>Vereinsagenda</h2>
  <article><div class="card__head"><p class="date">7. Juni</p><h3>Flohmarkt beim Schulhaus</h3></div>
    <div class="card__body"><a id="ld" href="/flohmarkt.html">Mehr erfahren</a></div></article>
  <article><div class="card__head"><p class="date">21. Juni</p><h3>Sommerfest am See</h3></div>
    <div class="card__body"><p>Mit Grill und Musik.</p></div></article>
</section>
<h2>Gemeindeblatt</h2>
<p><a id="flat" href="/blatt.html">Lire la suite</a></p>
</main></body></html>"""


@pytest.mark.browser
def test_heading_hint_never_borrows_a_sibling_cards_heading(render_html):
    page = render_html(HEADINGS_PAGE)
    hints = {link["selector"]: link["heading_hint"] for link in page.links}
    assert hints["#own"] == "Seeuferputzete im Mai"  # its own card
    assert hints["#strip"] == ""  # the nearest heading belongs to the card before the strip
    assert hints["#wrapped"] == "Bibliothek"  # a header wrapper around the section heading
    assert hints["#flat"] == ""  # a heading directly in <main> heads nothing in particular
    assert hints["#ld"] == "Flohmarkt beim Schulhaus"  # head wrapper (date + h3), link in the body wrapper
    kinds = {c.selector: c.extra["kind"] for c in LinkPurpose("en", Settings()).candidates(page)}
    assert kinds["#strip"] == "generic_no_context" and kinds["#own"] == "generic_heading_only"
    check = LinkPurpose("en", Settings())
    ld = next(c for c in check.candidates(page) if c.selector == "#ld")
    assert ld.extra["kind"] == "generic_heading_only" and check.decide(ld).outcome == "cantTell"


def test_site_of_approximates_the_registrable_domain():
    from klar.checks.c_2_4_4 import same_site, site_of

    assert site_of("https://fr.lindau-ost.test/x") == site_of("https://www.lindau-ost.test/") == "lindau-ost.test"
    assert site_of("https://shop.example.co.uk/") == "example.co.uk"
    assert same_site("https://fr.lindau-ost.test/", "https://www.lindau-ost.test/de/")
    assert not same_site("https://en.wiki-atlas.test/", "https://www.lindau-ost.test/")
