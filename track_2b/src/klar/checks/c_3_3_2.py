"""3.3.2 Labels or Instructions, level A. No ACT rule. Techniques G131, H44, H71, H90,
G89, G184, G167; failure F82.

What counts is what a sighted user SEES before typing (capture/js/c_3_3_2_labels.js):
visible <label> or aria-labelledby text (visually hidden text, aria-label, title and a
placeholder that disappears do not count), the fieldset legend, visible
aria-describedby hints, other visible text in the field's own wrapper, required
markers, the `pattern` attribute, and per form the instructions outside the labels.
Radio buttons of one name are judged as one group.

Decided in code (one finding per control, the first problem wins)
  * label is only a pictogram                                        → cantTell (Understanding: images
                                                                        only if widely understood)
  * no visible label, but the visible button right after it is a search button ("Suchen",
    "Rechercher", "Cerca", "Search")                                  → passed (G167)
  * search field without a visible label next to an icon-only button  → cantTell (icon clear enough?)
  * no visible label, only a placeholder                              → failed (G131 not met)
  * no visible label and no visible text next to the field            → failed
  * part of a group with a visible legend, own label visually hidden  → passed (low)
  * `pattern` field (PROTOCOL F3: only a "specific, non-obvious" format fails), no visible hint:
    - literal separators between groups (dots, dashes, slashes) or letters mixed with digits
                                                                      → failed (G89 not used)
    - a plain digit count ([0-9]{n} or its shorthand) on a well-known number (postal code, year, PIN,
      one-time code, house number; from the label words or the autocomplete token)
                                                                      → passed (format obvious)
    - an e-mail or web address ("@" or "://" in the pattern, email/url token)
                                                                      → passed (format known)
    - anything else                                                   → Apertus (below)
  * required field without "*" or a required word, in a form where other labels use "*" or
    other fields are optional, and no form instruction mentions required fields
                                                                      → failed (H90/G83 not used)
  * single-field form, or a form instruction that mentions required fields → no marker needed
  * native type="date" without a hint                                 → passed (browser shows the format)
  * telephone field (type=tel, a tel token, or a text field whose label names a phone)
    without hint or pattern in a form that posts to a server
                                                                      → cantTell (format unknown)
  * radio group with a visible legend / group label                   → passed (H71)
  * radio group with neither a group label nor text before it         → failed (H71 not used)
  * radio group with only text before it (no legend)                  → cantTell
  * otherwise                                                         → passed (G131)
Asked to Apertus (one categorical question) for a `pattern` field that has visible hint text,
or whose pattern is neither separated nor an obvious digit count:
  "Does the user know the required format before typing?"
    states_format | obvious_from_label | needs_instruction | unsure
  mapped in code: states_format, obvious_from_label → passed; needs_instruction → failed
  (G89 not used); unsure → cantTell.

Known limits: a label that is present but ambiguous on the page (protocol class C2) is not
detected; formats enforced only by script are not seen; visible text next to a field without
<label> is accepted as its label.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema, norm_ws
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "3.3.2/v2"
JS_PATH = Path(__file__).resolve().parents[1] / "capture" / "js" / "c_3_3_2_labels.js"
MAX_QUESTIONS = 8
# Word stems that mark a required field (DE · FR · IT · EN).
REQUIRED_STEMS = ("pflicht", "erforderlich", "obligatoir", "requis", "obbligatori", "richiest", "required",
                  "mandatory")
_WORD = re.compile(r"\w+", re.UNICODE)
CATEGORIES = ["states_format", "obvious_from_label", "needs_instruction", "unsure"]
CATEGORY_OUTCOME = {"states_format": "passed", "obvious_from_label": "passed", "needs_instruction": "failed"}
# Well-known numbers whose digit count users know (single words, DE · FR · IT · EN). Compound
# words ending in a year word ("…jahr") count too.
KNOWN_NUMBER_WORDS = frozenset({"plz", "postleitzahl", "npa", "postcode", "zip", "jahr", "jahrgang", "année",
                                "annee", "anno", "year", "pin", "hausnummer", "hausnr", "civico"})
KNOWN_NUMBER_AUTOCOMPLETE = frozenset({"postal-code", "bday-year", "cc-exp-year", "one-time-code", "cc-csc"})
_DIGIT_COUNT = re.compile(r"^\^?(?:\\d|\[0-9\])\{\d+(?:,\d*)?\}\$?$")


def separated_pattern(pattern: str) -> bool:
    """Literal separators between groups (an escaped dot, a dash, slash, colon or space outside
    character classes) or letters mixed with digits: a specific format users must be told."""
    outside = re.sub(r"\[[^\]]*\]", "C", pattern or "")
    outside = re.sub(r"\\[dDwWsS]", "C", outside)
    sep = bool(re.search(r"\\[.\-/: ]|[-/: ]", outside))
    # a letter group and a separate digit group ("two letters then digits"); one class that
    # accepts both (a free alphanumeric code) is not a fixed layout and goes to Apertus
    classes = re.findall(r"\[([^\]]*)\]", pattern or "")
    letters = "\\p{L" in (pattern or "") or any(re.search(r"[A-Za-z]-[A-Za-z]", c) and "0-9" not in c for c in classes)
    digits = "\\d" in (pattern or "") or any("0-9" in c and not re.search(r"[A-Za-z]-[A-Za-z]", c) for c in classes)
    return sep or (letters and digits)


def address_pattern(pattern: str, autocomplete: str) -> bool:
    """An e-mail or web address: a format users know (the pattern has "@" or "://", or the
    field's token is email/url)."""
    tokens = set((autocomplete or "").lower().split())
    return "@" in (pattern or "") or "://" in (pattern or "") or bool(tokens & {"email", "url"})


# Stems of label words that name a telephone number (DE · FR · IT · EN; "natel" is Swiss usage).
PHONE_STEMS = ("telefon", "téléphone", "telephone", "phone", "natel")


# G167: words of a button that labels the field before it (search). DE · FR · IT · EN.
SEARCH_STEMS = ("such", "recherch", "cherch", "cerca", "ricerc", "search", "find", "trouv", "trova")


def search_button(text: str) -> bool:
    ws = _WORD.findall(unicodedata.normalize("NFKC", text or "").casefold())
    return any(w.startswith(SEARCH_STEMS) for w in ws)


def phone_label(label: str) -> bool:
    ws = _WORD.findall(unicodedata.normalize("NFKC", label or "").casefold())
    return any(w.startswith(PHONE_STEMS) or w == "tel" for w in ws)


def obvious_number(pattern: str, label: str, autocomplete: str) -> bool:
    """A plain digit count on a field whose label or token names a well-known number."""
    if not _DIGIT_COUNT.match((pattern or "").strip()):
        return False
    if set((autocomplete or "").lower().split()) & KNOWN_NUMBER_AUTOCOMPLETE:
        return True
    ws = set(_WORD.findall(unicodedata.normalize("NFKC", label or "").casefold()))
    if ws & KNOWN_NUMBER_WORDS or any(w.endswith("jahr") for w in ws):
        return True
    # two-word names of the postal code / house number without listing phrases
    return bool(ws & {"code", "codice"} and ws & {"postal", "postale"}) or bool({"house", "number"} <= ws)


@lru_cache(maxsize=1)
def labels_js() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def mentions_required(text: str) -> bool:
    ws = _WORD.findall(unicodedata.normalize("NFKC", text or "").casefold())
    return any(w.startswith(REQUIRED_STEMS) for w in ws)


def marks_required(*texts: str) -> bool:
    return any("*" in (x or "") or mentions_required(x) for x in texts)


register({
    "c332.ok": {
        "en": "The field has the visible label “{label}”.",
        "de": "Das Feld hat die sichtbare Beschriftung «{label}».",
        "fr": "Le champ a l'étiquette visible « {label} ».",
        "it": "Il campo ha l'etichetta visibile «{label}».",
    },
    "c332.adjacent_button": {
        "en": "The field has no label of its own, but the visible button “{button}” right after it says what it is for (G167).",
        "de": "Das Feld hat keine eigene Beschriftung, aber die sichtbare Schaltfläche «{button}» direkt danach sagt, wofür es dient (G167).",
        "fr": "Le champ n'a pas d'étiquette propre, mais le bouton visible « {button} » juste après indique à quoi il sert (G167).",
        "it": "Il campo non ha un'etichetta propria, ma il pulsante visibile «{button}» subito dopo dice a cosa serve (G167).",
    },
    "c332.adjacent_icon": {
        "en": "A search field without a visible label, next to a button that shows only an icon. Whether the icon makes the purpose clear enough must be decided by a person.",
        "de": "Ein Suchfeld ohne sichtbare Beschriftung neben einer Schaltfläche, die nur ein Symbol zeigt. Ob das Symbol den Zweck klar genug macht, muss eine Person entscheiden.",
        "fr": "Un champ de recherche sans étiquette visible, à côté d'un bouton qui n'affiche qu'une icône. Une personne doit décider si l'icône rend le but assez clair.",
        "it": "Un campo di ricerca senza etichetta visibile, accanto a un pulsante che mostra solo un'icona. Una persona deve decidere se l'icona rende lo scopo abbastanza chiaro.",
    },
    "c332.placeholder_only": {
        "en": "The only visible cue is the placeholder “{placeholder}”, which disappears as soon as the user types.",
        "de": "Der einzige sichtbare Hinweis ist der Platzhalter «{placeholder}», der beim Tippen verschwindet.",
        "fr": "Le seul repère visible est le placeholder « {placeholder} », qui disparaît dès la saisie.",
        "it": "L'unico indizio visibile è il segnaposto «{placeholder}», che scompare appena si scrive.",
    },
    "c332.no_label": {
        "en": "This field has no visible label: sighted users cannot tell what to enter.",
        "de": "Dieses Feld hat keine sichtbare Beschriftung: Sehende wissen nicht, was einzugeben ist.",
        "fr": "Ce champ n'a pas d'étiquette visible : les personnes voyantes ne savent pas quoi saisir.",
        "it": "Questo campo non ha un'etichetta visibile: chi vede non sa cosa inserire.",
    },
    "c332.nearby_text": {
        "en": "The field has no label element, but the visible text “{label}” next to it says what to enter.",
        "de": "Das Feld hat kein Label-Element, aber der sichtbare Text «{label}» daneben sagt, was einzugeben ist.",
        "fr": "Le champ n'a pas d'élément label, mais le texte visible « {label} » à côté indique quoi saisir.",
        "it": "Il campo non ha un elemento label, ma il testo visibile «{label}» accanto dice cosa inserire.",
    },
    "c332.group_legend": {
        "en": "The field belongs to the group “{label}”, whose visible legend labels it.",
        "de": "Das Feld gehört zur Gruppe «{label}», deren sichtbare Legende es beschriftet.",
        "fr": "Le champ fait partie du groupe « {label} », dont la légende visible l'étiquette.",
        "it": "Il campo fa parte del gruppo «{label}», la cui legenda visibile lo etichetta.",
    },
    "c332.pictogram": {
        "en": "The visible label is only a pictogram. It works only if it is widely known: a person must decide.",
        "de": "Die sichtbare Beschriftung ist nur ein Piktogramm. Das genügt nur, wenn es allgemein bekannt ist: Eine Person muss entscheiden.",
        "fr": "L'étiquette visible n'est qu'un pictogramme. Cela ne suffit que s'il est largement connu : une personne doit trancher.",
        "it": "L'etichetta visibile è solo un pittogramma. Funziona solo se è ampiamente noto: una persona deve decidere.",
    },
    "c332.required_unmarked": {
        "en": "“{label}” is required, but nothing shows it (no asterisk or word), although other fields are marked as required or optional.",
        "de": "«{label}» ist ein Pflichtfeld, aber nichts zeigt das an (kein Sternchen, kein Hinweis), obwohl andere Felder als Pflichtfeld oder freiwillig gekennzeichnet sind.",
        "fr": "« {label} » est obligatoire, mais rien ne l'indique (ni astérisque ni mention), alors que d'autres champs sont signalés comme obligatoires ou facultatifs.",
        "it": "«{label}» è obbligatorio, ma nulla lo indica (né asterisco né dicitura), sebbene altri campi siano segnalati come obbligatori o facoltativi.",
    },
    "c332.required_all_unmarked": {
        "en": "All fields of this form are required and nothing says so. A person must decide whether users can tell.",
        "de": "Alle Felder dieses Formulars sind Pflichtfelder, und nichts weist darauf hin. Eine Person muss entscheiden, ob das erkennbar ist.",
        "fr": "Tous les champs de ce formulaire sont obligatoires et rien ne le dit. Une personne doit décider si c'est compréhensible.",
        "it": "Tutti i campi di questo modulo sono obbligatori e nulla lo dice. Una persona deve decidere se è comprensibile.",
    },
    "c332.format_missing": {
        "en": "“{label}” only accepts a specific format (pattern {pattern}), but no visible text states it.",
        "de": "«{label}» akzeptiert nur ein bestimmtes Format (Muster {pattern}), aber kein sichtbarer Text nennt es.",
        "fr": "« {label} » n'accepte qu'un format précis (motif {pattern}), mais aucun texte visible ne l'indique.",
        "it": "«{label}» accetta solo un formato preciso (pattern {pattern}), ma nessun testo visibile lo indica.",
    },
    "c332.format_address": {
        "en": "“{label}” asks for an e-mail or web address, a format users know; no instruction is needed.",
        "de": "«{label}» fragt nach einer E-Mail- oder Webadresse, einem bekannten Format; eine Anleitung ist nicht nötig.",
        "fr": "« {label} » demande une adresse e-mail ou web, un format connu ; aucune instruction n'est nécessaire.",
        "it": "«{label}» chiede un indirizzo e-mail o web, un formato noto; non servono istruzioni.",
    },
    "c332.format_obvious": {
        "en": "“{label}” only accepts a fixed number of digits ({pattern}); for this well-known number the format needs no instruction.",
        "de": "«{label}» akzeptiert nur eine feste Anzahl Ziffern ({pattern}); bei dieser bekannten Nummer braucht das Format keine Anleitung.",
        "fr": "« {label} » n'accepte qu'un nombre fixe de chiffres ({pattern}) ; pour ce numéro connu, le format n'a pas besoin d'instruction.",
        "it": "«{label}» accetta solo un numero fisso di cifre ({pattern}); per questo numero noto il formato non richiede istruzioni.",
    },
    "c332.apertus_obvious_from_label": {
        "en": "Apertus judged that users know the format of “{label}” from its label alone.",
        "de": "Apertus beurteilt, dass Nutzende das Format von «{label}» schon aus der Beschriftung kennen.",
        "fr": "Apertus juge que les utilisateurs connaissent le format de « {label} » par son étiquette.",
        "it": "Apertus giudica che gli utenti conoscano il formato di «{label}» già dall'etichetta.",
    },
    "c332.apertus_needs_instruction": {
        "en": "Apertus judged that “{label}” requires a specific format (pattern {pattern}) that users cannot guess and no visible text states.",
        "de": "Apertus beurteilt, dass «{label}» ein bestimmtes Format verlangt (Muster {pattern}), das man nicht erraten kann und das kein sichtbarer Text nennt.",
        "fr": "Apertus juge que « {label} » exige un format précis (motif {pattern}) que l'on ne peut pas deviner et qu'aucun texte visible n'indique.",
        "it": "Apertus giudica che «{label}» richieda un formato preciso (pattern {pattern}) che non si può indovinare e che nessun testo visibile indica.",
    },
    "c332.date_native": {
        "en": "A native date field: the browser shows its own date format and picker.",
        "de": "Ein natives Datumsfeld: Der Browser zeigt sein eigenes Datumsformat und eine Datumsauswahl.",
        "fr": "Un champ de date natif : le navigateur affiche son propre format et un sélecteur.",
        "it": "Un campo data nativo: il browser mostra il proprio formato e un selettore.",
    },
    "c332.tel_unknown": {
        "en": "A telephone field without a format hint; the form is checked on the server, so whether a format is required cannot be seen. A person must decide.",
        "de": "Ein Telefonfeld ohne Formathinweis; das Formular wird auf dem Server geprüft, daher ist nicht erkennbar, ob ein Format verlangt ist. Eine Person muss entscheiden.",
        "fr": "Un champ téléphone sans indication de format ; le formulaire est vérifié sur le serveur, on ne voit pas si un format est exigé. Une personne doit trancher.",
        "it": "Un campo telefono senza indicazione di formato; il modulo è verificato sul server, quindi non si vede se serve un formato. Una persona deve decidere.",
    },
    "c332.group_ok": {
        "en": "The options are grouped under the visible question “{label}”.",
        "de": "Die Optionen sind unter der sichtbaren Frage «{label}» gruppiert.",
        "fr": "Les options sont regroupées sous la question visible « {label} ».",
        "it": "Le opzioni sono raggruppate sotto la domanda visibile «{label}».",
    },
    "c332.group_no_question": {
        "en": "The options {options} have no visible question: users cannot tell what they answer.",
        "de": "Die Optionen {options} haben keine sichtbare Frage: Man weiss nicht, worauf sie antworten.",
        "fr": "Les options {options} n'ont pas de question visible : on ne sait pas à quoi elles répondent.",
        "it": "Le opzioni {options} non hanno una domanda visibile: non si sa a cosa rispondono.",
    },
    "c332.group_text_before": {
        "en": "The options {options} have no legend, only the text “{label}” before them. A person must check that it states the question.",
        "de": "Die Optionen {options} haben keine Legende, nur den Text «{label}» davor. Eine Person muss prüfen, ob er die Frage stellt.",
        "fr": "Les options {options} n'ont pas de légende, seulement le texte « {label} » avant elles. Une personne doit vérifier qu'il pose la question.",
        "it": "Le opzioni {options} non hanno una legenda, solo il testo «{label}» prima. Una persona deve verificare che ponga la domanda.",
    },
    "c332.apertus_states_format": {
        "en": "Apertus judged that the visible text of “{label}” states the required format.",
        "de": "Apertus beurteilt, dass der sichtbare Text zu «{label}» das verlangte Format nennt.",
        "fr": "Apertus juge que le texte visible de « {label} » indique le format exigé.",
        "it": "Apertus giudica che il testo visibile di «{label}» indichi il formato richiesto.",
    },
    "c332.apertus_unsure": {
        "en": "Apertus could not decide whether the format of “{label}” is explained. A person must check it.",
        "de": "Apertus konnte nicht entscheiden, ob das Format von «{label}» erklärt wird. Eine Person muss es prüfen.",
        "fr": "Apertus n'a pas pu décider si le format de « {label} » est expliqué. Une personne doit vérifier.",
        "it": "Apertus non ha potuto decidere se il formato di «{label}» sia spiegato. Una persona deve verificare.",
    },
    "c332.impact": {
        "en": "Users, especially those with cognitive disabilities or low vision, do not know what to enter or in which format, and make avoidable errors.",
        "de": "Nutzende, besonders solche mit kognitiven Einschränkungen oder Sehbehinderung, wissen nicht, was oder in welchem Format sie eingeben sollen, und machen vermeidbare Fehler.",
        "fr": "Les utilisateurs, surtout ceux ayant un handicap cognitif ou une basse vision, ne savent pas quoi saisir ni sous quel format, et font des erreurs évitables.",
        "it": "Gli utenti, soprattutto quelli con disabilità cognitive o ipovisione, non sanno cosa inserire né in che formato, e commettono errori evitabili.",
    },
    "c332.impact_ok": {
        "en": "Users can see what to enter before they start typing.",
        "de": "Nutzende sehen vor dem Tippen, was einzugeben ist.",
        "fr": "Les utilisateurs voient quoi saisir avant de commencer.",
        "it": "Gli utenti vedono cosa inserire prima di iniziare a scrivere.",
    },
})


class LabelsOrInstructions(BaseCheck):
    criterion = "3.3.2"
    prompt_version = PROMPT_VERSION
    max_candidates = 120

    def candidates(self, page: CapturedPage) -> list[Candidate]:
        data = self._collect(page)
        forms = {f["selector"]: f for f in data.get("forms", [])}
        by_form: dict[str | None, list[dict]] = {}
        for f in data.get("fields", []):
            by_form.setdefault(f.get("form"), []).append(f)
        out: list[Candidate] = []
        asked = 0
        for f in data.get("fields", []):
            kind, extra = self._classify(f, forms.get(f.get("form") or ""), by_form.get(f.get("form"), []))
            if kind == "ask_format":
                if asked >= MAX_QUESTIONS:
                    kind = "format_unasked"
                asked += 1
            label = f.get("visible_label") or f.get("legend") or ""
            text = norm_ws(" ".join(x for x in (f.get("visible_label"), f.get("hint"), f.get("wrapper_text"),
                                                f.get("placeholder")) if x))
            out.append(self.candidate(page, selector=f["selector"], html=f.get("html", ""), text=text,
                                      accessible_name=label or None, lang=f.get("lang"), kind=kind,
                                      label=label, pattern=f.get("pattern") or "", placeholder=f.get("placeholder") or "",
                                      **extra))
        for g in data.get("groups", []):
            options = ", ".join(f"“{o}”" for o in (g.get("options") or [])[:4])
            if g.get("group_label"):
                kind, label = "group_ok", g["group_label"]
            elif g.get("prev_text") and g["prev_text"].rstrip().endswith(("?", ":")):
                kind, label = "group_ok", g["prev_text"]
            elif g.get("prev_text"):
                kind, label = "group_text_before", g["prev_text"]
            else:
                kind, label = "group_no_question", ""
            out.append(self.candidate(page, selector=g["selector"], html=g.get("html", ""), text=label,
                                      accessible_name=label or None, lang=g.get("lang"), kind=kind, label=label,
                                      options=options, key="#group"))
        return out[: self.max_candidates]

    @staticmethod
    def _collect(page: CapturedPage) -> dict:
        if page.live is not None:
            try:
                return page.evaluate(labels_js(), 200) or {}
            except Exception:
                pass
        # Static fallback: the shared extractor's field records (labels are not checked for visibility).
        return {"fields": [{"selector": f["selector"], "tag": f.get("tag"), "type": (f.get("type") or "").lower(),
                            "required": f.get("required"), "pattern": None, "placeholder": f.get("placeholder") or "",
                            "visible_label": " ".join(f.get("labels") or []), "hidden_label": "",
                            "legend": f.get("legend") or "", "hint": f.get("describedby") or "", "wrapper_text": "",
                            "form": f.get("form"), "html": f.get("html", ""), "lang": f.get("lang"),
                            "autocomplete": f.get("autocomplete") or ""}
                           for f in page.fields if (f.get("type") or "").lower() != "radio"],
                "groups": [], "forms": []}

    @staticmethod
    def _classify(f: dict, form: dict | None, siblings: list[dict]) -> tuple[str, dict]:
        label = f.get("visible_label") or ""
        ftype = (f.get("type") or "").lower()
        if not label:
            if f.get("label_image_only"):
                return "pictogram", {}
            if f.get("legend") and (f.get("hidden_label") or f.get("aria_label")):
                return "group_legend", {}
            if f.get("wrapper_text") and not f.get("placeholder"):
                return "nearby_text", {"nearby": f["wrapper_text"]}
            btn = f.get("adjacent_button") or {}
            if search_button(btn.get("text", "")):
                return "adjacent_button", {"button": btn["text"]}  # G167
            if f.get("search_like") and btn.get("icon"):
                return "adjacent_icon", {}
            if f.get("placeholder"):
                return "placeholder_only", {}
            return "no_label", {}
        pattern = f.get("pattern")
        hint = norm_ws(" ".join(x for x in (f.get("hint"), f.get("wrapper_text"), f.get("placeholder")) if x))
        if pattern and ftype not in ("date", "email", "number", "url"):
            if address_pattern(pattern, f.get("autocomplete", "")):
                return "format_address", {}
            if hint or re.search(r"[\d(]", label):
                return "ask_format", {"hint": hint}
            if separated_pattern(pattern):
                return "format_missing", {}
            if obvious_number(pattern, label, f.get("autocomplete", "")):
                return "format_obvious", {}
            return "ask_format", {"hint": ""}
        if f.get("required") and not marks_required(label, f.get("hint", ""), f.get("wrapper_text", "")):
            units = (form or {}).get("units", len(siblings))
            if units > 1:
                if (form or {}).get("star_labels"):
                    return "required_unmarked", {}
                if not mentions_required((form or {}).get("instructions", "")):
                    if any(not s.get("required") for s in siblings if s is not f):
                        return "required_unmarked", {}
                    return "required_all_unmarked", {}
        if ftype == "date":
            return "date_native", {}
        phone = ftype == "tel" or f.get("autocomplete", "").endswith("tel") or (
            ftype in ("", "text") and phone_label(label))
        if phone and not hint and not pattern and (form or {}).get("action"):
            return "tel_unknown", {}
        return "ok", {}

    def decide(self, c: Candidate) -> Finding | None:
        kind, ui = c.extra.get("kind"), self.ui_lang
        label = (c.extra.get("label") or "")[:120]
        kw = {"label": label, "placeholder": c.extra.get("placeholder", "")[:80], "pattern": c.extra.get("pattern", ""),
              "options": c.extra.get("options", "")}
        ok = lambda key, conf="medium": self.finding(  # noqa: E731
            c, outcome="passed", source="heuristic", confidence=conf, explanation=t(key, ui, **kw),
            user_impact=t("c332.impact_ok", ui))
        bad = lambda key, conf="high": self.finding(  # noqa: E731
            c, outcome="failed", source="heuristic", confidence=conf, explanation=t(key, ui, **kw),
            user_impact=t("c332.impact", ui))
        review = lambda key: self.finding(  # noqa: E731
            c, outcome="cantTell", source="heuristic", confidence="low", explanation=t(key, ui, **kw),
            user_impact=t("impact.review", ui))
        if kind == "ok":
            return ok("c332.ok")
        if kind == "nearby_text":
            kw["label"] = c.extra.get("nearby", "")[:120]
            return ok("c332.nearby_text", "low")
        if kind == "group_legend":
            return ok("c332.group_legend", "low")
        if kind == "date_native":
            return ok("c332.date_native")
        if kind == "format_obvious":
            return ok("c332.format_obvious")
        if kind == "format_address":
            return ok("c332.format_address")
        if kind == "group_ok":
            return ok("c332.group_ok")
        if kind == "adjacent_button":
            kw["button"] = c.extra.get("button", "")[:80]
            return ok("c332.adjacent_button", "low")
        if kind == "adjacent_icon":
            return review("c332.adjacent_icon")
        if kind == "placeholder_only":
            return bad("c332.placeholder_only")
        if kind == "no_label":
            return bad("c332.no_label")
        if kind == "required_unmarked":
            return bad("c332.required_unmarked", "medium")
        if kind == "format_missing":
            return bad("c332.format_missing", "medium")
        if kind == "group_no_question":
            return bad("c332.group_no_question", "medium")
        if kind == "pictogram":
            return review("c332.pictogram")
        if kind == "required_all_unmarked":
            return review("c332.required_all_unmarked")
        if kind == "tel_unknown":
            return review("c332.tel_unknown")
        if kind == "group_text_before":
            return review("c332.group_text_before")
        if kind == "format_unasked":
            return review("c332.apertus_unsure")
        return None

    SYSTEM = (
        "You check WCAG 2.1 success criterion 3.3.2 Labels or Instructions for ONE form field. The field only "
        "accepts input that matches the given HTML pattern (a regular expression). Instructions are needed only "
        "for a specific format that users cannot guess. Read the visible label and hints and classify:\n"
        "- states_format: the visible text tells the user the required format, length or characters, or gives "
        "a matching example\n"
        "- obvious_from_label: no text states it, but the label names an item whose format users already know\n"
        "- needs_instruction: the format is specific, users cannot guess it, and no visible text states it\n"
        "- unsure: cannot tell\n"
        "quote: the words that decide, copied exactly (the label if nothing else)."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        element = {"label": c.extra.get("label", ""), "visible_hints": c.extra.get("hint", ""),
                   "pattern": c.extra.get("pattern", "")}
        return self.task(system=self.system_prompt(self.SYSTEM, c), element=element, context={},
                         question="Does the user know the required format before typing?",
                         schema=category_schema(CATEGORIES), max_tokens=100)

    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        category = answer.get("category")
        outcome = CATEGORY_OUTCOME.get(category, "cantTell")
        key = f"c332.apertus_{category}" if category in CATEGORY_OUTCOME else "c332.apertus_unsure"
        kw = {"label": (c.extra.get("label") or "")[:120], "pattern": c.extra.get("pattern", "")}
        impact = {"passed": t("c332.impact_ok", ui), "failed": t("c332.impact", ui)}.get(outcome, t("impact.review", ui))
        return self.finding(c, outcome=outcome, source="apertus",
                            confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
                            excerpt=self.model_excerpt(c, answer, outcome), explanation=t(key, ui, **kw),
                            user_impact=impact, reason=answer.get("reason"),
                            reason_code=f"apertus_{category}" if category in CATEGORIES else "apertus_unsure")


CHECK = LabelsOrInstructions
