"""2.4.5 Multiple Ways, level AA. No ACT rule. Decided in code (no Apertus question).

This module also hosts the small helpers that the Group B checks share (no new
shared file was needed): a static HTML parser with the extractor's selector
algorithm (`parse_html`, `Node.css_path`) and a bounded same-site page sample
(`site_sample`) used by 2.4.2, 2.4.5, 3.2.3 and 3.2.4.

Why a site sample. A Klar. scan renders ONE page and the pipeline has no site-level
step, so 2.4.2, 2.4.5, 3.2.3 and 3.2.4 share a bounded sample of the site that they
fetch themselves (`site_sample`, built once per scan and memoised on the CapturedPage):
  * home page = the target of the brand/home link (rel=home, else the first banner
    link), else the origin's "/"; never above an allow-listed prefix (bundled demo,
    evaluation servers). For file: scans, the home page's folder.
  * scope = the whole origin (or the allow-listed prefix); breadth-first from the
    audited page, navigation, header and footer links first; only <a href> links,
    never forms; language-switcher links (hreflang/lang) are not followed; a query
    string that selects a page ("?id=…") is followed (≤ 8 such pages), a query that
    only selects a view (search, filter, sort, paging, tracking) is dropped.
  * limits: ≤ 20 pages, depth ≤ 3, ≤ 21 GET requests per scan (pages, redirect hops,
    the home page), ≤ 512 kB and ≤ 5 s per page (checked while reading, so a server
    that drips bytes is cut off), ≤ 15 s per sample and never past the scan deadline
    (page.remaining(), KLAR_SCAN_TIMEOUT). One HTTP client per sample; every redirect
    hop goes through the scan's network policy and must stay on the same origin.
  * pages are parsed statically (no scripts run).
A set of pages is one language version: pages whose main text is in another language
(lingua; the declared lang as fallback) are left out (Understanding 3.2.3/3.2.4).

What counts as a way to reach page p (Understanding 2.4.5, G125/G63/G64/G161/G185)
  nav      p is linked from a navigation, header, footer or side block repeated on at
           least half of the sampled pages (the navigation counts as ONE way)
  links    p is linked from the content of another page, or from a block that is not
           repeated site-wide (sub-navigation, teaser, related links)
  sitemap  p is listed on a page that links to ≥ 80 % of the other pages and is
           itself reachable site-wide (site map, A–Z index, table of contents, G185)
  search   a search form on the sampled pages covers p: its inline index lists p, or
           it is a same-origin search without an inline index (assumed site-wide)

Cascade (one finding for the set of pages, reported on the audited page)
  1. pasted HTML                              → cantTell (a site-level criterion needs a URL)
  2. the page links to no other page of its origin → inapplicable (a single page is not a set)
  3. fewer than 2 pages fetched (time, errors, limits) → cantTell, never inapplicable
  4. a complete sample of ≤ 5 pages where every page links to every other page
                                              → passed (small-site note, G126)
  5. every page (except the home page and the site map itself) has ≥ 2 ways → passed
  6. some page has < 2 ways and
       the sample stopped at the page limit             → cantTell (sample incomplete)
       a search posts to another origin                 → cantTell (coverage not observable)
       no site map or search at all, but breadcrumbs   → cantTell (breadcrumbs as a way are disputed)
       otherwise                                         → failed
  Steps of a process are exempt (SC exception): pages reachable only by submitting a
  form are never fetched, and a sampled page that a (non-search) form submits to is
  not required to have two ways.

Known limits: scripts are not run on the sampled pages (menus built by JavaScript are
missed); a server-side search is assumed to cover the whole site; large sites are
judged on a sample; pages linked only from a non-HTML resource are invisible.
"""

from __future__ import annotations

import html as htmllib
import logging
import re
import time
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable, Iterator
from urllib.parse import parse_qsl, urldefrag, urlencode, urljoin, urlparse, urlsplit, urlunsplit
from urllib.request import url2pathname

import httpx

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask
from klar.netpolicy import NetPolicy, origin_of

log = logging.getLogger(__name__)

PROMPT_VERSION = "2.4.5/v1"  # no model question; kept for the cache-key contract

# ---------------------------------------------------------------------------------------
# Static DOM (shared by the Group B checks)
# ---------------------------------------------------------------------------------------

VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())
NO_TEXT = frozenset("script style noscript template head title".split())
INLINE = frozenset("a abbr b bdi bdo cite code data dfn em i kbd mark q s samp small span strong sub sup "
                   "time u var label font".split())
CONTROLS = frozenset("input select textarea button".split())
_P_CLOSERS = frozenset("address article aside blockquote div dl fieldset figure footer form h1 h2 h3 h4 h5 h6 "
                       "header hr main nav ol p pre section table ul".split())
# Common class names of visually hidden ("screen-reader only") text.
SR_ONLY = re.compile(r"(?:^|\s)(?:sr-only|visually-hidden|visuallyhidden|screen-reader-text|screenreader|"
                     r"hidden-visually|a11y-hidden|vh|element-invisible|offscreen)(?:\s|$)", re.IGNORECASE)
_HIDDEN_STYLE = re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden", re.IGNORECASE)
_SIMPLE_ID = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


def css_escape(s: str) -> str:
    """CSS.escape() for identifiers (same output as the browser for ordinary ids)."""
    if _SIMPLE_ID.match(s) and not s.startswith("--"):
        return s
    out = []
    for i, ch in enumerate(s):
        o = ord(ch)
        if o == 0:
            out.append("�")
        elif 1 <= o <= 0x1F or o == 0x7F or (i == 0 and ch.isdigit()) or (i == 1 and ch.isdigit() and s[0] == "-"):
            out.append("\\%x " % o)
        elif i == 0 and ch == "-" and len(s) == 1:
            out.append("\\-")
        elif o >= 0x80 or ch in "-_" or (ch.isascii() and ch.isalnum()):
            out.append(ch)
        else:
            out.append("\\" + ch)
    return "".join(out)


def norm_text(s: str | None) -> str:
    return " ".join((s or "").split())


class Node:
    __slots__ = ("tag", "attrs", "children", "parent", "root")

    def __init__(self, tag: str, attrs: dict[str, str], parent: "Node | None"):
        self.tag = tag
        self.attrs = attrs
        self.children: list["Node | str"] = []
        self.parent = parent
        self.root: "Document | None" = parent.root if parent is not None else None

    # -- navigation ---------------------------------------------------------------------
    def get(self, name: str, default: str | None = None) -> str | None:
        return self.attrs.get(name, default)

    def elements(self) -> Iterator["Node"]:
        return (c for c in self.children if isinstance(c, Node))

    def iter(self) -> Iterator["Node"]:
        """Descendant elements in document order (self excluded)."""
        for c in self.children:
            if isinstance(c, Node):
                yield c
                yield from c.iter()

    def find_all(self, pred: Callable[["Node"], bool]) -> list["Node"]:
        return [n for n in self.iter() if pred(n)]

    def find(self, pred: Callable[["Node"], bool]) -> "Node | None":
        return next((n for n in self.iter() if pred(n)), None)

    def ancestors(self) -> Iterator["Node"]:
        p = self.parent
        while p is not None and p.tag != "#document":
            yield p
            p = p.parent

    def closest(self, pred: Callable[["Node"], bool]) -> "Node | None":
        n: Node | None = self
        while n is not None and n.tag != "#document":
            if pred(n):
                return n
            n = n.parent
        return None

    def contains(self, other: "Node") -> bool:
        return other is self or any(a is self for a in other.ancestors())

    @property
    def role(self) -> str:
        return (self.attrs.get("role") or "").strip().lower()

    # -- visibility and text --------------------------------------------------------------
    def hidden(self) -> bool:
        """Removed from rendering (hidden attribute, display:none, type=hidden)."""
        a = self.attrs
        return ("hidden" in a or bool(_HIDDEN_STYLE.search(a.get("style", "")))
                or (self.tag == "input" and a.get("type", "").lower() == "hidden"))

    def sr_only(self) -> bool:
        return bool(SR_ONLY.search(self.attrs.get("class", "")))

    def text(self, *, visible: bool = False, accessible: bool = False, skip: Callable[["Node"], bool] | None = None,
             limit: int = 20000) -> str:
        """Text content with spaces at block boundaries. visible=True drops visually
        hidden text; accessible=True drops aria-hidden content and adds img alts."""
        parts: list[str] = []

        def walk(n: Node) -> None:
            for c in n.children:
                if sum(len(p) for p in parts) > limit:
                    return
                if isinstance(c, str):
                    parts.append(c)
                    continue
                if c.tag in NO_TEXT or c.hidden() or (skip and skip(c)):
                    continue
                if visible and c.sr_only():
                    continue
                if accessible and c.attrs.get("aria-hidden", "").lower() == "true":
                    continue
                if accessible and c.tag == "img":
                    parts.append(" " + (c.attrs.get("alt") or "") + " ")
                    continue
                block = c.tag not in INLINE
                if block:
                    parts.append(" ")
                walk(c)
                if block:
                    parts.append(" ")

        walk(self)
        return norm_text("".join(parts))

    def accessible_name(self) -> str:
        """Static approximation of the accessible name (aria-labelledby, aria-label,
        label, alt, value, content, title)."""
        a = self.attrs
        doc = self.root
        if a.get("aria-labelledby") and doc is not None:
            names = [doc.by_id(i) for i in a["aria-labelledby"].split()]
            txt = norm_text(" ".join(n.text(accessible=True) for n in names if n is not None))
            if txt:
                return txt
        if norm_text(a.get("aria-label")):
            return norm_text(a.get("aria-label"))
        if self.tag == "img":
            return norm_text(a.get("alt"))
        if self.tag == "input":
            typ = a.get("type", "text").lower()
            if typ in ("submit", "button", "reset"):
                return norm_text(a.get("value")) or {"submit": "Submit", "reset": "Reset"}.get(typ, "")
            if typ == "image":
                return norm_text(a.get("alt") or a.get("value"))
        if self.tag in ("input", "select", "textarea") and doc is not None:
            labels = doc.labels_for(self)
            if labels:
                return norm_text(" ".join(lb.text(accessible=True, skip=lambda n: n.tag in CONTROLS) for lb in labels))
        if self.tag in ("a", "button") or self.role in ("button", "link", "heading", "tab", "menuitem"):
            txt = self.text(accessible=True)
            if txt:
                return txt
        return norm_text(a.get("title") or a.get("placeholder"))

    def outer(self, limit: int = 600) -> str:
        """Serialised HTML of the element (attributes escaped), truncated."""
        out: list[str] = []

        def ser(n: Node) -> None:
            if sum(len(p) for p in out) > limit:
                return
            attrs = "".join(f' {k}="{htmllib.escape(v, quote=True)}"' if v != "" else f" {k}"
                            for k, v in n.attrs.items())
            out.append(f"<{n.tag}{attrs}>")
            if n.tag in VOID:
                return
            for c in n.children:
                if isinstance(c, str):
                    out.append(c if n.tag in ("script", "style") else htmllib.escape(c, quote=False))
                else:
                    ser(c)
            out.append(f"</{n.tag}>")

        ser(self)
        s = "".join(out)
        return s if len(s) <= limit else s[:limit]

    def css_path(self) -> str:
        """Same algorithm as cssPath() in capture/js/klar_extract.js: a unique id ends the
        path, else tag:nth-of-type steps up to html."""
        parts: list[str] = []
        node: Node | None = self
        doc = self.root
        while node is not None and node.tag != "#document":
            nid = node.attrs.get("id")
            if nid and doc is not None and doc.id_count.get(nid) == 1:
                parts.insert(0, "#" + css_escape(nid))
                break
            if node.tag == "html":
                parts.insert(0, "html")
                break
            part = css_escape(node.tag)
            parent = node.parent
            if parent is not None:
                same = [c for c in parent.elements() if c.tag == node.tag]
                if len(same) > 1:
                    part += f":nth-of-type({same.index(node) + 1})"
            parts.insert(0, part)
            node = parent
        return " > ".join(parts)


class Document(Node):
    __slots__ = ("id_count", "_ids", "_labels")

    def __init__(self) -> None:
        super().__init__("#document", {}, None)
        self.root = self
        self.id_count: Counter = Counter()
        self._ids: dict[str, Node] = {}
        self._labels: dict[int, list[Node]] | None = None

    def by_id(self, i: str) -> Node | None:
        return self._ids.get(i)

    @property
    def html_el(self) -> Node | None:
        return next((c for c in self.elements() if c.tag == "html"), None)

    @property
    def body(self) -> Node:
        return self.find(lambda n: n.tag == "body") or self

    @property
    def main(self) -> Node | None:
        return self.find(lambda n: n.tag == "main" or n.role == "main")

    @property
    def lang(self) -> str | None:
        h = self.html_el
        return h.attrs.get("lang") if h is not None and "lang" in h.attrs else None

    @property
    def title_el(self) -> Node | None:
        return self.find(lambda n: n.tag == "title" and n.closest(lambda a: a.tag == "svg") is None)

    @property
    def title(self) -> str:
        el = self.title_el
        return norm_text("".join(c for c in el.children if isinstance(c, str))) if el is not None else ""

    def labels_for(self, control: Node) -> list[Node]:
        if self._labels is None:
            self._labels = {}
            for lb in self.find_all(lambda n: n.tag == "label"):
                target = self.by_id(lb.attrs["for"]) if lb.attrs.get("for") else \
                    lb.find(lambda n: n.tag in ("input", "select", "textarea"))
                if target is not None:
                    self._labels.setdefault(id(target), []).append(lb)
        return self._labels.get(id(control), [])

    def control_of(self, label: Node) -> Node | None:
        if label.attrs.get("for"):
            return self.by_id(label.attrs["for"])
        return label.find(lambda n: n.tag in ("input", "select", "textarea"))


class _Builder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.doc = Document()
        self.stack: list[Node] = [self.doc]

    def _close(self, tags: set[str], *, stop: set[str]) -> None:
        for i in range(len(self.stack) - 1, 0, -1):
            tag = self.stack[i].tag
            if tag in stop:
                return
            if tag in tags:
                del self.stack[i:]
                return

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "li":
            self._close({"li"}, stop={"ul", "ol", "menu"})
        elif tag in ("dt", "dd"):
            self._close({"dt", "dd"}, stop={"dl"})
        elif tag in ("td", "th"):
            self._close({"td", "th"}, stop={"tr", "table"})
        elif tag == "tr":
            self._close({"tr"}, stop={"table", "tbody", "thead", "tfoot"})
        elif tag == "option":
            self._close({"option"}, stop={"select", "datalist"})
        if tag in _P_CLOSERS and self.stack[-1].tag == "p":
            self.stack.pop()
        parent = self.stack[-1]
        a: dict[str, str] = {}
        for k, v in attrs:
            a.setdefault(k.lower(), v if v is not None else "")
        node = Node(tag, a, parent)
        parent.children.append(node)
        if a.get("id"):
            self.doc.id_count[a["id"]] += 1
            self.doc._ids.setdefault(a["id"], node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        n = len(self.stack)
        self.handle_starttag(tag, attrs)
        if len(self.stack) > n:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


@lru_cache(maxsize=16)
def parse_html(html: str) -> Document:
    """Parse HTML into a read-only tree (cached: several checks parse the same page)."""
    b = _Builder()
    try:
        b.feed(html or "")
        b.close()
    except Exception as exc:  # malformed markup never breaks a scan
        log.info("static parse stopped early: %s", exc)
    return b.doc


def page_doc(page: CapturedPage) -> Document:
    """The audited page as a static tree: the rendered DOM when available."""
    return parse_html(page.html or page.source_html or "")


def live_selector(page: CapturedPage, node: Node | None, fallback: str = "html") -> str:
    """css_path of a static node if it resolves in the audited page, else `fallback`."""
    if node is None:
        return fallback
    sel = node.css_path()
    if page.live is None:
        return sel
    try:
        return sel if page.selector_exists(sel) else fallback
    except Exception:
        return fallback


def region_of(n: Node) -> str:
    """nav | header | footer | aside | main | other: the landmark that holds `n`."""
    for a in (n, *n.ancestors()):
        tag, role = a.tag, a.role
        if tag == "nav" or role == "navigation":
            return "nav"
        if tag == "main" or role == "main":
            return "main"
        if tag == "aside" or role == "complementary":
            return "aside"
        if tag == "footer" or role == "contentinfo":
            return "footer"
        if tag == "header" or role == "banner":
            return "header"
    return "other"


# Breadcrumb navigation, recognised by its label, id or class (DE · FR · IT · EN).
BREADCRUMB = re.compile(r"breadcrumb|crumb|brotkr[uü]m|krümel|ariane|briciol|percorso|sie sind hier|"
                        r"vous [eê]tes ici|ti trovi|you are here", re.IGNORECASE)


def is_breadcrumb(n: Node) -> bool:
    nav = n.closest(lambda a: a.tag == "nav" or a.role == "navigation")
    if nav is None:
        return False
    label = " ".join(nav.attrs.get(k, "") for k in ("aria-label", "id", "class"))
    if nav.attrs.get("aria-labelledby") and nav.root is not None:
        lab = nav.root.by_id(nav.attrs["aria-labelledby"].split()[0])
        label += " " + (lab.text() if lab is not None else "")
    return bool(BREADCRUMB.search(label))


# Search forms (role=search, type=search, or a form/field named like a search, DE · FR · IT · EN).
# A word that starts a name part ("suche", "search-form"), so that a visit ("Besuch") or an
# attempt ("Versuch") is not a search.
_SEARCH_WORD = re.compile(r"(?:^|[^a-z])(?:search|such|recherch|cerca|ricerca|query)|^[qs]$", re.IGNORECASE)


def is_search_form(form: Node) -> bool:
    if form.role == "search" or (form.parent is not None and form.parent.role == "search"):
        return True
    if form.find(lambda n: n.tag == "input" and n.attrs.get("type", "").lower() == "search"):
        return True
    names = " ".join([form.attrs.get("aria-label", ""), form.attrs.get("id", ""), form.attrs.get("class", ""),
                      form.attrs.get("action", "")])
    fields = [n for n in form.iter() if n.tag in ("input", "select", "textarea")
              and n.attrs.get("type", "text").lower() not in ("hidden", "submit", "button", "image", "reset")]
    if len(fields) != 1:
        return False
    f = fields[0]
    return bool(_SEARCH_WORD.search(names) or _SEARCH_WORD.search(f.attrs.get("name", ""))
                or _SEARCH_WORD.search(f.attrs.get("id", "")))


# ---------------------------------------------------------------------------------------
# Site sample (shared by 2.4.2, 2.4.5, 3.2.3, 3.2.4)
# ---------------------------------------------------------------------------------------

MAX_PAGES = 20  # pages in the sample, entry page included
MAX_QUERY_PAGES = 8  # of which pages addressed by a query string ("index.php?id=…")
MAX_REQUESTS = 21  # GET requests per scan (pages + redirect hops + the home page)
MAX_DEPTH = 3
MAX_BYTES = 524288
FETCH_TIMEOUT = 3.0  # per network operation
FETCH_DEADLINE = 5.0  # absolute, per page: a server that drips bytes is cut off
SAMPLE_BUDGET_S = 15.0  # absolute, per sample, and never beyond the scan's remaining time
USER_AGENT = "Klar./0.1 accessibility pre-check"
_NOT_PAGE = re.compile(r"\.(?:pdf|jpe?g|png|gif|webp|svg|ico|zip|docx?|xlsx?|pptx?|mp[34]|mov|avi|css|js|json|xml|"
                       r"txt|csv|ics|vcf|gz|woff2?)$", re.IGNORECASE)
# Query parameters that select a VIEW of a page (search, filter, sort, paging, tracking,
# language, print), not another page. Any other parameter ("id", "node"…) selects a page.
_VIEW_PARAM = re.compile(r"^(?:q|s|p|query|search\w*|such\w*|recherch\w*|cerca|ricerca|keywords?|terms?|"
                         r"filter\w*|sort\w*|order\w*|dir|page|offset|start|limit|per_?page|utm_\w+|fbclid|gclid|"
                         r"mc_\w+|lang|language|locale|print|format|view|ref|source|sid|session\w*)$", re.IGNORECASE)
_SKIP_HREF = ("#", "mailto:", "tel:", "javascript:", "data:", "sms:", "ftp:")


def page_key(url: str) -> str:
    """Canonical page address: no fragment, no view parameters, ".../index.html" == ".../".
    Used to compare pages."""
    parts = urlsplit(urldefrag(url or "")[0])
    path = re.sub(r"/index\.(?:html?|php|aspx?)$", "/", parts.path, flags=re.IGNORECASE)
    query = ""
    if parts.query:
        query = urlencode(sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                                 if not _VIEW_PARAM.match(k)))
    return urlunsplit((parts.scheme, parts.netloc, path, query, ""))


def request_url(url: str) -> str:
    """The address to GET for a link: as linked, minus fragment and view parameters
    (the path is kept as written: "index.php?id=3" is not rewritten to "/?id=3")."""
    parts = urlsplit(urldefrag(url or "")[0])
    query = urlsplit(page_key(url)).query
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))


def scope_prefix(url: str) -> str:
    """The folder of an address (scheme://host/path/ up to the last "/")."""
    u = urlparse(url)
    path = u.path if u.path.endswith("/") else u.path.rsplit("/", 1)[0] + "/"
    return f"{u.scheme}://{u.netloc}{path}"


def _allowed_prefix(page_url: str, policy: NetPolicy | None) -> str | None:
    """The allow-listed path prefix that admits this page (bundled demo, evaluation
    servers), or None for an ordinary public site."""
    if policy is None:
        return None
    path = urlparse(page_url).path or "/"
    hits = [prefix for origin, prefix in policy.allowed if origin_of(page_url) == origin and path.startswith(prefix)]
    return max(hits, key=len) if hits else None


def brand_link(doc: Document) -> Node | None:
    """The brand/home link: rel=home, else the first link of the banner (header)."""
    def usable(n: Node) -> bool:
        href = (n.attrs.get("href") or "").strip()
        return (n.tag == "a" and bool(href) and not href.lower().startswith(_SKIP_HREF)
                and "hreflang" not in n.attrs and "lang" not in n.attrs)

    brand = doc.find(lambda n: usable(n) and "home" in (n.attrs.get("rel") or "").lower().split())
    if brand is None:
        banner = doc.find(lambda n: n.tag == "header" or n.role == "banner")
        brand = banner.find(usable) if banner is not None else None
    return brand


def site_name(doc: Document) -> str:
    """The site or organisation name as the brand link announces it ("" when unknown)."""
    brand = brand_link(doc)
    return brand.accessible_name() if brand is not None else ""


def site_root(page_url: str, doc: Document, policy: NetPolicy | None = None) -> str:
    """The site's home page (page key): the target of the brand/home link (rel=home, else
    the first link of the banner), else the origin's "/" (for file: scans the page's
    folder), never above an allow-listed prefix."""
    u = urlparse(page_url)
    brand = brand_link(doc)
    root = None
    if brand is not None:
        t = urlparse(urljoin(page_url, brand.attrs["href"].strip()))
        if (t.scheme, t.netloc) == (u.scheme, u.netloc) and not _NOT_PAGE.search(t.path):
            root = page_key(t.geturl())
    if root is None:
        root = page_key(scope_prefix(page_url)) if u.scheme == "file" else f"{u.scheme}://{u.netloc}/"
    prefix = _allowed_prefix(page_url, policy)
    if prefix and not urlparse(root).path.startswith(prefix):
        root = origin_of(page_url) + prefix
    return root


def sample_budget(check: BaseCheck) -> float:
    """Seconds a check may spend on the site sample now: SAMPLE_BUDGET_S, and never more
    than what is left of KLAR_SCAN_TIMEOUT (the checks are created when the scan starts;
    same idea as remaining_budget() in c_2_4_3). site_sample() also caps it with
    page.remaining(), the pipeline's own scan deadline."""
    created = getattr(check, "_created", None)
    if created is None:
        return SAMPLE_BUDGET_S
    return max(0.0, min(SAMPLE_BUDGET_S, check.settings.scan_timeout - (time.monotonic() - created)))


class SiteSampling:
    """Mixin for checks that use the site sample: starts the scan clock (for the budget)."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._created = time.monotonic()

    def site(self, page: CapturedPage) -> "SiteSample":
        return site_sample(page, budget=sample_budget(self))  # type: ignore[arg-type]


class _Fetcher:
    """GET pages of the audited site: one HTTP client per sample, every hop checked by the
    scan's network policy and kept on the same origin, a byte cap, a per-page deadline,
    the sample deadline and a request cap. Never submits forms, never runs scripts."""

    def __init__(self, page: CapturedPage, deadline: float):
        self.page = page
        self.deadline = deadline
        self.requests = 0
        self.cut = False  # a deadline or the request cap stopped a fetch
        self._client: httpx.Client | None = None

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def left(self) -> float:
        return self.deadline - time.monotonic()

    def get(self, url: str) -> str | None:
        try:
            return self._get(url)
        except Exception as exc:  # network errors, malformed responses: the page is simply missing
            log.info("site sample: fetching %s failed: %s", url, exc)
            return None

    def _get(self, url: str) -> str | None:
        u = urlparse(url)
        if u.scheme == "file":
            if urlparse(self.page.url).scheme != "file":
                return None
            path = Path(url2pathname(u.path))
            if path.is_dir():
                path = path / "index.html"
            if not path.is_file():
                return None
            with path.open("rb") as fh:
                return fh.read(MAX_BYTES).decode("utf-8", errors="replace")
        if u.scheme not in ("http", "https"):
            return None
        stop = min(time.monotonic() + FETCH_DEADLINE, self.deadline)
        if self._client is None:
            self._client = httpx.Client(follow_redirects=False, timeout=FETCH_TIMEOUT,
                                        headers={"User-Agent": USER_AGENT})
        current = url
        for _ in range(4):
            if time.monotonic() >= stop or self.requests >= MAX_REQUESTS:
                self.cut = True
                return None
            verdict = self.page.policy.check(current)
            if not verdict.ok or not self.page.same_origin(current):
                self.page.policy.log_block(current, "site sample: " + (verdict.reason or "other origin"))
                return None
            self.requests += 1
            timeout = httpx.Timeout(max(0.2, min(FETCH_TIMEOUT, stop - time.monotonic())))
            with self._client.stream("GET", current, timeout=timeout) as r:
                if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("location"):
                    current = urljoin(current, r.headers["location"])
                    continue
                if r.status_code != 200 or "html" not in r.headers.get("content-type", ""):
                    return None
                buf = bytearray()
                for chunk in r.iter_bytes():
                    buf += chunk
                    if len(buf) > MAX_BYTES:
                        break
                    if time.monotonic() > stop:  # absolute deadline, also for a server that drips bytes
                        self.cut = True
                        return None
                return bytes(buf[:MAX_BYTES]).decode(r.encoding or "utf-8", errors="replace")
        return None


@dataclass
class SitePage:
    url: str
    doc: Document
    depth: int = 0

    @property
    def key(self) -> str:
        return page_key(self.url)

    @property
    def lang(self) -> str:
        return (self.doc.lang or "").strip().lower().replace("_", "-").split("-")[0]

    @property
    def content_lang(self) -> str:
        """Language of the main text (detector), else the declared one. Language versions
        are separate sets of pages, and a version may declare the wrong language."""
        root = self.doc.main or self.doc.body
        text = root.text(limit=800)[:800]
        if len(text.split()) >= 5:
            from klar.config import Settings
            from klar.langid import get_detector

            d = get_detector(Settings().detect_langs).detect(text)
            if d is not None and d.confidence >= 0.5:
                return d.lang
        return self.lang

    def links(self) -> list[tuple[str, str, Node]]:
        """(page key, address to request, <a> node) for every link to an HTML page of the
        same origin. A query that only selects a view (search, filter…) is dropped."""
        out = []
        me = urlparse(self.url)
        for a in self.doc.find_all(lambda n: n.tag == "a" and "href" in n.attrs):
            href = (a.attrs.get("href") or "").strip()
            if not href or href.lower().startswith(_SKIP_HREF):
                continue
            url = urldefrag(urljoin(self.url, href))[0]
            t = urlparse(url)
            if (t.scheme, t.netloc) != (me.scheme, me.netloc) or _NOT_PAGE.search(t.path):
                continue
            out.append((page_key(url), request_url(url), a))
        return out


@dataclass
class SiteSample:
    entry: SitePage | None
    pages: list[SitePage] = field(default_factory=list)
    complete: bool = True  # False when a limit (pages, queries, depth, time, requests) stopped the crawl
    linked: bool = False  # the entry page links to at least one other page of the same origin
    reason: str = ""  # why there is no sample ("inline_html")
    root: str = ""  # page key of the site's home page
    scope: str = ""  # address prefix of the sampled pages
    home: SitePage | None = None  # the home page (sampled, or fetched for its title only)
    requests: int = 0

    def by_key(self) -> dict[str, SitePage]:
        return {p.key: p for p in self.pages}

    def same_set(self) -> list[SitePage]:
        """The entry page and the sampled pages in the same language (one set of pages)."""
        if self.entry is None:
            return []
        lang = self.entry.content_lang
        return [p for p in self.pages if p is self.entry or p.content_lang == lang]

    def in_scope(self, key: str) -> bool:
        return bool(self.scope) and key.startswith(self.scope)


def site_sample(page: CapturedPage, *, budget: float | None = None) -> SiteSample:
    """The bounded sample of the audited site, built once per scan and memoised on the
    CapturedPage (nothing is cached across scans). See the module docstring."""
    memo = page.__dict__.get("_klar_site_sample")
    if memo is not None:
        return memo
    # Never past the scan deadline set by the pipeline (page.remaining(); inf when unbounded).
    remaining = page.remaining() if hasattr(page, "remaining") else SAMPLE_BUDGET_S
    sample = _build_sample(page, max(0.0, min(SAMPLE_BUDGET_S if budget is None else budget, remaining)))
    page.__dict__["_klar_site_sample"] = sample
    return sample


def _build_sample(page: CapturedPage, budget: float) -> SiteSample:
    """Breadth-first from the audited page: links in navigation, header and footer first;
    only <a href> links (never forms); language-switcher links are not followed."""
    u = urlparse(page.url)
    if u.scheme not in ("http", "https", "file"):
        return SiteSample(entry=None, reason="inline_html")
    fetcher = _Fetcher(page, time.monotonic() + max(0.0, budget))
    try:
        raw = fetcher.get(page.url) if budget > 0 else None
        entry = SitePage(page.url, parse_html(raw) if raw else page_doc(page), 0)
        root = site_root(page.url, entry.doc, page.policy)
        if u.scheme == "file":
            scope = scope_prefix(root)
        else:
            scope = origin_of(page.url) + (_allowed_prefix(page.url, page.policy) or "/")
        sample = SiteSample(entry=entry, pages=[entry], root=root, scope=scope)
        seen = {entry.key}
        queries = 0
        frontier = [entry]
        while frontier:
            nxt: list[SitePage] = []
            for sp in frontier:
                links = sorted(sp.links(), key=lambda kla: region_of(kla[2]) not in ("nav", "header", "footer"))
                for key, url, a in links:
                    if sp is entry and key != entry.key:
                        sample.linked = True  # any same-origin page link, in scope or not
                    if key in seen or not sample.in_scope(key) or "hreflang" in a.attrs or "lang" in a.attrs:
                        continue  # language-switcher links lead to another set of pages
                    seen.add(key)
                    is_query = bool(urlsplit(key).query)
                    if (len(sample.pages) >= MAX_PAGES or (is_query and queries >= MAX_QUERY_PAGES)
                            or fetcher.left() <= 0 or fetcher.requests >= MAX_REQUESTS):
                        sample.complete = False
                        continue
                    html = fetcher.get(url)
                    if not html:
                        continue
                    queries += is_query
                    child = SitePage(url, parse_html(html), sp.depth + 1)
                    sample.pages.append(child)
                    if child.depth < MAX_DEPTH:
                        nxt.append(child)
                    elif any(sample.in_scope(k) and k not in seen for k, _, _ in child.links()):
                        sample.complete = False
            frontier = nxt
        if fetcher.cut:
            sample.complete = False
        sample.home = sample.by_key().get(root)
        if sample.home is None and sample.in_scope(root) and fetcher.left() > 0 and fetcher.requests < MAX_REQUESTS:
            raw_home = fetcher.get(root)  # for its title only (2.4.2); not part of the link graph
            if raw_home:
                sample.home = SitePage(root, parse_html(raw_home), 1)
        sample.requests = fetcher.requests
        return sample
    finally:
        fetcher.close()


def is_home(sp: SitePage, sample: SiteSample) -> bool:
    """The site's home page: the target of the brand/home link (see site_root)."""
    return bool(sample.root) and sp.key == sample.root


def short_path(url: str, base: str) -> str:
    """Page address relative to the folder of `base` (the site root), for explanations."""
    pre = scope_prefix(base)
    return (url[len(pre):] or "./") if url.startswith(pre) else (urlparse(url).path or url)


# ---------------------------------------------------------------------------------------
# 2.4.5 Multiple Ways
# ---------------------------------------------------------------------------------------

SITE_WIDE_SHARE = 0.5
SITEMAP_COVERAGE = 0.8
SMALL_SITE = 5
_QUOTED_URL = re.compile(r"""["']([^"'\s<>]{1,200})["']""")

register({
    "c245.passed": {
        "en": "Each of the {n} sampled pages can be reached in at least two ways ({ways}).",
        "de": "Jede der {n} geprüften Seiten ist auf mindestens zwei Wegen erreichbar ({ways}).",
        "fr": "Chacune des {n} pages examinées est accessible par au moins deux moyens ({ways}).",
        "it": "Ognuna delle {n} pagine esaminate è raggiungibile in almeno due modi ({ways}).",
    },
    "c245.small_site": {
        "en": "Small site: each of the {n} pages links to all the others, which is enough to find every page.",
        "de": "Kleine Website: Jede der {n} Seiten verlinkt alle anderen; so ist jede Seite auffindbar.",
        "fr": "Petit site : chacune des {n} pages renvoie vers toutes les autres, ce qui suffit pour trouver chaque page.",
        "it": "Sito piccolo: ognuna delle {n} pagine rimanda a tutte le altre, il che basta per trovare ogni pagina.",
    },
    "c245.failed": {
        "en": "Pages with only one way to reach them (no site map, search or second set of links lists them): {pages}.",
        "de": "Seiten mit nur einem Zugangsweg (keine Sitemap, Suche oder zweite Linkliste führt sie auf): {pages}.",
        "fr": "Pages accessibles par un seul chemin (aucun plan du site, aucune recherche ni seconde liste de liens ne les répertorie) : {pages}.",
        "it": "Pagine raggiungibili in un solo modo (nessuna mappa del sito, ricerca o seconda lista di link le elenca): {pages}.",
    },
    "c245.impact": {
        "en": "People who cannot use the menu easily, for example with a screen reader or a magnifier, have no other way to find these pages.",
        "de": "Wer das Menü schlecht bedienen kann, etwa mit Screenreader oder Vergrösserung, findet diese Seiten auf keinem anderen Weg.",
        "fr": "Les personnes qui ont du mal à utiliser le menu, par exemple avec un lecteur d'écran ou une loupe, n'ont aucun autre moyen de trouver ces pages.",
        "it": "Chi ha difficoltà a usare il menu, per esempio con un lettore di schermo o un ingranditore, non ha altri modi per trovare queste pagine.",
    },
    "c245.impact_ok": {
        "en": "People can reach each page in more than one way: menu, links, site map or search.",
        "de": "Man erreicht jede Seite auf mehr als einem Weg: über Menü, Links, Sitemap oder Suche.",
        "fr": "Chaque page est accessible par plusieurs chemins : menu, liens, plan du site ou recherche.",
        "it": "Ogni pagina è raggiungibile in più di un modo: menu, link, mappa del sito o ricerca.",
    },
    "c245.external_search": {
        "en": "The search sends queries to another website, so its coverage of this site cannot be checked. Without it, only one way leads to: {pages}.",
        "de": "Die Suche schickt Anfragen an eine andere Website; ob sie diese Seiten abdeckt, lässt sich nicht prüfen. Ohne sie führt nur ein Weg zu diesen Seiten: {pages}.",
        "fr": "La recherche envoie les requêtes à un autre site ; sa couverture de ce site ne peut pas être vérifiée. Sans elle, un seul chemin mène à : {pages}.",
        "it": "La ricerca invia le richieste a un altro sito; non si può verificare se copre questo sito. Senza di essa, un solo percorso porta a: {pages}.",
    },
    "c245.breadcrumbs": {
        "en": "Besides the menu, only breadcrumbs lead to {pages}. Whether breadcrumbs count as a second way is disputed: a person must decide.",
        "de": "Neben dem Menü führt nur ein Brotkrumenpfad zu {pages}. Ob er als zweiter Weg zählt, ist umstritten: Eine Person muss entscheiden.",
        "fr": "En plus du menu, seul un fil d'Ariane mène à {pages}. Compte-t-il comme second chemin ? Les avis divergent : une personne doit trancher.",
        "it": "Oltre al menu, solo il percorso di navigazione (breadcrumb) porta a {pages}. Se valga come secondo modo è controverso: una persona deve decidere.",
    },
    "c245.incomplete": {
        "en": "The sample stopped at {n} pages. So far only one way leads to: {pages}. A site map or search may exist elsewhere: a person must check.",
        "de": "Die Stichprobe endete bei {n} Seiten. Bisher gibt es nur einen Weg zu diesen Seiten: {pages}. Eine Sitemap oder Suche könnte anderswo liegen: Eine Person muss prüfen.",
        "fr": "L'échantillon s'est arrêté à {n} pages. Pour l'instant, un seul chemin mène à : {pages}. Un plan du site ou une recherche peut exister ailleurs : une personne doit vérifier.",
        "it": "Il campione si è fermato a {n} pagine. Finora un solo percorso porta a: {pages}. Una mappa o una ricerca potrebbe trovarsi altrove: una persona deve verificare.",
    },
    "c245.needs_url": {
        "en": "The Multiple Ways criterion concerns a set of pages; pasted HTML has no site around it. Scan the page by its address.",
        "de": "Das Kriterium «Mehrere Zugangswege» betrifft eine Gruppe von Seiten; eingefügtes HTML gehört zu keiner Website. Scannen Sie die Seite über ihre Adresse.",
        "fr": "Le critère Accès multiples concerne un ensemble de pages ; le HTML collé n'appartient à aucun site. Analysez la page par son adresse.",
        "it": "Il criterio 2.4.5 (Più modalità) riguarda un insieme di pagine; l'HTML incollato non ha un sito intorno. Analizzate la pagina tramite il suo indirizzo.",
    },
    "c245.too_few": {
        "en": "The other pages of the site could not be loaded, so the ways to reach them cannot be compared. A person must check.",
        "de": "Die anderen Seiten der Website liessen sich nicht laden; die Zugangswege können nicht verglichen werden. Eine Person muss prüfen.",
        "fr": "Les autres pages du site n'ont pas pu être chargées ; les chemins d'accès ne peuvent pas être comparés. Une personne doit vérifier.",
        "it": "Le altre pagine del sito non si sono potute caricare; i percorsi non si possono confrontare. Una persona deve verificare.",
    },
    "c245.single_page": {
        "en": "This page links to no other page of the same site: there is no set of pages to find.",
        "de": "Diese Seite verlinkt keine andere Seite derselben Website: Es gibt keine Gruppe von Seiten, die auffindbar sein müsste.",
        "fr": "Cette page ne renvoie vers aucune autre page du même site : il n'y a pas d'ensemble de pages à trouver.",
        "it": "Questa pagina non rimanda ad altre pagine dello stesso sito: non c'è un insieme di pagine da trovare.",
    },
    "c245.fix_hint": {
        "en": "Add a site map or a site search that lists every page, or link these pages from a second place.",
        "de": "Ergänzen Sie eine Sitemap oder eine Suche, die alle Seiten enthält, oder verlinken Sie diese Seiten an einer zweiten Stelle.",
        "fr": "Ajoutez un plan du site ou une recherche qui couvre toutes les pages, ou liez ces pages depuis un second endroit.",
        "it": "Aggiungete una mappa del sito o una ricerca che copra tutte le pagine, oppure collegate queste pagine da un secondo punto.",
    },
    "c245.way.nav": {"en": "menu", "de": "Menü", "fr": "menu", "it": "menu"},
    "c245.way.links": {"en": "links in content", "de": "Links im Inhalt", "fr": "liens dans le contenu", "it": "link nel contenuto"},
    "c245.way.sitemap": {"en": "site map or index", "de": "Sitemap oder Index", "fr": "plan du site ou index", "it": "mappa del sito o indice"},
    "c245.way.search": {"en": "search", "de": "Suche", "fr": "recherche", "it": "ricerca"},
})


def search_coverage(sp: SitePage, form: Node, known: set[str],
                    results_page: Callable[[str], "SitePage | None"] | None = None) -> set[str] | str:
    """Pages a search form covers: a set of page keys (an inline index on the form's page
    or on its results page), "all" (same-origin search without an inline index: assumed
    site-wide) or "external" (another origin: not observable)."""
    action = (form.attrs.get("action") or "").strip()
    target = urljoin(sp.url, action) if action and not action.startswith("#") else sp.url
    tu, su = urlparse(target), urlparse(sp.url)
    if tu.scheme in ("http", "https", "file") and (tu.scheme, tu.netloc) != (su.scheme, su.netloc):
        return "external"
    docs = [sp]
    if results_page is not None and page_key(target) != sp.key:
        rp = results_page(page_key(target))
        if rp is not None:
            docs.append(rp)
    covered: set[str] = set()
    for d in docs:
        for script in (n for n in d.doc.iter() if n.tag == "script" and "src" not in n.attrs):
            body = "".join(c for c in script.children if isinstance(c, str))
            for m in _QUOTED_URL.finditer(body):
                key = page_key(urljoin(d.url, m.group(1)))
                if key in known:
                    covered.add(key)
    return covered if len(covered) >= 2 else "all"


class MultipleWays(SiteSampling, BaseCheck):
    criterion = "2.4.5"
    prompt_version = PROMPT_VERSION
    max_candidates = 1

    def candidates(self, page: CapturedPage) -> list[Candidate]:
        sample = self.site(page)
        doc = page_doc(page)
        nav = doc.find(lambda n: (n.tag == "nav" or n.role == "navigation") and not is_breadcrumb(n))
        html = nav.outer(800) if nav is not None else (doc.html_el.outer(200) if doc.html_el else "<html>")
        text = nav.text() if nav is not None else ""
        extra = self.analyse(sample)
        return [self.candidate(page, selector=live_selector(page, nav), html=html, text=text, lang=page.lang,
                               key="#site", **extra)]

    # -- facts (code) --------------------------------------------------------------------
    @staticmethod
    def analyse(sample: SiteSample) -> dict:
        if sample.entry is None:
            return {"kind": "needs_url"}
        pages = sample.same_set()
        n = len(pages)
        if n < 2:
            return {"kind": "too_few" if sample.linked else "single_page", "n": n}
        base = sample.root
        known = {p.key for p in pages}
        links_of = {p.key: [(k, a) for k, _url, a in p.links() if k in known and k != p.key] for p in pages}

        # Small site (G126 / Understanding): every page links to every other page.
        if sample.complete and n <= SMALL_SITE and all({k for k, _ in links_of[p.key]} >= known - {p.key} for p in pages):
            return {"kind": "small_site", "n": n}

        nav_pages: Counter = Counter()
        content_targets: set[str] = set()
        for p in pages:
            nav_here: set[str] = set()
            for k, a in links_of[p.key]:
                region = region_of(a)
                if region in ("nav", "header", "footer", "aside") and not is_breadcrumb(a):
                    nav_here.add(k)
                else:
                    content_targets.add(k)
            nav_pages.update(nav_here)
        need = max(2, -(-n // 2)) if n > 2 else 1
        site_wide = {k for k, c in nav_pages.items() if c >= need}
        # Links in a block that is not repeated site-wide (sub-navigation, teasers) are content links.
        for p in pages:
            for k, a in links_of[p.key]:
                if k not in site_wide and not is_breadcrumb(a):
                    content_targets.add(k)

        sitemap_cover: set[str] = set()
        sitemaps: set[str] = set()
        for p in pages:
            targets = {k for k, a in links_of[p.key] if region_of(a) in ("main", "other")}
            if len(targets) >= max(3, SITEMAP_COVERAGE * (n - 1)) and p.key in site_wide:
                sitemap_cover |= targets
                sitemaps.add(p.key)

        by_key = {p.key: p for p in sample.pages}

        def results_page(key: str) -> SitePage | None:
            return by_key.get(key)

        # Steps of a process (pages that a non-search form submits to) are exempt (SC exception).
        process_steps = {page_key(urljoin(p.url, f.attrs.get("action") or "")) for p in pages
                         for f in p.doc.find_all(lambda x: x.tag == "form")
                         if not is_search_form(f) and (f.attrs.get("action") or "").strip() not in ("", "#")}

        search_cover: set[str] = set()
        external_search = False
        search_pages = 0
        for p in pages:
            forms = [f for f in p.doc.find_all(lambda x: x.tag == "form") if is_search_form(f)]
            if not forms:
                continue
            search_pages += 1
            for f in forms:
                cov = search_coverage(p, f, known, results_page)
                if cov == "external":
                    external_search = True
                elif cov == "all":
                    search_cover |= known
                else:
                    search_cover |= cov
        if search_pages < need:
            search_cover = set()

        breadcrumbs = any(is_breadcrumb(a) for p in pages for _, a in links_of[p.key])
        ways: dict[str, list[str]] = {}
        lacking: list[str] = []
        for p in pages:
            if is_home(p, sample) or p.key in sitemaps or p.key in process_steps:
                continue  # the entry point, the site map itself, steps of a process
            w = [name for name, ok in (("nav", p.key in site_wide), ("links", p.key in content_targets),
                                       ("sitemap", p.key in sitemap_cover), ("search", p.key in search_cover)) if ok]
            ways[p.key] = w
            if len(w) < 2:
                lacking.append(p.key)
        used = sorted({w for ws in ways.values() for w in ws}, key=["nav", "links", "sitemap", "search"].index)
        common = {"n": n, "ways_used": used, "lacking": [short_path(k, base) for k in lacking][:5],
                  "complete": sample.complete}
        if not lacking:
            return {"kind": "passed", **common}
        if not sample.complete:
            return {"kind": "incomplete", **common}
        if external_search:
            return {"kind": "external_search", **common}
        if breadcrumbs and not sitemap_cover and not search_cover:
            return {"kind": "breadcrumbs", **common}  # menu + breadcrumbs only (PROTOCOL 2.4.5/C2)
        return {"kind": "failed", **common}

    # -- decisions (code) -------------------------------------------------------------------
    def decide(self, c: Candidate) -> Finding | None:
        ui = self.ui_lang
        kind = c.extra.get("kind")
        pages = ", ".join(c.extra.get("lacking") or [])
        n = c.extra.get("n", 0)
        excerpt = c.text[:300] if c.text else None
        if kind == "single_page":
            return self.finding(c, outcome="inapplicable", source="heuristic", confidence="medium", excerpt=excerpt,
                                explanation=t("c245.single_page", ui), user_impact=t("impact.review", ui))
        if kind in ("needs_url", "too_few"):
            return self.note(c, f"c245.{kind}", source="heuristic")
        if kind == "small_site":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", excerpt=excerpt,
                                explanation=t("c245.small_site", ui, n=n), user_impact=t("c245.impact_ok", ui))
        if kind == "passed":
            ways = ", ".join(t(f"c245.way.{w}", ui) for w in c.extra.get("ways_used", []))
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", excerpt=excerpt,
                                explanation=t("c245.passed", ui, n=n, ways=ways), user_impact=t("c245.impact_ok", ui))
        if kind in ("incomplete", "external_search", "breadcrumbs"):
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="low", excerpt=excerpt,
                                explanation=t(f"c245.{kind}", ui, pages=pages, n=n),
                                user_impact=t("c245.impact", ui), fix_hint=t("c245.fix_hint", ui))
        return self.finding(c, outcome="failed", source="heuristic", confidence="medium", excerpt=excerpt,
                            explanation=t("c245.failed", ui, pages=pages), user_impact=t("c245.impact", ui),
                            fix_hint=t("c245.fix_hint", ui))

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:  # pragma: no cover - decide() always answers
        raise NotImplementedError("2.4.5 is decided in code")


CHECK = MultipleWays
