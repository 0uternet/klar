"""1.3.3 Sensory Characteristics, level A. No ACT judgement rule applies to the text of
an instruction; technique G96, failures F14 (shape or location only) and F26 (a
graphical symbol alone). Colour alone is 1.4.1; here colour counts together with shape,
size, position or sound.

Facts in code
  * Candidates: visible text blocks (4–120 words) that contain a sensory word (shape,
    colour, size, position or sound; generic DE · FR · IT · EN lexicon below) AND look
    like an instruction (an operating verb, or a word for a control, field, menu, table…),
    or that refer to a sound. No candidate on the page → no finding (inapplicable).
  * The instruction quotes a text (in «», "", „“, “”, ‹›) that is the VISIBLE text of a
    control, heading, caption, legend or label on the page   → passed (heuristic, G96):
    the sensory words are only an extra cue.
  * It quotes a name that exists only as a hidden name (aria-label, title, alt)
                                                             → cantTell (heuristic): whether
    a non-visible name is enough is disputed (PROTOCOL §1.3.3 C1).
  * It mentions an asterisk and a visible label on the page contains "*"
                                                             → passed (heuristic): the cue is text.

Asked to Apertus (one question per remaining instruction)
  The instruction + the controls of its section (visible text and accessible name) + the
  element that follows it. CATEGORICAL question "How does the instruction identify the
  item it refers to?", mapped in code:
      visible_text     → passed      the item is also named by its visible text
      reading_order    → passed      "below/above" pointing to the one next item in reading order
      text_symbol      → passed      the cue is a visible text character
      sensory_only     → failed      only shape, colour, size, position or sound (F14, F26)
      hidden_name      → cantTell    a name that is not visible on screen
      purpose_only     → cantTell    only the purpose, which merely overlaps the control's label
      not_instruction  → inapplicable  the words describe the physical world or decoration
      unsure           → cantTell
  The quote must be copied from the instruction (evidence guard).

Known limits: instructions split over several blocks are judged block by block; a
sound cue's visual counterpart is only seen if it is in the same section; the
lexicon covers the four national/working languages, not dialect spellings.
"""

from __future__ import annotations

import re
import unicodedata

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema
from klar.checks.c_2_4_5 import Document, Node, norm_text, page_doc
from klar.i18n import register, t
from klar.langid import word_count
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "1.3.3/v2"  # v2: screen positions are sensory
MIN_WORDS, MAX_WORDS = 4, 120
MAX_CONTROLS = 8
MAX_INSTRUCTIONS = 12

# -- lexicon (written for Klar.; one regex per family, all four languages) ------------------
_F = re.IGNORECASE
# Adjectives take their inflected forms only (so "Grossrat", "grossartig" or "Kleinkind" are
# not sizes), "links" is case-sensitive (the noun "Links" is a hyperlink), "des Rechts"
# (of the law) is not a position, the bare "weiss" (knows) is not a colour, and "Kreis"
# before a name or a number is a district.
_ADJ_DE = r"(?:e[nmrs]?)?"
SHAPE = re.compile(
    r"\b(?:rund" + _ADJ_DE + r"|eckig" + _ADJ_DE + r"|viereckig" + _ADJ_DE + r"|quadratisch" + _ADJ_DE +
    r"|dreieck(?:ig" + _ADJ_DE + r")?|kreis(?:e|en|förmig" + _ADJ_DE + r")?(?!\s+(?-i:[A-ZÄÖÜ\d]))|"
    r"stern(?:e|en)?|pfeil(?:e|en)?|lupe|"
    r"zahnrad|herzsymbol|kreuz(?:chen)?|"
    r"rond(?:e|s|es)?|carré(?:e|s|es)?|triangle|triangulaire|cercle|étoile|flèche|loupe|engrenage|croix|"
    r"rotond[oaie]|tond[oaie]|triangol[oaie]|cerchi(?:o|etto)|stell[ae]|frecc[ei]a|lente|ingranaggio|croce|crocetta|"
    r"round|square|circle|circular|stars?|arrows?|magnifier|magnifying|gear|cog|cross|shaped?|form[ea]|"
    r"symbol(?:e|s)?|simbol[oi]|icon[ae]?s?|icône|pictogram(?:me|ma|s)?|piktogramm|pittogramm[ai])\b", _F)
COLOUR = re.compile(
    r"\b(?:rot" + _ADJ_DE + r"|grün" + _ADJ_DE + r"|blau" + _ADJ_DE + r"|gelb" + _ADJ_DE + r"|orange" + _ADJ_DE +
    r"|grau" + _ADJ_DE + r"|schwarz" + _ADJ_DE + r"|weiss(?:e[nmrs]?)|violett" + _ADJ_DE + r"|farbig" + _ADJ_DE +
    r"|rouges?|vert(?:e|s|es)?|bleu(?:e|s|es)?|jaunes?|gris(?:e|es)?|noir(?:e|s|es)?|blanc(?:s|he|hes)?|"
    r"ross[oaie]|verd[ei]|blu|azzurr[oaie]|giall[oaie]|arancion[ei]|grigi[oae]?|ner[oaie]|bianc[oaih]e?|"
    r"red|green|blue|yellow|gr[ae]y|black|white|purple)\b", _F)
POSITION = re.compile(
    r"(?-i:\blinks\b)|(?<!des\s)\brechts\b|\b(?:oben|unten|oberhalb|unterhalb|darüber|darunter|nebenan|"
    r"seitlich" + _ADJ_DE + r"|ecke|spalte|seitenleiste|"
    r"gauche|droite|en\s+haut|en\s+bas|ci-dessus|ci-dessous|au-dessus|au-dessous|en\s+dessous|"
    r"à\s+côté|coin|colonne|sinistra|destra|in\s+alto|in\s+basso|sopra|sotto|accanto|angolo|colonna|"
    r"left|right|top|bottom|above|below|beside|next\s+to|corner|sidebar|column)\b", _F)
SIZE = re.compile(r"\b(?:gross" + _ADJ_DE + r"|grösser" + _ADJ_DE + r"|klein" + _ADJ_DE + r"|kleiner" + _ADJ_DE +
                  r"|grand(?:e|s|es)?|petit(?:e|s|es)?|piccol[oaie]|big(?:ger)?|large(?:r)?|small(?:er)?)\b", _F)
SOUND = re.compile(
    r"\b(?:ton|töne|signalton|piep\w*|klingel\w*|hören|hörbar" + _ADJ_DE + r"|akustisch" + _ADJ_DE +
    r"|sonore\w*|bip\w*|entend\w*|sonnerie\w*|"
    r"suono\w*|acustic\w*|squill\w*|sentirete|sentite|"
    r"sound\w*|beep\w*|tone|chime\w*|hear\w*|audible)\b", _F)
CUE_DISTANCE = 8  # a sensory word counts only within this many words of an instruction cue
CUE = re.compile(
    r"\b(?:klick\w*|drück\w*|wähl\w*|tipp\w*|benutz\w*|verwend\w*|öffn\w*|schaltfläche\w*|button\w*|taste\w*|"
    r"knopf\w*|feld\w*|formular\w*|menü\w*|tabelle\w*|liste\w*|link\w*|siehe|folgen\w*|"
    r"cliqu\w*|appuy\w*|sélectionn\w*|choisi\w*|touch\w*|utilis\w*|ouvr\w*|bouton\w*|champ\w*|formulaire\w*|"
    r"menu\w*|tableau\w*|lien\w*|case|voir|voyez|consultez|"
    r"clicc\w*|prem\w*|selezion\w*|scegli\w*|tocc\w*|utilizz\w*|usate|apri\w*|pulsant\w*|tast[oi]|bottone\w*|"
    r"campo|campi|modulo|tabell\w*|elenco|vedi|vedere|consulta\w*|"
    r"click\w*|press\w*|select\w*|choose|tap\w*|use|open\w*|key|field\w*|form|table\w*|list\w*|see)\b", _F)
ASTERISK = re.compile(r"\*|\b(?:sternchen|astérisque|asterisco|asterisk)\b", _F)
QUOTED = re.compile(r"«\s*([^»]{1,80}?)\s*»|\"([^\"]{1,80})\"|„([^“”\"]{1,80})[“”\"]|“([^”]{1,80})”|‹\s*([^›]{1,80}?)\s*›")

CATEGORIES = ["visible_text", "reading_order", "text_symbol", "sensory_only", "hidden_name", "purpose_only",
              "not_instruction", "unsure"]
CATEGORY_OUTCOME = {"visible_text": "passed", "reading_order": "passed", "text_symbol": "passed",
                    "sensory_only": "failed", "hidden_name": "cantTell", "purpose_only": "cantTell",
                    "not_instruction": "inapplicable", "unsure": "cantTell"}
_LABELLED = ("button", "a", "label", "legend", "caption", "summary", "th", "h1", "h2", "h3", "h4", "h5", "h6",
             "figcaption", "option")

register({
    "c133.quoted_visible": {
        "en": "The instruction names the item by its visible text “{name}”; the sensory words are only an extra cue.",
        "de": "Die Anleitung nennt das Element mit seinem sichtbaren Text «{name}»; die Sinnesmerkmale sind nur ein Zusatz.",
        "fr": "La consigne nomme l'élément par son texte visible « {name} » ; les indications sensorielles ne sont qu'un repère en plus.",
        "it": "L'istruzione indica l'elemento con il suo testo visibile «{name}»; le caratteristiche sensoriali sono solo un aiuto in più.",
    },
    "c133.quoted_hidden": {
        "en": "The instruction names “{name}”, but that name exists only for assistive technology, not as visible text. Whether that is enough is disputed: a person must decide.",
        "de": "Die Anleitung nennt «{name}», doch diesen Namen gibt es nur für assistive Technologien, nicht als sichtbaren Text. Ob das genügt, ist umstritten: Eine Person muss entscheiden.",
        "fr": "La consigne nomme « {name} », mais ce nom n'existe que pour les technologies d'assistance, pas comme texte visible. Les avis divergent : une personne doit trancher.",
        "it": "L'istruzione nomina «{name}», ma questo nome esiste solo per le tecnologie assistive, non come testo visibile. Gli esperti non concordano: una persona deve decidere.",
    },
    "c133.asterisk": {
        "en": "The instruction refers to the asterisk, which is a visible text character in the labels.",
        "de": "Die Anleitung verweist auf das Sternchen, ein sichtbares Textzeichen in den Beschriftungen.",
        "fr": "La consigne renvoie à l'astérisque, un caractère de texte visible dans les étiquettes.",
        "it": "L'istruzione rimanda all'asterisco, un carattere di testo visibile nelle etichette.",
    },
    "c133.apertus_passed": {
        "en": "Apertus judged that the instruction also identifies the item without sensory cues ({how}).",
        "de": "Apertus beurteilt, dass die Anleitung das Element auch ohne Sinnesmerkmale bestimmt ({how}).",
        "fr": "Apertus juge que la consigne identifie aussi l'élément sans repère sensoriel ({how}).",
        "it": "Apertus giudica che l'istruzione identifichi l'elemento anche senza caratteristiche sensoriali ({how}).",
    },
    "c133.apertus_sensory_only": {
        "en": "Apertus judged that the instruction identifies the item only by shape, colour, size, position or sound (“{quote}”).",
        "de": "Apertus beurteilt, dass die Anleitung das Element nur über Form, Farbe, Grösse, Lage oder Ton bestimmt («{quote}»).",
        "fr": "Apertus juge que la consigne identifie l'élément uniquement par sa forme, sa couleur, sa taille, sa position ou un son (« {quote} »).",
        "it": "Apertus giudica che l'istruzione identifichi l'elemento solo per forma, colore, dimensione, posizione o suono («{quote}»).",
    },
    "c133.apertus_hidden_name": {
        "en": "The instruction names the item only by a name that is not visible on screen. Whether that is enough is disputed: a person must decide.",
        "de": "Die Anleitung nennt das Element nur mit einem Namen, der am Bildschirm nicht sichtbar ist. Ob das genügt, ist umstritten: Eine Person muss entscheiden.",
        "fr": "La consigne ne nomme l'élément que par un nom invisible à l'écran. Les avis divergent : une personne doit trancher.",
        "it": "L'istruzione nomina l'elemento solo con un nome non visibile sullo schermo. Gli esperti non concordano: una persona deve decidere.",
    },
    "c133.apertus_purpose_only": {
        "en": "The instruction gives the purpose of the control, which only overlaps its visible label. Whether that names it is a judgement call: a person must decide.",
        "de": "Die Anleitung nennt den Zweck des Bedienelements, der sich nur teilweise mit seiner Beschriftung deckt. Ob es damit benannt ist, muss eine Person entscheiden.",
        "fr": "La consigne indique le but du contrôle, qui ne recoupe qu'en partie son libellé visible. Une personne doit décider si cela suffit à le nommer.",
        "it": "L'istruzione indica lo scopo del comando, che coincide solo in parte con la sua etichetta visibile. Una persona deve decidere se basta a nominarlo.",
    },
    "c133.apertus_not_instruction": {
        "en": "Apertus judged that the sensory words describe the physical world or decoration, not how to use the page.",
        "de": "Apertus beurteilt, dass die Sinnesmerkmale die reale Umgebung oder Gestaltung beschreiben, nicht die Bedienung der Seite.",
        "fr": "Apertus juge que les indications sensorielles décrivent le monde physique ou la décoration, pas l'utilisation de la page.",
        "it": "Apertus giudica che le caratteristiche sensoriali descrivano il mondo fisico o la decorazione, non l'uso della pagina.",
    },
    "c133.apertus_visible_ungrounded": {
        "en": "Apertus says the instruction names the item by its visible text, but it contains none of the visible texts of the nearby controls. A person must check whether it relies on shape, colour or position only.",
        "de": "Apertus meint, die Anleitung nenne das Element über seinen sichtbaren Text, doch sie enthält keinen sichtbaren Text der Bedienelemente in der Nähe. Eine Person muss prüfen, ob sie sich nur auf Form, Farbe oder Position stützt.",
        "fr": "Apertus estime que la consigne nomme l'élément par son texte visible, mais elle ne contient aucun texte visible des commandes voisines. Une personne doit vérifier si elle repose uniquement sur la forme, la couleur ou la position.",
        "it": "Apertus ritiene che l'istruzione nomini l'elemento con il suo testo visibile, ma non contiene alcun testo visibile dei comandi vicini. Una persona deve verificare se si basa solo su forma, colore o posizione.",
    },
    "c133.apertus_unsure": {
        "en": "Apertus could not decide how this instruction identifies the item. A person must check.",
        "de": "Apertus konnte nicht entscheiden, wie diese Anleitung das Element bestimmt. Eine Person muss prüfen.",
        "fr": "Apertus n'a pas pu décider comment cette consigne identifie l'élément. Une personne doit vérifier.",
        "it": "Apertus non ha potuto decidere come questa istruzione identifichi l'elemento. Una persona deve verificare.",
    },
    "c133.how.visible_text": {"en": "by its visible text", "de": "über seinen sichtbaren Text", "fr": "par son texte visible", "it": "con il suo testo visibile"},
    "c133.how.reading_order": {"en": "by its place in the reading order", "de": "über seine Stelle in der Lesereihenfolge", "fr": "par sa place dans l'ordre de lecture", "it": "con la sua posizione nell'ordine di lettura"},
    "c133.how.text_symbol": {"en": "by a visible text character", "de": "über ein sichtbares Textzeichen", "fr": "par un caractère de texte visible", "it": "con un carattere di testo visibile"},
    "c133.impact": {
        "en": "Blind and partially sighted people cannot find the item from this instruction, because they do not perceive its shape, colour or position.",
        "de": "Blinde und sehbehinderte Menschen finden das Element mit dieser Anleitung nicht, weil sie Form, Farbe oder Lage nicht wahrnehmen.",
        "fr": "Les personnes aveugles ou malvoyantes ne trouvent pas l'élément avec cette consigne, car elles ne perçoivent pas sa forme, sa couleur ou sa position.",
        "it": "Le persone cieche o ipovedenti non trovano l'elemento con questa istruzione, perché non ne percepiscono forma, colore o posizione.",
    },
    "c133.impact_ok": {
        "en": "Everyone can follow this instruction, also without seeing or hearing the cue.",
        "de": "Alle können dieser Anleitung folgen, auch ohne das Merkmal zu sehen oder zu hören.",
        "fr": "Tout le monde peut suivre cette consigne, même sans voir ni entendre le repère.",
        "it": "Tutti possono seguire questa istruzione, anche senza vedere o sentire il segnale.",
    },
    "c133.fix_hint": {
        "en": "Add the visible name of the control or section to the instruction, for example: … the button “Name” …",
        "de": "Ergänzen Sie in der Anleitung den sichtbaren Namen des Bedienelements oder Bereichs, zum Beispiel: … die Schaltfläche «Name» …",
        "fr": "Ajoutez à la consigne le nom visible du contrôle ou de la zone, par exemple : … le bouton « Nom » …",
        "it": "Aggiungete all'istruzione il nome visibile del comando o della sezione, per esempio: … il pulsante «Nome» …",
    },
})


def _key(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").casefold()
    return " ".join(re.sub(r"[^\w*]+", " ", s).split())


def _word_index(text: str, pos: int) -> int:
    return len(re.findall(r"\w+", text[:pos]))


def sensory_hits(text: str) -> list[str]:
    """Sensory families that occur NEAR an instruction cue (≤ CUE_DISTANCE words): a shape,
    colour, size or position word far from any "click/button/field…" is not part of an
    instruction ("Kreis" as a district, a colour in a description). Sound always counts."""
    cues = [_word_index(text, m.start()) for m in CUE.finditer(text)]
    out = []
    for name, rx in (("shape", SHAPE), ("colour", COLOUR), ("position", POSITION), ("size", SIZE), ("sound", SOUND)):
        for m in rx.finditer(text):
            if name == "sound" or any(abs(_word_index(text, m.start()) - c) <= CUE_DISTANCE for c in cues):
                out.append(name)
                break
    return out


def quoted(text: str) -> list[str]:
    return [norm_text(next(g for g in m.groups() if g)) for m in QUOTED.finditer(text)]


def page_names(doc: Document) -> tuple[set[str], set[str]]:
    """(visible texts of labelled things, names that exist only non-visibly)."""
    visible: set[str] = set()
    hidden: set[str] = set()
    for n in doc.body.iter():
        if n.hidden():
            continue
        if n.tag in _LABELLED or n.role in ("button", "link", "tab", "heading"):
            v = n.text(visible=True)
            if v:
                visible.add(_key(v))
        if n.tag == "input" and n.attrs.get("type", "").lower() in ("submit", "button", "reset") and n.attrs.get("value"):
            visible.add(_key(n.attrs["value"]))
        for attr in ("aria-label", "title", "alt"):
            if n.attrs.get(attr):
                hidden.add(_key(n.attrs[attr]))
        if n.sr_only():
            hidden.add(_key(n.text()))
    return visible, hidden - visible


def find_node(doc: Document, selector: str, index: dict[str, Node] | None = None) -> Node | None:
    if selector.startswith("#") and " " not in selector:
        n = doc.by_id(selector[1:])
        if n is not None:
            return n
    if index is not None:
        if not index:
            index.update((n.css_path(), n) for n in doc.body.iter())
        return index.get(selector)
    return next((n for n in doc.body.iter() if n.css_path() == selector), None)


def control_summary(scope: Node, limit: int = MAX_CONTROLS) -> str:
    out = []
    for n in scope.iter():
        if len(out) >= limit:
            break
        if n.hidden():
            continue
        if n.tag in ("button", "a") or n.role in ("button", "link") or \
                (n.tag == "input" and n.attrs.get("type", "").lower() in ("submit", "button", "image", "reset")):
            visible = n.text(visible=True) if n.tag != "input" else (n.attrs.get("value") or "")
            kind = "link" if n.tag == "a" or n.role == "link" else "button"
            out.append(f'{kind}: visible text "{visible}", name "{n.accessible_name()}"')
    return "; ".join(out)


def control_texts(scope: Node, limit: int = MAX_CONTROLS) -> list[str]:
    """Visible texts of the controls in `scope` (the ones control_summary shows the model)."""
    out = []
    for n in scope.iter():
        if len(out) >= limit:
            break
        if n.hidden():
            continue
        if n.tag in ("button", "a") or n.role in ("button", "link") or \
                (n.tag == "input" and n.attrs.get("type", "").lower() in ("submit", "button", "image", "reset")):
            out.append(n.text(visible=True) if n.tag != "input" else (n.attrs.get("value") or ""))
    return out


def next_item(n: Node) -> str:
    sib = None
    p = n
    while p is not None and sib is None:
        parent = p.parent
        if parent is None:
            break
        kids = list(parent.elements())
        i = next((k for k, c in enumerate(kids) if c is p), -1)
        sib = kids[i + 1] if 0 <= i < len(kids) - 1 else None
        p = parent if sib is None else p
    if sib is None:
        return ""
    cap = sib.find(lambda x: x.tag in ("caption", "figcaption", "legend", "h2", "h3", "h4", "summary"))
    label = cap.text() if cap is not None else sib.text()
    return f"{sib.tag}: {label[:80]}"


class SensoryCharacteristics(BaseCheck):
    criterion = "1.3.3"
    prompt_version = PROMPT_VERSION
    max_candidates = MAX_INSTRUCTIONS

    def candidates(self, page: CapturedPage) -> list[Candidate]:
        doc = page_doc(page)
        visible, hidden = page_names(doc)
        star_labels = any("*" in v for v in visible) or any(
            "*" in n.text() for n in doc.find_all(lambda x: x.tag == "label"))
        out: list[Candidate] = []
        seen: set[str] = set()
        index: dict[str, Node] = {}  # css path → node, built on first use
        for p in self._blocks(page, doc):
            text = " ".join((p.get("text") or "").split())
            if p["selector"] in seen or not (MIN_WORDS <= word_count(text) <= MAX_WORDS):
                continue
            hits = sensory_hits(text)
            if not hits:
                continue
            seen.add(p["selector"])
            names = quoted(text)
            kind, name = "ask", ""
            for q in names:
                if _key(q) in visible:
                    kind, name = "quoted_visible", q
                    break
                if _key(q) in hidden:
                    kind, name = "quoted_hidden", q
            if kind == "ask" and ASTERISK.search(text) and star_labels:
                kind = "asterisk"
            node = find_node(doc, p["selector"], index)
            context: dict[str, str] = {}
            names_control: bool | None = None  # does the instruction contain a nearby control's visible text?
            if node is not None:
                scope = node.closest(lambda a: a.tag in ("form", "section", "article", "main", "fieldset")
                                     or a.role in ("main", "region")) or doc.body
                ctrl = control_summary(scope)
                if ctrl:
                    context["controls_nearby"] = ctrl
                # Visible texts that may name the item: nearby controls, labels, headings, captions
                # (≥ 3 characters: "DE"/"FR" language links would match almost any sentence).
                named = control_texts(scope) + [n.text(visible=True) for n in scope.iter() if not n.hidden() and n.tag in
                                                ("label", "legend", "caption", "figcaption", "h1", "h2", "h3", "h4", "h5", "h6")]
                texts = [k for k in (" ".join(_key(v).replace("*", " ").split()) for v in named) if len(k) >= 3]
                if texts:
                    names_control = any(f" {v} " in f" {_key(text)} " for v in texts)
                nxt = next_item(node)
                if nxt:
                    context["next_element"] = nxt
            out.append(self.candidate(page, selector=p["selector"], html=p.get("html", ""), text=text,
                                      lang=p.get("lang") or page.lang, context=context, kind=kind, name=name,
                                      sensory=hits, names_control=names_control))
            if len(out) >= self.max_candidates:
                break
        return out

    @staticmethod
    def _blocks(page: CapturedPage, doc: Document) -> list[dict]:
        """Extracted passages, or (no extraction) block elements of the static DOM."""
        if page.passages:
            return [p for p in page.passages if p.get("is_container", True)]
        out = []
        for n in doc.body.iter():
            if n.tag in ("p", "li", "dd", "td", "figcaption", "div") and not n.find(
                    lambda x: x.tag in ("p", "li", "div", "ul", "ol", "table")):
                out.append({"selector": n.css_path(), "html": n.outer(600), "text": n.text(),
                            "lang": (n.closest(lambda a: "lang" in a.attrs) or doc).attrs.get("lang")})
        return out

    # -- decisions (code) -------------------------------------------------------------------
    def decide(self, c: Candidate) -> Finding | None:
        ui = self.ui_lang
        kind = c.extra.get("kind")
        name = c.extra.get("name", "")
        if kind == "quoted_visible":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", excerpt=c.text[:300],
                                explanation=t("c133.quoted_visible", ui, name=name), user_impact=t("c133.impact_ok", ui))
        if kind == "quoted_hidden":
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="low", excerpt=c.text[:300],
                                explanation=t("c133.quoted_hidden", ui, name=name), user_impact=t("impact.review", ui))
        if kind == "asterisk":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", excerpt=c.text[:300],
                                explanation=t("c133.asterisk", ui), user_impact=t("c133.impact_ok", ui))
        return None

    # -- the closed (categorical) question ----------------------------------------------------
    SYSTEM = (
        "You check WCAG 2.1 success criterion 1.3.3 Sensory Characteristics for ONE instruction. Instructions for "
        "using web content must not rely only on shape, colour, size, visual position, orientation or sound. "
        "`controls_nearby` lists the controls of the same section with their visible text and their accessible "
        "name; `next_element` is what follows the instruction in reading order.\n"
        "How does the instruction identify the item it refers to?\n"
        "- visible_text: it also names the item by text that is visible on screen (label, heading, caption)\n"
        "- reading_order: it says 'below' or 'above' and means the single next or previous item in reading order "
        "(a place on the screen, such as left, right, top, bottom or a corner, is sensory_only)\n"
        "- text_symbol: the cue is a visible text character, such as an asterisk in the labels\n"
        "- sensory_only: only by shape, colour, size, position or sound, with no visible text name\n"
        "- hidden_name: by a name that exists only as an accessible name, not as visible text\n"
        "- purpose_only: only by what the control does, which merely overlaps its visible label\n"
        "- not_instruction: the words describe the physical world or decoration, not how to use the page\n"
        "- unsure: none of these\n"
        "quote: the words of the instruction that refer to the item, copied exactly."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        return self.task(
            system=self.system_prompt(self.SYSTEM, c),
            element={"instruction": c.text[:600]},
            context=c.context,
            question="How does the instruction identify the item it refers to?",
            schema=category_schema(CATEGORIES),
            max_tokens=130,
        )

    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        category = answer.get("category", "unsure")
        outcome = CATEGORY_OUTCOME.get(category, "cantTell")
        quote = (answer.get("quote") or "").strip()
        if category == "visible_text" and c.extra.get("names_control") is False:
            # Checked in code: the instruction contains none of the visible texts of the
            # controls shown to the model, so "named by its visible text" is not grounded.
            return self.finding(c, outcome="cantTell", source="apertus", confidence="low", excerpt=quote or c.text[:300],
                                explanation=t("c133.apertus_visible_ungrounded", ui), user_impact=t("impact.review", ui),
                                reason=answer.get("reason"), reason_code="apertus_visible_ungrounded")
        if outcome == "passed":
            explanation = t("c133.apertus_passed", ui, how=t(f"c133.how.{category}", ui))
            impact = t("c133.impact_ok", ui)
        elif outcome == "failed":
            explanation = t("c133.apertus_sensory_only", ui, quote=quote)
            impact = t("c133.impact", ui)
        elif outcome == "inapplicable":
            explanation, impact = t("c133.apertus_not_instruction", ui), t("impact.review", ui)
        else:
            key = f"c133.apertus_{category}" if category in ("hidden_name", "purpose_only") else "c133.apertus_unsure"
            explanation, impact = t(key, ui), t("impact.review", ui)
        return self.finding(c, outcome=outcome, source="apertus",
                            confidence=answer.get("confidence", "low") if outcome not in ("cantTell",) else "low",
                            excerpt=quote or (c.text[:300] if outcome != "failed" else ""),
                            explanation=explanation, user_impact=impact, reason=answer.get("reason"),
                            reason_code=f"apertus_{category}" if category in CATEGORY_OUTCOME else "apertus_unsure",
                            fix_hint=t("c133.fix_hint", ui) if outcome == "failed" else None)


CHECK = SensoryCharacteristics
