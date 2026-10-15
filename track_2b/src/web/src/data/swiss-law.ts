/**
 * Official sources for the Swiss context (Home "Why it matters", How it works "Swiss law in brief").
 * Every fact and URL is from _prive/SWISS_FACTS.md (checked 15 Oct 2026). Links open the
 * official text in the UI language where one exists; `lang` names the target's language
 * when it differs (rendered as hreflang).
 */
import type { UiLang } from '@/types'

/** The day the sources were last checked (shown as "Sources checked on …"). */
export const SOURCES_CHECKED = '2026-10-15'

type Localised = Partial<Record<UiLang, string>> & { de: string }

export interface Source {
  url: Localised
  /** Language of each URL's page (defaults to the URL's own UI language). */
  lang?: Partial<Record<UiLang, UiLang>>
}

const FEDLEX = (eli: string): Localised => ({
  de: `https://www.fedlex.admin.ch/eli/${eli}/de`,
  fr: `https://www.fedlex.admin.ch/eli/${eli}/fr`,
  it: `https://www.fedlex.admin.ch/eli/${eli}/it`,
})

export const SOURCES = {
  /** BehiG / LHand / LDis, SR 151.3, art. 14 (an English translation exists). */
  behig: { url: { ...FEDLEX('cc/2003/667'), en: 'https://www.fedlex.admin.ch/eli/cc/2003/667/en' } },
  /** BehiV / OHand / ODis, SR 151.31, art. 10 (no English version: EN links to German). */
  behiv: { url: FEDLEX('cc/2003/668'), lang: { en: 'de' } },
  /** eCH-0059 Accessibility Standard v3.0 (DE and FR pages only). */
  ech0059: {
    url: { de: 'https://www.ech.ch/de/ech/ech-0059/3.0', fr: 'https://www.ech.ch/fr/ech/ech-0059/3.0' },
    lang: { en: 'de', it: 'de' },
  },
  /** Basel-Stadt, Behindertenrechtegesetz (BRG), SG 140.500, § 6 (German only). */
  bsBrg: { url: { de: 'https://www.gesetzessammlung.bs.ch/app/de/texts_of_law/140.500' }, lang: { en: 'de', fr: 'de', it: 'de' } },
  /** Valais, VRIMB / ODIPH, SGS 850.60, art. 33 (German and French). */
  vsVrimb: {
    url: { de: 'https://lex.vs.ch/app/de/texts_of_law/850.60', fr: 'https://lex.vs.ch/app/fr/texts_of_law/850.60', it: 'https://lex.vs.ch/app/fr/texts_of_law/850.60' },
    lang: { en: 'de', it: 'fr' },
  },
  /** European Accessibility Act, Directive (EU) 2019/882. */
  eaa: {
    url: {
      de: 'https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32019L0882',
      fr: 'https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32019L0882',
      it: 'https://eur-lex.europa.eu/legal-content/IT/TXT/?uri=CELEX:32019L0882',
      en: 'https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019L0882',
    },
  },
  /** BehiG revision, business 25.020 (Curia Vista; status "In Kommission des Nationalrats" on 15 Oct 2026). */
  behigRevision: {
    url: {
      de: 'https://www.parlament.ch/de/ratsbetrieb/suche-curia-vista/geschaeft?AffairId=20250020',
      fr: 'https://www.parlament.ch/fr/ratsbetrieb/suche-curia-vista/geschaeft?AffairId=20250020',
      it: 'https://www.parlament.ch/it/ratsbetrieb/suche-curia-vista/geschaeft?AffairId=20250020',
    },
    lang: { en: 'de' },
  },
  /** CORRECTIV.Schweiz with Stiftung Zugang für alle, 27 Oct 2025 (German only). */
  correctiv: {
    url: { de: 'https://correctiv.org/barrierefreiheit/2025/10/27/diese-schweizer-gemeinde-websites-sind-nicht-barrierefrei/' },
    lang: { en: 'de', fr: 'de', it: 'de' },
  },
  /** Stiftung Zugang für alle, certification prices and duration (German). */
  accessForAll: { url: { de: 'https://access-for-all.ch/leistungen/zertifizierung/' }, lang: { en: 'de', fr: 'de', it: 'de' } },
  /** Regierungsrat Basel-Stadt, answer of 28 Jan 2026 to Interpellation Nr. 147 (Copilot Chat). */
  bsAi: { url: { de: 'https://grosserrat.bs.ch/dokumente/100411/000000411872.pdf' }, lang: { en: 'de', fr: 'de', it: 'de' } },
} satisfies Record<string, Source>

export type SourceId = keyof typeof SOURCES

/** The URL for the UI language (falling back to German), and its language when it differs. */
export function sourceLink(id: SourceId, ui: UiLang): { href: string; hreflang?: string } {
  const s: Source = SOURCES[id]
  const href = s.url[ui] ?? s.url.de
  const target = s.lang?.[ui] ?? (s.url[ui] ? ui : 'de')
  return target === ui ? { href } : { href, hreflang: target }
}
