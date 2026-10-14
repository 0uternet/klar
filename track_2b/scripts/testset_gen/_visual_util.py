"""Private helpers for the 'visual' criterion modules (1.1.1, 1.4.1, 1.4.3, 1.4.5, 1.4.11).

Only stdlib + common.py. Everything here is deterministic given the rng passed in.
Distractor blocks contain NO images, NO form controls, NO custom colours and only
underlined (UA default) links, so they are passing non-candidates for all five criteria.
"""
from __future__ import annotations

from common import (SITE_LANG_TAG, STREETS, PEOPLE, esc, page, pick, pick_theme, sample, slug,
                    contrast)

# ---------------------------------------------------------------------------
# Organisations by type, and matching navigation menus (all fictional)
# ---------------------------------------------------------------------------

ORG = {
    "de": {
        "gemeinde": ["Gemeinde Beispielwil", "Gemeinde Beispielberg", "Stadt Mustersee", "Gemeinde Fiktal",
                     "Gemeinde Ober-Beispielwil"],
        "schule": ["Schule Beispielberg", "Primarschule Fiktal"],
        "bibliothek": ["Bibliothek Mustersee", "Gemeindebibliothek Fiktal"],
        "verkehr": ["Beispielwiler Verkehrsbetriebe", "Ortsbus Beispielberg"],
        "museum": ["Museum im Kornhaus Mustersee"],
        "werke": ["Wasserversorgung Fiktal", "Werke Beispielberg"],
        "sport": ["Sportzentrum Mustersee", "Sportverein Beispielberg"],
    },
    "fr": {
        "gemeinde": ["Commune de Valfictif", "Ville de Bourg-Modèle", "Commune d'Exempleval"],
        "schule": ["École de Valfictif", "Établissement primaire d'Exempleval"],
        "bibliothek": ["Bibliothèque de Bourg-Modèle", "Bibliothèque communale de Valfictif"],
        "verkehr": ["Transports publics de Valfictif"],
        "museum": ["Musée du Moulin, Bourg-Modèle"],
        "werke": ["Service des eaux d'Exempleval", "Services industriels de Valfictif"],
        "sport": ["Piscine de Bourg-Modèle", "Club sportif d'Exempleval"],
    },
    "it": {
        "gemeinde": ["Comune di Esempiano", "Città di Modellina", "Comune di Valfittizia"],
        "schule": ["Scuola di Esempiano", "Scuole comunali di Modellina"],
        "bibliothek": ["Biblioteca di Modellina", "Biblioteca comunale di Esempiano"],
        "verkehr": ["Trasporti pubblici di Modellina"],
        "museum": ["Museo della Filanda, Esempiano"],
        "werke": ["Azienda acqua potabile Valfittizia", "Aziende municipalizzate di Esempiano"],
        "sport": ["Centro sportivo di Modellina", "Società sportiva Valfittizia"],
    },
    "en": {
        "tourism": ["Example Valley Tourism", "Lake Fictal Hostel"],
    },
}

NAVS = {
    "de": {
        "gemeinde": ["Startseite", "Aktuelles", "Verwaltung", "Leben & Wohnen", "Freizeit"],
        "schule": ["Startseite", "Schulhäuser", "Termine", "Elternrat", "Kontakt"],
        "bibliothek": ["Startseite", "Medien", "Veranstaltungen", "Öffnungszeiten", "Kontakt"],
        "verkehr": ["Fahrplan", "Billette", "Linien", "Störungen", "Kontakt"],
        "museum": ["Ausstellungen", "Besuch", "Vermittlung", "Sammlung", "Kontakt"],
        "werke": ["Startseite", "Wasser", "Abfall", "Gebühren", "Kontakt"],
        "sport": ["Startseite", "Anlagen", "Kurse", "Preise", "Kontakt"],
    },
    "fr": {
        "gemeinde": ["Accueil", "Actualités", "Administration", "Population", "Loisirs"],
        "schule": ["Accueil", "Établissements", "Agenda", "Parents", "Contact"],
        "bibliothek": ["Accueil", "Catalogue", "Animations", "Horaires", "Contact"],
        "verkehr": ["Horaires", "Billets", "Lignes", "Perturbations", "Contact"],
        "museum": ["Expositions", "Visite", "Médiation", "Collection", "Contact"],
        "werke": ["Accueil", "Eau", "Déchets", "Taxes", "Contact"],
        "sport": ["Accueil", "Installations", "Cours", "Tarifs", "Contact"],
    },
    "it": {
        "gemeinde": ["Home", "Attualità", "Amministrazione", "Popolazione", "Tempo libero"],
        "schule": ["Home", "Sedi", "Calendario", "Genitori", "Contatti"],
        "bibliothek": ["Home", "Catalogo", "Eventi", "Orari", "Contatti"],
        "verkehr": ["Orari", "Biglietti", "Linee", "Perturbazioni", "Contatti"],
        "museum": ["Mostre", "Visita", "Mediazione", "Collezione", "Contatti"],
        "werke": ["Home", "Acqua", "Rifiuti", "Tasse", "Contatti"],
        "sport": ["Home", "Impianti", "Corsi", "Tariffe", "Contatti"],
    },
    "en": {
        "tourism": ["Home", "Plan your visit", "Hiking", "Accommodation", "Contact"],
    },
}

NAV_LABEL = {"de": "Hauptnavigation", "fr": "Navigation principale", "it": "Navigazione principale",
             "en": "Main navigation"}
CRUMB_LABEL = {"de": "Sie sind hier", "fr": "Fil d'Ariane", "it": "Percorso", "en": "Breadcrumb"}
HOME = {"de": "Startseite", "fr": "Accueil", "it": "Home", "en": "Home"}


def org_of(rng, lang, kind="gemeinde"):
    return pick(rng, ORG[lang][kind])


def host_of(org: str) -> str:
    return slug(org) + ".example"


def phone(rng) -> str:
    area = pick(rng, ["031", "032", "026", "027", "091", "044", "052", "061"])
    return f"{area} 000 {rng.randint(10, 99)} {rng.randint(10, 99)}"


def date_str(rng, lang, year=2026) -> str:
    d, m = rng.randint(1, 28), rng.randint(1, 12)
    return f"{d}.{m}.{year}" if lang != "en" else f"{d}.{m}.{year}"


# ---------------------------------------------------------------------------
# Distractor blocks (hand-written, per language). Placeholders: {org} {street} {phone}
# {host} {person} {d1} {d2}
# ---------------------------------------------------------------------------

FILLER = {
    "de": [
        "<section><h2>Öffnungszeiten</h2><p>Montag bis Freitag 8.30–11.30 Uhr und 14.00–17.00 Uhr, "
        "Donnerstag durchgehend bis 18.30 Uhr. Vor Feiertagen schliessen wir bereits um 16.00 Uhr.</p></section>",
        "<section><h2>Kontakt</h2><p>{org}<br>{street}<br>Telefon {phone}<br>"
        "<a href=\"mailto:info@{host}\">info@{host}</a></p></section>",
        "<section><h2>Weitere Meldungen</h2><ul><li><a href=\"meldung-festtage.html\">Geänderte Öffnungszeiten "
        "über die Festtage</a></li><li><a href=\"meldung-kirchweg.html\">Kirchweg wegen Leitungsbau gesperrt</a></li>"
        "<li><a href=\"meldung-umfrage.html\">Ergebnisse der Umfrage zum Ortsbus</a></li></ul></section>",
        "<section class=\"box\"><h2>Gut zu wissen</h2><p>Die meisten Formulare können Sie online ausfüllen und per "
        "E-Mail oder Post einreichen. Bei Fragen hilft Ihnen das Team am Schalter gerne weiter.</p></section>",
        "<section><h2>Downloads</h2><ul><li><a href=\"merkblatt.pdf\">Merkblatt (PDF, 180 KB)</a></li>"
        "<li><a href=\"gebuehren-2026.pdf\">Gebührenübersicht 2026 (PDF, 95 KB)</a></li></ul></section>",
        "<section><h2>Nächste Termine</h2><table><thead><tr><th>Datum</th><th>Anlass</th></tr></thead><tbody>"
        "<tr><td>{d1}</td><td>Informationsabend im Gemeindesaal</td></tr><tr><td>{d2}</td>"
        "<td>Sprechstunde des Gemeindepräsidiums</td></tr></tbody></table></section>",
        "<section><h2>Newsletter</h2><p>Einmal im Monat informieren wir per E-Mail über Neuigkeiten aus der Region. "
        "<a href=\"newsletter.html\">Newsletter abonnieren</a></p></section>",
        "<section><h2>Notfallnummern</h2><ul><li>Feuerwehr 118</li><li>Polizei 117</li><li>Sanität 144</li></ul></section>",
        "<section><h2>Zuständig</h2><p>{person}, Sekretariat<br>Telefon {phone}</p></section>",
        "<section><h2>Barrierefreiheit</h2><p>Wir arbeiten laufend daran, diese Website für alle zugänglich zu "
        "machen. Hinweise nehmen Sie gerne unter <a href=\"mailto:web@{host}\">web@{host}</a> entgegen.</p></section>",
    ],
    "fr": [
        "<section><h2>Horaires du guichet</h2><p>Du lundi au vendredi, de 8 h 30 à 11 h 30 et de 14 h à 17 h ; "
        "le jeudi sans interruption jusqu'à 18 h 30. La veille des jours fériés, fermeture à 16 h.</p></section>",
        "<section><h2>Contact</h2><p>{org}<br>{street}<br>Téléphone {phone}<br>"
        "<a href=\"mailto:info@{host}\">info@{host}</a></p></section>",
        "<section><h2>Autres actualités</h2><ul><li><a href=\"actu-fetes.html\">Horaires pendant les fêtes</a></li>"
        "<li><a href=\"actu-travaux.html\">Travaux à la rue de l'Église dès lundi</a></li>"
        "<li><a href=\"actu-sondage.html\">Résultats du sondage sur le bus local</a></li></ul></section>",
        "<section class=\"box\"><h2>Bon à savoir</h2><p>La plupart des formulaires peuvent être remplis en ligne "
        "puis envoyés par courriel ou par la poste. Notre équipe vous renseigne volontiers au guichet.</p></section>",
        "<section><h2>Documents</h2><ul><li><a href=\"aide-memoire.pdf\">Aide-mémoire (PDF, 160 Ko)</a></li>"
        "<li><a href=\"tarifs-2026.pdf\">Tarifs 2026 (PDF, 90 Ko)</a></li></ul></section>",
        "<section><h2>Prochains rendez-vous</h2><table><thead><tr><th>Date</th><th>Événement</th></tr></thead>"
        "<tbody><tr><td>{d1}</td><td>Séance d'information à la salle communale</td></tr><tr><td>{d2}</td>"
        "<td>Permanence de la syndique</td></tr></tbody></table></section>",
        "<section><h2>Infolettre</h2><p>Une fois par mois, nous vous informons des nouveautés de la région. "
        "<a href=\"infolettre.html\">S'abonner à l'infolettre</a></p></section>",
        "<section><h2>Numéros d'urgence</h2><ul><li>Pompiers 118</li><li>Police 117</li><li>Ambulance 144</li></ul></section>",
        "<section><h2>Personne de contact</h2><p>{person}, secrétariat<br>Téléphone {phone}</p></section>",
        "<section><h2>Accessibilité</h2><p>Nous améliorons constamment l'accessibilité de ce site. Vos remarques "
        "sont les bienvenues à l'adresse <a href=\"mailto:web@{host}\">web@{host}</a>.</p></section>",
    ],
    "it": [
        "<section><h2>Orari dello sportello</h2><p>Da lunedì a venerdì, 8.30–11.30 e 14.00–17.00; il giovedì "
        "orario continuato fino alle 18.30. Alla vigilia dei giorni festivi chiudiamo alle 16.00.</p></section>",
        "<section><h2>Contatti</h2><p>{org}<br>{street}<br>Telefono {phone}<br>"
        "<a href=\"mailto:info@{host}\">info@{host}</a></p></section>",
        "<section><h2>Altre notizie</h2><ul><li><a href=\"notizia-festivi.html\">Orari durante le festività</a></li>"
        "<li><a href=\"notizia-cantiere.html\">Cantiere in Via Cantonale da lunedì</a></li>"
        "<li><a href=\"notizia-sondaggio.html\">Risultati del sondaggio sul bus locale</a></li></ul></section>",
        "<section class=\"box\"><h2>Buono a sapersi</h2><p>La maggior parte dei moduli si può compilare online e "
        "inviare per e-mail o per posta. Allo sportello vi aiutiamo volentieri.</p></section>",
        "<section><h2>Documenti</h2><ul><li><a href=\"promemoria.pdf\">Promemoria (PDF, 170 kB)</a></li>"
        "<li><a href=\"tariffe-2026.pdf\">Tariffe 2026 (PDF, 92 kB)</a></li></ul></section>",
        "<section><h2>Prossimi appuntamenti</h2><table><thead><tr><th>Data</th><th>Evento</th></tr></thead><tbody>"
        "<tr><td>{d1}</td><td>Serata informativa in sala comunale</td></tr><tr><td>{d2}</td>"
        "<td>Udienza del sindaco</td></tr></tbody></table></section>",
        "<section><h2>Newsletter</h2><p>Una volta al mese vi informiamo sulle novità della regione. "
        "<a href=\"newsletter.html\">Iscriversi alla newsletter</a></p></section>",
        "<section><h2>Numeri d'emergenza</h2><ul><li>Pompieri 118</li><li>Polizia 117</li><li>Ambulanza 144</li></ul></section>",
        "<section><h2>Persona di riferimento</h2><p>{person}, segretariato<br>Telefono {phone}</p></section>",
        "<section><h2>Accessibilità</h2><p>Lavoriamo costantemente per rendere questo sito accessibile a tutti. "
        "Segnalazioni a <a href=\"mailto:web@{host}\">web@{host}</a>.</p></section>",
    ],
    "en": [
        "<section><h2>Opening hours</h2><p>Monday to Saturday, 8.30–12.00 and 13.30–18.00. Sundays and public "
        "holidays 9.00–12.00.</p></section>",
        "<section><h2>Contact</h2><p>{org}<br>{street}<br>Phone {phone}<br>"
        "<a href=\"mailto:info@{host}\">info@{host}</a></p></section>",
        "<section class=\"box\"><h2>Good to know</h2><p>Guests staying overnight receive a free regional transport "
        "card for the duration of their stay.</p></section>",
        "<section><h2>More news</h2><ul><li><a href=\"news-season.html\">Winter season opens on 12 December</a></li>"
        "<li><a href=\"news-trails.html\">Two hiking trails closed for repairs</a></li></ul></section>",
    ],
}


def fill(rng, lang, org, k):
    street = pick(rng, STREETS[lang])
    ctx = dict(org=esc(org), street=esc(street), phone=phone(rng), host=host_of(org),
               person=esc(pick(rng, PEOPLE[lang])), d1=date_str(rng, lang), d2=date_str(rng, lang))
    return [b.format(**ctx) for b in sample(rng, FILLER[lang], k)]


# ---------------------------------------------------------------------------
# Page composition
# ---------------------------------------------------------------------------

LAYOUT_CSS = (".cols{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr);gap:28px}"
              "@media (max-width:720px){.cols{grid-template-columns:1fr}}"
              ".crumbs{list-style:none;padding:0;margin:0 0 8px;display:flex;flex-wrap:wrap;gap:8px;font-size:.9rem}"
              ".crumbs li+li::before{content:'/';margin-right:8px}")


def header_html(lang, org, kind, logo_html=None):
    nav = NAVS[lang][kind]
    items = "".join(f'<li><a href="{slug(n)}.html">{esc(n)}</a></li>' for n in nav)
    brand = logo_html if logo_html is not None else esc(org)
    return (f'<header class="site-header"><a class="site-name" href="index.html">{brand}</a>'
            f'<nav class="site-nav" aria-label="{NAV_LABEL[lang]}"><ul>{items}</ul></nav></header>')


def footer_html(lang, org, rng, extra=""):
    street = pick(rng, STREETS[lang])
    contact = {"de": "Kontakt", "fr": "Contact", "it": "Contatti", "en": "Contact"}[lang]
    imp = {"de": "Impressum", "fr": "Mentions légales", "it": "Note legali", "en": "Legal notice"}[lang]
    return (f'<footer class="site-footer">{extra}<p>{esc(org)} · {esc(street)} · '
            f'<a href="kontakt.html">{contact}</a> · <a href="impressum.html">{imp}</a></p></footer>')


def compose(rng, lang, org, main_html, *, kind="gemeinde", chrome=None, n_fill=None, layout=None,
            crumb=None, logo_html=None, footer_extra="", before_main=""):
    """Return (body_html, css). ``main_html`` should start with the page's <h1>."""
    if chrome is None:
        chrome = rng.random() < 0.75
    if n_fill is None:
        n_fill = rng.randint(1, 3)
    if layout is None:
        layout = rng.randrange(3)
    blocks = fill(rng, lang, org, n_fill) if n_fill else []
    if layout == 1 and blocks:
        inner = (f'<div class="cols"><div>{main_html}</div>'
                 f'<aside>{"".join(blocks)}</aside></div>')
    else:
        inner = main_html + "".join(blocks)
    if crumb is None:
        crumb = chrome and rng.random() < 0.4
    if crumb:
        inner = (f'<nav aria-label="{CRUMB_LABEL[lang]}"><ol class="crumbs"><li><a href="index.html">'
                 f'{HOME[lang]}</a></li><li>{esc(pick(rng, NAVS[lang].get(kind, list(NAVS[lang].values())[0])[1:4]))}</li>'
                 f'</ol></nav>' + inner)
    main = f"<main>\n{inner}\n</main>"
    if not chrome:
        return before_main + main, LAYOUT_CSS
    body = (header_html(lang, org, kind, logo_html) + "\n" + before_main + main + "\n"
            + footer_html(lang, org, rng, footer_extra))
    return body, LAYOUT_CSS


def doc(rng, lang, title, org, body, css="", *, theme=None, head=""):
    theme = theme or pick_theme(rng)
    return page(SITE_LANG_TAG[lang], f"{title} – {org}", body, theme=theme, css=css, head=head)


def ratio(a, b):
    """Contrast ratio, truncated (never rounded up) to 2 decimals for notes."""
    r = contrast(a, b)
    return int(r * 100) / 100


def img(src, alt=None, w=None, h=None, **extra):
    a = f'<img src="{src}"'
    if alt is not None:
        a += f' alt="{esc(alt)}"'
    if w:
        a += f' width="{w}"'
    if h:
        a += f' height="{h}"'
    for k, v in extra.items():
        k = k.rstrip("_").replace("_", "-")
        a += f' {k}' if v is True else f' {k}="{esc(str(v))}"'
    return a + ">"
