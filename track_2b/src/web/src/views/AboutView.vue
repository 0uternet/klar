<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { ArrowRight } from '@lucide/vue'
import type { Mode } from '@/types'
import { t, type MessageKey } from '@/i18n'
import { ensureBooted, health, unreachable } from '@/stores/app'
import { implementedCount, loadCriteria } from '@/stores/criteria'
import { MODE_COLOR, MODE_SHAPE } from '@/lib/format'
import { useDocumentTitle } from '@/composables/useDocumentTitle'
import ShapeIcon from '@/components/ShapeIcon.vue'
import CopyBlock from '@/components/CopyBlock.vue'
import SovereigntyBadge from '@/components/SovereigntyBadge.vue'

useDocumentTitle(() => t('about.docTitle'))

const pipeline = [1, 2, 3, 4, 5, 6].map((i) => ({
  title: `about.p${i}.title` as MessageKey,
  body: `about.p${i}.body` as MessageKey,
}))
const modes: Mode[] = ['local', 'swiss_cloud', 'external', 'replay']
/** From the backend registry (GET /api/criteria), never a hard-coded number. */
const prechecked = computed(() => implementedCount() ?? '—')
onMounted(async () => {
  await ensureBooted()
  void loadCriteria()
})
const providerSub = (m: Mode) => (m === 'swiss_cloud' ? t('sov.swiss_cloud.sub', { provider: 'Phoeniqs / CSCS' }) : t(`sov.${m}.sub`))

/** The three endpoint variables (see .env.example). */
const ENV_LINES = ['LLM_NAME=swiss-ai/Apertus-v1.5-8B', 'LLM_BASE_URL=https://your-apertus-endpoint/v1', 'LLM_API_KEY=your-key'].join('\n')
</script>

<template>
  <div class="container about">
    <header class="about__head">
      <p class="eyebrow">{{ t('about.eyebrow') }}</p>
      <h1 class="h1 about__title" tabindex="-1">{{ t('about.title') }}</h1>
      <p class="lede">{{ t('about.lede') }}</p>
    </header>

    <section class="about__section" aria-labelledby="ab-pipeline">
      <h2 id="ab-pipeline" class="about__h2">{{ t('about.pipeline') }}</h2>
      <ol class="pipe" role="list">
        <li v-for="(p, i) in pipeline" :key="p.title" class="pipe__step" :class="{ 'pipe__step--model': i === 3, 'pipe__step--human': i === 5 }">
          <span class="pipe__num mono" aria-hidden="true">{{ String(i + 1).padStart(2, '0') }}</span>
          <h3 class="pipe__title">{{ t(p.title) }}</h3>
          <p class="pipe__body">{{ t(p.body) }}</p>
        </li>
      </ol>
    </section>

    <section id="modes" class="about__section" aria-labelledby="ab-modes">
      <h2 id="ab-modes" class="about__h2">{{ t('about.modes') }}</h2>
      <p class="about__lede">{{ t('about.modes.lede') }}</p>
      <div class="modes">
        <ul class="modes__list" role="list">
          <li v-for="m in modes" :key="m" class="mode" :class="{ 'is-current': health?.mode === m }">
            <p class="mode__label">
              <ShapeIcon :shape="MODE_SHAPE[m]" :color="MODE_COLOR[m]" :size="12" />
              <span>{{ t(`sov.${m}`) }}</span>
              <span v-if="health?.mode === m" class="mode__current">{{ t('about.current') }}</span>
            </p>
            <p class="mode__sub">{{ providerSub(m) }}</p>
            <p class="mode__body">{{ t(`about.mode.${m}`) }}</p>
            <code class="mode__env">{{ m === 'replay' ? 'KLAR_REPLAY=1' : m === 'local' ? 'LLM_BASE_URL=http://llm-gpu:8000/v1' : m === 'swiss_cloud' ? 'LLM_BASE_URL=https://maas.phoeniqs.com/v1' : 'LLM_BASE_URL=https://…' }}</code>
          </li>
        </ul>
        <div class="modes__current">
          <p class="about__label">{{ t('about.current') }}</p>
          <SovereigntyBadge variant="card" :health="health" :unreachable="unreachable" />
        </div>
      </div>
    </section>

    <section id="connect" class="about__section about__two" aria-labelledby="ab-connect">
      <div>
        <h2 id="ab-connect" class="about__h2">{{ t('connect.title') }}</h2>
        <p class="about__lede">{{ t('connect.lede') }}</p>
      </div>
      <div class="connect">
        <ol class="connect__steps">
          <li>
            <p class="connect__step">{{ t('connect.step1') }}</p>
            <CopyBlock :text="ENV_LINES" :label="t('connect.copyEnv')" />
          </li>
          <li>
            <p class="connect__step">{{ t('connect.step2') }}</p>
            <CopyBlock text="make run" :label="t('connect.copyCmd')" />
          </li>
        </ol>
        <p class="connect__note">{{ t('connect.note') }}</p>
      </div>
    </section>

    <section class="about__section about__two" aria-labelledby="ab-sov">
      <h2 id="ab-sov" class="about__h2">{{ t('about.sov') }}</h2>
      <ul class="ticks" role="list">
        <li>{{ t('about.sov.1') }}</li>
        <li>{{ t('about.sov.2') }}</li>
        <li>{{ t('about.sov.3') }}</li>
      </ul>
    </section>

    <section class="about__section about__two" aria-labelledby="ab-limits">
      <h2 id="ab-limits" class="about__h2">{{ t('about.limits') }}</h2>
      <ul class="ticks ticks--limits" role="list">
        <li>{{ t('about.limit.1') }}</li>
        <li>{{ t('about.limit.2', { n: prechecked }) }}</li>
        <li>{{ t('about.limit.3') }}</li>
        <li>{{ t('about.limit.4') }}</li>
        <li>{{ t('about.limit.5') }}</li>
      </ul>
    </section>

    <section class="about__section about__two" aria-labelledby="ab-credits">
      <h2 id="ab-credits" class="about__h2">{{ t('about.credits') }}</h2>
      <ul class="credits" role="list">
        <li class="credits__main">{{ t('about.credits.apertus') }}</li>
        <li>{{ t('about.credits.axe') }}</li>
        <li>{{ t('about.credits.act') }}</li>
        <li>{{ t('about.credits.fonts') }}</li>
        <li>{{ t('about.credits.icons') }}</li>
      </ul>
    </section>

    <div class="about__cta">
      <RouterLink class="btn btn--primary" :to="{ name: 'home', query: { focus: '1' } }">
        {{ t('about.cta') }} <ArrowRight :size="18" aria-hidden="true" />
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
.about {
  padding-top: var(--s-8);
}
.about__head {
  display: flex;
  flex-direction: column;
  gap: var(--s-4);
  max-width: 900px;
}
.about__title {
  font-size: clamp(2rem, 1.3rem + 2.6vw, var(--fs-48));
}
.about__section {
  margin-top: var(--s-8);
  padding-top: var(--s-5);
  border-top: 2px solid var(--ink);
}
.about__h2 {
  font-size: var(--fs-24);
  font-weight: 700;
  letter-spacing: -0.02em;
  max-width: 30ch;
}
.about__lede {
  margin-top: var(--s-3);
  max-width: 70ch;
  color: var(--muted);
}
.about__label {
  margin-bottom: var(--s-3);
  font-size: var(--fs-14);
  font-weight: 600;
  color: var(--muted);
}
.connect {
  display: flex;
  flex-direction: column;
  gap: var(--s-4);
  min-width: 0;
}
.connect__steps {
  margin: 0;
  padding-left: 1.4em;
  display: flex;
  flex-direction: column;
  gap: var(--s-5);
}
.connect__steps li::marker {
  font-weight: 700;
}
.connect__step {
  margin-bottom: var(--s-2);
  font-weight: 600;
}
.connect__note {
  font-size: var(--fs-14);
  color: var(--muted);
  max-width: 68ch;
}
.about__two {
  display: grid;
  grid-template-columns: 4fr 8fr;
  gap: var(--gutter);
}
.pipe {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: var(--s-3);
  margin: var(--s-5) 0 0;
  padding: 0;
}
.pipe__step {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--s-2);
  padding: var(--s-4);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
}
.pipe__step--model {
  border-color: var(--ink);
  box-shadow: inset 0 3px 0 var(--klar-red);
}
.pipe__step--human {
  background: var(--ink);
  border-color: var(--ink);
  color: var(--on-ink);
}
.pipe__step--human .pipe__body,
.pipe__step--human .pipe__num {
  color: color-mix(in srgb, var(--on-ink) 82%, transparent);
}
.pipe__num {
  font-size: var(--fs-12);
  color: var(--muted);
}
.pipe__title {
  font-size: var(--fs-16);
  font-weight: 700;
}
.pipe__body {
  font-size: var(--fs-14);
  color: var(--muted);
  line-height: 1.5;
}
.modes {
  display: grid;
  grid-template-columns: 8fr 4fr;
  gap: var(--gutter);
  margin-top: var(--s-5);
}
.modes__list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--s-3);
  margin: 0;
  padding: 0;
}
.mode {
  display: flex;
  flex-direction: column;
  gap: var(--s-2);
  padding: var(--s-4);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-card);
}
.mode.is-current {
  border-color: var(--ink);
}
.mode__label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: var(--fs-20);
  font-weight: 700;
  letter-spacing: -0.01em;
}
.mode__current {
  margin-left: auto;
  padding: 2px 8px;
  background: var(--ink);
  color: var(--on-ink);
  border-radius: var(--r-pill);
  font-size: var(--fs-12);
  font-weight: 600;
  letter-spacing: 0;
}
.mode__sub {
  font-size: var(--fs-14);
  font-weight: 600;
}
.mode__body {
  font-size: var(--fs-14);
  color: var(--muted);
}
.mode__env {
  margin-top: auto;
  padding: 6px 8px;
  background: var(--surface-2);
  border-radius: 6px;
  font-size: var(--fs-12);
  overflow-wrap: anywhere;
}
.ticks,
.credits {
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--s-3);
}
.ticks li,
.credits li {
  position: relative;
  padding-left: 22px;
  max-width: 68ch;
}
.ticks li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.55em;
  width: 9px;
  height: 9px;
  background: var(--green);
}
.ticks--limits li::before {
  background: transparent;
  border: 1.5px solid var(--amber);
  transform: rotate(45deg) scale(0.85);
}
.credits li::before {
  content: '';
  position: absolute;
  left: 2px;
  top: 0.7em;
  width: 8px;
  height: 1.5px;
  background: var(--muted);
}
.credits__main {
  font-size: var(--fs-20);
  font-weight: 600;
  letter-spacing: -0.01em;
}
.about__cta {
  margin-top: var(--s-8);
}
@media (max-width: 1100px) {
  .pipe {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .modes {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 760px) {
  .pipe,
  .modes__list {
    grid-template-columns: 1fr;
  }
  .about__two {
    grid-template-columns: 1fr;
  }
}
@media (forced-colors: active) {
  .ticks li::before {
    background: CanvasText;
  }
}
</style>
