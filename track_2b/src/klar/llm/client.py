"""OpenAI-compatible client for Apertus (vLLM, llama.cpp, Phoeniqs, CSCS).

Every request: temperature 0, seed 42, NO `tools`, thinking disabled through
`chat_template_kwargs` (extra_body) when the endpoint accepts it, and
`response_format: json_schema` when the endpoint supports it. Both flags come
from the start-up capability probes (llm/capabilities.py) and are never
inferred from a mid-scan error: a rejected request is a failed question
(cantTell "model unavailable"), not a silent downgrade.

Answers are parsed tolerantly, validated against the task schema and, when
invalid, the model gets ONE retry with the validation error. Tokens, latency and
the number of HTTP requests are recorded. Every request is counted by
destination class (local / swiss_cloud / external) for the sovereignty badge.
"""

from __future__ import annotations

import base64
import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Literal, Protocol
from urllib.parse import urlparse

import openai
from openai import OpenAI

from klar.config import Settings
from klar.llm.cache import AnswerStore, canonical_json, keys_for
from klar.llm.parse import parse_and_validate, strip_for_wire
from klar.models import LLMTask

if TYPE_CHECKING:
    from klar.llm.capabilities import Capabilities

log = logging.getLogger(__name__)

SEED = 42
TEMPERATURE = 0
NO_THINKING = {"chat_template_kwargs": {"enable_thinking": False}}
ErrorKind = Literal["not_recorded", "unparseable", "request_failed", "budget"]


@dataclass
class LLMResult:
    answer: dict | None
    raw: str | None = None
    error_kind: ErrorKind | None = None
    error: str | None = None
    cached: bool = False
    match: str | None = None  # exact | task | loose (cache / replay)
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    requests: int = 0  # HTTP requests actually sent for this question (incl. retries)
    model: str | None = None
    # the answer store record behind this answer (cache/replay hit, or the one just
    # recorded): provenance for the model response dataset (endpoint, original cost)
    record: dict | None = None


class RequestCounter:
    """Process-wide count of model requests by destination class."""

    CLASSES = ("local", "swiss_cloud", "external")

    def __init__(self) -> None:
        self._n = {c: 0 for c in self.CLASSES}
        self._lock = threading.Lock()

    def add(self, destination: str = "external", n: int = 1) -> None:
        with self._lock:
            self._n[destination if destination in self._n else "external"] += n

    @property
    def by_class(self) -> dict[str, int]:
        with self._lock:
            return dict(self._n)

    @property
    def value(self) -> int:
        """Requests that left the organisation (swiss_cloud + external)."""
        with self._lock:
            return self._n["swiss_cloud"] + self._n["external"]


class LLMBackend(Protocol):
    model: str

    def ask(self, task: LLMTask, *, prompt_version: str, criterion: str,
            image_root: Path | None = None) -> LLMResult: ...


def image_part(path: Path) -> dict:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{data}"}}


def build_messages(task: LLMTask, image_root: Path | None, *, plain_json: bool) -> list[dict]:
    system = task.system
    if plain_json:
        system += (
            "\n\nAnswer with ONLY one JSON object (no prose, no code fence) that matches this JSON schema:\n"
            + canonical_json(strip_for_wire(task.json_schema))
        )
    if task.images:
        root = image_root or Path(".")
        content: list[dict] | str = [{"type": "text", "text": task.user}] + [image_part(root / p) for p in task.images]
    else:
        content = task.user
    return [{"role": "system", "content": system}, {"role": "user", "content": content}]


def fold_system(messages: list[dict]) -> list[dict]:
    """For endpoints that take a single user turn (seen on a hosted Apertus 70B): the system
    prompt goes first in the user message, and a retry (the previous answer and the
    correction) follows it in that same message. Same question, same cache key."""
    if len(messages) < 2 or messages[0].get("role") != "system":
        return messages
    system, content = messages[0]["content"], messages[1]["content"]
    later = [f"Your previous answer:\n{m['content']}" if m["role"] == "assistant" else m["content"] for m in messages[2:]]
    if isinstance(content, str):
        return [{"role": "user", "content": "\n\n".join([system, content, *later])}]
    return [{"role": "user", "content": [{"type": "text", "text": system}, *content,
                                         *({"type": "text", "text": t} for t in later)]}]


def refuses_system_message(exc: Exception) -> bool:
    text = str(exc)
    return "system_message_invalid" in text or "only accepts a system message" in text


class LLMClient:
    """Live backend with the content-addressed cache in front of it."""

    def __init__(self, settings: Settings, store: AnswerStore, counter: RequestCounter,
                 *, openai_client: OpenAI | None = None, capabilities: Callable[[], "Capabilities"] | None = None):
        self.settings = settings
        self.model = settings.llm_name
        self.store = store
        self.counter = counter
        self._caps = capabilities
        self._fold_system = False  # set once the endpoint refuses a system message
        self._client = openai_client or OpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key or "local",
            timeout=settings.llm_timeout,
            max_retries=0,  # we retry ourselves so that every request is counted
        )

    # -- capability flags ----------------------------------------------------------------
    def flags(self) -> tuple[bool, bool]:
        """(json_schema, chat_template_kwargs). Unknown (no probe / unreachable) → try both."""
        if self._caps is None:
            return True, True
        caps = self._caps()
        return caps.json_schema is not False, caps.chat_template_kwargs is not False

    @property
    def schema_level(self) -> str:
        return "json_schema" if self.flags()[0] else "json_prompt"

    # -- public ----------------------------------------------------------------------
    def is_free(self, task: LLMTask, *, prompt_version: str, image_root: Path | None = None) -> bool:
        """True when ask() would answer from the cache (no endpoint request): such
        answers do not count against KLAR_MAX_LLM_CALLS."""
        return self.store.get(keys_for(self.model, prompt_version, task, image_root), exact_only=True) is not None

    def ask(self, task: LLMTask, *, prompt_version: str, criterion: str,
            image_root: Path | None = None) -> LLMResult:
        keys = keys_for(self.model, prompt_version, task, image_root)
        rec = self.store.get(keys, exact_only=True)
        if rec is not None:
            return LLMResult(answer=rec["answer"], raw=rec.get("raw"), cached=True, match="exact", record=rec,
                             model=rec.get("model", self.model))

        result = LLMResult(answer=None, model=self.model)
        t0 = time.monotonic()
        try:
            text, usage = self._complete(task, image_root, result)
            answer, errors = parse_and_validate(text, task.json_schema)
            if answer is None:
                # ONE retry, telling the model what was wrong. With temperature 0 the same schema
                # gives the same broken answer, so the retry asks for the evidence fields last.
                log.info("invalid answer for %s (%s); retrying once", criterion, "; ".join(errors[:3]))
                fix = [
                    {"role": "assistant", "content": text or ""},
                    {"role": "user", "content": "Your answer was not valid: " + "; ".join(errors[:3])
                     + ". Reply again with ONLY the corrected JSON object."},
                ]
                text, usage2 = self._complete(task, image_root, result, extra=fix,
                                              schema=evidence_last(task.json_schema))
                usage = (usage[0] + usage2[0], usage[1] + usage2[1])
                answer, errors = parse_and_validate(text, task.json_schema)
            result.raw = text
            result.tokens_in, result.tokens_out = usage
        except Exception as exc:  # network, HTTP, timeout: the scan goes on
            result.latency_ms = int((time.monotonic() - t0) * 1000)
            result.error_kind, result.error = "request_failed", _short_error(exc)
            log.warning("model request failed for %s: %s", criterion, result.error)
            return result
        result.latency_ms = int((time.monotonic() - t0) * 1000)
        if answer is None:
            result.error_kind, result.error = "unparseable", "; ".join(errors[:3])
            return result
        result.answer = answer
        if self.settings.record:
            json_schema, thinking_flag = self.flags()
            result.record = self.store.put(
                keys, prompt_version=prompt_version, criterion=criterion, answer=answer,
                raw=text, tokens_in=result.tokens_in, tokens_out=result.tokens_out,
                latency_ms=result.latency_ms, provenance={
                    "endpoint_host": urlparse(self.settings.llm_base_url or "").hostname,
                    "has_image": bool(task.images),  # replay offers vision only if true somewhere
                    "mode": self.settings.mode,
                    "decoding": {"temperature": TEMPERATURE, "seed": SEED, "max_tokens": task.max_tokens,
                                 "schema_level": "json_schema" if json_schema else "json_prompt",
                                 "thinking": "disabled" if thinking_flag else "template default"},
                })
        return result

    # -- internals -------------------------------------------------------------------
    def _complete(self, task: LLMTask, image_root: Path | None, result: LLMResult,
                  extra: list[dict] | None = None, schema: dict | None = None) -> tuple[str | None, tuple[int, int]]:
        json_schema, thinking_flag = self.flags()
        messages = build_messages(task, image_root, plain_json=not json_schema) + (extra or [])
        kwargs: dict = {
            "model": self.model,
            "messages": fold_system(messages) if self._fold_system else messages,
            "temperature": TEMPERATURE,
            "seed": SEED,
            "max_tokens": task.max_tokens,
        }
        if json_schema:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "klar_answer", "schema": strip_for_wire(schema or task.json_schema),
                                "strict": True},
            }
        if thinking_flag:
            kwargs["extra_body"] = NO_THINKING
        transient_retry_left = 1
        while True:
            result.requests += 1
            self.counter.add(self.settings.destination)
            try:
                resp = self._client.chat.completions.create(**kwargs)
            except openai.BadRequestError as exc:
                if self._fold_system or not refuses_system_message(exc):
                    raise
                # The endpoint refuses system messages: fold the instructions into the user
                # message, now and for every later question.
                log.info("endpoint refuses system messages; sending the instructions in the user message")
                self._fold_system = True
                kwargs["messages"] = fold_system(kwargs["messages"])
                continue
            except (openai.APIConnectionError, openai.APITimeoutError, openai.RateLimitError,
                    openai.InternalServerError):
                if transient_retry_left <= 0:
                    raise
                transient_retry_left -= 1
                time.sleep(2.0)
                continue
            choice = resp.choices[0] if resp.choices else None
            text = choice.message.content if choice and choice.message else None
            usage = resp.usage
            return text, ((usage.prompt_tokens or 0) if usage else 0, (usage.completion_tokens or 0) if usage else 0)


def evidence_last(schema: dict) -> dict:
    """The retry schema: `quote` and `reason` moved to the end. In evidence-first order the 8B
    model sometimes takes `reason` for the last field, writes `.}` inside the string and stops."""
    props = schema.get("properties") or {}
    tail = {k: props[k] for k in ("quote", "reason") if k in props}
    if not tail:
        return schema
    ordered = {**{k: v for k, v in props.items() if k not in tail}, **tail}
    return {**schema, "properties": ordered, "required": list(ordered)}


def _short_error(exc: Exception) -> str:
    name = type(exc).__name__
    msg = str(exc).strip().splitlines()[0] if str(exc).strip() else ""
    return f"{name}: {msg[:160]}" if msg else name
