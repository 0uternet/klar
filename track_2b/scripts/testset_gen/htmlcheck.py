"""Tiny stdlib-only HTML tree builder and CSS selector matcher.

Used to validate the evaluation set without third-party packages:
  * every ``target_selector`` must match exactly one element;
  * generated HTML must be well formed (every non-void element explicitly closed).

Supported selector subset (enough for test-case targets, and valid CSS for a browser):
  type, ``*``, ``#id``, ``.class``, ``[attr]``, ``[attr="v"]``, ``[attr~="v"]``,
  ``[attr^="v"]``, ``[attr$="v"]``, ``[attr*="v"]``, ``:first-child``, ``:last-child``,
  ``:first-of-type``, ``:last-of-type``, ``:nth-child(n)``, ``:nth-of-type(n)``,
  combinators: descendant (space), child ``>``, adjacent ``+``, general sibling ``~``.
  Selector lists (``a, b``) are supported as a union.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

VOID = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "param", "source", "track", "wbr",
}
# Elements whose end tag may legitimately be omitted in HTML (lenient mode only).
OPTIONAL_END = {"p", "li", "dt", "dd", "option", "tr", "td", "th", "thead", "tbody",
                "tfoot", "colgroup", "optgroup", "rt", "rp", "html", "head", "body"}


class Node:
    __slots__ = ("tag", "attrs", "parent", "children", "text_parts", "line")

    def __init__(self, tag, attrs, parent, line=0):
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children = []
        self.text_parts = []
        self.line = line

    # -- helpers -----------------------------------------------------------
    def element_children(self):
        return [c for c in self.children if isinstance(c, Node)]

    def iter(self):
        for c in self.children:
            if isinstance(c, Node):
                yield c
                yield from c.iter()

    def text(self):
        out = []
        for c in self.children:
            if isinstance(c, Node):
                if c.tag in ("script", "style"):
                    continue
                out.append(c.text())
            else:
                out.append(c)
        return "".join(out)

    def classes(self):
        return (self.attrs.get("class") or "").split()

    def __repr__(self):
        return f"<{self.tag} {self.attrs}>"


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", {}, None)
        self.stack = [self.root]
        self.errors: list[str] = []
        self.doctype = None

    def handle_decl(self, decl):
        self.doctype = decl

    def handle_starttag(self, tag, attrs):
        parent = self.stack[-1]
        d = {}
        for k, v in attrs:
            if k in d:
                self.errors.append(f"line {self.getpos()[0]}: duplicate attribute {k!r} on <{tag}>")
            d[k] = "" if v is None else v
        node = Node(tag, d, parent, self.getpos()[0])
        parent.children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        parent = self.stack[-1]
        d = {k: ("" if v is None else v) for k, v in attrs}
        node = Node(tag, d, parent, self.getpos()[0])
        parent.children.append(node)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack[-1].tag == tag:
            self.stack.pop()
            return
        tags = [n.tag for n in self.stack]
        if tag in tags:
            while self.stack[-1].tag != tag:
                n = self.stack.pop()
                self.errors.append(f"line {self.getpos()[0]}: <{n.tag}> (line {n.line}) closed implicitly by </{tag}>")
            self.stack.pop()
        else:
            self.errors.append(f"line {self.getpos()[0]}: stray </{tag}>")

    def handle_data(self, data):
        self.stack[-1].children.append(data)

    def close(self):
        super().close()
        for n in self.stack[1:]:
            self.errors.append(f"<{n.tag}> (line {n.line}) never closed")


def parse(html: str) -> tuple[Node, list[str], str | None]:
    tb = TreeBuilder()
    tb.feed(html)
    tb.close()
    return tb.root, tb.errors, tb.doctype


def strict_errors(errors: list[str]) -> list[str]:
    return errors


def lenient_errors(errors: list[str]) -> list[str]:
    """Drop errors that only concern elements with optional end tags."""
    out = []
    for e in errors:
        m = re.search(r"<(\w+)> \(line \d+\) (closed implicitly|never closed)", e)
        if m and m.group(1) in OPTIONAL_END:
            continue
        out.append(e)
    return out


# ---------------------------------------------------------------------------
# Selector engine
# ---------------------------------------------------------------------------
_TOKEN = re.compile(r"""
    (?P<ws>\s*[>+~]\s*|\s+)
  | (?P<tag>\*|[a-zA-Z][a-zA-Z0-9-]*)
  | \#(?P<id>[A-Za-z0-9_\-]+)
  | \.(?P<cls>[A-Za-z0-9_\-]+)
  | \[(?P<attr>[A-Za-z_:][A-Za-z0-9_:.\-]*)\s*(?:(?P<op>[~^$*|]?=)\s*(?:"(?P<v1>[^"]*)"|'(?P<v2>[^']*)'|(?P<v3>[A-Za-z0-9_\-]+)))?\s*\]
  | :(?P<pseudo>[a-z\-]+)(?:\((?P<arg>[^)]*)\))?
""", re.X)


class SelectorError(ValueError):
    pass


def _parse_compound_list(sel: str):
    """Return list of (combinator, compound) from left to right."""
    sel = sel.strip()
    pos = 0
    parts = []  # list of [combinator, compound dict]
    comb = None
    cur = None
    while pos < len(sel):
        m = _TOKEN.match(sel, pos)
        if not m or m.end() == pos:
            raise SelectorError(f"cannot parse selector {sel!r} at {pos}")
        pos = m.end()
        if m.group("ws") is not None:
            c = m.group("ws").strip() or " "
            if cur is not None:
                parts.append((comb, cur))
                cur = None
            comb = c
            continue
        if cur is None:
            cur = {"tag": None, "ids": [], "classes": [], "attrs": [], "pseudos": []}
        if m.group("tag"):
            cur["tag"] = m.group("tag").lower()
        elif m.group("id"):
            cur["ids"].append(m.group("id"))
        elif m.group("cls"):
            cur["classes"].append(m.group("cls"))
        elif m.group("attr"):
            v = m.group("v1") if m.group("v1") is not None else (m.group("v2") if m.group("v2") is not None else m.group("v3"))
            cur["attrs"].append((m.group("attr").lower(), m.group("op"), v))
        elif m.group("pseudo"):
            cur["pseudos"].append((m.group("pseudo"), m.group("arg")))
    if cur is not None:
        parts.append((comb, cur))
    if not parts:
        raise SelectorError(f"empty selector {sel!r}")
    return parts


def _siblings(node):
    return node.parent.element_children() if node.parent else [node]


def _match_compound(node: Node, c) -> bool:
    if node.tag.startswith("#"):
        return False
    if c["tag"] and c["tag"] != "*" and node.tag != c["tag"]:
        return False
    for i in c["ids"]:
        if node.attrs.get("id") != i:
            return False
    cls = node.classes()
    for k in c["classes"]:
        if k not in cls:
            return False
    for name, op, v in c["attrs"]:
        if name not in node.attrs:
            return False
        av = node.attrs[name]
        if op is None:
            continue
        if op == "=" and av != v:
            return False
        if op == "~=" and v not in av.split():
            return False
        if op == "^=" and not av.startswith(v):
            return False
        if op == "$=" and not av.endswith(v):
            return False
        if op == "*=" and v not in av:
            return False
        if op == "|=" and not (av == v or av.startswith(v + "-")):
            return False
    for name, arg in c["pseudos"]:
        sibs = _siblings(node)
        same = [s for s in sibs if s.tag == node.tag]
        if name == "first-child":
            if sibs[0] is not node:
                return False
        elif name == "last-child":
            if sibs[-1] is not node:
                return False
        elif name == "first-of-type":
            if same[0] is not node:
                return False
        elif name == "last-of-type":
            if same[-1] is not node:
                return False
        elif name == "nth-child":
            if not arg or not arg.strip().isdigit() or sibs.index(node) + 1 != int(arg):
                return False
        elif name == "nth-of-type":
            if not arg or not arg.strip().isdigit() or same.index(node) + 1 != int(arg):
                return False
        else:
            raise SelectorError(f"unsupported pseudo-class :{name}")
    return True


def _match_from(node: Node, parts, idx: int) -> bool:
    comb, comp = parts[idx]
    if not _match_compound(node, comp):
        return False
    if idx == 0:
        return True
    if comb == ">":
        p = node.parent
        return p is not None and _match_from(p, parts, idx - 1)
    if comb == " ":
        p = node.parent
        while p is not None:
            if _match_from(p, parts, idx - 1):
                return True
            p = p.parent
        return False
    sibs = _siblings(node)
    i = sibs.index(node)
    if comb == "+":
        return i > 0 and _match_from(sibs[i - 1], parts, idx - 1)
    if comb == "~":
        return any(_match_from(s, parts, idx - 1) for s in sibs[:i])
    raise SelectorError(f"bad combinator {comb!r}")


def select(root: Node, selector: str) -> list[Node]:
    groups = [g for g in _split_groups(selector)]
    result = []
    seen = set()
    for g in groups:
        parts = _parse_compound_list(g)
        for n in root.iter():
            if id(n) not in seen and _match_from(n, parts, len(parts) - 1):
                seen.add(id(n))
                result.append(n)
    return result


def _split_groups(selector: str):
    out, depth, cur, quote = [], 0, [], None
    for ch in selector:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        elif ch == "," and depth == 0:
            out.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    out.append("".join(cur))
    return [g.strip() for g in out if g.strip()]


def outer_html(node: Node, limit: int | None = None) -> str:
    """Re-serialise a node (attribute order preserved, entities re-escaped)."""
    import html as _h
    out: list[str] = []

    def rec(n):
        if isinstance(n, str):
            out.append(_h.escape(n, quote=False))
            return
        a = "".join(f' {k}="{_h.escape(v, quote=True)}"' if v != "" else f" {k}" for k, v in n.attrs.items())
        out.append(f"<{n.tag}{a}>")
        if n.tag in VOID:
            return
        for c in n.children:
            rec(c)
        out.append(f"</{n.tag}>")

    rec(node)
    s = "".join(out)
    return s if limit is None or len(s) <= limit else s[:limit] + "…"


def html_lang(root: Node) -> str | None:
    for n in root.iter():
        if n.tag == "html":
            return n.attrs.get("lang")
    return None


if __name__ == "__main__":  # tiny self-test
    doc = """<!DOCTYPE html><html lang="de"><head><title>t</title></head><body>
    <main><article class="card"><h3>A</h3><p class="more"><a href="a.html" id="m1">Mehr</a></p></article>
    <article class="card"><h3>B</h3><p class="more"><a href="b.html">Mehr</a></p></article>
    <ul><li>x</li><li data-k="2">y <a href="#">z</a></li></ul><svg><rect x="1"/></svg></main></body></html>"""
    root, errs, dt = parse(doc)
    assert not errs, errs
    assert len(select(root, "article.card p.more > a")) == 2
    assert len(select(root, "article:nth-of-type(2) a")) == 1
    assert select(root, "#m1")[0].text() == "Mehr"
    assert len(select(root, 'li[data-k="2"] a')) == 1
    assert len(select(root, "h3 + p a")) == 2
    assert html_lang(root) == "de"
    print("htmlcheck self-test ok")
