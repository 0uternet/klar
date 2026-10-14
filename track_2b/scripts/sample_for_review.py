#!/usr/bin/env python3
"""Draw a stratified sample of generated TEST cases for blind human label review,
and score the review once it is filled in (stdlib only).

Usage (from track_2b/):
    python -I scripts/sample_for_review.py                 # writes data/testset/review_sample.csv
    python -I scripts/sample_for_review.py --n 50 --seed 20261014
    python -I scripts/sample_for_review.py --score data/testset/review_sample.csv
          # → observed agreement and Cohen's kappa between reviewer_label and the frozen labels

Sampling: only source=generated, split=test (ACT labels come from W3C). Every criterion
gets at least one case; the remaining slots are allocated proportionally to criterion
size (largest remainder). Each pick takes, inside its criterion, the case whose expected
outcome (then page language) is most under-represented relative to the pool, so the
sample's outcome and language mix mirrors the test split. The CSV is BLIND: it does not
contain the expected label, the rule id, the trap flag or the notes.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "testset_gen"))
import common  # noqa: E402
import htmlcheck  # noqa: E402

ROOT = HERE.parent
TESTSET = ROOT / "data" / "testset"
OUT = TESTSET / "review_sample.csv"
FIELDS = ["case_id", "criterion", "criterion_name", "page_lang", "rendered_snippet_path", "target_selector",
          "target_snippet", "reviewer_label", "comment"]
VALID = {"failed", "passed", "cantTell", "inapplicable"}


def allocate(sizes: dict[str, int], n: int) -> dict[str, int]:
    keys = sorted(sizes, key=list(common.CRITERIA).index)
    alloc = {k: 1 for k in keys}
    rest = n - len(keys)
    total = sum(sizes.values())
    quotas = {k: rest * sizes[k] / total for k in keys}
    for k in keys:
        alloc[k] += int(math.floor(quotas[k]))
    left = n - sum(alloc.values())
    for k in sorted(keys, key=lambda k: (-(quotas[k] - math.floor(quotas[k])), keys.index(k)))[:left]:
        alloc[k] += 1
    return {k: min(alloc[k], sizes[k]) for k in keys}


def snippet(row) -> str:
    path = TESTSET / row["path"]
    root, _, _ = htmlcheck.parse(path.read_text(encoding="utf-8"))
    if row["target_selector"]:
        nodes = htmlcheck.select(root, row["target_selector"])
        if nodes:
            return " ".join(htmlcheck.outer_html(nodes[0], 400).split())
    for n in root.iter():
        if n.tag == "title":
            return "<title>" + n.text().strip() + "</title> (page-level criterion)"
    return "(page-level criterion)"


def draw(n: int, seed: int) -> list[dict]:
    rows = [json.loads(l) for l in (TESTSET / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    pool = [r for r in rows if r["source"] == "generated" and r["split"] == "test"]
    by_crit = defaultdict(list)
    for r in sorted(pool, key=lambda r: r["case_id"]):
        by_crit[r["criterion"]].append(r)
    alloc = allocate({k: len(v) for k, v in by_crit.items()}, n)
    rng = random.Random(f"klar-review-{seed}")
    # global targets: outcome shares and page languages follow the pool
    exp_share = Counter(r["expected"] for r in pool)
    lang_share = Counter(r["page_lang"] for r in pool)
    exp_target = {e: n * c / len(pool) for e, c in exp_share.items()}
    lang_target = {l: n * c / len(pool) for l, c in lang_share.items()}
    exp_got, lang_got = Counter(), Counter()
    remaining = {c: rng.sample(v, len(v)) for c, v in by_crit.items()}
    chosen = []
    # round 1 gives every criterion one case, later rounds fill the proportional allocation;
    # each pick takes the outcome (then language) with the largest deficit
    rounds = max(alloc.values())
    for rnd in range(rounds):
        crits = [c for c, k in alloc.items() if k > rnd]
        rng.shuffle(crits)
        for c in crits:
            cands = remaining[c]
            if not cands:
                continue
            best = max(cands, key=lambda r: (exp_target.get(r["expected"], 0) - exp_got[r["expected"]],
                                             lang_target.get(r["page_lang"], 0) - lang_got[r["page_lang"]]))
            cands.remove(best)
            chosen.append(best)
            exp_got[best["expected"]] += 1
            lang_got[best["page_lang"]] += 1
    rng.shuffle(chosen)                    # reviewer sees criteria interleaved
    return chosen


def write_csv(rows: list[dict]) -> None:
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({
                "case_id": r["case_id"],
                "criterion": r["criterion"],
                "criterion_name": common.CRITERIA[r["criterion"]][0],
                "page_lang": r["page_lang"],
                "rendered_snippet_path": "data/testset/" + r["path"],
                "target_selector": r["target_selector"] or "",
                "target_snippet": snippet(r),
                "reviewer_label": "",
                "comment": "",
            })


def cohen_kappa(pairs: list[tuple[str, str]]) -> tuple[float, float]:
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return po, (po - pe) / (1 - pe) if pe < 1 else 1.0


def score(path: Path) -> int:
    rows = {json.loads(l)["case_id"]: json.loads(l)
            for l in (TESTSET / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    pairs, bad = [], 0
    disagreements = []
    with path.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            lab = r["reviewer_label"].strip()
            if not lab:
                continue
            if lab not in VALID:
                bad += 1
                continue
            exp = rows[r["case_id"]]["expected"]
            pairs.append((exp, lab))
            if exp != lab:
                disagreements.append((r["case_id"], exp, lab, r["comment"]))
    if not pairs:
        print("no reviewer labels filled in yet")
        return 0
    po, k = cohen_kappa(pairs)
    print(f"reviewed: {len(pairs)} (invalid labels skipped: {bad})")
    print(f"observed agreement: {po:.3f}   Cohen's kappa: {k:.3f}")
    collapsed = [("failed" if a == "failed" else "not-failed", "failed" if b == "failed" else "not-failed") for a, b in pairs]
    po2, k2 = cohen_kappa(collapsed)
    print(f"binary failed vs not-failed: agreement {po2:.3f}, kappa {k2:.3f}")
    for d in disagreements:
        print("  disagreement:", *d)
    return 0


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20261014)
    ap.add_argument("--score", type=Path, default=None, help="score a filled review CSV")
    args = ap.parse_args(argv)
    if args.score:
        return score(args.score)
    rows = draw(args.n, args.seed)
    write_csv(rows)
    c = Counter(r["criterion"] for r in rows)
    e = Counter(r["expected"] for r in rows)
    print(f"wrote {OUT.relative_to(ROOT).as_posix()}: {len(rows)} cases, {len(c)} criteria, "
          f"labels (hidden in the CSV): {dict(e)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
