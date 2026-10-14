"""1.3.5 Identify Input Purpose – hand-written scenarios (see protocol_parts/1.3.5.md)."""
from common import *
from _structure_util import mk

CRITERION = "1.3.5"

CSS = ("form{max-width:560px}fieldset{border:1px solid #c9d3d8;border-radius:8px;margin:16px 0;padding:8px 14px 14px}"
       "legend{font-weight:700}.inline label{display:inline;font-weight:400;margin:0 14px 0 4px}"
       ".datum-teile{display:flex;gap:12px}.datum-teile div{flex:0 0 auto}.datum-teile input{width:5em}")


def F(id_, label, ac=None, type_="text", extra=""):
    """label + input; ac=None omits autocomplete."""
    a = f' autocomplete="{esc(ac)}"' if ac else ""
    return (f'<label for="{id_}">{esc(label)}</label>\n'
            f'<input id="{id_}" name="{id_}" type="{type_}"{a}{extra}>')


def _c(rng, lang, expected, rule, title, main, target, notes, **kw):
    return mk(CRITERION, rng, lang, expected, rule, title, main, target, notes, css=CSS, **kw)


def form(action, inner, button):
    return f'<form action="{action}" method="post">\n{inner}\n<p><button type="submit">{esc(button)}</button></p>\n</form>'


# ---------------------------------------------------------------------------
# failed
# ---------------------------------------------------------------------------

def f_given_missing_de(rng):
    inner = "\n".join([
        F("vorname", "Vorname"),
        F("nachname", "Nachname", "family-name"),
        F("geburtsdatum", "Geburtsdatum", "bday", extra=' placeholder="TT.MM.JJJJ"'),
        F("strasse", "Strasse und Nr.", "street-address"),
        F("plz", "PLZ", "postal-code", extra=' inputmode="numeric"'),
        F("ort", "Ort", "address-level2"),
        F("email", "E-Mail", "email", "email"),
    ])
    main = f"""<h1>Leseausweis beantragen</h1>
<p>Der Leseausweis ist für Einwohnerinnen und Einwohner von Mustersee kostenlos. Sie können ihn nach der Anmeldung am Ausleihschalter abholen.</p>
{form("ausweis-beantragt.html", inner, "Antrag senden")}"""
    return _c(rng, "de", "failed", "1.3.5/F1", "Leseausweis", main, "#vorname",
              "The applicant's own first name has no autocomplete attribute, while all other personal fields carry valid tokens; 'given-name' is a listed input purpose (H98 not applied).",
              org="Bibliothek Mustersee", diff="easy")


def f_email_missing_fr(rng):
    inner = "\n".join([
        F("prenom", "Prénom", "given-name"),
        F("nom", "Nom", "family-name"),
        F("courriel", "Adresse électronique", None, "email"),
    ])
    main = f"""<h1>Newsletter communale</h1>
<p>Recevez une fois par mois les nouvelles de la commune : travaux, manifestations, décisions du Conseil communal.</p>
{form("newsletter-merci.html", inner, "M'inscrire")}"""
    return _c(rng, "fr", "failed", "1.3.5/F1", "Newsletter", main, "#courriel",
              "The subscriber's own e-mail field only has type=email and no autocomplete=\"email\"; the input type does not expose the purpose required by 1.3.5.",
              org="Commune de Valfictif", diff="medium")


def f_cap_invalid_it(rng):
    inner = "\n".join([
        F("nome", "Nome", "given-name"),
        F("cognome", "Cognome", "family-name"),
        F("via", "Via e numero", "street-address"),
        F("cap", "NAP", "cap", extra=' inputmode="numeric"'),
        F("localita", "Località", "address-level2"),
        F("telefono", "Telefono", "tel", "tel"),
    ])
    main = f"""<h1>Corsi di lingua per adulti 2027</h1>
<p>Iscrizione ai corsi serali di tedesco e francese (livelli A1–B2). Le lezioni si svolgono nelle aule della scuola media.</p>
{form("iscrizione-corso.html", inner, "Iscrivermi")}"""
    return _c(rng, "it", "failed", "1.3.5/F2", "Corsi di lingua", main, "#cap",
              "The participant's postal code uses autocomplete=\"cap\", which is not a valid token (should be postal-code), so the purpose cannot be determined (F107).",
              org="Comune di Esempiano", diff="medium")


def f_bday_invalid_de(rng):
    inner = "\n".join([
        F("ms-name", "Vor- und Nachname", "name"),
        F("ms-geburtsdatum", "Geburtsdatum", "birthday", extra=' placeholder="TT.MM.JJJJ"'),
        F("ms-email", "E-Mail", "email", "email"),
        '<label for="instrument">Gewünschtes Instrument</label>\n<select id="instrument" name="instrument"><option>Klavier</option><option>Gitarre</option><option>Querflöte</option><option>Schlagzeug</option></select>',
    ])
    main = f"""<h1>Anmeldung Musikschule – Erwachsene</h1>
<p>Erwachsene können Einzelunterricht in 30- oder 45-Minuten-Lektionen belegen. Der Unterricht beginnt im Februar.</p>
{form("musikschule-danke.html", inner, "Anmelden")}"""
    return _c(rng, "de", "failed", "1.3.5/F2", "Musikschule", main, "#ms-geburtsdatum",
              "The user's date of birth uses autocomplete=\"birthday\", an invalid token (the listed purpose is bday) (F107, ACT 73f2c2).",
              org="Gemeinde Beispielberg", diff="medium")


def f_tel_invalid_fr(rng):
    inner = "\n".join([
        F("rappel-nom", "Nom et prénom", "name"),
        F("rappel-tel", "Numéro de téléphone", "phone", "tel"),
        '<label for="sujet">Sujet</label>\n<select id="sujet" name="sujet"><option>Impôts</option><option>Contrôle des habitants</option><option>Constructions</option></select>',
    ])
    main = f"""<h1>Demande de rappel</h1>
<p>Laissez-nous votre numéro : un collaborateur de l'administration vous rappelle dans les deux jours ouvrables.</p>
{form("rappel-merci.html", inner, "Demander un rappel")}"""
    return _c(rng, "fr", "failed", "1.3.5/F2", "Demande de rappel", main, "#rappel-tel",
              "The user's phone number field has autocomplete=\"phone\", which is not a valid token (tel is) (F107).",
              org="Commune d'Exempleval", diff="medium")


def f_address_invalid_it(rng):
    inner = "\n".join([
        F("tr-nome", "Nome e cognome", "name"),
        F("tr-indirizzo", "Nuovo indirizzo (via e numero)", "address"),
        F("tr-nap", "NAP", "postal-code"),
        F("tr-localita", "Località", "address-level2"),
        F("tr-data", "Data del trasloco", None, extra=' placeholder="gg.mm.aaaa"'),
    ])
    main = f"""<h1>Notifica di cambiamento d'indirizzo</h1>
<p>Chi trasloca all'interno del Comune deve notificare il nuovo indirizzo entro 14 giorni.</p>
{form("trasloco-notificato.html", inner, "Invia la notifica")}"""
    return _c(rng, "it", "failed", "1.3.5/F2", "Cambiamento d'indirizzo", main, "#tr-indirizzo",
              "The user's new street address uses autocomplete=\"address\", which is not a valid token (street-address or address-line1 are) (F107).",
              org="Comune di Valfittizia", diff="medium")


def f_family_wrong_de(rng):
    inner = "\n".join([
        F("k-vorname", "Vorname", "given-name"),
        F("k-nachname", "Nachname", "given-name"),
        F("k-email", "E-Mail", "email", "email"),
        '<label for="anliegen">Ihr Anliegen</label>\n<textarea id="anliegen" name="anliegen" rows="4"></textarea>',
    ])
    main = f"""<h1>Kontakt Steueramt</h1>
<p>Fragen zu Ihrer Steuererklärung oder Rechnung? Schreiben Sie uns – wir antworten innerhalb von drei Arbeitstagen.</p>
{form("nachricht-gesendet.html", inner, "Nachricht senden")}"""
    return _c(rng, "de", "failed", "1.3.5/F2", "Kontakt Steueramt", main, "#k-nachname",
              "The user's family-name field is marked autocomplete=\"given-name\"; the token is valid but states the wrong purpose, so the field's purpose is misidentified (F107).",
              org="Gemeinde Fiktal", diff="hard")


def f_locality_missing_fr(rng):
    inner = "\n".join([
        F("dt-nom", "Nom", "family-name"),
        F("dt-prenom", "Prénom", "given-name"),
        F("dt-adresse", "Rue et numéro", "street-address"),
        F("dt-npa", "NPA", "postal-code"),
        F("dt-localite", "Localité"),
    ])
    main = f"""<h1>Carte d'accès à la déchetterie</h1>
<p>Chaque ménage reçoit une carte d'accès gratuite. Une carte de remplacement coûte CHF 20.–.</p>
{form("carte-commandee.html", inner, "Commander la carte")}"""
    return _c(rng, "fr", "failed", "1.3.5/F1", "Carte déchetterie", main, "#dt-localite",
              "The applicant's own locality field has no autocomplete (address-level2 would apply), while all other address fields are tagged (H98).",
              org="Commune d'Exempleval", diff="medium")


def f_email_off_it(rng):
    inner = "\n".join([
        F("nl-nome", "Nome", "given-name"),
        F("nl-email", "Il tuo indirizzo e-mail", "off", "email"),
        '<fieldset class="inline"><legend>Argomenti</legend>'
        '<input type="checkbox" id="arg-libri" name="argomenti" value="libri"><label for="arg-libri">Nuovi libri</label>'
        '<input type="checkbox" id="arg-eventi" name="argomenti" value="eventi"><label for="arg-eventi">Eventi</label></fieldset>',
    ])
    main = f"""<h1>Newsletter della biblioteca</h1>
<p>Ogni mese le novità in biblioteca e il programma delle letture per bambini.</p>
{form("newsletter-grazie.html", inner, "Abbonarmi")}"""
    return _c(rng, "it", "failed", "1.3.5/F3", "Newsletter biblioteca", main, "#nl-email",
              "The subscriber's own e-mail field sets autocomplete=\"off\" instead of email, so its listed purpose is not programmatically exposed.",
              org="Biblioteca di Modellina", diff="hard")


def f_name_missing_en(rng):
    inner = "\n".join([
        F("guest-name", "Full name"),
        F("guest-email", "Email", "email", "email"),
        F("guest-phone", "Mobile phone", "tel", "tel"),
        F("guest-country", "Country of residence", "country-name"),
    ])
    main = f"""<h1>Your booking: guest details</h1>
<p>2 nights in a 6-bed dormitory, 14–16 November 2026. Breakfast included.</p>
{form("booking-confirmed.html", inner, "Confirm booking")}"""
    return _c(rng, "en", "failed", "1.3.5/F1", "Guest details", main, "#guest-name",
              "The booking guest's own full name field has no autocomplete=\"name\", unlike the other personal fields (H98).",
              org="Lake Fictal Hostel", diff="easy")


# ---------------------------------------------------------------------------
# passed
# ---------------------------------------------------------------------------

def p_email_de(rng):
    inner = "\n".join([F("nl-vorname", "Vorname", "given-name"), F("nl-mail", "E-Mail-Adresse", "email", "email")])
    main = f"""<h1>Newsletter abonnieren</h1>
<p>Erhalten Sie die Mitteilungen der Gemeinde bequem per E-Mail, etwa zehnmal pro Jahr.</p>
{form("abo-bestaetigt.html", inner, "Abonnieren")}"""
    return _c(rng, "de", "passed", "1.3.5/P1", "Newsletter", main, "#nl-mail",
              "The user's e-mail field has autocomplete=\"email\" (H98).",
              org="Gemeinde Ober-Beispielwil", diff="easy")


def p_tel_fr(rng):
    inner = "\n".join([F("cb-nom", "Nom et prénom", "name"), F("cb-telephone", "Téléphone", "tel", "tel")])
    main = f"""<h1>Être rappelé par le service social</h1>
<p>Indiquez vos coordonnées, nous vous rappelons en toute confidentialité.</p>
{form("rappel-ok.html", inner, "Envoyer")}"""
    return _c(rng, "fr", "passed", "1.3.5/P1", "Service social", main, "#cb-telephone",
              "The user's phone field carries the valid token tel (H98).",
              org="Ville de Bourg-Modèle", diff="easy")


def p_postal_it(rng):
    inner = "\n".join([
        F("ab-nome", "Nome e cognome", "name"),
        F("ab-via", "Via e numero", "street-address"),
        F("ab-nap", "NAP", "postal-code", extra=' inputmode="numeric"'),
        F("ab-localita", "Località", "address-level2"),
    ])
    main = f"""<h1>Abbonamento al bollettino comunale</h1>
<p>Il bollettino «Esempiano informa» esce quattro volte all'anno ed è gratuito per i domiciliati.</p>
{form("abbonamento-ok.html", inner, "Abbonarmi")}"""
    return _c(rng, "it", "passed", "1.3.5/P1", "Bollettino comunale", main, "#ab-nap",
              "The user's postal code uses the valid token postal-code; the other address fields are tagged too (H98).",
              org="Comune di Esempiano", diff="easy")


def p_bday_parts_de(rng):
    inner = (F("ve-name", "Name und Vorname", "name") + "\n"
             '<fieldset><legend>Geburtsdatum</legend><div class="datum-teile">'
             '<div><label for="geb-tag">Tag</label><input id="geb-tag" name="geb-tag" type="text" inputmode="numeric" autocomplete="bday-day"></div>'
             '<div><label for="geb-monat">Monat</label><input id="geb-monat" name="geb-monat" type="text" inputmode="numeric" autocomplete="bday-month"></div>'
             '<div><label for="geb-jahr">Jahr</label><input id="geb-jahr" name="geb-jahr" type="text" inputmode="numeric" autocomplete="bday-year"></div>'
             '</div></fieldset>')
    main = f"""<h1>Verbilligte Tageskarte für Seniorinnen und Senioren</h1>
<p>Ab 65 Jahren erhalten Sie die Tageskarte zum Preis von CHF 30.–. Bitte geben Sie Ihr Geburtsdatum an.</p>
{form("tageskarte-senioren.html", inner, "Weiter")}"""
    return _c(rng, "de", "passed", "1.3.5/P1", "Tageskarte Senioren", main, "#geb-jahr",
              "The user's birth year field in a split date uses the valid token bday-year (day and month are tagged as well).",
              org="Gemeinde Beispielwil", diff="medium")


def p_username_fr(rng):
    inner = "\n".join([
        F("eg-identifiant", "Nom d'utilisateur", "username"),
        F("eg-mdp", "Mot de passe", "new-password", "password"),
        F("eg-courriel", "Adresse e-mail", "email", "email"),
    ])
    main = f"""<h1>Créer un compte e-guichet</h1>
<p>Avec votre compte, vous commandez des attestations et suivez vos demandes en ligne.</p>
{form("compte-cree.html", inner, "Créer le compte")}"""
    return _c(rng, "fr", "passed", "1.3.5/P1", "Compte e-guichet", main, "#eg-identifiant",
              "The account's user name field uses autocomplete=\"username\", a listed purpose (H98).",
              org="Ville de Bourg-Modèle", diff="medium")


# traps --------------------------------------------------------------------

def t_child_de(rng):
    inner = ('<fieldset><legend>Angaben zum Kind</legend>\n'
             + F("kind-vorname", "Vorname des Kindes") + "\n"
             + F("kind-nachname", "Nachname des Kindes") + "\n"
             + F("kind-geburtsdatum", "Geburtsdatum des Kindes", extra=' placeholder="TT.MM.JJJJ"')
             + '\n</fieldset>\n<fieldset><legend>Ihre Angaben (erziehungsberechtigte Person)</legend>\n'
             + F("eltern-name", "Vor- und Nachname", "name") + "\n"
             + F("eltern-email", "E-Mail", "email", "email") + "\n"
             + F("eltern-tel", "Telefon", "tel", "tel") + "\n</fieldset>")
    main = f"""<h1>Anmeldung Kindergarten 2027/28</h1>
<p>Kinder, die bis zum 31. Juli 2027 vier Jahre alt werden, treten im August in den Kindergarten ein.</p>
{form("anmeldung-kindergarten.html", inner, "Anmeldung senden")}"""
    return _c(rng, "de", "passed", "1.3.5/T1", "Kindergarten", main, "#kind-vorname",
              "The child's first name is information about another person, not the user, so it needs no autocomplete; the parent's own fields carry valid tokens.",
              org="Schule Beispielberg", trap=True, diff="medium")


def t_recipient_fr(rng):
    inner = ('<fieldset><legend>Vos coordonnées</legend>\n'
             + F("ach-nom", "Nom et prénom", "name") + "\n"
             + F("ach-courriel", "Courriel", "email", "email")
             + '\n</fieldset>\n<fieldset><legend>Destinataire du bon</legend>\n'
             + F("dest-nom", "Nom et prénom du destinataire") + "\n"
             + F("dest-rue", "Rue et numéro du destinataire") + "\n"
             + F("dest-npa", "NPA et localité du destinataire") + "\n</fieldset>")
    main = f"""<h1>Offrir un bon cadeau pour la piscine</h1>
<p>Le bon (CHF 50.– ou CHF 100.–) est envoyé par la poste directement à la personne de votre choix.</p>
{form("bon-commande.html", inner, "Commander le bon")}"""
    return _c(rng, "fr", "passed", "1.3.5/T1", "Bon cadeau", main, "#dest-rue",
              "The recipient's street address concerns a third person, so 1.3.5 does not require an autocomplete token; the buyer's own fields are tagged.",
              org="Ville de Bourg-Modèle", trap=True, diff="medium")


def t_emergency_it(rng):
    inner = ("\n".join([F("col-nome", "Nome e cognome del genitore", "name"), F("col-email", "E-mail", "email", "email")])
             + '\n<fieldset><legend>In caso d\'urgenza</legend>\n'
             + F("urg-persona", "Persona da contattare") + "\n"
             + F("tel-urgenza", "Telefono della persona da contattare", None, "tel") + "\n</fieldset>")
    main = f"""<h1>Colonia estiva 2027 – iscrizione</h1>
<p>Due settimane in montagna per bambini dai 7 ai 12 anni, dal 5 al 17 luglio 2027.</p>
{form("colonia-iscrizione.html", inner, "Iscrivere")}"""
    return _c(rng, "it", "passed", "1.3.5/T1", "Colonia estiva", main, "#tel-urgenza",
              "The emergency contact's phone number belongs to another person, so no autocomplete purpose is required; the parent's own fields are tagged.",
              org="Comune di Valfittizia", trap=True, diff="medium")


def t_search_de(rng):
    main = """<h1>Suche</h1>
<form action="suche.html" method="get" role="search">
<label for="suchbegriff">Suchbegriff</label>
<input id="suchbegriff" name="q" type="search">
<label for="rubrik">Rubrik</label>
<select id="rubrik" name="rubrik"><option>Alle Inhalte</option><option>Formulare</option><option>Aktuelles</option><option>Reglemente</option></select>
<p><button type="submit">Suchen</button></p>
</form>"""
    return _c(rng, "de", "inapplicable", "1.3.5/N1", "Suche", main, "#suchbegriff",
              "The page only has a search box and a category filter; neither collects information about the user, so no input is in scope of 1.3.5.",
              org="Gemeinde Beispielwil", trap=True, diff="easy", box=False)


def t_feedback_fr(rng):
    main = """<h1>Votre avis sur cette page</h1>
<form action="avis-merci.html" method="post">
<fieldset class="inline"><legend>Cette page vous a-t-elle été utile ?</legend>
<input type="radio" id="utile-oui" name="utile" value="oui"><label for="utile-oui">Oui</label>
<input type="radio" id="utile-non" name="utile" value="non"><label for="utile-non">Non</label></fieldset>
<label for="commentaire">Commentaire (facultatif, anonyme)</label>
<textarea id="commentaire" name="commentaire" rows="4" autocomplete="off"></textarea>
<p><button type="submit">Envoyer</button></p>
</form>"""
    return _c(rng, "fr", "inapplicable", "1.3.5/N1", "Votre avis", main, "#commentaire",
              "Anonymous feedback form: the comment and the yes/no question do not collect information about the user, so autocomplete=\"off\" is irrelevant and 1.3.5 does not apply.",
              org="Commune de Valfictif", trap=True, diff="medium", box=False)


def t_doctor_it(rng):
    inner = "\n".join([
        F("sp-nome", "Il suo nome e cognome", "name"),
        F("sp-telefono", "Il suo numero di telefono", "tel", "tel"),
        F("medico", "Nome del medico curante"),
        '<label for="bisogno">Di quale aiuto ha bisogno?</label>\n<textarea id="bisogno" name="bisogno" rows="3"></textarea>',
    ])
    main = f"""<h1>Richiesta di aiuto domiciliare</h1>
<p>Il servizio di aiuto domiciliare sostiene le persone anziane nelle faccende di casa e nella cura personale.</p>
{form("richiesta-aiuto.html", inner, "Invia la richiesta")}"""
    return _c(rng, "it", "passed", "1.3.5/T1", "Aiuto domiciliare", main, "#medico",
              "The doctor's name is information about a third party, not the user, so no autocomplete purpose is needed; the user's own fields are tagged.",
              org="Comune di Esempiano", trap=True, diff="medium")


def t_quantity_de(rng):
    inner = "\n".join([
        F("anzahl", "Anzahl Broschüren", None, "number", ' min="1" max="10" value="1"'),
        F("be-name", "Vor- und Nachname", "name"),
        F("be-strasse", "Strasse und Nr.", "street-address"),
        F("be-plz", "PLZ", "postal-code"),
        F("be-ort", "Ort", "address-level2"),
    ])
    main = f"""<h1>Gemeindechronik «Fiktal im Wandel» bestellen</h1>
<p>Die reich bebilderte Chronik (240 Seiten) kostet CHF 45.– inklusive Versand.</p>
{form("chronik-bestellt.html", inner, "Bestellen")}"""
    return _c(rng, "de", "passed", "1.3.5/T2", "Gemeindechronik", main, "#anzahl",
              "The number of copies is not one of the listed input purposes and not information about the user, so a missing autocomplete is fine; all personal fields are tagged.",
              org="Gemeinde Fiktal", trap=True, diff="easy")


# ---------------------------------------------------------------------------
# cantTell
# ---------------------------------------------------------------------------

def c_reserve_for_other_de(rng):
    inner = "\n".join([
        F("res-name", "Name"),
        F("res-ausweis", "Nummer des Leseausweises", None, extra=' inputmode="numeric"'),
        F("res-titel", "Titel des Mediums"),
    ])
    main = f"""<h1>Medium reservieren</h1>
<p>Ausgeliehene Medien können Sie für CHF 1.– reservieren. Sie können auch für eine andere Person reservieren, zum Beispiel für Ihr Kind.</p>
{form("reservation-ok.html", inner, "Reservieren")}"""
    return _c(rng, "de", "cantTell", "1.3.5/C1", "Medium reservieren", main, "#res-name",
              "The 'Name' field may hold the user's own name or that of another person (the page invites both), so whether it collects information about the user cannot be decided.",
              org="Bibliothek Mustersee", alt="failed", diff="hard")


def c_vaccination_fr(rng):
    inner = "\n".join([
        F("vac-nom", "Nom et prénom de la personne à vacciner"),
        F("vac-tel", "Téléphone", None, "tel"),
        '<label for="vac-date">Date souhaitée</label>\n<select id="vac-date" name="vac-date"><option>mardi 3 novembre</option><option>mardi 10 novembre</option></select>',
    ])
    main = f"""<h1>Vaccination contre la grippe</h1>
<p>Le centre médico-social propose la vaccination le mardi après-midi. Vous pouvez inscrire vous-même ou un proche.</p>
{form("vaccination-ok.html", inner, "Réserver")}"""
    return _c(rng, "fr", "cantTell", "1.3.5/C1", "Vaccination", main, "#vac-tel",
              "The phone number belongs to 'the person to vaccinate', who may or may not be the user filling the form; whether it is information about the user is undecidable from the page.",
              org="Commune de Valfictif", alt="failed", diff="hard")


def c_delivery_it(rng):
    inner = ('<fieldset><legend>Fatturazione</legend>\n'
             + F("fa-nome", "Nome e cognome", "name") + "\n"
             + F("fa-via", "Via e numero", "street-address") + "\n"
             + F("fa-nap", "NAP", "postal-code") + "\n"
             + F("fa-localita", "Località", "address-level2")
             + '\n</fieldset>\n<fieldset><legend>Consegna</legend>\n'
             + F("consegna-via", "Indirizzo di consegna (se diverso)") + "\n"
             + '<label for="steri">Quantità</label>\n<select id="steri" name="steri"><option>1 stero</option><option>2 steri</option><option>4 steri</option></select>'
             + "\n</fieldset>")
    main = f"""<h1>Ordinazione di legna da ardere</h1>
<p>Il patriziato vende legna di faggio stagionata, tagliata a 33 cm: CHF 140.– per stero, consegna compresa.</p>
{form("legna-ordinata.html", inner, "Ordinare")}"""
    return _c(rng, "it", "cantTell", "1.3.5/C1", "Legna da ardere", main, "#consegna-via",
              "An alternative delivery address may be the user's own second address or someone else's; whether this field collects information about the user is ambiguous.",
              org="Comune di Valfittizia", diff="hard")


def c_representative_de(rng):
    inner = "\n".join([
        F("gs-name", "Name der gesuchstellenden Person oder der Vertretung"),
        F("gs-email", "E-Mail für Rückfragen", None, "email"),
        F("parzelle", "Parzellennummer"),
    ])
    main = f"""<h1>Baugesuch – Kontaktangaben</h1>
<p>Das Gesuch kann von der Bauherrschaft selbst oder von einer bevollmächtigten Vertretung (z. B. Architekturbüro) eingereicht werden.</p>
{form("baugesuch-schritt-2.html", inner, "Weiter")}"""
    return _c(rng, "de", "cantTell", "1.3.5/C1", "Baugesuch", main, "#gs-email",
              "The contact e-mail may be the user's own or that of the represented applicant; the page leaves open whose data it is, so the scope 'about the user' cannot be settled.",
              org="Gemeinde Ober-Beispielwil", diff="hard")


SCENARIOS = [
    f_given_missing_de, f_email_missing_fr, f_cap_invalid_it, f_bday_invalid_de, f_tel_invalid_fr,
    f_address_invalid_it, f_family_wrong_de, f_locality_missing_fr, f_email_off_it, f_name_missing_en,
    p_email_de, p_tel_fr, p_postal_it, p_bday_parts_de, p_username_fr,
    t_child_de, t_recipient_fr, t_emergency_it, t_search_de, t_feedback_fr, t_doctor_it, t_quantity_de,
    c_reserve_for_other_de, c_vaccination_fr, c_delivery_it, c_representative_de,
]


def build(rng):
    return [fn(rng) for fn in SCENARIOS]
