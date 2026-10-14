<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import type { CoverageKind, Finding, Scan } from '@/types'
import { COVERAGE_KINDS } from '@/types'
import { CRITERIA, PRINCIPLES, type WcagCriterion } from '@/data/wcag'
import { formatNumber, locale, t } from '@/i18n'
import { cellStatus, criteriaInfo, type CellStatus } from '@/stores/criteria'
import ShapeIcon from './ShapeIcon.vue'

/**
 * 50 cells, one per WCAG 2.1 AA criterion, grouped by principle.
 * Fill = how Klar. checks it, taken from the backend registry (GET /api/criteria):
 * a criterion without a check module is shown as "Not implemented", never as covered.
 * Underline = evaluated on the test set (only when the backend says so).
 * Marker = what this scan found. Keyboard: one tab stop, arrow keys move between
 * cells (roving tabindex), Enter filters the findings.
 */
const props = defineProps<{ scan?: Scan | null; findings: Finding[]; selected?: string | null; interactive?: boolean }>()
const emit = defineEmits<{ select: [code: string] }>()

const statuses = computed(() => {
  // Recompute when the registry arrives.
  void criteriaInfo.value
  return new Map<string, CellStatus>(CRITERIA.map((c) => [c.code, cellStatus(c.code, props.scan)]))
})
const kind = (code: string): CoverageKind => statuses.value.get(code)?.kind ?? 'unknown'
const evaluated = (code: string): boolean => statuses.value.get(code)?.evaluated ?? false
/**
 * A criterion Klar. does not pre-check (planned, human or unknown) never shows a
 * failure marker, even when axe-core rules hit it: it gets a neutral "flagged by
 * automatic rules" marker instead, without claiming coverage (UX-7/UX-16).
 */
const prechecks = (code: string): boolean => !['planned', 'human', 'unknown'].includes(kind(code))
const ruleHits = (code: string): number => {
  const s = stats.value.get(code)
  return s ? s.failed + s.review : 0
}
const anyRuleHits = computed(() => CRITERIA.some((c) => !prechecks(c.code) && ruleHits(c.code) > 0))
const unavailable = computed(() => CRITERIA.every((c) => kind(c.code) === 'unknown'))
const anyEvaluated = computed(() => CRITERIA.some((c) => evaluated(c.code)))

const stats = computed(() => {
  const m = new Map<string, { failed: number; review: number; passed: number; total: number }>()
  for (const f of props.findings) {
    const s = m.get(f.criterion) ?? { failed: 0, review: 0, passed: 0, total: 0 }
    s.total++
    if (f.outcome === 'failed') s.failed++
    else if (f.outcome === 'cantTell') s.review++
    else if (f.outcome === 'passed') s.passed++
    m.set(f.criterion, s)
  }
  return m
})

const groups = computed(() => PRINCIPLES.map((p) => ({ p, items: CRITERIA.filter((c) => c.principle === p) })))
const flat = computed(() => groups.value.flatMap((g) => g.items))
const counts = computed(() => {
  const c = Object.fromEntries([...COVERAGE_KINDS, 'unknown'].map((m) => [m, 0])) as Record<CoverageKind, number>
  for (const k of CRITERIA) c[kind(k.code)]++
  return c
})
const legend = computed(() => COVERAGE_KINDS.filter((k) => counts.value[k] > 0))

const active = ref(0)
const hovered = ref<WcagCriterion | null>(null)
const cells = ref<HTMLButtonElement[]>([])
const inspect = computed(() => hovered.value ?? null)

function kindLabel(code: string): string {
  const k = kind(code)
  const base = t(`method.${k}`)
  if (k === 'human' || k === 'planned' || k === 'unknown') return base
  return evaluated(code) ? `${base} · ${t('coverage.evaluated')}` : `${base} · ${t('coverage.notEvaluated')}`
}

function describe(c: WcagCriterion): string {
  const s = stats.value.get(c.code)
  const base = t('coverage.cell', { code: c.code, name: c.plain[locale.value], level: c.level, method: kindLabel(c.code) })
  if (!s) return `${base} ${t('coverage.noFindingsTip')}.`
  if (!prechecks(c.code)) return ruleHits(c.code) ? `${base} ${t('coverage.ruleHits', { n: ruleHits(c.code) })}` : `${base} ${t('coverage.noFindingsTip')}.`
  return `${base} ${t('coverage.findings', { failed: s.failed, review: s.review, passed: s.passed })}`
}

async function focusCell(i: number) {
  active.value = Math.max(0, Math.min(flat.value.length - 1, i))
  await nextTick()
  cells.value[active.value]?.focus()
}

function onKey(e: KeyboardEvent, i: number) {
  const c = flat.value[i]!
  const gi = groups.value.findIndex((g) => g.p === c.principle)
  const offset = groups.value[gi]!.items.indexOf(c)
  const startOf = (g: number) => groups.value.slice(0, g).reduce((n, x) => n + x.items.length, 0)
  switch (e.key) {
    case 'ArrowRight':
      void focusCell(i + 1)
      break
    case 'ArrowLeft':
      void focusCell(i - 1)
      break
    case 'ArrowDown':
      if (gi < groups.value.length - 1) void focusCell(startOf(gi + 1) + Math.min(offset, groups.value[gi + 1]!.items.length - 1))
      break
    case 'ArrowUp':
      if (gi > 0) void focusCell(startOf(gi - 1) + Math.min(offset, groups.value[gi - 1]!.items.length - 1))
      break
    case 'Home':
      void focusCell(0)
      break
    case 'End':
      void focusCell(flat.value.length - 1)
      break
    default:
      return
  }
  e.preventDefault()
}

function indexOf(c: WcagCriterion) {
  return flat.value.indexOf(c)
}
</script>

<template>
  <div class="cov">
    <p v-if="unavailable" class="cov__unavailable">{{ t('coverage.unavailable') }}</p>
    <div class="cov__legend" :aria-label="t('coverage.legend')" role="group">
      <span v-for="m in legend" :key="m" class="cov__key">
        <span class="tile tile--sm" :class="`tile--${m}`" aria-hidden="true" />
        <span class="cov__key-label">{{ t(`method.${m}`) }}</span>
        <span class="cov__key-n tabular">{{ formatNumber(counts[m]) }}</span>
      </span>
      <span v-if="anyEvaluated" class="cov__key">
        <span class="cov__eval-sample mono" aria-hidden="true">2.4.4</span>
        <span class="cov__key-label">{{ t('coverage.evaluated') }}</span>
      </span>
      <span class="cov__key cov__key--marker">
        <ShapeIcon shape="square" color="var(--klar-red)" :size="9" />
        <span class="cov__key-label">{{ t('coverage.marker.failed') }}</span>
      </span>
      <span class="cov__key cov__key--marker">
        <ShapeIcon shape="diamond" color="var(--amber)" :size="9" />
        <span class="cov__key-label">{{ t('coverage.marker.review') }}</span>
      </span>
      <span v-if="anyRuleHits" class="cov__key cov__key--marker">
        <ShapeIcon shape="ring" color="var(--grey-shape)" :size="9" />
        <span class="cov__key-label">{{ t('coverage.marker.rules') }}</span>
      </span>
    </div>

    <div class="cov__grid" role="group" :aria-label="t('coverage.label')">
      <div v-for="g in groups" :key="g.p" class="cov__row">
        <p class="cov__principle">
          <span class="mono">{{ g.p }}</span> {{ t(`principle.${g.p}`) }}
        </p>
        <div class="cov__cells">
          <button
            v-for="c in g.items"
            :key="c.code"
            :ref="(el) => { if (el) cells[indexOf(c)] = el as HTMLButtonElement }"
            type="button"
            class="cell"
            :class="{ 'is-selected': selected === c.code, 'has-findings': stats.has(c.code), 'is-planned': kind(c.code) === 'planned' }"
            :tabindex="indexOf(c) === active ? 0 : -1"
            :aria-label="describe(c)"
            :aria-pressed="interactive && stats.has(c.code) ? selected === c.code : undefined"
            :aria-disabled="interactive && !stats.has(c.code) ? 'true' : undefined"
            @click="interactive && stats.has(c.code) && emit('select', c.code)"
            @keydown="onKey($event, indexOf(c))"
            @focus="(active = indexOf(c)), (hovered = c)"
            @mouseenter="hovered = c"
            @mouseleave="hovered = null"
            @blur="hovered = null"
          >
            <span class="tile" :class="`tile--${kind(c.code)}`" aria-hidden="true">
              <template v-if="prechecks(c.code)">
                <span v-if="stats.get(c.code)?.failed" class="cell__marker">
                  <ShapeIcon shape="square" color="var(--klar-red)" :size="9" />
                </span>
                <span v-else-if="stats.get(c.code)?.review" class="cell__marker">
                  <ShapeIcon shape="diamond" color="var(--amber)" :size="9" />
                </span>
              </template>
              <span v-else-if="ruleHits(c.code)" class="cell__marker">
                <ShapeIcon shape="ring" color="var(--grey-shape)" :size="9" />
              </span>
            </span>
            <span class="cell__code mono" :class="{ 'is-evaluated': evaluated(c.code) }" aria-hidden="true">{{ c.code }}</span>
          </button>
        </div>
      </div>
    </div>

    <p class="cov__inspect" aria-hidden="true">
      <template v-if="inspect">
        <span class="mono cov__inspect-code">{{ inspect.code }}</span>
        <strong>{{ inspect.plain[locale] }}</strong>
        <span class="muted" lang="en">{{ inspect.title }}</span>
        <span class="muted">· {{ inspect.level }} · {{ kindLabel(inspect.code) }}</span>
        <span v-if="!stats.get(inspect.code)" class="cov__inspect-n">· {{ t('coverage.noFindingsTip') }}</span>
        <span v-else-if="!prechecks(inspect.code)" class="cov__inspect-n">· {{ ruleHits(inspect.code) ? t('coverage.ruleHits', { n: ruleHits(inspect.code) }) : t('coverage.noFindingsTip') }}</span>
        <span v-else class="cov__inspect-n">
          · {{ t('coverage.findings', { failed: stats.get(inspect.code)!.failed, review: stats.get(inspect.code)!.review, passed: stats.get(inspect.code)!.passed }) }}
        </span>
      </template>
      <span v-else class="muted">{{ t('coverage.hint') }}</span>
    </p>
  </div>
</template>

<style scoped>
.cov {
  display: flex;
  flex-direction: column;
  gap: var(--s-5);
}
.cov__legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--s-2) var(--s-5);
  font-size: var(--fs-14);
}
.cov__key {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.cov__key-n {
  color: var(--muted);
  font-family: var(--font-mono);
  font-size: var(--fs-12);
}
.cov__key--marker .cov__key-label {
  color: var(--muted);
}
.cov__grid {
  display: flex;
  flex-direction: column;
  gap: var(--s-4);
}
.cov__row {
  display: grid;
  grid-template-columns: 9.5rem 1fr;
  gap: var(--s-4);
  align-items: start;
  padding-top: var(--s-4);
  border-top: 1px solid var(--line);
}
.cov__principle {
  padding-top: 4px;
  font-size: var(--fs-14);
  font-weight: 600;
}
.cov__principle .mono {
  color: var(--muted);
  margin-right: 4px;
}
.cov__cells {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 4px;
}
.cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
  width: 47px;
  padding: 4px 0 2px;
  background: transparent;
  border: 0;
  border-radius: 6px;
  color: var(--ink);
  cursor: default;
}
.cell.has-findings {
  cursor: pointer;
}
.cell:hover {
  background: var(--surface-2);
}
.cell:focus-visible {
  outline-offset: 0;
}
.cell.is-selected {
  background: var(--surface-3);
  box-shadow: inset 0 -2px 0 var(--klar-red);
}
.cell__code {
  font-size: var(--fs-12);
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.tile {
  position: relative;
  display: block;
  width: 40px;
  height: 26px;
  border-radius: 3px;
  border: 1.5px solid transparent;
}
.tile--sm {
  width: 22px;
  height: 14px;
  border-radius: 2px;
}
.tile--apertus_text {
  background: var(--ink);
  border-color: var(--ink);
}
.tile--apertus_vision {
  border-color: var(--ink);
  background: repeating-linear-gradient(135deg, var(--ink) 0 2px, transparent 2px 5px);
}
.tile--rule {
  background: var(--fill-rule);
  border-color: var(--fill-rule);
}
.tile--experimental {
  border: 1.5px dashed var(--ink);
  background: radial-gradient(circle, var(--ink) 1px, transparent 1.4px) 0 0 / 6px 6px;
}
.tile--planned {
  border: 1.5px dashed var(--control-border);
  background: transparent;
}
.tile--unknown {
  border: 1.5px dotted var(--control-border);
  background: transparent;
}
.cell.is-planned .cell__code {
  color: var(--muted);
}
.cell__code.is-evaluated,
.cov__eval-sample {
  text-decoration: underline;
  text-decoration-thickness: 2px;
  text-underline-offset: 3px;
  text-decoration-color: var(--green);
}
.cov__eval-sample {
  font-size: var(--fs-12);
}
.cov__unavailable {
  padding: var(--s-3) var(--s-4);
  background: var(--amber-tint);
  border-radius: var(--r-control);
  font-size: var(--fs-14);
}
.tile--human {
  border-color: var(--ink);
  background: var(--surface);
}
.cell__marker {
  position: absolute;
  right: -5px;
  top: -5px;
  display: grid;
  place-items: center;
  width: 15px;
  height: 15px;
  background: var(--surface);
  border-radius: 50%;
}
.cov__inspect {
  min-height: 1.5em;
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  column-gap: 8px;
  font-size: var(--fs-14);
}
.cov__inspect-code {
  font-weight: 700;
}
@media (max-width: 720px) {
  .cov__row {
    grid-template-columns: 1fr;
    gap: var(--s-2);
  }
}
@media (forced-colors: active) {
  .tile--apertus_text,
  .tile--rule {
    forced-color-adjust: none;
    background: CanvasText;
  }
  .cell.is-selected {
    outline: 2px solid Highlight;
  }
}
</style>
