"""Template grouping and group-wise dev/test split (stdlib only).

Why: dev and test must not share scenario families (EVAL-1). A prompt tuned on a dev case
must never have seen a near-copy of a test case.

* Every case gets a *signature*: the word set of the text a checker would look at:
  - element-level case: the target's own text and text-bearing attributes, plus the text of
    its closest component ancestor (card/article, section, form, fieldset, table, list, …);
  - page-level case: the text of <main> (or <body>); for mini sites, of every page.
* Cases of one criterion are linked when they share an explicit ``Case.template`` or when the
  Jaccard similarity of their signatures is >= JACCARD_GROUP (0.6). Connected components are the
  template groups (``template_id``).
* The split assigns whole groups: forced groups first (``Case.split``), then groups chosen
  greedily (seeded order) to fill ~20 % dev per criterion and per expected outcome.
  Add-on cases (tag "addon", e.g. the 3.1.2 v3 span categories) keep their designed split and
  are excluded from the quota, so adding them never moves an existing case.
  Consequence: no template and no pair of cases with Jaccard >= 0.6 is shared across splits.
"""
from __future__ import annotations

import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

import htmlcheck

JACCARD_GROUP = 0.6
DEV_SHARE = 0.20
MIN_TEST_HEADLINE = 30
COMPONENT_TAGS = {"article", "section", "form", "fieldset", "table", "ul", "ol", "dl", "nav", "aside",
                  "header", "footer", "figure", "blockquote", "details", "dialog"}
TEXT_ATTRS = ("alt", "aria-label", "title", "value", "placeholder", "aria-description")
WORD = re.compile(r"\w{2,}", re.UNICODE)


def _tokens(text: str) -> frozenset:
    return frozenset(w.casefold() for w in WORD.findall(text or ""))


def _main_text(root) -> str:
    for tag in ("main", "body"):
        for n in root.iter():
            if n.tag == tag:
                return n.text()
    return root.text()


def signature(entry: Path, target: str | None, pages: int) -> frozenset:
    html = entry.read_text(encoding="utf-8")
    root, _, _ = htmlcheck.parse(html)
    if target:
        nodes = htmlcheck.select(root, target)
        if nodes:
            n = nodes[0]
            parts = [n.text()] + [n.attrs.get(a, "") for a in TEXT_ATTRS]
            anc = n.parent
            while anc is not None and anc.tag not in COMPONENT_TAGS and anc.tag not in ("main", "body"):
                anc = anc.parent
            if anc is not None:
                parts.append(anc.text())
            return _tokens(" ".join(parts))
    texts = [_main_text(root)]
    if pages > 1:
        for f in sorted(entry.parent.rglob("*.html")):
            if f != entry:
                r2, _, _ = htmlcheck.parse(f.read_text(encoding="utf-8"))
                texts.append(_main_text(r2))
    return _tokens(" ".join(texts))


def jaccard(a: frozenset, b: frozenset) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


class _UF:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, i):
        while self.p[i] != i:
            self.p[i] = self.p[self.p[i]]
            i = self.p[i]
        return i

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def assign_templates(rows: list[dict], testset: Path) -> dict:
    """Set row['template_id'] for every row; return {criterion: n_templates}."""
    by_crit = defaultdict(list)
    for r in rows:
        by_crit[r["criterion"]].append(r)
    counts = {}
    for crit, items in by_crit.items():
        items.sort(key=lambda r: r["case_id"])
        sigs = [signature(testset / r["path"], r["target_selector"], r.get("pages", 1)) for r in items]
        uf = _UF(len(items))
        by_hint = defaultdict(list)
        for i, r in enumerate(items):
            if r.get("template_hint"):
                by_hint[r["template_hint"]].append(i)
        for idx in by_hint.values():
            for j in idx[1:]:
                uf.union(idx[0], j)
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if jaccard(sigs[i], sigs[j]) >= JACCARD_GROUP:
                    uf.union(i, j)
        comps = defaultdict(list)
        for i in range(len(items)):
            comps[uf.find(i)].append(i)
        ordered = sorted(comps.values(), key=lambda idx: items[idx[0]]["case_id"])
        for k, idx in enumerate(ordered, 1):
            hints = sorted({items[i]["template_hint"] for i in idx if items[i].get("template_hint")})
            name = hints[0] if hints else f"auto{k:03d}"
            tid = f"{crit}/{name}"
            for i in idx:
                items[i]["template_id"] = tid
        counts[crit] = len(ordered)
    return counts


def group_split(rows: list[dict], seed: int, headline=("1.1.1", "2.4.4", "3.1.2")) -> None:
    """Assign row['split'] by template group (see module docstring)."""
    by_crit = defaultdict(list)
    for r in rows:
        by_crit[r["criterion"]].append(r)
    for crit, items in sorted(by_crit.items()):
        rng = random.Random(f"klar-groupsplit-{seed}-{crit}")
        # add-on cases (tag "addon") carry a designed, forced split and are left out of the quota,
        # so adding them never moves an existing case between dev and test (split stability)
        for r in items:
            if "addon" in (r.get("tags") or []):
                if r.get("split_hint") not in ("dev", "test"):
                    raise ValueError(f"add-on case {r['case_id']} needs a forced split")
                r["split"] = r["split_hint"]
        items = [r for r in items if "addon" not in (r.get("tags") or [])]
        groups = defaultdict(list)
        for r in sorted(items, key=lambda r: r["case_id"]):
            groups[r["template_id"]].append(r)
        n = len(items)
        tot = Counter(r["expected"] for r in items)
        target_dev = round(DEV_SHARE * n)
        if crit in headline:
            target_dev = min(target_dev, n - MIN_TEST_HEADLINE)
        target_o = {o: DEV_SHARE * c for o, c in tot.items()}
        dev_o, dev_n = Counter(), 0
        free = []
        for tid, g in sorted(groups.items()):
            forced = {r.get("split_hint") for r in g if r.get("split_hint")}
            if len(forced) > 1:
                raise ValueError(f"group {tid} has conflicting forced splits {forced}")
            if forced:
                s = forced.pop()
                for r in g:
                    r["split"] = s
                if s == "dev":
                    dev_n += len(g)
                    dev_o.update(r["expected"] for r in g)
            else:
                free.append((tid, g))
        rng.shuffle(free)
        free.sort(key=lambda t: len(t[1]))          # small groups first: finer control
        for tid, g in free:
            go = Counter(r["expected"] for r in g)
            gain = sum(min(c, max(0.0, target_o.get(o, 0) - dev_o[o])) for o, c in go.items())
            fits = dev_n + len(g) <= target_dev + 0.5
            if fits and gain >= len(g) / 2:
                s = "dev"
                dev_n += len(g)
                dev_o.update(go)
            else:
                s = "test"
            for r in g:
                r["split"] = s


def near_duplicates_across(rows: list[dict], testset: Path, threshold: float = 0.8) -> list[tuple]:
    """Pairs (dev case, test case, jaccard) of the same criterion above threshold."""
    by_crit = defaultdict(list)
    for r in rows:
        by_crit[r["criterion"]].append(r)
    out = []
    for crit, items in by_crit.items():
        sig = {r["case_id"]: signature(testset / r["path"], r["target_selector"], r.get("pages", 1)) for r in items}
        dev = [r for r in items if r["split"] == "dev"]
        test = [r for r in items if r["split"] == "test"]
        for a in dev:
            for b in test:
                j = jaccard(sig[a["case_id"]], sig[b["case_id"]])
                if j > threshold:
                    out.append((a["case_id"], b["case_id"], round(j, 3)))
    return out
