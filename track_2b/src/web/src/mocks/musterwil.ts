/**
 * MOCK-UP DATA — dev server or `npm run build:demo` only, never in production builds.
 * A simulated scan of the fictional trilingual site "Gemeinde Musterwil", in the
 * shape of `klar/models.py` (Scan, Finding). Texts exist in the four UI languages;
 * fixes stay in the language of the content.
 */
import { DEMO_URL } from '@/config'
import { criterion as wcag, en301549 } from '@/data/wcag'
import { MOCK_CRITERIA, MOCK_IMPLEMENTED, MOCK_SENTINEL } from './criteria'
import type { AiRequests, Confidence, Finding, Mode, Outcome, ProgressStep, Scan, ScanStats, Source, UiLang } from '@/types'
import { guessLang } from '@/i18n/lang-guess'
import { ARROW_LINK, BANNER, CHART, FORM_BUTTONS, FORM_ERROR, LOGO, TOWN_HALL } from './images'

type L = Record<UiLang, string>

export interface FindingSpec {
  key: string
  criterion: string
  outcome: Outcome
  source: Source
  confidence: Confidence
  page: string
  selector: string
  excerpt: string
  context: Record<string, string>
  diff: string | null
  screenshot?: string
  act?: string
  impact: L
  explanation: L
  hint: L | null
}

const base = DEMO_URL.endsWith('/') ? DEMO_URL : `${DEMO_URL}/`
export const PAGES = {
  deHome: `${base}de/`,
  deNews: `${base}de/aktuelles.html`,
  deContact: `${base}de/kontakt.html`,
  deFinance: `${base}de/finanzen.html`,
  deWaste: `${base}de/abfall.html`,
  frHome: `${base}fr/`,
  itHome: `${base}it/`,
}

function diff(file: string, line: number, minus: string[], plus: string[]): string {
  return [
    `--- a/${file}`,
    `+++ b/${file}`,
    `@@ -${line},${minus.length} +${line},${plus.length} @@`,
    ...minus.map((l) => `-${l}`),
    ...plus.map((l) => `+${l}`),
  ].join('\n')
}

const FR_P = 'Les habitantes et habitants francophones peuvent obtenir tous les documents en français au guichet communal.'
const IT_P = 'Il programma completo è disponibile anche in italiano presso la cancelleria comunale.'
const DE_P = 'Weitere Informationen erhalten Sie nur auf Deutsch.'

const MEHR = [
  { href: 'aktuelles.html#dorfstrasse', heading: 'Sanierung Dorfstrasse', fix: 'Mehr zur Sanierung der Dorfstrasse', conf: 'high' },
  { href: 'aktuelles.html#oeffnungszeiten', heading: 'Neue Öffnungszeiten der Verwaltung', fix: 'Mehr zu den neuen Öffnungszeiten', conf: 'high' },
  { href: 'abfall.html#feiertage', heading: 'Kehrichtabfuhr an Feiertagen', fix: 'Mehr zur Kehrichtabfuhr an Feiertagen', conf: 'high' },
  { href: 'aktuelles.html#veloboerse', heading: 'Velobörse im Schulhaus Matt', fix: 'Mehr zur Velobörse', conf: 'medium' },
] as const

const mehrSpecs: FindingSpec[] = MEHR.map((m, i) => ({
  key: `mehr-${i + 1}`,
  criterion: '2.4.4',
  outcome: 'failed',
  source: 'apertus',
  confidence: m.conf,
  page: PAGES.deHome,
  selector: `main > section.aktuell > div.teaser:nth-of-type(${i + 1}) > p.mehr > a`,
  excerpt: 'Mehr',
  act: '5effbb',
  context: { element: `<a href="${m.href}">Mehr</a>`, link_text: 'Mehr', paragraph: 'Mehr', links_with_same_text: '4' },
  diff: diff('de/index.html', 61 + i * 7, [`<p class="mehr"><a href="${m.href}">Mehr</a></p>`], [`<p class="mehr"><a href="${m.href}">${m.fix}</a></p>`]),
  impact: {
    en: 'Screen-reader users hear “Mehr” four times and can’t tell where each link goes.',
    de: 'Screenreader-Nutzende hören viermal «Mehr» und wissen nicht, wohin welcher Link führt.',
    fr: 'Les utilisateurs de lecteurs d’écran entendent quatre fois « Mehr » sans savoir où mène chaque lien.',
    it: 'Chi usa uno screen reader sente quattro volte «Mehr» senza sapere dove porta ciascun link.',
  },
  explanation: {
    en: `The link’s own paragraph contains only “Mehr” (more). The heading above it, “${m.heading}”, is not programmatic context under WCAG 2.4.4, so the purpose can’t be determined from the link and its context. In a list of links, all four read “Mehr”.`,
    de: `Der Absatz des Links enthält nur «Mehr». Die Überschrift darüber, «${m.heading}», gilt nach WCAG 2.4.4 nicht als programmatischer Kontext. Der Zweck lässt sich also weder aus dem Link noch aus seinem Kontext erkennen. In einer Linkliste heissen alle vier «Mehr».`,
    fr: `Le paragraphe du lien ne contient que « Mehr » (plus). Le titre au-dessus, « ${m.heading} », n’est pas un contexte programmatique au sens du critère 2.4.4 : la fonction du lien ne ressort ni du lien ni de son contexte. Dans une liste de liens, les quatre s’appellent « Mehr ».`,
    it: `Il paragrafo del link contiene solo «Mehr» (di più). Il titolo sopra, «${m.heading}», non è contesto programmatico secondo il criterio 2.4.4: lo scopo non si ricava né dal link né dal suo contesto. In un elenco di link, tutti e quattro si chiamano «Mehr».`,
  },
  hint: {
    en: `Change the link text to “${m.fix}”. If the design needs a short text, add the rest as visually hidden text.`,
    de: `Ändern Sie den Linktext in «${m.fix}». Braucht das Design einen kurzen Text, ergänzen Sie den Rest als visuell verborgenen Text.`,
    fr: `Remplacez le texte du lien par « ${m.fix} ». Si la mise en page exige un texte court, ajoutez le reste en texte masqué visuellement.`,
    it: `Sostituire il testo del link con «${m.fix}». Se il design richiede un testo breve, aggiungere il resto come testo visivamente nascosto.`,
  },
}))

export const SPECS: FindingSpec[] = [
  {
    key: 'fr-paragraph',
    criterion: '3.1.2',
    outcome: 'failed',
    source: 'apertus',
    confidence: 'high',
    page: PAGES.deHome,
    selector: 'main > section#willkommen > p:nth-of-type(3)',
    excerpt: FR_P,
    act: 'off6ek',
    context: { element: `<p>${FR_P}</p>`, lang_declared: 'de', previous_sentence: 'Die Gemeindeverwaltung ist von Montag bis Freitag geöffnet.' },
    diff: diff('de/index.html', 42, [`<p>${FR_P}</p>`], [`<p lang="fr">${FR_P}</p>`]),
    impact: {
      en: 'Screen readers will read this French paragraph with German pronunciation.',
      de: 'Screenreader lesen diesen französischen Absatz mit deutscher Aussprache vor.',
      fr: 'Les lecteurs d’écran liront ce paragraphe français avec une prononciation allemande.',
      it: 'Gli screen reader leggeranno questo paragrafo francese con la pronuncia tedesca.',
    },
    explanation: {
      en: 'The page is declared as German (lang="de"), but this paragraph is entirely French. Without lang="fr", speech synthesis applies German pronunciation rules and braille displays use the wrong contraction table.',
      de: 'Die Seite ist als Deutsch ausgezeichnet (lang="de"), dieser Absatz ist aber vollständig französisch. Ohne lang="fr" verwendet die Sprachausgabe deutsche Ausspracheregeln, und Braillezeilen nutzen die falsche Kurzschrifttabelle.',
      fr: 'La page est déclarée en allemand (lang="de"), mais ce paragraphe est entièrement en français. Sans lang="fr", la synthèse vocale applique les règles de prononciation allemandes et les plages braille utilisent la mauvaise table d’abrégé.',
      it: 'La pagina è dichiarata in tedesco (lang="de"), ma questo paragrafo è interamente in francese. Senza lang="fr" la sintesi vocale applica le regole di pronuncia tedesche e i display braille usano la tabella di abbreviazioni sbagliata.',
    },
    hint: {
      en: 'In the editor, select the paragraph and set its language to French. If your CMS has no language option, ask your web agency to add lang="fr" to it.',
      de: 'Markieren Sie im Editor den Absatz und stellen Sie die Sprache auf Französisch. Bietet Ihr CMS keine Sprachoption, bitten Sie Ihre Webagentur, lang="fr" zu ergänzen.',
      fr: 'Dans l’éditeur, sélectionnez le paragraphe et réglez sa langue sur français. Si votre CMS n’a pas d’option de langue, demandez à votre agence web d’ajouter lang="fr".',
      it: 'Nell’editor selezionare il paragrafo e impostarne la lingua su francese. Se il CMS non offre questa opzione, chiedere all’agenzia web di aggiungere lang="fr".',
    },
  },
  {
    key: 'it-sentence',
    criterion: '3.1.2',
    outcome: 'failed',
    source: 'apertus',
    confidence: 'high',
    page: PAGES.deNews,
    selector: 'main article.news-item:nth-of-type(2) > p.hinweis',
    excerpt: IT_P,
    act: 'off6ek',
    context: { element: `<p class="hinweis">${IT_P}</p>`, lang_declared: 'de' },
    diff: diff('de/aktuelles.html', 27, [`<p class="hinweis">${IT_P}</p>`], [`<p class="hinweis" lang="it">${IT_P}</p>`]),
    impact: {
      en: 'This Italian sentence will be read with German pronunciation.',
      de: 'Dieser italienische Satz wird mit deutscher Aussprache vorgelesen.',
      fr: 'Cette phrase italienne sera lue avec une prononciation allemande.',
      it: 'Questa frase italiana verrà letta con la pronuncia tedesca.',
    },
    explanation: {
      en: 'The sentence is Italian but sits in a German page without its own lang attribute, so assistive technology keeps the German voice. Italian-speaking residents who rely on a screen reader will hardly understand it.',
      de: 'Der Satz ist italienisch, steht aber ohne eigenes lang-Attribut in einer deutschen Seite. Hilfsmittel behalten deshalb die deutsche Stimme bei. Italienischsprachige Einwohnerinnen und Einwohner mit Screenreader verstehen ihn kaum.',
      fr: 'La phrase est en italien mais se trouve dans une page allemande sans attribut lang propre : les aides techniques gardent la voix allemande. Les habitants italophones qui utilisent un lecteur d’écran la comprendront difficilement.',
      it: 'La frase è in italiano ma si trova in una pagina tedesca senza un proprio attributo lang: le tecnologie assistive mantengono la voce tedesca. Chi parla italiano e usa uno screen reader la capirà a fatica.',
    },
    hint: {
      en: 'Mark the sentence as Italian in the editor (language: Italian).',
      de: 'Zeichnen Sie den Satz im Editor als Italienisch aus (Sprache: Italienisch).',
      fr: 'Dans l’éditeur, marquez la phrase comme italienne (langue : italien).',
      it: 'Nell’editor contrassegnare la frase come italiana (lingua: italiano).',
    },
  },
  {
    key: 'public-viewing',
    criterion: '3.1.2',
    outcome: 'cantTell',
    source: 'apertus',
    confidence: 'medium',
    page: PAGES.deNews,
    selector: 'main article.news-item:nth-of-type(3) > p:nth-of-type(1)',
    excerpt: 'Public Viewing',
    act: 'off6ek',
    context: {
      element: '<p>Am Freitag zeigt die Gemeinde den Cupfinal als Public Viewing auf dem Dorfplatz.</p>',
      sentence: 'Am Freitag zeigt die Gemeinde den Cupfinal als Public Viewing auf dem Dorfplatz.',
      lang_declared: 'de',
    },
    diff: diff(
      'de/aktuelles.html',
      34,
      ['<p>Am Freitag zeigt die Gemeinde den Cupfinal als Public Viewing auf dem Dorfplatz.</p>'],
      ['<p>Am Freitag zeigt die Gemeinde den Cupfinal als <span lang="en">Public Viewing</span> auf dem Dorfplatz.</p>'],
    ),
    impact: {
      en: 'May be read with German pronunciation; acceptable if the term counts as a German loanword.',
      de: 'Wird eventuell deutsch ausgesprochen; das ist in Ordnung, wenn der Begriff als deutsches Lehnwort gilt.',
      fr: 'Pourrait être prononcé à l’allemande ; c’est acceptable si le terme est considéré comme un emprunt en allemand.',
      it: 'Potrebbe essere pronunciato alla tedesca; va bene se il termine è considerato un prestito in tedesco.',
    },
    explanation: {
      en: '“Public Viewing” is English, but it is widely used in Swiss German. WCAG does not require lang for words that have become part of the surrounding language. Apertus cannot decide this reliably, so a person should.',
      de: '«Public Viewing» ist Englisch, wird aber im Schweizer Deutsch verbreitet verwendet. WCAG verlangt kein lang-Attribut für Wörter, die Teil der umgebenden Sprache geworden sind. Apertus kann das nicht zuverlässig entscheiden – ein Mensch sollte es tun.',
      fr: '« Public Viewing » est de l’anglais, mais l’expression est courante en suisse allemand. Les WCAG n’exigent pas d’attribut lang pour les mots intégrés à la langue environnante. Apertus ne peut pas trancher de façon fiable : une personne doit décider.',
      it: '«Public Viewing» è inglese, ma è molto usato nel tedesco svizzero. Le WCAG non richiedono l’attributo lang per le parole entrate nella lingua circostante. Apertus non può deciderlo in modo affidabile: deve farlo una persona.',
    },
    hint: {
      en: 'If your editors consider the term English, mark the two words as English. Otherwise, reject this finding.',
      de: 'Wenn Ihre Redaktion den Begriff als Englisch betrachtet, zeichnen Sie die zwei Wörter als Englisch aus. Andernfalls verwerfen Sie diesen Befund.',
      fr: 'Si votre rédaction considère le terme comme anglais, marquez les deux mots comme anglais. Sinon, rejetez ce constat.',
      it: 'Se la redazione considera il termine inglese, contrassegnare le due parole come inglesi. Altrimenti respingere questo risultato.',
    },
  },
  {
    key: 'de-on-fr',
    criterion: '3.1.2',
    outcome: 'failed',
    source: 'apertus',
    confidence: 'high',
    page: PAGES.frHome,
    selector: 'main > section.infos > p:nth-of-type(2)',
    excerpt: DE_P,
    act: 'off6ek',
    context: { element: `<p>${DE_P}</p>`, lang_declared: 'fr' },
    diff: diff('fr/index.html', 48, [`<p>${DE_P}</p>`], [`<p lang="de">${DE_P}</p>`]),
    impact: {
      en: 'This German sentence will be read with French pronunciation.',
      de: 'Dieser deutsche Satz wird mit französischer Aussprache vorgelesen.',
      fr: 'Cette phrase allemande sera lue avec une prononciation française.',
      it: 'Questa frase tedesca verrà letta con la pronuncia francese.',
    },
    explanation: {
      en: 'The page is declared as French (lang="fr"). This sentence is German and has no lang="de", so a French voice reads it.',
      de: 'Die Seite ist als Französisch ausgezeichnet (lang="fr"). Dieser Satz ist deutsch und hat kein lang="de", deshalb liest ihn eine französische Stimme vor.',
      fr: 'La page est déclarée en français (lang="fr"). Cette phrase est en allemand et n’a pas de lang="de" : une voix française la lit.',
      it: 'La pagina è dichiarata in francese (lang="fr"). Questa frase è in tedesco e non ha lang="de": la legge una voce francese.',
    },
    hint: {
      en: 'Mark the sentence as German in the editor. Better still: translate it.',
      de: 'Zeichnen Sie den Satz im Editor als Deutsch aus. Noch besser: Übersetzen Sie ihn.',
      fr: 'Marquez la phrase comme allemande dans l’éditeur. Mieux encore : traduisez-la.',
      it: 'Contrassegnare la frase come tedesca nell’editor. Meglio ancora: tradurla.',
    },
  },
  ...mehrSpecs,
  {
    key: 'mehr-in-context',
    criterion: '2.4.4',
    outcome: 'passed',
    source: 'apertus',
    confidence: 'medium',
    page: PAGES.deNews,
    selector: 'main article.news-item:nth-of-type(1) > p:nth-of-type(2) > a',
    excerpt: 'Mehr',
    act: '5effbb',
    context: {
      element: '<a href="gv-2026.html">Mehr</a>',
      link_text: 'Mehr',
      paragraph: 'Die Gemeindeversammlung findet am 24. November in der Mehrzweckhalle statt. Mehr',
    },
    diff: null,
    impact: {
      en: 'In context, the link clearly leads to the municipal assembly.',
      de: 'Im Kontext ist klar, dass der Link zur Gemeindeversammlung führt.',
      fr: 'Dans son contexte, le lien mène clairement à l’assemblée communale.',
      it: 'Nel contesto è chiaro che il link porta all’assemblea comunale.',
    },
    explanation: {
      en: 'The link sits in the same paragraph as “Die Gemeindeversammlung findet am 24. November … statt”, which is programmatic context. The purpose is clear in context. “Mehr zur Gemeindeversammlung” would still help people who navigate by links.',
      de: 'Der Link steht im selben Absatz wie «Die Gemeindeversammlung findet am 24. November … statt» – das ist programmatischer Kontext. Der Zweck ist im Kontext klar. «Mehr zur Gemeindeversammlung» würde dennoch Menschen helfen, die über Linklisten navigieren.',
      fr: 'Le lien se trouve dans le même paragraphe que « Die Gemeindeversammlung findet am 24. November … statt », qui constitue un contexte programmatique. Sa fonction est claire dans le contexte. « Mehr zur Gemeindeversammlung » aiderait tout de même les personnes qui naviguent par liens.',
      it: 'Il link si trova nello stesso paragrafo di «Die Gemeindeversammlung findet am 24. November … statt», che è contesto programmatico. Lo scopo è chiaro nel contesto. «Mehr zur Gemeindeversammlung» aiuterebbe comunque chi naviga tramite elenchi di link.',
    },
    hint: null,
  },
  {
    key: 'hier',
    criterion: '2.4.4',
    outcome: 'cantTell',
    source: 'apertus',
    confidence: 'medium',
    page: PAGES.deContact,
    selector: 'main section.formulare > p:nth-of-type(1) > a',
    excerpt: 'hier',
    act: '5effbb',
    context: { element: '<a href="formulare/">hier</a>', link_text: 'hier', sentence: 'Das Formular finden Sie hier.' },
    diff: diff(
      'de/kontakt.html',
      18,
      ['<p>Das Formular finden Sie <a href="formulare/">hier</a>.</p>'],
      ['<p>Das Formular finden Sie hier: <a href="formulare/hund.pdf">Formular Hundeanmeldung (PDF)</a>.</p>'],
    ),
    impact: {
      en: 'People who list links hear “hier” (here) and can’t tell which form it opens.',
      de: 'Wer sich Links auflisten lässt, hört «hier» und weiss nicht, welches Formular sich öffnet.',
      fr: 'Les personnes qui listent les liens entendent « hier » (ici) sans savoir quel formulaire s’ouvre.',
      it: 'Chi elenca i link sente «hier» (qui) senza sapere quale modulo si apre.',
    },
    explanation: {
      en: 'In its sentence the link means “the form”, but the page offers three forms (dog registration, change of address, parking permit). Whether the sentence is precise enough depends on the section around it, which is not programmatic context. A person should decide.',
      de: 'Im Satz bedeutet der Link «das Formular», die Seite bietet aber drei Formulare an (Hundeanmeldung, Adressänderung, Parkkarte). Ob der Satz genau genug ist, hängt vom umgebenden Abschnitt ab – und der ist kein programmatischer Kontext. Ein Mensch sollte entscheiden.',
      fr: 'Dans sa phrase, le lien signifie « le formulaire », mais la page en propose trois (inscription d’un chien, changement d’adresse, carte de stationnement). La précision de la phrase dépend de la section qui l’entoure, qui n’est pas un contexte programmatique. Une personne doit décider.',
      it: 'Nella frase il link significa «il modulo», ma la pagina ne offre tre (registrazione del cane, cambio d’indirizzo, permesso di parcheggio). Se la frase sia abbastanza precisa dipende dalla sezione circostante, che non è contesto programmatico. Deve decidere una persona.',
    },
    hint: {
      en: 'Name the form in the link, e.g. “Formular Hundeanmeldung (PDF)”.',
      de: 'Nennen Sie das Formular im Link, z. B. «Formular Hundeanmeldung (PDF)».',
      fr: 'Nommez le formulaire dans le lien, p. ex. « Formular Hundeanmeldung (PDF) ».',
      it: 'Indicare il modulo nel link, p. es. «Formular Hundeanmeldung (PDF)».',
    },
  },
  {
    key: 'leggi',
    criterion: '2.4.4',
    outcome: 'failed',
    source: 'apertus',
    confidence: 'high',
    page: PAGES.itHome,
    selector: 'main > section.attualita > div.teaser:nth-of-type(1) > p.altro > a',
    excerpt: 'Leggi di più',
    act: '5effbb',
    context: { element: '<a href="attualita.html#via-principale">Leggi di più</a>', link_text: 'Leggi di più', paragraph: 'Leggi di più' },
    diff: diff(
      'it/index.html',
      58,
      ['<p class="altro"><a href="attualita.html#via-principale">Leggi di più</a></p>'],
      ['<p class="altro"><a href="attualita.html#via-principale">Leggi di più sul risanamento di via Principale</a></p>'],
    ),
    impact: {
      en: 'Screen-reader users hear “Leggi di più” (read more) without knowing what it refers to.',
      de: 'Screenreader-Nutzende hören «Leggi di più» (weiterlesen), ohne zu wissen, worauf es sich bezieht.',
      fr: 'Les utilisateurs de lecteurs d’écran entendent « Leggi di più » (lire la suite) sans savoir à quoi cela renvoie.',
      it: 'Chi usa uno screen reader sente «Leggi di più» senza sapere a cosa si riferisce.',
    },
    explanation: {
      en: 'Same pattern as the German “Mehr” links: the link is alone in its paragraph and the heading above it is not programmatic context. Klar. checks each language version separately.',
      de: 'Dasselbe Muster wie bei den deutschen «Mehr»-Links: Der Link steht allein in seinem Absatz, und die Überschrift darüber ist kein programmatischer Kontext. Klar. prüft jede Sprachversion einzeln.',
      fr: 'Même schéma que les liens allemands « Mehr » : le lien est seul dans son paragraphe et le titre au-dessus n’est pas un contexte programmatique. Klar. vérifie chaque version linguistique séparément.',
      it: 'Stesso schema dei link tedeschi «Mehr»: il link è da solo nel suo paragrafo e il titolo sopra non è contesto programmatico. Klar. verifica ogni versione linguistica separatamente.',
    },
    hint: {
      en: 'Change the link text to “Leggi di più sul risanamento di via Principale”.',
      de: 'Ändern Sie den Linktext in «Leggi di più sul risanamento di via Principale».',
      fr: 'Remplacez le texte du lien par « Leggi di più sul risanamento di via Principale ».',
      it: 'Sostituire il testo del link con «Leggi di più sul risanamento di via Principale».',
    },
  },
  {
    key: 'details-guard',
    criterion: '2.4.4',
    outcome: 'cantTell',
    source: 'apertus',
    confidence: 'low',
    page: PAGES.deWaste,
    selector: 'main section#sammelstellen > ul > li:nth-child(3) > a',
    excerpt: 'Details',
    act: '5effbb',
    context: {
      element: '<a href="sammelstellen.html#hinterdorf">Details</a>',
      link_text: 'Details',
      list_item: 'Sammelstelle Hinterdorf: Glas, Alu, Blech · Details',
    },
    diff: diff(
      'de/abfall.html',
      73,
      ['<a href="sammelstellen.html#hinterdorf">Details</a>'],
      ['<a href="sammelstellen.html#hinterdorf">Details zur Sammelstelle Hinterdorf</a>'],
    ),
    impact: {
      en: 'Not decided: the model’s answer was not grounded in the page.',
      de: 'Nicht entschieden: Die Antwort des Modells war nicht durch die Seite belegt.',
      fr: 'Non tranché : la réponse du modèle ne s’appuyait pas sur la page.',
      it: 'Non deciso: la risposta del modello non era fondata sulla pagina.',
    },
    explanation: {
      en: 'Apertus quoted “Öffnungszeiten der Sammelstelle” as evidence, but that text is not in the candidate, so the evidence guard discarded the answer (model answer not grounded). In its list item, “Details” probably refers to the Hinterdorf collection point, but a person should confirm.',
      de: 'Apertus zitierte «Öffnungszeiten der Sammelstelle» als Beleg, doch dieser Text steht nicht im Kandidaten. Die Belegprüfung hat die Antwort deshalb verworfen (Modellantwort nicht belegt). Im Listenpunkt bezieht sich «Details» wahrscheinlich auf die Sammelstelle Hinterdorf, ein Mensch sollte das aber bestätigen.',
      fr: 'Apertus a cité « Öffnungszeiten der Sammelstelle » comme preuve, mais ce texte ne figure pas dans le candidat : le contrôle des preuves a écarté la réponse (réponse du modèle non fondée). Dans son élément de liste, « Details » renvoie probablement au point de collecte Hinterdorf, mais une personne doit le confirmer.',
      it: 'Apertus ha citato «Öffnungszeiten der Sammelstelle» come prova, ma quel testo non è nel candidato: la verifica delle prove ha scartato la risposta (risposta del modello non fondata). Nella sua voce di elenco «Details» si riferisce probabilmente al punto di raccolta Hinterdorf, ma una persona deve confermarlo.',
    },
    hint: {
      en: 'If in doubt, make the link text explicit: “Details zur Sammelstelle Hinterdorf”.',
      de: 'Im Zweifel den Linktext eindeutig machen: «Details zur Sammelstelle Hinterdorf».',
      fr: 'En cas de doute, rendez le texte du lien explicite : « Details zur Sammelstelle Hinterdorf ».',
      it: 'Nel dubbio, rendere esplicito il testo del link: «Details zur Sammelstelle Hinterdorf».',
    },
  },
  {
    key: 'alt-bild',
    criterion: '1.1.1',
    outcome: 'failed',
    source: 'apertus',
    confidence: 'high',
    page: PAGES.deFinance,
    selector: 'main figure.diagramm > img',
    excerpt: 'alt="Bild"',
    act: 'qt1vmo',
    screenshot: CHART,
    context: {
      element: '<img src="img/steuerertrag-2021-2025.png" alt="Bild" width="640" height="360">',
      alt: 'Bild',
      image: '[screenshot crop 640 × 360 px]',
      surrounding_text: 'Die Steuererträge der natürlichen Personen haben sich in den letzten fünf Jahren erfreulich entwickelt.',
    },
    diff: diff(
      'de/finanzen.html',
      31,
      ['<img src="img/steuerertrag-2021-2025.png" alt="Bild" width="640" height="360">'],
      ['<img src="img/steuerertrag-2021-2025.png" alt="Steuerertrag natürliche Personen 2021–2025: von 4,1 auf 5,3 Mio. Franken gestiegen. Zahlen in der Tabelle unten." width="640" height="360">'],
    ),
    impact: {
      en: 'Blind users hear “Bild” (image) instead of the tax revenue trend shown in the chart.',
      de: 'Blinde Menschen hören «Bild» statt der Entwicklung der Steuererträge, die das Diagramm zeigt.',
      fr: 'Les personnes aveugles entendent « Bild » (image) au lieu de l’évolution des recettes fiscales montrée par le graphique.',
      it: 'Le persone cieche sentono «Bild» (immagine) invece dell’andamento del gettito fiscale mostrato dal grafico.',
    },
    explanation: {
      en: 'The image is a bar chart of tax revenue from natural persons, 2021 to 2025, rising from CHF 4.1 m to CHF 5.3 m. The alt text “Bild” gives no information, and the surrounding text says the trend is positive but gives no figures.',
      de: 'Das Bild ist ein Balkendiagramm der Steuererträge natürlicher Personen von 2021 bis 2025, die von 4,1 auf 5,3 Mio. Franken steigen. Der Alternativtext «Bild» enthält keine Information, und der Text daneben nennt zwar eine positive Entwicklung, aber keine Zahlen.',
      fr: 'L’image est un graphique en barres des recettes fiscales des personnes physiques de 2021 à 2025, qui passent de 4,1 à 5,3 millions de francs. Le texte alternatif « Bild » n’apporte aucune information, et le texte voisin évoque une évolution positive sans donner de chiffres.',
      it: 'L’immagine è un grafico a barre del gettito fiscale delle persone fisiche dal 2021 al 2025, che sale da 4,1 a 5,3 milioni di franchi. Il testo alternativo «Bild» non dà alcuna informazione e il testo accanto parla di un andamento positivo senza indicare cifre.',
    },
    hint: {
      en: 'Replace the image description “Bild” with the chart’s key message, and publish the figures as a table below the chart.',
      de: 'Ersetzen Sie die Bildbeschreibung «Bild» durch die Kernaussage des Diagramms und veröffentlichen Sie die Zahlen als Tabelle darunter.',
      fr: 'Remplacez la description « Bild » par le message clé du graphique et publiez les chiffres sous forme de tableau en dessous.',
      it: 'Sostituire la descrizione «Bild» con il messaggio principale del grafico e pubblicare le cifre in una tabella sotto.',
    },
  },
  {
    key: 'logo-filename',
    criterion: '1.1.1',
    outcome: 'failed',
    source: 'heuristic',
    confidence: 'high',
    page: PAGES.deHome,
    selector: 'header > a.logo > img',
    excerpt: 'alt="logo_musterwil_final_v2.png"',
    screenshot: LOGO,
    context: {},
    diff: diff(
      'de/index.html',
      12,
      ['<a class="logo" href="./"><img src="img/logo_musterwil_final_v2.png" alt="logo_musterwil_final_v2.png"></a>'],
      ['<a class="logo" href="./"><img src="img/logo_musterwil_final_v2.png" alt="Gemeinde Musterwil – Startseite"></a>'],
    ),
    impact: {
      en: 'Screen readers announce a file name instead of “Gemeinde Musterwil”.',
      de: 'Screenreader sagen einen Dateinamen an statt «Gemeinde Musterwil».',
      fr: 'Les lecteurs d’écran annoncent un nom de fichier au lieu de « Gemeinde Musterwil ».',
      it: 'Gli screen reader annunciano un nome di file invece di «Gemeinde Musterwil».',
    },
    explanation: {
      en: 'The alt text is a file name (it ends in .png). A heuristic in code decided this without asking Apertus. The logo is the only content of the home link, so its alt text is the link’s name.',
      de: 'Der Alternativtext ist ein Dateiname (er endet auf .png). Eine Heuristik im Code hat das entschieden, ohne Apertus zu fragen. Das Logo ist der einzige Inhalt des Links zur Startseite; sein Alternativtext ist also der Name des Links.',
      fr: 'Le texte alternatif est un nom de fichier (il se termine par .png). Une heuristique dans le code l’a déterminé sans interroger Apertus. Le logo est le seul contenu du lien vers l’accueil : son texte alternatif est donc le nom du lien.',
      it: 'Il testo alternativo è un nome di file (termina con .png). Lo ha stabilito un’euristica nel codice, senza interrogare Apertus. Il logo è l’unico contenuto del link alla pagina iniziale: il suo testo alternativo è quindi il nome del link.',
    },
    hint: {
      en: 'In the site settings, set the logo’s alternative text to “Gemeinde Musterwil – Startseite”.',
      de: 'Setzen Sie in den Website-Einstellungen den Alternativtext des Logos auf «Gemeinde Musterwil – Startseite».',
      fr: 'Dans les réglages du site, définissez le texte alternatif du logo sur « Gemeinde Musterwil – Startseite ».',
      it: 'Nelle impostazioni del sito impostare il testo alternativo del logo su «Gemeinde Musterwil – Startseite».',
    },
  },
  {
    key: 'arrow-icon',
    criterion: '1.1.1',
    outcome: 'cantTell',
    source: 'apertus',
    confidence: 'medium',
    page: PAGES.deHome,
    selector: 'main a.cta-schalter > img',
    excerpt: 'alt="Pfeil nach rechts"',
    act: 'qt1vmo',
    screenshot: ARROW_LINK,
    context: {
      element: '<a class="cta-schalter" href="https://www.musterwil.ch/schalter">Zum Online-Schalter <img src="img/pfeil.svg" alt="Pfeil nach rechts"></a>',
      link_text: 'Zum Online-Schalter',
      alt: 'Pfeil nach rechts',
      image: '[screenshot crop 16 × 16 px]',
    },
    diff: diff('de/index.html', 88, ['<img src="img/pfeil.svg" alt="Pfeil nach rechts">'], ['<img src="img/pfeil.svg" alt="">']),
    impact: {
      en: 'Screen-reader users hear “Zum Online-Schalter Pfeil nach rechts”: the arrow adds noise.',
      de: 'Screenreader-Nutzende hören «Zum Online-Schalter Pfeil nach rechts» – der Pfeil ist überflüssig.',
      fr: 'Les utilisateurs de lecteurs d’écran entendent « Zum Online-Schalter Pfeil nach rechts » : la flèche ajoute du bruit.',
      it: 'Chi usa uno screen reader sente «Zum Online-Schalter Pfeil nach rechts»: la freccia aggiunge rumore.',
    },
    explanation: {
      en: 'The arrow looks decorative: the link text already says where it goes. Its alt text describes a visual detail, so an empty alt (alt="") is probably better. If the arrow is meant to signal an external site, that should be said in words.',
      de: 'Der Pfeil wirkt dekorativ: Der Linktext sagt bereits, wohin er führt. Sein Alternativtext beschreibt ein visuelles Detail; ein leeres alt (alt="") ist wahrscheinlich besser. Soll der Pfeil eine externe Website anzeigen, gehört das in Worte gefasst.',
      fr: 'La flèche semble décorative : le texte du lien indique déjà la destination. Son texte alternatif décrit un détail visuel ; un alt vide (alt="") est probablement préférable. Si la flèche signale un site externe, il faut le dire en toutes lettres.',
      it: 'La freccia sembra decorativa: il testo del link dice già dove porta. Il suo testo alternativo descrive un dettaglio visivo, quindi un alt vuoto (alt="") è probabilmente meglio. Se la freccia segnala un sito esterno, va detto a parole.',
    },
    hint: {
      en: 'Mark the arrow image as decorative in the image settings.',
      de: 'Markieren Sie das Pfeilbild in den Bildeinstellungen als dekorativ.',
      fr: 'Marquez l’image de la flèche comme décorative dans ses réglages.',
      it: 'Contrassegnare l’immagine della freccia come decorativa nelle impostazioni.',
    },
  },
  {
    key: 'town-hall',
    criterion: '1.1.1',
    outcome: 'passed',
    source: 'apertus',
    confidence: 'high',
    page: PAGES.deHome,
    selector: 'main > section#willkommen > figure > img',
    excerpt: 'alt="Das Gemeindehaus von Musterwil mit Uhrturm und Linde"',
    act: 'qt1vmo',
    screenshot: TOWN_HALL,
    context: {
      element: '<img src="img/gemeindehaus.jpg" alt="Das Gemeindehaus von Musterwil mit Uhrturm und Linde">',
      alt: 'Das Gemeindehaus von Musterwil mit Uhrturm und Linde',
      image: '[screenshot crop 480 × 300 px]',
    },
    diff: null,
    impact: {
      en: 'The description matches the photo.',
      de: 'Die Beschreibung passt zum Foto.',
      fr: 'La description correspond à la photo.',
      it: 'La descrizione corrisponde alla foto.',
    },
    explanation: {
      en: 'The photo shows a town hall with a clock tower and a large tree in front. The alt text describes exactly that, in German like the page.',
      de: 'Das Foto zeigt ein Gemeindehaus mit Uhrturm und einem grossen Baum davor. Der Alternativtext beschreibt genau das, auf Deutsch wie die Seite.',
      fr: 'La photo montre une maison communale avec une tour d’horloge et un grand arbre devant. Le texte alternatif décrit exactement cela, en allemand comme la page.',
      it: 'La foto mostra una casa comunale con una torre dell’orologio e un grande albero davanti. Il testo alternativo descrive esattamente questo, in tedesco come la pagina.',
    },
    hint: null,
  },
  {
    key: 'green-button',
    criterion: '1.3.3',
    outcome: 'failed',
    source: 'apertus',
    confidence: 'high',
    page: PAGES.deContact,
    selector: 'main form#kontakt > p.anleitung',
    excerpt: 'Klicken Sie auf den grünen Knopf rechts, um das Formular abzusenden.',
    screenshot: FORM_BUTTONS,
    context: {
      element: '<p class="anleitung">Klicken Sie auf den grünen Knopf rechts, um das Formular abzusenden.</p>',
      buttons_in_form: 'Zurücksetzen; Anfrage senden',
    },
    diff: diff(
      'de/kontakt.html',
      44,
      ['<p class="anleitung">Klicken Sie auf den grünen Knopf rechts, um das Formular abzusenden.</p>'],
      ['<p class="anleitung">Klicken Sie auf «Anfrage senden», um das Formular abzusenden.</p>'],
    ),
    impact: {
      en: 'People who can’t see colours or the layout can’t find “the green button on the right”.',
      de: 'Wer Farben oder das Layout nicht sieht, findet «den grünen Knopf rechts» nicht.',
      fr: 'Les personnes qui ne voient pas les couleurs ou la mise en page ne trouvent pas « le bouton vert à droite ».',
      it: 'Chi non vede i colori o il layout non trova «il pulsante verde a destra».',
    },
    explanation: {
      en: 'The instruction identifies the button only by its colour and position. Screen-reader users, people with colour vision deficiency and anyone using a zoomed or mobile layout (where the button moves below the form) can’t rely on that. The button’s visible label is “Anfrage senden”.',
      de: 'Die Anweisung bezeichnet den Button nur über Farbe und Position. Darauf können sich Screenreader-Nutzende, Menschen mit Farbsehschwäche und alle, die vergrössert oder mobil arbeiten (dort rutscht der Button unter das Formular), nicht verlassen. Die sichtbare Beschriftung des Buttons lautet «Anfrage senden».',
      fr: 'La consigne désigne le bouton uniquement par sa couleur et sa position. Les utilisateurs de lecteurs d’écran, les personnes daltoniennes et toute personne qui zoome ou utilise un mobile (où le bouton passe sous le formulaire) ne peuvent pas s’y fier. Le libellé visible du bouton est « Anfrage senden ».',
      it: 'L’istruzione identifica il pulsante solo con il colore e la posizione. Chi usa uno screen reader, chi ha un deficit della visione dei colori e chi ingrandisce la pagina o usa un dispositivo mobile (dove il pulsante finisce sotto il modulo) non può farvi affidamento. L’etichetta visibile del pulsante è «Anfrage senden».',
    },
    hint: {
      en: 'Rewrite the instruction to name the button by its label: “Klicken Sie auf «Anfrage senden», um das Formular abzusenden.”',
      de: 'Formulieren Sie die Anweisung mit der Beschriftung des Buttons: «Klicken Sie auf ‹Anfrage senden›, um das Formular abzusenden.»',
      fr: 'Reformulez la consigne avec le libellé du bouton : « Klicken Sie auf ‹ Anfrage senden ›, um das Formular abzusenden. »',
      it: 'Riformulare l’istruzione con l’etichetta del pulsante: «Klicken Sie auf ‹Anfrage senden›, um das Formular abzusenden.»',
    },
  },
  {
    key: 'map-red',
    criterion: '1.3.3',
    outcome: 'cantTell',
    source: 'apertus',
    confidence: 'medium',
    page: PAGES.deWaste,
    selector: 'main section#sammelstellen > p:nth-of-type(1)',
    excerpt: 'Die Sammelstellen sind auf der Karte unten rot markiert.',
    context: {
      element: '<p>Die Sammelstellen sind auf der Karte unten rot markiert.</p>',
      next_sibling: '<img src="img/karte-sammelstellen.png" alt="Karte">',
    },
    diff: diff(
      'de/abfall.html',
      66,
      ['<p>Die Sammelstellen sind auf der Karte unten rot markiert.</p>'],
      ['<p>Die Sammelstellen sind auf der Karte rot markiert und darunter als Liste aufgeführt.</p>'],
    ),
    impact: {
      en: 'People who can’t see the map or the colour red may miss where the collection points are.',
      de: 'Wer die Karte oder die Farbe Rot nicht sieht, erfährt womöglich nicht, wo die Sammelstellen sind.',
      fr: 'Les personnes qui ne voient pas la carte ou le rouge risquent de ne pas savoir où se trouvent les points de collecte.',
      it: 'Chi non vede la mappa o il colore rosso rischia di non sapere dove si trovano i punti di raccolta.',
    },
    explanation: {
      en: 'The sentence relies on position (“unten”, below) and colour (“rot”, red). That is fine if the collection points are also listed as text, but no such list is in the context Klar. was allowed to show. A person should check the page.',
      de: 'Der Satz stützt sich auf Position («unten») und Farbe («rot»). Das ist in Ordnung, wenn die Sammelstellen auch als Text aufgeführt sind – im Kontext, den Klar. zeigen durfte, ist aber keine solche Liste. Ein Mensch sollte die Seite prüfen.',
      fr: 'La phrase repose sur la position (« unten », en bas) et la couleur (« rot », rouge). C’est acceptable si les points de collecte sont aussi listés en texte, mais aucune liste de ce type ne figure dans le contexte que Klar. pouvait montrer. Une personne doit vérifier la page.',
      it: 'La frase si basa sulla posizione («unten», sotto) e sul colore («rot», rosso). Va bene se i punti di raccolta sono elencati anche come testo, ma nel contesto che Klar. poteva mostrare non c’è alcun elenco del genere. Una persona deve verificare la pagina.',
    },
    hint: {
      en: 'List the collection points as text below the map and mention the list in the sentence.',
      de: 'Führen Sie die Sammelstellen unter der Karte als Text auf und verweisen Sie im Satz auf die Liste.',
      fr: 'Listez les points de collecte en texte sous la carte et mentionnez la liste dans la phrase.',
      it: 'Elencare i punti di raccolta come testo sotto la mappa e citare l’elenco nella frase.',
    },
  },
  {
    key: 'fehler',
    criterion: '3.3.1',
    outcome: 'failed',
    source: 'apertus',
    confidence: 'high',
    page: PAGES.deContact,
    selector: 'main form#kontakt > p.error',
    excerpt: 'Fehler',
    screenshot: FORM_ERROR,
    context: {
      probe: 'Form submitted with e-mail "anna.muster.musterwil.ch" (no @)',
      message: 'Fehler',
      fields: 'Name; E-Mail; Feld 3',
      email_field: '<input type="email" id="email" name="email">',
    },
    diff: diff(
      'de/kontakt.html',
      51,
      ['<p class="error">Fehler</p>', '<input type="email" id="email" name="email">'],
      [
        '<p class="error" id="email-fehler">Die E-Mail-Adresse ist ungültig: Es fehlt das Zeichen «@».</p>',
        '<input type="email" id="email" name="email" aria-invalid="true" aria-describedby="email-fehler">',
      ],
    ),
    impact: {
      en: 'After submitting, users only read “Fehler” (error) and don’t know which field is wrong or why.',
      de: 'Nach dem Absenden lesen die Nutzenden nur «Fehler» und wissen nicht, welches Feld falsch ist und warum.',
      fr: 'Après l’envoi, les personnes lisent seulement « Fehler » (erreur) sans savoir quel champ pose problème ni pourquoi.',
      it: 'Dopo l’invio si legge solo «Fehler» (errore), senza sapere quale campo è sbagliato né perché.',
    },
    explanation: {
      en: 'Klar. submitted the form with an e-mail address without “@”. The only feedback is “Fehler” above the form: it doesn’t name the field or describe the problem, and the field gets neither aria-invalid nor aria-describedby.',
      de: 'Klar. hat das Formular mit einer E-Mail-Adresse ohne «@» abgesendet. Die einzige Rückmeldung ist «Fehler» über dem Formular: Sie nennt weder das Feld noch das Problem, und das Feld erhält weder aria-invalid noch aria-describedby.',
      fr: 'Klar. a envoyé le formulaire avec une adresse e-mail sans « @ ». Le seul retour est « Fehler » au-dessus du formulaire : il ne nomme ni le champ ni le problème, et le champ ne reçoit ni aria-invalid ni aria-describedby.',
      it: 'Klar. ha inviato il modulo con un indirizzo e-mail senza «@». L’unico riscontro è «Fehler» sopra il modulo: non indica né il campo né il problema, e il campo non riceve né aria-invalid né aria-describedby.',
    },
    hint: {
      en: 'In the form settings, replace the generic error text with one message per field, e.g. “Die E-Mail-Adresse ist ungültig: Es fehlt das Zeichen @.”',
      de: 'Ersetzen Sie in den Formulareinstellungen den allgemeinen Fehlertext durch eine Meldung pro Feld, z. B. «Die E-Mail-Adresse ist ungültig: Es fehlt das Zeichen @.»',
      fr: 'Dans les réglages du formulaire, remplacez le message générique par un message par champ, p. ex. « Die E-Mail-Adresse ist ungültig: Es fehlt das Zeichen @. »',
      it: 'Nelle impostazioni del modulo sostituire il messaggio generico con un messaggio per campo, p. es. «Die E-Mail-Adresse ist ungültig: Es fehlt das Zeichen @.»',
    },
  },
  {
    key: 'datum',
    criterion: '3.3.3',
    outcome: 'failed',
    source: 'apertus',
    confidence: 'high',
    page: PAGES.deContact,
    selector: 'main form#termin > span#datum-fehler',
    excerpt: 'Ungültiges Datum',
    context: { field_label: 'Gewünschter Termin', entered_value: '14/10/2026', message: 'Ungültiges Datum' },
    diff: diff(
      'de/kontakt.html',
      97,
      ['<span id="datum-fehler">Ungültiges Datum</span>'],
      ['<span id="datum-fehler">Bitte geben Sie das Datum im Format TT.MM.JJJJ ein, z. B. 14.10.2026.</span>'],
    ),
    impact: {
      en: 'Users learn that the date is wrong, but not which format is expected.',
      de: 'Man erfährt, dass das Datum falsch ist, aber nicht, welches Format erwartet wird.',
      fr: 'On apprend que la date est fausse, mais pas quel format est attendu.',
      it: 'Si scopre che la data è sbagliata, ma non quale formato è previsto.',
    },
    explanation: {
      en: 'The field rejected “14/10/2026”. The message identifies the error but suggests no correction, although the system knows the expected format (TT.MM.JJJJ). People with cognitive disabilities in particular may give up here.',
      de: 'Das Feld hat «14/10/2026» abgelehnt. Die Meldung benennt den Fehler, schlägt aber keine Korrektur vor, obwohl das System das erwartete Format (TT.MM.JJJJ) kennt. Gerade Menschen mit kognitiven Beeinträchtigungen geben hier womöglich auf.',
      fr: 'Le champ a refusé « 14/10/2026 ». Le message signale l’erreur sans proposer de correction, alors que le système connaît le format attendu (TT.MM.JJJJ). Les personnes avec des troubles cognitifs, en particulier, risquent d’abandonner ici.',
      it: 'Il campo ha rifiutato «14/10/2026». Il messaggio segnala l’errore ma non propone una correzione, anche se il sistema conosce il formato previsto (TT.MM.JJJJ). Soprattutto le persone con disabilità cognitive rischiano di rinunciare.',
    },
    hint: {
      en: 'Change the message to “Bitte geben Sie das Datum im Format TT.MM.JJJJ ein, z. B. 14.10.2026.”',
      de: 'Ändern Sie die Meldung in «Bitte geben Sie das Datum im Format TT.MM.JJJJ ein, z. B. 14.10.2026.»',
      fr: 'Remplacez le message par « Bitte geben Sie das Datum im Format TT.MM.JJJJ ein, z. B. 14.10.2026. »',
      it: 'Sostituire il messaggio con «Bitte geben Sie das Datum im Format TT.MM.JJJJ ein, z. B. 14.10.2026.»',
    },
  },
  {
    key: 'no-form',
    criterion: '3.3.1',
    outcome: 'inapplicable',
    source: 'rule',
    confidence: 'high',
    page: PAGES.itHome,
    selector: 'html',
    excerpt: '',
    context: {},
    diff: null,
    impact: {
      en: 'No form on this page: nothing to check.',
      de: 'Kein Formular auf dieser Seite: nichts zu prüfen.',
      fr: 'Aucun formulaire sur cette page : rien à vérifier.',
      it: 'Nessun modulo in questa pagina: niente da verificare.',
    },
    explanation: {
      en: 'The page has no form controls, so error identification does not apply.',
      de: 'Die Seite enthält keine Formularelemente; die Fehlererkennung ist daher nicht anwendbar.',
      fr: 'La page ne contient aucun champ de formulaire : l’identification des erreurs ne s’applique pas.',
      it: 'La pagina non contiene campi di modulo: l’identificazione degli errori non si applica.',
    },
    hint: null,
  },
  {
    key: 'feld-3',
    criterion: '2.4.6',
    outcome: 'failed',
    source: 'apertus',
    confidence: 'high',
    page: PAGES.deContact,
    selector: 'main form#kontakt label[for="f3"]',
    excerpt: 'Feld 3',
    act: 'cc0f0a',
    context: {
      element: '<label for="f3">Feld 3</label>',
      control: '<textarea id="f3" name="nachricht" rows="6"></textarea>',
      other_labels: 'Name; E-Mail',
    },
    diff: diff('de/kontakt.html', 63, ['<label for="f3">Feld 3</label>'], ['<label for="f3">Ihre Nachricht</label>']),
    impact: {
      en: 'Screen-reader users hear “Feld 3” (field 3) and have to guess what to type.',
      de: 'Screenreader-Nutzende hören «Feld 3» und müssen raten, was sie eingeben sollen.',
      fr: 'Les utilisateurs de lecteurs d’écran entendent « Feld 3 » (champ 3) et doivent deviner quoi saisir.',
      it: 'Chi usa uno screen reader sente «Feld 3» (campo 3) e deve indovinare cosa scrivere.',
    },
    explanation: {
      en: 'The label is a default name from the form builder. The field is a large text area named “nachricht” (message), so the label should say so.',
      de: 'Die Beschriftung ist ein Standardname aus dem Formular-Baukasten. Das Feld ist ein grosses Textfeld mit dem Namen «nachricht»; die Beschriftung sollte das sagen.',
      fr: 'Le libellé est un nom par défaut du générateur de formulaires. Le champ est une grande zone de texte nommée « nachricht » (message) : le libellé devrait le dire.',
      it: 'L’etichetta è un nome predefinito del generatore di moduli. Il campo è un’ampia area di testo chiamata «nachricht» (messaggio): l’etichetta dovrebbe dirlo.',
    },
    hint: {
      en: 'In the form builder, rename the label “Feld 3” to “Ihre Nachricht”.',
      de: 'Benennen Sie im Formular-Baukasten die Beschriftung «Feld 3» in «Ihre Nachricht» um.',
      fr: 'Dans le générateur de formulaires, renommez le libellé « Feld 3 » en « Ihre Nachricht ».',
      it: 'Nel generatore di moduli rinominare l’etichetta «Feld 3» in «Ihre Nachricht».',
    },
  },
  {
    key: 'diverses',
    criterion: '2.4.6',
    outcome: 'cantTell',
    source: 'apertus',
    confidence: 'medium',
    page: PAGES.deHome,
    selector: 'main > section:nth-of-type(4) > h2',
    excerpt: 'Diverses',
    act: 'b49b2e',
    context: {
      element: '<h2>Diverses</h2>',
      section_text: 'Baugesuche können neu elektronisch eingereicht werden. Die Publikation erfolgt im Amtsblatt des Kantons.',
    },
    diff: diff('de/index.html', 102, ['<h2>Diverses</h2>'], ['<h2>Baugesuche</h2>']),
    impact: {
      en: 'People who jump between headings can’t tell that this section is about building applications.',
      de: 'Wer von Überschrift zu Überschrift springt, erkennt nicht, dass es in diesem Abschnitt um Baugesuche geht.',
      fr: 'Les personnes qui naviguent de titre en titre ne devinent pas que cette section porte sur les demandes de permis de construire.',
      it: 'Chi salta da un titolo all’altro non capisce che questa sezione riguarda le domande di costruzione.',
    },
    explanation: {
      en: '“Diverses” (miscellaneous) doesn’t describe the section, which is only about building applications; “Baugesuche” would. If the section is meant to collect varied news later, the heading may be acceptable, so a person should decide.',
      de: '«Diverses» beschreibt den Abschnitt nicht, der nur von Baugesuchen handelt; «Baugesuche» würde es tun. Soll der Abschnitt später verschiedene Meldungen sammeln, kann die Überschrift vertretbar sein – deshalb sollte ein Mensch entscheiden.',
      fr: '« Diverses » (divers) ne décrit pas la section, qui ne traite que des demandes de permis de construire ; « Baugesuche » le ferait. Si la section doit accueillir plus tard des nouvelles variées, le titre peut se défendre : une personne doit décider.',
      it: '«Diverses» (varie) non descrive la sezione, che tratta solo di domande di costruzione; «Baugesuche» lo farebbe. Se la sezione dovrà raccogliere in futuro notizie diverse, il titolo può andare bene: deve decidere una persona.',
    },
    hint: {
      en: 'Rename the heading to “Baugesuche”.',
      de: 'Benennen Sie die Überschrift in «Baugesuche» um.',
      fr: 'Renommez le titre en « Baugesuche ».',
      it: 'Rinominare il titolo in «Baugesuche».',
    },
  },
  {
    key: 'abfallkalender',
    criterion: '2.4.6',
    outcome: 'passed',
    source: 'apertus',
    confidence: 'high',
    page: PAGES.deWaste,
    selector: 'main > h1',
    excerpt: 'Abfallkalender 2026',
    act: 'b49b2e',
    context: {
      element: '<h1>Abfallkalender 2026</h1>',
      section_text: 'Kehricht, Papier, Karton und Grüngut: alle Sammeldaten 2026 auf einen Blick.',
    },
    diff: null,
    impact: {
      en: 'The heading describes the page content.',
      de: 'Die Überschrift beschreibt den Inhalt der Seite.',
      fr: 'Le titre décrit le contenu de la page.',
      it: 'Il titolo descrive il contenuto della pagina.',
    },
    explanation: {
      en: 'The heading names the topic and the year, and the content below is the 2026 collection schedule.',
      de: 'Die Überschrift nennt Thema und Jahr, und der Inhalt darunter ist der Sammelplan 2026.',
      fr: 'Le titre indique le sujet et l’année, et le contenu qui suit est le calendrier de collecte 2026.',
      it: 'Il titolo indica il tema e l’anno, e il contenuto sotto è il calendario di raccolta 2026.',
    },
    hint: null,
  },
  {
    key: 'banner-text',
    criterion: '1.4.5',
    outcome: 'failed',
    source: 'apertus',
    confidence: 'high',
    page: PAGES.deHome,
    selector: 'main > section#willkommen > img.banner',
    excerpt: 'alt="Öffnungszeiten"',
    act: '0va7u6',
    screenshot: BANNER,
    context: {
      element: '<img class="banner" src="img/oeffnungszeiten.png" alt="Öffnungszeiten" width="640" height="160">',
      alt: 'Öffnungszeiten',
      image: '[screenshot crop 640 × 160 px]',
    },
    diff: diff(
      'de/index.html',
      36,
      ['<img class="banner" src="img/oeffnungszeiten.png" alt="Öffnungszeiten" width="640" height="160">'],
      ['<h2>Öffnungszeiten</h2>', '<p>Montag bis Freitag 08.00–11.30 Uhr, Donnerstag zusätzlich 14.00–18.30 Uhr</p>'],
    ),
    impact: {
      en: 'When users enlarge text or change colours, the opening hours stay small and blurry, and the times aren’t in the alt text either.',
      de: 'Wer Text vergrössert oder Farben anpasst, sieht die Öffnungszeiten weiterhin klein und unscharf – und im Alternativtext fehlen die Zeiten ganz.',
      fr: 'Quand on agrandit le texte ou change les couleurs, les horaires restent petits et flous, et ils ne figurent pas non plus dans le texte alternatif.',
      it: 'Chi ingrandisce il testo o cambia i colori vede gli orari sempre piccoli e sfocati, e gli orari mancano anche nel testo alternativo.',
    },
    explanation: {
      en: 'The banner shows the opening hours (Mon–Fri 08.00–11.30, Thu 14.00–18.30) as text inside an image. Images of text can’t be resized, recoloured or translated reliably. The alt text “Öffnungszeiten” also omits the actual times (1.1.1).',
      de: 'Das Banner zeigt die Öffnungszeiten (Mo–Fr 08.00–11.30, Do 14.00–18.30) als Text in einem Bild. Bilder von Text lassen sich nicht zuverlässig vergrössern, umfärben oder übersetzen. Zudem fehlen im Alternativtext «Öffnungszeiten» die eigentlichen Zeiten (1.1.1).',
      fr: 'La bannière affiche les horaires (lu–ve 08.00–11.30, je 14.00–18.30) sous forme de texte dans une image. Un texte en image ne peut pas être agrandi, recoloré ou traduit de façon fiable. De plus, le texte alternatif « Öffnungszeiten » omet les horaires eux-mêmes (1.1.1).',
      it: 'Il banner mostra gli orari (lu–ve 08.00–11.30, gio 14.00–18.30) come testo dentro un’immagine. Le immagini di testo non si possono ingrandire, ricolorare o tradurre in modo affidabile. Inoltre il testo alternativo «Öffnungszeiten» omette gli orari veri e propri (1.1.1).',
    },
    hint: {
      en: 'Delete the banner image and type the opening hours as normal text in a text block.',
      de: 'Löschen Sie das Bannerbild und erfassen Sie die Öffnungszeiten als normalen Text in einem Textblock.',
      fr: 'Supprimez l’image de la bannière et saisissez les horaires comme texte normal dans un bloc de texte.',
      it: 'Eliminare l’immagine del banner e inserire gli orari come testo normale in un blocco di testo.',
    },
  },
  {
    key: 'fake-heading',
    criterion: '1.3.1',
    outcome: 'failed',
    source: 'apertus',
    confidence: 'medium',
    page: PAGES.deWaste,
    selector: 'main > p:nth-of-type(4)',
    excerpt: '<b>Grünabfuhr</b>',
    context: {
      element: '<p><b>Grünabfuhr</b></p>',
      next_element: '<p>Jeden zweiten Mittwoch, März bis November.</p>',
      neighbour_headings: 'h2 «Kehricht»; h2 «Papier und Karton»',
    },
    diff: diff('de/abfall.html', 41, ['<p><b>Grünabfuhr</b></p>'], ['<h2>Grünabfuhr</h2>']),
    impact: {
      en: 'Screen-reader users who jump between headings skip the “Grünabfuhr” (green waste) section.',
      de: 'Screenreader-Nutzende, die von Überschrift zu Überschrift springen, überspringen den Abschnitt «Grünabfuhr».',
      fr: 'Les utilisateurs de lecteurs d’écran qui naviguent par titres sautent la section « Grünabfuhr » (déchets verts).',
      it: 'Chi usa uno screen reader e salta da un titolo all’altro perde la sezione «Grünabfuhr» (scarti vegetali).',
    },
    explanation: {
      en: 'This bold paragraph looks and works like a heading: it is short, introduces the green waste schedule and sits between two real h2 headings. It is not marked up as a heading, so its role is lost for assistive technology.',
      de: 'Dieser fette Absatz sieht aus wie eine Überschrift und funktioniert auch so: Er ist kurz, leitet den Sammelplan für Grüngut ein und steht zwischen zwei echten h2-Überschriften. Er ist aber nicht als Überschrift ausgezeichnet; Hilfsmittel erkennen seine Rolle nicht.',
      fr: 'Ce paragraphe en gras ressemble à un titre et en a la fonction : il est court, introduit le calendrier des déchets verts et se trouve entre deux vrais titres h2. Il n’est pas balisé comme titre, si bien que les aides techniques ignorent son rôle.',
      it: 'Questo paragrafo in grassetto sembra un titolo e ne ha la funzione: è breve, introduce il calendario degli scarti vegetali e si trova tra due veri titoli h2. Non è marcato come titolo, quindi le tecnologie assistive ne perdono il ruolo.',
    },
    hint: {
      en: 'Format the line as “Heading 2” instead of bold text.',
      de: 'Formatieren Sie die Zeile als «Überschrift 2» statt als fetten Text.',
      fr: 'Mettez la ligne en forme « Titre 2 » au lieu du gras.',
      it: 'Formattare la riga come «Titolo 2» invece che in grassetto.',
    },
  },
  {
    key: 'title-default',
    criterion: '2.4.2',
    outcome: 'failed',
    source: 'apertus',
    confidence: 'high',
    page: PAGES.deContact,
    selector: 'head > title',
    excerpt: 'Neue Seite 1',
    act: 'c4a8a4',
    context: { title: 'Neue Seite 1', h1: 'Kontakt', url_path: '/demo/de/kontakt.html' },
    diff: diff('de/kontakt.html', 6, ['<title>Neue Seite 1</title>'], ['<title>Kontakt – Gemeinde Musterwil</title>']),
    impact: {
      en: 'People with several tabs open, and screen-reader users, can’t tell what this page is.',
      de: 'Wer mehrere Tabs offen hat oder einen Screenreader nutzt, erkennt nicht, um welche Seite es geht.',
      fr: 'Les personnes qui ont plusieurs onglets ouverts, comme les utilisateurs de lecteurs d’écran, ne savent pas de quelle page il s’agit.',
      it: 'Chi ha più schede aperte, o usa uno screen reader, non capisce di che pagina si tratta.',
    },
    explanation: {
      en: 'The title “Neue Seite 1” (new page 1) is a CMS default. The page is the municipality’s contact form, as the h1 “Kontakt” shows. The title is the first thing a screen reader announces.',
      de: 'Der Titel «Neue Seite 1» ist ein Standardwert des CMS. Die Seite ist das Kontaktformular der Gemeinde, wie die h1 «Kontakt» zeigt. Der Titel ist das Erste, was ein Screenreader ansagt.',
      fr: 'Le titre « Neue Seite 1 » (nouvelle page 1) est une valeur par défaut du CMS. La page est le formulaire de contact de la commune, comme l’indique le h1 « Kontakt ». Le titre est la première chose qu’annonce un lecteur d’écran.',
      it: 'Il titolo «Neue Seite 1» (nuova pagina 1) è un valore predefinito del CMS. La pagina è il modulo di contatto del comune, come mostra l’h1 «Kontakt». Il titolo è la prima cosa che annuncia uno screen reader.',
    },
    hint: {
      en: 'In the page settings, set the title to “Kontakt – Gemeinde Musterwil”.',
      de: 'Setzen Sie in den Seiteneinstellungen den Titel auf «Kontakt – Gemeinde Musterwil».',
      fr: 'Dans les réglages de la page, définissez le titre « Kontakt – Gemeinde Musterwil ».',
      it: 'Nelle impostazioni della pagina impostare il titolo «Kontakt – Gemeinde Musterwil».',
    },
  },
  {
    key: 'title-it',
    criterion: '2.4.2',
    outcome: 'cantTell',
    source: 'apertus',
    confidence: 'medium',
    page: PAGES.itHome,
    selector: 'head > title',
    excerpt: 'Gemeinde Musterwil',
    act: 'c4a8a4',
    context: { title: 'Gemeinde Musterwil', h1: 'Benvenuti a Musterwil', lang_declared: 'it' },
    diff: diff('it/index.html', 6, ['<title>Gemeinde Musterwil</title>'], ['<title>Pagina iniziale – Comune di Musterwil</title>']),
    impact: {
      en: 'Italian-speaking users hear a German title on the Italian home page.',
      de: 'Italienischsprachige Nutzende hören auf der italienischen Startseite einen deutschen Titel.',
      fr: 'Les utilisateurs italophones entendent un titre allemand sur la page d’accueil italienne.',
      it: 'Chi parla italiano sente un titolo tedesco sulla pagina iniziale italiana.',
    },
    explanation: {
      en: 'The title names the municipality, but in German, while the page is Italian (lang="it") and its h1 reads “Benvenuti a Musterwil”. “Comune di Musterwil” would match. Whether an official name in another language is descriptive enough is a judgement call.',
      de: 'Der Titel nennt die Gemeinde, aber auf Deutsch, während die Seite italienisch ist (lang="it") und ihre h1 «Benvenuti a Musterwil» lautet. «Comune di Musterwil» würde passen. Ob ein offizieller Name in einer anderen Sprache ausreichend beschreibt, ist eine Ermessensfrage.',
      fr: 'Le titre nomme la commune, mais en allemand, alors que la page est en italien (lang="it") et que son h1 est « Benvenuti a Musterwil ». « Comune di Musterwil » conviendrait. Savoir si un nom officiel dans une autre langue est assez descriptif relève de l’appréciation.',
      it: 'Il titolo nomina il comune, ma in tedesco, mentre la pagina è in italiano (lang="it") e il suo h1 è «Benvenuti a Musterwil». «Comune di Musterwil» sarebbe adatto. Se un nome ufficiale in un’altra lingua sia abbastanza descrittivo è una valutazione.',
    },
    hint: {
      en: 'Set the title of the Italian home page to “Pagina iniziale – Comune di Musterwil”.',
      de: 'Setzen Sie den Titel der italienischen Startseite auf «Pagina iniziale – Comune di Musterwil».',
      fr: 'Définissez le titre de la page d’accueil italienne sur « Pagina iniziale – Comune di Musterwil ».',
      it: 'Impostare il titolo della pagina iniziale italiana su «Pagina iniziale – Comune di Musterwil».',
    },
  },
  {
    key: 'title-fr',
    criterion: '2.4.2',
    outcome: 'passed',
    source: 'apertus',
    confidence: 'high',
    page: PAGES.frHome,
    selector: 'head > title',
    excerpt: 'Accueil – Commune de Musterwil',
    act: 'c4a8a4',
    context: { title: 'Accueil – Commune de Musterwil', h1: 'Bienvenue à Musterwil', lang_declared: 'fr' },
    diff: null,
    impact: {
      en: 'The title says which page this is and whose site it is.',
      de: 'Der Titel sagt, welche Seite das ist und zu welcher Website sie gehört.',
      fr: 'Le titre indique de quelle page il s’agit et à quel site elle appartient.',
      it: 'Il titolo dice di quale pagina si tratta e a quale sito appartiene.',
    },
    explanation: {
      en: 'The title names the page (“Accueil”, home) and the site, in the page’s language.',
      de: 'Der Titel nennt die Seite («Accueil», Startseite) und die Website, in der Sprache der Seite.',
      fr: 'Le titre nomme la page (« Accueil ») et le site, dans la langue de la page.',
      it: 'Il titolo nomina la pagina («Accueil», pagina iniziale) e il sito, nella lingua della pagina.',
    },
    hint: null,
  },
  {
    key: 'contrast-footer',
    criterion: '1.4.3',
    outcome: 'failed',
    source: 'rule',
    confidence: 'high',
    page: PAGES.deHome,
    selector: 'footer > nav > a:nth-of-type(2)',
    excerpt: 'Impressum',
    act: 'afw4f7',
    context: {},
    diff: diff('css/site.css', 88, ['footer a { color: #8c8c8c; }'], ['footer a { color: #5e5e5e; }']),
    impact: {
      en: 'People with low vision may not be able to read the footer links.',
      de: 'Menschen mit Sehbehinderung können die Links in der Fusszeile womöglich nicht lesen.',
      fr: 'Les personnes malvoyantes risquent de ne pas pouvoir lire les liens du pied de page.',
      it: 'Le persone ipovedenti potrebbero non riuscire a leggere i link nel piè di pagina.',
    },
    explanation: {
      en: 'Text contrast is 3.1:1 (#8C8C8C on #F4F4F4). At this size at least 4.5:1 is required. axe-core measured it; no model was involved.',
      de: 'Der Textkontrast beträgt 3,1:1 (#8C8C8C auf #F4F4F4). Bei dieser Grösse sind mindestens 4,5:1 nötig. axe-core hat das gemessen; kein Modell war beteiligt.',
      fr: 'Le contraste du texte est de 3,1:1 (#8C8C8C sur #F4F4F4). À cette taille, il faut au moins 4,5:1. axe-core l’a mesuré ; aucun modèle n’est intervenu.',
      it: 'Il contrasto del testo è 3,1:1 (#8C8C8C su #F4F4F4). A questa dimensione servono almeno 4,5:1. L’ha misurato axe-core; nessun modello è stato coinvolto.',
    },
    hint: {
      en: 'Ask your web agency to darken the footer link colour to at least #5E5E5E.',
      de: 'Bitten Sie Ihre Webagentur, die Linkfarbe in der Fusszeile auf mindestens #5E5E5E abzudunkeln.',
      fr: 'Demandez à votre agence web d’assombrir la couleur des liens du pied de page à au moins #5E5E5E.',
      it: 'Chiedere all’agenzia web di scurire il colore dei link del piè di pagina almeno a #5E5E5E.',
    },
  },
]

/** Deterministic 12-hex id, like the backend's sha1(...)[:12]. */
export function hexId(seed: string): string {
  let h1 = 0x811c9dc5
  let h2 = 0x01000193
  for (let i = 0; i < seed.length; i++) {
    const c = seed.charCodeAt(i)
    h1 = Math.imul(h1 ^ c, 0x01000193) >>> 0
    h2 = Math.imul(h2 ^ c, 0x5bd1e995) >>> 0
  }
  return (h1.toString(16).padStart(8, '0') + h2.toString(16).padStart(8, '0')).slice(0, 12)
}

/**
 * Only fixtures for implemented criteria are served, so the mock-up never shows a
 * finding for a check that does not exist. The other texts wait for their check modules.
 */
export const SERVED_SPECS = SPECS.filter((s) => MOCK_IMPLEMENTED.includes(s.criterion))

export const MODEL_BY_MODE: Record<Mode, string> = {
  local: 'swiss-ai/Apertus-v1.5-8B',
  swiss_cloud: 'swiss-ai/Apertus-v1.5-70B',
  external: 'swiss-ai/Apertus-v1.5-70B',
  replay: 'swiss-ai/Apertus-v1.5-8B',
}

export function buildFinding(spec: FindingSpec, scanId: string, lang: UiLang, model: string): Finding {
  const c = wcag(spec.criterion)
  const pageLang = spec.page.match(/\/(de|fr|it|en)\//)?.[1] ?? null
  return {
    id: hexId(`${scanId}|${spec.page}|${spec.selector}|${spec.criterion}`),
    criterion: spec.criterion,
    criterion_name: c?.title ?? spec.criterion,
    level: c?.level ?? 'A',
    act_rule: spec.act ?? null,
    axe_rule: spec.source === 'rule' && spec.criterion === '1.4.3' ? 'color-contrast' : null,
    en301549: en301549(spec.criterion),
    outcome: spec.outcome,
    source: spec.source,
    confidence: spec.confidence,
    page_url: spec.page,
    selector: spec.selector,
    excerpt: spec.excerpt,
    content_lang: guessLang(spec.excerpt) ?? pageLang,
    context_shown: spec.context,
    // The four "Mehr" teasers share one reason: the UI groups them into one row ×4.
    reason_code: /^mehr-\d$/.test(spec.key) ? 'link_text_generic' : spec.key.replace(/-/g, '_'),
    reason: spec.source === 'apertus' ? `${spec.explanation.en.split('. ')[0]!.replace(/\.$/, '')}.` : null,
    explanation: spec.explanation[lang],
    user_impact: spec.impact[lang],
    fix_diff: spec.diff,
    fix_hint: spec.hint ? spec.hint[lang] : null,
    screenshot: spec.screenshot ?? null,
    model: spec.source === 'apertus' ? model : null,
    status: 'to_review',
  }
}

export const LLM_CALLS = 37
export const ELEMENTS = 142

export function finalProgress(createdAt: number): ProgressStep[] {
  const steps: [string, number, string | null][] = [
    ['render', 1300, 'Gemeinde Musterwil'],
    ['axe', 1000, '31 rule violations'],
    ['extract', 600, `${ELEMENTS} elements`],
    ['apertus', 6000, `${LLM_CALLS}/${LLM_CALLS}`],
    ['verify', 700, '1 answer not grounded'],
    ['done', 100, null],
  ]
  let t = createdAt
  return steps.map(([step, dur, detail]) => {
    const apertus = step === 'apertus'
    const s: ProgressStep = {
      step,
      state: 'done',
      started_at: new Date(t).toISOString(),
      duration_ms: dur,
      detail,
      current: apertus ? LLM_CALLS : null,
      total: apertus ? LLM_CALLS : null,
    }
    t += dur
    return s
  })
}

/** Simulated AI requests per destination for a finished mock scan. */
export function mockAiRequests(mode: Mode): AiRequests {
  const calls = mode === 'replay' ? 0 : LLM_CALLS
  return {
    local: mode === 'local' ? calls : 0,
    swiss_cloud: mode === 'swiss_cloud' ? calls : 0,
    external: mode === 'external' ? calls : 0,
  }
}

export function buildScan(opts: { id: string; url: string; lang: UiLang; mode: Mode; createdAt: number }): Scan {
  const model = MODEL_BY_MODE[opts.mode]
  const findings = SERVED_SPECS.map((s) => buildFinding(s, opts.id, opts.lang, model))
  const coverage = Object.fromEntries(MOCK_CRITERIA.map((c) => [c.criterion, c.method]))
  const counts = { failed: 0, cantTell: 0, passed: 0, inapplicable: 0 }
  for (const f of findings) counts[f.outcome]++
  const ruleCriteria = new Set(findings.filter((f) => f.source !== 'apertus').map((f) => f.criterion))
  const stats: ScanStats = {
    ...counts,
    to_review: findings.length,
    accepted: 0,
    rejected: 0,
    criteria_checked: MOCK_IMPLEMENTED.length,
    criteria_rule: ruleCriteria.size,
    criteria_apertus: MOCK_IMPLEMENTED.length - ruleCriteria.size,
    llm_calls: opts.mode === 'replay' ? 0 : LLM_CALLS,
    tokens_in: 48210,
    tokens_out: 4630,
    seconds: 9.7,
    guard_rejected: 1,
    injection_flagged: 0,
    not_recorded: 0,
    llm_errors: 0,
    budget_skipped: {},
    replay_loose_hits: 0,
    ai_requests: mockAiRequests(opts.mode),
    error_code: null,
    http_status: 200,
    final_url: opts.url,
    page_title: 'Gemeinde Musterwil',
    max_llm_calls: 150,
    timeout_notes: 0,
    timeout_skipped_checks: [],
    asked_apertus: LLM_CALLS,
    mock: MOCK_SENTINEL,
  }
  return {
    id: opts.id,
    url: opts.url,
    created_at: new Date(opts.createdAt).toISOString(),
    mode: opts.mode,
    model,
    ui_lang: opts.lang,
    state: 'done',
    progress: finalProgress(opts.createdAt),
    findings,
    coverage,
    stats,
  }
}
