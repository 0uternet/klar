"""4.1.2 Name, Role, Value, level A. ACT rules e086e5 (form field has a name), 97a4e1,
4e8ab6 (required states), 6cfa84, cae760. Failures F59, F15, F68, F89.

axe-core already reports the presence/syntax failures of this criterion on every page
(button-name, link-name, label, frame-title, aria-required-attr, aria-hidden-focus, …;
see capture/axe.py). This module adds what axe cannot see; capture/js/c_4_1_2_widgets.js
collects the facts, the DevTools protocol (read-only) lists event listeners.

Decided in code
  * a div/span/li… without a widget role, with a CLICK listener or onclick (or a key listener
    and tabindex), that looks like a control (1 to 40 characters of text, at most 6 words, on a box at
    most 160 px high) and holds no native link, button or field          → failed (F59/F15)
    - the same inside an aria-hidden subtree and not focusable (a mouse-only duplicate) → passed
    - pointer/touch/key listeners on a container (map, slider) that is not control-like → ignored
    - a listener on an element inside a web component (custom element or shadow DOM) with no
      pointer cursor, no keyboard focus and no onclick → ignored (component frameworks attach
      handlers to inert parts; nothing presents it as a control)
    - every other clickable (a card around a link, a large area, a control-like element with
      only pointer listeners) → Apertus, see below (max 5 per page, then cantTell)
  * role=checkbox/switch/radio/menuitemcheckbox without aria-checked  → failed (ACT 4e8ab6)
  * role=tab in a tablist where no tab has aria-selected              → failed (state only in CSS)
  * other custom widgets with a role                                   → passed (ARIA4)
  * a link with aria-haspopup/aria-expanded that also navigates       → cantTell (which role is right?)
  * native details/summary                                             → passed (H91)
  * icon-only control whose name is a file or icon identifier          → failed (F89-like)
  * icon-only control with a name of two or more words                 → passed (ARIA14)
Interaction (only where the scan allows it, in a throw-away tab where navigations and
non-GET requests are stopped): each toggle-like control (button type=button, role=button,
switch, checkbox, tab, link to "#", element with aria-expanded; max 8) is clicked once.
  * its aria-expanded/-checked/-pressed/-selected changes              → passed (state kept in sync)
  * content shows/hides but the state attribute stays the same         → failed (stale state, F15)
  * content shows/hides and there is no state attribute:
      the control is a link to "#"                                     → cantTell (link or button?)
      only its own name changes ("show"/"hide")                        → cantTell (state in the name)
      otherwise                                                        → failed (state not exposed)
  * only the URL fragment changes                                      → cantTell (in-page link behaviour)
Asked to Apertus (one categorical question per element)
  * icon-only control with a one-word name: "Does this name tell what the control does?"
    describes | meaningless | unsure → passed | failed | cantTell
  * ambiguous clickable (the events and "contains a native link/button/field: yes|no" are code
    facts given in the question): "Is this element itself used as a button or link?"
    own_control | duplicate | widget_area | unsure → failed | passed | inapplicable | cantTell;
    an answer that contradicts the DOM fact (duplicate without a control inside, own_control
    with one) → cantTell.

Known limits: listeners delegated to an ancestor or the document are not seen; keyboard
support (2.1.1) is not judged; only one click per control; state changes after ~0.5 s are missed;
content fetched from the network after the click is never loaded (the tab sends nothing after it).
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

PROMPT_VERSION = "4.1.2/v2"
JS_PATH = Path(__file__).resolve().parents[1] / "capture" / "js" / "c_4_1_2_widgets.js"
_GLOBAL = "__kw_" + secrets.token_hex(5)
MAX_TOGGLES = 8
SETTLE_MS = 350
KEY_EVENTS = {"keydown", "keyup", "keypress"}
POINTER_EVENTS = {"mousedown", "mouseup", "pointerdown", "pointerup", "touchstart", "touchend"}
LISTEN_EVENTS = {"click"} | KEY_EVENTS | POINTER_EVENTS
MAX_CLICK_QUESTIONS = 5
# "Looks like a control": short visible text on a control-sized box (not a map, slider or card).
CONTROL_MAX_CHARS, CONTROL_MAX_WORDS, CONTROL_MAX_H = 40, 6, 160  # a block div may span the row: no width limit
CHECKED_ROLES = {"checkbox", "switch", "radio", "menuitemcheckbox", "menuitemradio"}
STATE_ATTRS = ("aria-expanded", "aria-checked", "aria-pressed", "aria-selected")
_TECHNICAL = re.compile(r"\.(?:svg|png|jpe?g|gif|webp|ico)$|^[a-z0-9]+(?:[-_][a-z0-9]+)+$|^(?:icon|btn|img|svg)\d*$",
                        re.IGNORECASE)
CATEGORIES = ["describes", "meaningless", "unsure"]
CLICK_CATEGORIES = ["own_control", "duplicate", "widget_area", "unsure"]
CLICK_OUTCOME = {"own_control": "failed", "duplicate": "passed", "widget_area": "inapplicable"}


def clickable_kind(rec: dict) -> str | None:
    """F59 in code only for a click (or key + tabindex) listener on a control-like element with no
    native control inside; ambiguous containers go to Apertus; gesture-only areas are ignored."""
    types = set(rec.get("types") or [])
    if rec.get("aria_hidden") and not rec.get("focusable"):
        return "hidden_duplicate"
    if rec.get("in_component") and not (rec.get("pointer") or rec.get("focusable") or rec.get("onclick")):
        # Inside a web component, with no pointer cursor, no keyboard focus and no inline handler:
        # component frameworks attach click handlers to inert parts (a non-interactive tag in a card).
        return None
    strong = bool(rec.get("onclick") or "click" in types or (types & KEY_EVENTS and rec.get("focusable")))
    control_like = (0 < (rec.get("chars") or 0) <= CONTROL_MAX_CHARS and (rec.get("words") or 0) <= CONTROL_MAX_WORDS
                    and (rec.get("height") or 0) <= CONTROL_MAX_H)
    if strong and control_like and not rec.get("has_interactive"):
        return "clickable"
    if strong or (types & POINTER_EVENTS and control_like and not rec.get("has_interactive")):
        return "ask_clickable"
    return None  # pointer/touch/key listeners on a container (map, slider): not a button or link


@lru_cache(maxsize=1)
def widgets_js() -> str:
    return JS_PATH.read_text(encoding="utf-8").replace("__KW__", _GLOBAL)


def click_listener_map(page: CapturedPage, limit: int = 150) -> dict[str, list[str]]:
    """selector → event types (click/pointer/touch/key) registered on that very element, read
    with the DevTools protocol in ONE subtree query (read-only; no event is dispatched).
    Delegated listeners on the document or an ancestor are not attributed to inner elements."""
    from klar.capture.browser import js

    out: dict[str, list[str]] = {}
    try:
        cdp = page.live.context.new_cdp_session(page.live)
    except Exception as exc:
        log.info("CDP session unavailable: %s", exc)
        return out
    try:
        cdp.send("DOM.getDocument", {"depth": 0})
        doc = cdp.send("Runtime.evaluate", {"expression": "document.body", "objectGroup": "k412"})
        oid = (doc.get("result") or {}).get("objectId")
        if not oid:
            return out
        ls = cdp.send("DOMDebugger.getEventListeners", {"objectId": oid, "depth": -1, "pierce": False})
        ids: dict[int, set[str]] = {}
        for x in ls.get("listeners", []):
            if x.get("type") in LISTEN_EVENTS and x.get("backendNodeId"):
                ids.setdefault(x["backendNodeId"], set()).add(x["type"])
        fn = js("function () { try { return window.__klar.cssPath(this); } catch (e) { return null; } }")
        for bid in list(ids)[:limit]:
            try:
                obj = cdp.send("DOM.resolveNode", {"backendNodeId": bid, "objectGroup": "k412"})
                res = cdp.send("Runtime.callFunctionOn", {"objectId": obj["object"]["objectId"], "functionDeclaration": fn,
                                                          "returnByValue": True})
                sel = (res.get("result") or {}).get("value")
                if sel:
                    out[sel] = sorted(set(out.get(sel, [])) | ids[bid])
            except Exception:
                continue
        cdp.send("Runtime.releaseObjectGroup", {"objectGroup": "k412"})
    except Exception as exc:
        log.info("listener query failed: %s", exc)
    finally:
        try:
            cdp.detach()
        except Exception:
            pass
    return out


def collect(page: CapturedPage) -> dict:
    if page.live is None:
        return {}
    try:
        listeners = click_listener_map(page)
        page.evaluate(widgets_js())
        return page.evaluate(f"m => window.{_GLOBAL}.collect(m)", listeners) or {}
    except Exception as exc:
        log.info("widget collection failed: %s", exc)
        return {}


def toggle_runs(page: CapturedPage, toggles: list[dict]) -> list[dict]:
    """Click each toggle once in its own throw-away tab (navigation → 204, non-GET aborted)."""
    from klar.capture.browser import CaptureOptions, js, load

    out = []
    for tg in toggles[:MAX_TOGGLES]:
        st = {"armed": False, "navigations": 0}
        tab = page.live.context.new_page()

        def handler(route, request, st=st, tab=tab):
            try:
                if st["armed"] and request.is_navigation_request() and request.frame == tab.main_frame:
                    st["navigations"] += 1
                    route.fulfill(status=204, body="")
                    return
            except Exception:
                pass
            if st["armed"]:  # after the click: nothing at all leaves the tab
                route.abort("blockedbyclient")
                return
            if request.method not in ("GET", "HEAD"):
                route.abort("blockedbyclient")
                return
            route.fallback()

        rec = dict(tg)
        try:
            tab.route("**/*", handler)
            tab.on("dialog", lambda d: d.dismiss())
            tab.add_init_script("window.open = function () { return null; };")
            load(tab, url=None if page.source_html is not None else page.url, html=page.source_html,
                 opts=CaptureOptions(scroll=False, idle_timeout_ms=1500, timeout_ms=15000))
            tab.evaluate(js(widgets_js()))
            tab.evaluate(f"() => window.{_GLOBAL}.collect({{}})")
            st["armed"] = True
            tab.evaluate(f"i => window.{_GLOBAL}.click(i)", tg["i"])
            tab.wait_for_timeout(SETTLE_MS)
            rec.update(tab.evaluate(f"i => window.{_GLOBAL}.observe(i)", tg["i"]))
        except Exception as exc:
            rec["error"] = str(exc)[:160]
        finally:
            try:
                tab.close()
            except Exception:
                pass
        rec["navigated"] = st["navigations"] > 0
        out.append(rec)
    return out


def toggle_kind(rec: dict) -> str | None:
    if rec.get("error") or rec.get("navigated"):
        return None
    before, after = rec.get("states_before") or {}, rec.get("states_after") or {}
    present = [a for a in STATE_ATTRS if before.get(a) is not None or after.get(a) is not None]
    toggled = [a for a in present if before.get(a) != after.get(a)]
    changed = bool(rec.get("dialog") or (rec.get("words_changed") or 0) >= 3)
    if toggled:
        return "state_synced"
    if present and (changed or rec.get("role") in CHECKED_ROLES):
        return "state_stale"
    if changed:
        if rec.get("tag") == "a":
            return "link_toggle"
        if norm_ws(rec.get("name_before")) != norm_ws(rec.get("name_after")):
            return "name_toggle"
        return "state_missing"
    if rec.get("hash_changed"):
        return "fragment_only"
    return None


register({
    "c412.clickable": {
        "en": "This {tag} reacts to clicks but has no role: screen readers do not announce it as a button or link, and it may not be reachable by keyboard.",
        "de": "Dieses {tag}-Element reagiert auf Klicks, hat aber keine Rolle: Screenreader kündigen es nicht als Schaltfläche oder Link an, und es ist eventuell nicht per Tastatur erreichbar.",
        "fr": "Cet élément {tag} réagit aux clics mais n'a pas de rôle : les lecteurs d'écran ne l'annoncent ni comme bouton ni comme lien, et il est peut-être inaccessible au clavier.",
        "it": "Questo elemento {tag} reagisce ai clic ma non ha un ruolo: i lettori di schermo non lo annunciano come pulsante o link, e forse non è raggiungibile da tastiera.",
    },
    "c412.apertus_own_control": {
        "en": "Apertus judged that this {tag} is itself used as a button or link, but it has no role: screen readers do not announce it as one.",
        "de": "Apertus beurteilt, dass dieses {tag}-Element selbst als Schaltfläche oder Link dient, aber keine Rolle hat: Screenreader kündigen es nicht so an.",
        "fr": "Apertus juge que cet élément {tag} sert lui-même de bouton ou de lien, mais il n'a pas de rôle : les lecteurs d'écran ne l'annoncent pas ainsi.",
        "it": "Apertus giudica che questo elemento {tag} funga da pulsante o link, ma non ha un ruolo: i lettori di schermo non lo annunciano come tale.",
    },
    "c412.apertus_duplicate": {
        "en": "Apertus judged that this click area repeats a link or button inside it, which assistive technology can use.",
        "de": "Apertus beurteilt, dass diese Klickfläche einen Link oder eine Schaltfläche darin wiederholt, die Hilfsmittel nutzen können.",
        "fr": "Apertus juge que cette zone cliquable répète un lien ou un bouton qu'elle contient, utilisable par les technologies d'assistance.",
        "it": "Apertus giudica che quest'area cliccabile ripeta un link o un pulsante al suo interno, usabile dalle tecnologie assistive.",
    },
    "c412.apertus_widget_area": {
        "en": "Apertus judged that this is a gesture area or complex widget (map, slider), not a button or link; its own controls are checked separately.",
        "de": "Apertus beurteilt, dass dies eine Gestenfläche oder ein komplexes Widget ist (Karte, Slider), keine Schaltfläche und kein Link; seine Bedienelemente werden einzeln geprüft.",
        "fr": "Apertus juge qu'il s'agit d'une zone de gestes ou d'un widget complexe (carte, carrousel), pas d'un bouton ni d'un lien ; ses contrôles sont vérifiés à part.",
        "it": "Apertus giudica che sia un'area per gesti o un widget complesso (mappa, slider), non un pulsante o un link; i suoi controlli sono verificati a parte.",
    },
    "c412.click_unsure": {
        "en": "This {tag} reacts to the mouse, touch or keys but has no role. Whether it is used as a button or link is unclear: a person must check it.",
        "de": "Dieses {tag}-Element reagiert auf Maus, Touch oder Tasten, hat aber keine Rolle. Ob es als Schaltfläche oder Link dient, ist unklar: Eine Person muss es prüfen.",
        "fr": "Cet élément {tag} réagit à la souris, au toucher ou au clavier mais n'a pas de rôle. On ne sait pas s'il sert de bouton ou de lien : une personne doit vérifier.",
        "it": "Questo elemento {tag} reagisce a mouse, tocco o tasti ma non ha un ruolo. Se funga da pulsante o link non è chiaro: una persona deve verificare.",
    },
    "c412.hidden_duplicate": {
        "en": "A mouse-only click area hidden from assistive technology and not focusable; it duplicates another control.",
        "de": "Eine nur per Maus nutzbare Klickfläche, für Hilfsmittel verborgen und nicht fokussierbar; sie doppelt ein anderes Bedienelement.",
        "fr": "Une zone cliquable pour la souris, masquée aux technologies d'assistance et non focalisable ; elle double un autre contrôle.",
        "it": "Un'area cliccabile solo col mouse, nascosta alle tecnologie assistive e non focalizzabile; duplica un altro controllo.",
    },
    "c412.no_checked": {
        "en": "This custom {role} has no aria-checked: screen readers cannot say whether it is on or off.",
        "de": "Dieses selbst gebaute {role}-Element hat kein aria-checked: Screenreader können nicht sagen, ob es an oder aus ist.",
        "fr": "Ce {role} personnalisé n'a pas d'aria-checked : les lecteurs d'écran ne peuvent pas dire s'il est activé.",
        "it": "Questo {role} personalizzato non ha aria-checked: i lettori di schermo non possono dire se è attivo.",
    },
    "c412.tab_unselected": {
        "en": "None of these tabs has aria-selected: the selected tab is shown only by its look.",
        "de": "Keiner dieser Tabs hat aria-selected: Der gewählte Tab ist nur optisch erkennbar.",
        "fr": "Aucun de ces onglets n'a aria-selected : l'onglet choisi n'est signalé que visuellement.",
        "it": "Nessuna di queste schede ha aria-selected: la scheda scelta si vede solo graficamente.",
    },
    "c412.widget_ok": {
        "en": "A custom {role} with an exposed role and name “{name}”.",
        "de": "Ein selbst gebautes {role}-Element mit vermittelter Rolle und dem Namen «{name}».",
        "fr": "Un {role} personnalisé avec rôle et nom « {name} » exposés.",
        "it": "Un {role} personalizzato con ruolo e nome «{name}» esposti.",
    },
    "c412.dual_link": {
        "en": "This link navigates and also opens a sub-menu (aria-haspopup / aria-expanded). Whether link or menu button is the right role is disputed: a person must decide.",
        "de": "Dieser Link navigiert und öffnet zugleich ein Untermenü (aria-haspopup / aria-expanded). Ob Link oder Menüschaltfläche die richtige Rolle ist, ist umstritten: Eine Person muss entscheiden.",
        "fr": "Ce lien mène à une page et ouvre aussi un sous-menu (aria-haspopup / aria-expanded). Le bon rôle (lien ou bouton de menu) est discuté : une personne doit trancher.",
        "it": "Questo link naviga e apre anche un sottomenu (aria-haspopup / aria-expanded). Se il ruolo giusto sia link o pulsante di menu è discusso: una persona deve decidere.",
    },
    "c412.details": {
        "en": "A native details/summary disclosure: the browser exposes its role and open state.",
        "de": "Ein natives details/summary-Element: Der Browser vermittelt Rolle und Zustand.",
        "fr": "Un details/summary natif : le navigateur expose son rôle et son état.",
        "it": "Un details/summary nativo: il browser espone ruolo e stato.",
    },
    "c412.icon_technical": {
        "en": "This icon-only control is named “{name}”, a file or code name that does not say what it does.",
        "de": "Dieses reine Symbol-Element heisst «{name}», ein Datei- oder Codename, der nicht sagt, was es tut.",
        "fr": "Ce contrôle à icône seule s'appelle « {name} », un nom de fichier ou de code qui ne dit pas ce qu'il fait.",
        "it": "Questo controllo con sola icona si chiama «{name}», un nome di file o di codice che non dice cosa fa.",
    },
    "c412.icon_ok": {
        "en": "This icon-only control has the name “{name}”.",
        "de": "Dieses reine Symbol-Element hat den Namen «{name}».",
        "fr": "Ce contrôle à icône seule a le nom « {name} ».",
        "it": "Questo controllo con sola icona ha il nome «{name}».",
    },
    "c412.state_synced": {
        "en": "Clicking this control updates its state attribute, so screen readers announce the new state.",
        "de": "Ein Klick aktualisiert das Zustandsattribut dieses Elements; Screenreader melden den neuen Zustand.",
        "fr": "Un clic met à jour l'attribut d'état de ce contrôle ; les lecteurs d'écran annoncent le nouvel état.",
        "it": "Un clic aggiorna l'attributo di stato di questo controllo; i lettori di schermo annunciano il nuovo stato.",
    },
    "c412.state_stale": {
        "en": "Clicking this control changes the page, but its state attribute stays the same: screen readers announce the wrong state.",
        "de": "Ein Klick verändert die Seite, das Zustandsattribut bleibt aber gleich: Screenreader melden den falschen Zustand.",
        "fr": "Un clic modifie la page, mais l'attribut d'état reste le même : les lecteurs d'écran annoncent un état faux.",
        "it": "Un clic modifica la pagina, ma l'attributo di stato resta uguale: i lettori di schermo annunciano uno stato errato.",
    },
    "c412.state_missing": {
        "en": "Clicking this control shows or hides content, but it exposes no state (no aria-expanded): screen-reader users do not know whether it is open.",
        "de": "Ein Klick blendet Inhalte ein oder aus, das Element vermittelt aber keinen Zustand (kein aria-expanded): Screenreader-Nutzende wissen nicht, ob es offen ist.",
        "fr": "Un clic affiche ou masque du contenu, mais le contrôle n'expose aucun état (pas d'aria-expanded) : les utilisateurs de lecteurs d'écran ne savent pas s'il est ouvert.",
        "it": "Un clic mostra o nasconde contenuti, ma il controllo non espone alcuno stato (niente aria-expanded): chi usa un lettore di schermo non sa se è aperto.",
    },
    "c412.link_toggle": {
        "en": "This link to “#” opens or shows content instead of navigating. Experts disagree whether it needs the button role: a person must decide.",
        "de": "Dieser Link auf «#» öffnet oder zeigt Inhalte, statt zu navigieren. Ob er die Rolle Schaltfläche braucht, ist umstritten: Eine Person muss entscheiden.",
        "fr": "Ce lien vers « # » ouvre ou affiche du contenu au lieu de naviguer. Le besoin d'un rôle bouton est discuté : une personne doit trancher.",
        "it": "Questo link a «#» apre o mostra contenuti invece di navigare. Se serva il ruolo pulsante è discusso: una persona deve decidere.",
    },
    "c412.name_toggle": {
        "en": "This control shows its state only by changing its own name (“{name}”). Experts disagree whether that is enough: a person must decide.",
        "de": "Dieses Element zeigt seinen Zustand nur durch den eigenen Namen («{name}»). Ob das genügt, ist umstritten: Eine Person muss entscheiden.",
        "fr": "Ce contrôle n'indique son état qu'en changeant de nom (« {name} »). Les experts divergent : une personne doit trancher.",
        "it": "Questo controllo indica il suo stato solo cambiando nome («{name}»). Gli esperti non concordano: una persona deve decidere.",
    },
    "c412.fragment_only": {
        "en": "This button only changes the part of the address after #, like an in-page link. Which role is right is disputed: a person must decide.",
        "de": "Diese Schaltfläche ändert nur den Teil der Adresse nach #, wie ein Link innerhalb der Seite. Welche Rolle richtig ist, ist umstritten: Eine Person muss entscheiden.",
        "fr": "Ce bouton ne change que la partie de l'adresse après #, comme un lien interne. Le bon rôle est discuté : une personne doit trancher.",
        "it": "Questo pulsante cambia solo la parte dell'indirizzo dopo #, come un link interno. Il ruolo giusto è discusso: una persona deve decidere.",
    },
    "c412.apertus_describes": {
        "en": "Apertus judged that the name “{name}” says what this icon-only control does.",
        "de": "Apertus beurteilt, dass der Name «{name}» sagt, was dieses Symbol-Element tut.",
        "fr": "Apertus juge que le nom « {name} » dit ce que fait ce contrôle à icône.",
        "it": "Apertus giudica che il nome «{name}» dica cosa fa questo controllo con sola icona.",
    },
    "c412.apertus_meaningless": {
        "en": "Apertus judged that the name “{name}” does not say what this icon-only control does.",
        "de": "Apertus beurteilt, dass der Name «{name}» nicht sagt, was dieses Symbol-Element tut.",
        "fr": "Apertus juge que le nom « {name} » ne dit pas ce que fait ce contrôle à icône.",
        "it": "Apertus giudica che il nome «{name}» non dica cosa fa questo controllo con sola icona.",
    },
    "c412.apertus_unsure": {
        "en": "Apertus could not decide whether the name “{name}” is meaningful. A person must check it.",
        "de": "Apertus konnte nicht entscheiden, ob der Name «{name}» aussagekräftig ist. Eine Person muss es prüfen.",
        "fr": "Apertus n'a pas pu décider si le nom « {name} » est parlant. Une personne doit vérifier.",
        "it": "Apertus non ha potuto decidere se il nome «{name}» sia significativo. Una persona deve verificare.",
    },
    "c412.impact": {
        "en": "Screen-reader and voice-control users cannot tell what this control is, what it is called or what state it is in.",
        "de": "Screenreader- und Sprachsteuerungs-Nutzende erfahren nicht, was dieses Element ist, wie es heisst oder in welchem Zustand es ist.",
        "fr": "Les utilisateurs de lecteurs d'écran ou de commande vocale ne savent pas ce qu'est ce contrôle, son nom ou son état.",
        "it": "Chi usa lettori di schermo o comandi vocali non sa cosa sia questo controllo, come si chiami o in che stato sia.",
    },
    "c412.impact_ok": {
        "en": "Assistive technology can announce this control's role, name and state.",
        "de": "Hilfsmittel können Rolle, Name und Zustand dieses Elements ansagen.",
        "fr": "Les technologies d'assistance peuvent annoncer le rôle, le nom et l'état de ce contrôle.",
        "it": "Le tecnologie assistive possono annunciare ruolo, nome e stato di questo controllo.",
    },
})


class NameRoleValue(BaseCheck):
    criterion = "4.1.2"
    prompt_version = PROMPT_VERSION
    max_candidates = 120

    def candidates(self, page: CapturedPage) -> list[Candidate]:
        facts = collect(page)
        if not facts:
            return []
        out: dict[str, Candidate] = {}

        def add(rec: dict, kind: str, **extra) -> None:
            sel = rec["selector"]
            if sel in out and out[sel].extra.get("kind") in ("clickable", "no_checked", "tab_unselected"):
                return  # a static failure is kept
            out[sel] = self.candidate(page, selector=sel, html=rec.get("html", ""), text=norm_ws(rec.get("text", "")),
                                      accessible_name=norm_ws(rec.get("name") or "") or None, kind=kind,
                                      tag=rec.get("tag", ""), role=rec.get("role") or "", **extra)

        asked = 0
        for c in facts.get("clickables") or []:
            kind = clickable_kind(c)
            if kind == "ask_clickable":
                asked += 1
                if asked > MAX_CLICK_QUESTIONS:
                    kind = "clickable_unasked"
            if kind:
                add(c, kind, types=", ".join(c.get("types") or (["click"] if c.get("onclick") else [])),
                    has_interactive=bool(c.get("has_interactive")))
        for w in facts.get("widgets") or []:
            if w.get("aria_hidden"):
                continue
            role, states = w.get("role"), w.get("states") or {}
            if role in CHECKED_ROLES and states.get("aria-checked") is None:
                add(w, "no_checked")
            elif role == "tab" and w.get("tablist_selected") is False:
                add(w, "tab_unselected")
            elif norm_ws(w.get("name")):
                add(w, "widget_ok")
        for d in facts.get("dual") or []:
            add(d, "dual_link")
        for d in facts.get("details") or []:
            add(d, "details")
        for ic in facts.get("icons") or []:
            name = norm_ws(ic.get("name"))
            if _TECHNICAL.search(name):
                add(ic, "icon_technical")
            elif len(name.split()) >= 2:
                add(ic, "icon_ok")
            else:
                add(ic, "ask_icon")
        if page.allow_form_submit and page.live is not None and facts.get("toggles") and not self._probe_skipped(page):
            for rec in toggle_runs(page, facts["toggles"]):
                kind = toggle_kind(rec)
                if kind:
                    rec = {**rec, "name": rec.get("name_after") or rec.get("name")}
                    add(rec, kind, name_before=rec.get("name_before", ""))
        return list(out.values())[: self.max_candidates]

    @staticmethod
    def _probe_skipped(page: CapturedPage) -> bool:
        """The shared form probe refused a form of this page (origin not allow-listed): no clicks."""
        try:
            return any(r.get("skipped") for r in page.form_probe())
        except Exception:
            return True

    def decide(self, c: Candidate) -> Finding | None:
        kind, ui = c.extra.get("kind"), self.ui_lang
        kw = {"tag": c.extra.get("tag") or "element", "role": c.extra.get("role") or "widget",
              "name": (c.accessible_name or "")[:100]}
        if kind == "name_toggle":
            kw["name"] = f"{c.extra.get('name_before', '')[:50]} / {(c.accessible_name or '')[:50]}"

        def fin(outcome: str, key: str, conf: str = "medium", source: str = "heuristic", act: str | None = None):
            impact = {"passed": t("c412.impact_ok", ui), "failed": t("c412.impact", ui)}.get(outcome, t("impact.review", ui))
            return self.finding(c, outcome=outcome, source=source, confidence=conf, excerpt=c.html[:300],
                                explanation=t(key, ui, **kw), user_impact=impact,
                                act_rule=act if act else (None if outcome != "passed" else ...))

        table = {
            "clickable": ("failed", "c412.clickable", "high", "heuristic", None),
            "clickable_unasked": ("cantTell", "c412.click_unsure", "low", "heuristic", None),
            "hidden_duplicate": ("passed", "c412.hidden_duplicate", "low", "heuristic", None),
            "no_checked": ("failed", "c412.no_checked", "high", "rule", "4e8ab6"),
            "tab_unselected": ("failed", "c412.tab_unselected", "medium", "heuristic", None),
            "widget_ok": ("passed", "c412.widget_ok", "medium", "heuristic", None),
            "dual_link": ("cantTell", "c412.dual_link", "low", "heuristic", None),
            "details": ("passed", "c412.details", "high", "heuristic", None),
            "icon_technical": ("failed", "c412.icon_technical", "medium", "heuristic", None),
            "icon_ok": ("passed", "c412.icon_ok", "medium", "heuristic", None),
            "state_synced": ("passed", "c412.state_synced", "high", "heuristic", None),
            "state_stale": ("failed", "c412.state_stale", "high", "heuristic", None),
            "state_missing": ("failed", "c412.state_missing", "medium", "heuristic", None),
            "link_toggle": ("cantTell", "c412.link_toggle", "low", "heuristic", None),
            "name_toggle": ("cantTell", "c412.name_toggle", "low", "heuristic", None),
            "fragment_only": ("cantTell", "c412.fragment_only", "low", "heuristic", None),
        }
        if kind in table:
            outcome, key, conf, source, act = table[kind]
            return fin(outcome, key, conf, source, act)
        return None

    SYSTEM = (
        "You check WCAG 2.1 success criterion 4.1.2 Name, Role, Value for ONE control that shows no visible "
        "text, only an icon. Assistive technology announces its accessible name, given below. Classify the name:\n"
        "- describes: it says what the control does or where it leads\n"
        "- meaningless: it is a file name, a code, an icon or shape name, or a word that does not say what the "
        "control does\n"
        "- unsure: cannot tell\n"
        "quote: the name, copied exactly."
    )

    SYSTEM_CLICK = (
        "You check WCAG 2.1 success criterion 4.1.2 Name, Role, Value for ONE element that has no role but "
        "reacts to the mouse, touch or keys (the events are given in the question). An element used as a button "
        "or link needs that role. Classify the element:\n"
        "- own_control: the element itself acts as a button or link, and no link or button inside it does the "
        "same thing\n"
        "- duplicate: a larger click area (a card, a row, a teaser) whose action repeats a link or button inside it\n"
        "- widget_area: an area for gestures or a complex widget (a map, a slider, a carousel, a drawing area) "
        "whose own controls are separate\n"
        "- unsure: cannot tell\n"
        "quote: the element's text, copied exactly, or empty."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        if c.extra.get("kind") == "ask_clickable":
            inner = "contains" if c.extra.get("has_interactive") else "does not contain"
            return self.task(system=self.system_prompt(self.SYSTEM_CLICK, c),
                             element={"text": c.text[:200], "html": self.prompt_html(c)}, context={},
                             question=(f"The element reacts to: {c.extra.get('types') or 'click'}. It {inner} a native "
                                       "link, button or form field. Is this element itself used as a button or link?"),
                             schema=category_schema(CLICK_CATEGORIES), max_tokens=100)
        return self.task(system=self.system_prompt(self.SYSTEM, c),
                         element={"accessible_name": c.accessible_name or "", "html": self.prompt_html(c)},
                         context={}, question="Does this name tell what the control does?",
                         schema=category_schema(CATEGORIES), max_tokens=100)

    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        category = answer.get("category")
        if c.extra.get("kind") == "ask_clickable":
            outcome = CLICK_OUTCOME.get(category, "cantTell")
            if (category == "duplicate" and not c.extra.get("has_interactive")) or (
                    category == "own_control" and c.extra.get("has_interactive")):
                outcome = "cantTell"  # contradicts the DOM fact: a person decides
            key = {"failed": "c412.apertus_own_control", "passed": "c412.apertus_duplicate",
                   "inapplicable": "c412.apertus_widget_area"}.get(outcome, "c412.click_unsure")
            impact = {"passed": t("c412.impact_ok", ui), "failed": t("c412.impact", ui)}.get(outcome, t("impact.review", ui))
            return self.finding(c, outcome=outcome, source="apertus",
                                confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
                                excerpt=self.model_excerpt(c, answer, outcome),
                                explanation=t(key, ui, tag=c.extra.get("tag") or "element"), user_impact=impact,
                                reason=answer.get("reason"),
                                reason_code=f"apertus_{category}" if category in CLICK_CATEGORIES else "apertus_unsure")
        outcome = {"describes": "passed", "meaningless": "failed"}.get(category, "cantTell")
        key = f"c412.apertus_{category}" if category in CATEGORIES else "c412.apertus_unsure"
        impact = {"passed": t("c412.impact_ok", ui), "failed": t("c412.impact", ui)}.get(outcome, t("impact.review", ui))
        return self.finding(c, outcome=outcome, source="apertus",
                            confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
                            excerpt=self.model_excerpt(c, answer, outcome),
                            explanation=t(key, ui, name=(c.accessible_name or "")[:100]), user_impact=impact,
                            reason=answer.get("reason"),
                            reason_code=f"apertus_{category}" if category in CATEGORIES else "apertus_unsure")


CHECK = NameRoleValue
