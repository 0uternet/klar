"""CapturedPage: everything a check may look at, computed in code.

Element records (plain dicts produced by capture/js/klar_extract.js; `name` is
Chromium's computed accessible name via CDP, `name_js` the JS fallback):

  links          selector, tag, html, text, href, raw_href, name, role, lang,
                 context{sentence, paragraph, list_item, table_cell, table_headers, described_by},
                 image_alts, target, title, heading_hint, hreflang, own_lang (lang attribute), rect
  images         selector, tag, html, alt (None = no attribute), role, aria_hidden,
                 decorative_markup, name, src, natural{w,h}, rect, lang, in_link,
                 context{caption, link_href, link_text, surrounding_text, title}
  passages       selector, tag, html, text, lang (inherited), own_lang, container_selector,
                 container_text, is_container
  lang_elements  selector, tag, lang, text, html, parent_lang
  fields         selector, tag, type, html, name, labels, legend, describedby, errormessage,
                 placeholder, title, required, autocomplete, field_name, id, invalid, lang, form, rect
  forms          selector, html, action, method, novalidate, field_count, submit
  headings       selector, html, text, lang, level

`live` is the Playwright page. It is only valid inside the pipeline thread while
the scan runs (Playwright's sync API is not thread-safe): use it in
`candidates()`, never in `question()`/`interpret()`.
"""

from __future__ import annotations

import hashlib
import logging
import math
import re
import ssl
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import url2pathname

import httpx

from klar.netpolicy import NetPolicy

log = logging.getLogger(__name__)

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_MAX_TITLE_BYTES = 262144  # a destination's <title> is read from its first 256 kB
_MIN_FETCH_SECONDS = 0.2  # below this, a title fetch is not started
_SSL: ssl.SSLContext | None = None
_SSL_LOCK = threading.Lock()


def _ssl_context() -> ssl.SSLContext:
    """One TLS context per process: building it (CA bundle) takes ~0.5–1 s on a small
    machine, which must not eat the 2.5 s of a title fetch."""
    global _SSL
    with _SSL_LOCK:
        if _SSL is None:
            import certifi

            _SSL = ssl.create_default_context(cafile=certifi.where())
        return _SSL


def candidate_id(page_url: str, selector: str, criterion: str) -> str:
    """Stable candidate id: sha1(page_url + selector + criterion)[:12]."""
    return hashlib.sha1(f"{page_url}{selector}{criterion}".encode("utf-8")).hexdigest()[:12]


@dataclass
class CapturedPage:
    url: str  # final URL after redirects ("about:blank" for raw HTML)
    requested_url: str
    title: str
    lang: str | None  # <html lang>
    html: str  # serialised DOM after rendering
    text: str  # body innerText
    scan_dir: Path
    elements: dict[str, list[dict]] = field(default_factory=dict)
    axe: dict = field(default_factory=dict)
    allow_form_submit: bool = False  # True only for the bundled demo and the eval servers
    # origins whose forms may be submitted (CaptureOptions.form_origins, copied by render());
    # empty = none. Anything that submits must require the page's final origin AND the form
    # target's origin to be in here (never fall back to the page's own origin: after a
    # redirect or meta refresh that may be any external site).
    form_origins: tuple[str, ...] = ()
    source_html: str | None = None  # raw HTML when scanned via set_content
    live: Any = None  # playwright.sync_api.Page | None
    policy: NetPolicy = field(default_factory=NetPolicy)  # URL policy (also for fetch_title)
    http_status: int | None = None  # status of the navigation response (None for raw HTML)
    # time.monotonic() timestamp by which the whole scan must be finished (KLAR_SCAN_TIMEOUT),
    # set by the pipeline right after rendering; None = unbounded. Checks read remaining().
    deadline: float | None = None
    id_base: str | None = None  # what candidate ids are computed from (default: url)
    title_fetch_budget: int = 8  # destination titles fetched per page (2.4.4 fixes)
    title_fetch_seconds: float = 6.0  # wall-clock budget for all title fetches of this page
    title_fetch_timeout: float = 2.5  # hard limit for one title fetch (all hops, headers and body)
    title_fetch_stats: dict[str, int] = field(default_factory=lambda: {"fetched": 0, "timed_out": 0, "skipped": 0})
    _title_spent: float = 0.0
    _title_cache: dict[str, str | None] = field(default_factory=dict)
    _form_probe: list[dict] | None = None
    _form_probe_fn: Callable[["CapturedPage"], list[dict]] | None = None

    # -- element collections -------------------------------------------------------
    @property
    def links(self) -> list[dict]:
        return self.elements.get("links", [])

    @property
    def images(self) -> list[dict]:
        return self.elements.get("images", [])

    @property
    def passages(self) -> list[dict]:
        return self.elements.get("passages", [])

    @property
    def lang_elements(self) -> list[dict]:
        return self.elements.get("lang_elements", [])

    @property
    def fields(self) -> list[dict]:
        return self.elements.get("fields", [])

    @property
    def forms(self) -> list[dict]:
        return self.elements.get("forms", [])

    @property
    def headings(self) -> list[dict]:
        return self.elements.get("headings", [])

    def known_selectors(self) -> set[str]:
        out = set()
        for records in self.elements.values():
            for r in records:
                for key in ("selector", "container_selector"):
                    if r.get(key):
                        out.add(r[key])
        return out

    # -- scan time -------------------------------------------------------------------------
    def remaining(self) -> float:
        """Seconds left before the scan deadline (`deadline`); math.inf when unbounded.
        A check doing slow work in candidates() (network, many evaluate() calls, a site
        sample) stops when this reaches 0 and returns what it has; the pipeline turns
        whatever is left into cantTell `timeout` notes."""
        return math.inf if self.deadline is None else self.deadline - time.monotonic()

    # -- live helpers (pipeline thread only) ------------------------------------------
    def evaluate(self, expression: str, arg: Any = None) -> Any:
        """Run JS in the audited page. `window.__klar` in the expression is rewritten to
        the extractor's (randomised) global name. None if the page is not live."""
        if self.live is None:
            return None
        from klar.capture.browser import js

        return self.live.evaluate(js(expression), arg)

    def describe(self, selector: str) -> dict | None:
        return self.evaluate("s => window.__klar.describe(s)", selector)

    def selector_exists(self, selector: str) -> bool:
        if self.live is not None:
            try:
                return bool(self.evaluate("s => window.__klar.count(s) > 0", selector))
            except Exception:
                return False
        return selector in self.known_selectors()

    def screenshot(self, selector: str, name: str) -> str | None:
        """PNG crop of one element → path relative to scan_dir, or None."""
        if self.live is None:
            return None
        rel = f"crops/{name}.png"
        path = self.scan_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            loc = self.live.locator(selector).first
            box = loc.bounding_box(timeout=3000)
            if not box or box["width"] < 1 or box["height"] < 1:
                return None
            loc.screenshot(path=str(path), animations="disabled", timeout=5000, scale="css")
            return rel
        except Exception as exc:
            log.info("screenshot of %s failed: %s", selector, exc)
            return None

    def form_probe(self) -> list[dict]:
        """Lazy interaction probe (see capture/probe.py). Empty unless allow_form_submit."""
        if self._form_probe is None:
            self._form_probe = self._form_probe_fn(self) if (self._form_probe_fn and self.allow_form_submit) else []
        return self._form_probe

    # -- destination titles (2.4.4 fix suggestions) -------------------------------
    def same_origin(self, href: str) -> bool:
        a, b = urlparse(self.url), urlparse(href)
        if a.scheme == "file" and b.scheme == "file":
            return True
        return a.scheme in ("http", "https") and (a.scheme, a.netloc) == (b.scheme, b.netloc)

    def fetch_title(self, href: str) -> str | None:
        """<title> of a same-origin destination, cheap and bounded: at most
        `title_fetch_budget` fetches and `title_fetch_seconds` of wall-clock time per page,
        each fetch at most `title_fetch_timeout` s and never past the scan deadline, first
        256 kB only. None when unknown. Never leaves the audited site."""
        href = urldefrag(href)[0]
        if not href or not self.same_origin(href):
            return None
        if href in self._title_cache:
            return self._title_cache[href]
        if urldefrag(self.url)[0] == href:
            self._title_cache[href] = self.title or None
            return self._title_cache[href]
        if self.title_fetch_budget <= 0:
            return None
        if not href.startswith("file:"):
            _ssl_context()  # once per process, before the clock starts
        limit = min(self.title_fetch_timeout, self.title_fetch_seconds - self._title_spent, self.remaining())
        if limit < _MIN_FETCH_SECONDS:  # out of time: unknown, not cached (not the page's fault)
            self.title_fetch_stats["skipped"] += 1
            return None
        self.title_fetch_budget -= 1
        title = None
        t0 = time.monotonic()
        try:
            if href.startswith("file:"):
                p = Path(url2pathname(urlparse(href).path))
                if p.is_dir():
                    p = p / "index.html"
                if p.is_file():
                    title = self._parse_title(p.read_text(encoding="utf-8", errors="replace")[:_MAX_TITLE_BYTES])
            else:
                title = self._http_title(href, limit)
        except Exception as exc:
            log.info("title fetch for %s failed: %s", href, exc)
        finally:
            self._title_spent += time.monotonic() - t0
        self.title_fetch_stats["fetched"] += 1
        self._title_cache[href] = title
        return title

    def _http_title(self, href: str, limit: float | None = None) -> str | None:
        """Hard wall-clock limit of `limit` seconds for the whole fetch (all redirect hops,
        headers and body). httpx timeouts are per read, so a server that drips one byte
        per second would never trip them: the fetch runs in a daemon thread, the caller
        waits at most `limit`, and the thread itself stops reading at the same deadline."""
        limit = self.title_fetch_timeout if limit is None else limit
        if limit <= 0:
            return None
        stop = time.monotonic() + limit
        box: dict[str, Any] = {}

        def work() -> None:
            try:
                box["title"] = self._http_title_until(href, stop)
            except Exception as exc:  # re-raised in the caller's thread
                box["error"] = exc

        worker = threading.Thread(target=work, name="klar-title-fetch", daemon=True)
        worker.start()
        worker.join(max(0.0, stop - time.monotonic()) + 0.05)
        # out of time, whether the caller noticed first or the worker (deadline in its
        # read loop, or httpx's read timeout set to the time left)
        if worker.is_alive() or (box.get("title") is None and time.monotonic() >= stop):
            self.title_fetch_stats["timed_out"] += 1
            log.info("title fetch for %s exceeded %.1f s", href, limit)
            return None
        if "error" in box:
            raise box["error"]
        return box.get("title")

    def _http_title_until(self, href: str, stop: float) -> str | None:
        """GET without automatic redirects: every hop must pass the URL policy and stay
        on the audited origin (a same-origin redirect to an internal IP is refused).
        Gives up at `stop` (time.monotonic()); parses whatever arrived until then."""
        current = href
        with httpx.Client(follow_redirects=False, verify=_ssl_context(),
                          headers={"User-Agent": "Klar./0.1 accessibility pre-check"}) as client:
            for _ in range(4):
                left = stop - time.monotonic()
                if left <= 0:
                    return None
                verdict = self.policy.check(current)
                if not verdict.ok or not self.same_origin(current):
                    self.policy.log_block(current, "title fetch: " + (verdict.reason or "other origin"))
                    return None
                # every single read is bounded by the time left at the start of this hop …
                with client.stream("GET", current, timeout=httpx.Timeout(left)) as r:
                    if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("location"):
                        current = urljoin(current, r.headers["location"])
                        continue
                    if r.status_code != 200 or "html" not in r.headers.get("content-type", ""):
                        return None
                    buf = bytearray()
                    for chunk in r.iter_bytes():
                        buf += chunk
                        # … and the loop itself by the deadline (slow drip), the size cap and
                        # the end of the <title> element (nothing after it is needed)
                        if (len(buf) > _MAX_TITLE_BYTES or time.monotonic() >= stop
                                or b"</title" in buf[-(len(chunk) + 8):].lower()):
                            break
                    return self._parse_title(bytes(buf).decode(r.encoding or "utf-8", errors="replace"))
        return None

    @staticmethod
    def _parse_title(html: str) -> str | None:
        import html as htmllib

        m = _TITLE_RE.search(html)
        if not m:
            return None
        t = re.sub(r"\s+", " ", htmllib.unescape(m.group(1))).strip()
        return t[:200] or None

    def close(self) -> None:
        if self.live is not None:
            try:
                self.live.context.close()
            except Exception:
                pass
            self.live = None

    # -- tests ------------------------------------------------------------------------
    @classmethod
    def from_elements(cls, *, url: str = "https://example.test/", lang: str | None = "de", scan_dir: Path | None = None,
                      title: str = "", html: str = "", text: str = "", **elements: list[dict]) -> "CapturedPage":
        """A page without a browser (unit tests of candidates/decide/interpret)."""
        return cls(url=url, requested_url=url, title=title, lang=lang, html=html, text=text,
                   scan_dir=scan_dir or Path("."), elements=dict(elements))
