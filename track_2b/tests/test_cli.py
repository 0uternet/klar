"""CLI: demo (all pages, in-process and through the API), replay-check gate, scan policy, serve defaults."""

import json
import socket
import threading
import time

import pytest

from klar.cli import build_parser, demo_pages, main

PAGE_OK = '<html lang="de"><body><p><a href="b.html">Steuererklärung online einreichen</a></p></body></html>'
PAGE_ASK = '<html lang="de"><body><p>Den Abfallkalender finden Sie <a href="a.html">hier</a>.</p></body></html>'


@pytest.fixture
def demo_env(tmp_path, monkeypatch):
    demo = tmp_path / "demo-site"
    (demo / "fr").mkdir(parents=True)
    (demo / "index.html").write_text(PAGE_OK, encoding="utf-8")
    (demo / "fr" / "index.html").write_text(PAGE_OK, encoding="utf-8")
    for k in ("LLM_BASE_URL", "LLM_NAME", "LLM_API_KEY", "KLAR_VISION"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("KLAR_REPLAY", "1")
    monkeypatch.setenv("KLAR_DATA_DIR", str(tmp_path / "var"))
    monkeypatch.setenv("KLAR_DEMO_DIR", str(demo))
    monkeypatch.setenv("KLAR_REPLAY_DIR", str(tmp_path / "replay"))
    monkeypatch.setenv("KLAR_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("KLAR_APP_PORT", str(_free_port()))  # no server there unless a test starts one
    return tmp_path


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_demo_pages_lists_every_page_index_first(tmp_path):
    for p in ("b.html", "index.html", "fr/index.html", "fr/a.html"):
        (tmp_path / p).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / p).write_text("<p>x</p>", encoding="utf-8")
    assert demo_pages(tmp_path) == ["index.html", "b.html", "fr/a.html", "fr/index.html"]


def test_serve_defaults_to_localhost():
    assert build_parser().parse_args(["serve"]).host == "127.0.0.1"


@pytest.mark.browser
def test_demo_in_process_then_replay_check(demo_env, chromium, capsys):
    assert main(["demo", "--in-process", "-q", "--criteria", "2.4.4"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("demo: mode=replay") and "pages=2" in out
    summary = json.loads((demo_env / "var" / "reports" / "demo-latest.json").read_text(encoding="utf-8"))
    assert summary["via"] == "in-process" and summary["not_recorded"] == 0 and summary["errors"] == 0
    assert (demo_env / "var" / "reports" / "demo-latest.html").is_file()
    assert main(["replay-check"]) == 0
    assert capsys.readouterr().out.startswith("replay-check (demo-latest.json): OK")


@pytest.mark.browser
def test_replay_check_fails_on_unrecorded_answers(demo_env, chromium, capsys):
    (demo_env / "demo-site" / "fr" / "index.html").write_text(PAGE_ASK, encoding="utf-8")
    assert main(["replay-check", "--rescan", "--criteria", "2.4.4"]) == 1
    line = capsys.readouterr().out.strip().splitlines()[-1]
    assert line.startswith("replay-check (fresh replay, exact keys): FAIL") and "not_recorded=1" in line


@pytest.mark.browser
def test_demo_goes_through_a_running_server(demo_env, chromium, capsys, monkeypatch):
    import uvicorn

    from klar.api.app import create_app
    from klar.config import Settings

    port = _free_port()
    monkeypatch.setenv("KLAR_APP_PORT", str(port))
    server = uvicorn.Server(uvicorn.Config(create_app(Settings.from_env()), host="127.0.0.1", port=port,
                                           log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.1)
    try:
        assert main(["demo", "-q", "--criteria", "2.4.4"]) == 0
        summary = json.loads((demo_env / "var" / "reports" / "demo-latest.json").read_text(encoding="utf-8"))
        assert summary["via"] == "api" and summary["pages"] == 2 and summary["errors"] == 0
        import httpx

        scans = httpx.get(f"http://127.0.0.1:{port}/api/scans").json()
        assert len(scans) == 2 and all(s["url"].startswith(f"http://127.0.0.1:{port}/demo/") for s in scans)
    finally:
        server.should_exit = True
        thread.join(timeout=10)


def test_scan_refuses_blocked_urls_and_never_offers_form_submission(demo_env, capsys):
    assert main(["scan", "http://169.254.169.254/"]) == 2
    assert "not allowed" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        build_parser().parse_args(["scan", "https://www.example.test/", "--allow-form-submit"])


def test_criteria_json(capsys):
    assert main(["criteria", "--json"]) == 0
    items = json.loads(capsys.readouterr().out)
    assert len(items) == 50 and {"criterion", "method", "implemented", "evaluated"} <= set(items[0])
