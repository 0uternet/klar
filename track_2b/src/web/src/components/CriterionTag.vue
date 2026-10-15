<script setup lang="ts">
import { computed, ref, useId } from 'vue'
import { criterion as wcag, en301549 } from '@/data/wcag'
import { locale, t } from '@/i18n'

/**
 * Mono criterion code + plain-language name.
 * With `tooltip`, it is focusable and shows the official title and the
 * EN 301 549 clause on hover or focus; Esc dismisses it (WCAG 1.4.13).
 */
const props = withDefaults(defineProps<{ code: string; name?: string; tooltip?: boolean; showLevel?: boolean }>(), {
  tooltip: false,
  showLevel: false,
})

const c = computed(() => wcag(props.code))
const plain = computed(() => c.value?.plain[locale.value] ?? props.name ?? '')
const id = useId()
const open = ref(false)
</script>

<template>
  <span
    class="crit"
    :class="{ 'crit--tip': tooltip }"
    :tabindex="tooltip ? 0 : undefined"
    :aria-describedby="tooltip ? id : undefined"
    @mouseenter="open = true"
    @mouseleave="open = false"
    @focus="open = true"
    @blur="open = false"
    @keydown.esc="open = false"
  >
    <code class="crit__code">{{ code }}</code>
    <span class="crit__name">{{ plain }}</span>
    <span v-if="showLevel && c" class="crit__level">{{ c.level }}</span>
    <span v-if="tooltip" :id="id" role="tooltip" class="crit__tip" :class="{ 'is-open': open }">
      <span class="crit__tip-label">{{ t('finding.official') }}</span>
      <span lang="en" class="crit__tip-title">{{ c?.title ?? name }}</span>
      <span class="crit__tip-meta">{{ t('level', { level: c?.level ?? '—' }) }} · EN 301 549 {{ en301549(code) }}</span>
    </span>
  </span>
</template>

<style scoped>
.crit {
  position: relative;
  display: inline-flex;
  align-items: baseline;
  flex-wrap: wrap;
  column-gap: 8px;
  min-width: 0;
  font-size: var(--fs-14);
  color: var(--ink);
}
.crit--tip {
  cursor: help;
  border-radius: 4px;
}
.crit__code {
  font-size: 0.8125rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.crit__name {
  font-weight: 500;
}
.crit__level {
  align-self: center;
  font-size: var(--fs-12);
  color: var(--muted);
  border: 1px solid var(--control-border);
  border-radius: 4px;
  padding: 0 4px;
  line-height: 16px;
}
.crit__tip {
  position: absolute;
  z-index: 30;
  left: 0;
  top: calc(100% + 8px);
  display: flex;
  visibility: hidden;
  opacity: 0;
  transform: translateY(-2px);
  transition: opacity var(--dur-1) var(--ease-out), transform var(--dur-1) var(--ease-out), visibility 0s linear var(--dur-1);
  flex-direction: column;
  gap: 2px;
  width: max-content;
  max-width: min(320px, 80vw);
  padding: 10px 12px;
  background: var(--ink);
  color: var(--on-ink);
  border-radius: var(--r-control);
  box-shadow: var(--shadow-overlay);
  font-size: var(--fs-14);
  font-weight: 500;
  line-height: 1.4;
}
.crit__tip.is-open {
  visibility: visible;
  opacity: 1;
  transform: none;
  transition-delay: 0s;
}
/* Invisible bridge so the pointer can move onto the tooltip (WCAG 1.4.13 hoverable). */
.crit__tip::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  top: -10px;
  height: 10px;
}
.crit__tip-title {
  font-weight: 600;
}
.crit__tip-label,
.crit__tip-meta {
  font-size: var(--fs-12);
  opacity: 0.85;
}
</style>
