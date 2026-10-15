<script setup lang="ts">
import { computed } from 'vue'
import { LANGUAGES, locale, setLocale, t } from '@/i18n'

/**
 * EN · DE · FR · IT. Each option's accessible name starts with its visible label
 * (WCAG 2.5.3) followed by the endonym, in its own language (WCAG 3.1.2).
 * A single thumb slides to the active language.
 */
const index = computed(() => Math.max(0, LANGUAGES.findIndex((l) => l.code === locale.value)))
</script>

<template>
  <div class="lang" role="group" :aria-label="t('lang.label')" :style="{ '--idx': index }">
    <span class="lang__thumb" aria-hidden="true" />
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
  --w: 34px;
  position: relative;
  display: inline-flex;
  padding: 2px;
  background: var(--surface-2);
  border-radius: var(--r-control);
}
.lang__thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: var(--w);
  height: 32px;
  border-radius: var(--r-sm);
  background: var(--surface-raised);
  box-shadow: 0 0 0 1px var(--line), var(--shadow-xs);
  transform: translateX(calc(var(--idx) * var(--w)));
  transition: transform var(--dur-3) var(--ease-out);
}
.lang__btn {
  position: relative;
  width: var(--w);
  height: 32px;
  padding: 0;
  border: 0;
  border-radius: var(--r-sm);
  background: transparent;
  color: var(--muted);
  font-size: var(--fs-12);
  font-weight: 650;
  letter-spacing: 0.04em;
  transition: color var(--dur-1) var(--ease-out);
}
.lang__btn:hover {
  color: var(--ink);
}
.lang__btn[aria-pressed='true'] {
  color: var(--ink);
}
@media (forced-colors: active) {
  .lang__thumb {
    display: none;
  }
  .lang__btn[aria-pressed='true'] {
    outline: 2px solid CanvasText;
    outline-offset: -2px;
  }
}
</style>
