#!/usr/bin/env bash
# 12-eliza.sh
#
# Why: 1.3.0 ships ELIZA (Weizenbaum 1966 DOCTOR, ADR 0011) two ways —
# a `play eliza` DOOR (no login; practice-only conversation) and a
# private `/eliza` side-channel inside chat (login-gated; replies go
# only to the asker, never to the room). The decomposition/reassembly
# engine is unit-tested (t149-t154); this drives both wire surfaces.
#
# Requires: openssl >= 3.0, xxd (only for the side-channel half).
#
# Success: the door greets + decomposes "I am sad" -> "How long have you
# been sad?", AND the /eliza side-channel answers privately. Exit 0.

set -euo pipefail
cd "$(dirname "$0")/../.."

STORE=./bbs
HOST=127.0.0.1
PORT=${1:-2325}

[ -x ./build/agora ] || cyrius build src/main.cyr build/agora
mkdir -p ./keys
[ -f ./keys/qix ] || ./build/agora keygen --key ./keys/qix >/dev/null
./build/agora register --handle qix --key ./keys/qix --store "$STORE" >/dev/null 2>&1 || true
rm -rf "$STORE/.chat/lobby"

./build/agora serve "$PORT" --store "$STORE" >/tmp/agora-eliza-smoke.log 2>&1 &
SERVER=$!
trap 'kill "$SERVER" 2>/dev/null || true' EXIT
sleep 0.5

rc=0

# ---------- Part 1: the `play eliza` door (no login) ----------
exec 3<>/dev/tcp/"$HOST"/"$PORT"
while IFS= read -r -t 0.4 -u 3 _; do :; done          # drain banner + IAC
printf 'play eliza\r\n' >&3
sleep 0.3
greet=""
while IFS= read -r -t 0.5 -u 3 line; do greet+="$(printf '%s' "$line" | tr -d '\r')"$'\n'; done
echo "=== eliza door greeting ==="; printf '%s' "$greet"

printf 'I am sad\r\n' >&3
sleep 0.3
reply=""
while IFS= read -r -t 0.5 -u 3 line; do reply+="$(printf '%s' "$line" | tr -d '\r')"$'\n'; done
echo "=== eliza reply to 'I am sad' ==="; printf '%s' "$reply"

printf 'bye\r\n' >&3
exec 3<&-
case "$reply" in *"How long have you been sad?"*) echo "OK — door decomposed 'I am sad'";; *) echo "FAIL — door reply wrong" >&2; rc=1;; esac

# ---------- Part 2: the private /eliza side-channel (login + chat) ----------
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
printf 'chat lobby\r\n' >&4
sleep 0.3
while IFS= read -r -t 0.5 -u 4 _; do :; done
printf '/eliza\r\n' >&4
sleep 0.3
while IFS= read -r -t 0.5 -u 4 _; do :; done          # drain greeting
printf 'you are just a machine\r\n' >&4
sleep 0.4
priv=""
while IFS= read -r -t 0.5 -u 4 line; do priv+="$(printf '%s' "$line" | tr -d '\r')"$'\n'; done
echo "=== private /eliza reply ==="; printf '%s' "$priv"
printf '/quit\r\n' >&4
exec 4<&-

# The room transcript must NOT contain the private line.
roomlog=""
[ -f "$STORE/.chat/lobby/log" ] && roomlog=$(cat "$STORE/.chat/lobby/log")
case "$priv" in *"ELIZA:"*) echo "OK — /eliza answered privately";; *) echo "FAIL — no private ELIZA reply" >&2; rc=1;; esac
case "$roomlog" in *"just a machine"*) echo "FAIL — private line leaked into the room transcript!" >&2; rc=1;; *) echo "OK — private line stayed off the room transcript";; esac

exit "$rc"
