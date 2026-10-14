#!/bin/sh
# Air-gap proof (make airgap-check). Starts Klar. on an internal-only Docker network
# (deploy/compose.airgap.yml: no gateway, no NAT) and passes only if
#   1. the app container (and the LLM container, if any) cannot open a connection to the internet,
#   2. `klar demo` still scans the bundled demo site end to end,
#   3. /api/health answers from inside the network.
#
# usage: [AIRGAP_LLM=replay|cpu|gpu] [BUILD=1|0] [KEEP=1] sh deploy/airgap_check.sh
#   replay  (default) recorded Apertus answers, works on any machine
#   cpu     llama.cpp + text-only GGUF (needs models/apertus-v1.5-8b-text-q4_k_m.gguf)
#   gpu     vLLM + Apertus 1.5 8B (needs an NVIDIA GPU and the weights in models/huggingface)
set -eu
cd "$(dirname "$0")/.."

LLM=${AIRGAP_LLM:-replay}
BUILD=${BUILD:-1}
P=klar-airgap
GGUF=models/apertus-v1.5-8b-text-q4_k_m.gguf
HF_WEIGHTS=models/huggingface/hub/models--swiss-ai--Apertus-v1.5-8B

profile=""; svc=""
case $LLM in
  replay)
    export KLAR_REPLAY=1 LLM_BASE_URL="" ;;
  cpu)
    [ -f "$GGUF" ] || { echo "ERROR: $GGUF is missing. Fetch it first (build-time step): make download-model" >&2; exit 1; }
    profile=cpu; svc=llm-cpu
    export KLAR_REPLAY=0 LLM_BASE_URL=http://llm-cpu:8080/v1 LLM_NAME=swiss-ai/Apertus-v1.5-8B LLM_API_KEY=local ;;
  gpu)
    [ -d "$HF_WEIGHTS" ] || { echo "ERROR: $HF_WEIGHTS is missing. Run 'make run-gpu' once with network (downloads the weights)." >&2; exit 1; }
    profile=gpu; svc=llm-gpu
    export KLAR_REPLAY=0 LLM_BASE_URL=http://llm-gpu:8000/v1 LLM_NAME=swiss-ai/Apertus-v1.5-8B LLM_API_KEY=local ;;
  *)
    echo "usage: AIRGAP_LLM=replay|cpu|gpu sh deploy/airgap_check.sh" >&2; exit 2 ;;
esac

dc() {
  if [ -n "$profile" ]; then
    docker compose -p "$P" -f docker-compose.yml -f deploy/compose.airgap.yml --profile "$profile" "$@"
  else
    docker compose -p "$P" -f docker-compose.yml -f deploy/compose.airgap.yml "$@"
  fi
}

# Python probe, run INSIDE a container: every target must be unreachable.
PROBE='
import socket, sys
bad = 0
for host, port in (("1.1.1.1", 443), ("9.9.9.9", 53), ("huggingface.co", 443), ("github.com", 443)):
    try:
        socket.create_connection((host, port), timeout=5).close()
        print(f"      FAIL  {host}:{port} is reachable"); bad += 1
    except OSError as exc:
        print(f"      ok    {host}:{port} unreachable ({type(exc).__name__})")
sys.exit(1 if bad else 0)
'

status=1
cleanup() {
  if [ "$status" -ne 0 ]; then
    echo; echo "AIR-GAP CHECK FAILED. Last log lines:" >&2
    dc logs --no-color --tail 60 >&2 2>&1 || true
  fi
  if [ "${KEEP:-0}" = 1 ]; then
    echo "    KEEP=1: containers left running (docker compose -p $P ... down to remove)"
  else
    dc down --remove-orphans >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo
echo "==> Air-gap check (LLM: $LLM)"
echo "--- build time (network allowed): images and weights must be present beforehand"
mkdir -p var eval/results models/huggingface
if [ "$BUILD" = 1 ]; then docker compose build app; fi
for img in $(dc config --images); do
  if docker image inspect "$img" >/dev/null 2>&1; then
    echo "    image present: $img"
  elif [ "$img" = "${KLAR_IMAGE:-klar:local}" ]; then
    echo "ERROR: image $img is missing; run with BUILD=1" >&2; exit 1
  else
    echo "    pulling (build-time step): $img"; docker pull "$img"
  fi
done

echo "--- run time: NO network (internal Docker network '${P}_default')"
dc down --remove-orphans >/dev/null 2>&1 || true
if [ -n "$svc" ]; then
  dc up -d --no-build "$svc"
  sh deploy/wait_for.sh "$(dc ps -q "$svc")" "${LLM_WAIT:-1800}" "$svc (offline)"
fi
dc up -d --no-build app
sh deploy/wait_for.sh "$(dc ps -q app)" "${APP_WAIT:-300}" "app (offline)"

echo "--- proof 1: the app container cannot reach the internet"
dc exec -T app python3 -c "$PROBE"
if [ "$svc" = llm-gpu ]; then
  echo "--- proof 1b: the inference container cannot reach the internet either"
  dc exec -T llm-gpu python3 -c "$PROBE"
elif [ "$svc" = llm-cpu ]; then
  echo "--- proof 1b: the inference container cannot reach the internet either"
  if dc exec -T llm-cpu curl -sS --max-time 5 -o /dev/null https://huggingface.co 2>/dev/null; then
    echo "      FAIL  llm-cpu reached https://huggingface.co" >&2; exit 1
  fi
  echo "      ok    llm-cpu: https://huggingface.co unreachable"
fi

echo "--- proof 2: end-to-end demo scan of the bundled site, offline"
dc exec -T app klar demo

echo "--- proof 3: health, from inside the network"
health=$(dc exec -T app curl -fsS --max-time 10 http://127.0.0.1:8080/api/health)
echo "      $health"

status=0
echo
echo "AIR-GAP CHECK PASSED: Klar. ran and completed a scan with no network route out (LLM: $LLM)."
echo "Reports: ./var"
