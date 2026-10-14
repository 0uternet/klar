<script setup lang="ts">
import { computed, onBeforeUnmount, ref, useId, watch } from 'vue'
import { useRoute } from 'vue-router'
import type { Health, Mode } from '@/types'
import { t } from '@/i18n'
import { aiCounterText } from '@/lib/sovereignty'
import { MODE_COLOR, MODE_SHAPE, isApertus, prettyModel, providerName } from '@/lib/format'
import ShapeIcon from './ShapeIcon.vue'

/**
 * Sovereignty badge: computed from GET /api/health, never hard-coded.
 * Answers one question: where do your pages go?
 *  - header: compact pill + disclosure panel with the details
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
/**
 * A problem with the current configuration, shown instead of the subline with an
 * amber diamond (UX-8: replay without recordings; UX-22: model not reachable).
 * Only for the header and About badges: the inline badge of a report or scan describes that run.
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
 * "AI requests that left this network: N" (SOV-1/2), counted per destination by the
 * server (Health.ai_requests). Unknown stays "unknown", never 0 (FE-1).
 */
const counterInfo = computed(() => aiCounterText(mode.value, props.health?.ai_requests, provider.value))
const counter = computed(() => counterInfo.value.text)
const counterSource = computed(() => (counterInfo.value.measured ? t('sov.measured') : t('sov.notReported')))
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
    button.value?.focus()
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
const route = useRoute()
watch(() => route.fullPath, () => (open.value = false))
</script>

<template>
  <!-- Header pill with disclosure panel -->
  <div v-if="variant === 'header'" ref="root" class="sov" :class="mode ? `sov--${mode}` : offline ? 'sov--offline' : 'sov--loading'">
    <button
      ref="button"
      type="button"
      class="sov__pill"
      :aria-expanded="open"
      :aria-controls="panelId"
      @click="open = !open"
    >
      <ShapeIcon v-if="mode" :shape="MODE_SHAPE[mode]" :color="MODE_COLOR[mode]" :size="10" />
      <ShapeIcon v-else-if="offline" shape="ring" color="var(--red-text)" :size="10" />
      <span v-else class="sov__loading" aria-hidden="true" />
      <span class="sov__text">
        <span class="sov__label">{{ label }}</span>
        <span v-if="warning" class="sov__warn"><ShapeIcon shape="diamond" color="var(--amber)" :size="8" /><span class="sov__warn-text">{{ warning }}</span></span>
        <span v-else-if="sub" class="sov__sub">{{ sub }}</span>
        <span class="sr-only">. {{ t('sov.details') }}</span>
      </span>
    </button>
    <div v-show="open" :id="panelId" class="sov__panel" role="region" :aria-label="t('sov.details')">
      <template v-if="offline">
        <p class="sov__big">{{ t('offline.title') }}</p>
        <p class="sov__line">{{ t('offline.body') }}</p>
      </template>
      <template v-else>
        <p class="sov__q">{{ t('sov.question') }}</p>
        <p class="sov__big">
          <ShapeIcon v-if="mode" :shape="MODE_SHAPE[mode]" :color="MODE_COLOR[mode]" :size="12" />
          <span>{{ label }}</span>
        </p>
        <p class="sov__line">{{ sub }}</p>
        <p v-if="warning" class="sov__line sov__line--warn"><ShapeIcon shape="diamond" color="var(--amber)" :size="8" />{{ warning }}</p>
        <p v-if="warning && health?.llm_error" class="sov__fine mono">{{ health.llm_error }}</p>
        <p v-if="mode === 'swiss_cloud'" class="sov__line">{{ t('sov.providerDocs') }}</p>
        <dl class="sov__dl">
          <div>
            <dt>{{ t('report.meta.model') }}</dt>
            <dd>{{ modelLine }}</dd>
          </div>
          <div>
            <dt>{{ t('sov.endpoint') }}</dt>
            <dd class="mono">{{ health?.base_url_host ?? '—' }}</dd>
          </div>
          <div>
            <dt>{{ t('sov.vision') }}</dt>
            <dd>{{ vision }}</dd>
          </div>
        </dl>
        <p class="sov__counter tabular">{{ counter }}</p>
        <p class="sov__fine">{{ counterSource }} {{ t('sov.computed') }}</p>
      </template>
      <RouterLink class="sov__more" :to="{ name: 'about', hash: '#modes' }">{{ t('sov.learnMore') }}</RouterLink>
    </div>
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
}
.sov__pill {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 40px;
  padding: 4px 14px 4px 12px;
  background: var(--surface);
  color: var(--ink);
  border: 1px solid var(--line);
  border-radius: var(--r-pill);
  text-align: left;
  transition: border-color var(--dur-1) var(--ease), background-color var(--dur-1) var(--ease);
}
.sov__pill:hover {
  border-color: var(--control-border);
}
.sov__pill[aria-expanded='true'] {
  border-color: var(--ink);
}
.sov__text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}
.sov__label {
  font-size: var(--fs-14);
  font-weight: 600;
  white-space: nowrap;
}
.sov__warn,
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
.sov__sub {
  display: none;
  font-size: var(--fs-12);
  color: var(--muted);
  white-space: nowrap;
}
@media (min-width: 1360px) {
  .sov__sub {
    display: block;
  }
}
.sov__loading {
  width: 10px;
  height: 10px;
  background: var(--klar-red);
  animation: klar-pulse 1.2s ease-in-out infinite;
}
.sov__panel {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  z-index: 40;
  width: min(360px, calc(100vw - 32px));
  padding: var(--s-5);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
  box-shadow: var(--shadow-overlay);
  animation: klar-fade-up var(--dur-2) var(--ease);
}
.sov__q {
  font-size: var(--fs-14);
  font-weight: 600;
  color: var(--muted);
}
.sov__big {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: var(--s-2);
  font-size: var(--fs-20);
  font-weight: 700;
  letter-spacing: -0.01em;
}
.sov__line {
  margin-top: 2px;
  color: var(--muted);
  font-size: var(--fs-14);
}
.sov__dl {
  margin: var(--s-4) 0 0;
  display: grid;
  gap: var(--s-2);
  font-size: var(--fs-14);
}
.sov__dl div {
  display: grid;
  grid-template-columns: 9.5em 1fr;
  gap: var(--s-3);
  padding-top: var(--s-2);
  border-top: 1px solid var(--line);
}
.sov__dl dt {
  color: var(--muted);
}
.sov__dl dd {
  margin: 0;
  overflow-wrap: anywhere;
}
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
.sov__fine {
  margin-top: var(--s-3);
  font-size: var(--fs-12);
  color: var(--muted);
}
.sov__more {
  display: inline-block;
  margin-top: var(--s-3);
  font-size: var(--fs-14);
  font-weight: 600;
}
.sov-inline {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  column-gap: 8px;
  font-size: var(--fs-14);
}
.sov-inline strong {
  font-weight: 700;
}
.sov-inline .muted {
  font-weight: 400;
}
.sov-card {
  padding: var(--s-5);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
}
.sov-card__big {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: var(--s-2);
  font-size: var(--fs-32);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.1;
}
.sov-card__model {
  margin-top: var(--s-3);
  font-weight: 600;
}
</style>
