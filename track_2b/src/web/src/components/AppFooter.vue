<script setup lang="ts">
import { APP_VERSION } from '@/config'
import { t } from '@/i18n'
import { shortcutsDialogOpen } from '@/stores/app'
import KlarLogo from './KlarLogo.vue'
</script>

<template>
  <footer class="ftr">
    <div class="container ftr__inner">
      <div class="ftr__brand">
        <KlarLogo :size="20" />
        <p class="ftr__tag">{{ t('footer.tagline') }}</p>
      </div>
      <ul class="ftr__links" role="list">
        <li><RouterLink :to="{ name: 'about' }">{{ t('nav.about') }}</RouterLink></li>
        <li><RouterLink :to="{ name: 'human' }">{{ t('nav.human') }}</RouterLink></li>
        <li>
          <button type="button" class="ftr__btn" aria-haspopup="dialog" @click="shortcutsDialogOpen = true">
            {{ t('footer.shortcuts') }} <kbd aria-hidden="true">?</kbd>
          </button>
        </li>
      </ul>
      <ul class="ftr__facts" role="list">
        <li>{{ t('footer.requests') }}</li>
        <li>{{ t('footer.a11y') }} · {{ t('footer.license') }} · <span class="mono">{{ t('footer.version', { v: APP_VERSION }) }}</span></li>
      </ul>
    </div>
  </footer>
</template>

<style scoped>
.ftr {
  margin-top: var(--s-9);
  border-top: 1px solid var(--line);
  font-size: var(--fs-14);
  color: var(--muted);
}
.ftr__inner {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1.6fr;
  gap: var(--s-6);
  padding-top: var(--s-6);
  padding-bottom: var(--s-7);
}
.ftr__brand {
  display: flex;
  flex-direction: column;
  gap: var(--s-2);
}
.ftr__links,
.ftr__facts {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--s-2);
}
.ftr__links a,
.ftr__btn {
  color: var(--ink);
  text-decoration: none;
  font-weight: 500;
}
.ftr__links a:hover,
.ftr__btn:hover {
  text-decoration: underline;
}
.ftr__btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  border: 0;
  background: none;
  font-size: inherit;
}
@media (max-width: 860px) {
  .ftr__inner {
    grid-template-columns: 1fr;
  }
}
</style>
