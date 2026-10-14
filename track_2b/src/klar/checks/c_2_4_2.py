"""2.4.2 Page Titled, level A. ACT rules 2779a5 (page has a non-empty title) and
c4a8a4 (page title is descriptive).

Facts in code (no model)
  1. no <title> element                      → failed (rule, 2779a5; axe document-title)
  2. <title> empty or only whitespace         → failed (rule, 2779a5; axe document-title)
  3. title is a file name or an internal identifier (it has a file extension, or it is
     one lower-case token joined by - _ / . with no space, or it equals the last
     segment of the page address)              → failed (heuristic, F25)
  4. an inner page whose title is exactly the HOME page's title, when that title is only
     the site name (the brand link's text) (PROTOCOL 2.4.2/F4)  → failed (heuristic, c4a8a4)
     Any other duplicate (views of a web application titled with the application name,
     T5; articles titled with their section, C1) is NOT decided in code: the heading of
     the other page with the same title goes to Apertus as context.
     (sample: c_2_4_5.site_sample, shared with 2.4.5/3.2.3/3.2.4; skipped when nothing
     is fetchable)

Asked to Apertus (one question per page, unless decided above)
  Data: the title, the main heading (first h1, else first heading) and the first
  ~300 characters of the main content. Categorical question "What does the title
  describe?", mapped in code (data/testset/PROTOCOL.md §2.4.2):
      names_topic          → passed  (topic or purpose; the site name may be added;
                                      the order and the length do not matter; the name
                                      of a web application is enough for its views)
      site_name_only       → failed  (only the website or organisation, while the page is
                                      about a narrower topic), passed on the home page
      section_or_umbrella  → cantTell (a section name over one specific item, or an
                                      umbrella term over unrelated short items)
      different_topic      → failed
      placeholder          → failed  (editor default, numbering, file name, code)
      unsure               → cantTell
  The quote must be the title, verbatim (evidence guard).

Home page (code): the site root is the target of the brand/home link (rel=home, else
the first banner link), else the origin's "/" (c_2_4_5.site_root). The page is the home
page when a link with aria-current="page" points to that root, or when its own address
is that root. A title that names only the organisation is a home page's topic
(Understanding 2.4.2).

Known limits: titles changed by scripts after load are seen as rendered; the page's
purpose is judged from its first heading and opening text only; the duplicate-title
rule only sees the sampled pages.
"""

from __future__ import annotations

import re
from urllib.parse import unquote, urljoin, urlparse

from klar.capture.page import CapturedPage
from klar.checks.base import BaseCheck, category_schema, unified_diff
from klar.checks.c_2_4_5 import (Document, SitePage, SiteSample, SiteSampling, is_home, page_doc, page_key, short_path,
                                 site_name, site_root)
from klar.i18n import register, t
from klar.models import Candidate, Finding, LLMTask

PROMPT_VERSION = "2.4.2/v2"  # v2: same-title context, application views
EXCERPT_CHARS = 300

CATEGORIES = ["names_topic", "site_name_only", "section_or_umbrella", "different_topic", "placeholder", "unsure"]
CATEGORY_OUTCOME = {"names_topic": "passed", "site_name_only": "failed", "section_or_umbrella": "cantTell",
                    "different_topic": "failed", "placeholder": "failed", "unsure": "cantTell"}

_FILE_EXT = re.compile(r"\.(?:s?html?|php\d?|aspx?|jsp|cfm|cgi|pdf|docx?|xml|json)$", re.IGNORECASE)
_IDENT = re.compile(r"^[a-z0-9]+(?:[-_/.][a-z0-9]+)+$")

MAX_SITE_QUESTIONS = 2  # other pages' shared titles asked per scan


def _norm_name(s: str) -> str:
    return " ".join(re.sub(r"[^\w]+", " ", (s or "").casefold()).split())


def site_name_title(sample: SiteSample) -> str:
    """The home page's title (casefolded) when it is ONLY the site/organisation name (part
    of the brand link text), else "". Only such a title, repeated on an inner page, is decided
    in code (PROTOCOL 2.4.2/F4); an application's start-page title repeated on its views
    is T5 and goes to the model."""
    home = sample.home
    if home is None:
        return ""
    title = " ".join(home.doc.title.split())
    name = site_name(home.doc) or (site_name(sample.entry.doc) if sample.entry is not None else "")
    # the brand link may announce more ("… – home page", a logo text): the title must be
    # contained in what it says, never the other way round (an application's title)
    return title.casefold() if name and _norm_name(title) and _norm_name(title) in _norm_name(name) else ""


def _h1(sp: SitePage) -> str:
    h = sp.doc.find(lambda n: n.tag == "h1")
    return h.text() if h is not None else ""


register({
    "c242.on_page": {"en": "{page}: {text}", "de": "{page}: {text}", "fr": "{page} : {text}", "it": "{page}: {text}"},
    "c242.missing": {
        "en": "The page has no title element.",
        "de": "Die Seite hat kein title-Element.",
        "fr": "La page n'a pas d'élément title.",
        "it": "La pagina non ha un elemento title.",
    },
    "c242.empty": {
        "en": "The page title is empty.",
        "de": "Der Seitentitel ist leer.",
        "fr": "Le titre de la page est vide.",
        "it": "Il titolo della pagina è vuoto.",
    },
    "c242.filename": {
        "en": "The title “{title}” is a file name or an internal code, not a description of the page.",
        "de": "Der Titel «{title}» ist ein Dateiname oder interner Code, keine Beschreibung der Seite.",
        "fr": "Le titre « {title} » est un nom de fichier ou un code interne, pas une description de la page.",
        "it": "Il titolo «{title}» è un nome di file o un codice interno, non una descrizione della pagina.",
    },
    "c242.home_title": {
        "en": "The title “{title}” is the title of the home page; this page is about “{heading}”, but its title only names the site.",
        "de": "Der Titel «{title}» ist der Titel der Startseite; diese Seite handelt von «{heading}», ihr Titel nennt aber nur die Website.",
        "fr": "Le titre « {title} » est celui de la page d'accueil ; cette page traite de « {heading} », mais son titre ne nomme que le site.",
        "it": "Il titolo «{title}» è quello della pagina iniziale; questa pagina tratta di «{heading}», ma il suo titolo indica solo il sito.",
    },
    "c242.apertus_names_topic": {
        "en": "Apertus judged that the title “{title}” names the topic or purpose of the page.",
        "de": "Apertus beurteilt, dass der Titel «{title}» Thema oder Zweck der Seite nennt.",
        "fr": "Apertus juge que le titre « {title} » nomme le sujet ou le but de la page.",
        "it": "Apertus giudica che il titolo «{title}» indichi l'argomento o lo scopo della pagina.",
    },
    "c242.apertus_site_name_only": {
        "en": "Apertus judged that the title “{title}” names only the website or organisation, while the page is about “{heading}”.",
        "de": "Apertus beurteilt, dass der Titel «{title}» nur die Website oder Organisation nennt, die Seite aber von «{heading}» handelt.",
        "fr": "Apertus juge que le titre « {title} » ne nomme que le site ou l'organisation, alors que la page traite de « {heading} ».",
        "it": "Apertus giudica che il titolo «{title}» indichi solo il sito o l'organizzazione, mentre la pagina tratta di «{heading}».",
    },
    "c242.home_site_name": {
        "en": "The title “{title}” names the organisation; on the home page that is its topic.",
        "de": "Der Titel «{title}» nennt die Organisation; auf der Startseite ist das ihr Thema.",
        "fr": "Le titre « {title} » nomme l'organisation ; sur la page d'accueil, c'est son sujet.",
        "it": "Il titolo «{title}» indica l'organizzazione; nella pagina iniziale è il suo argomento.",
    },
    "c242.apertus_section_or_umbrella": {
        "en": "The title “{title}” names a section or a broad category rather than this page's specific content. Experts disagree whether that is enough: a person must decide.",
        "de": "Der Titel «{title}» nennt eine Rubrik oder einen Oberbegriff statt des konkreten Inhalts dieser Seite. Ob das genügt, ist umstritten: Eine Person muss entscheiden.",
        "fr": "Le titre « {title} » nomme une rubrique ou une catégorie générale plutôt que le contenu précis de cette page. Les avis divergent : une personne doit trancher.",
        "it": "Il titolo «{title}» indica una sezione o una categoria generica invece del contenuto specifico di questa pagina. Gli esperti non concordano: una persona deve decidere.",
    },
    "c242.apertus_different_topic": {
        "en": "Apertus judged that the title “{title}” names another topic than the page, which is about “{heading}”.",
        "de": "Apertus beurteilt, dass der Titel «{title}» ein anderes Thema nennt als die Seite, die von «{heading}» handelt.",
        "fr": "Apertus juge que le titre « {title} » nomme un autre sujet que la page, qui traite de « {heading} ».",
        "it": "Apertus giudica che il titolo «{title}» indichi un altro argomento rispetto alla pagina, che tratta di «{heading}».",
    },
    "c242.apertus_placeholder": {
        "en": "Apertus judged that the title “{title}” is a placeholder that says nothing about the page.",
        "de": "Apertus beurteilt den Titel «{title}» als Platzhalter, der nichts über die Seite sagt.",
        "fr": "Apertus juge que le titre « {title} » est un texte provisoire qui ne dit rien de la page.",
        "it": "Apertus giudica che il titolo «{title}» sia un segnaposto che non dice nulla della pagina.",
    },
    "c242.apertus_unsure": {
        "en": "Apertus could not decide whether the title “{title}” describes the page. A person must check.",
        "de": "Apertus konnte nicht entscheiden, ob der Titel «{title}» die Seite beschreibt. Eine Person muss prüfen.",
        "fr": "Apertus n'a pas pu décider si le titre « {title} » décrit la page. Une personne doit vérifier.",
        "it": "Apertus non ha potuto decidere se il titolo «{title}» descriva la pagina. Una persona deve verificare.",
    },
    "c242.impact": {
        "en": "Screen-reader users hear the title first and people switching between tabs read it: they cannot tell what this page is.",
        "de": "Screenreader lesen den Titel zuerst vor, und wer zwischen Tabs wechselt, liest ihn: Man erkennt nicht, worum es auf dieser Seite geht.",
        "fr": "Les lecteurs d'écran annoncent d'abord le titre, et on le lit en changeant d'onglet : on ne sait pas de quoi parle cette page.",
        "it": "I lettori di schermo annunciano per primo il titolo e chi passa da una scheda all'altra lo legge: non si capisce di cosa tratti questa pagina.",
    },
    "c242.impact_ok": {
        "en": "Screen-reader users and people switching tabs know which page they are on.",
        "de": "Screenreader-Nutzende und wer zwischen Tabs wechselt, wissen, auf welcher Seite sie sind.",
        "fr": "Les utilisateurs de lecteurs d'écran et les personnes qui changent d'onglet savent sur quelle page ils sont.",
        "it": "Chi usa un lettore di schermo o passa da una scheda all'altra sa in quale pagina si trova.",
    },
    "c242.fix_hint": {
        "en": "In your CMS, give the page a title that names its topic, for example “{proposal}”.",
        "de": "Geben Sie der Seite im CMS einen Titel, der ihr Thema nennt, zum Beispiel «{proposal}».",
        "fr": "Dans votre CMS, donnez à la page un titre qui nomme son sujet, par exemple « {proposal} ».",
        "it": "Nel CMS, date alla pagina un titolo che ne indichi l'argomento, per esempio «{proposal}».",
    },
    "c242.home_title_other_page": {
        "en": "Another page of this site, “{page}”, has only the site name as its title (“{title}”), so its topic (“{heading}”) is not announced.",
        "de": "Eine andere Seite dieser Website, «{page}», hat nur den Namen der Website als Titel («{title}»); ihr Thema («{heading}») wird so nicht angekündigt.",
        "fr": "Une autre page de ce site, « {page} », n'a que le nom du site comme titre (« {title} ») : son sujet (« {heading} ») n'est donc pas annoncé.",
        "it": "Un'altra pagina di questo sito, «{page}», ha come titolo solo il nome del sito («{title}»): il suo argomento («{heading}») non viene quindi annunciato.",
    },
    "c242.impact_other_page": {
        "en": "On that page, screen-reader users and people switching tabs cannot tell what it is about.",
        "de": "Auf jener Seite erkennen Screenreader-Nutzende und wer zwischen Tabs wechselt nicht, worum es geht.",
        "fr": "Sur cette autre page, les utilisateurs de lecteurs d'écran et les personnes qui changent d'onglet ne savent pas de quoi elle traite.",
        "it": "Su quell'altra pagina, chi usa un lettore di schermo o passa da una scheda all'altra non capisce di cosa tratti.",
    },
    "c242.fix_hint_other_page": {
        "en": "On “{page}”, change the title in your CMS so that it names that page's topic, for example “{proposal}”.",
        "de": "Ändern Sie im CMS auf «{page}» den Titel so, dass er das Thema jener Seite nennt, zum Beispiel «{proposal}».",
        "fr": "Sur « {page} », modifiez le titre dans votre CMS pour qu'il nomme le sujet de cette page, par exemple « {proposal} ».",
        "it": "Su «{page}», modificate il titolo nel CMS in modo che indichi l'argomento di quella pagina, per esempio «{proposal}».",
    },
    "c242.fix_hint_other_page_plain": {
        "en": "On “{page}”, change the title in your CMS so that it names that page's topic.",
        "de": "Ändern Sie im CMS auf «{page}» den Titel so, dass er das Thema jener Seite nennt.",
        "fr": "Sur « {page} », modifiez le titre dans votre CMS pour qu'il nomme le sujet de cette page.",
        "it": "Su «{page}», modificate il titolo nel CMS in modo che indichi l'argomento di quella pagina.",
    },
    "c242.fix_hint_plain": {
        "en": "In your CMS, give the page a title that names its topic.",
        "de": "Geben Sie der Seite im CMS einen Titel, der ihr Thema nennt.",
        "fr": "Dans votre CMS, donnez à la page un titre qui nomme son sujet.",
        "it": "Nel CMS, date alla pagina un titolo che ne indichi l'argomento.",
    },
})


def is_filename_title(title: str, url: str) -> bool:
    s = title.strip()
    if not s or " " in s:
        return False
    if _FILE_EXT.search(s) or _IDENT.match(s):
        return True
    last = unquote(urlparse(url).path.rstrip("/").rsplit("/", 1)[-1])
    return bool(last) and s.lower() == last.lower() and bool(re.search(r"[-_.\d]", last))


def main_heading(page: CapturedPage, doc: Document) -> tuple[str, str]:
    """(text, selector) of the main heading: first visible h1, else the first heading."""
    hs = page.headings
    if hs:
        h = next((h for h in hs if h.get("level") == 1 and (h.get("text") or "").strip()), None) or \
            next((h for h in hs if (h.get("text") or "").strip()), None)
        if h:
            return " ".join(h["text"].split()), h["selector"]
    for tag in ("h1", "h2", "h3"):
        n = doc.find(lambda x, tag=tag: x.tag == tag and x.text())
        if n is not None:
            return n.text(), n.css_path()
    return "", ""


def content_excerpt(doc: Document, heading: str, limit: int = EXCERPT_CHARS) -> str:
    root = doc.main or doc.body
    skip = (lambda n: n.tag in ("nav", "header", "footer", "aside", "form") or n.role == "navigation") \
        if root is doc.body else None
    text = root.text(skip=skip)
    if heading and text.startswith(heading):
        text = text[len(heading):].strip()
    return text[:limit]


def home_evidence(page: CapturedPage, doc: Document) -> bool | None:
    """True (home page), False (inner page) or None (unknown, e.g. pasted HTML)."""
    root = site_root(page.url, doc, page.policy) if urlparse(page.url).scheme in ("http", "https", "file") else None
    current = doc.find(lambda n: n.tag == "a" and n.attrs.get("aria-current", "").lower() in ("page", "true"))
    if current is not None and root and current.attrs.get("href"):
        target = page_key(urljoin(page.url, current.attrs["href"]))
        return target == root
    if root is None:
        return None
    return page_key(page.url) == root


class PageTitled(SiteSampling, BaseCheck):
    criterion = "2.4.2"
    prompt_version = PROMPT_VERSION
    max_candidates = 1 + 1 + MAX_SITE_QUESTIONS

    def candidates(self, page: CapturedPage) -> list[Candidate]:
        doc = page_doc(page)
        title_el = doc.title_el
        title = doc.title if title_el is not None else ""
        if title_el is not None and not title and page.title:
            title = " ".join(page.title.split())
        heading, h_sel = main_heading(page, doc)
        excerpt = content_excerpt(doc, heading)
        home = home_evidence(page, doc)
        html = title_el.outer(300) if title_el is not None else "<head>"
        extra: dict = {"title": title, "heading": heading, "home": home, "heading_selector": h_sel}
        if title_el is None:
            extra["kind"] = "missing"
        elif not title:
            extra["kind"] = "empty"
        elif is_filename_title(title, page.url):
            extra["kind"] = "filename"
        context = {"main_heading": heading, "content_start": excerpt}
        if extra.get("kind") is None:
            home_title, same_title = self.same_titles(page, title, heading, home)
            if home_title:
                extra["kind"] = "home_title"
            else:
                extra["kind"] = "ask"
                if same_title:  # another page with this title: context for the model, never a verdict
                    context["heading_of_other_page_with_same_title"] = same_title[1]
                    extra["same_title_page"] = same_title[0]
        own = self.candidate(page, selector="html", html=html, text=title, lang=page.lang, context=context,
                             key="#title", **extra)
        return [own, *self.site_candidates(page, title)]

    def site_candidates(self, page: CapturedPage, own_title: str) -> list[Candidate]:
        """The other sampled pages of the same set (PROTOCOL: a mini site's outcome is its worst
        page). In code: inner pages that carry exactly the home page's title (F4). To the model,
        with the same context as above: one page per other title shared by several pages (an
        application's views, T5; articles titled with their section, C1). Nothing else is asked:
        a page with a title of its own is judged when it is scanned itself."""
        if urlparse(page.url).scheme not in ("http", "https", "file"):
            return []
        sample = self.site(page)
        if sample.entry is None:
            return []
        others = [sp for sp in sample.same_set() if sp is not sample.entry]
        home = sample.home
        home_title = site_name_title(sample)
        out: list[Candidate] = []
        f4 = [sp for sp in others if home is not None and sp.key != home.key and home_title
              and " ".join(sp.doc.title.split()).casefold() == home_title]
        if f4:
            sp = f4[0]
            title = " ".join(sp.doc.title.split())
            heading = _h1(sp)
            out.append(self.candidate(
                page, selector="html", html=f"<title>{title}</title>", text=title, lang=page.lang, key="#site-home-title",
                kind="site_home_title", title=title, heading=heading, home=False,
                page_path=", ".join(short_path(x.url, sample.root) for x in f4[:3])))
        groups: dict[str, list] = {}
        for sp in others:
            if home is not None and sp.key == home.key:
                continue  # the home page is judged when it is scanned itself
            t_ = " ".join(sp.doc.title.split())
            if t_ and t_.casefold() not in (home_title, own_title.casefold()):
                groups.setdefault(t_.casefold(), []).append(sp)
        for pages in [g for g in groups.values() if len(g) >= 2][:MAX_SITE_QUESTIONS]:
            # Ask about the page the shared title fits least: one whose main heading is not part
            # of the title (an article under a section title, not the section page itself).
            pages = sorted(pages, key=lambda x: _norm_name(_h1(x)) in _norm_name(x.doc.title))
            sp, other = pages[0], pages[1]
            title = " ".join(sp.doc.title.split())
            heading = _h1(sp)
            context = {"main_heading": heading, "content_start": content_excerpt(sp.doc, heading),
                       "heading_of_other_page_with_same_title": _h1(other)}
            out.append(self.candidate(
                page, selector="html", html=f"<title>{title}</title>", text=title, lang=page.lang, context=context,
                key="#site-title:" + sp.key[-120:], kind="ask", title=title, heading=heading,
                home=is_home(sp, sample), page_path=short_path(sp.url, sample.root)))
        return out

    def same_titles(self, page: CapturedPage, title: str, heading: str,
                    home: bool | None) -> tuple[bool, tuple[str, str] | None]:
        """(the title is the home page's title on an inner page,
            (path, main heading) of another sampled page with the same title and another heading).
        Uses the shared, memoised site sample; nothing when the page is the home page or
        when no other page can be fetched."""
        if home is not False or urlparse(page.url).scheme not in ("http", "https", "file"):
            return False, None
        sample = self.site(page)
        key = title.casefold()
        if sample.home is not None and sample.entry is not None and sample.home.key != sample.entry.key \
                and site_name_title(sample) == key:
            return True, None
        for sp in sample.pages[1:]:
            if " ".join(sp.doc.title.split()).casefold() != key:
                continue
            h1 = sp.doc.find(lambda n: n.tag == "h1")
            other = h1.text() if h1 is not None else ""
            if other and other.casefold() != (heading or "").casefold():
                return False, (short_path(sp.url, sample.root), other)
        return False, None

    # -- decisions (code) -------------------------------------------------------------------
    def decide(self, c: Candidate) -> Finding | None:
        ui = self.ui_lang
        kind = c.extra.get("kind")
        title, heading = c.extra.get("title", ""), c.extra.get("heading", "")
        if kind in ("missing", "empty"):
            f = self.finding(c, outcome="failed", source="rule", confidence="high", act_rule="2779a5",
                             excerpt=c.html[:300], explanation=t(f"c242.{kind}", ui),
                             user_impact=t("c242.impact", ui), **self.fix(c))
            return f.model_copy(update={"axe_rule": "document-title"})
        if kind == "filename":
            return self.finding(c, outcome="failed", source="heuristic", confidence="high", act_rule="c4a8a4",
                                excerpt=title, explanation=t("c242.filename", ui, title=title),
                                user_impact=t("c242.impact", ui), **self.fix(c))
        if kind == "home_title":
            return self.finding(c, outcome="failed", source="heuristic", confidence="medium", act_rule="c4a8a4",
                                excerpt=title, reason_code="home_title",
                                explanation=t("c242.home_title", ui, title=title, heading=heading),
                                user_impact=t("c242.impact", ui), **self.fix(c))
        if kind == "site_home_title":
            # About ANOTHER page of the set, reported on the scanned page (page_url, selector
            # "html"): no fix_diff (it would target the other page), the hint names that page.
            return self.finding(c, outcome="failed", source="heuristic", confidence="medium", act_rule="c4a8a4",
                                excerpt=title, reason_code="site_home_title_other_page",
                                explanation=t("c242.home_title_other_page", ui, page=c.extra.get("page_path", ""),
                                              title=title, heading=heading),
                                user_impact=t("c242.impact_other_page", ui), **self.fix(c))
        return None

    def on_page(self, c: Candidate, text: str) -> str:
        """Prefix the explanation with the page it is about when that is another sampled page."""
        path = c.extra.get("page_path")
        return t("c242.on_page", self.ui_lang, page=path, text=text) if path else text

    def fix(self, c: Candidate) -> dict:
        heading = (c.extra.get("heading") or "").strip()
        other = c.extra.get("page_path")
        if other:  # another page of the set: a hint that names it, never a diff on the scanned page
            if not heading:
                return {"fix_hint": t("c242.fix_hint_other_page_plain", self.ui_lang, page=other)}
            return {"fix_hint": t("c242.fix_hint_other_page", self.ui_lang, page=other, proposal=heading)}
        if not heading:
            return {"fix_hint": t("c242.fix_hint_plain", self.ui_lang)}
        before = c.html if c.html.startswith("<title") else "<title></title>"
        after = f"<title>{heading}</title>"
        return {"fix_hint": t("c242.fix_hint", self.ui_lang, proposal=heading),
                "fix_diff": unified_diff(before, after, "head > title")}

    # -- the closed (categorical) question ----------------------------------------------------
    SYSTEM = (
        "You check WCAG 2.1 success criterion 2.4.2 Page Titled for ONE web page. A page title must describe the "
        "topic or purpose of the page. It may be short, it need not repeat the main heading word for word, and "
        "the name of the website may come before or after the topic. If present, "
        "`heading_of_other_page_with_same_title` is the main heading of another page of the same site that has "
        "exactly the same title.\n"
        "What does the title describe?\n"
        "- names_topic: the topic or purpose of this page (on a page about the organisation as a whole, its name "
        "is the topic; for the pages of a web application, the name of the application is enough)\n"
        "- site_name_only: only the website or organisation, while the page is about a narrower topic\n"
        "- section_or_umbrella: only the section the page belongs to while the page shows one specific item, or "
        "a broad umbrella term over unrelated short items\n"
        "- different_topic: a different topic than the page content\n"
        "- placeholder: an editor default, a number, a file name or a code that says nothing\n"
        "- unsure: none of these\n"
        "quote: the title, copied exactly."
    )

    def question(self, c: Candidate, ui_lang: str) -> LLMTask:
        return self.task(
            system=self.system_prompt(self.SYSTEM, c),
            element={"title": c.extra.get("title", "")},
            context=c.context,
            question="What does the page title describe?",
            schema=category_schema(CATEGORIES),
            max_tokens=120,
        )

    def interpret(self, c: Candidate, answer: dict) -> Finding:
        ui = self.ui_lang
        category = answer.get("category", "unsure")
        outcome = CATEGORY_OUTCOME.get(category, "cantTell")
        title, heading = c.extra.get("title", ""), c.extra.get("heading", "")
        key = f"c242.apertus_{category}" if category in CATEGORY_OUTCOME else "c242.apertus_unsure"
        code = key.split(".")[-1]
        if category == "site_name_only" and c.extra.get("home"):
            outcome, key, code = "passed", "c242.home_site_name", "home_site_name"
        if category in ("site_name_only", "different_topic") and not heading:
            outcome, key, code = "cantTell", "c242.apertus_unsure", "apertus_no_heading"
        failed_impact = t("c242.impact_other_page" if c.extra.get("page_path") else "c242.impact", ui)
        impact = {"failed": failed_impact, "passed": t("c242.impact_ok", ui)}.get(outcome, t("impact.review", ui))
        quote = (answer.get("quote") or "").strip()
        return self.finding(c, outcome=outcome, source="apertus", act_rule="c4a8a4",
                            confidence=answer.get("confidence", "low") if outcome != "cantTell" else "low",
                            excerpt=quote or (title if outcome != "failed" else ""),
                            explanation=self.on_page(c, t(key, ui, title=title, heading=heading)), user_impact=impact,
                            reason=answer.get("reason"), reason_code=code,
                            **(self.fix(c) if outcome == "failed" else {}))


CHECK = PageTitled
