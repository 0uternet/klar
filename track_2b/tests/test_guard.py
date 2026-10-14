from klar import guard
from klar.models import Candidate, Finding


def cand(**kw) -> Candidate:
    base = dict(id="c1", criterion="3.1.2", page_url="https://x.test/", selector="main > p",
                html='<p>Weitere Infos beim Office f&eacute;d&eacute;ral de la statistique, Tel. 058 463 60 11.</p>',
                text="Weitere Infos beim Office fédéral de la statistique, Tel. 058 463 60 11.",
                lang_declared="de", context={"detector": '"Office fédéral" looks like fr'},
                extra={"langs": ["de", "fr", "it"]})
    base.update(kw)
    return Candidate(**base)


def finding(excerpt: str, outcome="failed", selector="main > p") -> Finding:
    return Finding(id="f", criterion="3.1.2", criterion_name="Language of Parts", level="AA", act_rule="off6ek",
                   en301549="9.3.1.2", outcome=outcome, source="apertus", confidence="high",
                   page_url="https://x.test/", selector=selector, excerpt=excerpt, context_shown={},
                   explanation="", user_impact="", fix_diff=None, fix_hint=None, screenshot=None, model="m",
                   reason_code="apertus_test")


def test_verbatim_quote_passes_after_normalisation():
    v = guard.check(finding("Office  fédéral de la\nstatistique"), cand(), {"language": "fr", "reason": "A name."})
    assert v.ok, v.reason


def test_entity_and_quote_marks_are_normalised():
    c = cand(html="<p>L&rsquo;office n’est pas ouvert</p>", text="L’office n’est pas ouvert")
    assert guard.check(finding("L'office n'est pas ouvert"), c, {}).ok


def test_quote_not_in_element_is_rejected():
    v = guard.check(finding("Bundesamt für Statistik"), cand(), {})
    assert not v.ok and "quote" in v.reason


def test_failed_without_quote_is_rejected_but_passed_is_not():
    assert not guard.check(finding("", outcome="failed"), cand(), {}).ok
    assert guard.check(finding("", outcome="passed"), cand(), {}).ok


def test_selector_must_resolve():
    v = guard.check(finding("Office fédéral"), cand(), {}, selector_exists=lambda s: False)
    assert not v.ok and "selector" in v.reason
    assert guard.check(finding("Office fédéral"), cand(), {}, selector_exists=lambda s: True).ok


def test_hallucinated_language_code_is_rejected():
    v = guard.check(finding("Office fédéral"), cand(), {"language": "es", "reason": "Spanish."})
    assert not v.ok and "language" in v.reason
    v = guard.check(finding("Office fédéral"), cand(), {"language": "fr-CH", "reason": 'Use lang="fr".'})
    assert v.ok


def test_hallucinated_number_is_rejected_but_page_numbers_and_wcag_refs_are_fine():
    assert not guard.check(finding("Office fédéral"), cand(), {"reason": "Call 044 123 45 67 instead."}).ok
    assert guard.check(finding("Office fédéral"), cand(), {"reason": "The number 058 463 60 11 is fine."}).ok
    assert guard.check(finding("Office fédéral"), cand(), {"reason": "WCAG 2.1 criterion 3.1.2 applies."}).ok
    assert guard.check(finding("Office fédéral"), cand(), {"reason": "Call 044 123 45 67."}, check_numbers=False).ok


def test_hallucinated_url_is_rejected():
    v = guard.check(finding("Office fédéral"), cand(), {"reason": "See https://www.bfs.admin.ch for details."})
    assert not v.ok and "URL" in v.reason
    c = cand(html='<p><a href="https://www.bfs.admin.ch">Office fédéral</a></p>')
    assert guard.check(finding("Office fédéral"), c, {"reason": "Links to https://www.bfs.admin.ch."}).ok


def test_downgrade_produces_a_grounded_cant_tell():
    c = cand()
    f = guard.downgrade(finding("invented"), c, "quote not found in the element", "de")
    assert f.outcome == "cantTell" and f.confidence == "low"
    assert f.excerpt in c.text  # the fallback excerpt is chosen by code, verbatim
    assert "nicht belegt" in f.explanation and f.fix_diff is None and f.reason_code == "not_grounded"
