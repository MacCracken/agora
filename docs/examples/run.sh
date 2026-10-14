#!/usr/bin/env bash
# docs/examples/run.sh — run the example smokes the way each one needs to be run.
#
# Why (1.8.2): the smokes are the only proof of agora's wire behaviour that the
# unit suites cannot reach, and until 1.8.2 nothing in the repo could run them:
# the README's "run them in order" contract did not hold (09, 10, 18, 19 and 20
# `rm -rf ./bbs ./keys` on exit; 03, 06, 11-13, 15, 24, 26 and 27 need a
# registered `qix`), and six scripts were client-only, each needing a server
# started by hand under a model named only in its header. Every release from
# 1.6.7 to 1.8.1 was verified with a throwaway harness. This is that harness,
# made the contract — CI runs it under both serve models.
#
# Each script runs from the repo root with a clean ./bbs and ./keys (several
# scripts use those paths, so the runner REFUSES to start if either already
# exists — move your own data aside, or pass --force to let it be deleted).
#
# Usage: docs/examples/run.sh [--model fork|poll|both] [--fast] [--force]
#                             [--skip NN[,NN...]] [NN ...]
#   --model  serve model(s) for the scripts that start a server and honour
#            AGORA_SERVE, and for the client-only ones (default: both)
#   --fast   skip the slow halves (26's 80 s idle wait, 31's fork-mode wait)
#   --skip   leave these out (e.g. --skip 01 when CI has already built and tested)
#   NN ...   run only these
# Logs: build/smoke-logs/<script>[-<model>].log. Exit 0 iff every run passed.

set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT" || exit 2
EX=docs/examples
PORT="${AGORA_SMOKE_PORT:-2323}"
LOGS="$ROOT/build/smoke-logs"

MODELS="fork poll"
FAST=0
FORCE=0
SKIP=","
ONLY=""
while [ $# -gt 0 ]; do
    case "$1" in
        --model)
            case "${2:-}" in
                fork|poll) MODELS="$2" ;;
                both) MODELS="fork poll" ;;
                *) echo "run.sh: --model fork|poll|both" >&2; exit 2 ;;
            esac
            shift 2 ;;
        --fast)  FAST=1; shift ;;
        --force) FORCE=1; shift ;;
        --skip)  SKIP=",${2:-},"; shift 2 ;;
        -h|--help) sed -n '2,30p' "$0"; exit 0 ;;
        [0-9][0-9]) ONLY="$ONLY $1"; shift ;;
        *) echo "run.sh: unknown argument '$1' (see --help)" >&2; exit 2 ;;
    esac
done

if [ "$FORCE" -eq 0 ]; then
    for d in bbs keys; do
        if [ -e "./$d" ]; then
            echo "run.sh: ./$d exists — the smokes create and delete it. Move it aside or pass --force." >&2
            exit 2
        fi
    done
fi
[ -x ./build/agora ] || { echo "run.sh: build first: CYRIUS_DCE=1 cyrius build src/main.cyr build/agora" >&2; exit 2; }
mkdir -p "$LOGS"

# NN kind needs   — kind: cli | self | own | client;  needs: - | reg (a fresh store
# with qix registered by 02 first) | mud (the sibling Yeoman's Descent repo).
TABLE="
01 cli    -
02 cli    -
03 cli    reg
04 client -
05 client reg
06 cli    reg
07 self   -
08 cli    -
09 self   -
10 self   -
11 self   reg
12 self   reg
13 self   reg
14 self   -
15 self   reg
16 self   -
17 self   -
18 self   -
19 self   -
20 self   mud
21 self   -
22 self   -
23 client -
24 own    reg
25 client -
26 client reg
27 client reg
28 own    -
29 own    -
30 own    -
31 own    -
32 own    -
33 own    -
34 own    -
35 own    -
36 own    -
37 own    -
38 own    -
39 own    -
"

pass=0; fail=0; skipped=0; failed=""
SRV=""

# A fork-mode connection child outlives its stopped server long enough to run its
# close path — 1.8.1's door checkpoint writes ./bbs/.users/<fp>/games/ — so wait
# for any process still serving ./bbs first, or the next smoke starts on its debris
# (found at 1.9.0: a jabberwacky.sav landed after the clean and the next run refused).
clean()  { local k=0
           while pgrep -f -- '--store \./bbs( |$)' >/dev/null && [ $k -lt 50 ]; do sleep 0.1; k=$((k + 1)); done
           rm -rf ./bbs ./keys; }
reg()    { clean; bash "$EX/02-register-and-post.sh" >"$LOGS/register.log" 2>&1; }
port_busy() { (exec 3<>"/dev/tcp/127.0.0.1/$PORT") 2>/dev/null; }
# A self-starting smoke may still be tearing its own server down on $PORT, and
# an old listener answering would make a failed bind look like a started server.
port_free() { local k=0; while port_busy && [ $k -lt 100 ]; do sleep 0.1; k=$((k + 1)); done; }
serve()  { port_free
           AGORA_SERVE="$1" ./build/agora serve "$PORT" --store ./bbs >"$LOGS/server-$2-$1.log" 2>&1 & SRV=$!
           local k=0; while [ $k -lt 50 ]; do
               kill -0 "$SRV" 2>/dev/null || { echo "run.sh: server for $2 ($1) exited — see $LOGS/server-$2-$1.log" >&2; return 1; }
               port_busy && return 0
               sleep 0.1; k=$((k + 1)); done; return 1; }
stop()   { if [ -n "$SRV" ]; then kill "$SRV" 2>/dev/null; wait "$SRV" 2>/dev/null; SRV=""; sleep 0.3; fi; }
trap 'stop; clean' EXIT

record() {   # name rc
    if [ "$2" -eq 0 ]; then echo "PASS  $1"; pass=$((pass + 1))
    else echo "FAIL  $1  (exit $2 — $LOGS/$1.log)"; fail=$((fail + 1)); failed="$failed $1"; fi
}

run_one() {  # name model cmd...
    local name="$1" model="$2"; shift 2
    if [ "$model" = "-" ]; then
        timeout 600 "$@" >"$LOGS/$name.log" 2>&1
    else
        AGORA_SERVE="$model" timeout 600 "$@" >"$LOGS/$name.log" 2>&1
    fi
    record "$name" $?
}

want() {
    case "$SKIP" in *",$1,"*) return 1 ;; esac
    [ -z "$ONLY" ] && return 0
    case " $ONLY " in *" $1 "*) return 0 ;; esac
    return 1
}

echo "agora example smokes — models: $MODELS$([ $FAST -eq 1 ] && echo ', fast')"
while read -r nn kind needs; do
    [ -z "$nn" ] && continue
    want "$nn" || continue
    script="$(ls $EX/$nn-* 2>/dev/null | head -1)"
    [ -n "$script" ] || { echo "SKIP  $nn  (no script)"; skipped=$((skipped + 1)); continue; }
    case "$script" in *.py) cmd=(python3 "$script") ;; *) cmd=(bash "$script") ;; esac
    args=()
    [ "$nn" = 04 ] && args=("$PORT" 8)
    case "$nn" in 05|23|25|27) args=("$PORT") ;; esac
    [ "$nn" = 26 ] && { args=("$PORT"); [ $FAST -eq 1 ] && args+=(--fast); }
    [ "$nn" = 31 ] && [ $FAST -eq 1 ] && args+=(--fast)
    if [ "$needs" = mud ] && [ ! -d ../cyrius-yeomans-descent ]; then
        echo "SKIP  $nn  (needs ../cyrius-yeomans-descent)"; skipped=$((skipped + 1)); continue
    fi
    case "$kind" in
        cli|own)
            port_free
            if [ "$needs" = reg ]; then reg; else clean; fi
            run_one "$nn" - "${cmd[@]}" "${args[@]}" ;;
        self)
            for m in $MODELS; do
                port_free
                if [ "$needs" = reg ]; then reg; else clean; fi
                run_one "$nn-$m" "$m" "${cmd[@]}" "${args[@]}"
            done ;;
        client)
            for m in $MODELS; do
                if [ "$needs" = reg ]; then reg; else clean; fi
                if serve "$m" "$nn"; then
                    run_one "$nn-$m" "$m" "${cmd[@]}" "${args[@]}"
                else
                    record "$nn-$m" 99
                fi
                stop
            done ;;
    esac
done <<< "$TABLE"

echo "== $pass passed, $fail failed, $skipped skipped${failed:+ —$failed}"
[ "$fail" -eq 0 ]
