#!/usr/bin/env python3
"""Leakage check for the Klar. evaluation set (stdlib only). Exit 1 if any overlap is found.

Usage (from track_2b/):  python -I scripts/check_leakage.py [--verbose] [--root .] [--src src/klar]

Run it in CI and before tagging `labels-v1` (PROTOCOL.md decision D3). Scope: the TEST split of
the generated cases (ACT cases are W3C's, not authored by us).

Text extraction (``ws_text``) inserts a space at every element boundary, block or inline, so
words of neighbouring elements never fuse ("3.9.2026" + "nach" stays two words). Words are
NFC-normalised, case-folded runs of letters/digits; *shingles* are runs of 8 consecutive words.
"Page text" = visible text of all pages of the case plus title, alt, aria-label, title,
placeholder and value attributes. "Text under test" = the target element's text and text
attributes plus its enclosing component (card, section, form, list, table …); <main> for
page-level cases. "Surface forms" = the decisive words of a case stored in the manifest.

1. code -> test (src/klar)
   a. Examples quoted inside string literals, docstrings or comments of src/klar/checks/**
      ("…", “…”, «…», ‘…’) with >= 3 words must not occur in the text under test of a test case.
   b. Lexicon items (items of string lists/tuples/sets with >= 3 items in src/klar/checks/**) and
      shorter quoted examples must not equal a test surface form; lexicon items of >= 2 words
      must not occur in the text under test of a test TRAP or cantTell case.
   c. No test surface form may occur anywhere in src/klar/** (literals, comments, other files).
   d. Few-shot copies: no 8-word shingle of a test page may occur in the string literals or
      comments of src/klar/**/*.py or *.js.
2. demo -> test (data/demo-site, data/demo-truth)
   a. Strings quoted in the demo answer keys with >= 3 words must not occur in a test page.
   b. No demo answer-key string may equal a test surface form, and no test surface form may
      occur in the demo site's text.
   c. No 8-word shingle of the demo site's text may occur in a test page.
   d. The demo site's fictional place names (DEMO_ENTITIES) must not occur in a test page.
3. dev -> test
   a. No template group (`template_id`) in both splits.
   b. No near-duplicate pair across splits (signature Jaccard > 0.8; testset_gen/grouping.py).
   c. No surface form shared by a dev case and a test case.
4. answer keys: no ISSUES.md / issues.jsonl or other answer-key-like file, no rationale text and
   no verdict marker ("cantTell", "alt_expected", '"expected"') inside the served data/demo-site/.

Excluded from the code side: third-party and build artefacts that are not Klar.'s prompts —
src/klar/capture/vendor/** (unmodified vendored libraries such as axe-core),
src/klar/api/static/** (the compiled web UI, git-ignored) and licence texts (LICENSE*, NOTICE*,
COPYING*, *.txt). Licence boilerplate ("fitness for a particular purpose") would otherwise
collide with ordinary words.

Criterion vocabulary is not reported: generic link texts ("Mehr", "Lire la suite", "Di più",
"Download" …, taken from testset_gen/c_2_4_4.py) are the phenomenon under test for 2.4.4 —
whether they fail depends on their context, not on the words — so a lexicon of generic link
texts in the application is not an answer key. Everything else is reported.

Regression tests: tests/test_leakage.py seeds one violation per rule in a temporary tree.
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import re
import sys
import tokenize
import unicodedata
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "testset_gen"))
import grouping  # noqa: E402
import htmlcheck  # noqa: E402
import c_2_4_4  # noqa: E402  (generic link vocabulary)

ROOT = HERE.parent
DEMO_ENTITIES = ("Musterwil", "Aarenwald", "Moosmatt")      # names invented for the demo site only
TEXT_ATTRS = ("alt", "aria-label", "title", "placeholder", "value", "aria-description")
QUOTED = re.compile(r'"([^"\n]{2,80})"|“([^”\n]{2,80})”|«\s*([^»\n]{2,80}?)\s*»|‘([^’\n]{2,80})’')
SKIP_SUFFIX = (".pyc", ".png", ".jpg", ".jpeg", ".gif", ".woff", ".woff2", ".gguf", ".ico")
SHINGLE = 8
WORD = re.compile(r"\w+", re.UNICODE)
JS_STRINGS = re.compile(r"""//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'|`(?:\\.|[^`\\])*`""", re.S)
CATEGORIES = ("code->test", "demo->test", "dev->test", "answer-keys")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "").casefold()
    s = s.replace("’", "'").replace(" ", " ").replace(" ", " ").replace(" ", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .,;:!?«»\"'()[]{}–-…")


GENERIC = {norm(w) for lst in c_2_4_4.GENERIC.values() for w in lst}
GENERIC |= {norm(w) for w in list(c_2_4_4.DOWNLOAD.values()) + list(c_2_4_4.REGISTER.values())}
GENERIC |= {"leggi di più", "click here", "cliquez ici", "clicca qui", "klicken sie hier", "hier klicken", "pdf",
            "la suite", "zur seite", "diese seite", "cette page", "questa pagina", "this page"}   # vague deixis


def words(text: str) -> list[str]:
    return WORD.findall(unicodedata.normalize("NFC", text or "").casefold())


def shingles(text: str, n: int = SHINGLE) -> set[str]:
    w = words(text)
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)}


def contains(hay: str, needle: str) -> bool:
    if not needle or needle not in hay:
        return False
    return re.search(r"(?<!\w)" + re.escape(needle) + r"(?!\w)", hay) is not None


def _quoted(text: str):
    for m in QUOTED.finditer(text):
        yield next(g for g in m.groups() if g)


# ---------------------------------------------------------------------------- HTML text
def ws_text(node) -> str:
    """Text of a node with a space at every element boundary (script/style skipped)."""
    out = []

    def rec(n):
        for c in n.children:
            if isinstance(c, str):
                out.append(c)
            elif c.tag not in ("script", "style"):
                out.append(" ")
                rec(c)
                out.append(" ")
    rec(node)
    return re.sub(r"\s+", " ", "".join(out)).strip()


def _page_parts(root) -> list[str]:
    parts = []
    for n in root.iter():
        if n.tag in ("body", "title"):
            parts.append(ws_text(n))
        for a in TEXT_ATTRS:
            if a in n.attrs:
                parts.append(n.attrs[a])
    return parts


def page_text(path: Path) -> str:
    root, _, _ = htmlcheck.parse(path.read_text(encoding="utf-8"))
    return " \n ".join(_page_parts(root))


# ---------------------------------------------------------------------------- code strings
EXCLUDED_DIRS = (("capture", "vendor"), ("api", "static"))   # third-party code, build output


def excluded(f: Path, src: Path) -> bool:
    """Third-party code, build artefacts and licence texts are not Klar.'s prompts or code."""
    parts = f.relative_to(src).parts
    for d in EXCLUDED_DIRS:
        if any(parts[i:i + len(d)] == d for i in range(len(parts) - len(d) + 1)):
            return True
    name = f.name.upper()
    return name.startswith(("LICENSE", "LICENCE", "COPYING", "NOTICE")) or f.suffix.lower() == ".txt"


def code_strings(src: Path):
    """Return (examples, lexicon, code_text, code_shingles) for src/**.

    examples / lexicon come from src/**/checks only; code_text covers every file;
    code_shingles cover string literals and comments of *.py and *.js files."""
    examples, lexicon, chunks, code_sh = set(), set(), [], set()
    for f in sorted(src.rglob("*")):
        if not f.is_file() or "__pycache__" in f.parts or f.suffix in SKIP_SUFFIX or excluded(f, src):
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        in_checks = "checks" in f.relative_to(src).parts
        strings = []
        if f.suffix == ".py":
            try:
                tree = ast.parse(text)
            except SyntaxError:
                tree = None
            if tree is None:
                strings.append(text)
            else:
                for node in ast.walk(tree):
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        strings.append(node.value)
                    elif in_checks and isinstance(node, (ast.List, ast.Tuple, ast.Set)):
                        items = [e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
                        if len(items) >= 3:
                            lexicon.update(norm(it) for it in items)
                try:
                    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
                        if tok.type == tokenize.COMMENT:
                            strings.append(tok.string)
                except (tokenize.TokenError, IndentationError, SyntaxError):
                    pass
            for v in strings:
                code_sh |= shingles(v)
        elif f.suffix in (".js", ".mjs", ".ts"):
            strings += [m.group(0) for m in JS_STRINGS.finditer(text)]
            for v in strings:
                code_sh |= shingles(v)
        else:
            strings.append(text)
        chunks += strings
        if in_checks:
            for v in strings:
                examples.update(norm(q) for q in _quoted(v))
    examples = {e for e in examples if e and e not in GENERIC}
    lexicon = {e for e in lexicon if e and e not in GENERIC}
    return examples, lexicon, norm(" \n ".join(chunks)), code_sh


# ---------------------------------------------------------------------------- the check
def run(root: Path = ROOT, src: Path | None = None) -> dict[str, list[str]]:
    """Return {category: [findings]} for the tree at ``root`` (track_2b/)."""
    root = Path(root)
    src = Path(src) if src is not None else root / "src" / "klar"
    testset, demo, truth = root / "data" / "testset", root / "data" / "demo-site", root / "data" / "demo-truth"

    def case_text(row) -> str:
        entry = testset / row["path"]
        files = [entry] if row.get("pages", 1) == 1 else sorted(entry.parent.rglob("*.html"))
        return " \n ".join(page_text(f) for f in files)

    def target_text(row) -> str:
        entry = testset / row["path"]
        r0, _, _ = htmlcheck.parse(entry.read_text(encoding="utf-8"))
        if row.get("target_selector"):
            nodes = htmlcheck.select(r0, row["target_selector"])
            if nodes:
                n = nodes[0]
                parts = [ws_text(n)] + [n.attrs.get(a, "") for a in TEXT_ATTRS]
                anc = n.parent
                while anc is not None and anc.tag not in grouping.COMPONENT_TAGS and anc.tag not in ("main", "body"):
                    anc = anc.parent
                if anc is not None:
                    parts.append(ws_text(anc))
                return norm(" \n ".join(parts))
        for tag in ("main", "body"):
            for n in r0.iter():
                if n.tag == tag:
                    return norm(ws_text(n))
        return ""

    rows = [json.loads(l) for l in (testset / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    gen = [r for r in rows if r["source"] == "generated"]
    test = [r for r in gen if r["split"] == "test"]
    dev = [r for r in gen if r["split"] == "dev"]
    raw = {r["case_id"]: case_text(r) for r in test}
    full = {cid: norm(t) for cid, t in raw.items()}
    page_sh = {cid: shingles(t) for cid, t in raw.items()}
    under = {r["case_id"]: target_text(r) for r in test}
    surf = {r["case_id"]: [norm(s) for s in (r.get("surface_forms") or [])] for r in test}
    lexical = {r["case_id"] for r in test if r.get("trap") or r["expected"] == "cantTell"}
    findings: dict[str, list[str]] = defaultdict(list)

    # 1. code -> test --------------------------------------------------------------------
    if src.exists():
        examples, lexicon, code_text, code_sh = code_strings(src)
        long_ex = {e for e in examples if len(e.split()) >= 3}
        short_ex = examples - long_ex
        multi_lex = {e for e in lexicon if len(e.split()) >= 2}
        for cid in full:
            for e in long_ex:
                if contains(under[cid], e):
                    findings["code->test"].append(f"{cid}: quoted code example {e!r} in the text under test")
            if cid in lexical:
                for e in multi_lex:
                    if contains(under[cid], e):
                        findings["code->test"].append(f"{cid}: code lexicon item {e!r} in a trap/cantTell text under test")
            hits = sorted(page_sh[cid] & code_sh)
            if hits:
                findings["code->test"].append(f"{cid}: {len(hits)} 8-word shingle(s) of the page occur in src code, "
                                              f"e.g. {hits[0]!r}")
            for sf in surf[cid]:
                if sf in short_ex or sf in lexicon or sf in long_ex:
                    findings["code->test"].append(f"{cid}: surface form {sf!r} is a code example/lexicon item")
                elif contains(code_text, sf):
                    findings["code->test"].append(f"{cid}: surface form {sf!r} occurs in {src.as_posix()}")

    # 2. demo -> test --------------------------------------------------------------------
    if demo.exists():
        dtexts = [page_text(f) for f in sorted(demo.rglob("*.html"))]
        demo_all = norm(" \n ".join(dtexts))
        demo_sh = set()
        for t in dtexts:
            demo_sh |= shingles(t)
        keys = set()
        for kf in (truth / "issues.jsonl", demo / "issues.jsonl"):
            if kf.exists():
                for line in kf.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        keys.update(norm(q) for q in _quoted(json.loads(line).get("rationale", "")))
        keys = {k for k in keys if k and k not in GENERIC}
        long_keys = {k for k in keys if len(k.split()) >= 3}
        ents = [norm(e) for e in DEMO_ENTITIES]
        for cid, t in full.items():
            for k in long_keys:
                if contains(t, k):
                    findings["demo->test"].append(f"{cid}: demo answer-key string {k!r}")
            for sf in surf[cid]:
                if sf in keys or contains(demo_all, sf):
                    findings["demo->test"].append(f"{cid}: surface form {sf!r} occurs in the demo site / answer keys")
            hits = sorted(page_sh[cid] & demo_sh)
            if hits:
                findings["demo->test"].append(f"{cid}: {len(hits)} 8-word shingle(s) shared with the demo site, e.g. {hits[0]!r}")
            for e in ents:
                if re.search(r"(?<!\w)" + re.escape(e), t):
                    findings["demo->test"].append(f"{cid}: demo place name {e!r}")

    # 3. dev -> test ---------------------------------------------------------------------
    splits_of = defaultdict(set)
    for r in gen:
        splits_of[r["template_id"]].add(r["split"])
    for tid, splits in sorted(splits_of.items()):
        if len(splits) > 1:
            findings["dev->test"].append(f"template {tid} is in both splits")
    for a, b, j in grouping.near_duplicates_across(gen, testset, 0.8):
        findings["dev->test"].append(f"near-duplicate {a} (dev) ~ {b} (test), Jaccard {j}")
    dev_sf = defaultdict(list)
    for r in dev:
        for sf in r.get("surface_forms") or []:
            dev_sf[norm(sf)].append(r["case_id"])
    for r in test:
        for sf in surf[r["case_id"]]:
            if sf in dev_sf:
                findings["dev->test"].append(f"surface form {sf!r} in {r['case_id']} (test) and {dev_sf[sf]} (dev)")

    # 4. answer keys / truth strings inside the served demo folder ---------------------------
    if demo.exists():
        markers = {'"expected"', "canttell", "alt_expected", "strict act"}
        kf = truth / "issues.jsonl"
        if kf.exists():
            for line in kf.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rat = norm(json.loads(line).get("rationale", ""))
                    if len(rat) >= 40:
                        markers.add(rat[:60])
        for f in sorted(demo.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(demo).as_posix()
            if re.search(r"issues|truth|answer|expected", f.name, re.I):
                findings["answer-keys"].append(f"data/demo-site/{rel}: answer-key-like file in the served folder")
            if f.suffix.lower() not in (".html", ".htm", ".js", ".css", ".json", ".jsonl", ".md", ".txt", ".svg", ".xml"):
                continue
            t = norm(f.read_text(encoding="utf-8", errors="replace"))
            for mk in markers:
                if mk in t:
                    findings["answer-keys"].append(f"data/demo-site/{rel}: contains answer-key text {mk[:50]!r}")
                    break
    return {k: sorted(set(findings[k])) for k in CATEGORIES}


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT), help="track_2b/ root holding data/ (default: this checkout)")
    ap.add_argument("--src", default=None, help="application source to scan (default: <root>/src/klar)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)
    res = run(Path(args.root), Path(args.src) if args.src else None)
    total = 0
    for k in CATEGORIES:
        items = res[k]
        total += len(items)
        print(f"{k:12s} {len(items)} overlap(s)")
        for it in items[: (None if args.verbose else 25)]:
            print("   ", it)
        if len(items) > 25 and not args.verbose:
            print(f"    … {len(items) - 25} more (use --verbose)")
    print(f"{total} overlaps" if total else "0 overlaps")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
