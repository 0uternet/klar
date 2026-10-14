"""Data contracts shared by the pipeline, the API and the web UI (contract freeze v2).

These Pydantic models are the source of truth for the API. The web UI mirrors
them; tests/test_contract.py writes their JSON Schemas to
tests/fixtures/contract/*.json so that any drift is visible in review and in the
frontend's contract check.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Outcome = Literal["failed", "cantTell", "passed", "inapplicable"]  # W3C ACT / EARL vocabulary
Source = Literal["rule", "heuristic", "apertus"]  # who decided
Mode = Literal["local", "swiss_cloud", "external", "replay"]
Status = Literal["to_review", "accepted", "rejected"]
# Coverage of a criterion in this build: its method when a check module exists, else "planned".
Method = Literal["rule", "apertus_text", "apertus_vision", "human", "experimental", "planned"]
Confidence = Literal["high", "medium", "low"]
UiLang = Literal["en", "de", "fr", "it"]
Destination = Literal["local", "swiss_cloud", "external"]
Step = Literal["render", "axe", "extract", "apertus", "verify", "done"]
# Why a scan ended in state "error" (ScanStats.error_code).
ErrorCode = Literal["unreachable", "tls", "dns", "timeout_page", "blocked_redirect", "too_many_redirects",
                    "not_html", "scan_timeout", "browser", "internal", "blocked_private", "blocked_metadata",
                    "blocked_localhost"]

UI_LANGS: tuple[str, ...] = ("en", "de", "fr", "it")


class Candidate(BaseModel):
    """One element (or page, or form) a check looks at. Internal, not part of the API."""

    id: str  # stable: sha1(page_url + selector + criterion)[:12]
    criterion: str  # "2.4.4"
    page_url: str
    selector: str  # unique CSS selector
    html: str  # outerHTML, truncated to 2000 chars
    text: str = ""  # visible text
    accessible_name: str | None = None
    context: dict[str, str] = {}  # ONLY what the check is allowed to show, e.g. {"sentence": ..., "list_item": ...}
    lang_declared: str | None = None  # inherited lang of the element
    screenshot: str | None = None  # path of a PNG crop, relative to the scan dir ("crops/<id>.png")
    extra: dict = {}


class Finding(BaseModel):
    id: str  # "<scan id>-<candidate id>", unique across scans
    criterion: str  # "3.1.2"
    criterion_name: str  # "Language of Parts"
    level: Literal["A", "AA"]
    act_rule: str | None  # ACT rule id ONLY when the finding applies that rule ("off6ek")
    en301549: str | None  # "9.3.1.2"
    outcome: Outcome
    source: Source
    confidence: Confidence
    page_url: str
    selector: str
    excerpt: str  # MUST be a verbatim substring of the captured DOM/text (guard)
    context_shown: dict[str, str]  # exactly what the model saw
    explanation: str  # rendered from i18n (criterion, reason_code, ui_lang)
    user_impact: str  # one sentence, rendered from i18n
    fix_diff: str | None  # unified diff on the HTML snippet
    fix_hint: str | None  # plain-language CMS instruction
    screenshot: str | None  # file name for GET /api/scans/{id}/files/{name} ("<id>.png")
    model: str | None  # e.g. "swiss-ai/Apertus-v1.5-8B"
    status: Status = "to_review"
    content_lang: str | None = None  # BCP 47 language of the quoted page content (excerpt, fix)
    axe_rule: str | None = None  # axe rule id when the finding came from axe-core
    reason_code: str  # closed enum per check, e.g. "generic_no_context", "apertus_context", "not_recorded", "axe"
    reason: str | None = None  # the model's short English reason, kept for audit (null without a model)


class ProgressStep(BaseModel):
    step: Step
    state: Literal["pending", "running", "done", "error", "skipped"]
    started_at: datetime | None = None
    duration_ms: int | None = None
    detail: str | None = None
    current: int | None = None
    total: int | None = None


class ScanStats(BaseModel):
    """Shape of Scan.stats. FLAT. A few extra diagnostic keys are allowed
    (candidates, cache_hits, check_errors, blocked_requests, criteria lists…)."""

    model_config = ConfigDict(extra="allow")

    failed: int = 0
    cantTell: int = 0
    passed: int = 0
    inapplicable: int = 0
    to_review: int = 0
    accepted: int = 0
    rejected: int = 0
    criteria_checked: int = 0  # criteria with ≥ 1 implemented check that ran
    criteria_rule: int = 0  # criteria with automated rules (axe-core or rule checks) that ran
    criteria_apertus: int = 0  # criteria with an Apertus-backed check that ran
    llm_calls: int = 0  # HTTP requests to the model endpoint (incl. retries)
    tokens_in: int = 0
    tokens_out: int = 0
    seconds: float = 0.0
    guard_rejected: int = 0
    injection_flagged: int = 0  # candidates held back by the prompt-injection pre-filter
    not_recorded: int = 0
    llm_errors: int = 0
    budget_skipped: dict[str, int] = {}  # per criterion
    replay_loose_hits: int = 0  # replayed answers matched without the exact key (approximate)
    ai_requests: dict[Destination, int] = {}  # measured, persisted per scan
    error_code: ErrorCode | None = None  # set when state == "error"
    http_status: int | None = None  # status of the page's navigation response (None for pasted HTML)
    final_url: str | None = None  # after redirects
    page_title: str | None = None
    max_llm_calls: int | None = None  # the effective per-scan model budget (KLAR_MAX_LLM_CALLS)
    timeout_notes: int = 0  # candidates left as cantTell `timeout` notes when KLAR_SCAN_TIMEOUT hit
    timeout_skipped_checks: list[str] = []  # criteria whose check never started (scan out of time)


class Scan(BaseModel):
    id: str
    url: str
    created_at: datetime
    mode: Mode
    model: str
    ui_lang: UiLang
    state: Literal["queued", "running", "done", "error"]
    progress: list[dict]  # ProgressStep objects (kept as dicts: updated in place while running)
    findings: list[Finding]
    coverage: dict[str, Method]  # method if implemented, otherwise "planned"
    stats: dict  # ScanStats


class LLMTask(BaseModel):
    """ONE closed question for Apertus (internal).

    Only `system`, `user`, `images`, `json_schema` and `max_tokens` are sent to the
    model and enter the cache key. `context_shown` is bookkeeping: the exact
    context rendered into `user`, copied into Finding.context_shown.
    """

    system: str
    user: str
    images: list[str] = []  # PNG paths, relative to the scan directory
    json_schema: dict
    max_tokens: int = 200
    context_shown: dict[str, str] = Field(default_factory=dict, exclude=True)

    def wire(self) -> dict:
        """The part of the task that is sent to the model (and hashed)."""
        return {
            "system": self.system,
            "user": self.user,
            "images": list(self.images),
            "json_schema": self.json_schema,
            "max_tokens": self.max_tokens,
        }


# --- API request / response models -----------------------------------------------------


class ScanRequest(BaseModel):
    url: str | None = Field(default=None, max_length=4096)
    html: str | None = None  # size limit KLAR_MAX_HTML_BYTES (default 2 MB) → HTTP 413
    ui_lang: UiLang = "en"
    criteria: list[str] | None = None


class ScanCreated(BaseModel):
    id: str


class FindingPatch(BaseModel):
    status: Literal["accepted", "rejected", "to_review"]


class CriterionInfo(BaseModel):
    """Item of GET /api/criteria and `klar criteria --json`."""

    criterion: str  # "2.4.4"
    name: str
    level: Literal["A", "AA"]
    principle: Literal["perceivable", "operable", "understandable", "robust"]
    method: Method  # the registry method if implemented, otherwise "planned"
    implemented: bool  # a check module exists and is registered
    evaluated: bool  # measured in eval/results/results.json
    act_rule: str | None
    en301549: str | None
    url: str  # W3C Understanding page


class Health(BaseModel):
    mode: Mode
    model: str
    replay_models: list[str] | None = None  # replay mode: the recorded models actually replayed
    base_url_host: str | None
    provider: str | None = None  # "phoeniqs" | "cscs" | "vllm" | "llamacpp" | None
    vision: bool
    vision_source: Literal["pending", "probe", "override", "replay", "error"] = "pending"
    json_schema: bool = False
    chat_template_kwargs: bool = False
    version: str
    config_error: str | None = None
    ai_requests: dict[Destination, int] = Field(
        default_factory=dict, description="model requests by destination since the server started (in memory)")
    llm_reachable: bool | None = None  # None: replay mode, or the start-up probe has not finished
    llm_error: str | None = None  # why the endpoint could not be reached
    # Additional (not in the frozen contract, kept for older clients / provenance display):
    external_ai_requests: int = Field(
        0, description="ai_requests.swiss_cloud + ai_requests.external, since the server started")
    replay_recorded: dict | None = None  # {"from", "to", "hosts", "records"} of the replayed recordings
