"""API contract: the Pydantic models are the source of truth.

tests/fixtures/contract/ holds, generated from the real models:
  health.json, criteria.json, scan.json, finding.json, progress_step.json, stats.json
      deterministic EXAMPLES (the web UI's `npm run contract` type-checks them);
  schema/<name>.schema.json
      the JSON Schemas of the models.
The tests fail when a committed fixture is out of date, so every contract change
is visible in review. Regenerate with KLAR_UPDATE_CONTRACT=1.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from klar import __version__
from klar.checks import registry
from klar.models import CriterionInfo, Finding, Health, ProgressStep, Scan, ScanRequest, ScanStats
from klar.pipeline import STEPS, empty_stats

FIXTURES = Path(__file__).parent / "fixtures" / "contract"
SCHEMAS = {"scan": Scan, "finding": Finding, "scan_stats": ScanStats, "progress_step": ProgressStep,
           "criterion_info": CriterionInfo, "health": Health, "scan_request": ScanRequest}
T0 = datetime(2026, 10, 14, 9, 30, tzinfo=timezone.utc)
MODEL = "swiss-ai/Apertus-v1.5-8B"


def _finding(**kw) -> Finding:
    base = dict(
        id="0123456789-1a2b3c4d5e6f", criterion="2.4.4", criterion_name="Link Purpose (In Context)", level="A",
        act_rule="5effbb", en301549="9.2.4.4", outcome="failed", source="apertus", confidence="high",
        page_url="http://127.0.0.1:8080/demo/index.html", selector="#main > p:nth-of-type(3) > a", excerpt="Mehr",
        context_shown={"link_text": "Mehr", "html": '<a href="…">Mehr</a>', "block": "Mehr"},
        explanation="Apertus judged that neither “Mehr” nor its programmatic context says where the link goes.",
        user_impact="Screen-reader users who list the links hear “Mehr” without knowing where it leads.",
        fix_diff="--- a/#main > p:nth-of-type(3) > a\n+++ b/#main > p:nth-of-type(3) > a\n@@ -1 +1 @@\n"
                 '-<a href="news.html">Mehr</a>\n+<a href="news.html">Neue Öffnungszeiten</a>',
        fix_hint="In your CMS, change the link text so that it names the destination, for example “Neue Öffnungszeiten”.",
        screenshot=None, model=MODEL, status="to_review", content_lang="de", axe_rule=None,
        reason_code="apertus_nowhere", reason="The link text and its block do not name the destination.")
    base.update(kw)
    return Finding(**base)


EXAMPLE_IMPLEMENTED = ("1.1.1", "2.4.4", "3.1.2")


def _coverage() -> dict[str, str]:
    return {c.number: registry.claimed_method(c, c.number in EXAMPLE_IMPLEMENTED) for c in registry.CRITERIA}


def examples() -> dict[str, object]:
    steps = [ProgressStep(step=s, state="done", started_at=T0, duration_ms=1000 + 10 * i, detail=None,
                          current=7 if s == "apertus" else None, total=7 if s == "apertus" else None)
             for i, s in enumerate(STEPS)]
    findings = [
        _finding(),
        _finding(id="0123456789-6f5e4d3c2b1a", criterion="3.1.2", criterion_name="Language of Parts", level="AA",
                 act_rule="off6ek", en301549="9.3.1.2", source="heuristic", model=None, reason=None,
                 selector="#notice > p", excerpt="Les communes sont invitées à participer.", context_shown={},
                 explanation="This passage is French but it inherits lang=\"de\" and has no lang attribute of its own.",
                 user_impact="Screen readers will read this French text with a German voice.",
                 fix_diff=None, fix_hint="In your CMS, mark this text as French (language attribute lang=\"fr\").",
                 reason_code="untagged_sentence", content_lang="de"),
        _finding(id="0123456789-aabbccddeeff", criterion="1.1.1", criterion_name="Non-text Content",
                 act_rule="23a2a8", en301549="9.1.1.1", source="rule", model=None, reason=None, confidence="high",
                 selector="#news > img", excerpt='<img src="logo.svg">', context_shown={}, axe_rule="image-alt",
                 reason_code="axe", explanation="axe-core rule “image-alt”: Images must have alternative text",
                 user_impact="Screen-reader users do not learn what this image shows.", fix_diff=None,
                 fix_hint="Fix any of the following: Element does not have an alt attribute", content_lang=None),
    ]
    stats = empty_stats(vision=False)
    stats.update(failed=3, to_review=3, criteria_checked=3, criteria_rule=2, criteria_apertus=3, llm_calls=1,
                 tokens_in=380, tokens_out=60, seconds=4.2, asked_apertus=1, candidates=12,
                 decided_deterministically=10, schema_level="replay", criteria_list=["1.1.1", "2.4.4", "3.1.2"],
                 criteria_apertus_list=["1.1.1", "2.4.4", "3.1.2"], external_ai_requests=0)
    stats = ScanStats.model_validate(stats).model_dump(mode="json")
    scan = Scan(id="0123456789", url="http://127.0.0.1:8080/demo/index.html", created_at=T0, mode="replay",
                model=MODEL, ui_lang="en", state="done", progress=[s.model_dump(mode="json") for s in steps],
                findings=findings, coverage=_coverage(), stats=stats)
    health = Health(mode="replay", model=MODEL, replay_models=[MODEL], base_url_host=None, provider=None,
                    vision=False, vision_source="replay", json_schema=False, chat_template_kwargs=False,
                    version=__version__, config_error=None, ai_requests={"local": 0, "swiss_cloud": 0, "external": 0},
                    external_ai_requests=0,
                    replay_recorded={"from": "2026-10-15T08:00:00+00:00", "to": "2026-10-15T09:00:00+00:00",
                                     "hosts": ["llm-gpu"], "records": 118})
    # Fixed example set, so the fixtures describe the contract, not which check modules exist
    # today; `evaluated` comes from eval results at run time.
    criteria = [CriterionInfo(criterion=c.number, name=c.name, level=c.level,  # type: ignore[arg-type]
                              principle=registry.PRINCIPLES[c.principle],  # type: ignore[arg-type]
                              method=_coverage()[c.number], implemented=c.number in EXAMPLE_IMPLEMENTED,
                              evaluated=False, act_rule=c.act_rule, en301549=c.en301549, url=c.url)
                for c in registry.CRITERIA]
    return {
        "health.json": health.model_dump(mode="json"),
        "criteria.json": [c.model_dump(mode="json") for c in criteria],
        "scan.json": scan.model_dump(mode="json"),
        "finding.json": findings[0].model_dump(mode="json"),
        "progress_step.json": steps[3].model_dump(mode="json"),
        "stats.json": stats,
    }


def _check(path: Path, text: str) -> None:
    if not path.is_file() or os.environ.get("KLAR_UPDATE_CONTRACT") == "1":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    assert path.read_text(encoding="utf-8") == text, (
        f"{path.relative_to(FIXTURES)} is out of date: the API contract changed. "
        "Re-run with KLAR_UPDATE_CONTRACT=1 and tell the frontend.")


@pytest.mark.parametrize("name", sorted(SCHEMAS))
def test_schema_fixture_is_current(name):
    text = json.dumps(SCHEMAS[name].model_json_schema(), indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    _check(FIXTURES / "schema" / f"{name}.schema.json", text)


@pytest.mark.parametrize("name", ["health.json", "criteria.json", "scan.json", "finding.json",
                                  "progress_step.json", "stats.json"])
def test_example_fixture_is_current(name):
    text = json.dumps(examples()[name], indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    _check(FIXTURES / name, text)


def test_examples_validate_against_the_models():
    ex = examples()
    Health.model_validate(ex["health.json"])
    Scan.model_validate(ex["scan.json"])
    Finding.model_validate(ex["finding.json"])
    ProgressStep.model_validate(ex["progress_step.json"])
    ScanStats.model_validate(ex["stats.json"])
    assert len([CriterionInfo.model_validate(c) for c in ex["criteria.json"]]) == 50


def test_frozen_field_names():
    assert {"content_lang", "axe_rule", "reason_code", "reason"} <= set(Finding.model_fields)
    flat = {"failed", "cantTell", "passed", "inapplicable", "to_review", "accepted", "rejected", "criteria_checked",
            "criteria_rule", "criteria_apertus", "llm_calls", "tokens_in", "tokens_out", "seconds", "guard_rejected",
            "injection_flagged", "not_recorded", "llm_errors", "budget_skipped", "replay_loose_hits", "ai_requests"}
    assert flat <= set(ScanStats.model_fields)
    assert {"criterion", "name", "level", "principle", "method", "implemented", "evaluated", "act_rule",
            "en301549", "url"} == set(CriterionInfo.model_fields)
    assert {"mode", "model", "replay_models", "base_url_host", "provider", "vision", "vision_source", "json_schema",
            "chat_template_kwargs", "version", "config_error", "ai_requests"} <= set(Health.model_fields)
    assert {"step", "state", "started_at", "duration_ms", "detail", "current", "total"} == set(ProgressStep.model_fields)
