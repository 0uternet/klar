"""WCAG check modules: one module per success criterion, discovered automatically.

How to add a check (example: 2.4.6 Headings and Labels)
--------------------------------------------------------
1. File and discovery. Create klar/checks/c_2_4_6.py (dots → underscores). Define ONE
   subclass of klar.checks.base.BaseCheck and expose it as the module-level name
   `CHECK = HeadingsAndLabels`. registry.implemented() finds it; nothing else to
   register. The registry already holds the criterion's name, level, method, ACT rule
   and EN 301 549 clause, and BaseCheck copies name/level/act_rule/en301549 from it.
   Once the module imports, coverage and /api/criteria switch from "planned" to the
   registry method automatically.

2. Class attributes.
       criterion = "2.4.6"
       prompt_version = "2.4.6/v1"   # bump on ANY change of SYSTEM, element/context keys or schema
       needs_vision = False          # True exactly when the registry method is "apertus_vision"
       guard_numbers = True          # False only if the model reads numbers off an image
       max_candidates = 200

3. candidates(page) -> list[Candidate]: facts, computed in CODE from the CapturedPage:
   page.links / images / passages / lang_elements / fields / forms / headings,
   page.axe (violations, incomplete), page.form_probe() (bundled demo and test set only),
   page.evaluate("s => window.__klar.describe(s)", sel) for more DOM facts, and
   page.screenshot(selector, cand_id) for a PNG crop (vision checks; only if self.vision).
   Build each with self.candidate(page, selector=..., html=..., text=..., context={...},
   lang=..., **extra). `context` holds ONLY what the model may see; deterministic
   features go into extra (e.g. extra["kind"], which becomes the default reason_code).

4. decide(c) -> Finding | None: the deterministic tier (rule / heuristic).
       return self.finding(c, outcome="failed", source="heuristic", confidence="high",
                           reason_code="generic_label",            # closed set per module
                           explanation=t("c246.generic_label", self.ui_lang, ...),
                           user_impact=t("c246.impact", self.ui_lang, ...),
                           fix_diff=..., fix_hint=...)
   Return None to ask Apertus. Never return "passed" for something you could not verify.
   For a cantTell note use self.note(c, "note.<key>").

5. question(c, ui_lang) -> LLMTask: ONE closed question.
       return self.task(system=self.system_prompt(SYSTEM, c),   # fix=True to ask for a fix
                        element={"heading": c.text, "html": self.prompt_html(c)},
                        context=c.context,
                        question="Which category describes this heading?",
                        schema=category_schema(CATEGORIES),     # or verdict_schema()
                        images=[c.screenshot],                  # vision checks only
                        max_tokens=140)
   Rules (tested): page data reaches the model ONLY through element/context, which the
   base class JSON-encodes inside <page_data>…</page_data> under an untrusted-data
   instruction; the prompt must not depend on ui_lang
   (question(c, "en").wire() == question(c, "de").wire()); no concrete examples taken
   from data/testset or data/demo-site (scripts/check_leakage.py must print 0 overlaps);
   prefer a categorical question whose categories are mapped to outcomes in code; keep
   outputs tiny (quote ≤ 80 chars, reason ≤ 160 chars, English).

6. interpret(c, answer) -> Finding: map the validated answer.
   source="apertus", reason_code="apertus_<category>", explanation and user_impact from
   i18n templates, reason=answer["reason"] (English, kept for audit, never shown as UI
   text). The excerpt (usually answer["quote"]) must be a verbatim substring of c.html or
   c.text: the evidence guard turns anything else into cantTell "not grounded". Build
   fixes with set_attr / replace_text / wrap_text / unified_diff from base.py.

7. UI strings. At import time call klar.i18n.register({...}) with the module's own keys,
   prefixed "c" + criterion without dots ("c246.generic_label"), each in en, de, fr and
   it. Writing rules: short, concrete, no jargon; never "compliant", "certified",
   "conformance score" or "100 %".

8. Tests. tests/test_c_2_4_6.py: build pages with CapturedPage.from_elements(...) to test
   candidates / decide / question / interpret without a browser; use the `render_html`
   fixture (conftest.py) for DOM-dependent facts and fake_llm.FakeLLM for end-to-end runs.
   Run the whole suite: tests/test_registry.py imports every check module strictly.

What the pipeline does for every module: the prompt-injection pre-filter before decide(),
vision gating (needs_vision), the round-robin model budget across criteria, cache and
replay, the evidence guard, finding ids, progress events and all reports. Shared files
(base.py, registry.py, pipeline.py, capture/*, guard.py, models.py, i18n.py except
register(), eval/*) are changed only through the backend owner.
"""
