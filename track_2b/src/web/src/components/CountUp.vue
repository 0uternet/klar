<script setup lang="ts">
// A number that counts up when it appears or changes; screen readers get the final value only.
import { useCountUp } from '@/lib/motion'

const props = withDefaults(defineProps<{ value: number; duration?: number; format?: (n: number) => string }>(), {
  duration: 900,
  format: (n: number) => Math.round(n).toLocaleString(),
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
