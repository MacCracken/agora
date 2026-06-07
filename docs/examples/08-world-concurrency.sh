#!/usr/bin/env bash
# 08-world-concurrency.sh — prove the 1.2.0 world-transaction framework
# has NO lost updates under concurrency (ADR 0010 § Phasing bite 1).
#
# Launches PROCS independent `agora worldbench` processes, each running
# COUNT flock'd +1 transactions against ONE shared on-disk world, then
# reads the counter. A correct framework yields exactly PROCS×COUNT —
# any lost update (a broken/missing lock) shows up as a lower total.
#
# This is the cross-process check the unit harness can't do (it's
# single-process); the per-transaction logic itself is unit-tested
# (t122/t123). Mirrors how ADR 0007's fork loop is smoke-tested.
#
# Usage: ./08-world-concurrency.sh [procs] [count]
set -euo pipefail

PROCS="${1:-8}"
COUNT="${2:-300}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="$ROOT/build/agora"
STORE="/tmp/agora-world-smoke-$$"

[ -x "$BIN" ] || { echo "build first: cyrius build src/main.cyr build/agora"; exit 1; }
rm -rf "$STORE"; mkdir -p "$STORE"
trap 'rm -rf "$STORE"' EXIT

echo "launching $PROCS workers x $COUNT transactions against one world..."
pids=()
for _ in $(seq 1 "$PROCS"); do
    "$BIN" worldbench bench "$COUNT" --store "$STORE" >/dev/null 2>&1 &
    pids+=($!)
done
for p in "${pids[@]}"; do wait "$p"; done

EXPECT=$(( PROCS * COUNT ))
GOT=$("$BIN" worldread bench --store "$STORE")
echo "expected $EXPECT, got $GOT"
if [ "$GOT" = "$EXPECT" ]; then
    echo "OK — no lost updates ($PROCS concurrent processes serialized correctly on flock)"
    exit 0
fi
echo "FAIL — lost updates: $(( EXPECT - GOT )) transactions dropped"
exit 1
