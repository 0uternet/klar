/* Klar. on-input probe (check 3.2.2), loaded by klar/checks/c_3_2_2.py.
 *
 * Runs ONLY in a throw-away tab of the audited page, only when the scan allows form
 * submission. Python answers every navigation of that tab with "204 No Content" and
 * aborts every non-GET request, so changing a control never leaves the browser.
 *
 *   window.__KOI__.list()      → controls whose setting can be changed (select, radio group,
 *                                checkbox, short/numeric text field) + the text before/after
 *   window.__KOI__.change(i)   → snapshot, then change the setting (select / click); text
 *                                fields are typed by Python with real key events
 *   window.__KOI__.observe(i)  → focus move, submit, new window, heading change, share of new text
 */
(() => {
  const K = window.__klar;
  const norm = (s) => (s || '').replace(/[\s ​]+/g, ' ').trim();
  const S = { controls: [], snap: null, submits: 0 };
  document.addEventListener('submit', () => { S.submits++; }, true);
  const origSubmit = HTMLFormElement.prototype.submit;
  HTMLFormElement.prototype.submit = function () { S.submits++; return origSubmit.apply(this, arguments); };
  const origReq = HTMLFormElement.prototype.requestSubmit;
  if (origReq) HTMLFormElement.prototype.requestSubmit = function () { S.submits++; return origReq.apply(this, arguments); };

  function textAround(el, group) {
    const box = (group || el).closest('form, section, article, main, [role="main"]') || document.body;
    const skip = 'script,style,template,select,option,noscript';
    let before = '', after = '', where = 0;
    const self = group || el;
    const walker = document.createTreeWalker(box, NodeFilter.SHOW_TEXT, {
      acceptNode(n) {
        const p = n.parentElement;
        if (!p || p.closest(skip)) return NodeFilter.FILTER_REJECT;
        if (p.closest('[aria-hidden="true"]')) return NodeFilter.FILTER_REJECT;
        return K.isVisible(p) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      },
    });
    let n;
    while ((n = walker.nextNode())) {
      const pos = self.compareDocumentPosition(n);
      if (self.contains(n)) { if (group) before += ' ' + n.nodeValue; continue; }
      if (pos & Node.DOCUMENT_POSITION_PRECEDING) before += ' ' + n.nodeValue;
      else if (pos & Node.DOCUMENT_POSITION_FOLLOWING) after += ' ' + n.nodeValue;
      where++;
    }
    return { before: norm(before).slice(-400), after: norm(after).slice(0, 300) };
  }

  function described(el) {
    return norm((el.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean)
      .map((id) => { const t = document.getElementById(id); return t ? t.textContent : ''; }).join(' '));
  }

  function list(max) {
    const out = [];
    const seen = new Set();
    for (const el of document.querySelectorAll('select, input[type="radio"], input[type="checkbox"], input:not([type]), input[type="text"], input[type="tel"], input[type="number"]')) {
      if (out.length >= (max || 10)) break;
      if (!K.isVisible(el) || el.disabled || el.readOnly) continue;
      const type = (el.type || '').toLowerCase();
      let kind = el.localName === 'select' ? 'select' : type;
      let group = null;
      if (type === 'radio') {
        if (!el.name || seen.has('r:' + el.name)) continue;
        seen.add('r:' + el.name);
        const peers = Array.from(document.querySelectorAll('input[type="radio"]')).filter((r) => r.name === el.name);
        group = el.closest('fieldset, [role="radiogroup"]') || null;
        const target = peers.find((r) => !r.checked && K.isVisible(r)) || null;
        if (!target) continue;
        out.push({ el: target, kind, group });
        continue;
      }
      if (kind === 'text' || kind === 'tel' || kind === 'number' || kind === '') {
        const ml = el.maxLength > 0 && el.maxLength <= 12;
        const numeric = /numeric|decimal/.test(el.getAttribute('inputmode') || '') || /\\d/.test(el.getAttribute('pattern') || '');
        if (!ml && !numeric) continue;
        kind = 'text';
        group = el.closest('fieldset, [role="group"]') || null;
        if (group && seen.has(group)) continue;
        if (group) seen.add(group);
      }
      out.push({ el, kind, group });
    }
    S.controls = out;
    return out.map((c, i) => {
      const around = textAround(c.el, c.group);
      return {
        i, kind: c.kind, selector: K.cssPath(c.el), group_selector: c.group ? K.cssPath(c.group) : null,
        label: K.nameFallback(c.el), described: described(c.el) || (c.group ? described(c.group) : ''),
        before: around.before, after: around.after, maxlength: c.el.maxLength > 0 ? c.el.maxLength : null,
        html: (c.el.outerHTML || '').slice(0, 600), group_html: c.group ? (c.group.outerHTML || '').slice(0, 1200) : '',
      };
    });
  }

  function mainOf() { return document.querySelector('main, [role="main"]') || document.body; }

  function snapshot() {
    const m = mainOf();
    return {
      lines: new Set((m.innerText || '').split('\n').map(norm).filter(Boolean)),
      chars: norm(m.innerText).length || 1,
      headings: Array.from(m.querySelectorAll('h1, h2, h3, h4, h5, h6')).filter(K.isVisible).map((h) => norm(h.innerText)).join('|'),
      hash: location.hash, scrollY: window.scrollY,
    };
  }

  function change(i) {
    const c = S.controls[i];
    if (!c) return { error: 'no control' };
    S.snap = snapshot();
    S.submits = 0;
    c.el.focus();
    S.active0 = document.activeElement;
    if (c.kind === 'select') {
      const opts = Array.from(c.el.options);
      let k = opts.findIndex((o, j) => j !== c.el.selectedIndex && !o.disabled && o.value !== '');
      if (k < 0) k = opts.findIndex((o, j) => j !== c.el.selectedIndex);
      if (k < 0) return { error: 'single option' };
      c.el.selectedIndex = k;
      c.el.dispatchEvent(new Event('input', { bubbles: true }));
      c.el.dispatchEvent(new Event('change', { bubbles: true }));
      return { done: 'select' };
    }
    if (c.kind === 'radio' || c.kind === 'checkbox') { c.el.click(); return { done: 'click' }; }
    return { type: c.el.maxLength > 0 && c.el.maxLength <= 12 ? c.el.maxLength : 4 };
  }

  function observe(i) {
    const c = S.controls[i];
    const before = S.snap;
    const now = snapshot();
    const m = mainOf();
    let newChars = 0;
    for (const line of (m.innerText || '').split('\n').map(norm).filter(Boolean)) if (!before.lines.has(line)) newChars += line.length;
    const a = document.activeElement;
    const inGroup = c && c.group && a && c.group.contains(a) && a !== c.el;
    const moved = !!(a && a !== S.active0 && a !== document.body && c && a !== c.el);
    return {
      submits: S.submits, focus_moved: moved, focus_to_field: moved && !!a.matches('input, select, textarea'),
      focus_in_group: !!inGroup, focus_target: moved ? K.nameFallback(a) : '',
      headings_changed: now.headings !== before.headings, new_text_ratio: Math.round(100 * newChars / before.chars) / 100,
      hash_changed: now.hash !== before.hash, opened: window.__koiOpened || 0,
    };
  }

  window.__KOI__ = { list, change, observe };
})();
