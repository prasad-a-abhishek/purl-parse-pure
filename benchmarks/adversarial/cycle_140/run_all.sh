#!/usr/bin/env bash
# run_all.sh -- 5-second smoke run for every purl-parse-pure fuzz harness.
#
# Each harness is run with `-max_total_time=5` (libFuzzer's wall-clock cap).
# We additionally pass `-seed_inputs=<dir>` so Atheris/libFuzzer loads the
# canonical seed bank rather than starting from an empty corpus.
#
# Usage:
#   ./run_all.sh                      # smoke all harnesses
#   HARNESSES=harness_core_parse.py ./run_all.sh   # smoke one surface
#
# For the full 300s-per-surface corpus run, see T3 (CORPUS_RUN).

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

HARNESSES=${HARNESSES:-"harness_core_parse.py harness_cli_parse.py harness_cli_decode.py harness_cli_validate.py harness_unquote_edge.py"}
SMOKE_SECONDS=${SMOKE_SECONDS:-5}
TIMEOUT_SECONDS=$((SMOKE_SECONDS + 5))

if ! python3 -c "import atheris" 2>/dev/null; then
   echo "FATAL: atheris not installed in current Python env" >&2
   exit 2
fi

fail=0
for h in $HARNESSES; do
   if [[ ! -f "$h" ]]; then
       echo "FAIL  $h  (missing)" >&2
       fail=$((fail + 1))
       continue
   fi

   # Derive the seed dir from the harness name (strip harness_ prefix, strip .py).
   name=${h#harness_}
   name=${name%.py}
   seed_dir="corpus/seed_${name}"
   seed_arg=""
   if [[ -d "$seed_dir" ]]; then
       seed_arg="-seed_inputs=$seed_dir"
   fi

   # Run with timeout. libFuzzer prints progress to stderr; we collapse stdout.
   # `-max_total_time` is in seconds and is the libFuzzer-native wall-clock cap.
   rc=0
   timeout "$TIMEOUT_SECONDS" python3 "$h" \
       -max_total_time="$SMOKE_SECONDS" \
       $seed_arg \
       >/dev/null 2>"$HERE/.smoke_${name}.log" || rc=$?

   if [[ "$rc" -eq 124 ]]; then
       echo "HANG  $h  (timeout after ${TIMEOUT_SECONDS}s wall)"
       fail=$((fail + 1))
   elif [[ "$rc" -ne 0 ]]; then
       echo "FAIL  $h  (exit=$rc) -- see .smoke_${name}.log"
       fail=$((fail + 1))
   else
       echo "PASS   $h  (exit=0, ${SMOKE_SECONDS}s)"
   fi
done

if [[ "$fail" -eq 0 ]]; then
   echo "OK  all ${HARNESSES} harnesses smoke-clean for ${SMOKE_SECONDS}s"
   exit 0
else
   echo "FAIL  $fail harness(es) failed smoke"
   exit 1
fi