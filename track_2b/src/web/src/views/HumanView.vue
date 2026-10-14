<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, ExternalLink } from '@lucide/vue'
import type { Scan } from '@/types'
import { STORAGE } from '@/config'
import { locale, polish, t } from '@/i18n'
import { CRITERIA, PRINCIPLES, understandingUrl, type WcagCriterion } from '@/data/wcag'
import { cellStatus, loadCriteria, needsPerson } from '@/stores/criteria'
import { guideFor } from '@/data/human-guides'
import { ensureBooted, lastScanId } from '@/stores/app'
import { loadScan } from '@/stores/scans'
import { shortUrl } from '@/lib/format'
import { useDocumentTitle } from '@/composables/useDocumentTitle'
import CriterionTag from '@/components/CriterionTag.vue'

const route = useRoute()
useDocumentTitle(() => t('human.docTitle'))

const scan = ref<Scan | null>(null)
const scanUrl = computed(() => scan.value?.url ?? null)
const scanId = computed(() => (typeof route.query.scan === 'string' ? route.query.scan : lastScanId.value))

onMounted(async () => {
  await ensureBooted()
  void loadCriteria()
  if (scanId.value) {
    try {
      scan.value = await loadScan(scanId.value)
    } catch {
      /* the registry alone decides */
    }
  }
})

/** Everything Klar. does not pre-check: human by nature, or not implemented yet (from the registry). */
const kindOf = (c: WcagCriterion) => cellStatus(c.code, scan.value).kind
const human = computed(() => CRITERIA.filter((c) => needsPerson(c.code, scan.value)))
const experimental = computed(() => CRITERIA.filter((c) => kindOf(c) === 'experimental'))
const byPrinciple = computed(() =>
  PRINCIPLES.map((p) => ({ p, items: human.value.filter((c) => c.principle === p) })).filter((g) => g.items.length),
)

/* Per-viewer convenience: ticks live in this browser only. */
function readChecked(): string[] {
  try {
    return JSON.parse(localStorage.getItem(STORAGE.humanChecks) ?? '[]') as string[]
  } catch {
    return []
  }
}
const checked = ref<Set<string>>(new Set(readChecked()))
watch(
  checked,
  (s) => {
    try {
      localStorage.setItem(STORAGE.humanChecks, JSON.stringify([...s]))
    } catch {
      /* storage unavailable */
    }
  },
  { deep: true },
)
function toggle(code: string) {
  const s = new Set(checked.value)
  if (s.has(code)) s.delete(code)
  else s.add(code)
  checked.value = s
}
/** UX-16: automatic rules (axe-core) may hit a criterion Klar. does not pre-check. */
function ruleHits(code: string): number {
  return scan.value?.findings.filter((f) => f.criterion === code && (f.outcome === 'failed' || f.outcome === 'cantTell')).length ?? 0
}
const all = computed(() => [...human.value, ...experimental.value])
const done = computed(() => all.value.filter((c) => checked.value.has(c.code)).length)
</script>

<template>
  <div class="container human">
    <header class="human__head">
      <p class="eyebrow">{{ t('human.eyebrow') }}</p>
      <h1 class="h1" tabindex="-1">{{ t('human.title') }}</h1>
      <p class="lede">{{ t('human.lede', { n: human.length }) }}</p>
      <div class="human__meta">
        <p class="muted small">
          {{ scanUrl ? t('human.basedOn', { url: shortUrl(scanUrl) }) : t('human.basedOnDefault') }}
          <RouterLink v-if="scanUrl && scanId" :to="{ name: 'report', params: { id: scanId } }" class="human__back">
            <ArrowLeft :size="14" aria-hidden="true" />{{ t('human.backToReport') }}
          </RouterLink>
        </p>
        <div class="human__progress">
          <span class="tabular">{{ t('human.progress', { done, total: all.length }) }}</span>
          <span class="human__bar" aria-hidden="true"><span :style="{ transform: `scaleX(${all.length ? done / all.length : 0})` }" /></span>
          <span class="muted xsmall">{{ t('human.stored') }}</span>
        </div>
      </div>
    </header>

    <section v-for="g in byPrinciple" :key="g.p" class="human__group" :aria-labelledby="`hp-${g.p}`">
      <h2 :id="`hp-${g.p}`" class="human__h2"><span class="mono">{{ g.p }}</span> {{ t(`principle.${g.p}`) }}</h2>
      <ul class="cards" role="list">
        <li v-for="c in g.items" :key="c.code" class="card" :class="{ 'is-done': checked.has(c.code) }">
          <div class="card__head">
            <CriterionTag :code="c.code" tooltip show-level />
            <label class="card__check">
              <input type="checkbox" :checked="checked.has(c.code)" @change="toggle(c.code)" />
              <span>{{ t('human.mark') }}<span class="sr-only">: {{ c.code }} {{ c.plain[locale] }}</span></span>
            </label>
          </div>
          <span class="card__tag" :class="{ 'card__tag--planned': kindOf(c) === 'planned' }">
            {{ kindOf(c) === 'planned' ? t('human.tag.planned') : t('human.tag.human') }}
          </span>
          <RouterLink v-if="scan && ruleHits(c.code)" class="card__hits" :to="{ name: 'report', params: { id: scan.id }, query: { criterion: c.code } }">
            {{ t('human.ruleHits', { n: ruleHits(c.code) }) }}
          </RouterLink>
          <p class="card__why"><span class="card__label">{{ t('human.why') }}</span> {{ polish(guideFor(c.code, locale).why) }}</p>
          <p class="card__label">{{ t('human.steps') }}</p>
          <ol class="card__steps">
            <li v-for="(s, i) in guideFor(c.code, locale).steps" :key="i">{{ polish(s) }}</li>
          </ol>
          <a class="card__link" :href="understandingUrl(c.code)" target="_blank" rel="noopener noreferrer">
            {{ t('human.guidance', { code: c.code }) }}<ExternalLink :size="13" aria-hidden="true" /><span class="sr-only"> {{ t('finding.newTab') }}</span>
          </a>
        </li>
      </ul>
    </section>

    <section v-if="experimental.length" class="human__group" aria-labelledby="hp-exp">
      <h2 id="hp-exp" class="human__h2">{{ t('human.experimental') }}</h2>
      <p class="muted human__exp-lede">{{ t('human.experimentalLede', { n: experimental.length }) }}</p>
      <ul class="cards" role="list">
        <li v-for="c in experimental" :key="c.code" class="card card--exp" :class="{ 'is-done': checked.has(c.code) }">
          <div class="card__head">
            <CriterionTag :code="c.code" tooltip show-level />
            <label class="card__check">
              <input type="checkbox" :checked="checked.has(c.code)" @change="toggle(c.code)" />
              <span>{{ t('human.mark') }}<span class="sr-only">: {{ c.code }} {{ c.plain[locale] }}</span></span>
            </label>
          </div>
          <p class="card__why"><span class="card__label">{{ t('human.why') }}</span> {{ polish(guideFor(c.code, locale).why) }}</p>
          <p class="card__label">{{ t('human.steps') }}</p>
          <ol class="card__steps">
            <li v-for="(s, i) in guideFor(c.code, locale).steps" :key="i">{{ polish(s) }}</li>
          </ol>
          <a class="card__link" :href="understandingUrl(c.code)" target="_blank" rel="noopener noreferrer">
            {{ t('human.guidance', { code: c.code }) }}<ExternalLink :size="13" aria-hidden="true" /><span class="sr-only"> {{ t('finding.newTab') }}</span>
          </a>
        </li>
      </ul>
    </section>
  </div>
</template>

<style scoped>
.human {
  padding-top: var(--s-8);
}
.human__head {
  display: flex;
  flex-direction: column;
  gap: var(--s-4);
  padding-bottom: var(--s-6);
  border-bottom: 1px solid var(--line);
}
.human__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--s-4);
}
.human__back {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-left: var(--s-2);
  font-weight: 600;
}
.human__progress {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 240px;
  font-size: var(--fs-14);
  font-weight: 600;
}
.human__bar {
  display: block;
  height: 4px;
  background: var(--surface-3);
  border-radius: 2px;
  overflow: hidden;
}
.human__bar span {
  display: block;
  height: 100%;
  background: var(--green);
  transform-origin: left;
  transition: transform var(--dur-3) var(--ease);
}
.human__group {
  margin-top: var(--s-7);
}
.human__h2 {
  margin-bottom: var(--s-4);
  font-size: var(--fs-24);
  font-weight: 700;
  letter-spacing: -0.02em;
}
.human__h2 .mono {
  color: var(--muted);
  margin-right: 6px;
}
.human__exp-lede {
  margin: calc(-1 * var(--s-2)) 0 var(--s-4);
}
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 340px), 1fr));
  gap: var(--s-4);
  margin: 0;
  padding: 0;
}
.card {
  display: flex;
  flex-direction: column;
  gap: var(--s-3);
  padding: var(--s-5);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
  transition: border-color var(--dur-1) var(--ease);
}
.card--exp {
  border-style: dashed;
  border-color: var(--control-border);
}
.card.is-done {
  border-color: var(--green);
  box-shadow: inset 3px 0 0 var(--green);
}
.card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--s-3);
}
.card__check {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  font-size: var(--fs-14);
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
}
.card__check input {
  width: 18px;
  height: 18px;
  margin: 0;
  accent-color: var(--green);
  cursor: pointer;
}
.card__hits {
  align-self: flex-start;
  font-size: var(--fs-14);
  font-weight: 600;
}
.card__tag {
  align-self: flex-start;
  padding: 2px 10px;
  border: 1px solid var(--control-border);
  border-radius: var(--r-pill);
  font-size: var(--fs-12);
  font-weight: 600;
  color: var(--ink);
}
.card__tag--planned {
  border-style: dashed;
  color: var(--muted);
}
.card__why {
  font-size: var(--fs-14);
  color: var(--muted);
}
.card__label {
  display: block;
  margin-bottom: 2px;
  font-size: var(--fs-14);
  font-weight: 700;
  color: var(--ink);
}
.card__steps {
  margin: 0;
  padding-left: 1.3em;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: var(--fs-14);
}
.card__steps li::marker {
  font-family: var(--font-mono);
  font-weight: 700;
  color: var(--muted);
}
.card__link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: auto;
  padding-top: var(--s-2);
  font-size: var(--fs-14);
  font-weight: 600;
}
</style>
