/* 1.4.5 Images of Text: graphics that may contain text (READ-ONLY).
 *
 * <img>, <input type="image">, role="img", <canvas>, inline <svg> without <text>
 * (SVG <text> is real text), and elements painted with a CSS background image (url()).
 * Facts per graphic: rendered size, alternative, whether it sits in a link / button,
 * logo signals, and whether HTML text inside a background-image element is hidden
 * (CSS image replacement: text-indent, font-size 0, transparent colour, clipping).
 */
(arg, K) => {
  const MIN_W = 40, MIN_H = 16, MIN_AREA = 2000;
  const out = [];
  const seen = new Set();

  function sized(el) {
    const r = el.getBoundingClientRect();
    if (r.width < MIN_W || r.height < MIN_H || r.width * r.height < MIN_AREA) return null;
    if (r.width <= 48 && r.height <= 48) return null;  // icon-sized
    return r;
  }

  function hiddenText(el) {
    const txt = K.norm(el.textContent);
    if (!K.LETTER.test(txt)) return '';
    const st = K.cs(el);
    if (parseFloat(st.textIndent) <= -500 || parseFloat(st.fontSize) < 2 || K.transparent(st.color)) return txt.slice(0, 200);
    const v = el.innerText ? K.norm(el.innerText) : '';
    if (!v) return txt.slice(0, 200);
    return '';
  }

  // Text that is really painted over the element's box (not moved out by text-indent, not
  // transparent, not clipped away): HTML text over a background picture, not text in it.
  function shownText(el) {
    const er = el.getBoundingClientRect();
    const parts = [];
    const tw = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = tw.nextNode()) && parts.length < 20) {
      const t = K.norm(n.nodeValue);
      if (!t || !K.LETTER.test(t)) continue;
      const p = n.parentElement;
      if (!p || !K.visible(p)) continue;
      const st = K.cs(p);
      if (parseFloat(st.fontSize) < 2 || K.transparent(st.color)) continue;
      const rg = document.createRange();
      rg.selectNodeContents(n);
      const r = rg.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) continue;
      if (r.right <= er.left || r.left >= er.right || r.bottom <= er.top || r.top >= er.bottom) continue;
      parts.push(t);
    }
    return parts.join(' ').slice(0, 200);
  }

  function push(el, kind, extra) {
    if (seen.has(el) || out.length >= 80) return;
    seen.add(el);
    out.push(Object.assign({
      selector: K.path(el), tag: el.localName, kind, html: K.outer(el), rect: K.rect(el), lang: K.lang(el),
      alt: el.getAttribute('alt'), label: el.getAttribute('aria-label') || '', title: el.getAttribute('title') || '',
      in_control: !!el.closest('a[href], button, [role="button"], [role="link"]'), brand: K.brand(el),
      hidden: K.hiddenFromAT(el),
      control_text: (() => { const c = el.closest('a[href], button'); return c ? K.norm(c.innerText).slice(0, 120) : ''; })(),
    }, extra || {}));
  }

  for (const el of document.querySelectorAll('img, input[type="image"], [role="img"], canvas, svg')) {
    if (el.localName !== 'svg' && el.closest('svg')) continue;
    if (el.localName === 'svg' && (el.parentElement && el.parentElement.closest('svg'))) continue;
    if (!K.visible(el) || !sized(el)) continue;
    if (el.localName === 'svg' && el.querySelector('text')) continue;  // SVG text is real text
    // An icon hidden from assistive technology inside a link or button (arrows, chevrons).
    if (el.localName === 'svg' && el.getAttribute('aria-hidden') === 'true' &&
        el.closest('a[href], button, [role="button"], [role="link"]')) continue;
    push(el, el.localName === 'svg' ? 'svg' : 'img');
  }

  const all = document.body ? document.body.getElementsByTagName('*') : [];
  for (let i = 0; i < all.length && out.length < 80; i++) {
    const el = all[i];
    if (seen.has(el) || el.closest('svg')) continue;
    const st = K.cs(el);
    if (!st.backgroundImage || !/url\(/.test(st.backgroundImage)) continue;
    if (!K.visible(el) || !sized(el)) continue;
    push(el, 'background', { background: st.backgroundImage.slice(0, 200), hidden_text: hiddenText(el),
                             visible_text: shownText(el) });
  }
  return out;
}
