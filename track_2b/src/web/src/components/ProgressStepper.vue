<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { Check, Minus, X } from '@lucide/vue'
import type { ProgressStep } from '@/types'
import { KNOWN_STEPS } from '@/types'
import { formatNumber, t } from '@/i18n'
import { useNow } from '@/composables/useNow'

/**
 * Render → axe-core → Extract N elements → Apertus x/y → Verify evidence → Done,
 * with a live duration for each step. Durations of running steps are
 * measured on the client to avoid clock skew with the server.
 */
const props = defineProps<{
  steps: ProgressStep[]
  /** The scan ended in error: steps that never ran read "Skipped" (the server does not emit them). */
  failed?: boolean
  /** Plain title of the failure, shown on the failed step; the raw text stays under Details (UX-6). */
  errorTitle?: string
}>()
const now = useNow(100)

const firstSeen = reactive(new Map<string, number>())
watch(
  () => props.steps.map((s) => `${s.step}:${s.state}`).join('|'),
  () => {
    for (const s of props.steps) if (s.state === 'running' && !firstSeen.has(s.step)) firstSeen.set(s.step, Date.now())
  },
  { immediate: true },
)

const ordered = computed(() => {
  const known = KNOWN_STEPS.map((k) => props.steps.find((s) => s.step === k) ?? { step: k, state: 'pending', started_at: null, duration_ms: null, detail: null })
  const extra = props.steps.filter((s) => !(KNOWN_STEPS as readonly string[]).includes(s.step))
  const all = [...known, ...extra] as ProgressStep[]
  if (!props.failed) return all
  return all.map((s) => (s.state === 'pending' || s.state === 'running' ? { ...s, state: s.state === 'running' ? 'error' : 'skipped' } : s)) as ProgressStep[]
})

function label(s: ProgressStep): string {
  return (KNOWN_STEPS as readonly string[]).includes(s.step) ? t(`scan.step.${s.step as (typeof KNOWN_STEPS)[number]}`) : s.step
}

function fraction(s: ProgressStep): [number, number] | null {
  if (typeof s.current === 'number' && typeof s.total === 'number' && s.total > 0) return [s.current, s.total]
  const m = s.detail?.match(/^(\d+)\s*\/\s*(\d+)$/)
  return m ? [Number(m[1]), Number(m[2])] : null
}

function duration(s: ProgressStep): string {
  let ms: number | null = null
  if (s.state === 'done' || s.state === 'error') ms = s.duration_ms
  else if (s.state === 'running') ms = now.value - (firstSeen.get(s.step) ?? now.value)
  if (ms == null) return ''
  return `${formatNumber(ms / 1000, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} s`
}

function detail(s: ProgressStep): string {
  // The plain failure title goes on the step that failed first, not on every step marked as failed.
  if (s.state === 'error') return ordered.value.find((x) => x.state === 'error') === s ? (props.errorTitle ?? '') : ''
  if (s.state === 'skipped') return t('scan.state.skipped')
  // UX-21: no count on the axe-core step (its findings arrive later, after extraction).
  if (s.step === 'axe') return ''
  const f = fraction(s)
  if (f && s.step === 'apertus') return t('scan.questions', { x: formatNumber(f[0]), y: formatNumber(f[1]) })
  return s.detail ?? ''
}
</script>

<template>
  <ol class="stepper" role="list">
    <li v-for="(s, i) in ordered" :key="s.step" class="step" :class="`step--${s.state}`">
      <span class="step__rail" aria-hidden="true">
        <span class="step__icon">
          <Check v-if="s.state === 'done'" :size="14" :stroke-width="3" />
          <X v-else-if="s.state === 'error'" :size="14" :stroke-width="3" />
          <Minus v-else-if="s.state === 'skipped'" :size="14" :stroke-width="3" />
          <span v-else-if="s.state === 'running'" class="step__live" />
          <span v-else class="step__index">{{ i + 1 }}</span>
        </span>
      </span>
      <span class="step__body">
        <span class="step__head">
          <span class="step__label">{{ label(s) }}</span>
          <span class="sr-only">: {{ t(`scan.state.${s.state}`) }}</span>
          <span class="step__time tabular" aria-hidden="true">{{ duration(s) }}</span>
        </span>
        <span v-if="detail(s)" class="step__detail tabular" :aria-hidden="s.state === 'skipped' ? 'true' : undefined">{{ detail(s) }}</span>
        <span v-if="s.step === 'apertus' && fraction(s) && s.state !== 'pending'" class="step__bar" aria-hidden="true">
          <span class="step__fill" :style="{ transform: `scaleX(${fraction(s)![0] / fraction(s)![1]})` }" />
        </span>
      </span>
    </li>
  </ol>
</template>

<style scoped>
.stepper {
  margin: 0;
  padding: 0;
  list-style: none;
}
.step {
  position: relative;
  display: grid;
  grid-template-columns: 28px 1fr;
  gap: var(--s-4);
  padding-bottom: var(--s-5);
}
.step:last-child {
  padding-bottom: 0;
}
.step:not(:last-child)::before {
  content: '';
  position: absolute;
  left: 13.5px;
  top: 30px;
  bottom: 2px;
  width: 1px;
  background: var(--line);
}
.step--done:not(:last-child)::before {
  background: var(--ink);
}
.step__rail {
  display: flex;
  justify-content: center;
}
.step__icon {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid var(--control-border);
  background: var(--surface);
  color: var(--muted);
  font-size: var(--fs-12);
  font-weight: 700;
  transition: background-color var(--dur-2) var(--ease), border-color var(--dur-2) var(--ease);
}
.step--done .step__icon {
  background: var(--ink);
  border-color: var(--ink);
  color: var(--on-ink);
}
.step--running .step__icon {
  border-color: var(--ink);
}
.step--error .step__icon {
  background: var(--klar-red);
  border-color: var(--klar-red);
  color: var(--bg);
}
.step__live {
  width: 10px;
  height: 10px;
  background: var(--klar-red);
  animation: klar-pulse 1s ease-in-out infinite;
}
.step__body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  padding-top: 3px;
}
.step__head {
  display: flex;
  align-items: baseline;
  gap: var(--s-3);
}
.step__label {
  font-weight: 600;
  color: var(--ink);
}
.step--error .step__detail,
.step--skipped .step__detail {
  font-family: var(--font-sans);
}
.step--error .step__detail {
  color: var(--red-text);
  font-weight: 600;
}
.step--skipped .step__label,
.step--pending .step__label {
  color: var(--muted);
  font-weight: 500;
}
.step__time {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: var(--fs-14);
  color: var(--muted);
}
.step--running .step__time {
  color: var(--ink);
}
.step__detail {
  font-family: var(--font-mono);
  font-size: var(--fs-14);
  color: var(--muted);
}
.step__bar {
  display: block;
  height: 4px;
  margin-top: 4px;
  background: var(--surface-3);
  border-radius: 2px;
  overflow: hidden;
}
.step__fill {
  display: block;
  height: 100%;
  background: var(--ink);
  transform-origin: left;
  transition: transform var(--dur-2) var(--ease);
}
</style>
