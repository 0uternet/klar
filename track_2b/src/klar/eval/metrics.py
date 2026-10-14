"""Evaluation metrics (frozen before any test-split run).

Unit of evaluation: (case, criterion). The findings of that criterion about the
case's target element (the element itself, a descendant or an ancestor; all of
them for page-level cases) are aggregated to the WORST outcome:
failed > cantTell > passed > inapplicable (no finding at all).

Positive class = `failed`. Gold `cantTell` cases are excluded from the P/R/F1
confusion and reported separately as their flag rate.

  TP/FP/FN/TN       on gold ∈ {failed, passed, inapplicable}, predicted failed vs not
  precision, recall, F1
  explicit_false_pass  gold failed → predicted passed
  silent_miss          gold failed → no finding at all (predicted inapplicable)
  false_pass           explicit + silent (both shown)
  flagged_recall       gold failed → predicted failed OR cantTell (the human-review view)
  deferral_rate        predicted cantTell, over all cases
  gold_cantTell_flag_rate  gold cantTell → predicted failed or cantTell
  accuracy             exact outcome; decision_accuracy: failed / review / no-failure
                       (passed ≡ inapplicable)
Every proportion carries a Wilson 95 % interval. Paired comparisons against the
baseline use the exact McNemar test on decision correctness; no difference is
claimed unless p < 0.05.
"""

from __future__ import annotations

import math
from collections import Counter

OUTCOMES = ("failed", "cantTell", "passed", "inapplicable")


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion k/n."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4))


def rate(k: int, n: int) -> dict:
    return {"k": k, "n": n, "value": round(k / n, 4) if n else None, "ci95": wilson(k, n)}


def decision(outcome: str) -> str:
    return {"passed": "ok", "inapplicable": "ok"}.get(outcome, outcome)


def aggregate(outcomes: list[str]) -> str:
    """ACT-style aggregation of the findings about one target."""
    if "failed" in outcomes:
        return "failed"
    if "cantTell" in outcomes:
        return "cantTell"
    if "passed" in outcomes:
        return "passed"
    return "inapplicable"


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value from the discordant counts b and c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return round(min(1.0, 2 * tail), 6)


def summarize(pairs: list[tuple[str, str]]) -> dict:
    """pairs = [(gold, predicted)] → the metric block described in the module docstring."""
    n = len(pairs)
    gold = Counter(g for g, _ in pairs)
    decided = [(g, p) for g, p in pairs if g != "cantTell"]
    tp = sum(g == "failed" and p == "failed" for g, p in decided)
    fn = sum(g == "failed" and p != "failed" for g, p in decided)
    fp = sum(g != "failed" and p == "failed" for g, p in decided)
    tn = sum(g != "failed" and p != "failed" for g, p in decided)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = (2 * precision * recall / (precision + recall)) if precision and recall else (0.0 if precision == 0 or recall == 0 else None)
    gold_failed = [p for g, p in pairs if g == "failed"]
    gold_ct = [p for g, p in pairs if g == "cantTell"]
    explicit = sum(p == "passed" for p in gold_failed)
    silent = sum(p == "inapplicable" for p in gold_failed)
    return {
        "n": n,
        "gold": {o: gold.get(o, 0) for o in OUTCOMES},
        "confusion": {"TP": tp, "FP": fp, "FN": fn, "TN": tn},
        "precision": rate(tp, tp + fp),
        "recall": rate(tp, tp + fn),
        "f1": round(f1, 4) if f1 is not None else None,
        "explicit_false_pass": rate(explicit, len(gold_failed)),
        "silent_miss": rate(silent, len(gold_failed)),
        "false_pass": rate(explicit + silent, len(gold_failed)),
        "flagged_recall": rate(sum(p in ("failed", "cantTell") for p in gold_failed), len(gold_failed)),
        "deferral_rate": rate(sum(p == "cantTell" for _, p in pairs), n),
        "gold_cantTell_flag_rate": rate(sum(p in ("failed", "cantTell") for p in gold_ct), len(gold_ct)),
        "accuracy": rate(sum(g == p for g, p in pairs), n),
        "decision_accuracy": rate(sum(decision(g) == decision(p) for g, p in pairs), n),
        "outcomes": dict(Counter(f"{g}->{p}" for g, p in pairs)),
    }


def compare(pairs_a: list[tuple[str, str]], pairs_b: list[tuple[str, str]]) -> dict:
    """McNemar on decision correctness, system A vs B, same cases in the same order."""
    ok_a = [decision(g) == decision(p) for g, p in pairs_a]
    ok_b = [decision(g) == decision(p) for g, p in pairs_b]
    b = sum(x and not y for x, y in zip(ok_a, ok_b))
    c = sum(y and not x for x, y in zip(ok_a, ok_b))
    p = mcnemar_exact(b, c)
    return {"a_only_correct": b, "b_only_correct": c, "p_value": p, "significant": p < 0.05}
