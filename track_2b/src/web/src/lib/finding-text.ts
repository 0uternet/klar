/**
 * What a finding row says (UX-3). Notes get a short title from their reason_code
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

/** Reason codes with a plain row title of their own, besides the notes (FE-4). */
const TITLED_REASONS: readonly string[] = ['language_switcher', 'phone_number']

/** klar/i18n.py "impact.review": says nothing about this element, so never a row title. */
export const GENERIC_IMPACT: readonly string[] = [
  'A person must decide whether this element is a barrier.',
  'Eine Person muss entscheiden, ob dieses Element eine Barriere ist.',
  'Une personne doit décider si cet élément constitue un obstacle.',
  'Una persona deve decidere se questo elemento è una barriera.',
]

/** The first sentence of a text: up to the first . ; : ! or ? followed by a capital letter, else all of it. */
function firstSentence(s: string): string {
  const x = s.replace(/\s+/g, ' ').trim()
  const m = x.match(/^(.+?[.;:!?])\s(?=[A-ZÀ-ÖØ-Ý«“"])/)
  const out = (m ? m[1]! : x).replace(/[;:]$/, '.')
  return out
}

export function rowTitle(f: Finding, scanLang: UiLang): RowTitle {
  if (isNote(f) || TITLED_REASONS.includes(f.reason_code)) return { text: t(`reason.${f.reason_code}` as MessageKey), lang: null }
  if (f.reason_code === 'axe') {
    const i = f.explanation.indexOf(': ')
    const help = i >= 0 ? f.explanation.slice(i + 2).trim() : ''
    if (help) return { text: help, lang: scanLang }
  }
  // P2 (FE review): a check-specific note (e.g. 2.4.5 "needs a URL") titles the row with its own reason.
  if (GENERIC_IMPACT.includes(f.user_impact.trim()) && f.explanation.trim()) return { text: firstSentence(f.explanation), lang: scanLang }
  return { text: f.user_impact, lang: scanLang }
}

/** The evidence line under a row title: the quote, on one line, at most 80 characters. */
export function evidenceLine(f: Finding, max = 80): string {
  const s = f.excerpt.replace(/\s+/g, ' ').trim()
  return s.length > max ? `${s.slice(0, max - 1)}…` : s
}
