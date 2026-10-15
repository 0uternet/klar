<script setup lang="ts">
/**
 * Nothing to show yet: say so in one line, offer the next step (default slot) and,
 * where it helps, an example (`hint` or the #hint slot).
 */
withDefaults(defineProps<{ title: string; body?: string; hint?: string | null; headingLevel?: 2 | 3 }>(), { headingLevel: 2, hint: null })
</script>

<template>
  <div class="empty m-rise">
    <span class="empty__mark" aria-hidden="true"><span /></span>
    <component :is="`h${headingLevel}`" class="h3 empty__title">{{ title }}</component>
    <p v-if="body" class="empty__body">{{ body }}</p>
    <div v-if="$slots.default" class="empty__actions"><slot /></div>
    <p v-if="hint || $slots.hint" class="empty__hint"><slot name="hint">{{ hint }}</slot></p>
  </div>
</template>

<style scoped>
.empty {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--s-2);
  padding: var(--s-7) var(--s-6);
  border: 1px dashed var(--line-strong);
  border-radius: var(--r-card);
}
.empty__mark {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  margin-bottom: var(--s-2);
  border-radius: var(--r-control);
  background: var(--surface-2);
}
.empty__mark span {
  width: 9px;
  height: 9px;
  background: var(--klar-red);
}
.empty__body {
  color: var(--muted);
  max-width: 52ch;
}
.empty__actions {
  margin-top: var(--s-3);
  display: flex;
  flex-wrap: wrap;
  gap: var(--s-3);
}
.empty__hint {
  font-size: var(--fs-14);
  color: var(--muted);
}
@media (max-width: 480px) {
  .empty {
    padding: var(--s-6) var(--s-4);
  }
}
@media (forced-colors: active) {
  .empty__mark span {
    background: CanvasText;
  }
}
</style>
