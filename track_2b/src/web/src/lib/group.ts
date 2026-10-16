/**
 * Duplicate findings are shown as one row with "×N" and a list of places.
 * Decisions on a group apply to every item.
 *  - Notes (cantTell with a note reason_code: "not recorded", "model unreachable"…)
 *    group by criterion + outcome + reason_code: the quoted text does not matter,
 *    the reason is the same.
 *  - Other findings group by criterion + outcome + reason + normalised quote
 *    (typically one template repeated across a page or a site).
 */
import type { Finding, Outcome, Status } from '@/types'

export interface FindingGroup {
  key: string
  lead: Finding
  items: Finding[]
}

/** cantTell reason codes that mean "Klar. could not judge this; a person must". */
export const NOTE_CODES: readonly string[] = [
  'not_recorded',
  'request_failed',
  'vision_required',
  'budget',
  'timeout',
  'stopped',
  'suspicious',
  'not_grounded',
  'unparseable',
  'no_screenshot',
]

export function isNote(f: Pick<Finding, 'outcome' | 'reason_code'>): boolean {
  return f.outcome === 'cantTell' && NOTE_CODES.includes(f.reason_code)
}

export function groupKey(f: Finding): string {
  if (isNote(f)) return [f.criterion, f.outcome, f.reason_code].join('|')
  const text = f.excerpt.replace(/\s+/g, ' ').trim().toLowerCase()
  const reason = f.reason_code || f.user_impact
  return [f.criterion, f.outcome, reason, text].join('|')
}

/** Groups in first-seen order; a group's lead is its first finding. */
export function groupFindings(findings: Finding[]): FindingGroup[] {
  const map = new Map<string, FindingGroup>()
  for (const f of findings) {
    const key = groupKey(f)
    const g = map.get(key)
    if (g) g.items.push(f)
    else map.set(key, { key, lead: f, items: [f] })
  }
  return [...map.values()]
}

/** Aggregate status of a group: a single status, or null when mixed. */
export function groupStatus(g: FindingGroup): Status | null {
  const first = g.items[0]!.status
  return g.items.every((f) => f.status === first) ? first : null
}

export function reviewedCount(g: FindingGroup): number {
  return g.items.filter((f) => f.status !== 'to_review').length
}

/* ---- Review scope: only Failed and Needs review ask for a decision ---- */

export const REVIEW_OUTCOMES: readonly Outcome[] = ['failed', 'cantTell']

export function toReview(f: Pick<Finding, 'outcome'>): boolean {
  return f.outcome === 'failed' || f.outcome === 'cantTell'
}

/** "Reviewed {done} of {total} to review": decisions within the review scope only. */
export function reviewProgress(findings: Finding[]): { done: number; total: number } {
  const scope = findings.filter(toReview)
  return { done: scope.filter((f) => f.status !== 'to_review').length, total: scope.length }
}

/** Criterion order: most failures first, then most "Needs review", then the code. */
export function compareSections(
  a: { code: string; failed: number; cantTell: number },
  b: { code: string; failed: number; cantTell: number },
  compareCodes: (x: string, y: string) => number,
): number {
  return b.failed - a.failed || b.cantTell - a.cantTell || compareCodes(a.code, b.code)
}
