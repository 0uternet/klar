<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft, ChevronDown, ExternalLink, Search, X } from '@lucide/vue'
import type { Scan } from '@/types'
import { STORAGE } from '@/config'
import { locale, polish, t, tp } from '@/i18n'
import { CRITERIA, PRINCIPLES, en301549, understandingUrl, type WcagCriterion } from '@/data/wcag'
import { cellStatus, criteriaError, criteriaInfo, loadCriteria, needsPerson } from '@/stores/criteria'
import { guideFor, type Guide } from '@/data/human-guides'
import { ensureBooted, lastScanId } from '@/stores/app'
import { loadScan } from '@/stores/scans'
import { shortUrl } from '@/lib/format'
import { useDocumentTitle } from '@/composables/useDocumentTitle'

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

/** The list waits for the registry, so it never flashes all 50 criteria first. */
const ready = computed(() => criteriaInfo.value !== null || criteriaError.value || !!scan.value?.coverage)

/** Everything Klar. does not pre-check: human by nature, or not implemented yet (from the registry). */
const kindOf = (c: WcagCriterion) => cellStatus(c.code, scan.value).kind
const human = computed(() => CRITERIA.filter((c) => needsPerson(c.code, scan.value)))
const experimental = computed(() => CRITERIA.filter((c) => kindOf(c) === 'experimental'))
const all = computed(() => [...human.value, ...experimental.value])

const guide = (c: WcagCriterion): Guide => guideFor(c.code, locale.value)

/* Filter: code, plain name, official title and the one-line check, accents ignored. */
const query = ref('')
const norm = (s: string) => s.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase()
const haystack = (c: WcagCriterion) => norm(`${c.code} ${c.plain[locale.value]} ${c.title} ${guide(c).steps[0] ?? ''}`)
const tokens = computed(() => norm(query.value).split(/\s+/).filter(Boolean))
const matches = (c: WcagCriterion) => tokens.value.every((tok) => haystack(c).includes(tok))
const visible = computed(() => all.value.filter(matches))

interface Group {
  key: string
  num: string | null
  title: string
  lede: string | null
  items: WcagCriterion[]
}
const groups = computed<Group[]>(() => {
  const shown = new Set(visible.value.map((c) => c.code))
  const out: Group[] = PRINCIPLES.map((p) => ({
    key: String(p),
    num: String(p),
    title: t(`principle.${p}`),
    lede: null,
    items: human.value.filter((c) => c.principle === p && shown.has(c.code)),
  }))
  out.push({
    key: 'exp',
    num: null,
    title: t('human.experimental'),
    lede: t('human.experimentalLede', { n: experimental.value.length }),
    items: experimental.value.filter((c) => shown.has(c.code)),
  })
  return out.filter((g) => g.items.length)
})

/* Disclosure: one guide or all of them. */
const open = ref<Set<string>>(new Set())
const isOpen = (code: string) => open.value.has(code)
function toggleOpen(code: string) {
  const s = new Set(open.value)
  if (s.has(code)) s.delete(code)
  else s.add(code)
  open.value = s
}
const allOpen = computed(() => visible.value.length > 0 && visible.value.every((c) => open.value.has(c.code)))
function toggleAll() {
  open.value = allOpen.value ? new Set() : new Set(visible.value.map((c) => c.code))
}
const panelId = (code: string) => `hg-${code.replace(/\./g, '-')}`

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
function toggleCheck(code: string) {
  const s = new Set(checked.value)
  if (s.has(code)) s.delete(code)
  else s.add(code)
  checked.value = s
}
const done = computed(() => all.value.filter((c) => checked.value.has(c.code)).length)

/** Automatic rules (axe-core) may hit a criterion Klar. does not pre-check. */
function ruleHits(code: string): number {
  return scan.value?.findings.filter((f) => f.criterion === code && (f.outcome === 'failed' || f.outcome === 'cantTell')).length ?? 0
}

/* Rows rise in once, on the first render only; filtering then uses the list transition. */
const intro = ref(true)
onMounted(() => window.setTimeout(() => (intro.value = false), 1200))
</script>

<template>
  <div class="container human">
    <header class="head">
      <RouterLink v-if="scanUrl && scanId" class="head__back m-rise" :to="{ name: 'report', params: { id: scanId } }">
        <ArrowLeft :size="16" aria-hidden="true" />{{ t('human.backTo', { url: shortUrl(scanUrl) }) }}
      </RouterLink>
      <h1 class="h1 head__title m-rise" style="--i: 1" tabindex="-1">{{ t('human.title') }}</h1>
      <p class="lede m-rise" style="--i: 2">{{ t('human.lede', { n: ready ? all.length : '…' }) }}</p>
    </header>

    <div class="tools m-rise" style="--i: 3">
      <div class="search">
        <label for="human-filter" class="sr-only">{{ t('human.search') }}</label>
        <Search class="search__icon" :size="16" aria-hidden="true" />
        <input
          id="human-filter"
          v-model="query"
          class="field search__input"
          type="search"
          autocomplete="off"
          spellcheck="false"
          :placeholder="t('human.searchPlaceholder')"
          @keydown.esc="query = ''"
        />
      </div>
      <div class="progress">
        <p class="progress__text">
          <span class="tabular">{{ t('human.progress', { done, total: all.length }) }}</span>
          <span class="progress__note">{{ t('human.stored') }}</span>
        </p>
        <span class="progress__bar" aria-hidden="true"><span :style="{ transform: `scaleX(${all.length ? done / all.length : 0})` }" /></span>
      </div>
      <button type="button" class="btn btn--ghost btn--sm press tools__all" :disabled="!visible.length" @click="toggleAll">
        <ChevronDown class="tools__all-icon" :class="{ 'is-up': allOpen }" :size="16" aria-hidden="true" />{{ allOpen ? t('human.collapseAll') : t('human.expandAll') }}
      </button>
    </div>
    <p class="sr-only" role="status">{{ query.trim() ? tp('human.results', visible.length) : '' }}</p>

    <ul v-if="!ready" class="rows rows--loading" role="list" :aria-label="t('common.loading')">
      <li v-for="i in 6" :key="i" class="skel-row"><span class="skel skel-row__a" /><span class="skel skel-row__b" /></li>
    </ul>

    <div v-else-if="!visible.length" class="empty m-rise">
      <p>{{ t('human.noMatch', { q: query.trim() }) }}</p>
      <button type="button" class="btn btn--secondary btn--sm press" @click="query = ''">
        <X :size="16" aria-hidden="true" />{{ t('human.clearSearch') }}
      </button>
    </div>

    <section v-for="(g, gi) in groups" :key="g.key" v-reveal="gi" class="group" :aria-labelledby="`hp-${g.key}`">
      <h2 :id="`hp-${g.key}`" class="group__title">
        <span v-if="g.num" class="group__num mono">{{ g.num }}</span>{{ g.title }}<span class="group__count tabular" aria-hidden="true">{{ g.items.length }}</span>
      </h2>
      <p v-if="g.lede" class="group__lede">{{ g.lede }}</p>
      <TransitionGroup tag="ul" name="list" class="rows" role="list">
        <li
          v-for="(c, i) in g.items"
          :key="c.code"
          class="row"
          :class="{ 'is-done': checked.has(c.code), 'is-open': isOpen(c.code), 'm-rise': intro }"
          :style="intro ? { '--i': Math.min(i, 10) } : undefined"
        >
          <div class="row__line">
            <label class="tick">
              <input type="checkbox" class="tick__input" :checked="checked.has(c.code)" @change="toggleCheck(c.code)" />
              <span class="tick__box" aria-hidden="true">
                <svg v-if="checked.has(c.code)" viewBox="0 0 16 16" width="14" height="14" fill="none">
                  <path class="m-draw" pathLength="1" d="M3.5 8.4 6.6 11.4 12.6 4.8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                </svg>
              </span>
              <span class="sr-only">{{ t('human.mark', { name: `${c.code} ${c.plain[locale]}` }) }}</span>
            </label>
            <button
              type="button"
              class="row__btn"
              :aria-expanded="isOpen(c.code)"
              :aria-controls="panelId(c.code)"
              @click="toggleOpen(c.code)"
            >
              <span class="row__head">
                <code class="row__code">{{ c.code }}</code>
                <span class="row__name">{{ c.plain[locale] }}</span>
                <span class="row__level">{{ c.level }}</span>
                <span v-if="kindOf(c) === 'planned'" class="row__tag">{{ t('human.tag.planned') }}</span>
                <span v-if="scan && ruleHits(c.code)" class="row__tag row__tag--flag">{{ tp('human.flagged', ruleHits(c.code)) }}</span>
              </span>
              <span class="row__sum">{{ polish(guide(c).steps[0] ?? '') }}</span>
              <ChevronDown class="row__chev" :size="18" aria-hidden="true" />
            </button>
          </div>
          <div :id="panelId(c.code)" class="m-collapse" :data-open="isOpen(c.code)">
            <div :inert="!isOpen(c.code)">
              <div class="panel">
                <ol v-if="guide(c).steps.length > 1" class="panel__steps">
                  <li v-for="(s, k) in guide(c).steps.slice(1)" :key="k">{{ polish(s) }}</li>
                </ol>
                <p class="panel__why"><span class="panel__label">{{ t('human.why') }}</span> {{ polish(guide(c).why) }}</p>
                <p class="panel__links">
                  <a :href="understandingUrl(c.code)" target="_blank" rel="noopener noreferrer">
                    {{ t('human.guidance', { code: c.code }) }}<ExternalLink :size="13" aria-hidden="true" /><span class="sr-only"> {{ t('finding.newTab') }}</span>
                  </a>
                  <RouterLink v-if="scan && ruleHits(c.code)" :to="{ name: 'report', params: { id: scan.id }, query: { criterion: c.code } }">
                    {{ t('human.openInReport') }}
                  </RouterLink>
                </p>
                <p class="panel__meta"><span lang="en">{{ c.title }}</span> · EN 301 549 {{ en301549(c.code) }}</p>
              </div>
            </div>
          </div>
        </li>
      </TransitionGroup>
    </section>
  </div>
</template>

<style scoped>
.human {
  padding-top: var(--s-8);
  padding-bottom: var(--s-8);
}

/* ---- Head ------------------------------------------------------------- */
.head {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--s-4);
  max-width: 760px;
}
.head__title {
  letter-spacing: -0.035em;
}
.head__back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  font-size: var(--fs-14);
  font-weight: 600;
  text-decoration: none;
}
.head__back:hover {
  text-decoration: underline;
}

/* ---- Tools: filter, progress, expand all ------------------------------ */
.tools {
  display: grid;
  grid-template-columns: minmax(0, 360px) 1fr auto;
  align-items: center;
  gap: var(--s-5);
  margin-top: var(--s-7);
  padding-bottom: var(--s-5);
  border-bottom: 1px solid var(--line);
}
.search {
  position: relative;
}
.search__icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--muted);
  pointer-events: none;
}
.search__input {
  min-height: 44px;
  padding-left: 38px;
  font-size: var(--fs-16);
  transition: border-color var(--dur-2) var(--ease-out), box-shadow var(--dur-2) var(--ease-out);
}
.search__input:hover {
  border-color: var(--ink);
}
.progress {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 320px;
  justify-self: end;
  width: 100%;
}
.progress__text {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  column-gap: var(--s-3);
  font-size: var(--fs-14);
  font-weight: 600;
}
.progress__note {
  font-size: var(--fs-12);
  font-weight: 400;
  color: var(--muted);
}
.progress__bar {
  display: block;
  height: 4px;
  background: var(--surface-3);
  border-radius: 2px;
  overflow: hidden;
}
.progress__bar span {
  display: block;
  height: 100%;
  background: var(--green);
  transform-origin: left;
  transition: transform var(--dur-4) var(--ease-out);
}
.tools__all {
  color: var(--ink);
}
.tools__all-icon {
  transition: transform var(--dur-3) var(--ease-out);
}
.tools__all-icon.is-up {
  transform: rotate(180deg);
}

/* ---- Empty filter ----------------------------------------------------- */
.empty {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--s-4);
  padding: var(--s-7) 0;
  color: var(--muted);
}

/* ---- Groups ----------------------------------------------------------- */
.group {
  margin-top: var(--s-7);
}
.group__title {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding-bottom: var(--s-3);
  font-size: var(--fs-20);
  font-weight: 650;
  letter-spacing: -0.02em;
}
.group__num {
  color: var(--muted);
  font-size: var(--fs-14);
  font-weight: 500;
}
.group__count {
  margin-left: auto;
  font-size: var(--fs-14);
  font-weight: 500;
  color: var(--muted);
}
.group__lede {
  margin-bottom: var(--s-3);
  font-size: var(--fs-14);
  color: var(--muted);
}

/* ---- Rows ------------------------------------------------------------- */
.rows {
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--line);
}
.row {
  position: relative;
  border-bottom: 1px solid var(--line);
}
.row::before {
  /* Done marker: a green rule that grows in from the left edge. */
  content: '';
  position: absolute;
  left: 0;
  top: -1px;
  bottom: -1px;
  width: 2px;
  background: var(--green);
  transform: scaleY(0);
  transform-origin: top;
  transition: transform var(--dur-3) var(--ease-out);
}
.row.is-done::before {
  transform: scaleY(1);
}
.row__line {
  display: flex;
  align-items: flex-start;
  gap: var(--s-2);
  padding-left: var(--s-2);
}

/* Tick: a native checkbox under a drawn box (keyboard and forced colours keep working). */
.tick {
  position: relative;
  flex: none;
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  margin-top: 10px;
  cursor: pointer;
}
.tick__input {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  margin: 0;
  opacity: 0;
  cursor: pointer;
}
.tick__box {
  display: grid;
  place-items: center;
  width: 20px;
  height: 20px;
  border: 1.5px solid var(--control-border);
  border-radius: 6px;
  background: var(--surface);
  color: var(--on-ink);
  transition: background-color var(--dur-2) var(--ease-out), border-color var(--dur-2) var(--ease-out), transform var(--dur-1) var(--ease-out);
}
.tick:hover .tick__box {
  border-color: var(--ink);
}
.tick:active .tick__box {
  transform: scale(0.92);
}
.tick__input:checked + .tick__box {
  background: var(--green);
  border-color: var(--green);
}
.tick__input:focus-visible + .tick__box {
  outline: 2px solid var(--blue);
  outline-offset: 2px;
}

.row__btn {
  position: relative;
  flex: 1;
  min-width: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  column-gap: var(--s-4);
  row-gap: 4px;
  padding: var(--s-4) var(--s-3) var(--s-4) var(--s-2);
  background: none;
  border: 0;
  border-radius: var(--r-control);
  color: inherit;
  text-align: left;
  transition: background-color var(--dur-2) var(--ease-out);
}
.row__btn:focus-visible {
  outline-offset: -2px;
}
@media (hover: hover) {
  .row__btn:hover {
    background: var(--surface-2);
  }
  .row__btn:hover .row__chev {
    color: var(--ink);
  }
}
.row__head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  column-gap: 10px;
  row-gap: 4px;
  min-width: 0;
}
.row__code {
  font-size: var(--fs-14);
  font-weight: 500;
  color: var(--muted);
  font-variant-numeric: tabular-nums;
  min-width: 6ch;
}
.row__name {
  font-size: var(--fs-16);
  font-weight: 600;
  letter-spacing: -0.01em;
}
.row__level {
  padding: 0 6px;
  border: 1px solid var(--control-border);
  border-radius: 4px;
  font-size: var(--fs-12);
  font-weight: 600;
  line-height: 18px;
  color: var(--muted);
}
.row__tag {
  padding: 0 8px;
  border: 1px dashed var(--control-border);
  border-radius: var(--r-pill);
  font-size: var(--fs-12);
  font-weight: 500;
  line-height: 20px;
  color: var(--muted);
}
.row__tag--flag {
  border-style: solid;
  border-color: var(--amber);
  color: var(--amber);
}
.row__sum {
  grid-column: 1;
  font-size: var(--fs-14);
  color: var(--muted);
  text-wrap: pretty;
}
.row__chev {
  grid-column: 2;
  grid-row: 1 / span 2;
  align-self: center;
  color: var(--muted);
  transition: transform var(--dur-3) var(--ease-out), color var(--dur-2) var(--ease-out);
}
.row.is-open .row__chev {
  transform: rotate(180deg);
}

/* Expanded guide, aligned with the row text. */
.panel {
  display: flex;
  flex-direction: column;
  gap: var(--s-3);
  padding: 0 var(--s-6) var(--s-5) calc(var(--s-2) + 40px + var(--s-2) + var(--s-2));
  max-width: 84ch;
}
.panel__steps {
  margin: 0;
  padding-left: 1.4em;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: var(--fs-14);
}
.panel__steps li::marker {
  font-family: var(--font-mono);
  font-size: var(--fs-12);
  font-weight: 600;
  color: var(--muted);
}
.panel__why {
  font-size: var(--fs-14);
  color: var(--muted);
}
.panel__label {
  font-weight: 600;
  color: var(--ink);
}
.panel__label::after {
  content: ':';
}
.panel__links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--s-2) var(--s-5);
  font-size: var(--fs-14);
  font-weight: 600;
}
.panel__links a {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-height: 24px;
}
.panel__meta {
  font-size: var(--fs-12);
  color: var(--muted);
}

/* Loading */
.skel-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: var(--s-4) var(--s-2) var(--s-4) 56px;
  border-bottom: 1px solid var(--line);
}
.skel-row__a {
  width: min(320px, 70%);
  height: 18px;
}
.skel-row__b {
  width: min(520px, 90%);
  height: 14px;
}

@media (max-width: 900px) {
  .tools {
    grid-template-columns: 1fr auto;
  }
  .search {
    grid-column: 1 / -1;
  }
  .progress {
    justify-self: start;
  }
}
@media (max-width: 560px) {
  .human {
    padding-top: var(--s-6);
  }
  .tools {
    margin-top: var(--s-6);
    gap: var(--s-4);
  }
  .row__line {
    padding-left: 0;
  }
  .row__btn {
    padding-right: var(--s-2);
    column-gap: var(--s-2);
  }
  .panel {
    padding-left: calc(40px + var(--s-2) + var(--s-2));
    padding-right: var(--s-2);
  }
}
@media (forced-colors: active) {
  .tick__box {
    border-color: CanvasText;
  }
  .tick__input:checked + .tick__box {
    background: Highlight;
    border-color: Highlight;
    color: HighlightText;
  }
  .row::before {
    background: Highlight;
  }
  .progress__bar {
    border: 1px solid CanvasText;
  }
  .progress__bar span {
    background: Highlight;
  }
}
</style>
