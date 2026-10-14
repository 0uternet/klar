/**
 * Client-side exports (mock mode). The real backend serves these from
 * GET /api/scans/{id}/export?format=…; the shapes here mirror what it should produce.
 */
import { TOTAL_CRITERIA } from '@/config'
import { criterion as wcag } from '@/data/wcag'
import type { ExportFormat, Finding, Scan } from '@/types'

const EARL_OUTCOME: Record<Finding['outcome'], string> = {
  failed: 'earl:failed',
  cantTell: 'earl:cantTell',
  passed: 'earl:passed',
  inapplicable: 'earl:inapplicable',
}

/** N of "pre-checks N of 50": the criteria this scan actually checked. */
export function precheckedCount(scan: Scan): number | null {
  const cc = scan.stats?.criteria_checked
  if (Array.isArray(cc)) return cc.length
  return typeof cc === 'number' ? cc : null
}

function csvCell(v: unknown): string {
  let s = v == null ? '' : String(v)
  // Formula-injection guard: page text must never become a spreadsheet formula.
  if (/^[=+\-@\t\r]/.test(s)) s = `'${s}`
  return /[",\n\r;]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}

function toCsv(scan: Scan): string {
  const cols: (keyof Finding)[] = [
    'id', 'criterion', 'criterion_name', 'level', 'outcome', 'status', 'source', 'confidence', 'page_url', 'selector',
    'excerpt', 'user_impact', 'explanation', 'fix_hint', 'act_rule', 'en301549', 'model',
  ]
  const rows = scan.findings.map((f) => cols.map((c) => csvCell(f[c])).join(','))
  // BOM so that spreadsheet apps open umlauts correctly.
  return '﻿' + [cols.join(','), ...rows].join('\r\n') + '\r\n'
}

function toEarl(scan: Scan): string {
  const doc = {
    '@context': {
      earl: 'http://www.w3.org/ns/earl#',
      dct: 'http://purl.org/dc/terms/',
      foaf: 'http://xmlns.com/foaf/0.1/',
      ptr: 'http://www.w3.org/2009/pointers#',
      WCAG21: 'https://www.w3.org/TR/WCAG21/#',
      klar: 'urn:klar:',
    },
    '@graph': scan.findings.map((f) => ({
      '@type': 'earl:Assertion',
      'earl:assertedBy': {
        '@type': ['earl:Assertor', 'earl:Software'],
        'dct:title': 'Klar.',
        'dct:description': f.source === 'apertus' ? `Klar. with ${f.model ?? scan.model}` : `Klar. (${f.source})`,
      },
      'earl:subject': { '@id': f.page_url, '@type': 'earl:TestSubject' },
      'earl:test': { '@id': `WCAG21:${wcag(f.criterion)?.slug ?? f.criterion}`, 'dct:title': `${f.criterion} ${f.criterion_name}` },
      'earl:mode': { '@id': f.status === 'to_review' ? (f.source === 'apertus' ? 'earl:semiAuto' : 'earl:automatic') : 'earl:semiAuto' },
      'earl:result': {
        '@type': 'earl:TestResult',
        'earl:outcome': { '@id': EARL_OUTCOME[f.outcome] },
        'earl:pointer': { '@type': 'ptr:CSSSelectorPointer', 'ptr:expression': f.selector },
        'earl:info': f.explanation,
        'dct:date': scan.created_at,
        'klar:status': f.status,
        'klar:confidence': f.confidence,
        'klar:excerpt': f.excerpt,
      },
    })),
  }
  return JSON.stringify(doc, null, 2)
}

const ESC: Record<string, string> = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }
const esc = (s: unknown) => String(s ?? '').replace(/[&<>"']/g, (c) => ESC[c] ?? c)

function toHtml(scan: Scan): string {
  const counts = { failed: 0, cantTell: 0, passed: 0, inapplicable: 0 }
  for (const f of scan.findings) counts[f.outcome]++
  const label = { failed: '■ Failed', cantTell: '◆ Needs review', passed: '● Passed', inapplicable: '○ N/A' }
  const rows = scan.findings
    .map(
      (f) => `<tr><td><code>${esc(f.criterion)}</code><br>${esc(f.criterion_name)}</td><td>${esc(label[f.outcome])}</td>
<td>${esc(f.user_impact)}<br><small>${esc(f.page_url)} · <code>${esc(f.selector)}</code></small></td><td>${esc(f.status)}</td></tr>`,
    )
    .join('\n')
  const n = precheckedCount(scan)
  const disclaimer =
    n === null
      ? 'Klar. pre-checks a subset of the 50 WCAG 2.1 AA criteria. This report does not certify conformance.'
      : `Klar. pre-checks ${n} of ${TOTAL_CRITERIA} WCAG 2.1 AA criteria. This report does not certify conformance.`
  const mock = typeof scan.stats?.mock === 'string' ? '<p class="d"><strong>Mock-up data — not a real scan.</strong></p>' : ''
  return `<!doctype html>
<html lang="${esc(scan.ui_lang)}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'">
<title>Klar. report – ${esc(scan.url)}</title>
<style>body{font:16px/1.5 system-ui,sans-serif;max-width:1000px;margin:40px auto;padding:0 16px;color:#0f1115;background:#fafaf7}
h1{font-size:28px;letter-spacing:-.02em}.d{border-left:4px solid #d0021b;padding:8px 16px;background:#fff}
table{border-collapse:collapse;width:100%;background:#fff}td,th{border-top:1px solid #e4e2dc;padding:8px;text-align:left;vertical-align:top}
code{font-family:ui-monospace,monospace;font-size:.9em}small{color:#565b66}</style></head>
<body><h1>Klar<span style="color:#d0021b">.</span> report</h1>
<p>${esc(scan.url)} · ${esc(new Date(scan.created_at).toISOString())} · ${esc(scan.mode)} · ${esc(scan.model)}</p>
${mock}<p class="d">${esc(disclaimer)}</p>
<p>Failed: ${counts.failed} · Needs review: ${counts.cantTell} · Passed: ${counts.passed} · N/A: ${counts.inapplicable}</p>
<table><thead><tr><th scope="col">Criterion</th><th scope="col">Outcome</th><th scope="col">Finding</th><th scope="col">Status</th></tr></thead>
<tbody>${rows}</tbody></table></body></html>`
}

export function exportFile(scan: Scan, format: ExportFormat): { name: string; type: string; body: string } {
  let host = 'scan'
  try {
    host = new URL(scan.url).host.replace(/[^a-z0-9.-]/gi, '-') || 'scan'
  } catch {
    /* not a URL (pasted HTML) */
  }
  const stamp = scan.created_at.slice(0, 10)
  const name = `klar-${host}-${stamp}`
  switch (format) {
    case 'json':
      return { name: `${name}.json`, type: 'application/json', body: JSON.stringify(scan, null, 2) }
    case 'earl':
      return { name: `${name}.earl.jsonld`, type: 'application/ld+json', body: toEarl(scan) }
    case 'csv':
      return { name: `${name}.csv`, type: 'text/csv;charset=utf-8', body: toCsv(scan) }
    case 'html':
      return { name: `${name}.html`, type: 'text/html;charset=utf-8', body: toHtml(scan) }
  }
}

export function download(name: string, type: string, body: string): void {
  const url = URL.createObjectURL(new Blob([body], { type }))
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
