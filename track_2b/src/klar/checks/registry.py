"""The 50 WCAG 2.1 level A/AA success criteria and how Klar. covers each one.
This registry is the ONLY source of methods: the API (/api/criteria), the UI
coverage map, `klar criteria --json` and the report figure all read it.

`method` is the planned coverage strategy; what a build actually claims is
`coverage()`: the method when a check module is implemented, "human" for criteria
that need a person by nature, else "planned".
  rule            deterministic (axe-core or a custom rule module)
  apertus_text    deterministic facts + Apertus on text (closed question)
  apertus_vision  deterministic facts + Apertus on a screenshot crop
  experimental    audio/video, research only
  human           out of scope for automation: listed so the report is honest

`act_rule` is the W3C ACT rule (https://act-rules.github.io/rules/) closest to
what our check judges; None where no ACT rule fits. `en301549` is the matching
clause of EN 301 549 V3.2.1, chapter 9 (web): "9." + criterion.

Implemented check modules (`c_<criterion>.py`) are discovered automatically;
`implemented()` lists them. `evaluated()` lists the criteria measured on the test
split in eval/results/results.json. axe-core rules may touch other criteria, but
those are never claimed as covered.

4.1.1 Parsing is always satisfied for HTML content under the WCAG 2.1 errata
(2023); it stays "planned" and is never claimed.
"""

from __future__ import annotations

import importlib
import json
import logging
import pkgutil
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from klar.models import CriterionInfo, Method

if TYPE_CHECKING:
    from klar.checks.base import BaseCheck

log = logging.getLogger(__name__)

PRINCIPLES = {1: "perceivable", 2: "operable", 3: "understandable", 4: "robust"}


@dataclass(frozen=True)
class Criterion:
    number: str
    name: str
    level: str  # "A" | "AA"
    method: Method
    act_rule: str | None
    slug: str  # anchor in https://www.w3.org/TR/WCAG21/

    @property
    def en301549(self) -> str:
        return "9." + self.number

    @property
    def principle(self) -> int:
        return int(self.number.split(".")[0])

    @property
    def url(self) -> str:
        """W3C Understanding page."""
        return f"https://www.w3.org/WAI/WCAG21/Understanding/{self.slug}.html"

    @property
    def spec_url(self) -> str:
        return "https://www.w3.org/TR/WCAG21/#" + self.slug

    def info(self, evaluated_set: set[str] | None = None) -> CriterionInfo:
        is_impl = self.number in implemented()
        return CriterionInfo(
            criterion=self.number, name=self.name, level=self.level,  # type: ignore[arg-type]
            principle=PRINCIPLES[self.principle],  # type: ignore[arg-type]
            method=claimed_method(self, is_impl), implemented=is_impl,
            evaluated=self.number in (evaluated_set if evaluated_set is not None else evaluated()),
            act_rule=self.act_rule, en301549=self.en301549, url=self.url,
        )


T, V, R, H, X = "apertus_text", "apertus_vision", "rule", "human", "experimental"

CRITERIA: tuple[Criterion, ...] = (
    # 1 Perceivable
    Criterion("1.1.1", "Non-text Content", "A", V, "qt1vmo", "non-text-content"),
    Criterion("1.2.1", "Audio-only and Video-only (Prerecorded)", "A", X, None, "audio-only-and-video-only-prerecorded"),
    Criterion("1.2.2", "Captions (Prerecorded)", "A", X, "eac66b", "captions-prerecorded"),
    Criterion("1.2.3", "Audio Description or Media Alternative (Prerecorded)", "A", H, None, "audio-description-or-media-alternative-prerecorded"),
    Criterion("1.2.4", "Captions (Live)", "AA", H, None, "captions-live"),
    Criterion("1.2.5", "Audio Description (Prerecorded)", "AA", H, None, "audio-description-prerecorded"),
    Criterion("1.3.1", "Info and Relationships", "A", T, None, "info-and-relationships"),
    Criterion("1.3.2", "Meaningful Sequence", "A", T, None, "meaningful-sequence"),
    Criterion("1.3.3", "Sensory Characteristics", "A", T, "9bd38c", "sensory-characteristics"),
    Criterion("1.3.4", "Orientation", "AA", R, "b33eff", "orientation"),
    Criterion("1.3.5", "Identify Input Purpose", "AA", T, "73f2c2", "identify-input-purpose"),
    Criterion("1.4.1", "Use of Color", "A", V, None, "use-of-color"),
    Criterion("1.4.2", "Audio Control", "A", R, "80f0bf", "audio-control"),
    Criterion("1.4.3", "Contrast (Minimum)", "AA", V, "afw4f7", "contrast-minimum"),
    Criterion("1.4.4", "Resize text", "AA", V, "b4f0c3", "resize-text"),
    Criterion("1.4.5", "Images of Text", "AA", V, "0va7u6", "images-of-text"),
    Criterion("1.4.10", "Reflow", "AA", V, "b4f0c3", "reflow"),
    Criterion("1.4.11", "Non-text Contrast", "AA", V, None, "non-text-contrast"),
    Criterion("1.4.12", "Text Spacing", "AA", V, "24afc2", "text-spacing"),
    Criterion("1.4.13", "Content on Hover or Focus", "AA", H, None, "content-on-hover-or-focus"),
    # 2 Operable
    Criterion("2.1.1", "Keyboard", "A", R, "0ssw9k", "keyboard"),
    Criterion("2.1.2", "No Keyboard Trap", "A", R, "80af7b", "no-keyboard-trap"),
    Criterion("2.1.4", "Character Key Shortcuts", "A", H, None, "character-key-shortcuts"),
    Criterion("2.2.1", "Timing Adjustable", "A", H, "bc659a", "timing-adjustable"),
    Criterion("2.2.2", "Pause, Stop, Hide", "A", T, "efbfc7", "pause-stop-hide"),
    Criterion("2.3.1", "Three Flashes or Below Threshold", "A", H, None, "three-flashes-or-below-threshold"),
    Criterion("2.4.1", "Bypass Blocks", "A", R, "cf77f2", "bypass-blocks"),
    Criterion("2.4.2", "Page Titled", "A", T, "c4a8a4", "page-titled"),
    Criterion("2.4.3", "Focus Order", "A", T, None, "focus-order"),
    Criterion("2.4.4", "Link Purpose (In Context)", "A", T, "5effbb", "link-purpose-in-context"),
    Criterion("2.4.5", "Multiple Ways", "AA", R, None, "multiple-ways"),  # decided in code only
    Criterion("2.4.6", "Headings and Labels", "AA", T, "b49b2e", "headings-and-labels"),
    Criterion("2.4.7", "Focus Visible", "AA", R, "oj04fd", "focus-visible"),
    Criterion("2.5.1", "Pointer Gestures", "A", H, None, "pointer-gestures"),
    Criterion("2.5.2", "Pointer Cancellation", "A", H, None, "pointer-cancellation"),
    Criterion("2.5.3", "Label in Name", "A", T, "2ee8b8", "label-in-name"),
    Criterion("2.5.4", "Motion Actuation", "A", H, None, "motion-actuation"),
    # 3 Understandable
    Criterion("3.1.1", "Language of Page", "A", T, "ucwvc8", "language-of-page"),
    Criterion("3.1.2", "Language of Parts", "AA", T, "off6ek", "language-of-parts"),
    Criterion("3.2.1", "On Focus", "A", R, None, "on-focus"),
    Criterion("3.2.2", "On Input", "A", T, None, "on-input"),
    Criterion("3.2.3", "Consistent Navigation", "AA", R, None, "consistent-navigation"),  # decided in code only
    Criterion("3.2.4", "Consistent Identification", "AA", T, None, "consistent-identification"),
    Criterion("3.3.1", "Error Identification", "A", T, "36b590", "error-identification"),
    Criterion("3.3.2", "Labels or Instructions", "A", T, None, "labels-or-instructions"),
    Criterion("3.3.3", "Error Suggestion", "AA", T, None, "error-suggestion"),
    Criterion("3.3.4", "Error Prevention (Legal, Financial, Data)", "AA", T, None, "error-prevention-legal-financial-data"),
    # 4 Robust
    Criterion("4.1.1", "Parsing", "A", R, None, "parsing"),
    Criterion("4.1.2", "Name, Role, Value", "A", T, "e086e5", "name-role-value"),
    Criterion("4.1.3", "Status Messages", "AA", H, None, "status-messages"),
)

BY_NUMBER: dict[str, Criterion] = {c.number: c for c in CRITERIA}


def get(number: str) -> Criterion:
    return BY_NUMBER[number]


def coverage() -> dict[str, Method]:
    """What this build covers: the method if a check module is implemented, "human" when a
    person must judge by nature, else "planned"."""
    impl = implemented()
    return {c.number: claimed_method(c, c.number in impl) for c in CRITERIA}


def claimed_method(c: Criterion, is_impl: bool) -> Method:
    if is_impl:
        return c.method
    return "human" if c.method == "human" else "planned"


def criteria_info() -> list[CriterionInfo]:
    ev = evaluated()
    return [c.info(ev) for c in CRITERIA]


def evaluated(results: Path | None = None) -> set[str]:
    """Criteria with test-split numbers in eval/results/results.json (empty if absent)."""
    if results is None:
        from klar.config import Settings

        results = Settings.from_env().project_root / "eval" / "results" / "results.json"
    try:
        data = json.loads(Path(results).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    if (data.get("run") or {}).get("split") != "test":
        return set()
    # by_criterion keys are "<source>:<criterion>" (generated and W3C ACT are never pooled)
    out = set()
    for key, block in (data.get("by_criterion") or {}).items():
        source, _, number = key.rpartition(":")
        if source in ("generated", "act") and any((m or {}).get("n") for m in (block or {}).values()):
            out.add(number)
    return out & set(implemented())


def sort_key(number: str) -> tuple[int, ...]:
    return tuple(int(p) for p in number.split("."))


def module_name(number: str) -> str:
    return "c_" + number.replace(".", "_")


_IMPORT_ERRORS: dict[str, str] = {}


def import_errors() -> dict[str, str]:
    """module name → error, for check modules that could not be loaded (shown in scan stats)."""
    implemented()
    return dict(_IMPORT_ERRORS)


@lru_cache(maxsize=1)
def implemented() -> dict[str, type["BaseCheck"]]:
    """criterion → check class, discovered from klar/checks/c_*.py.

    Each module exposes `CHECK = <class>`. A module that fails to import is
    logged and skipped so that one broken check never breaks every scan
    (tests/test_registry.py imports them strictly)."""
    import klar.checks as pkg

    found: dict[str, type] = {}
    for info in pkgutil.iter_modules(pkg.__path__):
        if not info.name.startswith("c_"):
            continue
        try:
            mod = importlib.import_module(f"klar.checks.{info.name}")
        except Exception as exc:
            log.exception("check module %s failed to import; skipped", info.name)
            _IMPORT_ERRORS[info.name] = f"{type(exc).__name__}: {exc}"
            continue
        cls = getattr(mod, "CHECK", None)
        if cls is None:
            log.error("check module %s has no CHECK attribute; skipped", info.name)
            _IMPORT_ERRORS[info.name] = "no CHECK attribute"
            continue
        if getattr(cls, "criterion", None) not in BY_NUMBER:
            log.error("check module %s declares unknown criterion %r", info.name, getattr(cls, "criterion", None))
            _IMPORT_ERRORS[info.name] = "unknown criterion"
            continue
        found[cls.criterion] = cls
    return dict(sorted(found.items(), key=lambda kv: sort_key(kv[0])))
