/**
 * What a finding row says. Notes get a short title from their reason_code
 * (in the UI language); axe-core findings use their rule help; findings whose
 * impact is the backend's generic "a person must decide" sentence use the first
 * sentence of their specific explanation; everything else the backend's
 * user_impact (in the scan language).
 */
import type { Finding, UiLang } from '@/types'
import { t, type MessageKey } from '@/i18n'
import { isNote } from './group'

export interface RowTitle {
  text: string
  /** Language of the text: the UI language (null, inherited) or the scan language. */
  lang: UiLang | null
}

/** Reason codes with a plain row title of their own, besides the notes. */
const TITLED_REASONS: readonly string[] = ['language_switcher', 'phone_number']

/** klar/i18n.py "impact.review": says nothing about this element, so never a row title. */
export const GENERIC_IMPACT: readonly string[] = [
  'A person must decide whether this element is a barrier.',
  'Eine Person muss entscheiden, ob dieses Element eine Barriere ist.',
  'Une personne doit décider si cet élément constitue un obstacle.',
  'Una persona deve decidere se questo elemento è una barriera.',
]

/** Opening quote → its closing quote (French, English, German, straight). */
const QUOTES: Record<string, string> = { '«': '»', '‹': '›', '“': '”', '„': '“', '"': '"' }

/**
 * The first sentence of a text: up to the first . ; : ! or ? followed by a capital letter, else all
 * of it. Punctuation inside a quotation does not end the sentence: a quoted heading such as
 * « Willkommen in Biel. Bienvenue à Bienne. » stays whole.
 */
export function firstSentence(s: string): string {
  const x = s.replace(/\s+/g, ' ').trim()
  const open: string[] = []
  for (let i = 0; i < x.length; i++) {
    const c = x[i]!
    if (open.length && c === open[open.length - 1]) open.pop()
    else if (c in QUOTES) open.push(QUOTES[c]!)
    else if (!open.length && '.;:!?'.includes(c) && x[i + 1] === ' ' && /[A-ZÀ-ÖØ-Ý«“"„]/.test(x[i + 2] ?? '')) {
      return x.slice(0, i + 1).replace(/[;:]$/, '.')
    }
  }
  // An unmatched quote (an inch mark, a lone «) must not swallow the whole text: plain split instead.
  if (open.length) {
    const m = x.match(/^(.+?[.;:!?])\s(?=[A-ZÀ-ÖØ-Ý«“"])/)
    return (m ? m[1]! : x).replace(/[;:]$/, '.')
  }
  return x
}

export function rowTitle(f: Finding, scanLang: UiLang): RowTitle {
  if (isNote(f) || TITLED_REASONS.includes(f.reason_code)) return { text: t(`reason.${f.reason_code}` as MessageKey), lang: null }
  if (f.reason_code === 'axe') {
    const i = f.explanation.indexOf(': ')
    const help = i >= 0 ? f.explanation.slice(i + 2).trim() : ''
    if (help) return { text: help, lang: scanLang }
  }
  // A check-specific note (e.g. 2.4.5 "needs a URL") titles the row with its own reason.
  if (GENERIC_IMPACT.includes(f.user_impact.trim()) && f.explanation.trim()) return { text: firstSentence(f.explanation), lang: scanLang }
  return { text: f.user_impact, lang: scanLang }
}

/** The evidence line under a row title: the quote, on one line, at most 80 characters. */
export function evidenceLine(f: Finding, max = 80): string {
  const s = f.excerpt.replace(/\s+/g, ' ').trim()
  return s.length > max ? `${s.slice(0, max - 1)}…` : s
}
