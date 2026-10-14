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

const rows: { keys: string[]; label: MessageKey }[] = [
  { keys: ['/'], label: 'shortcuts.focus' },
  { keys: ['J'], label: 'shortcuts.next' },
  { keys: ['K'], label: 'shortcuts.prev' },
  { keys: ['A'], label: 'shortcuts.accept' },
  { keys: ['R'], label: 'shortcuts.reject' },
  { keys: ['Esc'], label: 'shortcuts.close' },
  { keys: ['?'], label: 'shortcuts.help' },
]
</script>

<template>
  <dialog ref="dialog" class="dlg" :aria-labelledby="titleId" @close="shortcutsDialogOpen = false" @click.self="shortcutsDialogOpen = false">
    <div class="dlg__inner">
      <div class="dlg__head">
        <h2 :id="titleId" class="h3">{{ t('shortcuts.title') }}</h2>
        <button type="button" class="btn btn--ghost btn--icon btn--sm" :aria-label="t('common.close')" @click="shortcutsDialogOpen = false">
          <X :size="18" aria-hidden="true" />
        </button>
      </div>
      <table class="dlg__table">
        <tbody>
          <tr v-for="r in rows" :key="r.label">
            <th scope="row"><kbd v-for="k in r.keys" :key="k">{{ k }}</kbd></th>
            <td>{{ t(r.label) }}</td>
          </tr>
        </tbody>
      </table>
      <p class="dlg__scope">{{ t('shortcuts.scope') }}</p>
      <ul class="dlg__hints" role="list">
        <li><strong>{{ t('outcome.failed') }}, {{ t('outcome.passed') }}</strong> · {{ t('decide.hint.failed') }}</li>
        <li><strong>{{ t('outcome.cantTell') }}</strong> · {{ t('decide.hint.review') }}</li>
      </ul>
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
  width: min(520px, calc(100vw - 32px));
  max-height: calc(100vh - 64px);
  padding: 0;
  border: 1px solid var(--line);
  border-radius: var(--r-card);
  background: var(--surface);
  color: var(--ink);
  box-shadow: var(--shadow-overlay);
}
.dlg::backdrop {
  background: var(--scrim);
}
.dlg[open] {
  animation: klar-fade-up var(--dur-2) var(--ease);
}
.dlg__inner {
  padding: var(--s-5);
}
.dlg__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--s-4);
}
.dlg__table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-14);
}
.dlg__table th,
.dlg__table td {
  padding: 10px 0;
  border-top: 1px solid var(--line);
  text-align: left;
  vertical-align: middle;
}
.dlg__table th {
  width: 5.5rem;
  font-weight: 400;
}
.dlg__scope {
  margin-top: var(--s-3);
  font-size: var(--fs-14);
  color: var(--muted);
}
.dlg__hints {
  margin: var(--s-3) 0 0;
  padding-left: 1.1em;
  font-size: var(--fs-14);
  color: var(--muted);
}
.dlg__hints li + li {
  margin-top: 4px;
}
.dlg__switch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s-4);
  margin-top: var(--s-5);
  padding: var(--s-4);
  background: var(--surface-2);
  border-radius: var(--r-control);
}
.dlg__switch-label {
  font-weight: 600;
}
.dlg__switch-hint {
  font-size: var(--fs-14);
  color: var(--muted);
}
.switch {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  min-height: 44px;
  padding: 0 4px;
  border: 0;
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
  transition: background-color var(--dur-1) var(--ease);
}
.switch__thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 17px;
  height: 17px;
  border-radius: 50%;
  background: var(--muted);
  transition: transform var(--dur-1) var(--ease), background-color var(--dur-1) var(--ease);
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
</style>
