"""CSV export, one finding per row. The first line is the disclaimer, prefixed with
'#' (pandas: read_csv(comment="#")). Cells are formula-safe: page text such as
'=HYPERLINK(...)' is prefixed with an apostrophe so spreadsheets never run it."""

from __future__ import annotations

import csv
import io

from klar.models import Scan

COLUMNS = ["id", "criterion", "criterion_name", "level", "outcome", "source", "confidence", "status",
           "page_url", "selector", "excerpt", "content_lang", "explanation", "user_impact", "fix_hint", "fix_diff",
           "reason_code", "reason", "act_rule", "axe_rule", "en301549", "model"]
_FORMULA_START = ("=", "+", "-", "@", chr(9), chr(13))  # = + - @ TAB CR


def safe_cell(value: object) -> str:
    s = "" if value is None else str(value)
    return "'" + s if s.startswith(_FORMULA_START) else s


def to_csv(scan: Scan) -> str:
    from klar.report import disclaimer

    buf = io.StringIO()
    buf.write("# " + disclaimer(scan) + "\n")
    w = csv.DictWriter(buf, fieldnames=COLUMNS, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for f in scan.findings:
        w.writerow({k: safe_cell(v) for k, v in f.model_dump().items()})
    return buf.getvalue()
