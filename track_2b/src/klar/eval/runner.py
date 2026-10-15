"""`klar eval`: run Klar. on data/testset and compare systems on the same cases.

Systems (all computed from the SAME scan of each case, except ours_no_context):
  axe              axe-core alone (findings with an axe rule)
  baseline         same capture + keyword lists + lingua, every undecided candidate
                   → cantTell (= "Ours without the LLM"; the fair baseline)
  ours             rules + heuristics + Apertus + evidence guard
  ours_no_guard    Ours with the guard's downgrades undone (same answers, 0 extra tokens)
  ours_no_context  Ours, but every question is asked without its programmatic context
                   (a second pass: extra model calls, or extra recordings in replay)

The split comes from the manifest (`split`); test is the default and dev is for
tuning only. `surface_forms` and `tags` are not used for scoring, except the
`injection` tag, which gives a separate prompt-injection slice.

Scoring (metric definitions in klar/eval/metrics.py): unit = (case, criterion);
the target element is resolved in the live DOM; generated cases and W3C ACT
cases are reported separately and never pooled. The test set keeps only ACT judgement
rules; an ACT case is scored when its criterion has an implemented check. A rule our
check cannot score is listed in ACT_EXCLUDED with its reason; results.json reports n
per rule and every exclusion (`run.act_rules`), never silently.

Integrity: `--split test` is refused unless data/testset/manifest.jsonl is
byte-identical to the one at git tag `labels-v1`. Every test-split run is
appended to eval/results/RUNLOG.jsonl. The evaluation uses exact cache keys
only (no approximate replay) and one model request at a time.

Outputs: <KLAR_PROJECT_ROOT>/eval/results/results.json, table.md and responses.jsonl
(the model response dataset: one line per question put to the model while scoring a
case, sorted by case_id, candidate_id, system; RESPONSE_FIELDS. No prompt text: the
prompt is reproducible from the code version, `prompt_sha256` is its cache key).
"""

from __future__ import annotations

import functools
import hashlib
import json
import logging
import os
import subprocess
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from klar import __version__
from klar.capture.browser import Browser
from klar.checks import registry
from klar.config import Settings
from klar.eval.metrics import aggregate, compare, summarize
from klar.llm import make_backend
from klar.llm.capabilities import CapabilityCache
from klar.llm.client import SEED, TEMPERATURE, RequestCounter
from klar.netpolicy import origin_of
from klar.pipeline import ScanJob, new_scan, run_scan

log = logging.getLogger(__name__)

SYSTEMS = ("axe", "baseline", "ours", "ours_no_guard", "ours_no_context")
DEFAULT_SYSTEMS = ("axe", "baseline", "ours", "ours_no_guard")
# ACT rule id → why our check cannot score it (none today: every rule in the test set
# judges what its criterion's check targets).
ACT_EXCLUDED: dict[str, str] = {}
LABELS_TAG = "labels-v1"

_RELATED_JS = """([target, selectors]) => {
  let t = null;
  try { t = target ? document.querySelector(target) : null; } catch (e) { t = null; }
  return selectors.map(s => {
    if (!target) return true;
    if (!t) return false;
    let el = null;
    try { el = document.querySelector(s); } catch (e) { return false; }
    return !!el && (el === t || t.contains(el) || el.contains(t));
  });
}"""


class EvalRefused(RuntimeError):
    pass


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class StaticServer:
    """Local HTTP server for test pages (ACT cases use root-relative /test-assets/)."""

    def __init__(self, root: Path):
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(root)))
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{self.httpd.server_address[1]}/"

    @property
    def origin(self) -> str:
        return origin_of(self.base)

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


# --- integrity ------------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(["git", *args], cwd=root, capture_output=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.decode("utf-8", "replace").strip() if out.returncode == 0 else None


def commit_of(root: Path) -> str | None:
    """Commit of the code under evaluation: git when available, else KLAR_GIT_COMMIT
    (the Docker image has no .git; the Makefile passes the commit)."""
    head = _git(root, "rev-parse", "HEAD")
    if head:
        if _git(root, "status", "--porcelain", "--", "src", "data/testset"):
            head += "-dirty"
        return head
    return os.environ.get("KLAR_GIT_COMMIT") or None


def tagged_manifest_sha(root: Path) -> tuple[str | None, str]:
    """(sha256 of data/testset/manifest.jsonl at git tag labels-v1, where it came from).

    With git: read the file at the tag. Without git (Docker image): the value of
    KLAR_LABELS_MANIFEST_SHA256, which the Makefile computes from the tag."""
    top = _git(root, "rev-parse", "--show-toplevel")
    if top:
        rel = (root / "data" / "testset" / "manifest.jsonl").resolve().relative_to(Path(top).resolve()).as_posix()
        try:
            out = subprocess.run(["git", "show", f"{LABELS_TAG}:{rel}"], cwd=root, capture_output=True, timeout=20)
            if out.returncode == 0:
                return hashlib.sha256(out.stdout).hexdigest(), "git"
        except (OSError, subprocess.TimeoutExpired):
            pass
    env = (os.environ.get("KLAR_LABELS_MANIFEST_SHA256") or "").strip().lower()
    return (env, "env") if env else (None, "none")

# --- cases ------------------------------------------------------------------------------------

def load_manifest(testset: Path, *, split: str, criteria: set[str] | None, source: str,
                  limit: int | None) -> tuple[list[dict], dict[str, dict]]:
    """Cases to scan, and per ACT rule: criterion, n, status (evaluated / excluded) and
    the reason of an exclusion."""
    rows = [json.loads(line) for line in (testset / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()]
    implemented = set(registry.implemented())
    out: list[dict] = []
    act_rules: dict[str, dict] = {}
    for r in rows:
        if split != "all" and r.get("split") != split:
            continue
        if source != "all" and r.get("source") != source:
            continue
        if r["criterion"] not in registry.BY_NUMBER:
            continue
        is_act = r.get("source") == "act"
        # a criterion left out on purpose (--criteria) is not an exclusion; one without a
        # check is, for ACT rows (reported with its reason)
        if criteria is not None and r["criterion"] not in criteria and not (is_act and r["criterion"] not in implemented):
            continue
        if is_act:
            rule = r.get("act_rule") or "?"
            reason = ACT_EXCLUDED.get(rule) or (None if r["criterion"] in implemented
                                                 else f"no implemented check for {r['criterion']}")
            entry = act_rules.setdefault(rule, {"criterion": r["criterion"], "n": 0,
                                                "status": "excluded" if reason else "evaluated", "reason": reason})
            entry["n"] += 1
            if reason:
                continue
        out.append(r)
    return (out[:limit] if limit else out), dict(sorted(act_rules.items()))


def _case_url(case: dict, servers: dict[str, StaticServer]) -> str:
    if case.get("source") == "act":
        rel = case["path"][len("act/"):] if case["path"].startswith("act/") else case["path"]
        return servers["act"].base + rel
    return servers["generated"].base + case["path"]


def _scan_case(case: dict, settings: Settings, llm, vision: bool, counter: RequestCounter, browser: Browser,
               servers: dict[str, StaticServer], on_responses=None) -> tuple[list, dict, dict]:
    """Scan one case → (related findings, stats, guard log by finding id)."""
    url = _case_url(case, servers)
    allowed = tuple((s.origin, "/") for s in servers.values())
    job = ScanJob(url=url, ui_lang="en", criteria=[case["criterion"]], allow_form_submit=True,
                  policy=settings.net_policy(*allowed), form_origins=tuple(s.origin for s in servers.values()),
                  id_base=f"testset/{case['path']}")
    scan = new_scan(settings, job, model=llm.model)
    related: dict[str, bool] = {}

    def match(page, s):
        sels = [f.selector for f in s.findings] + [a["selector"] for a in s.stats.get("axe_superseded", [])]
        flags = page.live.evaluate(_RELATED_JS, [case.get("target_selector"), sels])
        related.update(dict(zip(sels, flags)))

    run_scan(scan, job, settings=settings, llm=llm, vision=vision, counter=counter, browser=browser,
             before_close=match, on_responses=on_responses)
    fs = [f for f in scan.findings if f.criterion == case["criterion"] and related.get(f.selector)]
    guard_log = {f"{scan.id}-{g['candidate']}": g for g in scan.stats.get("guard_log", [])}
    scan.stats["axe_superseded_case"] = [a for a in scan.stats.get("axe_superseded", [])
                                         if a["criterion"] == case["criterion"] and related.get(a["selector"])]
    return fs, scan.stats, guard_log


def predictions(fs: list, guard_log: dict, axe_superseded: list | tuple = ()) -> dict[str, str]:
    # "axe-core only" = axe's raw verdicts: its own findings plus those a check superseded.
    axe = aggregate([f.outcome for f in fs if f.reason_code == "axe"] + [a["outcome"] for a in axe_superseded])
    baseline = aggregate([f.outcome if f.source != "apertus" else "cantTell" for f in fs])
    ours = aggregate([f.outcome for f in fs])
    no_guard = aggregate([guard_log.get(f.id, {}).get("before", f.outcome) if f.source == "apertus" else f.outcome
                          for f in fs])
    return {"axe": axe, "baseline": baseline, "ours": ours, "ours_no_guard": no_guard}


def tier_of(fs: list, outcome: str) -> str:
    """Which tier produced the aggregated outcome (rule > heuristic > apertus on ties)."""
    for source in ("rule", "heuristic", "apertus"):
        if any(f.outcome == outcome and f.source == source for f in fs):
            return source
    return "none"


# --- the run ---------------------------------------------------------------------------------

def run_eval(settings: Settings, *, split: str = "test", criteria: list[str] | None = None, source: str = "all",
             systems: tuple[str, ...] = DEFAULT_SYSTEMS, limit: int | None = None, out_dir: Path | None = None,
             all_criteria: bool = False, dry_run: bool = False, progress=print) -> dict:
    root = settings.project_root
    testset = root / "data" / "testset"
    manifest = testset / "manifest.jsonl"
    if not manifest.is_file():
        raise FileNotFoundError(f"no test set at {testset}")
    unknown = set(systems) - set(SYSTEMS)
    if unknown or "ours" not in systems or "baseline" not in systems:
        raise ValueError(f"systems must include baseline and ours, from {', '.join(SYSTEMS)}")
    manifest_sha = sha256_file(manifest)
    tag_sha, tag_source = tagged_manifest_sha(root)
    if split in ("test", "all") and tag_sha != manifest_sha:
        why = (f"no git tag {LABELS_TAG} and no KLAR_LABELS_MANIFEST_SHA256" if tag_sha is None
               else f"the manifest differs from {LABELS_TAG} ({tag_source}: {tag_sha[:12]}…, file: {manifest_sha[:12]}…)")
        raise EvalRefused(f"refusing --split {split}: {why}. Use --split dev while developing.")

    # One request at a time, exact keys only: comparable, reproducible numbers.
    settings = settings.with_(llm_concurrency=1, replay_exact=True)
    wanted = set(criteria) if criteria else (None if all_criteria else set(registry.implemented()))
    cases, act_rules = load_manifest(testset, split=split, criteria=wanted, source=source, limit=limit)
    counter = RequestCounter()
    caps = CapabilityCache(settings, counter)
    llm = make_backend(settings, counter, capabilities=caps.get)
    vision = caps.get().vision
    llm_nc = None
    if "ours_no_context" in systems:
        nc_settings = settings.with_(ablation="no_context")
        llm_nc = make_backend(nc_settings, counter, capabilities=caps.get)
    servers = {"generated": StaticServer(testset), "act": StaticServer(testset / "act")}
    results: list[dict] = []
    responses: list[dict] = []

    def collect(case_id: str, system: str):
        return lambda records: responses.extend({"case_id": case_id, "system": system, **r} for r in records)

    # Cost of the "ours" pass only; the −context ablation's second pass is counted apart.
    totals = {"tokens_in": 0, "tokens_out": 0, "llm_calls": 0, "not_recorded": 0, "llm_errors": 0,
              "seconds": 0.0, "asked": 0}
    totals_nc = {"tokens_in": 0, "tokens_out": 0, "llm_calls": 0, "not_recorded": 0, "llm_errors": 0}
    started = time.monotonic()
    try:
        with Browser() as browser:
            for i, case in enumerate(cases, 1):
                t0 = time.monotonic()
                eval_settings = settings.with_(max_llm_calls=0) if dry_run else settings
                fs, stats, glog = _scan_case(case, eval_settings, llm, vision, counter, browser, servers,
                                             on_responses=collect(case["case_id"], "ours"))
                totals["seconds"] += time.monotonic() - t0
                row = {
                    "case_id": case["case_id"], "criterion": case["criterion"], "source": case.get("source"),
                    "lang": case.get("page_lang"), "trap": bool(case.get("trap")), "expected": case["expected"],
                    "injection": "injection" in (case.get("tags") or []), "template_id": case.get("template_id"),
                    "act_rule": case.get("act_rule"),
                    **predictions(fs, glog, stats.get("axe_superseded_case", [])),
                    "tier": tier_of(fs, aggregate([f.outcome for f in fs])),
                    "to_llm": any(f.source == "apertus" for f in fs) or bool(stats.get("budget_skipped")),
                    "findings": [{"outcome": f.outcome, "source": f.source, "reason_code": f.reason_code,
                                  "selector": f.selector[:120]} for f in fs],
                    "error": stats.get("error"),
                }
                if dry_run:
                    row["questions"] = sum(stats.get("budget_skipped", {}).values())
                if llm_nc is not None and not dry_run:
                    fs_nc, stats_nc, _ = _scan_case(case, settings.with_(ablation="no_context"), llm_nc, vision,
                                                    counter, browser, servers,
                                                    on_responses=collect(case["case_id"], "ours_no_context"))
                    row["ours_no_context"] = aggregate([f.outcome for f in fs_nc])
                    for k in totals_nc:
                        totals_nc[k] += stats_nc.get(k, 0)
                for k in ("tokens_in", "tokens_out", "llm_calls", "not_recorded", "llm_errors"):
                    totals[k] += stats.get(k, 0)
                totals["asked"] += stats.get("asked_apertus", 0)
                results.append(row)
                if progress and (i % 25 == 0 or i == len(cases)):
                    progress(f"  {i}/{len(cases)} cases · {time.monotonic() - started:.0f} s")
    finally:
        for s in servers.values():
            s.close()

    if dry_run:
        questions = sum(r.get("questions", 0) for r in results)
        return {"dry_run": True, "cases": len(results), "questions": questions,
                "estimated_tokens": questions * 700, "systems": list(systems)}

    report = build_report(results, systems=systems, settings=settings, llm=llm, caps=caps.get(), split=split,
                          source=source, manifest_sha=manifest_sha, tag_sha=tag_sha, tag_source=tag_source,
                          act_rules=act_rules, totals=totals, totals_nc=totals_nc if llm_nc is not None else None,
                          seconds=time.monotonic() - started, counter=counter, vision=vision)
    out = out_dir or (root / "eval" / "results")
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "table.md").write_text(to_markdown(report), encoding="utf-8")
    write_responses(out / "responses.jsonl", responses)
    if split in ("test", "all"):
        entry = {k: report["run"][k] for k in ("id", "commit", "split", "mode", "model", "endpoint_host",
                                                "labels_tag", "manifest_sha256", "cases")}
        entry["systems"] = list(systems)
        with (out / "RUNLOG.jsonl").open("a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(entry) + "\n")
    report["paths"] = [str(out / "results.json"), str(out / "table.md"), str(out / "responses.jsonl")]
    return report


# One line of eval/results/responses.jsonl ("ours" covers ours and ours_no_guard: same answers).
RESPONSE_FIELDS = ("case_id", "system", "criterion", "candidate_id", "selector", "prompt_version", "prompt_sha256",
                   "model", "endpoint_host", "answer", "error", "guard", "final_outcome", "latency_ms", "tokens_in",
                   "tokens_out", "from_cache", "match")


def write_responses(path: Path, records: list[dict]) -> None:
    """Deterministic: sorted by (case_id, candidate_id, system), fixed field order."""
    rows = sorted(records, key=lambda r: (str(r["case_id"]), r["candidate_id"], r["system"]))
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps({k: r.get(k) for k in RESPONSE_FIELDS}, ensure_ascii=False) + "\n")


def _group_block(rows: list[dict], systems: tuple[str, ...]) -> dict:
    block = {s: summarize([(r["expected"], r[s]) for r in rows]) for s in systems if all(s in r for r in rows)}
    for s in block:
        if s != "baseline":
            block[s]["vs_baseline"] = compare([(r["expected"], r[s]) for r in rows],
                                              [(r["expected"], r["baseline"]) for r in rows])
    return block


def build_report(results: list[dict], *, systems, settings: Settings, llm, caps, split: str, source: str,
                 manifest_sha: str, tag_sha: str | None, tag_source: str, act_rules: dict, totals: dict,
                 seconds: float, counter: RequestCounter, totals_nc: dict | None = None,
                 vision: bool | None = None) -> dict:
    from urllib.parse import urlparse

    by: dict[str, dict[str, list]] = {k: defaultdict(list) for k in ("source", "criterion", "lang", "trap", "injection")}
    for r in results:
        by["source"][r["source"]].append(r)
        by["criterion"][f"{r['source']}:{r['criterion']}"].append(r)
        by["lang"][f"{r['source']}:{r['lang']}"].append(r)
        by["trap"][f"{r['source']}:{'trap' if r['trap'] else 'regular'}"].append(r)
        if r.get("injection"):
            by["injection"][r["source"]].append(r)
    def tiers_of(rows_all: list[dict]) -> dict[str, dict]:
        # Precision as in summarize(): gold-cantTell cases are left out.
        out = {}
        for tier in ("rule", "heuristic", "apertus", "none"):
            rows = [r for r in rows_all if r["tier"] == tier]
            failed_pred = [r for r in rows if r["ours"] == "failed" and r["expected"] != "cantTell"]
            out[tier] = {"n": len(rows), "failed_predictions": len(failed_pred),
                         "failed_precision": (round(sum(r["expected"] == "failed" for r in failed_pred) / len(failed_pred), 4)
                                              if failed_pred else None)}
        return out

    # Generated and ACT cases are never pooled: tiers and the share sent to the model are per source.
    tiers = {k: tiers_of(v) for k, v in sorted(by["source"].items())}
    share_to_llm = {k: round(sum(r["to_llm"] for r in v) / len(v), 4) for k, v in sorted(by["source"].items())}
    n = len(results) or 1
    run = {
        "id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"), "klar_version": __version__,
        "commit": commit_of(settings.project_root), "labels_tag": LABELS_TAG if tag_sha == manifest_sha else None,
        "manifest_sha256": manifest_sha, "labels_sha256": tag_sha, "labels_source": tag_source, "split": split, "source": source, "cases": len(results),
        "act_rules": act_rules,  # per ACT rule: criterion, n, evaluated / excluded (+ reason)
        "act_cases_excluded": sum(v["n"] for v in act_rules.values() if v["status"] != "evaluated"),
        "templates": len({r.get("template_id") for r in results if r.get("template_id")}),
        "mode": settings.mode, "model": llm.model,
        "endpoint_host": urlparse(settings.llm_base_url or "").hostname if settings.mode != "replay" else None,
        "replay_models": getattr(llm, "recorded_models", None), "seconds": round(seconds, 1),
        "ai_requests": counter.by_class, "vision": vision,
    }
    system_params = [{"system": s, "model": llm.model if s.startswith("ours") else None,
                      "endpoint_host": run["endpoint_host"] if s.startswith("ours") else None, "mode": settings.mode,
                      "concurrency": settings.llm_concurrency, "seed": SEED, "temperature": TEMPERATURE,
                      "schema_level": caps.schema_level if settings.mode != "replay" else "replay"} for s in systems]
    return {
        "run": run,
        "systems": system_params,
        "by_source": {k: _group_block(v, systems) for k, v in sorted(by["source"].items())},
        "by_criterion": {k: _group_block(v, systems) for k, v in sorted(by["criterion"].items())},
        "by_lang": {k: _group_block(v, systems) for k, v in sorted(by["lang"].items())},
        "by_trap": {k: _group_block(v, systems) for k, v in sorted(by["trap"].items())},
        # Prompt-injection cases (manifest tag "injection"), reported on their own (SEC-1).
        "injection": {k: _group_block(v, systems) for k, v in sorted(by["injection"].items())},
        "tiers": tiers,
        "share_to_llm": share_to_llm,
        # System "ours" only (one scan per case); the −context ablation's own pass is in ablation_no_context.
        "cost": {"llm_calls": totals["llm_calls"], "tokens_in": totals["tokens_in"], "tokens_out": totals["tokens_out"],
                 "tokens_per_page": round((totals["tokens_in"] + totals["tokens_out"]) / n, 1),
                 "seconds_per_page": round(totals["seconds"] / n, 2), "not_recorded": totals["not_recorded"],
                 "llm_errors": totals["llm_errors"], "ablation_no_context": totals_nc},
        "cases": results,
    }


def _fmt(m: dict | None) -> str:
    if not m or m.get("value") is None:
        return "–"
    lo, hi = m["ci95"]
    return f"{m['value'] * 100:.1f} % [{lo * 100:.0f}–{hi * 100:.0f}]"


LABELS = {"axe": "axe-core only", "baseline": "Baseline (no LLM)", "ours": "Ours (Apertus)",
          "ours_no_guard": "Ours − guard", "ours_no_context": "Ours − context"}


def to_markdown(report: dict) -> str:
    run = report["run"]
    lines = [
        f"# Klar. evaluation — split `{run['split']}`",
        "",
        f"Run {run['id']} · commit `{run['commit']}` · labels `{run['labels_tag']}` · manifest sha256 "
        f"`{run['manifest_sha256'][:12]}…` · mode `{run['mode']}` · model `{run['model']}` · {run['cases']} cases "
        f"({run['act_cases_excluded']} ACT cases excluded) · "
        f"tokens/page {report['cost']['tokens_per_page']} · s/page {report['cost']['seconds_per_page']} (Ours) · "
        f"not recorded {_not_recorded(report)} · model errors {_llm_errors(report)}",
        "",
        "Positive class = failed. Rates with Wilson 95 % intervals; p = exact McNemar vs Baseline on "
        "decision correctness (failed / review / no failure). Generated and W3C ACT cases are never pooled.",
        "",
    ]
    if run.get("act_rules"):
        lines += ["## W3C ACT rules", "", "| Rule | Criterion | n | Status |", "|---|---|---|---|"]
        for rule, v in run["act_rules"].items():
            status = v["status"] if not v.get("reason") else f"{v['status']}: {v['reason']}"
            lines.append(f"| {rule} | {v['criterion']} | {v['n']} | {status} |")
        lines.append("")
    for scope_name, groups in (("Source", report["by_source"]), ("Criterion", report["by_criterion"])):
        lines += [f"## By {scope_name.lower()}", "",
                  f"| {scope_name} | System | n | Precision | Recall | F1 | False pass (explicit + silent) "
                  "| Flagged recall | Deferral | p vs B |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for key, block in groups.items():
            for system, m in block.items():
                p = m.get("vs_baseline", {}).get("p_value")
                lines.append(f"| {key} | {LABELS.get(system, system)} | {m['n']} | {_fmt(m['precision'])} | "
                             f"{_fmt(m['recall'])} | {m['f1'] if m['f1'] is not None else '–'} | "
                             f"{_fmt(m['false_pass'])} | {_fmt(m['flagged_recall'])} | {_fmt(m['deferral_rate'])} | "
                             f"{p if p is not None else '–'} |")
        lines.append("")
    for src, t in report["tiers"].items():
        lines += [f"## Tiers (Ours, {src} cases)", "",
                  "| Tier | Cases decided | Failed predictions | Precision of failed |", "|---|---|---|---|"]
        lines += [f"| {k} | {v['n']} | {v['failed_predictions']} | {v['failed_precision'] if v['failed_precision'] is not None else '–'} |"
                  for k, v in t.items()]
        lines += ["", f"Share of {src} cases that reached the LLM: {report['share_to_llm'][src] * 100:.1f} %", ""]
    lines += ["Klar. pre-checks WCAG 2.1 AA criteria. These numbers do not certify conformance.", ""]
    return "\n".join(lines)


def _not_recorded(report: dict) -> int:
    c = report["cost"]
    return c["not_recorded"] + ((c.get("ablation_no_context") or {}).get("not_recorded") or 0)


def _llm_errors(report: dict) -> int:
    c = report["cost"]
    return c["llm_errors"] + ((c.get("ablation_no_context") or {}).get("llm_errors") or 0)
