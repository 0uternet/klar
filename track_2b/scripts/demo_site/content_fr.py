"""French pages (fr/)."""
from chrome import page, icon
from common import calendar, search_index, hours_grid

A = '../assets/'
L = 'fr'


def build(R):
    out = {}

    # ------------------------------------------------------------------ fr/index.html
    main = f'''<section class="hero" aria-labelledby="hero-title">
  <div class="container">
    <div class="hero-text" data-testid="hero-text">
      <h1 id="hero-title">Bienvenue à Musterwil</h1>
      <p>Une commune vivante entre la forêt de l’Aarenwald et le bord du lac – et en ligne pour vous, jour et nuit.</p>
    </div>
    <p class="hero-actions"><a class="btn btn-light" href="guichet-en-ligne.html">Accéder au guichet en ligne</a> <a class="btn" href="calendrier-dechets.html">Calendrier des déchets 2026</a></p>
  </div>
</section>

<nav class="quicklinks container" aria-label="Accès rapide">
  <ul>
    <li><a href="guichet-en-ligne.html"><span class="ql-icon">{icon("monitor")}</span><span class="ql-text"><strong>Guichet en ligne</strong><small>Attestation de domicile et autres</small></span></a></li>
    <li><a href="instructions.html"><span class="ql-icon">{icon("box")}</span><span class="ql-text"><strong>Annoncer un déménagement</strong><small>eDéménagement en cinq étapes</small></span></a></li>
    <li><a href="calendrier-dechets.html"><span class="ql-icon">{icon("calendar")}</span><span class="ql-text"><strong>Calendrier des déchets</strong><small>Dates et points de collecte</small></span></a></li>
    <li><a href="horaires.html"><span class="ql-icon">{icon("clock")}</span><span class="ql-text"><strong>Horaires</strong><small>Administration, voirie, bibliothèque</small></span></a></li>
  </ul>
</nav>

<section class="section container" aria-labelledby="news-title">
  <div class="section-head"><h2 id="news-title">Actualités</h2></div>
  <div class="grid-4">
    <article class="card">
      <img src="{A}img/news-gemeindehaus.svg" alt="Maison communale de Musterwil avec sa tour de l’horloge" width="640" height="360" data-testid="news-card-1-img">
      <div class="card-body">
        <p class="card-date"><time datetime="2026-10-12">12 octobre 2026</time></p>
        <h3>Nouveaux horaires des guichets dès le 1<sup>er</sup> novembre</h3>
        <p>L’administration communale sera désormais ouverte le jeudi soir jusqu’à 18 h 30. En contrepartie, le guichet sera fermé le mercredi après-midi.</p>
        <p class="card-more"><a href="horaires.html" data-testid="news-card-1-more">En savoir plus</a></p>
      </div>
    </article>
    <article class="card">
      <img src="{A}img/news-recycling.svg" alt="DSC_0157.JPG" width="640" height="360" data-testid="news-card-2-img">
      <div class="card-body">
        <p class="card-date"><time datetime="2026-10-08">8 octobre 2026</time></p>
        <h3>Déchets verts : rythme d’hiver</h3>
        <p>Dès novembre, les déchets verts ne seront plus ramassés que toutes les deux semaines. Merci de tenir compte des nouvelles dates.</p>
        <p class="card-more"><a href="calendrier-dechets.html" data-testid="news-card-2-more">En savoir plus</a></p>
      </div>
    </article>
    <article class="card">
      <img src="{A}img/news-maerit.svg" alt="Stands de marché avec courges, pommes et pain sur la place du village" width="640" height="360" data-testid="news-card-3-img">
      <div class="card-body">
        <p class="card-date"><time datetime="2026-10-05">5 octobre 2026</time></p>
        <h3>Marché d’automne le 24 octobre</h3>
        <p>Plus de 40 stands de produits régionaux, d’artisanat et de soupe à la courge, avec la fanfare du village.</p>
        <p class="card-more"><a href="loisirs.html" data-testid="news-card-3-more">En savoir plus</a></p>
      </div>
    </article>
    <article class="card">
      <img src="{A}img/news-laternen.svg" alt="Enfants avec des lanternes allumées dans la nuit" width="640" height="360" data-testid="news-card-4-img">
      <div class="card-body">
        <p class="card-date"><time datetime="2026-10-01">1<sup>er</sup> octobre 2026</time></p>
        <h3>Cortège des lanternes le 11 novembre</h3>
        <p>Les enfants de l’école enfantine défilent dans le village avec leurs lanternes de raves. Départ à 18 h devant l’école de Moosmatt.</p>
        <p class="card-more"><a href="loisirs.html" data-testid="news-card-4-more">En savoir plus</a></p>
      </div>
    </article>
  </div>

  <div class="teaser-strip">
    <span class="strip-icon">{icon("users")}</span>
    <div>
      <p>Lors de sa séance du 6 octobre 2026, le Conseil communal a adopté le budget 2027 et inscrit l’assainissement de l’école de Moosmatt à l’ordre du jour de l’assemblée communale du 24 novembre.</p>
      <p><a href="bilingue.html" data-testid="council-readmore">Lire la suite</a></p>
    </div>
  </div>
</section>

<div class="container layout-main-aside section">
  <div class="main-col">
    <section aria-labelledby="admin-title">
      <h2 id="admin-title">Votre administration communale</h2>
      <p data-testid="intro-para">Carte d’identité, attestation de domicile ou marque pour chien : l’administration communale est votre premier interlocuteur. De nombreuses prestations sont disponibles jour et nuit au guichet en ligne ; les nouveaux <a href="horaires.html" class="link-plain" data-testid="intro-inline-link">horaires d’ouverture</a> de nos guichets s’appliquent dès le 1<sup>er</sup> novembre 2026.</p>
    </section>
    <aside class="notice" aria-labelledby="notice-title" data-testid="notice-box">
      <p class="notice-label">{icon("megaphone")}Communiqué</p>
      <h2 id="notice-title">Communiqué du service des routes de la Région Aarenwald</h2>
      <p>Ce communiqué n’est disponible qu’en allemand :</p>
      <p data-testid="notice-de-para">Wegen Belagsarbeiten ist die Seestrasse vom 2. bis 13. November 2026 für den Durchgangsverkehr gesperrt. Die Zufahrt für Anwohnende ist jederzeit gewährleistet. Die Buslinie 12 wird in dieser Zeit über die Bahnhofstrasse umgeleitet.</p>
    </aside>
  </div>
  <div class="aside-col">
    <section class="box" aria-labelledby="tips-title">
      <h2 id="tips-title">Bon à savoir</h2>
      <p data-testid="tips-sentence">Toutes les dates de ramassage des déchets verts figurent dans le calendrier des déchets – <a href="calendrier-dechets.html" data-testid="tips-sentence-more">plus</a>.</p>
      <ul class="tick-list">
        <li>La bibliothèque communale a de nouveaux horaires dès le 2 novembre – <a href="horaires.html#bibliotheque" data-testid="tips-list-more">plus</a></li>
        <li>Annoncer un déménagement en ligne dans toute la Suisse – <a href="instructions.html" data-testid="tips-list-more-2">plus</a></li>
      </ul>
      <div class="mini-promo">
        <h3>Calendrier des déchets 2026</h3>
        <p>Toutes les dates de collecte des ordures, des déchets verts, du papier et du carton en un coup d’œil.</p>
        <p><a class="btn btn-small" href="calendrier-dechets.html" aria-label="Plus d’informations sur le calendrier des déchets 2026" data-testid="tips-aria-more">Plus</a></p>
      </div>
    </section>
    <section class="box" aria-labelledby="contact-title">
      <h2 id="contact-title">Contact</h2>
      <div class="contact-row">
        <div>
          <p>Administration communale de Musterwil<br>Dorfstrasse 1, 9999 Musterwil</p>
          <p>Téléphone <a href="tel:+41320001234">032 000 12 34</a><br><a href="mailto:gemeinde@musterwil.example">gemeinde@musterwil.example</a></p>
        </div>
        <a class="icon-link" href="horaires.html#situation" data-testid="contact-map-link"><img src="{A}img/icon-map-pin.svg" alt="" width="24" height="24"></a>
      </div>
    </section>
  </div>
</div>

<section class="section-alt" aria-labelledby="events-title">
  <div class="container">
    <h2 id="events-title">Manifestations</h2>
    <div class="events-layout">
      <ul class="event-list">
        <li class="event" data-testid="event-maerit">
          <p class="date-tile"><time datetime="2026-10-24"><span class="d">24</span><span class="m">oct.</span></time></p>
          <div><h3>Musterwiler Märit sur la place du village</h3><p>Samedi, de 9 h à 16 h. Le traditionnel Musterwiler Märit propose des produits régionaux et de l’artisanat ; à 11 h, le Conseil communal offre l’apéritif.</p></div>
        </li>
        <li class="event">
          <p class="date-tile"><time datetime="2026-11-11"><span class="d">11</span><span class="m">nov.</span></time></p>
          <div><h3>Cortège des lanternes</h3><p>Mercredi, 18 h, départ devant l’école de Moosmatt. L’association des parents offre ensuite du punch chaud.</p></div>
        </li>
        <li class="event">
          <p class="date-tile"><time datetime="2026-11-24"><span class="d">24</span><span class="m">nov.</span></time></p>
          <div><h3>Assemblée communale</h3><p>Mardi, 19 h 30, salle polyvalente. Ordre du jour : budget 2027 et assainissement de l’école de Moosmatt.</p></div>
        </li>
        <li class="event" data-testid="event-library">
          <p class="date-tile"><time datetime="2026-12-04"><span class="d">4</span><span class="m">déc.</span></time></p>
          <div><h3>Heure du conte à la bibliothèque</h3><p>Vendredi, 17 h, bibliothèque communale, Bahnhofstrasse 12. Pour les enfants de 4 à 8 ans, entrée libre.</p></div>
        </li>
      </ul>
      <figure class="banner-figure">
        <img src="{A}img/banner-versammlung-fr.svg" alt="Assemblée communale, 24 novembre 2026, 19 h 30, salle polyvalente" width="640" height="800" data-testid="assembly-banner">
      </figure>
    </div>
  </div>
</section>

<section class="section container" aria-labelledby="stats-title">
  <h2 id="stats-title">Musterwil en chiffres</h2>
  <dl class="stats">
    <div><dt>Habitantes et habitants</dt><dd>3842</dd></div>
    <div><dt>Superficie</dt><dd>12,6 km²</dd></div>
    <div><dt>Altitude</dt><dd>431 m</dd></div>
    <div><dt>Sociétés locales</dt><dd>41</dd></div>
  </dl>
  <p class="source">Source : Office fédéral de la statistique (OFS), état au 31 décembre 2025.</p>
</section>'''
    out['index.html'] = page(L, 'home', 'Commune de Musterwil', main,
                             description='Site officiel de la commune de Musterwil : actualités, guichet en ligne, calendrier des déchets et manifestations.')
    P = 'fr/index.html'
    for i, title in enumerate(['Nouveaux horaires des guichets', 'Déchets verts : rythme d’hiver', 'Marché d’automne', 'Cortège des lanternes'], 1):
        R(P, f'news-card-{i}-more', '2.4.4', 'issue', 'cantTell',
          f'Link text "En savoir plus" sits alone in <p class="card-more">; only the card heading ("{title}") disambiguates it and a preceding heading is not programmatic context '
          f'(Klar. rule, Understanding 2.4.4) → cantTell; strict ACT 5effbb reading: failed.')
    R(P, 'news-card-1-img', '1.1.1', 'trap', 'passed', 'Understanding 1.1.1: short meaningful alt for the photo.')
    R(P, 'news-card-2-img', '1.1.1', 'issue', 'failed', 'Understanding 1.1.1 / F30: alt="DSC_0157.JPG" is a camera file name, not a text alternative.')
    R(P, 'hero-text', '1.4.3', 'issue', 'failed', 'Understanding 1.4.3: white heading and lead on the light-blue sky of the background image, about 2.2–2.7:1.')
    R(P, 'notice-de-para', '3.1.2', 'issue', 'failed', 'Understanding 3.1.2: a German paragraph (3 sentences) inside a fr-CH page has no lang="de"; it would be read with French pronunciation.')
    R(P, 'council-readmore', '2.4.4', 'issue', 'failed', 'Understanding 2.4.4: "Lire la suite" stands alone in its own paragraph with no programmatic context.')
    R(P, 'intro-inline-link', '1.4.1', 'issue', 'failed', 'Understanding 1.4.1 / F73: inline link without underline, colour contrast with the surrounding text only 2.7:1 (< 3:1).')
    R(P, 'contact-map-link', '1.1.1', 'issue', 'failed', 'Understanding 1.1.1 / F89: image-only link with alt="".')
    R(P, 'contact-map-link', '2.4.4', 'issue', 'failed', 'Understanding 2.4.4: the link has an empty accessible name.')
    R(P, 'assembly-banner', '1.4.5', 'issue', 'failed', 'Understanding 1.4.5: poster image of text ("Assemblée communale, 24 novembre 2026, 19 h 30, salle polyvalente"); real text could be used.')
    R(P, 'tips-sentence-more', '2.4.4', 'trap', 'passed', 'Understanding 2.4.4: "plus" is in a sentence that names the target (calendrier des déchets).')
    R(P, 'tips-list-more', '2.4.4', 'trap', 'passed', 'Understanding 2.4.4: "plus" is inside a list item that names the topic.')
    R(P, 'tips-list-more-2', '2.4.4', 'trap', 'passed', 'Understanding 2.4.4: list-item context gives the purpose.')
    R(P, 'tips-aria-more', '2.4.4', 'trap', 'passed', 'Understanding 2.4.4 / ARIA8: aria-label "Plus d’informations sur le calendrier des déchets 2026".')
    R(P, 'tips-aria-more', '2.5.3', 'trap', 'passed', 'Understanding 2.5.3: visible label "Plus" is contained at the start of the accessible name.')
    R(P, 'event-maerit', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: "Musterwiler Märit" is the proper name of the market.')
    R(P, 'event-library', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: "Bahnhofstrasse 12" is an address (proper name).')
    R(P, 'lang-switch', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2 / H58: switcher links DE and IT carry lang and hreflang.')
    R(P, 'site-logo', '1.1.1', 'trap', 'passed', 'Understanding 1.1.1: logo alt "Commune de Musterwil – Accueil" names the link target.')
    R(P, None, '3.1.1', 'trap', 'passed', 'Understanding 3.1.1: <html lang="fr-CH"> matches the French content.')

    # ------------------------------------------------------------------ fr/guichet-en-ligne.html  (review step, good error handling)
    def fld(fid, label, testid, ac=None, req=True, typ='text', extra='', review=None, msg_req='', msg_fmt='', pattern=None, kind=None, hint='', full=False, label_testid=None):
        star = ' <span class="req" aria-hidden="true">*</span>' if req else ''
        hint_html = f' <span class="hint-inline">{hint}</span>' if hint else ''
        ac_attr = f' autocomplete="{ac}"' if ac else ''
        req_attr = ' required' if req else ''
        pat = f' data-pattern="{pattern}"' if pattern else ''
        knd = f' data-kind="{kind}"' if kind else ''
        rv = f' data-review-label="{review or label}"'
        msgs = (f' data-msg-required="{msg_req}"' if msg_req else '') + (f' data-msg-format="{msg_fmt}"' if msg_fmt else '')
        lt = f' data-testid="{label_testid}"' if label_testid else ''
        cls = 'field field-full' if full else 'field'
        return (f'<div class="{cls}"><label for="{fid}"{lt}>{label}{star}{hint_html}</label>'
                f'<input id="{fid}" name="{fid}" type="{typ}"{ac_attr}{req_attr}{pat}{knd}{rv}{msgs} data-error-id="{fid}-error" aria-describedby="{fid}-error"{extra} data-testid="{testid}">'
                f'<span class="field-error" id="{fid}-error"{" data-testid=\"form-plz-error\"" if testid == "form-plz" else ""} hidden></span></div>')

    main = f'''<div class="container page-head">
  <h1>Guichet en ligne</h1>
  <p class="lead">De nombreuses prestations de l’administration communale peuvent être commandées en ligne. Vous recevez les documents par la poste.</p>
</div>
<div class="container layout-main-aside">
  <div class="main-col">
    <form class="form-card form-std" id="residence-form" action="merci.html" method="get" data-form-mode="review" data-success="merci.html" data-msg-summary="Le formulaire contient {{n}} erreur(s). Veuillez corriger :" data-testid="residence-form">
      <h2>Commander une attestation de domicile</h2>
      <p class="fee">Émolument : CHF 20.– par exemplaire. L’attestation vous est envoyée par la poste avec la facture dans un délai de trois jours ouvrables.</p>
      <div class="form-alert" tabindex="-1" data-error-summary data-testid="form-error-summary" hidden></div>
      <div data-step-edit>
        <p class="hint">Les champs marqués d’un astérisque (<span class="req">*</span>) sont obligatoires.</p>
        <fieldset>
          <legend>Données personnelles</legend>
          <div class="form-grid">
            {fld('f-given', 'Prénom', 'form-given-name', 'given-name', msg_req='Prénom : veuillez indiquer votre prénom.')}
            {fld('f-family', 'Nom', 'form-family-name', 'family-name', msg_req='Nom : veuillez indiquer votre nom de famille.', label_testid='form-family-name-label')}
            {fld('f-birth', 'Date de naissance', 'form-birthdate', 'bday', hint='(JJ.MM.AAAA)', pattern='^[0-9]{2}\\.[0-9]{2}\\.[0-9]{4}$', msg_req='Date de naissance : veuillez indiquer votre date de naissance.', msg_fmt='Date de naissance : utilisez le format JJ.MM.AAAA, p. ex. 14.03.1985.', review='Date de naissance')}
            {fld('f-email', 'E-mail', 'form-email', 'email', typ='email', kind='email', msg_req='E-mail : veuillez indiquer votre adresse e-mail.', msg_fmt='E-mail : l’adresse doit contenir un « @ », p. ex. marie.exemple@musterwil.example.')}
            {fld('f-tel', 'Téléphone', 'form-tel', 'tel', req=False, typ='tel', hint='(facultatif)')}
            <div class="field"><label for="f-copies">Nombre d’exemplaires</label><input id="f-copies" name="f-copies" type="number" min="1" max="5" value="1" data-review-label="Nombre d’exemplaires" data-testid="form-copies"></div>
          </div>
        </fieldset>
        <fieldset>
          <legend>Adresse de domicile</legend>
          <div class="form-grid-3">
            {fld('f-street', 'Rue et numéro', 'form-street', 'street-address', msg_req='Rue et numéro : veuillez indiquer votre adresse.')}
            {fld('f-plz', 'NPA', 'form-plz', 'postal-code', pattern='^[0-9]{4}$', extra=' inputmode="numeric"', msg_req='NPA : veuillez indiquer votre NPA, p. ex. 2500.', msg_fmt='NPA : le NPA doit comporter 4 chiffres, p. ex. 2500.')}
            {fld('f-city', 'Localité', 'form-city', 'address-level2', msg_req='Localité : veuillez indiquer votre localité.')}
          </div>
        </fieldset>
        <fieldset>
          <legend>Annoncer un changement d’adresse (facultatif)</legend>
          <div class="form-grid">
            {fld('f-new-street', 'Nouvelle rue et numéro', 'form-new-street', 'street-address', req=False)}
            {fld('f-move', 'Date du déménagement', 'form-move-date', None, req=False, hint='(JJ.MM.AAAA)', pattern='^[0-9]{2}\\.[0-9]{2}\\.[0-9]{4}$', msg_fmt='Date du déménagement : utilisez le format JJ.MM.AAAA, p. ex. 01.12.2026.')}
          </div>
        </fieldset>
        <div class="form-actions">
          <button type="button" class="btn btn-secondary" disabled data-testid="form-save-draft">Enregistrer le brouillon</button>
          <button type="submit" class="btn" data-testid="form-submit">Vérifier la commande</button>
        </div>
      </div>
      <section data-review data-testid="form-review" aria-labelledby="review-title" hidden>
        <h2 id="review-title" tabindex="-1">Vérifier votre commande</h2>
        <p>Veuillez contrôler vos données. Vous pouvez encore les modifier avant l’envoi.</p>
        <dl class="review-list" data-review-list></dl>
        <p class="fee">Montant facturé : CHF 20.– par exemplaire.</p>
        <div class="check"><input type="checkbox" id="f-confirm" data-confirm aria-describedby="f-confirm-error"><label for="f-confirm">Je confirme que les données sont exactes et j’accepte la facture de CHF 20.– par exemplaire.</label></div>
        <p class="field-error" id="f-confirm-error" data-confirm-error hidden>Veuillez cocher la case de confirmation pour passer la commande.</p>
        <div class="form-actions">
          <button type="button" class="btn btn-secondary" data-review-back>Modifier les données</button>
          <button type="submit" class="btn" data-testid="form-order-button">Commander</button>
        </div>
      </section>
    </form>
  </div>
  <div class="aside-col">
    <section class="box" aria-labelledby="more-services">
      <h2 id="more-services">Autres prestations</h2>
      <ul class="link-list">
        <li><a href="instructions.html">Annoncer un déménagement avec eDéménagement</a></li>
        <li><a href="calendrier-dechets.html">Calendrier des déchets et points de collecte</a></li>
        <li><a href="horaires.html">Horaires de l’administration</a></li>
      </ul>
    </section>
    <section class="box" aria-labelledby="questions">
      <h2 id="questions">Des questions ?</h2>
      <p>Le contrôle des habitants vous renseigne volontiers : téléphone <a href="tel:+41320001210">032 000 12 10</a>.</p>
    </section>
  </div>
</div>'''
    out['guichet-en-ligne.html'] = page(L, 'form', 'Guichet en ligne – Commune de Musterwil', main, crumbs=['Guichet en ligne'],
                                        scripts=('forms.js',), description='Commander une attestation de domicile et annoncer un changement d’adresse.')
    P = 'fr/guichet-en-ligne.html'
    R(P, 'form-error-summary', '3.3.1', 'trap', 'passed', 'Understanding 3.3.1 / G139: on submit the summary states the number of errors and lists each field with a description and a link to it.')
    R(P, 'form-plz-error', '3.3.1', 'trap', 'passed', 'Understanding 3.3.1: the field message names the field (NPA) and describes the problem in text.')
    R(P, 'form-plz-error', '3.3.3', 'trap', 'passed', 'Understanding 3.3.3: "Le NPA doit comporter 4 chiffres, p. ex. 2500" suggests how to correct the input.')
    R(P, 'residence-form', '3.3.4', 'trap', 'passed', 'Understanding 3.3.4 / G98: before the billed order is sent, a review step shows all data, allows changes (a button to go back and edit the data) and requires a confirmation checkbox.')
    R(P, 'form-email', '1.3.5', 'trap', 'passed', 'Understanding 1.3.5: autocomplete="email" matches the e-mail field.')
    R(P, 'form-street', '1.3.5', 'trap', 'passed', 'Understanding 1.3.5: autocomplete="street-address" matches the street field.')
    R(P, 'form-copies', '1.3.5', 'trap', 'inapplicable', 'Understanding 1.3.5: the number of copies is not information about the user.')
    R(P, 'form-given-name', '1.4.11', 'trap', 'passed', 'Understanding 1.4.11: input border #6b7780 on white is 4.6:1 (≥ 3:1).')
    R(P, 'form-family-name-label', '1.4.1', 'trap', 'passed', 'Understanding 1.4.1: required fields are marked with an asterisk explained in text, not by colour alone.')
    R(P, 'form-birthdate', '3.3.2', 'trap', 'passed', 'Understanding 3.3.2: a visible date-of-birth label with format hint "(JJ.MM.AAAA)" and required marker.')
    R(P, 'form-submit', '2.5.3', 'trap', 'passed', 'Understanding 2.5.3: the accessible name equals the visible label "Vérifier la commande".')
    R(P, 'form-submit', '2.4.3', 'trap', 'passed', 'Understanding 2.4.3: no positive tabindex; focus order follows the visual order.')

    # ------------------------------------------------------------------ fr/merci.html
    main = f'''<div class="container narrow">
  <ol class="progress-steps" aria-label="Étapes de la commande">
    <li><span class="step-num">1</span>Données</li>
    <li><span class="step-num">2</span>Vérification</li>
    <li class="current" aria-current="step"><span class="step-num">3</span>Confirmation</li>
  </ol>
  <h1>Merci pour votre commande</h1>
  <div class="status status-success" role="status" data-testid="order-status">{icon("check")}<p><strong>Commande transmise avec succès.</strong> Votre numéro de commande : MW-2026-04818.</p></div>
  <p>Vous recevrez l’attestation de domicile par la poste dans un délai de trois jours ouvrables, avec la facture de CHF 20.– par exemplaire. Une copie de vos données vous est envoyée par e-mail.</p>
  <p>Des questions sur votre commande ? Le contrôle des habitants est joignable au <a href="tel:+41320001210">032 000 12 10</a>.</p>
  <p class="button-row"><a class="btn" href="index.html">Retour à l’accueil</a> <a class="btn btn-secondary" href="guichet-en-ligne.html">Nouvelle commande</a></p>
</div>'''
    out['merci.html'] = page(L, 'thanks', 'Commande confirmée – Commune de Musterwil', main,
                             crumbs=[('Guichet en ligne', 'guichet-en-ligne.html'), 'Confirmation'])
    R('fr/merci.html', None, '2.4.5', 'set', 'passed', 'Set-level criterion (PROTOCOL.md: the label applies to the set of pages of this language version). The French set PASSES 2.4.5: every content page is reachable through the main navigation, the site map and the search; fr/merci.html is exempt as the result of a process (Understanding 2.4.5).', scope='set', deciding_page=None)
    R('fr/merci.html', 'order-status', '1.4.1', 'trap', 'passed', 'Understanding 1.4.1: status uses colour, icon and text.')

    # ------------------------------------------------------------------ fr/calendrier-dechets.html
    chart_alt = ('Diagramme en barres des déchets verts collectés en 2025, en tonnes par mois : janvier 6, février 7, mars 18, avril 31, mai 38, '
                 'juin 35, juillet 29, août 27, septembre 30, octobre 36, novembre 22, décembre 8 ; total 287 tonnes, maximum en mai.')
    main = f'''<div class="container page-head">
  <h1>Calendrier des déchets 2026</h1>
  <p class="lead">Dates de ramassage, points de collecte et taxes de la commune de Musterwil.</p>
</div>
<div class="container layout-main-aside">
  <div class="main-col">
    <p>Veuillez déposer les sacs à ordures et les conteneurs à déchets verts au bord de la route le jour du ramassage, <strong>avant 7 h</strong>. Les sacs taxés sont en vente au magasin du village, à la boulangerie de la place du village et à l’administration communale.</p>
    <h2 data-testid="waste-dates-title">Dates de ramassage 2026</h2>
    <p>Les dates de novembre en un coup d’œil :</p>
    {calendar('fr', letters=True)}
    <h2>Déchets verts : quantités collectées en 2025</h2>
    <p>La quantité de déchets verts varie fortement selon les saisons. En hiver, le ramassage n’a donc lieu que toutes les deux semaines.</p>
    <figure class="chart-figure"><img src="{A}img/chart-gruengut-fr.svg" alt="{chart_alt}" width="960" height="560" data-testid="waste-chart"></figure>
    <h2>Points de collecte</h2>
    <div class="table-wrap">
      <table class="data-table" data-testid="collection-points-table">
        <caption>Points de collecte et heures d’ouverture</caption>
        <thead><tr><th scope="col">Point de collecte</th><th scope="col">Déchets acceptés</th><th scope="col">Heures d’ouverture</th></tr></thead>
        <tbody>
          <tr><th scope="row">Voirie de Moosmatt</th><td>Déchets verts, encombrants, ferraille, appareils électriques</td><td>Me 13 h 30–17 h, sa 9 h–12 h</td></tr>
          <tr><th scope="row">Point de collecte de la gare</th><td>Verre, aluminium, fer-blanc</td><td>Lu–sa 7 h–20 h</td></tr>
          <tr><th scope="row">École de Moosmatt</th><td>Vêtements et chaussures</td><td>En tout temps (conteneur)</td></tr>
        </tbody>
      </table>
    </div>
    <h2>Taxes et règlement</h2>
    <p>La taxe de base s’élève à CHF 95.– par ménage et par an. Un sac de 35 litres coûte CHF 2.20.</p>
    <ul class="doc-list"><li><a href="{A}docs/abfallreglement-musterwil.pdf" hreflang="de" data-testid="regulation-pdf-link">{icon("file")}Règlement sur les déchets (PDF, {{PDF_KB}} Ko, en allemand)</a></li></ul>
  </div>
  <div class="aside-col">
    <section class="box" aria-labelledby="next-title">
      <h2 id="next-title">Prochains ramassages</h2>
      <ul class="link-list"><li>Mardi 20 octobre : ordures ménagères</li><li>Jeudi 22 octobre : déchets verts</li><li>Mercredi 28 octobre : papier</li></ul>
    </section>
  </div>
</div>'''
    out['calendrier-dechets.html'] = page(L, 'waste', 'Calendrier des déchets 2026 – Commune de Musterwil', main, crumbs=['Calendrier des déchets'])
    P = 'fr/calendrier-dechets.html'
    R(P, 'waste-chart', '1.1.1', 'trap', 'passed', 'Understanding 1.1.1: the chart alt gives the type, unit, all twelve values, the total and the peak.')
    R(P, 'waste-calendar', '1.4.1', 'trap', 'passed', 'Understanding 1.4.1: each collection day shows a letter (O, V, P, C) explained in the legend, plus hidden text, not colour alone.')
    R(P, 'waste-dates-title', '1.3.1', 'trap', 'passed', 'Understanding 1.3.1: the section title is a real <h2>.')
    R(P, 'main-nav', '3.2.3', 'set', 'passed', 'Set-level criterion (PROTOCOL.md: the label applies to the set of pages of this language version). The French set PASSES 3.2.3: the main navigation has the same order on every French page, including this one.', scope='set', deciding_page=None)
    R(P, 'regulation-pdf-link', '2.4.4', 'trap', 'passed', 'Understanding 2.4.4: link text names the document, its format, size and language.')

    # ------------------------------------------------------------------ fr/horaires.html
    lib = hours_grid([('Lundi', 'fermé'), ('Mardi', '15 h–18 h'), ('Mercredi', '14 h–18 h'),
                      ('Jeudi', '15 h–19 h'), ('Vendredi', 'fermé'), ('Samedi', '9 h 30–12 h')], wrong_order=False)

    def faq(i, q, a):
        return (f'<div class="acc-item"><h3 class="sr-heading"><button type="button" class="acc-toggle" aria-expanded="false" aria-controls="faq-panel-{i}" data-testid="faq-toggle-{i}">{q}</button></h3>'
                f'<div class="acc-panel" id="faq-panel-{i}" hidden><p>{a}</p></div></div>')
    main = f'''<div class="container page-head">
  <h1>Horaires d’ouverture</h1>
  <p class="lead">Horaires de l’administration communale, de la voirie et de la bibliothèque communale.</p>
</div>
<div class="container layout-main-aside">
  <div class="main-col">
    <section aria-labelledby="h-admin">
      <h2 id="h-admin" data-testid="admin-heading">Administration communale</h2>
      <div class="table-wrap">
        <table class="data-table" data-testid="hours-admin">
          <caption>Heures d’ouverture des guichets dès le 1<sup>er</sup> novembre 2026</caption>
          <thead><tr><th scope="col">Jour</th><th scope="col">Matin</th><th scope="col">Après-midi</th></tr></thead>
          <tbody>
            <tr><th scope="row">Lundi</th><td>8 h–11 h 30</td><td>14 h–17 h</td></tr>
            <tr><th scope="row">Mardi</th><td>8 h–11 h 30</td><td>14 h–17 h</td></tr>
            <tr><th scope="row">Mercredi</th><td>8 h–11 h 30</td><td>fermé</td></tr>
            <tr><th scope="row">Jeudi</th><td>8 h–11 h 30</td><td>14 h–18 h 30</td></tr>
            <tr><th scope="row">Vendredi</th><td>8 h–11 h 30</td><td>14 h–16 h</td></tr>
          </tbody>
        </table>
      </div>
    </section>
    <section aria-labelledby="h-voirie">
      <h2 id="h-voirie" data-testid="werkhof-heading">Voirie et déchetterie de Moosmatt</h2>
      <div class="table-wrap">
        <table class="data-table" data-testid="hours-werkhof">
          <caption>Heures d’ouverture de la voirie, Industriestrasse 8</caption>
          <thead><tr><th scope="col">Jour</th><th scope="col">Heures</th></tr></thead>
          <tbody><tr><th scope="row">Mercredi</th><td>13 h 30–17 h</td></tr><tr><th scope="row">Samedi</th><td>9 h–12 h</td></tr></tbody>
        </table>
      </div>
    </section>
    <section id="bibliotheque" aria-labelledby="h-lib">
      <h2 id="h-lib">Bibliothèque communale</h2>
      <p>Bibliothèque à la Bahnhofstrasse 12, nouveaux horaires dès le 2 novembre 2026 :</p>
      {lib}
    </section>
    <section id="situation" aria-labelledby="h-loc">
      <h2 id="h-loc">Situation et accès</h2>
      <div class="loc-grid">
        <img src="{A}img/map-standort.svg" alt="Plan de situation : l’administration communale se trouve à la Dorfstrasse 1, à environ 100 mètres de l’arrêt de bus Musterwil Dorf." width="800" height="450">
        <div><p>Administration communale de Musterwil<br>Dorfstrasse 1<br>9999 Musterwil</p><p>Bus ligne 12 jusqu’à l’arrêt « Musterwil Dorf ». Quatre places de stationnement pour les visiteurs se trouvent derrière la maison communale.</p></div>
      </div>
    </section>
    <section aria-labelledby="h-faq">
      <h2 id="h-faq">Questions fréquentes</h2>
      <div class="accordion">
        {faq(1, 'L’administration est-elle ouverte entre Noël et Nouvel An ?', 'L’administration est fermée du 24 décembre 2026 au 3 janvier 2027 inclus. En cas de décès, l’office des inhumations est joignable au 032 000 12 99.')}
        {faq(2, 'Puis-je venir en dehors des heures d’ouverture ?', 'Oui, sur rendez-vous téléphonique.')}
        {faq(3, 'Où puis-je garer mon vélo ?', 'Un abri à vélos couvert de douze places se trouve devant l’entrée principale.')}
      </div>
    </section>
  </div>
  <div class="aside-col">
    <section class="box" aria-labelledby="phone-hours"><h2 id="phone-hours">Heures téléphoniques</h2><p>Lu–ve 8 h–11 h 30 et 14 h–16 h<br>Téléphone <a href="tel:+41320001234">032 000 12 34</a></p></section>
  </div>
</div>'''
    out['horaires.html'] = page(L, 'hours', 'Horaires d’ouverture – Commune de Musterwil', main, crumbs=['Horaires'], scripts=('accordion.js',))
    P = 'fr/horaires.html'
    R(P, None, '2.4.2', 'trap', 'passed', 'Understanding 2.4.2: title "Horaires d’ouverture – Commune de Musterwil" describes topic and site.')
    R(P, 'hours-library', '1.3.2', 'trap', 'passed', 'Understanding 1.3.2: each day is directly followed by its hours in the DOM; reading order matches the visual order.')
    R(P, 'hours-werkhof', '1.3.1', 'trap', 'passed', 'Understanding 1.3.1: table with caption and th scope.')
    R(P, 'werkhof-heading', '2.4.6', 'trap', 'passed', 'Understanding 2.4.6: heading "Voirie et déchetterie de Moosmatt" describes the section.')
    for i in (1, 2, 3):
        R(P, f'faq-toggle-{i}', '4.1.2', 'trap', 'passed', 'Understanding 4.1.2: FAQ toggle is a native <button> with aria-expanded and aria-controls.')

    # ------------------------------------------------------------------ fr/bilingue.html
    main = '''<div class="container page-head">
  <h1>Avis officiels · <span lang="de-CH">Amtliche Mitteilungen</span></h1>
  <p class="lead">Musterwil est une commune bilingue. Les avis officiels du Conseil communal paraissent donc en français et en allemand.</p>
</div>
<div class="container">
  <article class="bi-notice">
    <header class="bi-head">
      <p class="bi-date"><time datetime="2026-10-09">9 octobre 2026</time></p>
      <h2>Assemblée communale du 24 novembre 2026 · <span lang="de-CH">Gemeindeversammlung vom 24. November 2026</span></h2>
    </header>
    <div class="bi-grid">
      <div class="bi-col" lang="fr-CH" data-testid="notice-col-fr">
        <p class="bi-lang">Français</p>
        <p>Les ayants droit au vote sont convoqués à l’assemblée communale ordinaire : mardi 24 novembre 2026, à 19 h 30, à la salle polyvalente.</p>
        <ol><li>Budget 2027 et fixation de la quotité d’impôt</li><li>Assainissement de l’école de Moosmatt : crédit d’engagement de 2,4 millions de francs</li><li>Révision partielle du règlement sur les déchets</li><li>Divers</li></ol>
      </div>
      <div class="bi-col" lang="de-CH" data-testid="notice-col-de">
        <p class="bi-lang">Deutsch</p>
        <p>Die Stimmberechtigten werden zur ordentlichen Gemeindeversammlung eingeladen: Dienstag, 24. November 2026, 19.30 Uhr, Mehrzweckhalle.</p>
        <ol><li>Budget 2027 und Festsetzung der Steueranlage</li><li>Sanierung Schulhaus Moosmatt: Verpflichtungskredit von CHF 2,4 Mio.</li><li>Teilrevision des Abfallreglements</li><li>Verschiedenes</li></ol>
      </div>
    </div>
  </article>
  <article class="bi-notice">
    <header class="bi-head">
      <p class="bi-date"><time datetime="2026-10-07">7 octobre 2026</time></p>
      <h2>Budget 2027 adopté · <span lang="de-CH">Budget 2027 verabschiedet</span></h2>
    </header>
    <div class="bi-grid">
      <div class="bi-col" lang="fr-CH">
        <p class="bi-lang">Français</p>
        <p data-testid="budget-fr-para">Le Conseil communal a adopté le budget 2027. Avec des charges de 18,4 millions de francs, il prévoit un excédent de 210 000 francs ; la quotité d’impôt reste inchangée. Der ausführliche Bericht kann kostenlos bei der Gemeindeverwaltung bezogen werden. L’assemblée communale du 24 novembre 2026 se prononcera sur le budget.</p>
      </div>
      <div class="bi-col" lang="de-CH">
        <p class="bi-lang">Deutsch</p>
        <p>Der Gemeinderat hat das Budget 2027 verabschiedet. Es rechnet bei einem Aufwand von 18,4 Millionen Franken mit einem Überschuss von 210 000 Franken; die Steueranlage bleibt unverändert. Der ausführliche Bericht kann kostenlos bei der Gemeindeverwaltung bezogen werden.</p>
      </div>
    </div>
  </article>
</div>'''
    out['bilingue.html'] = page(L, 'bilingual', 'Avis officiels – Commune de Musterwil', main, crumbs=['Avis officiels'])
    P = 'fr/bilingue.html'
    R(P, 'notice-col-de', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2 / H58: the German column is marked lang="de-CH".')
    R(P, 'notice-col-fr', '3.1.2', 'trap', 'passed', 'Understanding 3.1.2: the French column is marked lang="fr-CH" (same as the page).')
    R(P, 'budget-fr-para', '3.1.2', 'issue', 'failed', 'Understanding 3.1.2: the German sentence "Der ausführliche Bericht kann …" sits inside a French paragraph without lang="de".')

    # ------------------------------------------------------------------ fr/loisirs.html  (carousel WITH pause)
    main = f'''<div class="container page-head">
  <h1>Loisirs et tourisme</h1>
  <p class="lead">Bord du lac, forêt de l’Aarenwald et vie villageoise animée : découvrez Musterwil en toute saison.</p>
</div>
<div class="container">
  <div class="carousel" role="region" aria-label="Images de Musterwil" data-carousel data-interval="5000" data-testid="carousel">
    <div class="carousel-track">
      <figure class="slide is-active"><img src="{A}img/slide-seeufer.svg" alt="Ponton et voilier sur le lac dans la lumière du soir" width="1200" height="500"><figcaption>Bord du lac : plage, ponton et promenade</figcaption></figure>
      <figure class="slide"><img src="{A}img/slide-wald.svg" alt="Chemin forestier avec panneau d’information dans l’Aarenwald en automne" width="1200" height="500"><figcaption>Sentier didactique de l’Aarenwald – 4,5 km, idéal pour les familles</figcaption></figure>
      <figure class="slide"><img src="{A}img/slide-dorfplatz.svg" alt="Place du village avec fontaine et stands de marché" width="1200" height="500"><figcaption>Marché sur la place du village – prochaine date : 24 octobre</figcaption></figure>
      <figure class="slide"><img src="{A}img/slide-schiff.svg" alt="Bateau de ligne sur le lac devant des collines boisées" width="1200" height="500"><figcaption>Tour du lac en bateau : tous les jours d’avril à octobre</figcaption></figure>
    </div>
    <button type="button" class="carousel-ctrl carousel-prev" aria-label="Image précédente" data-carousel-prev data-testid="carousel-prev">{icon("left")}</button>
    <button type="button" class="carousel-ctrl carousel-next" aria-label="Image suivante" data-carousel-next data-testid="carousel-next">{icon("right")}</button>
    <button type="button" class="carousel-pause" data-carousel-pause data-state="running" data-label-pause="Pause" data-label-play="Lecture" data-testid="carousel-pause"><span data-icon-pause>{icon("pause")}</span><span data-icon-play hidden>{icon("play")}</span><span data-label>Pause</span></button>
    <div class="carousel-dots" aria-hidden="true"><span class="carousel-dot is-active"></span><span class="carousel-dot"></span><span class="carousel-dot"></span><span class="carousel-dot"></span></div>
  </div>

  <section class="section" aria-labelledby="offers-title">
    <h2 id="offers-title">Offres à Musterwil</h2>
    <div class="filter-bar">
      <label for="offer-filter">Filtrer les offres</label>
      <select id="offer-filter" data-filter-target="offer-list" data-filter-status="offer-count" data-testid="activity-filter">
        <option value="all">Toutes les offres</option><option value="sport">Sport et baignade</option><option value="kultur">Culture</option><option value="natur">Nature</option><option value="kurse">Cours</option>
      </select>
      <p id="offer-count" class="filter-count" role="status" data-template="{{n}} offres affichées"></p>
    </div>
    <ul class="offer-grid" id="offer-list">
      <li data-category="sport"><p class="offer-tag">Sport et baignade</p><h3>Plage du bord du lac</h3><p>Pelouse, plongeoir et pataugeoire. Ouverte de mi-mai à mi-septembre, de 9 h à 20 h par beau temps.</p></li>
      <li data-category="sport"><p class="offer-tag">Sport et baignade</p><h3>Parcours Vita de l’Aarenwald</h3><p>2,8 km et 15 postes. Départ au parking de la maison forestière.</p></li>
      <li data-category="kultur"><p class="offer-tag">Culture</p><h3>Cinéma en plein air au bord du lac</h3><p>Chaque vendredi en juillet et en août, la société culturelle projette un film à la belle étoile. Entrée libre, collecte.</p></li>
      <li data-category="kultur"><p class="offer-tag">Culture</p><h3>Musée du village</h3><p>Artisanat et histoire locale, ouvert le premier dimanche du mois de 14 h à 17 h.</p></li>
      <li data-category="natur"><p class="offer-tag">Nature</p><h3>Sentier didactique</h3><p>4,5 km et 20 panneaux sur les arbres, les animaux et les champignons. Accessible aux poussettes.</p></li>
      <li data-category="kurse"><p class="offer-tag">Cours</p><h3>Atelier de réparation de vélos</h3><p>L’équipe de la voirie partage son savoir-faire : réparer une chambre à air, régler les freins, huiler la chaîne. Samedi 7 novembre 2026, de 9 h à 12 h.</p></li>
    </ul>
  </section>
</div>'''
    out['loisirs.html'] = page(L, 'leisure', 'Loisirs et tourisme – Commune de Musterwil', main, crumbs=['Loisirs et tourisme'], scripts=('carousel.js', 'filter.js'))
    P = 'fr/loisirs.html'
    R(P, 'carousel', '2.2.2', 'trap', 'passed', 'Understanding 2.2.2 / G4: the auto-advancing carousel has a visible, working "Pause" button (label switches to "Lecture").')
    R(P, 'carousel-pause', '4.1.2', 'trap', 'passed', 'Understanding 4.1.2: native <button> with visible text label.')
    R(P, 'carousel-next', '4.1.2', 'trap', 'passed', 'Understanding 4.1.2: native <button> with aria-label "Image suivante".')
    R(P, 'carousel-next', '2.5.3', 'trap', 'inapplicable', 'Understanding 2.5.3: icon-only button without visible text label.')
    R(P, 'activity-filter', '3.2.2', 'trap', 'passed', 'Understanding 3.2.2: the select filters the list on the same page; no change of context.')

    # ------------------------------------------------------------------ fr/instructions.html
    main = f'''<div class="container page-head">
  <h1>Annoncer un déménagement en ligne</h1>
  <p class="lead">Avec eDéménagement, vous annoncez votre déménagement en Suisse en ligne – à l’ancienne et à la nouvelle commune en même temps.</p>
</div>
<div class="container guide-layout">
  <ol class="steps">
    <li><h2>Ouvrir le formulaire</h2><p>Ouvrez le guichet en ligne et choisissez « Annoncer un déménagement ». Préparez votre nouvelle adresse et la date du déménagement.</p></li>
    <li><h2>Saisir les données personnelles</h2><p data-testid="instruction-table-ref">Indiquez votre nom, votre date de naissance et votre adresse actuelle. Les documents nécessaires figurent dans le tableau ci-dessous.</p></li>
    <li><h2>Passer à la nouvelle adresse</h2><p data-testid="instruction-next-button">Cliquez en bas à droite sur « Suivant ».</p></li>
    <li><h2>Confirmer les données</h2><p data-testid="instruction-green-button">Vérifiez votre nouvelle adresse. Si tout est correct, cliquez sur le bouton vert à droite.</p></li>
    <li><h2>Recevoir la confirmation</h2><p>Vous recevez immédiatement une confirmation par e-mail. La commune vous contacte s’il manque des documents.</p></li>
  </ol>
  <aside class="mock-wrap" aria-labelledby="mock-title">
    <h2 id="mock-title" class="mock-heading">Vue d’exercice</h2>
    <p class="mock-intro">Voici à quoi ressemble eDéménagement. Essayez les boutons : aucune donnée n’est transmise.</p>
    <div class="mock-window">
      <div class="mock-bar"><span></span><span></span><span></span><p>eDéménagement – étape 2 sur 4</p></div>
      <div class="mock-body">
        <p class="mock-label">Nom</p><p class="mock-value">Lukas Muster</p>
        <p class="mock-label">Adresse actuelle</p><p class="mock-value">Lindenweg 3, 9998 Beispielhausen</p>
        <div class="mock-actions"><button type="button" class="btn" data-practice="practice-status" data-practice-msg="Exercice : vous êtes maintenant à l’étape 3." data-testid="practice-next-button">Suivant</button></div>
      </div>
    </div>
    <div class="mock-window">
      <div class="mock-bar"><span></span><span></span><span></span><p>eDéménagement – étape 3 sur 4</p></div>
      <div class="mock-body mock-confirm">
        <div><p class="mock-label">Nouvelle adresse</p><p class="mock-value">Seeweg 7, 9999 Musterwil</p><p class="mock-label">Date d’arrivée</p><p class="mock-value">1<sup>er</sup> décembre 2026</p></div>
        <button type="button" class="round-go" aria-label="Continuer" data-practice="practice-status" data-practice-msg="Exercice : vos données seraient maintenant confirmées." data-testid="practice-confirm-button">{icon("arrow")}</button>
      </div>
    </div>
    <p id="practice-status" class="practice-status" role="status"></p>
  </aside>
</div>
<div class="container section">
  <div class="table-wrap">
    <table class="data-table" data-testid="documents-table">
      <caption>Documents nécessaires</caption>
      <thead><tr><th scope="col">Votre situation</th><th scope="col">Documents</th></tr></thead>
      <tbody>
        <tr><th scope="row">Ressortissants suisses</th><td>Acte d’origine (uniquement en cas d’arrivée d’une autre commune)</td></tr>
        <tr><th scope="row">Ressortissants étrangers</th><td>Permis de séjour et passeport ou carte d’identité valable</td></tr>
        <tr><th scope="row">Familles</th><td>Certificat de famille ou livret de famille</td></tr>
        <tr><th scope="row">Locataires</th><td>Contrat de bail indiquant le numéro du logement</td></tr>
      </tbody>
    </table>
  </div>
</div>'''
    out['instructions.html'] = page(L, 'guide', 'Instructions eDéménagement – Commune de Musterwil', main, crumbs=['Instructions eDéménagement'])
    P = 'fr/instructions.html'
    R(P, 'instruction-green-button', '1.3.3', 'issue', 'failed', 'Understanding 1.3.3: "cliquez sur le bouton vert à droite" relies only on colour and position; the button shows only an arrow (name "Continuer" not mentioned).')
    R(P, 'instruction-next-button', '1.3.3', 'trap', 'passed', 'Understanding 1.3.3: position plus the visible button text « Suivant ».')
    R(P, 'instruction-table-ref', '1.3.3', 'trap', 'passed', 'Understanding 1.3.3: "tableau ci-dessous" points to the only table, which has the caption "Documents nécessaires".')
    R(P, 'practice-confirm-button', '2.5.3', 'trap', 'inapplicable', 'Understanding 2.5.3: icon-only button with aria-label, no visible text label.')

    # ------------------------------------------------------------------ fr/plan-du-site.html
    main = '''<div class="container page-head">
  <h1>Plan du site</h1>
  <p class="lead">Toutes les pages du site de Musterwil en un coup d’œil.</p>
</div>
<div class="container sitemap-grid">
  <section aria-labelledby="sm-admin"><h2 id="sm-admin">Administration</h2>
    <ul><li><a href="index.html">Accueil</a></li><li><a href="guichet-en-ligne.html">Guichet en ligne</a></li><li><a href="horaires.html">Horaires d’ouverture</a></li><li><a href="bilingue.html">Avis officiels</a></li></ul></section>
  <section aria-labelledby="sm-living"><h2 id="sm-living">Habiter et environnement</h2>
    <ul><li><a href="instructions.html">Instructions eDéménagement</a></li><li><a href="calendrier-dechets.html">Calendrier des déchets 2026</a></li></ul></section>
  <section aria-labelledby="sm-leisure"><h2 id="sm-leisure">Loisirs</h2>
    <ul><li><a href="loisirs.html">Loisirs et tourisme</a></li></ul></section>
  <section aria-labelledby="sm-service"><h2 id="sm-service">Services</h2>
    <ul><li><a href="recherche.html">Recherche</a></li><li><a href="plan-du-site.html">Plan du site</a></li><li><a href="accessibilite.html">Déclaration d’accessibilité</a></li></ul></section>
  <section aria-labelledby="sm-lang"><h2 id="sm-lang">Autres langues</h2>
    <ul><li><a href="../sitemap.html" lang="de-CH" hreflang="de">Sitemap auf Deutsch</a></li><li><a href="../it/mappa-del-sito.html" lang="it-CH" hreflang="it">Mappa del sito in italiano</a></li></ul></section>
</div>'''
    out['plan-du-site.html'] = page(L, 'sitemap', 'Plan du site – Commune de Musterwil', main, crumbs=['Plan du site'])
    R('fr/plan-du-site.html', 'header-search-button', '3.2.4', 'set', 'passed', 'Set-level criterion (PROTOCOL.md: the label applies to the set of pages of this language version). The French set PASSES 3.2.4: the search button reads «Recherche» with a magnifier on every French page, including the site map.', scope='set', deciding_page=None)

    # ------------------------------------------------------------------ fr/recherche.html
    entries = [
        dict(title='Accueil', url='index.html', text='Actualités, manifestations et avis de la commune de Musterwil.', keywords='actualites nouvelles'),
        dict(title='Guichet en ligne', url='guichet-en-ligne.html', text='Commander une attestation de domicile et annoncer un changement d’adresse.', keywords='formulaire commande attestation domicile adresse'),
        dict(title='Instructions eDéménagement', url='instructions.html', text='Annoncer un déménagement en ligne : instructions pas à pas et documents nécessaires.', keywords='demenagement arrivee depart adresse'),
        dict(title='Horaires d’ouverture', url='horaires.html', text='Horaires de l’administration, de la voirie et de la bibliothèque ; situation et accès.', keywords='guichet bibliotheque voirie telephone'),
        dict(title='Calendrier des déchets 2026', url='calendrier-dechets.html', text='Dates de ramassage des ordures, déchets verts, papier et carton ; points de collecte et taxes.', keywords='dechets ordures dechets verts papier carton'),
        dict(title='Loisirs et tourisme', url='loisirs.html', text='Plage, sentier didactique, culture et cours à Musterwil.', keywords='tourisme excursion baignade culture'),
        dict(title='Avis officiels', url='bilingue.html', text='Avis bilingues du Conseil communal : assemblée communale, budget 2027.', keywords='conseil communal budget assemblee'),
        dict(title='Plan du site', url='plan-du-site.html', text='Toutes les pages du site en un coup d’œil.', keywords='apercu pages'),
        dict(title='Déclaration d’accessibilité', url='accessibilite.html', text='État de l’accessibilité de ce site et formulaire de contact.', keywords='accessibilite feedback'),
    ]
    main = f'''<div class="container page-head"><h1>Recherche</h1></div>
<div class="container narrow">
  <form class="search-page" role="search" action="recherche.html" method="get" data-search-form>
    <label for="search-q">Terme de recherche</label>
    <div class="search-field"><input id="search-q" name="q" type="search" autocomplete="off"><button type="submit" class="search-go search-go-strong" aria-label="Recherche" data-testid="search-page-button">{icon("search")}</button></div>
  </form>
  <p class="search-status" role="status" data-search-status data-msg-empty="Saisissez un terme de recherche, par exemple « déchets » ou « déménagement »." data-msg-count="{{n}} résultat(s) pour « {{q}} »" data-msg-none="Aucun résultat pour « {{q}} ». Essayez un autre terme ou consultez le plan du site."></p>
  <ol class="search-results" data-search-results></ol>
</div>
{search_index(entries)}'''
    out['recherche.html'] = page(L, 'search', 'Recherche – Commune de Musterwil', main, crumbs=['Recherche'], scripts=('search.js',))
    R('fr/recherche.html', 'search-page-button', '1.4.11', 'trap', 'passed', 'Understanding 1.4.11: white icon on a dark teal button (#0e5a63), well above 3:1.')
    R('fr/recherche.html', 'search-page-button', '2.5.3', 'trap', 'inapplicable', 'Understanding 2.5.3: icon-only button without visible text.')

    # ------------------------------------------------------------------ fr/accessibilite.html
    main = '''<div class="container page-head"><h1>Déclaration d’accessibilité</h1></div>
<div class="container with-sidebar">
  <div class="content">
    <p>La commune de Musterwil s’efforce de rendre son site musterwil.example accessible conformément aux Web Content Accessibility Guidelines (WCAG) 2.1, niveau AA, et à la norme eCH-0059.</p>
    <h2>État de conformité</h2>
    <p>Ce site est <strong>partiellement conforme</strong> aux WCAG 2.1, niveau AA. Les contenus énumérés ci-dessous ne sont pas encore accessibles.</p>
    <h2>Contenus non accessibles</h2>
    <ul><li>Certains anciens documents PDF des archives (avant 2022) ne sont pas entièrement accessibles.</li><li>Certaines images d’anciens articles n’ont pas de texte alternatif pertinent.</li><li>Les enregistrements de l’assemblée communale n’ont pas encore de sous-titres.</li></ul>
    <h2>Établissement de cette déclaration</h2>
    <p>Cette déclaration a été établie le 3 mars 2025 sur la base d’une auto-évaluation de l’administration communale.</p>
    <h2>Retour d’information</h2>
    <p>Vous avez constaté un problème d’accessibilité ? Merci de nous le signaler au moyen du formulaire suivant.</p>
    <form class="form-card form-std" action="accessibilite.html" method="get" data-feedback-form>
      <div class="form-grid">
        <div class="field"><label for="fb-name">Votre nom</label><input id="fb-name" type="text" autocomplete="name"></div>
        <div class="field"><label for="fb-email">Votre adresse e-mail</label><input id="fb-email" type="email" autocomplete="email"></div>
        <div class="field field-full"><label for="fb-msg">Votre message</label><textarea id="fb-msg" rows="5"></textarea></div>
      </div>
      <div class="form-actions"><button type="submit" class="btn" data-testid="feedback-submit">Envoyer</button></div>
      <p class="feedback-status" role="status" data-feedback-status data-msg="Merci pour votre message. Nous vous répondrons dans un délai de dix jours ouvrables." hidden></p>
    </form>
  </div>
  <nav class="side" aria-labelledby="related-title" data-testid="related-sidebar">
    <h2 id="related-title" class="side-title">Pages liées</h2>
    <ul><li><a href="plan-du-site.html">Plan du site</a></li><li><a href="recherche.html">Recherche</a></li><li><a href="guichet-en-ligne.html">Guichet en ligne</a></li></ul>
  </nav>
</div>'''
    out['accessibilite.html'] = page(L, 'a11y', 'Déclaration d’accessibilité – Commune de Musterwil', main, crumbs=['Accessibilité'])
    R('fr/accessibilite.html', 'feedback-submit', '4.1.2', 'trap', 'passed', 'Understanding 4.1.2: the feedback form uses a native submit <button>.')

    return out
