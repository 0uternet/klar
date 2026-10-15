<script setup lang="ts">
import { computed, nextTick, ref, useId } from 'vue'
import { ArrowRight, Code2, FileCode2, Globe, Upload, X } from '@lucide/vue'
import { MAX_HTML_BYTES } from '@/config'
import type { CheckInput } from '@/types'
import { formatBytes, t, type MessageKey } from '@/i18n'
import KeyboardHint from './KeyboardHint.vue'

/**
 * The primary action: one large field with "Check" inside on the right.
 * Three ways in: a web address, pasted HTML (its own mode, with an example to
 * insert and an upload button), or an .html file dropped on the field (the upload
 * button is the keyboard alternative to dragging, WCAG 2.5.7). The #aside slot sits
 * left of the quiet "Paste HTML or upload a file" switch, under the field.
 */
const props = withDefaults(defineProps<{ busy?: boolean; secondary?: boolean; label?: string }>(), {
  busy: false,
  secondary: false,
  label: undefined,
})
const emit = defineEmits<{ submit: [input: CheckInput] }>()

type FieldMode = 'url' | 'html' | 'file'
const mode = ref<FieldMode>('url')
const value = ref('')
const htmlText = ref('')
const file = ref<{ text: string; name: string } | null>(null)
const error = ref<string | null>(null)
const dragging = ref(false)
const focused = ref(false)
const input = ref<HTMLInputElement | null>(null)
const textarea = ref<HTMLTextAreaElement | null>(null)
const picker = ref<HTMLInputElement | null>(null)
const ids = { label: useId(), error: useId(), example: useId() }

const fileLabel = computed(() => (file.value ? t('home.form.file', { name: file.value.name, size: formatBytes(new Blob([file.value.text]).size) }) : ''))
const fieldLabel = computed(() => (mode.value === 'html' ? t('home.form.htmlLabel') : (props.label ?? t('home.form.label'))))

/** A small page with two known issues (3.1.2 and 1.1.1). Not a real site. */
const EXAMPLE_HTML = `<!doctype html>
<html lang="de">
<head><title>Steuern – Gemeinde Beispiel</title></head>
<body>
  <h1>Steuern</h1>
  <p>Die Steuererklärung 2026 kann bis 31. März eingereicht werden.</p>
  <p>Les habitants francophones peuvent obtenir tous les documents en français au guichet.</p>
  <img src="steuerertrag.png" alt="Bild" width="640" height="360">
</body>
</html>`

function looksLikeHtml(s: string): boolean {
  const x = s.trim()
  return x.startsWith('<') && /<\/?[a-z][\s\S]*>/i.test(x)
}

/** M7: a precise reason when the address is not usable (not a URL, not http(s), no domain). */
function normaliseUrl(raw: string): { url: string } | { error: MessageKey } {
  const s = raw.trim()
  const hasScheme = /^[a-z][a-z0-9+.-]*:/i.test(s) && !/^[^:/]+:\d+(\/|$)/.test(s)
  if (hasScheme && !/^https?:/i.test(s)) return { error: 'home.form.errorScheme' }
  const withScheme = /^https?:\/\//i.test(s) ? s : `https://${s.replace(/^https?:\/*/i, '')}`
  try {
    const u = new URL(withScheme)
    if (/\s/.test(s) || !u.hostname) return { error: 'home.form.errorUrl' }
    if (!u.hostname.includes('.') && u.hostname !== 'localhost' && !/^\[.*\]$/.test(u.hostname)) return { error: 'home.form.errorNoDot' }
    return { url: u.toString() }
  } catch {
    return { error: 'home.form.errorUrl' }
  }
}

async function setMode(m: FieldMode) {
  mode.value = m
  error.value = null
  await nextTick()
  if (m === 'html') textarea.value?.focus()
  else if (m === 'url') input.value?.focus()
}

function tooBig(text: string) {
  return new Blob([text]).size > MAX_HTML_BYTES
}

function onPaste(e: ClipboardEvent) {
  const text = e.clipboardData?.getData('text/plain') ?? ''
  if (looksLikeHtml(text)) {
    e.preventDefault()
    if (tooBig(text)) {
      error.value = t('home.form.errorPasteSize')
      return
    }
    htmlText.value = text
    void setMode('html')
  }
}

async function readFile(f: File | undefined | null) {
  if (!f) return
  if (!/\.html?$/i.test(f.name) && f.type !== 'text/html') {
    error.value = t('home.form.errorFileType')
    return
  }
  if (f.size > MAX_HTML_BYTES) {
    error.value = t('home.form.errorFile')
    return
  }
  file.value = { text: await f.text(), name: f.name }
  mode.value = 'file'
  error.value = null
}

function onPick(e: Event) {
  const el = e.target as HTMLInputElement
  void readFile(el.files?.[0])
  el.value = ''
}

function onDrop(e: DragEvent) {
  dragging.value = false
  const f = e.dataTransfer?.files?.[0]
  if (f) void readFile(f)
  else {
    const text = e.dataTransfer?.getData('text/plain') ?? ''
    if (looksLikeHtml(text)) {
      htmlText.value = text
      void setMode('html')
    } else if (text) value.value = text.trim()
  }
}

function clearFile() {
  file.value = null
  void setMode('url')
}

function insertExample() {
  htmlText.value = EXAMPLE_HTML
  error.value = null
  textarea.value?.focus()
}

function submit() {
  if (props.busy) return
  if (mode.value === 'file' && file.value) {
    emit('submit', { html: file.value.text, name: file.value.name })
    return
  }
  if (mode.value === 'html') {
    if (!htmlText.value.trim()) {
      error.value = t('home.form.errorHtmlEmpty')
      textarea.value?.focus()
      return
    }
    if (tooBig(htmlText.value)) {
      error.value = t('home.form.errorPasteSize')
      return
    }
    emit('submit', { html: htmlText.value, name: null })
    return
  }
  if (!value.value.trim()) {
    error.value = t('home.form.errorEmpty')
    input.value?.focus()
    return
  }
  const res = normaliseUrl(value.value)
  if ('error' in res) {
    error.value = t(res.error)
    input.value?.focus()
    return
  }
  error.value = null
  value.value = res.url
  emit('submit', { url: res.url })
}

function fill(url: string) {
  file.value = null
  mode.value = 'url'
  value.value = url
  error.value = null
}

defineExpose({
  focus: () => (mode.value === 'html' ? textarea.value?.focus() : input.value?.focus()),
  fill,
  submit,
  /** M13 "Paste HTML instead", M16 "Edit the HTML". */
  setMode: (m: 'url' | 'html') => setMode(m),
})
</script>

<template>
  <form
    class="uf"
    :class="{ 'is-dragging': dragging, 'has-error': !!error, 'is-secondary': secondary, 'is-busy': busy }"
    novalidate
    @submit.prevent="submit"
    @dragover.prevent="dragging = true"
    @dragleave.self="dragging = false"
    @drop.prevent="onDrop"
  >
    <label :id="ids.label" :for="mode === 'html' ? 'klar-html' : 'klar-url'" class="uf__label">{{ fieldLabel }}</label>

    <!-- Pasted HTML -->
    <div v-if="mode === 'html'" class="uf__html m-rise">
      <textarea
        id="klar-html"
        ref="textarea"
        v-model="htmlText"
        class="uf__area"
        rows="7"
        spellcheck="false"
        translate="no"
        :placeholder="t('home.form.htmlPlaceholder')"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="error ? `${ids.error} ${ids.example}` : ids.example"
        @input="error = null"
      />
      <div class="uf__bar">
        <div class="uf__tools">
          <button type="button" class="uf__tool" @click="insertExample">
            <Code2 :size="15" aria-hidden="true" />{{ t('home.form.insertExample') }}
          </button>
          <button type="button" class="uf__tool" @click="picker?.click()">
            <Upload :size="15" aria-hidden="true" />{{ t('home.form.upload') }}
          </button>
        </div>
        <button type="submit" class="btn uf__submit" :class="secondary ? 'btn--secondary' : 'btn--primary'" :disabled="busy" :aria-busy="busy ? 'true' : undefined">
          <span>{{ t('home.form.submit') }}</span>
          <span class="uf__glyph" aria-hidden="true"><ArrowRight class="uf__arrow" :size="18" /><span class="uf__spin" /></span>
        </button>
      </div>
    </div>

    <!-- Web address or file -->
    <div v-else class="uf__field">
      <span class="uf__lead" aria-hidden="true">
        <FileCode2 v-if="mode === 'file' && file" :size="20" />
        <Globe v-else :size="20" />
      </span>
      <div v-if="mode === 'file' && file" class="uf__chip" role="group" :aria-labelledby="ids.label">
        <span class="uf__chip-text">{{ fileLabel }}</span>
        <button type="button" class="uf__chip-x" :aria-label="t('home.form.clear')" @click="clearFile">
          <X :size="16" aria-hidden="true" />
        </button>
      </div>
      <input
        v-else
        id="klar-url"
        ref="input"
        v-model="value"
        class="uf__input"
        type="text"
        inputmode="url"
        autocomplete="url"
        autocapitalize="off"
        spellcheck="false"
        :placeholder="t('home.form.placeholder')"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="error ? ids.error : undefined"
        @paste="onPaste"
        @input="error = null"
        @focus="focused = true"
        @blur="focused = false"
      />
      <span v-if="mode === 'url' && !value && !focused" class="uf__key"><KeyboardHint :keys="['/']" /></span>
      <button type="submit" class="btn uf__submit" :class="secondary ? 'btn--secondary' : 'btn--primary'" :disabled="busy" :aria-busy="busy ? 'true' : undefined">
        <span>{{ t('home.form.submit') }}</span>
        <span class="uf__glyph" aria-hidden="true"><ArrowRight class="uf__arrow" :size="18" /><span class="uf__spin" /></span>
      </button>
      <div v-if="dragging" class="uf__drop" aria-hidden="true">{{ t('home.form.drop') }}</div>
    </div>

    <p v-if="error" :id="ids.error" class="uf__error" role="alert"><span class="uf__error-mark" aria-hidden="true" />{{ error }}</p>
    <p v-if="mode === 'html'" :id="ids.example" class="uf__note">{{ t('home.form.exampleNote') }}</p>

    <div class="uf__foot">
      <slot name="aside" />
      <button v-if="mode !== 'html'" type="button" class="uf__alt" @click="setMode('html')">
        <Code2 :size="15" aria-hidden="true" />{{ t('home.form.alt') }}
      </button>
      <button v-else type="button" class="uf__alt" @click="setMode('url')">
        <Globe :size="15" aria-hidden="true" />{{ t('home.form.useUrl') }}
      </button>
    </div>

    <input ref="picker" type="file" accept=".html,.htm,text/html" class="sr-only" tabindex="-1" aria-hidden="true" @change="onPick" />
    <span class="sr-only" role="status">{{ busy ? t('home.form.starting') : '' }}</span>
  </form>
</template>

<style scoped>
.uf {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--s-2);
  width: 100%;
  max-width: 640px;
}
.uf__label {
  font-size: var(--fs-14);
  font-weight: 600;
  color: var(--ink);
}

/* ---- The field: large, inline submit, soft focus glow ---- */
.uf__field,
.uf__html {
  position: relative;
  background: var(--surface);
  border: 1px solid var(--control-border);
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(15, 17, 21, 0.04), 0 10px 30px -18px rgba(15, 17, 21, 0.35);
}
.uf__field {
  display: flex;
  align-items: center;
  min-height: 64px;
  padding: 7px;
}
/* The glow is its own layer so only its opacity animates. */
.uf__field::after,
.uf__html::after {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: inherit;
  box-shadow: 0 0 0 2px var(--blue), 0 0 0 7px color-mix(in srgb, var(--blue) 16%, transparent),
    0 16px 40px -16px color-mix(in srgb, var(--blue) 55%, transparent);
  opacity: 0;
  pointer-events: none;
  transition: opacity var(--dur-2) var(--ease-out);
}
.uf__field:focus-within::after,
.uf__html:focus-within::after {
  opacity: 1;
}
.has-error .uf__field,
.has-error .uf__html {
  border-color: var(--red-text);
}
.is-secondary .uf__field,
.is-secondary .uf__html {
  box-shadow: none;
}
.uf__lead {
  flex: none;
  display: grid;
  place-items: center;
  width: 40px;
  color: var(--muted);
}
.uf__input {
  flex: 1;
  min-width: 0;
  height: 48px;
  padding: 0 var(--s-2) 0 2px;
  border: 0;
  background: transparent;
  font-size: var(--fs-20);
  letter-spacing: -0.01em;
}
.uf__input:focus-visible {
  outline: none;
}
.uf__input::placeholder {
  color: var(--muted);
  opacity: 1;
}
.uf__key {
  flex: none;
  margin-right: 8px;
}
.uf__submit {
  --btn-h: 48px;
  flex: none;
  gap: 10px;
  padding: 0 18px 0 22px;
  border-radius: 10px;
  font-size: var(--fs-16);
}
/* Busy: the arrow slides out, a spinner fades in at the same spot (no layout shift). */
.uf__glyph {
  position: relative;
  display: grid;
  place-items: center;
  width: 18px;
  height: 18px;
}
.uf__arrow,
.uf__spin {
  grid-area: 1 / 1;
  transition: opacity var(--dur-2) var(--ease-out), transform var(--dur-2) var(--ease-out);
}
@media (hover: hover) {
  .uf__submit:hover:not(:disabled) .uf__arrow {
    transform: translateX(2px);
  }
}
.uf__spin {
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  opacity: 0;
  transform: scale(0.5);
}
.is-busy .uf__arrow,
.is-busy .uf__submit:hover .uf__arrow {
  opacity: 0;
  transform: translateX(10px);
}
.is-busy .uf__spin {
  opacity: 1;
  transform: none;
  animation: klar-spin 0.8s linear infinite;
}
.is-busy .uf__submit:disabled {
  opacity: 0.8;
  cursor: progress;
}

/* ---- A dropped file ---- */
.uf__chip {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-right: 8px;
  padding: 6px 6px 6px 12px;
  background: var(--surface-2);
  border-radius: 8px;
  font-size: var(--fs-16);
  font-weight: 500;
}
.uf__chip-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.uf__chip-x {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--muted);
}
.uf__chip-x:hover {
  background: var(--surface-3);
  color: var(--ink);
}
.uf__drop {
  position: absolute;
  inset: -1px;
  z-index: 1;
  display: grid;
  place-items: center;
  background: color-mix(in srgb, var(--surface) 94%, transparent);
  border: 2px dashed var(--blue);
  border-radius: inherit;
  font-weight: 600;
  color: var(--blue);
  pointer-events: none;
}

/* ---- Pasted HTML ---- */
.uf__html {
  display: flex;
  flex-direction: column;
}
.uf__area {
  width: 100%;
  min-height: 168px;
  padding: 14px 16px;
  border: 0;
  border-radius: 14px 14px 0 0;
  background: transparent;
  font-family: var(--font-mono);
  font-size: var(--fs-14);
  line-height: 1.6;
  resize: vertical;
}
.uf__area:focus-visible {
  outline: none;
}
.uf__area::placeholder {
  color: var(--muted);
  opacity: 1;
}
.uf__bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--s-2);
  padding: 7px;
  border-top: 1px solid var(--line);
}
.uf__tools {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
}
.uf__tool,
.uf__alt {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 36px;
  padding: 0 10px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--muted);
  font-size: var(--fs-14);
  font-weight: 600;
  transition: color var(--dur-1) var(--ease-out), background-color var(--dur-1) var(--ease-out);
}
.uf__tool:hover,
.uf__alt:hover {
  color: var(--ink);
  background: var(--surface-2);
}

/* ---- Under the field ---- */
.uf__error {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding-top: 2px;
  color: var(--red-text);
  font-size: var(--fs-14);
  font-weight: 500;
  overflow-wrap: anywhere;
  animation: klar-fade-up var(--dur-2) var(--ease-out);
}
.uf__error-mark {
  flex: none;
  width: 8px;
  height: 8px;
  background: var(--klar-red);
  transform: translateY(-1px);
}
.uf__note {
  font-size: var(--fs-14);
  color: var(--muted);
}
.uf__foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--s-2) var(--s-4);
  margin-top: var(--s-2);
}
/* Text aligns with the content edge; the padding only shows as the hover background. */
.uf__alt {
  margin-left: -10px;
}

@media (max-width: 520px) {
  .uf__field {
    flex-wrap: wrap;
  }
  .uf__lead {
    width: 32px;
  }
  .uf__input {
    flex-basis: 0;
    font-size: var(--fs-16);
  }
  .uf__chip {
    margin-right: 0;
  }
  .uf__field .uf__submit {
    flex: 1 0 100%;
    margin-top: 6px;
  }
  .uf__key {
    display: none;
  }
}
@media (forced-colors: active) {
  .uf__field:focus-within,
  .uf__html:focus-within {
    outline: 2px solid Highlight;
    outline-offset: 2px;
  }
  .uf__error-mark {
    background: CanvasText;
  }
}
</style>
