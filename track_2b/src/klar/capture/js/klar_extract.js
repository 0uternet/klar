/* Klar. DOM extraction library.
 *
 * Injected with page.evaluate() (not a <script> tag: no DOM change, no CSP issue).
 * READ-ONLY: it never mutates the audited DOM. Extracted elements are kept in
 * window.__klar.refs so that Python can ask Chromium (CDP) for the computed
 * accessible name of each one (record field `k` = index in refs).
 *
 * Programmatic link context follows WCAG 2.4.4 / ACT rule 5effbb: the same
 * sentence, the closest ancestor that generates a block container ("block"),
 * list item, table cell + its header cells, aria-describedby.
 * A preceding heading is NOT context: it is returned separately as
 * `heading_hint` (metadata for the cantTell decision, never shown to the model).
 */
(() => {
  // The global name is randomised per process by Python (capture/browser.py) and
  // always (re)defined here: a hostile page cannot pre-define it.
  const MAX_HTML = 2000;
  const MAX_CTX = 600;
  const refs = [];
  const norm = (s) => (s || '').replace(/[\s ​]+/g, ' ').trim();
  const ref = (el) => { refs.push(el); return refs.length - 1; };

  // --- basics ---------------------------------------------------------------
  function cssEscape(s) {
    return window.CSS && CSS.escape ? CSS.escape(s) : String(s).replace(/[^a-zA-Z0-9_-]/g, (c) => '\\' + c);
  }

  function uniqueIdSelector(el) {
    if (!el.id) return null;
    const sel = '#' + cssEscape(el.id);
    try { return document.querySelectorAll(sel).length === 1 ? sel : null; } catch (e) { return null; }
  }

  /** Unique, valid CSS selector (document scope; shadow DOM is not traversed). */
  function cssPath(el) {
    const parts = [];
    let node = el;
    while (node && node.nodeType === 1) {
      const idSel = uniqueIdSelector(node);
      if (idSel) { parts.unshift(idSel); break; }
      if (node === document.documentElement) { parts.unshift('html'); break; }
      let part = cssEscape(node.localName);
      const parent = node.parentElement;
      if (parent) {
        const same = Array.from(parent.children).filter((c) => c.localName === node.localName);
        if (same.length > 1) part += ':nth-of-type(' + (same.indexOf(node) + 1) + ')';
      }
      parts.unshift(part);
      node = parent;
    }
    return parts.join(' > ');
  }

  function langHolder(el) {
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      if (n.hasAttribute('lang')) return n;
    }
    return null;
  }

  function inheritedLang(el) {
    const h = langHolder(el);
    return h ? h.getAttribute('lang') : null;
  }

  function isVisible(el) {
    if (!el || !el.isConnected) return false;
    if (typeof el.checkVisibility === 'function' &&
        !el.checkVisibility({ visibilityProperty: true, checkVisibilityCSS: true })) return false;
    return el.getClientRects().length > 0;
  }

  function isInline(el) {
    const d = getComputedStyle(el).display;
    return d === 'contents' || d.startsWith('inline');
  }

  /** Nearest ancestor-or-self that is not an inline box. */
  function nearestBlock(el) {
    let n = el;
    while (n && n !== document.body && isInline(n)) n = n.parentElement;
    return n || document.body;
  }

  function rect(el) {
    const r = el.getBoundingClientRect();
    return { x: Math.round(r.left + window.scrollX), y: Math.round(r.top + window.scrollY),
             w: Math.round(r.width), h: Math.round(r.height) };
  }

  function outer(el) {
    const h = el.outerHTML || '';
    return h.length > MAX_HTML ? h.slice(0, MAX_HTML) : h;
  }

  function textOf(el) {
    const t = typeof el.innerText === 'string' && isVisible(el) ? el.innerText : el.textContent;
    return norm(t);
  }

  function idrefText(el, attr) {
    const ids = (el.getAttribute(attr) || '').split(/\s+/).filter(Boolean);
    return norm(ids.map((id) => {
      const t = document.getElementById(id);
      return t ? (t.textContent || '') : '';
    }).join(' '));
  }

  /** Clip long text to MAX_CTX characters around `needle`. */
  function clip(text, needle, max = MAX_CTX) {
    text = norm(text);
    if (text.length <= max) return text;
    const i = needle ? text.indexOf(norm(needle)) : -1;
    if (i < 0) return text.slice(0, max - 1) + '…';
    let start = Math.max(0, i - Math.floor(max / 2));
    const end = Math.min(text.length, start + max);
    start = Math.max(0, end - max);
    return (start > 0 ? '…' : '') + text.slice(start, end) + (end < text.length ? '…' : '');
  }

  // --- accessible name (fallback; Python prefers Chromium's own via CDP) -----
  const NAME_FROM_CONTENT = new Set(['link', 'button', 'heading', 'cell', 'columnheader', 'rowheader',
    'menuitem', 'option', 'tab', 'treeitem', 'checkbox', 'radio', 'switch', 'tooltip', 'gridcell']);

  function subtreeName(el) {
    let out = '';
    for (const n of el.childNodes) {
      if (n.nodeType === 3) { out += n.nodeValue; continue; }
      if (n.nodeType !== 1) continue;
      if (n.getAttribute('aria-hidden') === 'true') continue;
      if (getComputedStyle(n).display === 'none') continue;
      const al = norm(n.getAttribute('aria-label'));
      if (al) { out += ' ' + al + ' '; continue; }
      if (n.localName === 'img') { out += ' ' + (n.getAttribute('alt') || '') + ' '; continue; }
      out += ' ' + subtreeName(n) + ' ';
    }
    return norm(out);
  }

  function nameFallback(el) {
    const lb = idrefText(el, 'aria-labelledby');
    if (lb) return lb;
    const al = norm(el.getAttribute('aria-label'));
    if (al) return al;
    const tag = el.localName;
    if (tag === 'img' || tag === 'area' || (tag === 'input' && el.type === 'image')) {
      const a = el.getAttribute('alt');
      if (a !== null && norm(a)) return norm(a);
    }
    if (tag === 'input' || tag === 'select' || tag === 'textarea') {
      if (el.labels && el.labels.length) return norm(Array.from(el.labels).map((l) => l.textContent).join(' '));
      if (['submit', 'button', 'reset'].includes(el.type)) return norm(el.value);
    }
    if (tag === 'svg') {
      const t = el.querySelector(':scope > title');
      if (t) return norm(t.textContent);
    }
    const role = el.getAttribute('role') || (tag === 'a' && el.hasAttribute('href') ? 'link' : tag === 'button' ? 'button' : '');
    if (NAME_FROM_CONTENT.has(role)) {
      const s = subtreeName(el);
      if (s) return s;
    }
    return norm(el.getAttribute('title'));
  }

  // --- sentences -------------------------------------------------------------
  const TERMINATORS = '.!?…';
  // Abbreviations (DE/FR/IT/EN) whose period does not end a sentence; a single
  // letter + period is an initial or an abbreviation ("z. B.", "M. Rossi").
  const ABBR = /(?:^|[\s(])(?:[A-Za-zÀ-ÿ]|z\.\s?B|d\.\s?h|u\.\s?a|bzw|ca|usw|etc|vgl|evtl|inkl|ggf|Nr|Str|Tel|Dr|Prof|St|Hr|Fr|Mio|Mrd|e\.g|i\.e|vs|Mr|Mrs|Ms|Mme|Mlle|cf|p\.\s?ex|env|ecc|Sig|Dott|pag|Abs|Art|Ziff|resp|no)\.$/i;
  const MONTH = /^\s*(Jan|Feb|Mär|Mar|Apr|Mai|May|Jun|Jul|Aug|Sep|Okt|Oct|Nov|Dez|Dec)/;

  function isBoundary(text, i) {
    if (!TERMINATORS.includes(text[i])) return false;
    if (i + 1 < text.length && !/\s/.test(text[i + 1])) return false;
    if (text[i] === '.') {
      if (ABBR.test(text.slice(Math.max(0, i - 12), i + 1))) return false;
      if (/(^|\s)\d{1,2}$/.test(text.slice(Math.max(0, i - 3), i)) && MONTH.test(text.slice(i + 1, i + 8))) return false; // "4. Oktober"
    }
    return true;
  }

  /** Text of `block` split around `el`; block boundaries and <br> become "\n". */
  function splitAround(block, el) {
    let before = '', after = '', where = 0;
    const add = (s) => { if (where === 0) before += s; else after += s; };
    const walk = (node) => {
      if (node === el) { where = 1; return; }
      if (node.nodeType === 3) { add(node.nodeValue); return; }
      if (node.nodeType !== 1) return;
      const tag = node.localName;
      if (['script', 'style', 'noscript', 'template'].includes(tag)) return;
      if (tag === 'br') { add('\n'); return; }
      const cs = getComputedStyle(node);
      if (cs.display === 'none') return;
      const blockish = !isInline(node);
      if (blockish) add('\n');
      if (node.localName === 'img') add(' ');
      for (const c of node.childNodes) walk(c);
      if (blockish) add('\n');
    };
    for (const c of block.childNodes) walk(c);
    return { before, after };
  }

  function sentenceOf(el) {
    const block = nearestBlock(el.parentElement || el);
    const { before, after } = splitAround(block, el);
    const self = textOf(el);
    let start = Math.max(before.lastIndexOf('\n') + 1, 0);
    for (let i = before.length - 1; i >= start; i--) {
      if (isBoundary(before, i)) { start = i + 1; break; }
    }
    let end = after.indexOf('\n');
    if (end < 0) end = after.length;
    for (let i = 0; i < end; i++) {
      if (isBoundary(after, i)) { end = i + 1; break; }
    }
    const s = norm(before.slice(start) + ' ' + self + ' ' + after.slice(0, end))
      .replace(/\s+([.,;:!?…])/g, '$1');
    return s === self ? '' : clip(s, self);
  }

  // --- tables ----------------------------------------------------------------
  function tableGrid(table) {
    const grid = [];
    Array.from(table.rows).forEach((row, r) => {
      grid[r] = grid[r] || [];
      let c = 0;
      for (const cell of row.cells) {
        while (grid[r][c]) c++;
        const cs = Math.max(1, cell.colSpan || 1), rs = Math.max(1, cell.rowSpan || 1);
        for (let i = 0; i < rs; i++) for (let j = 0; j < cs; j++) (grid[r + i] = grid[r + i] || [])[c + j] = cell;
        c += cs;
      }
    });
    return grid;
  }

  /** Header cells assigned to `cell` (headers attribute, else column/row headers). */
  function headersOf(cell) {
    const out = [];
    const push = (h) => { const t = norm(h.textContent); if (t && !out.includes(t)) out.push(t); };
    const ids = (cell.getAttribute('headers') || '').split(/\s+/).filter(Boolean);
    if (ids.length) {
      ids.forEach((id) => { const h = document.getElementById(id); if (h) push(h); });
      return out;
    }
    const table = cell.closest('table');
    if (!table || !(cell instanceof HTMLTableCellElement)) return out;
    const grid = tableGrid(table);
    let pos = null;
    grid.forEach((row, r) => row.forEach((c, j) => { if (!pos && c === cell) pos = [r, j]; }));
    if (!pos) return out;
    const [r, c] = pos;
    const isHeader = (h) => h && h !== cell && (h.localName === 'th' ||
      ['columnheader', 'rowheader'].includes(h.getAttribute('role')));
    for (let i = 0; i < r; i++) {
      const h = grid[i] && grid[i][c];
      if (isHeader(h) && !['row', 'rowgroup'].includes(h.getAttribute('scope'))) push(h);
    }
    for (let j = 0; j < c; j++) {
      const h = grid[r][j];
      if (isHeader(h) && !['col', 'colgroup'].includes(h.getAttribute('scope'))) push(h);
    }
    return out;
  }

  // --- link context (ACT 5effbb) ------------------------------------------------
  function linkContext(a) {
    const ctx = {};
    const self = textOf(a);
    const keep = (key, text) => { const t = clip(text, self); if (t && t !== self) ctx[key] = t; };
    const sentence = sentenceOf(a);
    if (sentence) ctx.sentence = sentence;
    // ACT 5effbb: the closest ancestor that generates a block container (p, div, td, li, …)
    const block = nearestBlock(a.parentElement || a);
    if (block && block !== document.body && block !== document.documentElement) keep('block', textOf(block));
    const li = a.closest('li, [role="listitem"]');
    if (li) keep('list_item', textOf(li));
    const cell = a.closest('td, th, [role="cell"], [role="gridcell"], [role="rowheader"], [role="columnheader"]');
    if (cell && cell.closest('table, [role="table"], [role="grid"], [role="treegrid"]')) {
      keep('table_cell', textOf(cell));
      const hs = headersOf(cell);
      if (hs.length) ctx.table_headers = clip(hs.join(' | '), '');
    }
    const d = idrefText(a, 'aria-describedby');
    if (d) ctx.described_by = clip(d, '');
    return ctx;
  }

  const HEADINGS = 'h1, h2, h3, h4, h5, h6, [role="heading"]';

  function headingLevel(h) {
    const m = /^h([1-6])$/.exec(h.localName);
    return m ? Number(m[1]) : Number(h.getAttribute('aria-level')) || 2;
  }

  /** The heading of the part of the page that `a` belongs to (a card, a section):
   *  the nearest ancestor of `a` (below main/body) that holds a heading before `a`
   *  decides. Its last such heading counts only if that ancestor holds no other
   *  heading of the same or a higher level (else it is a list of cards or sections:
   *  the heading belongs to a sibling) and no other link with the same name.
   *  Head/body wrappers ("card__head" with a date + h3, "card__body" with the link)
   *  are covered; a sibling card's heading never is. NOT programmatic context:
   *  used only to tell "failed" from "cantTell" (technique H80), never shown to
   *  the model. */
  function headingHint(a) {
    for (let anc = a.parentElement; anc && !['main', 'body', 'html'].includes(anc.localName); anc = anc.parentElement) {
      const hs = Array.from(anc.querySelectorAll(HEADINGS)).filter((h) => !h.contains(a) && !h.closest('[aria-hidden="true"]'));
      const before = hs.filter((h) => h.compareDocumentPosition(a) & Node.DOCUMENT_POSITION_FOLLOWING);
      if (!before.length) continue;
      const h = before[before.length - 1];
      const level = headingLevel(h);
      if (hs.some((o) => o !== h && headingLevel(o) <= level)) return '';
      const name = norm(nameFallback(a) || a.textContent).toLowerCase();
      const same = Array.from(anc.querySelectorAll('a[href], [role="link"]'))
        .filter((l) => norm(nameFallback(l) || l.textContent).toLowerCase() === name);
      return same.length > 1 ? '' : clip(textOf(h), '', 200);
    }
    return '';
  }

  // --- collections ---------------------------------------------------------------
  function links(max = 600) {
    const out = [];
    for (const a of document.querySelectorAll('a[href], area[href], [role="link"]')) {
      if (out.length >= max) break;
      if (a.closest('[aria-hidden="true"]')) continue;
      const visible = a.localName === 'area' ? true : isVisible(a);
      if (!visible) continue;
      out.push({
        k: ref(a), selector: cssPath(a), tag: a.localName, html: outer(a), text: textOf(a),
        href: a.href || a.getAttribute('href') || '', raw_href: a.getAttribute('href'),
        name_js: nameFallback(a), lang: inheritedLang(a), context: linkContext(a), rect: rect(a),
        image_alts: Array.from(a.querySelectorAll('img')).map((i) => i.getAttribute('alt')),
        target: a.getAttribute('target'), title: norm(a.getAttribute('title')), heading_hint: headingHint(a),
        hreflang: a.getAttribute('hreflang'), own_lang: a.getAttribute('lang'),
      });
    }
    return out;
  }

  function imageContext(el) {
    const ctx = {};
    const fig = el.closest('figure');
    const cap = fig && fig.querySelector('figcaption');
    if (cap) ctx.caption = clip(textOf(cap), '');
    const a = el.closest('a[href], button');
    if (a) {
      ctx.link_href = a.localName === 'a' ? (a.href || '') : '';
      const t = textOf(a);
      if (t) ctx.link_text = clip(t, '');
      ctx.link_name = nameFallback(a);  // empty → the image is the control's only content (F89)
    }
    const block = nearestBlock(el.parentElement || el);
    const { before, after } = splitAround(block, el);
    const around = norm(before.slice(-220) + ' … ' + after.slice(0, 220));
    if (around.replace(/[\s…]/g, '')) ctx.surrounding_text = around;
    const title = norm(el.getAttribute('title'));
    if (title) ctx.title = title;
    return ctx;
  }

  function images(max = 300) {
    const out = [];
    const seen = new Set();
    for (const el of document.querySelectorAll('img, input[type="image"], [role="img"], area')) {
      if (out.length >= max) break;
      if (seen.has(el)) continue;
      seen.add(el);
      const tag = el.localName;
      let visible;
      if (tag === 'area') {
        const map = el.closest('map');
        const img = map && map.name ? document.querySelector('img[usemap="#' + cssEscape(map.name) + '"]') : null;
        visible = !!img && isVisible(img);
      } else {
        visible = isVisible(el);
      }
      if (!visible) continue;
      const role = el.getAttribute('role');
      const alt = el.hasAttribute('alt') ? el.getAttribute('alt') : null;
      const hidden = !!el.closest('[aria-hidden="true"]');
      out.push({
        k: ref(el), selector: cssPath(el), tag, html: outer(el), alt, role, aria_hidden: hidden,
        decorative_markup: (alt === '' && !el.getAttribute('aria-label') && !el.getAttribute('aria-labelledby')) ||
          role === 'presentation' || role === 'none' || hidden,
        name_js: nameFallback(el), src: el.currentSrc || el.src || el.getAttribute('src') || '',
        natural: tag === 'img' ? { w: el.naturalWidth, h: el.naturalHeight } : null,
        rect: rect(el), lang: inheritedLang(el), context: imageContext(el),
        in_link: !!el.closest('a[href], button'),
      });
    }
    return out;
  }

  const PASSAGE_SKIP = 'script,style,noscript,template,code,pre,kbd,samp,var,textarea,select,svg,math';

  /** Text passages grouped by nearest block container and by lang-holder:
   *  an inline <span lang="fr"> inside a <p> becomes its own passage. */
  // Elements that separate lines of text even when they are styled inline (nav menus,
  // definition lists, address blocks): a line break is inserted at their start.
  const LINE_TAGS = new Set(['br', 'li', 'dd', 'dt', 'td', 'th', 'tr', 'p', 'div', 'address', 'h1', 'h2', 'h3',
    'h4', 'h5', 'h6', 'label', 'option', 'figcaption', 'caption', 'section', 'article', 'header', 'footer']);

  /** Collapse spaces but keep line breaks: "a  b\n\n c" → "a b\nc". */
  function normLines(s) {
    return (s || '').split('\n').map(norm).filter(Boolean).join('\n');
  }

  function passages(max = 800) {
    const groups = new Map();
    const order = [];
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, {
      acceptNode(n) {
        if (n.nodeType === 1) {
          if (n.matches(PASSAGE_SKIP) || n.getAttribute('aria-hidden') === 'true') return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_ACCEPT;
        }
        if (!n.nodeValue || !n.nodeValue.trim()) return NodeFilter.FILTER_SKIP;
        const p = n.parentElement;
        if (!p || p.closest(PASSAGE_SKIP) || p.closest('[aria-hidden="true"]')) return NodeFilter.FILTER_REJECT;
        return isVisible(p) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      },
    });
    const groupOf = (el) => {
      const container = nearestBlock(el);
      let g = groups.get(container);
      if (!g) { g = { container, parts: new Map(), sep: false }; groups.set(container, g); order.push(g); }
      return g;
    };
    let n;
    while ((n = walker.nextNode())) {
      if (n.nodeType === 1) {
        // A line boundary inside an inline formatting context: <br>, an inline-block box,
        // or a line-level element styled inline. The next text of that container starts a new line.
        const d = getComputedStyle(n).display;
        if (n.localName === 'br' || d.startsWith('inline-') || (d === 'inline' && LINE_TAGS.has(n.localName))) {
          groupOf(n.parentElement || n).sep = true;
        }
        continue;
      }
      const parent = n.parentElement;
      const g = groupOf(parent);
      const holder = langHolder(parent);
      const sub = holder && holder !== g.container && g.container.contains(holder) ? holder : null;
      const key = sub || g.container;
      const prev = g.parts.get(key) || '';
      g.parts.set(key, prev + (g.sep && prev ? '\n' : '') + n.nodeValue);
      g.sep = false;
    }
    const out = [];
    for (const g of order) {
      const containerText = norm(Array.from(g.parts.values()).join(' '));
      for (const [el, raw] of g.parts) {
        const text = normLines(raw);
        if (!text) continue;
        // Quote-like inline elements (titles, citations, emphasised terms): 3.1.2 never
        // fails these in code, it asks whether they are a title, a name or a passage.
        const QUOTE_LIKE = 'q, cite, i, em, dfn';
        const quoted = Array.from(el.querySelectorAll(QUOTE_LIKE)).map(textOf).filter(Boolean).slice(0, 20);
        if (el.matches(QUOTE_LIKE)) quoted.push(norm(text));
        out.push({
          selector: cssPath(el), tag: el.localName, html: outer(el), text,
          lang: inheritedLang(el), own_lang: el.hasAttribute('lang') ? el.getAttribute('lang') : null,
          container_selector: cssPath(g.container), container_text: clip(containerText, norm(text)),
          is_container: el === g.container, quoted,
        });
        if (out.length >= max) return out;
      }
    }
    return out;
  }

  function langElements(max = 300) {
    return Array.from(document.body ? document.body.querySelectorAll('[lang]') : []).slice(0, max).map((el) => ({
      selector: cssPath(el), tag: el.localName, lang: el.getAttribute('lang'), text: clip(textOf(el), ''),
      html: outer(el), parent_lang: el.parentElement ? inheritedLang(el.parentElement) : null,
    }));
  }

  const FIELD_SEL = 'input:not([type="hidden"]), select, textarea, [role="textbox"], [role="combobox"], ' +
    '[role="listbox"], [role="checkbox"], [role="radio"], [role="switch"], [role="spinbutton"], [role="slider"], ' +
    '[contenteditable=""], [contenteditable="true"]';

  function fields(max = 300) {
    const out = [];
    for (const el of document.querySelectorAll(FIELD_SEL)) {
      if (out.length >= max) break;
      if (!isVisible(el)) continue;
      const fs = el.closest('fieldset');
      const legend = fs && fs.querySelector('legend');
      out.push({
        k: ref(el), selector: cssPath(el), tag: el.localName, type: el.getAttribute('type') || el.type || null,
        html: outer(el), name_js: nameFallback(el),
        labels: el.labels ? Array.from(el.labels).map((l) => norm(l.textContent)) : [],
        legend: legend ? norm(legend.textContent) : null,
        describedby: idrefText(el, 'aria-describedby'), errormessage: idrefText(el, 'aria-errormessage'),
        placeholder: el.getAttribute('placeholder'), title: el.getAttribute('title'),
        required: !!(el.required || el.getAttribute('aria-required') === 'true'),
        autocomplete: el.getAttribute('autocomplete'), field_name: el.getAttribute('name'), id: el.id || null,
        invalid: el.getAttribute('aria-invalid'), lang: inheritedLang(el),
        form: el.form ? cssPath(el.form) : null, rect: rect(el),
      });
    }
    return out;
  }

  function forms(max = 50) {
    return Array.from(document.forms).slice(0, max).filter(isVisible).map((f) => {
      const submit = f.querySelector('button:not([type]), button[type="submit"], input[type="submit"], input[type="image"]');
      return {
        selector: cssPath(f), html: outer(f), action: f.getAttribute('action'), action_url: f.action || '',
        method: (f.method || 'get').toLowerCase(),
        novalidate: f.noValidate, field_count: f.elements.length, submit: submit ? cssPath(submit) : null,
      };
    });
  }

  function headings(max = 300) {
    return Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, [role="heading"]')).slice(0, max)
      .filter(isVisible).map((h) => ({
        selector: cssPath(h), html: outer(h), text: textOf(h), lang: inheritedLang(h),
        level: h.getAttribute('aria-level') ? Number(h.getAttribute('aria-level')) : Number(h.localName.slice(1)) || null,
      }));
  }

  function snapshot() {
    return {
      url: location.href, title: document.title,
      lang: document.documentElement.getAttribute('lang'),
      html: document.documentElement.outerHTML.slice(0, 3000000),
      text: document.body ? norm(document.body.innerText) : '',
    };
  }

  function all() {
    refs.length = 0;
    return { links: links(), images: images(), passages: passages(), lang_elements: langElements(),
             fields: fields(), forms: forms(), headings: headings() };
  }

  function describe(selector) {
    let el;
    try { el = document.querySelector(selector); } catch (e) { return null; }
    if (!el) return null;
    return { selector, html: outer(el), text: textOf(el), lang: inheritedLang(el), rect: rect(el), visible: isVisible(el) };
  }

  function count(selector) {
    try { return document.querySelectorAll(selector).length; } catch (e) { return 0; }
  }

  window.__klar = {
    version: 1, refs, norm, cssPath, inheritedLang, isVisible, nearestBlock, textOf, nameFallback,
    sentenceOf, headersOf, linkContext, headingHint, imageContext, links, images, passages, langElements, fields,
    forms, headings, snapshot, all, describe, count,
  };
})();
