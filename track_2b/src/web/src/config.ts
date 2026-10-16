/** App-wide constants. Values prefixed VITE_ can be overridden at build time. */

/**
 * The bundled demo site (data/demo-site), served by the Klar. container at /demo/.
 * In production the UI is served by the same container, so the demo lives on the
 * same origin; the dev server (port 5173) points at the API container on :8080.
 */
export const DEMO_URL: string =
  import.meta.env.VITE_DEMO_URL ??
  (import.meta.env.DEV ? 'http://localhost:8080/demo/' : new URL('demo/', `${location.origin}/`).toString())

/**
 * Real Swiss pages whose Apertus answers ship with the replay recordings (data/replay), so a
 * visitor without a model endpoint can still see Apertus at work on the live web. If a page
 * changed since the recording, its new elements go to a person ("not recorded").
 */
export const REAL_SAMPLES: readonly { url: string; host: string; who: string }[] = [
  { url: 'https://www.ebgb.admin.ch/de', host: 'ebgb.admin.ch', who: 'home.real.ebgb' },
  { url: 'https://www.biel-bienne.ch/de', host: 'biel-bienne.ch', who: 'home.real.biel' },
]

export function isRealSample(url: string): boolean {
  const norm = (u: string) => u.replace(/\/+$/, '').toLowerCase()
  return REAL_SAMPLES.some((s) => norm(s.url) === norm(url))
}

/** True for pages of the bundled demo site (the only site with recorded replay answers). */
export function isDemoUrl(url: string): boolean {
  try {
    const u = new URL(url)
    return u.pathname.startsWith('/demo/') && ['localhost', '127.0.0.1', '[::1]', location.hostname].includes(u.hostname)
  } catch {
    return false
  }
}
export const DEMO_NAME = 'Gemeinde Musterwil'

/** Base path of the HTTP API. */
export const API_BASE: string = import.meta.env.VITE_API_BASE ?? '/api'

/** How long to wait for GET /api/health before showing the "server unreachable" state. */
export const HEALTH_TIMEOUT_MS = 2500

/** WCAG 2.1 level A + AA success criteria. */
export const TOTAL_CRITERIA = 50

export const APP_VERSION = '0.1.0'

/** Pasted HTML / dropped file size limit. */
export const MAX_HTML_BYTES = 2_000_000 // = KLAR_MAX_HTML_BYTES (server default)

export const STORAGE = {
  theme: 'klar.theme',
  lang: 'klar.lang',
  shortcuts: 'klar.shortcuts',
  humanChecks: 'klar.human',
  mock: 'klar.mock',
  mockScans: 'klar.mockScans',
} as const
