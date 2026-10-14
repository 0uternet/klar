"""Programmatically determined link context (WCAG 2.4.4 / ACT rule 5effbb),
computed in the browser by capture/js/klar_extract.js.

The fixtures are written for Klar., in the style of the W3C ACT 5effbb test cases
(they are not copies of them): same sentence, paragraph, list item, table cell
with its header cells, aria-describedby — and NOT a preceding heading.
"""

import pytest

from klar.checks.c_2_4_4 import LinkPurpose
from klar.config import Settings

pytestmark = pytest.mark.browser


def ctx_of(page, href):
    link = next(item for item in page.links if item["raw_href"] == href)
    return link["context"], link


def test_same_sentence_only(render_html):
    page = render_html("""<html lang="de"><body><p>Die Sammelstellen sind am Samstag geschlossen.
        Den Abfallkalender 2026 finden Sie <a href="/abfall">hier</a>. Fragen? Rufen Sie an.</p></body></html>""")
    ctx, _ = ctx_of(page, "/abfall")
    assert ctx["sentence"] == "Den Abfallkalender 2026 finden Sie hier."
    assert "Samstag" in ctx["block"]  # the closest block container is context too (ACT 5effbb)


def test_abbreviations_and_dates_do_not_split_sentences(render_html):
    page = render_html("""<html lang="de"><body>
        <p>Lesen Sie z. B. den <a href="/bericht">Bericht</a> zur Lage.</p>
        <p>Ab dem 4. Oktober gilt der neue <a href="/plan">Fahrplan</a> für alle Linien.</p></body></html>""")
    assert ctx_of(page, "/bericht")[0]["sentence"] == "Lesen Sie z. B. den Bericht zur Lage."
    assert ctx_of(page, "/plan")[0]["sentence"] == "Ab dem 4. Oktober gilt der neue Fahrplan für alle Linien."


def test_line_break_ends_the_sentence_but_not_the_block(render_html):
    page = render_html('<html lang="de"><body><p>Abfallkalender 2026<br><a href="/abfall">Mehr</a></p></body></html>')
    ctx, _ = ctx_of(page, "/abfall")
    assert "sentence" not in ctx
    assert ctx["block"] == "Abfallkalender 2026 Mehr"


def test_closest_block_container_is_context_not_only_p(render_html):
    """ACT 5effbb: a <div> (or td, section…) that generates a block box is context."""
    page = render_html("""<html lang="de"><body>
        <div>Die Velostation ist ab 1. November offen. <a href="/velo">Mehr</a></div>
        <section><div><div>Neue Öffnungszeiten.</div><div><a href="/zeiten">Mehr</a></div></div></section>
        </body></html>""")
    ctx, _ = ctx_of(page, "/velo")
    assert ctx["block"] == "Die Velostation ist ab 1. November offen. Mehr"
    check = LinkPurpose("en", Settings())
    kinds = {c.selector: c.extra["kind"] for c in check.candidates(page)}
    velo = next(item["selector"] for item in page.links if item["raw_href"] == "/velo")
    zeiten = next(item["selector"] for item in page.links if item["raw_href"] == "/zeiten")
    assert kinds[velo] == "ask"  # context exists → Apertus, not a heuristic failure
    assert kinds[zeiten] == "generic_no_context"  # sibling-block teaser is not context (F63)


def test_list_item(render_html):
    page = render_html("""<html lang="de"><body><ul>
        <li>Steuererklärung 2025: <a href="/steuern">Formular</a></li></ul></body></html>""")
    ctx, _ = ctx_of(page, "/steuern")
    assert ctx["list_item"] == "Steuererklärung 2025: Formular"


def test_table_cell_with_column_and_row_headers(render_html):
    page = render_html("""<html lang="de"><body><table>
        <thead><tr><th>Dokument</th><th>Download</th></tr></thead>
        <tbody><tr><th scope="row">Budget 2026</th><td><a href="/budget.pdf">PDF</a></td></tr>
               <tr><th scope="row">Rechnung 2025</th><td><a href="/rechnung.pdf">PDF</a></td></tr></tbody>
        </table></body></html>""")
    ctx, _ = ctx_of(page, "/budget.pdf")
    assert "table_cell" not in ctx  # the cell holds only the link text itself
    assert ctx["table_headers"] == "Download | Budget 2026"
    assert ctx_of(page, "/rechnung.pdf")[0]["table_headers"] == "Download | Rechnung 2025"


def test_headers_attribute(render_html):
    page = render_html("""<html lang="de"><body><table><tr><th id="h1">Bauprojekte</th><th id="h2">Plan</th></tr>
        <tr><td>Schulhaus</td><td headers="h1 h2"><a href="/plan.pdf">ansehen</a></td></tr></table></body></html>""")
    assert ctx_of(page, "/plan.pdf")[0]["table_headers"] == "Bauprojekte | Plan"


def test_aria_describedby(render_html):
    page = render_html("""<html lang="de"><body><div><a href="/bau" aria-describedby="d1">Mehr</a></div>
        <div id="d1">über die Baubewilligung</div></body></html>""")
    ctx, _ = ctx_of(page, "/bau")
    assert ctx == {"described_by": "über die Baubewilligung"}


def test_preceding_heading_is_not_context(render_html):
    page = render_html("""<html lang="de"><body><section><h2>Abfallkalender</h2>
        <p><a href="/abfall">Mehr</a></p></section></body></html>""")
    ctx, link = ctx_of(page, "/abfall")
    assert not any("Abfallkalender" in v for v in ctx.values())  # never context, never shown to the model
    assert link["heading_hint"] == "Abfallkalender"
    check = LinkPurpose("en", Settings())
    cands = check.candidates(page)
    assert "Abfallkalender" not in " ".join(cands[0].context.values())
    # protocol 2.4.4/C1: only a preceding heading disambiguates → human review, model not asked
    f = check.decide(cands[0])
    assert f.outcome == "cantTell" and f.source == "heuristic" and "H80" in f.explanation


def test_heading_shared_by_several_identical_links_is_no_hint(render_html):
    page = render_html("""<html lang="de"><body><section><h2>Aktuelles</h2>
        <div><div>Neue Öffnungszeiten.</div><div><a href="/a">Mehr erfahren</a></div></div>
        <div><div>Velo-Aktion.</div><div><a href="/b">Mehr erfahren</a></div></div></section></body></html>""")
    assert [item["heading_hint"] for item in page.links] == ["", ""]
    check = LinkPurpose("en", Settings())
    assert {check.decide(c).outcome for c in check.candidates(page)} == {"failed"}  # protocol 2.4.4/F1


def test_heading_inside_the_list_item_is_context(render_html):
    """Card lists: the heading is inside the list item, so it IS programmatic context."""
    page = render_html("""<html lang="de"><body><ul><li><h3>Hundesteuer</h3><p>Fällig bis 31. März.</p>
        <a href="/hund">Mehr</a></li></ul></body></html>""")
    ctx, _ = ctx_of(page, "/hund")
    assert "Hundesteuer" in ctx["list_item"]


def test_accessible_names_come_from_chromium(render_html):
    page = render_html("""<html lang="de"><body>
        <a href="/k"><img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="Kontakt"></a>
        <a href="/s" aria-label="Suche öffnen">🔍</a>
        <a href="/m">Mehr <span style="position:absolute;clip:rect(0 0 0 0);width:1px;height:1px;overflow:hidden">über Steuern</span></a>
        <a href="/x" aria-labelledby="l1">X</a><span id="l1">Label eins</span>
        <a href="/hidden" style="display:none">versteckt</a></body></html>""")
    names = {item["raw_href"]: item["name"] for item in page.links}
    assert names == {"/k": "Kontakt", "/s": "Suche öffnen", "/m": "Mehr über Steuern", "/x": "Label eins"}
    assert all(item["role_computed"] == "link" for item in page.links)


def test_selectors_are_unique_and_resolve(render_html):
    page = render_html("""<html lang="de"><body><ul><li><a href="/a">A</a></li><li><a href="/b">B</a></li></ul>
        <p id="x:1"><a href="/c">C</a></p></body></html>""")
    sels = [item["selector"] for item in page.links]
    assert len(set(sels)) == 3
    for s in sels:
        assert page.evaluate("s => document.querySelectorAll(s).length", s) == 1
    assert page.selector_exists(sels[0]) and not page.selector_exists("#nope")
