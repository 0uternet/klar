<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight } from '@lucide/vue'
import type { Finding, Outcome, Scan, Status } from '@/types'
import { api, ApiError } from '@/api'
import { compareSections, groupFindings, reviewProgress, toReview, type FindingGroup } from '@/lib/group'
import { formatNumber, locale, t, type MessageKey } from '@/i18n'
import { CRITERIA, compareCodes, plainName } from '@/data/wcag'
import { checkedCount, loadCriteria, needsPerson } from '@/stores/criteria'
import { DEMO_URL, isDemoUrl } from '@/config'
import { ensureBooted, lastScanId, modalOpen, unreachable } from '@/stores/app'
import { loadScan, scans, setStatus } from '@/stores/scans'
import { toast } from '@/stores/toast'
import { pageCount, scanTitle } from '@/lib/format'
import { leftNetwork } from '@/lib/sovereignty'
import { reducedMotion } from '@/lib/motion'
import { classifyHttpStatus, classifyScanError, hostOf, renderProblem, type Problem, type ProblemAction } from '@/lib/errors'
import { apertusAnswers, runNotes } from '@/lib/notes'
import { rowTitle } from '@/lib/finding-text'
import { useShortcuts } from '@/composables/useShortcuts'
import { useDocumentTitle } from '@/composables/useDocumentTitle'
import { useRerun } from '@/composables/useRerun'
import CoverageMap from '@/components/CoverageMap.vue'
import FindingDetail from '@/components/FindingDetail.vue'
import EmptyState from '@/components/EmptyState.vue'
import ErrorState from '@/components/ErrorState.vue'
import ReportHeader from '@/components/report/ReportHeader.vue'
import ReportStats from '@/components/report/ReportStats.vue'
import FindingsToolbar from '@/components/report/FindingsToolbar.vue'
import FindingSection from '@/components/report/FindingSection.vue'

const props = defineProps<{ id: string }>()
const route = useRoute()
const router = useRouter()
const { rerun, rerunning, editAddress, pasteHtml } = useRerun()

const scan = computed<Scan | undefined>(() => scans.get(props.id))
const loading = ref(true)
const notFound = ref(false)
const loadError = ref<string | null>(null)

/** H1 = the page title, the URL as a linked fact under it (UX-11). */
const head = computed(() => (scan.value ? scanTitle(scan.value) : null))
const headTitle = computed(() => head.value?.title ?? t('report.pastedHtml'))
/** The address shown under the H1, unless the H1 already is that address. */
const subUrl = computed(() => {
  const h = head.value
  if (!h?.url) return null
  const bare = h.url.replace(/^https?:\/\//, '')
  return h.title && !bare.startsWith(h.title) ? bare : null
})
useDocumentTitle(() => (scan.value ? t('report.docTitle', { url: headTitle.value }) : t('report.eyebrow')))

onMounted(async () => {
  await ensureBooted()
  lastScanId.value = props.id
  void loadCriteria()
  if (typeof route.query.criterion === 'string') filters.criterion = route.query.criterion
  try {
    const s = await loadScan(props.id)
    if (s.state === 'queued' || s.state === 'running') {
      await router.replace({ name: 'scan', params: { id: props.id } })
      return
    }
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound.value = true
    else loadError.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
})

/* ---- Derived data ---------------------------------------------------- */

const findings = computed(() => scan.value?.findings ?? [])
/** N of "pre-check of N of 50": what this scan actually checked (stats.criteria_checked). */
const prechecked = computed(() => checkedCount(scan.value))
const humanCount = computed(() => CRITERIA.filter((c) => needsPerson(c.code, scan.value)).length)
const multiPage = computed(() => pageCount(findings.value) > 1)
const host = computed(() => hostOf(scan.value?.stats?.final_url as string | undefined) || hostOf(scan.value?.url))
const counts = computed(() => {
  const c: Record<Outcome, number> = { failed: 0, cantTell: 0, passed: 0, inapplicable: 0 }
  for (const f of findings.value) c[f.outcome]++
  return c
})
/** UX-4: the review scope is Failed + Needs review; passed rows never need a decision. */
const progress = computed(() => reviewProgress(findings.value))
const remaining = computed(() => progress.value.total - progress.value.done)
/** Who pre-checked the review scope: code (rules and patterns) or Apertus. */
const byApertus = computed(() => findings.value.filter((f) => toReview(f) && f.source === 'apertus').length)
const byCode = computed(() => progress.value.total - byApertus.value)
const seconds = computed(() => {
  const s = scan.value?.stats?.seconds
  if (typeof s === 'number') return s
  const total = scan.value?.progress.reduce((n, p) => n + (p.duration_ms ?? 0), 0) ?? 0
  return total / 1000
})
const left = computed(() => leftNetwork(scan.value?.stats?.ai_requests))
const answers = computed(() => apertusAnswers(scan.value?.stats))
const tokens = computed(() => {
  const s = scan.value?.stats
  return typeof s?.tokens_in === 'number' && typeof s?.tokens_out === 'number' && (s.tokens_in > 0 || s.tokens_out > 0)
    ? `${formatNumber(s.tokens_in)} / ${formatNumber(s.tokens_out)}`
    : null
})

/* ---- Problems and run notes (UX-2, UX-6, UX-23) ------------------------------- */

const notes = computed(() => (scan.value ? runNotes(scan.value, findings.value, isDemoUrl(scan.value.url)) : []))

/** M30: a report of a failed check says why, and that the results are partial. */
const failure = computed<Problem | null>(() =>
  scan.value?.state === 'error' ? classifyScanError(scan.value.stats, host.value, findings.value.length, scan.value.id) : null,
)
/** M27: the page itself answered 4xx/5xx, so Klar. checked an error page. */
const httpDismissed = ref(false)
const httpProblem = computed<Problem | null>(() => (httpDismissed.value || failure.value ? null : classifyHttpStatus(scan.value?.stats?.http_status as number | null, host.value)))

const problemText = (p: Problem) => renderProblem(p)
const ACTION_LABEL: Record<ProblemAction, MessageKey> = {
  edit: 'start.edit',
  retry: 'scan.rerun',
  pasteHtml: 'home.form.pasteHtml',
  editHtml: 'start.editHtml',
  partial: 'scan.rerun',
  anyway: 'fail.http.anyway',
}
function act(a: ProblemAction) {
  if (a === 'edit' || a === 'editHtml') void editAddress(scan.value)
  else if (a === 'pasteHtml') void pasteHtml()
  else if (a === 'anyway') httpDismissed.value = true
  else void rerun(scan.value)
}
/** On a report, "Open the partial report" is where we already are: offer the re-run instead. */
const failurePrimary = computed<ProblemAction | null>(() => (failure.value ? (failure.value.primary === 'partial' ? 'retry' : failure.value.primary) : null))

/** N9: the findings are in the language the check ran in. */
const langDiffers = computed(() => !!scan.value && scan.value.ui_lang !== locale.value)

function checkDemo() {
  void rerun({ url: DEMO_URL })
}

/* ---- Filters --------------------------------------------------------- */

type By = '' | 'code' | 'apertus'
const filters = reactive({ outcome: '' as Outcome | '', criterion: '', by: '' as By, status: '' as Status | '', q: '', reason: '' })
const hasFilters = computed(() => !!(filters.outcome || filters.criterion || filters.by || filters.status || filters.q || filters.reason))
function resetFilters() {
  Object.assign(filters, { outcome: '', criterion: '', by: '', status: '', q: '', reason: '' })
}
function toFindings() {
  void nextTick(() => document.getElementById('rep-findings')?.scrollIntoView({ block: 'start' }))
}
function filterReason(code: string) {
  resetFilters()
  filters.reason = code
  toFindings()
}

const criteriaPresent = computed(() => Array.from(new Set(findings.value.map((f) => f.criterion))).sort(compareCodes))
const OUTCOME_RANK: Record<Outcome, number> = { failed: 0, cantTell: 1, passed: 2, inapplicable: 3 }
const CONF_RANK = { high: 0, medium: 1, low: 2 }

const multiPageSearch = computed(() => new Set(findings.value.map((f) => f.page_url)).size > 1)
const filtered = computed(() => {
  const q = filters.q.trim().toLowerCase()
  return findings.value.filter((f) => {
    if (filters.outcome && f.outcome !== filters.outcome) return false
    if (filters.criterion && f.criterion !== filters.criterion) return false
    if (filters.by && (f.source === 'apertus') !== (filters.by === 'apertus')) return false
    if (filters.status && f.status !== filters.status) return false
    if (filters.reason && f.reason_code !== filters.reason) return false
    if (q) {
      // The page URL only in a multi-page report: on one page it would match every finding.
      const hay = [f.criterion, f.criterion_name, plainName(f.criterion, locale.value), rowTitle(f, scan.value?.ui_lang ?? 'en').text, f.user_impact, f.explanation, f.excerpt, f.selector, multiPageSearch.value ? f.page_url : '']
        .join(' ')
        .toLowerCase()
      if (!hay.includes(q)) return false
    }
    return true
  })
})

/**
 * Criterion sections (UX-4): most failures first. Each holds its rows to review;
 * passed and not-applicable rows fold into "{n} with no problem".
 */
const showAllOk = ref(false)
const openOk = reactive(new Set<string>())
const okForced = computed(() => filters.outcome === 'passed' || filters.outcome === 'inapplicable' || showAllOk.value)
const okVisible = (code: string) => okForced.value || openOk.has(code)
function toggleOk(code: string) {
  if (openOk.has(code)) openOk.delete(code)
  else openOk.add(code)
}

/**
 * Section order comes from the whole report, not from the filtered list, so sections stay
 * put while filters change and while rows are decided (no jumps under the reviewer's eyes).
 */
const sectionRank = computed(() => {
  const m = new Map<string, { failed: number; cantTell: number }>()
  for (const f of findings.value) {
    const r = m.get(f.criterion) ?? { failed: 0, cantTell: 0 }
    if (f.outcome === 'failed') r.failed++
    else if (f.outcome === 'cantTell') r.cantTell++
    m.set(f.criterion, r)
  }
  return m
})

const sections = computed(() => {
  const map = new Map<string, Finding[]>()
  for (const f of filtered.value) {
    const list = map.get(f.criterion) ?? []
    list.push(f)
    map.set(f.criterion, list)
  }
  return Array.from(map.entries())
    .map(([code, items]) => {
      const sorted = [...items].sort((a, b) => OUTCOME_RANK[a.outcome] - OUTCOME_RANK[b.outcome] || CONF_RANK[a.confidence] - CONF_RANK[b.confidence])
      const review = sorted.filter(toReview)
      const ok = sorted.filter((f) => !toReview(f))
      return {
        code,
        name: items[0]!.criterion_name,
        failed: sectionRank.value.get(code)?.failed ?? 0,
        cantTell: sectionRank.value.get(code)?.cantTell ?? 0,
        reviewRows: groupFindings(review),
        okRows: groupFindings(ok),
        okCount: ok.length,
      }
    })
    .sort((a, b) => compareSections(a, b, compareCodes))
})
/** Rows in visual order (j/k move between visible rows). */
const ordered = computed<FindingGroup[]>(() => sections.value.flatMap((s) => [...s.reviewRows, ...(okVisible(s.code) ? s.okRows : [])]))
const reviewRows = computed(() => ordered.value.filter((r) => toReview(r.lead)))
const rowOf = (id: string | null) => (id ? (ordered.value.find((r) => r.items.some((f) => f.id === id)) ?? null) : null)
const rowByKey = (key: string) => ordered.value.find((r) => r.key === key) ?? null
const visibleCount = computed(() => ordered.value.reduce((n, r) => n + r.items.length, 0))

function toggleOutcome(o: Outcome) {
  filters.outcome = filters.outcome === o ? '' : o
}
function toggleBy(b: Exclude<By, ''>) {
  filters.by = filters.by === b ? '' : b
}
function selectCriterion(code: string) {
  filters.criterion = filters.criterion === code ? '' : code
  toFindings()
}
function showPassed() {
  showAllOk.value = true
  toFindings()
}

/* ---- Selection & detail panel ----------------------------------------- */

const selectedId = ref<string | null>(typeof route.query.f === 'string' ? route.query.f : null)
const selectedRow = computed(() => rowOf(selectedId.value))
/** While a decision settles, the panel keeps showing the row even if a filter has just hidden it. */
const pinned = shallowRef<FindingGroup | null>(null)
const panelRow = computed(() => selectedRow.value ?? (pinned.value?.items.some((f) => f.id === selectedId.value) ? pinned.value : null))
/** The finding shown in the panel: the lead of its row (a deep link may point at any item). */
const selected = computed(() => panelRow.value?.lead ?? findings.value.find((f) => f.id === selectedId.value) ?? null)
const selectedIndex = computed(() => (selectedRow.value ? ordered.value.indexOf(selectedRow.value) : -1))
const busy = ref(false)
const toolbar = ref<InstanceType<typeof FindingsToolbar> | null>(null)

const docked = ref(false)
const mq = window.matchMedia('(min-width: 1280px)')
const syncDock = () => (docked.value = mq.matches)
onMounted(() => {
  syncDock()
  mq.addEventListener('change', syncDock)
})
onBeforeUnmount(() => {
  mq.removeEventListener('change', syncDock)
  modalOpen.value = false
})

watch(selectedId, (id) => {
  const q = { ...route.query }
  if (id) q.f = id
  else delete q.f
  void router.replace({ query: q })
})

async function focusPanelHeading() {
  await nextTick()
  document.getElementById('finding-title')?.focus({ preventScroll: true })
}

function rowFor(id: string): HTMLElement | null {
  return document.querySelector<HTMLElement>(`[data-finding="${CSS.escape(id)}"]`)
}

function select(f: Finding) {
  selectedId.value = f.id
  void nextTick(() => rowFor(f.id)?.scrollIntoView({ block: 'nearest' }))
  void focusPanelHeading()
}

function open(f: Finding) {
  selectedId.value = f.id
  void focusPanelHeading()
}

function close() {
  const id = selectedId.value
  selectedId.value = null
  if (id) void nextTick(() => (rowFor(id) ?? document.getElementById('rep-findings'))?.focus())
}

function move(delta: number) {
  const list = ordered.value
  if (!list.length) return
  const i = selectedIndex.value
  const next = i < 0 ? (delta > 0 ? 0 : list.length - 1) : Math.max(0, Math.min(list.length - 1, i + delta))
  select(list[next]!.lead)
}

/** The page's primary action: open the first row in the list that still needs a decision. */
async function startReview() {
  let row = reviewRows.value.find((r) => r.items.some((x) => x.status === 'to_review'))
  if (!row && hasFilters.value) {
    resetFilters()
    await nextTick()
    row = reviewRows.value.find((r) => r.items.some((x) => x.status === 'to_review'))
  }
  if (row) select(row.lead)
}
const ctaLabel = computed(() => (remaining.value === 0 ? null : progress.value.done ? t('report.continue') : t('report.start')))

/**
 * Focus is never lost: when the focused row (or one of its buttons) has just left the
 * filtered list, focus moves to the row now in its place, else to the list heading.
 */
function rescueFocus(at: number) {
  const el = document.activeElement as HTMLElement | null
  const rowEl = el?.closest<HTMLElement>('[data-row]')
  const stale = !el || el === document.body || !el.isConnected || (!!rowEl && !rowByKey(rowEl.dataset.row ?? ''))
  if (!stale) return
  const list = ordered.value
  const target = list[Math.min(Math.max(at, 0), list.length - 1)]
  const next = target ? rowFor(target.lead.id) : null
  ;(next ?? document.getElementById('rep-findings'))?.focus()
}

const wait = (ms: number) => new Promise<void>((r) => window.setTimeout(r, ms))
/** Time for the check to draw itself before the panel moves on (none with reduced motion). */
const BEAT = 280

/**
 * A decision on a row applies to every identical finding in it. From the panel, the
 * triage flow moves on to the next row that still needs a decision; from the list, the
 * focus stays in the list.
 */
async function decide(status: 'accepted' | 'rejected', row: FindingGroup | null = panelRow.value, from: 'panel' | 'list' = 'panel') {
  if (!row || busy.value) return
  busy.value = true
  const at = ordered.value.findIndex((r) => r.key === row.key)
  const after = [...ordered.value.slice(at + 1), ...ordered.value.slice(0, Math.max(at, 0))].filter((r) => toReview(r.lead)).map((r) => r.key)
  if (from === 'panel') pinned.value = row
  try {
    const saving = Promise.all(row.items.map((f) => setStatus(f, status)))
    await nextTick()
    if (from === 'list') rescueFocus(at)
    await Promise.all([saving, from === 'panel' && !reducedMotion() ? wait(BEAT) : null])
    const code = row.items.length > 1 ? `${row.lead.criterion} ×${row.items.length}` : row.lead.criterion
    toast(t(status === 'accepted' ? 'finding.accepted' : 'finding.rejected', { code }), status === 'accepted' ? 'success' : 'neutral', 3800, 'decision')
    if (from === 'panel') advance(row, at, after)
    else rescueFocus(at)
  } catch {
    toast(t('finding.saveError'), 'danger', 3800, 'decision', { label: t('toast.retry'), run: () => void decide(status, row, from) })
  } finally {
    pinned.value = null
    busy.value = false
  }
}

/** Triage flow: the next row that still needs a decision, else what comes next on the page. */
function advance(row: FindingGroup, at: number, after: string[]) {
  const next = after.map(rowByKey).find((r) => r?.items.some((x) => x.status === 'to_review'))
  if (next) {
    select(next.lead)
  } else if (allReviewed.value) {
    selectedId.value = null
    void nextTick(() => {
      const h = document.getElementById('review-done')
      h?.scrollIntoView({ block: 'center' })
      h?.focus({ preventScroll: true })
    })
  } else if (!rowByKey(row.key)) {
    // The decided row left the filtered list and nothing else here needs a decision.
    const list = ordered.value
    const fallback = list[Math.min(at, list.length - 1)]
    if (fallback) select(fallback.lead)
    else {
      selectedId.value = null
      void nextTick(() => document.getElementById('rep-findings')?.focus())
    }
  }
}

/** Per-place override inside a grouped row (finding panel). */
async function decideOne(f: Finding, status: 'accepted' | 'rejected') {
  if (busy.value) return
  busy.value = true
  try {
    const saving = setStatus(f, status)
    await nextTick()
    const el = document.activeElement
    if (!el || el === document.body || !el.isConnected) void focusPanelHeading()
    await saving
  } catch {
    toast(t('finding.saveError'), 'danger', 3800, 'decision', { label: t('toast.retry'), run: () => void decideOne(f, status) })
  } finally {
    busy.value = false
  }
}

const allReviewed = computed(() => progress.value.total > 0 && progress.value.done === progress.value.total)
/** E2: nothing failed and nothing is uncertain, but something was checked. */
const noFailures = computed(() => findings.value.length > 0 && counts.value.failed === 0 && counts.value.cantTell === 0)

async function exportReport() {
  if (!scan.value) return
  try {
    await api().exportScan(scan.value, 'html')
    toast(t('export.done', { format: t('export.html') }), 'success')
  } catch {
    toast(t('export.failed'), 'danger', 3800, 'export', { label: t('toast.retry'), run: () => void exportReport() })
  }
}

/**
 * WCAG 2.1.4: J, K, A, R act only while focus is in the findings list or the
 * finding panel (and never while typing; useShortcuts also lets users turn them off).
 * A and R decide the row that has focus, else the row open in the panel.
 */
function inFindings(): boolean {
  const el = document.activeElement
  return !!el && !!(el.closest('#findings') || el.closest('#finding-panel'))
}
function focusedRow(): FindingGroup | null {
  const key = (document.activeElement as HTMLElement | null)?.closest<HTMLElement>('[data-row]')?.dataset.row
  return key ? rowByKey(key) : null
}
function shortcutDecide(e: KeyboardEvent, status: 'accepted' | 'rejected') {
  if (!inFindings()) return
  const row = focusedRow()
  if (row) {
    e.preventDefault()
    void decide(status, row, 'list')
  } else if (selected.value) {
    e.preventDefault()
    void decide(status)
  }
}

useShortcuts({
  j: (e) => {
    if (!inFindings()) return
    e.preventDefault()
    move(1)
  },
  k: (e) => {
    if (!inFindings()) return
    e.preventDefault()
    move(-1)
  },
  a: (e) => shortcutDecide(e, 'accepted'),
  r: (e) => shortcutDecide(e, 'rejected'),
  '/': (e) => {
    e.preventDefault()
    toolbar.value?.focusSearch()
  },
  Escape: () => {
    if (selected.value && !document.querySelector('dialog[open]')) close()
  },
})

function reload() {
  location.reload()
}

const panelOpen = computed(() => !!selected.value)
/** Below 1280 px the panel is a modal dialog (UX-14). */
const overlay = computed(() => panelOpen.value && !docked.value)
watch(overlay, (o) => (modalOpen.value = o), { immediate: true })

/** Keep Tab inside the modal panel. */
function trapTab(e: KeyboardEvent) {
  if (!overlay.value || e.key !== 'Tab') return
  const panel = e.currentTarget as HTMLElement
  const items = Array.from(
    panel.querySelectorAll<HTMLElement>('a[href], button:not([disabled]), input, select, textarea, summary, [tabindex]:not([tabindex="-1"])'),
  ).filter((el) => (el.offsetParent !== null || el === document.activeElement) && !el.closest('[inert]'))
  if (!items.length) return
  const first = items[0]!
  const last = items[items.length - 1]!
  if (e.shiftKey && (document.activeElement === first || !panel.contains(document.activeElement))) {
    e.preventDefault()
    last.focus()
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault()
    first.focus()
  }
}
</script>

<template>
  <div class="rep" :class="{ 'rep--docked': panelOpen && docked }">
    <div class="rep__content" :inert="overlay || undefined">
      <div v-if="loading && !scan" class="container rep__loading" role="status">
        <span class="sr-only">{{ t('report.loading') }}</span>
        <span class="skel rep__skel rep__skel--h1" aria-hidden="true" />
        <span class="skel rep__skel rep__skel--line" aria-hidden="true" />
        <span class="skel rep__skel rep__skel--band" aria-hidden="true" />
        <span v-for="i in 5" :key="i" class="skel rep__skel rep__skel--row" aria-hidden="true" />
      </div>

      <div v-else-if="notFound || loadError" class="container rep__state">
        <ErrorState v-if="notFound" :title="t('report.notFound')" :body="t('scan.notFoundBody')" :details="`id: ${id}`" :heading-level="1">
          <RouterLink class="btn btn--primary" :to="{ name: 'home' }">{{ t('report.newCheck') }}</RouterLink>
          <RouterLink class="btn btn--ghost" :to="{ name: 'home', hash: '#recent' }">{{ t('recent.title') }}</RouterLink>
        </ErrorState>
        <ErrorState v-else-if="unreachable" :title="t('offline.title')" :body="t('offline.body')" :details="t('offline.detail')" :heading-level="1">
          <button type="button" class="btn btn--primary" @click="reload">{{ t('common.retry') }}</button>
        </ErrorState>
        <ErrorState v-else :title="t('report.loadError')" :body="t('report.loadErrorBody')" :details="loadError" :heading-level="1">
          <button type="button" class="btn btn--primary" @click="reload">{{ t('common.retry') }}</button>
        </ErrorState>
      </div>

      <template v-else-if="scan && head">
        <div class="container rep__top">
          <ReportHeader
            :scan="scan"
            :title="headTitle"
            :url="subUrl"
            :href="head.url"
            :pasted="head.pasted"
            :prechecked="prechecked"
            :notes="notes"
            :answers="answers"
            :tokens="tokens"
            :seconds="seconds"
            :left="left"
            :lang-differs="langDiffers"
            :rerunning="rerunning"
            @demo="checkDemo"
            @rerun="rerun(scan)"
            @rerun-in="rerun(scan, locale)"
            @filter="filterReason"
          />

          <!-- M30: the check failed; what is shown is partial -->
          <ErrorState v-if="failure && failurePrimary" :title="problemText(failure).title" :body="`${problemText(failure).body} ${t('fail.partialNote')}`" :details="problemText(failure).details" role="none">
            <button type="button" class="btn btn--primary" :disabled="rerunning" @click="act(failurePrimary)">{{ t(ACTION_LABEL[failurePrimary]) }}</button>
            <button v-for="a in failure.secondary" :key="a" type="button" class="btn btn--ghost" @click="act(a)">{{ t(ACTION_LABEL[a]) }}</button>
          </ErrorState>
          <!-- M27: the page answered with an HTTP error -->
          <ErrorState v-else-if="httpProblem" :title="problemText(httpProblem).title" :body="problemText(httpProblem).body" role="none">
            <button type="button" class="btn btn--primary" @click="act('edit')">{{ t('start.edit') }}</button>
            <button type="button" class="btn btn--ghost" @click="act('anyway')">{{ t('fail.http.anyway') }}</button>
          </ErrorState>

          <ReportStats
            v-if="findings.length && !noFailures"
            :remaining="remaining"
            :done="progress.done"
            :total="progress.total"
            :failed="counts.failed"
            :by-code="byCode"
            :by-apertus="byApertus"
            :outcome="filters.outcome"
            :by="filters.by"
            :cta="ctaLabel"
            @outcome="toggleOutcome"
            @by="toggleBy"
            @start="startReview"
          />

          <!-- Next step: review complete (E3), or no failures (E2) -->
          <Transition name="fade-rise">
            <section v-if="allReviewed" class="next" aria-labelledby="review-done">
              <svg class="next__mark" viewBox="0 0 24 24" width="28" height="28" aria-hidden="true" focusable="false">
                <circle cx="12" cy="12" r="11" />
                <path class="m-draw" pathLength="1" d="M7 12.4l3.3 3.3L17.2 8.6" />
              </svg>
              <div class="next__text" role="status">
                <h2 id="review-done" class="next__title" tabindex="-1">{{ t('review.done.title') }}</h2>
                <p>{{ t('review.done.body', { n: formatNumber(progress.total) }) }}</p>
              </div>
              <div class="next__actions">
                <button type="button" class="btn btn--primary press" @click="exportReport">{{ t('review.download') }}</button>
                <RouterLink class="btn btn--ghost" :to="{ name: 'human', query: { scan: scan.id } }">{{ t('review.continue', { m: humanCount }) }}</RouterLink>
              </div>
            </section>
            <section v-else-if="noFailures" class="next next--info" aria-labelledby="nothing-found">
              <svg class="next__mark" viewBox="0 0 24 24" width="28" height="28" aria-hidden="true" focusable="false">
                <circle cx="12" cy="12" r="11" />
                <path class="m-draw" pathLength="1" d="M7 12.4l3.3 3.3L17.2 8.6" />
              </svg>
              <div class="next__text">
                <h2 id="nothing-found" class="next__title">{{ t('clean.title', { n: prechecked ?? 0 }) }}</h2>
                <p>{{ t('clean.body', { p: counts.passed, m: humanCount }) }}</p>
              </div>
              <div class="next__actions">
                <RouterLink class="btn btn--primary" :to="{ name: 'human', query: { scan: scan.id } }">{{ t('empty.human') }}</RouterLink>
                <button v-if="!showAllOk" type="button" class="btn btn--ghost" @click="showPassed">{{ t('clean.showPassed') }}</button>
              </div>
            </section>
          </Transition>
        </div>

        <!-- Findings -->
        <section id="findings" class="container rep__section m-rise" style="--i: 3" aria-labelledby="rep-findings">
          <div class="rep__bar">
            <h2 id="rep-findings" class="rep__h2" tabindex="-1">{{ t('report.findings') }}</h2>
            <FindingsToolbar
              v-if="findings.length"
              ref="toolbar"
              v-model:status="filters.status"
              v-model:q="filters.q"
              v-model:criterion="filters.criterion"
              class="rep__toolbar"
              :criteria="criteriaPresent"
              :active="hasFilters"
              :shown="visibleCount"
              :total="findings.length"
              :reason="filters.reason"
              @reset="resetFilters"
              @clear-reason="filters.reason = ''"
            />
          </div>

          <!-- E1: nothing at all to report -->
          <EmptyState v-if="!findings.length" :title="t('empty.title', { n: prechecked ?? 0 })" :body="t('empty.body', { m: humanCount })" :heading-level="3">
            <RouterLink class="btn btn--primary" :to="{ name: 'human', query: { scan: scan.id } }">{{ t('empty.human') }}</RouterLink>
          </EmptyState>

          <EmptyState v-else-if="!filtered.length" :title="t('report.emptyFilter.title')" :body="t('report.emptyFilter.body')" :heading-level="3">
            <button type="button" class="btn btn--secondary" @click="resetFilters">{{ t('report.reset') }}</button>
          </EmptyState>

          <TransitionGroup v-else tag="div" name="list" class="rep__groups">
            <FindingSection
              v-for="g in sections"
              :key="g.code"
              :code="g.code"
              :name="g.name"
              :review-rows="g.reviewRows"
              :ok-rows="g.okRows"
              :ok-count="g.okCount"
              :ok-open="openOk.has(g.code)"
              :ok-forced="okForced"
              :selected-key="selectedRow?.key ?? null"
              :scan-lang="scan.ui_lang"
              :base="scan.url"
              :multi-page="multiPage"
              :panel-id="selected ? 'finding-panel' : undefined"
              @open="open"
              @decide="(row, s) => decide(s, row, 'list')"
              @toggle-ok="toggleOk"
            />
          </TransitionGroup>
        </section>

        <!-- Coverage, below the findings (UX-4) -->
        <section class="container rep__section" aria-labelledby="rep-coverage">
          <h2 id="rep-coverage" class="rep__h2 rep__h2--spaced">{{ t('report.coverage') }}</h2>
          <CoverageMap :scan="scan" :findings="findings" :selected="filters.criterion || null" interactive @select="selectCriterion" />
          <RouterLink class="human-link" :to="{ name: 'human', query: { scan: scan.id } }">
            <span class="human-link__text">{{ t('report.humanCta', { n: humanCount }) }}</span>
            <span class="human-link__go">{{ t('report.humanLink') }}<ArrowRight :size="16" aria-hidden="true" /></span>
          </RouterLink>
        </section>
      </template>
    </div>

    <!-- Detail panel: docked beside the list on wide screens, a modal dialog below 1280 px (UX-14) -->
    <Transition name="fade">
      <div v-if="overlay" class="rep__scrim" aria-hidden="true" @click="close" />
    </Transition>
    <Transition name="panel">
      <aside
        v-if="selected && scan"
        id="finding-panel"
        class="panel"
        :role="overlay ? 'dialog' : undefined"
        :aria-modal="overlay ? 'true' : undefined"
        aria-labelledby="finding-title"
        @keydown="trapTab"
      >
        <FindingDetail
          :finding="selected"
          :items="panelRow && panelRow.items.length > 1 ? panelRow.items : undefined"
          :scan="scan"
          :index="selectedIndex"
          :total="ordered.length"
          heading-id="finding-title"
          @close="close"
          @prev="move(-1)"
          @next="move(1)"
          @decide="decide"
          @decide-one="decideOne"
        />
      </aside>
    </Transition>
  </div>
</template>

<style scoped>
.rep {
  padding-top: var(--s-7);
  padding-bottom: var(--s-8);
}
.rep--docked {
  padding-right: var(--drawer-w);
}
.rep__loading {
  display: flex;
  flex-direction: column;
  gap: var(--s-3);
}
.rep__skel {
  display: block;
}
.rep__skel--h1 {
  width: min(420px, 70%);
  height: 40px;
}
.rep__skel--line {
  width: min(560px, 90%);
  height: 16px;
  margin-bottom: var(--s-5);
}
.rep__skel--band {
  height: 96px;
  margin-bottom: var(--s-6);
}
.rep__skel--row {
  height: 56px;
}
.rep__state {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--s-4);
  padding-top: var(--s-8);
}
.rep__top {
  display: flex;
  flex-direction: column;
  gap: var(--s-6);
}
.rep__top > :deep(.es) {
  max-width: none;
}

/* Next step: review complete / nothing failed */
.next {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--s-4);
  padding: var(--s-4) var(--s-5);
  background: var(--green-tint);
  border-radius: var(--r-card);
}
.next--info {
  background: var(--surface-2);
}
.next__mark {
  flex: none;
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.next__mark circle {
  fill: var(--green);
  stroke: none;
}
.next__mark path {
  stroke: var(--on-ink);
  stroke-width: 2.4;
}
.next__text {
  flex: 1 1 280px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.next__title {
  font-size: var(--fs-20);
  font-weight: 680;
  letter-spacing: -0.02em;
}
.next__text p {
  color: var(--muted);
}
.next__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--s-2);
  min-width: 0;
  max-width: 100%;
}
.next__actions > * {
  max-width: 100%;
}

/* Sections */
.rep__section {
  margin-top: var(--s-8);
}
.rep__bar {
  display: flex;
  flex-direction: column;
  gap: var(--s-4);
  margin-bottom: var(--s-6);
}
.rep__toolbar {
  min-width: 0;
}
.rep__h2 {
  font-size: var(--fs-24);
  font-weight: 700;
  letter-spacing: -0.025em;
}
.rep__h2--spaced {
  margin-bottom: var(--s-5);
}
.rep__groups {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--s-7);
}
.rep__groups > .list-leave-active {
  position: absolute;
  left: 0;
  right: 0;
}

/* Human checks: one quiet link row */
.human-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--s-2) var(--s-4);
  margin-top: var(--s-6);
  padding: var(--s-4) 0;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  color: var(--ink);
  text-decoration: none;
}
.human-link__text {
  font-size: var(--fs-16);
  font-weight: 600;
}
.human-link__go {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--blue);
  font-weight: 600;
}
.human-link__go svg {
  transition: transform var(--dur-2) var(--ease-out);
}
.human-link:hover .human-link__go {
  text-decoration: underline;
}
.human-link:hover .human-link__go svg {
  transform: translateX(3px);
}

/* Finding panel */
.panel {
  position: fixed;
  z-index: 45;
  top: var(--header-h);
  right: 0;
  bottom: 0;
  width: min(var(--drawer-w), 100vw);
  background: var(--surface);
  border-left: 1px solid var(--line);
  box-shadow: var(--shadow-overlay);
}
.rep--docked .panel {
  box-shadow: none;
}
.rep__scrim {
  position: fixed;
  z-index: 44;
  inset: var(--header-h) 0 0 0;
  background: var(--scrim);
}
.panel-enter-active {
  transition: transform var(--dur-3) var(--ease-out), opacity var(--dur-2) var(--ease-out);
}
.panel-leave-active {
  transition: transform var(--dur-2) var(--ease-in-out), opacity var(--dur-2) var(--ease-in-out);
}
.panel-enter-from,
.panel-leave-to {
  transform: translateX(24px);
  opacity: 0;
}
@media (max-width: 640px) {
  .rep {
    padding-top: var(--s-6);
  }
  .rep__bar {
    margin-bottom: var(--s-5);
  }
}
</style>
