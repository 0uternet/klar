#!/usr/bin/env python3
"""Validate the Klar. evaluation set and the demo site (stdlib only).

Usage (from track_2b/):  python -I scripts/validate_testset.py [--quiet]

Checks
  manifest.jsonl  – required fields and enums, unique case_id, path exists,
                    split/source consistency, ACT rows are split=test
  generated cases – strict well-formedness (every non-void element closed), DOCTYPE,
                    target_selector matches exactly ONE element, no label leakage,
                    no external resources, every referenced local file exists,
                    all pages of multi-page cases parse
  ACT cases       – file exists, lenient parse, root-relative /test-assets/ resolve
  demo site       – every data/demo-truth/issues.jsonl selector matches exactly one element,
                    no answer key inside the served folder,
                    local links/images resolve, no external resource URLs
  sizes           – data/ total < 100 MB (warning above 20 MB), large files listed
Exit status 1 if any error is found.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "testset_gen"))
sys.path.insert(0, str(HERE))
import common  # noqa: E402
import htmlcheck  # noqa: E402
from generate_testset import leak_scan, LEAK_RE  # noqa: E402

ROOT = HERE.parent
DATA = ROOT / "data"
TESTSET = DATA / "testset"
DEMO = DATA / "demo-site"
DEMO_TRUTH = DATA / "demo-truth"     # answer keys, outside the served folder

OUTCOMES = set(common.OUTCOMES)
REQUIRED = ["case_id", "criterion", "page_lang", "source", "act_rule", "split", "expected", "path",
            "target_selector", "notes"]
REF_RE = re.compile(r"""\b(src|href|data|poster|action)\s*=\s*["']([^"']*)["']""", re.I)
EXT_RES_RE = re.compile(r"""<(?:img|script|link|iframe|source|video|audio|object|embed)\b[^>]*\b(?:src|href|data)\s*=\s*["']\s*(?:https?:)?//""", re.I)
CSS_EXT_RE = re.compile(r"""url\(\s*["']?\s*(?:https?:)?//""", re.I)


class Report:
    def __init__(self, quiet=False):
        self.errors, self.warnings, self.quiet = [], [], quiet

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)


TAG_RE = re.compile(r"<([a-zA-Z][\w-]*)\b([^>]*)>")
ATTR_RE = re.compile(r"""\b(src|href|data|poster)\s*=\s*["']([^"']*)["']""", re.I)
NAV_TAGS = {"a", "area", "form"}


def local_refs_ok(html: str, base: Path, rep: Report, label: str, *, site_root: Path | None = None,
                  check_pages: bool = False, soft: bool = False) -> None:
    """Resource references (img/src, link/href, script/src, object/data …) must resolve.
    Navigation hrefs (<a>, <area>) are only checked for multi-page cases (check_pages)."""
    report = rep.warn if soft else rep.err
    for tag, attrs_ in TAG_RE.findall(html):
        tag = tag.lower()
        for attr, url in ATTR_RE.findall(attrs_):
            url = url.strip()
            if not url or url.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
                continue
            parts = urlsplit(url)
            if parts.scheme or parts.netloc:
                continue
            path = unquote(parts.path)
            if not path:
                continue
            if tag in NAV_TAGS or (attr.lower() == "href" and tag != "link"):
                if not check_pages or not (path.endswith((".html", "/"))):
                    continue
            if path.startswith("/"):
                if site_root is None:
                    continue
                target = site_root / path.lstrip("/")
            else:
                target = base / path
            if path.endswith("/"):
                target = target / "index.html"
            if not target.resolve().exists():
                report(f"{label}: broken local reference <{tag} {attr}={url!r}>")


def check_generated(row, rep: Report):
    entry = TESTSET / row["path"]
    files = [entry] if row.get("pages", 1) == 1 else sorted(entry.parent.rglob("*.html"))
    for f in files:
        text = f.read_text(encoding="utf-8")
        root, errors, doctype = htmlcheck.parse(text)
        rel = f.relative_to(TESTSET).as_posix()
        for e in errors:
            rep.err(f"{row['case_id']}: {rel}: {e}")
        if not doctype or doctype.lower() != "doctype html":
            rep.err(f"{row['case_id']}: {rel}: missing <!DOCTYPE html>")
        for p in leak_scan(text):
            rep.err(f"{row['case_id']}: {rel}: {p}")
        local_refs_ok(text, f.parent, rep, f"{row['case_id']}: {rel}",
                      check_pages=row.get("pages", 1) > 1)
        if f == entry and row["target_selector"]:
            try:
                n = len(htmlcheck.select(root, row["target_selector"]))
            except htmlcheck.SelectorError as e:
                rep.err(f"{row['case_id']}: unsupported selector {row['target_selector']!r}: {e}")
            else:
                if n != 1:
                    rep.err(f"{row['case_id']}: target {row['target_selector']!r} matches {n} elements")
    if row["target_selector"] and LEAK_RE.search(row["target_selector"]):
        rep.err(f"{row['case_id']}: label leakage in selector")


def check_act(row, rep: Report):
    f = TESTSET / row["path"]
    text = f.read_bytes().decode("utf-8", errors="replace")
    if f.suffix in (".html", ".xhtml"):
        _, errors, _ = htmlcheck.parse(text)
        if htmlcheck.lenient_errors(errors):
            rep.warn(f"{row['case_id']}: ACT file not strictly well-formed ({len(errors)} parser notes; unmodified W3C copy)")
    local_refs_ok(text, f.parent, rep, row["case_id"], site_root=TESTSET / "act", soft=True)


def check_demo(rep: Report):
    if not DEMO.exists():
        rep.warn("data/demo-site/ not found")
        return 0
    pages = sorted(DEMO.rglob("*.html"))
    for p in pages:
        text = p.read_text(encoding="utf-8")
        rel = p.relative_to(DEMO).as_posix()
        if EXT_RES_RE.search(text) or CSS_EXT_RE.search(text):
            rep.err(f"demo-site/{rel}: external resource reference")
        _, errors, doctype = htmlcheck.parse(text)
        for e in htmlcheck.lenient_errors(errors):
            rep.err(f"demo-site/{rel}: {e}")
        local_refs_ok(text, p.parent, rep, f"demo-site/{rel}", site_root=DEMO, check_pages=True)
    for css in DEMO.rglob("*.css"):
        if CSS_EXT_RE.search(css.read_text(encoding="utf-8")):
            rep.err(f"demo-site/{css.relative_to(DEMO).as_posix()}: external url() in CSS")
    for stale in ("ISSUES.md", "issues.jsonl"):
        if (DEMO / stale).exists():
            rep.err(f"data/demo-site/{stale}: answer key inside the served folder (move it to data/demo-truth/)")
    issues = DEMO_TRUTH / "issues.jsonl"
    n = 0
    if not issues.exists():
        rep.warn("data/demo-truth/issues.jsonl not found")
        return 0
    for i, line in enumerate(issues.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        n += 1
        r = json.loads(line)
        page = DEMO / r["page"]
        if r.get("expected") not in OUTCOMES:
            rep.err(f"issues.jsonl:{i}: bad expected {r.get('expected')!r}")
        if not page.exists():
            rep.err(f"issues.jsonl:{i}: page {r['page']} missing")
            continue
        if r.get("selector"):
            root, _, _ = htmlcheck.parse(page.read_text(encoding="utf-8"))
            try:
                k = len(htmlcheck.select(root, r["selector"]))
            except htmlcheck.SelectorError as e:
                rep.err(f"issues.jsonl:{i}: unsupported selector {r['selector']!r}: {e}")
                continue
            if k != 1:
                rep.err(f"issues.jsonl:{i}: {r['page']} {r['selector']!r} matches {k} elements")
    return n


def dir_size(p: Path) -> int:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quiet", action="store_true", help="print only the summary and errors")
    args = ap.parse_args(argv)
    rep = Report(args.quiet)

    mpath = TESTSET / "manifest.jsonl"
    rows = [json.loads(l) for l in mpath.read_text(encoding="utf-8").splitlines() if l.strip()]
    ids = Counter(r.get("case_id") for r in rows)
    for k, v in ids.items():
        if v > 1:
            rep.err(f"duplicate case_id {k}")
    for r in rows:
        for f in REQUIRED:
            if f not in r:
                rep.err(f"{r.get('case_id')}: missing field {f}")
        if r["expected"] not in OUTCOMES:
            rep.err(f"{r['case_id']}: bad expected {r['expected']!r}")
        if r["criterion"] not in common.CRITERIA:
            rep.err(f"{r['case_id']}: criterion {r['criterion']} out of scope")
        if r["source"] not in ("generated", "act"):
            rep.err(f"{r['case_id']}: bad source")
        if r["split"] not in ("dev", "test"):
            rep.err(f"{r['case_id']}: bad split")
        if r["source"] == "act" and (r["split"] != "test" or not r["act_rule"]):
            rep.err(f"{r['case_id']}: ACT rows must be split=test with act_rule")
        if not (TESTSET / r["path"]).exists():
            rep.err(f"{r['case_id']}: path {r['path']} does not exist")
            continue
        if r["source"] == "generated":
            if r["page_lang"] not in common.LANGS:
                rep.err(f"{r['case_id']}: bad page_lang")
            check_generated(r, rep)
        else:
            check_act(r, rep)

    n_issues = check_demo(rep)

    total = dir_size(DATA)
    if total > 100e6:
        rep.err(f"data/ is {total / 1e6:.1f} MB (> 100 MB limit)")
    elif total > 20e6:
        rep.warn(f"data/ is {total / 1e6:.1f} MB (> 20 MB target)")
    big = [(f.stat().st_size, f) for f in DATA.rglob("*") if f.is_file() and f.stat().st_size > 1_000_000]
    for s, f in sorted(big, reverse=True):
        rep.warn(f"large file {f.relative_to(ROOT).as_posix()} ({s / 1e6:.1f} MB)")

    gen = [r for r in rows if r["source"] == "generated"]
    act = [r for r in rows if r["source"] == "act"]
    sel = [r for r in gen if r["target_selector"]]
    print(f"manifest rows: {len(rows)} (generated {len(gen)}, act {len(act)}); "
          f"generated with target selector: {len(sel)}; demo-site issue/trap rows: {n_issues}")
    print(f"sizes: data/ {total / 1e6:.1f} MB · testset {dir_size(TESTSET) / 1e6:.1f} MB · "
          f"demo-site {dir_size(DEMO) / 1e6 if DEMO.exists() else 0:.1f} MB")
    if rep.warnings and not args.quiet:
        shown = rep.warnings[:15]
        print(f"warnings: {len(rep.warnings)}" + (" (first 15)" if len(rep.warnings) > 15 else ""))
        for w in shown:
            print("  -", w)
    elif rep.warnings:
        print(f"warnings: {len(rep.warnings)}")
    if rep.errors:
        print(f"ERRORS: {len(rep.errors)}")
        for e in rep.errors[:200]:
            print("  !!", e)
        return 1
    print("OK: no errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
