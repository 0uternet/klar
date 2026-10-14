<script setup lang="ts">
import { computed, nextTick, ref, useId } from 'vue'
import { ArrowRight, Code2, FileCode2, Link2, Upload, X } from '@lucide/vue'
import { MAX_HTML_BYTES } from '@/config'
import type { CheckInput } from '@/types'
import { formatBytes, t, type MessageKey } from '@/i18n'
import KeyboardHint from './KeyboardHint.vue'

/**
 * Hero field: 56 px, 20 px text, "Check" inside on the right.
 * Three ways in: a web address, pasted HTML (its own mode, with an example to
 * insert), or an .html file (drop or upload; the upload button is the keyboard
 * alternative to dragging, WCAG 2.5.7).
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
const ids = { label: useId(), hint: useId(), error: useId(), example: useId() }

const describedBy = computed(() => [ids.hint, error.value ? ids.error : null].filter(Boolean).join(' '))
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
    class="hero-form"
    :class="{ 'is-dragging': dragging, 'has-error': !!error, 'is-secondary': secondary }"
    novalidate
    @submit.prevent="submit"
    @dragover.prevent="dragging = true"
    @dragleave.self="dragging = false"
    @drop.prevent="onDrop"
  >
    <label :id="ids.label" :for="mode === 'html' ? 'klar-html' : 'klar-url'" class="hero-form__label">{{ fieldLabel }}</label>

    <!-- Pasted HTML -->
    <div v-if="mode === 'html'" class="field-html">
      <textarea
        id="klar-html"
        ref="textarea"
        v-model="htmlText"
        class="field-html__area"
        rows="7"
        spellcheck="false"
        translate="no"
        :placeholder="t('home.form.htmlPlaceholder')"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="[describedBy, ids.example].join(' ')"
        @input="error = null"
      />
      <div class="field-html__bar">
        <button type="button" class="hero-form__link" @click="insertExample">
          <Code2 :size="14" aria-hidden="true" />{{ t('home.form.insertExample') }}
        </button>
        <button
          type="submit"
          class="btn field-hero__submit"
          :class="secondary ? 'btn--secondary' : 'btn--primary'"
          :disabled="busy"
          :aria-busy="busy ? 'true' : undefined"
        >
          <span v-if="busy" class="field-hero__spinner" aria-hidden="true" />
          <span>{{ busy ? t('home.form.starting') : t('home.form.submit') }}</span>
          <ArrowRight v-if="!busy" :size="18" aria-hidden="true" />
        </button>
      </div>
    </div>

    <!-- Web address or file -->
    <div v-else class="field-hero">
      <div v-if="mode === 'file' && file" class="field-hero__chip" role="group" :aria-labelledby="ids.label">
        <FileCode2 :size="18" aria-hidden="true" />
        <span class="field-hero__chip-text">{{ fileLabel }}</span>
        <button type="button" class="field-hero__chip-x" :aria-label="t('home.form.clear')" @click="clearFile">
          <X :size="16" aria-hidden="true" />
        </button>
      </div>
      <input
        v-else
        id="klar-url"
        ref="input"
        v-model="value"
        class="field-hero__input"
        type="text"
        inputmode="url"
        autocomplete="url"
        autocapitalize="off"
        spellcheck="false"
        :placeholder="t('home.form.placeholder')"
        :aria-invalid="error ? 'true' : undefined"
        :aria-describedby="describedBy"
        @paste="onPaste"
        @input="error = null"
        @focus="focused = true"
        @blur="focused = false"
      />
      <span v-if="mode === 'url' && !value && !focused" class="field-hero__key"><KeyboardHint :keys="['/']" /></span>
      <button
        type="submit"
        class="btn field-hero__submit"
        :class="secondary ? 'btn--secondary' : 'btn--primary'"
        :disabled="busy"
        :aria-busy="busy ? 'true' : undefined"
      >
        <span v-if="busy" class="field-hero__spinner" aria-hidden="true" />
        <span>{{ busy ? t('home.form.starting') : t('home.form.submit') }}</span>
        <ArrowRight v-if="!busy" :size="18" aria-hidden="true" />
      </button>
      <div v-if="dragging" class="field-hero__drop" aria-hidden="true">{{ t('home.form.drop') }}</div>
    </div>

    <p v-if="error" :id="ids.error" class="hero-form__error" role="alert">
      <span class="hero-form__error-mark" aria-hidden="true" />{{ error }}
    </p>

    <p v-if="mode === 'html'" :id="ids.example" class="hero-form__note">{{ t('home.form.exampleNote') }}</p>

    <div class="hero-form__hint">
      <span :id="ids.hint">{{ t('home.form.hint') }}</span>
      <button v-if="mode !== 'html'" type="button" class="hero-form__link" @click="setMode('html')">
        <Code2 :size="14" aria-hidden="true" />{{ t('home.form.pasteHtml') }}
      </button>
      <button v-else type="button" class="hero-form__link" @click="setMode('url')">
        <Link2 :size="14" aria-hidden="true" />{{ t('home.form.useUrl') }}
      </button>
      <button type="button" class="hero-form__link" @click="picker?.click()">
        <Upload :size="14" aria-hidden="true" />{{ t('home.form.upload') }}
      </button>
      <input ref="picker" type="file" accept=".html,.htm,text/html" class="sr-only" tabindex="-1" aria-hidden="true" @change="readFile(($event.target as HTMLInputElement).files?.[0])" />
    </div>
  </form>
</template>

<style scoped>
.hero-form {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--s-2);
  max-width: 760px;
}
.hero-form__label {
  font-size: var(--fs-14);
  font-weight: 600;
}
.field-hero {
  position: relative;
  display: flex;
  align-items: center;
  min-height: 56px;
  padding: 6px 6px 6px 0;
  background: var(--surface);
  border: 1.5px solid var(--ink);
  border-radius: var(--r-control);
  transition: box-shadow var(--dur-1) var(--ease);
}
.field-hero:focus-within {
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--blue) 22%, transparent);
}
.has-error .field-hero {
  border-color: var(--red-text);
}
.field-hero__input {
  flex: 1;
  min-width: 0;
  height: 44px;
  padding: 0 var(--s-4);
  border: 0;
  background: transparent;
  font-size: var(--fs-20);
  letter-spacing: -0.01em;
}
.field-hero__input:focus-visible {
  outline: none;
}
.field-hero__input::placeholder {
  color: var(--muted);
  opacity: 1;
}
.field-hero__chip {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: 8px;
  padding: 6px 6px 6px 12px;
  background: var(--surface-2);
  border-radius: 6px;
  font-size: var(--fs-16);
  font-weight: 500;
}
.field-hero__chip-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.field-hero__chip-x {
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--muted);
}
.field-hero__chip-x:hover {
  background: var(--surface-3);
  color: var(--ink);
}
.field-hero__submit {
  flex: none;
  margin-left: 6px;
  padding: 0 18px 0 20px;
  font-size: var(--fs-16);
}
.field-hero__spinner {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: klar-spin 0.8s linear infinite;
}
.field-hero__drop {
  position: absolute;
  inset: -1.5px;
  display: grid;
  place-items: center;
  background: color-mix(in srgb, var(--surface) 92%, transparent);
  border: 2px dashed var(--blue);
  border-radius: var(--r-control);
  font-weight: 600;
  color: var(--blue);
  pointer-events: none;
}
.hero-form__error {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--red-text);
  font-size: var(--fs-14);
  font-weight: 500;
}
.hero-form__error-mark {
  width: 9px;
  height: 9px;
  background: var(--klar-red);
  flex: none;
}
.hero-form__hint {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px var(--s-4);
  font-size: var(--fs-14);
  color: var(--muted);
}
.hero-form__note {
  font-size: var(--fs-14);
  color: var(--muted);
}
.field-html {
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border: 1.5px solid var(--ink);
  border-radius: var(--r-control);
  transition: box-shadow var(--dur-1) var(--ease);
}
.field-html:focus-within {
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--blue) 22%, transparent);
}
.has-error .field-html {
  border-color: var(--red-text);
}
.field-html__area {
  width: 100%;
  min-height: 160px;
  padding: 12px 14px;
  border: 0;
  border-radius: var(--r-control) var(--r-control) 0 0;
  background: transparent;
  font-family: var(--font-mono);
  font-size: var(--fs-14);
  line-height: 1.6;
  resize: vertical;
}
.field-html__area:focus-visible {
  outline: none;
}
.field-html__area::placeholder {
  color: var(--muted);
  opacity: 1;
}
.field-html__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--s-3);
  padding: 6px;
  border-top: 1px solid var(--line);
}
.is-secondary .field-hero,
.is-secondary .field-html {
  border-width: 1px;
  border-color: var(--control-border);
}
.hero-form__link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 0 8px;
  margin-left: -8px;
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--blue);
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 0.18em;
}
.hero-form__link:hover {
  background: var(--blue-tint);
}
.field-hero__key {
  flex: none;
  margin-right: 6px;
}
@media (max-width: 520px) {
  .field-hero {
    flex-wrap: wrap;
    padding: 6px;
  }
  .field-hero__input {
    flex-basis: 100%;
    padding: 0 10px;
    font-size: var(--fs-16);
  }
  .field-hero__submit {
    flex: 1;
    margin: 6px 0 0;
  }
  .field-hero__key {
    display: none;
  }
}
</style>
