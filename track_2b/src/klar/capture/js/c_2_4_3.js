/* Klar. 2.4.3 Focus Order helpers. Installed on an ISOLATED CLONE of the audited page
 * (a new browser context), never on the page other checks read.
 * Needs window.__klar (extractor library). Defines window.__k243.
 */
() => {
  const K = window.__klar;
  const norm = K.norm;
  const FOC = 'a[href], area[href], button, input:not([type="hidden"]), select, textarea, summary, iframe, ' +
    '[tabindex], [contenteditable=""], [contenteditable="true"]';

  function hiddenByAncestors(el) {
    for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (parseFloat(cs.opacity) === 0) return true;
      if (cs.visibility === 'hidden') return true;
      const r = n.getBoundingClientRect();
      const clipped = (cs.clip && cs.clip.replace(/\s/g, '') === 'rect(0px,0px,0px,0px)') ||
        /inset\(50%|circle\(0/.test(cs.clipPath || '');
      if (clipped || (cs.overflow === 'hidden' && r.width <= 1 && r.height <= 1)) return true;
    }
    return false;
  }

  function onScreen(el) {
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return false;
    const docW = Math.max(document.documentElement.scrollWidth, innerWidth);
    const docH = Math.max(document.documentElement.scrollHeight, innerHeight);
    const x = r.left + scrollX, y = r.top + scrollY;
    return x + r.width > 0 && y + r.height > 0 && x < docW && y < docH && !hiddenByAncestors(el);
  }

  function fixedAncestor(el) {
    for (let n = el; n && n.nodeType === 1 && n !== document.body; n = n.parentElement) {
      const p = getComputedStyle(n).position;
      if (p === 'fixed' || p === 'sticky') return true;
    }
    return false;
  }

  function info(el) {
    if (!el || el === document.body || el === document.documentElement) return null;
    const group = el.closest('fieldset, [role="group"], [role="radiogroup"]');
    const region = el.closest('dialog, [role="dialog"], [role="alertdialog"], form, nav, aside, header, footer, main, section, [role="region"]');
    const b = el.getBoundingClientRect();
    const type = (el.getAttribute('type') || '').toLowerCase();
    return {
      selector: K.cssPath(el), tag: el.localName, type,
      name: norm(K.nameFallback(el) || el.getAttribute('name') || el.getAttribute('placeholder') || '').slice(0, 80),
      tabindex: el.hasAttribute('tabindex') ? parseInt(el.getAttribute('tabindex'), 10) : null,
      rect: { x: Math.round(b.left + scrollX), y: Math.round(b.top + scrollY), w: Math.round(b.width), h: Math.round(b.height) },
      visible: onScreen(el), fixed: fixedAncestor(el),
      group: group ? K.cssPath(group) : null, region: region ? K.cssPath(region) : null,
      form: el.form ? K.cssPath(el.form) : (el.closest('form') ? K.cssPath(el.closest('form')) : null),
      submit: (el.localName === 'button' && (type === 'submit' || (!type && !!el.form))) ||
        (el.localName === 'input' && ['submit', 'image'].includes(type)),
    };
  }

  function visibleFocusContainers() {
    // every visible element that contains (or is) a focusable element
    const out = new Set();
    for (const f of Array.from(document.querySelectorAll(FOC)).slice(0, 3000)) {
      if (!K.isVisible(f)) continue;
      for (let n = f; n && n !== document.body; n = n.parentElement) out.add(n);
    }
    return out;
  }

  let before = new Set();
  window.__k243 = {
    active: () => info(document.activeElement),
    reset: () => { if (document.activeElement && document.activeElement.blur) document.activeElement.blur(); window.scrollTo(0, 0); return true; },
    remember: () => { before = visibleFocusContainers(); return before.size; },
    /** Topmost elements that became visible (with focusables) since remember(). */
    appeared: () => {
      const now = visibleFocusContainers();
      const fresh = Array.from(now).filter((n) => !before.has(n));
      const top = fresh.filter((n) => !fresh.some((m) => m !== n && m.contains(n)));
      return top.slice(0, 5).map((n) => ({
        selector: K.cssPath(n), tag: n.localName, html: (n.outerHTML || '').slice(0, 1200), text: K.textOf(n).slice(0, 300),
        dialog: n.matches('dialog, [role="dialog"], [role="alertdialog"]') || !!n.querySelector('dialog, [role="dialog"]'),
        modal: (() => { try { return n.matches(':modal') || !!n.querySelector(':modal') || n.getAttribute('aria-modal') === 'true'; } catch (e) { return false; } })(),
        contains_focus: n.contains(document.activeElement),
      }));
    },
    focusIn: (selectors) => {
      const a = document.activeElement;
      return selectors.some((s) => { try { const n = document.querySelector(s); return !!n && n.contains(a); } catch (e) { return false; } });
    },
    /** External sites (nothing is activated): controls that ANNOUNCE opened content, then hidden dialogs. */
    announced: (max) => {
      const out = [];
      for (const el of document.querySelectorAll('[aria-haspopup]:not([aria-haspopup="false"]), [aria-expanded], [aria-controls]')) {
        if (out.length >= max) break;
        if (!K.isVisible(el) || el.matches('input, select, textarea')) continue;
        out.push({ selector: K.cssPath(el), name: norm(K.nameFallback(el)).slice(0, 80), html: (el.outerHTML || '').slice(0, 600) });
      }
      for (const d of document.querySelectorAll('dialog, [role="dialog"], [role="alertdialog"], [aria-modal="true"]')) {
        if (out.length >= max) break;
        if (K.isVisible(d) || !d.querySelector('a[href], button, input, select, textarea, [tabindex]')) continue;
        out.push({ selector: K.cssPath(d), name: norm(K.nameFallback(d) || '').slice(0, 80) || d.localName,
                   html: (d.outerHTML || '').slice(0, 600) });
      }
      return out;
    },
    /** Controls that may open a dialog, menu or inserted content (no links with a real target, no submit). */
    triggers: (max) => {
      const out = [];
      for (const el of document.querySelectorAll('button, [role="button"], [aria-haspopup], [aria-expanded], [aria-controls]')) {
        if (out.length >= max) break;
        if (!K.isVisible(el) || el.disabled) continue;
        if (el.localName === 'a' && !/^(#|javascript:)/i.test(el.getAttribute('href') || '#')) continue;
        const type = (el.getAttribute('type') || '').toLowerCase();
        if (el.localName === 'button' && (type === 'submit' || type === 'reset' || (!type && el.form))) continue;
        if (el.localName === 'input') continue;
        out.push({ selector: K.cssPath(el), name: norm(K.nameFallback(el)).slice(0, 80),
                   html: (el.outerHTML || '').slice(0, 600) });
      }
      return out;
    },
  };
  return true;
}
