"""3.2.4 Consistent Identification, level AA. No ACT rule (technique G197, failure F31).

The audited page is compared with a bounded sample of the same site (see
c_2_4_5.site_sample: same origin, static HTML, at most 20 pages and 15 s).
Pages whose main text is in another language form another set of pages and are not
compared. Findings are about the SET of pages and name the page where the label differs.

Facts in code
  * Components with the same functionality, keyed by what they DO, never by their label:
      link:<landmark>:<destination>  links in header, navigation, footer and sidebars, and
                                image-only links anywhere (same destination + same role);
                                links to the current page and to other language versions
                                (hreflang / lang) are not components of this set
      search                    the submit button and the field of a search form
      action:<handler>          buttons with the same onclick handler
      submit:<form action>      submit buttons of forms posting to the same address
  * Identification = accessible name (+ visible text). Names are compared after
    normalisation: case, punctuation and NUMBERS are ignored, so "page 2" / "page 3"
    follow one pattern (Understanding 3.2.4, pagination example).
  * Same visible label on both pages, but a different accessible name that does not
    contain the other one                 → failed (heuristic, F31: what the screen reader
                                             announces differs)
  * An icon-only variant whose name equals the text variant → consistent.

Asked to Apertus (one closed question per inconsistent component, at most 4 per page)
  "Do these two labels identify the same function consistently?" with the two labels
  only, CATEGORICAL, mapped in code:
      same_or_pattern     → passed   (same words, or one pattern with a changing number)
      synonyms            → failed   (different words for the same function, F31)
      more_specific       → cantTell (one label names a narrower purpose: same function?)
      different_function  → passed   (no consistency requirement, Understanding ex. 6)
      unsure              → cantTell

Cascade for the set of pages (findings reported on the audited page)
  1. pasted HTML                              → cantTell (needs a URL)
  2. no component on the audited page         → inapplicable
  3. no other page of the same language       → cantTell (not enough pages)
  4. no component repeated on two pages       → inapplicable
  5. all repeated components identified alike → passed (one finding)
  6. per inconsistent component: F31 rule above, else Apertus.

Known limits: scripts are not run on the sampled pages; a print button and a link
to a print version (same purpose, different mechanism) are not paired; components in
the main content are compared only when they are buttons with a handler or image links.
"""

from __future__ import annotations

import html as htmllib
import re
import unicodedata
from collections import Counter, defaultdict
from urllib.parse import urljoin

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema
from klar.checks.c_2_4_5 import (Node, SiteSampling, SitePage, is_breadcrumb, is_search_form, live_selector, page_doc,
                                 page_key, region_of, short_path)
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "3.2.4/v1"
MAX_QUESTIONS = 4

CATEGORIES = ["same_or_pattern", "synonyms", "more_specific", "different_function", "unsure"]
CATEGORY_OUTCOME = {"same_or_pattern": "passed", "synonyms": "failed", "more_specific": "cantTell",
                    "different_function": "passed", "unsure": "cantTell"}

register({
    "c324.passed": {
        "en": "The {k} components repeated across the {n} sampled pages carry the same names.",
        "de": "Die {k} wiederholten Bedienelemente tragen auf den {n} geprüften Seiten dieselben Namen.",
        "fr": "Les {k} composants répétés sur les {n} pages examinées portent les mêmes noms.",
        "it": "I {k} componenti ripetuti nelle {n} pagine esaminate hanno gli stessi nomi.",
    },
    "c324.name_differs": {
        "en": "The component labelled “{visible}” is announced as “{a}” here but as “{b}” on {page}.",
        "de": "Das Element mit der Beschriftung «{visible}» wird hier als «{a}», auf {page} aber als «{b}» angesagt.",
        "fr": "Le composant libellé « {visible} » est annoncé « {a} » ici, mais « {b} » sur {page}.",
        "it": "Il componente con l'etichetta «{visible}» è annunciato come «{a}» qui, ma come «{b}» in {page}.",
    },
    "c324.apertus_synonyms": {
        "en": "Apertus judged that “{a}” and “{b}” ({page}) are different words for the same function.",
        "de": "Apertus beurteilt «{a}» und «{b}» ({page}) als verschiedene Wörter für dieselbe Funktion.",
        "fr": "Apertus juge que « {a} » et « {b} » ({page}) sont des mots différents pour la même fonction.",
        "it": "Apertus giudica che «{a}» e «{b}» ({page}) siano parole diverse per la stessa funzione.",
    },
    "c324.apertus_same_or_pattern": {
        "en": "Apertus judged that “{a}” and “{b}” ({page}) follow one pattern.",
        "de": "Apertus beurteilt, dass «{a}» und «{b}» ({page}) einem Muster folgen.",
        "fr": "Apertus juge que « {a} » et « {b} » ({page}) suivent un même modèle.",
        "it": "Apertus giudica che «{a}» e «{b}» ({page}) seguano uno stesso schema.",
    },
    "c324.apertus_different_function": {
        "en": "Apertus judged that “{a}” and “{b}” ({page}) name different functions, which may be labelled differently.",
        "de": "Apertus beurteilt, dass «{a}» und «{b}» ({page}) verschiedene Funktionen benennen; sie dürfen verschieden heissen.",
        "fr": "Apertus juge que « {a} » et « {b} » ({page}) désignent des fonctions différentes, qui peuvent porter des noms différents.",
        "it": "Apertus giudica che «{a}» e «{b}» ({page}) indichino funzioni diverse, che possono avere nomi diversi.",
    },
    "c324.apertus_more_specific": {
        "en": "“{a}” and “{b}” ({page}) lead to the same place, but one names a narrower purpose. Whether this is the same function is for a person to decide.",
        "de": "«{a}» und «{b}» ({page}) führen zum selben Ziel, eines benennt aber einen engeren Zweck. Ob es dieselbe Funktion ist, muss eine Person entscheiden.",
        "fr": "« {a} » et « {b} » ({page}) mènent au même endroit, mais l'un désigne un but plus précis. Une personne doit décider s'il s'agit de la même fonction.",
        "it": "«{a}» e «{b}» ({page}) portano allo stesso punto, ma uno indica uno scopo più specifico. Una persona deve decidere se è la stessa funzione.",
    },
    "c324.apertus_unsure": {
        "en": "Apertus could not decide whether “{a}” and “{b}” ({page}) identify the same function. A person must check.",
        "de": "Apertus konnte nicht entscheiden, ob «{a}» und «{b}» ({page}) dieselbe Funktion bezeichnen. Eine Person muss prüfen.",
        "fr": "Apertus n'a pas pu décider si « {a} » et « {b} » ({page}) désignent la même fonction. Une personne doit vérifier.",
        "it": "Apertus non ha potuto decidere se «{a}» e «{b}» ({page}) indichino la stessa funzione. Una persona deve verificare.",
    },
    "c324.impact": {
        "en": "People who learn a control by its name, for example screen-reader or voice-control users, do not recognise it on the next page.",
        "de": "Wer ein Bedienelement an seinem Namen erkennt, etwa mit Screenreader oder Sprachsteuerung, findet es auf der nächsten Seite nicht wieder.",
        "fr": "Les personnes qui reconnaissent un contrôle à son nom, par exemple avec un lecteur d'écran ou la commande vocale, ne le retrouvent pas sur la page suivante.",
        "it": "Chi riconosce un comando dal suo nome, per esempio con un lettore di schermo o il controllo vocale, non lo ritrova nella pagina successiva.",
    },
    "c324.impact_ok": {
        "en": "People recognise the same controls by the same names on every page.",
        "de": "Man erkennt dieselben Bedienelemente auf jeder Seite am selben Namen.",
        "fr": "Les mêmes contrôles se reconnaissent au même nom sur chaque page.",
        "it": "Gli stessi comandi si riconoscono dallo stesso nome in ogni pagina.",
    },
    "c324.fix_hint": {
        "en": "Give this component the same name on every page, for example “{a}”.",
        "de": "Geben Sie diesem Element auf allen Seiten denselben Namen, zum Beispiel «{a}».",
        "fr": "Donnez à ce composant le même nom sur toutes les pages, par exemple « {a} ».",
        "it": "Date a questo componente lo stesso nome in tutte le pagine, per esempio «{a}».",
    },
    "c324.needs_url": {
        "en": "Consistent identification concerns a set of pages; pasted HTML has no site around it. Scan the page by its address.",
        "de": "Einheitliche Bezeichnung betrifft eine Gruppe von Seiten; eingefügtes HTML hat keine Website dazu. Scannen Sie die Seite über ihre Adresse.",
        "fr": "L'identification cohérente concerne un ensemble de pages ; le HTML collé n'a pas de site autour. Analysez la page par son adresse.",
        "it": "L'identificazione coerente riguarda un insieme di pagine; l'HTML incollato non ha un sito intorno. Analizzate la pagina tramite il suo indirizzo.",
    },
    "c324.too_few": {
        "en": "No other page of the site in the same language could be loaded. A person must compare the pages.",
        "de": "Es liess sich keine andere Seite derselben Website und Sprache laden. Eine Person muss die Seiten vergleichen.",
        "fr": "Aucune autre page du site dans la même langue n'a pu être chargée. Une personne doit comparer les pages.",
        "it": "Non è stato possibile caricare altre pagine del sito nella stessa lingua. Una persona deve confrontare le pagine.",
    },
    "c324.none": {
        "en": "No component with the same function appears on more than one sampled page.",
        "de": "Kein Bedienelement mit derselben Funktion kommt auf mehr als einer geprüften Seite vor.",
        "fr": "Aucun composant de même fonction n'apparaît sur plus d'une des pages examinées.",
        "it": "Nessun componente con la stessa funzione compare in più di una delle pagine esaminate.",
    },
})


def ident_key(s: str) -> str:
    """Normalised identification: case, punctuation and numbers ignored."""
    s = unicodedata.normalize("NFKC", s or "").casefold()
    s = re.sub(r"\d+", "#", s)
    s = re.sub(r"[^\w#]+", " ", s)
    return " ".join(s.split())


def _onclick(n: Node) -> str:
    return re.sub(r"\s+", "", n.attrs.get("onclick", ""))[:80]


def components(sp: SitePage) -> list[tuple[str, Node, str, str]]:
    """(function key, node, accessible name, visible text) of one page."""
    out = []
    for n in sp.doc.body.iter():
        if n.hidden() or n.closest(lambda a: a.hidden()) is not None:
            continue
        key = None
        if n.tag == "a" and n.attrs.get("href") and not n.attrs["href"].startswith("#"):
            region = region_of(n)
            target = page_key(urljoin(sp.url, n.attrs["href"]))
            if target == sp.key or "hreflang" in n.attrs or "lang" in n.attrs:
                continue  # the current page, or a link to another language version (another set of pages)
            icon_only = not n.text(visible=True) and n.find(lambda x: x.tag in ("img", "svg")) is not None
            if (region in ("nav", "header", "footer", "aside") and not is_breadcrumb(n)) or icon_only:
                key = f"link:{region}:{target}"
        elif n.tag == "button" or (n.tag == "input" and n.attrs.get("type", "").lower() in ("submit", "button", "image")):
            form = n.closest(lambda a: a.tag == "form")
            if form is not None and is_search_form(form):
                key = "search"
            elif _onclick(n):
                key = "action:" + _onclick(n)
            elif form is not None and n.attrs.get("type", "submit").lower() == "submit":
                key = "submit:" + page_key(urljoin(sp.url, form.attrs.get("action") or ""))
        elif n.tag == "input" and n.attrs.get("type", "").lower() == "search":
            key = "searchfield"
        if key:
            visible = (n.attrs.get("value") or "") if n.tag == "input" else n.text(visible=True)
            out.append((key, n, n.accessible_name(), visible))
    return out


def _contains(a: str, b: str) -> bool:
    return bool(a and b) and (a in b or b in a)


class ConsistentIdentification(SiteSampling, BaseCheck):
    criterion = "3.2.4"
    prompt_version = PROMPT_VERSION
    max_candidates = MAX_QUESTIONS + 1

    def candidates(self, page: CapturedPage) -> list[Candidate]:
        sample = self.site(page)
        doc = page_doc(page)
        root_html = doc.html_el.outer(200) if doc.html_el else "<html>"
        if sample.entry is None:
            return [self.candidate(page, selector="html", html=root_html, lang=page.lang, key="#site", kind="needs_url")]
        entry = sample.entry
        mine = components(entry)
        if not mine:
            return [self.candidate(page, selector="html", html=root_html, lang=page.lang, key="#site", kind="no_component")]
        others = sample.same_set()[1:]
        if not others:
            return [self.candidate(page, selector="html", html=root_html, lang=page.lang, key="#site", kind="too_few")]
        # function key → page → (name, visible, node), first occurrence per page
        seen: dict[str, dict[str, tuple[str, str, Node]]] = defaultdict(dict)
        for sp in [entry, *others]:
            for key, node, name, visible in components(sp):
                seen[key].setdefault(sp.key, (name, visible, node))
        repeated = {k: v for k, v in seen.items() if len(v) >= 2 and entry.key in v}
        if not repeated:
            return [self.candidate(page, selector="html", html=root_html, lang=page.lang, key="#site", kind="none")]
        out: list[Candidate] = []
        consistent = 0
        for key, per_page in repeated.items():
            names = Counter(ident_key(nm) for nm, _, _ in per_page.values())
            if len(names) == 1:
                consistent += 1
                continue
            my_name, my_visible, my_node = per_page[entry.key]
            # len(names) > 1, so at least one other page names it differently from this page
            other_key, (o_name, o_visible, o_node) = next(
                (pk, v) for pk, v in per_page.items() if pk != entry.key and ident_key(v[0]) != ident_key(my_name))
            same_visible = bool(ident_key(my_visible)) and ident_key(my_visible) == ident_key(o_visible)
            kind = "name_differs" if same_visible and not _contains(ident_key(my_name), ident_key(o_name)) else "ask"
            html = my_node.outer(400) + "\n" + o_node.outer(400)
            out.append(self.candidate(
                page, selector=live_selector(page, my_node), html=html, text=f"{my_name} | {o_name}",
                accessible_name=my_name, lang=page.lang, key="#" + key[:120], kind=kind, function=key,
                name_here=my_name, name_other=o_name, visible=my_visible or o_visible,
                other_page=short_path(other_key, sample.root),
                context={"label_on_this_page": my_name, "label_on_other_page": o_name,
                         "component": "search" if key.startswith("search") else
                         ("link to the same address" if key.startswith("link:") else "button with the same action")}))
            if len(out) >= MAX_QUESTIONS:
                break
        if not out:
            nav = doc.find(lambda n: n.tag == "nav" or n.role == "navigation")
            out.append(self.candidate(page, selector=live_selector(page, nav), html=nav.outer(600) if nav else root_html,
                                      text=nav.text() if nav else "", lang=page.lang, key="#site", kind="passed",
                                      k=consistent, n=1 + len(others)))
        return out

    # -- decisions (code) -------------------------------------------------------------------
    def decide(self, c: Candidate) -> Finding | None:
        ui = self.ui_lang
        kind = c.extra.get("kind")
        if kind in ("needs_url", "too_few"):
            return self.note(c, f"c324.{kind}", source="heuristic")
        if kind in ("no_component", "none"):
            return self.finding(c, outcome="inapplicable", source="heuristic", confidence="medium", excerpt="",
                                explanation=t("c324.none", ui), user_impact=t("impact.review", ui))
        if kind == "passed":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium",
                                excerpt=c.text[:300] if c.text else "",
                                explanation=t("c324.passed", ui, k=c.extra.get("k", 0), n=c.extra.get("n", 0)),
                                user_impact=t("c324.impact_ok", ui))
        if kind == "name_differs":
            a, b = c.extra["name_here"], c.extra["name_other"]
            return self.finding(c, outcome="failed", source="heuristic", confidence="high", excerpt=a,
                                explanation=t("c324.name_differs", ui, visible=c.extra.get("visible", ""), a=a, b=b,
                                              page=c.extra.get("other_page", "")),
                                user_impact=t("c324.impact", ui), fix_hint=t("c324.fix_hint", ui, a=c.extra["visible"]))
        return None  # "ask" → Apertus

    # -- the closed question --------------------------------------------------------------------
    SYSTEM = (
        "You check WCAG 2.1 success criterion 3.2.4 Consistent Identification. The same component (a link to the "
        "same address, or a button with the same action) appears on two pages of one website, with two different "
        "labels. Classify the two labels:\n"
        "- same_or_pattern: the same words, or one pattern where only a number or the current item changes\n"
        "- synonyms: different words for the same function\n"
        "- more_specific: one label names a narrower part or purpose of the same destination\n"
        "- different_function: the labels name different functions\n"
        "- unsure: none of these\n"
        "quote: the label on the other page, copied exactly."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        return self.task(
            system=self.system_prompt(self.SYSTEM, c),
            element={"label_on_this_page": c.extra["name_here"], "label_on_other_page": c.extra["name_other"]},
            context={"component": c.context.get("component", "")},
            question="Do these two labels identify the same function consistently?",
            schema=category_schema(CATEGORIES),
            max_tokens=120,
        )

    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        category = answer.get("category", "unsure")
        outcome = CATEGORY_OUTCOME.get(category, "cantTell")
        kw = {"a": c.extra["name_here"], "b": c.extra["name_other"], "page": c.extra.get("other_page", "")}
        key = f"c324.apertus_{category}" if category in CATEGORY_OUTCOME else "c324.apertus_unsure"
        impact = {"failed": t("c324.impact", ui), "passed": t("c324.impact_ok", ui)}.get(outcome, t("impact.review", ui))
        quote = (answer.get("quote") or "").strip() or (c.extra["name_other"] if outcome != "failed" else "")
        return self.finding(c, outcome=outcome, source="apertus",
                            confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
                            excerpt=htmllib.unescape(quote), explanation=t(key, ui, **kw), user_impact=impact,
                            reason=answer.get("reason"), reason_code=key.split(".")[-1],
                            fix_hint=t("c324.fix_hint", ui, a=kw["a"]) if outcome == "failed" else None)


CHECK = ConsistentIdentification
