"""3.2.2 On Input, level A. No ACT rule.

Interaction (only where the scan allows form submission: the bundled demo site and the
evaluation's local test pages, and only for pages on the existing probe's allow-list).
For each control whose setting can be changed (select, radio group, checkbox, short or
numeric text field; max 8 per page) a throw-away tab loads the page, changes the
setting (select the next option, click the radio/checkbox, type the field's maxlength
in digits with real key events) and capture/js/c_3_2_2_probe.js records what happened.
The tab loads the page with its own GET requests (non-GET is aborted); from the first
change on, a navigation is answered with "204 No Content" by Klar., every other request
is aborted and window.open is stubbed: nothing Klar. changes is sent to a server.
A tab is reused for the next control while the previous change had no effect.
On every other site nothing is changed: controls that carry change/input listeners
(Chromium DevTools protocol, read-only) or inline on-change handlers get one cantTell
note each asking a person to test them.

Decided in code (glossary "change of context")
  * a change of context was observed: navigation, new window, form submission, or focus
    moved to another element; and there is no text at all before or after the
    control                                                              → failed (F36/F37)
  * no change of context, the content barely changes (filtering, extra
    fields below)                                                         → passed (change of content)
  * no change of context, but a heading changes or more than half of the
    main text is new (the view is replaced)                               → cantTell (judgement)
Asked to Apertus (one categorical question per control that changed the context)
  "Changing this control <observed effect>. Is the user told so in advance?"
    warning_before | warning_after | no_warning
  The texts are split by code: before = everything that precedes the control in its form or
  section, plus its aria-describedby description (read by screen readers on focus); after =
  what follows it. Mapped in code (data/testset/PROTOCOL.md §3.2.2): warning_before → passed
  (G13), warning_after → cantTell (visually close, but read after the control), no_warning → failed.

Known limits: only the first different option / one click / one typed value is tried;
effects after more than ~0.5 s, effects on blur, and changes inside iframes are not seen;
custom (ARIA) listboxes and comboboxes are not changed.
"""

from __future__ import annotations

import logging
import re
import secrets
from functools import lru_cache
from pathlib import Path

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema, norm_ws
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

log = logging.getLogger(__name__)

PROMPT_VERSION = "3.2.2/v1"
MAX_CONTROLS = 8
SETTLE_MS = 450
MAJOR_NEW_TEXT = 0.5
JS_PATH = Path(__file__).resolve().parents[1] / "capture" / "js" / "c_3_2_2_probe.js"
_GLOBAL = "__koi_" + secrets.token_hex(5)
_PAGE_CACHE = "_klar_c322_runs"
_INLINE_HANDLER = re.compile(r"\son(change|input|keyup|keydown|click)\s*=", re.IGNORECASE)

CATEGORIES = ["warning_before", "warning_after", "no_warning"]
CATEGORY_OUTCOME = {"warning_before": "passed", "warning_after": "cantTell", "no_warning": "failed"}

EFFECT_EN = {
    "navigate": "opens another page",
    "new_window": "opens a new window",
    "submit": "submits the form",
    "focus": "moves the keyboard focus to another element",
}


@lru_cache(maxsize=1)
def probe_js() -> str:
    return JS_PATH.read_text(encoding="utf-8").replace("__KOI__", _GLOBAL)


def event_listeners(page: CapturedPage, selectors: list[str]) -> dict[str, set[str]]:
    """selector → event types registered on that very element (DevTools protocol,
    read-only; no event is dispatched). Empty when the page is not live."""
    out: dict[str, set[str]] = {}
    if page.live is None or not selectors:
        return out
    try:
        cdp = page.live.context.new_cdp_session(page.live)
    except Exception as exc:
        log.info("CDP session unavailable: %s", exc)
        return out
    try:
        for sel in selectors[:80]:
            try:
                res = cdp.send("Runtime.evaluate", {"expression": f"document.querySelector({_js_str(sel)})",
                                                    "objectGroup": "klar322"})
                oid = (res.get("result") or {}).get("objectId")
                if not oid:
                    continue
                ls = cdp.send("DOMDebugger.getEventListeners", {"objectId": oid})
                out[sel] = {x.get("type", "") for x in ls.get("listeners", [])}
            except Exception:
                continue
        try:
            cdp.send("Runtime.releaseObjectGroup", {"objectGroup": "klar322"})
        except Exception:
            pass
    finally:
        try:
            cdp.detach()
        except Exception:
            pass
    return out


def _js_str(s: str) -> str:
    import json

    return json.dumps(s)


def control_runs(page: CapturedPage) -> list[dict] | None:
    """One record per tested control, or None when interaction is not allowed."""
    if _PAGE_CACHE in page.__dict__:
        return page.__dict__[_PAGE_CACHE]
    runs: list[dict] | None = None
    if page.allow_form_submit and page.live is not None:
        try:
            skipped = [r for r in page.form_probe() if r.get("skipped")]
        except Exception:
            skipped = []
        if not skipped:
            try:
                runs = _run_controls(page)
            except Exception as exc:
                log.info("on-input probe failed: %s", exc)
                runs = []
    page.__dict__[_PAGE_CACHE] = runs
    return runs


def _open_tab(page: CapturedPage, st: dict):
    from klar.capture.browser import CaptureOptions, js, load

    tab = page.live.context.new_page()

    def handler(route, request):
        try:
            if st["armed"] and request.is_navigation_request() and request.frame == tab.main_frame:
                st["navigations"].append(request.url[:160])
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

    tab.route("**/*", handler)
    tab.on("dialog", lambda d: _dismiss(d))
    tab.on("popup", lambda p: st.__setitem__("popups", st.get("popups", 0) + 1))
    tab.add_init_script("window.open = function () { window.__koiOpened = (window.__koiOpened || 0) + 1; return null; };")
    load(tab, url=None if page.source_html is not None else page.url, html=page.source_html,
         opts=CaptureOptions(scroll=False, idle_timeout_ms=1500, timeout_ms=15000))
    tab.evaluate(js(probe_js()))
    return tab


def _dismiss(d) -> None:
    try:
        d.dismiss()
    except Exception:
        pass


def _run_controls(page: CapturedPage) -> list[dict]:
    st = {"armed": False, "navigations": [], "blocked": []}
    tab = _open_tab(page, st)
    try:
        controls = tab.evaluate(f"n => window.{_GLOBAL}.list(n)", MAX_CONTROLS)
    except Exception:
        tab.close()
        raise
    out = []
    fresh = True  # the open tab is unchanged and may serve the next control
    for ctl in controls:
        if not fresh:
            try:
                tab.close()
            except Exception:
                pass
            st = {"armed": False, "navigations": [], "blocked": []}
            try:
                tab = _open_tab(page, st)
                tab.evaluate(f"n => window.{_GLOBAL}.list(n)", MAX_CONTROLS)
            except Exception as exc:
                out.append({**ctl, "error": str(exc)[:160]})
                fresh = False
                continue
        rec = dict(ctl)
        n_nav, n_blk = len(st["navigations"]), len(st["blocked"])
        try:
            st["armed"] = True
            res = tab.evaluate(f"i => window.{_GLOBAL}.change(i)", ctl["i"])
            if res.get("type"):
                tab.locator(ctl["selector"]).first.press_sequentially("1" * int(res["type"]), delay=15, timeout=3000)
            elif res.get("error"):
                rec["error"] = res["error"]
            tab.wait_for_timeout(SETTLE_MS)
            rec.update(tab.evaluate(f"i => window.{_GLOBAL}.observe(i)", ctl["i"]))
        except Exception as exc:
            rec["error"] = str(exc)[:160]
        rec["navigations"], rec["blocked"] = st["navigations"][n_nav:], st["blocked"][n_blk:]
        rec["popups"] = st.get("popups", 0)
        fresh = not (rec.get("error") or effect_of(rec) or rec.get("headings_changed")
                     or (rec.get("new_text_ratio") or 0) > 0 or rec.get("popups"))
        out.append(rec)
    try:
        tab.close()
    except Exception:
        pass
    return out


def effect_of(rec: dict) -> str | None:
    if rec.get("navigations") and not rec.get("submits"):
        return "navigate"
    if rec.get("submits") or rec.get("blocked"):
        return "submit"
    if rec.get("opened") or rec.get("popups"):
        return "new_window"
    if rec.get("focus_moved"):
        return "focus"
    return None


register({
    "c322.no_change": {
        "en": "Changing this control does not change the context: no new page, window or focus move. The page waits for a button.",
        "de": "Eine Änderung an diesem Element wechselt den Kontext nicht: keine neue Seite, kein neues Fenster, kein Fokussprung.",
        "fr": "Modifier ce contrôle ne change pas de contexte : ni nouvelle page, ni nouvelle fenêtre, ni déplacement du focus.",
        "it": "Modificare questo controllo non cambia il contesto: nessuna nuova pagina, finestra o spostamento del focus.",
    },
    "c322.content_only": {
        "en": "Changing this control only updates content on the same page (a filter or extra fields); focus and page stay put.",
        "de": "Eine Änderung an diesem Element aktualisiert nur Inhalte auf derselben Seite (Filter oder zusätzliche Felder); Fokus und Seite bleiben.",
        "fr": "Modifier ce contrôle ne fait que mettre à jour le contenu de la même page (filtre ou champs supplémentaires) ; le focus et la page restent.",
        "it": "Modificare questo controllo aggiorna solo il contenuto della stessa pagina (filtro o campi aggiuntivi); focus e pagina restano.",
    },
    "c322.major": {
        "en": "Changing this control replaces a large part of the page (a heading changes) without moving the focus. Whether that is a change of context is a judgement: a person must decide.",
        "de": "Eine Änderung an diesem Element ersetzt einen grossen Teil der Seite (eine Überschrift ändert sich), ohne den Fokus zu verschieben. Ob das ein Kontextwechsel ist, muss eine Person entscheiden.",
        "fr": "Modifier ce contrôle remplace une grande partie de la page (un titre change) sans déplacer le focus. Savoir si c'est un changement de contexte relève du jugement : une personne doit trancher.",
        "it": "Modificare questo controllo sostituisce gran parte della pagina (cambia un titolo) senza spostare il focus. Se sia un cambio di contesto va giudicato: una persona deve decidere.",
    },
    "c322.no_text": {
        "en": "Changing this control {effect_text}, and no text near it says so.",
        "de": "Eine Änderung an diesem Element {effect_text}, und kein Text in der Nähe kündigt das an.",
        "fr": "Modifier ce contrôle {effect_text}, et aucun texte à proximité ne l'annonce.",
        "it": "Modificare questo controllo {effect_text}, e nessun testo vicino lo annuncia.",
    },
    "c322.effect.navigate": {"en": "opens another page", "de": "öffnet eine andere Seite", "fr": "ouvre une autre page", "it": "apre un'altra pagina"},
    "c322.effect.new_window": {"en": "opens a new window", "de": "öffnet ein neues Fenster", "fr": "ouvre une nouvelle fenêtre", "it": "apre una nuova finestra"},
    "c322.effect.submit": {"en": "submits the form", "de": "schickt das Formular ab", "fr": "envoie le formulaire", "it": "invia il modulo"},
    "c322.effect.focus": {"en": "moves the focus to another element", "de": "verschiebt den Fokus auf ein anderes Element", "fr": "déplace le focus vers un autre élément", "it": "sposta il focus su un altro elemento"},
    "c322.apertus_warning_before": {
        "en": "Changing this control {effect_text}, and Apertus judged that a text before it announces this.",
        "de": "Eine Änderung an diesem Element {effect_text}; Apertus beurteilt, dass ein Text davor das ankündigt.",
        "fr": "Modifier ce contrôle {effect_text} ; Apertus juge qu'un texte placé avant l'annonce.",
        "it": "Modificare questo controllo {effect_text}; Apertus giudica che un testo posto prima lo annunci.",
    },
    "c322.apertus_warning_after": {
        "en": "Changing this control {effect_text}. Only a text after it announces this, which screen-reader users reach too late. Experts disagree: a person must decide.",
        "de": "Eine Änderung an diesem Element {effect_text}. Nur ein Text danach kündigt das an, den Screenreader-Nutzende zu spät erreichen. Fachleute sind uneins: Eine Person muss entscheiden.",
        "fr": "Modifier ce contrôle {effect_text}. Seul un texte placé après l'annonce, que les utilisateurs de lecteurs d'écran atteignent trop tard. Les experts divergent : une personne doit trancher.",
        "it": "Modificare questo controllo {effect_text}. Solo un testo posto dopo lo annuncia, che chi usa un lettore di schermo raggiunge troppo tardi. Gli esperti non concordano: una persona deve decidere.",
    },
    "c322.apertus_no_warning": {
        "en": "Changing this control {effect_text}, and Apertus found no text that announces this.",
        "de": "Eine Änderung an diesem Element {effect_text}, und Apertus fand keinen Text, der das ankündigt.",
        "fr": "Modifier ce contrôle {effect_text}, et Apertus n'a trouvé aucun texte qui l'annonce.",
        "it": "Modificare questo controllo {effect_text}, e Apertus non ha trovato alcun testo che lo annunci.",
    },
    "c322.apertus_unsure": {
        "en": "Changing this control {effect_text}. Apertus could not decide whether the user is told in advance: a person must check it.",
        "de": "Eine Änderung an diesem Element {effect_text}. Apertus konnte nicht entscheiden, ob das vorher angekündigt wird: Eine Person muss es prüfen.",
        "fr": "Modifier ce contrôle {effect_text}. Apertus n'a pas pu décider si c'est annoncé avant : une personne doit vérifier.",
        "it": "Modificare questo controllo {effect_text}. Apertus non ha potuto decidere se sia annunciato prima: una persona deve verificare.",
    },
    "c322.untested": {
        "en": "This control reacts to changes with a script. Klar. changes controls only on the demo site and on test pages: a person must check that changing it does not open a page, a window or move the focus unannounced.",
        "de": "Dieses Element reagiert per Skript auf Änderungen. Klar. ändert Elemente nur auf der Demo-Site und auf Testseiten: Eine Person muss prüfen, dass eine Änderung nicht unangekündigt eine Seite, ein Fenster öffnet oder den Fokus verschiebt.",
        "fr": "Ce contrôle réagit aux changements par un script. Klar. ne modifie des contrôles que sur le site de démonstration et les pages de test : une personne doit vérifier qu'un changement n'ouvre pas une page ou une fenêtre et ne déplace pas le focus sans annonce.",
        "it": "Questo controllo reagisce alle modifiche con uno script. Klar. modifica i controlli solo sul sito demo e sulle pagine di test: una persona deve verificare che una modifica non apra pagine o finestre né sposti il focus senza preavviso.",
    },
    "c322.impact": {
        "en": "Keyboard and screen-reader users are moved somewhere else while they are still choosing, and may lose their place or their input.",
        "de": "Tastatur- und Screenreader-Nutzende werden mitten in der Auswahl an einen anderen Ort versetzt und verlieren eventuell ihre Position oder Eingaben.",
        "fr": "Les personnes au clavier ou avec un lecteur d'écran sont déplacées ailleurs pendant leur choix et risquent de perdre leur position ou leur saisie.",
        "it": "Chi usa tastiera o lettore di schermo viene spostato altrove mentre sta ancora scegliendo e può perdere la posizione o i dati inseriti.",
    },
    "c322.impact_ok": {
        "en": "Users stay where they are while they change the setting.",
        "de": "Nutzende bleiben, wo sie sind, während sie die Einstellung ändern.",
        "fr": "Les utilisateurs restent où ils sont pendant qu'ils changent le réglage.",
        "it": "Gli utenti restano dove sono mentre cambiano l'impostazione.",
    },
})


class OnInput(BaseCheck):
    criterion = "3.2.2"
    prompt_version = PROMPT_VERSION
    max_candidates = 20

    def candidates(self, page: CapturedPage) -> list[Candidate]:
        runs = control_runs(page)
        out: list[Candidate] = []
        if runs is None:
            return self._static(page)
        for rec in runs:
            if rec.get("error") and "focus_moved" not in rec:
                continue
            effect = effect_of(rec)
            if effect:
                kind = "ask" if (rec.get("before") or rec.get("after") or rec.get("described")) else "no_text"
            elif rec.get("headings_changed") or (rec.get("new_text_ratio") or 0) > MAJOR_NEW_TEXT:
                kind = "major"
            elif (rec.get("new_text_ratio") or 0) > 0:
                kind = "content_only"
            else:
                kind = "no_change"
            before = norm_ws(" ".join(x for x in (rec.get("before", ""), rec.get("described", "")) if x))
            after = norm_ws(rec.get("after", ""))
            text = " … ".join(x for x in (before, after) if x)
            out.append(self.candidate(page, selector=rec["selector"], html=rec.get("html", ""), text=text,
                                      accessible_name=rec.get("label") or None, kind=kind, effect=effect,
                                      before=before[-400:], after=after[:300], control=rec.get("kind")))
        return out[: self.max_candidates]

    def _static(self, page: CapturedPage) -> list[Candidate]:
        fields = [f for f in page.fields if f.get("tag") == "select" or (f.get("type") or "").lower() in
                  ("radio", "checkbox", "text", "tel", "number")][:40]
        listeners = event_listeners(page, [f["selector"] for f in fields])
        out = []
        for f in fields:
            types = listeners.get(f["selector"], set())
            if {"change", "input", "keyup", "keydown"} & types or _INLINE_HANDLER.search(f.get("html", "")):
                out.append(self.candidate(page, selector=f["selector"], html=f.get("html", ""), kind="untested"))
        return out[:10]

    def decide(self, c: Candidate) -> Finding | None:
        kind, ui = c.extra.get("kind"), self.ui_lang
        excerpt = c.html[:300]
        if kind == "no_change":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", excerpt=excerpt,
                                explanation=t("c322.no_change", ui), user_impact=t("c322.impact_ok", ui))
        if kind == "content_only":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", excerpt=excerpt,
                                explanation=t("c322.content_only", ui), user_impact=t("c322.impact_ok", ui))
        if kind == "major":
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="low", excerpt=excerpt,
                                explanation=t("c322.major", ui), user_impact=t("impact.review", ui))
        if kind == "no_text":
            effect = t(f"c322.effect.{c.extra.get('effect')}", ui)
            return self.finding(c, outcome="failed", source="heuristic", confidence="high", excerpt=excerpt,
                                explanation=t("c322.no_text", ui, effect_text=effect), user_impact=t("c322.impact", ui))
        if kind == "untested":
            return self.note(c, "c322.untested", source="heuristic")
        return None

    SYSTEM = (
        "You check WCAG 2.1 success criterion 3.2.2 On Input for ONE form control. Changing its value causes a "
        "change of context (the effect is given in the question). That is allowed only if the user is told "
        "about it before using the control. `text_before` is the text that precedes the control, including its "
        "label and its programmatic description; `text_after` is the text that follows it. Classify:\n"
        "- warning_before: a text in text_before says that changing the control will cause this effect\n"
        "- warning_after: only a text in text_after says so\n"
        "- no_warning: no text says so (a label alone is not a warning)\n"
        "quote: the warning, copied exactly; for no_warning, the control's label."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        effect = EFFECT_EN.get(c.extra.get("effect") or "", "changes the context")
        element = {"label": c.accessible_name or "", "text_before": c.extra.get("before", ""),
                   "text_after": c.extra.get("after", "")}
        return self.task(system=self.system_prompt(self.SYSTEM, c), element=element, context={},
                         question=f"Changing this control {effect}. Is the user told so in advance?",
                         schema=category_schema(CATEGORIES), max_tokens=120)

    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        category = answer.get("category")
        outcome = CATEGORY_OUTCOME.get(category, "cantTell")
        if (category == "warning_before" and not c.extra.get("before")) or (
                category == "warning_after" and not c.extra.get("after")):
            outcome, category = "cantTell", "unsure"  # warning in an empty text: contradiction
        key = f"c322.apertus_{category}" if category in CATEGORY_OUTCOME else "c322.apertus_unsure"
        effect = t(f"c322.effect.{c.extra.get('effect')}", ui)
        impact = {"passed": t("c322.impact_ok", ui), "failed": t("c322.impact", ui)}.get(outcome, t("impact.review", ui))
        quote = (answer.get("quote") or "").strip()
        excerpt = quote if quote else (c.html[:300] if outcome != "failed" else "")
        if outcome == "failed" and not quote:
            excerpt = c.accessible_name or ""
        return self.finding(c, outcome=outcome, source="apertus",
                            confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
                            excerpt=excerpt, explanation=t(key, ui, effect_text=effect), user_impact=impact,
                            reason=answer.get("reason"), reason_code=key.split(".")[-1])


CHECK = OnInput
