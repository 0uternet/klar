"""Exports: json, earl (JSON-LD), csv, html (standalone). Every report starts with
the mandatory disclaimer ("does not certify conformance")."""

from __future__ import annotations

from pathlib import Path

from klar.i18n import t
from klar.models import Scan

FORMATS = {
    "json": ("application/json", "json"),
    "earl": ("application/ld+json", "jsonld"),
    "csv": ("text/csv; charset=utf-8", "csv"),
    "html": ("text/html; charset=utf-8", "html"),
}


def disclaimer(scan: Scan) -> str:
    n = int(scan.stats.get("criteria_checked") or 0)  # criteria with an implemented check that ran
    m = int(scan.stats.get("criteria_apertus") or 0)  # of which judged with Apertus
    return t("disclaimer", scan.ui_lang, n=n, m=m)


def render(scan: Scan, fmt: str, assets_dir: Path | None = None) -> bytes:
    if fmt == "json":
        from klar.report.json import to_json

        return to_json(scan).encode("utf-8")
    if fmt == "earl":
        from klar.report.earl import to_earl

        return to_earl(scan).encode("utf-8")
    if fmt == "csv":
        from klar.report.csv import to_csv

        return to_csv(scan).encode("utf-8-sig")  # BOM: Excel opens umlauts correctly
    if fmt == "html":
        from klar.report.html import to_html

        return to_html(scan, assets_dir).encode("utf-8")
    raise ValueError(f"unknown format {fmt!r}; use one of {', '.join(FORMATS)}")
