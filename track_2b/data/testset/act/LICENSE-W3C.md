# W3C licence for the imported ACT Rules test cases

The files in `data/testset/act/testcases/` and `data/testset/act/test-assets/` are **unmodified
copies** of material published by the W3C ACT Rules Community Group at <https://act-rules.github.io/>
(retrieved 2026-10-14 by `scripts/import_act.py`). They are redistributed under the
W3C Software and Document Notice and License (SPDX `W3C-20150513`) reproduced in full below.

Copyright notice for the copied material: *This dataset includes material copied from the
ACT Rules Community test cases, <https://act-rules.github.io/testcases.json> and <https://act-rules.github.io/rules/>.
Copyright © 2017–2026 W3C® (MIT, ERCIM, Keio, Beihang).*

**Modifications and derived files.**
- The test-case files and test assets are **not modified**.
- `testcases-filtered.json` is **derived** from `https://act-rules.github.io/testcases.json`: it keeps only the entries
  of the imported rules (entries themselves unchanged) and adds a provenance header. The full
  original had sha256 `a805d865d61ae2418e56a6a9d303fe60c85089c792b897eb9472ea5513156293` and 1134 entries on
  2026-10-14.
- `manifest_act.jsonl` is **derived** metadata written by Klar. (rule id, in-scope WCAG
  criterion, expected rule outcome taken from the index).
- No translations of ACT test cases are included. If translated copies are ever added, they
  must be stored in a separate folder and marked as modified.

**Interpretation note.** The `expected` value of an ACT case is the outcome of the *ACT rule*,
not of the WCAG success criterion: per `ruleAccessibilityRequirements`, a rule outcome `failed`
means the criterion is "not satisfied", while `passed` and `inapplicable` mean "further testing
needed".

**Selection.** Only rules that need judgement are imported (presence/syntax rules are covered
by axe-core). Test assets of rules that are not imported (videos, audio) are not copied. The
largest kept asset, `test-assets/0va7u6/ivanhoe.png` (0.9 MB), is the image-of-text fixture of
rule 0va7u6 (1.4.5) and is needed to render those cases.

Rules imported:

- `0va7u6` — HTML graphics contain no text (<https://act-rules.github.io/rules/0va7u6/>)
- `2ee8b8` — Visible label is part of accessible name (<https://act-rules.github.io/rules/2ee8b8/>)
- `36b590` — Error message describes invalid form field value (<https://act-rules.github.io/rules/36b590/>)
- `5effbb` — Link in context is descriptive (<https://act-rules.github.io/rules/5effbb/>)
- `9bd38c` — Content has alternative for visual reference (<https://act-rules.github.io/rules/9bd38c/>)
- `b49b2e` — Heading is descriptive (<https://act-rules.github.io/rules/b49b2e/>)
- `c4a8a4` — HTML page title is descriptive (<https://act-rules.github.io/rules/c4a8a4/>)
- `cc0f0a` — Form field label is descriptive (<https://act-rules.github.io/rules/cc0f0a/>)
- `e88epe` — Image not in the accessibility tree is decorative (<https://act-rules.github.io/rules/e88epe/>)
- `efbfc7` — Text content that changes automatically can be paused, stopped or hidden (<https://act-rules.github.io/rules/efbfc7/>)
- `fd3a94` — Links with identical accessible names and same context serve equivalent purpose (<https://act-rules.github.io/rules/fd3a94/>)
- `off6ek` — HTML element language subtag matches language (<https://act-rules.github.io/rules/off6ek/>)
- `qt1vmo` — Image accessible name is descriptive (<https://act-rules.github.io/rules/qt1vmo/>)
- `ucwvc8` — HTML page language subtag matches default language (<https://act-rules.github.io/rules/ucwvc8/>)

---

W3C Software And Document Notice And License

This work is being provided by the copyright holders under the following license.

License

By obtaining and/or copying this work, you (the licensee) agree that you have read, understood, and will comply with the following terms and conditions.

Permission to copy, modify, and distribute this work, with or without modification, for any purpose and without fee or royalty is hereby granted, provided that you include the following on ALL copies of the work or portions thereof, including modifications:

- The full text of this NOTICE in a location viewable to users of the redistributed or derivative work.

- Any pre-existing intellectual property disclaimers, notices, or terms and conditions. If none exist, the W3C Software and Document Short Notice should be included.

- Notice of any changes or modifications, through a copyright statement on the new code or document such as "This software or document includes material copied from or derived from [title and URI of the W3C document]. Copyright © [YEAR] W3C® (MIT, ERCIM, Keio, Beihang)."

Disclaimer

This work is provided "AS IS," and copyright holders make no representations or warranties, express or implied, including but not limited to, warranties of merchantability or fitness for any particular purpose or that the use of the software or document will not infringe any third party patents, copyrights, trademarks or other rights.

Copyright holders will not be liable for any direct, indirect, special or consequential damages arising out of any use of the software or document.

The name and trademarks of copyright holders may NOT be used in advertising or publicity pertaining to the work without specific, written prior permission. Title to copyright in this work will at all times remain with copyright holders.
