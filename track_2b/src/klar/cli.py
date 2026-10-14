"""Command line: klar serve | scan | demo | record | replay-check | criteria | eval | health.

    klar serve [--host 127.0.0.1] [--port 8080]
    klar scan https://www.example.ch/ --lang de --criteria 2.4.4,3.1.2 --out report.html
    klar scan ./page.html --out findings.json          (a local file is scanned via file://)
    klar demo [--strict]                               (every page of the bundled demo → $KLAR_DATA_DIR/reports/)
    klar record                                        (live endpoint: record answers for every demo page)
    klar replay-check [--rescan]                       (CI gate: replay complete, exit 1 otherwise)
    klar criteria --json                               (the 50 criteria, from the registry)
    klar eval --split dev|test [--systems …]           (data/testset → eval/results/{results.json,table.md})
    klar health                                        (mode, model, capability probes)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

from klar import __version__
from klar.config import Settings

EXT_FORMAT = {".json": "json", ".jsonld": "earl", ".csv": "csv", ".html": "html", ".htm": "html"}
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f\x1b]|\x1b\[[0-9;]*[A-Za-z]")


def clean(text: str, n: int | None = None) -> str:
    """Page text printed to a terminal: no control characters, no ANSI escapes."""
    s = _CONTROL.sub("", text or "")
    return s[:n] if n else s


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")


def _utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass


def _settings_or_exit() -> Settings:
    settings = Settings.from_env()
    if settings.config_error:
        print(f"configuration error: {settings.config_error}", file=sys.stderr)
        raise SystemExit(2)
    return settings


# --- serve ----------------------------------------------------------------------------------

def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    from klar.api.app import create_app

    os.environ["KLAR_APP_PORT"] = str(args.port)  # the app must know its own port (/demo/ allow-list)
    settings = Settings.from_env()
    if settings.config_error:
        print(f"configuration error: {settings.config_error} (health reports it)", file=sys.stderr)
    uvicorn.run(create_app(settings), host=args.host, port=args.port, log_level="info")
    return 0


# --- scan --------------------------------------------------------------------------------------

class _Run:
    """Backend, capabilities and browser shared by several scans of one CLI command."""

    def __init__(self, settings: Settings):
        from klar.llm import make_backend
        from klar.llm.capabilities import CapabilityCache
        from klar.llm.client import RequestCounter

        self.settings = settings
        self.counter = RequestCounter()
        self.caps = CapabilityCache(settings, self.counter)
        self.llm = make_backend(settings, self.counter, capabilities=self.caps.get)
        self.vision = self.caps.get().vision

    def scan(self, job, *, browser=None, quiet: bool = True):
        from klar.pipeline import new_scan, run_scan
        from klar.store import Store

        scan = new_scan(self.settings, job, model=self.llm.model)

        def emit(event: str, data: dict) -> None:
            if not quiet and event == "progress" and data["state"] in ("done", "error"):
                print(f"  {data['step']:<8} {data['state']:<5} {data['duration_ms'] or 0:>7} ms  "
                      f"{clean(data.get('detail') or '', 80)}", file=sys.stderr)

        run_scan(scan, job, settings=self.settings, llm=self.llm, vision=self.vision, counter=self.counter,
                 emit=emit, browser=browser)
        try:
            Store(self.settings.db_path).save_scan(scan)
        except Exception as exc:
            print(f"warning: scan not stored ({exc})", file=sys.stderr)
        return scan


def _print_scan(scan) -> None:
    s = scan.stats
    print(f"\n{clean(scan.url)}\n  failed {s.get('failed', 0)} · needs review {s.get('cantTell', 0)} · "
          f"passed {s.get('passed', 0)} · {s.get('seconds')} s · model calls {s.get('llm_calls')} · "
          f"guard rejected {s.get('guard_rejected')} · AI requests {s.get('ai_requests')}")
    for f in scan.findings:
        if f.outcome in ("failed", "cantTell"):
            mark = "■" if f.outcome == "failed" else "◆"
            print(f"  {mark} {f.criterion:<6} [{f.source}] {clean(f.selector, 60)}\n      {clean(f.explanation, 160)}")
    for err in s.get("check_errors", []):
        print(f"warning: {err}", file=sys.stderr)
    if s.get("error"):
        print(f"error: {s['error']}", file=sys.stderr)


def _write(scan, settings: Settings, path: Path, fmt: str | None = None) -> Path:
    from klar.report import render

    fmt = fmt or EXT_FORMAT.get(path.suffix.lower(), "json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(render(scan, fmt, assets_dir=settings.scans_path / scan.id))
    return path


def cmd_scan(args: argparse.Namespace) -> int:
    from klar.pipeline import ScanJob

    settings = _settings_or_exit()
    local = Path(args.url)
    if local.exists():  # an operator-chosen local file: file: URLs are allowed for this scan only
        url = (local / "index.html" if local.is_dir() else local).resolve().as_uri()
        policy = settings.net_policy(allow_file=True)
    else:
        url = args.url if "://" in args.url else "https://" + args.url
        policy = settings.net_policy()
        verdict = policy.check(url)
        if not verdict.ok:
            print(f"url not allowed: {verdict.reason}", file=sys.stderr)
            return 2
    criteria = [c.strip() for c in args.criteria.split(",")] if args.criteria else None
    run = _Run(settings)
    print(f"Klar. {__version__} · mode={settings.mode} · model={run.llm.model} · vision={run.vision}", file=sys.stderr)
    # No form is ever submitted on a scanned site: the probe runs only on the bundled demo.
    job = ScanJob(url=url, ui_lang=args.lang, criteria=criteria, allow_form_submit=False, policy=policy)
    scan = run.scan(job, quiet=args.quiet)
    _print_scan(scan)
    if args.out:
        print(f"report: {_write(scan, settings, Path(args.out), args.format).resolve()}")
    return 0 if scan.state == "done" else 1


# --- demo, record, replay-check ---------------------------------------------------------------------

def demo_pages(demo_dir: Path) -> list[str]:
    """Every HTML page of the bundled demo site, index first."""
    pages = sorted(p.relative_to(demo_dir).as_posix() for p in demo_dir.rglob("*.html"))
    return sorted(pages, key=lambda p: (p != "index.html", "/" in p, p))


def _api_base(settings: Settings) -> str | None:
    import httpx

    base = f"http://127.0.0.1:{settings.app_port}"
    try:
        r = httpx.get(base + "/api/health", timeout=2)
        r.raise_for_status()
        return base
    except Exception:
        return None


def _summary(scans: list, pages: list[str], settings: Settings, model: str, via: str) -> dict:
    keys = ("failed", "cantTell", "passed", "inapplicable", "not_recorded", "llm_errors", "replay_loose_hits",
            "llm_calls", "guard_rejected", "injection_flagged", "tokens_in", "tokens_out")
    totals = {k: sum(int(s.stats.get(k, 0) or 0) for s in scans) for k in keys}
    ai = {"local": 0, "swiss_cloud": 0, "external": 0}
    per_criterion: dict[str, dict[str, int]] = {}
    for s in scans:
        for k, v in (s.stats.get("ai_requests") or {}).items():
            ai[k] = ai.get(k, 0) + v
        for f in s.findings:
            per_criterion.setdefault(f.criterion, {}).setdefault(f.outcome, 0)
            per_criterion[f.criterion][f.outcome] += 1
    return {
        "mode": settings.mode, "model": model, "via": via, "pages": len(pages),
        "errors": sum(1 for s in scans if s.state != "done"), **totals, "ai_requests": ai,
        "per_criterion": dict(sorted(per_criterion.items())),
        "scans": [{"page": p, "scan_id": s.id, "state": s.state, "failed": s.stats.get("failed", 0),
                   "cantTell": s.stats.get("cantTell", 0), "passed": s.stats.get("passed", 0),
                   "not_recorded": s.stats.get("not_recorded", 0), "llm_errors": s.stats.get("llm_errors", 0)}
                  for p, s in zip(pages, scans)],
    }


def run_demo(settings: Settings, *, lang: str, criteria: list[str] | None, prefix: str = "demo",
             use_api: bool = True, quiet: bool = True) -> tuple[dict, list[Path]]:
    """Scan every demo page; write <prefix>-<page>.{html,json}, <prefix>-summary.json and
    <prefix>-latest.{json,html} (summary + index page) under $KLAR_DATA_DIR/reports/."""
    from klar.models import Scan
    from klar.pipeline import ScanJob

    pages = demo_pages(settings.demo_path)
    if not pages:
        raise FileNotFoundError(f"demo site not found at {settings.demo_path}")
    reports = settings.data_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    scans: list = []
    base = _api_base(settings) if use_api else None
    if base:  # through the running app: its counters and scan history stay consistent
        import httpx

        model = "?"
        with httpx.Client(base_url=base, timeout=30) as client:
            for page in pages:
                r = client.post("/api/scans", json={"url": f"{base}/demo/{page}", "ui_lang": lang, "criteria": criteria})
                r.raise_for_status()
                scan_id = r.json()["id"]
                deadline = time.monotonic() + settings.scan_timeout + 60
                while True:
                    data = client.get(f"/api/scans/{scan_id}").json()
                    if data["state"] in ("done", "error") or time.monotonic() > deadline:
                        break
                    time.sleep(0.5)
                scan = Scan.model_validate(data)
                model = scan.model
                scans.append(scan)
                if not quiet:
                    print(f"  {page:<32} {scan.state:<5} failed {scan.stats.get('failed', 0)} · "
                          f"review {scan.stats.get('cantTell', 0)}", file=sys.stderr)
        via = "api"
    else:
        from klar.capture.browser import Browser
        from klar.eval.runner import StaticServer

        run = _Run(settings)
        model = run.llm.model
        server = StaticServer(settings.demo_path)
        try:
            policy = settings.net_policy((server.origin, "/"))
            with Browser() as browser:
                for page in pages:
                    job = ScanJob(url=server.base + page, ui_lang=lang, criteria=criteria, allow_form_submit=True,
                                  policy=policy, form_origins=(server.origin,))
                    scan = run.scan(job, browser=browser)
                    scans.append(scan)
                    if not quiet:
                        print(f"  {page:<32} {scan.state:<5} failed {scan.stats.get('failed', 0)} · "
                              f"review {scan.stats.get('cantTell', 0)}", file=sys.stderr)
        finally:
            server.close()
        via = "in-process"
    written: list[Path] = []
    for page, scan in zip(pages, scans):
        slug = re.sub(r"[^a-z0-9]+", "-", page.lower().removesuffix(".html")).strip("-")
        for ext in ("html", "json"):
            written.append(_write(scan, settings, reports / f"{prefix}-{slug}.{ext}"))
    summary = _summary(scans, pages, settings, model, via)
    for name in (f"{prefix}-summary.json", f"{prefix}-latest.json"):
        (reports / name).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    _write(scans[0], settings, reports / f"{prefix}-latest.html")
    return summary, [reports / f"{prefix}-latest.json", reports / f"{prefix}-latest.html"] + written


def _summary_line(tag: str, s: dict, ok: bool | None = None) -> str:
    head = f"{tag}: {'OK' if ok else 'FAIL'} · " if ok is not None else f"{tag}: "
    return (head + f"mode={s['mode']} · model={s['model']} · pages={s['pages']} · errors={s['errors']} · "
            f"failed={s['failed']} · review={s['cantTell']} · passed={s['passed']} · not_recorded={s['not_recorded']} · "
            f"llm_errors={s['llm_errors']} · loose_hits={s['replay_loose_hits']} · ai_requests={s['ai_requests']}")


def cmd_demo(args: argparse.Namespace) -> int:
    settings = _settings_or_exit()
    criteria = [c.strip() for c in args.criteria.split(",")] if args.criteria else None
    try:
        summary, paths = run_demo(settings, lang=args.lang, criteria=criteria, use_api=not args.in_process,
                                  quiet=args.quiet)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(_summary_line("demo", summary))
    for p in paths[:2]:
        print(f"report: {p.resolve()}")
    failed = summary["errors"] > 0 or (args.strict and (summary["not_recorded"] or summary["llm_errors"]))
    return 1 if failed else 0


def replay_ok(summary: dict) -> bool:
    return (summary.get("mode") == "replay" and summary.get("errors", 1) == 0
            and summary.get("not_recorded", 1) == 0 and summary.get("llm_errors", 1) == 0)


def cmd_replay_check(args: argparse.Namespace) -> int:
    """CI gate: exit 0 only if the demo report is a replay with every answer recorded."""
    settings = Settings.from_env()
    report = Path(args.report) if args.report else settings.data_dir / "reports" / "demo-latest.json"
    if report.is_file() and not args.rescan:
        summary = json.loads(report.read_text(encoding="utf-8"))
        tag = f"replay-check ({report.name})"
    else:
        settings = settings.with_(replay=True, replay_exact=True)
        criteria = [c.strip() for c in args.criteria.split(",")] if args.criteria else None
        try:
            summary, _ = run_demo(settings, lang=args.lang, criteria=criteria, prefix="replay-check", use_api=False)
        except FileNotFoundError as exc:
            print(f"replay-check: FAIL · {exc}")
            return 1
        tag = "replay-check (fresh replay, exact keys)"
    ok = replay_ok(summary)
    print(_summary_line(tag, summary, ok))
    return 0 if ok else 1


def cmd_record(args: argparse.Namespace) -> int:
    settings = _settings_or_exit()
    if settings.mode == "replay":
        print("record needs a live Apertus endpoint (set LLM_BASE_URL, LLM_NAME, LLM_API_KEY; KLAR_REPLAY=0)",
              file=sys.stderr)
        return 2
    settings = settings.with_(record=True)
    print(f"recording into {settings.replay_path} from {settings.llm_name} at {settings.base_url_host}",
          file=sys.stderr)
    summary, _ = run_demo(settings, lang=args.lang, criteria=None, prefix="record", use_api=False, quiet=args.quiet)
    print(_summary_line("record", summary))
    check = settings.with_(replay=True, replay_exact=True, llm_base_url=None)
    replay, _ = run_demo(check, lang=args.lang, criteria=None, prefix="replay-check", use_api=False)
    ok = replay_ok(replay)
    print(_summary_line("replay-check (exact keys)", replay, ok))
    return 0 if ok and summary["errors"] == 0 else 1


# --- criteria, eval, health -------------------------------------------------------------------------

def cmd_criteria(args: argparse.Namespace) -> int:
    from klar.checks import registry

    items = registry.criteria_info()
    if args.json:
        print(json.dumps([c.model_dump() for c in items], ensure_ascii=False, indent=2))
    else:
        for c in items:
            mark = "✓" if c.implemented else " "
            ev = "evaluated" if c.evaluated else ""
            print(f"{mark} {c.criterion:<7} {c.level:<3} {c.method:<15} {ev:<10} {c.name}")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    from klar.eval.runner import DEFAULT_SYSTEMS, EvalRefused, run_eval, to_markdown

    settings = _settings_or_exit()
    criteria = [c.strip() for c in args.criteria.split(",")] if args.criteria else None
    systems = tuple(s.strip() for s in args.systems.split(",")) if args.systems else DEFAULT_SYSTEMS
    try:
        report = run_eval(settings, split=args.split, criteria=criteria, source=args.source, systems=systems,
                          limit=args.limit, out_dir=Path(args.out) if args.out else None,
                          all_criteria=args.all_criteria, dry_run=args.dry_run,
                          progress=lambda m: print(m, file=sys.stderr))
    except (FileNotFoundError, EvalRefused, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if report.get("dry_run"):
        print(f"dry run: {report['cases']} cases · {report['questions']} model questions · "
              f"~{report['estimated_tokens']} tokens per system that uses the model")
        return 0
    print(to_markdown(report))
    for p in report["paths"]:
        print(f"results: {p}")
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    from klar.api.app import health_of
    from klar.api.manager import Services

    settings = Settings.from_env()
    svc = Services(settings)
    try:
        svc.caps.get()  # probe now (the API does it in the background)
        print(health_of(svc).model_dump_json(indent=2))
    finally:
        svc.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="klar", description="Klar. — WCAG 2.1 AA pre-checks with Apertus.")
    ap.add_argument("--version", action="version", version=f"klar {__version__}")
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    langs = ["en", "de", "fr", "it"]

    s = sub.add_parser("serve", help="start the web app and API")
    s.add_argument("--host", default="127.0.0.1", help="bind address (Docker passes 0.0.0.0 explicitly)")
    s.add_argument("--port", type=int, default=8080)
    s.set_defaults(func=cmd_serve)

    s = sub.add_parser("scan", help="scan one URL or local HTML file")
    s.add_argument("url")
    s.add_argument("--lang", default=None, choices=langs, help="UI language of the findings")
    s.add_argument("--criteria", help="comma-separated, e.g. 2.4.4,3.1.2 (default: all implemented)")
    s.add_argument("--out", help="report file; format from extension (.json .jsonld .csv .html)")
    s.add_argument("--format", choices=["json", "earl", "csv", "html"])
    s.add_argument("-q", "--quiet", action="store_true")
    s.set_defaults(func=cmd_scan)

    s = sub.add_parser("demo", help="scan every page of the bundled demo site")
    s.add_argument("--lang", default=None, choices=langs)
    s.add_argument("--criteria")
    s.add_argument("--in-process", action="store_true", help="do not go through a running server")
    s.add_argument("--strict", action="store_true", help="exit 1 also on unrecorded answers or model errors")
    s.add_argument("-q", "--quiet", action="store_true")
    s.set_defaults(func=cmd_demo)

    s = sub.add_parser("record", help="record Apertus answers for every demo page (live endpoint)")
    s.add_argument("--lang", default=None, choices=langs)
    s.add_argument("-q", "--quiet", action="store_true")
    s.set_defaults(func=cmd_record)

    s = sub.add_parser("replay-check", help="CI gate: the demo replays completely (exit 1 otherwise)")
    s.add_argument("--report", help="demo summary to check (default $KLAR_DATA_DIR/reports/demo-latest.json)")
    s.add_argument("--rescan", action="store_true", help="ignore existing reports, replay every demo page now")
    s.add_argument("--criteria", help="with --rescan: comma-separated criteria (default: all implemented)")
    s.add_argument("--lang", default=None, choices=langs)
    s.set_defaults(func=cmd_replay_check)

    s = sub.add_parser("criteria", help="list the 50 criteria and their coverage")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_criteria)

    s = sub.add_parser("eval", help="evaluate on data/testset: Baseline vs Ours (+ ablations)")
    s.add_argument("--split", default="test", choices=["test", "dev", "all"])
    s.add_argument("--systems", help="comma-separated from axe,baseline,ours,ours_no_guard,ours_no_context")
    s.add_argument("--criteria", help="comma-separated (default: criteria with an implemented check)")
    s.add_argument("--all-criteria", action="store_true", help="every criterion in the manifest")
    s.add_argument("--source", default="all", choices=["all", "generated", "act"])
    s.add_argument("--limit", type=int, help="first N cases only (smoke runs)")
    s.add_argument("--dry-run", action="store_true", help="count model questions and tokens, ask nothing")
    s.add_argument("--out", help="results directory (default: <KLAR_PROJECT_ROOT>/eval/results)")
    s.set_defaults(func=cmd_eval)

    s = sub.add_parser("health", help="print mode, model and capability probes")
    s.set_defaults(func=cmd_health)
    return ap


def main(argv: list[str] | None = None) -> int:
    _utf8_stdout()
    args = build_parser().parse_args(argv)
    _setup_logging(args.verbose)
    if getattr(args, "lang", "x") is None:
        args.lang = Settings.from_env().ui_lang
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
