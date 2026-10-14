/**
 * Run notes (UX-2, catalogue N1–N8): what this run could not do, from the scan's
 * own counters, ordered by severity, each with one way forward. Pure (message
 * keys only) so it is unit-tested; RunNotes.vue renders them.
 */
import type { Finding, Scan } from '@/types'
import type { MessageKey, PluralBase } from '@/i18n'

export type NoteAction =
  | { kind: 'demo' }
  | { kind: 'rerun' }
  | { kind: 'runAgain' }
  | { kind: 'connect' }
  | { kind: 'checkConnection' }
  | { kind: 'filter'; reason: string }

export interface RunNote {
  id: 'N1' | 'N1b' | 'N2' | 'NT' | 'N3' | 'N4' | 'N5' | 'N6' | 'N7' | 'N8'
  /** Bold title (N2 when Apertus answered nothing). */
  title?: MessageKey
  /** A plain message, or a plural base ("….one" / "….other") chosen by `count`. */
  text: MessageKey | PluralBase
  count?: number
  params: Record<string, string | number>
  /** "warning": the run lost answers; "info": a fact worth knowing. */
  tone: 'warning' | 'info'
  actions: NoteAction[]
  details?: string
}

const num = (v: unknown): number => (typeof v === 'number' && Number.isFinite(v) ? v : 0)
const list = (v: unknown): unknown[] => (Array.isArray(v) ? v : [])

export function runNotes(scan: Pick<Scan, 'stats'>, findings: Finding[], isDemo: boolean): RunNote[] {
  const s = scan.stats ?? {}
  const out: RunNote[] = []
  const byReason = (code: string) => findings.filter((f) => f.reason_code === code).length

  const notRecorded = num(s.not_recorded)
  if (notRecorded > 0) {
    out.push(
      isDemo
        ? { id: 'N1', text: 'notes.nrDemo', count: notRecorded, params: {}, tone: 'warning', actions: [{ kind: 'connect' }] }
        : { id: 'N1b', text: 'notes.nrPage', count: notRecorded, params: {}, tone: 'warning', actions: [{ kind: 'demo' }, { kind: 'connect' }] },
    )
  }

  const llmErrors = num(s.llm_errors)
  if (llmErrors > 0) {
    const asked = Math.max(num(s.asked_apertus), llmErrors)
    out.push({
      id: 'N2',
      title: llmErrors >= asked ? 'notes.llm.allTitle' : undefined,
      text: 'notes.llm',
      params: { n: llmErrors, m: asked },
      tone: 'warning',
      actions: [{ kind: 'rerun' }, { kind: 'checkConnection' }],
    })
  }

  // FE-4: the scan ran out of time (KLAR_SCAN_TIMEOUT): elements left as notes, checks never started.
  const timeoutNotes = num(s.timeout_notes)
  const skippedChecks = list(s.timeout_skipped_checks).map(String)
  if (timeoutNotes > 0 || skippedChecks.length > 0) {
    const criteria = skippedChecks.join(', ')
    out.push({
      id: 'NT',
      text: timeoutNotes > 0 ? (skippedChecks.length ? 'notes.timeoutBoth' : 'notes.timeoutElems') : 'notes.timeoutCrit',
      count: timeoutNotes > 0 ? timeoutNotes : undefined,
      params: { criteria },
      tone: 'warning',
      actions: [{ kind: 'runAgain' }, ...(byReason('timeout') > 0 ? [{ kind: 'filter' as const, reason: 'timeout' }] : [])],
      details: 'KLAR_SCAN_TIMEOUT',
    })
  }

  const budget = Object.values((s.budget_skipped as Record<string, unknown> | undefined) ?? {}).reduce<number>((a, v) => a + num(v), 0)
  if (budget > 0) {
    const max = num(s.max_llm_calls)
    out.push({
      id: 'N3',
      text: max > 0 ? 'notes.budgetMax' : 'notes.budgetAny',
      count: budget,
      params: { max },
      tone: 'warning',
      actions: byReason('budget') > 0 ? [{ kind: 'filter', reason: 'budget' }] : [],
      details: 'KLAR_MAX_LLM_CALLS',
    })
  }

  const vision = byReason('vision_required')
  if (vision > 0) out.push({ id: 'N4', text: 'notes.visionN', count: vision, params: {}, tone: 'warning', actions: [{ kind: 'filter', reason: 'vision_required' }] })

  const injection = num(s.injection_flagged)
  if (injection > 0) {
    out.push({
      id: 'N5',
      text: 'notes.injectionN',
      count: injection,
      params: {},
      tone: 'info',
      actions: byReason('suspicious') > 0 ? [{ kind: 'filter', reason: 'suspicious' }] : [],
    })
  }

  const guard = num(s.guard_rejected)
  if (guard > 0) {
    out.push({
      id: 'N6',
      text: 'notes.guardN',
      count: guard,
      params: {},
      tone: 'info',
      actions: byReason('not_grounded') > 0 ? [{ kind: 'filter', reason: 'not_grounded' }] : [],
    })
  }

  const checkErrors = list(s.check_errors).map(String)
  if (checkErrors.length > 0) {
    const criteria = [...new Set(checkErrors.map((e) => e.match(/^(\d\.\d+\.\d+)/)?.[1] ?? e.split(':')[0]!.trim()))]
    out.push({ id: 'N7', text: 'notes.checkErrors', params: { criteria: criteria.join(', ') }, tone: 'warning', actions: [], details: checkErrors.join('\n') })
  }

  const blocked = list(s.blocked_requests)
  if (blocked.length > 0) {
    const lines = blocked.map((b) =>
      b && typeof b === 'object'
        ? Object.values(b as Record<string, unknown>)
            .filter((v) => typeof v === 'string')
            .join(' · ')
        : String(b),
    )
    out.push({ id: 'N8', text: 'notes.blockedN', count: blocked.length, params: {}, tone: 'info', actions: [], details: lines.join('\n') })
  }
  return out
}

/** "Apertus answers: {answered} of {asked}" (UX-2): null when nothing was asked. */
export function apertusAnswers(stats: Scan['stats'] | undefined): { answered: number; asked: number } | null {
  const asked = num(stats?.asked_apertus)
  if (asked <= 0) return null
  return { answered: Math.max(0, asked - num(stats?.llm_errors) - num(stats?.not_recorded)), asked }
}
