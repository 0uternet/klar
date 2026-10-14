"""Evaluation: metric definitions on toy tables and a tiny end-to-end run."""

import json
import math

import pytest

from klar.eval.metrics import aggregate, compare, decision, mcnemar_exact, summarize, wilson
from klar.eval.runner import RESPONSE_FIELDS, EvalRefused, run_eval


def test_wilson_interval_known_values():
    assert wilson(0, 0) == (0.0, 0.0)
    assert wilson(8, 10) == (0.4902, 0.9433)  # reference: Wilson 95 % for 8/10
    assert wilson(10, 10)[1] == 1.0


def test_mcnemar_exact_known_values():
    assert mcnemar_exact(0, 0) == 1.0
    # b=10, c=2: 2 * P(X <= 2 | n=12, p=.5) = 2 * (1 + 12 + 66) / 4096
    assert math.isclose(mcnemar_exact(10, 2), round(2 * 79 / 4096, 6))
    assert mcnemar_exact(5, 5) == 1.0


def test_aggregate_and_decision():
    assert aggregate([]) == "inapplicable"
    assert aggregate(["passed", "cantTell"]) == "cantTell"
    assert aggregate(["passed", "failed", "cantTell"]) == "failed"
    assert decision("inapplicable") == decision("passed") == "ok"


def test_summarize_follows_the_metric_spec():
    pairs = [("failed", "failed"), ("failed", "passed"), ("failed", "inapplicable"), ("failed", "cantTell"),
             ("passed", "failed"), ("passed", "inapplicable"), ("cantTell", "cantTell"), ("cantTell", "passed")]
    m = summarize(pairs)
    assert m["confusion"] == {"TP": 1, "FP": 1, "FN": 3, "TN": 1}  # gold cantTell excluded
    assert m["precision"]["value"] == 0.5 and m["recall"]["value"] == 0.25
    assert m["explicit_false_pass"]["k"] == 1 and m["silent_miss"]["k"] == 1 and m["false_pass"]["k"] == 2
    assert m["flagged_recall"]["value"] == 0.5  # failed or cantTell on gold failed
    assert m["deferral_rate"]["k"] == 2
    assert m["gold_cantTell_flag_rate"]["value"] == 0.5
    assert m["gold"] == {"failed": 4, "cantTell": 2, "passed": 2, "inapplicable": 0}


def test_compare_counts_discordant_pairs():
    gold = ["failed", "passed", "failed"]
    a = list(zip(gold, ["failed", "passed", "failed"]))
    b = list(zip(gold, ["passed", "passed", "cantTell"]))
    r = compare(a, b)
    assert (r["a_only_correct"], r["b_only_correct"]) == (2, 0) and r["significant"] is False


def _testset(root, rows_html):
    (root / "data" / "testset" / "generated").mkdir(parents=True)
    (root / "data" / "testset" / "act").mkdir()
    rows = []
    for i, (name, html, expected) in enumerate(rows_html):
        (root / "data" / "testset" / "generated" / name).write_text(html, encoding="utf-8")
        rows.append({"case_id": f"c{i}", "criterion": "2.4.4", "source": "generated", "split": "dev",
                     "page_lang": "de", "expected": expected, "path": f"generated/{name}", "target_selector": "#t"})
    (root / "data" / "testset" / "manifest.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


def test_test_split_is_refused_without_the_labels_tag(make_settings, tmp_path):
    root = tmp_path / "proj"
    _testset(root, [("a.html", "<p>x</p>", "failed")])
    with pytest.raises(EvalRefused):
        run_eval(make_settings(project_root=root, replay=True), split="test", progress=None)


@pytest.mark.browser
def test_run_eval_on_a_tiny_testset(make_settings, tmp_path, chromium):
    root = tmp_path / "proj"
    _testset(root, [
        ("a.html", '<html lang="de"><body><section><div>Text.</div><div><a id="t" href="x.html">Mehr</a></div>'
                   '<div><a href="y.html">Mehr</a></div></section></body></html>', "failed"),
        ("b.html", '<html lang="de"><body><p>Den Abfallkalender finden Sie <a id="t" href="z.html">hier</a>.</p>'
                   '</body></html>', "passed"),
    ])
    report = run_eval(make_settings(project_root=root, replay=True), split="dev", out_dir=tmp_path / "results",
                      progress=None)
    preds = {c["case_id"]: c for c in report["cases"]}
    assert (preds["c0"]["axe"], preds["c0"]["baseline"], preds["c0"]["ours"]) == ("inapplicable", "failed", "failed")
    assert preds["c0"]["tier"] == "heuristic"
    assert preds["c1"]["ours"] == "cantTell"  # replay without a recording → needs review (exact keys only)
    gen = report["by_source"]["generated"]
    assert gen["ours"]["recall"]["value"] == 1.0 and "vs_baseline" in gen["ours"]
    assert report["run"]["manifest_sha256"] and report["run"]["labels_tag"] is None
    assert {s["system"] for s in report["systems"]} == {"axe", "baseline", "ours", "ours_no_guard"}
    assert (tmp_path / "results" / "results.json").is_file()
    assert (tmp_path / "results" / "table.md").read_text(encoding="utf-8").startswith("# Klar. evaluation")
    assert not (tmp_path / "results" / "RUNLOG.jsonl").exists()  # only test-split runs are logged


def _one_test_case(root):
    _testset(root, [("a.html", '<html lang="de"><body><p><a id="t" href="x.html">Mehr</a></p></body></html>', "failed")])
    path = root / "data" / "testset" / "manifest.jsonl"
    path.write_text(path.read_text(encoding="utf-8").replace('"split": "dev"', '"split": "test"'), encoding="utf-8")
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.mark.browser
def test_labels_check_without_git_uses_the_env_vars(make_settings, tmp_path, monkeypatch, chromium):
    root = tmp_path / "proj"  # not inside a git repository (like the Docker image)
    sha = _one_test_case(root)
    settings = make_settings(project_root=root, replay=True)
    monkeypatch.setenv("KLAR_LABELS_MANIFEST_SHA256", "0" * 64)
    with pytest.raises(EvalRefused, match="differs"):
        run_eval(settings, split="test", progress=None)
    monkeypatch.setenv("KLAR_LABELS_MANIFEST_SHA256", sha)
    monkeypatch.setenv("KLAR_GIT_COMMIT", "abc1234")
    report = run_eval(settings, split="test", out_dir=tmp_path / "results", progress=None)
    run = report["run"]
    assert run["labels_source"] == "env" and run["labels_tag"] == "labels-v1" and run["commit"] == "abc1234"
    assert run["manifest_sha256"] == sha
    assert (tmp_path / "results" / "RUNLOG.jsonl").is_file()


@pytest.mark.browser
def test_labels_check_with_git_reads_the_tag(make_settings, tmp_path, monkeypatch, chromium):
    import shutil
    import subprocess

    if not shutil.which("git"):
        pytest.skip("git not installed")
    monkeypatch.delenv("KLAR_LABELS_MANIFEST_SHA256", raising=False)
    root = tmp_path / "proj"
    sha = _one_test_case(root)

    def git(*args):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)

    git("init", "-q")
    git("-c", "user.email=t@example.test", "-c", "user.name=t", "add", "data")
    git("-c", "user.email=t@example.test", "-c", "user.name=t", "commit", "-q", "-m", "labels")
    git("tag", "labels-v1")
    report = run_eval(make_settings(project_root=root, replay=True), split="test", out_dir=tmp_path / "r",
                      progress=None)
    assert report["run"]["labels_source"] == "git" and report["run"]["labels_sha256"] == sha
    assert report["run"]["commit"] and len(report["run"]["commit"].split("-")[0]) == 40


@pytest.mark.browser
def test_eval_writes_the_model_response_dataset(make_settings, tmp_path, chromium):
    from fake_llm import FakeLLM, klar_responder

    root = tmp_path / "proj"
    _testset(root, [
        ("a.html", '<html lang="de"><body><p>Den Abfallkalender finden Sie <a id="t" href="z.html">hier</a>.</p>'
                   '</body></html>', "passed"),
        ("b.html", '<html lang="de"><body><p><a id="t" href="y.html">Mehr</a></p></body></html>', "failed"),
    ])
    systems = ("axe", "baseline", "ours", "ours_no_guard", "ours_no_context")

    def read(path):
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    with FakeLLM(klar_responder) as fake:
        settings = make_settings(project_root=root, llm_base_url=fake.base_url)
        run_eval(settings, split="dev", out_dir=tmp_path / "r1", progress=None, systems=systems)
        run_eval(settings, split="dev", out_dir=tmp_path / "r2", progress=None, systems=systems)  # all cached
    first, again = read(tmp_path / "r1" / "responses.jsonl"), read(tmp_path / "r2" / "responses.jsonl")
    assert first and all(tuple(r) == RESPONSE_FIELDS for r in first)
    assert [(r["case_id"], r["candidate_id"], r["system"]) for r in first] == sorted(
        (r["case_id"], r["candidate_id"], r["system"]) for r in first)
    assert {r["case_id"] for r in first} == {"c0"}  # c1 is decided in code: no question, no line
    ours = next(r for r in first if r["system"] == "ours")
    assert ours["answer"]["category"] == "context" and ours["guard"] == {"verdict": "accepted", "reason": None}
    assert ours["final_outcome"] == "passed" and ours["error"] is None and ours["from_cache"] is False
    assert ours["endpoint_host"] == "127.0.0.1" and ours["tokens_in"] == 100 and ours["tokens_out"] == 20
    assert len(ours["prompt_sha256"]) == 64 and ours["prompt_version"].startswith("2.4.4/")
    assert any(r["system"] == "ours_no_context" for r in first)
    assert "page_data" not in json.dumps(first)  # no prompt text
    # the second run answers from the cache: same lines, same recorded cost, flagged as cached
    assert all(r["from_cache"] and r["match"] == "exact" for r in again)
    strip = lambda rows: [{k: v for k, v in r.items() if k not in ("from_cache", "match")} for r in rows]  # noqa: E731
    assert strip(again) == strip(first)


def test_act_cases_follow_the_implemented_checks_and_exclusions_are_explicit(tmp_path, monkeypatch):
    import klar.eval.runner as runner

    testset = tmp_path / "testset"
    testset.mkdir()
    rows = [{"case_id": f"a{i}", "criterion": crit, "source": "act", "act_rule": rule, "split": "test",
             "expected": "failed", "path": f"act/{rule}/{i}.html"}
            for i, (crit, rule) in enumerate([("2.4.4", "5effbb"), ("2.4.4", "5effbb"), ("2.4.4", "fd3a94"),
                                              ("3.1.2", "off6ek"), ("1.4.10", "b4f0c3")])]
    rows.append({"case_id": "g1", "criterion": "2.4.4", "source": "generated", "split": "test", "expected": "passed",
                 "path": "generated/g1.html"})
    (testset / "manifest.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    monkeypatch.setitem(runner.ACT_EXCLUDED, "off6ek", "our 3.1.2 check does not target this element type")
    cases, rules = runner.load_manifest(testset, split="test", criteria={"2.4.4", "3.1.2"}, source="all", limit=None)
    assert sorted(c["case_id"] for c in cases) == ["a0", "a1", "a2", "g1"]
    assert rules["5effbb"] == {"criterion": "2.4.4", "n": 2, "status": "evaluated", "reason": None}
    assert rules["fd3a94"]["n"] == 1 and rules["fd3a94"]["status"] == "evaluated"
    assert rules["off6ek"]["status"] == "excluded" and "does not target" in rules["off6ek"]["reason"]
    assert rules["b4f0c3"] == {"criterion": "1.4.10", "n": 1, "status": "excluded",
                               "reason": "no implemented check for 1.4.10"}
