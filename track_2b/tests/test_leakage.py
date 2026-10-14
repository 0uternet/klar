"""Regression tests for scripts/check_leakage.py (PROTOCOL.md decision D3).

Each test builds a tiny synthetic tree (data/testset, data/demo-site, data/demo-truth,
src/klar) in a temporary directory, seeds exactly one kind of leakage and checks that the
checker reports it. A negative control checks that the clean tree gives 0 overlaps.
The real src/klar and data/ are never touched. Stdlib + pytest only; no browser.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load_checker():
    sys.path.insert(0, str(SCRIPTS / "testset_gen"))
    spec = importlib.util.spec_from_file_location("check_leakage", SCRIPTS / "check_leakage.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cl = _load_checker()

PAGE = """<!DOCTYPE html>
<html lang="de-CH"><head><meta charset="utf-8"><title>{title}</title></head>
<body><main>{main}</main></body></html>
"""
TEST_MAIN = ('<h1>Chorprobe</h1><p id="t">Die Chorprobe findet ab Januar im Saal der Brasserie des Trois Sapins statt.</p>'
             '<table><tr><td>Anmeldung bis 3.9.2026</td><td>nach drei Monaten verfällt die Reservation ohne weitere '
             'Mitteilung der Verwaltung.</td></tr></table>')
DEV_MAIN = ('<h1>Wochenmarkt</h1><p id="t">Le marché a lieu chaque samedi matin sur la place de l\'église, '
            'avec des produits de la région.</p>')
DEMO_HTML = ('<!DOCTYPE html><html lang="de-CH"><head><meta charset="utf-8"><title>Startseite</title></head><body><main>'
             '<p>Willkommen auf der Website der Gemeinde Beispieldorf. Hier finden Sie Neuigkeiten aus der Verwaltung.</p>'
             '</main></body></html>')


def _row(case_id, split, path, template, *, surface=(), trap=True, expected="passed"):
    return {"case_id": case_id, "criterion": "3.1.2", "page_lang": "de", "source": "generated", "act_rule": None,
            "split": split, "expected": expected, "path": path, "target_selector": "#t", "notes": "n",
            "rule": "3.1.2/T1", "trap": trap, "alt_expected": None, "difficulty": "medium", "pages": 1,
            "template_id": template, "surface_forms": list(surface), "tags": [], "license": "CDLA-Permissive-2.0"}


def build_tree(root: Path, *, dev_main=DEV_MAIN, dev_template="3.1.2/b", demo_html=DEMO_HTML,
               src_files=None, truth_rationale="Understanding 3.1.2: \"Gratis-Service für Schulvelos\" is a heading.") -> Path:
    ts = root / "data" / "testset"
    (ts / "generated" / "3.1.2").mkdir(parents=True)
    (ts / "generated" / "3.1.2" / "gen-test-001.html").write_text(PAGE.format(title="Chorprobe", main=TEST_MAIN), encoding="utf-8")
    (ts / "generated" / "3.1.2" / "gen-dev-001.html").write_text(PAGE.format(title="Markt", main=dev_main), encoding="utf-8")
    rows = [_row("gen-test-001", "test", "generated/3.1.2/gen-test-001.html", "3.1.2/a", surface=["Brasserie des Trois Sapins"]),
            _row("gen-dev-001", "dev", "generated/3.1.2/gen-dev-001.html", dev_template, surface=["place de l'église"])]
    (ts / "manifest.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    demo = root / "data" / "demo-site"
    demo.mkdir(parents=True)
    (demo / "index.html").write_text(demo_html, encoding="utf-8")
    truth = root / "data" / "demo-truth"
    truth.mkdir(parents=True)
    (truth / "issues.jsonl").write_text(json.dumps({"page": "index.html", "selector": None, "criterion": "3.1.2",
                                                    "kind": "trap", "expected": "passed",
                                                    "rationale": truth_rationale}, ensure_ascii=False) + "\n", encoding="utf-8")
    checks = root / "src" / "klar" / "checks"
    checks.mkdir(parents=True)
    files = {"c_clean.py": 'SYSTEM = "Classify the flagged part, e.g. \\"Gasthof zur Linde am Bach\\"."\n'}
    files.update(src_files or {})
    for name, text in files.items():
        (checks / name).write_text(text, encoding="utf-8")
    return root


def findings(root: Path) -> dict:
    return cl.run(root)


def test_negative_control_clean_tree(tmp_path):
    res = findings(build_tree(tmp_path))
    assert all(not v for v in res.values()), res
    assert cl.main(["--root", str(tmp_path)]) == 0


def test_quoted_span_in_prompt(tmp_path):
    src = {"c_seed.py": 'SYSTEM = "e.g. \\"im Saal der Brasserie des Trois Sapins\\" is an institution"\n'}
    res = findings(build_tree(tmp_path, src_files=src))
    assert any("quoted code example" in f for f in res["code->test"]), res
    assert cl.main(["--root", str(tmp_path)]) == 1


def test_surface_form_in_lexicon(tmp_path):
    src = {"c_seed.py": 'PROPER_NAMES = ["Brasserie des Trois Sapins", "Gasthof Krone", "Hotel Post"]\n'}
    res = findings(build_tree(tmp_path, src_files=src))
    assert any("surface form 'brasserie des trois sapins'" in f for f in res["code->test"]), res


def test_few_shot_sentence_across_elements(tmp_path):
    # the sentence spans two table cells: words must not fuse ("3.9.2026" + "nach")
    src = {"c_seed.py": 'FEWSHOT = """Anmeldung bis 3.9.2026 nach drei Monaten verfällt die Reservation."""\n'}
    res = findings(build_tree(tmp_path, src_files=src))
    assert any("8-word shingle" in f for f in res["code->test"]), res


def test_few_shot_in_comment_and_js(tmp_path):
    src = {"c_seed.py": "# ab Januar im Saal der Brasserie des Trois Sapins statt\nX = 1\n",
           "fewshot.js": "const s = 'Mitteilung der Verwaltung'; // nach drei Monaten verfällt die Reservation ohne weitere Mitteilung\n"}
    res = findings(build_tree(tmp_path, src_files=src))
    assert sum("8-word shingle" in f for f in res["code->test"]) >= 1, res


def test_demo_sentence_shared(tmp_path):
    demo = DEMO_HTML.replace("Hier finden Sie Neuigkeiten aus der Verwaltung.",
                             "Achtung: nach drei Monaten verfällt die Reservation ohne weitere Mitteilung der Verwaltung.")
    res = findings(build_tree(tmp_path, demo_html=demo))
    assert any("shared with the demo site" in f for f in res["demo->test"]), res


def test_demo_answer_key_string(tmp_path):
    res = findings(build_tree(tmp_path, truth_rationale='Understanding 3.1.2: "Saal der Brasserie" is a venue name.'))
    assert any("demo answer-key string" in f for f in res["demo->test"]), res


def test_template_in_both_splits(tmp_path):
    res = findings(build_tree(tmp_path, dev_template="3.1.2/a"))
    assert any("in both splits" in f for f in res["dev->test"]), res


def test_near_duplicate_across_splits(tmp_path):
    res = findings(build_tree(tmp_path, dev_main=TEST_MAIN))
    assert any("near-duplicate" in f for f in res["dev->test"]), res


def test_answer_key_file_in_demo_site(tmp_path):
    root = build_tree(tmp_path)
    (root / "data" / "demo-site" / "issues.jsonl").write_text('{"expected": "failed"}\n', encoding="utf-8")
    res = findings(root)
    assert any("answer-key-like file" in f for f in res["answer-keys"]), res


def test_verdict_marker_in_demo_page(tmp_path):
    demo = DEMO_HTML.replace("</main>", '<p data-note="cantTell">x</p></main>')
    res = findings(build_tree(tmp_path, demo_html=demo))
    assert any("contains answer-key text" in f for f in res["answer-keys"]), res


def test_ws_text_inserts_boundaries():
    from htmlcheck import parse
    root, _, _ = parse("<p><b>3.9.2026</b>nach drei</p><ul><li>eins</li><li>zwei</li></ul>")
    text = cl.ws_text(root)
    assert "3.9.2026 nach" in text and "eins zwei" in text


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
