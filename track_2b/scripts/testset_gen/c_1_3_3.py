"""1.3.3 Sensory Characteristics – hand-written scenarios (see protocol_parts/1.3.3.md)."""
from common import *
from _structure_util import mk, icon_svg

CRITERION = "1.3.3"

GEAR = ('<svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><g fill="none" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="3.5"/>'
        '<path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/></g></svg>')


def _map_svg(variant: int) -> str:
    """Plain street map without any text (stands in for an interactive map)."""
    parts = ['<rect width="560" height="320" fill="#eef3e8"/>',
             '<path d="M0 230 Q140 200 260 240 T560 220 V320 H0Z" fill="#9cc9e6"/>',
             '<g stroke="#ffffff" stroke-width="12" fill="none"><path d="M40 0 V320"/><path d="M0 90 H560"/>'
             '<path d="M300 0 L340 320"/><path d="M120 90 L220 200"/></g>',
             '<g stroke="#c9d3d8" stroke-width="2" fill="none"><path d="M40 0 V320"/><path d="M0 90 H560"/></g>']
    spots = [(70, 40), (180, 130), (360, 60), (450, 150)] if variant == 0 else [(90, 150), (250, 50), (400, 120)]
    for x, y in spots:
        parts.append(f'<rect x="{x}" y="{y}" width="22" height="22" rx="4" fill="#1f6f8b"/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="560" height="320" viewBox="0 0 560 320">'
            + "".join(parts) + "</svg>")


def _c(rng, lang, expected, rule, title, main, target, notes, **kw):
    return mk(CRITERION, rng, lang, expected, rule, title, main, target, notes, **kw)


MAPCSS = (".carte{position:relative;display:inline-block;max-width:100%}.carte img{display:block}"
          ".carte .ctrl{position:absolute;width:44px;height:44px;border-radius:50%;padding:0;display:flex;"
          "align-items:center;justify-content:center}")


# ---------------------------------------------------------------------------
# failed
# ---------------------------------------------------------------------------

def f_round_icon_fr(rng):
    img = asset("map-parking-a", _map_svg(0))
    css = MAPCSS + ".carte .zoom{top:10px;right:10px}"
    main = f"""<h1>Places de parc publiques</h1>
<p>La carte indique les parkings publics du centre. Les places sont gratuites pendant 30 minutes avec le disque.</p>
<p id="consigne-carte">Pour voir tous les détails du quartier, cliquez sur l'icône ronde en haut de la carte.</p>
<div class="carte"><img src="{img}" alt="Carte des parkings du centre (4 parkings)" width="560" height="320">
<button type="button" class="ctrl zoom" aria-label="Zoom avant">{icon_svg('plus', 22)}</button></div>"""
    return _c(rng, "fr", "failed", "1.3.3/F1", "Places de parc", main, "#consigne-carte",
              "The instruction identifies the control only by its round shape and position; the button shows only a '+' icon and the instruction gives no text name for it (F14).",
              org="Ville de Bourg-Modèle", css=css, diff="easy")


def f_bottom_left_it(rng):
    css = (".azioni{display:flex;justify-content:space-between;align-items:center;margin-top:20px;border-top:1px solid #c9d3d8;padding-top:12px}"
           ".azioni .stampa{background:#ffffff;color:#1d2327;border:1px solid #6b7280;padding:8px}")
    main = f"""<h1>Disdetta del posteggio comunale</h1>
<p id="istruzione-copia">Per conservare una copia, premi il pulsante in basso a sinistra prima di inviare il modulo.</p>
<form action="disdetta-inviata.html" method="post">
<label for="numero-posteggio">Numero del posteggio</label>
<input id="numero-posteggio" name="numero-posteggio" type="text">
<label for="data-disdetta">Disdetta a partire dal</label>
<input id="data-disdetta" name="data-disdetta" type="text" placeholder="gg.mm.aaaa">
<div class="azioni">
<button type="button" class="stampa" aria-label="Stampa" onclick="window.print()">{icon_svg('printer', 22)}</button>
<button type="submit">Invia la disdetta</button>
</div>
</form>"""
    return _c(rng, "it", "failed", "1.3.3/F1", "Disdetta posteggio", main, "#istruzione-copia",
              "The print control is referred to only by its location ('in basso a sinistra'); it is an icon-only button and the instruction gives no textual identification (F14).",
              org="Comune di Valfittizia", css=css, diff="easy")


def f_green_right_de(rng):
    css = (".navi{display:flex;justify-content:space-between;margin-top:20px}"
           ".navi .vor{background:#2f7d3a;border-color:#2f7d3a;padding:8px 14px}"
           ".navi .zurueck{background:#6b7280;border-color:#6b7280;padding:8px 14px}")
    main = f"""<h1>Umzug innerhalb der Gemeinde melden</h1>
<p class="muted">Schritt 1 von 3: Neue Adresse</p>
<form action="umzug-schritt-2.html" method="get">
<label for="neue-strasse">Strasse und Hausnummer</label>
<input id="neue-strasse" name="neue-strasse" type="text" autocomplete="street-address">
<label for="umzugsdatum">Umzugsdatum</label>
<input id="umzugsdatum" name="umzugsdatum" type="text" placeholder="TT.MM.JJJJ">
<p id="hinweis-weiter">Wenn alle Angaben stimmen, wählen Sie die grüne Schaltfläche unten links.</p>
<div class="navi">
<button type="button" class="zurueck" aria-label="Zurück" onclick="history.back()">{icon_svg('arrow-left', 22)}</button>
<button type="submit" class="vor" aria-label="Weiter">{icon_svg('arrow-right', 22)}</button>
</div>
</form>"""
    return _c(rng, "de", "failed", "1.3.3/F1", "Umzug melden", main, "#hinweis-weiter",
              "The next-step button is identified only by colour and position ('grüne Schaltfläche unten links'); it shows only an arrow icon and the instruction does not name it (F14).",
              org="Gemeinde Beispielwil", css=css, diff="easy")


def f_big_button_fr(rng):
    css = (".boutons{display:flex;align-items:center;gap:20px;margin-top:16px}"
           ".boutons .grand{width:72px;height:72px;border-radius:50%;padding:0;display:flex;align-items:center;justify-content:center}"
           ".boutons .petit{width:34px;height:34px;padding:0;background:#ffffff;color:#1d2327;border:1px solid #6b7280}")
    main = f"""<h1>Signaler un problème sur la voie publique</h1>
<p>Lampadaire en panne, nid-de-poule, banc cassé ? Décrivez le problème et indiquez l'endroit le plus précisément possible.</p>
<form action="signalement-recu.html" method="post">
<label for="lieu">Lieu</label>
<input id="lieu" name="lieu" type="text">
<label for="description">Description du problème</label>
<textarea id="description" name="description" rows="4"></textarea>
<p id="consigne-envoi">Une fois la description rédigée, utilisez le grand bouton pour transmettre votre message.</p>
<div class="boutons">
<button type="submit" class="grand" aria-label="Envoyer le signalement">{icon_svg('arrow-right', 30)}</button>
<button type="reset" class="petit" aria-label="Effacer le formulaire">{icon_svg('close', 16)}</button>
</div>
</form>"""
    return _c(rng, "fr", "failed", "1.3.3/F1", "Signaler un problème", main, "#consigne-envoi",
              "The submit control is identified only by its size ('le grand bouton'); both buttons are icon-only and the instruction offers no text identification (F14).",
              org="Commune d'Exempleval", css=css, diff="medium")


def f_sound_it(rng):
    main = """<h1>Sportello virtuale</h1>
<p>Siete in coda per una consulenza video con l'Ufficio controllo abitanti. Il tempo di attesa medio è di 8 minuti.</p>
<p id="istruzione-turno">Lasciate aperta questa pagina: quando sentite il segnale acustico è il vostro turno e potete entrare nella videochiamata.</p>
<p><a href="videochiamata.html">Entrare nella videochiamata</a></p>
<script>
setTimeout(function () {
  try {
    var Ctx = window.AudioContext || window.webkitAudioContext;
    var ctx = new Ctx();
    var osc = ctx.createOscillator();
    osc.frequency.value = 880;
    osc.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.4);
  } catch (e) {}
}, 6000);
</script>"""
    return _c(rng, "it", "failed", "1.3.3/F2", "Sportello virtuale", main, "#istruzione-turno",
              "The only cue that it is the user's turn is an audio beep (the script plays a tone and changes nothing visually); the instruction relies solely on sound.",
              org="Comune di Esempiano", diff="medium")


def f_box_right_de(rng):
    css = (".inhalt{display:flex;flex-wrap:wrap;gap:24px}.inhalt .text{flex:1 1 360px}"
           ".inhalt .daten{flex:0 0 220px;background:#e3f1e3;border-radius:8px;padding:12px}"
           ".inhalt .daten ul{margin:0;padding-left:1.1em}")
    main = """<h1>Grünabfuhr 2027</h1>
<div class="inhalt">
<div class="text">
<p>Gras, Laub, Rüstabfälle und Gartenabraum werden von März bis November abgeholt. Stellen Sie den Container mit gültiger Vignette bis 7.00 Uhr an den Strassenrand.</p>
<p id="hinweis-kasten">Die Abfuhrdaten für Ihr Quartier finden Sie im grünen Kasten rechts.</p>
<p>Äste bis 10 cm Durchmesser bitte bündeln und nicht länger als 1,5 m.</p>
</div>
<div class="daten">
<ul>
<li>Quartier Nord: Dienstag</li>
<li>Quartier Seematte: Mittwoch</li>
<li>Quartier Bahnhof: Donnerstag</li>
</ul>
</div>
</div>"""
    return _c(rng, "de", "failed", "1.3.3/F1", "Grünabfuhr", main, "#hinweis-kasten",
              "The collection dates are referred to only by colour and location ('grünen Kasten rechts'); the box has no heading or label that the instruction could name, and 'rechts' is not a reading-order reference (F14).",
              org="Gemeinde Beispielberg", css=css, diff="medium")


def f_vertical_menu_it(rng):
    css = (".colonne{display:flex;flex-wrap:wrap;gap:24px}.colonne .menu-v{flex:0 0 180px}"
           ".colonne .menu-v ul{list-style:none;padding:0;margin:0;border-left:3px solid #1f6f8b}"
           ".colonne .menu-v li a{display:block;padding:6px 10px}.colonne .corpo{flex:1 1 320px}")
    main = """<h1>Raccolta dei rifiuti 2027</h1>
<div class="colonne">
<nav class="menu-v" aria-label="Zone">
<ul>
<li><a href="raccolta-nord.html">Nord</a></li>
<li><a href="raccolta-centro.html">Centro</a></li>
<li><a href="raccolta-sud.html">Sud</a></li>
<li><a href="raccolta-monti.html">Monti</a></li>
</ul>
</nav>
<div class="corpo">
<p>Il calendario 2027 contiene tutte le date di raccolta dei rifiuti solidi urbani, della carta e degli scarti vegetali.</p>
<p id="istruzione-menu">Per gli orari di raccolta, scegli una voce del menu verticale.</p>
</div>
</div>"""
    return _c(rng, "it", "failed", "1.3.3/F1", "Raccolta rifiuti 2027", main, "#istruzione-menu",
              "The district menu is identified only by its orientation ('menu verticale'); it has no visible heading and the instruction does not name it or its items.",
              org="Comune di Valfittizia", css=css, diff="hard")


def f_star_de(rng):
    css = (".anlass{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #c9d3d8;padding:8px 0}"
           ".anlass button{background:#ffffff;color:#b7791f;border:1px solid #b7791f;padding:6px}")
    star = icon_svg("star", 20)
    main = f"""<h1>Veranstaltungen im November</h1>
<p id="hinweis-stern">Mit einem Klick auf den Stern neben einer Veranstaltung erscheint diese in Ihrer persönlichen Übersicht.</p>
<div class="anlass"><p><strong>7.11.</strong> Räbeliechtliumzug, Schulhausplatz, 18.00 Uhr</p><button type="button" aria-label="Vormerken: Räbeliechtliumzug">{star}</button></div>
<div class="anlass"><p><strong>14.11.</strong> Kammerkonzert in der Kirche, 19.30 Uhr</p><button type="button" aria-label="Vormerken: Kammerkonzert">{star}</button></div>
<div class="anlass"><p><strong>28.11.</strong> Adventsmarkt auf dem Dorfplatz, ab 10.00 Uhr</p><button type="button" aria-label="Vormerken: Adventsmarkt">{star}</button></div>"""
    return _c(rng, "de", "failed", "1.3.3/F1", "Veranstaltungen", main, "#hinweis-stern",
              "The bookmark buttons are referred to only by their star shape; they are icon-only and the instruction gives no text by which a non-visual user could identify them (F26/F14).",
              org="Gemeinde Fiktal", css=css, diff="medium")


def f_map_corner_en(rng):
    img = asset("map-trails-b", _map_svg(1))
    css = MAPCSS + ".carte .locate{bottom:10px;right:10px}"
    main = f"""<h1>Trail map</h1>
<p>All marked trails around Lake Fictal at a glance. Blue squares are car parks with a trailhead.</p>
<div class="carte"><img src="{img}" alt="Map of the lake shore with three car parks" width="560" height="320">
<button type="button" class="ctrl locate" aria-label="Locate me">{icon_svg('pin', 22)}</button></div>
<p id="map-hint">To see where you are, use the button at the bottom right of the map.</p>"""
    return _c(rng, "en", "failed", "1.3.3/F1", "Trail map", main, "#map-hint",
              "The geolocation control is identified only by its position on the map; it is an icon-only button and the instruction gives no text name (F14).",
              org="Example Valley Hiking Association", css=css, diff="easy")


def f_globe_fr(rng):
    css = (".entete{position:relative;padding-right:60px}.entete .langue{position:absolute;top:0;right:0;width:42px;height:42px;"
           "border-radius:50%;padding:0;display:flex;align-items:center;justify-content:center}")
    main = f"""<div class="entete">
<h1>Taxe de séjour</h1>
<button type="button" class="langue" aria-label="Langue" aria-haspopup="true">{icon_svg('globe', 24)}</button>
</div>
<p id="consigne-langue">Pour lire cette page en allemand ou en italien, cliquez sur le globe en haut à droite.</p>
<p>La taxe de séjour s'élève à CHF 2.50 par nuitée et par personne dès 16 ans. Elle est encaissée par les hébergeurs.</p>"""
    return _c(rng, "fr", "failed", "1.3.3/F1", "Taxe de séjour", main, "#consigne-langue",
              "The language switch is identified by shape ('le globe') and location only; the button is icon-only and the instruction never names it in text (F14/F26).",
              org="Commune de Valfictif", css=css, diff="medium")


# ---------------------------------------------------------------------------
# passed
# ---------------------------------------------------------------------------

def p_named_button_de(rng):
    main = """<h1>Turnhalle reservieren</h1>
<form action="reservation-bestaetigt.html" method="post">
<label for="halle">Halle</label>
<select id="halle" name="halle"><option>Turnhalle Seematte</option><option>Mehrzweckhalle Dorf</option></select>
<label for="datum-res">Datum</label>
<input id="datum-res" name="datum-res" type="text" placeholder="TT.MM.JJJJ">
<p id="hinweis-abschluss">Klicken Sie auf «Reservation abschliessen», um die Buchung verbindlich abzuschicken.</p>
<p><button type="submit">Reservation abschliessen</button></p>
</form>"""
    return _c(rng, "de", "passed", "1.3.3/P1", "Turnhalle reservieren", main, "#hinweis-abschluss",
              "The instruction names the button by its visible text 'Reservation abschliessen' (G96); no sensory characteristic is needed.",
              org="Gemeinde Ober-Beispielwil", diff="easy")


def p_named_controls_fr(rng):
    main = """<h1>Calendrier des collectes</h1>
<p id="consigne-quartier">Choisissez votre quartier dans la liste Quartier, puis cliquez sur Afficher les dates.</p>
<form action="collectes.html" method="get">
<label for="quartier">Quartier</label>
<select id="quartier" name="quartier"><option>Centre</option><option>Les Vignes</option><option>La Combe</option></select>
<p><button type="submit">Afficher les dates</button></p>
</form>"""
    return _c(rng, "fr", "passed", "1.3.3/P1", "Collectes", main, "#consigne-quartier",
              "Both controls are referred to by their visible label texts ('Quartier', 'Afficher les dates') (G96).",
              org="Commune d'Exempleval", diff="easy")


def p_named_button_it(rng):
    main = """<h1>Richiesta di un allacciamento idrico</h1>
<p id="istruzione-invio">Compila tutti i campi e premi «Invia richiesta». Riceverai una conferma per e-mail entro due giorni lavorativi.</p>
<form action="richiesta-inviata.html" method="post">
<label for="particella">Numero di particella</label>
<input id="particella" name="particella" type="text">
<label for="indirizzo-cantiere">Indirizzo del cantiere</label>
<input id="indirizzo-cantiere" name="indirizzo-cantiere" type="text">
<p><button type="submit">Invia richiesta</button></p>
</form>"""
    return _c(rng, "it", "passed", "1.3.3/P1", "Allacciamento idrico", main, "#istruzione-invio",
              "The instruction identifies the submit button by its visible label 'Invia richiesta' (G96).",
              org="Azienda acqua potabile Valfittizia", diff="easy")


def p_section_de(rng):
    main = """<h1>Hundehaltung</h1>
<p>Hunde müssen jedes Jahr bis zum 31. März bei der Gemeinde angemeldet werden.</p>
<p id="hinweis-tarife">Die Höhe der Hundetaxe finden Sie im Abschnitt Tarife.</p>
<h2>Anmeldung</h2>
<p>Bringen Sie den Heimtierausweis und den Nachweis der Haftpflichtversicherung mit.</p>
<h2>Tarife</h2>
<p>Erster Hund CHF 120.–, jeder weitere Hund CHF 160.–. Blindenführhunde sind von der Taxe befreit.</p>"""
    return _c(rng, "de", "passed", "1.3.3/P1", "Hundehaltung", main, "#hinweis-tarife",
              "The content is referenced by the text of its heading ('Abschnitt Tarife'), not by location or appearance.",
              org="Gemeinde Beispielwil", diff="easy")


def p_named_button_en(rng):
    main = """<h1>Book a dormitory bed</h1>
<form action="availability.html" method="get">
<label for="arrival">Arrival date</label>
<input id="arrival" name="arrival" type="date">
<label for="nights">Nights</label>
<input id="nights" name="nights" type="number" min="1" max="14" value="1">
<p id="booking-hint">Select your arrival date, then press Check availability.</p>
<p><button type="submit">Check availability</button></p>
</form>"""
    return _c(rng, "en", "passed", "1.3.3/P1", "Book a bed", main, "#booking-hint",
              "The instruction refers to the field and the button by their visible labels (G96).",
              org="Lake Fictal Hostel", diff="easy")


# traps --------------------------------------------------------------------

def t_location_plus_text_de(rng):
    css = (".navi{display:flex;justify-content:flex-end;margin-top:20px}"
           ".navi button{display:inline-flex;align-items:center;gap:6px}")
    main = f"""<h1>Tageskarte Gemeinde reservieren</h1>
<p class="muted">Schritt 1 von 2: Reisedatum</p>
<form action="tageskarte-schritt-2.html" method="get">
<label for="reisedatum">Reisedatum</label>
<input id="reisedatum" name="reisedatum" type="text" placeholder="TT.MM.JJJJ">
<label for="anzahl-karten">Anzahl Karten</label>
<select id="anzahl-karten" name="anzahl-karten"><option>1</option><option>2</option><option>3</option><option>4</option></select>
<p id="hinweis-unten-rechts">Klicken Sie unten rechts auf «Weiter», sobald alle Felder ausgefüllt sind.</p>
<div class="navi"><button type="submit">Weiter {icon_svg('arrow-right', 18)}</button></div>
</form>"""
    return _c(rng, "de", "passed", "1.3.3/T1", "Tageskarte reservieren", main, "#hinweis-unten-rechts",
              "The location 'unten rechts' is only an extra cue: the instruction also names the button by its visible text 'Weiter' (Understanding 1.3.3, Example 2).",
              org="Gemeinde Fiktal", css=css, trap=True, diff="medium")


def t_table_below_fr(rng):
    main = """<h1>Location du refuge forestier</h1>
<p>Le refuge des Écureuils peut accueillir 40 personnes. Il dispose d'une cheminée, d'une cuisine et de toilettes sèches.</p>
<p id="consigne-tableau">Les tarifs figurent dans le tableau ci-dessous.</p>
<table>
<caption>Tarifs de location du refuge</caption>
<tr><th scope="col">Durée</th><th scope="col">Habitants</th><th scope="col">Externes</th></tr>
<tr><th scope="row">Demi-journée</th><td>CHF 80.–</td><td>CHF 120.–</td></tr>
<tr><th scope="row">Journée</th><td>CHF 140.–</td><td>CHF 200.–</td></tr>
<tr><th scope="row">Week-end</th><td>CHF 250.–</td><td>CHF 360.–</td></tr>
</table>"""
    return _c(rng, "fr", "passed", "1.3.3/T2", "Refuge forestier", main, "#consigne-tableau",
              "'Ci-dessous' refers to the next item in reading order, which is the only table and has a caption; Understanding 1.3.3 accepts above/below references that match the reading sequence.",
              org="Commune de Valfictif", trap=True, diff="medium")


def t_colour_plus_text_it(rng):
    css = ".conferma{background:#2f7d3a;border-color:#2f7d3a}"
    main = """<h1>Prenotazione della sala multiuso</h1>
<p>Riepilogo: Sala multiuso, sabato 21 novembre 2026, dalle 14.00 alle 22.00. Prezzo: CHF 280.–.</p>
<p id="istruzione-verde">Premi il pulsante verde «Conferma prenotazione» per completare la procedura.</p>
<form action="prenotazione-confermata.html" method="post">
<p><button type="submit" class="conferma">Conferma prenotazione</button></p>
</form>"""
    return _c(rng, "it", "passed", "1.3.3/T1", "Sala multiuso", main, "#istruzione-verde",
              "Colour is mentioned, but the instruction also quotes the visible label 'Conferma prenotazione', so it does not rely solely on a sensory characteristic.",
              org="Comune di Esempiano", css=css, trap=True, diff="easy")


def t_asterisk_fr(rng):
    main = """<h1>Inscription au cours de premiers secours</h1>
<p id="consigne-asterisque">Tous les champs suivis d'un astérisque (*) doivent être remplis.</p>
<form action="inscription-cours.html" method="post">
<label for="nom-participant">Nom *</label>
<input id="nom-participant" name="nom-participant" type="text" autocomplete="family-name" required>
<label for="prenom-participant">Prénom *</label>
<input id="prenom-participant" name="prenom-participant" type="text" autocomplete="given-name" required>
<label for="remarque-cours">Remarque</label>
<textarea id="remarque-cours" name="remarque-cours" rows="3"></textarea>
<p><button type="submit">S'inscrire</button></p>
</form>"""
    return _c(rng, "fr", "passed", "1.3.3/T3", "Premiers secours", main, "#consigne-asterisque",
              "The asterisk is a text character inside the labels, named in the instruction; it is available to everyone as text, not a purely visual shape.",
              org="Club sportif d'Exempleval", trap=True, diff="medium")


def t_figure_above_it(rng):
    img = asset("scene-mountain-gita", scene("mountain", w=480, h=260, seed=7))
    main = f"""<h1>Gita sociale al Pizzo Fittizio</h1>
<figure>
<img src="{img}" alt="Panorama del Pizzo Fittizio con il sentiero di salita" width="480" height="260">
<figcaption>Figura 1 – Percorso della gita: partenza dai Monti di Valfittizia, salita in 3 ore.</figcaption>
</figure>
<p id="istruzione-figura">Il percorso è illustrato nella figura 1 qui sopra. Ritrovo alle 7.00 alla fermata Piazza Grande.</p>"""
    return _c(rng, "it", "passed", "1.3.3/T2", "Gita sociale", main, "#istruzione-figura",
              "'Qui sopra' matches the reading order and the figure is also identified by its caption number ('figura 1'), so the reference does not rely on location alone.",
              org="Società sportiva Valfittizia", trap=True, diff="medium")


def t_physical_de(rng):
    main = """<h1>Sammelstelle beim Werkhof</h1>
<p>Die Sammelstelle beim Werkhof an der Mühlegasse 5 ist rund um die Uhr zugänglich.</p>
<p id="container-glas">Der grüne Container für Altglas steht rechts vom Eingang des Werkhofs, die Kleidersammlung gleich daneben.</p>
<p>Bitte werfen Sie kein Glas zwischen 20.00 und 7.00 Uhr ein.</p>"""
    return _c(rng, "de", "inapplicable", "1.3.3/N1", "Sammelstelle", main, "#container-glas",
              "Colour and position describe a container in the physical world; this is not an instruction for understanding or operating web content, so 1.3.3 has no applicable instruction on the page.",
              org="Gemeinde Ober-Beispielwil", trap=True, diff="medium", box=False)


def t_physical_it(rng):
    main = """<h1>Ecocentro comunale</h1>
<p>L'ecocentro di Via ai Monti 6 è aperto il mercoledì dalle 13.30 alle 17.00 e il sabato dalle 8.00 alle 12.00.</p>
<p id="contenitori">Il contenitore blu a sinistra dell'entrata è riservato alla carta; quello grande in fondo al piazzale al vetro.</p>
<p>I rifiuti ingombranti si consegnano al personale.</p>"""
    return _c(rng, "it", "inapplicable", "1.3.3/N1", "Ecocentro", main, "#contenitori",
              "Colour, size and location describe physical containers on site, not web content to be operated; no instruction on the page is in scope of 1.3.3.",
              org="Comune di Esempiano", trap=True, diff="medium", box=False)


# ---------------------------------------------------------------------------
# cantTell
# ---------------------------------------------------------------------------

def c_hidden_name_de(rng):
    css = (".suchzeile{display:flex;justify-content:flex-end;gap:8px}.suchzeile button{padding:8px}")
    main = f"""<div class="suchzeile"><input type="search" aria-label="Suchbegriff" name="q"><button type="button" aria-label="Suchen">{icon_svg('search', 20)}</button></div>
<h1>Formulare und Merkblätter</h1>
<p>Hier finden Sie alle Formulare der Gemeindeverwaltung als PDF.</p>
<p id="hinweis-lupe">Sie finden ein bestimmtes Formular nicht? Klicken Sie oben rechts auf das Lupen-Symbol «Suchen».</p>"""
    return _c(rng, "de", "cantTell", "1.3.3/C1", "Formulare", main, "#hinweis-lupe",
              "Besides shape and location the instruction gives the name 'Suchen', but that text exists only as the button's aria-label, not visibly; whether a non-visible name suffices as textual identification is debatable.",
              org="Gemeinde Beispielwil", css=css, alt="failed", diff="hard")


def c_title_tooltip_fr(rng):
    css = (".barre{display:flex;justify-content:space-between;align-items:center}"
           ".barre .reglages{width:40px;height:40px;padding:0;display:flex;align-items:center;justify-content:center}")
    main = f"""<div class="barre"><h1>Mon compte e-guichet</h1>
<button type="button" class="reglages" title="Préférences">{GEAR}</button></div>
<p>Vous recevez actuellement un avis par e-mail pour chaque nouvelle facture.</p>
<p id="consigne-roue">Cliquez sur la roue dentée en haut de la page pour modifier vos préférences de notification.</p>"""
    return _c(rng, "fr", "cantTell", "1.3.3/C1", "Mon compte", main, "#consigne-roue",
              "The gear icon is named 'Préférences' only through a title tooltip (visible on hover); the instruction echoes that word, but whether a hover-only name counts as textual identification is unclear.",
              org="Ville de Bourg-Modèle", css=css, alt="failed", diff="hard")


def c_purpose_matches_fr(rng):
    css = ".suite{background:#1f4fd8;border-color:#1f4fd8;display:inline-flex;align-items:center;gap:6px}"
    main = f"""<h1>Demande de carte d'accès à la déchetterie</h1>
<p class="muted">Étape 2 sur 3 : vérification</p>
<p>Nom : Marc Modèle · Adresse : Chemin des Vignes 7 · Nombre de cartes : 1</p>
<p id="consigne-fleche">Si ces données sont exactes, cliquez sur la flèche bleue pour continuer.</p>
<form action="carte-etape-3.html" method="get"><p><button type="submit" class="suite">Continuer {icon_svg('arrow-right', 18)}</button></p></form>"""
    return _c(rng, "fr", "cantTell", "1.3.3/C2", "Carte d'accès", main, "#consigne-fleche",
              "The button is referred to by shape and colour ('flèche bleue'), and only the purpose phrase 'pour continuer' happens to match its visible label 'Continuer'; whether this counts as naming the control is debatable.",
              org="Commune d'Exempleval", css=css, diff="hard")


def c_purpose_matches_it(rng):
    css = ".annulla{background:#b42318;border-color:#b42318}.azioni-pren{display:flex;gap:12px}"
    main = """<h1>La tua prenotazione</h1>
<p>Campo da tennis n. 2, giovedì 19 novembre 2026, dalle 18.00 alle 19.00.</p>
<p id="istruzione-rosso">Se non puoi venire, premi il pulsante rosso per annullare la prenotazione entro 24 ore.</p>
<div class="azioni-pren">
<form action="annullata.html" method="post"><button type="submit" class="annulla">Annulla</button></form>
<form action="modifica.html" method="get"><button type="submit">Modifica</button></form>
</div>"""
    return _c(rng, "it", "cantTell", "1.3.3/C2", "La tua prenotazione", main, "#istruzione-rosso",
              "The control is identified by colour ('pulsante rosso'); the purpose 'annullare' matches the visible label 'Annulla' only indirectly, so whether the instruction relies solely on colour is a judgement call.",
              org="Società sportiva Valfittizia", css=css, diff="hard")


SCENARIOS = [
    f_round_icon_fr, f_bottom_left_it, f_green_right_de, f_big_button_fr, f_sound_it, f_box_right_de,
    f_vertical_menu_it, f_star_de, f_map_corner_en, f_globe_fr,
    p_named_button_de, p_named_controls_fr, p_named_button_it, p_section_de, p_named_button_en,
    t_location_plus_text_de, t_table_below_fr, t_colour_plus_text_it, t_asterisk_fr, t_figure_above_it,
    t_physical_de, t_physical_it,
    c_hidden_name_de, c_title_tooltip_fr, c_purpose_matches_fr, c_purpose_matches_it,
]


def build(rng):
    return [fn(rng) for fn in SCENARIOS]
