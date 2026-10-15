<script setup lang="ts">
import { ArrowRight } from '@lucide/vue'
import { t } from '@/i18n'
import { useDocumentTitle } from '@/composables/useDocumentTitle'

useDocumentTitle(() => t('notFound.docTitle'))
</script>

<template>
  <div class="container nf">
    <p class="nf__code mono m-rise" aria-hidden="true">404</p>
    <h1 class="h1 m-rise" style="--i: 1" tabindex="-1">{{ t('notFound.title') }}</h1>
    <p class="lede m-rise" style="--i: 2">{{ t('notFound.body') }}</p>
    <RouterLink class="btn btn--primary nf__cta m-rise" style="--i: 3" :to="{ name: 'home' }">
      {{ t('common.home') }}<ArrowRight :size="18" aria-hidden="true" />
    </RouterLink>
  </div>
</template>

<style scoped>
.nf {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--s-4);
  padding-top: clamp(var(--s-8), 12vh, var(--s-10));
}
.nf__code {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: var(--fs-13);
  font-weight: 500;
  color: var(--muted);
}
.nf__code::before {
  content: '';
  width: 7px;
  height: 7px;
  background: var(--klar-red);
}
.nf__cta {
  margin-top: var(--s-3);
}
@media (forced-colors: active) {
  .nf__code::before {
    background: CanvasText;
  }
}
</style>
