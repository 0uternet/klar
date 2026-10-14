#!/usr/bin/env python3
"""Import W3C ACT Rules test cases for the judgement rules of Klar.'s criteria (stdlib only).

Usage (from track_2b/):
    python -I scripts/import_act.py              # download (cached files are reused) and prune
    python -I scripts/import_act.py --refresh    # re-download everything
    python -I scripts/import_act.py --offline    # rebuild manifest_act.jsonl from files on disk

What it does
  1. downloads https://act-rules.github.io/testcases.json (the full index, ~1 MB) and keeps
     only the entries of the selected rules in act/testcases-filtered.json — a DERIVED file
     (filtered, otherwise unmodified entries) that records the source URL, retrieval date and
     the sha256 of the full original;
  2. selects the ACT rules that map, *for conformance*, to one of the 26 in-scope WCAG 2.1
     criteria AND need judgement (JUDGEMENT_RULES below). Presence/syntax rules (accessible
     name present, valid lang tag, ARIA validity …) are axe-core territory and are not
     imported (pass --all-rules to import every mapped rule anyway);
  3. downloads each test case of those rules, sequentially with a polite delay, into
     data/testset/act/testcases/<ruleId>/<testcaseId>.<ext> — byte-for-byte UNMODIFIED;
  4. downloads the /test-assets/ files these test cases reference (unmodified; serve
     data/testset/act/ as web root so the root-relative URLs used by ACT resolve) and deletes
     files of rules or assets that are no longer selected;
  5. writes act/manifest_act.jsonl (one row per test case x in-scope criterion, split=test,
     expected = the ACT *rule* outcome) and act/LICENSE-W3C.md;
  6. rebuilds data/testset/manifest.jsonl and STATS.md (scripts/build_manifest.py).

Licence: ACT Rules test cases are (c) W3C, published under the W3C Software and Document
Notice and License; see data/testset/act/LICENSE-W3C.md.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import html as _html
import json
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "testset_gen"))
sys.path.insert(0, str(HERE))
import common  # noqa: E402

ROOT = HERE.parent
ACT_DIR = ROOT / "data" / "testset" / "act"
BASE = "https://act-rules.github.io/"
TESTCASES_URL = BASE + "testcases.json"
LICENSE_URL = BASE + "pages/license/"
UA = "Klar-eval-importer/1.0 (+research; polite, sequential)"
DELAY = 0.25           # seconds between requests
MAX_ASSET_BYTES = 3_000_000
FILTERED = "testcases-filtered.json"

IN_SCOPE = set(common.CRITERIA)
# ACT rules whose expectation needs human-like judgement (meaning, language, visual reading,
# behaviour) for one of the in-scope criteria. The rest of the mapped rules check presence or
# syntax and are covered by axe-core; they are not part of Klar.'s evaluation.
JUDGEMENT_RULES = {
    "5effbb": "2.4.4 link in context is descriptive",
    "fd3a94": "2.4.4 identical link names in the same context serve the same purpose",
    "qt1vmo": "1.1.1 image accessible name is descriptive",
    "e88epe": "1.1.1 image not in the accessibility tree is decorative",
    "b49b2e": "2.4.6 heading is descriptive",
    "cc0f0a": "2.4.6 form field label is descriptive",
    "off6ek": "3.1.2 element language subtag matches the language of its text",
    "ucwvc8": "3.1.1 page language subtag matches the default language of the content",
    "c4a8a4": "2.4.2 page title is descriptive",
    "9bd38c": "1.3.3 content has an alternative for visual references",
    "0va7u6": "1.4.5 HTML graphics contain no text",
    "2ee8b8": "2.5.3 visible label is part of the accessible name",
    "36b590": "3.3.1 error message describes the invalid value",
    "efbfc7": "2.2.2 automatically changing text can be paused, stopped or hidden",
}


def fetch(url: str, *, retries: int = 3) -> bytes:
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError) as e:  # pragma: no cover - network
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {last}")


def in_scope_criteria(reqs: dict | None) -> list[str]:
    out = []
    for key, val in (reqs or {}).items():
        if not (key.startswith("wcag20:") or key.startswith("wcag21:")):
            continue
        crit = key.split(":", 1)[1]
        if crit in IN_SCOPE and val.get("forConformance", False) and not val.get("secondary", False):
            out.append(crit)
    order = list(common.CRITERIA)
    return sorted(set(out), key=order.index)


ASSET_ATTR_RE = re.compile(r"""\b(?:src|href|data|poster)\s*=\s*["']([^"']+)["']""", re.I)
SRCSET_RE = re.compile(r"""\bsrcset\s*=\s*["']([^"']+)["']""", re.I)
CSS_URL_RE = re.compile(r"""url\(\s*["']?([^"')]+)["']?\s*\)""", re.I)


def referenced_assets(text: str) -> set[str]:
    refs = set(ASSET_ATTR_RE.findall(text)) | set(CSS_URL_RE.findall(text))
    for s in SRCSET_RE.findall(text):
        refs |= {p.strip().split()[0] for p in s.split(",") if p.strip()}
    out = set()
    for r in refs:
        r = _html.unescape(r.strip())
        if r.startswith(BASE + "test-assets/"):
            r = "/" + r[len(BASE):]
        if r.startswith("/test-assets/"):
            out.add(r.split("#")[0].split("?")[0])
    return out


def license_text() -> str:
    raw = fetch(LICENSE_URL).decode("utf-8")
    raw = re.sub(r"<style.*?</style>|<script.*?</script>", "", raw, flags=re.S)
    seg = raw[raw.find("<main"):] if "<main" in raw else raw
    txt = re.sub(r"<(br|/p|/h\d|/li|/ul|/div)[^>]*>", "\n", seg)
    txt = re.sub(r"<li[^>]*>", "- ", txt)
    txt = _html.unescape(re.sub(r"<[^>]+>", "", txt))
    txt = re.sub(r"[ \t]+\n", "\n", txt)
    txt = re.sub(r"\n\s*\n+", "\n\n", txt)
    start = txt.find("W3C Software And Document Notice And License")
    end_marker = "will at all times remain with copyright holders."
    end = txt.find(end_marker)
    if start < 0 or end < 0:
        raise RuntimeError("could not locate licence text on " + LICENSE_URL)
    return txt[start:end + len(end_marker)].strip()


def write_license(text: str, rules: dict, prov: dict) -> None:
    rule_lines = "\n".join(f"- `{rid}` — {name} (<{BASE}rules/{rid}/>)" for rid, name in sorted(rules.items()))
    md = f"""# W3C licence for the imported ACT Rules test cases

The files in `data/testset/act/testcases/` and `data/testset/act/test-assets/` are **unmodified
copies** of material published by the W3C ACT Rules Community Group at <{BASE}>
(retrieved {prov['retrieved']} by `scripts/import_act.py`). They are redistributed under the
W3C Software and Document Notice and License (SPDX `W3C-20150513`) reproduced in full below.

Copyright notice for the copied material: *This dataset includes material copied from the
ACT Rules Community test cases, <{TESTCASES_URL}> and <{BASE}rules/>.
Copyright © 2017–{prov['retrieved'][:4]} W3C® (MIT, ERCIM, Keio, Beihang).*

**Modifications and derived files.**
- The test-case files and test assets are **not modified**.
- `testcases-filtered.json` is **derived** from `{TESTCASES_URL}`: it keeps only the entries
  of the imported rules (entries themselves unchanged) and adds a provenance header. The full
  original had sha256 `{prov['source_sha256']}` and {prov['source_count']} entries on
  {prov['retrieved']}.
- `manifest_act.jsonl` is **derived** metadata written by Klar. (rule id, in-scope WCAG
  criterion, expected rule outcome taken from the index).
- No translations of ACT test cases are included. If translated copies are ever added, they
  must be stored in a separate folder and marked as modified.

**Interpretation note.** The `expected` value of an ACT case is the outcome of the *ACT rule*,
not of the WCAG success criterion: per `ruleAccessibilityRequirements`, a rule outcome `failed`
means the criterion is "not satisfied", while `passed` and `inapplicable` mean "further testing
needed".

**Selection.** Only rules that need judgement are imported (presence/syntax rules are covered
by axe-core). Test assets of rules that are not imported (videos, audio) are not copied. The
largest kept asset, `test-assets/0va7u6/ivanhoe.png` (0.9 MB), is the image-of-text fixture of
rule 0va7u6 (1.4.5) and is needed to render those cases.

Rules imported:

{rule_lines}

---

{text}
"""
    (ACT_DIR / "LICENSE-W3C.md").write_text(md, encoding="utf-8", newline="\n")


def detect_lang(text: str) -> str:
    m = re.search(r"<html\b[^>]*\blang\s*=\s*[\"']([^\"']*)[\"']", text, re.I)
    if not m:
        return "und"
    prim = m.group(1).strip().split("-")[0].lower()
    return prim if re.fullmatch(r"[a-z]{2,3}", prim) else "und"


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh", action="store_true", help="re-download files that already exist")
    ap.add_argument("--offline", action="store_true", help="no network: use testcases-filtered.json and files on disk")
    ap.add_argument("--all-rules", action="store_true", help="import every rule mapped to an in-scope criterion")
    ap.add_argument("--no-merge", action="store_true")
    args = ap.parse_args(argv)

    ACT_DIR.mkdir(parents=True, exist_ok=True)
    fpath = ACT_DIR / FILTERED
    if args.offline:
        filt = json.loads(fpath.read_text(encoding="utf-8"))
        entries, prov = filt["testcases"], filt["provenance"]
    else:
        raw = fetch(TESTCASES_URL)
        data = json.loads(raw.decode("utf-8"))
        entries = data["testcases"]
        prov = {"source_url": TESTCASES_URL, "source_sha256": hashlib.sha256(raw).hexdigest(),
                "source_count": len(entries), "retrieved": _dt.date.today().isoformat(),
                "license": data.get("license"), "filter": None}
    old_full = ACT_DIR / "testcases.json"
    if old_full.exists():
        old_full.unlink()                                  # the full index is no longer shipped

    selected, rules = [], {}
    for t in entries:
        if t["ruleName"].upper().startswith("DEPRECATED"):
            continue
        crits = in_scope_criteria(t.get("ruleAccessibilityRequirements"))
        if not crits:
            continue
        if not args.all_rules and t["ruleId"] not in JUDGEMENT_RULES:
            continue
        selected.append((t, crits))
        rules[t["ruleId"]] = t["ruleName"]
    prov = dict(prov, filter=("all rules mapped to an in-scope criterion" if args.all_rules
                              else "judgement rules: " + ", ".join(sorted(JUDGEMENT_RULES))))
    print(f"{prov['source_count']} ACT test cases in the index; {len(selected)} selected from {len(rules)} rules")

    rows, assets_wanted, keep_files, n_dl = [], set(), set(), 0
    for t, crits in selected:
        rel = Path(t["relativePath"])            # testcases/<rule>/<id>.<ext>
        out = ACT_DIR / rel
        keep_files.add(out.resolve())
        if not out.exists() or args.refresh:
            if args.offline:
                print(f"  missing (offline): {rel}")
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(fetch(t["url"]))
            n_dl += 1
            time.sleep(DELAY)
        text = out.read_bytes().decode("utf-8", errors="replace")
        assets_wanted |= referenced_assets(text)
        lang = detect_lang(text) if rel.suffix in (".html", ".xhtml") else "und"
        for crit in crits:
            rows.append({
                "case_id": f"act-{t['ruleId']}-{t['testcaseId'][:10]}-{crit}",
                "criterion": crit,
                "page_lang": lang,
                "source": "act",
                "act_rule": t["ruleId"],
                "split": "test",
                "expected": t["expected"],
                "path": "act/" + rel.as_posix(),
                "target_selector": None,
                "notes": (f"ACT rule {t['ruleId']} “{t['ruleName']}”, {t['testcaseTitle']}. "
                          f"Expected = rule outcome (failed ⇒ SC not satisfied; passed/inapplicable ⇒ "
                          f"further testing needed). Unmodified W3C copy of {t['url']}"),
                "rule": f"ACT:{t['ruleId']}",
                "trap": False,
                "alt_expected": None,
                "difficulty": "medium",
                "pages": 1,
                "template_id": f"act/{t['ruleId']}",
            })
    print(f"downloaded {n_dl} test case files")

    # assets referenced by the selected cases (one level of recursion for nested HTML/CSS)
    seen, skipped, queue = set(), [], sorted(assets_wanted)
    while queue:
        a = queue.pop(0)
        if a in seen:
            continue
        seen.add(a)
        out = ACT_DIR / a.lstrip("/")
        if not out.exists() or args.refresh:
            if args.offline:
                continue
            try:
                body = fetch(urllib.parse.urljoin(BASE, urllib.parse.quote(a)))
            except RuntimeError as e:
                skipped.append(f"{a} ({e})")
                continue
            if len(body) > MAX_ASSET_BYTES:
                skipped.append(f"{a} ({len(body)} bytes, over size cap)")
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(body)
            time.sleep(DELAY)
        if out.exists():
            keep_files.add(out.resolve())
            if out.suffix in (".html", ".css", ".svg", ".xhtml"):
                for b in sorted(referenced_assets(out.read_bytes().decode("utf-8", errors="replace"))):
                    if b not in seen:
                        queue.append(b)
        if a.endswith("/") and (out / "index.html").exists():
            keep_files.add((out / "index.html").resolve())

    # prune files that belong to rules/assets no longer selected
    removed = 0
    for sub in ("testcases", "test-assets"):
        base = ACT_DIR / sub
        if not base.exists():
            continue
        for f in sorted(base.rglob("*"), reverse=True):
            if f.is_file() and f.resolve() not in keep_files:
                f.unlink()
                removed += 1
            elif f.is_dir() and not any(f.iterdir()):
                f.rmdir()
    size = sum(f.stat().st_size for f in ACT_DIR.rglob("*") if f.is_file())
    print(f"test assets referenced: {len(seen)}; skipped {len(skipped)}; files pruned: {removed}; act/ now {size / 1e6:.1f} MB")
    for s in skipped:
        print("  skipped asset:", s)

    kept_entries = [t for t, _ in selected]
    fpath.write_text(json.dumps({"provenance": prov, "testcases": kept_entries}, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8", newline="\n")
    with (ACT_DIR / "manifest_act.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"manifest_act.jsonl: {len(rows)} rows; {FILTERED}: {len(kept_entries)} entries")

    if not args.offline:
        write_license(license_text(), rules, prov)
        print("LICENSE-W3C.md written")
    if not args.no_merge:
        import build_manifest
        build_manifest.main([])
    return 0


if __name__ == "__main__":
    sys.exit(main())
