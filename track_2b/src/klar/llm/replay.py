"""Replay backend: answers come from the recorded JSONL store, never from the network.

Used when KLAR_REPLAY=1 or LLM_BASE_URL is unset. A miss yields `cantTell` with
the note "not recorded" (the pipeline maps error_kind). Only records of
allow-listed models are served (KLAR_REPLAY_MODELS, default Apertus v1.5).
With KLAR_REPLAY_EXACT=1 (forced by `klar eval` and `klar replay-check`) only
exact keys count; otherwise the demo may fall back to model-independent keys,
and every such approximate hit is counted (stats.replay_loose_hits).

How recordings are made: `klar record` (or any live scan with KLAR_RECORD=1)
appends every validated answer, with its provenance, to
<KLAR_REPLAY_DIR>/<model-slug>.jsonl (data/replay/ by default).
"""

from __future__ import annotations

from pathlib import Path

from klar.config import Settings
from klar.llm.cache import AnswerStore, keys_for
from klar.llm.client import LLMResult
from klar.llm.parse import coerce, validate
from klar.models import LLMTask


class ReplayClient:
    def __init__(self, settings: Settings, store: AnswerStore):
        self.settings = settings
        self.store = store
        self.exact_only = settings.replay_exact
        summary = store.summary()
        self.recorded_models: list[str] = summary["models"]
        # The model whose answers are replayed (keys are computed with it). With
        # several recorded models, LLM_NAME picks one if it was recorded.
        if settings.llm_name in self.recorded_models or not self.recorded_models:
            self.model = settings.llm_name
        else:
            self.model = self.recorded_models[0]

    def is_free(self, task: LLMTask, *, prompt_version: str, image_root: Path | None = None) -> bool:
        """A recorded answer costs nothing, like a cache hit in a live run. A question
        that was not recorded counts like a cache miss: within KLAR_MAX_LLM_CALLS it ends
        as a `not_recorded` note (so replay-check reports the gap), beyond it as `budget`."""
        keys = keys_for(self.model, prompt_version, task, image_root)
        return self.store.lookup(keys, exact_only=self.exact_only)[0] is not None

    def ask(self, task: LLMTask, *, prompt_version: str, criterion: str,
            image_root: Path | None = None) -> LLMResult:
        keys = keys_for(self.model, prompt_version, task, image_root)
        rec, match = self.store.lookup(keys, exact_only=self.exact_only)
        if rec is None:
            return LLMResult(answer=None, error_kind="not_recorded", error="not recorded", model=self.model)
        answer = coerce(dict(rec.get("answer") or {}), task.json_schema)
        if validate(answer, task.json_schema):
            return LLMResult(answer=None, error_kind="not_recorded",
                             error="recorded answer no longer matches the schema",
                             model=rec.get("model", self.model), record=rec)
        return LLMResult(answer=answer, raw=rec.get("raw"), cached=True, match=match,
                         model=rec.get("model", self.model), record=rec)
