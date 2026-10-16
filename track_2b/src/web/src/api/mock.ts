/**
 * MOCK-UP implementation of the Klar. API, for UI development and labelled demos.
 * Compiled only into dev and `--mode demo` builds (see vite.config.ts), and used
 * only when the URL says `?mock=1`. The UI then shows a persistent
 * "Mock-up data — not a real scan" banner. Never an automatic fallback.
 *
 * URL options (query string, before or after the #):
 *   ?mock=1                 use mock-up data (?mock=0 leaves the mode)
 *   &mode=local|swiss_cloud|external|replay   sovereignty mode to simulate
 *   &speed=0.5              slow down (or speed up) the simulated scan
 */
import { APP_VERSION, DEMO_URL, STORAGE } from '@/config'
import { MOCK_CRITERIA } from '@/mocks/criteria'
import { LLM_CALLS, ELEMENTS, MODEL_BY_MODE, SERVED_SPECS as SPECS, buildScan, hexId } from '@/mocks/musterwil'
import type { Finding, Health, Mode, ProgressStep, Scan, ScanEventHandlers, Status, UiLang } from '@/types'
import { KNOWN_STEPS } from '@/types'
import { locale } from '@/i18n'
import { download, exportFile } from './export'
import { ApiError, type KlarApi } from './types'

export function urlParam(name: string): string | null {
  const fromSearch = new URLSearchParams(location.search).get(name)
  if (fromSearch !== null) return fromSearch
  const q = location.hash.indexOf('?')
  return q >= 0 ? new URLSearchParams(location.hash.slice(q + 1)).get(name) : null
}

const MODES: Mode[] = ['local', 'swiss_cloud', 'external', 'replay']
const requestedMode = urlParam('mode') as Mode | null
const MODE: Mode = requestedMode && MODES.includes(requestedMode) ? requestedMode : 'local'
const SPEED = Math.min(10, Math.max(0.1, Number(urlParam('speed')) || 1))

const HOSTS: Record<Mode, string | null> = {
  local: 'llm-gpu',
  swiss_cloud: 'maas.phoeniqs.com',
  external: 'api.inference.example.com',
  replay: null,
}

interface Meta {
  url: string
  lang: UiLang
  createdAt: number
  statuses: Record<string, Status>
}

interface Entry {
  scan: Scan
  full: Scan
  listeners: Set<ScanEventHandlers>
  started: boolean
  timers: number[]
}

const entries = new Map<string, Entry>()
/** Simulated AI requests of this session (one per simulated Apertus question). */
let aiRequests = 0

function readMeta(): Record<string, Meta> {
  try {
    return JSON.parse(sessionStorage.getItem(STORAGE.mockScans) ?? '{}') as Record<string, Meta>
  } catch {
    return {}
  }
}

function writeMeta(id: string, patch: Partial<Meta>): void {
  try {
    const all = readMeta()
    const prev = all[id] ?? { url: DEMO_URL, lang: 'en', createdAt: Date.now(), statuses: {} }
    all[id] = { ...prev, ...patch, statuses: { ...prev.statuses, ...patch.statuses } }
    sessionStorage.setItem(STORAGE.mockScans, JSON.stringify(all))
  } catch {
    /* storage unavailable: decisions live in memory only */
  }
}

const clone = <T>(v: T): T => JSON.parse(JSON.stringify(v)) as T

function applyStatuses(scan: Scan, statuses: Record<string, Status>): void {
  for (const f of scan.findings) if (statuses[f.id]) f.status = statuses[f.id]!
}

/** Unknown ids (deep links, reloads) resolve to a finished scan of the demo site. */
function ensure(id: string, lang: UiLang = locale.value): Entry {
  const existing = entries.get(id)
  if (existing) return existing
  const meta = readMeta()[id]
  const full = buildScan({
    id,
    url: meta?.url ?? DEMO_URL,
    lang: meta?.lang ?? lang,
    mode: MODE,
    createdAt: meta?.createdAt ?? Date.now() - 4 * 60_000,
  })
  applyStatuses(full, meta?.statuses ?? {})
  const entry: Entry = { scan: clone(full), full, listeners: new Set(), started: true, timers: [] }
  entries.set(id, entry)
  return entry
}

function emit(entry: Entry, fn: (h: ScanEventHandlers) => void): void {
  for (const h of entry.listeners) {
    try {
      fn(h)
    } catch (e) {
      console.error(e)
    }
  }
}

function simulate(entry: Entry): void {
  entry.started = true
  const { scan, full } = entry
  const t0 = performance.now()
  const at = (ms: number, fn: () => void) => entry.timers.push(window.setTimeout(fn, ms / SPEED))

  const setStep = (name: string, patch: Partial<ProgressStep>) => {
    const step = scan.progress.find((s) => s.step === name)
    if (!step) return
    if (patch.state === 'running') step.started_at = new Date().toISOString()
    if (patch.state === 'done' && step.started_at) {
      step.duration_ms = Math.round((Date.now() - Date.parse(step.started_at)) * SPEED)
    }
    Object.assign(step, patch)
    const snapshot = clone(step)
    emit(entry, (h) => h.onProgress?.(snapshot))
  }

  const pushFinding = (key: string) => {
    const idx = SPECS.findIndex((s) => s.key === key)
    const f = full.findings[idx]
    if (!f || scan.findings.some((x) => x.id === f.id)) return
    scan.findings.push(clone(f))
    const snapshot = clone(f)
    emit(entry, (h) => h.onFinding?.(snapshot))
  }

  scan.state = 'running'
  setStep('render', { state: 'running' })
  at(1300, () => {
    setStep('render', { state: 'done', detail: 'Gemeinde Musterwil' })
    setStep('axe', { state: 'running' })
  })
  at(2300, () => {
    setStep('axe', { state: 'done', detail: '31 rule violations' })
    for (const s of SPECS) if (s.source !== 'apertus') pushFinding(s.key)
    setStep('extract', { state: 'running' })
  })
  at(2900, () => {
    setStep('extract', { state: 'done', detail: `${ELEMENTS} elements` })
    setStep('apertus', { state: 'running', detail: `0/${LLM_CALLS}`, current: 0, total: LLM_CALLS })
  })

  // Apertus answers stream in; findings appear once they pass the evidence guard.
  const llmSpecs = SPECS.filter((s) => s.source === 'apertus' && s.key !== 'details-guard').sort((a, b) =>
    hexId(a.key).localeCompare(hexId(b.key)),
  )
  const window_ = 6000
  for (let q = 1; q <= LLM_CALLS; q++) {
    at(2900 + (q * window_) / LLM_CALLS, () => {
      setStep('apertus', { detail: `${q}/${LLM_CALLS}`, current: q, total: LLM_CALLS })
      const from = Math.floor(((q - 1) * llmSpecs.length) / LLM_CALLS)
      const to = Math.floor((q * llmSpecs.length) / LLM_CALLS)
      for (const s of llmSpecs.slice(from, to)) pushFinding(s.key)
      if (MODE !== 'replay') aiRequests++
    })
  }
  at(2900 + window_, () => {
    setStep('apertus', { state: 'done' })
    setStep('verify', { state: 'running' })
  })
  at(9600, () => {
    pushFinding('details-guard')
    setStep('verify', { state: 'done', detail: '1 answer not grounded' })
    setStep('done', { state: 'running' })
  })
  at(9700, () => {
    setStep('done', { state: 'done' })
    for (const f of full.findings) pushFinding(SPECS[full.findings.indexOf(f)]!.key)
    scan.state = 'done'
    scan.stats = { ...full.stats, seconds: Math.round(((performance.now() - t0) / 1000) * SPEED * 10) / 10 }
    // Keep the final progress (with real durations) as the canonical one.
    full.progress = clone(scan.progress)
    full.stats = clone(scan.stats)
    // Contract v2: `done` carries {scan_id, state}; clients refetch the Scan.
    const done = { scan_id: full.id, state: 'done' as const }
    emit(entry, (h) => h.onDone?.(done))
  })
}

function findFinding(id: string): Finding[] {
  const out: Finding[] = []
  for (const e of entries.values()) {
    for (const f of [...e.scan.findings, ...e.full.findings]) if (f.id === id) out.push(f)
  }
  return out
}

export const mockApi: KlarApi = {
  kind: 'mock',

  async health(): Promise<Health> {
    return {
      mode: MODE,
      model: MODEL_BY_MODE[MODE],
      replay_models: MODE === 'replay' ? [MODEL_BY_MODE.replay] : null,
      base_url_host: HOSTS[MODE],
      provider: MODE === 'swiss_cloud' ? 'phoeniqs' : MODE === 'local' ? 'vllm' : null,
      vision: true,
      vision_source: MODE === 'replay' ? 'replay' : 'probe',
      json_schema: true,
      chat_template_kwargs: true,
      version: `${APP_VERSION}-mock`,
      config_error: null,
      llm_reachable: MODE === 'replay' ? null : true,
      llm_error: null,
      ai_requests: {
        local: MODE === 'local' ? aiRequests : 0,
        swiss_cloud: MODE === 'swiss_cloud' ? aiRequests : 0,
        external: MODE === 'external' ? aiRequests : 0,
      },
    }
  },

  async criteria() {
    return MOCK_CRITERIA.map((c) => ({ ...c }))
  },

  async createScan(body) {
    const id = `demo-${Date.now().toString(36)}`
    const createdAt = Date.now()
    const full = buildScan({ id, url: DEMO_URL, lang: body.ui_lang, mode: MODE, createdAt })
    const scan: Scan = {
      ...clone(full),
      state: 'queued',
      findings: [],
      stats: {},
      progress: KNOWN_STEPS.map((step) => ({ step, state: 'pending', started_at: null, duration_ms: null, detail: null, current: null, total: null })),
    }
    entries.set(id, { scan, full, listeners: new Set(), started: false, timers: [] })
    writeMeta(id, { url: DEMO_URL, lang: body.ui_lang, createdAt, statuses: {} })
    return { id }
  },

  async getScan(id) {
    if (!id) throw new ApiError(404, 'Not found')
    return clone(ensure(id).scan)
  },

  async listScans(limit = 20) {
    // Scans created in this tab (session storage), newest first. The mock never invents a history.
    return Object.entries(readMeta())
      .sort(([, a], [, b]) => b.createdAt - a.createdAt)
      .slice(0, limit)
      .map(([id, m]) => ({ id, created_at: new Date(m.createdAt).toISOString(), url: m.url, state: entries.get(id)?.scan.state ?? 'done' }))
  },

  subscribe(id, handlers) {
    const entry = ensure(id)
    entry.listeners.add(handlers)
    // Like an SSE endpoint that replays state to late subscribers.
    queueMicrotask(() => {
      if (!entry.listeners.has(handlers)) return
      handlers.onProgress?.(clone(entry.scan.progress))
      for (const f of entry.scan.findings) handlers.onFinding?.(clone(f))
      if (entry.scan.state === 'done') handlers.onDone?.(clone(entry.scan))
      else if (!entry.started) simulate(entry)
    })
    return () => {
      entry.listeners.delete(handlers)
    }
  },

  async controlScan(id, action) {
    // The mock-up plays a fixed timeline: it acknowledges the action without changing it.
    const entry = ensure(id)
    if (entry.scan.state === 'done' || entry.scan.state === 'error') throw new ApiError(409, 'The scan is not running')
    const state = { paused: action === 'pause', stopping: action === 'stop' }
    emit(entry, (h) => h.onControl?.(state))
    return state
  },

  async patchFinding(id, body) {
    const matches = findFinding(id)
    if (matches.length === 0) throw new ApiError(404, 'Finding not found')
    for (const f of matches) f.status = body.status
    for (const [scanId, e] of entries) if (e.full.findings.some((f) => f.id === id)) writeMeta(scanId, { statuses: { [id]: body.status } })
    await new Promise((r) => setTimeout(r, 120))
    return clone(matches[0]!)
  },

  async exportScan(scan, format) {
    const f = exportFile(scan, format)
    download(f.name, f.type, f.body)
  },
}
