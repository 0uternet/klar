"""Playwright Chromium rendering, DOM snapshot and element extraction.

Usage (one thread; Playwright's sync API is not thread-safe):

    with Browser() as b:
        page = render(b, url="https://…", scan_dir=Path("var/scans/x"), opts=CaptureOptions(policy=…))
        extract(page)            # links, images, passages, fields… + CDP names
        ...
        page.close()

Network policy (klar/netpolicy.py) is enforced on EVERY browser request by a
context-wide route. Playwright does not show redirect hops to route handlers,
so the handler fetches each request itself without following redirects,
checks every hop, and fulfils only the final response. WebSockets are mocked
(never connected), WebRTC is kept off non-proxied UDP, downloads are refused. Raw HTML is rendered with set_content (origin about:blank).
"""

from __future__ import annotations

import logging
import re
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx

from klar.capture.page import CapturedPage
from klar.netpolicy import NetPolicy, origin_of

log = logging.getLogger(__name__)

JS_DIR = Path(__file__).resolve().parent / "js"
_EXTRACT_SRC = (JS_DIR / "klar_extract.js").read_text(encoding="utf-8")
# A random global name per process: a hostile page cannot pre-define it.
KLAR_GLOBAL = "__klar_" + secrets.token_hex(6)
EXTRACT_JS = _EXTRACT_SRC.replace("window.__klar", f"window.{KLAR_GLOBAL}")
MAX_REDIRECTS = 6
# --disable-dev-shm-usage: small /dev/shm in containers.
# WebRTC is not covered by request routing: these flags keep it off non-proxied UDP,
# so a page cannot reach internal hosts (or leak local addresses) through ICE.
CHROMIUM_ARGS = [
    "--disable-dev-shm-usage",
    "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
    "--webrtc-ip-handling-policy=disable_non_proxied_udp",
]
REDIRECT_CODES = {301, 302, 303, 307, 308}

_LAZY_SCROLL_JS = """async () => {
  const step = Math.max(200, Math.floor(window.innerHeight * 0.8));
  const max = Math.min(document.documentElement.scrollHeight, 30000);
  for (let y = 0; y < max; y += step) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 50)); }
  window.scrollTo(0, 0);
  const pending = Array.from(document.images).filter(i => !i.complete);
  await Promise.race([
    Promise.all(pending.map(i => new Promise(r => { i.addEventListener('load', r, {once: true}); i.addEventListener('error', r, {once: true}); }))),
    new Promise(r => setTimeout(r, 3000)),
  ]);
}"""


def js(expr: str) -> str:
    """Rewrite `window.__klar` in a JS snippet to this process' random global."""
    return expr.replace("window.__klar", f"window.{KLAR_GLOBAL}")


class ScanError(RuntimeError):
    """A scan that could not render its page, with a stable error code (ScanStats.error_code):
    unreachable | tls | dns | timeout_page | blocked_redirect | too_many_redirects | not_html |
    browser | internal | blocked_private | blocked_metadata | blocked_localhost."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class BlockedURL(ScanError, ValueError):
    def __init__(self, message: str, code: str = "blocked_redirect"):
        super().__init__(code, message)


# Network error text (Chromium net::ERR_*, Node/Playwright fetch errors) -> error code.
_ERROR_PATTERNS = (
    ("dns", ("ERR_NAME_NOT_RESOLVED", "ENOTFOUND", "EAI_AGAIN", "getaddrinfo", "Name or service not known")),
    ("tls", ("ERR_CERT", "ERR_SSL", "SSL", "certificate", "CERT_", "TLS")),
    ("not_html", ("Download is starting", "download")),
    ("timeout_page", ("Timeout", "ERR_TIMED_OUT", "ETIMEDOUT", "timed out")),
    ("unreachable", ("ERR_CONNECTION", "ECONNREFUSED", "ECONNRESET", "ERR_ADDRESS_UNREACHABLE", "EHOSTUNREACH",
                     "ENETUNREACH", "ERR_INTERNET_DISCONNECTED", "ERR_EMPTY_RESPONSE", "ERR_NETWORK_CHANGED",
                     "socket hang up")),
)
_ABORT_FOR = {"dns": "namenotresolved", "unreachable": "connectionrefused", "timeout_page": "timedout"}
_POLICY_CODES = {"blocked_metadata", "blocked_localhost", "blocked_private", "dns"}


def classify_error(message: str) -> str:
    for code, needles in _ERROR_PATTERNS:
        if any(n in message for n in needles):
            return code
    return "internal"


def policy_code(verdict_code: str) -> str:
    return verdict_code if verdict_code in _POLICY_CODES else "internal"


@dataclass
class CaptureOptions:
    viewport_width: int = 1280
    viewport_height: int = 900
    timeout_ms: int = 30000
    idle_timeout_ms: int = 5000
    allow_form_submit: bool = False
    scroll: bool = True
    locale: str | None = None  # e.g. "de-CH"; None = browser default
    policy: NetPolicy = field(default_factory=NetPolicy)
    # origins that may receive non-GET requests from the form probe (bundled demo, test set)
    form_origins: tuple[str, ...] = ()


class Browser:
    """Owns one Playwright driver and one headless Chromium."""

    def __init__(self, *, headless: bool = True):
        self.headless = headless
        self._pw = None
        self.browser = None

    def __enter__(self) -> "Browser":
        from playwright.sync_api import sync_playwright

        try:
            self._pw = sync_playwright().start()
            self.browser = self._pw.chromium.launch(headless=self.headless, args=CHROMIUM_ARGS)
        except Exception as exc:
            if self._pw:
                self._pw.stop()
            raise ScanError("browser", f"Chromium could not start: {exc}") from exc
        return self

    def __exit__(self, *exc) -> None:
        try:
            if self.browser:
                self.browser.close()
        finally:
            if self._pw:
                self._pw.stop()

    def new_page(self, opts: CaptureOptions):
        ctx = self.browser.new_context(
            viewport={"width": opts.viewport_width, "height": opts.viewport_height},
            device_scale_factor=1,
            bypass_csp=True,
            service_workers="block",
            accept_downloads=False,
            locale=opts.locale,
        )
        ctx.set_default_timeout(opts.timeout_ms)
        install_policy(ctx, opts.policy)
        return ctx.new_page()


def install_policy(context, policy: NetPolicy) -> None:
    def handler(route, request):
        url = request.url
        verdict = policy.check(url)
        if not verdict.ok:
            policy.log_block(url, verdict.reason, policy_code(verdict.code))
            route.abort("blockedbyclient")
            return
        if urlparse(url).scheme not in ("http", "https"):
            route.continue_()
            return
        try:
            current, method = url, request.method
            for _ in range(MAX_REDIRECTS):
                if current == url:
                    resp = route.fetch(max_redirects=0)
                else:
                    resp = route.fetch(url=current, method=method, max_redirects=0)
                location = resp.headers.get("location")
                if resp.status in REDIRECT_CODES and location:
                    nxt = urljoin(current, location)
                    v = policy.check(nxt)
                    if not v.ok:
                        policy.log_block(nxt, "redirect: " + v.reason)
                        policy.note_error(url, "blocked_redirect")
                        route.abort("blockedbyclient")
                        return
                    if resp.status == 303 or (resp.status in (301, 302) and method == "POST"):
                        method = "GET"
                    current = nxt
                    continue
                route.fulfill(response=resp)
                return
            policy.log_block(url, "too many redirects", "too_many_redirects")
            route.abort("failed")
        except Exception as exc:  # network error, closed page: keep the real cause
            code = classify_error(str(exc))
            policy.note_error(url, code)
            log.debug("request %s failed (%s): %s", url, code, exc)
            try:
                route.abort(_ABORT_FOR.get(code, "failed"))
            except Exception:
                pass

    context.route("**/*", handler)
    try:  # Playwright ≥ 1.48. The handler must NOT call Playwright (ws.close() from inside the
        # dispatcher deadlocks the sync API): doing nothing leaves the socket mocked, so it
        # never connects and no byte leaves.
        context.route_web_socket(re.compile(".*"), _mock_web_socket)
    except AttributeError:
        pass


def _mock_web_socket(ws) -> None:
    """Route handler for WebSockets: no connect_to_server() → mocked, nothing leaves."""
    return None


def resolve_start_url(url: str, policy: NetPolicy, timeout: float = 15.0) -> str:
    """Follow the redirect chain of the start URL hop by hop under the policy,
    so that the page is loaded at its final address (relative links stay right)."""
    verdict = policy.check(url)
    if not verdict.ok:
        raise BlockedURL(verdict.reason, policy_code(verdict.code))
    if urlparse(url).scheme not in ("http", "https"):
        return url
    current = url
    with httpx.Client(follow_redirects=False, timeout=timeout,
                      headers={"User-Agent": "Klar./0.1 accessibility pre-check"}) as client:
        for _ in range(MAX_REDIRECTS):
            try:
                with client.stream("GET", current) as r:
                    location = r.headers.get("location")
                    status = r.status_code
            except httpx.HTTPError:
                return current  # let the browser report the network error
            if status in REDIRECT_CODES and location:
                nxt = urljoin(current, location)
                v = policy.check(nxt)
                if not v.ok:
                    raise BlockedURL("redirect: " + v.reason, "blocked_redirect")
                current = nxt
                continue
            return current
    raise BlockedURL("too many redirects", "too_many_redirects")


def load(page, *, url: str | None, html: str | None, opts: CaptureOptions):
    """Navigate (or set_content), wait for network idle (bounded), scroll for lazy images.
    Returns the navigation response (None for raw HTML). Raises ScanError with the cause."""
    from playwright.sync_api import TimeoutError as PwTimeout

    response = None
    if html is not None:
        page.set_content(html, wait_until="load", timeout=opts.timeout_ms)
    else:
        try:
            response = page.goto(url, wait_until="load", timeout=opts.timeout_ms)
        except Exception as exc:
            code = opts.policy.errors.get(url) or classify_error(str(exc))
            first = (str(exc).splitlines() or [""])[0][:200]
            raise ScanError(code, f"{url} could not be loaded ({code}): {first}") from exc
        ctype = (response.headers.get("content-type", "") if response else "").lower()
        if response is not None and ctype and "html" not in ctype and "xml" not in ctype:
            raise ScanError("not_html", f"{url} is not an HTML page ({ctype.split(';')[0]})")
    try:
        page.wait_for_load_state("networkidle", timeout=opts.idle_timeout_ms)
    except PwTimeout:
        log.info("network never went idle; continuing with the loaded page")
    if opts.scroll:
        try:
            page.evaluate(_LAZY_SCROLL_JS)
        except Exception as exc:
            log.info("lazy-load scroll failed: %s", exc)
    page.evaluate(EXTRACT_JS)
    return response


def render(browser: Browser, *, url: str | None = None, html: str | None = None, scan_dir: Path,
           opts: CaptureOptions | None = None) -> CapturedPage:
    if (url is None) == (html is None):
        raise ValueError("give exactly one of url or html")
    opts = opts or CaptureOptions()
    if url is not None:
        url = resolve_start_url(url, opts.policy)
    scan_dir.mkdir(parents=True, exist_ok=True)
    page = browser.new_page(opts)
    try:
        response = load(page, url=url, html=html, opts=opts)
        snap = page.evaluate(js("() => window.__klar.snapshot()"))
    except Exception:
        page.context.close()
        raise
    captured = CapturedPage(
        url=snap["url"], requested_url=url or "about:blank", title=snap["title"] or "",
        lang=snap["lang"], html=snap["html"], text=snap["text"], scan_dir=scan_dir,
        allow_form_submit=opts.allow_form_submit, form_origins=tuple(opts.form_origins), source_html=html,
        live=page, policy=opts.policy,
        http_status=response.status if response is not None else None,
    )
    from klar.capture.probe import probe_forms

    captured._form_probe_fn = lambda p: probe_forms(p, opts)
    try:
        (scan_dir / "page.html").write_text(snap["html"], encoding="utf-8")
    except OSError:
        pass
    return captured


def accessible_names(page) -> dict[int, tuple[str | None, str]]:
    """Chromium's computed role and accessible name for every element in the
    extractor's refs array, via CDP (the same values a screen reader receives)."""
    out: dict[int, tuple[str | None, str]] = {}
    cdp = page.context.new_cdp_session(page)
    try:
        arr = cdp.send("Runtime.evaluate", {"expression": f"window.{KLAR_GLOBAL}.refs", "objectGroup": "klar"})
        oid = arr.get("result", {}).get("objectId")
        if not oid:
            return out
        props = cdp.send("Runtime.getProperties", {"objectId": oid, "ownProperties": True})
        for p in props.get("result", []):
            if not p.get("name", "").isdigit():
                continue
            el_id = p.get("value", {}).get("objectId")
            if not el_id:
                continue
            try:
                ax = cdp.send("Accessibility.getPartialAXTree", {"objectId": el_id, "fetchRelatives": False})
            except Exception:
                continue
            nodes = ax.get("nodes") or []
            if not nodes:
                continue
            node = nodes[0]
            role = (node.get("role") or {}).get("value")
            name = (node.get("name") or {}).get("value") or ""
            out[int(p["name"])] = (role, " ".join(str(name).split()))
        cdp.send("Runtime.releaseObjectGroup", {"objectGroup": "klar"})
    finally:
        try:
            cdp.detach()
        except Exception:
            pass
    return out


def extract(page: CapturedPage) -> dict[str, list[dict]]:
    """Run the standard extraction and attach CDP accessible names."""
    if page.live is None:
        return page.elements
    data = page.live.evaluate(js("() => window.__klar.all()"))
    try:
        names = accessible_names(page.live)
    except Exception as exc:
        log.warning("CDP accessible names unavailable (%s); using the JS fallback", exc)
        names = {}
    for kind in ("links", "images", "fields"):
        for rec in data.get(kind, []):
            role, name = names.get(rec.get("k"), (None, None))
            rec["role_computed"] = role
            rec["name"] = name if name is not None else rec.get("name_js", "")
    page.elements = data
    return data


__all__ = ["Browser", "BlockedURL", "ScanError", "classify_error", "CaptureOptions", "EXTRACT_JS", "KLAR_GLOBAL", "extract", "js", "load",
           "origin_of", "render", "resolve_start_url"]
