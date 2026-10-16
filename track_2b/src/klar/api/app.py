"""FastAPI app. One container, one port: /api/*, the built Vue UI at / (from
api/static) and the bundled demo site at /demo/. API contract: klar/models.py.

    klar serve                      (127.0.0.1:8080 by default)

Security: Host-header allow-list (DNS rebinding), URL policy on every scan target
(klar/netpolicy.py), size and queue limits, strict security headers on UI and API
responses, no third-party assets (the OpenAPI HTML pages are disabled: they load
a CDN; the schema stays at /api/openapi.json).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from klar import __version__
from klar.api.manager import NotRunning, QueueFull, Services
from klar.checks import registry
from klar.config import Settings
from klar.models import CriterionInfo, Finding, FindingPatch, Health, Scan, ScanCreated, ScanRequest
from klar.netpolicy import origin_of
from klar.report import FORMATS, render

log = logging.getLogger(__name__)

SCAN_ID = re.compile(r"^[0-9a-f]{10}$")
FILE_NAME = re.compile(r"^[a-z0-9_-]{1,64}\.png$")

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
        "connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; "
        "form-action 'self'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}

PLACEHOLDER = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Klar.</title>
<style>:root{--bg:#FAFAF7;--ink:#0F1115;--muted:#565B66;--red:#D0021B;--blue:#1F4FD8}
@media (prefers-color-scheme:dark){:root{--bg:#0B0C0F;--ink:#F2F1EC;--muted:#A3A8B3;--red:#FF4D4F;--blue:#7FA2FF}}
body{background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif;max-width:720px;margin:0 auto;padding:48px 16px}
h1{font-size:48px;letter-spacing:-.02em;margin:0}h1 span{display:inline-block;width:.18em;height:.18em;background:var(--red)}
p{color:var(--muted)}a{color:var(--blue)}a:focus-visible{outline:2px solid var(--blue);outline-offset:2px}</style></head>
<body><main><h1>Klar<span aria-hidden="true"></span></h1>
<p>Meaning checks for an accessible Swiss web. The API is running; the web interface has not been built yet
(<code>src/web</code> builds into <code>src/klar/api/static</code>).</p>
<ul><li><a href="/api/health">/api/health</a></li><li><a href="/api/criteria">/api/criteria</a></li>
<li><a href="/demo/">/demo/</a></li><li><a href="/api/openapi.json">/api/openapi.json</a></li></ul></main></body></html>"""

DEMO_MISSING = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Demo site not found</title></head>
<body><main><h1>Demo site not found</h1><p>The bundled demo site (data/demo-site) is not installed.</p></main></body></html>"""


class SPAStaticFiles(StaticFiles):
    """Serve index.html for unknown paths (client-side routing)."""

    async def get_response(self, path: str, scope):  # type: ignore[override]
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404 and not path.startswith(("api", "demo")):
                return await super().get_response("index.html", scope)
            raise


def host_name(header: str) -> str:
    """Host header → bare host name, lower case, without port or IPv6 brackets."""
    h = header.strip().lower()
    if h.startswith("["):
        return h[1:h.find("]")] if "]" in h else h[1:]
    return h.rsplit(":", 1)[0] if h.count(":") == 1 else h


def is_bundled_demo(url: str, settings: Settings) -> bool:
    """Forms are submitted (interaction probe) only on the app's own /demo/ (host AND port)."""
    u = urlparse(url)
    return any(origin_of(url) == o and (u.path or "/").startswith(prefix) for o, prefix in settings.demo_origins())


def health_of(svc: Services) -> Health:
    settings = svc.settings
    caps = svc.caps.get(wait=False)
    by_class = svc.counter.by_class
    provider = settings.provider.lower() if settings.provider else None
    if provider is None and settings.mode == "local" and caps.owned_by in ("vllm", "llamacpp"):
        provider = caps.owned_by
    replay_models = replay_recorded = None
    if settings.mode == "replay":
        summary = svc.llm.store.summary()  # type: ignore[attr-defined]
        replay_models = summary["models"]
        replay_recorded = {k: summary[k] for k in ("from", "to", "hosts", "records")}
    return Health(
        mode=settings.mode, model=svc.llm.model, replay_models=replay_models,
        base_url_host=settings.base_url_host, provider=provider, vision=caps.vision,
        vision_source=caps.source if caps.source in ("pending", "probe", "override", "replay", "error") else "probe",
        json_schema=bool(caps.json_schema), chat_template_kwargs=bool(caps.chat_template_kwargs),
        version=__version__, config_error=settings.config_error, ai_requests=by_class,
        llm_reachable=caps.reachable, llm_error=caps.error,
        external_ai_requests=by_class["swiss_cloud"] + by_class["external"], replay_recorded=replay_recorded,
    )


def create_app(settings: Settings | None = None, *, services: Services | None = None, probe: bool = True) -> FastAPI:
    settings = settings or Settings.from_env()
    svc = services or Services(settings)
    if settings.config_error:
        log.error("configuration error: %s", settings.config_error)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if probe:
            svc.caps.start_background()
        yield
        svc.close()

    app = FastAPI(title="Klar.", version=__version__, lifespan=lifespan, docs_url=None, redoc_url=None,
                  openapi_url="/api/openapi.json",
                  description="WCAG 2.1 AA pre-checks with Apertus. Does not certify conformance.")
    app.state.services = svc
    allowed_hosts = {h.lower().strip("[]") for h in settings.allowed_hosts}

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        # Host allow-list (DNS-rebinding protection). IPv6-safe: "[::1]:8080" → "::1".
        if host_name(request.headers.get("host", "")) not in allowed_hosts:
            return JSONResponse({"detail": "invalid host header"}, status_code=400)
        response = await call_next(request)
        if not request.url.path.startswith("/demo"):  # the demo site is audited content, not our UI
            for k, v in SECURITY_HEADERS.items():
                response.headers.setdefault(k, v)
        return response

    origins = [o.strip() for o in os.environ.get("KLAR_CORS_ORIGINS", "").split(",") if o.strip()]
    if origins:  # only for UI development (vite dev server); production is same-origin
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"], allow_headers=["*"])

    # ---- API --------------------------------------------------------------------------
    @app.get("/api/health", response_model=Health)
    def health() -> Health:
        return health_of(svc)

    @app.get("/api/criteria", response_model=list[CriterionInfo])
    def criteria() -> list[CriterionInfo]:
        return registry.criteria_info()

    @app.post("/api/scans", response_model=ScanCreated, status_code=201)
    def create_scan(req: ScanRequest) -> ScanCreated:
        if req.html is not None and len(req.html.encode("utf-8")) > settings.max_html_bytes:
            raise HTTPException(413, f"html is larger than {settings.max_html_bytes} bytes")
        form_origins: tuple[str, ...] = ()
        allow_forms = False
        if req.url:
            verdict = settings.net_policy().check(req.url)
            if not verdict.ok:
                raise HTTPException(422, f"url not allowed: {verdict.reason}")
            if is_bundled_demo(req.url, settings):
                allow_forms, form_origins = True, (origin_of(req.url),)
        try:
            scan = svc.scans.submit(req, allow_form_submit=allow_forms, form_origins=form_origins)
        except QueueFull as exc:
            raise HTTPException(429, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        return ScanCreated(id=scan.id)

    @app.get("/api/scans")
    def list_scans(limit: int = Query(50, ge=1, le=500)) -> list[dict]:
        return svc.store.list_scans(limit)

    @app.get("/api/scans/{scan_id}", response_model=Scan)
    def get_scan(scan_id: str) -> Scan:
        scan = svc.scans.get(scan_id) if SCAN_ID.match(scan_id) else None
        if scan is None:
            raise HTTPException(404, "scan not found")
        return scan

    def control(scan_id: str, action: str) -> dict:
        if not SCAN_ID.match(scan_id):
            raise HTTPException(404, "scan not found")
        try:
            return svc.scans.control(scan_id, action)
        except NotRunning as exc:
            if svc.scans.get(scan_id) is None:
                raise HTTPException(404, "scan not found") from exc
            raise HTTPException(409, "the scan is not running") from exc

    @app.post("/api/scans/{scan_id}/pause")
    def pause_scan(scan_id: str) -> dict:
        """Pause at the next step, check or model question. The paused time does not count
        against KLAR_SCAN_TIMEOUT."""
        return control(scan_id, "pause")

    @app.post("/api/scans/{scan_id}/resume")
    def resume_scan(scan_id: str) -> dict:
        return control(scan_id, "resume")

    @app.post("/api/scans/{scan_id}/stop")
    def stop_scan(scan_id: str) -> dict:
        """Stop at the next step, check or model question; the scan ends "done" with the
        findings so far, and the elements not judged are noted "stopped"."""
        return control(scan_id, "stop")

    @app.get("/api/scans/{scan_id}/files/{name}")
    def scan_file(scan_id: str, name: str) -> FileResponse:
        if not SCAN_ID.match(scan_id) or not FILE_NAME.match(name):
            raise HTTPException(404, "not found")
        base = (settings.scans_path / scan_id / "crops").resolve()
        path = (base / name).resolve()
        if path.parent != base or not path.is_file():
            raise HTTPException(404, "not found")
        return FileResponse(path, media_type="image/png")

    @app.get("/api/scans/{scan_id}/events")
    async def scan_events(scan_id: str, request: Request) -> StreamingResponse:
        bus = svc.scans.bus(scan_id) if SCAN_ID.match(scan_id) else None
        stored = None if bus else (svc.scans.get(scan_id) if SCAN_ID.match(scan_id) else None)
        if bus is None and stored is None:
            raise HTTPException(404, "scan not found")
        try:
            start = max(0, int(request.headers.get("last-event-id") or 0))
        except ValueError:
            start = 0

        def sse(n: int, event: str, data: dict) -> str:
            return f"id: {n}\nevent: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

        async def stream():
            if bus is None:  # finished before this process started: replay from the store
                events = [("progress", e) for e in stored.progress]
                events += [("finding", f.model_dump(mode="json")) for f in stored.findings]
                events.append(("done", {"scan_id": stored.id, "state": stored.state}))
                for n, (event, data) in enumerate(events, 1):
                    if n > start:
                        yield sse(n, event, data)
                return
            index = start
            while True:
                if await request.is_disconnected():
                    return
                events, closed = await asyncio.to_thread(bus.wait, index, 15.0)
                for event, data in events:
                    index += 1
                    yield sse(index, event, data)
                if closed:  # "done" was published; nothing follows it
                    return
                if not events:
                    yield ": keep-alive\n\n"

        return StreamingResponse(stream(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.patch("/api/findings/{finding_id}", response_model=Finding)
    def patch_finding(finding_id: str, patch: FindingPatch) -> Finding:
        f = svc.scans.set_status(finding_id, patch.status)
        if f is None:
            raise HTTPException(404, "finding not found")
        return f

    @app.get("/api/scans/{scan_id}/export")
    def export(scan_id: str, format: str = Query("json")) -> Response:
        if format not in FORMATS:
            raise HTTPException(422, f"format must be one of {', '.join(FORMATS)}")
        scan = svc.scans.get(scan_id) if SCAN_ID.match(scan_id) else None
        if scan is None:
            raise HTTPException(404, "scan not found")
        media, ext = FORMATS[format]
        body = render(scan, format, assets_dir=settings.scans_path / scan.id)
        return Response(body, media_type=media,
                        headers={"Content-Disposition": f'attachment; filename="klar-{scan.id}.{ext}"'})

    @app.get("/api/{rest:path}", include_in_schema=False)
    def api_not_found(rest: str) -> JSONResponse:
        return JSONResponse({"detail": "not found"}, status_code=404)

    # ---- demo site + UI ------------------------------------------------------------------
    demo = settings.demo_path
    if demo.is_dir():
        app.mount("/demo", StaticFiles(directory=demo, html=True), name="demo")
    else:
        @app.get("/demo", include_in_schema=False)
        @app.get("/demo/{rest:path}", include_in_schema=False)
        def demo_missing(rest: str = "") -> HTMLResponse:
            return HTMLResponse(DEMO_MISSING, status_code=404)

    static = settings.static_path
    if (static / "index.html").is_file():
        app.mount("/", SPAStaticFiles(directory=static, html=True), name="ui")
    else:
        @app.get("/", include_in_schema=False)
        def placeholder() -> HTMLResponse:
            return HTMLResponse(PLACEHOLDER)

    return app


def __getattr__(name: str):
    """`uvicorn klar.api.app:app` builds the app lazily from the environment."""
    if name == "app":
        return create_app()
    raise AttributeError(name)
