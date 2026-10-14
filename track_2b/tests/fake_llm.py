"""A fake OpenAI-compatible server (stdlib http.server in a thread).

    with FakeLLM(responder) as fake:
        settings = Settings(llm_base_url=fake.base_url, ...)

`responder(request_json) -> str | dict | (status, str | dict)`: the content of the
assistant message (a dict is JSON-encoded), or an HTTP error. Every request body
is kept in `fake.requests` for assertions.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

Responder = Callable[[dict], Any]


def _default(_: dict) -> dict:
    return {"outcome": "cantTell", "confidence": "low", "quote": "", "reason": "default", "fix": ""}


class FakeLLM:
    def __init__(self, responder: Responder | None = None, *, model: str = "swiss-ai/Apertus-v1.5-8B",
                 modalities: list[str] | None = None):
        self.responder = responder or _default
        self.model = model
        self.modalities = modalities
        self.requests: list[dict] = []
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # silence
                pass

            def _send(self, status: int, body: dict) -> None:
                data = json.dumps(body).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                if self.path.rstrip("/").endswith("/models"):
                    entry: dict = {"id": fake.model, "object": "model"}
                    if fake.modalities is not None:
                        entry["input_modalities"] = fake.modalities
                    self._send(200, {"object": "list", "data": [entry]})
                else:
                    self._send(404, {"error": {"message": "not found"}})

            def do_POST(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(length) or b"{}")
                fake.requests.append(body)
                try:
                    out = fake.responder(body)
                except Exception as exc:  # a bug in a test responder → 500
                    self._send(500, {"error": {"message": f"responder failed: {exc}"}})
                    return
                status = 200
                if isinstance(out, tuple):
                    status, out = out
                if status != 200:
                    msg = out if isinstance(out, str) else json.dumps(out)
                    self._send(status, {"error": {"message": msg, "type": "invalid_request_error"}})
                    return
                content = out if isinstance(out, str) else json.dumps(out, ensure_ascii=False)
                self._send(200, {
                    "id": "chatcmpl-fake", "object": "chat.completion", "created": 0, "model": fake.model,
                    "choices": [{"index": 0, "finish_reason": "stop",
                                 "message": {"role": "assistant", "content": content}}],
                    "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
                })

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_address[1]}/v1"

    def start(self) -> "FakeLLM":
        self._thread.start()
        return self

    def stop(self) -> None:
        self.server.shutdown()
        self.server.server_close()

    def __enter__(self) -> "FakeLLM":
        return self.start()

    def __exit__(self, *exc) -> None:
        self.stop()


def user_text(request: dict) -> str:
    """The user prompt text of a chat request (string or multimodal parts)."""
    content = request["messages"][-1]["content"] if len(request["messages"]) < 2 else request["messages"][1]["content"]
    if isinstance(content, list):
        return " ".join(p.get("text", "") for p in content if p.get("type") == "text")
    return content


def system_text(request: dict) -> str:
    first = request["messages"][0]
    return first["content"] if first.get("role") == "system" and isinstance(first["content"], str) else ""


def is_probe(request: dict) -> bool:
    """Capability probes: one user message, no system prompt."""
    return len(request["messages"]) == 1


def klar_responder(request: dict) -> dict:
    """Scripted 'Apertus' that answers each check's closed question plausibly."""
    if is_probe(request):
        return '{"ok": true}' if "response_format" in request else "red"
    system, user = system_text(request), user_text(request)
    if "3.1.2" in system:
        if "Office fédéral de la statistique" in user:
            return {"category": "institution", "language": "fr", "confidence": "high",
                    "quote": "Office fédéral de la statistique", "reason": "Name of a federal office."}
        if "Benvenuti" in user:
            return {"category": "foreign_language_passage", "language": "it", "confidence": "high",
                    "quote": "Benvenuti a Musterwil!", "reason": "An Italian greeting."}
        return {"category": "other", "language": "de", "confidence": "low", "quote": "", "reason": "Unsure."}
    if "2.4.4" in system:
        if '"link_text": "hier"' in user and "Abfallkalender" in user:
            return {"category": "context", "confidence": "high", "quote": "hier",
                    "reason": "The sentence names the waste calendar.", "fix": ""}
        if '"link_text": "Weiterlesen"' in user:
            # A hallucinated quote: must be rejected by the evidence guard.
            return {"category": "nowhere", "confidence": "high", "quote": "Klicken Sie hier für alles",
                    "reason": "Generic.", "fix": "Bericht lesen"}
        name = user.split('"link_text": "', 1)[1].split('"', 1)[0] if '"link_text": "' in user else ""
        return {"category": "nowhere", "confidence": "medium", "quote": name,
                "reason": "The text does not name the destination."}
    if "1.1.1" in system:
        return {"image_type": "informative", "outcome": "passed", "confidence": "medium",
                "quote": "Rathaus Musterwil", "reason": "The alternative describes the photo.", "fix": ""}
    return _default(request)
