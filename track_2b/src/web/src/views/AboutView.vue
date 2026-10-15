<script setup lang="ts">
import { computed, onMounted, type Component } from 'vue'
import { ArrowRight, Cloud, CodeXml, MessageSquareText, Server, TextQuote, UserCheck, WifiOff } from '@lucide/vue'
import type { Mode } from '@/types'
import { formatDate, t, type MessageKey } from '@/i18n'
import { ensureBooted, health } from '@/stores/app'
import { implementedCount, loadCriteria } from '@/stores/criteria'
import { MODE_COLOR, MODE_SHAPE } from '@/lib/format'
import { useDocumentTitle } from '@/composables/useDocumentTitle'
import ShapeIcon from '@/components/ShapeIcon.vue'
import CopyBlock from '@/components/CopyBlock.vue'
import CountUp from '@/components/CountUp.vue'
import SourceLink from '@/components/SourceLink.vue'
import { SOURCES_CHECKED, type SourceId } from '@/data/swiss-law'

useDocumentTitle(() => t('about.docTitle'))

onMounted(async () => {
  await ensureBooted()
  void loadCriteria()
})

/** Code → Apertus → evidence guard → a person. One example (alt="Bild") runs through all four. */
const steps: { icon: Component; tone: 'code' | 'model' | 'guard' | 'person' }[] = [
  { icon: CodeXml, tone: 'code' },
  { icon: MessageSquareText, tone: 'model' },
  { icon: TextQuote, tone: 'guard' },
  { icon: UserCheck, tone: 'person' },
]
const stepKey = (i: number, f: 'title' | 'body' | 'trace') => `about.s${i + 1}.${f}` as MessageKey

/** From the backend registry (GET /api/criteria), never a hard-coded number. */
const prechecked = computed(() => implementedCount())
const TOTAL = 50

/** The three target architectures, with the command or setting that selects each. */
const archs: { key: 'onprem' | 'airgap' | 'cloud'; icon: Component; cmd: string }[] = [
  { key: 'onprem', icon: Server, cmd: 'make run-gpu' },
  { key: 'airgap', icon: WifiOff, cmd: 'make airgap-check' },
  { key: 'cloud', icon: Cloud, cmd: 'LLM_BASE_URL=https://maas.phoeniqs.com/v1' },
]
/** Swiss law in brief: one line per level, each with its official text (_prive/SWISS_FACTS.md). */
const lawRows: { term: MessageKey; body: MessageKey; links: { source: SourceId; label: MessageKey }[] }[] = [
  {
    term: 'swiss.about.fed',
    body: 'swiss.about.fed.body',
    links: [
      { source: 'behig', label: 'swiss.about.fed.law' },
      { source: 'behiv', label: 'swiss.about.fed.ord' },
    ],
  },
  { term: 'swiss.about.std', body: 'swiss.about.std.body', links: [{ source: 'ech0059', label: 'swiss.about.std.link' }] },
  {
    term: 'swiss.about.cantons',
    body: 'swiss.about.cantons.body',
    links: [
      { source: 'bsBrg', label: 'swiss.about.cantons.bs' },
      { source: 'vsVrimb', label: 'swiss.about.cantons.vs' },
    ],
  },
  { term: 'swiss.about.eu', body: 'swiss.about.eu.body', links: [{ source: 'eaa', label: 'swiss.about.eu.link' }] },
  { term: 'swiss.about.next', body: 'swiss.about.next.body', links: [{ source: 'behigRevision', label: 'swiss.about.next.link' }] },
]
const checkedOn = computed(() => formatDate(SOURCES_CHECKED, false))

/** The four states of the header badge. */
const modes: Mode[] = ['local', 'swiss_cloud', 'external', 'replay']

const limits = ['cert', 'rating', 'edit', 'final', 'journey'] as const

const credits: { name: string; role: MessageKey; licence: string }[] = [
  { name: 'Apertus v1.5', role: 'about.credits.apertus', licence: 'Apache-2.0' },
  { name: 'axe-core', role: 'about.credits.axe', licence: 'MPL-2.0' },
  { name: 'W3C ACT Rules', role: 'about.credits.act', licence: 'W3C' },
  { name: 'Inter · JetBrains Mono', role: 'about.credits.fonts', licence: 'OFL-1.1' },
  { name: 'Lucide', role: 'about.credits.icons', licence: 'ISC' },
]

/** The three endpoint variables (see .env.example). */
const ENV_LINES = ['LLM_NAME=swiss-ai/Apertus-v1.5-8B', 'LLM_BASE_URL=https://your-apertus-endpoint/v1', 'LLM_API_KEY=your-key'].join('\n')
</script>

<template>
  <div class="container about">
    <header class="hero">
      <h1 class="hero__title m-rise" tabindex="-1">{{ t('about.title') }}</h1>
      <p class="lede m-rise" style="--i: 1">{{ t('about.lede') }}</p>
    </header>

    <!-- 1. The pipeline: a step diagram that draws itself on scroll. -->
    <section class="sec sec--pipe" aria-labelledby="ab-pipeline">
      <h2 id="ab-pipeline" class="sr-only">{{ t('about.pipeline') }}</h2>
      <div class="pipe">
        <span v-reveal class="pipe__rail" aria-hidden="true" />
        <ol class="pipe__list" role="list">
        <li v-for="(s, i) in steps" :key="s.tone" v-reveal="i * 2" class="step" :class="`step--${s.tone}`">
          <span class="step__node" aria-hidden="true"><component :is="s.icon" :size="20" :stroke-width="1.75" /></span>
          <span v-if="i < steps.length - 1" class="step__seg" aria-hidden="true" />
          <div class="step__text">
            <p class="step__num mono" aria-hidden="true">{{ String(i + 1).padStart(2, '0') }}</p>
            <h3 class="step__title">{{ t(stepKey(i, 'title')) }}</h3>
            <p class="step__body">{{ t(stepKey(i, 'body')) }}</p>
            <p class="step__trace mono" translate="no">{{ t(stepKey(i, 'trace')) }}</p>
          </div>
        </li>
        </ol>
      </div>
    </section>

    <!-- 2. Coverage, from the registry. -->
    <section v-reveal class="cov" aria-labelledby="ab-cov">
      <p class="cov__num" aria-hidden="true">
        <CountUp v-if="prechecked !== null" :value="prechecked" /><span v-else class="skel cov__skel">00</span><span class="cov__of">/{{ TOTAL }}</span>
      </p>
      <div class="cov__text">
        <h2 id="ab-cov" class="cov__label">
          <span class="sr-only">{{ prechecked ?? '—' }}</span> {{ t('about.cov.label') }}
        </h2>
        <p class="cov__body">{{ t('about.cov.body', { n: prechecked !== null ? TOTAL - prechecked : '—' }) }}</p>
        <RouterLink class="cov__link" :to="{ name: 'human' }">
          {{ t('about.cov.link') }}<ArrowRight :size="16" aria-hidden="true" />
        </RouterLink>
      </div>
    </section>

    <!-- 3. Swiss law in brief: why accessibility is a duty, each line with its official text. -->
    <section id="law" v-reveal class="sec split" aria-labelledby="ab-law">
      <div>
        <h2 id="ab-law" class="sec__title">{{ t('swiss.about.title') }}</h2>
        <p class="sec__lede">{{ t('swiss.about.lede') }}</p>
      </div>
      <div class="law">
        <dl class="law__list">
          <div v-for="(r, i) in lawRows" :key="r.term" v-reveal="i" class="law__row">
            <dt class="law__term">{{ t(r.term) }}</dt>
            <dd class="law__body">
              <p>{{ t(r.body) }}</p>
              <p class="law__links">
                <SourceLink v-for="l in r.links" :key="l.source" :source="l.source" :label="t(l.label)" />
              </p>
            </dd>
          </div>
        </dl>
        <p class="law__fine">{{ t('swiss.fine', { date: checkedOn }) }}</p>
      </div>
    </section>

    <!-- 4. Where pages go: the three architectures, then the badge's four states. -->
    <section id="modes" class="sec" aria-labelledby="ab-modes">
      <div class="sec__head">
        <h2 id="ab-modes" class="sec__title">{{ t('about.modes') }}</h2>
        <p class="sec__lede">{{ t('about.modes.lede') }}</p>
      </div>
      <ul class="archs" role="list">
        <li v-for="(a, i) in archs" :key="a.key" v-reveal="i" class="arch">
          <span class="arch__icon" aria-hidden="true"><component :is="a.icon" :size="20" :stroke-width="1.75" /></span>
          <h3 class="arch__title">{{ t(`about.arch.${a.key}`) }}</h3>
          <p class="arch__body">{{ t(`about.arch.${a.key}.body`) }}</p>
          <code class="arch__cmd" translate="no">{{ a.cmd }}</code>
        </li>
      </ul>
      <div v-reveal class="badge-key">
        <p class="badge-key__lead">{{ t('about.badge') }}</p>
        <ul class="badge-key__list" role="list">
          <li v-for="m in modes" :key="m" class="badge-key__item" :class="{ 'is-current': health?.mode === m }">
            <ShapeIcon :shape="MODE_SHAPE[m]" :color="MODE_COLOR[m]" :size="12" />
            <span class="badge-key__text">
              <span class="badge-key__name">{{ t(`sov.${m}`) }}</span>
              <span v-if="health?.mode === m" class="badge-key__current">{{ t('about.current') }}</span>
              <span class="badge-key__sub">{{ t(`about.mode.${m}`) }}</span>
            </span>
          </li>
        </ul>
      </div>
    </section>

    <!-- 5. Connect (target of every "connect an endpoint" link). -->
    <section id="connect" v-reveal class="sec split" aria-labelledby="ab-connect">
      <div>
        <h2 id="ab-connect" class="sec__title">{{ t('connect.title') }}</h2>
        <p class="sec__lede">{{ t('connect.lede') }}</p>
      </div>
      <div class="connect">
        <ol class="connect__steps" role="list">
          <li class="connect__step">
            <span class="connect__n mono" aria-hidden="true">1</span>
            <div class="connect__body">
              <p class="connect__label">{{ t('connect.step1') }}</p>
              <CopyBlock :text="ENV_LINES" :label="t('connect.copyEnv')" />
            </div>
          </li>
          <li class="connect__step">
            <span class="connect__n mono" aria-hidden="true">2</span>
            <div class="connect__body">
              <p class="connect__label">{{ t('connect.step2') }}</p>
              <CopyBlock text="make run" :label="t('connect.copyCmd')" />
            </div>
          </li>
        </ol>
        <p class="connect__note">{{ t('connect.note') }}</p>
      </div>
    </section>

    <!-- 6. What Klar. does not do. -->
    <section v-reveal class="sec split" aria-labelledby="ab-no">
      <h2 id="ab-no" class="sec__title">{{ t('about.no') }}</h2>
      <ul class="nots" role="list">
        <li v-for="k in limits" :key="k" class="not">
          <strong class="not__title">{{ t(`about.no.${k}`) }}</strong> {{ t(`about.no.${k}.body`) }}
        </li>
      </ul>
    </section>

    <div v-reveal class="cta">
      <RouterLink class="btn btn--primary press" :to="{ name: 'home', query: { focus: '1' } }">
        {{ t('about.cta') }}<ArrowRight :size="18" aria-hidden="true" />
      </RouterLink>
    </div>

    <!-- 7. Credits and licences. -->
    <section v-reveal class="credits split" aria-labelledby="ab-credits">
      <h2 id="ab-credits" class="credits__title">{{ t('about.credits') }}</h2>
      <dl class="credits__list">
        <div v-for="c in credits" :key="c.name" class="credit">
          <dt class="credit__name" translate="no">{{ c.name }}</dt>
          <dd class="credit__role">{{ t(c.role) }}</dd>
          <dd class="credit__lic mono" translate="no">{{ c.licence }}</dd>
        </div>
      </dl>
    </section>
  </div>
</template>

<style scoped>
.about {
  padding-top: var(--s-8);
  padding-bottom: var(--s-8);
}

/* ---- Hero ------------------------------------------------------------- */
.hero {
  display: flex;
  flex-direction: column;
  gap: var(--s-4);
  max-width: 820px;
}
.hero__title {
  font-size: clamp(2.25rem, 1.3rem + 3.6vw, var(--fs-64));
  line-height: var(--lh-display);
  font-weight: 700;
  letter-spacing: -0.035em;
  text-wrap: balance;
}

/* ---- Sections --------------------------------------------------------- */
.sec {
  margin-top: var(--s-9);
}
.sec--pipe {
  margin-top: var(--s-8);
}
.sec__head {
  max-width: 720px;
}
.sec__title {
  font-size: var(--fs-32);
  line-height: 1.15;
  font-weight: 700;
  letter-spacing: -0.03em;
  text-wrap: balance;
}
.sec__lede {
  margin-top: var(--s-3);
  max-width: 62ch;
  color: var(--muted);
  text-wrap: pretty;
}
.split {
  display: grid;
  grid-template-columns: 4fr 8fr;
  gap: var(--gutter);
}

/* ---- Pipeline diagram ------------------------------------------------- */
.pipe {
  --node: 48px;
  position: relative;
}
.pipe__list {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--gutter);
  margin: 0;
  padding: 0;
}
.pipe__rail {
  /* The connector: drawn left to right when the diagram scrolls into view. */
  position: absolute;
  top: calc(var(--node) / 2 - 1px);
  left: calc(var(--node) / 2);
  right: calc((100% - 3 * var(--gutter)) / 4 - var(--node) / 2);
  height: 2px;
  background: var(--ink);
  transform-origin: left center;
}
.pipe__rail[data-reveal='out'] {
  opacity: 1;
  transform: scaleX(0);
}
.pipe__rail[data-reveal='in'] {
  transform: none;
  transition: transform var(--dur-4) var(--ease-out);
}
.step {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--s-5);
}
.step__seg {
  display: none;
}
.step__node {
  position: relative;
  display: grid;
  place-items: center;
  width: var(--node);
  height: var(--node);
  background: var(--bg);
  border: 1.5px solid var(--ink);
  border-radius: 12px;
  color: var(--ink);
}
.step--model .step__node {
  background: var(--klar-red);
  border-color: var(--klar-red);
  color: var(--on-ink);
}
.step--person .step__node {
  background: var(--ink);
  border-color: var(--ink);
  color: var(--on-ink);
}
.step__text {
  display: flex;
  flex-direction: column;
  gap: var(--s-2);
}
.step__num {
  font-size: var(--fs-12);
  color: var(--muted);
}
.step__title {
  font-size: var(--fs-20);
  font-weight: 650;
  letter-spacing: -0.02em;
}
.step__body {
  font-size: var(--fs-14);
  line-height: 1.55;
  color: var(--muted);
  text-wrap: pretty;
}
.step__trace {
  align-self: flex-start;
  margin-top: var(--s-2);
  padding: 4px 8px;
  background: var(--surface-2);
  border-radius: 6px;
  font-size: var(--fs-12);
  color: var(--ink);
  overflow-wrap: anywhere;
}
.step--model .step__trace {
  box-shadow: inset 2px 0 0 var(--klar-red);
}

/* ---- Coverage --------------------------------------------------------- */
.cov {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: var(--s-6);
  margin-top: var(--s-9);
  padding: var(--s-6) 0;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}
.cov__num {
  display: flex;
  align-items: baseline;
  font-size: clamp(3.5rem, 2.5rem + 4vw, 6rem);
  line-height: 1;
  font-weight: 700;
  letter-spacing: -0.045em;
  font-variant-numeric: tabular-nums;
}
.cov__of {
  font-size: 0.42em;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--muted);
  margin-left: 4px;
}
.cov__skel {
  display: inline-block;
  line-height: 1;
}
.cov__text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--s-2);
}
.cov__label {
  font-size: var(--fs-20);
  font-weight: 650;
  letter-spacing: -0.02em;
}
.cov__body {
  color: var(--muted);
}
.cov__link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  font-weight: 600;
  text-decoration: none;
}
.cov__link:hover {
  text-decoration: underline;
}
.cov__link svg {
  transition: transform var(--dur-2) var(--ease-out);
}
.cov__link:hover svg {
  transform: translateX(3px);
}

/* ---- Swiss law in brief ------------------------------------------------ */
.law {
  min-width: 0;
}
.law__list {
  margin: 0;
  border-top: 1px solid var(--line);
}
.law__row {
  display: grid;
  grid-template-columns: minmax(0, 9.5rem) minmax(0, 1fr);
  gap: var(--s-1) var(--s-5);
  padding: var(--s-4) 0;
  border-bottom: 1px solid var(--line);
}
.law__term {
  font-weight: 650;
  letter-spacing: -0.01em;
}
.law__body {
  margin: 0;
  color: var(--muted);
  text-wrap: pretty;
  overflow-wrap: break-word;
  hyphens: auto;
}
.law__links {
  display: flex;
  flex-wrap: wrap;
  gap: 0 var(--s-4);
  margin-top: var(--s-1);
}
.law__fine {
  margin-top: var(--s-3);
  font-size: var(--fs-12);
  color: var(--muted);
}

/* ---- Architectures ---------------------------------------------------- */
.archs {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--gutter);
  margin: var(--s-6) 0 0;
  padding: 0;
}
.arch {
  display: flex;
  flex-direction: column;
  gap: var(--s-3);
  padding-top: var(--s-5);
  border-top: 1px solid var(--line);
}
.arch__icon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  margin-bottom: var(--s-1);
  border: 1.5px solid var(--line);
  border-radius: 10px;
  color: var(--ink);
}
.arch__title {
  font-size: var(--fs-20);
  font-weight: 650;
  letter-spacing: -0.02em;
}
.arch__body {
  font-size: var(--fs-14);
  line-height: 1.55;
  color: var(--muted);
  text-wrap: pretty;
}
.arch__cmd {
  align-self: flex-start;
  margin-top: auto;
  padding: 4px 8px;
  background: var(--surface-2);
  border-radius: 6px;
  font-size: var(--fs-12);
  color: var(--ink);
  overflow-wrap: anywhere;
}

/* Badge key */
.badge-key {
  margin-top: var(--s-7);
}
.badge-key__lead {
  margin-bottom: var(--s-3);
  font-size: var(--fs-14);
  font-weight: 600;
}
.badge-key__list {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--s-2);
  margin: 0;
  padding: 0;
}
.badge-key__item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: var(--s-3) var(--s-4);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
}
.badge-key__item :deep(svg) {
  flex: none;
  margin-top: 5px;
}
.badge-key__item.is-current {
  border-color: var(--ink);
  box-shadow: inset 0 0 0 1px var(--ink);
}
.badge-key__text {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 2px 8px;
}
.badge-key__name {
  font-size: var(--fs-14);
  font-weight: 650;
}
.badge-key__current {
  padding: 0 7px;
  background: var(--ink);
  color: var(--on-ink);
  border-radius: var(--r-pill);
  font-size: var(--fs-12);
  font-weight: 600;
  line-height: 18px;
}
.badge-key__sub {
  flex-basis: 100%;
  font-size: var(--fs-12);
  line-height: 1.5;
  color: var(--muted);
}

/* ---- Connect ---------------------------------------------------------- */
.connect {
  display: flex;
  flex-direction: column;
  gap: var(--s-4);
  min-width: 0;
}
.connect__steps {
  display: flex;
  flex-direction: column;
  gap: var(--s-5);
  margin: 0;
}
.connect__step {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  gap: var(--s-3);
}
.connect__n {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border: 1.5px solid var(--ink);
  border-radius: 8px;
  font-size: var(--fs-12);
  font-weight: 600;
}
.connect__body {
  min-width: 0;
}
.connect__label {
  margin-bottom: var(--s-2);
  font-weight: 600;
  line-height: 28px;
}
.connect__note {
  padding-left: calc(28px + var(--s-3));
  font-size: var(--fs-14);
  color: var(--muted);
}

/* ---- Does not do ------------------------------------------------------ */
.nots {
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--line);
}
.not {
  position: relative;
  padding: var(--s-4) 0 var(--s-4) 28px;
  border-bottom: 1px solid var(--line);
  color: var(--muted);
  text-wrap: pretty;
}
.not::before {
  /* A struck square: "not this". */
  content: '';
  position: absolute;
  left: 2px;
  top: calc(var(--s-4) + 0.42em);
  width: 10px;
  height: 10px;
  border: 1.5px solid var(--klar-red);
  background: linear-gradient(135deg, transparent calc(50% - 0.75px), var(--klar-red) calc(50% - 0.75px) calc(50% + 0.75px), transparent calc(50% + 0.75px));
}
.not__title {
  font-weight: 650;
  color: var(--ink);
}

/* ---- CTA and credits -------------------------------------------------- */
.cta {
  margin-top: var(--s-8);
}
.cta .btn svg {
  transition: transform var(--dur-2) var(--ease-out);
}
.cta .btn:hover svg {
  transform: translateX(3px);
}
.credits {
  margin-top: var(--s-9);
  padding-top: var(--s-5);
  border-top: 1px solid var(--line);
}
.credits__title {
  font-size: var(--fs-14);
  font-weight: 650;
}
.credits__list {
  margin: 0;
  display: flex;
  flex-direction: column;
}
.credit {
  display: grid;
  grid-template-columns: minmax(0, 13rem) minmax(0, 1fr) auto;
  gap: var(--s-1) var(--s-4);
  padding: var(--s-2) 0;
  font-size: var(--fs-14);
}
.credit + .credit {
  border-top: 1px solid var(--line);
}
.credit__name {
  font-weight: 600;
}
.credit__role {
  margin: 0;
  color: var(--muted);
}
.credit__lic {
  margin: 0;
  font-size: var(--fs-12);
  color: var(--muted);
  line-height: 1.75;
}

/* ---- Responsive ------------------------------------------------------- */
@media (max-width: 1023px) {
  .badge-key__list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 860px) {
  .pipe__list {
    grid-template-columns: minmax(0, 1fr);
    gap: var(--s-6);
  }
  .pipe__rail {
    display: none;
  }
  .step__seg {
    /* Vertical connector: from this node down to the next one. */
    display: block;
    position: absolute;
    left: calc(var(--node) / 2 - 1px);
    top: var(--node);
    bottom: calc(-1 * var(--s-6));
    width: 2px;
    background: var(--ink);
    transform-origin: center top;
  }
  .step[data-reveal='out'] .step__seg {
    transform: scaleY(0);
  }
  .step[data-reveal='in'] .step__seg {
    transition: transform var(--dur-4) var(--ease-out) calc(var(--i, 0) * var(--stagger) + var(--dur-2));
  }
  .step {
    flex-direction: row;
    align-items: flex-start;
    gap: var(--s-4);
  }
  .step__node {
    flex: none;
  }
  .step__text {
    padding-top: 2px;
  }
  .archs {
    grid-template-columns: minmax(0, 1fr);
    gap: var(--s-6);
  }
  .split {
    grid-template-columns: minmax(0, 1fr);
    gap: var(--s-5);
  }
  .cov {
    grid-template-columns: minmax(0, 1fr);
    gap: var(--s-4);
  }
}
@media (max-width: 560px) {
  .about {
    padding-top: var(--s-6);
  }
  .sec,
  .cov {
    margin-top: var(--s-8);
  }
  .sec__title {
    font-size: var(--fs-24);
  }
  .badge-key__list {
    grid-template-columns: minmax(0, 1fr);
  }
  .law__row {
    grid-template-columns: minmax(0, 1fr);
  }
  .credit {
    grid-template-columns: minmax(0, 1fr) auto;
  }
  .credit__role {
    grid-column: 1 / -1;
    grid-row: 2;
  }
}
@media (forced-colors: active) {
  .step__node,
  .arch__icon,
  .connect__n {
    border-color: CanvasText;
  }
  .pipe__rail,
  .step__seg {
    background: CanvasText;
  }
  .not::before {
    border-color: CanvasText;
    background: none;
  }
}
</style>
