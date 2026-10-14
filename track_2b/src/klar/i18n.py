"""User-facing strings produced by code (not by the model), in EN · DE · FR · IT.

Writing rules: short, concrete, no jargon. Never "compliant", "certified",
"conformance score" or "100 %". Apertus writes its own explanations in the UI
language; the strings here cover deterministic findings, notes and templates.

Usage: t("note.vision_required", "de")  or  t("c244.impact", "fr", name="Plus").
Missing keys fall back to English, then to the key itself (never crash a scan).
"""

from __future__ import annotations

MESSAGES: dict[str, dict[str, str]] = {
    # --- report ----------------------------------------------------------------
    "disclaimer": {
        "en": "Klar. pre-checks {n} of 50 WCAG 2.1 AA criteria ({m} with an Apertus judgement). This report does not certify conformance.",
        "de": "Klar. prüft {n} von 50 Kriterien der WCAG 2.1 AA vor ({m} mit einer Beurteilung durch Apertus). Dieser Bericht bescheinigt keine Konformität.",
        "fr": "Klar. pré-contrôle {n} des 50 critères WCAG 2.1 AA ({m} avec un jugement d'Apertus). Ce rapport ne certifie pas la conformité.",
        "it": "Klar. pre-verifica {n} dei 50 criteri WCAG 2.1 AA ({m} con una valutazione di Apertus). Questo rapporto non certifica la conformità.",
    },
    # --- notes for cantTell: say plainly WHY a person must decide -----------------------
    "note.vision_required": {
        "en": "Apertus has to look at this image to judge it, but the connected model cannot read images. Please check it yourself.",
        "de": "Apertus müsste dieses Bild ansehen, um es zu beurteilen, aber das verbundene Modell kann keine Bilder lesen. Bitte prüfen Sie es selbst.",
        "fr": "Apertus devrait regarder cette image pour la juger, mais le modèle connecté ne sait pas lire les images. Merci de la vérifier vous-même.",
        "it": "Apertus dovrebbe guardare questa immagine per giudicarla, ma il modello collegato non sa leggere le immagini. Verificatela voi stessi.",
    },
    "note.not_recorded": {
        "en": "This is a recorded demo without a live model, and no Apertus answer was recorded for this element. Please check it yourself.",
        "de": "Dies ist eine aufgezeichnete Demo ohne laufendes Modell, und für dieses Element wurde keine Apertus-Antwort aufgezeichnet. Bitte prüfen Sie es selbst.",
        "fr": "Ceci est une démo enregistrée sans modèle actif, et aucune réponse d'Apertus n'a été enregistrée pour cet élément. Merci de le vérifier vous-même.",
        "it": "Questa è una demo registrata senza modello attivo, e per questo elemento non è stata registrata alcuna risposta di Apertus. Verificatelo voi stessi.",
    },
    "note.not_grounded": {
        "en": "Apertus' answer did not match the page ({reason}), so Klar. discarded it. Please check this element yourself.",
        "de": "Die Antwort von Apertus passte nicht zur Seite und ist nicht belegt ({reason}); Klar. hat sie verworfen. Bitte prüfen Sie das Element selbst.",
        "fr": "La réponse d'Apertus ne correspondait pas à la page ({reason}) ; Klar. l'a écartée. Merci de vérifier cet élément vous-même.",
        "it": "La risposta di Apertus non corrispondeva alla pagina ({reason}); Klar. l'ha scartata. Verificate voi stessi questo elemento.",
    },
    "note.unparseable": {
        "en": "Apertus answered, but not in the expected form, so Klar. did not use the answer. Please check this element yourself.",
        "de": "Apertus hat geantwortet, aber nicht in der erwarteten Form; Klar. hat die Antwort nicht verwendet. Bitte prüfen Sie das Element selbst.",
        "fr": "Apertus a répondu, mais pas sous la forme attendue ; Klar. n'a pas utilisé la réponse. Merci de vérifier cet élément vous-même.",
        "it": "Apertus ha risposto, ma non nella forma attesa; Klar. non ha usato la risposta. Verificate voi stessi questo elemento.",
    },
    "note.request_failed": {
        "en": "The model could not be reached ({error}), so this element was not judged. Please check it yourself.",
        "de": "Das Modell war nicht erreichbar ({error}), daher wurde dieses Element nicht beurteilt. Bitte prüfen Sie es selbst.",
        "fr": "Le modèle n'a pas pu être joint ({error}) ; cet élément n'a donc pas été jugé. Merci de le vérifier vous-même.",
        "it": "Il modello non era raggiungibile ({error}), quindi questo elemento non è stato giudicato. Verificatelo voi stessi.",
    },
    "note.budget": {
        "en": "This scan reached its limit of questions to the model before this element. Please check it yourself.",
        "de": "Dieser Scan hat sein Limit an Fragen an das Modell vor diesem Element erreicht. Bitte prüfen Sie es selbst.",
        "fr": "Cette analyse a atteint sa limite de questions au modèle avant cet élément. Merci de le vérifier vous-même.",
        "it": "Questa scansione ha raggiunto il limite di domande al modello prima di questo elemento. Verificatelo voi stessi.",
    },
    "note.no_screenshot": {
        "en": "Klar. could not take a picture of this element, so Apertus could not look at it. Please check it yourself.",
        "de": "Klar. konnte kein Bild dieses Elements aufnehmen, daher konnte Apertus es nicht ansehen. Bitte prüfen Sie es selbst.",
        "fr": "Klar. n'a pas pu prendre d'image de cet élément ; Apertus n'a donc pas pu le regarder. Merci de le vérifier vous-même.",
        "it": "Klar. non ha potuto fotografare questo elemento, quindi Apertus non ha potuto guardarlo. Verificatelo voi stessi.",
    },
    "note.suspicious": {
        "en": "This element contains text that looks like instructions to an AI ({pattern}). To avoid manipulation, Klar. did not ask the model. Please check it yourself.",
        "de": "Dieses Element enthält Text, der wie Anweisungen an eine KI aussieht ({pattern}). Um Manipulation zu vermeiden, hat Klar. das Modell nicht gefragt. Bitte prüfen Sie es selbst.",
        "fr": "Cet élément contient un texte qui ressemble à des instructions pour une IA ({pattern}). Pour éviter toute manipulation, Klar. n'a pas interrogé le modèle. Merci de le vérifier vous-même.",
        "it": "Questo elemento contiene testo che sembra un'istruzione per un'IA ({pattern}). Per evitare manipolazioni, Klar. non ha interrogato il modello. Verificatelo voi stessi.",
    },
    "note.timeout": {
        "en": "The scan reached its time limit before this element was judged. Please check it yourself.",
        "de": "Der Scan hat sein Zeitlimit erreicht, bevor dieses Element beurteilt wurde. Bitte prüfen Sie es selbst.",
        "fr": "L'analyse a atteint sa limite de temps avant que cet élément soit jugé. Merci de le vérifier vous-même.",
        "it": "La scansione ha raggiunto il limite di tempo prima che questo elemento fosse giudicato. Verificatelo voi stessi.",
    },

    "impact.review": {
        "en": "A person must decide whether this element is a barrier.",
        "de": "Eine Person muss entscheiden, ob dieses Element eine Barriere ist.",
        "fr": "Une personne doit décider si cet élément constitue un obstacle.",
        "it": "Una persona deve decidere se questo elemento è una barriera.",
    },
    "impact.generic": {
        "en": "People using assistive technology may not be able to perceive or use this element.",
        "de": "Menschen mit assistiven Technologien können dieses Element eventuell nicht wahrnehmen oder bedienen.",
        "fr": "Les personnes utilisant une technologie d'assistance risquent de ne pas pouvoir percevoir ou utiliser cet élément.",
        "it": "Le persone che usano tecnologie assistive potrebbero non riuscire a percepire o usare questo elemento.",
    },
    # --- axe-core (rule findings) -------------------------------------------------
    "axe.explanation": {
        "en": "axe-core rule “{rule}”: {help}",
        "de": "axe-core-Regel «{rule}»: {help}",
        "fr": "Règle axe-core « {rule} » : {help}",
        "it": "Regola axe-core «{rule}»: {help}",
    },
    # --- 3.1.2 Language of parts ------------------------------------------------
    "c312.impact": {
        "en": "Screen readers will read this {actual} text with a {declared} voice.",
        "de": "Screenreader lesen diesen {actual} Text mit einer {declared} Stimme vor.",
        "fr": "Les lecteurs d'écran liront ce texte {actual} avec une voix {declared}.",
        "it": "I lettori di schermo leggeranno questo testo {actual} con una voce {declared}.",
    },
    "c312.impact_invalid": {
        "en": "Screen readers cannot pick a voice for the code “{value}” and may mispronounce this text.",
        "de": "Screenreader finden keine Stimme für den Code «{value}» und sprechen den Text eventuell falsch aus.",
        "fr": "Les lecteurs d'écran ne trouvent pas de voix pour le code « {value} » et risquent de mal prononcer ce texte.",
        "it": "I lettori di schermo non trovano una voce per il codice «{value}» e potrebbero pronunciare male il testo.",
    },
    "c312.impact_ok": {
        "en": "Screen readers switch to a {actual} voice for this text.",
        "de": "Screenreader wechseln für diesen Text zu einer {declared_like} Stimme.",
        "fr": "Les lecteurs d'écran passent à une voix {declared_like} pour ce texte.",
        "it": "I lettori di schermo passano a una voce {declared_like} per questo testo.",
    },
    "c312.page_mismatch": {
        "en": "The main text of this page is {actual_noun_en}, but the page declares lang=\"{declared_code}\". Fix the page language first (3.1.1 Language of Page); the language of parts is checked once it is right.",
        "de": "Der Haupttext dieser Seite ist {actual_pred}, die Seite deklariert aber lang=\"{declared_code}\". Korrigieren Sie zuerst die Seitensprache (3.1.1 Sprache der Seite); die Sprache von Teilen wird danach geprüft.",
        "fr": "Le texte principal de cette page est en {actual_noun}, mais la page déclare lang=\"{declared_code}\". Corrigez d'abord la langue de la page (3.1.1 Langue de la page) ; la langue des passages sera vérifiée ensuite.",
        "it": "Il testo principale di questa pagina è in {actual_noun}, ma la pagina dichiara lang=\"{declared_code}\". Correggete prima la lingua della pagina (3.1.1 Lingua della pagina); la lingua delle parti sarà verificata dopo.",
    },
    "c312.contact_line": {
        "en": "This line is only an address or contact detail. Names and addresses need no lang attribute.",
        "de": "Diese Zeile enthält nur eine Adresse oder Kontaktangabe. Namen und Adressen brauchen kein lang-Attribut.",
        "fr": "Cette ligne ne contient qu'une adresse ou un contact. Les noms et adresses n'ont pas besoin d'attribut lang.",
        "it": "Questa riga contiene solo un indirizzo o un contatto. Nomi e indirizzi non richiedono l'attributo lang.",
    },
    "c312.switcher": {
        "en": "“{text}” is a language name written in that language; it needs lang=\"{code}\" to be pronounced correctly.",
        "de": "«{text}» ist ein Sprachname in der eigenen Sprache; er braucht lang=\"{code}\", damit er richtig ausgesprochen wird.",
        "fr": "« {text} » est un nom de langue écrit dans cette langue ; il doit porter lang=\"{code}\" pour être bien prononcé.",
        "it": "«{text}» è il nome di una lingua scritto in quella lingua; serve lang=\"{code}\" perché sia pronunciato correttamente.",
    },
    "c312.impact_exception": {
        "en": "No change needed: names and everyday loanwords are read with the voice of the page.",
        "de": "Keine Änderung nötig: Namen und gebräuchliche Lehnwörter werden mit der Stimme der Seite gelesen.",
        "fr": "Aucune modification nécessaire : les noms et les emprunts courants sont lus avec la voix de la page.",
        "it": "Nessuna modifica necessaria: i nomi e i prestiti comuni sono letti con la voce della pagina.",
    },
    "c312.tagged_ok": {
        "en": "The passage is marked lang=\"{code}\" and the language detector agrees.",
        "de": "Die Passage ist mit lang=\"{code}\" ausgezeichnet und die Spracherkennung stimmt zu.",
        "fr": "Le passage est balisé lang=\"{code}\" et le détecteur de langue le confirme.",
        "it": "Il passaggio è marcato lang=\"{code}\" e il rilevatore di lingua lo conferma.",
    },
    "c312.invalid": {
        "en": "The lang value “{value}” is not a valid language code.",
        "de": "Der lang-Wert «{value}» ist kein gültiger Sprachcode.",
        "fr": "La valeur lang « {value} » n'est pas un code de langue valide.",
        "it": "Il valore lang «{value}» non è un codice di lingua valido.",
    },
    "c312.mismatch": {
        "en": "The passage is marked lang=\"{declared_code}\" but its text is {actual}.",
        "de": "Die Passage ist mit lang=\"{declared_code}\" ausgezeichnet, ihr Text ist aber {actual_pred}.",
        "fr": "Le passage est balisé lang=\"{declared_code}\" mais son texte est en {actual_noun}.",
        "it": "Il passaggio è marcato lang=\"{declared_code}\" ma il testo è in {actual_noun}.",
    },
    "c312.untagged": {
        "en": "This passage is {actual} but it inherits lang=\"{declared_code}\" and has no lang attribute of its own.",
        "de": "Diese Passage ist {actual_pred}, erbt aber lang=\"{declared_code}\" und hat kein eigenes lang-Attribut.",
        "fr": "Ce passage est en {actual_noun}, mais il hérite de lang=\"{declared_code}\" et n'a pas d'attribut lang propre.",
        "it": "Questo passaggio è in {actual_noun}, ma eredita lang=\"{declared_code}\" e non ha un attributo lang proprio.",
    },
    "c312.exception": {
        "en": "Apertus classified “{quote}” as {category}, an exception in WCAG 3.1.2 that needs no lang attribute.",
        "de": "Apertus stuft «{quote}» als {category} ein, eine Ausnahme nach WCAG 3.1.2, die kein lang-Attribut braucht.",
        "fr": "Apertus classe « {quote} » comme {category}, une exception du critère WCAG 3.1.2 qui ne demande pas d'attribut lang.",
        "it": "Apertus classifica «{quote}» come {category}, un'eccezione del criterio WCAG 3.1.2 che non richiede l'attributo lang.",
    },
    "c312.foreign": {
        "en": "Apertus classified “{quote}” as a passage in {actual_noun_en}, which needs its own lang attribute.",
        "de": "Apertus stuft «{quote}» als Passage auf {actual_noun} ein; sie braucht ein eigenes lang-Attribut.",
        "fr": "Apertus classe « {quote} » comme un passage en {actual_noun}, qui doit avoir son propre attribut lang.",
        "it": "Apertus classifica «{quote}» come un passaggio in {actual_noun}, che richiede un attributo lang proprio.",
    },
    "c312.other": {
        "en": "Apertus could not classify “{quote}”. A person must decide whether it needs a lang attribute.",
        "de": "Apertus konnte «{quote}» nicht einordnen. Eine Person muss entscheiden, ob ein lang-Attribut nötig ist.",
        "fr": "Apertus n'a pas pu classer « {quote} ». Une personne doit décider s'il faut un attribut lang.",
        "it": "Apertus non ha potuto classificare «{quote}». Una persona deve decidere se serve un attributo lang.",
    },
    "c312.fix_hint": {
        "en": "In your CMS, mark this text as {actual_noun_en} (language attribute lang=\"{code}\").",
        "de": "Markieren Sie diesen Text im CMS als {actual_noun} (Sprachattribut lang=\"{code}\").",
        "fr": "Dans votre CMS, indiquez que ce texte est en {actual_noun} (attribut de langue lang=\"{code}\").",
        "it": "Nel CMS, indicate che questo testo è in {actual_noun} (attributo di lingua lang=\"{code}\").",
    },
    "c312.fix_hint_invalid": {
        "en": "In your CMS, replace the language code “{value}” with a valid code such as “{code}”.",
        "de": "Ersetzen Sie im CMS den Sprachcode «{value}» durch einen gültigen Code wie «{code}».",
        "fr": "Dans votre CMS, remplacez le code de langue « {value} » par un code valide comme « {code} ».",
        "it": "Nel CMS, sostituite il codice di lingua «{value}» con un codice valido come «{code}».",
    },
    "c312.boundary": {
        "en": "Apertus classified “{quote}” as {category}: whether it needs a lang attribute is a judgement call. A person must decide.",
        "de": "Apertus stuft «{quote}» als {category} ein: Ob ein lang-Attribut nötig ist, ist Ermessenssache. Eine Person muss entscheiden.",
        "fr": "Apertus classe « {quote} » comme {category} : la nécessité d'un attribut lang relève de l'appréciation. Une personne doit trancher.",
        "it": "Apertus classifica «{quote}» come {category}: se serva l'attributo lang è una questione di giudizio. Una persona deve decidere.",
    },
    "c312.cat.greeting_or_formula": {"en": "a short greeting or formula", "de": "kurze Grussformel", "fr": "courte formule de salutation", "it": "breve formula di saluto"},
    "c312.cat.title_of_work": {"en": "the title of a work", "de": "Werktitel", "fr": "titre d'une œuvre", "it": "titolo di un'opera"},
    "c312.cat.proper_name": {"en": "a proper name", "de": "Eigenname", "fr": "nom propre", "it": "nome proprio"},
    "c312.cat.institution": {"en": "the name of an institution", "de": "Name einer Institution", "fr": "nom d'institution", "it": "nome di un'istituzione"},
    "c312.cat.place_or_address": {"en": "a place name or address", "de": "Ortsname oder Adresse", "fr": "nom de lieu ou adresse", "it": "nome di luogo o indirizzo"},
    "c312.cat.technical_term": {"en": "a technical term", "de": "Fachbegriff", "fr": "terme technique", "it": "termine tecnico"},
    "c312.cat.loanword_in_vernacular": {"en": "a loanword of everyday language", "de": "Lehnwort der Alltagssprache", "fr": "emprunt de la langue courante", "it": "prestito della lingua corrente"},
    # --- 2.4.4 Link purpose (in context) ----------------------------------------
    "c244.url_text": {
        "en": "The link text is the address itself, which identifies the destination.",
        "de": "Der Linktext ist die Adresse selbst und benennt damit das Ziel.",
        "fr": "Le texte du lien est l'adresse elle-même, qui identifie la destination.",
        "it": "Il testo del link è l'indirizzo stesso, che identifica la destinazione.",
    },
    "c244.descriptive": {
        "en": "The link text “{name}” names its destination on its own.",
        "de": "Der Linktext «{name}» benennt sein Ziel für sich allein.",
        "fr": "Le texte du lien « {name} » nomme sa destination à lui seul.",
        "it": "Il testo del link «{name}» indica da solo la sua destinazione.",
    },
    "c244.no_context": {
        "en": "“{name}” does not say where the link goes, and no sentence, paragraph, list item or table cell around it explains it.",
        "de": "«{name}» sagt nicht, wohin der Link führt, und kein Satz, Absatz, Listeneintrag oder keine Tabellenzelle darum herum erklärt es.",
        "fr": "« {name} » n'indique pas où mène le lien, et aucune phrase, aucun paragraphe, élément de liste ou cellule de tableau autour ne l'explique.",
        "it": "«{name}» non dice dove porta il link, e nessuna frase, paragrafo, voce di elenco o cella di tabella intorno lo spiega.",
    },
    "c244.apertus_link_text": {
        "en": "Apertus judged that the link text “{name}” says where the link goes.",
        "de": "Apertus beurteilt, dass der Linktext «{name}» sagt, wohin der Link führt.",
        "fr": "Apertus juge que le texte du lien « {name} » indique où il mène.",
        "it": "Apertus giudica che il testo del link «{name}» indichi dove porta.",
    },
    "c244.apertus_context": {
        "en": "Apertus judged that the programmatic context of “{name}” (sentence, block, list item, table cell or description) says where the link goes.",
        "de": "Apertus beurteilt, dass der programmatische Kontext von «{name}» (Satz, Block, Listeneintrag, Tabellenzelle oder Beschreibung) sagt, wohin der Link führt.",
        "fr": "Apertus juge que le contexte programmatique de « {name} » (phrase, bloc, élément de liste, cellule ou description) indique où mène le lien.",
        "it": "Apertus giudica che il contesto programmatico di «{name}» (frase, blocco, voce di elenco, cella o descrizione) indichi dove porta il link.",
    },
    "c244.apertus_nowhere": {
        "en": "Apertus judged that neither “{name}” nor its programmatic context says where the link goes.",
        "de": "Apertus beurteilt, dass weder «{name}» noch sein programmatischer Kontext sagt, wohin der Link führt.",
        "fr": "Apertus juge que ni « {name} » ni son contexte programmatique n'indiquent où mène le lien.",
        "it": "Apertus giudica che né «{name}» né il suo contesto programmatico indichino dove porta il link.",
    },
    "c244.apertus_unsure": {
        "en": "Apertus could not decide where “{name}” leads. A person must check it.",
        "de": "Apertus konnte nicht entscheiden, wohin «{name}» führt. Eine Person muss es prüfen.",
        "fr": "Apertus n'a pas pu décider où mène « {name} ». Une personne doit vérifier.",
        "it": "Apertus non ha potuto decidere dove porti «{name}». Una persona deve verificare.",
    },
    "c244.heading_only": {
        "en": "“{name}” is explained only by the heading “{heading}” before it. Headings are not programmatic link context, but some experts accept them (technique H80): a person must decide.",
        "de": "«{name}» wird nur durch die vorangehende Überschrift «{heading}» erklärt. Überschriften gehören nicht zum programmatischen Linkkontext, manche Fachleute akzeptieren sie aber (Technik H80): Eine Person muss entscheiden.",
        "fr": "« {name} » n'est expliqué que par le titre « {heading} » qui le précède. Les titres ne font pas partie du contexte programmatique du lien, mais certains experts les acceptent (technique H80) : une personne doit trancher.",
        "it": "«{name}» è spiegato solo dal titolo «{heading}» che lo precede. I titoli non fanno parte del contesto programmatico del link, ma alcuni esperti li accettano (tecnica H80): una persona deve decidere.",
    },
    "c244.language_switcher": {
        "en": "“{name}” is a language switch: it names a language ({language}) and leads to the version of the site in that language. This convention is clear without further context.",
        "de": "«{name}» ist eine Sprachumschaltung: Der Link nennt eine Sprache ({language}) und führt zur Version der Website in dieser Sprache. Diese Konvention ist ohne weiteren Kontext verständlich.",
        "fr": "« {name} » est un sélecteur de langue : il nomme une langue ({language}) et mène à la version du site dans cette langue. Cette convention se comprend sans autre contexte.",
        "it": "«{name}» è un selettore di lingua: indica una lingua ({language}) e porta alla versione del sito in quella lingua. Questa convenzione è comprensibile senza altro contesto.",
    },
    "c244.phone_number": {
        "en": "The link text is the phone number the link dials, which identifies the destination.",
        "de": "Der Linktext ist die Telefonnummer, die der Link wählt, und benennt damit das Ziel.",
        "fr": "Le texte du lien est le numéro de téléphone que le lien compose, ce qui identifie la destination.",
        "it": "Il testo del link è il numero di telefono che il link compone, e ne identifica quindi la destinazione.",
    },
    "c244.title_only": {
        "en": "“{name}” is explained only by its title attribute, which keyboard and touch users do not get (technique H33): a person must decide.",
        "de": "«{name}» wird nur durch sein title-Attribut erklärt, das Tastatur- und Touch-Nutzende nicht erhalten (Technik H33): Eine Person muss entscheiden.",
        "fr": "« {name} » n'est expliqué que par son attribut title, que les personnes au clavier ou sur écran tactile ne reçoivent pas (technique H33) : une personne doit trancher.",
        "it": "«{name}» è spiegato solo dal suo attributo title, che chi usa tastiera o touch non riceve (tecnica H33): una persona deve decidere.",
    },
    "c244.impact_maybe": {
        "en": "Screen-reader users who list the links may hear “{name}” without knowing where it leads.",
        "de": "Screenreader-Nutzende, die sich die Links auflisten lassen, hören eventuell «{name}», ohne zu wissen, wohin er führt.",
        "fr": "Les utilisateurs de lecteurs d'écran qui listent les liens risquent d'entendre « {name} » sans savoir où il mène.",
        "it": "Chi usa un lettore di schermo ed elenca i link potrebbe sentire «{name}» senza sapere dove porta.",
    },
    "c244.impact": {
        "en": "Screen-reader users who list the links hear “{name}” without knowing where it leads.",
        "de": "Screenreader-Nutzende, die sich die Links auflisten lassen, hören «{name}», ohne zu wissen, wohin er führt.",
        "fr": "Les utilisateurs de lecteurs d'écran qui listent les liens entendent « {name} » sans savoir où il mène.",
        "it": "Chi usa un lettore di schermo ed elenca i link sente «{name}» senza sapere dove porta.",
    },
    "c244.impact_ok": {
        "en": "Screen-reader users know where “{name}” leads.",
        "de": "Screenreader-Nutzende wissen, wohin «{name}» führt.",
        "fr": "Les utilisateurs de lecteurs d'écran savent où mène « {name} ».",
        "it": "Chi usa un lettore di schermo sa dove porta «{name}».",
    },
    "c244.fix_hint": {
        "en": "In your CMS, change the link text so that it names the destination, for example “{proposal}”.",
        "de": "Ändern Sie im CMS den Linktext so, dass er das Ziel benennt, zum Beispiel «{proposal}».",
        "fr": "Dans votre CMS, modifiez le texte du lien pour qu'il nomme la destination, par exemple « {proposal} ».",
        "it": "Nel CMS, modificate il testo del link in modo che indichi la destinazione, per esempio «{proposal}».",
    },
    "c244.fix_hint_plain": {
        "en": "In your CMS, change the link text so that it names the destination.",
        "de": "Ändern Sie im CMS den Linktext so, dass er das Ziel benennt.",
        "fr": "Dans votre CMS, modifiez le texte du lien pour qu'il nomme la destination.",
        "it": "Nel CMS, modificate il testo del link in modo che indichi la destinazione.",
    },
    "c244.fix_unverified": {
        "en": "Check that the suggestion matches the destination page.",
        "de": "Prüfen Sie, ob der Vorschlag zur Zielseite passt.",
        "fr": "Vérifiez que la suggestion correspond à la page de destination.",
        "it": "Verificate che il suggerimento corrisponda alla pagina di destinazione.",
    },
    # --- 1.1.1 Non-text content -------------------------------------------------
    "c111.filename": {
        "en": "The text alternative “{alt}” is a file name, not a description of the image.",
        "de": "Der Alternativtext «{alt}» ist ein Dateiname, keine Beschreibung des Bildes.",
        "fr": "L'alternative textuelle « {alt} » est un nom de fichier, pas une description de l'image.",
        "it": "L'alternativa testuale «{alt}» è un nome di file, non una descrizione dell'immagine.",
    },
    "c111.placeholder": {
        "en": "The text alternative “{alt}” only says that there is an image, not what it shows.",
        "de": "Der Alternativtext «{alt}» sagt nur, dass hier ein Bild ist, nicht was es zeigt.",
        "fr": "L'alternative textuelle « {alt} » dit seulement qu'il y a une image, pas ce qu'elle montre.",
        "it": "L'alternativa testuale «{alt}» dice solo che c'è un'immagine, non cosa mostra.",
    },
    "c111.apertus_ok": {
        "en": "Apertus judged that the text alternative “{alt}” gives the same information as the image ({type}).",
        "de": "Apertus beurteilt den Alternativtext «{alt}» als gleichwertig zum Bild ({type}).",
        "fr": "Apertus juge que l'alternative textuelle « {alt} » donne la même information que l'image ({type}).",
        "it": "Apertus giudica che l'alternativa testuale «{alt}» dia la stessa informazione dell'immagine ({type}).",
    },
    "c111.apertus_failed": {
        "en": "Apertus judged that the text alternative “{alt}” does not convey what the image shows ({type}).",
        "de": "Apertus beurteilt, dass der Alternativtext «{alt}» nicht wiedergibt, was das Bild zeigt ({type}).",
        "fr": "Apertus juge que l'alternative textuelle « {alt} » ne rend pas ce que montre l'image ({type}).",
        "it": "Apertus giudica che l'alternativa testuale «{alt}» non renda ciò che mostra l'immagine ({type}).",
    },
    "c111.apertus_hidden": {
        "en": "Apertus judged that this image carries information but is hidden from screen readers ({type}).",
        "de": "Apertus beurteilt, dass dieses Bild Information trägt, aber vor Screenreadern verborgen ist ({type}).",
        "fr": "Apertus juge que cette image porte une information mais qu'elle est masquée aux lecteurs d'écran ({type}).",
        "it": "Apertus giudica che questa immagine porti informazioni ma sia nascosta ai lettori di schermo ({type}).",
    },
    "c111.apertus_unsure": {
        "en": "Apertus could not decide whether the text alternative “{alt}” is adequate. A person must check it.",
        "de": "Apertus konnte nicht entscheiden, ob der Alternativtext «{alt}» angemessen ist. Eine Person muss es prüfen.",
        "fr": "Apertus n'a pas pu décider si l'alternative textuelle « {alt} » convient. Une personne doit vérifier.",
        "it": "Apertus non ha potuto decidere se l'alternativa testuale «{alt}» sia adeguata. Una persona deve verificare.",
    },
    "c111.type.decorative": {"en": "decorative", "de": "dekorativ", "fr": "décorative", "it": "decorativa"},
    "c111.type.informative": {"en": "informative", "de": "informativ", "fr": "informative", "it": "informativa"},
    "c111.type.functional": {"en": "functional", "de": "funktional", "fr": "fonctionnelle", "it": "funzionale"},
    "c111.type.complex": {"en": "complex: chart, map or diagram", "de": "komplex: Diagramm, Karte oder Schema", "fr": "complexe : graphique, carte ou schéma", "it": "complessa: grafico, mappa o schema"},
    "c111.type.text": {"en": "image of text", "de": "Textgrafik", "fr": "image de texte", "it": "immagine di testo"},
    "c111.functional_empty": {
        "en": "The image is the only content of a link or button but its text alternative is empty, so the control has no name.",
        "de": "Das Bild ist der einzige Inhalt eines Links oder einer Schaltfläche, sein Alternativtext ist aber leer: Das Bedienelement hat keinen Namen.",
        "fr": "L'image est le seul contenu d'un lien ou d'un bouton, mais son alternative textuelle est vide : le contrôle n'a pas de nom.",
        "it": "L'immagine è l'unico contenuto di un link o di un pulsante, ma la sua alternativa testuale è vuota: il controllo non ha nome.",
    },
    "c111.impact_functional": {
        "en": "Screen-reader users hear a link or button without knowing where it leads or what it does.",
        "de": "Screenreader-Nutzende hören einen Link oder eine Schaltfläche, ohne zu wissen, wohin er führt oder was sie bewirkt.",
        "fr": "Les utilisateurs de lecteurs d'écran entendent un lien ou un bouton sans savoir où il mène ni ce qu'il fait.",
        "it": "Chi usa un lettore di schermo sente un link o un pulsante senza sapere dove porta o cosa fa.",
    },
    "c111.fix_hint_functional": {
        "en": "In your CMS, give the image a text alternative that names the link destination or the button action.",
        "de": "Geben Sie dem Bild im CMS einen Alternativtext, der das Linkziel oder die Aktion der Schaltfläche benennt.",
        "fr": "Dans votre CMS, donnez à l'image une alternative textuelle qui nomme la destination du lien ou l'action du bouton.",
        "it": "Nel CMS, date all'immagine un testo alternativo che indichi la destinazione del link o l'azione del pulsante.",
    },
    "c111.decorative_small": {
        "en": "The image is marked as decorative and is too small to carry information.",
        "de": "Das Bild ist als dekorativ ausgezeichnet und zu klein, um Information zu tragen.",
        "fr": "L'image est marquée comme décorative et elle est trop petite pour porter une information.",
        "it": "L'immagine è marcata come decorativa ed è troppo piccola per veicolare informazioni.",
    },
    "c111.impact": {
        "en": "Screen-reader users hear “{alt}” instead of what the image shows.",
        "de": "Screenreader-Nutzende hören «{alt}» statt dessen, was das Bild zeigt.",
        "fr": "Les utilisateurs de lecteurs d'écran entendent « {alt} » au lieu de ce que montre l'image.",
        "it": "Chi usa un lettore di schermo sente «{alt}» invece di ciò che mostra l'immagine.",
    },
    "c111.impact_hidden": {
        "en": "Screen-reader users miss the information in this image because it is hidden from them.",
        "de": "Screenreader-Nutzenden entgeht die Information in diesem Bild, weil es vor ihnen verborgen ist.",
        "fr": "Les utilisateurs de lecteurs d'écran manquent l'information de cette image, car elle leur est masquée.",
        "it": "Chi usa un lettore di schermo perde l'informazione di questa immagine, perché gli è nascosta.",
    },
    "c111.impact_ok": {
        "en": "Screen-reader users get the same information as sighted users.",
        "de": "Screenreader-Nutzende erhalten dieselbe Information wie Sehende.",
        "fr": "Les utilisateurs de lecteurs d'écran reçoivent la même information que les personnes voyantes.",
        "it": "Chi usa un lettore di schermo riceve la stessa informazione di chi vede.",
    },
    "c111.fix_hint": {
        "en": "In your CMS, write in the alternative text field what the image shows, for example “{proposal}”.",
        "de": "Beschreiben Sie im CMS im Feld für den Alternativtext, was das Bild zeigt, zum Beispiel «{proposal}».",
        "fr": "Dans votre CMS, décrivez dans le champ « texte alternatif » ce que montre l'image, par exemple « {proposal} ».",
        "it": "Nel CMS, descrivete nel campo del testo alternativo cosa mostra l'immagine, per esempio «{proposal}».",
    },
    "c111.fix_hint_plain": {
        "en": "In your CMS, write in the alternative text field what the image shows.",
        "de": "Beschreiben Sie im CMS im Feld für den Alternativtext, was das Bild zeigt.",
        "fr": "Dans votre CMS, décrivez dans le champ « texte alternatif » ce que montre l'image.",
        "it": "Nel CMS, descrivete nel campo del testo alternativo cosa mostra l'immagine.",
    },
    "c111.fix_hint_decorative": {
        "en": "In your CMS, mark the image as decorative (empty alternative text).",
        "de": "Markieren Sie das Bild im CMS als dekorativ (leerer Alternativtext).",
        "fr": "Dans votre CMS, marquez l'image comme décorative (texte alternatif vide).",
        "it": "Nel CMS, marcate l'immagine come decorativa (testo alternativo vuoto).",
    },
    "c111.fix_hint_complex": {
        "en": "Keep a short alternative text and add a long description next to the image (for example the data as a table).",
        "de": "Behalten Sie einen kurzen Alternativtext und ergänzen Sie neben dem Bild eine ausführliche Beschreibung (zum Beispiel die Daten als Tabelle).",
        "fr": "Gardez une alternative courte et ajoutez une description détaillée à côté de l'image (par exemple les données sous forme de tableau).",
        "it": "Mantenete un'alternativa breve e aggiungete una descrizione estesa accanto all'immagine (per esempio i dati in una tabella).",
    },
}


# Language names with the grammatical forms the templates above need.
#   en      noun/adjective ("French")
#   de_adj  inflected adjective: "diesen französischen Text", "einer deutschen Stimme"
#   de_pred predicative: "ist französisch"; de_noun: "auf Französisch"
#   fr_m / fr_f  "ce texte français", "une voix française"; fr_noun "en français"
#   it_m / it_f  "testo francese", "voce tedesca"; it_noun "in francese"
LANG_FORMS: dict[str, dict[str, str]] = {
    "de": dict(en="German", de_adj="deutschen", de_pred="deutsch", de_noun="Deutsch", fr_m="allemand", fr_f="allemande", fr_noun="allemand", it_m="tedesco", it_f="tedesca", it_noun="tedesco"),
    "fr": dict(en="French", de_adj="französischen", de_pred="französisch", de_noun="Französisch", fr_m="français", fr_f="française", fr_noun="français", it_m="francese", it_f="francese", it_noun="francese"),
    "it": dict(en="Italian", de_adj="italienischen", de_pred="italienisch", de_noun="Italienisch", fr_m="italien", fr_f="italienne", fr_noun="italien", it_m="italiano", it_f="italiana", it_noun="italiano"),
    "en": dict(en="English", de_adj="englischen", de_pred="englisch", de_noun="Englisch", fr_m="anglais", fr_f="anglaise", fr_noun="anglais", it_m="inglese", it_f="inglese", it_noun="inglese"),
    "rm": dict(en="Romansh", de_adj="rätoromanischen", de_pred="rätoromanisch", de_noun="Rätoromanisch", fr_m="romanche", fr_f="romanche", fr_noun="romanche", it_m="romancio", it_f="romancia", it_noun="romancio"),
    "es": dict(en="Spanish", de_adj="spanischen", de_pred="spanisch", de_noun="Spanisch", fr_m="espagnol", fr_f="espagnole", fr_noun="espagnol", it_m="spagnolo", it_f="spagnola", it_noun="spagnolo"),
    "pt": dict(en="Portuguese", de_adj="portugiesischen", de_pred="portugiesisch", de_noun="Portugiesisch", fr_m="portugais", fr_f="portugaise", fr_noun="portugais", it_m="portoghese", it_f="portoghese", it_noun="portoghese"),
    "nl": dict(en="Dutch", de_adj="niederländischen", de_pred="niederländisch", de_noun="Niederländisch", fr_m="néerlandais", fr_f="néerlandaise", fr_noun="néerlandais", it_m="olandese", it_f="olandese", it_noun="olandese"),
    "la": dict(en="Latin", de_adj="lateinischen", de_pred="lateinisch", de_noun="Latein", fr_m="latin", fr_f="latine", fr_noun="latin", it_m="latino", it_f="latina", it_noun="latino"),
    "sq": dict(en="Albanian", de_adj="albanischen", de_pred="albanisch", de_noun="Albanisch", fr_m="albanais", fr_f="albanaise", fr_noun="albanais", it_m="albanese", it_f="albanese", it_noun="albanese"),
    "tr": dict(en="Turkish", de_adj="türkischen", de_pred="türkisch", de_noun="Türkisch", fr_m="turc", fr_f="turque", fr_noun="turc", it_m="turco", it_f="turca", it_noun="turco"),
    "hr": dict(en="Croatian", de_adj="kroatischen", de_pred="kroatisch", de_noun="Kroatisch", fr_m="croate", fr_f="croate", fr_noun="croate", it_m="croato", it_f="croata", it_noun="croato"),
    "sr": dict(en="Serbian", de_adj="serbischen", de_pred="serbisch", de_noun="Serbisch", fr_m="serbe", fr_f="serbe", fr_noun="serbe", it_m="serbo", it_f="serba", it_noun="serbo"),
    "gsw": dict(en="Swiss German", de_adj="schweizerdeutschen", de_pred="schweizerdeutsch", de_noun="Schweizerdeutsch", fr_m="suisse allemand", fr_f="suisse allemande", fr_noun="suisse allemand", it_m="svizzero tedesco", it_f="svizzera tedesca", it_noun="svizzero tedesco"),
}

UI_LANGUAGE_NAMES = {"en": "English", "de": "German", "fr": "French", "it": "Italian"}


def register(messages: dict[str, dict[str, str]]) -> None:
    """Add a check module's own strings (called at import time from c_<criterion>.py).
    Keys must be prefixed with the module's criterion, e.g. "c135." for 1.3.5; a key
    that already exists is an error, so two modules can never overwrite each other."""
    clash = sorted(set(messages) & set(MESSAGES))
    if clash:
        raise ValueError(f"i18n keys already registered: {clash}")
    MESSAGES.update(messages)


def t(key: str, lang: str, **kwargs: object) -> str:
    table = MESSAGES.get(key)
    if table is None:
        return key
    template = table.get(lang) or table.get("en") or key
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        return template


def primary_subtag(code: str | None) -> str:
    return (code or "").strip().lower().replace("_", "-").split("-")[0]


def lang_forms(code: str | None) -> dict[str, str]:
    """Grammatical forms for a language code; unknown codes are quoted as-is."""
    p = primary_subtag(code)
    forms = LANG_FORMS.get(p)
    if forms:
        return forms
    q = f"“{code}”"
    return dict(en=q, de_adj=q, de_pred=q, de_noun=q, fr_m=q, fr_f=q, fr_noun=q, it_m=q, it_f=q, it_noun=q)


def voice_sentence(actual: str, declared: str, ui_lang: str) -> str:
    """'Screen readers will read this French text with a German voice.' in the UI language."""
    a, d = lang_forms(actual), lang_forms(declared)
    if ui_lang == "de":
        return t("c312.impact", "de", actual=a["de_adj"], declared=d["de_adj"])
    if ui_lang == "fr":
        return t("c312.impact", "fr", actual=a["fr_m"], declared=d["fr_f"])
    if ui_lang == "it":
        return t("c312.impact", "it", actual=a["it_m"], declared=d["it_f"])
    return t("c312.impact", "en", actual=a["en"], declared=d["en"])


def lang_noun(code: str, ui_lang: str) -> str:
    """'French' / 'Französisch' / 'français' / 'francese' (used after 'in'/'auf'/'en')."""
    f = lang_forms(code)
    return {"de": f["de_noun"], "fr": f["fr_noun"], "it": f["it_noun"]}.get(ui_lang, f["en"])


def lang_kwargs(actual: str, declared: str | None, ui_lang: str) -> dict[str, str]:
    """All the placeholders used by the c312.* templates."""
    a = lang_forms(actual)
    d = lang_forms(declared or "")
    return {
        "actual": a["en"],
        "actual_pred": a["de_pred"],
        "actual_noun": lang_noun(actual, ui_lang),
        "actual_noun_en": a["en"],
        "declared": d["en"],
        "declared_like": {"de": d["de_adj"], "fr": d["fr_f"], "it": d["it_f"]}.get(ui_lang, d["en"]),
        "declared_code": declared or "",
        "code": actual,
    }
