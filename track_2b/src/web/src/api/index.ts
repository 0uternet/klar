/**
 * API entry point.
 *
 * Honesty rule (P0-5b): the UI never falls back to sample data on its own.
 *  - Production builds talk to the Klar. server only. If GET /api/health fails,
 *    the UI shows an "unreachable" state and no findings.
 *  - Mock-up data exists only in dev and `--mode demo` builds (`__KLAR_MOCKS__`,
 *    see vite.config.ts) and is used only with an explicit `?mock=1`. The mock
 *    module is then loaded on demand; production builds do not contain it.
 */
import { HEALTH_TIMEOUT_MS, STORAGE } from '@/config'
import type { Health } from '@/types'
import { httpApi } from './http'
import type { KlarApi } from './types'

export type DemoReason = 'forced' | null

let current: KlarApi = httpApi

export function api(): KlarApi {
  return current
}

export const MOCKS_AVAILABLE: boolean = __KLAR_MOCKS__

function param(name: string): string | null {
  const fromSearch = new URLSearchParams(location.search).get(name)
  if (fromSearch !== null) return fromSearch
  const q = location.hash.indexOf('?')
  return q >= 0 ? new URLSearchParams(location.hash.slice(q + 1)).get(name) : null
}

/** `?mock=1` turns mock-up mode on for this browser session, `?mock=0` turns it off. */
function mockRequested(): boolean {
  const p = param('mock')
  try {
    if (p === '1' || p === 'true') sessionStorage.setItem(STORAGE.mock, '1')
    if (p === '0' || p === 'false') sessionStorage.removeItem(STORAGE.mock)
    return sessionStorage.getItem(STORAGE.mock) === '1'
  } catch {
    return p === '1' || p === 'true'
  }
}

export type BootResult = { health: Health | null; demo: DemoReason; unreachable: boolean }

export async function boot(): Promise<BootResult> {
  if (__KLAR_MOCKS__ && mockRequested()) {
    const { mockApi } = await import('./mock')
    current = mockApi
    return { health: await mockApi.health(), demo: 'forced', unreachable: false }
  }
  current = httpApi
  const ctrl = new AbortController()
  const timer = window.setTimeout(() => ctrl.abort(), HEALTH_TIMEOUT_MS)
  try {
    const health = await httpApi.health(ctrl.signal)
    if (!health || typeof health.mode !== 'string') throw new Error('Unexpected /api/health response')
    return { health, demo: null, unreachable: false }
  } catch {
    return { health: null, demo: null, unreachable: true }
  } finally {
    window.clearTimeout(timer)
  }
}

/** Leave mock-up mode (and reload, so no mock data stays on screen). */
export function leaveMock(): void {
  try {
    sessionStorage.removeItem(STORAGE.mock)
  } catch {
    /* storage unavailable */
  }
  const url = new URL(location.href)
  url.searchParams.delete('mock')
  url.hash = '#/'
  location.replace(url.toString())
}

export { ApiError } from './types'
export type { KlarApi } from './types'
