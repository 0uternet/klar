"""3.3.4 Error Prevention (Legal, Financial, Data), level AA. No ACT rule.

Unit: the <form>. Uses the form interaction of 3.3.1 (`c_3_3_1.form_evidence`): the form is
submitted empty in a throw-away tab where nothing can leave the browser, only where the
scan allows form submission (see that module).

Decided in code (the SC is met when a submission is Reversible, Checked or Confirmed)
  * the page checks the input: an empty submission shows errors          → passed ("Checked")
  * a confirm() dialog, an in-page dialog, or new buttons outside the form
    after submitting (a review step with a final button)                 → passed ("Confirmed", G98/G168)
  * the submission leaves the page (to a server or a payment provider)   → cantTell (not observable)
  * nothing observable, or the test submission failed twice              → cantTell
  * not tested (any site other than the demo site / test pages)          → cantTell note
Asked to Apertus (one categorical question per form that completed at once, with the page
heading, the text around the form, the field labels, the button and the text shown after):
  "What does this submission commit the user to, and can it be undone?"
    no_commitment | conditional_fee | cancellable_stated | cancellable_vague | final
  mapped in code (data/testset/PROTOCOL.md §3.3.4): no_commitment → inapplicable (out of scope),
  conditional_fee → cantTell (scope depends on terms not on the page), cancellable_stated →
  passed (Reversible: a stated time or way to cancel or restore), cancellable_vague → cantTell
  (asserted without a mechanism), final → failed.

Known limits: one empty submission; a review step is recognised by new buttons, not by
reading them; whether "checked" covers every value is not verified; payment pages and
server steps are not followed.
"""

from __future__ import annotations

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema, norm_ws
from klar.checks.c_3_3_1 import form_evidence, is_search_form
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "3.3.4/v1"

CATEGORIES = ["no_commitment", "conditional_fee", "cancellable_stated", "cancellable_vague", "final"]
CATEGORY_OUTCOME = {"no_commitment": "inapplicable", "conditional_fee": "cantTell", "cancellable_stated": "passed",
                    "cancellable_vague": "cantTell", "final": "failed"}

register({
    "c334.checked": {
        "en": "The page checks the entries before sending: an empty submission shows errors that can be corrected (“Checked”).",
        "de": "Die Seite prüft die Eingaben vor dem Senden: Wird das Formular leer abgeschickt, erscheinen Fehler, die man korrigieren kann («Geprüft»).",
        "fr": "La page vérifie les saisies avant l'envoi : un envoi vide affiche des erreurs que l'on peut corriger (« Vérifié »).",
        "it": "La pagina controlla i dati prima dell'invio: un invio vuoto mostra errori che si possono correggere («Verificato»).",
    },
    "c334.confirmed": {
        "en": "Submitting does not finish at once: the page asks for a confirmation or shows a review step with a final button (“Confirmed”).",
        "de": "Das Absenden ist nicht sofort abgeschlossen: Die Seite verlangt eine Bestätigung oder zeigt einen Kontrollschritt mit einer letzten Schaltfläche («Bestätigt»).",
        "fr": "L'envoi ne se termine pas d'un coup : la page demande une confirmation ou affiche une étape de contrôle avec un bouton final (« Confirmé »).",
        "it": "L'invio non si conclude subito: la pagina chiede una conferma o mostra un passo di verifica con un pulsante finale («Confermato»).",
    },
    "c334.leaves": {
        "en": "Submitting this form continues on another page or server, which Klar. does not follow. A person must check whether a review, check or cancellation happens there.",
        "de": "Nach dem Absenden geht es auf einer anderen Seite oder einem anderen Server weiter; dorthin folgt Klar. nicht. Eine Person muss prüfen, ob dort eine Kontrolle, Prüfung oder Stornierung möglich ist.",
        "fr": "Ce formulaire se poursuit sur une autre page ou un serveur que Klar. ne suit pas. Une personne doit vérifier s'il y a là une étape de contrôle, de vérification ou d'annulation.",
        "it": "Questo modulo prosegue su un'altra pagina o un server che Klar. non segue. Una persona deve verificare se lì c'è un controllo, una verifica o un annullamento.",
    },
    "c334.nothing": {
        "en": "Submitting this form produced no visible change. A person must check what it commits to and whether it can be reviewed or undone.",
        "de": "Das Absenden dieses Formulars bewirkte keine sichtbare Änderung. Eine Person muss prüfen, wozu es verpflichtet und ob es kontrolliert oder rückgängig gemacht werden kann.",
        "fr": "L'envoi de ce formulaire n'a produit aucun changement visible. Une personne doit vérifier ce qu'il engage et s'il peut être contrôlé ou annulé.",
        "it": "L'invio di questo modulo non ha prodotto cambiamenti visibili. Una persona deve verificare a cosa impegna e se può essere controllato o annullato.",
    },
    "c334.probe_failed": {
        "en": "Klar. could not complete the test submission of this form (the page did not respond in time). A person must check it.",
        "de": "Klar. konnte das testweise Absenden dieses Formulars nicht abschliessen (die Seite reagierte nicht rechtzeitig). Eine Person muss es prüfen.",
        "fr": "Klar. n'a pas pu terminer l'envoi de test de ce formulaire (la page n'a pas répondu à temps). Une personne doit le vérifier.",
        "it": "Klar. non ha potuto completare l'invio di prova di questo modulo (la pagina non ha risposto in tempo). Una persona deve verificarlo.",
    },
    "c334.untested": {
        "en": "Klar. submits forms only on the demo site and on test pages. If this form orders, pays, signs or deletes data, a person must check that it can be reviewed, checked or undone.",
        "de": "Klar. schickt Formulare nur auf der Demo-Website und auf Testseiten ab. Wenn dieses Formular bestellt, bezahlt, verpflichtet oder Daten löscht, muss eine Person prüfen, ob es kontrolliert, geprüft oder rückgängig gemacht werden kann.",
        "fr": "Klar. n'envoie des formulaires que sur le site de démonstration et les pages de test. Si ce formulaire commande, paie, engage ou supprime des données, une personne doit vérifier qu'il peut être contrôlé, vérifié ou annulé.",
        "it": "Klar. invia moduli solo sul sito demo e sulle pagine di test. Se questo modulo ordina, paga, impegna o cancella dati, una persona deve verificare che possa essere controllato, verificato o annullato.",
    },
    "c334.apertus_no_commitment": {
        "en": "Apertus judged that this form creates no payment, contract or change to stored data, so the criterion does not apply.",
        "de": "Apertus beurteilt, dass dieses Formular keine Zahlung, keinen Vertrag und keine Änderung gespeicherter Daten bewirkt; das Kriterium gilt hier nicht.",
        "fr": "Apertus juge que ce formulaire n'entraîne ni paiement, ni contrat, ni modification de données enregistrées : le critère ne s'applique pas.",
        "it": "Apertus giudica che questo modulo non comporti pagamenti, contratti o modifiche a dati salvati: il criterio non si applica.",
    },
    "c334.apertus_conditional_fee": {
        "en": "The service is free, but a fee applies under some condition. Whether this is a binding commitment depends on terms not on the page: a person must decide.",
        "de": "Das Angebot ist kostenlos, unter einer Bedingung fällt aber eine Gebühr an. Ob das eine verbindliche Verpflichtung ist, hängt von Bestimmungen ab, die nicht auf der Seite stehen: Eine Person muss entscheiden.",
        "fr": "Le service est gratuit, mais des frais s'appliquent sous condition. Savoir s'il s'agit d'un engagement dépend de conditions absentes de la page : une personne doit trancher.",
        "it": "Il servizio è gratuito, ma in certi casi si paga una tassa. Se sia un impegno vincolante dipende da condizioni non presenti nella pagina: una persona deve decidere.",
    },
    "c334.apertus_cancellable_stated": {
        "en": "Apertus judged that the page states a time or a way to cancel or restore this submission (“Reversible”).",
        "de": "Apertus beurteilt, dass die Seite eine Frist oder einen Weg nennt, um diese Übermittlung zu stornieren oder wiederherzustellen («Umkehrbar»).",
        "fr": "Apertus juge que la page indique un délai ou un moyen d'annuler ou de restaurer cet envoi (« Réversible »).",
        "it": "Apertus giudica che la pagina indichi un termine o un modo per annullare o ripristinare questo invio («Reversibile»).",
    },
    "c334.apertus_cancellable_vague": {
        "en": "The page says the submission can be revoked, but gives no time and no way to do it. A person must check that it really can be undone.",
        "de": "Die Seite sagt, die Übermittlung könne widerrufen werden, nennt aber weder Frist noch Weg. Eine Person muss prüfen, ob sie wirklich rückgängig gemacht werden kann.",
        "fr": "La page dit que l'envoi peut être révoqué, sans délai ni moyen. Une personne doit vérifier qu'il peut vraiment être annulé.",
        "it": "La pagina dice che l'invio può essere revocato, ma senza termine né modalità. Una persona deve verificare che si possa davvero annullare.",
    },
    "c334.apertus_final": {
        "en": "This form commits the user (payment, order, contract or deletion) and completes on the first click: no review, no check of the entries, no way to cancel.",
        "de": "Dieses Formular verpflichtet (Zahlung, Bestellung, Vertrag oder Löschung) und schliesst beim ersten Klick ab: keine Kontrolle, keine Prüfung der Eingaben, keine Stornierung.",
        "fr": "Ce formulaire engage l'utilisateur (paiement, commande, contrat ou suppression) et se termine au premier clic : ni contrôle, ni vérification des saisies, ni annulation.",
        "it": "Questo modulo impegna l'utente (pagamento, ordine, contratto o cancellazione) e si conclude al primo clic: nessuna verifica, nessun controllo dei dati, nessun annullamento.",
    },
    "c334.apertus_unsure": {
        "en": "Apertus could not decide what this form commits to. A person must check it.",
        "de": "Apertus konnte nicht entscheiden, wozu dieses Formular verpflichtet. Eine Person muss es prüfen.",
        "fr": "Apertus n'a pas pu décider ce qu'engage ce formulaire. Une personne doit vérifier.",
        "it": "Apertus non ha potuto decidere a cosa impegni questo modulo. Una persona deve verificare.",
    },
    "c334.impact": {
        "en": "A typing or clicking mistake, more likely with a disability, becomes a binding order, payment or deletion that cannot be corrected.",
        "de": "Ein Tipp- oder Klickfehler, mit einer Behinderung wahrscheinlicher, wird zu einer verbindlichen Bestellung, Zahlung oder Löschung, die sich nicht korrigieren lässt.",
        "fr": "Une erreur de frappe ou de clic, plus probable avec un handicap, devient une commande, un paiement ou une suppression définitifs.",
        "it": "Un errore di digitazione o di clic, più probabile con una disabilità, diventa un ordine, un pagamento o una cancellazione definitivi.",
    },
    "c334.impact_ok": {
        "en": "Users can catch a mistake before it becomes binding, or undo it.",
        "de": "Nutzende können einen Fehler erkennen, bevor er verbindlich wird, oder ihn rückgängig machen.",
        "fr": "Les utilisateurs peuvent repérer une erreur avant qu'elle ne devienne définitive, ou l'annuler.",
        "it": "Gli utenti possono accorgersi di un errore prima che diventi vincolante, o annullarlo.",
    },
})


class ErrorPrevention(BaseCheck):
    criterion = "3.3.4"
    prompt_version = PROMPT_VERSION
    max_candidates = 10

    def candidates(self, page: CapturedPage) -> list[Candidate]:
        _, forms = form_evidence(page)
        out: list[Candidate] = []
        for frec in forms:
            if is_search_form(frec, page) or not (frec.get("has_submit") or frec.get("status") == "tested"):
                continue
            sel, html = frec["selector"], frec.get("html", "")
            if frec["status"] != "tested":
                out.append(self.candidate(page, selector=sel, html=html, kind="untested"))
                continue
            passes = frec.get("passes") or {}
            empty = passes.get("empty") or passes.get("junk") or {}
            checked = any((f.get("visible_text") or f.get("native") or f.get("marked") or f.get("hidden_text"))
                          for p in passes.values() for f in (p.get("fields") or []))
            confirmed = any(d.get("type") == "confirm" for d in empty.get("dialogs", [])) or bool(
                empty.get("dialog_open") or empty.get("new_controls"))
            leaves = bool(empty.get("navigations") or empty.get("blocked"))
            changed = bool(empty.get("new_text") or not empty.get("form_visible", True))
            if frec.get("probe_error"):
                kind = "probe_failed"
            elif checked:
                kind = "checked"
            elif confirmed:
                kind = "confirmed"
            elif leaves and not changed:
                kind = "leaves"
            elif not changed:
                kind = "nothing"
            else:
                kind = "ask"
            ctx = frec.get("context") or {}
            labels = ", ".join(norm_ws(f.get("label") or f.get("name") or "") for f in (frec.get("fields") or [])
                               if (f.get("label") or f.get("name")))[:300]
            after = norm_ws(empty.get("new_text", "").replace(" | ", " "))[:400]
            before = ctx.get("before", "")
            if ctx.get("heading") and before.startswith(ctx["heading"]):
                before = before[len(ctx["heading"]):].strip()
            parts = {"page_heading": ctx.get("heading", "")[:200], "text_before_form": before[-700:],
                     "form_fields": labels, "submit_button": ctx.get("submit", "")[:120],
                     "text_after_form": ctx.get("after", "")[:300], "shown_after_submit": after}
            parts = {k: v for k, v in parts.items() if v}
            text = " … ".join(parts.values())
            out.append(self.candidate(page, selector=sel, html=html, text=text, kind=kind, parts=parts,
                                      new_controls=empty.get("new_controls", [])))
        return out[: self.max_candidates]

    def decide(self, c: Candidate) -> Finding | None:
        kind, ui = c.extra.get("kind"), self.ui_lang
        excerpt = c.html[:300]
        if kind == "checked":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", excerpt=excerpt,
                                explanation=t("c334.checked", ui), user_impact=t("c334.impact_ok", ui))
        if kind == "confirmed":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", excerpt=excerpt,
                                explanation=t("c334.confirmed", ui), user_impact=t("c334.impact_ok", ui))
        if kind == "leaves":
            return self.note(c, "c334.leaves", source="heuristic")
        if kind == "nothing":
            return self.note(c, "c334.nothing", source="heuristic")
        if kind == "probe_failed":
            return self.note(c, "c334.probe_failed", source="heuristic")
        if kind == "untested":
            return self.note(c, "c334.untested", source="heuristic")
        return None

    SYSTEM = (
        "You check WCAG 2.1 success criterion 3.3.4 Error Prevention (Legal, Financial, Data) for ONE form. "
        "Submitting it completed at once, without a review step and without checking the entries. Read the page "
        "text and classify the submission:\n"
        "- no_commitment: it creates no payment, order, contract or other legal obligation, does not delete or "
        "change the user's stored data, and does not submit test answers\n"
        "- conditional_fee: the service is free, but a fee or penalty applies under some condition\n"
        "- cancellable_stated: it is a commitment, and the page states a time limit or a concrete way to "
        "cancel, undo or restore it\n"
        "- cancellable_vague: it is a commitment, and the page only says that it can be revoked, without a time "
        "or a way\n"
        "- final: it is a commitment (payment, order, contract, deletion or change of stored data, test answers) "
        "and the page offers no way to cancel it\n"
        "quote: the words of the page that decide, copied exactly."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        return self.task(system=self.system_prompt(self.SYSTEM, c), element=c.extra.get("parts", {}), context={},
                         question="What does this submission commit the user to, and can it be undone?",
                         schema=category_schema(CATEGORIES), max_tokens=140)

    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        category = answer.get("category")
        outcome = CATEGORY_OUTCOME.get(category, "cantTell")
        key = f"c334.apertus_{category}" if category in CATEGORY_OUTCOME else "c334.apertus_unsure"
        impact = {"passed": t("c334.impact_ok", ui), "failed": t("c334.impact", ui)}.get(outcome, t("impact.review", ui))
        conf = answer.get("confidence", "low") if outcome in ("passed", "failed", "inapplicable") else "low"
        return self.finding(c, outcome=outcome, source="apertus", confidence=conf,
                            excerpt=self.model_excerpt(c, answer, outcome), explanation=t(key, ui),
                            user_impact=impact, reason=answer.get("reason"), reason_code=key.split(".")[-1])


CHECK = ErrorPrevention
