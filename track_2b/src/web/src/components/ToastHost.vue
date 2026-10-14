<script setup lang="ts">
import { X } from '@lucide/vue'
import { t } from '@/i18n'
import { dismissToast, toasts } from '@/stores/toast'
import ShapeIcon from './ShapeIcon.vue'

const SHAPE = { neutral: 'square', success: 'circle', danger: 'square', info: 'ring' } as const
const COLOR = { neutral: 'var(--on-ink)', success: 'var(--green)', danger: 'var(--klar-red)', info: 'var(--on-ink)' }
</script>

<template>
  <!-- The live region exists before any toast, so screen readers announce additions. -->
  <div class="toasts" role="status" aria-live="polite" aria-atomic="false">
    <TransitionGroup name="toast">
      <div v-for="item in toasts" :key="item.id" class="toast">
        <ShapeIcon :shape="SHAPE[item.tone]" :color="COLOR[item.tone]" :size="10" />
        <span class="toast__msg">{{ item.message }}</span>
        <button v-if="item.action" type="button" class="toast__action" @click="item.action.run(); dismissToast(item.id)">{{ item.action.label }}</button>
        <button type="button" class="toast__x" :aria-label="t('common.dismiss')" @click="dismissToast(item.id)">
          <X :size="16" aria-hidden="true" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toasts {
  position: fixed;
  z-index: 80;
  left: 50%;
  bottom: var(--s-5);
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--s-2);
  width: max-content;
  max-width: calc(100vw - 32px);
  pointer-events: none;
}
.toast {
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 44px;
  padding: 6px 6px 6px 16px;
  background: var(--ink);
  color: var(--on-ink);
  border-radius: var(--r-card);
  box-shadow: var(--shadow-overlay);
  font-size: var(--fs-14);
  font-weight: 500;
}
.toast__msg {
  max-width: 52ch;
}
.toast__action {
  min-height: 32px;
  padding: 0 12px;
  border: 1px solid var(--on-ink);
  border-radius: var(--r-control);
  background: transparent;
  color: var(--on-ink);
  font-weight: 700;
  font-size: var(--fs-14);
}
.toast__action:hover {
  background: color-mix(in srgb, var(--on-ink) 14%, transparent);
}
.toast__x {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--on-ink);
  opacity: 0.8;
}
.toast__x:focus-visible {
  outline-color: var(--on-ink);
  outline-offset: -2px;
}
.toast__x:hover {
  opacity: 1;
  background: rgba(127, 127, 127, 0.2);
}
.toast-enter-active,
.toast-leave-active {
  transition: opacity var(--dur-2) var(--ease), transform var(--dur-2) var(--ease);
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
@media (forced-colors: active) {
  .toast {
    border: 1px solid CanvasText;
  }
}
</style>
