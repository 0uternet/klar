"""Why a scan failed (ScanStats.error_code), what the page answered (http_status,
final_url, page_title), whether the model is reachable (Health), and no no-op fixes."""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from fake_llm import FakeLLM
from klar.api.app import health_of
from klar.api.manager import Services
from klar.capture.browser import classify_error
from klar.capture.page import CapturedPage
from klar.checks.c_1_1_1 import NonTextContent
from klar.config import Settings
from klar.llm import RequestCounter, make_backend
from klar.netpolicy import NetPolicy
from klar.pipeline import ScanJob, new_scan, run_scan


@pytest.mark.parametrize("message, code", [
    ("net::ERR_NAME_NOT_RESOLVED at https://x.invalid/", "dns"),
    ("net::ERR_CONNECTION_REFUSED at http://127.0.0.1:9/", "unreachable"),
    ("net::ERR_CERT_AUTHORITY_INVALID", "tls"),
    ("Timeout 30000ms exceeded.", "timeout_page"),
    ("Download is starting", "not_html"),
    ("something else", "internal"),
])
def test_classify_error(message, code):
    assert classify_error(message) == code


def test_policy_says_which_rule_fired():
    p = NetPolicy()
    assert p.check("http://169.254.169.254/").code == "blocked_metadata"
    assert p.check("http://127.0.0.1/").code == "blocked_localhost"
    assert p.check("http://10.0.0.1/").code == "blocked_private"
    assert p.check("ftp://example.test/").code == "blocked_scheme"


class _Site:
    def __init__(self):
        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                if self.path == "/ok":
                    body, ctype = b"<html><head><title>Startseite</title></head><body><p>Hallo</p></body></html>", "text/html"
                elif self.path == "/pdf":
                    body, ctype = b"%PDF-1.4", "application/pdf"
                elif self.path == "/meta":
                    self.send_response(302)
                    self.send_header("Location", "http://169.254.169.254/")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                    return
                else:
                    body, ctype = b"missing", "text/html"
                    self.send_response(404)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def _scan(settings, url, policy):
    counter = RequestCounter()
    llm = make_backend(settings, counter)
    job = ScanJob(url=url, criteria=["2.4.4"], policy=policy)
    return run_scan(new_scan(settings, job, model=llm.model), job, settings=settings, llm=llm, vision=False,
                    counter=counter)


@pytest.mark.browser
def test_scan_error_codes_and_page_facts(make_settings, chromium):
    site = _Site()
    settings = make_settings(replay=True)
    try:
        policy = lambda: NetPolicy(allowed=((site.base, "/"),))  # noqa: E731
        ok = _scan(settings, site.base + "/ok", policy())
        assert ok.state == "done" and ok.stats["http_status"] == 200 and ok.stats["page_title"] == "Startseite"
        assert ok.stats["final_url"] == site.base + "/ok" and ok.stats["error_code"] is None
        missing = _scan(settings, site.base + "/nope", policy())
        assert missing.state == "done" and missing.stats["http_status"] == 404
        assert _scan(settings, site.base + "/pdf", policy()).stats["error_code"] == "not_html"
        assert _scan(settings, site.base + "/meta", policy()).stats["error_code"] == "blocked_redirect"
        assert _scan(settings, "http://169.254.169.254/", NetPolicy()).stats["error_code"] == "blocked_metadata"
    finally:
        site.close()
    closed = f"{site.base}/ok"  # the server is gone: connection refused
    dead = _scan(settings, closed, NetPolicy(allowed=((site.base, "/"),)))
    assert dead.state == "error" and dead.stats["error_code"] == "unreachable"


def test_health_reports_an_unreachable_model(make_settings):
    fake = FakeLLM()
    url = fake.base_url
    fake.server.server_close()
    settings = make_settings(llm_base_url=url, llm_timeout=2, vision_override=None)
    svc = Services(settings)
    try:
        svc.caps.get()
        h = health_of(svc)
        assert h.llm_reachable is False and h.llm_error  # refused or timed out, depending on the platform
        assert h.vision is False and h.vision_source == "error"
    finally:
        svc.close()
    with FakeLLM() as ok:
        svc = Services(make_settings(llm_base_url=ok.base_url))
        try:
            svc.caps.get()
            assert health_of(svc).llm_reachable is True and health_of(svc).llm_error is None
        finally:
            svc.close()
    replay = Services(make_settings(replay=True))
    try:
        assert health_of(replay).llm_reachable is None
    finally:
        replay.close()


@pytest.mark.parametrize("fix", ["No change needed.", "Keine Änderung nötig", "", "Rathaus"])
def test_failed_findings_never_carry_a_no_op_fix(fix):
    page = CapturedPage.from_elements(images=[{
        "selector": "img.a", "tag": "img", "html": '<img src="r.jpg" alt="Rathaus">', "alt": "Rathaus", "role": None,
        "aria_hidden": False, "decorative_markup": False, "name": "Rathaus", "src": "r.jpg",
        "natural": {"w": 200, "h": 100}, "rect": {"x": 0, "y": 0, "w": 200, "h": 100}, "lang": "de",
        "in_link": False, "context": {}}])
    check = NonTextContent("en", Settings(), vision=False)
    c = check.candidates(page)[0]
    f = check.interpret(c, {"image_type": "informative", "outcome": "failed", "confidence": "high",
                            "quote": "Rathaus", "reason": "Too short.", "fix": fix})
    assert f.outcome == "failed" and f.fix_diff is None
    assert "No change" not in (f.fix_hint or "") and "Keine" not in (f.fix_hint or "")
