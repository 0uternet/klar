"""2.4.3 Focus Order — tabindex, CSS reordering, dialogs/menus and inserted content (inline JS)."""
from __future__ import annotations

from common import *  # noqa: F401,F403
from common import Case, esc, pick, pick_theme
from _operable_util import (UI, brand, content_page, footer_simple, get_page, main_content, nav_block, nav_items,
                            site_by_kind, site_doc, skip_link)

CRITERION = "2.4.3"

FORM_CSS = ("form{max-width:620px}fieldset{border:1px solid #c9d3d8;border-radius:8px;margin:12px 0;padding:8px 14px 14px}"
            "button{margin-top:14px}textarea{width:100%;box-sizing:border-box}")
OVERLAY_CSS = (".overlay{position:fixed;inset:0;background:rgba(0,0,0,.45);display:flex;align-items:center;justify-content:center;z-index:30}"
               ".overlay[hidden]{display:none}.overlay .panel{background:#ffffff;color:#1d2327;border-radius:10px;padding:20px;max-width:420px;width:90%}"
               "dialog{border:0;border-radius:10px;padding:20px;max-width:420px}dialog::backdrop{background:rgba(0,0,0,.45)}")


def _f(fid, label, typ="text", extra=""):
    t = "" if typ == "text" else f' type="{typ}"'
    return f'<label for="{fid}">{esc(label)}</label><input id="{fid}" name="{fid}"{t}{extra}>'


def _ta(fid, label, rows=4, extra=""):
    return f'<label for="{fid}">{esc(label)}</label><textarea id="{fid}" name="{fid}" rows="{rows}"{extra}></textarea>'


def _lay(rng):
    return pick(rng, ("top", "side", "band"))


def build(rng):
    cases = []

    def add(lang, expected, html, target, rule, notes, *, trap=False, alt=None, diff="medium"):
        cases.append(Case(CRITERION, lang, expected, html=html, target=target, rule=rule, notes=notes,
                          trap=trap, alt_expected=alt, difficulty=diff))

    # ---------------- F1: positive tabindex, illogical -----------------
    s = site_by_kind("de", "municipality")
    form = ('<h1>Kontakt</h1><p>Schreiben Sie uns – wir antworten innert zwei Arbeitstagen.</p>'
            '<form id="kontaktformular" action="danke.html" method="post">'
            + _f("name", "Name, Vorname", extra=' autocomplete="name"') + _f("mail", "E-Mail", "email", ' autocomplete="email"')
            + '<label for="thema">Thema</label><select id="thema" name="thema"><option>Allgemeine Anfrage</option>'
              '<option>Einwohnerdienste</option><option>Bauverwaltung</option><option>Steuern</option></select>'
            + _ta("nachricht", "Ihre Nachricht", 6)
            + '<button type="submit" id="senden" tabindex="1">Nachricht senden</button></form>')
    add("de", "failed", content_page(s, get_page(s, "verwaltung"), "Kontakt – Gemeinde Beispielwil", pick_theme(rng), _lay(rng),
                                    main_html=form, css=FORM_CSS),
        "#senden", "2.4.3/F1",
        "tabindex=1 on the submit button makes it the first stop on the page, before the navigation and before the fields it submits.",
        diff="easy")

    s = site_by_kind("fr", "school")
    ui = UI["fr"]
    pg = get_page(s, "horaires")
    foot = (f'<footer class="site-footer"><p>{esc(s["org"])} · {esc(s["street"])}</p><nav class="foot-links" aria-label="{esc(ui["footer_nav"])}">'
            '<ul><li><a href="mentions-legales.html">Mentions légales</a></li><li><a href="plan-du-site.html" id="plan-site" tabindex="1">Plan du site</a></li>'
            '<li><a href="accessibilite.html">Accessibilité</a></li></ul></nav></footer>')
    top = [skip_link("fr"), f'<header class="site-header">{brand(s["org"])}{nav_block(nav_items(s), ui["nav"], current="horaires.html")}</header>']
    main = main_content(pg) + '<h2>Arrivées tardives</h2><p>Les élèves qui arrivent après 8 h 05 se présentent au secrétariat.</p>'
    add("fr", "failed", site_doc("fr", "Horaires des cours – École de Valfictif", pick_theme(rng), top=top, main=main, bottom=[foot]),
        "#plan-site", "2.4.3/F1",
        "The footer link 'Plan du site' has tabindex=1, so it receives focus first, before the skip link, the navigation and the content.",
        diff="easy")

    s = site_by_kind("it", "library")
    form = ('<h1>Iscrizione online</h1><p>Compilate il modulo: la tessera vi aspetterà al bancone.</p>'
            '<form id="iscrizione" action="grazie.html" method="post">'
            + _f("nome", "Nome", extra=' tabindex="1" autocomplete="given-name"')
            + _f("cognome", "Cognome", extra=' tabindex="3" autocomplete="family-name"')
            + _f("via", "Via e numero", extra=' tabindex="4" autocomplete="street-address"')
            + _f("cap", "CAP", extra=' tabindex="2" inputmode="numeric" autocomplete="postal-code"')
            + _f("localita", "Località", extra=' tabindex="5" autocomplete="address-level2"')
            + _f("email", "E-mail", "email", ' tabindex="6" autocomplete="email"')
            + '<button type="submit" tabindex="7">Invia l\'iscrizione</button></form>')
    add("it", "failed", content_page(s, get_page(s, "iscrizione"), "Iscrizione online – Biblioteca di Modellina", pick_theme(rng),
                                    _lay(rng), main_html=form, css=FORM_CSS),
        "#iscrizione", "2.4.3/F1",
        "Positive tabindex values send focus from Nome to CAP, then back to Cognome and Via, which breaks the visual and logical sequence of the address.",
        diff="medium")

    s = site_by_kind("de", "transport")
    css = FORM_CSS + ".zwei{display:grid;grid-template-columns:1fr 1fr;gap:20px}"
    def grp(legend, pre, base):
        return (f'<fieldset><legend>{legend}</legend>'
                + _f(f"{pre}-name", "Name, Vorname", extra=f' tabindex="{base}"')
                + _f(f"{pre}-strasse", "Strasse, Nr.", extra=f' tabindex="{base + 2}"')
                + _f(f"{pre}-plz", "PLZ", extra=f' tabindex="{base + 4}" inputmode="numeric"')
                + _f(f"{pre}-ort", "Ort", extra=f' tabindex="{base + 6}"') + "</fieldset>")
    form = ('<h1>Jahresabo bestellen</h1><p>Das Jahresabo Zone 10 kostet CHF 680.– und wird per Post zugestellt.</p>'
            '<form id="abo-bestellung" action="bestaetigung.html" method="post"><div class="zwei">'
            + grp("Rechnungsadresse", "re", 1) + grp("Lieferadresse", "li", 2)
            + '</div><button type="submit" tabindex="9">Bestellung absenden</button></form>')
    add("de", "failed", content_page(s, get_page(s, "billette"), "Jahresabo bestellen – Beispielwiler Verkehrsbetriebe",
                                    pick_theme(rng), _lay(rng), main_html=form, css=css),
        "#abo-bestellung", "2.4.3/F1",
        "tabindex values alternate between the billing and delivery fieldsets (Name billing, Name delivery, Street billing …), so focus never completes one address group.",
        diff="hard")

    # ---------------- F2: dialogs / menus at end of DOM, focus not moved -----------------
    s = site_by_kind("fr", "municipality")
    main = ('<h1>Salle communale</h1><p>La salle communale accueille jusqu\'à 120 personnes. Location : CHF 250.– le week-end, '
            'nettoyage compris.</p><p><button type="button" id="ouvrir-resa">Réserver la salle</button></p>'
            '<h2>Équipement</h2><ul><li>Cuisine équipée</li><li>Sonorisation</li><li>Tables et chaises pour 120 personnes</li></ul>'
            '<p><a href="reglement-salle.html">Règlement d\'utilisation</a></p>')
    dlg = ('<div class="overlay" id="reservation" hidden><div class="panel" role="dialog" aria-labelledby="resa-h">'
           '<h2 id="resa-h">Réserver la salle communale</h2><form action="reservation-envoyee.html" method="post">'
           + _f("resa-date", "Date souhaitée", "date") + '<label for="resa-type">Type de manifestation</label>'
             '<select id="resa-type" name="resa-type"><option>Fête privée</option><option>Assemblée</option><option>Concert</option></select>'
             '<button type="submit">Envoyer</button> <button type="button" id="fermer-resa">Annuler</button></form></div></div>'
           "<script>(function(){var o=document.getElementById('reservation');"
           "document.getElementById('ouvrir-resa').addEventListener('click',function(){o.hidden=false;});"
           "document.getElementById('fermer-resa').addEventListener('click',function(){o.hidden=true;});})();</script>")
    html = content_page(s, get_page(s, "administration"), "Salle communale – Commune de Valfictif", pick_theme(rng), _lay(rng),
                        main_html=main, css=OVERLAY_CSS + FORM_CSS)
    html = html.replace("</body>", dlg + "\n</body>")
    add("fr", "failed", html, "#reservation", "2.4.3/F2",
        "The booking overlay is the last element of the body and is shown without moving focus; after pressing the button, Tab goes through the rest of the page and footer before reaching it.",
        diff="medium")

    s = site_by_kind("it", "library")
    main = (main_content(get_page(s, "eventi")) + '<p><button type="button" id="apri-news">Iscriviti alla newsletter</button></p>'
            '<h2>Archivio</h2><p><a href="eventi-2025.html">Eventi del 2025</a></p>')
    dlg = ('<div class="overlay" id="newsletter" hidden><div class="panel" role="dialog" aria-labelledby="nl-h">'
           '<h2 id="nl-h">Newsletter della biblioteca</h2><p>Una mail al mese con novità ed eventi.</p>'
           '<form action="newsletter-ok.html" method="post">' + _f("nl-mail", "Indirizzo e-mail", "email")
           + '<button type="submit">Iscrivimi</button> <button type="button" id="chiudi-news">Chiudi</button></form></div></div>'
           "<script>(function(){var o=document.getElementById('newsletter');"
           "document.getElementById('apri-news').addEventListener('click',function(){o.hidden=false;});"
           "document.getElementById('chiudi-news').addEventListener('click',function(){o.hidden=true;});})();</script>")
    html = content_page(s, get_page(s, "eventi"), "Eventi – Biblioteca di Modellina", pick_theme(rng), _lay(rng),
                        main_html=main, css=OVERLAY_CSS + FORM_CSS)
    html = html.replace("</body>", dlg + "\n</body>")
    add("it", "failed", html, "#newsletter", "2.4.3/F2",
        "The newsletter dialog is appended at the end of the DOM and opened without focus management, so keyboard users must tab through the whole page to reach it.",
        diff="medium")

    s = site_by_kind("de", "transport")
    ui = UI["de"]
    css = ("#megamenu{position:absolute;top:64px;left:0;right:0;background:#ffffff;border-bottom:3px solid #2b2f3a;"
           "padding:16px 24px;display:grid;grid-template-columns:repeat(3,1fr);gap:16px;z-index:25}#megamenu[hidden]{display:none}"
           "#megamenu ul{list-style:none;padding:0}.menu-btn{background:transparent;border:2px solid currentColor}")
    hdr = (f'<header class="site-header">{brand(s["org"])}<button type="button" class="menu-btn" id="menu-knopf" '
           'aria-expanded="false" aria-controls="megamenu">Menü</button></header>')
    main = main_content(get_page(s, "fahrplan")) + (
        '<h2>Fahrplanauskunft</h2><p><a href="fahrplan-linie-1.html">Linie 1</a> · <a href="fahrplan-linie-2.html">Linie 2</a> · '
        '<a href="fahrplan-linie-3.html">Linie 3</a></p>')
    mm = ('<div id="megamenu" hidden><div><h2>Unterwegs</h2><ul><li><a href="fahrplan.html">Fahrplan</a></li>'
          '<li><a href="haltestellen.html">Haltestellen</a></li><li><a href="nachtbus.html">Nachtbus</a></li></ul></div>'
          '<div><h2>Billette</h2><ul><li><a href="billette.html">Billette und Abos</a></li><li><a href="fundbuero.html">Fundbüro</a></li></ul></div>'
          '<div><h2>Über uns</h2><ul><li><a href="unternehmen.html">Unternehmen</a></li><li><a href="kontakt.html">Kontakt</a></li></ul></div></div>'
          "<script>(function(){var b=document.getElementById('menu-knopf');var m=document.getElementById('megamenu');"
          "b.addEventListener('click',function(){var o=m.hidden;m.hidden=!o;b.setAttribute('aria-expanded',o?'true':'false');});})();</script>")
    html = site_doc("de", "Fahrplan – Beispielwiler Verkehrsbetriebe", pick_theme(rng), top=[skip_link("de"), hdr], main=main,
                    bottom=[footer_simple(s), mm], css=css)
    add("de", "failed", html, "#megamenu", "2.4.3/F2",
        "The 'Menü' button opens a mega-menu that is positioned under the header but stored after the footer; focus stays on the button and the menu links come last in the tab order.",
        diff="hard")

    # ---------------- F3: CSS reordering of form fields -----------------
    s = site_by_kind("de", "municipality")
    css = FORM_CSS + ("#umzug .felder{display:grid;grid-template-columns:1fr 1fr;gap:4px 18px}"
                      "#umzug .felder>div:nth-child(1){order:1}#umzug .felder>div:nth-child(2){order:5}"
                      "#umzug .felder>div:nth-child(3){order:2}#umzug .felder>div:nth-child(4){order:6}"
                      "#umzug .felder>div:nth-child(5){order:3}#umzug .felder>div:nth-child(6){order:4}")
    fl = [("vorname", "Vorname"), ("plz", "Neue PLZ"), ("nachname", "Nachname"), ("ort", "Neuer Wohnort"),
          ("strasse", "Neue Strasse"), ("hausnr", "Hausnummer")]
    form = ('<h1>Umzug melden</h1><p>Melden Sie Ihren Wegzug spätestens 14 Tage nach dem Umzug.</p><form id="umzug" action="umzug-2.html" method="post">'
            '<div class="felder">' + "".join(f"<div>{_f(a, b)}</div>" for a, b in fl) + '</div>'
            + _f("datum", "Umzugsdatum", "date") + '<button type="submit">Weiter</button></form>')
    add("de", "failed", content_page(s, get_page(s, "verwaltung"), "Umzug melden – Gemeinde Beispielwil", pick_theme(rng), _lay(rng),
                                    main_html=form, css=css),
        "#umzug", "2.4.3/F3",
        "CSS 'order' shows the fields as Vorname|Nachname, Strasse|Nr., PLZ|Ort, but the DOM (focus) order is Vorname, PLZ, Nachname, Ort, Strasse, Nr.",
        diff="hard")

    s = site_by_kind("fr", "utility")
    css = FORM_CSS + ("#signalement{display:flex;flex-direction:column}#signalement .envoi{order:9;align-self:flex-start}"
                      "#signalement label,#signalement input,#signalement textarea{order:1}")
    form = ('<h1>Signaler une panne</h1><p>Urgence (fuite importante) : appelez le piquet au 024 000 33 44.</p>'
            '<form id="signalement" action="merci.html" method="post"><button type="submit" class="envoi">Envoyer le signalement</button>'
            + _ta("description", "Description du problème", 4) + _f("lieu", "Adresse concernée", extra=' autocomplete="street-address"')
            + _f("tel", "Téléphone pour vous rappeler", "tel", ' autocomplete="tel"') + '</form>')
    add("fr", "failed", content_page(s, get_page(s, "pannes"), "Signaler une panne – Service des eaux d'Exempleval", pick_theme(rng),
                                    _lay(rng), main_html=form, css=css),
        "#signalement", "2.4.3/F3",
        "The submit button is first in the DOM and moved to the bottom only visually with CSS order, so keyboard focus reaches 'Envoyer' before any field.",
        diff="medium")

    s = site_by_kind("it", "tourism")
    css = FORM_CSS + ("#prenotazione .griglia{display:grid;grid-template-columns:1fr 1fr;gap:4px 24px}"
                      "#prenotazione .c1{grid-column:1}#prenotazione .c2{grid-column:2}"
                      "#prenotazione .r1{grid-row:1}#prenotazione .r2{grid-row:2}#prenotazione .r3{grid-row:3}#prenotazione .r4{grid-row:4}")
    cells = [("c1 r1", "<h2>La visita</h2>"), ("c2 r1", "<h2>I vostri dati</h2>"),
             ("c1 r2", _f("data", "Data", "date")), ("c2 r2", _f("nome", "Nome e cognome", extra=' autocomplete="name"')),
             ("c1 r3", '<label for="ora">Ora</label><select id="ora" name="ora"><option>10.00</option><option>14.00</option><option>16.00</option></select>'),
             ("c2 r3", _f("telefono", "Telefono", "tel", ' autocomplete="tel"')),
             ("c1 r4", _f("persone", "Numero di persone", "number", ' min="1" max="25"')),
             ("c2 r4", _f("email", "E-mail", "email", ' autocomplete="email"'))]
    form = ('<h1>Visita guidata al mulino</h1><p>Ogni domenica da aprile a ottobre; prezzo CHF 12.–, bambini gratis.</p>'
            '<form id="prenotazione" action="conferma.html" method="post"><div class="griglia">'
            + "".join(f'<div class="{c}">{h}</div>' for c, h in cells) + '</div><button type="submit">Prenota</button></form>')
    add("it", "failed", content_page(s, get_page(s, "escursioni"), "Prenotare una visita guidata – Ente turistico Valfittizia",
                                    pick_theme(rng), _lay(rng), main_html=form, css=css),
        "#prenotazione", "2.4.3/F3",
        "Grid placement shows two columns (visit details | personal data) but the DOM interleaves them, so focus zigzags Data → Nome → Ora → Telefono …",
        diff="hard")

    # ---------------- P1: natural order -----------------
    s = site_by_kind("de", "library")
    form = ('<h1>Anschaffungsvorschlag</h1><p>Fehlt ein Buch in unserem Angebot? Schlagen Sie es uns vor.</p>'
            '<form id="vorschlag" action="danke.html" method="post">' + _f("titel", "Titel") + _f("autor", "Autorin / Autor")
            + '<label for="art">Medienart</label><select id="art" name="art"><option>Buch</option><option>Hörbuch</option>'
              '<option>E-Book</option><option>Spiel</option></select>'
            + _f("mail", "Ihre E-Mail (für die Rückmeldung)", "email", ' autocomplete="email"')
            + '<button type="submit">Vorschlag senden</button></form>')
    add("de", "passed", content_page(s, get_page(s, "medien"), "Anschaffungsvorschlag – Bibliothek Mustersee", pick_theme(rng),
                                    _lay(rng), main_html=form, css=FORM_CSS),
        "#vorschlag", "2.4.3/P1",
        "No tabindex and no CSS reordering: navigation, form fields and the submit button receive focus in their visual reading order.",
        diff="easy")

    s = site_by_kind("fr", "library")
    form = ('<h1>Inscription et tarifs</h1><p>L\'abonnement annuel coûte CHF 25.–. Il est gratuit jusqu\'à 18 ans.</p>'
            '<form id="abonnement" action="merci.html" method="post"><fieldset><legend>Vos coordonnées</legend>'
            + _f("prenom", "Prénom", extra=' autocomplete="given-name"') + _f("nom", "Nom", extra=' autocomplete="family-name"')
            + _f("adresse", "Adresse", extra=' autocomplete="street-address"') + _f("courriel", "Courriel", "email", ' autocomplete="email"')
            + '</fieldset><fieldset><legend>Abonnement</legend><label><input type="radio" name="abo" value="adulte" checked> Adulte (CHF 25.–)</label>'
              '<label><input type="radio" name="abo" value="jeune"> Jeune ou en formation (gratuit)</label></fieldset>'
            + '<button type="submit">S\'inscrire</button></form>')
    add("fr", "passed", content_page(s, get_page(s, "inscription"), "Inscription – Bibliothèque de Bourg-Modèle", pick_theme(rng),
                                    _lay(rng), main_html=form, css=FORM_CSS),
        "#abonnement", "2.4.3/P1",
        "The DOM order of the two fieldsets and the submit button matches the visual order; nothing alters the default focus sequence.",
        diff="easy")

    s = site_by_kind("it", "utility")
    form = ('<h1>Segnalare un guasto</h1><p>Per perdite importanti chiamate subito il picchetto allo 091 000 44 55.</p>'
            '<form id="guasto" action="grazie.html" method="post"><label for="tipo">Tipo di guasto</label><select id="tipo" name="tipo">'
            '<option>Perdita d\'acqua</option><option>Mancanza d\'acqua</option><option>Acqua torbida</option></select>'
            + _f("indirizzo", "Indirizzo", extra=' autocomplete="street-address"') + _ta("descrizione", "Descrizione", 4)
            + _f("telefono", "Telefono", "tel", ' autocomplete="tel"') + '<button type="submit">Invia la segnalazione</button></form>')
    add("it", "passed", content_page(s, get_page(s, "guasti"), "Segnalare un guasto – Azienda acqua potabile Valfittizia",
                                    pick_theme(rng), _lay(rng), main_html=form, css=FORM_CSS),
        "#guasto", "2.4.3/P1",
        "Focus follows the DOM, which matches the visual order of the form (type, address, description, phone, submit).",
        diff="easy")

    # ---------------- P2: content inserted after trigger -----------------
    s = site_by_kind("fr", "school")
    form = ('<h1>Inscription au camp de ski</h1><p>Le camp aura lieu du 8 au 12 février 2027. Participation : CHF 140.– par enfant.</p>'
            '<form id="inscription-camp" action="merci.html" method="post"><fieldset><legend>Enfant 1</legend>'
            + _f("e1-nom", "Nom et prénom") + _f("e1-classe", "Classe") + '</fieldset>'
            '<p><button type="button" id="ajout">Ajouter un enfant</button></p>'
            + _f("parent-tel", "Téléphone d\'un parent", "tel", ' autocomplete="tel"') + '<button type="submit">Envoyer l\'inscription</button></form>'
            "<script>(function(){var n=1;var b=document.getElementById('ajout');b.addEventListener('click',function(){n+=1;"
            "var fs=document.createElement('fieldset');var lg=document.createElement('legend');lg.textContent='Enfant '+n;fs.appendChild(lg);"
            "[['nom','Nom et prénom'],['classe','Classe']].forEach(function(f){var id='e'+n+'-'+f[0];var l=document.createElement('label');"
            "l.htmlFor=id;l.textContent=f[1];var i=document.createElement('input');i.id=id;i.name=id;fs.appendChild(l);fs.appendChild(i);});"
            "b.parentNode.insertAdjacentElement('afterend',fs);});})();</script>")
    add("fr", "passed", content_page(s, get_page(s, "parents"), "Inscription au camp de ski – École de Valfictif", pick_theme(rng),
                                    _lay(rng), main_html=form, css=FORM_CSS),
        "#inscription-camp", "2.4.3/P2",
        "'Ajouter un enfant' inserts the new fieldset directly after the button, so the next Tab moves into the added fields before the phone field.",
        diff="medium")

    # ---------------- T1: tabindex=0 widget -----------------
    s = site_by_kind("fr", "transport")
    times = ["5 h 42", "6 h 02", "6 h 22", "6 h 42", "7 h 02", "7 h 22", "7 h 42", "8 h 02", "8 h 32", "9 h 02", "9 h 32", "10 h 02"]
    stops = ["Gare", "Poste", "Collège", "Les Prés", "Zone artisanale"]
    rows = "".join(f'<tr><th scope="row">{st}</th>' + "".join(
        f"<td>{t[:-2]}{int(t[-2:]) + 3 * k:02d}</td>" for t in times) + "</tr>" for k, st in enumerate(stops))
    css = ("#horaire-ligne2{overflow-x:auto;border:1px solid #c9d3d8;border-radius:8px;margin:12px 0}"
           "#horaire-ligne2:focus{outline:3px solid #1f4fd8}#horaire-ligne2 table{white-space:nowrap}")
    main = (main_content(get_page(s, "horaires")) + '<h2>Ligne 2 – départs du matin</h2>'
            '<div id="horaire-ligne2" tabindex="0" role="region" aria-label="Horaire ligne 2, défilement horizontal">'
            f'<table><caption class="vh">Ligne 2, du lundi au vendredi</caption><tbody>{rows}</tbody></table></div>'
            '<p><a href="horaire-ligne-2.html">Horaire complet de la ligne 2</a></p>')
    add("fr", "passed", content_page(s, get_page(s, "horaires"), "Horaires – Transports publics de Valfictif", pick_theme(rng),
                                    _lay(rng), main_html=main, css=css),
        "#horaire-ligne2", "2.4.3/T1",
        "The scrollable timetable region has tabindex=0, which inserts it into the focus order at its DOM position between the heading and the following link.",
        trap=True, diff="medium")

    # ---------------- T2: tabindex=-1 on skip target -----------------
    s = site_by_kind("de", "school")
    pg = get_page(s, "tagesschule")
    html = content_page(s, pg, "Tagesschule – Schule Beispielberg", pick_theme(rng), _lay(rng),
                        main_html=main_content(pg) + '<p><a href="anmeldung-tagesschule.html">Zur Anmeldung</a></p>')
    html = html.replace('<main id="main">', '<main id="main" tabindex="-1">')
    add("de", "passed", html, "#main", "2.4.3/T2",
        "tabindex=-1 on <main> only lets the skip link move focus there programmatically; it does not add a stop to the sequential order.",
        trap=True, diff="medium")

    # ---------------- T3: CSS reorder of non-interactive content -----------------
    s = site_by_kind("it", "library")
    css = (".eventi{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:14px}"
           ".eventi li{display:flex;flex-direction:column-reverse;border:1px solid #c9d3d8;border-radius:8px;padding:10px}"
           ".eventi .data{font-weight:700;font-size:.9rem}")
    ev = [("Ora del racconto", "4 nov · 15.00", "ora-del-racconto.html"), ("Incontro con Giulia Fittizi", "19 nov · 20.00", "incontro-fittizi.html"),
          ("Laboratorio di fumetto", "28 nov · 10.00", "laboratorio-fumetto.html")]
    lis = "".join(f'<li><h2><a href="{h}">{esc(t)}</a></h2><p class="data">{esc(d)}</p></li>' for t, d, h in ev)
    main = ('<h1>Eventi</h1><p>Tutti gli eventi sono gratuiti.</p><ul class="eventi" id="lista-eventi">' + lis + "</ul>")
    add("it", "passed", content_page(s, get_page(s, "eventi"), "Eventi – Biblioteca di Modellina", pick_theme(rng), _lay(rng),
                                    main_html=main, css=css),
        "#lista-eventi", "2.4.3/T3",
        "CSS column-reverse only shows each date badge above its title; every card holds a single link and the cards keep their DOM order, so focus order is unaffected.",
        trap=True, diff="medium")

    # ---------------- T4: modal dialog at end of DOM with focus management -----------------
    s = site_by_kind("it", "municipality")
    main = ('<h1>Appuntamenti allo sportello</h1><p>Per i documenti d\'identità e le notifiche di arrivo vi preghiamo di prenotare.</p>'
            '<p><button type="button" id="apri-app">Prenota un appuntamento</button></p>'
            '<h2>Documenti necessari</h2><ul><li>Documento d\'identità valido</li><li>Fotografia recente</li><li>Contratto di locazione</li></ul>')
    dlg = ('<dialog id="appuntamento" aria-labelledby="app-h"><h2 id="app-h">Prenota un appuntamento</h2>'
           '<form method="dialog">' + _f("app-giorno", "Giorno", "date")
           + '<label for="app-ora">Fascia oraria</label><select id="app-ora" name="app-ora"><option>8.30–9.30</option>'
             '<option>9.30–10.30</option><option>10.30–11.30</option></select>'
             '<button type="submit" value="ok">Conferma</button> <button type="submit" value="annulla">Annulla</button></form></dialog>'
           "<script>(function(){var d=document.getElementById('appuntamento');var b=document.getElementById('apri-app');"
           "b.addEventListener('click',function(){d.showModal();});d.addEventListener('close',function(){b.focus();});})();</script>")
    html = content_page(s, get_page(s, "amministrazione"), "Appuntamenti – Comune di Esempiano", pick_theme(rng), _lay(rng),
                        main_html=main, css=OVERLAY_CSS + FORM_CSS)
    html = html.replace("</body>", dlg + "\n</body>")
    add("it", "passed", html, "#appuntamento", "2.4.3/T4",
        "The dialog sits at the end of the DOM but is opened with showModal(), which moves focus into it, and focus returns to the trigger on close.",
        trap=True, diff="hard")

    s = site_by_kind("de", "school")
    main = ('<h1>Absenzen</h1><p>Melden Sie Absenzen Ihres Kindes bis 7.30 Uhr. Bei längeren Absenzen benötigen wir ein Arztzeugnis.</p>'
            '<p><button type="button" id="absenz-oeffnen">Absenz melden</button></p>'
            '<h2>Urlaubsgesuche</h2><p>Gesuche für Jokertage reichen Sie mindestens eine Woche im Voraus ein: '
            '<a href="jokertage.html">Jokertage</a>.</p>')
    dlg = ('<dialog id="absenz" aria-labelledby="absenz-h"><h2 id="absenz-h">Absenz melden</h2><form method="dialog">'
           + _f("abs-kind", "Name des Kindes") + _f("abs-klasse", "Klasse") + _f("abs-von", "Abwesend ab", "date")
           + '<label for="abs-grund">Grund</label><select id="abs-grund" name="abs-grund"><option>Krankheit</option>'
             '<option>Arzttermin</option><option>Anderes</option></select>'
             '<button type="submit" value="ok">Melden</button> <button type="submit" value="x">Abbrechen</button></form></dialog>'
           "<script>(function(){var d=document.getElementById('absenz');var b=document.getElementById('absenz-oeffnen');"
           "b.addEventListener('click',function(){d.showModal();});d.addEventListener('close',function(){b.focus();});})();</script>")
    html = content_page(s, get_page(s, "unterricht"), "Absenzen – Schule Beispielberg", pick_theme(rng), _lay(rng),
                        main_html=main, css=OVERLAY_CSS + FORM_CSS)
    html = html.replace("</body>", dlg + "\n</body>")
    add("de", "passed", html, "#absenz", "2.4.3/T4",
        "The absence dialog is placed after the footer, but showModal() moves focus to its first field and closing returns focus to the 'Absenz melden' button.",
        trap=True, diff="hard")

    # ---------------- T5: positive tabindex in a logical order -----------------
    t = pick_theme(rng)
    main = ('<h1>Zählerstand melden</h1><p>Sie waren bei der Ablesung nicht zu Hause? Melden Sie uns den Stand Ihres Wasserzählers '
            'bis 30. November 2026.</p><form id="zaehlerstand" action="danke.html" method="post">'
            + _f("zaehlernr", "Zählernummer (auf der Ablesekarte)", extra=' tabindex="1"')
            + _f("stand", "Zählerstand in m³", extra=' tabindex="2" inputmode="numeric"')
            + _f("ablesedatum", "Ablesedatum", "date", ' tabindex="3"')
            + _f("mail", "E-Mail für Rückfragen", "email", ' tabindex="4" autocomplete="email"')
            + '<button type="submit" tabindex="5">Zählerstand senden</button></form>'
            '<p class="muted">Wasserversorgung Fiktal · Mühlegasse 5, 3996 Fiktal · Telefon 032 000 55 60</p>')
    html = site_doc("de", "Zählerstand melden – Wasserversorgung Fiktal", t, main=main, css=FORM_CSS)
    add("de", "passed", html, "#zaehlerstand", "2.4.3/T5",
        "All five controls carry positive tabindex values numbered in visual order and the page has no other focusable element, so the order is fully logical.",
        trap=True, diff="hard")

    # ---------------- C1: side block visually first, DOM after -----------------
    s = site_by_kind("it", "library")
    css = (".duo{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,2fr);grid-template-areas:'cat testo';gap:24px}"
           ".duo .testo{grid-area:testo}#catalogo{grid-area:cat;align-self:start}")
    main = ('<div class="duo"><div class="testo">' + main_content(get_page(s, "raccolte"))
            + '<p><a href="storia-regionale.html">Sezione di storia regionale</a> · <a href="caratteri-grandi.html">Libri in caratteri grandi</a></p></div>'
            '<aside id="catalogo" class="box"><h2>Catalogo</h2><form action="catalogo.html" method="get">'
            + _f("cat-q", "Titolo, autore o parola chiave", "search") + '<button type="submit">Cerca nel catalogo</button></form></aside></div>')
    add("it", "cantTell", content_page(s, get_page(s, "raccolte"), "Le nostre raccolte – Biblioteca di Modellina", pick_theme(rng),
                                      _lay(rng), main_html=main, css=css),
        "#catalogo", "2.4.3/C1",
        "The catalogue search box is shown left of the article but follows it in the DOM; both blocks are self-contained, so whether this cross-block order harms meaning is debatable.",
        diff="hard")

    s = site_by_kind("fr", "tourism")
    css = ("#corps{display:flex;flex-direction:column}#reserver{order:-1;margin-bottom:16px}")
    main = ('<div id="corps">' + main_content(get_page(s, "hebergement"))
            + '<p><a href="hotels.html">Hôtels</a> · <a href="chambres-hotes.html">Chambres d\'hôtes</a> · <a href="camping.html">Camping</a></p>'
            '<section id="reserver" class="box"><h2>Réservez votre séjour</h2><form action="disponibilites.html" method="get">'
            + _f("arrivee", "Arrivée", "date") + _f("nuits", "Nombre de nuits", "number", ' min="1" max="21"')
            + '<button type="submit">Voir les disponibilités</button></form></section></div>')
    add("fr", "cantTell", content_page(s, get_page(s, "hebergement"), "Hébergement – Office du tourisme du Val-Modèle",
                                      pick_theme(rng), _lay(rng), main_html=main, css=css),
        "#reserver", "2.4.3/C1",
        "The booking box is moved visually above the article with CSS order but comes after the article links in the focus order; the box is independent, so impact on meaning is a judgement call.",
        diff="hard")

    # ---------------- C2: unsolicited banner fixed at top, last in DOM -----------------
    s = site_by_kind("de", "utility")
    css = ("#hinweis-netz{position:fixed;top:0;left:0;right:0;background:#fff4d6;color:#1d2327;border-bottom:2px solid #d4a017;"
           "padding:8px 24px;display:flex;gap:16px;align-items:center;z-index:30}body{padding-top:56px}")
    banner = ('<div id="hinweis-netz" role="region" aria-label="Hinweis"><p>Am 3. November 2026, 8.00–12.00 Uhr, ist die Wasserversorgung '
              'im Quartier Mühlematt unterbrochen.</p><a href="unterbruch-muehlematt.html">Details</a>'
              '<button type="button" id="hinweis-zu">Schliessen</button></div>'
              "<script>document.getElementById('hinweis-zu').addEventListener('click',function(){"
              "document.getElementById('hinweis-netz').hidden=true;document.body.style.paddingTop='0';});</script>")
    pg = get_page(s, "stoerungen")
    html = content_page(s, pg, "Störung melden – Wasserversorgung Fiktal", pick_theme(rng), _lay(rng),
                        main_html=main_content(pg) + '<p><a href="stoerungsmeldung.html">Online-Störungsmeldung</a></p>', css=css)
    html = html.replace("</body>", banner + "\n</body>")
    add("de", "cantTell", html, "#hinweis-netz", "2.4.3/C2",
        "An unsolicited notice banner is fixed at the top of the viewport but is the last element in the DOM, so its link and close button are reached only after the footer; F85 strictly covers triggered dialogs.",
        diff="hard")

    s = site_by_kind("it", "transport")
    css = ("#avviso-sciopero{position:fixed;top:0;left:0;right:0;background:#fde8e6;color:#1d2327;border-bottom:2px solid #c2453b;"
           "padding:8px 24px;display:flex;gap:16px;align-items:center;z-index:30}body{padding-top:56px}")
    banner = ('<div id="avviso-sciopero" role="region" aria-label="Avviso"><p>Giovedì 12 novembre possibili disagi sulle linee 1 e 4 '
              'per un\'assemblea del personale.</p><a href="disagi-12-novembre.html">Dettagli</a>'
              '<button type="button" id="avviso-chiudi">Chiudi</button></div>'
              "<script>document.getElementById('avviso-chiudi').addEventListener('click',function(){"
              "document.getElementById('avviso-sciopero').hidden=true;document.body.style.paddingTop='0';});</script>")
    pg = get_page(s, "orari")
    html = content_page(s, pg, "Orari – Trasporti pubblici di Modellina", pick_theme(rng), _lay(rng),
                        main_html=main_content(pg) + '<p><a href="orario-linea-4.html">Orario della linea 4</a></p>', css=css)
    html = html.replace("</body>", banner + "\n</body>")
    add("it", "cantTell", html, "#avviso-sciopero", "2.4.3/C2",
        "The service-disruption banner appears fixed at the top but sits after the footer in the DOM; for an unsolicited banner it is disputed whether this breaks the focus order.",
        diff="hard")

    return cases
