/**
 * HTTP implementation of the Klar. API (routes in `klar/api/app.py`).
 * Same origin only: the UI is served by FastAPI, so no CORS and no third party.
 */
import { API_BASE } from '@/config'
import type { ExportFormat, ScanControlState } from '@/types'
import { normaliseCriteria, normaliseFinding, normaliseHealth, normaliseScan, normaliseScanList, normaliseStep } from './normalise'
import { ApiError, type KlarApi } from './types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: { Accept: 'application/json', ...(init?.body ? { 'Content-Type': 'application/json' } : {}), ...init?.headers },
    })
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') throw e
    throw new ApiError(0, 'Network error')
  }
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`
    try {
      const body = (await res.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') message = body.detail
      else if (Array.isArray(body.detail) && body.detail[0]?.msg) message = String(body.detail[0].msg)
    } catch {
      /* not JSON */
    }
    throw new ApiError(res.status, message)
  }
  return (await res.json()) as T
}

function parse<T>(data: string): T | null {
  try {
    return JSON.parse(data) as T
  } catch {
    return null
  }
}

export const httpApi: KlarApi = {
  kind: 'http',

  async health(signal) {
    return normaliseHealth(await request<unknown>('/health', { signal }))
  },

  async criteria() {
    return normaliseCriteria(await request<unknown>('/criteria'))
  },

  createScan(body) {
    return request('/scans', { method: 'POST', body: JSON.stringify(body) })
  },

  async getScan(id) {
    return normaliseScan(await request<unknown>(`/scans/${encodeURIComponent(id)}`))
  },

  async listScans(limit = 20) {
    return normaliseScanList(await request<unknown>(`/scans?limit=${limit}`))
  },

  async controlScan(id, action) {
    const data = await request<Partial<ScanControlState>>(`/scans/${encodeURIComponent(id)}/${action}`, { method: 'POST' })
    return { paused: data?.paused === true, stopping: data?.stopping === true }
  },

  async patchFinding(id, body) {
    return normaliseFinding(await request<unknown>(`/findings/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(body) }))
  },

  subscribe(id, h) {
    let closed = false
    let pollTimer: number | undefined
    let es: EventSource | null = null
    let finished = false

    // Fallback when SSE is unavailable (proxy buffering, old server): poll the scan.
    const poll = async () => {
      if (closed) return
      try {
        const scan = await httpApi.getScan(id)
        h.onProgress?.(scan.progress)
        for (const f of scan.findings) h.onFinding?.(f) // upserted by id: no duplicates
        if (scan.state === 'done' || scan.state === 'error') {
          finished = true
          h.onDone?.(scan)
          return
        }
      } catch (e) {
        h.onError?.(e instanceof Error ? e.message : String(e))
        return
      }
      pollTimer = window.setTimeout(poll, 1000)
    }

    // Every event carries an `id:`; on reconnect the browser sends Last-Event-ID and the
    // server resumes after it. Findings are upserted by id and steps by name anyway.
    try {
      es = new EventSource(`${API_BASE}/scans/${encodeURIComponent(id)}/events`)
      es.addEventListener('progress', (ev) => {
        const data = parse<unknown>((ev as MessageEvent<string>).data)
        if (data) h.onProgress?.(Array.isArray(data) ? data.map(normaliseStep) : normaliseStep(data))
      })
      es.addEventListener('finding', (ev) => {
        const data = parse<unknown>((ev as MessageEvent<string>).data)
        if (data) h.onFinding?.(normaliseFinding(data))
      })
      es.addEventListener('control', (ev) => {
        const data = parse<Partial<ScanControlState>>((ev as MessageEvent<string>).data)
        if (data) h.onControl?.({ paused: data.paused === true, stopping: data.stopping === true })
      })
      es.addEventListener('done', (ev) => {
        finished = true
        const data = parse<{ scan_id?: string; state?: 'queued' | 'running' | 'done' | 'error' }>((ev as MessageEvent<string>).data) ?? {}
        es?.close()
        h.onDone?.(data)
      })
      // Named server-side error event, if the backend emits one.
      es.addEventListener('scan_error', (ev) => {
        const data = parse<{ message?: string }>((ev as MessageEvent<string>).data)
        h.onError?.(data?.message ?? 'Scan failed')
      })
      es.onerror = () => {
        if (closed || finished) return
        // The browser retries on its own while CONNECTING; on CLOSED, switch to polling.
        if (es?.readyState === EventSource.CLOSED) {
          es = null
          void poll()
        }
      }
    } catch {
      void poll()
    }

    return () => {
      closed = true
      es?.close()
      if (pollTimer) window.clearTimeout(pollTimer)
    }
  },

  /**
   * Fetch, then save the blob, so a server error is reported instead of being
   * saved as a file. Name: klar-{host}-{yyyy-mm-dd}.{ext} (ext from the server's name).
   */
  async exportScan(scan, format: ExportFormat) {
    let res: Response
    try {
      res = await fetch(`${API_BASE}/scans/${encodeURIComponent(scan.id)}/export?format=${format}`)
    } catch {
      throw new ApiError(0, 'Network error')
    }
    if (!res.ok) throw new ApiError(res.status, `${res.status} ${res.statusText}`)
    const blob = await res.blob()
    const served = /filename="?([^";]+)"?/i.exec(res.headers.get('Content-Disposition') ?? '')?.[1] ?? ''
    const ext = served.includes('.') ? served.slice(served.lastIndexOf('.') + 1) : format === 'earl' ? 'jsonld' : format
    let host = 'html'
    try {
      host = /^https?:/i.test(scan.url) ? new URL(scan.url).hostname : 'html'
    } catch {
      /* keep "html" */
    }
    const day = (scan.created_at || new Date().toISOString()).slice(0, 10)
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `klar-${host.replace(/[^\w.-]+/g, '-')}-${day}.${ext}`
    a.rel = 'noopener'
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.setTimeout(() => URL.revokeObjectURL(a.href), 10_000)
  },
}
