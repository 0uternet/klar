<script setup lang="ts">
import { shortcutsEnabled } from '@/stores/app'

/** Visual key hint. Hidden from assistive tech (the shortcut list lives in the dialog). */
defineProps<{ keys: string[] }>()
</script>

<template>
  <span v-if="shortcutsEnabled" class="kh" aria-hidden="true"
    ><kbd v-for="k in keys" :key="k">{{ k }}</kbd></span
  >
</template>

<style scoped>
.kh {
  display: inline-flex;
  gap: 3px;
  vertical-align: middle;
}
/* UX-27: no key hints on touch screens or small viewports. */
@media (hover: none), (max-width: 767px) {
  .kh {
    display: none;
  }
}
</style>
