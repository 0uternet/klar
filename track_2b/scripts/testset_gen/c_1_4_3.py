"""1.4.3 Contrast (Minimum) — 28 cases (protocol rules 1.4.3/F1–F5, P1, T1–T5, C1–C2).

All ratios are computed with common.contrast() and asserted against the thresholds at build time.
"""
from common import *
import random
from _visual_util import compose, doc, img, org_of, host_of, phone, ratio

CRITERION = "1.4.3"


def chk(fg, bg, lo=None, hi=None):
    r = contrast(fg, bg)
    if lo is not None:
        assert r >= lo, (fg, bg, r)
    if hi is not None:
        assert r < hi, (fg, bg, r)
    return ratio(fg, bg)


def mk(rng, lang, kind, title, main, expected, target, rule, notes, *, trap=False, alt_expected=None,
       difficulty="medium", css="", theme=None, org=None, head="", **kw):
    org = org or org_of(rng, lang, kind)
    main = main.replace("{ORG}", esc(org)).replace("{HOST}", host_of(org)).replace("{PHONE}", phone(rng))
    body, lcss = compose(rng, lang, org, main, kind=kind, **kw)
    html = doc(rng, lang, title, org, body, lcss + css, theme=theme, head=head)
    return Case(CRITERION, lang, expected, html=html, target=target, rule=rule, notes=notes, trap=trap,
                alt_expected=alt_expected, difficulty=difficulty)


def flat_bg(color, line):
    """Flat 'texture' background: one colour plus a thin wave at the very bottom edge."""
    d = "M0 192 " + " ".join(f"Q{x + 30} {186 if (x // 60) % 2 == 0 else 198} {x + 60} 192" for x in range(0, 1200, 60))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="200" viewBox="0 0 1200 200" '
            f'preserveAspectRatio="none"><rect width="1200" height="200" fill="{color}"/>'
            f'<path d="{d}" fill="none" stroke="{line}" stroke-width="3"/></svg>')


def band_bg(top, bottom, split=0.5, end=0.72):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="30" viewBox="0 0 400 30" '
            f'preserveAspectRatio="none"><defs><linearGradient id="v" x1="0" x2="0" y1="0" y2="1">'
            f'<stop offset="0" stop-color="{top}"/><stop offset="{split}" stop-color="{top}"/>'
            f'<stop offset="{end}" stop-color="{bottom}"/><stop offset="1" stop-color="{bottom}"/>'
            f'</linearGradient></defs><rect width="400" height="30" fill="url(#v)"/>'
            f'<circle cx="340" cy="8" r="5" fill="{top}" opacity="0.6"/></svg>')


def scene_sky(kind, seed):
    """Sky colour chosen by common.scene() for (kind, seed) — replicates its first rng draw."""
    r = random.Random(f"scene-{kind}-{seed}")
    return pick(r, ["#bfe3f2", "#cde8f6", "#f6dcc4", "#d7e9d2", "#e4ddf2"])


def logo_pale(word1, word2, col):
    inner = (f'<g fill="none" stroke="{col}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
             f'transform="translate(6 10) scale(1.3)">{ICONS["star"]}</g>'
             f'<text x="50" y="26" font-family="Georgia, serif" font-size="18" font-weight="700" fill="{col}">{esc(word1)}</text>'
             f'<text x="50" y="46" font-family="Georgia, serif" font-size="13" fill="{col}">{esc(word2)}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="230" height="56" viewBox="0 0 230 56">'
            f'<rect width="230" height="56" fill="#ffffff"/>{inner}</svg>')


# ---------------------------------------------------------------------------
# FAILED
# ---------------------------------------------------------------------------

def f1_smallprint_de(rng):
    t = pick_theme(rng)
    fg = "#8a8a8a"
    r = chk(fg, t["bg"], hi=4.5)
    main = ("<h1>Wohnsitzbestätigung bestellen</h1><p>Die Bestätigung wird Ihnen innert zwei Arbeitstagen per "
            "Post zugestellt. Gebühr: CHF 20.–, zahlbar mit beiliegendem Einzahlungsschein.</p>"
            "<form action=\"bestellung-danke.html\" method=\"post\"><label for=\"name\">Name und Vorname</label>"
            "<input type=\"text\" id=\"name\" name=\"name\"><label for=\"geb\">Geburtsdatum</label>"
            "<input type=\"text\" id=\"geb\" name=\"geb\"><p><button type=\"submit\">Bestellen</button></p>"
            "<p id=\"datenschutz\" class=\"kleingedruckt\">Ihre Angaben werden ausschliesslich zur Bearbeitung "
            "Ihrer Bestellung verwendet und nicht an Dritte weitergegeben.</p></form>")
    css = f".kleingedruckt{{font-size:14px;color:{fg}}}"
    return mk(rng, "de", "gemeinde", "Wohnsitzbestätigung", main, "failed", "#datenschutz", "1.4.3/F1",
              f"The 14 px privacy note in {fg} has {r}:1 against the page background {t['bg']} (< 4.5:1).",
              css=css, theme=t, difficulty="easy")


def f1_button_fr(rng):
    fg, bg = "#ffffff", "#e07a2e"
    r = chk(fg, bg, hi=4.5)
    main = ("<h1>Fête au village 2027</h1><p>La fête aura lieu les 28 et 29 août sur la place du Village. Pour "
            "tenir les stands, monter les tentes et servir au bar, nous cherchons une soixantaine de "
            "bénévoles.</p><p><a class=\"bouton\" href=\"benevoles-inscription.html\">Devenir bénévole</a></p>"
            "<p>Chaque bénévole reçoit un bon repas et le t-shirt de la fête.</p>")
    css = (f".bouton{{display:inline-block;background:{bg};color:{fg};padding:10px 18px;border-radius:6px;"
           "text-decoration:none;font-size:16px;font-weight:600}")
    return mk(rng, "fr", "gemeinde", "Fête au village", main, "failed", ".bouton", "1.4.3/F1",
              f"The 16 px semibold button text (white on {bg}) has only {r}:1, below 4.5:1 for normal text.",
              css=css, difficulty="easy")


def f1_badge_it(rng):
    fg, bg = "#2a9d8f", "#e8f1f5"
    r = chk(fg, bg, hi=4.5)
    main = ("<h1>Notizie dalla biblioteca</h1><ul class=\"notizie\">"
            "<li><span class=\"badge\">Novità</span> Prestito di e-book: da novembre anche per i ragazzi</li>"
            "<li>Chiusura per inventario dal 21 al 26 settembre</li>"
            "<li>Serata di lettura con l'autrice Sara Prova, giovedì 5 novembre alle 20.00</li></ul>")
    css = (f".notizie{{padding-left:18px}}.notizie li{{margin:6px 0}}.badge{{background:{bg};color:{fg};"
           "font-size:14px;padding:2px 8px;border-radius:4px;margin-right:6px}")
    return mk(rng, "it", "bibliothek", "Notizie", main, "failed", ".badge", "1.4.3/F1",
              f"The 14 px 'Novità' badge text ({fg} on {bg}) reaches only {r}:1.",
              css=css, difficulty="easy")


def f1_status_de(rng):
    fg = "#5cb85c"
    r = chk(fg, "#ffffff", hi=4.5)
    main = ("<h1>Hallenbad</h1><div class=\"cards\"><div class=\"card\"><h2>Heute</h2><p>Status: "
            "<span class=\"status\">geöffnet</span></p><p>Wassertemperatur 28 °C</p></div><div class=\"card\">"
            "<h2>Öffnungszeiten</h2><p>Mo–Fr 6.30–21.30 Uhr<br>Sa–So 8.00–19.00 Uhr</p></div>"
            "<div class=\"card\"><h2>Eintritt</h2><p>Erwachsene CHF 8.–<br>Kinder CHF 4.–</p></div></div>")
    css = f".status{{color:{fg};font-weight:700;font-size:16px}}"
    return mk(rng, "de", "sport", "Hallenbad", main, "failed", ".status", "1.4.3/F1",
              f"The 16 px bold green status word on the white card has {r}:1 (normal text, needs 4.5:1).",
              css=css, difficulty="easy")


def f1_strip_fr(rng):
    fg, bg = "#ffffff", "#4fa3d9"
    r = chk(fg, bg, hi=4.5)
    main = ("<div class=\"bandeau-info\">Travaux sur la ligne 2 du 3 au 14 novembre : les arrêts Poste et Collège "
            "sont déplacés de 50 mètres.</div><h1>Horaires et lignes</h1><p>Toutes les lignes circulent toutes "
            "les 15 minutes du lundi au vendredi, toutes les 30 minutes le week-end.</p>")
    css = f".bandeau-info{{background:{bg};color:{fg};font-size:15px;padding:10px 16px;border-radius:6px}}"
    return mk(rng, "fr", "verkehr", "Horaires et lignes", main, "failed", ".bandeau-info", "1.4.3/F1",
              f"The 15 px white notice on light blue {bg} has {r}:1.", css=css, difficulty="easy")


def f2_large_it(rng):
    t = pick_theme(rng)
    fg = "#9fb3c8"
    r = chk(fg, t["bg"], hi=3)
    main = ("<h1>Corsi di nuoto 2027</h1><h2 class=\"sottotitolo\">Iscrizioni aperte fino al 30 novembre</h2>"
            "<p>I corsi per bambini dai 5 anni si svolgono il sabato mattina. Gruppi di sei bambini al massimo, "
            "con monitori certificati.</p>")
    css = f".sottotitolo{{font-size:32px;font-weight:400;color:{fg};margin-top:0}}"
    return mk(rng, "it", "sport", "Corsi di nuoto", main, "failed", ".sottotitolo", "1.4.3/F2",
              f"Even as large text (32 px) the pale blue subtitle reaches only {r}:1 on {t['bg']}, below 3:1.",
              css=css, theme=t, difficulty="easy")


def f2_large_de(rng):
    fg, bg = "#ffffff", "#f4a261"
    r = chk(fg, bg, hi=3)
    main = ("<div class=\"aktion\"><p class=\"aktion-titel\">Jetzt anmelden: Ferienkurse 2027</p><p>Schwimmen, "
            "Klettern, Töpfern – über 40 Kurse für Kinder und Jugendliche.</p></div>"
            "<h1>Ferienkurse</h1><p>Die Anmeldung ist ab 1. März online möglich. Die Plätze werden nach "
            "Eingang vergeben.</p>")
    css = (f".aktion{{background:{bg};padding:12px 20px;border-radius:8px}}.aktion p{{color:#1d2327}}"
           f".aktion .aktion-titel{{font-size:26px;font-weight:700;color:{fg};margin:0}}")
    return mk(rng, "de", "schule", "Ferienkurse", main, "failed", ".aktion-titel", "1.4.3/F2",
              f"The 26 px bold white headline on orange {bg} is large text but has only {r}:1 (< 3:1); the dark body text in the box passes.",
              css=css, difficulty="medium")


def f3_bold18_fr(rng):
    fg = "#bf6d1f"
    r = chk(fg, "#ffffff", lo=3, hi=4.5)
    main = ("<h1>Camp de ski 2027</h1><div class=\"card\"><p class=\"avertissement\">Inscriptions closes le "
            "15 décembre</p><p>Le camp aura lieu du 1er au 5 février au chalet de la Combe-Modèle. Participation : "
            "CHF 180.– par enfant.</p></div>")
    css = f".avertissement{{font-size:18px;font-weight:700;color:{fg};margin:0 0 8px}}"
    return mk(rng, "fr", "schule", "Camp de ski", main, "failed", ".avertissement", "1.4.3/F3",
              f"18 px bold is below the 18.66 px (14 pt) bold threshold, so this is normal text: {r}:1 is under 4.5:1.",
              css=css, difficulty="hard")


def f4_bgimage_de(rng):
    fg, bgc = "#8a6d5a", "#f6dcc4"
    r = chk(fg, bgc, hi=4.5)
    src = asset("v-bg-sand", flat_bg(bgc, "#e9c9ab"))
    main = ("<div class=\"titelbild\"><p class=\"titeltext\">Sommerprogramm im Museum: Führungen, Werkstätten "
            "und Konzerte im Innenhof</p></div><h1>Sommer im Kornhaus</h1><p>Von Juli bis August ist das Museum "
            "täglich von 10 bis 18 Uhr geöffnet. Kinder bis 16 Jahre haben freien Eintritt.</p>")
    css = (f".titelbild{{background-image:url({src});background-size:100% 100%;padding:28px 24px 36px;"
           f"border-radius:8px}}.titeltext{{color:{fg};font-size:17px;margin:0;max-width:640px}}")
    return mk(rng, "de", "museum", "Sommer im Kornhaus", main, "failed", ".titeltext", "1.4.3/F4",
              f"The 17 px text sits on a flat sand-coloured background image ({bgc}); {fg} on it gives {r}:1.",
              css=css, difficulty="medium")


def f4_bgimage_it(rng):
    fg, bgc = "#ffffff", "#7fb3d5"
    r = chk(fg, bgc, hi=4.5)
    src = asset("v-bg-sky", flat_bg(bgc, "#6fa5c9"))
    main = ("<div class=\"testata\"><p class=\"slogan\">Il lago vi aspetta: battelli ogni ora da aprile a "
            "ottobre</p></div><h1>Navigazione sul lago</h1><p>Gli orari estivi sono validi dal 4 aprile al "
            "18 ottobre 2027. Biciclette a bordo: CHF 5.–.</p>")
    css = (f".testata{{background-image:url({src});background-size:100% 100%;padding:30px 24px 38px}}"
           f".slogan{{color:{fg};font-size:18px;margin:0;max-width:620px}}")
    return mk(rng, "it", "verkehr", "Navigazione", main, "failed", ".slogan", "1.4.3/F4",
              f"White 18 px text on a flat light-blue background image ({bgc}) has {r}:1.",
              css=css, difficulty="medium")


def f5_borderline_it(rng):
    fg = "#777777"
    r = contrast(fg, "#ffffff")
    assert 4.4 < r < 4.5
    main = ("<h1>Regolamento sull'uso delle palestre</h1><div class=\"card\"><p>Le palestre comunali sono "
            "messe a disposizione delle società locali secondo il calendario stabilito dal Municipio.</p>"
            "<p class=\"aggiornamento\">Ultimo aggiornamento: 12.10.2026 – Cancelleria comunale</p></div>")
    css = f".aggiornamento{{font-size:15px;color:{fg};margin-bottom:0}}"
    return mk(rng, "it", "gemeinde", "Regolamento palestre", main, "failed", ".aggiornamento", "1.4.3/F5",
              f"#777777 on white is {r:.3f}:1 — just under 4.5:1; ratios are not rounded, so the 15 px text fails.",
              css=css, difficulty="hard")


# ---------------------------------------------------------------------------
# PASSED
# ---------------------------------------------------------------------------

def p1_borderline_de(rng):
    fg = "#767676"
    r = chk(fg, "#ffffff", lo=4.5)
    main = ("<h1>Kehrichtabfuhr 2027</h1><div class=\"card\"><p>Die Abfuhr findet jeden Dienstag statt. Fällt "
            "der Dienstag auf einen Feiertag, wird am Mittwoch abgeholt.</p><p class=\"stand\">Stand: 1.10.2026 · "
            "Änderungen vorbehalten</p></div>")
    css = f".stand{{font-size:14px;color:{fg};margin-bottom:0}}"
    return mk(rng, "de", "werke", "Kehrichtabfuhr", main, "passed", ".stand", "1.4.3/P1",
              f"The grey 14 px note #767676 on the white card has {r}:1, just above 4.5:1.",
              difficulty="hard", css=css)


def p1_button_fr(rng):
    fg, bg = "#ffffff", "#0b4f6c"
    r = chk(fg, bg, lo=4.5)
    main = ("<h1>Abonnements annuels</h1><p>Les abonnements 2027 sont en vente dès le 1er décembre au guichet "
            "de la gare et en ligne.</p><p><a class=\"bouton\" href=\"abonnement-commande.html\">Commander mon "
            "abonnement</a></p>")
    css = (f".bouton{{display:inline-block;background:{bg};color:{fg};padding:10px 18px;border-radius:6px;"
           "text-decoration:none;font-size:16px;font-weight:600}")
    return mk(rng, "fr", "verkehr", "Abonnements", main, "passed", ".bouton", "1.4.3/P1",
              f"White 16 px button text on {bg} has {r}:1.", css=css, difficulty="easy")


def p1_warning_it(rng):
    fg, bg = "#8a4b08", "#fff3e0"
    r = chk(fg, bg, lo=4.5)
    main = ("<h1>Acqua potabile</h1><div class=\"avviso\"><p>Lavori alla rete idrica in Via ai Monti: "
            "giovedì 12 novembre, dalle 8.00 alle 12.00, l'acqua potrà essere torbida. Lasciatela scorrere "
            "qualche minuto prima dell'uso.</p></div><p>Per urgenze il servizio di picchetto risponde al "
            "numero {PHONE}.</p>")
    css = f".avviso{{background:{bg};border-left:4px solid #e0a040;padding:4px 16px}}.avviso p{{color:{fg};font-size:15px}}"
    return mk(rng, "it", "werke", "Acqua potabile", main, "passed", ".avviso p", "1.4.3/P1",
              f"The brown 15 px warning text on light orange has {r}:1.", css=css, difficulty="easy")


def p1_bgimage_de(rng):
    fg, bgc = "#3e2723", "#f6dcc4"
    r = chk(fg, bgc, lo=4.5)
    src = asset("v-bg-sand", flat_bg(bgc, "#e9c9ab"))
    main = ("<div class=\"titelbild\"><p class=\"titeltext\">Herbstferien im Museum: Werkstatt «Papier "
            "schöpfen» für Kinder ab 7 Jahren</p></div><h1>Vermittlung</h1><p>Anmeldung bis eine Woche vor dem "
            "Termin. Kosten: CHF 15.– inklusive Material.</p>")
    css = (f".titelbild{{background-image:url({src});background-size:100% 100%;padding:28px 24px 36px;"
           f"border-radius:8px}}.titeltext{{color:{fg};font-size:17px;margin:0;max-width:640px}}")
    return mk(rng, "de", "museum", "Vermittlung", main, "passed", ".titeltext", "1.4.3/P1",
              f"Dark brown text on the flat sand background image ({bgc}) has {r}:1.", css=css, difficulty="medium")


def p1_status_fr(rng):
    fg = "#2e7d32"
    r = chk(fg, "#ffffff", lo=4.5)
    main = ("<h1>Piscine couverte</h1><div class=\"cards\"><div class=\"card\"><h2>Aujourd'hui</h2><p>État : "
            "<span class=\"etat\">ouvert</span></p><p>Eau à 28 °C</p></div><div class=\"card\"><h2>Horaires</h2>"
            "<p>Lu–ve 6 h 30–21 h 30<br>Sa–di 8 h–19 h</p></div></div>")
    css = f".etat{{color:{fg};font-weight:700;font-size:16px}}"
    return mk(rng, "fr", "sport", "Piscine couverte", main, "passed", ".etat", "1.4.3/P1",
              f"Green bold status text on the white card has {r}:1.", css=css, difficulty="easy")


def t1_large_it(rng):
    fg = "#8a8a8a"
    r = chk(fg, "#ffffff", lo=3, hi=4.5)
    main = ("<h1>Biblioteca per ragazzi</h1><div class=\"card\"><p class=\"motto\">Leggere è un'avventura</p>"
            "<p>Ogni mercoledì pomeriggio letture animate per bambini dai 4 agli 8 anni. Entrata libera.</p></div>")
    css = f".motto{{font-size:28px;font-weight:400;color:{fg};margin:0 0 8px}}"
    return mk(rng, "it", "bibliothek", "Biblioteca per ragazzi", main, "passed", ".motto", "1.4.3/T1",
              f"The grey motto is 28 px (large text), so {r}:1 meets the 3:1 requirement.",
              trap=True, css=css, difficulty="medium")


def t1_bold19_de(rng):
    fg = "#bf6d1f"
    r = chk(fg, "#ffffff", lo=3, hi=4.5)
    main = ("<h1>Skilager 2027</h1><div class=\"card\"><p class=\"hinweis\">Anmeldeschluss: 15. Dezember</p>"
            "<p>Das Lager findet vom 1. bis 5. Februar statt. Elternbeitrag: CHF 180.– pro Kind.</p></div>")
    css = f".hinweis{{font-size:19px;font-weight:700;color:{fg};margin:0 0 8px}}"
    return mk(rng, "de", "schule", "Skilager", main, "passed", ".hinweis", "1.4.3/T1",
              f"19 px bold exceeds the 18.66 px (14 pt) bold threshold, so this is large text and {r}:1 ≥ 3:1 suffices.",
              trap=True, css=css, difficulty="hard")


def t1_banner_fr(rng):
    fg, bg = "#ffffff", "#d35400"
    r = chk(fg, bg, lo=3, hi=4.5)
    main = ("<div class=\"promo\"><p class=\"promo-titre\">Nouveau : la carte journalière à CHF 9.–</p></div>"
            "<h1>Billets</h1><p>La carte journalière est valable sur tout le réseau urbain jusqu'à 5 h le "
            "lendemain matin.</p>")
    css = (f".promo{{background:{bg};padding:14px 20px;border-radius:8px}}"
           f".promo-titre{{font-size:26px;font-weight:400;color:{fg};margin:0}}")
    return mk(rng, "fr", "verkehr", "Billets", main, "passed", ".promo-titre", "1.4.3/T1",
              f"White on {bg} is {r}:1, insufficient for body text but the 26 px headline is large text (≥ 3:1).",
              trap=True, css=css, difficulty="medium")


def t2_disabled_de(rng):
    main = ("<h1>Umfrage zum Ortsbus</h1><p>Wie zufrieden sind Sie mit dem Angebot des Ortsbusses? Die Umfrage "
            "dauert etwa fünf Minuten.</p><form id=\"umfrage\" action=\"umfrage-danke.html\" method=\"post\">"
            "<label for=\"fahrten\">Wie oft fahren Sie mit dem Ortsbus?</label><select id=\"fahrten\" name=\"fahrten\">"
            "<option>täglich</option><option>wöchentlich</option><option>selten</option><option>nie</option></select>"
            "<p><input type=\"checkbox\" id=\"ok\" name=\"ok\"> <label for=\"ok\" style=\"display:inline\">Ich habe "
            "die Hinweise zum Datenschutz gelesen.</label></p>"
            "<p><button type=\"submit\" id=\"senden\" disabled>Antworten senden</button></p></form>")
    css = "button[disabled]{background:#e0e0e0;color:#9e9e9e;border-color:#e0e0e0;cursor:not-allowed}"
    js = ("<script>document.addEventListener('DOMContentLoaded',function(){var c=document.getElementById('ok');"
          "c.addEventListener('change',function(){document.getElementById('senden').disabled=!c.checked;});});</script>")
    r = ratio("#9e9e9e", "#e0e0e0")
    return mk(rng, "de", "verkehr", "Umfrage Ortsbus", main, "passed", "#senden", "1.4.3/T2",
              f"The submit button is disabled until the checkbox is ticked; its {r}:1 text is exempt as an inactive component.",
              trap=True, css=css, head=js, difficulty="medium")


def t2_fieldset_it(rng):
    main = ("<h1>Ordinazione della carta giornaliera</h1><form action=\"ordine-inviato.html\" method=\"post\">"
            "<fieldset><legend>Indirizzo di consegna</legend><label for=\"via\">Via e numero</label>"
            "<input type=\"text\" id=\"via\" name=\"via\"><label for=\"npa\">NPA e località</label>"
            "<input type=\"text\" id=\"npa\" name=\"npa\"></fieldset>"
            "<p><input type=\"checkbox\" id=\"uguale\" name=\"uguale\" checked> <label for=\"uguale\" "
            "style=\"display:inline\">L'indirizzo di fatturazione è uguale a quello di consegna</label></p>"
            "<fieldset id=\"fatturazione\" disabled><legend>Indirizzo di fatturazione</legend>"
            "<label for=\"via2\">Via e numero</label><input type=\"text\" id=\"via2\" name=\"via2\">"
            "<label for=\"npa2\">NPA e località</label><input type=\"text\" id=\"npa2\" name=\"npa2\"></fieldset>"
            "<p><button type=\"submit\">Ordina</button></p></form>")
    css = "fieldset[disabled]{color:#a0a0a0}fieldset[disabled] input{color:#a0a0a0;border-color:#d0d0d0;background:#f5f5f5}"
    js = ("<script>document.addEventListener('DOMContentLoaded',function(){var c=document.getElementById('uguale');"
          "c.addEventListener('change',function(){document.getElementById('fatturazione').disabled=c.checked;});});</script>")
    r = ratio("#a0a0a0", "#ffffff")
    return mk(rng, "it", "gemeinde", "Carta giornaliera", main, "passed", "#fatturazione", "1.4.3/T2",
              f"The billing-address group is a disabled fieldset; its grey text ({r}:1) belongs to inactive components and is exempt.",
              trap=True, css=css, head=js, difficulty="medium")


def t3_logo_fr(rng):
    col = "#b0b7bf"
    r = ratio(col, "#ffffff")
    src = asset("v-logo-partner-fr", logo_pale("Fondation Exemple", "pour la culture régionale", col))
    extra = (f'<p>Avec le soutien de</p><p>{img(src, "Fondation Exemple pour la culture régionale", 230, 56, class_="partenaire")}</p>')
    main = ("<h1>Saison culturelle 2026–2027</h1><p>Théâtre, concerts et lectures : la saison culturelle propose "
            "douze rendez-vous à la salle communale, d'octobre à mai.</p><p>Abonnement de saison : CHF 150.–, "
            "billet individuel : CHF 18.–.</p>")
    return mk(rng, "fr", "gemeinde", "Saison culturelle", main, "passed", ".partenaire", "1.4.3/T3",
              f"The pale wordmark ({r}:1) is part of a sponsor's logo; logotypes have no contrast requirement.",
              trap=True, chrome=True, footer_extra=extra, difficulty="medium")


def t4_watermark_it(rng):
    main = ("<div class=\"giubileo\"><span class=\"filigrana\" aria-hidden=\"true\">1926</span>"
            "<h1>Cent'anni di scuola a Esempiano</h1><p>Nel 1926 si inaugurava la prima sede della scuola "
            "elementare. Per festeggiare, sabato 12 settembre porte aperte con mostra fotografica e "
            "merenda per tutti.</p></div>")
    css = (".giubileo{position:relative;overflow:hidden;padding:12px 0}.filigrana{position:absolute;right:0;"
           "top:-10px;font-size:140px;font-weight:700;color:#eceff1;line-height:1}"
           ".giubileo h1,.giubileo p{position:relative}")
    return mk(rng, "it", "schule", "Cent'anni di scuola", main, "passed", ".filigrana", "1.4.3/T4",
              "The huge pale '1926' (about 1.1:1) is an aria-hidden decorative watermark repeating the year stated in the text; pure decoration is exempt.",
              trap=True, css=css, difficulty="medium")


def t5_backdrop_de(rng):
    src = asset("v-scene-market-12", scene("market", seed=12, w=960, h=320))
    main = ("<div class=\"titelbild\"><div class=\"kasten\"><h2>Willkommen am Wochenmarkt</h2><p>Jeden Samstag "
            "von 8 bis 12 Uhr auf dem Dorfplatz – regionale Produkte direkt vom Hof.</p></div></div>"
            "<h1>Wochenmarkt</h1><p>Neue Marktfahrerinnen und Marktfahrer melden sich bei der Gemeindekanzlei.</p>")
    r = chk("#ffffff", "#0b4f6c", lo=4.5)
    css = (f".titelbild{{background-image:url({src});background-size:cover;background-position:center;"
           "padding:48px 24px;border-radius:8px}.kasten{background:#0b4f6c;color:#ffffff;padding:4px 18px;"
           "max-width:440px;border-radius:6px}.kasten h2{color:#ffffff}")
    return mk(rng, "de", "gemeinde", "Wochenmarkt", main, "passed", ".kasten p", "1.4.3/T5",
              f"Although placed over a busy illustration, the text sits on an opaque dark box; white on #0b4f6c is {r}:1.",
              trap=True, css=css, difficulty="medium")


# ---------------------------------------------------------------------------
# CANTTELL
# ---------------------------------------------------------------------------

def c1_gradient_fr(rng):
    top, bottom = "#1b5a80", "#a4cfe6"
    r_top, r_bot = chk("#ffffff", top, lo=4.5), chk("#ffffff", bottom, hi=4.5)
    main = ("<h1>Vendanges 2027</h1><p><span class=\"degrade\">Caves ouvertes le 2 octobre</span></p>"
            "<p>Les vignerons vous accueillent de 10 h à 18 h. Navette gratuite depuis la gare toutes les 30 minutes. "
            "Dégustation : verre souvenir à CHF 10.–.</p>")
    css = (f".degrade{{display:inline-block;white-space:nowrap;color:#ffffff;font-size:20px;line-height:28px;padding:0 14px;"
           f"background:linear-gradient(180deg,{top} 0%,{top} 40%,{bottom} 62%,{bottom} 100%) 0 0/100% 28px repeat-y}}")
    return mk(rng, "fr", "gemeinde", "Vendanges", main, "cantTell", ".degrade", "1.4.3/C1",
              f"The 28 px line box has a dark top ({r_top}:1 with white) and a light bottom ({r_bot}:1), so every glyph has passing and failing pixels; ACT's highest-contrast reading passes, worst-area testing fails.",
              alt_expected="passed", css=css, difficulty="hard")


def c1_image_it(rng):
    top, bottom = "#2b4f6e", "#e9c8a0"
    r_top, r_bot = chk("#ffffff", top, lo=4.5), chk("#ffffff", bottom, hi=4.5)
    src = asset("v-bg-dusk", band_bg(top, bottom, 0.40, 0.62))
    main = ("<h1>Festa d'autunno</h1><p><span class=\"tramonto\">Sabato 17 ottobre in piazza</span></p>"
            "<p>Mercato, musica e castagne in Piazza Grande fino a mezzanotte. In caso di pioggia la festa si sposta "
            "nella sala multiuso.</p>")
    css = (f".tramonto{{display:inline-block;white-space:nowrap;color:#ffffff;font-size:19px;line-height:30px;padding:0 14px;"
           f"background-image:url({src});background-size:100% 30px;background-repeat:repeat-y}}")
    return mk(rng, "it", "gemeinde", "Festa d'autunno", main, "cantTell", ".tramonto", "1.4.3/C1",
              f"The dusk-sky background image is dark behind the upper part of the glyphs ({r_top}:1) and pale at the bottom ({r_bot}:1); contrast varies inside each glyph.",
              alt_expected="passed", css=css, difficulty="hard")


def c2_halo_de(rng):
    src = asset("v-scene-lake-13", scene("lake", seed=13, w=960, h=320))
    main = ("<div class=\"titelbild\"><p class=\"schatten\">Schifffahrt auf dem Mustersee: Sommerfahrplan ab "
            "1. Mai</p></div><h1>Schifffahrt</h1><p>Die Kursschiffe verkehren stündlich zwischen 9 und 19 Uhr. "
            "Velos werden gegen einen Zuschlag von CHF 5.– befördert.</p>")
    css = (f".titelbild{{background-image:url({src});background-size:cover;background-position:center top;"
           "padding:24px;min-height:120px;border-radius:8px}.schatten{color:#ffffff;font-size:20px;font-weight:600;"
           "margin:0;max-width:560px;text-shadow:0 0 3px #000000,0 0 6px #000000}")
    sky = scene_sky("lake", 13)
    return mk(rng, "de", "verkehr", "Schifffahrt", main, "cantTell", ".schatten", "1.4.3/C2",
              f"White text on a pale sky ({ratio('#ffffff', sky)}:1) is legible only through a dark blurred text-shadow; whether that counts as a halo/background cannot be decided from the colours.",
              alt_expected="passed", css=css, difficulty="hard")


def c2_shadow_fr(rng):
    fg, bgc = "#d0d0d0", "#8a8f96"
    r = chk(fg, bgc, hi=4.5)
    src = asset("v-bg-stone", flat_bg(bgc, "#7c8188"))
    main = ("<div class=\"entete\"><p class=\"ombre\">Exposition « Pierres du vallon » – jusqu'au 28 février</p>"
            "</div><h1>Exposition temporaire</h1><p>Une centaine de minéraux et de fossiles récoltés dans la "
            "région, présentés par le club de géologie.</p>")
    css = (f".entete{{background-image:url({src});background-size:100% 100%;padding:28px 24px 36px}}"
           f".ombre{{color:{fg};font-size:18px;margin:0;text-shadow:1px 1px 2px #000000}}")
    return mk(rng, "fr", "museum", "Exposition temporaire", main, "cantTell", ".ombre", "1.4.3/C2",
              f"Light grey text on grey ({r}:1 without shadow) gets a 1 px dark drop shadow; whether this narrow shadow is an outline of the glyph or a halo that becomes the background is not decidable from CSS.",
              alt_expected="passed", css=css, difficulty="hard")


BUILDERS = [
    f1_smallprint_de, f1_button_fr, f1_badge_it, f1_status_de, f1_strip_fr, f2_large_it, f2_large_de,
    f3_bold18_fr, f4_bgimage_de, f4_bgimage_it, f5_borderline_it,
    p1_borderline_de, p1_button_fr, p1_warning_it, p1_bgimage_de, p1_status_fr,
    t1_large_it, t1_bold19_de, t1_banner_fr, t2_disabled_de, t2_fieldset_it, t3_logo_fr, t4_watermark_it,
    t5_backdrop_de,
    c1_gradient_fr, c1_image_it, c2_halo_de, c2_shadow_fr,
]


def build(rng):
    return [b(rng) for b in BUILDERS]
