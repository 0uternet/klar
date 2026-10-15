"""Render technical_report.md to the submission PDF (A4) and check the page limit.

    python scripts/build_report_pdf.py [--out Klar_Report.pdf] [--max-pages 6]

The report is limited to 6 pages
without references. The body (everything before "## References") must fit in
--max-pages; the script fails otherwise. Development tool only: it needs the
`markdown` package (pip install markdown==3.8.2) and Playwright Chromium, which the
app already uses. Figures are inlined from docs/report/assets, so the PDF is self-contained.
"""

from __future__ import annotations

import argparse
import base64
import re
import sys
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

CSS = """
@page { size: A4; margin: 15mm 15mm 14mm 15mm; }
html { font-family: "Liberation Sans", "DejaVu Sans", Arial, sans-serif; font-size: 8.6pt; line-height: 1.32; color: #111; }
body { margin: 0; }
h1 { font-size: 15pt; margin: 0 0 3pt; }
h1 + p { margin-top: 0; font-size: 10pt; }
h2 { font-size: 10.6pt; margin: 8pt 0 2pt; border-bottom: 0.6pt solid #999; padding-bottom: 1pt; break-after: avoid; }
h3 { font-size: 9.2pt; margin: 6pt 0 2pt; break-after: avoid; }
p, ul, ol { margin: 2.5pt 0; }
ul, ol { padding-left: 13pt; }
li { margin: 0.8pt 0; }
code { font-family: "DejaVu Sans Mono", Consolas, monospace; font-size: 7.6pt; }
table { border-collapse: collapse; width: 100%; margin: 3pt 0 4pt; font-size: 7.4pt; break-inside: avoid; }
th, td { border: 0.5pt solid #aaa; padding: 1.2pt 3pt; text-align: left; vertical-align: top; }
th { background: #eee; }
figure { margin: 4pt 0; text-align: center; break-inside: avoid; }
figure img { max-width: 100%; }
figure.fig-narrow img { max-width: 62%; }
figcaption { font-size: 7.6pt; color: #333; margin-top: 2pt; text-align: left; }
a { color: #0645ad; text-decoration: none; }
.references { font-size: 7.2pt; line-height: 1.22; }
.references ol li { margin: 0.4pt 0; }
"""


def inline_images(html: str) -> str:
    def repl(m: re.Match) -> str:
        src = m.group(1)
        path = ROOT / src
        if not path.is_file():
            return m.group(0)
        mime = "image/svg+xml" if path.suffix == ".svg" else f"image/{path.suffix.lstrip('.')}"
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f'src="data:{mime};base64,{data}"'
    return re.sub(r'src="([^"]+)"', repl, html)


def render(md_text: str) -> str:
    body, sep, refs = md_text.partition("\n## References")
    html = markdown.markdown(body, extensions=["tables", "md_in_html"])
    if sep:
        html += '<div id="refs" class="references">' + markdown.markdown("## References" + refs, extensions=["tables"]) + "</div>"
    # HTML comments (VERIFY notes) never reach the PDF
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    return f"<!doctype html><html lang='en'><head><meta charset='utf-8'><style>{CSS}</style></head><body>{inline_images(html)}</body></html>"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT / "technical_report.md"))
    ap.add_argument("--out", default=str(ROOT / "Klar_Report.pdf"))
    ap.add_argument("--max-pages", type=int, default=6)
    args = ap.parse_args()

    md_text = Path(args.src).read_text(encoding="utf-8")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.emulate_media(media="print")
        # The body alone (without References) gives the page count the limit applies to.
        page.set_content(render(md_text.partition("\n## References")[0]), wait_until="load")
        body_pdf = page.pdf(format="A4", print_background=True, prefer_css_page_size=True)
        page.set_content(render(md_text), wait_until="load")
        page.pdf(path=args.out, format="A4", print_background=True, prefer_css_page_size=True)
        browser.close()
    count = lambda b: len(re.findall(rb"/Type\s*/Page[^s]", b))  # noqa: E731
    total, body_pages = count(Path(args.out).read_bytes()), count(body_pdf)
    print(f"{args.out}: {total} pages, body {body_pages} pages before References (limit {args.max_pages})")
    if body_pages > args.max_pages:
        print("ERROR: the body exceeds the page limit", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
