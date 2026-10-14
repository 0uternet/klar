"""3.1.2 Language of Parts — 45 core cases (15 per page language de / fr / it) + 38 designed span cases (v3).

Decision rules: PROTOCOL.md §3.1.2. The element under test is the passage (paragraph,
quote, list item, cell, column) that contains the other-language text or the look-alike.
Exceptions (Understanding 3.1.2): proper names, technical terms, words of indeterminate
language, words or phrases that have become part of the vernacular of the surrounding text.
"""
from common import *

CRITERION = "3.1.2"

TAG = {"de": ["de", "de-CH"], "fr": ["fr", "fr-CH"], "it": ["it", "it-CH"], "en": ["en", "en-GB"]}

# ---------------------------------------------------------------------------
# Foreign passages (used as the element under test for F1/F2/F3/P1)
PASSAGES = {
    "de": [
        "Die Gemeinde Beispielwil lädt alle Interessierten herzlich zum Herbstmärit vom 7. November ein. Der Markt findet bei jeder Witterung statt.",
        "Bitte beachten Sie, dass die Gemeindeverwaltung zwischen Weihnachten und Neujahr geschlossen bleibt. In dringenden Fällen erreichen Sie den Pikettdienst rund um die Uhr.",
        "Wir danken allen Freiwilligen herzlich für ihren grossen Einsatz am Dorffest. Ohne sie wäre dieser Anlass nicht möglich gewesen.",
        "Anmeldungen nehmen wir gerne bis zum 30. November entgegen. Die Teilnehmerzahl ist auf zwanzig Personen beschränkt.",
        "Der Seeuferweg ist ab Montag wieder durchgehend begehbar. Hunde sind an der Leine zu führen.",
    ],
    "fr": [
        "La commune de Valfictif invite toute la population à la fête des vendanges du 3 octobre. Un apéritif sera servi à l'issue de la partie officielle.",
        "Les inscriptions sont ouvertes jusqu'au 30 novembre auprès de l'administration communale. Le nombre de places est limité.",
        "Nous remercions chaleureusement tous les bénévoles pour leur engagement lors de la fête du village. Sans eux, cette manifestation n'aurait pas pu avoir lieu.",
        "En raison de travaux, la route cantonale sera fermée à la circulation du 3 au 21 novembre. Une déviation est signalée par le village voisin.",
        "Le bureau communal sera exceptionnellement fermé le lundi 26 décembre. Merci de votre compréhension.",
    ],
    "it": [
        "Il Comune di Esempiano invita tutta la popolazione alla festa d'autunno di sabato 7 novembre. In caso di pioggia la manifestazione si terrà in palestra.",
        "Le iscrizioni sono aperte fino al 30 novembre presso la cancelleria comunale. Il numero dei posti è limitato.",
        "Ringraziamo di cuore tutti i volontari per il prezioso aiuto durante la festa del paese. Senza di loro la manifestazione non sarebbe stata possibile.",
        "A causa di lavori, la strada cantonale resterà chiusa al traffico dal 3 al 21 novembre. È prevista una deviazione attraverso il paese vicino.",
        "La cancelleria comunale resterà eccezionalmente chiusa lunedì 26 dicembre. Grazie per la comprensione.",
    ],
    "en": [
        "Kindly sign up at the town hall counter by the end of November. Places are limited.",
        "Guided tours in English are available every Saturday at 10 a.m. from the tourist office.",
        "Visitors are kindly asked to use public transport, as parking near the lake is very limited.",
    ],
}

# Page-language filler text
FILL = {
    "de": dict(
        h1=["Mitteilungen", "Aus der Region", "Veranstaltungen", "Gemeindenachrichten"],
        notice_h="Mitteilung der Regionalkonferenz",
        notice_intro="Die Gemeinden der Region Lindental veröffentlichen ihre Mitteilungen im Wortlaut der absendenden Gemeinde.",
        after="Bei Fragen wenden Sie sich an die Gemeindekanzlei, Telefon 032 000 12 34.",
        quote_intro="Beim Besuch der Partnergemeinde sagte die Gemeindepräsidentin in ihrer Ansprache:",
        list_h="Herbstmärit 2026 – das Wichtigste in Kürze",
        list_items=["Samstag, 7. November, 9 bis 16 Uhr", "Dorfplatz und Schulhausstrasse", "Rund 40 Stände mit regionalen Produkten"],
        table_h="Mitteilungen der Nachbargemeinden",
        table_cols=("Gemeinde", "Mitteilung"),
        own_msg="Die Sammelstelle beim Werkhof bleibt am Samstag geschlossen.",
        col_h="Gemeinsame Mitteilung",
        col_own="Die beiden Gemeinden organisieren den Winterdienst ab diesem Jahr gemeinsam. Die Schneeräumung beginnt jeweils um 5 Uhr.",
    ),
    "fr": dict(
        h1=["Communications", "Nouvelles de la région", "Manifestations", "Informations communales"],
        notice_h="Communication de la conférence régionale",
        notice_intro="Les communes de la région publient leurs communications dans la langue de la commune expéditrice.",
        after="Pour toute question, veuillez contacter le secrétariat communal au 032 000 12 34.",
        quote_intro="Lors de la visite de la commune partenaire, la syndique a déclaré dans son allocution :",
        list_h="Marché d'automne 2026 – l'essentiel en bref",
        list_items=["Samedi 7 novembre, de 9 h à 16 h", "Place du Village et rue de l'Église", "Une quarantaine de stands de produits régionaux"],
        table_h="Communications des communes voisines",
        table_cols=("Commune", "Communication"),
        own_msg="La déchetterie de la voirie restera fermée samedi.",
        col_h="Communication commune",
        col_own="Dès cette année, les deux communes organisent ensemble le service hivernal. Le déneigement commence à 5 h.",
    ),
    "it": dict(
        h1=["Comunicazioni", "Notizie dalla regione", "Manifestazioni", "Informazioni comunali"],
        notice_h="Comunicato della conferenza regionale",
        notice_intro="I comuni della regione pubblicano i loro comunicati nella lingua del comune mittente.",
        after="Per domande rivolgersi alla cancelleria comunale, telefono 091 000 12 34.",
        quote_intro="Durante la visita al comune gemellato, la sindaca ha dichiarato nel suo discorso:",
        list_h="Mercato d'autunno 2026 – in breve",
        list_items=["Sabato 7 novembre, dalle 9 alle 16", "Piazza Grande e Via alla Stazione", "Una quarantina di bancarelle con prodotti regionali"],
        table_h="Comunicati dei comuni vicini",
        table_cols=("Comune", "Comunicato"),
        own_msg="L'ecocentro del magazzino comunale resterà chiuso sabato.",
        col_h="Comunicato congiunto",
        col_own="Da quest'anno i due comuni organizzano insieme il servizio invernale. Lo sgombero della neve inizia alle 5.",
    ),
}
NEIGHBOUR = {"de": "Gemeinde Beispielwil", "fr": "Commune de Valfictif", "it": "Comune di Esempiano", "en": "Example Valley Tourism"}
GUEST_NOTE = {"de": "Hinweis für Gäste: ", "fr": "Information pour nos hôtes : ", "it": "Avviso per gli ospiti: "}

MSG_ID = ' id="msg-cell"'
COL_OWN_EN = ("From this year on, the two municipalities organise the winter road service together. "
              "Snow clearing starts at 5 a.m.")
COL_CSS =".cols{display:grid;grid-template-columns:1fr 1fr;gap:20px}.cols>div{border-top:3px solid #c9d3d8;padding-top:8px}"


def foreign_for(rng, lang):
    swiss = [l for l in ("de", "fr", "it") if l != lang]
    return pick(rng, swiss * 3 + ["en"])          # national languages ~86 %, English ~14 %


def lang_attr(value):
    return f' lang="{esc(value)}"' if value is not None else ""


def frame(rng, lang, flang, passage, tag_value, kind):
    """Embed a foreign passage as the element under test. Returns (main_html, selector)."""
    F = FILL[lang]
    la = lang_attr(tag_value)
    if kind == "notice":
        main = (f'<h1>{esc(pick(rng, F["h1"]))}</h1><section class="box"><h2>{esc(F["notice_h"])}</h2>'
                f'<p>{esc(F["notice_intro"])}</p><p id="notice-text"{la}>{esc(passage)}</p></section>'
                f'<p>{esc(F["after"])}</p>')
        return main, "#notice-text"
    if kind == "quote":
        main = (f'<h1>{esc(pick(rng, F["h1"]))}</h1><p>{esc(F["quote_intro"])}</p>'
                f'<blockquote id="speech"{la}><p>{esc(passage)}</p></blockquote><p>{esc(F["after"])}</p>')
        return main, "#speech"
    if kind == "list":
        items = [f"<li>{esc(x)}</li>" for x in F["list_items"]]
        pos = rng.randrange(len(items) + 1)
        items.insert(pos, f'<li id="guest-note"><span>{esc(GUEST_NOTE[lang])}</span><span{la}>{esc(passage)}</span></li>')
        main = f'<h1>{esc(pick(rng, F["h1"]))}</h1><h2>{esc(F["list_h"])}</h2><ul>{"".join(items)}</ul>'
        return main, "#guest-note span:nth-of-type(2)"
    if kind == "table":
        rows = [(NEIGHBOUR[lang], F["own_msg"], None), (NEIGHBOUR[flang] if flang in NEIGHBOUR else NEIGHBOUR["en"], passage, tag_value)]
        if rng.random() < 0.5:
            rows.reverse()
        trs = "".join(
            f'<tr><th scope="row">{esc(n)}</th><td{MSG_ID if t is not None or m is passage else ""}{lang_attr(t)}>{esc(m)}</td></tr>'
            for n, m, t in rows)
        main = (f'<h1>{esc(pick(rng, F["h1"]))}</h1><table><caption>{esc(F["table_h"])}</caption>'
                f'<thead><tr><th scope="col">{esc(F["table_cols"][0])}</th><th scope="col">{esc(F["table_cols"][1])}</th></tr></thead>'
                f"<tbody>{trs}</tbody></table>")
        return main, "#msg-cell"
    # two-column bilingual notice: the second column is the translation of the first
    passage = FILL[flang]["col_own"] if flang in FILL else COL_OWN_EN
    cols = [f'<div><p>{esc(F["col_own"])}</p></div>', f'<div id="col-2"{la}><p>{esc(passage)}</p></div>']
    main = (f'<h1>{esc(F["col_h"])}</h1><div class="cols">{"".join(cols)}</div><p class="muted">{esc(F["after"])}</p>')
    return main, "#col-2"


# ---------------------------------------------------------------------------
# Hand-written look-alike paragraphs (traps and cantTell), v2 after the leakage review.
# Each entry: (text, note, surface forms). Surface forms are unique across the bank, fictional where
# they are names, and absent from src/klar and from the demo site (scripts/check_leakage.py).
TRAPS = {
    "T1": {  # proper names: institutions, venues, associations, addresses (all fictional)
        "de": [
            ("Laut dem neuen Bericht der Haute école de gestion de Valfictif pendeln 38 Prozent der Erwerbstätigen in einen anderen Kanton.",
             "The French name of a (fictional) school, 'Haute école de gestion de Valfictif', is a proper name (exception).",
             ("Haute école de gestion de Valfictif",)),
            ("Die Chorprobe findet ab Januar im Saal der Brasserie des Trois Sapins an der Route de Bellevue 9 statt.",
             "Restaurant name 'Brasserie des Trois Sapins' and address 'Route de Bellevue 9' are proper names (exception).",
             ("Brasserie des Trois Sapins", "Route de Bellevue 9")),
        ],
        "fr": [
            ("La permanence juridique gratuite est assurée par la Stiftung Rechtsberatung Mustersee, Hofstattgasse 4, chaque premier mardi du mois.",
             "German foundation name and street address are proper names (exception).",
             ("Stiftung Rechtsberatung Mustersee", "Hofstattgasse 4")),
        ],
        "it": [
            ("Il corso di primo soccorso è organizzato dal Samariterverein Fiktal e si svolge nella Turnhalle Mattenhof.",
             "German association name 'Samariterverein Fiktal' and venue name 'Turnhalle Mattenhof' are proper names (exception).",
             ("Samariterverein Fiktal", "Turnhalle Mattenhof")),
        ],
    },
    "T2": {  # vernacular: helvetisms and established loanwords
        "de": [
            ("Während der Bauarbeiten wird die Bushaltestelle aufs Trottoir vor dem Coiffeur verschoben; bitte beachten Sie die Signalisation.",
             "'Trottoir', 'Coiffeur' and 'Signalisation' are Swiss Standard German vocabulary (vernacular, exception).",
             ("Trottoir", "Coiffeur", "Signalisation")),
            ("Das Jugendhaus bietet neu ein Coaching für Lehrstellensuchende an; Freiwillige begleiten die Jugendlichen im Mentoring.",
             "'Coaching' and 'Mentoring' are established loanwords in German (vernacular, exception).",
             ("Coaching", "Mentoring")),
        ],
        "fr": [
            ("Pendant le chantier, il est interdit de parquer devant le collège ; les places derrière la halle de gymnastique restent ouvertes.",
             "Swiss French 'parquer' (to park) belongs to the vernacular of the surrounding French (exception).",
             ("parquer",)),
            ("Le nouveau coach du club propose un training de fitness chaque mardi soir à la salle polyvalente.",
             "'coach', 'training' and 'fitness' are anglicisms established in French (vernacular, exception).",
             ("coach", "training", "fitness")),
        ],
        "it": [
            ("D'estate il chiosco del lido propone brunch la domenica e un happy hour con musica dal vivo il venerdì.",
             "'brunch' and 'happy hour' are anglicisms established in Italian (vernacular, exception).",
             ("brunch", "happy hour")),
        ],
    },
    "T3": {  # Latin / indeterminate language
        "fr": [
            ("Le conseil communal a siégé in corpore ; les décisions prises a posteriori seront publiées dans le prochain bulletin.",
             "Latin 'in corpore' and 'a posteriori' are words of indeterminate language / vernacular (exception).",
             ("in corpore", "a posteriori")),
        ],
        "it": [
            ("Il municipio ha nominato una commissione pro tempore; il regolamento resta valido mutatis mutandis fino alla revisione.",
             "Latin 'pro tempore' and 'mutatis mutandis' are of indeterminate language / vernacular (exception).",
             ("pro tempore", "mutatis mutandis")),
        ],
    },
    "T4": {  # personal names
        "it": [
            ("Alla cerimonia hanno partecipato il sindaco Reto Muster, la vicesindaca Corinne Probst e il presidente del consiglio comunale Marc Modèle.",
             "Personal names of German- and French-speaking persons are proper names (exception).",
             ("Reto Muster", "Corinne Probst", "Marc Modèle")),
        ],
    },
}

CANT = {
    "F4": {  # language switcher entries without lang (single words clearly intended in another language)
        "de": ("Italiano", "it"), "it": ("Deutsch", "de"),
    },
    "C2": {  # short formula / greeting that may or may not be vernacular
        "de": [("Zum Abschluss des Dorffests stösst der Gemeinderat mit allen Helferinnen und Helfern an – santé!",
                "French toast 'santé' at the end of a German sentence without lang: common in Swiss German usage, so it may be vernacular (exception) or a phrase needing lang; the doubt test gives no clear answer.",
                ("santé",))],
        "fr": [("Le marché se termine par un concert de la fanfare des Vergers. Uf Wiederluege et à l'année prochaine !",
                "Swiss German farewell 'Uf Wiederluege' inside French text without lang: a two-word formula that may be regional vernacular or a foreign phrase; debatable.",
                ("Uf Wiederluege",))],
        "it": [("La serata si conclude con una polenta per tutti i partecipanti. Bun appetit!",
                "Romansh formula 'Bun appetit' closing an Italian paragraph without lang: very close to Italian, so whether it is a foreign phrase or vernacular is debatable.",
                ("Bun appetit",)),
               ("Grazie a tutti i volontari che hanno reso possibile la festa e, come dicono i nostri vicini, merci beaucoup!",
                "French 'merci beaucoup' inside Italian text without lang: a two-word formula that may be regional vernacular or a phrase requiring lang; debatable.",
                ("merci beaucoup",))],
    },
    "C3": {  # title of a work/event in another language
        "de": ("Das Theater im Kornhaus zeigt im Januar die Komödie «Le Jardin des Voisins» in deutscher Übersetzung.",
               "French play title inside German text: title-like proper name made of ordinary French words; whether the proper-name exception applies is debatable.",
               ("Le Jardin des Voisins",)),
        "fr": ("Le cinéma en plein air projette le documentaire «Zwischen Fels und Wasser», sous-titré en français.",
               "German film title inside French text: name-like phrase made of ordinary German words; exception debatable.",
               ("Zwischen Fels und Wasser",)),
        "it": ("La biblioteca presenta il libro illustrato «Der kleine Uhrmacher», disponibile anche in traduzione italiana.",
               "German book title inside Italian text: name-like phrase made of ordinary German words; exception debatable.",
               ("Der kleine Uhrmacher",)),
    },
}


TRAP_H1 = {"de": ["Aus der Gemeinde", "Veranstaltungen", "Kurz notiert"],
           "fr": ["La vie au village", "Manifestations", "En bref"],
           "it": ["Vita in paese", "Manifestazioni", "In breve"]}


def trap_main(rng, lang, text, wrap_kind):
    h1 = pick(rng, TRAP_H1[lang])
    other = FILL[lang]["after"]
    if wrap_kind == "card":
        return (f'<h1>{esc(h1)}</h1><div class="cards"><div class="card"><p id="item-text">{esc(text)}</p></div>'
                f'<div class="card"><p>{esc(FILL[lang]["own_msg"])}</p></div></div><p>{esc(other)}</p>'), "#item-text"
    if wrap_kind == "list":
        return (f'<h1>{esc(h1)}</h1><ul><li>{esc(FILL[lang]["list_items"][0])}</li><li id="item-text">{esc(text)}</li>'
                f'<li>{esc(FILL[lang]["list_items"][2])}</li></ul>'), "#item-text"
    return f'<h1>{esc(h1)}</h1><p>{esc(FILL[lang]["notice_intro"])}</p><p id="item-text">{esc(text)}</p><p>{esc(other)}</p>', "#item-text"


def switcher_main(rng, lang, word, wlang):
    langs = {"de": "Deutsch", "fr": "Français", "it": "Italiano"}
    links = []
    for code, name in langs.items():
        if code == lang:
            links.append(f'<li><span aria-current="true">{name}</span></li>')
        else:
            idattr = ' id="lang-link"' if name == word else ""
            links.append(f'<li><a href="../{code}/index.html"{idattr}>{name}</a></li>')
    nav_label = {"de": "Sprache wählen", "fr": "Choisir la langue", "it": "Scegliere la lingua"}[lang]
    sw = f'<nav aria-label="{nav_label}" class="lang-switch"><ul style="list-style:none;display:flex;gap:10px;padding:0">{"".join(links)}</ul></nav>'
    F = FILL[lang]
    main = f"{sw}<h1>{esc(pick(rng, F['h1']))}</h1><p>{esc(F['notice_intro'])}</p><p>{esc(F['own_msg'])}</p>"
    return main, "#lang-link"


# ---------------------------------------------------------------------------
PLAN = (
    # (rule, lang, expected)
    [("F1", "de")] * 3 + [("F1", "fr")] * 3 + [("F1", "it")] * 2 +
    [("F4", "de"), ("F4", "it")] +
    [("F2", "de")] + [("F2", "fr")] * 2 + [("F2", "it")] * 2 +
    [("F3", "de"), ("F3", "fr"), ("F3", "it")] +
    [("P1", "de")] * 3 + [("P1", "fr")] * 3 + [("P1", "it")] * 2 +
    [("T1", "de")] * 2 + [("T1", "fr"), ("T1", "it")] +
    [("T2", "de")] * 2 + [("T2", "fr")] * 2 + [("T2", "it")] +
    [("T3", "fr"), ("T3", "it"), ("T4", "it")] +
    [("C2", "de"), ("C3", "de"), ("C2", "fr"), ("C3", "fr"), ("C3", "it"), ("C2", "it"), ("C2", "it")]
)
EXPECTED = {"F": "failed", "P": "passed", "T": "passed", "C": "cantTell"}
KINDS = ["notice", "quote", "list", "table", "columns"]
LANG_NAME = {"de": "German", "fr": "French", "it": "Italian", "en": "English"}
WRONG = {  # foreign language -> plausible wrong declarations (valid tags of another language)
    "fr": ["it", "de", "ch"], "it": ["fr", "es"], "de": ["en", "sw", "fr"], "en": ["de", "fr"],
}
INVALID = {"fr": ["fra", "fr.CH", "fr_suisse"], "it": ["ita", "it.CH", "it_ticino"],
           "de": ["deu", "de.CH", "de_schweiz"], "en": ["eng", "en.GB", "en_uk"]}   # unregistered 3-letter codes, bad syntax, names


def build(rng):
    cases = []
    used = {}
    kinds_cycle = {l: shuffled(rng, KINDS * 3) for l in ("de", "fr", "it")}
    pos = {"de": 0, "fr": 0, "it": 0}
    trap_idx = {}
    for rule, lang in PLAN:
        expected = EXPECTED[rule[0]]
        trap = rule.startswith("T")
        org = pick(rng, ORGS[lang][:4])
        alt = None
        css = COL_CSS
        if rule in ("F1", "F2", "F3", "P1"):  # foreign passage embedded in a frame
            flang = foreign_for(rng, lang)
            key = (lang, flang)
            i = used.get(key, rng.randrange(len(PASSAGES[flang])))
            used[key] = i + 1
            passage = PASSAGES[flang][i % len(PASSAGES[flang])]
            kind = kinds_cycle[lang][pos[lang] % len(kinds_cycle[lang])]
            pos[lang] += 1
            if rule == "F1":
                tag_value = None
                notes = f"{LANG_NAME[flang]} passage inside a page in {LANG_NAME[lang]} has no lang attribute, so it inherits '{lang}'."
                diff = "easy" if kind in ("notice", "columns") else "medium"
            elif rule == "F2":
                tag_value = pick(rng, WRONG[flang])
                notes = f"{LANG_NAME[flang]} passage is marked lang=\"{tag_value}\", which does not match its language."
                diff = "medium"
            elif rule == "F3":
                tag_value = pick(rng, INVALID[flang])
                notes = f"{LANG_NAME[flang]} passage carries lang=\"{tag_value}\", which is not a valid BCP 47 language tag."
                diff = "medium"
            else:
                tag_value = pick(rng, TAG[flang])
                notes = f"{LANG_NAME[flang]} passage is correctly marked lang=\"{tag_value}\" (H58)."
                diff = "easy"
            main, target = frame(rng, lang, flang, passage, tag_value, kind)
            template = f"passage-{flang}-{i % len(PASSAGES[flang])}"
            surface = (tag_value,) if rule == "F3" else ()
        elif rule.startswith("T"):
            k = (rule, lang)
            j = trap_idx.get(k, 0)
            trap_idx[k] = j + 1
            text, notes, surface = TRAPS[rule][lang][j % len(TRAPS[rule][lang])]
            main, target = trap_main(rng, lang, text, pick(rng, ["p", "card"]))
            diff = "hard" if rule in ("T1", "T2") else "medium"
            template = f"{rule}-{lang}-{j}"
        elif rule == "F4":
            word, wlang = CANT["F4"][lang]
            main, target = switcher_main(rng, lang, word, wlang)
            template, surface = f"switcher-{lang}", ()
            notes = (f"Language-switcher link '{word}' is written in {LANG_NAME[wlang]} but has no lang attribute; a single word "
                     "clearly intended in another language (Understanding 3.1.2 language-selector example, H58).")
            diff = "hard"
        elif rule == "C2":
            k = (rule, lang)
            j = trap_idx.get(k, 0)
            trap_idx[k] = j + 1
            text, notes, surface = CANT["C2"][lang][j % len(CANT["C2"][lang])]
            main, target = trap_main(rng, lang, text, "p")
            diff = "hard"
            template = f"C2-{lang}-{j}"
        else:  # C3
            text, notes, surface = CANT["C3"][lang]
            main, target = trap_main(rng, lang, text, pick(rng, ["p", "card"]))
            diff = "hard"
            template = f"C3-{lang}"
        chrome = rng.random() < 0.75
        body = wrap(lang, org, main, chrome=chrome)
        title = f"{pick(rng, FILL[lang]['h1'])} – {org}"
        html = page(pick(rng, TAG[lang]), title, body, rng=rng, css=css)
        cases.append(Case(CRITERION, lang, expected, html=html, target=target, rule=f"{CRITERION}/{rule}",
                          notes=notes, trap=trap, alt_expected=alt, difficulty=diff,
                          template=template, surface=surface))
    cases += extra_cases(rng)      # v3 designed span categories (appended: earlier case ids unchanged)
    return cases


# ---------------------------------------------------------------------------
# v3 (backend review, 14 Oct): designed span categories that a language-detector rule tends to
# misclassify, each present in BOTH splits (forced split, one template per case, fresh fictional
# vocabulary from the Beispielwil universe, nothing shared with the demo site).
#   A  quoted title of a work inside running text  («», „“, "", <q>, <cite>, <i>)  -> C3 cantTell
#   B  title of a work standing alone in its own paragraph                          -> C3 cantTell
#   C  institution name + street address + postcode/place in another language       -> T1 passed (trap)
#   D  address-only line in another language                                         -> T1 passed (trap)
#   E  contrast: a quoted SENTENCE in another language without lang                  -> F1 failed
#   F  contrast: the same kind of quoted sentence correctly marked with lang         -> P1 passed
# Each entry: (category, lang, split, h2, body_html, target, surface forms, note)
EXTRA = [
    # A: quoted titles in running text (C3)
    ("A", "de", "dev", "Kino im Kornhaus",
     '<p id="kino-text">Am Freitag zeigt der Filmclub den Dokumentarfilm «La mémoire des glaciers» in der Originalfassung mit deutschen Untertiteln. Der Eintritt kostet CHF 12.–.</p>',
     "#kino-text", ("La mémoire des glaciers",), "French film title in «» inside a German sentence"),
    ("A", "de", "test", "Neu in der Bibliothek",
     '<p id="neu-text">Ab sofort ausleihbar: der Roman „Il silenzio del bosco“ einer Autorin aus Valfittizia, dazu zwei neue Hörbücher für Kinder.</p>',
     "#neu-text", ("Il silenzio del bosco",), "Italian novel title in „“ inside a German sentence"),
    ("A", "fr", "dev", "Théâtre au collège",
     '<p id="theatre-texte">La troupe des Vergers joue samedi la comédie "Der falsche Gemeindeschreiber" dans une adaptation française.</p>',
     "#theatre-texte", ("Der falsche Gemeindeschreiber",), "German play title in straight quotes inside a French sentence"),
    ("A", "fr", "test", "Concert d'automne",
     '<p>Le chœur mixte interprète en ouverture le cycle <q id="concert-titre">Lieder vom alten Brunnen</q> d\'un compositeur de la région.</p>',
     "#concert-titre", ("Lieder vom alten Brunnen",), "German song-cycle title marked up with <q> inside a French sentence"),
    ("A", "it", "dev", "Serata letteraria",
     '<p>La biblioteca dedica una serata al racconto <cite id="serata-titolo">Le phare des oubliés</cite>, appena tradotto in italiano.</p>',
     "#serata-titolo", ("Le phare des oubliés",), "French story title marked up with <cite> inside an Italian sentence"),
    ("A", "it", "test", "Cineforum",
     '<p>Giovedì il cineforum propone il film <i id="cine-titolo">Die Fähre im Nebel</i>, in versione originale con sottotitoli.</p>',
     "#cine-titolo", ("Die Fähre im Nebel",), "German film title in <i> inside an Italian sentence"),
    # B: standalone title paragraph (C3)
    ("B", "de", "dev", "Ausstellung im Gemeindehaus",
     '<p class="kicker">Fotografie</p><p id="ausst-titel" class="title-line">«L\'heure bleue sur le lac»</p><p>Bis 30. November, jeweils Mittwoch bis Sonntag von 14 bis 18 Uhr.</p>',
     "#ausst-titel", ("L'heure bleue sur le lac",), "French exhibition title alone in its own paragraph of a German page"),
    ("B", "de", "test", "Gastspiel im Saal",
     '<p class="title-line" id="stueck-titel">„Sotto il cielo d\'inverno“</p><p>Eine Theatergruppe aus Esempiano spielt auf Italienisch, mit deutschen Übertiteln.</p>',
     "#stueck-titel", ("Sotto il cielo d'inverno",), "Italian play title alone in its own paragraph of a German page"),
    ("B", "fr", "dev", "Exposition à la Grange",
     '<p id="expo-titre" class="title-line">«Stille Wasser im Fiktal»</p><p>Aquarelles et dessins, du 4 au 26 novembre, entrée libre.</p>',
     "#expo-titre", ("Stille Wasser im Fiktal",), "German exhibition title alone in its own paragraph of a French page"),
    ("B", "fr", "test", "Lecture publique",
     '<p class="title-line" id="lecture-titre"><cite>Le voci del mercato</cite></p><p>Lecture bilingue par l\'autrice, suivie d\'une discussion et d\'une collation.</p>',
     "#lecture-titre", ("Le voci del mercato",), "Italian book title (<cite>) alone in its own paragraph of a French page"),
    ("B", "it", "dev", "Mostra in biblioteca",
     '<p class="title-line" id="mostra-titolo">«Schnee über den Dächern»</p><p>Fotografie d\'epoca del nucleo, visibili fino al 15 gennaio.</p>',
     "#mostra-titolo", ("Schnee über den Dächern",), "German exhibition title alone in its own paragraph of an Italian page"),
    ("B", "it", "test", "Concerto di Natale",
     '<p class="title-line" id="concerto-titolo">«Le chemin des crêtes»</p><p>Suite per coro e fiati, prima esecuzione nella chiesa parrocchiale.</p>',
     "#concerto-titolo", ("Le chemin des crêtes",), "French suite title alone in its own paragraph of an Italian page"),
    # C: institution + address (T1)
    ("C", "de", "dev", "Elternberatung",
     '<p>Die Elternberatung findet neu in den Räumen des Partnervereins statt:</p><p id="adresse-1">Association des parents d\'élèves de Valfictif, Rue des Mésanges 7, 2998 Valfictif</p>',
     "#adresse-1", ("Association des parents d'élèves de Valfictif", "Rue des Mésanges 7"), "French association name with its street address and place"),
    ("C", "de", "test", "Kontakt Sommerkurse",
     '<p>Anmeldungen für die Sommerkurse nimmt die Partnerstiftung entgegen:</p><address id="adresse-2">Fondazione Casa degli Artisti<br>Via dei Mulini 4<br>6998 Esempiano</address>',
     "#adresse-2", ("Fondazione Casa degli Artisti", "Via dei Mulini 4"), "Italian foundation name with street address and postcode/place in an <address>"),
    ("C", "de", "dev", "Musikschule",
     '<p>Den Instrumentalunterricht für Blasinstrumente übernimmt ab Februar:</p><address id="adresse-7">Scuola di musica Valfittizia<br>Piazzetta del Ponte 1<br>6997 Valfittizia</address>',
     "#adresse-7", ("Scuola di musica Valfittizia", "Piazzetta del Ponte 1"), "Italian music-school name with street address and postcode/place"),
    ("C", "fr", "dev", "Cours de musique",
     '<p id="adresse-3">Inscriptions auprès de la Musikschule Beispielwil, Lindenhofweg 2, 3998 Beispielwil, jusqu\'au 15 décembre.</p>',
     "#adresse-3", ("Musikschule Beispielwil", "Lindenhofweg 2"), "German school name and address inside a French sentence"),
    ("C", "fr", "test", "Visites de la vieille ville",
     '<p>Les visites guidées sont organisées par l\'association partenaire :</p><address id="adresse-4">Verein Altstadtfreunde Mustersee<br>Ankengasse 9<br>3997 Mustersee</address>',
     "#adresse-4", ("Verein Altstadtfreunde Mustersee", "Ankengasse 9"), "German association name with street address and postcode/place"),
    ("C", "it", "dev", "Biblioteca per ragazzi",
     '<p id="adresse-5">Prestiti interbibliotecari: Bibliothèque des Jeunes de Valfictif, Rue du Four-Banal 3, 2998 Valfictif.</p>',
     "#adresse-5", ("Bibliothèque des Jeunes de Valfictif", "Rue du Four-Banal 3"), "French library name and address after an Italian lead-in"),
    ("C", "it", "test", "Banda giovanile",
     '<p>Per le prove congiunte ci si ritrova presso la banda ospite:</p><address id="adresse-6">Jugendmusik Fiktal<br>Schützenmattstrasse 21<br>3996 Fiktal</address>',
     "#adresse-6", ("Jugendmusik Fiktal", "Schützenmattstrasse 21"), "German band name with street address and postcode/place"),
    ("C", "it", "test", "Scambio culturale",
     '<p id="adresse-8">Partner del progetto: Centre culturel de Bourg-Modèle, Place des Halles 5, 2997 Bourg-Modèle.</p>',
     "#adresse-8", ("Centre culturel de Bourg-Modèle", "Place des Halles 5"), "French cultural-centre name and address after an Italian lead-in"),
    # D: address only (T1)
    ("D", "de", "dev", "Treffpunkt Wanderung",
     '<p id="treff-1">Treffpunkt: Rue des Cerisiers 14, 2998 Valfictif, um 8.15 Uhr.</p>',
     "#treff-1", ("Rue des Cerisiers 14",), "French street address and place in a German line"),
    ("D", "de", "test", "Abholstelle",
     '<p id="treff-2">Abholung der Bestellungen: Vicolo delle Rose 6, 6998 Esempiano.</p>',
     "#treff-2", ("Vicolo delle Rose 6",), "Italian street address and place in a German line"),
    ("D", "fr", "dev", "Nouvelle adresse",
     '<p id="treff-3">Le bureau de l\'association a déménagé : Brunnmattweg 18, 3998 Beispielwil.</p>',
     "#treff-3", ("Brunnmattweg 18",), "German street address and place in a French line"),
    ("D", "fr", "test", "Point de rencontre",
     '<p id="treff-4">Rendez-vous devant l\'entrée : Via del Castagneto 11, 6997 Valfittizia.</p>',
     "#treff-4", ("Via del Castagneto 11",), "Italian street address and place in a French line"),
    ("D", "it", "dev", "Punto d'incontro",
     '<p id="treff-5">Ritrovo alle 9 in Eichholzstrasse 33, 3997 Mustersee.</p>',
     "#treff-5", ("Eichholzstrasse 33",), "German street address and place in an Italian line"),
    ("D", "it", "test", "Nuova sede",
     '<p id="treff-6">La sede del club si trova ora in Chemin des Lavandières 2, 2997 Bourg-Modèle.</p>',
     "#treff-6", ("Chemin des Lavandières 2",), "French street address and place in an Italian line"),
    # E: contrast — quoted foreign sentence without lang (F1)
    ("E", "de", "dev", "Einweihung der Passerelle",
     '<p id="zitat-1">Die Syndique von Valfictif freute sich: «Nous sommes très heureux de pouvoir enfin traverser la rivière à pied.»</p>',
     "#zitat-1", (), "a full French sentence quoted in a German paragraph without lang"),
    ("E", "de", "test", "Gemeinsames Projekt",
     '<p>Der Sindaco von Esempiano betonte bei der Feier: <q id="zitat-2">Questo ponte unisce davvero le due rive del fiume.</q></p>',
     "#zitat-2", (), "a full Italian sentence in <q> without lang in a German paragraph"),
    ("E", "de", "dev", "Grussbotschaft",
     '<p>Zum Schluss las die Präsidentin den Gruss der Partnergemeinde vor: <i id="zitat-7">Grazie di cuore per l\'accoglienza e arrivederci in primavera.</i></p>',
     "#zitat-7", (), "a full Italian sentence in <i> without lang in a German paragraph"),
    ("E", "fr", "dev", "Saison commune",
     '<p id="zitat-3">Le président du club partenaire a déclaré : „Wir freuen uns sehr auf die gemeinsame Saison mit euch.“</p>',
     "#zitat-3", (), "a full German sentence in „“ in a French paragraph without lang"),
    ("E", "fr", "test", "Rénovation terminée",
     '<p>L\'architecte a résumé le chantier en une phrase : <q id="zitat-4">Abbiamo lavorato due anni per questo risultato.</q></p>',
     "#zitat-4", (), "a full Italian sentence in <q> without lang in a French paragraph"),
    ("E", "fr", "test", "Le mot du partenaire",
     '<p id="zitat-8">Le président de Beispielwil a conclu par ces mots : «Die neue Brücke verbindet endlich beide Ortsteile.»</p>',
     "#zitat-8", (), "a full German sentence in «» in a French paragraph without lang"),
    ("E", "it", "dev", "Ringraziamenti",
     '<p id="zitat-5">Il presidente della società partner ha scritto: "Wir danken allen Helferinnen und Helfern für den grossen Einsatz am Wochenende."</p>',
     "#zitat-5", (), "a full German sentence in straight quotes in an Italian paragraph without lang"),
    ("E", "it", "test", "Visita della delegazione",
     '<p id="zitat-6">La delegazione di Bourg-Modèle ha concluso: «C\'est une belle journée pour nos deux communes.»</p>',
     "#zitat-6", (), "a full French sentence in «» in an Italian paragraph without lang"),
    # F: contrast — quoted foreign sentence with a correct lang (P1)
    ("F", "de", "dev", "Weihnachtsmarkt",
     '<p>Die Organisatoren aus Valfictif laden ein: <q id="zitat-9" lang="fr">Le marché de Noël ouvre ses portes le premier samedi de décembre.</q></p>',
     "#zitat-9", (), 'a French sentence in <q lang="fr">'),
    ("F", "fr", "dev", "Merci à nos hôtes",
     '<p>Le groupe de chant d\'Esempiano a laissé ce message : «<span id="zitat-11" lang="it">Grazie per la splendida accoglienza nel vostro villaggio.</span>»</p>',
     "#zitat-11", (), 'an Italian sentence in a <span lang="it"> inside French quotation marks'),
    ("F", "it", "test", "Iscrizioni aperte",
     '<p>Il comitato di Beispielwil comunica: <q id="zitat-10" lang="de">Die Anmeldung für den Ferienpass ist ab sofort online möglich.</q></p>',
     "#zitat-10", (), 'a German sentence in <q lang="de">'),
    ("F", "de", "test", "Besuch aus Bourg-Modèle",
     '<p>Zum Abschied schrieb die Delegation ins Gästebuch:</p><blockquote id="zitat-12" lang="fr-CH"><p>Nous reviendrons l\'an prochain avec beaucoup de plaisir.</p></blockquote>',
     "#zitat-12", (), 'a French sentence in <blockquote lang="fr-CH">'),
]
EXTRA_RULE = {"A": ("C3", "cantTell", False, "hard"), "B": ("C3", "cantTell", False, "hard"),
              "C": ("T1", "passed", True, "hard"), "D": ("T1", "passed", True, "hard"),
              "E": ("F1", "failed", False, "medium"), "F": ("P1", "passed", False, "easy")}
EXTRA_NOTE = {
    "A": "Title of a work in another language made of ordinary words ({d}); name-like but pronounced as a foreign phrase, so whether the proper-name exception applies is debatable (C3).",
    "B": "Title of a work in another language ({d}); a standalone title is still a title: name-like, pronounced as a foreign phrase, expert practice differs (C3).",
    "C": "Proper names: {d}; institution names and postal addresses are exempt from 3.1.2 (T1).",
    "D": "Proper names: {d}; a postal address is a proper name and is exempt from 3.1.2 (T1).",
    "E": "Not a name or title but {d}, so it inherits the page language: failed (F1).",
    "F": "Passage in another language correctly marked: {d} (P1).",
}


def extra_cases(rng):
    out = []
    for i, (cat, lang, split, h2, body, target, surface, desc) in enumerate(EXTRA):
        rule, expected, trap, diff = EXTRA_RULE[cat]
        F = FILL[lang]
        main = (f'<h1>{esc(pick(rng, F["h1"]))}</h1><p>{esc(F["notice_intro"])}</p>'
                f'<section class="box"><h2>{esc(h2)}</h2>{body}</section><p class="muted">{esc(F["after"])}</p>')
        org = pick(rng, ORGS[lang][:4])
        html = page(pick(rng, TAG[lang]), f"{h2} – {org}", wrap(lang, org, main, chrome=rng.random() < 0.75),
                    rng=rng, css=".title-line{font-size:1.4rem;font-weight:700;margin:.2em 0}.kicker{text-transform:uppercase;letter-spacing:.06em;font-size:.8rem;margin:0}")
        out.append(Case(CRITERION, lang, expected, html=html, target=target, rule=f"{CRITERION}/{rule}",
                        notes=EXTRA_NOTE[cat].format(d=desc), trap=trap, difficulty=diff,
                        template=f"v3-{cat}-{i:02d}", surface=surface, split=split,
                        tags=("addon", "span-category-" + cat)))
    return out
