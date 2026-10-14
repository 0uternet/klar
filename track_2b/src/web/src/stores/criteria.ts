/**
 * Coverage comes from the backend registry only (GET /api/criteria): method,
 * `implemented` and, when the backend provides it, `evaluated`. The local table
 * in data/wcag.ts holds titles and translations only, so the UI can never claim
 * a criterion that the backend does not check.
 */
import { ref } from 'vue'
import type { CoverageKind, CriterionInfo, Scan } from '@/types'
import { api } from '@/api'
import { CRITERIA } from '@/data/wcag'

export const criteriaInfo = ref<Map<string, CriterionInfo> | null>(null)
export const criteriaError = ref(false)
let loading: Promise<void> | null = null

export function loadCriteria(force = false): Promise<void> {
  if (loading && !force) return loading
  loading = api()
    .criteria()
    .then((list) => {
      criteriaInfo.value = list.length ? new Map(list.map((c) => [c.criterion, c])) : null
      criteriaError.value = !list.length
    })
    .catch(() => {
      criteriaError.value = true
    })
  return loading
}

export interface CellStatus {
  kind: CoverageKind
  /** Measured on the test set (only when the backend says so). */
  evaluated: boolean
}

/** Honest status of one criterion: planned (not implemented) is never shown as covered. */
export function cellStatus(code: string, scan?: Scan | null): CellStatus {
  const info = criteriaInfo.value?.get(code)
  const fromScan = scan?.coverage?.[code]
  if (fromScan === 'planned') return { kind: 'planned', evaluated: false }
  const method = info?.method ?? fromScan ?? null
  if (!method) return { kind: 'unknown', evaluated: false }
  if (method === 'human') return { kind: 'human', evaluated: false }
  if (info && info.implemented === false) return { kind: 'planned', evaluated: false }
  return { kind: method, evaluated: info?.evaluated === true }
}

/** Criteria a person must check: human ones, planned ones and unknown ones. */
export function needsPerson(code: string, scan?: Scan | null): boolean {
  const k = cellStatus(code, scan).kind
  return k === 'human' || k === 'planned' || k === 'unknown'
}

/**
 * N in "Klar. pre-checks N of 50": `stats.criteria_checked` of the scan when present,
 * otherwise the number of implemented automatable criteria in the registry.
 */
export function checkedCount(scan?: Scan | null): number | null {
  const cc = scan?.stats?.criteria_checked
  if (Array.isArray(cc)) return cc.length
  if (typeof cc === 'number') return cc
  const info = criteriaInfo.value
  if (!info) return null
  const n = CRITERIA.filter((c) => {
    const i = info.get(c.code)
    return i && i.method !== 'human' && i.method !== 'planned' && i.implemented
  }).length
  // Without a measured number, never print "0 of 50" next to real findings.
  return n > 0 ? n : null
}

export function implementedCount(): number | null {
  const info = criteriaInfo.value
  if (!info) return null
  return [...info.values()].filter((c) => c.implemented === true && c.method !== 'human').length
}
