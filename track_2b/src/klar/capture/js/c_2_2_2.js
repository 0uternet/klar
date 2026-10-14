/* Klar. 2.2.2 Pause, Stop, Hide helpers. Installed on an ISOLATED CLONE of the audited
 * page (a new browser context with a fake clock), never on the page other checks read.
 * Needs window.__klar (extractor library). Defines window.__k222. Read-only.
 */
() => {
  const K = window.__klar;
  const norm = K.norm;
  const MAX_EL = 4000;
  const REGIONISH = 'section, aside, article, figure, marquee, [role="region"], [role="marquee"], [role="timer"], ' +
    '[role="status"], [aria-live], [aria-roledescription]';
  const CLASSY = /carousel|slider|slideshow|ticker|marquee|news|live|rotat|swiper|slick|banner|teaser/i;
  const CONTROL = 'button, [role="button"], [role="switch"], a[href], input[type="checkbox"], input[type="radio"], select';
  let refs = [];
  const snaps = [];

  function component(el) {
    let n = el;
    for (let i = 0; i < 6 && n && n.parentElement; i++) {
      if (['body', 'main', 'html'].includes(n.localName)) break;
      if (n.id || n.matches(REGIONISH) || CLASSY.test(n.className && n.className.baseVal === undefined ? n.className : '')) return n;
      if (['body', 'main'].includes(n.parentElement.localName)) return n;
      n = n.parentElement;
    }
    return el.closest('p, div, section, li') || el;
  }

  function state(el) {
    const parts = [];
    const own = Array.from(el.childNodes).filter((c) => c.nodeType === 3).map((c) => c.nodeValue).join('').trim();
    if (own) parts.push('t:' + own.slice(0, 120));
    if (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1) parts.push('s:' + el.scrollLeft + ',' + el.scrollTop);
    if (el.hasAttribute('hidden')) parts.push('h');
    const cls = el.getAttribute('class'); if (cls) parts.push('c:' + cls);
    const st = el.getAttribute('style'); if (st) parts.push('y:' + st);
    const ah = el.getAttribute('aria-hidden'); if (ah) parts.push('a:' + ah);
    if (el.localName === 'img') parts.push('i:' + (el.getAttribute('src') || ''));
    return parts.join('|');
  }

  function textOf(el) { return K.textOf(el).slice(0, 400); }

  function controlsNear(comp) {
    const scope = [comp];
    // a sibling counts only when it is a control or a small control bar (not another component)
    for (const sib of [comp.previousElementSibling, comp.nextElementSibling]) {
      if (!sib) continue;
      const ctrls = Array.from(sib.querySelectorAll(CONTROL));
      const rest = norm(sib.textContent).length - ctrls.reduce((s, c) => s + norm(c.textContent).length, 0);
      if (sib.matches(CONTROL) || (ctrls.length && rest <= 15)) scope.push(sib);
    }
    const parent = comp.parentElement;
    if (parent && !['body', 'main', 'html'].includes(parent.localName) && norm(parent.textContent).length <= norm(comp.textContent).length + 400) scope.push(parent);
    const out = [], seen = new Set();
    const add = (el, inside) => {
      if (seen.has(el) || !K.isVisible(el) || out.length >= 12) return;
      seen.add(el);
      // never a candidate for a click: submit/reset buttons and any button that belongs to a form
      const type = (el.getAttribute('type') || '').toLowerCase();
      const buttonLike = el.localName === 'button' || el.getAttribute('role') === 'button' ||
        (el.localName === 'input' && ['button', 'submit', 'reset', 'image'].includes(type || 'text'));
      if (buttonLike && (['submit', 'reset', 'image'].includes(type) || el.form || el.closest('form'))) return;
      out.push({
        selector: K.cssPath(el), tag: el.localName, type: (el.getAttribute('type') || '').toLowerCase(),
        name: norm(K.nameFallback(el) || el.getAttribute('aria-label') || el.value || '').slice(0, 80),
        href: el.localName === 'a' ? (el.getAttribute('href') || '') : '',
        options: el.localName === 'select' ? Array.from(el.options).map((o) => norm(o.textContent)).slice(0, 8) : [],
        html: (el.outerHTML || '').slice(0, 300), inside,
      });
    };
    for (const s of scope) {
      if (s.matches(CONTROL)) add(s, s === comp);
      for (const c of s.querySelectorAll(CONTROL)) add(c, comp.contains(c));
    }
    for (const c of document.querySelectorAll('[aria-controls]')) {
      const ids = (c.getAttribute('aria-controls') || '').split(/\s+/).filter(Boolean);
      if (ids.some((id) => { const t = document.getElementById(id); return t && (comp.contains(t) || t.contains(comp)); })) add(c, false);
    }
    return out;
  }

  window.__k222 = {
    /** CSS animations / transitions currently in effect, with their total duration. */
    animations: () => {
      const out = [];
      for (const a of document.getAnimations().slice(0, 200)) {
        const eff = a.effect;
        const el = eff && eff.target;
        if (!el || el.nodeType !== 1 || !K.isVisible(el)) continue;
        const timing = eff.getComputedTiming();
        let props = [];
        try { props = Array.from(new Set(eff.getKeyframes().flatMap((k) => Object.keys(k)))).filter((p) => !['offset', 'easing', 'composite', 'computedOffset'].includes(p)); } catch (e) { /* ignore */ }
        const comp = component(el);
        out.push({
          selector: K.cssPath(el), component: K.cssPath(comp), name: a.animationName || a.transitionProperty || '',
          end_ms: timing.endTime === Infinity ? -1 : Math.round(timing.endTime || 0),
          iterations: timing.iterations === Infinity ? -1 : timing.iterations, play_state: a.playState,
          props, text: textOf(el), has_text: !!textOf(el) || !!el.querySelector('img[alt]:not([alt=""])'),
        });
      }
      return out;
    },
    marquees: () => Array.from(document.querySelectorAll('marquee, blink')).filter((m) => K.isVisible(m)).slice(0, 10)
      .map((m) => ({ selector: K.cssPath(m), component: K.cssPath(component(m)), text: textOf(m), has_text: !!textOf(m) })),
    snapshot: () => {
      if (!refs.length) refs = Array.from(document.body.querySelectorAll('*')).filter((e) => !['script', 'style', 'template', 'noscript'].includes(e.localName)).slice(0, MAX_EL);
      snaps.push(refs.map(state));
      return snaps.length;
    },
    /** Elements whose observable state changed in EVERY interval between snapshots. */
    changes: () => {
      if (snaps.length < 3) return [];
      const changedIn = (a, b) => { const s = new Set(); a.forEach((v, i) => { if (v !== b[i]) s.add(i); }); return s; };
      const sets = [];
      for (let k = 1; k < snaps.length; k++) sets.push(changedIn(snaps[k - 1], snaps[k]));
      const byComp = new Map();
      sets.forEach((set, k) => set.forEach((i) => {
        const el = refs[i];
        if (!el.isConnected) return;
        const comp = component(el);
        if (!byComp.has(comp)) byComp.set(comp, { intervals: new Set(), els: new Set(), text_only: true });
        const rec = byComp.get(comp);
        rec.intervals.add(k);
        rec.els.add(el);
        const a = snaps[k][i], b = snaps[k + 1][i];
        const strip = (s) => s.split('|').filter((p) => !p.startsWith('t:')).join('|');
        if (strip(a) !== strip(b)) rec.text_only = false;
      }));
      const out = [];
      for (const [comp, rec] of byComp) {
        if (rec.intervals.size < sets.length || out.length >= 10) continue;
        const els = Array.from(rec.els);
        out.push({ component: K.cssPath(comp), selector: K.cssPath(els[0]), count: els.length, text_only: rec.text_only,
                   text: textOf(comp), has_text: els.some((e) => !!norm(e.textContent)) || !!textOf(comp) });
      }
      return out;
    },
    reset: () => { snaps.length = 0; refs = []; return true; },
    describe: (sel) => {
      let comp; try { comp = document.querySelector(sel); } catch (e) { return null; }
      if (!comp) return null;
      const bodyText = norm(document.body.innerText || '').length;
      return { selector: sel, html: (comp.outerHTML || '').slice(0, 1500), text: textOf(comp), lang: K.inheritedLang(comp),
               visible: K.isVisible(comp), other_text: Math.max(0, bodyText - norm(comp.innerText || '').length),
               controls: controlsNear(comp) };
    },
    /** Is anything inside the component still moving? (CSS animations running past 5 s, or snapshot changes.) */
    cssMoving: (sel) => {
      let comp; try { comp = document.querySelector(sel); } catch (e) { return false; }
      if (!comp || !K.isVisible(comp)) return false;
      return document.getAnimations().some((a) => {
        const el = a.effect && a.effect.target;
        if (!el || !comp.contains(el) || !K.isVisible(el) || a.playState !== 'running') return false;
        const end = a.effect.getComputedTiming().endTime;
        return end === Infinity || end > 5000;
      });
    },
    visible: (sel) => { try { const n = document.querySelector(sel); return !!n && K.isVisible(n); } catch (e) { return false; } },
  };
  return true;
}
