<script setup lang="ts">
// A number that counts up when it appears or changes; screen readers get the final value only.
import { formatNumber } from '@/i18n'
import { useCountUp } from '@/lib/motion'

const props = withDefaults(defineProps<{ value: number; duration?: number; format?: (n: number) => string }>(), {
  duration: 900,
  format: (n: number) => formatNumber(Math.round(n)),  // the UI language, not the browser's
})
const shown = useCountUp(() => props.value, props.duration)
</script>

<template>
  <span class="countup"><span aria-hidden="true">{{ format(shown) }}</span><span class="sr-only">{{ format(value) }}</span></span>
</template>

<style scoped>
.countup {
  font-variant-numeric: tabular-nums;
}
</style>
