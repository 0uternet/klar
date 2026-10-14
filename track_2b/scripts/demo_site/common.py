"""Helpers shared by the DE/FR/IT content modules."""
import json

COLLECT = {3: 'rest', 10: 'rest', 17: 'rest', 24: 'rest', 5: 'green', 19: 'green', 11: 'paper', 25: 'carton'}

CAL_TEXT = {
    'de': dict(caption='November 2026',
               days=[('Mo', 'Montag'), ('Di', 'Dienstag'), ('Mi', 'Mittwoch'), ('Do', 'Donnerstag'), ('Fr', 'Freitag'), ('Sa', 'Samstag'), ('So', 'Sonntag')],
               types={'rest': ('K', 'Kehricht'), 'green': ('G', 'Grüngut'), 'paper': ('P', 'Papier'), 'carton': ('C', 'Karton')}),
    'fr': dict(caption='Novembre 2026',
               days=[('lu', 'lundi'), ('ma', 'mardi'), ('me', 'mercredi'), ('je', 'jeudi'), ('ve', 'vendredi'), ('sa', 'samedi'), ('di', 'dimanche')],
               types={'rest': ('O', 'Ordures ménagères'), 'green': ('V', 'Déchets verts'), 'paper': ('P', 'Papier'), 'carton': ('C', 'Carton')}),
    'it': dict(caption='Novembre 2026',
               days=[('lu', 'lunedì'), ('ma', 'martedì'), ('me', 'mercoledì'), ('gi', 'giovedì'), ('ve', 'venerdì'), ('sa', 'sabato'), ('do', 'domenica')],
               types={'rest': ('R', 'Rifiuti domestici'), 'green': ('V', 'Scarti vegetali'), 'paper': ('C', 'Carta'), 'carton': ('Ca', 'Cartone')}),
}


def calendar(lang, letters=False, testid='waste-calendar'):
    t = CAL_TEXT[lang]
    head = ''.join(f'<th scope="col"><abbr title="{full}">{short}</abbr></th>' for short, full in t['days'])
    # 1 November 2026 is a Sunday
    cells = [None] * 6 + list(range(1, 31))
    while len(cells) % 7:
        cells.append(None)
    rows = []
    for w in range(0, len(cells), 7):
        tds = []
        for d in cells[w:w + 7]:
            if d is None:
                tds.append('<td></td>')
                continue
            kind = COLLECT.get(d)
            mark = ''
            if kind and letters:
                letter, name = t['types'][kind]
                mark = f'<span class="dot dot-letter dot-{kind}" aria-hidden="true">{letter}</span><span class="sr-only">{name}</span>'
            elif kind:
                mark = f'<span class="dot dot-{kind}"></span>'
            tds.append(f'<td><span class="cal-day">{d}</span>{mark}</td>')
        rows.append('<tr>' + ''.join(tds) + '</tr>')
    if letters:
        legend = ''.join(f'<li><span class="dot dot-letter dot-{k}" aria-hidden="true">{l}</span>{name}</li>' for k, (l, name) in t['types'].items())
    else:
        legend = ''.join(f'<li><span class="dot dot-{k}"></span>{name}</li>' for k, (l, name) in t['types'].items())
    return (f'<figure class="waste-calendar" data-testid="{testid}">\n'
            f'<div class="table-wrap"><table class="cal"><caption>{t["caption"]}</caption>'
            f'<thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>\n'
            f'<ul class="legend">{legend}</ul>\n</figure>')


def search_index(entries):
    data = json.dumps(entries, ensure_ascii=False, indent=1)
    return f'<script>\nwindow.SEARCH_INDEX = {data};\n</script>'


def hours_grid(pairs, wrong_order, testid='hours-library'):
    """pairs: list of (day, time). wrong_order=True puts all days first, then all times (grid rows restore the visual pairing)."""
    if wrong_order:
        days = ''.join(f'<dt class="hg-day hg-r{i + 1}">{d}</dt>' for i, (d, _) in enumerate(pairs))
        times = ''.join(f'<dd class="hg-time hg-r{i + 1}">{t}</dd>' for i, (_, t) in enumerate(pairs))
        inner = days + times
    else:
        inner = ''.join(f'<dt class="hg-day">{d}</dt><dd class="hg-time">{t}</dd>' for d, t in pairs)
    return f'<dl class="hours-grid" data-testid="{testid}">{inner}</dl>'
