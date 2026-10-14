<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, ExternalLink } from '@lucide/vue'
import type { ProgressStep, Scan } from '@/types'
import { KNOWN_STEPS } from '@/types'
import { api, ApiError } from '@/api'
import { formatNumber, polish, t, tp, type MessageKey } from '@/i18n'
import { ensureBooted, health, lastScanId, refreshHealth, unreachable } from '@/stores/app'
import { applyDone, applyFinding, applyProgress, loadScan, scans } from '@/stores/scans'
import { prettyModel, scanTitle } from '@/lib/format'
import { classifyScanError, hostOf, renderProblem, type Problem, type ProblemAction } from '@/lib/errors'
import { evidenceLine, rowTitle } from '@/lib/finding-text'
import { groupFindings, type FindingGroup } from '@/lib/group'
import { useDocumentTitle } from '@/composables/useDocumentTitle'
import { useNow } from '@/composables/useNow'
import { useRerun } from '@/composables/useRerun'
import ProgressStepper from '@/components/ProgressStepper.vue'
import SovereigntyBadge from '@/components/SovereigntyBadge.vue'
import VerdictChip from '@/components/VerdictChip.vue'
import CriterionTag from '@/components/CriterionTag.vue'
import ErrorState from '@/components/ErrorState.vue'

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
let navTimer: number | undefined

/** H1 = the page title once the page is loaded, else the address (UX-11). */
const head = computed(() => (scan.value ? scanTitle(scan.value) : null))
const headTitle = computed(() => (head.value ? (head.value.title ?? t('report.pastedHtml')) : t('scan.connecting')))
/** The linked address under the H1, when the H1 is a page title rather than the address itself. */
const subUrl = computed(() => {
  const h = head.value
  if (!h?.url) return null
  const bare = h.url.replace(/^https?:\/\//, '')
  return h.title && !bare.startsWith(h.title) ? bare : null
})
useDocumentTitle(() => t('scan.docTitle', { url: scan.value ? headTitle.value : '…' }))

const finished = computed(() => scan.value?.state === 'done')
const failedState = computed(() => scan.value?.state === 'error')
const elapsed = computed(() => {
  if (!startedAt.value) return 0
  return ((finishedAt.value ?? now.value) - startedAt.value) / 1000
})
/** Newest first; identical findings (and notes with the same reason) collapse into one row with ×N. */
const live = computed(() => groupFindings(scan.value?.findings ?? []).reverse())
function liveTitle(g: FindingGroup) {
  const lang = scan.value?.ui_lang ?? 'en'
  const r = rowTitle(g.lead, lang)
  return { text: r.lang ? polish(r.text, r.lang) : r.text, lang: r.lang ?? undefined }
}

/** UX-6: a failed check says what happened in plain words; the raw text stays under Details. */
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
  // Announce state changes politely (not every tick of the Apertus counter).
  for (const p of Array.isArray(data) ? data : [data]) {
    if (p.step !== 'done' && before.get(p.step) !== p.state && p.state === 'running') {
      announcement.value = t('scan.announce.step', { step: stepLabel(p), state: t(`scan.state.${p.state}`) })
    }
  }
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
  navTimer = window.setTimeout(() => void router.replace({ name: 'report', params: { id: props.id } }), 1600)
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
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound.value = true
    else transportError.value = e instanceof Error ? e.message : String(e)
    return
  }
  unsubscribe.value = api().subscribe(props.id, {
    onProgress,
    onFinding: (f) => scan.value && applyFinding(scan.value, f),
    onDone: (d) => void finish(d),
    onError: async (m) => {
      // Maybe the check ended while the stream dropped: ask the server before showing an error.
      const fresh = await loadScan(props.id, true).catch(() => null)
      if (fresh && (fresh.state === 'done' || fresh.state === 'error')) void finish({ state: fresh.state })
      else transportError.value = m
    },
  })
})

onBeforeUnmount(() => {
  unsubscribe.value?.()
  if (navTimer) window.clearTimeout(navTimer)
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

    <template v-else>
      <header class="scan__head">
        <p class="eyebrow">{{ failedState ? t('scan.failedEyebrow') : finished ? t('scan.done') : t('scan.eyebrow') }}</p>
        <h1 class="h1 scan__url" tabindex="-1">{{ headTitle }}</h1>
        <p v-if="subUrl || head?.pasted" class="scan__sub">
          <a v-if="subUrl && head?.url" :href="head.url" target="_blank" rel="noopener noreferrer" class="mono">
            {{ subUrl }}<ExternalLink :size="13" aria-hidden="true" /><span class="sr-only"> {{ t('finding.newTab') }}</span>
          </a>
          <span v-else>{{ t('report.pastedHtml') }}</span>
        </p>
        <p class="scan__meta">
          <SovereigntyBadge variant="inline" :health="health" :mode="scan?.mode" :model="scan?.model" />
          <span aria-hidden="true">·</span>
          <span>{{ prettyModel(scan?.model ?? health?.model) }}</span>
          <span aria-hidden="true">·</span>
          <span class="tabular mono scan__elapsed">
            <span class="sr-only">{{ t('scan.elapsed') }}: </span>{{ formatNumber(elapsed, { minimumFractionDigits: 1, maximumFractionDigits: 1 }) }} s
          </span>
        </p>
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
        <section class="scan__progress" aria-labelledby="scan-progress">
          <h2 id="scan-progress" class="scan__h">{{ t('scan.progress') }}</h2>
          <ProgressStepper :steps="scan?.progress ?? []" :failed="failedState" :error-title="failureText?.title" />
          <div v-if="finished" class="scan__done">
            <RouterLink class="btn btn--primary" :to="{ name: 'report', params: { id } }">
              {{ t('scan.openReport') }} <ArrowRight :size="18" aria-hidden="true" />
            </RouterLink>
          </div>
        </section>

        <!-- Hidden when a failed check found nothing: an empty "arriving" box would suggest work still going on. -->
        <section v-if="!(failedState && !live.length)" class="scan__live" aria-labelledby="scan-live">
          <div class="scan__live-head">
            <h2 id="scan-live" class="scan__h">{{ t('scan.live') }}</h2>
            <p class="scan__count tabular">{{ tp('scan.count', scan?.findings.length ?? 0) }}</p>
          </div>
          <p v-if="!live.length" class="scan__waiting">
            <span class="scan__pulse" aria-hidden="true" />{{ t('scan.waiting') }}
          </p>
          <TransitionGroup v-else tag="ul" name="arrive" class="scan__list" role="list">
            <li v-for="g in live" :key="g.key" class="scan__item">
              <VerdictChip :outcome="g.lead.outcome" size="sm" />
              <span class="scan__item-main">
                <span class="scan__item-head">
                  <CriterionTag :code="g.lead.criterion" :name="g.lead.criterion_name" />
                  <span v-if="g.items.length > 1" class="scan__times tabular">×{{ g.items.length }}<span class="sr-only">, {{ tp('group.places', g.items.length) }}</span></span>
                </span>
                <span class="scan__item-impact" :lang="liveTitle(g).lang">{{ liveTitle(g).text }}</span>
                <span v-if="evidenceLine(g.lead)" class="scan__evidence mono muted" :lang="g.lead.content_lang ?? undefined" translate="no">{{ evidenceLine(g.lead) }}</span>
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
  padding-top: var(--s-8);
}
.scan__head {
  display: flex;
  flex-direction: column;
  gap: var(--s-3);
  padding-bottom: var(--s-6);
  border-bottom: 1px solid var(--line);
}
.scan__url {
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
.scan__evidence {
  display: block;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: var(--fs-12);
}
.scan__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 10px;
  font-size: var(--fs-14);
  color: var(--muted);
}
.scan__meta :deep(strong) {
  color: var(--ink);
}
.scan__elapsed {
  color: var(--ink);
}
.scan__note {
  margin-top: var(--s-5);
  padding: var(--s-3) var(--s-4);
  background: var(--amber-tint);
  border-radius: var(--r-control);
  font-size: var(--fs-14);
}
.scan__error {
  margin-top: var(--s-5);
}
.scan__grid {
  display: grid;
  grid-template-columns: minmax(0, 5fr) minmax(0, 7fr);
  gap: var(--s-8);
  padding-top: var(--s-6);
}
.scan__h {
  margin-bottom: var(--s-5);
  font-size: var(--fs-16);
  font-weight: 700;
  color: var(--ink);
}
.scan__item-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px;
}
.scan__times {
  padding: 0 7px;
  border-radius: var(--r-pill);
  background: var(--ink);
  color: var(--on-ink);
  font-size: var(--fs-12);
  font-weight: 700;
  line-height: 18px;
}
.scan__done {
  margin-top: var(--s-6);
  animation: klar-fade-up var(--dur-3) var(--ease);
}
.scan__live-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--s-3);
}
.scan__count {
  font-size: var(--fs-14);
  color: var(--muted);
}
.scan__waiting {
  display: flex;
  align-items: center;
  gap: var(--s-3);
  padding: var(--s-6) var(--s-5);
  border: 1px dashed var(--control-border);
  border-radius: var(--r-card);
  color: var(--muted);
}
.scan__pulse {
  width: 10px;
  height: 10px;
  background: var(--klar-red);
  animation: klar-pulse 1.2s ease-in-out infinite;
  flex: none;
}
.scan__list {
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--line);
}
.scan__item {
  display: grid;
  grid-template-columns: 9.5rem minmax(0, 1fr);
  gap: var(--s-4);
  align-items: start;
  padding: 12px 0;
  border-bottom: 1px solid var(--line);
}
.scan__item > .verdict {
  justify-self: start;
}
.scan__item-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.scan__item-impact {
  font-size: var(--fs-14);
  color: var(--ink);
}
.arrive-enter-active {
  transition: opacity var(--dur-3) var(--ease), transform var(--dur-3) var(--ease), background-color 1.2s var(--ease);
}
.arrive-enter-from {
  opacity: 0;
  transform: translateY(-6px);
  background-color: var(--surface-2);
}
.arrive-move {
  transition: transform var(--dur-2) var(--ease);
}
@media (max-width: 900px) {
  .scan__grid {
    grid-template-columns: 1fr;
    gap: var(--s-7);
  }
}
@media (max-width: 560px) {
  .scan__item {
    grid-template-columns: 1fr;
    gap: var(--s-2);
  }
}
</style>
