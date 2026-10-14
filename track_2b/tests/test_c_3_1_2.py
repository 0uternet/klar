"""3.1.2 Language of parts: detector proposals, deterministic decisions, the
categorical question and its mapping, WCAG Understanding exceptions."""

import pytest

from klar import guard
from klar.capture.page import CapturedPage
from klar.checks.c_3_1_2 import CATEGORIES, LanguageOfParts, endonym, is_valid_lang, sentence_like
from klar.config import Settings


def passage(text, lang="de", own=None, selector=None, html=None, is_container=True, container_text=None):
    sel = selector or f"main > p:nth-of-type({abs(hash(text)) % 1000})"
    tag_lang = f' lang="{own}"' if own else ""
    return {"selector": sel, "tag": "p", "html": html or f"<p{tag_lang}>{text}</p>", "text": text,
            "lang": own or lang, "own_lang": own, "container_selector": sel,
            "container_text": container_text or text, "is_container": is_container}


def run(passages, lang_elements=(), ui="en", page_lang="de"):
    page = CapturedPage.from_elements(lang=page_lang, passages=list(passages), lang_elements=list(lang_elements))
    check = LanguageOfParts(ui, Settings())
    cands = check.candidates(page)
    return check, cands


def kinds(cands):
    return [c.extra["kind"] for c in cands]


def test_full_french_sentence_untagged_is_failed_without_the_model():
    text = "Bienvenue sur le site de la commune de Musterwil. Pour plus d'informations, veuillez contacter l'administration."
    check, cands = run([passage(text)])
    assert kinds(cands) == ["untagged_sentence"]
    f = check.decide(cands[0])
    assert f.outcome == "failed" and f.source == "heuristic" and f.act_rule == "off6ek"
    assert f.user_impact == "Screen readers will read this French text with a German voice."
    assert '<p lang="fr">' in f.fix_diff
    assert f.excerpt in cands[0].text


def test_user_impact_in_german_and_french():
    text = "Les déchets verts sont collectés chaque mardi. Merci de sortir les conteneurs avant 7 heures."
    check, cands = run([passage(text)], ui="de")
    assert check.decide(cands[0]).user_impact == "Screenreader lesen diesen französischen Text mit einer deutschen Stimme vor."
    check, cands = run([passage(text)], ui="fr")
    assert check.decide(cands[0]).user_impact == "Les lecteurs d'écran liront ce texte français avec une voix allemande."


@pytest.mark.parametrize("text", [
    "Nach der Sitzung gibt es ein Apéro im Foyer.",  # vernacular loanword
    "Bitte bringen Sie Ihr Velo in den Veloständer.",  # vernacular
    "Das Know-how unserer Mitarbeitenden ist ad hoc verfügbar.",  # loanword + Latin
    "Die Gemeindeverwaltung ist am Montag geschlossen.",  # plain German
])
def test_vernacular_and_plain_text_are_not_candidates(text):
    _, cands = run([passage(text)])
    assert cands == []


def test_institution_inside_german_sentence_goes_to_apertus_with_a_categorical_question():
    text = "Weitere Informationen erhalten Sie beim Office fédéral de la statistique in Neuchâtel."
    check, cands = run([passage(text)])
    assert kinds(cands) == ["ask"]
    c = cands[0]
    assert check.decide(c) is None
    task = check.question(c, "de")
    assert task.json_schema["properties"]["category"]["enum"] == CATEGORIES
    assert list(task.json_schema["properties"])[:2] == ["category", "language"]
    assert "Write `reason` as one short sentence in English" in task.system  # never the UI language
    assert "untrusted" in task.system
    assert "looks like fr" in task.user and text in task.user
    assert task.context_shown["declared_language"] == 'lang="de"'
    assert task.wire() == check.question(c, "it").wire()  # identical prompt for every UI language

    answer = {"category": "institution", "language": "fr", "confidence": "high",
              "quote": "Office fédéral de la statistique", "reason": "Name of a federal office."}
    f = check.interpret(c, answer)
    assert f.outcome == "passed" and f.source == "apertus" and f.reason_code == "apertus_institution"
    assert "institution" in f.explanation and f.reason == "Name of a federal office."
    assert f.reason not in f.explanation  # UI text comes from i18n, the English reason is kept apart
    assert guard.check(f, c, answer).ok


def test_foreign_passage_category_maps_to_failed_with_a_span_fix():
    text = "Die Abteilung Soziales berät Sie gerne. Benvenuti a Musterwil!"
    check, cands = run([passage(text)])
    assert kinds(cands) == ["ask"]
    answer = {"category": "foreign_language_passage", "language": "it", "confidence": "high",
              "quote": "Benvenuti a Musterwil!", "reason": "Italian greeting."}
    f = check.interpret(cands[0], answer)
    assert f.outcome == "failed"
    assert '<span lang="it">Benvenuti a Musterwil!</span>' in f.fix_diff
    assert f.user_impact == "Screen readers will read this Italian text with a German voice."
    assert guard.check(f, cands[0], answer).ok


@pytest.mark.parametrize("category, outcome", [
    ("proper_name", "passed"), ("place_or_address", "passed"), ("technical_term", "passed"),
    ("loanword_in_vernacular", "passed"), ("greeting_or_formula", "cantTell"), ("title_of_work", "cantTell"),
    ("other", "cantTell"), ("foreign_language_passage", "failed"),
])
def test_category_mapping(category, outcome):
    text = "Die Abteilung Soziales berät Sie gerne. Benvenuti a Musterwil!"
    check, cands = run([passage(text)])
    f = check.interpret(cands[0], {"category": category, "language": "it", "confidence": "medium",
                                   "quote": "Benvenuti a Musterwil!", "reason": "r"})
    assert f.outcome == outcome


def test_self_contradictory_answer_becomes_cant_tell():
    text = "Die Abteilung Soziales berät Sie gerne. Benvenuti a Musterwil!"
    check, cands = run([passage(text)])
    f = check.interpret(cands[0], {"category": "foreign_language_passage", "language": "de", "confidence": "high",
                                   "quote": "Benvenuti a Musterwil!", "reason": "r"})
    assert f.outcome == "cantTell"


def test_guard_rejects_a_language_the_detector_never_proposed():
    text = "Weitere Informationen erhalten Sie beim Office fédéral de la statistique in Neuchâtel."
    check, cands = run([passage(text)])
    answer = {"category": "foreign_language_passage", "language": "es", "confidence": "high",
              "quote": "Office fédéral de la statistique", "reason": "Spanish."}
    f = check.interpret(cands[0], answer)
    assert not guard.check(f, cands[0], answer).ok


def test_correctly_tagged_passage_passes_and_wrong_tag_fails():
    ok = passage("Know-how matters for everyone in the community.", own="en", selector="main > span")
    wrong = passage("Les déchets verts sont collectés chaque mardi matin devant la maison.", own="de", selector="main > p.w")
    check, cands = run([ok, wrong])
    assert kinds(cands) == ["tagged_ok", "tagged_mismatch"]
    assert check.decide(cands[0]).outcome == "passed"
    f = check.decide(cands[1])
    assert f.outcome == "failed" and 'lang="fr"' in f.fix_diff


def test_invalid_lang_values_are_rule_failures():
    els = [{"selector": "p.a", "tag": "p", "lang": "francais", "text": "Texte en français pour la commune.",
            "html": '<p lang="francais">Texte en français pour la commune.</p>'},
           {"selector": "p.b", "tag": "p", "lang": "de_CH", "text": "Hallo", "html": '<p lang="de_CH">Hallo</p>'},
           {"selector": "p.c", "tag": "p", "lang": "fr-CH", "text": "ok", "html": '<p lang="fr-CH">ok</p>'}]
    check, cands = run([], lang_elements=els)
    assert [c.selector for c in cands] == ["p.a", "p.b"]
    a, b = (check.decide(c) for c in cands)
    assert a.source == "rule" and a.act_rule == "de46e4" and a.excerpt == 'lang="francais"'
    assert 'lang="fr"' in a.fix_diff
    assert 'lang="de-CH"' in b.fix_diff


@pytest.mark.parametrize("value, ok", [("de", True), ("de-CH", True), ("gsw", True), ("rm", True),
                                       ("zh-Hant-TW", True), ("francais", False), ("de_CH", False),
                                       ("xx", False), ("en-", False), ("x-klingon", False)])
def test_is_valid_lang(value, ok):
    assert is_valid_lang(value) is ok


def test_language_switcher_entries():
    fr = passage("Français", selector="nav li:nth-of-type(2)", html='<li><a href="/fr/">Français</a></li>')
    it_ok = passage("Italiano", own="it", selector="nav li:nth-of-type(3) > a", is_container=False,
                    html='<a href="/it/" lang="it">Italiano</a>')
    de = passage("Deutsch", selector="nav li:nth-of-type(1)")
    check, cands = run([fr, it_ok, de])
    assert kinds(cands) == ["switcher", "tagged_ok"]
    f = check.decide(cands[0])
    assert f.outcome == "failed" and '<li lang="fr">' in f.fix_diff
    assert endonym("Français ") == "fr" and endonym("English") == "en"


def test_switcher_codes_with_their_own_lang_pass():
    fr = passage("FR", own="fr", selector="nav li:nth-of-type(2) > a", is_container=False,
                 html='<a href="/fr/" lang="fr" hreflang="fr">FR</a>')
    untagged = passage("IT", selector="nav li:nth-of-type(3)")
    check, cands = run([fr, untagged])
    assert kinds(cands) == ["tagged_ok"]
    assert check.decide(cands[0]).outcome == "passed"


def test_unverifiable_declared_language_is_skipped():
    _, cands = run([passage("Bainvegni a Musterwil. Qua chattais Vus tut las infurmaziuns da la vischnanca.", lang="rm")],
                   page_lang="rm")
    assert cands == []


def test_sentence_like():
    assert sentence_like("Pour plus d'informations, veuillez contacter l'administration.")
    assert not sentence_like("Département fédéral de l'environnement, des transports, de l'énergie et de la communication")
    assert not sentence_like("Benvenuti a Musterwil!")
