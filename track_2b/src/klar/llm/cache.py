"""Content-addressed answer store: cache in live mode, replay store in replay mode.

Key   = sha256(model + "\\n" + prompt_version + "\\n" + canonical task JSON)
File  = <replay_dir>/<model-slug>.jsonl, append-only, one JSON object per line:

    {"key", "task_key", "loose_key", "model", "prompt_version", "criterion",
     "answer", "raw", "tokens_in", "tokens_out", "latency_ms", "created_at",
     "endpoint_host", "mode", "has_image", "decoding": {"temperature", "seed", "max_tokens",
     "schema_level", "thinking"}, "klar_version"}

Images enter the canonical task as sha256 of their bytes (never their path).
Two extra keys make the DEMO replay robust when the exact key misses:
  task_key  = same hash without the model,
  loose_key = without model AND without image bytes (screenshots rendered on a
              different machine differ by a few anti-aliased pixels).
Live mode and the evaluation trust the exact key only. Replay serves only
records of allow-listed models (KLAR_REPLAY_MODELS, Apertus by default), so a
comparison model's answers can never be replayed as if they were Apertus'.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import logging
import re
import threading
from datetime import datetime, timezone
from pathlib import Path

from klar.models import LLMTask

log = logging.getLogger(__name__)


def model_slug(model: str) -> str:
    return re.sub(r"[^a-z0-9.]+", "-", model.lower()).strip("-") or "model"


def canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def image_digest(path: Path) -> str:
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return "missing:" + path.name


def task_fingerprint(task: LLMTask, image_root: Path | None, *, with_images: bool = True) -> dict:
    wire = task.wire()
    root = image_root or Path(".")
    if with_images:
        wire["images"] = [image_digest(root / p) for p in task.images]
    else:
        wire["images"] = len(task.images)
    return wire


def keys_for(model: str, prompt_version: str, task: LLMTask, image_root: Path | None) -> dict[str, str]:
    fp = canonical_json(task_fingerprint(task, image_root))
    loose = canonical_json(task_fingerprint(task, image_root, with_images=False))
    return {
        "key": _sha(f"{model}\n{prompt_version}\n{fp}"),
        "task_key": _sha(f"{prompt_version}\n{fp}"),
        "loose_key": _sha(f"{prompt_version}\n{loose}"),
    }


def model_allowed(model: str | None, patterns: tuple[str, ...] | None) -> bool:
    if patterns is None:
        return True
    return bool(model) and any(fnmatch.fnmatchcase(model, p) for p in patterns)


class AnswerStore:
    """Thread-safe. Loads every *.jsonl in the directory once (records of models
    outside `allowed_models` are ignored); appends to the model's own file. A write
    failure (read-only volume) only logs a warning: answers stay in memory."""

    def __init__(self, directory: Path, model: str, *, writable: bool = True,
                 allowed_models: tuple[str, ...] | None = None):
        self.directory = Path(directory)
        self.model = model
        self.writable = writable
        self.allowed_models = allowed_models
        self.path = self.directory / f"{model_slug(model)}.jsonl"
        self._lock = threading.Lock()
        self._by: dict[str, dict[str, dict]] = {"key": {}, "task_key": {}, "loose_key": {}}
        self._records: list[dict] = []
        self.ignored_models: set[str] = set()
        self._load()

    def _load(self) -> None:
        if not self.directory.is_dir():
            return
        files = sorted(self.directory.glob("*.jsonl"))
        files.sort(key=lambda p: p == self.path)  # our own model's file last: its records win
        for f in files:
            try:
                lines = f.read_text(encoding="utf-8").splitlines()
            except OSError as exc:
                log.warning("cannot read %s: %s", f, exc)
                continue
            for n, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    log.warning("%s:%d is not valid JSON; skipped", f.name, n)
                    continue
                if not model_allowed(rec.get("model"), self.allowed_models):
                    self.ignored_models.add(str(rec.get("model")))
                    continue
                self._index(rec)

    def _index(self, rec: dict) -> None:
        # The first answer recorded for a key wins. A later run that asks the same question
        # again (the -context ablation does, when an element has no computed context) may get a
        # different answer from the server; it is kept in the file but never replaces the first.
        self._records.append(rec)
        for kind in ("key", "task_key", "loose_key"):
            k = rec.get(kind)
            if k:
                self._by[kind].setdefault(k, rec)

    def __len__(self) -> int:
        return len(self._by["key"])

    def lookup(self, keys: dict[str, str], *, exact_only: bool = True) -> tuple[dict | None, str | None]:
        """(record, match) with match in {"exact", "task", "loose"} or (None, None)."""
        with self._lock:
            rec = self._by["key"].get(keys["key"])
            if rec is not None:
                return rec, "exact"
            if exact_only:
                return None, None
            rec = self._by["task_key"].get(keys["task_key"])
            if rec is not None:
                return rec, "task"
            rec = self._by["loose_key"].get(keys["loose_key"])
            return (rec, "loose") if rec is not None else (None, None)

    def get(self, keys: dict[str, str], *, exact_only: bool = True) -> dict | None:
        return self.lookup(keys, exact_only=exact_only)[0]

    def summary(self) -> dict:
        """What this store would replay: models, recording dates, endpoint hosts."""
        with self._lock:
            recs = list(self._records)
        dates = sorted(r.get("created_at") for r in recs if r.get("created_at"))
        return {
            "models": sorted({r.get("model") for r in recs if r.get("model")}),
            "from": dates[0] if dates else None,
            "to": dates[-1] if dates else None,
            "hosts": sorted({r.get("endpoint_host") for r in recs if r.get("endpoint_host")}),
            "records": len(recs),
            "criteria": sorted({r.get("criterion") for r in recs if r.get("criterion")}),
            "has_image": any(r.get("has_image") for r in recs),
        }

    def put(self, keys: dict[str, str], *, prompt_version: str, criterion: str, answer: dict,
            raw: str | None, tokens_in: int, tokens_out: int, latency_ms: int,
            provenance: dict | None = None) -> dict:
        from klar import __version__

        rec = {
            **keys,
            "model": self.model,
            "prompt_version": prompt_version,
            "criterion": criterion,
            "answer": answer,
            "raw": raw,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "latency_ms": latency_ms,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "klar_version": __version__,
            **(provenance or {}),
        }
        with self._lock:
            self._index(rec)
            if self.writable:
                try:
                    self.directory.mkdir(parents=True, exist_ok=True)
                    with self.path.open("a", encoding="utf-8", newline="\n") as fh:
                        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                except OSError as exc:
                    log.warning("cannot append to %s (%s); answer kept in memory only", self.path, exc)
        return rec
