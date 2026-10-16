"""Pause, resume and stop of a running scan (ScanControl, POST /api/scans/{id}/pause|resume|stop)."""

from __future__ import annotations

import threading
import time

import pytest

from fake_llm import FakeLLM, is_probe
from klar.llm import RequestCounter, make_backend
from klar.pipeline import ScanControl, ScanJob, new_scan, run_scan

LINKS = "".join(f'<p>Thema {i}: <a href="/{i}">hier</a>.</p>' for i in range(6))
PAGE = f'<html lang="de"><head><title>t</title></head><body>{LINKS}</body></html>'


def slow_answer(delay: float):
    def respond(req):
        if is_probe(req):
            return '{"ok": true}' if "response_format" in req else "red"
        time.sleep(delay)
        return {"category": "nowhere", "confidence": "low", "quote": "hier", "reason": "no context"}
    return respond


def questions(fake: FakeLLM) -> int:
    return sum(1 for r in fake.requests if not is_probe(r))


def test_control_states():
    ctl = ScanControl()
    assert ctl.state() == {"paused": False, "stopping": False}
    ctl.pause()
    assert ctl.paused
    ctl.resume()
    assert not ctl.paused
    ctl.pause()
    ctl.stop()  # stopping wakes a paused scan, and a stopped scan cannot be paused again
    assert ctl.state() == {"paused": False, "stopping": True}
    ctl.pause()
    assert not ctl.paused


def test_a_scan_stopped_while_queued_never_opens_the_page(make_settings):
    settings = make_settings(replay=True)
    llm = make_backend(settings, RequestCounter())
    job = ScanJob(html=PAGE, criteria=["2.4.4"], control=ScanControl())
    job.control.stop()
    scan = run_scan(new_scan(settings, job, model=llm.model), job, settings=settings, llm=llm, vision=False,
                    counter=RequestCounter())
    assert scan.state == "done" and scan.stats["stopped"] is True
    assert scan.findings == []
    assert all(s["state"] == "skipped" for s in scan.progress if s["step"] != "done")


@pytest.mark.browser
def test_pause_holds_the_questions_and_stop_keeps_the_answers_so_far(make_settings, chromium):
    with FakeLLM(slow_answer(0.3)) as fake:
        settings = make_settings(llm_base_url=fake.base_url, llm_concurrency=1, scan_timeout=120)
        counter = RequestCounter()
        llm = make_backend(settings, counter)
        ctl = ScanControl()
        job = ScanJob(html=PAGE, criteria=["2.4.4"], control=ctl)
        events: list[tuple[str, dict]] = []

        def emit(event, data):
            events.append((event, data))
            if event == "progress" and data["step"] == "apertus" and data.get("current") == 1 and not ctl.paused:
                ctl.pause()

        scan = new_scan(settings, job, model=llm.model)
        worker = threading.Thread(target=run_scan, args=(scan, job),
                                  kwargs=dict(settings=settings, llm=llm, vision=False, counter=counter, emit=emit))
        worker.start()
        deadline = time.monotonic() + 60
        while not any(e == "control" and d["paused"] for e, d in events):
            assert time.monotonic() < deadline, "the scan never paused"
            time.sleep(0.05)
        asked = questions(fake)
        time.sleep(1.2)
        assert questions(fake) == asked  # nothing is asked while paused
        ctl.stop()
        worker.join(30)
    assert not worker.is_alive()
    assert scan.state == "done" and scan.stats["stopped"] is True
    assert scan.stats["paused_seconds"] >= 1.0
    stopped = [f for f in scan.findings if f.reason_code == "stopped"]
    answered = [f for f in scan.findings if f.source == "apertus" and f.reason_code != "stopped"]
    assert stopped and all(f.outcome == "cantTell" for f in stopped)
    assert len(answered) >= 1 and scan.stats["stopped_notes"] == len(stopped)
    apertus = next(s for s in scan.progress if s["step"] == "apertus")
    assert apertus["state"] == "done" and apertus["detail"] == "stopped"
    assert apertus["current"] == len(answered) < apertus["total"]  # the count shows what was asked
    assert next(s for s in scan.progress if s["step"] == "verify")["state"] == "skipped"


@pytest.mark.browser
def test_paused_time_does_not_count_against_the_scan_timeout(make_settings, chromium):
    with FakeLLM(slow_answer(0.05)) as fake:
        settings = make_settings(llm_base_url=fake.base_url, llm_concurrency=1, scan_timeout=8)
        counter = RequestCounter()
        llm = make_backend(settings, counter)
        ctl = ScanControl()
        job = ScanJob(html=PAGE, criteria=["2.4.4"], control=ctl)

        def emit(event, data):
            if event == "progress" and data["step"] == "apertus" and data.get("current") == 1 and not ctl.paused:
                ctl.pause()
                threading.Timer(9.0, ctl.resume).start()  # longer than the whole scan budget

        scan = run_scan(new_scan(settings, job, model=llm.model), job, settings=settings, llm=llm, vision=False,
                        counter=counter, emit=emit)
    assert scan.state == "done", scan.stats.get("error")
    assert scan.stats["stopped"] is False and scan.stats["paused_seconds"] >= 8.5
    assert not any(f.reason_code == "timeout" for f in scan.findings)


def test_control_routes_answer_404_for_an_unknown_scan(make_settings):
    from fastapi.testclient import TestClient

    from klar.api.app import create_app

    with TestClient(create_app(make_settings(replay=True), probe=False)) as client:
        for action in ("pause", "resume", "stop"):
            assert client.post(f"/api/scans/abcdef0123/{action}").status_code == 404
