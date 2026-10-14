"""Accessibility check of Klar.'s own pages with the vendored axe-core (CI job `a11y`).

Runs INSIDE the app container, which already has Playwright, Chromium and axe-core:

    docker compose exec -T app python3 - < deploy/a11y_check.py

Checks the UI views (light and dark colour scheme, English and German browser locale) and the
standalone HTML report written by `klar demo`. Exit code 1 if axe reports any violation of
WCAG 2.0 / 2.1 / 2.2 level A or AA, 2 if a page cannot be checked.
Extra views: KLAR_A11Y_VIEWS="/#/foo,/#/bar". Base URL: KLAR_A11Y_BASE (default http://127.0.0.1:8080).
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.environ.get("KLAR_A11Y_BASE", "http://127.0.0.1:8080").rstrip("/")
TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
SCHEMES = ("light", "dark")
LOCALES = ("en-GB", "de-CH")

pkg = Path(importlib.util.find_spec("klar").submodule_search_locations[0])
AXE = (pkg / "capture" / "vendor" / "axe.min.js").read_text(encoding="utf-8")
data_dir = Path(os.environ.get("KLAR_DATA_DIR", "/app/var"))

views = ["/#/", "/#/about", "/#/human"]
latest = data_dir / "reports" / "demo-latest.json"
if latest.is_file():
    scan_id = json.loads(latest.read_text(encoding="utf-8")).get("id")
    if scan_id:
        views += [f"/#/scan/{scan_id}", f"/#/report/{scan_id}"]
views += [v.strip() for v in os.environ.get("KLAR_A11Y_VIEWS", "").split(",") if v.strip()]

targets = [(BASE + v, s, loc) for v in views for s in SCHEMES for loc in LOCALES]
report = data_dir / "reports" / "demo-latest.html"
if report.is_file():
    targets += [(report.as_uri(), s, "en-GB") for s in SCHEMES]

violations_total = 0
errors = 0
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for url, scheme, locale in targets:
        label = f"{url} [{scheme}, {locale}]"
        # bypass_csp: inject axe even under the app's strict Content-Security-Policy.
        ctx = browser.new_context(color_scheme=scheme, locale=locale, bypass_csp=True)
        page = ctx.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=30_000)
            page.wait_for_timeout(1_000)          # let the single-page app render
            page.add_script_tag(content=AXE)
            result = page.evaluate(
                "async (tags) => await axe.run(document, {runOnly: {type: 'tag', values: tags}})", TAGS)
        except Exception as exc:  # noqa: BLE001 - report and continue with the next page
            print(f"ERROR  {label}: {type(exc).__name__}: {exc}")
            errors += 1
            ctx.close()
            continue
        found = result.get("violations", [])
        if not found:
            print(f"ok     {label}")
        for v in found:
            violations_total += 1
            nodes = v.get("nodes", [])
            print(f"FAIL   {label}: {v['id']} ({v.get('impact')}) x{len(nodes)} - {v.get('help')}")
            for n in nodes[:3]:
                print(f"         {', '.join(n.get('target', []))}")
        ctx.close()
    browser.close()

print(f"\n{len(targets)} page states checked, {violations_total} violation types, {errors} errors")
sys.exit(2 if errors else (1 if violations_total else 0))
