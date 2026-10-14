"""2.4.6 Headings and Labels – hand-written scenarios (see protocol_parts/2.4.6.md)."""
from common import *
from _structure_util import mk

CRITERION = "2.4.6"

FORM_CSS = "form{max-width:540px}"


def _c(rng, lang, expected, rule, title, main, target, notes, **kw):
    return mk(CRITERION, rng, lang, expected, rule, title, main, target, notes, **kw)


def F(id_, label, type_="text", extra=""):
    return f'<label for="{id_}">{esc(label)}</label>\n<input id="{id_}" name="{id_}" type="{type_}"{extra}>'


# ---------------------------------------------------------------------------
# failed – headings
# ---------------------------------------------------------------------------

def f_section_number_de(rng):
    main = """<h1>Steuern und Abgaben</h1>
<section id="liegenschaft"><h2>Liegenschaftssteuer</h2>
<p>Die Liegenschaftssteuer beträgt 1 Promille des amtlichen Werts und wird im Juni in Rechnung gestellt.</p></section>
<section id="hunde"><h2>Abschnitt 2</h2>
<p>Wer einen Hund hält, bezahlt eine jährliche Hundetaxe von CHF 120.–. Für jeden weiteren Hund im selben Haushalt sind es CHF 160.–. Melden Sie neue Hunde innert 30 Tagen an.</p></section>
<section id="feuerwehr"><h2>Feuerwehrersatzabgabe</h2>
<p>Personen zwischen 20 und 50 Jahren, die keinen Feuerwehrdienst leisten, bezahlen eine Ersatzabgabe von 3 % der Staatssteuer.</p></section>"""
    return _c(rng, "de", "failed", "2.4.6/F1", "Steuern und Abgaben", main, "#hunde h2",
              "The heading 'Abschnitt 2' says nothing about its section, which is entirely about the dog tax; the sibling headings show that descriptive headings were expected (G130).",
              org="Gemeinde Beispielberg", diff="easy")


def f_informations_fr(rng):
    main = """<h1>Piscine en plein air des Vignes</h1>
<h2>Horaires d'ouverture</h2>
<p>Du 15 mai au 15 septembre, tous les jours de 9 h à 19 h 30. Par beau temps, ouverture prolongée jusqu'à 20 h 30 en juillet.</p>
<h2>Tarifs</h2>
<p>Adultes CHF 6.–, enfants CHF 3.–, abonnement de saison famille CHF 140.–.</p>
<h2 id="titre-vidange">Informations</h2>
<p>Pour la vidange et le nettoyage du grand bassin, la piscine sera fermée du lundi 10 au vendredi 14 août. Les abonnements de saison sont prolongés d'autant.</p>"""
    return _c(rng, "fr", "failed", "2.4.6/F1", "Piscine en plein air", main, "#titre-vidange",
              "The heading 'Informations' is a generic word over a specific notice (closure for draining, 10–14 August); it does not describe the topic, unlike the other headings (G130).",
              org="Commune d'Exempleval", diff="medium")


def f_placeholder_it(rng):
    main = """<h1>Notizie</h1>
<article id="notizia-linea"><h2>Titolo</h2>
<p class="muted">14.10.2026</p>
<p>Dal 14 dicembre la nuova linea 5 collega la stazione con il quartiere dei Monti ogni 30 minuti, anche la domenica.</p></article>
<article id="notizia-mercato"><h2>Il mercato di Natale torna in Piazza Grande</h2>
<p class="muted">10.10.2026</p>
<p>Dal 5 all'8 dicembre oltre quaranta bancarelle di artigiani e produttori della regione.</p></article>"""
    return _c(rng, "it", "failed", "2.4.6/F1", "Notizie", main, "#notizia-linea h2",
              "'Titolo' is a CMS placeholder left as the heading of a news item about the new bus line 5; it does not describe the item (G130).",
              org="Città di Modellina", diff="easy")


def f_mismatch_de(rng):
    main = """<h1>Ludothek Beispielwil</h1>
<h2>Spielausleihe</h2>
<p>Über 800 Spiele für jedes Alter: Brettspiele, Puzzles, Fahrzeuge und Outdoor-Spiele. Ausleihdauer drei Wochen.</p>
<h2 id="titel-zeiten">Öffnungszeiten</h2>
<p>Jahresbeitrag pro Familie CHF 30.–. Die Ausleihe kostet je nach Spiel CHF 1.– bis CHF 3.–. Für verspätete Rückgabe verrechnen wir CHF 1.– pro Woche.</p>
<h2>Kontakt</h2>
<p>Schulhausstrasse 8, Telefon 032 000 45 10, ludothek@beispielwil.example</p>"""
    return _c(rng, "de", "failed", "2.4.6/F2", "Ludothek", main, "#titel-zeiten",
              "The heading 'Öffnungszeiten' sits above a section that only lists fees; the heading misdescribes its content.",
              org="Gemeinde Beispielwil", diff="medium")


def f_cms_block_fr(rng):
    main = """<h1>Passeport vacances 2027</h1>
<p>Du 5 au 16 juillet 2027, plus de 50 activités pour les enfants de 6 à 15 ans : escalade, poterie, visite de la caserne des pompiers…</p>
<h2 id="bloc-2">Bloc de texte</h2>
<p>Les inscriptions se font en ligne du 1er au 31 mai 2027. Le passeport coûte CHF 30.– par enfant ; dès le troisième enfant, il est gratuit.</p>
<h2>Activités proposées</h2>
<p>Le programme détaillé sera publié fin avril.</p>"""
    return _c(rng, "fr", "failed", "2.4.6/F1", "Passeport vacances", main, "#bloc-2",
              "'Bloc de texte' is an editor placeholder heading over the registration dates and price; it describes neither topic nor purpose.",
              org="Commune de Valfictif", diff="easy")


def f_more_en(rng):
    main = """<h1>Lake Fictal Hostel</h1>
<h2>Rooms</h2>
<p>Dormitories with 4 or 6 beds, two family rooms with private shower. Bed linen is included.</p>
<h2 id="more-heading">More</h2>
<p>Breakfast is served from 7 to 9.30 am (CHF 12). Packed lunches for hikers can be ordered the evening before at reception.</p>
<h2>Getting here</h2>
<p>Bus 21 from the station to the stop "Lake", then 5 minutes on foot.</p>"""
    return _c(rng, "en", "failed", "2.4.6/F1", "Hostel", main, "#more-heading",
              "The heading 'More' does not describe its section, which is about breakfast and packed lunches; the other headings are descriptive.",
              org="Lake Fictal Hostel", diff="easy")


# ---------------------------------------------------------------------------
# failed – labels
# ---------------------------------------------------------------------------

def f_label_field1_de(rng):
    inner = "\n".join([F("vn", "Vorname"), F("nn", "Nachname"),
                       F("feld-1", "Feld 1", extra=' placeholder="TT.MM.JJJJ"'), F("wohnort", "Wohnort")])
    main = f"""<h1>Anmeldung Altersnachmittag</h1>
<p>Der Altersnachmittag findet am 2. Dezember 2026 im Gemeindesaal statt. Teilnehmen können alle Einwohnerinnen und Einwohner ab 70 Jahren.</p>
<form action="altersnachmittag-danke.html" method="post">
{inner}
<p><button type="submit">Anmelden</button></p>
</form>"""
    return _c(rng, "de", "failed", "2.4.6/F3", "Altersnachmittag", main, 'label[for="feld-1"]',
              "The date-of-birth field is labelled 'Feld 1'; the label does not describe the purpose (only the placeholder hints at a date) (G131, ACT cc0f0a).",
              org="Gemeinde Fiktal", css=FORM_CSS, diff="easy")


def f_label_saisie_fr(rng):
    inner = "\n".join([F("nom-av", "Nom et prénom"), F("saisie", "Saisie", extra=' placeholder="756.0000.0000.00"'),
                       F("caisse", "Caisse de compensation")])
    main = f"""<h1>Demande de réduction des primes</h1>
<p>Les personnes à revenu modeste peuvent demander une réduction de leur prime d'assurance-maladie.</p>
<form action="reduction-envoyee.html" method="post">
{inner}
<p><button type="submit">Envoyer la demande</button></p>
</form>"""
    return _c(rng, "fr", "failed", "2.4.6/F3", "Réduction des primes", main, 'label[for="saisie"]',
              "The AVS number field is labelled 'Saisie' (input); the label does not say what to enter (G131).",
              org="Ville de Bourg-Modèle", css=FORM_CSS, diff="easy")


def f_label_valore_it(rng):
    inner = "\n".join([F("gruppo", "Nome del gruppo o della scuola"),
                       '<label for="data-visita">Data della visita</label>\n<select id="data-visita" name="data-visita"><option>martedì 10 novembre</option><option>giovedì 12 novembre</option></select>',
                       F("valore", "Valore", "number", ' min="1" max="25"')])
    main = f"""<h1>Visite guidate per gruppi</h1>
<p>Il Museo della Filanda propone visite guidate di un'ora per gruppi fino a 25 persone.</p>
<form action="visita-prenotata.html" method="post">
{inner}
<p><button type="submit">Prenotare</button></p>
</form>"""
    return _c(rng, "it", "failed", "2.4.6/F3", "Visite guidate", main, 'label[for="valore"]',
              "The field for the number of participants is labelled 'Valore'; the label does not identify what value is expected (G131).",
              org="Museo della Filanda, Esempiano", css=FORM_CSS, diff="medium")


def f_label_angaben_de(rng):
    inner = "\n".join([F("rf-name", "Name"), F("angaben", "Angaben", "tel", ' placeholder="032 000 00 00"'),
                       '<label for="rf-zeit">Bevorzugte Zeit für den Rückruf</label>\n<select id="rf-zeit" name="rf-zeit"><option>Vormittag</option><option>Nachmittag</option></select>'])
    main = f"""<h1>Rückruf durch die Spitex</h1>
<p>Wir rufen Sie gerne zurück und besprechen, welche Unterstützung zu Hause möglich ist.</p>
<form action="rueckruf-danke.html" method="post">
{inner}
<p><button type="submit">Rückruf anfordern</button></p>
</form>"""
    return _c(rng, "de", "failed", "2.4.6/F3", "Rückruf", main, 'label[for="angaben"]',
              "The phone number field is labelled 'Angaben' (details); the label does not describe the field's purpose (G131).",
              org="Spitex Fiktal-Beispielwil", css=FORM_CSS, diff="medium")


def f_label_wrong_it(rng):
    inner = "\n".join([F("pr-nome", "Nome e cognome"),
                       F("pr-contatto", "Telefono", "email", ' placeholder="nome@esempio.example"')])
    main = f"""<h1>Prenotazione del campo di calcio</h1>
<p>Le società sportive e i privati possono prenotare il campo sintetico. Riceverete la conferma per e-mail.</p>
<form action="campo-prenotato.html" method="post">
{inner}
<p><button type="submit">Prenotare</button></p>
</form>"""
    return _c(rng, "it", "failed", "2.4.6/F4", "Campo di calcio", main, 'label[for="pr-contatto"]',
              "The field is an e-mail field (type=email, placeholder 'nome@esempio.example', confirmation sent by e-mail) but is labelled 'Telefono'; the label misdescribes its purpose.",
              org="Società sportiva Valfittizia", css=FORM_CSS, diff="hard")


# ---------------------------------------------------------------------------
# passed
# ---------------------------------------------------------------------------

def p_heading_ferienpass_de(rng):
    main = """<h1>Ferienpass</h1>
<p>Der Ferienpass bietet Kindern von 6 bis 14 Jahren abwechslungsreiche Sommerferien.</p>
<h2 id="anmeldung-fp">Anmeldung zum Ferienpass 2027</h2>
<p>Die Anmeldung ist vom 1. bis 31. Mai 2027 online möglich. Pro Kind können Sie bis zu acht Kurse auswählen.</p>"""
    return _c(rng, "de", "passed", "2.4.6/P1", "Ferienpass", main, "#anmeldung-fp",
              "The heading states exactly what the section is about (registration for the 2027 holiday pass) (G130).",
              org="Gemeinde Beispielberg", diff="easy")


def p_heading_dechetterie_fr(rng):
    main = """<h1>Déchetterie de la Combe</h1>
<h2 id="hiver">Horaires de la déchetterie en hiver</h2>
<p>De novembre à mars : mercredi de 14 h à 17 h et samedi de 9 h à 12 h.</p>
<h2>Déchets acceptés</h2>
<p>Verre, papier, carton, métaux, déchets verts, appareils électriques et huiles usées.</p>"""
    return _c(rng, "fr", "passed", "2.4.6/P1", "Déchetterie", main, "#hiver",
              "The heading describes its content (winter opening hours of the waste centre) (G130).",
              org="Commune d'Exempleval", diff="easy")


def p_label_nascita_it(rng):
    inner = "\n".join([F("ins-nome", "Nome e cognome"), F("nascita", "Data di nascita", extra=' placeholder="gg.mm.aaaa"')])
    main = f"""<h1>Corso di ginnastica per anziani</h1>
<p>Il corso si tiene il giovedì mattina nella palestra comunale.</p>
<form action="ginnastica-iscrizione.html" method="post">
{inner}
<p><button type="submit">Iscrivermi</button></p>
</form>"""
    return _c(rng, "it", "passed", "2.4.6/P2", "Ginnastica anziani", main, 'label[for="nascita"]',
              "The label 'Data di nascita' describes the field's purpose (G131).",
              org="Comune di Esempiano", css=FORM_CSS, diff="easy")


def p_label_avs_fr(rng):
    inner = "\n".join([F("av-nom", "Nom et prénom"), F("no-avs", "Numéro AVS", extra=' placeholder="756.0000.0000.00"')])
    main = f"""<h1>Attestation de domicile</h1>
<p>L'attestation coûte CHF 15.– et vous est envoyée par la poste.</p>
<form action="attestation.html" method="post">
{inner}
<p><button type="submit">Commander</button></p>
</form>"""
    return _c(rng, "fr", "passed", "2.4.6/P2", "Attestation de domicile", main, 'label[for="no-avs"]',
              "The label 'Numéro AVS' states exactly what to enter (G131).",
              org="Commune de Valfictif", css=FORM_CSS, diff="easy")


def p_label_email_de(rng):
    inner = "\n".join([F("nl-name", "Vor- und Nachname"), F("nl-adresse", "E-Mail-Adresse", "email")])
    main = f"""<h1>Veranstaltungs-Newsletter</h1>
<p>Einmal im Monat alle Konzerte, Führungen und Märkte in Mustersee.</p>
<form action="newsletter-ok.html" method="post">
{inner}
<p><button type="submit">Abonnieren</button></p>
</form>"""
    return _c(rng, "de", "passed", "2.4.6/P2", "Newsletter", main, 'label[for="nl-adresse"]',
              "The label 'E-Mail-Adresse' describes the purpose of the field (G131).",
              org="Stadt Mustersee", css=FORM_CSS, diff="easy")


# traps --------------------------------------------------------------------

def t_kontakt_de(rng):
    main = """<h1>Bauverwaltung</h1>
<p>Die Bauverwaltung prüft Baugesuche, berät Bauherrschaften und führt die Baukontrollen durch.</p>
<h2 id="kontakt-bau">Kontakt</h2>
<p>Bauverwaltung Fiktal, Kirchweg 3<br>Telefon 032 000 12 60<br>bau@fiktal.example</p>"""
    return _c(rng, "de", "passed", "2.4.6/T1", "Bauverwaltung", main, "#kontakt-bau",
              "The one-word heading 'Kontakt' accurately describes the address and phone details below it; headings need not be long (Understanding 2.4.6).",
              org="Gemeinde Fiktal", trap=True, diff="medium")


def t_horaires_fr(rng):
    main = """<h1>Bibliothèque de Bourg-Modèle</h1>
<h2 id="horaires-biblio">Horaires</h2>
<p>Mardi et jeudi de 15 h à 19 h, mercredi de 14 h à 18 h, samedi de 9 h à 12 h.</p>
<h2>Inscription</h2>
<p>L'inscription est gratuite pour les habitants de la commune.</p>"""
    return _c(rng, "fr", "passed", "2.4.6/T1", "Bibliothèque", main, "#horaires-biblio",
              "'Horaires' is short but matches its content (opening hours); a single word can be descriptive.",
              org="Bibliothèque de Bourg-Modèle", trap=True, diff="easy")


def t_plz_de(rng):
    inner = "\n".join([F("lf-strasse", "Strasse"), F("lf-plz", "PLZ", extra=' inputmode="numeric"'), F("lf-ort", "Ort")])
    main = f"""<h1>Lieferadresse für die Kompostabgabe</h1>
<p>Der Werkhof liefert Kompost ab 1 m³ gratis innerhalb der Gemeinde.</p>
<form action="kompost-bestellt.html" method="post">
{inner}
<p><button type="submit">Bestellen</button></p>
</form>"""
    return _c(rng, "de", "passed", "2.4.6/T2", "Kompostabgabe", main, 'label[for="lf-plz"]',
              "'PLZ' is the standard Swiss abbreviation for postal code, universally understood in an address form; the label is descriptive.",
              org="Gemeinde Ober-Beispielwil", css=FORM_CSS, trap=True, diff="medium")


def t_nap_it(rng):
    inner = "\n".join([F("sp-via", "Via e numero"), F("sp-nap", "NAP", extra=' inputmode="numeric"'), F("sp-loc", "Località")])
    main = f"""<h1>Ritiro di rifiuti ingombranti a domicilio</h1>
<p>Il servizio costa CHF 40.– per ritiro (fino a 2 m³).</p>
<form action="ritiro-prenotato.html" method="post">
{inner}
<p><button type="submit">Prenotare il ritiro</button></p>
</form>"""
    return _c(rng, "it", "passed", "2.4.6/T2", "Ritiro ingombranti", main, 'label[for="sp-nap"]',
              "'NAP' (numero d'avviamento postale) is the usual Swiss-Italian abbreviation for postal code; in an address form it describes the field.",
              org="Comune di Valfittizia", css=FORM_CSS, trap=True, diff="medium")


def t_nom_fr(rng):
    inner = "\n".join([F("cl-nom", "Nom"), F("cl-prenom", "Prénom"), F("cl-mail", "Courriel", "email")])
    main = f"""<h1>Inscription au club de lecture</h1>
<p>Rencontre un jeudi par mois à la bibliothèque, de 19 h à 20 h 30.</p>
<form action="club-inscrit.html" method="post">
{inner}
<p><button type="submit">S'inscrire</button></p>
</form>"""
    return _c(rng, "fr", "passed", "2.4.6/T2", "Club de lecture", main, 'label[for="cl-nom"]',
              "The short label 'Nom' is descriptive for a family-name field next to 'Prénom'.",
              org="Bibliothèque de Bourg-Modèle", css=FORM_CSS, trap=True, diff="easy")


def t_letter_de(rng):
    css = ".az h2{font-size:1.6rem;border-bottom:2px solid #c9d3d8;margin-bottom:.2em}.az ul{columns:2}"
    main = """<h1>Dienstleistungen von A bis Z</h1>
<div class="az">
<h2 id="buchstabe-a">A</h2>
<ul><li><a href="abfall.html">Abfall</a></li><li><a href="abwasser.html">Abwasser</a></li><li><a href="ahv-zweigstelle.html">AHV-Zweigstelle</a></li><li><a href="altersheim.html">Altersheim</a></li></ul>
<h2>B</h2>
<ul><li><a href="baugesuch.html">Baugesuch</a></li><li><a href="bestattung.html">Bestattung</a></li><li><a href="betreibungsamt.html">Betreibungsamt</a></li></ul>
</div>"""
    return _c(rng, "de", "passed", "2.4.6/T1", "A bis Z", main, "#buchstabe-a",
              "In an A–Z index, the single letter 'A' fully describes the group of entries below it; Understanding 2.4.6 notes that even a single character may suffice.",
              org="Gemeinde Beispielwil", css=css, trap=True, diff="hard")


def t_costi_it(rng):
    main = """<h1>Doposcuola comunale</h1>
<p>Il doposcuola accoglie gli allievi delle elementari dalle 15.30 alle 18.00, con merenda e aiuto per i compiti.</p>
<h2 id="costi-doposcuola">Costi</h2>
<p>CHF 8.– al pomeriggio; dal secondo figlio CHF 5.–. La fattura è inviata ogni trimestre.</p>"""
    return _c(rng, "it", "passed", "2.4.6/T1", "Doposcuola", main, "#costi-doposcuola",
              "'Costi' is a one-word heading that correctly names the content (prices of the after-school care).",
              org="Comune di Esempiano", trap=True, diff="easy")


def t_no_headings_it(rng):
    main = """<p><strong>Grazie!</strong> La sua iscrizione alla giornata di pulizia del bosco di sabato 7 novembre 2026 è stata registrata.</p>
<p>Ritrovo alle 8.30 al magazzino comunale. Guanti, sacchi e merenda sono offerti dal Comune.</p>
<p><a href="index.html">Torna alla pagina iniziale</a></p>"""
    return _c(rng, "it", "inapplicable", "2.4.6/N1", "Iscrizione registrata", main, None,
              "The confirmation page contains no headings and no form labels; 2.4.6 does not require headings, so there is nothing to evaluate.",
              org="Comune di Valfittizia", trap=True, diff="medium", box=False)


# ---------------------------------------------------------------------------
# cantTell
# ---------------------------------------------------------------------------

def c_aktuelles_de(rng):
    main = """<h1>Werkdienst</h1>
<h2>Aufgaben</h2>
<p>Der Werkdienst unterhält Strassen, Plätze, Brunnen und Grünanlagen und ist für den Winterdienst zuständig.</p>
<h2 id="aktuelles-wd">Aktuelles</h2>
<p>Vom 9. bis 20. November 2026 ersetzt der Werkdienst die Strassenbeleuchtung im Quartier Seematte durch LED-Leuchten.</p>
<h2>Kontakt Werkdienst</h2>
<p>Werkhof, Mühlegasse 5, Telefon 032 000 12 70</p>"""
    return _c(rng, "de", "cantTell", "2.4.6/C1", "Werkdienst", main, "#aktuelles-wd",
              "'Aktuelles' (news) names the kind of content but not its topic (street lighting works); whether such a category heading is descriptive enough is a judgement call.",
              org="Gemeinde Beispielwil", diff="hard")


def c_divers_fr(rng):
    main = """<h1>Informations communales – novembre 2026</h1>
<h2>Séance du Conseil général</h2>
<p>Le Conseil général siège le 25 novembre à 20 h à la salle du Conseil. La séance est publique.</p>
<h2 id="divers-nov">Divers</h2>
<p>Les objets trouvés de l'été peuvent être retirés au guichet jusqu'au 30 novembre.</p>
<p>Le marché aux puces de l'école aura lieu le 21 novembre dans la cour.</p>
<p>Les heures d'ouverture de la poste d'agence changent dès le 1er décembre.</p>"""
    return _c(rng, "fr", "cantTell", "2.4.6/C1", "Informations communales", main, "#divers-nov",
              "'Divers' sits over three unrelated short notices; it is generic, but for genuinely miscellaneous content it may be the most accurate description, so experts can disagree.",
              org="Commune de Valfictif", diff="hard")


def c_altre_info_it(rng):
    main = """<h1>Concerto di Capodanno 2027</h1>
<h2>Programma</h2>
<p>La Filarmonica di Modellina esegue valzer e polke di Strauss, direzione Marco Modello.</p>
<h2>Biglietti</h2>
<p>CHF 25.–, ridotti CHF 15.–; prevendita alla cancelleria comunale.</p>
<h2 id="altre-info">Altre informazioni</h2>
<p>Posteggi gratuiti presso le scuole. La sala è accessibile in sedia a rotelle dall'entrata laterale.</p>"""
    return _c(rng, "it", "cantTell", "2.4.6/C1", "Concerto di Capodanno", main, "#altre-info",
              "'Altre informazioni' groups parking and wheelchair access; it is generic but tells users the section holds the remaining practical details, so its descriptiveness is debatable.",
              org="Città di Modellina", diff="hard")


def c_details_de(rng):
    main = """<h1>Schaden an einer Wasserleitung melden</h1>
<p>Bei Wasser auf der Strasse oder fehlendem Druck rufen Sie bitte sofort den Pikettdienst an: 079 000 44 55.</p>
<form action="schaden-gemeldet.html" method="post">
<label for="sm-ort">Ort des Schadens (Strasse, Hausnummer)</label>
<input id="sm-ort" name="sm-ort" type="text">
<label for="sm-details">Details</label>
<textarea id="sm-details" name="sm-details" rows="4"></textarea>
<p><button type="submit">Schaden melden</button></p>
</form>"""
    return _c(rng, "de", "cantTell", "2.4.6/C2", "Schaden melden", main, 'label[for="sm-details"]',
              "The textarea label 'Details' is vague but, in a damage report form after the location field, users can infer it asks for a description; whether it is descriptive enough is debatable.",
              org="Wasserversorgung Fiktal", css=FORM_CSS, diff="hard")


SCENARIOS = [
    f_section_number_de, f_informations_fr, f_placeholder_it, f_mismatch_de, f_cms_block_fr, f_more_en,
    f_label_field1_de, f_label_saisie_fr, f_label_valore_it, f_label_angaben_de, f_label_wrong_it,
    p_heading_ferienpass_de, p_heading_dechetterie_fr, p_label_nascita_it, p_label_avs_fr, p_label_email_de,
    t_kontakt_de, t_horaires_fr, t_plz_de, t_nap_it, t_nom_fr, t_letter_de, t_costi_it, t_no_headings_it,
    c_aktuelles_de, c_divers_fr, c_altre_info_it, c_details_de,
]


def build(rng):
    return [fn(rng) for fn in SCENARIOS]
