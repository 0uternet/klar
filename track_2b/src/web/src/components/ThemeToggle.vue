<script setup lang="ts">
import { computed } from 'vue'
import { Monitor, Moon, Sun } from '@lucide/vue'
import { t } from '@/i18n'
import { cycleTheme, theme } from '@/stores/app'

const label = computed(() => t('theme.button', { mode: t(`theme.${theme.value}`) }))
const icon = computed(() => (theme.value === 'light' ? Sun : theme.value === 'dark' ? Moon : Monitor))
</script>

<template>
  <button type="button" class="btn btn--ghost btn--icon theme" :aria-label="label" :title="label" @click="cycleTheme">
    <span class="theme__icon" aria-hidden="true">
      <Transition name="theme-swap">
        <component :is="icon" :key="theme" :size="18" />
      </Transition>
    </span>
  </button>
</template>

<style scoped>
.theme {
  --btn-h: 36px;
  color: var(--muted);
}
.theme:hover {
  color: var(--ink);
}
/* The icons cross-fade with a quarter turn; both share one cell. */
.theme__icon {
  display: grid;
}
.theme__icon > * {
  grid-area: 1 / 1;
}
.theme-swap-enter-active,
.theme-swap-leave-active {
  transition: opacity var(--dur-2) var(--ease-out), transform var(--dur-3) var(--ease-out);
}
.theme-swap-enter-from {
  opacity: 0;
  transform: rotate(-90deg) scale(0.6);
}
.theme-swap-leave-to {
  opacity: 0;
  transform: rotate(90deg) scale(0.6);
}
</style>
