"""Add-on cases from the group A review (tag "addon"): 4.1.2, 3.3.2, 1.3.5.

Designed split (dev and test for every item), excluded from the split quota, appended after all
earlier cases so existing case ids, splits and contents do not change. Labels are by construction
from PROTOCOL.md as it stands (rule ids in each case). Every case has its own scenario text, so
no dev case is a near-duplicate of a test case. Fresh fictional vocabulary (Beispielwil universe);
nothing is shared with the demo site. Listener behaviour is real inline JavaScript.
"""
from common import *

SR = ".visually-hidden{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}"
ORG = {"de": ["Gemeinde Beispielwil", "Bibliothek Mustersee", "Gemeinde Fiktal"],
       "fr": ["Commune de Valfictif", "Ville de Bourg-Modèle", "Commune d'Exempleval"],
       "it": ["Comune di Esempiano", "Città di Modellina", "Comune di Valfittizia"]}


def _page(rng, lang, title, main, css="", script=""):
    org = pick(rng, ORG[lang])
    head = f"<script>{script}</script>" if script else ""
    return page(SITE_LANG_TAG[lang], f"{title} – {org}", wrap(lang, org, main, chrome=rng.random() < 0.8),
                rng=rng, css=css + SR, head=head)


# =============================================================================== 4.1.2
SLIDER_CSS = (".slider{position:relative;max-width:560px;touch-action:pan-y;user-select:none}"
              ".slides{list-style:none;margin:0;padding:0}.slides li{display:none}.slides li.on{display:block}"
              ".slider-nav{display:flex;gap:8px;margin-top:8px}")
SLIDER_JS = """
document.addEventListener('DOMContentLoaded', function () {
  var root = document.querySelector('.slider'); var items = root.querySelectorAll('.slides li');
  var i = 0, x0 = null;
  function show(n) { items[i].classList.remove('on'); i = (n + items.length) % items.length; items[i].classList.add('on');
    document.getElementById('slide-status').textContent = (i + 1) + ' / ' + items.length; }
  root.querySelector('.prev').addEventListener('click', function () { show(i - 1); });
  root.querySelector('.next').addEventListener('click', function () { show(i + 1); });
  root.addEventListener('pointerdown', function (e) { x0 = e.clientX; });
  root.addEventListener('pointerup', function (e) { if (x0 !== null && Math.abs(e.clientX - x0) > 40) { show(e.clientX < x0 ? i + 1 : i - 1); } x0 = null; });
  root.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; }, {passive: true});
  root.addEventListener('touchend', function (e) { var x = e.changedTouches[0].clientX; if (x0 !== null && Math.abs(x - x0) > 40) { show(x < x0 ? i + 1 : i - 1); } x0 = null; });
});
"""
# (lang, split, title, captions, prev label, next label, container id, scene kinds)
SLIDERS = [
    ("de", "dev", "Rückblick Dorffest", ["Festumzug auf der Hauptgasse", "Kinderprogramm im Pfarrgarten", "Feuerwerk über dem Weiher"],
     "Vorheriges Bild", "Nächstes Bild", "fotos-dorffest", ("concert", "playground", "lake")),
    ("fr", "test", "Retour sur la fête du lac", ["Régates devant le port", "Atelier de cerfs-volants", "Bal sur la place"],
     "Image précédente", "Image suivante", "photos-fete", ("lake", "playground", "concert")),
    ("it", "dev", "La sagra in immagini", ["Corteo storico in piazza", "Laboratorio per bambini", "Concerto della filarmonica"],
     "Immagine precedente", "Immagine successiva", "foto-sagra", ("market", "playground", "concert")),
    ("de", "test", "Neues Schulhaus Rainweg", ["Eingangshalle mit Holzdecke", "Turnhalle mit Kletterwand", "Pausenplatz mit Brunnen"],
     "Zurück", "Weiter", "bilder-schulhaus", ("school", "playground", "townhall")),
]


def slider_case(rng, k, spec):
    lang, split, title, captions, prev, nxt, sid, kinds = spec
    lis = ""
    for j, c in enumerate(captions):
        cls = ' class="on"' if j == 0 else ""
        src = asset(f"slide-{sid}-{j}", scene(kinds[j], w=520, h=280, seed=40 + 3 * k + j))
        lis += f'<li{cls}><img src="{src}" alt="{esc(c)}" width="520" height="280"></li>'
    main = (f'<h1>{esc(title)}</h1><div class="slider" id="{sid}"><ul class="slides">{lis}</ul>'
            f'<div class="slider-nav"><button type="button" class="prev">{esc(prev)}</button>'
            f'<span id="slide-status" aria-live="polite">1 / {len(captions)}</span>'
            f'<button type="button" class="next">{esc(nxt)}</button></div></div>')
    return Case("4.1.2", lang, "passed", html=_page(rng, lang, title, main, SLIDER_CSS, SLIDER_JS), target=f"#{sid}",
                rule="4.1.2/P1", trap=True, difficulty="hard", split=split, template=f"ra-slider-{k}",
                tags=("addon", "review-a-4.1.2-slider"),
                notes=("The slider container has pointer and touch listeners for swiping, but it is not a separate control: "
                       "every function is provided by native, named buttons (previous/next), and the swipe only duplicates them (P1)."))


MAP_JS = """
document.addEventListener('DOMContentLoaded', function () {
  var map = document.querySelector('.map'); var x = 0, y = 0, z = 1, drag = null;
  function draw() { map.querySelector('.map-layer').style.transform = 'translate(' + x + 'px,' + y + 'px) scale(' + z + ')'; }
  map.addEventListener('keydown', function (e) {
    var s = 20; if (e.key === 'ArrowLeft') x += s; else if (e.key === 'ArrowRight') x -= s;
    else if (e.key === 'ArrowUp') y += s; else if (e.key === 'ArrowDown') y -= s;
    else if (e.key === '+') z = Math.min(3, z + 0.25); else if (e.key === '-') z = Math.max(1, z - 0.25); else return;
    e.preventDefault(); draw(); });
  map.addEventListener('pointerdown', function (e) { drag = [e.clientX - x, e.clientY - y]; });
  map.addEventListener('pointermove', function (e) { if (drag) { x = e.clientX - drag[0]; y = e.clientY - drag[1]; draw(); } });
  map.addEventListener('pointerup', function () { drag = null; });
  var zin = document.getElementById('zoom-in'), zout = document.getElementById('zoom-out');
  if (zin) zin.addEventListener('click', function () { z = Math.min(3, z + 0.25); draw(); });
  if (zout) zout.addEventListener('click', function () { z = Math.max(1, z - 0.25); draw(); });
});
"""
MAP_CSS = ".map{width:560px;max-width:100%;height:300px;overflow:hidden;border:2px solid #4f5b62;border-radius:8px}.map:focus{outline:3px solid #0b5394}.map-layer{transform-origin:center}"
# (lang, split, exposed, title, name, help, zoom in, zoom out, listed rows, scene)
MAPS = [
    ("de", "dev", True, "Sammelstellen im Gemeindegebiet", "Karte der Sammelstellen", "Pfeiltasten verschieben die Karte, Plus und Minus zoomen.",
     "Vergrössern", "Verkleinern", ["Werkhof Erlenmatt: Glas, Alu, Altöl", "Schulhaus Rainweg: Papier und Karton"], "recycling"),
    ("it", "test", True, "Punti di raccolta del comune", "Mappa dei punti di raccolta", "Le frecce spostano la mappa, più e meno ingrandiscono.",
     "Ingrandisci", "Riduci", ["Magazzino ai Ronchi: vetro, alluminio, olio", "Scuola Via Lago: carta e cartone"], "recycling"),
    ("fr", "dev", False, "Sentiers balisés autour du village", "Carte des sentiers", "Utilisez les flèches pour déplacer la carte.",
     None, None, ["Sentier des Crêtes : 2 h 30, difficulté moyenne", "Tour du Marais : 1 h, facile"], "mountain"),
    ("de", "test", False, "Velorouten rund um Fiktal", "Karte der Velorouten", "Mit den Pfeiltasten lässt sich die Karte verschieben.",
     None, None, ["Seerunde: 18 km, flach", "Hügelroute Sonnhalde: 26 km, 420 Höhenmeter"], "bridge"),
]


def map_case(rng, k, spec):
    lang, split, exposed, title, label, help_, zin, zout, rows, kind = spec
    svg = asset(f"plan-{kind}-{k}", scene(kind, w=560, h=300, seed=60 + k))
    mid = f"karte-{k}"
    if exposed:
        mapdiv = (f'<div class="map" id="{mid}" tabindex="0" role="application" aria-roledescription="{esc(label.split()[0])}" '
                  f'aria-label="{esc(label)}" aria-describedby="map-help"><div class="map-layer"><img src="{svg}" alt=""></div></div>'
                  f'<p id="map-help">{esc(help_)}</p>'
                  f'<p><button type="button" id="zoom-in">{esc(zin)}</button> <button type="button" id="zoom-out">{esc(zout)}</button></p>')
        expected, rule, alt, trap = "passed", "4.1.2/T1", None, True
        notes = ("The focusable map surface has role=application, an accessible name and its own keyboard handling; zoom is also "
                 "available through native buttons, and the locations are listed as text (custom widget exposed, T1).")
    else:
        mapdiv = (f'<p class="muted">{esc(label)}</p><div class="map" id="{mid}" tabindex="0">'
                  f'<div class="map-layer"><img src="{svg}" alt=""></div></div><p>{esc(help_)}</p>')
        expected, rule, alt, trap = "cantTell", "4.1.2/C1", "failed", False
        notes = ("A focusable map surface with pointer and arrow-key listeners has no role and no name (the caption is not "
                 "associated). Whether a pan surface is a user-interface component that needs a role (application, region …) is "
                 "debated; the routes are also given as text below (C1).")
    lst = "<ul>" + "".join(f"<li>{esc(r)}</li>" for r in rows) + "</ul>"
    main = f"<h1>{esc(title)}</h1>{mapdiv}{lst}"
    return Case("4.1.2", lang, expected, html=_page(rng, lang, title, main, MAP_CSS, MAP_JS), target=f"#{mid}",
                rule=rule, trap=trap, alt_expected=alt, difficulty="hard", split=split, template=f"ra-map-{k}",
                tags=("addon", "review-a-4.1.2-map"), notes=notes)


CARD_JS = """
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.event-card').forEach(function (card) {
    var link = card.querySelector('a');
    card.addEventListener('click', function (e) { if (e.target.closest('a')) return; window.location.href = link.href; });
  });
});
"""
CARD_CSS = ".event-card{cursor:pointer;border:1px solid #c9d3d8;border-radius:10px;padding:12px;margin-bottom:12px}.event-card:hover{background:#f1f2f5}"
CARDS = [
    ("fr", "dev", "Agenda de décembre", [("Concert de l'Avent du chœur d'enfants", "dimanche 6 décembre, 17 h, temple de Valfictif", "concert-avent.html"),
                                         ("Atelier de biscuits de Noël", "mercredi 9 décembre, 14 h, salle des Tilleuls", "atelier-biscuits.html")]),
    ("it", "test", "Appuntamenti di dicembre", [("Concerto dell'Avvento", "domenica 6 dicembre, ore 17, chiesa di Esempiano", "concerto-avvento.html"),
                                                ("Laboratorio di candele", "mercoledì 9 dicembre, ore 14, sala ai Ronchi", "laboratorio-candele.html")]),
    ("de", "dev", "Kurse im Frühling", [("Obstbaumschnitt für Einsteiger", "Samstag, 7. März, 9 Uhr, Hofstatt Lindenweg", "obstbaumschnitt.html"),
                                        ("Erste Hilfe bei Hunden", "Dienstag, 17. März, 19 Uhr, Werkhof Erlenmatt", "erste-hilfe-hund.html")]),
    ("fr", "test", "Offres de la bibliothèque", [("Club de lecture des ados", "un jeudi sur deux, 16 h 30, bibliothèque de Bourg-Modèle", "club-lecture.html"),
                                                 ("Heure du conte en famille", "samedi 21 mars, 10 h, coin des petits", "heure-du-conte.html")]),
]


def card_case(rng, k, spec):
    lang, split, title, items = spec
    cards = "".join(f'<article class="event-card" id="karte-anlass-{j + 1}"><h2><a href="{href}">{esc(t)}</a></h2><p>{esc(d)}</p></article>'
                    for j, (t, d, href) in enumerate(items))
    main = f"<h1>{esc(title)}</h1>{cards}"
    return Case("4.1.2", lang, "passed", html=_page(rng, lang, title, main, CARD_CSS, CARD_JS), target="#karte-anlass-1",
                rule="4.1.2/T4", trap=True, difficulty="hard", split=split, template=f"ra-card-{k}",
                tags=("addon", "review-a-4.1.2-card"),
                notes=("The whole card has a click listener, but it only repeats the action of the native link in the card heading; "
                       "the card is not focusable and keyboard / assistive-technology users operate the exposed link (redundant "
                       "mouse-only target duplicated by a native link, T4)."))


DIVBTN_JS = """
document.addEventListener('DOMContentLoaded', function () {
  var b = document.querySelector('.action-clear');
  b.addEventListener('click', function () { document.querySelector('.saved').innerHTML = ''; document.getElementById('saved-msg').textContent = b.dataset.done; });
});
"""
DIVBTNS = [
    ("it", "dev", "I miei preferiti", ["Modulo cani", "Scheda scarti vegetali", "Regolamento cimitero"], "Svuota l'elenco", "L'elenco è vuoto."),
    ("de", "test", "Meine Merkliste", ["Formular Hundeanmeldung", "Merkblatt Grüngut", "Reglement Friedhof"], "Merkliste leeren", "Die Merkliste ist leer."),
    ("fr", "dev", "Mon panier de cartes journalières", ["Carte journalière du 12 mars", "Carte journalière du 19 mars"], "Vider le panier", "Le panier est vide."),
    ("it", "test", "Prenotazioni sala multiuso", ["Sabato 14 marzo, sera", "Domenica 22 marzo, pomeriggio"], "Annulla tutte le prenotazioni", "Nessuna prenotazione."),
]


def divbtn_case(rng, k, spec):
    lang, split, title, items, label, done = spec
    main = (f"<h1>{esc(title)}</h1><ul class=\"saved\">" + "".join(f"<li>{esc(x)}</li>" for x in items) + "</ul>"
            f'<div class="action-clear btn-look" id="liste-leeren" data-done="{esc(done)}">{esc(label)}</div><p id="saved-msg" aria-live="polite"></p>')
    css = ".btn-look{display:inline-block;padding:8px 16px;border-radius:6px;background:#2f5d34;color:#ffffff;cursor:pointer}"
    return Case("4.1.2", lang, "failed", html=_page(rng, lang, title, main, css, DIVBTN_JS), target="#liste-leeren",
                rule="4.1.2/F1", difficulty="medium", split=split, template=f"ra-divbtn-{k}",
                tags=("addon", "review-a-4.1.2-divbutton"),
                notes=("A div with a click listener is the only way to perform this action: it acts as a button but has no role and "
                       "no tabindex, so its role is not exposed and it cannot be reached by keyboard (F1)."))


def cases_4_1_2(rng):
    out = [slider_case(rng, k, s) for k, s in enumerate(SLIDERS)]
    out += [map_case(rng, k, s) for k, s in enumerate(MAPS)]
    out += [card_case(rng, k, s) for k, s in enumerate(CARDS)]
    out += [divbtn_case(rng, k, s) for k, s in enumerate(DIVBTNS)]
    return out


# =============================================================================== 3.3.2
FORM_CSS = ".fld{margin:10px 0}.hint{display:block;font-size:.9rem;color:#4f5b62}"
REQ = {"de": "* Pflichtfeld", "fr": "* Champ obligatoire", "it": "* Campo obbligatorio"}
SUBMIT = {"de": "Absenden", "fr": "Envoyer", "it": "Invia"}
PAT_PLZ = ' inputmode="numeric" pattern="[0-9]{4}" autocomplete="postal-code"'
PAT_YEAR = ' inputmode="numeric" pattern="(19|20)[0-9]{2}" autocomplete="bday-year"'
PAT_AHV = r' pattern="756\.[0-9]{4}\.[0-9]{4}\.[0-9]{2}"'
HINT = {"de": "Format: 756.1234.5678.97 (mit Punkten, wie auf dem Versicherungsausweis)",
        "fr": "Format : 756.1234.5678.97 (avec les points, comme sur la carte d'assurance)",
        "it": "Formato: 756.1234.5678.97 (con i punti, come sulla tessera d'assicurazione)"}

# item, lang, split, h1, intro, other fields [(id, label, attrs)], target (id, label)
FORMS = [
    # postcode with a 4-digit pattern, no hint -> passed (obvious format)
    ("postcode", "de", "dev", "Parkkarte für Anwohnende", "Bestellen Sie die Jahreskarte für die blaue Zone in Ihrem Quartier.",
     [("vorname", "Vorname", ' autocomplete="given-name"'), ("nachname", "Nachname", ' autocomplete="family-name"')], ("plz", "PLZ")),
    ("postcode", "fr", "test", "Ramassage des encombrants", "Annoncez un ramassage d'objets encombrants devant votre domicile.",
     [("rue", "Rue et numéro", ' autocomplete="street-address"'), ("ort-enc", "Localité", ' autocomplete="address-level2"')], ("npa", "NPA")),
    ("postcode", "it", "dev", "Contrassegno per residenti", "Ordinate il contrassegno annuale per la zona blu del vostro quartiere.",
     [("nome", "Nome", ' autocomplete="given-name"'), ("cognome", "Cognome", ' autocomplete="family-name"')], ("nap", "NAP")),
    ("postcode", "de", "test", "Kompostberatung vor Ort", "Unsere Beraterin besucht Ihren Garten kostenlos; geben Sie die Adresse an.",
     [("strasse", "Strasse und Hausnummer", ' autocomplete="street-address"'), ("ort", "Ort", ' autocomplete="address-level2"')], ("plz-garten", "PLZ")),
    # birth year 4 digits -> passed (obvious format)
    ("birthyear", "fr", "dev", "Sortie des aînés 2027", "Inscrivez-vous à l'excursion en car au lac de Valfictif.",
     [("nom-ins", "Nom et prénom", ' autocomplete="name"')], ("annee", "Année de naissance")),
    ("birthyear", "it", "test", "Gita degli anziani 2027", "Iscrivetevi alla gita in torpedone sul lago di Esempiano.",
     [("nome-isc", "Nome e cognome", ' autocomplete="name"')], ("anno", "Anno di nascita")),
    ("birthyear", "de", "dev", "Jahrgängertreffen 1966", "Melden Sie sich für das Treffen im Restaurant Sonnhalde an.",
     [("name-anm", "Name und Vorname", ' autocomplete="name"'), ("mail-anm", "E-Mail", ' type="email" autocomplete="email"')], ("jahrgang", "Jahrgang")),
    ("birthyear", "fr", "test", "Cours de natation pour adultes", "Inscription aux cours du mardi soir à la piscine couverte.",
     [("nom-nat", "Nom de famille", ' autocomplete="family-name"'), ("prenom-nat", "Prénom usuel", ' autocomplete="given-name"'),
      ("niveau", "Niveau de natation actuel", ""), ("jour", "Soir de cours souhaité", "")], ("an-naiss", "Année de naissance du participant")),
    # social-insurance number with separators in the pattern, no hint -> failed (F3)
    ("sv", "it", "dev", "Richiesta di sussidio", "Compilate la richiesta di riduzione dei premi per l'anno 2027.",
     [("nome2", "Nome", ' autocomplete="given-name"'), ("cognome2", "Cognome", ' autocomplete="family-name"')], ("num-avs", "Numero AVS")),
    ("sv", "de", "test", "Antrag Prämienverbilligung", "Füllen Sie den Antrag für das Jahr 2027 vollständig aus.",
     [("vorname2", "Vorname", ' autocomplete="given-name"'), ("nachname2", "Nachname", ' autocomplete="family-name"')], ("ahv-nr", "AHV-Nummer")),
    ("sv", "fr", "dev", "Allocations familiales", "Annoncez la naissance de votre enfant pour recevoir l'allocation.",
     [("enfant", "Prénom de l'enfant", ""), ("naissance-enf", "Date de naissance de l'enfant", ' type="date"')], ("avs-parent", "Numéro AVS du parent")),
    ("sv", "it", "test", "Iscrizione alla cassa pensioni comunale", "Nuovi collaboratori: inviate i dati per l'affiliazione.",
     [("funzione", "Funzione", ' autocomplete="organization-title"'), ("entrata", "Data d'entrata", ' type="date"')], ("avs-collab", "Numero AVS")),
    # same pattern with a visible hint -> passed (P1)
    ("sv-hint", "de", "dev", "Gesuch Kinderbetreuungsbeitrag", "Für die Kita-Beiträge 2027 benötigen wir folgende Angaben.",
     [("kind-name", "Name des Kindes", ""), ("kita", "Kindertagesstätte", "")], ("ahv-eltern", "AHV-Nummer eines Elternteils")),
    ("sv-hint", "fr", "test", "Demande de bourse d'études", "Les apprentis et étudiants domiciliés dans la commune peuvent déposer une demande.",
     [("ecole", "École ou entreprise formatrice", ""), ("debut", "Début de la formation", ' type="date"')], ("avs-etud", "Numéro AVS")),
    ("sv-hint", "it", "dev", "Rimborso spese di trasporto scolastico", "Le famiglie della frazione di Valfittizia possono chiedere il rimborso.",
     [("allievo", "Nome dell'allievo", ""), ("classe", "Classe", "")], ("avs-gen", "Numero AVS del genitore")),
    ("sv-hint", "de", "test", "Anmeldung Freiwilligenarbeit", "Für die Haftpflichtversicherung der Freiwilligen brauchen wir Ihre Nummer.",
     [("einsatz", "Gewünschter Einsatz", ""), ("verfueg", "Verfügbarkeit pro Monat", ""), ("sprachen", "Sprachkenntnisse", "")],
     ("ahv-frei", "AHV-Nummer", "Bitte mit Punkten eingeben, zum Beispiel 756.9217.0769.85; die Nummer steht auf der Krankenkassenkarte.")),
]


def _fld(fid, label, attrs_, hint=None, req=True):
    star = " *" if req else ""
    h = f'<span class="hint" id="{fid}-hint">{esc(hint)}</span>' if hint else ""
    desc = f' aria-describedby="{fid}-hint"' if hint else ""
    return (f'<div class="fld"><label for="{fid}">{esc(label)}{star}</label>{h}'
            f'<input id="{fid}" name="{fid}"{attrs_}{desc}{" required" if req else ""}></div>')


def form332(rng, k, spec):
    item, lang, split, h1, intro, others, target = spec
    tid, tlabel = target[0], target[1]
    fields = "".join(_fld(fid, lab, at) for fid, lab, at in others)
    pat = {"postcode": PAT_PLZ, "birthyear": PAT_YEAR}.get(item, PAT_AHV)
    hint = (target[2] if len(target) > 2 else HINT[lang]) if item == "sv-hint" else None
    fields += _fld(tid, tlabel, pat, hint=hint)
    main = (f"<h1>{esc(h1)}</h1><p>{esc(intro)}</p><p class=\"muted\">{REQ[lang]}</p>"
            f'<form action="danke.html" method="get">{fields}<p><button type="submit">{SUBMIT[lang]}</button></p></form>')
    if item == "postcode":
        exp, rule, trap, diff = "passed", "3.3.2/P1", True, "hard"
        notes = ("The postcode field enforces 4 digits without a format hint, but a 4-digit Swiss postcode is the standard, obvious "
                 "format of a field labelled PLZ/NPA/NAP, not a non-obvious author format (F3 does not apply; visible label, P1).")
    elif item == "birthyear":
        exp, rule, trap, diff = "passed", "3.3.2/P1", True, "hard"
        notes = ("The birth-year field accepts a 4-digit year without a hint; a year of birth has an obvious format, so no "
                 "instruction is needed beyond the visible label (F3 does not apply, P1).")
    elif item == "sv-hint":
        exp, rule, trap, diff = "passed", "3.3.2/P1", False, "easy"
        notes = "The social-insurance number field enforces dots as separators and the required format is stated in a visible hint (G89, P1)."
    else:
        exp, rule, trap, diff = "failed", "3.3.2/F3", False, "medium"
        notes = ("The social-insurance number field enforces a pattern with dots (756.xxxx.xxxx.xx) but no visible instruction "
                 "states this format; entries without dots are rejected (F3).")
    return Case("3.3.2", lang, exp, html=_page(rng, lang, h1, main, FORM_CSS), target=f"#{tid}", rule=rule, trap=trap,
                difficulty=diff, split=split, template=f"ra-332-{k}", tags=("addon", f"review-a-3.3.2-{item}"), notes=notes)


def cases_3_3_2(rng):
    return [form332(rng, k, s) for k, s in enumerate(FORMS)]


# =============================================================================== 1.3.5
# (lang, split, with_user_field, h1, intro, code label, button, e-mail label)
WIFI = [
    ("de", "dev", False, "Gäste-WLAN im Gemeindesaal", "Geben Sie den Zugangscode ein, der auf Ihrem Eintrittsbillett für den Neujahrsempfang steht.",
     "Zugangscode Gäste-WLAN", "WLAN freischalten", None),
    ("fr", "test", False, "Wi-Fi invités de la salle communale", "Saisissez le code d'accès imprimé sur votre billet pour la soirée de gala.",
     "Code d'accès Wi-Fi invités", "Activer le Wi-Fi", None),
    ("it", "dev", True, "Wi-Fi ospiti della sala multiuso", "Inserite il codice d'accesso stampato sul biglietto della serata di gala.",
     "Codice d'accesso Wi-Fi ospiti", "Attiva il Wi-Fi", "E-mail per la conferma"),
    ("de", "test", True, "Internet im Hallenbad", "Der Tagescode für das Besucher-Netz hängt an der Kasse aus.",
     "Tagescode Besucher-Netz", "Verbinden", "E-Mail für Hinweise zur Badeordnung"),
]
# (lang, split, h1, intro, user label, password label, button)
LOGIN = [
    ("fr", "dev", "Connexion au guichet citoyen", "Connectez-vous avec votre nom d'utilisateur et votre mot de passe.", "Nom d'utilisateur", "Mot de passe", "Se connecter"),
    ("it", "test", "Accesso allo sportello cittadini", "Accedete con il vostro nome utente e la vostra password.", "Nome utente", "Password", "Accedi"),
    ("de", "dev", "Login Vereinsportal", "Vereinsvorstände melden hier ihre Anlässe für den Gemeindekalender.", "Benutzername", "Passwort", "Einloggen"),
    ("fr", "test", "Espace locataires des jardins familiaux", "Accédez à votre parcelle et à vos factures.", "Identifiant", "Mot de passe", "Entrer"),
]


def wifi_case(rng, k, spec):
    lang, split, user, h1, intro, lab, btn, mail = spec
    fields = f'<div class="fld"><label for="wlan-code">{esc(lab)}</label><input type="password" id="wlan-code" name="code"></div>'
    if user:
        fields += f'<div class="fld"><label for="mail-best">{esc(mail)}</label><input type="email" id="mail-best" name="mail" autocomplete="email"></div>'
    main = f'<h1>{esc(h1)}</h1><p>{esc(intro)}</p><form action="wlan.html" method="get">{fields}<p><button type="submit">{esc(btn)}</button></p></form>'
    if user:
        exp, rule = "passed", "1.3.5/T2"
        notes = ("The password-type field holds a shared venue access code, not the user's own credential: its purpose is not "
                 "one of the §7 input purposes, so no autocomplete is needed; the user's own e-mail field is tagged (T2).")
    else:
        exp, rule = "inapplicable", "1.3.5/N1"
        notes = ("The only field is a shared venue Wi-Fi access code printed on the ticket, not information about the user; "
                 "no field collects information about the user, so 1.3.5 does not apply (N1).")
    return Case("1.3.5", lang, exp, html=_page(rng, lang, h1, main, ".fld{margin:10px 0}"), target="#wlan-code", rule=rule, trap=True,
                difficulty="hard", split=split, template=f"ra-135-wifi-{k}", tags=("addon", "review-a-1.3.5-wifi"), notes=notes)


def login_case(rng, k, spec):
    lang, split, h1, intro, ulab, plab, btn = spec
    fields = (f'<div class="fld"><label for="benutzer">{esc(ulab)}</label><input id="benutzer" name="user" autocomplete="username"></div>'
              f'<div class="fld"><label for="kennwort">{esc(plab)}</label><input type="password" id="kennwort" name="pw"></div>')
    main = f'<h1>{esc(h1)}</h1><p>{esc(intro)}</p><form action="portal.html" method="post">{fields}<p><button type="submit">{esc(btn)}</button></p></form>'
    return Case("1.3.5", lang, "failed", html=_page(rng, lang, h1, main, ".fld{margin:10px 0}"), target="#kennwort", rule="1.3.5/F1",
                difficulty="medium", split=split, template=f"ra-135-login-{k}", tags=("addon", "review-a-1.3.5-login"),
                notes=("The login form's password field holds the user's own current password, a §7 purpose "
                       "(current-password), but has no autocomplete attribute (F1)."))


def cases_1_3_5(rng):
    return [wifi_case(rng, k, s) for k, s in enumerate(WIFI)] + [login_case(rng, k, s) for k, s in enumerate(LOGIN)]


BUILDERS = {"4.1.2": cases_4_1_2, "3.3.2": cases_3_3_2, "1.3.5": cases_1_3_5}


def cases_for(criterion: str, rng) -> list:
    fn = BUILDERS.get(criterion)
    return fn(rng) if fn else []
