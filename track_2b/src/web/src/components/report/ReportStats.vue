<script setup lang="ts">
import { computed, useId } from 'vue'
import { ArrowRight } from '@lucide/vue'
import type { Outcome } from '@/types'
import { formatNumber, t } from '@/i18n'
import CountUp from '@/components/CountUp.vue'
import ShapeIcon from '@/components/ShapeIcon.vue'

/**
 * The triage numbers (they count up; screen readers hear the final value):
 * what is left to decide, what failed, and who pre-checked it (code or Apertus).
 * Failed, Code and Apertus filter the list; the review button is the page's one primary action.
 */
const props = defineProps<{
  remaining: number
  done: number
  total: number
  failed: number
  byCode: number
  byApertus: number
  outcome: Outcome | ''
  by: '' | 'code' | 'apertus'
  cta: string | null
}>()
const emit = defineEmits<{ outcome: [o: Outcome]; by: [b: 'code' | 'apertus']; start: [] }>()

const fmt = (n: number) => formatNumber(Math.round(n))
const ratio = computed(() => (props.total ? props.done / props.total : 0))
const codeShare = computed(() => {
  const all = props.byCode + props.byApertus
  return all ? props.byCode / all : 0
})
const byId = useId()
</script>

<template>
  <div class="st" role="group" :aria-label="t('report.summary')">
    <div class="st__cell st__cell--lead m-rise" style="--i: 1">
      <p class="st__label">{{ t('status.to_review') }}</p>
      <p class="st__n"><CountUp :value="remaining" :format="fmt" /></p>
      <div class="st__foot">
        <span
          class="st__track"
          role="progressbar"
          :aria-label="t('report.reviewed')"
          aria-valuemin="0"
          :aria-valuemax="total"
          :aria-valuenow="done"
          :aria-valuetext="t('report.reviewedScope', { done: fmt(done), total: fmt(total) })"
        >
          <span class="st__grow m-grow" style="--i: 3"><span class="st__fill" :style="{ transform: `scaleX(${ratio})` }" /></span>
        </span>
        <span class="st__sub tabular" aria-hidden="true">{{ t('report.reviewedScope', { done: fmt(done), total: fmt(total) }) }}</span>
      </div>
    </div>

    <button type="button" class="st__cell st__cell--failed st__btn m-rise" style="--i: 2" :aria-pressed="outcome === 'failed'" @click="emit('outcome', 'failed')">
      <span class="st__label">{{ t('outcome.failed') }}</span>
      <span class="st__n"><ShapeIcon shape="square" color="var(--klar-red)" :size="10" /><CountUp :value="failed" :format="fmt" /></span>
    </button>

    <div class="st__cell st__cell--by m-rise" style="--i: 2" role="group" :aria-labelledby="byId">
      <p :id="byId" class="st__label">{{ t('filter.source') }}</p>
      <div class="st__pair">
        <button type="button" class="st__btn st__btn--pair" :aria-pressed="by === 'code'" @click="emit('by', 'code')">
          <span class="st__n"><CountUp :value="byCode" :format="fmt" /></span>
          <span class="st__unit">{{ t('report.byCode') }}</span>
        </button>
        <button type="button" class="st__btn st__btn--pair" :aria-pressed="by === 'apertus'" @click="emit('by', 'apertus')">
          <span class="st__n"><CountUp :value="byApertus" :format="fmt" /></span>
          <span class="st__unit">{{ t('source.apertus') }}</span>
        </button>
      </div>
      <span class="st__ratio" aria-hidden="true">
        <span class="st__ratio-code m-grow" style="--i: 3" :style="{ width: `${codeShare * 100}%` }" />
      </span>
    </div>

    <div v-if="cta" class="st__cta m-rise" style="--i: 2">
      <button type="button" class="btn btn--primary press st__start" @click="emit('start')">
        {{ cta }}<ArrowRight :size="16" aria-hidden="true" class="st__arrow" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.st {
  display: grid;
  grid-template-columns: minmax(180px, 1.3fr) minmax(110px, 0.8fr) minmax(200px, 1.4fr) auto;
  align-items: stretch;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}
.st__cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
  padding: var(--s-4) var(--s-5);
}
.st__cell + .st__cell {
  border-left: 1px solid var(--line);
}
.st__cell--lead {
  padding-left: 0;
}
.st__label {
  font-size: var(--fs-14);
  font-weight: 500;
  color: var(--muted);
}
.st__n {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 2.25rem;
  line-height: 1;
  font-weight: 680;
  letter-spacing: -0.035em;
  font-variant-numeric: tabular-nums;
  color: var(--ink);
}
.st__foot {
  display: flex;
  align-items: center;
  gap: var(--s-3);
  margin-top: auto;
  padding-top: 4px;
}
.st__track {
  display: block;
  flex: 1 1 auto;
  max-width: 180px;
  height: 4px;
  background: var(--surface-3);
  border-radius: 2px;
  overflow: hidden;
}
.st__grow {
  display: block;
  height: 100%;
}
.st__fill {
  display: block;
  height: 100%;
  background: var(--green);
  transform-origin: left;
  transition: transform var(--dur-4) var(--ease-out);
}
.st__sub {
  font-size: var(--fs-12);
  color: var(--muted);
  white-space: nowrap;
}

/* Clickable numbers: a quiet hover, a clear pressed state. */
.st__btn {
  align-items: flex-start;
  border: 0;
  background: transparent;
  text-align: left;
  color: inherit;
  transition: background-color var(--dur-1) var(--ease-out), box-shadow var(--dur-1) var(--ease-out);
}
.st__btn:hover {
  background: var(--surface-2);
}
.st__btn:focus-visible {
  outline-offset: -2px;
}
.st__btn[aria-pressed='true'] {
  background: var(--surface-2);
  box-shadow: inset 0 -2px 0 var(--ink);
}
.st__cell--by {
  gap: 6px;
}
.st__pair {
  display: flex;
  gap: 4px;
  margin-left: -10px;
}
.st__btn--pair {
  display: inline-flex;
  flex-direction: row;
  align-items: baseline;
  gap: 8px;
  padding: 2px 10px 4px;
  border-radius: var(--r-control);
}
.st__unit {
  font-size: var(--fs-14);
  font-weight: 600;
  color: var(--muted);
}
.st__btn--pair[aria-pressed='true'] .st__unit {
  color: var(--ink);
}
.st__ratio {
  display: flex;
  height: 4px;
  max-width: 220px;
  margin-top: auto;
  border-radius: 2px;
  background: var(--blue);
  overflow: hidden;
}
.st__ratio-code {
  display: block;
  height: 100%;
  background: var(--fill-rule);
}
.st__cta {
  display: flex;
  align-items: center;
  padding-left: var(--s-5);
}
.st__start {
  gap: 10px;
}
.st__arrow {
  transition: transform var(--dur-2) var(--ease-out);
}
.st__start:hover .st__arrow {
  transform: translateX(3px);
}

@media (max-width: 900px) {
  .st {
    grid-template-columns: minmax(0, auto) minmax(0, 1fr);
  }
  .st__cell--lead {
    grid-column: 1 / -1;
    padding: var(--s-4) 0;
    border-bottom: 1px solid var(--line);
  }
  .st__cell--failed.st__cell {
    border-left: 0;
    margin-left: -8px;
    padding-left: 8px;
  }
  .st__cta {
    grid-column: 1 / -1;
    padding: var(--s-4) 0;
    border-top: 1px solid var(--line);
  }
  .st__start {
    width: 100%;
  }
}
@media (max-width: 420px) {
  .st__n {
    font-size: 1.875rem;
  }
  .st__cell--failed.st__cell {
    padding-right: var(--s-4);
  }
  .st__cell--by {
    padding-left: var(--s-4);
    padding-right: 0;
  }
  .st__pair {
    flex-wrap: wrap;
    gap: 0;
  }
}
@media (forced-colors: active) {
  .st__btn[aria-pressed='true'] {
    outline: 2px solid Highlight;
  }
  .st__fill,
  .st__ratio-code {
    forced-color-adjust: none;
    background: CanvasText;
  }
}
</style>
