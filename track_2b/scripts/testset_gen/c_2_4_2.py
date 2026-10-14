"""2.4.2 Page Titled — page-level cases built from the hand-written mini-site library."""
from __future__ import annotations

from common import *  # noqa: F401,F403
from common import Case, esc, pick, pick_theme
from _operable_util import (LAYOUTS, content_page, get_page, main_content, site_by_kind)

CRITERION = "2.4.2"

FORM_CSS = "form{max-width:560px}fieldset{border:1px solid #c9d3d8;border-radius:8px;margin:12px 0}button{margin-top:16px}"


def _layout(rng):
    return pick(rng, LAYOUTS)


def build(rng):
    cases = []

    def add(lang, expected, kind, slug, title, rule, notes, *, trap=False, alt=None, diff="medium",
            main_html=None, css="", layout=None):
        site = site_by_kind(lang, kind)
        pg = get_page(site, slug) if slug else None
        if pg is None:
            pg = {"slug": "x", "nav": "", "h1": "", "p": [], "li": []}
        html = content_page(site, pg, title, pick_theme(rng), layout or _layout(rng), main_html=main_html, css=css)
        cases.append(Case(CRITERION, lang, expected, html=html, target=None, rule=rule, notes=notes,
                          trap=trap, alt_expected=alt, difficulty=diff))

    # ---------------- failed -----------------
    add("de", "failed", "municipality", "abfall", None, "2.4.2/F1",
        "The document has no title element at all, so the waste-collection page has no title describing it.", diff="easy")
    add("it", "failed", "library", "orari", None, "2.4.2/F1",
        "The opening-hours page of the library has no title element.", diff="easy")
    add("fr", "failed", "school", "horaires", "", "2.4.2/F2",
        "The title element exists but is empty, so the school-hours page has no title text.", diff="easy")
    add("de", "failed", "transport", "billette", "   ", "2.4.2/F2",
        "The title element contains only spaces; the ticket-prices page is effectively untitled.", diff="easy")
    add("it", "failed", "transport", "fermate", "Senza titolo", "2.4.2/F3",
        "'Senza titolo' is an editor placeholder that does not describe the bus-stop accessibility page.", diff="easy")
    add("fr", "failed", "utility", "tarifs", "Nouvelle page", "2.4.2/F3",
        "'Nouvelle page' is a CMS default title and says nothing about the water tariffs shown on the page.", diff="easy")
    add("de", "failed", "utility", "tarife", "Wasserversorgung Fiktal", "2.4.2/F4",
        "The tariffs page is titled only with the utility's name, which does not describe this inner page's topic (tariffs 2026).",
        diff="medium")
    add("fr", "failed", "library", "inscription", "Bibliothèque de Bourg-Modèle", "2.4.2/F4",
        "The registration-and-fees page uses only the library name as title, identical to the site name, and does not describe the page.",
        diff="medium")
    add("it", "failed", "municipality", "imposte", "Rifiuti e riciclaggio – Comune di Esempiano", "2.4.2/F5",
        "The page is about taxes (dichiarazione d'imposta) but the title, copied from another page, announces waste and recycling.",
        diff="medium")
    add("de", "failed", "school", "ferienplan", "Tagesschule – Schule Beispielberg", "2.4.2/F5",
        "The page shows the holiday plan 2026/27 but its title names the day-care page (Tagesschule), so it describes different content.",
        diff="hard")
    add("fr", "failed", "tourism", "randonnees", "randonnees-2026-v3.html", "2.4.2/F6",
        "The title is a file name ('randonnees-2026-v3.html') rather than a description of the hiking page.", diff="medium")

    # ---------------- passed -----------------
    add("de", "passed", "library", "veranstaltungen", "Veranstaltungen – Bibliothek Mustersee", "2.4.2/P1",
        "The title names the page topic (events) and the library, matching the h1 and the event list.", diff="easy")
    add("fr", "passed", "municipality", "dechets", "Déchets et recyclage – Commune de Valfictif", "2.4.2/P1",
        "Topic plus organisation: the title matches the waste-collection content of the page.", diff="easy")
    add("it", "passed", "utility", "tariffe", "Tariffe 2026 | Azienda acqua potabile Valfittizia", "2.4.2/P1",
        "The title states the topic (tariffs 2026) and the organisation of the page.", diff="easy")
    add("de", "passed", "tourism", "wandern", "Wandern – Verkehrsverein Ober-Beispielwil", "2.4.2/P1",
        "The title describes the hiking page and its publisher.", diff="easy")

    mensa = ('<h1>Iscrizione alla mensa</h1><p>Compilate il modulo entro il 15 settembre. Il pasto costa CHF 8.– al giorno.</p>'
             '<form action="grazie.html" method="post"><label for="allievo">Nome e cognome dell\'allievo</label>'
             '<input id="allievo" name="allievo" autocomplete="off"><label for="classe">Classe</label>'
             '<select id="classe" name="classe"><option>1a</option><option>2a</option><option>3a</option><option>4a</option>'
             '<option>5a</option></select><fieldset><legend>Giorni</legend>'
             '<label><input type="checkbox" name="g" value="lu"> lunedì</label><label><input type="checkbox" name="g" value="ma"> martedì</label>'
             '<label><input type="checkbox" name="g" value="gi"> giovedì</label><label><input type="checkbox" name="g" value="ve"> venerdì</label>'
             '</fieldset><label for="allergie">Allergie o diete particolari</label><textarea id="allergie" name="allergie" rows="3"></textarea>'
             '<button type="submit">Invia l\'iscrizione</button></form>')
    add("it", "passed", "school", "mensa", "Iscrizione alla mensa 2026/27 – Scuola di Esempiano", "2.4.2/P2",
        "The title names the task of the page (registering for the school canteen) and the school.", diff="easy",
        main_html=mensa, css=FORM_CSS)

    racc = ('<h1>Demande de raccordement</h1><p>Envoyez votre demande au moins deux mois avant le début des travaux.</p>'
            '<form action="merci.html" method="post"><label for="adresse">Adresse du bien-fonds</label><input id="adresse" name="adresse">'
            '<label for="parcelle">N° de parcelle</label><input id="parcelle" name="parcelle" inputmode="numeric">'
            '<label for="mo">Maître d\'ouvrage</label><input id="mo" name="mo"><label for="type">Type de bâtiment</label>'
            '<select id="type" name="type"><option>Maison individuelle</option><option>Immeuble locatif</option>'
            '<option>Bâtiment artisanal</option></select><label for="debut">Début prévu des travaux</label>'
            '<input id="debut" name="debut" type="date"><button type="submit">Envoyer la demande</button></form>')
    add("fr", "passed", "utility", "raccordement", "Demande de raccordement – Service des eaux d'Exempleval", "2.4.2/P2",
        "The title describes the purpose of the form page (applying for a water connection).", diff="easy",
        main_html=racc, css=FORM_CSS)

    add("de", "passed", "school", "ferienplan", "Ferienplan 2026/27", "2.4.2/T1",
        "Short title without the school name, but it names exactly the page topic (holiday plan 2026/27); site name and length are not required.",
        trap=True, diff="medium")
    add("it", "passed", "transport", "oggetti-smarriti", "Oggetti smarriti", "2.4.2/T1",
        "Two words, no organisation name, yet the title describes the lost-property page precisely.", trap=True, diff="medium")
    add("fr", "passed", "transport", "billets", "Transports publics de Valfictif | Billets et abonnements", "2.4.2/T2",
        "Organisation name first, then the topic (tickets and passes): the order does not matter, the topic is described.",
        trap=True, diff="medium")
    add("de", "passed", "municipality", "steuern", "Gemeinde Beispielwil: Steuern", "2.4.2/T2",
        "The municipality name comes first but the title still names the page topic (Steuern).", trap=True, diff="medium")
    add("it", "passed", "municipality", "index", "Comune di Esempiano", "2.4.2/T3",
        "This is the home page of the municipality site; the organisation name describes its topic and purpose.",
        trap=True, diff="medium")

    s_par = site_by_kind("fr", "school")
    par = main_content(get_page(s_par, "parascolaire")) + (
        '<h2>Tarifs</h2><ul><li>Accueil du matin : CHF 6.– par jour</li><li>Repas de midi et encadrement : CHF 14.–</li>'
        '<li>Après-midi jusqu\'à 18 h 30 : CHF 12.–</li></ul>')
    add("fr", "passed", "school", "parascolaire", "Garde des enfants avant et après l'école – École de Valfictif", "2.4.2/T4",
        "The title words differ from the h1 'Accueil parascolaire' but describe the same topic (childcare before/after school).",
        trap=True, diff="hard", main_html=par)

    app = ('<h1>Wohnsitzbestätigung bestellen</h1><p class="muted">Schritt 1 von 2 · Angaben zur Person</p>'
           '<form action="bestellen-2.html" method="post"><label for="name">Name, Vorname</label><input id="name" name="name" autocomplete="name">'
           '<label for="geb">Geburtsdatum</label><input id="geb" name="geb" placeholder="TT.MM.JJJJ" autocomplete="bday">'
           '<label for="zweck">Verwendungszweck</label><select id="zweck" name="zweck"><option>Arbeitgeber</option>'
           '<option>Behörde</option><option>Bank</option><option>Andere</option></select>'
           '<p>Gebühr: CHF 20.–, zahlbar mit Rechnung.</p><button type="submit">Weiter</button></form>'
           '<aside class="box"><h2>Weitere Dienste im Online-Schalter</h2><ul><li><a href="umzug.html">Umzug melden</a></li>'
           '<li><a href="hund.html">Hund anmelden</a></li><li><a href="kehricht.html">Kehrichtmarken bestellen</a></li></ul></aside>')
    add("de", "passed", "municipality", "verwaltung", "Online-Schalter – Gemeinde Beispielwil", "2.4.2/T5",
        "The page is a view of the municipality's e-service application; its title gives the application name, which Understanding 2.4.2 deems sufficient for web applications.",
        trap=True, diff="hard", main_html=app, css=FORM_CSS)

    # ---------------- cantTell -----------------
    s = site_by_kind("de", "municipality")
    art = ('<article>' + main_content(s["deep"]) + '<p class="muted">Publiziert am 12.01.2026 · Einwohnerdienste</p></article>')
    add("de", "cantTell", "municipality", "hundekontrolle", "Aktuelles – Gemeinde Beispielwil", "2.4.2/C1",
        "A single notice about dog registration is titled only with its section name 'Aktuelles'; whether a section title describes a specific article is disputed.",
        alt="failed", diff="hard", main_html=art)
    s = site_by_kind("fr", "library")
    art = ('<article>' + main_content(s["deep"]) + '<p class="muted">Publié le 3 novembre 2026</p></article>')
    add("fr", "cantTell", "library", "troc-livres", "Actualités – Bibliothèque de Bourg-Modèle", "2.4.2/C1",
        "The page is one news item (book swap on 5 December) but the title only names the news section.",
        alt="failed", diff="hard", main_html=art)

    info = ('<h1>Informazioni</h1>'
            '<section><h2>Cancelleria chiusa l\'8 dicembre</h2><p>In occasione dell\'Immacolata gli sportelli restano chiusi.</p></section>'
            '<section><h2>Raccolta carta anticipata</h2><p>La raccolta di carta e cartone di mercoledì 6 gennaio è anticipata a lunedì 4 gennaio.</p></section>'
            '<section><h2>Lavori in Via ai Monti</h2><p>Dal 12 al 23 ottobre la strada è percorribile a senso unico alternato.</p></section>'
            '<section><h2>Nuovi sacchi ufficiali</h2><p>Dal 1° gennaio sono in vendita i nuovi sacchi da 35 litri a CHF 1.80.</p></section>')
    add("it", "cantTell", "municipality", None, "Informazioni – Comune di Esempiano", "2.4.2/C2",
        "The page gathers unrelated notices under the umbrella title 'Informazioni'; the title is generic but there is no single topic it could name.",
        diff="hard", main_html=info)

    faq = ('<h1>Wissenswertes</h1>'
           '<details><summary>Wie hart ist das Fiktaler Wasser?</summary><p>Die Gesamthärte beträgt 18 °fH (mittelhart).</p></details>'
           '<details><summary>Wer bezahlt einen Rohrbruch auf meinem Grundstück?</summary><p>Ab dem Wasserzähler ist die Hausleitung Sache der Eigentümerschaft.</p></details>'
           '<details><summary>Darf ich Regenwasser für die WC-Spülung nutzen?</summary><p>Ja, die Anlage muss aber vom Trinkwassernetz getrennt und gemeldet sein.</p></details>'
           '<details><summary>Warum ist das Wasser manchmal trüb?</summary><p>Nach Arbeiten am Netz können Luftbläschen auftreten; lassen Sie das Wasser kurz laufen.</p></details>')
    add("de", "cantTell", "utility", None, "Wissenswertes – Wasserversorgung Fiktal", "2.4.2/C2",
        "A mixed FAQ page is titled 'Wissenswertes' (things worth knowing): generic but not wrong for heterogeneous content, so descriptiveness is a judgement call.",
        diff="hard", main_html=faq)

    return cases
