<script setup lang="ts">
/**
 * A small link to an official source, opened in a new tab (said to screen readers).
 * The URL follows the UI language where the source has one (src/data/swiss-law.ts).
 */
import { computed } from 'vue'
import { ExternalLink } from '@lucide/vue'
import { locale, t } from '@/i18n'
import { sourceLink, type SourceId } from '@/data/swiss-law'

const props = defineProps<{ source: SourceId; label: string }>()
const link = computed(() => sourceLink(props.source, locale.value))
</script>

<template>
  <a class="src-link" :href="link.href" :hreflang="link.hreflang" target="_blank" rel="noopener noreferrer"
    >{{ label }}<ExternalLink class="src-link__icon" :size="12" aria-hidden="true" /><span class="sr-only"> {{ t('finding.newTab') }}</span></a
  >
</template>

<style scoped>
.src-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-height: 24px;
  font-size: var(--fs-13);
  font-weight: 500;
  color: var(--muted);
  text-decoration: underline;
  text-decoration-color: var(--line-strong);
  text-decoration-thickness: 1px;
  text-underline-offset: 0.22em;
  transition: color var(--dur-1) var(--ease-out), text-decoration-color var(--dur-1) var(--ease-out);
}
.src-link:hover {
  color: var(--ink);
  text-decoration-color: currentColor;
}
.src-link__icon {
  flex: none;
  transition: transform var(--dur-2) var(--ease-out);
}
@media (hover: hover) {
  .src-link:hover .src-link__icon {
    transform: translate(1px, -1px);
  }
}
@media (prefers-reduced-motion: reduce) {
  .src-link:hover .src-link__icon {
    transform: none;
  }
}
@media (forced-colors: active) {
  .src-link {
    color: LinkText;
    text-decoration-color: LinkText;
  }
}
</style>
