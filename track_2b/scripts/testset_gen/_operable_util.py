"""Private helpers for the "operable" modules (2.2.2, 2.4.2, 2.4.3, 2.4.5, 3.2.2, 3.2.3, 3.2.4).

Contains a hand-written library of small fictional sites (DE/FR/IT, six site types each)
and builders for multi-page mini sites (navigation, search with an inline JS index,
site map, breadcrumbs, footers). Stdlib only; deterministic.
"""
from __future__ import annotations

import json

from common import *  # noqa: F401,F403
from common import esc, page, SITE_LANG_TAG


def P(slug, nav, h1, paras, li=None):
    return {"slug": slug, "nav": nav, "h1": h1, "p": list(paras), "li": list(li or [])}


UI = {
    "de": dict(home="Startseite", skip="Zum Inhalt springen", nav="Hauptnavigation", search_label="Suchbegriff",
               search_btn="Suchen", search_region="Website durchsuchen", no_hits="Keine Treffer.",
               sitemap="Sitemap", az="Themen A–Z", crumbs="Sie sind hier", related="Das könnte Sie auch interessieren",
               news="Aktuell", more="Weiterlesen", service="Service", imprint="Impressum", privacy="Datenschutz",
               a11y="Barrierefreiheit", contact="Kontakt", phone="Telefon", lang_label="Sprache", subnav="Unternavigation",
               footer_nav="Servicelinks", topics="Themen", quick="Direkt zu"),
    "fr": dict(home="Accueil", skip="Aller au contenu", nav="Navigation principale", search_label="Terme recherché",
               search_btn="Rechercher", search_region="Rechercher sur le site", no_hits="Aucun résultat.",
               sitemap="Plan du site", az="Index A–Z", crumbs="Vous êtes ici", related="À voir aussi",
               news="Actualités", more="Lire la suite", service="Services", imprint="Mentions légales",
               privacy="Protection des données", a11y="Accessibilité", contact="Contact", phone="Téléphone",
               lang_label="Langue", subnav="Sous-navigation", footer_nav="Liens utiles", topics="Thèmes",
               quick="Accès direct"),
    "it": dict(home="Home", skip="Vai al contenuto", nav="Navigazione principale", search_label="Termine di ricerca",
               search_btn="Cerca", search_region="Cerca nel sito", no_hits="Nessun risultato.",
               sitemap="Mappa del sito", az="Indice A–Z", crumbs="Vi trovate qui", related="Vedi anche",
               news="Attualità", more="Continua a leggere", service="Servizi", imprint="Note legali",
               privacy="Protezione dei dati", a11y="Accessibilità", contact="Contatti", phone="Telefono",
               lang_label="Lingua", subnav="Sottonavigazione", footer_nav="Link utili", topics="Temi",
               quick="Accesso rapido"),
}


def _site(lang, kind, org, street, phone, mail, host, pages, deep, teaser):
    return dict(lang=lang, kind=kind, org=org, street=street, phone=phone, mail=mail, host=host,
                pages=pages, deep=deep, teaser=teaser)


SITES = {
    "de": [
        _site("de", "municipality", "Gemeinde Beispielwil", "Dorfstrasse 1, 3999 Beispielwil", "032 000 12 34",
              "gemeinde@beispielwil.example", "www.beispielwil.example", [
                  P("index", "Startseite", "Willkommen in Beispielwil", [
                      "Beispielwil zählt rund 4200 Einwohnerinnen und Einwohner und liegt am Fuss des Beispielbergs.",
                      "Die Gemeindekanzlei ist am Montag von 8.30–11.30 und 14.00–18.30 Uhr geöffnet, Dienstag bis Freitag von 8.30–11.30 Uhr."]),
                  P("verwaltung", "Verwaltung", "Gemeindeverwaltung", [
                      "Die Gemeindeverwaltung befindet sich im Gemeindehaus an der Dorfstrasse 1."],
                    ["Gemeindekanzlei", "Einwohnerdienste", "Finanzen und Steuern", "Bauverwaltung"]),
                  P("abfall", "Abfall", "Abfall und Recycling", [
                      "Der Kehricht wird jeden Dienstag ab 7.00 Uhr abgeholt. Stellen Sie die gebührenpflichtigen Säcke erst am Abholtag bereit."],
                    ["Grüngut: jeden zweiten Freitag", "Papier und Karton: 1. Mittwoch im Monat",
                     "Sammelstelle Werkhof: Samstag 9.00–12.00 Uhr"]),
                  P("steuern", "Steuern", "Steuern", [
                      "Die Steuererklärung 2025 ist bis am 31. März 2026 einzureichen.",
                      "Eine Fristerstreckung bis 30. September können Sie online beantragen; sie ist kostenlos."]),
                  P("bauen", "Bauen", "Bauen und Wohnen", [
                      "Baugesuche reichen Sie in dreifacher Ausführung bei der Bauverwaltung ein.",
                      "Kleinere Vorhaben wie Gartenhäuser bis 10 m² sind meldepflichtig, aber nicht bewilligungspflichtig."]),
                  P("freizeit", "Freizeit", "Freizeit und Vereine", [
                      "In Beispielwil sind über 30 Vereine aktiv – vom Turnverein bis zur Musikgesellschaft."],
                    ["Hallenbad Beispielwil", "Ludothek im Schulhaus Matte", "Vita-Parcours am Waldrand"]),
              ],
              P("hundekontrolle", "Hundekontrolle", "Hundekontrolle und Hundesteuer", [
                  "Hunde müssen bis Ende Februar bei den Einwohnerdiensten angemeldet werden.",
                  "Die Hundesteuer beträgt CHF 120.– pro Jahr; für Blindenführhunde wird keine Steuer erhoben."]),
              "Bis Ende Februar: Hunde anmelden"),
        _site("de", "school", "Schule Beispielberg", "Schulhausstrasse 8, 3998 Beispielberg", "033 000 45 10",
              "sekretariat@schule-beispielberg.example", "www.schule-beispielberg.example", [
                  P("index", "Startseite", "Schule Beispielberg", [
                      "Rund 380 Kinder besuchen bei uns den Kindergarten und die Primarschule.",
                      "Das Schulsekretariat ist von Montag bis Freitag von 7.30–11.30 Uhr erreichbar."]),
                  P("unterricht", "Unterricht", "Unterrichtszeiten", [
                      "Der Unterricht beginnt um 7.50 Uhr. Die Blockzeiten dauern am Vormittag bis 11.55 Uhr.",
                      "Am Mittwochnachmittag ist für alle Klassen schulfrei."]),
                  P("ferienplan", "Ferienplan", "Ferienplan 2026/27", [
                      "Die Ferien gelten für den Kindergarten und alle Primarklassen."],
                    ["Herbstferien: 3.–18. Oktober 2026", "Weihnachtsferien: 24. Dezember 2026 – 6. Januar 2027",
                     "Sportferien: 6.–14. Februar 2027", "Frühlingsferien: 10.–25. April 2027"]),
                  P("tagesschule", "Tagesschule", "Tagesschule", [
                      "Die Tagesschule betreut Kinder vor und nach dem Unterricht sowie über Mittag.",
                      "Die Anmeldung für das neue Schuljahr ist jeweils bis am 31. Mai möglich."]),
                  P("schulsozialarbeit", "Schulsozialarbeit", "Schulsozialarbeit", [
                      "Die Schulsozialarbeiterin berät Kinder, Eltern und Lehrpersonen vertraulich.",
                      "Sprechstunde: Mittwoch 13.30–16.00 Uhr im Pavillon."]),
                  P("eltern", "Eltern", "Elternrat", [
                      "Der Elternrat organisiert den Pausenkiosk und das Schulfest.",
                      "Neue Mitglieder sind jederzeit willkommen."]),
              ],
              P("skilager", "Skilager", "Skilager 2027", [
                  "Das Skilager der 5. und 6. Klassen findet vom 15. bis 19. Februar 2027 in Fiktal statt.",
                  "Der Elternbeitrag beträgt CHF 150.–; Ski können vor Ort gemietet werden."]),
              "Skilager 2027: Infos für Eltern"),
        _site("de", "library", "Bibliothek Mustersee", "Seeweg 21, 3997 Mustersee", "031 000 77 20",
              "info@bibliothek-mustersee.example", "www.bibliothek-mustersee.example", [
                  P("index", "Startseite", "Bibliothek Mustersee", [
                      "Über 25 000 Bücher, Hörbücher und Spiele für alle Generationen.",
                      "Ausweis vergessen? Ausleihen sind auch mit einem amtlichen Ausweis möglich."]),
                  P("oeffnungszeiten", "Öffnungszeiten", "Öffnungszeiten", [
                      "In den Schulferien gelten reduzierte Öffnungszeiten."],
                    ["Dienstag: 14.00–18.30 Uhr", "Mittwoch: 9.00–12.00 und 14.00–18.30 Uhr",
                     "Freitag: 14.00–19.00 Uhr", "Samstag: 9.30–13.00 Uhr"]),
                  P("ausleihe", "Ausleihe", "Ausleihe und Gebühren", [
                      "Das Jahresabo kostet CHF 30.–; für Kinder und Jugendliche bis 18 Jahre ist die Ausleihe gratis.",
                      "Die Leihfrist beträgt vier Wochen und kann zweimal verlängert werden."]),
                  P("medien", "Medien", "Medienangebot", [
                      "Neben Büchern finden Sie bei uns Zeitschriften, DVDs, Gesellschaftsspiele und Tonies."],
                    ["Romane und Sachbücher", "Grossdruckbücher", "Comics und Mangas", "Sprachkurse"]),
                  P("e-medien", "E-Medien", "E-Books und E-Audio", [
                      "Mit Ihrem Bibliotheksausweis können Sie rund um die Uhr E-Books und Hörbücher ausleihen."]),
                  P("veranstaltungen", "Veranstaltungen", "Veranstaltungen", [
                      "Alle Veranstaltungen sind kostenlos; eine Anmeldung ist nicht nötig."],
                    ["Erzählstunde für Kinder ab 4 Jahren: jeden ersten Mittwoch, 15.00 Uhr",
                     "Lesung mit Corinne Probst: 12.11.2026, 19.30 Uhr", "Spielnachmittag: 28.11.2026, 14.00–17.00 Uhr"]),
              ],
              P("sommerleseclub", "Sommerleseclub", "Sommerleseclub", [
                  "Wer bis Ende August fünf Bücher liest, erhält einen Gutschein für das Strandbad.",
                  "Die Lesepässe liegen ab 1. Juli an der Theke bereit."]),
              "Mitmachen beim Sommerleseclub"),
        _site("de", "utility", "Wasserversorgung Fiktal", "Mühlegasse 5, 3996 Fiktal", "032 000 55 60",
              "wasser@fiktal.example", "www.wasser-fiktal.example", [
                  P("index", "Startseite", "Wasserversorgung Fiktal", [
                      "Wir liefern täglich rund 1800 m³ Trinkwasser an Haushalte und Betriebe in Fiktal."]),
                  P("wasserqualitaet", "Wasserqualität", "Wasserqualität", [
                      "Unser Trinkwasser stammt zu 70 % aus Quellen und zu 30 % aus Grundwasser.",
                      "Die Gesamthärte beträgt 18 °fH (mittelhart)."]),
                  P("hausanschluss", "Hausanschluss", "Neuer Hausanschluss", [
                      "Für einen neuen Hausanschluss reichen Sie das Anschlussgesuch mindestens acht Wochen vor Baubeginn ein."]),
                  P("tarife", "Tarife", "Tarife 2026", [
                      "Die Tarife wurden von der Gemeindeversammlung im Juni 2025 genehmigt."],
                    ["Wasserpreis: CHF 1.60 pro m³", "Grundgebühr: CHF 90.– pro Jahr und Zähler",
                     "Anschlussgebühr: nach Gebäudeversicherungswert"]),
                  P("stoerungen", "Störungen", "Störung melden", [
                      "Bei Rohrbrüchen oder fehlendem Wasser erreichen Sie unseren Pikettdienst rund um die Uhr unter 032 000 55 66."]),
                  P("ueber-uns", "Über uns", "Über uns", [
                      "Die Wasserversorgung ist ein Betrieb der Gemeinde Fiktal und beschäftigt sechs Mitarbeitende."]),
              ],
              P("zaehlerablesung", "Zählerablesung", "Zählerablesung 2026", [
                  "Zwischen dem 10. und 21. November lesen unsere Mitarbeitenden die Wasserzähler ab.",
                  "Sind Sie nicht zu Hause, erhalten Sie eine Ablesekarte."]),
              "Ab 10. November: Zählerablesung"),
        _site("de", "transport", "Beispielwiler Verkehrsbetriebe", "Gerberngasse 15, 3999 Beispielwil", "032 000 80 80",
              "info@mvb.example", "www.mvb.example", [
                  P("index", "Startseite", "Beispielwiler Verkehrsbetriebe", [
                      "Sechs Buslinien verbinden Beispielwil, Beispielberg und Fiktal im 15-Minuten-Takt."]),
                  P("fahrplan", "Fahrplan", "Fahrplan", [
                      "Der neue Fahrplan gilt ab 13. Dezember 2026.",
                      "Linie 3 fährt neu bis zum Spital Mustersee."]),
                  P("billette", "Billette", "Billette und Abos", [
                      "Billette erhalten Sie am Automaten, im Bus und in der App."],
                    ["Einzelbillett Zone 10: CHF 2.80", "Tageskarte: CHF 8.40", "Monatsabo Erwachsene: CHF 68.–"]),
                  P("haltestellen", "Haltestellen", "Haltestellen", [
                      "Alle 42 Haltestellen sind mit Abfahrtsanzeigen ausgestattet; 35 davon sind stufenlos zugänglich."]),
                  P("fundbuero", "Fundbüro", "Fundbüro", [
                      "Fundgegenstände aus unseren Bussen holen Sie am Schalter Bahnhofplatz ab: Montag bis Freitag, 8.00–12.00 Uhr."]),
                  P("unternehmen", "Unternehmen", "Unternehmen", [
                      "Rund 120 Mitarbeitende sorgen dafür, dass jährlich 6,5 Millionen Fahrgäste ans Ziel kommen."]),
              ],
              P("nachtbus", "Nachtbus", "Nachtbus am Wochenende", [
                  "In den Nächten auf Samstag und Sonntag fährt der Nachtbus N1 um 1.15 und 2.30 Uhr ab Bahnhof Beispielwil.",
                  "Es gilt der normale Tarif; ein Nachtzuschlag wird nicht erhoben."]),
              "Neu: Nachtbus am Wochenende"),
        _site("de", "tourism", "Verkehrsverein Ober-Beispielwil", "Dorfplatz 2, 3990 Ober-Beispielwil", "033 000 31 31",
              "info@ober-beispielwil.example", "www.ober-beispielwil.example", [
                  P("index", "Startseite", "Ferien in Ober-Beispielwil", [
                      "Auf 1200 m ü. M. erwarten Sie 80 km markierte Wanderwege, zwei Bergseen und ruhige Unterkünfte."]),
                  P("wandern", "Wandern", "Wandern", [
                      "Alle Routen sind gelb markiert und ab Dorfplatz signalisiert."],
                    ["Seenweg: 3 h, mittel", "Panoramaweg: 1 h 45, leicht",
                     "Gratwanderung Hohe Fiktalspitze: 5 h 30, anspruchsvoll"]),
                  P("unterkuenfte", "Unterkünfte", "Unterkünfte", [
                      "Vom Familienhotel bis zur Alphütte: 14 Betriebe mit insgesamt 420 Betten."]),
                  P("winter", "Winter", "Winterangebote", [
                      "Die Schlittelbahn ist bei guten Verhältnissen täglich von 9.00 bis 16.30 Uhr geöffnet.",
                      "Die Tageskarte kostet CHF 18.–, für Kinder CHF 9.–."]),
                  P("anreise", "Anreise", "Anreise", [
                      "Ab Bahnhof Beispielwil fährt der Bus Linie 61 stündlich nach Ober-Beispielwil; die Fahrzeit beträgt 25 Minuten."]),
                  P("infostelle", "Infostelle", "Tourist Info", [
                      "Die Infostelle am Dorfplatz ist täglich von 9.00–12.00 Uhr und 14.00–17.30 Uhr geöffnet."]),
              ],
              P("alpkaesemarkt", "Alpkäsemarkt", "Alpkäsemarkt", [
                  "Am 26. September verkaufen acht Alpbetriebe ihren Käse auf dem Dorfplatz.",
                  "Ab 10.00 Uhr spielt die Alphorngruppe Ober-Beispielwil."]),
              "26. September: Alpkäsemarkt"),
    ],
    "fr": [
        _site("fr", "municipality", "Commune de Valfictif", "Place du Village 2, 1999 Valfictif", "024 000 21 21",
              "greffe@valfictif.example", "www.valfictif.example", [
                  P("index", "Accueil", "Bienvenue à Valfictif", [
                      "Valfictif compte quelque 3100 habitantes et habitants, entre vignes et forêts.",
                      "Le guichet communal est ouvert du lundi au vendredi de 8 h 30 à 11 h 30, le jeudi aussi de 14 h à 18 h."]),
                  P("administration", "Administration", "Administration communale", [
                      "L'administration se trouve à la Maison de commune, Place du Village 2."],
                    ["Greffe municipal", "Contrôle des habitants", "Bourse communale", "Service technique"]),
                  P("dechets", "Déchets", "Déchets et recyclage", [
                      "Les ordures ménagères sont ramassées chaque mardi. Les sacs taxés doivent être déposés le matin même, avant 7 h."],
                    ["Déchets verts : un vendredi sur deux", "Papier et carton : premier mercredi du mois",
                     "Déchetterie : samedi de 9 h à 12 h"]),
                  P("impots", "Impôts", "Impôts", [
                      "La déclaration d'impôt 2025 doit être déposée d'ici au 15 mars 2026.",
                      "Une prolongation de délai peut être demandée en ligne, gratuitement, jusqu'au 30 septembre."]),
                  P("constructions", "Constructions", "Police des constructions", [
                      "Les demandes de permis de construire sont à déposer au service technique en trois exemplaires.",
                      "Les petites constructions de moins de 10 m² doivent simplement être annoncées."]),
                  P("loisirs", "Loisirs", "Loisirs et sociétés locales", [
                      "Une trentaine de sociétés locales animent la vie du village, du chœur mixte au club de pétanque."],
                    ["Piscine couverte", "Ludothèque", "Parcours Vita de la Côte"]),
              ],
              P("chiens", "Taxe des chiens", "Taxe des chiens 2026", [
                  "Tout chien doit être annoncé au contrôle des habitants avant le 28 février.",
                  "La taxe annuelle s'élève à CHF 100.– ; les chiens d'assistance en sont exonérés."]),
              "Taxe des chiens : délai au 28 février"),
        _site("fr", "school", "École de Valfictif", "Rue de l'Église 15, 1999 Valfictif", "024 000 40 50",
              "secretariat@ecole-valfictif.example", "www.ecole-valfictif.example", [
                  P("index", "Accueil", "École de Valfictif", [
                      "Quelque 260 élèves fréquentent nos classes de la 1re à la 8e année.",
                      "Le secrétariat répond du lundi au vendredi de 7 h 30 à 11 h 30."]),
                  P("horaires", "Horaires", "Horaires des cours", [
                      "Les cours ont lieu de 8 h à 11 h 45 le matin, puis de 13 h 30 à 15 h 15 l'après-midi.",
                      "Le mercredi après-midi est libre pour toutes les classes."]),
                  P("vacances", "Vacances", "Vacances scolaires 2026-2027", [
                      "Le calendrier est valable pour tous les degrés."],
                    ["Automne : du 10 au 25 octobre 2026", "Hiver : du 24 décembre 2026 au 10 janvier 2027",
                     "Relâches : du 13 au 21 février 2027", "Printemps : du 3 au 18 avril 2027"]),
                  P("parascolaire", "Parascolaire", "Accueil parascolaire", [
                      "L'accueil parascolaire prend en charge les enfants dès 7 h et jusqu'à 18 h 30, repas de midi compris."]),
                  P("devoirs", "Devoirs surveillés", "Devoirs surveillés", [
                      "Les devoirs surveillés ont lieu le lundi, le mardi et le jeudi de 15 h 30 à 16 h 30.",
                      "Inscription auprès du secrétariat jusqu'au 15 septembre."]),
                  P("parents", "Parents", "Conseil d'établissement", [
                      "Le conseil d'établissement réunit parents, enseignants et autorités quatre fois par année."]),
              ],
              P("camp-ski", "Camp de ski", "Camp de ski 2027", [
                  "Le camp de ski des élèves de 7e et 8e aura lieu du 8 au 12 février 2027 aux Mayens-Fictifs.",
                  "La participation des parents s'élève à CHF 140.–."]),
              "Camp de ski 2027 : informations aux parents"),
        _site("fr", "library", "Bibliothèque de Bourg-Modèle", "Rue des Granges 4, 1998 Bourg-Modèle", "026 000 18 18",
              "biblio@bourg-modele.example", "www.biblio-bourg-modele.example", [
                  P("index", "Accueil", "Bibliothèque de Bourg-Modèle", [
                      "Plus de 30 000 livres, BD, films et jeux à découvrir sur deux étages."]),
                  P("horaires", "Horaires", "Horaires d'ouverture", [
                      "Pendant les vacances scolaires, la bibliothèque ferme le samedi."],
                    ["Mardi : 14 h – 18 h 30", "Mercredi : 10 h – 12 h et 14 h – 18 h 30",
                     "Jeudi : 14 h – 19 h", "Samedi : 9 h 30 – 13 h"]),
                  P("inscription", "S'inscrire", "Inscription et tarifs", [
                      "L'abonnement annuel coûte CHF 25.–.",
                      "Il est gratuit jusqu'à 18 ans et pour les personnes en formation."]),
                  P("collections", "Collections", "Nos collections", [
                      "Romans, documentaires, bandes dessinées, livres en gros caractères et livres audio : tout s'emprunte pour quatre semaines."]),
                  P("numerique", "Offre numérique", "Offre numérique", [
                      "Votre carte de lecteur vous donne accès 24 heures sur 24 à des milliers de livres numériques."]),
                  P("animations", "Animations", "Animations", [
                      "Toutes nos animations sont gratuites."],
                    ["Heure du conte (dès 4 ans) : mercredi 4 novembre, 15 h",
                     "Club de lecture adultes : jeudi 19 novembre, 19 h", "Atelier BD : samedi 28 novembre, 10 h"]),
              ],
              P("troc-livres", "Troc de livres", "Troc de livres", [
                  "Le samedi 5 décembre, apportez vos livres en bon état et échangez-les contre d'autres sur le parvis de la bibliothèque.",
                  "Les livres restants seront offerts à la ludothèque."]),
              "5 décembre : grand troc de livres"),
        _site("fr", "utility", "Service des eaux d'Exempleval", "Chemin des Vignes 7, 1997 Exempleval", "024 000 33 40",
              "eaux@exempleval.example", "www.eaux-exempleval.example", [
                  P("index", "Accueil", "Service des eaux d'Exempleval", [
                      "Nous distribuons chaque jour environ 1500 m³ d'eau potable dans la commune."]),
                  P("qualite", "Qualité de l'eau", "Qualité de l'eau", [
                      "Notre eau provient à 60 % de sources et à 40 % de la nappe phréatique.",
                      "Sa dureté totale est de 22 °f (eau moyennement dure)."]),
                  P("raccordement", "Raccordement", "Nouveau raccordement", [
                      "Toute demande de raccordement doit nous parvenir au moins deux mois avant le début des travaux."]),
                  P("tarifs", "Tarifs", "Tarifs 2026", [
                      "Les tarifs ont été adoptés par le Conseil général le 12 juin 2025."],
                    ["Prix de l'eau : CHF 1.80 le m³", "Taxe de base : CHF 85.– par an et par compteur",
                     "Location du compteur : CHF 30.– par an"]),
                  P("pannes", "Pannes", "Signaler une panne", [
                      "En cas de fuite ou de coupure d'eau, notre service de piquet est atteignable jour et nuit au 024 000 33 44."]),
                  P("qui-sommes-nous", "Qui sommes-nous", "Qui sommes-nous ?", [
                      "Le service des eaux dépend de la Municipalité d'Exempleval et emploie cinq collaborateurs."]),
              ],
              P("releve-compteurs", "Relevé des compteurs", "Relevé des compteurs", [
                  "Du 9 au 20 novembre, nos releveurs passeront dans tous les quartiers.",
                  "En cas d'absence, une carte-réponse sera déposée dans votre boîte aux lettres."]),
              "Dès le 9 novembre : relevé des compteurs"),
        _site("fr", "transport", "Transports publics de Valfictif", "Avenue de la Gare 10, 1999 Valfictif", "024 000 60 60",
              "info@tpv.example", "www.tpv.example", [
                  P("index", "Accueil", "Transports publics de Valfictif", [
                      "Cinq lignes de bus desservent Valfictif et les villages voisins toutes les vingt minutes."]),
                  P("horaires", "Horaires", "Horaires", [
                      "Le nouvel horaire entre en vigueur le 13 décembre 2026.",
                      "La ligne 2 dessert désormais la zone artisanale des Prés."]),
                  P("billets", "Billets", "Billets et abonnements", [
                      "Les billets s'achètent aux distributeurs, auprès du chauffeur ou dans l'application."],
                    ["Billet simple zone 20 : CHF 3.–", "Carte journalière : CHF 9.–",
                     "Abonnement mensuel adulte : CHF 70.–"]),
                  P("arrets", "Arrêts", "Arrêts et accessibilité", [
                      "Trente des trente-huit arrêts sont accessibles de plain-pied ; les autres seront adaptés d'ici 2028."]),
                  P("objets-trouves", "Objets trouvés", "Objets trouvés", [
                      "Les objets oubliés dans nos véhicules peuvent être retirés au guichet de la gare, du lundi au vendredi de 8 h à 12 h."]),
                  P("entreprise", "Entreprise", "L'entreprise", [
                      "Nonante collaboratrices et collaborateurs transportent chaque année près de quatre millions de voyageurs."]),
              ],
              P("noctambus", "Noctambus", "Noctambus du week-end", [
                  "Les nuits de vendredi à samedi et de samedi à dimanche, le Noctambus N2 part de la gare à 1 h 10 et à 2 h 40.",
                  "Le tarif normal s'applique, sans supplément de nuit."]),
              "Nouveau : le Noctambus du week-end"),
        _site("fr", "tourism", "Office du tourisme du Val-Modèle", "Place du Marché 1, 1998 Bourg-Modèle", "026 000 90 90",
              "info@val-modele.example", "www.val-modele.example", [
                  P("index", "Accueil", "Bienvenue au Val-Modèle", [
                      "Entre lac et montagne, le Val-Modèle propose 120 km de sentiers balisés et une vieille ville médiévale."]),
                  P("randonnees", "Randonnées", "Randonnées", [
                      "Tous les itinéraires partent de la place du Marché."],
                    ["Tour du lac : 2 h 30, facile", "Sentier des crêtes : 5 h, difficile",
                     "Balade des moulins : 1 h 15, facile"]),
                  P("hebergement", "Hébergement", "Hébergement", [
                      "Hôtels, chambres d'hôtes et camping : 18 établissements vous accueillent toute l'année."]),
                  P("patrimoine", "Patrimoine", "Patrimoine", [
                      "La vieille ville de Bourg-Modèle conserve ses remparts du XIVe siècle et un moulin encore en activité."]),
                  P("acces", "Accès", "Accès", [
                      "Depuis la gare de Bourg-Modèle, le bus 12 rejoint le centre du val en 20 minutes, toutes les demi-heures."]),
                  P("office", "Office du tourisme", "Office du tourisme", [
                      "Notre bureau de la place du Marché est ouvert tous les jours de 9 h à 12 h et de 14 h à 17 h 30."]),
              ],
              P("fete-vendanges", "Fête des vendanges", "Fête des vendanges", [
                  "Les 2 et 3 octobre, cortège, caveaux ouverts et marché du terroir animent la vieille ville.",
                  "Le cortège part à 14 h de la porte du Lac."]),
              "2 et 3 octobre : Fête des vendanges"),
    ],
    "it": [
        _site("it", "municipality", "Comune di Esempiano", "Piazza Grande 3, 6999 Esempiano", "091 000 12 12",
              "cancelleria@esempiano.example", "www.esempiano.example", [
                  P("index", "Home", "Benvenuti a Esempiano", [
                      "Esempiano conta circa 2800 abitanti e si trova tra il lago e le prime pendici della valle.",
                      "La cancelleria comunale è aperta dal lunedì al venerdì dalle 8.30 alle 11.30."]),
                  P("amministrazione", "Amministrazione", "Amministrazione comunale", [
                      "Gli uffici si trovano nella Casa comunale in Piazza Grande."],
                    ["Cancelleria comunale", "Controllo abitanti", "Servizio finanze", "Ufficio tecnico"]),
                  P("rifiuti", "Rifiuti", "Rifiuti e riciclaggio", [
                      "I rifiuti solidi urbani vengono raccolti ogni martedì. I sacchi ufficiali vanno esposti la mattina stessa entro le 7.00."],
                    ["Scarti vegetali: ogni secondo venerdì", "Carta e cartone: primo mercoledì del mese",
                     "Ecocentro: sabato dalle 9.00 alle 12.00"]),
                  P("imposte", "Imposte", "Imposte", [
                      "La dichiarazione d'imposta 2025 va inoltrata entro il 30 aprile 2026.",
                      "È possibile chiedere una proroga online fino al 31 ottobre."]),
                  P("edilizia", "Edilizia", "Edilizia privata", [
                      "Le domande di costruzione vanno presentate all'ufficio tecnico in tre copie.",
                      "Per piccoli interventi basta la notifica."]),
                  P("tempo-libero", "Tempo libero", "Tempo libero e associazioni", [
                      "Una ventina di associazioni animano il paese, dalla filarmonica alla società di bocce."],
                    ["Lido comunale", "Ludoteca", "Percorso vita al Ronco"]),
              ],
              P("cani", "Tassa sui cani", "Tassa sui cani 2026", [
                  "I cani vanno annunciati al controllo abitanti entro fine febbraio.",
                  "La tassa annuale ammonta a CHF 80.–; i cani guida ne sono esenti."]),
              "Tassa sui cani: termine a fine febbraio"),
        _site("it", "school", "Scuola di Esempiano", "Via ai Monti 6, 6999 Esempiano", "091 000 40 41",
              "direzione@scuola-esempiano.example", "www.scuola-esempiano.example", [
                  P("index", "Home", "Scuola di Esempiano", [
                      "Circa 220 allievi frequentano la nostra scuola dell'infanzia e la scuola elementare.",
                      "La direzione risponde dal lunedì al venerdì dalle 8.00 alle 11.30."]),
                  P("orari", "Orari", "Orari delle lezioni", [
                      "Le lezioni iniziano alle 8.15 e terminano alle 11.45; il pomeriggio dalle 13.30 alle 15.50.",
                      "Il mercoledì pomeriggio è libero."]),
                  P("calendario", "Calendario", "Calendario scolastico 2026/27", [
                      "Il calendario vale per tutte le sezioni."],
                    ["Vacanze autunnali: 31 ottobre – 8 novembre 2026", "Vacanze natalizie: 24 dicembre 2026 – 6 gennaio 2027",
                     "Carnevale: 6 – 14 febbraio 2027", "Vacanze pasquali: 27 marzo – 5 aprile 2027"]),
                  P("mensa", "Mensa", "Mensa e doposcuola", [
                      "La mensa è aperta dal lunedì al venerdì.",
                      "Il doposcuola accoglie i bambini fino alle 18.00."]),
                  P("trasporto", "Trasporto allievi", "Trasporto allievi", [
                      "Lo scuolabus parte da Vicolo del Forno alle 7.50 e riporta gli allievi a casa dopo le lezioni."]),
                  P("genitori", "Genitori", "Assemblea dei genitori", [
                      "L'assemblea dei genitori organizza la festa di fine anno e la merenda sana del giovedì."]),
              ],
              P("settimana-bianca", "Settimana bianca", "Settimana bianca 2027", [
                  "La settimana bianca delle classi quarte e quinte si svolgerà dal 15 al 19 febbraio 2027 ai Monti di Valfittizia.",
                  "Il contributo dei genitori è di CHF 130.–."]),
              "Settimana bianca 2027: informazioni per i genitori"),
        _site("it", "library", "Biblioteca di Modellina", "Vicolo del Forno 2, 6998 Modellina", "091 000 25 25",
              "biblioteca@modellina.example", "www.biblioteca-modellina.example", [
                  P("index", "Home", "Biblioteca di Modellina", [
                      "Oltre 20 000 libri, riviste e audiolibri per tutte le età, nel cuore del nucleo."]),
                  P("orari", "Orari", "Orari di apertura", [
                      "Durante le vacanze scolastiche il sabato la biblioteca resta chiusa."],
                    ["Martedì: 14.00 – 18.30", "Mercoledì: 9.00 – 12.00 e 14.00 – 18.30",
                     "Venerdì: 14.00 – 19.00", "Sabato: 9.30 – 12.30"]),
                  P("iscrizione", "Iscrizione", "Iscrizione e tariffe", [
                      "La tessera annuale costa CHF 20.–; per bambini e ragazzi fino a 18 anni è gratuita.",
                      "Il prestito dura quattro settimane."]),
                  P("raccolte", "Raccolte", "Le nostre raccolte", [
                      "Romanzi, saggi, fumetti, libri in caratteri grandi e una sezione dedicata alla storia della regione."]),
                  P("digitale", "Biblioteca digitale", "Biblioteca digitale", [
                      "Con la tessera potete prendere in prestito e-book e audiolibri a qualsiasi ora."]),
                  P("eventi", "Eventi", "Eventi", [
                      "Tutti gli eventi sono gratuiti."],
                    ["Ora del racconto (dai 4 anni): mercoledì 4 novembre, ore 15.00",
                     "Incontro con l'autrice Giulia Fittizi: giovedì 19 novembre, ore 20.00",
                     "Laboratorio di fumetto: sabato 28 novembre, ore 10.00"]),
              ],
              P("scambio-libri", "Scambio di libri", "Scambio di libri", [
                  "Sabato 5 dicembre portate i libri che avete già letto e scambiateli sotto i portici della biblioteca.",
                  "I libri rimasti saranno donati alla ludoteca."]),
              "Sabato 5 dicembre: scambio di libri"),
        _site("it", "utility", "Azienda acqua potabile Valfittizia", "Via Cantonale 9, 6997 Valfittizia", "091 000 44 50",
              "acqua@valfittizia.example", "www.acqua-valfittizia.example", [
                  P("index", "Home", "Azienda acqua potabile Valfittizia", [
                      "Ogni giorno forniamo circa 1200 m³ di acqua potabile a economie domestiche e aziende."]),
                  P("qualita", "Qualità dell'acqua", "Qualità dell'acqua", [
                      "La nostra acqua proviene per l'80 % da sorgenti e per il 20 % dalla falda.",
                      "La durezza totale è di 12 °f (acqua dolce)."]),
                  P("allacciamenti", "Allacciamenti", "Nuovo allacciamento", [
                      "La domanda di allacciamento va inoltrata almeno due mesi prima dell'inizio dei lavori."]),
                  P("tariffe", "Tariffe", "Tariffe 2026", [
                      "Le tariffe sono state approvate dal Consiglio comunale il 15 giugno 2025."],
                    ["Prezzo dell'acqua: CHF 1.40 al m³", "Tassa base: CHF 75.– all'anno per contatore",
                     "Noleggio contatore: CHF 25.– all'anno"]),
                  P("guasti", "Guasti", "Segnalare un guasto", [
                      "In caso di perdite o mancanza d'acqua il servizio di picchetto risponde giorno e notte allo 091 000 44 55."]),
                  P("chi-siamo", "Chi siamo", "Chi siamo", [
                      "L'azienda è un servizio del Comune di Valfittizia e conta quattro collaboratori."]),
              ],
              P("lettura-contatori", "Lettura dei contatori", "Lettura dei contatori", [
                  "Dal 9 al 20 novembre i nostri addetti leggeranno i contatori in tutti i quartieri.",
                  "In caso di assenza troverete una cartolina nella bucalettere."]),
              "Dal 9 novembre: lettura dei contatori"),
        _site("it", "transport", "Trasporti pubblici di Modellina", "Via alla Stazione 14, 6998 Modellina", "091 000 70 70",
              "info@tpm.example", "www.tpm.example", [
                  P("index", "Home", "Trasporti pubblici di Modellina", [
                      "Quattro linee di bus collegano Modellina e le frazioni ogni 15 minuti."]),
                  P("orari", "Orari", "Orari", [
                      "Il nuovo orario entra in vigore il 13 dicembre 2026.",
                      "La linea 4 serve ora anche l'ospedale."]),
                  P("biglietti", "Biglietti", "Biglietti e abbonamenti", [
                      "I biglietti si acquistano ai distributori, a bordo o con l'app."],
                    ["Biglietto singolo zona 10: CHF 2.60", "Carta giornaliera: CHF 7.80",
                     "Abbonamento mensile adulti: CHF 62.–"]),
                  P("fermate", "Fermate", "Fermate", [
                      "Tutte le 31 fermate dispongono di pannelli con gli orari in tempo reale; 26 sono accessibili senza gradini."]),
                  P("oggetti-smarriti", "Oggetti smarriti", "Oggetti smarriti", [
                      "Gli oggetti dimenticati sui nostri bus si possono ritirare allo sportello in Piazza Grande, dal lunedì al venerdì dalle 8.00 alle 12.00."]),
                  P("azienda", "Azienda", "L'azienda", [
                      "Ottanta collaboratrici e collaboratori trasportano ogni anno circa tre milioni di passeggeri."]),
              ],
              P("bus-notturno", "Bus notturno", "Bus notturno del fine settimana", [
                  "Nelle notti di venerdì e sabato il bus notturno N3 parte da Piazza Grande alle 1.20 e alle 2.40.",
                  "Vale la tariffa normale, senza supplemento notturno."]),
              "Novità: bus notturno nel fine settimana"),
        _site("it", "tourism", "Ente turistico Valfittizia", "Piazza Grande 1, 6997 Valfittizia", "091 000 88 88",
              "info@valfittizia-turismo.example", "www.valfittizia-turismo.example", [
                  P("index", "Home", "Benvenuti in Valfittizia", [
                      "Una valle di boschi di castagni, grotti e villaggi di pietra, a mezz'ora dal lago."]),
                  P("escursioni", "Escursioni", "Escursioni", [
                      "Tutti i sentieri partono dalla piazza del paese."],
                    ["Sentiero dei mulini: 2 ore, facile", "Via dei monti: 4 ore e 30, media",
                     "Traversata delle creste: 6 ore, impegnativa"]),
                  P("alloggi", "Alloggi", "Alloggi", [
                      "Alberghi, ostelli e rustici ristrutturati: 16 strutture con circa 350 posti letto."]),
                  P("grotti", "Grotti", "Grotti e cucina locale", [
                      "Polenta, formaggini e vino nostrano: una dozzina di grotti vi aspettano da aprile a ottobre."]),
                  P("come-arrivare", "Come arrivare", "Come arrivare", [
                      "Dalla stazione di Modellina il bus 31 raggiunge il fondovalle in 30 minuti, ogni ora."]),
                  P("ufficio", "Ufficio turistico", "Ufficio turistico", [
                      "Il nostro sportello in Piazza Grande è aperto tutti i giorni dalle 9.00 alle 12.00 e dalle 14.00 alle 17.30."]),
              ],
              P("castagnata", "Castagnata", "Castagnata d'autunno", [
                  "Domenica 18 ottobre caldarroste, musica popolare e mercatino dei prodotti locali in piazza.",
                  "La festa inizia alle 11.00 e si tiene anche in caso di pioggia sotto il porticato."]),
              "Domenica 18 ottobre: castagnata"),
    ],
}

SERVICE_PAGES = {
    "de": [("impressum", "imprint", "Verantwortlich für den Inhalt dieser Website: {org}, {street}."),
           ("datenschutz", "privacy", "Wir bearbeiten Personendaten nur, soweit dies für unsere Aufgaben nötig ist. Diese Website setzt keine Tracking-Cookies."),
           ("barrierefreiheit", "a11y", "Wir möchten, dass alle Menschen diese Website nutzen können. Hinweise auf Barrieren nehmen wir gerne unter {mail} entgegen."),
           ("kontakt", "contact", "{org}, {street}. Telefon {phone}, E-Mail {mail}.")],
    "fr": [("mentions-legales", "imprint", "Responsable du contenu de ce site : {org}, {street}."),
           ("protection-donnees", "privacy", "Nous ne traitons des données personnelles que dans la mesure nécessaire à nos tâches. Ce site n'utilise aucun cookie de suivi."),
           ("accessibilite", "a11y", "Nous souhaitons que chacun puisse utiliser ce site. Signalez-nous tout obstacle à l'adresse {mail}."),
           ("contact", "contact", "{org}, {street}. Téléphone {phone}, courriel {mail}.")],
    "it": [("note-legali", "imprint", "Responsabile dei contenuti di questo sito: {org}, {street}."),
           ("protezione-dati", "privacy", "Trattiamo dati personali solo nella misura necessaria ai nostri compiti. Questo sito non usa cookie di tracciamento."),
           ("accessibilita", "a11y", "Desideriamo che tutti possano usare questo sito. Segnalateci eventuali barriere all'indirizzo {mail}."),
           ("contatti", "contact", "{org}, {street}. Telefono {phone}, e-mail {mail}.")],
}


def service_pages(site):
    """Return list of P() dicts for imprint / privacy / accessibility / contact of a site."""
    lang = site["lang"]
    out = []
    for slug, key, txt in SERVICE_PAGES[lang]:
        label = UI[lang][key]
        out.append(P(slug, label, label, [txt.format(org=site["org"], street=site["street"],
                                                   phone=site["phone"], mail=site["mail"])]))
    return out


def href(slug: str) -> str:
    return "index.html" if slug == "index" else f"{slug}.html"


SITE_CSS = (
    ".vh{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}"
    ".skip{position:absolute;left:-9999px;top:4px;background:#ffffff;color:#000000;padding:6px 10px}"
    ".skip:focus{left:8px;z-index:20}"
    ".cols{display:grid;grid-template-columns:minmax(150px,210px) 1fr;gap:24px;max-width:1100px;margin:0 auto;padding:0 16px}"
    ".cols main{margin:0;max-width:none;padding:24px 0}"
    ".side-nav ul{list-style:none;margin:24px 0;padding:0 0 0 10px;border-left:3px solid #8a96a0}"
    ".side-nav li{margin:0 0 8px}.side-nav li ul{margin:6px 0 4px;border-left:0;font-size:.95rem}"
    ".band{padding:8px 24px;border-bottom:1px solid #c9d3d8}"
    ".band ul{list-style:none;margin:0;padding:0;display:flex;flex-wrap:wrap;gap:18px}"
    ".band li ul{display:inline-flex;gap:10px;margin-left:8px;font-size:.92rem}"
    "[aria-current=page]{font-weight:700;text-decoration:underline}"
    ".crumbs ol{list-style:none;display:flex;flex-wrap:wrap;gap:6px;padding:0;margin:0 0 12px;font-size:.9rem}"
    ".crumbs li+li::before{content:'›';margin-right:6px}"
    ".foot-links ul{list-style:none;display:flex;flex-wrap:wrap;gap:16px;padding:0;margin:8px 0}"
    ".tools{display:flex;gap:12px;align-items:center;flex-wrap:wrap}"
    ".search{display:flex;gap:6px;align-items:center}.search label{margin:0;font-weight:400}"
    ".hits{flex-basis:100%}"
    ".teasers{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;padding:0;list-style:none}"
    ".teasers li{border:1px solid #c9d3d8;border-radius:8px;padding:10px}"
    ".lang-switch ul{list-style:none;display:flex;gap:8px;margin:0;padding:0}"
)


def ul_links(items, current=None, mode="link", sub=None):
    """items: [(label, href)]; mode: 'link' (aria-current on the link), 'text' (current as span), None.
    sub: optional {href: inner_ul_html} inserted inside the matching <li>."""
    lis = []
    for label, h in items:
        extra = (sub or {}).get(h, "")
        if h == current and mode == "text":
            lis.append(f'<li><span aria-current="page">{esc(label)}</span>{extra}</li>')
        elif h == current and mode == "link":
            lis.append(f'<li><a href="{esc(h)}" aria-current="page">{esc(label)}</a>{extra}</li>')
        else:
            lis.append(f'<li><a href="{esc(h)}">{esc(label)}</a>{extra}</li>')
    return "<ul>" + "".join(lis) + "</ul>"


def nav_block(items, label, *, cls="site-nav", current=None, mode="link", sub=None):
    return f'<nav class="{cls}" aria-label="{esc(label)}">{ul_links(items, current, mode, sub)}</nav>'


def brand(org, href_="index.html"):
    return f'<a class="site-name" href="{esc(href_)}">{esc(org)}</a>'


def main_content(pg, extra=""):
    out = [f"<h1>{esc(pg['h1'])}</h1>"]
    out += [f"<p>{esc(p)}</p>" for p in pg["p"]]
    if pg["li"]:
        out.append("<ul>" + "".join(f"<li>{esc(x)}</li>" for x in pg["li"]) + "</ul>")
    if extra:
        out.append(extra)
    return "\n".join(out)


def search_box(lang, idx, *, fid="suche", label=None, button=None, button_html=None, results=True):
    """Working client-side search. idx: [[title, href, keywords], ...]; results rendered in-page."""
    ui = UI[lang]
    label = label or ui["search_label"]
    button_html = button_html or f'<button type="submit">{esc(button or ui["search_btn"])}</button>'
    qid, oid = f"{fid}-q", f"{fid}-out"
    form = (f'<form class="search" id="{fid}" role="search" aria-label="{esc(ui["search_region"])}" action="#">'
            f'<label class="vh" for="{qid}">{esc(label)}</label><input type="search" id="{qid}" name="q">'
            f'{button_html}</form>')
    if not results:
        return form
    out = f'<div class="hits" id="{oid}" role="status"></div>'
    js = ("(function(){var IDX=" + json.dumps(idx, ensure_ascii=False) + ";"
          f"var f=document.getElementById('{fid}');var q=document.getElementById('{qid}');"
          f"var out=document.getElementById('{oid}');"
          "f.addEventListener('submit',function(e){e.preventDefault();var t=q.value.trim().toLowerCase();"
          "out.textContent='';if(!t){return;}var ul=document.createElement('ul');"
          "IDX.forEach(function(r){if((r[0]+' '+r[2]).toLowerCase().indexOf(t)>-1){"
          "var li=document.createElement('li');var a=document.createElement('a');a.href=r[1];"
          "a.textContent=r[0];li.appendChild(a);ul.appendChild(li);}});"
          "if(ul.childNodes.length){out.appendChild(ul);}else{out.textContent=" + json.dumps(ui["no_hits"], ensure_ascii=False) + ";}});})();")
    return form + out + f"<script>{js}</script>"


def search_index(pages):
    """Build [[h1, href, keywords]] from P() dicts."""
    out = []
    for pg in pages:
        words = " ".join([pg["nav"]] + pg["p"] + pg["li"])
        out.append([pg["h1"], href(pg["slug"]), words[:220]])
    return out


def site_doc(lang, title, theme, *, top=(), main="", aside=None, bottom=(), css="", head="",
             html_lang=None):
    parts = list(top)
    m = f'<main id="main">\n{main}\n</main>'
    if aside is not None:
        parts.append(f'<div class="cols">{aside}{m}</div>')
    else:
        parts.append(m)
    parts += list(bottom)
    return page(html_lang or SITE_LANG_TAG[lang], title, "\n".join(parts), theme=theme,
                css=SITE_CSS + css, head=head)


def skip_link(lang):
    return f'<a class="skip" href="#main">{esc(UI[lang]["skip"])}</a>'


def title_of(pg, site, sep=" – "):
    if pg["slug"] == "index":
        return site["org"]
    return f"{pg['h1']}{sep}{site['org']}"


def footer_simple(site, links_html=""):
    return (f'<footer class="site-footer"><p>{esc(site["org"])} · {esc(site["street"])} · '
            f'{esc(UI[site["lang"]]["phone"])} {esc(site["phone"])}</p>{links_html}</footer>')


def site_by_kind(lang, kind):
    for s in SITES[lang]:
        if s["kind"] == kind:
            return s
    raise KeyError((lang, kind))


LAYOUTS = ("top", "side", "band", "bare")


def nav_items(site, pages=None):
    pages = site["pages"] if pages is None else pages
    return [(p["nav"], href(p["slug"])) for p in pages]


def content_page(site, pg, title, theme, layout="top", *, main_html=None, css="", head="", current_mode="link"):
    """A single content page of ``site`` with the given chrome layout ("top", "side", "band", "bare")."""
    lang = site["lang"]
    ui = UI[lang]
    items = nav_items(site)
    cur = href(pg["slug"])
    main_html = main_html if main_html is not None else main_content(pg)
    if layout == "bare":
        return site_doc(lang, title, theme, main=main_html, css=css, head=head)
    nav = nav_block(items, ui["nav"], current=cur, mode=current_mode,
                    cls={"top": "site-nav", "side": "side-nav", "band": "band"}[layout])
    top = [skip_link(lang)]
    if layout == "top":
        top.append(f'<header class="site-header">{brand(site["org"])}{nav}</header>')
        return site_doc(lang, title, theme, top=top, main=main_html, bottom=[footer_simple(site)], css=css, head=head)
    top.append(f'<header class="site-header">{brand(site["org"])}</header>')
    if layout == "band":
        top.append(nav)
        return site_doc(lang, title, theme, top=top, main=main_html, bottom=[footer_simple(site)], css=css, head=head)
    return site_doc(lang, title, theme, top=top, main=main_html, aside=nav, bottom=[footer_simple(site)], css=css, head=head)


def get_page(site, slug):
    for p in site["pages"] + [site["deep"]]:
        if p["slug"] == slug:
            return p
    raise KeyError(slug)
