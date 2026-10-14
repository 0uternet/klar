"""Process-wide services and the background scan manager used by the API."""

from __future__ import annotations

import logging
import threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

from klar.config import Settings
from klar.llm import make_backend
from klar.llm.capabilities import CapabilityCache
from klar.llm.client import RequestCounter
from klar.models import Finding, Scan, ScanRequest
from klar.pipeline import ScanJob, count_outcomes, new_scan, resolve_criteria, run_scan
from klar.store import Store, apply_reviews

log = logging.getLogger(__name__)


class QueueFull(RuntimeError):
    pass


class EventBus:
    """Append-only event log of one scan. Event ids are 1-based positions, so a
    client reconnecting with Last-Event-ID: n resumes at event n+1 (no duplicates)."""

    def __init__(self) -> None:
        self._events: list[tuple[str, dict]] = []
        self._cond = threading.Condition()
        self.closed = False

    def publish(self, event: str, data: dict) -> None:
        with self._cond:
            self._events.append((event, data))
            if event == "done":
                self.closed = True
            self._cond.notify_all()

    def wait(self, index: int, timeout: float) -> tuple[list[tuple[str, dict]], bool]:
        """Events after position `index` (0 = from the start)."""
        with self._cond:
            if len(self._events) <= index and not self.closed:
                self._cond.wait(timeout)
            return self._events[index:], self.closed


class Services:
    def __init__(self, settings: Settings, *, openai_client=None, max_workers: int = 2):
        self.settings = settings
        self.counter = RequestCounter()
        self.caps = CapabilityCache(settings, self.counter, openai_client=openai_client)
        self.llm = make_backend(settings, self.counter, openai_client=openai_client, capabilities=self.caps.get)
        self.store = Store(settings.db_path)
        self.scans = ScanManager(self, max_workers=max_workers)

    def close(self) -> None:
        self.scans.shutdown()
        self.store.close()


class ScanManager:
    KEEP_BUSES = 100

    def __init__(self, services: Services, *, max_workers: int = 2):
        self.s = services
        self.live: dict[str, Scan] = {}
        self.buses: OrderedDict[str, EventBus] = OrderedDict()
        self._lock = threading.Lock()
        self._pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="klar-scan")

    def submit(self, req: ScanRequest, *, allow_form_submit: bool = False, form_origins: tuple[str, ...] = ()) -> Scan:
        if bool(req.url) == bool(req.html):
            raise ValueError("give exactly one of url or html")
        job = ScanJob(url=req.url, html=req.html, ui_lang=req.ui_lang, criteria=req.criteria,
                      allow_form_submit=allow_form_submit, form_origins=form_origins)
        resolve_criteria(job.criteria)  # raises ValueError on unknown criteria
        with self._lock:
            if len(self.live) >= self.s.settings.max_queue:
                raise QueueFull(f"{len(self.live)} scans queued or running (KLAR_QUEUE_MAX={self.s.settings.max_queue})")
            scan = new_scan(self.s.settings, job, model=self.s.llm.model)
            self.live[scan.id] = scan
            bus = EventBus()
            self.buses[scan.id] = bus
            while len(self.buses) > self.KEEP_BUSES:
                self.buses.popitem(last=False)
        self.s.store.save_scan(scan)
        self._pool.submit(self._run, scan, job, bus)
        return scan

    def _run(self, scan: Scan, job: ScanJob, bus: EventBus) -> None:
        def emit(event: str, data: dict) -> None:
            bus.publish(event, data)
            if event == "progress" and data.get("state") in ("done", "error"):
                try:
                    self.s.store.save_scan(scan)
                except Exception:
                    log.exception("could not persist scan %s", scan.id)

        try:
            vision = self.s.caps.get().vision
            run_scan(scan, job, settings=self.s.settings, llm=self.s.llm, vision=vision,
                     counter=self.s.counter, emit=emit)
        except Exception as exc:  # run_scan handles its own errors; this is a last resort
            log.exception("scan %s crashed", scan.id)
            scan.state = "error"
            scan.stats["error"] = str(exc)
            if not bus.closed:
                bus.publish("done", {"scan_id": scan.id, "state": "error"})
        finally:
            self.s.store.save_scan(scan)
            with self._lock:
                self.live.pop(scan.id, None)

    def get(self, scan_id: str) -> Scan | None:
        with self._lock:
            live = self.live.get(scan_id)
        if live is not None:
            for _ in range(3):  # the worker may be appending while we copy
                try:
                    snap = live.model_copy(deep=True)
                    snap = apply_reviews(snap, self.s.store.reviews_for(scan_id))
                    if snap.stats:
                        count_outcomes(snap)
                    return snap
                except RuntimeError:
                    continue
        return self.s.store.get_scan(scan_id)

    def bus(self, scan_id: str) -> EventBus | None:
        with self._lock:
            return self.buses.get(scan_id)

    def set_status(self, finding_id: str, status: str) -> Finding | None:
        scan_id = finding_id.split("-", 1)[0]
        with self._lock:
            live = self.live.get(scan_id)
        if live is not None:
            f = next((x for x in list(live.findings) if x.id == finding_id), None)
            if f is not None:
                self.s.store.write_review(finding_id, scan_id, status)
                return f.model_copy(update={"status": status})
        return self.s.store.set_status(finding_id, status)

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)
