<script setup lang="ts">
import { Check, Circle, X } from '@lucide/vue'
import type { Status } from '@/types'
import { t } from '@/i18n'

defineProps<{ status: Status }>()
</script>

<template>
  <span class="status" :class="`status--${status}`">
    <Check v-if="status === 'accepted'" :size="14" :stroke-width="3" aria-hidden="true" />
    <X v-else-if="status === 'rejected'" :size="14" :stroke-width="3" aria-hidden="true" />
    <Circle v-else :size="12" :stroke-width="2.5" aria-hidden="true" />
    {{ t(`status.${status}`) }}
  </span>
</template>

<style scoped>
.status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-14);
  font-weight: 500;
  white-space: nowrap;
  color: var(--muted);
}
.status--accepted {
  color: var(--green);
  font-weight: 600;
}
.status--rejected {
  color: var(--muted);
}
</style>
