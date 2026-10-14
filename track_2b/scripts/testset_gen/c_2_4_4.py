"""2.4.4 Link Purpose (In Context) — 40 cases.

Decision rules: PROTOCOL.md §2.4.4. Programmatic link context = same sentence, closest
block container (paragraph), list item ancestor(s), table cell + associated header cells,
aria-describedby targets; the link's own accessible name includes aria-label /
aria-labelledby / visually hidden text. A preceding heading is NOT context (→ cantTell).
"""
from common import *

CRITERION = "2.4.4"

# --------------------------------------------------------------------------- content
# news: (title, teaser, slug, image scene)
NEWS = {
    "de": [
        ("Neue Velostation am Bahnhof", "Ab 1. November stehen beim Bahnhof 120 gedeckte Veloabstellplätze bereit.", "velostation", "bike"),
        ("Gemeindeversammlung vom 24. November", "Traktandiert sind das Budget 2027 und die Sanierung des Schulhauses Matte.", "gemeindeversammlung", "townhall"),
        ("Grüngutabfuhr im Winter", "Von Dezember bis Februar wird das Grüngut nur noch alle zwei Wochen abgeholt.", "gruengut-winter", "recycling"),
        ("Räbeliechtli-Umzug", "Am 6. November ziehen die Kinder um 18 Uhr mit ihren Laternen durchs Dorf.", "raebeliechtli", "concert"),
        ("Seeweg gesperrt", "Wegen Belagsarbeiten ist der Seeweg vom 3. bis 21. November gesperrt.", "seeweg-sperrung", "lake"),
        ("Bibliothek neu auch am Samstag offen", "Ab Januar ist die Bibliothek zusätzlich am Samstag von 9 bis 12 Uhr geöffnet.", "bibliothek-samstag", "library"),
        ("Hundekontrollmarken 2027", "Die neuen Marken können ab dem 4. Januar am Schalter der Einwohnerdienste bezogen werden.", "hundemarken", "townhall"),
        ("Winterdienst: Parkieren verboten", "Vom 1. Dezember bis 31. März ist das Parkieren auf Gemeindestrassen nachts verboten.", "winterdienst", "snow"),
    ],
    "fr": [
        ("Nouvelle vélostation à la gare", "Dès le 1er novembre, 120 places couvertes pour vélos sont à disposition à la gare.", "velostation", "bike"),
        ("Assemblée communale du 24 novembre", "L'ordre du jour comprend le budget 2027 et la rénovation du collège des Vergers.", "assemblee-communale", "townhall"),
        ("Déchets verts : rythme d'hiver", "De décembre à février, les déchets verts ne sont ramassés qu'une semaine sur deux.", "dechets-verts-hiver", "recycling"),
        ("Fête des lumignons", "Le 6 novembre à 18 h, les enfants traversent le village avec leurs lumignons.", "fete-lumignons", "concert"),
        ("Avenue de la Gare en travaux", "Circulation alternée du 3 au 21 novembre en raison de la pose d'un nouveau revêtement.", "travaux-gare", "bridge"),
        ("La bibliothèque ouvre le samedi", "Dès janvier, la bibliothèque sera également ouverte le samedi de 9 h à 12 h.", "bibliotheque-samedi", "library"),
        ("Marques de contrôle pour chiens 2027", "Les nouvelles marques sont disponibles dès le 4 janvier au guichet du contrôle des habitants.", "marques-chiens", "townhall"),
        ("Service hivernal : stationnement interdit", "Du 1er décembre au 31 mars, le stationnement de nuit est interdit sur les routes communales.", "service-hivernal", "snow"),
    ],
    "it": [
        ("Nuova velostazione alla stazione", "Dal 1° novembre sono disponibili alla stazione 120 posteggi coperti per biciclette.", "velostazione", "bike"),
        ("Assemblea comunale del 24 novembre", "All'ordine del giorno il preventivo 2027 e il risanamento delle scuole elementari.", "assemblea-comunale", "townhall"),
        ("Scarti vegetali: calendario invernale", "Da dicembre a febbraio gli scarti vegetali vengono raccolti solo ogni due settimane.", "scarti-vegetali", "recycling"),
        ("Sfilata dei lampioncini", "Il 6 novembre alle 18 i bambini attraversano il nucleo con i lampioncini accesi.", "sfilata-lampioncini", "concert"),
        ("Lavori in Via Cantonale", "Dal 3 al 21 novembre è in vigore il senso unico alternato per la posa della nuova pavimentazione.", "lavori-via-cantonale", "bridge"),
        ("La biblioteca apre anche il sabato", "Da gennaio la biblioteca sarà aperta anche il sabato dalle 9 alle 12.", "biblioteca-sabato", "library"),
        ("Marche di controllo per cani 2027", "Le nuove marche si possono ritirare dal 4 gennaio allo sportello del controllo abitanti.", "marche-cani", "townhall"),
        ("Servizio invernale: divieto di posteggio", "Dal 1° dicembre al 31 marzo è vietato posteggiare di notte sulle strade comunali.", "servizio-invernale", "snow"),
    ],
    "en": [
        ("New bike station at the railway station", "From 1 November, 120 covered bike parking spaces are available next to platform 1.", "bike-station", "bike"),
        ("Lakeside path closed", "The lakeside path between the harbour and the campsite is closed from 3 to 21 November.", "lakeside-path", "lake"),
        ("Winter timetable for mountain buses", "From 13 December the Example Valley buses run every 30 minutes on weekends.", "winter-buses", "bus"),
        ("Christmas market on the village square", "Thirty stalls, mulled wine and a lantern parade on 12 and 13 December.", "christmas-market", "market"),
    ],
}

# downloads: (title, file slug, meta)
DOCS = {
    "de": [("Abfallkalender 2027", "abfallkalender-2027.pdf", "PDF, 240 KB"),
           ("Gebührenreglement Wasserversorgung", "gebuehrenreglement-wasser.pdf", "PDF, 410 KB"),
           ("Merkblatt Feuerungskontrolle", "merkblatt-feuerungskontrolle.pdf", "PDF, 180 KB"),
           ("Anmeldeformular Mittagstisch", "anmeldung-mittagstisch.pdf", "PDF, 95 KB"),
           ("Jahresbericht 2025", "jahresbericht-2025.pdf", "PDF, 2,1 MB")],
    "fr": [("Calendrier des déchets 2027", "calendrier-dechets-2027.pdf", "PDF, 240 Ko"),
           ("Règlement sur les taxes de l'eau", "reglement-taxes-eau.pdf", "PDF, 410 Ko"),
           ("Aide-mémoire contrôle des chauffages", "aide-memoire-chauffages.pdf", "PDF, 180 Ko"),
           ("Inscription à la cantine scolaire", "inscription-cantine.pdf", "PDF, 95 Ko"),
           ("Rapport annuel 2025", "rapport-annuel-2025.pdf", "PDF, 2,1 Mo")],
    "it": [("Calendario dei rifiuti 2027", "calendario-rifiuti-2027.pdf", "PDF, 240 KB"),
           ("Regolamento tasse acqua potabile", "regolamento-tasse-acqua.pdf", "PDF, 410 KB"),
           ("Promemoria controllo impianti di combustione", "promemoria-combustione.pdf", "PDF, 180 KB"),
           ("Iscrizione alla mensa scolastica", "iscrizione-mensa.pdf", "PDF, 95 KB"),
           ("Rapporto annuale 2025", "rapporto-annuale-2025.pdf", "PDF, 2,1 MB")],
    "en": [("Hiking map Example Valley", "hiking-map.pdf", "PDF, 1.2 MB"),
           ("Bus timetable winter 2026/27", "bus-timetable-winter.pdf", "PDF, 300 KB"),
           ("Hostel house rules", "house-rules.pdf", "PDF, 80 KB")],
}

# courses / events: (name, date, place, slug)
COURSES = {
    "de": [("Erste Hilfe bei Kleinkindern", "Di, 3.11.2026, 19.00 Uhr", "Kirchgemeindehaus", "erste-hilfe"),
           ("Velofahren für Senioren", "Sa, 7.11.2026, 9.30 Uhr", "Schulhausplatz Matte", "velokurs"),
           ("Kompostieren im Garten", "Mi, 11.11.2026, 18.30 Uhr", "Werkhof", "kompost"),
           ("Smartphone-Grundkurs", "Do, 19.11.2026, 14.00 Uhr", "Bibliothek", "smartphone")],
    "fr": [("Premiers secours aux petits enfants", "mar. 3.11.2026, 19 h", "Salle de paroisse", "premiers-secours"),
           ("Le vélo en toute sécurité pour les aînés", "sam. 7.11.2026, 9 h 30", "Cour du collège", "velo-aines"),
           ("Compostage au jardin", "mer. 11.11.2026, 18 h 30", "Voirie", "compostage"),
           ("Cours de base smartphone", "jeu. 19.11.2026, 14 h", "Bibliothèque", "smartphone")],
    "it": [("Primo soccorso per bambini piccoli", "mar 3.11.2026, ore 19", "Sala parrocchiale", "primo-soccorso"),
           ("In bicicletta sicuri per anziani", "sab 7.11.2026, ore 9.30", "Piazzale delle scuole", "bici-anziani"),
           ("Il compostaggio in giardino", "mer 11.11.2026, ore 18.30", "Magazzino comunale", "compostaggio"),
           ("Corso base smartphone", "gio 19.11.2026, ore 14", "Biblioteca", "smartphone")],
    "en": [("Guided glacier walk", "Sat 7 Nov 2026, 8.00", "Valley station", "glacier-walk"),
           ("Cheese-making demonstration", "Wed 11 Nov 2026, 15.00", "Alpine dairy", "cheese"),
           ("Snowshoe tour for beginners", "Sun 13 Dec 2026, 10.00", "Tourist office", "snowshoe")],
}

GENERIC = {
    "de": ["Mehr", "Weiterlesen", "Hier", "Details", "Mehr erfahren", "Zum Beitrag"],
    "fr": ["Plus", "Lire la suite", "Ici", "Détails", "En savoir plus", "Voir"],
    "it": ["Di più", "Leggi tutto", "Qui", "Dettagli", "Scopri di più", "Continua"],
    "en": ["More", "Read more", "Here", "Details"],
}
DOWNLOAD = {"de": "Download", "fr": "Télécharger", "it": "Scarica", "en": "Download"}
REGISTER = {"de": "Anmelden", "fr": "S'inscrire", "it": "Iscriversi", "en": "Book"}
NEWS_H = {"de": "Aktuelles", "fr": "Actualités", "it": "Attualità", "en": "News"}
DOCS_H = {"de": "Dokumente und Formulare", "fr": "Documents et formulaires", "it": "Documenti e moduli", "en": "Downloads"}
COURSE_H = {"de": "Kurse im November", "fr": "Cours en novembre", "it": "Corsi di novembre", "en": "Activities"}
TH = {
    "de": ("Kurs", "Datum", "Ort", "Anmeldung"), "fr": ("Cours", "Date", "Lieu", "Inscription"),
    "it": ("Corso", "Data", "Luogo", "Iscrizione"), "en": ("Activity", "Date", "Meeting point", "Booking"),
}
SR_CSS = ".visually-hidden{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}"
CARD_CSS = (".news-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:18px}"
            ".news-card{border:1px solid #d4d7de;border-radius:10px;overflow:hidden;background:#fff}"
            ".news-card img{display:block;width:100%;height:auto}.news-card .body{padding:12px 14px}"
            ".news-card h3{margin:.2em 0 .4em;font-size:1.05rem}.news-card .date{font-size:.85rem;margin:0}"
            ".more{margin:.6em 0 0;font-weight:600}")


def org_for(rng, lang):
    pool = {"de": ORGS["de"][:5], "fr": ORGS["fr"][:4], "it": ORGS["it"][:4], "en": ORGS["en"][:2]}[lang]
    return pick(rng, pool)


def title_for(lang, section, org):
    return f"{section} – {org}"


def img_for(item, lang, idx):
    kind = item[3]
    return asset(f"scene-{kind}-{idx % 3}", scene(kind, w=420, h=240, seed=idx % 3))


def date_str(lang, d):
    return {"de": f"{d}.10.2026", "fr": f"{d}.10.2026", "it": f"{d}.10.2026", "en": f"{d} Oct 2026"}[lang]


# --------------------------------------------------------------------------- builders
# Each builder returns (main_html, target_selector, notes, difficulty, extra_css)

def b_card_grid(rng, lang, *, mode):
    """News cards: img + heading + teaser + link in its own paragraph.

    mode: "heading-only"  -> generic link, no programmatic context      (cantTell, C1)
          "describedby"   -> generic link + aria-describedby to heading  (passed, T4)
          "title-link"    -> heading text is the link                    (passed, P1)
          "sr-text"       -> generic visible text + visually hidden topic (passed, T4)
          "title-attr"    -> generic link + title attribute only         (cantTell, C2)
    """
    items = sample(rng, NEWS[lang], 4 if lang != "en" else 3)
    word = pick(rng, GENERIC[lang][:3])
    tgt_i = rng.randrange(len(items))
    h = pick(rng, ["h2", "h3"])
    cards = []
    for i, (t, teaser, slug, kind) in enumerate(items):
        hid = f"news-{slug}"
        img = f'<img src="{img_for(items[i], lang, i)}" alt="">'
        idattr = ' id="news-link-%d"' % (i + 1)
        if mode == "heading-only":
            head = f'<{h} id="{hid}">{esc(t)}</{h}>'
            link = f'<p class="more"><a href="{slug}.html"{idattr}>{esc(word)}</a></p>'
        elif mode == "describedby":
            head = f'<{h} id="{hid}">{esc(t)}</{h}>'
            link = f'<p class="more"><a href="{slug}.html"{idattr} aria-describedby="{hid}">{esc(word)}</a></p>'
        elif mode == "sr-text":
            head = f'<{h}>{esc(t)}</{h}>'
            link = f'<p class="more"><a href="{slug}.html"{idattr}>{esc(word)}<span class="visually-hidden">: {esc(t)}</span></a></p>'
        elif mode == "title-attr":
            head = f'<{h}>{esc(t)}</{h}>'
            link = f'<p class="more"><a href="{slug}.html"{idattr} title="{esc(t)}">{esc(word)}</a></p>'
        else:  # title-link
            head = f'<{h}><a href="{slug}.html"{idattr}>{esc(t)}</a></{h}>'
            link = ""
        cards.append(f'<article class="news-card">{img}<div class="body"><p class="date muted">{date_str(lang, 5 + 3 * i)}</p>'
                     f'{head}<p>{esc(teaser)}</p>{link}</div></article>')
    main = f'<h1>{NEWS_H[lang]}</h1>\n<div class="news-grid">\n' + "\n".join(cards) + "\n</div>"
    target = f"#news-link-{tgt_i + 1}"
    topic = items[tgt_i][0]
    notes = {
        "heading-only": f"Link text '{word}' is generic; the card heading '{topic}' is outside the link's paragraph, so it is not programmatic context (H80 is advisory only).",
        "describedby": f"Generic '{word}' but aria-describedby points to the card heading '{topic}', which is programmatic link context.",
        "sr-text": f"Visible text '{word}' is completed by visually hidden text naming '{topic}' (C7); the accessible name is descriptive.",
        "title-attr": f"Generic '{word}'; the purpose is only given in the title attribute ('{topic}'), which H33 accepts but is not reliably exposed and is not ACT link context.",
        "title-link": f"The card heading itself is the link; its text '{topic}' describes the purpose.",
    }[mode]
    css = CARD_CSS + (SR_CSS if mode == "sr-text" else "")
    return main, target, notes, ("hard" if mode in ("heading-only", "describedby", "title-attr") else "medium"), css


def b_teaser_list(rng, lang, *, mode):
    """Teaser paragraphs without headings, link in separate block (F1), or in same paragraph (T2)."""
    items = sample(rng, NEWS[lang], 3)
    word = pick(rng, GENERIC[lang])
    tgt_i = rng.randrange(3)
    blocks = []
    for i, (t, teaser, slug, _) in enumerate(items):
        lid = f' id="teaser-{i + 1}"'
        if mode == "separate-p":
            blocks.append(f'<div class="teaser"><p>{esc(teaser)}</p><p><a href="{slug}.html"{lid}>{esc(word)}</a></p></div>')
        elif mode == "separate-div":
            blocks.append(f'<div class="teaser" style="display:flex;gap:12px;align-items:baseline;justify-content:space-between">'
                          f'<div>{esc(teaser)}</div><div><a href="{slug}.html"{lid}>{esc(word)}</a></div></div>')
        else:  # same-p
            blocks.append(f'<p class="teaser">{esc(teaser)} <a href="{slug}.html"{lid}>{esc(word)}</a></p>')
    box = pick(rng, ["box", ""])
    main = (f'<h1>{NEWS_H[lang]}</h1>\n<section class="{box}">' + "\n".join(blocks) + "</section>")
    teaser = items[tgt_i][1]
    if mode == "same-p":
        notes = f"Generic '{word}' is inside the same paragraph as the teaser ('{teaser[:50]}…'), which is programmatic context (H78)."
        diff = "medium"
    else:
        notes = f"Generic '{word}' sits in its own block; the teaser ('{teaser[:50]}…') is a separate block, so the purpose is only visually implied (F63)."
        diff = "medium" if mode == "separate-p" else "hard"
    return main, f"#teaser-{tgt_i + 1}", notes, diff, ""


def b_figure_link(rng, lang):
    """Figure with caption; generic link below the figure (F1)."""
    t, teaser, slug, kind = pick(rng, NEWS[lang])
    word = pick(rng, GENERIC[lang])
    src = asset(f"scene-{kind}-fig", scene(kind, w=560, h=300, seed=7))
    cap = {"de": "Bild: Gemeinde", "fr": "Photo : commune", "it": "Foto: Comune", "en": "Photo: tourist office"}[lang]
    main = (f'<h1>{NEWS_H[lang]}</h1><figure style="margin:0"><img src="{src}" alt="{esc(t)}">'
            f'<figcaption class="muted">{esc(teaser)} {cap}</figcaption></figure>'
            f'<div class="actions" style="margin-top:8px"><a href="{slug}.html" id="figure-more" class="button-like">{esc(word)}</a></div>')
    notes = f"Generic '{word}' in its own container; the photo alt and caption are not programmatic link context (F63)."
    return main, "#figure-more", notes, "hard", ".button-like{display:inline-block;padding:6px 14px;border:2px solid currentColor;border-radius:6px;text-decoration:none;font-weight:600}"


def b_course_table(rng, lang, *, with_th):
    """Table of courses with identical 'register' links (F2 without headers, T3 with th)."""
    rows = COURSES[lang]
    k = len(rows)
    tgt_i = rng.randrange(k)
    reg = REGISTER[lang]
    hdr = TH[lang]
    trs = []
    for i, (name, date, place, slug) in enumerate(rows):
        first = f'<th scope="row">{esc(name)}</th>' if with_th else f"<td>{esc(name)}</td>"
        trs.append(f'<tr>{first}<td>{esc(date)}</td><td>{esc(place)}</td>'
                   f'<td><a href="anmeldung-{slug}.html" id="reg-{i + 1}">{esc(reg)}</a></td></tr>')
    if with_th:
        head = "<thead><tr>" + "".join(f'<th scope="col">{esc(x)}</th>' for x in hdr) + "</tr></thead>"
    else:
        head = ('<thead><tr>' + "".join(f'<td class="th-like"><strong>{esc(x)}</strong></td>' for x in hdr) + "</tr></thead>")
    main = f'<h1>{COURSE_H[lang]}</h1><table>{head}<tbody>{"".join(trs)}</tbody></table>'
    if with_th:
        notes = f"Identical '{reg}' links, but each cell is associated with a row header naming the course (H79)."
    else:
        notes = f"Identical '{reg}' links to different courses; the course name is in a plain td (no th/headers), so no programmatic context distinguishes them."
    return main, f"#reg-{tgt_i + 1}", notes, ("hard" if not with_th else "medium"), ".th-like{background:#f1f2f5}"


def b_download_rows(rng, lang, *, mode):
    """Download list. mode: 'split-div' (F2), 'li-topic' (T2), 'nested' (T2, H81), 'descriptive' (P1)."""
    docs = sample(rng, DOCS[lang], 3)
    tgt_i = rng.randrange(3)
    dl = DOWNLOAD[lang]
    if mode == "split-div":
        rows = "".join(f'<div class="file-row" style="display:flex;justify-content:space-between;border-bottom:1px solid #d4d7de;padding:8px 0">'
                       f'<div class="file-name">{esc(t)} <span class="muted">({esc(meta)})</span></div>'
                       f'<div class="file-action"><a href="{f}" id="dl-{i + 1}">{esc(dl)}</a></div></div>'
                       for i, (t, f, meta) in enumerate(docs))
        notes = f"Three identical '{dl}' links; each file name is in a sibling div, not in the link's block, list item or cell (F63)."
        diff = "hard"
    elif mode == "li-topic":
        rows = "<ul>" + "".join(f'<li>{esc(t)} ({esc(meta)}): <a href="{f}" id="dl-{i + 1}">{esc(dl)}</a></li>'
                                for i, (t, f, meta) in enumerate(docs)) + "</ul>"
        notes = f"Identical '{dl}' links, each inside a list item that names the document (H77)."
        diff = "medium"
    elif mode == "nested":
        rows = "<ul>" + "".join(f'<li>{esc(t)}<ul><li><a href="{f}" id="dl-{i + 1}">PDF</a> ({esc(meta)})</li>'
                                f'<li><a href="{f.replace(".pdf", ".docx")}">Word</a></li></ul></li>'
                                for i, (t, f, meta) in enumerate(docs)) + "</ul>"
        notes = "Link text 'PDF' is generic, but the parent list item names the document (nested list, H81)."
        diff = "hard"
    else:  # descriptive
        verb = {"de": "herunterladen", "fr": "télécharger", "it": "scaricare", "en": "download"}[lang]
        rows = "<ul>" + "".join(f'<li><a href="{f}" id="dl-{i + 1}">{esc(t)} {verb} ({esc(meta)})</a></li>'
                                for i, (t, f, meta) in enumerate(docs)) + "</ul>"
        notes = "Link text names the document, the action and the file format (G91/H30)."
        diff = "easy"
    main = f"<h1>{DOCS_H[lang]}</h1>{rows}"
    return main, f"#dl-{tgt_i + 1}", notes, diff, ""


SENTENCE_TPL = {
    "de": [("Alle Abfuhrdaten für das nächste Jahr finden Sie im neuen Abfallkalender – {a}.", "Abfallkalender"),
           ("Wer eine Parkkarte für die Blaue Zone braucht, kann sie {a} online bestellen.", "Parkkarte"),
           ("Das Anmeldeformular für den Mittagstisch können Sie {a} herunterladen.", "Mittagstisch")],
    "fr": [("Toutes les dates de ramassage de l'année prochaine figurent dans le nouveau calendrier des déchets – {a}.", "calendrier des déchets"),
           ("Les macarons de stationnement pour la zone bleue peuvent être commandés en ligne {a}.", "macaron"),
           ("Le formulaire d'inscription à la cantine scolaire peut être téléchargé {a}.", "cantine")],
    "it": [("Tutte le date di raccolta del prossimo anno sono riportate nel nuovo calendario dei rifiuti – {a}.", "calendario"),
           ("I contrassegni per la zona blu si possono ordinare online {a}.", "contrassegno"),
           ("Il modulo d'iscrizione alla mensa scolastica si può scaricare {a}.", "mensa")],
    "en": [("All bus departures for the winter season are listed in the new timetable – {a}.", "timetable")],
}


def b_sentence(rng, lang):
    """Generic link inside an explanatory sentence (T1, G53)."""
    tpl, topic = pick(rng, SENTENCE_TPL[lang])
    word = {"de": pick(rng, ["hier", "mehr"]), "fr": pick(rng, ["ici", "plus"]),
            "it": pick(rng, ["qui", "di più"]), "en": pick(rng, ["here", "more"])}[lang]
    a = f'<a href="{slug(topic)}.html" id="inline-link">{esc(word)}</a>'
    s = esc(tpl).replace("{a}", a)
    intro = {"de": "Service", "fr": "Prestations", "it": "Servizi", "en": "Service"}[lang]
    other = pick(rng, NEWS[lang])
    main = (f"<h1>{intro}</h1><p>{s}</p>"
            f"<p>{esc(other[1])} <a href=\"{other[2]}.html\">{esc(other[0])}</a></p>")
    notes = f"Generic '{word}' but the enclosing sentence states the purpose ({topic}); sentence context is sufficient (G53)."
    return main, "#inline-link", notes, "medium", ""


def b_aria_label(rng, lang, *, mode):
    """mode 'good': visible 'Mehr' + aria-label 'Mehr zu …' (T4); 'generic-override': descriptive visible
    text overridden by a generic aria-label (F4); 'wrong-override': aria-label names another target (F4)."""
    t, teaser, slug_, kind = pick(rng, NEWS[lang])
    word = GENERIC[lang][0]
    if mode == "good":
        lab = {"de": f"{word} zu: {t}", "fr": f"{word} sur : {t}", "it": f"{word} su: {t}", "en": f"{word} about: {t}"}[lang]
        link = f'<a href="{slug_}.html" id="promo-link" aria-label="{esc(lab)}">{esc(word)}</a>'
        notes = f"Visible '{word}' with aria-label '{lab}' (ARIA8); the accessible name describes the purpose and starts with the visible text."
        diff = "medium"
    elif mode == "generic-override":
        lab = pick(rng, ["Link", DOWNLOAD[lang], word])
        link = f'<a href="{slug_}.html" id="promo-link" aria-label="{esc(lab)}">{esc(t)}</a>'
        notes = f"Visible text '{t}' is descriptive, but aria-label='{lab}' replaces it; the accessible name is generic and the block has no other context."
        diff = "hard"
    else:
        other = pick(rng, [n for n in NEWS[lang] if n[0] != t])
        link = f'<a href="{slug_}.html" id="promo-link" aria-label="{esc(other[0])}">{esc(t)}</a>'
        notes = f"aria-label names a different topic ('{other[0]}') than the link target ('{t}'); the accessible name misdescribes the purpose."
        diff = "hard"
    src = asset(f"scene-{kind}-promo", scene(kind, w=520, h=220, seed=11))
    main = (f'<h1>{NEWS_H[lang]}</h1><div class="promo box" style="display:grid;gap:12px">'
            f'<img src="{src}" alt="">'
            f'<div class="promo-cta">{link}</div></div>')
    return main, "#promo-link", notes, diff, ""


def b_icon_link(rng, lang, *, mode):
    """mode: 'empty-alt' (F3, F89 in a paragraph with context), 'filename-alt' (F3), 'good-alt' (P1),
    'icon-text' (P1: decorative icon + text)."""
    doc_t, f, meta = pick(rng, DOCS[lang])
    icon = asset("pic-download-dark", pictogram("download", color="#1d2327", size=28))
    if mode == "empty-alt":
        body = f'<p>{esc(doc_t)} ({esc(meta)}) <a href="{f}" id="file-link"><img src="{icon}" alt="" width="28" height="28"></a></p>'
        notes = "Image-only link with alt=\"\": the link has no accessible name at all, so its purpose cannot be determined even though the paragraph names the document (F89)."
        diff = "medium"
    elif mode == "filename-alt":
        body = f'<p class="file">{esc(doc_t)}</p><p><a href="{f}" id="file-link"><img src="{icon}" alt="icon_download_28px.svg" width="28" height="28"></a></p>'
        notes = "Image-only link whose alt is a file name; the document name is in a different paragraph, so the purpose is not determinable."
        diff = "easy"
    elif mode == "good-alt":
        verb = {"de": "herunterladen", "fr": "télécharger", "it": "scaricare", "en": "download"}[lang]
        body = f'<p class="file">{esc(doc_t)} <span class="muted">({esc(meta)})</span></p><p><a href="{f}" id="file-link"><img src="{icon}" alt="{esc(doc_t)} {verb}" width="28" height="28"></a></p>'
        notes = "Image-only link whose alt names the document and the action (H30)."
        diff = "medium"
    else:
        body = f'<p><a href="{f}" id="file-link"><img src="{icon}" alt="" width="20" height="20"> {esc(doc_t)} ({esc(meta)})</a></p>'
        notes = "Decorative icon with alt=\"\" plus descriptive link text naming the document."
        diff = "easy"
    main = f"<h1>{DOCS_H[lang]}</h1>{body}"
    return main, "#file-link", notes, diff, ""


def b_button_link(rng, lang):
    """Descriptive call-to-action link (P1)."""
    txt = {"de": ["Wohnsitzbestätigung online bestellen", "Hundekontrollmarke beantragen", "Parkkarte Blaue Zone bestellen"],
           "fr": ["Commander une attestation de domicile en ligne", "Demander une marque de contrôle pour chien", "Commander un macaron zone bleue"],
           "it": ["Ordinare online un certificato di domicilio", "Richiedere la marca di controllo per cani", "Ordinare il contrassegno zona blu"],
           "en": ["Book a guided glacier walk", "Download the winter bus timetable"]}[lang]
    t = pick(rng, txt)
    intro = {"de": "Online-Schalter", "fr": "Guichet en ligne", "it": "Sportello online", "en": "Plan your visit"}[lang]
    lead = {"de": "Viele Dienstleistungen der Einwohnerdienste können Sie rund um die Uhr online erledigen.",
            "fr": "De nombreuses prestations du contrôle des habitants sont disponibles en ligne 24 heures sur 24.",
            "it": "Molti servizi del controllo abitanti sono disponibili online 24 ore su 24.",
            "en": "Most bookings can be made online at any time."}[lang]
    main = (f'<h1>{intro}</h1><p>{esc(lead)}</p><p><a class="cta" href="{slug(t)}.html" id="cta">{esc(t)}</a></p>')
    return main, "#cta", f"Link text '{t}' fully describes the purpose (G91).", "easy", \
        ".cta{display:inline-block;padding:10px 18px;border-radius:8px;background:#0b4f6c;color:#ffffff;text-decoration:none;font-weight:600}"


AMBIG = {
    "de": ("Spezialitäten der Region", "Zu den bekanntesten Erzeugnissen des Tals gehört die {a}, die seit über hundert Jahren in kleinen Familienbetrieben hergestellt wird.", "Beispielwiler Nusstorte"),
    "fr": ("Spécialités régionales", "Parmi les produits les plus connus de la vallée figure la {a}, fabriquée depuis plus d'un siècle par de petites entreprises familiales.", "taillaule de Valfictif"),
    "it": ("Specialità regionali", "Tra i prodotti più noti della valle c'è la {a}, preparata da oltre un secolo in piccole aziende familiari.", "torta di noci di Esempiano"),
}


def b_ambiguous(rng, lang):
    """Exception: purpose ambiguous to users in general (T5)."""
    h, tpl, word = AMBIG[lang]
    a = f'<a href="{slug(word)}.html" id="term-link">{esc(word)}</a>'
    main = f"<h1>{esc(h)}</h1><p>{esc(tpl).replace('{a}', a)}</p>"
    notes = ("The link on the product name could lead to a recipe, a shop or a history page; the purpose is ambiguous "
             "to all users, which is the exception of 2.4.4 (Understanding 2.4.4, 'guava' example).")
    return main, "#term-link", notes, "hard", ""


def b_no_href(rng, lang):
    """<a> without href (no link role) and no other links: inapplicable (N1)."""
    t, teaser, slug_, kind = pick(rng, NEWS[lang])
    word = GENERIC[lang][0]
    main = (f'<h1>{esc(t)}</h1><p>{esc(teaser)}</p>'
            f'<p><a id="more-anchor" class="more-anchor">{esc(word)}</a></p>')
    notes = "The only <a> element has no href, so it is not a link (no link role) and there are no other links: 2.4.4 does not apply."
    return main, "#more-anchor", notes, "hard", ".more-anchor{color:#0b5394;text-decoration:underline}"


# --------------------------------------------------------------------------- plan
PLAN = [
    # (rule, expected, builder, kwargs, trap, alt)
    ("F1", "failed", b_teaser_list, {"mode": "separate-p"}, False, None),
    ("F1", "failed", b_teaser_list, {"mode": "separate-p"}, False, None),
    ("F1", "failed", b_teaser_list, {"mode": "separate-div"}, False, None),
    ("F1", "failed", b_figure_link, {}, False, None),
    ("F1", "failed", b_figure_link, {}, False, None),
    ("F2", "failed", b_course_table, {"with_th": False}, False, None),
    ("F2", "failed", b_course_table, {"with_th": False}, False, None),
    ("F2", "failed", b_download_rows, {"mode": "split-div"}, False, None),
    ("F2", "failed", b_download_rows, {"mode": "split-div"}, False, None),
    ("F3", "failed", b_icon_link, {"mode": "empty-alt"}, False, None),
    ("F3", "failed", b_icon_link, {"mode": "empty-alt"}, False, None),
    ("F3", "failed", b_icon_link, {"mode": "filename-alt"}, False, None),
    ("F3", "failed", b_icon_link, {"mode": "filename-alt"}, False, None),
    ("F4", "failed", b_aria_label, {"mode": "generic-override"}, False, None),
    ("F4", "failed", b_aria_label, {"mode": "generic-override"}, False, None),
    ("F4", "failed", b_aria_label, {"mode": "wrong-override"}, False, None),
    ("P1", "passed", b_download_rows, {"mode": "descriptive"}, False, None),
    ("P1", "passed", b_download_rows, {"mode": "descriptive"}, False, None),
    ("P1", "passed", b_icon_link, {"mode": "good-alt"}, False, None),
    ("P1", "passed", b_icon_link, {"mode": "icon-text"}, False, None),
    ("P1", "passed", b_button_link, {}, False, None),
    ("P1", "passed", b_button_link, {}, False, None),
    ("P1", "passed", b_card_grid, {"mode": "title-link"}, False, None),
    ("T1", "passed", b_sentence, {}, True, None),
    ("T1", "passed", b_sentence, {}, True, None),
    ("T2", "passed", b_teaser_list, {"mode": "same-p"}, True, None),
    ("T2", "passed", b_download_rows, {"mode": "li-topic"}, True, None),
    ("T2", "passed", b_download_rows, {"mode": "nested"}, True, None),
    ("T3", "passed", b_course_table, {"with_th": True}, True, None),
    ("T3", "passed", b_course_table, {"with_th": True}, True, None),
    ("T4", "passed", b_card_grid, {"mode": "describedby"}, True, None),
    ("T4", "passed", b_card_grid, {"mode": "sr-text"}, True, None),
    ("T4", "passed", b_aria_label, {"mode": "good"}, True, None),
    ("T5", "passed", b_ambiguous, {}, True, None),
    ("N1", "inapplicable", b_no_href, {}, True, None),
    ("C1", "cantTell", b_card_grid, {"mode": "heading-only"}, False, "failed"),
    ("C1", "cantTell", b_card_grid, {"mode": "heading-only"}, False, "failed"),
    ("C1", "cantTell", b_card_grid, {"mode": "heading-only"}, False, "failed"),
    ("C1", "cantTell", b_card_grid, {"mode": "heading-only"}, False, "failed"),
    ("C2", "cantTell", b_card_grid, {"mode": "title-attr"}, False, "failed"),
]


def assign_langs(rng, plan):
    """Deterministic language assignment: each rule group spread over de/fr/it, EN sparingly."""
    langs = []
    cycle = ["de", "fr", "it"]
    offset = 0
    groups = {}
    for i, row in enumerate(plan):
        groups.setdefault(row[0], []).append(i)
    out = [None] * len(plan)
    for rule, idxs in groups.items():
        start = rng.randrange(3)
        for j, i in enumerate(idxs):
            out[i] = cycle[(start + j) % 3]
    # a few EN pages where the builder supports it (tourism context)
    en_ok = [i for i, r in enumerate(plan) if r[2] in (b_teaser_list, b_course_table, b_button_link) and r[0] in ("F1", "T3", "P1", "F2")]
    for i in sorted(rng.sample(en_ok, 2)):
        out[i] = "en"
    return out


def build(rng):
    plan = list(PLAN)
    langs = assign_langs(rng, plan)
    cases = []
    for (rule, expected, fn, kw, trap, alt), lang in zip(plan, langs):
        main, target, notes, diff, css = fn(rng, lang, **kw)
        org = org_for(rng, lang)
        chrome = rng.random() < 0.8 and rule != "N1"
        theme = pick_theme(rng)
        section = {"de": pick(rng, ["Aktuelles", "Verwaltung", "Dienstleistungen"]),
                   "fr": pick(rng, ["Actualités", "Administration", "Prestations"]),
                   "it": pick(rng, ["Attualità", "Amministrazione", "Servizi"]),
                   "en": pick(rng, ["News", "Plan your visit"])}[lang]
        body = wrap(lang, org, main, chrome=chrome)
        html = page(SITE_LANG_TAG[lang] if rng.random() < 0.7 else lang, title_for(lang, section, org), body,
                    theme=theme, css=css)
        # template family = builder x language: cases built from the same content pool stay in one split
        cases.append(Case(CRITERION, lang, expected, html=html, target=target, rule=f"{CRITERION}/{rule}",
                          notes=notes, trap=trap, alt_expected=alt, difficulty=diff,
                          template=f"{fn.__name__[2:]}-{lang}"))
    return cases
