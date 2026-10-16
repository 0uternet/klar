<script lang="ts">
import { ref } from 'vue'
/** The two technical disclosures stay as the reviewer left them while moving between findings. */
const contextOpen = ref(false)
const techOpen = ref(false)
</script>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { ArrowDown, ArrowUp, Check, Copy, ExternalLink, X } from '@lucide/vue'
import type { Finding, Scan, Status } from '@/types'
import { API_BASE } from '@/config'
import { polish, t, type MessageKey } from '@/i18n'
import { actRuleUrl, understandingUrl } from '@/data/wcag'
import { pageCount, pagePath, prettyModel } from '@/lib/format'
import { GENERIC_IMPACT, evidenceLine, rowTitle } from '@/lib/finding-text'
import { isNote, toReview } from '@/lib/group'
import VerdictChip from './VerdictChip.vue'
import CriterionTag from './CriterionTag.vue'
import ConfidenceMeter from './ConfidenceMeter.vue'
import EvidenceBlock from './EvidenceBlock.vue'
import DiffBlock from './DiffBlock.vue'
import StatusBadge from './StatusBadge.vue'
import KeyboardHint from './KeyboardHint.vue'
import Disclosure from './report/Disclosure.vue'

/**
 * The finding panel, in reading order: what happened (with the quoted evidence), why it
 * matters for a person, how to fix it. What the model saw and the technical ids are one
 * click away. Accept and reject stay pinned at the bottom.
 */
const props = defineProps<{
  finding: Finding
  items?: Finding[]
  scan: Scan
  index: number
  total: number
  headingId: string
}>()
const emit = defineEmits<{
  close: []
  prev: []
  next: []
  decide: [status: 'accepted' | 'rejected']
  decideOne: [finding: Finding, status: 'accepted' | 'rejected']
}>()

const ctxOpen = contextOpen
const detailsOpen = techOpen
const lang = computed(() => props.scan.ui_lang)
const count = computed(() => props.items?.length ?? 1)
const multiPage = computed(() => pageCount(props.scan.findings) > 1)
/** Aggregate decision of a grouped row (null when the places differ). */
const status = computed<Status | null>(() => {
  const all = props.items ?? [props.finding]
  return all.every((f) => f.status === all[0]!.status) ? all[0]!.status : null
})
const decided = computed(() => (props.items ?? [props.finding]).filter((f) => f.status !== 'to_review').length)

/** The DOM excerpt: the element's HTML if the model saw it, else the context value containing the quote. */
const evidenceSource = computed(() => {
  const ctx = props.finding.context_shown ?? {}
  const preferred = ctx.element ?? ctx.html ?? ctx.outer_html ?? ctx.outerHTML
  if (preferred) return preferred
  const q = props.finding.excerpt
  const hit = Object.values(ctx)
    .filter((v) => typeof v === 'string' && q && v.includes(q))
    .sort((a, b) => b.length - a.length)[0]
  return hit ?? q
})

const title = computed(() => rowTitle(props.finding, lang.value))

/**
 * "What happened": the explanation, minus what the title already says. An axe-core
 * explanation is "rule id: the title", so it adds nothing here (the rule id is in the
 * technical details); a title taken from the explanation's first sentence is not repeated.
 */
const explanation = computed(() => {
  const x = props.finding.explanation.replace(/\s+/g, ' ').trim()
  if (!x) return null
  const head = title.value.text.replace(/\s+/g, ' ').trim().replace(/[.;:]$/, '')
  if (!head) return x
  const lx = x.toLowerCase()
  const lh = head.toLowerCase()
  if (lx.replace(/[.;:]$/, '').endsWith(lh) && (props.finding.reason_code === 'axe' || lx.length - lh.length < 60)) return null
  if (lx.startsWith(lh)) {
    const rest = x.slice(head.length).replace(/^[\s.;:!?]+/, '').trim()
    return rest || null
  }
  return x
})

/** "Why it matters": the impact sentence, when the title is a rule or a reason rather than the impact itself. */
const impact = computed(() =>
  !isNote(props.finding) && title.value.text !== props.finding.user_impact && !GENERIC_IMPACT.includes(props.finding.user_impact.trim())
    ? props.finding.user_impact
    : null,
)

/**
 * "How to fix": the diff when there is one, else the CMS hint alone; with
 * neither, a failed or uncertain finding says so plainly. "No change needed" is
 * only ever said of a passed or not-applicable finding.
 */
const fixState = computed<'diff' | 'hint' | 'none' | 'ok'>(() => {
  if (props.finding.fix_diff) return 'diff'
  if (props.finding.fix_hint) return 'hint'
  return toReview(props.finding) ? 'none' : 'ok'
})

/** A note whose cause is the model connection gets a way to fix it (attached to reason_code, never to the text). */
const NOTE_ACTION: Partial<Record<string, MessageKey>> = {
  not_recorded: 'replay.connectShort',
  request_failed: 'notes.checkConnection',
  vision_required: 'notes.connect',
}
const noteAction = computed(() => (isNote(props.finding) ? (NOTE_ACTION[props.finding.reason_code] ?? null) : null))

/** What Accept and Reject mean for this kind of finding. */
const decideHint = computed(() => (props.finding.outcome === 'cantTell' ? t('decide.hint.review') : t('decide.hint.failed')))

const contextEntries = computed(() => Object.entries(props.finding.context_shown ?? {}))

const screenshotUrl = computed(() => {
  const s = props.finding.screenshot
  if (!s) return null
  if (/^(data:|https?:|blob:|\/)/.test(s)) return s
  return `${API_BASE}/scans/${encodeURIComponent(props.scan.id)}/files/${s.split('/').map(encodeURIComponent).join('/')}`
})

const copied = ref(false)
async function copySelector() {
  try {
    await navigator.clipboard.writeText(props.finding.selector)
    copied.value = true
    window.setTimeout(() => (copied.value = false), 1600)
  } catch {
    /* clipboard unavailable */
  }
}

const scroller = ref<HTMLElement | null>(null)
watch(
  () => props.finding.id,
  () => {
    copied.value = false
    scroller.value?.scrollTo({ top: 0 })
  },
)
</script>

<template>
  <div class="fd">
    <div class="fd__bar">
      <span class="fd__pos tabular">{{ index >= 0 ? t('finding.position', { i: index + 1, n: total }) : '' }}</span>
      <div class="fd__nav">
        <button type="button" class="fd__icon" :disabled="index <= 0" :aria-label="t('finding.prev')" aria-keyshortcuts="k" @click="emit('prev')">
          <ArrowUp :size="16" aria-hidden="true" />
        </button>
        <button type="button" class="fd__icon" :disabled="index >= total - 1" :aria-label="t('finding.next')" aria-keyshortcuts="j" @click="emit('next')">
          <ArrowDown :size="16" aria-hidden="true" />
        </button>
        <KeyboardHint :keys="['J', 'K']" />
        <span class="fd__sep" aria-hidden="true" />
        <button type="button" class="fd__icon" :aria-label="t('finding.close')" aria-keyshortcuts="Escape" @click="emit('close')">
          <X :size="18" aria-hidden="true" />
        </button>
      </div>
    </div>

    <div ref="scroller" class="fd__scroll">
      <div :key="finding.id" class="fd__body">
        <header class="fd__head">
          <div class="fd__chips">
            <VerdictChip :outcome="finding.outcome" long />
            <CriterionTag :code="finding.criterion" :name="finding.criterion_name" tooltip show-level />
          </div>
          <h2 :id="headingId" class="fd__title" :lang="title.lang ?? undefined" tabindex="-1">{{ title.lang ? polish(title.text, title.lang) : title.text }}</h2>
        </header>

        <section class="fd__sec" aria-labelledby="fd-what">
          <h3 id="fd-what" class="fd__h">{{ t('finding.what') }}</h3>
          <p v-if="explanation" class="fd__text" :lang="lang">{{ polish(explanation, lang) }}</p>
          <RouterLink v-if="noteAction" class="fd__note-action" :to="{ name: 'about', hash: '#connect' }">{{ t(noteAction) }}</RouterLink>
          <EvidenceBlock
            v-if="finding.excerpt || finding.screenshot"
            class="fd__evidence"
            :source="evidenceSource"
            :quote="finding.excerpt"
            :screenshot="screenshotUrl"
            :lang="finding.content_lang ?? undefined"
          />

          <div v-if="items && count > 1" class="fd__places">
            <p class="fd__places-title">{{ t('group.title', { n: count }) }}</p>
            <ol class="fd__place-list" role="list">
              <li v-for="(f, i) in items" :key="f.id" class="fd__place" :data-place="f.id">
                <span class="fd__place-n tabular" aria-hidden="true">{{ i + 1 }}</span>
                <span class="fd__place-where">
                  <span v-if="evidenceLine(f)" class="mono fd__place-quote" :lang="f.content_lang ?? undefined" translate="no">{{ evidenceLine(f, 90) }}</span>
                  <span v-if="multiPage" class="mono fd__place-path">{{ pagePath(f.page_url, scan.url) }}</span>
                  <code class="fd__place-sel" translate="no">{{ f.selector }}</code>
                </span>
                <StatusBadge v-if="f.status !== 'to_review'" :status="f.status" compact />
                <span class="fd__place-acts">
                  <button
                    type="button"
                    class="fd__mini fd__mini--reject"
                    :aria-pressed="f.status === 'rejected'"
                    :aria-label="t('group.rejectOne', { i: i + 1 })"
                    @click="emit('decideOne', f, 'rejected')"
                  >
                    <X :size="14" aria-hidden="true" />
                  </button>
                  <button
                    type="button"
                    class="fd__mini fd__mini--accept"
                    :aria-pressed="f.status === 'accepted'"
                    :aria-label="t('group.acceptOne', { i: i + 1 })"
                    @click="emit('decideOne', f, 'accepted')"
                  >
                    <Check :size="14" aria-hidden="true" />
                  </button>
                </span>
              </li>
            </ol>
            <p class="fd__places-note">{{ t('group.applies', { n: count }) }}</p>
          </div>
        </section>

        <section v-if="impact" class="fd__sec" aria-labelledby="fd-why">
          <h3 id="fd-why" class="fd__h">{{ t('finding.why') }}</h3>
          <p class="fd__text" :lang="lang">{{ polish(impact, lang) }}</p>
        </section>

        <section class="fd__sec" aria-labelledby="fd-fix">
          <h3 id="fd-fix" class="fd__h">{{ t('finding.fix') }}</h3>
          <DiffBlock v-if="fixState === 'diff'" :diff="finding.fix_diff!" :lang="finding.content_lang ?? undefined" />
          <p v-else-if="fixState === 'none'" class="fd__text muted">{{ t('finding.noAutoFix') }}</p>
          <p v-else-if="fixState === 'ok'" class="fd__text muted">{{ t('finding.noFix') }}</p>
          <div v-if="finding.fix_hint" class="fd__cms">
            <p class="fd__cms-label">{{ t('finding.cms') }}</p>
            <p :lang="lang">{{ polish(finding.fix_hint, lang) }}</p>
          </div>
        </section>

        <div class="fd__more">
          <Disclosure v-model:open="ctxOpen">
            <template #summary>
              {{ t('finding.context') }}<span class="fd__badge tabular" aria-hidden="true">{{ contextEntries.length }}</span>
            </template>
            <p class="fd__ctx-hint">{{ contextEntries.length ? t('finding.contextHint') : t('finding.contextNone') }}</p>
            <dl v-if="contextEntries.length" class="fd__ctx">
              <div v-for="[k, v] in contextEntries" :key="k">
                <dt class="mono">{{ k }}</dt>
                <dd class="mono" translate="no">{{ v }}</dd>
              </div>
            </dl>
          </Disclosure>

          <Disclosure v-model:open="detailsOpen">
            <template #summary>{{ t('finding.details') }}</template>
            <dl class="fd__facts">
              <div>
                <dt>{{ t('finding.confidence') }}</dt>
                <dd><ConfidenceMeter :level="finding.confidence" /></dd>
              </div>
              <div>
                <dt>{{ t('finding.source') }}</dt>
                <dd>{{ t(`source.${finding.source}.long`) }}</dd>
              </div>
              <div v-if="finding.model">
                <dt>{{ t('finding.model') }}</dt>
                <dd>{{ prettyModel(finding.model) }} <span class="muted mono xsmall">{{ finding.model }}</span></dd>
              </div>
              <div>
                <dt>{{ t('finding.page') }}</dt>
                <dd>
                  <a :href="finding.page_url" target="_blank" rel="noopener noreferrer" class="fd__link">
                    <span class="mono">{{ pagePath(finding.page_url, scan.url) }}</span>
                    <ExternalLink :size="13" aria-hidden="true" />
                    <span class="sr-only">{{ t('finding.newTab') }}</span>
                  </a>
                </dd>
              </div>
              <div>
                <dt>{{ t('finding.selector') }}</dt>
                <dd class="fd__selector">
                  <code translate="no">{{ finding.selector }}</code>
                  <button type="button" class="fd__icon fd__icon--sm" :aria-label="copied ? t('finding.copied') : t('finding.copy')" @click="copySelector">
                    <component :is="copied ? Check : Copy" :size="14" aria-hidden="true" />
                  </button>
                  <span class="sr-only" role="status">{{ copied ? t('finding.copied') : '' }}</span>
                </dd>
              </div>
              <div v-if="finding.act_rule">
                <dt>{{ t('finding.act') }}</dt>
                <dd>
                  <a :href="actRuleUrl(finding.act_rule)" target="_blank" rel="noopener noreferrer" class="mono"
                    >{{ finding.act_rule }}<span class="sr-only"> {{ t('finding.newTab') }}</span></a
                  >
                </dd>
              </div>
              <div v-if="finding.axe_rule">
                <dt>{{ t('finding.axe') }}</dt>
                <dd class="mono" translate="no">{{ finding.axe_rule }}</dd>
              </div>
              <div v-if="finding.reason_code">
                <dt>{{ t('finding.reasonCode') }}</dt>
                <dd class="mono" translate="no">{{ finding.reason_code }}</dd>
              </div>
              <div v-if="finding.reason">
                <dt>{{ t('finding.reason') }}</dt>
                <dd lang="en">{{ finding.reason }}</dd>
              </div>
              <div>
                <dt>{{ t('finding.en301549') }}</dt>
                <dd class="mono">{{ finding.en301549 ?? `9.${finding.criterion}` }}</dd>
              </div>
              <div>
                <dt>WCAG</dt>
                <dd>
                  <a :href="understandingUrl(finding.criterion)" target="_blank" rel="noopener noreferrer"
                    >{{ t('finding.understanding', { code: finding.criterion }) }}<span class="sr-only"> {{ t('finding.newTab') }}</span></a
                  >
                </dd>
              </div>
            </dl>
          </Disclosure>
        </div>
      </div>
    </div>

    <footer class="fd__decide">
      <p class="fd__hint">
        {{ decideHint }}
        <span v-if="count > 1 && !status" class="fd__mixed tabular"> · {{ t('group.reviewed', { done: decided, n: count }) }}</span>
      </p>
      <div class="fd__actions" role="group" :aria-label="t('finding.undecided')">
        <button type="button" class="fd__btn fd__btn--reject press" :aria-pressed="status === 'rejected'" aria-keyshortcuts="r" @click="emit('decide', 'rejected')">
          <svg :key="`r-${finding.id}-${status === 'rejected'}`" class="fd__glyph" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false">
            <path :class="{ 'm-draw': status === 'rejected' }" pathLength="1" d="M4.2 4.2l7.6 7.6M11.8 4.2l-7.6 7.6" />
          </svg>
          <span>{{ count > 1 ? t('group.rejectAll', { n: count }) : t('finding.reject') }}</span>
          <KeyboardHint :keys="['R']" />
        </button>
        <button type="button" class="fd__btn fd__btn--accept press" :aria-pressed="status === 'accepted'" aria-keyshortcuts="a" @click="emit('decide', 'accepted')">
          <svg :key="`a-${finding.id}-${status === 'accepted'}`" class="fd__glyph" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false">
            <path :class="{ 'm-draw': status === 'accepted' }" pathLength="1" d="M3.2 8.4l3.1 3.1 6.5-6.9" />
          </svg>
          <span>{{ count > 1 ? t('group.acceptAll', { n: count }) : t('finding.accept') }}</span>
          <KeyboardHint :keys="['A']" />
        </button>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.fd {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}
.fd__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s-3);
  min-height: 52px;
  padding: 0 12px 0 var(--s-5);
  border-bottom: 1px solid var(--line);
}
.fd__pos {
  font-size: var(--fs-14);
  font-weight: 550;
  color: var(--muted);
}
.fd__nav {
  display: flex;
  align-items: center;
  gap: 2px;
}
.fd__nav .kh {
  margin: 0 6px 0 4px;
}
.fd__sep {
  width: 1px;
  height: 20px;
  margin: 0 6px;
  background: var(--line);
}
.fd__icon {
  display: inline-grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border: 0;
  border-radius: var(--r-control);
  background: transparent;
  color: var(--ink);
  transition: background-color var(--dur-1) var(--ease-out);
}
.fd__icon:hover:not(:disabled) {
  background: var(--surface-2);
}
.fd__icon:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.fd__icon--sm {
  width: 30px;
  height: 30px;
  flex: none;
  color: var(--muted);
}
.fd__scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
}
.fd__body {
  padding: var(--s-5) var(--s-5) var(--s-6);
  animation: fd-in var(--dur-3) var(--ease-out);
}
@keyframes fd-in {
  from {
    opacity: 0;
  }
}
.fd__head {
  display: flex;
  flex-direction: column;
  gap: var(--s-3);
}
.fd__chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-2) var(--s-3);
}
.fd__title {
  font-size: 1.375rem;
  line-height: 1.3;
  font-weight: 680;
  letter-spacing: -0.022em;
  text-wrap: pretty;
}
.fd__sec {
  margin-top: var(--s-6);
}
.fd__h {
  margin-bottom: var(--s-2);
  font-size: var(--fs-12);
  font-weight: 650;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--muted);
}
.fd__text {
  font-size: var(--fs-16);
  line-height: 1.6;
  max-width: 62ch;
  text-wrap: pretty;
}
.fd__text + .fd__evidence,
.fd__note-action + .fd__evidence {
  margin-top: var(--s-4);
}
.fd__note-action {
  display: inline-block;
  margin-top: var(--s-2);
  font-size: var(--fs-14);
  font-weight: 600;
}
/* Identical places, decided all at once or one by one. */
.fd__places {
  margin-top: var(--s-5);
}
.fd__places-title {
  margin-bottom: var(--s-2);
  font-size: var(--fs-14);
  font-weight: 650;
}
.fd__place-list {
  margin: 0;
  border-top: 1px solid var(--line);
}
.fd__place {
  display: grid;
  grid-template-columns: 1.25rem minmax(0, 1fr) auto auto;
  align-items: center;
  gap: var(--s-3);
  padding: 8px 0;
  border-bottom: 1px solid var(--line);
  font-size: var(--fs-14);
}
.fd__place-n {
  font-size: var(--fs-12);
  color: var(--muted);
}
.fd__place-where {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.fd__place-quote,
.fd__place-path {
  font-size: var(--fs-12);
  overflow-wrap: anywhere;
}
.fd__place-sel {
  font-size: 0.6875rem;
  color: var(--muted);
  overflow-wrap: anywhere;
}
.fd__place-acts {
  display: flex;
  gap: 4px;
}
.fd__mini {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--control-border);
  border-radius: 7px;
  background: var(--surface);
  color: var(--ink);
  transition: background-color var(--dur-1) var(--ease-out), border-color var(--dur-1) var(--ease-out), color var(--dur-1) var(--ease-out);
}
.fd__mini:hover {
  background: var(--surface-2);
}
.fd__mini--accept[aria-pressed='true'] {
  background: var(--green-tint);
  border-color: var(--green);
  color: var(--green);
}
.fd__mini--reject[aria-pressed='true'] {
  background: var(--surface-3);
  border-color: var(--ink);
}
.fd__places-note {
  margin-top: var(--s-2);
  font-size: var(--fs-12);
  color: var(--muted);
}
.fd__cms {
  margin-top: var(--s-4);
  padding: var(--s-3) var(--s-4);
  background: var(--blue-tint);
  border-radius: var(--r-control);
  font-size: var(--fs-14);
  line-height: 1.55;
}
.fd__cms-label {
  margin-bottom: 2px;
  font-size: var(--fs-12);
  font-weight: 700;
  color: var(--blue);
}
.fd__more {
  margin-top: var(--s-7);
  border-bottom: 1px solid var(--line);
}
.fd__badge {
  display: inline-grid;
  place-items: center;
  min-width: 20px;
  height: 18px;
  margin-left: 8px;
  padding: 0 5px;
  border-radius: var(--r-pill);
  background: var(--surface-3);
  font-size: 0.6875rem;
  font-weight: 650;
  color: var(--muted);
}
.fd__ctx-hint {
  margin-bottom: var(--s-3);
  font-size: var(--fs-14);
  color: var(--muted);
}
.fd__ctx {
  margin: 0;
  display: grid;
  gap: var(--s-2);
}
.fd__ctx > div {
  display: grid;
  gap: 2px;
  padding: var(--s-2) var(--s-3);
  background: var(--surface-2);
  border-radius: 6px;
}
.fd__ctx dt {
  font-size: var(--fs-12);
  color: var(--muted);
}
.fd__ctx dd {
  margin: 0;
  font-size: var(--fs-12);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.fd__facts {
  margin: 0;
  display: grid;
  font-size: var(--fs-14);
}
.fd__facts > div {
  display: grid;
  grid-template-columns: 8.5rem minmax(0, 1fr);
  gap: var(--s-3);
  padding: 7px 0;
}
.fd__facts > div + div {
  border-top: 1px solid var(--line);
}
.fd__facts dt {
  color: var(--muted);
}
.fd__facts dd {
  margin: 0;
  min-width: 0;
  overflow-wrap: anywhere;
}
.fd__link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.fd__selector {
  display: flex;
  align-items: flex-start;
  gap: 4px;
}
.fd__selector code {
  padding-top: 5px;
  font-size: var(--fs-12);
  overflow-wrap: anywhere;
}

/* Decision bar */
.fd__decide {
  display: flex;
  flex-direction: column;
  gap: var(--s-3);
  padding: var(--s-3) var(--s-5) var(--s-4);
  border-top: 1px solid var(--line);
  background: var(--surface);
}
.fd__hint {
  font-size: var(--fs-14);
  line-height: 1.4;
  color: var(--muted);
}
.fd__actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--s-2);
}
.fd__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 44px;
  padding: 0 var(--s-4);
  border: 1px solid var(--control-border);
  border-radius: var(--r-control);
  background: var(--surface);
  color: var(--ink);
  font-size: var(--fs-16);
  font-weight: 600;
  transition: background-color var(--dur-2) var(--ease-out), border-color var(--dur-2) var(--ease-out), color var(--dur-2) var(--ease-out),
    transform var(--dur-1) var(--ease-out);
}
.fd__btn:hover {
  background: var(--surface-2);
}
.fd__btn--accept {
  background: var(--ink);
  border-color: var(--ink);
  color: var(--on-ink);
}
.fd__btn--accept:hover {
  background: var(--ink-hover);
}
.fd__btn--accept[aria-pressed='true'] {
  background: var(--green);
  border-color: var(--green);
  color: var(--on-ink);
}
.fd__btn--reject[aria-pressed='true'] {
  background: var(--surface-3);
  border-color: var(--ink);
  box-shadow: inset 0 0 0 1px var(--ink);
}
.fd__glyph {
  flex: none;
  fill: none;
  stroke: currentColor;
  stroke-width: 2.4;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.fd__btn :deep(kbd) {
  background: transparent;
  color: inherit;
  border-color: color-mix(in srgb, currentColor 40%, transparent);
}
@media (forced-colors: active) {
  .fd__btn[aria-pressed='true'],
  .fd__mini[aria-pressed='true'] {
    outline: 2px solid Highlight;
    outline-offset: 1px;
  }
}
</style>
