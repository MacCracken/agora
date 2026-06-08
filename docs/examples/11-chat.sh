#!/usr/bin/env bash
# 11-chat.sh
#
# Why: the 1.3.0 chat area (ADR 0011) is the synchronous public-assembly
# surface — a live multi-user teleconference. The pure transcript logic
# is unit-tested (t142-t148); the *interleaving* (two logged-in sessions
# seeing each other's lines on disk under flock) needs a wire smoke, the
# way ADR 0010's world concurrency is smoke-tested rather than unit-
# tested. This drives two telnet sessions through the real flow:
#
#   1. qix logs in (Ed25519 challenge/response), joins #lobby, says a line
#   2. pac logs in, joins #lobby → sees qix's line in SCROLLBACK
#      (cross-session delivery via the flock'd transcript)
#   3. pac says a line; qix's session (kept open) picks it up on its next
#      live-tail POLL TICK (the CHAT_POLL_SECS recv-timeout flush)
#
# Requires: openssl >= 3.0 (rawin Ed25519 signer), xxd.
#
# Success: pac's scrollback contains qix's line AND qix's live tail
# contains pac's line. Exit 0.

set -euo pipefail
cd "$(dirname "$0")/../.."

STORE=./bbs
HOST=127.0.0.1
PORT=${1:-2324}

[ -x ./build/agora ] || cyrius build src/main.cyr build/agora

mkdir -p ./keys
# Register two identities (idempotent — ignore "already registered").
for h in qix pac; do
    [ -f "./keys/$h" ] || ./build/agora keygen --key "./keys/$h" >/dev/null
    ./build/agora register --handle "$h" --key "./keys/$h" --store "$STORE" >/dev/null 2>&1 || true
done

# Fresh lobby each run so scrollback assertions are deterministic.
rm -rf "$STORE/.chat/lobby"

./build/agora serve "$PORT" --store "$STORE" >/tmp/agora-chat-smoke.log 2>&1 &
SERVER=$!
trap 'kill "$SERVER" 2>/dev/null || true' EXIT
sleep 0.5

# Wrap a raw 32-byte seed into a PKCS#8 Ed25519 DER blob (RFC 8410 §7).
der_for() {
    local key="$1" out="$2"
    ( printf '\x30\x2e\x02\x01\x00\x30\x05\x06\x03\x2b\x65\x70\x04\x22\x04\x20'; cat "$key" ) > "$out"
}

# Drive the challenge/response login on an already-open fd.
#   login_on <fd> <handle> <key>
login_on() {
    local fd="$1" handle="$2" key="$3"
    local der msg sig nonce sighex
    der=$(mktemp --suffix=.der); msg=$(mktemp); sig=$(mktemp)
    der_for "$key" "$der"
    # drain banner + IAC
    while IFS= read -r -t 0.3 -u "$fd" _; do :; done
    printf 'login %s\r\n' "$handle" >&"$fd"
    nonce=""
    while IFS= read -r -t 2 -u "$fd" line; do
        line=$(printf '%s' "$line" | tr -d '\r')
        case "$line" in challenge:*) nonce=$(printf '%s' "$line" | awk '{print $2}'); break;; esac
    done
    [ -n "$nonce" ] || { echo "FAIL: no challenge for $handle" >&2; exit 1; }
    printf 'agora-login:%s' "$nonce" > "$msg"
    openssl pkeyutl -sign -rawin -keyform DER -inkey "$der" -in "$msg" -out "$sig"
    sighex=$(xxd -p -c 256 "$sig")
    printf 'auth: %s\r\n' "$sighex" >&"$fd"
    while IFS= read -r -t 1 -u "$fd" _; do :; done   # drain "welcome, <h>"
    rm -f "$der" "$msg" "$sig"
}

# --- Session A: qix ---
exec 3<>/dev/tcp/"$HOST"/"$PORT"
login_on 3 qix ./keys/qix
printf 'chat lobby\r\n' >&3
sleep 0.3
while IFS= read -r -t 0.5 -u 3 _; do :; done          # drain join banner
printf 'hello-from-qix\r\n' >&3
sleep 0.5
while IFS= read -r -t 0.5 -u 3 _; do :; done          # drain own echo

# --- Session B: pac --- (joins after qix said its line)
exec 4<>/dev/tcp/"$HOST"/"$PORT"
login_on 4 pac ./keys/pac
printf 'chat lobby\r\n' >&4
sleep 0.5
pac_scrollback=""
while IFS= read -r -t 0.6 -u 4 line; do
    pac_scrollback+="$(printf '%s' "$line" | tr -d '\r')"$'\n'
done
echo "=== pac scrollback on join ==="
printf '%s' "$pac_scrollback"

# pac says a line; qix should see it via its live-tail poll tick.
printf 'ping-from-pac\r\n' >&4
sleep 0.5

# qix has been idle — its 2s poll tick flushes pac's line. Give it >1 tick.
sleep 3
qix_tail=""
while IFS= read -r -t 0.6 -u 3 line; do
    qix_tail+="$(printf '%s' "$line" | tr -d '\r')"$'\n'
done
echo "=== qix live tail (should contain pac's line) ==="
printf '%s' "$qix_tail"

printf '/quit\r\n' >&3 || true
printf '/quit\r\n' >&4 || true
exec 3<&- 4<&-

rc=0
case "$pac_scrollback" in *"<qix> hello-from-qix"*) echo "OK — pac saw qix's line in scrollback";; *) echo "FAIL — pac scrollback missing qix's line" >&2; rc=1;; esac
case "$qix_tail" in *"<pac> ping-from-pac"*) echo "OK — qix saw pac's line via live tail";; *) echo "FAIL — qix live tail missing pac's line" >&2; rc=1;; esac

exit "$rc"
