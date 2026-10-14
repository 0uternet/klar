<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, ChevronDown, ExternalLink, Info, Plus, Search, X } from '@lucide/vue'
import type { Finding, Outcome, Scan, Source, Status } from '@/types'
import { OUTCOMES, SOURCES, STATUSES } from '@/types'
import { api, ApiError } from '@/api'
import { compareSections, groupFindings, reviewProgress, toReview, type FindingGroup } from '@/lib/group'
import { formatDate, formatNumber, languageName, locale, t, tp, type MessageKey } from '@/i18n'
import { CRITERIA, compareCodes, plainName } from '@/data/wcag'
import { checkedCount, loadCriteria, needsPerson } from '@/stores/criteria'
import { DEMO_URL, isDemoUrl } from '@/config'
import { ensureBooted, health, lastScanId, modalOpen, unreachable } from '@/stores/app'
import { loadScan, scans, setStatus } from '@/stores/scans'
import { toast } from '@/stores/toast'
import { pageCount, prettyModel, scanTitle } from '@/lib/format'
import { leftNetwork } from '@/lib/sovereignty'
import { classifyHttpStatus, classifyScanError, hostOf, renderProblem, type Problem, type ProblemAction } from '@/lib/errors'
import { apertusAnswers, runNotes } from '@/lib/notes'
import { rowTitle } from '@/lib/finding-text'
import { useShortcuts } from '@/composables/useShortcuts'
import { useDocumentTitle } from '@/composables/useDocumentTitle'
import { useRerun } from '@/composables/useRerun'
import VerdictChip from '@/components/VerdictChip.vue'
import CriterionTag from '@/components/CriterionTag.vue'
import CoverageMap from '@/components/CoverageMap.vue'
import FindingCard from '@/components/FindingCard.vue'
import FindingDetail from '@/components/FindingDetail.vue'
import ExportMenu from '@/components/ExportMenu.vue'
import SovereigntyBadge from '@/components/SovereigntyBadge.vue'
import EmptyState from '@/components/EmptyState.vue'
import ErrorState from '@/components/ErrorState.vue'
import RunNotes from '@/components/RunNotes.vue'
import ShapeIcon from '@/components/ShapeIcon.vue'
import KeyboardHint from '@/components/KeyboardHint.vue'

const props = defineProps<{ id: string }>()
const route = useRoute()
const router = useRouter()
const { rerun, rerunning, editAddress, pasteHtml } = useRerun()

const scan = computed<Scan | undefined>(() => scans.get(props.id))
const loading = ref(true)
const notFound = ref(false)
const loadError = ref<string | null>(null)

/** H1 = the page title, the URL as a linked subline (UX-11). */
const head = computed(() => (scan.value ? scanTitle(scan.value) : null))
const headTitle = computed(() => head.value?.title ?? t('report.pastedHtml'))
/** The linked address under the H1, unless the H1 already is that address. */
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
/** N of "pre-checks N of 50": what this scan actually checked (stats.criteria_checked). */
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
const shownNotes = computed(() => notes.value.slice(0, 3))
const moreNotes = computed(() => notes.value.slice(3))

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

const filters = reactive({ outcome: '' as Outcome | '', criterion: '', source: '' as Source | '', status: '' as Status | '', q: '', reason: '' })
const hasFilters = computed(() => !!(filters.outcome || filters.criterion || filters.source || filters.status || filters.q || filters.reason))
function resetFilters() {
  Object.assign(filters, { outcome: '', criterion: '', source: '', status: '', q: '', reason: '' })
}
function filterReason(code: string) {
  resetFilters()
  filters.reason = code
  void nextTick(() => document.getElementById('rep-findings')?.scrollIntoView({ block: 'start' }))
}

const criteriaPresent = computed(() => Array.from(new Set(findings.value.map((f) => f.criterion))).sort(compareCodes))
const OUTCOME_RANK: Record<Outcome, number> = { failed: 0, cantTell: 1, passed: 2, inapplicable: 3 }
const CONF_RANK = { high: 0, medium: 1, low: 2 }

const filtered = computed(() => {
  const q = filters.q.trim().toLowerCase()
  return findings.value.filter((f) => {
    if (filters.outcome && f.outcome !== filters.outcome) return false
    if (filters.criterion && f.criterion !== filters.criterion) return false
    if (filters.source && f.source !== filters.source) return false
    if (filters.status && f.status !== filters.status) return false
    if (filters.reason && f.reason_code !== filters.reason) return false
    if (q) {
      const hay = [f.criterion, f.criterion_name, plainName(f.criterion, locale.value), rowTitle(f, scan.value?.ui_lang ?? 'en').text, f.user_impact, f.explanation, f.excerpt, f.selector, f.page_url]
        .join(' ')
        .toLowerCase()
      if (!hay.includes(q)) return false
    }
    return true
  })
})

/**
 * Criterion sections (UX-4): most failures first. Each holds its rows to review;
 * passed and not-applicable rows collapse into "{n} checked, no problem found".
 */
const showAllOk = ref(false)
const openOk = reactive(new Set<string>())
const okForced = computed(() => filters.outcome === 'passed' || filters.outcome === 'inapplicable' || showAllOk.value)
const okVisible = (code: string) => okForced.value || openOk.has(code)
function toggleOk(code: string) {
  if (openOk.has(code)) openOk.delete(code)
  else openOk.add(code)
}

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
        failed: items.filter((f) => f.outcome === 'failed').length,
        cantTell: items.filter((f) => f.outcome === 'cantTell').length,
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
const visibleCount = computed(() => ordered.value.reduce((n, r) => n + r.items.length, 0))

function toggleOutcome(o: Outcome) {
  filters.outcome = filters.outcome === o ? '' : o
}
function selectCriterion(code: string) {
  filters.criterion = filters.criterion === code ? '' : code
  void nextTick(() => document.getElementById('rep-findings')?.scrollIntoView({ block: 'start' }))
}
function showPassed() {
  showAllOk.value = true
  void nextTick(() => document.getElementById('rep-findings')?.scrollIntoView({ block: 'start' }))
}

/* ---- Selection & detail panel ----------------------------------------- */

const selectedId = ref<string | null>(typeof route.query.f === 'string' ? route.query.f : null)
const selectedRow = computed(() => rowOf(selectedId.value))
/** The finding shown in the panel: the lead of its row (a deep link may point at any item). */
const selected = computed(() => selectedRow.value?.lead ?? findings.value.find((f) => f.id === selectedId.value) ?? null)
const selectedIndex = computed(() => (selectedRow.value ? ordered.value.indexOf(selectedRow.value) : -1))
/** "3 of 35 to review" for rows in the review scope; "{i} of {n}" for an opened passed row. */
const positionLabel = computed(() => {
  const row = selectedRow.value
  if (!row || !toReview(row.lead)) return undefined
  return t('report.toReviewPos', { i: formatNumber(reviewRows.value.indexOf(row) + 1), n: formatNumber(reviewRows.value.length) })
})
const busy = ref(false)
const searchInput = ref<HTMLInputElement | null>(null)

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

function open(f: Finding) {
  selectedId.value = f.id
  void focusPanelHeading()
}

function close() {
  const id = selectedId.value
  selectedId.value = null
  if (id) void nextTick(() => rowFor(id)?.focus())
}

function move(delta: number) {
  const list = ordered.value
  if (!list.length) return
  const i = selectedIndex.value
  const next = i < 0 ? (delta > 0 ? 0 : list.length - 1) : Math.max(0, Math.min(list.length - 1, i + delta))
  const f = list[next]!.lead
  selectedId.value = f.id
  void nextTick(() => rowFor(f.id)?.scrollIntoView({ block: 'nearest' }))
  void focusPanelHeading()
}

/** A decision on a row applies to every identical finding in it. */
async function decide(status: 'accepted' | 'rejected') {
  const row = selectedRow.value
  if (!row || busy.value) return
  busy.value = true
  try {
    await Promise.all(row.items.map((f) => setStatus(f, status)))
    const code = row.items.length > 1 ? `${row.lead.criterion} ×${row.items.length}` : row.lead.criterion
    toast(t(status === 'accepted' ? 'finding.accepted' : 'finding.rejected', { code }), status === 'accepted' ? 'success' : 'neutral', 3800, 'decision')
    // Triage flow: jump to the next row in the review scope that still needs a decision.
    const list = reviewRows.value
    const from = list.indexOf(row)
    const rest = from >= 0 ? [...list.slice(from + 1), ...list.slice(0, from)] : list
    const nextOpen = rest.find((r) => r.items.some((x) => x.status === 'to_review'))
    if (nextOpen) {
      selectedId.value = nextOpen.lead.id
      void nextTick(() => rowFor(nextOpen.lead.id)?.scrollIntoView({ block: 'nearest' }))
      void focusPanelHeading()
    } else if (allReviewed.value) {
      selectedId.value = null
      void nextTick(() => {
        const h = document.getElementById('review-done')
        h?.scrollIntoView({ block: 'center' })
        h?.focus({ preventScroll: true })
      })
    }
  } catch {
    toast(t('finding.saveError'), 'danger', 3800, 'decision', { label: t('toast.retry'), run: () => void decide(status) })
  } finally {
    busy.value = false
  }
}

/** Per-place override inside an expanded row. */
async function decideOne(f: Finding, status: 'accepted' | 'rejected') {
  if (busy.value) return
  busy.value = true
  try {
    await setStatus(f, status)
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
 */
function inFindings(): boolean {
  const el = document.activeElement
  return !!el && !!(el.closest('#findings') || el.closest('#finding-panel'))
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
  a: (e) => {
    if (!selected.value || !inFindings()) return
    e.preventDefault()
    void decide('accepted')
  },
  r: (e) => {
    if (!selected.value || !inFindings()) return
    e.preventDefault()
    void decide('rejected')
  },
  '/': (e) => {
    e.preventDefault()
    searchInput.value?.focus()
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
  ).filter((el) => el.offsetParent !== null || el === document.activeElement)
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
        <span class="rep__pulse" aria-hidden="true" />{{ t('report.loading') }}
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
        <!-- Header: title, one line of facts, the rest under "Run details" (UX-11, UX-12) -->
        <header class="container rep__head">
          <div class="rep__top">
            <div class="rep__title">
              <p class="eyebrow">{{ t('report.eyebrow') }} · <span class="tabular">{{ formatDate(scan.created_at) }}</span></p>
              <h1 class="h1 rep__h1" tabindex="-1">{{ headTitle }}</h1>
              <p v-if="subUrl || head.pasted" class="rep__sub">
                <a v-if="subUrl && head.url" :href="head.url" target="_blank" rel="noopener noreferrer" class="rep__url mono">
                  {{ subUrl }}<ExternalLink :size="13" aria-hidden="true" /><span class="sr-only"> {{ t('finding.newTab') }}</span>
                </a>
                <span v-else>{{ t('report.pastedHtml') }}</span>
              </p>
            </div>
            <div class="rep__actions">
              <RouterLink class="btn btn--ghost" :to="{ name: 'home' }"><Plus :size="16" aria-hidden="true" />{{ t('report.newCheck') }}</RouterLink>
              <ExportMenu :scan="scan" />
            </div>
          </div>

          <p v-if="langDiffers" class="rep__lang" role="note">
            <span>{{ t('notes.lang', { scanLang: languageName(scan.ui_lang) }) }}</span>
            <button v-if="head.url" type="button" class="btn btn--ghost btn--sm" :disabled="rerunning" @click="rerun(scan, locale)">
              {{ t('notes.rerunIn', { uiLang: languageName(locale) }) }}
            </button>
          </p>

          <div class="rep__metaline">
            <SovereigntyBadge variant="inline" :health="health" :mode="scan.mode" :model="scan.model" />
            <span aria-hidden="true">·</span>
            <span>{{ prettyModel(scan.model) }}</span>
            <span aria-hidden="true">·</span>
            <span class="tabular">{{ t('report.seconds', { n: formatNumber(seconds, { maximumFractionDigits: 1 }) }) }}</span>
            <span aria-hidden="true">·</span>
            <span class="tabular">{{ left === null ? t('report.leftUnknown') : tp('report.left', left) }}</span>
          </div>

          <details class="rep__details">
            <summary>{{ t('report.runDetails') }}<ChevronDown :size="16" aria-hidden="true" class="rep__details-chev" /></summary>
            <dl class="rep__meta">
              <div>
                <dt>{{ t('report.meta.answers') }}</dt>
                <dd class="tabular">{{ answers ? t('report.answersOf', { answered: formatNumber(answers.answered), asked: formatNumber(answers.asked) }) : t('report.noneNeeded') }}</dd>
              </div>
              <div v-if="typeof scan.stats.guard_rejected === 'number'">
                <dt>{{ t('report.meta.guard') }}</dt>
                <dd class="tabular">{{ formatNumber(scan.stats.guard_rejected) }}</dd>
              </div>
              <div v-if="typeof scan.stats.llm_calls === 'number'">
                <dt>{{ t('report.meta.calls') }}</dt>
                <dd class="tabular">{{ formatNumber(scan.stats.llm_calls) }}</dd>
              </div>
              <div v-if="tokens">
                <dt>{{ t('report.tokens') }}</dt>
                <dd class="tabular">{{ tokens }}</dd>
              </div>
              <div>
                <dt>{{ t('report.scanId') }}</dt>
                <dd class="mono">{{ scan.id }}</dd>
              </div>
            </dl>
            <RunNotes v-if="moreNotes.length" :notes="moreNotes" @demo="checkDemo" @rerun="rerun(scan)" @filter="filterReason" />
          </details>

          <p class="rep__disclaimer" role="note">
            <Info :size="18" aria-hidden="true" />
            <span>{{ prechecked !== null ? t('report.disclaimer', { n: prechecked }) : t('report.disclaimerNoN') }}</span>
          </p>

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

          <RunNotes v-if="shownNotes.length" :notes="shownNotes" @demo="checkDemo" @rerun="rerun(scan)" @filter="filterReason" />
          <p v-if="moreNotes.length" class="rep__more-notes">{{ tp('notes.more', moreNotes.length) }}</p>
        </header>

        <!-- Next step: review complete (E3), or no failures (E2) -->
        <div v-if="allReviewed || noFailures" class="container rep__next">
          <section v-if="allReviewed" class="next" aria-labelledby="review-done">
            <ShapeIcon shape="circle" color="var(--green)" :size="12" />
            <div class="next__text" role="status">
              <h2 id="review-done" class="next__title" tabindex="-1">{{ t('review.done.title') }}</h2>
              <p>{{ t('review.done.body', { n: progress.total }) }}</p>
            </div>
            <div class="next__actions">
              <button type="button" class="btn btn--primary" @click="exportReport">{{ t('review.download') }}</button>
              <RouterLink class="btn btn--ghost" :to="{ name: 'human', query: { scan: scan.id } }">{{ t('review.continue', { m: humanCount }) }}</RouterLink>
            </div>
          </section>
          <section v-else class="next next--info" aria-labelledby="nothing-found">
            <Info :size="18" aria-hidden="true" />
            <div class="next__text">
              <h2 id="nothing-found" class="next__title">{{ t('clean.title', { n: prechecked ?? 0 }) }}</h2>
              <p>{{ t('clean.body', { p: counts.passed, m: humanCount }) }}</p>
            </div>
            <div class="next__actions">
              <RouterLink class="btn btn--primary" :to="{ name: 'human', query: { scan: scan.id } }">{{ t('empty.human') }}</RouterLink>
              <button v-if="!showAllOk" type="button" class="btn btn--ghost" @click="showPassed">{{ t('clean.showPassed') }}</button>
            </div>
          </section>
        </div>

        <!-- Findings -->
        <section id="findings" class="container rep__section" aria-labelledby="rep-findings">
          <div class="rep__section-head rep__section-head--row">
            <h2 id="rep-findings" class="rep__h2" tabindex="-1">{{ t('report.findings') }}</h2>
            <p v-if="findings.length" class="rep__showing tabular" role="status">{{ t('report.showing', { shown: visibleCount, total: findings.length }) }}</p>
          </div>

          <!-- E1: nothing at all to report -->
          <EmptyState v-if="!findings.length" :title="t('empty.title', { n: prechecked ?? 0 })" :body="t('empty.body', { m: humanCount })" :heading-level="3">
            <RouterLink class="btn btn--primary" :to="{ name: 'human', query: { scan: scan.id } }">{{ t('empty.human') }}</RouterLink>
          </EmptyState>

          <template v-else>
            <!-- Summary: one row of outcome chips that filter, then the review progress (UX-4) -->
            <div class="chips" role="group" :aria-label="t('report.summary')">
              <button
                v-for="o in OUTCOMES"
                :key="o"
                type="button"
                class="chip"
                :class="{ 'is-active': filters.outcome === o }"
                :aria-pressed="filters.outcome === o"
                :aria-label="`${t(`outcome.${o}`)} ${formatNumber(counts[o])}. ${t('report.filterChip', { outcome: t(`outcome.${o}`) })}`"
                @click="toggleOutcome(o)"
              >
                <VerdictChip :outcome="o" size="sm" />
                <span class="chip__n tabular">{{ formatNumber(counts[o]) }}</span>
              </button>
              <div class="chips__progress">
                <span class="chips__label tabular">{{ t('report.reviewedScope', { done: formatNumber(progress.done), total: formatNumber(progress.total) }) }}</span>
                <span
                  class="chips__bar"
                  role="progressbar"
                  :aria-label="t('report.reviewed')"
                  :aria-valuenow="progress.done"
                  aria-valuemin="0"
                  :aria-valuemax="progress.total"
                  :aria-valuetext="t('report.reviewedScope', { done: progress.done, total: progress.total })"
                >
                  <span class="chips__fill" :style="{ transform: `scaleX(${progress.total ? progress.done / progress.total : 0})` }" />
                </span>
              </div>
            </div>

            <div class="toolbar" role="search" :aria-label="t('report.filters')">
              <div class="toolbar__search">
                <label for="rep-search" class="toolbar__label">{{ t('report.search') }}</label>
                <div class="toolbar__search-field">
                  <Search :size="16" aria-hidden="true" class="toolbar__search-icon" />
                  <input
                    id="rep-search"
                    ref="searchInput"
                    v-model="filters.q"
                    type="search"
                    class="field toolbar__input"
                    :placeholder="t('report.searchPlaceholder')"
                    autocomplete="off"
                    @keydown.esc.stop="filters.q = ''"
                  />
                  <span class="toolbar__key"><KeyboardHint :keys="['/']" /></span>
                </div>
              </div>
              <div class="toolbar__filter">
                <label for="f-outcome" class="toolbar__label">{{ t('filter.outcome') }}</label>
                <select id="f-outcome" v-model="filters.outcome" class="field">
                  <option value="">{{ t('filter.all') }}</option>
                  <option v-for="o in OUTCOMES" :key="o" :value="o">{{ t(`outcome.${o}`) }}</option>
                </select>
              </div>
              <div class="toolbar__filter">
                <label for="f-crit" class="toolbar__label">{{ t('filter.criterion') }}</label>
                <select id="f-crit" v-model="filters.criterion" class="field">
                  <option value="">{{ t('filter.all') }}</option>
                  <option v-for="c in criteriaPresent" :key="c" :value="c">{{ c }} {{ plainName(c, locale) }}</option>
                </select>
              </div>
              <div class="toolbar__filter">
                <label for="f-source" class="toolbar__label">{{ t('filter.source') }}</label>
                <select id="f-source" v-model="filters.source" class="field">
                  <option value="">{{ t('filter.all') }}</option>
                  <option v-for="s in SOURCES" :key="s" :value="s">{{ t(`source.${s}`) }}</option>
                </select>
              </div>
              <div class="toolbar__filter">
                <label for="f-status" class="toolbar__label">{{ t('filter.status') }}</label>
                <select id="f-status" v-model="filters.status" class="field">
                  <option value="">{{ t('filter.all') }}</option>
                  <option v-for="s in STATUSES" :key="s" :value="s">{{ t(`status.${s}`) }}</option>
                </select>
              </div>
              <button v-if="hasFilters" type="button" class="btn btn--ghost btn--sm toolbar__reset" @click="resetFilters">
                <X :size="14" aria-hidden="true" />{{ t('report.reset') }}
              </button>
            </div>

            <p v-if="filters.reason" class="reason-filter" role="status">
              <span>{{ t('notes.filtered', { reason: t(`reason.${filters.reason}` as MessageKey) }) }}</span>
              <button type="button" class="btn btn--ghost btn--sm" @click="filters.reason = ''">{{ t('notes.clearFilter') }}</button>
            </p>

            <EmptyState v-if="!filtered.length" :title="t('report.emptyFilter.title')" :body="t('report.emptyFilter.body')" :heading-level="3">
              <button type="button" class="btn btn--secondary" @click="resetFilters">{{ t('report.reset') }}</button>
            </EmptyState>

            <div v-else class="groups">
              <section v-for="g in sections" :key="g.code" class="group" :aria-labelledby="`g-${g.code}`">
                <h3 :id="`g-${g.code}`" class="group__h">
                  <CriterionTag :code="g.code" :name="g.name" show-level />
                  <span class="group__n tabular">{{ tp('report.groupCount', g.reviewRows.reduce((n, r) => n + r.items.length, 0) + g.okCount) }}</span>
                </h3>
                <ul v-if="g.reviewRows.length || okVisible(g.code)" class="group__list" role="list">
                  <li v-for="row in g.reviewRows" :key="row.key">
                    <FindingCard
                      :finding="row.lead"
                      :items="row.items.length > 1 ? row.items : undefined"
                      :selected="selectedRow === row"
                      :scan-lang="scan.ui_lang"
                      :base="scan.url"
                      :multi-page="multiPage"
                      :busy="busy"
                      :panel-id="selected ? 'finding-panel' : undefined"
                      @open="open"
                      @decide-one="decideOne"
                    />
                  </li>
                  <template v-if="okVisible(g.code)">
                    <li v-for="row in g.okRows" :key="row.key">
                      <FindingCard
                        :finding="row.lead"
                        :items="row.items.length > 1 ? row.items : undefined"
                        :selected="selectedRow === row"
                        :scan-lang="scan.ui_lang"
                        :base="scan.url"
                        :multi-page="multiPage"
                        :busy="busy"
                        :panel-id="selected ? 'finding-panel' : undefined"
                        @open="open"
                        @decide-one="decideOne"
                      />
                    </li>
                  </template>
                </ul>
                <button
                  v-if="g.okCount && !okForced"
                  type="button"
                  class="okrow"
                  :aria-expanded="openOk.has(g.code)"
                  @click="toggleOk(g.code)"
                >
                  <ShapeIcon shape="circle" color="var(--green)" :size="10" />
                  <span>{{ t('report.okRow', { n: formatNumber(g.okCount) }) }}</span>
                  <span class="okrow__action">
                    {{ openOk.has(g.code) ? t('report.hide') : t('report.show') }}
                    <ChevronDown :size="16" aria-hidden="true" class="okrow__chev" :class="{ 'is-open': openOk.has(g.code) }" />
                  </span>
                </button>
              </section>
            </div>
          </template>
        </section>

        <!-- Coverage, below the findings (UX-4) -->
        <section class="container rep__section" aria-labelledby="rep-coverage">
          <div class="rep__section-head">
            <h2 id="rep-coverage" class="rep__h2">{{ t('report.coverage') }}</h2>
            <p class="rep__section-lede">{{ t('report.coverageLede') }}</p>
          </div>
          <CoverageMap :scan="scan" :findings="findings" :selected="filters.criterion || null" interactive @select="selectCriterion" />
          <RouterLink class="human-cta" :to="{ name: 'human', query: { scan: scan.id } }">
            <span class="human-cta__n tabular">{{ humanCount }}</span>
            <span class="human-cta__text">
              <strong>{{ t('report.humanLink') }}</strong>
              <span>{{ t('report.humanCta', { n: humanCount }) }}</span>
            </span>
            <ArrowRight :size="20" aria-hidden="true" />
          </RouterLink>
        </section>
      </template>
    </div>

    <!-- Detail panel: docked beside the list on wide screens, a modal dialog below 1280 px (UX-14) -->
    <div v-if="overlay" class="rep__scrim" aria-hidden="true" @click="close" />
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
          :items="selectedRow && selectedRow.items.length > 1 ? selectedRow.items : undefined"
          :scan="scan"
          :index="selectedIndex"
          :total="ordered.length"
          :position-label="positionLabel"
          heading-id="finding-title"
          :busy="busy"
          @close="close"
          @prev="move(-1)"
          @next="move(1)"
          @decide="decide"
        />
      </aside>
    </Transition>
  </div>
</template>

<style scoped>
.rep {
  padding-top: var(--s-7);
  transition: padding-right var(--dur-3) var(--ease);
}
.rep--docked {
  padding-right: var(--drawer-w);
}
.rep__loading {
  display: flex;
  align-items: center;
  gap: var(--s-3);
  padding-top: var(--s-8);
  color: var(--muted);
}
.rep__pulse {
  width: 12px;
  height: 12px;
  background: var(--klar-red);
  animation: klar-pulse 1.2s ease-in-out infinite;
}
.rep__state {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--s-4);
  padding-top: var(--s-8);
}
.rep__head {
  display: flex;
  flex-direction: column;
  gap: var(--s-5);
}
.rep__top {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--s-4);
}
.rep__title {
  display: flex;
  flex-direction: column;
  gap: var(--s-3);
  min-width: 0;
}
.rep__h1 {
  overflow-wrap: anywhere;
}
.rep__sub {
  font-size: var(--fs-14);
  color: var(--muted);
}
.rep__url {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--muted);
  font-size: var(--fs-14);
  overflow-wrap: anywhere;
  word-break: break-all;
}
.rep__url:hover {
  color: var(--ink);
}
.rep__lang {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-2) var(--s-3);
  font-size: var(--fs-14);
  color: var(--muted);
}
.rep__metaline {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-2) var(--s-3);
  padding-top: var(--s-4);
  border-top: 1px solid var(--line);
  font-size: var(--fs-14);
  font-weight: 600;
}
.rep__metaline > span[aria-hidden] {
  color: var(--muted);
  font-weight: 400;
}
.rep__details {
  margin-top: calc(-1 * var(--s-3));
  font-size: var(--fs-14);
}
.rep__details > summary {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  cursor: pointer;
  color: var(--muted);
  font-weight: 600;
}
.rep__details[open] > summary {
  margin-bottom: var(--s-3);
}
.rep__details > summary::-webkit-details-marker {
  display: none;
}
.rep__details-chev {
  margin-left: 4px;
  transition: transform var(--dur-1) var(--ease);
}
.rep__details[open] .rep__details-chev {
  transform: rotate(180deg);
}
.rep__details > .notes {
  margin-top: var(--s-3);
}
.rep__more-notes {
  font-size: var(--fs-12);
  color: var(--muted);
}
/* FE-3 (WCAG 1.4.10): the actions wrap at 320 px instead of widening the page. */
.rep__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--s-2);
  min-width: 0;
  max-width: 100%;
}
.rep__top > *,
.rep__actions > * {
  min-width: 0;
  max-width: 100%;
}
.rep__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--s-3) var(--s-6);
  margin: 0;
  padding: var(--s-3) var(--s-4);
  background: var(--surface-2);
  border-radius: var(--r-control);
  font-size: var(--fs-14);
}
.rep__meta dt {
  font-size: var(--fs-12);
  color: var(--muted);
}
.rep__meta dd {
  margin: 2px 0 0;
  font-weight: 600;
}
.rep__next {
  margin-top: var(--s-7);
}
.next {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: var(--s-4);
  padding: var(--s-5);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
  box-shadow: inset 3px 0 0 var(--green);
}
.next--info {
  box-shadow: inset 3px 0 0 var(--blue);
}
.next > svg,
.next > .shape {
  flex: none;
  margin-top: 6px;
  color: var(--blue);
}
.next__text {
  flex: 1 1 320px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.next__title {
  font-size: var(--fs-20);
  font-weight: 700;
  letter-spacing: -0.01em;
}
.next__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--s-2);
  align-self: center;
  min-width: 0;
  max-width: 100%;
}
.next__actions > * {
  max-width: 100%;
}
/* Neutral and informative: a fact about scope, not an error. */
.rep__disclaimer {
  display: flex;
  align-items: flex-start;
  gap: var(--s-3);
  padding: var(--s-3) var(--s-4);
  background: var(--surface-2);
  border-radius: var(--r-control);
  font-size: var(--fs-16);
  line-height: 1.45;
}
.rep__note {
  padding: var(--s-3) var(--s-4);
  background: var(--amber-tint);
  border-radius: var(--r-control);
  font-size: var(--fs-14);
}
.rep__head > :deep(.es) {
  max-width: none;
}
.rep__disclaimer svg {
  flex: none;
  margin-top: 2px;
  color: var(--blue);
}
.rep__section {
  margin-top: var(--s-8);
}
.rep__section-head {
  display: flex;
  flex-direction: column;
  gap: var(--s-2);
  margin-bottom: var(--s-5);
}
.rep__section-head--row {
  flex-direction: row;
  align-items: baseline;
  justify-content: space-between;
  flex-wrap: wrap;
}
.rep__h2 {
  font-size: var(--fs-24);
  font-weight: 700;
  letter-spacing: -0.02em;
}
.rep__section-lede,
.rep__showing {
  color: var(--muted);
  font-size: var(--fs-14);
}
.chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-2);
  min-height: 56px;
  padding: var(--s-2) var(--s-3);
  margin-bottom: var(--s-3);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 40px;
  padding: 0 12px 0 8px;
  border: 1px solid transparent;
  border-radius: var(--r-control);
  background: transparent;
  color: var(--ink);
}
.chip:hover {
  background: var(--surface-2);
}
.chip.is-active {
  background: var(--surface-2);
  border-color: var(--ink);
}
.chip__n {
  font-size: var(--fs-20);
  font-weight: 700;
  letter-spacing: -0.02em;
}
.chips__progress {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-left: auto;
  min-width: 180px;
  padding: 0 var(--s-2);
}
.chips__label {
  font-size: var(--fs-14);
  font-weight: 600;
}
.chips__bar {
  display: block;
  width: 100%;
  height: 4px;
  background: var(--surface-3);
  border-radius: 2px;
  overflow: hidden;
}
.chips__fill {
  display: block;
  height: 100%;
  background: var(--green);
  transform-origin: left;
  transition: transform var(--dur-3) var(--ease);
}
.reason-filter {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-2) var(--s-3);
  margin: calc(-1 * var(--s-2)) 0 var(--s-4);
  padding: var(--s-2) var(--s-3);
  background: var(--blue-tint);
  border-radius: var(--r-control);
  font-size: var(--fs-14);
  font-weight: 600;
}
.okrow {
  display: flex;
  align-items: center;
  gap: var(--s-3);
  width: 100%;
  min-height: 44px;
  padding: 0 var(--s-4);
  border: 0;
  border-top: 1px solid var(--line);
  background: var(--surface);
  color: var(--muted);
  font-size: var(--fs-14);
  text-align: left;
}
.okrow:hover {
  background: var(--surface-2);
  color: var(--ink);
}
.okrow__action {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
  color: var(--blue);
  font-weight: 600;
}
.okrow__chev {
  transition: transform var(--dur-1) var(--ease);
}
.okrow__chev.is-open {
  transform: rotate(180deg);
}
.group__h + .okrow {
  border-top: 0;
}
.human-cta {
  display: flex;
  align-items: center;
  gap: var(--s-5);
  margin-top: var(--s-6);
  padding: var(--s-4) var(--s-5);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
  background: var(--surface);
  color: var(--ink);
  text-decoration: none;
  transition: border-color var(--dur-1) var(--ease);
}
.human-cta:hover {
  border-color: var(--ink);
}
.human-cta__n {
  display: grid;
  place-items: center;
  min-width: 56px;
  height: 56px;
  border: 1.5px solid var(--ink);
  border-radius: 6px;
  font-size: var(--fs-24);
  font-weight: 700;
}
.human-cta__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: var(--fs-14);
  color: var(--muted);
}
.human-cta__text strong {
  font-size: var(--fs-16);
  color: var(--ink);
}
.human-cta svg {
  margin-left: auto;
  flex: none;
}
.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--s-3);
  padding: var(--s-4);
  margin-bottom: var(--s-5);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
}
.toolbar__search {
  flex: 2 1 220px;
  min-width: 0;
}
.toolbar__filter {
  flex: 1 1 118px;
  min-width: 0;
}
.toolbar__label {
  display: block;
  margin-bottom: 4px;
  font-size: var(--fs-12);
  font-weight: 600;
  color: var(--muted);
}
.toolbar__search-field {
  position: relative;
}
.toolbar__search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--muted);
  pointer-events: none;
}
.toolbar__input {
  padding-left: 36px;
  padding-right: 40px;
}
.toolbar__key {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
}
.toolbar__reset {
  --btn-h: 40px;
}
.groups {
  display: flex;
  flex-direction: column;
  gap: var(--s-6);
}
.group__h {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--s-3);
  padding-bottom: var(--s-3);
  border-bottom: 2px solid var(--ink);
  font-size: var(--fs-16);
}
.group__h :deep(.crit) {
  font-size: var(--fs-16);
}
.group__h :deep(.crit__code) {
  font-size: var(--fs-14);
}
.group__h :deep(.crit__name) {
  font-weight: 650;
}
.group__n {
  font-size: var(--fs-14);
  font-weight: 500;
  color: var(--muted);
}
.group__list {
  margin: 0;
  padding: 0;
}
.group__list li + li {
  border-top: 1px solid var(--line);
}
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
.rep--docked + .panel,
.rep--docked .panel {
  box-shadow: none;
}
.rep__scrim {
  position: fixed;
  z-index: 44;
  inset: var(--header-h) 0 0 0;
  background: var(--scrim);
  animation: klar-fade-in var(--dur-2) var(--ease);
}
.panel-enter-active,
.panel-leave-active {
  transition: transform var(--dur-3) var(--ease), opacity var(--dur-2) var(--ease);
}
.panel-enter-from,
.panel-leave-to {
  transform: translateX(24px);
  opacity: 0;
}
@keyframes klar-fade-in {
  from {
    opacity: 0;
  }
}
@media (max-width: 640px) {
  /* One fact per line on phones: no orphaned "·" separators at line ends. */
  .rep__metaline {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  .rep__metaline > span[aria-hidden] {
    display: none;
  }
  .rep__actions {
    width: 100%;
  }
  .human-cta {
    gap: var(--s-3);
  }
}
</style>
