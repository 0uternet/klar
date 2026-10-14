/**
 * Tiny stop-word language guesser for DE / FR / IT / EN snippets.
 * Used only to put a correct `lang` attribute on quoted page content
 * (WCAG 3.1.2 for Klar. itself), never to judge a finding.
 */
import type { UiLang } from '@/types'

const WORDS: Record<UiLang, string[]> = {
  de: ['der', 'die', 'das', 'und', 'ist', 'nicht', 'mit', 'für', 'auf', 'den', 'dem', 'des', 'ein', 'eine', 'sie', 'wir', 'im', 'zu', 'von', 'bei', 'sich', 'auch', 'nur', 'oder', 'wird', 'sind', 'klicken', 'mehr', 'bitte', 'zum', 'zur', 'über', 'unten', 'rechts', 'gemeinde', 'seite', 'bild', 'feld', 'fehler', 'diverses', 'ihre', 'ihr', 'finden', 'alle', 'neue', 'erhalten', 'weitere', 'deutsch', 'abfall'],
  fr: ['le', 'la', 'les', 'et', 'est', 'des', 'une', 'un', 'du', 'pour', 'pas', 'que', 'qui', 'dans', 'sur', 'au', 'aux', 'vous', 'nous', 'avec', 'ce', 'ces', 'en', 'tous', 'peuvent', 'commune', 'accueil', 'plus', 'français', 'habitants', 'documents', 'guichet', 'obtenir', 'de'],
  it: ['il', 'lo', 'gli', 'e', 'è', 'di', 'che', 'per', 'non', 'una', 'del', 'della', 'dei', 'con', 'sono', 'anche', 'nel', 'nella', 'alla', 'presso', 'comune', 'programma', 'completo', 'disponibile', 'italiano', 'leggi', 'più', 'pagina', 'iniziale'],
  en: ['the', 'and', 'is', 'are', 'of', 'to', 'in', 'for', 'with', 'you', 'your', 'this', 'that', 'on', 'not', 'be', 'it', 'by', 'or', 'as', 'welcome', 'information', 'english', 'read', 'more'],
}

const SETS = Object.fromEntries(Object.entries(WORDS).map(([l, w]) => [l, new Set(w)])) as Record<UiLang, Set<string>>

export function guessLang(text: string | null | undefined): UiLang | undefined {
  if (!text) return undefined
  const plain = text
    .replace(/<[^>]*>/g, ' ')
    .replace(/&[a-z]+;/gi, ' ')
    .toLowerCase()
  const tokens = plain.match(/[\p{L}’']+/gu)
  if (!tokens || tokens.length === 0) return undefined
  const scores: Record<UiLang, number> = { de: 0, fr: 0, it: 0, en: 0 }
  for (const raw of tokens) {
    const tok = raw.replace(/^(l|d|qu|n|s|c|j|un|dell|all|nell|sull)[’']/, '')
    for (const l of Object.keys(SETS) as UiLang[]) if (SETS[l].has(tok)) scores[l]++
  }
  // French/Italian elisions are a strong signal.
  if (/\b(l|d|qu|n)[’'][a-zàâéèêîôû]/i.test(plain)) scores.fr += 0.5
  if (/\b(dell|all|nell|un)[’'][a-zàèéìòù]/i.test(plain)) scores.it += 0.5
  if (/[äöü]/.test(plain)) scores.de += 1
  if (/[çœ]|[éèê]\w/.test(plain)) scores.fr += 0.5
  const ranked = (Object.entries(scores) as [UiLang, number][]).sort((a, b) => b[1] - a[1])
  const [best, second] = ranked
  if (!best || best[1] < 1) return undefined
  if (second && best[1] - second[1] < 0.5) return undefined
  return best[0]
}
