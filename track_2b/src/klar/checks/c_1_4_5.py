"""1.4.5 Images of Text, level AA (vision). ACT rule 0va7u6 (HTML graphics contain
no text) is the closest rule.

Found in CODE (capture/js/c_1_4_5_images.js): <img>, <input type="image">,
role="img", <canvas>, inline <svg> without <text> (SVG text is real text) and
elements painted with a CSS background image (url()), of a meaningful size
(≥ 40×16 px rendered and ≥ 2000 px², icon-sized squares ≤ 48 px skipped; a background image
behind visible HTML text and an aria-hidden SVG icon inside a control are skipped too: the
first crop would show real text as if it were in the image). Facts kept
for the decision and the prompt: the text alternative, whether the graphic is the
content of a link or button (and that control's visible text), logo signals, and
whether HTML text inside a background-image element is visually hidden (CSS image
replacement). A present and correct `alt` never makes an image of text pass.

Decided in code: the SITE LOGO → passed (heuristic: logotypes are an exception), only
when all of these hold: inside the page header, links to the home page, logo-like
size (≤ 120 px high, and ≤ 400 px wide or an aspect ratio ≤ 5:1), an alternative of
at most 4 words, and either a logo/brand id or class or an alternative sharing a
word (≥ 3 letters) with the page <title>. A wide or tall header banner, a slogan
image, or any other header image goes to the model.

Asked to APERTUS (vision, crop of the graphic), every other candidate:
  Closed question: "What kind of image is this, with regard to the text in it?"
  category                 outcome      (PROTOCOL 1.4.5)
    text_only              failed       F1–F4 (heading, button label, banner, table as image)
    logotype               passed       T1 (logotypes are essential)
    text_in_picture        passed       T2/T3 (chart, map, photo: significant other content)
    specimen               passed       T4 (the look of the text is the information)
    document_facsimile     cantTell     C2 (signed or stamped original: essential or not)
    illustration_with_text cantTell     C1 (poster: no threshold in the Understanding)
    no_text                inapplicable
    unsure                 cantTell
  Consistency in code: CSS image replacement (hidden HTML text) answered no_text →
  cantTell (contradiction).
At most 6 crops per page: buttons and linked images first, then the largest; the
rest → cantTell. No vision backend → cantTell "vision backend required".

Limits: the C30 exception (a visible control that switches to real text) is not
detected; text drawn in <canvas> or as SVG paths is only seen by the model; very
small images of text (≤ 48 px squares, < 2000 px²) are skipped.
"""

from __future__ import annotations

import re

from klar.capture.page import CapturedPage
from klar.checks import colour as C
from klar.checks.base import BaseCheck, category_schema
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "1.4.5/v2"  # v2: organisation names set as a logo
VISION_CAP = 6
LOGO_MAX_H = 120  # px: a site logo is small; a taller header image may be a banner of text
LOGO_MAX_W = 400  # px, unless the aspect ratio stays within LOGO_MAX_ASPECT
LOGO_MAX_ASPECT = 5.0  # width : height
LOGO_MAX_WORDS = 4  # words in the alternative / accessible name
CATEGORIES = ["text_only", "logotype", "text_in_picture", "specimen", "document_facsimile",
              "illustration_with_text", "no_text", "unsure"]
CATEGORY_OUTCOME = {
    "text_only": "failed", "logotype": "passed", "text_in_picture": "passed", "specimen": "passed",
    "document_facsimile": "cantTell", "illustration_with_text": "cantTell", "no_text": "inapplicable",
    "unsure": "cantTell",
}

register({
    "c145.site_logo": {
        "en": "Image in the page header that links to the home page: treated as the site logo. Logotypes are an exception to 1.4.5.",
        "de": "Bild im Seitenkopf mit Link auf die Startseite: als Logo der Website behandelt. Logos sind von 1.4.5 ausgenommen.",
        "fr": "Image dans l'en-tête qui renvoie à la page d'accueil : traitée comme logo du site. Les logotypes sont une exception au critère 1.4.5.",
        "it": "Immagine nell'intestazione con link alla pagina iniziale: trattata come logo del sito. I logotipi sono un'eccezione al criterio 1.4.5.",
    },
    "c145.apertus_text_only": {
        "en": "Apertus: this image is essentially text{alt}. It should be real text styled with CSS; a text alternative does not change this.",
        "de": "Apertus: Dieses Bild besteht im Wesentlichen aus Text{alt}. Er sollte als echter, mit CSS gestalteter Text vorliegen; ein Alternativtext ändert daran nichts.",
        "fr": "Apertus : cette image est essentiellement du texte{alt}. Il devrait s'agir de vrai texte mis en forme avec CSS ; une alternative textuelle n'y change rien.",
        "it": "Apertus: questa immagine è essenzialmente testo{alt}. Dovrebbe essere vero testo formattato con CSS; un'alternativa testuale non cambia nulla.",
    },
    "c145.apertus_logotype": {
        "en": "Apertus: this image is a logo or brand name. Logotypes are an exception to 1.4.5.",
        "de": "Apertus: Dieses Bild ist ein Logo oder Markenname. Logos sind von 1.4.5 ausgenommen.",
        "fr": "Apertus : cette image est un logo ou un nom de marque. Les logotypes sont une exception au critère 1.4.5.",
        "it": "Apertus: questa immagine è un logo o un marchio. I logotipi sono un'eccezione al criterio 1.4.5.",
    },
    "c145.apertus_text_in_picture": {
        "en": "Apertus: the text is part of a chart, diagram, map or photo with significant other visual content, so this is not an image of text.",
        "de": "Apertus: Der Text ist Teil eines Diagramms, Plans, einer Karte oder eines Fotos mit wesentlichem anderem Bildinhalt; es ist kein Textbild.",
        "fr": "Apertus : le texte fait partie d'un graphique, d'un schéma, d'une carte ou d'une photo au contenu visuel important ; ce n'est pas une image de texte.",
        "it": "Apertus: il testo fa parte di un grafico, schema, mappa o foto con un contenuto visivo importante; non è un'immagine di testo.",
    },
    "c145.apertus_specimen": {
        "en": "Apertus: the particular look of the text is the information here (a sample of how it looks), which is essential.",
        "de": "Apertus: Hier ist das Aussehen des Textes selbst die Information (ein Muster, wie es aussieht); das gilt als wesentlich.",
        "fr": "Apertus : ici, l'apparence du texte est elle-même l'information (un exemple de son aspect), ce qui est essentiel.",
        "it": "Apertus: qui l'aspetto del testo è l'informazione stessa (un esempio di come appare), il che è essenziale.",
    },
    "c145.apertus_document_facsimile": {
        "en": "Apertus: this is a facsimile of a signed or stamped document. It is essential if the original's appearance matters, a failure if it only replaces the text. A person must decide.",
        "de": "Apertus: Dies ist ein Faksimile eines unterzeichneten oder gestempelten Dokuments. Wesentlich, wenn das Aussehen des Originals zählt; ein Mangel, wenn es nur den Text ersetzt. Eine Person muss entscheiden.",
        "fr": "Apertus : il s'agit du fac-similé d'un document signé ou tamponné. C'est essentiel si l'aspect de l'original compte, un défaut s'il ne fait que remplacer le texte. Une personne doit trancher.",
        "it": "Apertus: è il facsimile di un documento firmato o timbrato. È essenziale se conta l'aspetto dell'originale, un difetto se sostituisce solo il testo. Una persona deve decidere.",
    },
    "c145.apertus_illustration_with_text": {
        "en": "Apertus: a large illustration combined with substantial text. Whether this is an image of text has no fixed threshold. A person must decide.",
        "de": "Apertus: eine grosse Illustration mit viel Text. Ob es ein Textbild ist, lässt sich nicht an einem festen Schwellenwert festmachen. Eine Person muss entscheiden.",
        "fr": "Apertus : une grande illustration accompagnée de beaucoup de texte. Il n'existe pas de seuil fixe pour dire s'il s'agit d'une image de texte. Une personne doit trancher.",
        "it": "Apertus: una grande illustrazione con molto testo. Non esiste una soglia fissa per dire se è un'immagine di testo. Una persona deve decidere.",
    },
    "c145.apertus_no_text": {
        "en": "Apertus: this image contains no text.",
        "de": "Apertus: Dieses Bild enthält keinen Text.",
        "fr": "Apertus : cette image ne contient pas de texte.",
        "it": "Apertus: questa immagine non contiene testo.",
    },
    "c145.apertus_unsure": {
        "en": "Apertus could not tell whether this image is an image of text. A person must check it.",
        "de": "Apertus konnte nicht beurteilen, ob dies ein Textbild ist. Eine Person muss es prüfen.",
        "fr": "Apertus n'a pas pu dire s'il s'agit d'une image de texte. Une personne doit vérifier.",
        "it": "Apertus non ha potuto stabilire se si tratta di un'immagine di testo. Una persona deve verificare.",
    },
    "c145.apertus_contradiction": {
        "en": "The HTML text of this element is hidden and replaced by a background image, yet Apertus saw no text in it. A person must check it.",
        "de": "Der HTML-Text dieses Elements ist versteckt und durch ein Hintergrundbild ersetzt, Apertus hat darin aber keinen Text erkannt. Eine Person muss es prüfen.",
        "fr": "Le texte HTML de cet élément est masqué et remplacé par une image de fond, mais Apertus n'y a vu aucun texte. Une personne doit vérifier.",
        "it": "Il testo HTML di questo elemento è nascosto e sostituito da un'immagine di sfondo, ma Apertus non vi ha visto testo. Una persona deve verificare.",
    },
    "c145.over_cap": {
        "en": "This image may contain text, but the per-page limit of image questions is reached. A person must check it.",
        "de": "Dieses Bild könnte Text enthalten, aber die Höchstzahl an Bildfragen pro Seite ist erreicht. Eine Person muss es prüfen.",
        "fr": "Cette image peut contenir du texte, mais la limite de questions sur image par page est atteinte. Une personne doit vérifier.",
        "it": "Questa immagine potrebbe contenere testo, ma il limite di domande su immagini per pagina è raggiunto. Una persona deve verificare.",
    },
    "c145.alt_part": {"en": " (alternative: «{alt}»)", "de": " (Alternativtext: «{alt}»)", "fr": " (alternative : «{alt}»)",
                      "it": " (alternativa: «{alt}»)"},
    "c145.impact": {
        "en": "People with low vision who enlarge text, change fonts, colours or spacing cannot adapt text inside an image; it blurs when zoomed.",
        "de": "Menschen mit Sehbehinderung, die Text vergrössern oder Schrift, Farben und Abstände anpassen, können Text in einem Bild nicht anpassen; beim Zoomen wird er unscharf.",
        "fr": "Les personnes malvoyantes qui agrandissent le texte ou adaptent police, couleurs et espacements ne peuvent pas adapter le texte d'une image ; il devient flou au zoom.",
        "it": "Le persone ipovedenti che ingrandiscono il testo o adattano carattere, colori e spaziature non possono adattare il testo in un'immagine; ingrandito diventa sfocato.",
    },
    "c145.impact_ok": {
        "en": "No adaptable text is locked inside this image.",
        "de": "In diesem Bild ist kein anpassbarer Text eingeschlossen.",
        "fr": "Aucun texte adaptable n'est enfermé dans cette image.",
        "it": "In questa immagine non è racchiuso testo adattabile.",
    },
    "c145.fix_hint": {
        "en": "Replace the image with real text styled with CSS (web font, colours, a background image without text).",
        "de": "Ersetzen Sie das Bild durch echten, mit CSS gestalteten Text (Webfont, Farben, Hintergrundbild ohne Text).",
        "fr": "Remplacez l'image par du vrai texte mis en forme avec CSS (police web, couleurs, image de fond sans texte).",
        "it": "Sostituite l'immagine con vero testo formattato con CSS (font web, colori, immagine di sfondo senza testo).",
    },
})


# Real HTML text must cover at least this share of a background picture's box for the crop to be
# skipped (a heading or teaser over a photo); a small button over a hero picture keeps it.
MIN_TEXT_SHARE = 0.1


class ImagesOfText(BaseCheck):
    criterion = "1.4.5"
    prompt_version = PROMPT_VERSION
    needs_vision = True
    guard_numbers = False  # numbers are read off the image
    max_candidates = 80
    prompt_html_chars = 300

    # -- 1. candidates ------------------------------------------------------------------
    def candidates(self, page: CapturedPage) -> list[Candidate]:
        out: list[Candidate] = []
        for rec in C.records(page, "c145_images", "c_1_4_5_images.js")[: self.max_candidates]:
            if (rec.get("kind") == "background" and rec.get("visible_text") and not rec.get("hidden_text")
                    and (rec.get("text_share") or 0) >= MIN_TEXT_SHARE):
                continue  # real HTML text over a picture: its crop would show that text as if it were in the image
            alt = rec.get("alt")
            name = " ".join((alt if alt is not None else (rec.get("label") or "")).split())
            brand = list(rec.get("brand") or [])
            r = rec.get("rect") or {}
            kind = "site_logo" if self.site_logo(brand, r, name, page.title) else "ask"
            ctx = {}
            if rec.get("in_control"):
                ctx["inside"] = "a link or button" + (f" with visible text: {rec['control_text']}"
                                                       if rec.get("control_text") else " (its only content)")
            if rec.get("hidden_text"):
                ctx["hidden_html_text"] = rec["hidden_text"][:200]
            pos = [s.replace("_", " ") for s in brand if s != "logo_class_or_id"]
            if pos:
                ctx["position"] = ", ".join(pos)
            out.append(self.candidate(
                page, selector=rec["selector"], html=rec.get("html", ""), text=name, accessible_name=name,
                context=ctx, lang=rec.get("lang"), kind=kind, tag=rec.get("tag"), source_kind=rec.get("kind"),
                alt_present=alt is not None, in_control=bool(rec.get("in_control")),
                hidden_text=rec.get("hidden_text", ""), area=r.get("w", 0) * r.get("h", 0),
                input_image="type=\"image\"" in (rec.get("html") or "")[:200],
            ))
        asks = [c for c in out if c.extra["kind"] == "ask"]
        asks.sort(key=lambda c: (not (c.extra["in_control"] or c.extra["input_image"]), bool(c.extra["hidden_text"]) is False,
                                 -c.extra["area"]))
        for i, c in enumerate(asks):
            if i >= VISION_CAP:
                c.extra["kind"] = "over_cap"
            elif self.vision:
                c.screenshot = page.screenshot(c.selector, c.id)
                c.extra["screenshot_failed"] = c.screenshot is None
        return out

    @staticmethod
    def site_logo(brand: list[str], rect: dict, name: str, title: str) -> bool:
        w, h = rect.get("w", 0), rect.get("h", 0)
        if not {"links_to_home_page", "in_page_header"} <= set(brand) or not 0 < h <= LOGO_MAX_H:
            return False
        if not (w <= LOGO_MAX_W or w <= LOGO_MAX_ASPECT * h):
            return False  # a wide strip: a slogan or welcome banner, not a logo
        if len(name.split()) > LOGO_MAX_WORDS:
            return False  # a sentence-long alternative describes a banner, not a brand mark
        if "logo_class_or_id" in brand:
            return True
        words = lambda s: {w for w in re.findall(r"\w{3,}", (s or "").casefold())}  # noqa: E731
        return bool(words(name) & words(title))

    # -- 2. deterministic decisions ----------------------------------------------------------
    def decide(self, c: Candidate) -> Finding | None:
        kind, ui = c.extra.get("kind"), self.ui_lang
        if kind == "site_logo":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", reason_code=kind,
                                excerpt=self._excerpt(c), explanation=t("c145.site_logo", ui),
                                user_impact=t("c145.impact_ok", ui), act_rule=None)
        if kind == "over_cap":
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="low", reason_code=kind,
                                excerpt=self._excerpt(c), explanation=t("c145.over_cap", ui),
                                user_impact=t("impact.review", ui), act_rule=None)
        if kind == "ask" and self.vision and c.extra.get("screenshot_failed"):
            return self.note(c, "note.no_screenshot")
        return None

    @staticmethod
    def _excerpt(c: Candidate) -> str:
        alt = c.accessible_name or ""
        if c.extra.get("alt_present") and alt and f'alt="{alt}"' in c.html:
            return f'alt="{alt}"'
        return alt if alt and alt in c.html else c.html[:300]

    # -- 3. the closed question (vision) --------------------------------------------------------
    SYSTEM = (
        "You check WCAG 2.1 success criterion 1.4.5 Images of Text for ONE image (attached crop). An image of text "
        "is text rendered as a picture although it could be real text styled with CSS. A correct text alternative "
        "does not change the answer.\n"
        "category: text_only = the image is essentially text (a heading, a button or link label, an announcement or "
        "banner, a price list or timetable); logotype = a logo or brand name, including the name of an organisation set in its logo design; text_in_picture = the text is part of "
        "a chart, diagram, map, screenshot or photo with significant other visual content; specimen = the particular "
        "look of the text is the information (a font sample, what a printed item or a sign looks like); "
        "document_facsimile = a scan or facsimile of a signed or stamped document; illustration_with_text = a large "
        "illustration combined with substantial text, in about equal measure; no_text = the image contains no text; "
        "unsure = cannot tell.\n"
        "quote: the text alternative exactly as written in the page data, or an empty string."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        # ui_lang is deliberately unused: prompts are identical for every UI language.
        return self.task(
            system=self.system_prompt(self.SYSTEM, c),
            element={"tag": c.extra.get("tag") or "", "alternative": c.accessible_name or "", "html": self.prompt_html(c)},
            context=c.context,
            images=[c.screenshot] if c.screenshot else [],
            question="What kind of image is this, with regard to the text in it?",
            schema=category_schema(CATEGORIES),
            max_tokens=120,
        )

    # -- 4. interpretation ----------------------------------------------------------------------
    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        cat = answer.get("category", "unsure")
        if cat not in CATEGORY_OUTCOME:
            cat = "unsure"
        outcome = CATEGORY_OUTCOME[cat]
        key = f"c145.apertus_{cat}"
        if cat == "no_text" and c.extra.get("hidden_text"):
            outcome, key = "cantTell", "c145.apertus_contradiction"
        alt = c.accessible_name or ""
        alt_part = t("c145.alt_part", ui, alt=alt) if alt else ""
        impact = {"failed": "c145.impact", "passed": "c145.impact_ok", "inapplicable": "c145.impact_ok"}.get(
            outcome, "impact.review")
        quote = (answer.get("quote") or "").strip()
        excerpt = quote if quote and quote != 'alt=""' else self._excerpt(c)
        return self.finding(c, outcome=outcome, source="apertus",
                            confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
                            excerpt=excerpt, explanation=t(key, ui, alt=alt_part), user_impact=t(impact, ui),
                            reason=answer.get("reason"), reason_code=key.split(".", 1)[1],
                            fix_hint=t("c145.fix_hint", ui) if outcome == "failed" else None,
                            act_rule=None)


CHECK = ImagesOfText
