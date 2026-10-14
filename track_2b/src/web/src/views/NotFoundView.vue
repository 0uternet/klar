<script setup lang="ts">
import { t } from '@/i18n'
import { useDocumentTitle } from '@/composables/useDocumentTitle'

useDocumentTitle(() => t('notFound.docTitle'))
</script>

<template>
  <div class="container nf">
    <p class="nf__code mono" aria-hidden="true">404</p>
    <h1 class="h1" tabindex="-1">{{ t('notFound.title') }}</h1>
    <p class="lede">{{ t('notFound.body') }}</p>
    <RouterLink class="btn btn--primary" :to="{ name: 'home' }">{{ t('common.home') }}</RouterLink>
  </div>
</template>

<style scoped>
.nf {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--s-4);
  padding-top: var(--s-9);
}
.nf__code {
  font-size: var(--fs-14);
  color: var(--muted);
}
</style>
