<script setup lang="ts">
import { computed, useId } from 'vue'
import { ChevronDown } from '@lucide/vue'
import type { Finding, Status, UiLang } from '@/types'
import type { FindingGroup } from '@/lib/group'
import { formatNumber, t } from '@/i18n'
import CriterionTag from '@/components/CriterionTag.vue'
import FindingCard from '@/components/FindingCard.vue'
import ShapeIcon from '@/components/ShapeIcon.vue'

/**
 * One criterion: its rows to review, then the rows with no problem, folded behind
 * a quiet toggle in the section header. Rows enter, leave and move with FLIP (list).
 */
const props = defineProps<{
  code: string
  name: string
  reviewRows: FindingGroup[]
  okRows: FindingGroup[]
  okCount: number
  okOpen: boolean
  okForced: boolean
  selectedKey: string | null
  scanLang: UiLang
  base?: string
  multiPage?: boolean
  panelId?: string
}>()
const emit = defineEmits<{ open: [f: Finding]; decide: [row: FindingGroup, status: Exclude<Status, 'to_review'>]; toggleOk: [code: string] }>()

const headingId = useId()
const listId = useId()
const okVisible = computed(() => props.okForced || props.okOpen)
const rows = computed(() => [...props.reviewRows, ...(okVisible.value ? props.okRows : [])])
const reviewCount = computed(() => props.reviewRows.reduce((n, r) => n + r.items.length, 0))
</script>

<template>
  <section class="sec" :aria-labelledby="headingId">
    <div class="sec__head">
      <h3 :id="headingId" class="sec__h">
        <CriterionTag :code="code" :name="name" show-level />
        <span v-if="reviewCount" class="sec__n tabular">{{ formatNumber(reviewCount) }}</span>
      </h3>
      <button v-if="okCount && !okForced" type="button" class="sec__ok" :aria-expanded="okOpen" :aria-controls="listId" @click="emit('toggleOk', code)">
        <ShapeIcon shape="circle" color="var(--green)" :size="8" />
        {{ t('report.okRow', { n: formatNumber(okCount) }) }}
        <ChevronDown :size="15" aria-hidden="true" class="sec__chev" />
      </button>
    </div>
    <TransitionGroup :id="listId" tag="ul" name="list" class="sec__list" role="list">
      <li v-for="row in rows" :key="row.key">
        <FindingCard
          :finding="row.lead"
          :items="row.items.length > 1 ? row.items : undefined"
          :row-key="row.key"
          :selected="selectedKey === row.key"
          :scan-lang="scanLang"
          :base="base"
          :multi-page="multiPage"
          :panel-id="panelId"
          @open="emit('open', $event)"
          @decide="emit('decide', row, $event)"
        />
      </li>
    </TransitionGroup>
  </section>
</template>

<style scoped>
.sec__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--s-2) var(--s-4);
  padding: 0 0 var(--s-2);
  border-bottom: 1px solid var(--ink);
}
.sec__h {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 4px var(--s-3);
  min-width: 0;
  font-size: var(--fs-16);
}
.sec__h :deep(.crit) {
  font-size: var(--fs-16);
}
.sec__h :deep(.crit__code) {
  font-size: var(--fs-14);
}
.sec__h :deep(.crit__name) {
  font-weight: 650;
  letter-spacing: -0.01em;
}
.sec__n {
  display: inline-grid;
  place-items: center;
  min-width: 22px;
  height: 20px;
  padding: 0 6px;
  border-radius: var(--r-pill);
  background: var(--surface-3);
  font-size: var(--fs-12);
  font-weight: 650;
  color: var(--ink);
}
.sec__ok {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 32px;
  padding: 0 8px;
  margin-right: -8px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--muted);
  font-size: var(--fs-14);
  font-weight: 550;
  transition: color var(--dur-1) var(--ease-out), background-color var(--dur-1) var(--ease-out);
}
.sec__ok:hover {
  color: var(--ink);
  background: var(--surface-2);
}
.sec__chev {
  transition: transform var(--dur-2) var(--ease-out);
}
.sec__ok[aria-expanded='true'] .sec__chev {
  transform: rotate(180deg);
}
.sec__list {
  position: relative;
  margin: 0;
  padding: 0;
}
.sec__list > li {
  border-bottom: 1px solid var(--line);
}
/* FLIP: a leaving row is taken out of the flow at once, so the rows below glide up. */
.sec__list > li.list-leave-active {
  position: absolute;
  left: 0;
  right: 0;
}
</style>
