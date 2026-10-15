<script setup lang="ts">
import { computed, ref, useId } from 'vue'
import { ChevronDown, ExternalLink } from '@lucide/vue'
import type { Scan } from '@/types'
import { formatDate, formatNumber, languageName, locale, t, tp } from '@/i18n'
import { MODE_COLOR, MODE_SHAPE, prettyModel } from '@/lib/format'
import type { RunNote } from '@/lib/notes'
import ExportMenu from '@/components/ExportMenu.vue'
import RunNotes from '@/components/RunNotes.vue'
import ShapeIcon from '@/components/ShapeIcon.vue'
import { health } from '@/stores/app'

/**
 * Report header: the page name, one line of honest framing, one line of facts about
 * the run, and "Run details" (counters and run notes, collapsed by default).
 */
const props = defineProps<{
  scan: Scan
  title: string
  /** The linked address under the title (null when the title already is the address). */
  url: string | null
  href: string | null
  pasted: boolean
  prechecked: number | null
  notes: RunNote[]
  answers: { answered: number; asked: number } | null
  tokens: string | null
  seconds: number
  left: number | null
  langDiffers: boolean
  rerunning: boolean
}>()
const emit = defineEmits<{ demo: []; rerun: []; rerunIn: []; filter: [reason: string] }>()

const open = ref(false)
const regionId = useId()
const warn = computed(() => props.notes.some((n) => n.tone === 'warning'))
/** The header badge already names the current mode: repeat it here only when this check ran in another one. */
const otherMode = computed(() => !health.value || health.value.mode !== props.scan.mode)

function filter(reason: string) {
  open.value = false
  emit('filter', reason)
}
</script>

<template>
  <header class="rh">
    <div class="rh__top">
      <div class="rh__title m-rise" style="--i: 0">
        <h1 class="rh__h1" tabindex="-1">{{ title }}</h1>
        <p class="rh__lede">{{ prechecked !== null ? t('report.disclaimer', { n: prechecked }) : t('report.disclaimerNoN') }}</p>
      </div>
      <div class="rh__actions m-rise" style="--i: 1">
        <ExportMenu :scan="scan" />
      </div>
    </div>

    <div class="rh__meta m-rise" style="--i: 1">
      <div class="rh__clip">
      <ul class="rh__facts" role="list">
        <li v-if="url && href">
          <a :href="href" target="_blank" rel="noopener noreferrer" class="rh__url mono"
            >{{ url }}<ExternalLink :size="12" aria-hidden="true" /><span class="sr-only"> {{ t('finding.newTab') }}</span></a
          >
        </li>
        <li v-else-if="pasted">{{ t('report.pastedHtml') }}</li>
        <li><time :datetime="scan.created_at" class="tabular">{{ formatDate(scan.created_at) }}</time></li>
        <li>{{ prettyModel(scan.model) }}</li>
        <li v-if="otherMode" class="rh__mode">
          <ShapeIcon :shape="MODE_SHAPE[scan.mode]" :color="MODE_COLOR[scan.mode]" :size="9" />{{ t(`sov.${scan.mode}`) }}
        </li>
        <li class="tabular">{{ left === null ? t('report.leftUnknown') : tp('report.left', left) }}</li>
      </ul>
      </div>
      <button type="button" class="rh__toggle" :class="{ 'is-warn': warn }" :aria-expanded="open" :aria-controls="regionId" @click="open = !open">
        <ShapeIcon v-if="warn" shape="diamond" color="var(--amber)" :size="9" />
        <span>{{ t('report.runDetails') }}</span>
        <span v-if="notes.length" class="rh__count tabular">· {{ tp('report.notes', notes.length) }}</span>
        <ChevronDown :size="16" aria-hidden="true" class="rh__chev" />
      </button>
    </div>

    <p v-if="langDiffers" class="rh__lang m-rise" style="--i: 1" role="note">
      <span>{{ t('notes.lang', { scanLang: languageName(scan.ui_lang) }) }}</span>
      <button v-if="href" type="button" class="rh__link" :disabled="rerunning" @click="emit('rerunIn')">
        {{ t('notes.rerunIn', { uiLang: languageName(locale) }) }}
      </button>
    </p>

    <div :id="regionId" class="m-collapse" :data-open="open">
      <div :inert="!open || undefined">
        <div class="rh__details">
          <RunNotes v-if="notes.length" :notes="notes" @demo="emit('demo')" @rerun="emit('rerun')" @filter="filter" />
          <dl class="rh__dl">
            <div>
              <dt>{{ t('report.meta.duration') }}</dt>
              <dd class="tabular">{{ t('report.seconds', { n: formatNumber(seconds, { maximumFractionDigits: 1 }) }) }}</dd>
            </div>
            <div>
              <dt>{{ t('report.meta.answers') }}</dt>
              <dd class="tabular">
                {{ answers ? t('report.answersOf', { answered: formatNumber(answers.answered), asked: formatNumber(answers.asked) }) : t('report.noneNeeded') }}
              </dd>
            </div>
            <div v-if="typeof scan.stats.llm_calls === 'number'">
              <dt>{{ t('report.meta.calls') }}</dt>
              <dd class="tabular">{{ formatNumber(scan.stats.llm_calls) }}</dd>
            </div>
            <div v-if="typeof scan.stats.guard_rejected === 'number'">
              <dt>{{ t('report.meta.guard') }}</dt>
              <dd class="tabular">{{ formatNumber(scan.stats.guard_rejected) }}</dd>
            </div>
            <div v-if="tokens">
              <dt>{{ t('report.tokens') }}</dt>
              <dd class="tabular">{{ tokens }}</dd>
            </div>
            <div>
              <dt>{{ t('report.scanId') }}</dt>
              <dd class="mono">{{ scan.id }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  </header>
</template>

<style scoped>
.rh {
  display: flex;
  flex-direction: column;
  gap: var(--s-4);
}
.rh__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--s-4);
}
.rh__title {
  display: flex;
  flex-direction: column;
  gap: var(--s-2);
  min-width: 0;
}
.rh__h1 {
  font-size: clamp(1.75rem, 1.3rem + 1.5vw, 2.5rem);
  line-height: 1.1;
  font-weight: 700;
  letter-spacing: -0.032em;
  text-wrap: balance;
  overflow-wrap: anywhere;
}
.rh__lede {
  font-size: var(--fs-16);
  color: var(--muted);
  text-wrap: pretty;
}
.rh__actions {
  /* Above the stats band that rises in after it (its animation makes a stacking context). */
  position: relative;
  z-index: 5;
  flex: none;
  padding-top: 4px;
}
.rh__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px var(--s-4);
}
.rh__clip {
  /* Every fact starts with a dot; the dot that starts a line is clipped, so a wrapped line never begins with one. */
  min-width: 0;
  margin: -4px;
  padding: 4px;
  overflow: hidden;
}
.rh__facts {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 0;
  margin: 0 0 0 -23px;
  font-size: var(--fs-14);
  color: var(--muted);
}
.rh__facts > li {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.rh__facts > li::before {
  content: '';
  flex: none;
  width: 3px;
  height: 3px;
  margin: 0 10px;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.6;
}
.rh__mode {
  color: var(--ink);
  font-weight: 600;
}
.rh__url {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--ink);
  font-size: 0.8125rem;
  text-decoration: none;
  overflow-wrap: anywhere;
  word-break: break-all;
}
.rh__url:hover {
  text-decoration: underline;
}
.rh__toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 0 8px;
  margin-left: -8px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--muted);
  font-size: var(--fs-14);
  font-weight: 600;
  transition: color var(--dur-1) var(--ease-out), background-color var(--dur-1) var(--ease-out);
}
.rh__toggle:hover {
  color: var(--ink);
  background: var(--surface-2);
}
.rh__toggle.is-warn {
  color: var(--amber);
}
.rh__count {
  font-weight: 500;
}
.rh__chev {
  transition: transform var(--dur-2) var(--ease-out);
}
.rh__toggle[aria-expanded='true'] .rh__chev {
  transform: rotate(180deg);
}
.rh__lang {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px var(--s-3);
  font-size: var(--fs-14);
  color: var(--muted);
}
.rh__link {
  padding: 0;
  border: 0;
  background: none;
  color: var(--blue);
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 0.18em;
}
.rh__link:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.rh__details {
  display: flex;
  flex-direction: column;
  gap: var(--s-4);
  padding: 2px 2px var(--s-2);
}
.rh__dl {
  display: flex;
  flex-wrap: wrap;
  gap: var(--s-3) var(--s-6);
  margin: 0;
  font-size: var(--fs-14);
}
.rh__dl dt {
  font-size: var(--fs-12);
  color: var(--muted);
}
.rh__dl dd {
  margin: 2px 0 0;
  font-weight: 600;
}
@media (max-width: 640px) {
  .rh__top {
    flex-direction: column;
  }
  .rh__actions {
    padding-top: 0;
  }
}
</style>
