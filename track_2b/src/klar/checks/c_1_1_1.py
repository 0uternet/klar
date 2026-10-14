"""1.1.1 Non-text Content, level A (vision). ACT rule qt1vmo (image accessible
name is descriptive); presence rules (23a2a8, 59796f, 7d6734) are axe-core's job.

Candidates: <img>, <input type="image">, role="img" (incl. <svg role="img">), <area>.

Cascade
  1. no accessible name and not marked decorative   → not ours: axe-core (image-alt,
                                                       input-image-alt, role-img-alt,
                                                       svg-img-alt, area-alt)
  2. marked decorative but it is the ONLY content of a link/button (F89)
                                                     → failed (heuristic)
     marked decorative (alt="", role=presentation/none, aria-hidden) and tiny
                                                     → passed (heuristic)
  3. marked decorative inside a link/button with text → skipped: the text names the control
  4. alternative is a file name ("IMG_2041.jpg")     → failed (heuristic)
  5. alternative is a placeholder word ("Bild", "image", "logo")
                                                     → failed (heuristic)
  6. everything else                                 → Apertus VISION: crop + current
     alternative + minimal context (caption, link destination, surrounding text).
     Categorical first (decorative | informative | functional | complex | text),
     then the verdict, then a proposed alternative in the content language.
  No vision backend → cantTell "vision backend required" (pipeline, needs_vision=True).
"""

from __future__ import annotations

import re
import unicodedata

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, set_attr, unified_diff, useful_fix, verdict_schema
from klar.i18n import t
from klar.models import Candidate, Finding, LLMTask

# v2: page data block, English reason, explanations from i18n.
PROMPT_VERSION = "1.1.1/v2"

FILENAME = re.compile(
    r"^\S+\.(?:jpe?g|png|gif|webp|svg|bmp|tiff?|avif|heic)$"
    r"|^(?:img|dsc|dscn|dcim|image|pic|photo|screenshot|bild|foto)[-_ ]?\d+(?:\.\w{3,4})?$",
    re.IGNORECASE,
)
PLACEHOLDER = {
    "image", "img", "bild", "foto", "photo", "picture", "pic", "grafik", "graphic", "graphique", "icon", "icône",
    "icona", "symbol", "symbole", "simbolo", "logo", "platzhalter", "placeholder", "spacer", "immagine", "photographie",
    "fotografia", "untitled", "alt", "alt text", "alttext", "abbildung", "illustration", "illustrazione", "banner",
    "titelbild", "teaser", "image description", "bildbeschreibung", "description",
}
SMALL_SIDE_PX = 32
IMAGE_TYPES = ["decorative", "informative", "functional", "complex", "text"]


def _norm(s: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", s or "").lower().strip(" .:-_").split())


class NonTextContent(BaseCheck):
    criterion = "1.1.1"
    prompt_version = PROMPT_VERSION
    needs_vision = True
    guard_numbers = False  # numbers read off a chart cannot appear in the DOM
    max_candidates = 60  # each vision question is expensive
    prompt_html_chars = 300

    # -- 1. candidates ------------------------------------------------------------------
    def candidates(self, page: CapturedPage) -> list[Candidate]:
        out: list[Candidate] = []
        for img in page.images:
            if len(out) >= self.max_candidates:
                break
            rect = img.get("rect") or {}
            w, h = rect.get("w", 0), rect.get("h", 0)
            if img.get("tag") != "area" and (w < 2 or h < 2):
                continue  # not rendered, or a tracking pixel (judged by RENDERED size: broken images
                #           report 0×0 natural size and a stretched 1×1 GIF can still carry an alt)
            name = " ".join((img.get("name") or "").split())
            decorative = bool(img.get("decorative_markup"))
            ctx = {k: v for k, v in (img.get("context") or {}).items() if v}
            if not decorative and not name:
                continue  # missing alternative → axe-core
            if decorative and img.get("in_link") and not ctx.get("link_name") and not ctx.get("link_text"):
                kind = "functional_empty"  # the image IS the link/button: alt="" leaves it unnamed (F89)
            elif decorative and max(w, h) <= SMALL_SIDE_PX:
                kind = "decorative_small"
            elif decorative and img.get("in_link") and ctx.get("link_text"):
                continue
            elif decorative:
                kind = "ask"
            elif FILENAME.search(name):
                kind = "filename"
            elif _norm(name) in PLACEHOLDER:
                kind = "placeholder"
            else:
                kind = "ask"
            shot = None
            cand = self.candidate(page, selector=img["selector"], html=img.get("html", ""), text=name,
                                  accessible_name=name, context=self._context(ctx), lang=img.get("lang"),
                                  kind=kind, decorative=decorative, tag=img.get("tag"), role=img.get("role"),
                                  src=img.get("src", ""))
            if kind == "ask" and self.vision:
                shot = page.screenshot(img["selector"], cand.id)
                cand.screenshot = shot
                cand.extra["screenshot_failed"] = shot is None
            out.append(cand)
        return out

    @staticmethod
    def _context(ctx: dict[str, str]) -> dict[str, str]:
        """Minimal context: caption, link destination, surrounding text, title."""
        out = {}
        if ctx.get("caption"):
            out["caption"] = ctx["caption"][:300]
        if ctx.get("link_href"):
            out["link_destination"] = ctx["link_href"][:200]
        if ctx.get("link_text"):
            out["link_text"] = ctx["link_text"][:200]
        if ctx.get("surrounding_text"):
            out["surrounding_text"] = ctx["surrounding_text"][:300]
        if ctx.get("title"):
            out["title"] = ctx["title"][:200]
        return out

    # -- 2. deterministic decisions ----------------------------------------------------------
    def decide(self, c: Candidate) -> Finding | None:
        kind, ui, alt = c.extra.get("kind"), self.ui_lang, c.accessible_name or ""
        if kind == "decorative_small":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium",
                                excerpt=c.html[:300], explanation=t("c111.decorative_small", ui),
                                user_impact=t("c111.impact_ok", ui))
        if kind == "functional_empty":
            return self.finding(c, outcome="failed", source="heuristic", confidence="high",
                                excerpt='alt=""' if 'alt=""' in c.html else c.html[:300],
                                explanation=t("c111.functional_empty", ui), user_impact=t("c111.impact_functional", ui),
                                fix_hint=t("c111.fix_hint_functional", ui))
        if kind in ("filename", "placeholder"):
            return self.finding(c, outcome="failed", source="heuristic",
                                confidence="high" if kind == "filename" else "medium",
                                excerpt=alt, explanation=t(f"c111.{kind}", ui, alt=alt),
                                user_impact=t("c111.impact", ui, alt=alt), fix_hint=t("c111.fix_hint_plain", ui))
        if kind == "ask" and self.vision and c.extra.get("screenshot_failed"):
            return self.note(c, "note.no_screenshot")
        return None

    # -- 3. the closed question (vision) --------------------------------------------------------
    # Needs a vision-capable Apertus endpoint (vLLM on a GPU). Prompt tuning happens on the
    # dev split only; bump PROMPT_VERSION on any change.
    SYSTEM = (
        "You check WCAG 2.1 success criterion 1.1.1 Non-text Content for ONE image (attached crop).\n"
        "image_type: decorative = adds no information; informative = photo or illustration with content; "
        "functional = inside a link or button, its alternative must say where it goes or what it does; "
        "complex = chart, map or diagram that needs a long description; text = image of text.\n"
        "outcome: failed = the current alternative is missing, wrong or not equivalent, or an informative "
        "image is hidden as decorative; passed = the alternative conveys the same information (or the image "
        "is decorative and hidden); cantTell = unsure.\n"
        "quote: the current alternative exactly as written, or alt=\"\" if it is empty. "
        "fix: a better alternative text (empty string for a decorative image)."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        # ui_lang is deliberately unused: prompts are identical for every UI language.
        return self.task(
            system=self.system_prompt(self.SYSTEM, c, fix=True),
            element={"current_alternative": c.accessible_name or "", "marked_decorative": str(bool(c.extra.get("decorative"))).lower(),
                     "html": self.prompt_html(c)},
            context=c.context,
            images=[c.screenshot] if c.screenshot else [],
            question="Does the current alternative give the same information as the image?",
            schema=_with_type_first(),
            max_tokens=180,
        )

    # -- 4. interpretation ----------------------------------------------------------------------
    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        image_type = answer.get("image_type", "informative")
        outcome = answer["outcome"]
        decorative = bool(c.extra.get("decorative"))
        # Consistency rules between the category and the verdict (decided in code).
        if decorative and image_type == "decorative":
            outcome = "passed"
        elif decorative and outcome == "passed" and image_type != "decorative":
            outcome = "cantTell"
        alt = c.accessible_name or ""
        type_label = t(f"c111.type.{image_type}", ui)
        proposal = useful_fix(answer.get("fix"), alt)
        fix_diff = fix_hint = None
        if outcome == "failed":
            if image_type == "decorative":
                fix_diff = self.fix_diff(c, "")
                fix_hint = t("c111.fix_hint_decorative", ui)
            else:
                fix_diff = self.fix_diff(c, proposal) if proposal else None
                fix_hint = t("c111.fix_hint", ui, proposal=proposal) if proposal else t("c111.fix_hint_plain", ui)
                if image_type == "complex":
                    fix_hint += " " + t("c111.fix_hint_complex", ui)
            impact = t("c111.impact_hidden", ui) if decorative else t("c111.impact", ui, alt=alt)
            code = "apertus_hidden" if decorative else "apertus_failed"
            explanation = t(f"c111.{code}", ui, alt=alt, type=type_label)
        elif outcome == "passed":
            impact = t("c111.impact_ok", ui)
            code = "apertus_ok"
            explanation = t("c111.apertus_ok", ui, alt=alt or 'alt=""', type=type_label)
        else:
            impact = t("impact.review", ui)
            code = "apertus_unsure"
            explanation = t("c111.apertus_unsure", ui, alt=alt or 'alt=""')
        excerpt = (answer.get("quote") or "").strip()
        if not excerpt or excerpt == 'alt=""':
            excerpt = 'alt=""' if 'alt=""' in c.html else (alt or c.html[:300])
        return self.finding(c, outcome=outcome, source="apertus", confidence=answer.get("confidence", "low"),
                            excerpt=excerpt, explanation=explanation, user_impact=impact,
                            fix_diff=fix_diff, fix_hint=fix_hint, reason=answer.get("reason"), reason_code=code)

    @staticmethod
    def fix_diff(c: Candidate, alt: str) -> str | None:
        attr = "alt" if c.extra.get("tag") in ("img", "area", "input") else "aria-label"
        after = set_attr(c.html, attr, alt)
        if attr == "alt" and alt and c.extra.get("decorative"):
            after = re.sub(r'\s(?:role="(?:presentation|none)"|aria-hidden="true")', "", after, count=2)
        return unified_diff(c.html, after, c.selector)


def _with_type_first() -> dict:
    """Schema with image_type FIRST (category before verdict: more reliable on 8B)."""
    base = verdict_schema()
    props = {"image_type": {"type": "string", "enum": IMAGE_TYPES}, **base["properties"]}
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


CHECK = NonTextContent
