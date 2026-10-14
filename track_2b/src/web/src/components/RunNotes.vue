<script setup lang="ts">
import { ArrowRight } from '@lucide/vue'
import { formatNumber, t, tp, type MessageKey, type PluralBase } from '@/i18n'
import type { RunNote } from '@/lib/notes'
import ShapeIcon from './ShapeIcon.vue'

/** "About this run" (UX-2): what this run could not do, each line with one way forward. */
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
      <ShapeIcon :shape="n.tone === 'warning' ? 'diamond' : 'circle'" :color="n.tone === 'warning' ? 'var(--amber)' : 'var(--blue)'" :size="10" />
      <div class="note__body">
        <p>
          <strong v-if="n.title" class="note__strong">{{ t(n.title) }}. </strong>{{ message(n) }}
        </p>
        <div v-if="n.actions.length" class="note__actions">
          <template v-for="(a, i) in n.actions" :key="i">
            <button v-if="a.kind === 'demo'" type="button" class="btn btn--secondary btn--sm" @click="emit('demo')">
              {{ t('home.demo.primary') }} <ArrowRight :size="14" aria-hidden="true" />
            </button>
            <button v-else-if="a.kind === 'rerun'" type="button" class="btn btn--secondary btn--sm" @click="emit('rerun')">{{ t('scan.rerun') }}</button>
            <button v-else-if="a.kind === 'runAgain'" type="button" class="btn btn--secondary btn--sm" @click="emit('rerun')">{{ t('notes.runAgain') }}</button>
            <button
              v-else-if="a.kind === 'filter'"
              type="button"
              class="btn btn--secondary btn--sm"
              :aria-label="`${t('notes.show')}: ${reasonTitle(a.reason)}`"
              @click="emit('filter', a.reason)"
            >
              {{ t('notes.show') }}
            </button>
            <RouterLink v-else-if="a.kind === 'connect'" class="note__link" :to="{ name: 'about', hash: '#connect' }">{{ t('replay.connectShort') }}</RouterLink>
            <RouterLink v-else class="note__link" :to="{ name: 'about', hash: '#connect' }">{{ t('notes.checkConnection') }}</RouterLink>
          </template>
        </div>
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
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--s-2);
}
.note {
  display: flex;
  align-items: flex-start;
  gap: var(--s-3);
  padding: var(--s-3) var(--s-4);
  border-radius: var(--r-control);
  font-size: var(--fs-14);
  line-height: 1.45;
}
.note--warning {
  background: var(--amber-tint);
}
.note--info {
  background: var(--surface-2);
}
.note > :first-child {
  flex: none;
  margin-top: 5px;
}
.note__body {
  display: flex;
  flex-direction: column;
  gap: var(--s-2);
  min-width: 0;
}
.note__strong {
  font-weight: 700;
}
.note__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-2) var(--s-4);
}
.note__actions .btn {
  --btn-h: 32px;
}
.note__link {
  font-weight: 600;
}
.note__details summary {
  cursor: pointer;
  color: var(--muted);
  font-size: var(--fs-12);
  font-weight: 600;
}
.note__details pre {
  margin: var(--s-2) 0 0;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  font-size: var(--fs-12);
  color: var(--muted);
}
</style>
