#!/bin/sh
# Print the base URL of a bundled model server that is running AND healthy, or nothing.
# llm-gpu (vLLM, text + images) is preferred over llm-cpu (llama.cpp, text only).
# Used by `make eval` and `make record` as their default endpoint.
cd "$(dirname "$0")/.." || exit 0
for svc in llm-gpu llm-cpu; do
  cid=$(docker compose --profile gpu --profile cpu ps -q "$svc" 2>/dev/null | head -n 1)
  [ -n "$cid" ] || continue
  health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$cid" 2>/dev/null)
  [ "$health" = healthy ] || continue
  case $svc in
    llm-gpu) echo "http://llm-gpu:8000/v1" ;;
    llm-cpu) echo "http://llm-cpu:8080/v1" ;;
  esac
  exit 0
done
exit 0
