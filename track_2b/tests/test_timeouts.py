"""KLAR_SCAN_TIMEOUT is a wall-clock limit: a slow-drip server cannot hold a title
fetch, and a slow check cannot hold the worker past the scan deadline."""

from __future__ import annotations

import math
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from klar.capture.page import CapturedPage, _ssl_context
from klar.checks import registry
from klar.checks.base import BaseCheck
from klar.llm import RequestCounter, make_backend
from klar.netpolicy import NetPolicy
from klar.pipeline import ScanJob, new_scan, run_scan

TITLE = "Ferry timetable for the eastern pier"


class _SlowServer:
    """/drip: headers, then one byte every 0.2 s for a minute (never a <title>).
    /stall: headers, then silence. /title-then-drip: a <title> first, then the drip.
    /fast: a normal page."""

    def __init__(self) -> None:
        self.stop = threading.Event()
        self.hits: list[str] = []
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):  # quiet
                pass

            def do_GET(self):  # noqa: N802
                outer.hits.append(self.path)
                route = self.path.split("?")[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                if route == "/fast":
                    body = f"<html><head><title>{TITLE}</title></head><body></body></html>".encode()
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                self.end_headers()
                try:
                    if route == "/title-then-drip":
                        self.wfile.write(f"<html><head><title>{TITLE}</title>".encode())
                        self.wfile.flush()
                    if route == "/stall":
                        outer.stop.wait(60)
                        return
                    for _ in range(300):
                        if outer.stop.wait(0.2):
                            return
                        self.wfile.write(b" ")
                        self.wfile.flush()
                except OSError:  # the client hung up: expected
                    return

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.httpd.daemon_threads = True
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def page(self, **kw) -> CapturedPage:
        page = CapturedPage.from_elements(url=self.base + "/start")
        page.policy = NetPolicy(allowed=((self.base, "/"),))
        for k, v in kw.items():
            setattr(page, k, v)
        return page

    def close(self) -> None:
        self.stop.set()
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def slow_server():
    _ssl_context()  # built once per process, before any fetch's clock starts
    srv = _SlowServer()
    yield srv
    srv.close()


def _fetch_threads() -> list[threading.Thread]:
    return [t for t in threading.enumerate() if t.name == "klar-title-fetch" and t.is_alive()]


def test_slow_drip_cannot_hold_a_title_fetch(slow_server):
    page = slow_server.page(title_fetch_timeout=1.0)
    t0 = time.monotonic()
    assert page.fetch_title(slow_server.base + "/drip") is None
    assert time.monotonic() - t0 < 1.6  # per-read timeouts alone would wait a minute
    assert page.title_fetch_stats["timed_out"] == 1
    # the worker itself stops reading at the same deadline (no thread left dripping)
    end = time.monotonic() + 2.0
    while _fetch_threads() and time.monotonic() < end:
        time.sleep(0.05)
    assert not _fetch_threads()


def test_a_server_that_sends_headers_then_nothing(slow_server):
    page = slow_server.page(title_fetch_timeout=0.8)
    t0 = time.monotonic()
    assert page.fetch_title(slow_server.base + "/stall") is None
    assert time.monotonic() - t0 < 1.4


def test_the_title_is_read_without_waiting_for_the_rest_of_the_body(slow_server):
    page = slow_server.page(title_fetch_timeout=2.0)
    t0 = time.monotonic()
    assert page.fetch_title(slow_server.base + "/title-then-drip") == TITLE
    assert time.monotonic() - t0 < 1.0
    assert page.fetch_title(slow_server.base + "/fast") == TITLE


def test_total_title_time_per_page_is_bounded(slow_server):
    page = slow_server.page(title_fetch_timeout=1.0, title_fetch_seconds=1.5)
    t0 = time.monotonic()
    for i in range(6):
        assert page.fetch_title(f"{slow_server.base}/drip?n={i}") is None
    assert time.monotonic() - t0 < 2.3  # 1.0 + 0.5, then nothing is started
    assert page.title_fetch_stats["skipped"] >= 4
    assert len(slow_server.hits) == 2


def test_title_fetching_is_bounded_by_the_scan_deadline(slow_server):
    page = slow_server.page(title_fetch_timeout=5.0, deadline=time.monotonic() + 0.6)
    t0 = time.monotonic()
    assert page.fetch_title(slow_server.base + "/drip?a") is None
    assert time.monotonic() - t0 < 1.1
    # past the deadline: no request at all, and the miss is not cached
    page.deadline = time.monotonic() - 1
    assert page.remaining() < 0
    assert page.fetch_title(slow_server.base + "/fast") is None
    assert slow_server.hits == ["/drip?a"]
    page.deadline = None
    assert page.remaining() == math.inf
    assert page.fetch_title(slow_server.base + "/fast") == TITLE


# --- the pipeline: KLAR_SCAN_TIMEOUT between checks and between decide() calls ---------------

SCAN_TIMEOUT = 6.0


class _SlowDecide(BaseCheck):
    """Five candidates: the first goes to Apertus, the second's decide() runs past the
    scan deadline (page.remaining()), the last three are never judged."""

    criterion = "1.1.1"
    prompt_version = "1.1.1/timeout-test"
    page: CapturedPage | None = None

    def candidates(self, page):
        _SlowDecide.page = page
        return [self.candidate(page, selector=f"#p{i}", html=f'<p id="p{i}">x</p>', text="x", kind=str(i))
                for i in range(5)]

    def decide(self, c):
        if c.extra["kind"] == "0":
            return None
        if c.extra["kind"] == "1":
            assert _SlowDecide.page is not None and _SlowDecide.page.deadline is not None
            time.sleep(max(0.0, _SlowDecide.page.remaining()) + 0.3)
        return self.finding(c, outcome="passed", source="rule", confidence="high", reason_code="test",
                            explanation="ok", user_impact="none")

    def question(self, c, ui_lang):
        raise AssertionError("never asked: the scan ran out of time first")


class _NeverStarted(BaseCheck):
    criterion = "2.4.4"
    prompt_version = "2.4.4/timeout-test"

    def candidates(self, page):
        raise AssertionError("started after the scan deadline")


@pytest.mark.browser
def test_a_slow_check_cannot_hold_the_worker_past_the_scan_timeout(make_settings, browser, monkeypatch):
    monkeypatch.setattr(registry, "implemented", lambda: {"1.1.1": _SlowDecide, "2.4.4": _NeverStarted})
    settings = make_settings(replay=True, scan_timeout=SCAN_TIMEOUT)
    llm = make_backend(settings, RequestCounter())
    html = '<html lang="en"><head><title>t</title></head><body>' + "".join(
        f'<p id="p{i}">x</p>' for i in range(5)) + "</body></html>"
    job = ScanJob(html=html, criteria=["1.1.1", "2.4.4"])
    t0 = time.monotonic()
    scan = run_scan(new_scan(settings, job, model=llm.model), job, settings=settings, llm=llm, vision=False,
                    counter=RequestCounter(), browser=browser)
    assert time.monotonic() - t0 < SCAN_TIMEOUT + 3
    assert scan.state == "error" and scan.stats["error_code"] == "scan_timeout"
    assert scan.stats["timeout_skipped_checks"] == ["2.4.4"]
    assert scan.stats["check_errors"] == []
    mine = [f for f in scan.findings if f.criterion == "1.1.1" and f.reason_code != "axe"]
    timeouts = [f for f in mine if f.reason_code == "timeout"]
    # #p2–#p4 were never judged, #p0 was waiting for Apertus: all four are cantTell notes
    assert sorted(f.selector for f in timeouts) == ["#p0", "#p2", "#p3", "#p4"]
    assert all(f.outcome == "cantTell" for f in timeouts)
    assert [f.selector for f in mine if f.outcome == "passed"] == ["#p1"]  # decided before the limit hit
    assert scan.stats["timeout_notes"] == 4
    assert scan.stats["asked_apertus"] == 0 and scan.stats["llm_calls"] == 0
    assert scan.stats["criteria_list"] == ["1.1.1"]
    extract = next(s for s in scan.progress if s["step"] == "extract")
    assert extract["state"] == "error"
