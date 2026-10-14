/**
 * Boundary normalisers: everything the HTTP API returns is brought to the frozen
 * contract (klar/models.py, contract v2) before the UI sees it. They also accept the
 * older payload shapes (registry key `number`, nested `stats.counts`, list-valued
 * `criteria_checked`, `external_ai_requests`) so the UI keeps working during the
 * transition. Nothing here invents data: missing values become null, 0 or "unknown".
 */
import { understandingUrl } from '@/data/wcag'
import type {
  AiRequests,
  CriterionInfo,
  Finding,
  Health,
  Method,
  Principle,
  ProgressStep,
  Scan,
  ScanState,
  ScanStats,
  ScanSummary,
  VisionSource,
} from '@/types'

type Obj = Record<string, unknown>
const obj = (v: unknown): Obj => (v && typeof v === 'object' ? (v as Obj) : {})
const str = (v: unknown): string | null => (typeof v === 'string' ? v : null)
/** A missing number stays unknown (null). Never 0: 0 would claim a measurement. */
const num = (v: unknown): number | null => (typeof v === 'number' && Number.isFinite(v) ? v : null)
const bool = (v: unknown): boolean | null => (typeof v === 'boolean' ? v : null)

const PRINCIPLES: Principle[] = ['perceivable', 'operable', 'understandable', 'robust']
const METHODS: Method[] = ['rule', 'apertus_text', 'apertus_vision', 'human', 'experimental', 'planned']
const VISION: VisionSource[] = ['pending', 'probe', 'override', 'replay', 'error']

/** Per-destination counters; null when the server sent nothing, per-field null when partial. */
export function normaliseAiRequests(v: unknown, legacyExternal?: unknown): AiRequests | null {
  if (v && typeof v === 'object') {
    const o = v as Obj
    return { local: num(o.local), swiss_cloud: num(o.swiss_cloud), external: num(o.external) }
  }
  // Older servers only counted external requests; the other destinations stay unknown.
  if (typeof legacyExternal === 'number') return { local: null, swiss_cloud: null, external: legacyExternal }
  return null
}

export function normaliseHealth(raw: unknown): Health {
  const o = obj(raw)
  if (typeof o.mode !== 'string') throw new Error('Unexpected /api/health response')
  const vs = str(o.vision_source)
  return {
    mode: o.mode as Health['mode'],
    model: str(o.model) ?? '',
    replay_models: Array.isArray(o.replay_models) ? o.replay_models.map(String) : null,
    base_url_host: str(o.base_url_host),
    provider: str(o.provider),
    vision: bool(o.vision),
    vision_source: vs && (VISION as string[]).includes(vs) ? (vs as VisionSource) : null,
    json_schema: bool(o.json_schema),
    chat_template_kwargs: bool(o.chat_template_kwargs),
    version: str(o.version) ?? '',
    config_error: str(o.config_error),
    ai_requests: normaliseAiRequests(o.ai_requests, o.external_ai_requests),
    llm_reachable: bool(o.llm_reachable),
    llm_error: str(o.llm_error),
    external_ai_requests: num(o.external_ai_requests),
    replay_recorded: o.replay_recorded && typeof o.replay_recorded === 'object' ? (o.replay_recorded as Record<string, unknown>) : null,
  }
}

export function normaliseCriteria(raw: unknown): CriterionInfo[] {
  const list = Array.isArray(raw) ? raw : ((obj(raw).criteria as unknown[]) ?? [])
  return list
    .map((c): CriterionInfo | null => {
      const o = obj(c)
      const criterion = String(o.criterion ?? o.number ?? '')
      const method = str(o.method)
      if (!criterion || !method || !(METHODS as string[]).includes(method)) return null
      const p = o.principle
      const principle =
        typeof p === 'string' && (PRINCIPLES as string[]).includes(p.toLowerCase())
          ? (p.toLowerCase() as Principle)
          : typeof p === 'number' && PRINCIPLES[p - 1]
            ? PRINCIPLES[p - 1]!
            : PRINCIPLES[Number(criterion[0]) - 1] ?? 'perceivable'
      return {
        criterion,
        name: String(o.name ?? ''),
        level: o.level === 'AA' || o.level === 'A' ? o.level : null,
        principle,
        method: method as Method,
        // Unknown means "not implemented": the UI never claims coverage it was not told about.
        implemented: o.implemented === true,
        evaluated: o.evaluated === true,
        act_rule: str(o.act_rule),
        en301549: str(o.en301549),
        url: str(o.url) ?? understandingUrl(criterion),
      }
    })
    .filter((c): c is CriterionInfo => c !== null)
}

export function normaliseStep(raw: unknown): ProgressStep {
  const o = obj(raw)
  return {
    step: String(o.step ?? ''),
    state: (str(o.state) ?? 'pending') as ProgressStep['state'],
    started_at: str(o.started_at),
    duration_ms: typeof o.duration_ms === 'number' ? o.duration_ms : null,
    detail: str(o.detail) || null,
    current: typeof o.current === 'number' ? o.current : null,
    total: typeof o.total === 'number' ? o.total : null,
  }
}

export function normaliseFinding(raw: unknown): Finding {
  const o = obj(raw) as Partial<Finding> & Obj
  return {
    ...(o as unknown as Finding),
    act_rule: str(o.act_rule),
    axe_rule: str(o.axe_rule),
    en301549: str(o.en301549),
    content_lang: str(o.content_lang),
    context_shown: (o.context_shown as Record<string, string>) ?? {},
    reason_code: str(o.reason_code) ?? '',
    reason: str(o.reason),
    fix_diff: str(o.fix_diff),
    fix_hint: str(o.fix_hint),
    screenshot: str(o.screenshot),
    model: str(o.model),
    status: (str(o.status) ?? 'to_review') as Finding['status'],
  }
}

export function normaliseStats(raw: unknown): Partial<ScanStats> {
  const o = obj(raw)
  const counts = obj(o.counts)
  const out: Partial<ScanStats> = { ...(o as Partial<ScanStats>) }
  for (const k of ['failed', 'cantTell', 'passed', 'inapplicable'] as const) {
    if (typeof o[k] !== 'number' && typeof counts[k] === 'number') out[k] = counts[k] as number
  }
  if (Array.isArray(o.criteria_checked)) out.criteria_checked = o.criteria_checked.length
  if ('max_llm_calls' in o) out.max_llm_calls = num(o.max_llm_calls)
  if ('timeout_skipped_checks' in o) out.timeout_skipped_checks = Array.isArray(o.timeout_skipped_checks) ? o.timeout_skipped_checks.map(String) : []
  // Absent stays absent (unknown); never filled with zeros.
  const ai = normaliseAiRequests(o.ai_requests, o.external_ai_requests)
  if (ai) out.ai_requests = ai
  else delete out.ai_requests
  delete (out as Obj).counts
  delete (out as Obj).external_ai_requests
  return out
}

export function normaliseScan(raw: unknown): Scan {
  const o = obj(raw) as Partial<Scan> & Obj
  return {
    ...(o as unknown as Scan),
    progress: Array.isArray(o.progress) ? o.progress.map(normaliseStep) : [],
    findings: Array.isArray(o.findings) ? o.findings.map(normaliseFinding) : [],
    coverage: (o.coverage as Scan['coverage']) ?? {},
    stats: normaliseStats(o.stats),
  }
}

const STATES: ScanState[] = ['queued', 'running', 'done', 'error']

/** GET /api/scans: newest first. Rows without an id are dropped. */
export function normaliseScanList(raw: unknown): ScanSummary[] {
  const list = Array.isArray(raw) ? raw : ((obj(raw).scans as unknown[]) ?? [])
  return list
    .map((r): ScanSummary | null => {
      const o = obj(r)
      const id = str(o.id)
      const state = str(o.state)
      if (!id || !state || !(STATES as string[]).includes(state)) return null
      return { id, created_at: str(o.created_at) ?? '', url: str(o.url) ?? '', state: state as ScanState }
    })
    .filter((s): s is ScanSummary => s !== null)
}
