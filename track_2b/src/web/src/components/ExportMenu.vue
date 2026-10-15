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
      class="export__btn"
      aria-haspopup="menu"
      :aria-expanded="open"
      :aria-controls="menuId"
      @click="open ? hide() : show(0)"
      @keydown="onButtonKey"
    >
      <Download :size="16" aria-hidden="true" />
      {{ t('export.label') }}
      <ChevronDown :size="15" aria-hidden="true" class="export__chev" :class="{ 'is-open': open }" />
    </button>
    <Transition name="fade-rise">
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
    </Transition>
  </div>
</template>

<style scoped>
.export {
  position: relative;
}
.export__btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 38px;
  padding: 0 10px 0 12px;
  border: 1px solid var(--line);
  border-radius: var(--r-control);
  background: transparent;
  color: var(--ink);
  font-size: var(--fs-14);
  font-weight: 600;
  white-space: nowrap;
  transition: background-color var(--dur-1) var(--ease-out), border-color var(--dur-1) var(--ease-out);
}
.export__btn:hover,
.export__btn[aria-expanded='true'] {
  background: var(--surface-2);
  border-color: var(--control-border);
}
.export__chev {
  color: var(--muted);
  transition: transform var(--dur-2) var(--ease-out);
}
.export__chev.is-open {
  transform: rotate(180deg);
}
.export__menu {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  z-index: 40;
  min-width: 300px;
  max-width: calc(100vw - 2 * var(--page-pad));
  margin: 0;
  padding: 4px;
  list-style: none;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
  box-shadow: var(--shadow-overlay);
  transform-origin: top right;
}
.export__item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  width: 100%;
  padding: 7px 10px;
  background: transparent;
  border: 0;
  border-radius: 6px;
  text-align: left;
  color: var(--ink);
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
@media (max-width: 640px) {
  .export__menu {
    right: auto;
    left: 0;
    transform-origin: top left;
  }
}
</style>
