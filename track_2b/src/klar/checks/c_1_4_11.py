"""1.4.11 Non-text Contrast, level AA (vision for graphics only). No ACT rule maps
to 1.4.11; techniques G195, G207, G209 and failure F78.

Measured in CODE (capture/js/c_1_4_11_ui.js + checks/colour.py), 3:1 never rounded:
  1. Text inputs, selects, textareas and custom (appearance:none or ARIA) checkboxes,
     radios and switches: the boundary is visible when ANY of border vs the colour
     outside, border vs the field's fill, or fill vs the colour outside reaches 3:1
     (PROTOCOL 1.4.11/F1, F3). Below → failed (rule); disabled → passed (exemption,
     T1). Native checkboxes and radios are drawn by the browser: exempt, skipped. A
     field with no border and no fill difference has no boundary to measure: skipped.
  2. Controls without visible text whose only identifying visual is an icon: the
     dominant colour of the inline-SVG shapes (or of an icon-font glyph) against the
     control's background → failed / passed (rule, G207, PROTOCOL F2). Icons drawn
     with a gradient → cantTell (C2). <img> or background-image icons: the dominant
     non-background colour of the screenshot crop (heuristic).
  3. Author focus styles, read from the stylesheets (CSSOM, nothing is focused): the
     outline / box-shadow / border colour of a :focus or :focus-visible rule against
     the colour around the control → failed / passed (heuristic, G195 / F78, F5).
     Removing the outline without a replacement is 2.4.7's business: skipped here.
  4. Graphics ≥ 100×60 px outside controls (charts, maps, diagrams): colours of the
     SVG shapes, or the flat palette of the crop for <img>/<canvas> (photos skipped),
     against the graphic's background. Every part ≥ 3:1 → passed (heuristic).

Asked to APERTUS (vision, crop) ONLY for graphics with parts below 3:1: is the
low-contrast part required to understand the content?
  category: required → failed (F4) · labelled → passed (T2) · decorative → passed (T4)
            · essential_scale → passed (T5, heat maps) · unclear → cantTell (C1)
At most 6 crops per page (largest first); the rest → cantTell.
No vision backend → cantTell "vision backend required" (pipeline, needs_vision).

Passed findings: at most 3 per colour pair. Limits: hover and pressed states are
not measured; focus styles from cross-origin stylesheets, inline style changes made
by scripts and :focus-within are not seen; the winning :focus rule is the LAST one
in document order (specificity and !important are not resolved). Nothing is focused,
by design: focus handlers could change the shared live page that the other checks
measure. Contrast between adjacent chart parts is left to the model; the colour
around an outline is measured on one side.
"""

from __future__ import annotations

import hashlib

from klar.capture.page import CapturedPage
from klar.checks import colour as C
from klar.checks.base import BaseCheck, category_schema
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "1.4.11/v1"
VISION_CAP = 6
GRAPHIC_SAMPLE_CAP = 12
PASSES_PER_PAIR = 3
CATEGORIES = ["required", "labelled", "decorative", "essential_scale", "unclear"]
CATEGORY_OUTCOME = {"required": "failed", "labelled": "passed", "decorative": "passed", "essential_scale": "passed",
                    "unclear": "cantTell"}

register({
    "c1411.input_fail": {
        "en": "The boundary of this field is hard to see: the best contrast of its border or fill against the surroundings is {ratio} (3:1 needed; border {border}, fill {fill}, outside {outside}).",
        "de": "Der Rand dieses Feldes ist schwer zu erkennen: Der beste Kontrast von Rahmen oder Füllung zur Umgebung beträgt {ratio} (nötig sind 3:1; Rahmen {border}, Füllung {fill}, aussen {outside}).",
        "fr": "Le contour de ce champ est peu visible : le meilleur contraste de sa bordure ou de son fond avec l'entourage est de {ratio} (3:1 requis ; bordure {border}, fond {fill}, extérieur {outside}).",
        "it": "Il bordo di questo campo è poco visibile: il miglior contrasto del bordo o dello sfondo rispetto all'ambiente è {ratio} (serve 3:1; bordo {border}, sfondo {fill}, esterno {outside}).",
    },
    "c1411.input_pass": {
        "en": "The boundary of this field has {ratio} against its surroundings (3:1 needed).",
        "de": "Der Rand dieses Feldes hat {ratio} Kontrast zur Umgebung (nötig sind 3:1).",
        "fr": "Le contour de ce champ atteint {ratio} par rapport à son entourage (3:1 requis).",
        "it": "Il bordo di questo campo ha {ratio} rispetto all'ambiente (serve 3:1).",
    },
    "c1411.inactive": {
        "en": "Inactive (disabled) component: its low contrast ({ratio}) is exempt from 1.4.11.",
        "de": "Inaktives (deaktiviertes) Bedienelement: Sein geringer Kontrast ({ratio}) ist von 1.4.11 ausgenommen.",
        "fr": "Composant inactif (désactivé) : son faible contraste ({ratio}) est exempté du critère 1.4.11.",
        "it": "Componente inattivo (disattivato): il suo basso contrasto ({ratio}) è esente dal criterio 1.4.11.",
    },
    "c1411.icon_fail": {
        "en": "This control has no visible text and its icon has only {ratio} against the background (3:1 needed): {fg} on {bg}.",
        "de": "Dieses Bedienelement hat keinen sichtbaren Text und sein Symbol hat nur {ratio} Kontrast zum Hintergrund (nötig sind 3:1): {fg} auf {bg}.",
        "fr": "Ce contrôle n'a pas de texte visible et son icône n'atteint que {ratio} par rapport au fond (3:1 requis) : {fg} sur {bg}.",
        "it": "Questo controllo non ha testo visibile e la sua icona ha solo {ratio} rispetto allo sfondo (serve 3:1): {fg} su {bg}.",
    },
    "c1411.icon_pass": {
        "en": "The icon of this control has {ratio} against the background (3:1 needed): {fg} on {bg}.",
        "de": "Das Symbol dieses Bedienelements hat {ratio} Kontrast zum Hintergrund (nötig sind 3:1): {fg} auf {bg}.",
        "fr": "L'icône de ce contrôle atteint {ratio} par rapport au fond (3:1 requis) : {fg} sur {bg}.",
        "it": "L'icona di questo controllo ha {ratio} rispetto allo sfondo (serve 3:1): {fg} su {bg}.",
    },
    "c1411.icon_gradient": {
        "en": "The icon of this control is drawn with a gradient: part of it may be below 3:1. Whether it stays recognisable must be checked by eye.",
        "de": "Das Symbol dieses Bedienelements ist mit einem Farbverlauf gezeichnet: Ein Teil davon liegt eventuell unter 3:1. Ob es erkennbar bleibt, muss eine Person prüfen.",
        "fr": "L'icône de ce contrôle est dessinée avec un dégradé : une partie peut être sous 3:1. Une personne doit vérifier si elle reste reconnaissable.",
        "it": "L'icona di questo controllo è disegnata con una sfumatura: una parte può essere sotto 3:1. Una persona deve verificare se resta riconoscibile.",
    },
    "c1411.focus_fail": {
        "en": "The author's focus indicator ({indicator}, {fg}) has only {ratio} against the colour around the control ({bg}); 3:1 is needed.",
        "de": "Der gestaltete Fokusindikator ({indicator}, {fg}) hat nur {ratio} Kontrast zur Farbe um das Bedienelement ({bg}); nötig sind 3:1.",
        "fr": "L'indicateur de focus défini par l'auteur ({indicator}, {fg}) n'atteint que {ratio} par rapport à la couleur autour du contrôle ({bg}) ; 3:1 requis.",
        "it": "L'indicatore di focus definito dall'autore ({indicator}, {fg}) ha solo {ratio} rispetto al colore intorno al controllo ({bg}); serve 3:1.",
    },
    "c1411.focus_pass": {
        "en": "The author's focus indicator ({indicator}, {fg}) has {ratio} against the colour around the control ({bg}).",
        "de": "Der gestaltete Fokusindikator ({indicator}, {fg}) hat {ratio} Kontrast zur Farbe um das Bedienelement ({bg}).",
        "fr": "L'indicateur de focus défini par l'auteur ({indicator}, {fg}) atteint {ratio} par rapport à la couleur autour du contrôle ({bg}).",
        "it": "L'indicatore di focus definito dall'autore ({indicator}, {fg}) ha {ratio} rispetto al colore intorno al controllo ({bg}).",
    },
    "c1411.graphic_pass": {
        "en": "All graphical parts measured in this graphic have at least {ratio} against its background (3:1 needed).",
        "de": "Alle gemessenen grafischen Teile dieser Grafik haben mindestens {ratio} Kontrast zum Hintergrund (nötig sind 3:1).",
        "fr": "Toutes les parties graphiques mesurées de ce graphique atteignent au moins {ratio} par rapport au fond (3:1 requis).",
        "it": "Tutte le parti grafiche misurate di questo grafico hanno almeno {ratio} rispetto allo sfondo (serve 3:1).",
    },
    "c1411.facts": {
        "en": "{low} of {n} colours below 3:1 against the background, lowest {ratio}",
        "de": "{low} von {n} Farben unter 3:1 zum Hintergrund, tiefster Wert {ratio}",
        "fr": "{low} couleurs sur {n} sous 3:1 par rapport au fond, minimum {ratio}",
        "it": "{low} colori su {n} sotto 3:1 rispetto allo sfondo, minimo {ratio}",
    },
    "c1411.apertus_required": {
        "en": "Apertus: a low-contrast part of this graphic is needed to understand it, and the text does not give the same information ({facts}).",
        "de": "Apertus: Ein kontrastarmer Teil dieser Grafik ist zum Verständnis nötig, und der Text gibt nicht dieselbe Information ({facts}).",
        "fr": "Apertus : une partie peu contrastée de ce graphique est nécessaire pour le comprendre, et le texte ne donne pas la même information ({facts}).",
        "it": "Apertus: una parte poco contrastata di questo grafico è necessaria per capirlo e il testo non dà la stessa informazione ({facts}).",
    },
    "c1411.apertus_labelled": {
        "en": "Apertus: the low-contrast parts are also given as text (labels or values) in or next to the graphic, so they are not required ({facts}).",
        "de": "Apertus: Die kontrastarmen Teile sind auch als Text (Beschriftungen oder Werte) in oder neben der Grafik angegeben und daher nicht nötig ({facts}).",
        "fr": "Apertus : les parties peu contrastées sont aussi données sous forme de texte (étiquettes ou valeurs) dans le graphique ou à côté ; elles ne sont donc pas nécessaires ({facts}).",
        "it": "Apertus: le parti poco contrastate sono date anche come testo (etichette o valori) nel grafico o accanto, quindi non sono necessarie ({facts}).",
    },
    "c1411.apertus_decorative": {
        "en": "Apertus: this graphic is decorative and conveys no information ({facts}).",
        "de": "Apertus: Diese Grafik ist dekorativ und vermittelt keine Information ({facts}).",
        "fr": "Apertus : ce graphique est décoratif et ne transmet aucune information ({facts}).",
        "it": "Apertus: questo grafico è decorativo e non trasmette informazioni ({facts}).",
    },
    "c1411.apertus_essential_scale": {
        "en": "Apertus: the colours form a measurement scale (such as a heat map), where low contrast between steps is essential ({facts}).",
        "de": "Apertus: Die Farben bilden eine Messskala (etwa eine Heatmap), bei der geringer Kontrast zwischen den Stufen wesentlich ist ({facts}).",
        "fr": "Apertus : les couleurs forment une échelle de mesure (comme une carte de chaleur), où le faible contraste entre les paliers est essentiel ({facts}).",
        "it": "Apertus: i colori formano una scala di misura (come una mappa di calore), in cui il basso contrasto tra i livelli è essenziale ({facts}).",
    },
    "c1411.apertus_unclear": {
        "en": "Apertus: whether the low-contrast part is needed depends on the user's task; the text gives only part of its information ({facts}). A person must decide.",
        "de": "Apertus: Ob der kontrastarme Teil nötig ist, hängt von der Aufgabe ab; der Text gibt nur einen Teil seiner Information wieder ({facts}). Eine Person muss entscheiden.",
        "fr": "Apertus : la nécessité de la partie peu contrastée dépend de la tâche ; le texte ne donne qu'une partie de son information ({facts}). Une personne doit trancher.",
        "it": "Apertus: se la parte poco contrastata sia necessaria dipende dal compito; il testo ne riporta solo una parte ({facts}). Una persona deve decidere.",
    },
    "c1411.over_cap": {
        "en": "Parts of this graphic are below 3:1 ({facts}), but the per-page limit of image questions is reached. A person must check it.",
        "de": "Teile dieser Grafik liegen unter 3:1 ({facts}), aber die Höchstzahl an Bildfragen pro Seite ist erreicht. Eine Person muss es prüfen.",
        "fr": "Des parties de ce graphique sont sous 3:1 ({facts}), mais la limite de questions sur image par page est atteinte. Une personne doit vérifier.",
        "it": "Parti di questo grafico sono sotto 3:1 ({facts}), ma il limite di domande su immagini per pagina è raggiunto. Una persona deve verificare.",
    },
    "c1411.impact": {
        "en": "People with low vision may not see this control or graphic part, or may not find where to click or type.",
        "de": "Menschen mit Sehbehinderung sehen dieses Bedienelement oder diesen Grafikteil eventuell nicht und finden nicht, wo sie klicken oder tippen sollen.",
        "fr": "Les personnes malvoyantes risquent de ne pas voir ce contrôle ou cette partie graphique, ni où cliquer ou saisir.",
        "it": "Le persone ipovedenti potrebbero non vedere questo controllo o questa parte grafica, né dove cliccare o scrivere.",
    },
    "c1411.impact_focus": {
        "en": "Keyboard users with low vision may lose track of where the focus is.",
        "de": "Tastaturnutzende mit Sehbehinderung verlieren eventuell den Überblick, wo der Fokus ist.",
        "fr": "Les personnes malvoyantes qui naviguent au clavier risquent de perdre de vue où se trouve le focus.",
        "it": "Chi naviga con la tastiera e ha un'ipovisione potrebbe perdere di vista dove si trova il focus.",
    },
    "c1411.impact_ok": {
        "en": "People with low vision can make out this component or graphic.",
        "de": "Menschen mit Sehbehinderung können dieses Element oder diese Grafik erkennen.",
        "fr": "Les personnes malvoyantes peuvent distinguer ce composant ou ce graphique.",
        "it": "Le persone ipovedenti possono distinguere questo componente o grafico.",
    },
    "c1411.impact_exempt": {
        "en": "No contrast requirement applies here.",
        "de": "Hier gilt keine Kontrastanforderung.",
        "fr": "Aucune exigence de contraste ne s'applique ici.",
        "it": "Qui non si applica alcun requisito di contrasto.",
    },
    "c1411.fix_hint": {
        "en": "Use a colour with at least 3:1 against the adjacent colours, for example {suggestion} ({new_ratio}).",
        "de": "Verwenden Sie eine Farbe mit mindestens 3:1 zu den angrenzenden Farben, zum Beispiel {suggestion} ({new_ratio}).",
        "fr": "Utilisez une couleur d'au moins 3:1 par rapport aux couleurs adjacentes, par exemple {suggestion} ({new_ratio}).",
        "it": "Usate un colore con almeno 3:1 rispetto ai colori adiacenti, ad esempio {suggestion} ({new_ratio}).",
    },
    "c1411.fix_hint_graphic": {
        "en": "Darken the low-contrast parts to at least 3:1, or write their information as text (labels, values) in or next to the graphic.",
        "de": "Dunkeln Sie die kontrastarmen Teile auf mindestens 3:1 ab oder schreiben Sie ihre Information als Text (Beschriftungen, Werte) in oder neben die Grafik.",
        "fr": "Foncez les parties peu contrastées jusqu'à au moins 3:1, ou donnez leur information en texte (étiquettes, valeurs) dans le graphique ou à côté.",
        "it": "Scurite le parti poco contrastate fino ad almeno 3:1, oppure date la loro informazione come testo (etichette, valori) nel grafico o accanto.",
    },
    "c1411.ind.outline": {"en": "outline", "de": "Umriss", "fr": "contour", "it": "contorno"},
    "c1411.ind.box_shadow": {"en": "shadow", "de": "Schatten", "fr": "ombre", "it": "ombra"},
    "c1411.ind.border": {"en": "border", "de": "Rahmen", "fr": "bordure", "it": "bordo"},
})


def _stack(layers: list[dict] | None) -> C.RGB | None:
    """Composite a background layer list; None when an image or unknown colour is in it."""
    cols = []
    for layer in layers or []:
        c = C.parse_color(layer.get("c"))
        if layer.get("media") or layer.get("img") or c is None:
            return None
        cols.append(c)
    return C.composite(cols)


def _fix(fg: C.RGB, bg: C.RGB, ui: str) -> str | None:
    from klar.checks.c_1_4_3 import suggest_colour

    s = suggest_colour(fg, bg, C.NON_TEXT_MIN)
    return t("c1411.fix_hint", ui, suggestion=C.hex_of(s[0]), new_ratio=C.fmt_ratio(s[1])) if s else None


class NonTextContrast(BaseCheck):
    criterion = "1.4.11"
    prompt_version = PROMPT_VERSION
    needs_vision = True
    guard_numbers = False  # values may be read off a chart
    max_candidates = 200
    prompt_html_chars = 300

    # -- 1. candidates ------------------------------------------------------------------
    def candidates(self, page: CapturedPage) -> list[Candidate]:
        out: list[Candidate] = []
        pairs: dict[tuple, int] = {}

        def keep(m: dict) -> bool:
            if not m["kind"].endswith("_pass"):
                return True
            key = (m["kind"], m.get("fg"), m.get("bg"))
            pairs[key] = pairs.get(key, 0) + 1
            return pairs[key] <= PASSES_PER_PAIR

        for rec in C.records(page, "c1411_items", "c_1_4_11_ui.js"):
            m = self.measure_input(rec)
            if m and keep(m):
                out.append(self._cand(page, rec, m, rec.get("label", ""), "#input"))
        for rec in page.elements.get("c1411_items.icons", []):
            m = self.measure_icon(rec, page)
            if m and keep(m):
                out.append(self._cand(page, rec, m, rec.get("name", ""), "#icon"))
        for rec in page.elements.get("c1411_items.focus", []):
            m = self.measure_focus(rec)
            if m and keep(m):
                out.append(self._cand(page, rec, m, rec.get("text", ""), "#focus"))
        asks: list[Candidate] = []
        for i, rec in enumerate(page.elements.get("c1411_items.graphics", [])):
            if i >= GRAPHIC_SAMPLE_CAP:
                break
            cand = self._cand(page, rec, {"kind": "graphic"}, rec.get("alt", ""), "#graphic",
                              context={"caption": rec.get("caption", ""), "surrounding_text": rec.get("surrounding", "")})
            m = self.measure_graphic(rec, page, cand)
            if m is None:
                continue
            cand.extra.update(m)
            if m["kind"] == "ask":
                r = rec.get("rect") or {}
                cand.extra["area"] = r.get("w", 0) * r.get("h", 0)
                asks.append(cand)
            elif keep(m):
                out.append(cand)
        asks.sort(key=lambda c: -c.extra.get("area", 0))
        for i, cand in enumerate(asks):
            if i >= VISION_CAP:
                cand.extra["kind"] = "over_cap"
            elif self.vision and not cand.screenshot:
                cand.screenshot = page.screenshot(cand.selector, cand.id)
                cand.extra["screenshot_failed"] = cand.screenshot is None
        return out + asks

    def _cand(self, page: CapturedPage, rec: dict, m: dict, name: str, key: str,
              context: dict | None = None) -> Candidate:
        return self.candidate(page, selector=rec["selector"], html=rec.get("html", ""), text=name, accessible_name=name,
                              lang=rec.get("lang"), key=key, context=context, **m)

    # -- measurements (pure functions of a record, unit-tested) -------------------------------
    @staticmethod
    def measure_input(rec: dict) -> dict | None:
        outside = _stack(rec.get("outside"))
        if outside is None or rec.get("fill_image"):
            return None
        fill_c = C.parse_color(rec.get("fill"))
        if fill_c is None:
            return None
        fill = C.over(fill_c, outside)
        best, border_hex = C.contrast(fill, outside), ""
        has_border = False
        for b in rec.get("borders") or []:
            bc = C.parse_color(b.get("c"))
            if bc is None or bc[3] == 0:
                continue
            has_border = True
            col = C.over(bc, outside)
            r = max(C.contrast(col, outside), C.contrast(col, fill))
            if r >= best or not border_hex:
                border_hex = C.hex_of(col)
            best = max(best, r)
        if not has_border and best < 1.1:
            return None  # no visual boundary at all: nothing to measure
        base = dict(ratio=round(best, 4), border=border_hex or "–", fill=C.hex_of(fill), outside=C.hex_of(outside),
                    fg=border_hex, bg=C.hex_of(outside), fg_rgb=list(C.rgb(C.parse_color(border_hex) or fill)),
                    bg_rgb=list(C.rgb(outside)), component=rec.get("kind"))
        if best >= C.NON_TEXT_MIN:
            return {**base, "kind": "input_pass"}
        return {**base, "kind": "inactive" if rec.get("inactive") else "input_fail"}

    @staticmethod
    def measure_icon(rec: dict, page: CapturedPage | None = None) -> dict | None:
        bg = _stack(rec.get("layers"))
        if bg is None:
            return None
        fg = None
        svg = rec.get("svg") or None
        if svg and svg.get("gradient"):
            return {"kind": "icon_gradient", "bg": C.hex_of(bg)}
        if svg and svg.get("colours"):
            for item in svg["colours"]:  # heaviest colour that is not the background itself
                c = C.parse_color(item.get("c"))
                if c is None:
                    continue
                c = (c[0], c[1], c[2], c[3] * float(item.get("a", 1) or 1))
                col = C.over(c, bg)
                if C.contrast(col, bg) > 1.05:
                    fg = col
                    break
        elif rec.get("glyph"):
            c = C.parse_color(rec["glyph"])
            fg = C.over(c, bg) if c else None
        elif rec.get("image") and page is not None and page.live is not None:
            shot = page.screenshot(rec["selector"], "icon-" + hashlib.sha1(rec["selector"].encode("utf-8")).hexdigest()[:12])
            bm = C.load_crop(page, shot)
            if bm is not None:
                pal = C.palette(bm, min_share=0.01)
                if pal.colours:
                    bg = pal.background
                    fg = max(pal.colours, key=lambda kc: kc[1])[0]
        if fg is None:
            return None
        ratio = C.contrast(fg, bg)
        base = dict(ratio=round(ratio, 4), fg=C.hex_of(fg), bg=C.hex_of(bg), fg_rgb=list(C.rgb(fg)),
                    bg_rgb=list(C.rgb(bg)), from_pixels=not svg and not rec.get("glyph"))
        if ratio >= C.NON_TEXT_MIN:
            return {**base, "kind": "icon_pass"}
        return {**base, "kind": "inactive" if rec.get("inactive") else "icon_fail"}

    @staticmethod
    def measure_focus(rec: dict) -> dict | None:
        if rec.get("indicator") in (None, "removed"):
            return None
        colours = C.colours_in(rec.get("colour")) if rec.get("indicator") == "box_shadow" else \
            [c for c in [C.parse_color(rec.get("colour"))] if c]
        outside = _stack(rec.get("outside"))
        if not colours or outside is None:
            return None
        col = C.over(colours[0], outside)
        ratio = C.contrast(col, outside)
        return dict(kind="focus_pass" if ratio >= C.NON_TEXT_MIN else "focus_fail", ratio=round(ratio, 4),
                    fg=C.hex_of(col), bg=C.hex_of(outside), fg_rgb=list(C.rgb(col)), bg_rgb=list(C.rgb(outside)),
                    indicator=rec.get("indicator"))

    @staticmethod
    def measure_graphic(rec: dict, page: CapturedPage | None, cand: Candidate | None = None) -> dict | None:
        bg = _stack(rec.get("layers"))
        parts: list[C.RGB] = []
        svg = rec.get("svg") or None
        if svg and svg.get("colours"):
            if bg is None:
                return None
            for item in svg["colours"]:
                c = C.parse_color(item.get("c"))
                if c is not None:
                    col = C.over((c[0], c[1], c[2], c[3] * float(item.get("a", 1) or 1)), bg)
                    if C.contrast(col, bg) > 1.02:
                        parts.append(col)
        elif page is not None and page.live is not None and cand is not None:
            shot = page.screenshot(rec["selector"], cand.id)
            bm = C.load_crop(page, shot)
            if bm is None:
                return None
            pal = C.palette(bm, step=2 if bm.w * bm.h > 200_000 else 1)
            if pal.flat_share < 0.5:
                return None  # a photo: not a graphical object made of flat parts
            cand.screenshot = shot
            bg = pal.background
            parts = [col for col, _ in pal.colours]
        else:
            return None
        if not parts or bg is None:
            return None
        ratios = sorted(C.contrast(p, bg) for p in parts)
        low = [r for r in ratios if r < C.NON_TEXT_MIN]
        base = dict(ratio=round(ratios[0], 4), parts=len(parts), low_parts=len(low), bg=C.hex_of(bg))
        return {**base, "kind": "ask" if low else "graphic_pass"}

    # -- 2. deterministic decisions ----------------------------------------------------------
    def _kw(self, c: Candidate) -> dict:
        x = c.extra
        return dict(ratio=C.fmt_ratio(x.get("ratio", 0), 3.0), fg=x.get("fg", ""), bg=x.get("bg", ""),
                    border=x.get("border", ""), fill=x.get("fill", ""), outside=x.get("outside", ""),
                    indicator=t(f"c1411.ind.{x.get('indicator', 'outline')}", self.ui_lang))

    def _facts(self, c: Candidate) -> str:
        x = c.extra
        return t("c1411.facts", self.ui_lang, low=x.get("low_parts", 0), n=x.get("parts", 0),
                 ratio=C.fmt_ratio(x.get("ratio", 0), 3.0))

    def decide(self, c: Candidate) -> Finding | None:
        x, ui, kind = c.extra, self.ui_lang, c.extra.get("kind")
        kw = self._kw(c)
        fix = _fix(tuple(x["fg_rgb"]), tuple(x["bg_rgb"]), ui) if "fg_rgb" in x and kind and kind.endswith("_fail") else None
        table = {
            "input_fail": ("failed", "rule", "high", "c1411.input_fail", "c1411.impact"),
            "input_pass": ("passed", "rule", "high", "c1411.input_pass", "c1411.impact_ok"),
            "inactive": ("passed", "rule", "medium", "c1411.inactive", "c1411.impact_exempt"),
            "icon_fail": ("failed", "heuristic" if x.get("from_pixels") else "rule",
                          "medium" if x.get("from_pixels") else "high", "c1411.icon_fail", "c1411.impact"),
            "icon_pass": ("passed", "heuristic" if x.get("from_pixels") else "rule", "medium", "c1411.icon_pass",
                          "c1411.impact_ok"),
            "icon_gradient": ("cantTell", "heuristic", "low", "c1411.icon_gradient", "impact.review"),
            "focus_fail": ("failed", "heuristic", "high", "c1411.focus_fail", "c1411.impact_focus"),
            "focus_pass": ("passed", "heuristic", "medium", "c1411.focus_pass", "c1411.impact_ok"),
            "graphic_pass": ("passed", "heuristic", "medium", "c1411.graphic_pass", "c1411.impact_ok"),
        }
        if kind in table:
            outcome, source, conf, key, impact = table[kind]
            excerpt = c.text if c.text and c.text in c.html else c.html[:300]
            return self.finding(c, outcome=outcome, source=source, confidence=conf, reason_code=kind,  # type: ignore[arg-type]
                                excerpt=excerpt, explanation=t(key, ui, **kw), user_impact=t(impact, ui), fix_hint=fix)
        if kind == "over_cap":
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="low", reason_code=kind,
                                explanation=t("c1411.over_cap", ui, facts=self._facts(c)), user_impact=t("impact.review", ui))
        if kind == "ask" and self.vision and (x.get("screenshot_failed") or not c.screenshot):
            return self.note(c, "note.no_screenshot")
        return None

    # -- 3. the closed question (vision) --------------------------------------------------------
    SYSTEM = (
        "You check WCAG 2.1 success criterion 1.4.11 Non-text Contrast for ONE graphic (attached crop). Code "
        "measured that some of its graphical parts (lines, areas, symbols) have less than 3:1 contrast against the "
        "background. That is a failure only if those parts are required to understand the content.\n"
        "category: required = a low-contrast part is needed to understand the content and the same information is "
        "not given as text in or next to the graphic; labelled = the information of the low-contrast parts is also "
        "written as text (labels, values, a description) in or next to the graphic; decorative = the graphic is "
        "decoration and conveys no information; essential_scale = the colours are a heat map or colour scale of a "
        "measurement, where low contrast between steps is essential; unclear = the text gives only part of the "
        "information, or it depends on what the user needs to do.\n"
        "quote: the text alternative or caption exactly as written in the page data, or an empty string."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        # ui_lang is deliberately unused: prompts are identical for every UI language.
        x = c.extra
        ctx = {**c.context, "low_contrast_parts": f"{x.get('low_parts', 0)} of {x.get('parts', 0)} colours below 3:1, "
                                                  f"lowest {C.fmt_ratio(x.get('ratio', 0), 3.0)}"}
        return self.task(system=self.system_prompt(self.SYSTEM, c),
                         element={"alternative": c.accessible_name or "", "html": self.prompt_html(c)},
                         context=ctx, images=[c.screenshot] if c.screenshot else [],
                         question="Are the low-contrast parts of this graphic required to understand the content?",
                         schema=category_schema(CATEGORIES), max_tokens=120)

    # -- 4. interpretation ----------------------------------------------------------------------
    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        cat = answer.get("category", "unclear")
        if cat not in CATEGORY_OUTCOME:
            cat = "unclear"
        outcome = CATEGORY_OUTCOME[cat]
        impact = {"failed": "c1411.impact", "passed": "c1411.impact_ok"}.get(outcome, "impact.review")
        quote = (answer.get("quote") or "").strip()
        excerpt = quote or (c.accessible_name if c.accessible_name and c.accessible_name in c.html else c.html[:300])
        return self.finding(c, outcome=outcome, source="apertus",
                            confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
                            excerpt=excerpt, explanation=t(f"c1411.apertus_{cat}", ui, facts=self._facts(c)),
                            user_impact=t(impact, ui), reason=answer.get("reason"), reason_code=f"apertus_{cat}",
                            fix_hint=t("c1411.fix_hint_graphic", ui) if outcome == "failed" else None)


CHECK = NonTextContrast
