"""API + pipeline smoke test: scan inline HTML end to end with the fake LLM."""

import time

import pytest
from fastapi.testclient import TestClient

from fake_llm import user_text
from klar.api.app import create_app, host_name
from klar.api.manager import Services
from klar.models import CriterionInfo, Health, ProgressStep, ScanStats

pytestmark = pytest.mark.browser

HTML = """<!doctype html><html lang="de"><head><title>Gemeinde Musterwil</title></head><body><main>
<h1>Willkommen</h1>
<p>Bienvenue sur le site de la commune de Musterwil. Pour plus d'informations, veuillez contacter l'administration.</p>
<p>Weitere Informationen erhalten Sie beim Office fédéral de la statistique in Neuchâtel.</p>
<p>Die Abteilung Soziales berät Sie gerne. Benvenuti a Musterwil!</p>
<p>Den Abfallkalender 2026 finden Sie <a href="/abfall">hier</a>.</p>
<section><h2>Abfall</h2><p><a href="/abfall">Mehr</a></p></section>
<p>Unser Jahresbericht ist online. <a href="/bericht">Weiterlesen</a></p>
<img src="data:image/gif;base64,R0lGODlhAQABAAAAACw=" alt="Rathaus Musterwil" width="200" height="120">
</main></body></html>"""


@pytest.fixture
def api(make_settings, fake_llm, chromium):
    settings = make_settings(llm_base_url=fake_llm.base_url)
    services = Services(settings)
    with TestClient(create_app(settings, services=services)) as client:
        yield client, fake_llm, settings


def wait_done(client, scan_id, timeout=90):
    end = time.time() + timeout
    while time.time() < end:
        scan = client.get(f"/api/scans/{scan_id}").json()
        if scan["state"] in ("done", "error"):
            return scan
        time.sleep(0.3)
    raise AssertionError("scan did not finish")


def by(scan, criterion, text):
    return [f for f in scan["findings"] if f["criterion"] == criterion and text in f["excerpt"]]


def test_health_criteria_headers_and_static(api):
    client, _, _ = api
    client.app.state.services.caps.get()  # wait for the start-up probe
    r = client.get("/api/health")
    h = Health.model_validate(r.json())
    assert h.mode == "local" and h.vision is False and h.vision_source == "override"
    assert h.ai_requests["external"] == 0 and h.base_url_host == "127.0.0.1" and h.config_error is None
    assert "default-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["referrer-policy"] == "no-referrer"
    crit = [CriterionInfo.model_validate(c) for c in client.get("/api/criteria").json()]
    assert len(crit) == 50 and {c.method for c in crit} >= {"apertus_text", "apertus_vision", "planned"}
    assert next(c for c in crit if c.criterion == "2.4.4").implemented
    assert client.get("/").status_code == 200 and "Klar" in client.get("/").text
    assert client.get("/demo/").status_code == 404
    assert client.get("/api/nope").status_code == 404
    assert client.get("/docs").status_code in (404, 200) and "swagger" not in client.get("/docs").text.lower()


def test_host_header_allow_list(api):
    client, _, _ = api
    assert client.get("/api/health", headers={"host": "evil.test"}).status_code == 400
    for host in ("localhost", "localhost:8080", "127.0.0.1:8080", "[::1]:8080", "[::1]"):
        assert client.get("/api/health", headers={"host": host}).status_code == 200, host
    assert host_name("[::1]:8080") == "::1" and host_name("LOCALHOST:80") == "localhost"


def test_scan_end_to_end(api):
    client, fake, settings = api
    r = client.post("/api/scans", json={"html": HTML, "ui_lang": "en", "criteria": ["2.4.4", "3.1.2", "1.1.1"]})
    assert r.status_code == 201
    scan_id = r.json()["id"]
    scan = wait_done(client, scan_id)
    assert scan["state"] == "done", scan["stats"]
    stats = ScanStats.model_validate(scan["stats"])
    steps = [ProgressStep.model_validate(p) for p in scan["progress"]]
    assert [p.step for p in steps] == ["render", "axe", "extract", "apertus", "verify", "done"]
    assert all(p.state == "done" for p in steps)
    apertus = next(p for p in steps if p.step == "apertus")
    assert apertus.total == apertus.current and apertus.total >= 3
    assert stats.ai_requests == {"local": stats.llm_calls, "swiss_cloud": 0, "external": 0}
    assert stats.criteria_checked == 3 and stats.criteria_apertus == 3
    assert stats.failed + stats.cantTell + stats.passed + stats.inapplicable == len(scan["findings"])
    assert stats.to_review == len(scan["findings"])
    assert scan["coverage"]["2.4.4"] == "apertus_text" and scan["coverage"]["1.4.10"] == "planned"

    # 3.1.2 — deterministic full French sentence, Apertus institution exception, Apertus foreign phrase
    fr = by(scan, "3.1.2", "Bienvenue")[0]
    assert fr["outcome"] == "failed" and fr["source"] == "heuristic" and fr["reason_code"] == "untagged_sentence"
    assert fr["content_lang"] == "de"
    inst = by(scan, "3.1.2", "Office fédéral de la statistique")[0]
    assert inst["outcome"] == "passed" and inst["source"] == "apertus" and inst["model"] == settings.llm_name
    assert inst["context_shown"]["declared_language"] == 'lang="de"' and inst["reason"]
    it = by(scan, "3.1.2", "Benvenuti")[0]
    assert it["outcome"] == "failed" and '<span lang="it">' in it["fix_diff"] and it["content_lang"] == "it"

    # 2.4.4 — context passes, heading-only is human review, hallucinated quote is rejected by the guard
    hier = by(scan, "2.4.4", "hier")[0]
    assert hier["outcome"] == "passed" and hier["source"] == "apertus"
    mehr = by(scan, "2.4.4", "Mehr")[0]
    assert mehr["outcome"] == "cantTell" and mehr["reason_code"] == "generic_heading_only"
    weiter = by(scan, "2.4.4", "Weiterlesen")[0]
    assert weiter["outcome"] == "cantTell" and weiter["reason_code"] == "not_grounded"
    assert stats.guard_rejected >= 1
    asked = [user_text(r) for r in fake.requests if "2.4.4" in (r["messages"][0].get("content") or "")]
    assert asked and all("<page_data>" in u and "Abfall\\n" not in u and "/bericht" not in u.split('"html"')[0]
                         for u in asked)

    # 1.1.1 — no vision backend: needs review with the note
    img = [f for f in scan["findings"] if f["criterion"] == "1.1.1" and f["reason_code"] == "vision_required"]
    assert len(img) == 1 and img[0]["outcome"] == "cantTell" and img[0]["excerpt"] == "Rathaus Musterwil"

    # finding ids are unique and prefixed with the scan id
    ids = [f["id"] for f in scan["findings"]]
    assert len(ids) == len(set(ids)) and all(i.startswith(scan_id + "-") for i in ids)

    # ---- SSE: ids, done payload, Last-Event-ID resume --------------------------------------
    with client.stream("GET", f"/api/scans/{scan_id}/events") as resp:
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = "".join(resp.iter_text())
    blocks = [b for b in body.strip().split("\n\n") if b.strip()]
    assert all(b.startswith("id: ") for b in blocks)
    assert blocks[-1].split("\n")[1] == "event: done" and f'"scan_id": "{scan_id}"' in blocks[-1]
    n_findings = body.count("event: finding")
    assert n_findings == len(scan["findings"])
    last_id = int(blocks[-3].split("\n")[0][4:])
    with client.stream("GET", f"/api/scans/{scan_id}/events", headers={"Last-Event-ID": str(last_id)}) as resp:
        rest = "".join(resp.iter_text())
    assert rest.count("id: ") == 2  # resumes after last_id: no duplicates

    # ---- review --------------------------------------------------------------------------
    fid = fr["id"]
    r = client.patch(f"/api/findings/{fid}", json={"status": "accepted"})
    assert r.status_code == 200 and r.json()["status"] == "accepted"
    again = client.get(f"/api/scans/{scan_id}").json()
    assert next(f for f in again["findings"] if f["id"] == fid)["status"] == "accepted"
    assert again["stats"]["accepted"] == 1 and again["stats"]["to_review"] == len(ids) - 1
    assert client.patch("/api/findings/nope-123", json={"status": "accepted"}).status_code == 404
    assert client.patch(f"/api/findings/{fid}", json={"status": "maybe"}).status_code == 422

    # ---- exports -------------------------------------------------------------------------
    j = client.get(f"/api/scans/{scan_id}/export?format=json")
    assert j.headers["content-disposition"].endswith('.json"')
    assert j.json()["disclaimer"].startswith("Klar. pre-checks 3 of 50")
    earl = client.get(f"/api/scans/{scan_id}/export?format=earl").json()
    modes = {a["earl:mode"]["@id"] for a in earl["@graph"] if a.get("@type") == "earl:Assertion"}
    assert modes == {"earl:semiAuto", "earl:automatic"}
    csv_text = client.get(f"/api/scans/{scan_id}/export?format=csv").content.decode("utf-8-sig")
    assert csv_text.startswith("# Klar. pre-checks") and "criterion_name" in csv_text.splitlines()[1]
    html = client.get(f"/api/scans/{scan_id}/export?format=html").text
    assert "This report does not certify conformance." in html and '<html lang="en">' in html
    assert "Content-Security-Policy" in html and "Apache-2.0" in html  # Apertus model → licence line
    assert client.get(f"/api/scans/{scan_id}/export?format=pdf").status_code == 422

    # ---- replay: the same scan without the model gives the same Apertus verdicts ------------
    replay_settings = settings.with_(replay=True, llm_base_url=None)
    with TestClient(create_app(replay_settings, services=Services(replay_settings))) as rc:
        h = rc.get("/api/health").json()
        assert h["mode"] == "replay" and h["replay_models"] == [settings.llm_name]
        assert h["replay_recorded"]["hosts"] == ["127.0.0.1"]
        rid = rc.post("/api/scans", json={"html": HTML, "ui_lang": "de", "criteria": ["2.4.4", "3.1.2"]}).json()["id"]
        rscan = wait_done(rc, rid)
    # UI language changed (en → de): prompts are language-neutral, so every answer is still recorded
    assert rscan["stats"]["llm_calls"] == 0 and rscan["stats"]["not_recorded"] == 0
    assert by(rscan, "3.1.2", "Office fédéral de la statistique")[0]["outcome"] == "passed"
    assert by(rscan, "2.4.4", "hier")[0]["outcome"] == "passed"


def test_screenshot_file_endpoint_is_traversal_safe(api):
    client, _, settings = api
    crops = settings.scans_path / "0123456789" / "crops"
    crops.mkdir(parents=True)
    (crops / "abc123def456.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    assert client.get("/api/scans/0123456789/files/abc123def456.png").status_code == 200
    for bad in ("../klar.db", "..%2Fklar.db", "abc.PNG", "x.html"):
        assert client.get(f"/api/scans/0123456789/files/{bad}").status_code == 404, bad
    assert client.get("/api/scans/..%2F..%2Fvar/files/abc123def456.png").status_code == 404


@pytest.mark.parametrize("url", ["http://169.254.169.254/latest/meta-data/", "http://127.0.0.1:9/",
                                 "http://10.0.0.1/", "file:///etc/passwd", "ftp://example.test/",
                                 "http://[::ffff:169.254.169.254]/"])
def test_ssrf_targets_are_refused(api, url):
    client, _, _ = api
    r = client.post("/api/scans", json={"url": url, "ui_lang": "en"})
    assert r.status_code == 422, (url, r.text)


def test_queue_cap_gives_429(make_settings, fake_llm, chromium):
    settings = make_settings(llm_base_url=fake_llm.base_url, max_queue=1)
    with TestClient(create_app(settings, services=Services(settings))) as client:
        first = client.post("/api/scans", json={"html": HTML, "ui_lang": "en", "criteria": ["2.4.4"]})
        assert first.status_code == 201
        assert client.post("/api/scans", json={"html": "<p>x</p>", "ui_lang": "en"}).status_code == 429
        wait_done(client, first.json()["id"])


def test_bad_requests(api):
    client, _, settings = api
    assert client.post("/api/scans", json={"ui_lang": "en"}).status_code == 422
    assert client.post("/api/scans", json={"html": "<p>x</p>", "criteria": ["9.9.9"]}).status_code == 422
    big = "<p>" + "x" * (settings.max_html_bytes + 10) + "</p>"
    assert client.post("/api/scans", json={"html": big, "ui_lang": "en"}).status_code == 413
    assert client.get("/api/scans/doesnotexist").status_code == 404
    assert client.get("/api/scans/doesnotexist/events").status_code == 404
