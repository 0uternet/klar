/* Klar. widget facts (check 4.1.2), loaded by klar/checks/c_4_1_2.py.
 *
 *   window.__KW__.collect(map) READ-ONLY: non-semantic elements with an onclick attribute or a
 *                             listener (map: selector → event types, from the DevTools protocol) and
 *                             the facts that tell a control from a container; custom widgets with
 *                             their ARIA states, disclosure-like toggles, dual-purpose links,
 *                             native details/summary, icon-only controls and their names.
 *   window.__KW__.click(i)    (throw-away tab only, when the scan allows interaction)
 *   window.__KW__.observe(i)  state after the click: aria-expanded/-checked/-pressed/-selected,
 *                             own name, share of main text changed, hash, dialog.
 */
(() => {
  const K = window.__klar;
  const norm = (s) => (s || '').replace(/[\s ​]+/g, ' ').trim();
  const NATIVE = 'a[href], button, input, select, textarea, summary, details, label, option, area, iframe, video, audio';
  const WIDGET_ROLES = ['button', 'link', 'checkbox', 'switch', 'radio', 'tab', 'menuitem', 'menuitemcheckbox',
    'menuitemradio', 'option', 'slider', 'spinbutton', 'combobox', 'textbox', 'treeitem', 'searchbox'];
  const STATE = ['aria-expanded', 'aria-checked', 'aria-pressed', 'aria-selected'];
  const S = { toggles: [], snap: null };

  const focusable = (el) => el.tabIndex >= 0 && !el.disabled;
  const hiddenAnc = (el) => !!el.closest('[aria-hidden="true"]');
  const states = (el) => Object.fromEntries(STATE.map((a) => [a, el.getAttribute(a)]));
  const visText = (el) => (K.isVisible(el) ? norm(el.innerText) : '');

  const INTERACTIVE = 'a[href], button, input:not([type="hidden"]), select, textarea, summary, ' +
    WIDGET_ROLES.map((r) => '[role="' + r + '"]').join(', ');

  /** Part of a small web component: a custom element (name with a hyphen) at most 3 levels up that
   *  holds no page landmark (an app wrapper such as <app-root> around <main> does not count), or a
   *  shadow root. */
  function inComponent(el) {
    let n = el;
    for (let i = 0; n && i <= 3; i++, n = n.parentElement) {
      if (n.localName && n.localName.includes('-') && !n.querySelector('main, header, nav, footer, form, [role="main"]')) return true;
    }
    return typeof ShadowRoot !== 'undefined' && el.getRootNode() instanceof ShadowRoot;
  }

  /** listenerMap: selector → event types registered on that element (DevTools protocol). */
  function collect(listenerMap) {
    const L = new Map();
    for (const [s, types] of Object.entries(listenerMap || {})) {
      let el = null;
      try { el = document.querySelector(s); } catch (e) { el = null; }
      if (el) L.set(el, types);
    }
    const clickables = [], widgets = [], toggles = [], dual = [], icons = [], details = [];
    let n = 0;
    for (const el of document.body.querySelectorAll('*')) {
      if (++n > 8000) break;
      const tag = el.localName;
      const role = (el.getAttribute('role') || '').trim().split(/\s+/)[0];
      if (['script', 'style', 'template', 'noscript', 'html', 'body', 'main', 'header', 'footer', 'nav'].includes(tag)) continue;
      const native = el.matches(NATIVE);
      if (!native && !WIDGET_ROLES.includes(role) && K.isVisible(el) && !el.parentElement.closest(INTERACTIVE)) {
        if ((el.hasAttribute('onclick') || L.has(el)) && clickables.length < 60) {
          const r = el.getBoundingClientRect();
          const text = visText(el);
          clickables.push({ selector: K.cssPath(el), tag, text: text.slice(0, 200), types: L.get(el) || [],
            onclick: el.hasAttribute('onclick'), focusable: focusable(el), aria_hidden: hiddenAnc(el),
            has_interactive: !!el.querySelector(INTERACTIVE), words: text ? text.split(' ').length : 0,
            chars: text.length, width: Math.round(r.width), height: Math.round(r.height),
            pointer: getComputedStyle(el).cursor === 'pointer', in_component: inComponent(el),
            html: (el.outerHTML || '').slice(0, 600) });
        }
      }
      if (!native && WIDGET_ROLES.includes(role) && K.isVisible(el)) {
        const list = el.closest('[role="tablist"]');
        widgets.push({ selector: K.cssPath(el), role, tag, states: states(el), focusable: focusable(el),
          name: K.nameFallback(el), tablist_selected: list ? !!list.querySelector('[role="tab"][aria-selected]') : null,
          aria_hidden: hiddenAnc(el), html: (el.outerHTML || '').slice(0, 600) });
      }
      if (tag === 'details' && K.isVisible(el)) {
        const sm = el.querySelector(':scope > summary');
        if (sm) details.push({ selector: K.cssPath(sm), name: K.nameFallback(sm), html: (sm.outerHTML || '').slice(0, 400) });
      }
      const href = tag === 'a' ? (el.getAttribute('href') || '') : null;
      if (tag === 'a' && el.hasAttribute('href') && K.isVisible(el) && (el.hasAttribute('aria-haspopup') || el.hasAttribute('aria-expanded'))
          && href && !href.startsWith('#') && !href.startsWith('javascript')) {
        dual.push({ selector: K.cssPath(el), name: K.nameFallback(el), html: (el.outerHTML || '').slice(0, 600) });
        continue;
      }
      const isToggleish = (tag === 'button' && (el.type || '') === 'button') || role === 'button' || role === 'switch' ||
        role === 'checkbox' || role === 'tab' || (tag === 'a' && href !== null && (href === '' || href.startsWith('#') || href.startsWith('javascript'))) ||
        (el.hasAttribute('aria-expanded') && (native || role));
      if (isToggleish && K.isVisible(el) && !hiddenAnc(el) && !el.closest('form [type="submit"]') && toggles.length < 15) {
        S.toggles.push(el);
        toggles.push({ i: S.toggles.length - 1, selector: K.cssPath(el), tag, role, href, states: states(el),
          name: K.nameFallback(el), controls: el.getAttribute('aria-controls') || '', html: (el.outerHTML || '').slice(0, 600) });
      }
      if ((tag === 'button' || role === 'button' || (tag === 'a' && el.hasAttribute('href'))) && K.isVisible(el) && !hiddenAnc(el)) {
        const name = K.nameFallback(el);
        if (!visText(el) && name && icons.length < 40) {
          icons.push({ selector: K.cssPath(el), tag, name, html: (el.outerHTML || '').slice(0, 600) });
        }
      }
    }
    return { clickables, widgets, toggles, dual, icons, details };
  }

  function mainText() { return norm((document.querySelector('main, [role="main"]') || document.body).innerText); }

  function click(i) {
    const el = S.toggles[i];
    if (!el) return { error: 'gone' };
    S.snap = { states: states(el), name: K.nameFallback(el), text: mainText(), hash: location.hash };
    el.click();
    return { ok: true };
  }

  function observe(i) {
    const el = S.toggles[i];
    const b = S.snap;
    const now = mainText();
    const before = new Set(b.text.split(' '));
    const after = new Set(now.split(' '));
    let diff = 0;
    for (const w of after) if (!before.has(w)) diff++;
    for (const w of before) if (!after.has(w)) diff++;
    const dialog = Array.from(document.querySelectorAll('[role="dialog"], [role="alertdialog"], dialog[open]')).some((d) => K.isVisible(d));
    return { states_before: b.states, states_after: el ? states(el) : {}, name_before: b.name,
             name_after: el ? K.nameFallback(el) : '', content_changed: now !== b.text, words_changed: diff,
             hash_changed: location.hash !== b.hash, dialog };
  }

  window.__KW__ = { collect, click, observe };
})();
