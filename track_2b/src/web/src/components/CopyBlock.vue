<script setup lang="ts">
import { ref } from 'vue'
import { Check, Copy } from '@lucide/vue'
import { t } from '@/i18n'

/** A command or config snippet with a copy button (the result is announced politely). */
const props = defineProps<{ text: string; label: string }>()
const copied = ref(false)

async function copy() {
  try {
    await navigator.clipboard.writeText(props.text)
    copied.value = true
    window.setTimeout(() => (copied.value = false), 1800)
  } catch {
    /* clipboard unavailable: the text stays selectable */
  }
}
</script>

<template>
  <div class="cb">
    <pre class="cb__pre" translate="no"><code>{{ text }}</code></pre>
    <button type="button" class="btn btn--secondary btn--sm cb__btn" @click="copy">
      <component :is="copied ? Check : Copy" :size="14" aria-hidden="true" />{{ copied ? t('common.copied') : label }}
    </button>
    <span class="sr-only" role="status">{{ copied ? t('common.copied') : '' }}</span>
  </div>
</template>

<style scoped>
.cb {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--s-2);
  width: 100%;
}
.cb__pre {
  width: 100%;
  margin: 0;
  padding: 12px 14px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: var(--r-control);
  font-size: var(--fs-14);
  line-height: 1.7;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.cb__btn {
  gap: 6px;
}
</style>
