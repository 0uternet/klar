<script setup lang="ts">
/** The four status shapes: square, diamond, circle, ring. Never colour alone. */
withDefaults(defineProps<{ shape: 'square' | 'diamond' | 'circle' | 'ring'; color?: string; size?: number }>(), {
  color: 'currentColor',
  size: 10,
})
</script>

<template>
  <svg class="shape" :width="size" :height="size" viewBox="0 0 10 10" aria-hidden="true" focusable="false">
    <rect v-if="shape === 'square'" x="0.5" y="0.5" width="9" height="9" :fill="color" />
    <polygon v-else-if="shape === 'diamond'" points="5,0 10,5 5,10 0,5" :fill="color" />
    <circle v-else-if="shape === 'circle'" cx="5" cy="5" r="4.6" :fill="color" />
    <circle v-else cx="5" cy="5" r="3.7" fill="none" :stroke="color" stroke-width="1.6" />
  </svg>
</template>

<style scoped>
.shape {
  flex: none;
  display: inline-block;
}
@media (forced-colors: active) {
  .shape rect,
  .shape polygon {
    fill: CanvasText;
  }
  .shape circle {
    stroke: CanvasText;
  }
}
</style>
