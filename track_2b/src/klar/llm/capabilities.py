"""Backend capabilities, probed once per process, each one INDEPENDENTLY:

  chat_template_kwargs  tiny request with {"enable_thinking": false}: 400/422 → False
  json_schema           tiny request with response_format json_schema: 400/422 → False
  vision                GET /models first (llama.cpp and some proxies expose
                        `input_modalities`; text-only → False without an image);
                        then a tiny red PNG: the answer must say red/rot/rouge/rosso
                        (some proxies drop images silently and answer anyway).

The client uses these flags; it never infers them from unrelated mid-scan errors.
KLAR_VISION=0/1 skips the vision probe. Replay mode probes nothing: vision is
True only when the store holds recorded answers of a vision check. An unreachable endpoint gives
`None` (unknown) for the request-format flags and vision=False.
"""

from __future__ import annotations

import base64
import logging
import re
import struct
import threading
import zlib
from dataclasses import dataclass

import httpx
import openai
from openai import OpenAI

from klar.config import Settings
from klar.llm.client import NO_THINKING, SEED, RequestCounter, _short_error

log = logging.getLogger(__name__)

RED = re.compile(r"\b(red|rot|rouge|rosso|rossa)\b", re.IGNORECASE)


@dataclass(frozen=True)
class Capabilities:
    vision: bool
    source: str  # pending | probe | override | replay | error  (contract vision_source)
    detail: str = ""
    json_schema: bool | None = None
    chat_template_kwargs: bool | None = None
    owned_by: str | None = None  # from GET /models: "vllm", "llamacpp"… (a hint, not a proof)
    reachable: bool | None = None  # None: replay mode / not probed yet
    error: str | None = None  # why the endpoint could not be reached

    @property
    def schema_level(self) -> str:
        return "json_schema" if self.json_schema else "json_prompt"


PENDING = Capabilities(False, "pending")


def tiny_png(w: int = 16, h: int = 16, rgb: tuple[int, int, int] = (208, 2, 27)) -> bytes:
    """A solid red square (the Klar. symbol), built without Pillow."""
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def models_info(settings: Settings, counter: RequestCounter) -> tuple[list[str] | None, str | None]:
    """(input_modalities, owned_by) of our model from GET /models; None when not declared."""
    url = (settings.llm_base_url or "").rstrip("/") + "/models"
    counter.add(settings.destination)
    try:
        r = httpx.get(url, headers={"Authorization": f"Bearer {settings.llm_api_key}"}, timeout=10)
        r.raise_for_status()
        models = r.json().get("data") or []
    except Exception as exc:
        log.info("GET /models failed (%s); falling back to the image probe", _short_error(exc))
        return None, None
    entry = next((m for m in models if isinstance(m, dict) and m.get("id") == settings.llm_name),
                 models[0] if len(models) == 1 else None)
    if not isinstance(entry, dict):
        return None, None
    owned_by = str(entry.get("owned_by") or "").lower() or None
    for holder in (entry, entry.get("architecture") or {}, entry.get("meta") or {}):
        if not isinstance(holder, dict):
            continue
        mods = holder.get("input_modalities") or holder.get("modalities")
        if isinstance(mods, list) and mods:
            return [str(m).lower() for m in mods], owned_by
    return None, owned_by


_LAST_ERROR: dict[str, str] = {}


def _accepts(client: OpenAI, counter: RequestCounter, settings: Settings, **kwargs) -> bool | None:
    """True = accepted, False = rejected with 400/422, None = endpoint unreachable/other."""
    counter.add(settings.destination)
    try:
        client.chat.completions.create(
            model=settings.llm_name, messages=[{"role": "user", "content": 'Reply with {"ok": true}.'}],
            temperature=0, seed=SEED, max_tokens=8, **kwargs)
        return True
    except (openai.BadRequestError, openai.UnprocessableEntityError) as exc:
        log.info("endpoint rejected %s: %s", list(kwargs), _short_error(exc))
        return False
    except Exception as exc:
        log.warning("capability probe failed: %s", _short_error(exc))
        _LAST_ERROR[settings.llm_base_url or ""] = _short_error(exc)
        return None


def probe_capabilities(settings: Settings, counter: RequestCounter, *,
                       openai_client: OpenAI | None = None) -> Capabilities:
    if settings.mode == "replay":
        if settings.vision_override is not None:
            return Capabilities(settings.vision_override, "override")
        # Vision is replayable only if at least one recorded request really carried an image
        # (`has_image`, stored at record time). A text-only endpoint records none: image
        # candidates then say "vision backend required" instead of missing their recordings.
        from klar.llm.cache import AnswerStore

        has = AnswerStore(settings.replay_path, settings.llm_name, writable=False,
                          allowed_models=settings.replay_models).summary()["has_image"]
        return Capabilities(has, "replay", "recorded vision answers" if has else "no recorded vision answers")
    client = openai_client or OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key or "local",
                                     timeout=min(settings.llm_timeout, 120), max_retries=0)
    ctk = _accepts(client, counter, settings, extra_body=NO_THINKING)
    schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"],
              "additionalProperties": False}
    js = _accepts(client, counter, settings,
                  response_format={"type": "json_schema",
                                   "json_schema": {"name": "probe", "schema": schema, "strict": True}},
                  **({"extra_body": NO_THINKING} if ctk else {}))
    mods, owned_by = models_info(settings, counter)
    reachable = not (ctk is None and js is None)  # both tiny requests failed outright → unreachable
    flags = {"json_schema": js, "chat_template_kwargs": ctk, "owned_by": owned_by, "reachable": reachable,
             "error": None if reachable else _LAST_ERROR.get(settings.llm_base_url or "", "unreachable")}
    if not reachable:  # do not report "no vision" when the model is simply not there
        vision = settings.vision_override if settings.vision_override is not None else False
        return Capabilities(vision, "override" if settings.vision_override is not None else "error",
                            "endpoint unreachable", **flags)

    if settings.vision_override is not None:
        return Capabilities(settings.vision_override, "override", **flags)
    if mods is not None and "image" not in mods:
        return Capabilities(False, "probe", f"GET /models declares input_modalities={mods}", **flags)
    png = base64.b64encode(tiny_png()).decode("ascii")
    counter.add(settings.destination)
    try:
        resp = client.chat.completions.create(
            model=settings.llm_name,
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "What colour is this square? Answer with one word."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{png}"}},
            ]}],
            temperature=0, seed=SEED, max_tokens=5, **({"extra_body": NO_THINKING} if ctk else {}),
        )
    except Exception as exc:
        return Capabilities(False, "error", _short_error(exc), **flags)
    answer = (resp.choices[0].message.content or "") if resp.choices else ""
    if not RED.search(answer):
        return Capabilities(False, "probe", f"image not understood (answer {answer[:30]!r})", **flags)
    return Capabilities(True, "probe", **flags)


class CapabilityCache:
    """Probe once (in a background thread for the API), read many times."""

    def __init__(self, settings: Settings, counter: RequestCounter, *, openai_client: OpenAI | None = None):
        self.settings = settings
        self.counter = counter
        self.openai_client = openai_client
        self._caps: Capabilities | None = None
        self._lock = threading.Lock()

    def get(self, *, wait: bool = True) -> Capabilities:
        if self._caps is None and not wait:
            return PENDING
        with self._lock:
            if self._caps is None:
                try:
                    self._caps = probe_capabilities(self.settings, self.counter, openai_client=self.openai_client)
                except Exception as exc:  # never let the probe kill the app
                    self._caps = Capabilities(False, "error", _short_error(exc))
                log.info("capabilities: %s", self._caps)
            return self._caps

    def set(self, caps: Capabilities) -> None:
        with self._lock:
            self._caps = caps

    def start_background(self) -> None:
        threading.Thread(target=self.get, name="klar-capabilities", daemon=True).start()
