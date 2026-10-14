"""3.2.4 Consistent Identification — mini sites with repeated functional components (target None)."""
from __future__ import annotations

from common import *  # noqa: F401,F403
from common import Case, asset, esc, pick, pick_theme, pictogram
from _operable_util import (P, UI, brand, footer_simple, get_page, href, main_content, nav_block, search_box,
                            search_index, service_pages, site_by_kind, site_doc, skip_link, title_of)

CRITERION = "3.2.4"

CSS = (".pagetools{display:flex;justify-content:flex-end;gap:8px;margin-bottom:8px}"
       ".icon-btn{display:inline-flex;align-items:center;justify-content:center;padding:6px;line-height:0}"
       ".pagetools .icon-btn{background:#ffffff;border:1px solid #6b7280}"
       ".home{display:inline-flex;align-items:center;gap:8px;text-decoration:none}"
       ".pager{list-style:none;display:flex;gap:10px;align-items:center;padding:0}"
       ".news-list{list-style:none;padding:0}.news-list li{border-bottom:1px solid #c9d3d8;padding:8px 0}"
       ".bigsearch{background:#e8f1f5;padding:16px;border-radius:10px;margin:16px 0}.bigsearch .search label{position:static;width:auto;height:auto;clip:auto;font-weight:600}")


def ico(name, color):
    return asset(f"sym-{name}-{color.lstrip('#')}", pictogram(name, color=color, size=24))


def render(site, theme, layout, pg, *, items, tools="", page_tools="", foot_links=None, lang_switch="", extra_main="",
           sep=" – ", title=None, brand_html=None, main_html=None):
    lang = site["lang"]
    ui = UI[lang]
    cur = href(pg["slug"])
    cls = {"top": "site-nav", "side": "side-nav", "band": "band"}[layout]
    nav = nav_block(items, ui["nav"], cls=cls, current=cur)
    bh = brand_html or brand(site["org"])
    tl = f'<div class="tools">{tools}</div>' if tools else ""
    top = [skip_link(lang)]
    aside = None
    if layout == "top":
        top.append(f'<header class="site-header">{bh}{lang_switch}{nav}{tl}</header>')
    elif layout == "band":
        top += [f'<header class="site-header">{bh}{lang_switch}{tl}</header>', nav]
    else:
        top.append(f'<header class="site-header">{bh}{lang_switch}{tl}</header>')
        aside = nav
    fl = ""
    if foot_links:
        fl = (f'<nav class="foot-links" aria-label="{esc(ui["footer_nav"])}"><ul>'
              + "".join(f'<li><a href="{esc(h)}">{esc(lb)}</a></li>' for lb, h in foot_links) + "</ul></nav>")
    main = (f'<div class="pagetools">{page_tools}</div>' if page_tools else "")
    main += main_html if main_html is not None else main_content(pg, extra_main)
    return site_doc(lang, title or title_of(pg, site, sep), theme, top=top, main=main, aside=aside,
                    bottom=[footer_simple(site, fl)], css=CSS)


def items_of(pages):
    return [(p["nav"], href(p["slug"])) for p in pages]


def _lay(rng):
    return pick(rng, ("top", "side", "band"))


def _sep(rng):
    return pick(rng, (" – ", " | ", " · "))


def build(rng):
    cases = []

    def add(lang, expected, pages, rule, notes, *, trap=False, alt=None, diff="medium"):
        cases.append(Case(CRITERION, lang, expected, pages=pages, target=None, rule=rule, notes=notes,
                          trap=trap, alt_expected=alt, difficulty=diff))

    def make(site, pgs, *, nav_pgs=None, per_page=None, layout=None, **kw):
        theme, lay, sep = pick_theme(rng), layout or _lay(rng), _sep(rng)
        nav_pgs = nav_pgs or pgs
        out = {}
        for pg in pgs:
            opts = dict(kw)
            opts.update((per_page or {}).get(pg["slug"], {}))
            out[href(pg["slug"])] = render(site, theme, lay, pg, items=items_of(nav_pgs), sep=sep, **opts)
        return out

    # ---------------- F1: different visible label -----------------
    s = site_by_kind("de", "municipality")
    pgs = [get_page(s, x) for x in ("index", "abfall", "steuern", "freizeit")]
    idx = search_index(pgs)
    pages = make(s, pgs, tools=search_box("de", idx, fid="suche"),
                 per_page={"steuern": {"tools": search_box("de", idx, fid="suche", button="Finden")}})
    add("de", "failed", pages, "3.2.4/F1",
        "The site search button is labelled 'Suchen' on every page except steuern.html, where the same search is labelled 'Finden'.",
        diff="easy")

    s = site_by_kind("it", "tourism")
    pgs = [get_page(s, x) for x in ("index", "escursioni", "alloggi", "grotti")]
    idx = search_index(pgs)
    pages = make(s, pgs, tools=search_box("it", idx, fid="ricerca"),
                 per_page={"alloggi": {"tools": search_box("it", idx, fid="ricerca", button="Trova")}})
    add("it", "failed", pages, "3.2.4/F1",
        "The same site search is labelled 'Cerca' on three pages and 'Trova' on alloggi.html.", diff="easy")

    # ---------------- F2: same look, different accessible name -----------------
    s = site_by_kind("de", "library")
    pgs = [get_page(s, x) for x in ("index", "oeffnungszeiten", "ausleihe", "veranstaltungen")]
    idx = search_index(pgs)
    pages = make(s, pgs, tools=search_box("de", idx, fid="suche"),
                 per_page={"ausleihe": {"tools": search_box("de", idx, fid="suche",
                                                            button_html='<button type="submit" aria-label="Finden">Suchen</button>')}})
    add("de", "failed", pages, "3.2.4/F2",
        "The button looks identical everywhere ('Suchen'), but on ausleihe.html its accessible name is overridden with aria-label 'Finden', so assistive technology announces a different name.",
        diff="hard")

    s = site_by_kind("fr", "utility")
    pgs = [get_page(s, x) for x in ("index", "qualite", "tarifs", "pannes")]
    home = ico("home", "#ffffff")

    def bh(alt):
        return (f'<a class="home" href="index.html"><img src="{home}" alt="{esc(alt)}" width="24" height="24"></a>'
                f'<span class="site-name">{esc(s["org"])}</span>')
    pages = make(s, pgs, brand_html=bh("Accueil"), per_page={"qualite": {"brand_html": bh("Page principale")}})
    add("fr", "failed", pages, "3.2.4/F2",
        "The house icon linking to the home page has alt 'Accueil' on every page except qualite.html, where the same icon and link are named 'Page principale'.",
        diff="medium")

    # ---------------- F3: same link, different label -----------------
    s = site_by_kind("it", "municipality")
    pgs = [get_page(s, x) for x in ("index", "rifiuti", "imposte", "edilizia")]
    contatti = service_pages(s)[3]
    allp = pgs + [contatti]
    pages = make(s, allp, nav_pgs=pgs, tools='<a href="contatti.html">Contatti</a>',
                 per_page={"edilizia": {"tools": '<a href="contatti.html">Scriveteci</a>'}})
    add("it", "failed", pages, "3.2.4/F3",
        "The header link to contatti.html reads 'Contatti' on all pages except edilizia.html, where the same link reads 'Scriveteci'.",
        diff="medium")

    s = site_by_kind("fr", "school")
    pgs = [get_page(s, x) for x in ("index", "horaires", "vacances", "parascolaire")]
    nl = P("newsletter", "Newsletter", "Lettre d'information", [
        "Recevez chaque mois les nouvelles de l'école par courriel.",
        f"Pour vous inscrire, écrivez à {s['mail']} avec l'objet « Newsletter »."])
    allp = pgs + [nl]
    pages = make(s, allp, nav_pgs=pgs, foot_links=[("Newsletter", "newsletter.html")],
                 per_page={"vacances": {"foot_links": [("Restez informés", "newsletter.html")]}})
    add("fr", "failed", pages, "3.2.4/F3",
        "The footer link to newsletter.html is called 'Newsletter' everywhere but 'Restez informés' on vacances.html.", diff="medium")

    # ---------------- P1: consistent -----------------
    s = site_by_kind("fr", "library")
    pgs = [get_page(s, x) for x in ("index", "horaires", "collections", "animations")]
    idx = search_index(pgs)
    pages = make(s, pgs, tools=search_box("fr", idx, fid="recherche"),
                 page_tools='<button type="button" onclick="window.print()">Imprimer la page</button>')
    add("fr", "passed", pages, "3.2.4/P1",
        "Search ('Rechercher') and print ('Imprimer la page') are labelled identically on all four pages.", diff="easy")

    s = site_by_kind("it", "transport")
    pgs = [get_page(s, x) for x in ("index", "orari", "biglietti", "fermate")]
    contatti = service_pages(s)[3]
    pr = ico("printer", "#1d2327")
    pages = make(s, pgs + [contatti], nav_pgs=pgs, tools='<a href="contatti.html">Contatti</a>',
                 page_tools=(f'<button type="button" class="icon-btn" aria-label="Stampa questa pagina" onclick="window.print()">'
                             f'<img src="{pr}" alt="" width="24" height="24"></button>'))
    add("it", "passed", pages, "3.2.4/P1",
        "The printer icon button is named 'Stampa questa pagina' and the header link 'Contatti' on every page.", diff="easy")

    # ---------------- T1: pagination following one pattern -----------------
    s = site_by_kind("de", "transport")
    news = [
        [("Neuer Fahrplan ab 13. Dezember", "Linie 3 fährt neu bis zum Spital Mustersee."),
         ("Nachtbus N1 auch an Silvester", "Zusätzliche Kurse um 3.15 und 4.30 Uhr."),
         ("Baustelle Kirchweg", "Vom 2. bis 20. November wird Linie 2 umgeleitet.")],
        [("Neue Busse für Linie 1", "Vier Elektrobusse ersetzen ab Januar die alten Dieselbusse."),
         ("Fundbüro am 8. Dezember geschlossen", "Ab 9. Dezember gelten wieder die üblichen Öffnungszeiten."),
         ("Umfrage zur Kundenzufriedenheit", "Wir danken den 1240 Fahrgästen, die mitgemacht haben.")],
        [("Haltestelle Seeweg barrierefrei", "Die Haltekante wurde auf 22 cm erhöht."),
         ("Tageskarte neu in der App", "Die Tageskarte kostet weiterhin CHF 8.40."),
         ("Sommerfahrplan 2026", "Vom 6. Juli bis 16. August fahren die Linien 4 und 5 im 30-Minuten-Takt.")]]
    files = ["index.html", "aktuell-2.html", "aktuell-3.html"]
    la, ra = ico("arrow-left", "#0b5394"), ico("arrow-right", "#0b5394")
    pgs = []
    for k in range(3):
        pgs.append(P("index" if k == 0 else f"aktuell-{k + 1}", "Aktuell" if k == 0 else f"Aktuell, Seite {k + 1}",
                     "Aktuell", ["Neuigkeiten der Beispielwiler Verkehrsbetriebe."]))
    fp = get_page(s, "fahrplan")
    theme, lay, sep = pick_theme(rng), _lay(rng), _sep(rng)
    nav_items = [("Aktuell", "index.html"), (fp["nav"], "fahrplan.html")]
    pages = {}
    for k, pg in enumerate(pgs):
        lis = []
        if k > 0:
            lis.append(f'<li><a href="{files[k - 1]}"><img src="{la}" alt="Zurück zu Seite {k}" width="24" height="24"></a></li>')
        for j in range(3):
            if j == k:
                lis.append(f'<li><span aria-current="page">Seite {j + 1}</span></li>')
            else:
                lis.append(f'<li><a href="{files[j]}">Seite {j + 1}</a></li>')
        if k < 2:
            lis.append(f'<li><a href="{files[k + 1]}"><img src="{ra}" alt="Weiter zu Seite {k + 2}" width="24" height="24"></a></li>')
        body = ("<h1>Aktuell</h1><ul class=\"news-list\">"
                + "".join(f"<li><h2>{esc(t)}</h2><p>{esc(x)}</p></li>" for t, x in news[k])
                + f'</ul><nav aria-label="Seiten"><ul class="pager">{"".join(lis)}</ul></nav>')
        pages[files[k]] = render(s, theme, lay, pg, items=nav_items, sep=sep, main_html=body,
                                 title=f"Aktuell, Seite {k + 1}{sep}{s['org']}")
    pages["fahrplan.html"] = render(s, theme, lay, fp, items=nav_items, sep=sep)
    add("de", "passed", pages, "3.2.4/T1",
        "The pagination arrows are named 'Weiter zu Seite 2' on page 1 and 'Weiter zu Seite 3' on page 2: the names differ but follow one consistent pattern (Understanding 'page 4/5' example).",
        trap=True, diff="hard")

    # ---------------- T2: same icon, different functions -----------------
    s = site_by_kind("it", "utility")
    pr = ico("printer", "#1d2327")
    fat = P("fatture", "Le mie fatture", "Fattura 2026-1043", ["Periodo: 1° luglio – 31 dicembre 2026."],
            ["Consumo: 64 m³ × CHF 1.40 = CHF 89.60", "Tassa base: CHF 37.50", "Totale: CHF 127.10, scadenza 31.01.2027"])
    pag = P("pagamento", "Pagamento", "Pagamento ricevuto", ["Abbiamo ricevuto il vostro pagamento di CHF 127.10 il 18.01.2027. Grazie!"],
            ["Riferimento: 2026-1043", "Modalità: bonifico bancario"])
    pgs = [get_page(s, "index"), get_page(s, "tariffe"), fat, pag]

    def ptool(label):
        return (f'<button type="button" class="icon-btn" aria-label="{esc(label)}" onclick="window.print()">'
                f'<img src="{pr}" alt="" width="24" height="24"></button>')
    idx = search_index(pgs)
    pages = make(s, pgs, tools=search_box("it", idx, fid="ricerca"),
                 per_page={"fatture": {"page_tools": ptool("Stampa la fattura")},
                           "pagamento": {"page_tools": ptool("Stampa la ricevuta")}})
    add("it", "passed", pages, "3.2.4/T2",
        "The same printer icon prints an invoice on fatture.html and a payment receipt on pagamento.html; different functions may carry different names, while the search is labelled 'Cerca' everywhere.",
        trap=True, diff="hard")

    # ---------------- T3: language versions -----------------
    s = site_by_kind("fr", "tourism")
    fr_p = [get_page(s, x) for x in ("index", "randonnees", "hebergement")]
    de_p = [P("index", "Startseite", "Willkommen im Val-Modèle", [
                "Zwischen See und Bergen bietet das Val-Modèle 120 km markierte Wege und eine mittelalterliche Altstadt."]),
            P("wandern", "Wandern", "Wandern", ["Alle Routen beginnen auf der Place du Marché."],
              ["Seerundweg: 2 h 30, leicht", "Gratweg: 5 h, schwierig", "Mühlenweg: 1 h 15, leicht"]),
            P("unterkuenfte", "Unterkünfte", "Unterkünfte", ["Hotels, Gästezimmer und ein Campingplatz: 18 Betriebe empfangen Sie das ganze Jahr."])]
    theme, lay, sep = pick_theme(rng), _lay(rng), _sep(rng)
    pages = {}
    sw_fr = ('<nav class="lang-switch" aria-label="Langue"><ul><li><span aria-current="true">FR</span></li>'
             '<li><a href="de/index.html" lang="de" hreflang="de">DE</a></li></ul></nav>')
    for pg in fr_p:
        pages[href(pg["slug"])] = render(s, theme, lay, pg, items=items_of(fr_p), sep=sep, lang_switch=sw_fr,
                                         tools=search_box("fr", search_index(fr_p), fid="recherche"))
    s_de = dict(s, lang="de", org="Tourismusbüro Val-Modèle")
    sw_de = ('<nav class="lang-switch" aria-label="Sprache"><ul><li><a href="../index.html" lang="fr" hreflang="fr">FR</a></li>'
             '<li><span aria-current="true">DE</span></li></ul></nav>')
    for pg in de_p:
        pages["de/" + href(pg["slug"])] = render(s_de, theme, lay, pg, items=items_of(de_p), sep=sep, lang_switch=sw_de,
                                                 tools=search_box("de", search_index(de_p), fid="suche"))
    add("fr", "passed", pages, "3.2.4/T3",
        "The search button reads 'Rechercher' on the French pages and 'Suchen' on the German pages in de/; each language version is its own set and is internally consistent.",
        trap=True, diff="hard")

    # ---------------- T4: text button vs icon button with same name -----------------
    s = site_by_kind("de", "utility")
    pgs = [get_page(s, x) for x in ("index", "wasserqualitaet", "tarife", "stoerungen")]
    idx = search_index(pgs)
    mag = ico("search", "#ffffff")
    icon_btn = (f'<button type="submit" class="icon-btn" aria-label="Suchen"><img src="{mag}" alt="" width="24" height="24"></button>')
    big = ('<div class="bigsearch"><h2>Was suchen Sie?</h2>' + search_box("de", idx, fid="suche-gross") + "</div>")
    pages = make(s, pgs, tools=search_box("de", idx, fid="suche", button_html=icon_btn),
                 per_page={"index": {"tools": "", "extra_main": big}})
    add("de", "passed", pages, "3.2.4/T4",
        "The home page offers a large search with a text button 'Suchen'; inner pages use a magnifier icon button whose accessible name is also 'Suchen' (Understanding example 5).",
        trap=True, diff="medium")

    # ---------------- C1: contact link with a more specific label -----------------
    s = site_by_kind("de", "school")
    pgs = [get_page(s, x) for x in ("index", "unterricht", "ferienplan", "tagesschule")]
    kontakt = service_pages(s)[3]
    ks = ('<section id="tagesschule"><h2>Tagesschule</h2><p>Sekretariat Tagesschule: Montag bis Freitag 7.00–9.00 Uhr, '
          'Telefon 033 000 45 19.</p></section>')
    pages = make(s, pgs + [kontakt], nav_pgs=pgs, tools='<a href="kontakt.html">Kontakt</a>',
                 per_page={"tagesschule": {"tools": '<a href="kontakt.html#tagesschule">Sekretariat Tagesschule</a>'},
                           "kontakt": {"extra_main": ks}})
    add("de", "cantTell", pages, "3.2.4/C1",
        "The header contact link reads 'Kontakt' on most pages but 'Sekretariat Tagesschule' on tagesschule.html and jumps to a section of the same contact page; same or more specific functionality is debatable.",
        diff="hard")

    # ---------------- C2: print button vs print-version link -----------------
    s = site_by_kind("fr", "transport")
    pgs = [get_page(s, x) for x in ("index", "horaires", "billets", "arrets")]
    pv = P("horaires-impression", "Version imprimable", "Horaires – version imprimable",
           ["Ligne 1 : départs de la gare à 6 h 02, puis toutes les vingt minutes jusqu'à 23 h 42.",
            "Ligne 2 : départs de la gare à 6 h 12, puis toutes les vingt minutes jusqu'à 22 h 52."])
    btn = '<button type="button" onclick="window.print()">Imprimer la page</button>'
    pages = make(s, pgs + [pv], nav_pgs=pgs, page_tools=btn,
                 per_page={"horaires": {"page_tools": '<a href="horaires-impression.html">Version imprimable</a>'},
                           "horaires-impression": {"page_tools": ""}})
    add("fr", "cantTell", pages, "3.2.4/C2",
        "Printing is a button 'Imprimer la page' on most pages but a link 'Version imprimable' to a separate print page on horaires.html; whether both are the same functionality is a judgement call.",
        diff="hard")

    return cases
