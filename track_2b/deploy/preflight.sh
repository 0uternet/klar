#!/bin/sh
# Checks Docker before any make target touches it, with actionable messages.
# usage: preflight.sh [gpu]
set -eu

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

command -v docker >/dev/null 2>&1 \
  || fail "docker not found. Install Docker Engine (Linux) or Docker Desktop (macOS/Windows): https://docs.docker.com/get-docker/"

docker info >/dev/null 2>&1 \
  || fail "cannot reach the Docker daemon. Start Docker (Desktop), or on Linux add your user to the 'docker' group (then log in again)."

v=$(docker compose version --short 2>/dev/null || true)
[ -n "$v" ] || fail "the Docker Compose plugin is missing ('docker compose'). Install Compose v2.24+: https://docs.docker.com/compose/install/"
major=$(printf '%s' "$v" | sed -n 's/^v\{0,1\}\([0-9][0-9]*\)\.\([0-9][0-9]*\).*/\1/p')
minor=$(printf '%s' "$v" | sed -n 's/^v\{0,1\}\([0-9][0-9]*\)\.\([0-9][0-9]*\).*/\2/p')
if [ -n "$major" ] && [ -n "$minor" ]; then
  if [ "$major" -lt 2 ] || { [ "$major" -eq 2 ] && [ "$minor" -lt 24 ]; }; then
    fail "Docker Compose $v is too old: Klar. needs v2.24 or newer (depends_on 'required: false', '!reset'). Update Docker."
  fi
fi

if [ "${1:-}" = gpu ]; then
  if ! docker info --format '{{json .Runtimes}} {{json .CDISpecDirs}}' 2>/dev/null | grep -qi nvidia \
     && ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "WARNING: no NVIDIA runtime/driver detected. 'make run-gpu' needs an NVIDIA GPU, driver >= 580" >&2
    echo "         (the vLLM image is CUDA 13.0) and the NVIDIA Container Toolkit:" >&2
    echo "         https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html" >&2
    echo "         No GPU? Use 'make run-cpu' (text only) or a Swiss cloud endpoint in .env." >&2
  fi
fi
exit 0
