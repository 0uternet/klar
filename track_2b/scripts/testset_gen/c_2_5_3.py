"""2.5.3 Label in Name – hand-written scenarios (see protocol_parts/2.5.3.md)."""
from common import *
from _structure_util import mk, icon_svg

CRITERION = "2.5.3"

BTN_CSS = (".btn{display:inline-block;padding:8px 16px;border-radius:6px;text-decoration:none;font-weight:600}"
           "form{max-width:540px}")


def _c(rng, lang, expected, rule, title, main, target, notes, **kw):
    css = BTN_CSS + kw.pop("css", "")
    return mk(CRITERION, rng, lang, expected, rule, title, main, target, notes, css=css, **kw)


def _ski_banner() -> str:
    base = scene("snow", w=420, h=200, seed=11)
    overlay = ('<rect x="270" y="150" width="140" height="34" rx="6" fill="#ffffff" opacity="0.9"/>'
               '<text x="282" y="173" font-family="Arial, sans-serif" font-size="15" font-weight="700" fill="#0b4f6c">Inscriptions 2027</text>')
    return base[:-len("</svg>")] + overlay + "</svg>"


# ---------------------------------------------------------------------------
# failed
# ---------------------------------------------------------------------------

def f_senden_de(rng):
    main = """<h1>Kontakt Einwohnerdienste</h1>
<form action="nachricht-danke.html" method="post">
<label for="kd-name">Name</label>
<input id="kd-name" name="kd-name" type="text" autocomplete="name">
<label for="kd-nachricht">Ihre Nachricht</label>
<textarea id="kd-nachricht" name="kd-nachricht" rows="4"></textarea>
<p><button type="submit" id="kd-senden" aria-label="Nachricht übermitteln">Senden</button></p>
</form>"""
    return _c(rng, "de", "failed", "2.5.3/F1", "Kontakt", main, "#kd-senden",
              "The button shows 'Senden' but its accessible name is 'Nachricht übermitteln', which does not contain the visible label (F96).",
              org="Gemeinde Ober-Beispielwil", diff="easy")


def f_suche_de(rng):
    css = ".suchform{display:flex;gap:8px;align-items:flex-end}.suchform label{margin-top:0}"
    main = """<h1>Reglemente und Verordnungen</h1>
<form class="suchform" action="suche.html" method="get" role="search">
<div><label for="reg-q">Suchbegriff</label><input id="reg-q" name="q" type="search"></div>
<button type="submit" id="reg-suche" aria-label="Finden">Suche</button>
</form>
<ul><li><a href="abfallreglement.pdf">Abfallreglement (PDF)</a></li><li><a href="gebuehrenreglement.pdf">Gebührenreglement (PDF)</a></li></ul>"""
    return _c(rng, "de", "failed", "2.5.3/F1", "Reglemente", main, "#reg-suche",
              "The visible button text is 'Suche' while aria-label overrides the name with 'Finden'; a speech user saying 'Suche' cannot activate it (F96).",
              org="Gemeinde Fiktal", css=css, diff="easy")


def f_pdf_fr(rng):
    main = """<h1>Publications</h1>
<section class="card" id="rapport">
<h2>Rapport de gestion 2025</h2>
<p>Comptes, investissements et activités des services communaux en 2025 (48 pages).</p>
<p><a href="rapport-gestion-2025.pdf" id="dl-rapport" class="btn" aria-label="Rapport annuel 2025">Télécharger le PDF</a></p>
</section>"""
    return _c(rng, "fr", "failed", "2.5.3/F1", "Publications", main, "#dl-rapport",
              "The link reads 'Télécharger le PDF' on screen but its accessible name is only 'Rapport annuel 2025', which does not contain the visible words (F96).",
              org="Commune d'Exempleval", diff="medium")


def f_iscriviti_it(rng):
    css = ".nl{display:flex;gap:8px;align-items:flex-end;flex-wrap:wrap}.nl label{margin-top:0}"
    main = """<h1>Biblioteca di Modellina</h1>
<p>Nuovi arrivi, letture per bambini e incontri con autori: ogni mese nella nostra newsletter.</p>
<form class="nl" action="newsletter-ok.html" method="post">
<div><label for="nl-mail">Indirizzo e-mail</label><input id="nl-mail" name="nl-mail" type="email" autocomplete="email"></div>
<button type="submit" id="nl-iscriviti" aria-label="Registrazione alla newsletter">Iscriviti</button>
</form>"""
    return _c(rng, "it", "failed", "2.5.3/F1", "Newsletter", main, "#nl-iscriviti",
              "Visible label 'Iscriviti', accessible name 'Registrazione alla newsletter': the name does not contain the visible text (F96).",
              org="Biblioteca di Modellina", css=css, diff="easy")


def f_order_fr(rng):
    css = ".tuiles a{display:block;padding:14px;border:1px solid #c9d3d8;border-radius:8px;text-decoration:none;font-weight:600}"
    main = """<h1>Piscine couverte</h1>
<div class="cards tuiles">
<a href="horaires-tarifs.html" id="tuile-horaires" aria-label="Tarifs et horaires">Horaires et tarifs</a>
<a href="cours-natation.html">Cours de natation</a>
<a href="acces.html">Accès et parking</a>
</div>"""
    return _c(rng, "fr", "failed", "2.5.3/F2", "Piscine couverte", main, "#tuile-horaires",
              "The accessible name uses the visible words in a different order ('Tarifs et horaires' vs 'Horaires et tarifs'), so the visible label string is not contained in the name (ACT 2ee8b8).",
              org="Ville de Bourg-Modèle", css=css, diff="hard")


def f_input_cap_it(rng):
    main = """<h1>Calendario della raccolta rifiuti</h1>
<p>Inserisci il codice postale per vedere le date di raccolta della tua zona.</p>
<form action="calendario.html" method="get">
<label for="cp">Codice postale</label>
<input id="cp" name="cp" type="text" inputmode="numeric" aria-label="CAP">
<p><button type="submit">Mostra le date</button></p>
</form>"""
    return _c(rng, "it", "failed", "2.5.3/F1", "Calendario raccolta", main, "#cp",
              "The field's visible label is 'Codice postale', but aria-label='CAP' overrides it, so the accessible name does not contain the visible label (F96).",
              org="Comune di Esempiano", diff="medium")


def f_labelledby_heading_de(rng):
    main = """<h1>Aktuelles</h1>
<article class="card">
<h2 id="titel-hallenbad">Sanierung Hallenbad</h2>
<p>Das Hallenbad bleibt vom 1. März bis 30. September 2027 geschlossen. Die Schulen weichen nach Mustersee aus.</p>
<p><a href="hallenbad-sanierung.html" id="mehr-hallenbad" aria-labelledby="titel-hallenbad">Mehr erfahren</a></p>
</article>"""
    return _c(rng, "de", "failed", "2.5.3/F1", "Aktuelles", main, "#mehr-hallenbad",
              "aria-labelledby replaces the link's name with the heading 'Sanierung Hallenbad'; the visible link text 'Mehr erfahren' is not part of the name (F96).",
              org="Stadt Mustersee", diff="hard")


def f_checkbox_de(rng):
    css = ".zustimmung{display:flex;gap:8px;align-items:flex-start;margin-top:14px}.zustimmung label{margin-top:0;font-weight:400}"
    main = """<h1>Online-Schalter: Konto eröffnen</h1>
<form action="konto-eroeffnet.html" method="post">
<label for="ks-email">E-Mail</label>
<input id="ks-email" name="ks-email" type="email" autocomplete="email">
<div class="zustimmung"><input type="checkbox" id="nutzung" name="nutzung" aria-label="AGB akzeptieren"><label for="nutzung">Ich akzeptiere die Nutzungsbedingungen</label></div>
<p><button type="submit">Konto eröffnen</button></p>
</form>"""
    return _c(rng, "de", "failed", "2.5.3/F1", "Konto eröffnen", main, "#nutzung",
              "The checkbox's visible label 'Ich akzeptiere die Nutzungsbedingungen' is overridden by aria-label 'AGB akzeptieren', which does not contain it (F96).",
              org="Gemeinde Beispielwil", css=css, diff="medium")


def f_english_name_fr(rng):
    css = ".recherche{display:flex;gap:8px;align-items:flex-end}.recherche label{margin-top:0}"
    main = """<h1>Recherche dans le site</h1>
<form class="recherche" action="recherche.html" method="get" role="search">
<div><label for="site-q">Rechercher sur le site</label><input id="site-q" name="q" type="search" aria-label="Search"></div>
<button type="submit">Rechercher</button>
</form>"""
    return _c(rng, "fr", "failed", "2.5.3/F1", "Recherche", main, "#site-q",
              "The visible label is 'Rechercher sur le site' but a leftover English aria-label='Search' becomes the accessible name, which does not contain the visible text (F96).",
              org="Commune de Valfictif", css=css, diff="medium")


def f_tab_it(rng):
    css = (".schede{display:flex;gap:4px;border-bottom:2px solid #1f6f8b}.schede button{border-radius:6px 6px 0 0;"
           "background:#ffffff;color:#1d2327;border:1px solid #1f6f8b}.schede button[aria-pressed=\"true\"]{background:#1f6f8b;color:#ffffff}")
    main = """<h1>Sentiero didattico del castagno</h1>
<div class="schede">
<button type="button" id="scheda-descrizione" aria-pressed="true">Descrizione</button>
<button type="button" id="scheda-mappa" aria-pressed="false" aria-label="Cartina del percorso">Mappa</button>
</div>
<p>Un percorso di 4 km con dodici pannelli sulla coltura del castagno, adatto anche alle famiglie.</p>"""
    return _c(rng, "it", "failed", "2.5.3/F1", "Sentiero del castagno", main, "#scheda-mappa",
              "The button reads 'Mappa' but is named 'Cartina del percorso'; the visible word is not part of the accessible name (F96).",
              org="Comune di Valfittizia", css=css, diff="medium")


# ---------------------------------------------------------------------------
# passed
# ---------------------------------------------------------------------------

def p_same_de(rng):
    main = """<h1>Anmeldung Neuzuzüger-Apéro</h1>
<p>Die Gemeinde lädt alle Neuzugezogenen am 20. November 2026 um 18.30 Uhr zu einem Apéro ins Gemeindehaus ein.</p>
<form action="apero-danke.html" method="post">
<label for="ap-name">Name</label>
<input id="ap-name" name="ap-name" type="text" autocomplete="name">
<p><button type="submit" id="ap-anmelden" aria-label="Anmelden">Anmelden</button></p>
</form>"""
    return _c(rng, "de", "passed", "2.5.3/P1", "Neuzuzüger-Apéro", main, "#ap-anmelden",
              "The aria-label repeats the visible text exactly (G211).",
              org="Gemeinde Beispielberg", diff="easy")


def p_label_fr(rng):
    main = """<h1>Alerte travaux</h1>
<p>Recevez un courriel lorsqu'un chantier commence dans votre rue.</p>
<form action="alerte-ok.html" method="post">
<label for="al-courriel">Adresse e-mail</label>
<input id="al-courriel" name="al-courriel" type="email" autocomplete="email">
<p><button type="submit">Activer l'alerte</button></p>
</form>"""
    return _c(rng, "fr", "passed", "2.5.3/P1", "Alerte travaux", main, "#al-courriel",
              "The input's name comes from its visible <label>, so name and label are identical (G208/H44).",
              org="Ville de Bourg-Modèle", diff="easy")


def p_link_it(rng):
    main = """<h1>Iscrizione alla scuola dell'infanzia</h1>
<p>Le iscrizioni per l'anno scolastico 2027/28 sono aperte fino al 31 gennaio 2027.</p>
<p><a href="iscrizione-infanzia.pdf" id="modulo-infanzia">Scarica il modulo d'iscrizione</a> (PDF, 90 kB)</p>"""
    return _c(rng, "it", "passed", "2.5.3/P1", "Scuola dell'infanzia", main, "#modulo-infanzia",
              "The link's accessible name is its visible text (name from content).",
              org="Scuola di Esempiano", diff="easy")


def p_labelledby_de(rng):
    css = ".feldtitel{display:block;font-weight:600;margin-top:12px}"
    main = """<h1>Hundemarke bestellen</h1>
<form action="hundemarke.html" method="post">
<span class="feldtitel" id="txt-wohnort">Wohnort</span>
<input id="wohnort-hund" name="wohnort" type="text" aria-labelledby="txt-wohnort">
<span class="feldtitel" id="txt-hundename">Name des Hundes</span>
<input id="hundename" name="hundename" type="text" aria-labelledby="txt-hundename">
<p><button type="submit">Bestellen</button></p>
</form>"""
    return _c(rng, "de", "passed", "2.5.3/P1", "Hundemarke", main, "#wohnort-hund",
              "aria-labelledby points to the visible text 'Wohnort', so the accessible name equals the visible label.",
              org="Gemeinde Fiktal", css=css, diff="medium")


def p_labelledby_extra_it(rng):
    main = """<h1>Corsi di nuoto</h1>
<section class="card">
<h2 id="tit-adulti">Corso di nuoto per adulti</h2>
<p>Dieci lezioni il martedì sera, dalle 19.00 alle 20.00, CHF 180.–.</p>
<p><button type="button" id="iscr-adulti" aria-labelledby="iscr-adulti tit-adulti">Iscriviti</button></p>
</section>"""
    return _c(rng, "it", "passed", "2.5.3/P2", "Corsi di nuoto", main, "#iscr-adulti",
              "The name 'Iscriviti Corso di nuoto per adulti' starts with the visible label and only adds context after it (G208).",
              org="Società sportiva Valfittizia", diff="medium")


def p_filesize_fr(rng):
    main = """<h1>Camp de ski 2027</h1>
<p>Le camp de ski des écoles a lieu du 8 au 13 février 2027 à Valfictif-les-Bains.</p>
<p><a href="inscription-camp.pdf" id="dl-inscription" aria-label="Télécharger le formulaire d'inscription (PDF, 120 Ko)">Télécharger le formulaire d'inscription</a></p>"""
    return _c(rng, "fr", "passed", "2.5.3/P2", "Camp de ski", main, "#dl-inscription",
              "The aria-label begins with the full visible text and adds file format and size (G208).",
              org="École de Valfictif", diff="medium")


# traps --------------------------------------------------------------------

def t_mehr_de(rng):
    main = """<h1>Abfall</h1>
<article class="card">
<h2>Abfallkalender 2026</h2>
<p>Alle Sammeldaten für Kehricht, Grüngut, Papier und Karton auf einen Blick.</p>
<p><a href="abfallkalender-2026.html" id="mehr-kalender" aria-label="Mehr zum Abfallkalender 2026">Mehr</a></p>
</article>"""
    return _c(rng, "de", "passed", "2.5.3/T1", "Abfall", main, "#mehr-kalender",
              "The terse visible label 'Mehr' is kept at the start of the longer accessible name 'Mehr zum Abfallkalender 2026', which only adds context (G208).",
              org="Gemeinde Beispielwil", trap=True, diff="medium")


def t_punctuation_fr(rng):
    main = """<h1>Inscription au passeport vacances</h1>
<p class="muted">Étape 1 sur 3</p>
<form action="passeport-etape-2.html" method="get">
<label for="pv-enfant">Prénom de l'enfant</label>
<input id="pv-enfant" name="pv-enfant" type="text">
<p><button type="submit" id="pv-continuer" aria-label="continuer">Continuer…</button></p>
</form>"""
    return _c(rng, "fr", "passed", "2.5.3/T2", "Passeport vacances", main, "#pv-continuer",
              "Visible 'Continuer…' vs name 'continuer' differ only in case and punctuation, which Understanding 2.5.3 says can be ignored.",
              org="Commune de Valfictif", trap=True, diff="medium")


def t_close_symbol_it(rng):
    css = (".avviso{display:flex;justify-content:space-between;align-items:center;background:#fff8e1;border:1px solid #d4a017;"
           "border-radius:8px;padding:10px 14px}.avviso p{margin:0}.avviso .chiudi{background:transparent;color:#1d2327;"
           "border:0;font-size:1.4rem;line-height:1;padding:4px 8px}")
    main = """<div class="avviso" id="avviso-acqua"><p>Martedì 17 novembre, dalle 8.00 alle 12.00, interruzione dell'acqua in Via Cantonale.</p>
<button type="button" class="chiudi" id="chiudi-avviso" aria-label="Chiudi avviso">×</button></div>
<h1>Azienda acqua potabile</h1>
<p>L'azienda garantisce l'approvvigionamento di acqua potabile a 3 500 abitanti.</p>"""
    return _c(rng, "it", "passed", "2.5.3/T3", "Acqua potabile", main, "#chiudi-avviso",
              "The button shows only the symbol '×'; symbolic characters are not text labels (Understanding 2.5.3), so the descriptive name 'Chiudi avviso' is appropriate.",
              org="Azienda acqua potabile Valfittizia", css=css, trap=True, diff="hard")


def t_extra_words_it(rng):
    main = """<h1>Campi da tennis</h1>
<table>
<caption>Disponibilità giovedì 19 novembre 2026</caption>
<tr><th scope="col">Campo</th><th scope="col">18.00–19.00</th></tr>
<tr><th scope="row">Campo n. 2</th><td><button type="button" id="prenota-2" aria-label="Prenota il campo da tennis n. 2, ore 18">Prenota</button></td></tr>
</table>"""
    return _c(rng, "it", "passed", "2.5.3/T1", "Campi da tennis", main, "#prenota-2",
              "The accessible name starts with the visible label 'Prenota' and appends the court and time (G208).",
              org="Società sportiva Valfittizia", trap=True, diff="medium")


def t_uppercase_fr(rng):
    css = ".majuscules{text-transform:uppercase;letter-spacing:.05em;background:#0b4f6c;color:#ffffff}"
    main = """<h1>Cartes journalières</h1>
<p>Quatre cartes par jour, CHF 45.– pour les habitants.</p>
<p><a class="btn majuscules" id="commander-carte" href="commande-carte.html" aria-label="Commander la carte journalière">Commander</a></p>"""
    return _c(rng, "fr", "passed", "2.5.3/T2", "Cartes journalières", main, "#commander-carte",
              "The label is displayed in capitals by CSS (text 'Commander'); case is ignored and the name begins with the visible word.",
              org="Commune d'Exempleval", css=css, trap=True, diff="medium")


def t_icon_only_de(rng):
    css = (".kopf{display:flex;justify-content:space-between;align-items:center}"
           ".kopf .menu-knopf{padding:8px;display:flex;align-items:center}")
    main = f"""<div class="kopf"><h1>Gemeindeverwaltung</h1>
<button type="button" class="menu-knopf" id="menu-oeffnen" aria-label="Menü öffnen" aria-expanded="false">{icon_svg('menu', 22)}</button></div>
<p>Die Verwaltung ist von Montag bis Freitag von 8.00 bis 11.30 Uhr geöffnet.</p>"""
    return _c(rng, "de", "passed", "2.5.3/T3", "Gemeindeverwaltung", main, "#menu-oeffnen",
              "The menu button has no visible text (icon only), so there is no visible label the name would have to contain; its aria-label is free.",
              org="Gemeinde Ober-Beispielwil", css=css, trap=True, diff="medium")


# ---------------------------------------------------------------------------
# cantTell
# ---------------------------------------------------------------------------

def c_placeholder_heading_de(rng):
    css = ".nl-box{max-width:420px}.nl-box input{width:100%;box-sizing:border-box}"
    main = """<h1>Kulturagenda</h1>
<p>Konzerte, Lesungen und Ausstellungen in Mustersee.</p>
<div class="box nl-box">
<h2>Newsletter</h2>
<p>Einmal im Monat alle Veranstaltungen per E-Mail.</p>
<form action="kultur-newsletter.html" method="post">
<input id="nl-adresse" name="nl-adresse" type="email" placeholder="E-Mail-Adresse" aria-label="Newsletter-E-Mail">
<p><button type="submit">Abonnieren</button></p>
</form>
</div>"""
    return _c(rng, "de", "cantTell", "2.5.3/C1", "Kulturagenda", main, "#nl-adresse",
              "The field has no label element; the only nearby visible texts are a placeholder 'E-Mail-Adresse' and the box heading 'Newsletter'. Which (if any) is its visible label is unclear, so it is unclear whether 'Newsletter-E-Mail' contains it.",
              org="Stadt Mustersee", css=css, diff="hard")


def c_image_banner_fr(rng):
    img = asset("banner-camp-ski", _ski_banner())
    main = f"""<h1>Écoles de Valfictif</h1>
<p>Toutes les informations pour les familles : horaires, transports scolaires, camps et activités.</p>
<p><a href="camp-ski.html" id="lien-camp"><img src="{img}" alt="S'inscrire au camp de ski" width="420" height="200"></a></p>"""
    return _c(rng, "fr", "cantTell", "2.5.3/C2", "Écoles", main, "#lien-camp",
              "The linked picture is a snow scene with small embedded text 'Inscriptions 2027'; whether that text is a visible label (image of text) or part of a picture with significant other content is debatable, so containment cannot be judged.",
              org="École de Valfictif", diff="hard")


def c_block_link_it(rng):
    css = (".blocco{display:block;text-decoration:none;color:inherit;border:1px solid #c9d3d8;border-radius:10px;padding:14px;max-width:420px}"
           ".blocco h2{margin:0 0 .3em;font-size:1.2rem}.blocco .leggi{color:#0b5394;text-decoration:underline}")
    main = """<h1>Museo della Filanda</h1>
<a class="blocco" id="mostra-filande" href="mostra-filande.html" aria-label="Mostra Filande ticinesi">
<h2>Filande ticinesi</h2>
<p>Una mostra sulle donne che lavoravano la seta, fino al 28 febbraio 2027.</p>
<span class="leggi">Leggi</span>
</a>"""
    return _c(rng, "it", "cantTell", "2.5.3/C1", "Museo della Filanda", main, "#mostra-filande",
              "A whole card is one link containing a heading, a sentence and 'Leggi'; the name contains the heading text but not 'Leggi' or the sentence. Which visible text is the link's label is unclear.",
              org="Museo della Filanda, Esempiano", css=css, alt="failed", diff="hard")


def c_switch_de(rng):
    css = (".schalter{display:flex;align-items:center;gap:10px}.schalter .knopf{width:52px;height:28px;border-radius:14px;"
           "padding:0;background:#6b7280;border-color:#6b7280;position:relative}.schalter .knopf::after{content:\"\";position:absolute;"
           "top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:#ffffff}"
           ".schalter .knopf[aria-checked=\"true\"]{background:#2f7d3a;border-color:#2f7d3a}"
           ".schalter .knopf[aria-checked=\"true\"]::after{left:27px}")
    main = """<h1>Mein Konto</h1>
<h2>Benachrichtigungen</h2>
<p>SMS-Erinnerung am Vorabend der Kehrichtabfuhr</p>
<div class="schalter"><span>Aus</span><button type="button" role="switch" class="knopf" id="sms-schalter" aria-checked="false" aria-label="Erinnerung per SMS aktivieren"></button><span>An</span></div>
<script>
document.getElementById('sms-schalter').addEventListener('click', function () {
  this.setAttribute('aria-checked', this.getAttribute('aria-checked') === 'true' ? 'false' : 'true');
});
</script>"""
    return _c(rng, "de", "cantTell", "2.5.3/C1", "Mein Konto", main, "#sms-schalter",
              "The switch has no own text; nearby are the state words 'Aus'/'An' and a description line. Whether any of them is the switch's visible label (which the name would have to contain) is ambiguous.",
              org="Gemeinde Beispielwil", css=css, diff="hard")


SCENARIOS = [
    f_senden_de, f_suche_de, f_pdf_fr, f_iscriviti_it, f_order_fr, f_input_cap_it, f_labelledby_heading_de,
    f_checkbox_de, f_english_name_fr, f_tab_it,
    p_same_de, p_label_fr, p_link_it, p_labelledby_de, p_labelledby_extra_it, p_filesize_fr,
    t_mehr_de, t_punctuation_fr, t_close_symbol_it, t_extra_words_it, t_uppercase_fr, t_icon_only_de,
    c_placeholder_heading_de, c_image_banner_fr, c_block_link_it, c_switch_de,
]


def build(rng):
    return [fn(rng) for fn in SCENARIOS]
