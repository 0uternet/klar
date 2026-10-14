"""Form interaction probe (for 3.3.1 / 3.3.3 / 3.3.4 checks).

For each form (max 3) we open a SEPARATE tab of the same browser context, load
the same page, fill empty/invalid values, submit, and record what the page says
back: native validation messages, aria-invalid fields with their error texts,
role=alert / aria-live messages and text that appeared.

It submits forms, so it only runs when allow_form_submit=True (the bundled demo
site served by this app, and the test set's local servers), and even then only
for forms whose target origin is allow-listed (CaptureOptions.form_origins). On
any other site no form is submitted, whatever its method; requests other than
GET/HEAD to other origins are aborted as a second line of defence.
"""

from __future__ import annotations

import logging

from urllib.parse import urlparse

from klar.capture.page import CapturedPage

log = logging.getLogger(__name__)

_FILL_AND_SUBMIT_JS = """(formSel) => {
  const f = document.querySelector(formSel);
  if (!f) return { error: 'form not found' };
  const before = document.body.innerText;
  const bad = { email: 'not-an-email', tel: 'abc', url: 'not a url', number: '', date: '', text: '', search: '' };
  for (const el of f.elements) {
    const tag = el.localName, type = (el.type || '').toLowerCase();
    if (['hidden', 'submit', 'button', 'reset', 'image', 'file'].includes(type)) continue;
    if (type === 'checkbox' || type === 'radio') { el.checked = false; continue; }
    if (tag === 'select') { el.selectedIndex = 0; el.dispatchEvent(new Event('change', { bubbles: true })); continue; }
    if (el.pattern) { el.value = 'x'; }
    else if (type in bad) { el.value = bad[type]; }
    else { el.value = ''; }
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }
  window.__klarBefore = before;
  const submit = f.querySelector('button:not([type]), button[type="submit"], input[type="submit"], input[type="image"]');
  if (submit) { submit.click(); return { via: 'click' }; }
  if (f.requestSubmit) { f.requestSubmit(); return { via: 'requestSubmit' }; }
  f.submit(); return { via: 'submit' };
}"""

_COLLECT_JS = """(formSel) => {
  const K = window.__klar;
  const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
  const f = document.querySelector(formSel);
  const out = { native: [], invalid_fields: [], alerts: [], new_text: [] };
  if (f) {
    for (const el of f.elements) {
      if (el.willValidate && el.validity && !el.validity.valid) {
        out.native.push({ selector: K.cssPath(el), name: K.nameFallback(el), message: el.validationMessage });
      }
    }
  }
  const refText = (el, attr) => norm((el.getAttribute(attr) || '').split(/\\s+/).filter(Boolean)
    .map(id => { const t = document.getElementById(id); return t ? t.textContent : ''; }).join(' '));
  for (const el of document.querySelectorAll('[aria-invalid="true"]')) {
    const errormessage = refText(el, 'aria-errormessage'), describedby = refText(el, 'aria-describedby');
    out.invalid_fields.push({ selector: K.cssPath(el), name: K.nameFallback(el),
      error_text: errormessage || describedby, errormessage_text: errormessage, describedby_text: describedby,
      html: el.outerHTML.slice(0, 500) });
  }
  for (const el of document.querySelectorAll('[role="alert"], [role="status"], [aria-live]:not([aria-live="off"])')) {
    const tx = norm(el.innerText);
    if (tx) out.alerts.push({ selector: K.cssPath(el), text: tx.slice(0, 500), html: el.outerHTML.slice(0, 800) });
  }
  const before = new Set((window.__klarBefore || '').split('\\n').map(norm).filter(Boolean));
  out.new_text = document.body.innerText.split('\\n').map(norm).filter(l => l && !before.has(l)).slice(0, 20);
  return out;
}"""


def probe_forms(page: CapturedPage, opts, max_forms: int = 3) -> list[dict]:
    if not page.allow_form_submit or page.live is None:
        return []
    from klar.capture.browser import EXTRACT_JS, js, load
    from klar.netpolicy import origin_of

    allowed = set(opts.form_origins)
    blocked: list[str] = []

    def only_safe_methods(route, request):
        """During the probe, nothing but GET/HEAD may leave, except to allow-listed origins."""
        if request.method not in ("GET", "HEAD") and origin_of(request.url) not in allowed:
            blocked.append(f"{request.method} {request.url[:200]}")
            route.abort("blockedbyclient")
        else:
            route.fallback()

    results = []
    page_scheme = urlparse(page.url).scheme
    for form in page.forms[:max_forms]:
        target = form.get("action_url") or page.url
        scheme = urlparse(target).scheme
        networked = scheme in ("http", "https", "file")
        if (networked and origin_of(target) not in allowed) or (page_scheme in ("http", "https", "file")
                                                                and origin_of(page.url) not in allowed):
            results.append({"form_selector": form["selector"], "submitted_via": None, "navigated": False,
                            "skipped": "form target outside the allow-list: not submitted"})
            continue
        tab = page.live.context.new_page()
        tab.route("**/*", only_safe_methods)
        rec: dict = {"form_selector": form["selector"], "submitted_via": None, "navigated": False}
        try:
            load(tab, url=None if page.source_html is not None else page.url, html=page.source_html, opts=opts)
            url_before = tab.url
            started = tab.evaluate(js(_FILL_AND_SUBMIT_JS), form["selector"])
            rec["submitted_via"] = started.get("via")
            try:
                tab.wait_for_load_state("networkidle", timeout=3000)
            except Exception:
                pass
            tab.wait_for_timeout(500)
            rec["navigated"] = tab.url != url_before
            rec["url_after"] = tab.url
            if rec["navigated"]:
                tab.evaluate(EXTRACT_JS)
            rec.update(tab.evaluate(js(_COLLECT_JS), form["selector"]))
        except Exception as exc:
            rec["error"] = str(exc)[:200]
            log.info("form probe on %s failed: %s", form["selector"], exc)
        finally:
            try:
                tab.close()
            except Exception:
                pass
        rec["blocked_requests"] = list(blocked)
        results.append(rec)
    return results
