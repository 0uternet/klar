import pytest

from klar.checks.base import category_schema, verdict_schema
from klar.llm.parse import coerce, parse_and_validate, parse_json_loose, strip_for_wire, validate


@pytest.mark.parametrize("text", [
    '{"outcome": "failed"}',
    '```json\n{"outcome": "failed"}\n```',
    'Sure! Here is my answer: {"outcome": "failed"} Hope it helps.',
    '{"outcome": "failed",}',
    "<think>hmm</think>{\"outcome\": \"failed\"}",
    '{"outcome": "failed", "x": True}',
])
def test_parse_json_loose(text):
    assert parse_json_loose(text)["outcome"] == "failed"


def test_parse_json_loose_respects_braces_in_strings():
    assert parse_json_loose('noise {"quote": "a } b", "n": 1} tail') == {"quote": "a } b", "n": 1}


@pytest.mark.parametrize("text", ["", "no json here", "[1, 2]"])
def test_parse_json_loose_rejects(text):
    with pytest.raises(ValueError):
        parse_json_loose(text)


def test_coerce_fixes_enum_aliases_case_and_length():
    schema = verdict_schema()
    out = coerce({"outcome": "Cannot Tell", "confidence": "HIGH", "quote": "x" * 200, "reason": "r"}, schema)
    assert out["outcome"] == "cantTell"
    assert out["confidence"] == "high"
    assert len(out["quote"]) == 80
    assert out["fix"] == ""  # default filled
    assert validate(out, schema) == []


def test_validate_reports_errors():
    errs = validate({"outcome": "maybe", "confidence": "high"}, verdict_schema())
    assert any("outcome" in e for e in errs)
    assert any("quote" in e for e in errs)


def test_parse_and_validate_category_schema():
    schema = category_schema(["a", "b"], extra={"language": {"type": "string", "maxLength": 12}})
    ans, errs = parse_and_validate('{"category": "b", "language": "fr", "confidence": "low", "quote": "q", "reason": "r"}', schema)
    assert errs == [] and ans["category"] == "b"
    assert list(schema["properties"])[0] == "category"  # category is generated first


def test_verdict_field_order_and_wire_schema():
    schema = verdict_schema()
    assert list(schema["properties"]) == ["outcome", "confidence", "quote", "reason", "fix"]
    assert schema["properties"]["quote"]["maxLength"] == 80
    assert schema["properties"]["reason"]["maxLength"] == 160
    wire = strip_for_wire(schema)
    assert "default" not in wire["properties"]["fix"]
    assert "default" in schema["properties"]["fix"]  # original untouched
