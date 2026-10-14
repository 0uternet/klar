/**
 * Mock-up data only (dev server or `npm run build:demo`), never in production builds.
 * Methods and implemented checks mirror `klar/checks/registry.py` (1.1.1, 2.4.4,
 * 3.1.2); `evaluated` marks 2.4.4 and 3.1.2. Real values come from GET /api/criteria.
 */
import type { CriterionInfo, Method, Principle } from '@/types'
import { CRITERIA, understandingUrl } from '@/data/wcag'

/** Grep target: this string must never appear in a production build (P0-5b). */
export const MOCK_SENTINEL = 'MOCK_SENTINEL: Klar. mock-up data, not a real scan'

const T: Method = 'apertus_text'
const V: Method = 'apertus_vision'
const R: Method = 'rule'
const H: Method = 'human'
const X: Method = 'experimental'

const REGISTRY: Record<string, [Method, string | null]> = {
  '1.1.1': [V, 'qt1vmo'], '1.2.1': [X, null], '1.2.2': [X, 'eac66b'], '1.2.3': [H, null], '1.2.4': [H, null],
  '1.2.5': [H, null], '1.3.1': [V, null], '1.3.2': [V, null], '1.3.3': [T, null], '1.3.4': [R, 'b33eff'],
  '1.3.5': [T, '73f2c2'], '1.4.1': [V, null], '1.4.2': [R, '80f0bf'], '1.4.3': [V, 'afw4f7'], '1.4.4': [V, 'b4f0c3'],
  '1.4.5': [V, null], '1.4.10': [V, '59br37'], '1.4.11': [V, null], '1.4.12': [V, '24afc2'], '1.4.13': [H, null],
  '2.1.1': [R, '0ssw9k'], '2.1.2': [R, '80af7b'], '2.1.4': [H, null], '2.2.1': [H, 'bc659a'], '2.2.2': [V, null],
  '2.3.1': [H, null], '2.4.1': [R, 'cf77f2'], '2.4.2': [T, 'c4a8a4'], '2.4.3': [V, null], '2.4.4': [T, '5effbb'],
  '2.4.5': [T, null], '2.4.6': [T, 'b49b2e'], '2.4.7': [R, 'oj04fd'], '2.5.1': [H, null], '2.5.2': [H, null],
  '2.5.3': [T, '2ee8b8'], '2.5.4': [H, null], '3.1.1': [T, 'ucwvc8'], '3.1.2': [T, 'off6ek'], '3.2.1': [R, null],
  '3.2.2': [T, null], '3.2.3': [T, null], '3.2.4': [T, null], '3.3.1': [T, '36b590'], '3.3.2': [T, null],
  '3.3.3': [T, null], '3.3.4': [T, null], '4.1.1': [R, null], '4.1.2': [T, 'e086e5'], '4.1.3': [H, null],
}

/** Same as the backend registry today: three check modules. */
export const MOCK_IMPLEMENTED = ['1.1.1', '2.4.4', '3.1.2']
const MOCK_EVALUATED = ['2.4.4', '3.1.2']

const PRINCIPLE: Principle[] = ['perceivable', 'operable', 'understandable', 'robust']

/** Contract v2: method is the registry method if implemented, "human" stays human, otherwise "planned". */
export const MOCK_CRITERIA: CriterionInfo[] = CRITERIA.map((c) => {
  const [registryMethod, act] = REGISTRY[c.code] ?? [H, null]
  const implemented = MOCK_IMPLEMENTED.includes(c.code)
  const method: Method = registryMethod === H ? H : implemented ? registryMethod : 'planned'
  return {
    criterion: c.code,
    name: c.title,
    level: c.level,
    principle: PRINCIPLE[c.principle - 1]!,
    method,
    implemented,
    evaluated: MOCK_EVALUATED.includes(c.code),
    act_rule: act,
    en301549: `9.${c.code}`,
    url: understandingUrl(c.code),
  }
})
