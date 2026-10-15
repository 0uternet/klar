<script setup lang="ts">
import { APP_VERSION } from '@/config'
import { t } from '@/i18n'
import { shortcutsDialogOpen } from '@/stores/app'
import KlarLogo from './KlarLogo.vue'
</script>

<template>
  <!-- One line: what it is and which version. Navigation lives in the header. -->
  <footer class="ftr">
    <div class="container ftr__inner">
      <p class="ftr__meta">
        <KlarLogo :size="15" />
        <span>{{ t('footer.license') }}</span>
        <span class="ftr__dot" aria-hidden="true">·</span>
        <span class="mono">{{ t('footer.version', { v: APP_VERSION }) }}</span>
      </p>
      <button type="button" class="ftr__btn" aria-haspopup="dialog" @click="shortcutsDialogOpen = true">
        {{ t('footer.shortcuts') }}<kbd aria-hidden="true">?</kbd>
      </button>
    </div>
  </footer>
</template>

<style scoped>
.ftr {
  margin-top: var(--s-8);
  border-top: 1px solid var(--line);
  font-size: var(--fs-13);
  color: var(--muted);
}
.ftr__inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--s-2) var(--s-5);
  padding-block: var(--s-4);
}
.ftr__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-2);
}
.ftr__meta :deep(.wordmark) {
  margin-right: var(--s-1);
}
.ftr__dot {
  color: var(--muted);
}
.ftr__btn {
  display: inline-flex;
  align-items: center;
  gap: var(--s-2);
  min-height: 32px;
  margin-right: -8px;
  padding: 0 8px;
  border: 0;
  border-radius: var(--r-sm);
  background: none;
  color: var(--muted);
  font-size: inherit;
  font-weight: 500;
  transition: color var(--dur-1) var(--ease-out), background-color var(--dur-1) var(--ease-out);
}
.ftr__btn:hover {
  color: var(--ink);
  background: var(--surface-2);
}
.ftr__btn kbd {
  font-size: 0.6875rem;
  min-width: 1.25rem;
  height: 1.25rem;
}
@media (max-width: 639px) {
  .ftr__btn {
    margin: 0 0 0 -8px;
  }
}
</style>
