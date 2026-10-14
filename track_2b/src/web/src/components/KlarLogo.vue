<script setup lang="ts">
/** Wordmark "Klar" + red square period. Decorative: the parent names it. */
withDefaults(defineProps<{ size?: number }>(), { size: 24 })
</script>

<template>
  <span class="wordmark" :style="{ fontSize: `${size}px` }" aria-hidden="true"
    >Klar<svg class="wordmark__dot" viewBox="0 0 1 1" focusable="false"><rect width="1" height="1" /></svg
  ></span>
</template>

<style scoped>
.wordmark {
  display: inline-flex;
  align-items: baseline;
  font-weight: 700;
  font-variation-settings: 'opsz' 32;
  letter-spacing: -0.02em;
  line-height: 1;
  color: var(--ink);
}
.wordmark__dot {
  width: 0.155em;
  height: 0.155em;
  margin-left: 0.045em;
  fill: var(--klar-red);
  flex: none;
}
@media (forced-colors: active) {
  .wordmark__dot {
    fill: CanvasText;
  }
}
</style>
