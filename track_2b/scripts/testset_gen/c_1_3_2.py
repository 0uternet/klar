"""1.3.2 Meaningful Sequence – hand-written scenarios (see protocol_parts/1.3.2.md)."""
from common import *
from _structure_util import mk, icon_svg, news_box

CRITERION = "1.3.2"


def _c(rng, lang, expected, rule, title, main, target, notes, **kw):
    return mk(CRITERION, rng, lang, expected, rule, title, main, target, notes, **kw)


# ---------------------------------------------------------------------------
# failed
# ---------------------------------------------------------------------------

def f_steps_order_de(rng):
    css = (".schritte{display:flex;flex-wrap:wrap;gap:28px;margin:1em 0}"
           ".schritt{flex:1 1 180px;border:2px solid #1f6f8b;border-radius:8px;padding:12px;position:relative}"
           ".schritt:nth-child(1){order:3}.schritt:nth-child(2){order:1}.schritt:nth-child(3){order:2}"
           ".schritt:nth-child(2)::after,.schritt:nth-child(3)::after{content:\"\";position:absolute;right:-24px;top:40%;"
           "border:9px solid transparent;border-left-color:#1f6f8b}")
    main = """<h1>Parkkarte für die blaue Zone</h1>
<p>Anwohnerinnen und Anwohner können eine Jahresparkkarte für die blaue Zone beantragen. So kommen Sie zu Ihrer Karte:</p>
<div class="schritte" id="ablauf">
<div class="schritt">Karte am Schalter der Gemeindepolizei abholen, Ausweis mitbringen</div>
<div class="schritt">Formular «Parkkarte Anwohnende» online ausfüllen</div>
<div class="schritt">Gebühr von CHF 240.– mit der zugestellten Rechnung bezahlen</div>
</div>
<p>Die Karte ist ein Jahr gültig und an das Kontrollschild gebunden.</p>"""
    return _c(rng, "de", "failed", "1.3.2/F1", "Parkkarte blaue Zone", main, "#ablauf",
              "CSS order shows the steps as form → fee → pick-up, but in the DOM 'Karte abholen' comes first; the reading order inverts a meaningful sequence (F1, C27).",
              org="Gemeinde Beispielwil", css=css, diff="medium")


def f_hours_grid_fr(rng):
    css = (".grille{display:grid;grid-template-rows:repeat(5,auto);grid-auto-flow:column;grid-template-columns:9em auto;"
           "gap:4px 18px;justify-content:start}.grille .jour{font-weight:700}")
    main = """<h1>Guichet de l'administration communale</h1>
<p>Le guichet se trouve au rez-de-chaussée de la maison de commune, place du Village 2.</p>
<h2>Horaires d'ouverture</h2>
<div class="grille" id="horaires">
<span class="jour">Lundi</span><span class="jour">Mardi</span><span class="jour">Mercredi</span><span class="jour">Jeudi</span><span class="jour">Vendredi</span>
<span>fermé</span><span>8 h 30 – 11 h 30</span><span>8 h 30 – 11 h 30 et 14 h – 18 h</span><span>fermé</span><span>8 h 30 – 11 h 30</span>
</div>
<p>Sur rendez-vous, nous vous recevons aussi en dehors de ces horaires.</p>"""
    return _c(rng, "fr", "failed", "1.3.2/F1", "Horaires du guichet", main, "#horaires",
              "The grid visually pairs each weekday with its hours, but the DOM lists all five days and then all five time slots, so the reading order separates days from their hours (F1).",
              org="Commune d'Exempleval", css=css, diff="medium")


def f_faq_reverse_it(rng):
    css = (".faq{display:flex;flex-direction:column-reverse;border-bottom:1px solid #c9d3d8;padding:10px 0}"
           ".faq p{margin:0}.faq .domanda{font-weight:700;margin-bottom:4px}")
    main = """<h1>Domande frequenti sulla tassa rifiuti</h1>
<p>Qui trovate le risposte alle domande più frequenti sulla nuova tassa causale.</p>
<div id="faq">
<div class="faq"><p class="risposta">La tassa base viene fatturata in aprile; la tassa sul sacco si paga al momento dell'acquisto dei sacchi ufficiali.</p><p class="domanda">Quando ricevo la fattura?</p></div>
<div class="faq"><p class="risposta">Tutte le economie domestiche e tutte le aziende con sede nel Comune.</p><p class="domanda">Chi deve pagare la tassa base?</p></div>
<div class="faq"><p class="risposta">Nei negozi di alimentari del Comune e allo sportello della cancelleria.</p><p class="domanda">Dove posso comprare i sacchi ufficiali?</p></div>
</div>"""
    return _c(rng, "it", "failed", "1.3.2/F1", "FAQ tassa rifiuti", main, "#faq",
              "flex-direction:column-reverse displays each question above its answer, but in the DOM every answer precedes its question, so the reading order is answer-then-question (F1).",
              org="Comune di Esempiano", css=css, diff="easy")


def f_line_reverse_de(rng):
    css = (".linie{list-style:none;display:flex;flex-direction:column-reverse;border-left:4px solid #e07a2e;"
           "margin:1em 0 1em 8px;padding-left:18px}.linie li{position:relative;padding:6px 0}"
           ".linie li::before{content:\"\";position:absolute;left:-27px;top:12px;width:14px;height:14px;border-radius:50%;"
           "background:#ffffff;border:3px solid #e07a2e}")
    main = """<h1>Linie 7: Bahnhof – Friedhof</h1>
<p>Die Linie 7 fährt von Montag bis Samstag im Halbstundentakt. Haltestellen in Fahrtrichtung Friedhof:</p>
<ul class="linie" id="haltestellen">
<li>Friedhof</li>
<li>Spital</li>
<li>Schulhaus Seematte</li>
<li>Dorfplatz</li>
<li>Bahnhof</li>
</ul>
<p>Fahrzeit bis zur Endhaltestelle: 14 Minuten.</p>"""
    return _c(rng, "de", "failed", "1.3.2/F1", "Linie 7", main, "#haltestellen",
              "The stop diagram reads Bahnhof → Friedhof from top to bottom only through column-reverse; the DOM lists the stops against the direction of travel announced in the text (F1).",
              org="Beispielwiler Verkehrsbetriebe", css=css, diff="medium")


def f_quiz_fr(rng):
    css = (".question{display:flex;flex-direction:column;border:1px solid #c9d3d8;border-radius:8px;padding:12px;margin:12px 0}"
           ".question .enonce{order:-1;font-weight:700;margin:0 0 6px}.question ul{list-style:none;padding:0;margin:0}"
           ".question label{display:inline;font-weight:400;margin-left:6px}")
    main = """<h1>Quiz : êtes-vous champion du tri ?</h1>
<p>Testez vos connaissances. Les solutions s'affichent après l'envoi.</p>
<form action="quiz-resultat.html" method="get">
<div class="question" id="question-1">
<ul role="radiogroup" aria-labelledby="enonce-1">
<li><input type="radio" name="q1" id="q1a" value="a"><label for="q1a">Dans le conteneur à verre</label></li>
<li><input type="radio" name="q1" id="q1b" value="b"><label for="q1b">Dans le sac taxé</label></li>
<li><input type="radio" name="q1" id="q1c" value="c"><label for="q1c">À la déchetterie, benne « verre plat »</label></li>
</ul>
<p class="enonce" id="enonce-1">Question 1 – Où faut-il jeter une vitre cassée ?</p>
</div>
<div class="question" id="question-2">
<p class="enonce" id="enonce-2">Question 2 – Les capsules de café en aluminium vont…</p>
<ul role="radiogroup" aria-labelledby="enonce-2">
<li><input type="radio" name="q2" id="q2a" value="a"><label for="q2a">au point de collecte des capsules</label></li>
<li><input type="radio" name="q2" id="q2b" value="b"><label for="q2b">dans le compost</label></li>
</ul>
</div>
<p><button type="submit">Voir mes résultats</button></p>
</form>"""
    return _c(rng, "fr", "failed", "1.3.2/F1", "Quiz du tri", main, "#question-1",
              "In question 1 the statement is moved above the answer options with order:-1, but in the DOM the options come before the question they answer (question 2 is in the right order) (F1).",
              org="Commune de Valfictif", css=css, diff="medium")


def f_prices_abs_it(rng):
    css = (".listino{position:relative;max-width:22em}.listino ul{list-style:none;margin:0;padding:0}"
           ".listino li{padding:4px 0;border-bottom:1px dotted #9aa5ab}.categorie{width:14em}"
           ".importi{position:absolute;top:0;left:14em;width:8em;text-align:right}")
    main = """<h1>Piscina comunale all'aperto</h1>
<p>La piscina è aperta dal 1° giugno al 31 agosto, tutti i giorni dalle 9.00 alle 19.30.</p>
<h2>Tariffe d'entrata</h2>
<div class="listino" id="tariffe">
<ul class="categorie"><li>Adulti</li><li>Ragazzi 6–16 anni</li><li>AVS/AI</li><li>Bambini sotto i 6 anni</li></ul>
<ul class="importi"><li>CHF 8.–</li><li>CHF 4.–</li><li>CHF 6.–</li><li>gratis</li></ul>
</div>
<p>Abbonamento stagionale per famiglie: CHF 150.–.</p>"""
    return _c(rng, "it", "failed", "1.3.2/F1", "Piscina – tariffe", main, "#tariffe",
              "Absolute positioning puts the prices beside their categories, but the DOM reads all four categories and then all four prices, so the price-to-category pairing is lost in reading order (F1).",
              org="Comune di Valfittizia", css=css, diff="medium")


def f_pre_columns_de(rng):
    main = """<h1>Mitteilungsblatt November 2026</h1>
<p>Das Mitteilungsblatt erscheint monatlich. Hier die wichtigsten Meldungen im Textformat:</p>
<pre id="mitteilung">GEMEINDEVERSAMMLUNG               CHRISTBAUMVERKAUF
Die Versammlung findet am         Der Forstbetrieb verkauft am
Montag, 30. November 2026,        Samstag, 12. Dezember 2026,
um 20.00 Uhr in der Turnhalle     ab 9.00 Uhr Bäume aus dem
statt. Traktanden: Budget         Gemeindewald beim Werkhof.
2027 und Steuerfuss.              Für Glühwein ist gesorgt.</pre>"""
    return _c(rng, "de", "failed", "1.3.2/F2", "Mitteilungsblatt", main, "#mitteilung",
              "Two text columns are created with spaces inside a <pre>; read line by line, sentences of both notices are interleaved (F33/F34).",
              org="Gemeinde Fiktal", diff="easy")


def f_spaced_letters_it(rng):
    css = (".striscione{background:#c2453b;color:#ffffff;font-weight:700;font-size:1.3rem;padding:10px 16px;"
           "border-radius:6px;text-align:center}")
    main = """<h1>Ufficio tecnico comunale</h1>
<p class="striscione" id="avviso-trasloco">C H I U S O &nbsp; P E R &nbsp; T R A S L O C O</p>
<p>Dal 2 al 6 novembre 2026 l'Ufficio tecnico si trasferisce in Via alla Stazione 14. Per le urgenze telefonate al numero 091 000 22 33.</p>
<p>Dal 9 novembre vi accogliamo nei nuovi uffici con gli orari abituali.</p>"""
    return _c(rng, "it", "failed", "1.3.2/F3", "Ufficio tecnico", main, "#avviso-trasloco",
              "Letter spacing is produced with space characters inside the words ('C H I U S O'), so the words are not programmatically determinable in sequence (F32; C8 would be sufficient).",
              org="Comune di Esempiano", css=css, diff="easy")


def f_layout_table_de(rng):
    css = "table.spalten,table.spalten td{border:0;padding:0 18px 0 0;vertical-align:top}"
    main = """<h1>Schulhaussanierung bewilligt</h1>
<table role="presentation" class="spalten" id="zweispaltig">
<tr><td>Die Gemeindeversammlung hat</td><td>Die Arbeiten beginnen in den</td></tr>
<tr><td>am 16. Juni 2026 den Kredit</td><td>Sommerferien 2027 und dauern</td></tr>
<tr><td>von CHF 1,2 Millionen für die</td><td>voraussichtlich bis im Herbst</td></tr>
<tr><td>Sanierung des Schulhauses genehmigt.</td><td>2028. Der Unterricht findet im Pavillon statt.</td></tr>
</table>"""
    return _c(rng, "de", "failed", "1.3.2/F4", "Schulhaussanierung", main, "#zweispaltig",
              "A layout table builds two newspaper columns line by line; linearised row by row, the lines of both columns alternate and the text no longer makes sense (F49).",
              org="Gemeinde Beispielberg", css=css, diff="medium")


def f_itinerary_grid_fr(rng):
    css = (".etapes{display:grid;gap:8px;margin:1em 0}.e1{grid-row:1}.e2{grid-row:2}.e3{grid-row:3}.e4{grid-row:4}"
           ".etape{border-left:4px solid #3c8d4f;padding:6px 12px;background:#eef3e8}")
    main = """<h1>Randonnée du col des Écureuils</h1>
<p>Boucle de 14 km, 650 m de dénivelé, environ 5 heures de marche. Itinéraire étape par étape :</p>
<div class="etapes" id="itineraire">
<div class="etape e2"><strong>Col des Écureuils</strong> – montée raide dans la forêt, pique-nique au sommet.</div>
<div class="etape e4"><strong>Retour en bus</strong> – ligne 21 depuis la plage, départ toutes les heures.</div>
<div class="etape e1"><strong>Gare de Valfictif</strong> – départ du sentier balisé en jaune.</div>
<div class="etape e3"><strong>Lac de la Combe</strong> – descente par les pâturages, baignade possible.</div>
</div>"""
    return _c(rng, "fr", "failed", "1.3.2/F1", "Randonnée", main, "#itineraire",
              "grid-row places the stages in walking order on screen, but the DOM order is col → bus → station → lake, so the route is read in a meaningless order (F1, C27).",
              org="Commune de Valfictif", css=css, diff="medium")


# ---------------------------------------------------------------------------
# passed
# ---------------------------------------------------------------------------

def p_steps_ol_it(rng):
    css = ".passi{display:flex;flex-wrap:wrap;gap:16px;padding-left:1.4em}.passi li{flex:1 1 160px;border:1px solid #c9d3d8;border-radius:8px;padding:10px}"
    main = """<h1>Permesso di pesca annuale</h1>
<p>Il permesso di pesca per i corsi d'acqua comunali si richiede in tre passi:</p>
<ol class="passi" id="passi">
<li>Compila il modulo online con i tuoi dati.</li>
<li>Paga la tassa di CHF 60.– con la fattura QR.</li>
<li>Ritira il permesso allo sportello comunale.</li>
</ol>"""
    return _c(rng, "it", "passed", "1.3.2/P1", "Permesso di pesca", main, "#passi",
              "The steps are laid out horizontally with flex but the DOM order equals the visual order (C27, G57).",
              org="Comune di Valfittizia", css=css, diff="easy")


def p_hours_table_de(rng):
    main = """<h1>Werkhof und Sammelstelle</h1>
<table id="oeffnungszeiten-tabelle">
<caption>Öffnungszeiten der Sammelstelle</caption>
<tr><th scope="col">Tag</th><th scope="col">Zeit</th></tr>
<tr><th scope="row">Mittwoch</th><td>13.30–17.00 Uhr</td></tr>
<tr><th scope="row">Freitag</th><td>13.30–18.30 Uhr</td></tr>
<tr><th scope="row">Samstag</th><td>8.00–12.00 Uhr</td></tr>
</table>
<p>An Feiertagen bleibt die Sammelstelle geschlossen.</p>"""
    return _c(rng, "de", "passed", "1.3.2/P1", "Werkhof", main, "#oeffnungszeiten-tabelle",
              "Days and times are in a table whose DOM order matches the visual rows; reading order keeps each day with its time.",
              org="Gemeinde Ober-Beispielwil", diff="easy")


def p_faq_details_fr(rng):
    css = "details{border-bottom:1px solid #c9d3d8;padding:8px 0}summary{font-weight:700;cursor:pointer}"
    main = """<h1>Inscription à l'accueil parascolaire</h1>
<div id="faq-accueil">
<details><summary>Jusqu'à quand puis-je inscrire mon enfant ?</summary><p>Les inscriptions pour l'année scolaire 2027-2028 sont ouvertes jusqu'au 15 mars 2027.</p></details>
<details><summary>Combien coûte une journée ?</summary><p>Le tarif dépend du revenu des parents et varie entre CHF 12.– et CHF 68.– par jour.</p></details>
<details><summary>Les repas sont-ils compris ?</summary><p>Oui, le repas de midi et le goûter sont inclus dans le tarif.</p></details>
</div>"""
    return _c(rng, "fr", "passed", "1.3.2/P1", "Accueil parascolaire", main, "#faq-accueil",
              "Each question precedes its answer both visually and in the DOM (details/summary); no CSS reordering.",
              org="Ville de Bourg-Modèle", css=css, diff="easy")


def p_css_columns_de(rng):
    css = "#artikel{column-count:2;column-gap:32px}#artikel p{margin-top:0}"
    main = """<h1>150 Jahre Feuerwehr Beispielberg</h1>
<div id="artikel">
<p>Am 1. Mai 1876 gründeten zwölf Männer aus dem Dorf die erste Feuerwehr. Ausgerüstet waren sie mit einer handbetriebenen Pumpe und ledernen Eimern.</p>
<p>Heute zählt die Feuerwehr 48 Angehörige, darunter elf Frauen. Sie rückt jährlich zu rund 60 Einsätzen aus – von Wasserschäden bis zu Verkehrsunfällen.</p>
<p>Zum Jubiläum lädt die Feuerwehr am 5. September 2026 zum Tag der offenen Tür ins Magazin an der Schulhausstrasse 8 ein.</p>
</div>"""
    return _c(rng, "de", "passed", "1.3.2/P1", "150 Jahre Feuerwehr", main, "#artikel",
              "The article is shown in two CSS columns; the text flows in DOM order down the first and then the second column, so reading order matches.",
              org="Gemeinde Beispielberg", css=css, diff="medium")


def p_layout_table_fr(rng):
    css = "table.mise,table.mise td{border:0;vertical-align:top;padding:0 20px 0 0}"
    main = """<h1>Bulletin d'information – automne 2026</h1>
<table role="presentation" class="mise" id="bulletin">
<tr><td><p><strong>Nouvelle ligne de bus.</strong> Depuis le 14 décembre, la ligne 21 relie la gare à la plage toutes les heures, aussi le dimanche.</p></td>
<td><p><strong>Soirée des aînés.</strong> Le repas annuel des aînés aura lieu le 28 novembre 2026 à la salle polyvalente. Inscription au greffe.</p></td></tr>
</table>"""
    return _c(rng, "fr", "passed", "1.3.2/P1", "Bulletin d'automne", main, "#bulletin",
              "Layout table whose cells each hold a complete, independent item; linearised row by row the content still reads correctly (F49 not met).",
              org="Commune de Valfictif", css=css, diff="medium")


# traps --------------------------------------------------------------------

def t_sidebar_first_de(rng):
    css = (".layout{display:flex;flex-wrap:wrap;gap:24px}.layout .haupt{flex:1 1 380px}"
           ".layout .seitenleiste{order:-1;flex:0 0 220px}")
    main = """<div class="layout" id="inhalt">
<div class="haupt">
<h1>Steuererklärung 2026</h1>
<p>Die Formulare für die Steuererklärung 2026 werden Ende Januar 2027 verschickt. Die Frist für die Einreichung ist der 31. März 2027.</p>
<p>Eine Fristerstreckung bis zum 30. September können Sie kostenlos online beantragen.</p>
</div>
<aside class="seitenleiste box">
<h2>Steueramt</h2>
<p>Dorfstrasse 1<br>Telefon 032 000 12 40<br>Mo–Fr 8.30–11.30 Uhr</p>
</aside>
</div>"""
    return _c(rng, "de", "passed", "1.3.2/T1", "Steuererklärung", main, "#inhalt",
              "The contact sidebar is displayed left of the article via order:-1 but comes after it in the DOM; the two blocks are independent, so their relative order does not affect meaning.",
              org="Gemeinde Beispielwil", css=css, trap=True, diff="medium")


def t_deco_image_first_fr(rng):
    css = ".actu{display:flex;flex-direction:column;max-width:520px}.actu img{order:-1;border-radius:8px;margin-bottom:8px}"
    img = asset("scene-snow-actu", scene("snow", w=520, h=220, seed=5))
    main = f"""<h1>Actualités</h1>
<article class="actu" id="actu-deneigement">
<h2>Service hivernal : déneigement des trottoirs</h2>
<p>Dès la première neige, les équipes de voirie déneigent les routes principales dès 4 h du matin. Merci de ne pas stationner sur les trottoirs.</p>
<img src="{img}" alt="" width="520" height="220">
</article>"""
    return _c(rng, "fr", "passed", "1.3.2/T2", "Actualités", main, "#actu-deneigement",
              "The decorative illustration (alt=\"\") is moved visually above the heading by CSS; it carries no information, so the reading order of the meaningful content is unchanged.",
              org="Ville de Bourg-Modèle", css=css, trap=True, diff="medium")


def t_icon_row_reverse_it(rng):
    css = (".scarica{list-style:none;padding:0}.scarica li{margin:6px 0}"
           ".scarica a{display:inline-flex;flex-direction:row-reverse;align-items:center;gap:8px}")
    ic = icon_svg("download", 20)
    main = f"""<h1>Moduli per la scuola dell'infanzia</h1>
<p>Scaricate i moduli, compilateli e consegnateli in segreteria entro il 31 gennaio 2027.</p>
<ul class="scarica" id="moduli">
<li><a href="iscrizione-infanzia.pdf">{ic}<span>Modulo di iscrizione (PDF, 85 kB)</span></a></li>
<li><a href="refezione.pdf">{ic}<span>Richiesta per la refezione (PDF, 60 kB)</span></a></li>
<li><a href="trasporto.pdf">{ic}<span>Richiesta per il trasporto scolastico (PDF, 58 kB)</span></a></li>
</ul>"""
    return _c(rng, "it", "passed", "1.3.2/T2", "Moduli scuola dell'infanzia", main, "#moduli",
              "row-reverse only moves a decorative aria-hidden icon to the other side of the link text; the meaningful content keeps its order.",
              org="Scuola di Esempiano", css=css, trap=True, diff="easy")


def t_cards_featured_de(rng):
    css = ".cards .hervorgehoben{order:-1;grid-column:span 2;background:#eef3e8}.card h3{margin-top:0}"
    main = """<h1>Meldungen aus der Gemeinde</h1>
<div class="cards" id="meldungen">
<article class="card"><h3>Neue Sitzbänke am Seeweg</h3><p>Der Werkdienst hat entlang des Seewegs acht neue Sitzbänke aus Gemeindeholz aufgestellt.</p></article>
<article class="card"><h3>Hundekot-Säckli</h3><p>Die Spender beim Schulhaus und beim Friedhof wurden aufgefüllt. Bitte benutzen Sie sie.</p></article>
<article class="card hervorgehoben"><h3>Gemeindeversammlung vom 30. November</h3><p>Traktanden sind das Budget 2027 und der Steuerfuss. Die Unterlagen liegen in der Kanzlei auf.</p></article>
</div>"""
    return _c(rng, "de", "passed", "1.3.2/T1", "Meldungen", main, "#meldungen",
              "The featured card is moved to the front by CSS, but the three news cards are independent items; their order does not change meaning (Understanding 1.3.2).",
              org="Gemeinde Fiktal", css=css, trap=True, diff="medium")


def t_nav_after_main_fr(rng):
    css = (".page{display:flex;flex-direction:column}.page .nav-site{order:-1;background:#0b4f6c;padding:10px 24px}"
           ".page .nav-site ul{list-style:none;display:flex;flex-wrap:wrap;gap:16px;margin:0;padding:0}"
           ".page .nav-site a{color:#ffffff;text-decoration:none}")
    body = """<div class="page" id="page">
<main>
<h1>Location de la salle polyvalente</h1>
<p>La salle polyvalente (300 places) peut être louée par les sociétés locales et les particuliers. Tarif : CHF 350.– par jour, nettoyage compris.</p>
<p>Réservations au greffe communal, au moins deux mois à l'avance.</p>
</main>
<nav class="nav-site" aria-label="Navigation principale">
<ul><li><a href="index.html">Accueil</a></li><li><a href="administration.html">Administration</a></li><li><a href="loisirs.html">Loisirs</a></li><li><a href="contact.html">Contact</a></li></ul>
</nav>
</div>"""
    return _c(rng, "fr", "passed", "1.3.2/T1", "Location de salle", body, "#page",
              "The main navigation is shown on top but follows the main content in the DOM; Understanding 1.3.2 states the relative order of navigation and main content does not affect meaning.",
              org="Commune d'Exempleval", css=css, trap=True, diff="hard", raw=True)


def t_date_badge_it(rng):
    css = (".evento{display:flex;flex-direction:column;max-width:460px}.evento .data{order:-1;font-weight:700;color:#7a1f2b;margin:0}"
           ".evento h2{margin:.2em 0}")
    main = """<h1>Agenda</h1>
<article class="evento card" id="evento-castagnata">
<h2>Castagnata in piazza</h2>
<p class="data">domenica 25 ottobre 2026</p>
<p>Caldarroste, vin brulé e musica popolare dalle 14.00 in Piazza Grande. Organizza la Pro Esempiano.</p>
</article>"""
    return _c(rng, "it", "passed", "1.3.2/T1", "Agenda", main, "#evento-castagnata",
              "The date is shown above the event title but follows it in the DOM; title-then-date conveys exactly the same information, so the sequence is not meaningful here.",
              org="Comune di Esempiano", css=css, trap=True, diff="medium")


# ---------------------------------------------------------------------------
# cantTell
# ---------------------------------------------------------------------------

def c_notice_after_form_de(rng):
    css = ".antrag{display:flex;flex-direction:column}.antrag .vorbereitung{order:-1}"
    main = """<h1>Prämienverbilligung beantragen</h1>
<div class="antrag" id="antrag">
<form action="antrag-gesendet.html" method="post">
<label for="ahv">AHV-Nummer</label>
<input id="ahv" name="ahv" type="text" inputmode="numeric">
<label for="einkommen">Steuerbares Einkommen gemäss letzter Veranlagung (CHF)</label>
<input id="einkommen" name="einkommen" type="text" inputmode="numeric">
<p><button type="submit">Antrag senden</button></p>
</form>
<p class="vorbereitung box">Halten Sie Ihre AHV-Nummer und die letzte definitive Steuerveranlagung bereit, bevor Sie beginnen.</p>
</div>"""
    return _c(rng, "de", "cantTell", "1.3.2/C1", "Prämienverbilligung", main, "#antrag",
              "The 'have these documents ready' note is shown above the form but follows the submit button in the DOM; whether this preparatory note's position is part of a meaningful sequence is debatable.",
              org="Gemeinde Ober-Beispielwil", css=css, alt="failed", diff="hard")


def c_summary_box_fr(rng):
    css = ".article-budget{display:flex;flex-direction:column}.article-budget .essentiel{order:-1}"
    main = """<article class="article-budget" id="article-budget">
<h1>Budget 2027 : un léger excédent</h1>
<p>Le Conseil communal présente un budget 2027 avec un excédent de revenus de CHF 84 000.–. Les charges augmentent de 2 % en raison des coûts scolaires.</p>
<p>Le taux d'imposition reste inchangé à 68 %. Les investissements prévus concernent surtout la rénovation du collège et le réseau d'eau.</p>
<div class="essentiel box"><p><strong>L'essentiel en bref :</strong> excédent de CHF 84 000.–, impôt inchangé, investissements de CHF 3,1 millions.</p></div>
</article>"""
    return _c(rng, "fr", "cantTell", "1.3.2/C1", "Budget 2027", main, "#article-budget",
              "The 'essentiel en bref' summary is displayed before the article text but placed after it in the DOM; a summary may be read before or after the body, so whether the sequence affects meaning is debatable.",
              org="Commune de Valfictif", css=css, diff="hard")


def c_kicker_it(rng):
    css = (".intestazione{display:flex;flex-direction:column}.intestazione .occhiello{order:-1;text-transform:uppercase;"
           "font-size:.85rem;letter-spacing:.06em;color:#4f5b62;margin:0}.intestazione h2{margin:.1em 0 .4em}")
    main = """<h1>Rifiuti e riciclaggio</h1>
<div class="intestazione" id="intestazione-tariffe">
<h2>Nuove tariffe per i sacchi ufficiali</h2>
<p class="occhiello">Novità da gennaio 2027</p>
</div>
<p>Il sacco da 35 litri costerà CHF 2.– invece di CHF 1.80; il sacco da 60 litri CHF 3.50. I sacchi già acquistati restano validi.</p>"""
    return _c(rng, "it", "cantTell", "1.3.2/C1", "Nuove tariffe", main, "#intestazione-tariffe",
              "The kicker 'Novità da gennaio 2027' is displayed above the heading but follows it in the DOM; whether heading-then-kicker changes the meaning is a judgement call.",
              org="Comune di Esempiano", css=css, diff="hard")


SCENARIOS = [
    f_steps_order_de, f_hours_grid_fr, f_faq_reverse_it, f_line_reverse_de, f_quiz_fr, f_prices_abs_it,
    f_pre_columns_de, f_spaced_letters_it, f_layout_table_de, f_itinerary_grid_fr,
    p_steps_ol_it, p_hours_table_de, p_faq_details_fr, p_css_columns_de, p_layout_table_fr,
    t_sidebar_first_de, t_deco_image_first_fr, t_icon_row_reverse_it, t_cards_featured_de, t_nav_after_main_fr,
    t_date_badge_it,
    c_notice_after_form_de, c_summary_box_fr, c_kicker_it,
]


def build(rng):
    return [fn(rng) for fn in SCENARIOS]
