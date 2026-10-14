<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowRight, Check, Quote, Server, Unlock, WifiOff, X } from '@lucide/vue'
import { DEMO_NAME, DEMO_URL, isDemoUrl } from '@/config'
import { api, ApiError } from '@/api'
import { formatNumber, formatRelative, locale, t, tp, type MessageKey } from '@/i18n'
import { ensureBooted, health, healthRetrying, lastScanId, prefill, refreshHealth, unreachable } from '@/stores/app'
import { scans } from '@/stores/scans'
import { toast } from '@/stores/toast'
import { classifyStartError, hostOf, type Problem, type ProblemAction } from '@/lib/errors'
import { isPasted, providerName, scanTitle } from '@/lib/format'
import { toReview } from '@/lib/group'
import { useShortcuts } from '@/composables/useShortcuts'
import { useDocumentTitle } from '@/composables/useDocumentTitle'
import UrlInput from '@/components/UrlInput.vue'
import ErrorState from '@/components/ErrorState.vue'
import type { CheckInput, ScanSummary } from '@/types'
import VerdictChip from '@/components/VerdictChip.vue'
import CriterionTag from '@/components/CriterionTag.vue'
import DiffBlock from '@/components/DiffBlock.vue'
import ShapeIcon from '@/components/ShapeIcon.vue'

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

const isReplay = computed(() => health.value?.mode === 'replay')
/** UX-8 / M3: replay mode without any recorded answer. */
const noRecordings = computed(() => {
  const r = health.value?.replay_recorded
  return isReplay.value && !!r && typeof r.records === 'number' && r.records === 0
})
/** UX-22 / M4: the model endpoint did not answer the start-up probe (null = unknown: say nothing). */
const llmDown = computed(() => !isReplay.value && health.value?.llm_reachable === false)

/** UX-17 / M5: at the moment of submitting, say where pages go when they leave the network. */
const sendNotice = computed(() => {
  const h = health.value
  if (h?.mode === 'external') return { shape: 'diamond' as const, color: 'var(--amber)', text: t('notice.external', { host: h.base_url_host ?? t('common.unknown') }) }
  if (h?.mode === 'swiss_cloud') return { shape: 'square' as const, color: 'var(--ink)', text: t('notice.swiss', { provider: providerName(h.provider, h.base_url_host) }) }
  return null
})

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

const specimenDiff = [
  '@@ -42 +42 @@',
  '-<p>Documents en français…</p>',
  '+<p lang="fr">Documents en français…</p>',
].join('\n')
</script>

<template>
  <div class="home">
    <section class="container hero">
      <div class="hero__text">
        <p class="eyebrow eyebrow--plain">{{ t('home.eyebrow') }}</p>
        <h1 class="display hero__title" tabindex="-1">{{ t('home.title') }}</h1>
        <p class="lede hero__lede">{{ t('home.lede') }}</p>

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
          <ErrorState v-else-if="llmDown" tone="info" :title="t('llm.down.title')" :body="t('llm.down.body', { host: health?.base_url_host ?? t('common.unknown') })" :details="health?.llm_error">
            <button type="button" class="btn btn--primary" :disabled="retrying" @click="retryHealth">{{ t('common.retry') }}</button>
            <RouterLink class="hero__link" :to="{ name: 'about', hash: '#connect' }">{{ t('notes.connect') }}</RouterLink>
          </ErrorState>
        </div>

        <!-- Replay mode: the demo site is the first, primary action -->
        <div v-if="isReplay && !replayGate && !unreachable" class="demo-cta">
          <div class="demo-cta__row">
            <button type="button" class="btn btn--primary demo-cta__btn" :disabled="busy" @click="tryDemo">
              {{ t('home.demo.primary') }} <ArrowRight :size="20" aria-hidden="true" />
            </button>
            <RouterLink v-if="demoReportId" class="btn btn--secondary demo-cta__open" :to="{ name: 'report', params: { id: demoReportId } }">
              {{ t('home.demo.openReport') }}
            </RouterLink>
          </div>
          <p class="demo-cta__sub">{{ t('home.demo.primarySub') }}</p>
          <ErrorState v-if="noRecordings" tone="info" :title="t('replay.empty.title')" :body="t('replay.empty.body')" :details="t('replay.empty.detail')">
            <RouterLink class="btn btn--secondary" :to="{ name: 'about', hash: '#connect' }">{{ t('notes.connect') }}</RouterLink>
          </ErrorState>
        </div>

        <UrlInput
          ref="field"
          class="hero__form"
          :class="{ 'hero__form--secondary': isReplay }"
          :busy="busy"
          :secondary="isReplay || unreachable || !!startProblem || !!replayGate"
          :label="isReplay ? t('home.form.labelReplay') : undefined"
          @submit="onSubmit"
        />
        <p v-if="sendNotice" class="send-notice">
          <ShapeIcon :shape="sendNotice.shape" :color="sendNotice.color" :size="9" />
          <span>{{ sendNotice.text }}</span>
          <RouterLink class="send-notice__link" :to="{ name: 'about', hash: '#connect' }">{{ t('notice.change') }}</RouterLink>
        </p>

        <!-- Live modes: the demo site is a secondary shortcut -->
        <button v-if="!isReplay" type="button" class="example" :disabled="busy" @click="tryDemo">
          <ShapeIcon shape="square" color="var(--klar-red)" :size="8" />
          <span class="example__name">{{ t('home.demo.secondary') }}</span>
          <span class="example__sub">{{ DEMO_NAME }}</span>
          <ArrowRight :size="16" aria-hidden="true" />
        </button>

        <section v-if="recent.length" id="recent" class="recent" aria-labelledby="recent-title">
          <h2 id="recent-title" class="recent__title">{{ t('recent.title') }}</h2>
          <ul class="recent__list" role="list">
            <li v-for="r in recent" :key="r.id">
              <RouterLink class="recent__item" :to="{ name: 'report', params: { id: r.id } }">
                <span class="recent__name">{{ r.title }}</span>
                <span class="recent__meta">
                  <span>{{ formatRelative(r.when) }}</span>
                  <template v-if="r.toReview !== null">
                    <span aria-hidden="true">·</span>
                    <span class="tabular">{{ tp('recent.toReview', r.toReview) }}</span>
                  </template>
                </span>
                <ArrowRight :size="16" aria-hidden="true" class="recent__arrow" />
              </RouterLink>
            </li>
          </ul>
        </section>
      </div>

      <!-- A static illustration, never shown as a result, and hidden while the server is unreachable. -->
      <figure v-if="!unreachable" class="specimen" aria-hidden="true">
        <div class="specimen__card">
          <figcaption class="specimen__tag">{{ t('home.specimen.tag') }}</figcaption>
          <div class="specimen__chips">
            <VerdictChip outcome="failed" />
            <CriterionTag code="3.1.2" />
          </div>
          <p class="specimen__impact">{{ t('home.specimen.impact') }}</p>
          <DiffBlock :diff="specimenDiff" bare />
          <div class="specimen__actions">
            <span class="specimen__label"><X :size="14" />{{ t('finding.reject') }}</span>
            <span class="specimen__label"><Check :size="14" />{{ t('finding.accept') }}</span>
          </div>
        </div>
      </figure>
    </section>

    <section class="container how" aria-labelledby="how-title">
      <h2 id="how-title" class="sr-only">{{ t('home.how') }}</h2>
      <ol class="how__grid" role="list">
        <li class="how__step">
          <span class="how__num mono" aria-hidden="true">01</span>
          <h3 class="how__title">{{ t('home.step1.title') }}</h3>
          <p class="how__body">{{ t('home.step1.body') }}</p>
          <div class="how__visual" aria-hidden="true">
            <code class="how__code"><span class="tk-p">&lt;</span><span class="tk-t">img</span> <span class="tk-a">alt</span>=<span class="tk-v">"Bild"</span><span class="tk-p">&gt;</span></code>
            <span class="how__ok"><Check :size="14" :stroke-width="3" />{{ t('home.step1.ok') }}</span>
          </div>
        </li>
        <li class="how__step how__step--accent">
          <span class="how__num mono" aria-hidden="true">02</span>
          <h3 class="how__title">{{ t('home.step2.title') }}</h3>
          <p class="how__body">{{ t('home.step2.body') }}</p>
          <div class="how__visual" aria-hidden="true">
            <span class="how__q">{{ t('home.step2.q') }}</span>
            <VerdictChip outcome="failed" size="sm" />
          </div>
        </li>
        <li class="how__step">
          <span class="how__num mono" aria-hidden="true">03</span>
          <h3 class="how__title">{{ t('home.step3.title') }}</h3>
          <p class="how__body">{{ t('home.step3.body') }}</p>
          <div class="how__visual" aria-hidden="true">
            <span class="specimen__label"><X :size="14" />{{ t('finding.reject') }}</span>
            <span class="specimen__label"><Check :size="14" />{{ t('finding.accept') }}</span>
          </div>
        </li>
      </ol>
    </section>

    <section class="container trust" :aria-label="t('home.trust.label')">
      <ul class="trust__list" role="list">
        <li><Server :size="18" aria-hidden="true" />{{ t('home.trust.sovereign') }}</li>
        <li><Unlock :size="18" aria-hidden="true" />{{ t('home.trust.open') }}</li>
        <li><WifiOff :size="18" aria-hidden="true" />{{ t('home.trust.requests') }}</li>
        <li><Quote :size="18" aria-hidden="true" />{{ t('home.trust.guard') }}</li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.hero {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  column-gap: var(--gutter);
  align-items: start;
  padding-top: clamp(32px, 6vw, 72px);
  padding-bottom: var(--s-8);
}
.hero__text {
  grid-column: 1 / span 8;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}
.hero__title {
  margin-top: var(--s-5);
}
.hero__lede {
  margin-top: var(--s-5);
  max-width: 58ch;
}
.hero__form {
  width: 100%;
  margin-top: var(--s-7);
}
.hero__form--secondary {
  margin-top: var(--s-6);
}
.hero__notice {
  width: 100%;
}
.hero__notice:not(:empty) {
  margin-top: var(--s-6);
}
.demo-cta {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--s-2);
  margin-top: var(--s-7);
}
.demo-cta__row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-3);
}
.demo-cta__open {
  --btn-h: 56px;
}
.demo-cta > .es {
  margin-top: var(--s-3);
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
.send-notice {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 8px;
  margin-top: var(--s-3);
  font-size: var(--fs-14);
  color: var(--muted);
}
.send-notice__link {
  font-weight: 600;
}
.recent {
  width: 100%;
  max-width: 760px;
  margin-top: var(--s-7);
}
.recent__title {
  margin-bottom: var(--s-3);
  font-size: var(--fs-14);
  font-weight: 700;
}
.recent__list {
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--line);
}
.recent__item {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px var(--s-3);
  min-height: 48px;
  padding: 12px 4px;
  border-bottom: 1px solid var(--line);
  color: var(--ink);
  text-decoration: none;
}
.recent__item:hover {
  background: var(--surface-2);
}
.recent__name {
  font-weight: 600;
  overflow-wrap: anywhere;
}
.recent__meta {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 6px;
  font-size: var(--fs-14);
  color: var(--muted);
}
.recent__arrow {
  margin-left: auto;
  align-self: center;
  color: var(--muted);
}
.demo-cta__btn {
  --btn-h: 56px;
  padding: 0 24px 0 28px;
  font-size: var(--fs-20);
  gap: 12px;
}
.demo-cta__sub {
  font-size: var(--fs-14);
  color: var(--muted);
}
.example {
  margin-top: var(--s-5);
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 40px;
  padding: 0 14px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-pill);
  font-size: var(--fs-14);
  color: var(--ink);
  transition: border-color var(--dur-1) var(--ease), transform var(--dur-1) var(--ease);
}
.example:hover:not(:disabled) {
  border-color: var(--ink);
}
.example:active:not(:disabled) {
  transform: translateY(1px);
}
.example__name {
  font-weight: 600;
}
.example__sub {
  color: var(--muted);
}
.specimen {
  grid-column: 9 / span 4;
  align-self: start;
  margin: 56px 0 0;
}
.specimen__tag {
  align-self: flex-start;
  padding: 2px 10px;
  border: 1px dashed var(--control-border);
  border-radius: var(--r-pill);
  font-size: var(--fs-12);
  font-weight: 600;
  color: var(--muted);
}
/* Inert look: these are labels in a picture, not buttons. */
.specimen__label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 30px;
  padding: 0 10px;
  border: 1px dashed var(--control-border);
  border-radius: var(--r-control);
  color: var(--muted);
  font-size: var(--fs-14);
  font-weight: 500;
  cursor: default;
  user-select: none;
}
.specimen__card {
  display: flex;
  flex-direction: column;
  gap: var(--s-4);
  padding: var(--s-5);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
  box-shadow: 0 1px 0 var(--line), 0 24px 48px -24px color-mix(in srgb, var(--ink) 18%, transparent);
}
.specimen__chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-3);
}
.specimen__impact {
  font-size: var(--fs-20);
  font-weight: 600;
  line-height: 1.3;
  letter-spacing: -0.015em;
}
.specimen__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--s-2);
}
.how__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--gutter);
  margin: 0;
  padding: 0;
}
.how__step {
  display: flex;
  flex-direction: column;
  gap: var(--s-3);
  padding-top: var(--s-5);
  border-top: 2px solid var(--ink);
}
.how__step--accent {
  border-top-color: var(--klar-red);
}
.how__num {
  font-size: var(--fs-14);
  color: var(--muted);
}
.how__title {
  font-size: var(--fs-24);
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
}
.how__body {
  color: var(--muted);
  max-width: 40ch;
}
.how__visual {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-3);
  margin-top: auto;
  padding: var(--s-4);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
  min-height: 72px;
}
.how__code {
  font-size: var(--fs-14);
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
.how__ok {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-14);
  font-weight: 600;
  color: var(--green);
}
.how__q {
  font-size: var(--fs-14);
  font-weight: 600;
}
.trust {
  margin-top: var(--s-8);
}
.trust__list {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 0;
  padding: var(--s-5) 0 0;
  border-top: 1px solid var(--line);
  gap: var(--gutter);
}
.trust__list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: var(--fs-14);
  font-weight: 500;
}
.trust__list svg {
  flex: none;
  margin-top: 1px;
  color: var(--muted);
}
@media (max-width: 1100px) {
  .hero__text {
    grid-column: 1 / -1;
  }
  .specimen {
    grid-column: 1 / -1;
    max-width: 520px;
    margin-top: var(--s-7);
  }
}
@media (max-width: 860px) {
  .how__grid,
  .trust__list {
    grid-template-columns: 1fr 1fr;
  }
}
@media (max-width: 560px) {
  .how__grid,
  .trust__list {
    grid-template-columns: 1fr;
  }
  .example__sub {
    display: none;
  }
}
</style>
