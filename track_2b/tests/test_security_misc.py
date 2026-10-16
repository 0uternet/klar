"""Output encoding, budget fairness, form-probe method policy, leakage gate."""

import subprocess
import sys
from pathlib import Path

import pytest

from klar.checks.c_2_4_4 import LinkPurpose
from klar.config import Settings
from klar.models import Candidate
from klar.pipeline import round_robin
from klar.report.csv import safe_cell

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("value, expected", [("=1+1", "'=1+1"), ("+41 58 000", "'+41 58 000"), ("-x", "'-x"),
                                             ("@SUM(A1)", "'@SUM(A1)"), ("\tx", "'\tx"), ("normal", "normal"),
                                             (None, "")])
def test_csv_formula_guard(value, expected):
    assert safe_cell(value) == expected


def test_budget_is_shared_round_robin_across_criteria():
    class FakeCheck:
        def __init__(self, crit):
            self.criterion = crit

    checks = [FakeCheck(c) for c in ("1.1.1", "2.4.4", "3.1.2")]
    pending = [(ch, Candidate(id=f"{ch.criterion}-{i}", criterion=ch.criterion, page_url="u", selector="s", html=""))
               for ch in checks for i in range(100)]
    asked, skipped = round_robin(pending, 30)
    per = {c: sum(1 for ch, _ in asked if ch.criterion == c) for c in ("1.1.1", "2.4.4", "3.1.2")}
    assert per == {"1.1.1": 10, "2.4.4": 10, "3.1.2": 10} and len(skipped) == 270


@pytest.mark.browser
def test_form_probe_submits_nothing_to_other_origins(render_html):
    page = render_html("""<html lang="de"><body>
        <form method="post" action="https://other.example/collect">
        <label>E-Mail <input type="email" name="e" required></label><button>Senden</button></form>
        <form method="get" action="https://other.example/search" novalidate>
        <label>Suche <input name="q"></label><button>Suchen</button></form></body></html>""", allow_form_submit=True)
    seen: list[str] = []
    page.live.context.on("request", lambda r: seen.append(r.url))
    probe = page.form_probe()
    assert len(probe) == 2 and all("skipped" in rec for rec in probe)  # neither POST nor GET is submitted
    assert not [u for u in seen if "other.example" in u]


def test_prompts_contain_no_test_set_strings():
    """The data owner's leakage check (prompts/lexicons/demo vs the test split)."""
    script = ROOT / "scripts" / "check_leakage.py"
    if not script.is_file() or not (ROOT / "data" / "testset" / "manifest.jsonl").is_file():
        pytest.skip("leakage script or test set not present")
    out = subprocess.run([sys.executable, "-I", str(script)], cwd=ROOT, capture_output=True, text=True, timeout=300,
                         encoding="utf-8", errors="replace")
    assert out.returncode == 0 and "0 overlaps" in out.stdout, out.stdout[-2000:] + out.stderr[-2000:]


def test_prompts_have_no_concrete_examples_from_the_demo_site():
    demo = (ROOT / "data" / "demo-site")
    if not demo.is_dir():
        pytest.skip("no demo site")
    text = " ".join(p.read_text(encoding="utf-8", errors="replace") for p in demo.rglob("*.html")).lower()
    from klar.checks import c_1_1_1, c_3_1_2

    for system in (LinkPurpose.SYSTEM, c_3_1_2.LanguageOfParts.SYSTEM, c_1_1_1.NonTextContent.SYSTEM):
        for quoted in __import__("re").findall(r'"([^"]{4,})"', system):
            assert quoted.lower() not in text, quoted
    assert Settings().replay_models == ("swiss-ai/Apertus-v1.5-*",)


@pytest.mark.browser
def test_scan_timeout_cancels_and_reports(make_settings, chromium):
    import time as _time

    from fake_llm import FakeLLM, is_probe
    from klar.llm import RequestCounter, make_backend
    from klar.pipeline import ScanJob, new_scan, run_scan

    def slow(req):
        if not is_probe(req):
            _time.sleep(3)
        return {"category": "nowhere", "confidence": "low", "quote": "hier", "reason": "slow"}

    html = "".join(f'<p>Thema {i}: <a href="/{i}">hier</a>.</p>' for i in range(6))
    with FakeLLM(slow) as fake:
        settings = make_settings(llm_base_url=fake.base_url, scan_timeout=6, llm_concurrency=1)
        counter = RequestCounter()
        llm = make_backend(settings, counter)
        job = ScanJob(html=f'<html lang="de"><body>{html}</body></html>', criteria=["2.4.4"])
        t0 = _time.monotonic()
        scan = run_scan(new_scan(settings, job, model=llm.model), job, settings=settings, llm=llm, vision=False,
                        counter=counter)
    assert _time.monotonic() - t0 < 15
    assert scan.state == "error" and "KLAR_SCAN_TIMEOUT" in scan.stats["error"]
    assert any(f.reason_code == "timeout" for f in scan.findings)
