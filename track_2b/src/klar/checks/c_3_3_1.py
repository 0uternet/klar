"""3.3.1 Error Identification, level A. ACT rule 36b590 (error message describes
invalid form field value). Also home of the form interaction shared by 3.3.3 and
3.3.4 (`form_evidence`).

Interaction (only where the scan allows form submission: the bundled demo site and
the evaluation's local test pages; `page.allow_form_submit`, and the form must be on
the existing probe's allow-list, see capture/probe.py). For each form (max 3) a
throw-away tab of the same browser context loads the page (its own GET requests go
to the allow-listed server, as in the scan itself; any non-GET request is aborted) and
submits the form with every text field set to "x" (an invalid non-empty value), and
again with every field empty unless the first submission already produced evidence
for every text field. From the moment Klar. starts typing, the tab sends nothing more:
a navigation (a submitted form, a redirect) is answered with "204 No Content" by Klar.
itself and every other request, GET included, is aborted. So the values Klar. types are
never sent to any server. capture/js/c_3_3_1_probe.js records, per field: aria-invalid,
a style change (border/background), new icons, visible and visually-hidden text that
appeared in the field's own wrapper or in its aria-describedby/aria-errormessage
targets, the browser's own validation message, focus, and whether the page's script
READ the field's value during submit (instrumented getters). Text that appeared
elsewhere (a form-level box, an alert dialog) is attributed to the fields the script
read but did not mark with their own text. When native validation blocks the
submit, the passes are repeated with `noValidate` so that script checks run too.
On every other site no form is submitted: each form gets one cantTell note asking a
person to test it, and only error messages already present in the static DOM
(server-rendered, aria-invalid="true") are judged.

Decided in code
  * native validation message (no `novalidate`)              → passed (Understanding: native validation)
  * error shown only by colour/border/icon/aria-invalid      → failed (F81-like, ACT 36b590 expectation 2)
  * error text that exists but is not visible                → failed
  * the message contains the field's visible label           → passed (the item is named in text)
  * nothing observable, the form posts to a server           → cantTell (behaviour not observable)
  * the test submission failed twice (timeout)               → cantTell (never silently inapplicable)
Asked to Apertus (one categorical question per field that has a message)
  "What does the message tell the user about this field?"
    field_and_problem | field_only | problem_only | generic | not_an_error
  mapped in code (data/testset/PROTOCOL.md §3.3.1): field_and_problem, field_only → passed;
  problem_only → passed when the message is programmatically associated (aria-describedby /
  aria-errormessage / aria-invalid), cantTell when it is only visually next to the field
  (ACT accepts presentation, other readings do not) or elsewhere on the page; generic → failed;
  not_an_error (a receipt) → inapplicable.

Known limits: the probe types one invalid value ("x") and the empty value, not the value a
person would try; checks that only run on blur/input, asynchronous checks, checks that ask the
server (every request is stopped once Klar. types) and server checks are not observed; texts in canvas/images are not read; findings sit on the field (message
selectors from the probe tab may not exist in the captured DOM).
"""

from __future__ import annotations

import logging
import re
import secrets
import unicodedata
from functools import lru_cache
from pathlib import Path

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema, norm_ws
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

log = logging.getLogger(__name__)

PROMPT_VERSION = "3.3.1/v1"
MAX_FORMS = 3
MAX_FIELDS_PER_FORM = 12
SETTLE_MS = 450
JS_PATH = Path(__file__).resolve().parents[1] / "capture" / "js" / "c_3_3_1_probe.js"
_GLOBAL = "__kga_" + secrets.token_hex(5)
_PAGE_CACHE = "_klar_c331_forms"

# --- form interaction (shared with 3.3.3 and 3.3.4) ---------------------------------------


@lru_cache(maxsize=1)
def probe_js() -> str:
    return JS_PATH.read_text(encoding="utf-8").replace("__KGA__", _GLOBAL)


_CONTEXT_JS = """(sel) => {
  const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
  const f = document.querySelector(sel);
  if (!f) return {};
  const main = f.closest('main') || document.body;
  const h1 = main.querySelector('h1') || document.querySelector('h1');
  let before = '', after = '';
  const walk = (node, dir) => {
    for (let n = node; n && n !== main; n = n.parentElement) {
      let s = dir < 0 ? n.previousElementSibling : n.nextElementSibling;
      while (s) {
        if (!s.matches('script,style,template,nav,header,footer') && s.getClientRects().length) {
          const tx = norm(s.innerText);
          if (tx) { if (dir < 0) before = tx + ' ' + before; else after += ' ' + tx; }
        }
        if ((dir < 0 ? before : after).length > 900) return;
        s = dir < 0 ? s.previousElementSibling : s.nextElementSibling;
      }
    }
  };
  walk(f, -1); walk(f, 1);
  const submit = f.querySelector('button:not([type]), button[type="submit"], input[type="submit"]');
  return { heading: h1 ? norm(h1.innerText) : '', before: norm(before).slice(-700), after: norm(after).slice(0, 400),
           submit: submit ? norm(submit.innerText || submit.value) : '', form_text: norm(f.innerText).slice(0, 600) };
}"""


def interaction_allowed(page: CapturedPage) -> bool:
    return bool(page.allow_form_submit and page.live is not None)


def form_runs(page: CapturedPage) -> dict[str, dict]:
    """form selector → {"skipped": reason} | {"prepare", "context", "passes": {name: collect()}}.
    Cached on the page; empty when interaction is not allowed (pipeline thread only)."""
    cached = page.__dict__.get(_PAGE_CACHE)
    if cached is not None:
        return cached
    out: dict[str, dict] = {}
    if interaction_allowed(page):
        try:
            probed = {r.get("form_selector"): r for r in page.form_probe()}
        except Exception as exc:  # the shared probe failed: be conservative
            log.info("form probe failed: %s", exc)
            probed = {}
        for form in page.forms[:MAX_FORMS]:
            rec = probed.get(form["selector"])
            if rec is None or rec.get("skipped"):
                out[form["selector"]] = {"skipped": (rec or {}).get("skipped") or "not probed"}
                continue
            try:
                out[form["selector"]] = run_form(page, form["selector"])
            except Exception as exc:
                log.info("form interaction on %s failed: %s", form["selector"], exc)
                out[form["selector"]] = {"skipped": f"error: {exc}"[:160]}
    page.__dict__[_PAGE_CACHE] = out
    return out


JUNK_TYPES = frozenset({"", "text", "email", "tel", "url", "search", "password"})


def _needs_no_validate(rec: dict) -> bool:
    """Native validation stopped the submit while some fields had no native message: the
    page's own script never ran for them."""
    fields = rec.get("fields") or []
    return any(f.get("native") for f in fields) and any(not f.get("native") for f in fields)


def _empty_pass_needed(result: dict) -> bool:
    """The empty submission adds evidence only for text fields that "x" did not implicate
    (selects, checkboxes, number and date fields get the same value in both passes)."""
    meta = (result.get("prepare") or {}).get("fields") or []
    text_fields = [m["i"] for m in meta if m.get("type") in JUNK_TYPES or m.get("tag") == "textarea"]
    covered = {i for name in ("junk", "junk_nv") for i, ev in attribute(result["passes"].get(name) or {}).items()
               if ev.get("own")}
    return any(i not in covered for i in text_fields)


def run_form(page: CapturedPage, selector: str) -> dict:
    """At most 4 page loads per form, usually 1–2: "x", then empty only if needed; each again
    with noValidate only when native validation blocked the page's script."""
    result: dict = {"passes": {}}

    def run(mode: str, no_validate: bool) -> dict:
        rec = _one_pass(page, selector, mode, no_validate)
        if rec.get("error"):  # one retry: a slow page or a busy machine
            rec = _one_pass(page, selector, mode, no_validate)
        result["passes"][mode + ("_nv" if no_validate else "")] = rec
        result.setdefault("prepare", rec.get("prepare"))
        result.setdefault("context", rec.get("context"))
        return rec

    junk = run("junk", False)
    if junk.get("error"):
        return result
    if _needs_no_validate(junk):
        run("junk", True)
    if _empty_pass_needed(result):
        empty = run("empty", False)
        if _needs_no_validate(empty):
            run("empty", True)
    return result


def _one_pass(page: CapturedPage, selector: str, mode: str, no_validate: bool) -> dict:
    from klar.capture.browser import CaptureOptions, js, load

    tab = page.live.context.new_page()
    st: dict = {"armed": False, "navigations": [], "blocked": [], "dialogs": []}

    def handler(route, request):
        try:
            if st["armed"] and request.is_navigation_request() and request.frame == tab.main_frame:
                st["navigations"].append(f"{request.method} {request.url[:160]}")
                route.fulfill(status=204, body="")
                return
        except Exception:
            pass
        if st["armed"]:  # after the first change: nothing at all leaves the tab
            st["blocked"].append(request.method)
            route.abort("blockedbyclient")
            return
        if request.method not in ("GET", "HEAD"):
            st["blocked"].append(request.method)
            route.abort("blockedbyclient")
            return
        route.fallback()

    def on_dialog(d):
        st["dialogs"].append({"type": d.type, "message": (d.message or "")[:300]})
        try:
            d.dismiss()
        except Exception:
            pass

    tab.route("**/*", handler)
    tab.on("dialog", on_dialog)
    tab.add_init_script("window.open = function () { window.__kgaOpened = (window.__kgaOpened || 0) + 1; return null; };")
    rec: dict = {"mode": mode, "no_validate": no_validate}
    try:
        load(tab, url=None if page.source_html is not None else page.url, html=page.source_html,
             opts=CaptureOptions(scroll=False, idle_timeout_ms=1500, timeout_ms=15000))
        url_before = tab.url
        tab.evaluate(js(probe_js()))
        rec["prepare"] = tab.evaluate(f"s => window.{_GLOBAL}.prepare(s)", selector)
        rec["context"] = tab.evaluate(_CONTEXT_JS, selector)
        if no_validate:
            tab.evaluate("s => { const f = document.querySelector(s); if (f) f.noValidate = true; }", selector)
        st["armed"] = True
        rec["fill"] = tab.evaluate(f"m => window.{_GLOBAL}.fill(m)", mode)
        tab.wait_for_timeout(SETTLE_MS)
        rec.update(tab.evaluate(f"() => window.{_GLOBAL}.collect()"))
        rec["opened"] = tab.evaluate("() => window.__kgaOpened || 0")
        rec["url_changed"] = tab.url != url_before
    except Exception as exc:
        rec["error"] = str(exc)[:200]
    finally:
        try:
            tab.close()
        except Exception:
            pass
    rec["navigations"] = st["navigations"]
    rec["blocked"] = st["blocked"]
    rec["dialogs"] = st["dialogs"]
    return rec


def _implicated(f: dict) -> bool:
    return bool(f.get("visible_text") or f.get("native") or f.get("hidden_text") or f.get("marked")
                or f.get("style_changed") or f.get("icons"))


def _pass_messages(p: dict) -> list[str]:
    msgs = [m["text"] for m in p.get("messages", []) if m.get("text")]
    msgs += [d["message"] for d in p.get("dialogs", []) if d.get("message") and d.get("type") == "alert"]
    seen: list[str] = []
    for m in msgs:
        if m not in seen and not any(m in s for s in seen):
            seen.append(m)
    return seen


def attribute(p: dict) -> dict[int, dict]:
    """Per field index → evidence of one pass, form-level messages attributed to the
    fields the script read (or focused/marked) but did not give their own text."""
    fields = p.get("fields") or []
    msgs = _pass_messages(p)
    out: dict[int, dict] = {}
    # A message elsewhere is an ERROR message only when the page also shows an error state
    # (a field marked, focused or given its own text); otherwise it may be a receipt.
    error_state = any(_implicated(f) or f.get("focused") for f in fields)
    pool = [f for f in fields if not (f.get("visible_text") or f.get("native"))
            and (f.get("focused") or f.get("marked") or f.get("style_changed") or f.get("icons")
                 or f.get("hidden_text") or (f.get("read") and error_state))]
    for f in fields:
        ev = dict(f)
        ev["form_message"] = " ".join(msgs)[:400] if msgs and f in pool else ""
        ev["own"] = _implicated(f)
        if ev["own"] or ev["form_message"]:
            out[f["i"]] = ev
    return out


def form_evidence(page: CapturedPage) -> tuple[list[dict], list[dict]]:
    """(field records, form records) for 3.3.1 / 3.3.3 / 3.3.4.

    field record: selector, html, label, type, hint, required, pattern, autocomplete, form,
      source ("probe" | "static"), pass, evidence (see attribute()), static_message
    form record: selector, html, status ("tested" | "skipped" | "untested"), outcome facts."""
    fields_out: list[dict] = []
    forms_out: list[dict] = []
    runs = form_runs(page)
    forms = {f["selector"]: f for f in page.forms}
    for sel, form in list(forms.items())[: MAX_FORMS if runs else 50]:
        run = runs.get(sel)
        frec = {"selector": sel, "html": form.get("html", ""), "method": form.get("method"),
                "action": form.get("action"), "has_submit": bool(form.get("submit"))}
        if not run:
            frec["status"] = "untested"
            forms_out.append(frec)
            continue
        if run.get("skipped"):
            frec["status"] = "skipped"
            frec["reason"] = run["skipped"]
            forms_out.append(frec)
            continue
        prep = run.get("prepare") or {}
        passes = run.get("passes") or {}
        frec.update(status="tested", context=run.get("context") or {}, passes=passes,
                    novalidate=prep.get("novalidate"), fields=prep.get("fields") or [])
        per_pass = {name: attribute(p) for name, p in passes.items() if not p.get("error")}
        any_field = False
        for meta in (prep.get("fields") or [])[:MAX_FIELDS_PER_FORM]:
            i = meta["i"]
            chosen = None
            for want_own in (True, False):  # a pass with the field's own evidence beats an attributed message
                for name in ("junk", "junk_nv", "empty", "empty_nv"):
                    ev = per_pass.get(name, {}).get(i)
                    if ev is None or (want_own and not ev.get("own")):
                        continue
                    if name.endswith("_nv") and ev.get("native"):
                        continue
                    chosen = (name, ev)
                    break
                if chosen:
                    break
            rec = {**meta, "form": sel, "source": "probe", "pass": chosen[0] if chosen else None,
                   "evidence": chosen[1] if chosen else None}
            # The page accepted "x" but rejected the empty value: it only checks presence.
            junk_ok = "junk" in per_pass and not (per_pass["junk"].get(i) or {}).get("own")
            rec["presence_only"] = bool(chosen and chosen[0] == "empty" and junk_ok
                                        and meta.get("type") in ("", "text", "email", "tel", "url", "search", "password")
                                        or chosen and chosen[0] == "empty" and junk_ok and meta.get("tag") == "textarea")
            if meta.get("static_invalid") and meta.get("static_message"):
                rec.update(source="static", evidence=None)
            if rec["evidence"] is not None or rec["source"] == "static":
                any_field = True
                fields_out.append(rec)
        base = passes.get("junk") or next(iter(passes.values()), {})
        frec["navigated"] = any(p.get("navigations") for p in passes.values())
        frec["blocked"] = any(p.get("blocked") for p in passes.values())
        frec["formdata"] = any(p.get("formdata") for p in passes.values())
        frec["any_read"] = any(f.get("read") for p in passes.values() for f in (p.get("fields") or []))
        frec["form_stays"] = all(p.get("form_visible", True) for p in passes.values())
        frec["any_field"] = any_field
        frec["probe_error"] = any(p.get("error") for p in passes.values()) and not any_field
        frec["messages"] = _pass_messages(base)
        frec["observed"] = bool(any_field or frec["messages"])
        forms_out.append(frec)
    if not runs:  # static evidence only: server-rendered errors
        for f in page.fields:
            if f.get("invalid") == "true" and (f.get("errormessage") or f.get("describedby")):
                fields_out.append({
                    "selector": f["selector"], "html": f.get("html", ""), "label": " ".join(f.get("labels") or []),
                    "name": f.get("name") or f.get("name_js") or "", "type": (f.get("type") or "").lower(),
                    "hint": "", "required": f.get("required"), "pattern": None,
                    "autocomplete": f.get("autocomplete"), "form": f.get("form"), "source": "static",
                    "static_message": f.get("errormessage") or f.get("describedby"), "evidence": None,
                })
    return fields_out, forms_out


# --- helpers -----------------------------------------------------------------------------

_WORD = re.compile(r"\w+", re.UNICODE)


def words(s: str) -> list[str]:
    s = unicodedata.normalize("NFKC", s or "").casefold()
    return _WORD.findall(s)


def contains_words(hay: str, needle: str) -> bool:
    """`needle`'s words appear contiguously, as whole words, in `hay` (case/punctuation-insensitive)."""
    n, h = words(needle), words(hay)
    if not n or len(n) > len(h):
        return False
    return any(h[i:i + len(n)] == n for i in range(len(h) - len(n) + 1))


def field_label(rec: dict) -> str:
    label = norm_ws(rec.get("label") or rec.get("name") or "")
    return label.rstrip(" *:").strip()


def message_of(rec: dict) -> tuple[str, str]:
    """(message text, where) where ∈ field | form | static | native | none."""
    if rec.get("source") == "static":
        return norm_ws(rec.get("static_message") or ""), "static"
    ev = rec.get("evidence") or {}
    if ev.get("native"):
        return ev["native"], "native"
    if ev.get("visible_text"):
        return norm_ws(ev["visible_text"]), "field"
    if ev.get("form_message"):
        return norm_ws(ev["form_message"]), "form"
    return "", "none"


def is_search_form(form: dict, page: CapturedPage) -> bool:
    fs = [f for f in page.fields if f.get("form") == form["selector"]]
    return bool(fs) and all((f.get("type") or "").lower() == "search" or (f.get("field_name") or "") in ("q", "query", "search", "s")
                            for f in fs) and len(fs) <= 2


# --- strings -------------------------------------------------------------------------------

register({
    "c331.native": {
        "en": "When this field is invalid, the browser's own validation stops the form and names the problem in text.",
        "de": "Ist dieses Feld ungültig, stoppt die Validierung des Browsers das Formular und nennt das Problem als Text.",
        "fr": "Si ce champ est invalide, la validation du navigateur bloque le formulaire et décrit le problème par un texte.",
        "it": "Se questo campo non è valido, la validazione del browser blocca il modulo e descrive il problema con un testo.",
    },
    "c331.names_field": {
        "en": "After an invalid submission the message “{message}” names the field “{label}”.",
        "de": "Nach einem ungültigen Absenden nennt die Meldung «{message}» das Feld «{label}».",
        "fr": "Après un envoi invalide, le message « {message} » nomme le champ « {label} ».",
        "it": "Dopo un invio non valido il messaggio «{message}» nomina il campo «{label}».",
    },
    "c331.presentation_only": {
        "en": "After an invalid submission this field is only marked by colour, border or an icon. No text says what is wrong.",
        "de": "Nach einem ungültigen Absenden wird dieses Feld nur mit Farbe, Rahmen oder Symbol markiert. Kein Text sagt, was falsch ist.",
        "fr": "Après un envoi invalide, ce champ n'est signalé que par une couleur, une bordure ou une icône. Aucun texte ne dit ce qui ne va pas.",
        "it": "Dopo un invio non valido questo campo è segnalato solo da colore, bordo o icona. Nessun testo dice cosa non va.",
    },
    "c331.hidden_only": {
        "en": "The error text for this field exists but is not visible. Sighted users only see that something is marked.",
        "de": "Der Fehlertext zu diesem Feld existiert, ist aber nicht sichtbar. Sehende Nutzende sehen nur eine Markierung.",
        "fr": "Le texte d'erreur de ce champ existe mais n'est pas visible. Les personnes voyantes ne voient qu'un marquage.",
        "it": "Il testo di errore di questo campo esiste ma non è visibile. Chi vede nota solo una marcatura.",
    },
    "c331.apertus_field_and_problem": {
        "en": "Apertus judged that the message “{message}” names the field and says what is wrong.",
        "de": "Apertus beurteilt, dass die Meldung «{message}» das Feld nennt und sagt, was falsch ist.",
        "fr": "Apertus juge que le message « {message} » nomme le champ et dit ce qui ne va pas.",
        "it": "Apertus giudica che il messaggio «{message}» nomini il campo e dica cosa non va.",
    },
    "c331.apertus_field_only": {
        "en": "Apertus judged that the message “{message}” names the field in error.",
        "de": "Apertus beurteilt, dass die Meldung «{message}» das fehlerhafte Feld nennt.",
        "fr": "Apertus juge que le message « {message} » nomme le champ en erreur.",
        "it": "Apertus giudica che il messaggio «{message}» nomini il campo con l'errore.",
    },
    "c331.apertus_problem_assoc": {
        "en": "Apertus judged that the message “{message}” describes the problem; it is linked to the field in the code.",
        "de": "Apertus beurteilt, dass die Meldung «{message}» das Problem beschreibt; sie ist im Code mit dem Feld verknüpft.",
        "fr": "Apertus juge que le message « {message} » décrit le problème ; il est lié au champ dans le code.",
        "it": "Apertus giudica che il messaggio «{message}» descriva il problema; è collegato al campo nel codice.",
    },
    "c331.apertus_problem_near": {
        "en": "The message “{message}” describes the problem but does not name the field and is not linked to it in the code; it is only placed next to it. Experts disagree whether that identifies the field: a person must decide.",
        "de": "Die Meldung «{message}» beschreibt das Problem, nennt das Feld aber nicht und ist im Code nicht damit verknüpft; sie steht nur daneben. Fachleute sind uneins, ob das Feld so erkennbar ist: Eine Person muss entscheiden.",
        "fr": "Le message « {message} » décrit le problème mais ne nomme pas le champ et n'y est pas lié dans le code ; il est seulement placé à côté. Les experts divergent sur ce point : une personne doit trancher.",
        "it": "Il messaggio «{message}» descrive il problema ma non nomina il campo e non vi è collegato nel codice; è solo posto accanto. Gli esperti non concordano: una persona deve decidere.",
    },
    "c331.apertus_problem_form": {
        "en": "The message “{message}” describes a problem but does not say which field it is about. A person must check it.",
        "de": "Die Meldung «{message}» beschreibt ein Problem, sagt aber nicht, welches Feld betroffen ist. Eine Person muss es prüfen.",
        "fr": "Le message « {message} » décrit un problème sans dire quel champ est concerné. Une personne doit vérifier.",
        "it": "Il messaggio «{message}» descrive un problema ma non dice quale campo riguarda. Una persona deve verificare.",
    },
    "c331.apertus_generic": {
        "en": "The only message after an invalid submission is “{message}”: it names neither the field nor the problem.",
        "de": "Die einzige Meldung nach einem ungültigen Absenden ist «{message}»: Sie nennt weder das Feld noch das Problem.",
        "fr": "Le seul message après un envoi invalide est « {message} » : il ne nomme ni le champ ni le problème.",
        "it": "L'unico messaggio dopo un invio non valido è «{message}»: non nomina né il campo né il problema.",
    },
    "c331.apertus_not_an_error": {
        "en": "Apertus judged that “{message}” is not an error message (for example a confirmation).",
        "de": "Apertus beurteilt, dass «{message}» keine Fehlermeldung ist (zum Beispiel eine Bestätigung).",
        "fr": "Apertus juge que « {message} » n'est pas un message d'erreur (par exemple une confirmation).",
        "it": "Apertus giudica che «{message}» non sia un messaggio di errore (per esempio una conferma).",
    },
    "c331.apertus_unsure": {
        "en": "Apertus could not decide whether the message “{message}” identifies the error. A person must check it.",
        "de": "Apertus konnte nicht entscheiden, ob die Meldung «{message}» den Fehler erkennbar macht. Eine Person muss es prüfen.",
        "fr": "Apertus n'a pas pu décider si le message « {message} » identifie l'erreur. Une personne doit vérifier.",
        "it": "Apertus non ha potuto decidere se il messaggio «{message}» identifichi l'errore. Una persona deve verificare.",
    },
    "c331.server": {
        "en": "Submitting this form sends it to the server; Klar. stopped the request, so the error messages could not be observed. A person must submit it with an invalid value.",
        "de": "Dieses Formular wird an den Server geschickt; Klar. hat die Anfrage gestoppt, die Fehlermeldungen waren also nicht sichtbar. Eine Person muss es mit einem ungültigen Wert absenden.",
        "fr": "Ce formulaire est envoyé au serveur ; Klar. a bloqué la requête, les messages d'erreur n'ont donc pas pu être observés. Une personne doit l'envoyer avec une valeur invalide.",
        "it": "Questo modulo viene inviato al server; Klar. ha bloccato la richiesta, quindi i messaggi di errore non sono osservabili. Una persona deve inviarlo con un valore non valido.",
    },
    "c331.probe_failed": {
        "en": "Klar. could not complete the test submission of this form (the page did not respond in time). A person must check it.",
        "de": "Klar. konnte das Testabsenden dieses Formulars nicht abschliessen (die Seite reagierte nicht rechtzeitig). Eine Person muss es prüfen.",
        "fr": "Klar. n'a pas pu terminer l'envoi de test de ce formulaire (la page n'a pas répondu à temps). Une personne doit le vérifier.",
        "it": "Klar. non ha potuto completare l'invio di prova di questo modulo (la pagina non ha risposto in tempo). Una persona deve verificarlo.",
    },
    "c331.untested": {
        "en": "Klar. submits forms only on the demo site and on test pages. A person must submit this form with an invalid value and check the error messages.",
        "de": "Klar. schickt Formulare nur auf der Demo-Site und auf Testseiten ab. Eine Person muss dieses Formular mit einem ungültigen Wert absenden und die Fehlermeldungen prüfen.",
        "fr": "Klar. n'envoie des formulaires que sur le site de démonstration et les pages de test. Une personne doit envoyer ce formulaire avec une valeur invalide et vérifier les messages d'erreur.",
        "it": "Klar. invia moduli solo sul sito demo e sulle pagine di test. Una persona deve inviare questo modulo con un valore non valido e controllare i messaggi di errore.",
    },
    "c331.impact": {
        "en": "Screen-reader users and people with cognitive disabilities do not learn which field is wrong or why, and may give up.",
        "de": "Screenreader-Nutzende und Menschen mit kognitiven Einschränkungen erfahren nicht, welches Feld falsch ist und warum, und geben eventuell auf.",
        "fr": "Les utilisateurs de lecteurs d'écran et les personnes avec un handicap cognitif ne savent pas quel champ est faux ni pourquoi, et risquent d'abandonner.",
        "it": "Chi usa un lettore di schermo e le persone con disabilità cognitive non sanno quale campo è sbagliato né perché, e possono rinunciare.",
    },
    "c331.impact_ok": {
        "en": "Users learn in text which field is wrong.",
        "de": "Nutzende erfahren als Text, welches Feld falsch ist.",
        "fr": "Les utilisateurs apprennent par un texte quel champ est faux.",
        "it": "Gli utenti sanno da un testo quale campo è sbagliato.",
    },
})

CATEGORIES = ["field_and_problem", "field_only", "problem_only", "generic", "not_an_error"]


class ErrorIdentification(BaseCheck):
    criterion = "3.3.1"
    prompt_version = PROMPT_VERSION
    max_candidates = 60

    # -- 1. candidates ------------------------------------------------------------------
    def candidates(self, page: CapturedPage) -> list[Candidate]:
        fields, forms = form_evidence(page)
        out: list[Candidate] = []
        for rec in fields:
            label = field_label(rec)
            msg, where = message_of(rec)
            ev = rec.get("evidence") or {}
            assoc = bool(ev.get("associated_text") or ev.get("marked") or rec.get("source") == "static")
            if where == "native":
                kind = "native"
            elif where in ("field", "form", "static"):
                kind = "names_field" if label and contains_words(msg, label) and len(words(msg)) > len(words(label)) else "ask"
            elif ev.get("hidden_text"):
                kind = "hidden_only"
            elif ev.get("marked") or ev.get("style_changed") or ev.get("icons"):
                kind = "presentation_only"
            else:
                continue
            out.append(self.candidate(page, selector=rec["selector"], html=rec.get("html", ""),
                                      text=msg if where != "native" else "", accessible_name=label or None,
                                      context={"field_label": label}, kind=kind, where=where, associated=assoc,
                                      hidden_text=ev.get("hidden_text", ""), message=msg))
        for frec in forms:
            if frec["status"] in ("untested", "skipped"):
                if not frec.get("has_submit") or is_search_form(frec, page):
                    continue
                out.append(self.candidate(page, selector=frec["selector"], html=frec.get("html", ""),
                                          key="#untested", kind="untested"))
            elif frec.get("probe_error"):
                out.append(self.candidate(page, selector=frec["selector"], html=frec.get("html", ""),
                                          key="#probe", kind="probe_failed"))
            elif not frec.get("observed") and (frec.get("navigated") or frec.get("blocked")):
                out.append(self.candidate(page, selector=frec["selector"], html=frec.get("html", ""),
                                          key="#server", kind="server"))
            elif not frec.get("any_field") and frec.get("messages") and not frec.get("any_read") and frec.get("form_stays"):
                msg = frec["messages"][0][:400]
                out.append(self.candidate(page, selector=frec["selector"], html=frec.get("html", ""), text=msg,
                                          key="#formmsg", context={"field_label": ""}, kind="ask", where="form",
                                          associated=False, message=msg))
        return out[: self.max_candidates]

    # -- 2. deterministic decisions --------------------------------------------------------------
    def decide(self, c: Candidate) -> Finding | None:
        kind, ui = c.extra.get("kind"), self.ui_lang
        label, msg = c.accessible_name or "", c.extra.get("message", "")
        if kind == "native":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium",
                                explanation=t("c331.native", ui), user_impact=t("c331.impact_ok", ui))
        if kind == "names_field":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", excerpt=msg[:300],
                                explanation=t("c331.names_field", ui, message=msg[:160], label=label),
                                user_impact=t("c331.impact_ok", ui))
        if kind == "presentation_only":
            return self.finding(c, outcome="failed", source="heuristic", confidence="high", act_rule="36b590",
                                explanation=t("c331.presentation_only", ui), user_impact=t("c331.impact", ui))
        if kind == "hidden_only":
            return self.finding(c, outcome="failed", source="heuristic", confidence="medium", act_rule="36b590",
                                explanation=t("c331.hidden_only", ui), user_impact=t("c331.impact", ui))
        if kind == "server":
            return self.note(c, "c331.server", source="heuristic")
        if kind == "untested":
            return self.note(c, "c331.untested", source="heuristic")
        if kind == "probe_failed":
            return self.note(c, "c331.probe_failed", source="heuristic")
        return None

    # -- 3. the closed (categorical) question -------------------------------------------------
    SYSTEM = (
        "You check WCAG 2.1 success criterion 3.3.1 Error Identification for ONE form field. The form was "
        "submitted with an invalid or empty value in this field and the page showed the message below. "
        "Classify what the message tells the user:\n"
        "- field_and_problem: it names the field (by its label or a clear synonym) and says what is wrong or "
        "how to fix it\n"
        "- field_only: it names the field but only says that its value is wrong\n"
        "- problem_only: it says what is wrong or how to fix it (missing value, expected format, length, allowed "
        "values) but does not name the field\n"
        "- generic: it only says that there is an error, without the field and without the cause\n"
        "- not_an_error: the message confirms the submission or is not about an error\n"
        "quote: the part of the message that supports your answer, copied exactly."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        return self.task(
            system=self.system_prompt(self.SYSTEM, c),
            element={"field_label": c.accessible_name or "", "message": c.extra.get("message", "")[:400]},
            context={},
            question="What does the message tell the user about this field?",
            schema=category_schema(CATEGORIES),
            max_tokens=120,
        )

    # -- 4. interpretation ----------------------------------------------------------------------
    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        category = answer.get("category")
        msg = c.extra.get("message", "")[:160]
        where, assoc = c.extra.get("where"), c.extra.get("associated")
        if category in ("field_and_problem", "field_only") and not c.accessible_name:
            category = "unsure"  # "names the field" but the field has no label: contradiction
        if category in ("field_and_problem", "field_only"):
            outcome, key = "passed", f"c331.apertus_{category}"
        elif category == "problem_only" and where in ("field", "static") and assoc:
            outcome, key = "passed", "c331.apertus_problem_assoc"
        elif category == "problem_only" and where == "field":
            outcome, key = "cantTell", "c331.apertus_problem_near"
        elif category == "problem_only":
            outcome, key = "cantTell", "c331.apertus_problem_form"
        elif category == "generic":
            outcome, key = "failed", "c331.apertus_generic"
        elif category == "not_an_error":
            outcome, key = "inapplicable", "c331.apertus_not_an_error"
        else:
            outcome, key = "cantTell", "c331.apertus_unsure"
        impact = {"passed": t("c331.impact_ok", ui), "failed": t("c331.impact", ui)}.get(outcome, t("impact.review", ui))
        return self.finding(c, outcome=outcome, source="apertus",
                            confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
                            excerpt=self.model_excerpt(c, answer, outcome), explanation=t(key, ui, message=msg),
                            user_impact=impact, reason=answer.get("reason"), reason_code=key.split(".")[-1],
                            act_rule="36b590" if outcome == "failed" else ...)


CHECK = ErrorIdentification
