<script setup lang="ts">
import { formatNumber, t, tp, type MessageKey, type PluralBase } from '@/i18n'
import type { RunNote } from '@/lib/notes'
import ShapeIcon from './ShapeIcon.vue'

/**
 * "About this run" (UX-2): what this run could not do. Calm plain rows: a shape (the tone),
 * one sentence, and one way forward as a text link. No boxes: the warning lives in the icon.
 */
defineProps<{ notes: RunNote[]; label?: string }>()
const emit = defineEmits<{ demo: []; rerun: []; filter: [reason: string] }>()

function params(p: Record<string, string | number>) {
  return Object.fromEntries(Object.entries(p).map(([k, v]) => [k, typeof v === 'number' ? formatNumber(v) : v]))
}
const reasonTitle = (code: string) => t(`reason.${code}` as MessageKey)
function message(n: RunNote): string {
  return n.count !== undefined ? tp(n.text as PluralBase, n.count, params(n.params)) : t(n.text as MessageKey, params(n.params))
}
</script>

<template>
  <ul class="notes" role="list" :aria-label="label ?? t('notes.title')">
    <li v-for="n in notes" :key="n.id" class="note" :class="`note--${n.tone}`" :data-note="n.id">
      <ShapeIcon :shape="n.tone === 'warning' ? 'diamond' : 'circle'" :color="n.tone === 'warning' ? 'var(--amber)' : 'var(--grey-shape)'" :size="9" />
      <div class="note__body">
        <p class="note__text">
          <strong v-if="n.title" class="note__strong">{{ t(n.title) }}. </strong>{{ message(n) }}
          <template v-for="(a, i) in n.actions" :key="i">
            {{ ' ' }}<span v-if="i > 0" class="note__sep" aria-hidden="true">·{{ ' ' }}</span
            ><button v-if="a.kind === 'demo'" type="button" class="note__link" @click="emit('demo')">{{ t('home.demo.primary') }}</button>
            <button v-else-if="a.kind === 'rerun'" type="button" class="note__link" @click="emit('rerun')">{{ t('scan.rerun') }}</button>
            <button v-else-if="a.kind === 'runAgain'" type="button" class="note__link" @click="emit('rerun')">{{ t('notes.runAgain') }}</button>
            <button
              v-else-if="a.kind === 'filter'"
              type="button"
              class="note__link"
              :aria-label="`${t('notes.show')}: ${reasonTitle(a.reason)}`"
              @click="emit('filter', a.reason)"
            >
              {{ t('notes.show') }}
            </button>
            <RouterLink v-else-if="a.kind === 'connect'" class="note__link" :to="{ name: 'about', hash: '#connect' }">{{ t('replay.connectShort') }}</RouterLink>
            <RouterLink v-else class="note__link" :to="{ name: 'about', hash: '#connect' }">{{ t('notes.checkConnection') }}</RouterLink>
          </template>
        </p>
        <details v-if="n.details" class="note__details">
          <summary>{{ t('error.details') }}</summary>
          <pre class="mono" translate="no">{{ n.details }}</pre>
        </details>
      </div>
    </li>
  </ul>
</template>

<style scoped>
.notes {
  display: flex;
  flex-direction: column;
  gap: var(--s-3);
  margin: 0;
  padding: 0;
}
.note {
  display: grid;
  grid-template-columns: 9px minmax(0, 1fr);
  align-items: start;
  gap: var(--s-3);
  font-size: var(--fs-14);
  line-height: 1.5;
  color: var(--ink);
}
.note > svg {
  margin-top: 6px;
}
.note__body {
  min-width: 0;
}
.note__text {
  max-width: 72ch;
  text-wrap: pretty;
}
.note__strong {
  font-weight: 650;
}
/* The way forward: a text link, never a second button style. */
.note__link {
  display: inline;
  padding: 0;
  border: 0;
  background: none;
  color: var(--blue);
  font: inherit;
  font-weight: 600;
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 0.18em;
  white-space: nowrap;
  cursor: pointer;
}
.note__link:hover {
  text-decoration-thickness: 2px;
}
.note__sep {
  color: var(--muted);
}
.note__details {
  margin-top: 2px;
  font-size: var(--fs-12);
  color: var(--muted);
}
.note__details summary {
  width: max-content;
  cursor: pointer;
  font-weight: 600;
}
.note__details pre {
  margin: var(--s-2) 0 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-size: var(--fs-12);
}
@media (forced-colors: active) {
  .note__link {
    color: LinkText;
  }
}
</style>
