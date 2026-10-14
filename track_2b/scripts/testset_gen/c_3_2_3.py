"""3.2.3 Consistent Navigation — mini sites with repeated navigation blocks (target None)."""
from __future__ import annotations

from common import *  # noqa: F401,F403
from common import Case, esc, pick, pick_theme, THEMES
from _operable_util import (P, UI, brand, footer_simple, get_page, href, main_content, nav_block, service_pages,
                            site_by_kind, site_doc, skip_link, title_of)

CRITERION = "3.2.3"

QUICK_CSS = (".quick ul{list-style:none;display:flex;flex-wrap:wrap;gap:12px;margin:0;padding:0;font-size:.92rem}"
             ".quickbar{padding:6px 24px;border-bottom:1px solid #c9d3d8}")


def render(site, theme, layout, pg, *, items, nav_pos="top", mode="link", sub=None, quick=None, quick_first=False,
           foot_links=None, sep=" – ", brand_text=None, skip=True, lang_switch="", title=None, extra_main="", css=""):
    lang = site["lang"]
    ui = UI[lang]
    cur = href(pg["slug"])
    cls = {"top": "site-nav", "side": "side-nav", "band": "band"}[layout]
    nav = nav_block(items, ui["nav"], cls=cls if nav_pos == "top" else "band", current=cur, mode=mode, sub=sub)
    qb = ""
    if quick:
        qb = (f'<nav class="quick quickbar" aria-label="{esc(ui["quick"])}"><ul>'
              + "".join(f'<li><a href="{esc(h)}">{esc(lb)}</a></li>' for lb, h in quick) + "</ul></nav>")
    fl = ""
    if foot_links:
        fl = (f'<nav class="foot-links" aria-label="{esc(ui["footer_nav"])}"><ul>'
              + "".join(f'<li><a href="{esc(h)}">{esc(lb)}</a></li>' for lb, h in foot_links) + "</ul></nav>")
    top = [skip_link(lang)] if skip else []
    hdr_inner = brand(brand_text or site["org"]) + lang_switch
    bottom = []
    aside = None
    if nav_pos == "bottom":
        top.append(f'<header class="site-header">{hdr_inner}</header>')
        if qb:
            top.append(qb)
        bottom.append(nav)
    elif layout == "top":
        top.append(f'<header class="site-header">{hdr_inner}{nav}</header>')
        if qb:
            top.insert(len(top) - 1 if quick_first else len(top), qb)
    elif layout == "band":
        top.append(f'<header class="site-header">{hdr_inner}</header>')
        if qb and quick_first:
            top += [qb, nav]
        else:
            top += [nav] + ([qb] if qb else [])
    else:
        top.append(f'<header class="site-header">{hdr_inner}</header>')
        if qb:
            top.append(qb)
        aside = nav
    bottom.append(footer_simple(site, fl))
    return site_doc(lang, title or title_of(pg, site, sep), theme, top=top, main=main_content(pg, extra_main),
                    aside=aside, bottom=bottom, css=QUICK_CSS + css)


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

    def site_pages(site, pgs, *, theme, layout, sep, per_page=None, **kw):
        per_page = per_page or {}
        out = {}
        for pg in pgs:
            opts = dict(kw)
            opts.update(per_page.get(pg["slug"], {}))
            out[href(pg["slug"])] = render(site, theme, layout, pg, sep=sep, **opts)
        return out

    # ---------------- F1: items in a different relative order -----------------
    s = site_by_kind("de", "library")
    pgs = s["pages"][:5]
    it = items_of(pgs)
    swapped = [it[0], it[3], it[1], it[2], it[4]]
    pages = site_pages(s, pgs, theme=pick_theme(rng), layout=_lay(rng), sep=_sep(rng), items=it,
                       per_page={"ausleihe": {"items": swapped}})
    add("de", "failed", pages, "3.2.3/F1",
        "On ausleihe.html the menu reads Startseite, Medien, Öffnungszeiten, Ausleihe, E-Medien – 'Medien' moved ahead of two items that precede it on all other pages.",
        diff="medium")

    s = site_by_kind("fr", "utility")
    pgs = [get_page(s, x) for x in ("index", "qualite", "tarifs", "pannes")]
    it = items_of(pgs)
    moved = [it[3], it[0], it[1], it[2]]
    pages = site_pages(s, pgs, theme=pick_theme(rng), layout=_lay(rng), sep=_sep(rng), items=it,
                       per_page={"tarifs": {"items": moved}})
    add("fr", "failed", pages, "3.2.3/F1",
        "On tarifs.html 'Pannes' is moved to the first position of the main navigation, before 'Accueil'; on the other pages it is last.",
        diff="easy")

    s = site_by_kind("it", "school")
    pgs = s["pages"][:5]
    it = items_of(pgs)
    alt_order = [it[0], it[1], it[4], it[3], it[2]]
    pages = site_pages(s, pgs, theme=pick_theme(rng), layout=_lay(rng), sep=_sep(rng), items=it,
                       per_page={"mensa": {"items": alt_order}})
    add("it", "failed", pages, "3.2.3/F1",
        "On mensa.html the last three menu items appear as Trasporto allievi, Mensa, Calendario instead of Calendario, Mensa, Trasporto allievi.",
        diff="medium")

    # ---------------- F2: navigation moved to the bottom -----------------
    s = site_by_kind("it", "transport")
    pgs = [get_page(s, x) for x in ("index", "orari", "biglietti", "fermate")]
    pages = site_pages(s, pgs, theme=pick_theme(rng), layout=pick(rng, ("top", "band")), sep=_sep(rng), items=items_of(pgs),
                       per_page={"fermate": {"nav_pos": "bottom"}})
    add("it", "failed", pages, "3.2.3/F2",
        "On fermate.html the main navigation is rendered after the content, just above the footer, while every other page shows it in the header before the content.",
        diff="medium")

    s = site_by_kind("de", "tourism")
    pgs = [get_page(s, x) for x in ("index", "wandern", "winter", "anreise")]
    pages = site_pages(s, pgs, theme=pick_theme(rng), layout="side", sep=_sep(rng), items=items_of(pgs),
                       per_page={"winter": {"nav_pos": "bottom"}})
    add("de", "failed", pages, "3.2.3/F2",
        "winter.html drops the side navigation and repeats the same menu only at the end of the page, so its position relative to header, content and footer changes.",
        diff="medium")

    # ---------------- F3: two nav blocks swap -----------------
    s = site_by_kind("fr", "municipality")
    svc = service_pages(s)
    contact = svc[3]
    pgs = [get_page(s, x) for x in ("index", "administration", "dechets", "impots")]
    quick = [("Guichet en ligne", "administration.html"), ("Calendrier des déchets", "dechets.html"), (contact["nav"], href(contact["slug"]))]
    allp = pgs + [contact]
    pages = site_pages(s, allp, theme=pick_theme(rng), layout=pick(rng, ("top", "band")), sep=_sep(rng), items=items_of(pgs),
                       quick=quick, per_page={"impots": {"quick_first": True}})
    add("fr", "failed", pages, "3.2.3/F3",
        "On impots.html the 'Accès direct' quick-links bar comes before the main navigation; on all other pages it follows it.",
        diff="hard")

    # ---------------- P1: consistent -----------------
    s = site_by_kind("fr", "tourism")
    pgs = [get_page(s, x) for x in ("index", "randonnees", "hebergement", "acces")]
    svc = service_pages(s)
    foot = [(svc[0]["nav"], href(svc[0]["slug"])), (svc[3]["nav"], href(svc[3]["slug"]))]
    pages = site_pages(s, pgs + [svc[0], svc[3]], theme=pick_theme(rng), layout=_lay(rng), sep=_sep(rng), items=items_of(pgs),
                       foot_links=foot)
    add("fr", "passed", pages, "3.2.3/P1",
        "All six pages repeat the same header navigation and the same footer links in the same order.", diff="easy")

    s = site_by_kind("it", "library")
    pgs = s["pages"][:5]
    pages = site_pages(s, pgs, theme=pick_theme(rng), layout=_lay(rng), sep=_sep(rng), items=items_of(pgs))
    add("it", "passed", pages, "3.2.3/P1", "The five pages share one navigation in an identical order.", diff="easy")

    # ---------------- T1: expanded sub-navigation -----------------
    s = site_by_kind("de", "municipality")
    pgs = [get_page(s, x) for x in ("index", "verwaltung", "steuern", "bauen", "abfall")]
    top_items = items_of([pgs[0], pgs[1], pgs[4]])
    def sub_ul(cur):
        mark = ' aria-current="page"'
        return '<ul>' + "".join(
            f'<li><a href="{href(p["slug"])}"{mark if p["slug"] == cur else ""}>{esc(p["nav"])}</a></li>'
            for p in pgs[2:4]) + '</ul>'
    per = {sl: {"sub": {"verwaltung.html": sub_ul(sl)}} for sl in ("verwaltung", "steuern", "bauen")}
    pages = site_pages(s, pgs, theme=pick_theme(rng), layout=pick(rng, ("side", "band")), sep=_sep(rng), items=top_items,
                       per_page=per)
    add("de", "passed", pages, "3.2.3/T1",
        "On the Verwaltung section pages a sub-list (Steuern, Bauen) is expanded under 'Verwaltung'; Startseite, Verwaltung, Abfall keep their relative order everywhere.",
        trap=True, diff="medium")

    # ---------------- T2: current page as text -----------------
    s = site_by_kind("it", "municipality")
    pgs = [get_page(s, x) for x in ("index", "amministrazione", "imposte", "tempo-libero")]
    pages = site_pages(s, pgs, theme=pick_theme(rng), layout=_lay(rng), sep=_sep(rng), items=items_of(pgs), mode="text")
    add("it", "passed", pages, "3.2.3/T2",
        "Each page shows its own menu item as plain text with aria-current instead of a link; the item order is the same on all pages.",
        trap=True, diff="medium")

    # ---------------- T3: skip link + extra item on some pages -----------------
    s = site_by_kind("fr", "transport")
    trav = P("travaux", "Travaux été 2027", "Travaux à la gare routière", [
        "Du 5 juillet au 15 août 2027, les quais de la gare routière sont rénovés.",
        "Les lignes 1 et 2 partent de l'arrêt provisoire « Gare Sud »."])
    pgs = [get_page(s, x) for x in ("index", "horaires", "billets", "arrets")]
    base = items_of(pgs)
    extra = [base[0], base[1], ("Travaux été 2027", "travaux.html"), base[2], base[3]]
    per = {sl: {"items": extra} for sl in ("index", "horaires", "travaux")}
    pages = site_pages(s, pgs + [trav], theme=pick_theme(rng), layout=_lay(rng), sep=_sep(rng), items=base, per_page=per)
    add("fr", "passed", pages, "3.2.3/T3",
        "A temporary 'Travaux été 2027' item is inserted between Horaires and Billets on three pages only; the other items and the skip link keep their relative order.",
        trap=True, diff="hard")

    # ---------------- T4: language versions -----------------
    s = site_by_kind("de", "transport")
    de_p = [get_page(s, x) for x in ("index", "fahrplan", "billette")]
    fr_p = [P("index", "Accueil", "Transports publics de Beispielwil", [
                "Six lignes de bus relient Beispielwil, Beispielberg et Fiktal toutes les quinze minutes."]),
            P("horaire", "Horaire", "Horaire", ["Le nouvel horaire est valable dès le 13 décembre 2026.",
                                               "La ligne 3 dessert désormais l'hôpital de Mustersee."]),
            P("billets", "Billets", "Billets et abonnements", ["Les billets s'achètent au distributeur, dans le bus ou dans l'application."],
              ["Billet simple zone 10 : CHF 2.80", "Carte journalière : CHF 8.40", "Abonnement mensuel adulte : CHF 68.–"])]
    theme = pick_theme(rng)
    layout = _lay(rng)
    sep = _sep(rng)
    pages = {}
    for pg in de_p:
        sw = ('<nav class="lang-switch" aria-label="Sprache"><ul><li><span aria-current="true" lang="de">DE</span></li>'
              '<li><a href="fr/index.html" lang="fr" hreflang="fr">FR</a></li></ul></nav>')
        pages[href(pg["slug"])] = render(s, theme, layout, pg, items=items_of(de_p), sep=sep, lang_switch=sw)
    s_fr = dict(s, lang="fr", street="Gerberngasse 15, 3999 Beispielwil")
    for pg in fr_p:
        sw = ('<nav class="lang-switch" aria-label="Langue"><ul><li><a href="../index.html" lang="de" hreflang="de">DE</a></li>'
              '<li><span aria-current="true" lang="fr">FR</span></li></ul></nav>')
        pages["fr/" + href(pg["slug"])] = render(s_fr, theme, layout, pg, items=items_of(fr_p), sep=sep, lang_switch=sw)
    add("de", "passed", pages, "3.2.3/T4",
        "The German pages and the French pages (fr/) each repeat their own navigation in a consistent order; the switcher shows the current language as text. Language versions are separate sets.",
        trap=True, diff="hard")

    # ---------------- C1: footer service links reordered -----------------
    s = site_by_kind("fr", "library")
    pgs = [get_page(s, x) for x in ("index", "horaires", "inscription")]
    svc = service_pages(s)
    sv = [svc[0], svc[2], svc[3]]
    foot = [(p["nav"], href(p["slug"])) for p in sv]
    pages = site_pages(s, pgs + sv, theme=pick_theme(rng), layout=_lay(rng), sep=_sep(rng), items=items_of(pgs), foot_links=foot,
                       per_page={"inscription": {"foot_links": [foot[2], foot[0], foot[1]]}})
    add("fr", "cantTell", pages, "3.2.3/C1",
        "Only the footer links differ: on inscription.html 'Contact' comes first instead of last; whether a footer link list is a repeated navigational mechanism is disputed.",
        alt="failed", diff="hard")

    # ---------------- C2: sub-offer page with own branding -----------------
    s = site_by_kind("de", "school")
    pgs = [get_page(s, x) for x in ("index", "unterricht", "ferienplan", "tagesschule")]
    it = items_of(pgs)
    theme = pick_theme(rng)
    other = THEMES[(THEMES.index(theme) + 2) % len(THEMES)]
    pages = site_pages(s, pgs[:3], theme=theme, layout="top", sep=" – ", items=it)
    pages["tagesschule.html"] = render(s, other, "band", pgs[3], items=[it[3], it[0], it[1], it[2]],
                                       brand_text="Tagesschule Beispielberg · ein Angebot der Schule Beispielberg",
                                       title="Tagesschule Beispielberg",
                                       extra_main="<h2>Tarife</h2><p>Die Tarife richten sich nach dem steuerbaren Einkommen; "
                                                  "ein Mittagessen kostet höchstens CHF 9.–.</p>")
    add("de", "cantTell", pages, "3.2.3/C2",
        "tagesschule.html is styled as the day-care unit's own sub-site (different branding and colours) and lists the menu with 'Tagesschule' first; whether it belongs to the same set of pages is unclear.",
        diff="hard")

    return cases
