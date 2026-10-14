"""1.4.5 Images of Text — 26 cases (protocol rules 1.4.5/F1–F4, P1–P2, T1–T5, C1–C2)."""
from common import *
from _visual_util import compose, doc, img, org_of, host_of, phone
from c_1_1_1 import network_svg, logo_svg

CRITERION = "1.4.5"


def mk(rng, lang, kind, title, main, expected, target, rule, notes, *, trap=False, alt_expected=None,
       difficulty="medium", css="", theme=None, org=None, head="", **kw):
    org = org or org_of(rng, lang, kind)
    main = main.replace("{ORG}", esc(org)).replace("{HOST}", host_of(org)).replace("{PHONE}", phone(rng))
    body, lcss = compose(rng, lang, org, main, kind=kind, **kw)
    html = doc(rng, lang, title, org, body, lcss + css, theme=theme, head=head)
    return Case(CRITERION, lang, expected, html=html, target=target, rule=rule, notes=notes, trap=trap,
                alt_expected=alt_expected, difficulty=difficulty)


def _svg(w, h, inner, extra=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"{extra}>'
            f'{inner}</svg>')


def _text(x, y, s, size, fill, *, weight=400, anchor="start", font="Arial, sans-serif", style=""):
    st = f' font-style="{style}"' if style else ""
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{font}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}"{st}>{esc(s)}</text>')


def btn_svg(label, bg, bg2, fg, w=220, h=56, size=22):
    inner = (f'<defs><linearGradient id="b" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{bg}"/>'
             f'<stop offset="1" stop-color="{bg2}"/></linearGradient></defs>'
             f'<rect x="1" y="3" width="{w - 2}" height="{h - 4}" rx="10" fill="#00000033"/>'
             f'<rect x="0" y="0" width="{w - 2}" height="{h - 4}" rx="10" fill="url(#b)"/>'
             + _text((w - 2) / 2, (h - 4) / 2 + size * 0.36, label, size, fg, weight=700, anchor="middle"))
    return _svg(w, h, inner)


def title_svg(label, color, w, h, size, accent):
    inner = (_text(4, h * 0.62, label, size, color, weight=700, font="Georgia, 'Times New Roman', serif", style="italic")
             + f'<path d="M6 {h * 0.8:.0f} C {w * 0.3:.0f} {h * 0.7:.0f}, {w * 0.6:.0f} {h * 0.95:.0f}, {w - 10} {h * 0.78:.0f}" '
               f'fill="none" stroke="{accent}" stroke-width="4" stroke-linecap="round"/>')
    return _svg(w, h, inner)


def table_svg(title, header, rows, widths, *, accent="#1f6f8b"):
    rh, top = 34, 56
    w = sum(widths) + 2
    h = top + rh * (len(rows) + 1) + 12
    p = [f'<rect width="{w}" height="{h}" fill="#ffffff"/>', _text(4, 32, title, 22, "#1d2327", weight=700),
         f'<rect x="1" y="{top}" width="{sum(widths)}" height="{rh}" fill="{accent}"/>']
    x = 1
    for wd, hd in zip(widths, header):
        p.append(_text(x + 10, top + 23, hd, 15, "#ffffff", weight=700))
        x += wd
    for i, row in enumerate(rows):
        y = top + rh * (i + 1)
        if i % 2:
            p.append(f'<rect x="1" y="{y}" width="{sum(widths)}" height="{rh}" fill="#eef3f6"/>')
        x = 1
        for wd, cell in zip(widths, row):
            p.append(_text(x + 10, y + 23, cell, 15, "#1d2327"))
            x += wd
        p.append(f'<line x1="1" y1="{y + rh}" x2="{sum(widths) + 1}" y2="{y + rh}" stroke="#c9d3d8"/>')
    return _svg(w, h, "".join(p))


def logo_dark(word1, word2, icon="leaf", col="#2f5d34"):
    inner = (f'<g fill="none" stroke="{col}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
             f'transform="translate(6 10) scale(1.4)">{ICONS[icon]}</g>'
             + _text(52, 27, word1, 19, col, weight=700, font="Georgia, serif")
             + _text(52, 47, word2, 13, "#1d2327", font="Georgia, serif"))
    return _svg(250, 58, '<rect width="250" height="58" fill="#ffffff"/>' + inner)


def with_overlay(svg, overlay):
    assert svg.endswith("</svg>")
    return svg[:-6] + overlay + "</svg>"


def market_sign(seed, label):
    w, h = 480, 300
    sign = (f'<rect x="{w * .32:.0f}" y="{h * .12:.0f}" width="{w * .36:.0f}" height="{h * .12:.0f}" rx="6" fill="#6d4c41"/>'
            f'<line x1="{w * .36:.0f}" y1="{h * .24:.0f}" x2="{w * .36:.0f}" y2="{h * .5:.0f}" stroke="#6d4c41" stroke-width="5"/>'
            f'<line x1="{w * .64:.0f}" y1="{h * .24:.0f}" x2="{w * .64:.0f}" y2="{h * .5:.0f}" stroke="#6d4c41" stroke-width="5"/>'
            + _text(w / 2, h * .21, label, 24, "#fff7e6", weight=700, anchor="middle"))
    return with_overlay(scene("market", seed=seed), sign)


def bag_svg(lines):
    p = ['<rect width="360" height="420" fill="#f4f6f8"/>',
         '<path d="M150 40 Q180 10 210 40 L225 70 L135 70 Z" fill="#d9e2ea"/>',
         '<path d="M70 70 H290 L320 400 H40 Z" fill="#e9eef3" stroke="#9aa9b6" stroke-width="2"/>',
         '<rect x="95" y="130" width="170" height="190" rx="8" fill="#ffffff" stroke="#c2453b" stroke-width="4"/>',
         '<g fill="none" stroke="#c2453b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
         'transform="translate(160 146) scale(1.7)">' + ICONS["bin"] + '</g>']
    y = 222
    for i, (s, size, wt) in enumerate(lines):
        p.append(_text(180, y, s, size, "#c2453b", weight=wt, anchor="middle"))
        y += size + 10
    return _svg(360, 420, "".join(p))


def permit_svg(lines, band):
    p = ['<rect width="420" height="260" fill="#ffffff"/>',
         '<rect x="10" y="10" width="400" height="240" rx="16" fill="#fdfdfb" stroke="#9aa9b6" stroke-width="2"/>',
         f'<path d="M10 70 V26 Q10 10 26 10 H394 Q410 10 410 26 V70 Z" fill="{band}"/>',
         _text(210, 50, lines[0], 24, "#ffffff", weight=700, anchor="middle"),
         f'<circle cx="340" cy="160" r="46" fill="none" stroke="{band}" stroke-width="6"/>',
         _text(340, 176, lines[1], 44, band, weight=700, anchor="middle")]
    y = 125
    for s in lines[2:]:
        p.append(_text(36, y, s, 18, "#1d2327"))
        y += 32
    return _svg(420, 260, "".join(p))


def poster_svg(kind, seed, lines, bg):
    sc = scene(kind, w=480, h=330, seed=seed)
    inner = sc.replace('<svg xmlns="http://www.w3.org/2000/svg"', '<svg x="0" y="0"', 1)
    p = [f'<rect width="480" height="640" fill="{bg}"/>', inner]
    y = 400
    for s, size, wt in lines:
        p.append(_text(240, y, s, size, "#ffffff", weight=wt, anchor="middle", font="Georgia, serif"))
        y += size + 18
    return _svg(480, 640, "".join(p))


def facsimile_svg(head, title, paras, signer, stamp):
    p = ['<rect width="460" height="620" fill="#fbfaf4"/>',
         _text(40, 60, head, 15, "#2b2b2b", weight=700, font="'Times New Roman', serif"),
         '<line x1="40" y1="72" x2="420" y2="72" stroke="#2b2b2b" stroke-width="1"/>',
         _text(40, 118, title, 19, "#1a1a1a", weight=700, font="'Times New Roman', serif")]
    y = 156
    for para in paras:
        for line in para:
            p.append(_text(40, y, line, 14, "#2b2b2b", font="'Times New Roman', serif"))
            y += 21
        y += 12
    p.append(f'<path d="M250 {y + 40} c20 -30 30 10 45 -12 s20 -10 30 8 s25 -20 40 -4" fill="none" stroke="#1d3c8a" '
             f'stroke-width="2.2" stroke-linecap="round"/>')
    p.append(_text(250, y + 70, signer, 13, "#2b2b2b", font="'Times New Roman', serif"))
    p.append(f'<circle cx="110" cy="{y + 50}" r="44" fill="none" stroke="#7a3fa0" stroke-width="3" opacity="0.8"/>'
             f'<circle cx="110" cy="{y + 50}" r="34" fill="none" stroke="#7a3fa0" stroke-width="1.5" opacity="0.8"/>'
             + _text(110, y + 55, stamp, 12, "#7a3fa0", weight=700, anchor="middle"))
    return _svg(460, 620, "".join(p))


# ---------------------------------------------------------------------------
# FAILED
# ---------------------------------------------------------------------------

def f1_banner_de(rng):
    lines = ["Gemeindeversammlung", "Mittwoch, 2. Dezember 2026, 20.00 Uhr", "Mehrzweckhalle"]
    src = asset("v-banner-versammlung-de", banner(lines, bg="#0b4f6c", accent="#e07a2e"))
    main = (f"<p>{img(src, ', '.join(lines), 800, 220, id='banner-versammlung')}</p>"
            "<h1>Einladung</h1><p>Die Stimmberechtigten werden zur ordentlichen Gemeindeversammlung eingeladen. "
            "Traktanden: Budget 2027, Kreditantrag Sanierung Schulhausdach, Verschiedenes.</p>"
            "<p>Die Unterlagen liegen ab 16. November auf der Gemeindekanzlei auf.</p>")
    return mk(rng, "de", "gemeinde", "Gemeindeversammlung", main, "failed", "#banner-versammlung", "1.4.5/F1",
              "The banner is an image whose only content is the date/place text, which could be HTML text; a correct alt does not exempt it.",
              difficulty="easy")


def f1_banner_fr(rng):
    lines = ["Fête au village", "Samedi 28 août 2027 · dès 11 h", "Place du Village"]
    src = asset("v-banner-fete-fr", banner(lines, bg="#7a1f2b", accent="#d4a017", bg2="#a33a2b"))
    main = ("<h1>Agenda</h1>"
            f"<p>{img(src, ', '.join(lines), 800, 220, id='banner-fete')}</p>"
            "<p>Au programme : marché artisanal, concert de la fanfare et bal populaire. Les sociétés locales "
            "tiennent les stands de restauration.</p>")
    return mk(rng, "fr", "gemeinde", "Agenda", main, "failed", "#banner-fete", "1.4.5/F1",
              "Event title, date and place are rendered as a bitmap-like banner image instead of styled text.",
              difficulty="easy")


def f1_banner_it(rng):
    lines = ["Uffici comunali chiusi", "Da giovedì 24 dicembre a venerdì 1° gennaio", "Riapertura: lunedì 4 gennaio, ore 8.30"]
    src = asset("v-banner-chiusura-it", banner(lines, bg="#2f5d34", accent=None, sizes=[40, 22, 22]))
    main = (f"<p>{img(src, '. '.join(lines), 800, 220, id='avviso-chiusura')}</p>"
            "<h1>Festività di fine anno</h1><p>In caso di decesso durante la chiusura, rivolgersi al servizio di "
            "picchetto della Cancelleria, telefono {PHONE}.</p>")
    return mk(rng, "it", "gemeinde", "Festività", main, "failed", "#avviso-chiusura", "1.4.5/F1",
              "The closure notice is an image containing only text that could be presented as HTML text.",
              difficulty="easy")


def f2_button_de(rng):
    src = asset("v-btn-anmelden-de", btn_svg("Anmelden", "#3c8d4f", "#2f6f3e", "#ffffff"))
    main = ("<h1>Newsletter</h1><p>Einmal im Monat erhalten Sie die wichtigsten Neuigkeiten aus der Gemeinde per "
            "E-Mail. Sie können sich jederzeit wieder abmelden.</p><form action=\"newsletter-danke.html\" method=\"post\">"
            "<label for=\"mail\">E-Mail-Adresse</label><input type=\"email\" id=\"mail\" name=\"mail\">"
            f"<p><input type=\"image\" src=\"{src}\" alt=\"Anmelden\" width=\"220\" height=\"56\"></p></form>")
    return mk(rng, "de", "gemeinde", "Newsletter", main, "failed", 'input[type="image"]', "1.4.5/F2",
              "The submit button is an image of the word 'Anmelden' instead of a styled text button.",
              difficulty="medium")


def f2_cta_it(rng):
    src = asset("v-btn-iscriviti-it", btn_svg("Iscriviti ora", "#e07a2e", "#c2621c", "#ffffff", w=240))
    main = ("<h1>Corsi di lingua per adulti</h1><p>Inglese, francese e tedesco a tutti i livelli. I corsi "
            "iniziano la settimana del 18 gennaio e durano dodici serate.</p>"
            f"<p><a href=\"iscrizione-corsi.html\">{img(src, 'Iscriviti ora', 240, 56, id='pulsante-iscrizione')}</a></p>"
            "<p>Quota: CHF 240.– per corso, materiale incluso.</p>")
    return mk(rng, "it", "schule", "Corsi di lingua", main, "failed", "#pulsante-iscrizione", "1.4.5/F2",
              "The call-to-action is a linked image of the text 'Iscriviti ora' that could be a CSS-styled link.",
              difficulty="medium")


def f3_heading_fr(rng):
    src = asset("v-title-horaires-fr", title_svg("Horaires d'ouverture", "#0b4f6c", 460, 70, 38, "#e07a2e"))
    main = (f"<h1>{img(src, 'Horaires d’ouverture', 460, 70, id='titre-horaires')}</h1>"
            "<table><thead><tr><th>Jour</th><th>Matin</th><th>Après-midi</th></tr></thead><tbody>"
            "<tr><td>Mardi</td><td>–</td><td>14 h – 18 h</td></tr><tr><td>Mercredi</td><td>9 h – 12 h</td>"
            "<td>14 h – 18 h</td></tr><tr><td>Samedi</td><td>9 h – 12 h</td><td>–</td></tr></tbody></table>")
    return mk(rng, "fr", "bibliothek", "Horaires", main, "failed", "#titre-horaires", "1.4.5/F3",
              "The page heading is an image of decorative italic text; the same look is achievable with a web font and CSS.",
              difficulty="medium")


def f3_heading_de(rng):
    src = asset("v-title-senioren-de", title_svg("Unser Angebot für Seniorinnen und Senioren", "#7a1f2b", 700, 64, 28, "#d4a017"))
    main = ("<h1>Alter</h1><p>Die Gemeinde unterstützt ältere Menschen dabei, möglichst lange selbständig zu "
            "Hause zu leben.</p>"
            f"<h2>{img(src, 'Unser Angebot für Seniorinnen und Senioren', 700, 64, id='titel-angebot')}</h2>"
            "<ul><li>Mahlzeitendienst: CHF 14.– pro Menü</li><li>Fahrdienst zu Arztterminen</li>"
            "<li>Mittagstisch jeden Donnerstag im Kirchgemeindehaus</li></ul>")
    return mk(rng, "de", "gemeinde", "Alter", main, "failed", "#titel-angebot", "1.4.5/F3",
              "A section heading is rendered as an image of text.", difficulty="medium")


def f3_replace_it(rng):
    src = asset("v-title-mostre-it", title_svg("Mostre in corso", "#2b2f3a", 360, 64, 36, "#c2453b"))
    main = ("<h1>Museo della Filanda</h1><p>Il museo racconta la storia della lavorazione della seta nella "
            "valle, dal 1850 alla chiusura della filanda nel 1968.</p>"
            "<h2 class=\"titolo-mostre\">Mostre in corso</h2><ul><li>«Fili d'oro» – tessuti antichi, fino al "
            "10 gennaio</li><li>«Mani al lavoro» – fotografie 1920–1960, fino al 28 febbraio</li></ul>")
    css = (f".titolo-mostre{{background:url({src}) left center/contain no-repeat;height:64px;max-width:360px;"
           "text-indent:-9999px;overflow:hidden}")
    return mk(rng, "it", "museum", "Museo della Filanda", main, "failed", ".titolo-mostre", "1.4.5/F3",
              "The heading text is hidden and replaced by a CSS background image of the same words, with no way to switch back to text.",
              css=css, difficulty="hard")


def f4_prices_de(rng):
    rows = [("Erwachsene", "CHF 8.–", "CHF 70.–"), ("Kinder 6–16 Jahre", "CHF 4.–", "CHF 35.–"),
            ("Studierende, AHV/IV", "CHF 6.–", "CHF 52.–"), ("Familien", "CHF 20.–", "–")]
    src = asset("v-table-preise-de", table_svg("Eintrittspreise Hallenbad", ["Kategorie", "Einzeleintritt", "10er-Abo"],
                                              rows, [240, 170, 150]))
    alt = "Eintrittspreise Hallenbad: " + "; ".join(f"{a}: Einzeleintritt {b}, 10er-Abo {c}" for a, b, c in rows)
    main = ("<h1>Preise</h1><p>Die Preise gelten ab 1. Januar 2027. Kinder unter 6 Jahren baden gratis.</p>"
            f"<p>{img(src, alt, 562, 238, id='preistabelle')}</p>")
    return mk(rng, "de", "sport", "Preise Hallenbad", main, "failed", "#preistabelle", "1.4.5/F4",
              "The price list is a picture of a table; the same data could be an HTML table.", difficulty="easy")


def f4_hours_fr(rng):
    rows = [("Lundi", "fermé"), ("Mardi", "14 h – 18 h"), ("Mercredi", "9 h – 12 h / 14 h – 18 h"),
            ("Jeudi", "14 h – 19 h"), ("Samedi", "8 h – 16 h")]
    src = asset("v-table-dechetterie-fr", table_svg("Horaires de la déchetterie", ["Jour", "Heures d'ouverture"],
                                                   rows, [160, 300], accent="#2f5d34"))
    alt = "Horaires de la déchetterie : " + " ; ".join(f"{a} {b}" for a, b in rows)
    main = ("<h1>Déchetterie communale</h1><p>La déchetterie se trouve au chemin des Vignes 7. Les déchets "
            "spéciaux sont repris le premier samedi du mois.</p>"
            f"<p>{img(src, alt, 462, 272, id='horaires-dechetterie')}</p>")
    return mk(rng, "fr", "werke", "Déchetterie", main, "failed", "#horaires-dechetterie", "1.4.5/F4",
              "Opening hours are published as an image of a table instead of text.", difficulty="easy")


# ---------------------------------------------------------------------------
# PASSED
# ---------------------------------------------------------------------------

def p1_banner_de(rng):
    main = ("<div class=\"banner\" id=\"banner-einladung\"><p class=\"b1\">Gemeindeversammlung</p>"
            "<p class=\"b2\">Mittwoch, 9. Dezember 2026, 20.00 Uhr</p><p class=\"b2\">Turnhalle Schulhaus Dorf</p></div>"
            "<h1>Einladung</h1><p>Traktanden: Budget 2027, Teilrevision Abfallreglement, Varia. Die "
            "Akten können ab dem 23. November eingesehen werden.</p>")
    css = (".banner{background:linear-gradient(135deg,#0b4f6c,#1f6f8b);color:#ffffff;padding:22px 32px;"
           "border-radius:10px;position:relative;overflow:hidden;min-height:150px}"
           ".banner::after{content:'';position:absolute;right:-50px;top:-30px;width:220px;height:220px;"
           "border-radius:50%;background:#e07a2e;opacity:.85}"
           ".banner p{position:relative;z-index:1;margin:6px 0;max-width:70%}.b1{font-size:2.4rem;font-weight:700}"
           ".b2{font-size:1.3rem}")
    return mk(rng, "de", "gemeinde", "Gemeindeversammlung", main, "passed", "#banner-einladung", "1.4.5/P1",
              "The banner looks like a graphic but its text is real HTML text styled with CSS (the orange disc is a pseudo-element).",
              css=css, difficulty="medium")


def p1_cta_fr(rng):
    dots = asset("v-pattern-dots", ornament("dots", color="#ffffff", w=240, h=24))
    main = ("<h1>Cours de langues pour adultes</h1><p>Anglais, allemand et italien, tous niveaux. Début des "
            "cours la semaine du 18 janvier.</p><p><a class=\"cta\" href=\"inscription-cours.html\">S'inscrire "
            "maintenant</a></p><p>Prix : CHF 240.– par cours de douze soirées.</p>")
    css = (f".cta{{display:inline-block;padding:14px 28px;border-radius:10px;font-size:1.3rem;font-weight:700;"
           f"color:#ffffff;text-decoration:none;background:url({dots}) left bottom/120px 12px repeat-x,"
           "linear-gradient(#a33a2b,#7a1f2b);box-shadow:0 3px 0 #00000033}")
    return mk(rng, "fr", "schule", "Cours de langues", main, "passed", ".cta", "1.4.5/P1",
              "The call-to-action is real link text styled with CSS gradients and a decorative dot pattern that contains no text.",
              css=css, difficulty="medium")


def p1_heading_it(rng):
    main = ("<h1 class=\"titolo\">Benvenuti a Modellina</h1><p>Borgo di lago ai piedi dei monti, Modellina "
            "conta 3 400 abitanti e offre sentieri, spiagge libere e un centro storico pedonale.</p>"
            "<p>L'ufficio turistico in Piazza Grande è aperto tutti i giorni dalle 9.00 alle 17.00.</p>")
    css = (".titolo{font-family:Georgia,'Times New Roman',serif;font-style:italic;font-size:2.8rem;letter-spacing:.02em;"
           "color:#0b4f6c;text-shadow:2px 2px 0 #e9c46a;border-bottom:4px solid #e07a2e;display:inline-block}")
    return mk(rng, "it", "gemeinde", "Benvenuti", main, "passed", ".titolo", "1.4.5/P1",
              "The decorative display heading is HTML text styled with CSS (font, shadow, border), not an image.",
              css=css, difficulty="medium")


def p2_photo_it(rng):
    src = asset("v-scene-lake-14", scene("lake", seed=14))
    main = ("<h1>Spiagge libere</h1><p>Le tre spiagge libere del Comune sono sorvegliate dal 15 giugno al "
            "31 agosto, dalle 10.00 alle 18.00.</p>"
            f"<p>{img(src, 'Il lago con le montagne sullo sfondo, vista dalla spiaggia del Lido', 480, 300, id='foto-lido')}</p>")
    return mk(rng, "it", "gemeinde", "Spiagge libere", main, "passed", "#foto-lido", "1.4.5/P2",
              "The illustration contains no text at all.", difficulty="easy")


def t1_logo_de(rng):
    org = "Beispielwiler Verkehrsbetriebe"
    src = asset("v-logo-mvb", logo_svg("Beispielwil", "Verkehrsbetriebe"))
    logo = img(src, "Beispielwiler Verkehrsbetriebe – Startseite", 240, 52, id="logo")
    main = ("<h1>Störungen und Umleitungen</h1><p>Wegen Bauarbeiten an der Bahnhofstrasse verkehrt die Linie 4 "
            "vom 2. bis 13. November über den Kirchweg. Die Haltestelle Post wird nicht bedient.</p>")
    return mk(rng, "de", "verkehr", "Störungen", main, "passed", "#logo", "1.4.5/T1",
              "The header logo contains the company name as a logotype, which is essential and exempt.",
              trap=True, org=org, chrome=True, logo_html=logo, difficulty="medium")


def t1_logo_it(rng):
    src = asset("v-logo-fondazione-it", logo_dark("Fondazione Esempio", "per la cultura in valle"))
    main = ("<h1>Rassegna «Musica in piazza»</h1><p>Cinque concerti gratuiti, ogni venerdì di luglio alle 20.30 in "
            "Piazza Grande. In caso di pioggia i concerti si tengono nella chiesa parrocchiale.</p>"
            "<p>La rassegna è sostenuta da:</p>"
            f"<p>{img(src, 'Fondazione Esempio per la cultura in valle', 250, 58, id='logo-sostegno')}</p>")
    return mk(rng, "it", "gemeinde", "Musica in piazza", main, "passed", "#logo-sostegno", "1.4.5/T1",
              "The sponsor's logo includes its name as a wordmark; logotypes are considered essential.",
              trap=True, difficulty="medium")


def t2_chart_fr(rng):
    months = ["janv.", "févr.", "mars", "avr.", "mai", "juin"]
    vals = [1520, 1480, 1610, 1390, 1270, 1180]
    src = asset("v-chart-prets-fr", bar_chart("Prêts mensuels, premier semestre 2026", months, vals, color="#8e5ea2"))
    alt = "Prêts mensuels 2026 : " + ", ".join(f"{m} {v}" for m, v in zip(months, vals))
    main = ("<h1>Statistiques</h1><p>Les prêts diminuent légèrement au printemps, comme chaque année.</p>"
            f"<p>{img(src, alt, 640, 360, id='graphique-prets')}</p>")
    return mk(rng, "fr", "bibliothek", "Statistiques", main, "passed", "#graphique-prets", "1.4.5/T2",
              "The chart contains axis labels and values, but text that is part of a graph with significant other visual content is not an image of text.",
              trap=True, difficulty="medium")


def t2_network_de(rng):
    lines = [("2", "#8e5ea2", ["Bahnhof", "Dorfplatz", "Schulhaus", "Seeweg"]),
             ("5", "#d4a017", ["Bahnhof", "Spital", "Oberdorf", "Weiler"]),
             ("8", "#1f6f8b", ["Dorfplatz", "Industrie", "Sportzentrum", "Waldrand", "Friedhof"])]
    src = asset("v-network-de-2", network_svg(lines))
    alt = "Liniennetz: " + "; ".join(f"Linie {n}: " + " – ".join(st) for n, _, st in lines)
    main = ("<h1>Liniennetz</h1><p>Drei Linien erschliessen das Gemeindegebiet. Umsteigen ist am Bahnhof und "
            "am Dorfplatz möglich.</p>"
            f"<p>{img(src, alt, 680, 320, id='liniennetz')}</p>")
    return mk(rng, "de", "verkehr", "Liniennetz", main, "passed", "#liniennetz", "1.4.5/T2",
              "Stop names are part of a network diagram whose lines and nodes are significant visual content.",
              trap=True, difficulty="medium")


def t3_market_it(rng):
    src = asset("v-scene-market-sign-it", market_sign(15, "MERCATO"))
    main = ("<h1>Il mercato del sabato</h1><p>Ogni sabato dalle 8.00 alle 12.00 una ventina di bancarelle "
            "propongono frutta, verdura, formaggi e pane della regione.</p>"
            f"<p>{img(src, 'Le bancarelle colorate del mercato sotto l’insegna del mercato', 480, 300, id='foto-mercato')}</p>")
    return mk(rng, "it", "gemeinde", "Mercato", main, "passed", "#foto-mercato", "1.4.5/T3",
              "The sign 'MERCATO' is incidental text inside a picture with significant other visual content.",
              trap=True, difficulty="medium")


def t4_bag_de(rng):
    src = asset("v-gebuehrensack-de", bag_svg([("Gebührensack", 22, 700), ("35 Liter", 20, 400), ("gültig ab 2027", 14, 400)]))
    main = ("<h1>Neue Gebührensäcke ab 2027</h1><p>Ab 1. Januar 2027 werden nur noch Säcke mit dem neuen "
            "roten Aufdruck abgeholt. So sieht der Aufdruck aus:</p>"
            f"<p>{img(src, 'Grauer Kehrichtsack mit rotem Aufdruck: Abfalleimer-Symbol, «Gebührensack», «35 Liter», «gültig ab 2027»', 360, 420, id='muster-sack')}</p>"
            "<p>Alte Säcke können bis 31. März 2027 am Schalter umgetauscht werden.</p>")
    return mk(rng, "de", "werke", "Gebührensäcke", main, "passed", "#muster-sack", "1.4.5/T4",
              "The image shows what the printed bag looks like so residents can recognise it; the particular presentation is essential.",
              trap=True, difficulty="hard")


def t4_permit_fr(rng):
    src = asset("v-macaron-residents-fr", permit_svg(["Macaron résidents", "A", "Zone bleue", "Valable 2027",
                                                     "N° 0000"], "#1f5fae"))
    main = ("<h1>Nouveau macaron de stationnement</h1><p>Le macaron 2027 change de couleur. Voici à quoi il "
            "ressemble ; il doit être placé bien visible derrière le pare-brise :</p>"
            f"<p>{img(src, 'Macaron bleu « Macaron résidents », grande lettre A dans un cercle, « Zone bleue », « Valable 2027 »', 420, 260, id='modele-macaron')}</p>"
            "<p>Les anciens macarons ne sont plus valables dès le 1er février 2027.</p>")
    return mk(rng, "fr", "gemeinde", "Macaron de stationnement", main, "passed", "#modele-macaron", "1.4.5/T4",
              "The permit picture is a specimen: its exact appearance is what residents must recognise, so the presentation is essential.",
              trap=True, difficulty="hard")


def t5_switch_en(rng):
    src = asset("v-tagline-en", title_svg("Fresh air, clear lakes, open trails", "#0b4f6c", 560, 64, 30, "#3c8d4f"))
    main = ("<p class=\"tagline-wrap\"><span class=\"tagline\" id=\"tagline\">Fresh air, clear lakes, open trails</span></p>"
            "<p><button type=\"button\" id=\"plain-text\" aria-pressed=\"false\">Show plain text instead of text images</button></p>"
            "<h1>Plan your visit</h1><p>The valley is easy to reach by train and bus. Hiking trails start right "
            "behind the station; maps are available at the visitor centre.</p>")
    css = (f".tagline{{display:inline-block;width:560px;max-width:100%;height:64px;background:url({src}) left center/contain "
           "no-repeat;text-indent:-9999px;overflow:hidden}body.plain .tagline{width:auto;height:auto;background:none;"
           "text-indent:0;font-size:1.6rem;font-style:italic}")
    js = ("<script>document.addEventListener('DOMContentLoaded',function(){var b=document.getElementById('plain-text');"
          "b.addEventListener('click',function(){var on=document.body.classList.toggle('plain');"
          "b.setAttribute('aria-pressed',on?'true':'false');});});</script>")
    return mk(rng, "en", "tourism", "Plan your visit", main, "passed", "#tagline", "1.4.5/T5",
              "The tagline is real text replaced by an image via CSS, and a visible button switches to the plain-text presentation (C30).",
              trap=True, css=css, head=js, difficulty="hard")


# ---------------------------------------------------------------------------
# CANTTELL
# ---------------------------------------------------------------------------

def c1_poster_de(rng):
    src = asset("v-poster-dorffest-de", poster_svg("concert", 16, [("Dorffest", 56, 700),
                                                                  ("28. und 29. August 2027", 26, 400),
                                                                  ("Festzelt beim Schulhaus", 22, 400)], "#3d405b"))
    main = ("<h1>Das Plakat zum Dorffest ist da</h1><p>Das Plakat hängt ab sofort in den Läden und Restaurants "
            "des Dorfes. Gedruckte Exemplare erhalten Sie gratis auf der Gemeindekanzlei.</p>"
            f"<p>{img(src, 'Plakat: Illustration einer Festbühne zwischen Tannen; Text: Dorffest, 28. und 29. August 2027, Festzelt beim Schulhaus', 480, 640, id='plakat')}</p>")
    return mk(rng, "de", "gemeinde", "Plakat Dorffest", main, "cantTell", "#plakat", "1.4.5/C1",
              "The poster combines a large illustration with event text; whether this is an image of text or a picture with significant other visual content (shown as the poster design) has no defined threshold.",
              difficulty="hard")


def c1_invite_it(rng):
    src = asset("v-poster-concerto-it", poster_svg("concert", 17, [("Concerto d'estate", 44, 700),
                                                                  ("Coro misto di Esempiano", 24, 400),
                                                                  ("Sabato 3 luglio 2027, ore 20.30", 22, 400)], "#81475a"))
    main = ("<h1>Invito</h1><p>Il coro misto vi invita al tradizionale concerto d'estate. Entrata libera, "
            "colletta all'uscita.</p>"
            f"<p>{img(src, 'Invito illustrato con un palco tra gli alberi: Concerto d’estate, Coro misto di Esempiano, sabato 3 luglio 2027, ore 20.30', 480, 640, id='invito')}</p>")
    return mk(rng, "it", "gemeinde", "Concerto d'estate", main, "cantTell", "#invito", "1.4.5/C1",
              "Illustrated invitation card whose text is a major part of the image; whether the artwork makes it a picture rather than an image of text is a judgement call.",
              difficulty="hard")


def c2_arrete_fr(rng):
    paras = [["La Municipalité de Valfictif,", "vu la loi sur la circulation routière,", "vu le règlement communal de police,"],
             ["arrête :", "Article premier. – La rue de l'Église est interdite à", "tout véhicule du 2 au 20 novembre 2026,",
              "riverains et services d'urgence exceptés."],
             ["Art. 2. – Le présent arrêté entre en vigueur dès sa", "publication."]]
    src = asset("v-arrete-municipal-fr", facsimile_svg("COMMUNE DE VALFICTIF – MUNICIPALITÉ", "Arrêté municipal du 5 octobre 2026",
                                                     paras, "Le syndic : Marc Modèle", "SCEAU"))
    alt = ("Arrêté municipal du 5 octobre 2026, signé et muni du sceau : la rue de l'Église est interdite à tout "
           "véhicule du 2 au 20 novembre 2026, riverains et services d'urgence exceptés ; entrée en vigueur dès publication.")
    main = ("<h1>Arrêté municipal : fermeture de la rue de l'Église</h1><p>Vous trouverez ci-dessous l'arrêté "
            "signé, tel qu'il a été affiché au pilier public.</p>"
            f"<p>{img(src, alt, 460, 620, id='arrete-signe')}</p>")
    return mk(rng, "fr", "gemeinde", "Arrêté municipal", main, "cantTell", "#arrete-signe", "1.4.5/C2",
              "The signed and sealed decision is published only as a facsimile image; essential if the signed original's appearance matters, a failure if it just substitutes for the operative text.",
              org="Commune de Valfictif", difficulty="hard")


def c2_enquete_fr(rng):
    paras = [["Conformément à la loi sur l'aménagement du territoire,", "la Municipalité soumet à l'enquête publique",
              "du 9 octobre au 7 novembre 2026 :"],
             ["Construction d'un hangar agricole,", "parcelle n° 412, chemin des Vignes 7.",
              "Propriétaire : Luc Témoin."],
             ["Le dossier peut être consulté au greffe pendant les", "heures d'ouverture. Les oppositions motivées sont",
              "à adresser par écrit à la Municipalité."]]
    src = asset("v-avis-enquete-fr", facsimile_svg("COMMUNE D'EXEMPLEVAL", "Avis d'enquête publique", paras,
                                                      "Le greffe municipal", "GREFFE"))
    alt = ("Avis d'enquête publique, du 9 octobre au 7 novembre 2026 : construction d'un hangar agricole, parcelle "
           "n° 412, chemin des Vignes 7, propriétaire Luc Témoin. Dossier consultable au greffe ; oppositions par "
           "écrit à la Municipalité. Timbre du greffe.")
    main = ("<h1>Enquêtes publiques</h1><p>Avis officiel publié au pilier public et reproduit ci-dessous.</p>"
            f"<p>{img(src, alt, 460, 620, id='avis-enquete')}</p>")
    return mk(rng, "fr", "gemeinde", "Enquêtes publiques", main, "cantTell", "#avis-enquete", "1.4.5/C2",
              "An official stamped notice reproduced as an image; whether the facsimile presentation is essential (authentic notice) or replaceable by text depends on intent.",
              org="Commune d'Exempleval", difficulty="hard")


BUILDERS = [
    f1_banner_de, f1_banner_fr, f1_banner_it, f2_button_de, f2_cta_it, f3_heading_fr, f3_heading_de, f3_replace_it,
    f4_prices_de, f4_hours_fr,
    p1_banner_de, p1_cta_fr, p1_heading_it, p2_photo_it, t1_logo_de, t1_logo_it, t2_chart_fr, t2_network_de,
    t3_market_it, t4_bag_de, t4_permit_fr, t5_switch_en,
    c1_poster_de, c1_invite_it, c2_arrete_fr, c2_enquete_fr,
]


def build(rng):
    return [b(rng) for b in BUILDERS]
