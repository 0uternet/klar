<script setup lang="ts">
import { LANGUAGES, locale, setLocale, t } from '@/i18n'

/**
 * EN · DE · FR · IT. Each option's accessible name starts with its visible label
 * (WCAG 2.5.3) followed by the endonym, in its own language (WCAG 3.1.2).
 */
</script>

<template>
  <div class="lang" role="group" :aria-label="t('lang.label')">
    <button
      v-for="l in LANGUAGES"
      :key="l.code"
      type="button"
      class="lang__btn"
      :lang="l.code"
      :aria-pressed="locale === l.code"
      @click="setLocale(l.code)"
    >
      {{ l.short }}<span class="sr-only">, {{ l.name }}</span>
    </button>
  </div>
</template>

<style scoped>
.lang {
  display: inline-flex;
  padding: 3px;
  gap: 2px;
  background: var(--surface-2);
  border-radius: var(--r-control);
}
.lang__btn {
  min-width: 36px;
  height: 32px;
  padding: 0 6px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--muted);
  font-size: var(--fs-12);
  font-weight: 700;
  letter-spacing: 0.04em;
  transition: background-color var(--dur-1) var(--ease), color var(--dur-1) var(--ease);
}
.lang__btn:hover {
  color: var(--ink);
}
.lang__btn[aria-pressed='true'] {
  background: var(--surface);
  color: var(--ink);
  box-shadow: 0 0 0 1px var(--line);
}
@media (forced-colors: active) {
  .lang__btn[aria-pressed='true'] {
    outline: 2px solid CanvasText;
  }
}
</style>
