"""1.1.1 Non-text Content — 40 cases (protocol rules 1.1.1/N1, F1–F5, P1–P3, T1–T5, C1–C3)."""
from common import *
from _visual_util import compose, doc, img, org_of, host_of, phone

CRITERION = "1.1.1"


# ---------------------------------------------------------------------------
# SVG helpers (own drawings)
# ---------------------------------------------------------------------------

def _svg(w, h, inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'{inner}</svg>')


ZONES = [("0,0 600,0 600,110 380,140 0,120", "#cfe3c4"),
         ("0,120 380,140 600,110 600,230 300,250 0,240", "#f3e1b6"),
         ("0,240 300,250 600,230 600,360 0,360", "#cddbea")]


def zones_map(names):
    inner = ['<rect width="600" height="360" fill="#ffffff"/>']
    for (pts, col) in ZONES:
        inner.append(f'<polygon points="{pts}" fill="{col}" stroke="#55606a" stroke-width="2"/>')
    inner.append('<path d="M0 300 C150 280 260 330 420 300 S560 270 600 290" fill="none" stroke="#4d9de0" stroke-width="6"/>')
    for (x, y), n in zip([(300, 70), (300, 185), (300, 310)], names):
        inner.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Arial, sans-serif" font-size="26" '
                     f'font-weight="700" fill="#1d2327">{esc(n)}</text>')
    return _svg(600, 360, "".join(inner))


AREA_POLYS = [z[0] for z in ZONES]


def status_svg(ok, label=None):
    icon = ICONS["check"] if ok else ICONS["close"]
    col = "#2e7d32" if ok else "#b3261e"
    lab = f' aria-label="{esc(label)}"' if label else ""
    return (f'<svg role="img"{lab} width="22" height="22" viewBox="0 0 24 24"><g fill="none" stroke="{col}" '
            f'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">{icon}</g></svg>')


def sign_svg():
    bike = ('<g fill="none" stroke="#ffffff" stroke-width="5" stroke-linecap="round" stroke-linejoin="round">'
            '<circle cx="62" cy="112" r="20"/><circle cx="138" cy="112" r="20"/>'
            '<path d="M62 112l22-40h30l24 40M84 72l20 40M100 56h16"/></g>')
    return _svg(200, 200, '<rect width="200" height="200" fill="#ffffff"/>'
                '<circle cx="100" cy="100" r="92" fill="#1f5fae" stroke="#ffffff" stroke-width="6"/>' + bike)


def leaf_svg():
    d = ("M120 230 L120 170 M120 170 L60 190 L72 150 L28 128 L70 112 L52 64 L96 86 L120 30 L144 86 L188 64 "
         "L170 112 L212 128 L168 150 L180 190 Z")
    return _svg(240, 250, '<rect width="240" height="250" fill="#fbfaf6"/>'
                f'<path d="{d}" fill="#d98c2b" stroke="#8a4b0f" stroke-width="3" stroke-linejoin="round"/>'
                '<path d="M120 170 L120 60 M120 140 L70 112 M120 140 L170 112 M120 110 L90 80 M120 110 L150 80" '
                'fill="none" stroke="#8a4b0f" stroke-width="2"/>')


def detour_map(streets, closed_label):
    s1, s2, s3, s4 = streets
    inner = ['<rect width="640" height="380" fill="#f4f1ea"/>',
             '<path d="M40 190 H600" stroke="#bfc5cc" stroke-width="22"/>',
             '<path d="M180 40 V340 M460 40 V340" stroke="#bfc5cc" stroke-width="16"/>',
             '<path d="M180 80 H460" stroke="#bfc5cc" stroke-width="14"/>',
             '<path d="M260 175 l40 30 M300 175 l-40 30" stroke="#b3261e" stroke-width="6"/>',
             '<path d="M40 190 H180 V80 H460 V190 H600" fill="none" stroke="#e07a2e" stroke-width="7" '
             'stroke-dasharray="14 8"/>',
             f'<text x="60" y="230" font-family="Arial, sans-serif" font-size="16" fill="#1d2327">{esc(s1)}</text>',
             f'<text x="190" y="66" font-family="Arial, sans-serif" font-size="16" fill="#1d2327">{esc(s2)}</text>',
             f'<text x="470" y="300" font-family="Arial, sans-serif" font-size="16" fill="#1d2327">{esc(s3)}</text>',
             f'<text x="190" y="320" font-family="Arial, sans-serif" font-size="16" fill="#1d2327">{esc(s4)}</text>',
             f'<text x="245" y="160" font-family="Arial, sans-serif" font-size="14" fill="#b3261e">{esc(closed_label)}</text>']
    return _svg(640, 380, "".join(inner))


def network_svg(lines):
    """lines: list of (name, colour, [stop names]) drawn as horizontal tracks."""
    inner = ['<rect width="680" height="320" fill="#ffffff"/>']
    for i, (name, col, stops) in enumerate(lines):
        y = 70 + i * 90
        inner.append(f'<rect x="16" y="{y - 16}" width="44" height="32" rx="6" fill="{col}"/>'
                     f'<text x="38" y="{y + 7}" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" '
                     f'font-weight="700" fill="#ffffff">{esc(name)}</text>')
        inner.append(f'<path d="M80 {y} H650" stroke="{col}" stroke-width="8"/>')
        for j, st in enumerate(stops):
            x = 90 + j * (550 / max(1, len(stops) - 1))
            inner.append(f'<circle cx="{x:.0f}" cy="{y}" r="8" fill="#ffffff" stroke="{col}" stroke-width="4"/>'
                         f'<text x="{x:.0f}" y="{y + 30}" text-anchor="middle" font-family="Arial, sans-serif" '
                         f'font-size="13" fill="#1d2327">{esc(st)}</text>')
    return _svg(680, 320, "".join(inner))


def logo_svg(word1, word2):
    inner = ('<g fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
             'transform="translate(4 8) scale(1.4)">' + ICONS["bus"] + '</g>'
             f'<text x="48" y="24" font-family="Arial, sans-serif" font-size="17" font-weight="700" fill="#ffffff">{esc(word1)}</text>'
             f'<text x="48" y="44" font-family="Arial, sans-serif" font-size="14" fill="#ffffff">{esc(word2)}</text>')
    return _svg(240, 52, inner)


PIXEL = _svg(1, 1, '<rect width="1" height="1" fill="#ffffff"/>')

ICON_CSS = (".tool-icon{vertical-align:middle;margin-right:6px}"
            ".stato{list-style:none;padding:0}.stato li{display:flex;align-items:center;gap:10px;padding:6px 0;"
            "border-bottom:1px solid #d4d7de}")


def ok_icon_link(rng, lang):
    """A passing distractor: pictogram with alt="" inside a link that has visible text."""
    txt = {"de": "E-Mail an uns", "fr": "Nous écrire", "it": "Scriveteci", "en": "Write to us"}[lang]
    src = asset("v-ico-mail", pictogram("mail", color="#1d2327", size=20))
    return ('<p><a href="mailto:info@{HOST}">' + img(src, "", 20, 20, class_="tool-icon") + txt + '</a></p>')


def ok_ornament(rng):
    kind = pick(rng, ["dots", "wave", "leaves"])
    src = asset(f"v-orn-{kind}", ornament(kind, color="#b8c4cc"))
    return f'<p>{img(src, "", 600, 24)}</p>'


def maybe_distractor(rng, lang):
    r = rng.random()
    if r < 0.3:
        return ok_icon_link(rng, lang)
    if r < 0.5:
        return ok_ornament(rng)
    return ""


def mk(rng, lang, kind, title, main, expected, target, rule, notes, *, trap=False, alt_expected=None,
       difficulty="medium", org=None, css="", distract=False, **kw):
    org = org or org_of(rng, lang, kind)
    if distract:
        main += maybe_distractor(rng, lang)
    main = main.replace("{ORG}", esc(org)).replace("{HOST}", host_of(org)).replace("{PHONE}", phone(rng))
    body, lcss = compose(rng, lang, org, main, kind=kind, **kw)
    html = doc(rng, lang, title, org, body, lcss + ICON_CSS + css)
    return Case(CRITERION, lang, expected, html=html, target=target, rule=rule, notes=notes, trap=trap,
                alt_expected=alt_expected, difficulty=difficulty)


# ---------------------------------------------------------------------------
# FAILED
# ---------------------------------------------------------------------------

def f1_playground(rng):
    src = asset("v-scene-playground-1", scene("playground", seed=1))
    main = ("<h1>Neuer Spielplatz am Seeweg eröffnet</h1><p class=\"muted\">Publiziert am 3.9.2026</p>"
            "<p>Nach drei Monaten Bauzeit ist der Spielplatz am Seeweg seit Samstag wieder offen. Die alten Geräte "
            "wurden ersetzt; neu gibt es eine Rutschbahn und eine Nestschaukel für die Kleinsten.</p>"
            "<p>So sieht die neue Anlage aus:</p>"
            f"<p>{img(src, None, 480, 300, id='bild-spielplatz')}</p>"
            "<p>Die Gemeinde dankt dem Quartierverein für die Mithilfe bei der Planung. Rückmeldungen nehmen wir "
            "gerne unter <a href=\"mailto:info@{HOST}\">info@{HOST}</a> entgegen.</p>")
    return mk(rng, "de", "gemeinde", "Neuer Spielplatz am Seeweg", main, "failed", "#bild-spielplatz",
              "1.1.1/F1", "The photo introduced with 'So sieht die neue Anlage aus' has no alt attribute at all.",
              difficulty="easy")


def f1_bridge(rng):
    src = asset("v-scene-bridge-2", scene("bridge", seed=2))
    main = ("<h1>Passerella sul riale: lavori a buon punto</h1>"
            "<p>I lavori di rifacimento della passerella pedonale procedono secondo il programma. La riapertura è "
            "prevista per metà dicembre, condizioni meteo permettendo.</p>"
            "<p>Ecco lo stato del cantiere a fine settembre:</p>"
            f"<figure>{img(src, None, 480, 300)}<figcaption>Foto: Ufficio tecnico comunale</figcaption></figure>"
            "<p>Durante i lavori il passaggio è garantito dal ponte provvisorio a valle.</p>")
    return mk(rng, "it", "gemeinde", "Lavori alla passerella", main, "failed", "figure img",
              "1.1.1/F1", "The progress photo of the construction site has no alt attribute; the caption only credits the photographer.",
              distract=True, difficulty="easy")


def f1_input_image(rng):
    src = asset("v-ico-search-dark", pictogram("search", color="#ffffff", bg="#0b4f6c", size=36))
    main = ("<h1>Catalogue en ligne</h1><p>Plus de 28 000 livres, BD, films et jeux sont disponibles au prêt. "
            "Recherchez un titre, un auteur ou un sujet.</p>"
            "<form action=\"recherche.html\" role=\"search\"><label for=\"q\">Rechercher dans le catalogue</label>"
            f"<input type=\"search\" id=\"q\" name=\"q\"> <input type=\"image\" src=\"{src}\" width=\"36\" height=\"36\">"
            "</form><h2>Nouveautés du mois</h2><ul><li>« Le Lac endormi », roman</li><li>« Cuisiner de saison », "
            "livre de cuisine</li><li>« Les oiseaux du Jura », documentaire</li></ul>")
    return mk(rng, "fr", "bibliothek", "Catalogue en ligne", main, "failed", 'input[type="image"]',
              "1.1.1/F1", "The search submit button is an input type=image without alt, so it has no accessible name.",
              difficulty="easy")


def f1_area(rng):
    names = ["Nord", "Mitte", "Süd"]
    src = asset("v-map-zones-de", zones_map(names))
    areas = (f'<area shape="poly" coords="{AREA_POLYS[0]}" href="schulkreis-nord.html" alt="Schulkreis Nord">'
             f'<area shape="poly" coords="{AREA_POLYS[1]}" href="schulkreis-mitte.html" alt="Schulkreis Mitte">'
             f'<area shape="poly" coords="{AREA_POLYS[2]}" href="schulkreis-sued.html" id="kreis-sued">')
    main = ("<h1>Welches Schulhaus ist zuständig?</h1><p>Die Gemeinde ist in drei Schulkreise eingeteilt. Wählen "
            "Sie auf der Karte Ihren Schulkreis, um das zuständige Schulhaus und den Schulweg zu sehen.</p>"
            f"<p>{img(src, 'Karte der drei Schulkreise', 600, 360, usemap='#schulkreise')}</p>"
            f"<map name=\"schulkreise\">{areas}</map>"
            "<p>Bei Unklarheiten hilft Ihnen die Schulverwaltung, Telefon {PHONE}.</p>")
    return mk(rng, "de", "schule", "Schulkreise", main, "failed", "#kreis-sued", "1.1.1/F1",
              "The image-map area linking to the southern school district has no alt, so the link has no name; the other two areas are named.",
              difficulty="medium")


def f1_svg_status(rng):
    main = ("<h1>Stato degli impianti sportivi</h1><p>Aggiornato oggi alle 7.30. In caso di maltempo lo stato "
            "può cambiare durante la giornata.</p><ul class=\"stato\">"
            f"<li>{status_svg(True, 'aperta')} Piscina coperta</li>"
            f"<li>{status_svg(False, 'chiuso')} Campo di calcio (terreno impraticabile)</li>"
            f"<li id=\"pista\">{status_svg(True)} Pista di ghiaccio</li>"
            f"<li>{status_svg(True, 'aperta')} Palestra comunale</li></ul>"
            "<p>Informazioni telefoniche: {PHONE}.</p>")
    return mk(rng, "it", "sport", "Stato degli impianti", main, "failed", "#pista svg", "1.1.1/F1",
              "The status icon for the ice rink is an svg role=img without any accessible name, so its open/closed state is not conveyed in text.",
              distract=True, difficulty="medium")


def f2_bild(rng):
    src = asset("v-scene-bike-3", scene("bike", seed=3))
    main = ("<h1>Mobilität</h1><p>Die Gemeinde fördert den Fuss- und Veloverkehr mit sicheren Wegen und "
            "genügend Abstellplätzen.</p><section class=\"box\"><h2>Unser Tipp: die neue Velostation</h2>"
            "<p>240 gedeckte Plätze direkt beim Bahnhof, rund um die Uhr zugänglich.</p>"
            f"<p><a href=\"velostation.html\">{img(src, 'Bild', 320, 200)}</a></p></section>"
            "<h2>Velorouten</h2><p>Die signalisierten Routen führen abseits der Hauptstrassen durch die Quartiere.</p>")
    return mk(rng, "de", "gemeinde", "Mobilität", main, "failed", ".box a img", "1.1.1/F2",
              "The image is the only content of the link to the bike-station page and its alt is the placeholder 'Bild'.",
              difficulty="easy")


def f2_filename(rng):
    src = asset("v-scene-townhall-4", scene("townhall", seed=4))
    main = ("<h1>La salle polyvalente se refait une beauté</h1><p>Les travaux de rénovation de la salle "
            "polyvalente ont débuté en juin. Toiture, fenêtres et chauffage sont remplacés ; la salle rouvrira "
            "pour la soirée des sociétés locales.</p><p>Voici l'état du chantier à la mi-octobre :</p>"
            f"<p>{img(src, 'DSC_0457.JPG', 480, 300)}</p>"
            "<p>Pendant les travaux, les manifestations ont lieu au collège.</p>")
    return mk(rng, "fr", "gemeinde", "Rénovation de la salle polyvalente", main, "failed", 'img[alt="DSC_0457.JPG"]',
              "1.1.1/F2", "The construction photo's alt is the camera file name 'DSC_0457.JPG', which is not a text alternative.",
              distract=True, difficulty="easy")


def f2_grafico(rng):
    src = asset("v-chart-water-it", bar_chart("Consumo medio per abitante (litri al giorno)",
                                              ["2021", "2022", "2023", "2024", "2025"],
                                              [171, 166, 168, 159, 154], unit="litri / abitante / giorno",
                                              color="#1f6f8b"))
    main = ("<h1>Acqua potabile: consumi in calo</h1><p>Negli ultimi anni le economie domestiche hanno ridotto "
            "il consumo di acqua potabile. Il grafico mostra l'andamento del consumo medio per abitante.</p>"
            f"<p>{img(src, 'grafico', 640, 360)}</p><p>Consigli per risparmiare acqua sono disponibili allo "
            "sportello dell'azienda.</p>")
    return mk(rng, "it", "werke", "Consumi di acqua potabile", main, "failed", 'img[alt="grafico"]',
              "1.1.1/F2", "The bar chart's alt is the placeholder 'grafico'; the yearly values appear nowhere in text.",
              distract=True, difficulty="easy")


def f2_icone(rng):
    src = asset("v-ico-download", pictogram("download", color="#0b4f6c", size=28))
    main = ("<h1>Gestion des déchets</h1><p>Le nouveau règlement communal sur la gestion des déchets entre en "
            "vigueur le 1er janvier 2027. Il fixe notamment la taxe au sac et les jours de ramassage.</p>"
            "<h2>Documents</h2><p id=\"doc-reglement\">Règlement communal sur la gestion des déchets (PDF, 220 Ko) "
            f"<a href=\"reglement-dechets.pdf\">{img(src, 'icône', 28, 28)}</a></p>")
    return mk(rng, "fr", "gemeinde", "Gestion des déchets", main, "failed", "#doc-reglement img", "1.1.1/F2",
              "The download link contains only an icon whose alt is 'icône', so the link's purpose is not conveyed.",
              difficulty="medium")


def f3_bar(rng):
    vals = [1840, 1795, 1752, 1690, 1655]
    src = asset("v-chart-waste-de", bar_chart("Kehrichtmenge pro Jahr (Tonnen)", ["2021", "2022", "2023", "2024", "2025"],
                                              vals, unit="Tonnen", color="#3c8d4f"))
    main = ("<h1>Abfallmengen 2021–2025</h1><p>Die Gemeinde erhebt jedes Jahr, wie viel Kehricht in den "
            "Sammelstellen anfällt. Die Grafik zeigt, wie sich die Menge seit 2021 entwickelt hat.</p>"
            f"<p>{img(src, 'Diagramm zu den Abfallmengen 2021 bis 2025', 640, 360, id='grafik-abfall')}</p>"
            "<p>Wir danken der Bevölkerung für das sorgfältige Trennen der Wertstoffe.</p>")
    return mk(rng, "de", "werke", "Abfallmengen", main, "failed", "#grafik-abfall", "1.1.1/F3",
              "The chart alt only names the topic; the five yearly tonnages are not available in any text on the page.",
              distract=True, difficulty="medium", n_fill=rng.randint(0, 2), layout=0)


def f3_line(rng):
    months = MONTHS_SHORT["fr"]
    vals = [3120, 2980, 3310, 2640, 4210, 6950, 8820, 8460, 4890, 3020, 2870, 2550]
    src = asset("v-chart-pool-fr", line_chart("Entrées à la piscine, 2025", months, {"Entrées": vals},
                                              unit="entrées par mois", legend=False))
    main = ("<h1>Fréquentation 2025</h1><p>La piscine a connu une année record grâce à l'ouverture du bassin "
            "extérieur en été. La fréquentation a évolué au fil des saisons, comme le montre le graphique.</p>"
            f"<p>{img(src, 'Graphique de la fréquentation 2025', 640, 360, id='graphique-entrees')}</p>"
            "<p>Merci à toutes nos visiteuses et à tous nos visiteurs !</p>")
    return mk(rng, "fr", "sport", "Fréquentation 2025", main, "failed", "#graphique-entrees", "1.1.1/F3",
              "The line chart alt only names the topic; the monthly visitor numbers are nowhere in text.",
              difficulty="medium", n_fill=rng.randint(0, 2), layout=0)


def f3_pie(rng):
    labels = ["Istruzione", "Socialità e salute", "Trasporti", "Amministrazione", "Cultura e tempo libero", "Ambiente"]
    vals = [34, 22, 14, 12, 9, 9]
    src = asset("v-chart-budget-it", pie_chart("Spese comunali 2025 per settore", labels, vals))
    main = ("<h1>Consuntivo 2025</h1><p>Il Consiglio comunale ha approvato il consuntivo 2025, chiuso con un "
            "leggero avanzo. La ripartizione delle spese per settore è illustrata qui sotto.</p>"
            f"<p>{img(src, 'Grafico a torta delle spese', 520, 320, id='grafico-spese')}</p>"
            "<p>Il messaggio municipale completo è consultabile presso la cancelleria.</p>")
    return mk(rng, "it", "gemeinde", "Consuntivo 2025", main, "failed", "#grafico-spese", "1.1.1/F3",
              "The pie chart alt only says it is a pie chart of expenses; the shares per sector are not given in text.",
              distract=True, difficulty="medium")


def f4_print(rng):
    src = asset("v-ico-printer", pictogram("printer", color="#1d2327", size=28))
    main = ("<h1>Merkblatt Hundehaltung</h1>"
            f"<p class=\"werkzeuge\"><a href=\"merkblatt-hunde-druck.html\">{img(src, '', 28, 28)}</a></p>"
            "<p>Hunde müssen bis zum 31. März bei der Gemeindeverwaltung angemeldet werden. Die Hundetaxe beträgt "
            "CHF 120.– pro Hund und Jahr.</p><p>Im Siedlungsgebiet gilt von April bis Juli Leinenpflicht. "
            "Hundekot ist in den dafür vorgesehenen Behältern zu entsorgen.</p>")
    return mk(rng, "de", "gemeinde", "Merkblatt Hundehaltung", main, "failed", ".werkzeuge img", "1.1.1/F4",
              "The printer icon is the only content of the link to the print version but is marked decorative with alt=\"\", so the link has no name.",
              difficulty="medium")


def f4_detour(rng):
    src = asset("v-map-detour-it", detour_map(["Via Cantonale", "Via ai Monti", "Via alla Stazione", "Vicolo del Forno"],
                                              "chiuso"))
    main = ("<h1>Deviazione per lavori in Via Cantonale</h1><p>Dal 2 novembre al 18 dicembre 2026 la Via "
            "Cantonale è chiusa al traffico tra la piazza e il vicolo del Forno per il rinnovo delle condotte.</p>"
            "<p>Il percorso della deviazione è indicato sulla cartina:</p>"
            f"<p>{img(src, '', 640, 380, id='cartina-deviazione')}</p><p>I pedoni possono transitare sul marciapiede lato lago.</p>")
    return mk(rng, "it", "gemeinde", "Deviazione Via Cantonale", main, "failed", "#cartina-deviazione", "1.1.1/F4",
              "The detour map is the only source of the detour route but has alt=\"\", so the information is lost.",
              distract=True, difficulty="medium", n_fill=rng.randint(0, 2), layout=0)


def f5_bus(rng):
    src = asset("v-scene-bus-5", scene("bus", seed=5))
    main = ("<h1>Neue Velostation beim Bahnhof</h1><p>Ab 1. November stehen beim Bahnhof 240 gedeckte "
            "Veloabstellplätze zur Verfügung, davon 40 mit Ladestation für E-Bikes. Die Velostation ist rund um "
            "die Uhr zugänglich.</p>"
            f"<p>{img(src, 'Die neue Velostation mit gedeckten Abstellplätzen', 480, 300, id='bild-velostation')}</p>"
            "<p>Ein Jahresabo kostet CHF 60.–, eine Tageskarte CHF 2.–.</p>")
    return mk(rng, "de", "gemeinde", "Neue Velostation", main, "failed", "#bild-velostation", "1.1.1/F5",
              "The alt claims the picture shows the bike station, but the image shows a red bus; the alternative does not match the image.",
              distract=True, difficulty="hard")


def f5_chart(rng):
    vals = [138, 141, 145, 149, 152]
    src = asset("v-chart-water-fr", bar_chart("Consommation d'eau potable (litres par habitant et par jour)",
                                              ["2021", "2022", "2023", "2024", "2025"], vals, unit="litres",
                                              color="#2d9cdb"))
    alt = ("Consommation d'eau par habitant de 2021 à 2025 : baisse régulière de 152 à 138 litres par jour")
    main = ("<h1>Eau potable : chiffres clés</h1><p>Le Service des eaux publie chaque année l'évolution de la "
            "consommation des ménages.</p>"
            f"<p>{img(src, alt, 640, 360, id='graphique-eau')}</p><p>Le rapport de gestion est disponible au guichet.</p>")
    return mk(rng, "fr", "werke", "Eau potable", main, "failed", "#graphique-eau", "1.1.1/F5",
              "The alt states a decrease from 152 to 138 litres, but the chart shows an increase from 138 (2021) to 152 (2025).",
              distract=True, difficulty="hard")


# ---------------------------------------------------------------------------
# PASSED (non-trap)
# ---------------------------------------------------------------------------

def p1_market(rng):
    src = asset("v-scene-market-6", scene("market", seed=6))
    main = ("<h1>Le marché du samedi déménage</h1><p>Pendant les travaux de la place du Village, le marché "
            "hebdomadaire se tiendra sur la place de la Gare, du 7 novembre au 19 décembre, de 8 h à 12 h.</p>"
            f"<p>{img(src, 'Trois stands du marché sous des auvents de couleur', 480, 300, id='photo-marche')}</p>"
            "<p>Les places de stationnement de la gare seront réservées aux marchands le samedi matin.</p>")
    return mk(rng, "fr", "gemeinde", "Marché du samedi", main, "passed", "#photo-marche", "1.1.1/P1",
              "The illustrative photo has a short alt describing what it shows.", distract=True, difficulty="easy")


def p1_library(rng):
    src = asset("v-scene-library-7", scene("library", seed=7))
    main = ("<h1>La biblioteca rinnovata riapre</h1><p>Dopo otto mesi di lavori la biblioteca riapre lunedì "
            "con orari prolungati: da martedì a venerdì 10.00–19.00, sabato 9.00–16.00.</p>"
            f"<p>{img(src, 'La facciata rinnovata della biblioteca, con il tetto rosso e il nuovo ingresso', 480, 300, id='foto-biblioteca')}</p>"
            "<p>All'interno vi attendono una nuova sala di lettura e un angolo per i più piccoli.</p>")
    return mk(rng, "it", "bibliothek", "Riapertura della biblioteca", main, "passed", "#foto-biblioteca", "1.1.1/P1",
              "The photo of the renovated building has a descriptive alt.", distract=True, difficulty="easy")


def p1_lake_en(rng):
    src = asset("v-scene-lake-8", scene("lake", seed=8))
    main = ("<h1>Rooms with a view</h1><p>All our dormitories and family rooms face the lake. Breakfast is "
            "served on the terrace from May to September.</p>"
            f"<p>{img(src, 'View from the hostel terrace across the lake to the mountains', 480, 300, id='photo-view')}</p>"
            "<p>A family room for four costs CHF 140.– per night, breakfast included.</p>")
    return mk(rng, "en", "tourism", "Rooms", main, "passed", "#photo-view", "1.1.1/P1",
              "The view photo has a short descriptive alt.", difficulty="easy")


def p2_table(rng):
    years = ["2021", "2022", "2023", "2024", "2025"]
    vals = [162, 158, 155, 151, 149]
    src = asset("v-chart-water-de", bar_chart("Wasserverbrauch pro Kopf und Tag (Liter)", years, vals,
                                              unit="Liter pro Person und Tag", color="#1f6f8b"))
    rows = "".join(f"<tr><td>{y}</td><td>{v}</td></tr>" for y, v in zip(years, vals))
    alt = "Säulendiagramm Wasserverbrauch pro Kopf 2021 bis 2025; die Werte stehen in der Tabelle unter der Grafik"
    main = ("<h1>Wasserverbrauch</h1><p>Der durchschnittliche Wasserverbrauch der Haushalte ist in den letzten "
            "fünf Jahren leicht gesunken.</p>"
            f"<p>{img(src, alt, 640, 360, id='grafik-wasser')}</p>"
            "<table><caption>Wasserverbrauch pro Kopf und Tag</caption><thead><tr><th>Jahr</th><th>Liter</th></tr>"
            f"</thead><tbody>{rows}</tbody></table>")
    return mk(rng, "de", "werke", "Wasserverbrauch", main, "passed", "#grafik-wasser", "1.1.1/P2",
              "The chart has a short alt and the same values are given in the adjacent data table.", distract=True, difficulty="medium")


def p2_describedby(rng):
    q = ["1er trim.", "2e trim.", "3e trim.", "4e trim."]
    vals = [4820, 4310, 3650, 5140]
    src = asset("v-chart-loans-fr", bar_chart("Prêts par trimestre, 2025", q, vals, unit="prêts", color="#8e5ea2"))
    main = ("<h1>Bilan 2025</h1><p>La bibliothèque a accueilli plus de lecteurs que jamais.</p>"
            f"<p>{img(src, 'Graphique des prêts par trimestre en 2025', 640, 360, aria_describedby='desc-prets', id='graphique-prets')}</p>"
            "<p id=\"desc-prets\">En 2025, la bibliothèque a enregistré 4 820 prêts au premier trimestre, 4 310 au "
            "deuxième, 3 650 au troisième et 5 140 au quatrième, soit 17 920 prêts au total.</p>")
    return mk(rng, "fr", "bibliothek", "Bilan 2025", main, "passed", "#graphique-prets", "1.1.1/P2",
              "The chart has a short alt plus an aria-describedby paragraph that gives all four values.",
              difficulty="medium")


def p2_details(rng):
    labels = ["Rifiuti urbani", "Carta e cartone", "Scarti vegetali", "Vetro", "Altro", "Metalli"]
    vals = [38, 21, 19, 14, 5, 3]
    src = asset("v-chart-waste-it", pie_chart("Rifiuti raccolti nel 2025", labels, vals))
    rows = "".join(f"<tr><td>{esc(l)}</td><td>{v} %</td></tr>" for l, v in zip(labels, vals))
    main = ("<h1>Raccolta dei rifiuti 2025</h1><p>Nel 2025 sono state raccolte 2 140 tonnellate di rifiuti, "
            "il 3 % in meno rispetto all'anno precedente.</p>"
            f"<p>{img(src, 'Grafico a torta della ripartizione dei rifiuti raccolti nel 2025 (dati nella tabella sotto)', 520, 320, id='grafico-rifiuti')}</p>"
            "<details><summary>Dati del grafico</summary><table><thead><tr><th>Categoria</th><th>Quota</th></tr>"
            f"</thead><tbody>{rows}</tbody></table></details>")
    return mk(rng, "it", "werke", "Raccolta dei rifiuti", main, "passed", "#grafico-rifiuti", "1.1.1/P2",
              "The pie chart has a short alt and the full data is in a table inside the following details element.",
              difficulty="medium")


def p3_input_image(rng):
    src = asset("v-ico-search-dark", pictogram("search", color="#ffffff", bg="#0b4f6c", size=36))
    main = ("<h1>Rechercher un horaire</h1><p>Indiquez un arrêt pour afficher les prochains départs.</p>"
            "<form action=\"departs.html\" role=\"search\"><label for=\"arret\">Arrêt</label>"
            f"<input type=\"text\" id=\"arret\" name=\"arret\"> <input type=\"image\" src=\"{src}\" alt=\"Rechercher\" "
            "width=\"36\" height=\"36\"></form><p>Les horaires tiennent compte des perturbations annoncées.</p>")
    return mk(rng, "fr", "verkehr", "Horaires", main, "passed", 'input[type="image"]', "1.1.1/P3",
              "The image submit button has alt='Rechercher', which names its function.", difficulty="easy")


def p3_area(rng):
    names = ["Monte", "Centro", "Lago"]
    src = asset("v-map-zones-it", zones_map(names))
    ids = {"Centro": ' id="q-centro"'}
    areas = "".join(f'<area shape="poly" coords="{c}" href="quartiere-{slug(n)}.html" alt="Quartiere {n}"{ids.get(n, "")}>'
                    for c, n in zip(AREA_POLYS, names))
    main = ("<h1>Giorni di raccolta per quartiere</h1><p>Scegliete il vostro quartiere sulla cartina per "
            "vedere il calendario della raccolta dei rifiuti.</p>"
            f"<p>{img(src, 'Cartina dei tre quartieri', 600, 360, usemap='#quartieri')}</p>"
            f"<map name=\"quartieri\">{areas}</map>")
    return mk(rng, "it", "gemeinde", "Raccolta per quartiere", main, "passed", "#q-centro", "1.1.1/P3",
              "The image-map area has alt='Quartiere Centro', naming the link destination.", difficulty="easy")


def p3_svg_status(rng):
    main = ("<h1>Anlagen heute</h1><p>Stand 7.30 Uhr. Bei Gewitter werden die Aussenanlagen kurzfristig "
            "geschlossen.</p><ul class=\"stato\">"
            f"<li>{status_svg(True, 'geöffnet')} Hallenbad</li>"
            f"<li id=\"eisbahn\">{status_svg(False, 'geschlossen')} Kunsteisbahn</li>"
            f"<li>{status_svg(True, 'geöffnet')} Sauna</li></ul>"
            "<p>Auskunft: Telefon {PHONE}</p>")
    return mk(rng, "de", "sport", "Anlagen heute", main, "passed", "#eisbahn svg", "1.1.1/P3",
              "The status icon is an svg role=img with aria-label 'geschlossen', conveying the state in text.",
              distract=True, difficulty="medium")


# ---------------------------------------------------------------------------
# PASSED — exception traps
# ---------------------------------------------------------------------------

def t1_ornament_de(rng):
    src = asset("v-orn-leaves-green", ornament("leaves", color="#9cbf8a"))
    main = ("<h1>Programm Herbstmarkt</h1><h2>Samstag, 17. Oktober</h2><p>9.00 Uhr Marktbeginn auf dem "
            "Dorfplatz<br>11.00 Uhr Konzert der Musikgesellschaft<br>14.00 Uhr Kürbisschnitzen für Kinder</p>"
            f"<p>{img(src, '', 600, 24, class_='zier')}</p>"
            "<h2>Sonntag, 18. Oktober</h2><p>10.00 Uhr Gottesdienst im Festzelt<br>12.00 Uhr Mittagessen<br>"
            "16.00 Uhr Schluss</p>")
    return mk(rng, "de", "gemeinde", "Herbstmarkt", main, "passed", "img.zier", "1.1.1/T1",
              "The leaf ornament between the two days is purely decorative and correctly has alt=\"\".",
              trap=True, difficulty="easy")


def t1_ornament_it(rng):
    src = asset("v-orn-wave-blue", ornament("wave", color="#8fb3d0"))
    main = ("<h1>Corsi di nuoto per adulti</h1><p>I corsi si svolgono il martedì e il giovedì dalle 19.30 alle "
            "20.30. Gruppi di massimo otto persone.</p>"
            f"<p>{img(src, '', 600, 24, role='presentation')}</p>"
            "<h2>Iscrizioni</h2><p>Quota: CHF 180.– per dieci lezioni. Iscrizioni alla cassa della piscina.</p>")
    return mk(rng, "it", "sport", "Corsi di nuoto", main, "passed", 'img[role="presentation"]', "1.1.1/T1",
              "The wave divider is decoration and is hidden with alt=\"\" and role=presentation.",
              trap=True, difficulty="easy")


def t2_download_fr(rng):
    src = asset("v-ico-download", pictogram("download", color="#0b4f6c", size=28))
    main = ("<h1>Horaire d'hiver</h1><p>L'horaire d'hiver est valable du 13 décembre 2026 au 12 avril 2027. "
            "Le bus de nuit circule les vendredis et samedis.</p>"
            f"<p><a href=\"horaire-hiver.pdf\">{img(src, '', 28, 28, class_='tool-icon')}Télécharger l'horaire "
            "d'hiver (PDF, 240 Ko)</a></p>")
    return mk(rng, "fr", "verkehr", "Horaire d'hiver", main, "passed", "main a img", "1.1.1/T2",
              "The download icon has alt=\"\" but sits inside a link whose visible text already says what it does.",
              trap=True, difficulty="medium", n_fill=rng.randint(0, 1))


def t2_mail_de(rng):
    src = asset("v-ico-mail-blue", pictogram("mail", color="#0b5394", size=24))
    main = ("<h1>Fernleihe</h1><p>Medien, die nicht in unserem Bestand sind, bestellen wir gerne bei einer "
            "anderen Bibliothek. Die Gebühr beträgt CHF 5.– pro Medium.</p>"
            f"<p id=\"bestellen\"><a href=\"mailto:fernleihe@{{HOST}}\">{img(src, '', 24, 24, class_='tool-icon')}"
            "Fernleihe per E-Mail bestellen</a></p>")
    return mk(rng, "de", "bibliothek", "Fernleihe", main, "passed", "#bestellen img", "1.1.1/T2",
              "The envelope icon is redundant with the link text in the same link, so alt=\"\" is appropriate.",
              trap=True, difficulty="medium", n_fill=rng.randint(0, 1))


def t3_logo_it(rng):
    org = "Trasporti pubblici di Modellina"
    src = asset("v-logo-tpm", logo_svg("TPM", "Trasporti pubblici"))
    logo = img(src, "Trasporti pubblici di Modellina – pagina iniziale", 240, 52, id="logo")
    main = ("<h1>Abbonamenti 2027</h1><p>Gli abbonamenti annuali per il 2027 sono in vendita dal 1° dicembre. "
            "Ragazzi fino a 25 anni: CHF 390.–; adulti: CHF 590.–.</p><p>Gli abbonamenti si possono acquistare allo "
            "sportello della stazione o online.</p>")
    return mk(rng, "it", "verkehr", "Abbonamenti", main, "passed", "#logo", "1.1.1/T3",
              "The logo in the home link has an alt naming the organisation and the link function, which is the appropriate alternative.",
              trap=True, difficulty="medium", org=org, chrome=True, logo_html=logo)


def t4_velo(rng):
    bike = asset("v-ico-bike", pictogram("bike", color="#1d2327", size=32))
    bus = asset("v-ico-bus", pictogram("bus", color="#1d2327", size=32))
    main = ("<h1>Mobilität am Bahnhof</h1><p>Am Bahnhof finden Sie verschiedene Angebote für die "
            "Weiterreise.</p><table><thead><tr><th>Angebot</th><th>Ort</th><th>Hinweis</th></tr></thead><tbody>"
            f"<tr><td id=\"zeile-velo\">{img(bike, 'Velo', 32, 32)}</td><td>Velostation Nord</td><td>240 Plätze, gedeckt</td></tr>"
            f"<tr><td>{img(bus, 'Bus', 32, 32)}</td><td>Bahnhofplatz</td><td>Linien 1, 4 und 7</td></tr>"
            "</tbody></table>")
    return mk(rng, "de", "verkehr", "Mobilität am Bahnhof", main, "passed", "#zeile-velo img", "1.1.1/T4",
              "The one-word alt 'Velo' fully conveys what the pictogram means in this table.",
              trap=True, difficulty="medium")


def t5_sign(rng):
    src = asset("v-sign-quiz", sign_svg())
    opts = ["Radweg", "Fussweg", "Fahrverbot für Velos"]
    radios = "".join(f'<p><input type="radio" name="f3" id="f3-{i}" value="{i}"> <label for="f3-{i}" '
                     f'style="display:inline;font-weight:400">{o}</label></p>' for i, o in enumerate(opts, 1))
    main = ("<h1>Veloprüfung: Übungsfragen</h1><p>Mit diesen Fragen können sich die Kinder der 5. Klasse auf "
            "die theoretische Veloprüfung vorbereiten. Die Lösungen besprechen wir im Unterricht.</p>"
            "<form action=\"auswertung.html\"><fieldset><legend>Frage 3: Was bedeutet dieses Signal?</legend>"
            f"<p>{img(src, 'Signal zu Frage 3', 160, 160, id='signal-3')}</p>{radios}</fieldset>"
            "<p><button type=\"submit\">Antwort prüfen</button></p></form>")
    return mk(rng, "de", "schule", "Veloprüfung", main, "passed", "#signal-3", "1.1.1/T5",
              "The sign is the object of a test question; describing it in the alt would give away the answer, so descriptive identification ('Signal zu Frage 3') is sufficient.",
              trap=True, difficulty="hard")


def t5_leaf(rng):
    src = asset("v-leaf-quiz", leaf_svg())
    opts = ["Érable", "Chêne", "Hêtre"]
    radios = "".join(f'<p><input type="radio" name="q2" id="q2-{i}" value="{i}"> <label for="q2-{i}" '
                     f'style="display:inline;font-weight:400">{o}</label></p>' for i, o in enumerate(opts, 1))
    main = ("<h1>Quiz nature – 6e année</h1><p>Après la sortie en forêt, testez vos connaissances. Les réponses "
            "seront corrigées en classe.</p><form action=\"quiz-envoi.html\"><fieldset><legend>Question 2 : de "
            "quel arbre provient cette feuille ?</legend>"
            f"<p>{img(src, 'Feuille de la question 2', 240, 250, id='feuille-2')}</p>{radios}</fieldset>"
            "<p><button type=\"submit\">Envoyer mes réponses</button></p></form>")
    return mk(rng, "fr", "schule", "Quiz nature", main, "passed", "#feuille-2", "1.1.1/T5",
              "The leaf is the object of an identification exercise; the alt identifies it without giving the answer, as the test exception allows.",
              trap=True, difficulty="hard")


def n1_pixel(rng):
    src = asset("v-px", PIXEL)
    main = ("<h1>Albo comunale</h1><p>Sono pubblicati all'albo comunale:</p><ul>"
            "<li>Domanda di costruzione, mappale 412, Via ai Monti – dal 5 al 19 ottobre 2026</li>"
            "<li>Ordinanza sulla circolazione in Piazza Grande durante il mercato</li>"
            "<li>Avviso di convocazione del Consiglio comunale del 9 novembre 2026</li></ul>"
            "<p>Eventuali opposizioni vanno inoltrate per iscritto alla Cancelleria comunale entro il termine.</p>"
            f"{img(src, None, 1, 1, style='display:none')}")
    return mk(rng, "it", "gemeinde", "Albo comunale", main, "inapplicable", 'img[style="display:none"]', "1.1.1/N1",
              "The only image is a display:none statistics pixel that is not presented to anyone, so there is no non-text content to evaluate.",
              trap=True, difficulty="medium")


# ---------------------------------------------------------------------------
# CANTTELL
# ---------------------------------------------------------------------------

def c1_library(rng):
    src = asset("v-scene-library-7", scene("library", seed=7))
    main = ("<h1>Bibliothek nach Renovation wieder offen</h1><p>Seit Montag ist die Bibliothek nach achtmonatiger "
            "Renovation wieder geöffnet. Die Fassade wurde saniert, der Eingang ist neu stufenlos erreichbar.</p>"
            f"<p>{img(src, '', 480, 300, id='bild-fassade')}</p>"
            "<p>Neue Öffnungszeiten: Dienstag bis Freitag 10.00–19.00 Uhr, Samstag 9.00–16.00 Uhr.</p>")
    return mk(rng, "de", "bibliothek", "Wiedereröffnung", main, "cantTell", "#bild-fassade", "1.1.1/C1",
              "Picture of the renovated building marked alt=\"\"; the text mentions the facade only generally, so whether the picture is decorative or conveys the new appearance depends on author intent.",
              distract=True, difficulty="hard")


def c1_bus(rng):
    src = asset("v-scene-bus-9", scene("bus", seed=9))
    main = ("<h1>Un bus électrique sur la ligne 3</h1><p>Depuis lundi, un bus électrique circule à titre "
            "d'essai sur la ligne 3. Plus silencieux, il dispose de deux emplacements pour poussettes.</p>"
            f"<p>{img(src, '', 480, 300, id='photo-bus')}</p>"
            "<p>L'essai dure jusqu'à fin mars. Vos impressions nous intéressent : écrivez-nous.</p>")
    return mk(rng, "fr", "verkehr", "Bus électrique", main, "cantTell", "#photo-bus", "1.1.1/C1",
              "Photo of the new bus marked alt=\"\"; it is unclear from the page whether showing the vehicle's appearance is information or illustration.",
              distract=True, difficulty="hard")


def c2_art_it(rng):
    src = asset("v-scene-lake-10", scene("lake", seed=10))
    main = ("<h1>Opera del mese: «Lago d'autunno»</h1>"
            f"<p>{img(src, '«Lago d’autunno», tempera di Elsa Fittizia, 1931', 480, 300, id='opera-mese')}</p>"
            "<p>La tempera fu donata al museo nel 1978 dagli eredi dell'artista, che per oltre trent'anni dipinse "
            "dal suo atelier sopra la filanda. L'opera è esposta fino al 30 novembre nella sala al primo piano.</p>"
            "<p>Visita guidata gratuita: domenica 8 novembre alle 15.00.</p>")
    return mk(rng, "it", "museum", "Opera del mese", main, "cantTell", "#opera-mese", "1.1.1/C2",
              "The painting's alt only identifies the work; whether it is sensory content (identification suffices) or informative content needing a description depends on the page's purpose.",
              difficulty="hard")


def c2_art_fr(rng):
    src = asset("v-scene-snow-11", scene("snow", seed=11))
    main = ("<h1>L'œuvre du mois : « Hiver au moulin »</h1><p>Cette gouache de Jules Modèle (1907) a rejoint la "
            "collection en 1992. Le peintre, fils de meunier, a consacré une série entière aux saisons du "
            "vallon.</p>"
            f"<p>{img(src, '« Hiver au moulin », gouache de Jules Modèle, 1907', 480, 300, id='oeuvre-mois')}</p>"
            "<p>À voir jusqu'au 31 janvier dans la salle des meules.</p>")
    return mk(rng, "fr", "museum", "L'œuvre du mois", main, "cantTell", "#oeuvre-mois", "1.1.1/C2",
              "Artwork identified only by title/artist/date; whether the sensory-experience exception applies or a description of its content is needed cannot be decided from the page.",
              difficulty="hard")


def c3_lake_level(rng):
    months = MONTHS_SHORT["it"]
    vals = [112, 108, 121, 145, 168, 172, 150, 131, 120, 118, 115, 110]
    src = asset("v-chart-lakelevel-it", line_chart("Altezza all'idrometro del porto, 2025 (cm)", months,
                                                   {"Livello": vals}, unit="cm", legend=False))
    main = ("<h1>Livello del lago 2025</h1><p>Le precipitazioni di maggio e giugno hanno portato il lago al "
            "livello più alto degli ultimi dieci anni.</p>"
            f"<p>{img(src, 'Grafico del livello del lago nel 2025; descrizione dettagliata nel documento collegato', 640, 360, id='grafico-livello')}</p>"
            "<p><a href=\"livello-lago-2025-descrizione.pdf\">Descrizione testuale del grafico (PDF, 40 kB)</a></p>")
    return mk(rng, "it", "werke", "Livello del lago", main, "cantTell", "#grafico-livello", "1.1.1/C3",
              "The chart has a short alt and a long description only in a linked PDF that is not part of the page, so equivalence cannot be verified.",
              alt_expected="passed", distract=True, difficulty="hard")


def c3_network(rng):
    lines = [("1", "#c2453b", ["Bahnhof", "Post", "Schulhaus", "Seeweg", "Spital"]),
             ("4", "#1f6f8b", ["Bahnhof", "Kirche", "Sportzentrum", "Oberdorf"]),
             ("7", "#3c8d4f", ["Bahnhof", "Industrie", "Mühlegasse", "Waldrand", "Friedhof"])]
    src = asset("v-network-de", network_svg(lines))
    main = ("<h1>Liniennetz ab Fahrplanwechsel</h1><p>Ab 13. Dezember 2026 fährt die Linie 7 neu bis zum "
            "Friedhof. Alle Linien verkehren werktags im Viertelstundentakt.</p>"
            f"<p>{img(src, 'Liniennetzplan der Verkehrsbetriebe, gültig ab 13.12.2026', 680, 320, id='netzplan')}</p>"
            "<p><a href=\"liniennetz-textversion.pdf\">Liniennetz als Textversion (PDF, 85 KB)</a></p>")
    return mk(rng, "de", "verkehr", "Liniennetz", main, "cantTell", "#netzplan", "1.1.1/C3",
              "The network plan has a short alt; the full long description exists only as a linked PDF outside the page.",
              alt_expected="passed", distract=True, difficulty="hard")


BUILDERS = [
    f1_playground, f1_bridge, f1_input_image, f1_area, f1_svg_status,
    f2_bild, f2_filename, f2_grafico, f2_icone,
    f3_bar, f3_line, f3_pie,
    f4_print, f4_detour,
    f5_bus, f5_chart,
    p1_market, p1_library, p1_lake_en, p2_table, p2_describedby, p2_details,
    p3_input_image, p3_area, p3_svg_status,
    t1_ornament_de, t1_ornament_it, t2_download_fr, t2_mail_de, t3_logo_it, t4_velo, t5_sign, t5_leaf, n1_pixel,
    c1_library, c1_bus, c2_art_it, c2_art_fr, c3_lake_level, c3_network,
]


def build(rng):
    return [b(rng) for b in BUILDERS]
