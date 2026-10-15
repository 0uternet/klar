<script setup lang="ts">
import { ref, useId } from 'vue'
import { Search, X } from '@lucide/vue'
import type { Status } from '@/types'
import { formatNumber, locale, t, type MessageKey } from '@/i18n'
import { plainName } from '@/data/wcag'
import KeyboardHint from '@/components/KeyboardHint.vue'

/**
 * One compact toolbar: status (segmented, native radios: arrow keys work), search, criterion.
 * The result count and "Clear filters" appear only while a filter is active.
 */
const status = defineModel<Status | ''>('status', { required: true })
const q = defineModel<string>('q', { required: true })
const criterion = defineModel<string>('criterion', { required: true })
defineProps<{ criteria: string[]; active: boolean; shown: number; total: number; reason: string }>()
const emit = defineEmits<{ reset: []; clearReason: [] }>()

const OPTIONS: (Status | '')[] = ['', 'to_review', 'accepted', 'rejected']
const name = useId()
const input = ref<HTMLInputElement | null>(null)
defineExpose({ focusSearch: () => input.value?.focus() })
</script>

<template>
  <div class="tb" role="search" :aria-label="t('report.filters')">
    <fieldset class="seg">
      <legend class="sr-only">{{ t('filter.status') }}</legend>
      <label v-for="o in OPTIONS" :key="o || 'all'" class="seg__opt" :class="{ 'is-on': status === o }">
        <input v-model="status" type="radio" class="seg__input" :name="name" :value="o" />
        <span>{{ o ? t(`status.${o}`) : t('filter.all') }}</span>
      </label>
    </fieldset>

    <div class="tb__search">
      <label for="rep-search" class="sr-only">{{ t('report.search') }}</label>
      <Search :size="15" aria-hidden="true" class="tb__icon" />
      <input
        id="rep-search"
        ref="input"
        v-model="q"
        type="search"
        class="tb__input"
        :placeholder="t('report.searchPlaceholder')"
        autocomplete="off"
        @keydown.esc.stop="q = ''"
      />
      <span class="tb__key"><KeyboardHint :keys="['/']" /></span>
    </div>

    <div class="tb__crit">
      <label for="f-crit" class="sr-only">{{ t('filter.criterion') }}</label>
      <select id="f-crit" v-model="criterion" class="tb__select" :class="{ 'is-set': criterion }">
        <option value="">{{ t('filter.allCriteria') }}</option>
        <option v-for="c in criteria" :key="c" :value="c">{{ c }} {{ plainName(c, locale) }}</option>
      </select>
    </div>

    <span v-if="reason" class="tb__chip">
      <span class="tb__chip-text">{{ t(`reason.${reason}` as MessageKey) }}</span>
      <button type="button" class="tb__chip-x" :aria-label="t('notes.clearFilter')" @click="emit('clearReason')"><X :size="14" aria-hidden="true" /></button>
    </span>

    <div class="tb__end">
      <span class="tb__count tabular" role="status">{{ active ? t('report.showing', { shown: formatNumber(shown), total: formatNumber(total) }) : '' }}</span>
      <Transition name="fade">
        <button v-if="active" type="button" class="tb__reset" @click="emit('reset')"><X :size="14" aria-hidden="true" />{{ t('report.reset') }}</button>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.tb {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-2) var(--s-3);
}
/* Segmented control */
.seg {
  display: inline-flex;
  margin: 0;
  padding: 3px;
  min-width: 0;
  border: 0;
  border-radius: var(--r-control);
  background: var(--surface-2);
  box-shadow: inset 0 0 0 1px var(--line);
}
.seg__opt {
  position: relative;
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 6px;
  font-size: var(--fs-14);
  font-weight: 550;
  color: var(--muted);
  white-space: nowrap;
  cursor: pointer;
  transition: color var(--dur-1) var(--ease-out), background-color var(--dur-2) var(--ease-out), box-shadow var(--dur-2) var(--ease-out);
}
.seg__opt:hover {
  color: var(--ink);
}
.seg__opt.is-on {
  background: var(--surface);
  color: var(--ink);
  box-shadow: 0 0 0 1px var(--control-border), 0 1px 2px rgba(15, 17, 21, 0.06);
}
.seg__input {
  position: absolute;
  opacity: 0;
  inset: 0;
  margin: 0;
  cursor: pointer;
}
.seg__opt:has(.seg__input:focus-visible) {
  outline: 2px solid var(--blue);
  outline-offset: 1px;
}
/* Search */
.tb__search {
  position: relative;
  flex: 1 1 200px;
  min-width: 0;
  max-width: 340px;
}
.tb__icon {
  position: absolute;
  left: 11px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--muted);
  pointer-events: none;
}
.tb__input,
.tb__select {
  display: block;
  width: 100%;
  min-height: 38px;
  padding: 0 12px;
  background: var(--surface);
  color: var(--ink);
  border: 1px solid var(--control-border);
  border-radius: var(--r-control);
  font-size: var(--fs-14);
  transition: border-color var(--dur-1) var(--ease-out), box-shadow var(--dur-1) var(--ease-out);
}
.tb__input {
  padding-left: 34px;
  padding-right: 36px;
}
.tb__input::placeholder {
  color: var(--muted);
  opacity: 1;
}
.tb__input:hover,
.tb__select:hover {
  border-color: var(--ink);
}
.tb__key {
  position: absolute;
  right: 9px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}
.tb__crit {
  flex: 0 1 220px;
  min-width: 0;
}
.tb__select {
  appearance: none;
  padding-right: 30px;
  text-overflow: ellipsis;
  background-image: linear-gradient(45deg, transparent 50%, currentColor 50%), linear-gradient(135deg, currentColor 50%, transparent 50%);
  background-position: calc(100% - 16px) 50%, calc(100% - 11px) 50%;
  background-size: 5px 5px, 5px 5px;
  background-repeat: no-repeat;
  cursor: pointer;
}
.tb__select.is-set {
  border-color: var(--ink);
  box-shadow: inset 0 0 0 1px var(--ink);
  font-weight: 600;
}
.tb__chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  max-width: 100%;
  min-height: 32px;
  padding: 0 4px 0 12px;
  border-radius: var(--r-pill);
  background: var(--blue-tint);
  font-size: var(--fs-14);
  font-weight: 600;
}
.tb__chip-text {
  min-width: 0;
  overflow-wrap: anywhere;
}
.tb__chip-x {
  display: grid;
  place-items: center;
  flex: none;
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--ink);
}
.tb__chip-x:hover {
  background: var(--surface);
}
.tb__end {
  display: flex;
  align-items: center;
  gap: var(--s-2);
  margin-left: auto;
}
.tb__count {
  font-size: var(--fs-14);
  color: var(--muted);
}
.tb__count:empty {
  display: none;
}
.tb__reset {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 0 10px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--ink);
  font-size: var(--fs-14);
  font-weight: 600;
}
.tb__reset:hover {
  background: var(--surface-2);
}
@media (max-width: 640px) {
  .seg {
    display: flex;
    width: 100%;
  }
  .seg__opt {
    flex: 1 1 auto;
    justify-content: center;
    padding: 0 6px;
  }
  .tb__search,
  .tb__crit {
    flex: 1 1 100%;
    max-width: none;
  }
}
@media (max-width: 380px) {
  .seg {
    flex-wrap: wrap;
  }
  .seg__opt {
    padding: 0 4px;
    font-size: 0.8125rem;
  }
}
@media (forced-colors: active) {
  .tb__select {
    appearance: auto;
    background-image: none;
  }
  .seg__opt.is-on {
    outline: 2px solid Highlight;
  }
  .seg__input {
    opacity: 0;
  }
}
</style>
