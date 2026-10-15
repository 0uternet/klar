<script setup lang="ts">
import type { Status } from '@/types'
import { t } from '@/i18n'

/** A person's decision: icon + word, never colour alone. The check draws itself when it appears. */
withDefaults(defineProps<{ status: Status; compact?: boolean }>(), { compact: false })
</script>

<template>
  <span class="status" :class="[`status--${status}`, { 'status--compact': compact }]">
    <svg class="status__icon" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true" focusable="false">
      <path v-if="status === 'accepted'" class="m-draw" pathLength="1" d="M3.2 8.4l3.1 3.1 6.5-6.9" />
      <path v-else-if="status === 'rejected'" class="m-draw" pathLength="1" d="M4.2 4.2l7.6 7.6M11.8 4.2l-7.6 7.6" />
      <circle v-else cx="8" cy="8" r="5" />
    </svg>
    <span :class="{ 'sr-only': compact }">{{ t(`status.${status}`) }}</span>
  </span>
</template>

<style scoped>
.status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-14);
  font-weight: 550;
  white-space: nowrap;
  color: var(--muted);
}
.status__icon {
  flex: none;
  fill: none;
  stroke: currentColor;
  stroke-width: 2.4;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.status--to_review .status__icon {
  stroke-width: 1.8;
}
.status--accepted {
  color: var(--green);
  font-weight: 650;
}
.status--accepted .status__icon {
  stroke-width: 2.8;
}
</style>
