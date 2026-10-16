"""2.4.3 Focus Order, level A: does the sequential (Tab) order preserve meaning and
operability? No ACT rule exists for this criterion.

Facts (code). The live work happens in an ISOLATED, GUARDED CLONE of the audited page
(see Clone: the same URL or raw HTML in a new browser context with the same viewport and
network policy; every non-GET/HEAD request and every new top-level navigation is aborted
unless its origin is allow-listed, window.open is stubbed). The page other checks read is
never focused, clicked or scrolled. Bounded: ≤ 60 Tab stops, ≤ 4 trigger probes, at most
20 s and a quarter of the time left before the scan deadline (page.remaining());
submit/reset buttons and links with a real target are never activated.
  * Tab sequence: the real keyboard order (Playwright key presses), with each stop's box,
    tabindex, fieldset/group, form, landmark, fixed/sticky position and whether it is
    visible WHILE focused.
  * Trigger probes, ONLY on the bundled demo and the evaluation servers (allow_form_submit,
    the same gate as the form probe): a button that opens something (aria-haspopup/
    expanded/controls or a plain type="button") is activated with Enter on a freshly
    reloaded clone; content that becomes visible is located; does focus move into it, or
    does the next Tab reach it? On any other site nothing is activated: controls that
    announce opened content (and hidden dialogs) become cantTell "not tested on external
    sites".
  * CSS reordering: the 1.3.2 facts (capture/js/c_1_3_2.js, read-only, main page):
    containers whose blocks are shown in another order than the DOM order, restricted
    to moved blocks that contain focusable elements.
  * Without a live page (unit tests, raw facts): the sequential order is rebuilt from the
    serialised DOM (positive tabindex first in ascending order, then document order).

Cascade
  positive tabindex
    a fieldset/group is left and re-entered (interleaved groups) → failed (heuristic, F44)
    a submit button is reached before fields of its form           → failed (heuristic, F44)
    the first stop is a positive-tabindex element shown far below
      the next stops (footer link, final button reached first)     → failed (heuristic, F44)
    focus order of the tabindex elements = their reading order
      (row by row or column by column)                             → passed (heuristic)
    inside one form, neither reading order                         → failed (heuristic, F44)
    otherwise                                                       → Apertus
  CSS-reordered blocks with focusable elements
    inside one form / fieldset                                      → failed (heuristic, C27)
    only fixed or sticky blocks moved (banner fixed at the top,
      last in the DOM)                                              → cantTell (heuristic)
    across independent blocks                                       → Apertus
  trigger probe (demo / evaluation): new content appeared
    focus moved into it, or the next Tab reaches it                 → passed (heuristic, H102/SCR26)
    neither                                                         → failed (heuristic, F85)
  external site: control announcing opened content, hidden dialog   → cantTell (not tested)
  stop not visible while focused                                    → cantTell (heuristic)

Apertus question (text; vision never required): `focus_order` and `visual_order` list the
names of the focusable elements concerned.
  "Does this focus order preserve meaning and operability?"
  effect: breaks | independent | preserves | other → failed | cantTell | passed | cantTell
  (independent blocks in another order: a judgement call, PROTOCOL 2.4.3/C1 → cantTell)

Limits: shadow DOM and iframes are not traversed; menus that open on hover only are not
probed; arrow-key navigation inside composite widgets is out of scope; a page that
changes on load (random content) may give the clone other selectors.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from pathlib import Path

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

log = logging.getLogger(__name__)

PROMPT_VERSION = "2.4.3/v1"
JS = (Path(__file__).resolve().parents[1] / "capture" / "js" / "c_2_4_3.js").read_text(encoding="utf-8")
EFFECTS = ["breaks", "independent", "preserves", "other"]
EFFECT_OUTCOME = {"breaks": "failed", "independent": "cantTell", "preserves": "passed", "other": "cantTell"}
MAX_STOPS = 60
MAX_PROBES = 4
LIVE_BUDGET_S = 20.0  # wall-clock budget for all live work of this check on one page
MAX_NAMES = 16

register({
    "c243.interleaved": {
        "en": "Positive tabindex values make the focus leave a group of fields and come back to it later, so one group is never completed before the next.",
        "de": "Positive tabindex-Werte lassen den Fokus eine Feldgruppe verlassen und später zurückkehren: Keine Gruppe wird vor der nächsten abgeschlossen.",
        "fr": "Des valeurs tabindex positives font sortir le focus d'un groupe de champs puis l'y ramènent : aucun groupe n'est terminé avant le suivant.",
        "it": "Valori tabindex positivi fanno uscire il focus da un gruppo di campi e poi rientrarvi: nessun gruppo viene completato prima del successivo.",
    },
    "c243.submit_first": {
        "en": "Positive tabindex values make the keyboard reach the button \"{name}\" before the fields of its form.",
        "de": "Positive tabindex-Werte führen den Tastaturfokus zur Schaltfläche «{name}», bevor er die Felder ihres Formulars erreicht.",
        "fr": "Des valeurs tabindex positives amènent le clavier sur le bouton « {name} » avant les champs de son formulaire.",
        "it": "Valori tabindex positivi portano la tastiera sul pulsante «{name}» prima dei campi del suo modulo.",
    },
    "c243.jump_first": {
        "en": "A positive tabindex makes \"{name}\" the first Tab stop, although it is shown far below content that is reached after it.",
        "de": "Ein positiver tabindex macht «{name}» zum ersten Fokus-Halt, obwohl es weit unter dem Inhalt steht, der danach fokussiert wird.",
        "fr": "Un tabindex positif fait de « {name} » le premier arrêt de la touche Tab, alors qu'il est affiché bien plus bas que du contenu atteint après lui.",
        "it": "Un tabindex positivo rende «{name}» la prima tappa del tasto Tab, anche se è mostrato molto più in basso di contenuti raggiunti dopo di esso.",
    },
    "c243.tabindex_logical": {
        "en": "Positive tabindex values are used, but the resulting focus order follows the reading order.",
        "de": "Es werden positive tabindex-Werte verwendet, die Fokusreihenfolge folgt aber der Lesereihenfolge.",
        "fr": "Des valeurs tabindex positives sont utilisées, mais l'ordre du focus suit l'ordre de lecture.",
        "it": "Sono usati valori tabindex positivi, ma l'ordine del focus segue l'ordine di lettura.",
    },
    "c243.tabindex_jumbled": {
        "en": "Positive tabindex values make the focus jump around the fields of one form instead of following the reading order.",
        "de": "Positive tabindex-Werte lassen den Fokus zwischen den Feldern eines Formulars springen, statt der Lesereihenfolge zu folgen.",
        "fr": "Des valeurs tabindex positives font sauter le focus entre les champs d'un formulaire au lieu de suivre l'ordre de lecture.",
        "it": "Valori tabindex positivi fanno saltare il focus tra i campi di un modulo invece di seguire l'ordine di lettura.",
    },
    "c243.form_reordered": {
        "en": "CSS shows the fields of this form in a different order from the code: the Tab key follows the code order and jumps between them.",
        "de": "CSS zeigt die Felder dieses Formulars in anderer Reihenfolge als im Code: Die Tabulatortaste folgt dem Code und springt zwischen ihnen.",
        "fr": "Le CSS affiche les champs de ce formulaire dans un autre ordre que le code : la touche Tab suit le code et saute d'un champ à l'autre.",
        "it": "Il CSS mostra i campi di questo modulo in un ordine diverso dal codice: il tasto Tab segue il codice e salta da un campo all'altro.",
    },
    "c243.fixed_last": {
        "en": "A block fixed at the edge of the screen comes last in the focus order. Whether this harms the order is debated.",
        "de": "Ein am Bildschirmrand fixierter Block kommt in der Fokusreihenfolge zuletzt. Ob das die Reihenfolge stört, ist umstritten.",
        "fr": "Un bloc fixé au bord de l'écran arrive en dernier dans l'ordre du focus. Cela nuit-il à l'ordre ? Les avis divergent.",
        "it": "Un blocco fissato al bordo dello schermo arriva per ultimo nell'ordine del focus. Se ciò nuoccia all'ordine è controverso.",
    },
    "c243.dialog_not_reached": {
        "en": "After \"{name}\" opens new content, focus stays outside it and the next Tab does not reach it.",
        "de": "Wenn «{name}» neuen Inhalt öffnet, bleibt der Fokus ausserhalb, und mit der nächsten Tabulatortaste gelangt man nicht hinein.",
        "fr": "Après l'ouverture d'un contenu par « {name} », le focus reste à l'extérieur et la touche Tab suivante ne l'atteint pas.",
        "it": "Dopo che «{name}» apre un nuovo contenuto, il focus resta fuori e il Tab successivo non lo raggiunge.",
    },
    "c243.dialog_focus_in": {
        "en": "\"{name}\" opens new content and focus moves into it.",
        "de": "«{name}» öffnet neuen Inhalt, und der Fokus wird hineinverschoben.",
        "fr": "« {name} » ouvre un contenu et le focus y est déplacé.",
        "it": "«{name}» apre un nuovo contenuto e il focus vi viene spostato.",
    },
    "c243.dialog_adjacent": {
        "en": "\"{name}\" opens new content that the next Tab reaches directly.",
        "de": "«{name}» öffnet neuen Inhalt, den man mit der nächsten Tabulatortaste direkt erreicht.",
        "fr": "« {name} » ouvre un contenu que la touche Tab suivante atteint directement.",
        "it": "«{name}» apre un nuovo contenuto che il Tab successivo raggiunge direttamente.",
    },
    "c243.not_tested_external": {
        "en": "Not tested on external sites: \"{name}\" may open content, and Klar. activates controls only on the demo and test pages. A person must check that focus moves into the opened content.",
        "de": "Auf externen Websites nicht getestet: «{name}» öffnet womöglich Inhalt, und Klar. betätigt Bedienelemente nur auf der Demo-Website und auf Testseiten. Eine Person muss prüfen, ob der Fokus in den geöffneten Inhalt wechselt.",
        "fr": "Non testé sur les sites externes : « {name} » peut ouvrir un contenu, et Klar. n'active des contrôles que sur la démo et les pages de test. Une personne doit vérifier que le focus passe dans le contenu ouvert.",
        "it": "Non verificato sui siti esterni: «{name}» può aprire un contenuto, e Klar. attiva i comandi solo sulla demo e sulle pagine di test. Una persona deve verificare che il focus passi nel contenuto aperto.",
    },
    "c243.hidden_focus": {
        "en": "The keyboard focus lands on \"{name}\", which is not visible while it has focus.",
        "de": "Der Tastaturfokus landet auf «{name}», das nicht sichtbar ist, solange es den Fokus hat.",
        "fr": "Le focus clavier arrive sur « {name} », qui n'est pas visible pendant qu'il a le focus.",
        "it": "Il focus da tastiera arriva su «{name}», che non è visibile mentre ha il focus.",
    },
    "c243.apertus_breaks": {
        "en": "The focus order differs from the visual order, and Apertus judged that it separates things that belong together.",
        "de": "Die Fokusreihenfolge weicht von der optischen ab; Apertus beurteilt, dass sie Zusammengehöriges trennt.",
        "fr": "L'ordre du focus diffère de l'ordre visuel ; selon Apertus, il sépare des éléments qui vont ensemble.",
        "it": "L'ordine del focus differisce da quello visivo; secondo Apertus separa elementi che vanno insieme.",
    },
    "c243.apertus_independent": {
        "en": "Independent blocks are reached in a different order from the one shown. Whether this affects meaning is a judgement call.",
        "de": "Unabhängige Blöcke werden in anderer Reihenfolge erreicht als angezeigt. Ob das den Sinn betrifft, ist eine Ermessensfrage.",
        "fr": "Des blocs indépendants sont atteints dans un autre ordre que celui de l'affichage. L'effet sur le sens relève de l'appréciation.",
        "it": "Blocchi indipendenti sono raggiunti in un ordine diverso da quello mostrato. Se ciò influisca sul senso è una questione di giudizio.",
    },
    "c243.apertus_preserves": {
        "en": "The focus order differs from the visual order, but Apertus judged that it still follows a logical sequence.",
        "de": "Die Fokusreihenfolge weicht von der optischen ab; Apertus beurteilt sie aber als logische Abfolge.",
        "fr": "L'ordre du focus diffère de l'ordre visuel, mais selon Apertus il suit une séquence logique.",
        "it": "L'ordine del focus differisce da quello visivo, ma secondo Apertus segue una sequenza logica.",
    },
    "c243.apertus_unsure": {
        "en": "The focus order differs from the visual order; Apertus could not tell whether this harms meaning or operation. A person must check it.",
        "de": "Die Fokusreihenfolge weicht von der optischen ab; Apertus konnte nicht entscheiden, ob das Sinn oder Bedienung stört. Eine Person muss es prüfen.",
        "fr": "L'ordre du focus diffère de l'ordre visuel ; Apertus n'a pas pu décider si cela nuit au sens ou à l'utilisation. Une personne doit le vérifier.",
        "it": "L'ordine del focus differisce da quello visivo; Apertus non ha potuto stabilire se ciò nuoccia al senso o all'uso. Una persona deve verificarlo.",
    },
    "c243.impact": {
        "en": "Keyboard and screen-reader users meet the content in an order that separates things that belong together.",
        "de": "Tastatur- und Screenreader-Nutzende erreichen die Inhalte in einer Reihenfolge, die Zusammengehöriges trennt.",
        "fr": "Les personnes utilisant le clavier ou un lecteur d'écran parcourent le contenu dans un ordre qui sépare ce qui va ensemble.",
        "it": "Chi usa la tastiera o un lettore di schermo incontra i contenuti in un ordine che separa ciò che va insieme.",
    },
    "c243.impact_dialog": {
        "en": "Keyboard users do not reach the opened content without tabbing through the rest of the page.",
        "de": "Tastatur-Nutzende erreichen den geöffneten Inhalt erst, nachdem sie mit der Tabulatortaste den Rest der Seite durchlaufen haben.",
        "fr": "Les personnes utilisant le clavier n'atteignent le contenu ouvert qu'après avoir parcouru le reste de la page.",
        "it": "Chi usa la tastiera raggiunge il contenuto aperto solo dopo aver attraversato il resto della pagina.",
    },
    "c243.impact_hidden": {
        "en": "Sighted keyboard users lose track of where the focus is.",
        "de": "Sehende Tastatur-Nutzende verlieren den Überblick, wo der Fokus ist.",
        "fr": "Les personnes voyantes utilisant le clavier ne savent plus où se trouve le focus.",
        "it": "Chi vede e usa la tastiera perde di vista dove si trova il focus.",
    },
    "c243.impact_ok": {
        "en": "Keyboard users move through the content in a logical order.",
        "de": "Tastatur-Nutzende bewegen sich in einer logischen Reihenfolge durch den Inhalt.",
        "fr": "Les personnes utilisant le clavier parcourent le contenu dans un ordre logique.",
        "it": "Chi usa la tastiera si muove nel contenuto in un ordine logico.",
    },
    "c243.fix_tabindex": {
        "en": "Remove the positive tabindex values and put the elements in the code in the reading order.",
        "de": "Entfernen Sie die positiven tabindex-Werte und ordnen Sie die Elemente im Code in Lesereihenfolge an.",
        "fr": "Supprimez les valeurs tabindex positives et placez les éléments dans le code dans l'ordre de lecture.",
        "it": "Eliminate i valori tabindex positivi e disponete gli elementi nel codice nell'ordine di lettura.",
    },
    "c243.fix_order": {
        "en": "Put the fields in the code in the order in which they are shown, instead of reordering them with CSS.",
        "de": "Ordnen Sie die Felder im Code in der angezeigten Reihenfolge an, statt sie mit CSS umzuordnen.",
        "fr": "Placez les champs dans le code dans l'ordre affiché au lieu de les réordonner avec CSS.",
        "it": "Disponete i campi nel codice nell'ordine in cui sono mostrati invece di riordinarli con CSS.",
    },
    "c243.fix_dialog": {
        "en": "Move focus into the opened content (for example with dialog.showModal()), or insert it in the code right after its button.",
        "de": "Verschieben Sie den Fokus in den geöffneten Inhalt (zum Beispiel mit dialog.showModal()) oder fügen Sie ihn im Code direkt nach seiner Schaltfläche ein.",
        "fr": "Déplacez le focus dans le contenu ouvert (par exemple avec dialog.showModal()) ou insérez-le dans le code juste après son bouton.",
        "it": "Spostate il focus nel contenuto aperto (per esempio con dialog.showModal()) o inseritelo nel codice subito dopo il suo pulsante.",
    },
})


# --- live helpers (shared with 2.2.2) ---------------------------------------------------------------

def allowed_origins(page: CapturedPage) -> set[str]:
    """Origins that may receive non-GET requests and navigations from a clone: EXACTLY the
    scan's form_origins (CapturedPage.form_origins: demo / evaluation servers), never a
    fallback. Empty (the default, and always when allow_form_submit is off) means no
    interaction at all."""
    if not page.allow_form_submit:
        return set()
    return {o for o in (page.form_origins or ()) if o}


def interaction_allowed(page: CapturedPage) -> bool:
    """Clicks and key presses that may trigger page scripts (control tests, trigger probes)
    run ONLY where the scan may submit forms (the same gate as capture/probe.py):
    allow_form_submit, a non-empty form_origins, and the page's FINAL origin (after
    redirects or a meta refresh) in form_origins. Elsewhere code only observes."""
    from urllib.parse import urlparse

    from klar.netpolicy import origin_of

    allowed = allowed_origins(page)
    if not allowed:
        return False
    if urlparse(page.url).scheme in ("http", "https", "file"):
        try:
            return origin_of(page.url) in allowed
        except Exception:
            return False
    return True  # raw HTML (about:blank): the clone's guard still allows only `allowed`


class Clone:
    """The audited page loaded again in a NEW browser context (same browser, viewport and
    network policy), guarded so that it cannot change anything on the audited site:
      * every request that is not GET/HEAD is aborted, and so is every new top-level
        document navigation after the initial load, unless its origin is allow-listed
        (demo / evaluation only, see allowed_origins);
      * window.open is stubbed (a pop-up's own navigation is blocked like any other);
      * focus, clicks, a fake clock or reduced-motion emulation never touch the page other
        checks read (Playwright's clock is context-wide, hence the new context)."""

    def __init__(self, page: CapturedPage, *, clock: bool, timeout_ms: int):
        self.source = page
        self.clock = clock
        self.timeout_ms = timeout_ms
        # a page that ended up outside form_origins (redirect, meta refresh) allows nothing at all
        self.allowed = allowed_origins(page) if interaction_allowed(page) else set()
        self.blocked: list[str] = []
        self._armed = False
        self.ctx = None
        self.tab = None

    def _guard(self, route, request) -> None:
        from klar.netpolicy import origin_of

        try:
            origin = origin_of(request.url)
        except Exception:
            origin = ""
        try:
            nav = self._armed and request.is_navigation_request() and request.frame.parent_frame is None
        except Exception:
            nav = self._armed
        if (request.method not in ("GET", "HEAD") or nav) and origin not in self.allowed:
            self.blocked.append(f"{request.method} {request.url[:200]}")
            route.abort("blockedbyclient")
            return
        route.fallback()

    def open(self) -> "Clone":
        from klar.capture.browser import install_policy

        live = self.source.live
        vp = live.viewport_size or {"width": 1280, "height": 900}
        self.ctx = live.context.browser.new_context(viewport=vp, device_scale_factor=1, bypass_csp=True,
                                                    service_workers="block", accept_downloads=False)
        self.ctx.set_default_timeout(self.timeout_ms)
        install_policy(self.ctx, self.source.policy)
        self.ctx.route("**/*", self._guard)  # registered last → runs first, then falls back to the policy
        self.ctx.add_init_script("window.open = function () { return null; };")
        if self.clock:
            self.ctx.clock.install()
        self.tab = self.ctx.new_page()
        self.reload()
        return self

    def reload(self, *, reduced_motion: str | None = None) -> None:
        """(Re)load the audited URL or raw HTML: a fresh state for the next test."""
        from klar.capture.browser import EXTRACT_JS

        self._armed = False
        try:
            if reduced_motion:
                self.tab.emulate_media(reduced_motion=reduced_motion)
            if self.source.source_html is not None:
                self.tab.set_content(self.source.source_html, wait_until="load")
            else:
                self.tab.goto(self.source.url, wait_until="load")
            self.tab.evaluate(EXTRACT_JS)
        finally:
            self._armed = True

    def close(self) -> None:
        try:
            if self.ctx is not None:
                self.ctx.close()
        except Exception:
            pass


@contextmanager
def isolated_clone(page: CapturedPage, *, clock: bool = False, timeout_ms: int = 8000):
    """Yield an open, guarded Clone (see Clone); its context is closed on exit."""
    clone = Clone(page, clock=clock, timeout_ms=timeout_ms)
    try:
        yield clone.open()
    finally:
        clone.close()


def remaining_budget(page: CapturedPage, cap: float) -> float:
    """Seconds this check may spend on live work now: at most `cap`, and at most a quarter of
    what is left before the scan deadline (CapturedPage.remaining(), math.inf when unbounded)."""
    return max(0.0, min(cap, page.remaining() / 4))


def visual_orders(items: list[tuple[int, dict]]) -> tuple[list[int], list[int]]:
    """(row-by-row, column-by-column) order of boxes {x, y, w, h}; returns item ids."""
    def overlap(a0, a1, b0, b1):
        return max(0.0, min(a1, b1) - max(a0, b0))

    rows: list[dict] = []
    for i, b in sorted(items, key=lambda it: (it[1]["y"], it[1]["x"])):
        row = next((r for r in rows if overlap(r["y0"], r["y1"], b["y"], b["y"] + b["h"]) >= 0.5 * min(r["y1"] - r["y0"], b["h"])), None)
        if row:
            row["items"].append((i, b))
            row["y0"], row["y1"] = min(row["y0"], b["y"]), max(row["y1"], b["y"] + b["h"])
        else:
            rows.append({"y0": b["y"], "y1": b["y"] + b["h"], "items": [(i, b)]})
    by_row = [i for r in sorted(rows, key=lambda r: r["y0"]) for i, _ in sorted(r["items"], key=lambda it: it[1]["x"])]
    cols: list[dict] = []
    for i, b in sorted(items, key=lambda it: (it[1]["x"], it[1]["y"])):
        col = next((c for c in cols if overlap(c["x0"], c["x1"], b["x"], b["x"] + b["w"]) >= 0.5 * min(c["x1"] - c["x0"], b["w"])), None)
        if col:
            col["items"].append((i, b))
            col["x0"], col["x1"] = min(col["x0"], b["x"]), max(col["x1"], b["x"] + b["w"])
        else:
            cols.append({"x0": b["x"], "x1": b["x"] + b["w"], "items": [(i, b)]})
    by_col = [i for c in sorted(cols, key=lambda c: c["x0"]) for i, _ in sorted(c["items"], key=lambda it: it[1]["y"])]
    return by_row, by_col


def static_stops(html: str) -> list[dict]:
    """Sequential focus order rebuilt from the serialised DOM: positive tabindex first
    (ascending, ties in document order), then tabindex=0 / natively focusable elements."""
    from klar.checks.c_1_3_1 import parse_html

    root = parse_html(html)
    natural = {"button", "select", "textarea", "summary", "iframe"}
    found: list[tuple[int, int, dict]] = []
    for pos, n in enumerate(root.iter()):
        tag, a = n.tag, n.attrs
        ti = a.get("tabindex")
        try:
            tabindex = int(ti) if ti not in (None, "") else None
        except ValueError:
            tabindex = None
        focusable = (tag in natural or (tag == "a" and "href" in a) or (tag == "input" and a.get("type") != "hidden")
                     or tabindex is not None)
        if not focusable or "disabled" in a or (tabindex is not None and tabindex < 0):
            continue
        anc = list(n.ancestors())
        group = next((x for x in anc if x.tag == "fieldset" or x.attrs.get("role") in ("group", "radiogroup")), None)
        form = next((x for x in anc if x.tag == "form"), None)
        region = next((x for x in anc if x.tag in ("form", "nav", "aside", "header", "footer", "main", "section", "dialog")), None)
        typ = a.get("type", "").lower()
        found.append((tabindex or 0, pos, {
            "selector": n.path(), "tag": tag, "type": typ, "tabindex": tabindex,
            "name": " ".join(n.text().split())[:80] or a.get("aria-label", "") or a.get("name", "") or a.get("value", ""),
            "rect": None, "visible": True, "fixed": False,
            "group": group.path() if group else None, "form": form.path() if form else None,
            "region": region.path() if region else None,
            "submit": (tag == "button" and typ in ("submit", "") and form is not None) or (tag == "input" and typ in ("submit", "image")),
        }))
    positive = sorted((f for f in found if f[0] > 0), key=lambda f: (f[0], f[1]))
    rest = [f for f in found if f[0] <= 0]
    return [f[2] for f in positive + rest]


class FocusOrder(BaseCheck):
    criterion = "2.4.3"
    prompt_version = PROMPT_VERSION
    needs_vision = False  # text question; no image is ever sent
    max_candidates = 30

    # -- 1. facts --------------------------------------------------------------------------------
    def facts(self, page: CapturedPage) -> dict:
        pre = page.elements.get("c243")  # tests inject [facts] (a list, like every element collection)
        if isinstance(pre, list):
            pre = pre[0] if pre else None
        if pre is not None:
            return pre
        if page.live is None:
            return {"stops": static_stops(page.html), "probes": [], "reorders": [], "static": True}
        from klar.checks import c_1_3_2

        facts: dict = {"stops": [], "probes": [], "reorders": [], "untested": []}
        try:
            facts["reorders"] = (page.evaluate(c_1_3_2.JS, {"max": 30}) or {}).get("reorders", [])
        except Exception as exc:
            log.info("2.4.3 reorder facts failed: %s", exc)
        budget = remaining_budget(page, LIVE_BUDGET_S)
        if budget < 3.0:
            facts.update(stops=static_stops(page.html), static=True)
            return facts
        deadline = time.monotonic() + budget
        try:
            with isolated_clone(page, timeout_ms=int(min(8.0, budget) * 1000)) as clone:
                facts["stops"] = self.tab_sequence(clone.tab, deadline)
                if interaction_allowed(page):
                    facts["probes"] = self.probe_triggers(clone, deadline)
                else:  # no key presses on buttons of external sites: a person checks opened content
                    facts["untested"] = self.untested_triggers(clone.tab)
        except Exception as exc:
            log.info("2.4.3 live facts failed: %s", exc)
            if not facts["stops"]:
                facts["stops"] = static_stops(page.html)
                facts["static"] = True
        return facts

    @staticmethod
    def _install(tab) -> None:
        from klar.capture.browser import js

        tab.evaluate(js(JS))

    def tab_sequence(self, tab, deadline: float) -> list[dict]:
        """Passive walk: Tab key presses only (focus handlers may run; the clone's guard
        aborts any non-GET request or navigation they start)."""
        from klar.capture.browser import js

        self._install(tab)
        tab.evaluate("() => window.__k243.reset()")
        stops: list[dict] = []
        seen: dict[str, int] = {}
        for _ in range(MAX_STOPS):
            if time.monotonic() > deadline:
                break
            tab.keyboard.press("Tab")
            info = tab.evaluate(js("() => window.__k243.active()"))
            if not info:
                break
            if info["selector"] in seen:
                break  # wrapped around
            seen[info["selector"]] = len(stops)
            stops.append(info)
        return stops

    def untested_triggers(self, tab) -> list[dict]:
        """Controls that announce opened content (aria-haspopup/expanded/controls) and hidden
        dialogs, listed without activating anything."""
        from klar.capture.browser import js

        self._install(tab)
        return tab.evaluate(js(f"() => window.__k243.announced({MAX_PROBES})")) or []

    def probe_triggers(self, clone, deadline: float) -> list[dict]:
        """Demo / evaluation only (interaction_allowed): Enter on each trigger in a freshly
        reloaded clone. Submit/reset buttons and links with a real target are never chosen."""
        from klar.capture.browser import js

        tab = clone.tab
        url = tab.url
        triggers = tab.evaluate(js(f"() => window.__k243.triggers({MAX_PROBES})")) or []
        probes: list[dict] = []
        for trig in triggers:
            if time.monotonic() > deadline:
                break
            try:
                clone.reload()  # fresh state for every probe (same guarded context, HTTP cache kept)
                self._install(tab)
                tab.evaluate("() => window.__k243.remember()")
                tab.locator(trig["selector"]).first.focus(timeout=2000)
                tab.keyboard.press("Enter")
                tab.wait_for_timeout(250)
                if tab.url != url:
                    break  # the control navigated: stop probing
                new = tab.evaluate("() => window.__k243.appeared()") or []
                if not new:
                    continue
                sels = [n["selector"] for n in new]
                if any(n.get("contains_focus") for n in new):
                    result = "focus_in"
                else:
                    tab.keyboard.press("Tab")
                    result = "adjacent" if tab.evaluate("s => window.__k243.focusIn(s)", sels) else "not_reached"
                probes.append({"trigger": trig, "content": new[0], "result": result})
            except Exception as exc:
                log.info("2.4.3 probe of %s failed: %s", trig.get("selector"), exc)
        return probes

    # -- 2. candidates -----------------------------------------------------------------------------
    def candidates(self, page: CapturedPage) -> list[Candidate]:
        f = self.facts(page)
        stops = f.get("stops") or []
        out: list[Candidate] = []
        out += self.tabindex_candidates(page, stops, static=bool(f.get("static")))
        out += self.reorder_candidates(page, f.get("reorders") or [])
        for p in f.get("probes") or []:
            trig, content = p["trigger"], p["content"]
            sel = content["selector"] if page.selector_exists(content["selector"]) else trig["selector"]
            kind = {"focus_in": "dialog_focus_in", "adjacent": "dialog_adjacent"}.get(p["result"], "dialog_not_reached")
            out.append(self.candidate(page, selector=sel, html=content.get("html", ""),
                                      text=f"{trig.get('name', '')} {content.get('text', '')}".strip(), lang=page.lang,
                                      kind=kind, trigger=trig.get("name", ""), trigger_selector=trig["selector"],
                                      key="#probe"))
        for u in (f.get("untested") or [])[:MAX_PROBES]:
            out.append(self.candidate(page, selector=u["selector"], html=u.get("html", ""), text=u.get("name", ""),
                                      lang=page.lang, kind="not_tested_external", name=u.get("name", ""), key="#untested"))
        for s in [s for s in stops if not s.get("visible", True)][:5]:
            out.append(self.candidate(page, selector=s["selector"], html="", text=s.get("name", ""), lang=page.lang,
                                      kind="hidden_focus", name=s.get("name", ""), key="#hidden"))
        return out[: self.max_candidates]

    def tabindex_candidates(self, page: CapturedPage, stops: list[dict], *, static: bool) -> list[Candidate]:
        pos = [i for i, s in enumerate(stops) if (s.get("tabindex") or 0) > 0]
        if not pos:
            return []
        out: list[Candidate] = []

        def container(idx: list[int]) -> str:
            forms = {stops[i].get("form") for i in idx}
            if len(forms) == 1 and None not in forms:
                return forms.pop()
            regions = {stops[i].get("region") for i in idx}
            if len(regions) == 1 and None not in regions:
                return regions.pop()
            return stops[idx[0]]["selector"]

        def make(kind: str, idx: list[int], **extra) -> Candidate:
            names = [stops[i].get("name", "") for i in idx][:MAX_NAMES]
            return self.candidate(page, selector=extra.pop("selector", None) or container(idx), html="",
                                  text=" | ".join(n for n in names if n), lang=page.lang, kind=kind, key=f"#{kind}",
                                  **extra)

        # (a) a group is left and re-entered
        by_group: dict[str, list[int]] = {}
        for i, s in enumerate(stops):
            if s.get("group"):
                by_group.setdefault(s["group"], []).append(i)
        broken = [ix for ix in by_group.values() if len(ix) >= 2 and ix[-1] - ix[0] + 1 != len(ix)
                  and any(i in pos for i in ix)]
        if broken:
            idx = sorted({i for ix in broken for i in ix})
            return [make("interleaved", idx)]
        # (b) a submit button before fields of its form
        for i, s in enumerate(stops):
            if s.get("submit") and s.get("form") and any(
                    o.get("form") == s["form"] and not o.get("submit") for o in stops[i + 1:]) and (i in pos or any(
                    j in pos for j in range(i + 1, len(stops)) if stops[j].get("form") == s["form"])):
                return [make("submit_first", [i] + [j for j in range(i + 1, len(stops)) if stops[j].get("form") == s["form"]],
                             name=s.get("name", ""))]
        # (c) the first stop is a positive-tabindex element far below the following ones
        first = stops[0]
        if 0 in pos and first.get("rect") and len(stops) >= 4:
            following = [s["rect"]["y"] for s in stops[1:4] if s.get("rect")]
            if following and first["rect"]["y"] > max(following) + 200:
                return [make("jump_first", [0], selector=first["selector"], name=first.get("name", ""))]
        if static and first.get("region") and "footer" in (first.get("region") or "") and 0 in pos:
            return [make("jump_first", [0], selector=first["selector"], name=first.get("name", ""))]
        # (d) does the order of the tabindex elements follow a reading order?
        rects = [(i, stops[i]["rect"]) for i in pos if stops[i].get("rect")]
        if len(rects) == len(pos) and len(pos) >= 2:
            by_row, by_col = visual_orders(rects)
            if pos in (by_row, by_col):
                return [make("tabindex_logical", pos)]
            forms = {stops[i].get("form") for i in pos}
            if len(forms) == 1 and None not in forms:
                return [make("tabindex_jumbled", pos)]
            focus_names = [stops[i].get("name", "") for i in pos]
            visual_names = [stops[i].get("name", "") for i in by_row]
        else:
            focus_names = [stops[i].get("name", "") for i in pos]
            visual_names = []
        context = {"focus_order": self._numbered(focus_names)}
        if visual_names:
            context["visual_order"] = self._numbered(visual_names)
        cand = make("ask_tabindex", pos)
        cand.context = context
        return out + [cand]

    def reorder_candidates(self, page: CapturedPage, reorders: list[dict]) -> list[Candidate]:
        out: list[Candidate] = []
        for r in reorders:
            segs = {s["i"]: s for s in r.get("segments", [])}
            moved = [segs[i] for i in r.get("moved", []) if i in segs]
            if not any(s.get("focusables") for s in moved):
                continue  # only non-interactive parts move: the focus order is unaffected
            focus_names = [n for i in sorted(segs) for n in segs[i].get("names", [])]
            visual_names = [n for i in r.get("visual", []) if i in segs for n in segs[i].get("names", [])]
            if focus_names == visual_names:
                continue
            if r.get("fixed_only"):
                kind = "fixed_last"
            elif r.get("in_form"):
                kind = "form_reordered"
            else:
                kind = "ask_reorder"
            context = {"focus_order": self._numbered(focus_names[:MAX_NAMES]),
                       "visual_order": self._numbered(visual_names[:MAX_NAMES])} if kind == "ask_reorder" else {}
            out.append(self.candidate(page, selector=r["selector"], html=r.get("html", ""),
                                      text=" | ".join(focus_names[:MAX_NAMES]), context=context,
                                      lang=r.get("lang") or page.lang, kind=kind, key="#reorder"))
        return out

    @staticmethod
    def _numbered(names: list[str]) -> str:
        return " ; ".join(f"{k}. {n or '(unnamed)'}" for k, n in enumerate(names, 1))

    # -- 3. deterministic decisions --------------------------------------------------------------------
    def decide(self, c: Candidate) -> Finding | None:
        kind, ui = c.extra.get("kind"), self.ui_lang
        name = c.extra.get("name") or c.extra.get("trigger") or ""
        excerpt = name if name and name in c.text else None
        failed = {
            "interleaved": ("c243.interleaved", "c243.impact", "c243.fix_tabindex", "high"),
            "submit_first": ("c243.submit_first", "c243.impact", "c243.fix_tabindex", "high"),
            "jump_first": ("c243.jump_first", "c243.impact", "c243.fix_tabindex", "high"),
            "tabindex_jumbled": ("c243.tabindex_jumbled", "c243.impact", "c243.fix_tabindex", "medium"),
            "form_reordered": ("c243.form_reordered", "c243.impact", "c243.fix_order", "high"),
            "dialog_not_reached": ("c243.dialog_not_reached", "c243.impact_dialog", "c243.fix_dialog", "high"),
        }
        if kind in failed:
            key, impact, fix, conf = failed[kind]
            return self.finding(c, outcome="failed", source="heuristic", confidence=conf, excerpt=excerpt,
                                explanation=t(key, ui, name=name), user_impact=t(impact, ui), fix_hint=t(fix, ui))
        if kind in ("tabindex_logical", "dialog_focus_in", "dialog_adjacent"):
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", excerpt=excerpt,
                                explanation=t(f"c243.{kind}", ui, name=name), user_impact=t("c243.impact_ok", ui))
        if kind == "not_tested_external":
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="low", excerpt=excerpt,
                                explanation=t("c243.not_tested_external", ui, name=name), user_impact=t("impact.review", ui))
        if kind == "fixed_last":
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="medium",
                                explanation=t("c243.fixed_last", ui), user_impact=t("impact.review", ui))
        if kind == "hidden_focus":
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="medium", excerpt=excerpt,
                                explanation=t("c243.hidden_focus", ui, name=name), user_impact=t("c243.impact_hidden", ui))
        return None

    # -- 4. the closed question ----------------------------------------------------------------------------
    SYSTEM = (
        "You check WCAG 2.1 success criterion 2.4.3 Focus Order for ONE part of a page where the keyboard focus "
        "order differs from the order in which things are shown. `focus_order` lists the focusable elements "
        "(label or text) in the order the Tab key reaches them; `visual_order` lists them as they are shown.\n"
        "effect:\n"
        "- breaks: the focus order separates things that belong together, or reaches an action before the "
        "information or fields it depends on\n"
        "- independent: the parts reached in another order are independent blocks; nothing that belongs "
        "together is separated\n"
        "- preserves: the focus order is still a logical sequence for this content\n"
        "- other: unsure\n"
        "quote: the label of one element whose position differs, copied exactly."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        # ui_lang is deliberately unused: prompts are identical for every UI language.
        return self.task(system=self.system_prompt(self.SYSTEM, c), element={"component": "focus sequence"},
                         context=c.context, question="Does this focus order preserve meaning and operability?",
                         schema=category_schema(EFFECTS), max_tokens=140)

    # -- 5. interpretation -----------------------------------------------------------------------------------
    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        cat = answer.get("category", "other")
        outcome = EFFECT_OUTCOME.get(cat, "cantTell")
        key = {"breaks": "c243.apertus_breaks", "independent": "c243.apertus_independent",
               "preserves": "c243.apertus_preserves"}.get(cat, "c243.apertus_unsure")
        impact = {"failed": t("c243.impact", ui), "passed": t("c243.impact_ok", ui)}.get(outcome, t("impact.review", ui))
        fix = None
        if outcome == "failed":
            fix = t("c243.fix_tabindex" if c.extra.get("kind") == "ask_tabindex" else "c243.fix_order", ui)
        return self.finding(c, outcome=outcome, source="apertus",
                            confidence=answer.get("confidence", "low") if outcome in ("failed", "passed") else "low",
                            excerpt=self.model_excerpt(c, answer, outcome), explanation=t(key, ui), user_impact=impact,
                            fix_hint=fix, reason=answer.get("reason"), reason_code=f"apertus_{cat}")


CHECK = FocusOrder
