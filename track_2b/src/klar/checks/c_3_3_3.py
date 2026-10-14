"""3.3.3 Error Suggestion, level AA. No ACT rule.

Uses the form interaction of 3.3.1 (`c_3_3_1.form_evidence`: the form submitted in a
throw-away tab with an invalid and with an empty value, only where the scan allows
form submission; see that module). A field "has an automatically detected error"
when the page reacted to its value (message, aria-invalid, style, native validation).

Decided in code
  * password / access-code fields, or any field of a form with a password field
    (the SC's security exception: suggesting the right value would reveal it)  → passed
  * the browser's own validation (required, type, pattern with a title)        → passed
  * native validation of a `pattern` without a `title` (no format given)       → cantTell
  * the page accepts "x" but rejects the empty value (a presence check only) and
    shows a message: "fill it in" is the suggestion (technique G83)            → passed
  * the error is shown without any text (colour, icon, hidden text only)       → failed
  * nothing observable / form posts to a server / not tested / probe failed    → cantTell note
Asked to Apertus (one categorical question per field that has an error message)
  "Does the message help the user to correct the input?"
    format_or_example | allowed_values | corrected_value | missing_value | secret_answer | no_suggestion
  mapped in code (data/testset/PROTOCOL.md §3.3.3): every suggestion category and
  secret_answer (security / test-answer exception) → passed; no_suggestion → failed, except
  cantTell when the message was already in the static page (a server rejected a value: whether a
  suggestion is "known" is not visible) or when the field keeps a visible format hint next to it
  (experts disagree whether that hint counts as the suggestion).

Known limits: as 3.3.1 (one invalid value "x" and the empty value; asynchronous and server
checks are not observed); a quiz is only recognised from the page heading and the message.
"""

from __future__ import annotations

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema
from klar.checks.c_3_3_1 import field_label, form_evidence, is_search_form, message_of
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "3.3.3/v1"
SECRET_AUTOCOMPLETE = {"current-password", "new-password", "one-time-code"}

CATEGORIES = ["format_or_example", "allowed_values", "corrected_value", "missing_value", "secret_answer",
              "no_suggestion"]
SUGGESTS = {"format_or_example", "allowed_values", "corrected_value", "missing_value"}

register({
    "c333.secret": {
        "en": "This field asks for a password or access code. Suggesting the correct value would reveal it, so a plain error message is enough (security exception).",
        "de": "Dieses Feld fragt nach einem Kennwort oder Zugangscode. Ein Korrekturvorschlag würde ihn verraten, eine einfache Fehlermeldung genügt (Sicherheitsausnahme).",
        "fr": "Ce champ demande un mot de passe ou un code d'accès. Suggérer la bonne valeur la révélerait : un simple message d'erreur suffit (exception de sécurité).",
        "it": "Questo campo chiede una password o un codice di accesso. Suggerire il valore giusto lo rivelerebbe: basta un semplice messaggio di errore (eccezione di sicurezza).",
    },
    "c333.native": {
        "en": "The browser's own validation tells the user what is expected in this field.",
        "de": "Die Validierung des Browsers sagt, was in diesem Feld erwartet wird.",
        "fr": "La validation du navigateur indique ce qui est attendu dans ce champ.",
        "it": "La validazione del browser indica cosa è atteso in questo campo.",
    },
    "c333.presence_only": {
        "en": "The page only checks that this field is filled in, and the message “{message}” says that it is missing: that is the correction.",
        "de": "Die Seite prüft nur, ob dieses Feld ausgefüllt ist, und die Meldung «{message}» sagt, dass es fehlt: Das ist die Korrektur.",
        "fr": "La page vérifie seulement que ce champ est rempli, et le message « {message} » dit qu'il manque : c'est la correction.",
        "it": "La pagina verifica solo che questo campo sia compilato, e il messaggio «{message}» dice che manca: questa è la correzione.",
    },
    "c333.native_pattern": {
        "en": "The browser only says that the format does not match: the field has a pattern but no title that describes it. A person must check whether the format is explained.",
        "de": "Der Browser sagt nur, dass das Format nicht passt: Das Feld hat ein Muster (pattern), aber keinen title, der es beschreibt. Eine Person muss prüfen, ob das Format erklärt wird.",
        "fr": "Le navigateur dit seulement que le format ne correspond pas : le champ a un motif (pattern) sans title qui le décrive. Une personne doit vérifier si le format est expliqué.",
        "it": "Il browser dice solo che il formato non corrisponde: il campo ha un pattern ma nessun title che lo descriva. Una persona deve verificare se il formato è spiegato.",
    },
    "c333.no_text": {
        "en": "The page detects an error in this field but shows no text at all, so it suggests no correction.",
        "de": "Die Seite erkennt einen Fehler in diesem Feld, zeigt aber keinen Text und schlägt somit keine Korrektur vor.",
        "fr": "La page détecte une erreur dans ce champ mais n'affiche aucun texte, elle ne propose donc aucune correction.",
        "it": "La pagina rileva un errore in questo campo ma non mostra alcun testo, quindi non suggerisce correzioni.",
    },
    "c333.apertus_suggests": {
        "en": "Apertus judged that the message “{message}” tells the user how to correct the input.",
        "de": "Apertus beurteilt, dass die Meldung «{message}» sagt, wie die Eingabe zu korrigieren ist.",
        "fr": "Apertus juge que le message « {message} » indique comment corriger la saisie.",
        "it": "Apertus giudica che il messaggio «{message}» indichi come correggere l'inserimento.",
    },
    "c333.apertus_secret": {
        "en": "Apertus judged that this field asks for a secret or a test answer: suggesting the right value would defeat its purpose (exception).",
        "de": "Apertus beurteilt, dass dieses Feld nach einem Geheimnis oder einer Testantwort fragt: Ein Vorschlag würde den Zweck vereiteln (Ausnahme).",
        "fr": "Apertus juge que ce champ demande un secret ou une réponse de test : suggérer la bonne valeur irait contre son but (exception).",
        "it": "Apertus giudica che questo campo chieda un segreto o una risposta di test: suggerire il valore giusto ne vanificherebbe lo scopo (eccezione).",
    },
    "c333.apertus_none": {
        "en": "The message “{message}” only says that the input is wrong. It gives no format, example or allowed values, although the page checks them.",
        "de": "Die Meldung «{message}» sagt nur, dass die Eingabe falsch ist. Sie nennt weder Format noch Beispiel noch erlaubte Werte, obwohl die Seite sie prüft.",
        "fr": "Le message « {message} » dit seulement que la saisie est fausse. Il ne donne ni format, ni exemple, ni valeurs admises, alors que la page les vérifie.",
        "it": "Il messaggio «{message}» dice solo che l'inserimento è sbagliato. Non indica formato, esempio o valori ammessi, anche se la pagina li verifica.",
    },
    "c333.apertus_none_server": {
        "en": "The message “{message}” gives no suggestion, but the value was rejected by the server: whether a correction is known cannot be seen on the page. A person must decide.",
        "de": "Die Meldung «{message}» macht keinen Vorschlag, der Wert wurde aber vom Server abgelehnt: Ob eine Korrektur bekannt ist, lässt sich auf der Seite nicht erkennen. Eine Person muss entscheiden.",
        "fr": "Le message « {message} » ne propose rien, mais la valeur a été refusée par le serveur : on ne voit pas sur la page si une correction est connue. Une personne doit trancher.",
        "it": "Il messaggio «{message}» non suggerisce nulla, ma il valore è stato rifiutato dal server: dalla pagina non si vede se una correzione è nota. Una persona deve decidere.",
    },
    "c333.apertus_none_hint": {
        "en": "The message “{message}” gives no suggestion, but a format hint stays visible next to the field. Experts disagree whether that hint is enough: a person must decide.",
        "de": "Die Meldung «{message}» macht keinen Vorschlag, neben dem Feld bleibt aber ein Formathinweis sichtbar. Fachleute sind uneins, ob das genügt: Eine Person muss entscheiden.",
        "fr": "Le message « {message} » ne propose rien, mais une indication de format reste visible près du champ. Les experts divergent sur ce point : une personne doit trancher.",
        "it": "Il messaggio «{message}» non suggerisce nulla, ma accanto al campo resta visibile un'indicazione di formato. Gli esperti non concordano: una persona deve decidere.",
    },
    "c333.apertus_unsure": {
        "en": "Apertus could not decide whether the message “{message}” suggests a correction. A person must check it.",
        "de": "Apertus konnte nicht entscheiden, ob die Meldung «{message}» eine Korrektur vorschlägt. Eine Person muss es prüfen.",
        "fr": "Apertus n'a pas pu décider si le message « {message} » propose une correction. Une personne doit vérifier.",
        "it": "Apertus non ha potuto decidere se il messaggio «{message}» suggerisca una correzione. Una persona deve verificare.",
    },
    "c333.untested": {
        "en": "Klar. submits forms only on the demo site and on test pages. A person must enter wrong values and check that the messages say how to correct them.",
        "de": "Klar. schickt Formulare nur auf der Demo-Site und auf Testseiten ab. Eine Person muss falsche Werte eingeben und prüfen, ob die Meldungen sagen, wie man sie korrigiert.",
        "fr": "Klar. n'envoie des formulaires que sur le site de démonstration et les pages de test. Une personne doit saisir des valeurs fausses et vérifier que les messages disent comment les corriger.",
        "it": "Klar. invia moduli solo sul sito demo e sulle pagine di test. Una persona deve inserire valori errati e verificare che i messaggi dicano come correggerli.",
    },
    "c333.probe_failed": {
        "en": "Klar. could not complete the test submission of this form (the page did not respond in time). A person must check it.",
        "de": "Klar. konnte das Testabsenden dieses Formulars nicht abschliessen (die Seite reagierte nicht rechtzeitig). Eine Person muss es prüfen.",
        "fr": "Klar. n'a pas pu terminer l'envoi de test de ce formulaire (la page n'a pas répondu à temps). Une personne doit le vérifier.",
        "it": "Klar. non ha potuto completare l'invio di prova di questo modulo (la pagina non ha risposto in tempo). Una persona deve verificarlo.",
    },
    "c333.server": {
        "en": "This form is checked on the server; Klar. stopped the request, so the error messages could not be observed. A person must test it.",
        "de": "Dieses Formular wird auf dem Server geprüft; Klar. hat die Anfrage gestoppt, die Fehlermeldungen waren also nicht sichtbar. Eine Person muss es testen.",
        "fr": "Ce formulaire est vérifié sur le serveur ; Klar. a bloqué la requête, les messages d'erreur n'ont donc pas pu être observés. Une personne doit le tester.",
        "it": "Questo modulo è verificato sul server; Klar. ha bloccato la richiesta, quindi i messaggi di errore non sono osservabili. Una persona deve testarlo.",
    },
    "c333.impact": {
        "en": "People with cognitive disabilities or low vision may not find out how to fix the input and may give up.",
        "de": "Menschen mit kognitiven Einschränkungen oder Sehbehinderung finden eventuell nicht heraus, wie sie die Eingabe korrigieren, und geben auf.",
        "fr": "Les personnes avec un handicap cognitif ou une déficience visuelle risquent de ne pas savoir comment corriger la saisie et d'abandonner.",
        "it": "Le persone con disabilità cognitive o ipovisione possono non capire come correggere l'inserimento e rinunciare.",
    },
    "c333.impact_ok": {
        "en": "Users learn how to correct the input.",
        "de": "Nutzende erfahren, wie sie die Eingabe korrigieren.",
        "fr": "Les utilisateurs savent comment corriger la saisie.",
        "it": "Gli utenti sanno come correggere l'inserimento.",
    },
})


class ErrorSuggestion(BaseCheck):
    criterion = "3.3.3"
    prompt_version = PROMPT_VERSION
    max_candidates = 60

    def candidates(self, page: CapturedPage) -> list[Candidate]:
        fields, forms = form_evidence(page)
        secret_forms = {f["form"] for f in fields if self._secret(f)}
        for frec in forms:
            for meta in frec.get("fields") or []:
                if self._secret(meta):
                    secret_forms.add(frec["selector"])
        heading = ""
        for frec in forms:
            heading = heading or (frec.get("context") or {}).get("heading", "")
        out: list[Candidate] = []
        for rec in fields:
            msg, where = message_of(rec)
            ev = rec.get("evidence") or {}
            label = field_label(rec)
            if rec.get("form") in secret_forms:
                kind = "secret"
            elif where == "native":
                kind = "native_pattern" if rec.get("pattern") and "title=" not in (rec.get("html") or "") else "native"
            elif where in ("field", "form") and rec.get("presence_only"):
                kind = "presence_only"
            elif where in ("field", "form", "static"):
                kind = "ask"
            elif ev.get("marked") or ev.get("style_changed") or ev.get("icons") or ev.get("hidden_text"):
                kind = "no_text"
            else:
                continue
            context = {"field_label": label}
            if heading:
                context["page_heading"] = heading[:160]
            out.append(self.candidate(page, selector=rec["selector"], html=rec.get("html", ""),
                                      text=msg if where not in ("native", "none") else "",
                                      accessible_name=label or None, context=context, kind=kind, where=where,
                                      hint=rec.get("hint", ""), message=msg))
        for frec in forms:
            if frec["status"] in ("untested", "skipped"):
                if frec.get("has_submit") and not is_search_form(frec, page):
                    out.append(self.candidate(page, selector=frec["selector"], html=frec.get("html", ""),
                                              key="#untested", kind="untested"))
            elif frec.get("probe_error"):
                out.append(self.candidate(page, selector=frec["selector"], html=frec.get("html", ""),
                                          key="#probe", kind="probe_failed"))
            elif not frec.get("observed") and (frec.get("navigated") or frec.get("blocked")):
                out.append(self.candidate(page, selector=frec["selector"], html=frec.get("html", ""),
                                          key="#server", kind="server"))
        return out[: self.max_candidates]

    @staticmethod
    def _secret(rec: dict) -> bool:
        ac = (rec.get("autocomplete") or "").lower().split()
        return (rec.get("type") or "").lower() == "password" or bool(SECRET_AUTOCOMPLETE & set(ac))

    def decide(self, c: Candidate) -> Finding | None:
        kind, ui = c.extra.get("kind"), self.ui_lang
        if kind == "secret":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium",
                                explanation=t("c333.secret", ui), user_impact=t("c333.impact_ok", ui))
        if kind == "native":
            return self.finding(c, outcome="passed", source="heuristic", confidence="low",
                                explanation=t("c333.native", ui), user_impact=t("c333.impact_ok", ui))
        if kind == "presence_only":
            msg = c.extra.get("message", "")
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", excerpt=msg[:300],
                                explanation=t("c333.presence_only", ui, message=msg[:160]),
                                user_impact=t("c333.impact_ok", ui))
        if kind == "native_pattern":
            return self.note(c, "c333.native_pattern", source="heuristic")
        if kind == "no_text":
            return self.finding(c, outcome="failed", source="heuristic", confidence="medium",
                                explanation=t("c333.no_text", ui), user_impact=t("c333.impact", ui))
        if kind == "untested":
            return self.note(c, "c333.untested", source="heuristic")
        if kind == "server":
            return self.note(c, "c333.server", source="heuristic")
        if kind == "probe_failed":
            return self.note(c, "c333.probe_failed", source="heuristic")
        return None

    SYSTEM = (
        "You check WCAG 2.1 success criterion 3.3.3 Error Suggestion for ONE form field. The page detected an "
        "input error in this field and showed the message below. Classify the message:\n"
        "- format_or_example: it states the expected format, length or characters, or gives an example\n"
        "- allowed_values: it lists the values that are accepted\n"
        "- corrected_value: it proposes a corrected value\n"
        "- missing_value: it says that a required value is missing\n"
        "- secret_answer: the field asks for a password, access code, anti-spam answer or test answer that must "
        "not be revealed\n"
        "- no_suggestion: it only says that the value is wrong, invalid or unknown\n"
        "quote: the part of the message that supports your answer, copied exactly."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        element = {"field_label": c.accessible_name or "", "message": c.extra.get("message", "")[:400]}
        return self.task(system=self.system_prompt(self.SYSTEM, c), element=element,
                         context={k: v for k, v in c.context.items() if k == "page_heading"},
                         question="Does the message help the user to correct the input?",
                         schema=category_schema(CATEGORIES), max_tokens=120)

    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        category = answer.get("category")
        msg = c.extra.get("message", "")[:160]
        if category in SUGGESTS:
            outcome, key = "passed", "c333.apertus_suggests"
        elif category == "secret_answer":
            outcome, key = "passed", "c333.apertus_secret"
        elif category == "no_suggestion" and c.extra.get("where") == "static":
            outcome, key = "cantTell", "c333.apertus_none_server"
        elif category == "no_suggestion" and c.extra.get("hint"):
            outcome, key = "cantTell", "c333.apertus_none_hint"
        elif category == "no_suggestion":
            outcome, key = "failed", "c333.apertus_none"
        else:
            outcome, key = "cantTell", "c333.apertus_unsure"
        impact = {"passed": t("c333.impact_ok", ui), "failed": t("c333.impact", ui)}.get(outcome, t("impact.review", ui))
        return self.finding(c, outcome=outcome, source="apertus",
                            confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
                            excerpt=self.model_excerpt(c, answer, outcome), explanation=t(key, ui, message=msg),
                            user_impact=impact, reason=answer.get("reason"),
                            reason_code=f"apertus_{category}" if category in CATEGORIES else "apertus_unsure")


CHECK = ErrorSuggestion
