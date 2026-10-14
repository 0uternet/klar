"""SSRF protection: one URL policy for scan targets, browser requests, redirects
and the destination-title fetch. The LLM endpoint has its own, wider rule."""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from klar.capture.browser import BlockedURL, CaptureOptions, render, resolve_start_url
from klar.capture.page import CapturedPage
from klar.config import Settings
from klar.netpolicy import NetPolicy, origin_of


@pytest.mark.parametrize("url, ok", [
    ("https://www.example.ch/", True),
    ("http://93.184.216.34/", True),
    ("http://169.254.169.254/latest/meta-data/", False),  # cloud metadata, always
    ("http://[fe80::1]/", False),
    ("http://0.0.0.0/", False),
    ("http://224.0.0.1/", False),
    ("http://127.0.0.1:9/", False),  # loopback
    ("http://localhost:8080/admin", False),
    ("http://[::1]/", False),
    ("http://[::ffff:127.0.0.1]/", False),
    ("http://10.0.0.1/", False),  # private: only with the flag
    ("http://192.168.1.10/", False),
    ("http://100.64.0.1/", False),
    ("file:///etc/passwd", False),
    ("ftp://example.test/", False),
    ("javascript:alert(1)", False),
    ("data:image/png;base64,AAAA", True),  # never reaches the network
    ("about:blank", True),
])
def test_default_policy(url, ok):
    assert NetPolicy().check(url).ok is ok, url


def test_private_networks_need_the_flag_and_metadata_never_passes():
    p = NetPolicy(allow_private=True)
    assert p.check("http://10.0.0.1/").ok and p.check("http://192.168.1.10/").ok
    assert not p.check("http://169.254.169.254/").ok and not p.check("http://127.0.0.1/").ok
    assert Settings(allow_private_networks=True).net_policy().check("http://10.1.2.3/").ok


def test_own_demo_is_the_only_loopback_exception():
    p = Settings(app_port=8080).net_policy()
    assert p.check("http://127.0.0.1:8080/demo/index.html").ok
    assert p.check("http://localhost:8080/demo/fr/index.html").ok
    assert not p.check("http://127.0.0.1:8080/api/scans").ok  # same port, not the demo
    assert not p.check("http://127.0.0.1:8081/demo/").ok  # other port
    assert origin_of("http://LOCALHOST:8080/x") == "http://localhost:8080"


def test_llm_endpoint_host_is_exempt_but_metadata_is_not():
    for url in ("http://llm-gpu:8000/v1", "http://llm-cpu:8080/v1", "http://host.docker.internal:8000/v1",
                "http://10.0.0.5:8000/v1", "http://127.0.0.1:8081/v1"):
        assert NetPolicy.check_endpoint(url).ok, url
        assert Settings(llm_base_url=url).config_error is None
    assert not NetPolicy.check_endpoint("http://169.254.169.254/v1").ok
    assert Settings(llm_base_url="http://169.254.169.254/v1").config_error
    assert Settings(llm_base_url="llm:8000/v1").config_error  # no scheme: never a silent replay
    assert Settings(llm_base_url="ftp://llm/v1").config_error
    # the endpoint exemption never leaks into the scan policy
    assert not Settings(llm_base_url="http://10.0.0.5:8000/v1").net_policy().check("http://10.0.0.5:8000/").ok


class _Redirector:
    """Local server: /start → 302 to a blocked address; /page links an image that redirects there."""

    def __init__(self):
        outer = self
        self.hits: list[str] = []

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                outer.hits.append(self.path)
                if self.path in ("/start", "/img.png", "/title"):
                    self.send_response(302)
                    self.send_header("Location", "http://169.254.169.254/latest/meta-data/")
                    self.send_header("Content-Length", "0")
                    self.end_headers()
                elif self.path == "/page":
                    body = b'<html><body><p>x</p><img src="/img.png" alt="x"></body></html>'
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_response(404)
                    self.send_header("Content-Length", "0")
                    self.end_headers()

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def test_redirects_to_blocked_addresses_are_refused():
    srv = _Redirector()
    try:
        policy = NetPolicy(allowed=((srv.base, "/"),))
        with pytest.raises(BlockedURL):
            resolve_start_url(srv.base + "/start", policy)
        page = CapturedPage.from_elements(url=srv.base + "/page")
        page.policy = policy
        assert page.fetch_title(srv.base + "/title") is None  # same-origin redirect to metadata → refused
        assert any("169.254.169.254" in b for b in policy.blocked_log)
    finally:
        srv.close()


@pytest.mark.browser
def test_browser_requests_go_through_the_policy(browser, tmp_path):
    srv = _Redirector()
    try:
        policy = NetPolicy(allowed=((srv.base, "/"),))
        page = render(browser, url=srv.base + "/page", scan_dir=tmp_path / "a", opts=CaptureOptions(policy=policy))
        page.close()
        assert "/img.png" in srv.hits
        assert any("redirect" in b and "169.254.169.254" in b for b in policy.blocked_log)  # hop refused
        html_policy = NetPolicy()
        page = render(browser, html='<img src="http://169.254.169.254/x.png"><img src="http://10.0.0.1/y.png">',
                      scan_dir=tmp_path / "b", opts=CaptureOptions(policy=html_policy))
        page.close()
        assert len([b for b in html_policy.blocked_log if "169.254" in b or "10.0.0.1" in b]) == 2
    finally:
        srv.close()
