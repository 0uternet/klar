"""1.4.3 Contrast (Minimum), level AA (vision for the exemptions only). ACT rule
afw4f7 (text has minimum contrast); axe-core rule `color-contrast`.

Measured in CODE (capture/js/c_1_4_3_texts.js + checks/colour.py), never by the model:
  * every element with its own visible text: computed `color` (and
    -webkit-text-fill-color), opacity of the ancestors, font size and weight;
  * what lies behind the text: the paint stack at the first glyph
    (document.elementsFromPoint), so a caption positioned over an <img> or a
    sibling box counts, down to the first opaque colour; alpha is composited;
  * WCAG relative-luminance contrast, never rounded before the comparison
    (#777 on #fff = 4.478:1 fails); 4.5:1, or 3:1 for large text (≥ 24 px, or
    ≥ 18.66 px at weight ≥ 700; 18 px bold is not large);
  * text over a background IMAGE or GRADIENT: element screenshots with the text
    repainted black, white and transparent (Playwright's screenshot-only `style`, the
    DOM is not touched). Where the black and white renderings differ, a glyph covers
    the pixel (white text on a white area is found too); its background is read from
    the text-less crop. 10th / 90th percentile of the glyph-pixel contrast:
      p10 ≥ required → passed;  p90 < required → failed (even the best part fails,
      so ACT's "highest possible contrast" fails too);  otherwise → cantTell
      (PROTOCOL 1.4.3/C1: some pixels of each glyph pass, others fail);
  * exemptions decided in code: inactive components (disabled control, disabled
    fieldset, aria-disabled; ACT afw4f7 inapplicable) → passed;
  * text-shadow or -webkit-text-stroke (inherited, so ancestors count): if the text
    fails against its background — solid, image or gradient — but passes against its
    own shadow / outline colour → cantTell (PROTOCOL 1.4.3/C2: outline or halo is a
    visual call); a halo that does not reach the threshold either does not help;
  * axe-core `color-contrast`: a violation on the same element is replaced by this
    check's measured finding (same selector; it carries the ratios); a candidate sent
    to Apertus claims axe's finding (`supersedes_axe`), so an exempt logotype is not
    left failed by axe; an "incomplete" node this check could not measure becomes
    cantTell (axe_rule="color-contrast": that finding does come from axe).

Asked to APERTUS (vision, crop of the element) ONLY when the text fails AND a code
signal says it may be exempt (inside aria-hidden, a link to the home page, an id or
class naming a logo/brand): the SC exempts logotypes and pure decoration.
  Closed question: "Is this text content, part of a logo or brand name, or pure decoration?"
  text_role: content → failed · logotype → passed · decoration → passed · unsure → cantTell
  (decoration on a link/button/label is a contradiction → cantTell).
At most 6 such questions per page (largest text first); the rest → cantTell.
No vision backend → cantTell "vision backend required" (pipeline, needs_vision).

Passed findings are reported only where they say something (contrast < 7:1, the
large-text threshold, a pixel measurement, an exemption), at most 3 per colour pair.

Limits: text inside images (logos, banners) is not measured here (1.4.5 asks about
images of text); colours in oklch()/lab() are skipped; pseudo-element text, text in
SVG and placeholder text are not measured (axe covers part of it); a filter or
mix-blend-mode on an ancestor is ignored; the glyph-pixel method treats a child of
another colour inside the element as part of the glyphs.
"""

from __future__ import annotations

import html as htmllib

from klar.capture.page import CapturedPage
from klar.checks import colour as C
from klar.checks.base import BaseCheck, category_schema
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "1.4.3/v1"
VISION_CAP = 6  # vision questions per page
SAMPLE_CAP = 8  # pixel measurements (4 small screenshots each) per page
REPORT_PASS_BELOW = 7.0
PASSES_PER_PAIR = 3
ROLES = ["content", "logotype", "decoration", "unsure"]
ROLE_OUTCOME = {"content": "failed", "logotype": "passed", "decoration": "passed", "unsure": "cantTell"}
EXEMPT_SIGNALS = {"aria_hidden", "links_to_home_page", "logo_class_or_id"}

register({
    "c143.size": {"en": "{px} px", "de": "{px} px", "fr": "{px} px", "it": "{px} px"},
    "c143.size_bold": {"en": "{px} px bold", "de": "{px} px fett", "fr": "{px} px gras", "it": "{px} px grassetto"},
    "c143.fail": {
        "en": "Text contrast is {ratio}, below the required {need} ({size}): {fg} on {bg}.",
        "de": "Der Textkontrast beträgt {ratio} und liegt unter den geforderten {need} ({size}): {fg} auf {bg}.",
        "fr": "Le contraste du texte est de {ratio}, inférieur aux {need} requis ({size}) : {fg} sur {bg}.",
        "it": "Il contrasto del testo è {ratio}, inferiore al {need} richiesto ({size}): {fg} su {bg}.",
    },
    "c143.pass": {
        "en": "Text contrast is {ratio}; {need} is required ({size}): {fg} on {bg}.",
        "de": "Der Textkontrast beträgt {ratio}; gefordert sind {need} ({size}): {fg} auf {bg}.",
        "fr": "Le contraste du texte est de {ratio} ; {need} sont requis ({size}) : {fg} sur {bg}.",
        "it": "Il contrasto del testo è {ratio}; è richiesto {need} ({size}): {fg} su {bg}.",
    },
    "c143.large_pass": {
        "en": "Large text ({size}): contrast {ratio} meets the 3:1 required for large text ({fg} on {bg}).",
        "de": "Grosser Text ({size}): Der Kontrast von {ratio} erfüllt die für grossen Text geforderten 3:1 ({fg} auf {bg}).",
        "fr": "Grand texte ({size}) : le contraste de {ratio} atteint les 3:1 requis pour le grand texte ({fg} sur {bg}).",
        "it": "Testo grande ({size}): il contrasto di {ratio} raggiunge il 3:1 richiesto per il testo grande ({fg} su {bg}).",
    },
    "c143.inactive": {
        "en": "Text of an inactive (disabled) component: contrast {ratio} is exempt from 1.4.3.",
        "de": "Text eines inaktiven (deaktivierten) Bedienelements: Der Kontrast von {ratio} ist von 1.4.3 ausgenommen.",
        "fr": "Texte d'un composant inactif (désactivé) : le contraste de {ratio} est exempté du critère 1.4.3.",
        "it": "Testo di un componente inattivo (disattivato): il contrasto di {ratio} è esente dal criterio 1.4.3.",
    },
    "c143.shadow": {
        "en": "Contrast against the background is only {ratio} (required {need}), but a text shadow or outline gives {shadow} against the text. Whether it outlines the letters or forms a wide halo must be checked by eye.",
        "de": "Der Kontrast zum Hintergrund beträgt nur {ratio} (gefordert {need}), ein Textschatten oder eine Kontur ergibt aber {shadow} zum Text. Ob sie die Buchstaben umrandet oder einen breiten Schein bildet, muss eine Person prüfen.",
        "fr": "Le contraste avec le fond n'est que de {ratio} ({need} requis), mais une ombre portée ou un contour donne {shadow} avec le texte. Une personne doit vérifier s'il suit le contour des lettres ou forme un large halo.",
        "it": "Il contrasto con lo sfondo è solo {ratio} (richiesto {need}), ma un'ombra o un contorno del testo dà {shadow} rispetto al testo. Una persona deve verificare se contorna le lettere o forma un ampio alone.",
    },
    "c143.image_shadow": {
        "en": "Text over an image or gradient: behind the letters the contrast is {low} to {high} (required {need}), but a text shadow or outline gives {shadow} against the text. Whether it outlines the letters or forms a wide halo must be checked by eye.",
        "de": "Text auf einem Bild oder Farbverlauf: Hinter den Buchstaben beträgt der Kontrast {low} bis {high} (gefordert {need}), ein Textschatten oder eine Kontur ergibt aber {shadow} zum Text. Ob sie die Buchstaben umrandet oder einen breiten Schein bildet, muss eine Person prüfen.",
        "fr": "Texte sur une image ou un dégradé : derrière les lettres, le contraste va de {low} à {high} ({need} requis), mais une ombre portée ou un contour donne {shadow} avec le texte. Une personne doit vérifier s'il suit le contour des lettres ou forme un large halo.",
        "it": "Testo su un'immagine o una sfumatura: dietro le lettere il contrasto va da {low} a {high} (richiesto {need}), ma un'ombra o un contorno del testo dà {shadow} rispetto al testo. Una persona deve verificare se contorna le lettere o forma un ampio alone.",
    },
    "c143.image_pass": {
        "en": "Text over an image or gradient, measured behind the letters: at least {low} for 90 % of the letter pixels (required {need}).",
        "de": "Text auf einem Bild oder Farbverlauf, hinter den Buchstaben gemessen: mindestens {low} für 90 % der Buchstabenpixel (gefordert {need}).",
        "fr": "Texte sur une image ou un dégradé, mesuré derrière les lettres : au moins {low} pour 90 % des pixels des lettres ({need} requis).",
        "it": "Testo su un'immagine o una sfumatura, misurato dietro le lettere: almeno {low} per il 90 % dei pixel delle lettere (richiesto {need}).",
    },
    "c143.image_fail": {
        "en": "Text over an image or gradient, measured behind the letters: even the best part reaches only {high} (required {need}).",
        "de": "Text auf einem Bild oder Farbverlauf, hinter den Buchstaben gemessen: Selbst der beste Teil erreicht nur {high} (gefordert {need}).",
        "fr": "Texte sur une image ou un dégradé, mesuré derrière les lettres : même la meilleure partie n'atteint que {high} ({need} requis).",
        "it": "Testo su un'immagine o una sfumatura, misurato dietro le lettere: anche la parte migliore raggiunge solo {high} (richiesto {need}).",
    },
    "c143.image_mixed": {
        "en": "Text over an image or gradient: behind the letters the contrast varies from {low} to {high} (required {need}). Parts of the letters meet the threshold, others do not.",
        "de": "Text auf einem Bild oder Farbverlauf: Hinter den Buchstaben schwankt der Kontrast zwischen {low} und {high} (gefordert {need}). Teile der Buchstaben erreichen den geforderten Wert, andere nicht.",
        "fr": "Texte sur une image ou un dégradé : derrière les lettres, le contraste varie de {low} à {high} ({need} requis). Une partie des lettres atteint le seuil, une autre non.",
        "it": "Testo su un'immagine o una sfumatura: dietro le lettere il contrasto varia da {low} a {high} (richiesto {need}). Parti delle lettere raggiungono la soglia, altre no.",
    },
    "c143.image_unmeasured": {
        "en": "Text over an image or gradient: the contrast could not be measured. A person must check it.",
        "de": "Text auf einem Bild oder Farbverlauf: Der Kontrast konnte nicht gemessen werden. Eine Person muss ihn prüfen.",
        "fr": "Texte sur une image ou un dégradé : le contraste n'a pas pu être mesuré. Une personne doit le vérifier.",
        "it": "Testo su un'immagine o una sfumatura: non è stato possibile misurare il contrasto. Una persona deve verificarlo.",
    },
    "c143.axe_incomplete": {
        "en": "axe-core could not decide the contrast of this text ({summary}). A person must check it.",
        "de": "axe-core konnte den Kontrast dieses Textes nicht beurteilen ({summary}). Eine Person muss ihn prüfen.",
        "fr": "axe-core n'a pas pu évaluer le contraste de ce texte ({summary}). Une personne doit le vérifier.",
        "it": "axe-core non ha potuto valutare il contrasto di questo testo ({summary}). Una persona deve verificarlo.",
    },
    "c143.over_cap": {
        "en": "Contrast {ratio} is below {need}; this may be a logo or decoration, but the per-page limit of image questions is reached. A person must check it.",
        "de": "Der Kontrast von {ratio} liegt unter {need}; es könnte ein Logo oder Dekoration sein, aber die Höchstzahl an Bildfragen pro Seite ist erreicht. Eine Person muss es prüfen.",
        "fr": "Le contraste de {ratio} est inférieur à {need} ; il peut s'agir d'un logo ou d'une décoration, mais la limite de questions sur image par page est atteinte. Une personne doit vérifier.",
        "it": "Il contrasto di {ratio} è inferiore a {need}; potrebbe essere un logo o una decorazione, ma il limite di domande su immagini per pagina è raggiunto. Una persona deve verificare.",
    },
    "c143.apertus_content": {
        "en": "Apertus: this is content text, not a logo or decoration. Its contrast of {ratio} is below the required {need}.",
        "de": "Apertus: Dies ist inhaltlicher Text, kein Logo und keine Dekoration. Sein Kontrast von {ratio} liegt unter den geforderten {need}.",
        "fr": "Apertus : il s'agit d'un texte de contenu, ni logo ni décoration. Son contraste de {ratio} est inférieur aux {need} requis.",
        "it": "Apertus: è un testo di contenuto, non un logo né una decorazione. Il suo contrasto di {ratio} è inferiore al {need} richiesto.",
    },
    "c143.apertus_logotype": {
        "en": "Apertus: this text is part of a logo or brand name. Logotypes are exempt from 1.4.3 (contrast {ratio}).",
        "de": "Apertus: Dieser Text ist Teil eines Logos oder Markennamens. Logos sind von 1.4.3 ausgenommen (Kontrast {ratio}).",
        "fr": "Apertus : ce texte fait partie d'un logo ou d'un nom de marque. Les logotypes sont exemptés du critère 1.4.3 (contraste {ratio}).",
        "it": "Apertus: questo testo fa parte di un logo o di un marchio. I logotipi sono esenti dal criterio 1.4.3 (contrasto {ratio}).",
    },
    "c143.apertus_decoration": {
        "en": "Apertus: this text is pure decoration and conveys nothing, so 1.4.3 does not apply (contrast {ratio}).",
        "de": "Apertus: Dieser Text ist reine Dekoration und vermittelt nichts, daher gilt 1.4.3 nicht (Kontrast {ratio}).",
        "fr": "Apertus : ce texte est purement décoratif et ne transmet rien, le critère 1.4.3 ne s'applique donc pas (contraste {ratio}).",
        "it": "Apertus: questo testo è pura decorazione e non trasmette nulla, quindi il criterio 1.4.3 non si applica (contrasto {ratio}).",
    },
    "c143.apertus_unsure": {
        "en": "Apertus could not tell whether this text is content, a logo or decoration (contrast {ratio}, required {need}). A person must check it.",
        "de": "Apertus konnte nicht beurteilen, ob dieser Text Inhalt, Logo oder Dekoration ist (Kontrast {ratio}, gefordert {need}). Eine Person muss ihn prüfen.",
        "fr": "Apertus n'a pas pu dire si ce texte est du contenu, un logo ou une décoration (contraste {ratio}, {need} requis). Une personne doit le vérifier.",
        "it": "Apertus non ha potuto stabilire se questo testo sia contenuto, logo o decorazione (contrasto {ratio}, richiesto {need}). Una persona deve verificarlo.",
    },
    "c143.impact": {
        "en": "People with low vision or colour-vision deficiency may not be able to read this text.",
        "de": "Menschen mit Sehbehinderung oder Farbsehschwäche können diesen Text eventuell nicht lesen.",
        "fr": "Les personnes malvoyantes ou ayant un trouble de la vision des couleurs risquent de ne pas pouvoir lire ce texte.",
        "it": "Le persone ipovedenti o con un deficit nella visione dei colori potrebbero non riuscire a leggere questo testo.",
    },
    "c143.impact_ok": {
        "en": "The text stands out enough from its background for people with low vision.",
        "de": "Der Text hebt sich für Menschen mit Sehbehinderung genügend vom Hintergrund ab.",
        "fr": "Le texte se détache suffisamment du fond pour les personnes malvoyantes.",
        "it": "Il testo si distingue abbastanza dallo sfondo per le persone ipovedenti.",
    },
    "c143.impact_exempt": {
        "en": "No contrast requirement applies here; people with low vision may still find this text hard to read.",
        "de": "Hier gilt keine Kontrastanforderung; Menschen mit Sehbehinderung lesen diesen Text eventuell trotzdem schlecht.",
        "fr": "Aucune exigence de contraste ne s'applique ici ; les personnes malvoyantes peuvent tout de même avoir du mal à lire ce texte.",
        "it": "Qui non si applica alcun requisito di contrasto; le persone ipovedenti potrebbero comunque leggere a fatica questo testo.",
    },
    "c143.fix_hint": {
        "en": "Raise the contrast to at least {need}: for example {suggestion} on {bg} gives {new_ratio}.",
        "de": "Erhöhen Sie den Kontrast auf mindestens {need}: zum Beispiel ergibt {suggestion} auf {bg} einen Wert von {new_ratio}.",
        "fr": "Augmentez le contraste à au moins {need} : par exemple, {suggestion} sur {bg} donne {new_ratio}.",
        "it": "Aumentate il contrasto ad almeno {need}: ad esempio {suggestion} su {bg} dà {new_ratio}.",
    },
    "c143.fix_hint_image": {
        "en": "Put the text on a solid backdrop, darken or lighten the image behind it, or move the text off the picture.",
        "de": "Setzen Sie den Text auf eine deckende Fläche, dunkeln Sie das Bild dahinter ab oder hellen Sie es auf, oder setzen Sie den Text neben das Bild.",
        "fr": "Placez le texte sur un fond uni, assombrissez ou éclaircissez l'image derrière lui, ou sortez le texte de l'image.",
        "it": "Mettete il testo su uno sfondo pieno, scurite o schiarite l'immagine dietro di esso, oppure spostate il testo fuori dall'immagine.",
    },
})


def suggest_colour(fg: C.RGB, bg: C.RGB, need: float) -> tuple[C.RGB, float] | None:
    """The closest darker or lighter shade of `fg` that reaches `need` on `bg`."""
    best = None
    for target in ((0, 0, 0), (255, 255, 255)):
        for step in range(1, 21):
            k = step / 20
            c = tuple(round(fg[i] + (target[i] - fg[i]) * k) for i in range(3))
            r = C.contrast(c, bg)
            if r >= need + 0.05:
                if best is None or k < best[2]:
                    best = (c, r, k)
                break
    return (best[0], best[1]) if best else None  # type: ignore[return-value]


def halo_colours(rec: dict) -> list[C.RGBA]:
    """Colours drawn around the glyphs: text-shadow (alpha ≥ 0.1) and -webkit-text-stroke.
    Both are inherited, so the element's computed value includes its ancestors'."""
    out = [h for h in C.colours_in(rec.get("text_shadow")) if h[3] >= 0.1]
    if float(rec.get("stroke_w") or 0) > 0:
        sc = C.parse_color(rec.get("stroke_c"))
        if sc is not None and sc[3] >= 0.1:
            out.append(sc)
    return out


def image_kind(low: float, high: float, need: float, fg: C.RGBA, halos: list[C.RGBA]) -> tuple[str, float | None]:
    """Decision for text over an image or gradient from the glyph-pixel percentiles.
    A shadow or outline is removed in the measurement repaints; when the letters fail
    against the image but pass against their own halo, whether the halo outlines the
    letters or is a wide glow is a visual judgement (PROTOCOL 1.4.3/C2) → cantTell.
    A semi-transparent halo is judged on both a white and a black base (worst case)."""
    if low >= need:
        return "image_pass", None
    if halos:
        best = max(min(C.contrast(C.over(fg, base), C.over(h, base)) for base in (C.WHITE, (0, 0, 0)))
                   for h in halos)
        if best >= need:
            return "image_shadow", best
    return ("image_fail" if high < need else "image_mixed"), None


class ContrastMinimum(BaseCheck):
    criterion = "1.4.3"
    prompt_version = PROMPT_VERSION
    needs_vision = True
    guard_numbers = False  # the model may cite the ratios we measured or read text off the crop
    max_candidates = 300
    prompt_html_chars = 300

    # -- 1. candidates ------------------------------------------------------------------
    def candidates(self, page: CapturedPage) -> list[Candidate]:
        recs = C.records(page, "c143_texts", "c_1_4_3_texts.js", {"max": 400})
        axe = C.axe_nodes(page, "color-contrast")
        out: list[Candidate] = []
        pairs: dict[tuple, int] = {}
        asks: list[Candidate] = []
        sampled = 0
        measured: set[str] = set()
        for rec in recs:
            if len(out) >= self.max_candidates:
                break
            m = self.measure(rec)
            if m is None:
                continue
            measured.add(rec["selector"])
            kind = m["kind"]
            cand = self.candidate(page, selector=rec["selector"], html=rec.get("html", ""), text=rec.get("text", ""),
                                  lang=rec.get("lang"), **m)
            if kind == "image":
                if sampled < SAMPLE_CAP and page.live is not None:
                    sampled += 1
                    self.sample(page, cand)
                else:
                    cand.extra["kind"] = "image_unmeasured"
            kind = cand.extra["kind"]
            if kind in ("fail", "image_fail") and set(cand.extra.get("signals", [])) & EXEMPT_SIGNALS:
                cand.extra["measured_kind"] = kind
                cand.extra["kind"] = "ask"
                asks.append(cand)
            elif kind in ("pass", "large_pass"):
                if cand.extra["ratio"] >= REPORT_PASS_BELOW and kind == "pass":
                    continue
                key = (cand.extra["fg"], cand.extra["bg"], kind)
                pairs[key] = pairs.get(key, 0) + 1
                if pairs[key] > PASSES_PER_PAIR:
                    continue
            if axe.get(rec["selector"]):
                cand.extra["axe"] = axe[rec["selector"]]["group"]
                if cand.extra["kind"] == "ask":
                    # this check judges the element itself (logo / decoration): axe's finding is
                    # superseded once the pipeline honours the claim
                    cand.extra["supersedes_axe"] = ["color-contrast"]
            out.append(cand)
        # Vision budget: the largest text first.
        asks.sort(key=lambda c: -(c.extra.get("font_px", 0) * max(1, len(c.text))))
        for i, cand in enumerate(asks):
            if i >= VISION_CAP:
                cand.extra["kind"] = "over_cap"
            elif self.vision:
                shot = cand.screenshot or page.screenshot(cand.selector, cand.id)
                cand.screenshot = shot
                cand.extra["screenshot_failed"] = shot is None
        # axe "incomplete" nodes this check could not measure
        for sel, node in axe.items():
            if node["group"] == "incomplete" and sel not in measured and len(out) < self.max_candidates:
                out.append(self.candidate(page, selector=sel, html=node.get("html", ""), text="", key="#axe",
                                          kind="axe_incomplete", summary=node.get("summary", "")[:200], axe="incomplete"))
        return out

    def measure(self, rec: dict) -> dict | None:
        """Facts for one text record (pure function of the record: unit-tested)."""
        fg = C.parse_color(rec.get("fill") or "") or C.parse_color(rec.get("color"))
        if fg is None:
            return None
        if rec.get("fill") and C.parse_color(rec["fill"]) and C.parse_color(rec["fill"])[3] == 0:
            fg = C.parse_color(rec.get("color"))
            if fg is None:
                return None
        alpha = fg[3] * float(rec.get("opacity", 1) or 1)
        if alpha <= 0.02:
            return None  # invisible text
        fg = (fg[0], fg[1], fg[2], alpha)
        px, weight = float(rec.get("font_px") or 0), float(rec.get("weight") or 400)
        need = C.text_threshold(px, weight)
        signals = list(rec.get("brand") or [])
        if rec.get("hidden"):
            signals.append("aria_hidden")
        halos = halo_colours(rec)
        base = dict(fg_rgba=list(fg), font_px=round(px, 2), weight=weight, need=need, large=C.is_large_text(px, weight),
                    signals=signals, interactive=bool(rec.get("interactive")), inactive=bool(rec.get("inactive")),
                    halos=[list(h) for h in halos])
        colours: list[C.RGBA] = []
        image = None
        for layer in rec.get("layers") or []:
            if layer.get("media") or layer.get("img"):
                image = layer
                break
            c = C.parse_color(layer.get("c"))
            if c is None:
                return None
            colours.append(c)
        if image is not None:
            return {**base, "kind": "image", "fg": C.hex_of(fg), "bg": "image", "ratio": 0.0,
                    "background": "gradient" if image.get("gradient") else (image.get("media") or "image")}
        bg = C.composite(colours)
        fg_eff = C.over(fg, bg)
        ratio = C.contrast(fg_eff, bg)
        out = {**base, "fg": C.hex_of(fg_eff), "bg": C.hex_of(bg), "ratio": round(ratio, 4), "bg_rgb": list(C.rgb(bg)),
               "fg_rgb": list(C.rgb(fg_eff))}
        if ratio >= need:
            kind = "large_pass" if (out["large"] and ratio < C.TEXT_MIN) else "pass"
        elif rec.get("inactive"):
            kind = "inactive"
        else:
            kind = "fail"
            if halos:
                best = max(C.contrast(fg_eff, C.over(h, bg)) for h in halos)
                if best >= need:
                    kind, out["shadow_ratio"] = "shadow", round(best, 4)
        return {**out, "kind": kind}

    def sample(self, page: CapturedPage, cand: Candidate) -> None:
        """Glyph-pixel measurement for text over an image or gradient."""
        shots = [C.element_png(page, cand.selector)]
        for colour in ("#000", "#fff", "transparent"):
            shots.append(C.element_png(page, cand.selector, text_colour=colour) if shots[-1] else None)
        if not all(shots):
            cand.extra["kind"] = "image_unmeasured"
            return
        cand.screenshot = C.save_crop(page, cand.id, shots[0])  # what the UI shows
        try:
            black, white, without = (C.decode_png(s) for s in shots[1:])
            gc = C.glyph_contrast(black, white, without, tuple(cand.extra["fg_rgba"]), cand.extra["need"])
        except Exception:
            gc = None
        if gc is None:
            cand.extra["kind"] = "image_unmeasured"
            return
        cand.extra.update(low=round(gc.low, 4), high=round(gc.high, 4), median=round(gc.median, 4),
                          share_ok=gc.share_ok, glyph_pixels=gc.pixels, ratio=round(gc.median, 4))
        kind, halo = image_kind(gc.low, gc.high, cand.extra["need"], tuple(cand.extra["fg_rgba"]),
                                [tuple(h) for h in cand.extra.get("halos", [])])
        cand.extra["kind"] = kind
        if halo is not None:
            cand.extra["shadow_ratio"] = round(halo, 4)

    # -- 2. deterministic decisions ----------------------------------------------------------
    def _kw(self, c: Candidate) -> dict:
        x, ui = c.extra, self.ui_lang
        need = x.get("need", C.TEXT_MIN)
        px = f"{x.get('font_px', 0):g}"
        size = t("c143.size_bold" if x.get("weight", 400) >= C.BOLD else "c143.size", ui, px=px)
        kw = dict(ratio=C.fmt_ratio(x.get("ratio", 0), need), need=C.fmt_ratio(need), size=size,
                  fg=x.get("fg", ""), bg=x.get("bg", ""))
        if "low" in x:
            kw.update(low=C.fmt_ratio(x["low"], need), high=C.fmt_ratio(x["high"], need))
        if "shadow_ratio" in x:
            kw["shadow"] = C.fmt_ratio(x["shadow_ratio"])
        return kw

    def _fix(self, c: Candidate) -> dict:
        x = c.extra
        if x.get("kind") in ("image_fail", "image_mixed") or x.get("measured_kind") == "image_fail":
            return {"fix_hint": t("c143.fix_hint_image", self.ui_lang)}
        if "fg_rgb" not in x:
            return {}
        s = suggest_colour(tuple(x["fg_rgb"]), tuple(x["bg_rgb"]), x["need"])
        if not s:
            return {}
        return {"fix_hint": t("c143.fix_hint", self.ui_lang, need=C.fmt_ratio(x["need"]), suggestion=C.hex_of(s[0]),
                              bg=x["bg"], new_ratio=C.fmt_ratio(s[1]))}

    def decide(self, c: Candidate) -> Finding | None:
        kind, ui, x = c.extra.get("kind"), self.ui_lang, c.extra
        kw = self._kw(c)
        if kind == "fail":
            return self._f(c, "failed", "rule", "high", "c143.fail", "c143.impact", kw, **self._fix(c))
        if kind == "pass":
            return self._f(c, "passed", "rule", "high", "c143.pass", "c143.impact_ok", kw)
        if kind == "large_pass":
            return self._f(c, "passed", "rule", "high", "c143.large_pass", "c143.impact_ok", kw)
        if kind == "inactive":
            return self._f(c, "passed", "rule", "medium", "c143.inactive", "c143.impact_exempt", kw, act_rule=None)
        if kind == "shadow":
            return self._f(c, "cantTell", "heuristic", "low", "c143.shadow", "impact.review", kw)
        if kind == "image_pass":
            return self._f(c, "passed", "heuristic", "medium", "c143.image_pass", "c143.impact_ok", kw)
        if kind == "image_fail":
            return self._f(c, "failed", "heuristic", "medium", "c143.image_fail", "c143.impact", kw, **self._fix(c))
        if kind == "image_shadow":
            return self._f(c, "cantTell", "heuristic", "low", "c143.image_shadow", "impact.review", kw)
        if kind == "image_mixed":
            return self._f(c, "cantTell", "heuristic", "low", "c143.image_mixed", "impact.review", kw, **self._fix(c))
        if kind == "image_unmeasured":
            return self._f(c, "cantTell", "heuristic", "low", "c143.image_unmeasured", "impact.review", kw)
        if kind == "axe_incomplete":
            return self.finding(c, outcome="cantTell", source="rule", confidence="low", reason_code=kind,
                                excerpt=c.html[:300], explanation=t("c143.axe_incomplete", ui, summary=x.get("summary") or "–"),
                                user_impact=t("impact.review", ui), act_rule=None, axe_rule="color-contrast")
        if kind == "over_cap":
            return self._f(c, "cantTell", "heuristic", "low", "c143.over_cap", "impact.review", kw)
        if kind == "ask" and self.vision and x.get("screenshot_failed"):
            return self.note(c, "note.no_screenshot")
        return None

    def _f(self, c: Candidate, outcome: str, source: str, confidence: str, key: str, impact: str, kw: dict,
           **extra) -> Finding:
        return self.finding(c, outcome=outcome, source=source, confidence=confidence,  # type: ignore[arg-type]
                            reason_code=key.split(".", 1)[1], explanation=t(key, self.ui_lang, **kw),
                            user_impact=t(impact, self.ui_lang), **extra)

    def finding(self, c: Candidate, *, axe_rule: str | None = None, **kwargs) -> Finding:  # type: ignore[override]
        f = super().finding(c, **kwargs)
        return f.model_copy(update={"axe_rule": axe_rule}) if axe_rule else f

    # -- 3. the closed question (vision) --------------------------------------------------------
    SYSTEM = (
        "You check WCAG 2.1 success criterion 1.4.3 Contrast (Minimum) for ONE piece of text (attached crop). "
        "Its measured contrast is below the required ratio. The criterion does not apply to text that is part "
        "of a logo or brand name, or to text that is pure decoration.\n"
        "text_role: content = the text gives information, names something or labels a control; "
        "logotype = the text is part of a logo or brand name; decoration = purely decorative text that conveys "
        "nothing (a watermark, an ornamental letter or number); unsure = cannot tell.\n"
        "quote: the text exactly as written in the page data."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        # ui_lang is deliberately unused: prompts are identical for every UI language.
        x = c.extra
        ctx = {"measured_contrast": C.fmt_ratio(x.get("ratio", 0), x.get("need")),
               "required_contrast": C.fmt_ratio(x.get("need", C.TEXT_MIN))}
        pos = [s for s in x.get("signals", []) if s in ("links_to_home_page", "in_page_header", "aria_hidden")]
        if pos:
            ctx["position"] = ", ".join(s.replace("_", " ") for s in pos)
        return self.task(
            system=self.system_prompt(self.SYSTEM, c),
            element={"text": c.text[:200], "html": self.prompt_html(c)},
            context=ctx,
            images=[c.screenshot] if c.screenshot else [],
            question="Is this text content, part of a logo or brand name, or pure decoration?",
            schema=category_schema(ROLES),
            max_tokens=120,
        )

    # -- 4. interpretation ----------------------------------------------------------------------
    def interpret(self, c: Candidate, answer: dict) -> Finding:
        role = answer.get("category", "unsure")
        outcome = ROLE_OUTCOME.get(role, "cantTell")
        if role == "decoration" and c.extra.get("interactive"):
            outcome, role = "cantTell", "unsure"  # a link, button or label is never decoration
        kw = self._kw(c)
        key = {"content": "c143.apertus_content", "logotype": "c143.apertus_logotype",
               "decoration": "c143.apertus_decoration"}.get(role, "c143.apertus_unsure")
        if outcome == "cantTell":
            key = "c143.apertus_unsure"
        impact = {"failed": "c143.impact", "passed": "c143.impact_exempt"}.get(outcome, "impact.review")
        quote = (answer.get("quote") or "").strip()
        excerpt = quote or (c.text[:300] if c.text else htmllib.unescape(c.html[:300]))
        return self.finding(c, outcome=outcome, source="apertus",
                            confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
                            excerpt=excerpt, explanation=t(key, self.ui_lang, **kw), user_impact=t(impact, self.ui_lang),
                            reason=answer.get("reason"), reason_code=key.split(".", 1)[1],
                            **(self._fix(c) if outcome == "failed" else {}))


CHECK = ContrastMinimum
