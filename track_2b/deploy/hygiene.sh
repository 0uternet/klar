#!/bin/sh
# Repository hygiene audit (CI job `hygiene`). Generic checks only; prints every offending line
# and exits 1 if there is any. Run from anywhere inside the repository.
#   1. absolute local paths        2. Co-Authored-By lines (files and commit messages)
#   3. placeholders and TODO/FIXME 4. likely secrets
#   5. files larger than 5 MB outside track_2b/data/; tracked data above 100 MB
#   6. forbidden artefacts (caches, build output, .env files, model weights, logs)
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
self=':!track_2b/deploy/hygiene.sh'
log=$(mktemp)
found() { printf '\n## %s\n%s\n' "$1" "$2" >> "$log"; }
check() { # TITLE OUTPUT
  [ -z "$2" ] || found "$1" "$2"
}

# 1. Absolute local paths (Windows user folders, Linux home directories).
check "absolute local paths" \
  "$(git grep -n -I -i -E 'C:\\Users|C:/Users|/c/Users|/home/[a-z][a-z0-9_-]*/|AppData' -- "$self")"

# 2. Co-Authored-By trailers, in tracked files and in the commit messages.
check "Co-Authored-By in tracked files" "$(git grep -n -I -i -E '^[[:space:]]*co-authored-by:' -- "$self")"
check "Co-Authored-By in commit messages" "$(git log --format='%h %(trailers:key=Co-authored-by,valueonly)' 2>/dev/null | awk 'NF > 1')"

# 3. Placeholders and open work (test data and vendored code excluded).
check "placeholders [X] / TODO / FIXME" \
  "$(git grep -n -I -E '\[X\]|\b(TODO|FIXME)\b' -- "$self" ':!track_2b/data/' ':!*/vendor/*' ':!*package-lock.json')"

# 4. Likely secrets.
check "possible secrets" "$(git grep -n -I -E \
  'hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}|xox[abpr]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----' \
  -- "$self" ':!*package-lock.json')"
check "possible secrets (key = value)" "$(git grep -n -I -i -E \
  '(api[_-]?key|secret|token|password)["'"'"']?[[:space:]]*[:=][[:space:]]*["'"'"'][A-Za-z0-9_./+=-]{24,}["'"'"']' \
  -- "$self" ':!*package-lock.json')"

# 5. Sizes.
sizes() { # "size path" for the tracked files matching the pathspec (GNU or BSD stat)
  if stat -c '%s' . >/dev/null 2>&1; then git ls-files -z -- "$@" | xargs -0 stat -c '%s %n' 2>/dev/null
  else git ls-files -z -- "$@" | xargs -0 stat -f '%z %N' 2>/dev/null; fi
}
check "files larger than 5 MB outside track_2b/data/" "$(sizes ':!track_2b/data/' | awk '$1 > 5242880')"
data=$(sizes track_2b/data | awk '{t += $1} END {print t + 0}')
echo "tracked data: $data bytes"
[ "$data" -le 104857600 ] || found "track_2b/data is larger than 100 MB" "$data bytes"

# 6. Forbidden artefacts.
check "forbidden artefacts" "$(git ls-files | grep -E '(__pycache__|\.pyc$|node_modules/|/dist/|src/klar/api/static/|(^|/)var/|(^|/)models/|(^|/)\.env$|(^|/)\.env\.|\.gguf$|\.safetensors$|\.ckpt$|\.log$|\.DS_Store|\.venv/|\.idea/|\.vscode/)' | grep -v '\.env\.example$')"

if [ -s "$log" ]; then
  cat "$log"; rm -f "$log"
  echo; echo "HYGIENE AUDIT FAILED"; exit 1
fi
rm -f "$log"
echo "HYGIENE AUDIT PASSED"
