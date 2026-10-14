"""3.1.1 Language of Page -- 26 page-level cases (target=None).

Case.lang is the ACTUAL language of the content (first language in DOM order for
bilingual pages), not the declared one. Rules: see protocol fragment 3.1.1.
"""
from __future__ import annotations

import re

from common import *

CRITERION = "3.1.1"

# ---------------------------------------------------------------------------
# Hand-written page contents (title, org, main html)
# ---------------------------------------------------------------------------

DE_GRUENGUT = ("Grüngutabfuhr im Winter", "Gemeinde Fiktal", """
<h1>Grüngutabfuhr im Winter</h1>
<p class="muted">Publiziert am 14.10.2026</p>
<p>Von Dezember bis Februar wird das Grüngut nur noch alle zwei Wochen abgeholt, jeweils am Dienstag. Stellen Sie den Container bis 7.00 Uhr gut sichtbar an den Strassenrand.</p>
<p>Weihnachtsbäume nehmen wir am 8. und 15. Januar 2027 kostenlos mit – bitte ohne Schmuck, Lametta und Ständer.</p>
<h2>Abfuhrdaten</h2>
<ul><li>Dienstag, 1. Dezember 2026</li><li>Dienstag, 15. Dezember 2026</li><li>Dienstag, 29. Dezember 2026</li><li>Dienstag, 12. Januar 2027</li></ul>
<p>Fragen beantwortet die Bauverwaltung unter 032 000 12 34.</p>""")

DE_HUNDETAXE = ("Hundetaxe 2027 – Gemeinde Ober-Beispielwil", "Gemeinde Ober-Beispielwil", """
<h1>Hundetaxe und Hundekontrolle 2027</h1>
<p>Alle Hunde, die in Ober-Beispielwil gehalten werden und älter als drei Monate sind, müssen bis zum 31. März 2027 bei der Einwohnerkontrolle angemeldet sein. Die Hundetaxe wird mit der Anmeldung in Rechnung gestellt.</p>
<table><caption>Gebühren pro Jahr</caption><tr><th>Hund</th><th>Taxe</th></tr><tr><td>Erster Hund</td><td>CHF 120.–</td></tr><tr><td>Jeder weitere Hund</td><td>CHF 160.–</td></tr></table>
<p>Die neue Hundemarke erhalten Sie gegen Vorweisen der Rechnung am Schalter. Von der Taxe befreit sind Blindenführhunde, Assistenzhunde und Rettungshunde mit gültigem Einsatzausweis.</p>""")

DE_LESESOMMER = ("Lesesommer 2026 – Bibliothek Mustersee", "Bibliothek Mustersee", """
<h1>Lesesommer 2026: 1250 Bücher gelesen!</h1>
<p>Zum Abschluss des Lesesommers danken wir allen Kindern, die mitgemacht haben. Zusammen habt ihr in den Sommerferien 1250 Bücher gelesen und 312 Lesepässe abgegeben.</p>
<p>Die Verlosung der Preise findet am Samstag, 24. Oktober 2026, um 10.30 Uhr im Lesesaal statt. Eingeladen sind alle Kinder mit ihren Eltern; für Sirup und Zopf ist gesorgt.</p>
<p>Wer seinen Lesepass noch nicht abgegeben hat, kann das bis Mittwoch, 21. Oktober, an der Ausleihtheke nachholen.</p>""")

DE_STELLE = ("Stelle: Fachperson Gesundheit 60–80 %", "Spitex Fiktal-Beispielwil", """
<h1>Wir suchen: Fachperson Gesundheit (60–80 %)</h1>
<p>Die Spitex Fiktal-Beispielwil pflegt und betreut rund 180 Klientinnen und Klienten zu Hause. Für unser Team suchen wir per 1. Januar 2027 oder nach Vereinbarung eine Fachperson Gesundheit EFZ.</p>
<h2>Ihre Aufgaben</h2>
<ul><li>Grundpflege und Behandlungspflege bei Klientinnen und Klienten zu Hause</li><li>Dokumentation im elektronischen Pflegedossier</li><li>Mitarbeit im Wochenend- und Feiertagsdienst</li></ul>
<h2>Wir bieten</h2>
<p>Ein motiviertes Team, ein Dienstfahrzeug oder E-Bike und fortschrittliche Anstellungsbedingungen. Ihre Bewerbung senden Sie bitte an Corinne Probst, Leiterin Pflege.</p>""")

DE_OEFFNUNG = ("Neue Öffnungszeiten – Gemeinde Beispielwil", "Gemeinde Beispielwil", """
<h1>Neue Öffnungszeiten der Gemeindeverwaltung</h1>
<p>Ab Montag, 2. November 2026, gelten geänderte Schalterzeiten. Am Montag ist die Verwaltung neu bis 18.30 Uhr geöffnet, dafür bleibt sie am Mittwochnachmittag geschlossen.</p>
<table><tr><th>Tag</th><th>Vormittag</th><th>Nachmittag</th></tr>
<tr><td>Montag</td><td>8.30–11.30 Uhr</td><td>14.00–18.30 Uhr</td></tr>
<tr><td>Dienstag, Donnerstag, Freitag</td><td>8.30–11.30 Uhr</td><td>14.00–16.30 Uhr</td></tr>
<tr><td>Mittwoch</td><td>8.30–11.30 Uhr</td><td>geschlossen</td></tr></table>
<p>Termine ausserhalb der Öffnungszeiten vereinbaren Sie telefonisch unter 032 000 12 34.</p>""")

DE_KULTURPARK = ("Kulturpark Mustersee – Programm 2027", "Stadt Mustersee", """
<h1>Kulturpark: Open-Air-Kino, Silent Disco und Food Trucks</h1>
<p>Der Kulturpark am See wird im Sommer 2027 wieder zur Bühne. Geplant sind zwölf Open-Air-Kino-Abende, ein Silent Disco für die grossen Fussballspiele und an jedem Freitag ein Street-Food-Markt mit Food Trucks aus der ganzen Region.</p>
<p>Neu gibt es im Pavillon einen Coworking Space mit WLAN, Lockers und einem kleinen Café. Für Start-ups und Vereine organisiert das Team ausserdem Workshops zu Social Media, Crowdfunding und Event-Management.</p>
<p><strong>Save the Date:</strong> Das Kick-off-Meeting für Vereine findet am Dienstag, 17. November 2026, um 19.00 Uhr im Foyer statt.</p>
<h2>Partner</h2>
<p>Brasserie du Port<br>Rue des Granges 4<br>Bourg-Modèle</p>""")

DE_TESSIN = ("Seniorenreise 2027 ins Tessin", "Gemeinde Beispielberg", """
<h1>Seniorenreise 2027: Drei Tage im Tessin</h1>
<p>Die Seniorenreise führt vom 4. bis 6. Mai 2027 in den Süden. Wir fahren mit dem Car nach Esempiano und wohnen im Albergo Al Lago direkt an der Piazza Grande.</p>
<ul><li>Dienstag: Ankunft, Umtrunk mit Merlot und Formaggini, Nachtessen im Grotto Valfittizia</li>
<li>Mittwoch: Schifffahrt nach Modellina, Mittagessen mit Polenta e brasato, freier Nachmittag in der Città vecchia</li>
<li>Donnerstag: Besuch im Museo della Filanda, Rückfahrt mit Halt in Bellavista</li></ul>
<p>Kosten: CHF 480.– im Doppelzimmer, CHF 560.– im Einzelzimmer. Anmeldung bis 15. Januar 2027 bei Reto Muster, Telefon 032 000 45 67.</p>""")

DE_BERATUNG = ("Mütter- und Väterberatung", "Gemeinde Beispielwil", """
<h1>Mütter- und Väterberatung</h1>
<p>Die Mütter- und Väterberatung begleitet Eltern von Kindern bis fünf Jahren. Die Beratung ist kostenlos und vertraulich. Wir beantworten Fragen zu Ernährung, Schlaf, Entwicklung und Erziehung.</p>
<h2>Beratungszeiten im Gemeindehaus</h2>
<ul><li>Jeden ersten und dritten Dienstag im Monat, 13.30–16.30 Uhr (ohne Anmeldung)</li>
<li>Telefonische Beratung: Montag bis Freitag, 8.00–11.00 Uhr, 032 000 77 10</li></ul>
<p>Hausbesuche nach Vereinbarung. Bitte bringen Sie das Gesundheitsheft Ihres Kindes mit.</p>""")

FR_PISCINE = ("Fermeture de la piscine couverte", "Commune de Valfictif", """
<h1>Fermeture de la piscine couverte</h1>
<p>En raison de travaux de révision, la piscine couverte restera fermée du lundi 19 octobre au vendredi 6 novembre 2026. Les abonnements annuels seront prolongés de trois semaines.</p>
<p>Pendant la fermeture, les leçons de natation scolaires ont lieu à la piscine de Bourg-Modèle; le transport est organisé par l'école. Le sauna et le fitness restent ouverts selon l'horaire habituel.</p>
<p>Nous vous remercions de votre compréhension.</p>""")

FR_ENCOMBRANTS = ("Ramassage des objets encombrants", "Ville de Bourg-Modèle", """
<h1>Ramassage des objets encombrants</h1>
<p>Le prochain ramassage des objets encombrants aura lieu le samedi 7 novembre 2026. Les objets doivent être déposés la veille dès 18 h devant votre immeuble, sans gêner le passage.</p>
<h2>Ce qui est accepté</h2>
<ul><li>Meubles, matelas, tapis</li><li>Skis, luges et vélos</li></ul>
<h2>Ce qui n'est pas accepté</h2>
<ul><li>Appareils électriques et électroniques</li><li>Pneus, déchets de chantier, peintures</li></ul>
<p>Les objets de plus de deux mètres doivent être démontés. Renseignements : voirie, 032 000 56 78.</p>""")

FR_ECOLE = ("Inscriptions à l'école enfantine", "École de Valfictif", """
<h1>Inscriptions à l'école enfantine pour la rentrée 2027</h1>
<p>Les enfants nés entre le 1er août 2022 et le 31 juillet 2023 commencent l'école enfantine en août 2027. Les parents concernés recevront un courrier d'ici la fin du mois de novembre.</p>
<p>La séance d'information pour les parents aura lieu le jeudi 21 janvier 2027 à 19 h 30 à l'aula du collège. Les inscriptions se font en ligne jusqu'au 28 février 2027.</p>
<p>Pour toute question, le secrétariat de l'école est à votre disposition le matin, au 032 000 34 56.</p>""")

FR_BIBLIO = ("Les rendez-vous de novembre – Bibliothèque", "Bibliothèque de Bourg-Modèle", """
<h1>Les rendez-vous de novembre</h1>
<div class="cards">
<div class="card"><h2>Heure du conte</h2><p>Chaque mercredi à 15 h, Nadia Spécimen raconte des histoires aux enfants de 4 à 8 ans. L'entrée est libre, sans inscription.</p></div>
<div class="card"><h2>Club de lecture</h2><p>Le club de lecture des adultes se réunit le mardi 24 novembre à 19 h. Au programme : les romans de la rentrée littéraire. Les nouveaux membres sont les bienvenus.</p></div>
<div class="card"><h2>Nouveautés</h2><p>Plus de septante nouveaux livres, bandes dessinées et albums vous attendent sur la table des nouveautés, juste à l'entrée.</p></div>
</div>""")

FR_HORAIRE = ("Nouvel horaire dès le 13 décembre", "Transports publics de Valfictif", """
<h1>Nouvel horaire dès le 13 décembre 2026</h1>
<p>Avec le changement d'horaire du 13 décembre 2026, la ligne 3 circulera toutes les quinze minutes aux heures de pointe, entre 6 h 30 et 8 h 30 et entre 16 h 30 et 18 h 30.</p>
<p>Le bus de nuit du vendredi et du samedi partira désormais de la gare à 0 h 40 et à 1 h 40. L'arrêt « Collège » est déplacé de cinquante mètres en direction du centre.</p>
<p>Les horaires de poche sont disponibles gratuitement au guichet de la gare dès le 1er décembre.</p>""")

FR_EXPO = ("Exposition « L'eau qui travaille »", "Musée du Moulin, Bourg-Modèle", """
<h1>Exposition « L'eau qui travaille »</h1>
<p>Du 6 novembre 2026 au 28 mars 2027, le Musée du Moulin présente l'histoire des moulins, des scieries et des petites centrales électriques de la vallée. Maquettes, photographies d'époque et témoignages audio font revivre deux siècles d'industrie au fil de l'eau.</p>
<p>La commissaire invitée, l'historienne britannique Jane Sample, résume ainsi le projet :</p>
<blockquote lang="en"><p>“Every mill in this valley tells the story of people who learned to share the river.”</p></blockquote>
<p>Visites guidées en français le dimanche à 14 h. Entrée : CHF 8.–, gratuit jusqu'à 16 ans.</p>""")

FR_NEIGE = ("Déneigement : règles pour les riverains", "Commune d'Exempleval", """
<nav aria-label="Langues"><ul class="langs">
<li><a href="../de/winterdienst.html" lang="de" hreflang="de">Deutsch</a></li>
<li><a href="../it/sgombero-neve.html" lang="it" hreflang="it">Italiano</a></li>
<li><a href="../en/snow-clearing.html" lang="en" hreflang="en">English</a></li></ul></nav>
<h1>Déneigement : ce que les riverains doivent savoir</h1>
<p>Dès les premières chutes de neige, la voirie dégage en priorité les routes principales, les arrêts de bus et les accès aux écoles. Les chemins privés ne sont pas déneigés par la commune.</p>
<p>Les propriétaires doivent dégager les trottoirs devant leur immeuble avant 7 h 30. Merci de ne pas repousser la neige sur la chaussée.</p>
<p>Les véhicules stationnés sur la route entre 2 h et 6 h peuvent être déplacés aux frais du détenteur.</p>""")

IT_BIBLIO = ("Nuovi orari invernali – Biblioteca", "Biblioteca di Modellina", """
<h1>Nuovi orari invernali</h1>
<p>Dal 2 novembre 2026 la biblioteca sarà aperta anche il sabato pomeriggio, dalle 14.00 alle 17.00. In compenso, il lunedì mattina la biblioteca resterà chiusa.</p>
<table><tr><th>Giorno</th><th>Orario</th></tr>
<tr><td>Lunedì</td><td>14.00–18.30</td></tr>
<tr><td>Da martedì a venerdì</td><td>9.00–12.00 e 14.00–18.30</td></tr>
<tr><td>Sabato</td><td>9.00–12.00 e 14.00–17.00</td></tr></table>
<p>Il servizio di prestito a domicilio per le persone anziane continua come di consueto ogni giovedì.</p>""")

IT_CARTA = ("Raccolta di carta e cartone", "Comune di Esempiano", """
<h1>Raccolta di carta e cartone</h1>
<p>La raccolta di carta e cartone avviene ogni secondo mercoledì del mese. I pacchi, legati con lo spago e non più pesanti di 10 kg, vanno depositati entro le 7.00 nei punti di raccolta abituali.</p>
<p>Non sono ammessi i cartoni delle bevande, la carta oleata, gli scontrini e la carta da regalo plastificata. Questi rifiuti vanno smaltiti con i sacchi tassati.</p>
<p>Per informazioni: Ufficio tecnico comunale, telefono 091 000 23 45.</p>""")

IT_CANTIERE = ("Lavori in Via Cantonale", "Comune di Valfittizia", """
<h1>Lavori di risanamento in Via Cantonale</h1>
<p>Dal 26 ottobre al 18 dicembre 2026 la Via Cantonale sarà chiusa al traffico tra la Piazza Grande e la stazione. I lavori riguardano la sostituzione delle condotte dell'acqua potabile e il rifacimento della pavimentazione.</p>
<p>Il traffico sarà deviato su Via ai Monti. Le fermate del bus « Piazza Grande » e « Posta » sono spostate provvisoriamente in Vicolo del Forno.</p>
<p>Ci scusiamo per i disagi e ringraziamo la popolazione per la comprensione.</p>""")

IT_SCUOLA = ("Iscrizioni alla scuola dell'infanzia", "Scuola di Esempiano", """
<h1>Iscrizioni alla scuola dell'infanzia 2027/2028</h1>
<p>Sono invitati a iscriversi i bambini nati tra il 1° agosto 2022 e il 31 luglio 2023. La frequenza è obbligatoria per il secondo anno e facoltativa per il primo.</p>
<p>Il modulo d'iscrizione è disponibile presso la segreteria scolastica e va consegnato entro venerdì 29 gennaio 2027. La serata informativa per i genitori si terrà martedì 19 gennaio alle 20.00 nell'aula magna.</p>""")

IT_GEMELLAGGIO = ("Dieci anni di gemellaggio con Beispielwil", "Comune di Esempiano", """
<h1>Dieci anni di gemellaggio con Beispielwil</h1>
<p>Sabato 21 novembre 2026 festeggiamo i dieci anni di gemellaggio con il comune di Beispielwil. Una delegazione di trenta persone arriverà in treno alle 10.30 e sarà accolta in Piazza Grande dalla banda comunale.</p>
<p>Nel suo messaggio, il sindaco di Beispielwil, Urs Exempel, scrive:</p>
<blockquote lang="de-CH"><p>«Wir freuen uns auf das Wiedersehen mit unseren Freundinnen und Freunden im Süden.»</p></blockquote>
<p>Dopo il pranzo in comune, alle 15.00 è previsto un concerto delle due bande. La popolazione è cordialmente invitata.</p>""")

IT_MOSTRA = ("Nuova mostra «Fili di seta»", "Museo della Filanda, Esempiano", """
<h1>Nuova mostra: «Fili di seta»</h1>
<p>Dal 14 novembre 2026 il Museo della Filanda presenta la mostra «Fili di seta», dedicata alle filandine che lavoravano nella valle all'inizio del Novecento. Fotografie, attrezzi originali e testimonianze raccolte negli archivi comunali raccontano una storia di lavoro duro e di grande solidarietà.</p>
<p>Orari: da mercoledì a domenica, 14.00–17.00. Ingresso: CHF 8.–, gratuito fino a 16 anni. Visite guidate per le scuole su prenotazione.</p>""")

EN_HOSTEL = ("Getting here – Lake Fictal Hostel", "Lake Fictal Hostel", """
<h1>Getting here</h1>
<p>Lake Fictal Hostel is a ten-minute walk from Beispielwil railway station. Follow Lake Road towards the harbour and turn left after the boat landing stage.</p>
<p>By car: there are only six parking spaces at the hostel. Please book a space in advance; a day ticket costs CHF 12.</p>
<p>Reception is open daily from 7.30 am to 10 pm. If you arrive later, please call us on +41 32 000 88 99 and we will leave your key in the key safe.</p>""")


# ---------------------------------------------------------------------------
# Bilingual pages (C1): built from language-tagged segments, words counted
# ---------------------------------------------------------------------------

_WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ]+")


def _words(fragment: str) -> int:
    return len(_WORD.findall(re.sub(r"<[^>]+>", " ", fragment)))


BILINGUAL = [
    dict(  # parallel DE/FR notice, DE first, lang de-CH, FR has more words
        lang="de", declared="de-CH", first="de",
        title=[("de", "Wasserunterbruch"), ("fr", "Coupure d'eau")],
        org=[("de", "Gemeinde Beispielwil"), ("fr", "Commune de Beispielwil")],
        nav=[[("de", "Aktuelles"), ("fr", "Actualités")], [("de", "Verwaltung"), ("fr", "Administration")],
             [("de", "Kontakt"), ("fr", "Contact")]],
        layout="columns",
        blocks=[
            ("de", "<h2>Wasserunterbruch am 3. November</h2><p>Wegen dringender Arbeiten an der Hauptleitung ist die Wasserversorgung im ganzen Quartier Seeweg am Dienstag, 3. November 2026, von 8.00 bis 12.00 Uhr unterbrochen.</p><p>Bitte füllen Sie vorher genügend Trinkwasser ab und schliessen Sie alle Wasserhähne. Nach dem Unterbruch kann das Wasser für kurze Zeit trüb sein; lassen Sie es dann einige Minuten laufen.</p>"),
            ("fr", "<h2>Coupure d'eau le 3 novembre</h2><p>En raison de travaux urgents sur la conduite principale, l'eau sera coupée dans tout le quartier du Seeweg le mardi 3 novembre 2026, de 8 h à 12 h.</p><p>Faites une réserve d'eau potable et fermez tous les robinets. Après la coupure, l'eau peut être trouble quelque temps; laissez-la couler quelques minutes.</p>"),
        ]),
    dict(  # mixed FR/DE school page, FR first, lang de-CH, DE slightly more words
        lang="fr", declared="de-CH", first="fr",
        title=[("fr", "Infos aux parents"), ("de", "Elterninformation")],
        org=[("de", "Schule Beispielberg"), ("fr", "École de Beispielberg")],
        nav=[[("fr", "Accueil"), ("de", "Startseite")], [("fr", "Horaires"), ("de", "Stundenpläne")],
             [("fr", "Contact"), ("de", "Kontakt")]],
        layout="stack",
        blocks=[
            ("fr", "<h2>Course d'école des classes françaises</h2><p>Les classes de 5H à 8H partiront en course d'école le jeudi 22 octobre. Rendez-vous à 7 h 45 devant le collège; retour vers 17 h.</p>"),
            ("de", "<h2>Elternabend der deutschsprachigen Klassen</h2><p>Der Elternabend der 1. bis 4. Klassen findet am Dienstag, 27. Oktober, um 19.30 Uhr in der Aula statt. Die Lehrpersonen stellen das Jahresprogramm und das neue Hausaufgabenkonzept vor. Anschliessend beantworten sie gerne Ihre Fragen.</p>"),
            ("fr", "<h2>Dentiste scolaire</h2><p>Le contrôle dentaire annuel aura lieu en novembre. Les enfants recevront une fiche à faire signer par les parents.</p>"),
            ("de", "<h2>Pausenkiosk</h2><p>Ab November verkauft der Elternrat jeden Freitag in der grossen Pause Früchte, Brötchen und Tee. Freiwillige Helferinnen und Helfer melden sich bitte bei Anna Beispiel. Der Erlös kommt dem Klassenlager zugute.</p>"),
        ]),
    dict(  # mixed IT/DE valley commune, IT first, lang it-CH, DE slightly more words
        lang="it", declared="it-CH", first="it",
        title=[("it", "Avvisi"), ("de", "Mitteilungen")],
        org=[("it", "Comune di Valfittizia"), ("de", "Gemeinde Valfittizia")],
        nav=[[("it", "Avvisi"), ("de", "Mitteilungen")], [("it", "Cancelleria"), ("de", "Kanzlei")],
             [("it", "Contatti"), ("de", "Kontakt")]],
        layout="stack",
        blocks=[
            ("it", "<h2>Chiusura della strada per Valfittizia di Sopra</h2><p>Per lavori di consolidamento del muro di sostegno, la strada comunale per Valfittizia di Sopra sarà chiusa dal 2 al 13 novembre, dalle 8.00 alle 17.00. Il servizio scolastico è garantito.</p>"),
            ("de", "<h2>Holzschlag im Gemeindewald</h2><p>Im Gemeindewald oberhalb von Valfittizia wird ab Mitte November Holz geschlagen. Die Wanderwege zur Alp sind während der Arbeiten zeitweise gesperrt. Bitte beachten Sie die Signalisation und die Anweisungen des Forstpersonals.</p>"),
            ("it", "<h2>Sportello comunale durante le feste</h2><p>La cancelleria comunale resterà chiusa dal 24 dicembre al 3 gennaio. Per urgenze è raggiungibile il numero 081 000 11 22.</p>"),
            ("de", "<h2>Christbaumverkauf beim Werkhof</h2><p>Am Samstag, 12. Dezember, verkauft der Forstdienst von 9.00 bis 12.00 Uhr Christbäume aus dem eigenen Wald. Der Erlös geht an die Jugendmusik.</p>"),
        ]),
    dict(  # mixed DE/IT sports club, DE first, lang it, IT more words
        lang="de", declared="it", first="de",
        title=[("de", "Sportverein"), ("it", "Società sportiva")],
        org=[("it", "Società sportiva Valfittizia")],
        nav=[[("it", "Squadre")], [("it", "Calendario")], [("it", "Contatti")]],
        layout="stack",
        blocks=[
            ("de", "<h2>Hallentraining im Winter</h2><p>Ab dem 2. November trainieren die Junioren jeweils am Dienstag und Donnerstag von 18.00 bis 19.30 Uhr in der Turnhalle. Bitte saubere Hallenschuhe mitbringen.</p>"),
            ("it", "<h2>Allenamenti invernali</h2><p>Dal 2 novembre gli juniori si allenano il martedì e il giovedì dalle 18.00 alle 19.30 in palestra. Si prega di portare scarpe da ginnastica pulite.</p>"),
            ("de", "<h2>Generalversammlung</h2><p>Die Generalversammlung findet am Freitag, 27. November, um 20.00 Uhr im Restaurant Sternen statt. Anschliessend offeriert der Verein einen Umtrunk.</p>"),
            ("it", "<h2>Assemblea generale</h2><p>L'assemblea generale si terrà venerdì 27 novembre alle 20.00 presso il ristorante Stella. Al termine è offerto un aperitivo.</p>"),
        ]),
]


def _bilingual(rng, spec):
    counts = {}

    def add(lang, frag):
        counts[lang] = counts.get(lang, 0) + _words(frag)
        return frag

    title = " – ".join(add(l, esc(t)) for l, t in spec["title"])
    org = " · ".join(add(l, esc(t)) for l, t in spec["org"])
    nav_items = []
    for item in spec["nav"]:
        label = " / ".join(add(l, esc(t)) for l, t in item)
        nav_items.append(f'<li><a href="{slug(item[0][1])}.html">{label}</a></li>')
    header_html = (f'<header class="site-header"><a class="site-name" href="index.html">{org}</a>'
                   f'<nav class="site-nav"><ul>{"".join(nav_items)}</ul></nav></header>')
    h1 = "<h1>" + " / ".join(add(l, esc(t)) for l, t in spec["title"]) + "</h1>"
    blocks = [add(l, f) for l, f in spec["blocks"]]
    if spec["layout"] == "columns":
        main = h1 + '<div class="cards">' + "".join(f'<section class="card">{b}</section>' for b in blocks) + "</div>"
    else:
        main = h1 + "".join(f"<section>{b}</section>" for b in blocks)
    langs = sorted(counts)
    assert len(langs) == 2, counts
    a, b = counts[langs[0]], counts[langs[1]]
    ratio = a / b
    assert 0.8 <= ratio <= 1.25, (spec["title"], counts)
    declared = spec["declared"].split("-")[0]
    other = [x for x in langs if x != declared][0]
    if counts[declared] > counts[other]:
        alt = "passed"
    elif counts[declared] < counts[other]:
        alt = "failed"
    else:
        alt = "inapplicable"
    first_reading = "passed" if spec["first"] == declared else "failed"
    assert alt != first_reading, (spec["title"], counts)
    body = header_html + f"\n<main>\n{main}\n</main>\n" + f'<footer class="site-footer"><p>{org}</p></footer>'
    html = page(spec["declared"], title, body, rng=rng)
    return html, alt, counts


# ---------------------------------------------------------------------------

def build(rng):
    cases = []

    def single(content, lang, declared, expected, rule, notes, *, trap=False, difficulty="medium",
               chrome=True, html_attrs=""):
        title, org, main = content
        body = wrap(lang, org, main.strip(), chrome=chrome)
        html = page(declared, title, body, rng=rng, html_attrs=html_attrs,
                    css=".langs{list-style:none;display:flex;gap:12px;padding:0;margin:0 0 8px;font-size:.9rem}")
        cases.append(Case(CRITERION, lang, expected, html=html, target=None, rule=rule, notes=notes,
                          trap=trap, difficulty=difficulty))

    # ---- failed ----------------------------------------------------------
    single(DE_GRUENGUT, "de", None, "failed", "3.1.1/F1",
           "German page, but the html element has no lang attribute at all.", difficulty="easy")
    single(FR_PISCINE, "fr", None, "failed", "3.1.1/F1",
           "French page without any lang attribute on the html element.", difficulty="easy", chrome=False)
    single(IT_BIBLIO, "it", " ", "failed", "3.1.1/F1",
           "Italian page whose html lang attribute contains only a space, which does not declare any language.",
           difficulty="medium")
    single(DE_HUNDETAXE, "de", "de_CH", "failed", "3.1.1/F2",
           "lang=\"de_CH\" uses locale syntax with an underscore; the value is not a known primary language subtag.",
           difficulty="medium")
    single(FR_ENCOMBRANTS, "fr", "fra", "failed", "3.1.1/F2",
           "lang=\"fra\" is an ISO 639-2 code that is not a registered IANA primary subtag (French is 'fr').",
           difficulty="hard")
    single(IT_CARTA, "it", "italiano", "failed", "3.1.1/F2",
           "lang=\"italiano\" is a word, not a valid language tag; the Italian page has no valid default language.",
           difficulty="easy", chrome=False)
    single(IT_CANTIERE, "it", "de-CH", "failed", "3.1.1/F3",
           "Italian road-works notice declares lang=\"de-CH\" (copied from the German site template); content is entirely Italian.",
           difficulty="easy")
    single(FR_ECOLE, "fr", "en", "failed", "3.1.1/F3",
           "French school page declares lang=\"en\" (CMS default) although all text is French.", difficulty="easy")
    single(DE_LESESOMMER, "de", "ch", "failed", "3.1.1/F3",
           "lang=\"ch\" is a valid tag but means Chamorro (country code used by mistake); the page is German.",
           difficulty="hard")
    single(DE_STELLE, "de", None, "failed", "3.1.1/F4",
           "Legacy XHTML markup: only xml:lang=\"de\" is set and lang is missing; xml:lang has no effect in text/html, so no language is declared.",
           difficulty="hard", html_attrs=' xmlns="http://www.w3.org/1999/xhtml" xml:lang="de"')
    single(IT_MOSTRA, "it", "en", "failed", "3.1.1/F4",
           "Italian page with lang=\"en\" and xml:lang=\"it\": browsers and AT use lang, so the effective language is English, which is wrong.",
           difficulty="hard", html_attrs=' xmlns="http://www.w3.org/1999/xhtml" xml:lang="it"')

    # ---- passed ----------------------------------------------------------
    single(DE_OEFFNUNG, "de", "de-CH", "passed", "3.1.1/P1",
           "German page with lang=\"de-CH\"; title, navigation and content are German.", difficulty="easy")
    single(FR_BIBLIO, "fr", "fr", "passed", "3.1.1/P1",
           "French library page with lang=\"fr\" matching all content.", difficulty="easy")
    single(FR_HORAIRE, "fr", "fr-CH", "passed", "3.1.1/P1",
           "French timetable notice with lang=\"fr-CH\"; region subtag is fine and the primary subtag matches.",
           difficulty="easy", chrome=False)
    single(IT_SCUOLA, "it", "it-CH", "passed", "3.1.1/P1",
           "Italian school page declared as it-CH; all text is Italian.", difficulty="easy")
    single(EN_HOSTEL, "en", "en", "passed", "3.1.1/P1",
           "English tourism page with lang=\"en\"; the place names (Beispielwil, Lake Road) are proper names.",
           difficulty="easy")
    single(DE_KULTURPARK, "de", "de-CH", "passed", "3.1.1/T1",
           "German page full of English event jargon (Open-Air, Silent Disco, Coworking Space, Save the Date) and a French partner address; German is still clearly the main language.",
           trap=True, difficulty="medium")
    single(DE_TESSIN, "de", "de-CH", "passed", "3.1.1/T1",
           "German trip programme with many Italian place names and dishes (Piazza Grande, Grotto, Polenta e brasato); sentences are German, so de-CH is right.",
           trap=True, difficulty="medium")
    single(FR_EXPO, "fr", "fr", "passed", "3.1.1/T2",
           "French museum page with a one-sentence English quotation marked lang=\"en\"; the page default French is correct.",
           trap=True, difficulty="medium")
    single(IT_GEMELLAGGIO, "it", "it-CH", "passed", "3.1.1/T2",
           "Italian page quoting one German sentence marked lang=\"de-CH\"; default language Italian is correct.",
           trap=True, difficulty="medium")
    single(FR_NEIGE, "fr", "fr-CH", "passed", "3.1.1/T2",
           "French page whose language switcher links (Deutsch, Italiano, English) carry their own lang attributes; the default fr-CH matches the content.",
           trap=True, difficulty="medium")
    single(DE_BERATUNG, "de", "de-CH-1996", "passed", "3.1.1/T3",
           "lang=\"de-CH-1996\" has a region and an orthography variant subtag; the primary subtag 'de' is valid and matches the German content.",
           trap=True, difficulty="hard")

    # ---- cantTell (bilingual) ----------------------------------------------
    notes_tpl = {
        0: "Parallel German/French notice of equal content, not marked with lang; lang=de-CH names the first language, while the French half has more words (ACT word count: French).",
        1: "Mixed French/German school page, French used first, lang=de-CH; amounts are nearly equal with slightly more German words, so 'first language' and 'word count' readings disagree.",
        2: "Italian/German valley-commune notices in roughly equal amounts, Italian first and declared (it-CH), German slightly longer; default language is debatable.",
        3: "German/Italian club page in parallel, German first but lang=it; Italian has slightly more words, so the 'first language' and 'most words' readings disagree.",
    }
    for i, spec in enumerate(BILINGUAL):
        html, alt, counts = _bilingual(rng, spec)
        cases.append(Case(CRITERION, spec["lang"], "cantTell", html=html, target=None, rule="3.1.1/C1",
                          notes=notes_tpl[i], alt_expected=alt, difficulty="hard"))

    return shuffled(rng, cases)
