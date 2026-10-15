<script setup lang="ts">
import { useId } from 'vue'
import { ChevronDown } from '@lucide/vue'

/**
 * Animated disclosure (.m-collapse): a button with aria-expanded, and a region that is
 * inert while closed, so its links and buttons leave the tab order and the a11y tree.
 *  - row:    full-width row with a hairline (finding panel sections)
 *  - inline: a quiet text button (report header)
 */
const open = defineModel<boolean>('open', { default: false })
withDefaults(defineProps<{ variant?: 'row' | 'inline' }>(), { variant: 'row' })
const id = useId()
</script>

<template>
  <div class="disc" :class="[`disc--${variant}`, { 'is-open': open }]">
    <button type="button" class="disc__btn" :aria-expanded="open" :aria-controls="id" @click="open = !open">
      <span class="disc__label"><slot name="summary" /></span>
      <ChevronDown :size="16" aria-hidden="true" class="disc__chev" />
    </button>
    <div :id="id" class="m-collapse" :data-open="open">
      <div :inert="!open || undefined">
        <div class="disc__body"><slot /></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.disc__btn {
  display: flex;
  align-items: center;
  gap: var(--s-2);
  border: 0;
  background: transparent;
  color: var(--ink);
  text-align: left;
}
.disc__label {
  display: flex;
  align-items: center;
  gap: var(--s-2);
  min-width: 0;
}
.disc__chev {
  flex: none;
  color: var(--muted);
  transition: transform var(--dur-2) var(--ease-out);
}
.is-open > .disc__btn .disc__chev {
  transform: rotate(180deg);
}

/* Row: a section of the finding panel. */
.disc--row {
  border-top: 1px solid var(--line);
}
.disc--row > .disc__btn {
  width: 100%;
  min-height: 48px;
  padding: 0;
  font-size: var(--fs-14);
  font-weight: 650;
}
.disc--row > .disc__btn .disc__label {
  flex: 1;
}
.disc--row > .disc__btn:hover .disc__chev {
  color: var(--ink);
}
.disc--row .disc__body {
  padding: 2px 2px var(--s-5);
}

/* Inline: a quiet text button. */
.disc--inline > .disc__btn {
  min-height: 32px;
  padding: 0 6px;
  margin-left: -6px;
  border-radius: 6px;
  font-size: var(--fs-14);
  font-weight: 600;
  color: var(--muted);
  transition: color var(--dur-1) var(--ease-out), background-color var(--dur-1) var(--ease-out);
}
.disc--inline > .disc__btn:hover {
  color: var(--ink);
  background: var(--surface-2);
}
.disc--inline .disc__body {
  padding: var(--s-3) 2px 2px;
}
</style>
