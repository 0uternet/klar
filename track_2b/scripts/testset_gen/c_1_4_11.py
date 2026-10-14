"""1.4.11 Non-text Contrast — 26 cases (protocol rules 1.4.11/F1–F5, P1, T1–T5, C1–C2)."""
import math
import random

from common import *
from _visual_util import compose, doc, img, org_of, host_of, phone, ratio

CRITERION = "1.4.11"


def chk(fg, bg, lo=None, hi=None):
    r = contrast(fg, bg)
    if lo is not None:
        assert r >= lo, (fg, bg, r)
    if hi is not None:
        assert r < hi, (fg, bg, r)
    return ratio(fg, bg)


def min_vs_themes(col):
    return min(contrast(col, t["bg"]) for t in THEMES)


def mk(rng, lang, kind, title, main, expected, target, rule, notes, *, trap=False, alt_expected=None,
       difficulty="medium", css="", theme=None, org=None, head="", **kw):
    org = org or org_of(rng, lang, kind)
    main = main.replace("{ORG}", esc(org)).replace("{HOST}", host_of(org)).replace("{PHONE}", phone(rng))
    body, lcss = compose(rng, lang, org, main, kind=kind, **kw)
    html = doc(rng, lang, title, org, body, lcss + css, theme=theme, head=head)
    return Case(CRITERION, lang, expected, html=html, target=target, rule=rule, notes=notes, trap=trap,
                alt_expected=alt_expected, difficulty=difficulty)


def _svg(w, h, inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'{inner}</svg>')


def _t(x, y, s, size=13, fill="#1d2327", anchor="start", weight=400):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Arial, sans-serif" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}">{esc(s)}</text>')


def icon_inline(name, stroke, size=24, grad=None):
    """Inline icon for a button (decorative inside a named button)."""
    defs = ""
    if grad:
        gid, stops = grad
        defs = (f'<defs><linearGradient id="{gid}" x1="0" x2="0" y1="0" y2="1">'
                + "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
                + '</linearGradient></defs>')
        stroke = f"url(#{gid})"
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{defs}'
            f'<g fill="none" stroke="{stroke}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">'
            f'{ICONS[name]}</g></svg>')


ICON_BTN_CSS = ".icon-btn{background:transparent;border:0;padding:6px;line-height:0;border-radius:6px}"


def pie_paths(cx, cy, r, vals, colors, stroke="#ffffff", hole=0):
    total = sum(vals)
    a0 = -math.pi / 2
    out, mids = [], []
    for v, c in zip(vals, colors):
        a1 = a0 + 2 * math.pi * v / total
        large = 1 if a1 - a0 > math.pi else 0
        x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
        x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
        out.append(f'<path d="M{cx},{cy} L{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f} Z" fill="{c}" '
                   f'stroke="{stroke}" stroke-width="2"/>')
        mids.append((a0 + a1) / 2)
        a0 = a1
    if hole:
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{hole}" fill="#ffffff"/>')
    return "".join(out), mids


PASTEL = ["#b3cde3", "#ccebc5", "#decbe4", "#fed9a6", "#e5d8bd"]


def donut_names_only(title, labels, vals):
    paths, _ = pie_paths(150, 180, 110, vals, PASTEL, hole=55)
    leg = "".join(f'<rect x="300" y="{90 + i * 30}" width="16" height="16" fill="{PASTEL[i]}"/>'
                  + _t(324, 103 + i * 30, l, 14) for i, l in enumerate(labels))
    return _svg(560, 330, '<rect width="560" height="330" fill="#ffffff"/>' + _t(20, 32, title, 18, weight=700)
                + paths + leg)


def pie_labelled(title, labels, vals):
    cx, cy, r = 290, 200, 110
    paths, mids = pie_paths(cx, cy, r, vals, PASTEL)
    total = sum(vals)
    lab = []
    for l, v, a in zip(labels, vals, mids):
        x1, y1 = cx + (r + 4) * math.cos(a), cy + (r + 4) * math.sin(a)
        x2, y2 = cx + (r + 22) * math.cos(a), cy + (r + 22) * math.sin(a)
        anchor = "start" if math.cos(a) >= 0 else "end"
        tx = x2 + (6 if anchor == "start" else -6)
        lab.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#55606a"/>'
                   + _t(f"{tx:.1f}", f"{y2 + 5:.1f}", f"{l} {100 * v / total:.0f} %", 14, anchor=anchor))
    return _svg(600, 380, '<rect width="600" height="380" fill="#ffffff"/>' + _t(20, 32, title, 18, weight=700)
                + paths + "".join(lab))


def heatmap(title, low, high, unit, seed):
    pal = ["#ffffb2", "#fed976", "#feb24c", "#fd8d3c", "#f03b20", "#bd0026"]
    r = random.Random(seed)
    p = ['<rect width="620" height="380" fill="#ffffff"/>', _t(20, 30, title, 17, weight=700),
         '<rect x="20" y="50" width="420" height="300" fill="#e9ecef"/>']
    for row in range(6):
        for col in range(8):
            if r.random() < 0.18:
                continue
            k = min(5, max(0, int(r.gauss(2.8 - 0.25 * abs(col - 4), 1.3))))
            p.append(f'<rect x="{28 + col * 51}" y="{58 + row * 48}" width="44" height="40" rx="3" fill="{pal[k]}"/>')
    p.append('<defs><linearGradient id="hs" x1="0" x2="0" y1="1" y2="0">'
             + "".join(f'<stop offset="{i / 5:.2f}" stop-color="{c}"/>' for i, c in enumerate(pal))
             + '</linearGradient></defs><rect x="480" y="70" width="28" height="240" fill="url(#hs)"/>')
    p.append(_t(516, 80, high, 13) + _t(516, 314, low, 13) + _t(480, 340, unit, 12))
    return _svg(620, 380, "".join(p))


def route_map(streets, route, route_col, *, dashed=False, forest=False):
    p = ['<rect width="640" height="380" fill="#f4f1ea"/>']
    if forest:
        p += ['<path d="M380 30 h230 v170 h-120 z" fill="#d8e6cf"/>', '<path d="M30 260 h180 v100 h-180 z" fill="#d8e6cf"/>']
    p += ['<path d="M30 190 H610 M200 30 V350 M450 30 V350 M200 90 H450 M450 290 H610" stroke="#c7ccd2" stroke-width="14" fill="none"/>']
    da = ' stroke-dasharray="12 7"' if dashed else ""
    p.append(f'<path d="{route}" fill="none" stroke="{route_col}" stroke-width="6" stroke-linejoin="round"{da}/>')
    for (x, y, s) in streets:
        p.append(_t(x, y, s, 14))
    return _svg(640, 380, "".join(p))


# ---------------------------------------------------------------------------
# FAILED
# ---------------------------------------------------------------------------

def f1_input_de(rng):
    col = "#d6d6d6"
    r1 = chk(col, "#ffffff", hi=3)
    assert max(contrast(col, t["bg"]) for t in THEMES) < 3
    main = ("<h1>Newsletter</h1><p>Einmal im Monat informieren wir über Baustellen, Veranstaltungen und "
            "Neuerungen in der Verwaltung. Die Abmeldung ist jederzeit möglich.</p>"
            "<form action=\"newsletter-danke.html\" method=\"post\"><label for=\"newsletter-mail\">E-Mail-Adresse</label>"
            "<input type=\"email\" id=\"newsletter-mail\" name=\"mail\" class=\"feld-hell\">"
            "<p><button type=\"submit\">Abonnieren</button></p></form>")
    css = f".feld-hell{{border:1px solid {col};background:#ffffff;width:280px;max-width:100%}}"
    return mk(rng, "de", "gemeinde", "Newsletter", main, "failed", "#newsletter-mail", "1.4.11/F1",
              f"The e-mail field is identified only by a {col} border ({r1}:1 against the white field and similar against the page), below 3:1.",
              css=css, difficulty="medium")


def f1_search_fr(rng):
    t = pick_theme(rng)
    col = "#cfd8dc"
    r = chk(col, t["bg"], hi=3)
    main = ("<h1>Rechercher</h1><form action=\"resultats.html\" role=\"search\"><label for=\"recherche\">Terme "
            "recherché</label><input type=\"search\" id=\"recherche\" name=\"q\" class=\"champ-recherche\">"
            " <button type=\"submit\">Rechercher</button></form><p>Astuce : utilisez des mots-clés courts, par "
            "exemple « déchets » ou « permis ».</p>")
    css = f".champ-recherche{{border:1px solid {col};background:#ffffff;width:300px;max-width:100%}}"
    return mk(rng, "fr", "gemeinde", "Recherche", main, "failed", "#recherche", "1.4.11/F1",
              f"The search field's border {col} has {r}:1 against the page background and the field fill is white, so its boundary is below 3:1.",
              css=css, theme=t, difficulty="medium")


def f2_close_it(rng):
    col = "#b0bec5"
    r = chk(col, "#ffffff", hi=3)
    main = ("<div class=\"avviso\" id=\"avviso\"><p>Da lunedì 2 novembre lo sportello della Cancelleria apre "
            "alle 9.00 anziché alle 8.30.</p><button type=\"button\" class=\"icon-btn chiudi\" aria-label=\"Chiudi avviso\">"
            + icon_inline("close", col) + "</button></div><h1>Cancelleria comunale</h1><p>La Cancelleria rilascia "
            "certificati, carte d'identità e attestati di domicilio.</p>")
    css = (ICON_BTN_CSS + ".avviso{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;"
           "background:#ffffff;border:1px solid #6b7280;border-radius:8px;padding:4px 12px}")
    js = ("<script>document.addEventListener('DOMContentLoaded',function(){document.querySelector('.chiudi')"
          ".addEventListener('click',function(){document.getElementById('avviso').hidden=true;});});</script>")
    return mk(rng, "it", "gemeinde", "Cancelleria", main, "failed", ".chiudi", "1.4.11/F2",
              f"The close button is identified only by its × glyph, drawn in {col} on white ({r}:1 < 3:1).",
              css=css, head=js, difficulty="easy")


def f2_print_de(rng):
    col = "#a3c4dc"
    r = chk(col, "#ffffff", hi=3)
    main = ("<h1>Merkblatt Bauen ausserhalb der Bauzone</h1><p class=\"werkzeuge\">"
            "<button type=\"button\" class=\"icon-btn\" id=\"drucken\" aria-label=\"Seite drucken\">"
            + icon_inline("printer", col, 28) + "</button></p><div class=\"card\"><p>Bauvorhaben ausserhalb der "
            "Bauzone benötigen eine Bewilligung des Kantons. Reichen Sie das Gesuch bei der Gemeinde ein; wir "
            "leiten es weiter.</p><p>Bearbeitungsdauer: rund acht Wochen.</p></div>")
    css = ICON_BTN_CSS + ".werkzeuge{text-align:right;margin:0}#drucken{background:#ffffff}"
    js = ("<script>document.addEventListener('DOMContentLoaded',function(){document.getElementById('drucken')"
          ".addEventListener('click',function(){window.print();});});</script>")
    return mk(rng, "de", "gemeinde", "Merkblatt Bauen", main, "failed", "#drucken", "1.4.11/F2",
              f"The icon-only print button's glyph is pale blue {col} on white ({r}:1).", css=css, head=js,
              difficulty="easy")


def f3_checkbox_fr(rng):
    col = "#d0d7de"
    r = chk(col, "#ffffff", hi=3)
    main = ("<h1>Réservation de la salle communale</h1><form action=\"reservation-envoyee.html\" method=\"post\">"
            "<label for=\"date\">Date souhaitée</label><input type=\"text\" id=\"date\" name=\"date\">"
            "<label for=\"personnes\">Nombre de personnes</label><input type=\"text\" id=\"personnes\" name=\"personnes\">"
            "<p class=\"case\"><input type=\"checkbox\" id=\"conditions\" name=\"conditions\"> <label for=\"conditions\">"
            "J'accepte le règlement d'utilisation de la salle</label></p><p><button type=\"submit\">Envoyer</button></p></form>")
    css = (f".case label{{display:inline;font-weight:400}}#conditions{{appearance:none;-webkit-appearance:none;width:20px;"
           f"height:20px;border:1px solid {col};border-radius:4px;background:#ffffff;padding:0;margin:0 6px 0 0;"
           "vertical-align:middle}#conditions:checked{background:#0b4f6c;border-color:#0b4f6c}")
    return mk(rng, "fr", "gemeinde", "Réservation de salle", main, "failed", "#conditions", "1.4.11/F3",
              f"The custom checkbox's unchecked outline {col} has {r}:1 against white, so the control is barely perceivable.",
              css=css, difficulty="medium")


def f3_radio_it(rng):
    col = "#c8d1d9"
    r = chk(col, "#ffffff", hi=3)
    opts = [("t1", "Adulti – CHF 8.–"), ("t2", "Ragazzi 6–16 anni – CHF 4.–"), ("t3", "Famiglia – CHF 20.–")]
    radios = "".join(f'<p><input type="radio" name="tariffa" id="{i}" value="{i}"> <label for="{i}">{esc(l)}</label></p>'
                     for i, l in opts)
    main = ("<h1>Biglietti online – Piscina</h1><form action=\"pagamento.html\" method=\"post\">"
            f"<fieldset id=\"tariffe\"><legend>Tariffa</legend>{radios}</fieldset>"
            "<label for=\"quanti\">Quantità</label><input type=\"text\" id=\"quanti\" name=\"quanti\" value=\"1\">"
            "<p><button type=\"submit\">Procedi al pagamento</button></p></form>")
    css = (f"#tariffe label{{display:inline;font-weight:400}}#tariffe input{{appearance:none;-webkit-appearance:none;"
           f"width:18px;height:18px;border:1px solid {col};border-radius:50%;background:#ffffff;padding:0;margin:0 6px 0 0;"
           "vertical-align:middle}#tariffe input:checked{border:6px solid #0b4f6c}")
    return mk(rng, "it", "sport", "Biglietti piscina", main, "failed", "#tariffe", "1.4.11/F3",
              f"The custom radio buttons are drawn with a {col} ring ({r}:1 against white), so the unselected options are not perceivable as controls.",
              css=css, difficulty="medium")


def f4_lines_de(rng):
    cols = ["#a6cee3", "#fdbf6f"]
    for c in cols:
        chk(c, "#ffffff", hi=3)
    months = MONTHS_SHORT["de"]
    series = {"Pegel Nord": [142, 138, 151, 166, 181, 188, 176, 160, 149, 145, 140, 139],
              "Pegel Süd": [128, 125, 133, 149, 170, 179, 171, 150, 137, 131, 129, 127]}
    src = asset("v-chart-pegel-de", line_chart("Wasserstand Mustersee 2025 (cm)", months, series, colors=cols))
    main = ("<h1>Wasserstände 2025</h1><p>Die Grafik zeigt den Verlauf der beiden Messstellen im Jahr 2025. "
            "Im Juni wurde an beiden Pegeln der höchste Stand seit zehn Jahren gemessen.</p>"
            f"<p>{img(src, 'Liniendiagramm der Wasserstände an den Pegeln Nord und Süd 2025', 640, 360, id='grafik-pegel')}</p>")
    return mk(rng, "de", "werke", "Wasserstände", main, "failed", "#grafik-pegel", "1.4.11/F4",
              f"The two data lines ({ratio(cols[0], '#ffffff')}:1 and {ratio(cols[1], '#ffffff')}:1 against white) carry the values, which are not given as labels or text.",
              difficulty="medium")


def f4_donut_fr(rng):
    labels = ["Région", "Reste de la Suisse", "Europe", "Autres pays"]
    vals = [46, 31, 17, 6]
    src = asset("v-chart-donut-fr", donut_names_only("Provenance des visiteurs 2025", labels, vals))
    main = ("<h1>Le musée en 2025</h1><p>Le musée a accueilli 18 400 visiteuses et visiteurs. Leur provenance "
            "est représentée ci-dessous.</p>"
            f"<p>{img(src, 'Graphique en anneau de la provenance des visiteurs 2025', 560, 330, id='graphique-provenance')}</p>")
    return mk(rng, "fr", "museum", "Le musée en 2025", main, "failed", "#graphique-provenance", "1.4.11/F4",
              f"The shares are readable only from pastel ring segments (1.04–1.65:1 against white and each other); the legend gives names but no values.",
              difficulty="hard")


def f5_focus_it(rng):
    col = "#ffd8a8"
    assert max(contrast(col, t["bg"]) for t in THEMES) < 3
    main = ("<h1>Visite guidate</h1><p>Ogni domenica alle 15.00 una guida vi accompagna attraverso le sale della "
            "filanda. Durata: un'ora. Gruppi su richiesta anche in settimana.</p>"
            "<p><a class=\"prenota\" href=\"prenotazione-visita.html\">Prenota una visita guidata</a></p>")
    css = (".prenota{display:inline-block;background:#0b4f6c;color:#ffffff;padding:10px 18px;border-radius:6px;"
           f"text-decoration:none}}.prenota:focus{{outline:2px solid {col};outline-offset:3px}}")
    return mk(rng, "it", "museum", "Visite guidate", main, "failed", ".prenota", "1.4.11/F5",
              f"The custom focus outline ({col}) is drawn outside the button against the page background at about {ratio(col, '#ffffff')}:1, below 3:1.",
              css=css, difficulty="hard")


def f5_focus_de(rng):
    col = "#cfe8ff"
    r = chk(col, "#ffffff", hi=3)
    main = ("<h1>Abfallkalender</h1><form action=\"abfallkalender-suche.html\" role=\"search\">"
            "<label for=\"strasse\">Ihre Strasse</label><input type=\"text\" id=\"strasse\" name=\"strasse\">"
            " <button type=\"submit\">Abfuhrdaten anzeigen</button></form><p>Der Kalender zeigt alle Abfuhrdaten "
            "für Kehricht, Papier, Karton und Grüngut.</p>")
    css = f"#strasse{{background:#ffffff}}#strasse:focus{{outline:none;border-color:{col}}}"
    return mk(rng, "de", "werke", "Abfallkalender", main, "failed", "#strasse", "1.4.11/F5",
              f"On focus the outline is removed and the border turns {col} ({r}:1), so the focused field loses its boundary and has no visible focus indicator.",
              css=css, difficulty="hard")


# ---------------------------------------------------------------------------
# PASSED
# ---------------------------------------------------------------------------

def p1_input_it(rng):
    col = "#767676"
    r = chk(col, "#ffffff", lo=3)
    assert min_vs_themes(col) >= 3
    main = ("<h1>Verifica dello stato della domanda</h1><p>Inserite il numero della pratica che trovate sulla "
            "conferma di ricezione.</p><form action=\"stato-pratica.html\" method=\"get\"><label for=\"pratica\">"
            "Numero della pratica</label><input type=\"text\" id=\"pratica\" name=\"pratica\" class=\"campo\">"
            "<p><button type=\"submit\">Verifica</button></p></form>")
    css = f".campo{{border:1px solid {col};background:#ffffff}}"
    return mk(rng, "it", "gemeinde", "Stato della domanda", main, "passed", "#pratica", "1.4.11/P1",
              f"The input border {col} gives {r}:1 against the white field (≥ 3:1 against every page background).",
              css=css, difficulty="easy")


def p1_icon_fr(rng):
    col = "#4f5b62"
    r = chk(col, "#ffffff", lo=3)
    main = ("<h1>Marché de Noël</h1><p class=\"outils\"><button type=\"button\" class=\"icon-btn\" id=\"partager\" "
            "aria-label=\"Partager la page\">" + icon_inline("share", col, 26) + "</button></p><p>Du 4 au 6 décembre, "
            "une quarantaine de stands sur la place du Village. Vin chaud offert par la société de développement le "
            "samedi soir.</p>")
    css = ICON_BTN_CSS + ".outils{text-align:right;margin:0}#partager{background:#ffffff}"
    return mk(rng, "fr", "gemeinde", "Marché de Noël", main, "passed", "#partager", "1.4.11/P1",
              f"The share icon is dark grey {col} on white ({r}:1 ≥ 3:1).", css=css, difficulty="easy")


def p1_checkbox_de(rng):
    col = "#6b7280"
    r = chk(col, "#ffffff", lo=3)
    main = ("<h1>Abo Ortsbus</h1><form action=\"abo-bestellt.html\" method=\"post\"><label for=\"name\">Name</label>"
            "<input type=\"text\" id=\"name\" name=\"name\"><p class=\"auswahl\"><input type=\"checkbox\" "
            "id=\"rechnung\" name=\"rechnung\"> <label for=\"rechnung\">Rechnung per E-Mail statt per Post</label></p>"
            "<p><button type=\"submit\">Bestellen</button></p></form>")
    css = (f".auswahl label{{display:inline;font-weight:400}}#rechnung{{appearance:none;-webkit-appearance:none;width:20px;"
           f"height:20px;border:2px solid {col};border-radius:4px;background:#ffffff;padding:0;margin:0 6px 0 0;"
           "vertical-align:middle}#rechnung:checked{background:#0b4f6c;border-color:#0b4f6c}")
    return mk(rng, "de", "verkehr", "Abo Ortsbus", main, "passed", "#rechnung", "1.4.11/P1",
              f"The custom checkbox outline {col} has {r}:1 against white.", css=css, difficulty="easy")


def p1_focus_fr(rng):
    col = "#0b4f6c"
    r = chk(col, "#ffffff", lo=3)
    main = ("<h1>Inscriptions scolaires</h1><p>Les enfants nés entre le 1er août 2022 et le 31 juillet 2023 "
            "entrent à l'école en août 2027. Les parents reçoivent un courrier en janvier.</p>"
            "<p><a class=\"lien-action\" href=\"inscription-ecole.html\">Inscrire mon enfant</a></p>")
    css = (".lien-action{display:inline-block;border:2px solid #0b4f6c;color:#0b4f6c;padding:8px 16px;border-radius:6px;"
           f"text-decoration:none;font-weight:600}}.lien-action:focus{{outline:3px solid {col};outline-offset:2px}}")
    return mk(rng, "fr", "schule", "Inscriptions scolaires", main, "passed", ".lien-action", "1.4.11/P1",
              f"The custom focus outline {col} is drawn on the page background with {r}:1.", css=css, difficulty="medium")


def t1_disabled_input_de(rng):
    main = ("<h1>Parkkarte beantragen</h1><form action=\"parkkarte-danke.html\" method=\"post\">"
            "<label for=\"kennzeichen\">Kontrollschild</label><input type=\"text\" id=\"kennzeichen\" name=\"kennzeichen\">"
            "<label for=\"gemeinde\">Wohngemeinde (aus Ihrem Konto übernommen)</label>"
            "<input type=\"text\" id=\"gemeinde\" name=\"gemeinde\" value=\"Beispielwil\" disabled>"
            "<p><button type=\"submit\">Antrag senden</button></p></form>")
    css = "#gemeinde{border:1px solid #e0e0e0;background:#f7f7f7;color:#595959}"
    return mk(rng, "de", "gemeinde", "Parkkarte", main, "passed", "#gemeinde", "1.4.11/T1",
              f"The faint border ({ratio('#e0e0e0', '#ffffff')}:1) belongs to a disabled field; inactive components are exempt.",
              trap=True, css=css, difficulty="medium")


def t1_disabled_check_it(rng):
    main = ("<h1>Abbonamento alla rivista comunale</h1><form action=\"abbonamento-ok.html\" method=\"post\">"
            "<p class=\"scelte\"><input type=\"checkbox\" id=\"digitale\" name=\"digitale\" checked> <label for=\"digitale\">"
            "Edizione digitale (e-mail)</label></p><p class=\"scelte\"><input type=\"checkbox\" id=\"cartacea\" "
            "name=\"cartacea\" disabled> <label for=\"cartacea\">Edizione cartacea (non disponibile nel 2027)</label></p>"
            "<p><button type=\"submit\">Conferma</button></p></form>")
    css = (".scelte label{display:inline;font-weight:400}.scelte input{appearance:none;-webkit-appearance:none;width:20px;"
           "height:20px;border:2px solid #6b7280;border-radius:4px;background:#ffffff;padding:0;margin:0 6px 0 0;"
           "vertical-align:middle}.scelte input:checked{background:#0b4f6c;border-color:#0b4f6c}"
           ".scelte input:disabled{border-color:#e0e0e0;background:#fafafa}")
    return mk(rng, "it", "gemeinde", "Rivista comunale", main, "passed", "#cartacea", "1.4.11/T1",
              "The pale outline belongs to a disabled checkbox; the enabled checkbox next to it uses #6b7280 (4.83:1).",
              trap=True, css=css, difficulty="medium")


def t2_pie_de(rng):
    labels = ["Wald", "Landwirtschaft", "Siedlung", "Gewässer", "Unproduktiv"]
    vals = [41, 33, 14, 7, 5]
    src = asset("v-chart-landuse-de", pie_labelled("Bodennutzung Gemeindegebiet", labels, vals))
    alt = "Bodennutzung: " + ", ".join(f"{l} {v} %" for l, v in zip(labels, vals))
    main = ("<h1>Zahlen und Fakten</h1><p>Das Gemeindegebiet umfasst 1 240 Hektaren zwischen See und "
            "Jurasüdfuss.</p>"
            f"<p>{img(src, alt, 600, 380, id='grafik-bodennutzung')}</p>")
    return mk(rng, "de", "gemeinde", "Zahlen und Fakten", main, "passed", "#grafik-bodennutzung", "1.4.11/T2",
              "Pastel slices have under 3:1 against each other, but every slice is labelled with its name and percentage, so the shapes are not required to understand the data.",
              trap=True, difficulty="hard")


def t2_bars_fr(rng):
    col = "#c6dbef"
    chk(col, "#ffffff", hi=3)
    months = ["janv.", "févr.", "mars", "avr.", "mai", "juin"]
    vals = [1520, 1480, 1610, 1390, 1270, 1180]
    src = asset("v-chart-bars-pale-fr", bar_chart("Prêts mensuels, 1er semestre 2026", months, vals, color=col))
    alt = "Prêts mensuels 2026 : " + ", ".join(f"{m} {v}" for m, v in zip(months, vals))
    main = ("<h1>Statistiques de prêt</h1><p>Les prêts reculent légèrement au printemps, comme chaque année.</p>"
            f"<p>{img(src, alt, 640, 360, id='graphique-prets')}</p>")
    return mk(rng, "fr", "bibliothek", "Statistiques", main, "passed", "#graphique-prets", "1.4.11/T2",
              f"The bars are very pale ({ratio(col, '#ffffff')}:1) but each bar carries its value as text, which conveys the same information.",
              trap=True, difficulty="hard")


def t3_ghost_it(rng):
    main = ("<h1>Domanda di contributo</h1><p>Passo 2 di 3: dati bancari.</p><form action=\"domanda-passo3.html\" "
            "method=\"post\"><label for=\"iban\">IBAN</label><input type=\"text\" id=\"iban\" name=\"iban\">"
            "<label for=\"titolare\">Titolare del conto</label><input type=\"text\" id=\"titolare\" name=\"titolare\">"
            "<p class=\"azioni\"><button type=\"submit\" formaction=\"domanda-passo1.html\" class=\"secondario\">Indietro</button> "
            "<button type=\"submit\">Avanti</button></p></form>")
    css = ".secondario{background:#ffffff;border:1px solid #d0d7de;color:#1d2327}"
    return mk(rng, "it", "gemeinde", "Domanda di contributo", main, "passed", ".secondario", "1.4.11/T3",
              f"The secondary button's border is faint ({ratio('#d0d7de', '#ffffff')}:1), but its visible text 'Indietro' identifies the control, so no boundary is required.",
              trap=True, css=css, difficulty="hard")


def t3_chips_fr(rng):
    cats = ["Culture", "Sport", "Famille", "Nature"]
    chips = "".join(f'<a class="puce" href="agenda-{slug(c)}.html">{c}</a>' for c in cats)
    main = ("<h1>Agenda</h1><nav class=\"filtres\" aria-label=\"Filtrer par catégorie\">" + chips + "</nav>"
            "<ul><li>Samedi 7 novembre, 20 h – Concert du chœur mixte</li><li>Dimanche 15 novembre, 10 h – Course "
            "des châtaignes</li><li>Mercredi 18 novembre, 14 h 30 – Après-midi jeux à la bibliothèque</li></ul>")
    css = (".filtres{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 16px}.puce{background:#eef2f5;color:#1d2327;"
           "padding:6px 14px;border-radius:16px;text-decoration:none}")
    return mk(rng, "fr", "gemeinde", "Agenda", main, "passed", ".puce:nth-child(2)", "1.4.11/T3",
              f"The filter chips' fill is almost invisible ({ratio('#eef2f5', '#ffffff')}:1) but each chip's text identifies it; a visible boundary is not required.",
              trap=True, css=css, difficulty="medium")


def t4_wave_de(rng):
    wave = ("<svg class=\"welle\" width=\"600\" height=\"24\" viewBox=\"0 0 600 24\" aria-hidden=\"true\" focusable=\"false\">"
            "<path d=\"M0 12 " + " ".join(f"Q{x + 15} {2 if (x // 30) % 2 == 0 else 22} {x + 30} 12" for x in range(0, 600, 30))
            + "\" fill=\"none\" stroke=\"#e3eef6\" stroke-width=\"3\"/></svg>")
    main = ("<h1>Badi Seeweg</h1><p>Das Strandbad ist von Mitte Mai bis Mitte September täglich von 9 bis 20 Uhr "
            f"geöffnet.</p>{wave}<h2>Eintritt</h2><p>Erwachsene CHF 6.–, Kinder CHF 3.–, Saisonkarte CHF 60.–.</p>")
    return mk(rng, "de", "sport", "Badi Seeweg", main, "passed", "svg.welle", "1.4.11/T4",
              f"The pale wave divider ({ratio('#e3eef6', '#ffffff')}:1) is purely decorative and hidden from assistive technology.",
              trap=True, difficulty="easy")


def t5_heatmap_it(rng):
    src = asset("v-heatmap-solare-it", heatmap("Potenziale solare dei tetti – quartiere Centro", "basso", "alto",
                                               "kWh/m² anno: 800–1 300", "heat-it"))
    main = ("<h1>Catasto solare</h1><p>La mappa indica quanta energia solare riceve ogni tetto del quartiere "
            "Centro in un anno, da circa 800 kWh/m² (giallo chiaro) a 1 300 kWh/m² (rosso scuro). Per una valutazione "
            "del vostro tetto contattate l'azienda elettrica.</p>"
            f"<p>{img(src, 'Mappa di calore del potenziale solare dei tetti del quartiere Centro, scala da basso (giallo chiaro) ad alto (rosso scuro)', 620, 380, id='mappa-solare')}</p>")
    return mk(rng, "it", "werke", "Catasto solare", main, "passed", "#mappa-solare", "1.4.11/T5",
              "Neighbouring heat-map colours differ by less than 3:1, but a continuous colour scale representing a measurement is an essential presentation.",
              trap=True, difficulty="hard")


# ---------------------------------------------------------------------------
# CANTTELL
# ---------------------------------------------------------------------------

def c1_detour_fr(rng):
    col = "#9ecae1"
    r = chk(col, "#f4f1ea", hi=3)
    streets = [(40, 182, "Rue de l'Église"), (210, 60, "Rue des Granges"), (460, 60, "Chemin des Vignes"),
               (470, 282, "Avenue de la Gare")]
    src = asset("v-map-deviation-fr", route_map(streets, "M30 190 H200 V90 H450 V290 H610", col))
    main = ("<h1>Fermeture de la rue de l'Église</h1><p>Du 2 au 20 novembre, la rue de l'Église est fermée entre "
            "la place et le collège. La déviation emprunte la rue des Granges puis rejoint l'avenue de la Gare.</p>"
            f"<p>{img(src, 'Plan de la déviation par la rue du Marché et l’avenue de la Gare', 640, 380, id='plan-deviation')}</p>")
    return mk(rng, "fr", "gemeinde", "Déviation", main, "cantTell", "#plan-deviation", "1.4.11/C1",
              f"The detour line is {r}:1 against the map; the text names two streets but not the turns via the Chemin des Vignes, so whether the line is required to understand the content is debatable.",
              difficulty="hard")


def c1_trail_de(rng):
    col = "#b9d7ea"
    r = chk(col, "#f4f1ea", hi=3)
    streets = [(40, 182, "Sportzentrum"), (470, 24, "Waldrand"), (60, 250, "Langmatt"), (470, 282, "Weiher")]
    src = asset("v-map-loipe-de", route_map(streets, "M30 190 H200 V90 H450 V290 H610 V40", col, dashed=True, forest=True))
    main = ("<h1>Langlaufloipe Waldrand</h1><p>Start beim Sportzentrum, Ziel beim Waldrand. Länge 7,5 km, "
            "klassisch und Skating. Die Loipe wird bei genügend Schnee täglich gespurt.</p>"
            f"<p>{img(src, 'Karte der Langlaufloipe vom Sportzentrum zum Waldrand', 640, 380, id='karte-loipe')}</p>")
    return mk(rng, "de", "sport", "Langlaufloipe", main, "cantTell", "#karte-loipe", "1.4.11/C1",
              f"The dashed trail line has {r}:1 against the map; start, end and length are in the text but the course is not, so whether the line is required is a judgement call.",
              difficulty="hard")


def c2_gradient_it(rng):
    dark, light = "#1d2327", "#c9d3d8"
    rd, rl = chk(dark, "#ffffff", lo=3), chk(light, "#ffffff", hi=3)
    ic = icon_inline("download", None, 30, grad=("sfumatura-scarica", [("0", dark), ("0.55", dark), ("0.75", light), ("1", light)]))
    main = ("<h1>Regolamento sui rifiuti</h1><p>Il nuovo regolamento entra in vigore il 1° gennaio 2027.</p>"
            "<p class=\"documento\">Regolamento comunale sui rifiuti (PDF, 310 kB) "
            f"<button type=\"button\" class=\"icon-btn\" id=\"scarica\" aria-label=\"Scarica il PDF\">{ic}</button></p>")
    css = ICON_BTN_CSS + "#scarica{background:#ffffff;vertical-align:middle}"
    js = ("<script>document.addEventListener('DOMContentLoaded',function(){document.getElementById('scarica')"
          ".addEventListener('click',function(){window.location.href='regolamento-rifiuti.pdf';});});</script>")
    return mk(rng, "it", "gemeinde", "Regolamento rifiuti", main, "cantTell", "#scarica", "1.4.11/C2",
              f"The download icon fades from {rd}:1 at the top to {rl}:1 at the bottom, so the tray part falls below 3:1; whether the arrow alone keeps the icon recognisable is a perceptual judgement.",
              css=css, head=js, difficulty="hard")


def c2_gradient_fr(rng):
    dark, light = "#2b2f3a", "#d4d7de"
    rd, rl = chk(dark, "#ffffff", lo=3), chk(light, "#ffffff", hi=3)
    ic = icon_inline("pin", None, 30, grad=("degrade-plan", [("0", dark), ("0.45", dark), ("0.7", light), ("1", light)]))
    main = ("<h1>Nous trouver</h1><p>Le musée se trouve à cinq minutes à pied de la gare, au bord de la rivière.</p>"
            f"<p class=\"acces\">Plan d'accès <button type=\"button\" class=\"icon-btn\" id=\"plan\" "
            f"aria-label=\"Afficher le plan d'accès\">{ic}</button></p>")
    css = ICON_BTN_CSS + "#plan{background:#ffffff;vertical-align:middle}"
    js = ("<script>document.addEventListener('DOMContentLoaded',function(){document.getElementById('plan')"
          ".addEventListener('click',function(){window.location.href='plan-acces.html';});});</script>")
    return mk(rng, "fr", "museum", "Nous trouver", main, "cantTell", "#plan", "1.4.11/C2",
              f"The pin icon is dark at the top ({rd}:1) but its lower point fades to {rl}:1; whether the shape stays identifiable without that part has no objective threshold.",
              css=css, head=js, difficulty="hard")


BUILDERS = [
    f1_input_de, f1_search_fr, f2_close_it, f2_print_de, f3_checkbox_fr, f3_radio_it, f4_lines_de, f4_donut_fr,
    f5_focus_it, f5_focus_de,
    p1_input_it, p1_icon_fr, p1_checkbox_de, p1_focus_fr, t1_disabled_input_de, t1_disabled_check_it, t2_pie_de,
    t2_bars_fr, t3_ghost_it, t3_chips_fr, t4_wave_de, t5_heatmap_it,
    c1_detour_fr, c1_trail_de, c2_gradient_it, c2_gradient_fr,
]


def build(rng):
    return [b(rng) for b in BUILDERS]
