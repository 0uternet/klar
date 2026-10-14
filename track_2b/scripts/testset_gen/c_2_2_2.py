"""2.2.2 Pause, Stop, Hide — carousels, tickers, live boxes, blinking notices (inline JS/CSS)."""
from __future__ import annotations

import json

from common import *  # noqa: F401,F403
from common import Case, asset, esc, header, footer, page, pick, pick_theme, scene, shuffled, SITE_LANG_TAG
from _operable_util import site_by_kind

CRITERION = "2.2.2"

CSS = (
    ".carousel{border:1px solid #c9d3d8;border-radius:10px;overflow:hidden;margin:16px 0;background:#ffffff}"
    ".carousel .slide{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr)}"
    ".carousel .slide[hidden]{display:none}"
    ".carousel .slide img{display:block;width:100%;height:auto}"
    ".carousel .cap{padding:16px}.carousel .cap h2{margin-top:0}"
    ".carousel .ctrl{display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:8px 16px;border-top:1px solid #c9d3d8}"
    ".dots{display:flex;gap:6px;list-style:none;margin:0 0 0 8px;padding:0}"
    ".dots li{width:10px;height:10px;border-radius:50%;background:#8a96a0}.dots li.on{background:#1d2327}"
    ".ticker{display:flex;align-items:center;gap:8px;background:#16181d;color:#ffffff;margin:12px 0;border-radius:6px}"
    ".ticker .lbl{font-weight:700;padding:8px 12px;background:#2b2f3a;white-space:nowrap}"
    ".ticker .vp{overflow:hidden;white-space:nowrap;flex:1}"
    ".ticker .track{display:inline-block;padding-left:100%;animation:tick 36s linear infinite}"
    ".ticker button{margin-right:6px;background:#ffffff;color:#16181d;border-color:#ffffff;padding:4px 10px}"
    "@keyframes tick{from{transform:translateX(0)}to{transform:translateX(-100%)}}"
    ".live{border:1px solid #c9d3d8;border-radius:10px;padding:12px 16px;margin:16px 0}"
    ".live h2{margin-top:0;font-size:1.15rem}"
    ".side{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr);gap:24px}"
)


def _img(kind, seed):
    return asset(f"illu-{kind}-{seed}", scene(kind, seed=seed))


def _chrome(lang, org, main_html, rng, theme, title, *, css="", head="", chrome=True):
    body = (header(lang, org) + "\n<main>\n" + main_html + "\n</main>\n" + footer(lang, org)) if chrome \
        else "<main>\n" + main_html + "\n</main>"
    return page(SITE_LANG_TAG[lang], title, body, theme=theme, css=CSS + css, head=head)


def _sections(site, rng, k=2):
    pages = [p for p in site["pages"] if p["slug"] != "index"]
    out = []
    for pg in shuffled(rng, pages)[:k]:
        out.append(f'<section><h2>{esc(pg["h1"])}</h2><p>{esc(pg["p"][0])}</p>'
                   f'<p><a href="{pg["slug"]}.html">{esc(pg["nav"])}</a></p></section>')
    return out


# ---------------------------------------------------------------------------
# Component builders
# ---------------------------------------------------------------------------

def carousel(cid, label, slides, *, ms=6000, auto=True, prevnext=True, dots=False, toggle=None,
             hover_pause=False, start_btn=None, once=False, extra_ctrl="", lang="de"):
    """slides: [(heading, text, img_url)]. toggle: (pause_label, play_label)."""
    words = {"de": ("Vorheriges Bild", "Nächstes Bild"), "fr": ("Image précédente", "Image suivante"),
             "it": ("Immagine precedente", "Immagine successiva")}[lang]
    sl = []
    for i, (h, t, img) in enumerate(slides):
        hid = "" if i == 0 else " hidden"
        sl.append(f'<div class="slide" role="group" aria-roledescription="slide" aria-label="{i + 1} / {len(slides)}"{hid}>'
                  f'<img src="{img}" alt=""><div class="cap"><h2>{esc(h)}</h2><p>{esc(t)}</p></div></div>')
    ctrl = []
    if start_btn:
        ctrl.append(f'<button type="button" class="go">{esc(start_btn)}</button>')
    if prevnext:
        ctrl.append(f'<button type="button" class="prev" aria-label="{esc(words[0])}">‹</button>'
                    f'<button type="button" class="next" aria-label="{esc(words[1])}">›</button>')
    if toggle:
        ctrl.append(f'<button type="button" class="toggle">{esc(toggle[0])}</button>')
    if dots:
        ctrl.append('<ul class="dots" aria-hidden="true">' + "".join(
            ('<li class="on"></li>' if i == 0 else '<li></li>') for i in range(len(slides))) + "</ul>")
    if extra_ctrl:
        ctrl.append(extra_ctrl)
    html = (f'<section id="{cid}" class="carousel" aria-roledescription="carousel" aria-label="{esc(label)}">'
            + "".join(sl) + (f'<div class="ctrl">{"".join(ctrl)}</div>' if ctrl else "") + "</section>")
    js = [f"var root=document.getElementById('{cid}');var s=root.querySelectorAll('.slide');"
          "var d=root.querySelectorAll('.dots li');var i=0;var t=null;",
          "function show(n){s[i].hidden=true;if(d.length){d[i].className='';}i=(n+s.length)%s.length;"
          "s[i].hidden=false;if(d.length){d[i].className='on';}"
          + ("if(i===s.length-1){stop();}" if once else "") + "}",
          f"function start(){{if(!t){{t=setInterval(function(){{show(i+1);}},{ms});}}}}"
          "function stop(){if(t){clearInterval(t);t=null;}}"]
    if prevnext:
        js.append("root.querySelector('.prev').addEventListener('click',function(){show(i-1);});"
                  "root.querySelector('.next').addEventListener('click',function(){show(i+1);});")
    if toggle:
        js.append(f"var b=root.querySelector('.toggle');b.addEventListener('click',function(){{"
                  f"if(t){{stop();b.textContent={json.dumps(toggle[1], ensure_ascii=False)};}}"
                  f"else{{start();b.textContent={json.dumps(toggle[0], ensure_ascii=False)};}}}});")
    if hover_pause:
        js.append("root.addEventListener('mouseenter',stop);root.addEventListener('mouseleave',start);"
                  "root.addEventListener('focusin',stop);root.addEventListener('focusout',start);")
    if start_btn:
        js.append("root.querySelector('.go').addEventListener('click',function(){if(i===s.length-1){show(0);}start();});")
    if auto:
        js.append("start();")
    return html + "<script>(function(){" + "".join(js) + "})();</script>"


def ticker(tid, label, items, *, secs=36, pause=None, hide=None, reduced=False, js_scroll=False):
    """CSS (or JS-scrolled) news ticker. pause: (pause_label, play_label); hide: label."""
    txt = "  +++  ".join(items)
    btns = ""
    if pause:
        btns += f'<button type="button" class="tgl">{esc(pause[0])}</button>'
    if hide:
        btns += f'<button type="button" class="hide">{esc(hide)}</button>'
    if js_scroll:
        html = (f'<div id="{tid}" class="ticker"><span class="lbl">{esc(label)}</span>'
                f'<div class="vp"><span class="txt" style="display:inline-block;padding:8px 100%">+++ {esc(txt)} +++</span></div>{btns}</div>')
        js = (f"(function(){{var vp=document.querySelector('#{tid} .vp');"
              "setInterval(function(){vp.scrollLeft+=2;if(vp.scrollLeft>=vp.scrollWidth-vp.clientWidth){vp.scrollLeft=0;}},40);})();")
        return html + f"<script>{js}</script>"
    html = (f'<div id="{tid}" class="ticker"><span class="lbl">{esc(label)}</span>'
            f'<div class="vp"><span class="track" style="animation-duration:{secs}s">+++ {esc(txt)} +++</span></div>{btns}</div>')
    js = ""
    if pause:
        js += (f"var tr=document.querySelector('#{tid} .track');var b=document.querySelector('#{tid} .tgl');"
               "b.addEventListener('click',function(){var p=tr.style.animationPlayState==='paused';"
               "tr.style.animationPlayState=p?'running':'paused';"
               f"b.textContent=p?{json.dumps(pause[0], ensure_ascii=False)}:{json.dumps(pause[1], ensure_ascii=False)};}});")
    if hide:
        js += (f"document.querySelector('#{tid} .hide').addEventListener('click',function(){{"
               f"document.getElementById('{tid}').hidden=true;}});")
    css = f"@media (prefers-reduced-motion: reduce){{#{tid} .track{{animation:none;padding-left:12px}}}}" if reduced else ""
    return html + (f"<script>(function(){{{js}}})();</script>" if js else "") + (f"<style>{css}</style>" if css else "")


# ---------------------------------------------------------------------------
# Scenario content
# ---------------------------------------------------------------------------

SLIDES = {
    ("de", "municipality"): [("Neue Velostation am Bahnhof", "Ab 1. November stehen 180 gedeckte Abstellplätze zur Verfügung.", "bike"),
                             ("Weihnachtsmarkt auf dem Dorfplatz", "Am 5. und 6. Dezember laden 40 Stände zum Bummeln ein.", "market"),
                             ("Schulhaus Matte saniert", "Die Kinder sind nach den Herbstferien ins renovierte Schulhaus zurückgekehrt.", "school"),
                             ("Winterdienst: Parkverbot beachten", "Bei Schneefall gilt auf Gemeindestrassen von 2.00 bis 7.00 Uhr ein Parkverbot.", "snow")],
    ("de", "tourism"): [("Herbstwandern am Seenweg", "Lärchen in Gold und klare Fernsicht – jetzt ist die schönste Wanderzeit.", "mountain"),
                        ("Alpkäsemarkt am 26. September", "Acht Alpbetriebe verkaufen ihren Käse auf dem Dorfplatz.", "market"),
                        ("Schlittelbahn ab Mitte Dezember", "Bei guter Schneelage täglich von 9.00 bis 16.30 Uhr offen.", "snow")],
    ("de", "school"): [("Projektwoche «Wasser»", "Alle Klassen erforschen eine Woche lang den Dorfbach.", "lake"),
                       ("Neuer Pausenplatz", "Die Kletterwand wurde von Eltern und Lehrpersonen gemeinsam gebaut.", "playground"),
                       ("Schulkonzert im Mai", "Der Schulchor singt am 21. Mai um 19.00 Uhr in der Mehrzweckhalle.", "concert")],
    ("fr", "municipality"): [("Nouvelle déchetterie aux Prés", "Dès le 2 novembre, la déchetterie accepte aussi les objets encombrants.", "recycling"),
                             ("Marché de Noël", "Les 5 et 6 décembre, une quarantaine de stands sur la place du Village.", "market"),
                             ("Fermeture des bureaux", "L'administration sera fermée du 24 décembre au 4 janvier.", "townhall"),
                             ("Concert de l'Avent", "Le chœur mixte chante au temple le dimanche 13 décembre à 17 h.", "concert")],
    ("fr", "tourism"): [("Le tour du lac en automne", "Deux heures et demie de balade facile, au départ de la place du Marché.", "lake"),
                        ("Fête des vendanges", "Cortège, caveaux ouverts et marché du terroir les 2 et 3 octobre.", "market"),
                        ("Le vieux moulin se visite", "Visites guidées chaque dimanche à 14 h, d'avril à octobre.", "bridge")],
    ("fr", "library"): [("Heure du conte", "Mercredi 4 novembre à 15 h, pour les enfants dès 4 ans.", "library"),
                        ("Club de lecture", "Prochaine rencontre le jeudi 19 novembre à 19 h.", "concert"),
                        ("Atelier BD", "Samedi 28 novembre à 10 h, inscription à l'accueil.", "school")],
    ("it", "municipality"): [("Nuovo ecocentro al Ronco", "Dal 2 novembre l'ecocentro accetta anche gli ingombranti.", "recycling"),
                             ("Mercatino di Natale", "Il 5 e 6 dicembre una quarantina di bancarelle in Piazza Grande.", "market"),
                             ("Lavori in Via Cantonale", "Fino al 20 novembre il traffico è regolato da un semaforo.", "bridge"),
                             ("Concerto della filarmonica", "Sabato 12 dicembre alle 20.30 nella chiesa parrocchiale.", "concert")],
    ("it", "tourism"): [("Castagnata d'autunno", "Domenica 18 ottobre caldarroste e musica popolare in piazza.", "forest"),
                        ("Sentiero dei mulini", "Due ore di passeggiata facile lungo il fiume.", "bridge"),
                        ("Grotti aperti fino a ottobre", "Polenta, formaggini e vino nostrano all'ombra dei castagni.", "lake"),
                        ("Traversata delle creste", "Sei ore di cammino per escursionisti allenati.", "mountain")],
    ("it", "school"): [("Settimana bianca 2027", "Le classi quarte e quinte partono il 15 febbraio.", "snow"),
                       ("Orto della scuola", "Gli allievi di terza hanno raccolto le prime zucche.", "forest"),
                       ("Festa di fine anno", "Venerdì 18 giugno dalle 17.00 nel cortile della scuola.", "playground")],
}

TICKER = {
    "de": ["Bahnhofstrasse: Belagsarbeiten bis 14.11.2026, Umleitung signalisiert",
           "Gemeindeversammlung am 2. Dezember, 20.00 Uhr, Mehrzweckhalle",
           "Kehrichtabfuhr vom 26. Dezember entfällt", "Hallenbad: Revision vom 1. bis 14. Juni"],
    "de-transport": ["Linie 3: Umleitung wegen Baustelle Kirchweg", "Ab 13. Dezember gilt der neue Fahrplan",
                     "Nachtbus N1 fährt auch an Silvester", "Fundbüro am 8. Dezember geschlossen"],
    "de-library": ["Neu eingetroffen: 40 Krimis für den Winter", "Lesung mit Corinne Probst am 12.11.2026",
                   "Rückgabebox beim Haupteingang neu rund um die Uhr offen", "Am 24. Dezember geschlossen"],
    "fr": ["Route de la Côte fermée du 9 au 13 novembre", "Conseil général : séance le 2 décembre à 20 h",
           "Pas de ramassage des ordures le 26 décembre", "Piscine couverte fermée pour révision du 1er au 14 juin"],
    "it": ["Linea 4: deviazione per lavori in Via alla Stazione", "Dal 13 dicembre nuovo orario",
           "Bus notturno N3 anche la notte di San Silvestro", "Sportello oggetti smarriti chiuso l'8 dicembre"],
}


def _slides(lang, kind, rng, n=None):
    raw = SLIDES[(lang, kind)]
    base = rng.randrange(100)
    out = [(h, t, _img(k, (base + i) % 7)) for i, (h, t, k) in enumerate(raw)]
    return out[:n] if n else out


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------

def build(rng):
    cases = []

    def add(lang, expected, html, target, rule, notes, *, trap=False, alt=None, diff="medium"):
        cases.append(Case(CRITERION, lang, expected, html=html, target=target, rule=rule, notes=notes,
                          trap=trap, alt_expected=alt, difficulty=diff))

    # ---------------- F1: auto carousels without pause -----------------
    s = site_by_kind("de", "municipality")
    t = pick_theme(rng)
    car = carousel("aktuell", "Aktuelles aus der Gemeinde", _slides("de", "municipality", rng), ms=6000,
                   prevnext=True, dots=True, lang="de")
    main = "<h1>Willkommen in Beispielwil</h1>\n" + car + "\n" + "\n".join(_sections(s, rng))
    add("de", "failed", _chrome("de", s["org"], main, rng, t, "Startseite – Gemeinde Beispielwil"), "#aktuell",
        "2.2.2/F1", "The news carousel rotates every 6 s indefinitely from page load; prev/next buttons and dots do not stop the rotation and there is no pause control.",
        diff="easy")

    s = site_by_kind("fr", "municipality")
    t = pick_theme(rng)
    car = carousel("a-la-une", "À la une", _slides("fr", "municipality", rng), ms=5000, prevnext=False, dots=True, lang="fr")
    secs = _sections(s, rng)
    main = ('<h1>Commune de Valfictif</h1>\n<div class="side"><div>' + car + '</div><aside class="box"><h2>Guichet</h2>'
            '<p>Lundi à vendredi, 8 h 30 – 11 h 30<br>Jeudi aussi 14 h – 18 h</p></aside></div>\n' + "\n".join(secs))
    add("fr", "failed", _chrome("fr", s["org"], main, rng, t, "Accueil – Commune de Valfictif"), "#a-la-une",
        "2.2.2/F1", "The slideshow changes slide every 5 s in a loop next to the opening-hours box; it only has decorative dots and no pause, stop or hide mechanism.",
        diff="easy")

    s = site_by_kind("it", "tourism")
    t = pick_theme(rng)
    car = carousel("in-evidenza", "In evidenza", _slides("it", "tourism", rng), ms=7000, prevnext=True, lang="it")
    main = ("<h1>Benvenuti in Valfittizia</h1>\n<p>Una valle di boschi di castagni, grotti e villaggi di pietra, a mezz'ora dal lago.</p>\n"
            + car + "\n" + "\n".join(_sections(s, rng)))
    add("it", "failed", _chrome("it", s["org"], main, rng, t, "Ente turistico Valfittizia – Home"), "#in-evidenza",
        "2.2.2/F1", "The tourism carousel advances every 7 s without end; the arrow buttons only change the slide and the rotation cannot be paused or stopped.",
        diff="medium")

    # ---------------- F2: tickers without pause -----------------
    s = site_by_kind("de", "municipality")
    t = pick_theme(rng)
    tk = ticker("laufband", "Kurz gemeldet", TICKER["de"], secs=34)
    main = ("<h1>Aktuelles</h1>\n" + tk + "\n<p>Hier finden Sie Mitteilungen der Gemeindeverwaltung und der Behörden.</p>\n"
            + "\n".join(_sections(s, rng, 3)))
    add("de", "failed", _chrome("de", s["org"], main, rng, t, "Aktuelles – Gemeinde Beispielwil"), "#laufband",
        "2.2.2/F2", "The '+++' ticker scrolls continuously via a CSS infinite animation next to the news content and offers no pause, stop or hide control.",
        diff="easy")

    s = site_by_kind("it", "transport")
    t = pick_theme(rng)
    tk = ticker("info-traffico", "Info traffico", TICKER["it"], js_scroll=True)
    main = ("<h1>Trasporti pubblici di Modellina</h1>\n<p>Quattro linee di bus collegano Modellina e le frazioni ogni 15 minuti.</p>\n"
            + "\n".join(_sections(s, rng)) + "\n" + tk)
    add("it", "failed", _chrome("it", s["org"], main, rng, t, "Trasporti pubblici di Modellina"), "#info-traffico",
        "2.2.2/F2", "A script scrolls the traffic-information strip every 40 ms in an endless loop below the page content; nothing lets the user pause or hide it.",
        diff="medium")

    # ---------------- F3: auto-updating live boxes -----------------
    s = site_by_kind("fr", "transport")
    t = pick_theme(rng)
    rows = [["1", "Exempleval", 2], ["2", "Zone artisanale des Prés", 5], ["4", "Bourg-Modèle", 8],
            ["1", "Hôpital", 12], ["5", "Les Mayens-Fictifs", 17]]
    live = ('<section id="departs" class="live" aria-labelledby="departs-h"><h2 id="departs-h">Prochains départs – Gare de Valfictif</h2>'
            '<table><thead><tr><th scope="col">Ligne</th><th scope="col">Direction</th><th scope="col">Départ</th></tr></thead>'
            '<tbody></tbody></table><p class="muted">Mise à jour automatique</p></section>'
            "<script>(function(){var R=" + json.dumps(rows, ensure_ascii=False) + ";var tb=document.querySelector('#departs tbody');"
            "function draw(){tb.innerHTML='';R.forEach(function(r){var tr=document.createElement('tr');"
            "[r[0],r[1],'dans '+r[2]+' min'].forEach(function(v){var td=document.createElement('td');td.textContent=v;tr.appendChild(td);});"
            "tb.appendChild(tr);});}function tick(){R.forEach(function(r){r[2]-=1;if(r[2]<1){r[2]+=20;}});"
            "R.sort(function(a,b){return a[2]-b[2];});draw();}draw();setInterval(tick,6000);})();</script>")
    main = "<h1>Transports publics de Valfictif</h1>\n" + "\n".join(_sections(s, rng, 1)) + "\n" + live + "\n" + "\n".join(_sections(s, rng, 1))
    add("fr", "failed", _chrome("fr", s["org"], main, rng, t, "Horaires en temps réel – TPV"), "#departs",
        "2.2.2/F3", "The departures table is rewritten by script every 6 s alongside other content, with no way to pause, stop, hide it or change the update frequency.",
        diff="medium")

    s = site_by_kind("de", "transport")
    t = pick_theme(rng)
    vals = [["Parkhaus Seeweg", [124, 119, 121, 116, 109]], ["Parkplatz Bahnhof", [18, 15, 16, 12, 9]],
            ["Tiefgarage Dorfzentrum", [57, 61, 58, 55, 60]]]
    live = ('<section id="parkleitsystem" class="live" aria-labelledby="pls-h"><h2 id="pls-h">Freie Parkplätze</h2><ul></ul>'
            '<p class="muted">Daten des Parkleitsystems</p></section>'
            "<script>(function(){var V=" + json.dumps(vals, ensure_ascii=False) + ";var k=0;var ul=document.querySelector('#parkleitsystem ul');"
            "function draw(){ul.innerHTML='';V.forEach(function(v){var li=document.createElement('li');"
            "li.textContent=v[0]+': '+v[1][k%v[1].length]+' frei';ul.appendChild(li);});}draw();"
            "setInterval(function(){k+=1;draw();},5000);})();</script>")
    side = ('<div class="side"><div><h1>Mit dem Auto ins Zentrum</h1><p>Die Parkhäuser in Beispielwil sind über die Seestrasse '
            'erreichbar. Die erste halbe Stunde ist gratis, danach kostet jede Stunde CHF 2.–.</p>'
            '<p>Für Pendlerinnen und Pendler empfehlen wir das Park-and-Ride beim Bahnhof.</p></div>' + live + '</div>')
    add("de", "failed", _chrome("de", s["org"], side, rng, t, "Parkieren – Beispielwiler Verkehrsbetriebe"), "#parkleitsystem",
        "2.2.2/F3", "The free-parking list updates itself every 5 s next to the article text and the page offers no control to pause, stop, hide or slow down the updates.",
        diff="medium")

    # ---------------- F4: blinking text -----------------
    s = site_by_kind("it", "municipality")
    t = pick_theme(rng)
    css = ("#avviso-strada{border:2px solid #c2453b;border-radius:8px;padding:10px 14px;margin:12px 0}"
           "#avviso-strada strong{animation:lampeggio 1.2s steps(2,start) infinite;color:#a1261c}"
           "@keyframes lampeggio{to{visibility:hidden}}")
    main = ('<h1>Attualità</h1>\n<p id="avviso-strada"><strong>Avviso: Via ai Monti chiusa per caduta sassi fino a nuovo avviso.</strong> '
            'Deviazione per il traffico locale da Via Cantonale.</p>\n' + "\n".join(_sections(s, rng, 3)))
    add("it", "failed", _chrome("it", s["org"], main, rng, t, "Attualità – Comune di Esempiano", css=css), "#avviso-strada",
        "2.2.2/F4", "The road-closure notice blinks (1.2 s cycle) through an infinite CSS animation and there is no way to stop the blinking.",
        diff="easy")

    s = site_by_kind("fr", "school")
    t = pick_theme(rng)
    css = (".neu{display:inline-block;background:#7a1f2b;color:#ffffff;padding:2px 8px;border-radius:4px;margin-left:8px;"
           "animation:clignote 1.5s ease-in-out infinite}@keyframes clignote{0%,100%{opacity:1}50%{opacity:.1}}")
    main = ('<h1>Informations aux parents</h1>\n<ul class="cards" style="list-style:none;padding:0">'
            '<li class="card" id="camp"><h2>Camp de ski 2027<span class="neu">Inscriptions ouvertes !</span></h2>'
            '<p>Le camp des élèves de 7e et 8e aura lieu du 8 au 12 février 2027 aux Mayens-Fictifs. Délai d\'inscription : 30 novembre.</p></li>'
            '<li class="card"><h2>Devoirs surveillés</h2><p>Lundi, mardi et jeudi de 15 h 30 à 16 h 30.</p></li>'
            '<li class="card"><h2>Vacances d\'automne</h2><p>Du 10 au 25 octobre 2026.</p></li></ul>')
    add("fr", "failed", _chrome("fr", s["org"], main, rng, t, "Informations aux parents – École de Valfictif", css=css), "#camp .neu",
        "2.2.2/F4", "The 'Inscriptions ouvertes !' label fades in and out every 1.5 s forever (infinite CSS animation) and cannot be stopped.",
        diff="medium")

    # ---------------- F5: hover-only pause -----------------
    s = site_by_kind("de", "tourism")
    t = pick_theme(rng)
    car = carousel("highlights", "Highlights", _slides("de", "tourism", rng), ms=6000, prevnext=True, dots=True,
                   hover_pause=True, lang="de")
    main = ("<h1>Ferien in Ober-Beispielwil</h1>\n" + car + "\n<p>Fährt die Maus über das Bild, bleibt es stehen.</p>\n"
            + "\n".join(_sections(s, rng)))
    add("de", "failed", _chrome("de", s["org"], main, rng, t, "Ferien in Ober-Beispielwil"), "#highlights",
        "2.2.2/F5", "Rotation stops only while the pointer or focus is inside the carousel and resumes on leaving, so it can never be paused in the WCAG sense; no pause button exists.",
        diff="hard")

    # ---------------- P1: pause / stop buttons -----------------
    s = site_by_kind("fr", "tourism")
    t = pick_theme(rng)
    car = carousel("decouvrir", "À découvrir", _slides("fr", "tourism", rng), ms=6000, prevnext=True,
                   toggle=("Mettre en pause", "Reprendre le défilement"), lang="fr")
    main = "<h1>Bienvenue au Val-Modèle</h1>\n" + car + "\n" + "\n".join(_sections(s, rng))
    add("fr", "passed", _chrome("fr", s["org"], main, rng, t, "Office du tourisme du Val-Modèle"), "#decouvrir",
        "2.2.2/P1", "The carousel auto-rotates but a visible 'Mettre en pause' button stops the rotation until the user resumes it.",
        diff="easy")

    s = site_by_kind("de", "transport")
    t = pick_theme(rng)
    tk = ticker("betriebsinfo", "Betriebsinfo", TICKER["de-transport"], secs=30, pause=("Anhalten", "Weiterlaufen"))
    main = (tk + "\n<h1>Fahrplan</h1>\n<p>Der neue Fahrplan gilt ab 13. Dezember 2026. Linie 3 fährt neu bis zum Spital Mustersee.</p>\n"
            + "\n".join(_sections(s, rng)))
    add("de", "passed", _chrome("de", s["org"], main, rng, t, "Fahrplan – Beispielwiler Verkehrsbetriebe"), "#betriebsinfo",
        "2.2.2/P1", "The scrolling service-information ticker has an 'Anhalten' button that pauses the CSS animation until 'Weiterlaufen' is pressed.",
        diff="easy")

    s = site_by_kind("it", "utility")
    t = pick_theme(rng)
    lv = [[193.42, 11.8], [193.43, 11.8], [193.43, 11.7], [193.44, 11.7], [193.44, 11.6]]
    live = ('<section id="livello-lago" class="live" aria-labelledby="ll-h"><h2 id="ll-h">Livello del lago e temperatura</h2>'
            '<p class="val"></p><button type="button" class="tgl">Sospendi aggiornamento</button></section>'
            "<script>(function(){var L=" + json.dumps(lv) + ";var k=0;var t=null;var p=document.querySelector('#livello-lago .val');"
            "var b=document.querySelector('#livello-lago .tgl');function draw(){var v=L[k%L.length];"
            "p.textContent='Livello: '+v[0].toFixed(2).replace('.',',')+' m s.l.m. · Acqua: '+v[1].toFixed(1).replace('.',',')+' °C';}"
            "function go(){t=setInterval(function(){k+=1;draw();},5000);}draw();go();"
            "b.addEventListener('click',function(){if(t){clearInterval(t);t=null;b.textContent='Riprendi aggiornamento';}"
            "else{go();b.textContent='Sospendi aggiornamento';}});})();</script>")
    main = ('<h1>Qualità dell\'acqua</h1>\n<p>La nostra acqua proviene per l\'80 % da sorgenti e per il 20 % dalla falda.</p>\n'
            + live + "\n" + "\n".join(_sections(s, rng)))
    add("it", "passed", _chrome("it", s["org"], main, rng, t, "Qualità dell'acqua – Azienda acqua potabile Valfittizia"), "#livello-lago",
        "2.2.2/P1", "The lake level box refreshes every 5 s but its 'Sospendi aggiornamento' button stops the updates until the user resumes them.",
        diff="medium")

    # ---------------- P2: hide -----------------
    s = site_by_kind("de", "municipality")
    t = pick_theme(rng)
    tk = ticker("kurzinfo", "Kurz gemeldet", TICKER["de"][1:] + TICKER["de"][:1], secs=40, hide="Ausblenden")
    main = ("<h1>Gemeindeverwaltung</h1>\n" + tk + "\n<p>Die Gemeindeverwaltung befindet sich im Gemeindehaus an der Dorfstrasse 1.</p>\n"
            + "\n".join(_sections(s, rng)))
    add("de", "passed", _chrome("de", s["org"], main, rng, t, "Verwaltung – Gemeinde Beispielwil"), "#kurzinfo",
        "2.2.2/P2", "The ticker scrolls continuously but its 'Ausblenden' button hides the whole ticker, which satisfies the 'hide' option of the SC.",
        diff="medium")

    # ---------------- P3: frequency control -----------------
    s = site_by_kind("fr", "transport")
    t = pick_theme(rng)
    rows = [["2", "Zone artisanale des Prés", 3], ["1", "Exempleval", 6], ["5", "Les Mayens-Fictifs", 11], ["4", "Bourg-Modèle", 14]]
    live = ('<section id="tableau-departs" class="live" aria-labelledby="td-h"><h2 id="td-h">Départs – Arrêt Poste</h2>'
            '<ul class="rows"></ul><label for="freq">Actualisation</label><select id="freq">'
            '<option value="6000">toutes les 6 secondes</option><option value="60000">toutes les minutes</option>'
            '<option value="0">jamais (manuelle)</option></select> <button type="button" class="now">Actualiser</button></section>'
            "<script>(function(){var R=" + json.dumps(rows, ensure_ascii=False) + ";var t=null;var ul=document.querySelector('#tableau-departs .rows');"
            "function draw(){ul.innerHTML='';R.forEach(function(r){var li=document.createElement('li');"
            "li.textContent='Ligne '+r[0]+' → '+r[1]+' : '+r[2]+' min';ul.appendChild(li);});}"
            "function tick(){R.forEach(function(r){r[2]-=1;if(r[2]<1){r[2]+=15;}});R.sort(function(a,b){return a[2]-b[2];});draw();}"
            "function set(ms){if(t){clearInterval(t);t=null;}if(ms>0){t=setInterval(tick,ms);}}"
            "document.getElementById('freq').addEventListener('change',function(e){set(parseInt(e.target.value,10));});"
            "document.querySelector('#tableau-departs .now').addEventListener('click',tick);draw();set(6000);})();</script>")
    main = ('<h1>Arrêts et accessibilité</h1>\n<p>Trente des trente-huit arrêts sont accessibles de plain-pied.</p>\n'
            + live + "\n" + "\n".join(_sections(s, rng)))
    add("fr", "passed", _chrome("fr", s["org"], main, rng, t, "Arrêt Poste – Transports publics de Valfictif"), "#tableau-departs",
        "2.2.2/P3", "The departures list auto-updates every 6 s, but the 'Actualisation' select lets users slow the updates or switch them off (manual refresh).",
        diff="medium")

    # ---------------- T1: stops within 5 s -----------------
    s = site_by_kind("it", "library")
    t = pick_theme(rng)
    css = (".nuovo{display:inline-block;background:#1f6f8b;color:#ffffff;font-size:.8rem;padding:1px 6px;border-radius:4px;"
           "margin-left:6px;animation:pulsa 1s ease-in-out 3}@keyframes pulsa{0%,100%{opacity:1}50%{opacity:.2}}")
    books = [("La casa sul lago", "Giulia Fittizi"), ("Sentieri d'autunno", "Paolo Campione"),
             ("Il mugnaio di Valfittizia", "Lucia Esempio"), ("Polenta e castagne", "Marco Modello")]
    lis = "".join(f'<li><cite>{esc(b)}</cite> – {esc(a)}' + ('<span class="nuovo" id="badge-novita">Novità</span>' if i == 0 else "")
                  + "</li>" for i, (b, a) in enumerate(books))
    main = ('<h1>Ultimi arrivi</h1>\n<p>Questo mese abbiamo accolto 64 nuovi titoli. Eccone alcuni.</p>\n<ul>' + lis + "</ul>\n"
            + "\n".join(_sections(s, rng)))
    add("it", "passed", _chrome("it", s["org"], main, rng, t, "Ultimi arrivi – Biblioteca di Modellina", css=css), "#badge-novita",
        "2.2.2/T1", "The 'Novità' badge pulses only three times (3 × 1 s) and then stays still, so the blinking stops within 5 seconds.",
        trap=True, diff="medium")

    s = site_by_kind("de", "utility")
    t = pick_theme(rng)
    months = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    vals = [52, 48, 51, 55, 61, 68, 74, 71, 60, 54, 50, 53]
    bars = "".join(f'<li><span class="bar" style="height:{v * 2}px"></span><span class="v">{v}</span><span class="m">{m}</span></li>'
                   for m, v in zip(months, vals))
    css = ("#verbrauch ol{display:flex;align-items:flex-end;gap:6px;list-style:none;padding:0;height:190px;border-bottom:2px solid #3d464d}"
           "#verbrauch li{display:flex;flex-direction:column-reverse;align-items:center;font-size:.8rem}"
           "#verbrauch .bar{display:block;width:26px;background:#1f6f8b;transform-origin:bottom;animation:wachsen 1.5s ease-out 1 both}"
           "@keyframes wachsen{from{transform:scaleY(0)}to{transform:scaleY(1)}}")
    fig = ('<figure id="verbrauch"><figcaption>Wasserverbrauch 2025 in 1000 m³ pro Monat (Total 697 000 m³)</figcaption>'
           f'<ol>{bars}</ol></figure>')
    main = ('<h1>Wasserverbrauch</h1>\n<p>Im Sommer steigt der Verbrauch wegen Gartenbewässerung und Schwimmbädern deutlich an.</p>\n'
            + fig + "\n" + "\n".join(_sections(s, rng)))
    add("de", "passed", _chrome("de", s["org"], main, rng, t, "Wasserverbrauch 2025 – Wasserversorgung Fiktal", css=css), "#verbrauch",
        "2.2.2/T1", "The chart bars grow once in 1.5 s when the page loads (animation-iteration-count 1) and then stay still: movement ends well within 5 s.",
        trap=True, diff="medium")

    # ---------------- T2: loading indicator alone -----------------
    t = pick_theme(rng)
    css = (".wait{max-width:520px;margin:80px auto;text-align:center}"
           ".spin{width:64px;height:64px;animation:tourne 1.2s linear infinite}@keyframes tourne{to{transform:rotate(360deg)}}")
    spin = ('<svg class="spin" viewBox="0 0 50 50" aria-hidden="true" focusable="false"><circle cx="25" cy="25" r="20" fill="none" '
            'stroke="#c9d3d8" stroke-width="6"/><path d="M25 5a20 20 0 0 1 20 20" fill="none" stroke="#0b4f6c" stroke-width="6"/></svg>')
    body = ('<main><div class="wait" id="transmission" role="status">' + spin +
            '<h1>Transmission en cours</h1><p>Votre demande de raccordement est en cours de transmission au Service des eaux. '
            'Veuillez patienter, cela peut prendre jusqu\'à une minute.</p></div></main>')
    html = page("fr-CH", "Transmission en cours – Service des eaux d'Exempleval", body, theme=t, css=css)
    add("fr", "passed", html, "#transmission", "2.2.2/T2",
        "The spinning indicator is the only content of this processing page (nothing is presented in parallel), so no pause mechanism is required.",
        trap=True, diff="hard")

    # ---------------- T3: user-started slideshow -----------------
    s = site_by_kind("it", "tourism")
    t = pick_theme(rng)
    car = carousel("galleria", "Galleria fotografica", _slides("it", "tourism", rng), ms=4000, auto=False, prevnext=False,
                   start_btn="Avvia la presentazione", once=True, lang="it")
    main = ("<h1>Escursioni</h1>\n<p>Tutti i sentieri partono dalla piazza del paese. Guardate le immagini dei percorsi più belli.</p>\n"
            + car + "\n" + "\n".join(_sections(s, rng)))
    add("it", "passed", _chrome("it", s["org"], main, rng, t, "Escursioni – Ente turistico Valfittizia"), "#galleria",
        "2.2.2/T3", "The slideshow does not move until the user presses 'Avvia la presentazione'; content started by user activation does not 'start automatically'.",
        trap=True, diff="hard")

    # ---------------- N1: manual carousels -----------------
    s = site_by_kind("de", "school")
    t = pick_theme(rng)
    car = carousel("einblicke", "Einblicke in den Schulalltag", _slides("de", "school", rng), auto=False, prevnext=True,
                   dots=True, lang="de")
    main = "<h1>Schule Beispielberg</h1>\n<p>Rund 380 Kinder besuchen bei uns den Kindergarten und die Primarschule.</p>\n" + car + "\n" + "\n".join(_sections(s, rng))
    cases.append(Case(CRITERION, "de", "inapplicable", html=_chrome("de", s["org"], main, rng, t, "Schule Beispielberg"),
                      target=None, rule="2.2.2/N1",
                      notes="The slider looks like a carousel but has no timer: slides change only when the user presses the arrow buttons, so nothing moves automatically.",
                      trap=True, difficulty="medium"))

    s = site_by_kind("it", "school")
    t = pick_theme(rng)
    car = carousel("vita-scolastica", "Vita scolastica", _slides("it", "school", rng), auto=False, prevnext=True, lang="it")
    main = "<h1>Scuola di Esempiano</h1>\n" + "\n".join(_sections(s, rng)) + "\n" + car
    cases.append(Case(CRITERION, "it", "inapplicable", html=_chrome("it", s["org"], main, rng, t, "Scuola di Esempiano – Home"),
                      target=None, rule="2.2.2/N1",
                      notes="The image slider only changes on prev/next activation; no script starts any automatic movement or update.",
                      trap=True, difficulty="easy"))

    # ---------------- C1: prefers-reduced-motion only -----------------
    s = site_by_kind("de", "library")
    t = pick_theme(rng)
    tk = ticker("neuigkeiten", "Neu", TICKER["de-library"], secs=32, reduced=True)
    main = ("<h1>Bibliothek Mustersee</h1>\n" + tk + "\n<p>Über 25 000 Bücher, Hörbücher und Spiele für alle Generationen.</p>\n"
            + "\n".join(_sections(s, rng)))
    add("de", "cantTell", _chrome("de", s["org"], main, rng, t, "Bibliothek Mustersee – Startseite"), "#neuigkeiten",
        "2.2.2/C1", "The ticker scrolls endlessly and stops only when the browser reports prefers-reduced-motion; there is no on-page control, and whether a user-agent setting counts as the mechanism is disputed.",
        alt="failed", diff="hard")

    # ---------------- C2: control on another page -----------------
    s = site_by_kind("fr", "library")
    t = pick_theme(rng)
    car = carousel("agenda-diapo", "Agenda", _slides("fr", "library", rng), ms=6000, prevnext=True, lang="fr",
                   extra_ctrl='<a href="preferences-affichage.html">Désactiver les animations (préférences d\'affichage)</a>')
    main = "<h1>Bibliothèque de Bourg-Modèle</h1>\n" + car + "\n" + "\n".join(_sections(s, rng))
    add("fr", "cantTell", _chrome("fr", s["org"], main, rng, t, "Accueil – Bibliothèque de Bourg-Modèle"), "#agenda-diapo",
        "2.2.2/C2", "The carousel rotates automatically; the only control is a link to a separate display-preferences page whose effect on this carousel cannot be verified from the page.",
        diff="hard")

    # ---------------- C3: decorative loop -----------------
    s = site_by_kind("it", "utility")
    t = pick_theme(rng)
    css = ("#onde{display:block;width:100%;height:70px;background:#e3eef6;overflow:hidden}"
           "#onde .w{animation:scorri 9s linear infinite}#onde .w2{animation-duration:14s}"
           "@keyframes scorri{from{transform:translateX(0)}to{transform:translateX(-120px)}}")
    waves = ('<svg id="onde" viewBox="0 0 800 70" preserveAspectRatio="none" aria-hidden="true" focusable="false">'
             '<path class="w" d="M0 40 Q30 25 60 40 T120 40 T180 40 T240 40 T300 40 T360 40 T420 40 T480 40 T540 40 T600 40 T660 40 T720 40 T780 40 T840 40 T900 40 T960 40 V70 H0Z" fill="#7fb3d5"/>'
             '<path class="w w2" d="M0 50 Q30 38 60 50 T120 50 T180 50 T240 50 T300 50 T360 50 T420 50 T480 50 T540 50 T600 50 T660 50 T720 50 T780 50 T840 50 T900 50 T960 50 V70 H0Z" fill="#1f6f8b"/></svg>')
    main = (waves + '\n<h1>Azienda acqua potabile Valfittizia</h1>\n<p>Ogni giorno forniamo circa 1200 m³ di acqua potabile a economie domestiche e aziende.</p>\n'
            + "\n".join(_sections(s, rng, 3)))
    add("it", "cantTell", _chrome("it", s["org"], main, rng, t, "Azienda acqua potabile Valfittizia – Home", css=css), "#onde",
        "2.2.2/C3", "Two wave shapes drift endlessly in a purely decorative header graphic without text; whether decorative motion is 'moving information' under the SC is disputed.",
        diff="hard")

    return cases
