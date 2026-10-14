"""3.3.1 Error Identification -- 26 cases, target = the form field under test.

Labels describe the state after submitting the form with the invalid value given in
``notes`` (all other fields valid). Rules: protocol fragment 3.3.1.
"""
from __future__ import annotations

from common import *
from _forms_util import (FORM_CSS, BTN, THANKS, field, select, fieldset, row, okbox, actions,
                         js_validate, js_done_only, compose, contact_aside)

CRITERION = "3.3.1"

# JS boolean expressions on the trimmed value v
PLZ = r"/^\d{4}$/.test(v)"
EMAIL = r"/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(v)"
AHV = r"/^756\.\d{4}\.\d{4}\.\d{2}$/.test(v)"
DATE = (r"(function(){var m=/^(\d{2})\.(\d{2})\.(\d{4})$/.exec(v);if(!m){return false;}"
        r"var d=new Date(+m[3],+m[2]-1,+m[1]);return d.getDate()===+m[1]&&d.getMonth()===+m[2]-1;})()")
FILLED = 'v !== ""'
PLATE = r"/^[A-Z]{2} ?\d{1,6}$/.test(v.toUpperCase())"
PHONE = r"/^(0|\+41 ?)\d{2} ?\d{3} ?\d{2} ?\d{2}$/.test(v)"


def digits(n):
    return r"/^\d{%d}$/.test(v)" % n


def rng_int(a, b):
    return r"/^\d+$/.test(v) && +v >= %d && +v <= %d" % (a, b)


DONE_ID = {"de": "danke", "fr": "merci", "it": "grazie"}
WARN_SVG = ('<svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
            '<path d="M12 3l10 18H2z" fill="#c8102e"/><path d="M12 10v5M12 18v.5" stroke="#ffffff" '
            'stroke-width="2.4" stroke-linecap="round"/></svg>')


def build(rng):
    cases = []

    def mk(lang, org, h1, intro, inner, rules, *, fid, target, expected, rule, notes, trap=False,
           difficulty="medium", alt=None, aside=None, novalidate=True, action=None, top="", bottom="",
           btn=None, summary=None, dialog=None, native=False, script=True, extra_after=""):
        done = DONE_ID[lang]
        nv = " novalidate" if novalidate else ""
        act = f' action="{action}" method="post"' if action else ""
        form = (f'<form id="{fid}"{act}{nv}>{top}{inner}{bottom}{actions(btn or BTN[lang])}</form>'
                + (okbox(lang, oid=done) if script else "") + extra_after)
        body = compose(rng, lang, org, h1, form, intro=intro, aside=aside)
        if script:
            body += "\n" + (js_done_only(fid, done) if native else
                            js_validate(fid, rules, done_id=done, summary=summary, dialog=dialog))
        tag = pick(rng, [SITE_LANG_TAG[lang], lang])
        html = page(tag, f"{h1} – {org}", body, rng=rng, css=FORM_CSS)
        cases.append(Case(CRITERION, lang, expected, html=html, target=target, rule=rule, notes=notes,
                          trap=trap, alt_expected=alt, difficulty=difficulty))

    # =====================================================================
    # FAILED
    # =====================================================================
    # F1 de -- generic box at the top, field not marked
    mk("de", "Gemeinde Beispielwil", "Ersatz-Hundemarke bestellen",
       "<p>Haben Sie die Hundemarke Ihres Hundes verloren? Eine Ersatzmarke kostet CHF 10.– und wird Ihnen per Post zugestellt.</p>",
       field("halter", "Name der Halterin / des Halters", ac="name", err=False)
       + field("hundename", "Name des Hundes", err=False)
       + field("marke", "Nummer der bisherigen Hundemarke", im="numeric",
               hint="Sie finden die Nummer auf der letzten Rechnung der Hundetaxe.")
       + field("bemerkung", "Bemerkungen", textarea=True, rows=3, err=False),
       [dict(f="marke", t=digits(5), m="Bitte überprüfen Sie Ihre Angaben.", o="text", x="formmsg", mk=False)],
       top='<p class="msgbox" id="formmsg" role="alert" hidden></p>',
       fid="ersatzmarke", target="#marke", expected="failed", rule="3.3.1/F1",
       notes="After submitting tag number '4172' (5 digits required) only the generic box 'Bitte überprüfen Sie Ihre Angaben.' appears; neither the field nor the problem is identified.",
       difficulty="easy",
       aside=contact_aside("de", "Einwohnerkontrolle Beispielwil", "032 000 12 34", "einwohner@beispielwil.example"))

    # F1 fr -- generic message near the button, other field (NPA) has a proper message
    mk("fr", "Commune d'Exempleval", "Macaron de stationnement pour résidents",
       "<p>Les résidents des zones bleues peuvent obtenir un macaron annuel au prix de CHF 240.–. Un seul macaron est délivré par véhicule.</p>",
       row(field("nom", "Nom", ac="family-name", err=False), field("prenom", "Prénom", ac="given-name", err=False))
       + row(field("npa", "NPA", im="numeric", ac="postal-code"), field("localite", "Localité", err=False))
       + field("plaque", "Numéro d'immatriculation", hint="Tel qu'il figure sur le permis de circulation."),
       [dict(f="npa", t=PLZ, m="Le NPA doit comporter 4 chiffres, par exemple 2000."),
        dict(f="plaque", t=PLATE, m="Une erreur s'est produite. Veuillez vérifier le formulaire.", o="text",
             x="msg-envoi", mk=False)],
       bottom='<p class="msgbox" id="msg-envoi" hidden></p>',
       fid="macaron", target="#plaque", expected="failed", rule="3.3.1/F1",
       notes="Submitting plate 'VD-12A45' only shows 'Une erreur s'est produite. Veuillez vérifier le formulaire.' near the button; the plate field is not named, marked or described (the NPA field, by contrast, has a full message).",
       difficulty="medium")

    # F2 it -- colour only (birth date)
    mk("it", "Comune di Esempiano", "Iscrizione al corso di nuoto per bambini",
       "<p>Il corso si svolge il mercoledì pomeriggio presso la piscina comunale, dal 4 novembre al 16 dicembre. Costo: CHF 90.– per sette lezioni.</p>",
       row(field("nome", "Nome del bambino", ac="off"), field("cognome", "Cognome", ac="off"))
       + field("nascita", "Data di nascita", err=False)
       + field("telefono", "Telefono di un genitore", type="tel", ac="tel", err=False),
       [dict(f="nome", t=FILLED, m="Inserisca il nome del bambino."),
        dict(f="cognome", t=FILLED, m="Inserisca il cognome del bambino."),
        dict(f="nascita", t=DATE, o="none")],
       fid="corso-nuoto", target="#nascita", expected="failed", rule="3.3.1/F2",
       notes="After submitting '2018-03-05' the birth-date field only gets a red border and background; no text describes the error, while name fields get text messages.",
       difficulty="medium")

    # F2 de -- colour + aria-invalid only (meter number)
    mk("de", "Wasserversorgung Fiktal", "Zählerstand online melden",
       "<p>Melden Sie uns den Stand Ihres Wasserzählers bis 31. Dezember 2026. Sie finden Kunden- und Zählernummer auf der letzten Rechnung.</p>",
       field("kunde", "Kundennummer", im="numeric")
       + field("zaehler", "Zählernummer", err=False)
       + row(field("stand", "Zählerstand in m³", im="numeric"), field("ablesung", "Ablesedatum", type="date", err=False)),
       [dict(f="kunde", t=digits(8), m="Die Kundennummer besteht aus 8 Ziffern (oben rechts auf der Rechnung)."),
        dict(f="zaehler", t=digits(7), o="none"),
        dict(f="stand", t=r"/^\d{1,6}$/.test(v)", m="Bitte den Zählerstand in ganzen m³ ohne Kommastellen eingeben.")],
       fid="zaehlerstand", target="#zaehler", expected="failed", rule="3.3.1/F2",
       notes="Submitting meter number '88412A' only sets aria-invalid and a red border on the field; no text anywhere says what is wrong.",
       difficulty="hard")

    # F3 fr -- icon only (NPA)
    mk("fr", "École de Valfictif", "Inscription à l'accueil parascolaire",
       "<p>L'accueil parascolaire est ouvert les jours d'école de 7 h à 18 h 30. Les inscriptions pour le second semestre doivent nous parvenir avant le 15 janvier.</p>",
       row(field("enfant", "Nom et prénom de l'enfant", err=False), select("classe", "Classe", ["1H", "2H", "3H", "4H", "5H", "6H", "7H", "8H"], err=False))
       + row(field("npa", "NPA du domicile", im="numeric", icon_slot=WARN_SVG), field("localite", "Localité", err=False))
       + field("courriel", "Courriel des parents", type="email", ac="email"),
       [dict(f="npa", t=PLZ, o="show"),
        dict(f="courriel", t=EMAIL, m="Adresse e-mail incomplète : indiquez-la au format nom@exemple.example.")],
       fid="parascolaire", target="#npa", expected="failed", rule="3.3.1/F3",
       notes="After submitting NPA '17000' the field only gets a red border and a red warning triangle (aria-hidden SVG); no text describes the error.",
       difficulty="medium")

    # F3 it -- icon img with empty alt (customer number)
    warn = asset("pic-warning-red", pictogram("warning", color="#c8102e", size=20, stroke=2.4))
    mk("it", "Comune di Valfittizia", "Ordinazione di sacchi tassati",
       "<p>I sacchi tassati possono essere ordinati online e vengono consegnati a domicilio entro cinque giorni lavorativi.</p>",
       field("cliente", "Numero cliente", im="numeric", icon_slot=f'<img src="{warn}" alt="" width="20" height="20">',
             hint="Lo trova sulla fattura della tassa base.")
       + select("formato", "Formato dei sacchi", ["17 litri", "35 litri", "60 litri", "110 litri"], err=False)
       + field("rotoli", "Quantità (rotoli da 10 sacchi)", im="numeric"),
       [dict(f="cliente", t=digits(6), o="show"),
        dict(f="rotoli", t=rng_int(1, 10), m="Indichi una quantità tra 1 e 10 rotoli.")],
       fid="sacchi", target="#cliente", expected="failed", rule="3.3.1/F3",
       notes="Submitting customer number '12-345' only adds a red border and a warning icon with empty alt next to the field; no text describes the error.",
       difficulty="medium")

    # F4 de -- 'Ungültige Eingabe' (no cause)
    mk("de", "Gemeinde Beispielberg", "Kehrichtmarken bestellen",
       "<p>Kehrichtmarken für 35-Liter-Säcke werden in Bogen zu 10 Stück verkauft (CHF 25.– pro Bogen). Die Lieferung erfolgt mit Rechnung.</p>",
       field("name", "Vorname und Name", ac="name", err=False)
       + field("adresse", "Strasse und Hausnummer", ac="street-address", err=False)
       + field("bogen", "Anzahl Bogen", im="numeric", size=4)
       + field("mail", "E-Mail für die Bestätigung", type="email", ac="email"),
       [dict(f="bogen", t=rng_int(1, 20), m="Ungültige Eingabe"),
        dict(f="mail", t=EMAIL, m="Bitte geben Sie eine E-Mail-Adresse im Format name@beispiel.example ein.")],
       fid="marken", target="#bogen", expected="failed", rule="3.3.1/F4",
       notes="Ordering '50' sheets (max. 20) shows 'Ungültige Eingabe' under the field: it says something is wrong but not what (cause/limit not described).",
       difficulty="medium")

    # F4 fr -- 'Erreur' (AHV number)
    mk("fr", "Commune de Valfictif", "Demande d'attestation de domicile",
       "<p>L'attestation de domicile coûte CHF 20.– et vous est envoyée par courrier dans les trois jours ouvrables.</p>",
       row(field("nom", "Nom", ac="family-name"), field("prenom", "Prénom", ac="given-name"))
       + field("naissance", "Date de naissance", hint="JJ.MM.AAAA")
       + field("avs", "Numéro AVS")
       + select("exemplaires", "Nombre d'exemplaires", ["1", "2", "3"], err=False),
       [dict(f="nom", t=FILLED, m="Veuillez indiquer votre nom."),
        dict(f="prenom", t=FILLED, m="Veuillez indiquer votre prénom."),
        dict(f="naissance", t=DATE, m="Date de naissance : utilisez le format JJ.MM.AAAA, p. ex. 07.04.1985."),
        dict(f="avs", t=AHV, m="Erreur")],
       fid="attestation", target="#avs", expected="failed", rule="3.3.1/F4",
       notes="Submitting AVS number '756.1234.5678' shows only 'Erreur' under the field; the cause (13 digits, 756.0000.0000.00) is not described.",
       difficulty="easy")

    # F4 it -- 'Campo non valido' (start date)
    mk("it", "Trasporti pubblici di Modellina", "Richiesta di abbonamento annuale",
       "<p>L'abbonamento annuale è valido su tutte le linee urbane. Il prezzo per adulti è di CHF 590.–, per giovani fino a 25 anni di CHF 390.–.</p>",
       row(field("nome", "Nome", ac="given-name"), field("cognome", "Cognome", ac="family-name"))
       + field("inizio", "Inizio della validità")
       + field("email", "E-mail", type="email", ac="email"),
       [dict(f="nome", t=FILLED, m="Inserisca il nome."),
        dict(f="cognome", t=FILLED, m="Inserisca il cognome."),
        dict(f="inizio", t=DATE, m="Campo non valido"),
        dict(f="email", t=EMAIL, m="Indirizzo e-mail incompleto: usi il formato nome@esempio.example.")],
       fid="abbonamento", target="#inizio", expected="failed", rule="3.3.1/F4",
       notes="Entering '1 dicembre' as start date shows 'Campo non valido': the message neither explains the cause nor the expected date format.",
       difficulty="medium")

    # F5 de -- text only in a visually hidden container
    mk("de", "Stadt Mustersee", "Parkkarte für Anwohnende beantragen",
       "<p>Mit der Anwohnerparkkarte parkieren Sie in der blauen Zone Ihres Quartiers ohne Zeitbeschränkung. Gebühr: CHF 40.– pro Monat.</p>",
       row(field("vorname", "Vorname", ac="given-name"), field("nachname", "Nachname", ac="family-name"))
       + field("schild", "Kontrollschild", err_hidden_cls="visually-hidden")
       + field("email", "E-Mail", type="email", ac="email"),
       [dict(f="vorname", t=FILLED, m="Bitte geben Sie Ihren Vornamen ein."),
        dict(f="nachname", t=FILLED, m="Bitte geben Sie Ihren Nachnamen ein."),
        dict(f="schild", t=PLATE, m="Kontrollschild: Bitte Kantonskürzel und Nummer eingeben, z. B. BE 123456."),
        dict(f="email", t=EMAIL, m="Bitte geben Sie eine gültige E-Mail-Adresse ein, z. B. name@beispiel.example.")],
       fid="parkkarte", target="#schild", expected="failed", rule="3.3.1/F5",
       notes="For plate '12345' the descriptive text is written into a visually-hidden container; sighted users only see a red border on the field.",
       difficulty="hard")

    # =====================================================================
    # PASSED
    # =====================================================================
    # P1 it -- inline text, aria-describedby
    mk("it", "Scuola di Esempiano", "Iscrizione alla scuola dell'infanzia",
       "<p>Le iscrizioni per l'anno scolastico 2027/2028 sono aperte fino al 29 gennaio 2027.</p>",
       fieldset("Dati del bambino",
                row(field("nome", "Nome", ac="off"), field("cognome", "Cognome", ac="off"))
                + field("nascita", "Data di nascita")
                + field("lingua", "Lingua parlata a casa", err=False))
       + field("email", "E-mail dei genitori", type="email", ac="email"),
       [dict(f="nome", t=FILLED, m="Inserisca il nome del bambino."),
        dict(f="cognome", t=FILLED, m="Inserisca il cognome del bambino."),
        dict(f="nascita", t=DATE, m="Data di nascita: inserisca la data nel formato GG.MM.AAAA, ad es. 05.03.2022."),
        dict(f="email", t=EMAIL, m="E-mail: inserisca un indirizzo completo, ad es. nome@esempio.example.")],
       fid="iscrizione", target="#nascita", expected="passed", rule="3.3.1/P1",
       notes="Submitting '5 marzo 2022' shows a visible text naming the field and the expected format, linked with aria-describedby and aria-invalid.",
       difficulty="easy")

    # P1 fr -- inline text in aria-live container
    mk("fr", "Ville de Bourg-Modèle", "Annonce d'arrivée",
       "<p>Vous venez de vous installer à Bourg-Modèle ? Annoncez votre arrivée dans les 14 jours. Munissez-vous ensuite de votre pièce d'identité pour passer au guichet.</p>",
       row(field("nom", "Nom", ac="family-name", err_live="polite"), field("prenom", "Prénom", ac="given-name", err_live="polite"))
       + field("avs", "Numéro AVS", hint="Il figure au dos de votre carte d'assurance-maladie.", err_live="polite")
       + field("arrivee", "Date d'arrivée", hint="JJ.MM.AAAA", err_live="polite")
       + field("ancienne", "Ancienne adresse", ac="off", err=False),
       [dict(f="nom", t=FILLED, m="Veuillez indiquer votre nom."),
        dict(f="prenom", t=FILLED, m="Veuillez indiquer votre prénom."),
        dict(f="avs", t=AHV, m="Le numéro AVS doit comporter 13 chiffres au format 756.0000.0000.00."),
        dict(f="arrivee", t=DATE, m="Date d'arrivée : utilisez le format JJ.MM.AAAA.")],
       fid="arrivee-form", target="#avs", expected="passed", rule="3.3.1/P1",
       notes="Submitting AVS number '7561234567' displays 'Le numéro AVS doit comporter 13 chiffres…' below the field in a polite live region, associated with the input.",
       difficulty="easy",
       aside=contact_aside("fr", "Contrôle des habitants", "032 000 21 00", "habitants@bourg-modele.example"))

    # P2 de -- summary with links
    mk("de", "Gemeinde Fiktal", "Anmeldung Ferienpass 2027",
       "<p>Der Ferienpass bietet in der ersten Sommerferienwoche über 40 Kurse für Kinder von 6 bis 14 Jahren. Die Anmeldung ist bis 31. März 2027 möglich.</p>",
       fieldset("Angaben zum Kind",
                row(field("kvorname", "Vorname des Kindes", err=False), field("kname", "Name des Kindes", err=False))
                + field("geburt", "Geburtsdatum des Kindes", err=False))
       + fieldset("Kontakt der Eltern",
                  field("elternmail", "E-Mail-Adresse", type="email", ac="email", err=False)
                  + field("notfall", "Telefon für Notfälle", type="tel", ac="tel", err=False)),
       [dict(f="kvorname", t=FILLED, m="Vorname des Kindes: Bitte ausfüllen.", o="list", ln=True),
        dict(f="kname", t=FILLED, m="Name des Kindes: Bitte ausfüllen.", o="list", ln=True),
        dict(f="geburt", t=DATE, m="Geburtsdatum des Kindes: Bitte im Format TT.MM.JJJJ eingeben, z. B. 03.05.2016.", o="list", ln=True),
        dict(f="elternmail", t=EMAIL, m="E-Mail-Adresse: Es fehlt das @-Zeichen oder die Domain.", o="list", ln=True),
        dict(f="notfall", t=PHONE, m="Telefon für Notfälle: Bitte mit Vorwahl eingeben, z. B. 032 000 12 34.", o="list", ln=True)],
       top=('<div class="msgbox" id="fehlerbox" tabindex="-1" hidden><p><strong>Bitte korrigieren Sie folgende Angaben:</strong></p>'
            '<ul id="fehlerliste"></ul></div>'),
       summary=dict(box="fehlerbox", list="fehlerliste"),
       fid="ferienpass", target="#geburt", expected="passed", rule="3.3.1/P2",
       notes="Submitting '3.5.16' opens an error summary at the top with a link 'Geburtsdatum des Kindes: Bitte im Format TT.MM.JJJJ eingeben…' that names the field and the problem.",
       difficulty="easy")

    # P2 fr -- summary with links, real date check
    mk("fr", "Commune de Valfictif", "Réservation de la salle communale",
       "<p>La salle communale (120 places) peut être louée par les sociétés locales et les particuliers domiciliés dans la commune.</p>",
       field("organisateur", "Nom ou société", err=False)
       + row(field("date", "Date souhaitée", err=False, hint="JJ.MM.AAAA"), field("personnes", "Nombre de personnes", im="numeric", err=False))
       + field("courriel", "Courriel", type="email", ac="email", err=False),
       [dict(f="organisateur", t=FILLED, m="Nom ou société : ce champ est obligatoire.", o="list", ln=True),
        dict(f="date", t=DATE, m="Date souhaitée : cette date n'existe pas ou n'est pas au format JJ.MM.AAAA.", o="list", ln=True),
        dict(f="personnes", t=rng_int(1, 120), m="Nombre de personnes : indiquez un nombre entre 1 et 120.", o="list", ln=True),
        dict(f="courriel", t=EMAIL, m="Courriel : l'adresse doit contenir un @ et un domaine, p. ex. nom@exemple.example.", o="list", ln=True)],
       top=('<div class="msgbox" id="erreurs" tabindex="-1" hidden><h2>Le formulaire contient des erreurs</h2>'
            '<ul id="erreurs-liste"></ul></div>'),
       summary=dict(box="erreurs", list="erreurs-liste"),
       fid="salle", target="#date", expected="passed", rule="3.3.1/P2",
       notes="Submitting the non-existent date '31.11.2026' lists 'Date souhaitée : cette date n'existe pas…' as a link to the field in the error summary.",
       difficulty="medium")

    # P3 it -- role=alert next to the field
    mk("it", "Città di Modellina", "Segnalare un guasto all'illuminazione pubblica",
       "<p>Un lampione è spento o lampeggia? Ci indichi il luogo preciso: la squadra dell'ufficio tecnico interviene di regola entro tre giorni lavorativi.</p>",
       field("luogo", "Luogo del guasto", hint="Via e numero civico più vicino, oppure numero del palo.", err=False)
       + field("descrizione", "Descrizione", textarea=True, rows=3, err=False)
       + field("email", "E-mail per la conferma", type="email", ac="email", err_live="alert"),
       [dict(f="email", t=EMAIL, m="E-mail per la conferma: l'indirizzo non è valido, manca il simbolo @ o il dominio (es. nome@esempio.example).")],
       fid="guasto", target="#email", expected="passed", rule="3.3.1/P3",
       notes="Submitting 'lucia.esempio.example' writes a message naming the field and the missing @ into a role=alert container under the field.",
       difficulty="easy")

    # T1 de -- very short but complete
    mk("de", "Beispielwiler Verkehrsbetriebe", "Veloabstellplatz am Bahnhof mieten",
       "<p>In der Velostation am Bahnhof Beispielwil vermieten wir gedeckte Abstellplätze für CHF 15.– pro Monat. Die Badge erhalten Sie per Post.</p>",
       field("name", "Vorname und Name", ac="name")
       + row(field("plz", "PLZ", im="numeric", ac="postal-code", size=6), field("ort", "Ort", ac="address-level2"))
       + select("dauer", "Mietdauer", ["1 Monat", "3 Monate", "12 Monate"], err=False),
       [dict(f="name", t=FILLED, m="Name fehlt"),
        dict(f="plz", t=FILLED, m="PLZ fehlt"),
        dict(f="ort", t=FILLED, m="Ort fehlt")],
       fid="velo", target="#plz", expected="passed", rule="3.3.1/T1", trap=True,
       notes="Submitting with the PLZ left empty shows 'PLZ fehlt' under the field: terse, but it identifies the field and the problem (missing value).",
       difficulty="medium")

    # T1 fr -- short message with the rule
    mk("fr", "Club sportif d'Exempleval", "Inscription au tournoi de unihockey",
       "<p>Le tournoi populaire a lieu le samedi 30 janvier 2027 à la salle de sport. Équipes de 5 joueurs, inscription CHF 50.– par équipe.</p>",
       field("equipe", "Nom de l'équipe")
       + field("capitaine", "Capitaine (nom et prénom)")
       + row(field("npa", "NPA", im="numeric", size=6), field("courriel", "Courriel", type="email"))
       ,
       [dict(f="equipe", t=FILLED, m="Nom d'équipe manquant"),
        dict(f="capitaine", t=FILLED, m="Capitaine manquant"),
        dict(f="npa", t=PLZ, m="NPA : 4 chiffres"),
        dict(f="courriel", t=EMAIL, m="Courriel incomplet (@ manquant)")],
       fid="tournoi", target="#npa", expected="passed", rule="3.3.1/T1", trap=True,
       notes="Submitting NPA '170' shows 'NPA : 4 chiffres' next to the field; short but it names the field and the rule.",
       difficulty="medium")

    # T2 de -- native validation (type=email required), no custom check
    mk("de", "Bibliothek Mustersee", "Newsletter der Bibliothek",
       "<p>Einmal im Monat informieren wir über Neuheiten, Lesungen und Veranstaltungen für Kinder. Sie können sich jederzeit wieder abmelden.</p>",
       field("adresse", "E-Mail-Adresse", type="email", ac="email", required=True, err=False),
       [], native=True, novalidate=False, btn="Abonnieren",
       fid="newsletter", target="#adresse", expected="passed", rule="3.3.1/T2", trap=True,
       notes="With 'lea.testmann.example' the browser's constraint validation (type=email, required) blocks submission and shows its own text bubble explaining the missing @.",
       difficulty="hard")

    # T2 it -- native pattern + title
    mk("it", "Comune di Esempiano", "Richiesta di posteggio per un trasloco",
       "<p>Per un trasloco può riservare fino a due posteggi pubblici davanti alla sua abitazione. La tassa è di CHF 30.– al giorno.</p>",
       row(field("nome", "Nome e cognome", ac="name", required=True, err=False),
           field("via", "Via e numero", ac="street-address", required=True, err=False))
       + row(field("cap", "NPA", im="numeric", required=True, pattern="[0-9]{4}", title="4 cifre, ad es. 6900", err=False),
             field("giorno", "Giorno del trasloco", type="date", required=True, err=False)),
       [], native=True, novalidate=False,
       fid="trasloco", target="#cap", expected="passed", rule="3.3.1/T2", trap=True,
       notes="With NPA '690' the native pattern check blocks submission; the browser bubble shows its 'match the requested format' text plus the title '4 cifre, ad es. 6900'.",
       difficulty="hard")

    # T3 fr -- red + icon + text
    mk("fr", "Commune de Valfictif", "Enregistrement d'un chien",
       "<p>Tout chien âgé de plus de trois mois doit être enregistré auprès de la commune. La taxe annuelle s'élève à CHF 100.–.</p>",
       row(field("detenteur", "Détenteur ou détentrice", ac="name"), field("chien", "Nom du chien"))
       + field("medaille", "Numéro de médaille")
       + field("race", "Race", err=False),
       [dict(f="detenteur", t=FILLED, m="Indiquez le nom du détenteur ou de la détentrice."),
        dict(f="chien", t=FILLED, m="Indiquez le nom du chien."),
        dict(f="medaille", t=digits(5), m="⚠ Le numéro de médaille comporte 5 chiffres, par ex. 04172.")],
       fid="chien-form", target="#medaille", expected="passed", rule="3.3.1/T3", trap=True,
       notes="Submitting '4172' turns the field red with a warning sign, but a text 'Le numéro de médaille comporte 5 chiffres…' also appears and is associated.",
       difficulty="medium")

    # T4 it -- summary near the submit button, no links
    mk("it", "Città di Modellina", "Iscrizione al servizio mensa",
       "<p>La mensa scolastica è aperta il lunedì, martedì, giovedì e venerdì. Il pasto costa CHF 9.– ed è fatturato ogni mese.</p>",
       row(field("bnome", "Nome del bambino", err=False), field("classe", "Classe", err=False))
       + field("bavs", "Numero AVS del bambino", hint="13 cifre, sulla tessera d'assicurazione malattia.", err=False)
       + field("allergie", "Allergie o diete", textarea=True, rows=2, err=False),
       [dict(f="bnome", t=FILLED, m="Il campo «Nome del bambino» è obbligatorio.", o="list"),
        dict(f="classe", t=FILLED, m="Il campo «Classe» è obbligatorio.", o="list"),
        dict(f="bavs", t=AHV, m="Il campo «Numero AVS del bambino» deve contenere 13 cifre nel formato 756.0000.0000.00.", o="list")],
       bottom='<div class="msgbox" id="avvisi" tabindex="-1" role="alert" hidden><ul id="avvisi-lista"></ul></div>',
       summary=dict(box="avvisi", list="avvisi-lista"),
       fid="mensa", target="#bavs", expected="passed", rule="3.3.1/T4", trap=True,
       notes="Submitting '756.1234.567.89' shows, next to the submit button, 'Il campo «Numero AVS del bambino» deve contenere 13 cifre…', which names the field and the problem.",
       difficulty="medium")

    # T4 de -- alertdialog listing errors
    mk("de", "Gemeinde Fiktal", "Anmeldung Deutschkurs für Erwachsene",
       "<p>Die Gemeinde bietet ab Januar Deutschkurse auf den Niveaus A1 bis B1 an. Die Kurse finden am Dienstag- und Donnerstagabend im Schulhaus statt.</p>",
       row(field("vorname", "Vorname", ac="given-name", err=False), field("nachname", "Nachname", ac="family-name", err=False))
       + field("mail", "E-Mail-Adresse", type="email", ac="email", err=False)
       + select("niveau", "Niveau", ["A1", "A2", "B1", "weiss nicht"], err=False),
       [dict(f="vorname", t=FILLED, m="Vorname: Bitte ausfüllen.", o="dlg"),
        dict(f="nachname", t=FILLED, m="Nachname: Bitte ausfüllen.", o="dlg"),
        dict(f="mail", t=EMAIL, m="E-Mail-Adresse: Bitte eine vollständige Adresse im Format name@beispiel.example eingeben.", o="dlg")],
       extra_after=('<div class="dialog" id="hinweis" role="alertdialog" aria-modal="true" aria-labelledby="hinweis-titel" hidden>'
                    '<h2 id="hinweis-titel">Bitte prüfen Sie Ihre Angaben</h2><ul id="hinweis-liste"></ul>'
                    '<button type="button" id="hinweis-ok">OK</button></div>'),
       dialog=dict(box="hinweis", list="hinweis-liste", close="hinweis-ok"),
       fid="deutschkurs", target="#mail", expected="passed", rule="3.3.1/T4", trap=True,
       notes="Submitting 'urs.exempel(at)fiktal.example' opens an in-page alertdialog listing 'E-Mail-Adresse: Bitte eine vollständige Adresse … eingeben.'",
       difficulty="medium")

    # =====================================================================
    # CANTTELL
    # =====================================================================
    # C1 fr -- server only
    mk("fr", "Service des eaux d'Exempleval", "Demande de raccordement au réseau d'eau",
       "<p>Pour toute nouvelle construction ou transformation, le raccordement doit être demandé au moins six semaines avant le début des travaux.</p>",
       row(field("requerant", "Requérant ou requérante", err=False), field("telephone", "Téléphone", type="tel", err=False))
       + field("parcelle", "Numéro de parcelle", hint="Selon le registre foncier, p. ex. 1234-5.", err=False)
       + field("travaux", "Description des travaux", textarea=True, rows=3, err=False),
       [], script=False, action="/guichet/raccordement", novalidate=False,
       fid="raccordement", target="#parcelle", expected="cantTell", rule="3.3.1/C1",
       notes="The form posts to a server endpoint with no client-side check; how an invalid parcel number would be reported cannot be observed on the page.",
       difficulty="medium")

    # C1 it -- server only
    mk("it", "Comune di Valfittizia", "Occupazione temporanea del suolo pubblico",
       "<p>Ponteggi, cassoni o gru sul suolo pubblico richiedono un'autorizzazione. La domanda va inoltrata almeno dieci giorni prima.</p>",
       field("ditta", "Ditta o richiedente", err=False)
       + row(field("dal", "Dal (data)", err=False), field("al", "Al (data)", err=False))
       + field("superficie", "Superficie occupata in m²", im="numeric", err=False),
       [], script=False, action="/sportello/occupazione-suolo", novalidate=False,
       fid="occupazione", target="#dal", expected="cantTell", rule="3.3.1/C1",
       notes="No client-side validation: the form is sent to the server, so error identification for an invalid start date cannot be observed.",
       difficulty="medium")

    # C2 de -- message under the PLZ/Ort row, not associated, field not named
    mk("de", "Gemeinde Beispielwil", "Adressänderung innerhalb der Gemeinde",
       "<p>Melden Sie einen Umzug innerhalb von Beispielwil bitte innert 14 Tagen. Die Adressänderung ist gebührenfrei.</p>",
       row(field("vn", "Vorname", ac="given-name"), field("nn", "Nachname", ac="family-name"))
       + field("strasse", "Neue Strasse und Hausnummer", ac="street-address")
       + row(field("plz", "PLZ", im="numeric", ac="postal-code", err=False, size=6),
             field("ort", "Ort", ac="address-level2", err=False))
       + '<p class="err" id="hinweis-adresse"></p>'
       + field("umzug", "Umzugsdatum", hint="TT.MM.JJJJ"),
       [dict(f="vn", t=FILLED, m="Bitte geben Sie Ihren Vornamen ein."),
        dict(f="nn", t=FILLED, m="Bitte geben Sie Ihren Nachnamen ein."),
        dict(f="strasse", t=FILLED, m="Bitte geben Sie die neue Strasse mit Hausnummer ein."),
        dict(f="plz", t=PLZ, m="Bitte genau 4 Ziffern eingeben.", x="hinweis-adresse", mk=False),
        dict(f="umzug", t=DATE, m="Umzugsdatum: Bitte im Format TT.MM.JJJJ eingeben.")],
       fid="adresse", target="#plz", expected="cantTell", rule="3.3.1/C2", alt="passed",
       notes="For PLZ '30123' the text 'Bitte genau 4 Ziffern eingeben.' appears below the PLZ/Ort row; it describes the cause but does not name the field and is not associated with it.",
       difficulty="hard")

    # C2 fr -- message right under the field, not associated, field not named
    mk("fr", "Bibliothèque de Bourg-Modèle", "Prolonger mes prêts",
       "<p>Vous pouvez prolonger vos documents deux fois de quatre semaines, sauf s'ils sont réservés par une autre personne.</p>",
       field("carte", "Numéro de carte de lecteur", im="numeric", describe_err=False)
       + field("naissance", "Année de naissance", im="numeric", size=6),
       [dict(f="carte", t=digits(9), m="Seulement des chiffres, sans espaces ni tirets.", mk=False),
        dict(f="naissance", t=r"/^(19|20)\d{2}$/.test(v)", m="Année de naissance : indiquez quatre chiffres, p. ex. 1987.")],
       fid="prolongation", target="#carte", expected="cantTell", rule="3.3.1/C2", alt="passed",
       notes="For card number '1234-567-89' a visible text 'Seulement des chiffres, sans espaces ni tirets.' appears below the input, but it neither names the field nor is programmatically associated with it.",
       difficulty="hard")

    return shuffled(rng, cases)
