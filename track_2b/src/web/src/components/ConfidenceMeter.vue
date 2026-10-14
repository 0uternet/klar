<script setup lang="ts">
import { computed } from 'vue'
import type { Confidence } from '@/types'
import { t } from '@/i18n'

const props = withDefaults(defineProps<{ level: Confidence; compact?: boolean }>(), { compact: false })
const filled = computed(() => ({ high: 3, medium: 2, low: 1 })[props.level])
const label = computed(() => t('confidence.label', { level: t(`confidence.${props.level}`) }))
</script>

<template>
  <span class="conf">
    <span class="conf__bars" aria-hidden="true">
      <span v-for="i in 3" :key="i" class="conf__bar" :class="{ 'is-on': i <= filled }" :style="{ height: `${4 + i * 3}px` }" />
    </span>
    <span :class="compact ? 'sr-only' : 'conf__label'">{{ label }}</span>
  </span>
</template>

<style scoped>
.conf {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: var(--fs-14);
  color: var(--muted);
  white-space: nowrap;
}
.conf__bars {
  display: inline-flex;
  align-items: flex-end;
  gap: 2px;
  height: 13px;
}
.conf__bar {
  width: 4px;
  border-radius: 1px;
  background: transparent;
  border: 1px solid var(--control-border);
}
.conf__bar.is-on {
  background: var(--ink);
  border-color: var(--ink);
}
</style>
