#!/bin/sh
# Wait until a container is healthy (its Docker HEALTHCHECK) and, when HOST_URL is given and
# curl exists on the host, until HOST_URL answers. Fails fast, with the last log lines, if
# the container exits, keeps restarting, turns unhealthy or the timeout expires.
#
# usage: wait_for.sh CONTAINER_ID TIMEOUT_SECONDS LABEL [HOST_URL]
set -eu
cid=${1:-}; timeout=${2:-300}; label=${3:-container}; url=${4:-}

dump() {
  printf '\nERROR: %s %s. Last log lines:\n' "$label" "$1" >&2
  docker logs --tail 80 "$cid" >&2 2>&1 || true
  echo "Full logs: make logs" >&2
  exit 1
}

[ -n "$cid" ] || { echo "ERROR: $label: no container (did 'docker compose up' fail?)" >&2; exit 1; }

printf '    waiting for %s ' "$label"
start=$(date +%s); next_note=60
while :; do
  info=$(docker inspect -f '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}' "$cid" 2>/dev/null || echo "missing none 0")
  set -- $info
  state=$1; health=$2; restarts=$3
  case $state in exited|dead|missing) dump "stopped (state: $state)" ;; esac
  [ "$restarts" -lt 3 ] || dump "keeps restarting ($restarts restarts)"
  [ "$health" != unhealthy ] || dump "is unhealthy"
  if [ "$state" = running ] && { [ "$health" = healthy ] || [ "$health" = none ]; }; then
    if [ -z "$url" ] || ! command -v curl >/dev/null 2>&1 || curl -fsS --max-time 5 -o /dev/null "$url" 2>/dev/null; then
      printf ' ready (%ss)\n' "$(( $(date +%s) - start ))"
      exit 0
    fi
  fi
  elapsed=$(( $(date +%s) - start ))
  [ "$elapsed" -lt "$timeout" ] || dump "not ready after ${timeout}s"
  if [ "$elapsed" -ge "$next_note" ]; then
    printf '\n    still waiting for %s (%ss, state: %s, health: %s) - follow with: make logs\n    ' "$label" "$elapsed" "$state" "$health"
    next_note=$(( next_note + 60 ))
  fi
  printf '.'
  sleep 3
done
