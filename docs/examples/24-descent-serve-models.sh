#!/usr/bin/env bash
# 24-descent-serve-models.sh — the Descent byte-proxy forwards under BOTH serve models (1.6.2).
#
# Why: 20-descent.sh proves the gateway against the real Yeoman's Descent MUD,
# but only in whatever serve model happens to be the default. 1.6.0 added the
# poll multiplex, and with it a silent regression: in poll mode `send_buf`
# ignores its fd argument and enqueues to the ACTIVE SESSION's tx queue
# (src/main.cyr:239), which is correct for BBS output and wrong for a proxy.
# So `send_buf(mfd, ...)` — the client→MUD direction — put the player's
# keystrokes on the player's own outbound queue and the MUD received NOTHING.
# The gateway looked alive (the MUD's banner still reached the client) but no
# input ever arrived. 1.6.2 gives descent_proxy its own direct full-write
# (descent_write_all) for both directions.
#
# This script pins that with a FAKE MUD rather than the real one — a stub that
# logs every byte it receives — so the assertion is exact ("the MUD saw these
# bytes") and the test needs no sibling repo. It runs the whole flow twice,
# once per AGORA_SERVE model.
#
# Requires: python3, openssl >= 3.0 (Ed25519 rawin signer), and a registered
# qix identity — run 02-register-and-post.sh first.
#
# Success: "FORWARDED-OK" for both fork and poll; exit 0.
# Failure (pre-1.6.2, poll): "BROKEN (poll): client->MUD bytes NEVER reached
# the MUD" and exit 1.
set -uo pipefail

cd "$(dirname "$0")/../.."

PORT_BASE="${1:-2394}"
MUD_BASE="${2:-4094}"
STORE=./bbs
KEY=./keys/qix
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

[ -x ./build/agora ] || { echo "build first: cyrius build src/main.cyr build/agora"; exit 1; }
[ -f "$KEY" ] || { echo "run 02-register-and-post.sh first (need a registered qix)"; exit 1; }

# PKCS#8 Ed25519 envelope around the raw 32-byte seed (RFC 8410 § 7), as in 05.
DER="$TMP/qix.der"
( printf '\x30\x2e\x02\x01\x00\x30\x05\x06\x03\x2b\x65\x70\x04\x22\x04\x20'; cat "$KEY" ) > "$DER"

run_model() {
    local MODE="$1" PORT="$2" MUDPORT="$3"
    local MUDLOG="$TMP/mud-$MODE.log"
    : > "$MUDLOG"

    # Fake MUD: greet like a MUD, then record everything the proxy forwards.
    python3 - "$MUDPORT" "$MUDLOG" <<'PY' &
import socket, sys
port, logpath = int(sys.argv[1]), sys.argv[2]
srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(("127.0.0.1", port)); srv.listen(4)
log = open(logpath, "ab", buffering=0)
while True:
    c, _ = srv.accept()
    c.sendall(b"MUD-BANNER: By what name are you known?\r\n")
    c.settimeout(12)
    try:
        while True:
            d = c.recv(4096)
            if not d:
                break
            log.write(b"MUD-RECEIVED:" + d + b"\n")
    except Exception:
        pass
    c.close()
PY
    local MUDPID=$!

    mkdir -p "$STORE"
    printf '%s' "$MUDPORT" > "$STORE/.descent"
    AGORA_SERVE="$MODE" ./build/agora serve "$PORT" --store "$STORE" > "$TMP/agora-$MODE.log" 2>&1 &
    local SRV=$!

    local i
    for i in $(seq 1 40); do
        if (exec 9<>/dev/tcp/127.0.0.1/"$PORT") 2>/dev/null; then break; fi
        sleep 0.25
    done

    # Authenticated session (descent is login-gated), then enter the Descent
    # and type a marker the fake MUD can assert on.
    exec 3<>/dev/tcp/127.0.0.1/"$PORT"
    sleep 0.5
    timeout 1 cat <&3 >/dev/null 2>&1
    printf 'login qix\r\n' >&3
    local CHAL="" line
    for i in $(seq 1 20); do
        IFS= read -r -t 1 line <&3 || true
        case "$line" in *challenge:*) CHAL=$(echo "$line" | sed 's/.*challenge: *//' | tr -d '\r'); break;; esac
    done
    if [ -z "$CHAL" ]; then
        echo "  ERROR ($MODE): server never issued a challenge"
        exec 3<&-; kill "$SRV" "$MUDPID" 2>/dev/null; return 1
    fi
    printf 'agora-login:%s' "$CHAL" > "$TMP/msg"
    openssl pkeyutl -sign -rawin -inkey "$DER" -keyform DER -in "$TMP/msg" -out "$TMP/sig" 2>/dev/null
    printf 'auth: %s\r\n' "$(xxd -p -c 256 "$TMP/sig")" >&3
    sleep 0.5
    timeout 1 cat <&3 >/dev/null 2>&1

    printf 'descent\r\n' >&3
    sleep 1.2
    printf 'PING-FROM-CLIENT\r\n' >&3
    sleep 1.5
    exec 3<&-

    sleep 0.5
    kill "$SRV" "$MUDPID" 2>/dev/null
    wait "$SRV" "$MUDPID" 2>/dev/null

    if grep -q "PING-FROM-CLIENT" "$MUDLOG" 2>/dev/null; then
        echo "  FORWARDED-OK ($MODE): the MUD received the client's bytes"
        return 0
    fi
    echo "  BROKEN ($MODE): client->MUD bytes NEVER reached the MUD"
    echo "  (fake MUD log: $(wc -c < "$MUDLOG") bytes)"
    return 1
}

echo "=== Descent proxy, AGORA_SERVE=fork ==="
run_model fork "$PORT_BASE" "$MUD_BASE" || exit 1
echo "=== Descent proxy, AGORA_SERVE=poll ==="
run_model poll "$((PORT_BASE + 1))" "$((MUD_BASE + 1))" || exit 1

echo
echo "OK — the Descent byte-proxy forwards client->MUD under both serve models"
