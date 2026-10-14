/**
 * Lightweight i18n: one flat dictionary per language, typed against English.
 * `t()` reads the reactive `locale`, so templates re-render on language change.
 * The <html lang> attribute follows the UI language.
 */
import { ref, shallowReactive, watch } from 'vue'
import type { UiLang } from '@/types'
import { STORAGE } from '@/config'
import { en, type MessageKey } from './en'

/**
 * English ships with the app; German, French and Italian are separate chunks,
 * loaded before they are shown (main.ts waits for the initial language, the
 * language switcher for the new one), so no screen flashes in English.
 */
type Dict = Record<MessageKey, string>
const DICTS = shallowReactive<Partial<Record<UiLang, Dict>>>({ en })
const LOADERS: Record<Exclude<UiLang, 'en'>, () => Promise<Dict>> = {
  de: () => import('./de').then((m) => m.de),
  fr: () => import('./fr').then((m) => m.fr),
  it: () => import('./it').then((m) => m.it),
}

/** Load a language's dictionary (no-op for English or when already loaded). */
export async function loadLocale(l: UiLang): Promise<void> {
  if (DICTS[l] || l === 'en') return
  try {
    DICTS[l] = await LOADERS[l]()
  } catch {
    /* offline chunk: English stays the fallback */
  }
}

/** Endonyms, always shown in their own language (with a matching lang attribute). */
export const LANGUAGES: { code: UiLang; short: string; name: string }[] = [
  { code: 'en', short: 'EN', name: 'English' },
  { code: 'de', short: 'DE', name: 'Deutsch' },
  { code: 'fr', short: 'FR', name: 'Français' },
  { code: 'it', short: 'IT', name: 'Italiano' },
]

/** BCP 47 tags used for dates and numbers (Swiss conventions). */
const INTL_TAG: Record<UiLang, string> = { en: 'en-CH', de: 'de-CH', fr: 'fr-CH', it: 'it-CH' }

function isLang(v: unknown): v is UiLang {
  return v === 'en' || v === 'de' || v === 'fr' || v === 'it'
}

function initialLocale(): UiLang {
  try {
    const saved = localStorage.getItem(STORAGE.lang)
    if (isLang(saved)) return saved
  } catch {
    /* storage unavailable */
  }
  for (const l of navigator.languages ?? [navigator.language]) {
    const base = l?.slice(0, 2).toLowerCase()
    if (isLang(base)) return base
  }
  return 'en'
}

export const locale = ref<UiLang>(initialLocale())

/** Switch language once its dictionary is loaded (no flash of English). */
export async function setLocale(l: UiLang): Promise<void> {
  await loadLocale(l)
  locale.value = l
}

watch(
  locale,
  (l) => {
    if (typeof document !== 'undefined') document.documentElement.lang = l
    try {
      localStorage.setItem(STORAGE.lang, l)
    } catch {
      /* storage unavailable */
    }
  },
  { immediate: true },
)

/** French typography: narrow no-break space before ; ! ? and inside « ». */
function typo(s: string, l: UiLang): string {
  if (l !== 'fr') return s
  return s
    .replace(/ ([;!?»])/g, ' $1')
    .replace(/« /g, '« ')
    .replace(/ :/g, ' :')
}

function interpolate(s: string, params?: Record<string, string | number>): string {
  if (!params) return s
  return s.replace(/\{(\w+)\}/g, (m, k: string) => (k in params ? String(params[k]) : m))
}

export function t(key: MessageKey, params?: Record<string, string | number>, lang?: UiLang): string {
  const l = lang ?? locale.value
  const raw = DICTS[l]?.[key] ?? en[key] ?? key
  return typo(interpolate(raw, params), l)
}

export type PluralBase = {
  [K in MessageKey]: K extends `${infer B}.one` ? (`${B}.other` extends MessageKey ? B : never) : never
}[MessageKey]

/** Plural-aware translation: picks `<key>.one` or `<key>.other`. `{n}` is filled in. */
export function tp(key: PluralBase, n: number, params?: Record<string, string | number>): string {
  const rule = new Intl.PluralRules(INTL_TAG[locale.value]).select(n)
  const k = (rule === 'one' ? `${key}.one` : `${key}.other`) as MessageKey
  return t(k, { n: formatNumber(n), ...params })
}

/** Apply language-specific typography to free text (e.g. guided steps). */
export function polish(s: string, lang?: UiLang): string {
  return typo(s, lang ?? locale.value)
}

export function formatNumber(n: number, opts?: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat(INTL_TAG[locale.value], opts).format(n)
}

export function formatDate(iso: string, withTime = true): string {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return new Intl.DateTimeFormat(INTL_TAG[locale.value], {
    dateStyle: 'medium',
    ...(withTime ? { timeStyle: 'short' } : {}),
  }).format(d)
}

/** "12 seconds", "15 minutes", "15 Minuten" (time limits). */
export function formatDuration(seconds: number): string {
  const tag = INTL_TAG[locale.value]
  if (seconds < 90) return new Intl.NumberFormat(tag, { style: 'unit', unit: 'second', unitDisplay: 'long' }).format(Math.round(seconds))
  return new Intl.NumberFormat(tag, { style: 'unit', unit: 'minute', unitDisplay: 'long' }).format(Math.round(seconds / 60))
}

/** "5 minutes ago", "yesterday" (Recent checks, UX-10). */
export function formatRelative(iso: string, now = Date.now()): string {
  const d = Date.parse(iso)
  if (Number.isNaN(d)) return iso
  const s = Math.round((d - now) / 1000)
  const rtf = new Intl.RelativeTimeFormat(INTL_TAG[locale.value], { numeric: 'auto' })
  const abs = Math.abs(s)
  if (abs < 60) return rtf.format(s, 'second')
  if (abs < 3600) return rtf.format(Math.round(s / 60), 'minute')
  if (abs < 86400) return rtf.format(Math.round(s / 3600), 'hour')
  if (abs < 86400 * 30) return rtf.format(Math.round(s / 86400), 'day')
  return formatDate(iso, false)
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${formatNumber(bytes)} B`
  if (bytes < 1024 * 1024) return `${formatNumber(bytes / 1024, { maximumFractionDigits: 1 })} KB`
  return `${formatNumber(bytes / 1024 / 1024, { maximumFractionDigits: 1 })} MB`
}

export function languageName(l: string): string {
  try {
    return new Intl.DisplayNames([INTL_TAG[locale.value]], { type: 'language' }).of(l) ?? l
  } catch {
    return l
  }
}

export type { MessageKey }
