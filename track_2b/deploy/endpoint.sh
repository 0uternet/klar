#!/bin/sh
# Sovereignty banner: says where inference runs, which setting chose it, and where the data goes.
# The mode rules mirror detect_mode() in src/klar/config.py.
#
# usage: endpoint.sh TARGET KLAR_REPLAY LLM_BASE_URL LLM_NAME [DATA_DIR] [CONFIG_SOURCE]
#   TARGET        make target (run | run-gpu | run-cpu | eval | ...), used for consistency warnings
#   CONFIG_SOURCE where LLM_BASE_URL came from (make command line, shell environment, .env, default)
# Also usable as a function library: ENDPOINT_LIB=1 . deploy/endpoint.sh; klar_mode "$replay" "$url"

klar_host() { # URL -> lower-case host, without scheme, credentials, port, path or [brackets]
  printf '%s' "$1" | sed -e 's#^[A-Za-z][A-Za-z0-9+.-]*://##' -e 's#^[^@/]*@##' -e 's|[/?#].*$||' \
    | sed -e 's#^\[\(.*\)\].*$#\1#' -e 's#^\([^:]*\):[0-9]*$#\1#' -e 's#\.$##' | tr 'A-Z' 'a-z'
}

klar_safe_url() { # URL -> the same URL without user:password@, query string or fragment (never print secrets)
  printf '%s' "$1" | sed -e 's#^\([A-Za-z][A-Za-z0-9+.-]*://\)[^@/]*@#\1#' -e 's|[?#].*$||'
}

klar_mode() { # REPLAY URL -> replay | local | swiss_cloud | external
  case $(printf '%s' "$1" | tr 'A-Z' 'a-z') in 1|true|yes|on) echo replay; return ;; esac
  [ -n "$2" ] || { echo replay; return; }
  h=$(klar_host "$2")
  [ -n "$h" ] || { echo replay; return; }
  case $h in
    llm-gpu|llm-cpu|llm|localhost|host.docker.internal|127.0.0.1|*.localhost) echo local; return ;;
    10.*|127.*|192.168.*|169.254.*|172.1[6-9].*|172.2[0-9].*|172.3[01].*) echo local; return ;;
    ::1|fc*:*|fd*:*|fe80:*) echo local; return ;;
    *.local|*.internal|*.lan|*.home.arpa) echo local; return ;;
    phoeniqs.com|*.phoeniqs.com|cscs.ch|*.cscs.ch) echo swiss_cloud; return ;;
  esac
  case $h in *.*|*:*) echo external ;; *) echo local ;; esac   # dot-less name = LAN/Docker service
}

[ -n "${ENDPOINT_LIB:-}" ] && return 0 2>/dev/null

target=${1:-run}; replay=${2:-}; url=${3:-}; model=${4:-swiss-ai/Apertus-v1.5-8B}; data=${5:-./var}; source=${6:-}
mode=$(klar_mode "$replay" "$url")
host=$(klar_host "$url")
shown=$(klar_safe_url "$url")
echo
echo "==> Klar. | make $target"
case $mode in
  replay)
    echo "    Mode         : replay  - recorded Apertus answers from data/replay; no model call, no key, no download"
    echo "    LLM endpoint : none (replay)" ;;
  local)
    echo "    Mode         : local"
    echo "    LLM endpoint : $shown  (on-premise: inference on this machine / in your network)" ;;
  swiss_cloud)
    echo "    Mode         : swiss_cloud"
    echo "    LLM endpoint : $shown  (Swiss cloud provider, see its own data-handling terms)"
    echo "                   Only the minimal context of each question is sent there; pages stay here." ;;
  external)
    echo "    Mode         : external"
    echo "    LLM endpoint : $shown  (EXTERNAL: question context leaves your infrastructure)" ;;
esac
if [ -n "$source" ]; then
  if [ "$mode" = replay ] && [ -n "$url" ]; then
    echo "    Configured by: KLAR_REPLAY=$replay (LLM_BASE_URL from $source is ignored)"
  elif [ -z "$url" ] && { [ "$source" = "shell environment" ] || [ "$source" = "make command line" ]; }; then
    echo "    Configured by: $source, where LLM_BASE_URL is set but empty (this wins over .env: replay)"
  else
    echo "    Configured by: $source"
  fi
fi
echo "    Model        : $model"
echo "    Your data    : scans, screenshots, reports and SQLite stay in $data on this machine"
echo "    Audited site : fetched directly by the headless Chromium inside Klar.; no other third-party calls"

# Consistency between the endpoint and the inference server this target starts.
if [ "$mode" = replay ]; then
  case $target in run-gpu|run-cpu)
    echo "    NOTE: replay mode is on (KLAR_REPLAY=1 or no LLM_BASE_URL): the model server starts but is not used." ;;
  esac
else
  case $host in
    llm|llm-gpu) [ "$target" = run-gpu ] || [ "$target" = eval ] || [ "$target" = record ] \
      || echo "    WARNING: LLM_BASE_URL points to the bundled vLLM server, which only 'make run-gpu' starts." ;;
    llm-cpu) [ "$target" = run-cpu ] || [ "$target" = eval ] || [ "$target" = record ] \
      || echo "    WARNING: LLM_BASE_URL points to the bundled llama.cpp server, which only 'make run-cpu' starts." ;;
    *) case $target in run-gpu|run-cpu)
         echo "    NOTE: LLM_BASE_URL ($source) is the endpoint above, so the local model server is started but not used."
         echo "          To use it: make $target LLM_BASE_URL=http://llm-${target#run-}:$( [ "$target" = run-gpu ] && echo 8000 || echo 8080 )/v1 LLM_NAME=swiss-ai/Apertus-v1.5-8B LLM_API_KEY=local" ;;
       esac ;;
  esac
fi
echo
