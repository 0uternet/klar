"""1.3.1 Info and Relationships – hand-written scenarios (see protocol_parts/1.3.1.md)."""
from common import *
from _structure_util import mk, SR_ONLY

CRITERION = "1.3.1"


def _c(rng, lang, expected, rule, title, main, target, notes, **kw):
    return mk(CRITERION, rng, lang, expected, rule, title, main, target, notes, **kw)


# ---------------------------------------------------------------------------
# failed
# ---------------------------------------------------------------------------

def f_fake_heading_de(rng):
    css = "main h2,.zwischentitel{font-size:1.35rem;font-weight:700;margin:1.4em 0 .4em;line-height:1.3}"
    main = """<h1>Abfall und Recycling</h1>
<p>Die Gemeinde organisiert die Abfuhr von Kehricht, Grüngut und Altpapier. Sonderabfälle nehmen wir an zwei Sammeltagen pro Jahr entgegen.</p>
<h2>Kehricht</h2>
<p>Der Kehricht wird jeden Montag ab 7.00 Uhr abgeholt. Verwenden Sie die offiziellen Gebührensäcke (35 Liter: CHF 2.20, 60 Liter: CHF 3.80).</p>
<h2>Altpapier und Karton</h2>
<p>Gebündeltes Altpapier stellen Sie am ersten Mittwoch des Monats bis 7.00 Uhr an den Strassenrand. Karton bitte separat bündeln.</p>
<p class="zwischentitel" id="sonderabfall">Sonderabfälle</p>
<p>Farben, Lösungsmittel, Batterien und Medikamente gehören nicht in den Kehricht. Bringen Sie diese am 7. November 2026 von 9.00 bis 12.00 Uhr zum Werkhof an der Mühlegasse 5.</p>
<p>Kleinmengen bis 5 kg nimmt auch die Drogerie im Dorfzentrum zurück.</p>
<h2>Grüngut</h2>
<p>Von März bis November wird das Grüngut jeden Dienstag abgeholt. Container mit Vignette an den Strassenrand stellen.</p>"""
    return _c(rng, "de", "failed", "1.3.1/F1", "Abfall und Recycling", main, "#sonderabfall",
              "'Sonderabfälle' is styled exactly like the h2 section headings and opens its own section, but it is a <p>, so its heading role is not programmatically determined (F2).",
              org="Gemeinde Beispielwil", css=css, diff="easy")


def f_fake_heading_fr(rng):
    css = ("main h2,.titre-section{font-family:Georgia,serif;font-size:1.4rem;font-weight:700;color:#7a1f2b;"
           "margin:1.3em 0 .4em;border-bottom:2px solid #e0d2d2;padding-bottom:4px}")
    main = """<h1>Prêt et retour des documents</h1>
<h2>Prêt</h2>
<p>Avec votre carte de lecteur, vous pouvez emprunter jusqu'à 15 documents pour quatre semaines. Les DVD sont prêtés pour deux semaines.</p>
<h2>Prolongation</h2>
<p>Vous pouvez prolonger un prêt deux fois, au guichet, par téléphone ou dans votre compte en ligne, à condition que le document ne soit pas réservé.</p>
<div class="titre-section" id="retour-hors-horaires">Boîte de retour</div>
<p>En dehors des heures d'ouverture, déposez vos documents dans la boîte de retour située à côté de l'entrée principale, rue des Granges 4.</p>
<p>Les documents déposés le week-end sont enregistrés le lundi matin. Les jeux de société et les liseuses doivent être rendus au guichet.</p>
<h2>Prêt entre bibliothèques</h2>
<p>Un livre n'est pas dans notre catalogue ? Nous le commandons pour vous dans une autre bibliothèque du réseau (CHF 5.– par document).</p>"""
    return _c(rng, "fr", "failed", "1.3.1/F1", "Prêt et retour", main, "#retour-hors-horaires",
              "The 'Boîte de retour' div carries the same font, size, colour and rule as the h2 headings and starts a section, but it has no heading markup (F2/H42).",
              org="Bibliothèque de Bourg-Modèle", css=css, diff="easy")


def f_fake_heading_it(rng):
    css = "main h2,.sottotitolo{font-size:1.3rem;margin:1.2em 0 .3em}.sottotitolo b{font-weight:700}"
    main = """<article>
<h1>Settimana bianca 2027 delle scuole medie</h1>
<p class="muted">Pubblicato il 14.10.2026</p>
<p>Dal 1° al 5 febbraio 2027 le classi di seconda media trascorrono una settimana sulla neve a Valfittizia.</p>
<h2>Date e alloggio</h2>
<p>Partenza lunedì alle 8.00 dal piazzale della scuola, rientro venerdì verso le 17.00. Gli allievi alloggiano nella colonia Al Faggio.</p>
<h2>Costi</h2>
<p>La partecipazione costa CHF 180.– per allievo. Le famiglie in difficoltà possono chiedere un contributo al Comune.</p>
<p class="sottotitolo" id="equipaggiamento"><b>Equipaggiamento</b></p>
<ul>
<li>giacca e pantaloni da sci impermeabili</li>
<li>guanti, berretto e occhiali da sole</li>
<li>casco (obbligatorio per sci e snowboard)</li>
<li>pantofole e sacco a pelo leggero</li>
</ul>
<p>Il materiale da sci può essere noleggiato sul posto il lunedì pomeriggio.</p>
</article>"""
    return _c(rng, "it", "failed", "1.3.1/F1", "Settimana bianca 2027", main, "#equipaggiamento",
              "'Equipaggiamento' is a bold paragraph at the same size as the h2 headings and introduces a list section; its heading role is conveyed only visually (F2).",
              org="Scuola di Esempiano", css=css, diff="medium")


def f_table_no_th_de(rng):
    css = ".kopf td{font-weight:700;background:#e8eef2}#preise td:first-child{font-weight:600}"
    main = """<h1>Hallenbad Mustersee</h1>
<p>Das Hallenbad ist von Montag bis Freitag von 6.30 bis 21.30 Uhr und am Wochenende von 8.00 bis 18.00 Uhr geöffnet.</p>
<h2>Eintrittspreise</h2>
<table id="preise">
<tr class="kopf"><td>Kategorie</td><td>Einzeleintritt</td><td>10er-Abo</td><td>Jahresabo</td></tr>
<tr><td>Erwachsene</td><td>CHF 7.–</td><td>CHF 60.–</td><td>CHF 320.–</td></tr>
<tr><td>Jugendliche 16–20 Jahre</td><td>CHF 5.–</td><td>CHF 42.–</td><td>CHF 220.–</td></tr>
<tr><td>Kinder 6–15 Jahre</td><td>CHF 3.50</td><td>CHF 30.–</td><td>CHF 150.–</td></tr>
<tr><td>AHV/IV</td><td>CHF 5.–</td><td>CHF 42.–</td><td>CHF 220.–</td></tr>
</table>
<p>Kinder unter 6 Jahren baden in Begleitung einer erwachsenen Person gratis.</p>"""
    return _c(rng, "de", "failed", "1.3.1/F2", "Hallenbad – Preise", main, "#preise",
              "The price table has a visually bold header row and first column, but every cell is a <td>; no th, scope or headers attributes link the prices to their category and ticket type (F91).",
              org="Stadt Mustersee", css=css, diff="easy")


def f_table_no_th_it(rng):
    css = ("table.orario td{text-align:center}table.orario tr:first-child td{background:#1f6f8b;color:#ffffff;font-weight:700}"
           "table.orario td.fermata{text-align:left;font-weight:700}")
    main = """<h1>Linea 3: Stazione – Ospedale</h1>
<p>Orario valido dal 14 dicembre 2026, giorni feriali. Le corse delle 6.12 e delle 7.12 sono rinforzate durante il periodo scolastico.</p>
<table class="orario">
<tr><td>Fermata</td><td>Corsa 1</td><td>Corsa 2</td><td>Corsa 3</td><td>Corsa 4</td></tr>
<tr><td class="fermata">Stazione</td><td>6.12</td><td>7.12</td><td>8.42</td><td>10.12</td></tr>
<tr><td class="fermata">Piazza Grande</td><td>6.15</td><td>7.15</td><td>8.45</td><td>10.15</td></tr>
<tr><td class="fermata">Scuole</td><td>6.19</td><td>7.19</td><td>8.49</td><td>10.19</td></tr>
<tr><td class="fermata">Ospedale</td><td>6.24</td><td>7.24</td><td>8.54</td><td>10.24</td></tr>
</table>
<p>Il sabato e la domenica circola il bus su chiamata: telefono 091 000 33 44.</p>"""
    return _c(rng, "it", "failed", "1.3.1/F2", "Linea 3 – Orario", main, "table.orario",
              "The timetable's header row and stop column are only coloured/bold <td> cells; the relationships between stops, runs and times are not programmatically determined (F91, H51/H63 not used).",
              org="Trasporti pubblici di Modellina", css=css, diff="easy")


def f_table_presentation_fr(rng):
    main = """<h1>Cartes journalières CFF « Commune »</h1>
<p>La commune met chaque jour quatre cartes journalières à disposition des habitantes et habitants. Réservation au guichet ou par téléphone.</p>
<table role="presentation" id="tarifs-cartes">
<caption>Prix des cartes journalières</caption>
<tr><th scope="col">Réservation</th><th scope="col">Habitants</th><th scope="col">Non-résidents</th></tr>
<tr><th scope="row">Jusqu'à 7 jours avant</th><td>CHF 45.–</td><td>CHF 55.–</td></tr>
<tr><th scope="row">Moins de 7 jours avant</th><td>CHF 35.–</td><td>CHF 45.–</td></tr>
<tr><th scope="row">Le jour même</th><td>CHF 30.–</td><td>CHF 40.–</td></tr>
</table>
<p>Les cartes ne sont ni reprises ni échangées.</p>"""
    return _c(rng, "fr", "failed", "1.3.1/F6", "Cartes journalières", main, "#tarifs-cartes",
              "The table is real tabular data with th/scope, but role=\"presentation\" removes the table semantics, so the header/cell relationships are no longer exposed (F92).",
              org="Commune de Valfictif", diff="medium")


def f_br_list_fr(rng):
    main = """<h1>Arrivée dans la commune</h1>
<p>Toute personne qui s'établit à Exempleval doit s'annoncer au contrôle des habitants dans les 14 jours suivant son arrivée.</p>
<h2>Documents à présenter</h2>
<p id="documents">• Pièce d'identité valable (passeport ou carte d'identité)<br>• Permis de séjour pour les ressortissants étrangers<br>• Contrat de bail ou attestation du bailleur<br>• Certificat de famille pour les couples mariés</p>
<h2>Émolument</h2>
<p>L'annonce d'arrivée coûte CHF 20.– par personne majeure. Les enfants sont inscrits gratuitement.</p>"""
    return _c(rng, "fr", "failed", "1.3.1/F3", "Annonce d'arrivée", main, "#documents",
              "The four documents are presented as a bulleted list but built from bullet characters and <br> inside one paragraph; list structure and item count are not programmatically determined (H48 not used).",
              org="Commune d'Exempleval", diff="easy")


def f_div_list_de(rng):
    css = ".mitnehmen{margin:.5em 0 1em}.mitnehmen div{padding:2px 0}"
    main = """<h1>Ferienpass 2027</h1>
<p>Vom 5. bis 16. Juli 2027 bieten Vereine und Private über 60 Kurse und Ausflüge für Kinder von 6 bis 14 Jahren an.</p>
<h2>Was die Kinder mitbringen</h2>
<div class="mitnehmen">
<div>– Znüni und genügend zu trinken</div>
<div>– Sonnencreme und Kopfbedeckung</div>
<div>– Ferienpass-Ausweis</div>
<div>– gutes Schuhwerk für Ausflüge</div>
</div>
<h2>Kosten</h2>
<p>Der Ferienpass kostet CHF 25.– pro Kind. Einzelne Kurse verlangen einen Materialbeitrag.</p>"""
    return _c(rng, "de", "failed", "1.3.1/F3", "Ferienpass 2027", main, "div.mitnehmen",
              "The packing list is visually a dash-bulleted list, but each item is a plain div with a typed dash, so the list relationship is not marked up (H48).",
              org="Gemeinde Beispielberg", css=css, diff="medium")


def f_radio_group_it(rng):
    css = ".opz label{display:inline;font-weight:400;margin:0 16px 0 4px}fieldset{border:1px solid #c9d3d8;border-radius:8px;margin-top:16px}"
    main = """<h1>Iscrizione al corso di nuoto per bambini</h1>
<form action="iscrizione-inviata.html" method="post">
<label for="nome-bimbo">Nome e cognome del bambino</label>
<input id="nome-bimbo" name="nome-bimbo" type="text">
<label for="nascita-bimbo">Data di nascita</label>
<input id="nascita-bimbo" name="nascita-bimbo" type="text" placeholder="gg.mm.aaaa">
<div id="sa-nuotare">
<p>Il bambino sa già nuotare senza ausili?</p>
<p class="opz"><input type="radio" id="n-si" name="nuota" value="si"><label for="n-si">Sì</label>
<input type="radio" id="n-no" name="nuota" value="no"><label for="n-no">No</label>
<input type="radio" id="n-bracc" name="nuota" value="braccioli"><label for="n-bracc">Solo con i braccioli</label></p>
</div>
<fieldset>
<legend>Turno preferito</legend>
<p class="opz"><input type="radio" id="t-mer" name="turno" value="mer"><label for="t-mer">mercoledì 14.00</label>
<input type="radio" id="t-sab" name="turno" value="sab"><label for="t-sab">sabato 9.30</label></p>
</fieldset>
<p><button type="submit">Invia l'iscrizione</button></p>
</form>"""
    return _c(rng, "it", "failed", "1.3.1/F4", "Corso di nuoto", main, "#sa-nuotare",
              "The radio buttons 'Sì/No/Solo con i braccioli' only make sense with the question above them, but the question is a plain <p> with no fieldset/legend or group name (H71/ARIA17 not used); the other group is correct.",
              org="Società sportiva Valfittizia", css=css, diff="medium")


def f_radio_group_de(rng):
    css = ".wahl label{display:inline;font-weight:400;margin:0 18px 0 4px}"
    main = """<h1>Anmeldung Vereinsanlass im Gemeindesaal</h1>
<p>Bitte melden Sie Ihren Anlass mindestens vier Wochen im Voraus an. Die Bewilligung erhalten Sie per E-Mail.</p>
<form action="anlass-gesendet.html" method="post">
<label for="verein">Name des Vereins</label>
<input id="verein" name="verein" type="text">
<label for="anlassdatum">Datum des Anlasses</label>
<input id="anlassdatum" name="anlassdatum" type="text" placeholder="TT.MM.JJJJ">
<div class="frage" id="parkplatz-frage">
<p><strong>Benötigen Sie reservierte Parkplätze?</strong></p>
<p class="wahl"><input type="radio" id="pp-ja" name="parkplatz" value="ja"><label for="pp-ja">Ja</label>
<input type="radio" id="pp-nein" name="parkplatz" value="nein"><label for="pp-nein">Nein</label></p>
</div>
<label for="bemerkung">Bemerkungen</label>
<textarea id="bemerkung" name="bemerkung" rows="3"></textarea>
<p><button type="submit">Anmeldung senden</button></p>
</form>"""
    return _c(rng, "de", "failed", "1.3.1/F4", "Vereinsanlass anmelden", main, "#parkplatz-frage",
              "The 'Ja'/'Nein' radio buttons depend on the bold question above, which is not associated with them (no fieldset/legend, no role=group with a name) (H71).",
              org="Gemeinde Fiktal", css=css, diff="medium")


def f_layout_th_fr(rng):
    css = "table.portrait,table.portrait th,table.portrait td{border:0}table.portrait th{vertical-align:top;padding-right:20px}"
    img = asset("scene-market-portrait", scene("market", w=300, h=200, seed=3))
    main = f"""<h1>Portrait du mois</h1>
<table class="portrait">
<tr><th><img src="{img}" alt="Stand de miel sur la place du Village" width="300" height="200"></th>
<th>Nadia Spécimen, apicultrice à Valfictif</th></tr>
<tr><td colspan="2"><p>Depuis vingt ans, Nadia Spécimen s'occupe de trente ruches sur les hauts de la commune. Chaque samedi, elle vend son miel de forêt et de fleurs au marché.</p>
<p>« Les abeilles m'ont appris la patience », dit-elle en souriant. Cet automne, elle propose pour la première fois un cours d'initiation pour les écoles.</p></td></tr>
</table>"""
    return _c(rng, "fr", "failed", "1.3.1/F5", "Portrait du mois", main, "table.portrait",
              "The table only positions a photo next to a caption and prose (a layout table), yet it uses th cells, exposing false header relationships (F46).",
              org="Commune de Valfictif", css=css, diff="hard")


# ---------------------------------------------------------------------------
# passed
# ---------------------------------------------------------------------------

def p_table_scope_fr(rng):
    main = """<h1>Déchetterie communale</h1>
<p>La déchetterie de la Combe accepte les déchets triés des ménages de la commune. Présentez votre carte d'accès à l'entrée.</p>
<table id="horaires-dechetterie">
<caption>Horaires d'ouverture</caption>
<tr><th scope="col">Jour</th><th scope="col">Été (avril–octobre)</th><th scope="col">Hiver (novembre–mars)</th></tr>
<tr><th scope="row">Mercredi</th><td>14 h – 19 h</td><td>14 h – 17 h</td></tr>
<tr><th scope="row">Vendredi</th><td>14 h – 19 h</td><td>fermé</td></tr>
<tr><th scope="row">Samedi</th><td>8 h – 12 h et 13 h 30 – 16 h</td><td>9 h – 12 h</td></tr>
</table>"""
    return _c(rng, "fr", "passed", "1.3.1/P2", "Déchetterie", main, "#horaires-dechetterie",
              "Data table with caption and th scope=col/row; header relationships are programmatically determined (H51, H63).",
              org="Commune d'Exempleval", diff="easy")


def p_table_headers_de(rng):
    main = """<h1>Separatsammlungen 2027</h1>
<p>Die Daten gelten für das ganze Gemeindegebiet. Bitte stellen Sie das Sammelgut bis 7.00 Uhr bereit.</p>
<table id="sammeldaten">
<caption>Sammeldaten erstes Halbjahr 2027</caption>
<tr><td></td><th id="h-q1" colspan="2" scope="colgroup">1. Quartal</th><th id="h-q2" colspan="2" scope="colgroup">2. Quartal</th></tr>
<tr><td></td><th id="h-jan" headers="h-q1">Januar</th><th id="h-mar" headers="h-q1">März</th><th id="h-apr" headers="h-q2">April</th><th id="h-jun" headers="h-q2">Juni</th></tr>
<tr><th id="h-papier">Altpapier</th><td headers="h-papier h-q1 h-jan">6.1.</td><td headers="h-papier h-q1 h-mar">3.3.</td><td headers="h-papier h-q2 h-apr">7.4.</td><td headers="h-papier h-q2 h-jun">2.6.</td></tr>
<tr><th id="h-karton">Karton</th><td headers="h-karton h-q1 h-jan">20.1.</td><td headers="h-karton h-q1 h-mar">17.3.</td><td headers="h-karton h-q2 h-apr">21.4.</td><td headers="h-karton h-q2 h-jun">16.6.</td></tr>
<tr><th id="h-metall">Altmetall</th><td headers="h-metall h-q1 h-jan">–</td><td headers="h-metall h-q1 h-mar">24.3.</td><td headers="h-metall h-q2 h-apr">–</td><td headers="h-metall h-q2 h-jun">23.6.</td></tr>
</table>"""
    return _c(rng, "de", "passed", "1.3.1/P2", "Separatsammlungen", main, "#sammeldaten",
              "Two-level header table; every data cell references existing header ids in the same table via headers (H43), so all relationships are determinable.",
              org="Gemeinde Ober-Beispielwil", diff="hard")


def p_ul_nobullets_it(rng):
    css = "ul.documenti{list-style:none;padding:0}ul.documenti li{padding:8px 0;border-bottom:1px solid #c9d3d8}"
    main = """<h1>Rilascio della carta d'identità</h1>
<p>La carta d'identità si richiede allo sportello del controllo abitanti. Il documento viene spedito a domicilio entro dieci giorni lavorativi.</p>
<h2>Documenti necessari</h2>
<ul class="documenti">
<li>Carta d'identità o passaporto precedente</li>
<li>Una fotografia recente formato passaporto</li>
<li>Per i minorenni: firma di un genitore</li>
</ul>
<p>Emolumento: CHF 70.– per gli adulti, CHF 35.– per i minorenni.</p>"""
    return _c(rng, "it", "passed", "1.3.1/P1", "Carta d'identità", main, "ul.documenti",
              "The list looks like plain lines (bullets removed by CSS) but is a real ul/li, so the list structure is programmatically determined (H48).",
              org="Comune di Esempiano", css=css, diff="easy")


def p_fieldset_fr(rng):
    css = ".choix label{display:inline;font-weight:400;margin:0 14px 0 4px}fieldset{border:1px solid #c9d3d8;border-radius:8px}"
    main = """<h1>Commande d'une carte de stationnement</h1>
<form action="commande-envoyee.html" method="post">
<label for="plaque">Numéro de plaque</label>
<input id="plaque" name="plaque" type="text" placeholder="VD 123 456">
<fieldset id="paiement">
<legend>Mode de paiement</legend>
<p class="choix"><input type="radio" id="pay-facture" name="paiement" value="facture"><label for="pay-facture">Facture</label>
<input type="radio" id="pay-twint" name="paiement" value="twint"><label for="pay-twint">TWINT</label>
<input type="radio" id="pay-guichet" name="paiement" value="guichet"><label for="pay-guichet">Au guichet</label></p>
</fieldset>
<p><button type="submit">Commander</button></p>
</form>"""
    return _c(rng, "fr", "passed", "1.3.1/P3", "Carte de stationnement", main, "#paiement",
              "The radio group is wrapped in a fieldset whose legend states the question (H71).",
              org="Ville de Bourg-Modèle", css=css, diff="easy")


def p_role_group_de(rng):
    css = ".tage label{display:inline;font-weight:400;margin:0 14px 0 4px}.frage{font-weight:700;margin-top:16px}"
    main = """<h1>Seniorenturnen – Anmeldung</h1>
<p>Das Seniorenturnen findet in der Turnhalle Schulhausstrasse 8 statt. Die Leitung hat Beat Vorlage.</p>
<form action="danke.html" method="post">
<label for="tn-name">Name und Vorname</label>
<input id="tn-name" name="tn-name" type="text" autocomplete="name">
<p class="frage" id="frage-tage">An welchen Tagen möchten Sie teilnehmen?</p>
<div role="group" aria-labelledby="frage-tage" class="tage" id="kurstage">
<input type="checkbox" id="tag-mo" name="tage" value="mo"><label for="tag-mo">Montag 9.00</label>
<input type="checkbox" id="tag-mi" name="tage" value="mi"><label for="tag-mi">Mittwoch 14.00</label>
<input type="checkbox" id="tag-fr" name="tage" value="fr"><label for="tag-fr">Freitag 9.00</label>
</div>
<p><button type="submit">Anmelden</button></p>
</form>"""
    return _c(rng, "de", "passed", "1.3.1/P3", "Seniorenturnen", main, "#kurstage",
              "Checkbox group uses role=group with aria-labelledby pointing to the visible question (ARIA17), so the grouping and its label are programmatic.",
              org="Sportverein Beispielberg", css=css, diff="medium")


def p_dl_it(rng):
    css = "dl.scheda{display:grid;grid-template-columns:10em 1fr;gap:6px 16px}dl.scheda dt{font-weight:700}dl.scheda dd{margin:0}"
    main = """<h1>Concerto d'autunno della Filarmonica</h1>
<p>La Filarmonica di Modellina presenta un programma dedicato alle marce e alle colonne sonore del cinema.</p>
<dl class="scheda">
<dt>Data</dt><dd>sabato 21 novembre 2026, ore 20.30</dd>
<dt>Luogo</dt><dd>Palestra comunale, Via ai Monti 6</dd>
<dt>Entrata</dt><dd>offerta libera</dd>
<dt>Direzione</dt><dd>Marco Modello</dd>
</dl>"""
    return _c(rng, "it", "passed", "1.3.1/P1", "Concerto d'autunno", main, "dl.scheda",
              "Label–value pairs shown in two columns are marked up as a description list (dt/dd), so each value is programmatically tied to its label.",
              org="Città di Modellina", css=css, diff="medium")


def p_nested_ol_de(rng):
    main = """<h1>Baugesuch einreichen</h1>
<p>Für Neubauten, Anbauten und Umnutzungen braucht es eine Baubewilligung. So gehen Sie vor:</p>
<ol id="ablauf-baugesuch">
<li>Vorabklärung mit dem Bauamt vereinbaren (Telefon 032 000 12 34).</li>
<li>Gesuchsunterlagen zusammenstellen:
<ul>
<li>Situationsplan 1:500</li>
<li>Grundrisse, Schnitte und Fassaden 1:100</li>
<li>Nachweis Energie</li>
</ul>
</li>
<li>Gesuch in dreifacher Ausführung bei der Gemeindekanzlei einreichen.</li>
<li>Öffentliche Auflage während 30 Tagen abwarten.</li>
</ol>"""
    return _c(rng, "de", "passed", "1.3.1/P1", "Baugesuch", main, "#ablauf-baugesuch",
              "The procedure is an ordered list with a correctly nested sub-list, so sequence and hierarchy are programmatic (H48).",
              org="Gemeinde Beispielwil", diff="easy")


# traps --------------------------------------------------------------------

def t_strong_runin_de(rng):
    main = """<h1>Skilager 2027 der Primarschule</h1>
<p>Das Skilager für die 5. und 6. Klassen findet vom 8. bis 13. Februar 2027 in Fiktal statt. Die Kosten betragen CHF 150.– pro Kind.</p>
<p id="frist"><strong>Wichtig:</strong> Anmeldeschluss ist der 30.11.2026. Später eingehende Anmeldungen können wir leider nicht mehr berücksichtigen.</p>
<h2>Ausrüstung</h2>
<p>Skis und Snowboards können über die Schule gemietet werden. Ein Helm ist obligatorisch.</p>"""
    return _c(rng, "de", "passed", "1.3.1/T1", "Skilager 2027", main, "#frist strong",
              "The bold 'Wichtig:' is a run-in emphasis inside a running paragraph, not a heading; strong conveys the emphasis programmatically (H49/G115).",
              org="Schule Beispielberg", trap=True, diff="medium")


def t_strong_inline_it(rng):
    main = """<h1>Servizio pasti a domicilio</h1>
<p>Il Comune organizza la consegna di pasti caldi a domicilio dal lunedì al venerdì per le persone anziane o convalescenti.</p>
<p id="servizio">Il servizio è <strong>gratuito</strong> per le persone beneficiarie di prestazioni complementari; per tutte le altre il pasto costa CHF 14.–.</p>
<h2>Come ordinare</h2>
<p>Telefonate entro le 10.00 del giorno precedente al numero 091 000 45 67.</p>"""
    return _c(rng, "it", "passed", "1.3.1/T1", "Pasti a domicilio", main, "#servizio strong",
              "Bold text in the middle of a sentence is emphasis, marked up with strong; it is not structure that needs heading markup.",
              org="Comune di Valfittizia", trap=True, diff="easy")


def t_layout_table_fr(rng):
    css = "table.contact,table.contact td{border:0;vertical-align:top}table.contact td{padding:0 16px 0 0}"
    img = asset("pic-phone-contact", pictogram("phone", color="#0b4f6c", size=64))
    main = f"""<h1>Service des eaux</h1>
<p>Le service des eaux assure l'approvisionnement en eau potable de 4 200 habitants. En cas de fuite sur la voie publique, appelez le numéro de piquet.</p>
<h2>Contact</h2>
<table role="presentation" class="contact">
<tr><td><img src="{img}" alt="" width="64" height="64"></td>
<td><p>Service des eaux d'Exempleval<br>Rue de l'Église 15, 1999 Exempleval</p>
<p>Téléphone 024 000 56 78 – piquet 24 h/24 : 079 000 11 22</p></td></tr>
</table>"""
    return _c(rng, "fr", "passed", "1.3.1/T2", "Service des eaux", main, "table.contact",
              "Layout table that only positions a decorative icon beside the address: role=presentation, no th/caption, content reads correctly when linearised – no relationship is lost.",
              org="Service des eaux d'Exempleval", css=css, trap=True, diff="medium")


def t_label_value_de(rng):
    main = """<h1>Einwohnerkontrolle</h1>
<p>Die Einwohnerkontrolle ist zuständig für An- und Abmeldungen, Wohnsitzbestätigungen und Identitätskarten.</p>
<div class="box">
<p id="zeiten"><b>Öffnungszeiten:</b> Montag bis Freitag, 8.30–11.30 Uhr und 14.00–16.30 Uhr</p>
</div>
<h2>Wohnsitzbestätigung bestellen</h2>
<p>Eine Wohnsitzbestätigung kostet CHF 15.– und wird Ihnen per Post zugestellt.</p>"""
    return _c(rng, "de", "passed", "1.3.1/T3", "Einwohnerkontrolle", main, "#zeiten",
              "A single bold label followed by its value on the same line is a run-in label, not a heading or tabular data; the relationship is available in the text itself (colon).",
              org="Gemeinde Fiktal", trap=True, diff="medium")


def t_label_value_it(rng):
    css = ".avviso{border-left:4px solid #d4a017;background:#fff8e1;padding:10px 14px}"
    main = """<h1>Domanda di sussidio per la mobilità aziendale</h1>
<p>Le aziende con sede nel Comune possono chiedere un contributo per gli abbonamenti dei trasporti pubblici dei loro dipendenti.</p>
<p class="avviso" id="scadenza"><b>Termine di inoltro:</b> 30 novembre 2026</p>
<h2>Importo del sussidio</h2>
<p>Il Comune rimborsa il 20 % del prezzo dell'abbonamento annuale, al massimo CHF 300.– per dipendente.</p>"""
    return _c(rng, "it", "passed", "1.3.1/T3", "Sussidio mobilità", main, "#scadenza",
              "The bold 'Termine di inoltro:' is an inline label for the date on the same line; no heading or table structure is conveyed.",
              org="Comune di Esempiano", css=css, trap=True, diff="easy")


def t_lead_fr(rng):
    css = ".chapeau{font-size:1.3rem;line-height:1.45;font-weight:600;margin:.4em 0 1.2em}"
    main = """<h1>Rénovation du collège des Vignes</h1>
<p class="chapeau" id="intro">Le Conseil communal a adjugé les travaux de rénovation du collège des Vignes. Le chantier débutera en mars 2027 et durera dix-huit mois.</p>
<p>Pendant les travaux, les classes de 5P à 8P seront accueillies dans des pavillons provisoires installés sur le terrain de sport. Les horaires des cours ne changent pas.</p>
<h2>Séance d'information</h2>
<p>Une séance publique aura lieu le jeudi 12 novembre 2026 à 19 h 30 à l'aula du collège.</p>"""
    return _c(rng, "fr", "passed", "1.3.1/T4", "Rénovation du collège", main, "#intro",
              "The large, semi-bold text is an introductory lead paragraph (two full sentences under the h1), correctly marked as <p>; it is not a heading.",
              org="Commune de Valfictif", css=css, trap=True, diff="medium")


# ---------------------------------------------------------------------------
# cantTell
# ---------------------------------------------------------------------------

def c_bold_line_fr(rng):
    main = """<h1>Marché hebdomadaire</h1>
<p>Chaque mercredi de 8 h à 12 h, une vingtaine de producteurs de la région vendent fruits, légumes, fromages et pain sur la place du Village.</p>
<p id="pluie"><strong>En cas de pluie</strong></p>
<p>Le marché a lieu sous le couvert de la salle polyvalente.</p>
<h2>Devenir exposant</h2>
<p>Les emplacements sont attribués pour une saison. Contactez le greffe communal avant le 31 janvier.</p>"""
    return _c(rng, "fr", "cantTell", "1.3.1/C1", "Marché hebdomadaire", main, "#pluie",
              "A standalone bold line at body size followed by a single sentence: it may be a minor sub-heading or just an emphasised lead-in; whether it functions as a heading depends on author intent.",
              org="Commune de Valfictif", alt="failed", diff="hard")


def c_bold_line_it(rng):
    main = """<h1>Orari e prezzi del Museo della Filanda</h1>
<h2>Orari</h2>
<p>Da aprile a ottobre il museo è aperto da martedì a domenica dalle 14.00 alle 17.30.</p>
<h2>Prezzi</h2>
<p>Adulti CHF 10.–, studenti e AVS CHF 7.–, bambini fino a 16 anni gratis.</p>
<p id="gruppi"><b>Per i gruppi</b></p>
<p>Le visite guidate per gruppi (al massimo 20 persone) si prenotano almeno due settimane prima.</p>"""
    return _c(rng, "it", "cantTell", "1.3.1/C1", "Orari e prezzi", main, "#gruppi",
              "Bold, body-size standalone line 'Per i gruppi' before one sentence under the h2 'Prezzi': could be an unmarked h3 or a paragraph lead-in; not decidable from the page.",
              org="Museo della Filanda, Esempiano", alt="failed", diff="hard")


def c_grid_pairs_it(rng):
    css = (".scheda-rifugio{display:grid;grid-template-columns:9em 1fr;gap:6px 14px;max-width:420px}"
           ".scheda-rifugio .k{font-weight:700;color:#4f5b62}")
    main = """<h1>Capanna Valfittizia</h1>
<p>La capanna del Club alpino è raggiungibile in circa due ore e mezza da Valfittizia lungo il sentiero bianco-rosso-bianco.</p>
<div class="scheda-rifugio" id="dati-capanna">
<span class="k">Quota</span><span>1 840 m s.l.m.</span>
<span class="k">Posti letto</span><span>32</span>
<span class="k">Apertura</span><span>giugno – ottobre</span>
<span class="k">Custode</span><span>Paolo Campione</span>
</div>
<p>Prenotazione obbligatoria per gruppi di più di sei persone.</p>"""
    return _c(rng, "it", "cantTell", "1.3.1/C2", "Capanna Valfittizia", main, "#dati-capanna",
              "Label/value pairs are shown as a two-column grid of spans without colons or dl/table markup; whether this is tabular data needing structure or adjacent text whose relationship is evident is debated.",
              org="Comune di Valfittizia", css=css, alt="failed", diff="hard")


def c_card_titles_de(rng):
    css = (".card-titel{font-size:1.15rem;font-weight:700;margin:0 0 .4em}.card-titel a{text-decoration:none}"
           ".card p{margin:.3em 0}")
    main = """<h1>Freizeit in Beispielwil</h1>
<h2>Aktuelle Angebote</h2>
<div class="cards">
<div class="card" id="karte-ferienpass"><p class="card-titel"><a href="ferienpass.html">Ferienpass 2027</a></p><p>Über 60 Kurse für Kinder in den Sommerferien.</p></div>
<div class="card" id="karte-eisbahn"><p class="card-titel"><a href="eisbahn.html">Eisbahn Seematte</a></p><p>Geöffnet ab 28. November, Schlittschuhverleih vor Ort.</p></div>
<div class="card" id="karte-bibliothek"><p class="card-titel"><a href="lesesommer.html">Lesesommer</a></p><p>Lesen, Stempel sammeln und am Schlussfest gewinnen.</p></div>
</div>"""
    return _c(rng, "de", "cantTell", "1.3.1/C3", "Freizeit", main, "#karte-ferienpass .card-titel",
              "Teaser-card titles are large bold links in <p> under a real h2; whether card titles must be headings or are adequately conveyed as links in a list-like grid is a known point of expert disagreement.",
              org="Gemeinde Beispielwil", css=css, diff="hard")


SCENARIOS = [
    f_fake_heading_de, f_fake_heading_fr, f_fake_heading_it, f_table_no_th_de, f_table_no_th_it,
    f_table_presentation_fr, f_br_list_fr, f_div_list_de, f_radio_group_it, f_radio_group_de, f_layout_th_fr,
    p_table_scope_fr, p_table_headers_de, p_ul_nobullets_it, p_fieldset_fr, p_role_group_de, p_dl_it, p_nested_ol_de,
    t_strong_runin_de, t_strong_inline_it, t_layout_table_fr, t_label_value_de, t_label_value_it, t_lead_fr,
    c_bold_line_fr, c_bold_line_it, c_grid_pairs_it, c_card_titles_de,
]


def build(rng):
    return [fn(rng) for fn in SCENARIOS]
