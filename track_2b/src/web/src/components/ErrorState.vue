<script setup lang="ts">
import { t } from '@/i18n'
import ShapeIcon from './ShapeIcon.vue'

/**
 * Every problem state says what happened (title), why in one plain sentence (body)
 * and offers one primary action (default slot). Optional: `hint` (or the #hint slot)
 * gives an example or a way round, e.g. "Try https://www.example.ch or the demo site".
 * Technical detail stays under "Details".
 */
withDefaults(
  defineProps<{
    title: string
    body: string
    hint?: string | null
    details?: string | null
    tone?: 'error' | 'info'
    headingLevel?: 1 | 2 | 3
    role?: 'alert' | 'status' | 'none'
  }>(),
  { hint: null, details: null, tone: 'error', headingLevel: 2, role: 'none' },
)
</script>

<template>
  <section class="es m-rise" :class="`es--${tone}`" :role="role === 'none' ? undefined : role">
    <span class="es__icon" aria-hidden="true">
      <ShapeIcon v-if="tone === 'error'" shape="square" color="var(--klar-red)" :size="10" />
      <ShapeIcon v-else shape="diamond" color="var(--amber)" :size="11" />
    </span>
    <div class="es__main">
      <component :is="`h${headingLevel}`" class="es__title" :tabindex="headingLevel === 1 ? -1 : undefined">{{ title }}</component>
      <p class="es__body">{{ body }}</p>
      <div v-if="$slots.default" class="es__actions"><slot /></div>
      <p v-if="hint || $slots.hint" class="es__hint"><slot name="hint">{{ hint }}</slot></p>
      <details v-if="details" class="es__details">
        <summary>{{ t('error.details') }}</summary>
        <pre class="es__pre" translate="no">{{ details }}</pre>
      </details>
    </div>
  </section>
</template>

<style scoped>
.es {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--s-4);
  width: 100%;
  max-width: 760px;
  padding: var(--s-5);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
}
.es__icon {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: var(--r-control);
  background: var(--red-tint);
}
.es--info .es__icon {
  background: var(--amber-tint);
}
.es__main {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--s-2);
  min-width: 0;
  padding-top: 4px;
}
.es__title {
  font-size: var(--fs-18);
  font-weight: 650;
  line-height: var(--lh-snug);
  letter-spacing: var(--tr-h3);
}
.es__body {
  max-width: 62ch;
  color: var(--muted);
}
.es__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-3);
  margin-top: var(--s-2);
}
.es__hint {
  font-size: var(--fs-14);
  color: var(--muted);
}
.es__details {
  margin-top: var(--s-1);
  font-size: var(--fs-13);
  color: var(--muted);
}
.es__details summary {
  cursor: pointer;
  min-height: 24px;
  width: fit-content;
  border-radius: var(--r-sm);
}
.es__details summary:hover {
  color: var(--ink);
}
.es__pre {
  margin-top: var(--s-2);
  padding: var(--s-3);
  background: var(--surface-2);
  border-radius: var(--r-sm);
  font-size: var(--fs-12);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
@media (max-width: 480px) {
  .es {
    grid-template-columns: 1fr;
    gap: var(--s-3);
    padding: var(--s-4);
  }
  .es__main {
    padding-top: 0;
  }
}
@media (forced-colors: active) {
  .es__icon {
    border: 1px solid CanvasText;
  }
}
</style>
