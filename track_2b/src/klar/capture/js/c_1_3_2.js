/* Klar. 1.3.2 Meaningful Sequence: DOM order vs visual order. Read-only.
 * Evaluated with page.evaluate(src, opts); needs window.__klar (extractor library).
 *
 * reorders       flex/grid containers (and containers with absolutely positioned
 *                children) whose children are shown in an order that is neither the
 *                DOM order read row by row nor column by column
 * pre_columns    text columns built with runs of spaces in preformatted text
 * spaced_words   words written with spaces between the letters
 * layout_tables  tables without header cells holding prose; does a sentence
 *                continue in the cell BELOW (column reading) while the DOM reads row by row?
 */
(opts) => {
  const K = window.__klar;
  const MAX = (opts && opts.max) || 30;
  const norm = K.norm;
  const out = { reorders: [], pre_columns: [], spaced_words: [], layout_tables: [] };
  const body = document.body;
  if (!body) return out;
  const sel = (el) => K.cssPath(el);
  const outer = (el) => { const h = el.outerHTML || ''; return h.length > 1500 ? h.slice(0, 1500) : h; };
  const box = (el) => { const r = el.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; };
  const overlap = (a0, a1, b0, b1) => Math.max(0, Math.min(a1, b1) - Math.max(a0, b0));

  function decorative(el) {
    if (norm(el.innerText || el.textContent)) return false;
    const imgs = Array.from(el.querySelectorAll('img, svg, [role="img"]'));
    if (el.matches('img, svg, [role="img"]')) imgs.push(el);
    return imgs.every((i) => i.getAttribute('alt') === '' || i.getAttribute('aria-hidden') === 'true' ||
      i.closest('[aria-hidden="true"]') || ['presentation', 'none'].includes(i.getAttribute('role')));
  }

  /** Visual order of boxes: row by row (rtl aware) and column by column. */
  function visualOrders(items, rtl) {
    const rows = [];
    for (const it of items.slice().sort((a, b) => a.b.y - b.b.y || a.b.x - b.b.x)) {
      const row = rows.find((r) => overlap(r.y0, r.y1, it.b.y, it.b.y + it.b.h) >= 0.5 * Math.min(r.y1 - r.y0, it.b.h));
      if (row) { row.items.push(it); row.y0 = Math.min(row.y0, it.b.y); row.y1 = Math.max(row.y1, it.b.y + it.b.h); }
      else rows.push({ y0: it.b.y, y1: it.b.y + it.b.h, items: [it] });
    }
    rows.sort((a, b) => a.y0 - b.y0);
    const byRow = rows.flatMap((r) => r.items.sort((a, b) => rtl ? b.b.x - a.b.x : a.b.x - b.b.x));
    const cols = [];
    for (const it of items.slice().sort((a, b) => a.b.x - b.b.x || a.b.y - b.b.y)) {
      const col = cols.find((c) => overlap(c.x0, c.x1, it.b.x, it.b.x + it.b.w) >= 0.5 * Math.min(c.x1 - c.x0, it.b.w));
      if (col) { col.items.push(it); col.x0 = Math.min(col.x0, it.b.x); col.x1 = Math.max(col.x1, it.b.x + it.b.w); }
      else cols.push({ x0: it.b.x, x1: it.b.x + it.b.w, items: [it] });
    }
    cols.sort((a, b) => rtl ? b.x1 - a.x1 : a.x0 - b.x0);
    const byCol = cols.flatMap((c) => c.items.sort((a, b) => a.b.y - b.b.y));
    return { byRow, byCol };
  }

  /** Indexes (DOM positions) that are NOT part of the longest run kept in visual order. */
  function moved(visual) {
    const seq = visual.map((it) => it.i);
    const n = seq.length, len = new Array(n).fill(1), prev = new Array(n).fill(-1);
    for (let i = 0; i < n; i++) for (let j = 0; j < i; j++) if (seq[j] < seq[i] && len[j] + 1 > len[i]) { len[i] = len[j] + 1; prev[i] = j; }
    let k = len.indexOf(Math.max(...len));
    const keep = new Set();
    while (k >= 0) { keep.add(seq[k]); k = prev[k]; }
    return seq.filter((i) => !keep.has(i));
  }

  const seen = new Set();
  for (const el of Array.from(body.querySelectorAll('*')).slice(0, 5000)) {
    if (out.reorders.length >= MAX) break;
    if (['script', 'style', 'svg', 'select', 'option', 'table', 'tr', 'thead', 'tbody'].includes(el.localName)) continue;
    const cs = getComputedStyle(el);
    const kids = Array.from(el.children).filter((c) => K.isVisible(c) && !['script', 'style', 'template'].includes(c.localName));
    if (kids.length < 2) continue;
    const flexGrid = /flex|grid/.test(cs.display);
    const positioned = kids.some((c) => ['absolute', 'fixed'].includes(getComputedStyle(c).position));
    if (!flexGrid && !positioned) continue;
    if (!K.isVisible(el) || el.closest('[aria-hidden="true"]')) continue;
    const items = kids.map((c, i) => ({ i, el: c, b: box(c) })).filter((it) => it.b.w > 0 && it.b.h > 0);
    if (items.length < 2) continue;
    const { byRow, byCol } = visualOrders(items, cs.direction === 'rtl');
    const same = (arr) => arr.every((it, k) => k === 0 || arr[k - 1].i < it.i);
    if (same(byRow) || same(byCol)) continue;
    const FOC = 'a[href], button, input:not([type="hidden"]), select, textarea, [tabindex]:not([tabindex="-1"])';
    const segs = items.map((it) => {
      const foc = Array.from(it.el.querySelectorAll(FOC)).filter((f) => K.isVisible(f));
      if (it.el.matches(FOC) && K.isVisible(it.el)) foc.unshift(it.el);
      const pos = getComputedStyle(it.el).position;
      return {
        i: it.i, text: norm(it.el.innerText || it.el.textContent).slice(0, 160), decorative: decorative(it.el),
        focusables: foc.length, names: foc.slice(0, 6).map((f) => norm(K.nameFallback(f) || f.getAttribute('name') || f.localName).slice(0, 60)),
        tag: it.el.localName, fixed: pos === 'fixed' || pos === 'sticky',
      };
    });
    // decorative children (and fixed/sticky overlays) do not make a reading sequence: is the
    // order still wrong once they are left out?
    const segBy = new Map(segs.map((s) => [s.i, s]));
    const rowOf = (keep) => byRow.filter((it) => keep(segBy.get(it.i)));
    const decoOnly = same(rowOf((s) => !s.decorative));
    const fixedOnly = !decoOnly && same(rowOf((s) => !s.decorative && !s.fixed));
    const mv = decoOnly ? moved(byRow) : moved(rowOf((s) => !s.decorative));
    if (!mv.length) continue;
    seen.add(el);
    out.reorders.push({
      selector: sel(el), html: outer(el), lang: K.inheritedLang(el), display: cs.display,
      flex_direction: cs.flexDirection, positioned, segments: segs,
      visual: byRow.map((it) => it.i), moved: mv,
      decorative_only: decoOnly,
      fixed_only: fixedOnly,
      in_form: !!el.closest('form, fieldset, [role="form"], [role="group"], [role="radiogroup"]'),
      text: K.textOf(el).slice(0, 1500),
    });
  }

  // --- text columns made of spaces ------------------------------------------------------------------
  for (const el of Array.from(body.querySelectorAll('pre, [style*="white-space"], div, p')).slice(0, 3000)) {
    if (out.pre_columns.length >= MAX) break;
    const ws = getComputedStyle(el).whiteSpace;
    if (!/^pre/.test(ws) || !K.isVisible(el)) continue;
    if (el.querySelector('code') || el.closest('code') || /\b(code|highlight|hljs|language-|lang-)/i.test(el.className || '')) continue;
    const lines = (el.textContent || '').split('\n');
    const gaps = [];
    for (const line of lines) {
      const m = /\S( {3,}|\t+)\S/.exec(line);
      if (m && /\p{L}/u.test(line.slice(0, m.index + 1)) && /\p{L}/u.test(line.slice(m.index + m[0].length - 1))) {
        gaps.push(m.index + m[0].length - 1);
      }
    }
    if (gaps.length < 3) continue;
    // the right-hand column starts at (almost) the same character position
    const counts = new Map();
    gaps.forEach((g) => counts.set(g, (counts.get(g) || 0) + 1));
    let aligned = 0;
    for (const g of counts.keys()) aligned = Math.max(aligned, gaps.filter((x) => Math.abs(x - g) <= 2).length);
    if (aligned < 3) continue;
    const firstLines = lines.filter((l) => l.trim()).slice(0, 3).map((l) => l.replace(/\s+$/, ''));
    out.pre_columns.push({ selector: sel(el), html: outer(el), lang: K.inheritedLang(el), lines: gaps.length,
                           first: firstLines, text: (el.textContent || '').slice(0, 1500) });
  }

  // --- words spelt with spaces between the letters ------------------------------------------------
  const SPACED = /(?:^|[\s(«"'„“])((?:\p{Lu} ){3,}\p{Lu}|(?:\p{L} ){4,}\p{L})(?=$|[\s.,:;!?)»"'“”])/u;
  const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
  let node, count = 0;
  while ((node = walker.nextNode()) && out.spaced_words.length < MAX && count < 20000) {
    count += 1;
    const v = node.nodeValue;
    if (!v || v.length < 7) continue;
    const m = SPACED.exec(v);
    if (!m) continue;
    const p = node.parentElement;
    if (!p || p.closest('script, style, code, pre, kbd, samp, [aria-hidden="true"]') || !K.isVisible(p)) continue;
    const block = K.nearestBlock(p);
    out.spaced_words.push({ selector: sel(block), html: outer(block), lang: K.inheritedLang(p), word: m[1],
                            text: K.textOf(block).slice(0, 600) });
  }

  // --- layout tables read row by row ------------------------------------------------------------------
  const END = /[.!?…:;)"»”]$/;
  for (const tb of Array.from(document.querySelectorAll('table')).slice(0, MAX)) {
    if (!K.isVisible(tb) || tb.querySelector('th, caption') || tb.closest('[aria-hidden="true"]')) continue;
    const rows = Array.from(tb.rows).filter((r) => r.closest('table') === tb);
    if (rows.length < 2) continue;
    const grid = rows.map((r) => Array.from(r.cells).map((c) => norm(c.innerText || c.textContent)));
    const cols = Math.max(...grid.map((r) => r.length));
    if (cols < 2) continue;
    const prose = grid.flat().filter((t) => t.split(/\s+/).length >= 4);
    if (prose.length < 2) continue;
    let split = null;
    for (let r = 0; r + 1 < grid.length && !split; r++) {
      for (let c = 0; c < grid[r].length; c++) {
        const cur = grid[r][c], below = (grid[r + 1] || [])[c] || '';
        if (cur.split(/\s+/).length >= 3 && !END.test(cur) && /^\p{Ll}/u.test(below)) { split = { cur: cur.slice(-80), below: below.slice(0, 80) }; break; }
      }
    }
    out.layout_tables.push({ selector: sel(tb), html: outer(tb), lang: K.inheritedLang(tb), role: tb.getAttribute('role'),
                             rows: rows.length, cols, split, text: K.textOf(tb).slice(0, 1500) });
  }
  return out;
}
