"""Flat SVG illustrations for the fictional Musterwil demo site (all drawn here, no external resources)."""
import os

FONT = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
C = dict(
    wall='#f5ead7', wall2='#ecdcc0', wall3='#f2dcc9', wall4='#e4e9dc', wall5='#f0e2c0',
    roof='#c1563e', roof2='#9c4433', roof3='#7d5a44', win='#5d7f8c', win_lit='#f6cf72',
    door='#7a4a2e', trunk='#6b4a2f', tree1='#2f7d4f', tree2='#3f9a5f', tree3='#5bb173',
    autumn1='#d9822b', autumn2='#e3a83a', autumn3='#c4572f',
    lake='#4f9fbf', lake2='#3d88a8', teal='#0e5a63', teal2='#1f7a7f', teal3='#12707a',
    accent='#e07a3f', cream='#fbeee5', sun='#f6cf72', ink='#2b3a40', stone='#c9c3b6',
    path='#e6d6b8', skin1='#f1c7a5', skin2='#c98b63', skin3='#8d5a3b',
)


def n(v):
    s = f'{v:.1f}'
    return s[:-2] if s.endswith('.0') else s


def svg(w, h, body, defs=''):
    d = f'<defs>{defs}</defs>' if defs else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'{d}{body}</svg>\n')


def rect(x, y, w, h, fill, rx=0, extra=''):
    r = f' rx="{n(rx)}"' if rx else ''
    e = f' {extra}' if extra else ''
    return f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}"{r} fill="{fill}"{e}/>'


def circle(cx, cy, r, fill, extra=''):
    e = f' {extra}' if extra else ''
    return f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" fill="{fill}"{e}/>'


def path(d, fill, extra=''):
    e = f' {extra}' if extra else ''
    return f'<path d="{d}" fill="{fill}"{e}/>'


def tree(x, base, h, c1, c2=None):
    r = h * 0.3
    tw = max(4, h * 0.075)
    return (rect(x - tw / 2, base - h * 0.45, tw, h * 0.45, C['trunk'], rx=2)
            + circle(x, base - h * 0.68, r, c1)
            + circle(x - r * 0.62, base - h * 0.5, r * 0.72, c1)
            + circle(x + r * 0.62, base - h * 0.5, r * 0.8, c2 or c1))


def conifer(x, base, h, c, c2=None):
    w = h * 0.48
    tw = max(3, h * 0.06)
    s = rect(x - tw / 2, base - h * 0.17, tw, h * 0.17, C['trunk'])
    for i, (top, bot, ww) in enumerate([(0, 0.45, 0.6), (0.22, 0.68, 0.82), (0.42, 0.87, 1.0)]):
        col = c if (i % 2 == 0 or not c2) else c2
        s += path(f'M{n(x)},{n(base - h + top * h)} L{n(x + w * ww / 2)},{n(base - h + bot * h)} '
                  f'L{n(x - w * ww / 2)},{n(base - h + bot * h)}Z', col)
    return s


def cloud(x, y, s=1.0, op=0.85):
    return (f'<g fill="#ffffff" opacity="{op}">'
            f'<ellipse cx="{n(x)}" cy="{n(y)}" rx="{n(62 * s)}" ry="{n(17 * s)}"/>'
            f'<circle cx="{n(x - 20 * s)}" cy="{n(y - 10 * s)}" r="{n(22 * s)}"/>'
            f'<circle cx="{n(x + 14 * s)}" cy="{n(y - 16 * s)}" r="{n(28 * s)}"/></g>')


def house(x, base, w, h, wall, roof, win=None, rows=1, cols=2, door=True, roof_h=None, lit=False):
    win = win or (C['win_lit'] if lit else C['win'])
    roof_h = roof_h if roof_h is not None else w * 0.42
    s = rect(x, base - h, w, h, wall)
    s += path(f'M{n(x - w * 0.08)},{n(base - h)} L{n(x + w / 2)},{n(base - h - roof_h)} L{n(x + w * 1.08)},{n(base - h)}Z', roof)
    ww, wh = w * 0.18, h * 0.2
    for r in range(rows):
        for c in range(cols):
            wx = x + w * (c + 1) / (cols + 1) - ww / 2
            wy = base - h + h * 0.16 + r * (wh + h * 0.12)
            s += rect(wx, wy, ww, wh, win, rx=2)
    if door:
        s += rect(x + w / 2 - w * 0.08, base - h * 0.3, w * 0.16, h * 0.3, C['door'], rx=2)
    return s


def gemeindehaus(x, base, s=1.0):
    W, H = 300 * s, 150 * s
    g = rect(x, base - H, W, H, C['wall'])
    g += rect(x, base - 12 * s, W, 12 * s, C['wall2'])
    g += path(f'M{n(x - 14 * s)},{n(base - H)} L{n(x + W + 14 * s)},{n(base - H)} '
              f'L{n(x + W - 52 * s)},{n(base - H - 58 * s)} L{n(x + 52 * s)},{n(base - H - 58 * s)}Z', C['roof'])
    tw = 50 * s
    tx = x + W / 2 - tw / 2
    ttop = base - H - 118 * s
    g += rect(tx, ttop, tw, 118 * s, C['wall2'])
    g += path(f'M{n(tx - 7 * s)},{n(ttop)} L{n(tx + tw / 2)},{n(ttop - 50 * s)} L{n(tx + tw + 7 * s)},{n(ttop)}Z', C['roof2'])
    cx, cy = tx + tw / 2, ttop + 32 * s
    g += circle(cx, cy, 15 * s, '#ffffff', f'stroke="{C["ink"]}" stroke-width="{n(2.2 * s)}"')
    g += (f'<path d="M{n(cx)},{n(cy)} L{n(cx)},{n(cy - 10 * s)} M{n(cx)},{n(cy)} L{n(cx + 7 * s)},{n(cy + 3 * s)}" '
          f'stroke="{C["ink"]}" stroke-width="{n(2.2 * s)}" stroke-linecap="round" fill="none"/>')
    g += rect(tx + tw / 2 - 7 * s, ttop + 62 * s, 14 * s, 26 * s, C['win'], rx=7 * s)
    slot = (W - 48 * s) / 6
    for row, wy in enumerate([base - H + 24 * s, base - H + 80 * s]):
        for i in range(6):
            if row == 1 and i in (2, 3):
                continue
            wx = x + 24 * s + i * slot + (slot - 24 * s) / 2
            g += rect(wx, wy, 24 * s, 32 * s, C['win'], rx=3 * s)
            g += rect(wx - 2 * s, wy + 32 * s, 28 * s, 5 * s, C['roof2'], rx=2 * s)
    dx = x + W / 2 - 22 * s
    g += path(f'M{n(dx)},{n(base)} V{n(base - 46 * s)} A{n(22 * s)},{n(22 * s)} 0 0 1 {n(dx + 44 * s)},{n(base - 46 * s)} V{n(base)}Z', C['door'])
    g += rect(dx - 10 * s, base - 4 * s, 64 * s, 6 * s, C['stone'], rx=2 * s)
    return g


def person(x, base, body, skin, hair='#3b2a20', h=1.0):
    s = h
    g = rect(x - 9 * s, base - 34 * s, 7 * s, 34 * s, '#34434a', rx=3 * s)
    g += rect(x + 2 * s, base - 34 * s, 7 * s, 34 * s, '#34434a', rx=3 * s)
    g += rect(x - 14 * s, base - 78 * s, 28 * s, 48 * s, body, rx=12 * s)
    g += circle(x, base - 92 * s, 13 * s, skin)
    g += path(f'M{n(x - 13 * s)},{n(base - 94 * s)} A{n(13 * s)},{n(13 * s)} 0 0 1 {n(x + 13 * s)},{n(base - 94 * s)} '
              f'Q{n(x)},{n(base - 100 * s)} {n(x - 13 * s)},{n(base - 94 * s)}Z', hair)
    return g


def bike(x, base, color, s=1.0):
    r = 30 * s
    rx, fx = x, x + 96 * s
    y = base - r
    st = f'stroke="{C["ink"]}" stroke-width="{n(5 * s)}" fill="none"'
    g = f'<circle cx="{n(rx)}" cy="{n(y)}" r="{n(r)}" {st}/><circle cx="{n(fx)}" cy="{n(y)}" r="{n(r)}" {st}/>'
    g += f'<circle cx="{n(rx)}" cy="{n(y)}" r="{n(3 * s)}" fill="{C["ink"]}"/><circle cx="{n(fx)}" cy="{n(y)}" r="{n(3 * s)}" fill="{C["ink"]}"/>'
    bb = (x + 42 * s, y)
    seat = (x + 34 * s, y - 46 * s)
    head = (x + 82 * s, y - 50 * s)
    fs = f'stroke="{color}" stroke-width="{n(6 * s)}" stroke-linecap="round" stroke-linejoin="round" fill="none"'
    g += (f'<path d="M{n(rx)},{n(y)} L{n(bb[0])},{n(bb[1])} L{n(seat[0])},{n(seat[1])} Z '
          f'M{n(seat[0])},{n(seat[1])} L{n(head[0])},{n(head[1])} L{n(bb[0])},{n(bb[1])} '
          f'M{n(head[0])},{n(head[1])} L{n(fx)},{n(y)}" {fs}/>')
    g += f'<path d="M{n(seat[0] - 10 * s)},{n(seat[1] - 6 * s)} h{n(20 * s)}" stroke="{C["ink"]}" stroke-width="{n(6 * s)}" stroke-linecap="round"/>'
    g += f'<path d="M{n(head[0])},{n(head[1])} l{n(-4 * s)},{n(-12 * s)} h{n(14 * s)}" stroke="{C["ink"]}" stroke-width="{n(5 * s)}" stroke-linecap="round" fill="none"/>'
    return g


def kid(x, base, jacket, helmet, skin):
    g = rect(x - 8, base - 30, 6, 30, '#34434a', rx=3) + rect(x + 2, base - 30, 6, 30, '#34434a', rx=3)
    g += rect(x - 12, base - 66, 24, 40, jacket, rx=10)
    g += circle(x, base - 77, 11, skin)
    g += path(f'M{x - 13},{base - 78} A13,13 0 0 1 {x + 13},{base - 78}Z', helmet)
    g += f'<path d="M{x + 8},{base - 56} L{x + 26},{base - 50}" stroke="{jacket}" stroke-width="7" stroke-linecap="round"/>'
    return g


def sky(gid, top, bottom, mid=None):
    stops = f'<stop offset="0" stop-color="{top}"/>'
    if mid:
        stops += f'<stop offset=".6" stop-color="{mid}"/>'
    stops += f'<stop offset="1" stop-color="{bottom}"/>'
    return f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">{stops}</linearGradient>'


# ---------------------------------------------------------------- hero
def hero():
    W, H = 1600, 560
    defs = (sky('sky', '#5fa6bd', '#8fc3d1', '#6aaec4')
            + '<linearGradient id="lake" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5aa8c6"/><stop offset="1" stop-color="#3f8eaf"/></linearGradient>')
    b = rect(0, 0, W, H, 'url(#sky)')
    b += circle(1330, 118, 56, '#f8dc94', 'opacity=".95"')
    b += cloud(1150, 96, 1.0, .7) + cloud(1480, 180, .8, .65) + cloud(1060, 210, .55, .5)
    b += path('M0,392 L130,360 L230,380 L350,350 L470,374 L590,352 L720,376 L860,334 L960,306 L1060,334 L1180,284 '
              'L1290,322 L1400,292 L1520,328 L1600,312 V560 H0Z', '#a3c9d3')
    b += path('M1180,284 L1158,300 L1172,298 L1186,306 L1200,296 Z M1400,292 L1382,305 L1396,304 L1408,310 L1418,302Z '
              'M960,306 L944,318 L958,316 L970,322 L978,316Z', '#eef6f7')
    b += path('M0,418 C220,388 420,404 640,396 C860,388 980,352 1200,354 C1380,356 1500,374 1600,370 V560 H0Z', '#9fcb8f')
    b += house(985, 386, 70, 46, C['wall3'], C['roof'], cols=2) + tree(950, 392, 70, C['tree2'], C['tree3'])
    b += gemeindehaus(1080, 396, 0.6)
    b += house(1290, 384, 82, 54, C['wall5'], C['roof2'], cols=2) + house(1395, 388, 66, 44, C['wall4'], C['roof'], cols=2)
    b += tree(1270, 392, 76, C['tree1'], C['tree2']) + conifer(1480, 394, 90, C['tree1']) + conifer(1515, 398, 70, C['tree2'])
    b += path('M0,456 C260,442 520,450 760,444 C900,440 1000,448 1110,456 L1110,488 C820,496 420,492 0,498Z', 'url(#lake)')
    b += ('<g stroke="#ffffff" stroke-width="3" stroke-linecap="round" opacity=".55">'
          '<path d="M120,470 h60 M320,462 h90 M560,474 h70 M780,462 h50 M930,476 h60"/></g>')
    b += path('M410,462 L470,462 L460,472 L420,472Z', '#ffffff') + path('M440,412 L440,460 L468,460Z', '#ffffff') + path('M436,420 L436,460 L414,460Z', '#f2e9da')
    b += path('M0,492 C300,474 560,504 860,490 C1100,478 1300,452 1600,464 V560 H0Z', '#77b27a')
    b += tree(70, 506, 96, C['tree1'], C['tree2']) + tree(170, 498, 70, C['tree2'], C['tree3'])
    b += conifer(1170, 476, 96, C['tree1']) + tree(1250, 470, 84, C['tree2'], C['tree1'])
    b += tree(1490, 474, 106, C['tree1'], C['tree2']) + conifer(1565, 478, 84, C['tree2'])
    b += path('M0,534 C380,514 820,542 1200,524 C1400,516 1500,522 1600,518 V560 H0Z', '#4f9562')
    return svg(W, H, b, defs)


# ---------------------------------------------------------------- news images (640x360)
def news_gemeindehaus():
    W, H = 640, 360
    b = rect(0, 0, W, H, 'url(#s)')
    b += circle(540, 70, 30, C['sun'], 'opacity=".9"') + cloud(120, 70, .8, .9)
    b += path('M0,280 C160,262 480,262 640,276 V360 H0Z', '#9fcb8f')
    b += tree(70, 300, 150, C['tree1'], C['tree2']) + tree(575, 300, 160, C['tree2'], C['tree1'])
    b += gemeindehaus(170, 300, 1.0)
    b += path('M250,360 C280,330 300,312 320,300 L340,300 C360,312 380,330 410,360Z', C['path'])
    b += rect(470, 286, 54, 6, C['roof3'], rx=2) + rect(474, 292, 4, 10, C['roof3']) + rect(516, 292, 4, 10, C['roof3'])
    b += path('M0,320 C200,310 440,314 640,322 V360 H0Z', '#77b27a')
    return svg(W, H, b, sky('s', '#cfe8ef', '#eef6f3'))


def news_recycling():
    W, H = 640, 360
    b = rect(0, 0, W, H, 'url(#s)')
    b += cloud(500, 60, .8, .9)
    b += tree(60, 220, 150, C['tree1'], C['tree2']) + conifer(590, 220, 170, C['tree1']) + tree(530, 220, 110, C['tree2'], C['tree3'])
    b += rect(0, 168, W, 56, '#c9d6d3') + ''.join(rect(x, 168, 3, 56, '#b5c4c0') for x in range(40, 640, 80))
    b += rect(0, 222, W, 138, '#d9dedc') + rect(0, 222, W, 6, '#c3cbc8')
    bins = [(58, '#2e7d32', 'leaf'), (196, '#2f6db5', 'paper'), (334, '#8a5a2b', 'box'), (472, '#5b6770', 'bag')]
    for x, col, sym in bins:
        b += rect(x + 8, 300, 16, 16, C['ink'], rx=8) + rect(x + 86, 300, 16, 16, C['ink'], rx=8)
        b += rect(x, 178, 110, 126, col, rx=12)
        b += rect(x - 4, 170, 118, 22, col, rx=8) + rect(x - 4, 170, 118, 22, '#000000', rx=8, extra='opacity=".18"')
        b += rect(x + 30, 200, 50, 8, '#000000', rx=4, extra='opacity=".3"')
        b += circle(x + 55, 250, 26, '#ffffff', 'opacity=".95"')
        if sym == 'leaf':
            b += path(f'M{x + 44},{262} C{x + 42},{240} {x + 58},{232} {x + 68},{236} C{x + 70},{252} {x + 58},{264} {x + 44},{262}Z', col)
        elif sym == 'paper':
            b += rect(x + 43, 236, 24, 30, col, rx=2) + rect(x + 48, 243, 14, 3, '#ffffff') + rect(x + 48, 250, 14, 3, '#ffffff') + rect(x + 48, 257, 10, 3, '#ffffff')
        elif sym == 'box':
            b += rect(x + 40, 240, 30, 24, col, rx=2) + path(f'M{x + 40},{240} L{x + 55},{232} L{x + 70},{240}Z', col)
        else:
            b += path(f'M{x + 42},{266} C{x + 38},{246} {x + 46},{238} {x + 55},{238} C{x + 64},{238} {x + 72},{246} {x + 68},{266}Z', col)
            b += rect(x + 50, 232, 10, 8, col, rx=2)
    return svg(W, H, b, sky('s', '#d6ecf0', '#eef6f3'))


def awning(x, y, w, h, c1, c2, stripes=6):
    g = ''
    sw = w / stripes
    for i in range(stripes):
        g += rect(x + i * sw, y, sw, h, c1 if i % 2 == 0 else c2)
    for i in range(stripes):
        g += circle(x + i * sw + sw / 2, y + h, sw / 2, c1 if i % 2 == 0 else c2)
    return g


def stall(x, base, w, c1, c2, produce):
    g = rect(x + 6, base - 150, 6, 150, C['roof3']) + rect(x + w - 12, base - 150, 6, 150, C['roof3'])
    g += awning(x - 6, base - 160, w + 12, 30, c1, c2)
    g += rect(x, base - 62, w, 14, C['roof3'], rx=3) + rect(x + 6, base - 48, w - 12, 48, C['teal'], rx=2)
    g += produce
    return g


def pumpkins(x, y, k=4):
    g = ''
    for i in range(k):
        cx = x + i * 26
        g += f'<ellipse cx="{cx}" cy="{y}" rx="14" ry="11" fill="{C["accent"]}"/>'
        g += f'<path d="M{cx},{y - 11} v-5" stroke="{C["tree1"]}" stroke-width="3" stroke-linecap="round"/>'
    return g


def apples(x, y, k=6):
    return ''.join(circle(x + (i % 3) * 14, y - (i // 3) * 12, 7, '#c84a3a' if i % 2 else '#d9603f') for i in range(k))


def news_maerit():
    W, H = 640, 360
    b = rect(0, 0, W, H, 'url(#s)')
    cols = [C['wall'], C['wall3'], C['wall4'], C['wall5'], C['wall3']]
    for i, c in enumerate(cols):
        b += house(-10 + i * 132, 196, 124, 120, c, C['roof'] if i % 2 else C['roof2'], rows=2, cols=3, door=False, roof_h=40)
    b += rect(0, 196, W, 164, '#e3d7c3')
    b += ''.join(f'<path d="M0,{y} H640" stroke="#d6c8b0" stroke-width="2"/>' for y in (230, 270, 315))
    b += stall(30, 300, 170, C['accent'], C['cream'], pumpkins(50, 230) + apples(140, 232))
    b += stall(240, 300, 170, C['teal2'], C['cream'],
               ''.join(f'<ellipse cx="{262 + i * 30}" cy="232" rx="13" ry="8" fill="#d9a35b"/>' for i in range(5)))
    b += stall(450, 300, 170, '#c1563e', C['cream'],
               ''.join(circle(470 + i * 26, 228, 9, c) + rect(466 + i * 26, 232, 8, 8, C['roof3'])
                       for i, c in enumerate(['#e3a83a', '#d9603f', '#f2b544', '#c84a3a', '#e07a3f', '#f2b544'])))
    b += person(215, 352, '#2f6db5', C['skin1'], h=.9) + person(430, 356, C['tree2'], C['skin2'], '#2a1d16', h=.95)
    return svg(W, H, b, sky('s', '#d3eaf0', '#f2f0e6'))


def news_velo():
    W, H = 640, 360
    b = rect(0, 0, W, H, 'url(#s)')
    b += cloud(110, 56, .7, .9)
    b += tree(40, 250, 170, C['tree1'], C['tree2'])
    b += rect(80, 110, 500, 140, '#f2e3c8')
    b += path('M64,110 L596,110 L560,76 L100,76Z', C['roof2'])
    for row in range(2):
        for i in range(9):
            if row == 1 and i == 4:
                continue
            b += rect(100 + i * 53, 128 + row * 56, 32, 36, C['win'], rx=3)
    b += rect(306, 186, 48, 64, C['door'], rx=3) + circle(330, 92, 11, '#ffffff', f'stroke="{C["ink"]}" stroke-width="2"')
    b += rect(0, 250, W, 110, '#e6d6b8') + rect(0, 250, W, 5, '#d7c4a0')
    b += tree(612, 252, 140, C['tree2'], C['tree3'])
    b += bike(150, 340, C['accent']) + kid(120, 340, '#2f6db5', C['sun'], C['skin1'])
    b += bike(390, 344, C['teal2']) + kid(518, 344, C['accent'], C['tree2'], C['skin2'])
    return svg(W, H, b, sky('s', '#cfe8ef', '#eef6f3'))


def news_laternen():
    W, H = 640, 360
    defs = sky('s', '#1b2a4a', '#34507a') + ('<radialGradient id="glow"><stop offset="0" stop-color="#f6cf72" stop-opacity=".75"/>'
                                            '<stop offset="1" stop-color="#f6cf72" stop-opacity="0"/></radialGradient>')
    b = rect(0, 0, W, H, 'url(#s)')
    for sx, sy in [(60, 40), (140, 80), (220, 30), (300, 64), (380, 24), (450, 70), (600, 50), (520, 110), (90, 120)]:
        b += circle(sx, sy, 1.8, '#ffffff', 'opacity=".8"')
    b += circle(560, 70, 26, '#f4f1e4') + circle(572, 62, 24, '#22345a')
    for i, (x, w, h) in enumerate([(0, 120, 120), (110, 100, 150), (200, 130, 110), (320, 110, 140), (420, 120, 120), (530, 120, 150)]):
        b += house(x, 270, w, h, '#16223b', '#111a2e', win=C['win_lit'] if i % 2 == 0 else '#3b4c6b', rows=2, cols=2, door=False, roof_h=34)
    b += rect(0, 268, W, 92, '#0a1222')
    for x, hgt in [(120, 1.0), (240, .85), (360, 1.05), (480, .9)]:
        base = 340
        b += rect(x - 10 * hgt, base - 90 * hgt, 20 * hgt, 60 * hgt, '#33476e', rx=8 * hgt)
        b += rect(x - 8 * hgt, base - 32 * hgt, 7 * hgt, 32 * hgt, '#33476e') + rect(x + 1 * hgt, base - 32 * hgt, 7 * hgt, 32 * hgt, '#33476e')
        b += circle(x, base - 100 * hgt, 11 * hgt, '#3d5480')
        lx, ly = x + 30 * hgt, base - 104 * hgt
        b += f'<path d="M{n(x + 8 * hgt)},{n(base - 76 * hgt)} L{n(lx)},{n(ly - 22 * hgt)}" stroke="#5b4630" stroke-width="3"/>'
        b += circle(lx, ly, 40 * hgt, 'url(#glow)')
        b += f'<path d="M{n(lx)},{n(ly - 22 * hgt)} v8" stroke="#5b4630" stroke-width="2"/>'
        b += circle(lx, ly, 13 * hgt, '#f6a94a') + circle(lx - 3 * hgt, ly - 3 * hgt, 5 * hgt, '#fde6b0')
    return svg(W, H, b, defs)


# ---------------------------------------------------------------- carousel slides (1200x500)
def slide_seeufer():
    W, H = 1200, 500
    defs = sky('s', '#8fc6d6', '#f6dcaa', '#c9e0dc') + sky('l', '#4a93b3', '#2f6f8c')
    b = rect(0, 0, W, H, 'url(#s)')
    b += circle(860, 296, 54, '#f7c063')
    b += path('M0,300 C200,270 380,292 560,280 C760,268 980,284 1200,276 V330 H0Z', '#86ab9e')
    b += rect(0, 318, W, 182, 'url(#l)')
    b += ''.join(f'<path d="M{820 - k * 12},{336 + k * 18} h{80 + k * 24}" stroke="#f7c063" stroke-width="4" stroke-linecap="round" opacity="{.8 - k * .1:.2f}"/>' for k in range(6))
    b += path('M0,318 C120,300 240,312 330,336 C372,380 330,450 270,500 H0Z', '#5f9a5c')
    b += tree(60, 340, 170, C['tree1'], C['tree2']) + tree(170, 336, 130, C['tree2'], C['tree3']) + conifer(260, 344, 140, C['tree1'])
    b += path('M300,500 L360,500 L640,372 L612,372Z', '#a0754f')
    b += ''.join(f'<path d="M{n(330 + i * 33)},{n(486 - i * 15)} h{n(30 - i * 0.6)}" stroke="#7d5a3b" stroke-width="3"/>' for i in range(9))
    b += ''.join(rect(326 + i * 62, 486 - i * 28, 6, 30, '#5e432c') for i in range(5))
    b += path('M720,388 L812,388 L800,402 L732,402Z', '#ffffff') + path('M766,300 L766,386 L812,386Z', '#ffffff') + path('M760,312 L760,386 L726,386Z', '#f3e7d5')
    b += ''.join(f'<path d="M{x},500 C{x - 4},470 {x + 6},440 {x + 2},{410 + (x % 30)}" stroke="#4f8a4a" stroke-width="4" fill="none"/>' for x in range(20, 280, 18))
    return svg(W, H, b, defs)


def slide_wald():
    W, H = 1200, 500
    defs = sky('s', '#cfe3c8', '#eef3e1')
    b = rect(0, 0, W, H, 'url(#s)')
    b += path('M760,0 L860,0 L560,500 L420,500Z', '#ffffff', 'opacity=".22"') + path('M900,0 L960,0 L760,500 L680,500Z', '#ffffff', 'opacity=".18"')
    for i, x in enumerate(range(-20, 1240, 70)):
        b += conifer(x, 330, 220 + (i % 3) * 30, '#5c8f62' if i % 2 else '#6e9e6a')
    b += rect(0, 320, W, 180, '#8fb06b')
    b += path('M520,500 C560,440 640,410 610,370 C590,344 640,330 660,322 L700,322 C690,340 650,350 680,380 C720,420 700,460 760,500Z', '#e6d6b8')
    cols = [(C['autumn1'], C['autumn2']), (C['tree1'], C['tree2']), (C['autumn3'], C['autumn1']), (C['autumn2'], C['sun'])]
    for i, x in enumerate([60, 200, 330, 470, 840, 980, 1110]):
        c1, c2 = cols[i % 4]
        b += tree(x, 420 + (i % 2) * 30, 230, c1, c2)
    b += conifer(760, 470, 260, C['tree1'], C['tree2'])
    b += rect(886, 360, 10, 90, C['roof3']) + rect(850, 330, 84, 50, '#7d5a3b', rx=4) + rect(858, 338, 68, 34, C['cream'], rx=2)
    b += rect(866, 346, 40, 4, C['roof3']) + rect(866, 354, 50, 4, C['roof3']) + rect(866, 362, 30, 4, C['roof3'])
    b += ''.join(circle(x, y, 5, c) for x, y, c in [(300, 470, C['autumn1']), (420, 486, C['autumn2']), (980, 480, C['autumn3']), (1060, 470, C['autumn1']), (140, 482, C['autumn2'])])
    return svg(W, H, b, defs)


def fountain(x, base):
    g = f'<ellipse cx="{x}" cy="{base}" rx="110" ry="24" fill="#b9b2a4"/>'
    g += rect(x - 110, base - 40, 220, 40, C['stone']) + f'<ellipse cx="{x}" cy="{base - 40}" rx="110" ry="22" fill="#d8d2c4"/>'
    g += f'<ellipse cx="{x}" cy="{base - 42}" rx="96" ry="16" fill="#8fd0e6"/>'
    g += rect(x - 10, base - 130, 20, 90, C['stone']) + circle(x, base - 136, 16, '#d8d2c4')
    g += (f'<path d="M{x - 8},{base - 120} C{x - 40},{base - 130} {x - 60},{base - 90} {x - 66},{base - 46} '
          f'M{x + 8},{base - 120} C{x + 40},{base - 130} {x + 60},{base - 90} {x + 66},{base - 46}" '
          f'stroke="#8fd0e6" stroke-width="6" fill="none" stroke-linecap="round"/>')
    return g


def slide_dorfplatz():
    W, H = 1200, 500
    b = rect(0, 0, W, H, 'url(#s)')
    b += cloud(200, 70, 1.0, .9) + cloud(980, 60, .8, .9)
    walls = [C['wall'], C['wall3'], C['wall5'], C['wall4'], C['wall'], C['wall3'], C['wall5']]
    for i, c in enumerate(walls):
        b += house(-20 + i * 176, 300, 164, 170, c, C['roof'] if i % 2 else C['roof2'], rows=2, cols=3, door=(i % 2 == 0), roof_h=56)
    b += rect(0, 298, W, 202, '#e3d7c3')
    b += ''.join(f'<path d="M0,{y} H1200" stroke="#d6c8b0" stroke-width="2"/>' for y in (340, 390, 450))
    b += stall(60, 440, 220, C['accent'], C['cream'], pumpkins(86, 370, 5) + apples(220, 372))
    b += stall(920, 440, 220, C['teal2'], C['cream'],
               ''.join(f'<ellipse cx="{946 + i * 34}" cy="372" rx="14" ry="9" fill="#d9a35b"/>' for i in range(6)))
    b += fountain(600, 440)
    b += person(380, 470, '#2f6db5', C['skin1']) + person(450, 476, C['accent'], C['skin3'], '#1e1410', .92)
    b += person(790, 472, C['tree2'], C['skin2'], '#2a1d16', .96)
    return svg(W, H, b, sky('s', '#cde7ee', '#f2f0e6'))


def slide_schiff():
    W, H = 1200, 500
    defs = sky('s', '#a9d6e3', '#e4f2f2') + sky('l', '#4c9cbc', '#2f7596')
    b = rect(0, 0, W, H, 'url(#s)')
    b += cloud(260, 90, 1.1, .9) + cloud(900, 70, .9, .85)
    b += path('M0,280 C200,220 360,250 520,236 C700,220 860,260 1000,244 C1100,236 1160,250 1200,256 V320 H0Z', '#86b48a')
    b += path('M0,300 C240,270 460,296 700,282 C900,272 1080,290 1200,284 V330 H0Z', '#5f9a5c')
    b += ''.join(conifer(x, 300 - (x % 3) * 4, 60 + (x % 4) * 6, C['tree1']) for x in range(20, 1200, 46))
    b += rect(0, 318, W, 182, 'url(#l)')
    b += path('M330,392 L870,392 L830,446 L372,446Z', '#ffffff') + rect(372, 410, 458, 10, C['teal'])
    b += rect(420, 346, 340, 48, '#f4f1ea', rx=6) + ''.join(rect(438 + i * 40, 358, 26, 20, C['win'], rx=3) for i in range(8))
    b += rect(470, 316, 220, 32, '#e9e4d8', rx=6) + rect(560, 270, 30, 50, C['accent'], rx=4) + rect(560, 270, 30, 10, C['ink'])
    b += path('M760,346 L760,300 L790,310 L760,320', C['teal'])
    b += ''.join(f'<path d="M{x},{y} q12,-10 24,0 q12,-10 24,0" stroke="#ffffff" stroke-width="3" fill="none" opacity=".7"/>'
                 for x, y in [(120, 430), (240, 470), (980, 420), (1060, 468), (900, 480)])
    b += ''.join(f'<path d="M{x},{y} q8,-8 16,0 q8,-8 16,0" stroke="{C["ink"]}" stroke-width="2.5" fill="none"/>'
                 for x, y in [(640, 120), (690, 96), (720, 140)])
    return svg(W, H, b, defs)


def tip_aussichtsturm():
    W, H = 800, 450
    b = rect(0, 0, W, H, 'url(#s)')
    b += path('M0,250 L120,170 L200,214 L320,140 L430,210 L540,150 L660,220 L800,180 V300 H0Z', '#b9cdd6')
    b += path('M300,150 L320,140 L342,154 L330,160Z M520,162 L540,150 L560,164 L546,168Z', '#ffffff')
    tx = 420
    st = 'stroke="#7d5a3b" stroke-width="8" stroke-linecap="round"'
    b += f'<path d="M{tx - 50},420 L{tx - 22},120 M{tx + 50},420 L{tx + 22},120" {st}/>'
    for y in range(160, 420, 52):
        k = (y - 120) / 300
        hw = 22 + 28 * k
        b += f'<path d="M{n(tx - hw)},{y} L{n(tx + hw + 6)},{y + 52}" stroke="#9a7350" stroke-width="5"/>'
        b += f'<path d="M{n(tx - hw)},{y} H{n(tx + hw)}" stroke="#7d5a3b" stroke-width="5"/>'
    b += rect(tx - 44, 104, 88, 16, '#7d5a3b', rx=3) + path(f'M{tx - 50},{70} L{tx},{40} L{tx + 50},{70}Z', C['roof2']) + rect(tx - 40, 70, 6, 36, '#7d5a3b') + rect(tx + 34, 70, 6, 36, '#7d5a3b')
    b += rect(0, 380, W, 70, '#2f6b4c')
    for i, x in enumerate(range(-30, 840, 52)):
        b += tree(x, 470 - (i % 3) * 14, 200 + (i % 4) * 24, [C['tree1'], C['tree2'], C['tree3']][i % 3], [C['tree2'], C['tree1'], C['tree2']][i % 3])
    return svg(W, H, b, sky('s', '#bfe1ea', '#eef6f3'))


def map_standort():
    W, H = 800, 450
    b = rect(0, 0, W, H, '#eef0e8')
    b += path('M0,0 H300 C260,60 200,90 120,110 C70,122 30,150 0,180Z', '#bcdbe6')
    b += rect(540, 40, 200, 120, '#d5e8c8', rx=18) + rect(60, 300, 180, 110, '#d5e8c8', rx=18)
    road = 'stroke="#ffffff" stroke-linecap="round" fill="none"'
    edge = 'stroke="#d6d0c2" stroke-linecap="round" fill="none"'
    roads = ['M0,236 H800', 'M520,0 V450', 'M140,110 C230,170 300,200 360,236', 'M520,236 C600,300 660,360 800,400']
    b += ''.join(f'<path d="{d}" {edge} stroke-width="30"/>' for d in roads)
    b += ''.join(f'<path d="{d}" {road} stroke-width="24"/>' for d in roads)
    blocks = [(300, 260, 90, 60), (410, 262, 80, 70), (560, 262, 70, 50), (650, 170, 90, 50), (560, 170, 70, 50),
              (330, 150, 70, 60), (410, 150, 80, 66), (260, 330, 110, 60), (560, 330, 70, 60), (680, 260, 70, 40)]
    b += ''.join(rect(x, y, w, h, '#d9d3c6', rx=4) for x, y, w, h in blocks)
    b += rect(400, 136, 100, 80, '#e9b8a8', rx=4)
    b += circle(318, 214, 14, C['teal']) + rect(311, 207, 14, 12, '#ffffff', rx=2) + rect(313, 209, 10, 4, C['teal'])
    b += path('M450,172 C450,172 416,140 416,114 A34,34 0 1 1 484,114 C484,140 450,172 450,172Z', '#c1563e')
    b += circle(450, 114, 12, '#ffffff')
    return svg(W, H, b)


def divider():
    W, H = 1200, 24
    d = 'M0,12 ' + ' '.join(f'Q{x + 15},2 {x + 30},12 T{x + 60},12' for x in range(0, 1200, 60))
    b = f'<path d="{d}" stroke="#9cc6c9" stroke-width="2" fill="none"/>'
    b += ''.join(circle(x, 12, 3.5, '#e07a3f') for x in (300, 600, 900))
    return svg(W, H, b)


def icon_map_pin():
    b = ('<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z" fill="none" stroke="#0e5a63" stroke-width="2" '
         'stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="10" r="2.6" fill="none" stroke="#0e5a63" stroke-width="2"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">{b}</svg>\n'


def mark(x, y, s=1.0):
    g = rect(x, y, 48 * s, 48 * s, C['teal'], rx=12 * s)
    g += circle(x + 30 * s, y + 17 * s, 9 * s, '#9fd3a5') + rect(x + 28.5 * s, y + 22 * s, 3 * s, 10 * s, '#9fd3a5', rx=1.5 * s)
    g += (f'<path d="M{n(x + 8 * s)},{n(y + 31 * s)} q{n(5 * s)},{n(-5 * s)} {n(10 * s)},0 t{n(10 * s)},0 t{n(10 * s)},0 t{n(10 * s)},0" '
          f'stroke="#ffffff" stroke-width="{n(3 * s)}" fill="none" stroke-linecap="round"/>')
    g += (f'<path d="M{n(8 * s + x)},{n(y + 39 * s)} q{n(5 * s)},{n(-5 * s)} {n(10 * s)},0 t{n(10 * s)},0 t{n(10 * s)},0 t{n(10 * s)},0" '
          f'stroke="#ffffff" stroke-width="{n(3 * s)}" fill="none" stroke-linecap="round" opacity=".65"/>')
    return g


def logo():
    b = mark(4, 4)
    b += (f'<text x="64" y="33" font-family="{FONT}" font-size="27" font-weight="700" fill="#0e5a63" '
          f'letter-spacing="-0.4">Musterwil</text>')
    b += (f'<text x="65" y="50" font-family="{FONT}" font-size="9.5" font-weight="600" fill="#8fb3b6" '
          f'letter-spacing="1.6">GEMEINDE · COMMUNE · COMUNE</text>')
    return svg(272, 56, b)


def favicon():
    return svg(56, 56, mark(4, 4))


# ---------------------------------------------------------------- poster with text (image of text)
def banner(lines):
    W, H = 640, 800
    b = rect(0, 0, W, H, C['teal'])
    b += circle(600, 60, 160, C['teal3'], 'opacity=".7"') + circle(40, 520, 120, '#0a3f47', 'opacity=".6"')
    b += rect(56, 76, 64, 8, '#f2b544', rx=4)
    t1, t2, t3, t4 = lines
    b += f'<text x="56" y="160" font-family="{FONT}" font-size="46" font-weight="800" fill="#ffffff" letter-spacing="-0.5">{t1}</text>'
    b += f'<text x="56" y="250" font-family="{FONT}" font-size="40" font-weight="600" fill="#ffffff">{t2}</text>'
    b += f'<text x="56" y="306" font-family="{FONT}" font-size="40" font-weight="600" fill="#ffffff">{t3}</text>'
    b += f'<text x="56" y="370" font-family="{FONT}" font-size="32" font-weight="400" fill="#ffffff">{t4}</text>'
    b += rect(0, 560, W, 240, '#0a3f47')
    b += rect(140, 470, 360, 140, '#f5ead7') + path('M120,470 L320,404 L520,470Z', C['roof'])
    b += ''.join(rect(166 + i * 70, 500, 44, 40, C['win_lit'], rx=4) for i in range(5))
    b += rect(296, 554, 48, 56, C['door'], rx=3)
    for i, x in enumerate(range(70, 600, 62)):
        y = 700 + (i % 2) * 14
        col = [C['accent'], '#f2b544', '#ffffff', C['tree3']][i % 4]
        b += rect(x - 16, y - 10, 32, 110, '#123c44', rx=14) + circle(x, y - 24, 16, '#1b4f57')
        if i % 3 != 1:
            b += f'<path d="M{x + 12},{y - 2} L{x + 22},{y - 54}" stroke="#123c44" stroke-width="9" stroke-linecap="round"/>'
            b += rect(x + 12, y - 82, 24, 30, col, rx=3, extra='transform="rotate(8 %d %d)"' % (x + 24, y - 67))
    return svg(W, H, b)


# ---------------------------------------------------------------- bar chart (image of a chart)
GREEN_2025 = [6, 7, 18, 31, 38, 35, 29, 27, 30, 36, 22, 8]


def chart(title, subtitle, months, footer):
    W, H = 960, 560
    x0, x1, y0, ytop = 104, 928, 452, 150
    vmax = 40
    b = rect(0, 0, W, H, '#ffffff')
    b += f'<text x="40" y="58" font-family="{FONT}" font-size="32" font-weight="700" fill="#1b2428">{title}</text>'
    b += f'<text x="40" y="96" font-family="{FONT}" font-size="22" fill="#55636a">{subtitle}</text>'
    for v in range(0, vmax + 1, 10):
        y = y0 - (y0 - ytop) * v / vmax
        b += f'<path d="M{x0},{n(y)} H{x1}" stroke="{"#9aa5ab" if v == 0 else "#e6e3dc"}" stroke-width="{2 if v == 0 else 1.2}"/>'
        b += f'<text x="{x0 - 16}" y="{n(y + 7)}" font-family="{FONT}" font-size="20" fill="#55636a" text-anchor="end">{v}</text>'
    slot = (x1 - x0) / 12
    bw = 44
    for i, v in enumerate(GREEN_2025):
        cx = x0 + slot * i + slot / 2
        top = y0 - (y0 - ytop) * v / vmax
        x = cx - bw / 2
        r = 5
        b += path(f'M{n(x)},{n(y0)} V{n(top + r)} Q{n(x)},{n(top)} {n(x + r)},{n(top)} H{n(x + bw - r)} '
                  f'Q{n(x + bw)},{n(top)} {n(x + bw)},{n(top + r)} V{n(y0)}Z', '#1f7a7f')
        b += f'<text x="{n(cx)}" y="{n(top - 10)}" font-family="{FONT}" font-size="21" font-weight="700" fill="#1b2428" text-anchor="middle">{v}</text>'
        b += f'<text x="{n(cx)}" y="{y0 + 32}" font-family="{FONT}" font-size="20" fill="#55636a" text-anchor="middle">{months[i]}</text>'
    b += f'<text x="40" y="540" font-family="{FONT}" font-size="20" fill="#55636a">{footer}</text>'
    return svg(W, H, b)


def write_all(img_dir):
    os.makedirs(img_dir, exist_ok=True)
    files = {
        'logo.svg': logo(),
        'favicon.svg': favicon(),
        'hero-musterwil.svg': hero(),
        'news-gemeindehaus.svg': news_gemeindehaus(),
        'news-recycling.svg': news_recycling(),
        'news-maerit.svg': news_maerit(),
        'news-velo.svg': news_velo(),
        'news-laternen.svg': news_laternen(),
        'slide-seeufer.svg': slide_seeufer(),
        'slide-wald.svg': slide_wald(),
        'slide-dorfplatz.svg': slide_dorfplatz(),
        'slide-schiff.svg': slide_schiff(),
        'tip-aussichtsturm.svg': tip_aussichtsturm(),
        'map-standort.svg': map_standort(),
        'divider-waves.svg': divider(),
        'icon-map-pin.svg': icon_map_pin(),
        'banner-versammlung-de.svg': banner(['Gemeindeversammlung', '24. November 2026', '19.30 Uhr', 'Mehrzweckhalle']),
        'banner-versammlung-fr.svg': banner(['Assemblée communale', '24 novembre 2026', '19 h 30', 'Salle polyvalente']),
        'banner-versammlung-it.svg': banner(['Assemblea comunale', '24 novembre 2026', 'ore 19.30', 'Sala multiuso']),
        'chart-gruengut-de.svg': chart('Grüngut-Sammelmengen 2025', 'in Tonnen pro Monat',
                                       ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'],
                                       'Total 2025: 287 t · Quelle: Werkhof Musterwil'),
        'chart-gruengut-fr.svg': chart('Déchets verts collectés en 2025', 'en tonnes par mois',
                                       ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'],
                                       'Total 2025 : 287 t · Source : voirie de Musterwil'),
        'chart-gruengut-it.svg': chart('Scarti vegetali raccolti nel 2025', 'in tonnellate al mese',
                                       ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic'],
                                       'Totale 2025: 287 t · Fonte: magazzino comunale di Musterwil'),
    }
    for name, content in files.items():
        with open(os.path.join(img_dir, name), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(content)
    return list(files)
