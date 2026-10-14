"""Build the Musterwil demo site into track_2b/data/demo-site (HTML pages, images, PDF, ISSUES.md, issues.jsonl).

Usage (from track_2b/):  python -I scripts/demo_site/build.py [--out DIR]

The answer keys (ISSUES.md, issues.jsonl) are written to data/demo-truth/, OUTSIDE the served
demo folder, so a scanner (or a judge browsing /demo/) never sees the expected outcomes.

The hand-written CSS and JS in data/demo-site/assets/{css,js}/ are not generated.
Everything is fictional (Gemeinde Musterwil). Stdlib only. Deterministic output.
"""
import json
import os
import sys
import textwrap
from collections import Counter, OrderedDict
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import svgs  # noqa: E402
import content_de  # noqa: E402
import content_fr  # noqa: E402
import content_it  # noqa: E402

SITE = str(Path(__file__).resolve().parents[2] / 'data' / 'demo-site')    # served folder (no answer keys!)
TRUTH = str(Path(__file__).resolve().parents[2] / 'data' / 'demo-truth')  # answer keys, outside the served root
if '--out' in sys.argv:
    SITE = os.path.abspath(sys.argv[sys.argv.index('--out') + 1])
    TRUTH = SITE.rstrip('/\\') + '-truth'

ROWS = []


def R(page, testid, criterion, kind, expected, rationale, *, scope='page', deciding_page=None):
    """kind: issue (planted defect) | trap (correct/exempt element) | set (a page of a set-level
    criterion whose expected outcome is the outcome of the whole language version)."""
    assert kind in ('issue', 'trap', 'set'), kind
    assert scope in ('page', 'set'), scope
    assert expected in ('failed', 'passed', 'cantTell', 'inapplicable'), expected
    lang = 'fr' if page.startswith('fr/') else 'it' if page.startswith('it/') else 'de'
    ROWS.append(OrderedDict(
        page=page,
        selector=f'[data-testid="{testid}"]' if testid else None,
        criterion=criterion,
        kind=kind,
        expected=expected,
        rationale=rationale,
        lang=lang,
        scope=scope,
        deciding_page=deciding_page,
    ))


# ---------------------------------------------------------------- PDF (fictional regulation)
PDF_LINES = [
    ('h1', 'Reglement über die Abfallentsorgung der Gemeinde Musterwil'),
    ('p', 'Fiktives Dokument der Demonstrationswebsite Musterwil. Vom Gemeinderat am 12. Mai 2025 genehmigt.'),
    ('h2', 'Art. 1 Zweck'),
    ('p', 'Dieses Reglement regelt die Sammlung, Verwertung und Entsorgung der Siedlungsabfälle auf dem Gemeindegebiet.'),
    ('h2', 'Art. 2 Kehricht'),
    ('p', 'Der Kehricht wird wöchentlich am Dienstag abgeführt. Es dürfen nur gebührenpflichtige Kehrichtsäcke verwendet werden.'),
    ('h2', 'Art. 3 Grüngut'),
    ('p', 'Grüngut wird von März bis Oktober wöchentlich, von November bis Februar alle zwei Wochen am Donnerstag abgeführt.'),
    ('h2', 'Art. 4 Separatsammlungen'),
    ('p', 'Papier und Karton werden monatlich gesammelt. Glas, Aluminium und Weissblech sind an der Sammelstelle Bahnhof abzugeben.'),
    ('h2', 'Art. 5 Bereitstellung'),
    ('p', 'Die Abfälle sind am Abfuhrtag bis 7 Uhr gut sichtbar am Strassenrand bereitzustellen.'),
    ('h2', 'Art. 6 Gebühren'),
    ('p', 'Die Grundgebühr beträgt CHF 95.– pro Haushalt und Jahr. Die Gebühr für einen 35-Liter-Sack beträgt CHF 2.20.'),
    ('h2', 'Art. 7 Inkrafttreten'),
    ('p', 'Dieses Reglement tritt am 1. Januar 2026 in Kraft.'),
]


def make_pdf(path):
    def esc(s):
        return s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    pages, cur, y = [], [], 780.0
    for style, text in PDF_LINES:
        size = {'h1': 16, 'h2': 12, 'p': 10.5}[style]
        font = 'F1' if style == 'p' else 'F2'
        lead = size * 1.45
        if style == 'h2':
            y -= 8
        for line in textwrap.wrap(text, int(480 / (size * 0.5))) or ['']:
            if y < 60:
                pages.append(cur)
                cur, y = [], 780.0
            cur.append(f'BT /{font} {size} Tf 56 {y:.1f} Td ({esc(line)}) Tj ET')
            y -= lead
        y -= 4
    pages.append(cur)
    objs = []
    n_pages = len(pages)
    kids = ' '.join(f'{5 + 2 * i} 0 R' for i in range(n_pages))
    objs.append(b'<< /Type /Catalog /Pages 2 0 R /Lang (de-CH) >>')
    objs.append(f'<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>'.encode())
    objs.append(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>')
    objs.append(b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>')
    for i, ops in enumerate(pages):
        stream = '\n'.join(ops).encode('cp1252')
        objs.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {6 + 2 * i} 0 R >>'.encode())
        objs.append(b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream')
    info_num = len(objs) + 1
    objs.append('<< /Title (Abfallreglement Musterwil – fiktiv) /Author (Gemeinde Musterwil) >>'.encode('cp1252'))
    out = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
    offsets = []
    for num, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f'{num} 0 obj\n'.encode() + body + b'\nendobj\n'
    xref = len(out)
    out += f'xref\n0 {len(objs) + 1}\n0000000000 65535 f \n'.encode()
    for off in offsets:
        out += f'{off:010d} 00000 n \n'.encode()
    out += f'trailer\n<< /Size {len(objs) + 1} /Root 1 0 R /Info {info_num} 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode()
    with open(path, 'wb') as fh:
        fh.write(out)
    return len(out)


# ---------------------------------------------------------------- docs
HIGHLIGHTS = [
    ('hook', 'Image-teaser strip "Kurz gemeldet": four tiles, each a decorative picture, a short label and a lone "Mehr" link', 'index.html',
     '[data-testid="news-teaser-1-more"] … [data-testid="news-teaser-4-more"]', '2.4.4', 'failed ×4 (no programmatic context at all)'),
    ('a', 'Four news cards, each with image, heading, teaser and a bare "Mehr" link', 'index.html',
     '[data-testid="news-card-1-more"] … [data-testid="news-card-4-more"]', '2.4.4', 'cantTell ×4 (strict ACT reading: failed)'),
    ('b', 'French paragraph inside the German "Mitteilung der Regionalkonferenz Aarenwald" box, no lang="fr"', 'index.html',
     '[data-testid="notice-fr-para"]', '3.1.2', 'failed'),
    ('c', 'Bar chart "Grüngut-Sammelmengen 2025" as <img alt="Bild">', 'abfallkalender.html',
     '[data-testid="waste-chart"]', '1.1.1', 'failed'),
    ('d', 'Form "Wohnsitzbestätigung bestellen": submit empty → red box with only "Fehler"; "Ungültige Eingabe" next to PLZ', 'online-schalter.html',
     '[data-testid="form-error-summary"], [data-testid="form-plz-error"]', '3.3.1 (and 3.3.3 for the PLZ message)', 'failed'),
    ('e', '"… klicken Sie auf den grünen Knopf rechts." next to a green round arrow button', 'anleitung.html',
     '[data-testid="instruction-green-button"]', '1.3.3', 'failed'),
]

GAPS = [
    'No date of the last review: only the creation date (3 March 2025) is given; there is no "last reviewed/updated" date.',
    "Feedback only through a web form: the statement's feedback section offers no e-mail address or phone number for accessibility feedback; in DE and IT the form's send control is itself a non-focusable `<div class=\"btn\">` (see the 4.1.2 rows), so keyboard users cannot use the only channel.",
    'Known problems are missing from the list of non-accessible content: the auto-rotating carousel without pause (freizeit.html), the online-counter form errors (online-schalter.html: "Fehler", positive tabindex, no review step) and the "Mehr" link texts.',
    'No enforcement / ombudsperson procedure: the statement does not say where to turn if the feedback is not answered satisfactorily (EU 2018/1523 model "enforcement procedure"; eCH-0059 practice of naming a contact and a conciliation/ombuds office).',
    'Assessment method given only as "Selbstbewertung" without scope or sample pages.',
]


def md_escape(s):
    return s.replace('|', '\\|').replace('<', '&lt;').replace('>', '&gt;')


def write_docs(rows):
    by_crit = Counter(r['criterion'] for r in rows)
    lines = []
    lines.append('# Musterwil demo site – planted issues and traps\n')
    lines.append('**Gemeinde Musterwil / Commune de Musterwil / Comune di Musterwil** is a fictional, trilingual (DE root, `fr/`, `it/`) '
                 'municipal website. Klar. scans it in `make run`. It looks like a normal small Swiss municipal site '
                 'but contains deliberately planted accessibility issues for criteria that need human judgement, plus correct "trap" elements '
                 'that must **not** be flagged. Everything is invented: the municipality, the region "Aarenwald", people, addresses '
                 '(`9999 Musterwil`), phone numbers (`032 000 …`), e-mails (`@musterwil.example`) and figures. All images are SVGs drawn for '
                 'this site; there are no external resources (no CDN, web fonts, remote images or analytics) and no coat of arms or federal marks.\n')
    lines.append('**Answer keys live outside the served folder.** This file and `issues.jsonl` are in `data/demo-truth/`; '
                 'the pages they describe are in `data/demo-site/` (all `page` paths below are relative to it).\n')
    lines.append('## Serve\n')
    lines.append('```\npython -m http.server -d data/demo-site 8000\n# then open http://localhost:8000/   (file:// works too; all links are relative)\n```\n')
    lines.append('The HTML pages, SVG images, the PDF, this file and `issues.jsonl` (both in `data/demo-truth/`) are generated by '
                 '`python -I scripts/demo_site/build.py` (stdlib only, deterministic); the CSS and JS in '
                 '`assets/css/` and `assets/js/` are hand-written. Edit the content modules in `scripts/demo_site/` '
                 'and rebuild rather than editing the HTML by hand. `python -I scripts/validate_testset.py` checks '
                 'that every selector below matches exactly one element.\n')
    lines.append('## Conventions\n')
    lines.append('- Every planted issue and every trap has a `data-testid`; `[data-testid="…"]` matches exactly one element on its page. '
                 'Testids are neutral names; verdicts appear only in this file and in `issues.jsonl`.\n'
                 '- `selector` `—` (JSON `null`) = page-level criterion (e.g. 2.4.2, 2.4.5, 3.1.1).\n'
                 '- `expected` uses the W3C ACT / EARL vocabulary: `failed` | `passed` | `cantTell` | `inapplicable`. '
                 '`kind` = `issue` (planted defect) or `trap` (correct or exempt element; must not be reported as failed).\n'
                 '- 2.4.4 follows decision D1 of `data/testset/PROTOCOL.md`: programmatic context = the link\'s accessible name plus the enclosing '
                 'sentence, the closest block container (ACT 5effbb), list item(s), table cell with its header cells and `aria-describedby` targets. '
                 '**A preceding heading is not context** (H80 is advisory), so links disambiguated only by a card heading are labelled `cantTell` '
                 '(strict ACT 5effbb reading: `failed`); links with no context at all (the "Kurz gemeldet" tiles) are `failed`.\n'
                 '- Error containers (`form-error-summary`, `form-plz-error`) exist empty and `hidden` in the static DOM; their text is injected '
                 'by `assets/js/forms.js` when the form is submitted.\n'
                 '- `velo-aktion.html` is intentionally reachable only from the 4th news card on `index.html` (not in nav, sitemap or search index).\n'
                 '- **Set-level criteria (2.4.5, 3.2.3, 3.2.4; and 2.4.2 for titles duplicated across pages).** As in `data/testset/PROTOCOL.md`, the label applies to the *set of pages*; '
                 'each language version (German root, `fr/`, `it/`) is one set. Rows for these criteria have `scope = set`, their `expected` '
                 'is the outcome of the whole set on every page where the row applies, and `deciding_page` names the page that decides it. '
                 'The German set is designed to fail each of them because of one page: 2.4.2 → `oeffnungszeiten.html`, 2.4.5 → `velo-aktion.html`, '
                 '3.2.3 → `abfallkalender.html`, 3.2.4 → `sitemap.html`; the French and Italian sets pass. `kind = set` marks a row whose '
                 'page itself is fine (or exempt) but which carries the set outcome; the deciding page keeps `kind = issue`.\n')
    lines.append('## Highlights\n')
    lines.append('| | Finding | Page | Selector | Criterion | Expected |\n|---|---|---|---|---|---|')
    for k, desc, page, sel, crit, exp in HIGHLIGHTS:
        lines.append(f'| ({k}) | {md_escape(desc)} | `{page}` | `{md_escape(sel)}` | {crit} | {exp} |')
    lines.append('')
    lines.append(f'## All planted issues and traps ({len(rows)} rows)\n')
    lines.append('| # | page | selector | criterion | kind | expected | rationale |\n|---|---|---|---|---|---|---|')
    for i, r in enumerate(rows, 1):
        sel = f'`{md_escape(r["selector"])}`' if r['selector'] else '—'
        lines.append(f'| {i} | `{r["page"]}` | {sel} | {r["criterion"]} | {r["kind"]} | {r["expected"]} | {md_escape(r["rationale"])} |')
    lines.append('')
    lines.append('### Rows per criterion\n')
    lines.append('| criterion | rows | issue | trap | set |\n|---|---|---|---|---|')

    def key(c):
        return tuple(int(x) for x in c.split('.'))
    for crit in sorted(by_crit, key=key):
        iss = sum(1 for r in rows if r['criterion'] == crit and r['kind'] == 'issue')
        trp = sum(1 for r in rows if r['criterion'] == crit and r['kind'] == 'trap')
        st = sum(1 for r in rows if r['criterion'] == crit and r['kind'] == 'set')
        lines.append(f'| {crit} | {by_crit[crit]} | {iss} | {trp} | {st} |')
    lines.append('')
    lines.append('## Barrierefreiheitserklärung – deliberate gaps (informational)\n')
    lines.append('`barrierefreiheit.html` (and the FR/IT translations `fr/accessibilite.html`, `it/accessibilita.html`) is a realistic '
                 'accessibility statement (scope, conformance status "teilweise konform", list of non-accessible content, feedback form). '
                 'Its gaps are **not a WCAG success criterion**; they are statement gaps measured against the EU 2018/1523 model statement and '
                 'eCH-0059 practice. They are listed here for information only and are not part of `issues.jsonl`.\n')
    for g in GAPS:
        lines.append(f'- {g}')
    lines.append('')
    os.makedirs(TRUTH, exist_ok=True)
    for stale in ('ISSUES.md', 'issues.jsonl'):          # never leave answer keys in the served folder
        if os.path.exists(os.path.join(SITE, stale)):
            os.remove(os.path.join(SITE, stale))
    with open(os.path.join(TRUTH, 'ISSUES.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lines))
    with open(os.path.join(TRUTH, 'issues.jsonl'), 'w', encoding='utf-8', newline='\n') as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + '\n')
    return by_crit


SITE_README = """# Gemeinde Musterwil – demo website

Licence: the content of this folder (texts, SVG images, PDF, CSS, JS) is licensed under CC-BY-4.0.
Musterwil is a fictional municipality: all names, people, addresses, phone numbers and figures are invented.
The pages are generated by `scripts/demo_site/build.py`; the CSS and JS are hand-written.
"""


def main():
    os.makedirs(SITE, exist_ok=True)
    with open(os.path.join(SITE, 'README.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(SITE_README)
    svgs.write_all(os.path.join(SITE, 'assets', 'img'))
    os.makedirs(os.path.join(SITE, 'assets', 'docs'), exist_ok=True)
    pdf_size = make_pdf(os.path.join(SITE, 'assets', 'docs', 'abfallreglement-musterwil.pdf'))
    pdf_kb = max(1, -(-pdf_size // 1024))
    pages = {}
    for prefix, mod in (('', content_de), ('fr/', content_fr), ('it/', content_it)):
        for name, html in mod.build(R).items():
            pages[prefix + name] = html.replace('{PDF_KB}', str(pdf_kb))
    for rel, html in pages.items():
        path = os.path.join(SITE, *rel.split('/'))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(html)
    # replace the size placeholder inside rationales too
    for r in ROWS:
        r['rationale'] = r['rationale'].replace('n KB', f'{pdf_kb} KB')
    by_crit = write_docs(ROWS)
    print(f'pages: {len(pages)}  rows: {len(ROWS)}  pdf: {pdf_size} bytes ({pdf_kb} KB)')
    print(dict(sorted(by_crit.items(), key=lambda kv: tuple(int(x) for x in kv[0].split('.')))))


if __name__ == '__main__':
    main()
