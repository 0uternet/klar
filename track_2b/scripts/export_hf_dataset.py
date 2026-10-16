"""Build the Hugging Face dataset folder from the repository.

    python scripts/export_hf_dataset.py --results eval/results/apertus-8b-gpu [--results ...] [--out dist/hf-dataset]

The dataset has three parts:
  * evaluation dataset   cases/ (the HTML test cases, unchanged) and data/cases.jsonl (one row per case)
  * model responses      data/responses.jsonl: every question Apertus answered while a case was scored,
                         from the `responses.jsonl` of each evaluation run given with --results
  * metadata             data/metadata.jsonl: per case the criterion, language, split, source, ACT rule,
                         template group, trap flag and the instance-level licence
plus results/<run>/ (results.json, table.md) and the dataset card README.md, which starts from
data/testset/README.md. Development tool: it reads the repository and writes only to --out.
Upload (needs a write token, publishes the folder):
    hf upload <user>/klar-wcag-judgement dist/hf-dataset --repo-type dataset
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTSET = ROOT / "data" / "testset"
CASE_FIELDS = ("case_id", "criterion", "page_lang", "source", "split", "expected", "path", "target_selector",
               "pages", "notes", "rule", "alt_expected")
META_FIELDS = ("case_id", "criterion", "page_lang", "source", "split", "act_rule", "template_id", "trap",
               "difficulty", "tags", "license")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", action="append", required=True, help="an evaluation run directory (repeatable)")
    ap.add_argument("--out", default=str(ROOT / "dist" / "hf-dataset"))
    args = ap.parse_args()

    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    (out / "data").mkdir(parents=True)

    rows = [json.loads(line) for line in (TESTSET / "manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    with (out / "data" / "cases.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps({k: r.get(k) for k in CASE_FIELDS}, ensure_ascii=False) + "\n")
    with (out / "data" / "metadata.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps({k: r.get(k) for k in META_FIELDS}, ensure_ascii=False) + "\n")

    # The cases themselves, with the licences and the labelling protocol next to them.
    for part in ("generated", "act"):
        shutil.copytree(TESTSET / part, out / "cases" / part)
    for f in ("PROTOCOL.md", "STATS.md", "LICENSE-CDLA-Permissive-2.0.txt", "review_sample.csv", "review_relabel.csv"):
        if (TESTSET / f).is_file():
            shutil.copy2(TESTSET / f, out / f)

    n_resp = 0
    with (out / "data" / "responses.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for res in args.results:
            run_dir = (ROOT / res) if not Path(res).is_absolute() else Path(res)
            run = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))["run"]
            for line in (run_dir / "responses.jsonl").read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rec = json.loads(line)
                    rec = {"run_id": run.get("id"), "split": run.get("split"), **rec}
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    n_resp += 1
            dest = out / "results" / run_dir.name
            dest.mkdir(parents=True)
            for f in ("results.json", "table.md"):
                shutil.copy2(run_dir / f, dest / f)

    card = (TESTSET / "README.md").read_text(encoding="utf-8")
    (out / "README.md").write_text(card, encoding="utf-8", newline="\n")
    size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    print(f"{out}: {len(rows)} cases, {n_resp} model responses, {size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
