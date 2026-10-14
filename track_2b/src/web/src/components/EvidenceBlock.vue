<script setup lang="ts">
import { computed } from 'vue'
import { findQuote, segment, tokenizeHtml } from '@/lib/highlight'
import { guessLang } from '@/i18n/lang-guess'
import { t } from '@/i18n'

/**
 * DOM excerpt with the quoted span highlighted, plus a screenshot crop.
 * Page content is rendered as text (never as HTML) and carries the `lang`
 * of its own language, so screen readers read a French excerpt in French.
 */
const props = defineProps<{ source: string; quote: string; screenshot?: string | null; lang?: string }>()

const range = computed(() => findQuote(props.source, props.quote))
const segments = computed(() => segment(tokenizeHtml(props.source), range.value))
const quoteMissing = computed(() => !!props.quote && !range.value)
const contentLang = computed(() => props.lang ?? guessLang(props.quote) ?? guessLang(props.source))
</script>

<template>
  <figure class="evidence">
    <pre v-if="source" class="evidence__code" :lang="contentLang" translate="no" tabindex="0" role="region" :aria-label="t('finding.codeExcerpt')"><code><template
      v-for="(seg, si) in segments" :key="si"><mark v-if="seg.mark" class="evidence__mark"><span
        v-for="(tok, ti) in seg.toks" :key="ti" :class="`tk-${tok.kind}`">{{ tok.text }}</span></mark><template v-else><span
        v-for="(tok, ti) in seg.toks" :key="ti" :class="`tk-${tok.kind}`">{{ tok.text }}</span></template></template></code></pre>
    <p v-if="quoteMissing" class="evidence__quote" :lang="contentLang"><mark>{{ quote }}</mark></p>
    <figcaption class="evidence__caption">
      <span class="evidence__swatch" aria-hidden="true" />{{ t('finding.quoted') }}
    </figcaption>
    <div v-if="screenshot" class="evidence__shot-wrap">
      <div class="evidence__shot">
        <img :src="screenshot" :alt="t('finding.screenshotAlt')" loading="lazy" decoding="async" />
      </div>
      <p class="evidence__shot-label">{{ t('finding.screenshot') }}</p>
    </div>
  </figure>
</template>

<style scoped>
.evidence {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--s-2);
}
.evidence__code {
  margin: 0;
  padding: 14px 16px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  border-radius: var(--r-control);
  font-size: 0.8125rem;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: anywhere;
  max-height: 320px;
  overflow: auto;
}
.evidence__mark {
  background: var(--mark-bg);
  color: var(--mark-ink);
  box-shadow: 0 0 0 2px var(--mark-bg);
  border-radius: 2px;
  text-decoration: underline;
  text-decoration-thickness: 2px;
  text-underline-offset: 3px;
  text-decoration-color: var(--klar-red);
}
.evidence__mark span {
  color: inherit !important;
}
.tk-tag {
  color: var(--syn-tag);
  font-weight: 700;
}
.tk-attr {
  color: var(--syn-attr);
}
.tk-value {
  color: var(--syn-value);
}
.tk-punct,
.tk-comment {
  color: var(--syn-punct);
}
.tk-text {
  color: var(--ink);
}
.evidence__quote {
  font-size: var(--fs-14);
}
.evidence__caption {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: var(--fs-12);
  color: var(--muted);
}
.evidence__swatch {
  width: 14px;
  height: 10px;
  background: var(--mark-bg);
  border-bottom: 2px solid var(--klar-red);
}
.evidence__shot-wrap {
  display: flex;
  flex-direction: column;
  gap: var(--s-2);
  margin-top: var(--s-3);
}
.evidence__shot {
  position: relative;
  border: 1px solid var(--line);
  border-radius: var(--r-control);
  overflow: hidden;
  background:
    repeating-conic-gradient(var(--surface-2) 0% 25%, var(--surface) 0% 50%) 50% / 16px 16px;
}
.evidence__shot img {
  width: 100%;
  height: auto;
}
.evidence__shot-label {
  font-size: var(--fs-12);
  color: var(--muted);
}
@media (forced-colors: active) {
  .evidence__mark {
    forced-color-adjust: none;
    background: Mark;
    color: MarkText;
  }
}
</style>
