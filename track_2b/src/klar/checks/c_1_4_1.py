"""1.4.1 Use of Color, level A (vision for colour coding). No ACT rule maps to
1.4.1; the link part follows axe-core `link-in-text-block` and techniques G183 / F73 (a measured finding on the
same link replaces axe's: same selector, source "rule").

Measured in CODE (capture/js/c_1_4_1_colour.js + checks/colour.py):
  1. Links inside a block of text (the block has ≥ 12 letters outside links; links in
     navigation, header, footer, menus and link lists are out of scope, PROTOCOL T3):
       a non-colour cue at rest (underline or other text decoration, border, outline,
       box-shadow, background, font weight / style / family / size, text-transform,
       an icon or ::before/::after content)       → passed (rule, G182)
       no cue, link vs surrounding text ≥ 3:1     → passed (rule, G183; lightness counts)
       no cue, link vs surrounding text < 3:1     → failed (rule, F73)
     A hover-only underline is not a cue (the link must be findable without pointing).
  2. Groups with a selected / pressed / current / checked member (aria-pressed,
     aria-selected, aria-current, aria-checked): style of the "on" member vs an "off" one.
       any non-colour difference (decoration, border shape, weight, size, icon…)
                                                  → passed (heuristic)
       colours only, on/off fill or text differ ≥ 3:1 (inverted scheme)
                                                  → cantTell (heuristic, PROTOCOL 1.4.1/C2)
       colours only, < 3:1 (a hue of similar lightness)
                                                  → failed (heuristic, F4 pattern)
  3. Candidates for colour coding: tables, lists and forms where some items carry a
     saturated text, background or border colour that other items lack (header cells
     excluded), and graphics ≥ 120×80 px whose crop has ≥ 3 distinct saturated flat
     colours (charts, maps, legends: palette measured on the screenshot in code).

Asked to APERTUS (vision, crop of the group or graphic; code facts in the context:
how many items are coloured and how many of them have no text):
  Closed question: "Is information in this part of the page conveyed by colour alone?"
  category: colour_only → failed · redundant → passed · no_meaning → passed ·
            unclear → cantTell (PROTOCOL 1.4.1/C1: meaning of the colour not stated)
At most 6 crops per page (largest first); the rest → cantTell.
No vision backend → cantTell "vision backend required" (pipeline, needs_vision).

Limits: colour coding in running text outside lists/tables/forms is not searched;
links inside navigation-like regions are skipped by design; text decoration
inherited from an ancestor is not distinguished from the link's own; a legend that
explains colour swatches is judged by the model, not in code; states set only by
a class name (no ARIA state) are not compared.
"""

from __future__ import annotations

from klar.capture.page import CapturedPage
from klar.checks import colour as C
from klar.checks.base import BaseCheck, category_schema, in_element
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "1.4.1/v1"
VISION_CAP = 6
PASSES_PER_CUE = 3
GRAPHIC_SAMPLE_CAP = 12
CATEGORIES = ["colour_only", "redundant", "no_meaning", "unclear"]
CATEGORY_OUTCOME = {"colour_only": "failed", "redundant": "passed", "no_meaning": "passed", "unclear": "cantTell"}

register({
    "c141.link_cue": {
        "en": "The link is set apart from the surrounding text by more than colour ({cues}).",
        "de": "Der Link hebt sich nicht nur durch die Farbe vom umgebenden Text ab ({cues}).",
        "fr": "Le lien se distingue du texte qui l'entoure par autre chose que la couleur ({cues}).",
        "it": "Il link si distingue dal testo circostante non solo per il colore ({cues}).",
    },
    "c141.link_contrast_ok": {
        "en": "The link has no underline, but its colour has a contrast of {ratio} with the surrounding text (at least 3:1): {link} vs {text}.",
        "de": "Der Link ist nicht unterstrichen, aber seine Farbe unterscheidet sich vom umgebenden Text um {ratio} (mindestens 3:1): {link} gegenüber {text}.",
        "fr": "Le lien n'est pas souligné, mais le contraste entre sa couleur et celle du texte environnant est de {ratio} (au moins 3:1) : {link} contre {text}.",
        "it": "Il link non è sottolineato, ma il suo colore differisce dal testo circostante di {ratio} (almeno 3:1): {link} rispetto a {text}.",
    },
    "c141.link_colour_only": {
        "en": "The link inside the text is marked only by its colour: no underline or other cue, and only {ratio} against the surrounding text (3:1 needed): {link} vs {text}.",
        "de": "Der Link im Text ist nur durch seine Farbe erkennbar: keine Unterstreichung oder andere Markierung und nur {ratio} gegenüber dem umgebenden Text (nötig sind 3:1): {link} gegenüber {text}.",
        "fr": "Le lien dans le texte n'est signalé que par sa couleur : ni soulignement ni autre indice, et seulement {ratio} par rapport au texte environnant (3:1 requis) : {link} contre {text}.",
        "it": "Il link nel testo è segnalato solo dal colore: nessuna sottolineatura o altro indizio e solo {ratio} rispetto al testo circostante (serve 3:1): {link} rispetto a {text}.",
    },
    "c141.state_cue": {
        "en": "The active item differs from the others by more than colour ({cues}).",
        "de": "Das aktive Element unterscheidet sich nicht nur durch die Farbe von den anderen ({cues}).",
        "fr": "L'élément actif se distingue des autres par autre chose que la couleur ({cues}).",
        "it": "L'elemento attivo si distingue dagli altri non solo per il colore ({cues}).",
    },
    "c141.state_inverted": {
        "en": "The active item (“{on}”) is shown only by an inverted colour scheme ({ratio} between active and inactive). Lightness counts as a cue, but with no shape, mark or underline the meaning rests on a convention. A person must decide.",
        "de": "Das aktive Element («{on}») ist nur durch ein umgekehrtes Farbschema erkennbar ({ratio} zwischen aktiv und inaktiv). Helligkeit zählt als Hinweis, ohne Form, Zeichen oder Unterstreichung beruht die Bedeutung aber auf einer Konvention. Eine Person muss entscheiden.",
        "fr": "L'élément actif (« {on} ») n'est signalé que par des couleurs inversées ({ratio} entre actif et inactif). La luminosité compte comme indice, mais sans forme, marque ni soulignement, le sens repose sur une convention. Une personne doit trancher.",
        "it": "L'elemento attivo («{on}») è indicato solo da uno schema di colori invertito ({ratio} tra attivo e inattivo). La luminosità conta come indizio, ma senza forma, segno o sottolineatura il significato si basa su una convenzione. Una persona deve decidere.",
    },
    "c141.state_hue_only": {
        "en": "The active item (“{on}”) differs from the others only by a colour of similar lightness ({ratio}, 3:1 needed), with no shape, mark or underline.",
        "de": "Das aktive Element («{on}») unterscheidet sich von den anderen nur durch eine Farbe ähnlicher Helligkeit ({ratio}, nötig sind 3:1), ohne Form, Zeichen oder Unterstreichung.",
        "fr": "L'élément actif (« {on} ») ne se distingue des autres que par une couleur de luminosité semblable ({ratio}, 3:1 requis), sans forme, marque ni soulignement.",
        "it": "L'elemento attivo («{on}») si distingue dagli altri solo per un colore di luminosità simile ({ratio}, serve 3:1), senza forma, segno o sottolineatura.",
    },
    "c141.apertus_colour_only": {
        "en": "Apertus: in this {what}, some information is given by colour alone ({facts}).",
        "de": "Apertus: In diesem Bereich ({what}) wird eine Information nur durch Farbe vermittelt ({facts}).",
        "fr": "Apertus : dans cette zone ({what}), une information n'est donnée que par la couleur ({facts}).",
        "it": "Apertus: in questa zona ({what}) un'informazione è data solo dal colore ({facts}).",
    },
    "c141.apertus_redundant": {
        "en": "Apertus: colour is used in this {what}, but text, symbols, patterns or labels give the same information.",
        "de": "Apertus: In diesem Bereich ({what}) wird Farbe verwendet, aber Text, Symbole, Muster oder Beschriftungen vermitteln dieselbe Information.",
        "fr": "Apertus : la couleur est utilisée dans cette zone ({what}), mais du texte, des symboles, des motifs ou des étiquettes donnent la même information.",
        "it": "Apertus: in questa zona ({what}) si usa il colore, ma testo, simboli, motivi o etichette danno la stessa informazione.",
    },
    "c141.apertus_no_meaning": {
        "en": "Apertus: the colour in this {what} is decoration or emphasis and carries no information.",
        "de": "Apertus: Die Farbe in diesem Bereich ({what}) ist Dekoration oder Hervorhebung und trägt keine Information.",
        "fr": "Apertus : la couleur de cette zone ({what}) est décorative ou sert à souligner, elle ne porte aucune information.",
        "it": "Apertus: il colore in questa zona ({what}) è decorazione o enfasi e non trasmette informazioni.",
    },
    "c141.apertus_unclear": {
        "en": "Apertus: the colour in this {what} seems to mean something, but the page does not say what ({facts}). A person must check it.",
        "de": "Apertus: Die Farbe in diesem Bereich ({what}) scheint etwas zu bedeuten, die Seite sagt aber nicht, was ({facts}). Eine Person muss es prüfen.",
        "fr": "Apertus : la couleur de cette zone ({what}) semble signifier quelque chose, mais la page ne dit pas quoi ({facts}). Une personne doit vérifier.",
        "it": "Apertus: il colore in questa zona ({what}) sembra significare qualcosa, ma la pagina non dice cosa ({facts}). Una persona deve verificare.",
    },
    "c141.over_cap": {
        "en": "Colour may carry information here ({facts}), but the per-page limit of image questions is reached. A person must check it.",
        "de": "Hier vermittelt Farbe möglicherweise Information ({facts}), aber die Höchstzahl an Bildfragen pro Seite ist erreicht. Eine Person muss es prüfen.",
        "fr": "La couleur porte peut-être une information ici ({facts}), mais la limite de questions sur image par page est atteinte. Une personne doit vérifier.",
        "it": "Qui il colore potrebbe trasmettere informazioni ({facts}), ma il limite di domande su immagini per pagina è raggiunto. Una persona deve verificare.",
    },
    "c141.facts": {
        "en": "{marked} of {items} items coloured, {empty} of them without text",
        "de": "{marked} von {items} Elementen farbig, davon {empty} ohne Text",
        "fr": "{marked} éléments colorés sur {items}, dont {empty} sans texte",
        "it": "{marked} elementi colorati su {items}, di cui {empty} senza testo",
    },
    "c141.facts_graphic": {
        "en": "{n} distinct colours in the graphic",
        "de": "{n} verschiedene Farben in der Grafik",
        "fr": "{n} couleurs distinctes dans le graphique",
        "it": "{n} colori distinti nel grafico",
    },
    "c141.what.table": {"en": "table", "de": "Tabelle", "fr": "tableau", "it": "tabella"},
    "c141.what.list": {"en": "list", "de": "Liste", "fr": "liste", "it": "elenco"},
    "c141.what.form": {"en": "form", "de": "Formular", "fr": "formulaire", "it": "modulo"},
    "c141.what.graphic": {"en": "graphic", "de": "Grafik", "fr": "graphique", "it": "grafico"},
    "c141.impact": {
        "en": "People who cannot tell these colours apart (colour-vision deficiency, low vision, monochrome screens) miss this information.",
        "de": "Wer diese Farben nicht unterscheiden kann (Farbsehschwäche, Sehbehinderung, Graustufen-Bildschirm), verpasst diese Information.",
        "fr": "Les personnes qui ne distinguent pas ces couleurs (trouble de la vision des couleurs, malvoyance, écran monochrome) n'ont pas accès à cette information.",
        "it": "Chi non distingue questi colori (deficit nella visione dei colori, ipovisione, schermo monocromatico) perde questa informazione.",
    },
    "c141.impact_link": {
        "en": "People with colour-vision deficiency may not see that this text is a link.",
        "de": "Menschen mit Farbsehschwäche erkennen eventuell nicht, dass dieser Text ein Link ist.",
        "fr": "Les personnes ayant un trouble de la vision des couleurs risquent de ne pas voir que ce texte est un lien.",
        "it": "Le persone con un deficit nella visione dei colori potrebbero non accorgersi che questo testo è un link.",
    },
    "c141.impact_ok": {
        "en": "People who do not see colours can still get this information.",
        "de": "Auch wer keine Farben sieht, erhält diese Information.",
        "fr": "Les personnes qui ne voient pas les couleurs obtiennent tout de même cette information.",
        "it": "Anche chi non vede i colori ottiene questa informazione.",
    },
    "c141.fix_hint_link": {
        "en": "Underline links in running text (text-decoration: underline), or make the link colour differ from the text by at least 3:1.",
        "de": "Unterstreichen Sie Links im Fliesstext (text-decoration: underline) oder wählen Sie eine Linkfarbe mit mindestens 3:1 Kontrast zum Text.",
        "fr": "Soulignez les liens dans le texte courant (text-decoration: underline) ou choisissez une couleur de lien d'au moins 3:1 par rapport au texte.",
        "it": "Sottolineate i link nel testo corrente (text-decoration: underline) o scegliete un colore del link con almeno 3:1 rispetto al testo.",
    },
    "c141.fix_hint_state": {
        "en": "Add a non-colour mark to the active item: a check mark, an underline, a bold label or a thicker border.",
        "de": "Ergänzen Sie das aktive Element um ein Merkmal, das nicht auf Farbe beruht: ein Häkchen, eine Unterstreichung, fette Schrift oder einen dickeren Rahmen.",
        "fr": "Ajoutez à l'élément actif un repère autre que la couleur : une coche, un soulignement, un libellé en gras ou une bordure plus épaisse.",
        "it": "Aggiungete all'elemento attivo un segno non cromatico: un segno di spunta, una sottolineatura, un'etichetta in grassetto o un bordo più spesso.",
    },
    "c141.fix_hint": {
        "en": "Repeat the information that the colour carries in text, a symbol, a pattern or a direct label.",
        "de": "Geben Sie die Information, die die Farbe vermittelt, zusätzlich als Text, Symbol, Muster oder direkte Beschriftung wieder.",
        "fr": "Répétez l'information portée par la couleur sous forme de texte, de symbole, de motif ou d'étiquette directe.",
        "it": "Ripetete l'informazione data dal colore con un testo, un simbolo, un motivo o un'etichetta diretta.",
    },
})

CUE_WORDS = {
    "text_decoration": {"en": "underline", "de": "Unterstreichung", "fr": "soulignement", "it": "sottolineatura"},
    "font_weight": {"en": "bold", "de": "fett", "fr": "gras", "it": "grassetto"},
}


class UseOfColor(BaseCheck):
    criterion = "1.4.1"
    prompt_version = PROMPT_VERSION
    needs_vision = True
    guard_numbers = False  # values may be read off a chart
    max_candidates = 200
    prompt_html_chars = 400

    # -- 1. candidates ------------------------------------------------------------------
    def candidates(self, page: CapturedPage) -> list[Candidate]:
        links = C.records(page, "c141_links", "c_1_4_1_colour.js")
        axe = C.axe_nodes(page, "link-in-text-block")
        out: list[Candidate] = []
        per_cue: dict[str, int] = {}
        for rec in links:
            m = self.measure_link(rec)
            if m is None:
                continue
            if m["kind"] == "link_cue":
                key = ",".join(m["cues"])
                per_cue[key] = per_cue.get(key, 0) + 1
                if per_cue[key] > PASSES_PER_CUE:
                    continue
            if rec["selector"] in axe:
                m["axe"] = axe[rec["selector"]]["group"]
            ctx = {"sentence": rec.get("sentence", "")}
            out.append(self.candidate(page, selector=rec["selector"], html=rec.get("html", ""), text=rec.get("text", ""),
                                      accessible_name=rec.get("text"), context=ctx, lang=rec.get("lang"), **m))
        for rec in page.elements.get("c141_links.states", []):
            m = self.measure_state(rec)
            if m:
                out.append(self.candidate(page, selector=rec["selector"], html=rec.get("html", ""),
                                          text=rec.get("text", ""), lang=rec.get("lang"), key="#state", **m))
        asks: list[Candidate] = []
        for rec in page.elements.get("c141_links.groups", []):
            what = {"table": "table", "form": "form", "fieldset": "form"}.get(rec.get("tag", ""), "list")
            r = rec.get("rect") or {}
            asks.append(self.candidate(page, selector=rec["selector"], html=rec.get("html", ""), text=rec.get("text", ""),
                                       lang=rec.get("lang"), key="#group", kind="ask", what=what,
                                       items=rec.get("items", 0), marked=rec.get("marked", 0),
                                       empty=rec.get("marked_without_text", 0), colours=rec.get("colours", []),
                                       area=r.get("w", 0) * r.get("h", 0)))
        sampled = 0
        for rec in page.elements.get("c141_links.graphics", []):
            if page.live is None or sampled >= GRAPHIC_SAMPLE_CAP:
                break
            sampled += 1
            cand = self.candidate(page, selector=rec["selector"], html=rec.get("html", ""), text=rec.get("alt", ""),
                                  accessible_name=rec.get("alt"), context={"caption": rec.get("caption", "")},
                                  lang=rec.get("lang"), key="#graphic", kind="ask", what="graphic")
            shot = page.screenshot(rec["selector"], cand.id)
            bm = C.load_crop(page, shot)
            if bm is None:
                continue
            pal = C.palette(bm, step=2 if bm.w * bm.h > 200_000 else 1)
            if pal.distinct_saturated < 3 or pal.flat_share < 0.5:
                continue  # a photo, or a graphic without colour coding
            r = rec.get("rect") or {}
            cand.screenshot = shot
            cand.extra.update(n_colours=pal.distinct_saturated, area=r.get("w", 0) * r.get("h", 0))
            asks.append(cand)
        asks.sort(key=lambda c: -c.extra.get("area", 0))
        for i, cand in enumerate(asks):
            if i >= VISION_CAP:
                cand.extra["kind"] = "over_cap"
            elif self.vision and not cand.screenshot:
                cand.screenshot = page.screenshot(cand.selector, cand.id)
                cand.extra["screenshot_failed"] = cand.screenshot is None
        return out + asks

    @staticmethod
    def measure_link(rec: dict) -> dict | None:
        link, text = C.parse_color(rec.get("color")), C.parse_color(rec.get("text_color"))
        if link is None or text is None:
            return None
        colours = []
        for layer in rec.get("layers") or []:
            c = C.parse_color(layer.get("c"))
            if layer.get("media") or layer.get("img") or c is None:
                colours = None
                break
            colours.append(c)
        bg = C.composite(colours) if colours is not None else C.WHITE
        lc, tc = C.over(link, bg), C.over(text, bg)
        ratio = C.contrast(lc, tc)
        cues = [x for x in rec.get("cues") or []]
        base = dict(ratio=round(ratio, 4), link=C.hex_of(lc), text_colour=C.hex_of(tc), cues=cues,
                    link_vs_bg=round(C.contrast(lc, bg), 4))
        if cues:
            return {**base, "kind": "link_cue"}
        return {**base, "kind": "link_contrast_ok" if ratio >= C.LINK_TEXT_MIN else "link_colour_only"}

    @staticmethod
    def measure_state(rec: dict) -> dict | None:
        diffs = list(rec.get("diffs") or [])
        on_fg, off_fg = C.parse_color(rec.get("on_color")), C.parse_color(rec.get("off_color"))
        layers_ok = True
        bgs = []
        for key in ("on_layers", "off_layers"):
            cols = []
            for layer in rec.get(key) or []:
                c = C.parse_color(layer.get("c"))
                if layer.get("media") or layer.get("img") or c is None:
                    layers_ok = False
                    break
                cols.append(c)
            bgs.append(C.composite(cols))
        base = dict(on=rec.get("on_text", ""), off=rec.get("off_text", ""), cues=diffs, attr=rec.get("attr"))
        if diffs:
            return {**base, "kind": "state_cue"}
        if on_fg is None or off_fg is None or not layers_ok:
            return None
        on_bg, off_bg = bgs
        fill = C.contrast(on_bg, off_bg)
        fg = C.contrast(C.over(on_fg, on_bg), C.over(off_fg, off_bg))
        ratio = max(fill, fg)
        if on_bg == off_bg and fg < 1.05:
            return None  # no visible difference at all: not a colour cue either
        return {**base, "ratio": round(ratio, 4), "kind": "state_inverted" if ratio >= C.NON_TEXT_MIN else "state_hue_only"}

    # -- 2. deterministic decisions ----------------------------------------------------------
    def _cues(self, cues: list[str]) -> str:
        names = []
        for c in cues:
            k = c.split(":")[0].split("::")[0]
            names.append(CUE_WORDS.get(k, {}).get(self.ui_lang, k.replace("_", " ")))
        return ", ".join(dict.fromkeys(names))

    def _facts(self, c: Candidate) -> str:
        x = c.extra
        if x.get("what") == "graphic":
            return t("c141.facts_graphic", self.ui_lang, n=x.get("n_colours", "≥ 3"))
        return t("c141.facts", self.ui_lang, marked=x.get("marked", 0), items=x.get("items", 0), empty=x.get("empty", 0))

    def decide(self, c: Candidate) -> Finding | None:
        x, ui, kind = c.extra, self.ui_lang, c.extra.get("kind")
        excerpt = c.text if c.text and in_element(c, c.text) else None
        if kind == "link_cue":
            return self.finding(c, outcome="passed", source="rule", confidence="high", reason_code=kind, excerpt=excerpt,
                                explanation=t("c141.link_cue", ui, cues=self._cues(x["cues"])),
                                user_impact=t("c141.impact_ok", ui))
        if kind in ("link_contrast_ok", "link_colour_only"):
            failed = kind == "link_colour_only"
            return self.finding(c, outcome="failed" if failed else "passed", source="rule",
                                confidence="high" if failed else "medium", reason_code=kind, excerpt=excerpt,
                                explanation=t(f"c141.{kind}", ui, ratio=C.fmt_ratio(x["ratio"], 3.0), link=x["link"],
                                              text=x["text_colour"]),
                                user_impact=t("c141.impact_link" if failed else "c141.impact_ok", ui),
                                fix_hint=t("c141.fix_hint_link", ui) if failed else None)
        if kind == "state_cue":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", reason_code=kind,
                                explanation=t("c141.state_cue", ui, cues=self._cues(x["cues"])),
                                user_impact=t("c141.impact_ok", ui))
        if kind == "state_inverted":
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="low", reason_code=kind,
                                explanation=t("c141.state_inverted", ui, on=x.get("on", ""), ratio=C.fmt_ratio(x["ratio"])),
                                user_impact=t("impact.review", ui), fix_hint=t("c141.fix_hint_state", ui))
        if kind == "state_hue_only":
            return self.finding(c, outcome="failed", source="heuristic", confidence="medium", reason_code=kind,
                                explanation=t("c141.state_hue_only", ui, on=x.get("on", ""),
                                              ratio=C.fmt_ratio(x["ratio"], 3.0)),
                                user_impact=t("c141.impact", ui), fix_hint=t("c141.fix_hint_state", ui))
        if kind == "over_cap":
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="low", reason_code=kind,
                                explanation=t("c141.over_cap", ui, facts=self._facts(c)), user_impact=t("impact.review", ui))
        if kind == "ask" and self.vision and (x.get("screenshot_failed") or not c.screenshot):
            return self.note(c, "note.no_screenshot")
        return None

    # -- 3. the closed question (vision) --------------------------------------------------------
    SYSTEM = (
        "You check WCAG 2.1 success criterion 1.4.1 Use of Color for ONE part of a web page (attached crop): a chart, "
        "map, table, list or form in which colour is used. Information must not be conveyed by colour alone.\n"
        "category: colour_only = some information (a status, category, selection, required or invalid field, data "
        "series or zone) is shown only by colour, with no text, symbol, pattern, shape or direct label that gives the "
        "same information (a legend of colour swatches alone does not count); redundant = text, symbols, patterns, "
        "shapes or direct labels also give the information that the colour gives; no_meaning = the colour is "
        "decoration or emphasis and carries no information; unclear = the colour seems to mean something, but the "
        "page does not say what.\n"
        "quote: the text of one coloured item exactly as written in the page data, or an empty string."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        # ui_lang is deliberately unused: prompts are identical for every UI language.
        x = c.extra
        what = x.get("what", "list")
        if what == "graphic":
            element = {"kind": "graphic", "alternative": c.accessible_name or "", "html": self.prompt_html(c)}
            ctx = {**c.context, "colours_measured": f"{x.get('n_colours', 3)} distinct saturated colours"}
        else:
            element = {"kind": what, "text": c.text[:500], "html": self.prompt_html(c)}
            ctx = {"coloured_items": f"{x.get('marked', 0)} of {x.get('items', 0)} items, "
                                     f"{x.get('empty', 0)} of them without text"}
        return self.task(system=self.system_prompt(self.SYSTEM, c), element=element, context=ctx,
                         images=[c.screenshot] if c.screenshot else [],
                         question="Is information in this part of the page conveyed by colour alone?",
                         schema=category_schema(CATEGORIES), max_tokens=140)

    # -- 4. interpretation ----------------------------------------------------------------------
    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        cat = answer.get("category", "unclear")
        outcome = CATEGORY_OUTCOME.get(cat, "cantTell")
        if cat not in CATEGORY_OUTCOME:
            cat = "unclear"
        what = t(f"c141.what.{c.extra.get('what', 'list')}", ui)
        impact = {"failed": "c141.impact", "passed": "c141.impact_ok"}.get(outcome, "impact.review")
        return self.finding(c, outcome=outcome, source="apertus",
                            confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
                            excerpt=self.model_excerpt(c, answer, outcome) or (c.accessible_name or c.html[:300]),
                            explanation=t(f"c141.apertus_{cat}", ui, what=what, facts=self._facts(c)),
                            user_impact=t(impact, ui), reason=answer.get("reason"), reason_code=f"apertus_{cat}",
                            fix_hint=t("c141.fix_hint", ui) if outcome == "failed" else None)


CHECK = UseOfColor
