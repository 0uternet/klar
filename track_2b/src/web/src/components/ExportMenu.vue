<script setup lang="ts">
import { nextTick, onBeforeUnmount, ref, useId, watch } from 'vue'
import { ChevronDown, Download } from '@lucide/vue'
import type { ExportFormat, Scan } from '@/types'
import { EXPORT_FORMATS } from '@/types'
import { api } from '@/api'
import { t } from '@/i18n'
import { toast } from '@/stores/toast'

/** Menu button (WAI-ARIA APG pattern): arrows move, Enter/Space choose, Esc closes. */
const props = defineProps<{ scan: Scan }>()

const open = ref(false)
const menuId = useId()
const btnId = useId()
const root = ref<HTMLElement | null>(null)
const button = ref<HTMLButtonElement | null>(null)
const items = ref<HTMLElement[]>([])

async function show(focusIndex = 0) {
  open.value = true
  await nextTick()
  items.value[(focusIndex + EXPORT_FORMATS.length) % EXPORT_FORMATS.length]?.focus()
}
function hide(returnFocus = true) {
  open.value = false
  if (returnFocus) button.value?.focus()
}
function onButtonKey(e: KeyboardEvent) {
  if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    void show(0)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    void show(-1)
  }
}
function onItemKey(e: KeyboardEvent, i: number) {
  const n = EXPORT_FORMATS.length
  if (e.key === 'ArrowDown') items.value[(i + 1) % n]?.focus()
  else if (e.key === 'ArrowUp') items.value[(i - 1 + n) % n]?.focus()
  else if (e.key === 'Home') items.value[0]?.focus()
  else if (e.key === 'End') items.value[n - 1]?.focus()
  else if (e.key === 'Escape') hide()
  else if (e.key === 'Tab') hide(false)
  else return
  e.preventDefault()
}

async function choose(format: ExportFormat) {
  hide()
  try {
    await api().exportScan(props.scan, format)
    toast(t('export.done', { format: t(`export.${format}`) }), 'success')
  } catch {
    toast(t('export.failed'), 'danger', 3800, 'export', { label: t('toast.retry'), run: () => void choose(format) })
  }
}

function onDocClick(e: MouseEvent) {
  if (root.value && !root.value.contains(e.target as Node)) open.value = false
}
watch(open, (o) => (o ? document.addEventListener('click', onDocClick) : document.removeEventListener('click', onDocClick)))
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))
</script>

<template>
  <div ref="root" class="export">
    <button
      :id="btnId"
      ref="button"
      type="button"
      class="btn btn--secondary"
      aria-haspopup="menu"
      :aria-expanded="open"
      :aria-controls="menuId"
      @click="open ? hide() : show(0)"
      @keydown="onButtonKey"
    >
      <Download :size="16" aria-hidden="true" />
      {{ t('export.label') }}
      <ChevronDown :size="16" aria-hidden="true" class="export__chev" :class="{ 'is-open': open }" />
    </button>
    <ul v-show="open" :id="menuId" class="export__menu" role="menu" :aria-labelledby="btnId">
      <li v-for="(f, i) in EXPORT_FORMATS" :key="f" role="none">
        <button
          :ref="(el) => { if (el) items[i] = el as HTMLElement }"
          type="button"
          role="menuitem"
          tabindex="-1"
          class="export__item"
          @click="choose(f)"
          @keydown="onItemKey($event, i)"
        >
          <span class="export__fmt">{{ t(`export.${f}`) }}</span>
          <span class="export__desc">{{ t(`export.${f}.desc`) }}</span>
        </button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.export {
  position: relative;
}
.export__chev {
  transition: transform var(--dur-1) var(--ease);
}
.export__chev.is-open {
  transform: rotate(180deg);
}
.export__menu {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  z-index: 40;
  min-width: 260px;
  margin: 0;
  padding: 6px;
  list-style: none;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
  box-shadow: var(--shadow-overlay);
  animation: klar-fade-up var(--dur-1) var(--ease);
}
.export__item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  width: 100%;
  padding: 8px 12px;
  background: transparent;
  border: 0;
  border-radius: 6px;
  text-align: left;
}
.export__item:hover,
.export__item:focus-visible {
  background: var(--surface-2);
}
.export__item:focus-visible {
  outline-offset: -2px;
}
.export__fmt {
  font-weight: 600;
  font-size: var(--fs-14);
}
.export__desc {
  font-size: var(--fs-12);
  color: var(--muted);
}
</style>
