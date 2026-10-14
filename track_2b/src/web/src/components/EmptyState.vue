<script setup lang="ts">
withDefaults(defineProps<{ title: string; body?: string; headingLevel?: 2 | 3 }>(), { headingLevel: 2 })
</script>

<template>
  <div class="empty">
    <span class="empty__mark" aria-hidden="true" />
    <component :is="`h${headingLevel}`" class="h3 empty__title">{{ title }}</component>
    <p v-if="body" class="empty__body">{{ body }}</p>
    <div v-if="$slots.default" class="empty__actions"><slot /></div>
  </div>
</template>

<style scoped>
.empty {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--s-3);
  padding: var(--s-7) var(--s-5);
  border: 1px dashed var(--control-border);
  border-radius: var(--r-card);
}
.empty__mark {
  width: 14px;
  height: 14px;
  background: var(--klar-red);
}
.empty__body {
  color: var(--muted);
  max-width: 52ch;
}
.empty__actions {
  margin-top: var(--s-2);
  display: flex;
  flex-wrap: wrap;
  gap: var(--s-3);
}
</style>
