<script setup lang="ts">
import { computed, ref } from 'vue'
import { Check, Copy } from '@lucide/vue'
import { parseDiff } from '@/lib/diff'
import { guessLang } from '@/i18n/lang-guess'
import { t } from '@/i18n'

/**
 * Unified diff with +/− signs (not colour alone), word-level emphasis on the
 * changed part, and a "copy" action for the fixed lines.
 */
const props = withDefaults(defineProps<{ diff: string; bare?: boolean; lang?: string }>(), { bare: false })

const parsed = computed(() => parseDiff(props.diff))
/** Content language from the backend (Finding.content_lang) when known; a local guess otherwise. */
const contentLang = computed(() => props.lang ?? guessLang(parsed.value.lines.map((l) => l.text).join(' ')))
const fixed = computed(() =>
  parsed.value.lines
    .filter((l) => l.kind === 'add' || l.kind === 'ctx')
    .map((l) => l.text)
    .join('\n'),
)

const copied = ref(false)
async function copy() {
  try {
    await navigator.clipboard.writeText(fixed.value)
    copied.value = true
    window.setTimeout(() => (copied.value = false), 1600)
  } catch {
    /* clipboard unavailable */
  }
}
</script>

<template>
  <figure class="diff" :class="{ 'diff--bare': bare }">
    <figcaption v-if="!bare" class="diff__head">
      <span class="diff__file mono">{{ parsed.file ?? t('diff.label') }}</span>
      <button type="button" class="btn btn--ghost btn--sm diff__copy" @click="copy">
        <component :is="copied ? Check : Copy" :size="14" aria-hidden="true" />
        {{ copied ? t('diff.copied') : t('diff.copy') }}
      </button>
      <span class="sr-only" role="status">{{ copied ? t('diff.copied') : '' }}</span>
    </figcaption>
    <div class="diff__body" :lang="contentLang" translate="no" :tabindex="bare ? undefined : 0" :role="bare ? undefined : 'region'" :aria-label="bare ? undefined : t('diff.label')">
      <template v-for="(l, i) in parsed.lines" :key="i">
        <div v-if="l.kind === 'hunk'" class="diff__hunk mono">{{ l.text }}</div>
        <div v-else class="diff__line" :class="`diff__line--${l.kind}`">
          <span class="diff__no mono" aria-hidden="true">{{ l.line }}</span>
          <span class="diff__sign mono" aria-hidden="true">{{ l.kind === 'add' ? '+' : l.kind === 'del' ? '−' : ' ' }}</span>
          <span v-if="l.kind === 'add'" class="sr-only">{{ t('diff.added') }}: </span>
          <span v-else-if="l.kind === 'del'" class="sr-only">{{ t('diff.removed') }}: </span>
          <code class="diff__code"><template v-for="(p, pi) in l.parts" :key="pi"><span v-if="p.em" class="diff__em">{{ p.text }}</span><template v-else>{{ p.text }}</template></template></code>
        </div>
      </template>
    </div>
  </figure>
</template>

<style scoped>
.diff {
  margin: 0;
  border: 1px solid var(--line);
  border-radius: var(--r-control);
  overflow: hidden;
  background: var(--surface);
}
.diff__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s-3);
  padding: 4px 4px 4px 12px;
  border-bottom: 1px solid var(--line);
  background: var(--surface-2);
}
.diff__file {
  font-size: var(--fs-12);
  color: var(--muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.diff__copy {
  --btn-h: 30px;
  font-size: var(--fs-12);
  color: var(--muted);
}
.diff__body {
  font-size: 0.8125rem;
  line-height: 1.65;
  max-height: 340px;
  overflow: auto;
}
.diff__body:focus-visible {
  outline-offset: -2px;
}
.diff--bare .diff__hunk {
  display: none;
}
.diff--bare .diff__no {
  display: none;
}
.diff--bare .diff__line {
  grid-template-columns: 1.6em 1fr;
  padding: 2px 0;
}
.diff__hunk {
  padding: 2px 12px;
  font-size: var(--fs-12);
  color: var(--muted);
  background: var(--surface-2);
}
.diff__line {
  display: grid;
  grid-template-columns: 3.2em 1.4em 1fr;
  align-items: start;
}
.diff__line--add {
  background: var(--diff-add);
}
.diff__line--del {
  background: var(--diff-del);
}
.diff__no {
  padding-right: 8px;
  text-align: right;
  font-size: var(--fs-12);
  line-height: 1.9;
  color: var(--muted);
  user-select: none;
}
.diff__sign {
  text-align: center;
  font-weight: 700;
  user-select: none;
}
.diff__line--add .diff__sign {
  color: var(--green);
}
.diff__line--del .diff__sign {
  color: var(--red-text);
}
.diff__code {
  padding-right: 12px;
  font-size: inherit;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-wrap: anywhere;
}
.diff__line--add .diff__em {
  background: var(--diff-add-strong);
  border-radius: 2px;
}
.diff__line--del .diff__em {
  background: var(--diff-del-strong);
  border-radius: 2px;
  text-decoration: line-through;
  text-decoration-thickness: 1px;
}
@media (forced-colors: active) {
  .diff__em {
    outline: 1px solid CanvasText;
  }
}
</style>
