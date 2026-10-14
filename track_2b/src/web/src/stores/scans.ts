/**
 * Scan cache shared by the scan-in-progress and report views, so navigating
 * from one to the other is instant. Applies SSE events idempotently.
 */
import { reactive } from 'vue'
import { api } from '@/api'
import type { Finding, ProgressStep, Scan, Status } from '@/types'

export const scans = reactive(new Map<string, Scan>())

export async function loadScan(id: string, force = false): Promise<Scan> {
  const cached = scans.get(id)
  if (cached && !force && cached.state === 'done') return cached
  const fresh = await api().getScan(id)
  scans.set(id, fresh)
  return scans.get(id)!
}

export function applyProgress(scan: Scan, data: ProgressStep | ProgressStep[]): void {
  const list = Array.isArray(data) ? data : [data]
  if (Array.isArray(data) && data.length > 0) {
    scan.progress = data.map((s) => ({ ...s }))
    return
  }
  for (const step of list) {
    const i = scan.progress.findIndex((s) => s.step === step.step)
    if (i >= 0) scan.progress[i] = { ...scan.progress[i], ...step }
    else scan.progress.push({ ...step })
  }
  if (scan.state === 'queued') scan.state = 'running'
}

export function applyFinding(scan: Scan, finding: Finding): void {
  const i = scan.findings.findIndex((f) => f.id === finding.id)
  if (i >= 0) scan.findings[i] = finding
  else scan.findings.push(finding)
}

/** SSE `done` carries `{scan_id, state}`; the caller refetches the full Scan afterwards. */
export function applyDone(scan: Scan, data: Partial<Scan> & { scan_id?: string }): void {
  scan.state = data.state ?? 'done'
  if (data.stats) scan.stats = data.stats
  if (data.progress?.length) scan.progress = data.progress
  if (data.findings?.length) for (const f of data.findings) applyFinding(scan, f)
}

export async function setStatus(finding: Finding, status: Exclude<Status, 'to_review'>): Promise<Finding> {
  const previous = finding.status
  finding.status = status // optimistic
  try {
    const updated = await api().patchFinding(finding.id, { status })
    finding.status = updated.status ?? status
    return finding
  } catch (e) {
    finding.status = previous
    throw e
  }
}
