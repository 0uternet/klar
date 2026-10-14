"""Capture layer: rendering, extraction, axe-core, screenshots, form probe."""

from pathlib import Path

import pytest

from klar.capture.axe import axe_findings, criteria_of, run_axe

pytestmark = pytest.mark.browser

PAGE = """<!doctype html><html lang="de"><head><title>Test</title></head><body>
<main>
  <h1>Willkommen</h1>
  <p>Text auf Deutsch mit <span lang="fr">un peu de français</span> dazwischen.</p>
  <img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" width="120" height="80">
  <figure><img id="photo" src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" width="200" height="100" alt="Rathaus">
  <figcaption>Das Rathaus von Musterwil</figcaption></figure>
  <form id="f" novalidate>
    <label for="email">E-Mail</label>
    <input id="email" type="email" required aria-describedby="email-hint">
    <span id="email-hint">Format: name@beispiel.ch</span>
    <span id="email-err" hidden></span>
    <button type="submit">Senden</button>
  </form>
  <script>
    document.getElementById('f').addEventListener('submit', (e) => {
      e.preventDefault();
      const el = document.getElementById('email');
      const err = document.getElementById('email-err');
      if (!el.value.includes('@')) {
        el.setAttribute('aria-invalid', 'true');
        el.setAttribute('aria-errormessage', 'email-err');
        err.hidden = false;
        err.setAttribute('role', 'alert');
        err.textContent = 'Bitte geben Sie eine gültige E-Mail-Adresse ein.';
      }
    });
  </script>
</main></body></html>"""


def test_snapshot_and_extraction(render_html):
    page = render_html(PAGE)
    assert page.lang == "de" and page.title == "Test" and "Willkommen" in page.text
    assert (page.scan_dir / "page.html").is_file()
    texts = {p["text"]: p for p in page.passages}
    assert texts["un peu de français"]["own_lang"] == "fr"
    assert texts["un peu de français"]["is_container"] is False
    assert texts["Text auf Deutsch mit dazwischen."]["lang"] == "de"
    imgs = {i["selector"]: i for i in page.images}
    photo = imgs["#photo"]
    assert photo["alt"] == "Rathaus" and photo["name"] == "Rathaus"
    assert photo["context"]["caption"] == "Das Rathaus von Musterwil"
    field = page.fields[0]
    assert field["name"] == "E-Mail" and field["labels"] == ["E-Mail"] and field["required"]
    assert field["describedby"] == "Format: name@beispiel.ch"
    assert page.forms[0]["submit"]
    assert [h["text"] for h in page.headings] == ["Willkommen"]


def test_axe_runs_and_maps_to_findings(render_html):
    page = render_html(PAGE)
    page.axe = run_axe(page.live, "de")
    assert page.axe["version"] == "4.13.0"
    findings = axe_findings(page.axe, page.url, None, "de")
    alt = [f for f in findings if f.criterion == "1.1.1"]
    assert alt and alt[0].source == "rule" and alt[0].outcome == "failed"
    assert alt[0].selector == "html > body > main > img"  # our canonical cssPath, not axe's own selector
    assert page.selector_exists(alt[0].selector)
    assert "axe-core" in alt[0].explanation
    assert "1.1.1" in page.axe["criteria_tested"]


def test_criteria_of_tags():
    assert criteria_of(["wcag2a", "wcag111", "wcag412", "wcag1410", "best-practice"]) == ["1.1.1", "4.1.2", "1.4.10"]


def test_element_screenshot(render_html):
    page = render_html(PAGE)
    rel = page.screenshot("#photo", "photo")
    assert rel == "crops/photo.png"
    data = (page.scan_dir / rel).read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert page.screenshot("#does-not-exist", "nope") is None


def test_form_probe_reports_error_messages(render_html):
    page = render_html(PAGE, allow_form_submit=True)
    probe = page.form_probe()
    assert len(probe) == 1 and probe[0]["submitted_via"] == "click"
    invalid = probe[0]["invalid_fields"]
    assert invalid and invalid[0]["error_text"] == "Bitte geben Sie eine gültige E-Mail-Adresse ein."
    assert invalid[0]["describedby_text"] == "Format: name@beispiel.ch"
    assert any("gültige E-Mail" in a["text"] for a in probe[0]["alerts"])
    # the probe ran in another tab: the audited page itself is unchanged
    assert page.evaluate("() => document.getElementById('email').getAttribute('aria-invalid')") is None


def test_form_probe_is_off_by_default(render_html):
    page = render_html(PAGE)
    assert page.form_probe() == [] and page.form_origins == () and page.allow_form_submit is False


def test_render_carries_the_form_allow_list(render_html):
    page = render_html(PAGE, allow_form_submit=True, form_origins=("http://127.0.0.1:9",))
    assert page.form_origins == ("http://127.0.0.1:9",) and page.allow_form_submit is True


def test_native_validation_messages(render_html):
    page = render_html("""<html lang="de"><body><form><label>Name <input name="n" required></label>
        <button>OK</button></form></body></html>""", allow_form_submit=True)
    probe = page.form_probe()
    assert probe[0]["native"] and probe[0]["native"][0]["message"]


def test_file_url_destination_title(render_html, tmp_path: Path):
    (tmp_path / "abfall.html").write_text("<html><head><title>Abfallkalender 2026</title></head></html>", encoding="utf-8")
    from klar.capture.page import CapturedPage

    page = CapturedPage.from_elements(url=(tmp_path / "index.html").as_uri())
    assert page.fetch_title((tmp_path / "abfall.html").as_uri()) == "Abfallkalender 2026"
    assert page.fetch_title("https://elsewhere.example/") is None  # never leaves the audited site
