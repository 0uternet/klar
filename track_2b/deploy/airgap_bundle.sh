#!/bin/sh
# Offline bundle for an air-gapped site (docs/DEPLOYMENT.md, architecture b).
#
#   sh deploy/airgap_bundle.sh save [cpu|gpu|all]   connected machine: build/pull the images,
#        download + verify the weights, write dist/klar-images-<what>.tar and dist/klar-offline.env
#   sh deploy/airgap_bundle.sh load                 air-gapped machine: docker load dist/*.tar
#
# Transfer: this repository checkout, dist/ and models/ (weights). The images are re-tagged
# with plain local names because a `docker load`ed image is not always resolvable by its
# registry digest; dist/klar-offline.env points docker-compose.yml at those names.
set -eu
cd "$(dirname "$0")/.."

cmd=${1:-}; what=${2:-cpu}
APP=${KLAR_IMAGE:-klar:local}
VLLM_LOCAL=klar-offline/vllm-apertus:1.5
LLAMA_LOCAL=klar-offline/llama-cpp-server:b11243

image_of() { # profile pattern -> image reference used by docker-compose.yml
  docker compose --profile "$1" config --images | grep "$2" | head -n 1
}

case $cmd in
save)
  case $what in cpu|gpu|all) ;; *) echo "usage: airgap_bundle.sh save cpu|gpu|all" >&2; exit 2 ;; esac
  mkdir -p dist models/huggingface var eval/results
  echo "==> Building the app image ($APP)"
  docker compose build app
  images=$APP
  env_out=dist/klar-offline.env
  printf '# Append to .env on the air-gapped machine.\nHF_HUB_OFFLINE=1\n' > "$env_out"

  if [ "$what" = cpu ] || [ "$what" = all ]; then
    src=$(image_of cpu llama.cpp)
    echo "==> llama.cpp server image: $src"
    docker pull "$src"; docker tag "$src" "$LLAMA_LOCAL"
    images="$images $LLAMA_LOCAL"
    echo "LLAMACPP_IMAGE=$LLAMA_LOCAL" >> "$env_out"
    sh deploy/download_model.sh
  fi

  if [ "$what" = gpu ] || [ "$what" = all ]; then
    src=$(image_of gpu vllm)
    echo "==> vLLM image (Apertus 1.5 release, ~9 GB compressed): $src"
    docker pull "$src"; docker tag "$src" "$VLLM_LOCAL"
    images="$images $VLLM_LOCAL"
    echo "VLLM_IMAGE=$VLLM_LOCAL" >> "$env_out"
    token=${HF_TOKEN:-$(sh deploy/dotenv_get.sh .env HF_TOKEN)}
    [ -n "$token" ] || echo "WARNING: HF_TOKEN is empty; the swiss-ai/Apertus-v1.5-8B repo is gated (accept the licence on huggingface.co first)" >&2
    echo "==> Downloading swiss-ai/Apertus-v1.5-8B weights (~18 GB) into models/huggingface (no GPU needed)"
    docker run --rm -e HF_TOKEN="$token" -e HF_HUB_DISABLE_TELEMETRY=1 \
      -v "$(pwd)/models/huggingface:/root/.cache/huggingface:z" \
      --entrypoint python3 "$src" \
      -c "from huggingface_hub import snapshot_download; print(snapshot_download('swiss-ai/Apertus-v1.5-8B'))"
  fi

  out=dist/klar-images-$what.tar
  echo "==> docker save -> $out ($images)"
  # shellcheck disable=SC2086
  docker save -o "$out" $images
  echo
  echo "Bundle ready. Copy to the air-gapped machine:"
  echo "  1. this repository checkout (git bundle / archive)   2. dist/   3. models/"
  echo "Then there: sh deploy/airgap_bundle.sh load && cat dist/klar-offline.env >> .env"
  echo "            make run-$what BUILD=0     (or: make run BUILD=0 for replay)"
  echo "            make airgap-check BUILD=0 AIRGAP_LLM=$( [ "$what" = all ] && echo cpu || echo "$what" )"
  ;;
load)
  found=0
  for f in dist/klar-images-*.tar; do
    [ -f "$f" ] || continue
    echo "==> docker load -i $f"; docker load -i "$f"; found=1
  done
  [ "$found" = 1 ] || { echo "ERROR: no dist/klar-images-*.tar found" >&2; exit 1; }
  echo "Loaded. Next: cat dist/klar-offline.env >> .env, then make run-cpu|run-gpu BUILD=0"
  ;;
*)
  echo "usage: sh deploy/airgap_bundle.sh save [cpu|gpu|all] | load" >&2; exit 2 ;;
esac
