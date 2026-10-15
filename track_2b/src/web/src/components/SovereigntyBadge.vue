<script setup lang="ts">
import { computed, onBeforeUnmount, ref, useId, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowRight } from '@lucide/vue'
import type { Destination, Health, Mode } from '@/types'
import { formatNumber, t, type MessageKey } from '@/i18n'
import { aiCounterText, leftNetwork } from '@/lib/sovereignty'
import { MODE_COLOR, MODE_SHAPE, isApertus, prettyModel, providerName } from '@/lib/format'
import ShapeIcon from './ShapeIcon.vue'

/**
 * Sovereignty badge: computed from GET /api/health, never hard-coded.
 * Answers one question: where do your pages go?
 *  - header: one compact pill (status dot + mode); everything else lives in its panel
 *  - inline: one line (report header, scan view)
 *  - card:   full details (About page)
 */
const props = withDefaults(
  defineProps<{ health: Health | null; variant?: 'header' | 'inline' | 'card'; mode?: Mode; model?: string; unreachable?: boolean }>(),
  { variant: 'header', unreachable: false },
)

const mode = computed<Mode | null>(() => props.mode ?? props.health?.mode ?? null)
const model = computed(() => props.model ?? props.health?.model ?? null)
const offline = computed(() => !mode.value && props.unreachable)
const provider = computed(() => providerName(props.health?.provider, props.health?.base_url_host))
const label = computed(() => (mode.value ? t(`sov.${mode.value}`) : offline.value ? t('offline.badge') : t('sov.loading')))
/** Colour of the status dot's halo (the shape inside keeps the meaning without colour). */
const dotColor = computed(() => (mode.value ? MODE_COLOR[mode.value] : offline.value ? 'var(--red-text)' : 'var(--grey-shape)'))
/**
 * A problem with the current configuration (UX-8: replay without recordings;
 * UX-22: model not reachable). Only for the header and About badges: the inline
 * badge of a report or scan describes that run.
 */
const warning = computed(() => {
  const h = props.health
  if (!h || props.variant === 'inline' || (props.mode && props.mode !== h.mode)) return null
  if (h.mode === 'replay' && typeof h.replay_recorded?.records === 'number' && h.replay_recorded.records === 0) return t('sov.replay.empty')
  if (h.mode !== 'replay' && h.llm_reachable === false) return t('sov.llmDown')
  return null
})
const sub = computed(() => {
  if (!mode.value) return ''
  if (mode.value === 'swiss_cloud') return t('sov.swiss_cloud.sub', { provider: provider.value })
  return t(`sov.${mode.value}.sub`)
})

/** Computed from the configured model, never assumed: only Apertus gets "open weights · Apache-2.0" (SOV-3). */
function describeModel(m: string | null | undefined): string {
  if (!m) return '—'
  return isApertus(m) ? t('sov.model', { model: prettyModel(m) }) : m
}
const modelLine = computed(() => {
  const recorded = props.health?.replay_models
  if (mode.value === 'replay' && recorded?.length) return t('sov.recorded', { models: recorded.map(describeModel).join(', ') })
  return describeModel(model.value)
})

/**
 * "AI requests that left this network" (SOV-1/2), counted per destination by the
 * server (Health.ai_requests). Unknown stays "unknown", never 0 (FE-1).
 */
const counterInfo = computed(() => aiCounterText(mode.value, props.health?.ai_requests, provider.value))
const counter = computed(() => counterInfo.value.text)
const counterSource = computed(() => (counterInfo.value.measured ? t('sov.measured') : t('sov.notReported')))
const left = computed(() => leftNetwork(props.health?.ai_requests))
const DESTS: { key: Destination; label: MessageKey }[] = [
  { key: 'local', label: 'sov.dest.local' },
  { key: 'swiss_cloud', label: 'sov.dest.swiss_cloud' },
  { key: 'external', label: 'sov.dest.external' },
]
const dests = computed(() =>
  DESTS.map((d) => {
    const n = props.health?.ai_requests?.[d.key]
    return { ...d, n: n == null ? null : n }
  }),
)
const vision = computed(() => {
  const h = props.health
  // vision_source "error" with an unreachable model means "unreachable", not "no vision".
  if (h?.llm_reachable === false) return t('sov.llmDown')
  if (h?.vision_source === 'pending') return t('sov.visionPending')
  if (h?.vision == null) return t('sov.visionUnknown')
  return h.vision ? t('sov.visionOn') : t('sov.visionOff')
})

const open = ref(false)
const panelId = useId()
const root = ref<HTMLElement | null>(null)
const button = ref<HTMLButtonElement | null>(null)

function onDocClick(e: MouseEvent) {
  if (root.value && !root.value.contains(e.target as Node)) open.value = false
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape' && open.value) {
    e.preventDefault()
    open.value = false
    button.value?.focus({ preventScroll: true })
  }
}
watch(open, (o) => {
  if (o) {
    document.addEventListener('click', onDocClick)
    document.addEventListener('keydown', onKey)
  } else {
    document.removeEventListener('click', onDocClick)
    document.removeEventListener('keydown', onKey)
  }
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('keydown', onKey)
})
/** Keyboard users who tab past the panel leave it closed behind them. */
function onFocusOut(e: FocusEvent) {
  const next = e.relatedTarget as Node | null
  if (open.value && next && root.value && !root.value.contains(next)) open.value = false
}
const route = useRoute()
watch(() => route.fullPath, () => (open.value = false))
</script>

<template>
  <!-- Header: one compact pill; the panel holds the detail. -->
  <div v-if="variant === 'header'" ref="root" class="sov" :class="mode ? `sov--${mode}` : offline ? 'sov--offline' : 'sov--loading'" @focusout="onFocusOut">
    <button ref="button" type="button" class="sov__pill" :aria-expanded="open" :aria-controls="panelId" @click="open = !open">
      <span class="sov__dot" :style="{ '--dot': dotColor }" aria-hidden="true">
        <ShapeIcon v-if="mode" :shape="MODE_SHAPE[mode]" :color="MODE_COLOR[mode]" :size="8" />
        <ShapeIcon v-else-if="offline" shape="ring" color="var(--red-text)" :size="9" />
        <ShapeIcon v-else shape="ring" color="var(--grey-shape)" :size="9" />
      </span>
      <span class="sov__label">{{ label }}</span>
      <ShapeIcon v-if="warning" class="sov__warn" shape="diamond" color="var(--amber)" :size="8" />
      <span class="sr-only"><template v-if="warning">, {{ warning }}</template>. {{ t('sov.details') }}</span>
    </button>

    <Transition name="fade-rise">
      <div v-show="open" :id="panelId" class="sov__panel" role="region" :aria-label="t('sov.details')">
        <template v-if="offline">
          <p class="sov__big">
            <ShapeIcon shape="ring" color="var(--red-text)" :size="12" />
            <span>{{ t('offline.title') }}</span>
          </p>
          <p class="sov__line">{{ t('offline.body') }}</p>
        </template>
        <template v-else>
          <p class="sov__q">{{ t('sov.question') }}</p>
          <p class="sov__big">
            <ShapeIcon v-if="mode" :shape="MODE_SHAPE[mode]" :color="MODE_COLOR[mode]" :size="12" />
            <span>{{ label }}</span>
          </p>
          <p v-if="sub" class="sov__line">{{ sub }}</p>
          <p v-if="mode === 'swiss_cloud'" class="sov__line">{{ t('sov.providerDocs') }}</p>

          <div v-if="warning" class="sov__alert">
            <ShapeIcon shape="diamond" color="var(--amber)" :size="9" />
            <div>
              <p class="sov__alert-title">{{ warning }}</p>
              <p v-if="health?.llm_error" class="sov__alert-detail mono" translate="no">{{ health.llm_error }}</p>
            </div>
          </div>

          <!-- The proof: requests counted by the server, per destination. -->
          <div class="sov__count">
            <p v-if="left !== null" class="sov__count-row">
              <span class="sov__count-n tabular">{{ formatNumber(left) }}</span>
              <span class="sov__count-label">{{ t('sov.left') }}</span>
            </p>
            <!-- FE-1: a number the server did not report stays "unknown", never 0. -->
            <p v-else class="sov__count-label">{{ counter }}</p>
            <dl class="sov__dest">
              <div v-for="d in dests" :key="d.key">
                <dt>{{ t(d.label) }}</dt>
                <dd class="tabular">{{ d.n === null ? t('common.unknown') : formatNumber(d.n) }}</dd>
              </div>
            </dl>
            <p class="sov__fine">{{ counterSource }} {{ t('sov.computed') }}</p>
          </div>

          <dl class="sov__dl">
            <div>
              <dt>{{ t('report.meta.model') }}</dt>
              <dd>{{ modelLine }}</dd>
            </div>
            <div>
              <dt>{{ t('sov.endpoint') }}</dt>
              <dd class="mono" translate="no">{{ health?.base_url_host ?? '—' }}</dd>
            </div>
            <div>
              <dt>{{ t('sov.vision') }}</dt>
              <dd>{{ vision }}</dd>
            </div>
          </dl>
        </template>
        <RouterLink class="sov__more" :to="{ name: 'about', hash: '#modes' }">
          {{ t('sov.learnMore') }}<ArrowRight :size="14" aria-hidden="true" />
        </RouterLink>
      </div>
    </Transition>
  </div>

  <!-- Inline -->
  <span v-else-if="variant === 'inline'" class="sov-inline">
    <ShapeIcon v-if="mode" :shape="MODE_SHAPE[mode]" :color="MODE_COLOR[mode]" :size="10" />
    <strong>{{ label }}</strong>
    <span v-if="warning" class="sov__warn-inline"><ShapeIcon shape="diamond" color="var(--amber)" :size="8" />{{ warning }}</span>
    <span v-else-if="sub" class="muted">{{ sub }}</span>
  </span>

  <!-- Card -->
  <div v-else class="sov-card" :class="mode ? `sov--${mode}` : ''">
    <p class="sov__q">{{ t('sov.question') }}</p>
    <p class="sov-card__big">
      <ShapeIcon v-if="mode" :shape="MODE_SHAPE[mode]" :color="MODE_COLOR[mode]" :size="16" />
      <span>{{ label }}</span>
    </p>
    <template v-if="mode">
      <p class="sov__line">{{ sub }}</p>
      <p v-if="warning" class="sov__line sov__line--warn"><ShapeIcon shape="diamond" color="var(--amber)" :size="8" />{{ warning }}</p>
      <p v-if="mode === 'swiss_cloud'" class="sov__line">{{ t('sov.providerDocs') }}</p>
      <p class="sov-card__model">{{ modelLine }}</p>
      <p class="sov__counter tabular">{{ counter }}</p>
      <p class="sov__fine">{{ counterSource }} {{ t('sov.computed') }}</p>
    </template>
    <p v-else-if="offline" class="sov__line">{{ t('offline.body') }}</p>
  </div>
</template>

<style scoped>
.sov {
  position: relative;
  min-width: 0;
}

/* ---- Pill ---- */
.sov__pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  max-width: 100%;
  height: 36px;
  padding: 0 14px 0 10px;
  background: var(--surface);
  color: var(--ink);
  border: 1px solid var(--line-strong);
  border-radius: var(--r-pill);
  box-shadow: var(--shadow-xs);
  font-size: var(--fs-13);
  font-weight: 600;
  letter-spacing: var(--tr-ui);
  white-space: nowrap;
  transition: border-color var(--dur-1) var(--ease-out), background-color var(--dur-1) var(--ease-out),
    transform var(--dur-1) var(--ease-out);
}
.sov__pill:hover {
  border-color: var(--control-border);
}
.sov__pill:active {
  transform: scale(0.98);
}
.sov__pill[aria-expanded='true'] {
  border-color: var(--ink);
}
.sov__dot {
  display: grid;
  place-items: center;
  flex: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--dot) 16%, transparent);
}
.sov__label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sov__warn {
  margin-left: -2px;
}

/* ---- Panel ---- */
.sov__panel {
  position: absolute;
  right: 0;
  top: calc(100% + 10px);
  z-index: 40;
  width: 360px;
  padding: var(--s-5);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
  box-shadow: var(--shadow-overlay);
  font-size: var(--fs-14);
  white-space: normal;
}
/* Small screens: the panel spans the page under the header instead of hanging off the pill. */
@media (max-width: 639px) {
  .sov {
    position: static;
  }
  .sov__panel {
    position: fixed;
    top: calc(var(--header-h) + 8px);
    left: var(--page-pad);
    right: var(--page-pad);
    width: auto;
    max-height: calc(100dvh - var(--header-h) - 24px);
    overflow-y: auto;
  }
}
.sov__q {
  font-size: var(--fs-13);
  font-weight: 600;
  color: var(--muted);
}
.sov__big {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: var(--s-1);
  font-size: var(--fs-20);
  font-weight: 650;
  letter-spacing: var(--tr-h3);
  line-height: var(--lh-snug);
}
.sov__line {
  margin-top: 2px;
  color: var(--muted);
}
.sov__alert {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-top: var(--s-4);
  padding: var(--s-3);
  background: var(--amber-tint);
  border-radius: var(--r-control);
}
.sov__alert > svg {
  transform: translateY(1px);
}
.sov__alert-title {
  font-weight: 600;
}
.sov__alert-detail {
  margin-top: 2px;
  font-size: var(--fs-12);
  color: var(--ink);
  overflow-wrap: anywhere;
}

.sov__count {
  margin-top: var(--s-5);
  padding-top: var(--s-4);
  border-top: 1px solid var(--line);
}
.sov__count-row {
  display: flex;
  align-items: baseline;
  gap: var(--s-3);
}
.sov__count-n {
  font-size: var(--fs-32);
  font-weight: 700;
  letter-spacing: var(--tr-h1);
  line-height: 1;
}
.sov--external .sov__count-n {
  color: var(--amber);
}
.sov__count-label {
  font-weight: 600;
  line-height: var(--lh-snug);
}
.sov__dest {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--s-2);
  margin: var(--s-4) 0 0;
}
.sov__dest div {
  padding: var(--s-2) var(--s-3);
  background: var(--surface-2);
  border-radius: var(--r-control);
}
.sov__dest dt {
  font-size: var(--fs-12);
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sov__dest dd {
  margin: 0;
  font-weight: 650;
}
.sov__fine {
  margin-top: var(--s-2);
  font-size: var(--fs-12);
  color: var(--muted);
}

.sov__dl {
  margin: var(--s-5) 0 0;
  padding-top: var(--s-4);
  border-top: 1px solid var(--line);
  display: grid;
  gap: var(--s-2);
}
.sov__dl div {
  display: grid;
  grid-template-columns: 8.5em 1fr;
  gap: var(--s-3);
}
.sov__dl dt {
  color: var(--muted);
}
.sov__dl dd {
  margin: 0;
  overflow-wrap: anywhere;
}
.sov__more {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: var(--s-4);
  min-height: 24px;
  font-weight: 600;
}
.sov__more svg {
  transition: transform var(--dur-2) var(--ease-out);
}
.sov__more:hover svg {
  transform: translateX(3px);
}

/* ---- Inline (report, scan) ---- */
.sov__warn-inline,
.sov__line--warn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-12);
  font-weight: 600;
  color: var(--ink);
  white-space: nowrap;
}
.sov__line--warn {
  font-size: var(--fs-14);
  white-space: normal;
}
.sov-inline {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  column-gap: 8px;
  font-size: var(--fs-14);
}
.sov-inline strong {
  font-weight: 650;
}
.sov-inline .muted {
  font-weight: 400;
}

/* ---- Card (About) ---- */
.sov__counter {
  margin-top: var(--s-4);
  padding: var(--s-2) var(--s-3);
  background: var(--surface-2);
  border-radius: var(--r-control);
  font-size: var(--fs-14);
  font-weight: 600;
}
.sov--external .sov__counter {
  background: var(--amber-tint);
  color: var(--amber);
}
.sov-card {
  padding: var(--s-5);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
}
.sov-card .sov__line {
  font-size: var(--fs-14);
}
.sov-card__big {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: var(--s-2);
  font-size: var(--fs-32);
  font-weight: 700;
  letter-spacing: var(--tr-h1);
  line-height: 1.1;
}
.sov-card__model {
  margin-top: var(--s-3);
  font-weight: 600;
}

@media (prefers-reduced-motion: reduce) {
  .sov__pill:active,
  .sov__more:hover svg {
    transform: none;
  }
}
@media (forced-colors: active) {
  .sov__pill {
    border-color: ButtonText;
  }
  .sov__dest div,
  .sov__alert {
    border: 1px solid CanvasText;
  }
}
</style>
