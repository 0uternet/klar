/* Klar. 1.3.1 Info and Relationships: facts about structure that is SHOWN but maybe
 * not CODED. Read-only (no DOM mutation). Evaluated with page.evaluate(src, opts);
 * needs the extractor library (window.__klar) for selectors, visibility and names.
 *
 * Returns { body_size, heading_styles, visual_headings, tables, fake_lists,
 *           choice_groups, kv_grids, run_ins }  (each list bounded).
 */
(opts) => {
  const K = window.__klar;
  const MAX = (opts && opts.max) || 40;
  const norm = K.norm;
  const out = { body_size: 16, heading_styles: [], visual_headings: [], tables: [], fake_lists: [],
                choice_groups: [], kv_grids: [], run_ins: [] };
  const px = (v) => parseFloat(v) || 0;
  const weight = (cs) => {
    const w = parseInt(cs.fontWeight, 10);
    return isNaN(w) ? (cs.fontWeight === 'bold' ? 700 : 400) : w;
  };
  const HEADING = 'h1,h2,h3,h4,h5,h6,[role="heading"]';
  const SKIP = 'a,button,label,legend,caption,th,summary,dt,nav,select,option,textarea,pre,code,table,' +
    'script,style,noscript,template,[aria-hidden="true"],[role="banner"],[role="contentinfo"],[role="navigation"],' +
    'body > header,body > footer,dialog';
  const BLOCKS = 'p,div,ul,ol,dl,table,form,section,article,figure,blockquote,fieldset,details,h1,h2,h3,h4,h5,h6,li,pre,img,input,select,textarea,button';
  const words = (s) => (s.match(/[\p{L}\p{N}][\p{L}\p{N}'’-]*/gu) || []).length;
  const body = document.body;
  if (!body) return out;
  const lang = (el) => K.inheritedLang(el);
  const sel = (el) => K.cssPath(el);
  const outer = (el) => { const h = el.outerHTML || ''; return h.length > 1500 ? h.slice(0, 1500) : h; };

  // --- body text size: the font size carrying most paragraph text ------------------------
  const sizes = new Map();
  for (const p of Array.from(document.querySelectorAll('p, li, dd, td')).slice(0, 2000)) {
    const t = norm(p.textContent);
    if (t.length < 40 || !K.isVisible(p)) continue;
    const s = Math.round(px(getComputedStyle(p).fontSize) * 2) / 2;
    sizes.set(s, (sizes.get(s) || 0) + t.length);
  }
  if (sizes.size) out.body_size = Array.from(sizes.entries()).sort((a, b) => b[1] - a[1])[0][0];
  const bodySize = out.body_size;

  // --- real heading styles -----------------------------------------------------------------
  for (const h of Array.from(document.querySelectorAll(HEADING)).slice(0, 200)) {
    if (!K.isVisible(h)) continue;
    const cs = getComputedStyle(h);
    const level = h.getAttribute('aria-level') ? Number(h.getAttribute('aria-level')) : Number(h.localName.slice(1)) || null;
    out.heading_styles.push({ level, size: px(cs.fontSize), weight: weight(cs), color: cs.color });
  }

  // --- label/value grids (two visual columns of short texts, no dl/table) --------------------
  const kvChildren = new Set();
  for (const g of Array.from(body.querySelectorAll('div, section, p')).slice(0, 4000)) {
    if (out.kv_grids.length >= MAX) break;
    const cs = getComputedStyle(g);
    if (!/grid/.test(cs.display)) continue;
    const tracks = cs.gridTemplateColumns.split(/\s+/).filter((x) => /px$/.test(x));
    if (tracks.length !== 2) continue;
    const kids = Array.from(g.children).filter((c) => K.isVisible(c));
    if (kids.length < 4 || kids.length % 2 !== 0) continue;
    if (kids.some((c) => c.querySelector('a,button,input,select,textarea,img,p,div,ul,ol,table') ||
                         norm(c.textContent).length > 80 || !norm(c.textContent))) continue;
    if (!K.isVisible(g) || g.closest(SKIP)) continue;
    const labels = kids.filter((_, i) => i % 2 === 0).map((c) => norm(c.textContent));
    const values = kids.filter((_, i) => i % 2 === 1).map((c) => norm(c.textContent));
    kids.forEach((c) => kvChildren.add(c));
    out.kv_grids.push({ selector: sel(g), html: outer(g), text: K.textOf(g), lang: lang(g), labels, values,
                        colon: labels.every((l) => /[:：]$/.test(l)) });
  }

  // --- visual headings: short bold/large standalone text followed by content ------------------
  function styledOf(el) {
    // the element whose style the text actually has: a single child covering the whole text
    let cur = el;
    for (let i = 0; i < 3; i++) {
      const kids = Array.from(cur.children);
      if (kids.length !== 1) break;
      const own = Array.from(cur.childNodes).filter((n) => n.nodeType === 3 && n.nodeValue.trim());
      if (own.length) break;
      if (norm(kids[0].textContent) !== norm(cur.textContent)) break;
      cur = kids[0];
    }
    return cur;
  }
  function nextContent(el) {
    let n = el.nextElementSibling;
    for (let i = 0; n && i < 4; i++, n = n.nextElementSibling) {
      if (!K.isVisible(n)) continue;
      const t = norm(n.textContent);
      if (!t && !n.querySelector('input,select,textarea,img,table')) continue;
      return n;
    }
    return null;
  }
  const seen = new Set();
  for (const el of Array.from(body.querySelectorAll('p, div, span, b, strong, font')).slice(0, 6000)) {
    if (out.visual_headings.length >= MAX) break;
    if (seen.has(el) || kvChildren.has(el) || el.closest(HEADING) || el.closest(SKIP)) continue;
    const cs = getComputedStyle(el);
    if (cs.display.startsWith('inline') || cs.display === 'contents' || cs.display === 'none') continue;
    if (el.querySelector(BLOCKS + ',' + HEADING)) {
      // a block that wraps one link is a card title; any other nested block → not a leaf
      const a = el.querySelector('a');
      if (!(a && el.querySelectorAll('*').length <= 3 && norm(a.textContent) === norm(el.textContent))) continue;
    }
    if (!K.isVisible(el)) continue;
    const text = K.textOf(el);
    const n = words(text);
    if (n < 1 || n > 12 || text.length > 100 || text.length < 2) continue;
    if (/[.!?…]["»”)]?$/.test(text) || /[:：]$/.test(text)) continue;  // sentences and run-in labels
    if (/^\s*([•·▪▫◦‣⁃∙●○■□►▶▸✓✔→*]|[-–—]\s|\d{1,2}[.)]\s)/.test(text)) continue;  // list-like
    const styled = styledOf(el);
    const scs = getComputedStyle(styled);
    const size = px(scs.fontSize);
    const w = Math.max(weight(scs), weight(cs));
    const big = size >= bodySize * 1.15;
    const bold = w >= 600 || ['b', 'strong'].includes(styled.localName);
    if (!big && !bold) continue;
    const next = nextContent(el);
    if (!next || next.matches(HEADING) || next.querySelector(HEADING)) continue;
    const nextText = norm(next.textContent);
    if (nextText.length < 15 && !next.querySelector('input,select,textarea,table')) continue;
    seen.add(el);
    el.querySelectorAll('*').forEach((d) => seen.add(d));
    const link = el.querySelector('a');
    const isLink = !!link && norm(link.textContent) === norm(text);
    const color = scs.color;
    const matches = out.heading_styles
      .filter((h) => Math.abs(h.size - size) <= 0.6 && (h.weight >= 600) === (w >= 600) && h.color === color)
      .map((h) => h.level);
    const sentences = (nextText.match(/[.!?…](\s|$)/g) || []).length;
    const r = el.getBoundingClientRect();
    out.visual_headings.push({
      selector: sel(el), html: outer(el), text, lang: lang(el), size, weight: w, ratio: size / bodySize,
      bold, big, matches, is_link: isLink, next_selector: sel(next), next_tag: next.localName,
      next_text: nextText.slice(0, 300), next_sentences: sentences,
      in_card: !!el.closest('li, article, [class*="card"], [class*="teaser"]'),
      rect: { x: Math.round(r.left + scrollX), y: Math.round(r.top + scrollY), w: Math.round(r.width), h: Math.round(r.height) },
    });
  }

  // --- tables --------------------------------------------------------------------------------
  const bg = (cell) => getComputedStyle(cell).backgroundColor;
  const strongCell = (cell) => {
    if (weight(getComputedStyle(cell)) >= 600) return true;
    const t = norm(cell.textContent);
    const b = cell.querySelector('b, strong');
    return !!b && t && norm(b.textContent) === t;
  };
  for (const tb of Array.from(document.querySelectorAll('table')).slice(0, MAX)) {
    if (!K.isVisible(tb) || tb.closest('[aria-hidden="true"]')) continue;
    const rows = Array.from(tb.rows).filter((r) => r.closest('table') === tb);
    const cells = rows.flatMap((r) => Array.from(r.cells));
    if (!cells.length) continue;
    const cols = Math.max(...rows.map((r) => Array.from(r.cells).reduce((s, c) => s + (c.colSpan || 1), 0)));
    const texts = cells.map((c) => norm(c.textContent));
    const nonEmpty = texts.filter(Boolean);
    const numeric = nonEmpty.filter((t) => /^[\d\s.,:'’%–\-+/()CHF€$°]+$/i.test(t) || /\d/.test(t) && t.length <= 12).length;
    const thCount = tb.querySelectorAll('th, [role="columnheader"], [role="rowheader"]').length;
    const blockCells = cells.filter((c) => c.querySelector('p, div > p, h1, h2, h3, h4, h5, h6, ul, ol, form, table, fieldset, img[width], input, select, textarea')).length;
    let firstRowDistinct = false, firstColDistinct = false;
    if (rows.length >= 2) {
      const r0 = Array.from(rows[0].cells), r1 = Array.from(rows[1].cells);
      const bodyBg = r1.length ? bg(r1[r1.length - 1]) : '';
      const bodyStrong = r1.length ? strongCell(r1[r1.length - 1]) : false;
      firstRowDistinct = r0.length >= 2 && r0.every((c) => (bg(c) !== bodyBg && bg(c) !== 'rgba(0, 0, 0, 0)') || (strongCell(c) && !bodyStrong));
      const c0 = rows.slice(1).map((r) => r.cells[0]).filter(Boolean);
      const c1 = rows.slice(1).map((r) => r.cells[1]).filter(Boolean);
      firstColDistinct = c0.length >= 2 && c1.length >= 2 && c0.every((c) => strongCell(c) || bg(c) !== bg(c1[0])) &&
        !c1.every((c) => strongCell(c));
    }
    const lin = rows.slice(0, 8).map((r) => Array.from(r.cells).map((c) => norm(c.textContent).slice(0, 40)).join(' | ')).join(' / ');
    out.tables.push({
      selector: sel(tb), html: outer(tb), lang: lang(tb), role: tb.getAttribute('role'), rows: rows.length, cols,
      th: thCount, scope: !!tb.querySelector('th[scope], [headers]'), caption: tb.caption ? norm(tb.caption.textContent) : '',
      summary: norm(tb.getAttribute('summary') || ''), nested: !!tb.querySelector('table'), block_cells: blockCells,
      cells: cells.length, avg_len: nonEmpty.length ? nonEmpty.reduce((s, t) => s + t.length, 0) / nonEmpty.length : 0,
      max_len: Math.max(0, ...nonEmpty.map((t) => t.length)), numeric_share: nonEmpty.length ? numeric / nonEmpty.length : 0,
      first_row_distinct: firstRowDistinct, first_col_distinct: firstColDistinct, linear: lin.slice(0, 600),
    });
  }

  // --- lists drawn with characters ---------------------------------------------------------------
  const MARK = /^\s*([•·▪▫◦‣⁃∙●○■□►▶▸✓✔✗→*]|[-–—](?=\s)|(\d{1,2})[.)](?=\s)|([a-z])\)(?=\s))/;
  function markerKind(line) {
    const m = MARK.exec(line);
    if (!m) return null;
    if (m[2]) return { kind: 'num', n: Number(m[2]) };
    if (m[3]) return { kind: 'alpha', n: m[3].charCodeAt(0) - 96 };
    return { kind: m[1] === '–' || m[1] === '—' ? '-' : m[1], n: 0 };
  }
  function runOf(lines) {
    // longest run of ≥ 3 consecutive lines with the same marker (numbers/letters must count up)
    let best = 0, cur = 0, prev = null;
    for (const l of lines) {
      const k = markerKind(l);
      if (k && prev && k.kind === prev.kind && (k.kind !== 'num' && k.kind !== 'alpha' || k.n === prev.n + 1)) cur += 1;
      else cur = k && (k.kind !== 'num' && k.kind !== 'alpha' || k.n === 1) ? 1 : 0;
      prev = k;
      best = Math.max(best, cur);
    }
    return best;
  }
  const listSeen = new Set();
  for (const el of Array.from(body.querySelectorAll('p, div, td, span')).slice(0, 6000)) {
    if (out.fake_lists.length >= MAX) break;
    if (el.closest('ul, ol, li, pre, code, nav, [aria-hidden="true"], [role="list"]') || listSeen.has(el)) continue;
    if (!K.isVisible(el)) continue;
    // (a) lines separated by <br> inside one block
    if (el.querySelector(':scope > br')) {
      const lines = (el.innerText || '').split('\n').map((s) => s.trim()).filter(Boolean);
      const run = runOf(lines);
      if (run >= 3) {
        listSeen.add(el);
        out.fake_lists.push({ selector: sel(el), html: outer(el), text: K.textOf(el), lang: lang(el), items: run,
                              first: lines.slice(0, 4), how: 'br' });
        continue;
      }
    }
    // (b) consecutive sibling blocks each starting with a marker
    const kids = Array.from(el.children).filter((c) => ['p', 'div', 'span'].includes(c.localName) && K.isVisible(c));
    if (kids.length >= 3) {
      const lines = kids.map((c) => norm(c.textContent));
      const run = runOf(lines);
      if (run >= 3) {
        listSeen.add(el);
        kids.forEach((c) => listSeen.add(c));
        out.fake_lists.push({ selector: sel(el), html: outer(el), text: K.textOf(el), lang: lang(el), items: run,
                              first: lines.slice(0, 4), how: 'siblings' });
      }
    }
  }

  // --- groups of radio buttons / checkboxes ---------------------------------------------------------
  const groups = new Map();
  for (const inp of Array.from(document.querySelectorAll('input[type="radio"], input[type="checkbox"]')).slice(0, 400)) {
    if (!K.isVisible(inp) && !(inp.labels && inp.labels.length && K.isVisible(inp.labels[0]))) continue;
    const key = inp.type + '|' + (inp.form ? sel(inp.form) : '') + '|' + (inp.name || ('#' + (inp.closest('fieldset,div,p,form') ? sel(inp.closest('fieldset,div,p,form')) : '')));
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(inp);
  }
  function lca(nodes) {
    let a = nodes[0].parentElement;
    while (a && !nodes.every((n) => a.contains(n))) a = a.parentElement;
    return a || body;
  }
  for (const [key, inputs] of groups) {
    if (out.choice_groups.length >= MAX) break;
    if (inputs.length < 2) continue;
    const fs = inputs[0].closest('fieldset');
    const legend = fs && inputs.every((i) => fs.contains(i)) && fs.querySelector('legend') ? norm(fs.querySelector('legend').textContent) : '';
    const grp = inputs[0].closest('[role="group"], [role="radiogroup"]');
    const grpName = grp && inputs.every((i) => grp.contains(i)) ? norm(K.nameFallback(grp)) : '';
    const box = lca(inputs);
    // visible question: text inside the group box before the first control, else the text
    // right before the box (up to three levels up)
    let question = '';
    for (const ch of box.childNodes) {
      if (ch.nodeType === 1 && (ch.contains(inputs[0]) || ch.matches('input, label, select, textarea'))) break;
      const t = norm(ch.textContent);
      if (t) question = (question + ' ' + t).trim();
    }
    question = question.slice(0, 200);
    let n = box;
    for (let i = 0; i < 3 && n && !question; i++) {
      let p = n.previousElementSibling;
      while (p && !norm(p.textContent)) p = p.previousElementSibling;
      if (p && !p.matches('fieldset, form, input, select, textarea, ul, ol, table') && norm(p.textContent).length <= 150) question = norm(p.textContent);
      if (!question) {
        const own = Array.from(n.childNodes).filter((c) => c.nodeType === 3).map((c) => norm(c.nodeValue)).join(' ');
        if (own) question = own.slice(0, 200);
      }
      n = n.parentElement;
      if (n && (n === body || n.localName === 'form' || n.localName === 'main')) break;
    }
    out.choice_groups.push({
      selector: sel(box), html: outer(box), text: K.textOf(box), lang: lang(box), type: inputs[0].type, count: inputs.length,
      labels: inputs.map((i) => norm(K.nameFallback(i))).slice(0, 12), legend, group_name: grpName,
      in_fieldset: !!legend, question, first: sel(inputs[0]),
    });
  }

  // --- bold run-in labels at the start of a paragraph (emphasis, not a heading) ------------------------
  for (const b of Array.from(body.querySelectorAll('p > b:first-child, p > strong:first-child')).slice(0, 400)) {
    if (out.run_ins.length >= 10) break;
    const p = b.parentElement;
    const bt = norm(b.textContent), pt = norm(p.textContent);
    if (!/[:：]$/.test(bt) || !pt.startsWith(bt) || words(pt.slice(bt.length)) < 3 || !K.isVisible(b)) continue;
    if (p.closest(SKIP)) continue;
    out.run_ins.push({ selector: sel(b), html: outer(b), text: bt, lang: lang(b), paragraph: pt.slice(0, 200) });
  }
  return out;
}
