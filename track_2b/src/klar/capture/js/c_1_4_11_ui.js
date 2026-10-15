/* 1.4.11 Non-text Contrast: colours of component boundaries, icons, focus styles
 * and graphics (READ-ONLY: focus styles are read from the author's stylesheets via
 * the CSSOM, no element is focused).
 *
 *  items     text inputs, selects, textareas (boundary) and custom (appearance:none or
 *            ARIA) checkboxes / radios / switches; native ones are drawn by the browser.
 *  icons     controls without visible text whose only identifying visual is an icon
 *            (inline SVG shapes, an icon-font glyph, an <img> or background image).
 *  focus     author :focus / :focus-visible rules that draw an outline, box-shadow or border.
 *  graphics  img / svg / canvas ≥ 100×60 outside controls (charts, maps, diagrams).
 */
(arg, K) => {
  const out = { items: [], icons: [], focus: [], graphics: [] };
  const sx = window.scrollX, sy = window.scrollY;  // restored at the end
  const TEXTISH = new Set(['text', 'search', 'email', 'url', 'tel', 'password', 'number', 'date', 'datetime-local',
                           'month', 'week', 'time']);
  const SIDES = ['Top', 'Right', 'Bottom', 'Left'];

  function borders(st) {
    return SIDES.map((s) => ({ side: s.toLowerCase(), w: parseFloat(st['border' + s + 'Width']) || 0,
                              style: st['border' + s + 'Style'], c: st['border' + s + 'Color'] }))
      .filter((b) => b.w >= 1 && b.style !== 'none' && b.style !== 'hidden');
  }

  function shapes(svg) {
    const res = {};
    let gradient = false;
    for (const s of svg.querySelectorAll('path, circle, rect, line, polyline, polygon, ellipse, use')) {
      const st = K.cs(s);
      if (st.display === 'none' || st.visibility === 'hidden' || parseFloat(st.opacity) === 0) continue;
      const add = (c, op, w) => {
        if (!c || c === 'none') return;
        if (/url\(/.test(c)) { gradient = true; return; }
        if (parseFloat(op) === 0) return;
        const k = c + '|' + (parseFloat(op) || 1);
        res[k] = (res[k] || 0) + w;
      };
      add(st.fill, st.fillOpacity, 1);
      const sw = parseFloat(st.strokeWidth) || 0;
      if (sw > 0) add(st.stroke, st.strokeOpacity, Math.max(1, sw));
    }
    return { colours: Object.entries(res).map(([k, w]) => ({ c: k.split('|')[0], a: parseFloat(k.split('|')[1]), w }))
      .sort((a, b) => b.w - a.w).slice(0, 12), gradient };
  }

  // --- input boundaries and custom toggles --------------------------------------------
  for (const el of document.querySelectorAll('input, textarea, select, [role="textbox"], [role="combobox"], [role="checkbox"], [role="radio"], [role="switch"]')) {
    if (out.items.length >= 120) break;
    if (!K.visible(el)) continue;
    const tag = el.localName;
    const type = tag === 'input' ? (el.getAttribute('type') || 'text').toLowerCase() : tag;
    const st = K.cs(el);
    let kind = null;
    if (tag === 'textarea' || tag === 'select' || (tag === 'input' && TEXTISH.has(type))) kind = 'input';
    else if (tag === 'input' && (type === 'checkbox' || type === 'radio')) {
      if ((st.appearance || st.webkitAppearance) !== 'none') continue;  // drawn by the browser: exempt
      kind = 'toggle';
    } else if (tag !== 'input' && ['checkbox', 'radio', 'switch'].includes(el.getAttribute('role'))) kind = 'toggle';
    else if (tag !== 'input' && el.getAttribute('role')) kind = 'input';
    if (!kind) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 6 || r.height < 6) continue;
    out.items.push({
      selector: K.path(el), html: K.outer(el), kind, type, borders: borders(st), fill: st.backgroundColor,
      fill_image: !!(st.backgroundImage && st.backgroundImage !== 'none'), outside: K.layersAround(el, true).layers,
      inactive: K.inactive(el), lang: K.lang(el), rect: K.rect(el),
      label: (el.labels && el.labels[0]) ? K.norm(el.labels[0].innerText).slice(0, 120) : (el.getAttribute('aria-label') || ''),
    });
  }

  // --- icon-only controls --------------------------------------------------------------------
  for (const el of document.querySelectorAll('button, a[href], [role="button"], input[type="button"], input[type="submit"], input[type="reset"]')) {
    if (out.icons.length >= 60) break;
    if (!K.visible(el)) continue;
    const vis = K.norm(el.innerText || el.value || '');
    const pua = vis.length > 0 && /^[-\s]+$/.test(vis);
    if (vis && !pua && K.LETTER.test(vis)) continue;  // visible text identifies the control
    const st = K.cs(el);
    const svg = el.querySelector('svg');
    const img = el.querySelector('img');
    const bgimg = !!(st.backgroundImage && /url\(/.test(st.backgroundImage));
    if (!svg && !img && !pua && !bgimg) continue;
    const r = el.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) continue;
    let glyph = null;
    if (pua) {
      let g = el;
      for (const d of el.querySelectorAll('*')) if (K.norm(d.textContent) === vis) g = d;
      glyph = K.cs(g).color;
    }
    out.icons.push({
      selector: K.path(el), html: K.outer(el), name: el.getAttribute('aria-label') || el.getAttribute('title') || '',
      svg: svg ? shapes(svg) : null, glyph, image: !!img || bgimg, layers: K.layersAround(el, false).layers,
      inactive: K.inactive(el), lang: K.lang(el), rect: K.rect(el),
    });
  }

  // --- author focus styles (CSSOM) -----------------------------------------------------------
  function resolveVar(v, el) {
    let s = v || '';
    for (let i = 0; i < 4 && /var\(/.test(s); i++) {
      s = s.replace(/var\(\s*(--[\w-]+)\s*(?:,\s*([^()]*))?\)/g, (m, name, fb) =>
        K.cs(el).getPropertyValue(name).trim() || (fb || '').trim());
    }
    return s.trim();
  }
  // A colour that depends on a variable set by a :focus rule (utility-CSS rings), or on an undefined
  // variable, cannot be measured without focusing. A variable set globally (:root) is a fact.
  function focusDependent(decl, el) {
    const names = Array.from((decl || '').matchAll(/var\(\s*(--[\w-]+)/g), (m) => m[1]);
    return names.some((n) => focusVars.has(n) || !K.cs(el).getPropertyValue(n).trim());
  }
  function* styleRules(list) {
    for (const rule of list) {
      if (rule.type === 1) yield rule;
      else if (rule.cssRules) {
        if (rule.media && rule.media.mediaText && !matchMedia(rule.media.mediaText).matches) continue;
        yield* styleRules(rule.cssRules);
      }
    }
  }
  const focusable = (el) => K.visible(el) && !el.disabled && el.tabIndex >= 0;
  const indicators = new Map();
  // Custom properties that a :focus rule sets: their value while focused is unknown here.
  const focusVars = new Set();
  for (const sheet of Array.from(document.styleSheets)) {
    let rules;
    try { rules = sheet.cssRules; } catch (e) { continue; }  // cross-origin sheet
    if (!rules) continue;
    for (const rule of styleRules(rules)) {
      const sel = rule.selectorText || '';
      if (!/:focus(?!-within)/.test(sel)) continue;
      const s = rule.style;
      for (let i = 0; i < s.length; i++) if (s[i].startsWith('--')) focusVars.add(s[i]);
      const props = { os: s.outlineStyle, ow: s.outlineWidth, oc: s.outlineColor, bs: s.boxShadow, bc: s.borderColor || s.borderBottomColor,
                      bst: s.borderStyle || s.borderBottomStyle, bw: s.borderWidth || s.borderBottomWidth, b: s.border };
      if (!props.os && !props.oc && !props.bs && !props.bc && !s.outline) continue;
      // A shorthand with var() leaves its longhands empty in the CSSOM: keep it, resolved per element.
      if (!props.os && s.outline && /var\(/i.test(s.outline)) props.outline_raw = s.outline;
      for (const part of sel.split(',')) {
        if (!/:focus(?!-within)/.test(part)) continue;
        let base = part.replace(/:focus-visible|:focus(?!-within)/g, '').trim();
        if (!base || /[>+~]$/.test(base)) base += '*';
        let els;
        try { els = document.querySelectorAll(base); } catch (e) { continue; }
        let n = 0;
        for (const el of els) {
          if (n++ > 200) break;
          if (!focusable(el)) continue;
          indicators.set(el, { rule: sel.slice(0, 160), props });  // later rules win (document order)
        }
      }
    }
  }
  let nf = 0;
  for (const [el, { rule, props }] of indicators) {
    if (nf++ >= 60) break;
    const st = K.cs(el);
    const res = (v) => {
      const r = resolveVar(v, el);
      return /^currentcolor$/i.test(r.trim()) ? st.color : (K.firstColour(r) || (/currentcolor/i.test(r) ? st.color : ''));
    };
    // Every colour the indicator draws: an outline, ALL box-shadow layers (a double ring such as
    // "0 0 0 2px #fff, 0 0 0 4px #000"), a border. The check keeps the best contrast of them.
    // A box-shadow layer is a ring when its spread (4th length) is > 0; a soft drop shadow is not
    // an indicator next to an outline. Only rings count, unless the shadow is the whole indicator.
    const layersOf = (v) => resolveVar(v, el).split(/,(?![^(]*\))/);
    const isRing = (layer) => {
      const lens = layer.replace(/[a-z-]+\([^)]*\)|#[0-9a-f]+/gi, ' ').match(/-?\d*\.?\d+(px|em|rem)?/g) || [];
      return lens.length >= 4 && parseFloat(lens[3]) > 0;
    };
    const resAll = (v, ringsOnly) => layersOf(v).filter((l) => !ringsOnly || isRing(l)).map(res).filter(Boolean).join(' ');
    // A border counts only when the focus rule draws one ("border: 0" reads as currentcolor).
    const ruleKillsBorder = /^(none|hidden)$/.test((props.bst || '').trim()) || /^0(px)?$/.test((props.bw || '').trim()) ||
      /(^|\s)(0|0px|none)(\s|$)/.test(props.b || '');
    const elHasBorder = !/^(none|hidden)$/.test(st.borderBottomStyle) && parseFloat(st.borderBottomWidth) > 0;
    const drawsBorder = !!props.bc && !ruleKillsBorder && (!!(props.bst && props.bw) || elHasBorder);
    let indicator = null;
    const parts = [];
    let { os, ow: owRaw, oc } = props;
    if (props.outline_raw) {
      const r = resolveVar(props.outline_raw, el);
      os = (r.match(/\b(none|auto|solid|dashed|dotted|double|groove|ridge|inset|outset)\b/i) || [])[1] || '';
      owRaw = (r.match(/\d*\.?\d+(px|em|rem)\b/i) || [])[0] || (/\bthick\b/i.test(r) ? '5px' : /\bthin\b/i.test(r) ? '1px' : '');
      oc = r;
    }
    const ow = parseFloat(resolveVar(owRaw, el)) || (os && os !== 'none' ? 2 : 0);
    if (os && os !== 'none' && os !== 'auto' && ow > 0) { indicator = 'outline'; parts.push(res(oc || 'currentcolor')); }
    if (props.bs && props.bs !== 'none') {
      parts.push(resAll(props.bs, !!indicator));   // next to an outline: rings only
      indicator = indicator || 'box_shadow';
    }
    if (drawsBorder) { indicator = indicator || 'border'; parts.push(res(props.bc)); }
    if (!indicator && (os === 'none' || owRaw === '0px')) indicator = 'removed';
    if (!indicator) continue;
    const colour = parts.filter(Boolean).join(' ');
    out.focus.push({
      selector: K.path(el), html: K.outer(el), rule, indicator, colour, outside: K.layersAround(el, true).layers,
      // Colours from CSS variables are resolved outside the focus state (nothing is focused):
      // utility-CSS rings set their colour variable only while focused, so a low value proves nothing.
      uses_var: focusDependent([props.oc, props.bs, props.bc, props.outline_raw].filter(Boolean).join(' '), el),
      own: K.layers(el, null).layers, lang: K.lang(el), text: K.norm(el.innerText || el.value || '').slice(0, 120),
    });
  }

  // --- graphics -----------------------------------------------------------------------------
  for (const g of document.querySelectorAll('img, svg, canvas, [role="img"]')) {
    if (out.graphics.length >= 30) break;
    if (g.localName !== 'svg' && g.closest('svg')) continue;
    if (g.localName === 'svg' && g.parentElement && g.parentElement.closest('svg')) continue;
    if (g.closest('a[href], button, [role="button"]') || !K.visible(g)) continue;
    const r = g.getBoundingClientRect();
    if (r.width < 100 || r.height < 60) continue;
    let ctx = {};
    try { ctx = window.__klar.imageContext(g) || {}; } catch (e) { ctx = {}; }
    out.graphics.push({
      selector: K.path(g), tag: g.localName, html: K.outer(g), alt: g.getAttribute('alt') || g.getAttribute('aria-label') || '',
      svg: g.localName === 'svg' ? shapes(g) : null, layers: K.layersAround(g, false).layers, rect: K.rect(g),
      caption: ctx.caption || '', surrounding: ctx.surrounding_text || '', hidden: K.hiddenFromAT(g), lang: K.lang(g),
    });
  }
  window.scrollTo(sx, sy);
  return out;
}
