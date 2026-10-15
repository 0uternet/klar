"""1.3.5 Identify Input Purpose, level AA. ACT rule 73f2c2 (autocomplete attribute has a
valid value). Technique H98, failure F107.

The SC applies only to fields that collect information ABOUT THE USER for one of the
53 input purposes of WCAG 2.1 §7. Token syntax is a fact; whose data a field collects
is a judgement.

Decided in code
  * autocomplete value with an unknown or misplaced token (HTML autofill grammar:
    section-*, shipping|billing, home|work|mobile|fax|pager, field name, webauthn)
                                                                    → failed (rule, 73f2c2, F107)
  * valid field-name token whose purpose the visible label does not contradict
                                                                    → passed (H98)
  * password field without autocomplete whose label names a password, in a login or sign-up
    form (a user-name field, two password fields, or login/account wording in the form, the
    account noun only in an account phrase; an e-mail field alone is not a login signal):
    purposes current/new-password                                    → failed
    (any other password-type field, e.g. an access code or a shared network key, goes to Apertus)
  * search fields, buttons, checkboxes, radios, files, hidden fields → not candidates
  * number field (type="number") whose label names no birth date, card, postcode or phone
    (a quantity: "Anzahl Exemplare")                              → inapplicable (heuristic)
Asked to Apertus (one categorical question per field without a purpose token, or with
"off"/"on", or whose label contradicts its name-part token)
  "Whose data does this field collect?"
    user_own | other_person | either | not_listed
  with the label, the fieldset legend, the closest heading and the text before the form.
  Mapped in code (data/testset/PROTOCOL.md §1.3.5): user_own → failed (F1, or F3 for "off"),
  other_person → passed (scope: data about the user only), either → cantTell (the page lets the
  user fill it for someone else), not_listed → passed (purpose not in §7).
  For a contradicted token the same question is not used: the model picks the purpose family
  (given_name | family_name | full_name | other) and code compares it with the token.

Known limits: the token is not checked against the input type in every combination; a field
whose label is only a placeholder or an image is judged on that text only; at most 12 questions
per page.
"""

from __future__ import annotations

import re
import unicodedata

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema, norm_ws, set_attr, unified_diff
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "1.3.5/v1"
MAX_QUESTIONS = 12

# HTML Living Standard, autofill field names (WCAG 2.1 §7 lists the user-related subset).
FIELD_NAMES = frozenset("""
name honorific-prefix given-name additional-name family-name honorific-suffix nickname username new-password
current-password one-time-code organization-title organization street-address address-line1 address-line2
address-line3 address-level4 address-level3 address-level2 address-level1 country country-name postal-code
cc-name cc-given-name cc-additional-name cc-family-name cc-number cc-exp cc-exp-month cc-exp-year cc-csc cc-type
transaction-currency transaction-amount language bday bday-day bday-month bday-year sex url photo
""".split())
CONTACT_NAMES = frozenset("""
tel tel-country-code tel-national tel-area-code tel-local tel-local-prefix tel-local-suffix tel-extension email impp
""".split())
CONTACT_KINDS = frozenset({"home", "work", "mobile", "fax", "pager"})
ADDRESS_KINDS = frozenset({"shipping", "billing"})
SKIP_TYPES = frozenset({"hidden", "submit", "button", "reset", "image", "checkbox", "radio", "file", "range",
                        "color", "search"})
NAME_PARTS = {"given-name": "given_name", "family-name": "family_name", "name": "full_name",
              "additional-name": "other"}
# Single words of visible labels that name ONE part of a person's name (DE · FR · IT · EN).
GIVEN_WORDS = frozenset({"vorname", "prénom", "prenom", "first", "given", "forename"})
FAMILY_WORDS = frozenset({"nachname", "familienname", "cognome", "surname", "last", "family"})

_WORD = re.compile(r"\w+", re.UNICODE)


def parse_autocomplete(value: str) -> tuple[bool, str | None]:
    """(valid, field name) for an autocomplete attribute value (HTML autofill grammar)."""
    tokens = [x.lower() for x in (value or "").split()]
    if not tokens:
        return True, None  # empty value: no purpose (treated like a missing attribute)
    if tokens in (["on"], ["off"]):
        return True, tokens[0]
    if tokens[-1] == "webauthn":
        tokens = tokens[:-1]
        if not tokens:
            return False, None
    if tokens and tokens[0].startswith("section-") and len(tokens[0]) > 8:
        tokens = tokens[1:]
    if tokens and tokens[0] in ADDRESS_KINDS:
        tokens = tokens[1:]
    if len(tokens) == 2 and tokens[0] in CONTACT_KINDS and tokens[1] in CONTACT_NAMES:
        return True, tokens[1]
    if len(tokens) == 1 and (tokens[0] in FIELD_NAMES or tokens[0] in CONTACT_NAMES):
        return True, tokens[0]
    return False, None


_USERNAME_NAME = re.compile(r"user|login|benutzer|utilisateur|utente", re.IGNORECASE)
# Words of a visible label that name a password (DE · FR · IT · EN). French and Italian use two
# words; they are matched as pairs in code (password_label) rather than listed as phrases.
PASSWORD_STEMS = ("passwort", "kennwort", "password", "passwd")
# Stems of words that on their own make a form a login or account sign-up (DE · FR · IT · EN).
ACCOUNT_STEMS = ("login", "logon", "einlogg", "registrier", "kundenkonto", "benutzerkonto", "accedi", "registra",
                 "signin", "signup")
# The plain nouns for "account" are everyday words too ("tenir compte de", "take into account",
# "compte rendu", a bank "Konto"): they count only as an account phrase, i.e. after a possessive,
# an article or "new", or before a verb that creates the account.
ACCOUNT_NOUN_BEFORE = {
    "compte": frozenset({"mon", "votre", "ton", "un", "nouveau"}),
    "account": frozenset({"my", "your", "an", "new", "un", "tuo", "mio", "suo", "nuovo"}),
    "konto": frozenset({"mein", "ihr", "dein", "neues"}),
}
ACCOUNT_NOUN_AFTER = {"konto": frozenset({"erstellen", "anlegen", "eröffnen"})}
ACCOUNT_NOUN_NOT_AFTER = {"compte": frozenset({"rendu", "rendus"})}


def _words(text: str) -> list[str]:
    return _WORD.findall(unicodedata.normalize("NFKC", text or "").casefold())


def password_label(label: str) -> bool:
    """The visible label names a password (not a code, PIN, access key or voucher)."""
    ws = _words(label)
    if any(w.startswith(PASSWORD_STEMS) for w in ws):
        return True
    return ("mot" in ws and "passe" in ws) or ("parola" in ws and "ordine" in ws)


def is_username_field(f: dict) -> bool:
    """A user-name field (token or field name/id). An e-mail field alone is NOT a login signal:
    almost every form has one."""
    tokens = set((f.get("autocomplete") or "").lower().split())
    return "username" in tokens or bool(_USERNAME_NAME.search(f"{f.get('field_name') or ''} {f.get('id') or ''}"))


def account_wording(text: str) -> bool:
    """Login or account wording: a login/registration stem, or an account noun used as an
    account phrase ("create an account", "your account", "Konto erstellen"), not in an idiom."""
    ws = _words(text)
    if any(w.startswith(ACCOUNT_STEMS) for w in ws):
        return True
    for i, w in enumerate(ws):
        if w in ("log", "sign") and i + 1 < len(ws) and ws[i + 1] in ("in", "on", "up"):
            return True  # "log in", "sign up" written as two words
        if w not in ACCOUNT_NOUN_BEFORE:
            continue
        before = ws[i - 1] if i else ""
        after = ws[i + 1] if i + 1 < len(ws) else ""
        if after in ACCOUNT_NOUN_NOT_AFTER.get(w, ()):
            continue
        if before in ACCOUNT_NOUN_BEFORE[w] or after in ACCOUNT_NOUN_AFTER.get(w, ()):
            return True
    return False


def _html_text(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html or "")


def label_words(label: str) -> set[str]:
    return set(_WORD.findall(unicodedata.normalize("NFKC", label or "").casefold()))


def contradicts(token: str, label: str) -> bool:
    """The visible label names the OTHER part of a person's name than the token."""
    w = label_words(label)
    given, family = bool(w & GIVEN_WORDS), bool(w & FAMILY_WORDS)
    if token == "given-name":
        return family and not given
    if token == "family-name":
        return given and not family
    return False


_CONTEXT_JS = """(sel) => {
  const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
  let el = null; try { el = document.querySelector(sel); } catch (e) { return {}; }
  if (!el) return {};
  let heading = '';
  const all = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6, legend'));
  for (const h of all) if (h.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING && !h.contains(el)) heading = norm(h.innerText);
  const form = el.form || el.closest('form');
  let intro = '';
  if (form) {
    for (let s = form.previousElementSibling; s && intro.length < 400; s = s.previousElementSibling) {
      if (/^(P|DIV|SECTION|ASIDE)$/.test(s.tagName) && s.getClientRects().length) intro = norm(s.innerText) + ' ' + intro;
      if (/^H[1-6]$/.test(s.tagName)) break;
    }
  }
  return { heading: heading.slice(0, 160), intro: norm(intro).slice(-400) };
}"""


register({
    "c135.invalid": {
        "en": "The autocomplete value “{value}” is not a valid input purpose, so browsers and assistive tools cannot fill in or label this field.",
        "de": "Der autocomplete-Wert «{value}» ist kein gültiger Eingabezweck; Browser und Hilfsmittel können dieses Feld weder ausfüllen noch kennzeichnen.",
        "fr": "La valeur autocomplete « {value} » n'est pas une finalité valide : navigateurs et aides techniques ne peuvent ni remplir ni signaler ce champ.",
        "it": "Il valore autocomplete «{value}» non è uno scopo valido: browser e tecnologie assistive non possono compilare né identificare questo campo.",
    },
    "c135.valid": {
        "en": "The field declares its purpose with autocomplete=\"{value}\".",
        "de": "Das Feld gibt seinen Zweck mit autocomplete=\"{value}\" an.",
        "fr": "Le champ déclare sa finalité avec autocomplete=\"{value}\".",
        "it": "Il campo dichiara il suo scopo con autocomplete=\"{value}\".",
    },
    "c135.password": {
        "en": "This password field has no autocomplete token (current-password or new-password).",
        "de": "Dieses Kennwortfeld hat kein autocomplete-Token (current-password oder new-password).",
        "fr": "Ce champ de mot de passe n'a pas de jeton autocomplete (current-password ou new-password).",
        "it": "Questo campo password non ha un token autocomplete (current-password o new-password).",
    },
    "c135.quantity": {
        "en": "A number field that asks for a quantity or count, not for data about the user: 1.3.5 does not apply.",
        "de": "Ein Zahlenfeld für eine Menge oder Anzahl, nicht für Daten über die Person: 1.3.5 gilt nicht.",
        "fr": "Un champ numérique qui demande une quantité, pas des données sur la personne : le critère 1.3.5 ne s'applique pas.",
        "it": "Un campo numerico che chiede una quantità, non dati sulla persona: l'1.3.5 non si applica.",
    },
    "c135.apertus_user_own": {
        "en": "Apertus judged that “{label}” asks for the user's own data, but the field declares no input purpose (autocomplete missing or off).",
        "de": "Apertus beurteilt, dass «{label}» nach eigenen Daten der Person fragt, das Feld aber keinen Eingabezweck angibt (autocomplete fehlt oder ist off).",
        "fr": "Apertus juge que « {label} » demande des données de la personne elle-même, mais le champ ne déclare aucune finalité (autocomplete absent ou off).",
        "it": "Apertus giudica che «{label}» chieda dati propri dell'utente, ma il campo non dichiara alcuno scopo (autocomplete assente o off).",
    },
    "c135.apertus_other_person": {
        "en": "Apertus judged that “{label}” asks for data about another person; the criterion only covers the user's own data.",
        "de": "Apertus beurteilt, dass «{label}» nach Daten einer anderen Person fragt; das Kriterium betrifft nur eigene Daten.",
        "fr": "Apertus juge que « {label} » demande des données d'une autre personne ; le critère ne vise que les données de l'utilisateur.",
        "it": "Apertus giudica che «{label}» chieda dati di un'altra persona; il criterio riguarda solo i dati dell'utente.",
    },
    "c135.apertus_either": {
        "en": "The page lets the user fill in “{label}” for themselves or for someone else, so whether it must declare a purpose cannot be decided from the page. A person must decide.",
        "de": "Die Seite erlaubt, «{label}» für sich selbst oder für jemand anderen auszufüllen; ob ein Eingabezweck nötig ist, lässt sich so nicht entscheiden. Eine Person muss entscheiden.",
        "fr": "La page permet de remplir « {label} » pour soi ou pour quelqu'un d'autre : on ne peut pas décider s'il faut une finalité. Une personne doit trancher.",
        "it": "La pagina consente di compilare «{label}» per sé o per altri: non si può decidere se serva uno scopo. Una persona deve decidere.",
    },
    "c135.apertus_not_listed": {
        "en": "Apertus judged that “{label}” is not one of the listed personal data purposes, so no autocomplete token is required.",
        "de": "Apertus beurteilt, dass «{label}» keiner der aufgeführten Zwecke für persönliche Daten ist; ein autocomplete-Token ist nicht nötig.",
        "fr": "Apertus juge que « {label} » ne correspond à aucune finalité de données personnelles listée : aucun jeton autocomplete n'est requis.",
        "it": "Apertus giudica che «{label}» non sia uno degli scopi di dati personali elencati: non serve un token autocomplete.",
    },
    "c135.apertus_unsure": {
        "en": "Apertus could not decide whose data “{label}” collects. A person must check it.",
        "de": "Apertus konnte nicht entscheiden, wessen Daten «{label}» erfasst. Eine Person muss es prüfen.",
        "fr": "Apertus n'a pas pu décider à qui appartiennent les données de « {label} ». Une personne doit vérifier.",
        "it": "Apertus non ha potuto decidere di chi siano i dati di «{label}». Una persona deve verificare.",
    },
    "c135.wrong_purpose": {
        "en": "The label “{label}” asks for a different part of the name than autocomplete=\"{value}\" says; autofill will put the wrong value here.",
        "de": "Die Beschriftung «{label}» fragt nach einem anderen Namensteil, als autocomplete=\"{value}\" angibt; das automatische Ausfüllen setzt hier den falschen Wert ein.",
        "fr": "L'étiquette « {label} » demande une autre partie du nom que autocomplete=\"{value}\" ; le remplissage automatique y mettra la mauvaise valeur.",
        "it": "L'etichetta «{label}» chiede una parte del nome diversa da autocomplete=\"{value}\"; la compilazione automatica inserirà il valore sbagliato.",
    },
    "c135.fix_hint": {
        "en": "Add autocomplete=\"{token}\" to the field (in your CMS: the field's autofill or input-purpose setting).",
        "de": "Ergänzen Sie autocomplete=\"{token}\" am Feld (im CMS: Einstellung für automatisches Ausfüllen bzw. Eingabezweck).",
        "fr": "Ajoutez autocomplete=\"{token}\" au champ (dans votre CMS : réglage de remplissage automatique ou de finalité).",
        "it": "Aggiungete autocomplete=\"{token}\" al campo (nel CMS: impostazione di compilazione automatica o scopo).",
    },
    "c135.fix_hint_plain": {
        "en": "Give the field an autocomplete token from the WCAG list of input purposes.",
        "de": "Geben Sie dem Feld ein autocomplete-Token aus der WCAG-Liste der Eingabezwecke.",
        "fr": "Donnez au champ un jeton autocomplete de la liste WCAG des finalités.",
        "it": "Assegnate al campo un token autocomplete dall'elenco WCAG degli scopi.",
    },
    "c135.impact": {
        "en": "People with motor or cognitive disabilities cannot let the browser fill in this field, and tools cannot add familiar icons to it.",
        "de": "Menschen mit motorischen oder kognitiven Einschränkungen können dieses Feld nicht automatisch ausfüllen lassen, und Hilfsmittel können keine vertrauten Symbole anzeigen.",
        "fr": "Les personnes avec un handicap moteur ou cognitif ne peuvent pas faire remplir ce champ par le navigateur, et les outils ne peuvent pas y ajouter d'icônes familières.",
        "it": "Le persone con disabilità motorie o cognitive non possono far compilare questo campo dal browser, e gli strumenti non possono aggiungervi icone familiari.",
    },
    "c135.impact_ok": {
        "en": "Browsers can fill in this field, and tools can show what it asks for.",
        "de": "Browser können dieses Feld ausfüllen, und Hilfsmittel können zeigen, wonach es fragt.",
        "fr": "Les navigateurs peuvent remplir ce champ, et les outils peuvent montrer ce qu'il demande.",
        "it": "I browser possono compilare questo campo e gli strumenti possono mostrare cosa chiede.",
    },
})

# A number field matches a WCAG §7 purpose only for these (birth date, card, postcode, phone).
NUMERIC_PURPOSE_STEMS = ("geburt", "jahrgang", "naissance", "nascita", "birth", "karte", "carte", "carta", "card",
                         "plz", "npa", "cap", "postleit", "postal", "telefon", "téléphone", "telefono", "phone",
                         "tel", "natel", "mobile", "handy", "jahr", "année", "anno", "year", "monat", "mois",
                         "mese", "month", "tag", "jour", "giorno", "day")


def numeric_purpose(label: str) -> bool:
    ws = re.findall(r"\w+", (label or "").casefold())
    return any(w.startswith(NUMERIC_PURPOSE_STEMS) for w in ws)


CATEGORIES = ["user_own", "other_person", "either", "not_listed"]
CATEGORY_OUTCOME = {"user_own": "failed", "other_person": "passed", "either": "cantTell", "not_listed": "passed"}
NAME_CATEGORIES = ["given_name", "family_name", "full_name", "other"]


class IdentifyInputPurpose(BaseCheck):
    criterion = "1.3.5"
    prompt_version = PROMPT_VERSION
    max_candidates = 80

    def candidates(self, page: CapturedPage) -> list[Candidate]:
        search_forms = {f["selector"] for f in page.forms if 'role="search"' in (f.get("html") or "")[:300]}
        # login / sign-up forms: a user-name field, two password fields (choose + repeat), or
        # login/account wording in the form (heading, button, labels)
        account_forms = {f.get("form") for f in page.fields if f.get("form") and is_username_field(f)}
        pw_count: dict[str | None, int] = {}
        for f in page.fields:
            if (f.get("type") or "").lower() == "password":
                pw_count[f.get("form")] = pw_count.get(f.get("form"), 0) + 1
        account_forms |= {k for k, n in pw_count.items() if k and n >= 2}
        account_forms |= {fm["selector"] for fm in page.forms if account_wording(_html_text(fm.get("html", "")))}
        out: list[Candidate] = []
        asked = 0
        for f in page.fields:
            ftype = (f.get("type") or "text").lower() if f.get("tag") == "input" else (f.get("tag") or "")
            if f.get("tag") not in ("input", "select", "textarea") or ftype in SKIP_TYPES:
                continue
            if f.get("form") in search_forms or (f.get("field_name") or "").lower() in ("q", "query", "search"):
                continue
            label = norm_ws(" ".join(f.get("labels") or []) or f.get("name") or f.get("name_js") or
                            f.get("placeholder") or "")
            value = f.get("autocomplete")
            valid, token = parse_autocomplete(value or "")
            common = dict(selector=f["selector"], html=f.get("html", ""), accessible_name=label or None,
                          lang=f.get("lang"))
            if value is not None and value.strip() and not valid:
                out.append(self.candidate(page, text=label, kind="invalid", value=value, **common))
                continue
            if token and token not in ("on", "off"):
                kind = "contradicted" if contradicts(token, label) else "valid"
                if kind == "contradicted":
                    asked += 1
                out.append(self.candidate(page, text=label, kind=kind, value=value, token=token,
                                          context={"label": label} if kind == "contradicted" else None, **common))
                continue
            if ftype == "password" and password_label(label) and f.get("form") in account_forms:
                out.append(self.candidate(page, text=label, kind="password", value=value or "", **common))
                continue
            if ftype == "number" and not numeric_purpose(label):
                out.append(self.candidate(page, text=label, kind="quantity", value=value, **common))
                continue
            if asked >= MAX_QUESTIONS:
                continue
            asked += 1
            ctx = self._context(page, f["selector"])
            parts = {"label": label, "legend": norm_ws(f.get("legend") or ""), "heading": ctx.get("heading", ""),
                     "text_before_form": ctx.get("intro", "")}
            if parts["heading"] == parts["legend"]:
                parts["heading"] = ""
            parts = {k: v for k, v in parts.items() if v}
            text = " … ".join(parts.values())
            out.append(self.candidate(page, text=text, kind="ask", value=value, off=(value or "").strip().lower() == "off",
                                      parts=parts, field_type=ftype, context=parts, **common))
        return out[: self.max_candidates]

    @staticmethod
    def _context(page: CapturedPage, selector: str) -> dict:
        try:
            return page.evaluate(_CONTEXT_JS, selector) or {}
        except Exception:
            return {}

    def decide(self, c: Candidate) -> Finding | None:
        kind, ui, value = c.extra.get("kind"), self.ui_lang, c.extra.get("value") or ""
        excerpt = f'autocomplete="{value}"' if f'autocomplete="{value}"' in c.html else None
        if kind == "invalid":
            return self.finding(c, outcome="failed", source="rule", confidence="high", act_rule="73f2c2",
                                excerpt=excerpt, explanation=t("c135.invalid", ui, value=value),
                                user_impact=t("c135.impact", ui), fix_hint=t("c135.fix_hint_plain", ui))
        if kind == "valid":
            return self.finding(c, outcome="passed", source="rule", confidence="medium", act_rule="73f2c2",
                                excerpt=excerpt, explanation=t("c135.valid", ui, value=value),
                                user_impact=t("c135.impact_ok", ui))
        if kind == "quantity":
            return self.finding(c, outcome="inapplicable", source="heuristic", confidence="medium",
                                explanation=t("c135.quantity", ui), user_impact=t("c135.impact_ok", ui))
        if kind == "password":
            token = "current-password"
            return self.finding(c, outcome="failed", source="heuristic", confidence="medium",
                                explanation=t("c135.password", ui), user_impact=t("c135.impact", ui),
                                fix_diff=unified_diff(c.html, set_attr(c.html, "autocomplete", token), c.selector),
                                fix_hint=t("c135.fix_hint", ui, token=token))
        return None

    SYSTEM = (
        "You check WCAG 2.1 success criterion 1.3.5 Identify Input Purpose for ONE form field. The criterion "
        "covers only fields that collect information about the user, for purposes such as name, contact "
        "details, postal address, birthday, account or payment data. Classify whose data the field collects:\n"
        "- user_own: personal data of the person filling in the form\n"
        "- other_person: personal data of someone else (a child, a recipient, a contact person, a doctor)\n"
        "- either: the page says the form can be filled in for oneself or for another person\n"
        "- not_listed: no personal data of such a purpose (a search, a comment, a quantity, a reference "
        "number, a title, a date of an event)\n"
        "quote: the words that decide, copied exactly."
    )
    SYSTEM_NAME = (
        "You check WCAG 2.1 success criterion 1.3.5 Identify Input Purpose for ONE form field. Classify which "
        "part of a person's name its visible label asks for:\n"
        "- given_name: the first or given name only\n"
        "- family_name: the last or family name only\n"
        "- full_name: the whole name\n"
        "- other: something else, or unsure\n"
        "quote: the label words that decide, copied exactly."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        if c.extra.get("kind") == "contradicted":
            return self.task(system=self.system_prompt(self.SYSTEM_NAME, c), element={"label": c.text}, context={},
                             question="Which part of the name does the label ask for?",
                             schema=category_schema(NAME_CATEGORIES), max_tokens=100)
        element = dict(c.extra.get("parts") or {})
        return self.task(system=self.system_prompt(self.SYSTEM, c), element=element, context={},
                         question="Whose data does this field collect?",
                         schema=category_schema(CATEGORIES), max_tokens=120)

    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        label = c.accessible_name or ""
        category = answer.get("category")
        conf = answer.get("confidence", "low")
        if c.extra.get("kind") == "contradicted":
            token = c.extra.get("token", "")
            expected = NAME_PARTS.get(token)
            if category in ("given_name", "family_name") and expected and category != expected:
                return self.finding(c, outcome="failed", source="apertus", confidence=conf, act_rule=None,
                                    excerpt=self.model_excerpt(c, answer, "failed"),
                                    explanation=t("c135.wrong_purpose", ui, label=label, value=c.extra.get("value")),
                                    user_impact=t("c135.impact", ui), reason=answer.get("reason"),
                                    reason_code="apertus_wrong_purpose")
            if category == expected:
                return self.finding(c, outcome="passed", source="apertus", confidence=conf,
                                    excerpt=self.model_excerpt(c, answer, "passed"),
                                    explanation=t("c135.valid", ui, value=c.extra.get("value")),
                                    user_impact=t("c135.impact_ok", ui), reason=answer.get("reason"),
                                    reason_code="apertus_purpose_matches")
            return self.finding(c, outcome="cantTell", source="apertus", confidence="low",
                                excerpt=self.model_excerpt(c, answer, "cantTell"),
                                explanation=t("c135.apertus_unsure", ui, label=label),
                                user_impact=t("impact.review", ui), reason=answer.get("reason"),
                                reason_code="apertus_unsure")
        outcome = CATEGORY_OUTCOME.get(category, "cantTell")
        key = f"c135.apertus_{category}" if category in CATEGORY_OUTCOME else "c135.apertus_unsure"
        fix: dict = {}
        if outcome == "failed":
            fix = {"fix_hint": t("c135.fix_hint_plain", ui)}
        impact = {"passed": t("c135.impact_ok", ui), "failed": t("c135.impact", ui)}.get(outcome, t("impact.review", ui))
        return self.finding(c, outcome=outcome, source="apertus",
                            confidence=conf if outcome != "cantTell" else "low",
                            excerpt=self.model_excerpt(c, answer, outcome), explanation=t(key, ui, label=label),
                            user_impact=impact, reason=answer.get("reason"),
                            reason_code=("apertus_user_own_off" if category == "user_own" and c.extra.get("off")
                                         else f"apertus_{category}" if category in CATEGORY_OUTCOME else "apertus_unsure"),
                            **fix)


CHECK = IdentifyInputPurpose
