<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, ExternalLink, Pause, Play, Square } from '@lucide/vue'
import type { Outcome, ProgressStep, Scan, ScanControlAction, ScanControlState } from '@/types'
import { KNOWN_STEPS } from '@/types'
import { api, ApiError } from '@/api'
import { formatNumber, polish, t, tp, type MessageKey } from '@/i18n'
import { ensureBooted, lastScanId, refreshHealth, unreachable } from '@/stores/app'
import { applyDone, applyFinding, applyProgress, loadScan, scans } from '@/stores/scans'
import { scanTitle } from '@/lib/format'
import { classifyScanError, hostOf, renderProblem, type Problem, type ProblemAction } from '@/lib/errors'
import { evidenceLine, rowTitle } from '@/lib/finding-text'
import { groupFindings, type FindingGroup } from '@/lib/group'
import { etaText, stepEta } from '@/lib/eta'
import { useDocumentTitle } from '@/composables/useDocumentTitle'
import { useNow } from '@/composables/useNow'
import { useRerun } from '@/composables/useRerun'
import ProgressStepper from '@/components/ProgressStepper.vue'
import VerdictChip from '@/components/VerdictChip.vue'
import CriterionTag from '@/components/CriterionTag.vue'
import ErrorState from '@/components/ErrorState.vue'
import ShapeIcon from '@/components/ShapeIcon.vue'
import CountUp from '@/components/CountUp.vue'

const props = defineProps<{ id: string }>()
const router = useRouter()
const now = useNow(100)
const { rerun, rerunning, rerunError, editAddress, pasteHtml } = useRerun()

const scan = computed<Scan | undefined>(() => scans.get(props.id))
const notFound = ref(false)
/** The page could not reach the server (transport), as opposed to a failed check. */
const transportError = ref<string | null>(null)
const announcement = ref('')
const startedAt = ref<number | null>(null)
const finishedAt = ref<number | null>(null)
const unsubscribe = shallowRef<(() => void) | null>(null)
const cta = ref<HTMLElement | null>(null)

/* ---- Pause / resume / stop: the server confirms at the scan's next step, check or question ---- */
const control = ref<ScanControlState>({ paused: false, stopping: false })
/** An action sent but not yet confirmed by a `control` event ("Pausing…", "Stopping…"). */
const requested = ref<ScanControlAction | null>(null)
const controlBusy = ref(false)
const confirmStop = ref(false)
const pausedAt = ref<number | null>(null)
const pausedMs = ref(0)
/** Step → arrival time of its last progress event (the time left counts down between events). */
const received = ref<Record<string, number>>({})

function setControl(state: ScanControlState) {
  if (state.paused && pausedAt.value == null) pausedAt.value = Date.now()
  if (!state.paused && pausedAt.value != null) {
    pausedMs.value += Date.now() - pausedAt.value
    pausedAt.value = null
  }
  control.value = state
  if (requested.value === 'pause' && state.paused) requested.value = null
  if (requested.value === 'resume' && !state.paused) requested.value = null
  if (requested.value === 'stop' && state.stopping) requested.value = null
}

async function doControl(action: ScanControlAction) {
  confirmStop.value = false
  controlBusy.value = true
  requested.value = action
  try {
    const state = await api().controlScan(props.id, action)
    if (action === 'stop') setControl(state)
  } catch {
    requested.value = null // the scan ended meanwhile: the done event takes over
  } finally {
    controlBusy.value = false
  }
}

/** H1 = the page title once the page is loaded, else the address. */
const head = computed(() => (scan.value ? scanTitle(scan.value) : null))
const headTitle = computed(() => (head.value ? (head.value.title ?? t('report.pastedHtml')) : t('scan.connecting')))
/** One line under the H1: the address when the H1 is a page title, or "Pasted HTML" under a pasted page's own title. */
const subUrl = computed(() => {
  const h = head.value
  if (!h?.url) return null
  const bare = h.url.replace(/^https?:\/\//, '')
  return h.title && !bare.startsWith(h.title) ? bare : null
})
const subPasted = computed(() => !!head.value?.pasted && !!head.value.title)
useDocumentTitle(() => t('scan.docTitle', { url: scan.value ? headTitle.value : '…' }))

const finished = computed(() => scan.value?.state === 'done')
const failedState = computed(() => scan.value?.state === 'error')
/** The stream dropped mid-check: say so instead of a live "Checking" mark. */
const offline = computed(() => transportError.value !== null && !finished.value && !failedState.value)
const phase = computed(() => (failedState.value || offline.value ? 'failed' : finished.value ? 'done' : 'running'))
const stopped = computed(() => finished.value && scan.value?.stats?.stopped === true)
const statusText = computed(() => {
  if (failedState.value) return t('scan.failedEyebrow')
  if (offline.value) return t('offline.badge')
  if (finished.value) return stopped.value ? t('scan.stopped') : t('scan.done')
  if (control.value.stopping || requested.value === 'stop') return t('scan.stopping')
  if (control.value.paused && requested.value !== 'resume') return t('scan.paused')
  if (requested.value === 'pause') return t('scan.pausing')
  return t('scan.eyebrow')
})
/** Running time without the paused time. */
const elapsed = computed(() => {
  if (!startedAt.value) return 0
  const end = finishedAt.value ?? now.value
  const pausing = pausedAt.value != null ? end - pausedAt.value : 0
  return Math.max(0, end - startedAt.value - pausedMs.value - pausing) / 1000
})
/** "about 40 s left": from the running step's pace, once it has one. */
const etaLabel = computed(() => {
  if (phase.value !== 'running' || control.value.paused || control.value.stopping || requested.value === 'stop') return ''
  const running = scan.value?.progress.find((s) => s.state === 'running')
  const sec = running ? stepEta(running, now.value, received.value[running.step], false) : null
  return sec == null ? '' : t('scan.eta', { t: etaText(sec) })
})
const canControl = computed(() => phase.value === 'running' && !!scan.value && !control.value.stopping && requested.value !== 'stop')

/** Newest first; identical findings (and notes with the same reason) collapse into one row with ×N. */
const live = computed(() => groupFindings(scan.value?.findings ?? []).reverse())
function liveTitle(g: FindingGroup) {
  const lang = scan.value?.ui_lang ?? 'en'
  const r = rowTitle(g.lead, lang)
  return { text: r.lang ? polish(r.text, r.lang) : r.text, lang: r.lang ?? undefined }
}

/** Status at a glance: one counter per outcome, counting up as findings stream in. */
const COUNTED: { outcome: Outcome; shape: 'square' | 'diamond' | 'circle'; color: string }[] = [
  { outcome: 'failed', shape: 'square', color: 'var(--klar-red)' },
  { outcome: 'cantTell', shape: 'diamond', color: 'var(--amber)' },
  { outcome: 'passed', shape: 'circle', color: 'var(--green)' },
]
const counts = computed(() => {
  const by: Record<string, number> = {}
  for (const f of scan.value?.findings ?? []) by[f.outcome] = (by[f.outcome] ?? 0) + 1
  return COUNTED.map((c) => ({ ...c, n: by[c.outcome] ?? 0 }))
})
const fmt = (n: number) => formatNumber(Math.round(n))

/** A failed check says what happened in plain words; the raw text stays under Details. */
const failure = computed<Problem | null>(() => {
  const s = scan.value
  if (!s || s.state !== 'error') return null
  return classifyScanError(s.stats, hostOf((s.stats?.final_url as string | undefined) ?? s.url), s.findings.length, s.id)
})
const failureText = computed(() => {
  const p = failure.value
  return p ? renderProblem(p, rerunError.value) : null
})
const ACTION_LABEL: Record<ProblemAction, MessageKey> = {
  edit: 'start.edit',
  retry: 'scan.rerun',
  pasteHtml: 'home.form.pasteHtml',
  editHtml: 'start.editHtml',
  partial: 'fail.partial',
  anyway: 'fail.http.anyway',
}
function act(a: ProblemAction) {
  if (a === 'partial') void router.push({ name: 'report', params: { id: props.id } })
  else if (a === 'edit' || a === 'editHtml') void editAddress(scan.value)
  else if (a === 'pasteHtml') void pasteHtml()
  else void rerun(scan.value)
}

function stepLabel(s: ProgressStep) {
  return (KNOWN_STEPS as readonly string[]).includes(s.step) ? t(`scan.step.${s.step as (typeof KNOWN_STEPS)[number]}`) : s.step
}

function onProgress(data: ProgressStep | ProgressStep[]) {
  const s = scan.value
  if (!s) return
  startedAt.value ??= Date.now()
  const before = new Map(s.progress.map((p) => [p.step, p.state]))
  applyProgress(s, data)
  const at = Date.now()
  for (const p of Array.isArray(data) ? data : [data]) received.value = { ...received.value, [p.step]: at }
  // Announce state changes politely (not every tick of the Apertus counter).
  for (const p of Array.isArray(data) ? data : [data]) {
    if (p.step !== 'done' && before.get(p.step) !== p.state && p.state === 'running') {
      announcement.value = t('scan.announce.step', { step: stepLabel(p), state: t(`scan.state.${p.state}`) })
    }
  }
}

/**
 * The check is complete: the primary action ("Open the report") rises in and takes the
 * focus, unless the person is busy elsewhere on the page (then it waits for them).
 */
async function focusCta() {
  await nextTick()
  const a = document.activeElement
  const idle = !a || a === document.body || a.id === 'main' || a.tagName === 'H1'
  if (idle) cta.value?.querySelector<HTMLElement>('a')?.focus({ preventScroll: true })
}

async function finish(data: Partial<Scan>) {
  const s = scan.value
  if (!s) return
  applyDone(s, data)
  finishedAt.value = Date.now()
  startedAt.value ??= finishedAt.value
  // The server marks unfinished steps "skipped" and writes stats.error without an event: refetch.
  const fresh = await loadScan(props.id, true).catch(() => null)
  void refreshHealth()
  const state = fresh?.state ?? s.state
  if (state === 'error') {
    announcement.value = failureText.value ? `${t('scan.failedEyebrow')}: ${failureText.value.title}` : t('scan.failedEyebrow')
    return
  }
  announcement.value = t('scan.announce.done', { n: formatNumber(s.findings.length) })
  void focusCta()
}

onMounted(async () => {
  await ensureBooted()
  lastScanId.value = props.id
  try {
    const s = await loadScan(props.id, true)
    if (s.state === 'done') {
      await router.replace({ name: 'report', params: { id: props.id } })
      return
    }
    if (s.state === 'error') {
      finishedAt.value = Date.now()
      return
    }
    if (s.state === 'running') startedAt.value = Date.now()
    if (s.stats?.paused === true || s.stats?.stopping === true) {
      setControl({ paused: s.stats.paused === true, stopping: s.stats.stopping === true })
    }
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound.value = true
    else transportError.value = e instanceof Error ? e.message : String(e)
    return
  }
  unsubscribe.value = api().subscribe(props.id, {
    onProgress,
    onFinding: (f) => scan.value && applyFinding(scan.value, f),
    onControl: setControl,
    onDone: (d) => {
      if (pausedAt.value != null) setControl({ paused: false, stopping: control.value.stopping })
      requested.value = null
      void finish(d)
    },
    onError: async (m) => {
      // Maybe the check ended while the stream dropped: ask the server before showing an error.
      const fresh = await loadScan(props.id, true).catch(() => null)
      if (fresh && (fresh.state === 'done' || fresh.state === 'error')) void finish({ state: fresh.state })
      else {
        transportError.value = m
        finishedAt.value ??= Date.now()
      }
    },
  })
})

onBeforeUnmount(() => {
  unsubscribe.value?.()
})

function reload() {
  location.reload()
}
</script>

<template>
  <div class="container scan">
    <ErrorState v-if="notFound" :title="t('scan.notFound')" :body="t('scan.notFoundBody')" :details="`id: ${id}`" :heading-level="1">
      <RouterLink class="btn btn--primary" :to="{ name: 'home' }">{{ t('report.newCheck') }}</RouterLink>
      <RouterLink class="btn btn--ghost" :to="{ name: 'home', hash: '#recent' }">{{ t('recent.title') }}</RouterLink>
    </ErrorState>
    <!-- Nothing loaded and the server is not answering: the problem is the page, with one way forward. -->
    <ErrorState
      v-else-if="transportError !== null && !scan"
      :title="t('offline.title')"
      :body="unreachable ? t('offline.body') : t('start.network.body')"
      :details="transportError"
      :heading-level="1"
      role="alert"
    >
      <button type="button" class="btn btn--primary" @click="reload">{{ t('common.retry') }}</button>
      <RouterLink class="btn btn--ghost" :to="{ name: 'home' }">{{ t('report.newCheck') }}</RouterLink>
    </ErrorState>

    <template v-else>
      <header class="scan__head">
        <div class="scan__title">
          <p class="scan__status m-rise" :class="`is-${phase}`">
            <span class="scan__mark" aria-hidden="true">
              <svg v-if="phase === 'done'" viewBox="0 0 16 16" width="12" height="12" focusable="false">
                <path class="m-draw" pathLength="1" d="M3.2 8.6 6.4 11.6 12.8 4.6" />
              </svg>
            </span>
            <span>{{ statusText }}</span>{{ ' ' }}
            <template v-if="startedAt">
              <span class="scan__sep" aria-hidden="true">·</span>
              <span class="tabular scan__elapsed"
                ><span class="sr-only">{{ t('scan.elapsed') }}: </span>{{ formatNumber(elapsed, { minimumFractionDigits: 1, maximumFractionDigits: 1 }) }} s</span
              >
            </template>
            <template v-if="etaLabel">
              <span class="scan__sep" aria-hidden="true">·</span>
              <span class="tabular scan__elapsed">{{ etaLabel }}</span>
            </template>
          </p>
          <h1 class="h1 scan__h1 m-rise" style="--i: 1" tabindex="-1">{{ headTitle }}</h1>
          <p v-if="subUrl || subPasted" class="scan__sub m-rise" style="--i: 2">
            <a v-if="subUrl && head?.url" :href="head.url" target="_blank" rel="noopener noreferrer" class="mono">
              {{ subUrl }}<ExternalLink :size="13" aria-hidden="true" /><span class="sr-only"> {{ t('finding.newTab') }}</span>
            </a>
            <span v-else>{{ t('report.pastedHtml') }}</span>
          </p>
        </div>
        <div v-if="canControl || confirmStop" class="scan__controls" :class="{ 'scan__controls--confirm': confirmStop }">
          <template v-if="!confirmStop">
            <button
              type="button"
              class="btn btn--ghost"
              :disabled="controlBusy || requested === 'pause' || requested === 'resume'"
              @click="doControl(control.paused ? 'resume' : 'pause')"
            >
              <Play v-if="control.paused" :size="16" aria-hidden="true" />
              <Pause v-else :size="16" aria-hidden="true" />
              {{ control.paused ? t('scan.resume') : t('scan.pause') }}
            </button>
            <button type="button" class="btn btn--ghost" :disabled="controlBusy" @click="confirmStop = true">
              <Square :size="14" aria-hidden="true" /> {{ t('scan.stop') }}
            </button>
          </template>
          <div v-else class="scan__confirm" role="group" :aria-label="t('scan.stop')">
            <span class="scan__confirm-text">{{ t('scan.stopConfirm') }}</span>
            <button type="button" class="btn btn--primary" @click="doControl('stop')">{{ t('scan.stopYes') }}</button>
            <button type="button" class="btn btn--ghost" @click="confirmStop = false">{{ t('scan.stopNo') }}</button>
          </div>
        </div>
        <Transition name="fade-rise">
          <div v-if="finished" ref="cta" class="scan__cta">
            <RouterLink class="btn btn--primary scan__open" :to="{ name: 'report', params: { id } }">
              {{ t('scan.openReport') }} <ArrowRight :size="18" aria-hidden="true" class="scan__open-arrow" />
            </RouterLink>
          </div>
        </Transition>
      </header>

      <div v-if="failure && failureText" class="scan__error">
        <ErrorState :title="failureText.title" :body="failureText.body" :details="failureText.details" role="alert">
          <button type="button" class="btn btn--primary" :disabled="rerunning" @click="act(failure.primary)">{{ t(ACTION_LABEL[failure.primary]) }}</button>
          <button v-for="a in failure.secondary" :key="a" type="button" class="btn btn--ghost" @click="act(a)">{{ t(ACTION_LABEL[a]) }}</button>
        </ErrorState>
      </div>
      <div v-else-if="transportError !== null" class="scan__error">
        <ErrorState :title="t('offline.title')" :body="unreachable ? t('offline.body') : t('start.network.body')" :details="transportError" role="alert">
          <button type="button" class="btn btn--primary" @click="reload">{{ t('common.retry') }}</button>
        </ErrorState>
      </div>

      <div class="scan__grid">
        <section class="scan__progress m-rise" style="--i: 3" aria-labelledby="scan-progress">
          <h2 id="scan-progress" class="scan__h">{{ t('scan.progress') }}</h2>
          <ProgressStepper
            :steps="scan?.progress ?? []"
            :failed="failedState"
            :error-title="failureText?.title"
            :now="now"
            :received="received"
            :paused="control.paused"
          />
        </section>

        <!-- Hidden when a failed check found nothing: an empty "arriving" box would suggest work still going on. -->
        <section v-if="!(failedState && !live.length)" class="live m-rise" style="--i: 4" aria-labelledby="scan-live">
          <div class="live__head">
            <h2 id="scan-live" class="scan__h">{{ t('scan.live') }}</h2>
            <ul class="live__counts" role="list">
              <li v-for="c in counts" :key="c.outcome" class="live__count" :class="{ 'is-zero': !c.n }">
                <ShapeIcon :shape="c.shape" :color="c.color" :size="9" />
                <CountUp class="live__n" :value="c.n" :duration="560" :format="fmt" />{{ ' ' }}
                <span class="live__label">{{ t(`outcome.${c.outcome}`) }}</span>
              </li>
            </ul>
          </div>

          <div v-if="!live.length" class="live__waiting">
            <p class="live__wait-text">{{ t('scan.waiting') }}</p>
            <ul class="live__skel" role="list" aria-hidden="true">
              <li v-for="n in 3" :key="n" class="live__skel-row">
                <span class="skel live__skel-chip" />
                <span class="live__skel-lines">
                  <span class="skel live__skel-line" :style="{ width: `${[62, 78, 54][n - 1]}%` }" />
                  <span class="skel live__skel-line live__skel-line--sm" :style="{ width: `${[38, 46, 30][n - 1]}%` }" />
                </span>
              </li>
            </ul>
          </div>
          <TransitionGroup v-else tag="ul" name="list" class="live__list" role="list">
            <li v-for="g in live" :key="g.key" class="live__item">
              <VerdictChip :outcome="g.lead.outcome" size="sm" />
              <span class="live__main">
                <span class="live__item-head">
                  <CriterionTag :code="g.lead.criterion" :name="g.lead.criterion_name" />
                  <span v-if="g.items.length > 1" class="live__times tabular">×{{ g.items.length }}<span class="sr-only">, {{ tp('group.places', g.items.length) }}</span></span>
                </span>
                <span class="live__impact" :lang="liveTitle(g).lang">{{ liveTitle(g).text }}</span>
                <span v-if="evidenceLine(g.lead)" class="live__evidence mono" :lang="g.lead.content_lang ?? undefined" translate="no">{{ evidenceLine(g.lead) }}</span>
              </span>
            </li>
          </TransitionGroup>
        </section>
      </div>
    </template>

    <p class="sr-only" role="status" aria-live="polite">{{ announcement }}</p>
  </div>
</template>

<style scoped>
.scan {
  padding-top: clamp(var(--s-6), 5vw, var(--s-8));
  padding-bottom: var(--s-8);
}

/* ---- Header: status, title, one address line; the primary action on completion ---- */
.scan__head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: end;
  gap: var(--s-5) var(--s-6);
  padding-bottom: var(--s-6);
  border-bottom: 1px solid var(--line);
}
.scan__title {
  display: flex;
  flex-direction: column;
  gap: var(--s-3);
  min-width: 0;
}
.scan__status {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  gap: 8px;
  min-height: 28px;
  padding: 0 12px 0 10px;
  border: 1px solid var(--line);
  border-radius: var(--r-pill);
  background: var(--surface);
  font-size: var(--fs-14);
  font-weight: 600;
  color: var(--ink);
}
.scan__mark {
  position: relative;
  display: grid;
  place-items: center;
  width: 12px;
  height: 12px;
}
/* Running: a red square, breathing. Done: a green disc whose check draws itself. */
.is-running .scan__mark::before {
  content: '';
  width: 8px;
  height: 8px;
  background: var(--klar-red);
  animation: klar-pulse 1.2s ease-in-out infinite;
}
.is-failed .scan__mark::before {
  content: '';
  width: 8px;
  height: 8px;
  background: var(--klar-red);
}
.is-done .scan__mark {
  border-radius: 50%;
  background: var(--green);
  animation: scan-pop var(--dur-3) var(--ease-spring) both;
}
.is-done .scan__mark svg {
  fill: none;
  stroke: var(--surface);
  stroke-width: 2.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.is-done .scan__mark .m-draw {
  animation-delay: 120ms;
}
@keyframes scan-pop {
  from {
    transform: scale(0.4);
    opacity: 0;
  }
}
.scan__sep {
  color: var(--muted);
}
.scan__elapsed {
  font-weight: 500;
  color: var(--muted);
}
.scan__h1 {
  overflow-wrap: anywhere;
}
.scan__sub {
  font-size: var(--fs-14);
  color: var(--muted);
}
.scan__sub a {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--muted);
  word-break: break-all;
}
.scan__sub a:hover {
  color: var(--ink);
}
.scan__cta {
  justify-self: end;
}
.scan__controls,
.scan__confirm {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-self: end;
  gap: var(--s-2);
}
.scan__controls .btn {
  gap: 6px;
}
/* The stop confirmation takes its own row under the title instead of squeezing it. */
.scan__controls--confirm {
  grid-column: 1 / -1;
  justify-self: start;
}
.scan__confirm-text {
  font-size: var(--fs-14);
  color: var(--muted);
}
.scan__open {
  --btn-h: 52px;
  gap: 10px;
  padding: 0 20px 0 24px;
  border-radius: 12px;
  font-size: var(--fs-16);
  box-shadow: var(--shadow-lift);
}
.scan__open-arrow {
  transition: transform var(--dur-2) var(--ease-out);
}
@media (hover: hover) {
  .scan__open:hover .scan__open-arrow {
    transform: translateX(3px);
  }
}
.scan__error {
  margin-top: var(--s-5);
}

/* ---- Body ---- */
.scan__grid {
  display: grid;
  grid-template-columns: minmax(0, 5fr) minmax(0, 7fr);
  gap: var(--s-8);
  padding-top: var(--s-6);
}
.scan__h {
  font-size: var(--fs-16);
  font-weight: 650;
  letter-spacing: -0.01em;
  color: var(--ink);
}
.scan__progress .scan__h {
  margin-bottom: var(--s-5);
}

/* ---- Live findings ---- */
.live__head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--s-2) var(--s-4);
  margin-bottom: var(--s-4);
}
.live__counts {
  display: flex;
  flex-wrap: wrap;
  gap: var(--s-2) var(--s-4);
  margin: 0;
  padding: 0;
}
.live__count {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-14);
  color: var(--muted);
}
.live__n {
  font-weight: 700;
  color: var(--ink);
}
.live__count.is-zero .live__n {
  color: var(--muted);
}
.live__waiting {
  border-top: 1px solid var(--line);
}
.live__wait-text {
  padding: var(--s-4) 0 var(--s-2);
  font-size: var(--fs-14);
  color: var(--muted);
}
.live__skel {
  margin: 0;
  padding: 0;
}
.live__skel-row {
  display: grid;
  grid-template-columns: 8.5rem minmax(0, 1fr);
  gap: var(--s-4);
  padding: 14px 0;
}
.live__skel-chip {
  width: 76px;
  height: 22px;
  border-radius: var(--r-pill);
}
.live__skel-lines {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.live__skel-line {
  height: 14px;
}
.live__skel-line--sm {
  height: 10px;
}
.live__list {
  position: relative;
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--line);
}
.live__item {
  display: grid;
  grid-template-columns: 8.5rem minmax(0, 1fr);
  gap: var(--s-4);
  align-items: start;
  padding: 14px 0;
  border-bottom: 1px solid var(--line);
  background: var(--bg);
}
.live__item > .verdict {
  justify-self: start;
}
.live__main {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}
.live__item-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px;
}
.live__times {
  padding: 0 7px;
  border-radius: var(--r-pill);
  background: var(--ink);
  color: var(--on-ink);
  font-size: var(--fs-12);
  font-weight: 700;
  line-height: 18px;
}
.live__impact {
  font-size: var(--fs-14);
  color: var(--ink);
}
.live__evidence {
  display: block;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: var(--fs-12);
  color: var(--muted);
}

@media (max-width: 900px) {
  .scan__grid {
    grid-template-columns: 1fr;
    gap: var(--s-7);
  }
}
@media (max-width: 640px) {
  .scan__head {
    grid-template-columns: 1fr;
  }
  .scan__cta,
  .scan__controls,
  .scan__confirm {
    justify-self: stretch;
  }
  .scan__open {
    width: 100%;
  }
}
@media (max-width: 560px) {
  .live__item,
  .live__skel-row {
    grid-template-columns: 1fr;
    gap: var(--s-2);
  }
}
@media (forced-colors: active) {
  .is-running .scan__mark::before,
  .is-failed .scan__mark::before,
  .is-done .scan__mark {
    background: CanvasText;
  }
  .is-done .scan__mark svg {
    stroke: Canvas;
  }
}
</style>
