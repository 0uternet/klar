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
    <component :is="icon" :size="18" aria-hidden="true" />
  </button>
</template>

<style scoped>
.theme {
  --btn-h: 40px;
  color: var(--muted);
}
.theme:hover {
  color: var(--ink);
}
</style>
