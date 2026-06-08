#!/usr/bin/env bash
# 13-parry.sh
#
# Why: 1.3.1 ships PARRY (Colby 1972, the paranoid foil to ELIZA) the
# same two ways Eliza ships — a `play parry` DOOR (no login) and a
# private `/parry` side-channel inside chat (login-gated; replies go
# only to the asker, never to the room). PARRY's affect engine
# (fear/anger/mistrust → mood-gated responses + the Mafia delusion
# story) is unit-tested (t156-t160); this drives both wire surfaces.
#
# Requires: openssl >= 3.0, xxd (only for the side-channel half).
#
# Success: the door greets, answers a neutral line calmly, then a
# Mafia "flare" launches the delusion story; AND the /parry side-channel
# answers privately, off the room transcript. Exit 0.

set -euo pipefail
cd "$(dirname "$0")/../.."

STORE=./bbs
HOST=127.0.0.1
PORT=${1:-2326}

[ -x ./build/agora ] || cyrius build src/main.cyr build/agora
mkdir -p ./keys
[ -f ./keys/qix ] || ./build/agora keygen --key ./keys/qix >/dev/null
./build/agora register --handle qix --key ./keys/qix --store "$STORE" >/dev/null 2>&1 || true
rm -rf "$STORE/.chat/lobby"

./build/agora serve "$PORT" --store "$STORE" >/tmp/agora-parry-smoke.log 2>&1 &
SERVER=$!
trap 'kill "$SERVER" 2>/dev/null || true' EXIT
sleep 0.5

rc=0

# ---------- Part 1: the `play parry` door (no login) ----------
exec 3<>/dev/tcp/"$HOST"/"$PORT"
while IFS= read -r -t 0.4 -u 3 _; do :; done            # drain banner + IAC
printf 'play parry\r\n' >&3
sleep 0.3
while IFS= read -r -t 0.5 -u 3 _; do :; done            # drain greeting
printf 'hello there\r\n' >&3
sleep 0.3
calm=""
while IFS= read -r -t 0.5 -u 3 line; do calm+="$(printf '%s' "$line" | tr -d '\r')"$'\n'; done
echo "=== parry, calm ==="; printf '%s' "$calm"

printf 'the mafia is after me\r\n' >&3
sleep 0.3
flare=""
while IFS= read -r -t 0.5 -u 3 line; do flare+="$(printf '%s' "$line" | tr -d '\r')"$'\n'; done
echo "=== parry, after a Mafia flare ==="; printf '%s' "$flare"

printf 'bye\r\n' >&3
exec 3<&-
case "$calm"  in *"getting by"*)              echo "OK — door answered the neutral line calmly";; *) echo "FAIL — no calm reply" >&2; rc=1;; esac
case "$flare" in *"betting the horses"*)       echo "OK — Mafia flare launched the delusion story";; *) echo "FAIL — flare did not launch the story" >&2; rc=1;; esac

# ---------- Part 2: the private /parry side-channel (login + chat) ----------
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
printf '/parry\r\n' >&4
sleep 0.3
while IFS= read -r -t 0.5 -u 4 _; do :; done            # drain greeting
printf 'are the cops following you\r\n' >&4
sleep 0.4
priv=""
while IFS= read -r -t 0.5 -u 4 line; do priv+="$(printf '%s' "$line" | tr -d '\r')"$'\n'; done
echo "=== private /parry reply ==="; printf '%s' "$priv"
printf '/quit\r\n' >&4
exec 4<&-

roomlog=""
[ -f "$STORE/.chat/lobby/log" ] && roomlog=$(cat "$STORE/.chat/lobby/log")
case "$priv"    in *"PARRY:"*) echo "OK — /parry answered privately";; *) echo "FAIL — no private PARRY reply" >&2; rc=1;; esac
case "$roomlog" in *"cops following"*) echo "FAIL — private line leaked into the room transcript!" >&2; rc=1;; *) echo "OK — private line stayed off the room transcript";; esac

exit "$rc"
