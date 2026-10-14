"""Italian pages (it/)."""
from chrome import page, icon
from common import calendar, search_index, hours_grid

A = '../assets/'
L = 'it'


def build(R):
    out = {}

    # ------------------------------------------------------------------ it/index.html
    main = f'''<section class="hero" aria-labelledby="hero-title">
  <div class="container">
    <div class="hero-text" data-testid="hero-text">
      <h1 id="hero-title">Benvenuti a Musterwil</h1>
      <p>Un comune vivace tra il bosco dell’Aarenwald e la riva del lago – e online per voi, giorno e notte.</p>
    </div>
    <p class="hero-actions"><a class="btn btn-light" href="sportello-online.html">Allo sportello online</a> <a class="btn" href="calendario-rifiuti.html">Calendario dei rifiuti 2026</a></p>
  </div>
</section>

<nav class="quicklinks container" aria-label="Accesso rapido">
  <ul>
    <li><a href="sportello-online.html"><span class="ql-icon">{icon("monitor")}</span><span class="ql-text"><strong>Sportello online</strong><small>Attestato di domicilio e altro</small></span></a></li>
    <li><a href="istruzioni.html"><span class="ql-icon">{icon("box")}</span><span class="ql-text"><strong>Notificare un trasloco</strong><small>eTrasloco in cinque passi</small></span></a></li>
    <li><a href="calendario-rifiuti.html"><span class="ql-icon">{icon("calendar")}</span><span class="ql-text"><strong>Calendario dei rifiuti</strong><small>Date e punti di raccolta</small></span></a></li>
    <li><a href="orari.html"><span class="ql-icon">{icon("clock")}</span><span class="ql-text"><strong>Orari</strong><small>Amministrazione, magazzino, biblioteca</small></span></a></li>
  </ul>
</nav>

<section class="section container" aria-labelledby="news-title">
  <div class="section-head"><h2 id="news-title">Attualità</h2></div>
  <div class="grid-4">
    <article class="card">
      <img src="{A}img/news-gemeindehaus.svg" alt="Casa comunale di Musterwil con la torre dell’orologio" width="640" height="360" data-testid="news-card-1-img">
      <div class="card-body">
        <p class="card-date"><time datetime="2026-10-12">12 ottobre 2026</time></p>
        <h3>Nuovi orari degli sportelli dal 1° novembre</h3>
        <p>L’amministrazione comunale sarà aperta il giovedì sera fino alle 18.30. In compenso, lo sportello resterà chiuso il mercoledì pomeriggio.</p>
        <p class="card-more"><a href="orari.html" data-testid="news-card-1-more">Scopri di più</a></p>
      </div>
    </article>
    <article class="card">
      <img src="{A}img/news-recycling.svg" alt="Contenitori colorati per la raccolta differenziata" width="640" height="360" data-testid="news-card-2-img">
      <div class="card-body">
        <p class="card-date"><time datetime="2026-10-08">8 ottobre 2026</time></p>
        <h3>Scarti vegetali: ritmo invernale</h3>
        <p>Da novembre gli scarti vegetali saranno raccolti solo ogni due settimane. Vi preghiamo di tenere conto delle nuove date.</p>
        <p class="card-more"><a href="calendario-rifiuti.html" data-testid="news-card-2-more">Scopri di più</a></p>
      </div>
    </article>
    <article class="card">
      <img src="{A}img/news-maerit.svg" alt="foto3_def.png" width="640" height="360" data-testid="news-card-3-img">
      <div class="card-body">
        <p class="card-date"><time datetime="2026-10-05">5 ottobre 2026</time></p>
        <h3>Mercato d’autunno il 24 ottobre</h3>
        <p>Oltre 40 bancarelle con prodotti regionali, artigianato e zuppa di zucca, con la musica della banda del paese.</p>
        <p class="card-more"><a href="tempo-libero.html" data-testid="news-card-3-more">Scopri di più</a></p>
      </div>
    </article>
    <article class="card">
      <img src="{A}img/news-laternen.svg" alt="Bambini con lanterne accese nel buio" width="640" height="360" data-testid="news-card-4-img">
      <div class="card-body">
        <p class="card-date"><time datetime="2026-10-01">1° ottobre 2026</time></p>
        <h3>Corteo delle lanterne l’11 novembre</h3>
        <p>I bambini della scuola dell’infanzia sfilano per il paese con le loro lanterne di rapa. Partenza alle 18 davanti alla scuola Moosmatt.</p>
        <p class="card-more"><a href="tempo-libero.html" data-testid="news-card-4-more">Scopri di più</a></p>
      </div>
    </article>
  </div>

  <div class="teaser-strip">
    <span class="strip-icon">{icon("users")}</span>
    <div>
      <p>Nella seduta del 6 ottobre 2026 il Municipio ha approvato il preventivo 2027 e ha iscritto il risanamento della scuola Moosmatt all’ordine del giorno dell’assemblea comunale del 24 novembre.</p>
      <p><a href="bilingue.html" data-testid="council-readmore">Continua a leggere</a></p>
    </div>
  </div>
</section>

<div class="container layout-main-aside section">
  <div class="main-col">
    <section aria-labelledby="admin-title">
      <h2 id="admin-title">La vostra amministrazione comunale</h2>
      <p data-testid="intro-para">Carta d’identità, attestato di domicilio o marca per cani: l’amministrazione comunale è il vostro primo punto di riferimento. Molti servizi sono disponibili giorno e notte allo sportello online; i nuovi <a href="orari.html" class="link-plain" data-testid="intro-inline-link">orari d’apertura</a> degli sportelli valgono dal 1° novembre 2026.</p>
    </section>
    <aside class="notice" aria-labelledby="notice-title" data-testid="notice-box">
      <p class="notice-label">{icon("megaphone")}Comunicazione</p>
      <h2 id="notice-title">Comunicazione della Conferenza regionale Aarenwald</h2>
      <p>La Conferenza regionale Aarenwald svolge una consultazione sulla rete ciclabile regionale. La comunicazione è pubblicata nella lingua originale:</p>
      <p data-testid="notice-fr-para">Les communes de la région sont invitées à se prononcer sur le projet de réseau cyclable régional jusqu’au 30 novembre 2026. Le dossier peut être consulté à l’administration communale pendant les heures d’ouverture. Une séance d’information publique aura lieu le 5 novembre 2026 à 19 h 30 à la salle polyvalente de Musterwil.</p>
    </aside>
  </div>
  <div class="aside-col">
    <section class="box" aria-labelledby="tips-title">
      <h2 id="tips-title">Buono a sapersi</h2>
      <p data-testid="tips-sentence">Tutte le date di raccolta degli scarti vegetali sono indicate nel calendario dei rifiuti – <a href="calendario-rifiuti.html" data-testid="tips-sentence-more">di più</a>.</p>
      <ul class="tick-list">
        <li>La biblioteca comunale ha nuovi orari dal 2 novembre – <a href="orari.html#biblioteca" data-testid="tips-list-more">di più</a></li>
        <li>Notificare online un trasloco in tutta la Svizzera – <a href="istruzioni.html" data-testid="tips-list-more-2">di più</a></li>
      </ul>
      <div class="mini-promo">
        <h3>Calendario dei rifiuti 2026</h3>
        <p>Tutte le date di raccolta di rifiuti domestici, scarti vegetali, carta e cartone in un colpo d’occhio.</p>
        <p><a class="btn btn-small" href="calendario-rifiuti.html" aria-label="Di più sul calendario dei rifiuti 2026" data-testid="tips-aria-more">Di più</a></p>
      </div>
    </section>
    <section class="box" aria-labelledby="contact-title">
      <h2 id="contact-title">Contatto</h2>
      <div class="contact-row">
        <div>
          <p>Amministrazione comunale di Musterwil<br>Dorfstrasse 1, 9999 Musterwil</p>
          <p>Telefono <a href="tel:+41320001234">032 000 12 34</a><br><a href="mailto:gemeinde@musterwil.example">gemeinde@musterwil.example</a></p>
        </div>
        <a class="icon-link" href="orari.html#ubicazione" data-testid="contact-map-link"><img src="{A}img/icon-map-pin.svg" alt="" width="24" height="24"></a>
      </div>
    </section>
  </div>
</div>

<section class="section-alt" aria-labelledby="events-title">
  <div class="container">
    <h2 id="events-title">Manifestazioni</h2>
    <div class="events-layout">
      <ul class="event-list">
        <li class="event" data-testid="event-maerit">
          <p class="date-tile"><time datetime="2026-10-24"><span class="d">24</span><span class="m">ott</span></time></p>
          <div><h3>Musterwiler Märit in piazza</h3><p>Sabato, dalle 9 alle 16. Il tradizionale Musterwiler Märit propone prodotti regionali e artigianato; alle 11 il Municipio offre l’aperitivo.</p></div>
        </li>
        <li class="event">
          <p class="date-tile"><time datetime="2026-11-11"><span class="d">11</span><span class="m">nov</span></time></p>
          <div><h3>Corteo delle lanterne</h3><p>Mercoledì alle 18, partenza dalla scuola Moosmatt. Segue un punch caldo offerto dall’associazione genitori.</p></div>
        </li>
        <li class="event">
          <p class="date-tile"><time datetime="2026-11-24"><span class="d">24</span><span class="m">nov</span></time></p>
          <div><h3>Assemblea comunale</h3><p>Martedì alle 19.30, sala multiuso. All’ordine del giorno: preventivo 2027 e risanamento della scuola Moosmatt.</p></div>
        </li>
        <li class="event">
          <p class="date-tile"><time datetime="2026-12-05"><span class="d">5</span><span class="m">dic</span></time></p>
          <div><h3>Corso di computer per principianti</h3>
            <p data-testid="event-computer-text">Biblioteca comunale, Bahnhofstrasse 12. Durante il weekend i nostri volontari condividono il loro know-how: e-mail, foto e videochiamate al computer, con calma e senza fretta.</p>
            <p class="event-note" data-testid="event-registration-note">Posti limitati. Please register before 30 November.</p></div>
        </li>
      </ul>
      <figure class="banner-figure">
        <img src="{A}img/banner-versammlung-it.svg" alt="Assemblea comunale, 24 novembre 2026, ore 19.30, sala multiuso" width="640" height="800" data-testid="assembly-banner">
      </figure>
    </div>
  </div>
</section>

<section class="section container" aria-labelledby="stats-title">
  <h2 id="stats-title">Musterwil in cifre</h2>
  <dl class="stats">
    <div><dt>Abitanti</dt><dd>3842</dd></div>
    <div><dt>Superficie</dt><dd>12,6 km²</dd></div>
    <div><dt>Altitudine</dt><dd>431 m</dd></div>
    <div><dt>Società locali</dt><dd>41</dd></div>
  </dl>
  <p class="source">Fonte: Ufficio federale di statistica (UST), stato al 31 dicembre 2025.</p>
</section>'''
    out['index.html'] = page(L, 'home', 'Comune di Musterwil', main,
                             description='Sito ufficiale del Comune di Musterwil: attualità, sportello online, calendario dei rifiuti e manifestazioni.')
    P = 'it/index.html'
    for i, title in enumerate(['Nuovi orari degli sportelli', 'Scarti vegetali: ritmo invernale', 'Mercato d’autunno', 'Corteo delle lanterne'], 1):
        R(P, f'news-card-{i}-more', '2.4.4', 'issue', 'cantTell',
          f'Link text "Scopri di più" sits alone in <p class="card-more">; only the card heading ("{title}") disambiguates it and a preceding heading is not programmatic context '
          f'(Klar. rule, Understanding 2.4.4) → cantTell; strict ACT 5effbb reading: failed.')
    R(P, 'news-card-2-img', '1.1.1', 'trap', 'passed', 'Understanding 1.1.1: short meaningful alt for the photo.')
    R(P, 'news-card-3-img', '1.1.1', 'issue', 'failed', 'Understanding 1.1.1 / F30: alt="foto3_def.png" is a file name, not a text alternative.')
    R(P, 'hero-text', '1.4.3', 'issue', 'failed', 'Understanding 1.4.3: white heading and lead on the light-blue sky of the background image, about 2.2–2.7:1.')
    R(P, 'notice-fr-para', '3.1.2', 'issue', 'failed', 'Understanding 3.1.2: a French paragraph (3 sentences) inside an it-CH page has no lang="fr".')
    R(P, 'event-registration-note', '3.1.2', 'issue', 'failed', 'Understanding 3.1.2: the English sentence "Please register before 30 November." has no lang="en".')
    R(P, 'event-computer-text', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: "weekend", "know-how", "computer" and "e-mail" are loanwords established in Italian; "Bahnhofstrasse 12" is an address (proper name).')
    R(P, 'event-maerit', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: "Musterwiler Märit" is the proper name of the market.')
    R(P, 'council-readmore', '2.4.4', 'issue', 'failed', 'Understanding 2.4.4: "Continua a leggere" stands alone in its own paragraph with no programmatic context.')
    R(P, 'intro-inline-link', '1.4.1', 'issue', 'failed', 'Understanding 1.4.1 / F73: inline link without underline, colour contrast with the surrounding text only 2.7:1 (< 3:1).')
    R(P, 'contact-map-link', '1.1.1', 'issue', 'failed', 'Understanding 1.1.1 / F89: image-only link with alt="".')
    R(P, 'contact-map-link', '2.4.4', 'issue', 'failed', 'Understanding 2.4.4: the link has an empty accessible name.')
    R(P, 'assembly-banner', '1.4.5', 'issue', 'failed', 'Understanding 1.4.5: poster image of text ("Assemblea comunale, 24 novembre 2026, ore 19.30, sala multiuso").')
    R(P, 'tips-aria-more', '2.4.4', 'trap', 'passed', 'Understanding 2.4.4 / ARIA8: aria-label "Di più sul calendario dei rifiuti 2026".')
    R(P, 'tips-aria-more', '2.5.3', 'trap', 'passed', 'Understanding 2.5.3: visible label "Di più" is contained at the start of the accessible name.')
    R(P, 'tips-sentence-more', '2.4.4', 'trap', 'passed', 'Understanding 2.4.4: "di più" is in a sentence that names the target.')
    R(P, 'tips-list-more', '2.4.4', 'trap', 'passed', 'Understanding 2.4.4: list-item context names the topic.')
    R(P, 'tips-list-more-2', '2.4.4', 'trap', 'passed', 'Understanding 2.4.4: list-item context gives the purpose.')
    R(P, 'lang-switch', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2 / H58: switcher links DE and FR carry lang and hreflang.')
    R(P, None, '3.1.1', 'trap', 'passed', 'Understanding 3.1.1: <html lang="it-CH"> matches the Italian content.')

    # ------------------------------------------------------------------ it/sportello-online.html  (issues replicated)
    main = f'''<div class="container page-head">
  <h1>Sportello online</h1>
  <p class="lead">Molti servizi dell’amministrazione comunale si possono ordinare comodamente online. I documenti vi vengono spediti per posta.</p>
</div>
<div class="container layout-main-aside">
  <div class="main-col">
    <form class="form-card form-classic" id="residence-form" action="grazie.html" method="get" data-form-mode="simple" data-success="grazie.html" data-msg-error="Errore" data-testid="residence-form">
      <h2>Ordinare un attestato di domicilio</h2>
      <p class="fee">Tassa: CHF 20.– per esemplare. Ricevete l’attestato con la fattura entro tre giorni lavorativi per posta.</p>
      <div class="form-alert" role="alert" data-error-summary data-testid="form-error-summary" hidden></div>
      <p class="hint">I campi contrassegnati con <span class="req">*</span> sono obbligatori.</p>
      <fieldset>
        <legend>Dati personali</legend>
        <div class="form-grid">
          <div class="field"><label for="f-given">Nome <span class="req">*</span></label><input id="f-given" name="nome" type="text" autocomplete="given-name" data-required data-testid="form-given-name"></div>
          <div class="field"><label for="f-family" data-testid="form-family-name-label">Cognome <span class="req">*</span></label><input id="f-family" name="cognome" type="text" autocomplete="family-name" data-required data-testid="form-family-name"></div>
          <div class="field"><label for="f-birth" data-testid="form-birthdate-label">Dati</label><input id="f-birth" name="nascita" type="text" inputmode="numeric" placeholder="GG.MM.AAAA" autocomplete="bday" data-testid="form-birthdate"></div>
          <div class="field"><label for="f-email">E-mail <span class="req">*</span></label><input id="f-email" name="email" type="email" autocomplete="email" data-required data-kind="email" data-testid="form-email"></div>
          <div class="field"><label for="f-tel">Telefono</label><input id="f-tel" name="telefono" type="tel" autocomplete="tel" data-testid="form-tel"></div>
          <div class="field"><label for="f-copies">Numero di esemplari</label><input id="f-copies" name="esemplari" type="number" min="1" max="5" value="1" data-testid="form-copies"></div>
        </div>
      </fieldset>
      <fieldset>
        <legend>Indirizzo di domicilio</legend>
        <div class="form-grid-3">
          <div class="field"><label for="f-street">Via e numero <span class="req">*</span></label><input id="f-street" name="via" type="text" data-required data-testid="form-street"></div>
          <div class="field"><label for="f-plz">NPA <span class="req">*</span></label><input id="f-plz" name="npa" type="text" inputmode="numeric" autocomplete="postal-code" data-required data-pattern="^[0-9]{{4}}$" data-error-id="f-plz-error" data-testid="form-plz"><span class="field-error" id="f-plz-error" data-msg="Inserimento non valido" data-testid="form-plz-error" hidden></span></div>
          <div class="field"><label for="f-city">Località <span class="req">*</span></label><input id="f-city" name="localita" type="text" autocomplete="address-level2" data-required data-testid="form-city"></div>
        </div>
      </fieldset>
      <div class="form-actions">
        <button type="submit" class="btn" aria-label="Invia il modulo" data-testid="form-submit">Invia</button>
      </div>
    </form>
  </div>
  <div class="aside-col">
    <section class="box" aria-labelledby="more-services">
      <h2 id="more-services">Altri servizi</h2>
      <ul class="link-list"><li><a href="istruzioni.html">Notificare un trasloco con eTrasloco</a></li><li><a href="calendario-rifiuti.html">Calendario dei rifiuti e punti di raccolta</a></li><li><a href="orari.html">Orari dell’amministrazione</a></li></ul>
    </section>
    <section class="box" aria-labelledby="questions"><h2 id="questions">Domande?</h2><p>Il controllo abitanti vi aiuta volentieri: telefono <a href="tel:+41320001210">032 000 12 10</a>.</p></section>
  </div>
</div>'''
    out['sportello-online.html'] = page(L, 'form', 'Sportello online – Comune di Musterwil', main, crumbs=['Sportello online'], scripts=('forms.js',))
    P = 'it/sportello-online.html'
    R(P, 'form-error-summary', '3.3.1', 'issue', 'failed', 'Understanding 3.3.1: on submit the summary only says "Errore"; fields in error are not identified (filled by JS).')
    R(P, 'form-plz-error', '3.3.1', 'issue', 'failed', 'Understanding 3.3.1: "Inserimento non valido" does not describe the error (filled by JS).')
    R(P, 'form-plz-error', '3.3.3', 'issue', 'failed', 'Understanding 3.3.3: no suggestion although the expected format (4-digit NPA) is known.')
    R(P, 'form-birthdate-label', '2.4.6', 'issue', 'failed', 'Understanding 2.4.6: the label "Dati" ("data") does not describe the date-of-birth field.')
    R(P, 'form-street', '1.3.5', 'issue', 'failed', 'Understanding 1.3.5: the user\'s street field has no autocomplete token.')
    R(P, 'form-email', '1.3.5', 'trap', 'passed', 'Understanding 1.3.5: autocomplete="email" matches the e-mail field.')
    R(P, 'form-copies', '1.3.5', 'trap', 'inapplicable', 'Understanding 1.3.5: the number of copies is not information about the user.')
    R(P, 'form-given-name', '1.4.11', 'issue', 'failed', 'Understanding 1.4.11: input border #dcdcdc on white is about 1.4:1 (< 3:1).')
    R(P, 'form-family-name-label', '1.4.1', 'trap', 'passed', 'Understanding 1.4.1: required fields are marked with an asterisk explained in text.')
    R(P, 'form-submit', '2.5.3', 'trap', 'passed', 'Understanding 2.5.3: visible label "Invia" is contained at the start of the accessible name "Invia il modulo".')
    R(P, 'residence-form', '3.3.4', 'issue', 'failed', 'Understanding 3.3.4: billed order (CHF 20.–) is submitted directly, without review, confirmation or correction step.')

    # ------------------------------------------------------------------ it/grazie.html
    main = f'''<div class="container narrow">
  <ol class="progress-steps" aria-label="Fasi dell’ordine">
    <li><span class="step-num">1</span>Dati</li>
    <li class="current" aria-current="step"><span class="step-num">2</span>Conferma</li>
  </ol>
  <h1>Grazie per il vostro ordine</h1>
  <div class="status status-success" role="status" data-testid="order-status">{icon("check")}<p><strong>Ordine trasmesso con successo.</strong> Numero d’ordine: MW-2026-04819.</p></div>
  <p>Riceverete l’attestato di domicilio per posta entro tre giorni lavorativi, insieme alla fattura di CHF 20.– per esemplare.</p>
  <p class="button-row"><a class="btn" href="index.html">Torna alla pagina iniziale</a> <a class="btn btn-secondary" href="sportello-online.html">Nuovo ordine</a></p>
</div>'''
    out['grazie.html'] = page(L, 'thanks', 'Ordine confermato – Comune di Musterwil', main, crumbs=[('Sportello online', 'sportello-online.html'), 'Conferma'])
    R('it/grazie.html', None, '2.4.5', 'trap', 'passed', 'Understanding 2.4.5: confirmation page is the result of a process, an explicit exception.')

    # ------------------------------------------------------------------ it/calendario-rifiuti.html
    main = f'''<div class="container page-head">
  <h1>Calendario dei rifiuti 2026</h1>
  <p class="lead">Date di raccolta, punti di raccolta e tasse del Comune di Musterwil.</p>
</div>
<div class="container layout-main-aside">
  <div class="main-col">
    <p>Vi preghiamo di depositare i sacchi dei rifiuti e i contenitori degli scarti vegetali a bordo strada il giorno della raccolta, <strong>entro le 7</strong>. I sacchi tassati sono in vendita nel negozio del paese, nella panetteria in piazza e presso l’amministrazione comunale.</p>
    <h2 data-testid="waste-dates-title">Date di raccolta 2026</h2>
    <p>Le date di novembre in un colpo d’occhio:</p>
    {calendar('it', letters=False)}
    <h2>Scarti vegetali: quantità raccolte nel 2025</h2>
    <p>La quantità di scarti vegetali varia molto con le stagioni. In inverno la raccolta avviene quindi solo ogni due settimane.</p>
    <figure class="chart-figure"><img src="{A}img/chart-gruengut-it.svg" alt="grafico.svg" width="960" height="560" data-testid="waste-chart"></figure>
    <h2>Punti di raccolta</h2>
    <div class="table-wrap">
      <table class="data-table" data-testid="collection-points-table">
        <caption>Punti di raccolta e orari</caption>
        <thead><tr><th scope="col">Punto di raccolta</th><th scope="col">Cosa si accetta</th><th scope="col">Orari</th></tr></thead>
        <tbody>
          <tr><th scope="row">Magazzino comunale Moosmatt</th><td>Scarti vegetali, ingombranti, metalli, apparecchi elettrici</td><td>Me 13.30–17.00, sa 09.00–12.00</td></tr>
          <tr><th scope="row">Punto di raccolta stazione</th><td>Vetro, alluminio, latta</td><td>Lu–sa 07.00–20.00</td></tr>
          <tr><th scope="row">Scuola Moosmatt</th><td>Abiti e scarpe usati</td><td>Sempre (container)</td></tr>
        </tbody>
      </table>
    </div>
  </div>
  <div class="aside-col">
    <section class="box" aria-labelledby="next-title"><h2 id="next-title">Prossime raccolte</h2>
      <ul class="link-list"><li>Martedì 20 ottobre: rifiuti domestici</li><li>Giovedì 22 ottobre: scarti vegetali</li><li>Mercoledì 28 ottobre: carta</li></ul></section>
  </div>
</div>'''
    out['calendario-rifiuti.html'] = page(L, 'waste', 'Calendario dei rifiuti 2026 – Comune di Musterwil', main, crumbs=['Calendario dei rifiuti'])
    P = 'it/calendario-rifiuti.html'
    R(P, 'waste-chart', '1.1.1', 'issue', 'failed', 'Understanding 1.1.1 / F30: the bar chart has alt="grafico.svg", a file name; data are not conveyed.')
    R(P, 'waste-calendar', '1.4.1', 'issue', 'failed', 'Understanding 1.4.1: collection types in the calendar are distinguished by dot colour only.')
    R(P, 'collection-points-table', '1.3.1', 'trap', 'passed', 'Understanding 1.3.1: table with caption and th scope.')
    R(P, 'main-nav', '3.2.3', 'trap', 'passed', 'Understanding 3.2.3: same navigation order as the other Italian pages.')

    # ------------------------------------------------------------------ it/orari.html  (lang="de-CH" by mistake)
    lib = hours_grid([('Lunedì', 'chiuso'), ('Martedì', '15.00–18.00'), ('Mercoledì', '14.00–18.00'),
                      ('Giovedì', '15.00–19.00'), ('Venerdì', 'chiuso'), ('Sabato', '09.30–12.00')], wrong_order=True)
    main = f'''<div class="container page-head">
  <h1>Orari d’apertura</h1>
  <p class="lead">Orari dell’amministrazione comunale, del magazzino comunale e della biblioteca.</p>
</div>
<div class="container layout-main-aside">
  <div class="main-col">
    <section aria-labelledby="h-admin">
      <h2 id="h-admin">Amministrazione comunale</h2>
      <div class="table-wrap">
        <table class="data-table" data-testid="hours-admin">
          <caption>Orari degli sportelli dal 1° novembre 2026</caption>
          <thead><tr><th scope="col">Giorno</th><th scope="col">Mattina</th><th scope="col">Pomeriggio</th></tr></thead>
          <tbody>
            <tr><th scope="row">Lunedì</th><td>08.00–11.30</td><td>14.00–17.00</td></tr>
            <tr><th scope="row">Martedì</th><td>08.00–11.30</td><td>14.00–17.00</td></tr>
            <tr><th scope="row">Mercoledì</th><td>08.00–11.30</td><td>chiuso</td></tr>
            <tr><th scope="row">Giovedì</th><td>08.00–11.30</td><td>14.00–18.30</td></tr>
            <tr><th scope="row">Venerdì</th><td>08.00–11.30</td><td>14.00–16.00</td></tr>
          </tbody>
        </table>
      </div>
    </section>
    <section id="biblioteca" aria-labelledby="h-lib">
      <h2 id="h-lib">Biblioteca comunale</h2>
      <p>Biblioteca in Bahnhofstrasse 12, nuovi orari dal 2 novembre 2026:</p>
      {lib}
    </section>
    <section id="ubicazione" aria-labelledby="h-loc">
      <h2 id="h-loc">Ubicazione e accesso</h2>
      <div class="loc-grid">
        <img src="{A}img/map-standort.svg" alt="Piantina: l’amministrazione comunale si trova in Dorfstrasse 1, a circa 100 metri dalla fermata dell’autobus Musterwil Dorf." width="800" height="450">
        <div><p>Amministrazione comunale di Musterwil<br>Dorfstrasse 1<br>9999 Musterwil</p><p>Autobus linea 12 fino alla fermata «Musterwil Dorf».</p></div>
      </div>
    </section>
    <section aria-labelledby="h-faq">
      <h2 id="h-faq">Domande frequenti</h2>
      <div class="accordion">
        <div class="acc-item"><div class="acc-toggle" data-testid="faq-toggle-1">L’amministrazione è aperta tra Natale e Capodanno?</div><div class="acc-panel"><p>L’amministrazione resta chiusa dal 24 dicembre 2026 al 3 gennaio 2027 compreso.</p></div></div>
        <div class="acc-item"><div class="acc-toggle" data-testid="faq-toggle-2">Posso venire fuori dagli orari d’apertura?</div><div class="acc-panel"><p>Sì, su appuntamento telefonico.</p></div></div>
      </div>
    </section>
  </div>
  <div class="aside-col">
    <section class="box" aria-labelledby="phone-hours"><h2 id="phone-hours">Orari telefonici</h2><p>Lu–ve 08.00–11.30 e 14.00–16.00<br>Telefono <a href="tel:+41320001234">032 000 12 34</a></p></section>
  </div>
</div>'''
    out['orari.html'] = page(L, 'hours', 'Orari d’apertura – Comune di Musterwil', main, crumbs=['Orari'], scripts=('accordion.js',), html_lang='de-CH')
    P = 'it/orari.html'
    R(P, None, '3.1.1', 'issue', 'failed', 'Understanding 3.1.1: <html lang="de-CH"> (copy-paste from the German page) although the whole page is in Italian.')
    R(P, None, '2.4.2', 'trap', 'passed', 'Understanding 2.4.2: title "Orari d’apertura – Comune di Musterwil" describes topic and site.')
    R(P, 'hours-library', '1.3.2', 'issue', 'failed', 'Understanding 1.3.2 / C27: CSS grid pairs days and hours visually, but the DOM lists all days first and then all times.')
    R(P, 'hours-library', '1.3.1', 'issue', 'failed', 'Understanding 1.3.1: six <dt> followed by six <dd> associate every day with every time; the pairing is not in the structure.')
    for i in (1, 2):
        R(P, f'faq-toggle-{i}', '4.1.2', 'issue', 'failed', 'Understanding 4.1.2: FAQ toggle is a <div> with a click handler: no role, not focusable, no expanded state.')
    R(P, 'hours-admin', '1.3.1', 'trap', 'passed', 'Understanding 1.3.1: table with caption and th scope.')

    # ------------------------------------------------------------------ it/bilingue.html
    main = '''<div class="container page-head">
  <h1>Avvisi ufficiali</h1>
  <p class="lead">Musterwil è un comune bilingue: gli avvisi ufficiali del Municipio sono pubblicati in tedesco e in francese. Qui trovate un riassunto in italiano e i testi originali.</p>
</div>
<div class="container">
  <article class="bi-notice">
    <header class="bi-head">
      <p class="bi-date"><time datetime="2026-10-09">9 ottobre 2026</time></p>
      <h2>Assemblea comunale del 24 novembre 2026</h2>
    </header>
    <p class="bi-summary" data-testid="notice-summary-it">Riassunto: gli aventi diritto di voto sono convocati martedì 24 novembre 2026 alle 19.30 nella sala multiuso. All’ordine del giorno figurano il preventivo 2027, il risanamento della scuola Moosmatt e la revisione parziale del regolamento sui rifiuti.</p>
    <div class="bi-grid">
      <div class="bi-col" lang="de-CH" data-testid="notice-col-de">
        <p class="bi-lang">Deutsch</p>
        <p>Die Stimmberechtigten werden zur ordentlichen Gemeindeversammlung eingeladen: Dienstag, 24. November 2026, 19.30 Uhr, Mehrzweckhalle.</p>
        <ol><li>Budget 2027 und Festsetzung der Steueranlage</li><li>Sanierung Schulhaus Moosmatt: Verpflichtungskredit von CHF 2,4 Mio.</li><li>Teilrevision des Abfallreglements</li><li>Verschiedenes</li></ol>
      </div>
      <div class="bi-col" lang="fr-CH" data-testid="notice-col-fr">
        <p class="bi-lang">Français</p>
        <p>Les ayants droit au vote sont convoqués à l’assemblée communale ordinaire : mardi 24 novembre 2026, à 19 h 30, à la salle polyvalente.</p>
        <ol><li>Budget 2027 et fixation de la quotité d’impôt</li><li>Assainissement de l’école de Moosmatt : crédit d’engagement de 2,4 millions de francs</li><li>Révision partielle du règlement sur les déchets</li><li>Divers</li></ol>
      </div>
    </div>
  </article>
</div>'''
    out['bilingue.html'] = page(L, 'bilingual', 'Avvisi ufficiali – Comune di Musterwil', main, crumbs=['Avvisi ufficiali'])
    P = 'it/bilingue.html'
    R(P, 'notice-col-de', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2 / H58: the German original is marked lang="de-CH".')
    R(P, 'notice-col-fr', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2 / H58: the French original is marked lang="fr-CH".')

    # ------------------------------------------------------------------ it/tempo-libero.html  (no pause, span controls)
    main = f'''<div class="container page-head">
  <h1>Tempo libero e turismo</h1>
  <p class="lead">Riva del lago, bosco dell’Aarenwald e un paese pieno di vita: scoprite Musterwil in ogni stagione.</p>
</div>
<div class="container">
  <div class="carousel" role="region" aria-label="Immagini di Musterwil" data-carousel data-interval="5000" data-testid="carousel">
    <div class="carousel-track">
      <figure class="slide is-active"><img src="{A}img/slide-seeufer.svg" alt="Pontile e barca a vela sul lago nella luce della sera" width="1200" height="500"><figcaption>Riva del lago: lido, pontile e passeggiata</figcaption></figure>
      <figure class="slide"><img src="{A}img/slide-wald.svg" alt="Sentiero nel bosco autunnale con pannello informativo" width="1200" height="500"><figcaption>Sentiero didattico dell’Aarenwald – 4,5 km, ideale per famiglie</figcaption></figure>
      <figure class="slide"><img src="{A}img/slide-dorfplatz.svg" alt="Piazza del paese con fontana e bancarelle" width="1200" height="500"><figcaption>Musterwiler Märit in piazza – prossima data: 24 ottobre</figcaption></figure>
      <figure class="slide"><img src="{A}img/slide-schiff.svg" alt="Battello di linea sul lago davanti a colline boscose" width="1200" height="500"><figcaption>Giro del lago in battello: ogni giorno da aprile a ottobre</figcaption></figure>
    </div>
    <span class="carousel-ctrl carousel-prev" data-carousel-prev data-testid="carousel-prev">{icon("left")}</span>
    <span class="carousel-ctrl carousel-next" data-carousel-next data-testid="carousel-next">{icon("right")}</span>
    <div class="carousel-dots" aria-hidden="true"><span class="carousel-dot is-active"></span><span class="carousel-dot"></span><span class="carousel-dot"></span><span class="carousel-dot"></span></div>
  </div>
  <section class="section" aria-labelledby="offers-title">
    <h2 id="offers-title">Offerte a Musterwil</h2>
    <div class="filter-bar">
      <label for="offer-filter">Filtrare le offerte</label>
      <select id="offer-filter" data-filter-target="offer-list" data-filter-status="offer-count" data-testid="activity-filter">
        <option value="all">Tutte le offerte</option><option value="sport">Sport e bagni</option><option value="kultur">Cultura</option><option value="natur">Natura</option><option value="gastro">Gastronomia</option>
      </select>
      <p id="offer-count" class="filter-count" role="status" data-template="{{n}} offerte visualizzate"></p>
    </div>
    <ul class="offer-grid" id="offer-list">
      <li data-category="sport"><p class="offer-tag">Sport e bagni</p><h3>Lido sulla riva del lago</h3><p>Prato, trampolino e vasca per bambini. Aperto da metà maggio a metà settembre, con il bel tempo dalle 9 alle 20.</p></li>
      <li data-category="kultur"><p class="offer-tag">Cultura</p><h3>Cinema all’aperto sul lago</h3><p>Ogni venerdì di luglio e agosto l’associazione culturale proietta un film sotto le stelle. Entrata libera, colletta.</p></li>
      <li data-category="natur"><p class="offer-tag">Natura</p><h3>Sentiero didattico</h3><p>4,5 km con 20 pannelli su alberi, animali e funghi. Percorribile con passeggini.</p></li>
      <li data-category="gastro" data-testid="activity-sushi"><p class="offer-tag">Gastronomia</p><h3>Serata sushi al Café du Lac</h3><p>Ogni primo venerdì del mese il Café du Lac propone sushi e piatti del lago. Prenotazione consigliata.</p></li>
    </ul>
  </section>
</div>'''
    out['tempo-libero.html'] = page(L, 'leisure', 'Tempo libero e turismo – Comune di Musterwil', main, crumbs=['Tempo libero e turismo'], scripts=('carousel.js', 'filter.js'))
    P = 'it/tempo-libero.html'
    R(P, 'carousel', '2.2.2', 'issue', 'failed', 'Understanding 2.2.2: auto-advancing carousel (every 5 s, indefinitely) without pause, stop or hide control.')
    R(P, 'carousel-prev', '4.1.2', 'issue', 'failed', 'Understanding 4.1.2: <span> control without role, name or keyboard access.')
    R(P, 'carousel-next', '4.1.2', 'issue', 'failed', 'Understanding 4.1.2: <span> control without role, name or keyboard access.')
    R(P, 'activity-filter', '3.2.2', 'trap', 'passed', 'Understanding 3.2.2: select filters the list on the same page; no change of context.')
    R(P, 'activity-sushi', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: "sushi" is a loanword in Italian and "Café du Lac" a proper name.')

    # ------------------------------------------------------------------ it/istruzioni.html
    main = f'''<div class="container page-head">
  <h1>Notificare un trasloco online</h1>
  <p class="lead">Con eTrasloco notificate online il vostro trasloco in Svizzera – al comune di partenza e a quello di arrivo contemporaneamente.</p>
</div>
<div class="container guide-layout">
  <ol class="steps">
    <li><h2>Aprire il modulo</h2><p>Aprite lo sportello online e scegliete «Notificare un trasloco». Tenete a portata di mano il nuovo indirizzo e la data del trasloco.</p></li>
    <li><h2>Inserire i dati personali</h2><p data-testid="instruction-table-ref">Inserite nome, data di nascita e indirizzo attuale. I documenti necessari sono elencati nella tabella qui sotto.</p></li>
    <li><h2>Passare al nuovo indirizzo</h2><p data-testid="instruction-next-button">Cliccate in basso a destra su «Avanti».</p></li>
    <li><h2>Confermare i dati</h2><p data-testid="instruction-green-button">Controllate il nuovo indirizzo. Se tutto è corretto, cliccate sul pulsante verde a destra.</p></li>
    <li><h2>Ricevere la conferma</h2><p>Riceverete subito una conferma per e-mail. Il comune vi contatterà se mancano documenti.</p></li>
  </ol>
  <aside class="mock-wrap" aria-labelledby="mock-title">
    <h2 id="mock-title" class="mock-heading">Vista di prova</h2>
    <p class="mock-intro">Ecco come si presenta eTrasloco. Provate pure i pulsanti: nessun dato viene trasmesso.</p>
    <div class="mock-window">
      <div class="mock-bar"><span></span><span></span><span></span><p>eTrasloco – passo 2 di 4</p></div>
      <div class="mock-body">
        <p class="mock-label">Nome</p><p class="mock-value">Lukas Muster</p>
        <p class="mock-label">Indirizzo attuale</p><p class="mock-value">Lindenweg 3, 9998 Beispielhausen</p>
        <div class="mock-actions"><button type="button" class="btn" data-practice="practice-status" data-practice-msg="Prova: ora siete al passo 3." data-testid="practice-next-button">Avanti</button></div>
      </div>
    </div>
    <div class="mock-window">
      <div class="mock-bar"><span></span><span></span><span></span><p>eTrasloco – passo 3 di 4</p></div>
      <div class="mock-body mock-confirm">
        <div><p class="mock-label">Nuovo indirizzo</p><p class="mock-value">Seeweg 7, 9999 Musterwil</p><p class="mock-label">Data di arrivo</p><p class="mock-value">1° dicembre 2026</p></div>
        <button type="button" class="round-go" aria-label="Procedi" data-practice="practice-status" data-practice-msg="Prova: i vostri dati sarebbero ora confermati." data-testid="practice-confirm-button">{icon("arrow")}</button>
      </div>
    </div>
    <p id="practice-status" class="practice-status" role="status"></p>
  </aside>
</div>
<div class="container section">
  <div class="table-wrap">
    <table class="data-table" data-testid="documents-table">
      <caption>Documenti necessari</caption>
      <thead><tr><th scope="col">La vostra situazione</th><th scope="col">Documenti</th></tr></thead>
      <tbody>
        <tr><th scope="row">Cittadini svizzeri</th><td>Atto d’origine (solo in caso di arrivo da un altro comune)</td></tr>
        <tr><th scope="row">Cittadini stranieri</th><td>Permesso di dimora e passaporto o carta d’identità validi</td></tr>
        <tr><th scope="row">Famiglie</th><td>Certificato di famiglia o libretto di famiglia</td></tr>
      </tbody>
    </table>
  </div>
</div>'''
    out['istruzioni.html'] = page(L, 'guide', 'Istruzioni eTrasloco – Comune di Musterwil', main, crumbs=['Istruzioni eTrasloco'])
    P = 'it/istruzioni.html'
    R(P, 'instruction-green-button', '1.3.3', 'issue', 'failed', 'Understanding 1.3.3: "cliccate sul pulsante verde a destra" relies only on colour and position; the button shows only an arrow (name "Procedi" not mentioned).')
    R(P, 'instruction-next-button', '1.3.3', 'trap', 'passed', 'Understanding 1.3.3: position plus the visible button text «Avanti».')
    R(P, 'instruction-table-ref', '1.3.3', 'trap', 'passed', 'Understanding 1.3.3: "tabella qui sotto" points to the only table, captioned "Documenti necessari".')

    # ------------------------------------------------------------------ it/mappa-del-sito.html
    main = '''<div class="container page-head">
  <h1>Mappa del sito</h1>
  <p class="lead">Tutte le pagine del sito di Musterwil in un colpo d’occhio.</p>
</div>
<div class="container sitemap-grid">
  <section aria-labelledby="sm-admin"><h2 id="sm-admin">Amministrazione</h2>
    <ul><li><a href="index.html">Pagina iniziale</a></li><li><a href="sportello-online.html">Sportello online</a></li><li><a href="orari.html">Orari d’apertura</a></li><li><a href="bilingue.html">Avvisi ufficiali</a></li></ul></section>
  <section aria-labelledby="sm-living"><h2 id="sm-living">Abitare e ambiente</h2>
    <ul><li><a href="istruzioni.html">Istruzioni eTrasloco</a></li><li><a href="calendario-rifiuti.html">Calendario dei rifiuti 2026</a></li></ul></section>
  <section aria-labelledby="sm-leisure"><h2 id="sm-leisure">Tempo libero</h2>
    <ul><li><a href="tempo-libero.html">Tempo libero e turismo</a></li></ul></section>
  <section aria-labelledby="sm-service"><h2 id="sm-service">Servizi</h2>
    <ul><li><a href="ricerca.html">Ricerca</a></li><li><a href="mappa-del-sito.html">Mappa del sito</a></li><li><a href="accessibilita.html">Dichiarazione di accessibilità</a></li></ul></section>
  <section aria-labelledby="sm-lang"><h2 id="sm-lang">Altre lingue</h2>
    <ul><li><a href="../sitemap.html" lang="de-CH" hreflang="de">Sitemap auf Deutsch</a></li><li><a href="../fr/plan-du-site.html" lang="fr-CH" hreflang="fr">Plan du site en français</a></li></ul></section>
</div>'''
    out['mappa-del-sito.html'] = page(L, 'sitemap', 'Mappa del sito – Comune di Musterwil', main, crumbs=['Mappa del sito'])

    # ------------------------------------------------------------------ it/ricerca.html
    entries = [
        dict(title='Pagina iniziale', url='index.html', text='Attualità, manifestazioni e comunicazioni del Comune di Musterwil.', keywords='notizie attualita'),
        dict(title='Sportello online', url='sportello-online.html', text='Ordinare un attestato di domicilio.', keywords='modulo ordine attestato domicilio'),
        dict(title='Istruzioni eTrasloco', url='istruzioni.html', text='Notificare un trasloco online: istruzioni passo per passo e documenti necessari.', keywords='trasloco arrivo partenza indirizzo'),
        dict(title='Orari d’apertura', url='orari.html', text='Orari dell’amministrazione, del magazzino comunale e della biblioteca; ubicazione.', keywords='sportello biblioteca telefono'),
        dict(title='Calendario dei rifiuti 2026', url='calendario-rifiuti.html', text='Date di raccolta di rifiuti domestici, scarti vegetali, carta e cartone; punti di raccolta.', keywords='rifiuti scarti vegetali carta cartone'),
        dict(title='Tempo libero e turismo', url='tempo-libero.html', text='Lido, sentiero didattico, cultura e gastronomia a Musterwil.', keywords='turismo gita cultura'),
        dict(title='Avvisi ufficiali', url='bilingue.html', text='Avvisi del Municipio in tedesco e francese con riassunto in italiano.', keywords='municipio assemblea preventivo'),
        dict(title='Mappa del sito', url='mappa-del-sito.html', text='Tutte le pagine del sito in un colpo d’occhio.', keywords='panoramica pagine'),
        dict(title='Dichiarazione di accessibilità', url='accessibilita.html', text='Stato dell’accessibilità di questo sito e modulo di contatto.', keywords='accessibilita feedback'),
    ]
    main = f'''<div class="container page-head"><h1>Ricerca</h1></div>
<div class="container narrow">
  <form class="search-page" role="search" action="ricerca.html" method="get" data-search-form>
    <label for="search-q">Termine di ricerca</label>
    <div class="search-field"><input id="search-q" name="q" type="search" autocomplete="off"><button type="submit" class="search-go" aria-label="Cerca" data-testid="search-page-button">{icon("search")}</button></div>
  </form>
  <p class="search-status" role="status" data-search-status data-msg-empty="Inserite un termine di ricerca, per esempio «rifiuti» o «trasloco»." data-msg-count="{{n}} risultati per «{{q}}»" data-msg-none="Nessun risultato per «{{q}}». Provate un altro termine o consultate la mappa del sito."></p>
  <ol class="search-results" data-search-results></ol>
</div>
{search_index(entries)}'''
    out['ricerca.html'] = page(L, 'search', 'Ricerca – Comune di Musterwil', main, crumbs=['Ricerca'], scripts=('search.js',))
    R('it/ricerca.html', 'search-page-button', '1.4.11', 'issue', 'failed', 'Understanding 1.4.11: icon-only search button drawn in #c9cdd2 on white (about 1.6:1).')
    R('it/ricerca.html', 'search-page-button', '2.5.3', 'trap', 'inapplicable', 'Understanding 2.5.3: icon-only button without visible text.')

    # ------------------------------------------------------------------ it/accessibilita.html
    main = '''<div class="container page-head"><h1>Dichiarazione di accessibilità</h1></div>
<div class="container with-sidebar">
  <div class="content">
    <p>Il Comune di Musterwil si impegna a rendere accessibile il proprio sito musterwil.example secondo le Web Content Accessibility Guidelines (WCAG) 2.1, livello AA, e lo standard eCH-0059.</p>
    <h2>Stato di conformità</h2>
    <p>Questo sito è <strong>parzialmente conforme</strong> alle WCAG 2.1, livello AA. I contenuti elencati qui sotto non sono ancora accessibili.</p>
    <h2>Contenuti non accessibili</h2>
    <ul><li>Alcuni vecchi documenti PDF dell’archivio (prima del 2022) non sono del tutto accessibili.</li><li>Ad alcune immagini di articoli meno recenti manca un testo alternativo significativo.</li><li>Le registrazioni dell’assemblea comunale non hanno ancora sottotitoli.</li></ul>
    <h2>Redazione della dichiarazione</h2>
    <p>La dichiarazione è stata redatta il 3 marzo 2025 sulla base di un’autovalutazione dell’amministrazione comunale.</p>
    <h2>Segnalazioni</h2>
    <p>Avete notato un problema di accessibilità? Segnalatecelo con il modulo seguente.</p>
    <form class="form-card form-std" action="accessibilita.html" method="get">
      <div class="form-grid">
        <div class="field"><label for="fb-name">Il vostro nome</label><input id="fb-name" type="text" autocomplete="name"></div>
        <div class="field"><label for="fb-email">Il vostro indirizzo e-mail</label><input id="fb-email" type="email" autocomplete="email"></div>
        <div class="field field-full"><label for="fb-msg">Il vostro messaggio</label><textarea id="fb-msg" rows="5"></textarea></div>
      </div>
      <div class="form-actions"><div class="btn" onclick="sendFeedback(this)" data-testid="feedback-submit">Invia</div></div>
      <p class="feedback-status" role="status" data-feedback-status data-msg="Grazie per la vostra segnalazione. Vi risponderemo entro dieci giorni lavorativi." hidden></p>
    </form>
  </div>
  <nav class="side" aria-labelledby="related-title" data-testid="related-sidebar">
    <h2 id="related-title" class="side-title">Pagine correlate</h2>
    <ul><li><a href="mappa-del-sito.html">Mappa del sito</a></li><li><a href="ricerca.html">Ricerca</a></li><li><a href="sportello-online.html">Sportello online</a></li></ul>
  </nav>
</div>'''
    out['accessibilita.html'] = page(L, 'a11y', 'Dichiarazione di accessibilità – Comune di Musterwil', main, crumbs=['Accessibilità'])
    R('it/accessibilita.html', 'feedback-submit', '4.1.2', 'issue', 'failed', 'Understanding 4.1.2: "Invia" is a <div class="btn" onclick>: no button role, not focusable.')

    return out
