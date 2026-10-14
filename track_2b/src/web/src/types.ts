/**
 * Klar. data contracts — TypeScript mirror of the Pydantic models in `klar/models.py`
 * (contract freeze v2). `npm run contract` compares this file with the JSON Schemas
 * that the backend exports to tests/fixtures/contract/.
 * Optional ("?") fields are UI-side tolerances, never part of the contract.
 */

/** W3C ACT / EARL outcome vocabulary. */
export type Outcome = 'failed' | 'cantTell' | 'passed' | 'inapplicable'
/** Who decided the outcome. */
export type Source = 'rule' | 'heuristic' | 'apertus'
/** Where pages go, computed server-side from LLM_BASE_URL. */
export type Mode = 'local' | 'swiss_cloud' | 'external' | 'replay'
/** Human review status of a finding. */
export type Status = 'to_review' | 'accepted' | 'rejected'
export type Confidence = 'high' | 'medium' | 'low'
export type Level = 'A' | 'AA'
export type UiLang = 'en' | 'de' | 'fr' | 'it'
export type ScanState = 'queued' | 'running' | 'done' | 'error'
/** How Klar. covers a criterion. "planned" = no check module yet (registry is the only source). */
export type Method = 'rule' | 'apertus_text' | 'apertus_vision' | 'human' | 'experimental' | 'planned'
/** What the coverage map shows: a method, or "unknown" when the server gave no information. */
export type CoverageKind = Method | 'unknown'
export type Principle = 'perceivable' | 'operable' | 'understandable' | 'robust'
export type Destination = 'local' | 'swiss_cloud' | 'external'
export type VisionSource = 'pending' | 'probe' | 'override' | 'replay' | 'error'
/** Why a scan ended in state "error" (models.py ErrorCode). */
export type ErrorCode =
  | 'unreachable'
  | 'tls'
  | 'dns'
  | 'timeout_page'
  | 'blocked_redirect'
  | 'too_many_redirects'
  | 'not_html'
  | 'scan_timeout'
  | 'browser'
  | 'internal'
  | 'blocked_private'
  | 'blocked_metadata'
  | 'blocked_localhost'

export const OUTCOMES: readonly Outcome[] = ['failed', 'cantTell', 'passed', 'inapplicable']
export const SOURCES: readonly Source[] = ['rule', 'heuristic', 'apertus']
export const STATUSES: readonly Status[] = ['to_review', 'accepted', 'rejected']
export const COVERAGE_KINDS: readonly CoverageKind[] = ['apertus_text', 'apertus_vision', 'rule', 'experimental', 'planned', 'human']
export const UI_LANGS: readonly UiLang[] = ['en', 'de', 'fr', 'it']

/** Pipeline steps: Render → axe-core → Extract → Apertus x/y → Verify evidence → Done. */
export type KnownStep = 'render' | 'axe' | 'extract' | 'apertus' | 'verify' | 'done'
export const KNOWN_STEPS: readonly KnownStep[] = ['render', 'axe', 'extract', 'apertus', 'verify', 'done']
export type StepState = 'pending' | 'running' | 'done' | 'error' | 'skipped'

/** models.py `ProgressStep` (SSE `progress`; clients upsert by `step`). */
export interface ProgressStep {
  step: KnownStep | (string & {})
  state: StepState
  started_at: string | null
  duration_ms: number | null
  detail: string | null
  current: number | null
  total: number | null
}

/** models.py `Finding` (SSE `finding`; clients upsert by `id`). */
export interface Finding {
  id: string
  criterion: string
  criterion_name: string
  level: Level
  /** ACT rule id, only when the check IS that ACT rule. */
  act_rule: string | null
  /** axe-core rule id when source is "rule" and the finding came from axe. */
  axe_rule: string | null
  en301549: string | null
  outcome: Outcome
  source: Source
  confidence: Confidence
  page_url: string
  selector: string
  /** Verbatim substring of the captured DOM/text (evidence guard). */
  excerpt: string
  /** BCP 47 language of the quoted page content (excerpt, fix): the UI sets lang= on it. */
  content_lang: string | null
  /** Exactly what the model saw. Empty for rule/heuristic findings. */
  context_shown: Record<string, string>
  /** Closed enum per check; explanation and user_impact are rendered from it by the backend. */
  reason_code: string
  /** Short English reason from the model, kept for audit. */
  reason: string | null
  /** In the scan's UI language (backend i18n templates). */
  explanation: string
  /** One sentence, in the scan's UI language (backend i18n templates). */
  user_impact: string
  /** Unified diff on the HTML snippet, in the language of the content. */
  fix_diff: string | null
  /** Plain-language CMS instruction. */
  fix_hint: string | null
  /** File name of a PNG crop, served by GET /api/scans/{id}/files/{name}. */
  screenshot: string | null
  model: string | null
  status: Status
}

/**
 * Per-destination AI request counters, measured and persisted per scan.
 * Unknown is `null`, never 0: the UI then says "unknown" instead of claiming a measurement.
 */
export type AiRequests = Record<Destination, number | null>

/** models.py `ScanStats` (flat). */
export interface ScanStats {
  failed: number
  cantTell: number
  passed: number
  inapplicable: number
  to_review: number
  accepted: number
  rejected: number
  /** Number of criteria with at least one implemented check that ran. */
  criteria_checked: number
  criteria_rule: number
  criteria_apertus: number
  llm_calls: number
  tokens_in: number
  tokens_out: number
  seconds: number
  guard_rejected: number
  injection_flagged: number
  not_recorded: number
  llm_errors: number
  budget_skipped: Record<string, number>
  replay_loose_hits: number
  ai_requests: AiRequests | null
  /** Set when state == "error". */
  error_code: ErrorCode | null
  /** Status of the page's navigation response (null for pasted HTML). */
  http_status: number | null
  /** After redirects. */
  final_url: string | null
  page_title: string | null
  /** The effective per-scan model budget (KLAR_MAX_LLM_CALLS); null when unknown. */
  max_llm_calls: number | null
  /** Elements left as cantTell "timeout" notes when KLAR_SCAN_TIMEOUT hit. */
  timeout_notes: number
  /** Criteria whose check never started (the scan ran out of time). */
  timeout_skipped_checks: string[]
  /** Diagnostic extras (outside the frozen schema). */
  title_fetch?: { fetched?: number; timed_out?: number; skipped?: number }
  free_answers?: number
  /** UI-side only: marks mock-up data (never sent by the backend). */
  mock?: string
  /** The pipeline also writes diagnostic keys (asked_apertus, guard_log, …) outside the contract. */
  [key: string]: unknown
}

/** models.py `Scan`. */
export interface Scan {
  id: string
  url: string
  created_at: string
  mode: Mode
  model: string
  ui_lang: UiLang
  state: ScanState
  progress: ProgressStep[]
  findings: Finding[]
  /** Criterion → method if implemented, otherwise "planned". */
  coverage: Record<string, Method>
  /** May be partially filled while a scan is queued or running. */
  stats: Partial<ScanStats>
}

/** models.py `Health` (GET /api/health). */
export interface Health {
  mode: Mode
  model: string
  /** Models whose answers are recorded (replay mode). */
  replay_models: string[] | null
  base_url_host: string | null
  /** "phoeniqs" | "cscs" | "vllm" | "llamacpp" | null */
  provider: string | null
  /** null = the server did not say. */
  vision: boolean | null
  vision_source: VisionSource | null
  json_schema: boolean | null
  chat_template_kwargs: boolean | null
  version: string
  /** A configuration problem the UI must show (never hidden). */
  config_error: string | null
  ai_requests: AiRequests | null
  /** null: replay mode, or the start-up probe has not finished. */
  llm_reachable: boolean | null
  /** Why the endpoint could not be reached. */
  llm_error: string | null
  /** Older single counter, superseded by `ai_requests` (kept by the server for old clients). */
  external_ai_requests?: number | null
  /** Replay mode: provenance of the recorded answers (period, hosts, number of records). */
  replay_recorded?: Record<string, unknown> | null
}

/** Item of GET /api/scans (store.list_scans). */
export interface ScanSummary {
  id: string
  created_at: string
  url: string
  state: ScanState
}

/** models.py `ScanRequest` (POST /api/scans). */
export interface CreateScanRequest {
  url?: string
  html?: string
  ui_lang: UiLang
  criteria?: string[]
}
/** models.py `ScanCreated`. */
export interface CreateScanResponse {
  id: string
}

/** models.py `FindingPatch` (PATCH /api/findings/{id}). */
export interface PatchFindingRequest {
  status: Status
}

export type ExportFormat = 'json' | 'earl' | 'csv' | 'html'
/** Menu order: the printable HTML report first (UX-29). */
export const EXPORT_FORMATS: readonly ExportFormat[] = ['html', 'json', 'earl', 'csv']

/** models.py `CriterionInfo` (item of GET /api/criteria). */
export interface CriterionInfo {
  criterion: string
  name: string
  level: Level | null
  principle: Principle
  method: Method
  /** A check module exists and is registered. */
  implemented: boolean
  /** Measured in eval/results. */
  evaluated: boolean
  act_rule: string | null
  en301549: string | null
  /** Understanding page URL. */
  url: string
}

/** SSE `done` payload. */
export interface ScanDone {
  scan_id: string
  state: ScanState
}

/** Handlers for GET /api/scans/{id}/events (each event has an `id:`; Last-Event-ID resumes). */
export interface ScanEventHandlers {
  /** `event: progress` — one ProgressStep (upsert by `step`), or the full list. */
  onProgress?: (data: ProgressStep | ProgressStep[]) => void
  /** `event: finding` — one Finding (upsert by `id`; may be replayed on reconnect). */
  onFinding?: (finding: Finding) => void
  /** `event: done` — `{scan_id, state}`; the UI then refetches the Scan. */
  onDone?: (done: Partial<ScanDone> & Partial<Scan>) => void
  /** Transport or server error. */
  onError?: (message: string) => void
}

/** What the hero field submits (UI only, not part of the API contract). */
export type CheckInput = { url: string } | { html: string; name: string | null }
