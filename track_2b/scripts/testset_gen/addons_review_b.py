"""Add-on cases from the group B review (tag "addon"): 3.1.1, 2.4.2 (multi-page), 2.4.5 (folder URLs).

Designed split (dev and test for every item), excluded from the split quota, appended after all
earlier cases (existing ids, splits and contents unchanged). Labels by construction from
PROTOCOL.md as it stands. Fresh fictional vocabulary; nothing shared with the demo site.

Multi-page cases are mini sites (Case.pages). For 2.4.2 the criterion is judged on every page of
the mini site and the case outcome is the worst page outcome; `notes` names the deciding page.
For 2.4.5 the label applies to the set of pages (PROTOCOL 2.4.5 unit). Folder pages
("abfall/index.html") are linked with trailing-slash URLs ("abfall/"); a static HTTP server maps
them to index.html.
"""
from common import *

SITE_CSS = (".site-header{background:#1f6f8b;color:#ffffff;padding:10px 20px}.site-header a{color:#ffffff}"
            ".site-nav ul{list-style:none;display:flex;flex-wrap:wrap;gap:14px;margin:6px 0 0;padding:0}")


def _doc(lang_tag, title, org, nav, main, foot, css=""):
    items = "".join(f'<li><a href="{esc(h)}">{esc(t)}</a></li>' for t, h in nav)
    body = (f'<header class="site-header"><a class="site-name" href="{esc(nav[0][1])}">{esc(org)}</a>'
            f'<nav class="site-nav" aria-label="{esc(foot[0])}"><ul>{items}</ul></nav></header>\n<main>\n{main}\n</main>\n'
            f'<footer class="site-footer"><p>{esc(foot[1])}</p></footer>')
    return page(lang_tag, title, body, css=SITE_CSS + css)


# =============================================================================== 3.1.1
RM_NAV = [("Pagina principala", "index.html"), ("Actualitads", "actualitads.html"), ("Administraziun", "administraziun.html"),
          ("Contact", "contact.html")]
RM_FOOT = ("Navigaziun principala", "Vischnanca da Exemplun · Via principala 5 · 7999 Exemplun · 081 000 45 67")
RM_PAGES = [
    ("Uffizi da vischnanca",
     "<h1>Uffizi da vischnanca</h1><p>L'uffizi da vischnanca è avert da glindesdi fin venderdi, da las 8.00 fin las 11.30 "
     "e da las 14.00 fin las 17.00.</p><p>Per dumondas pudais Vus telefonar al numer 081 000 45 67 u scriver ina "
     "brev a l'administraziun.</p>"),
    ("Radunanza da vischnanca",
     "<h1>Radunanza da vischnanca</h1><p>La radunanza da vischnanca ha lieu il venderdi, ils 27 da november, a las 20.00 "
     "en la sala da gimnastica.</p><p>Tractandas: preventiv 2027, renovaziun da la scola e elecziun d'in member da la "
     "cumissiun da gestiun.</p>"),
    ("Rimnada da ruments",
     "<h1>Rimnada da ruments</h1><p>Ils ruments vegnan rimnads mintga mesemna. Mettai ils satgs avant las 7.00 a la "
     "via.</p><p>Il vaider e l'aluminium pudais Vus purtar a la plazza da rimnada sper la staziun.</p>"),
    ("Biblioteca da la vischnanca",
     "<h1>Biblioteca da la vischnanca</h1><p>La biblioteca è averta il mardi e la gievgia da las 15.00 fin las 18.00.</p>"
     "<p>Ils cudeschs pon vegnir emprestads per quatter emnas. Ils uffants survegnan in carnet da lectura gratuit.</p>"),
]
# (page text index, split, declared lang, expected, rule, trap, note)
RM_CASES = [
    (0, "dev", "rm", "passed", "3.1.1/P1", False,
     "Romansh (Rumantsch Grischun) page declared lang=\"rm\": the primary subtag matches the only language of the page (P1)."),
    (1, "test", "rm-CH", "passed", "3.1.1/T3", True,
     "Romansh page declared lang=\"rm-CH\": the region subtag is irrelevant and the primary subtag rm matches (T3)."),
    (2, "dev", "de", "failed", "3.1.1/F3", False,
     "The page is entirely in Romansh but declares lang=\"de\" (valid tag, wrong language): screen readers read it with German rules (F3)."),
    (3, "test", "de-CH", "failed", "3.1.1/F3", False,
     "The page is entirely in Romansh but declares lang=\"de-CH\"; the primary subtag de does not match the content (F3)."),
]
ADDR = [
    ("dev", "Seniorenreise nach Valfittizia",
     "<h1>Seniorenreise nach Valfittizia</h1><p>Vom 8. bis 10. Juni reisen wir mit dem Car in die Partnergemeinde. "
     "Die Anmeldung ist bis Ende März bei der Gemeindekanzlei möglich. Unterwegs besuchen wir folgende Orte:</p>"
     "<ul><li>Museo della Pietra, Piazza della Fontana 2, 6997 Valfittizia</li><li>Grotto al Ponte, Via ai Mulini 11, "
     "6998 Esempiano</li><li>Cantina Sociale, Strada Cantonale 40, 6996 Modellina</li></ul><p>Im Reisepreis von "
     "CHF 380.– sind Fahrt, Unterkunft und alle Eintritte inbegriffen. Für Personen mit eingeschränkter Mobilität "
     "steht ein Begleitdienst zur Verfügung.</p>"),
    ("test", "Partnerschaften der Gemeinde",
     "<h1>Partnerschaften der Gemeinde</h1><p>Seit vielen Jahren pflegt unsere Gemeinde enge Beziehungen zu zwei "
     "Gemeinden südlich der Alpen. Die folgenden Stellen sind für Austauschprojekte von Schulen und Vereinen "
     "zuständig:</p><ul><li>Municipio di Esempiano, Piazza Grande 1, 6998 Esempiano</li><li>Casa della Cultura, "
     "Vicolo del Torchio 3, 6997 Valfittizia</li></ul><p>Anfragen können Sie auch direkt an unsere Gemeindekanzlei "
     "richten. Wir leiten sie gerne an die zuständigen Personen weiter und unterstützen Sie bei der Planung.</p>"),
]


def cases_3_1_1(rng):
    out = []
    for k, (idx, split, tag, exp, rule, trap, note) in enumerate(RM_CASES):
        title, main = RM_PAGES[idx]
        html = _doc(tag, f"{title} – Vischnanca da Exemplun", "Vischnanca da Exemplun", RM_NAV, main, RM_FOOT)
        out.append(Case("3.1.1", "rm", exp, html=html, target=None, rule=rule, trap=trap, notes=note,
                        difficulty="hard" if exp == "passed" else "medium", split=split,
                        template=f"rb-311-rm-{k}", tags=("addon", "review-b-3.1.1-romansh")))
    nav = [("Startseite", "index.html"), ("Leben & Wohnen", "leben.html"), ("Freizeit", "freizeit.html"), ("Kontakt", "kontakt.html")]
    for k, (split, title, main) in enumerate(ADDR):
        html = _doc("de-CH", f"{title} – Gemeinde Fiktal", "Gemeinde Fiktal", nav, main,
                    ("Hauptnavigation", "Gemeinde Fiktal · Erlenstrasse 22 · 3996 Fiktal"))
        out.append(Case("3.1.1", "de", "passed", html=html, target=None, rule="3.1.1/T1", trap=True, difficulty="hard",
                        split=split, template=f"rb-311-addr-{k}", tags=("addon", "review-b-3.1.1-placenames"),
                        notes=("German page whose main content lists Italian-named places, institutions and postal "
                               "addresses; these are proper names and do not change the dominant language, so de-CH is "
                               "correct (T1).")))
    return out


# =============================================================================== 2.4.2 (multi-page)
def _site242(lang, org, nav, foot, pages):
    """pages: {file: (title, main)} -> {file: html}"""
    tag = SITE_LANG_TAG[lang]
    return {f: _doc(tag, t, org, nav, m, foot) for f, (t, m) in pages.items()}


def app_site(lang, k):
    if lang == "de":
        org, app = "Gemeinde Fiktal", "Online-Schalter – Gemeinde Fiktal"
        nav = [("Online-Schalter", "index.html"), ("Hilfe", "hilfe.html")]
        foot = ("Hauptnavigation", "Gemeinde Fiktal · Online-Schalter")
        pages = {"index.html": (app, "<h1>Online-Schalter</h1><p>Wählen Sie eine Dienstleistung.</p><ul><li><a href=\"schritt-1.html\">Hundemarke bestellen</a></li></ul>"),
                 "schritt-1.html": (app, "<h1>Hundemarke bestellen – Schritt 1: Angaben zum Hund</h1><p>Name, Rasse und Geburtsjahr des Hundes.</p><p><a href=\"schritt-2.html\">Weiter zu Schritt 2</a></p>"),
                 "schritt-2.html": (app, "<h1>Hundemarke bestellen – Schritt 2: Zustelladresse</h1><p>An welche Adresse sollen wir die Marke senden?</p><p><a href=\"index.html\">Zurück zur Übersicht</a></p>"),
                 "hilfe.html": ("Hilfe zum Online-Schalter – Gemeinde Fiktal", "<h1>Hilfe</h1><p>Antworten auf häufige Fragen zum Online-Schalter.</p>")}
    else:
        org, app = "Comune di Valfittizia", "Sportello online – Comune di Valfittizia"
        nav = [("Sportello online", "index.html"), ("Aiuto", "aiuto.html")]
        foot = ("Navigazione principale", "Comune di Valfittizia · Sportello online")
        pages = {"index.html": (app, "<h1>Sportello online</h1><p>Scegliete un servizio.</p><ul><li><a href=\"passo-1.html\">Prenotare la sala multiuso</a></li></ul>"),
                 "passo-1.html": (app, "<h1>Prenotazione sala – Passo 1: data e orario</h1><p>Indicate il giorno e la fascia oraria desiderati.</p><p><a href=\"passo-2.html\">Avanti</a></p>"),
                 "passo-2.html": (app, "<h1>Prenotazione sala – Passo 2: dati di contatto</h1><p>Chi è la persona responsabile della manifestazione?</p><p><a href=\"index.html\">Torna alla panoramica</a></p>"),
                 "aiuto.html": ("Aiuto per lo sportello online – Comune di Valfittizia", "<h1>Aiuto</h1><p>Risposte alle domande frequenti.</p>")}
    return _site242(lang, org, nav, foot, pages)


def section_site(lang, k):
    if lang == "fr":
        org, sec = "Ville de Bourg-Modèle", "Actualités – Ville de Bourg-Modèle"
        nav = [("Accueil", "index.html"), ("Actualités", "actualites.html")]
        foot = ("Navigation principale", "Ville de Bourg-Modèle · Rue des Artisans 18")
        pages = {"index.html": ("Ville de Bourg-Modèle", "<h1>Bienvenue à Bourg-Modèle</h1><p>Toutes les nouvelles de la ville.</p><p><a href=\"actualites.html\">Actualités</a></p>"),
                 "actualites.html": (sec, "<h1>Actualités</h1><ul><li><a href=\"marche-noel.html\">Le marché de Noël s'agrandit</a></li><li><a href=\"pont-ferme.html\">Le pont des Tanneurs fermé en janvier</a></li></ul>"),
                 "marche-noel.html": (sec, "<h1>Le marché de Noël s'agrandit</h1><p>Cette année, quarante chalets occuperont la place des Halles du 4 au 20 décembre.</p>"),
                 "pont-ferme.html": (sec, "<h1>Le pont des Tanneurs fermé en janvier</h1><p>Des travaux d'entretien imposent la fermeture du pont du 8 au 26 janvier.</p>")}
    else:
        org, sec = "Gemeinde Ober-Beispielwil", "Aktuelles – Gemeinde Ober-Beispielwil"
        nav = [("Startseite", "index.html"), ("Aktuelles", "aktuelles.html")]
        foot = ("Hauptnavigation", "Gemeinde Ober-Beispielwil · Obere Gasse 7")
        pages = {"index.html": ("Gemeinde Ober-Beispielwil", "<h1>Willkommen in Ober-Beispielwil</h1><p>Neuigkeiten und Dienstleistungen der Gemeinde.</p><p><a href=\"aktuelles.html\">Aktuelles</a></p>"),
                 "aktuelles.html": (sec, "<h1>Aktuelles</h1><ul><li><a href=\"eisbahn.html\">Eisbahn auf dem Schulhausplatz eröffnet</a></li><li><a href=\"wasserleitung.html\">Wasserleitung Hofmattweg wird ersetzt</a></li></ul>"),
                 "eisbahn.html": (sec, "<h1>Eisbahn auf dem Schulhausplatz eröffnet</h1><p>Ab Samstag kann auf dem Schulhausplatz wieder Schlittschuh gelaufen werden.</p>"),
                 "wasserleitung.html": (sec, "<h1>Wasserleitung Hofmattweg wird ersetzt</h1><p>Vom 12. bis 30. Januar ist der Hofmattweg nur einspurig befahrbar.</p>")}
    return _site242(lang, org, nav, foot, pages)


def home_title_site(lang, k):
    if lang == "it":
        org = "Comune di Esempiano"
        nav = [("Home", "index.html"), ("Imposte", "imposte.html"), ("Rifiuti", "rifiuti.html")]
        foot = ("Navigazione principale", "Comune di Esempiano · Via ai Ronchi 5")
        pages = {"index.html": (org, "<h1>Benvenuti a Esempiano</h1><p>Il portale del comune.</p>"),
                 "imposte.html": (org, "<h1>Imposte comunali 2027</h1><p>Moltiplicatore d'imposta, scadenze e rate.</p>"),
                 "rifiuti.html": ("Raccolta rifiuti – Comune di Esempiano", "<h1>Raccolta rifiuti</h1><p>Calendario e punti di raccolta.</p>")}
        deciding = "imposte.html"
    else:
        org = "Commune d'Exempleval"
        nav = [("Accueil", "index.html"), ("Écoles", "ecoles.html"), ("Eau potable", "eau.html")]
        foot = ("Navigation principale", "Commune d'Exempleval · Chemin du Crêt 12")
        pages = {"index.html": (org, "<h1>Bienvenue à Exempleval</h1><p>Le site officiel de la commune.</p>"),
                 "ecoles.html": ("Écoles – Commune d'Exempleval", "<h1>Écoles</h1><p>Horaires, transports scolaires et cantine.</p>"),
                 "eau.html": (org, "<h1>Qualité de l'eau potable</h1><p>Résultats des analyses 2026 et dureté de l'eau.</p>")}
        deciding = "eau.html"
    return _site242(lang, org, nav, foot, pages), deciding


def cases_2_4_2(rng):
    out = []
    for k, (lang, split) in enumerate([("de", "dev"), ("it", "test")]):
        out.append(Case("2.4.2", lang, "passed", pages=app_site(lang, k), target=None, rule="2.4.2/T5", trap=True,
                        difficulty="hard", split=split, template=f"rb-242-app-{k}", tags=("addon", "review-b-2.4.2-app"),
                        notes=("Mini site (outcome = worst page). The views of the web application (steps 1 and 2) share the "
                               "application title while their h1 names the task (T5); the home page carries the application "
                               "name (T3) and the help page its own topic (P1).")))
    for k, (lang, split) in enumerate([("fr", "dev"), ("de", "test")]):
        out.append(Case("2.4.2", lang, "cantTell", pages=section_site(lang, k), target=None, rule="2.4.2/C1",
                        alt_expected="failed", difficulty="hard", split=split, template=f"rb-242-section-{k}",
                        tags=("addon", "review-b-2.4.2-section"),
                        notes=("Mini site (outcome = worst page). The two single articles are titled only with their section "
                               "name (\"Actualités/Aktuelles – …\") although each covers one specific topic (C1, strict ACT "
                               "c4a8a4: failed); the home and section overview pages are fine.")))
    for k, (lang, split) in enumerate([("it", "dev"), ("fr", "test")]):
        pages, deciding = home_title_site(lang, k)
        out.append(Case("2.4.2", lang, "failed", pages=pages, target=None, rule="2.4.2/F4", difficulty="medium",
                        split=split, template=f"rb-242-hometitle-{k}", tags=("addon", "review-b-2.4.2-hometitle"),
                        notes=(f"Mini site (outcome = worst page). The inner page {deciding} has exactly the home page's "
                               "title (the organisation name only) although it covers a specific topic (F4); the home page "
                               "itself may use the site name (T3).")))
    return out


# =============================================================================== 2.4.5 (folder URLs)
SITES245 = [
    # (lang, split, orphan, org, nav label, footer, home h1, folders [(folder, nav text, h1, text)], sitemap (folder, text), orphan page)
    ("de", "dev", False, "Gemeinde Fiktal", "Hauptnavigation", "Gemeinde Fiktal · Erlenstrasse 22", "Willkommen in Fiktal",
     [("abfall", "Abfall", "Abfall und Recycling", "Sammeltage, Gebühren und Annahmestellen."),
      ("steuern", "Steuern", "Steuern", "Steuerfuss, Fristen und Ratenzahlung."),
      ("schule", "Schule", "Schule und Betreuung", "Stundenpläne, Tagesschule und Schulweg.")],
     ("sitemap", "Sitemap"), None),
    ("fr", "test", False, "Commune de Valfictif", "Navigation principale", "Commune de Valfictif · Place de la Fontaine 1",
     "Bienvenue à Valfictif",
     [("dechets", "Déchets", "Déchets et recyclage", "Jours de ramassage, taxes et déchetterie."),
      ("impots", "Impôts", "Impôts", "Coefficient, délais et paiements échelonnés."),
      ("ecoles", "Écoles", "Écoles et accueil", "Horaires, accueil parascolaire et trajets.")],
     ("plan-du-site", "Plan du site"), None),
    ("it", "dev", True, "Comune di Modellina", "Navigazione principale", "Comune di Modellina · Strada del Bosco 8",
     "Benvenuti a Modellina",
     [("rifiuti", "Rifiuti", "Rifiuti e riciclaggio", "Giorni di raccolta, tasse ed ecocentro."),
      ("imposte", "Imposte", "Imposte", "Moltiplicatore, scadenze e rate."),
      ("scuole", "Scuole", "Scuole e doposcuola", "Orari, mensa e trasporto allievi.")],
     ("mappa-del-sito", "Mappa del sito"), ("pista-ghiaccio", "Pista di ghiaccio: apertura anticipata", "La pista sul piazzale della scuola apre già il 28 novembre.")),
    ("de", "test", True, "Stadt Mustersee", "Hauptnavigation", "Stadt Mustersee · Rosenweg 9", "Willkommen in Mustersee",
     [("verkehr", "Verkehr", "Verkehr und Parkieren", "Parkkarten, Baustellen und Busverbindungen."),
      ("kultur", "Kultur", "Kultur und Freizeit", "Museum, Bibliothek und Vereine."),
      ("bauen", "Bauen", "Bauen und Wohnen", "Baugesuche, Zonenplan und Merkblätter.")],
     ("sitemap", "Sitemap"), ("seebad", "Seebad: neue Saisonkarten", "Die Saisonkarten für das Seebad sind ab sofort am Kiosk erhältlich.")),
]


def site245(spec):
    lang, split, orphan, org, navlab, foot, home_h1, folders, (smap, smap_text), orphan_page = spec
    tag = SITE_LANG_TAG[lang]

    def nav_for(prefix):
        items = [({"de": "Startseite", "fr": "Accueil", "it": "Home"}[lang], prefix or "./")]
        items += [(t, f"{prefix}{f}/") for f, t, _, _ in folders]
        items += [(smap_text, f"{prefix}{smap}/")]
        return items

    pages = {}
    home_main = f"<h1>{esc(home_h1)}</h1><p>{esc(org)}</p>"
    if orphan_page:
        of, oh, ot = orphan_page
        more = {"de": "Mehr zum Seebad", "it": "Dettagli sulla pista"}[lang]
        home_main += (f'<aside class="box"><p><strong>{esc(oh)}</strong></p><p>{esc(ot)} '
                      f'<a href="{of}/">{esc(more)}</a></p></aside>')
    pages["index.html"] = _doc(tag, f"{home_h1} – {org}", org, nav_for(""), home_main, (navlab, foot))
    for f, t, h1, text in folders:
        pages[f"{f}/index.html"] = _doc(tag, f"{h1} – {org}", org, nav_for("../"), f"<h1>{esc(h1)}</h1><p>{esc(text)}</p>", (navlab, foot))
    smap_items = "".join(f'<li><a href="../{f}/">{esc(h1)}</a></li>' for f, _, h1, _ in folders)
    smap_items = f'<li><a href="../">{esc(home_h1)}</a></li>' + smap_items + f'<li><a href="../{smap}/">{esc(smap_text)}</a></li>'
    pages[f"{smap}/index.html"] = _doc(tag, f"{smap_text} – {org}", org, nav_for("../"),
                                       f"<h1>{esc(smap_text)}</h1><ul>{smap_items}</ul>", (navlab, foot))
    if orphan_page:
        of, oh, ot = orphan_page
        pages[f"{of}/index.html"] = _doc(tag, f"{oh} – {org}", org, nav_for("../"), f"<h1>{esc(oh)}</h1><p>{esc(ot)}</p>", (navlab, foot))
    return pages


def cases_2_4_5(rng):
    out = []
    for k, spec in enumerate(SITES245):
        lang, split, orphan = spec[0], spec[1], spec[2]
        pages = site245(spec)
        if orphan:
            of = spec[9][0]
            exp, rule, note = "failed", "2.4.5/F1", (f"Set of pages with folder URLs (\"{of}/\" → {of}/index.html). Every page is in "
                                                     f"the main navigation and the site map except {of}/, which is reachable only "
                                                     "through one teaser link on the home page and is not a step in a process (F1).")
        else:
            exp, rule, note = "passed", "2.4.5/P1", ("Set of pages with folder URLs (\"abfall/\" style, served as folder/index.html). "
                                                     "Every page is reachable through the main navigation and through the site map "
                                                     "linked from every page (P1).")
        out.append(Case("2.4.5", lang, exp, pages=pages, target=None, rule=rule, difficulty="medium", split=split,
                        template=f"rb-245-{k}", tags=("addon", "review-b-2.4.5-folders"), notes=note))
    return out


BUILDERS = {"3.1.1": cases_3_1_1, "2.4.2": cases_2_4_2, "2.4.5": cases_2_4_5}


def cases_for(criterion: str, rng) -> list:
    fn = BUILDERS.get(criterion)
    return fn(rng) if fn else []
