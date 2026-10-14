import type { Level, UiLang } from '@/types'

/**
 * The 50 WCAG 2.1 level A + AA success criteria: titles, slugs and plain-language
 * names in the four UI languages. Labels only: how Klar. covers each criterion
 * (method, implemented, evaluated) comes from the backend (GET /api/criteria).
 * `title` is the official W3C title (EN); EN 301 549 maps web content to 9.<sc>.
 */
export interface WcagCriterion {
  code: string
  principle: 1 | 2 | 3 | 4
  level: Level
  title: string
  slug: string
  plain: Record<UiLang, string>
}

type Row = [code: string, level: Level, title: string, slug: string, en: string, de: string, fr: string, it: string]

const ROWS: Row[] = [
  ['1.1.1', 'A', 'Non-text Content', 'non-text-content', 'Text alternatives', 'Textalternativen', 'Alternatives textuelles', 'Alternative testuali'],
  ['1.2.1', 'A', 'Audio-only and Video-only (Prerecorded)', 'audio-only-and-video-only-prerecorded', 'Audio-only and video-only', 'Reine Audio- und Videoinhalte', 'Audio seul ou vidéo seule', 'Solo audio e solo video'],
  ['1.2.2', 'A', 'Captions (Prerecorded)', 'captions-prerecorded', 'Captions', 'Untertitel', 'Sous-titres', 'Sottotitoli'],
  ['1.2.3', 'A', 'Audio Description or Media Alternative (Prerecorded)', 'audio-description-or-media-alternative-prerecorded', 'Audio description or transcript', 'Audiodeskription oder Transkript', 'Audiodescription ou transcription', 'Audiodescrizione o trascrizione'],
  ['1.2.4', 'AA', 'Captions (Live)', 'captions-live', 'Live captions', 'Live-Untertitel', 'Sous-titres en direct', 'Sottotitoli in diretta'],
  ['1.2.5', 'AA', 'Audio Description (Prerecorded)', 'audio-description-prerecorded', 'Audio description', 'Audiodeskription', 'Audiodescription', 'Audiodescrizione'],
  ['1.3.1', 'A', 'Info and Relationships', 'info-and-relationships', 'Structure in the code', 'Struktur im Code', 'Structure dans le code', 'Struttura nel codice'],
  ['1.3.2', 'A', 'Meaningful Sequence', 'meaningful-sequence', 'Reading order', 'Lesereihenfolge', 'Ordre de lecture', 'Ordine di lettura'],
  ['1.3.3', 'A', 'Sensory Characteristics', 'sensory-characteristics', 'Instructions by look or place', 'Anweisungen über Aussehen oder Ort', 'Consignes visuelles ou spatiales', 'Istruzioni visive o spaziali'],
  ['1.3.4', 'AA', 'Orientation', 'orientation', 'Screen orientation', 'Bildschirmausrichtung', 'Orientation de l’écran', 'Orientamento dello schermo'],
  ['1.3.5', 'AA', 'Identify Input Purpose', 'identify-input-purpose', 'Input purpose', 'Zweck von Eingabefeldern', 'Finalité des champs', 'Scopo dei campi'],
  ['1.4.1', 'A', 'Use of Color', 'use-of-color', 'Not colour alone', 'Nicht nur Farbe', 'Pas seulement la couleur', 'Non solo il colore'],
  ['1.4.2', 'A', 'Audio Control', 'audio-control', 'Audio control', 'Audio-Steuerung', 'Contrôle du son', 'Controllo dell’audio'],
  ['1.4.3', 'AA', 'Contrast (Minimum)', 'contrast-minimum', 'Text contrast', 'Textkontrast', 'Contraste du texte', 'Contrasto del testo'],
  ['1.4.4', 'AA', 'Resize text', 'resize-text', 'Text resize', 'Textgrösse ändern', 'Agrandissement du texte', 'Ridimensionamento del testo'],
  ['1.4.5', 'AA', 'Images of Text', 'images-of-text', 'Images of text', 'Bilder von Text', 'Texte sous forme d’image', 'Immagini di testo'],
  ['1.4.10', 'AA', 'Reflow', 'reflow', 'Reflow', 'Umbruch ohne Scrollen', 'Redistribution', 'Ridisposizione'],
  ['1.4.11', 'AA', 'Non-text Contrast', 'non-text-contrast', 'Non-text contrast', 'Kontrast von Grafiken', 'Contraste des éléments graphiques', 'Contrasto non testuale'],
  ['1.4.12', 'AA', 'Text Spacing', 'text-spacing', 'Text spacing', 'Textabstände', 'Espacement du texte', 'Spaziatura del testo'],
  ['1.4.13', 'AA', 'Content on Hover or Focus', 'content-on-hover-or-focus', 'Hover and focus content', 'Inhalte bei Hover oder Fokus', 'Contenu au survol ou au focus', 'Contenuti al passaggio o al focus'],
  ['2.1.1', 'A', 'Keyboard', 'keyboard', 'Keyboard', 'Tastatur', 'Clavier', 'Tastiera'],
  ['2.1.2', 'A', 'No Keyboard Trap', 'no-keyboard-trap', 'No keyboard trap', 'Keine Tastaturfalle', 'Pas de piège au clavier', 'Nessuna trappola da tastiera'],
  ['2.1.4', 'A', 'Character Key Shortcuts', 'character-key-shortcuts', 'Single-key shortcuts', 'Tastenkürzel mit einer Taste', 'Raccourcis à une touche', 'Scorciatoie a un tasto'],
  ['2.2.1', 'A', 'Timing Adjustable', 'timing-adjustable', 'Time limits', 'Zeitlimits', 'Limites de temps', 'Limiti di tempo'],
  ['2.2.2', 'A', 'Pause, Stop, Hide', 'pause-stop-hide', 'Pause, stop, hide', 'Pausieren, stoppen, ausblenden', 'Mettre en pause, arrêter, masquer', 'Mettere in pausa, fermare, nascondere'],
  ['2.3.1', 'A', 'Three Flashes or Below Threshold', 'three-flashes-or-below-threshold', 'Flashing', 'Blitzen', 'Flashs lumineux', 'Lampeggiamenti'],
  ['2.4.1', 'A', 'Bypass Blocks', 'bypass-blocks', 'Skip repeated blocks', 'Blöcke überspringen', 'Contourner des blocs', 'Saltare blocchi'],
  ['2.4.2', 'A', 'Page Titled', 'page-titled', 'Page title', 'Seitentitel', 'Titre de page', 'Titolo della pagina'],
  ['2.4.3', 'A', 'Focus Order', 'focus-order', 'Focus order', 'Fokusreihenfolge', 'Ordre du focus', 'Ordine del focus'],
  ['2.4.4', 'A', 'Link Purpose (In Context)', 'link-purpose-in-context', 'Link purpose', 'Linkzweck', 'Fonction du lien', 'Scopo del link'],
  ['2.4.5', 'AA', 'Multiple Ways', 'multiple-ways', 'Multiple ways', 'Mehrere Zugangswege', 'Accès multiples', 'Più modalità'],
  ['2.4.6', 'AA', 'Headings and Labels', 'headings-and-labels', 'Headings and labels', 'Überschriften und Beschriftungen', 'En-têtes et étiquettes', 'Intestazioni ed etichette'],
  ['2.4.7', 'AA', 'Focus Visible', 'focus-visible', 'Visible focus', 'Sichtbarer Fokus', 'Focus visible', 'Focus visibile'],
  ['2.5.1', 'A', 'Pointer Gestures', 'pointer-gestures', 'Pointer gestures', 'Zeigergesten', 'Gestes du pointeur', 'Gesti del puntatore'],
  ['2.5.2', 'A', 'Pointer Cancellation', 'pointer-cancellation', 'Pointer cancellation', 'Zeigeraktion abbrechen', 'Annulation du pointeur', 'Annullamento del puntatore'],
  ['2.5.3', 'A', 'Label in Name', 'label-in-name', 'Label in name', 'Beschriftung im Namen', 'Étiquette dans le nom', 'Etichetta nel nome'],
  ['2.5.4', 'A', 'Motion Actuation', 'motion-actuation', 'Motion actuation', 'Auslösung durch Bewegung', 'Activation par le mouvement', 'Azionamento tramite movimento'],
  ['3.1.1', 'A', 'Language of Page', 'language-of-page', 'Page language', 'Sprache der Seite', 'Langue de la page', 'Lingua della pagina'],
  ['3.1.2', 'AA', 'Language of Parts', 'language-of-parts', 'Language of parts', 'Sprache von Textteilen', 'Langue d’un passage', 'Lingua di parti del testo'],
  ['3.2.1', 'A', 'On Focus', 'on-focus', 'On focus', 'Bei Fokus', 'Au focus', 'Al focus'],
  ['3.2.2', 'A', 'On Input', 'on-input', 'On input', 'Bei Eingabe', 'À la saisie', 'All’input'],
  ['3.2.3', 'AA', 'Consistent Navigation', 'consistent-navigation', 'Consistent navigation', 'Einheitliche Navigation', 'Navigation cohérente', 'Navigazione coerente'],
  ['3.2.4', 'AA', 'Consistent Identification', 'consistent-identification', 'Consistent naming', 'Einheitliche Bezeichnung', 'Identification cohérente', 'Identificazione coerente'],
  ['3.3.1', 'A', 'Error Identification', 'error-identification', 'Error identification', 'Fehlererkennung', 'Identification des erreurs', 'Identificazione degli errori'],
  ['3.3.2', 'A', 'Labels or Instructions', 'labels-or-instructions', 'Labels or instructions', 'Beschriftungen oder Anweisungen', 'Étiquettes ou instructions', 'Etichette o istruzioni'],
  ['3.3.3', 'AA', 'Error Suggestion', 'error-suggestion', 'Error suggestion', 'Korrekturvorschläge', 'Suggestion après une erreur', 'Suggerimenti per gli errori'],
  ['3.3.4', 'AA', 'Error Prevention (Legal, Financial, Data)', 'error-prevention-legal-financial-data', 'Error prevention', 'Fehlervermeidung', 'Prévention des erreurs', 'Prevenzione degli errori'],
  ['4.1.1', 'A', 'Parsing', 'parsing', 'Parsing', 'Syntaxanalyse', 'Analyse syntaxique', 'Analisi sintattica'],
  ['4.1.2', 'A', 'Name, Role, Value', 'name-role-value', 'Name, role, value', 'Name, Rolle, Wert', 'Nom, rôle et valeur', 'Nome, ruolo, valore'],
  ['4.1.3', 'AA', 'Status Messages', 'status-messages', 'Status messages', 'Statusmeldungen', 'Messages d’état', 'Messaggi di stato'],
]

export const CRITERIA: readonly WcagCriterion[] = ROWS.map(([code, level, title, slug, en, de, fr, it]) => ({
  code,
  principle: Number(code[0]) as 1 | 2 | 3 | 4,
  level,
  title,
  slug,
  plain: { en, de, fr, it },
}))

const BY_CODE = new Map(CRITERIA.map((c) => [c.code, c]))

export function criterion(code: string): WcagCriterion | undefined {
  return BY_CODE.get(code)
}

export function plainName(code: string, lang: UiLang, fallback = ''): string {
  return BY_CODE.get(code)?.plain[lang] ?? fallback
}

export function en301549(code: string): string {
  return `9.${code}`
}

export function understandingUrl(code: string): string {
  const c = BY_CODE.get(code)
  return c
    ? `https://www.w3.org/WAI/WCAG21/Understanding/${c.slug}.html`
    : 'https://www.w3.org/WAI/WCAG21/Understanding/'
}

export function actRuleUrl(id: string): string {
  return `https://www.w3.org/WAI/standards-guidelines/act/rules/${encodeURIComponent(id)}/`
}

/** Compare "1.4.10" and "1.4.4" numerically. */
export function compareCodes(a: string, b: string): number {
  const pa = a.split('.').map(Number)
  const pb = b.split('.').map(Number)
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const d = (pa[i] ?? 0) - (pb[i] ?? 0)
    if (d !== 0) return d
  }
  return 0
}


export const PRINCIPLES = [1, 2, 3, 4] as const
