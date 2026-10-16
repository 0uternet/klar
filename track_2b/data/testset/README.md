---
pretty_name: Klar. WCAG judgement test set (DE/FR/IT)
license:
  - cdla-permissive-2.0   # generated cases (data/testset/generated), per-row field `license`
  - other                 # W3C Software and Document Notice and License, SPDX W3C-20150513 (data/testset/act)
language: [de, fr, it, en]
task_categories: [text-classification]
size_categories: [n<1K]
tags: [accessibility, wcag, a11y, evaluation, act-rules, switzerland, multilingual]
---

# Klar. evaluation set: WCAG 2.1 AA criteria that need judgement

> **Status:** labels are frozen by the git tag `labels-v1`, set before any test-split model call.
> Counts are in [`STATS.md`](STATS.md), which `scripts/build_manifest.py` regenerates. `STATS.md` also records the sha256 of `manifest.jsonl`.

## 1. Purpose

Klar. pre-checks the WCAG 2.1 AA / eCH-0059 success criteria that need human judgement on Swiss public-sector pages in German, French and Italian. Examples are link purpose, language of parts, sensory instructions and error messages. Klar. uses Apertus, the Swiss open LLM.

This set measures how well a checker separates **failed / passed / cantTell / inapplicable**. It is built so that keyword shortcuts fail. It contains many **exception traps**, for example:

- proper names in another language;
- helvetisms;
- logotypes;
- decorative images;
- a "Mehr" link whose sentence gives context.

It also has a small **prompt-injection** subset (6 cases).

It is meant for **evaluation**, not training. The `dev` split exists only so that prompts can be written without looking at `test`.

## 2. Composition

| Part | Folder | Cases | Labels |
|---|---|---|---|
| **Generated** (synthetic, trilingual) | `generated/<criterion>/` | **787 cases** over all 26 criteria, 14 to 85 per criterion. They include 6 prompt-injection cases, 94 designed add-on cases (38 for 3.1.2; 40 for 4.1.2, 3.3.2 and 1.3.5; 16 for 3.1.1, 2.4.2 and 2.4.5) and 52 multi-page mini sites (282 pages). | by construction, from the decision rules in [`PROTOCOL.md`](PROTOCOL.md) |
| **W3C ACT Rules test cases** | `act/testcases/<rule>/` | **207 test cases** from the 14 ACT *judgement* rules that map to 11 of the 26 criteria (57 failed, 88 passed, 62 inapplicable). | the expected *rule* outcome, from `act/testcases-filtered.json` |

Outcome mix of the generated cases:

| Outcome | Cases | Share |
|---|---:|---:|
| `failed` | 306 | 38.9 % |
| `passed` | 348 | 44.2 % |
| `cantTell` | 118 | 15.0 % |
| `inapplicable` | 15 | 1.9 % |

- **Exception traps:** 221, i.e. 61 % of the passed and inapplicable cases.
- **`alt_expected`:** 38 cases also carry the strict or alternative reading (PROTOCOL § 7).
- **Page languages:** DE 284, FR 248, IT 242, EN 9, RM (Romansh) 4. Criterion 3.1.2 has 15 core cases per language, 2 injection cases and 38 designed span cases (quoted titles, standalone titles, institution + address, address only, and quoted-sentence contrasts), each category in both splits.
- **Split:** 182 `dev` and 605 `test`. The headline criteria have 34 (1.1.1), 34 (2.4.4) and 57 (3.1.2) test cases.
- **Size:** about 7.4 MB for `data/` in total.

**Split by template group** (PROTOCOL § 6, decision D2). Every generated case belongs to a template group (`template_id`). Two cases share a group when they come from the same content pool, or when their texts under test have a Jaccard similarity ≥ 0.6. Whole groups go to `dev` (≈ 20 % per criterion and outcome, seed `20261014`) or to `test`. Designed add-on subsets (tag `addon`) carry a fixed, balanced split and do not shift the existing assignment. Dev and test therefore share no template, no near-duplicate and no surface form. All ACT cases are in `test`.

### `manifest.jsonl` (one JSON object per line)

| field | type | meaning |
|---|---|---|
| `case_id` | str | `gen-<criterion>-<lang>-<nnn>` or `act-<rule>-<testcase id>-<criterion>` |
| `criterion` | str | WCAG 2.1 success criterion, e.g. `"2.4.4"` |
| `page_lang` | str | generated: the actual language of the page content (`de`/`fr`/`it`/`en`/`rm`); ACT: the declared `<html lang>` primary subtag, or `und` |
| `source` | str | `generated` \| `act` |
| `act_rule` | str/null | ACT rule id for ACT cases |
| `split` | str | `dev` \| `test` |
| `expected` | str | `failed` \| `passed` \| `cantTell` \| `inapplicable` (W3C ACT/EARL vocabulary) |
| `path` | str | entry HTML file, relative to `data/testset/` (for multi-page cases, their `index.html`) |
| `target_selector` | str/null | CSS selector of the element under test (it matches exactly one element), or `null` for page-level and site-level criteria and for ACT cases |
| `notes` | str | one-sentence rationale. For ACT cases: rule name, test case title and source URL |
| `rule` | str | the PROTOCOL decision rule that produced the label (`2.4.4/C1`, `ACT:5effbb`) |
| `trap` | bool | an exception trap: it looks like a failure, but an exception or legitimate pattern applies |
| `alt_expected` | str/null | the outcome under the strict or alternative reading, where the protocol knowingly differs (PROTOCOL § 7) |
| `difficulty` | str | `easy` \| `medium` \| `hard` (construction estimate) |
| `pages` | int | number of HTML pages in the case (more than 1 for the mini sites of 2.4.2, 2.4.5, 3.2.3 and 3.2.4; some 2.4.5 sites use folder URLs `folder/` → `folder/index.html`) |
| `template_id` | str | template group used for the group split (`<criterion>/<family>`; `act/<rule>` for ACT) |
| `surface_forms` | list | the decisive words of the case: exception words of a trap, a title of a work, an invalid `lang` value. Checked for leakage. |
| `tags` | list | subset labels, e.g. `["injection", "sr-only"]` |
| `license` | str | SPDX id: `CDLA-Permissive-2.0` (generated) or `W3C-20150513` (ACT) |

## 3. Construction

- **Protocol first.** [`PROTOCOL.md`](PROTOCOL.md) gives, for each criterion, the decision rules for every outcome. They are grounded in the W3C *Understanding WCAG 2.1* documents, the sufficient techniques and failures, and the ACT rules. It also records the decisions D1–D5. Decision D1 covers link context: a preceding heading is not context, so a heading-only link is `cantTell`. The protocol was written before the cases were generated and before any model run.
- **Deterministic generator.** `scripts/generate_testset.py` uses only the standard library, with seed `20261014`. It has one module per criterion in `scripts/testset_gen/`. The scenario texts are in Swiss Standard German, French and Italian, about municipalities, schools, libraries, utilities, transport and tourism, all fictional. The generator combines them with rule-specific frames, layouts, themes and positions through a seeded RNG.
- **Images.** All images are SVGs we generated ourselves, in `generated/_assets/`: charts with real numbers, pictograms, banners containing text, decorative ornaments and flat illustrations. There are no third-party images.
- **Construction checks.** `scripts/validate_testset.py` checks that:
  - every path exists;
  - every `target_selector` matches exactly one element;
  - every generated page is strictly well formed;
  - no verdict words leak into ids, classes or URLs, and there are no HTML comments;
  - there are no external resources, and local references resolve;
  - the demo answer keys are outside the served demo folder;
  - the size budget is respected.

  We also checked every target selector in headless Chromium. Each matched exactly one element, with no script errors.
- **Leakage check.** `scripts/check_leakage.py` (decision D3, run in CI) must print `0 overlaps`. It checks that no test-split string occurs:
  - in the application code, its prompts or its lexicons (`src/klar/**`);
  - in the demo site or its answer keys;
  - in the dev split.

  It also checks templates, near-duplicates and surface forms across splits.
- **ACT import.** `scripts/import_act.py` imports only the judgement rules. Presence and syntax rules are axe-core territory; `--all-rules` restores them. It downloads the files sequentially with a polite delay. The files are byte-for-byte copies, and the source URL of each case is kept in `notes`.

### Regenerate

```bash
cd track_2b
python -I scripts/import_act.py          # optional: refresh the W3C ACT cases (network); --offline rebuilds from disk
python -I scripts/generate_testset.py    # rebuilds generated/, manifest.jsonl, STATS.md
python -I scripts/validate_testset.py    # must print "OK: no errors"
python -I scripts/check_leakage.py       # must print "0 overlaps"
python -I scripts/sample_for_review.py   # blind 50-case sample → review_sample.csv
python -I scripts/sample_for_review.py --score data/testset/review_sample.csv   # agreement + Cohen's kappa
```

Serve `data/testset/act/` as the web root when you render ACT cases, because they use root-relative `/test-assets/` URLs.

## 4. How the data was made

- **Authoring.** The case texts are the scenario strings in `scripts/testset_gen/`; the seeded generator turns them into pages. All pages, names and addresses are synthetic.
- **Labels.** The labels are **assigned by construction** from the written decision rules in `PROTOCOL.md`, which were written before the cases were generated. No model judged or labelled any case.
- **No Apertus output.** **No output of Apertus, or of any model under evaluation, was used to create, select or label data.**
- **Review.** A blind, stratified sample of 50 test cases (`review_sample.csv`) was re-labelled using only the protocol, into `review_relabel.csv`: all 50 labels agree (Cohen's κ = 1.0, from `sample_for_review.py --score data/testset/review_relabel.csv`). This is not an independent human annotation; until one is done, the labels are single-annotator. PROTOCOL § 11 logs the result.

## 5. Licences

- **Generated cases** (`generated/**`, `manifest.jsonl`, `STATS.md`, `PROTOCOL.md`, this card, `review_sample.csv`, `review_relabel.csv`): **CDLA-Permissive-2.0** ([text](LICENSE-CDLA-Permissive-2.0.txt)). © 2026 the Klar. team.
- **W3C ACT Rules test cases** (`act/testcases/**`, `act/test-assets/**`): © W3C, under the **W3C Software and Document Notice and License** (SPDX `W3C-20150513`). The full text, the provenance and the list of imported rules are in [`act/LICENSE-W3C.md`](act/LICENSE-W3C.md).
  - The case files are **unmodified copies**.
  - `act/testcases-filtered.json` and `act/manifest_act.jsonl` are **derived** files: a filtered index and our metadata.
- **Per-row licence.** Every manifest row names its licence in the `license` field.
- **Fictional content.** All organisations, people, addresses, e-mail addresses (`*.example`) and phone numbers in the generated cases are fictional. The trap names are fictional too, and disjoint from the demo site. The cases contain no Swiss cross, no coats of arms and no federal logos.

## 6. Intended use and metrics

Klar. matches each finding to a case by `target_selector`, or by page when the selector is `null`. It reports:

- precision, recall and **false-pass rate** on `failed`;
- accuracy over the four outcomes;
- the `cantTell` rate;
- Wilson confidence intervals.

These are reported separately for:

- generated `test` vs ACT;
- each criterion;
- each language;
- traps vs non-traps;
- the injection subset.

ACT cases are scored in the ACT consistency sense (PROTOCOL § 8). Cases with `alt_expected` can be scored under both readings.

## 7. Limitations

- **Synthetic.** The generated pages are short and cleaner than real CMS output. Each has one element under test. They do not show the long-tail mess of real sites: third-party widgets, PDFs, very long pages. Results on this set are an upper bound on real-world performance.
- **Labels by construction.** The labels follow the protocol mechanically. Where the protocol itself is debatable (the `cantTell` classes, `alt_expected`), the debate is documented, not settled. The blind re-labelling of 50 cases is reported in § 4.
- **Synthetic language.** The DE/FR/IT texts aim at idiomatic Swiss usage, but they are not a corpus of real municipal text. Romansh appears only in a single formula.
- **Behavioural criteria.** For 2.2.2, 2.4.3, 3.2.2, 3.3.x and others, the labels assume the inline scripts are executed as written in Chromium. Static-only checkers will see less.
- **Uneven external coverage.** 15 criteria have no ACT judgement rule and are covered only by the generated cases: 1.3.1, 1.3.2, 1.3.5, 1.4.1, 1.4.3, 1.4.11, 2.4.3, 2.4.5, 3.2.2, 3.2.3, 3.2.4, 3.3.2, 3.3.3, 3.3.4 and 4.1.2. The site-level criteria (2.4.5, 3.2.3, 3.2.4) have only 14 mini sites each, so their confidence intervals are wide.
- **ACT outcomes are rule outcomes.** An ACT `passed` case does not prove the success criterion is satisfied (PROTOCOL § 8). Many ACT cases are English-only and use non-Swiss contexts.
- **Not for training.** If the set is used for training or for prompt tuning on `test`, the `test` results are no longer valid evidence.
