import importlib
import json
import pkgutil
import re
from collections import Counter

import klar.checks
from klar.checks import registry
from klar.checks.base import BaseCheck

EXPECTED = {
    "apertus_text": "1.3.1 1.3.2 2.2.2 2.4.3 1.3.3 1.3.5 2.4.2 2.4.4 2.4.6 2.5.3 3.1.1 3.1.2 3.2.2 3.2.4 3.3.1 3.3.2 3.3.3 3.3.4 4.1.2",
    "apertus_vision": "1.1.1 1.4.1 1.4.3 1.4.5 1.4.11 1.4.4 1.4.10 1.4.12",
    "experimental": "1.2.1 1.2.2",
    "rule": "1.3.4 1.4.2 2.1.1 2.1.2 2.4.1 2.4.5 2.4.7 3.2.1 3.2.3 4.1.1",
    "human": "1.2.3 1.2.4 1.2.5 2.3.1 2.1.4 2.5.1 2.5.2 2.5.4 2.2.1 1.4.13 4.1.3",
}


def test_fifty_criteria_with_the_agreed_methods():
    assert len(registry.CRITERIA) == 50
    assert len(registry.BY_NUMBER) == 50
    for method, numbers in EXPECTED.items():
        for n in numbers.split():
            assert registry.get(n).method == method, n
    assert Counter(c.method for c in registry.CRITERIA) == {k: len(v.split()) for k, v in EXPECTED.items()}


def test_metadata_shapes():
    for c in registry.CRITERIA:
        assert c.level in ("A", "AA")
        assert c.en301549 == "9." + c.number
        assert c.act_rule is None or re.fullmatch(r"[0-9a-z]{6}", c.act_rule)
        assert re.fullmatch(r"[a-z0-9-]+", c.slug)
    assert registry.coverage()["2.4.4"] == "apertus_text"
    assert registry.coverage()["1.4.10"] == "planned"  # no check module yet → never claimed
    assert registry.coverage()["2.3.1"] == "human"  # needs a person by nature, never "planned"
    assert registry.get("1.4.10").url == "https://www.w3.org/WAI/WCAG21/Understanding/reflow.html"
    info = {c.criterion: c for c in registry.criteria_info()}
    assert len(info) == 50 and info["2.4.4"].implemented and info["2.4.4"].method == "apertus_text"
    assert info["1.4.10"].method == "planned" and not info["1.4.10"].implemented
    assert info["1.1.1"].principle == "perceivable" and info["4.1.2"].principle == "robust"


def test_every_check_module_imports_and_matches_the_registry():
    for info in pkgutil.iter_modules(klar.checks.__path__):
        if not info.name.startswith("c_"):
            continue
        mod = importlib.import_module(f"klar.checks.{info.name}")  # strict: an import error fails here
        cls = mod.CHECK
        assert issubclass(cls, BaseCheck)
        assert info.name == registry.module_name(cls.criterion)
        meta = registry.get(cls.criterion)
        assert (cls.name, cls.level, cls.en301549) == (meta.name, meta.level, meta.en301549)
        assert cls.prompt_version.startswith(cls.criterion + "/")
        assert cls.needs_vision == (meta.method == "apertus_vision")
    assert set(registry.implemented()) >= {"1.1.1", "2.4.4", "3.1.2"}


def test_a_check_that_never_asks_the_model_is_not_claimed_as_apertus():
    import inspect

    for number, cls in registry.implemented().items():
        never_asks = "raise NotImplementedError" in inspect.getsource(cls.question)
        assert not (never_asks and registry.get(number).method.startswith("apertus")), number
    assert registry.get("2.4.5").method == registry.get("3.2.3").method == "rule"


def test_evaluated_reads_source_prefixed_criterion_keys(tmp_path):
    block = {"ours": {"n": 12}, "baseline": {"n": 12}}
    results = {"run": {"split": "test"}, "by_criterion": {
        "generated:2.4.4": block, "act:3.1.2": block, "generated:1.4.10": block,  # 1.4.10: no check module
        "generated:2.4.6": {"ours": {"n": 0}}, "other:1.1.1": block}}
    path = tmp_path / "results.json"
    path.write_text(json.dumps(results), encoding="utf-8")
    assert registry.evaluated(path) == {"2.4.4", "3.1.2"}
    path.write_text(json.dumps({**results, "run": {"split": "dev"}}), encoding="utf-8")
    assert registry.evaluated(path) == set()  # dev numbers are not evaluation results
    assert registry.evaluated(tmp_path / "missing.json") == set()
