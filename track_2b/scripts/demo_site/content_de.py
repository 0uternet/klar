"""German pages (site root)."""
from chrome import page, icon
from common import calendar, search_index, hours_grid

A = 'assets/'
L = 'de'


def build(R):
    out = {}

    # ------------------------------------------------------------------ index.html
    main = f'''<section class="hero" aria-labelledby="hero-title">
  <div class="container">
    <div class="hero-text" data-testid="hero-text">
      <h1 id="hero-title">Willkommen in Musterwil</h1>
      <p>Lebendige Gemeinde zwischen Aarenwald und Seeufer – und rund um die Uhr online für Sie da.</p>
    </div>
    <p class="hero-actions"><a class="btn btn-light" href="online-schalter.html">Zum Online-Schalter</a> <a class="btn" href="abfallkalender.html">Abfallkalender 2026</a></p>
  </div>
</section>

<nav class="quicklinks container" aria-label="Schnellzugriff">
  <ul>
    <li><a href="online-schalter.html"><span class="ql-icon">{icon("monitor")}</span><span class="ql-text"><strong>Online-Schalter</strong><small>Wohnsitzbestätigung und mehr</small></span></a></li>
    <li><a href="anleitung.html"><span class="ql-icon">{icon("box")}</span><span class="ql-text"><strong>Umzug melden</strong><small>eUmzug in fünf Schritten</small></span></a></li>
    <li><a href="abfallkalender.html"><span class="ql-icon">{icon("calendar")}</span><span class="ql-text"><strong>Abfallkalender</strong><small>Termine und Sammelstellen</small></span></a></li>
    <li><a href="oeffnungszeiten.html"><span class="ql-icon">{icon("clock")}</span><span class="ql-text"><strong>Öffnungszeiten</strong><small>Verwaltung, Werkhof, Bibliothek</small></span></a></li>
  </ul>
</nav>

<section class="section container" aria-labelledby="short-title">
  <div class="section-head"><h2 id="short-title">Kurz gemeldet</h2></div>
  <div class="tile-row">
    <div class="tile">
      <img src="{A}img/slide-seeufer.svg" alt="" width="640" height="360" data-testid="news-teaser-1-img">
      <div class="tile-label">Seeweg wieder offen</div>
      <p class="tile-more"><a href="freizeit.html" data-testid="news-teaser-1-more">Mehr</a></p>
    </div>
    <div class="tile">
      <img src="{A}img/slide-wald.svg" alt="" width="640" height="360" data-testid="news-teaser-2-img">
      <div class="tile-label">Forstarbeiten im Bannwald</div>
      <p class="tile-more"><a href="abfallkalender.html" data-testid="news-teaser-2-more">Mehr</a></p>
    </div>
    <div class="tile">
      <img src="{A}img/slide-dorfplatz.svg" alt="" width="640" height="360" data-testid="news-teaser-3-img">
      <div class="tile-label">Neue Sitzbänke am Dorfplatz</div>
      <p class="tile-more"><a href="zweisprachig.html" data-testid="news-teaser-3-more">Mehr</a></p>
    </div>
    <div class="tile">
      <img src="{A}img/slide-schiff.svg" alt="" width="640" height="360" data-testid="news-teaser-4-img">
      <div class="tile-label">Winterfahrplan Kursschiff</div>
      <p class="tile-more"><a href="oeffnungszeiten.html" data-testid="news-teaser-4-more">Mehr</a></p>
    </div>
  </div>
</section>

<section class="section container" aria-labelledby="news-title">
  <div class="section-head"><h2 id="news-title">Aktuelles</h2></div>
  <div class="grid-4">
    <article class="card">
      <img src="{A}img/news-gemeindehaus.svg" alt="Gemeindehaus Musterwil mit Uhrturm" width="640" height="360" data-testid="news-card-1-img">
      <div class="card-body">
        <p class="card-date"><time datetime="2026-10-12">12. Oktober 2026</time></p>
        <h3>Neue Schalteröffnungszeiten ab 1. November</h3>
        <p>Die Gemeindeverwaltung ist neu am Donnerstagabend bis 18.30 Uhr geöffnet. Dafür bleibt der Schalter am Mittwochnachmittag geschlossen.</p>
        <p class="card-more"><a href="oeffnungszeiten.html" data-testid="news-card-1-more">Mehr</a></p>
      </div>
    </article>
    <article class="card">
      <img src="{A}img/news-recycling.svg" alt="IMG_2041.jpg" width="640" height="360" data-testid="news-card-2-img">
      <div class="card-body">
        <p class="card-date"><time datetime="2026-10-08">8. Oktober 2026</time></p>
        <h3>Grüngutabfuhr im Winterrhythmus</h3>
        <p>Ab November holen wir das Grüngut nur noch alle zwei Wochen ab. Bitte beachten Sie die neuen Daten.</p>
        <p class="card-more"><a href="abfallkalender.html" data-testid="news-card-2-more">Mehr</a></p>
      </div>
    </article>
    <article class="card">
      <img src="{A}img/news-maerit.svg" alt="Marktstände mit Kürbissen, Äpfeln und Brot auf dem Dorfplatz" width="640" height="360" data-testid="news-card-3-img">
      <div class="card-body">
        <p class="card-date"><time datetime="2026-10-05">5. Oktober 2026</time></p>
        <h3>Herbstmärit am 24. Oktober</h3>
        <p>Über 40 Stände mit regionalen Produkten, Handwerk und Kürbissuppe – dazu spielt die Dorfmusik Musterwil.</p>
        <p class="card-more"><a href="freizeit.html" data-testid="news-card-3-more">Mehr</a></p>
      </div>
    </article>
    <article class="card">
      <img src="{A}img/news-velo.svg" alt="Zwei Kinder mit Velohelm und ihren Velos vor dem Schulhaus" width="640" height="360" data-testid="news-card-4-img">
      <div class="card-body">
        <p class="card-date"><time datetime="2026-10-01">1. Oktober 2026</time></p>
        <h3>Gratis-Service für Schulvelos</h3>
        <p data-testid="news-card-4-teaser">Bringen Sie Velo oder Trottinett am 31. Oktober zum Werkhof: Wir prüfen Bremsen, Licht und Reifen kostenlos.</p>
        <p class="card-more"><a href="velo-aktion.html" data-testid="news-card-4-more">Mehr</a></p>
      </div>
    </article>
  </div>

  <div class="teaser-strip">
    <span class="strip-icon">{icon("users")}</span>
    <div>
      <p>Der Gemeinderat hat an seiner Sitzung vom 6. Oktober 2026 das Budget 2027 verabschiedet und die Sanierung des Schulhauses Moosmatt für die Gemeindeversammlung vom 24. November traktandiert.</p>
      <p><a href="zweisprachig.html" data-testid="council-readmore">Weiterlesen</a></p>
    </div>
  </div>
</section>

<div class="container layout-main-aside section">
  <div class="main-col">
    <section aria-labelledby="admin-title">
      <h2 id="admin-title">Ihre Gemeindeverwaltung</h2>
      <p data-testid="intro-para">Ob Identitätskarte, Wohnsitzbestätigung oder Hundemarke: Die Gemeindeverwaltung an der Dorfstrasse 1 ist Ihre erste Anlaufstelle. Viele Dienstleistungen erledigen Sie rund um die Uhr am Online-Schalter; die neuen <a href="oeffnungszeiten.html" class="link-plain" data-testid="intro-inline-link">Öffnungszeiten</a> unserer Schalter gelten ab 1. November 2026.</p>
    </section>
    <aside class="notice" aria-labelledby="notice-title" data-testid="notice-box">
      <p class="notice-label">{icon("megaphone")}Mitteilung</p>
      <h2 id="notice-title">Mitteilung der Regionalkonferenz Aarenwald</h2>
      <p>Die Regionalkonferenz Aarenwald führt eine Vernehmlassung zum regionalen Velowegnetz durch. Die Mitteilung wird in der Originalsprache publiziert:</p>
      <p data-testid="notice-fr-para">Les communes de la région sont invitées à se prononcer sur le projet de réseau cyclable régional jusqu’au 30 novembre 2026. Le dossier peut être consulté à l’administration communale pendant les heures d’ouverture. Une séance d’information publique aura lieu le 5 novembre 2026 à 19 h 30 à la salle polyvalente de Musterwil.</p>
    </aside>
  </div>
  <div class="aside-col">
    <section class="box" aria-labelledby="tips-title">
      <h2 id="tips-title">Gut zu wissen</h2>
      <p data-testid="tips-sentence">Alle Termine der Grüngutabfuhr finden Sie im Abfallkalender – <a href="abfallkalender.html" data-testid="tips-sentence-more">mehr</a>.</p>
      <ul class="tick-list">
        <li>Die Gemeindebibliothek hat ab 2. November neue Öffnungszeiten – <a href="oeffnungszeiten.html#bibliothek" data-testid="tips-list-more">mehr</a></li>
        <li>Umzug innerhalb der Schweiz online melden – <a href="anleitung.html" data-testid="tips-list-more-2">mehr</a></li>
      </ul>
      <div class="mini-promo">
        <h3>Abfallkalender 2026</h3>
        <p>Alle Sammeldaten für Kehricht, Grüngut, Papier und Karton auf einen Blick.</p>
        <p><a class="btn btn-small" href="abfallkalender.html" aria-label="Mehr zum Abfallkalender 2026" data-testid="tips-aria-more">Mehr</a></p>
      </div>
    </section>
    <section class="box" aria-labelledby="contact-title">
      <h2 id="contact-title">Kontakt</h2>
      <div class="contact-row">
        <div>
          <p>Gemeindeverwaltung Musterwil<br>Dorfstrasse 1, 9999 Musterwil</p>
          <p>Telefon <a href="tel:+41320001234">032 000 12 34</a><br><a href="mailto:gemeinde@musterwil.example">gemeinde@musterwil.example</a></p>
        </div>
        <a class="icon-link" href="oeffnungszeiten.html#standort" data-testid="contact-map-link"><img src="{A}img/icon-map-pin.svg" alt="" width="24" height="24"></a>
      </div>
    </section>
  </div>
</div>

<section class="section-alt" aria-labelledby="events-title">
  <div class="container">
    <h2 id="events-title">Veranstaltungen</h2>
    <div class="events-layout">
      <ul class="event-list">
        <li class="event" data-testid="event-maerit">
          <p class="date-tile"><time datetime="2026-10-24"><span class="d">24</span><span class="m">Okt</span></time></p>
          <div><h3>Herbstmärit auf dem Dorfplatz</h3><p>Samstag, 9 bis 16 Uhr. Regionale Produkte, Handwerk und Kürbissuppe; um 11 Uhr lädt der Gemeinderat zum Apéro.</p></div>
        </li>
        <li class="event">
          <p class="date-tile"><time datetime="2026-11-11"><span class="d">11</span><span class="m">Nov</span></time></p>
          <div><h3>Räbeliechtli-Umzug</h3><p>Mittwoch, 18 Uhr, Start beim Schulhaus Moosmatt. Anschliessend offeriert der Elternverein heissen Punsch.</p></div>
        </li>
        <li class="event">
          <p class="date-tile"><time datetime="2026-11-24"><span class="d">24</span><span class="m">Nov</span></time></p>
          <div><h3>Gemeindeversammlung</h3><p>Dienstag, 19.30 Uhr, Mehrzweckhalle. Traktanden: Budget 2027 und Sanierung Schulhaus Moosmatt.</p></div>
        </li>
        <li class="event" data-testid="event-advent">
          <p class="date-tile"><time datetime="2026-12-04"><span class="d">4</span><span class="m">Dez</span></time></p>
          <div><h3>Erstes Adventsfenster</h3><p>Freitag, 18 Uhr. Das erste Adventsfenster öffnet sich im Café du Lac an der Seestrasse 3 – mit Glühwein und Lebkuchen.</p></div>
        </li>
      </ul>
      <figure class="banner-figure">
        <img src="{A}img/banner-versammlung-de.svg" alt="Gemeindeversammlung, 24. November 2026, 19.30 Uhr, Mehrzweckhalle" width="640" height="800" data-testid="assembly-banner">
      </figure>
    </div>
  </div>
</section>

<section class="section container" aria-labelledby="stats-title">
  <h2 id="stats-title">Musterwil in Zahlen</h2>
  <dl class="stats">
    <div><dt>Einwohnerinnen und Einwohner</dt><dd>3842</dd></div>
    <div><dt>Fläche</dt><dd>12,6 km²</dd></div>
    <div><dt>Höhe über Meer</dt><dd>431 m</dd></div>
    <div><dt>Vereine</dt><dd>41</dd></div>
  </dl>
  <p class="source" data-testid="stats-source">Quelle: Statistik der Bevölkerung und der Haushalte, Office fédéral de la statistique (OFS), Stand 31. Dezember 2025.</p>
</section>'''
    out['index.html'] = page(L, 'home', 'Gemeinde Musterwil', main,
                             description='Offizielle Website der Gemeinde Musterwil: Aktuelles, Online-Schalter, Abfallkalender und Veranstaltungen.')

    P = 'index.html'
    for i, label in enumerate(['Seeweg wieder offen', 'Forstarbeiten im Bannwald', 'Neue Sitzbänke am Dorfplatz', 'Winterfahrplan Kursschiff'], 1):
        R(P, f'news-teaser-{i}-more', '2.4.4', 'issue', 'failed',
          f'Link text "Mehr" sits alone in <p class="tile-more">; the tile label ("{label}") is a sibling block, the image is '
          f'decorative (alt=""), and there is no heading, sentence, list item, table cell or aria-describedby: no programmatic link context '
          f'(F63; ACT 5effbb failed). Sighted users read the label, so the purpose is not "ambiguous to users in general" → failed.')
    R(P, 'news-teaser-1-img', '1.1.1', 'trap', 'passed',
      'Understanding 1.1.1: the landscape picture in the teaser tile is decorative (the tile label carries the information), so alt="" is correct.')
    for i, title in enumerate(['Neue Schalteröffnungszeiten', 'Grüngutabfuhr im Winterrhythmus', 'Herbstmärit', 'Gratis-Service für Schulvelos'], 1):
        R(P, f'news-card-{i}-more', '2.4.4', 'issue', 'cantTell',
          f'Link text "Mehr" sits alone in <p class="card-more">: no sentence, paragraph, list item, table cell or aria-describedby context. '
          f'Only the card heading ("{title}") disambiguates it, and a preceding heading is not programmatic context (Klar. rule, Understanding 2.4.4) → cantTell; strict ACT 5effbb reading: failed.')
    R(P, 'news-card-1-img', '1.1.1', 'trap', 'passed', 'Understanding 1.1.1: short alt "Gemeindehaus Musterwil mit Uhrturm" names what the photo shows.')
    R(P, 'news-card-2-img', '1.1.1', 'issue', 'failed', 'Understanding 1.1.1: alt="IMG_2041.jpg" is a file name, not a text alternative for the recycling picture (F30).')
    R(P, 'news-card-3-img', '1.1.1', 'trap', 'passed', 'Understanding 1.1.1: alt describes the market scene in a few words.')
    R(P, 'hero-text', '1.4.3', 'issue', 'failed', 'Understanding 1.4.3: white h1 and lead text on the light-blue sky of the background image (#5fa6bd–#7cb9cc) give about 2.2–2.7:1, below 3:1 for large and 4.5:1 for normal text.')
    R(P, 'notice-fr-para', '3.1.2', 'issue', 'failed', 'Understanding 3.1.2: a full French paragraph (3 sentences) inside a de-CH page has no lang="fr"; screen readers read it with German pronunciation (H58).')
    R(P, 'council-readmore', '2.4.4', 'issue', 'failed', 'Understanding 2.4.4: "Weiterlesen" stands alone in its own paragraph with no heading, list item or aria context; the purpose cannot be determined from the link or its programmatic context.')
    R(P, 'intro-inline-link', '1.4.1', 'issue', 'failed', 'Understanding 1.4.1 / F73: inline link "Öffnungszeiten" has no underline and its colour #1f6f7a differs from the body text #1b2428 by only 2.7:1 (< 3:1).')
    R(P, 'contact-map-link', '1.1.1', 'issue', 'failed', 'Understanding 1.1.1 / F89: the map-pin image is the only content of the link and has alt="", so the link has no text alternative.')
    R(P, 'contact-map-link', '2.4.4', 'issue', 'failed', 'Understanding 2.4.4 (ACT c487ae): the link has an empty accessible name, so its purpose cannot be determined.')
    R(P, 'assembly-banner', '1.4.5', 'issue', 'failed', 'Understanding 1.4.5: the poster image carries the text "Gemeindeversammlung 24. November 2026, 19.30 Uhr, Mehrzweckhalle", which could be real styled text; it is not a logotype.')
    R(P, 'assembly-banner', '1.1.1', 'trap', 'passed', 'Understanding 1.1.1: the alt repeats all the text shown in the image.')
    R(P, 'tips-sentence-more', '2.4.4', 'trap', 'passed', 'Understanding 2.4.4: "mehr" is in the same sentence as "Alle Termine der Grüngutabfuhr finden Sie im Abfallkalender" (G53).')
    R(P, 'tips-list-more', '2.4.4', 'trap', 'passed', 'Understanding 2.4.4: "mehr" is inside a list item that names the topic (new library opening hours) (H78).')
    R(P, 'tips-list-more-2', '2.4.4', 'trap', 'passed', 'Understanding 2.4.4: list-item context "Umzug innerhalb der Schweiz online melden" gives the purpose (H78).')
    R(P, 'tips-aria-more', '2.4.4', 'trap', 'passed', 'Understanding 2.4.4 / ARIA8: aria-label="Mehr zum Abfallkalender 2026" gives the purpose.')
    R(P, 'tips-aria-more', '2.5.3', 'trap', 'passed', 'Understanding 2.5.3: the visible label "Mehr" is contained (at the start) in the accessible name "Mehr zum Abfallkalender 2026".')
    R(P, 'site-logo', '1.1.1', 'trap', 'passed', 'Understanding 1.1.1: the logo inside the home link has alt "Gemeinde Musterwil – Startseite", which names the link target.')
    R(P, 'site-logo', '1.4.5', 'trap', 'passed', 'Understanding 1.4.5: logotypes (text that is part of a logo) are essential and exempt.')
    R(P, 'site-logo', '1.4.3', 'trap', 'passed', 'Understanding 1.4.3: the light tagline in the logo (#8fb3b6, about 2.3:1) is part of a logotype and has no contrast requirement.')
    R(P, 'lang-switch', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2 / H58: each language-switcher link (FR, IT) carries its own lang and hreflang attribute.')
    R(P, 'event-advent', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: "Café du Lac" is a proper name and does not need lang markup.')
    R(P, 'event-maerit', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: "Märit" and "Apéro" are Swiss Standard German words (helvetisms), part of the surrounding language.')
    R(P, 'news-card-4-teaser', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: "Velo" and "Trottinett" are helvetisms of Swiss Standard German, not foreign phrases.')
    R(P, 'stats-source', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: "Office fédéral de la statistique" is the proper name of an institution; proper names are exempt.')
    R(P, None, '2.4.2', 'trap', 'passed', 'Understanding 2.4.2: the home page title "Gemeinde Musterwil" identifies the site and the home page.')
    R(P, None, '3.1.1', 'trap', 'passed', 'Understanding 3.1.1: <html lang="de-CH"> matches the German content.')

    # ------------------------------------------------------------------ online-schalter.html
    main = f'''<div class="container page-head">
  <h1>Online-Schalter</h1>
  <p class="lead">Viele Dienstleistungen der Gemeindeverwaltung können Sie bequem online bestellen. Die Unterlagen erhalten Sie per Post.</p>
</div>
<div class="container layout-main-aside">
  <div class="main-col">
    <div class="form-lang">
      <label for="form-lang">Formular in einer anderen Sprache</label>
      <select id="form-lang" data-testid="form-language-select" onchange="location.href=this.value">
        <option value="online-schalter.html" selected>Deutsch</option>
        <option value="fr/guichet-en-ligne.html" lang="fr">Français</option>
        <option value="it/sportello-online.html" lang="it">Italiano</option>
      </select>
    </div>
    <form class="form-card form-classic" id="residence-form" action="danke.html" method="get" data-form-mode="simple" data-success="danke.html" data-msg-error="Fehler" data-testid="residence-form">
      <h2>Wohnsitzbestätigung bestellen</h2>
      <p class="fee">Gebühr: CHF 20.– pro Exemplar. Sie erhalten die Bestätigung zusammen mit der Rechnung innert drei Arbeitstagen per Post.</p>
      <div class="form-alert" role="alert" data-error-summary data-testid="form-error-summary" hidden></div>
      <p class="hint">Pflichtfelder sind rot markiert.</p>
      <fieldset>
        <legend>Persönliche Angaben</legend>
        <div class="form-grid">
          <div class="field"><label for="f-given" class="label-required">Vorname</label><input id="f-given" name="vorname" type="text" autocomplete="given-name" data-required data-testid="form-given-name"></div>
          <div class="field"><label for="f-family" class="label-required" data-testid="form-family-name-label">Nachname</label><input id="f-family" name="nachname" type="text" autocomplete="family-name" data-required data-testid="form-family-name"></div>
          <div class="field field-nolabel"><input id="f-birth" name="geburtsdatum" type="text" inputmode="numeric" placeholder="TT.MM.JJJJ" autocomplete="bday" data-testid="form-birthdate"></div>
          <div class="field"><label for="f-email" class="label-required">E-Mail</label><input id="f-email" name="email" type="email" autocomplete="name" data-required data-kind="email" data-testid="form-email"></div>
          <div class="field"><label for="f-tel">Telefon</label><input id="f-tel" name="telefon" type="tel" autocomplete="tel" data-required data-testid="form-tel"></div>
          <div class="field"><label for="f-copies">Anzahl Exemplare</label><input id="f-copies" name="anzahl" type="number" min="1" max="5" value="1" data-testid="form-copies"></div>
        </div>
      </fieldset>
      <fieldset>
        <legend>Wohnadresse</legend>
        <div class="form-grid-3">
          <div class="field"><label for="f-street" class="label-required">Strasse und Nr.</label><input id="f-street" name="strasse" type="text" data-required data-testid="form-street"></div>
          <div class="field"><label for="f-plz" class="label-required">PLZ</label><input id="f-plz" name="plz" type="text" inputmode="numeric" autocomplete="postal-code" data-required data-pattern="^[0-9]{{4}}$" data-error-id="f-plz-error" data-testid="form-plz"><span class="field-error" id="f-plz-error" data-msg="Ungültige Eingabe" data-testid="form-plz-error" hidden></span></div>
          <div class="field"><label for="f-city" class="label-required">Ort</label><input id="f-city" name="ort" type="text" autocomplete="address-level2" data-required data-testid="form-city"></div>
        </div>
      </fieldset>
      <fieldset>
        <legend>Adressänderung melden (optional)</legend>
        <p class="hint">Nur ausfüllen, wenn Sie innerhalb von Musterwil umziehen.</p>
        <div class="form-grid">
          <div class="field"><label for="f-new-street">Neue Strasse und Nr.</label><input id="f-new-street" name="neue-strasse" type="text" autocomplete="street-address" data-testid="form-new-street"></div>
          <div class="field"><label for="f-move">Umzugsdatum <span class="hint-inline">(TT.MM.JJJJ)</span></label><input id="f-move" name="umzugsdatum" type="text" inputmode="numeric" data-testid="form-move-date"></div>
        </div>
      </fieldset>
      <div class="form-actions">
        <button type="button" class="btn btn-secondary" disabled data-testid="form-save-draft">Entwurf speichern</button>
        <button type="submit" class="btn" tabindex="1" aria-label="Formular abschicken" data-testid="form-submit">Senden</button>
      </div>
    </form>
  </div>
  <div class="aside-col">
    <section class="box" aria-labelledby="more-services">
      <h2 id="more-services">Weitere Dienstleistungen</h2>
      <ul class="link-list">
        <li><a href="anleitung.html">Umzug melden mit eUmzug</a></li>
        <li><a href="abfallkalender.html">Abfallkalender und Sammelstellen</a></li>
        <li><a href="oeffnungszeiten.html">Öffnungszeiten der Verwaltung</a></li>
      </ul>
    </section>
    <section class="box" aria-labelledby="questions">
      <h2 id="questions">Fragen?</h2>
      <p>Die Einwohnerkontrolle hilft Ihnen gerne weiter: Telefon <a href="tel:+41320001210">032 000 12 10</a>.</p>
    </section>
  </div>
</div>'''
    out['online-schalter.html'] = page(L, 'form', 'Online-Schalter – Gemeinde Musterwil', main, crumbs=['Online-Schalter'],
                                       scripts=('forms.js',), description='Wohnsitzbestätigung online bestellen und Adressänderung melden.')
    P = 'online-schalter.html'
    R(P, 'form-error-summary', '3.3.1', 'issue', 'failed', 'Understanding 3.3.1: on submit the summary only says "Fehler"; it neither identifies the fields in error nor describes the errors (container is filled by JS, empty in the static DOM).')
    R(P, 'form-plz-error', '3.3.1', 'issue', 'failed', 'Understanding 3.3.1: "Ungültige Eingabe" does not describe what is wrong with the postcode (injected by JS on submit).')
    R(P, 'form-plz-error', '3.3.3', 'issue', 'failed', 'Understanding 3.3.3: the expected format (4-digit Swiss postcode) is known but no correction is suggested.')
    R(P, 'form-street', '1.3.5', 'issue', 'failed', 'Understanding 1.3.5: the user\'s street address field has no autocomplete token (expected street-address or address-line1).')
    R(P, 'form-email', '1.3.5', 'issue', 'failed', 'Understanding 1.3.5: e-mail field carries autocomplete="name"; the token does not match the purpose (expected email).')
    R(P, 'form-given-name', '1.3.5', 'trap', 'passed', 'Understanding 1.3.5: autocomplete="given-name" matches the first-name field.')
    R(P, 'form-family-name', '1.3.5', 'trap', 'passed', 'Understanding 1.3.5: autocomplete="family-name" matches the last-name field.')
    R(P, 'form-plz', '1.3.5', 'trap', 'passed', 'Understanding 1.3.5: autocomplete="postal-code" matches the PLZ field.')
    R(P, 'form-city', '1.3.5', 'trap', 'passed', 'Understanding 1.3.5: autocomplete="address-level2" matches the town field.')
    R(P, 'form-tel', '1.3.5', 'trap', 'passed', 'Understanding 1.3.5: autocomplete="tel" matches the phone field.')
    R(P, 'form-birthdate', '1.3.5', 'trap', 'passed', 'Understanding 1.3.5: autocomplete="bday" matches the date-of-birth field.')
    R(P, 'form-new-street', '1.3.5', 'trap', 'passed', 'Understanding 1.3.5: autocomplete="street-address" identifies the (new) street address of the user.')
    R(P, 'form-copies', '1.3.5', 'trap', 'inapplicable', 'Understanding 1.3.5: "Anzahl Exemplare" does not collect information about the user, so no input purpose applies.')
    R(P, 'form-family-name-label', '1.4.1', 'issue', 'failed', 'Understanding 1.4.1: required fields are marked only by red label colour ("Pflichtfelder sind rot markiert"), with no asterisk or text.')
    R(P, 'form-given-name', '1.4.11', 'issue', 'failed', 'Understanding 1.4.11: the text-input border #dcdcdc on white is about 1.4:1 (< 3:1), so the field boundary is hard to perceive.')
    R(P, 'form-save-draft', '1.4.11', 'trap', 'passed', 'Understanding 1.4.11: inactive (disabled) user interface components are exempt.')
    R(P, 'form-save-draft', '1.4.3', 'trap', 'passed', 'Understanding 1.4.3: text in an inactive (disabled) control (#9aa5ab on #eef1f2) has no contrast requirement.')
    R(P, 'form-submit', '2.5.3', 'issue', 'failed', 'Understanding 2.5.3: visible label "Senden" is not contained in the accessible name aria-label="Formular abschicken"; speech users saying "Senden" cannot activate it.')
    R(P, 'form-submit', '2.4.3', 'issue', 'failed', 'Understanding 2.4.3 / F44: tabindex="1" on the submit button moves it to the start of the tab order, before the navigation and all form fields.')
    R(P, 'form-birthdate', '3.3.2', 'issue', 'failed', 'Understanding 3.3.2: the date-of-birth field has no label, only the placeholder "TT.MM.JJJJ", which disappears on input.')
    R(P, 'form-tel', '3.3.2', 'issue', 'failed', 'Understanding 3.3.2: the phone field is required (validated as required) but nothing tells the user so; it is not even red.')
    R(P, 'form-move-date', '3.3.2', 'trap', 'passed', 'Understanding 3.3.2: label "Umzugsdatum (TT.MM.JJJJ)" gives the field and its expected format.')
    R(P, 'residence-form', '3.3.4', 'issue', 'failed', 'Understanding 3.3.4: the form orders a billed certificate (CHF 20.–, financial commitment) and submits directly, with no review, confirmation or correction step.')
    R(P, 'form-language-select', '3.2.2', 'issue', 'failed', 'Understanding 3.2.2 / F37: choosing a language in the select runs location.href in onchange and leaves the page (losing input) without a submit button or prior warning.')
    R(P, 'print-button', '4.1.2', 'trap', 'passed', 'Understanding 4.1.2: native <button> with visible text "Drucken" exposes name and role.')

    # ------------------------------------------------------------------ danke.html
    main = f'''<div class="container narrow">
  <ol class="progress-steps" aria-label="Bestellvorgang">
    <li><span class="step-num">1</span>Angaben</li>
    <li class="current" aria-current="step"><span class="step-num">2</span>Bestätigung</li>
  </ol>
  <h1>Vielen Dank für Ihre Bestellung</h1>
  <div class="status status-success" role="status" data-testid="order-status">{icon("check")}<p><strong>Bestellung erfolgreich übermittelt.</strong> Ihre Bestellnummer lautet MW-2026-04817.</p></div>
  <p data-testid="thanks-para">Merci vielmal! Sie erhalten die Wohnsitzbestätigung innert drei Arbeitstagen per Post, zusammen mit der Rechnung über CHF 20.– pro Exemplar. Eine Kopie Ihrer Angaben senden wir Ihnen per E-Mail.</p>
  <p>Haben Sie Fragen zu Ihrer Bestellung? Die Einwohnerkontrolle erreichen Sie unter <a href="tel:+41320001210">032 000 12 10</a>.</p>
  <p class="button-row"><a class="btn" href="index.html">Zur Startseite</a> <a class="btn btn-secondary" href="online-schalter.html">Weitere Bestellung</a></p>
</div>'''
    out['danke.html'] = page(L, 'thanks', 'Bestellung bestätigt – Gemeinde Musterwil', main,
                             crumbs=[('Online-Schalter', 'online-schalter.html'), 'Bestätigung'])
    P = 'danke.html'
    R(P, None, '2.4.5', 'set', 'failed', 'Set-level criterion (PROTOCOL.md: the label applies to the set of pages of this language version). The German set FAILS 2.4.5, decided by velo-aktion.html, which is reachable only through one home-page teaser (designed failure). danke.html itself is exempt (result of a process, Understanding 2.4.5) and does not cause the failure.', scope='set', deciding_page='velo-aktion.html')
    R(P, 'order-status', '1.4.1', 'trap', 'passed', 'Understanding 1.4.1: success is shown by colour plus a check icon plus the text "Bestellung erfolgreich übermittelt".')
    R(P, 'thanks-para', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: "Merci vielmal" is an everyday Swiss German expression (helvetism), not a French passage.')

    # ------------------------------------------------------------------ abfallkalender.html
    main = f'''<div class="container page-head">
  <h1>Abfallkalender 2026</h1>
  <p class="lead">Abfuhrtermine, Sammelstellen und Gebühren der Gemeinde Musterwil.</p>
</div>
<div class="container layout-main-aside">
  <div class="main-col">
    <p data-testid="waste-intro">Bitte stellen Sie Kehrichtsäcke und Grüngutcontainer am Abfuhrtag <strong data-testid="pickup-time-emphasis">bis 7 Uhr</strong> gut sichtbar an den Strassenrand. Gebührenpflichtige Kehrichtsäcke erhalten Sie im Dorfladen, in der Bäckerei am Dorfplatz und bei der Gemeindeverwaltung.</p>
    <p class="h-like" data-testid="waste-dates-title"><b>Abfuhrtermine 2026</b></p>
    <p>Die Termine im November auf einen Blick:</p>
    {calendar('de', letters=False)}
    <h2>Grüngut: Sammelmengen 2025</h2>
    <p>Die Grüngutmenge schwankt stark mit den Jahreszeiten. Im Winter sammeln wir deshalb nur alle zwei Wochen.</p>
    <figure class="chart-figure"><img src="{A}img/chart-gruengut-de.svg" alt="Bild" width="960" height="560" data-testid="waste-chart"></figure>
    <h2>Sammelstellen</h2>
    <div class="table-wrap">
      <table class="data-table" data-testid="collection-points-table">
        <caption>Sammelstellen und Annahmezeiten</caption>
        <thead><tr><th scope="col">Sammelstelle</th><th scope="col">Was wird angenommen?</th><th scope="col">Annahmezeiten</th></tr></thead>
        <tbody>
          <tr><th scope="row">Werkhof Moosmatt</th><td>Grüngut, Sperrgut, Altmetall, Elektrogeräte</td><td>Mi 13.30–17.00, Sa 09.00–12.00</td></tr>
          <tr><th scope="row">Sammelstelle Bahnhof</th><td>Glas, Aluminium, Weissblech</td><td>Mo–Sa 07.00–20.00</td></tr>
          <tr><th scope="row">Schulhaus Moosmatt</th><td>Altkleider und Schuhe</td><td>jederzeit (Container)</td></tr>
        </tbody>
      </table>
    </div>
    <h2>Gebühren und Reglement</h2>
    <p>Die Grundgebühr beträgt CHF 95.– pro Haushalt und Jahr. Ein 35-Liter-Kehrichtsack kostet CHF 2.20.</p>
    <ul class="doc-list"><li><a href="{A}docs/abfallreglement-musterwil.pdf" data-testid="regulation-pdf-link">{icon("file")}Abfallreglement (PDF, {{PDF_KB}} KB)</a></li></ul>
  </div>
  <div class="aside-col">
    <section class="box" aria-labelledby="next-title">
      <h2 id="next-title">Nächste Abfuhren</h2>
      <ul class="link-list">
        <li>Dienstag, 20. Oktober: Kehricht</li>
        <li>Donnerstag, 22. Oktober: Grüngut</li>
        <li>Mittwoch, 28. Oktober: Papier</li>
      </ul>
    </section>
    <section class="box" aria-labelledby="waste-contact">
      <h2 id="waste-contact">Fragen zur Entsorgung?</h2>
      <p>Werkhof Musterwil<br>Telefon <a href="tel:+41320001240">032 000 12 40</a></p>
    </section>
  </div>
</div>'''
    out['abfallkalender.html'] = page(L, 'waste', 'Abfallkalender 2026 – Gemeinde Musterwil', main, crumbs=['Abfallkalender'],
                                      nav_order=['waste', 'home', 'leisure', 'form', 'bilingual', 'hours', 'guide'],
                                      description='Abfuhrtermine für Kehricht, Grüngut, Papier und Karton in Musterwil.')
    P = 'abfallkalender.html'
    R(P, 'waste-chart', '1.1.1', 'issue', 'failed', 'Understanding 1.1.1: the bar chart (monthly green-waste tonnes 2025) has alt="Bild"; no data or trend is conveyed.')
    R(P, 'waste-dates-title', '1.3.1', 'issue', 'failed', 'Understanding 1.3.1 / F2: "Abfuhrtermine 2026" is a <p><b> styled exactly like an h2 but not marked up as a heading.')
    R(P, 'pickup-time-emphasis', '1.3.1', 'trap', 'passed', 'Understanding 1.3.1: bold "bis 7 Uhr" is emphasis inside running text, not a heading.')
    R(P, 'collection-points-table', '1.3.1', 'trap', 'passed', 'Understanding 1.3.1 / H51, H63: data table with caption and th scope="col"/"row".')
    R(P, 'waste-calendar', '1.4.1', 'issue', 'failed', 'Understanding 1.4.1: in the calendar the collection type (Kehricht, Grüngut, Papier, Karton) is shown only by the colour of a dot; the legend maps colours to names.')
    R(P, 'main-nav', '3.2.3', 'issue', 'failed', 'Set-level criterion (PROTOCOL.md: the label applies to the set of pages of this language version). Designed set-level failure; this page decides it: the main navigation lists the same links in a different order (Abfallkalender first) than on all other German pages (Understanding 3.2.3).', scope='set', deciding_page='abfallkalender.html')
    R(P, 'regulation-pdf-link', '2.4.4', 'trap', 'passed', 'Understanding 2.4.4: link text "Abfallreglement (PDF, n KB)" states the target and its format.')
    R(P, None, '2.4.2', 'trap', 'passed', 'Understanding 2.4.2: title "Abfallkalender 2026 – Gemeinde Musterwil" describes topic and site.')
    R(P, None, '2.4.5', 'set', 'failed', 'Set-level criterion (PROTOCOL.md: the label applies to the set of pages of this language version). The German set FAILS 2.4.5, decided by velo-aktion.html, which is reachable only through one home-page teaser (designed failure). abfallkalender.html itself is reachable via main navigation, sitemap and search.', scope='set', deciding_page='velo-aktion.html')

    # ------------------------------------------------------------------ oeffnungszeiten.html
    lib = hours_grid([('Montag', 'geschlossen'), ('Dienstag', '15.00–18.00'), ('Mittwoch', '14.00–18.00'),
                      ('Donnerstag', '15.00–19.00'), ('Freitag', 'geschlossen'), ('Samstag', '09.30–12.00')], wrong_order=True)
    main = f'''<div class="container page-head">
  <h1>Öffnungszeiten</h1>
  <p class="lead">Öffnungszeiten der Gemeindeverwaltung, des Werkhofs und der Gemeindebibliothek.</p>
</div>
<div class="container layout-main-aside">
  <div class="main-col">
    <section aria-labelledby="h-admin">
      <h2 id="h-admin" data-testid="admin-heading">Gemeindeverwaltung</h2>
      <div class="table-wrap">
        <table class="data-table" data-testid="hours-admin">
          <caption>Schalteröffnungszeiten ab 1. November 2026</caption>
          <thead><tr><th scope="col">Tag</th><th scope="col">Vormittag</th><th scope="col">Nachmittag</th></tr></thead>
          <tbody>
            <tr><th scope="row">Montag</th><td>08.00–11.30</td><td>14.00–17.00</td></tr>
            <tr><th scope="row">Dienstag</th><td>08.00–11.30</td><td>14.00–17.00</td></tr>
            <tr><th scope="row">Mittwoch</th><td>08.00–11.30</td><td>geschlossen</td></tr>
            <tr><th scope="row">Donnerstag</th><td>08.00–11.30</td><td>14.00–18.30</td></tr>
            <tr><th scope="row">Freitag</th><td>08.00–11.30</td><td>14.00–16.00</td></tr>
          </tbody>
        </table>
      </div>
      <p>Termine ausserhalb der Öffnungszeiten vereinbaren wir gerne telefonisch.</p>
    </section>
    <section>
      <h2 data-testid="werkhof-heading">Allgemeines</h2>
      <p>Werkhof und Entsorgungsstelle Moosmatt, Industriestrasse 8</p>
      <div class="table-wrap">
        <table class="data-table" data-testid="hours-werkhof">
          <tr class="thead-like"><td><strong>Tag</strong></td><td><strong>Öffnungszeit</strong></td></tr>
          <tr><td>Mittwoch</td><td>13.30–17.00</td></tr>
          <tr><td>Samstag</td><td>09.00–12.00</td></tr>
        </table>
      </div>
    </section>
    <section id="bibliothek" aria-labelledby="h-lib">
      <h2 id="h-lib">Gemeindebibliothek</h2>
      <p>Bibliothek an der Bahnhofstrasse 12, neue Öffnungszeiten ab 2. November 2026:</p>
      {lib}
    </section>
    <section id="standort" aria-labelledby="h-loc">
      <h2 id="h-loc">Standort und Anreise</h2>
      <div class="loc-grid">
        <img src="{A}img/map-standort.svg" alt="Lageplan: Die Gemeindeverwaltung liegt an der Dorfstrasse 1, rund 100 Meter von der Bushaltestelle Musterwil Dorf entfernt." width="800" height="450" data-testid="location-map">
        <div>
          <p>Gemeindeverwaltung Musterwil<br>Dorfstrasse 1<br>9999 Musterwil</p>
          <p>Bus Linie 12 bis Haltestelle «Musterwil Dorf». Hinter dem Gemeindehaus stehen vier Besucherparkplätze zur Verfügung.</p>
        </div>
      </div>
    </section>
    <section aria-labelledby="h-faq">
      <h2 id="h-faq">Häufige Fragen</h2>
      <div class="accordion">
        <div class="acc-item">
          <div class="acc-toggle" data-testid="faq-toggle-1">Ist die Verwaltung zwischen Weihnachten und Neujahr geöffnet?</div>
          <div class="acc-panel"><p>Vom 24. Dezember 2026 bis und mit 3. Januar 2027 bleibt die Verwaltung geschlossen. Bei Todesfällen erreichen Sie das Bestattungsamt unter 032 000 12 99.</p></div>
        </div>
        <div class="acc-item">
          <div class="acc-toggle" data-testid="faq-toggle-2">Kann ich ausserhalb der Öffnungszeiten vorbeikommen?</div>
          <div class="acc-panel"><p>Ja, nach telefonischer Vereinbarung. Rufen Sie uns während der Telefonzeiten an.</p></div>
        </div>
        <div class="acc-item">
          <div class="acc-toggle" data-testid="faq-toggle-3">Wo kann ich mein Velo abstellen?</div>
          <div class="acc-panel"><p>Vor dem Haupteingang gibt es einen gedeckten Veloständer mit zwölf Plätzen.</p></div>
        </div>
      </div>
    </section>
  </div>
  <div class="aside-col">
    <section class="box" aria-labelledby="phone-hours">
      <h2 id="phone-hours">Telefonzeiten</h2>
      <p>Mo–Fr 08.00–11.30 und 14.00–16.00 Uhr<br>Telefon <a href="tel:+41320001234">032 000 12 34</a></p>
    </section>
  </div>
</div>'''
    out['oeffnungszeiten.html'] = page(L, 'hours', 'Gemeinde Musterwil', main, crumbs=['Öffnungszeiten'], scripts=('accordion.js',))
    P = 'oeffnungszeiten.html'
    R(P, None, '2.4.2', 'issue', 'failed', 'Understanding 2.4.2 / F25: <title> is "Gemeinde Musterwil", identical to the home page, although the page is about opening hours.')
    R(P, 'hours-admin', '1.3.1', 'trap', 'passed', 'Understanding 1.3.1: opening-hours table with caption and th scope="col"/"row".')
    R(P, 'hours-werkhof', '1.3.1', 'issue', 'failed', 'Understanding 1.3.1 / F91: data table without <th>; the bold first row only looks like a header row.')
    R(P, 'werkhof-heading', '2.4.6', 'issue', 'failed', 'Understanding 2.4.6: the heading "Allgemeines" does not describe the section below (Werkhof opening hours).')
    R(P, 'admin-heading', '2.4.6', 'trap', 'passed', 'Understanding 2.4.6: heading "Gemeindeverwaltung" describes the section.')
    R(P, 'hours-library', '1.3.2', 'issue', 'failed', 'Understanding 1.3.2 / C27: CSS grid rows pair days and hours visually, but the DOM lists all six days first and then all six times, so the reading order is meaningless.')
    R(P, 'hours-library', '1.3.1', 'issue', 'failed', 'Understanding 1.3.1: the <dl> groups six <dt> before six <dd>, so programmatically every day is associated with every time; the visual day/time pairing is not in the structure.')
    for i in (1, 2, 3):
        R(P, f'faq-toggle-{i}', '4.1.2', 'issue', 'failed', 'Understanding 4.1.2: FAQ toggle is a <div> with a click handler: no button role, not focusable, no aria-expanded state.')
    R(P, 'location-map', '1.1.1', 'trap', 'passed', 'Understanding 1.1.1: the map image has an alt that gives the location information.')
    R(P, 'print-button', '3.2.4', 'set', 'failed', 'Set-level criterion (PROTOCOL.md: the label applies to the set of pages of this language version). The German set FAILS 3.2.4, decided by sitemap.html, where the search button is identified as „Finden“ with an arrow instead of „Suche“ with a magnifier (designed failure). The print button itself has the same icon, label and position on every content page.', scope='set', deciding_page='sitemap.html')
    R(P, 'main-nav', '3.2.3', 'set', 'failed', 'Set-level criterion (PROTOCOL.md: the label applies to the set of pages of this language version). The German set FAILS 3.2.3, decided by abfallkalender.html, whose main navigation is in a different order (designed failure). The navigation on this page itself has the common order.', scope='set', deciding_page='abfallkalender.html')

    # ------------------------------------------------------------------ zweisprachig.html
    main = '''<div class="container page-head">
  <h1>Amtliche Mitteilungen · <span lang="fr-CH">Avis officiels</span></h1>
  <p class="lead">Musterwil ist eine zweisprachige Gemeinde. Amtliche Mitteilungen des Gemeinderats erscheinen deshalb auf Deutsch und Französisch.</p>
</div>
<div class="container">
  <article class="bi-notice">
    <header class="bi-head">
      <p class="bi-date"><time datetime="2026-10-09">9. Oktober 2026</time></p>
      <h2>Gemeindeversammlung vom 24. November 2026 · <span lang="fr-CH">Assemblée communale du 24 novembre 2026</span></h2>
    </header>
    <div class="bi-grid">
      <div class="bi-col" lang="de-CH" data-testid="notice-col-de">
        <p class="bi-lang">Deutsch</p>
        <p>Die Stimmberechtigten werden zur ordentlichen Gemeindeversammlung eingeladen: Dienstag, 24. November 2026, 19.30 Uhr, Mehrzweckhalle.</p>
        <ol>
          <li>Budget 2027 und Festsetzung der Steueranlage</li>
          <li>Sanierung Schulhaus Moosmatt: Verpflichtungskredit von CHF 2,4 Mio.</li>
          <li>Teilrevision des Abfallreglements</li>
          <li>Verschiedenes</li>
        </ol>
        <p>Die Unterlagen liegen ab 23. Oktober 2026 bei der Gemeindeverwaltung auf.</p>
      </div>
      <div class="bi-col" lang="fr-CH" data-testid="notice-col-fr">
        <p class="bi-lang">Français</p>
        <p>Les ayants droit au vote sont convoqués à l’assemblée communale ordinaire : mardi 24 novembre 2026, à 19 h 30, à la salle polyvalente.</p>
        <ol>
          <li>Budget 2027 et fixation de la quotité d’impôt</li>
          <li>Assainissement de l’école de Moosmatt : crédit d’engagement de 2,4 millions de francs</li>
          <li>Révision partielle du règlement sur les déchets</li>
          <li>Divers</li>
        </ol>
        <p>Les documents peuvent être consultés à l’administration communale dès le 23 octobre 2026.</p>
      </div>
    </div>
  </article>

  <article class="bi-notice">
    <header class="bi-head">
      <p class="bi-date"><time datetime="2026-10-07">7. Oktober 2026</time></p>
      <h2>Budget 2027 verabschiedet · <span lang="fr-CH">Budget 2027 adopté</span></h2>
    </header>
    <div class="bi-grid">
      <div class="bi-col" lang="de-CH">
        <p class="bi-lang">Deutsch</p>
        <p data-testid="budget-de-para">Der Gemeinderat hat das Budget 2027 verabschiedet. Es rechnet bei einem Aufwand von 18,4 Millionen Franken mit einem Überschuss von 210 000 Franken; die Steueranlage bleibt unverändert. Le rapport détaillé peut être obtenu gratuitement auprès de l’administration communale. Über das Budget entscheidet die Gemeindeversammlung vom 24. November 2026.</p>
      </div>
      <div class="bi-col" lang="fr-CH">
        <p class="bi-lang">Français</p>
        <p>Le Conseil communal a adopté le budget 2027. Avec des charges de 18,4 millions de francs, il prévoit un excédent de 210 000 francs ; la quotité d’impôt reste inchangée. Le rapport détaillé peut être obtenu gratuitement auprès de l’administration communale. L’assemblée communale du 24 novembre 2026 se prononcera sur le budget.</p>
      </div>
    </div>
  </article>

  <article class="bi-notice">
    <header class="bi-head">
      <p class="bi-date"><time datetime="2026-10-02">2. Oktober 2026</time></p>
      <h2>Baupublikation · <span lang="fr-CH">Publication de construction</span></h2>
    </header>
    <div class="bi-grid">
      <div class="bi-col" lang="de-CH">
        <p class="bi-lang">Deutsch</p>
        <p data-testid="building-de-para">Bauherrschaft: Lea und Marco Beispiel, Rue du Marché 4, 9999 Musterwil. Bauvorhaben: Ersatz der Ölheizung durch eine Luft-Wasser-Wärmepumpe auf Parzelle Nr. 512. Einsprachen sind bis am 9. November 2026 schriftlich und begründet an den Gemeinderat zu richten.</p>
      </div>
      <div class="bi-col" lang="fr-CH">
        <p class="bi-lang">Français</p>
        <p>Maîtres d’ouvrage : Lea et Marco Beispiel, Rue du Marché 4, 9999 Musterwil. Projet : remplacement du chauffage à mazout par une pompe à chaleur air-eau sur la parcelle n° 512. Les oppositions dûment motivées doivent être adressées par écrit au Conseil communal jusqu’au 9 novembre 2026.</p>
      </div>
    </div>
  </article>
</div>'''
    out['zweisprachig.html'] = page(L, 'bilingual', 'Amtliche Mitteilungen – Gemeinde Musterwil', main, crumbs=['Amtliche Mitteilungen'],
                                    description='Zweisprachige amtliche Mitteilungen des Gemeinderats Musterwil.')
    P = 'zweisprachig.html'
    R(P, 'notice-col-fr', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2 / H58: the French column is marked lang="fr-CH".')
    R(P, 'notice-col-de', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: the German column is marked lang="de-CH" (same as the page).')
    R(P, 'budget-de-para', '3.1.2', 'issue', 'failed', 'Understanding 3.1.2: the French sentence "Le rapport détaillé peut être obtenu …" sits inside a German paragraph without lang="fr".')
    R(P, 'building-de-para', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: "Rue du Marché 4" is an address (proper name); no lang change needed.')

    # ------------------------------------------------------------------ freizeit.html
    main = f'''<div class="container page-head">
  <h1>Freizeit &amp; Tourismus</h1>
  <p class="lead">Seeufer, Aarenwald und ein lebendiges Dorfleben: Entdecken Sie Musterwil zu jeder Jahreszeit.</p>
</div>
<div class="container">
  <div class="carousel" role="region" aria-label="Impressionen aus Musterwil" data-carousel data-interval="5000" data-testid="carousel">
    <div class="carousel-track">
      <figure class="slide is-active"><img src="{A}img/slide-seeufer.svg" alt="Bootssteg und Segelboot auf dem See im Abendlicht" width="1200" height="500"><figcaption>Seeufer: Badeplatz, Bootssteg und Seepromenade</figcaption></figure>
      <figure class="slide"><img src="{A}img/slide-wald.svg" alt="Waldweg mit Infotafel im herbstlichen Aarenwald" width="1200" height="500"><figcaption>Waldlehrpfad im Aarenwald – 4,5 km, ideal für Familien</figcaption></figure>
      <figure class="slide"><img src="{A}img/slide-dorfplatz.svg" alt="Dorfplatz mit Brunnen und Marktständen" width="1200" height="500"><figcaption>Musterwiler Märit auf dem Dorfplatz – nächster Termin: 24. Oktober</figcaption></figure>
      <figure class="slide"><img src="{A}img/slide-schiff.svg" alt="Kursschiff auf dem See vor bewaldeten Hügeln" width="1200" height="500"><figcaption>Seerundfahrt: täglich von April bis Oktober</figcaption></figure>
    </div>
    <span class="carousel-ctrl carousel-prev" data-carousel-prev data-testid="carousel-prev">{icon("left")}</span>
    <span class="carousel-ctrl carousel-next" data-carousel-next data-testid="carousel-next">{icon("right")}</span>
    <div class="carousel-dots" aria-hidden="true"><span class="carousel-dot is-active"></span><span class="carousel-dot"></span><span class="carousel-dot"></span><span class="carousel-dot"></span></div>
  </div>
  <img src="{A}img/divider-waves.svg" alt="" class="divider" width="1200" height="24" data-testid="section-divider">

  <section class="section" aria-labelledby="offers-title">
    <h2 id="offers-title">Angebote in Musterwil</h2>
    <div class="filter-bar">
      <label for="offer-filter">Angebote filtern</label>
      <select id="offer-filter" data-filter-target="offer-list" data-filter-status="offer-count" data-testid="activity-filter">
        <option value="all">Alle Angebote</option>
        <option value="sport">Sport und Baden</option>
        <option value="kultur">Kultur</option>
        <option value="natur">Natur</option>
        <option value="kurse">Kurse</option>
      </select>
      <p id="offer-count" class="filter-count" role="status" data-template="{{n}} Angebote angezeigt"></p>
    </div>
    <ul class="offer-grid" id="offer-list">
      <li data-category="sport"><p class="offer-tag">Sport und Baden</p><h3>Strandbad Seeufer</h3><p>Liegewiese, Sprungturm und Kinderbecken. Geöffnet von Mitte Mai bis Mitte September, bei schönem Wetter 9 bis 20 Uhr.</p></li>
      <li data-category="sport"><p class="offer-tag">Sport und Baden</p><h3>Vita-Parcours Aarenwald</h3><p>2,8 km mit 15 Posten. Start beim Parkplatz Waldhaus.</p></li>
      <li data-category="kultur" data-testid="activity-openair"><p class="offer-tag">Kultur</p><h3>Open Air Kino am See</h3><p>Jeden Freitag im Juli und August zeigt der Kulturverein einen Film unter freiem Himmel. Eintritt frei, Kollekte.</p></li>
      <li data-category="kultur"><p class="offer-tag">Kultur</p><h3>Dorfmuseum im Spycher</h3><p>Handwerk und Dorfgeschichte, geöffnet am ersten Sonntag im Monat von 14 bis 17 Uhr.</p></li>
      <li data-category="natur"><p class="offer-tag">Natur</p><h3>Waldlehrpfad</h3><p>4,5 km mit 20 Infotafeln zu Bäumen, Tieren und Pilzen. Kinderwagentauglich.</p></li>
      <li data-category="kurse" data-testid="activity-workshop"><p class="offer-tag">Kurse</p><h3>Workshop Velo-Reparatur</h3><p>Das Werkhof-Team gibt sein Know-how weiter: Schlauch flicken, Bremsen einstellen, Kette ölen. Samstag, 7. November 2026, 9 bis 12 Uhr.</p></li>
    </ul>
  </section>

  <section class="section" aria-labelledby="tip-title">
    <h2 id="tip-title">Ausflugstipp</h2>
    <div class="tip-grid">
      <figure class="overlay-figure">
        <img src="{A}img/tip-aussichtsturm.svg" alt="Hölzerner Aussichtsturm über den Baumwipfeln des Aarenwalds" width="800" height="450" data-testid="tip-image">
        <figcaption class="overlay-caption" data-testid="tip-caption">Aussichtsturm Hohwacht, 28 Meter hoch</figcaption>
      </figure>
      <div>
        <p>Vom Dorfplatz erreichen Sie den Aussichtsturm Hohwacht in rund 40 Minuten zu Fuss. Bei klarer Sicht reicht der Blick bis zu den Alpen.</p>
        <p data-testid="boat-tour-para">Zurück geht es bequem mit dem Kursschiff: Das Billett für die Seerundfahrt erhalten Sie am Kiosk beim Steg, wo es im Sommer auch Glace und kühle Getränke gibt.</p>
        <p data-testid="guided-tours-para">Dorfführungen für Gruppen organisieren wir auch ad hoc – melden Sie sich einfach bei der Gemeindeverwaltung.</p>
      </div>
    </div>
  </section>
</div>'''
    out['freizeit.html'] = page(L, 'leisure', 'Freizeit &amp; Tourismus – Gemeinde Musterwil', main, crumbs=['Freizeit &amp; Tourismus'],
                                scripts=('carousel.js', 'filter.js'), description='Freizeitangebote, Ausflugstipps und Kultur in Musterwil.')
    P = 'freizeit.html'
    R(P, 'carousel', '2.2.2', 'issue', 'failed', 'Understanding 2.2.2: the carousel starts automatically, advances every 5 s indefinitely and has no pause, stop or hide control.')
    R(P, 'carousel-prev', '4.1.2', 'issue', 'failed', 'Understanding 4.1.2: "previous" control is a <span> with an icon and a click handler: no role, no accessible name, not focusable.')
    R(P, 'carousel-next', '4.1.2', 'issue', 'failed', 'Understanding 4.1.2: "next" control is a <span> with an icon and a click handler: no role, no accessible name, not focusable.')
    R(P, 'activity-filter', '3.2.2', 'trap', 'passed', 'Understanding 3.2.2: changing the select only filters the list below on the same page; no change of context.')
    R(P, 'tip-caption', '1.4.3', 'trap', 'passed', 'Understanding 1.4.3: white caption on an 80 % opaque dark overlay (≥ 12:1).')
    R(P, 'tip-image', '1.1.1', 'trap', 'passed', 'Understanding 1.1.1: meaningful short alt for the photo.')
    R(P, 'section-divider', '1.1.1', 'trap', 'passed', 'Understanding 1.1.1 / H67: purely decorative wave divider with alt="" is correctly ignored by assistive technology.')
    R(P, 'activity-openair', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: "Open Air" is an established loanword in Swiss German.')
    R(P, 'activity-workshop', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: "Workshop" and "Know-how" are loanwords that have become part of German.')
    R(P, 'boat-tour-para', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: "Billett" and "Glace" are helvetisms of Swiss Standard German.')
    R(P, 'guided-tours-para', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: Latin "ad hoc" is part of the German vernacular.')
    R(P, None, '2.4.5', 'set', 'failed', 'Set-level criterion (PROTOCOL.md: the label applies to the set of pages of this language version). The German set FAILS 2.4.5, decided by velo-aktion.html, which is reachable only through one home-page teaser (designed failure). freizeit.html itself is reachable via main navigation, sitemap and search.', scope='set', deciding_page='velo-aktion.html')

    # ------------------------------------------------------------------ anleitung.html
    main = f'''<div class="container page-head">
  <h1>Anleitung: Umzug online melden</h1>
  <p class="lead">Mit eUmzug melden Sie Ihren Umzug innerhalb der Schweiz bequem online – bei der bisherigen und der neuen Gemeinde gleichzeitig.</p>
</div>
<div class="container guide-layout">
  <ol class="steps">
    <li><h2>Formular öffnen</h2><p>Öffnen Sie den Online-Schalter und wählen Sie «Umzug melden». Halten Sie Ihre neue Adresse und das Umzugsdatum bereit.</p></li>
    <li><h2>Personalien erfassen</h2><p data-testid="instruction-table-ref">Geben Sie Name, Geburtsdatum und Ihre bisherige Adresse ein. Welche Unterlagen Sie zusätzlich brauchen, sehen Sie in der Tabelle unten.</p></li>
    <li><h2>Weiter zur neuen Adresse</h2><p data-testid="instruction-next-button">Klicken Sie unten rechts auf «Weiter».</p></li>
    <li><h2>Angaben bestätigen</h2><p data-testid="instruction-green-button">Prüfen Sie Ihre neue Adresse. Wenn alles stimmt, klicken Sie auf den grünen Knopf rechts.</p></li>
    <li><h2>Bestätigung erhalten</h2><p>Sie erhalten sofort eine Bestätigung per E-Mail. Die Gemeinde meldet sich, falls noch Unterlagen fehlen.</p></li>
  </ol>
  <aside class="mock-wrap" aria-labelledby="mock-title">
    <h2 id="mock-title" class="mock-heading">Übungsansicht</h2>
    <p class="mock-intro">So sieht eUmzug aus. Probieren Sie die Schaltflächen ruhig aus – es werden keine Daten übermittelt.</p>
    <div class="mock-window">
      <div class="mock-bar"><span></span><span></span><span></span><p>eUmzug – Schritt 2 von 4</p></div>
      <div class="mock-body">
        <p class="mock-label">Name</p><p class="mock-value">Lukas Muster</p>
        <p class="mock-label">Bisherige Adresse</p><p class="mock-value">Lindenweg 3, 9998 Beispielhausen</p>
        <div class="mock-actions"><button type="button" class="btn" data-practice="practice-status" data-practice-msg="Übung: Sie sind jetzt bei Schritt 3." data-testid="practice-next-button">Weiter</button></div>
      </div>
    </div>
    <div class="mock-window">
      <div class="mock-bar"><span></span><span></span><span></span><p>eUmzug – Schritt 3 von 4</p></div>
      <div class="mock-body mock-confirm">
        <div>
          <p class="mock-label">Neue Adresse</p><p class="mock-value">Seeweg 7, 9999 Musterwil</p>
          <p class="mock-label">Einzugsdatum</p><p class="mock-value">1. Dezember 2026</p>
        </div>
        <button type="button" class="round-go" aria-label="Fortfahren" data-practice="practice-status" data-practice-msg="Übung: Ihre Angaben wären jetzt bestätigt." data-testid="practice-confirm-button">{icon("arrow")}</button>
      </div>
    </div>
    <p id="practice-status" class="practice-status" role="status"></p>
  </aside>
</div>
<div class="container section">
  <div class="table-wrap">
    <table class="data-table" data-testid="documents-table">
      <caption>Benötigte Unterlagen</caption>
      <thead><tr><th scope="col">Ihre Situation</th><th scope="col">Unterlagen</th></tr></thead>
      <tbody>
        <tr><th scope="row">Schweizer Staatsangehörige</th><td>Heimatschein (nur bei Zuzug aus einer anderen Gemeinde)</td></tr>
        <tr><th scope="row">Ausländische Staatsangehörige</th><td>Ausländerausweis sowie gültiger Pass oder Identitätskarte</td></tr>
        <tr><th scope="row">Familien</th><td>Familienausweis oder Familienbüchlein</td></tr>
        <tr><th scope="row">Mieterinnen und Mieter</th><td>Mietvertrag mit Angabe der Wohnungsnummer</td></tr>
      </tbody>
    </table>
  </div>
</div>'''
    out['anleitung.html'] = page(L, 'guide', 'Anleitung eUmzug – Gemeinde Musterwil', main, crumbs=['Anleitung eUmzug'],
                                 description='Schritt-für-Schritt-Anleitung: Umzug online melden mit eUmzug.')
    P = 'anleitung.html'
    R(P, 'instruction-green-button', '1.3.3', 'issue', 'failed', 'Understanding 1.3.3 / F14, F26: "klicken Sie auf den grünen Knopf rechts" relies only on colour and position; the button shows only an arrow and its name ("Fortfahren") is not mentioned.')
    R(P, 'instruction-next-button', '1.3.3', 'trap', 'passed', 'Understanding 1.3.3: position ("unten rechts") is combined with the visible button text «Weiter», so the instruction does not rely on sensory characteristics alone.')
    R(P, 'instruction-table-ref', '1.3.3', 'trap', 'passed', 'Understanding 1.3.3: "in der Tabelle unten" refers to a table that also has the caption "Benötigte Unterlagen" and is the only table on the page.')
    R(P, 'documents-table', '1.3.1', 'trap', 'passed', 'Understanding 1.3.1: data table with caption and th scope="col"/"row".')
    R(P, 'practice-confirm-button', '2.5.3', 'trap', 'inapplicable', 'Understanding 2.5.3: icon-only button with aria-label and no visible text label; label-in-name does not apply.')
    R(P, 'practice-next-button', '4.1.2', 'trap', 'passed', 'Understanding 4.1.2: native <button> "Weiter" exposes name and role.')

    # ------------------------------------------------------------------ sitemap.html
    main = '''<div class="container page-head">
  <h1>Sitemap</h1>
  <p class="lead">Alle Seiten der Website von Musterwil auf einen Blick.</p>
</div>
<div class="container sitemap-grid">
  <section aria-labelledby="sm-admin"><h2 id="sm-admin">Verwaltung</h2>
    <ul><li><a href="index.html">Startseite</a></li><li><a href="online-schalter.html">Online-Schalter</a></li><li><a href="oeffnungszeiten.html">Öffnungszeiten</a></li><li><a href="zweisprachig.html">Amtliche Mitteilungen</a></li></ul></section>
  <section aria-labelledby="sm-living"><h2 id="sm-living">Wohnen und Umwelt</h2>
    <ul><li><a href="anleitung.html">Anleitung eUmzug</a></li><li><a href="abfallkalender.html">Abfallkalender 2026</a></li></ul></section>
  <section aria-labelledby="sm-leisure"><h2 id="sm-leisure">Freizeit</h2>
    <ul><li><a href="freizeit.html">Freizeit &amp; Tourismus</a></li></ul></section>
  <section aria-labelledby="sm-service"><h2 id="sm-service">Service</h2>
    <ul><li><a href="suche.html">Suche</a></li><li><a href="sitemap.html">Sitemap</a></li><li><a href="barrierefreiheit.html">Erklärung zur Barrierefreiheit</a></li></ul></section>
  <section aria-labelledby="sm-lang"><h2 id="sm-lang">Weitere Sprachen</h2>
    <ul><li><a href="fr/plan-du-site.html" lang="fr-CH" hreflang="fr">Plan du site en français</a></li><li><a href="it/mappa-del-sito.html" lang="it-CH" hreflang="it">Mappa del sito in italiano</a></li></ul></section>
</div>'''
    out['sitemap.html'] = page(L, 'sitemap', 'Sitemap – Gemeinde Musterwil', main, crumbs=['Sitemap'], search_variant='find')
    P = 'sitemap.html'
    R(P, 'header-search-button', '3.2.4', 'issue', 'failed', 'Set-level criterion (PROTOCOL.md: the label applies to the set of pages of this language version). Designed set-level failure; this page decides it: the site search button is labelled „Finden“ with an arrow icon here, but „Suche“ with a magnifier on every other German page; same function, different identification (Understanding 3.2.4).', scope='set', deciding_page='sitemap.html')

    # ------------------------------------------------------------------ suche.html
    entries = [
        dict(title='Startseite', url='index.html', text='Aktuelles, Veranstaltungen und Mitteilungen der Gemeinde Musterwil.', keywords='home news aktuelles'),
        dict(title='Online-Schalter', url='online-schalter.html', text='Wohnsitzbestätigung bestellen und Adressänderung melden.', keywords='formular bestellen wohnsitz bestätigung adresse'),
        dict(title='Anleitung eUmzug', url='anleitung.html', text='Umzug online melden: Schritt-für-Schritt-Anleitung und benötigte Unterlagen.', keywords='umzug zuzug wegzug adresse eumzug'),
        dict(title='Öffnungszeiten', url='oeffnungszeiten.html', text='Öffnungszeiten der Gemeindeverwaltung, des Werkhofs und der Bibliothek; Standort und Anreise.', keywords='schalter bibliothek werkhof telefon'),
        dict(title='Abfallkalender 2026', url='abfallkalender.html', text='Abfuhrtermine für Kehricht, Grüngut, Papier und Karton, Sammelstellen und Gebühren.', keywords='abfall entsorgung grüngut kehricht papier karton'),
        dict(title='Freizeit & Tourismus', url='freizeit.html', text='Strandbad, Waldlehrpfad, Aussichtsturm, Kultur und Kurse in Musterwil.', keywords='tourismus ausflug baden kultur'),
        dict(title='Amtliche Mitteilungen', url='zweisprachig.html', text='Zweisprachige Mitteilungen des Gemeinderats: Gemeindeversammlung, Budget 2027, Baupublikationen.', keywords='gemeinderat budget baugesuch versammlung'),
        dict(title='Sitemap', url='sitemap.html', text='Alle Seiten der Website im Überblick.', keywords='übersicht seiten'),
        dict(title='Erklärung zur Barrierefreiheit', url='barrierefreiheit.html', text='Stand der Barrierefreiheit dieser Website und Feedback-Formular.', keywords='barrierefreiheit accessibility feedback'),
    ]
    main = f'''<div class="container page-head">
  <h1>Suche</h1>
</div>
<div class="container narrow">
  <form class="search-page" role="search" action="suche.html" method="get" data-search-form>
    <label for="search-q">Suchbegriff</label>
    <div class="search-field"><input id="search-q" name="q" type="search" autocomplete="off"><button type="submit" class="search-go" aria-label="Suche" data-testid="search-page-button">{icon("search")}</button></div>
  </form>
  <p class="search-status" role="status" data-search-status data-msg-empty="Geben Sie einen Suchbegriff ein, zum Beispiel «Abfall» oder «Umzug»." data-msg-count="{{n}} Treffer für «{{q}}»" data-msg-none="Keine Treffer für «{{q}}». Versuchen Sie einen anderen Begriff oder nutzen Sie die Sitemap."></p>
  <ol class="search-results" data-search-results></ol>
  <section class="box" aria-labelledby="popular">
    <h2 id="popular">Häufig gesucht</h2>
    <ul class="chip-list"><li><a href="suche.html?q=Abfall">Abfall</a></li><li><a href="suche.html?q=Umzug">Umzug</a></li><li><a href="suche.html?q=Bibliothek">Bibliothek</a></li><li><a href="suche.html?q=Budget">Budget</a></li></ul>
  </section>
</div>
{search_index(entries)}'''
    out['suche.html'] = page(L, 'search', 'Suche – Gemeinde Musterwil', main, crumbs=['Suche'], scripts=('search.js',))
    P = 'suche.html'
    R(P, 'search-page-button', '1.4.11', 'issue', 'failed', 'Understanding 1.4.11: the icon-only search button draws its magnifier in #c9cdd2 on white (about 1.6:1 < 3:1).')
    R(P, 'search-page-button', '2.5.3', 'trap', 'inapplicable', 'Understanding 2.5.3: icon-only button (aria-label "Suche") has no visible text label, so label-in-name does not apply.')
    R(P, 'header-search-button', '3.2.4', 'set', 'failed', 'Set-level criterion (PROTOCOL.md: the label applies to the set of pages of this language version). The German set FAILS 3.2.4, decided by sitemap.html, where the search button is identified as „Finden“ with an arrow instead of „Suche“ with a magnifier (designed failure). On this page the header search is labelled „Suche“ with the magnifier, as on the other pages.', scope='set', deciding_page='sitemap.html')

    # ------------------------------------------------------------------ barrierefreiheit.html
    main = '''<div class="container page-head">
  <h1>Erklärung zur Barrierefreiheit</h1>
</div>
<div class="container with-sidebar">
  <div class="content">
    <p>Die Gemeinde Musterwil ist bestrebt, ihre Website musterwil.example gemäss den Web Content Accessibility Guidelines (WCAG) 2.1, Konformitätsstufe AA, und dem Standard eCH-0059 barrierefrei zugänglich zu machen.</p>
    <h2>Stand der Vereinbarkeit</h2>
    <p>Diese Website ist <strong>teilweise konform</strong> mit WCAG 2.1, Konformitätsstufe AA. Die unten aufgeführten Inhalte sind noch nicht barrierefrei.</p>
    <h2>Nicht barrierefreie Inhalte</h2>
    <ul>
      <li>Einige ältere PDF-Dokumente im Archiv (vor 2022) sind nicht vollständig zugänglich.</li>
      <li>Bei einzelnen Bildern in älteren Beiträgen fehlen aussagekräftige Alternativtexte.</li>
      <li>Die Aufzeichnungen der Gemeindeversammlung haben noch keine Untertitel.</li>
    </ul>
    <p>Wir arbeiten laufend daran, diese Mängel zu beheben.</p>
    <h2>Erstellung dieser Erklärung</h2>
    <p>Diese Erklärung wurde am 3. März 2025 erstellt. Sie beruht auf einer Selbstbewertung durch die Gemeindeverwaltung.</p>
    <h2>Feedback</h2>
    <p>Sind Ihnen Mängel beim barrierefreien Zugang aufgefallen? Teilen Sie uns diese bitte über das folgende Formular mit.</p>
    <form class="form-card form-std" action="barrierefreiheit.html" method="get">
      <div class="form-grid">
        <div class="field"><label for="fb-name">Ihr Name</label><input id="fb-name" type="text" autocomplete="name"></div>
        <div class="field"><label for="fb-email">Ihre E-Mail-Adresse</label><input id="fb-email" type="email" autocomplete="email"></div>
        <div class="field field-full"><label for="fb-page">Betroffene Seite</label><input id="fb-page" type="text" placeholder="z. B. Online-Schalter"></div>
        <div class="field field-full"><label for="fb-msg">Ihre Rückmeldung</label><textarea id="fb-msg" rows="5"></textarea></div>
      </div>
      <div class="form-actions"><div class="btn" onclick="sendFeedback(this)" data-testid="feedback-submit">Absenden</div></div>
      <p class="feedback-status" role="status" data-feedback-status data-msg="Vielen Dank für Ihre Rückmeldung. Wir antworten innert zehn Arbeitstagen." hidden></p>
    </form>
  </div>
  <nav class="side" aria-labelledby="related-title" data-testid="related-sidebar">
    <h2 id="related-title" class="side-title">Verwandte Seiten</h2>
    <ul><li><a href="sitemap.html">Sitemap</a></li><li><a href="suche.html">Suche</a></li><li><a href="online-schalter.html">Online-Schalter</a></li><li><a href="oeffnungszeiten.html">Öffnungszeiten</a></li></ul>
  </nav>
</div>'''
    out['barrierefreiheit.html'] = page(L, 'a11y', 'Erklärung zur Barrierefreiheit – Gemeinde Musterwil', main, crumbs=['Barrierefreiheit'])
    P = 'barrierefreiheit.html'
    R(P, 'feedback-submit', '4.1.2', 'issue', 'failed', 'Understanding 4.1.2: the feedback "Absenden" control is a <div class="btn" onclick>: no button role, not focusable, so keyboard and screen-reader users cannot send feedback.')
    R(P, 'related-sidebar', '1.3.2', 'trap', 'passed', 'Understanding 1.3.2: the related-links sidebar is shown on the left but comes after the content in the DOM; its position does not affect meaning.')

    # ------------------------------------------------------------------ velo-aktion.html (orphan)
    main = f'''<div class="container page-head">
  <h1>Velo-Aktion: Gratis-Service für Schulvelos</h1>
  <p class="lead">Sicher durch den Winter: Am Samstag, 31. Oktober 2026, prüfen wir Velos und Trottinetts von Schulkindern kostenlos.</p>
</div>
<div class="container layout-main-aside">
  <div class="main-col">
    <img class="rounded-img" src="{A}img/news-velo.svg" alt="Zwei Kinder mit Velohelm und ihren Velos vor dem Schulhaus" width="640" height="360">
    <h2>Was wir prüfen</h2>
    <ul><li>Bremsen vorne und hinten</li><li>Licht und Reflektoren</li><li>Reifen, Kette und Klingel</li></ul>
    <p>Kleine Reparaturen erledigt das Team des Werkhofs zusammen mit dem Veloclub Musterwil direkt vor Ort. Ersatzteile verrechnen wir zum Selbstkostenpreis.</p>
    <h2>Wann und wo?</h2>
    <p>Samstag, 31. Oktober 2026, 9 bis 13 Uhr, Werkhof Moosmatt, Industriestrasse 8. Eine Anmeldung ist nicht nötig.</p>
  </div>
  <div class="aside-col">
    <section class="box" aria-labelledby="velo-contact"><h2 id="velo-contact">Kontakt</h2><p>Werkhof Musterwil<br>Telefon <a href="tel:+41320001240">032 000 12 40</a></p></section>
  </div>
</div>'''
    out['velo-aktion.html'] = page(L, 'velo', 'Velo-Aktion – Gemeinde Musterwil', main, crumbs=['Velo-Aktion'])
    R('velo-aktion.html', None, '2.4.5', 'issue', 'failed', 'Set-level criterion (PROTOCOL.md: the label applies to the set of pages of this language version). Designed set-level failure; this page decides it: it is reachable only through one teaser link on the home page; it is not in the navigation, the sitemap or the search index, and it is not a step in a process (Understanding 2.4.5).', scope='set', deciding_page='velo-aktion.html')

    return out
