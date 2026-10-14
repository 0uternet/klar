/* 1.4.1 Use of Color: facts about colour cues (READ-ONLY).
 *
 *  links   links inside a block of text (ACT/axe link-in-text-block applicability):
 *          non-colour cues the link has and the surrounding text lacks, and the two colours.
 *  states  groups of controls with an "on" member (aria-pressed / aria-selected /
 *          aria-current / aria-checked): what differs between on and off members.
 *  groups  tables, lists and forms in which some items have a saturated colour the
 *          others lack (candidate colour coding; the model judges its meaning).
 *  graphics  img / svg / canvas large enough to be a chart or map.
 */
(arg, K) => {
  const out = { items: [], states: [], groups: [], graphics: [] };
  const LINKISH = 'a[href], [role="link"]';
  const NAV = 'nav, [role="navigation"], [role="menu"], [role="menubar"], [role="tablist"], header, footer';

  function decoLines(el) {
    return (K.cs(el).textDecorationLine || 'none').split(' ').filter((x) => x && x !== 'none');
  }

  function cueStyle(el) {
    const st = K.cs(el);
    const b = ['Top', 'Right', 'Bottom', 'Left'].map((s) => {
      const w = parseFloat(st['border' + s + 'Width']) || 0;
      const style = st['border' + s + 'Style'];
      return w > 0 && style !== 'none' && style !== 'hidden' && !K.transparent(st['border' + s + 'Color']) ? s.toLowerCase() : null;
    }).filter(Boolean);
    return {
      deco: decoLines(el), weight: parseFloat(st.fontWeight) || 400, style: st.fontStyle, family: st.fontFamily,
      size: parseFloat(st.fontSize) || 0, transform: st.textTransform, variant: st.fontVariantCaps || 'normal',
      borders: b, outline: (st.outlineStyle !== 'none' && parseFloat(st.outlineWidth) > 0) ? st.outlineColor : '',
      shadow: st.boxShadow && st.boxShadow !== 'none' ? st.boxShadow : '',
      bgimg: st.backgroundImage && st.backgroundImage !== 'none', bg: st.backgroundColor, color: st.color,
    };
  }

  function pseudoCue(el) {
    for (const p of ['::before', '::after']) {
      const st = K.cs(el, p);
      const c = st.content;
      if (c && c !== 'none' && c !== 'normal' && c !== '""' && c !== "''" && st.display !== 'none') return p;
    }
    return '';
  }

  // --- links in text blocks ----------------------------------------------------------
  const seenBlocks = new Map();
  for (const a of document.querySelectorAll(LINKISH)) {
    if (out.items.length >= 150) break;
    if (!K.visible(a)) continue;
    const st = K.cs(a);
    if (!(st.display || '').startsWith('inline') || st.display === 'inline-flex' || st.display === 'inline-grid') continue;
    const text = K.norm(a.innerText || a.textContent);
    if (!K.LETTER.test(text)) continue;
    const block = window.__klar.nearestBlock(a.parentElement || a);
    if (!block || block === document.body || block.closest(NAV)) continue;
    let around = seenBlocks.get(block);
    if (around === undefined) {
      let t = '';
      const w = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);
      let n;
      while ((n = w.nextNode())) {
        const p = n.parentElement;
        if (p && !p.closest(LINKISH) && !p.closest('script,style') && K.visible(p)) t += n.nodeValue;
      }
      around = K.norm(t);
      seenBlocks.set(block, around);
    }
    if ((around.match(/\p{L}/gu) || []).length < 12) continue;  // not inside a text block
    const parent = a.parentElement;
    const own = cueStyle(a);
    const ctx = cueStyle(parent);
    const cues = [];
    const innerDeco = Array.from(a.querySelectorAll('*')).some((d) => decoLines(d).length && K.visible(d));
    if ((own.deco.length && own.deco.join() !== ctx.deco.join()) || innerDeco) cues.push('text_decoration');
    if (own.borders.length) cues.push('border');
    if (own.outline) cues.push('outline');
    if (own.shadow) cues.push('box_shadow');
    if (own.bgimg) cues.push('background_image');
    if (!K.transparent(own.bg) && own.bg !== ctx.bg) cues.push('background:' + own.bg);
    if (Math.abs(own.weight - ctx.weight) >= 300 || (own.weight >= 600) !== (ctx.weight >= 600)) cues.push('font_weight');
    if (own.style !== ctx.style) cues.push('font_style');
    if (own.family !== ctx.family) cues.push('font_family');
    if (ctx.size && Math.abs(own.size - ctx.size) / ctx.size >= 0.2) cues.push('font_size');
    if (own.transform !== ctx.transform || own.variant !== ctx.variant) cues.push('text_transform');
    if (pseudoCue(a)) cues.push('icon' + pseudoCue(a));
    if (a.querySelector('img, svg')) cues.push('icon_image');
    const bg = K.layers(a, null);
    out.items.push({
      selector: K.path(a), html: K.outer(a), text: text.slice(0, 200), sentence: window.__klar.sentenceOf
        ? K.norm(window.__klar.sentenceOf(a) || '').slice(0, 300) : '', color: own.color, text_color: ctx.color,
      layers: bg.layers, cues, lang: K.lang(a), block: K.path(block),
    });
  }

  // --- state groups (selected / pressed / current) -------------------------------------
  const STATE = [['aria-pressed', 'true'], ['aria-selected', 'true'], ['aria-current', null], ['aria-checked', 'true']];
  const groupsSeen = new Set();
  for (const [attr, onVal] of STATE) {
    for (const on of document.querySelectorAll('[' + attr + ']')) {
      const v = on.getAttribute(attr);
      if (onVal ? v !== onVal : (v === 'false' || v === '')) continue;
      const parent = on.parentElement;
      if (!parent || groupsSeen.has(parent) || !K.visible(on)) continue;
      const sibs = Array.from(parent.querySelectorAll(':scope > *, :scope > * > *'))
        .filter((s) => s !== on && !s.contains(on) && !on.contains(s) && s.localName === on.localName && K.visible(s));
      const off = sibs.find((s) => attr === 'aria-current' ? !s.hasAttribute(attr) || s.getAttribute(attr) === 'false'
        : s.getAttribute(attr) === 'false' || !s.hasAttribute(attr));
      if (!off) continue;
      groupsSeen.add(parent);
      const a = cueStyle(on), b = cueStyle(off);
      const diffs = [];
      if (a.deco.join() !== b.deco.join()) diffs.push('text_decoration');
      // a border is a state cue when one member has none, or the members differ by two sides or
      // more (a missing side between adjacent segments is structure, not state)
      if ((a.borders.length === 0) !== (b.borders.length === 0) || Math.abs(a.borders.length - b.borders.length) >= 2) diffs.push('border_shape');
      if (a.outline !== b.outline && (a.outline || b.outline)) diffs.push('outline');
      if (a.weight !== b.weight) diffs.push('font_weight');
      if (a.style !== b.style) diffs.push('font_style');
      if (a.size !== b.size) diffs.push('font_size');
      if (a.transform !== b.transform) diffs.push('text_transform');
      if (pseudoCue(on) !== pseudoCue(off) || (pseudoCue(on) && K.cs(on, pseudoCue(on)).content !== K.cs(off, pseudoCue(on)).content)) diffs.push('icon');
      if (on.querySelectorAll('img, svg').length !== off.querySelectorAll('img, svg').length) diffs.push('icon_image');
      if (a.shadow !== b.shadow && (a.shadow || b.shadow)) diffs.push('box_shadow');
      out.states.push({
        selector: K.path(parent), html: K.outer(parent), text: K.norm(parent.innerText).slice(0, 300), attr,
        on: K.path(on), off: K.path(off), on_text: K.norm(on.innerText).slice(0, 80), off_text: K.norm(off.innerText).slice(0, 80),
        on_color: a.color, off_color: b.color, on_layers: K.layers(on, null).layers, off_layers: K.layers(off, null).layers,
        diffs, lang: K.lang(parent),
      });
    }
  }

  // --- colour-coded groups ---------------------------------------------------------------
  /** Chroma 0..1 (max - min channel): near-black navy or grey text has little. */
  function chroma(c) {
    const m = (c || '').match(/rgba?\(([^)]+)\)/);
    if (!m) return 0;
    const v = m[1].split(/[\s,/]+/).map(Number);
    if (v.length > 3 && v[3] === 0) return 0;
    return (Math.max(v[0], v[1], v[2]) - Math.min(v[0], v[1], v[2])) / 255;
  }
  /** Colours an item has that its container does not (inherited colours are not marks). */
  function marks(el, box) {
    const st = K.cs(el), bs = K.cs(box);
    const m = [];
    if (chroma(st.color) >= 0.25 && st.color !== bs.color && !el.closest(LINKISH)) m.push('text:' + st.color);
    if (!K.transparent(st.backgroundColor) && chroma(st.backgroundColor) >= 0.09 && st.backgroundColor !== bs.backgroundColor) {
      m.push('bg:' + st.backgroundColor);
    }
    for (const s of ['Top', 'Bottom', 'Left', 'Right']) {
      if ((parseFloat(st['border' + s + 'Width']) || 0) >= 1 && st['border' + s + 'Style'] !== 'none' &&
          chroma(st['border' + s + 'Color']) >= 0.25) { m.push('border:' + st['border' + s + 'Color']); break; }
    }
    return m;
  }
  const CONTAINERS = 'table, ul, ol, dl, form, fieldset, [role="list"], [role="grid"], [role="table"]';
  for (const box of document.querySelectorAll(CONTAINERS)) {
    if (out.groups.length >= 30) break;
    if (!K.visible(box) || box.closest(NAV) || box.parentElement && box.parentElement.closest(CONTAINERS + ', p')) continue;
    const items = box.localName === 'form' || box.localName === 'fieldset'
      ? box.querySelectorAll('label, input, select, textarea, legend, p, span, small, strong, em')
      : box.querySelectorAll('td, li, dt, dd, [role="cell"], [role="gridcell"], [role="listitem"]');  // header cells: theme
    const per = [];
    let marked = 0, empty = 0;
    const kinds = new Set();
    for (const it of items) {
      if (!K.visible(it)) continue;
      let m = marks(it, box);
      if (!m.length) {
        for (const d of it.querySelectorAll('span, strong, em, b, i, small, time, mark, abbr')) {
          if (K.visible(d)) { m = marks(d, box); if (m.length) break; }
        }
      }
      per.push(m.join('|'));
      if (m.length) {
        marked++;
        m.forEach((x) => kinds.add(x));
        if (!K.LETTER.test(K.norm(it.innerText || it.value || ''))) empty++;
      }
    }
    if (!marked || per.length < 2) continue;
    const distinct = new Set(per);
    if (distinct.size < 2) continue;  // every item looks the same: no coding by colour
    out.groups.push({
      selector: K.path(box), tag: box.localName, html: K.outer(box), text: K.norm(box.innerText).slice(0, 600),
      items: per.length, marked, marked_without_text: empty, colours: Array.from(kinds).slice(0, 8),
      rect: K.rect(box), lang: K.lang(box),
    });
  }

  // --- graphics -------------------------------------------------------------------------------
  for (const g of document.querySelectorAll('img, svg, canvas, [role="img"], input[type="image"]')) {
    if (out.graphics.length >= 40) break;
    if (g.localName !== 'svg' && g.closest('svg')) continue;
    if (!K.visible(g)) continue;
    const r = g.getBoundingClientRect();
    if (r.width < 120 || r.height < 80) continue;
    out.graphics.push({
      selector: K.path(g), tag: g.localName, html: K.outer(g),
      alt: g.getAttribute('alt') || g.getAttribute('aria-label') || '', rect: K.rect(g), lang: K.lang(g),
      caption: (() => { const f = g.closest('figure'); const c = f && f.querySelector('figcaption'); return c ? K.norm(c.innerText).slice(0, 300) : ''; })(),
    });
  }
  return out;
}
