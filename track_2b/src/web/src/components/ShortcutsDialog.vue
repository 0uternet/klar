<script setup lang="ts">
import { ref, useId, watch } from 'vue'
import { X } from '@lucide/vue'
import { t, type MessageKey } from '@/i18n'
import { shortcutsDialogOpen, shortcutsEnabled } from '@/stores/app'

/** Native <dialog>: focus trap, Esc and inert background come for free. */
const dialog = ref<HTMLDialogElement | null>(null)
const titleId = useId()
const hintId = useId()

watch(shortcutsDialogOpen, (open) => {
  const d = dialog.value
  if (!d) return
  if (open && !d.open) d.showModal()
  if (!open && d.open) d.close()
})

type Row = { keys: string[]; label: MessageKey }
const groups: { title: MessageKey; rows: Row[] }[] = [
  {
    title: 'shortcuts.groupGlobal',
    rows: [
      { keys: ['/'], label: 'shortcuts.focus' },
      { keys: ['?'], label: 'shortcuts.help' },
    ],
  },
  {
    title: 'shortcuts.groupFindings',
    rows: [
      { keys: ['J'], label: 'shortcuts.next' },
      { keys: ['K'], label: 'shortcuts.prev' },
      { keys: ['A'], label: 'shortcuts.accept' },
      { keys: ['R'], label: 'shortcuts.reject' },
      { keys: ['Esc'], label: 'shortcuts.close' },
    ],
  },
]
</script>

<template>
  <dialog ref="dialog" class="dlg" :aria-labelledby="titleId" @close="shortcutsDialogOpen = false" @click.self="shortcutsDialogOpen = false">
    <div class="dlg__inner">
      <div class="dlg__head">
        <h2 :id="titleId" class="h3">{{ t('shortcuts.title') }}</h2>
        <button type="button" class="btn btn--ghost btn--icon btn--sm dlg__x" :aria-label="t('common.close')" @click="shortcutsDialogOpen = false">
          <X :size="18" aria-hidden="true" />
        </button>
      </div>

      <div v-for="g in groups" :key="g.title" class="dlg__group">
        <h3 class="dlg__group-title">{{ t(g.title) }}</h3>
        <dl class="dlg__rows">
          <div v-for="r in g.rows" :key="r.label" class="dlg__row">
            <dt>{{ t(r.label) }}</dt>
            <dd><kbd v-for="k in r.keys" :key="k">{{ k }}</kbd></dd>
          </div>
        </dl>
      </div>

      <div class="dlg__switch">
        <div>
          <p class="dlg__switch-label" :id="`${hintId}-l`">{{ t('shortcuts.toggle') }}</p>
          <p :id="hintId" class="dlg__switch-hint">{{ t('shortcuts.toggleHint') }}</p>
        </div>
        <button
          type="button"
          role="switch"
          class="switch"
          :aria-checked="shortcutsEnabled"
          :aria-labelledby="`${hintId}-l`"
          :aria-describedby="hintId"
          @click="shortcutsEnabled = !shortcutsEnabled"
        >
          <span class="switch__track" aria-hidden="true"><span class="switch__thumb" /></span>
          <span class="switch__text">{{ shortcutsEnabled ? t('common.on') : t('common.off') }}</span>
        </button>
      </div>
    </div>
  </dialog>
</template>

<style scoped>
.dlg {
  width: min(460px, calc(100vw - 32px));
  max-height: calc(100dvh - 64px);
  padding: 0;
  border: 1px solid var(--line);
  border-radius: var(--r-lg);
  background: var(--surface);
  color: var(--ink);
  box-shadow: var(--shadow-overlay);
}
.dlg::backdrop {
  background: var(--scrim);
}
.dlg[open] {
  animation: dlg-in var(--dur-3) var(--ease-out);
}
.dlg[open]::backdrop {
  animation: dlg-fade var(--dur-2) var(--ease-out);
}
@keyframes dlg-in {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.98);
  }
}
@keyframes dlg-fade {
  from {
    opacity: 0;
  }
}
.dlg__inner {
  padding: var(--s-5);
}
.dlg__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.dlg__x {
  margin-right: -8px;
  color: var(--muted);
}
.dlg__x:hover {
  color: var(--ink);
}
.dlg__group {
  margin-top: var(--s-5);
}
.dlg__group-title {
  font-size: var(--fs-12);
  font-weight: 600;
  letter-spacing: var(--tr-caps);
  text-transform: uppercase;
  color: var(--muted);
}
.dlg__rows {
  margin: var(--s-2) 0 0;
}
.dlg__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s-4);
  min-height: 40px;
  border-top: 1px solid var(--line);
  font-size: var(--fs-14);
}
.dlg__row dd {
  display: inline-flex;
  gap: 4px;
  margin: 0;
}
.dlg__switch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s-4);
  margin-top: var(--s-5);
  padding: var(--s-4);
  background: var(--surface-2);
  border-radius: var(--r-card);
}
.dlg__switch-label {
  font-size: var(--fs-14);
  font-weight: 600;
}
.dlg__switch-hint {
  margin-top: 2px;
  font-size: var(--fs-13);
  color: var(--muted);
}
.switch {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex: none;
  min-height: 44px;
  padding: 0 4px;
  border: 0;
  border-radius: var(--r-control);
  background: transparent;
  font-size: var(--fs-14);
  font-weight: 600;
}
.switch__track {
  position: relative;
  width: 40px;
  height: 24px;
  border-radius: 12px;
  background: var(--surface);
  border: 1.5px solid var(--control-border);
  transition: background-color var(--dur-2) var(--ease-out), border-color var(--dur-2) var(--ease-out);
}
.switch__thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 17px;
  height: 17px;
  border-radius: 50%;
  background: var(--muted);
  transition: transform var(--dur-3) var(--ease-spring), background-color var(--dur-2) var(--ease-out);
}
.switch[aria-checked='true'] .switch__track {
  background: var(--ink);
  border-color: var(--ink);
}
.switch[aria-checked='true'] .switch__thumb {
  transform: translateX(16px);
  background: var(--on-ink);
}
.switch__text {
  min-width: 5.5em;
  text-align: left;
}
@media (max-width: 420px) {
  .dlg__switch {
    flex-direction: column;
    align-items: flex-start;
  }
}
@media (forced-colors: active) {
  .switch__thumb {
    background: CanvasText;
  }
  .switch[aria-checked='true'] .switch__track {
    background: Highlight;
  }
}
</style>
