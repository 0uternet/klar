#!/usr/bin/env python3
"""Deterministic generator of the Klar. synthetic evaluation set (stdlib only).

Usage (from track_2b/):
    python -I scripts/generate_testset.py               # all criteria
    python -I scripts/generate_testset.py --only 2.4.4,3.1.2   # some criteria (others kept)
    python -I scripts/generate_testset.py --seed 20261014
    python -I scripts/generate_testset.py --only 1.1.1 --out /tmp/scratch   # develop a module

Writes:
    data/testset/generated/<criterion>/<case_id>.html          single-page cases
    data/testset/generated/<criterion>/<case_id>/index.html …  multi-page (site-level) cases
    data/testset/generated/_assets/*.svg                       generated images
    data/testset/generated/manifest_generated.jsonl
and then rebuilds data/testset/manifest.jsonl and data/testset/STATS.md
(see scripts/build_manifest.py).

Labels are assigned by construction following data/testset/PROTOCOL.md.
The dev/test split is a GROUP split (scripts/testset_gen/grouping.py): cases are grouped into
template families (explicit Case.template, or signature-text Jaccard >= 0.6) and whole groups
go to dev (~20 % per criterion and outcome, seeded) or test, so dev and test share no template.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import random
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "testset_gen"))
sys.path.insert(0, str(HERE))

import common  # noqa: E402
import grouping  # noqa: E402
import injection  # noqa: E402
import htmlcheck  # noqa: E402

ROOT = HERE.parent                      # track_2b/
TESTSET = ROOT / "data" / "testset"
GEN = TESTSET / "generated"
ASSETS_DIR = GEN / "_assets"
DEFAULT_SEED = 20261014

LEAK_TOKENS = {"fail", "failed", "fails", "failure", "pass", "passed", "passes", "trap", "traps",
               "canttell", "cant", "expected", "wrong", "correct", "incorrect", "bad", "good", "issue",
               "issues", "verdict", "label-ok", "violation", "compliant", "noncompliant"}


class _LeakRe:
    """Token-based detector for verdict words in attribute values / selectors."""
    _split = re.compile(r"[^A-Za-z]+|(?<=[a-z])(?=[A-Z])")

    def search(self, value: str):
        toks = [t.lower() for t in self._split.split(value or "") if t]
        hit = [t for t in toks if t in LEAK_TOKENS or t.startswith("fail")]
        return hit or None


LEAK_RE = _LeakRe()
EXTERNAL_RES_RE = re.compile(r"""(?:src|srcset|data|poster)\s*=\s*["']\s*(?:https?:)?//""", re.I)
EXTERNAL_LINK_RES_RE = re.compile(r"""<(?:link|script)\b[^>]*(?:href|src)\s*=\s*["']\s*(?:https?:)?//""", re.I)


def module_name(crit: str) -> str:
    return "c_" + crit.replace(".", "_")


def load_cases(crit: str, seed: int):
    try:
        mod = importlib.import_module(module_name(crit))
    except ModuleNotFoundError as e:
        if e.name == module_name(crit):
            return None
        raise
    assert getattr(mod, "CRITERION", crit) == crit, f"{mod.__name__}.CRITERION mismatch"
    rng = random.Random(f"klar-testset-{seed}-{crit}")
    cases = mod.build(rng)
    core = [c for c in cases if "addon" not in c.tags]
    addons = [c for c in cases if "addon" in c.tags]
    # designed prompt-injection subset (SEC-1), then add-on cases (tag "addon"), appended in this
    # order so that existing case ids keep their numbers when a subset is added later
    cases = core + injection.cases_for(crit, random.Random(f"klar-injection-{seed}-{crit}")) + addons
    for c in cases:
        assert c.criterion == crit, f"{mod.__name__}: case with criterion {c.criterion}"
    return cases


def rel_assets(file_rel: Path) -> str:
    """Relative URL from a file inside generated/ to generated/_assets."""
    depth = len(file_rel.parent.parts)
    return "/".join([".."] * depth + ["_assets"]) if depth else "_assets"


def leak_scan(html: str) -> list[str]:
    probs = []
    if "<!--" in html:
        probs.append("HTML comment present")
    for m in re.finditer(r"""\s(id|class|name|for|data-[\w-]+|aria-labelledby|aria-describedby|aria-controls)\s*=\s*["']([^"']*)["']""", html):
        if LEAK_RE.search(m.group(2)):
            probs.append(f"label leakage in {m.group(1)}={m.group(2)!r}")
    for m in re.finditer(r"""(?:src|href)\s*=\s*["']([^"']*)["']""", html):
        v = m.group(1)
        if v.startswith(("http", "#", "mailto:", "tel:", "javascript:")):
            continue
        if LEAK_RE.search(v.replace(common.ASSET_PLACEHOLDER, "")):
            probs.append(f"label leakage in url {v!r}")
    if EXTERNAL_RES_RE.search(html) or EXTERNAL_LINK_RES_RE.search(html):
        probs.append("external resource reference")
    return probs


def check_case(case, entry_html: str, all_pages: dict[str, str]) -> list[str]:
    probs = []
    for name, h in all_pages.items():
        root, errors, doctype = htmlcheck.parse(h)
        for e in errors:
            probs.append(f"{name}: {e}")
        if not doctype or doctype.lower() != "doctype html":
            probs.append(f"{name}: missing <!DOCTYPE html>")
        probs += [f"{name}: {p}" for p in leak_scan(h)]
        if "@@" in h.replace(common.ASSET_PLACEHOLDER, ""):
            probs.append(f"{name}: stray @@ placeholder")
    if case.target is not None:
        root, _, _ = htmlcheck.parse(entry_html)
        try:
            n = len(htmlcheck.select(root, case.target))
        except htmlcheck.SelectorError as e:
            probs.append(f"bad selector {case.target!r}: {e}")
        else:
            if n != 1:
                probs.append(f"target {case.target!r} matches {n} elements")
        if LEAK_RE.search(case.target):
            probs.append(f"label leakage in target selector {case.target!r}")
    if not case.notes:
        probs.append("missing notes")
    if not case.rule or not case.rule.startswith(case.criterion + "/"):
        probs.append(f"rule id {case.rule!r} must look like '{case.criterion}/F1'")
    return probs


def mix_line(crit: str, cases) -> str:
    n = len(cases)
    c = Counter(x.expected for x in cases)
    langs = Counter(x.lang for x in cases)
    traps = sum(1 for x in cases if x.trap and x.expected in ("passed", "inapplicable"))
    passed = c["passed"] + c["inapplicable"]
    warn = []
    if n and not (0.30 <= c["failed"] / n <= 0.50):
        warn.append("failed share off")
    if n and not (0.08 <= c["cantTell"] / n <= 0.25):
        warn.append("cantTell share off")
    if passed and traps / passed < 1 / 3 - 1e-9:
        warn.append("traps < 1/3 of passed")
    return (f"{crit:7s} n={n:3d}  failed={c['failed']:3d} ({100 * c['failed'] / max(1, n):3.0f}%)  "
            f"passed={c['passed']:3d}  cantTell={c['cantTell']:3d} ({100 * c['cantTell'] / max(1, n):3.0f}%)  "
            f"inapp={c['inapplicable']:2d}  traps={traps:3d}  langs={dict(sorted(langs.items()))}"
            + (f"   !! {', '.join(warn)}" if warn else ""))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--only", default="", help="comma-separated criteria to (re)generate; others are kept")
    ap.add_argument("--no-merge", action="store_true", help="do not rebuild manifest.jsonl / STATS.md")
    ap.add_argument("--out", default=None,
                    help="write to OUT/generated instead of data/testset/generated (implies --no-merge); "
                         "use a scratch folder while developing a criterion module")
    args = ap.parse_args(argv)
    global TESTSET, GEN, ASSETS_DIR
    if args.out:
        TESTSET = Path(args.out).resolve()
        GEN = TESTSET / "generated"
        ASSETS_DIR = GEN / "_assets"
        args.no_merge = True

    only = [c.strip() for c in args.only.split(",") if c.strip()]
    crits = only or list(common.CRITERIA)
    for c in crits:
        if c not in common.CRITERIA:
            ap.error(f"unknown criterion {c}")

    gen_manifest = GEN / "manifest_generated.jsonl"
    kept_rows = []
    if only and gen_manifest.exists():
        kept_rows = [json.loads(l) for l in gen_manifest.read_text(encoding="utf-8").splitlines() if l.strip()]
        kept_rows = [r for r in kept_rows if r["criterion"] not in crits]
    if not only and GEN.exists():
        shutil.rmtree(GEN)
    GEN.mkdir(parents=True, exist_ok=True)

    rows = []
    problems = 0
    print(f"seed={args.seed}")
    for crit in crits:
        cases = load_cases(crit, args.seed)
        crit_dir = GEN / crit
        if crit_dir.exists():
            shutil.rmtree(crit_dir)
        if cases is None:
            print(f"{crit:7s} -- no module {module_name(crit)}.py yet, skipped")
            continue
        crit_dir.mkdir(parents=True)
        counters = Counter()
        for case in cases:
            counters[case.lang] += 1
            case_id = f"gen-{crit}-{case.lang}-{counters[case.lang]:03d}"
            if case.html is not None:
                files = {Path(crit) / f"{case_id}.html": case.html}
                entry = Path(crit) / f"{case_id}.html"
            else:
                files = {Path(crit) / case_id / name: h for name, h in case.pages.items()}
                entry = Path(crit) / case_id / "index.html"
            rendered = {}
            for rel, h in files.items():
                rendered[rel] = h.replace(common.ASSET_PLACEHOLDER, rel_assets(rel))
            probs = check_case(case, rendered[entry], {str(k): v for k, v in rendered.items()})
            if probs:
                problems += len(probs)
                for p in probs:
                    print(f"  !! {case_id}: {p}")
            for rel, h in rendered.items():
                out = GEN / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(h, encoding="utf-8", newline="\n")
            rows.append({
                "case_id": case_id,
                "criterion": crit,
                "page_lang": case.lang,
                "source": "generated",
                "act_rule": None,
                "split": None,
                "expected": case.expected,
                "path": ("generated/" + entry.as_posix()),
                "target_selector": case.target,
                "notes": case.notes,
                "rule": case.rule,
                "trap": bool(case.trap),
                "alt_expected": case.alt_expected,
                "difficulty": case.difficulty,
                "pages": (len(files) if case.pages is not None else 1),
                "template_hint": (f"{case.template}" if case.template else None),
                "split_hint": case.split,
                "surface_forms": list(case.surface),
                "tags": list(case.tags),
            })
        print(mix_line(crit, cases))

    # assets: write all registered assets (deterministic content)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    for name, svg in sorted(common.ASSETS.items()):
        (ASSETS_DIR / f"{name}.svg").write_text(svg, encoding="utf-8", newline="\n")
    # check every asset referenced exists
    for r in rows:
        base = TESTSET / r["path"]
        folder = base.parent
        files = [base] if r["pages"] == 1 else [p for p in folder.rglob("*.html")]
        for f in files:
            for m in re.finditer(r"""(?:src|href|data)\s*=\s*["']([^"'#]*_assets/[^"']+)["']""", f.read_text(encoding="utf-8")):
                if not (f.parent / m.group(1)).resolve().exists():
                    problems += 1
                    print(f"  !! {r['case_id']}: missing asset {m.group(1)}")

    all_rows = kept_rows + rows
    n_templates = grouping.assign_templates(all_rows, TESTSET)
    grouping.group_split(all_rows, args.seed)
    print("templates per criterion: " + ", ".join(f"{c} {k}" for c, k in n_templates.items()))
    order = {c: i for i, c in enumerate(common.CRITERIA)}
    all_rows.sort(key=lambda r: (order[r["criterion"]], r["case_id"]))
    with gen_manifest.open("w", encoding="utf-8", newline="\n") as fh:
        for r in all_rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    n_dev = sum(1 for r in all_rows if r["split"] == "dev")
    print(f"generated cases: {len(all_rows)} (dev {n_dev}, test {len(all_rows) - n_dev}); assets: {len(common.ASSETS)}")
    if not args.no_merge:
        import build_manifest
        build_manifest.main([])
    if problems:
        print(f"!! {problems} problem(s) found")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
