/* Klar. colour facts library for the visual checks (1.4.1, 1.4.3, 1.4.5, 1.4.11).
 *
 * Evaluated as an expression by klar/checks/colour.py and passed as `K` to the
 * per-criterion scripts (c_1_4_*.js). READ-ONLY: it never changes the audited DOM.
 * It may scroll the window to measure what lies behind an element (elementsFromPoint
 * only sees the viewport); the Python wrapper (colour.measure) restores the scroll
 * position in a `finally`, whatever the script does.
 * Colours are returned as computed-style strings; all colour arithmetic (compositing,
 * luminance, contrast) is done in Python, where it is unit-tested.
 */
(() => {
  const MAX_HTML = 2000;
  const norm = (s) => (s || '').replace(/[\s ​]+/g, ' ').trim();
  const cs = (el, pseudo) => getComputedStyle(el, pseudo || null);
  const path = (el) => window.__klar.cssPath(el);
  const visible = (el) => window.__klar.isVisible(el);
  const MEDIA = new Set(['img', 'picture', 'video', 'canvas', 'iframe', 'object', 'embed', 'svg']);
  const LETTER = /[\p{L}\p{N}]/u;

  function outer(el) {
    const h = el.outerHTML || '';
    return h.length > MAX_HTML ? h.slice(0, MAX_HTML) : h;
  }

  function transparent(c) {
    return !c || c === 'transparent' || /^rgba\([^)]*[,/]\s*0\s*\)$/.test(c);
  }

  function rect(el) {
    const r = el.getBoundingClientRect();
    return { x: Math.round(r.left + window.scrollX), y: Math.round(r.top + window.scrollY),
             w: Math.round(r.width), h: Math.round(r.height) };
  }

  function ownText(el) {
    let t = '';
    for (const n of el.childNodes) if (n.nodeType === 3) t += n.nodeValue;
    return norm(t);
  }

  function opacity(el) {
    let o = 1;
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) o *= parseFloat(cs(n).opacity || '1');
    return Math.round(o * 1000) / 1000;
  }

  /** Bring a document-y position into the viewport (elementsFromPoint needs it). */
  function into(docY, h) {
    const top = docY - window.scrollY;
    if (top >= 0 && top + Math.min(h, 40) <= window.innerHeight) return;
    window.scrollTo(0, Math.max(0, docY - Math.floor(window.innerHeight / 3)));
  }

  /** One background layer of element `n`, or null when it paints nothing. */
  function layerOf(n) {
    const st = cs(n);
    if (st.backgroundImage && st.backgroundImage !== 'none') {
      return { img: st.backgroundImage.slice(0, 160), c: st.backgroundColor, gradient: !/url\(/.test(st.backgroundImage),
               sel: path(n) };
    }
    if (!transparent(st.backgroundColor)) return { c: st.backgroundColor };
    return null;
  }

  function opaque(c) {
    return /^rgb\(/.test(c) || /^#[0-9a-f]{6}$/i.test(c) || /^color\(srgb [^/]*\)$/.test(c);
  }

  /** Background layers behind `el` (top first), ending at the first opaque colour.
   *  With a viewport point: the paint stack at that point (siblings painted below
   *  count: text over an <img>, an absolutely positioned caption…). Without: ancestors. */
  function layers(el, point) {
    let stack = null;
    if (point) {
      try {
        const all = document.elementsFromPoint(point.x, point.y);
        const i = all.indexOf(el);
        if (i >= 0) stack = all.slice(i);
      } catch (e) { stack = null; }
    }
    const viaPoint = !!stack;
    if (!stack) { stack = []; for (let n = el; n && n.nodeType === 1; n = n.parentElement) stack.push(n); }
    const out = [];
    for (const n of stack) {
      const tag = n.localName;
      if (n !== el && !n.contains(el) && (MEDIA.has(tag) || (n.closest && n.closest('svg')))) {
        out.push({ media: tag, sel: path(n.closest('svg') || n) });
        return { layers: out, via_point: viaPoint };
      }
      if (n !== el && !n.contains(el) && el.contains(n)) continue;
      const l = layerOf(n);
      if (!l) continue;
      out.push(l);
      if (l.img || opaque(l.c)) break;
    }
    return { layers: out, via_point: viaPoint };
  }

  /** Background behind a box, measured at its centre (or just outside it with `outside`). */
  function layersAround(el, outside) {
    const r = el.getBoundingClientRect();
    into(r.top + window.scrollY, r.height);
    const b = el.getBoundingClientRect();
    if (outside) {
      const parent = el.parentElement || el;
      const p = { x: b.left - 3, y: b.top + b.height / 2 };
      if (p.x < 0) p.x = b.right + 3;
      let res = null;
      try {
        const all = document.elementsFromPoint(p.x, p.y).filter((n) => n !== el && !el.contains(n));
        if (all.length) {
          const top = all[0];
          res = layers(top, null);
          if (top !== parent && !top.contains(el)) res.via_point = true;
        }
      } catch (e) { res = null; }
      return res || layers(parent, null);
    }
    return layers(el, { x: b.left + b.width / 2, y: b.top + b.height / 2 });
  }

  function inactive(el) {
    if (el.closest('[aria-disabled="true"]')) return true;
    if (el.closest('fieldset[disabled]')) return true;
    const ctl = el.closest('button, input, select, textarea, option, optgroup');
    if (ctl && ctl.disabled) return true;
    const lab = el.closest('label');
    if (lab && lab.control && lab.control.disabled) return true;
    return false;
  }

  function hiddenFromAT(el) {
    return !!el.closest('[aria-hidden="true"], [role="presentation"], [role="none"]');
  }

  function homeLink(el) {
    const a = el.closest('a[href]');
    if (!a) return false;
    if ((a.getAttribute('rel') || '').split(/\s+/).includes('home')) return true;
    try {
      const u = new URL(a.href, location.href);
      const here = new URL(location.href);
      if (u.origin !== here.origin && u.protocol !== 'file:') return false;
      return /^\/?(?:index\.html?)?$/.test(u.pathname) || u.pathname.replace(/\/index\.html?$/, '/') === '/';
    } catch (e) { return false; }
  }

  /** Signals that a text or graphic may be a logo / brand mark (never a verdict). */
  function brand(el) {
    const sig = [];
    if (homeLink(el)) sig.push('links_to_home_page');
    if (el.closest('header, [role="banner"]')) sig.push('in_page_header');
    for (let n = el, i = 0; n && n.nodeType === 1 && i < 4; n = n.parentElement, i++) {
      const s = ((n.id || '') + ' ' + (typeof n.className === 'string' ? n.className : '')).toLowerCase();
      if (/logo|brand|wordmark|signet|emblem/.test(s)) { sig.push('logo_class_or_id'); break; }
    }
    return sig;
  }

  // Normalise any CSS colour (keywords, hsl(), #hex…) through an UNATTACHED canvas
  // context: nothing is added to the audited DOM.
  const ctx2d = (() => { try { return document.createElement('canvas').getContext('2d'); } catch (e) { return null; } })();
  function colour(tok) {
    if (!ctx2d || !tok) return '';
    const probe = '#010203';
    ctx2d.fillStyle = probe;
    ctx2d.fillStyle = tok;
    const v = String(ctx2d.fillStyle);
    return v === probe && tok.trim().toLowerCase() !== probe ? '' : v;
  }
  /** The first token of a CSS value that is a colour (box-shadow, outline shorthand…). */
  function firstColour(str) {
    const toks = String(str || '').match(/(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color)\([^)]*\)|#[0-9a-f]{3,8}\b|[a-z]+/gi) || [];
    for (const t of toks) {
      if (/^(inset|none|currentcolor|transparent|initial|inherit|unset|solid|dashed|dotted|double|auto)$/i.test(t)) continue;
      const c = colour(t);
      if (c) return c;
    }
    return '';
  }

  function lang(el) {
    return window.__klar.inheritedLang(el);
  }

  return { norm, cs, path, visible, outer, transparent, rect, ownText, opacity, into, layers, layersAround,
           layerOf, inactive, hiddenFromAT, homeLink, brand, lang, colour, firstColour, LETTER, MEDIA };
})()
