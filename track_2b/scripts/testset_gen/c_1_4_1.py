"""1.4.1 Use of Color — 26 cases (protocol rules 1.4.1/F1–F4, P1–P3, T1–T3, C1–C2)."""
from common import *
from _visual_util import compose, doc, img, org_of, host_of, phone, ratio

CRITERION = "1.4.1"

WHITE_THEMES = [t for t in THEMES if t["bg"] == "#ffffff"]


def mk(rng, lang, kind, title, main, expected, target, rule, notes, *, trap=False, alt_expected=None,
       difficulty="medium", css="", theme=None, org=None, **kw):
    org = org or org_of(rng, lang, kind)
    main = main.replace("{ORG}", esc(org)).replace("{HOST}", host_of(org)).replace("{PHONE}", phone(rng))
    body, lcss = compose(rng, lang, org, main, kind=kind, **kw)
    html = doc(rng, lang, title, org, body, lcss + css, theme=theme)
    return Case(CRITERION, lang, expected, html=html, target=target, rule=rule, notes=notes, trap=trap,
                alt_expected=alt_expected, difficulty=difficulty)


def link_colours(text, link, *, min_ratio=None, max_ratio=None):
    r = contrast(text, link)
    for t in WHITE_THEMES:
        assert contrast(link, t["bg"]) >= 4.5 and contrast(text, t["bg"]) >= 4.5
    if min_ratio is not None:
        assert r >= min_ratio, (text, link, r)
    if max_ratio is not None:
        assert r < max_ratio, (text, link, r)
    return ratio(text, link)


def _svg(w, h, inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'{inner}</svg>')


# ---------------------------------------------------------------------------
# FAILED
# ---------------------------------------------------------------------------

def f1_link_de(rng):
    tx, ln = "#1d2327", "#0b5394"
    r = link_colours(tx, ln, max_ratio=3)
    main = ("<h1>Neue Gebühren für die Kehrichtabfuhr</h1><p>Der Gemeinderat hat an seiner Sitzung vom "
            "22. September die Gebühren für die Kehrichtabfuhr angepasst.</p>"
            "<p class=\"lead\">Ab 1. Januar 2027 kostet eine Gebührenmarke für einen 35-Liter-Sack CHF 2.40. "
            "Alle Einzelheiten regelt die <a href=\"gebuehrenverordnung.html\">revidierte Gebührenverordnung</a>, "
            "die ab sofort auf der Gemeindekanzlei aufliegt.</p><p>Bereits gekaufte Marken bleiben bis Ende März "
            "gültig.</p>")
    css = f".lead{{font-size:1.1rem;color:{tx}}}.lead a{{color:{ln};text-decoration:none}}"
    return mk(rng, "de", "gemeinde", "Neue Kehrichtgebühren", main, "failed", ".lead a", "1.4.1/F1",
              f"The inline link has no underline and its colour differs from the surrounding text only by hue ({r}:1 < 3:1).",
              css=css, theme=pick(rng, WHITE_THEMES), difficulty="medium")


def f1_link_fr(rng):
    tx, ln = "#333333", "#c0392b"
    r = link_colours(tx, ln, max_ratio=3)
    main = ("<h1>Cours de natation pour enfants</h1><p class=\"chapeau\">Les inscriptions aux cours d'automne "
            "sont ouvertes jusqu'au 30 septembre. Le <a href=\"programme-cours.html\">programme détaillé des "
            "cours</a> indique les niveaux et les horaires de chaque groupe.</p><h2>Prix</h2><p>CHF 120.– pour dix "
            "leçons de 45 minutes. Réduction de 20 % dès le deuxième enfant.</p>")
    css = (f".chapeau{{color:{tx}}}.chapeau a{{color:{ln};text-decoration:none}}"
           ".chapeau a:hover,.chapeau a:focus{text-decoration:underline}")
    return mk(rng, "fr", "sport", "Cours de natation", main, "failed", ".chapeau a", "1.4.1/F1",
              f"The red inline link is underlined only on hover/focus; at rest it differs from the text by colour alone ({r}:1 < 3:1).",
              css=css, theme=pick(rng, WHITE_THEMES), difficulty="hard")


def f1_link_it(rng):
    tx, ln = "#22241f", "#1e6b2a"
    r = link_colours(tx, ln, max_ratio=3)
    main = ("<h1>Concorso per un posto di custode</h1><p class=\"introduzione\">Il Municipio mette a concorso un "
            "posto di custode dello stabile scolastico al 100 %. Requisiti e condizioni d'impiego sono descritti "
            "nel <a href=\"bando-custode.html\">bando di concorso</a>; le candidature vanno inoltrate entro il "
            "15 novembre 2026.</p><p>Per informazioni rivolgersi alla Cancelleria comunale, telefono {PHONE}.</p>")
    css = f".introduzione{{color:{tx}}}.introduzione a{{color:{ln};text-decoration:none}}"
    return mk(rng, "it", "gemeinde", "Concorso custode", main, "failed", ".introduzione a", "1.4.1/F1",
              f"The green link inside the sentence has no underline and only {r}:1 contrast with the surrounding text.",
              css=css, theme=pick(rng, WHITE_THEMES), difficulty="medium")


def f2_required_de(rng):
    fields = [("vorname", "Vorname des Kindes", True, "text"), ("nachname", "Nachname des Kindes", True, "text"),
              ("geburtsdatum", "Geburtsdatum", True, "text"), ("allergien", "Allergien oder Unverträglichkeiten", False, "area"),
              ("notfall", "Telefon Notfallkontakt", True, "tel")]
    form = "".join(
        f'<label for="{i}"' + (' class="pflicht"' if req else '') + f'>{esc(l)}</label>'
        + (f'<textarea id="{i}" name="{i}" rows="3"></textarea>' if t == "area" else f'<input type="{t}" id="{i}" name="{i}">')
        for i, l, req, t in fields)
    main = ("<h1>Anmeldung Herbstferien-Angebot</h1><p>Für Kinder von 6 bis 12 Jahren. Anmeldeschluss ist der "
            "25. September.</p><form id=\"anmeldung\" action=\"anmeldung-danke.html\" method=\"post\">"
            "<p>Rot markierte Felder müssen ausgefüllt werden.</p>" + form +
            "<p><button type=\"submit\">Anmelden</button></p></form>")
    css = ".pflicht{color:#c62828}"
    return mk(rng, "de", "schule", "Herbstferien-Angebot", main, "failed", "#anmeldung", "1.4.1/F2",
              "Required fields are identified only by red label colour; the instruction itself refers to the colour.",
              css=css, difficulty="easy")


def f2_error_fr(rng):
    main = ("<h1>Demande de macaron de stationnement</h1><div class=\"alerte\" role=\"alert\"><p>Le formulaire "
            "contient une erreur. Veuillez corriger le champ encadré en rouge.</p></div>"
            "<form id=\"demande\" action=\"demande-envoi.html\" method=\"post\">"
            "<label for=\"nom\">Nom et prénom</label><input type=\"text\" id=\"nom\" name=\"nom\" value=\"Claire Exemple\">"
            "<label for=\"adresse\">Adresse</label><input type=\"text\" id=\"adresse\" name=\"adresse\" value=\"Rue des Granges 4\">"
            "<label for=\"tel\">Téléphone</label><input type=\"tel\" id=\"tel\" name=\"tel\" value=\"079 000 12 34\">"
            "<label for=\"courriel\">Adresse e-mail</label><input type=\"email\" id=\"courriel\" name=\"courriel\" "
            "value=\"claire.exemple@\" class=\"champ-erreur\">"
            "<p><button type=\"submit\">Envoyer la demande</button></p></form>")
    css = ("#demande input{border-width:2px}.champ-erreur{border-color:#c62828}"
           ".alerte{border:1px solid #c62828;background:#fdecea;padding:4px 12px;border-radius:6px}")
    return mk(rng, "fr", "gemeinde", "Macaron de stationnement", main, "failed", "#demande", "1.4.1/F2",
              "The erroneous field is marked only by a red border (same width as the others, grey vs red ~1.2:1); the message only says 'encadré en rouge'.",
              css=css, difficulty="medium")


def f2_required_it(rng):
    fields = [("nome", "Nome", True, "text"), ("cognome", "Cognome", True, "text"), ("email", "E-mail", True, "email"),
              ("tel", "Telefono", False, "tel"), ("osservazioni", "Osservazioni", False, "area")]
    form = "".join(
        f'<label for="{i}"' + (' class="obbl"' if req else '') + f'>{esc(l)}</label>'
        + (f'<textarea id="{i}" name="{i}" rows="3"></textarea>' if t == "area" else f'<input type="{t}" id="{i}" name="{i}">')
        for i, l, req, t in fields)
    main = ("<h1>Iscrizione al corso di tedesco per adulti</h1><p>Il corso si svolge il mercoledì sera dalle "
            "19.00 alle 20.30 nella sede della scuola media. Costo: CHF 240.– per 12 serate.</p>"
            "<form id=\"iscrizione\" action=\"iscrizione-inviata.html\" method=\"post\"><p>I campi in rosso sono "
            "obbligatori.</p>" + form + "<p><button type=\"submit\">Invia l'iscrizione</button></p></form>")
    css = ".obbl{color:#b3261e}"
    return mk(rng, "it", "schule", "Corso di tedesco", main, "failed", "#iscrizione", "1.4.1/F2",
              "Mandatory fields are distinguished only by red label colour, with no asterisk or text marker.",
              css=css, difficulty="easy")


def f3_lines_de(rng):
    months = MONTHS_SHORT["de"]
    series = {"Hallenbad": [5200, 5050, 4800, 3900, 2100, 900, 600, 700, 2300, 4100, 4900, 5300],
              "Freibad": [0, 0, 0, 0, 3800, 9200, 12400, 11800, 2600, 0, 0, 0],
              "Eisbahn": [6100, 5400, 2100, 0, 0, 0, 0, 0, 0, 1800, 4700, 6900]}
    src = asset("v-chart-entries-de", line_chart("Eintritte pro Monat, 2025", months, series,
                                                 colors=["#1f6f8b", "#e07a2e", "#3c8d4f"]))
    main = ("<h1>Jahresbericht Sportanlagen 2025</h1><p>Die Grafik zeigt die monatlichen Eintritte der drei "
            "Anlagen. Im Sommer verlagert sich der Betrieb ins Freibad, im Winter auf die Eisbahn.</p>"
            f"<p>{img(src, 'Liniendiagramm der monatlichen Eintritte 2025', 640, 360, id='diagramm-eintritte')}</p>"
            "<p>Insgesamt besuchten 2025 rund 115 000 Personen die Anlagen.</p>")
    return mk(rng, "de", "sport", "Jahresbericht Sportanlagen", main, "failed", "#diagramm-eintritte", "1.4.1/F3",
              "The three lines are identified only by colour (same marker shape, colour-swatch legend, no direct labels or data table).",
              difficulty="medium")


def zones_svg(lang_days, colors):
    polys = ["20,40 300,30 320,180 40,200", "300,30 600,50 590,170 320,180",
             "40,200 320,180 330,340 30,350", "320,180 590,170 610,340 330,340"]
    inner = ['<rect width="820" height="380" fill="#ffffff"/>']
    for p, c in zip(polys, colors):
        inner.append(f'<polygon points="{p}" fill="{c}" stroke="#ffffff" stroke-width="3"/>')
    inner.append('<path d="M10 260 C200 240 380 290 640 250" fill="none" stroke="#ffffff" stroke-width="8"/>')
    for i, (d, c) in enumerate(zip(lang_days, colors)):
        y = 80 + i * 40
        inner.append(f'<rect x="650" y="{y - 16}" width="22" height="22" fill="{c}"/>'
                     f'<text x="682" y="{y}" font-family="Arial, sans-serif" font-size="18" fill="#1d2327">{esc(d)}</text>')
    return _svg(820, 380, "".join(inner))


def f3_map_fr(rng):
    src = asset("v-map-collect-fr", zones_svg(["lundi", "mardi", "jeudi", "vendredi"],
                                              ["#e07a2e", "#3c8d4f", "#8e5ea2", "#d4a017"]))
    main = ("<h1>Ramassage des ordures ménagères</h1><p>Les ordures ménagères sont ramassées une fois par "
            "semaine. Le jour dépend du secteur dans lequel vous habitez : consultez la carte ci-dessous.</p>"
            f"<p>{img(src, 'Carte des secteurs de ramassage', 820, 380, id='carte-secteurs')}</p>"
            "<p>Les sacs doivent être déposés le jour même avant 7 h.</p>")
    return mk(rng, "fr", "gemeinde", "Ramassage des ordures", main, "failed", "#carte-secteurs", "1.4.1/F3",
              "Each sector's collection day is conveyed only by matching fill colour to a legend swatch; sectors carry no labels or patterns.",
              difficulty="medium")


def f4_cells_it(rng):
    days = ["lun", "mar", "mer", "gio", "ven"]
    slots = ["17.00–18.30", "18.30–20.00", "20.00–21.30"]
    grid = [[1, 0, 0, 1, 1], [0, 0, 1, 0, 1], [1, 1, 0, 0, 0]]
    rows = "".join(f"<tr><th>{s}</th>" + "".join(f'<td class="{"libero" if v else "occupato"}"></td>' for v in r) + "</tr>"
                   for s, r in zip(slots, grid))
    main = ("<h1>Disponibilità della palestra comunale</h1><p>Società e privati possono riservare la palestra "
            "nelle fasce orarie libere. Settimana dal 9 al 15 novembre 2026.</p>"
            "<p><span class=\"legenda verde\"></span> libero <span class=\"legenda rossa\"></span> occupato</p>"
            "<table id=\"disponibilita\"><thead><tr><th>Fascia oraria</th>"
            + "".join(f"<th>{d}</th>" for d in days) + f"</tr></thead><tbody>{rows}</tbody></table>"
            "<p>Prenotazioni allo sportello o al numero {PHONE}.</p>")
    css = (".libero,.verde{background:#43a047}.occupato,.rossa{background:#e53935}#disponibilita td{width:56px}"
           ".legenda{display:inline-block;width:14px;height:14px;vertical-align:middle;margin:0 4px 0 12px}")
    return mk(rng, "it", "sport", "Disponibilità palestra", main, "failed", "#disponibilita", "1.4.1/F4",
              f"Free and booked slots are empty cells told apart only by green vs red fill ({ratio('#43a047', '#e53935')}:1 lightness difference).",
              css=css, difficulty="easy")


def f4_tabs_de(rng):
    rows = [("6.12", "1", "Bahnhof"), ("6.27", "4", "Oberdorf"), ("6.42", "1", "Bahnhof"), ("6.57", "7", "Friedhof"),
            ("7.12", "1", "Bahnhof"), ("7.27", "4", "Oberdorf")]
    body = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in rows)
    main = ("<h1>Abfahrten ab Dorfplatz</h1><p>Wählen Sie den Verkehrstag:</p>"
            "<div class=\"reiter\"><a href=\"abfahrten-werktag.html\" class=\"aktiv\" aria-current=\"page\">Montag–Freitag</a>"
            "<a href=\"abfahrten-samstag.html\">Samstag</a><a href=\"abfahrten-sonntag.html\">Sonn- und Feiertage</a></div>"
            "<table><thead><tr><th>Zeit</th><th>Linie</th><th>Richtung</th></tr></thead>"
            f"<tbody>{body}</tbody></table>")
    css = (".reiter{display:flex;flex-wrap:wrap;gap:4px;margin:8px 0 0}.reiter a{padding:8px 14px;color:#ffffff;"
           "background:#2f6fb5;text-decoration:none;border-radius:6px 6px 0 0}.reiter a.aktiv{background:#b85a1f}")
    return mk(rng, "de", "verkehr", "Abfahrten", main, "failed", ".reiter", "1.4.1/F4",
              f"The selected day tab differs from the others only by hue (orange vs blue, {ratio('#2f6fb5', '#b85a1f')}:1); nothing else on the page says which day the table shows.",
              css=css, difficulty="medium")


# ---------------------------------------------------------------------------
# PASSED
# ---------------------------------------------------------------------------

def p1_underline_fr(rng):
    main = ("<h1>Permis de construire</h1><p>Toute construction ou transformation soumise à autorisation doit "
            "faire l'objet d'une demande de permis. Les formulaires se trouvent sur la "
            "<a id=\"lien-formulaires\" href=\"formulaires-construction.html\">page des formulaires</a> ; le "
            "<a href=\"reglement-constructions.html\">règlement communal des constructions</a> précise les "
            "distances et les hauteurs autorisées.</p><p>Le dossier complet est à déposer au greffe en trois "
            "exemplaires.</p>")
    return mk(rng, "fr", "gemeinde", "Permis de construire", main, "passed", "#lien-formulaires", "1.4.1/P1",
              "Inline links keep the default underline, a non-colour cue.", difficulty="easy")


def t1_g183_de(rng):
    tx, ln = "#111111", "#0d74c4"
    r = link_colours(tx, ln, min_ratio=3)
    main = ("<h1>Grüngutabfuhr im Winter</h1><div class=\"artikel\"><p>Von Dezember bis Februar wird das Grüngut "
            "nur alle zwei Wochen abgeholt. Die genauen Daten finden Sie im <a href=\"abfallkalender.html\">"
            "Abfallkalender 2027</a>, der Anfang Dezember in alle Haushalte verteilt wird.</p><p>Weihnachtsbäume "
            "nehmen wir am 9. Januar separat mit.</p></div>")
    css = (f".artikel{{color:{tx}}}.artikel a{{color:{ln};text-decoration:none}}"
           ".artikel a:hover,.artikel a:focus{text-decoration:underline}")
    return mk(rng, "de", "werke", "Grüngutabfuhr", main, "passed", ".artikel a", "1.4.1/T1",
              f"No underline at rest, but the link is {r}:1 lighter than the surrounding text (≥ 3:1, G183) and underlines on hover/focus.",
              trap=True, css=css, theme=pick(rng, WHITE_THEMES), difficulty="hard")


def t1_g183_it(rng):
    tx, ln = "#1b1b1b", "#0b7a75"
    r = link_colours(tx, ln, min_ratio=3)
    main = ("<h1>Sentieri escursionistici: chiusure</h1><div class=\"testo\"><p>A causa dei lavori forestali il "
            "sentiero tra l'Alpe Fittizia e il Monte Esempio resta chiuso fino al 20 ottobre. Le alternative "
            "consigliate sono descritte nella <a href=\"percorsi-alternativi.html\">pagina dei percorsi "
            "alternativi</a>.</p><p>Si prega di rispettare la segnaletica sul posto.</p></div>")
    css = f".testo{{color:{tx}}}.testo a{{color:{ln};text-decoration:none}}"
    return mk(rng, "it", "gemeinde", "Sentieri chiusi", main, "passed", ".testo a", "1.4.1/T1",
              f"The link has no underline, but its luminance contrast with the surrounding text is {r}:1 (≥ 3:1), which G183 and the Understanding accept as a non-hue distinction.",
              trap=True, css=css, theme=pick(rng, WHITE_THEMES), difficulty="hard")


def p2_asterisk_de(rng):
    fields = [("name", "Name und Vorname", True, "text"), ("verein", "Verein / Organisation", False, "text"),
              ("datum", "Gewünschtes Datum", True, "text"), ("personen", "Anzahl Personen", True, "text"),
              ("email", "E-Mail", True, "email")]
    form = "".join(
        f'<label for="{i}"' + (' class="pflicht"' if req else '') + f'>{esc(l)}{" *" if req else ""}</label>'
        f'<input type="{t}" id="{i}" name="{i}">' for i, l, req, t in fields)
    main = ("<h1>Reservation Gemeindesaal</h1><p>Der Gemeindesaal bietet Platz für 120 Personen und verfügt "
            "über eine Küche. Miete für Ortsvereine: CHF 150.– pro Tag.</p><form id=\"reservation\" "
            "action=\"reservation-danke.html\" method=\"post\"><p>Felder mit * sind Pflichtfelder.</p>" + form +
            "<p><button type=\"submit\">Anfrage senden</button></p></form>")
    css = ".pflicht{color:#c62828}"
    return mk(rng, "de", "gemeinde", "Reservation Gemeindesaal", main, "passed", "#reservation", "1.4.1/P2",
              "Required labels are red but also carry an asterisk explained above the form.", css=css,
              difficulty="easy")


def p2_obligatoire_fr(rng):
    fields = [("eleve", "Nom de l'élève", True, "text"), ("classe", "Classe", True, "text"),
              ("taille", "Taille des chaussures de ski", False, "text"), ("parent", "Téléphone d'un parent", True, "tel")]
    form = "".join(
        f'<label for="{i}"' + (' class="requis"' if req else '') + f'>{esc(l)}{" (obligatoire)" if req else ""}</label>'
        f'<input type="{t}" id="{i}" name="{i}">' for i, l, req, t in fields)
    main = ("<h1>Camp de ski 2027</h1><p>Le camp de ski des élèves de 7e et 8e années aura lieu du 1er au 5 février. "
            "Participation des parents : CHF 180.–.</p><form id=\"inscription-camp\" action=\"camp-merci.html\" "
            "method=\"post\">" + form + "<p><button type=\"submit\">Inscrire mon enfant</button></p></form>")
    css = ".requis{color:#b3261e}"
    return mk(rng, "fr", "schule", "Camp de ski", main, "passed", "#inscription-camp", "1.4.1/P2",
              "Required fields are shown in red and say '(obligatoire)' in the label text.", css=css,
              difficulty="easy")


def patterned_chart():
    years = ["2021", "2022", "2023", "2024", "2025"]
    series = [("Alberghi", "#1f6f8b", [41.2, 43.8, 45.1, 46.9, 48.3], "circle", ""),
              ("Campeggi", "#e07a2e", [18.3, 21.1, 19.8, 22.4, 23.6], "square", "8 5"),
              ("Appartamenti", "#3c8d4f", [12.1, 13.9, 15.2, 16.1, 17.4], "triangle", "2 4")]
    w, h, left, top, pw, ph = 700, 380, 60, 50, 500, 270
    ymax = 50
    p = ['<rect width="700" height="380" fill="#ffffff"/>',
         f'<text x="{left}" y="30" font-family="Arial, sans-serif" font-size="18" font-weight="700" fill="#1d2327">'
         'Pernottamenti per tipo di alloggio (migliaia)</text>']
    for v in range(0, 51, 10):
        y = top + ph - ph * v / ymax
        p.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + pw}" y2="{y:.1f}" stroke="#d9dee2"/>'
                 f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="#3d464d">{v}</text>')
    for i, yv in enumerate(years):
        x = left + pw * i / 4
        p.append(f'<text x="{x:.1f}" y="{top + ph + 20}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#3d464d">{yv}</text>')
    for name, col, vals, mark, dash in series:
        pts = [(left + pw * i / 4, top + ph - ph * v / ymax) for i, v in enumerate(vals)]
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        p.append(f'<polyline points="{d}" fill="none" stroke="{col}" stroke-width="3"{da}/>')
        for x, y in pts:
            if mark == "circle":
                p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{col}"/>')
            elif mark == "square":
                p.append(f'<rect x="{x - 5:.1f}" y="{y - 5:.1f}" width="10" height="10" fill="{col}"/>')
            else:
                p.append(f'<path d="M{x:.1f} {y - 6:.1f} L{x + 6:.1f} {y + 5:.1f} L{x - 6:.1f} {y + 5:.1f}Z" fill="{col}"/>')
        lx, ly = pts[-1]
        p.append(f'<text x="{lx + 12:.1f}" y="{ly + 5:.1f}" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="#1d2327">{name}</text>')
    return _svg(w, h, "".join(p))


def p3_chart_it(rng):
    src = asset("v-chart-nights-it", patterned_chart())
    main = ("<h1>Turismo: pernottamenti 2021–2025</h1><p>I pernottamenti sono in crescita in tutte le "
            "categorie di alloggio; i campeggi hanno registrato un calo nel 2023 a causa del maltempo.</p>"
            f"<p>{img(src, 'Grafico dei pernottamenti per tipo di alloggio 2021–2025', 700, 380, id='grafico-pernottamenti')}</p>")
    return mk(rng, "it", "gemeinde", "Pernottamenti", main, "passed", "#grafico-pernottamenti", "1.4.1/P3",
              "Each line has its own marker shape and dash pattern and is labelled directly at its end, so colour is not the only cue.",
              difficulty="medium")


def t2_grid_de(rng):
    days = ["Mo", "Di", "Mi", "Do", "Fr"]
    slots = ["17.00–18.30", "18.30–20.00", "20.00–21.30"]
    grid = [[0, 1, 1, 0, 1], [1, 0, 0, 0, 1], [0, 0, 1, 1, 0]]
    rows = "".join(f"<tr><th>{s}</th>" + "".join(
        (f'<td class="frei">frei</td>' if v else '<td class="belegt">belegt</td>') for v in r) + "</tr>"
                   for s, r in zip(slots, grid))
    main = ("<h1>Belegung Mehrzweckhalle</h1><p>Woche vom 9. bis 15. November 2026. Freie Zeiten können Sie "
            "bei der Gemeindekanzlei reservieren.</p><table id=\"belegung\"><thead><tr><th>Zeit</th>"
            + "".join(f"<th>{d}</th>" for d in days) + f"</tr></thead><tbody>{rows}</tbody></table>")
    css = ".frei{background:#43a047;color:#000000}.belegt{background:#e53935;color:#000000}"
    return mk(rng, "de", "gemeinde", "Belegung Mehrzweckhalle", main, "passed", "#belegung", "1.4.1/T2",
              "Green/red cells also contain the words 'frei'/'belegt', so colour is redundant.", trap=True,
              css=css, difficulty="easy")


def t2_pie_fr(rng):
    labels = ["Forêt", "Agriculture", "Zone bâtie", "Eaux", "Improductif"]
    vals = [41, 33, 14, 7, 5]
    src = asset("v-chart-land-fr", pie_chart("Répartition du territoire communal", labels, vals,
                                              colors=["#3c8d4f", "#d4a017", "#c2453b", "#2d9cdb", "#8e5ea2"]))
    alt = "Répartition du territoire : forêt 41 %, agriculture 33 %, zone bâtie 14 %, eaux 7 %, improductif 5 %"
    main = ("<h1>Notre commune en chiffres</h1><p>La commune s'étend sur 1 240 hectares, entre le lac et la "
            "lisière du Jura.</p>"
            f"<p>{img(src, alt, 520, 320, id='graphique-territoire')}</p>")
    return mk(rng, "fr", "gemeinde", "La commune en chiffres", main, "passed", "#graphique-territoire", "1.4.1/T2",
              "Slices are matched to the legend by colour, but the legend states each category's share in text, so no information depends on colour.",
              trap=True, difficulty="hard")


def t2_error_it(rng):
    main = ("<h1>Richiesta di carta giornaliera</h1><p>Le carte giornaliere del Comune costano CHF 45.– e "
            "sono valide su tutta la rete.</p><form id=\"richiesta\" action=\"richiesta-inviata.html\" method=\"post\">"
            "<label for=\"nome\">Nome e cognome</label><input type=\"text\" id=\"nome\" name=\"nome\" value=\"Lucia Esempio\">"
            "<label for=\"data\">Data del viaggio</label><input type=\"text\" id=\"data\" name=\"data\" value=\"31.11.2026\" "
            "class=\"campo-errore\" aria-describedby=\"msg-data\" aria-invalid=\"true\">"
            "<p id=\"msg-data\" class=\"msg-errore\">⚠ Data non valida: novembre ha 30 giorni. Usate il formato "
            "gg.mm.aaaa.</p><p><button type=\"submit\">Invia richiesta</button></p></form>")
    css = ("#richiesta input{border-width:2px}.campo-errore{border-color:#c62828}"
           ".msg-errore{color:#b3261e;font-weight:600;margin-top:4px}")
    return mk(rng, "it", "gemeinde", "Carta giornaliera", main, "passed", "#richiesta", "1.4.1/T2",
              "The red border is accompanied by a visible text error message next to the field.", trap=True,
              css=css, difficulty="medium")


def t3_nav_fr(rng):
    items = ["Contrôle des habitants", "État civil", "Naturalisation", "Cartes d'identité", "Attestations"]
    nav = "".join(f'<li><a href="{slug(i)}.html">{esc(i)}</a></li>' for i in items)
    main = ("<h1>Population</h1><div class=\"rubrique\"><nav class=\"sous-nav\" aria-label=\"Dans cette rubrique\">"
            f"<ul>{nav}</ul></nav><div><p>Le contrôle des habitants enregistre les arrivées, les départs et les "
            "changements d'adresse. Toute personne qui s'établit dans la commune doit s'annoncer dans les 14 jours, "
            "muni d'une pièce d'identité.</p><p>Les attestations de domicile coûtent CHF 20.– et peuvent être "
            "commandées en ligne.</p></div></div>")
    css = (".rubrique{display:grid;grid-template-columns:220px minmax(0,1fr);gap:24px}"
           "@media (max-width:640px){.rubrique{grid-template-columns:1fr}}"
           ".sous-nav ul{list-style:none;margin:0;padding:0}.sous-nav li{border-bottom:1px solid #d4d7de}"
           ".sous-nav a{display:block;padding:8px 4px;text-decoration:none}")
    return mk(rng, "fr", "gemeinde", "Population", main, "passed", ".sous-nav li:nth-child(2) a", "1.4.1/T3",
              "Links without underline in a sub-navigation list are identified by their position in the menu, not by colour within running text.",
              trap=True, css=css, layout=0, difficulty="medium")


def t2_tags_it(rng):
    main = ("<h1>Agenda di novembre</h1><ul class=\"agenda\">"
            "<li id=\"evento-1\"><span class=\"tag cultura\">Cultura</span> <strong>Sabato 7 novembre, 20.30</strong> – "
            "Concerto del coro misto nella chiesa parrocchiale</li>"
            "<li><span class=\"tag sport\">Sport</span> <strong>Domenica 15 novembre, 10.00</strong> – Corsa "
            "podistica delle castagne</li>"
            "<li><span class=\"tag famiglia\">Famiglie</span> <strong>Mercoledì 18 novembre, 14.30</strong> – "
            "Pomeriggio di giochi in biblioteca</li></ul>")
    css = (".agenda{list-style:none;padding:0}.agenda li{padding:8px 0;border-bottom:1px solid #d4d7de}"
           ".tag{display:inline-block;padding:1px 8px;border-radius:10px;font-size:.85rem;color:#1d2327}"
           ".cultura{background:#f3d1e6}.sport{background:#cfe8d5}.famiglia{background:#fde9b8}")
    return mk(rng, "it", "gemeinde", "Agenda", main, "passed", "#evento-1 .tag", "1.4.1/T2",
              "The coloured category badge contains the category name as text; the colour adds nothing that is not written.",
              trap=True, css=css, difficulty="easy")


def p1_bold_fr(rng):
    t = pick(rng, WHITE_THEMES)
    main = ("<h1>Déneigement</h1><div class=\"info\"><p>En cas de fortes chutes de neige, les trottoirs sont "
            "dégagés en priorité autour des écoles et de la gare. Consultez le <a href=\"plan-deneigement.html\">"
            "plan de déneigement</a> pour connaître l'ordre de passage dans votre quartier.</p><p>Merci de ne pas "
            "stationner sur la chaussée pendant les opérations.</p></div>")
    css = ".info a{text-decoration:none;font-weight:700}"
    return mk(rng, "fr", "gemeinde", "Déneigement", main, "passed", ".info a", "1.4.1/P1",
              f"The link has no underline and only {ratio(t['ink'], t['link'])}:1 contrast with the text, but it is set in bold while the rest of the paragraph is regular weight (G182).",
              trap=True, css=css, theme=t, difficulty="hard")


# ---------------------------------------------------------------------------
# CANTTELL
# ---------------------------------------------------------------------------

def c1_times_de(rng):
    hours = {6: ["12", "42"], 7: ["05", "12", "35", "42"], 8: ["12", "42"], 9: ["12", "42"], 12: ["05", "12", "42"],
             13: ["12", "42"]}
    red = {(7, "05"), (7, "35"), (12, "05")}
    rows = "".join(f"<tr><th>{hh}</th><td>" + " ".join(
        (f'<span class="rot">{m}</span>' if (hh, m) in red else m) for m in mins) + "</td></tr>"
                   for hh, mins in hours.items())
    main = ("<h1>Ortsbus Linie 2</h1><p>Fahrplan gültig ab 13. Dezember 2026. Haltestelle Dorfplatz, Richtung "
            "Bahnhof.</p><table id=\"fahrplan\"><thead><tr><th>Stunde</th><th>Minuten</th></tr></thead>"
            f"<tbody>{rows}</tbody></table><p>Abends verkehrt der Bus stündlich bis 23.12 Uhr.</p>")
    css = ".rot{color:#c62828;}"
    return mk(rng, "de", "verkehr", "Fahrplan Linie 2", main, "cantTell", "#fahrplan", "1.4.1/C1",
              "Three departure times are printed in red without any legend; whether red encodes a meaning (e.g. school days only) or is emphasis cannot be determined.",
              css=css, difficulty="hard")


def c1_dates_fr(rng):
    dates = ["Lundi 1er février", "Lundi 22 mars", "Lundi 10 mai", "Lundi 21 juin", "Lundi 27 septembre",
             "Lundi 13 décembre"]
    lis = "".join((f'<li class="marque">{d}</li>' if i == 2 else f"<li>{d}</li>") for i, d in enumerate(dates))
    main = ("<h1>Séances du Conseil communal 2027</h1><p>Les séances ont lieu à 20 h à la salle du Conseil. "
            f"Elles sont publiques.</p><ul id=\"seances\">{lis}</ul><p>L'ordre du jour est publié au pilier public "
            "dix jours avant chaque séance.</p>")
    css = ".marque{color:#a65300}"
    return mk(rng, "fr", "gemeinde", "Séances du Conseil", main, "cantTell", "#seances", "1.4.1/C1",
              "One session date is shown in orange with no explanation; if it signals something (e.g. a budget session) the information is colour-only, but the page does not say.",
              css=css, difficulty="hard")


def toggle_css(cls):
    return (f".{cls}{{display:inline-flex;margin:8px 0 16px}}.{cls} button{{background:#ffffff;color:#0b4f6c;"
            f"border:2px solid #0b4f6c;border-radius:0;margin:0}}.{cls} button+button{{border-left:0}}"
            f".{cls} button.an{{background:#0b4f6c;color:#ffffff}}")


def c2_toggle_it(rng):
    rows = [("Sala multiuso, giornata intera", "CHF 380.–"), ("Sala multiuso, mezza giornata", "CHF 220.–"),
            ("Cucina", "CHF 90.–"), ("Pulizia finale", "CHF 120.–")]
    tb = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in rows)
    main = ("<h1>Tariffe di noleggio</h1><p>Prezzi per società e privati domiciliati nel Comune.</p>"
            "<div class=\"commutatore\" role=\"group\" aria-label=\"Visualizzazione dei prezzi\">"
            "<button type=\"button\" class=\"an\" aria-pressed=\"true\">IVA inclusa</button>"
            "<button type=\"button\" aria-pressed=\"false\">IVA esclusa</button></div>"
            f"<table><thead><tr><th>Prestazione</th><th>Prezzo</th></tr></thead><tbody>{tb}</tbody></table>")
    return mk(rng, "it", "gemeinde", "Tariffe di noleggio", main, "cantTell", ".commutatore", "1.4.1/C2",
              "Which of the two price modes is active is shown only by the inverted (filled) colour scheme; the lightness difference passes the Understanding's 3:1 note but the 'filled = active' meaning is a convention.",
              alt_expected="passed", css=toggle_css("commutatore"), difficulty="hard")


def c2_toggle_de(rng):
    rows = [("Grundgebühr pro Jahr", "CHF 160.–"), ("Mengenpreis pro m³", "CHF 1.85"),
            ("Abwassergebühr pro m³", "CHF 2.10")]
    tb = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in rows)
    main = ("<h1>Wassertarife 2027</h1><p>Die Tarife wurden von der Gemeindeversammlung am 30. November "
            "genehmigt.</p><div class=\"umschalter\" role=\"group\" aria-label=\"Tarifart\">"
            "<button type=\"button\" aria-pressed=\"false\">Haushalte</button>"
            "<button type=\"button\" class=\"an\" aria-pressed=\"true\">Gewerbe</button></div>"
            f"<table><thead><tr><th>Position</th><th>Tarif</th></tr></thead><tbody>{tb}</tbody></table>")
    return mk(rng, "de", "werke", "Wassertarife", main, "cantTell", ".umschalter", "1.4.1/C2",
              "The selected tariff type is indicated only by a filled versus outlined colour scheme of two otherwise identical buttons.",
              alt_expected="passed", css=toggle_css("umschalter"), difficulty="hard")


BUILDERS = [
    f1_link_de, f1_link_fr, f1_link_it, f2_required_de, f2_error_fr, f2_required_it, f3_lines_de, f3_map_fr,
    f4_cells_it, f4_tabs_de,
    p1_underline_fr, t1_g183_de, t1_g183_it, p2_asterisk_de, p2_obligatoire_fr, p3_chart_it, t2_grid_de,
    t2_pie_fr, t2_error_it, t3_nav_fr, t2_tags_it, p1_bold_fr,
    c1_times_de, c1_dates_fr, c2_toggle_it, c2_toggle_de,
]


def build(rng):
    return [b(rng) for b in BUILDERS]
