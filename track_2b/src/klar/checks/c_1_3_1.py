"""1.3.1 Info and Relationships, level A: structure that is SHOWN but not CODED.
No ACT rule covers the judgement part (ffd0e9, d0f69e, a25f45, bc4a75… are axe-core's
presence rules), so findings carry no ACT id.

Facts (code, capture/js/c_1_3_1.js on the live page; a smaller static parse of the
serialised DOM when there is no live page):
  * visual headings: short (≤ 12 words) standalone text, bold or ≥ 1.15 × the body
    text size, followed by content, not inside h1–h6 / role=heading. Style compared
    with the page's real headings (size, weight, colour).
  * tables: th/scope/caption, role, nested tables, block content in cells, whether
    the first row / first column is visually distinguished (background, weight).
  * lists drawn with characters: ≥ 3 consecutive lines (<br> or sibling blocks) with
    the same bullet or dash, or counting numbers / letters, outside ul/ol.
  * radio / checkbox groups: fieldset + legend or a named role=group / radiogroup?
  * label/value pairs in a two-column CSS grid; bold run-in labels ("Label: text").

Cascade
  heading-like text
    whole text is a link (card title)                     → cantTell (heuristic)
    same size, weight and colour as a real heading level  → failed (heuristic, F2/H42)
    bold at body-text size                                → cantTell (heuristic): minor
                                                            heading or lead-in, author intent
    larger than body text, no matching heading style      → Apertus (text; an optional crop is attached
                                                            when vision is on, never required):
        "Does this text act as a heading for the content that follows?"
        role: heading | lead_in | label | emphasis | other
              → failed | passed | passed | passed | cantTell
    no computed style (static fallback)                   → cantTell (heuristic): style unknown
  table
    role=presentation/none with th, scope or caption      → failed (heuristic, F92)
    role=presentation/none, no header markup              → passed (heuristic)
    th + strong layout signals (nested table, block cells) → Apertus "data or layout?"
                                                            layout → failed (F46), data → passed
    th, no layout signals                                 → passed (heuristic, H51/H63)
    no th, header row/column only visually distinguished,
      ≥ 3 rows, short cells                               → failed (heuristic, F91)
    no th, ≥ 3 rows × ≥ 2 short columns, no distinction    → Apertus "data or layout?"
                                                            data → failed, layout → passed
  list drawn with characters                              → failed (heuristic, H48)
  radio/checkbox group
    fieldset + legend, or a named group                   → passed (heuristic, H71/ARIA17)
    not grouped, every option label ≤ 2 words, a visible
      question before them                                → failed (heuristic, H71, PROTOCOL F4)
    not grouped, labels ≤ 2 words, no visible question     → cantTell (heuristic)
    not grouped, longer labels                            → Apertus: "Does each option label make
        sense without the question?" self_explanatory | needs_question | other
        → passed | failed | cantTell
  label/value pairs in two CSS columns: with colons       → passed; without → cantTell
  bold run-in label at the start of a paragraph           → passed (emphasis, not a heading)

Limits: fake headings inside tables, nav, header/footer landmarks and dialogs are not
examined; colour-only structure is 1.4.1's job; ARIA structure errors are axe-core's.
Static fallback (no live page): tables, character lists, groups and bold-only lines.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema, norm_ws
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "1.3.1/v1"
JS = (Path(__file__).resolve().parents[1] / "capture" / "js" / "c_1_3_1.js").read_text(encoding="utf-8")

ROLES = ["heading", "lead_in", "label", "emphasis", "other"]
ROLE_OUTCOME = {"heading": "failed", "lead_in": "passed", "label": "passed", "emphasis": "passed", "other": "cantTell"}
TABLE_TYPES = ["data", "layout", "other"]
GROUP_TYPES = ["self_explanatory", "needs_question", "other"]
GROUP_OUTCOME = {"self_explanatory": "passed", "needs_question": "failed", "other": "cantTell"}
BIG_RATIO = 1.15
SHORT_CELL = 40  # average characters per cell of a data-like table

register({
    "c131.fake_heading": {
        "en": "This text looks like a level-{level} heading (same size, weight and colour) but is not marked up as a heading.",
        "de": "Dieser Text sieht aus wie eine Überschrift der Ebene {level} (gleiche Grösse, Stärke und Farbe), ist aber nicht als Überschrift ausgezeichnet.",
        "fr": "Ce texte a l'apparence d'un titre de niveau {level} (même taille, graisse et couleur), mais il n'est pas balisé comme titre.",
        "it": "Questo testo appare come un titolo di livello {level} (stessa dimensione, spessore e colore), ma non è marcato come titolo.",
    },
    "c131.apertus_heading": {
        "en": "Apertus judged that this larger text works as a heading for the content that follows, but it is not marked up as a heading.",
        "de": "Apertus beurteilt diesen grösseren Text als Überschrift des folgenden Inhalts; er ist aber nicht als Überschrift ausgezeichnet.",
        "fr": "Selon Apertus, ce texte plus grand sert de titre au contenu qui suit, mais il n'est pas balisé comme titre.",
        "it": "Secondo Apertus questo testo più grande funge da titolo per il contenuto che segue, ma non è marcato come titolo.",
    },
    "c131.apertus_not_heading": {
        "en": "Apertus judged that this styled text is not a heading ({role}); no heading markup is needed.",
        "de": "Apertus beurteilt diesen hervorgehobenen Text nicht als Überschrift ({role}); es braucht keine Überschrift.",
        "fr": "Selon Apertus, ce texte mis en forme n'est pas un titre ({role}) ; aucun balisage de titre n'est nécessaire.",
        "it": "Secondo Apertus questo testo formattato non è un titolo ({role}); non serve un markup da titolo.",
    },
    "c131.apertus_unsure": {
        "en": "Apertus could not tell whether this structure needs markup. A person must check it.",
        "de": "Apertus konnte nicht entscheiden, ob diese Struktur ausgezeichnet werden muss. Eine Person muss es prüfen.",
        "fr": "Apertus n'a pas pu décider si cette structure doit être balisée. Une personne doit le vérifier.",
        "it": "Apertus non ha potuto stabilire se questa struttura va marcata. Una persona deve verificarlo.",
    },
    "c131.minor_heading": {
        "en": "A bold line at body-text size stands alone before other text. It may be an unmarked minor heading or a lead-in; the author's intent decides.",
        "de": "Eine fette Zeile in Grundschriftgrösse steht allein vor weiterem Text. Sie kann eine nicht ausgezeichnete Zwischenüberschrift oder ein Einleitungssatz sein; das entscheidet die Absicht der Autorin oder des Autors.",
        "fr": "Une ligne en gras, de la taille du texte courant, précède un autre texte. Il peut s'agir d'un intertitre non balisé ou d'une accroche ; l'intention de l'auteur décide.",
        "it": "Una riga in grassetto, della dimensione del testo normale, precede altro testo. Può essere un sottotitolo non marcato o un'introduzione; decide l'intenzione dell'autore.",
    },
    "c131.style_unknown": {
        "en": "A bold line stands alone before other text. Without the rendered page its size cannot be compared with the headings. A person must check whether it is a heading.",
        "de": "Eine fette Zeile steht allein vor weiterem Text. Ohne gerenderte Seite lässt sich ihre Grösse nicht mit den Überschriften vergleichen. Eine Person muss prüfen, ob es eine Überschrift ist.",
        "fr": "Une ligne en gras précède seule un autre texte. Sans la page rendue, sa taille ne peut pas être comparée aux titres. Une personne doit vérifier s'il s'agit d'un titre.",
        "it": "Una riga in grassetto precede da sola altro testo. Senza la pagina renderizzata la sua dimensione non si può confrontare con i titoli. Una persona deve verificare se è un titolo.",
    },
    "c131.group_no_question": {
        "en": "These options are not grouped (no fieldset/legend or named group), and no visible question was found next to them. A person must check whether a question belongs to them.",
        "de": "Diese Optionen sind nicht gruppiert (kein fieldset/legend und keine benannte Gruppe), und daneben wurde keine sichtbare Frage gefunden. Eine Person muss prüfen, ob eine Frage zu ihnen gehört.",
        "fr": "Ces options ne sont pas groupées (pas de fieldset/legend ni de groupe nommé), et aucune question visible n'a été trouvée à côté. Une personne doit vérifier si une question s'y rapporte.",
        "it": "Queste opzioni non sono raggruppate (nessun fieldset/legend né gruppo con nome) e accanto non è stata trovata alcuna domanda visibile. Una persona deve verificare se vi si riferisce una domanda.",
    },
    "c131.card_title": {
        "en": "A large bold link works as the title of a card or teaser but is not a heading. Whether such titles must be headings is debated.",
        "de": "Ein grosser fetter Link dient als Titel einer Karte oder eines Teasers, ist aber keine Überschrift. Ob solche Titel Überschriften sein müssen, ist umstritten.",
        "fr": "Un grand lien en gras sert de titre à une carte ou à une accroche, mais n'est pas un titre balisé. L'obligation d'en faire un titre est débattue.",
        "it": "Un grande link in grassetto funge da titolo di una scheda o di un teaser, ma non è un titolo. Se debba esserlo è controverso.",
    },
    "c131.table_visual_headers": {
        "en": "This data table shows its header row or column only visually (bold or coloured cells). There are no th cells, so the headers are not announced.",
        "de": "Diese Datentabelle zeigt ihre Kopfzeile oder Kopfspalte nur optisch (fett oder farbig). Es gibt keine th-Zellen, daher werden die Kopfzellen nicht vorgelesen.",
        "fr": "Ce tableau de données ne montre sa ligne ou colonne d'en-tête que visuellement (gras ou couleur). Sans cellules th, les en-têtes ne sont pas annoncés.",
        "it": "Questa tabella di dati mostra la riga o colonna d'intestazione solo visivamente (grassetto o colore). Senza celle th le intestazioni non vengono annunciate.",
    },
    "c131.apertus_data_table": {
        "en": "Apertus judged this table to hold data that depends on row or column headers, but it has no header cells (th).",
        "de": "Apertus beurteilt diese Tabelle als Datentabelle, deren Werte von Zeilen- oder Spaltenköpfen abhängen; sie hat aber keine Kopfzellen (th).",
        "fr": "Selon Apertus, ce tableau contient des données qui dépendent d'en-têtes de ligne ou de colonne, mais il n'a pas de cellules d'en-tête (th).",
        "it": "Secondo Apertus questa tabella contiene dati che dipendono da intestazioni di riga o colonna, ma non ha celle d'intestazione (th).",
    },
    "c131.apertus_layout_table": {
        "en": "Apertus judged this table to be a layout table: no cell needs a header.",
        "de": "Apertus beurteilt diese Tabelle als Layouttabelle: Keine Zelle braucht einen Tabellenkopf.",
        "fr": "Selon Apertus, ce tableau sert à la mise en page : aucune cellule n'a besoin d'en-tête.",
        "it": "Secondo Apertus questa tabella serve all'impaginazione: nessuna cella ha bisogno di intestazione.",
    },
    "c131.apertus_layout_th": {
        "en": "Apertus judged this table to be a layout table, but it contains header cells or a caption that announce relationships which do not exist.",
        "de": "Apertus beurteilt diese Tabelle als Layouttabelle; sie enthält aber Kopfzellen oder eine Beschriftung, die nicht vorhandene Beziehungen ankündigen.",
        "fr": "Selon Apertus, ce tableau sert à la mise en page, mais il contient des en-têtes ou une légende qui annoncent des relations inexistantes.",
        "it": "Secondo Apertus questa tabella serve all'impaginazione, ma contiene intestazioni o una didascalia che annunciano relazioni inesistenti.",
    },
    "c131.presentation_th": {
        "en": "role=\"{role}\" removes the table semantics, but the table has header markup: the relationships between headers and data are lost.",
        "de": "role=\"{role}\" entfernt die Tabellensemantik, die Tabelle hat aber Kopfzellen: Die Beziehung zwischen Kopf und Daten geht verloren.",
        "fr": "role=\"{role}\" supprime la sémantique du tableau, alors qu'il a des en-têtes : le lien entre en-têtes et données est perdu.",
        "it": "role=\"{role}\" elimina la semantica della tabella, che però ha intestazioni: il legame tra intestazioni e dati va perso.",
    },
    "c131.layout_ok": {
        "en": "Layout table marked with role=presentation and without header markup.",
        "de": "Layouttabelle mit role=presentation und ohne Kopfzellen.",
        "fr": "Tableau de mise en page avec role=presentation et sans en-têtes.",
        "it": "Tabella di impaginazione con role=presentation e senza intestazioni.",
    },
    "c131.table_ok": {
        "en": "The table marks its headers with th cells.",
        "de": "Die Tabelle zeichnet ihre Kopfzellen mit th aus.",
        "fr": "Le tableau balise ses en-têtes avec des cellules th.",
        "it": "La tabella marca le intestazioni con celle th.",
    },
    "c131.fake_list": {
        "en": "{n} items are drawn as a list with typed characters instead of a list element (ul/ol).",
        "de": "{n} Einträge sind mit getippten Zeichen als Liste dargestellt statt mit einem Listenelement (ul/ol).",
        "fr": "{n} éléments sont présentés comme une liste avec des caractères tapés au lieu d'un élément de liste (ul/ol).",
        "it": "{n} voci sono presentate come elenco con caratteri digitati invece che con un elemento di lista (ul/ol).",
    },
    "c131.group_missing": {
        "en": "The options are not grouped with their question (no fieldset with legend and no named group).",
        "de": "Die Optionen sind nicht mit ihrer Frage gruppiert (kein fieldset mit legend und keine benannte Gruppe).",
        "fr": "Les options ne sont pas groupées avec leur question (pas de fieldset avec legend ni de groupe nommé).",
        "it": "Le opzioni non sono raggruppate con la loro domanda (nessun fieldset con legend né gruppo con nome).",
    },
    "c131.group_ok": {
        "en": "The options are grouped with their question (fieldset with legend or a named group).",
        "de": "Die Optionen sind mit ihrer Frage gruppiert (fieldset mit legend oder benannte Gruppe).",
        "fr": "Les options sont groupées avec leur question (fieldset avec legend ou groupe nommé).",
        "it": "Le opzioni sono raggruppate con la loro domanda (fieldset con legend o gruppo con nome).",
    },
    "c131.apertus_self_explanatory": {
        "en": "Apertus judged that each option label is understandable without the question.",
        "de": "Apertus beurteilt jede Optionsbeschriftung als verständlich ohne die Frage.",
        "fr": "Selon Apertus, chaque libellé d'option se comprend sans la question.",
        "it": "Secondo Apertus ogni etichetta d'opzione è comprensibile senza la domanda.",
    },
    "c131.apertus_needs_question": {
        "en": "Apertus judged that the option labels only make sense with the question, but the question is not grouped with them.",
        "de": "Apertus beurteilt die Optionsbeschriftungen als nur mit der Frage verständlich; die Frage ist aber nicht mit ihnen gruppiert.",
        "fr": "Selon Apertus, les libellés d'option n'ont de sens qu'avec la question, qui n'est pas groupée avec eux.",
        "it": "Secondo Apertus le etichette d'opzione hanno senso solo con la domanda, che però non è raggruppata con esse.",
    },
    "c131.kv_grid": {
        "en": "Short label/value pairs are laid out in two visual columns without list or table markup. Whether they need structure is debated.",
        "de": "Kurze Bezeichnung-Wert-Paare stehen in zwei optischen Spalten ohne Listen- oder Tabellenauszeichnung. Ob sie Struktur brauchen, ist umstritten.",
        "fr": "De courtes paires libellé/valeur sont disposées en deux colonnes visuelles, sans balisage de liste ni de tableau. Leur besoin de structure est débattu.",
        "it": "Brevi coppie etichetta/valore sono disposte in due colonne visive senza markup di elenco o tabella. Se serva una struttura è controverso.",
    },
    "c131.kv_colon": {
        "en": "Label/value pairs with a colon: the relationship is stated in the text itself.",
        "de": "Bezeichnung-Wert-Paare mit Doppelpunkt: Die Beziehung steht im Text selbst.",
        "fr": "Paires libellé/valeur avec deux-points : la relation est indiquée dans le texte.",
        "it": "Coppie etichetta/valore con i due punti: la relazione è indicata nel testo stesso.",
    },
    "c131.run_in": {
        "en": "A bold run-in label inside a paragraph: emphasis marked up with b/strong, not a heading.",
        "de": "Fett gesetzter Einstieg innerhalb eines Absatzes: Hervorhebung mit b/strong, keine Überschrift.",
        "fr": "Amorce en gras dans un paragraphe : mise en évidence avec b/strong, pas un titre.",
        "it": "Attacco in grassetto dentro un paragrafo: enfasi con b/strong, non un titolo.",
    },
    "c131.impact_heading": {
        "en": "Screen-reader users cannot reach this section with heading navigation and do not hear that a new section starts.",
        "de": "Screenreader-Nutzende erreichen diesen Abschnitt nicht über die Überschriften-Navigation und hören nicht, dass ein neuer Abschnitt beginnt.",
        "fr": "Les personnes utilisant un lecteur d'écran ne peuvent pas atteindre cette section par les titres et n'entendent pas qu'une section commence.",
        "it": "Chi usa un lettore di schermo non raggiunge questa sezione con la navigazione per titoli e non sente che inizia una nuova sezione.",
    },
    "c131.impact_table": {
        "en": "Screen-reader users hear the cell values without their row and column headers.",
        "de": "Screenreader-Nutzende hören die Zellwerte ohne ihre Zeilen- und Spaltenköpfe.",
        "fr": "Les personnes utilisant un lecteur d'écran entendent les valeurs des cellules sans leurs en-têtes de ligne et de colonne.",
        "it": "Chi usa un lettore di schermo sente i valori delle celle senza le intestazioni di riga e colonna.",
    },
    "c131.impact_layout": {
        "en": "Screen-reader users hear table headers and relationships that are not in the content.",
        "de": "Screenreader-Nutzende hören Tabellenköpfe und Beziehungen, die es im Inhalt nicht gibt.",
        "fr": "Les personnes utilisant un lecteur d'écran entendent des en-têtes et des relations absentes du contenu.",
        "it": "Chi usa un lettore di schermo sente intestazioni e relazioni che nel contenuto non esistono.",
    },
    "c131.impact_list": {
        "en": "Screen-reader users do not hear that this is a list or how many items it has.",
        "de": "Screenreader-Nutzende hören nicht, dass dies eine Liste ist und wie viele Einträge sie hat.",
        "fr": "Les personnes utilisant un lecteur d'écran n'entendent pas qu'il s'agit d'une liste ni combien elle compte d'éléments.",
        "it": "Chi usa un lettore di schermo non sente che si tratta di un elenco né quante voci contiene.",
    },
    "c131.impact_group": {
        "en": "Screen-reader users hear the options without the question they answer.",
        "de": "Screenreader-Nutzende hören die Optionen ohne die Frage, auf die sie antworten.",
        "fr": "Les personnes utilisant un lecteur d'écran entendent les options sans la question à laquelle elles répondent.",
        "it": "Chi usa un lettore di schermo sente le opzioni senza la domanda a cui rispondono.",
    },
    "c131.impact_ok": {
        "en": "Screen-reader users get the same structure that the page shows visually.",
        "de": "Screenreader-Nutzende erhalten dieselbe Struktur, die die Seite optisch zeigt.",
        "fr": "Les personnes utilisant un lecteur d'écran reçoivent la même structure que celle affichée.",
        "it": "Chi usa un lettore di schermo riceve la stessa struttura che la pagina mostra visivamente.",
    },
    "c131.fix_heading": {
        "en": "In the CMS, format this text as a heading (level {level}) instead of styling a paragraph.",
        "de": "Formatieren Sie diesen Text im CMS als Überschrift (Ebene {level}) statt einen Absatz zu gestalten.",
        "fr": "Dans le CMS, formatez ce texte comme titre (niveau {level}) au lieu de styler un paragraphe.",
        "it": "Nel CMS formattate questo testo come titolo (livello {level}) invece di formattare un paragrafo.",
    },
    "c131.fix_table": {
        "en": "Mark the header row or column as header cells (th) with scope=\"col\" or scope=\"row\".",
        "de": "Zeichnen Sie die Kopfzeile oder -spalte als Kopfzellen (th) mit scope=\"col\" oder scope=\"row\" aus.",
        "fr": "Balisez la ligne ou colonne d'en-tête en cellules th avec scope=\"col\" ou scope=\"row\".",
        "it": "Marcate la riga o colonna d'intestazione come celle th con scope=\"col\" o scope=\"row\".",
    },
    "c131.fix_layout": {
        "en": "Use CSS for the layout, or remove th, caption and summary from the layout table.",
        "de": "Verwenden Sie CSS für das Layout oder entfernen Sie th, caption und summary aus der Layouttabelle.",
        "fr": "Utilisez CSS pour la mise en page, ou retirez th, caption et summary du tableau de mise en page.",
        "it": "Usate CSS per l'impaginazione, oppure togliete th, caption e summary dalla tabella di impaginazione.",
    },
    "c131.fix_list": {
        "en": "Use the bulleted or numbered list of the CMS editor instead of typed characters.",
        "de": "Verwenden Sie die Aufzählungs- oder Nummerierungsliste des CMS-Editors statt getippter Zeichen.",
        "fr": "Utilisez la liste à puces ou numérotée de l'éditeur du CMS au lieu de caractères tapés.",
        "it": "Usate l'elenco puntato o numerato dell'editor del CMS invece di caratteri digitati.",
    },
    "c131.fix_group": {
        "en": "Wrap the options in a fieldset whose legend states the question.",
        "de": "Fassen Sie die Optionen in ein fieldset, dessen legend die Frage nennt.",
        "fr": "Placez les options dans un fieldset dont la legend énonce la question.",
        "it": "Racchiudete le opzioni in un fieldset la cui legend riporta la domanda.",
    },
})


# --- static fallback: a tiny DOM from the serialised HTML (no live page) -------------------

_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag: str, attrs: dict[str, str], parent: "Node | None"):
        self.tag, self.attrs, self.children, self.parent = tag, attrs, [], parent

    def iter(self):
        for ch in self.children:
            if isinstance(ch, Node):
                yield ch
                yield from ch.iter()

    def text(self) -> str:
        parts: list[str] = []
        for ch in self.children:
            if isinstance(ch, Node):
                if ch.tag in ("script", "style", "template"):
                    continue
                parts.append("\n" if ch.tag == "br" else ch.text())
            else:
                parts.append(ch)
        return "".join(parts)

    def ancestors(self):
        n = self.parent
        while n is not None:
            yield n
            n = n.parent

    def path(self) -> str:
        """CSS path in the extractor's style (id if present, else nth-of-type)."""
        parts: list[str] = []
        node: Node | None = self
        while node is not None and node.tag != "#root":
            if node.attrs.get("id"):
                parts.insert(0, "#" + node.attrs["id"])
                break
            part = node.tag
            if node.parent is not None:
                same = [c for c in node.parent.children if isinstance(c, Node) and c.tag == node.tag]
                if len(same) > 1:
                    part += f":nth-of-type({same.index(node) + 1})"
            parts.insert(0, part)
            node = node.parent
        return " > ".join(parts)


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: (v or "") for k, v in attrs}, self.cur)
        self.cur.children.append(node)
        if tag not in _VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, {k: (v or "") for k, v in attrs}, self.cur))

    def handle_endtag(self, tag):
        n: Node | None = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def parse_html(html: str) -> Node:
    b = _Builder()
    try:
        b.feed(html or "")
        b.close()
    except Exception:  # never let a broken document stop a scan
        pass
    return b.root


def _outer(n: Node) -> str:
    attrs = "".join(f' {k}="{v}"' for k, v in n.attrs.items())
    return f"<{n.tag}{attrs}>{norm_ws(n.text())[:300]}</{n.tag}>"


_MARK = re.compile(r"^\s*([•·▪▫◦‣⁃∙●○■□►▶▸✓✔✗→*]|[-–—](?=\s)|\d{1,2}[.)](?=\s))")


def static_facts(html: str, lang: str | None) -> dict:
    """The subset of the JS facts that needs no rendering."""
    root = parse_html(html)
    out: dict = {"body_size": None, "heading_styles": [], "visual_headings": [], "tables": [], "fake_lists": [],
                 "choice_groups": [], "kv_grids": [], "run_ins": [], "static": True}
    headings = {"h1", "h2", "h3", "h4", "h5", "h6"}
    for n in root.iter():
        anc = {a.tag for a in n.ancestors()}
        if n.tag == "table" and len(out["tables"]) < 40:
            rows = [r for r in n.iter() if r.tag == "tr"]
            cells = [c for c in n.iter() if c.tag in ("td", "th")]
            texts = [norm_ws(c.text()) for c in cells if norm_ws(c.text())]
            first = [c for c in rows[0].children if isinstance(c, Node) and c.tag in ("td", "th")] if rows else []
            out["tables"].append({
                "selector": n.path(), "html": _outer(n), "lang": lang, "role": n.attrs.get("role"),
                "rows": len(rows), "cols": max((sum(1 for c in r.children if isinstance(c, Node) and c.tag in ("td", "th"))
                                                for r in rows), default=0),
                "th": sum(1 for c in cells if c.tag == "th"), "scope": any("scope" in c.attrs or "headers" in c.attrs for c in cells),
                "caption": next((norm_ws(c.text()) for c in n.iter() if c.tag == "caption"), ""),
                "summary": n.attrs.get("summary", ""), "nested": any(c.tag == "table" for c in n.iter()),
                "block_cells": sum(1 for c in cells if any(d.tag in {"p", "ul", "ol", "form", "table"} | headings for d in c.iter())),
                "cells": len(cells), "avg_len": sum(map(len, texts)) / len(texts) if texts else 0,
                "max_len": max(map(len, texts), default=0), "numeric_share": 0.0,
                "first_row_distinct": len(first) >= 2 and all(any(d.tag in ("b", "strong") for d in c.iter()) for c in first),
                "first_col_distinct": False,
                "linear": " / ".join(" | ".join(norm_ws(c.text())[:40] for c in r.children if isinstance(c, Node))
                                     for r in rows[:8])[:600],
            })
        elif n.tag in ("p", "div") and not anc & {"ul", "ol", "li", "pre", "nav", "table"} and len(out["fake_lists"]) < 40:
            if any(isinstance(c, Node) and c.tag == "br" for c in n.children):
                lines = [s.strip() for s in n.text().split("\n") if s.strip()]
                marked = [ln for ln in lines if _MARK.match(ln)]
                if len(marked) >= 3:
                    out["fake_lists"].append({"selector": n.path(), "html": _outer(n), "text": norm_ws(n.text()),
                                              "lang": lang, "items": len(marked), "first": lines[:4], "how": "br"})
            kids = [c for c in n.children if isinstance(c, Node)]
            if (n.tag == "p" and len(kids) == 1 and kids[0].tag in ("b", "strong")
                    and norm_ws(kids[0].text()) == norm_ws(n.text()) and 0 < len(norm_ws(n.text()).split()) <= 12
                    and not re.search(r"[.!?:]$", norm_ws(n.text())) and not anc & {"a", "button", "label", "header", "footer"}):
                out["visual_headings"].append({"selector": n.path(), "html": _outer(n), "text": norm_ws(n.text()),
                                               "lang": lang, "bold": True, "big": None, "matches": [], "is_link": False,
                                               "next_text": "", "ratio": None})
    groups: dict[str, list[Node]] = {}
    for n in root.iter():
        if n.tag == "input" and n.attrs.get("type") in ("radio", "checkbox") and n.attrs.get("name"):
            groups.setdefault(n.attrs["type"] + "|" + n.attrs["name"], []).append(n)
    for inputs in groups.values():
        if len(inputs) < 2:
            continue
        box = inputs[0].parent
        while box is not None and not all(box in list(i.ancestors()) for i in inputs):
            box = box.parent
        if box is None or box.tag == "#root":
            continue
        fs = next((a for a in inputs[0].ancestors() if a.tag == "fieldset"), None)
        legend = next((norm_ws(c.text()) for c in fs.iter() if c.tag == "legend"), "") if fs else ""
        grp = next((a for a in inputs[0].ancestors() if a.attrs.get("role") in ("group", "radiogroup")), None)
        labels_by_id = {lb.attrs.get("for"): norm_ws(lb.text()) for lb in root.iter() if lb.tag == "label"}
        out["choice_groups"].append({
            "selector": box.path(), "html": _outer(box), "text": norm_ws(box.text()), "lang": lang,
            "type": inputs[0].attrs.get("type"), "count": len(inputs),
            "labels": [labels_by_id.get(i.attrs.get("id"), "") or i.attrs.get("aria-label", "") for i in inputs][:12],
            "legend": legend, "group_name": (grp.attrs.get("aria-label", "") or grp.attrs.get("aria-labelledby", "")) if grp else "",
            "in_fieldset": bool(legend), "question": "", "first": inputs[0].path(),
        })
    return out


class InfoAndRelationships(BaseCheck):
    criterion = "1.3.1"
    prompt_version = PROMPT_VERSION
    needs_vision = False  # text questions; a crop is attached only as an optional extra when vision is on
    guard_numbers = True
    max_candidates = 80

    # -- 1. facts ----------------------------------------------------------------------------
    def facts(self, page: CapturedPage) -> dict:
        pre = page.elements.get("c131")  # tests inject [facts] (a list, like every element collection)
        if isinstance(pre, list):
            pre = pre[0] if pre else None  # tests and replays may inject facts
        if pre is not None:
            return pre
        if page.live is not None:
            try:
                data = page.evaluate(JS, {"max": 40})
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        return static_facts(page.html, page.lang)

    def candidates(self, page: CapturedPage) -> list[Candidate]:
        f = self.facts(page)
        out: list[Candidate] = []
        body = f.get("body_size")

        for h in f.get("visual_headings", []):
            text = h.get("text", "")
            if h.get("is_link"):
                kind = "card_title"
            elif h.get("matches"):
                kind = "fake_heading"
            elif f.get("static"):
                kind = "style_unknown"  # no rendering: size and weight cannot be compared with the headings
            elif h.get("big"):
                kind = "ask_heading"
            else:
                kind = "minor_heading"
            ratio = h.get("ratio")
            style = (f"font size {ratio:.2f} x body text" if ratio else "font size unknown") + \
                    (", bold" if h.get("bold") else "") + "; no heading on the page has this style"
            context = {"next_text": (h.get("next_text") or "")[:300]} if kind.startswith("ask") else {}
            c = self.candidate(page, selector=h["selector"], html=h.get("html", ""), text=text, context=context,
                               lang=h.get("lang") or page.lang, kind=kind, level=(h.get("matches") or [2])[0],
                               style=style, body_size=body)
            if kind == "ask_heading" and self.vision:  # optional: the question is answerable from text
                c.screenshot = page.screenshot(h["selector"], c.id)
            out.append(c)

        for tb in f.get("tables", []):
            kind = self.table_kind(tb)
            if kind is None:
                continue
            context = {"rows": tb.get("linear", "")} if kind.startswith("ask") else {}
            if kind.startswith("ask") and tb.get("caption"):
                context["caption"] = tb["caption"]
            out.append(self.candidate(page, selector=tb["selector"], html=tb.get("html", ""), text=tb.get("linear", ""),
                                      context=context, lang=tb.get("lang") or page.lang, kind=kind,
                                      role=tb.get("role") or "", th=tb.get("th", 0)))

        for fl in f.get("fake_lists", []):
            first = fl.get("first") or []
            out.append(self.candidate(page, selector=fl["selector"], html=fl.get("html", ""), text=fl.get("text", ""),
                                      lang=fl.get("lang") or page.lang, kind="fake_list", items=fl.get("items", 3),
                                      first_item=first[0] if first else ""))

        for g in f.get("choice_groups", []):
            labels = [x for x in g.get("labels", []) if x]
            if g.get("in_fieldset") or g.get("group_name"):
                kind = "group_ok"
            elif labels and all(len(x.split()) <= 2 for x in labels):
                # PROTOCOL F4 needs a visible question that is not associated; without one the
                # short labels may simply be unlabelled options (3.3.2), not a 1.3.1 grouping failure
                kind = "group_missing" if (g.get("question") or "").strip() else "group_no_question"
            elif labels:
                kind = "ask_group"
            else:
                continue
            context = {"options": " | ".join(labels)[:300], "question": g.get("question", "")} if kind == "ask_group" else {}
            out.append(self.candidate(page, selector=g["selector"], html=g.get("html", ""), text=" | ".join(labels),
                                      context=context, lang=g.get("lang") or page.lang, kind=kind, labels=labels))

        for kv in f.get("kv_grids", []):
            out.append(self.candidate(page, selector=kv["selector"], html=kv.get("html", ""), text=kv.get("text", ""),
                                      lang=kv.get("lang") or page.lang, kind="kv_colon" if kv.get("colon") else "kv_grid"))

        for r in f.get("run_ins", []):
            out.append(self.candidate(page, selector=r["selector"], html=r.get("html", ""), text=r.get("text", ""),
                                      lang=r.get("lang") or page.lang, kind="run_in"))
        return out[: self.max_candidates]

    @staticmethod
    def table_kind(tb: dict) -> str | None:
        role = (tb.get("role") or "").strip().lower()
        has_headers = tb.get("th", 0) > 0 or bool(tb.get("caption")) or bool(tb.get("summary"))
        rows, cols, avg = tb.get("rows", 0), tb.get("cols", 0), tb.get("avg_len", 0)
        layout_strong = bool(tb.get("nested")) or (tb.get("block_cells", 0) >= 2 and avg >= 40) or \
            (rows == 1 and cols >= 2 and avg >= 60)
        if role in ("presentation", "none"):
            return "presentation_th" if has_headers or tb.get("scope") else "layout_ok"
        if tb.get("th", 0) > 0:
            return "ask_layout_th" if layout_strong else "table_ok"
        if layout_strong or rows < 3 or cols < 2 or avg > SHORT_CELL:
            return None  # a layout table without header markup is fine here (reading order: 1.3.2)
        if tb.get("first_row_distinct") or tb.get("first_col_distinct"):
            return "table_visual_headers"
        return "ask_table"

    # -- 2. deterministic decisions ----------------------------------------------------------------
    def decide(self, c: Candidate) -> Finding | None:
        kind, ui = c.extra.get("kind"), self.ui_lang
        level = c.extra.get("level", 2)
        if kind == "fake_heading":
            return self.finding(c, outcome="failed", source="heuristic", confidence="high", excerpt=c.text,
                                explanation=t("c131.fake_heading", ui, level=level),
                                user_impact=t("c131.impact_heading", ui), fix_hint=t("c131.fix_heading", ui, level=level))
        if kind == "minor_heading":
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="medium", excerpt=c.text,
                                explanation=t("c131.minor_heading", ui), user_impact=t("impact.review", ui))
        if kind == "style_unknown":
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="low", excerpt=c.text,
                                explanation=t("c131.style_unknown", ui), user_impact=t("impact.review", ui))
        if kind == "group_no_question":
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="low",
                                explanation=t("c131.group_no_question", ui), user_impact=t("impact.review", ui))
        if kind == "card_title":
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="medium", excerpt=c.text,
                                explanation=t("c131.card_title", ui), user_impact=t("impact.review", ui))
        if kind == "presentation_th":
            role = c.extra.get("role", "presentation")
            return self.finding(c, outcome="failed", source="heuristic", confidence="high",
                                excerpt=f'role="{role}"' if f'role="{role}"' in c.html else None,
                                explanation=t("c131.presentation_th", ui, role=role),
                                user_impact=t("c131.impact_table", ui), fix_hint=t("c131.fix_table", ui))
        if kind == "layout_ok":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium",
                                explanation=t("c131.layout_ok", ui), user_impact=t("c131.impact_ok", ui))
        if kind == "table_ok":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium",
                                explanation=t("c131.table_ok", ui), user_impact=t("c131.impact_ok", ui))
        if kind == "table_visual_headers":
            return self.finding(c, outcome="failed", source="heuristic", confidence="high",
                                explanation=t("c131.table_visual_headers", ui),
                                user_impact=t("c131.impact_table", ui), fix_hint=t("c131.fix_table", ui))
        if kind == "fake_list":
            first = c.extra.get("first_item", "")
            return self.finding(c, outcome="failed", source="heuristic", confidence="high",
                                excerpt=first if first and first in c.text else None,
                                explanation=t("c131.fake_list", ui, n=c.extra.get("items", 3)),
                                user_impact=t("c131.impact_list", ui), fix_hint=t("c131.fix_list", ui))
        if kind == "group_ok":
            return self.finding(c, outcome="passed", source="heuristic", confidence="high",
                                explanation=t("c131.group_ok", ui), user_impact=t("c131.impact_ok", ui))
        if kind == "group_missing":
            return self.finding(c, outcome="failed", source="heuristic", confidence="high",
                                explanation=t("c131.group_missing", ui), user_impact=t("c131.impact_group", ui),
                                fix_hint=t("c131.fix_group", ui))
        if kind == "kv_grid":
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="medium",
                                explanation=t("c131.kv_grid", ui), user_impact=t("impact.review", ui))
        if kind == "kv_colon":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium",
                                explanation=t("c131.kv_colon", ui), user_impact=t("c131.impact_ok", ui))
        if kind == "run_in":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", excerpt=c.text,
                                explanation=t("c131.run_in", ui), user_impact=t("c131.impact_ok", ui))
        return None

    # -- 3. closed questions ----------------------------------------------------------------------
    SYSTEM_HEADING = (
        "You check WCAG 2.1 success criterion 1.3.1 Info and Relationships for ONE short text that is styled "
        "bold or larger than the body text but is NOT marked up as a heading. `style` compares its look with "
        "the page; `next_text` is the content that follows it (an attached image, if any, shows the text).\n"
        "role:\n"
        "- heading: it names the topic of the content that follows, like a section title\n"
        "- lead_in: it is the opening of a paragraph or an introduction, not a title\n"
        "- label: it labels one value, field or item next to it\n"
        "- emphasis: it highlights a warning or key statement that is itself the content\n"
        "- other: none of these, or unsure\n"
        "quote: the styled text, copied exactly."
    )
    SYSTEM_TABLE = (
        "You check WCAG 2.1 success criterion 1.3.1 Info and Relationships for ONE HTML table. `rows` lists the "
        "cell texts row by row (cells separated by |, rows by /). `has_header_cells` says whether the table "
        "marks header cells (th).\n"
        "table_type:\n"
        "- data: cell values only make sense together with a header row or header column\n"
        "- layout: the table only places blocks of content side by side; no cell needs a header\n"
        "- other: unsure\n"
        "quote: one cell text, copied exactly."
    )
    SYSTEM_GROUP = (
        "You check WCAG 2.1 success criterion 1.3.1 Info and Relationships for ONE group of radio buttons or "
        "checkboxes that is not grouped with its question (no fieldset/legend). A screen-reader user hears each "
        "option label alone, without `question`.\n"
        "- self_explanatory: every option label says on its own what is being chosen\n"
        "- needs_question: at least one option label only makes sense together with the question\n"
        "- other: unsure\n"
        "quote: one option label, copied exactly."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        # ui_lang is deliberately unused: prompts are identical for every UI language.
        kind = c.extra.get("kind")
        if kind in ("ask_layout_th", "ask_table"):
            return self.task(
                system=self.system_prompt(self.SYSTEM_TABLE, c),
                element={"html_start": self.prompt_html(c), "has_header_cells": "yes" if c.extra.get("th") else "no"},
                context=c.context, question="Is this a data table or a layout table?",
                schema=category_schema(TABLE_TYPES), max_tokens=140)
        if kind == "ask_group":
            return self.task(
                system=self.system_prompt(self.SYSTEM_GROUP, c),
                element={"type": "options"}, context=c.context,
                question="Does each option label make sense without the question?",
                schema=category_schema(GROUP_TYPES), max_tokens=140)
        images = [c.screenshot] if c.screenshot else []
        return self.task(
            system=self.system_prompt(self.SYSTEM_HEADING, c),
            element={"text": c.text, "style": c.extra.get("style", "")}, context=c.context, images=images,
            question="Does this text act as a heading for the content that follows?",
            schema=category_schema(ROLES), max_tokens=140)

    # -- 4. interpretation -------------------------------------------------------------------------
    def interpret(self, c: Candidate, answer: dict) -> Finding:
        kind, ui = c.extra.get("kind"), self.ui_lang
        cat = answer.get("category", "other")
        conf = answer.get("confidence", "low")
        common = dict(source="apertus", reason=answer.get("reason"))
        if kind in ("ask_layout_th", "ask_table"):
            has_th = kind == "ask_layout_th"
            if cat == "data":
                outcome = "passed" if has_th else "failed"
                key = "c131.table_ok" if has_th else "c131.apertus_data_table"
            elif cat == "layout":
                outcome = "failed" if has_th else "passed"
                key = "c131.apertus_layout_th" if has_th else "c131.apertus_layout_table"
            else:
                outcome, key = "cantTell", "c131.apertus_unsure"
            impact = {"failed": t("c131.impact_layout" if has_th else "c131.impact_table", ui),
                      "passed": t("c131.impact_ok", ui)}.get(outcome, t("impact.review", ui))
            fix = t("c131.fix_layout" if has_th else "c131.fix_table", ui) if outcome == "failed" else None
            return self.finding(c, outcome=outcome, confidence=conf if outcome != "cantTell" else "low",
                                reason_code=f"apertus_{cat}", explanation=t(key, ui), user_impact=impact,
                                fix_hint=fix, excerpt=self.model_excerpt(c, answer, outcome), **common)
        if kind == "ask_group":
            outcome = GROUP_OUTCOME.get(cat, "cantTell")
            key = {"self_explanatory": "c131.apertus_self_explanatory",
                   "needs_question": "c131.apertus_needs_question"}.get(cat, "c131.apertus_unsure")
            impact = {"failed": t("c131.impact_group", ui), "passed": t("c131.impact_ok", ui)}.get(outcome, t("impact.review", ui))
            return self.finding(c, outcome=outcome, confidence=conf if outcome != "cantTell" else "low",
                                reason_code=f"apertus_{cat}", explanation=t(key, ui), user_impact=impact,
                                fix_hint=t("c131.fix_group", ui) if outcome == "failed" else None,
                                excerpt=self.model_excerpt(c, answer, outcome), **common)
        outcome = ROLE_OUTCOME.get(cat, "cantTell")
        if outcome == "failed":
            return self.finding(c, outcome="failed", confidence=conf, reason_code="apertus_heading",
                                explanation=t("c131.apertus_heading", ui), user_impact=t("c131.impact_heading", ui),
                                fix_hint=t("c131.fix_heading", ui, level=c.extra.get("level", 2)),
                                excerpt=self.model_excerpt(c, answer, "failed"), **common)
        if outcome == "passed":
            return self.finding(c, outcome="passed", confidence=conf, reason_code=f"apertus_{cat}",
                                explanation=t("c131.apertus_not_heading", ui, role=cat.replace("_", " ")),
                                user_impact=t("c131.impact_ok", ui), excerpt=self.model_excerpt(c, answer, "passed"),
                                **common)
        return self.finding(c, outcome="cantTell", confidence="low", reason_code="apertus_unsure",
                            explanation=t("c131.apertus_unsure", ui), user_impact=t("impact.review", ui),
                            excerpt=self.model_excerpt(c, answer, "cantTell"), **common)


CHECK = InfoAndRelationships
