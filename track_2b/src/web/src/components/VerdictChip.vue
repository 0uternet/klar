<script setup lang="ts">
import { computed } from 'vue'
import type { Outcome } from '@/types'
import { t } from '@/i18n'
import ShapeIcon from './ShapeIcon.vue'

/** Verdict = shape + label, never colour alone (W3C ACT/EARL vocabulary). */
const props = withDefaults(defineProps<{ outcome: Outcome; size?: 'sm' | 'md'; long?: boolean }>(), {
  size: 'md',
  long: false,
})

const SHAPE = { failed: 'square', cantTell: 'diamond', passed: 'circle', inapplicable: 'ring' } as const
const COLOR = { failed: 'var(--klar-red)', cantTell: 'var(--amber)', passed: 'var(--green)', inapplicable: 'var(--grey-shape)' }

const label = computed(() =>
  props.long && props.outcome === 'inapplicable' ? t('outcome.inapplicable.long') : t(`outcome.${props.outcome}`),
)
</script>

<template>
  <span class="verdict" :class="[`verdict--${outcome}`, `verdict--${size}`]">
    <ShapeIcon :shape="SHAPE[outcome]" :color="COLOR[outcome]" :size="size === 'sm' ? 8 : 10" />
    <span class="verdict__label">{{ label }}</span>
  </span>
</template>

<style scoped>
.verdict {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 26px;
  padding: 0 10px 0 9px;
  border-radius: var(--r-pill);
  font-size: var(--fs-14);
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  letter-spacing: -0.005em;
}
.verdict--sm {
  height: 22px;
  gap: 6px;
  padding: 0 8px 0 7px;
  font-size: var(--fs-12);
}
.verdict--failed {
  background: var(--red-tint);
  color: var(--red-text);
}
.verdict--cantTell {
  background: var(--amber-tint);
  color: var(--amber);
}
.verdict--passed {
  background: var(--green-tint);
  color: var(--green);
}
.verdict--inapplicable {
  background: var(--surface-2);
  color: var(--muted);
}
@media (forced-colors: active) {
  .verdict {
    border: 1px solid CanvasText;
  }
}
</style>
