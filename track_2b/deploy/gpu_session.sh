#!/bin/sh
# One GPU session on an NVIDIA workstation (reference: RTX 5090, 32 GB; driver >= 580): start
# Apertus 1.5 8B (text + images) with the official vLLM image, record the demo replay, run the
# evaluation, and collect the hardware facts. All outputs land on the host, ready to commit.
#
# usage (from track_2b/):  sh deploy/gpu_session.sh [--redo STEP ...] [--from STEP]
#   steps: preflight start probe record eval hardware summary
#   Idempotent and resumable: finished steps are remembered in var/gpu_session.done and skipped
#   when the script is run again (preflight and summary always run). Log: var/gpu_session.log.
# knobs: OUT (eval/results/apertus-8b-gpu), SYSTEMS (all five), ALLOW_NO_VISION=1, MIN_FREE_GB (60),
#        RECORD_CONCURRENCY (1)
# Not for CI. On Windows run it inside WSL2 (Ubuntu) with Docker Desktop's WSL integration.
set -u
script="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
cd "$(dirname "$script")/.." || exit 2
mkdir -p var
CUR=arguments
LOG=var/gpu_session.log
DONE=var/gpu_session.done

# Log everything (POSIX sh has no process substitution: re-run ourselves through tee).
if [ -z "${KLAR_GPU_SESSION_LOGGED:-}" ]; then
  KLAR_GPU_SESSION_LOGGED=1; export KLAR_GPU_SESSION_LOGGED
  printf '\n===== gpu_session %s =====\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$LOG"
  { sh "$script" "$@"; echo $? > var/.gpu_session.rc; } 2>&1 | tee -a "$LOG"
  exit "$(cat var/.gpu_session.rc 2>/dev/null || echo 1)"
fi

MODEL=swiss-ai/Apertus-v1.5-8B
GPU_URL=http://llm-gpu:8000/v1
OUT=${OUT:-eval/results/apertus-8b-gpu}
SYSTEMS=${SYSTEMS:-axe,baseline,ours,ours_no_guard,ours_no_context}
MIN_FREE_GB=${MIN_FREE_GB:-60}
# One question at a time while recording, so the demo timings are sequential (as the eval).
RECORD_CONCURRENCY=${RECORD_CONCURRENCY:-1}
LLM_VARS="LLM_BASE_URL=$GPU_URL LLM_NAME=$MODEL LLM_API_KEY=local KLAR_REPLAY=0"
DC="docker compose --profile gpu"

say()  { printf '%s\n' "$*"; }
step_title() { printf '\n==> [%s] %s\n' "$1" "$2"; }
die()  { printf '\nERROR [%s]: %s\nLog: %s. Fix it, then run the same command again (finished steps are skipped).\n' "$CUR" "$*" "$LOG" >&2; exit 1; }
done_step() { grep -qx "$1" "$DONE" 2>/dev/null; }
mark()  { done_step "$1" || echo "$1" >> "$DONE"; }

# --redo STEP / --from STEP
from=""
while [ $# -gt 0 ]; do
  case $1 in
    --redo) shift; [ $# -gt 0 ] && { grep -vx "$1" "$DONE" > "$DONE.tmp" 2>/dev/null; mv "$DONE.tmp" "$DONE" 2>/dev/null; }
            # A new recording moves the eval's answers (same data/replay files) to var/: redo the eval too.
            [ "${1:-}" = record ] && { grep -vx eval "$DONE" > "$DONE.tmp" 2>/dev/null; mv "$DONE.tmp" "$DONE" 2>/dev/null; } ;;
    --from) shift; from=${1:-} ;;
    -h|--help) awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$script"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
  shift
done
if [ -n "$from" ]; then
  keep=1; : > "$DONE.tmp"
  for s in preflight start probe record eval hardware summary; do
    [ "$s" = "$from" ] && keep=0
    if [ "$keep" = 1 ] && done_step "$s"; then echo "$s" >> "$DONE.tmp"; fi
  done
  mv "$DONE.tmp" "$DONE"
fi
should_run() { if done_step "$1"; then say "    (already done: skipped; --redo $1 to run it again)"; return 1; fi; return 0; }

# ------------------------------------------------------------------------------------- preflight
CUR=preflight; step_title "$CUR" "GPU, driver, container toolkit, disk, Hugging Face token"
command -v make >/dev/null 2>&1 || die "GNU make not found (Linux: sudo apt install make; Windows: use WSL2)"
command -v nvidia-smi >/dev/null 2>&1 || die "nvidia-smi not found: install the NVIDIA driver (>= 580)"
sh deploy/preflight.sh gpu || die "Docker is not ready (see above)"
gpu_line=$(nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null | head -n 1)
[ -n "$gpu_line" ] || die "nvidia-smi does not list a GPU"
say "    GPU: $gpu_line"
driver=$(printf '%s' "$gpu_line" | awk -F', ' '{print $2}')
[ "${driver%%.*}" -ge 580 ] 2>/dev/null || die "NVIDIA driver $driver is too old: the Apertus vLLM image is CUDA 13.0 and needs >= 580"
free_kb=$(df -Pk models 2>/dev/null | awk 'NR == 2 {print $4}')
mkdir -p models/huggingface
free_kb=${free_kb:-$(df -Pk . | awk 'NR == 2 {print $4}')}
free_gb=$((free_kb / 1024 / 1024))
say "    free disk where ./models lives: ${free_gb} GB (needed: ${MIN_FREE_GB} GB for weights + images)"
[ "$free_gb" -ge "$MIN_FREE_GB" ] || die "only ${free_gb} GB free, at least ${MIN_FREE_GB} GB needed (MIN_FREE_GB=... to override)"
weights=$(ls -d models/huggingface/hub/models--swiss-ai--Apertus-v1.5-8B/snapshots/*/ 2>/dev/null | head -n 1)
token=${HF_TOKEN:-$(sh deploy/dotenv_get.sh .env HF_TOKEN)}
if [ -z "$weights" ] && [ -z "$token" ]; then
  die "HF_TOKEN missing: accept the licence on https://huggingface.co/swiss-ai/Apertus-v1.5-8B and put HF_TOKEN=hf_... in .env"
fi
[ -n "$weights" ] && say "    weights already cached: $weights" || say "    HF_TOKEN present: the weights (~18 GB) will be downloaded once"
image=$($DC config --images 2>/dev/null | grep vllm | head -n 1)
say "    vLLM image: $image"
docker image inspect "$image" >/dev/null 2>&1 || { say "    pulling the vLLM image (~9 GB, once)"; docker pull "$image" || die "cannot pull $image"; }
say "    GPU access from a container (NVIDIA Container Toolkit):"
docker run --rm --gpus all --entrypoint nvidia-smi "$image" -L \
  || die "containers cannot see the GPU: install the NVIDIA Container Toolkit, run 'sudo nvidia-ctk runtime configure --runtime=docker' and restart Docker"

# ------------------------------------------------------------------------------------- start
CUR=start; step_title "$CUR" "make run-gpu DEMO=0 (vLLM + Klar.; first start downloads the weights)"
if should_run start; then
  # shellcheck disable=SC2086
  make run-gpu DEMO=0 $LLM_VARS || die "make run-gpu failed"
  mark start
fi

# ------------------------------------------------------------------------------------- probe
CUR=probe; step_title "$CUR" "vLLM healthy and the vision probe answers"
cid=$($DC ps -q llm-gpu 2>/dev/null)
[ -n "$cid" ] || die "the llm-gpu container is not running (run: sh deploy/gpu_session.sh --redo start)"
sh deploy/wait_for.sh "$cid" "${LLM_WAIT:-3600}" "llm-gpu (vLLM)" || die "vLLM is not healthy"
health=$($DC exec -T app klar health 2>/dev/null) || die "klar health failed inside the app container"
say "$health" | sed 's/^/    /'
if printf '%s' "$health" | grep -q '"vision": *true'; then
  say "    vision: OK"
elif [ "${ALLOW_NO_VISION:-0}" = 1 ]; then
  say "    WARNING: vision probe failed; continuing because ALLOW_NO_VISION=1 (image criteria will be 'can't tell')"
else
  die "the vision probe failed: image criteria would not be recorded. Check 'make logs SERVICE=llm-gpu' (ALLOW_NO_VISION=1 to continue anyway)"
fi
mark probe

# ------------------------------------------------------------------------------------- record
CUR=record; step_title "$CUR" "make record (demo replay -> data/replay/)"
if should_run record; then
  # shellcheck disable=SC2086
  KLAR_LLM_CONCURRENCY=$RECORD_CONCURRENCY make record BUILD=0 $LLM_VARS || die "make record failed (previous files are in var/replay-backup-*)"
  mark record
fi

# ------------------------------------------------------------------------------------- eval
CUR=eval; step_title "$CUR" "make eval with Apertus 8B on this GPU -> $OUT"
if should_run eval; then
  if git cat-file -e labels-v1:track_2b/data/testset/manifest.jsonl 2>/dev/null; then
    split=test
  else
    split=dev
    say ""
    say "    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    say "    !!  WARNING: git tag labels-v1 not found (git fetch --tags?). Running the DEV split.  !!"
    say "    !!  These numbers are NOT the frozen test results and must not be reported as such.  !!"
    say "    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    say ""
  fi
  # shellcheck disable=SC2086
  make eval BUILD=0 SPLIT="$split" OUT="$OUT" SYSTEMS="$SYSTEMS" $LLM_VARS || die "make eval failed"
  echo "$split" > var/gpu_session.split
  mark eval
fi

# ------------------------------------------------------------------------------------- hardware
CUR=hardware; step_title "$CUR" "hardware and software facts -> $OUT/HARDWARE.json"
if should_run hardware; then
  mkdir -p "$OUT"
  jq_esc() { printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' | tr -d '\r\n'; }
  q() { nvidia-smi --query-gpu="$1" --format=csv,noheader,nounits 2>/dev/null | head -n 1; }
  cuda=$(nvidia-smi 2>/dev/null | sed -n 's/.*CUDA Version: *\([0-9.]*\).*/\1/p' | head -n 1)
  cpu=$(sed -n 's/^model name[[:space:]]*:[[:space:]]*//p' /proc/cpuinfo 2>/dev/null | head -n 1)
  [ -n "$cpu" ] || cpu=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || uname -p)
  threads=$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo "")
  ram_kb=$(sed -n 's/^MemTotal:[[:space:]]*\([0-9]*\) kB/\1/p' /proc/meminfo 2>/dev/null)
  ram_gb=""; [ -n "$ram_kb" ] && ram_gb=$(( (ram_kb + 524288) / 1048576 ))   # rounded GiB, not truncated
  # Under WSL2 /proc/meminfo is the VM's share (half the host by default): record the host RAM too.
  ram_host_gb=""
  if grep -qi microsoft /proc/version 2>/dev/null && command -v powershell.exe >/dev/null 2>&1; then
    b=$(powershell.exe -NoProfile -Command "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory" 2>/dev/null | tr -d '\r')
    [ -n "$b" ] && ram_host_gb=$(( (b + 536870912) / 1073741824 ))
  fi
  docker_v=$(docker version --format '{{.Server.Version}}' 2>/dev/null)
  compose_v=$(docker compose version --short 2>/dev/null)
  os=$(sed -n 's/^PRETTY_NAME="\{0,1\}\([^"]*\)"\{0,1\}/\1/p' /etc/os-release 2>/dev/null | head -n 1)
  [ -n "$os" ] || os=$(uname -sr)
  kernel=$(uname -r)
  vllm_image=$($DC config --images 2>/dev/null | grep vllm | head -n 1)
  # what actually ran: the pulled image's digest, its CUDA, the vLLM version the server reports
  vllm_digest=$(docker image inspect --format '{{index .RepoDigests 0}}' "$vllm_image" 2>/dev/null)
  vllm_cuda=$(docker image inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$vllm_image" 2>/dev/null | sed -n 's/^CUDA_VERSION=//p' | head -n 1)
  vllm_version=$($DC exec -T app python3 -c 'import json, urllib.request; print(json.load(urllib.request.urlopen("http://llm-gpu:8000/version", timeout=10)).get("version", ""))' 2>/dev/null | tr -d '\r')
  # per-page facts of the GPU demo recording (var/ is not committed): report §5 cost and scale
  demo_record=$($DC exec -T app python3 -c 'import glob, json
s = [json.load(open(f, encoding="utf-8"))["stats"] for f in glob.glob("/app/var/reports/record-*.json") if not f.endswith(("-summary.json", "-latest.json"))]
print(json.dumps({"pages": len(s), **{k: round(sum(float(x.get(k) or 0) for x in s), 2) for k in ("seconds", "to_review", "failed", "cantTell", "passed", "asked_apertus", "llm_calls", "tokens_in", "tokens_out")}}))' 2>/dev/null | tr -d '\r')
  commit=$(git rev-parse HEAD 2>/dev/null)
  rev=$(sed -n 's/.*"revision": *"\([^"]*\)".*/\1/p' data/replay/RECORDING.json 2>/dev/null | head -n 1)
  split=$(cat var/gpu_session.split 2>/dev/null || echo "")
  cat > "$OUT/HARDWARE.json" <<EOF
{
  "collected_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "gpu": "$(jq_esc "$(q name)")",
  "gpu_memory_mib": "$(jq_esc "$(q memory.total)")",
  "gpu_count": "$(nvidia-smi -L 2>/dev/null | grep -c '^GPU')",
  "nvidia_driver": "$(jq_esc "$(q driver_version)")",
  "cuda_driver_api": "$(jq_esc "$cuda")",
  "cpu": "$(jq_esc "$cpu")",
  "cpu_threads": "$(jq_esc "$threads")",
  "ram_gb": "$(jq_esc "$ram_gb")",
  "ram_host_gb": "$(jq_esc "$ram_host_gb")",
  "os": "$(jq_esc "$os")",
  "kernel": "$(jq_esc "$kernel")",
  "docker": "$(jq_esc "$docker_v")",
  "docker_compose": "$(jq_esc "$compose_v")",
  "vllm_image": "$(jq_esc "$vllm_image")",
  "vllm_image_digest": "$(jq_esc "$vllm_digest")",
  "vllm_image_cuda": "$(jq_esc "$vllm_cuda")",
  "vllm_version": "$(jq_esc "$vllm_version")",
  "record_llm_concurrency": "$RECORD_CONCURRENCY",
  "demo_record": ${demo_record:-null},
  "model": "$MODEL",
  "model_revision": "$(jq_esc "$rev")",
  "vllm_args": "--max-model-len ${VLLM_MAX_MODEL_LEN:-32768} --gpu-memory-utilization ${VLLM_GPU_MEMORY_UTILIZATION:-0.85} --chat-template-content-format string --seed 0",
  "eval_split": "$(jq_esc "$split")",
  "eval_systems": "$(jq_esc "$SYSTEMS")",
  "klar_commit": "$(jq_esc "$commit")"
}
EOF
  sed 's/^/    /' "$OUT/HARDWARE.json"
  mark hardware
fi

# ------------------------------------------------------------------------------------- summary
CUR=summary; step_title "$CUR" "files to commit"
say "    data/replay/*.jsonl and data/replay/RECORDING.json   (the demo replay)"
for f in results.json table.md responses.jsonl RUNLOG.jsonl HARDWARE.json; do
  if [ -f "$OUT/$f" ]; then say "    $OUT/$f"; else say "    $OUT/$f   (MISSING)"; fi
done
say ""
git status --short -- data/replay "$OUT" 2>/dev/null | sed 's/^/    git: /'
say ""
say "    Commit with:"
say "      git add data/replay $OUT && git commit -m \"Record the Apertus 8B demo replay and GPU evaluation\""
if [ "$(cat var/gpu_session.split 2>/dev/null)" = dev ]; then
  say ""
  say "    REMINDER: the evaluation ran on the DEV split (labels-v1 was missing)."
fi
say ""
say "    The GPU stack is still running (make stop to stop it). Log: $LOG"
