"""2.4.5 Multiple Ways — mini sites (every internal link resolves; entry index.html; target None)."""
from __future__ import annotations

import unicodedata

from common import *  # noqa: F401,F403
from common import Case, esc, pick, pick_theme
from _operable_util import (P, UI, brand, footer_simple, get_page, href, main_content, nav_block, nav_items,
                            search_box, search_index, site_by_kind, site_doc, skip_link, title_of)

CRITERION = "2.4.5"

MORE = {"de": "Mehr zum Thema", "fr": "En savoir plus", "it": "Approfondimenti"}
SEARCH_ID = {"de": "suche", "fr": "recherche", "it": "ricerca"}


def _key(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def teasers(site, deep, other):
    ui = UI[site["lang"]]
    items = [(site["teaser"], href(deep["slug"]), deep["p"][0]),
             (other["h1"], href(other["slug"]), other["p"][0])]
    lis = "".join(f'<li><h3><a href="{h}">{esc(t)}</a></h3><p>{esc(p)}</p></li>' for t, h, p in items)
    return f'<section><h2>{esc(ui["news"])}</h2><ul class="teasers">{lis}</ul></section>'


def sitemap_html(site, groups):
    """groups: [(page, [children])]"""
    lis = []
    for pg, kids in groups:
        sub = ("<ul>" + "".join(f'<li><a href="{href(k["slug"])}">{esc(k["h1"])}</a></li>' for k in kids) + "</ul>") if kids else ""
        lis.append(f'<li><a href="{href(pg["slug"])}">{esc(pg["h1"] if pg["slug"] != "index" else pg["nav"])}</a>{sub}</li>')
    return "<ul>" + "".join(lis) + "</ul>"


def az_html(pages):
    pages = sorted(pages, key=lambda p: _key(p["h1"]))
    out, cur = [], None
    for p in pages:
        letter = _key(p["h1"])[0].upper()
        if letter != cur:
            if cur is not None:
                out.append("</ul>")
            out.append(f"<h2>{letter}</h2><ul>")
            cur = letter
        out.append(f'<li><a href="{href(p["slug"])}">{esc(p["h1"])}</a></li>')
    out.append("</ul>")
    return "".join(out)


def mk_site(site, theme, layout, *, pages, nav_pages, search_idx=None, search_ext=None, foot=(), extra=None,
            crumbs=None, sep=" – "):
    """Render every page in ``pages`` (P dicts). foot: [(label, slug)] footer links. extra: {slug: html}.
    crumbs: {slug: [P ancestors]}."""
    lang = site["lang"]
    ui = UI[lang]
    extra = extra or {}
    items = nav_items(site, nav_pages)
    out = {}
    for pg in pages:
        h = href(pg["slug"])
        cls = {"top": "site-nav", "side": "side-nav", "band": "band"}[layout]
        nav = nav_block(items, ui["nav"], current=h, cls=cls)
        tools = ""
        if search_idx is not None:
            tools = f'<div class="tools">{search_box(lang, search_idx, fid=SEARCH_ID[lang])}</div>'
        elif search_ext:
            tools = ('<div class="tools">' + search_box(lang, None, fid=SEARCH_ID[lang], results=False)
                     .replace('action="#"', f'action="{esc(search_ext)}" method="get"') + "</div>")
        main = ""
        if crumbs and pg["slug"] in crumbs:
            trail = crumbs[pg["slug"]]
            lis = "".join(f'<li><a href="{href(a["slug"])}">{esc(a["nav"])}</a></li>' for a in trail)
            main += (f'<nav class="crumbs" aria-label="{esc(ui["crumbs"])}"><ol>{lis}'
                     f'<li><a href="{h}" aria-current="page">{esc(pg["nav"])}</a></li></ol></nav>')
        main += main_content(pg, extra.get(pg["slug"], ""))
        fl = ""
        if foot:
            fl = (f'<nav class="foot-links" aria-label="{esc(ui["footer_nav"])}"><ul>'
                  + "".join(f'<li><a href="{href(sl)}">{esc(lb)}</a></li>' for lb, sl in foot) + "</ul></nav>")
        top = [skip_link(lang)]
        if layout == "top":
            top.append(f'<header class="site-header">{brand(site["org"])}{nav}{tools}</header>')
            doc = site_doc(lang, title_of(pg, site, sep), theme, top=top, main=main, bottom=[footer_simple(site, fl)])
        elif layout == "band":
            top += [f'<header class="site-header">{brand(site["org"])}{tools}</header>', nav]
            doc = site_doc(lang, title_of(pg, site, sep), theme, top=top, main=main, bottom=[footer_simple(site, fl)])
        else:
            top.append(f'<header class="site-header">{brand(site["org"])}{tools}</header>')
            doc = site_doc(lang, title_of(pg, site, sep), theme, top=top, main=main, aside=nav,
                           bottom=[footer_simple(site, fl)])
        out[h] = doc
    return out


def _lay(rng):
    return pick(rng, ("top", "side", "band"))


def _sep(rng):
    return pick(rng, (" – ", " | ", " · "))


def children_box(lang, kids):
    return (f"<h2>{esc(MORE[lang])}</h2><ul>" + "".join(f'<li><a href="{href(k["slug"])}">{esc(k["h1"])}</a></li>' for k in kids)
            + "</ul>")


def build(rng):
    cases = []

    def add(lang, expected, pages, rule, notes, *, trap=False, alt=None, diff="medium"):
        cases.append(Case(CRITERION, lang, expected, pages=pages, target=None, rule=rule, notes=notes,
                          trap=trap, alt_expected=alt, difficulty=diff))

    # ---------------- F1: one page only via a teaser -----------------
    s = site_by_kind("de", "utility")
    ui = UI["de"]
    idx, navp, deep = s["pages"][0], s["pages"], s["deep"]
    smap = P("sitemap", ui["sitemap"], ui["sitemap"], ["Alle Seiten der Wasserversorgung Fiktal auf einen Blick."])
    pages = navp + [deep, smap]
    pages_html = mk_site(s, pick_theme(rng), _lay(rng), pages=pages, nav_pages=navp, foot=[(ui["sitemap"], "sitemap")],
                         sep=_sep(rng), extra={"index": teasers(s, deep, navp[2]),
                                               "sitemap": sitemap_html(s, [(p, []) for p in navp])})
    add("de", "failed", pages_html, "2.4.5/F1",
        "zaehlerablesung.html is linked only from the home-page teaser: it is not in the navigation and the site map omits it, so it has a single way.",
        diff="medium")

    s = site_by_kind("fr", "transport")
    navp, deep = s["pages"], s["deep"]
    pages = navp + [deep]
    pages_html = mk_site(s, pick_theme(rng), _lay(rng), pages=pages, nav_pages=navp, search_idx=search_index(navp),
                         sep=_sep(rng), extra={"index": teasers(s, deep, navp[3])})
    add("fr", "failed", pages_html, "2.4.5/F1",
        "The working search indexes only the navigation pages; noctambus.html is reachable solely through the home-page teaser (search for 'Noctambus' finds nothing).",
        diff="hard")

    s = site_by_kind("it", "library")
    ui = UI["it"]
    navp, deep = s["pages"], s["deep"]
    az = P("indice-a-z", ui["az"], ui["az"], ["Tutti i temi del sito in ordine alfabetico."])
    pages = navp + [deep, az]
    pages_html = mk_site(s, pick_theme(rng), _lay(rng), pages=pages, nav_pages=navp, foot=[(ui["az"], "indice-a-z")],
                         sep=_sep(rng), extra={"index": teasers(s, deep, navp[5]), "indice-a-z": az_html(navp[1:])})
    add("it", "failed", pages_html, "2.4.5/F1",
        "scambio-libri.html appears neither in the navigation nor in the A–Z index; the only path to it is the news teaser on the home page.",
        diff="medium")

    # ---------------- F2: navigation only, sub-pages via parent -----------------
    s = site_by_kind("de", "municipality")
    navp, deep = s["pages"], s["deep"]
    bau = P("baugesuch", "Baugesuch", "Baugesuch einreichen", [
        "Ein vollständiges Baugesuch umfasst das Formular, die Pläne im Massstab 1:100 und einen Situationsplan.",
        "Die Bauverwaltung prüft die Unterlagen innert 30 Tagen und publiziert das Gesuch im Amtsanzeiger."])
    pages = navp + [deep, bau]
    pages_html = mk_site(s, pick_theme(rng), _lay(rng), pages=pages, nav_pages=navp, sep=_sep(rng),
                         extra={"verwaltung": children_box("de", [deep]), "bauen": children_box("de", [bau])})
    add("de", "failed", pages_html, "2.4.5/F2",
        "Eight pages, navigation is the only mechanism: hundekontrolle.html and baugesuch.html can be found only by opening their parent page (no search, site map or index).",
        diff="medium")

    s = site_by_kind("it", "school")
    navp, deep = s["pages"], s["deep"]
    menu = P("menu-settimanale", "Menù", "Menù della settimana", [
        "Il menù è preparato ogni giorno dalla cucina del Centro anziani con prodotti della regione."],
        ["Lunedì: risotto allo zafferano e insalata", "Martedì: polenta e spezzatino",
         "Giovedì: pasta al pomodoro e verdure", "Venerdì: filetto di pesce con patate"])
    pages = navp + [deep, menu]
    pages_html = mk_site(s, pick_theme(rng), _lay(rng), pages=pages, nav_pages=navp, sep=_sep(rng),
                         extra={"calendario": children_box("it", [deep]), "mensa": children_box("it", [menu])})
    add("it", "failed", pages_html, "2.4.5/F2",
        "Only the main navigation exists; settimana-bianca.html and menu-settimanale.html are reachable exclusively via the calendar and canteen pages.",
        diff="medium")

    s = site_by_kind("fr", "tourism")
    navp, deep = s["pages"], s["deep"]
    lac = P("tour-du-lac", "Tour du lac", "Le tour du lac", [
        "Ce parcours facile de 9 km longe la rive et traverse la réserve naturelle des Roseaux.",
        "Comptez 2 h 30 de marche ; bancs et fontaines jalonnent l'itinéraire."])
    pages = navp + [deep, lac]
    pages_html = mk_site(s, pick_theme(rng), _lay(rng), pages=pages, nav_pages=navp, sep=_sep(rng),
                         extra={"patrimoine": children_box("fr", [deep]), "randonnees": children_box("fr", [lac])})
    add("fr", "failed", pages_html, "2.4.5/F2",
        "The tourism site has no search, site map or index; fete-vendanges.html and tour-du-lac.html are only linked from one section page each.",
        diff="medium")

    # ---------------- P1: navigation + site map -----------------
    s = site_by_kind("it", "utility")
    ui = UI["it"]
    navp, deep = s["pages"], s["deep"]
    smap = P("mappa-del-sito", ui["sitemap"], ui["sitemap"], ["Tutte le pagine dell'azienda in un colpo d'occhio."])
    pages = navp + [deep, smap]
    groups = [(p, [deep] if p["slug"] == "chi-siamo" else []) for p in navp]
    pages_html = mk_site(s, pick_theme(rng), _lay(rng), pages=pages, nav_pages=navp, foot=[(ui["sitemap"], "mappa-del-sito")],
                         sep=_sep(rng), extra={"index": teasers(s, deep, navp[4]), "mappa-del-sito": sitemap_html(s, groups)})
    add("it", "passed", pages_html, "2.4.5/P1",
        "Every page is in the site map linked from each footer, and every page except the meter-reading notice is also in the navigation; that notice is additionally linked from the home teaser.",
        diff="easy")

    # ---------------- P2: navigation + working search -----------------
    s = site_by_kind("de", "library")
    navp, deep = s["pages"], s["deep"]
    pages = navp + [deep]
    pages_html = mk_site(s, pick_theme(rng), _lay(rng), pages=pages, nav_pages=navp, search_idx=search_index(navp + [deep]),
                         sep=_sep(rng), extra={"index": teasers(s, deep, navp[4])})
    add("de", "passed", pages_html, "2.4.5/P2",
        "Navigation plus a working client-side search whose index lists all seven pages, including the Sommerleseclub page that is not in the menu.",
        diff="medium")

    # ---------------- P3: navigation + A-Z index -----------------
    s = site_by_kind("fr", "municipality")
    ui = UI["fr"]
    navp, deep = s["pages"], s["deep"]
    az = P("index-a-z", ui["az"], ui["az"], ["Tous les thèmes du site par ordre alphabétique."])
    pages = navp + [deep, az]
    pages_html = mk_site(s, pick_theme(rng), _lay(rng), pages=pages, nav_pages=navp, foot=[(ui["az"], "index-a-z")],
                         sep=_sep(rng), extra={"index": teasers(s, deep, navp[3]), "index-a-z": az_html(navp[1:] + [deep])})
    add("fr", "passed", pages_html, "2.4.5/P3",
        "Besides the navigation, an A–Z index linked from every footer lists every content page, including the dog-tax notice.",
        diff="medium")

    # ---------------- T1: process pages (exception) -----------------
    s = site_by_kind("fr", "school")
    ui = UI["fr"]
    navp, deep = s["pages"], s["deep"]
    smap = P("plan-du-site", ui["sitemap"], ui["sitemap"], ["Vue d'ensemble de chaque rubrique de l'école."])
    st2 = P("inscription-devoirs-2", "Étape 2", "Inscription aux devoirs surveillés – étape 2 sur 2", [
        "Vérifiez les informations saisies, puis confirmez l'inscription."])
    conf = P("inscription-devoirs-confirmation", "Confirmation", "Inscription enregistrée", [
        "Merci ! Vous recevrez une confirmation par courriel dans les prochains jours."])
    form1 = ('<h2>Inscription</h2><form action="inscription-devoirs-2.html" method="get"><label for="enfant">Nom de l\'enfant</label>'
             '<input id="enfant" name="enfant"><label for="classe">Classe</label><input id="classe" name="classe">'
             '<fieldset><legend>Jours</legend><label><input type="checkbox" name="j" value="lu"> lundi</label>'
             '<label><input type="checkbox" name="j" value="ma"> mardi</label><label><input type="checkbox" name="j" value="je"> jeudi</label>'
             '</fieldset><button type="submit">Continuer</button></form>')
    form2 = ('<form action="inscription-devoirs-confirmation.html" method="get"><p><a href="devoirs.html">Corriger mes indications</a></p>'
             '<button type="submit">Confirmer l\'inscription</button></form>')
    pages = navp + [deep, smap, st2, conf]
    groups = [(p, [deep] if p["slug"] == "parents" else []) for p in navp]
    pages_html = mk_site(s, pick_theme(rng), _lay(rng), pages=pages, nav_pages=navp, foot=[(ui["sitemap"], "plan-du-site")],
                         sep=_sep(rng), extra={"index": teasers(s, deep, navp[2]), "plan-du-site": sitemap_html(s, groups),
                                               "devoirs": form1, "inscription-devoirs-2": form2,
                                               "inscription-devoirs-confirmation": '<p><a href="index.html">Retour à l\'accueil</a></p>'})
    add("fr", "passed", pages_html, "2.4.5/T1",
        "Content pages are in the navigation and the site map; inscription-devoirs-2.html and the confirmation page are reachable only through the form, but they are steps/results of a process (exception).",
        trap=True, diff="hard")

    s = site_by_kind("it", "transport")
    navp, deep = s["pages"], s["deep"]
    st2 = P("abbonamento-passo-2", "Passo 2", "Ordine dell'abbonamento – passo 2 di 3", [
        "Indicate l'indirizzo al quale spedire l'abbonamento."])
    conf = P("abbonamento-conferma", "Conferma", "Ordine ricevuto", [
        "Grazie! L'abbonamento vi sarà spedito entro cinque giorni lavorativi insieme alla fattura."])
    form1 = ('<h2>Ordinare l\'abbonamento mensile</h2><form action="abbonamento-passo-2.html" method="get">'
             '<label for="zona">Zona</label><select id="zona" name="zona"><option>Zona 10</option><option>Zone 10 + 11</option></select>'
             '<label for="mese">Primo mese di validità</label><select id="mese" name="mese"><option>gennaio 2027</option>'
             '<option>febbraio 2027</option></select><button type="submit">Avanti</button></form>')
    form2 = ('<form action="abbonamento-conferma.html" method="get"><label for="via">Via e numero</label><input id="via" name="via">'
             '<label for="cap">CAP e località</label><input id="cap" name="cap"><button type="submit">Invia l\'ordine</button></form>')
    pages = navp + [deep, st2, conf]
    pages_html = mk_site(s, pick_theme(rng), _lay(rng), pages=pages, nav_pages=navp, search_idx=search_index(navp + [deep]),
                         sep=_sep(rng), extra={"index": teasers(s, deep, navp[1]), "biglietti": form1,
                                               "abbonamento-passo-2": form2,
                                               "abbonamento-conferma": '<p><a href="index.html">Torna alla home</a></p>'})
    add("it", "passed", pages_html, "2.4.5/T1",
        "Navigation plus a search covering all content pages; the order step 2 and the confirmation page are only reachable by submitting the form, which the process exception allows.",
        trap=True, diff="hard")

    # ---------------- T2: tiny site, every page links to every page -----------------
    s = site_by_kind("de", "tourism")
    navp = [s["pages"][0], s["pages"][1], s["pages"][2], s["pages"][4]]
    intro = ('<h2>Entdecken</h2><ul><li><a href="wandern.html">Wanderrouten</a></li><li><a href="unterkuenfte.html">Unterkünfte</a></li>'
             '<li><a href="anreise.html">Anreise</a></li></ul>')
    pages_html = mk_site(s, pick_theme(rng), _lay(rng), pages=navp, nav_pages=navp, sep=_sep(rng), extra={"index": intro})
    add("de", "passed", pages_html, "2.4.5/T2",
        "A four-page site without search or site map, but every page links to every other page and the home page lists all pages (G126/G185, small-site note).",
        trap=True, diff="hard")

    # ---------------- C1: external search -----------------
    s = site_by_kind("de", "transport")
    navp = s["pages"]
    pages_html = mk_site(s, pick_theme(rng), _lay(rng), pages=navp, nav_pages=navp, sep=_sep(rng),
                         search_ext="https://suche.mvb.example/")
    add("de", "cantTell", pages_html, "2.4.5/C1",
        "Besides the menu, the only other mechanism is a search form posting to an external search service; whether it indexes all pages cannot be determined from the site.",
        diff="hard")

    # ---------------- C2: hierarchical nav + breadcrumbs -----------------
    s = site_by_kind("it", "municipality")
    navp, deep = s["pages"], s["deep"]
    eco = P("ecocentro", "Ecocentro", "Ecocentro al Ronco", [
        "L'ecocentro accetta vetro, metalli, ingombranti e scarti vegetali.",
        "Orari: sabato 9.00–12.00 e mercoledì 16.00–18.00."])
    home = navp[0]
    amm = get_page(s, "amministrazione")
    rif = get_page(s, "rifiuti")
    crumbs = {p["slug"]: [home] for p in navp[1:]}
    crumbs["cani"] = [home, amm]
    crumbs["ecocentro"] = [home, rif]
    pages = navp + [deep, eco]
    pages_html = mk_site(s, pick_theme(rng), _lay(rng), pages=pages, nav_pages=navp, sep=_sep(rng), crumbs=crumbs,
                         extra={"amministrazione": children_box("it", [deep]), "rifiuti": children_box("it", [eco])})
    add("it", "cantTell", pages_html, "2.4.5/C2",
        "Sub-pages (cani.html, ecocentro.html) are reached via their parent page; the only other device is a breadcrumb trail, whose status as a second way is disputed.",
        alt="failed", diff="hard")

    return cases
