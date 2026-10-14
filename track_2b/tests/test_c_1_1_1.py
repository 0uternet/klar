"""1.1.1 Non-text content: deterministic classes and the vision interpretation."""

from klar import guard
from klar.capture.page import CapturedPage
from klar.checks.c_1_1_1 import NonTextContent
from klar.config import Settings


def img(alt, *, selector=None, w=200, h=120, decorative=None, role=None, in_link=False, context=None, natural=None):
    alt_attr = "" if alt is None else f' alt="{alt}"'
    name = "" if (alt is None or decorative) else alt
    return {"selector": selector or f"img.{abs(hash((alt, w))) % 9999}", "tag": "img",
            "html": f'<img src="rathaus.jpg"{alt_attr}>', "alt": alt, "role": role, "aria_hidden": False,
            "decorative_markup": alt == "" if decorative is None else decorative, "name": name,
            "src": "https://x.test/rathaus.jpg", "natural": natural or {"w": w, "h": h},
            "rect": {"x": 0, "y": 0, "w": w, "h": h}, "lang": "de", "in_link": in_link, "context": context or {}}


def run(images, vision=False, ui="en"):
    page = CapturedPage.from_elements(images=list(images))
    check = NonTextContent(ui, Settings(), vision=vision)
    return check, check.candidates(page)


def test_kinds():
    check, cands = run([img("IMG_2041.jpg"), img("Bild"), img("", w=16, h=16), img(None),
                        img("Rathaus Musterwil mit Brunnen"), img("", w=400, h=300),
                        img("x", w=1, h=1, natural={"w": 1, "h": 1})])
    assert [c.extra["kind"] for c in cands] == ["filename", "placeholder", "decorative_small", "ask", "ask"]
    f = check.decide(cands[0])
    assert f.outcome == "failed" and f.confidence == "high" and f.excerpt == "IMG_2041.jpg"
    assert check.decide(cands[1]).outcome == "failed"
    assert check.decide(cands[2]).outcome == "passed"
    assert check.decide(cands[3]) is None


def test_broken_image_is_not_mistaken_for_a_tracking_pixel():
    _, cands = run([img("Rathaus Musterwil", natural={"w": 0, "h": 0})])
    assert len(cands) == 1


def test_decorative_icon_in_a_named_link_is_skipped():
    _, cands = run([img("", w=64, h=64, in_link=True,
                        context={"link_text": "Kontakt", "link_href": "/k", "link_name": "Kontakt"})])
    assert cands == []


def test_empty_alt_on_the_only_content_of_a_link_fails():
    check, cands = run([img("", w=24, h=24, in_link=True, context={"link_href": "/karte", "link_name": ""})])
    assert cands[0].extra["kind"] == "functional_empty"  # even though it is small
    f = check.decide(cands[0])
    assert f.outcome == "failed" and f.excerpt == 'alt=""' and "no name" in f.explanation


def test_question_is_vision_with_minimal_context():
    check, cands = run([img("Rathaus Musterwil", context={"caption": "Das Rathaus", "surrounding_text": "x … y",
                                                          "link_href": "https://x.test/r"})])
    c = cands[0]
    c.screenshot = "crops/a.png"
    task = check.question(c, "it")
    assert task.images == ["crops/a.png"]
    assert list(task.json_schema["properties"])[:2] == ["image_type", "outcome"]
    assert '"current_alternative": "Rathaus Musterwil"' in task.user
    assert '"caption": "Das Rathaus"' in task.user and '"link_destination": "https://x.test/r"' in task.user
    assert "Write `fix` in German." in task.system and "in English" in task.system
    assert task.wire() == check.question(c, "de").wire()


def test_interpretation_rules():
    check, cands = run([img("Rathaus"), img("", w=400, h=300)])
    named, hidden = cands
    f = check.interpret(named, {"image_type": "informative", "outcome": "failed", "confidence": "high",
                                "quote": "Rathaus", "reason": "Too short.",
                                "fix": "Rathaus Musterwil mit Brunnen am Marktplatz"})
    assert f.outcome == "failed"
    assert 'alt="Rathaus Musterwil mit Brunnen am Marktplatz"' in f.fix_diff
    assert guard.check(f, named, {}, check_numbers=check.guard_numbers).ok

    f = check.interpret(hidden, {"image_type": "decorative", "outcome": "failed", "confidence": "high",
                                 "quote": 'alt=""', "reason": "r", "fix": ""})
    assert f.outcome == "passed"  # decorative and marked decorative: consistent → passed

    f = check.interpret(hidden, {"image_type": "complex", "outcome": "failed", "confidence": "high",
                                 "quote": 'alt=""', "reason": "A chart.", "fix": "Balkendiagramm Steuerertrag"})
    assert f.outcome == "failed" and "hidden" in f.user_impact
    assert "long description" in f.fix_hint

    f = check.interpret(hidden, {"image_type": "informative", "outcome": "passed", "confidence": "high",
                                 "quote": 'alt=""', "reason": "r", "fix": ""})
    assert f.outcome == "cantTell"  # contradiction between category and verdict


def test_guard_ignores_numbers_read_from_the_image():
    check, cands = run([img("Steuerertrag")])
    answer = {"image_type": "complex", "outcome": "failed", "confidence": "high", "quote": "Steuerertrag",
              "reason": "The chart shows 2019 to 2025 values.", "fix": "Steuerertrag 2019-2025"}
    f = check.interpret(cands[0], answer)
    assert check.guard_numbers is False
    assert guard.check(f, cands[0], answer, check_numbers=check.guard_numbers).ok


def test_filename_pattern_is_anchored():
    _, cands = run([img("Foto 2024 vom Fest"), img("Bild 1: Gemeindehaus"), img("DSC_0157"), img("foto3_def.png")])
    assert [c.extra["kind"] for c in cands] == ["ask", "ask", "filename", "filename"]
