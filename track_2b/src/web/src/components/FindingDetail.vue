<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowDown, ArrowUp, Check, Copy, ExternalLink, X } from '@lucide/vue'
import type { Finding, Scan, Status } from '@/types'
import { API_BASE } from '@/config'
import { polish, t, type MessageKey } from '@/i18n'
import { actRuleUrl, understandingUrl } from '@/data/wcag'
import { pagePath, prettyModel } from '@/lib/format'
import { GENERIC_IMPACT, rowTitle } from '@/lib/finding-text'
import { isNote, toReview } from '@/lib/group'
import VerdictChip from './VerdictChip.vue'
import CriterionTag from './CriterionTag.vue'
import ConfidenceMeter from './ConfidenceMeter.vue'
import EvidenceBlock from './EvidenceBlock.vue'
import DiffBlock from './DiffBlock.vue'
import StatusBadge from './StatusBadge.vue'
import KeyboardHint from './KeyboardHint.vue'

const props = defineProps<{
  finding: Finding
  items?: Finding[]
  scan: Scan
  index: number
  total: number
  /** "3 of 35 to review" (UX-4); falls back to "{i} of {n}". */
  positionLabel?: string
  headingId: string
  busy?: boolean
}>()
const emit = defineEmits<{ close: []; prev: []; next: []; decide: [status: 'accepted' | 'rejected'] }>()

const lang = computed(() => props.scan.ui_lang)
const count = computed(() => props.items?.length ?? 1)
/** Aggregate decision of a grouped row (null when the places differ). */
const status = computed<Status | null>(() => {
  const all = props.items ?? [props.finding]
  return all.every((f) => f.status === all[0]!.status) ? all[0]!.status : null
})

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
/** The impact sentence under the title, when the title is a rule or a reason rather than the impact itself. */
const impact = computed(() =>
  !isNote(props.finding) && title.value.text !== props.finding.user_impact && !GENERIC_IMPACT.includes(props.finding.user_impact.trim()) ? props.finding.user_impact : null,
)

/**
 * "How to fix" (UX-5): the diff when there is one, else the CMS hint alone; with
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

/** UX-13: what Accept and Reject mean for this kind of finding. */
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
</script>

<template>
  <div class="fd">
    <div class="fd__bar">
      <span class="fd__pos tabular">{{ positionLabel ?? t('finding.position', { i: index + 1, n: total }) }}</span>
      <div class="fd__nav">
        <button type="button" class="btn btn--ghost btn--icon btn--sm" :disabled="index <= 0" :aria-label="t('finding.prev')" aria-keyshortcuts="k" @click="emit('prev')">
          <ArrowUp :size="16" aria-hidden="true" />
        </button>
        <button type="button" class="btn btn--ghost btn--icon btn--sm" :disabled="index >= total - 1" :aria-label="t('finding.next')" aria-keyshortcuts="j" @click="emit('next')">
          <ArrowDown :size="16" aria-hidden="true" />
        </button>
        <KeyboardHint :keys="['J', 'K']" />
        <button type="button" class="btn btn--ghost btn--icon btn--sm fd__close" :aria-label="t('finding.close')" aria-keyshortcuts="Escape" @click="emit('close')">
          <X :size="18" aria-hidden="true" />
        </button>
      </div>
    </div>

    <div class="fd__scroll">
      <header class="fd__head">
        <div class="fd__chips">
          <VerdictChip :outcome="finding.outcome" long />
          <CriterionTag :code="finding.criterion" :name="finding.criterion_name" tooltip show-level />
        </div>
        <h2 :id="headingId" class="fd__title" :lang="title.lang ?? undefined" tabindex="-1">{{ title.lang ? polish(title.text, title.lang) : title.text }}</h2>
        <p v-if="impact" class="fd__impact" :lang="lang">{{ polish(impact, lang) }}</p>
        <div class="fd__meta">
          <ConfidenceMeter :level="finding.confidence" />
          <span class="fd__source">{{ t(`source.${finding.source}.long`) }}</span>
        </div>
      </header>

      <section class="fd__section" aria-labelledby="fd-where">
        <h3 id="fd-where" class="fd__h">{{ t('finding.where') }}</h3>
        <dl class="fd__where">
          <div>
            <dt>{{ t('finding.page') }}</dt>
            <dd>
              <a :href="finding.page_url" target="_blank" rel="noopener noreferrer" class="fd__link">
                <span class="mono">{{ pagePath(finding.page_url, scan.url) }}</span>
                <ExternalLink :size="14" aria-hidden="true" />
                <span class="sr-only">{{ t('finding.newTab') }}</span>
              </a>
            </dd>
          </div>
        </dl>
        <div v-if="items && count > 1" class="fd__group">
          <p class="fd__group-title">{{ t('group.title', { n: count }) }}</p>
          <ol class="fd__group-list">
            <li v-for="f in items" :key="f.id">
              <span class="fd__place">
                <span class="mono">{{ pagePath(f.page_url, scan.url) }}</span>
                <code class="fd__place-sel" translate="no">{{ f.selector }}</code>
              </span>
              <StatusBadge :status="f.status" />
            </li>
          </ol>
          <p class="fd__group-note">{{ t('group.applies', { n: count }) }}</p>
        </div>
      </section>

      <section v-if="finding.excerpt || finding.screenshot" class="fd__section" aria-labelledby="fd-evidence">
        <h3 id="fd-evidence" class="fd__h">{{ t('finding.evidence') }}</h3>
        <EvidenceBlock :source="evidenceSource" :quote="finding.excerpt" :screenshot="screenshotUrl" :lang="finding.content_lang ?? undefined" />
      </section>

      <section class="fd__section" aria-labelledby="fd-why">
        <h3 id="fd-why" class="fd__h">{{ t('finding.why') }}</h3>
        <p class="fd__text" :lang="lang">{{ polish(finding.explanation, lang) }}</p>
        <RouterLink v-if="noteAction" class="fd__note-action" :to="{ name: 'about', hash: '#connect' }">{{ t(noteAction) }}</RouterLink>
      </section>

      <section class="fd__section" aria-labelledby="fd-fix">
        <h3 id="fd-fix" class="fd__h">{{ t('finding.fix') }}</h3>
        <DiffBlock v-if="fixState === 'diff'" :diff="finding.fix_diff!" :lang="finding.content_lang ?? undefined" />
        <p v-else-if="fixState === 'none'" class="fd__text muted">{{ t('finding.noAutoFix') }}</p>
        <p v-else-if="fixState === 'ok'" class="fd__text muted">{{ t('finding.noFix') }}</p>
        <div v-if="finding.fix_hint" class="fd__cms">
          <p class="fd__cms-label">{{ t('finding.cms') }}</p>
          <p :lang="lang">{{ polish(finding.fix_hint, lang) }}</p>
        </div>
      </section>

      <section class="fd__section">
        <details class="fd__ctx">
          <summary>
            <span class="fd__h fd__h--inline">{{ t('finding.context') }}</span>
            <span class="fd__count tabular" aria-hidden="true">{{ contextEntries.length }}</span>
          </summary>
          <p class="fd__ctx-hint">{{ contextEntries.length ? t('finding.contextHint') : t('finding.contextNone') }}</p>
          <dl v-if="contextEntries.length" class="fd__ctx-list">
            <div v-for="[k, v] in contextEntries" :key="k">
              <dt class="mono">{{ k }}</dt>
              <dd class="mono">{{ v }}</dd>
            </div>
          </dl>
        </details>
      </section>

      <section class="fd__section" aria-labelledby="fd-details">
        <h3 id="fd-details" class="fd__h">{{ t('finding.details') }}</h3>
        <dl class="fd__facts">
          <div>
            <dt>{{ t('finding.source') }}</dt>
            <dd>{{ t(`source.${finding.source}`) }}</dd>
          </div>
          <div v-if="finding.model">
            <dt>{{ t('finding.model') }}</dt>
            <dd>{{ prettyModel(finding.model) }} <span class="muted mono xsmall">{{ finding.model }}</span></dd>
          </div>
          <div v-if="finding.act_rule">
            <dt>{{ t('finding.act') }}</dt>
            <dd>
              <a :href="actRuleUrl(finding.act_rule)" target="_blank" rel="noopener noreferrer" class="mono"
                >{{ finding.act_rule }}<span class="sr-only"> {{ t('finding.newTab') }}</span></a
              >
            </dd>
          </div>
          <div>
            <dt>{{ t('finding.selector') }}</dt>
            <dd class="fd__selector">
              <code translate="no">{{ finding.selector }}</code>
              <button type="button" class="btn btn--ghost btn--icon btn--sm" :aria-label="copied ? t('finding.copied') : t('finding.copy')" @click="copySelector">
                <component :is="copied ? Check : Copy" :size="14" aria-hidden="true" />
              </button>
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
      </section>
    </div>

    <footer class="fd__decide">
      <p class="fd__hint">{{ decideHint }}</p>
      <div class="fd__status">
        <span class="fd__status-label">{{ t('finding.undecided') }}</span>
        <StatusBadge v-if="status" :status="status" />
        <span v-else class="fd__mixed">{{ t('group.reviewed', { done: (items ?? []).filter((f) => f.status !== 'to_review').length, n: count }) }}</span>
      </div>
      <div class="fd__actions">
        <button
          type="button"
          class="btn btn--secondary"
          :aria-pressed="status === 'rejected'"
          aria-keyshortcuts="r"
          :disabled="busy"
          @click="emit('decide', 'rejected')"
        >
          <X :size="16" aria-hidden="true" />{{ count > 1 ? t('group.rejectAll', { n: count }) : t('finding.reject') }}<KeyboardHint :keys="['R']" />
        </button>
        <button
          type="button"
          class="btn btn--primary"
          :aria-pressed="status === 'accepted'"
          aria-keyshortcuts="a"
          :disabled="busy"
          @click="emit('decide', 'accepted')"
        >
          <Check :size="16" aria-hidden="true" />{{ count > 1 ? t('group.acceptAll', { n: count }) : t('finding.accept') }}<KeyboardHint :keys="['A']" />
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
  padding: 8px 12px 8px var(--s-5);
  border-bottom: 1px solid var(--line);
}
.fd__pos {
  font-size: var(--fs-14);
  color: var(--muted);
}
.fd__nav {
  display: flex;
  align-items: center;
  gap: 4px;
}
.fd__nav .kh {
  margin: 0 6px 0 2px;
}
.fd__scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: var(--s-5);
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
  gap: var(--s-3);
}
.fd__title {
  font-size: var(--fs-24);
  line-height: 1.25;
  font-weight: 650;
  letter-spacing: -0.02em;
  text-wrap: pretty;
}
.fd__impact {
  font-size: var(--fs-16);
  color: var(--muted);
  line-height: 1.45;
}
.fd__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px 16px;
  font-size: var(--fs-14);
  color: var(--muted);
}
.fd__source {
  padding-left: 16px;
  border-left: 1px solid var(--line);
}
.fd__section {
  margin-top: var(--s-6);
}
.fd__h {
  margin-bottom: var(--s-3);
  font-size: var(--fs-14);
  font-weight: 700;
  color: var(--ink);
}
.fd__group {
  margin-top: var(--s-3);
  padding: var(--s-3) var(--s-4);
  background: var(--surface-2);
  border-radius: var(--r-control);
  font-size: var(--fs-14);
}
.fd__group-title {
  font-weight: 700;
}
.fd__group-list {
  margin: var(--s-2) 0;
  padding-left: 1.4em;
  display: grid;
  gap: 4px;
}
.fd__group-list li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--s-2);
}
.fd__group-list .mono {
  font-size: var(--fs-12);
}
.fd__place {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.fd__place-sel {
  font-size: var(--fs-12);
  color: var(--muted);
  overflow-wrap: anywhere;
}
.fd__group-note {
  color: var(--muted);
}
.fd__mixed {
  font-size: var(--fs-14);
  color: var(--muted);
}
.fd__h--inline {
  margin: 0;
}
.fd__note-action {
  display: inline-block;
  margin-top: var(--s-2);
  font-size: var(--fs-14);
  font-weight: 600;
}
.fd__text {
  font-size: var(--fs-16);
  line-height: 1.6;
  max-width: 62ch;
}
.fd__where,
.fd__facts {
  margin: 0;
  display: grid;
  gap: 0;
  font-size: var(--fs-14);
}
.fd__where > div,
.fd__facts > div {
  display: grid;
  grid-template-columns: 8.5rem minmax(0, 1fr);
  gap: var(--s-3);
  padding: 8px 0;
  border-top: 1px solid var(--line);
}
.fd__where dt,
.fd__facts dt {
  color: var(--muted);
}
.fd__where dd,
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
  padding-top: 7px;
  font-size: var(--fs-12);
  overflow-wrap: anywhere;
}
.fd__selector .btn {
  --btn-h: 30px;
  flex: none;
  color: var(--muted);
}
.fd__cms {
  margin-top: var(--s-4);
  padding: var(--s-4);
  background: var(--blue-tint);
  border-radius: var(--r-control);
  font-size: var(--fs-14);
  line-height: 1.55;
}
.fd__cms-label {
  margin-bottom: 4px;
  font-size: var(--fs-14);
  font-weight: 700;
  color: var(--blue);
}
.fd__ctx {
  border: 1px solid var(--line);
  border-radius: var(--r-control);
}
.fd__ctx summary {
  display: flex;
  align-items: center;
  gap: var(--s-3);
  min-height: 44px;
  padding: 0 var(--s-4);
  cursor: pointer;
  list-style: none;
}
.fd__ctx summary::-webkit-details-marker {
  display: none;
}
.fd__ctx summary::before {
  content: '';
  width: 7px;
  height: 7px;
  border-right: 2px solid var(--muted);
  border-bottom: 2px solid var(--muted);
  transform: rotate(-45deg);
  transition: transform var(--dur-1) var(--ease);
}
.fd__ctx[open] summary::before {
  transform: rotate(45deg);
}
.fd__count {
  margin-left: auto;
  font-size: var(--fs-12);
  color: var(--muted);
}
.fd__ctx-hint {
  padding: 0 var(--s-4) var(--s-3);
  font-size: var(--fs-14);
  color: var(--muted);
}
.fd__ctx-list {
  margin: 0;
  padding: 0 var(--s-4) var(--s-4);
  display: grid;
  gap: var(--s-2);
}
.fd__ctx-list > div {
  display: grid;
  gap: 2px;
  padding: var(--s-2) var(--s-3);
  background: var(--surface-2);
  border-radius: 6px;
}
.fd__ctx-list dt {
  font-size: var(--fs-12);
  color: var(--muted);
}
.fd__ctx-list dd {
  margin: 0;
  font-size: var(--fs-12);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.fd__decide {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--s-3);
  padding: var(--s-3) var(--s-5);
  border-top: 1px solid var(--line);
  background: var(--surface);
}
.fd__hint {
  flex: 1 0 100%;
  font-size: var(--fs-14);
  line-height: 1.4;
  color: var(--muted);
}
.fd__status {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.fd__status-label {
  font-size: var(--fs-12);
  color: var(--muted);
}
.fd__actions {
  display: flex;
  gap: var(--s-2);
}
.fd__actions .btn {
  gap: 8px;
}
.fd__actions .btn--primary :deep(kbd) {
  background: transparent;
  color: var(--on-ink);
  border-color: color-mix(in srgb, var(--on-ink) 45%, transparent);
}
.btn[aria-pressed='true'].btn--secondary {
  border-color: var(--ink);
  box-shadow: inset 0 0 0 1px var(--ink);
}
</style>
