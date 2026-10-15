<script setup lang="ts">
import { computed, useId } from 'vue'
import type { Finding, Status, UiLang } from '@/types'
import { polish, t, tp } from '@/i18n'
import { pagePath } from '@/lib/format'
import { evidenceLine, rowTitle } from '@/lib/finding-text'
import VerdictChip from './VerdictChip.vue'
import StatusBadge from './StatusBadge.vue'
import KeyboardHint from './KeyboardHint.vue'

/**
 * One row of the report (UX-3): verdict, a sentence that tells rows apart, and the quoted
 * element on one line. The criterion is the section heading, so the row does not repeat it.
 * Identical findings come as one row with "×N"; the places are listed in the finding panel.
 * Accept and reject sit on the right, revealed on hover and focus (A and R work too).
 */
const props = defineProps<{
  finding: Finding
  items?: Finding[]
  /** Group key of the row: focus is restored by it when rows change. */
  rowKey: string
  selected?: boolean
  scanLang: UiLang
  base?: string
  /** The scan covered more than one page: show where each row is. */
  multiPage?: boolean
  panelId?: string
}>()
const emit = defineEmits<{ open: [finding: Finding]; decide: [status: Exclude<Status, 'to_review'>] }>()

const all = computed(() => props.items ?? [props.finding])
const count = computed(() => all.value.length)
const title = computed(() => rowTitle(props.finding, props.scanLang))
const evidence = computed(() => evidenceLine(props.finding, 120))
const path = computed(() => pagePath(props.finding.page_url, props.base))
const pages = computed(() => new Set(all.value.map((f) => pagePath(f.page_url, props.base))).size)
/** Aggregate decision of the row (null when the places differ). */
const aggregate = computed<Status | null>(() => {
  const first = all.value[0]!.status
  return all.value.every((f) => f.status === first) ? first : null
})
const reviewed = computed(() => all.value.filter((f) => f.status !== 'to_review').length)
const titleId = useId()
</script>

<template>
  <div class="row" :class="[`row--${aggregate ?? 'mixed'}`, { 'is-selected': selected }]" :data-row="rowKey">
    <button
      type="button"
      class="row__open"
      :aria-current="selected ? 'true' : undefined"
      :aria-controls="panelId"
      :data-finding="finding.id"
      @click="emit('open', finding)"
    >
      <span class="row__verdict"><VerdictChip :outcome="finding.outcome" size="sm" /></span>
      <span class="row__main">
        <span :id="titleId" class="row__title" :lang="title.lang ?? undefined">{{ title.lang ? polish(title.text, title.lang) : title.text }}</span>
        <span class="row__sub">
          <span v-if="evidence" class="row__quote mono" :lang="finding.content_lang ?? undefined" translate="no">{{ evidence }}</span>
          <span v-if="count > 1" class="row__tag tabular">×{{ count }}<span class="sr-only">, {{ tp('group.places', count) }}</span></span>
          <span v-if="finding.source === 'apertus'" class="row__tag row__tag--apertus">{{ t('source.apertus') }}</span>
          <span v-if="multiPage" class="row__path mono">{{ count > 1 && pages > 1 ? tp('group.places', count) : path }}</span>
        </span>
      </span>
      <span class="row__status">
        <StatusBadge v-if="aggregate && aggregate !== 'to_review'" :status="aggregate" />
        <span v-else-if="!aggregate" class="row__mixed tabular">{{ t('group.reviewed', { done: reviewed, n: count }) }}</span>
      </span>
    </button>
    <span class="row__actions">
      <button
        type="button"
        class="row__act row__act--reject"
        :aria-pressed="aggregate === 'rejected'"
        :aria-describedby="titleId"
        :title="t('finding.reject')"
        @click="emit('decide', 'rejected')"
      >
        <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false"><path d="M4.5 4.5l7 7M11.5 4.5l-7 7" /></svg>
        <span class="sr-only">{{ t('finding.reject') }}</span>
        <KeyboardHint :keys="['R']" />
      </button>
      <button
        type="button"
        class="row__act row__act--accept"
        :aria-pressed="aggregate === 'accepted'"
        :aria-describedby="titleId"
        :title="t('finding.accept')"
        @click="emit('decide', 'accepted')"
      >
        <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false"><path d="M3.5 8.4l3 3 6-6.4" /></svg>
        <span class="sr-only">{{ t('finding.accept') }}</span>
        <KeyboardHint :keys="['A']" />
      </button>
    </span>
  </div>
</template>

<style scoped>
.row {
  position: relative;
  background: var(--bg);
  transition: background-color var(--dur-1) var(--ease-out);
}
.row::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 2px;
  border-radius: 2px;
  background: var(--klar-red);
  transform: scaleY(0);
  transition: transform var(--dur-2) var(--ease-out);
}
.row:hover {
  background: var(--surface-2);
}
.row.is-selected {
  background: var(--surface-2);
}
.row.is-selected::before {
  transform: scaleY(1);
}
.row__open {
  display: grid;
  grid-template-columns: 7.25rem minmax(0, 1fr) 7rem;
  align-items: start;
  gap: var(--s-4);
  width: 100%;
  padding: 12px var(--s-3) 12px var(--s-4);
  background: transparent;
  border: 0;
  border-radius: 0;
  text-align: left;
  color: var(--ink);
}
.row__open:focus-visible {
  outline-offset: -2px;
  border-radius: 6px;
}
.row__verdict {
  padding-top: 1px;
}
.row__main {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}
.row__title {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
  font-size: 0.9375rem;
  font-weight: 550;
  line-height: 1.45;
  letter-spacing: -0.006em;
  text-wrap: pretty;
}
.row--rejected .row__title {
  color: var(--muted);
  text-decoration: line-through;
  text-decoration-color: var(--control-border);
  text-decoration-thickness: 1px;
}
.row__sub {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  font-size: var(--fs-12);
  color: var(--muted);
}
.row__quote {
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: var(--fs-12);
  color: var(--muted);
}
.row__tag {
  flex: none;
  padding: 0 6px;
  border: 1px solid var(--line);
  border-radius: 5px;
  font-size: 0.6875rem;
  font-weight: 650;
  line-height: 17px;
  color: var(--ink);
}
.row__tag--apertus {
  border-color: transparent;
  background: var(--blue-tint);
  color: var(--blue);
}
.row__path {
  flex: none;
  font-size: var(--fs-12);
}
.row__status {
  display: flex;
  justify-content: flex-end;
  padding-top: 2px;
  transition: opacity var(--dur-1) var(--ease-out);
}
.row__mixed {
  font-size: var(--fs-12);
  color: var(--muted);
  white-space: nowrap;
}

/* Quick decisions, on the right: shown on hover and while the row has focus. */
.row__actions {
  position: absolute;
  top: 9px;
  right: var(--s-3);
  display: flex;
  gap: 4px;
  opacity: 0;
  transform: translateX(4px);
  pointer-events: none;
  transition: opacity var(--dur-1) var(--ease-out), transform var(--dur-2) var(--ease-out);
}
@media (hover: hover) {
  .row:hover .row__actions {
    opacity: 1;
    transform: none;
    pointer-events: auto;
  }
  .row:hover .row__status {
    opacity: 0;
  }
}
.row:focus-within .row__actions {
  opacity: 1;
  transform: none;
  pointer-events: auto;
}
.row:focus-within .row__status {
  opacity: 0;
}
.row__act {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-width: 34px;
  height: 30px;
  padding: 0 8px;
  border: 1px solid var(--control-border);
  border-radius: 7px;
  background: var(--surface);
  color: var(--ink);
  transition: background-color var(--dur-1) var(--ease-out), border-color var(--dur-1) var(--ease-out), color var(--dur-1) var(--ease-out),
    transform var(--dur-1) var(--ease-out);
}
.row__act svg {
  fill: none;
  stroke: currentColor;
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.row__act:active {
  transform: scale(0.94);
}
.row__act--accept:hover,
.row__act--accept[aria-pressed='true'] {
  background: var(--green-tint);
  border-color: var(--green);
  color: var(--green);
}
.row__act--reject:hover,
.row__act--reject[aria-pressed='true'] {
  background: var(--surface-3);
  border-color: var(--ink);
}
.row__act :deep(kbd) {
  height: 1.4em;
  min-width: 1.4em;
  font-size: 0.6875rem;
  border-bottom-width: 1px;
}
/* A and R act on the row that has focus, so the key hints show only then (not on hover). */
.row:not(:focus-within) .row__act :deep(.kh) {
  display: none;
}
@media (max-width: 720px) {
  .row__open {
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 6px var(--s-3);
  }
  .row__verdict {
    grid-column: 1;
    grid-row: 1;
  }
  .row__status {
    grid-column: 2;
    grid-row: 1;
  }
  .row__main {
    grid-column: 1 / -1;
  }
  .row__actions {
    top: 8px;
  }
}
@media (hover: none) {
  .row__actions {
    display: none;
  }
  .row:focus-within .row__status {
    opacity: 1;
  }
}
@media (forced-colors: active) {
  .row.is-selected {
    outline: 2px solid Highlight;
    outline-offset: -2px;
  }
}
</style>
