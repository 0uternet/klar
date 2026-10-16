"""3.2.3 Consistent Navigation, level AA. No ACT rule (technique G61, failure F66).
Decided in code (no Apertus question): relative order is a fact.

The audited page is compared with a bounded sample of the same site (see
c_2_4_5.site_sample: same origin, static HTML, at most 20 pages and 15 s).
Pages whose main text is in another language form another set of pages
(Understanding 3.2.3) and are not compared. The finding is about the SET of pages
(data/testset/PROTOCOL.md §3.2.3): it is reported on the audited page and names the
page that deviates (the audited page itself when most other pages differ from it).

Repeated navigation mechanisms, in DOM order, per page:
  skip     the first in-page link before the main content ("#…")
  nav      every <nav> / role=navigation (breadcrumbs excluded: they change by design)
  links    a header, footer or side block with ≥ 2 links outside any <nav>
  search   a search form
  MAIN     the position of the main content (a mechanism moved from before to after
           the content changes its relative order, F66)
Blocks are matched across pages by kind + landmark + label, else by the overlap of
their link targets. Items inside a block are matched by their normalised text (the
current page may be plain text with aria-current) or their target.

Cascade (one finding for the set of pages, reported on the audited page)
  1. pasted HTML                                   → cantTell (needs a URL)
  2. no navigation mechanism on the audited page   → inapplicable
  3. no other page of the same language shares a mechanism → cantTell (not enough pages)
  4. a page changes the relative order of the items of a repeated block, or of the
     repeated blocks themselves                     → failed (F66)
     except: only a small footer link list differs   → cantTell (whether it is a
             navigational mechanism is disputed)
             the deviating page carries another site name in its header → cantTell
             (it may not belong to the same set of pages)
  5. otherwise                                      → passed (items may be added or
     removed, sub-navigation may expand, the current item may be text: G61 allows it)

Known limits: scripts are not run on the sampled pages; a navigation rebuilt by
JavaScript, or one hidden by CSS on some pages, is not seen; pages beyond the sample
are not compared.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck
from klar.checks.c_2_4_5 import (Node, SiteSample, SiteSampling, SitePage, is_breadcrumb, is_search_form,
                                 live_selector, page_doc, region_of, short_path)
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "3.2.3/v1"  # no model question
FOOTER_SMALL = 6  # a footer list with at most this many links is a "small footer list"

register({
    "c323.passed": {
        "en": "The navigation blocks keep the same relative order on the {n} sampled pages.",
        "de": "Die Navigationsblöcke behalten auf den {n} geprüften Seiten dieselbe Reihenfolge.",
        "fr": "Les blocs de navigation gardent le même ordre relatif sur les {n} pages examinées.",
        "it": "I blocchi di navigazione mantengono lo stesso ordine relativo nelle {n} pagine esaminate.",
    },
    "c323.item_order": {
        "en": "On {page} the items of the navigation “{block}” appear in a different order ({items}).",
        "de": "Auf {page} stehen die Einträge der Navigation «{block}» in anderer Reihenfolge ({items}).",
        "fr": "Sur {page}, les entrées de la navigation « {block} » apparaissent dans un autre ordre ({items}).",
        "it": "In {page} le voci della navigazione «{block}» compaiono in un altro ordine ({items}).",
    },
    "c323.block_order": {
        "en": "On {page} the navigation “{block}” sits in a different place relative to the other repeated blocks and the content.",
        "de": "Auf {page} steht die Navigation «{block}» an anderer Stelle im Verhältnis zu den anderen wiederholten Blöcken und zum Inhalt.",
        "fr": "Sur {page}, la navigation « {block} » se trouve à un autre endroit par rapport aux autres blocs répétés et au contenu.",
        "it": "In {page} la navigazione «{block}» si trova in un altro punto rispetto agli altri blocchi ripetuti e al contenuto.",
    },
    "c323.footer_only": {
        "en": "Only the small footer list “{block}” changes order on {page}. Whether such a list is a navigation mechanism is disputed: a person must decide.",
        "de": "Nur die kurze Fusszeilen-Liste «{block}» ändert auf {page} die Reihenfolge. Ob sie als Navigation gilt, ist umstritten: Eine Person muss entscheiden.",
        "fr": "Seule la courte liste du pied de page « {block} » change d'ordre sur {page}. Une telle liste est-elle un mécanisme de navigation ? Les avis divergent : une personne doit trancher.",
        "it": "Solo la breve lista del piè di pagina «{block}» cambia ordine in {page}. Se sia un meccanismo di navigazione è controverso: una persona deve decidere.",
    },
    "c323.other_brand": {
        "en": "{page} shows its navigation in a different order, but its header names a different service (“{brand}”). Whether it belongs to the same set of pages is for a person to decide.",
        "de": "{page} zeigt die Navigation in anderer Reihenfolge, nennt im Kopf aber ein anderes Angebot («{brand}»). Ob die Seite zur selben Gruppe gehört, muss eine Person entscheiden.",
        "fr": "{page} présente la navigation dans un autre ordre, mais son en-tête nomme un autre service (« {brand} »). Une personne doit décider si elle fait partie du même ensemble de pages.",
        "it": "{page} mostra la navigazione in un altro ordine, ma la sua intestazione nomina un altro servizio («{brand}»). Una persona deve decidere se fa parte dello stesso insieme di pagine.",
    },
    "c323.impact": {
        "en": "People who rely on the position of the menu, for example screen-reader or magnifier users, lose their way when it moves.",
        "de": "Wer sich an der Lage des Menüs orientiert, etwa mit Screenreader oder Vergrösserung, verliert die Orientierung, wenn es sich verschiebt.",
        "fr": "Les personnes qui se repèrent à la position du menu, par exemple avec un lecteur d'écran ou une loupe, se perdent quand il change de place.",
        "it": "Chi si orienta con la posizione del menu, per esempio con un lettore di schermo o un ingranditore, si perde quando cambia posto.",
    },
    "c323.impact_ok": {
        "en": "People find the navigation in the same place and order on every page.",
        "de": "Man findet die Navigation auf jeder Seite an derselben Stelle und in derselben Reihenfolge.",
        "fr": "La navigation se trouve au même endroit et dans le même ordre sur chaque page.",
        "it": "La navigazione si trova nello stesso punto e nello stesso ordine in ogni pagina.",
    },
    "c323.fix_hint": {
        "en": "Use the same navigation template on every page, with the items in the same order.",
        "de": "Verwenden Sie auf allen Seiten dieselbe Navigationsvorlage mit derselben Reihenfolge der Einträge.",
        "fr": "Utilisez le même gabarit de navigation sur toutes les pages, avec les entrées dans le même ordre.",
        "it": "Usate lo stesso modello di navigazione in tutte le pagine, con le voci nello stesso ordine.",
    },
    "c323.needs_url": {
        "en": "The Consistent Navigation criterion concerns a set of pages; pasted HTML has no site around it. Scan the page by its address.",
        "de": "Das Kriterium «Einheitliche Navigation» betrifft eine Gruppe von Seiten; eingefügtes HTML gehört zu keiner Website. Scannen Sie die Seite über ihre Adresse.",
        "fr": "La navigation cohérente concerne un ensemble de pages ; le HTML collé n'appartient à aucun site. Analysez la page par son adresse.",
        "it": "La navigazione coerente riguarda un insieme di pagine; l'HTML incollato non ha un sito intorno. Analizzate la pagina tramite il suo indirizzo.",
    },
    "c323.too_few": {
        "en": "No other page of the site in the same language with the same navigation could be loaded. A person must compare the pages.",
        "de": "Es liess sich keine andere Seite derselben Website und Sprache mit derselben Navigation laden. Eine Person muss die Seiten vergleichen.",
        "fr": "Aucune autre page du site dans la même langue et avec la même navigation n'a pu être chargée. Une personne doit comparer les pages.",
        "it": "Non è stato possibile caricare altre pagine del sito nella stessa lingua con la stessa navigazione. Una persona deve confrontare le pagine.",
    },
    "c323.no_nav": {
        "en": "This page has no navigation block, so there is nothing to keep consistent.",
        "de": "Diese Seite hat keinen Navigationsblock; es gibt nichts einheitlich zu halten.",
        "fr": "Cette page n'a pas de bloc de navigation : il n'y a rien à garder cohérent.",
        "it": "Questa pagina non ha blocchi di navigazione: non c'è nulla da mantenere coerente.",
    },
})


def label_key(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").casefold()
    s = re.sub(r"[^\w]+", " ", s)
    return " ".join(s.split())


@dataclass
class Block:
    kind: str  # skip | nav | links | search | MAIN
    region: str
    label: str
    node: Node | None
    items: list[tuple[str, str]] = field(default_factory=list)  # (label key, target key)
    display: str = ""  # the block's own label as written (aria-label)
    raw: dict[str, str] = field(default_factory=dict)  # label key → text as written

    @property
    def targets(self) -> set[str]:
        return {tgt for _, tgt in self.items if tgt}

    @property
    def name(self) -> str:
        if self.display:
            return self.display
        return " · ".join(self.raw.get(lbl, lbl) for lbl, _ in self.items[:3]) or self.kind


def _items(sp: SitePage, root: Node) -> tuple[list[tuple[str, str]], dict[str, str]]:
    from urllib.parse import urljoin

    from klar.checks.c_2_4_5 import page_key

    out, raw = [], {}
    for n in root.iter():
        if n.tag == "a" and n.attrs.get("href"):
            text = n.accessible_name()
            out.append((label_key(text), page_key(urljoin(sp.url, n.attrs["href"]))))
        elif n.attrs.get("aria-current") and n.tag != "a" and not n.find(lambda x: x.tag == "a"):
            text = n.text()
            out.append((label_key(text), ""))
        else:
            continue
        raw.setdefault(out[-1][0], text)
    return [it for it in out if it[0] or it[1]], raw


def blocks_of(sp: SitePage) -> list[Block]:
    """Repeated-navigation candidates of one page, in DOM order (+ MAIN)."""
    doc = sp.doc
    body = doc.body
    main = doc.main
    out: list[Block] = []
    taken: list[Node] = []
    skip_done = False
    for n in body.iter():
        if any(t.contains(n) for t in taken):
            continue
        if main is not None and n is main:
            out.append(Block("MAIN", "main", "", n))
            taken.append(n)
            continue
        if n.tag == "a" and not skip_done and (n.attrs.get("href") or "").startswith("#") and len(n.attrs["href"]) > 1:
            skip_done = True
            out.append(Block("skip", region_of(n), "", n, [(label_key(n.text()), n.attrs["href"])], n.text()))
            continue
        if n.tag == "form" and is_search_form(n):
            out.append(Block("search", region_of(n), label_key(n.attrs.get("aria-label", "")), n,
                             display=n.attrs.get("aria-label", "")))
            taken.append(n)
            continue
        if (n.tag == "nav" or n.role == "navigation") and not is_breadcrumb(n):
            items, raw = _items(sp, n)
            out.append(Block("nav", region_of(n.parent) if n.parent is not None else "other",
                             label_key(n.attrs.get("aria-label", "")), n, items, n.attrs.get("aria-label", ""), raw))
            taken.append(n)
            continue
        if n.tag in ("ul", "ol", "p") and region_of(n) in ("header", "footer", "aside") and \
                not n.closest(lambda a: a.tag == "nav" or a.role == "navigation"):
            items, raw = _items(sp, n)
            if len([1 for _, tg in items if tg]) >= 2:
                out.append(Block("links", region_of(n), "", n, items, "", raw))
                taken.append(n)
    return out


def _match(block: Block, others: list[Block]) -> Block | None:
    family = {"nav": ("nav", "links"), "links": ("nav", "links")}.get(block.kind, (block.kind,))
    same = [o for o in others if o.kind in family]
    exact = [o for o in same if o.region == block.region and o.label == block.label]
    if block.kind in ("skip", "search", "MAIN"):
        return (exact or same or [None])[0]
    best, best_j = None, 0.0
    for o in same:
        a, b = block.targets | {lbl for lbl, _ in block.items}, o.targets | {lbl for lbl, _ in o.items}
        j = len(a & b) / len(a | b) if a | b else 0.0
        if o in exact:
            j += 0.5
        if j > best_j:
            best, best_j = o, j
    return best if best_j >= 0.4 else None


def relative_order_differs(a: list[str], b: list[str]) -> list[str] | None:
    """Common elements of a and b in a's order vs b's order; the first two that swap."""
    common = [x for x in a if x in set(b)]
    order_b = [x for x in b if x in set(common)]
    common = list(dict.fromkeys(common))
    order_b = list(dict.fromkeys(order_b))
    if common == order_b:
        return None
    for i, (x, y) in enumerate(zip(common, order_b)):
        if x != y:
            return [x, y]
    return common[:2]


def brand_of(sp: SitePage) -> str:
    header = sp.doc.find(lambda n: n.tag == "header" or n.role == "banner")
    if header is None:
        return ""
    first = header.find(lambda n: n.tag == "a")
    return label_key(first.accessible_name() if first is not None else header.text()[:60])


class ConsistentNavigation(SiteSampling, BaseCheck):
    criterion = "3.2.3"
    prompt_version = PROMPT_VERSION
    max_candidates = 1

    def candidates(self, page: CapturedPage) -> list[Candidate]:
        doc = page_doc(page)
        nav = doc.find(lambda n: (n.tag == "nav" or n.role == "navigation") and not is_breadcrumb(n))
        html = nav.outer(800) if nav is not None else (doc.html_el.outer(200) if doc.html_el else "<html>")
        extra = self.analyse(self.site(page))
        return [self.candidate(page, selector=live_selector(page, nav), html=html, text=nav.text() if nav else "",
                               lang=page.lang, key="#site", **extra)]

    @staticmethod
    def analyse(sample: SiteSample) -> dict:
        if sample.entry is None:
            return {"kind": "needs_url"}
        entry = sample.entry
        ref = blocks_of(entry)
        if not [b for b in ref if b.kind in ("nav", "links")]:
            return {"kind": "no_nav"}
        same_lang = sample.same_set()[1:]
        compared = 0
        violations: list[dict] = []
        for p in same_lang:
            blocks = blocks_of(p)
            pairs = []
            for b in ref:
                m = _match(b, blocks)
                if m is not None:
                    pairs.append((b, m))
            if not [1 for b, _ in pairs if b.kind in ("nav", "links")]:
                continue
            compared += 1
            where = short_path(p.url, sample.root)
            # (a) the order of the repeated blocks (and of the main content) among themselves
            ids_ref = [id(b) for b in ref if any(b is x for x, _ in pairs)]
            matched = {id(m): id(b) for b, m in pairs}
            ids_other = [matched[id(m)] for m in blocks if id(m) in matched]
            swap = relative_order_differs(ids_ref, ids_other)
            if swap:
                moved = next(b for b in ref if id(b) == swap[0])
                if moved.kind == "MAIN":
                    moved = next(b for b in ref if id(b) == swap[1])
                violations.append({"type": "block_order", "where": where, "block": moved.name, "region": moved.region,
                                   "links": len(moved.items), "brand": brand_of(p)})
            # (b) the order of the items inside each repeated block
            for b, m in pairs:
                if b.kind not in ("nav", "links"):
                    continue
                key = lambda it: it[0] or it[1]  # noqa: E731
                swap = relative_order_differs([key(i) for i in b.items], [key(i) for i in m.items])
                if swap:
                    violations.append({"type": "item_order", "where": where, "block": b.name, "region": b.region,
                                       "links": len(b.items), "items": " / ".join(b.raw.get(x, x) for x in swap),
                                       "brand": brand_of(p)})
        if compared == 0:
            return {"kind": "too_few", "n": len(sample.pages)}
        if not violations:
            return {"kind": "passed", "n": compared + 1}
        entry_brand = brand_of(entry)
        if compared >= 2 and len({v["where"] for v in violations}) > compared / 2:
            # most pages differ from the audited page: the audited page is the one that deviates
            here = short_path(entry.url, sample.root)
            others = [v["brand"] for v in violations if v["brand"]]
            majority = max(set(others), key=others.count) if others else ""
            for v in violations:
                v["where"], v["brand"] = here, (entry_brand if majority and entry_brand != majority else "")
            entry_brand = majority or entry_brand
        hard = [v for v in violations if not (v["region"] == "footer" and v["links"] <= FOOTER_SMALL)]
        if not hard:
            return {"kind": "footer_only", "n": compared + 1, **violations[0]}
        firm = [v for v in hard if not (v["brand"] and entry_brand and v["brand"] != entry_brand)]
        if not firm:
            return {"kind": "other_brand", "n": compared + 1, **hard[0]}
        return {"kind": firm[0]["type"], "n": compared + 1, **firm[0]}

    def decide(self, c: Candidate) -> Finding | None:
        ui = self.ui_lang
        kind = c.extra.get("kind")
        excerpt = c.text[:300] if c.text else None
        kw = {k: c.extra.get(k, "") for k in ("block", "items", "brand", "n")}
        kw["page"] = c.extra.get("where", "")
        if kind == "no_nav":
            return self.finding(c, outcome="inapplicable", source="heuristic", confidence="medium", excerpt=excerpt,
                                explanation=t("c323.no_nav", ui), user_impact=t("impact.review", ui))
        if kind in ("needs_url", "too_few"):
            return self.note(c, f"c323.{kind}", source="heuristic")
        if kind == "passed":
            return self.finding(c, outcome="passed", source="heuristic", confidence="medium", excerpt=excerpt,
                                explanation=t("c323.passed", ui, **kw), user_impact=t("c323.impact_ok", ui))
        if kind in ("footer_only", "other_brand"):
            return self.finding(c, outcome="cantTell", source="heuristic", confidence="low", excerpt=excerpt,
                                explanation=t(f"c323.{kind}", ui, **kw), user_impact=t("c323.impact", ui),
                                fix_hint=t("c323.fix_hint", ui))
        return self.finding(c, outcome="failed", source="heuristic", confidence="high", excerpt=excerpt,
                            reason_code=kind, explanation=t(f"c323.{kind}", ui, **kw),
                            user_impact=t("c323.impact", ui), fix_hint=t("c323.fix_hint", ui))

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:  # pragma: no cover - decide() always answers
        raise NotImplementedError("3.2.3 is decided in code")


CHECK = ConsistentNavigation
