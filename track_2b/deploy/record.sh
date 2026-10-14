#!/bin/sh
# `make record`: record the Apertus answers for every page of the bundled demo site into
# ./data/replay (committed, so that `make run` replays them), then prove the recordings are complete.
#
#   1. Start from an empty data/replay/ (old prompt versions must not mix). Existing files are moved
#      to var/replay-backup-<timestamp>/, never deleted. KEEP=1 keeps them and appends.
#   2. `klar record` in a one-off app container on the compose network (reaches llm-gpu / llm-cpu),
#      with ./data/replay mounted read-write.
#   3. `klar replay-check --rescan` in replay mode against the fresh files (mounted read-only).
#   4. data/replay/RECORDING.json: model, revision, endpoint host, date, Klar. commit, counts.
#
# usage (from the Makefile): KEEP=0|1 DC="docker compose" sh deploy/record.sh
# LLM_BASE_URL / LLM_NAME / LLM_API_KEY / KLAR_REPLAY=0 come from the environment (make exports them).
set -u
cd "$(dirname "$0")/.."
DC=${DC:-docker compose}
export MSYS_NO_PATHCONV=1                       # Git Bash: keep host:container volume specs intact
here=$(pwd -W 2>/dev/null || pwd)               # Windows-style path under Git Bash, POSIX elsewhere
ts=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p data/replay var

ENDPOINT_LIB=1 . deploy/endpoint.sh
host=$(klar_host "${LLM_BASE_URL:-}")
mode=$(klar_mode "${KLAR_REPLAY:-0}" "${LLM_BASE_URL:-}")

# 1. Clean start (backup, never delete).
if [ "${KEEP:-0}" != 1 ] && [ -n "$(ls -A data/replay 2>/dev/null | grep -v '^\.gitkeep$')" ]; then
  backup=var/replay-backup-$ts
  mkdir -p "$backup"
  for f in data/replay/* data/replay/.[!.]*; do
    [ -e "$f" ] || continue
    [ "$(basename "$f")" = .gitkeep ] && continue
    mv "$f" "$backup"/
  done
  echo "==> Previous recordings moved to $backup (KEEP=1 would have kept them)"
fi

# 2. Record.
echo "==> klar record: every demo page, live endpoint $host ($mode), model ${LLM_NAME:-?}"
$DC run --rm --no-deps -T -v "$here/data/replay:/app/data/replay:z" app klar record
rec_rc=$?

# 3. Replay check against the fresh recordings (replay mode, exact keys).
echo "==> klar replay-check --rescan (replay mode, the new recordings only)"
check_line=$($DC run --rm --no-deps -T -e KLAR_REPLAY=1 -e LLM_BASE_URL= \
  -v "$here/data/replay:/app/data/replay:ro,z" app klar replay-check --rescan)
check_rc=$?
echo "    $check_line"

# 4. Model facts: what the server says it serves, and the weights revision if it can be found.
models_json=$($DC run --rm --no-deps -T app python3 -c '
import json, os, urllib.request
url = os.environ.get("LLM_BASE_URL", "").rstrip("/") + "/models"
req = urllib.request.Request(url, headers={"Authorization": "Bearer " + os.environ.get("LLM_API_KEY", "local")})
try:
    data = json.load(urllib.request.urlopen(req, timeout=15)).get("data", [])
    print(json.dumps([{k: m.get(k) for k in ("id", "root", "owned_by", "max_model_len") if k in m} for m in data]))
except Exception:
    print("[]")
' 2>/dev/null || echo "[]")
revision=""; revision_source=""
model_dir=$(printf '%s' "${LLM_NAME:-}" | sed 's#/#--#g')
hf_cache=${HF_CACHE_DIR:-$(sh deploy/dotenv_get.sh .env HF_CACHE_DIR)}
ref=${hf_cache:-models/huggingface}/hub/models--$model_dir/refs/main
if [ "$host" = llm-gpu ] || [ "$host" = llm ]; then
  if [ -f "$ref" ]; then revision=$(tr -d ' \r\n' < "$ref"); revision_source="huggingface cache refs/main"; fi
elif [ "$host" = llm-cpu ]; then
  mark=models/apertus-v1.5-8b-text-q4_k_m.gguf.verified
  if [ -f "$mark" ]; then revision="sha256:$(cut -d' ' -f1 "$mark")"; revision_source="gguf file sha256"; fi
fi
commit=$(git rev-parse HEAD 2>/dev/null || true)
dirty=false; [ -n "$(git status --porcelain -- src 2>/dev/null)" ] && dirty=true

# 5. RECORDING.json, written by Python inside the container (no Python needed on the host).
$DC run --rm --no-deps -T -v "$here/data/replay:/app/data/replay:z" \
  -e REC_MODELS="$models_json" -e REC_REVISION="$revision" -e REC_REVISION_SOURCE="$revision_source" \
  -e REC_HOST="$host" -e REC_MODE="$mode" -e REC_COMMIT="$commit" -e REC_DIRTY="$dirty" \
  -e REC_RECORD_RC="$rec_rc" -e REC_CHECK_RC="$check_rc" -e REC_CHECK_LINE="$check_line" \
  app python3 -c '
import datetime, glob, json, os
import klar
reports = os.path.join(os.environ.get("KLAR_DATA_DIR", "/app/var"), "reports")
def load(name):
    try:
        return json.load(open(os.path.join(reports, name), encoding="utf-8"))
    except Exception:
        return None
keys = ("pages", "errors", "failed", "cantTell", "passed", "not_recorded", "llm_errors", "llm_calls",
        "tokens_in", "tokens_out", "replay_loose_hits", "ai_requests")
rec, chk = load("record-latest.json"), load("replay-check-latest.json")
files = {}
for f in sorted(glob.glob("/app/data/replay/*.jsonl")):
    with open(f, encoding="utf-8") as fh:
        files[os.path.basename(f)] = sum(1 for line in fh if line.strip())
e = os.environ
doc = {
    "model": e.get("LLM_NAME"),
    "served_models": json.loads(e.get("REC_MODELS") or "[]"),
    "revision": e.get("REC_REVISION") or None,
    "revision_source": e.get("REC_REVISION_SOURCE") or None,
    "endpoint_host": e.get("REC_HOST") or None,
    "mode": e.get("REC_MODE"),
    "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "klar_commit": e.get("REC_COMMIT") or None,
    "klar_commit_dirty": e.get("REC_DIRTY") == "true",
    "klar_version": getattr(klar, "__version__", None),
    "record": {k: rec.get(k) for k in keys} if rec else None,
    "record_exit_code": int(e.get("REC_RECORD_RC", "1")),
    "replay_check": {"ok": e.get("REC_CHECK_RC") == "0", "summary": e.get("REC_CHECK_LINE"),
                     **({k: chk.get(k) for k in keys} if chk else {})},
    "files": files,
    "records_total": sum(files.values()),
}
with open("/app/data/replay/RECORDING.json", "w", encoding="utf-8", newline="\n") as fh:
    json.dump(doc, fh, ensure_ascii=False, indent=2)
    fh.write("\n")
print(json.dumps({k: doc[k] for k in ("model", "revision", "endpoint_host", "recorded_at", "klar_commit", "records_total")}))
'
echo
echo "==> Recording finished"
echo "    model     : ${LLM_NAME:-?}   revision: ${revision:-unknown}   endpoint: $host ($mode)"
echo "    files     : $(ls data/replay 2>/dev/null | tr '\n' ' ')"
echo "    check     : $check_line"
if [ "$rec_rc" -ne 0 ] || [ "$check_rc" -ne 0 ]; then
  echo "ERROR: recording incomplete (klar record exit $rec_rc, replay-check exit $check_rc). See the lines above." >&2
  exit 1
fi
echo "    commit    : git add data/replay   (the .jsonl files and RECORDING.json)"
