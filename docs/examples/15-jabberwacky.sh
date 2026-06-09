#!/usr/bin/env bash
# 15-jabberwacky.sh
#
# Why: 1.3.3 ships Jabberwacky (Carpenter 1988→, ADR 0015) — agora's
# FIRST corpus-learning bot. Unlike the stateless ELIZA/PARRY, it learns
# (prev line -> this line) and replays it, and (logged in) PERSISTS what
# it learned per-user. Three surfaces: a `play jabberwacky` DOOR
# (practice; learns in-session, ephemeral), a private `/jabberwacky`
# chat side-channel (ephemeral, seed-only), and `play jabberwacky solo`
# (login-gated; the learned layer is saved under .users/<fp16>/games/).
# The retrieval/learn/save engine is unit-tested (t167-t175); this drives
# all three wire surfaces and proves cross-session learning end to end.
#
# Requires: openssl >= 3.0, xxd (for the login-gated halves).
#
# Success: (1) the door replays a pair taught mid-session; (2) the
# /jabberwacky couch answers privately and the line never hits the room
# transcript; (3) a pair taught in one solo session survives a
# disconnect and replays in the next. Exit 0.

set -euo pipefail
cd "$(dirname "$0")/../.."

STORE=./bbs
HOST=127.0.0.1
PORT=${1:-2328}

[ -x ./build/agora ] || cyrius build src/main.cyr build/agora
mkdir -p ./keys
[ -f ./keys/qix ] || ./build/agora keygen --key ./keys/qix >/dev/null
./build/agora register --handle qix --key ./keys/qix --store "$STORE" >/dev/null 2>&1 || true
rm -rf "$STORE/.chat/lobby"
rm -f "$STORE/.users"/*/games/jabberwacky.sav 2>/dev/null || true

./build/agora serve "$PORT" --store "$STORE" >/tmp/agora-jabberwacky-smoke.log 2>&1 &
SERVER=$!
trap 'kill "$SERVER" 2>/dev/null || true' EXIT
sleep 0.5

rc=0

drain() { while IFS= read -r -t "${1:-0.5}" -u "$2" _; do :; done; }
say() { printf '%s\r\n' "$2" >&"$1"; sleep 0.3; }
grab() { local out="" line; while IFS= read -r -t 0.5 -u "$1" line; do out+="$(printf '%s' "$line" | tr -d '\r')"$'\n'; done; printf '%s' "$out"; }

# ---------- Part 1: `play jabberwacky` door — teach, then replay ----------
exec 3<>/dev/tcp/"$HOST"/"$PORT"
drain 0.4 3                                  # banner + IAC
say 3 'play jabberwacky'; drain 0.4 3        # greeting
say 3 'what is the password'; drain 0.4 3    # turn 0
say 3 'the password is rosebud'; drain 0.4 3 # turn 1: teaches (prev -> this)
say 3 'what is the password'                 # turn 2: should replay
replay="$(grab 3)"
echo "=== door replay of taught pair ==="; printf '%s' "$replay"
printf 'bye\r\n' >&3
exec 3<&-
case "$replay" in *"rosebud"*) echo "OK — door learned and replayed the pair";; *) echo "FAIL — door did not replay the taught response" >&2; rc=1;; esac

# ---------- Part 2: the private /jabberwacky side-channel (login + chat) ----------
der_for() { ( printf '\x30\x2e\x02\x01\x00\x30\x05\x06\x03\x2b\x65\x70\x04\x22\x04\x20'; cat "$1" ) > "$2"; }
login_on() {
    local fd="$1" handle="$2" key="$3" der msg sig nonce sighex
    der=$(mktemp --suffix=.der); msg=$(mktemp); sig=$(mktemp); der_for "$key" "$der"
    while IFS= read -r -t 0.3 -u "$fd" _; do :; done
    printf 'login %s\r\n' "$handle" >&"$fd"
    nonce=""
    while IFS= read -r -t 2 -u "$fd" line; do
        line=$(printf '%s' "$line" | tr -d '\r')
        case "$line" in challenge:*) nonce=$(printf '%s' "$line" | awk '{print $2}'); break;; esac
    done
    [ -n "$nonce" ] || { echo "FAIL: no challenge" >&2; exit 1; }
    printf 'agora-login:%s' "$nonce" > "$msg"
    openssl pkeyutl -sign -rawin -keyform DER -inkey "$der" -in "$msg" -out "$sig"
    sighex=$(xxd -p -c 256 "$sig")
    printf 'auth: %s\r\n' "$sighex" >&"$fd"
    while IFS= read -r -t 1 -u "$fd" _; do :; done
    rm -f "$der" "$msg" "$sig"
}

exec 4<>/dev/tcp/"$HOST"/"$PORT"
login_on 4 qix ./keys/qix
say 4 'chat lobby'; drain 0.5 4
say 4 '/jabberwacky'; drain 0.5 4             # private greeting
say 4 'the moon is made of cheese'            # private line
priv="$(grab 4)"
echo "=== private /jabberwacky reply ==="; printf '%s' "$priv"
printf '/quit\r\n' >&4
exec 4<&-

roomlog=""
[ -f "$STORE/.chat/lobby/log" ] && roomlog=$(cat "$STORE/.chat/lobby/log")
case "$priv" in *"JABBERWACKY:"*) echo "OK — /jabberwacky answered privately";; *) echo "FAIL — no private JABBERWACKY reply" >&2; rc=1;; esac
case "$roomlog" in *"moon is made of cheese"*) echo "FAIL — private line leaked into the room transcript!" >&2; rc=1;; *) echo "OK — private line stayed off the room transcript";; esac

# ---------- Part 3: cross-session learning via `play jabberwacky solo` ----------
# Session A: teach a pair, then leave cleanly (which saves the learned layer).
exec 5<>/dev/tcp/"$HOST"/"$PORT"
login_on 5 qix ./keys/qix
say 5 'play jabberwacky solo'; drain 0.5 5
say 5 'what is my favourite colour'; drain 0.4 5   # turn 0
say 5 'my favourite colour is teal'; drain 0.4 5   # turn 1: teaches the pair
printf 'bye\r\n' >&5                                # exit -> persists the learned layer
sleep 0.3
exec 5<&-

# Session B: reconnect fresh; the taught pair must have survived to disk.
exec 6<>/dev/tcp/"$HOST"/"$PORT"
login_on 6 qix ./keys/qix
say 6 'play jabberwacky solo'; drain 0.5 6
say 6 'what is my favourite colour'                # should replay across sessions
persist="$(grab 6)"
echo "=== next-session replay (cross-session learning) ==="; printf '%s' "$persist"
printf 'bye\r\n' >&6
exec 6<&-
case "$persist" in *"teal"*) echo "OK — learned pair survived the disconnect (per-user persistence)";; *) echo "FAIL — cross-session learning did not persist" >&2; rc=1;; esac

exit "$rc"
