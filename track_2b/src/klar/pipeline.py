"""Scan orchestration: render → axe → extract → apertus → verify → done.

    scan = new_scan(settings, job, model=backend.model)
    run_scan(scan, job, settings=…, llm=backend, vision=True, counter=…, emit=callback)

`emit(event, data)` receives "progress" (a ProgressStep dict), "finding" (a
Finding as dict) and "done" ({scan_id, state}). The whole scan runs in the
calling thread (Playwright's sync API); model questions run in a small thread
pool and are guarded back in the calling thread.

Order of the cascade for every candidate:
  1. prompt-injection pre-filter (guard.suspicious) → cantTell, never decided, never asked
  2. check.decide()                                → rule / heuristic finding
  3. needs vision but no vision backend            → cantTell "vision backend required"
  4. Apertus (round-robin budget across criteria)  → interpret() → evidence guard
"""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import nullcontext
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from klar import guard
from klar.capture.axe import axe_findings, run_axe
from klar.capture.browser import Browser, CaptureOptions, ScanError, extract, render
from klar.capture.page import CapturedPage
from klar.checks import registry
from klar.checks.base import BaseCheck
from klar.config import Settings
from klar.i18n import t
from klar.llm.cache import keys_for
from klar.llm.client import LLMBackend, LLMResult, RequestCounter
from klar.models import Candidate, Finding, LLMTask, Scan
from klar.netpolicy import NetPolicy

log = logging.getLogger(__name__)

STEPS = ("render", "axe", "extract", "apertus", "verify", "done")
OUTCOME_ORDER = {"failed": 0, "cantTell": 1, "passed": 2, "inapplicable": 3}
Emit = Callable[[str, dict], None]
INTERNAL_ERROR = "Internal error while checking this page"


class ScanTimeout(RuntimeError):
    pass


@dataclass
class ScanJob:
    url: str | None = None
    html: str | None = None
    ui_lang: str = "en"
    criteria: list[str] | None = None
    allow_form_submit: bool = False
    policy: NetPolicy | None = None  # default: settings.net_policy()
    form_origins: tuple[str, ...] = field(default_factory=tuple)  # may receive non-GET requests from the probe
    # candidate ids are computed from this instead of the page URL (evaluation: the case
    # path, so ids do not depend on the port of the local test server)
    id_base: str | None = None


def now() -> datetime:
    return datetime.now(timezone.utc)


def new_scan(settings: Settings, job: ScanJob, *, model: str) -> Scan:
    return Scan(
        id=uuid.uuid4().hex[:10], url=job.url or "inline:html", created_at=now(), mode=settings.mode,
        model=model, ui_lang=job.ui_lang if job.ui_lang in ("en", "de", "fr", "it") else "en",  # type: ignore[arg-type]
        state="queued", progress=[], findings=[], coverage=registry.coverage(), stats={},
    )


def resolve_criteria(criteria: list[str] | None) -> set[str]:
    if not criteria:
        return set(registry.BY_NUMBER)
    unknown = [c for c in criteria if c not in registry.BY_NUMBER]
    if unknown:
        raise ValueError(f"unknown WCAG 2.1 A/AA criteria: {', '.join(unknown)}")
    return set(criteria)


def empty_stats(vision: bool) -> dict:
    """ScanStats (flat) + a few diagnostic extras."""
    return {
        "failed": 0, "cantTell": 0, "passed": 0, "inapplicable": 0,
        "to_review": 0, "accepted": 0, "rejected": 0,
        "criteria_checked": 0, "criteria_rule": 0, "criteria_apertus": 0,
        "llm_calls": 0, "tokens_in": 0, "tokens_out": 0, "seconds": 0.0,
        "guard_rejected": 0, "injection_flagged": 0, "not_recorded": 0, "llm_errors": 0,
        "budget_skipped": {}, "replay_loose_hits": 0,
        "ai_requests": {"local": 0, "swiss_cloud": 0, "external": 0},
        # extras
        "candidates": 0, "decided_deterministically": 0, "asked_apertus": 0, "cache_hits": 0,
        "llm_seconds": 0.0, "vision": vision, "schema_level": None, "criteria_list": [],
        "criteria_apertus_list": [], "check_errors": [], "blocked_requests": [], "guard_log": [],
        "axe_superseded": [], "title_fetch": {},
        "timeout_notes": 0, "timeout_skipped_checks": [], "free_answers": 0,
        "error_code": None, "http_status": None, "final_url": None, "page_title": None, "max_llm_calls": None,
    }


def count_outcomes(scan: Scan) -> None:
    for k in ("failed", "cantTell", "passed", "inapplicable", "to_review", "accepted", "rejected"):
        scan.stats[k] = 0
    for f in scan.findings:
        scan.stats[f.outcome] += 1
        scan.stats[f.status] += 1


class Progress:
    def __init__(self, scan: Scan, emit: Emit):
        self.scan, self.emit = scan, emit
        self._t: dict[str, float] = {}
        for step in STEPS:  # all steps known from the start (UI stepper)
            scan.progress.append({"step": step, "state": "pending", "started_at": None, "duration_ms": None,
                                  "detail": None, "current": None, "total": None})

    def _entry(self, step: str) -> dict:
        return next(e for e in self.scan.progress if e["step"] == step)

    def start(self, step: str, detail: str | None = None, *, total: int | None = None) -> None:
        e = self._entry(step)
        self._t[step] = time.monotonic()
        e.update(state="running", started_at=now().isoformat(), detail=detail, duration_ms=0,
                 current=0 if total is not None else None, total=total)
        self.emit("progress", dict(e))

    def update(self, step: str, *, current: int | None = None, detail: str | None = None) -> None:
        e = self._entry(step)
        e["duration_ms"] = int((time.monotonic() - self._t.get(step, time.monotonic())) * 1000)
        if current is not None:
            e["current"] = current
        if detail is not None:
            e["detail"] = detail
        self.emit("progress", dict(e))

    def finish(self, step: str, detail: str | None = None, state: str = "done") -> None:
        e = self._entry(step)
        if step not in self._t:
            self._t[step] = time.monotonic()
            e["started_at"] = now().isoformat()
        e.update(state=state, duration_ms=int((time.monotonic() - self._t[step]) * 1000))
        if detail is not None:
            e["detail"] = detail
        if e.get("total") is not None and state == "done":
            e["current"] = e["total"]
        self.emit("progress", dict(e))

    def running(self) -> str | None:
        return next((e["step"] for e in self.scan.progress if e["state"] == "running"), None)


def _note_for(check: BaseCheck, c: Candidate, res: LLMResult) -> Finding:
    if res.error_kind == "not_recorded":
        return check.note(c, "note.not_recorded", source="apertus")
    if res.error_kind == "unparseable":
        return check.note(c, "note.unparseable", source="apertus")
    return check.note(c, "note.request_failed", source="apertus", error=res.error or "error")


def _is_free(llm: LLMBackend, task: LLMTask, check: BaseCheck, image_root: Path) -> bool:
    """True when answering costs no endpoint request (cache hit, recorded replay answer)."""
    probe = getattr(llm, "is_free", None)
    if probe is None:
        return False
    try:
        return bool(probe(task, prompt_version=check.prompt_version, image_root=image_root))
    except Exception:
        log.exception("is_free() failed for %s", check.criterion)
        return False


def response_record(check: BaseCheck, c: Candidate, task: LLMTask, res: LLMResult, llm: LLMBackend,
                    settings: Settings, image_root: Path, guard_info: dict | None) -> dict:
    """One model question for the response dataset: no prompt text (it is reproducible
    from the code version and the page), the cache key instead. For a cached or
    replayed answer, latency and tokens are those of the request that produced it."""
    rec = res.record or {}
    stored = bool(res.cached and rec)
    return {
        "criterion": check.criterion,
        "candidate_id": c.id,
        "selector": c.selector[:200],
        "prompt_version": check.prompt_version,
        "prompt_sha256": keys_for(llm.model, check.prompt_version, task, image_root)["key"],
        "model": res.model or llm.model,
        "endpoint_host": rec.get("endpoint_host") if stored else settings.base_url_host,
        "answer": res.answer,
        "error": res.error_kind,
        "guard": guard_info,
        "final_outcome": None,
        "latency_ms": int(rec.get("latency_ms") or 0) if stored else res.latency_ms,
        "tokens_in": int(rec.get("tokens_in") or 0) if stored else res.tokens_in,
        "tokens_out": int(rec.get("tokens_out") or 0) if stored else res.tokens_out,
        "from_cache": bool(res.cached),
        "match": res.match,
    }


def round_robin(pending: list[tuple[BaseCheck, Candidate]], budget: int) -> tuple[list, list]:
    """Fair share of the model budget across criteria (one candidate per criterion in turn)."""
    queues: dict[str, deque] = defaultdict(deque)
    for item in pending:
        queues[item[0].criterion].append(item)
    asked: list = []
    while len(asked) < budget and any(queues.values()):
        for crit in list(queues):
            if queues[crit] and len(asked) < budget:
                asked.append(queues[crit].popleft())
    skipped = [item for q in queues.values() for item in q]
    return asked, skipped


def run_scan(scan: Scan, job: ScanJob, *, settings: Settings, llm: LLMBackend, vision: bool,
             counter: RequestCounter, emit: Emit | None = None, options: CaptureOptions | None = None,
             browser: Browser | None = None,
             before_close: Callable[[CapturedPage, Scan], None] | None = None,
             on_responses: Callable[[list[dict]], None] | None = None) -> Scan:
    """`browser`: reuse an open Browser (evaluation runs); `before_close(page, scan)`
    runs while the page is still live, after all findings exist (evaluation matches
    findings to a target element there). `on_responses(records)` receives one record
    per question put to the model (see `response_record`), at the end of the scan."""
    emit = emit or (lambda event, data: None)
    started = time.monotonic()
    deadline = started + settings.scan_timeout
    before = counter.by_class
    ui = scan.ui_lang
    p = Progress(scan, emit)
    stats = empty_stats(vision)
    stats["max_llm_calls"] = settings.max_llm_calls  # the effective per-scan model budget
    stats["schema_level"] = getattr(llm, "schema_level", None) if settings.mode != "replay" else "replay"
    scan.stats = stats
    scan.state = "running"
    seen_ids: set[str] = set()
    checked: set[str] = set()
    judged: set[str] = set()
    rule_criteria: set[str] = set()
    policy = job.policy or settings.net_policy()

    responses: list[dict] = []

    def add(f: Finding) -> str:
        fid = f"{scan.id}-{f.id}"
        n = 2
        while fid in seen_ids:  # never two findings with one id
            fid = f"{scan.id}-{f.id}-{n}"
            n += 1
        seen_ids.add(fid)
        f = f.model_copy(update={"id": fid})
        scan.findings.append(f)
        emit("finding", f.model_dump(mode="json"))
        return fid

    def check_deadline() -> None:
        if time.monotonic() > deadline:
            raise ScanTimeout(f"scan exceeded KLAR_SCAN_TIMEOUT ({settings.scan_timeout:.0f} s)")

    try:
        selected = resolve_criteria(job.criteria)
        checks = [cls(ui, settings, vision=vision) for crit, cls in registry.implemented().items() if crit in selected]
        for module, error in registry.import_errors().items():  # a broken check module must not stay silent
            stats["check_errors"].append(f"{module}: import failed: {error}")
        scan_dir = settings.scans_path / scan.id
        opts = options or CaptureOptions()
        opts.allow_form_submit = job.allow_form_submit
        opts.policy = policy
        opts.form_origins = tuple(job.form_origins)

        with (nullcontext(browser) if browser is not None else Browser()) as browser:
            # ---- render ----------------------------------------------------------
            p.start("render", job.url or "inline HTML")
            page = render(browser, url=job.url, html=job.html, scan_dir=scan_dir, opts=opts)
            page.deadline = deadline  # checks read page.remaining() (see CapturedPage.deadline)
            page.id_base = job.id_base
            stats.update(http_status=page.http_status, final_url=page.url, page_title=page.title or None)
            p.finish("render", page.title or page.url)
            try:
                check_deadline()
                # ---- axe-core ------------------------------------------------------
                p.start("axe")
                axe_fs: list[Finding] = []
                try:
                    page.axe = run_axe(page.live, ui)
                    axe_fs = axe_findings(page.axe, page.url, selected, ui)
                    rule_criteria |= set(page.axe.get("criteria_tested", [])) & selected
                    stats["axe"] = {"version": page.axe.get("version"), "violations": len(page.axe.get("violations", [])),
                                    "incomplete": len(page.axe.get("incomplete", []))}
                    p.finish("axe", f"{len(axe_fs)} findings")
                except Exception as exc:
                    log.exception("axe-core failed")
                    p.finish("axe", f"error: {exc}", state="error")

                # ---- extract + deterministic decisions --------------------------------
                check_deadline()
                p.start("extract")
                extract(page)
                pending: list[tuple[BaseCheck, Candidate]] = []
                decided: list[Finding] = []
                out_of_time = False

                def timed_out() -> bool:
                    nonlocal out_of_time
                    out_of_time = out_of_time or time.monotonic() > deadline
                    return out_of_time

                for check in checks:
                    # KLAR_SCAN_TIMEOUT between checks: a check that was not started is
                    # skipped (no candidates exist yet to note) and listed in stats
                    if timed_out():
                        stats["timeout_skipped_checks"].append(check.criterion)
                        continue
                    try:
                        cands = check.candidates(page)[: check.max_candidates]
                    except Exception as exc:
                        log.exception("candidates() failed for %s", check.criterion)
                        stats["check_errors"].append(f"{check.criterion}: {type(exc).__name__}: {exc}")
                        continue
                    checked.add(check.criterion)
                    if registry.get(check.criterion).method in ("apertus_text", "apertus_vision"):
                        judged.add(check.criterion)
                    else:
                        rule_criteria.add(check.criterion)
                    stats["candidates"] += len(cands)
                    for i, c in enumerate(cands):
                        if timed_out():  # … and between decide() calls: the rest is noted, not judged
                            decided.extend(check.note(rest, "note.timeout") for rest in cands[i:])
                            stats["timeout_notes"] += len(cands) - i
                            break
                        pattern = guard.suspicious(c)
                        try:
                            f = check.decide(c)
                        except Exception as exc:
                            log.exception("decide() failed for %s", check.criterion)
                            stats["check_errors"].append(f"{check.criterion}: {type(exc).__name__}: {exc}")
                            continue
                        if pattern:
                            # Instruction-like text: never sent to the model, never passed by a
                            # heuristic. A failure found in code stands (an injected "passed"
                            # cannot cause it, and a nearby injection must not hide it).
                            stats["injection_flagged"] += 1
                            if f is None or f.outcome != "failed":
                                decided.append(check.note(c, "note.suspicious", source="heuristic", pattern=pattern))
                                continue
                        if f is not None:
                            stats["decided_deterministically"] += 1
                            decided.append(f)
                        elif check.needs_vision and not vision:
                            decided.append(check.note(c, "note.vision_required"))
                        else:
                            pending.append((check, c))
                # axe-core and a check's own rule may report the same element for the same
                # criterion (e.g. valid-lang vs 3.1.2 de46e4): keep the check's finding, which
                # carries a fix. Selectors are canonical (see capture/axe.py).
                # A check may also claim an axe rule for an element it sends to Apertus (1.4.3:
                # is this failing text a logotype?) via Candidate.extra["supersedes_axe"].
                # Superseded axe findings leave the report but are kept in stats so the
                # eval's "axe-core only" column still scores axe's raw verdict.
                # A "not judged" note (time limit, no vision) never hides axe's verdict.
                own_rules = {(f.criterion, f.selector) for f in decided
                             if f.source == "rule" and f.reason_code not in ("timeout", "vision_required")}
                claimed = {(c.criterion, c.selector, r) for _, c in pending for r in c.extra.get("supersedes_axe", ())}
                for f in axe_fs:
                    if (f.criterion, f.selector) in own_rules or (f.criterion, f.selector, f.axe_rule) in claimed:
                        stats["axe_superseded"].append({"criterion": f.criterion, "selector": f.selector,
                                                        "outcome": f.outcome, "axe_rule": f.axe_rule})
                    else:
                        add(f)
                for f in decided:
                    add(f)
                stats["title_fetch"] = dict(page.title_fetch_stats)
                if out_of_time:  # nothing more is asked: the findings so far stay, the scan ends in error
                    for check, c in pending:
                        add(check.note(c, "note.timeout"))
                    stats["timeout_notes"] += len(pending)
                    raise ScanTimeout(f"scan exceeded KLAR_SCAN_TIMEOUT ({settings.scan_timeout:.0f} s)")
                p.finish("extract", f"{stats['candidates']} elements, {len(pending)} for Apertus")

                # ---- Apertus ------------------------------------------------------------
                # KLAR_MAX_LLM_CALLS limits the questions that reach the model endpoint.
                # Answers already in the cache (live) or recorded (replay) cost nothing: they
                # are always served and never use up the budget of the other questions.
                tasks: dict[int, tuple[LLMTask | None, str | None]] = {}  # by id(candidate)
                free: list[tuple[BaseCheck, Candidate]] = []
                paid: list[tuple[BaseCheck, Candidate]] = []
                for check, c in pending:
                    try:  # questions are built here (pure: no live page), answers in the pool
                        task, err = check.question(c, ui), None
                    except Exception as exc:
                        log.exception("question() failed for %s", check.criterion)
                        task, err = None, f"question(): {exc}"
                    tasks[id(c)] = (task, err)
                    if task is None or _is_free(llm, task, check, scan_dir):
                        free.append((check, c))
                    else:
                        paid.append((check, c))
                asked_paid, skipped = round_robin(paid, settings.max_llm_calls)
                asked = free + asked_paid
                stats["free_answers"] = len(free)
                for check, c in skipped:
                    stats["budget_skipped"][check.criterion] = stats["budget_skipped"].get(check.criterion, 0) + 1
                    add(check.note(c, "note.budget"))
                p.start("apertus", total=len(asked))
                guarded = 0

                def ask(check: BaseCheck, c: Candidate) -> tuple[LLMTask | None, LLMResult]:
                    task, err = tasks[id(c)]
                    if task is None:
                        return None, LLMResult(answer=None, error_kind="request_failed", error=err)
                    return task, llm.ask(task, prompt_version=check.prompt_version, criterion=check.criterion,
                                         image_root=scan_dir)

                done_n = 0
                pool = ThreadPoolExecutor(max_workers=max(1, settings.llm_concurrency))
                futures = {pool.submit(ask, check, c): (check, c) for check, c in asked}
                try:
                    remaining = set(futures)
                    while remaining:
                        timeout = max(0.0, deadline - time.monotonic())
                        finished, remaining = wait(remaining, timeout=timeout, return_when=FIRST_COMPLETED)
                        if not finished:  # time limit: the rest is not asked
                            for fut in remaining:
                                fut.cancel()
                                check, c = futures[fut]
                                add(check.note(c, "note.timeout"))
                            stats["timeout_notes"] += len(remaining)
                            raise ScanTimeout(f"scan exceeded KLAR_SCAN_TIMEOUT ({settings.scan_timeout:.0f} s)")
                        for fut in finished:
                            check, c = futures[fut]
                            task, res = fut.result()
                            guard_info: dict | None = None
                            done_n += 1
                            stats["asked_apertus"] += 1
                            stats["llm_calls"] += res.requests
                            stats["cache_hits"] += int(res.cached)
                            stats["replay_loose_hits"] += int(res.match in ("task", "loose"))
                            stats["tokens_in"] += res.tokens_in
                            stats["tokens_out"] += res.tokens_out
                            stats["llm_seconds"] += res.latency_ms / 1000
                            if res.answer is None:
                                stats["not_recorded" if res.error_kind == "not_recorded" else "llm_errors"] += 1
                                f = _note_for(check, c, res)
                            else:
                                try:
                                    f = check.interpret(c, res.answer)
                                except Exception as exc:
                                    log.exception("interpret() failed for %s", check.criterion)
                                    f = check.note(c, "note.unparseable", source="apertus")
                                    stats["check_errors"].append(f"{check.criterion}: interpret: {exc}")
                                else:
                                    f = f.model_copy(update={"source": "apertus", "model": res.model or llm.model})
                                    verdict = guard.check(f, c, res.answer, selector_exists=page.selector_exists,
                                                          check_numbers=check.guard_numbers)
                                    guarded += 1
                                    before_outcome = f.outcome
                                    guard_info = {"verdict": "accepted" if verdict.ok else "rejected",
                                                  "reason": verdict.reason}
                                    if not verdict.ok:
                                        stats["guard_rejected"] += 1
                                        f = guard.downgrade(f, c, verdict.reason or "", ui)
                                    stats["guard_log"].append({"candidate": c.id, "criterion": check.criterion,
                                                               "before": before_outcome, "after": f.outcome,
                                                               "reason": verdict.reason})
                            if task is not None and f.source == "apertus":
                                f = f.model_copy(update={"context_shown": task.context_shown,
                                                         "model": res.model or llm.model})
                            fid = add(f)
                            if on_responses is not None and task is not None:
                                responses.append({**response_record(check, c, task, res, llm, settings, scan_dir,
                                                                    guard_info), "_finding": fid})
                            p.update("apertus", current=done_n)
                finally:
                    pool.shutdown(wait=False, cancel_futures=True)
                p.finish("apertus", f"{done_n}/{len(asked)}")

                # ---- verify (final consistency pass) -----------------------------------------
                p.start("verify")
                for i, f in enumerate(scan.findings):
                    if f.source == "apertus" and f.outcome != "cantTell" and not page.selector_exists(f.selector):
                        stats["guard_rejected"] += 1
                        scan.findings[i] = f.model_copy(update={
                            "outcome": "cantTell", "confidence": "low", "fix_diff": None, "fix_hint": None,
                            "reason_code": "not_grounded",
                            "explanation": t("note.not_grounded", ui, reason="selector does not resolve")})
                p.finish("verify", f"{guarded} answers checked, {stats['guard_rejected']} rejected")
                if before_close is not None:
                    try:
                        before_close(page, scan)
                    except Exception:
                        log.exception("before_close hook failed")
            finally:
                page.close()
        scan.state = "done"
    except Exception as exc:
        log.exception("scan %s failed", scan.id) if not isinstance(exc, ScanTimeout) else log.warning("%s", exc)
        scan.state = "error"
        if isinstance(exc, (ScanTimeout, ScanError)):
            # our own messages: one line, no paths or call logs
            stats["error"] = str(exc).splitlines()[0][:200]
            stats["error_code"] = "scan_timeout" if isinstance(exc, ScanTimeout) else exc.code
        else:  # details go to the server log only (log.exception above)
            stats["error"] = INTERNAL_ERROR
            stats["error_code"] = "internal"
        step = p.running()
        if step:
            p.finish(step, f"error: {stats['error']}", state="error")

    # ---- done ------------------------------------------------------------------------
    if on_responses is not None:
        final = {f.id: f.outcome for f in scan.findings}  # after the guard and the verify pass
        for r in responses:
            r["final_outcome"] = final.get(r.pop("_finding"))
        try:
            on_responses(responses)
        except Exception:
            log.exception("on_responses hook failed")
    scan.findings.sort(key=lambda f: (OUTCOME_ORDER[f.outcome], registry.sort_key(f.criterion), f.selector))
    count_outcomes(scan)
    stats["criteria_list"] = sorted(checked, key=registry.sort_key)
    stats["criteria_apertus_list"] = sorted(judged, key=registry.sort_key)
    stats["criteria_checked"] = len(checked)
    stats["criteria_apertus"] = len(judged)
    stats["criteria_rule"] = len(rule_criteria)
    after = counter.by_class
    stats["ai_requests"] = {k: after[k] - before.get(k, 0) for k in after}
    stats["external_ai_requests"] = stats["ai_requests"]["swiss_cloud"] + stats["ai_requests"]["external"]
    stats["blocked_requests"] = list(policy.blocked_log)[:50]
    stats["seconds"] = round(time.monotonic() - started, 2)
    stats["llm_seconds"] = round(stats["llm_seconds"], 2)
    for step in STEPS[:-1]:
        e = p._entry(step)
        if e["state"] == "pending":
            e["state"] = "skipped"
    p.start("done")
    p.finish("done", "error" if scan.state == "error" else f"{len(scan.findings)} findings",
             state="error" if scan.state == "error" else "done")
    emit("done", {"scan_id": scan.id, "state": scan.state})
    return scan
