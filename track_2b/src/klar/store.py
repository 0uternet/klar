"""SQLite persistence (stdlib) for scans and the human review status of findings.

The whole Scan is stored as JSON (one row per scan); review decisions live in
their own table so that a PATCH never rewrites a large document.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from klar.models import Finding, Scan

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    id         TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    url        TEXT NOT NULL,
    state      TEXT NOT NULL,
    data       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reviews (
    finding_id TEXT PRIMARY KEY,
    scan_id    TEXT NOT NULL,
    status     TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS reviews_scan ON reviews(scan_id);
"""


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(self.path), check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.executescript(SCHEMA)
        self._db.commit()

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def save_scan(self, scan: Scan) -> None:
        data = scan.model_dump_json()
        with self._lock:
            self._db.execute(
                "INSERT INTO scans(id, created_at, url, state, data) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET state=excluded.state, data=excluded.data",
                (scan.id, scan.created_at.isoformat(), scan.url, scan.state, data),
            )
            self._db.commit()

    def get_scan(self, scan_id: str) -> Scan | None:
        with self._lock:
            row = self._db.execute("SELECT data FROM scans WHERE id = ?", (scan_id,)).fetchone()
            reviews = dict(self._db.execute("SELECT finding_id, status FROM reviews WHERE scan_id = ?", (scan_id,)).fetchall())
        if row is None:
            return None
        scan = Scan.model_validate_json(row[0])
        return apply_reviews(scan, reviews)

    def list_scans(self, limit: int = 50) -> list[dict]:
        """Recent scans for the home page: id, created_at, url, state, page_title and the
        number of findings still to review (reviews applied), without the findings."""
        with self._lock:
            rows = self._db.execute(
                "SELECT id, created_at, url, state, data FROM scans ORDER BY created_at DESC LIMIT ?",
                (limit,)).fetchall()
            reviewed = dict(self._db.execute(
                "SELECT scan_id, COUNT(*) FROM reviews WHERE status != 'to_review' GROUP BY scan_id").fetchall())
        out = []
        for scan_id, created_at, url, state, data in rows:
            try:
                doc = json.loads(data)
            except ValueError:
                doc = {}
            stats = doc.get("stats") or {}
            total = len(doc.get("findings") or [])
            out.append({"id": scan_id, "created_at": created_at, "url": url, "state": state,
                        "page_title": stats.get("page_title"),
                        "to_review": max(0, total - reviewed.get(scan_id, 0))})
        return out

    def reviews_for(self, scan_id: str) -> dict[str, str]:
        with self._lock:
            return dict(self._db.execute("SELECT finding_id, status FROM reviews WHERE scan_id = ?", (scan_id,)).fetchall())

    def set_status(self, finding_id: str, status: str) -> Finding | None:
        """Finding ids are '<scan_id>-<candidate_id>' (unique across scans)."""
        scan_id = finding_id.split("-", 1)[0]
        scan = self.get_scan(scan_id)
        if scan is None:
            return None
        finding = next((f for f in scan.findings if f.id == finding_id), None)
        if finding is None:
            return None
        self.write_review(finding_id, scan_id, status)
        return finding.model_copy(update={"status": status})

    def write_review(self, finding_id: str, scan_id: str, status: str) -> None:
        with self._lock:
            self._db.execute(
                "INSERT INTO reviews(finding_id, scan_id, status, updated_at) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(finding_id) DO UPDATE SET status=excluded.status, updated_at=excluded.updated_at",
                (finding_id, scan_id, status, datetime.now(timezone.utc).isoformat()),
            )
            self._db.commit()


def apply_reviews(scan: Scan, reviews: dict[str, str]) -> Scan:
    if reviews:
        scan.findings = [f.model_copy(update={"status": reviews[f.id]}) if f.id in reviews else f
                         for f in scan.findings]
    if scan.stats:
        for k in ("to_review", "accepted", "rejected"):
            scan.stats[k] = sum(1 for f in scan.findings if f.status == k)
    return scan
