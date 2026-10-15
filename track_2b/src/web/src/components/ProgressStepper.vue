<script setup lang="ts">
import { computed } from 'vue'
import { Minus, X } from '@lucide/vue'
import type { ProgressStep } from '@/types'
import { KNOWN_STEPS } from '@/types'
import { formatNumber, t } from '@/i18n'
import CountUp from './CountUp.vue'

/**
 * Render → axe-core → Extract N elements → Apertus x/y → Verify evidence → Done.
 * The rail fills as steps complete (and as Apertus answers, within its step); each
 * step's check draws itself and its duration fades in when it completes. The total
 * elapsed time lives in the page header, so running steps show a live mark, not a clock.
 */
const props = defineProps<{
  steps: ProgressStep[]
  /** The scan ended in error: steps that never ran read "Skipped" (the server does not emit them). */
  failed?: boolean
  /** Plain title of the failure, shown on the failed step; the raw text stays under Details (UX-6). */
  errorTitle?: string
}>()

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
  if ((s.state !== 'done' && s.state !== 'error') || s.duration_ms == null) return ''
  return `${formatNumber(s.duration_ms / 1000, { minimumFractionDigits: 1, maximumFractionDigits: 1 })} s`
}

/** "{x} of {y} questions", split around {x} so x can count up in any word order. */
function questions(f: [number, number]): [string, string] {
  const [a = '', b = ''] = t('scan.questions', { x: '\u0001', y: formatNumber(f[1]) }).split('\u0001')
  return [a, b]
}
const fmt = (n: number) => formatNumber(Math.round(n))

function detail(s: ProgressStep): string {
  // The plain failure title goes on the step that failed first, not on every step marked as failed.
  if (s.state === 'error') return ordered.value.find((x) => x.state === 'error') === s ? (props.errorTitle ?? '') : ''
  if (s.state === 'skipped') return t('scan.state.skipped')
  // UX-21: no count on the axe-core step (its findings arrive later, after extraction).
  // The render step's detail is the page title or address, already the page's H1.
  if (s.step === 'axe' || s.step === 'render') return ''
  return s.detail ?? ''
}

/** How much of the rail below a step is filled: done = all, Apertus = its share of answers. */
function fill(s: ProgressStep): number {
  if (s.state === 'done') return 1
  const f = s.state === 'running' ? fraction(s) : null
  return f ? Math.min(1, f[0] / f[1]) : 0
}
</script>

<template>
  <ol class="stepper" role="list">
    <li v-for="(s, i) in ordered" :key="s.step" class="step" :class="`step--${s.state}`">
      <span class="step__icon" aria-hidden="true">
        <span class="step__disc" />
        <svg v-if="s.state === 'done'" class="step__check" viewBox="0 0 16 16" width="14" height="14" focusable="false">
          <path class="m-draw" pathLength="1" d="M3.2 8.6 6.4 11.6 12.8 4.6" />
        </svg>
        <X v-else-if="s.state === 'error'" class="step__glyph" :size="14" :stroke-width="3" />
        <Minus v-else-if="s.state === 'skipped'" class="step__glyph" :size="14" :stroke-width="3" />
        <span v-else-if="s.state === 'running'" class="step__live" />
        <span v-else class="step__index">{{ i + 1 }}</span>
      </span>
      <span v-if="i < ordered.length - 1" class="step__rail" aria-hidden="true">
        <span class="step__rail-fill" :style="{ transform: `scaleY(${fill(s)})` }" />
      </span>

      <span class="step__body">
        <span class="step__head">
          <span class="step__label">{{ label(s) }}</span>
          <span class="sr-only">: {{ t(`scan.state.${s.state}`) }}</span>
          <Transition name="fade">
            <span v-if="duration(s)" class="step__time tabular" aria-hidden="true">{{ duration(s) }}</span>
          </Transition>
        </span>
        <template v-if="s.step === 'apertus' && fraction(s) && s.state !== 'pending' && s.state !== 'skipped'">
          <span class="step__detail tabular">
            {{ questions(fraction(s)!)[0] }}<CountUp :value="fraction(s)![0]" :duration="560" :format="fmt" />{{ questions(fraction(s)!)[1] }}
          </span>
          <span class="step__bar" aria-hidden="true">
            <span class="step__bar-fill" :style="{ transform: `scaleX(${fraction(s)![0] / fraction(s)![1]})` }" />
          </span>
        </template>
        <span v-else-if="detail(s)" class="step__detail" :aria-hidden="s.state === 'skipped' ? 'true' : undefined">{{ detail(s) }}</span>
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
  grid-template-columns: 28px minmax(0, 1fr);
  column-gap: var(--s-4);
  padding-bottom: var(--s-5);
}
.step:last-child {
  padding-bottom: 0;
}

/* ---- Icon: a disc that fills, a check that draws ---- */
.step__icon {
  position: relative;
  z-index: 1;
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
}
.step__icon > * {
  grid-area: 1 / 1;
}
.step__disc {
  width: 28px;
  height: 28px;
  margin: -1px;
  border-radius: 50%;
  background: var(--ink);
  transform: scale(0);
  transition: transform var(--dur-3) var(--ease-spring);
}
.step--done .step__icon,
.step--running .step__icon {
  border-color: var(--ink);
}
.step--done .step__disc {
  transform: scale(1);
}
.step--error .step__icon {
  border-color: var(--klar-red);
}
.step--error .step__disc {
  background: var(--klar-red);
  transform: scale(1);
}
.step__check {
  position: relative;
  fill: none;
  stroke: var(--on-ink);
  stroke-width: 2.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.step__check .m-draw {
  animation-delay: 90ms;
}
.step__glyph {
  position: relative;
  color: var(--on-ink);
}
.step--skipped .step__glyph {
  color: var(--muted);
}
.step__index {
  font-variant-numeric: tabular-nums;
}

/* Running: a red square with a soft halo (a progress indicator, like a loading state). */
.step__live {
  width: 8px;
  height: 8px;
  background: var(--klar-red);
}
.step--running .step__icon::after {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 50%;
  border: 1.5px solid var(--klar-red);
  opacity: 0;
  animation: step-halo calc(var(--dur-4) * 3) var(--ease-out) infinite;
}
@keyframes step-halo {
  from {
    opacity: 0.55;
    transform: scale(1);
  }
  to {
    opacity: 0;
    transform: scale(1.65);
  }
}

/* ---- Rail between icons: fills top-down as the step completes ---- */
.step__rail {
  position: absolute;
  left: 13px;
  top: 32px;
  bottom: 4px;
  width: 2px;
  overflow: hidden;
  border-radius: 1px;
  background: var(--line);
}
.step__rail-fill {
  position: absolute;
  inset: 0;
  background: var(--ink);
  transform-origin: top;
  transition: transform var(--dur-4) var(--ease-out);
}

/* ---- Text ---- */
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
.step--skipped .step__label,
.step--pending .step__label {
  color: var(--muted);
  font-weight: 500;
}
.step__time {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: var(--fs-12);
  color: var(--muted);
}
.step__detail {
  font-size: var(--fs-14);
  color: var(--muted);
  overflow-wrap: anywhere;
}
.step--error .step__detail {
  color: var(--red-text);
  font-weight: 600;
}
.step__bar {
  position: relative;
  display: block;
  height: 4px;
  margin-top: 6px;
  overflow: hidden;
  background: var(--surface-3);
  border-radius: 2px;
}
.step__bar-fill {
  position: absolute;
  inset: 0;
  background: var(--ink);
  border-radius: inherit;
  transform-origin: left;
  transition: transform var(--dur-4) var(--ease-out);
}

@media (forced-colors: active) {
  .step__disc,
  .step__rail-fill,
  .step__bar-fill,
  .step__live {
    background: CanvasText;
  }
  .step__check {
    stroke: Canvas;
  }
  .step__glyph {
    color: Canvas;
  }
}
</style>
