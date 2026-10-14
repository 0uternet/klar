<script setup lang="ts">
import { computed, ref, useId } from 'vue'
import { Check, ChevronDown, X } from '@lucide/vue'
import type { Finding, Status, UiLang } from '@/types'
import { polish, t, tp } from '@/i18n'
import { pagePath } from '@/lib/format'
import { evidenceLine, rowTitle } from '@/lib/finding-text'
import { isNote } from '@/lib/group'
import VerdictChip from './VerdictChip.vue'
import StatusBadge from './StatusBadge.vue'

/**
 * One row of the report (UX-3): a title that tells rows apart (the reason for
 * notes, the rule for axe-core, else the impact), then the evidence itself on one
 * line. The page path only shows when the check covered several pages.
 * Identical findings come as one row with "×N"; the places can be expanded and
 * decided one by one.
 */
const props = defineProps<{
  finding: Finding
  items?: Finding[]
  selected?: boolean
  scanLang: UiLang
  base?: string
  /** The scan covered more than one page: show where each row is. */
  multiPage?: boolean
  panelId?: string
  busy?: boolean
}>()
const emit = defineEmits<{ open: [finding: Finding]; decideOne: [finding: Finding, status: Exclude<Status, 'to_review'>] }>()

const all = computed(() => props.items ?? [props.finding])
const count = computed(() => all.value.length)
const title = computed(() => rowTitle(props.finding, props.scanLang))
const evidence = computed(() => evidenceLine(props.finding))
const path = computed(() => pagePath(props.finding.page_url, props.base))
const aggregate = computed<Status | null>(() => {
  const first = all.value[0]!.status
  return all.value.every((f) => f.status === first) ? first : null
})
const reviewed = computed(() => all.value.filter((f) => f.status !== 'to_review').length)
const pages = computed(() => new Set(all.value.map((f) => pagePath(f.page_url, props.base))).size)

/** UX-35: the list only flags low confidence (notes are low by nature: their title says why). */
const showLow = computed(() => props.finding.confidence === 'low' && !isNote(props.finding))

const expanded = ref(false)
const listId = useId()
</script>

<template>
  <div class="fcw" :class="{ 'is-selected': selected, [`fcw--${aggregate ?? 'mixed'}`]: true }">
    <button
      type="button"
      class="fc"
      :aria-current="selected ? 'true' : undefined"
      :aria-controls="panelId"
      :data-finding="finding.id"
      @click="emit('open', finding)"
    >
      <span class="fc__verdict"><VerdictChip :outcome="finding.outcome" size="sm" /></span>
      <span class="fc__main">
        <span class="fc__impact" :lang="title.lang ?? undefined">
          {{ title.lang ? polish(title.text, title.lang) : title.text }}
          <span v-if="count > 1" class="fc__count tabular">×{{ count }}<span class="sr-only">, {{ tp('group.places', count) }}</span></span>
        </span>
        <span v-if="evidence" class="fc__evidence mono" :lang="finding.content_lang ?? undefined" translate="no">{{ evidence }}</span>
        <span class="fc__meta">
          <template v-if="multiPage">
            <span class="mono fc__path">{{ count > 1 && pages > 1 ? tp('group.places', count) : path }}</span>
            <span aria-hidden="true">·</span>
          </template>
          <span>{{ t(`source.${finding.source}`) }}</span>
          <template v-if="showLow">
            <span aria-hidden="true">·</span>
            <span>{{ t('confidence.lowText') }}</span>
          </template>
        </span>
      </span>
      <span class="fc__side">
        <StatusBadge v-if="aggregate" :status="aggregate" />
        <span v-else class="fc__mixed tabular">{{ t('group.reviewed', { done: reviewed, n: count }) }}</span>
      </span>
    </button>

    <div v-if="count > 1" class="fcg">
      <button type="button" class="fcg__toggle" :aria-expanded="expanded" :aria-controls="listId" @click="expanded = !expanded">
        <ChevronDown :size="16" aria-hidden="true" class="fcg__chev" :class="{ 'is-open': expanded }" />
        {{ expanded ? t('group.hide') : t('group.show', { n: count }) }}
      </button>
      <ol v-show="expanded" :id="listId" class="fcg__list">
        <li v-for="(f, i) in all" :key="f.id" class="fcg__item">
          <span class="fcg__where">
            <span v-if="evidenceLine(f)" class="mono fcg__quote" :lang="f.content_lang ?? undefined" translate="no">{{ evidenceLine(f, 100) }}</span>
            <span v-if="multiPage" class="mono">{{ pagePath(f.page_url, base) }}</span>
            <code class="fcg__sel" translate="no">{{ f.selector }}</code>
          </span>
          <StatusBadge :status="f.status" />
          <span class="fcg__actions">
            <button
              type="button"
              class="btn btn--ghost btn--sm"
              :aria-pressed="f.status === 'rejected'"
              :aria-label="t('group.rejectOne', { i: i + 1 })"
              :disabled="busy"
              @click="emit('decideOne', f, 'rejected')"
            >
              <X :size="14" aria-hidden="true" />{{ t('finding.reject') }}
            </button>
            <button
              type="button"
              class="btn btn--secondary btn--sm"
              :aria-pressed="f.status === 'accepted'"
              :aria-label="t('group.acceptOne', { i: i + 1 })"
              :disabled="busy"
              @click="emit('decideOne', f, 'accepted')"
            >
              <Check :size="14" aria-hidden="true" />{{ t('finding.accept') }}
            </button>
          </span>
        </li>
      </ol>
    </div>
  </div>
</template>

<style scoped>
.fcw {
  background: var(--surface);
  border-left: 3px solid transparent;
  transition: background-color var(--dur-1) var(--ease), border-color var(--dur-1) var(--ease);
}
.fcw.is-selected {
  background: var(--surface-2);
  border-left-color: var(--klar-red);
}
.fc {
  display: grid;
  grid-template-columns: 9.5rem minmax(0, 1fr) auto;
  align-items: start;
  gap: var(--s-4);
  width: 100%;
  padding: 14px var(--s-4);
  background: transparent;
  border: 0;
  text-align: left;
  color: var(--ink);
}
.fc:hover {
  background: var(--surface-2);
}
.fc:focus-visible {
  outline-offset: -2px;
}
.fc__verdict {
  padding-top: 1px;
}
.fc__main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}
.fc__impact {
  font-size: var(--fs-16);
  font-weight: 500;
  line-height: 1.4;
  text-wrap: pretty;
}
.fcw--rejected .fc__impact {
  color: var(--muted);
  text-decoration: line-through;
  text-decoration-color: var(--control-border);
}
.fc__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  column-gap: 8px;
  font-size: var(--fs-12);
  color: var(--muted);
  min-width: 0;
}
.fc__meta .mono {
  font-size: var(--fs-12);
}
.fc__evidence {
  display: block;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  font-size: var(--fs-12);
  color: var(--ink);
}
.fcg__quote {
  font-size: var(--fs-12);
  overflow-wrap: anywhere;
}
.fc__count {
  display: inline-block;
  margin-left: 6px;
  vertical-align: 1px;
  font-size: var(--fs-12);
  padding: 0 7px;
  border-radius: var(--r-pill);
  background: var(--ink);
  color: var(--on-ink);
  font-weight: 700;
  line-height: 18px;
}
.fc__side {
  display: flex;
  align-items: center;
  gap: var(--s-4);
  padding-top: 2px;
}
.fc__mixed {
  font-size: var(--fs-14);
  color: var(--muted);
  white-space: nowrap;
}
.fcg {
  padding: 0 var(--s-4) 10px calc(9.5rem + 2 * var(--s-4));
}
.fcg__toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 0 8px;
  margin-left: -8px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--blue);
  font-size: var(--fs-14);
  font-weight: 600;
}
.fcg__toggle:hover {
  background: var(--blue-tint);
}
.fcg__chev {
  transition: transform var(--dur-1) var(--ease);
}
.fcg__chev.is-open {
  transform: rotate(180deg);
}
.fcg__list {
  margin: 6px 0 4px;
  padding: 0;
  list-style: none;
  border-top: 1px solid var(--line);
}
.fcg__item {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  align-items: center;
  gap: var(--s-3);
  padding: 8px 0;
  border-bottom: 1px solid var(--line);
  font-size: var(--fs-14);
}
.fcg__where {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.fcg__where .mono {
  font-size: var(--fs-12);
}
.fcg__sel {
  font-size: var(--fs-12);
  color: var(--muted);
  overflow-wrap: anywhere;
}
.fcg__actions {
  display: flex;
  gap: 4px;
}
.fcg__actions .btn {
  --btn-h: 32px;
  gap: 4px;
}
.fcg__actions .btn[aria-pressed='true'] {
  border-color: var(--ink);
  box-shadow: inset 0 0 0 1px var(--ink);
}
@media (max-width: 720px) {
  .fc {
    grid-template-columns: 1fr;
    gap: var(--s-2);
  }
  .fc__side {
    gap: var(--s-3);
  }
  .fcg {
    padding-left: var(--s-4);
  }
  .fcg__item {
    grid-template-columns: 1fr;
    gap: var(--s-2);
  }
}
</style>
