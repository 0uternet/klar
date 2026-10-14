"""Environment → Settings, including the sovereignty mode.

The three LLM_* variables select the model endpoint. Everything
else is prefixed KLAR_ and optional.

| Variable                      | Default                          | Meaning                                              |
|-------------------------------|----------------------------------|------------------------------------------------------|
| LLM_NAME                      | swiss-ai/Apertus-v1.5-8B         | model id sent to the endpoint                        |
| LLM_BASE_URL                  | (unset → replay mode)            | OpenAI-compatible base URL, e.g. http://llm:8000/v1  |
| LLM_API_KEY                   | "local"                          | bearer token                                         |
| KLAR_REPLAY                   | 0                                | 1 → replay recorded answers, never call a model      |
| KLAR_REPLAY_MODELS            | swiss-ai/Apertus-v1.5-*          | replay serves only recordings of these models (glob) |
| KLAR_REPLAY_EXACT             | 0                                | 1 → replay only exact keys (the evaluation forces it)|
| KLAR_DATA_DIR                 | ./var                            | SQLite DB, scan folders, screenshots, reports/       |
| KLAR_PROJECT_ROOT             | the track_2b root (auto)         | data/{demo-site,replay,testset}, eval/results        |
| KLAR_UI_LANG                  | en                               | default UI language (en, de, fr, it)                 |
| KLAR_REPLAY_DIR               | <project>/data/replay            | JSONL answer store (cache + replay)                  |
| KLAR_RECORD                   | 1                                | live mode: append new answers to the store           |
| KLAR_DEMO_DIR                 | <project>/data/demo-site         | served at /demo/                                     |
| KLAR_STATIC_DIR               | <package>/api/static             | built Vue UI                                         |
| KLAR_VISION                   | (auto: probed once)              | force 1/0 to skip the probe                          |
| KLAR_LLM_TIMEOUT              | 240                              | seconds per model request (CPU inference is slow)    |
| KLAR_LLM_CONCURRENCY          | 2                                | parallel model requests per scan                     |
| KLAR_MAX_LLM_CALLS            | 150                              | per-scan budget of model questions (round-robin)     |
| KLAR_DETECT_LANGS             | de,fr,it,en,es,pt,nl,la,sq,tr,hr | languages the 3.1.2 detector may propose             |
| KLAR_ALLOW_PRIVATE_NETWORKS   | 0                                | 1 → scans may reach RFC 1918 / ULA hosts (intranet)  |
| KLAR_APP_PORT                 | 8080                             | port the app listens on inside its host/container    |
| KLAR_ALLOWED_HOSTS            | (none)                           | extra Host headers accepted besides localhost,       |
|                               |                                  | 127.0.0.1 and ::1 (DNS-rebinding protection)         |
| KLAR_SCAN_TIMEOUT             | 900                              | seconds before a scan is cancelled                   |
| KLAR_QUEUE_MAX                | 4                                | queued + running scans before HTTP 429               |
| KLAR_MAX_HTML_BYTES           | 2000000                          | pasted HTML larger than this → HTTP 413              |
"""

from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass, field, replace
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from klar.models import Mode
from klar.netpolicy import NetPolicy

DEFAULT_MODEL = "swiss-ai/Apertus-v1.5-8B"
DEFAULT_REPLAY_MODELS = ("swiss-ai/Apertus-v1.5-*",)

# Docker-compose service names of the bundled inference servers, plus the name
# used in .env.example.
LOCAL_SERVICE_HOSTS = {"llm-gpu", "llm-cpu", "llm", "localhost", "host.docker.internal"}
SWISS_CLOUD_SUFFIXES = {"phoeniqs.com": "Phoeniqs", "cscs.ch": "CSCS"}

_PACKAGE_DIR = Path(__file__).resolve().parent


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _find_project_root() -> Path:
    """track_2b/ when running from a checkout (src layout) or the Docker image."""
    explicit = os.environ.get("KLAR_PROJECT_ROOT")
    if explicit:
        return Path(explicit).resolve()
    for candidate in (_PACKAGE_DIR.parents[1], Path.cwd()):  # src/klar → track_2b
        if (candidate / "data").is_dir() or (candidate / "pyproject.toml").is_file():
            return candidate
    return Path.cwd()


def base_url_error(base_url: str | None) -> str | None:
    """A set but unusable LLM_BASE_URL must never silently fall back to replay."""
    if not base_url:
        return None
    u = urlparse(base_url)
    if u.scheme not in ("http", "https") or not u.hostname:
        return f"LLM_BASE_URL must be an http(s) URL with a host, e.g. http://llm:8000/v1 (got {base_url!r})"
    return None


@lru_cache(maxsize=8)
def _endpoint_error(base_url: str | None) -> str | None:
    """LLM endpoint policy, resolved once per URL (health must stay fast)."""
    if not base_url:
        return None
    verdict = NetPolicy.check_endpoint(base_url)  # private hosts OK, metadata/link-local never
    return None if verdict.ok else verdict.reason


def detect_mode(base_url: str | None, replay_flag: bool) -> Mode:
    """Order matters: replay wins, then local, then Swiss cloud, then external."""
    if replay_flag or not base_url or base_url_error(base_url):
        return "replay"
    host = (urlparse(base_url).hostname or "").lower().rstrip(".")
    if host in LOCAL_SERVICE_HOSTS or host == "127.0.0.1" or host.endswith(".localhost"):
        return "local"
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return "local"
        return "external"
    except ValueError:
        pass
    # Superset of the documented table: a dot-less host name (docker/LAN service
    # such as "vllm") or a reserved local suffix cannot be a public internet host.
    if "." not in host or host.endswith((".local", ".internal", ".lan", ".home.arpa")):
        return "local"
    for suffix in SWISS_CLOUD_SUFFIXES:
        if host == suffix or host.endswith("." + suffix):
            return "swiss_cloud"
    return "external"


def destination_class(base_url: str | None) -> str:
    """'local', 'swiss_cloud' or 'external' for the AI-request counters."""
    mode = detect_mode(base_url, False)
    return "local" if mode == "replay" else mode


def provider_name(base_url: str | None) -> str | None:
    host = (urlparse(base_url or "").hostname or "").lower()
    for suffix, name in SWISS_CLOUD_SUFFIXES.items():
        if host == suffix or host.endswith("." + suffix):
            return name
    return None


@dataclass(frozen=True)
class Settings:
    llm_name: str = DEFAULT_MODEL
    llm_base_url: str | None = None
    llm_api_key: str = "local"
    replay: bool = False
    data_dir: Path = Path("var")
    ui_lang: str = "en"
    project_root: Path = field(default_factory=_find_project_root)
    replay_dir: Path | None = None
    demo_dir: Path | None = None
    static_dir: Path | None = None
    record: bool = True
    vision_override: bool | None = None
    llm_timeout: float = 240.0
    llm_concurrency: int = 2
    max_llm_calls: int = 150
    detect_langs: tuple[str, ...] = ("de", "fr", "it", "en", "es", "pt", "nl", "la", "sq", "tr", "hr")
    replay_models: tuple[str, ...] = DEFAULT_REPLAY_MODELS
    replay_exact: bool = False
    allow_private_networks: bool = False
    app_port: int = 8080
    allowed_hosts: tuple[str, ...] = ("localhost", "127.0.0.1", "::1", "[::1]")
    scan_timeout: float = 900.0
    max_queue: int = 4
    max_html_bytes: int = 2_000_000
    # Evaluation ablation: "no_context" sends every question without its programmatic context.
    ablation: str | None = None
    # Tests may force a mode (e.g. "external" against a fake server on 127.0.0.1).
    mode_override: Mode | None = None

    # -- derived -------------------------------------------------------------------
    @property
    def mode(self) -> Mode:
        if self.mode_override:
            return self.mode_override
        return detect_mode(self.llm_base_url, self.replay)

    @property
    def config_error(self) -> str | None:
        if self.replay:
            return None
        return base_url_error(self.llm_base_url) or _endpoint_error(self.llm_base_url)

    @property
    def base_url_host(self) -> str | None:
        if not self.llm_base_url:
            return None
        return urlparse(self.llm_base_url).hostname

    @property
    def provider(self) -> str | None:
        return provider_name(self.llm_base_url) if self.mode == "swiss_cloud" else None

    @property
    def destination(self) -> str:
        """Where model requests go: 'local', 'swiss_cloud' or 'external' (never 'replay')."""
        return "local" if self.mode == "replay" else self.mode

    @property
    def counts_external_requests(self) -> bool:
        """Requests that leave the machine/organisation are counted for the badge."""
        return self.mode in ("swiss_cloud", "external")

    @property
    def replay_path(self) -> Path:
        return self.replay_dir or (self.project_root / "data" / "replay")

    @property
    def demo_path(self) -> Path:
        return self.demo_dir or (self.project_root / "data" / "demo-site")

    @property
    def static_path(self) -> Path:
        return self.static_dir or (_PACKAGE_DIR / "api" / "static")

    @property
    def scans_path(self) -> Path:
        return self.data_dir / "scans"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "klar.db"

    def demo_origins(self) -> tuple[tuple[str, str], ...]:
        """The app's own bundled demo site: the only loopback target allowed by default."""
        return tuple((f"http://{h}:{self.app_port}", "/demo/") for h in ("127.0.0.1", "localhost"))

    def net_policy(self, *extra_allowed: tuple[str, str], allow_file: bool = False) -> NetPolicy:
        return NetPolicy(allow_private=self.allow_private_networks, allow_file=allow_file,
                         allowed=self.demo_origins() + tuple(extra_allowed))

    def with_(self, **changes) -> "Settings":
        return replace(self, **changes)

    # -- construction --------------------------------------------------------------
    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Settings":
        e = dict(os.environ if env is None else env)

        def path(name: str) -> Path | None:
            v = e.get(name)
            return Path(v).expanduser().resolve() if v else None

        def csv(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
            raw = e.get(name)
            return tuple(x.strip() for x in raw.split(",") if x.strip()) if raw else default

        vision = e.get("KLAR_VISION")
        ui_lang = (e.get("KLAR_UI_LANG") or "en").lower()
        root = path("KLAR_PROJECT_ROOT") or _find_project_root()
        return cls(
            project_root=root,
            llm_name=e.get("LLM_NAME") or DEFAULT_MODEL,
            llm_base_url=(e.get("LLM_BASE_URL") or "").strip() or None,
            llm_api_key=e.get("LLM_API_KEY") or "local",
            replay=_truthy(e.get("KLAR_REPLAY")),
            data_dir=Path(e.get("KLAR_DATA_DIR") or "var").expanduser().resolve(),
            ui_lang=ui_lang if ui_lang in ("en", "de", "fr", "it") else "en",
            replay_dir=path("KLAR_REPLAY_DIR"),
            demo_dir=path("KLAR_DEMO_DIR"),
            static_dir=path("KLAR_STATIC_DIR"),
            record=e.get("KLAR_RECORD", "1") != "0",
            vision_override=None if vision in (None, "") else _truthy(vision),
            llm_timeout=float(e.get("KLAR_LLM_TIMEOUT") or 240),
            llm_concurrency=max(1, int(e.get("KLAR_LLM_CONCURRENCY") or 2)),
            max_llm_calls=max(0, int(e.get("KLAR_MAX_LLM_CALLS") or 150)),
            detect_langs=tuple(x.lower() for x in csv("KLAR_DETECT_LANGS", cls.detect_langs)),
            replay_models=csv("KLAR_REPLAY_MODELS", DEFAULT_REPLAY_MODELS),
            replay_exact=_truthy(e.get("KLAR_REPLAY_EXACT")),
            allow_private_networks=_truthy(e.get("KLAR_ALLOW_PRIVATE_NETWORKS")),
            app_port=int(e.get("KLAR_APP_PORT") or 8080),
            allowed_hosts=("localhost", "127.0.0.1", "::1", "[::1]") + csv("KLAR_ALLOWED_HOSTS", ()),
            scan_timeout=float(e.get("KLAR_SCAN_TIMEOUT") or 900),
            max_queue=max(1, int(e.get("KLAR_QUEUE_MAX") or 4)),
            max_html_bytes=max(1000, int(e.get("KLAR_MAX_HTML_BYTES") or 2_000_000)),
        )
