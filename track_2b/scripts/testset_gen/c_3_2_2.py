"""3.2.2 On Input — selects, radios, checkboxes and segmented fields with inline change handlers."""
from __future__ import annotations

import json

from common import *  # noqa: F401,F403
from common import Case, esc, pick, pick_theme
from _operable_util import content_page, get_page, main_content, site_by_kind

CRITERION = "3.2.2"

CSS = ("form{max-width:620px}fieldset{border:1px solid #c9d3d8;border-radius:8px;margin:12px 0;padding:8px 14px 14px}"
       "button{margin-top:12px}.seg{display:flex;gap:8px;align-items:center}.seg input{width:4.5em}"
       ".seg label{display:inline;margin:0;font-weight:400}.inline label{display:inline;font-weight:400;margin-right:14px}"
       ".hint{color:#4f5b62;font-size:.95rem;margin:4px 0}")


def _opts(pairs, placeholder=None):
    out = f'<option value="">{esc(placeholder)}</option>' if placeholder else ""
    return out + "".join(f'<option value="{esc(v)}">{esc(t)}</option>' for v, t in pairs)


def _js(code):
    return f"<script>(function(){{{code}}})();</script>"


def _lay(rng):
    return pick(rng, ("top", "side", "band", "bare"))


def nav_select(sid, label, pairs, placeholder, *, before="", after="", described=False, new_window=False):
    desc = f' aria-describedby="{sid}-hinweis"' if described else ""
    act = "window.open(this.value,'_blank')" if new_window else "window.location.href=this.value"
    return (f'<div class="field">{before}<label for="{sid}">{esc(label)}</label>'
            f'<select id="{sid}" name="{sid}"{desc}>{_opts(pairs, placeholder)}</select>{after}</div>'
            + _js(f"document.getElementById('{sid}').addEventListener('change',function(){{if(this.value){{{act};}}}});"))


def segmented(gid, legend, n, size, labels, *, advance=True, before="", inputmode="numeric"):
    ins = "".join(f'<label class="vh" for="{gid}-{i + 1}">{esc(labels[i])}</label>'
                  f'<input id="{gid}-{i + 1}" name="{gid}-{i + 1}" maxlength="{size[i]}" size="{size[i]}" inputmode="{inputmode}">'
                  + ("<span aria-hidden=\"true\">–</span>" if i < n - 1 else "") for i in range(n))
    html = f'<fieldset id="{gid}"><legend>{esc(legend)}</legend>{before}<div class="seg">{ins}</div></fieldset>'
    if advance:
        html += _js(f"var f=document.querySelectorAll('#{gid} input');f.forEach(function(inp,i){{inp.addEventListener('input',function(){{"
                    "if(inp.value.length>=inp.maxLength&&f[i+1]){f[i+1].focus();}});});")
    return html


def build(rng):
    cases = []

    def add(lang, kind, slug, title, main, target, expected, rule, notes, *, trap=False, alt=None, diff="medium"):
        s = site_by_kind(lang, kind)
        pg = get_page(s, slug)
        html = content_page(s, pg, title, pick_theme(rng), _lay(rng), main_html=main, css=CSS)
        cases.append(Case(CRITERION, lang, expected, html=html, target=target, rule=rule, notes=notes,
                          trap=trap, alt_expected=alt, difficulty=diff))

    # ---------------- F1: select navigates -----------------
    main = ('<h1>Formulare und Merkblätter</h1><p>Die meisten Formulare können Sie online ausfüllen oder als Vorlage ausdrucken.</p>'
            + nav_select("schnellzugriff", "Schnellzugriff", [("formular-hund.html", "Hundeanmeldung"), ("formular-umzug.html", "Umzugsmeldung"),
                                                            ("formular-baugesuch.html", "Baugesuch"), ("merkblatt-kehricht.html", "Merkblatt Kehricht")],
                         "Bitte wählen …")
            + '<h2>Am häufigsten gesucht</h2><ul><li><a href="formular-umzug.html">Umzug melden</a></li>'
              '<li><a href="wohnsitzbestaetigung.html">Wohnsitzbestätigung bestellen</a></li></ul>')
    add("de", "municipality", "verwaltung", "Formulare – Gemeinde Beispielwil", main, "#schnellzugriff", "failed", "3.2.2/F1",
        "Choosing an entry in the 'Schnellzugriff' select immediately loads another page; there is no button and no prior notice.",
        diff="easy")

    s = site_by_kind("fr", "library")
    main = (main_content(get_page(s, "collections"))
            + '<aside class="box">' + nav_select("rubrique", "Aller à la rubrique", [("horaires.html", "Horaires"), ("inscription.html", "Inscription et tarifs"),
                                                                                      ("numerique.html", "Offre numérique"), ("animations.html", "Animations")],
                                                 "Choisir …") + "</aside>")
    add("fr", "library", "collections", "Nos collections – Bibliothèque de Bourg-Modèle", main, "#rubrique", "failed", "3.2.2/F1",
        "The 'Aller à la rubrique' select navigates to the chosen page as soon as its value changes, without warning.",
        diff="easy")

    main = ('<h1>Orari</h1><p>Il nuovo orario entra in vigore il 13 dicembre 2026.</p>'
            + nav_select("linea", "Orario della linea", [("orario-linea-1.html", "Linea 1 – Stazione ↔ Ospedale"),
                                                          ("orario-linea-2.html", "Linea 2 – Piazza Grande ↔ Lido"),
                                                          ("orario-linea-3.html", "Linea 3 – Stazione ↔ Monti"),
                                                          ("orario-linea-4.html", "Linea 4 – Stazione ↔ Ospedale via Centro")], "Scegliete una linea")
            + '<p>Gli orari sono validi dal lunedì al venerdì; nei giorni festivi vale l\'orario della domenica.</p>')
    add("it", "transport", "orari", "Orari – Trasporti pubblici di Modellina", main, "#linea", "failed", "3.2.2/F1",
        "Selecting a line in the select replaces the page with that line's timetable immediately (on change), with no advance description or button.",
        diff="easy")

    # ---------------- F2: radio / checkbox submits -----------------
    main = ('<h1>Ricerca nel catalogo</h1><form id="cat" action="catalogo-risultati.html" method="get">'
            '<label for="q">Titolo, autore o soggetto</label><input id="q" name="q" type="search">'
            '<fieldset id="supporto" class="inline"><legend>Tipo di supporto</legend>'
            '<label><input type="radio" name="s" value="tutti" checked> tutti</label><label><input type="radio" name="s" value="libri"> libri</label>'
            '<label><input type="radio" name="s" value="audio"> audiolibri</label><label><input type="radio" name="s" value="dvd"> DVD</label></fieldset>'
            '<button type="submit">Cerca</button></form>'
            + _js("var f=document.getElementById('cat');f.querySelectorAll('input[name=s]').forEach(function(r){"
                  "r.addEventListener('change',function(){f.submit();});});"))
    add("it", "library", "raccolte", "Catalogo – Biblioteca di Modellina", main, "#supporto", "failed", "3.2.2/F2",
        "Picking a media-type radio button submits the search form at once and loads the results page, although a 'Cerca' button exists.",
        diff="medium")

    s = site_by_kind("de", "transport")
    main = (main_content(get_page(s, "haltestellen"))
            + '<form id="haltestellen-filter" action="haltestellen-liste.html" method="get"><label class="inline">'
              '<input type="checkbox" id="stufenlos" name="stufenlos" value="1"> Nur stufenlos zugängliche Haltestellen</label></form>'
            + _js("var c=document.getElementById('stufenlos');c.addEventListener('change',function(){c.form.submit();});")
            + '<h2>Haltestellen A–Z</h2><ul><li>Bahnhof Beispielwil</li><li>Dorfplatz</li><li>Kirchweg</li><li>Schulhaus Matte</li><li>Seeweg</li></ul>')
    add("de", "transport", "haltestellen", "Haltestellen – Beispielwiler Verkehrsbetriebe", main, "#stufenlos", "failed", "3.2.2/F2",
        "Ticking the 'stufenlos' checkbox submits its form and loads a new page; nothing announces this beforehand.",
        diff="medium")

    # ---------------- F3: new window -----------------
    main = ('<h1>Inscription au camp de ski</h1><p>Le camp aura lieu du 8 au 12 février 2027 aux Mayens-Fictifs.</p>'
            '<form action="merci.html" method="post"><label for="enfant">Nom de l\'enfant</label><input id="enfant" name="enfant">'
            '<label for="taille">Taille de skis (cm)</label><input id="taille" name="taille" inputmode="numeric">'
            '<p class="inline"><label><input type="checkbox" id="reglement" name="reglement"> J\'ai pris connaissance du règlement du camp</label></p>'
            '<button type="submit">Envoyer</button></form>'
            + _js("document.getElementById('reglement').addEventListener('change',function(){if(this.checked){"
                  "window.open('reglement-camp.html','reglement','width=640,height=720');}});"))
    add("fr", "school", "parents", "Camp de ski – École de Valfictif", main, "#reglement", "failed", "3.2.2/F3",
        "Checking the 'règlement' box opens the regulations in a new window; launching a window on a checkbox change without warning is F37.",
        diff="medium")

    main = ('<h1>Elternbriefe</h1><p>Hier finden Sie die Elternbriefe des laufenden Schuljahres.</p>'
            + nav_select("elternbrief", "Elternbrief öffnen", [("elternbrief-august.html", "August 2026: Schulstart"),
                                                               ("elternbrief-september.html", "September 2026: Herbstwanderung"),
                                                               ("elternbrief-oktober.html", "Oktober 2026: Elterngespräche")],
                         "Brief auswählen", new_window=True)
            + '<p>Fragen zu den Briefen beantwortet das Schulsekretariat.</p>')
    add("de", "school", "eltern", "Elternbriefe – Schule Beispielberg", main, "#elternbrief", "failed", "3.2.2/F3",
        "Choosing a letter in the select opens it in a new browser window (window.open on change) with no prior warning.",
        diff="medium")

    # ---------------- F4: auto-advance without notice -----------------
    main = ('<h1>Relevé de compteur</h1><p>Vous avez reçu une carte de relevé ? Communiquez-nous l\'index de votre compteur.</p>'
            '<form action="merci.html" method="post">'
            + segmented("numero-client", "Numéro de client", 3, [4, 4, 4], ["Bloc 1", "Bloc 2", "Bloc 3"])
            + '<label for="index">Index du compteur (m³)</label><input id="index" name="index" inputmode="numeric">'
              '<button type="submit">Envoyer</button></form>')
    add("fr", "utility", "tarifs", "Relevé de compteur – Service des eaux d'Exempleval", main, "#numero-client", "failed", "3.2.2/F4",
        "Typing four digits moves focus to the next block automatically, and nothing before the fields announces this focus change.",
        diff="hard")

    main = ('<h1>Iscrizione online</h1><p>La tessera è gratuita fino ai 18 anni.</p><form action="grazie.html" method="post">'
            '<label for="nome">Nome e cognome</label><input id="nome" name="nome" autocomplete="name">'
            + segmented("nascita", "Data di nascita", 3, [2, 2, 4], ["Giorno", "Mese", "Anno"])
            + '<label for="mail">E-mail</label><input id="mail" name="mail" type="email" autocomplete="email">'
              '<button type="submit">Invia</button></form>')
    add("it", "library", "iscrizione", "Iscrizione – Biblioteca di Modellina", main, "#nascita", "failed", "3.2.2/F4",
        "The date-of-birth fields jump to the next field after 2/2/4 characters without any prior explanation; the focus move is a change of context.",
        diff="hard")

    # ---------------- F5: auto-submit on complete value -----------------
    main = ('<h1>Wasserhärte an Ihrem Wohnort</h1><p>Die Härte unterscheidet sich je nach Quelle. Geben Sie Ihre Postleitzahl ein.</p>'
            '<form id="haerte" action="haerte-ergebnis.html" method="get"><label for="plz">Postleitzahl</label>'
            '<input id="plz" name="plz" inputmode="numeric" maxlength="4" autocomplete="postal-code"></form>'
            + _js("var p=document.getElementById('plz');p.addEventListener('input',function(){if(/^[0-9]{4}$/.test(p.value)){p.form.submit();}});")
            + '<p>Alle Werte werden zweimal jährlich vom kantonalen Labor überprüft.</p>')
    add("de", "utility", "wasserqualitaet", "Wasserhärte – Wasserversorgung Fiktal", main, "#plz", "failed", "3.2.2/F5",
        "As soon as four digits are typed the form submits itself and a new page loads (F36).", diff="medium")

    # ---------------- P1: select + explicit button -----------------
    main = ('<h1>Fahrplan</h1><p>Der neue Fahrplan gilt ab 13. Dezember 2026.</p>'
            '<form action="fahrplan-linie.html" method="get"><label for="linie">Linie</label><select id="linie" name="linie">'
            + _opts([("1", "Linie 1 – Bahnhof ↔ Beispielberg"), ("2", "Linie 2 – Bahnhof ↔ Fiktal"), ("3", "Linie 3 – Bahnhof ↔ Spital Mustersee")])
            + '</select> <button type="submit">Fahrplan anzeigen</button></form>')
    add("de", "transport", "fahrplan", "Fahrplan – Beispielwiler Verkehrsbetriebe", main, "#linie", "passed", "3.2.2/P1",
        "The line select has no change handler; the timetable opens only when 'Fahrplan anzeigen' is pressed.", diff="easy")

    main = ('<h1>Horaires</h1><p>Le nouvel horaire entre en vigueur le 13 décembre 2026.</p>'
            '<form action="horaire-ligne.html" method="get"><label for="ligne">Ligne</label><select id="ligne" name="ligne">'
            + _opts([("1", "Ligne 1 – Gare ↔ Hôpital"), ("2", "Ligne 2 – Gare ↔ Zone artisanale des Prés"), ("4", "Ligne 4 – Gare ↔ Bourg-Modèle"),
                     ("5", "Ligne 5 – Gare ↔ Les Mayens-Fictifs")])
            + '</select> <button type="submit">Afficher l\'horaire</button></form>')
    add("fr", "transport", "horaires", "Horaires – Transports publics de Valfictif", main, "#ligne", "passed", "3.2.2/P1",
        "Choosing a line changes nothing by itself; the explicit 'Afficher l'horaire' button initiates navigation (H84).", diff="easy")

    main = ('<h1>Calendario della raccolta</h1><p>I giorni di raccolta variano secondo il quartiere.</p>'
            '<form action="calendario-quartiere.html" method="get"><label for="quartiere">Quartiere</label><select id="quartiere" name="q">'
            + _opts([("centro", "Centro"), ("ronco", "Ronco"), ("monti", "Monti"), ("lago", "Riva lago")])
            + '</select> <button type="submit">Mostra il calendario</button></form>')
    add("it", "municipality", "rifiuti", "Calendario della raccolta – Comune di Esempiano", main, "#quartiere", "passed", "3.2.2/P1",
        "The district select only takes effect when the 'Mostra il calendario' button is activated.", diff="easy")

    # ---------------- T1: same-page filtering -----------------
    ev = [("enfants", "Heure du conte", "mercredi 4 novembre, 15 h"), ("adultes", "Club de lecture", "jeudi 19 novembre, 19 h"),
          ("enfants", "Atelier BD", "samedi 28 novembre, 10 h"), ("adultes", "Rencontre avec Sophie Fictif", "vendredi 4 décembre, 20 h"),
          ("enfants", "Bricolage de Noël", "mercredi 16 décembre, 14 h")]
    lis = "".join(f'<li data-public="{p}"><strong>{esc(t)}</strong> – {esc(d)}</li>' for p, t, d in ev)
    main = ('<h1>Animations</h1><p>Toutes nos animations sont gratuites.</p><label for="public">Public</label>'
            '<select id="public">' + _opts([("tous", "Tous les publics"), ("enfants", "Enfants"), ("adultes", "Adultes")]) + '</select>'
            f'<p id="compte" role="status">5 animations</p><ul id="liste">{lis}</ul>'
            + _js("var s=document.getElementById('public');s.addEventListener('change',function(){var n=0;"
                  "document.querySelectorAll('#liste li').forEach(function(li){var ok=s.value==='tous'||li.getAttribute('data-public')===s.value;"
                  "li.hidden=!ok;if(ok){n+=1;}});document.getElementById('compte').textContent=n+(n>1?' animations':' animation');});"))
    add("fr", "library", "animations", "Animations – Bibliothèque de Bourg-Modèle", main, "#public", "passed", "3.2.2/T1",
        "Changing the audience select only filters the event list below and updates a status count; focus and page stay the same (SCR19).",
        trap=True, diff="medium")

    tours = [("facile", "Sentiero dei mulini", "2 ore"), ("media", "Via dei monti", "4 ore e 30"),
             ("impegnativa", "Traversata delle creste", "6 ore"), ("facile", "Giro dei grotti", "1 ora e 30")]
    lis = "".join(f'<li data-livello="{d}"><strong>{esc(n)}</strong> – {esc(t)}, {esc(d)}</li>' for d, n, t in tours)
    radios = "".join(f'<label><input type="radio" name="livello" value="{v}"{" checked" if v == "tutte" else ""}> {lab}</label>'
                     for v, lab in [("tutte", "tutte"), ("facile", "facili"), ("media", "medie"), ("impegnativa", "impegnative")])
    main = ('<h1>Escursioni</h1><p>Tutti i sentieri partono dalla piazza del paese.</p>'
            f'<fieldset id="filtro-livello" class="inline"><legend>Mostra le escursioni</legend>{radios}</fieldset>'
            f'<ul id="percorsi">{lis}</ul>'
            + _js("document.querySelectorAll('#filtro-livello input').forEach(function(r){r.addEventListener('change',function(){"
                  "document.querySelectorAll('#percorsi li').forEach(function(li){li.hidden=!(r.value==='tutte'||li.getAttribute('data-livello')===r.value);});});});"))
    add("it", "tourism", "escursioni", "Escursioni – Ente turistico Valfittizia", main, "#filtro-livello", "passed", "3.2.2/T1",
        "Selecting a difficulty radio hides non-matching hikes in the list on the same page; no navigation, no focus move.",
        trap=True, diff="medium")

    # ---------------- T2: advised navigation (G13) -----------------
    main = ('<h1>Abfuhrkalender</h1><p>Die Abfuhrtage unterscheiden sich je nach Ortsteil.</p>'
            + nav_select("ortsteil", "Ortsteil", [("abfuhr-dorf.html", "Dorf"), ("abfuhr-matte.html", "Matte"), ("abfuhr-oberdorf.html", "Oberdorf"),
                                                  ("abfuhr-seefeld.html", "Seefeld")], "Ortsteil wählen",
                         before='<p class="hint" id="ortsteil-hinweis">Nach der Auswahl wird sofort die Seite mit dem Kalender Ihres Ortsteils geöffnet.</p>',
                         described=True))
    add("de", "municipality", "abfall", "Abfuhrkalender – Gemeinde Beispielwil", main, "#ortsteil", "passed", "3.2.2/T2",
        "The select navigates on change, but a visible instruction before it (also referenced by aria-describedby) announces that the calendar page opens immediately (G13).",
        trap=True, diff="hard")

    main = ('<h1>Le nostre sedi</h1><p>La scuola ha tre sedi con orari e contatti propri.</p>'
            + nav_select("sede", "Sede", [("sede-centro.html", "Esempiano Centro"), ("sede-ronco.html", "Ronco"), ("sede-monti.html", "Monti")],
                         "Scegliete la sede",
                         before='<p class="hint" id="sede-hinweis">Attenzione: scegliendo una sede si apre subito la pagina corrispondente.</p>',
                         described=True))
    add("it", "school", "orari", "Sedi – Scuola di Esempiano", main, "#sede", "passed", "3.2.2/T2",
        "Navigation on change is announced by a warning placed before the select and linked with aria-describedby, so the user is advised beforehand.",
        trap=True, diff="hard")

    # ---------------- T3: expanding fields -----------------
    main = ('<h1>Neuer Hausanschluss</h1><p>Reichen Sie das Gesuch mindestens acht Wochen vor Baubeginn ein.</p>'
            '<form action="danke.html" method="post"><label for="liegenschaft">Adresse der Liegenschaft</label><input id="liegenschaft" name="liegenschaft">'
            '<label for="bauherr">Bauherrschaft</label><input id="bauherr" name="bauherr">'
            '<p class="inline"><label><input type="checkbox" id="abweichend" name="abweichend"> Rechnungsadresse weicht von der Liegenschaft ab</label></p>'
            '<fieldset id="rechnung" hidden><legend>Rechnungsadresse</legend><label for="r-name">Name</label><input id="r-name" name="r-name">'
            '<label for="r-adresse">Strasse, PLZ, Ort</label><input id="r-adresse" name="r-adresse"></fieldset>'
            '<button type="submit">Gesuch senden</button></form>'
            + _js("var c=document.getElementById('abweichend');c.addEventListener('change',function(){document.getElementById('rechnung').hidden=!c.checked;});"))
    add("de", "utility", "hausanschluss", "Hausanschluss – Wasserversorgung Fiktal", main, "#abweichend", "passed", "3.2.2/T3",
        "Checking the box only reveals the billing-address fieldset right below it; focus stays on the checkbox and no page change occurs.",
        trap=True, diff="medium")

    main = ('<h1>Brochure « Val-Modèle 2027 »</h1><p>Notre brochure présente toutes les randonnées et les hébergements du val.</p>'
            '<form action="merci.html" method="post"><fieldset id="envoi" class="inline"><legend>Comment souhaitez-vous la recevoir ?</legend>'
            '<label><input type="radio" name="envoi" value="pdf" checked> par courriel (PDF)</label>'
            '<label><input type="radio" name="envoi" value="poste"> par la poste</label></fieldset>'
            '<label for="courriel">Courriel</label><input id="courriel" name="courriel" type="email">'
            '<div id="adresse-postale" hidden><label for="adr">Adresse postale</label><input id="adr" name="adr"></div>'
            '<button type="submit">Commander</button></form>'
            + _js("document.querySelectorAll('#envoi input').forEach(function(r){r.addEventListener('change',function(){"
                  "document.getElementById('adresse-postale').hidden=(r.value!=='poste');});});"))
    add("fr", "tourism", "office", "Commander la brochure – Office du tourisme du Val-Modèle", main, "#envoi", "passed", "3.2.2/T3",
        "Choosing 'par la poste' merely shows an address field in the same form; the context (page, focus, window) does not change.",
        trap=True, diff="medium")

    # ---------------- T4: advised auto-advance -----------------
    main = ('<h1>Zählerstand melden</h1><p>Sie finden die Kundennummer oben rechts auf Ihrer Wasserrechnung.</p>'
            '<form action="danke.html" method="post">'
            + segmented("kundennummer", "Kundennummer", 3, [4, 4, 4], ["Block 1", "Block 2", "Block 3"],
                        before='<p class="hint">Die Kundennummer besteht aus drei Blöcken à 4 Ziffern. Nach jeweils 4 Ziffern '
                               'springt der Cursor automatisch in das nächste Feld.</p>')
            + '<label for="stand">Zählerstand (m³)</label><input id="stand" name="stand" inputmode="numeric">'
              '<button type="submit">Senden</button></form>')
    add("de", "utility", "tarife", "Zählerstand melden – Wasserversorgung Fiktal", main, "#kundennummer", "passed", "3.2.2/T4",
        "The fields auto-advance like the failed variant, but an instruction placed before them describes the automatic jump (Understanding phone-number example, G13).",
        trap=True, diff="hard")

    # ---------------- C1: large replacement -----------------
    views = {
        "liste": "<h2>Unterkünfte als Liste</h2><ul><li>Hotel Bergsee – 32 Zimmer</li><li>Gasthaus Krone – 12 Zimmer</li>"
                 "<li>Ferienwohnung Lärchenhof – 4 Wohnungen</li><li>Alphütte Obermatt – Matratzenlager</li></ul>",
        "kalender": "<h2>Verfügbarkeit im Dezember</h2><table><thead><tr><th scope=\"col\">Betrieb</th><th scope=\"col\">1.–14.12.</th>"
                    "<th scope=\"col\">15.–31.12.</th></tr></thead><tbody><tr><th scope=\"row\">Hotel Bergsee</th><td>frei</td><td>ausgebucht</td></tr>"
                    "<tr><th scope=\"row\">Gasthaus Krone</th><td>frei</td><td>frei</td></tr></tbody></table>",
        "karte": "<h2>Unterkünfte auf der Karte</h2><p>Hotel Bergsee: am Seeufer, 10 Minuten vom Dorfplatz. Gasthaus Krone: Dorfplatz. "
                 "Ferienwohnung Lärchenhof: Weiler Lärchen, 2 km. Alphütte Obermatt: 1650 m ü. M., nur zu Fuss.</p>",
    }
    main = ('<h1>Unterkünfte</h1><label for="ansicht">Ansicht</label><select id="ansicht">'
            + _opts([("liste", "Liste"), ("kalender", "Verfügbarkeitskalender"), ("karte", "Lageplan")]) + '</select>'
            f'<div id="ansicht-inhalt">{views["liste"]}</div><p><a href="unterkunft-anfragen.html">Unterkunft anfragen</a></p>'
            + _js("var V=" + json.dumps(views, ensure_ascii=False) + ";var s=document.getElementById('ansicht');"
                  "s.addEventListener('change',function(){document.getElementById('ansicht-inhalt').innerHTML=V[s.value];});"))
    add("de", "tourism", "unterkuenfte", "Unterkünfte – Verkehrsverein Ober-Beispielwil", main, "#ansicht", "cantTell", "3.2.2/C1",
        "Changing the view replaces the whole content block (list, availability table or location text, with a new heading) without moving focus; content change or significant rearrangement is debatable.",
        diff="hard")

    forms = {
        "particulier": "<h2>Raccordement d'une habitation</h2><label for=\"p-nom\">Nom et prénom</label><input id=\"p-nom\" name=\"p-nom\">"
                       "<label for=\"p-adresse\">Adresse du bien-fonds</label><input id=\"p-adresse\" name=\"p-adresse\">",
        "entreprise": "<h2>Raccordement d'un bâtiment professionnel</h2><label for=\"e-raison\">Raison sociale</label><input id=\"e-raison\" name=\"e-raison\">"
                      "<label for=\"e-ide\">Numéro IDE</label><input id=\"e-ide\" name=\"e-ide\"><label for=\"e-debit\">Débit de pointe estimé (l/min)</label>"
                      "<input id=\"e-debit\" name=\"e-debit\" inputmode=\"numeric\"><label for=\"e-adresse\">Adresse du site</label><input id=\"e-adresse\" name=\"e-adresse\">",
    }
    main = ('<h1>Demande de raccordement</h1><form action="merci.html" method="post"><fieldset id="profil" class="inline"><legend>Vous êtes</legend>'
            '<label><input type="radio" name="profil" value="particulier" checked> un particulier</label>'
            '<label><input type="radio" name="profil" value="entreprise"> une entreprise</label></fieldset>'
            f'<div id="formulaire-profil">{forms["particulier"]}</div><button type="submit">Envoyer la demande</button></form>'
            + _js("var F=" + json.dumps(forms, ensure_ascii=False) + ";document.querySelectorAll('#profil input').forEach(function(r){"
                  "r.addEventListener('change',function(){document.getElementById('formulaire-profil').innerHTML=F[r.value];});});"))
    add("fr", "utility", "raccordement", "Demande de raccordement – Service des eaux d'Exempleval", main, "#profil", "cantTell", "3.2.2/C1",
        "Switching the profile radio swaps the whole form body for a different form with its own heading; whether that is a change of context is a judgement call.",
        diff="hard")

    # ---------------- C2: notice after the control -----------------
    main = ('<h1>Rifiuti e riciclaggio</h1><p>I giorni di raccolta cambiano secondo il quartiere.</p>'
            + nav_select("zona", "Quartiere", [("rifiuti-centro.html", "Centro"), ("rifiuti-ronco.html", "Ronco"), ("rifiuti-monti.html", "Monti")],
                         "Scegliete …", after='<p class="hint">La pagina del quartiere si apre automaticamente dopo la scelta.</p>'))
    add("it", "municipality", "rifiuti", "Rifiuti – Comune di Esempiano", main, "#zona", "cantTell", "3.2.2/C2",
        "The select navigates on change; the only notice is a hint printed after the control and not associated with it, so whether users are advised before use is disputed.",
        diff="hard")

    main = ('<h1>Medienangebot</h1><p>Durchsuchen Sie unseren Bestand.</p><form id="bestand" action="katalog.html" method="get">'
            '<label for="such">Suchbegriff</label><input id="such" name="q" type="search"><button type="submit">Suchen</button>'
            '<p class="inline"><label><input type="checkbox" id="verfuegbar" name="verfuegbar" value="1"> Nur verfügbare Medien</label></p>'
            '<p class="hint">Hinweis: Beim Anklicken wird die Trefferliste neu geladen.</p></form>'
            + _js("var c=document.getElementById('verfuegbar');c.addEventListener('change',function(){c.form.submit();});"))
    add("de", "library", "medien", "Medienangebot – Bibliothek Mustersee", main, "#verfuegbar", "cantTell", "3.2.2/C2",
        "Ticking the checkbox reloads the result page; a hint explains this but only after the checkbox and without programmatic association.",
        diff="hard")

    return cases
