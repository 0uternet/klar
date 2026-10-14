"""4.1.2 Name, Role, Value – hand-written scenarios (see protocol_parts/4.1.2.md)."""
from common import *
from _structure_util import mk, icon_svg, SR_ONLY

CRITERION = "4.1.2"

BASE_CSS = (".btn{display:inline-block;padding:8px 16px;border-radius:6px;text-decoration:none;font-weight:600;"
            "background:#0b4f6c;color:#ffffff}.panel{border:1px solid #c9d3d8;border-radius:8px;padding:10px 14px;margin-top:8px}"
            ".chev svg{transition:transform .2s}.aperto .chev svg{transform:rotate(90deg)}")


def _c(rng, lang, expected, rule, title, main, target, notes, **kw):
    css = BASE_CSS + kw.pop("css", "")
    return mk(CRITERION, rng, lang, expected, rule, title, main, target, notes, css=css, **kw)


# ---------------------------------------------------------------------------
# failed
# ---------------------------------------------------------------------------

def f_div_button_de(rng):
    css = (".knopf{display:inline-block;background:#2f5d34;color:#ffffff;padding:8px 18px;border-radius:6px;cursor:pointer;"
           "font-weight:600;margin-top:12px}")
    main = """<h1>Online-Umfrage zum Ortsbus</h1>
<p>Wie zufrieden sind Sie mit dem Ortsbus? Die Umfrage dauert etwa fünf Minuten und ist anonym.</p>
<div class="knopf" id="umfrage-start" onclick="document.getElementById('frage-1').hidden = false; this.hidden = true;">Umfrage starten</div>
<div id="frage-1" hidden>
<p>Wie oft benutzen Sie den Ortsbus?</p>
<p><label><input type="radio" name="haeufigkeit" value="taeglich"> täglich</label>
<label><input type="radio" name="haeufigkeit" value="woechentlich"> wöchentlich</label>
<label><input type="radio" name="haeufigkeit" value="selten"> selten</label></p>
</div>"""
    return _c(rng, "de", "failed", "4.1.2/F1", "Umfrage Ortsbus", main, "#umfrage-start",
              "A <div> with an onclick handler is styled and used as a button, but it has no role (and is not focusable), so it is not exposed as a control (F59).",
              org="Beispielwiler Verkehrsbetriebe", css=css, diff="easy")


def f_span_more_fr(rng):
    css = ".lien-plus{color:#0b5394;text-decoration:underline;cursor:pointer}"
    main = """<h1>Histoire du moulin</h1>
<p>Le moulin de Bourg-Modèle a été construit en 1742 au bord de la Rivière-Fictive. Il a moulu le blé des paysans de la région pendant près de deux siècles.</p>
<p id="suite-histoire" hidden>En 1931, une crue a emporté la roue à aubes. Restauré par une association de bénévoles dès 1988, le moulin accueille aujourd'hui le musée et des démonstrations de mouture chaque premier dimanche du mois.</p>
<p><span class="lien-plus" id="afficher-plus" onclick="document.getElementById('suite-histoire').hidden = false; this.hidden = true;">Afficher plus</span></p>"""
    return _c(rng, "fr", "failed", "4.1.2/F1", "Histoire du moulin", main, "#afficher-plus",
              "A <span> styled like a link reveals hidden text on click but has no role, no focusability and no state; its function is not programmatically determined (F59).",
              org="Musée du Moulin, Bourg-Modèle", css=css, diff="easy")


def f_accordion_no_state_it(rng):
    css = (".fisarmonica{background:#ffffff;color:#1d2327;border:1px solid #c9d3d8;width:100%;text-align:left;"
           "display:flex;justify-content:space-between;align-items:center}main h2{margin:.6em 0 0;font-size:1.1rem}")
    chev = icon_svg("chevron-right", 18)
    main = f"""<h1>Ufficio controllo abitanti</h1>
<h2><button type="button" class="fisarmonica" id="acc-orari" aria-controls="pan-orari">Orari di apertura <span class="chev">{chev}</span></button></h2>
<div class="panel" id="pan-orari" hidden><p>Da lunedì a venerdì, 8.30–11.30; giovedì anche 14.00–18.00.</p></div>
<h2><button type="button" class="fisarmonica" id="acc-documenti" aria-controls="pan-documenti">Documenti necessari <span class="chev">{chev}</span></button></h2>
<div class="panel" id="pan-documenti" hidden><p>Documento d'identità valido e contratto di locazione.</p></div>
<script>
document.querySelectorAll('.fisarmonica').forEach(function (btn) {{
  btn.addEventListener('click', function () {{
    var pan = document.getElementById(btn.getAttribute('aria-controls'));
    pan.hidden = !pan.hidden;
    btn.classList.toggle('aperto');
  }});
}});
</script>"""
    return _c(rng, "it", "failed", "4.1.2/F2", "Controllo abitanti", main, "#acc-orari",
              "The accordion button opens/closes its panel and rotates a chevron, but no aria-expanded is ever set, so the expanded/collapsed state is only visual (ARIA5 not applied).",
              org="Comune di Esempiano", css=css, diff="medium")


def f_stale_expanded_de(rng):
    main = """<h1>Bestattungen</h1>
<p>Bei einem Todesfall unterstützt Sie das Bestattungsamt bei allen Formalitäten.</p>
<p><button type="button" id="toggle-gebuehren" aria-expanded="false" aria-controls="gebuehren-panel">Gebühren anzeigen</button></p>
<div class="panel" id="gebuehren-panel" hidden>
<p>Erdbestattung CHF 900.–, Urnenbeisetzung CHF 450.–, Gemeinschaftsgrab CHF 300.–. Für Einwohnerinnen und Einwohner gelten reduzierte Tarife.</p>
</div>
<script>
document.getElementById('toggle-gebuehren').addEventListener('click', function () {
  var p = document.getElementById('gebuehren-panel');
  p.hidden = !p.hidden;
});
</script>"""
    return _c(rng, "de", "failed", "4.1.2/F2", "Bestattungen", main, "#toggle-gebuehren",
              "The script shows and hides the panel but never updates aria-expanded, which stays 'false' while the fees are visible; the exposed state is wrong after interaction.",
              org="Gemeinde Fiktal", diff="hard")


def f_checkbox_no_checked_fr(rng):
    css = (".coche{display:flex;align-items:center;gap:10px;margin-top:14px}.coche .case{width:22px;height:22px;"
           "border:2px solid #1d2327;border-radius:4px;cursor:pointer}.coche .case.cochee{background:#0b4f6c;"
           "box-shadow:inset 0 0 0 3px #ffffff}")
    main = """<h1>Location de la salle de gymnastique</h1>
<form action="location-envoyee.html" method="post">
<label for="societe">Nom de la société</label>
<input id="societe" name="societe" type="text">
<div class="coche"><div class="case" role="checkbox" tabindex="0" id="reglement" aria-labelledby="txt-reglement"></div>
<span id="txt-reglement">J'ai lu le règlement d'utilisation de la salle</span></div>
<p><button type="submit">Envoyer la demande</button></p>
</form>
<script>
(function () {
  var c = document.getElementById('reglement');
  function basculer() { c.classList.toggle('cochee'); }
  c.addEventListener('click', basculer);
  c.addEventListener('keydown', function (e) { if (e.key === ' ') { e.preventDefault(); basculer(); } });
})();
</script>"""
    return _c(rng, "fr", "failed", "4.1.2/F3", "Salle de gymnastique", main, "#reglement",
              "The custom checkbox has role=checkbox and a name, but no aria-checked; its checked state is shown only by a CSS class (ACT 4e8ab6, ARIA5).",
              org="Ville de Bourg-Modèle", css=css, diff="medium")


def f_icon_no_name_de(rng):
    css = ".werkzeuge{display:flex;gap:8px;justify-content:flex-end}.werkzeuge button{padding:8px;display:flex;align-items:center}"
    main = f"""<div class="werkzeuge">
<button type="button" id="seite-drucken" onclick="window.print()">{icon_svg('printer', 20)}</button>
<a href="mailto:?subject=Wahlen%202026" class="btn">Seite per E-Mail teilen</a>
</div>
<h1>Gemeindewahlen 2026</h1>
<p>Die Gemeindewahlen finden am 29. November 2026 statt. Das Wahlbüro im Gemeindehaus ist von 10.00 bis 12.00 Uhr geöffnet.</p>"""
    return _c(rng, "de", "failed", "4.1.2/F4", "Gemeindewahlen", main, "#seite-drucken",
              "The print button contains only an aria-hidden SVG and has no aria-label or title, so it has no accessible name (ACT 97a4e1, F68).",
              org="Gemeinde Beispielberg", css=css, diff="easy")


def f_iframe_no_title_fr(rng):
    inner = ("<p style='font-family:sans-serif'>Arrêt de bus « Place du Village », ligne 21 – "
             "parking de 40 places derrière la salle polyvalente.</p>")
    main = f"""<h1>Plan d'accès à la salle polyvalente</h1>
<p>La salle polyvalente se trouve place du Village 2, à cinq minutes à pied de la gare.</p>
<iframe id="carte-acces" srcdoc="{esc(inner)}" width="560" height="120"></iframe>"""
    return _c(rng, "fr", "failed", "4.1.2/F5", "Plan d'accès", main, "#carte-acces",
              "The embedded frame has no title or other accessible name, so assistive technology cannot tell what it contains (ACT cae760, H64 not applied).",
              org="Commune d'Exempleval", diff="easy")


def f_hidden_focusable_it(rng):
    css = (".carosello{position:relative;overflow:hidden}.diapositiva{border:1px solid #c9d3d8;border-radius:8px;padding:12px}"
           ".diapositiva.nascosta{position:absolute;left:-10000px;top:0;width:100%}")
    main = """<h1>Eventi in evidenza</h1>
<div class="carosello">
<div class="diapositiva" id="diap-1"><h2>Castagnata in piazza</h2><p>Domenica 25 ottobre, dalle 14.00 in Piazza Grande.</p><a href="castagnata.html">Programma della castagnata</a></div>
<div class="diapositiva nascosta" id="diap-2" aria-hidden="true"><h2>Mercatino di Natale</h2><p>Bancarelle di artigiani dal 5 all'8 dicembre.</p><a href="mercatino.html" id="link-mercatino">Iscrizioni al mercatino</a></div>
</div>"""
    return _c(rng, "it", "failed", "4.1.2/F6", "Eventi", main, "#link-mercatino",
              "The off-screen slide is aria-hidden=\"true\" but its link stays in the tab order, so keyboard focus lands on an element with no exposed name or role (ACT 6cfa84).",
              org="Comune di Esempiano", css=css, diff="hard")


def f_img_link_no_alt_it(rng):
    img = asset("pic-share-social", pictogram("share", color="#ffffff", bg="#8e5ea2", size=36))
    css = ".social{display:flex;gap:10px;align-items:center}"
    main = f"""<h1>Pro Valfittizia</h1>
<p>L'associazione turistica organizza escursioni, concerti all'aperto e la festa d'estate.</p>
<div class="social"><span>Seguiteci:</span>
<a href="https://social.example/provalfittizia" id="link-social"><img src="{img}" width="36" height="36"></a>
<a href="newsletter.html">Newsletter</a></div>"""
    return _c(rng, "it", "failed", "4.1.2/F4", "Pro Valfittizia", main, "#link-social",
              "The link's only content is an image without alt, so the link has no accessible name (F89).",
              org="Comune di Valfittizia", css=css, diff="easy")


def f_input_no_name_de(rng):
    css = (".fuss-newsletter{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.fuss-newsletter p{margin:0;font-weight:700}")
    main = """<h1>Kultur in Mustersee</h1>
<p>Theater, Konzerte und Ausstellungen – das ganze Jahr über.</p>
<form class="fuss-newsletter box" action="kultur-abo.html" method="post">
<p>Newsletter</p>
<input id="kultur-mail" name="kultur-mail" type="email">
<button type="submit">Abonnieren</button>
</form>"""
    return _c(rng, "de", "failed", "4.1.2/F4", "Kultur", main, "#kultur-mail",
              "The e-mail input has no label, aria-label, title or placeholder; the nearby word 'Newsletter' is not associated, so the field has no accessible name (ACT e086e5, F68).",
              org="Stadt Mustersee", css=css, diff="medium")


def f_tab_no_selected_fr(rng):
    css = ("[role=\"tablist\"]{display:flex;gap:4px;border-bottom:2px solid #0b4f6c}[role=\"tab\"]{background:#ffffff;color:#1d2327;"
           "border:1px solid #0b4f6c;border-radius:6px 6px 0 0}[role=\"tab\"].actif{background:#0b4f6c;color:#ffffff}")
    main = """<h1>Horaires du téléski des Écureuils</h1>
<div role="tablist" aria-label="Saison">
<button type="button" role="tab" id="tab-hiver" aria-controls="pan-hiver" class="actif">Hiver</button>
<button type="button" role="tab" id="tab-printemps" aria-controls="pan-printemps" tabindex="-1">Printemps</button>
</div>
<div role="tabpanel" id="pan-hiver" aria-labelledby="tab-hiver" class="panel"><p>Décembre à mars : tous les jours de 9 h à 16 h 30.</p></div>
<div role="tabpanel" id="pan-printemps" aria-labelledby="tab-printemps" class="panel" hidden><p>Avril : week-ends uniquement, de 9 h à 15 h selon l'enneigement.</p></div>
<script>
document.querySelectorAll('[role="tab"]').forEach(function (tab) {
  tab.addEventListener('click', function () {
    document.querySelectorAll('[role="tab"]').forEach(function (t) {
      t.classList.remove('actif');
      t.tabIndex = -1;
      document.getElementById(t.getAttribute('aria-controls')).hidden = true;
    });
    tab.classList.add('actif');
    tab.tabIndex = 0;
    document.getElementById(tab.getAttribute('aria-controls')).hidden = false;
  });
});
</script>"""
    return _c(rng, "fr", "failed", "4.1.2/F3", "Téléski", main, "#tab-hiver",
              "The tabs show the active season only through a CSS class; aria-selected is never set, so which tab is selected cannot be programmatically determined (ARIA5).",
              org="Commune de Valfictif", css=css, diff="hard")


# ---------------------------------------------------------------------------
# passed
# ---------------------------------------------------------------------------

def p_native_button_de(rng):
    main = """<h1>Fundbüro</h1>
<p>Haben Sie etwas verloren? Durchsuchen Sie die Liste der Fundgegenstände der letzten 30 Tage.</p>
<form action="fundsachen.html" method="get" role="search">
<label for="fund-q">Gegenstand</label>
<input id="fund-q" name="q" type="search">
<p><button type="submit" id="fund-suchen">Suchen</button></p>
</form>"""
    return _c(rng, "de", "passed", "4.1.2/P1", "Fundbüro", main, "#fund-suchen",
              "Native <button> with text content: role and name are exposed by the browser (H91).",
              org="Gemeinde Beispielwil", diff="easy")


def p_native_checkbox_fr(rng):
    css = ".case-native{display:flex;gap:8px;align-items:flex-start;margin-top:14px}.case-native label{margin:0;font-weight:400}"
    main = """<h1>Bulletin communal</h1>
<form action="bulletin-ok.html" method="post">
<label for="bc-courriel">Adresse e-mail</label>
<input id="bc-courriel" name="bc-courriel" type="email" autocomplete="email">
<div class="case-native"><input type="checkbox" id="version-papier" name="papier"><label for="version-papier">Je souhaite aussi recevoir la version papier</label></div>
<p><button type="submit">S'abonner</button></p>
</form>"""
    return _c(rng, "fr", "passed", "4.1.2/P1", "Bulletin communal", main, "#version-papier",
              "Native checkbox with an associated label: name, role and checked state are exposed natively (H44, H91).",
              org="Commune de Valfictif", css=css, diff="easy")


def p_native_select_it(rng):
    main = """<h1>Prenotazione della sala del Consiglio</h1>
<form action="sala-prenotata.html" method="post">
<label for="fascia">Fascia oraria</label>
<select id="fascia" name="fascia"><option>Mattina (8.00–12.00)</option><option>Pomeriggio (13.00–17.00)</option><option>Sera (18.00–22.00)</option></select>
<p><button type="submit">Prenotare</button></p>
</form>"""
    return _c(rng, "it", "passed", "4.1.2/P1", "Sala del Consiglio", main, "#fascia",
              "Native select with label: role, name and selected value are exposed by the browser.",
              org="Comune di Valfittizia", diff="easy")


def p_disclosure_de(rng):
    main = """<h1>Hundekurse</h1>
<p>Der Kynologische Verein bietet Kurse für Welpen und Junghunde an.</p>
<p><button type="button" id="kursdaten-zeigen" aria-expanded="false" aria-controls="kursdaten">Kursdaten anzeigen</button></p>
<div class="panel" id="kursdaten" hidden><p>Welpenkurs: ab 6. März 2027, samstags 9.00 Uhr. Junghundekurs: ab 8. März 2027, montags 18.30 Uhr.</p></div>
<script>
document.getElementById('kursdaten-zeigen').addEventListener('click', function () {
  var offen = this.getAttribute('aria-expanded') === 'true';
  this.setAttribute('aria-expanded', offen ? 'false' : 'true');
  document.getElementById('kursdaten').hidden = offen;
});
</script>"""
    return _c(rng, "de", "passed", "4.1.2/P2", "Hundekurse", main, "#kursdaten-zeigen",
              "Native button whose aria-expanded is toggled together with the panel, so the state is exposed and updated (ARIA5).",
              org="Gemeinde Ober-Beispielwil", diff="medium")


def p_iframe_title_it(rng):
    inner = ("<p style='font-family:sans-serif'>Percorso Vita del Monte Fittizio: 2,8 km, 20 postazioni, "
             "partenza dal posteggio della piscina.</p>")
    main = f"""<h1>Percorso Vita</h1>
<p>Il percorso è aperto tutto l'anno ed è illuminato fino alle 21.00.</p>
<iframe id="mappa-percorso" title="Mappa del Percorso Vita" srcdoc="{esc(inner)}" width="560" height="120"></iframe>"""
    return _c(rng, "it", "passed", "4.1.2/P1", "Percorso Vita", main, "#mappa-percorso",
              "The iframe has a descriptive title, giving it an accessible name (H64).",
              org="Comune di Esempiano", diff="easy")


def p_switch_fr(rng):
    css = (".interrupteur{display:flex;align-items:center;gap:10px}.interrupteur button{width:52px;height:28px;border-radius:14px;"
           "padding:0;background:#6b7280;border-color:#6b7280;position:relative}.interrupteur button::after{content:\"\";"
           "position:absolute;top:3px;left:3px;width:20px;height:20px;border-radius:50%;background:#ffffff}"
           ".interrupteur button[aria-checked=\"true\"]{background:#2f5d34;border-color:#2f5d34}"
           ".interrupteur button[aria-checked=\"true\"]::after{left:27px}")
    main = """<h1>Mes notifications</h1>
<div class="interrupteur"><button type="button" role="switch" id="rappel-dechets" aria-checked="false" aria-labelledby="lbl-rappel"></button>
<span id="lbl-rappel">Rappel par SMS la veille du ramassage</span></div>
<script>
document.getElementById('rappel-dechets').addEventListener('click', function () {
  this.setAttribute('aria-checked', this.getAttribute('aria-checked') === 'true' ? 'false' : 'true');
});
</script>"""
    return _c(rng, "fr", "passed", "4.1.2/P2", "Notifications", main, "#rappel-dechets",
              "A native button with role=switch, a name via aria-labelledby and aria-checked updated on activation (keyboard comes with <button>).",
              org="Ville de Bourg-Modèle", css=css, diff="medium")


# traps --------------------------------------------------------------------

def t_aria_button_de(rng):
    css = (".kachel{display:inline-block;background:#2f5d34;color:#ffffff;padding:10px 18px;border-radius:6px;cursor:pointer;font-weight:600}"
           ".kachel:focus{outline:3px solid #e07a2e;outline-offset:2px}")
    main = """<h1>Wasserzähler ablesen</h1>
<p>Bitte melden Sie uns den Zählerstand bis 15. Januar 2027.</p>
<div class="kachel" role="button" tabindex="0" id="ablesung-start">Zählerstand melden</div>
<div id="ablesung-form" class="panel" hidden><p>Das Formular wird geladen …</p></div>
<script>
(function () {
  var k = document.getElementById('ablesung-start');
  function los() { document.getElementById('ablesung-form').hidden = false; }
  k.addEventListener('click', los);
  k.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); los(); }
  });
})();
</script>"""
    return _c(rng, "de", "passed", "4.1.2/T1", "Wasserzähler", main, "#ablesung-start",
              "Although it is a <div>, it has role=button, tabindex=0, a name from its text and Enter/Space handling, so name and role are exposed (ARIA4).",
              org="Wasserversorgung Fiktal", css=css, trap=True, diff="medium")


def t_details_fr(rng):
    css = "details{border:1px solid #c9d3d8;border-radius:8px;padding:8px 12px;margin:8px 0}summary{cursor:pointer;font-weight:700}"
    main = """<h1>Taxe d'exemption du service du feu</h1>
<details>
<summary id="qui-paie">Qui doit payer la taxe ?</summary>
<p>Toutes les personnes domiciliées âgées de 20 à 50 ans qui ne sont pas incorporées au corps des sapeurs-pompiers.</p>
</details>
<details>
<summary>Comment est-elle calculée ?</summary>
<p>Elle s'élève à 3 % de l'impôt cantonal, au maximum CHF 400.– par an.</p>
</details>"""
    return _c(rng, "fr", "passed", "4.1.2/T2", "Taxe du feu", main, "#qui-paie",
              "details/summary is a native disclosure: the browser exposes its role and expanded state without any ARIA.",
              org="Commune d'Exempleval", css=css, trap=True, diff="medium")


def t_link_as_button_it(rng):
    main = """<h1>Iscrizioni alla scuola di musica</h1>
<p>Lezioni individuali di pianoforte, chitarra, violino e fisarmonica per bambini e adulti.</p>
<p><a class="btn" id="vai-iscrizione" href="iscrizione-musica.html">Iscriviti ora</a></p>"""
    return _c(rng, "it", "passed", "4.1.2/T3", "Scuola di musica", main, "#vai-iscrizione",
              "It looks like a button but navigates to another page, so the native link role is the right one; name and role are exposed.",
              org="Scuola di Esempiano", trap=True, diff="easy")


def t_redundant_click_de(rng):
    img = asset("scene-library-teaser", scene("library", w=360, h=200, seed=2))
    css = ".teaser-bild{display:block;cursor:pointer}.teaser-bild img{border-radius:8px}"
    main = f"""<h1>Bibliothek</h1>
<article class="card">
<span class="teaser-bild" id="teaser-bild" aria-hidden="true" onclick="window.location.href='lesesommer.html'"><img src="{img}" alt="" width="360" height="200"></span>
<h2>Lesesommer 2027</h2>
<p>Lesen, Stempel sammeln und am Schlussfest tolle Preise gewinnen.</p>
<p><a href="lesesommer.html">Zum Lesesommer</a></p>
</article>"""
    return _c(rng, "de", "passed", "4.1.2/T4", "Bibliothek", main, "#teaser-bild",
              "The clickable picture is a mouse-only convenience: it is hidden from assistive technology, not focusable, and its action is duplicated by the native link 'Zum Lesesommer'.",
              org="Bibliothek Mustersee", css=css, trap=True, diff="hard")


def t_icon_aria_label_it(rng):
    css = ".strumenti{display:flex;justify-content:flex-end}.strumenti button{padding:8px;display:flex;align-items:center}"
    main = f"""<div class="strumenti"><button type="button" id="stampa-pagina" aria-label="Stampa la pagina" onclick="window.print()">{icon_svg('printer', 20)}</button></div>
<h1>Raccolta degli scarti vegetali</h1>
<p>Gli scarti vegetali sono raccolti ogni martedì da marzo a novembre.</p>"""
    return _c(rng, "it", "passed", "4.1.2/T5", "Scarti vegetali", main, "#stampa-pagina",
              "Icon-only button, but aria-label provides the accessible name 'Stampa la pagina' and the native button provides the role (ARIA14).",
              org="Comune di Valfittizia", css=css, trap=True, diff="easy")


def t_hidden_unfocusable_fr(rng):
    img = asset("scene-concert-teaser", scene("concert", w=360, h=200, seed=4))
    main = f"""<h1>Agenda culturelle</h1>
<article class="card">
<div aria-hidden="true"><a href="concert-fanfare.html" tabindex="-1" id="vignette-concert"><img src="{img}" alt="" width="360" height="200"></a></div>
<h2><a href="concert-fanfare.html">Concert de la fanfare</a></h2>
<p>Samedi 14 novembre 2026, 20 h, salle polyvalente. Entrée libre, collecte.</p>
</article>"""
    return _c(rng, "fr", "passed", "4.1.2/T6", "Agenda culturelle", main, "#vignette-concert",
              "The duplicate image link sits in an aria-hidden container but has tabindex=-1, so it is removed from both the accessibility tree and the tab order (ACT 6cfa84 passes); the heading link is the accessible one.",
              org="Ville de Bourg-Modèle", trap=True, diff="hard")


def t_sr_text_de(rng):
    css = SR_ONLY + ".teilen{display:flex;gap:8px}.teilen button{padding:8px;display:flex;align-items:center}"
    main = f"""<h1>Gemeindeversammlung vom 30. November 2026</h1>
<p>Traktanden: Budget 2027, Steuerfuss, Kredit für die Sanierung der Seestrasse.</p>
<div class="teilen"><button type="button" id="link-kopieren" onclick="navigator.clipboard &amp;&amp; navigator.clipboard.writeText(location.href)">{icon_svg('share', 20)}<span class="sr-only">Link zur Seite kopieren</span></button></div>"""
    return _c(rng, "de", "passed", "4.1.2/T5", "Gemeindeversammlung", main, "#link-kopieren",
              "The visible content is only an icon, but a visually hidden span gives the button the name 'Link zur Seite kopieren'.",
              org="Gemeinde Beispielberg", css=css, trap=True, diff="medium")


# ---------------------------------------------------------------------------
# cantTell
# ---------------------------------------------------------------------------

def c_hash_button_de(rng):
    main = """<h1>Spielplätze in Fiktal</h1>
<p>Die Gemeinde unterhält sieben öffentliche Spielplätze. Alle sind frei zugänglich.</p>
<p><button type="button" id="zur-karte" onclick="location.hash = 'karte'">Zur Karte</button></p>
<h2>Liste der Spielplätze</h2>
<ul><li>Schulhaus Seematte</li><li>Dorfplatz</li><li>Waldrand Kirchweg</li></ul>
<h2 id="karte">Karte</h2>
<p>Alle Spielplätze sind auf dem Ortsplan beim Gemeindehaus eingezeichnet.</p>"""
    return _c(rng, "de", "cantTell", "4.1.2/C1", "Spielplätze", main, "#zur-karte",
              "A native button that only changes the URL fragment to jump to a section: it is exposed as a button but behaves like an in-page link; whether its role is appropriate is debated.",
              org="Gemeinde Fiktal", diff="hard")


def c_link_opens_dialog_fr(rng):
    css = "dialog{border:1px solid #c9d3d8;border-radius:10px;max-width:460px}"
    main = """<h1>Salle polyvalente</h1>
<p>300 places, scène, cuisine équipée. Location pour sociétés et particuliers.</p>
<p><a href="#" id="ouvrir-plan" onclick="document.getElementById('plan').showModal(); return false;">Plan d'accès</a></p>
<dialog id="plan" aria-labelledby="titre-plan">
<h2 id="titre-plan">Plan d'accès</h2>
<p>Place du Village 2, bus 21 arrêt « Village ». Parking derrière la salle.</p>
<form method="dialog"><button type="submit">Fermer</button></form>
</dialog>"""
    return _c(rng, "fr", "cantTell", "4.1.2/C1", "Salle polyvalente", main, "#ouvrir-plan",
              "An <a href=\"#\"> opens a modal dialog instead of navigating; it is exposed as a link while acting as a button. Whether this role mismatch fails 4.1.2 is a known point of disagreement.",
              org="Commune d'Exempleval", css=css, alt="failed", diff="hard")


def c_text_toggle_it(rng):
    main = """<h1>Posteggi per biciclette</h1>
<p>Nel centro di Modellina ci sono 240 posteggi coperti per biciclette, di cui 40 con colonnina di ricarica.</p>
<p><button type="button" id="mostra-mappa">Mostra mappa</button></p>
<div class="panel" id="mappa-bici" hidden><p>Stazione (120 posti), Piazza Grande (60 posti), Scuole (60 posti).</p></div>
<script>
document.getElementById('mostra-mappa').addEventListener('click', function () {
  var m = document.getElementById('mappa-bici');
  m.hidden = !m.hidden;
  this.textContent = m.hidden ? 'Mostra mappa' : 'Nascondi mappa';
});
</script>"""
    return _c(rng, "it", "cantTell", "4.1.2/C2", "Posteggi bici", main, "#mostra-mappa",
              "The toggle conveys its state only by changing its own name ('Mostra'/'Nascondi mappa') without aria-expanded; whether a name change is an adequate programmatic state is debated.",
              org="Città di Modellina", diff="hard")


def c_hover_menu_it(rng):
    css = (".menu-top{list-style:none;display:flex;gap:18px;padding:0;margin:0 0 16px}.menu-top > li{position:relative}"
           ".menu-top .sotto{position:absolute;top:100%;left:0;background:#ffffff;border:1px solid #c9d3d8;list-style:none;"
           "padding:8px 12px;margin:0;min-width:200px}")
    main = """<nav aria-label="Servizi">
<ul class="menu-top">
<li id="voce-amm"><a href="amministrazione.html" id="link-amm" aria-haspopup="true" aria-expanded="false">Amministrazione</a>
<ul class="sotto" id="sotto-amm" hidden><li><a href="cancelleria.html">Cancelleria</a></li><li><a href="ufficio-tecnico.html">Ufficio tecnico</a></li><li><a href="controllo-abitanti.html">Controllo abitanti</a></li></ul></li>
<li><a href="tempo-libero.html">Tempo libero</a></li>
</ul>
</nav>
<h1>Benvenuti a Esempiano</h1>
<p>Il portale del Comune: servizi, notizie e appuntamenti.</p>
<script>
(function () {
  var voce = document.getElementById('voce-amm');
  var link = document.getElementById('link-amm');
  var sotto = document.getElementById('sotto-amm');
  function apri() { sotto.hidden = false; link.setAttribute('aria-expanded', 'true'); }
  function chiudi() { sotto.hidden = true; link.setAttribute('aria-expanded', 'false'); }
  voce.addEventListener('mouseenter', apri);
  voce.addEventListener('mouseleave', chiudi);
  link.addEventListener('focus', apri);
  voce.addEventListener('focusout', function (e) { if (!voce.contains(e.relatedTarget)) { chiudi(); } });
})();
</script>"""
    return _c(rng, "it", "cantTell", "4.1.2/C1", "Esempiano", main, "#link-amm",
              "A link that navigates on click but also opens a sub-menu on hover/focus, with aria-expanded updated by script: a dual-purpose control whose appropriate role (link vs menu button) and state handling need runtime inspection and are debated.",
              org="Comune di Esempiano", css=css, diff="hard")


SCENARIOS = [
    f_div_button_de, f_span_more_fr, f_accordion_no_state_it, f_stale_expanded_de, f_checkbox_no_checked_fr,
    f_icon_no_name_de, f_iframe_no_title_fr, f_hidden_focusable_it, f_img_link_no_alt_it, f_input_no_name_de,
    f_tab_no_selected_fr,
    p_native_button_de, p_native_checkbox_fr, p_native_select_it, p_disclosure_de, p_iframe_title_it, p_switch_fr,
    t_aria_button_de, t_details_fr, t_link_as_button_it, t_redundant_click_de, t_icon_aria_label_it,
    t_hidden_unfocusable_fr, t_sr_text_de,
    c_hash_button_de, c_link_opens_dialog_fr, c_text_toggle_it, c_hover_menu_it,
]


def build(rng):
    return [fn(rng) for fn in SCENARIOS]
