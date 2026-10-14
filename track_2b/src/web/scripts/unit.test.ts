/**
 * Unit checks for the "unknown is not 0" rule (FE-1) and the other no-invented-defaults
 * rules of the API boundary. Bundled and run by scripts/unit.mjs (part of `npm run check`).
 */
import { normaliseCriteria, normaliseHealth, normaliseStats } from '../src/api/normalise'
import { aiCounterText, leftNetwork, leftNetworkLabel } from '../src/lib/sovereignty'
import { setLocale } from '../src/i18n'
import { classifyHttpStatus, classifyScanError, classifyStartError, renderProblem } from '../src/lib/errors'
import { compareSections, groupFindings, reviewProgress } from '../src/lib/group'
import { rowTitle } from '../src/lib/finding-text'
import { apertusAnswers, runNotes } from '../src/lib/notes'
import { scanTitle } from '../src/lib/format'
import { guideFor } from '../src/data/human-guides'
import type { Finding } from '../src/types'

let failed = 0
function check(name: string, ok: boolean, got?: unknown) {
  if (ok) console.log(`  ok   ${name}`)
  else {
    failed++
    console.error(`  FAIL ${name}${got === undefined ? '' : ` (got ${JSON.stringify(got)})`}`)
  }
}

await setLocale('en')

// 1. Health without ai_requests: the counter says "unknown", never 0.
const bare = normaliseHealth({ mode: 'local', model: 'swiss-ai/Apertus-v1.5-8B', version: '0.1.0' })
check('health without ai_requests → null', bare.ai_requests === null, bare.ai_requests)
const c1 = aiCounterText(bare.mode, bare.ai_requests, 'vLLM')
check('counter text says unknown', /unknown/.test(c1.text), c1.text)
check('counter text has no 0', !/:\s*0\b/.test(c1.text), c1.text)
check('counter is not marked as measured', c1.measured === false)

// 2. Partial counters: a missing destination makes the total unknown.
const partial = normaliseHealth({ mode: 'swiss_cloud', model: 'x', ai_requests: { external: 0 } })
check('partial ai_requests keeps missing fields null', partial.ai_requests?.swiss_cloud === null, partial.ai_requests)
check('partial total is unknown', leftNetwork(partial.ai_requests) === null)
check('partial label says unknown', leftNetworkLabel(partial.ai_requests) === 'unknown', leftNetworkLabel(partial.ai_requests))

// 3. Reported zeros are a real measurement and are shown as 0.
const full = normaliseHealth({ mode: 'local', model: 'x', ai_requests: { local: 12, swiss_cloud: 0, external: 0 } })
const c3 = aiCounterText(full.mode, full.ai_requests, 'vLLM')
check('reported zeros → 0', leftNetwork(full.ai_requests) === 0)
check('reported zeros are measured', c3.measured === true && /: 0$/.test(c3.text), c3.text)

// 4. Scan stats without ai_requests stay unknown.
const stats = normaliseStats({ llm_calls: 3 })
check('stats without ai_requests → absent', stats.ai_requests === undefined, stats.ai_requests)
check('stats label says unknown', leftNetworkLabel(stats.ai_requests) === 'unknown')

// 5. No invented defaults for vision, vision_source, json_schema, level.
check('vision missing → null', bare.vision === null, bare.vision)
check('vision_source missing → null (not "pending")', bare.vision_source === null, bare.vision_source)
check('json_schema missing → null', bare.json_schema === null, bare.json_schema)
const crit = normaliseCriteria([{ number: '2.4.4', name: 'Link Purpose', method: 'apertus_text' }])
check('criterion level missing → null (not "A")', crit[0]?.level === null, crit[0]?.level)
check('criterion implemented missing → false (never claimed)', crit[0]?.implemented === false)

// 6. German says "unbekannt".
await setLocale('de')
check('DE counter says unbekannt', /unbekannt/.test(aiCounterText('local', null, 'vLLM').text))
await setLocale('en')

// 7. Start errors (UX-9, M11–M19): classified from today's 422 detail strings.
const se = (s: number, d: string) => classifyStartError(s, d, 'x.example').id
check('M11 private', se(422, "url not allowed: 192.168.1.1 is a private address (192.168.1.1); set KLAR_ALLOW_PRIVATE_NETWORKS=1 to allow") === 'M11')
check('M12 blocked', se(422, 'url not allowed: x resolves to a blocked address 169.254.169.254') === 'M12')
check('M13 loopback', se(422, 'url not allowed: 127.0.0.1 is a loopback address (127.0.0.1)') === 'M13')
check('M13 primary = paste HTML', classifyStartError(422, 'is a loopback address', '').primary === 'pasteHtml')
check("M14 dns", se(422, "url not allowed: host 'nope.example' does not resolve") === 'M14')
check('M15 other 422', se(422, 'url not allowed: scheme ftp') === 'M15')
check('M16 413', se(413, 'html is larger than 2097152 bytes') === 'M16')
check('M17 429 auto-retries once after 15 s', classifyStartError(429, 'queue full', '').autoRetry === 15)
check('M18 network', se(0, 'Network error') === 'M18')
check('M19 5xx', se(502, 'Bad Gateway') === 'M19')

// 8. Failed scans (UX-6, M20–M26): error_code first, regexes on stats.error as fallback.
const fe = (stats: Record<string, unknown>, n = 0) => classifyScanError(stats as never, 'x.example', n, 'abc').id
check('error_code tls → M20 (even with an unrelated text)', fe({ error_code: 'tls', error: 'whatever' }) === 'M20')
check('error_code dns → M14', fe({ error_code: 'dns' }) === 'M14')
check('error_code blocked_private → M11', fe({ error_code: 'blocked_private' }) === 'M11')
check('fallback net::ERR_FAILED → M20', fe({ error: 'Error: Page.goto: net::ERR_FAILED at https://x' }) === 'M20')
check('fallback Timeout 30000ms → M21', fe({ error: 'TimeoutError: Page.goto: Timeout 30000ms exceeded.' }) === 'M21')
check('fallback BlockedURL redirect → M22', fe({ error: 'BlockedURL: redirect: 10.0.0.1 is a private address' }) === 'M22')
check('fallback too many redirects → M23', fe({ error: 'BlockedURL: too many redirects' }) === 'M23')
check('fallback download → M24', fe({ error: 'Error: Download is starting' }) === 'M24')
const tmo = classifyScanError({ error: 'ScanTimeout: scan exceeded KLAR_SCAN_TIMEOUT (900 s)' } as never, 'x', 7, 'abc')
check('ScanTimeout → M25, partial report when findings exist, 15 minutes', tmo.id === 'M25' && tmo.primary === 'partial' && tmo.params.minutes === 15)
check('ScanTimeout without findings → retry', classifyScanError({ error_code: 'scan_timeout' } as never, 'x', 0, 'a').primary === 'retry')
check('unknown → M26 with the scan id in details', fe({ error: 'RuntimeError: boom' }) === 'M26' && /scan abc/.test(classifyScanError({ error: 'x' } as never, '', 0, 'abc').details ?? ''))
check('M27 for 404 only', classifyHttpStatus(404, 'x')?.params.status === '404 Not Found' && classifyHttpStatus(200, 'x') === null && classifyHttpStatus(null, 'x') === null)

// 9. Grouping and review scope (UX-3, UX-4).
const mk = (o: Partial<Finding>): Finding =>
  ({ id: Math.random().toString(36), criterion: '1.1.1', outcome: 'cantTell', reason_code: 'not_recorded', excerpt: 'a', user_impact: 'u', explanation: 'e', status: 'to_review', confidence: 'low', ...o }) as Finding
const notes9 = groupFindings([mk({ excerpt: '<img alt="">' }), mk({ excerpt: '<img src=x>' }), mk({ reason_code: 'budget' })])
check('notes with the same reason group regardless of the quote', notes9.length === 2 && notes9[0]!.items.length === 2)
const rp = reviewProgress([mk({}), mk({ outcome: 'failed', status: 'accepted' }), mk({ outcome: 'passed' })])
check('review scope = failed + cantTell only', rp.total === 2 && rp.done === 1, rp)
const order = [
  { code: '1.1.1', failed: 0, cantTell: 9 },
  { code: '2.4.4', failed: 3, cantTell: 0 },
  { code: '3.1.2', failed: 3, cantTell: 1 },
].sort((a, b) => compareSections(a, b, (x, y) => x.localeCompare(y)))
check('sections sorted by failed, then cantTell', order.map((s) => s.code).join() === '3.1.2,2.4.4,1.1.1', order)
check('note row title by reason_code', rowTitle(mk({}), 'de').text === 'No recorded Apertus answer: check it yourself')
check('axe row title = text after ": "', rowTitle(mk({ outcome: 'failed', reason_code: 'axe', explanation: 'axe-core rule “link-in-text-block”: Links must be distinguishable' }), 'en').text === 'Links must be distinguishable')

// 10. Run notes (UX-2) and the answers counter.
const n10 = runNotes({ stats: { not_recorded: 4, llm_errors: 22, asked_apertus: 22, budget_skipped: { '1.1.1': 3 } } } as never, [], false)
check('N1b before N2 before N3', n10.map((n) => n.id).join() === 'N1b,N2,N3', n10.map((n) => n.id))
check('N2 all failed → bold title', n10[1]!.title === 'notes.llm.allTitle')
check('no notes on a clean run', runNotes({ stats: { not_recorded: 0, llm_errors: 0 } } as never, [], true).length === 0)
check('answers = asked − errors − not recorded', JSON.stringify(apertusAnswers({ asked_apertus: 30, llm_errors: 2, not_recorded: 3 })) === '{"answered":25,"asked":30}')
check('answers: nothing asked → null ("none needed")', apertusAnswers({ asked_apertus: 0 }) === null)

// 11. Report title (UX-11).
check('title from stats.page_title', scanTitle({ url: 'http://127.0.0.1:8090/demo/', stats: { page_title: 'Gemeinde Musterwil' }, progress: [] }).title === 'Gemeinde Musterwil')
check('title from render detail when not a URL', scanTitle({ url: 'https://a.example/x', stats: {}, progress: [{ step: 'render', state: 'done', detail: 'Steuern', started_at: null, duration_ms: null, current: null, total: null }] }).title === 'Steuern')
check('render detail that is a URL is ignored', scanTitle({ url: 'https://a.example/x', stats: {}, progress: [{ step: 'render', state: 'done', detail: 'https://a.example/x', started_at: null, duration_ms: null, current: null, total: null }] }).title === 'a.example/x')
check('pasted HTML without title → null (UI says "Pasted HTML")', scanTitle({ url: 'inline:html', stats: {}, progress: [] }).title === null)

// 12. UX-7: no guide states what Klar. does, in any language.
for (const lang of ['en', 'de', 'fr', 'it'] as const) {
  const bad = ['1.3.2', '1.4.1', '2.4.7', '3.2.3', '3.3.4', '9.9.9'].filter((c) => /Klar/.test(guideFor(c, lang).why))
  check(`guides never claim Klar. capabilities (${lang})`, bad.length === 0, bad)
}

// 13. FE-4: timeout note, budget limit, new reason titles, specific titles for check notes.
const nt = runNotes({ stats: { timeout_notes: 12, timeout_skipped_checks: ['2.4.4', '3.1.2'] } } as never, [], true)
check('timeout note with elements and criteria', nt[0]?.id === 'NT' && nt[0].text === 'notes.timeoutBoth' && nt[0].count === 12 && nt[0].params.criteria === '2.4.4, 3.1.2', nt[0])
check('timeout note offers "Run again"', nt[0]?.actions[0]?.kind === 'runAgain')
check('timeout note with criteria only', runNotes({ stats: { timeout_notes: 0, timeout_skipped_checks: ['1.1.1'] } } as never, [], true)[0]?.text === 'notes.timeoutCrit')
check('N3 uses max_llm_calls when present', runNotes({ stats: { budget_skipped: { '1.1.1': 2 }, max_llm_calls: 150 } } as never, [], true)[0]?.text === 'notes.budgetMax')
check('row title: language switch link', rowTitle(mk({ outcome: 'passed', reason_code: 'language_switcher', user_impact: 'x' }), 'en').text === 'Language switch link')
check('row title: phone number link', rowTitle(mk({ outcome: 'passed', reason_code: 'phone_number', user_impact: 'x' }), 'en').text === 'Phone number link')
const g245 = rowTitle(
  mk({ criterion: '2.4.5', reason_code: 'needs_url', user_impact: 'A person must decide whether this element is a barrier.', explanation: 'Multiple ways concern a set of pages; pasted HTML has no site around it. Scan the page by its address.' }),
  'en',
)
check('generic impact → first sentence of the specific explanation', g245.text === 'Multiple ways concern a set of pages; pasted HTML has no site around it.', g245.text)
const tm = renderProblem(classifyScanError({ error_code: 'scan_timeout', error: 'scan exceeded KLAR_SCAN_TIMEOUT (12 s)' } as never, 'x', 3, 'a'))
check('timeout limit in words (12 seconds)', /after 12 seconds\./.test(tm.body), tm.body)
check('timeout limit in words (15 minutes)', /after 15 minutes\./.test(renderProblem(classifyScanError({ error_code: 'scan_timeout', error: '(900 s)' } as never, 'x', 3, 'a')).body))

if (failed) {
  console.error(`unit: ${failed} check(s) failed`)
  process.exit(1)
}
console.log('unit: OK')
