#!/bin/sh
# Run the demo scan of the bundled "Gemeinde Musterwil" site inside the running app
# container (`klar demo`), then print where to open Klar., where the report is, and the
# scan's own counters (taken from the report, not from the server's in-memory counter).
#
# usage: [DEMO=0] DC="docker compose [--profile ...]" sh deploy/demo.sh APP_URL
#   DEMO=0: skip the scan, only print where Klar. runs
set -eu
DC=${DC:-docker compose}
url=${1:-http://localhost:8080}

if [ "${DEMO:-1}" = 0 ]; then
  echo
  echo "==> Klar. is running: $url   (DEMO=0: no demo scan)    Stop: make stop"
  echo
  exit 0
fi

mkdir -p var
stamp=var/.demo-started
: > "$stamp"
sleep 1   # file systems with 1 s timestamp resolution

echo "==> Demo scan of the bundled Musterwil site (klar demo)"
rc=0
$DC exec -T app klar demo || rc=$?

reports=""
for f in var/reports/demo-latest.html var/reports/demo-latest.json; do
  [ -f "$f" ] && [ "$f" -nt "$stamp" ] && reports="$reports $f"
done
if [ -z "$reports" ]; then   # other layouts: any report written during the demo
  reports=$(find var -type f -newer "$stamp" \( -name '*.html' -o -name '*.json' \) 2>/dev/null | sort | head -n 5)
fi
rm -f "$stamp"

# Counters of THIS scan, read inside the container (no python needed on the host).
# Line 1: the counters. Line 2: who decided (code / Apertus, live or replayed), see klar.cli.decision_line.
out=$($DC exec -T app python3 -c '
import json, os, sys
path = os.path.join(os.environ.get("KLAR_DATA_DIR", "/app/var"), "reports", "demo-latest.json")
try:
    d = json.load(open(path, encoding="utf-8"))
except Exception:
    sys.exit(0)
sys.stdout.reconfigure(encoding="utf-8")     # as klar itself (the line below uses "·")
s = d.get("stats") or d                      # demo summary (top-level counts) or a single Scan
print("mode=%s pages=%s failed=%s review=%s not_recorded=%s llm_errors=%s" % (
    d.get("mode"), s.get("pages", 1), s.get("failed"), s.get("cantTell"), s.get("not_recorded"),
    s.get("llm_errors")))
try:
    from klar.cli import decision_line
    print(decision_line(s, d.get("mode")))
except Exception:
    pass
' 2>/dev/null || true)
summary=$(printf '%s\n' "$out" | sed -n 1p)
decided=$(printf '%s\n' "$out" | sed -n 2p)

echo
echo "==> Klar. is running"
echo "    Open             : $url"
if [ -n "$reports" ]; then
  echo "    Demo report      :"
  for f in $reports; do echo "      ./${f#./}"; done
else
  echo "    Demo report      : none found under ./var"
fi
[ -z "$summary" ] || echo "    Demo scan        : $summary"
[ -z "$decided" ] || echo "    Decided by       : $decided"
echo "    Data             : ./var (scans, SQLite, reports)"
echo "    Stop / logs      : make stop  |  make logs"
echo

if [ "$rc" -ne 0 ]; then
  echo "ERROR: 'klar demo' failed (exit $rc). The app is still running; see: make logs" >&2
  exit "$rc"
fi
case $summary in
  *not_recorded=0*|"") ;;
  *not_recorded=*) echo "WARNING: some answers were not in the replay recordings (shown as 'can't tell')." >&2 ;;
esac
[ -n "$reports" ] || echo "WARNING: 'klar demo' succeeded but wrote no report file under ./var" >&2
exit 0
