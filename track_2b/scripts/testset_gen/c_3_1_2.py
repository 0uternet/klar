"""3.1.2 Language of Parts — 45 cases, 15 per page language (de / fr / it).

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
        "Please register before 30 November at the municipal office. Places are limited.",
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
    return cases
