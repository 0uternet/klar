<script setup lang="ts">
import { X } from '@lucide/vue'
import { t } from '@/i18n'
import { dismissToast, toasts } from '@/stores/toast'
import ShapeIcon from './ShapeIcon.vue'

const SHAPE = { neutral: 'square', success: 'circle', danger: 'square', info: 'ring' } as const
const COLOR = { neutral: 'var(--on-ink)', success: 'var(--green-on-ink)', danger: 'var(--red-on-ink)', info: 'var(--on-ink)' }
</script>

<template>
  <!-- The live region exists before any toast, so screen readers announce additions. -->
  <div class="toasts" role="status" aria-live="polite" aria-atomic="false">
    <TransitionGroup name="fade-rise">
      <div v-for="item in toasts" :key="item.id" class="toast">
        <ShapeIcon :shape="SHAPE[item.tone]" :color="COLOR[item.tone]" :size="9" />
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
  left: 0;
  right: 0;
  bottom: max(var(--s-5), env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--s-2);
  padding-inline: var(--s-4);
  pointer-events: none;
}
.toast {
  pointer-events: auto;
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: min(560px, 100%);
  min-height: 44px;
  padding: 6px 6px 6px 16px;
  background: var(--ink);
  color: var(--on-ink);
  border-radius: var(--r-card);
  box-shadow: var(--shadow-overlay);
  font-size: var(--fs-14);
  font-weight: 500;
  letter-spacing: var(--tr-ui);
}
.toast__msg {
  min-width: 0;
  padding-right: 4px;
}
.toast__action {
  flex: none;
  min-height: 32px;
  padding: 0 12px;
  border: 0;
  border-radius: var(--r-control);
  background: color-mix(in srgb, var(--on-ink) 14%, transparent);
  color: var(--on-ink);
  font-weight: 650;
  font-size: var(--fs-14);
  transition: background-color var(--dur-1) var(--ease-out), transform var(--dur-1) var(--ease-out);
}
.toast__action:hover {
  background: color-mix(in srgb, var(--on-ink) 22%, transparent);
}
.toast__action:active {
  transform: scale(0.97);
}
.toast__x {
  flex: none;
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: var(--r-sm);
  background: transparent;
  color: var(--on-ink);
  opacity: 0.75;
  transition: opacity var(--dur-1) var(--ease-out), background-color var(--dur-1) var(--ease-out);
}
.toast__x:hover {
  opacity: 1;
  background: color-mix(in srgb, var(--on-ink) 14%, transparent);
}
.toast__action:focus-visible,
.toast__x:focus-visible {
  outline-color: var(--on-ink);
  outline-offset: -2px;
}
/* FLIP: the other toasts glide when one leaves. */
.fade-rise-move {
  transition: transform var(--dur-3) var(--ease-out);
}
@media (forced-colors: active) {
  .toast {
    border: 1px solid CanvasText;
  }
}
</style>
