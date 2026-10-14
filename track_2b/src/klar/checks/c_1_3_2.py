"""1.3.2 Meaningful Sequence, level A: does the code order (what screen readers read)
keep the meaning of the order users SEE? No ACT rule exists for this criterion.

Facts (code, capture/js/c_1_3_2.js on the live page):
  * reorders: flex/grid containers, and containers with absolutely positioned children,
    whose children are shown in an order that is neither the DOM order read row by row
    nor column by column (element boxes; CSS order, *-reverse, grid placement and
    absolute positioning all show up in the boxes). The longest run of children that
    keeps its order is computed; the others are the "moved" blocks.
  * pre_columns: ≥ 3 lines of preformatted text with a second text column made of
    spaces at the same character position (F33/F34).
  * spaced_words: words spelt with spaces between the letters (F32).
  * layout_tables: tables without th/caption holding prose; a sentence that ends
    without punctuation and continues in the cell BELOW is read in the wrong order
    when the table is linearised row by row (F49).

Cascade
  spaced word                                       → failed (heuristic, F32)
  text columns made of spaces                       → failed (heuristic, F33/F34)
  layout table, sentence continues in the cell below → failed (heuristic, F49)
  layout table, every cell self-contained           → passed (heuristic)
  reordered container, only decorative blocks moved → passed (heuristic)
  reordered container, only fixed/sticky overlays moved → skipped (2.4.3 looks at their focus order)
  reordered container with text                     → Apertus (text; a crop of the container
      is attached when a vision backend is available, never required). The model gets the
      text of each block in code order (A, B, C…) and the visual order ("B, A, C"):
      "Does reading the blocks in code order keep the meaning of the visual order?"
      relation: sequence | independent | secondary | other
                → failed | passed | cantTell | cantTell

Limits: only flex/grid containers and absolutely positioned children are compared
(floats, transforms and multi-column text are not); without a live page only the
spaced-word and space-column rules run (from the serialised DOM).
"""

from __future__ import annotations

import re
from pathlib import Path

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema, norm_ws
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "1.3.2/v1"
JS = (Path(__file__).resolve().parents[1] / "capture" / "js" / "c_1_3_2.js").read_text(encoding="utf-8")

RELATIONS = ["sequence", "independent", "secondary", "other"]
RELATION_OUTCOME = {"sequence": "failed", "independent": "passed", "secondary": "cantTell", "other": "cantTell"}
MAX_SEGMENTS = 8
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

_SPACED = re.compile(r"(?:^|[\s(«\"'„“])((?:[^\W\d_] ){4,}[^\W\d_])(?=$|[\s.,:;!?)»\"'“”])")
_GAP = re.compile(r"\S( {3,}|\t+)\S")

register({
    "c132.spaced_word": {
        "en": "The word \"{word}\" is spelt with spaces between its letters.",
        "de": "Das Wort «{word}» ist mit Leerzeichen zwischen den Buchstaben geschrieben.",
        "fr": "Le mot « {word} » est écrit avec des espaces entre les lettres.",
        "it": "La parola «{word}» è scritta con spazi tra le lettere.",
    },
    "c132.pre_columns": {
        "en": "Text columns are built with spaces in preformatted text. Read line by line, the columns are mixed.",
        "de": "Textspalten sind mit Leerzeichen in vorformatiertem Text gebaut. Zeile für Zeile gelesen, werden die Spalten vermischt.",
        "fr": "Des colonnes de texte sont construites avec des espaces dans un texte préformaté. Lues ligne par ligne, les colonnes se mélangent.",
        "it": "Colonne di testo sono costruite con spazi in un testo preformattato. Lette riga per riga, le colonne si mescolano.",
    },
    "c132.table_split": {
        "en": "A sentence continues in the table cell below, but tables are read row by row: the text is read in the wrong order.",
        "de": "Ein Satz geht in der Tabellenzelle darunter weiter, Tabellen werden aber Zeile für Zeile gelesen: Der Text wird in falscher Reihenfolge vorgelesen.",
        "fr": "Une phrase continue dans la cellule du dessous, mais un tableau est lu ligne par ligne : le texte est lu dans le mauvais ordre.",
        "it": "Una frase continua nella cella sottostante, ma le tabelle si leggono riga per riga: il testo viene letto nell'ordine sbagliato.",
    },
    "c132.table_ok": {
        "en": "Layout table whose cells are self-contained: reading it row by row keeps the meaning.",
        "de": "Layouttabelle mit in sich abgeschlossenen Zellen: Zeilenweises Lesen erhält den Sinn.",
        "fr": "Tableau de mise en page aux cellules autonomes : la lecture ligne par ligne garde le sens.",
        "it": "Tabella di impaginazione con celle autonome: la lettura riga per riga mantiene il senso.",
    },
    "c132.decorative": {
        "en": "Only decorative content is shown in a different order than in the code.",
        "de": "Nur dekorative Inhalte werden in anderer Reihenfolge angezeigt als im Code.",
        "fr": "Seul du contenu décoratif est affiché dans un autre ordre que dans le code.",
        "it": "Solo contenuti decorativi sono mostrati in un ordine diverso da quello del codice.",
    },
    "c132.apertus_sequence": {
        "en": "Blocks are shown in a different order than in the code, and Apertus judged that the code order breaks the sequence that the screen shows.",
        "de": "Blöcke werden in anderer Reihenfolge angezeigt als im Code; Apertus beurteilt, dass die Code-Reihenfolge die angezeigte Abfolge zerstört.",
        "fr": "Des blocs sont affichés dans un autre ordre que dans le code ; selon Apertus, l'ordre du code rompt la séquence affichée.",
        "it": "Dei blocchi sono mostrati in un ordine diverso da quello del codice; secondo Apertus l'ordine del codice rompe la sequenza mostrata.",
    },
    "c132.apertus_independent": {
        "en": "Blocks are shown in a different order than in the code, but Apertus judged them independent: their order does not change the meaning.",
        "de": "Blöcke werden in anderer Reihenfolge angezeigt als im Code; Apertus beurteilt sie aber als unabhängig: Die Reihenfolge ändert den Sinn nicht.",
        "fr": "Des blocs sont affichés dans un autre ordre que dans le code, mais selon Apertus ils sont indépendants : l'ordre ne change pas le sens.",
        "it": "Dei blocchi sono mostrati in un ordine diverso da quello del codice, ma secondo Apertus sono indipendenti: l'ordine non cambia il senso.",
    },
    "c132.apertus_secondary": {
        "en": "A secondary block (summary, note or introduction) is shown elsewhere than in the code. Whether its position changes the meaning depends on the author's intent.",
        "de": "Ein Nebenblock (Zusammenfassung, Hinweis oder Einleitung) steht optisch an anderer Stelle als im Code. Ob das den Sinn ändert, hängt von der Absicht der Autorin oder des Autors ab.",
        "fr": "Un bloc secondaire (résumé, remarque ou introduction) est affiché ailleurs que dans le code. Que cela change le sens dépend de l'intention de l'auteur.",
        "it": "Un blocco secondario (riassunto, nota o introduzione) è mostrato altrove rispetto al codice. Se ciò cambi il senso dipende dall'intenzione dell'autore.",
    },
    "c132.apertus_unsure": {
        "en": "Blocks are shown in a different order than in the code; Apertus could not tell whether this changes the meaning. A person must check it.",
        "de": "Blöcke werden in anderer Reihenfolge angezeigt als im Code; Apertus konnte nicht entscheiden, ob das den Sinn ändert. Eine Person muss es prüfen.",
        "fr": "Des blocs sont affichés dans un autre ordre que dans le code ; Apertus n'a pas pu décider si cela change le sens. Une personne doit le vérifier.",
        "it": "Dei blocchi sono mostrati in un ordine diverso da quello del codice; Apertus non ha potuto stabilire se ciò cambi il senso. Una persona deve verificarlo.",
    },
    "c132.impact": {
        "en": "Screen-reader users get the content in the code order, which breaks the order shown on screen.",
        "de": "Screenreader-Nutzende erhalten den Inhalt in der Code-Reihenfolge, die die angezeigte Reihenfolge zerstört.",
        "fr": "Les personnes utilisant un lecteur d'écran reçoivent le contenu dans l'ordre du code, qui rompt l'ordre affiché.",
        "it": "Chi usa un lettore di schermo riceve il contenuto nell'ordine del codice, che rompe l'ordine mostrato.",
    },
    "c132.impact_spaced": {
        "en": "Screen readers spell the letters one by one instead of reading the word.",
        "de": "Screenreader buchstabieren die Buchstaben einzeln, statt das Wort zu lesen.",
        "fr": "Les lecteurs d'écran épellent les lettres une à une au lieu de lire le mot.",
        "it": "I lettori di schermo sillabano le lettere una per una invece di leggere la parola.",
    },
    "c132.impact_ok": {
        "en": "Screen-reader users get the content in an order that keeps its meaning.",
        "de": "Screenreader-Nutzende erhalten den Inhalt in einer Reihenfolge, die den Sinn erhält.",
        "fr": "Les personnes utilisant un lecteur d'écran reçoivent le contenu dans un ordre qui garde son sens.",
        "it": "Chi usa un lettore di schermo riceve il contenuto in un ordine che ne mantiene il senso.",
    },
    "c132.fix_order": {
        "en": "Put the blocks in the code in the order in which they must be read; do not reorder them with CSS (order, grid placement, reverse).",
        "de": "Ordnen Sie die Blöcke im Code in der Lesereihenfolge an; ordnen Sie sie nicht mit CSS um (order, Grid-Platzierung, reverse).",
        "fr": "Placez les blocs dans le code dans l'ordre de lecture ; ne les réordonnez pas avec CSS (order, placement de grille, reverse).",
        "it": "Disponete i blocchi nel codice nell'ordine di lettura; non riordinateli con CSS (order, posizionamento grid, reverse).",
    },
    "c132.fix_pre": {
        "en": "Use real columns (CSS) or a table instead of spaces.",
        "de": "Verwenden Sie echte Spalten (CSS) oder eine Tabelle statt Leerzeichen.",
        "fr": "Utilisez de vraies colonnes (CSS) ou un tableau au lieu d'espaces.",
        "it": "Usate vere colonne (CSS) o una tabella invece degli spazi.",
    },
    "c132.fix_spaced": {
        "en": "Write the word normally and create the spacing with CSS letter-spacing.",
        "de": "Schreiben Sie das Wort normal und erzeugen Sie den Abstand mit CSS letter-spacing.",
        "fr": "Écrivez le mot normalement et créez l'espacement avec letter-spacing en CSS.",
        "it": "Scrivete la parola normalmente e create la spaziatura con letter-spacing in CSS.",
    },
    "c132.fix_table": {
        "en": "Do not use a table for layout, or keep each sentence within one cell.",
        "de": "Verwenden Sie keine Tabelle für das Layout, oder lassen Sie jeden Satz in einer Zelle.",
        "fr": "N'utilisez pas de tableau pour la mise en page, ou gardez chaque phrase dans une cellule.",
        "it": "Non usate una tabella per l'impaginazione, oppure tenete ogni frase in una sola cella.",
    },
})


def static_facts(page: CapturedPage) -> dict:
    """Without a live page: spaced words (from the extracted passages) and space columns
    in <pre> (from the serialised DOM)."""
    from klar.checks.c_1_3_1 import parse_html

    out: dict = {"reorders": [], "pre_columns": [], "spaced_words": [], "layout_tables": []}
    for p in page.passages:
        m = _SPACED.search(p.get("text", ""))
        if m:
            out["spaced_words"].append({"selector": p.get("container_selector") or p["selector"], "html": p.get("html", ""),
                                        "lang": p.get("lang"), "word": m.group(1), "text": p.get("container_text") or p["text"]})
    root = parse_html(page.html)
    for n in root.iter():
        if n.tag != "pre" or any(d.tag == "code" for d in n.iter()):
            continue
        lines = n.text().split("\n")
        gaps = [m.end() - 1 for m in (_GAP.search(ln) for ln in lines) if m]
        if len(gaps) >= 3 and max(sum(abs(x - g) <= 2 for x in gaps) for g in gaps) >= 3:
            out["pre_columns"].append({"selector": n.path(), "html": f"<pre>{n.text()[:1200]}</pre>", "lang": page.lang,
                                       "lines": len(gaps), "first": [ln for ln in lines if ln.strip()][:3],
                                       "text": n.text()[:1500]})
    return out


class MeaningfulSequence(BaseCheck):
    criterion = "1.3.2"
    prompt_version = PROMPT_VERSION
    needs_vision = False  # text question (both orders as text); the crop is an optional extra
    max_candidates = 40
    prompt_html_chars = 300

    def facts(self, page: CapturedPage) -> dict:
        pre = page.elements.get("c132")  # tests inject [facts] (a list, like every element collection)
        if isinstance(pre, list):
            pre = pre[0] if pre else None
        if pre is not None:
            return pre
        if page.live is not None:
            try:
                data = page.evaluate(JS, {"max": 30})
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        return static_facts(page)

    # -- 1. candidates -----------------------------------------------------------------------
    def candidates(self, page: CapturedPage) -> list[Candidate]:
        f = self.facts(page)
        out: list[Candidate] = []
        for s in f.get("spaced_words", []):
            out.append(self.candidate(page, selector=s["selector"], html=s.get("html", ""), text=s.get("text", ""),
                                      lang=s.get("lang") or page.lang, kind="spaced_word", word=s.get("word", ""),
                                      key="#spaced"))
        for p in f.get("pre_columns", []):
            out.append(self.candidate(page, selector=p["selector"], html=p.get("html", ""), text=p.get("text", ""),
                                      lang=p.get("lang") or page.lang, kind="pre_columns",
                                      first_line=(p.get("first") or [""])[0]))
        for tb in f.get("layout_tables", []):
            split = tb.get("split")
            out.append(self.candidate(page, selector=tb["selector"], html=tb.get("html", ""), text=tb.get("text", ""),
                                      lang=tb.get("lang") or page.lang, kind="table_split" if split else "table_ok",
                                      split_end=(split or {}).get("cur", "")))
        for r in f.get("reorders", []):
            c = self.reorder_candidate(page, r)
            if c is not None:
                out.append(c)
        return out[: self.max_candidates]

    def reorder_candidate(self, page: CapturedPage, r: dict) -> Candidate | None:
        segs = sorted(r.get("segments", []), key=lambda s: s["i"])
        moved = set(r.get("moved", []))
        if r.get("fixed_only"):
            return None  # a fixed/sticky overlay (banner, toolbar) is not part of the reading sequence here
        if r.get("decorative_only"):
            return self.candidate(page, selector=r["selector"], html=r.get("html", ""), text=r.get("text", ""),
                                  lang=r.get("lang") or page.lang, kind="decorative")
        keep = [s for s in segs if s.get("text") or s["i"] in moved]
        if len(keep) > MAX_SEGMENTS:
            others = [s for s in keep if s["i"] not in moved]
            keep = sorted([s for s in keep if s["i"] in moved][:MAX_SEGMENTS] +
                          others[: max(0, MAX_SEGMENTS - len(moved))], key=lambda s: s["i"])
        if sum(1 for s in keep if s.get("text")) < 2:
            return None
        label = {s["i"]: LETTERS[k] for k, s in enumerate(keep)}
        segments = " ".join(f"[{label[s['i']]}] {s.get('text') or '(no text)'}" for s in keep)
        visual = ", ".join(label[i] for i in r.get("visual", []) if i in label)
        moved_labels = ", ".join(label[i] for i in r.get("moved", []) if i in label)
        text = " ".join(s.get("text", "") for s in keep if s.get("text"))
        c = self.candidate(page, selector=r["selector"], html=r.get("html", ""), text=text,
                           context={"segments_in_code_order": segments}, lang=r.get("lang") or page.lang,
                           kind="reorder", visual_order=visual, moved=moved_labels,
                           focusables=sum(s.get("focusables", 0) for s in keep))
        if self.vision and page.live is not None:
            c.screenshot = page.screenshot(r["selector"], c.id)
        return c

    # -- 2. deterministic decisions ---------------------------------------------------------------
    def decide(self, c: Candidate) -> Finding | None:
        kind, ui = c.extra.get("kind"), self.ui_lang
        if kind == "spaced_word":
            word = c.extra.get("word", "")
            return self.finding(c, outcome="failed", source="heuristic", confidence="high",
                                excerpt=word if word in c.text else None,
                                explanation=t("c132.spaced_word", ui, word=word), user_impact=t("c132.impact_spaced", ui),
                                fix_hint=t("c132.fix_spaced", ui))
        if kind == "pre_columns":
            first = c.extra.get("first_line", "")
            return self.finding(c, outcome="failed", source="heuristic", confidence="high",
                                excerpt=first if first and first in c.text else None,
                                explanation=t("c132.pre_columns", ui), user_impact=t("c132.impact", ui),
                                fix_hint=t("c132.fix_pre", ui))
        if kind == "table_split":
            end = c.extra.get("split_end", "")
            return self.finding(c, outcome="failed", source="heuristic", confidence="medium",
                                excerpt=end if end and end in c.text else None,
                                explanation=t("c132.table_split", ui), user_impact=t("c132.impact", ui),
                                fix_hint=t("c132.fix_table", ui))
        if kind == "table_ok":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium",
                                explanation=t("c132.table_ok", ui), user_impact=t("c132.impact_ok", ui))
        if kind == "decorative":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium",
                                explanation=t("c132.decorative", ui), user_impact=t("c132.impact_ok", ui))
        return None

    # -- 3. the closed question ---------------------------------------------------------------------
    SYSTEM = (
        "You check WCAG 2.1 success criterion 1.3.2 Meaningful Sequence for ONE container whose blocks are "
        "shown on screen in a different order than in the code. Screen readers read the blocks in code order "
        "(`segments_in_code_order`, labelled A, B, C…); sighted users see them in `visual_order`; `moved` are "
        "the blocks out of place (an attached image, if any, shows the container).\n"
        "relation:\n"
        "- sequence: the blocks only make sense in one order (consecutive steps or stages, a question and its "
        "answer, a label and its value) and the code order breaks that order\n"
        "- independent: the blocks are independent of each other (navigation, a side box, separate items, "
        "decoration); either order keeps the meaning\n"
        "- secondary: a moved block is a summary, note, kicker or introduction for another block; whether its "
        "position matters is debatable\n"
        "- other: none of these, or unsure\n"
        "quote: the text of one moved block, copied exactly (at most 80 characters)."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        # ui_lang is deliberately unused: prompts are identical for every UI language.
        return self.task(
            system=self.system_prompt(self.SYSTEM, c),
            element={"visual_order": c.extra.get("visual_order", ""), "moved": c.extra.get("moved", "")},
            context=c.context, images=[c.screenshot] if c.screenshot else [],
            question="Does reading the blocks in code order keep the meaning of the visual order?",
            schema=category_schema(RELATIONS), max_tokens=140)

    # -- 4. interpretation -----------------------------------------------------------------------------
    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        cat = answer.get("category", "other")
        outcome = RELATION_OUTCOME.get(cat, "cantTell")
        key = {"sequence": "c132.apertus_sequence", "independent": "c132.apertus_independent",
               "secondary": "c132.apertus_secondary"}.get(cat, "c132.apertus_unsure")
        impact = {"failed": t("c132.impact", ui), "passed": t("c132.impact_ok", ui)}.get(outcome, t("impact.review", ui))
        return self.finding(c, outcome=outcome, source="apertus",
                            confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
                            excerpt=self.model_excerpt(c, answer, outcome), explanation=t(key, ui), user_impact=impact,
                            fix_hint=t("c132.fix_order", ui) if outcome == "failed" else None,
                            reason=answer.get("reason"), reason_code=f"apertus_{cat}")

    @staticmethod
    def default_excerpt(c: Candidate) -> str:
        return norm_ws(c.text or c.html)[:300]


CHECK = MeaningfulSequence
