"""3.3.2 Labels or Instructions -- 26 cases.

target = the control under test, or the container of a group of related controls
(radio group, split phone-number fields). Rules: protocol fragment 3.3.2.
"""
from __future__ import annotations

from common import *
from _forms_util import (field, select, fieldset, row, radios, contact_aside, form_case,
                         REQ_NOTE)

CRITERION = "3.3.2"


def _radios_bare(gid, name, options):
    """Radio buttons without fieldset/legend (only the option labels are visible)."""
    items = "".join(
        f'<span style="margin-right:18px"><input type="radio" id="{name}-{i + 1}" name="{name}" value="{esc(o)}"> '
        f'<label for="{name}-{i + 1}" style="display:inline;font-weight:400">{esc(o)}</label></span>'
        for i, o in enumerate(options))
    return f'<div class="fld" id="{gid}">{items}</div>'


def _req_legend(lang):
    return f'<p class="muted">{esc(REQ_NOTE[lang])}</p>'


def build(rng):
    cases = []

    def mk(*a, **k):
        k.setdefault("mode", "native")
        k.setdefault("novalidate", False)
        cases.append(form_case(rng, CRITERION, *a, **k))

    # =====================================================================
    # FAILED
    # =====================================================================
    mk("de", "Spitex Fiktal-Beispielwil", "Rückruf vereinbaren",
       "<p>Sie haben Fragen zu unseren Dienstleistungen oder zur Finanzierung? Wir rufen Sie gerne zurück.</p>",
       field("name", "Ihr Name", ac="name", err=False)
       + field("telefon", "", no_label=True, type="tel", ac="tel", ph="Telefonnummer",
               extra='aria-label="Telefonnummer"', err=False)
       + select("zeit", "Bevorzugte Zeit", ["Vormittag (8–12 Uhr)", "Nachmittag (13–17 Uhr)"], err=False)
       + field("anliegen", "Ihr Anliegen", textarea=True, rows=3, err=False),
       btn="Rückruf anfordern", fid="rueckruf", target="#telefon", expected="failed", rule="3.3.2/F1",
       notes="The phone field has only a placeholder 'Telefonnummer' (and an aria-label); the visible hint disappears as soon as the user types, while all other fields have visible labels.",
       difficulty="easy")

    mk("fr", "Bibliothèque de Bourg-Modèle", "Lettre d'information",
       "<p>Recevez chaque mois les nouveautés, les dates des lectures et les animations pour les enfants.</p>",
       '<div class="fld" style="display:flex;gap:8px;flex-wrap:wrap">'
       '<input id="infolettre" name="infolettre" type="email" autocomplete="email" placeholder="Votre adresse e-mail" '
       'aria-label="Adresse e-mail" required></div>',
       btn="S'abonner", fid="abonnement", target="#infolettre", expected="failed", rule="3.3.2/F1",
       notes="Single e-mail field identified only by the placeholder 'Votre adresse e-mail'; once typing starts nothing visible says what the field is (the button 'S'abonner' does not describe the input).",
       difficulty="medium")

    mk("it", "Città di Modellina", "Corso di italiano per adulti",
       "<p>Il corso serale (livello A2) si tiene il lunedì e il mercoledì dalle 19.00 alle 20.30 nelle aule delle scuole medie. Costo: CHF 180.– per semestre.</p>",
       '<div class="row"><div class="fld"><label for="nome">Nome</label>'
       '<input id="nome" name="nome" type="text" autocomplete="given-name"></div>'
       '<div class="fld" style="padding-top:1.6em"><input id="cognome" name="cognome" type="text" '
       'autocomplete="family-name" placeholder="Cognome"></div></div>'
       + field("email", "E-mail", type="email", ac="email", err=False)
       + select("livello", "Livello di conoscenza", ["Principiante", "A1", "A2"], err=False),
       btn="Iscriversi", fid="corso", target="#cognome", expected="failed", rule="3.3.2/F1",
       notes="The first-name input has a visible label 'Nome'; the surname input beside it is identified only by its placeholder 'Cognome', which vanishes on input.",
       difficulty="hard")

    mk("de", "Gemeinde Beispielwil", "Fundsache melden",
       "<p>Sie haben etwas gefunden? Geben Sie den Gegenstand bitte bei der Gemeindeverwaltung ab oder melden Sie ihn hier.</p>",
       field("gegenstand", "Was haben Sie gefunden?", err=False)
       + row(field("fundort", "Fundort", err=False), field("funddatum", "Funddatum", type="date", err=False))
       + field("finder", "Ihr Name", ac="name", err=False)
       + field("email", "E-Mail", type="email", ac="email", required=True, err=False),
       fid="fundsache", target="#email", expected="failed", rule="3.3.2/F2",
       notes="Only the e-mail field is required (required attribute) but nothing on the page indicates this; all other fields are optional and unmarked.",
       difficulty="medium")

    mk("fr", "Club sportif d'Exempleval", "Cours de jeunes sauveteurs",
       "<p>Le cours a lieu à la piscine couverte les samedis de mars. Âge minimum : 10 ans révolus au premier jour du cours.</p>",
       _req_legend("fr")
       + row(field("nom", "Nom", star=True, required=True, err=False), field("prenom", "Prénom", star=True, required=True, err=False))
       + field("naissance", "Date de naissance", type="date", required=True, err=False)
       + field("courriel", "Courriel", type="email", star=True, required=True, err=False)
       + field("remarques", "Remarques", textarea=True, rows=2, err=False),
       fid="sauveteurs", target="#naissance", expected="failed", rule="3.3.2/F2",
       notes="Required fields carry '*' explained by '* champ obligatoire', but the birth-date field is required (required attribute) without an asterisk, so it appears optional.",
       difficulty="hard")

    mk("de", "Gemeinde Beispielberg", "Anmeldung Seniorenausflug",
       "<p>Der diesjährige Ausflug führt am Donnerstag, 3. Juni 2027, an den Mustersee. Mitfahren können alle Einwohnerinnen und Einwohner ab 65 Jahren.</p>",
       row(field("vorname", "Vorname", ac="given-name", err=False), field("nachname", "Nachname", ac="family-name", err=False))
       + field("geburt", "Geburtsdatum", pattern=r"\d{4}-\d{2}-\d{2}", required=True, err=False)
       + field("telefon", "Telefon", type="tel", ac="tel", err=False)
       + radios("begleitung", "Kommt eine Begleitperson mit?", ["Ja", "Nein"]),
       fid="ausflug", target="#geburt", expected="failed", rule="3.3.2/F3",
       notes="The birth-date field only accepts the ISO pattern JJJJ-MM-TT (pattern attribute), unusual for Swiss users, but no format is stated anywhere.",
       difficulty="hard")

    mk("it", "Comune di Esempiano", "Iscrizione alla colonia estiva",
       "<p>La colonia estiva si svolge dal 5 al 16 luglio 2027 per i bambini dai 6 agli 11 anni. Posti limitati: fa fede la data d'iscrizione.</p>",
       row(field("bambino", "Nome e cognome del bambino", err=False), field("anni", "Età", im="numeric", size=4, err=False))
       + field("avs", "Numero AVS del bambino", pattern=r"756\.\d{4}\.\d{4}\.\d{2}", required=True, err=False)
       + field("genitore", "Telefono di un genitore", type="tel", err=False),
       fid="colonia", target="#avs", expected="failed", rule="3.3.2/F3",
       notes="The AVS field requires the dotted notation 756.0000.0000.00 (pattern attribute) but neither label nor hint states this format.",
       difficulty="medium")

    mk("fr", "Service des eaux d'Exempleval", "Passer à la facture électronique",
       "<p>Recevez votre facture d'eau par eBill ou par courriel. Vous trouverez votre numéro de client en haut à droite de la facture papier.</p>",
       field("client", "Numéro de client", im="numeric", pattern=r"\d{10}", required=True, err=False)
       + field("titulaire", "Nom du titulaire", ac="name", err=False)
       + field("courriel", "Courriel", type="email", ac="email", err=False),
       fid="efacture", target="#client", expected="failed", rule="3.3.2/F3",
       notes="The paper invoice prints the customer number in groups ('47 000 123 45'), but the field only accepts 10 digits without spaces; this rule is not stated.",
       difficulty="hard")

    mk("it", "Scuola di Esempiano", "Iscrizione al doposcuola",
       "<p>Il doposcuola accoglie gli allievi delle scuole elementari dalle 15.30 alle 18.00.</p>",
       row(field("allievo", "Nome dell'allievo", err=False), field("classe", "Classe", size=6, err=False))
       + _radios_bare("gruppo-uscita", "uscita", ["Sì", "No"])
       + '<fieldset><legend>Giorni di frequenza</legend>'
       + "".join(f'<div><input type="checkbox" id="g-{d}" name="giorni" value="{d}"> <label for="g-{d}" style="display:inline;font-weight:400">{d.capitalize()}</label></div>'
                 for d in ["lunedì", "martedì", "giovedì", "venerdì"])
       + "</fieldset>",
       fid="doposcuola", target="#gruppo-uscita", expected="failed", rule="3.3.2/F4",
       notes="Radio buttons 'Sì' / 'No' appear without any visible question or legend, so the user cannot know what is being asked (unlike the labelled checkbox group below).",
       difficulty="medium")

    mk("de", "Gemeinde Beispielwil", "Anmeldung Neuzuzügerapéro",
       "<p>Einmal im Jahr lädt der Gemeinderat alle neu zugezogenen Einwohnerinnen und Einwohner zu einem Apéro mit Dorfrundgang ein.</p>",
       row(field("name", "Name", ac="name", err=False), field("personen", "Anzahl Personen", im="numeric", size=4, err=False))
       + '<div class="fld" id="tel-gruppe">( <input id="tel-vw" name="tel-vw" type="tel" size="3" placeholder="032" title="Vorwahl"> ) '
         '<input id="tel-nr" name="tel-nr" type="tel" size="10" placeholder="000 12 34" title="Nummer"></div>'
       + field("mail", "E-Mail", type="email", ac="email", err=False),
       fid="apero", target="#tel-gruppe", expected="failed", rule="3.3.2/F5",
       notes="Two phone-number inputs are formatted only visually with brackets and placeholder digits; there is no text label saying that a phone number is expected (F82).",
       difficulty="medium")

    # =====================================================================
    # PASSED
    # =====================================================================
    mk("fr", "Commune de Valfictif", "Remboursement des frais de transport scolaire",
       "<p>Les frais de bus des élèves domiciliés à plus de 2,5 km du collège sont remboursés à la fin de l'année scolaire.</p>",
       field("eleve", "Nom et prénom de l'élève", err=False)
       + field("avs", "Numéro AVS de l'élève", hint="Format : 756.0000.0000.00", pattern=r"756\.\d{4}\.\d{4}\.\d{2}", err=False)
       + field("iban", "IBAN pour le remboursement", hint="P. ex. CH00 0000 0000 0000 0000 0", err=False),
       fid="transport", target="#avs", expected="passed", rule="3.3.2/P1",
       notes="Visible label plus the hint 'Format : 756.0000.0000.00' associated via aria-describedby.",
       difficulty="easy")

    mk("it", "Comune di Valfittizia", "Prenotazione della sala multiuso",
       "<p>La sala multiuso (150 posti) è a disposizione delle società locali e dei privati domiciliati nel comune.</p>",
       field("societa", "Società o nome del richiedente", err=False)
       + row(field("data", "Data dell'evento", hint="GG.MM.AAAA, ad es. 12.06.2027", pattern=r"\d{2}\.\d{2}\.\d{4}", hint_before=True, err=False),
             field("persone", "Numero di persone", im="numeric", size=5, err=False)),
       fid="sala", target="#data", expected="passed", rule="3.3.2/P1",
       notes="The date field has a visible label and a format hint 'GG.MM.AAAA, ad es. 12.06.2027' placed before the input and referenced by aria-describedby.",
       difficulty="easy")

    mk("de", "Gemeinde Fiktal", "E-Bike-Förderbeitrag beantragen",
       "<p>Die Gemeinde unterstützt den Kauf eines E-Bikes mit CHF 300.–. Der Beitrag wird auf Ihr Konto überwiesen.</p>",
       field("antragsteller", "Vorname und Name", ac="name", err=False)
       + field("iban", "IBAN", hint="Schweizer IBAN mit 21 Zeichen", ph="CH00 0000 0000 0000 0000 0", err=False)
       + field("beleg", "Nummer des Kaufbelegs", err=False),
       fid="ebike", target="#iban", expected="passed", rule="3.3.2/P1",
       notes="IBAN field with a visible label, a hint 'Schweizer IBAN mit 21 Zeichen' and an example format as placeholder.",
       difficulty="easy")

    mk("fr", "Commune d'Exempleval", "Abonnement aux déchets verts",
       "<p>Le ramassage des déchets verts a lieu chaque lundi d'avril à novembre. L'abonnement annuel coûte CHF 85.– par conteneur.</p>",
       field("abonne", "Nom et adresse", err=False)
       + radios("paiement", "Comment souhaitez-vous payer ?", ["Facture papier", "eBill", "Prélèvement automatique (LSV)"], gid="mode-paiement"),
       fid="dechets-verts", target="#mode-paiement", expected="passed", rule="3.3.2/P2",
       notes="Radio group inside a fieldset whose legend asks 'Comment souhaitez-vous payer ?'.",
       difficulty="easy")

    mk("it", "Città di Modellina", "Iscrizione alla mensa scolastica",
       "<p>I pasti sono preparati ogni giorno nella cucina della scuola con prodotti della regione.</p>",
       row(field("allievo", "Nome dell'allievo", err=False), field("classe", "Classe", size=6, err=False))
       + radios("allergie", "Il bambino ha allergie o intolleranze alimentari?", ["Sì", "No"], gid="gruppo-allergie")
       + field("dettagli", "Se sì, quali?", textarea=True, rows=2, err=False),
       fid="mensa", target="#gruppo-allergie", expected="passed", rule="3.3.2/P2",
       notes="The 'Sì / No' radios are grouped by a legend stating the question about food allergies (same options as a radio group without question).",
       difficulty="easy")

    # Traps
    mk("de", "Bibliothek Mustersee", "Katalog",
       "<p>Über 28 000 Bücher, Hörbücher, Filme und Zeitschriften – und alles kostenlos für Kinder und Jugendliche.</p>",
       '<div class="fld" style="display:flex;gap:8px;flex-wrap:wrap">'
       '<input id="q" name="q" type="search" aria-labelledby="suche-btn" size="32">'
       '<button type="submit" id="suche-btn">Suchen</button></div>',
       buttons="", fid="katalogsuche", target="#q", expected="passed", rule="3.3.2/T1", trap=True,
       notes="The search field has no label element, but the adjacent 'Suchen' button labels its purpose (G167, aria-labelledby).",
       difficulty="medium")

    mk("fr", "Commune de Valfictif", "Annonce d'un chien",
       "<p>Chaque chien doit être annoncé à la commune dans les dix jours suivant son arrivée.</p>",
       _req_legend("fr")
       + row(field("detenteur", "Nom du détenteur", star=True, required=True, err=False), field("chien", "Nom du chien", star=True, required=True, err=False))
       + field("puce", "Numéro de puce électronique", star=True, required=True, im="numeric",
               hint="15 chiffres, voir le passeport pour animaux de compagnie.", err=False)
       + field("race", "Race", err=False),
       fid="annonce-chien", target="#puce", expected="passed", rule="3.3.2/T2", trap=True,
       notes="The microchip field is marked with '*', and the asterisk is explained by '* champ obligatoire' at the top of the form (H90).",
       difficulty="medium")

    mk("it", "Biblioteca di Modellina", "Newsletter",
       "<p>Una volta al mese le novità in biblioteca, le letture per bambini e gli incontri con gli autori.</p>",
       field("posta", "Indirizzo e-mail", type="email", ac="email", required=True, err=False),
       btn="Iscriviti", fid="newsletter", target="#posta", expected="passed", rule="3.3.2/T3", trap=True,
       notes="Single-field newsletter form with a clear visible label; no 'required' marker is needed for the only field.",
       difficulty="medium")

    mk("de", "Gemeinde Ober-Beispielwil", "Sperrgut-Abholung auf Abruf",
       "<p>Sperrgut holen wir gegen eine Gebühr von CHF 40.– pro Kubikmeter direkt bei Ihnen zu Hause ab.</p>",
       field("adresse", "Abholadresse", ac="street-address", ph="z. B. Kirchweg 3", err=False)
       + field("gegenstaende", "Was sollen wir abholen?", textarea=True, rows=3, err=False)
       + field("termin", "Wunschtermin", type="date", err=False),
       fid="sperrgut", target="#termin", expected="passed", rule="3.3.2/T4", trap=True,
       notes="Native date input without textual format hint: the browser shows its own localized date mask and picker, so no author-defined format has to be stated.",
       difficulty="hard")

    sizes = [("17", "10.–"), ("35", "20.–"), ("60", "34.–"), ("110", "60.–")]
    table = ('<table><caption>Sacchi tassati (rotoli da 10 sacchi)</caption>'
             '<tr><th id="col-formato">Formato</th><th id="col-prezzo">Prezzo per rotolo</th><th id="col-rotoli">Numero di rotoli</th></tr>'
             + "".join(f'<tr><th id="riga-{s}">{s} litri</th><td>CHF {p}</td><td><input id="rotoli-{s}" name="rotoli-{s}" '
                       f'type="number" min="0" max="10" size="3" aria-labelledby="col-rotoli riga-{s}"></td></tr>'
                       for s, p in sizes)
             + "</table>")
    mk("it", "Comune di Esempiano", "Ordinazione di sacchi tassati",
       "<p>I sacchi vengono consegnati a domicilio con fattura. Ordinazione minima: un rotolo.</p>",
       table + field("cliente", "Nome e indirizzo", err=False),
       fid="ordine-sacchi", target="#rotoli-35", expected="passed", rule="3.3.2/T5", trap=True,
       notes="The quantity inputs have no label elements, but each is labelled by the visible row and column headers ('Numero di rotoli', '35 litri') via aria-labelledby.",
       difficulty="hard")

    mk("fr", "Ville de Bourg-Modèle", "Prendre rendez-vous au contrôle des habitants",
       "<p>Pour un passeport, une carte d'identité ou une attestation, réservez un créneau. Nous vous confirmons le rendez-vous par téléphone.</p>",
       field("personne", "Nom et prénom", ac="name", err=False)
       + field("tel", "Téléphone", type="tel", ac="tel", ph="p. ex. 032 000 12 34", err=False)
       + select("motif", "Motif du rendez-vous", ["Carte d'identité", "Passeport", "Attestation de domicile", "Autre"], err=False),
       fid="rendez-vous", target="#tel", expected="passed", rule="3.3.2/T6", trap=True,
       notes="The phone field has a visible label 'Téléphone'; its placeholder is only an additional example.",
       difficulty="medium")

    mk("de", "Gemeinde Fiktal", "Gesuch um Benützung der Turnhalle",
       "<p>Vereine und Gruppen aus Fiktal können die Turnhalle ausserhalb der Schulzeiten mieten.</p>",
       '<p><strong>Alle Felder sind Pflichtfelder.</strong></p>'
       + field("gruppe", "Verein oder Gruppe", required=True, err=False)
       + row(field("verantwortlich", "Verantwortliche Person", required=True, err=False),
             field("tel", "Telefon", type="tel", required=True, err=False))
       + select("wochentag", "Gewünschter Wochentag", ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"], err=False, required=True),
       fid="turnhalle", target="#verantwortlich", expected="passed", rule="3.3.2/T7", trap=True,
       notes="No asterisks, but the instruction 'Alle Felder sind Pflichtfelder.' at the start of the form tells users every field is required (G184).",
       difficulty="medium")

    # =====================================================================
    # CANTTELL
    # =====================================================================
    mk("de", "Gemeinde Beispielberg", "Infoabend der Feuerwehr",
       "<p>Die Feuerwehr Beispielberg sucht Verstärkung. Am Infoabend stellen wir den Feuerwehrdienst vor – mit Übung und Wurst vom Grill.</p>",
       row(field("vn", "Vorname", ac="given-name", err=False), field("nn", "Nachname", ac="family-name", err=False))
       + field("telefon", "Telefon", err=False)
       + field("jahrgang", "Jahrgang", im="numeric", size=6, err=False),
       mode="none", action="/feuerwehr/infoabend",
       fid="infoabend", target="#telefon", expected="cantTell", rule="3.3.2/C1",
       notes="Free-text 'Telefon' field without format hint; there is no pattern or script and the form posts to the server, so whether a specific format is required (and must be stated) cannot be told.",
       difficulty="medium")

    mk("fr", "Commune de Valfictif", "Changement de détenteur d'un chien",
       "<p>Le nouveau détenteur doit annoncer le chien dans les dix jours. Munissez-vous du passeport du chien : il contient le numéro de puce électronique et le numéro de la médaille communale.</p>",
       field("nouveau", "Nouveau détenteur", ac="name", err=False)
       + field("numero", "Numéro", err=False)
       + field("date", "Date de la remise", type="date", err=False),
       fid="detenteur", target="#numero", expected="cantTell", rule="3.3.2/C2",
       notes="The field is labelled only 'Numéro' while the page mentions both the microchip number and the tag number; whether the label is a sufficient instruction depends on what users already know.",
       difficulty="hard")

    phone = asset("pic-phone-label", pictogram("phone", color="#1d2327", size=22))
    mk("it", "Ente turistico Valfittizia", "Richiesta di informazioni",
       "<p>Vi aiutiamo a pianificare il vostro soggiorno in valle: alloggi, escursioni e trasporti.</p>",
       field("nome", "Nome e cognome", ac="name", err=False)
       + field("email", "E-mail", type="email", ac="email", err=False)
       + field("telefono", "", type="tel", ac="tel", err=False,
               label_html=f'<img src="{phone}" alt="Telefono" width="22" height="22">')
       + field("richiesta", "La vostra richiesta", textarea=True, rows=4, err=False),
       fid="informazioni", target="#telefono", expected="cantTell", rule="3.3.2/C3",
       notes="The phone field's only visible label is a telephone pictogram (alt 'Telefono'); whether this icon is widely understood by the target audience cannot be decided from the page.",
       difficulty="hard")

    mk("it", "Città di Modellina", "Rinnovo dell'autorizzazione di parcheggio",
       "<p>Sulla fattura dell'anno scorso trova sia il codice cliente sia il codice dell'autorizzazione. Il rinnovo vale dodici mesi.</p>",
       field("titolare", "Titolare", ac="name", err=False)
       + field("codice", "Codice", err=False)
       + field("targa", "Targa del veicolo", err=False),
       fid="rinnovo", target="#codice", expected="cantTell", rule="3.3.2/C2",
       notes="The label 'Codice' is ambiguous because the page mentions two codes (customer code and permit code); sufficiency of the label cannot be decided from the page.",
       difficulty="hard")

    return shuffled(rng, cases)
