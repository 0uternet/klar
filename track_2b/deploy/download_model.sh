#!/bin/sh
# Download the text-only Apertus 1.5 8B GGUF (Q4_K_M, for llama.cpp on CPU) and verify it.
# Build-time / install-time dependency only: once verified, nothing is downloaded again.
#
# Runs on the host (make run-cpu) or inside the `model-download` compose service
# (no curl / sha256 tool needed on the host).
#
# usage: [MODELS_DIR=dir] [FORCE_VERIFY=1] [HF_TOKEN=...] sh deploy/download_model.sh
# exit:  0 verified file present | 1 download or verification failed | 3 missing host tools
set -eu

NAME=apertus-v1.5-8b-text-q4_k_m.gguf
URL=${GGUF_URL:-https://huggingface.co/Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF/resolve/main/$NAME}
SHA256=a037df8d87ff6caacee794ee85f55342f2152e0d359b7389033300c3bee5f299
SIZE=5059027136

here=$(cd "$(dirname "$0")" && pwd)
DIR=${MODELS_DIR:-$here/../models}
DEST=$DIR/$NAME
MARK=$DEST.verified

size_of() { wc -c < "$1" | tr -d ' \t'; }
sha_of() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d' ' -f1
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1
  else openssl dgst -sha256 -r "$1" | cut -d' ' -f1
  fi
}

if [ -f "$DEST" ] && [ -f "$MARK" ] && [ "$(size_of "$DEST")" = "$SIZE" ] && [ "${FORCE_VERIFY:-0}" != 1 ]; then
  echo "    GGUF present and verified: $DEST"
  exit 0
fi

command -v curl >/dev/null 2>&1 || { echo "curl not found on this host" >&2; exit 3; }
command -v sha256sum >/dev/null 2>&1 || command -v shasum >/dev/null 2>&1 || command -v openssl >/dev/null 2>&1 \
  || { echo "no sha256 tool (sha256sum, shasum or openssl) on this host" >&2; exit 3; }

mkdir -p "$DIR"
rm -f "$DEST.bad"
if [ ! -f "$DEST" ]; then
  if [ -f "$DEST.part" ] && [ "$(size_of "$DEST.part")" = "$SIZE" ]; then
    echo "    complete partial download found"
  else
    echo "==> Downloading $NAME (5.06 GB, resumable) from Hugging Face"
    echo "    $URL"
    set -- -fL --retry 5 --retry-delay 5 -C - -o "$DEST.part"
    if [ -n "${HF_TOKEN:-}" ]; then set -- "$@" -H "Authorization: Bearer $HF_TOKEN"; fi
    curl "$@" "$URL"
  fi
  mv "$DEST.part" "$DEST"
fi

echo "==> Verifying $NAME (size + sha256, ~10-30 s)"
actual_size=$(size_of "$DEST")
if [ "$actual_size" != "$SIZE" ]; then
  mv "$DEST" "$DEST.bad"
  echo "ERROR: size $actual_size != expected $SIZE; moved to $DEST.bad, run again to re-download" >&2
  exit 1
fi
actual_sha=$(sha_of "$DEST")
if [ "$actual_sha" != "$SHA256" ]; then
  mv "$DEST" "$DEST.bad"
  echo "ERROR: sha256 $actual_sha != expected $SHA256; moved to $DEST.bad" >&2
  exit 1
fi
printf '%s  %s\n' "$SHA256" "$NAME" > "$MARK"
echo "    OK: $DEST (sha256 $SHA256)"
