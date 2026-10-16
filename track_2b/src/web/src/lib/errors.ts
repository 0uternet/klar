/**
 * Problem classification (UX audit §3, M11–M27): every failure gets a title that
 * says what happened, one plain sentence, one primary action, and the raw text
 * only under "Details". The classifiers are pure (message keys, no translation),
 * so they are unit-tested; `renderProblem` translates at render time.
 */
import type { ErrorCode, ScanStats } from '@/types'
import { formatDuration, formatNumber, t, type MessageKey } from '@/i18n'

/** What a button in an ErrorState does. The view decides how. */
export type ProblemAction = 'edit' | 'retry' | 'pasteHtml' | 'editHtml' | 'partial' | 'anyway'

export interface Problem {
  /** Catalogue id (M11 … M27), kept for tests and logs. */
  id: string
  title: MessageKey
  body: MessageKey
  params: Record<string, string | number>
  /** Technical text, shown only under "Details" (never translated). */
  details: string | null
  /** Extra explanation placed before the raw details (translated). */
  detailsLead?: MessageKey
  primary: ProblemAction
  secondary: ProblemAction[]
  /** Seconds before one automatic retry (M17). */
  autoRetry?: number
}

/** Host of a submitted address, for "{host}" in messages. */
export function hostOf(url: string | null | undefined): string {
  if (!url) return ''
  try {
    return new URL(url).host
  } catch {
    return url
  }
}

/* ---- Starting a check: POST /api/scans (M11–M19) ------------------------------ */

export function classifyStartError(status: number, detail: string, host: string): Problem {
  const raw = detail || null
  const p = (id: string, key: string, primary: ProblemAction, secondary: ProblemAction[] = [], extra: Partial<Problem> = {}): Problem => ({
    id,
    title: `${key}.title` as MessageKey,
    body: `${key}.body` as MessageKey,
    params: { host },
    details: raw,
    primary,
    secondary,
    ...extra,
  })
  if (status === 422 || status === 400) {
    if (/is a private address/i.test(detail)) return p('M11', 'start.private', 'edit', [], { detailsLead: 'start.private.detail' })
    if (/blocked address|metadata|reserved/i.test(detail)) return p('M12', 'start.blocked', 'edit')
    if (/loopback|localhost/i.test(detail)) return p('M13', 'start.loopback', 'pasteHtml', ['edit'])
    if (/does not resolve|not resolve|getaddrinfo|ENOTFOUND/i.test(detail)) return p('M14', 'start.dns', 'edit')
    return p('M15', 'start.invalid', 'edit')
  }
  if (status === 413) return p('M16', 'start.tooLarge', 'editHtml', [], { details: null })
  if (status === 429) return p('M17', 'start.busy', 'retry', [], { autoRetry: 15 })
  if (status === 0) return p('M18', 'start.network', 'retry', [], { details: null })
  return p('M19', 'start.server', 'retry', [], { details: raw ?? `HTTP ${status}` })
}

/* ---- A check that failed while running (M20–M26) ------------------------------ */

/** Fallback for servers without `stats.error_code`: regexes on `stats.error`. */
export function errorCodeFromText(error: string | null | undefined): ErrorCode {
  const e = error ?? ''
  if (/ScanTimeout|KLAR_SCAN_TIMEOUT/.test(e)) return 'scan_timeout'
  if (/Timeout \d+ms exceeded|ERR_TIMED_OUT/.test(e)) return 'timeout_page'
  if (/BlockedURL: redirect/i.test(e)) return 'blocked_redirect'
  if (/too many redirects|ERR_TOO_MANY_REDIRECTS/i.test(e)) return 'too_many_redirects'
  if (/Download is starting|net::ERR_ABORTED/.test(e)) return 'not_html'
  if (/ERR_NAME_NOT_RESOLVED|ENOTFOUND|does not resolve/.test(e)) return 'dns'
  if (/ERR_CERT|ERR_SSL/.test(e)) return 'tls'
  if (/net::ERR_/.test(e)) return 'unreachable'
  return 'internal'
}

/** "scan exceeded KLAR_SCAN_TIMEOUT (900 s)" → 900. */
export function timeoutSeconds(error: string | null | undefined): number | null {
  const m = (error ?? '').match(/\((\d+(?:\.\d+)?)\s*s\)/)
  return m ? Number(m[1]) : null
}

export function classifyScanError(
  stats: Partial<ScanStats> | null | undefined,
  host: string,
  findings: number,
  scanId: string,
): Problem {
  const raw = typeof stats?.error === 'string' ? stats.error : null
  const code: ErrorCode = stats?.error_code ?? errorCodeFromText(raw)
  const base = { params: { host } as Record<string, string | number>, details: raw }
  const p = (id: string, key: string, primary: ProblemAction, secondary: ProblemAction[] = [], extra: Partial<Problem> = {}): Problem => ({
    id,
    title: `${key}.title` as MessageKey,
    body: `${key}.body` as MessageKey,
    ...base,
    primary,
    secondary,
    ...extra,
  })
  switch (code) {
    case 'unreachable':
    case 'tls':
      return p('M20', 'fail.load', 'retry', ['edit'])
    case 'dns':
      return p('M14', 'start.dns', 'edit', ['retry'])
    case 'timeout_page':
      return p('M21', 'fail.slow', 'retry', ['edit'])
    case 'blocked_redirect':
      return p('M22', 'fail.redirect', 'edit')
    case 'blocked_private':
      return p('M11', 'start.private', 'edit', [], { detailsLead: 'start.private.detail' })
    case 'blocked_metadata':
      return p('M12', 'start.blocked', 'edit')
    case 'blocked_localhost':
      return p('M13', 'start.loopback', 'pasteHtml', ['edit'])
    case 'too_many_redirects':
      return p('M23', 'fail.loop', 'edit')
    case 'not_html':
      return p('M24', 'fail.notHtml', 'edit')
    case 'scan_timeout': {
      const s = timeoutSeconds(raw) ?? 900
      return p('M25', 'fail.timeout', findings > 0 ? 'partial' : 'retry', [], {
        params: { host, minutes: Math.max(1, Math.round(s / 60)), seconds: s, k: findings },
        details: `KLAR_SCAN_TIMEOUT=${Math.round(s)}${raw ? `\n${raw}` : ''}`,
      })
    }
    default:
      return p('M26', 'fail.internal', 'retry', [], { details: [raw, `scan ${scanId}`].filter(Boolean).join('\n') })
  }
}

/* ---- A page that answered with an HTTP error (M27, needs stats.http_status) ---- */

const REASONS: Record<number, string> = {
  400: 'Bad Request',
  401: 'Unauthorized',
  403: 'Forbidden',
  404: 'Not Found',
  405: 'Method Not Allowed',
  408: 'Request Timeout',
  410: 'Gone',
  429: 'Too Many Requests',
  500: 'Internal Server Error',
  502: 'Bad Gateway',
  503: 'Service Unavailable',
  504: 'Gateway Timeout',
}

export function classifyHttpStatus(status: number | null | undefined, host: string): Problem | null {
  if (typeof status !== 'number' || status < 400) return null
  const label = REASONS[status] ? `${status} ${REASONS[status]}` : String(status)
  return { id: 'M27', title: 'fail.http.title', body: 'fail.http.body', params: { host, status: label }, details: null, primary: 'edit', secondary: ['anyway'] }
}

/** Translate a problem at render time ("{limit}" = the time limit in words; numbers localised). */
export function renderProblem(p: Problem, extraDetails?: string | null): { title: string; body: string; details: string | null } {
  const params: Record<string, string | number> = { ...p.params }
  if (typeof params.seconds === 'number') params.limit = formatDuration(params.seconds)
  if (typeof params.k === 'number') params.k = formatNumber(params.k)
  return {
    title: t(p.title, params),
    body: t(p.body, params),
    details: [p.detailsLead ? t(p.detailsLead) : null, p.details, extraDetails].filter(Boolean).join('\n') || null,
  }
}
