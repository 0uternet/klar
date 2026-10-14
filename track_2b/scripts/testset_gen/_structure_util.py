"""Private helpers shared by the "structure" criterion modules
(1.3.1, 1.3.2, 1.3.3, 1.3.5, 2.4.6, 2.5.3, 4.1.2). Stdlib only, deterministic."""
from __future__ import annotations

from common import *  # noqa: F401,F403

# Neutral side boxes (independent news items). Every heading describes its content, every link
# has its own text, there are no instructions, no form fields and no sensory wording, so a box
# never adds a failing candidate for any of the criteria above.
NEWS = {
    "de": [
        ("Sperrung Seeweg", "Wegen Belagsarbeiten ist der Seeweg vom 3. bis 7.11.2026 für den Verkehr gesperrt. "
         "Der Bus fährt in dieser Zeit über die Dorfstrasse.", "Umleitungsplan Seeweg", "umleitung-seeweg.html"),
        ("Ludothek neu auch am Samstag", "Ab Dezember ist die Ludothek zusätzlich am Samstag von 9.30 bis 11.30 Uhr geöffnet.",
         "Angebot der Ludothek", "ludothek.html"),
        ("Christbaumverkauf beim Werkhof", "Der Forstbetrieb verkauft am 12.12.2026 Bäume aus dem Gemeindewald, "
         "Nordmanntannen ab CHF 35.–.", "Preise und Sorten", "christbaeume.html"),
        ("Neue Mitarbeiterin in der Einwohnerkontrolle", "Seit dem 1. Oktober verstärkt Corinne Probst das Team am Schalter.",
         "Team der Einwohnerkontrolle", "einwohnerkontrolle.html"),
        ("Budget 2027 aufgelegt", "Das Budget liegt bis zum 20.11.2026 in der Gemeindekanzlei zur Einsicht auf.",
         "Budget 2027 (PDF, 410 KB)", "budget-2027.pdf"),
    ],
    "fr": [
        ("Fermeture de la rue des Granges", "En raison de travaux, la rue des Granges est fermée du 3 au 7 novembre 2026. "
         "Les bus empruntent l'avenue de la Gare.", "Plan de déviation", "deviation.html"),
        ("Ludothèque ouverte le samedi", "Dès décembre, la ludothèque vous accueille aussi le samedi de 9 h 30 à 11 h 30.",
         "Offre de la ludothèque", "ludotheque.html"),
        ("Vente de sapins de Noël", "Le service forestier vend des sapins de la forêt communale le 12 décembre 2026 "
         "dès 9 heures.", "Prix et variétés", "sapins.html"),
        ("Budget 2027", "Le budget peut être consulté au greffe communal jusqu'au 20 novembre 2026.",
         "Budget 2027 (PDF, 380 Ko)", "budget-2027.pdf"),
        ("Nouvelle collaboratrice au contrôle des habitants", "Depuis le 1er octobre, Sophie Fictif renforce l'équipe du guichet.",
         "Équipe du contrôle des habitants", "controle-habitants.html"),
    ],
    "it": [
        ("Chiusura di Via Cantonale", "Per lavori di pavimentazione Via Cantonale resta chiusa dal 3 al 7 novembre 2026. "
         "Gli autobus transitano da Via alla Stazione.", "Piano delle deviazioni", "deviazioni.html"),
        ("Ludoteca aperta anche il sabato", "Da dicembre la ludoteca è aperta anche il sabato dalle 9.30 alle 11.30.",
         "Offerta della ludoteca", "ludoteca.html"),
        ("Vendita di alberi di Natale", "Il servizio forestale vende abeti del bosco patriziale il 12 dicembre 2026 "
         "presso il magazzino comunale.", "Prezzi e varietà", "alberi-natale.html"),
        ("Preventivo 2027", "Il preventivo è consultabile presso la cancelleria comunale fino al 20 novembre 2026.",
         "Preventivo 2027 (PDF, 395 kB)", "preventivo-2027.pdf"),
        ("Nuova collaboratrice all'Ufficio controllo abitanti", "Dal 1° ottobre Giulia Fittizi rafforza il team dello sportello.",
         "Team dell'Ufficio controllo abitanti", "controllo-abitanti.html"),
    ],
    "en": [
        ("Lake path closed for repairs", "The lakeside path between the pier and the campsite is closed until 20 November 2026.",
         "Alternative walking routes", "routes.html"),
        ("Winter opening hours", "From December the visitor centre is open daily from 10 am to 4 pm.",
         "All opening hours", "hours.html"),
    ],
}


def news_box(rng, lang: str) -> str:
    h, p, lt, href = pick(rng, NEWS[lang])
    return (f'<aside class="box news-aside"><h2>{esc(h)}</h2><p>{esc(p)}</p>'
            f'<p><a href="{esc(href)}">{esc(lt)}</a></p></aside>')


def doc(rng, lang: str, title: str, main: str, *, org: str | None = None, css: str = "", head: str = "",
        chrome: bool | None = None, box: bool | None = None, raw: bool = False) -> str:
    """Full page: theme, optional site chrome, optional neutral side box after the content.

    raw=True: ``main`` is the complete body markup (no <main> wrapper, no chrome, no box)."""
    org = org or pick(rng, ORGS[lang])
    theme = pick_theme(rng)
    if chrome is None:
        chrome = rng.random() < 0.65
    if box is None:
        box = rng.random() < 0.4
    if box and not raw:
        main = main + "\n" + news_box(rng, lang)
    tag = SITE_LANG_TAG[lang] if rng.random() < 0.75 else lang
    body = main if raw else wrap(lang, org, main, chrome=chrome)
    return page(tag, f"{title} – {org}", body, theme=theme, css=css, head=head)


def mk(crit: str, rng, lang: str, expected: str, rule: str, title: str, main: str, target, notes: str, *,
       org: str | None = None, trap: bool = False, alt: str | None = None, diff: str = "medium",
       css: str = "", head: str = "", chrome: bool | None = None, box: bool | None = None,
       raw: bool = False) -> Case:
    html = doc(rng, lang, title, main, org=org, css=css, head=head, chrome=chrome, box=box, raw=raw)
    return Case(crit, lang, expected, html=html, target=target, rule=rule, notes=notes, trap=trap,
                alt_expected=alt, difficulty=diff)


def icon_svg(name: str, size: int = 24, stroke: str = "currentColor") -> str:
    """Inline decorative SVG icon (aria-hidden), children self-closed."""
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
            f'<g fill="none" stroke="{stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            f'{ICONS[name]}</g></svg>')


SR_ONLY = (".sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;"
           "clip:rect(0,0,0,0);white-space:nowrap;border:0}")
