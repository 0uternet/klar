/* 1.4.3 Contrast (Minimum): computed text colours and what lies behind the text.
 *
 * One record per element that has its own visible text (like ACT afw4f7 and axe's
 * color-contrast: the element whose child text nodes are measured). READ-ONLY;
 * scrolls to measure, then restores the scroll position.
 */
(arg, K) => {
  const max = (arg && arg.max) || 400;
  const SKIP = 'script,style,noscript,template,svg,math,textarea,select,option,optgroup,head,title';
  const seen = new Set();
  const els = [];
  const walker = document.createTreeWalker(document.body || document.documentElement, NodeFilter.SHOW_TEXT, {
    acceptNode(n) {
      if (!n.nodeValue || !K.LETTER.test(n.nodeValue)) return NodeFilter.FILTER_REJECT;
      const p = n.parentElement;
      if (!p || seen.has(p) || p.closest(SKIP)) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  let node;
  while ((node = walker.nextNode()) && els.length < max) {
    const p = node.parentElement;
    seen.add(p);
    if (!K.visible(p)) continue;
    const st = K.cs(p);
    if (st.visibility !== 'visible') continue;
    const range = document.createRange();
    range.selectNodeContents(node);
    const rects = Array.from(range.getClientRects()).filter((r) => r.width >= 2 && r.height >= 2);
    if (!rects.length) continue;  // clipped to 1 px (visually hidden) or empty
    const r0 = rects[0];
    const docX = r0.left + window.scrollX, docY = r0.top + window.scrollY;
    if (docX + r0.width <= 0 || docY + r0.height <= 0) continue;  // moved off-screen
    els.push({ el: p, node, docY, h: r0.height });
  }
  const sx = window.scrollX, sy = window.scrollY;
  const out = [];
  els.sort((a, b) => a.docY - b.docY);
  for (const { el, node, docY, h } of els) {
    K.into(docY, h);
    const range = document.createRange();
    range.selectNodeContents(node);
    const rects = Array.from(range.getClientRects()).filter((r) => r.width >= 2 && r.height >= 2);
    const r = rects[0];
    const point = r ? { x: r.left + Math.min(r.width / 2, 12), y: r.top + r.height / 2 } : null;
    const st = K.cs(el);
    const bg = K.layers(el, point);
    out.push({
      selector: K.path(el), tag: el.localName, html: K.outer(el), text: K.ownText(el).slice(0, 300),
      color: st.color, fill: st.webkitTextFillColor || '', font_px: parseFloat(st.fontSize) || 0,
      weight: parseFloat(st.fontWeight) || 400, opacity: K.opacity(el), text_shadow: st.textShadow || 'none',
      // text-shadow and -webkit-text-stroke are inherited: the element's computed value covers its ancestors
      stroke_w: parseFloat(st.webkitTextStrokeWidth) || 0, stroke_c: st.webkitTextStrokeColor || '',
      layers: bg.layers, via_point: bg.via_point, inactive: K.inactive(el), hidden: K.hiddenFromAT(el),
      brand: K.brand(el), interactive: !!el.closest('a[href], button, [role="button"], [role="link"], label, summary'),
      rect: K.rect(el), lang: K.lang(el),
    });
  }
  window.scrollTo(sx, sy);
  return out;
}
