/* Klar. controls with a visible label and an author-given name (check 2.5.3), loaded by
 * klar/checks/c_2_5_3.py. READ-ONLY.
 *
 * Returns links, buttons, role widgets and form fields whose accessible name comes from
 * aria-label / aria-labelledby (otherwise the name IS the visible text). For each one:
 * the visible label (text content for widgets, the visible <label> for fields, the value
 * of input buttons), the text blocks inside the control (heading, paragraph, …), the
 * placeholder, and the extractor's name.
 */
(maxCount) => {
  const K = window.__klar;
  const norm = (s) => (s || '').replace(/[\s ​]+/g, ' ').trim();
  const SEL = 'a[href], button, input[type="submit"], input[type="button"], input[type="reset"], ' +
    '[role="button"], [role="link"], [role="menuitem"], [role="tab"], [role="checkbox"], [role="radio"], ' +
    '[role="switch"], [role="option"], [role="treeitem"], input:not([type="hidden"]), select, textarea';
  const FIELD = 'input:not([type="submit"]):not([type="button"]):not([type="reset"]):not([type="image"]), select, textarea';

  function visibleText(el) {
    if (!K.isVisible(el)) return '';
    return norm(el.innerText);
  }

  function blocks(el) {
    const out = [];
    for (const b of el.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, div, span')) {
      const cs = getComputedStyle(b);
      if (cs.display.startsWith('inline') && !/^H/.test(b.tagName)) continue;
      if (b.querySelector('h1, h2, h3, h4, h5, h6, p, div')) continue;
      const tx = visibleText(b);
      if (tx) out.push(tx);
    }
    return out.slice(0, 6);
  }

  function collect(max) {
    const out = [];
    for (const el of document.querySelectorAll(SEL)) {
      if (out.length >= (max || 300)) break;
      if (!el.hasAttribute('aria-label') && !el.hasAttribute('aria-labelledby')) continue;
      if (!K.isVisible(el) || el.closest('[aria-hidden="true"]')) continue;
      const isField = el.matches(FIELD) && !el.matches('[role="button"], [role="link"]');
      let label = '', source = 'content';
      if (isField) {
        const labels = Array.from(el.labels || []).filter((l) => K.isVisible(l));
        label = norm(labels.map((l) => l.innerText).join(' '));
        source = labels.length ? 'label' : 'none';
      } else if (el.localName === 'input') {
        label = norm(el.value); source = 'value';
      } else {
        label = visibleText(el);
      }
      out.push({
        selector: K.cssPath(el), tag: el.localName, role: el.getAttribute('role'), is_field: isField,
        label, label_source: source, blocks: isField ? [] : blocks(el), placeholder: el.getAttribute('placeholder') || '',
        aria_label: el.getAttribute('aria-label'), labelledby: !!el.getAttribute('aria-labelledby'),
        name_js: K.nameFallback(el), html: (el.outerHTML || '').slice(0, 1200), lang: K.inheritedLang(el),
        has_img: !!el.querySelector('img, svg, [role="img"]'),
      });
    }
    return out;
  }

  return collect(maxCount);
}
