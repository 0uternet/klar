<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight } from '@lucide/vue'
import { DEMO_NAME, DEMO_URL, isDemoUrl } from '@/config'
import { api, ApiError } from '@/api'
import { formatDate, formatNumber, formatRelative, locale, t, tp, type MessageKey } from '@/i18n'
import { ensureBooted, health, healthRetrying, lastScanId, prefill, refreshHealth, unreachable } from '@/stores/app'
import { scans } from '@/stores/scans'
import { toast } from '@/stores/toast'
import { classifyStartError, hostOf, type Problem, type ProblemAction } from '@/lib/errors'
import { isPasted, scanTitle } from '@/lib/format'
import { toReview } from '@/lib/group'
import { useShortcuts } from '@/composables/useShortcuts'
import { useDocumentTitle } from '@/composables/useDocumentTitle'
import UrlInput from '@/components/UrlInput.vue'
import ErrorState from '@/components/ErrorState.vue'
import type { CheckInput, ScanSummary } from '@/types'
import VerdictChip from '@/components/VerdictChip.vue'
import CriterionTag from '@/components/CriterionTag.vue'
import ShapeIcon from '@/components/ShapeIcon.vue'
import SwissBadge from '@/components/SwissBadge.vue'
import SourceLink from '@/components/SourceLink.vue'
import CountUp from '@/components/CountUp.vue'
import { reducedMotion } from '@/lib/motion'
import { SOURCES_CHECKED } from '@/data/swiss-law'

const router = useRouter()
const route = useRoute()
const field = ref<InstanceType<typeof UrlInput> | null>(null)
const busy = ref(false)

useDocumentTitle(() => t('home.docTitle'), true)

useShortcuts({
  '/': (e) => {
    e.preventDefault()
    field.value?.focus()
  },
})

/** The second headline line, with the brand's red full stop (as in the logo). */
const BRAND = 'Klar.'
const titleB = computed(() => t('home.titleB').split(/(Klar\.)/))

const isReplay = computed(() => health.value?.mode === 'replay')
/** UX-8 / M3: replay mode without any recorded answer. */
const noRecordings = computed(() => {
  const r = health.value?.replay_recorded
  return isReplay.value && !!r && typeof r.records === 'number' && r.records === 0
})
/** UX-22 / M4: the model endpoint did not answer the start-up probe (null = unknown: say nothing). */
const llmDown = computed(() => !isReplay.value && health.value?.llm_reachable === false)

/**
 * UX-17 / M5: at the moment of submitting, say where pages go when they leave the network.
 * Swiss cloud is said by the Swiss badge above the field ("Processed in Switzerland · provider"),
 * so only the external endpoint keeps this warning line, with its way to change it.
 */
const sendNotice = computed(() => {
  const h = health.value
  if (h?.mode === 'external') return { shape: 'diamond' as const, color: 'var(--amber)', text: t('notice.external', { host: h.base_url_host ?? t('common.unknown') }) }
  return null
})

/* ---- Why it matters in Switzerland (facts: _prive/SWISS_FACTS.md) ---------------- */

const GAP = { n: 5, total: 70 } as const
const AUDIT = { min: 3800, max: 8500 } as const
const checkedOn = computed(() => formatDate(SOURCES_CHECKED, false))
/** The numbers count up when the section scrolls into view (at once with reduced motion). */
const why = ref<HTMLElement | null>(null)
const whySeen = ref(false)
let whyIo: IntersectionObserver | null = null
onMounted(() => {
  if (reducedMotion() || typeof IntersectionObserver === 'undefined' || !why.value) {
    whySeen.value = true
    return
  }
  whyIo = new IntersectionObserver(
    (entries) => {
      if (!entries.some((e) => e.isIntersecting)) return
      whySeen.value = true
      whyIo?.disconnect()
    },
    { rootMargin: '0px 0px -8% 0px', threshold: 0.12 },
  )
  whyIo.observe(why.value)
})
onBeforeUnmount(() => whyIo?.disconnect())

/* ---- Problems, each with one way forward --------------------------------- */

const startProblem = ref<Problem | null>(null)
/** M10: in replay mode, a non-demo address gets a choice instead of a scan that can only come back grey. */
const replayGate = ref<{ host: string } | null>(null)
let lastInput: CheckInput | null = null
const notice = ref<HTMLElement | null>(null)

async function focusNotice() {
  await nextTick()
  const h = notice.value?.querySelector<HTMLElement>('h2')
  h?.setAttribute('tabindex', '-1')
  h?.focus()
}

const sameUrl = (a: string, b: string) => a.replace(/\/+$/, '') === b.replace(/\/+$/, '')

/* M17: one automatic retry after 15 s, with a visible countdown. */
const countdown = ref<number | null>(null)
let countdownTimer: number | undefined
function stopCountdown() {
  window.clearInterval(countdownTimer)
  countdown.value = null
}
function startCountdown(seconds: number) {
  stopCountdown()
  countdown.value = seconds
  countdownTimer = window.setInterval(() => {
    if (countdown.value === null) return
    countdown.value--
    if (countdown.value <= 0) {
      stopCountdown()
      retryStart(true)
    }
  }, 1000)
}
onBeforeUnmount(stopCountdown)
let autoRetried = false

async function onSubmit(input: CheckInput, opts: { bypassGate?: boolean; auto?: boolean } = {}) {
  startProblem.value = null
  replayGate.value = null
  stopCountdown()
  if (!opts.auto) autoRetried = false
  lastInput = input
  await ensureBooted()
  // UX-1: only external addresses are gated; pasted HTML and the demo always run.
  if (isReplay.value && 'url' in input && !isDemoUrl(input.url) && !opts.bypassGate) {
    replayGate.value = { host: hostOf(input.url) }
    void focusNotice()
    return
  }
  busy.value = true
  try {
    const client = api()
    const body = 'url' in input ? { url: input.url, ui_lang: locale.value } : { html: input.html, ui_lang: locale.value }
    const { id } = await client.createScan(body)
    if (client.kind === 'mock' && !('url' in input && sameUrl(input.url, DEMO_URL))) toast(t('mock.sample'), 'info', 6000)
    lastScanId.value = id
    await router.push({ name: 'scan', params: { id } })
  } catch (e) {
    const status = e instanceof ApiError ? e.status : 0
    const message = e instanceof Error ? e.message : String(e)
    const p = classifyStartError(status, message, 'url' in input ? hostOf(input.url) : '')
    startProblem.value = p
    if (p.autoRetry && !autoRetried) {
      autoRetried = true
      startCountdown(p.autoRetry)
    }
    void focusNotice()
  } finally {
    busy.value = false
  }
}

function retryStart(auto = false) {
  if (lastInput) void onSubmit(lastInput, { auto, bypassGate: true })
}
function editAddress() {
  startProblem.value = null
  stopCountdown()
  field.value?.focus()
}
function pasteHtmlInstead() {
  startProblem.value = null
  replayGate.value = null
  field.value?.setMode('html')
}
const ACTION_LABEL: Record<ProblemAction, MessageKey> = {
  edit: 'start.edit',
  retry: 'common.retry',
  pasteHtml: 'home.form.pasteHtml',
  editHtml: 'start.editHtml',
  partial: 'fail.partial',
  anyway: 'fail.http.anyway',
}
function act(a: ProblemAction) {
  if (a === 'retry') retryStart()
  else if (a === 'pasteHtml') pasteHtmlInstead()
  else if (a === 'editHtml') {
    startProblem.value = null
    field.value?.setMode('html')
  } else editAddress()
}
const problemText = computed(() => {
  const p = startProblem.value
  if (!p) return null
  return {
    title: t(p.title, p.params),
    body: t(p.body, p.params),
    details: [p.detailsLead ? t(p.detailsLead) : null, p.details ? t('start.server.detail', { detail: p.details }) : null].filter(Boolean).join('\n') || null,
  }
})

const retrying = ref(false)
async function retryHealth() {
  retrying.value = true
  await refreshHealth()
  retrying.value = false
}

function tryDemo() {
  replayGate.value = null
  field.value?.fill(DEMO_URL)
  void onSubmit({ url: DEMO_URL })
}
function checkAnyway() {
  if (lastInput) void onSubmit(lastInput, { bypassGate: true })
}

/* ---- Recent checks (UX-10): finished scans already on this server ---------- */

interface Recent {
  id: string
  title: string
  when: string
  toReview: number | null
}
const recent = ref<Recent[]>([])
const demoReportId = ref<string | null>(null)

async function loadRecent() {
  if (unreachable.value) return
  let list: ScanSummary[]
  try {
    list = await api().listScans(20)
  } catch {
    return
  }
  const done = list.filter((s) => s.state === 'done')
  demoReportId.value = done.find((s) => isDemoUrl(s.url))?.id ?? null
  const top = done.slice(0, 5)
  const full = await Promise.all(top.map((s) => api().getScan(s.id).catch(() => null)))
  recent.value = top.map((s, i) => {
    const scan = full[i]
    if (scan && !scans.has(scan.id)) scans.set(scan.id, scan)
    const head = scan ? scanTitle(scan) : null
    return {
      id: s.id,
      title: head?.title ?? (isPasted(s.url) ? t('recent.pasted') : hostOf(s.url)),
      when: s.created_at,
      toReview: scan ? scan.findings.filter((f) => toReview(f) && f.status === 'to_review').length : null,
    }
  })
}

onMounted(async () => {
  if (route.query.focus) field.value?.focus()
  await ensureBooted()
  const p = prefill.value
  if (p) {
    prefill.value = null
    if (p.url) field.value?.fill(p.url)
    if (p.mode === 'html') field.value?.setMode('html')
    else field.value?.focus()
  }
  void loadRecent()
})
</script>

<template>
  <div class="home">
    <section class="container hero" aria-labelledby="home-title">
      <h1 id="home-title" class="hero__title" tabindex="-1">
        <span class="hero__line hero__line--muted m-rise" style="--i: 0">{{ t('home.titleA') }}</span>{{ ' ' }}
        <span class="hero__line m-rise" style="--i: 1"
          ><template v-for="(part, i) in titleB" :key="i"
            ><span v-if="part === BRAND" class="hero__brand">Klar<span class="hero__dot">.</span></span
            ><template v-else>{{ part }}</template></template
          ></span
        >
      </h1>

      <div class="hero__grid">
        <div class="hero__main">
          <p class="hero__lede m-rise" style="--i: 2">{{ t('home.lede') }}</p>

          <!-- Where the model runs, from /api/health: the Swiss claim only when it is true. -->
          <SwissBadge v-if="!unreachable" class="hero__swiss m-rise" style="--i: 3" :health="health" />

          <!-- Blocking problems, each with one way forward -->
          <div ref="notice" class="hero__notice">
            <ErrorState v-if="unreachable" :title="t('offline.title')" :body="t('offline.body')" :details="t('offline.detail')" role="alert">
              <button type="button" class="btn btn--primary" :disabled="retrying" @click="retryHealth">{{ t('common.retry') }}</button>
              <span v-if="healthRetrying" class="hero__retrying" role="status">{{ t('offline.retrying') }}</span>
            </ErrorState>
            <ErrorState v-else-if="startProblem && problemText" :title="problemText.title" :body="problemText.body" :details="problemText.details">
              <button type="button" class="btn btn--primary" :disabled="busy" @click="act(startProblem.primary)">{{ t(ACTION_LABEL[startProblem.primary]) }}</button>
              <button v-for="a in startProblem.secondary" :key="a" type="button" class="btn btn--ghost" @click="act(a)">{{ t(ACTION_LABEL[a]) }}</button>
              <span v-if="countdown !== null" class="hero__retrying tabular" role="status">{{ t('start.busy.countdown', { s: formatNumber(countdown) }) }}</span>
            </ErrorState>
            <ErrorState v-else-if="replayGate" tone="info" :title="t('replay.gate.title')" :body="t('replay.gate.body', { host: replayGate.host })">
              <button type="button" class="btn btn--primary" :disabled="busy" @click="tryDemo">
                {{ t('home.demo.primary') }} <ArrowRight :size="18" aria-hidden="true" />
              </button>
              <button type="button" class="btn btn--secondary" :disabled="busy" @click="checkAnyway">{{ t('replay.gate.anyway') }}</button>
              <RouterLink class="hero__link" :to="{ name: 'about', hash: '#connect' }">{{ t('replay.connectShort') }}</RouterLink>
            </ErrorState>
          </div>

          <!-- Replay mode: the demo site is the first, primary action -->
          <div v-if="isReplay && !replayGate && !unreachable" class="demo-cta m-rise" style="--i: 3">
            <div class="demo-cta__row">
              <button type="button" class="btn btn--primary demo-cta__btn" :disabled="busy" @click="tryDemo">
                {{ t('home.demo.primary') }} <ArrowRight :size="20" aria-hidden="true" />
              </button>
              <RouterLink v-if="demoReportId" class="btn btn--ghost demo-cta__open" :to="{ name: 'report', params: { id: demoReportId } }">
                {{ t('home.demo.openReport') }}
              </RouterLink>
            </div>
            <p class="demo-cta__sub">{{ t('home.demo.primarySub') }}</p>
          </div>

          <UrlInput
            ref="field"
            class="hero__form m-rise"
            :class="{ 'hero__form--secondary': isReplay }"
            style="--i: 3"
            :busy="busy"
            :secondary="isReplay || unreachable || !!startProblem || !!replayGate"
            :label="isReplay ? t('home.form.labelReplay') : undefined"
            @submit="onSubmit"
          >
            <template v-if="!isReplay" #aside>
              <button type="button" class="demo-link" :disabled="busy" @click="tryDemo">
                <ShapeIcon shape="square" color="var(--klar-red)" :size="8" />
                <span class="demo-link__name">{{ t('home.demo.secondary') }}</span>{{ ' ' }}
                <span class="demo-link__sub">{{ DEMO_NAME }}</span>
                <ArrowRight :size="16" aria-hidden="true" class="demo-link__arrow" />
              </button>
            </template>
          </UrlInput>

          <p v-if="sendNotice" class="send-notice">
            <ShapeIcon :shape="sendNotice.shape" :color="sendNotice.color" :size="9" />
            <span>{{ sendNotice.text }}</span>
            <RouterLink class="send-notice__link" :to="{ name: 'about', hash: '#connect' }">{{ t('notice.change') }}</RouterLink>
          </p>

          <!-- Not blocking: checks still run. One compact line, one way forward. -->
          <div v-if="!unreachable && (llmDown || noRecordings)" class="hint m-rise" style="--i: 4">
            <ShapeIcon shape="diamond" color="var(--amber)" :size="10" />
            <div class="hint__body">
              <p v-if="llmDown">
                <strong>{{ t('llm.down.title') }}.</strong> {{ t('llm.down.body', { host: health?.base_url_host ?? t('common.unknown') }) }}
              </p>
              <p v-else>
                <strong>{{ t('replay.empty.title') }}.</strong> {{ t('replay.empty.body') }}
              </p>
              <div class="hint__actions">
                <button v-if="llmDown" type="button" class="hint__btn" :disabled="retrying" @click="retryHealth">{{ t('common.retry') }}</button>
                <RouterLink class="hint__link" :to="{ name: 'about', hash: '#connect' }">{{ t('notes.connect') }}</RouterLink>
                <details v-if="llmDown ? health?.llm_error : true" class="hint__details">
                  <summary>{{ t('error.details') }}</summary>
                  <pre class="mono" translate="no">{{ llmDown ? health?.llm_error : t('replay.empty.detail') }}</pre>
                </details>
              </div>
            </div>
          </div>
        </div>

        <!--
          The proof of the idea, as a short story played once on load (≤ 4 s, no loop):
          the scanner passes alt="Bild", Klar. flags the meaning, a person accepts.
          An illustration, labelled as such; screen readers get one sentence (the figure's label).
        -->
        <figure v-if="!unreachable" v-reveal="3" class="story" role="img" :aria-label="t('home.story.label')">
          <!-- inert: a picture, not controls; its text is never focused or read on its own. -->
          <div class="story__card" inert>
            <span class="story__tag">{{ t('home.story.tag') }}</span>
            <div class="story__page">
              <span class="story__chart">
                <span v-for="(h, i) in [38, 52, 46, 68, 84]" :key="i" class="story__bar" :style="{ height: `${h}%`, '--i': i }" />
              </span>
              <code class="story__code" lang="de" translate="no"
                ><span class="tk-p">&lt;</span><span class="tk-t">img</span> <span class="tk-a">src</span>=<span class="tk-v">"steuern.png"</span
                ><br /><span class="story__indent"> </span><span class="tk-a">alt</span>=<span class="tk-v">"Bild"</span><span class="tk-p">&gt;</span></code
              >
            </div>

            <ol class="story__rows">
              <li class="story__row story__row--scanner">
                <span class="story__who">{{ t('home.story.scanner') }}</span>
                <span class="story__what">
                  <VerdictChip outcome="passed" size="sm" />
                  <span class="story__muted">{{ t('home.story.present') }}</span>
                </span>
              </li>
              <li class="story__row story__row--klar">
                <span class="story__who story__who--klar">Klar<span class="hero__dot">.</span></span>
                <span class="story__what story__what--stack">
                  <span class="story__chips">
                    <VerdictChip outcome="failed" size="sm" />
                    <CriterionTag code="1.1.1" />
                  </span>
                  <span class="story__impact">{{ t('home.story.impact') }}</span>
                  <span class="story__diff" lang="de" translate="no">
                    <span class="story__del"><span class="story__sign">−</span><code>alt="Bild"</code></span>
                    <span class="story__add"><span class="story__sign">+</span><code>alt="Steuerertrag 2021–2025: steigend"</code></span>
                  </span>
                </span>
              </li>
              <li class="story__row story__row--you">
                <span class="story__who">{{ t('home.story.you') }}</span>
                <span class="story__what">
                  <span class="story__accept">
                    <span class="story__accept-bg" />
                    <svg class="story__check" viewBox="0 0 16 16" width="16" height="16" focusable="false">
                      <path class="m-draw" pathLength="1" d="M3.2 8.6 6.4 11.6 12.8 4.6" />
                    </svg>
                    <span class="story__label-a">{{ t('finding.accept') }}</span>
                    <span class="story__label-b">{{ t('status.accepted') }}</span>
                  </span>
                </span>
              </li>
            </ol>
          </div>
        </figure>
      </div>
    </section>

    <!-- Why it matters in Switzerland: the law, the gap, the value. Context, not legal advice. -->
    <section ref="why" class="container why" aria-labelledby="why-title">
      <h2 id="why-title" v-reveal class="why__title">{{ t('swiss.title') }}</h2>
      <ul class="why__cols" role="list">
        <li v-reveal="1" class="why__col">
          <p class="why__big" translate="no">WCAG 2.1 AA</p>
          <p class="why__body">{{ t('swiss.law.body') }}</p>
          <SourceLink class="why__src" source="behig" :label="t('swiss.law.source')" />
        </li>
        <li v-reveal="2" class="why__col">
          <p class="why__big">
            <span aria-hidden="true"
              ><CountUp v-if="whySeen" :value="GAP.n" /><template v-else>{{ formatNumber(GAP.n) }}</template
              ><span class="why__small">/{{ formatNumber(GAP.total) }}</span></span
            ><span class="sr-only">{{ t('swiss.gap.sr', { n: formatNumber(GAP.n), total: formatNumber(GAP.total) }) }}</span>
          </p>
          <p class="why__body">{{ t('swiss.gap.body') }}</p>
          <SourceLink class="why__src" source="correctiv" :label="t('swiss.gap.source')" />
        </li>
        <li v-reveal="3" class="why__col">
          <p class="why__big">
            <span aria-hidden="true"
              ><span class="why__small why__small--lead">CHF</span
              ><CountUp v-if="whySeen" :value="AUDIT.min" /><template v-else>{{ formatNumber(AUDIT.min) }}</template>–<CountUp
                v-if="whySeen"
                :value="AUDIT.max"
              /><template v-else>{{ formatNumber(AUDIT.max) }}</template></span
            ><span class="sr-only">{{ t('swiss.value.sr', { min: formatNumber(AUDIT.min), max: formatNumber(AUDIT.max) }) }}</span>
          </p>
          <p class="why__body">{{ t('swiss.value.body') }}</p>
          <SourceLink class="why__src" source="accessForAll" :label="t('swiss.value.source')" />
        </li>
      </ul>
      <p v-reveal="4" class="why__sov">
        <span class="why__mark" aria-hidden="true" />
        <span class="why__sov-text">{{ t('swiss.sov.body') }}{{ ' ' }}<SourceLink source="bsAi" :label="t('swiss.sov.source')" /></span>
      </p>
      <p v-reveal="5" class="why__fine">{{ t('swiss.fine', { date: checkedOn }) }}</p>
    </section>

    <section v-if="recent.length" id="recent" class="container recent" aria-labelledby="recent-title">
      <h2 id="recent-title" v-reveal class="recent__title">{{ t('recent.title') }}</h2>
      <ul class="recent__list" role="list">
        <li v-for="(r, i) in recent" :key="r.id" v-reveal="i + 1">
          <RouterLink class="recent__item lift" :to="{ name: 'report', params: { id: r.id } }">
            <ShapeIcon
              :shape="r.toReview === null ? 'ring' : r.toReview > 0 ? 'diamond' : 'circle'"
              :color="r.toReview === null ? 'var(--grey-shape)' : r.toReview > 0 ? 'var(--amber)' : 'var(--green)'"
              :size="10"
            />
            <span class="recent__name">{{ r.title }}</span>{{ ' ' }}
            <span class="recent__when">{{ formatRelative(r.when) }}</span>{{ ' ' }}
            <span v-if="r.toReview !== null" class="recent__status tabular" :class="{ 'is-clear': r.toReview === 0 }">
              {{ r.toReview > 0 ? tp('recent.toReview', r.toReview) : t('recent.nothing') }}
            </span>
            <ArrowRight :size="16" aria-hidden="true" class="recent__arrow" />
          </RouterLink>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
/* ---- Hero ---------------------------------------------------------------- */
.hero {
  padding-top: clamp(40px, 7vw, 96px);
  padding-bottom: var(--s-8);
}
.hero__title {
  font-size: clamp(2.25rem, 1.1rem + 3.4vw, 3.75rem);
  line-height: 1.04;
  font-weight: 700;
  letter-spacing: -0.035em;
  text-wrap: balance;
}
.hero__line {
  display: block;
}
.hero__line--muted {
  color: var(--muted);
}
.hero__brand {
  white-space: nowrap;
}
.hero__dot {
  color: var(--klar-red);
}
.hero__grid {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  column-gap: var(--gutter);
  align-items: start;
  margin-top: clamp(var(--s-6), 4vw, var(--s-7));
}
.hero__main {
  grid-column: 1 / span 6;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.hero__lede {
  max-width: 46ch;
  font-size: var(--fs-20);
  line-height: 1.5;
  color: var(--muted);
  text-wrap: pretty;
}
.hero__notice {
  width: 100%;
}
.hero__notice:not(:empty) {
  margin-top: var(--s-6);
}
.hero__form {
  margin-top: var(--s-6);
}
.hero__form--secondary {
  margin-top: var(--s-7);
}
.hero__retrying {
  align-self: center;
  font-size: var(--fs-14);
  color: var(--muted);
}
.hero__link {
  align-self: center;
  font-size: var(--fs-14);
  font-weight: 600;
}

/* Replay mode: the demo is the primary action. */
.demo-cta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--s-3);
  margin-top: var(--s-6);
}
.demo-cta__row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-2);
}
.demo-cta__btn {
  --btn-h: 56px;
  gap: 12px;
  padding: 0 24px 0 28px;
  border-radius: 12px;
  font-size: var(--fs-20);
}
.demo-cta__open {
  --btn-h: 56px;
}
.demo-cta__sub {
  font-size: var(--fs-14);
  color: var(--muted);
}

/* Live modes: the demo is one quiet, obvious shortcut under the field. */
.demo-link {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 40px;
  margin-left: -2px;
  padding: 0 14px 0 13px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-pill);
  color: var(--ink);
  font-size: var(--fs-14);
  transition: border-color var(--dur-2) var(--ease-out), transform var(--dur-1) var(--ease-out);
}
.demo-link:hover:not(:disabled) {
  border-color: var(--control-border);
}
.demo-link:active:not(:disabled) {
  transform: scale(0.98);
}
.demo-link:disabled {
  opacity: 0.55;
  cursor: progress;
}
.demo-link__name {
  font-weight: 600;
}
.demo-link__sub {
  color: var(--muted);
}
.demo-link__arrow {
  transition: transform var(--dur-2) var(--ease-out);
}
@media (hover: hover) {
  .demo-link:hover:not(:disabled) .demo-link__arrow {
    transform: translateX(3px);
  }
}

.send-notice {
  max-width: 640px;
  margin-top: var(--s-4);
  font-size: var(--fs-14);
  color: var(--muted);
}
.send-notice > svg {
  margin-right: 8px;
  vertical-align: 0;
}
.send-notice__link {
  margin-left: 8px;
  font-weight: 600;
  white-space: nowrap;
}

/* A compact, non-blocking notice. */
.hint {
  display: flex;
  align-items: flex-start;
  gap: var(--s-3);
  width: 100%;
  max-width: 640px;
  margin-top: var(--s-6);
  padding-top: var(--s-4);
  border-top: 1px solid var(--line);
  font-size: var(--fs-14);
  line-height: 1.5;
}
.hint > svg {
  margin-top: 5px;
}
.hint__body {
  display: flex;
  flex-direction: column;
  gap: var(--s-2);
  min-width: 0;
  color: var(--muted);
}
.hint__body strong {
  color: var(--ink);
  font-weight: 650;
}
.hint__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-2) var(--s-4);
}
.hint__btn {
  min-height: 32px;
  padding: 0 12px;
  border: 1px solid var(--control-border);
  border-radius: var(--r-pill);
  background: var(--surface);
  color: var(--ink);
  font-size: var(--fs-14);
  font-weight: 600;
}
.hint__btn:hover:not(:disabled) {
  background: var(--surface-2);
}
.hint__link {
  font-weight: 600;
}
.hint__details summary {
  cursor: pointer;
  color: var(--muted);
}
.hint__details pre {
  margin-top: var(--s-2);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-size: var(--fs-12);
}

/* ---- The story (illustration) --------------------------------------------- */
.story {
  --t-scanner: 700ms;
  --t-klar: 1500ms;
  --t-mark: 2250ms;
  --t-you: 2700ms;
  --t-press: 3150ms;
  --t-accept: 3300ms;
  grid-column: 8 / span 5;
  margin: 0;
}
.story__card {
  position: relative;
  padding: var(--s-5);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 16px;
  box-shadow: var(--shadow-lift);
}
.story__tag {
  position: absolute;
  top: var(--s-4);
  right: var(--s-4);
  padding: 1px 9px;
  border: 1px dashed var(--control-border);
  border-radius: var(--r-pill);
  font-size: var(--fs-12);
  font-weight: 600;
  color: var(--muted);
}
.story__page {
  display: flex;
  align-items: center;
  gap: var(--s-4);
  padding-right: 96px;
}
.story__chart {
  flex: none;
  display: flex;
  align-items: flex-end;
  gap: 4px;
  width: 76px;
  height: 56px;
  padding: 8px 8px 0;
  background: var(--surface-2);
  border-radius: 8px;
  box-shadow: inset 0 -1px 0 var(--line);
}
.story__bar {
  flex: 1;
  background: var(--blue);
  border-radius: 2px 2px 0 0;
  transform-origin: bottom;
  animation: story-bar var(--dur-4) var(--ease-out) both;
  animation-delay: calc(250ms + var(--i) * var(--stagger));
}
.story__bar:last-child {
  background: var(--ink);
}
.story__code {
  font-size: 0.8125rem;
  line-height: 1.6;
  white-space: nowrap;
}
.story__indent {
  display: inline-block;
  width: 2ch;
}
.tk-p {
  color: var(--syn-punct);
}
.tk-t {
  color: var(--syn-tag);
  font-weight: 700;
}
.tk-a {
  color: var(--syn-attr);
}
.tk-v {
  color: var(--syn-value);
}
.story__rows {
  margin: var(--s-5) 0 0;
  padding: 0;
  list-style: none;
}
.story__row {
  display: grid;
  grid-template-columns: 4.25rem minmax(0, 1fr);
  gap: var(--s-3);
  align-items: start;
  padding: var(--s-4) 0;
  border-top: 1px solid var(--line);
}
.story__row:last-child {
  padding-bottom: 0;
}
.story__row--you {
  align-items: center;
}
.story__row--you .story__who {
  padding-top: 0;
}
.story__who {
  padding-top: 2px;
  font-size: var(--fs-12);
  font-weight: 600;
  letter-spacing: 0.01em;
  color: var(--muted);
}
.story__who--klar {
  color: var(--ink);
  font-weight: 700;
}
.story__what {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-2) var(--s-3);
  min-width: 0;
}
.story__what--stack {
  flex-direction: column;
  align-items: stretch;
  gap: var(--s-3);
}
.story__muted {
  font-size: var(--fs-14);
  color: var(--muted);
}
.story__chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-2) var(--s-3);
}
.story__impact {
  font-size: var(--fs-16);
  font-weight: 600;
  line-height: 1.35;
  letter-spacing: -0.01em;
  text-wrap: pretty;
}
.story__diff {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--r-control);
  font-family: var(--font-mono);
  font-size: 0.8125rem;
  line-height: 1.6;
}
.story__del,
.story__add {
  position: relative;
  display: grid;
  grid-template-columns: 1.75em minmax(0, 1fr);
  padding: 3px 10px 3px 0;
  isolation: isolate;
}
.story__del {
  background: var(--diff-del);
}
.story__add {
  background: var(--diff-add);
}
/* The fix gets marked like a highlighter: a layer that sweeps in (transform only). */
.story__add::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: -1;
  background: var(--diff-add-strong);
  transform-origin: left center;
  animation: story-sweep var(--dur-4) var(--ease-out) both;
  animation-delay: var(--t-mark);
}
.story__del code,
.story__add code {
  font-size: inherit;
  overflow-wrap: anywhere;
}
.story__del code {
  text-decoration: line-through;
  text-decoration-thickness: 1px;
}
.story__sign {
  text-align: center;
  font-weight: 700;
}
.story__del .story__sign {
  color: var(--red-text);
}
.story__add .story__sign {
  color: var(--green);
}

/* Accept: pressed, the check draws itself, the label turns to "Accepted". */
/* Two columns (check, label); "Accept" spans both so it sits centred before the check appears. */
.story__accept {
  position: relative;
  display: inline-grid;
  grid-template-columns: 16px auto;
  align-items: center;
  column-gap: 6px;
  height: 34px;
  padding: 0 14px 0 11px;
  border: 1px solid var(--control-border);
  border-radius: var(--r-control);
  font-size: var(--fs-14);
  font-weight: 600;
  isolation: isolate;
  animation: story-press var(--dur-3) var(--ease-out) both;
  animation-delay: var(--t-press);
}
.story__accept-bg {
  position: absolute;
  inset: -1px;
  z-index: -1;
  background: var(--green-tint);
  border: 1px solid var(--green);
  border-radius: inherit;
  animation: story-in var(--dur-3) var(--ease-out) both;
  animation-delay: var(--t-accept);
}
.story__check {
  grid-area: 1 / 1;
  fill: none;
  stroke: var(--green);
  stroke-width: 2.25;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.story__check .m-draw {
  animation-delay: var(--t-accept);
}
.story__label-a {
  grid-area: 1 / 1 / 2 / 3;
  justify-self: center;
  color: var(--ink);
  opacity: 0;
  animation: story-out var(--dur-2) var(--ease-out) both;
  animation-delay: var(--t-accept);
}
.story__label-b {
  grid-area: 1 / 2;
  color: var(--green);
  animation: story-in var(--dur-3) var(--ease-out) both;
  animation-delay: var(--t-accept);
}

/* Rows enter in turn. The resting state is the final frame (reduced motion shows it at once). */
.story__row--scanner {
  animation: story-rise var(--dur-4) var(--ease-out) both;
  animation-delay: var(--t-scanner);
}
.story__row--klar {
  animation: story-slide var(--dur-4) var(--ease-out) both;
  animation-delay: var(--t-klar);
}
.story__row--you {
  animation: story-rise var(--dur-4) var(--ease-out) both;
  animation-delay: var(--t-you);
}
@keyframes story-bar {
  from {
    transform: scaleY(0);
  }
}
@keyframes story-rise {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
}
@keyframes story-slide {
  from {
    opacity: 0;
    transform: translateX(16px);
  }
}
@keyframes story-sweep {
  from {
    transform: scaleX(0);
  }
}
@keyframes story-press {
  50% {
    transform: scale(0.94);
  }
}
@keyframes story-in {
  from {
    opacity: 0;
  }
}
@keyframes story-out {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}
/* The story waits until it scrolls into view (v-reveal), so on phones it plays where it is seen. */
.story[data-reveal='out'] *,
.story[data-reveal='out'] *::before {
  animation-play-state: paused;
}
@media (prefers-reduced-motion: reduce) {
  .story,
  .story *,
  .story *::before {
    animation: none !important;
  }
}

/* ---- Swiss badge (hero) ------------------------------------------------------ */
.hero__swiss {
  margin-top: var(--s-5);
}

/* ---- Why it matters in Switzerland ------------------------------------------ */
.why {
  padding-top: var(--s-7);
  padding-bottom: var(--s-8);
}
.why__title {
  font-size: var(--fs-32);
  line-height: 1.15;
  font-weight: 700;
  letter-spacing: -0.03em;
  text-wrap: balance;
}
.why__cols {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--gutter);
  margin: var(--s-6) 0 0;
  padding: 0;
}
.why__col {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--s-3);
  padding-top: var(--s-5);
  border-top: 1px solid var(--line);
}
.why__big {
  font-size: clamp(2rem, 1.2rem + 1.9vw, 2.75rem);
  line-height: 1;
  font-weight: 700;
  letter-spacing: -0.04em;
  font-variant-numeric: tabular-nums;
}
.why__small {
  margin-left: 2px;
  font-size: 0.5em;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--muted);
}
.why__small--lead {
  margin: 0 0.3em 0 0;
}
.why__body {
  max-width: 38ch;
  font-size: var(--fs-15);
  line-height: 1.55;
  color: var(--muted);
  text-wrap: pretty;
}
.why__src {
  margin-top: auto;
}
.why__sov {
  display: flex;
  align-items: baseline;
  gap: var(--s-3);
  max-width: 78ch;
  margin-top: var(--s-7);
  font-size: var(--fs-16);
  line-height: 1.55;
  font-weight: 500;
  text-wrap: pretty;
}
.why__mark {
  flex: none;
  width: 9px;
  height: 9px;
  background: var(--klar-red);
  transform: translateY(-1px);
}
.why__sov-text :deep(.src-link) {
  vertical-align: baseline;
}
.why__fine {
  margin-top: var(--s-3);
  padding-left: calc(9px + var(--s-3));
  font-size: var(--fs-12);
  color: var(--muted);
}

/* ---- Recent checks ---------------------------------------------------------- */
/* Same columns as the hero, so the list lines up with the field above it. */
.recent {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  column-gap: var(--gutter);
  padding-bottom: var(--s-8);
}
.recent > * {
  grid-column: 1 / span 6;
}
.recent__title {
  margin-bottom: var(--s-4);
  font-size: var(--fs-16);
  font-weight: 650;
  letter-spacing: -0.01em;
}
.recent__list {
  display: grid;
  gap: var(--s-2);
  margin: 0;
  padding: 0;
}
.recent__item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px var(--s-3);
  min-height: 56px;
  padding: 10px var(--s-4);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
  color: var(--ink);
  text-decoration: none;
}
.recent__item:hover {
  border-color: var(--control-border);
}
.recent__name {
  font-weight: 600;
  overflow-wrap: anywhere;
}
.recent__when {
  font-size: var(--fs-14);
  color: var(--muted);
}
.recent__status {
  margin-left: auto;
  font-size: var(--fs-14);
  font-weight: 600;
  color: var(--amber);
}
.recent__status.is-clear {
  color: var(--green);
}
.recent__arrow {
  color: var(--muted);
  transition: transform var(--dur-2) var(--ease-out), color var(--dur-2) var(--ease-out);
}
.recent__status + .recent__arrow {
  margin-left: var(--s-2);
}
.recent__when + .recent__arrow {
  margin-left: auto;
}
@media (hover: hover) {
  .recent__item:hover .recent__arrow {
    color: var(--ink);
    transform: translateX(3px);
  }
}

/* ---- Responsive -------------------------------------------------------------- */
@media (max-width: 1100px) {
  .hero__main,
  .recent > * {
    grid-column: 1 / span 7;
  }
  .story {
    grid-column: 8 / span 5;
  }
}
@media (max-width: 900px) {
  .hero__main,
  .story,
  .recent > * {
    grid-column: 1 / -1;
  }
  .story {
    max-width: 520px;
    margin-top: var(--s-7);
  }
  .why__cols {
    grid-template-columns: minmax(0, 1fr);
    gap: var(--s-6);
  }
}
@media (max-width: 480px) {
  .story__card {
    padding: var(--s-4);
  }
  .story__page {
    padding-right: 0;
    padding-top: var(--s-6);
  }
  .story__row {
    grid-template-columns: 1fr;
    gap: var(--s-2);
  }
  .demo-link__sub {
    display: none;
  }
  .recent__status {
    margin-left: 0;
  }
  .recent__item {
    position: relative;
    padding-right: 44px;
  }
  .recent__item .recent__arrow {
    position: absolute;
    top: 0;
    bottom: 0;
    right: var(--s-4);
    margin: auto 0;
  }
}
@media (forced-colors: active) {
  .story__bar {
    background: CanvasText;
  }
  .hero__dot {
    color: CanvasText;
  }
  .why__mark {
    background: CanvasText;
  }
}
</style>
