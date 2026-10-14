/* Klar. form error probe (checks 3.3.1, 3.3.3, 3.3.4), loaded by klar/checks/c_3_3_1.py.
 *
 * Runs ONLY in a separate tab of the audited page (never in the captured page) and only
 * when the scan allows form submission. Python blocks every non-GET request and every
 * navigation of that tab, so nothing typed here ever leaves the browser.
 *
 *   window.__KGA__.prepare(formSelector)  → field list + "before" snapshot, instruments
 *                                          the value getters (which fields the page reads)
 *   window.__KGA__.fill(mode)             → mode "empty" | "junk"; clicks the submit button
 *   window.__KGA__.collect()              → per-field evidence + form-level messages
 *
 * Uses the extractor (window.__klar) for selectors and names. Read-only except for the
 * values it types into the form of this throw-away tab.
 */
(() => {
  const K = window.__klar;
  const norm = (s) => (s || '').replace(/[\s ​]+/g, ' ').trim();
  const FIELD = 'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="reset"])' +
    ':not([type="image"]), select, textarea';
  const STYLE_PROPS = ['borderTopColor', 'borderBottomColor', 'outlineColor', 'outlineStyle', 'backgroundColor', 'boxShadow'];
  const S = { form: null, fields: [], wrappers: [], before: new Map(), reads: new Set(), armed: false,
              formdata: false, styles: [], invalid0: [], desc0: [], hint0: [], visibleBefore: new Set(),
              controlsBefore: new Set(), active0: null };

  function reallyVisible(el) {
    if (!el || !K.isVisible(el)) return false;
    for (let n = el; n && n !== document.body; n = n.parentElement) {
      const cs = getComputedStyle(n);
      const r = n.getBoundingClientRect();
      if ((r.width <= 2 || r.height <= 2) && cs.overflow !== 'visible') return false;
      if (/rect\(0(px)?,? 0(px)?,? 0(px)?,? 0(px)?\)/.test(cs.clip)) return false;
      if (cs.clipPath && /inset\(50%/.test(cs.clipPath)) return false;
      if (parseFloat(cs.opacity) === 0) return false;
      if (r.right < 0 || r.bottom < 0) return false;
    }
    return true;
  }

  function ownText(el) {
    let t = '';
    for (const n of el.childNodes) if (n.nodeType === 3) t += n.nodeValue;
    return norm(t);
  }

  function idrefs(el, attr) {
    return (el.getAttribute(attr) || '').split(/\s+/).filter(Boolean)
      .map((id) => document.getElementById(id)).filter(Boolean);
  }

  function refText(el, attr, visibleOnly) {
    return norm(idrefs(el, attr).filter((t) => !visibleOnly || reallyVisible(t)).map((t) => t.textContent).join(' '));
  }

  function isField(el) { return el.matches && el.matches(FIELD); }

  /** Closest ancestor of `el` (below the form) that holds no other field; radios and
   *  checkboxes of the same name count as one field. */
  function wrapperOf(el) {
    let w = el;
    const same = (f) => f === el || (el.name && f.name === el.name && (f.type === 'radio' || f.type === 'checkbox'));
    for (let p = el.parentElement; p && p !== S.form && p !== document.body; p = p.parentElement) {
      const others = Array.from(p.querySelectorAll(FIELD)).filter((f) => !same(f));
      if (others.length) break;
      w = p;
    }
    return w;
  }

  function styleOf(el) {
    const cs = getComputedStyle(el);
    return STYLE_PROPS.map((p) => cs[p]).join('|');
  }

  function snapshotTexts() {
    const m = new Map();
    let n = 0;
    for (const el of document.body.querySelectorAll('*')) {
      if (++n > 6000) break;
      m.set(el, ownText(el));
    }
    return m;
  }

  function instrument(el, i) {
    for (const prop of ['value', 'checked', 'selectedIndex', 'validity', 'files']) {
      let proto = Object.getPrototypeOf(el), d = null;
      while (proto && !d) { d = Object.getOwnPropertyDescriptor(proto, prop); proto = Object.getPrototypeOf(proto); }
      if (!d || !d.get) continue;
      try {
        Object.defineProperty(el, prop, {
          configurable: true,
          get() { if (S.armed) S.reads.add(i); return d.get.call(this); },
          set(v) { if (d.set) d.set.call(this, v); },
        });
      } catch (e) { /* non-configurable: reads stay unknown */ }
    }
    for (const fn of ['checkValidity', 'reportValidity']) {
      const orig = el[fn];
      if (typeof orig !== 'function') continue;
      try { el[fn] = function () { if (S.armed) S.reads.add(i); return orig.apply(this, arguments); }; } catch (e) { /* ignore */ }
    }
  }

  function prepare(formSel) {
    let f = null;
    try { f = document.querySelector(formSel); } catch (e) { f = null; }
    if (!f) return { error: 'form not found' };
    S.form = f;
    S.fields = Array.from(f.querySelectorAll(FIELD)).filter((el) => K.isVisible(el) && !el.disabled && !el.readOnly);
    S.wrappers = S.fields.map(wrapperOf);
    S.styles = S.fields.map(styleOf);
    S.invalid0 = S.fields.map((el) => el.getAttribute('aria-invalid'));
    S.desc0 = S.fields.map((el) => refText(el, 'aria-describedby', true) + ' ' + refText(el, 'aria-errormessage', true));
    S.before = snapshotTexts();
    S.visibleBefore = new Set(Array.from(S.before.keys()).filter((el) => S.before.get(el) && reallyVisible(el)));
    S.controlsBefore = new Set(Array.from(document.querySelectorAll('button, [role="button"], input[type="submit"], input[type="button"], a[href]'))
      .filter((el) => K.isVisible(el)));
    S.fields.forEach(instrument);
    const OrigFD = window.FormData;
    window.FormData = function (form) { if (S.armed && form === S.form) S.formdata = true; return new OrigFD(...arguments); };
    window.FormData.prototype = OrigFD.prototype;
    const submit = f.querySelector('button:not([type]), button[type="submit"], input[type="submit"], input[type="image"]') ||
      (f.id ? document.querySelector('button[form="' + CSS.escape(f.id) + '"]') : null);
    return {
      novalidate: f.noValidate, has_submit: !!submit,
      fields: S.fields.map((el, i) => ({
        i, selector: K.cssPath(el), tag: el.localName, type: (el.getAttribute('type') || el.type || '').toLowerCase(),
        name: K.nameFallback(el), label: norm(Array.from(el.labels || []).map((l) => l.textContent).join(' ')),
        hint: S.desc0[i].trim(), required: !!(el.required || el.getAttribute('aria-required') === 'true'),
        pattern: el.getAttribute('pattern'), autocomplete: el.getAttribute('autocomplete'),
        static_invalid: el.getAttribute('aria-invalid') === 'true',
        static_message: el.getAttribute('aria-invalid') === 'true' ?
          norm(refText(el, 'aria-errormessage', true) || refText(el, 'aria-describedby', true)) : '',
        html: (el.outerHTML || '').slice(0, 600),
        wrapper_selector: S.wrappers[i] === el ? null : K.cssPath(S.wrappers[i]),
      })),
    };
  }

  function fill(mode) {
    const f = S.form;
    if (!f) return { error: 'not prepared' };
    const junk = { email: 'x', tel: 'x', url: 'x', text: 'x', search: 'x', password: 'x', '': 'x' };
    for (const el of S.fields) {
      const tag = el.localName, type = (el.type || '').toLowerCase();
      if (type === 'checkbox' || type === 'radio') { el.checked = false; continue; }
      if (tag === 'select') { el.selectedIndex = 0; }
      else if (tag === 'textarea') { el.value = mode === 'junk' ? 'x' : ''; }
      else { el.value = mode === 'junk' && type in junk ? junk[type] : ''; }
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
    }
    S.active0 = document.activeElement;
    const submit = f.querySelector('button:not([type]), button[type="submit"], input[type="submit"], input[type="image"]') ||
      (f.id ? document.querySelector('button[form="' + CSS.escape(f.id) + '"]') : null);
    S.armed = true;
    let via = null;
    try {
      if (submit) { submit.click(); via = 'click'; }
      else if (f.requestSubmit) { f.requestSubmit(); via = 'requestSubmit'; }
    } finally { S.armed = false; }
    return { via };
  }

  function collect() {
    const f = S.form;
    const changed = [];  // [element, text, visible]
    let n = 0;
    for (const el of document.body.querySelectorAll('*')) {
      if (++n > 6000) break;
      const now = ownText(el);
      if (!now) continue;
      const was = S.before.has(el) ? S.before.get(el) : '';
      const visNow = reallyVisible(el);
      if (now !== was || (visNow && !S.visibleBefore.has(el))) changed.push([el, now, visNow]);
    }
    const inWrapper = (el) => S.wrappers.findIndex((w) => w.contains(el));
    const fields = S.fields.map((el, i) => {
      const w = S.wrappers[i];
      const refs = idrefs(el, 'aria-describedby').concat(idrefs(el, 'aria-errormessage'));
      const mine = changed.filter(([c]) => w.contains(c) || refs.some((r) => r.contains(c)));
      const vis = mine.filter((x) => x[2]).map((x) => x[1]);
      const hidden = mine.filter((x) => !x[2]).map((x) => x[1]);
      const associated = mine.filter(([c]) => refs.some((r) => r.contains(c))).map((x) => x[1]);
      const icons = Array.from(w.querySelectorAll('img, svg, [class*="icon"]'))
        .filter((x) => reallyVisible(x) && !S.visibleBefore.has(x) && !norm(x.textContent)).length;
      const native = !f.noValidate && el.willValidate && el.validity && !el.validity.valid ? el.validationMessage : '';
      return {
        i, marked: el.getAttribute('aria-invalid') === 'true' && S.invalid0[i] !== 'true',
        style_changed: styleOf(el) !== S.styles[i], icons, read: S.reads.has(i),
        focused: document.activeElement === el && S.active0 !== el,
        visible_text: norm(vis.join(' ')).slice(0, 400), hidden_text: norm(hidden.join(' ')).slice(0, 400),
        associated_text: norm(associated.join(' ')).slice(0, 400), native: native || '',
      };
    });
    const formMsgs = [];
    for (const [el, text, vis] of changed) {
      if (!vis || inWrapper(el) >= 0 || S.fields.some((fl) => idrefs(fl, 'aria-describedby').some((r) => r.contains(el)))) continue;
      if (formMsgs.length >= 6) break;
      const live = el.closest('[role="alert"], [role="status"], [aria-live]:not([aria-live="off"]), [role="alertdialog"], [role="dialog"], dialog');
      const links = Array.from((live || el).querySelectorAll('a[href^="#"]')).length;
      formMsgs.push({ text: text.slice(0, 400), live: !!live, links, in_form: !!(f && f.contains(el)) });
    }
    // merge consecutive pieces of one container (a summary list) into one message
    const newControls = Array.from(document.querySelectorAll('button, [role="button"], input[type="submit"], input[type="button"]'))
      .filter((el) => K.isVisible(el) && !S.controlsBefore.has(el) && !(f && f.contains(el)))
      .map((el) => norm(el.textContent || el.value)).filter(Boolean).slice(0, 6);
    const dialogOpen = Array.from(document.querySelectorAll('[role="dialog"], [role="alertdialog"], dialog[open]'))
      .some((d) => K.isVisible(d));
    return {
      fields, messages: formMsgs, form_visible: !!(f && K.isVisible(f)), new_controls: newControls,
      dialog_open: dialogOpen, formdata: S.formdata, any_read: S.reads.size > 0,
      new_text: changed.filter((x) => x[2]).map((x) => x[1]).slice(0, 12).join(' | ').slice(0, 600),
    };
  }

  window.__KGA__ = { prepare, fill, collect };
})();
