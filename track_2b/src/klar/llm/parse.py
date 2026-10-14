"""Tolerant JSON extraction + a small JSON-schema validator (no extra dependency).

Used when the endpoint does not support `response_format: json_schema`, and as
a safety net when it does (some servers ignore the schema silently).
"""

from __future__ import annotations

import copy
import json
import re
from typing import Any

_FENCE = re.compile(r"```(?:json|JSON)?\s*(.*?)```", re.DOTALL)
_THINK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_TRAILING_COMMA = re.compile(r",\s*([}\]])")


def _balanced_object(text: str) -> str | None:
    """Return the first top-level {...} block, respecting strings and escapes."""
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
        start = text.find("{", start + 1)
    return None


def parse_json_loose(text: str | None) -> dict:
    """Best-effort: plain JSON, fenced JSON, JSON inside prose, trailing commas,
    Python literals. Raises ValueError with a short reason otherwise."""
    if not text or not text.strip():
        raise ValueError("empty answer")
    s = _THINK.sub("", text).strip()
    candidates = [s]
    m = _FENCE.search(s)
    if m:
        candidates.append(m.group(1).strip())
    obj = _balanced_object(s)
    if obj:
        candidates.append(obj)
    last_err = "no JSON object found"
    for c in candidates:
        for variant in (c, _TRAILING_COMMA.sub(r"\1", c)):
            try:
                value = json.loads(variant)
            except json.JSONDecodeError as exc:
                last_err = f"invalid JSON: {exc.msg}"
                # Python-style literals (True/False/None, single quotes) as a last resort
                try:
                    py = re.sub(r"\bTrue\b", "true", re.sub(r"\bFalse\b", "false", re.sub(r"\bNone\b", "null", variant)))
                    value = json.loads(py)
                except json.JSONDecodeError:
                    continue
            if isinstance(value, dict):
                return value
            last_err = "the answer is not a JSON object"
    raise ValueError(last_err)


# --- schema --------------------------------------------------------------------------

_ENUM_ALIASES = {
    # common model spellings → canonical enum value
    "cant_tell": "cantTell",
    "canttell": "cantTell",
    "cannot tell": "cantTell",
    "can't tell": "cantTell",
    "cant tell": "cantTell",
    "unknown": "cantTell",
    "fail": "failed",
    "pass": "passed",
}


def strip_for_wire(schema: dict) -> dict:
    """Remove keywords some OpenAI-compatible servers reject in strict mode."""
    s = copy.deepcopy(schema)

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            node.pop("default", None)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(s)
    return s


def _type_ok(value: Any, typ: str) -> bool:
    return {
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "array": isinstance(value, list),
        "object": isinstance(value, dict),
        "null": value is None,
    }.get(typ, True)


def coerce(answer: dict, schema: dict) -> dict:
    """Fix harmless deviations in place: enum case/aliases, missing fields that
    have a `default`, over-long strings (truncated to maxLength), extra keys."""
    props: dict = schema.get("properties", {})
    out: dict = {}
    for key, spec in props.items():
        if key not in answer:
            if "default" in spec:
                out[key] = copy.deepcopy(spec["default"])
            continue
        v = answer[key]
        if "enum" in spec and isinstance(v, str) and v not in spec["enum"]:
            norm = v.strip()
            low = norm.lower()
            match = next((e for e in spec["enum"] if isinstance(e, str) and e.lower() == low), None)
            if match is None:
                alias = _ENUM_ALIASES.get(low)
                match = alias if alias in spec["enum"] else None
            v = match if match is not None else v
        if spec.get("type") == "string" and v is None and "default" in spec:
            v = spec["default"]
        if isinstance(v, str) and isinstance(spec.get("maxLength"), int) and len(v) > spec["maxLength"]:
            v = v[: spec["maxLength"]].rstrip()
        out[key] = v
    return out


def validate(answer: Any, schema: dict) -> list[str]:
    """Return human-readable errors (empty list = valid). Supports the subset
    we use: type, properties, required, enum, maxLength, items."""
    errors: list[str] = []

    def check(value: Any, spec: dict, path: str) -> None:
        typ = spec.get("type")
        types = typ if isinstance(typ, list) else ([typ] if typ else [])
        if types and not any(_type_ok(value, t) for t in types):
            errors.append(f"{path or 'answer'} must be of type {'/'.join(types)}")
            return
        if "enum" in spec and value not in spec["enum"]:
            errors.append(f"{path} must be one of {spec['enum']}, got {value!r}")
        if isinstance(value, dict):
            for req in spec.get("required", []):
                if req not in value:
                    errors.append(f"missing field {req!r}")
            for k, sub in spec.get("properties", {}).items():
                if k in value:
                    check(value[k], sub, f"{path}.{k}" if path else k)
        if isinstance(value, list) and isinstance(spec.get("items"), dict):
            for i, item in enumerate(value):
                check(item, spec["items"], f"{path}[{i}]")

    check(answer, schema, "")
    return errors


def parse_and_validate(text: str | None, schema: dict) -> tuple[dict | None, list[str]]:
    try:
        raw = parse_json_loose(text)
    except ValueError as exc:
        return None, [str(exc)]
    fixed = coerce(raw, schema)
    errs = validate(fixed, schema)
    return (fixed if not errs else None), errs
