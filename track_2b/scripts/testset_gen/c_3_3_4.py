"""3.3.4 Error Prevention (Legal, Financial, Data) -- 24 cases, target = the <form>.

Behaviour is the inline script as written: submit is intercepted and the resulting
state (receipt, review step, confirmation dialog) is shown in-page. Rules: protocol
fragment 3.3.4.
"""
from __future__ import annotations

import json

from common import *
from _forms_util import (field, select, fieldset, row, radios, form_case, js_validate,
                         T_FILLED, T_IBAN, T_EMAIL, t_digits)

CRITERION = "3.3.4"


def _s(x):
    return json.dumps(x, ensure_ascii=False)


def receipt(rid, html):
    return f'<div class="okbox" id="{rid}" tabindex="-1" hidden>{html}</div>'


def js_direct(fid, rid, fill=None):
    """Submit completes at once: form hidden, receipt shown (optionally echoing field values)."""
    fill = fill or {}
    lines = "".join(f'    document.getElementById({_s(span)}).textContent = document.getElementById({_s(src)}).value;\n'
                    for span, src in fill.items())
    return ("<script>\n"
            'document.addEventListener("DOMContentLoaded", function () {\n'
            f"  var form = document.getElementById({_s(fid)}), receipt = document.getElementById({_s(rid)});\n"
            '  form.addEventListener("submit", function (ev) {\n'
            "    ev.preventDefault();\n"
            f"{lines}"
            "    form.hidden = true;\n"
            "    receipt.hidden = false;\n"
            "    receipt.focus();\n"
            "  });\n"
            "});\n</script>")


def js_review(fid, review_id, list_id, fields, edit_id, ok_id, rid):
    """Two steps: submit shows a review list; 'edit' returns to the form, 'ok' finalises (G98)."""
    flds = ", ".join("[%s, %s]" % (_s(i), _s(l)) for i, l in fields)
    return ("<script>\n"
            'document.addEventListener("DOMContentLoaded", function () {\n'
            f"  var form = document.getElementById({_s(fid)}), review = document.getElementById({_s(review_id)});\n"
            f"  var list = document.getElementById({_s(list_id)}), receipt = document.getElementById({_s(rid)});\n"
            f"  var fields = [{flds}];\n"
            '  form.addEventListener("submit", function (ev) {\n'
            "    ev.preventDefault();\n"
            "    while (list.firstChild) { list.removeChild(list.firstChild); }\n"
            "    fields.forEach(function (p) {\n"
            '      var dt = document.createElement("dt"), dd = document.createElement("dd");\n'
            "      var el = document.getElementById(p[0]);\n"
            "      dt.textContent = p[1];\n"
            '      dd.textContent = el.value || "–";\n'
            "      list.appendChild(dt); list.appendChild(dd);\n"
            "    });\n"
            "    form.hidden = true; review.hidden = false;\n"
            '    review.querySelector("h2").focus();\n'
            "  });\n"
            f'  document.getElementById({_s(edit_id)}).addEventListener("click", function () {{\n'
            "    review.hidden = true; form.hidden = false; form.querySelector(\"input, select, textarea\").focus();\n"
            "  });\n"
            f'  document.getElementById({_s(ok_id)}).addEventListener("click", function () {{\n'
            "    review.hidden = true; receipt.hidden = false; receipt.focus();\n"
            "  });\n"
            "});\n</script>")


def review_box(rid, list_id, edit_id, ok_id, title, intro, edit_label, ok_label):
    return (f'<section id="{rid}" hidden><h2 tabindex="-1">{esc(title)}</h2><p>{esc(intro)}</p>'
            f'<dl id="{list_id}"></dl><div class="actions">'
            f'<button type="button" class="btn-sec" id="{edit_id}">{esc(edit_label)}</button>'
            f'<button type="button" id="{ok_id}">{esc(ok_label)}</button></div></section>')


def js_confirm(fid, dlg_id, cancel_id, ok_id, rid):
    """Submit opens an in-page confirmation dialog (G168)."""
    return ("<script>\n"
            'document.addEventListener("DOMContentLoaded", function () {\n'
            f"  var form = document.getElementById({_s(fid)}), dlg = document.getElementById({_s(dlg_id)});\n"
            f"  var receipt = document.getElementById({_s(rid)});\n"
            '  form.addEventListener("submit", function (ev) {\n'
            "    ev.preventDefault();\n"
            f"    dlg.hidden = false; document.getElementById({_s(cancel_id)}).focus();\n"
            "  });\n"
            f'  document.getElementById({_s(cancel_id)}).addEventListener("click", function () {{ dlg.hidden = true; }});\n'
            f'  document.getElementById({_s(ok_id)}).addEventListener("click", function () {{\n'
            "    dlg.hidden = true; form.hidden = true; receipt.hidden = false; receipt.focus();\n"
            "  });\n"
            "});\n</script>")


def dialog(did, title, text, cancel_id, cancel, ok_id, ok):
    return (f'<div class="dialog" id="{did}" role="alertdialog" aria-modal="true" aria-labelledby="{did}-titel" '
            f'aria-describedby="{did}-text" hidden><h2 id="{did}-titel">{esc(title)}</h2><p id="{did}-text">{esc(text)}</p>'
            f'<div class="actions"><button type="button" class="btn-sec" id="{cancel_id}">{esc(cancel)}</button>'
            f'<button type="button" id="{ok_id}">{esc(ok)}</button></div></div>')


def build(rng):
    cases = []

    def mk(lang, org, h1, intro, inner, *, fid, expected, rule, notes, script, after="", btn=None,
           buttons=None, trap=False, difficulty="medium", alt=None, novalidate=True, mode="custom",
           action=None, rules=()):
        cases.append(form_case(rng, CRITERION, lang, org, h1, intro, inner, rules, fid=fid, target=f"#{fid}",
                               expected=expected, rule=rule, notes=notes, trap=trap, difficulty=difficulty,
                               alt=alt, novalidate=novalidate, mode=mode, custom_script=script,
                               extra_after=after, btn=btn, buttons=buttons, action=action))

    # =====================================================================
    # FAILED: in scope, completes on first submit, no check / review / reversal
    # =====================================================================
    mk("de", "Gemeinde Beispielwil", "Wohnsitzbestätigung bestellen",
       "<p>Die Wohnsitzbestätigung kostet CHF 20.– pro Exemplar und wird mit Rechnung per Post zugestellt.</p>",
       row(field("name", "Name", ac="family-name", err=False), field("vorname", "Vorname", ac="given-name", err=False))
       + field("geburtsdatum", "Geburtsdatum", err=False)
       + select("exemplare", "Anzahl Kopien", ["1", "2", "3"], err=False)
       + field("lieferadresse", "Lieferadresse", textarea=True, rows=2, err=False),
       btn="Kostenpflichtig bestellen", fid="bestellung",
       script=js_direct("bestellung", "quittung"),
       after=receipt("quittung", "<p>Vielen Dank. Ihre Bestellung Nr. 2026-10418 ist eingegangen. Die Bestätigung wird Ihnen mit einer Rechnung zugestellt.</p>"),
       expected="failed", rule="3.3.4/F1",
       notes="Paid order (CHF 20.– per copy) is placed with the first click on 'Kostenpflichtig bestellen'; no review, no confirmation, no input check, no way to cancel is offered.",
       difficulty="easy")

    mk("de", "Gemeinde Fiktal", "Abmeldung bei Wegzug",
       "<p>Wenn Sie aus Fiktal wegziehen, müssen Sie sich innert 14 Tagen abmelden. Die Abmeldung ist gebührenfrei.</p>",
       row(field("name", "Name", err=False), field("vorname", "Vorname", err=False))
       + field("ahv", "AHV-Nummer", hint="756.0000.0000.00", err=False)
       + field("wegzug", "Wegzugsdatum", hint="TT.MM.JJJJ", err=False)
       + field("neue-adresse", "Neue Adresse (Strasse, PLZ, Ort)", err=False),
       btn="Abmeldung absenden", fid="abmeldung",
       script=js_direct("abmeldung", "quittung", {"q-datum": "wegzug"}),
       after=receipt("quittung", '<p>Ihre Abmeldung per <span id="q-datum"></span> wurde im Einwohnerregister erfasst. Die Abmeldebestätigung erhalten Sie per Post.</p>'),
       expected="failed", rule="3.3.4/F1",
       notes="Deregistration (a legal act that changes the population register) is recorded directly on submit; there is no review step, confirmation or stated way to undo it.",
       difficulty="easy")

    mk("de", "Stadt Mustersee", "Benutzerkonto löschen",
       "<p>Wenn Sie Ihr Konto im Online-Schalter löschen, werden alle gespeicherten Gesuche, hochgeladenen Dokumente und Zahlungsbelege entfernt.</p>",
       field("grund", "Grund für die Löschung (freiwillig)", textarea=True, rows=3, err=False),
       btn="Konto löschen", fid="konto-loeschen",
       script=js_direct("konto-loeschen", "quittung"),
       after=receipt("quittung", "<p>Ihr Konto und alle gespeicherten Daten wurden gelöscht.</p>"),
       expected="failed", rule="3.3.4/F1",
       notes="One click on 'Konto löschen' deletes the account and all stored applications and documents; no confirmation request and no recovery are offered.",
       difficulty="easy")

    mk("fr", "Commune de Valfictif", "Débit direct pour la taxe des chiens",
       "<p>Avec le débit direct, la taxe annuelle des chiens (CHF 100.– par chien) est prélevée automatiquement sur votre compte le 31 mars.</p>",
       field("titulaire", "Titulaire du compte", err=False)
       + field("iban", "IBAN", err=False)
       + select("chiens", "Nombre de chiens", ["1", "2", "3"], err=False),
       btn="Autoriser le prélèvement", fid="debit-direct",
       script=js_direct("debit-direct", "recu"),
       after=receipt("recu", "<p>Votre autorisation de débit direct est enregistrée. Le premier prélèvement aura lieu le 31 mars 2027.</p>"),
       expected="failed", rule="3.3.4/F1",
       notes="The direct-debit authorization (financial commitment) is registered immediately; the IBAN is not checked and there is no review or cancellation period.",
       difficulty="medium")

    mk("fr", "Ville de Bourg-Modèle", "Réservation de la salle polyvalente",
       "<p>Location pour une journée : CHF 250.– pour les sociétés locales, CHF 400.– pour les privés. Le montant est facturé à la réservation.</p>",
       field("organisateur", "Organisateur", err=False)
       + row(field("jour", "Date (JJ.MM.AAAA)", err=False), field("invites", "Nombre de personnes", im="numeric", err=False))
       + radios("tarif", "Tarif", ["Société locale (CHF 250.–)", "Privé (CHF 400.–)"], checked=0),
       btn="Réserver et payer", fid="reservation",
       script=js_direct("reservation", "recu", {"q-jour": "jour"}),
       after=receipt("recu", '<p>Votre réservation pour le <span id="q-jour"></span> est confirmée. La facture vous sera envoyée par courrier. En cas d\'annulation, le montant reste dû.</p>'),
       expected="failed", rule="3.3.4/F1",
       notes="A paid, non-refundable booking is confirmed on the first submit; the date is neither checked nor shown for review before the booking becomes binding.",
       difficulty="medium")

    mk("fr", "Commune d'Exempleval", "Coordonnées de remboursement",
       "<p>Les remboursements d'impôts et de taxes sont versés sur le compte enregistré dans votre espace personnel. Compte actuel : CH•• •••• •••• •••• •••4 2.</p>",
       field("nouvel-iban", "Nouvel IBAN", err=False)
       + field("titulaire", "Titulaire du compte", err=False),
       btn="Remplacer le compte", fid="compte-remboursement",
       script=js_direct("compte-remboursement", "recu"),
       after=receipt("recu", "<p>Vos coordonnées bancaires ont été remplacées. Les prochains remboursements seront versés sur ce compte.</p>"),
       expected="failed", rule="3.3.4/F1",
       notes="Submitting overwrites the stored refund account (user data with financial effect) at once; the new IBAN is not checked, reviewed or recoverable.",
       difficulty="hard")

    mk("it", "Comune di Esempiano", "Carta giornaliera Comune",
       "<p>Il Comune mette a disposizione ogni giorno quattro carte giornaliere per i trasporti pubblici al prezzo di CHF 45.– ciascuna.</p>",
       field("giorno", "Giorno di validità (GG.MM.AAAA)", err=False)
       + row(field("acquirente", "Nome e cognome", err=False), select("quante", "Numero di carte", ["1", "2", "3", "4"], err=False))
       + radios("ritiro", "Ritiro", ["Allo sportello", "Invio per posta"], checked=0),
       btn="Acquista", fid="carta-giornaliera",
       script=js_direct("carta-giornaliera", "ricevuta", {"q-giorno": "giorno"}),
       after=receipt("ricevuta", '<p>Acquisto registrato: carta giornaliera valida il <span id="q-giorno"></span>. Le carte giornaliere non sono rimborsabili né cambiabili.</p>'),
       expected="failed", rule="3.3.4/F1",
       notes="Non-refundable day passes are bought with one click on 'Acquista'; a wrong date cannot be reviewed, checked or corrected before the purchase is final.",
       difficulty="easy")

    mk("it", "Città di Modellina", "Rinuncia al posto all'asilo nido",
       "<p>Se non ha più bisogno del posto assegnato, ci comunichi la rinuncia: il posto verrà offerto alla famiglia successiva in lista d'attesa.</p>",
       field("bambino", "Nome e cognome del bambino", err=False)
       + field("dal", "Rinuncia a partire dal (GG.MM.AAAA)", err=False)
       + field("motivo", "Motivo (facoltativo)", textarea=True, rows=2, err=False),
       btn="Conferma la rinuncia", fid="rinuncia",
       script=js_direct("rinuncia", "ricevuta"),
       after=receipt("ricevuta", "<p>La rinuncia è stata registrata. Il posto sarà assegnato alla prossima famiglia in lista d'attesa.</p>"),
       expected="failed", rule="3.3.4/F1",
       notes="Giving up the daycare place (contract termination) takes effect on the first click despite the button text 'Conferma'; there is no real confirmation step or reversal.",
       difficulty="hard")

    docs = [("doc-1", "Contratto di locazione.pdf"), ("doc-2", "Certificato di salario 2025.pdf"),
            ("doc-3", "Polizza assicurazione economia domestica.pdf")]
    doclist = "".join(f'<div><input type="checkbox" id="{i}" name="documenti" value="{esc(n)}"> '
                      f'<label for="{i}" style="display:inline;font-weight:400">{esc(n)}</label></div>' for i, n in docs)
    mk("it", "Comune di Valfittizia", "I miei documenti",
       "<p>Qui trova i documenti che ha caricato per le sue richieste allo sportello online.</p>",
       f"<fieldset><legend>Documenti caricati</legend>{doclist}</fieldset>",
       btn="Elimina i documenti selezionati", fid="documenti-form",
       script=js_direct("documenti-form", "ricevuta"),
       after=receipt("ricevuta", "<p>I documenti selezionati sono stati eliminati definitivamente.</p>"),
       expected="failed", rule="3.3.4/F1",
       notes="Selected uploaded documents (user data in the portal) are deleted permanently on submit, with no confirmation request and no way to restore them.",
       difficulty="medium")

    mk("de", "Sportverein Beispielberg", "Anmeldung Skilager 2027",
       "<p>Das Skilager für Kinder von 8 bis 14 Jahren findet vom 15. bis 20. Februar 2027 statt. Kosten: CHF 280.– inkl. Unterkunft, Verpflegung und Skipass.</p>",
       row(field("kind", "Name des Kindes", err=False), field("jahrgang", "Jahrgang", err=False))
       + select("shirt", "Grösse Lager-T-Shirt", ["128", "140", "152", "164", "S", "M"], err=False)
       + field("notfall", "Notfallnummer der Eltern", type="tel", err=False),
       btn="Verbindlich anmelden", fid="skilager",
       script=js_direct("skilager", "quittung"),
       after=receipt("quittung", "<p>Die Anmeldung ist verbindlich. Die Rechnung über CHF 280.– folgt per E-Mail.</p>"),
       expected="failed", rule="3.3.4/F1",
       notes="Binding registration with a CHF 280.– fee is final with the first submit; no data check, summary, confirmation or cancellation window.",
       difficulty="easy")

    # =====================================================================
    # PASSED
    # =====================================================================
    mk("de", "Gemeinde Ober-Beispielwil", "Tageskarte Gemeinde reservieren",
       "<p>Pro Tag stehen vier Tageskarten zum Preis von CHF 45.– zur Verfügung. Reservierte Karten sind nicht rückerstattbar.</p>",
       field("reisetag", "Reisetag (TT.MM.JJJJ)", err=False)
       + row(field("besteller", "Vorname und Name", err=False), select("anzahl", "Anzahl Karten", ["1", "2", "3", "4"], err=False)),
       btn="Weiter zur Übersicht", fid="tageskarte",
       script=js_review("tageskarte", "uebersicht", "uebersicht-liste",
                        [("reisetag", "Reisetag"), ("besteller", "Name"), ("anzahl", "Anzahl Karten")],
                        "aendern", "reservieren", "quittung"),
       after=review_box("uebersicht", "uebersicht-liste", "aendern", "reservieren", "Bitte prüfen Sie Ihre Angaben",
                        "Erst mit «Kostenpflichtig reservieren» wird die Reservation verbindlich.",
                        "Angaben ändern", "Kostenpflichtig reservieren")
       + receipt("quittung", "<p>Ihre Tageskarten sind reserviert. Bitte holen Sie sie innert drei Tagen am Schalter ab.</p>"),
       expected="passed", rule="3.3.4/P1",
       notes="Submitting first shows a summary with 'Angaben ändern' and a separate 'Kostenpflichtig reservieren' button; the reservation only becomes binding after this review (G98).",
       difficulty="easy")

    mk("fr", "Commune de Valfictif", "Commander une attestation de domicile",
       "<p>L'attestation de domicile coûte CHF 20.–. Elle vous est envoyée par courrier avec un bulletin de versement.</p>",
       row(field("nom", "Nom", err=False), field("prenom", "Prénom", err=False))
       + field("naissance", "Date de naissance", hint="JJ.MM.AAAA", err=False)
       + select("nombre", "Nombre d'exemplaires", ["1", "2", "3"], err=False),
       btn="Continuer", fid="attestation",
       script=js_review("attestation", "recapitulatif", "recap-liste",
                        [("nom", "Nom"), ("prenom", "Prénom"), ("naissance", "Date de naissance"), ("nombre", "Exemplaires")],
                        "modifier", "commander", "recu"),
       after=review_box("recapitulatif", "recap-liste", "modifier", "commander", "Récapitulatif de votre commande",
                        "Vérifiez vos données. La commande devient définitive en cliquant sur « Commander (CHF 20.–) ».",
                        "Modifier", "Commander (CHF 20.–)")
       + receipt("recu", "<p>Merci, votre commande a été transmise.</p>"),
       expected="passed", rule="3.3.4/P1",
       notes="A recap step lists the entered data with 'Modifier' before the paid order is finalised with 'Commander (CHF 20.–)'.",
       difficulty="easy")

    mk("it", "Azienda acqua potabile Valfittizia", "Disdetta dell'allacciamento",
       "<p>In caso di demolizione o di cambiamento di proprietario, l'allacciamento all'acquedotto va disdetto per iscritto.</p>",
       field("proprietario", "Proprietario", err=False)
       + field("particella", "Numero della particella", err=False)
       + field("data-disdetta", "Data della disdetta (GG.MM.AAAA)", err=False)
       + '<div class="fld"><input type="checkbox" id="conferma" name="conferma" required> '
         '<label for="conferma" style="display:inline;font-weight:400">Confermo di voler disdire l\'allacciamento e prendo atto che la disdetta è definitiva dalla data indicata.</label></div>',
       btn="Invia la disdetta", fid="disdetta", novalidate=False,
       script=js_direct("disdetta", "ricevuta"),
       after=receipt("ricevuta", "<p>La disdetta è stata registrata.</p>"),
       expected="passed", rule="3.3.4/P2",
       notes="The termination can only be sent after ticking the required checkbox 'Confermo di voler disdire…' in addition to the submit button (G155).",
       difficulty="medium")

    mk("de", "Wasserversorgung Fiktal", "Kundenkonto löschen",
       "<p>Mit dem Löschen Ihres Kontos entfernen wir Ihre Zugangsdaten, gespeicherten Zählerstände und elektronischen Rechnungen.</p>",
       field("grund", "Möchten Sie uns den Grund mitteilen? (freiwillig)", textarea=True, rows=3, err=False),
       btn="Konto löschen", fid="kundenkonto",
       script=js_confirm("kundenkonto", "rueckfrage", "abbrechen", "endgueltig", "quittung"),
       after=dialog("rueckfrage", "Konto wirklich löschen?",
                    "Alle gespeicherten Zählerstände und Rechnungen werden unwiderruflich gelöscht.",
                    "abbrechen", "Abbrechen", "endgueltig", "Ja, Konto endgültig löschen")
       + receipt("quittung", "<p>Ihr Konto wurde gelöscht.</p>"),
       expected="passed", rule="3.3.4/P3",
       notes="Clicking 'Konto löschen' opens an in-page dialog asking 'Konto wirklich löschen?' with 'Abbrechen' and an explicit final button (G168).",
       difficulty="easy")

    mk("fr", "Commune d'Exempleval", "Commander le macaron de stationnement",
       "<p>Le macaron annuel pour la zone bleue coûte CHF 240.–. Il est envoyé par la poste avec la facture.</p>",
       field("plaque", "Numéro d'immatriculation", err=False)
       + field("adresse", "Adresse de domicile", err=False)
       + '<p class="box">Vous pouvez annuler ou modifier cette commande sans frais pendant 24 heures dans votre espace « Mes commandes ».</p>',
       btn="Commander (CHF 240.–)", fid="macaron",
       script=js_direct("macaron", "recu"),
       after=receipt("recu", '<p>Commande enregistrée. Pendant 24 heures, vous pouvez encore <a href="mes-commandes.html">l\'annuler ou la modifier sans frais</a> dans « Mes commandes ».</p>'),
       expected="passed", rule="3.3.4/T1", trap=True,
       notes="The paid order is single-step, but the page states that it can be cancelled or changed free of charge for 24 hours online (G164), so the submission is reversible.",
       difficulty="hard")

    mk("it", "Comune di Esempiano", "Eliminare il profilo dello sportello online",
       "<p>Il profilo contiene le sue richieste, i documenti caricati e le ricevute di pagamento.</p>"
       "<p>Dopo l'eliminazione il profilo resta disattivato per 30 giorni: entro questo termine può ripristinarlo completamente con il link che riceve per e-mail. Solo in seguito i dati vengono cancellati.</p>",
       field("motivo", "Motivo (facoltativo)", textarea=True, rows=2, err=False),
       btn="Elimina il profilo", fid="profilo",
       script=js_direct("profilo", "ricevuta"),
       after=receipt("ricevuta", '<p>Il profilo è stato disattivato. Fino al 13.11.2026 può <a href="ripristino.html">ripristinarlo</a>.</p>'),
       expected="passed", rule="3.3.4/T1", trap=True,
       notes="Deletion happens in one step, but the profile stays restorable for 30 days via a link (G99), so the action is reversible.",
       difficulty="hard")

    lsv_rules = [
        dict(f="kundennr", t=t_digits(8), m="Kundennummer: 8 Ziffern, siehe Rechnung oben rechts."),
        dict(f="inhaber", t=T_FILLED, m="Bitte geben Sie die Kontoinhaberin oder den Kontoinhaber an."),
        dict(f="iban", t=T_IBAN, m="IBAN: Schweizer IBAN mit 21 Zeichen, z. B. CH00 0000 0000 0000 0000 0."),
        dict(f="mail", t=T_EMAIL, m="E-Mail: Bitte im Format name@beispiel.ch eingeben."),
    ]
    mk("de", "Gemeinde Beispielwil", "Lastschriftverfahren für Wasser- und Abwassergebühren",
       "<p>Mit dem Lastschriftverfahren (LSV) werden die Gebühren automatisch von Ihrem Konto abgebucht.</p>",
       field("kundennr", "Kundennummer", im="numeric")
       + field("inhaber", "Kontoinhaberin / Kontoinhaber")
       + field("iban", "IBAN")
       + field("mail", "E-Mail für Belastungsanzeigen", type="email"),
       btn="Lastschrift einrichten", fid="lastschrift", mode="validate", rules=lsv_rules, script="",
       expected="passed", rule="3.3.4/T2", trap=True,
       notes="No review step, but every entered value (customer number, holder, IBAN, e-mail) is checked and the user can correct errors before the debit order is sent ('Checked' option).",
       difficulty="hard")

    mk("de", "Gemeinde Fiktal", "Grillstelle am See reservieren",
       "<p>Die Grillstelle beim Badeplatz kann kostenlos für einen halben Tag reserviert werden.</p>",
       row(field("datum", "Datum (TT.MM.JJJJ)", err=False),
           select("halbtag", "Zeit", ["Vormittag 9–14 Uhr", "Nachmittag/Abend 15–22 Uhr"], err=False))
       + field("gruppe", "Name / Gruppe", err=False)
       + '<p class="muted">Reservationen können Sie bis am Vortag, 12.00 Uhr, über den Link in der Bestätigung kostenlos ändern oder stornieren.</p>',
       btn="Reservieren", fid="grillstelle",
       script=js_direct("grillstelle", "quittung"),
       after=receipt("quittung", '<p>Die Grillstelle ist für Sie reserviert. <a href="reservation-aendern.html">Reservation ändern oder stornieren</a> (bis am Vortag, 12.00 Uhr).</p>'),
       expected="passed", rule="3.3.4/T1", trap=True,
       notes="One-step reservation, but the page states that it can be changed or cancelled online until noon the day before (G164).",
       difficulty="medium")

    mk("fr", "Ville de Bourg-Modèle", "Signaler un nid-de-poule",
       "<p>Vous avez remarqué un trou dans la chaussée ? Signalez-le à la voirie.</p>",
       field("lieu", "Lieu (rue, numéro le plus proche)", err=False)
       + field("description", "Description", textarea=True, rows=3, err=False),
       btn="Envoyer le signalement", fid="signalement",
       script=js_direct("signalement", "recu"),
       after=receipt("recu", "<p>Merci pour votre signalement. La voirie interviendra dès que possible.</p>"),
       expected="inapplicable", rule="3.3.4/N1", trap=True,
       notes="A pothole report creates no legal commitment or financial transaction and modifies no stored user data, so direct submission is out of scope.",
       difficulty="medium")

    mk("it", "Biblioteca di Modellina", "Sondaggio sugli orari di apertura",
       "<p>Stiamo valutando nuovi orari. Ci dica quando preferisce venire in biblioteca: bastano due minuti.</p>",
       radios("preferenza", "Quando viene più volentieri?", ["Mattina", "Pomeriggio", "Sera dopo le 18.00", "Sabato"])
       + field("commento", "Commento (facoltativo)", textarea=True, rows=2, err=False),
       btn="Invia la risposta", fid="sondaggio",
       script=js_direct("sondaggio", "ricevuta"),
       after=receipt("ricevuta", "<p>Grazie per la sua partecipazione!</p>"),
       expected="inapplicable", rule="3.3.4/N1", trap=True,
       notes="An anonymous opinion poll creates no commitment, payment or change to stored user data; the criterion does not apply.",
       difficulty="medium")

    # =====================================================================
    # CANTTELL
    # =====================================================================
    mk("de", "Gemeinde Beispielberg", "Kurs «Erste Hilfe bei Kindern»",
       "<p>Der Kurs ist für Eltern aus Beispielberg kostenlos. Bei unentschuldigtem Fernbleiben verrechnen wir eine Umtriebsentschädigung von CHF 30.–.</p>",
       row(field("teilnehmer", "Vorname und Name", err=False), field("telefon", "Telefon", type="tel", err=False))
       + select("kursdatum", "Kursdatum", ["Samstag, 16. Januar 2027", "Samstag, 20. Februar 2027"], err=False),
       btn="Anmelden", fid="kurs",
       script=js_direct("kurs", "quittung"),
       after=receipt("quittung", "<p>Sie sind angemeldet. Wir freuen uns auf Ihre Teilnahme.</p>"),
       expected="cantTell", rule="3.3.4/C1",
       notes="Free course registration that only costs CHF 30.– on unexcused absence; whether this is a legal/financial commitment in scope of 3.3.4 cannot be decided from the page.",
       difficulty="hard")

    mk("fr", "Commune de Valfictif", "Réserver une salle de réunion",
       "<p>Les salles de réunion de la maison de commune sont mises gratuitement à disposition des sociétés locales. Annulation gratuite jusqu'à 48 heures avant ; ensuite, un forfait de CHF 50.– est facturé. Les annulations se font par téléphone.</p>",
       field("societe", "Société", err=False)
       + row(field("date-salle", "Date (JJ.MM.AAAA)", err=False), select("salle", "Salle", ["Salle du Conseil (20 places)", "Petite salle (8 places)"], err=False)),
       btn="Réserver", fid="salle-reunion",
       script=js_direct("salle-reunion", "recu"),
       after=receipt("recu", "<p>Votre réservation est enregistrée.</p>"),
       expected="cantTell", rule="3.3.4/C1",
       notes="Free room booking that becomes chargeable (CHF 50.–) only for late cancellation by phone; whether it counts as a financial/legal commitment needing review is debatable.",
       difficulty="hard")

    mk("it", "Comune di Valfittizia", "Addebito diretto per la tassa rifiuti",
       "<p>Con l'addebito diretto la tassa base sui rifiuti viene addebitata automaticamente sul suo conto. L'autorizzazione può essere revocata in qualsiasi momento.</p>",
       field("titolare", "Titolare del conto", err=False)
       + field("iban", "IBAN", err=False),
       btn="Autorizza l'addebito", fid="addebito",
       script=js_direct("addebito", "ricevuta"),
       after=receipt("ricevuta", "<p>L'autorizzazione all'addebito diretto è stata registrata.</p>"),
       expected="cantTell", rule="3.3.4/C2",
       notes="The debit authorization is final on submit; the page only asserts it 'può essere revocata in qualsiasi momento' without mechanism or time frame, so reversibility cannot be verified.",
       difficulty="hard")

    mk("de", "Gemeinde Ober-Beispielwil", "Hundetaxe online bezahlen",
       "<p>Bezahlen Sie die Hundetaxe 2027 bequem online. Sie benötigen die Rechnungsnummer aus dem Schreiben der Gemeinde.</p>",
       field("rechnung", "Rechnungsnummer", err=False)
       + '<p>Betrag: <strong>CHF 120.–</strong></p>',
       btn="Weiter zur Zahlung", fid="hundetaxe", mode="none", action="/epayment/start", script="",
       novalidate=False,
       expected="cantTell", rule="3.3.4/C3",
       notes="The form only hands over to an external payment step ('Weiter zur Zahlung' posting to /epayment/start); whether the payment is reviewed or confirmed there cannot be observed.",
       difficulty="medium")

    return shuffled(rng, cases)
