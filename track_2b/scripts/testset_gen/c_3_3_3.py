"""3.3.3 Error Suggestion -- 26 cases, target = the form field under test.

Same conventions as 3.3.1: labels describe the state after submitting the value given
in ``notes`` (other fields valid). Messages always identify the field (3.3.1 met), so
only the presence of a correction suggestion is judged. Rules: protocol fragment 3.3.3.
"""
from __future__ import annotations

from common import *
from _forms_util import (field, select, fieldset, row, contact_aside, form_case,
                         T_PLZ, T_EMAIL, T_AHV, T_DATE, T_FILLED, T_PLATE, T_PHONE, T_IBAN,
                         t_digits, t_range, t_oneof)

CRITERION = "3.3.3"

# "Did you mean ...?" suggestion computed with a tiny edit distance (G177)
_COMUNI = ["Esempiano", "Modellina", "Valfittizia"]
MF_COMUNE = (
    "(function(){var L=[\"Esempiano\",\"Modellina\",\"Valfittizia\"];"
    "function d(a,b){a=a.toLowerCase();b=b.toLowerCase();var p=[],i,j;for(j=0;j<=b.length;j++){p[j]=j;}"
    "for(i=1;i<=a.length;i++){var q=[i];for(j=1;j<=b.length;j++){q[j]=Math.min(p[j]+1,q[j-1]+1,p[j-1]+(a[i-1]===b[j-1]?0:1));}p=q;}"
    "return p[b.length];}"
    "var best=L[0];L.forEach(function(c){if(d(v,c)<d(v,best)){best=c;}});"
    "return \"Comune di domicilio: comune non trovato. Intendeva «\"+best+\"»? Sono ammessi solo i comuni del consorzio: Esempiano, Modellina e Valfittizia.\";})()"
)


def build(rng):
    cases = []

    def mk(*a, **k):
        cases.append(form_case(rng, CRITERION, *a, **k))

    # =====================================================================
    # FAILED
    # =====================================================================
    mk("de", "Gemeinde Beispielwil", "Fundbüro: Verlust melden",
       "<p>Haben Sie etwas verloren? Beschreiben Sie den Gegenstand möglichst genau. Wir melden uns, sobald ein passender Fund abgegeben wird.</p>",
       field("gegenstand", "Verlorener Gegenstand", textarea=True, rows=3)
       + row(field("vorname", "Vorname", ac="given-name"), field("name", "Name", ac="family-name"))
       + row(field("plz", "PLZ", im="numeric", ac="postal-code", size=6), field("ort", "Ort", ac="address-level2"))
       + field("email", "E-Mail", type="email", ac="email"),
       [dict(f="gegenstand", t=T_FILLED, m="Bitte beschreiben Sie den verlorenen Gegenstand."),
        dict(f="vorname", t=T_FILLED, m="Bitte geben Sie Ihren Vornamen ein."),
        dict(f="name", t=T_FILLED, m="Bitte geben Sie Ihren Namen ein."),
        dict(f="plz", t=T_PLZ, m="PLZ: ungültige Eingabe."),
        dict(f="ort", t=T_FILLED, m="Bitte geben Sie Ihren Wohnort ein."),
        dict(f="email", t=T_EMAIL, m="E-Mail: Bitte im Format name@beispiel.example eingeben.")],
       fid="fundbuero", target="#plz", expected="failed", rule="3.3.3/F1",
       notes="For PLZ '301' the page answers 'PLZ: ungültige Eingabe.' although the rule (exactly 4 digits) is known to the script; no format or example is suggested.",
       difficulty="easy")

    mk("de", "Schule Beispielberg", "Urlaubsgesuch für Schülerinnen und Schüler",
       "<p>Für bis zu zwei Jokertage brauchen Sie kein Gesuch. Längere Abwesenheiten beantragen Sie mindestens zwei Wochen im Voraus bei der Schulleitung.</p>",
       row(field("kind", "Name des Kindes"), field("klasse", "Klasse", size=6))
       + row(field("erster", "Erster Urlaubstag"), field("tage", "Anzahl Schultage", im="numeric", size=4))
       + field("grund", "Begründung", textarea=True, rows=3),
       [dict(f="kind", t=T_FILLED, m="Bitte geben Sie den Namen des Kindes ein."),
        dict(f="klasse", t=T_FILLED, m="Bitte geben Sie die Klasse an, z. B. 4b."),
        dict(f="erster", t=T_DATE, m="Erster Urlaubstag: Datum ungültig."),
        dict(f="tage", t=t_range(1, 10), m="Anzahl Schultage: Bitte eine Zahl von 1 bis 10 eingeben."),
        dict(f="grund", t=T_FILLED, m="Bitte begründen Sie das Gesuch in einigen Worten.")],
       fid="urlaub", target="#erster", expected="failed", rule="3.3.3/F1",
       notes="Entering '3.11.26' yields 'Erster Urlaubstag: Datum ungültig.'; the expected format TT.MM.JJJJ is known but neither stated in the message nor anywhere next to the field.",
       difficulty="medium")

    mk("de", "Gemeinde Fiktal", "Auszahlung des Vereinsbeitrags 2026",
       "<p>Ortsvereine mit Jugendabteilung erhalten einen Beitrag von CHF 30.– pro aktivem Kind. Der Betrag wird im Dezember überwiesen.</p>",
       field("verein", "Name des Vereins")
       + field("inhaber", "Kontoinhaberin / Kontoinhaber")
       + field("iban", "IBAN")
       + field("kinder", "Anzahl Kinder und Jugendliche", im="numeric", size=5),
       [dict(f="verein", t=T_FILLED, m="Bitte geben Sie den Namen des Vereins ein."),
        dict(f="inhaber", t=T_FILLED, m="Bitte geben Sie an, auf wen das Konto lautet."),
        dict(f="iban", t=T_IBAN, m="IBAN fehlerhaft."),
        dict(f="kinder", t=t_range(1, 500), m="Bitte geben Sie die Anzahl als ganze Zahl ein, z. B. 24.")],
       fid="beitrag", target="#iban", expected="failed", rule="3.3.3/F1",
       notes="For IBAN 'CH93 0076 2011 6238 5295' (one digit short) the message 'IBAN fehlerhaft.' gives no hint that a Swiss IBAN has 21 characters (CH + 19 digits).",
       difficulty="medium")

    mk("fr", "Commune de Valfictif", "Subvention à l'abonnement de bus des apprentis",
       "<p>La commune prend en charge 30 % de l'abonnement annuel des apprentis domiciliés à Valfictif. Joignez une copie du contrat d'apprentissage.</p>",
       row(field("nom", "Nom", ac="family-name"), field("prenom", "Prénom", ac="given-name"))
       + field("avs", "Numéro AVS")
       + field("entreprise", "Entreprise formatrice"),
       [dict(f="nom", t=T_FILLED, m="Veuillez indiquer votre nom."),
        dict(f="prenom", t=T_FILLED, m="Veuillez indiquer votre prénom."),
        dict(f="avs", t=T_AHV, m="Numéro AVS invalide."),
        dict(f="entreprise", t=T_FILLED, m="Veuillez indiquer le nom de l'entreprise formatrice.")],
       fid="subvention", target="#avs", expected="failed", rule="3.3.3/F1",
       notes="Entering '7561234567897' (13 digits without points) returns 'Numéro AVS invalide.'; the required notation 756.0000.0000.00 is known but not suggested.",
       difficulty="hard")

    mk("fr", "Club sportif d'Exempleval", "Inscription au camp de ski",
       "<p>Le camp a lieu du 15 au 20 février 2027 aux Mayens-Modèle pour les enfants de 8 à 14 ans. Prix : CHF 320.– tout compris.</p>",
       row(field("enfant", "Nom et prénom de l'enfant"), field("naissance", "Date de naissance"))
       + select("niveau", "Niveau de ski", ["Débutant", "Moyen", "Avancé"], err=False)
       + field("courriel", "Courriel des parents", type="email", ac="email"),
       [dict(f="enfant", t=T_FILLED, m="Indiquez le nom et le prénom de l'enfant."),
        dict(f="naissance", t=T_DATE, m="Date de naissance non valable."),
        dict(f="courriel", t=T_EMAIL, m="Courriel : saisissez une adresse du type nom@exemple.example.")],
       fid="camp", target="#naissance", expected="failed", rule="3.3.3/F1",
       notes="For '2019-04-12' the message 'Date de naissance non valable.' does not mention the expected JJ.MM.AAAA format, which the script enforces.",
       difficulty="medium")

    mk("fr", "Association intercommunale de la déchetterie", "Carte d'accès à la déchetterie",
       "<p>La déchetterie intercommunale est réservée aux habitants des communes membres. La carte d'accès est gratuite et envoyée par la poste.</p>",
       row(field("nom", "Nom et prénom", ac="name"), field("rue", "Rue et numéro", ac="street-address"))
       + field("commune", "Commune de domicile")
       + field("plaque", "Plaque du véhicule (facultatif)", err=False),
       [dict(f="nom", t=T_FILLED, m="Indiquez votre nom et votre prénom."),
        dict(f="rue", t=T_FILLED, m="Indiquez votre rue et votre numéro."),
        dict(f="commune", t=t_oneof(["Valfictif", "Exempleval", "Bourg-Modèle", "Beispielwil"]), m="Commune inconnue.")],
       fid="dechetterie", target="#commune", expected="failed", rule="3.3.3/F2",
       notes="Typing 'Valfictiff' returns 'Commune inconnue.'; the script knows the four member communes but neither lists them nor proposes 'Valfictif'.",
       difficulty="hard")

    mk("it", "Comune di Esempiano", "Servizio pasti a domicilio",
       "<p>Il servizio consegna un pasto caldo a mezzogiorno alle persone anziane o convalescenti. Prezzo: CHF 14.– per pasto.</p>",
       field("persona", "Nome e cognome", ac="name")
       + field("via", "Via e numero civico", ac="street-address")
       + field("telefono", "Telefono", type="tel", ac="tel")
       + field("note", "Diete o allergie", textarea=True, rows=2, err=False),
       [dict(f="persona", t=T_FILLED, m="Indichi nome e cognome."),
        dict(f="via", t=T_FILLED, m="Indichi via e numero civico per la consegna."),
        dict(f="telefono", t=T_PHONE, m="Numero di telefono errato.")],
       fid="pasti", target="#telefono", expected="failed", rule="3.3.3/F1",
       notes="For '091 000 12' (two digits missing) the reply is 'Numero di telefono errato.'; the expected 10-digit format is known but not suggested.",
       difficulty="medium")

    mk("it", "Comune di Valfittizia", "Ordinare sacchi tassati supplementari",
       "<p>Le famiglie con bambini fino a tre anni ricevono gratuitamente 20 sacchi supplementari all'anno. Indichi il formato desiderato.</p>",
       field("famiglia", "Cognome della famiglia")
       + field("formato", "Formato del sacco (litri)", size=8)
       + field("bambino", "Anno di nascita del bambino", im="numeric", size=6),
       [dict(f="famiglia", t=T_FILLED, m="Indichi il cognome della famiglia."),
        dict(f="formato", t=t_oneof(["17", "35", "60", "110"], strip_suffix=r"/\s*(l|litri)$/"), m="Formato del sacco: formato non disponibile."),
        dict(f="bambino", t=r"/^20(2[3-6])$/.test(v)", m="Anno di nascita: indichi un anno tra 2023 e 2026.")],
       fid="sacchi-extra", target="#formato", expected="failed", rule="3.3.3/F2",
       notes="Entering '50 litri' gives 'formato non disponibile.'; the allowed sizes (17, 35, 60, 110 l) are known to the script but not listed.",
       difficulty="medium")

    mk("it", "Città di Modellina", "Permesso di parcheggio per artigiani",
       "<p>Il permesso consente agli artigiani di sostare fino a quattro ore nelle zone blu durante gli interventi presso i clienti. Costo: CHF 50.– al mese.</p>",
       field("ditta", "Ditta")
       + field("targa", "Targa del veicolo")
       + select("durata", "Durata", ["1 mese", "3 mesi", "6 mesi", "12 mesi"], err=False),
       [dict(f="ditta", t=T_FILLED, m="Indichi il nome della ditta."),
        dict(f="targa", t=T_PLATE, m="Targa non valida.")],
       fid="artigiani", target="#targa", expected="failed", rule="3.3.3/F1",
       notes="For 'TI12345 6' the message 'Targa non valida.' does not say that a plate is two letters followed by up to six digits.",
       difficulty="medium")

    mk("de", "Gemeinde Ober-Beispielwil", "Anmeldung Mittagstisch",
       "<p>Der Mittagstisch ist an den Schultagen Montag, Dienstag und Donnerstag geöffnet. Ein Mittagessen kostet CHF 12.–.</p>",
       row(field("kind", "Vorname und Name des Kindes"), field("klasse", "Klasse", size=6))
       + field("schulhaus", "Schulhaus")
       + field("mail", "E-Mail der Eltern", type="email", ac="email"),
       [dict(f="kind", t=T_FILLED, m="Bitte geben Sie Vorname und Name des Kindes ein."),
        dict(f="klasse", t=T_FILLED, m="Bitte geben Sie die Klasse an, z. B. 2a."),
        dict(f="schulhaus", t=t_oneof(["Dorfmatt", "Schachen", "Oberfeld"]), m="Schulhaus nicht gefunden."),
        dict(f="mail", t=T_EMAIL, m="E-Mail: Bitte eine Adresse im Format name@beispiel.example eingeben.")],
       fid="mittagstisch", target="#schulhaus", expected="failed", rule="3.3.3/F2",
       notes="Typing 'Dorf' returns 'Schulhaus nicht gefunden.'; the three valid school buildings are known to the script but not proposed.",
       difficulty="medium")

    # =====================================================================
    # PASSED
    # =====================================================================
    mk("de", "Gemeinde Fiktal", "Gedruckten Abfallkalender bestellen",
       "<p>Der Abfallkalender 2027 erscheint Mitte Dezember. Haushalte ohne Internet erhalten ihn auf Wunsch kostenlos per Post.</p>",
       field("name", "Vorname und Name", ac="name")
       + field("strasse", "Strasse und Hausnummer", ac="street-address")
       + row(field("plz", "PLZ", im="numeric", ac="postal-code", size=6), field("ort", "Ort", ac="address-level2")),
       [dict(f="name", t=T_FILLED, m="Bitte geben Sie Vorname und Name ein."),
        dict(f="strasse", t=T_FILLED, m="Bitte geben Sie Strasse und Hausnummer ein."),
        dict(f="plz", t=T_PLZ, m="Die PLZ besteht aus 4 Ziffern, z. B. 3011."),
        dict(f="ort", t=T_FILLED, m="Bitte geben Sie den Ort ein.")],
       fid="kalender", target="#plz", expected="passed", rule="3.3.3/P1",
       notes="For PLZ '30111' the message 'Die PLZ besteht aus 4 Ziffern, z. B. 3011.' states the format and an example.",
       difficulty="easy")

    mk("fr", "Ville de Bourg-Modèle", "Demande d'allocation de naissance communale",
       "<p>La Ville verse une allocation unique de CHF 500.– pour chaque enfant né ou adopté dont un parent est domicilié à Bourg-Modèle.</p>",
       row(field("parent", "Nom et prénom du parent"), field("enfant", "Prénom de l'enfant"))
       + field("avs", "Numéro AVS du parent")
       + field("naissance", "Date de naissance de l'enfant")
       + field("iban", "IBAN pour le versement"),
       [dict(f="parent", t=T_FILLED, m="Indiquez le nom et le prénom du parent."),
        dict(f="enfant", t=T_FILLED, m="Indiquez le prénom de l'enfant."),
        dict(f="avs", t=T_AHV, m="Le numéro AVS comporte 13 chiffres et commence par 756. Saisissez-le avec les points : 756.0000.0000.00."),
        dict(f="naissance", t=T_DATE, m="Date de naissance : utilisez le format JJ.MM.AAAA, p. ex. 02.09.2026."),
        dict(f="iban", t=T_IBAN, m="IBAN : un IBAN suisse compte 21 caractères, p. ex. CH00 0000 0000 0000 0000 0.")],
       fid="allocation", target="#avs", expected="passed", rule="3.3.3/P1",
       notes="Entering '7561234567897' produces a message stating the 13 digits, the 756 prefix and the notation 756.0000.0000.00.",
       difficulty="easy")

    mk("it", "Biblioteca di Modellina", "Tessera della biblioteca per bambini",
       "<p>La tessera è gratuita fino a 16 anni. Per i bambini sotto i 12 anni la richiesta va fatta da un genitore.</p>",
       field("bambino", "Nome e cognome del bambino")
       + field("nascita", "Data di nascita")
       + field("email", "E-mail del genitore", type="email", ac="email"),
       [dict(f="bambino", t=T_FILLED, m="Indichi nome e cognome del bambino."),
        dict(f="nascita", t=T_DATE, m="Data di nascita: inserire la data nel formato GG.MM.AAAA, ad esempio 05.03.2019."),
        dict(f="email", t=T_EMAIL, m="E-mail: inserisca un indirizzo completo, ad es. nome@esempio.example.")],
       fid="tessera", target="#nascita", expected="passed", rule="3.3.3/P1",
       notes="For '5/3/2019' the message gives the expected format GG.MM.AAAA and an example date.",
       difficulty="easy")

    mk("fr", "Commune d'Exempleval", "Commande de sacs taxés",
       "<p>Les sacs taxés sont livrés à domicile par rouleaux de dix. La facture suit avec la livraison.</p>",
       field("client", "Nom et adresse")
       + row(field("taille", "Taille des sacs (litres)", size=8), field("rouleaux", "Nombre de rouleaux", im="numeric", size=4)),
       [dict(f="client", t=T_FILLED, m="Indiquez votre nom et votre adresse."),
        dict(f="taille", t=t_oneof(["17", "35", "60", "110"], strip_suffix=r"/\s*(l|litres)$/"),
             m="Taille des sacs : les tailles disponibles sont 17, 35, 60 et 110 litres."),
        dict(f="rouleaux", t=t_range(1, 10), m="Nombre de rouleaux : entre 1 et 10.")],
       fid="sacs", target="#taille", expected="passed", rule="3.3.3/P2",
       notes="For '50' the message lists the allowed sizes '17, 35, 60 et 110 litres'.",
       difficulty="easy")

    mk("it", "Consorzio raccolta rifiuti Esempiano-Modellina", "Tessera per l'ecocentro",
       "<p>L'ecocentro consortile è riservato alle economie domestiche dei comuni del consorzio. La tessera è gratuita.</p>",
       field("nominativo", "Nome e cognome", ac="name")
       + field("comune", "Comune di domicilio")
       + field("via", "Via e numero", ac="street-address"),
       [dict(f="nominativo", t=T_FILLED, m="Indichi nome e cognome."),
        dict(f="comune", t=t_oneof(_COMUNI), m="", mf=MF_COMUNE),
        dict(f="via", t=T_FILLED, m="Indichi via e numero civico.")],
       fid="ecocentro", target="#comune", expected="passed", rule="3.3.3/P3",
       notes="Typing 'Valfitizia' produces 'Comune non trovato. Intendeva «Valfittizia»?' plus the list of admitted communes (computed suggestion, G177).",
       difficulty="medium")

    # Traps: exceptions
    login_inner = (field("benutzer", "Benutzername", ac="username")
                   + field("kennwort", "Kennwort", type="password", ac="current-password"))
    cases.append(form_case(
        rng, CRITERION, "de", "Wasserversorgung Fiktal", "Anmelden im Kundenportal",
        "<p>Im Kundenportal sehen Sie Ihre Rechnungen und können Zählerstände melden.</p>",
        '<p class="msgbox" id="login-msg" role="alert" hidden></p>' + login_inner
        + '<p><a href="kennwort-vergessen.html">Kennwort vergessen?</a></p>',
        [dict(f="benutzer", t=T_FILLED, m="Bitte geben Sie Ihren Benutzernamen ein."),
         dict(f="kennwort", t="false", m="Benutzername oder Kennwort ist falsch. Bitte versuchen Sie es erneut.",
              x="login-msg")],
        btn="Anmelden", fid="login", target="#kennwort", expected="passed", rule="3.3.3/T1", trap=True,
        notes="Any combination, e.g. 'Sommer2026' with user 'reto.muster', returns 'Benutzername oder Kennwort ist falsch.'; suggesting the right password would jeopardize security.",
        difficulty="medium"))

    mk("fr", "Commune de Valfictif", "Accès à votre déclaration d'impôt en ligne",
       "<p>Saisissez le numéro de contribuable et le code d'accès personnel figurant sur la lettre accompagnant votre déclaration.</p>",
       field("contribuable", "Numéro de contribuable", im="numeric",
             hint="9 chiffres, en haut à droite de la lettre, p. ex. 123456789.")
       + field("code", "Code d'accès personnel", ac="off"),
       [dict(f="contribuable", t=t_digits(9), m="Numéro de contribuable : saisissez les 9 chiffres sans espaces, p. ex. 123456789."),
        dict(f="code", t="false", m="Code d'accès incorrect. Il vous reste 2 essais.")],
       btn="Accéder", fid="acces-impot", target="#code", expected="passed", rule="3.3.3/T1", trap=True,
       notes="Any wrong access code (e.g. 'K7P-22Q') is answered 'Code d'accès incorrect. Il vous reste 2 essais.' without hints; the security exception applies.",
       difficulty="medium")

    mk("it", "Scuola di Esempiano", "Quiz di educazione stradale – 4a elementare",
       "<p>Rispondi alle tre domande scrivendo un numero. Se sbagli puoi riprovare: la maestra ti spiegherà le risposte in classe.</p>",
       field("d1", "1. Quante luci deve avere almeno la bicicletta quando è buio?", im="numeric", size=4)
       + field("d2", "2. Fino a quanti anni i bambini possono pedalare sul marciapiede in assenza di pista ciclabile?", im="numeric", size=4)
       + field("d3", "3. Quante mani devi tenere sul manubrio quando non segnali una svolta?", im="numeric", size=4),
       [dict(f="d1", t='v === "2"', m="Domanda 1: risposta errata, riprova."),
        dict(f="d2", t='v === "12"', m="Domanda 2: risposta errata, riprova."),
        dict(f="d3", t='v === "2"', m="Domanda 3: risposta errata, riprova.")],
       btn="Controlla le risposte", fid="quiz", target="#d2", expected="passed", rule="3.3.3/T2", trap=True,
       notes="For answer '10' to question 2 the quiz only says 'risposta errata, riprova.'; giving the right answer would defeat the purpose of the test.",
       difficulty="hard")

    mk("de", "Gemeinde Beispielberg", "Kontakt zur Gemeindeverwaltung",
       "<p>Schreiben Sie uns. Wir antworten in der Regel innert zwei Arbeitstagen.</p>",
       row(field("name", "Ihr Name", ac="name"), field("mail", "E-Mail", type="email", ac="email"))
       + field("nachricht", "Nachricht", textarea=True, rows=5)
       + field("kontrolle", "Kontrollfrage zum Spamschutz: Wie viel ist drei plus vier?", im="numeric", size=4),
       [dict(f="name", t=T_FILLED, m="Bitte geben Sie Ihren Namen ein."),
        dict(f="mail", t=T_EMAIL, m="E-Mail: Bitte im Format name@beispiel.example eingeben."),
        dict(f="nachricht", t=T_FILLED, m="Bitte schreiben Sie uns eine Nachricht."),
        dict(f="kontrolle", t='v === "7"', m="Die Antwort auf die Kontrollfrage stimmt nicht.")],
       fid="kontakt", target="#kontrolle", expected="passed", rule="3.3.3/T1", trap=True,
       notes="Answering '8' to the anti-spam question returns 'Die Antwort auf die Kontrollfrage stimmt nicht.'; revealing the answer would defeat the spam protection (security exception).",
       difficulty="hard")

    mk("fr", "Service des eaux d'Exempleval", "Changement d'adresse de facturation",
       "<p>Vous déménagez ou souhaitez recevoir la facture d'eau à une autre adresse ? Indiquez-nous la nouvelle adresse de facturation.</p>",
       field("client", "Numéro de client", im="numeric")
       + field("adresse", "Nouvelle adresse (rue et numéro)", ac="street-address")
       + row(field("npa", "NPA", im="numeric", size=6), field("localite", "Localité")),
       [dict(f="client", t=t_digits(8), m="N° de client : 8 chiffres, voir facture."),
        dict(f="adresse", t=T_FILLED, m="Adresse manquante."),
        dict(f="npa", t=T_PLZ, m="NPA : 4 chiffres, p. ex. 2000."),
        dict(f="localite", t=T_FILLED, m="Localité manquante.")],
       fid="facturation", target="#npa", expected="passed", rule="3.3.3/T3", trap=True,
       notes="For NPA '20000' the short message 'NPA : 4 chiffres, p. ex. 2000.' still contains the format and an example.",
       difficulty="medium")

    # Inapplicable: no automatic error detection
    mk("de", "Stadt Mustersee", "Ihre Meinung zur neuen Website",
       "<p>Seit September ist unsere Website neu gestaltet. Was gefällt Ihnen, was fehlt? Alle Angaben sind freiwillig und anonym.</p>",
       field("gefallen", "Was gefällt Ihnen?", textarea=True, rows=3, err=False)
       + field("verbessern", "Was können wir verbessern?", textarea=True, rows=3, err=False)
       + select("haeufig", "Wie oft besuchen Sie unsere Website?", ["täglich", "wöchentlich", "monatlich", "seltener"], err=False, first="Bitte wählen"),
       mode="native", btn="Feedback senden",
       fid="feedback", target="#verbessern", expected="inapplicable", rule="3.3.3/N1",
       notes="All fields are optional free text or a select; nothing is checked, so no input error is ever detected automatically.",
       difficulty="medium")

    mk("it", "Comune di Esempiano", "Un nome per il nuovo parco giochi",
       "<p>Il nuovo parco giochi in Via ai Monti sarà inaugurato in primavera. Proponete un nome: la giuria dei bambini sceglierà il migliore.</p>",
       field("proposta", "La tua proposta", err=False)
       + field("motivazione", "Perché questo nome? (facoltativo)", textarea=True, rows=3, err=False),
       mode="native", btn="Invia la proposta",
       fid="parco", target="#proposta", expected="inapplicable", rule="3.3.3/N1",
       notes="Free-text name proposal without any constraint or script check: no input error can be detected, so the criterion does not apply.",
       difficulty="medium")

    # =====================================================================
    # CANTTELL
    # =====================================================================
    mk("de", "Gemeinde Beispielberg", "Verein im Vereinsverzeichnis eintragen",
       "<p>Das Vereinsverzeichnis auf der Gemeindewebsite ist für Vereine mit Sitz in Beispielberg kostenlos.</p>",
       '<div class="msgbox" role="alert"><p>Ihre Angaben konnten nicht gespeichert werden. Bitte prüfen Sie das markierte Feld.</p></div>'
       + field("vereinsname", "Name des Vereins", value="FC Beispielberg Senioren",
               extra='aria-invalid="true" class="is-invalid"',
               err_text="Dieser Vereinsname kann nicht verwendet werden.")
       + field("kontakt", "Kontaktperson", value="Beat Vorlage", err=False)
       + field("vmail", "E-Mail des Vereins", type="email", value="info@fc-senioren.example", err=False),
       mode="none", action="/vereine/eintrag", novalidate=False, btn="Erneut senden",
       fid="vereinsverzeichnis", target="#vereinsname", expected="cantTell", rule="3.3.3/C1",
       notes="Server re-rendered form: 'FC Beispielberg Senioren' was rejected with 'Dieser Vereinsname kann nicht verwendet werden.'; the rule (duplicate? reserved word?) is not visible, so whether a suggestion is known cannot be decided.",
       difficulty="hard")

    mk("fr", "Commune de Bourg-Modèle", "Créer un compte sur le guichet virtuel",
       "<p>Le guichet virtuel vous permet de commander des documents et de suivre vos demandes en ligne.</p>",
       '<div class="msgbox" role="alert"><p>Le compte n\'a pas pu être créé.</p></div>'
       + field("utilisateur", "Nom d'utilisateur", value="claire.exemple",
               extra='aria-invalid="true" class="is-invalid"',
               err_text="Ce nom d'utilisateur n'est pas disponible.")
       + field("courriel", "Courriel", type="email", value="claire@exemple.example", err=False),
       mode="none", action="/guichet/compte", novalidate=False, btn="Créer le compte",
       fid="compte", target="#utilisateur", expected="cantTell", rule="3.3.3/C1",
       notes="After server validation the user name 'claire.exemple' is rejected as 'non disponible'; whether alternative names are 'known' suggestions depends on server data not visible on the page.",
       difficulty="hard")

    mk("it", "Comune di Esempiano", "Contributo per i pannolini",
       "<p>Le famiglie con bambini fino a due anni ricevono un contributo di CHF 120.– all'anno per i sacchi supplementari. Il versamento avviene sul conto indicato.</p>",
       field("richiedente", "Nome e cognome del richiedente")
       + field("iban", "IBAN", hint="Formato: CH00 0000 0000 0000 0000 0 (21 caratteri)"),
       [dict(f="richiedente", t=T_FILLED, m="Indichi nome e cognome del richiedente."),
        dict(f="iban", t=T_IBAN, m="IBAN non valido.")],
       fid="pannolini", target="#iban", expected="cantTell", rule="3.3.3/C2",
       notes="For 'CH93 0076 2011 6238 5295' the message is only 'IBAN non valido.', but the visible format hint (aria-describedby) stays right under the field; whether that counts as a suggestion is disputed.",
       difficulty="hard")

    mk("de", "Bibliothek Mustersee", "Gruppenraum reservieren",
       "<p>Der Gruppenraum im 1. Stock bietet Platz für 8 Personen und kann für maximal drei Stunden reserviert werden.</p>",
       field("person", "Name")
       + row(field("tag", "Datum der Reservation", hint="TT.MM.JJJJ"),
             select("zeit", "Zeitfenster", ["9.00–12.00 Uhr", "13.00–16.00 Uhr", "16.00–19.00 Uhr"], err=False)),
       [dict(f="person", t=T_FILLED, m="Bitte geben Sie Ihren Namen ein."),
        dict(f="tag", t=T_DATE, m="Datum ungültig.")],
       fid="gruppenraum", target="#tag", expected="cantTell", rule="3.3.3/C2",
       notes="For '2026-11-12' the error reads 'Datum ungültig.' while the persistent hint 'TT.MM.JJJJ' remains next to the field; evaluators differ on whether this satisfies the suggestion requirement.",
       difficulty="hard")

    return shuffled(rng, cases)
