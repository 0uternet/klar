"""Shared page chrome for the Musterwil demo site: language config, header, nav, footer, icons."""

FILES = {
    'home': ('index.html', 'index.html', 'index.html'),
    'form': ('online-schalter.html', 'guichet-en-ligne.html', 'sportello-online.html'),
    'thanks': ('danke.html', 'merci.html', 'grazie.html'),
    'waste': ('abfallkalender.html', 'calendrier-dechets.html', 'calendario-rifiuti.html'),
    'hours': ('oeffnungszeiten.html', 'horaires.html', 'orari.html'),
    'bilingual': ('zweisprachig.html', 'bilingue.html', 'bilingue.html'),
    'leisure': ('freizeit.html', 'loisirs.html', 'tempo-libero.html'),
    'guide': ('anleitung.html', 'instructions.html', 'istruzioni.html'),
    'sitemap': ('sitemap.html', 'plan-du-site.html', 'mappa-del-sito.html'),
    'search': ('suche.html', 'recherche.html', 'ricerca.html'),
    'a11y': ('barrierefreiheit.html', 'accessibilite.html', 'accessibilita.html'),
    'velo': ('velo-aktion.html', None, None),
}
IDX = {'de': 0, 'fr': 1, 'it': 2}
CODES = {'de': 'de-CH', 'fr': 'fr-CH', 'it': 'it-CH'}


def fname(lang, key):
    return FILES[key][IDX[lang]]


def rel(from_lang, to_lang, key):
    fn = fname(to_lang, key) or 'index.html'
    if from_lang == to_lang:
        return fn
    if from_lang == 'de':
        return f'{to_lang}/{fn}'
    if to_lang == 'de':
        return f'../{fn}'
    return f'../{to_lang}/{fn}'


def page_path(lang, key):
    fn = fname(lang, key)
    return fn if lang == 'de' else f'{lang}/{fn}'


def asset(lang):
    return 'assets/' if lang == 'de' else '../assets/'


ICONS = {
    'search': '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
    'arrow': '<path d="M5 12h14M13 6l6 6-6 6"/>',
    'printer': '<path d="M6 9V3h12v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M6 14h12v7H6z"/>',
    'megaphone': '<path d="M3 11v2a1 1 0 0 0 1 1h3l6 4V6L7 10H4a1 1 0 0 0-1 1z"/><path d="M17 8a5 5 0 0 1 0 8"/>',
    'monitor': '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    'box': '<path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 7v10l9 4 9-4V7"/><path d="M12 11v10"/>',
    'calendar': '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'users': '<circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0"/><circle cx="17" cy="9" r="2.5"/><path d="M15.5 14.5A5 5 0 0 1 21 19"/>',
    'check': '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.5 2.5L16 9.5"/>',
    'left': '<path d="M15 6l-6 6 6 6"/>',
    'right': '<path d="M9 6l6 6-6 6"/>',
    'pause': '<path d="M9 5v14M15 5v14"/>',
    'play': '<path d="M7 5l12 7-12 7z"/>',
    'menu': '<path d="M4 7h16M4 12h16M4 17h16"/>',
    'file': '<path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8z"/><path d="M14 3v5h5"/>',
}


def icon(name, extra=''):
    e = f' {extra}' if extra else ''
    return (f'<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"{e}>{ICONS[name]}</svg>')


S = {
    'de': dict(
        skip='Zum Inhalt springen', note='Gemeinde Musterwil · Region Aarenwald', lang_label='Sprache',
        search_label='Suchbegriff', search_ph='Suchbegriff eingeben', search_btn='Suche', menu='Menü',
        nav_label='Hauptnavigation', crumb_label='Brotkrümelnavigation', home='Startseite', print='Drucken',
        logo_alt='Gemeinde Musterwil – Startseite', site='Gemeinde Musterwil',
        f_admin='Gemeindeverwaltung Musterwil', f_street='Dorfstrasse 1', f_city='9999 Musterwil', f_phone='Telefon',
        f_hours_title='Schalteröffnungszeiten',
        f_hours='Mo–Fr 08.00–11.30 Uhr<br>Mo, Di 14.00–17.00 Uhr<br>Do 14.00–18.30 Uhr<br>Fr 14.00–16.00 Uhr',
        f_hours_link='Alle Öffnungszeiten', f_service='Service',
        f_links=[('form', 'Online-Schalter'), ('sitemap', 'Sitemap'), ('search', 'Suche'), ('a11y', 'Barrierefreiheit')],
        f_copy='© 2026 Gemeinde Musterwil',
        f_note='Musterwil ist eine fiktive Gemeinde. Alle Namen, Adressen und Zahlen auf dieser Demonstrationswebsite sind erfunden.',
        nav=[('home', 'Startseite'), ('form', 'Online-Schalter'), ('guide', 'eUmzug'), ('hours', 'Öffnungszeiten'),
             ('waste', 'Abfallkalender'), ('leisure', 'Freizeit'), ('bilingual', 'Mitteilungen')],
    ),
    'fr': dict(
        skip='Aller au contenu', note='Commune de Musterwil · Région Aarenwald', lang_label='Langue',
        search_label='Terme de recherche', search_ph='Saisir un terme de recherche', search_btn='Recherche', menu='Menu',
        nav_label='Navigation principale', crumb_label="Fil d'Ariane", home='Accueil', print='Imprimer',
        logo_alt='Commune de Musterwil – Accueil', site='Commune de Musterwil',
        f_admin='Administration communale de Musterwil', f_street='Dorfstrasse 1', f_city='9999 Musterwil', f_phone='Téléphone',
        f_hours_title="Heures d'ouverture des guichets",
        f_hours='Lu–ve 8 h 00–11 h 30<br>Lu, ma 14 h 00–17 h 00<br>Je 14 h 00–18 h 30<br>Ve 14 h 00–16 h 00',
        f_hours_link='Tous les horaires', f_service='Services',
        f_links=[('form', 'Guichet en ligne'), ('sitemap', 'Plan du site'), ('search', 'Recherche'), ('a11y', 'Accessibilité')],
        f_copy='© 2026 Commune de Musterwil',
        f_note='Musterwil est une commune fictive. Les noms, adresses et chiffres de ce site de démonstration sont inventés.',
        nav=[('home', 'Accueil'), ('form', 'Guichet en ligne'), ('guide', 'eDéménagement'), ('hours', 'Horaires'),
             ('waste', 'Déchets'), ('leisure', 'Loisirs'), ('bilingual', 'Avis officiels')],
    ),
    'it': dict(
        skip='Vai al contenuto', note='Comune di Musterwil · Regione Aarenwald', lang_label='Lingua',
        search_label='Termine di ricerca', search_ph='Inserire un termine di ricerca', search_btn='Cerca', menu='Menu',
        nav_label='Navigazione principale', crumb_label='Percorso di navigazione', home='Pagina iniziale', print='Stampa',
        logo_alt='Comune di Musterwil – Pagina iniziale', site='Comune di Musterwil',
        f_admin='Amministrazione comunale di Musterwil', f_street='Dorfstrasse 1', f_city='9999 Musterwil', f_phone='Telefono',
        f_hours_title='Orari degli sportelli',
        f_hours='Lu–ve 08.00–11.30<br>Lu, ma 14.00–17.00<br>Gio 14.00–18.30<br>Ve 14.00–16.00',
        f_hours_link='Tutti gli orari', f_service='Servizi',
        f_links=[('form', 'Sportello online'), ('sitemap', 'Mappa del sito'), ('search', 'Ricerca'), ('a11y', 'Accessibilità')],
        f_copy='© 2026 Comune di Musterwil',
        f_note='Musterwil è un comune fittizio. Nomi, indirizzi e cifre di questo sito dimostrativo sono inventati.',
        nav=[('home', 'Pagina iniziale'), ('form', 'Sportello online'), ('guide', 'eTrasloco'), ('hours', 'Orari'),
             ('waste', 'Rifiuti'), ('leisure', 'Tempo libero'), ('bilingual', 'Avvisi')],
    ),
}


def lang_switch(lang, key):
    items = []
    for code, label in (('de', 'DE'), ('fr', 'FR'), ('it', 'IT')):
        target = key if fname(code, key) else 'home'
        cur = ' aria-current="true"' if code == lang else ''
        items.append(f'<li><a href="{rel(lang, code, target)}" lang="{code}" hreflang="{code}"{cur}>{label}</a></li>')
    return (f'<nav class="lang-switch" aria-label="{S[lang]["lang_label"]}" data-testid="lang-switch">'
            f'<ul>{"".join(items)}</ul></nav>')


def header(lang, key, nav_order=None, search_variant=None):
    s = S[lang]
    a = asset(lang)
    if search_variant == 'find':
        btn = f'<button type="submit" class="search-btn" data-testid="header-search-button">{icon("arrow")}<span>Finden</span></button>'
    else:
        btn = f'<button type="submit" class="search-btn" data-testid="header-search-button">{icon("search")}<span>{s["search_btn"]}</span></button>'
    nav = s['nav']
    if nav_order:
        lookup = dict(nav)
        nav = [(k, lookup[k]) for k in nav_order]
    lis = []
    for k, label in nav:
        cur = ' aria-current="page"' if k == key else ''
        lis.append(f'<li><a href="{rel(lang, lang, k)}"{cur}>{label}</a></li>')
    return f'''<a class="skip-link" href="#main">{s["skip"]}</a>
<div class="topbar">
  <div class="container topbar-inner">
    <p class="topbar-note">{s["note"]}</p>
    {lang_switch(lang, key)}
  </div>
</div>
<header class="site-header">
  <div class="container header-inner">
    <a class="brand" href="{rel(lang, lang, 'home')}"><img src="{a}img/logo.svg" alt="{s["logo_alt"]}" width="272" height="56" data-testid="site-logo"></a>
    <form class="site-search" role="search" action="{rel(lang, lang, 'search')}" method="get">
      <label class="sr-only" for="site-q">{s["search_label"]}</label>
      <input id="site-q" name="q" type="search" placeholder="{s["search_ph"]}">
      {btn}
    </form>
    <button type="button" class="nav-toggle" aria-expanded="false" aria-controls="main-nav-list" data-nav-toggle>{icon("menu")}{s["menu"]}</button>
  </div>
  <nav class="main-nav" aria-label="{s["nav_label"]}" data-testid="main-nav">
    <div class="container">
      <ul id="main-nav-list">
        {"".join(lis)}
      </ul>
    </div>
  </nav>
</header>'''


def page_tools(lang, crumbs):
    s = S[lang]
    parts = [f'<li><a href="{rel(lang, lang, "home")}">{s["home"]}</a></li>']
    for c in crumbs[:-1]:
        label, href = c
        parts.append(f'<li><a href="{href}">{label}</a></li>')
    parts.append(f'<li aria-current="page">{crumbs[-1]}</li>')
    return f'''<div class="container page-tools">
  <nav class="breadcrumb" aria-label="{s["crumb_label"]}"><ol>{"".join(parts)}</ol></nav>
  <button type="button" class="tool-btn" data-print data-testid="print-button">{icon("printer")}{s["print"]}</button>
</div>'''


def footer(lang):
    s = S[lang]
    links = ''.join(f'<li><a href="{rel(lang, lang, k)}">{label}</a></li>' for k, label in s['f_links'])
    return f'''<footer class="site-footer">
  <div class="container footer-grid">
    <div>
      <h2 class="footer-title">{s["f_admin"]}</h2>
      <address>{s["f_street"]}<br>{s["f_city"]}<br>{s["f_phone"]} <a href="tel:+41320001234">032 000 12 34</a><br><a href="mailto:gemeinde@musterwil.example">gemeinde@musterwil.example</a></address>
    </div>
    <div>
      <h2 class="footer-title">{s["f_hours_title"]}</h2>
      <p>{s["f_hours"]}</p>
      <p><a href="{rel(lang, lang, 'hours')}">{s["f_hours_link"]}</a></p>
    </div>
    <div>
      <h2 class="footer-title">{s["f_service"]}</h2>
      <ul>{links}</ul>
    </div>
  </div>
  <div class="container footer-bottom">
    <p>{s["f_copy"]}</p>
    <p>{s["f_note"]}</p>
  </div>
</footer>'''


def page(lang, key, title, main, *, description='', crumbs=None, scripts=(), html_lang=None,
         nav_order=None, search_variant=None, head_extra='', body_end=''):
    a = asset(lang)
    code = html_lang or CODES[lang]
    tools = page_tools(lang, crumbs) if crumbs else ''
    js = ''.join(f'\n<script src="{a}js/{name}" defer></script>' for name in ('site.js',) + tuple(scripts))
    desc = f'\n<meta name="description" content="{description}">' if description else ''
    return f'''<!doctype html>
<html lang="{code}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>{desc}
<link rel="icon" href="{a}img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{a}css/site.css">
<script>document.documentElement.classList.add('js');</script>{js}{head_extra}
</head>
<body>
{header(lang, key, nav_order, search_variant)}
<main id="main" tabindex="-1">
{tools}
{main}
</main>
{footer(lang)}{body_end}
</body>
</html>
'''
