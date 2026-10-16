"""2.2.2 Pause, Stop, Hide, level A. The closest ACT rule, efbfc7 (text content that
changes automatically can be paused, stopped or hidden), is a proposed rule and is not
claimed (findings carry no ACT id).

Facts (code). All live work happens in ONE ISOLATED, GUARDED CLONE of the audited page
(c_2_4_3.Clone: a new browser context with the same viewport and network policy; every
non-GET/HEAD request and every new top-level navigation is aborted unless its origin is
allow-listed; window.open is stubbed), with Playwright's fake clock installed before the
page scripts run: timers are fast-forwarded (2 × 6 s of page time) in a fraction of a
second of real time, so a 5-second carousel is observed without waiting. The clone is
reloaded (GET) for each test. Bounded: ≤ 10 components, ≤ 4 controls tested (each "still
moving" result is repeated once), at most 25 s and a quarter of the time left before
the scan deadline (page.remaining()).
  * motion: CSS animations in effect right after load with their total duration
    (document.getAnimations(): infinite or > 5 s = long), <marquee>/<blink>, and
    scripted changes: elements whose text, scroll position, class, inline style,
    hidden state or image source change in EVERY 6-second interval. Changes grouped
    into components (nearest landmark-like ancestor). Text-only changes = auto-updating.
  * parallel content: other page text besides the component (≥ 200 characters).
  * controls in, next to, or aria-controls-linked to the component, classified by a
    DE/FR/IT/EN stem lexicon: pause/stop, hide/close, navigation (previous/next/
    numbers/dots), settings elsewhere, unknown. Submit/reset buttons and every button
    that belongs to a form are never candidates.
  * control test, ONLY on the bundled demo and the evaluation servers (allow_form_submit,
    the same gate as the form probe): the control is clicked, the pointer moved away and
    the focus removed (hover/focus-pause does not count as a pause), 12 s of page time
    pass: is the component still moving? On any other site nothing is clicked.
  * reduced motion: the clone reloaded with prefers-reduced-motion: reduce.

Cascade (per component)
  every animation ends within 5 s                         → passed (heuristic, G11/G152)
  nothing else on the page (loading indicator alone)      → passed (heuristic, not in parallel)
  moving content without text (decoration)                → cantTell (heuristic)
  a control was clicked and the motion stopped / hid      → passed (heuristic, verified, G4/G186)
  motion stops only under prefers-reduced-motion          → cantTell (heuristic, mechanism disputed)
  only a link to a settings page elsewhere                → cantTell (heuristic, not verifiable)
  select / checkbox / unknown-named controls not tested   → Apertus (text): "Which control lets the
      user pause, stop or hide this content?" mechanism: pause_or_stop | hide | frequency |
      elsewhere | none → passed (demo/eval) or cantTell (external: not tested) | … | cantTell | failed
  pause/stop/hide control on an external site             → cantTell (heuristic, not tested on external sites)
  click test gave different results twice                 → cantTell (heuristic)
  a pause/stop/hide control, clicked twice, did NOT stop  → failed (heuristic, medium)
  no control, or only navigation controls                 → failed (heuristic, F16/F47/F50)

"Essential" motion is never assumed: the model is not asked about it and code never
passes motion as essential. Limits: canvas/WebGL/video motion and animated GIF frames
are not observed (video autoplay is 1.4.2/2.2.2 human review); motion that starts on
scroll or hover is not triggered; flashing (2.3.1) is out of scope.
"""

from __future__ import annotations

import logging
import re
import time
from pathlib import Path

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

log = logging.getLogger(__name__)

PROMPT_VERSION = "2.2.2/v1"
JS = (Path(__file__).resolve().parents[1] / "capture" / "js" / "c_2_2_2.js").read_text(encoding="utf-8")
MECHANISMS = ["pause_or_stop", "hide", "frequency", "elsewhere", "none"]
MECHANISM_OUTCOME = {"pause_or_stop": "passed", "hide": "passed", "frequency": "passed", "elsewhere": "cantTell",
                     "none": "failed"}
OBSERVE_MS = 6000  # page time per observation interval (fake clock)
FIVE_S = 5000
MIN_PARALLEL_TEXT = 200
MAX_COMPONENTS = 10
MAX_TESTS = 4
LIVE_BUDGET_S = 25.0

# Control lexicon (stems, DE · FR · IT · EN), written for this module.
PAUSE = re.compile(
    r"\b(paus\w*|anhalt\w*|stopp\w*|beend\w*|einfrier\w*|deaktivier\w*|ausschalt\w*"
    r"|arr[eê]t\w*|stop\w*|suspend\w*|d[ée]sactiv\w*|figer"
    r"|ferma(re)?|interromp\w*|arresta\w*|sospend\w*|disattiv\w*|blocca\w*"
    r"|freez\w*|halt|disabl\w*)\b|\b(turn|switch)\s+off\b|^\s*(⏸|■|❚❚|\|\|)\s*$",
    re.IGNORECASE)
HIDE = re.compile(
    r"\b(ausblend\w*|schlie(ss|ß)\w*|verberg\w*|versteck\w*|masquer|ferm(er|ez)|cacher"
    r"|nascond\w*|chiud\w*|hide\w*|close\w*|dismiss\w*)\b|^\s*[×✕✖xX]\s*$", re.IGNORECASE)
NAV = re.compile(
    r"\b(zur[üu]ck|weiter|vorherig\w*|n[äa]chst\w*|pr[ée]c[ée]dent\w*|suivant\w*|retour|precedent\w*|successiv\w*"
    r"|avanti|indietro|prev\w*|next|back|forward)\b|^\s*[‹›«»<>←→◀▶❮❯]+\s*$|^\s*\d+\s*$"
    r"|\b(slide|folie|diapositive|immagine|bild|image)\s*\d+", re.IGNORECASE)
SETTINGS = re.compile(r"\b(animation\w*|bewegung\w*|mouvement\w*|moviment\w*|motion|einstellung\w*|r[ée]glage\w*"
                      r"|pr[ée]f[ée]renc\w*|preferenz\w*|impostazion\w*|setting\w*)\b", re.IGNORECASE)

register({
    "c222.short": {
        "en": "The animation stops by itself within 5 seconds.",
        "de": "Die Animation endet von selbst innerhalb von 5 Sekunden.",
        "fr": "L'animation s'arrête d'elle-même en moins de 5 secondes.",
        "it": "L'animazione si ferma da sola entro 5 secondi.",
    },
    "c222.alone": {
        "en": "The moving content is the only content of the page; nothing is presented next to it.",
        "de": "Der bewegte Inhalt ist der einzige Inhalt der Seite; daneben wird nichts angezeigt.",
        "fr": "Le contenu en mouvement est le seul contenu de la page ; rien n'est présenté à côté.",
        "it": "Il contenuto in movimento è l'unico contenuto della pagina; accanto non c'è altro.",
    },
    "c222.decorative": {
        "en": "Content without text moves for more than 5 seconds. Whether decorative motion needs a pause control is debated.",
        "de": "Inhalt ohne Text bewegt sich länger als 5 Sekunden. Ob dekorative Bewegung eine Pause-Möglichkeit braucht, ist umstritten.",
        "fr": "Un contenu sans texte bouge plus de 5 secondes. La nécessité d'une pause pour un mouvement décoratif est débattue.",
        "it": "Un contenuto senza testo si muove per più di 5 secondi. Se un movimento decorativo richieda una pausa è controverso.",
    },
    "c222.verified": {
        "en": "The control \"{control}\" stopped the motion in our test (clicked, pointer moved away).",
        "de": "Das Bedienelement «{control}» hat die Bewegung in unserem Test gestoppt (geklickt, Mauszeiger danach entfernt).",
        "fr": "Le contrôle « {control} » a arrêté le mouvement lors de notre test (clic, puis pointeur éloigné).",
        "it": "Il comando «{control}» ha fermato il movimento nel nostro test (clic, poi puntatore allontanato).",
    },
    "c222.reduced_only": {
        "en": "The motion stops only when the browser asks for reduced motion; the page itself offers no control. Whether that counts as a mechanism is disputed.",
        "de": "Die Bewegung stoppt nur, wenn der Browser reduzierte Bewegung verlangt; die Seite selbst bietet kein Bedienelement. Ob das als Mechanismus gilt, ist umstritten.",
        "fr": "Le mouvement ne s'arrête que si le navigateur demande un mouvement réduit ; la page n'offre aucun contrôle. Cela compte-t-il comme mécanisme ? Les avis divergent.",
        "it": "Il movimento si ferma solo se il browser chiede movimento ridotto; la pagina non offre alcun comando. Se ciò valga come meccanismo è controverso.",
    },
    "c222.settings_link": {
        "en": "The only control is a link to settings elsewhere (\"{control}\"); its effect cannot be checked on this page.",
        "de": "Das einzige Bedienelement ist ein Link zu Einstellungen an anderer Stelle («{control}»); seine Wirkung lässt sich auf dieser Seite nicht prüfen.",
        "fr": "Le seul contrôle est un lien vers des réglages ailleurs (« {control} ») ; son effet ne peut pas être vérifié sur cette page.",
        "it": "L'unico comando è un link a impostazioni altrove («{control}»); il suo effetto non è verificabile su questa pagina.",
    },
    "c222.not_tested_external": {
        "en": "Not tested on external sites: Klar. clicks controls only on the demo and test pages. A person must check that \"{control}\" pauses or stops this moving content.",
        "de": "Auf externen Websites nicht getestet: Klar. klickt Bedienelemente nur auf der Demo-Website und auf Testseiten. Eine Person muss prüfen, ob «{control}» diesen bewegten Inhalt anhält oder stoppt.",
        "fr": "Non testé sur les sites externes : Klar. ne clique sur des contrôles que sur la démo et les pages de test. Une personne doit vérifier que « {control} » met en pause ou arrête ce contenu en mouvement.",
        "it": "Non verificato sui siti esterni: Klar. clicca sui comandi solo sulla demo e sulle pagine di test. Una persona deve verificare che «{control}» metta in pausa o fermi questo contenuto in movimento.",
    },
    "c222.inconclusive": {
        "en": "Two tests of the control \"{control}\" gave different results. A person must check whether it stops the motion.",
        "de": "Zwei Tests des Bedienelements «{control}» ergaben unterschiedliche Ergebnisse. Eine Person muss prüfen, ob es die Bewegung stoppt.",
        "fr": "Deux tests du contrôle « {control} » ont donné des résultats différents. Une personne doit vérifier s'il arrête le mouvement.",
        "it": "Due test del comando «{control}» hanno dato risultati diversi. Una persona deve verificare se ferma il movimento.",
    },
    "c222.apertus_untested": {
        "en": "Apertus judged that the control \"{control}\" lets users {what}, but on external sites Klar. does not click it. A person must check it.",
        "de": "Apertus beurteilt, dass das Bedienelement «{control}» erlaubt, {what}; auf externen Websites klickt Klar. es aber nicht. Eine Person muss es prüfen.",
        "fr": "Selon Apertus, le contrôle « {control} » permet de {what}, mais sur les sites externes Klar. ne clique pas dessus. Une personne doit le vérifier.",
        "it": "Secondo Apertus il comando «{control}» permette di {what}, ma sui siti esterni Klar. non lo clicca. Una persona deve verificarlo.",
    },
    "c222.ineffective": {
        "en": "The control \"{control}\" did not stop the motion in two tests (clicked, pointer moved away).",
        "de": "Das Bedienelement «{control}» hat die Bewegung in zwei Tests nicht gestoppt (geklickt, Mauszeiger danach entfernt).",
        "fr": "Le contrôle « {control} » n'a pas arrêté le mouvement lors de deux tests (clic, puis pointeur éloigné).",
        "it": "Il comando «{control}» non ha fermato il movimento in due test (clic, poi puntatore allontanato).",
    },
    "c222.no_control": {
        "en": "This content {how} for more than 5 seconds and there is no control to pause, stop or hide it.",
        "de": "Dieser Inhalt {how} länger als 5 Sekunden, und es gibt kein Bedienelement, um ihn anzuhalten, zu stoppen oder auszublenden.",
        "fr": "Ce contenu {how} plus de 5 secondes et aucun contrôle ne permet de le mettre en pause, de l'arrêter ou de le masquer.",
        "it": "Questo contenuto {how} per più di 5 secondi e non c'è alcun comando per metterlo in pausa, fermarlo o nasconderlo.",
    },
    "c222.how.moves": {"en": "moves", "de": "bewegt sich", "fr": "bouge", "it": "si muove"},
    "c222.how.updates": {"en": "updates by itself", "de": "aktualisiert sich selbst", "fr": "se met à jour tout seul",
                         "it": "si aggiorna da solo"},
    "c222.apertus_mechanism": {
        "en": "Apertus judged that the control \"{control}\" lets users {what} (not tested by clicking).",
        "de": "Apertus beurteilt, dass das Bedienelement «{control}» erlaubt, {what} (nicht durch Klicken getestet).",
        "fr": "Selon Apertus, le contrôle « {control} » permet de {what} (non testé par un clic).",
        "it": "Secondo Apertus il comando «{control}» permette di {what} (non verificato con un clic).",
    },
    "c222.what.pause_or_stop": {"en": "pause or stop the motion", "de": "die Bewegung anzuhalten oder zu stoppen",
                                "fr": "mettre en pause ou arrêter le mouvement", "it": "mettere in pausa o fermare il movimento"},
    "c222.what.hide": {"en": "hide the moving content", "de": "den bewegten Inhalt auszublenden",
                       "fr": "masquer le contenu en mouvement", "it": "nascondere il contenuto in movimento"},
    "c222.what.frequency": {"en": "turn the automatic updates off", "de": "die automatischen Aktualisierungen abzuschalten",
                            "fr": "désactiver les mises à jour automatiques", "it": "disattivare gli aggiornamenti automatici"},
    "c222.apertus_elsewhere": {
        "en": "Apertus judged that the only control leads to settings elsewhere; its effect cannot be checked on this page.",
        "de": "Apertus beurteilt, dass das einzige Bedienelement zu Einstellungen an anderer Stelle führt; die Wirkung lässt sich hier nicht prüfen.",
        "fr": "Selon Apertus, le seul contrôle mène à des réglages ailleurs ; son effet ne peut pas être vérifié ici.",
        "it": "Secondo Apertus l'unico comando porta a impostazioni altrove; il suo effetto non è verificabile qui.",
    },
    "c222.apertus_none": {
        "en": "Apertus judged that none of the controls next to this moving content pauses, stops or hides it.",
        "de": "Apertus beurteilt, dass sich dieser bewegte Inhalt mit keinem der Bedienelemente daneben anhalten, stoppen oder ausblenden lässt.",
        "fr": "Selon Apertus, aucun des contrôles proches de ce contenu en mouvement ne le met en pause, ne l'arrête ni ne le masque.",
        "it": "Secondo Apertus nessuno dei comandi vicini a questo contenuto in movimento lo mette in pausa, lo ferma o lo nasconde.",
    },
    "c222.apertus_unsure": {
        "en": "Apertus could not tell whether a control stops this moving content. A person must check it.",
        "de": "Apertus konnte nicht entscheiden, ob ein Bedienelement diesen bewegten Inhalt stoppt. Eine Person muss es prüfen.",
        "fr": "Apertus n'a pas pu décider si un contrôle arrête ce contenu en mouvement. Une personne doit le vérifier.",
        "it": "Apertus non ha potuto stabilire se un comando ferma questo contenuto in movimento. Una persona deve verificarlo.",
    },
    "c222.impact": {
        "en": "People with attention disorders are distracted, and people who read slowly or use screen magnifiers cannot follow content that keeps moving or changing.",
        "de": "Menschen mit Aufmerksamkeitsstörungen werden abgelenkt; wer langsam liest oder eine Bildschirmlupe nutzt, kann bewegtem oder wechselndem Inhalt nicht folgen.",
        "fr": "Les personnes ayant des troubles de l'attention sont distraites ; celles qui lisent lentement ou utilisent une loupe ne peuvent pas suivre un contenu qui bouge ou change.",
        "it": "Le persone con disturbi dell'attenzione vengono distratte; chi legge lentamente o usa un ingranditore non riesce a seguire contenuti che si muovono o cambiano.",
    },
    "c222.impact_ok": {
        "en": "Users can stop the motion, or it ends on its own, so it does not keep distracting them.",
        "de": "Die Bewegung lässt sich stoppen oder endet von selbst und lenkt daher nicht dauerhaft ab.",
        "fr": "Le mouvement peut être arrêté ou s'arrête seul ; il ne distrait donc pas en permanence.",
        "it": "Il movimento si può fermare o termina da solo, quindi non distrae in modo continuo.",
    },
    "c222.fix": {
        "en": "Add a visible pause button in or next to the moving content that stops it until the user restarts it.",
        "de": "Fügen Sie in oder neben dem bewegten Inhalt eine sichtbare Pause-Schaltfläche hinzu, die ihn stoppt, bis er wieder gestartet wird.",
        "fr": "Ajoutez dans ou à côté du contenu en mouvement un bouton pause visible qui l'arrête jusqu'à ce que l'utilisateur le relance.",
        "it": "Aggiungete nel contenuto in movimento o accanto un pulsante pausa visibile che lo ferma finché l'utente non lo riavvia.",
    },
})


def classify_control(ctrl: dict) -> str:
    name = ctrl.get("name") or ""
    href = (ctrl.get("href") or "").strip()
    if ctrl.get("type") in ("submit", "reset", "image") or (ctrl.get("in_form") and ctrl.get("tag") in ("button", "input")
                                                           and ctrl.get("type") not in ("checkbox", "radio")):
        return "excluded"  # never clicked: it could submit a form
    if ctrl.get("tag") == "a" and href and not href.startswith("#") and not href.lower().startswith("javascript:"):
        return "settings_link" if (PAUSE.search(name) or SETTINGS.search(name)) else "link"
    if ctrl.get("tag") == "select" or ctrl.get("type") in ("checkbox", "radio") or ctrl.get("tag") == "input":
        return "untestable"
    if PAUSE.search(name):
        return "pause"
    if HIDE.search(name):
        return "hide"
    if NAV.search(name) or not name.strip():
        return "nav"
    return "unknown"


class PauseStopHide(BaseCheck):
    criterion = "2.2.2"
    prompt_version = PROMPT_VERSION
    needs_vision = False  # text question; no image is ever sent
    max_candidates = MAX_COMPONENTS

    # -- 1. facts -----------------------------------------------------------------------------------
    def facts(self, page: CapturedPage) -> dict:
        pre = page.elements.get("c222")  # tests inject [facts] (a list, like every element collection)
        if isinstance(pre, list):
            pre = pre[0] if pre else None
        if pre is not None:
            return pre
        if page.live is None:
            return self.static_facts(page)
        try:
            return self.live_facts(page)
        except Exception as exc:
            log.info("2.2.2 live facts failed: %s", exc)
            return {"components": []}

    @staticmethod
    def static_facts(page: CapturedPage) -> dict:
        """No live page: <marquee>/<blink> only (no timing, no control test)."""
        from klar.checks.c_1_3_1 import _outer, parse_html

        comps = []
        root = parse_html(page.html)
        body_text = " ".join(root.text().split())
        for n in root.iter():
            if n.tag in ("marquee", "blink") and len(comps) < MAX_COMPONENTS:
                parent = n.parent
                controls = [{"selector": c.path(), "tag": c.tag, "type": c.attrs.get("type", ""),
                             "name": " ".join(c.text().split()) or c.attrs.get("aria-label", ""),
                             "href": c.attrs.get("href", ""), "options": [], "inside": False,
                             "in_form": any(a.tag == "form" for a in c.ancestors())}
                            for c in (parent.iter() if parent is not None else []) if c.tag in ("button", "a", "select")]
                text = " ".join(n.text().split())
                comps.append({"selector": n.path(), "html": _outer(n), "text": text, "lang": page.lang, "kind": "marquee",
                              "long": True, "has_text": bool(text), "parallel": len(body_text) - len(text) >= MIN_PARALLEL_TEXT,
                              "controls": controls, "tests": {}, "reduced_only": None, "interactive": False})
        return {"components": comps, "static": True}

    @staticmethod
    def _observe(tab) -> tuple[list[dict], list[dict], list[dict]]:
        from klar.capture.browser import js

        tab.evaluate(js(JS))
        anims = tab.evaluate("() => window.__k222.animations()") or []
        marq = tab.evaluate("() => window.__k222.marquees()") or []
        tab.evaluate("() => window.__k222.reset()")
        for k in range(3):
            if k:
                tab.clock.run_for(OBSERVE_MS)
            tab.evaluate("() => window.__k222.snapshot()")
        changes = tab.evaluate("() => window.__k222.changes()") or []
        return anims, marq, changes

    def live_facts(self, page: CapturedPage) -> dict:
        from klar.checks.c_2_4_3 import interaction_allowed, isolated_clone, remaining_budget

        budget = remaining_budget(page, LIVE_BUDGET_S)
        if budget < 3.0:
            return self.static_facts(page)
        deadline = time.monotonic() + budget
        interactive = interaction_allowed(page)
        comps: dict[str, dict] = {}
        with isolated_clone(page, clock=True, timeout_ms=int(min(8.0, budget) * 1000)) as clone:
            tab = clone.tab
            anims, marq, changes = self._observe(tab)
            for a in anims:
                if a.get("play_state") not in ("running", "pending"):
                    continue
                rec = comps.setdefault(a["component"], {"selector": a["component"], "kind": "css", "long": False,
                                                        "has_text": False, "anims": []})
                rec["anims"].append(a)
                rec["long"] = rec["long"] or a.get("end_ms", 0) < 0 or a.get("end_ms", 0) > FIVE_S
                rec["has_text"] = rec["has_text"] or bool(a.get("has_text"))
            for m in marq:
                rec = comps.setdefault(m["component"], {"selector": m["component"], "kind": "marquee", "long": True,
                                                        "has_text": False})
                rec.update(kind="marquee", long=True, has_text=rec["has_text"] or bool(m.get("has_text")))
            for ch in changes:
                rec = comps.setdefault(ch["component"], {"selector": ch["component"], "kind": "scripted", "long": True,
                                                         "has_text": False})
                rec["kind"] = "auto_update" if ch.get("text_only") and rec["kind"] != "css" else "scripted"
                rec["long"] = True
                rec["has_text"] = rec["has_text"] or bool(ch.get("has_text"))
            for sel in list(comps)[:MAX_COMPONENTS]:
                desc = tab.evaluate("s => window.__k222.describe(s)", sel) or {}
                comps[sel].update(html=desc.get("html", ""), text=desc.get("text", ""), lang=desc.get("lang"),
                                  parallel=desc.get("other_text", 0) >= MIN_PARALLEL_TEXT,
                                  controls=desc.get("controls", []), tests={}, reduced_only=None,
                                  interactive=interactive)
            comps = {k: v for k, v in list(comps.items())[:MAX_COMPONENTS] if "controls" in v}

            # control tests (demo / evaluation only): click, pointer away, focus dropped, 12 s of page time
            if interactive:
                left = MAX_TESTS
                for sel, rec in comps.items():
                    if not rec["long"]:
                        continue
                    for ctrl in [c for c in rec["controls"] if classify_control(c) in ("pause", "hide", "unknown")][:2]:
                        if left <= 0 or time.monotonic() > deadline:
                            break
                        left -= 1
                        result = self._test_control(clone, sel, ctrl)
                        if result == "moving":  # a failure needs a second, identical result
                            again = self._test_control(clone, sel, ctrl) if time.monotonic() <= deadline else None
                            result = "moving" if again == "moving" else "inconclusive"
                        rec["tests"][ctrl["selector"]] = result or "inconclusive"

            # reduced motion: does the motion stop when the browser asks for it?
            open_ = [s for s, r in comps.items() if r["long"] and "stopped" not in r["tests"].values()]
            if open_ and time.monotonic() <= deadline:
                try:
                    clone.reload(reduced_motion="reduce")
                    anims, marq, changes = self._observe(tab)
                    still = {a["component"] for a in anims if a.get("end_ms", 0) < 0 or a.get("end_ms", 0) > FIVE_S}
                    still |= {m["component"] for m in marq} | {c["component"] for c in changes}
                    for s in open_:
                        comps[s]["reduced_only"] = s not in still
                except Exception as exc:
                    log.info("2.2.2 reduced-motion check failed: %s", exc)
        return {"components": list(comps.values())}

    def _test_control(self, clone, comp: str, ctrl: dict) -> str | None:
        """"stopped" (motion stopped or the component was hidden), "moving", or None (test failed).
        Runs in the guarded clone, reloaded first; only called when interaction is allowed."""
        from klar.capture.browser import js

        tab = clone.tab
        try:
            clone.reload()
            url = tab.url
            tab.evaluate(js(JS))
            tab.locator(ctrl["selector"]).first.click(timeout=3000, no_wait_after=True)
            tab.mouse.move(1, 1)
            tab.evaluate("() => { if (document.activeElement && document.activeElement.blur) document.activeElement.blur(); }")
            if tab.url != url:
                return None
            anims, marq, changes = self._observe(tab)
            if not tab.evaluate("s => window.__k222.visible(s)", comp):
                return "stopped"
            moving = tab.evaluate("s => window.__k222.cssMoving(s)", comp)
            moving = moving or any(m["component"] == comp for m in marq) or any(c["component"] == comp for c in changes)
            return "moving" if moving else "stopped"
        except Exception as exc:
            log.info("2.2.2 control test %s failed: %s", ctrl.get("selector"), exc)
            return None

    # -- 2. candidates -----------------------------------------------------------------------------------
    def candidates(self, page: CapturedPage) -> list[Candidate]:
        out: list[Candidate] = []
        for rec in self.facts(page).get("components", [])[: self.max_candidates]:
            interactive = rec.get("interactive", True)
            kinds = {c["selector"]: classify_control(c) for c in rec.get("controls") or []}
            controls = [c for c in rec.get("controls") or [] if kinds[c["selector"]] != "excluded"]
            tests = {k: {True: "stopped", False: "moving"}.get(v, v) for k, v in (rec.get("tests") or {}).items()}

            def of(*want: str, test=None) -> list[dict]:
                return [c for c in controls if kinds[c["selector"]] in want and tests.get(c["selector"]) == test]

            stopped = [c for c in controls if tests.get(c["selector"]) == "stopped"]
            moving = of("pause", "hide", test="moving")
            inconclusive = of("pause", "hide", "unknown", test="inconclusive")
            settings = of("settings_link")
            untestable = of("untestable")
            unknown_untested = of("unknown")
            lexicon_untested = of("pause", "hide")
            if not rec.get("long"):
                kind = "short"
            elif rec.get("parallel") is False:
                kind = "alone"
            elif not rec.get("has_text"):
                kind = "decorative"
            elif stopped:
                kind = "verified"
            elif rec.get("reduced_only"):
                kind = "reduced_only"
            elif lexicon_untested and not interactive:
                kind = "not_tested_external"  # a pause control is there; on external sites it is never clicked
            elif inconclusive:
                kind = "inconclusive"
            elif untestable or unknown_untested or lexicon_untested:
                kind = "ask"
            elif settings:
                kind = "settings_link"
            elif moving:
                kind = "ineffective"
            else:
                kind = "no_control"
            control = (stopped or lexicon_untested or inconclusive or moving or settings or [None])[0]
            asked = untestable + unknown_untested + lexicon_untested + settings
            shown = (asked if kind == "ask" else controls)[:8]
            names = [c.get("name") or "(unnamed)" for c in shown]
            context = {}
            if kind == "ask":
                context = {"content": (rec.get("text") or "")[:400],
                           "controls": " ; ".join(
                               (c.get("name") or "(unnamed)") + (f" [options: {', '.join(c['options'])}]" if c.get("options") else "")
                               + (" [link]" if c.get("tag") == "a" else "") for c in shown)}
            text = (rec.get("text") or "") + (" | " + " | ".join(names) if names else "")
            out.append(self.candidate(page, selector=rec["selector"], html=rec.get("html", ""), text=text.strip(" |"),
                                      context=context, lang=rec.get("lang") or page.lang, kind=kind,
                                      motion=rec.get("kind", "css"), control=(control or {}).get("name", ""),
                                      interactive=interactive))
        return out

    # -- 3. deterministic decisions ------------------------------------------------------------------------
    def decide(self, c: Candidate) -> Finding | None:
        kind, ui = c.extra.get("kind"), self.ui_lang
        control = c.extra.get("control", "")
        cx = control if control and control in c.text else None
        if kind in ("short", "alone", "verified"):
            return self.finding(c, outcome="passed", source="heuristic", confidence="high" if kind == "verified" else "medium",
                                excerpt=cx, explanation=t(f"c222.{kind}", ui, control=control),
                                user_impact=t("c222.impact_ok", ui))
        if kind in ("decorative", "reduced_only", "settings_link", "not_tested_external", "inconclusive"):
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="medium", excerpt=cx,
                                explanation=t(f"c222.{kind}", ui, control=control), user_impact=t("impact.review", ui))
        if kind == "ineffective":
            return self.finding(c, outcome="failed", source="heuristic", confidence="medium", excerpt=cx,
                                explanation=t("c222.ineffective", ui, control=control), user_impact=t("c222.impact", ui),
                                fix_hint=t("c222.fix", ui))
        if kind == "no_control":
            how = t("c222.how.updates" if c.extra.get("motion") == "auto_update" else "c222.how.moves", ui)
            return self.finding(c, outcome="failed", source="heuristic", confidence="high",
                                explanation=t("c222.no_control", ui, how=how), user_impact=t("c222.impact", ui),
                                fix_hint=t("c222.fix", ui))
        return None

    # -- 4. the closed question ----------------------------------------------------------------------------------
    SYSTEM = (
        "You check WCAG 2.1 success criterion 2.2.2 Pause, Stop, Hide for ONE component that moves, scrolls, "
        "blinks or updates by itself for more than five seconds, next to other content. `content` is its text; "
        "`controls` lists the controls in or next to it (name; options of a select; [link] for a link).\n"
        "mechanism:\n"
        "- pause_or_stop: a control pauses or stops the motion or the updates until the user restarts them\n"
        "- hide: a control hides or closes the moving component\n"
        "- frequency: a control sets how often the content updates and offers a manual or never option\n"
        "- elsewhere: the only such control leads to settings on another page\n"
        "- none: no control does any of this (previous/next, slide numbers and other controls do not count)\n"
        "quote: the name of the control you mean, copied exactly; for none, a few words of `content`."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        # ui_lang is deliberately unused: prompts are identical for every UI language.
        motion = "updates" if c.extra.get("motion") == "auto_update" else "moves"
        return self.task(system=self.system_prompt(self.SYSTEM, c), element={"behaviour": motion},
                         context=c.context, question="Which control lets the user pause, stop or hide this content?",
                         schema=category_schema(MECHANISMS), max_tokens=140)

    # -- 5. interpretation -----------------------------------------------------------------------------------------
    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        cat = answer.get("category", "none")
        outcome = MECHANISM_OUTCOME.get(cat, "cantTell")
        quote = (answer.get("quote") or "").strip()
        conf = answer.get("confidence", "low")
        common = dict(source="apertus", reason=answer.get("reason"), reason_code=f"apertus_{cat}",
                      excerpt=self.model_excerpt(c, answer, outcome))
        if outcome == "passed" and not c.extra.get("interactive", True):
            return self.finding(c, outcome="cantTell", confidence="low",
                                explanation=t("c222.apertus_untested", ui, control=quote, what=t(f"c222.what.{cat}", ui)),
                                user_impact=t("impact.review", ui), **common)
        if outcome == "passed":
            return self.finding(c, outcome="passed", confidence="medium" if conf == "high" else conf,
                                explanation=t("c222.apertus_mechanism", ui, control=quote, what=t(f"c222.what.{cat}", ui)),
                                user_impact=t("c222.impact_ok", ui), **common)
        if outcome == "failed":
            return self.finding(c, outcome="failed", confidence=conf, explanation=t("c222.apertus_none", ui),
                                user_impact=t("c222.impact", ui), fix_hint=t("c222.fix", ui), **common)
        key = "c222.apertus_elsewhere" if cat == "elsewhere" else "c222.apertus_unsure"
        return self.finding(c, outcome="cantTell", confidence="low", explanation=t(key, ui),
                            user_impact=t("impact.review", ui), **common)


CHECK = PauseStopHide
