/* Klar. visible labels and instructions of form controls (check 3.3.2), loaded by
 * klar/checks/c_3_3_2.py. READ-ONLY. What a sighted user sees BEFORE typing:
 * visible <label>/aria-labelledby text (visually-hidden text does not count), legend,
 * visible aria-describedby hints, other visible text in the field's own wrapper,
 * required markers, pattern; radio groups as one unit; per form the instructions
 * outside labels.
 */
(maxCount) => {
  const K = window.__klar;
  const norm = (s) => (s || '').replace(/[\s ​]+/g, ' ').trim();
  const FIELD = 'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="reset"])' +
    ':not([type="image"]), select, textarea';

  function reallyVisible(el) {
    if (!el || !K.isVisible(el)) return false;
    for (let n = el; n && n !== document.body; n = n.parentElement) {
      const cs = getComputedStyle(n);
      const r = n.getBoundingClientRect();
      if ((r.width <= 2 || r.height <= 2) && cs.overflow !== 'visible') return false;
      if (/rect\(0(px)?,? 0(px)?,? 0(px)?,? 0(px)?\)/.test(cs.clip)) return false;
      if (cs.clipPath && /inset\(50%/.test(cs.clipPath)) return false;
      if (r.right < 0 || r.bottom < 0) return false;
    }
    return true;
  }
  const vtext = (el) => (reallyVisible(el) ? norm(el.innerText) : '');
  const refs = (el, attr) => (el.getAttribute(attr) || '').split(/\s+/).filter(Boolean)
    .map((id) => document.getElementById(id)).filter(Boolean);

  function wrapperOf(el, form) {
    let w = el;
    const same = (f) => f === el || (el.name && f.name === el.name && (f.type === 'radio' || f.type === 'checkbox'));
    for (let p = el.parentElement; p && p !== form && p !== document.body; p = p.parentElement) {
      if (Array.from(p.querySelectorAll(FIELD)).some((f) => !same(f))) break;
      w = p;
    }
    return w;
  }

  // G167: the first visible button after the field in its wrapper (or in a one-field form).
  function adjacentButton(el, form) {
    const single = form && form.querySelectorAll(FIELD).length === 1;
    const scope = single ? form : (el.parentElement && el.parentElement.parentElement) || el.parentElement;
    if (!scope) return null;
    const b = Array.from(scope.querySelectorAll('button, input[type="submit"], input[type="button"], input[type="image"], [role="button"]'))
      .find((x) => (el.compareDocumentPosition(x) & Node.DOCUMENT_POSITION_FOLLOWING) && reallyVisible(x));
    if (!b) return null;
    const text = b.localName === 'input' && b.type !== 'image' ? norm(b.value || '') : vtext(b);
    const icon = !text && (b.type === 'image' || !!b.querySelector('svg, img, i, [class*="icon"]'));
    return { text: text.slice(0, 80), icon };
  }

  function searchLike(el) {
    const id = `${el.name || ''} ${el.id || ''}`.toLowerCase();
    return el.type === 'search' || el.getAttribute('role') === 'searchbox' || !!el.closest('[role="search"], search') ||
      /search|such|recherch|cerca|query|^q\b/.test(id);
  }

  function info(el) {
    const form = el.form || el.closest('form');
    const labels = Array.from(el.labels || []);
    const lb = refs(el, 'aria-labelledby');
    const visLabel = norm(labels.map(vtext).concat(lb.map(vtext)).join(' '));
    const hidLabel = norm(labels.filter((l) => !reallyVisible(l)).map((l) => l.textContent).join(' '));
    const imgOnly = labels.some((l) => reallyVisible(l) && !norm(l.innerText) && l.querySelector('img, svg, [role="img"]'));
    const imgAlt = norm(labels.map((l) => Array.from(l.querySelectorAll('img[alt], [role="img"][aria-label]'))
      .map((i) => i.getAttribute('alt') || i.getAttribute('aria-label')).join(' ')).join(' '));
    const fs = el.closest('fieldset');
    const legend = fs ? fs.querySelector(':scope > legend') : null;
    const w = wrapperOf(el, form);
    let wrapText = w !== el ? vtext(w) : '';
    for (const l of labels) wrapText = wrapText.replace(norm(l.innerText), ' ');
    return {
      selector: K.cssPath(el), tag: el.localName, type: (el.getAttribute('type') || el.type || '').toLowerCase(),
      name_attr: el.name || '', required: !!(el.required || el.getAttribute('aria-required') === 'true'),
      pattern: el.getAttribute('pattern'), title: el.getAttribute('title') || '', placeholder: el.getAttribute('placeholder') || '',
      autocomplete: el.getAttribute('autocomplete') || '', aria_label: el.getAttribute('aria-label') || '',
      visible_label: visLabel, hidden_label: hidLabel, label_image_only: imgOnly, label_image_alt: imgAlt,
      legend: legend ? vtext(legend) : '', hint: norm(refs(el, 'aria-describedby').map(vtext).join(' ')),
      wrapper_text: norm(wrapText).slice(0, 300), form: form ? K.cssPath(form) : null,
      adjacent_button: adjacentButton(el, form), search_like: searchLike(el),
      html: (el.outerHTML || '').slice(0, 600), lang: K.inheritedLang(el),
    };
  }

  function groupInfo(name, radios) {
    const first = radios[0];
    let box = first.closest('fieldset, [role="radiogroup"]');
    if (!box) {
      box = first.parentElement;
      while (box && !radios.every((r) => box.contains(r))) box = box.parentElement;
    }
    const legend = box && box.matches('fieldset') ? box.querySelector(':scope > legend') : null;
    const lb = box ? refs(box, 'aria-labelledby') : [];
    let prev = '';
    for (let s = box ? box.previousElementSibling : null; s && !prev; s = s.previousElementSibling) {
      if (s.matches(FIELD) || s.querySelector(FIELD)) break;
      prev = vtext(s);
    }
    return {
      selector: box ? K.cssPath(box) : K.cssPath(first), group: true, name_attr: name,
      group_label: norm((legend ? vtext(legend) : '') + ' ' + lb.map(vtext).join(' ')),
      options: radios.map((r) => norm(Array.from(r.labels || []).map((l) => l.innerText).join(' '))).filter(Boolean),
      prev_text: prev.slice(0, 200), required: radios.some((r) => r.required),
      form: first.form ? K.cssPath(first.form) : null, html: box ? (box.outerHTML || '').slice(0, 900) : '',
      lang: K.inheritedLang(first),
    };
  }

  const out = { fields: [], groups: [], forms: [] };
  const radiosByName = new Map();
  for (const el of document.querySelectorAll(FIELD)) {
    if (out.fields.length >= (maxCount || 200)) break;
    if (!K.isVisible(el) || el.disabled) continue;
    if (el.type === 'radio' && el.name) {
      if (!radiosByName.has(el.name)) radiosByName.set(el.name, []);
      radiosByName.get(el.name).push(el);
      continue;
    }
    out.fields.push(info(el));
  }
  for (const [name, radios] of radiosByName) {
    if (radios.length >= 2) out.groups.push(groupInfo(name, radios));
    else out.fields.push(info(radios[0]));
  }
  for (const f of document.forms) {
    if (!K.isVisible(f)) continue;
    const fields = Array.from(f.querySelectorAll(FIELD)).filter((x) => K.isVisible(x));
    let instr = '';
    for (const el of f.querySelectorAll('p, div, span, small, legend')) {
      if (el.closest('label') || el.querySelector(FIELD) || el.querySelector('p, div')) continue;
      const tx = vtext(el);
      if (tx && instr.length < 400) instr += ' ' + tx;
    }
    for (let s = f.previousElementSibling, k = 0; s && k < 2; s = s.previousElementSibling, k++) {
      if (s.matches('p, div') && !s.querySelector(FIELD)) instr = vtext(s) + ' ' + instr;
    }
    const names = new Set();
    let units = 0;
    for (const x of fields) {
      if ((x.type === 'radio' || x.type === 'checkbox') && x.name) { if (names.has(x.name)) continue; names.add(x.name); }
      units++;
    }
    out.forms.push({ selector: K.cssPath(f), units, action: f.getAttribute('action'),
                     instructions: norm(instr).slice(0, 500),
                     star_labels: Array.from(f.querySelectorAll('label, legend')).filter((l) => /\*/.test(l.innerText)).length });
  }
  return out;
}
