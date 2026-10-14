import type { Health, Mode, Scan } from '@/types'

/** "swiss-ai/Apertus-v1.5-8B" → "Apertus v1.5 8B"; "inference-apertus-v15-70b" → "Apertus v1.5 70B". */
export function prettyModel(model: string | null | undefined): string {
  if (!model) return '—'
  const name = model.split('/').pop() ?? model
  const m = name.match(/apertus[-_ ]?v?(\d)(?:[._]?(\d+))?[-_ ](\d+)\s*b/i)
  if (m) return `Apertus v${m[1]}${m[2] ? `.${m[2]}` : ''} ${m[3]}B`
  return name.replace(/-/g, ' ')
}

export function isApertus(model: string | null | undefined): boolean {
  return !!model && /apertus/i.test(model)
}

const PROVIDERS: Record<string, string> = { phoeniqs: 'Phoeniqs', cscs: 'CSCS', vllm: 'vLLM', llamacpp: 'llama.cpp' }

/** Display name of Health.provider ("phoeniqs" | "cscs" | "vllm" | "llamacpp"), else derived from the host. */
export function providerName(provider: string | null | undefined, host?: string | null): string {
  if (provider) return PROVIDERS[provider.toLowerCase()] ?? provider
  if (!host) return '—'
  if (/phoeniqs\.com$/i.test(host)) return 'Phoeniqs'
  if (/cscs\.ch$/i.test(host)) return 'CSCS'
  return host
}

export const MODE_SHAPE: Record<Mode, 'square' | 'diamond' | 'ring'> = {
  local: 'square',
  swiss_cloud: 'square',
  external: 'diamond',
  replay: 'ring',
}

export const MODE_COLOR: Record<Mode, string> = {
  local: 'var(--green)',
  swiss_cloud: 'var(--ink)',
  external: 'var(--amber)',
  replay: 'var(--grey-shape)',
}

export function modeOf(h: Health | null): Mode | null {
  return h?.mode ?? null
}

/** "http://localhost:8080/demo/de/kontakt.html" → "localhost:8080/demo/de/kontakt.html" */
export function shortUrl(url: string): string {
  try {
    const u = new URL(url)
    const path = u.pathname === '/' ? '' : u.pathname
    return `${u.host}${path}${u.search}`
  } catch {
    return url
  }
}

/** Path relative to a base URL when possible ("de/kontakt.html"). */
export function pagePath(url: string, base?: string): string {
  try {
    const u = new URL(url)
    if (base) {
      const b = new URL(base)
      if (u.host === b.host && u.pathname.startsWith(b.pathname)) return u.pathname.slice(b.pathname.length) || '/'
    }
    return u.pathname || '/'
  } catch {
    return url
  }
}

export function seconds(ms: number | null | undefined, digits = 1): string {
  if (ms == null || !Number.isFinite(ms)) return '—'
  return `${(ms / 1000).toFixed(digits)} s`
}

/** A check of pasted HTML or an uploaded file (the server stores "inline:html"). */
export function isPasted(url: string | null | undefined): boolean {
  return !url || !/^https?:\/\//i.test(url)
}

const looksLikeUrl = (s: string) =>
  /^[a-z][a-z0-9+.-]*:\/\//i.test(s) || /^inline[: ]/i.test(s) || /^[\w.-]+\.[a-z]{2,}(:\d+)?(\/|$)/i.test(s)

/**
 * The report's H1 (UX-11): the page title when the server knows it (stats.page_title,
 * else the render step's detail when that is not a URL), otherwise the short URL.
 * `url` is the address for the linked subline (null for pasted HTML).
 */
export function scanTitle(scan: Pick<Scan, 'url' | 'stats' | 'progress'>): { title: string | null; url: string | null; pasted: boolean } {
  const pasted = isPasted(scan.url)
  const fromStats = typeof scan.stats?.page_title === 'string' ? scan.stats.page_title.trim() : ''
  const render = scan.progress?.find((p) => p.step === 'render')
  const fromStep = render?.state === 'done' && render.detail && !looksLikeUrl(render.detail.trim()) ? render.detail.trim() : ''
  const title = fromStats || fromStep || null
  const finalUrl = typeof scan.stats?.final_url === 'string' && /^https?:/i.test(scan.stats.final_url) ? scan.stats.final_url : null
  const url = pasted ? null : (finalUrl ?? scan.url)
  return { title: title ?? (pasted ? null : shortUrl(url!)), url, pasted }
}

/** Whether a scan's findings span more than one page (then rows show their page path). */
export function pageCount(findings: { page_url: string }[]): number {
  return new Set(findings.map((f) => f.page_url)).size
}
