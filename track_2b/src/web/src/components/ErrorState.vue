<script setup lang="ts">
import { t } from '@/i18n'
import ShapeIcon from './ShapeIcon.vue'

/**
 * Every problem state has a title (what happened), one sentence (why, in plain
 * words) and one primary action (slot). Technical detail stays under "Details".
 */
withDefaults(
  defineProps<{ title: string; body: string; details?: string | null; tone?: 'error' | 'info'; headingLevel?: 1 | 2 | 3; role?: 'alert' | 'status' | 'none' }>(),
  { details: null, tone: 'error', headingLevel: 2, role: 'none' },
)
</script>

<template>
  <section class="es" :class="`es--${tone}`" :role="role === 'none' ? undefined : role">
    <div class="es__head">
      <ShapeIcon v-if="tone === 'error'" shape="square" color="var(--klar-red)" :size="10" />
      <ShapeIcon v-else shape="diamond" color="var(--amber)" :size="10" />
      <component :is="`h${headingLevel}`" class="es__title" :tabindex="headingLevel === 1 ? -1 : undefined">{{ title }}</component>
    </div>
    <p class="es__body">{{ body }}</p>
    <div v-if="$slots.default" class="es__actions"><slot /></div>
    <details v-if="details" class="es__details">
      <summary>{{ t('error.details') }}</summary>
      <pre class="es__pre" translate="no">{{ details }}</pre>
    </details>
  </section>
</template>

<style scoped>
.es {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--s-3);
  width: 100%;
  max-width: 760px;
  padding: var(--s-5);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
}
.es--error {
  box-shadow: inset 3px 0 0 var(--klar-red);
}
.es--info {
  box-shadow: inset 3px 0 0 var(--amber);
}
.es__head {
  display: flex;
  align-items: center;
  gap: 10px;
}
.es__title {
  font-size: var(--fs-20);
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: -0.01em;
}
.es__body {
  max-width: 62ch;
  color: var(--ink);
}
.es__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-3);
  margin-top: var(--s-1);
}
.es__details {
  font-size: var(--fs-14);
  color: var(--muted);
}
.es__details summary {
  cursor: pointer;
  min-height: 24px;
}
.es__pre {
  margin-top: var(--s-2);
  padding: var(--s-3);
  background: var(--surface-2);
  border-radius: 6px;
  font-size: var(--fs-12);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
</style>
