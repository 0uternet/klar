"""Colour facts for the visual checks (1.4.1, 1.4.3, 1.4.5, 1.4.11). Stdlib only.

  * CSS colour parsing (the computed-style forms Chromium returns: rgb()/rgba(),
    color(srgb …), #hex, transparent) and alpha compositing;
  * WCAG 2.x relative luminance and contrast ratio (never rounded before a
    comparison: 4.478:1 fails 4.5:1);
  * large-scale text (≥ 24 px, or ≥ 18.66 px at weight ≥ 700);
  * a minimal PNG decoder (8-bit, non-interlaced: what Chromium screenshots are)
    and two pixel measurements on screenshot crops: the contrast of text against
    what is actually behind its glyphs, and the flat-colour palette of a graphic;
  * loading the per-criterion measurement scripts (capture/js/c_1_4_*.js) into
    the live page. They are READ-ONLY, like klar_extract.js.

Pillow and numpy are not dependencies: crops are small and decoded in Python.
"""

from __future__ import annotations

import logging
import math
import re
import struct
import zlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

RGB = tuple[int, int, int]
RGBA = tuple[float, float, float, float]

JS_DIR = Path(__file__).resolve().parent.parent / "capture" / "js"
LIB_JS = "c_1_4_3_colour_lib.js"

WHITE: RGB = (255, 255, 255)
LARGE_PX = 24.0  # 18 pt
LARGE_BOLD_PX = 18.66  # 14 pt (18.666… px); 18 px bold is NOT large
BOLD = 700
TEXT_MIN = 4.5
TEXT_LARGE_MIN = 3.0
NON_TEXT_MIN = 3.0
LINK_TEXT_MIN = 3.0  # 1.4.1, G183: link colour vs surrounding text colour

# --- parsing -------------------------------------------------------------------------------

_NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?%?"
_RGB_FN = re.compile(rf"rgba?\(\s*({_NUM})[\s,]+({_NUM})[\s,]+({_NUM})(?:\s*[,/]\s*({_NUM}))?\s*\)", re.I)
_SRGB_FN = re.compile(rf"color\(\s*srgb\s+({_NUM})\s+({_NUM})\s+({_NUM})(?:\s*/\s*({_NUM}))?\s*\)", re.I)
_HEX = re.compile(r"#([0-9a-f]{3,8})\b", re.I)
_ANY_COLOUR = re.compile(rf"rgba?\([^)]*\)|color\(\s*srgb[^)]*\)|#[0-9a-f]{{3,8}}\b|\btransparent\b", re.I)


def _num(v: str, scale: float) -> float:
    v = v.strip()
    if v.endswith("%"):
        return float(v[:-1]) / 100 * scale
    return float(v)


def parse_color(css: str | None) -> RGBA | None:
    """A CSS colour → (r, g, b, a) with r, g, b in 0..255 and a in 0..1, or None
    for forms we do not convert (oklch(), lab(), currentcolor, keywords…)."""
    s = (css or "").strip().lower()
    if not s:
        return None
    if s == "transparent":
        return (0.0, 0.0, 0.0, 0.0)
    m = _RGB_FN.fullmatch(s)
    if m:
        r, g, b = (_num(x, 255) for x in m.groups()[:3])
        a = _num(m.group(4), 1) if m.group(4) else 1.0
        return (_clamp(r), _clamp(g), _clamp(b), max(0.0, min(1.0, a)))
    m = _SRGB_FN.fullmatch(s)
    if m:
        r, g, b = (_num(x, 1) * 255 for x in m.groups()[:3])
        a = _num(m.group(4), 1) if m.group(4) else 1.0
        return (_clamp(r), _clamp(g), _clamp(b), max(0.0, min(1.0, a)))
    m = _HEX.fullmatch(s)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) not in (6, 8):
            return None
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return (float(int(h[0:2], 16)), float(int(h[2:4], 16)), float(int(h[4:6], 16)), a)
    return None


def colours_in(css: str | None) -> list[RGBA]:
    """Every parseable colour in a value such as `text-shadow` or `box-shadow`."""
    out = []
    for m in _ANY_COLOUR.finditer(css or ""):
        c = parse_color(m.group(0))
        if c is not None:
            out.append(c)
    return out


def _clamp(v: float) -> float:
    return max(0.0, min(255.0, v))


def rgb(c: RGBA | RGB) -> RGB:
    return (round(c[0]), round(c[1]), round(c[2]))


def hex_of(c: RGBA | RGB) -> str:
    r, g, b = rgb(c)
    return f"#{r:02x}{g:02x}{b:02x}"


# --- compositing and contrast ---------------------------------------------------------------

def over(top: RGBA, below: RGB) -> RGB:
    """Alpha-composite a colour over an opaque one."""
    a = top[3]
    return (top[0] * a + below[0] * (1 - a), top[1] * a + below[1] * (1 - a), top[2] * a + below[2] * (1 - a))  # type: ignore[return-value]


def composite(layers_top_first: list[RGBA], base: RGB = WHITE) -> RGB:
    """Composite background colour layers (topmost first) over `base`."""
    out: Any = base
    for layer in reversed(layers_top_first):
        out = over(layer, out)
    return out


def _channel(v: float) -> float:
    c = v / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(c: RGBA | RGB) -> float:
    """WCAG relative luminance."""
    return 0.2126 * _channel(c[0]) + 0.7152 * _channel(c[1]) + 0.0722 * _channel(c[2])


def contrast(a: RGBA | RGB, b: RGBA | RGB) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def fmt_ratio(r: float, threshold: float | None = None) -> str:
    """'4.48:1', but never display a value that seems to meet a threshold it misses
    (4.4996 → '4.499:1', not '4.50:1')."""
    s = f"{r:.2f}"
    if threshold is not None and r < threshold <= float(s):
        s = f"{math.floor(r * 1000) / 1000:.3f}"
    return s.rstrip("0").rstrip(".") + ":1" if "." in s else s + ":1"


def is_large_text(font_px: float, weight: float) -> bool:
    return font_px >= LARGE_PX or (font_px >= LARGE_BOLD_PX and weight >= BOLD)


def text_threshold(font_px: float, weight: float) -> float:
    return TEXT_LARGE_MIN if is_large_text(font_px, weight) else TEXT_MIN


def saturation(c: RGBA | RGB) -> float:
    """HSV-style chroma share (0 = grey, 1 = fully saturated)."""
    hi, lo = max(c[0], c[1], c[2]), min(c[0], c[1], c[2])
    return 0.0 if hi <= 0 else (hi - lo) / hi


def chroma(c: RGBA | RGB) -> float:
    return (max(c[0], c[1], c[2]) - min(c[0], c[1], c[2])) / 255


# --- PNG ---------------------------------------------------------------------------------------

@dataclass
class Bitmap:
    w: int
    h: int
    px: bytes  # RGB, 3 bytes per pixel, row-major

    def at(self, x: int, y: int) -> RGB:
        i = (y * self.w + x) * 3
        return (self.px[i], self.px[i + 1], self.px[i + 2])


MAX_PIXELS = 600_000


def decode_png(data: bytes) -> Bitmap:
    """8-bit, non-interlaced PNG (grey, grey+alpha, RGB, RGBA) → opaque RGB over white."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos, idat = 8, []
    w = h = depth = ctype = interlace = None
    while pos + 8 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        kind = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", chunk)
        elif kind == b"IDAT":
            idat.append(chunk)
        elif kind == b"IEND":
            break
    if w is None or depth != 8 or interlace != 0 or ctype not in (0, 2, 4, 6):
        raise ValueError(f"unsupported PNG (depth={depth}, colour type={ctype}, interlace={interlace})")
    if w * h > MAX_PIXELS:
        raise ValueError(f"crop too large ({w}x{h})")
    bpp = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    stride = w * bpp
    expected = h * (1 + stride)
    # bounded inflate: never more than the header announces (w*h is capped above)
    raw = zlib.decompressobj().decompress(b"".join(idat), expected)
    if len(raw) < expected:
        raise ValueError("truncated PNG data")
    prev = bytearray(stride)
    rows = bytearray()
    i = 0
    for _ in range(h):
        f = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        if f == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif f == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif f == 3:
            for x in range(stride):
                left = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((left + prev[x]) >> 1)) & 255
        elif f == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[x] = (line[x] + pred) & 255
        rows += line
        prev = line
    if ctype == 2:
        return Bitmap(w, h, bytes(rows))
    out = bytearray(w * h * 3)
    for p in range(w * h):
        if ctype == 0:
            g = rows[p]
            out[p * 3:p * 3 + 3] = bytes((g, g, g))
        elif ctype == 4:
            g, a = rows[p * 2], rows[p * 2 + 1]
            v = (g * a + 255 * (255 - a)) // 255
            out[p * 3:p * 3 + 3] = bytes((v, v, v))
        else:
            r, g, b, a = rows[p * 4:p * 4 + 4]
            out[p * 3:p * 3 + 3] = bytes(((r * a + 255 * (255 - a)) // 255, (g * a + 255 * (255 - a)) // 255,
                                          (b * a + 255 * (255 - a)) // 255))
    return Bitmap(w, h, bytes(out))


def encode_png(bm: Bitmap) -> bytes:
    """RGB bitmap → PNG (tests and synthetic crops)."""
    raw = b"".join(b"\x00" + bm.px[y * bm.w * 3:(y + 1) * bm.w * 3] for y in range(bm.h))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", bm.w, bm.h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


# --- pixel measurements --------------------------------------------------------------------------

@dataclass
class GlyphContrast:
    """Contrast of a text colour against the pixels actually behind its glyphs."""
    pixels: int  # glyph pixels measured
    low: float  # 10th percentile ratio
    median: float
    high: float  # 90th percentile ratio
    minimum: float
    maximum: float
    share_ok: float  # share of glyph pixels whose background gives ≥ the threshold


def glyph_contrast(black_text: Bitmap, white_text: Bitmap, without_text: Bitmap, fg: RGBA,
                   threshold: float) -> GlyphContrast | None:
    """Three crops of the same element: text forced black, text forced white, text
    transparent. Where the black and the white rendering differ by at least half the
    full range, a glyph covers the pixel (whatever the background: white text on a
    white area is found too); its background is read from the text-less crop and
    compared with the real text colour. None when the crops differ in size or show
    no glyphs."""
    if not ((black_text.w, black_text.h) == (white_text.w, white_text.h) == (without_text.w, without_text.h)):
        return None
    ratios: list[float] = []
    cache: dict[RGB, float] = {}
    n = black_text.w * black_text.h
    k_, w_, b = black_text.px, white_text.px, without_text.px
    for p in range(n):
        i = p * 3
        cover = abs(w_[i] - k_[i]) + abs(w_[i + 1] - k_[i + 1]) + abs(w_[i + 2] - k_[i + 2])
        if cover < 0.5 * 765:
            continue
        bg = (b[i], b[i + 1], b[i + 2])
        r = cache.get(bg)
        if r is None:
            r = cache[bg] = contrast(over(fg, bg), bg)
        ratios.append(r)
    if len(ratios) < 12:
        return None
    ratios.sort()
    k = len(ratios)

    def pct(q: float) -> float:
        return ratios[min(k - 1, max(0, int(q * (k - 1))))]

    ok = sum(1 for r in ratios if r >= threshold) / k
    return GlyphContrast(pixels=k, low=pct(0.10), median=pct(0.5), high=pct(0.90), minimum=ratios[0],
                         maximum=ratios[-1], share_ok=round(ok, 3))


@dataclass
class Palette:
    background: RGB
    colours: list[tuple[RGB, float]]  # (colour, share of pixels), background excluded, ≥ min_share
    flat_share: float  # share of pixels covered by the 12 most common (quantised) colours
    distinct_saturated: int  # palette colours with a clear hue


def palette(bm: Bitmap, *, min_share: float = 0.004, step: int = 1) -> Palette:
    """Dominant flat colours of a graphic (quantised to 5 bits per channel).
    The most common colour is taken as the background."""
    counts: Counter = Counter()
    px = bm.px
    total = 0
    for y in range(0, bm.h, step):
        row = y * bm.w * 3
        for x in range(0, bm.w, step):
            i = row + x * 3
            counts[(px[i] >> 3, px[i + 1] >> 3, px[i + 2] >> 3)] += 1
            total += 1
    if not total:
        return Palette(WHITE, [], 0.0, 0)
    common = counts.most_common()
    to_rgb = lambda q: (q[0] * 8 + 4, q[1] * 8 + 4, q[2] * 8 + 4)  # noqa: E731
    background = to_rgb(common[0][0])
    flat = sum(c for _, c in common[:12]) / total
    colours: list[tuple[RGB, float]] = []
    for q, c in common[1:]:
        share = c / total
        if share < min_share:
            break
        col = to_rgb(q)
        if any(sum(abs(col[j] - k[j]) for j in range(3)) < 40 for k, _ in colours) or \
                sum(abs(col[j] - background[j]) for j in range(3)) < 40:
            continue  # anti-aliasing shade of a colour already listed
        colours.append((col, round(share, 4)))
    sat = sum(1 for col, _ in colours if saturation(col) >= 0.35 and 0.12 <= max(col) / 255)
    return Palette(background, colours, round(flat, 3), sat)


# --- the live measurement scripts ---------------------------------------------------------------

_JS_CACHE: dict[str, str] = {}


def _js_source(name: str) -> str:
    if name not in _JS_CACHE:
        _JS_CACHE[name] = (JS_DIR / name).read_text(encoding="utf-8")
    return _JS_CACHE[name]


def measure(page: Any, name: str, arg: Any = None) -> Any:
    """Run capture/js/<name> (a function `(arg, K) => …` where K is the shared colour
    library) in the live page; None when the page is not live or the script fails."""
    if getattr(page, "live", None) is None:
        return None
    # The wrapper restores the scroll position whatever the script does (the library
    # scrolls to measure; the live page is shared with the other checks).
    src = ("(arg) => { const sx = window.scrollX, sy = window.scrollY;\n const K = "
           + _js_source(LIB_JS).strip().rstrip(";")
           + ";\n try { return (" + _js_source(name).strip().rstrip(";") + ")(arg, K); }"
           + "\n finally { window.scrollTo(sx, sy); } }")
    try:
        return page.evaluate(src, arg)
    except Exception as exc:
        log.warning("measurement script %s failed: %s", name, exc)
        return None


def records(page: Any, key: str, name: str, arg: Any = None) -> list[dict]:
    """Element records for one check, cached in page.elements[key] (lists of dicts
    with a selector, like the extractor's). Unit tests put records there directly."""
    if key in page.elements:
        return page.elements[key]
    out = measure(page, name, arg)
    if isinstance(out, dict):
        for k, v in out.items():
            if isinstance(v, list):
                page.elements[f"{key}.{k}" if k != "items" else key] = v
        return page.elements.get(key, [])
    page.elements[key] = out if isinstance(out, list) else []
    return page.elements[key]


def element_png(page: Any, selector: str, *, text_colour: str | None = None) -> bytes | None:
    """PNG bytes of one element's box (CSS pixels). With `text_colour` ("transparent",
    "#000", "#fff"), a temporary screenshot-only stylesheet repaints the element's
    text (Playwright's `style` option: nothing is written into the audited DOM)."""
    if getattr(page, "live", None) is None:
        return None
    style = None
    if text_colour:
        style = (f"{selector}, {selector} * {{ color: {text_colour} !important; -webkit-text-fill-color: "
                 f"{text_colour} !important; text-shadow: none !important; text-decoration-color: transparent "
                 "!important; caret-color: transparent !important; }")
    try:
        loc = page.live.locator(selector).first
        box = loc.bounding_box(timeout=3000)
        if not box or box["width"] < 2 or box["height"] < 2 or box["width"] * box["height"] > MAX_PIXELS:
            return None
        kwargs: dict[str, Any] = dict(animations="disabled", timeout=5000, scale="css", caret="hide")
        if style:
            kwargs["style"] = style
        return loc.screenshot(**kwargs)
    except Exception as exc:
        log.info("element screenshot of %s failed: %s", selector, exc)
        return None


def save_crop(page: Any, name: str, png: bytes) -> str | None:
    """Store crop bytes as <scan_dir>/crops/<name>.png (what the UI shows)."""
    rel = f"crops/{name}.png"
    try:
        path = Path(page.scan_dir) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(png)
        return rel
    except OSError as exc:
        log.info("could not store crop %s: %s", rel, exc)
        return None


def load_crop(page: Any, rel: str | None) -> Bitmap | None:
    if not rel:
        return None
    try:
        return decode_png((Path(page.scan_dir) / rel).read_bytes())
    except (OSError, ValueError, zlib.error) as exc:
        log.info("could not decode crop %s: %s", rel, exc)
        return None


def axe_nodes(page: Any, rule_id: str) -> dict[str, dict]:
    """selector → {group: 'violation' | 'incomplete', html, summary} for one axe rule
    (selectors are canonical: capture/axe.py rewrites them with cssPath)."""
    out: dict[str, dict] = {}
    axe = getattr(page, "axe", None) or {}
    for group, label in (("incomplete", "incomplete"), ("violations", "violation")):
        for rule in axe.get(group, []):
            if rule.get("id") != rule_id:
                continue
            for node in rule.get("nodes", []):
                sel = node.get("selector")
                if sel:
                    out[sel] = {"group": label, "html": node.get("html", ""),
                                "summary": " ".join((node.get("failureSummary") or "").split())}
    return out
