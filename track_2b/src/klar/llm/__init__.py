"""LLM access: live client (with cache), replay client, capability probes."""

from __future__ import annotations

from klar.config import Settings
from klar.llm.cache import AnswerStore
from klar.llm.client import LLMBackend, LLMClient, LLMResult, RequestCounter
from klar.llm.replay import ReplayClient

__all__ = ["AnswerStore", "LLMBackend", "LLMClient", "LLMResult", "ReplayClient", "RequestCounter", "make_backend"]


def make_backend(settings: Settings, counter: RequestCounter, *, openai_client=None, capabilities=None) -> LLMBackend:
    """Replay mode → ReplayClient (no network, allow-listed models only). Otherwise
    the live client, which records validated answers into the same store when
    KLAR_RECORD=1 (default). `capabilities` is a callable returning the probed
    Capabilities (CapabilityCache.get)."""
    if settings.mode == "replay":
        store = AnswerStore(settings.replay_path, settings.llm_name, writable=False,
                            allowed_models=settings.replay_models)
        return ReplayClient(settings, store)
    store = AnswerStore(settings.replay_path, settings.llm_name, writable=settings.record)
    return LLMClient(settings, store, counter, openai_client=openai_client, capabilities=capabilities)
