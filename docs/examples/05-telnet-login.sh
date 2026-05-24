#!/usr/bin/env bash
# 05-telnet-login.sh
#
# Why: M6 telnet challenge/response is the only auth path that uses
# the wire — CLI --as resolves the binding locally. This script drives
# the wire flow end-to-end:
#
#   1. server: `login qix` → emits `challenge: <nonce_hex>`
#   2. client: signs "agora-login:<nonce_hex>" with the Ed25519 seed
#   3. client: sends `auth: <hex_signature>`
#   4. server: ed25519_verify → bind session → confirm via `whoami`
#
# Requires: openssl ≥ 3.0 (needs the rawin Ed25519 signer); the
# server running with the same --store that holds qix's registration.
#
# Run server first:
#   ./build/agora serve 2323 --store ./bbs
#   (qix must already be registered — run 03-authenticated-post.sh first)
#
# Success: final response from server is "qix <fp16>" — i.e. whoami
# reports the bound identity rather than `anonymous`. Exit 0.

set -euo pipefail

cd "$(dirname "$0")/../.."

STORE=./bbs
KEY=./keys/qix
HOST=127.0.0.1
PORT=${1:-2323}

if [ ! -f "$KEY" ]; then
    echo "error: $KEY not found — run 03-authenticated-post.sh first" >&2
    exit 1
fi

# Wrap the raw 32-byte seed into a PKCS#8 Ed25519 DER blob openssl can
# sign with directly. The 16-byte prefix is the fixed PKCS#8 envelope
# for Ed25519 (OID 1.3.101.112, version 0, nested OCTET STRING). See
# RFC 8410 § 7 for the wire shape.
DER=$(mktemp --suffix=.der)
MSG=$(mktemp)
SIG=$(mktemp)
trap 'rm -f "$DER" "$MSG" "$SIG"' EXIT
(
    printf '\x30\x2e\x02\x01\x00\x30\x05\x06\x03\x2b\x65\x70\x04\x22\x04\x20'
    cat "$KEY"
) > "$DER"

# Coproc-style telnet session driven from bash. We send `login qix`,
# read the challenge line, sign it, and reply with `auth <hex>`, then
# `whoami` to confirm and `quit` to close cleanly.
exec 3<>/dev/tcp/"$HOST"/"$PORT"

# Drain banner + IAC negotiation. We drain-and-print instead of
# discarding so the user sees the full bannermanor MOTD; the first
# line will carry leading IAC byte noise (binary 0xFF sequences from
# the announce_salvo), which is expected — every subsequent line is
# the rendered banner / prompt.
sleep 0.5
while IFS= read -r -t 0.2 -u 3 line; do
    echo "<-- $(printf '%s' "$line" | tr -d '\r')"
done

echo "=== login qix ==="
printf 'login qix\r\n' >&3

# Read until we see "challenge: <hex>".
nonce_hex=""
while IFS= read -r -t 2 -u 3 line; do
    line=$(printf '%s' "$line" | tr -d '\r')
    echo "<-- $line"
    case "$line" in
        challenge:*)
            nonce_hex=$(printf '%s' "$line" | awk '{print $2}')
            break
            ;;
    esac
done

if [ -z "$nonce_hex" ]; then
    echo "error: no challenge received" >&2
    exit 1
fi

echo
echo "=== sign 'agora-login:$nonce_hex' ==="
# Ed25519's `pkeyutl -sign -rawin` needs a file (oneshot operation),
# not stdin — so we write the challenge to disk first.
printf 'agora-login:%s' "$nonce_hex" > "$MSG"
openssl pkeyutl -sign -rawin -keyform DER -inkey "$DER" -in "$MSG" -out "$SIG"
sig_hex=$(xxd -p -c 256 "$SIG")
echo "sig: $sig_hex"

echo
echo "=== auth: $sig_hex ==="
printf 'auth: %s\r\n' "$sig_hex" >&3

# Drain the auth response.
sleep 0.2
while IFS= read -r -t 1 -u 3 line; do
    echo "<-- $(printf '%s' "$line" | tr -d '\r')"
done

echo
echo "=== whoami ==="
printf 'whoami\r\n' >&3
sleep 0.2
identity=""
while IFS= read -r -t 1 -u 3 line; do
    line=$(printf '%s' "$line" | tr -d '\r')
    echo "<-- $line"
    case "$line" in
        qix\ *) identity="$line" ;;
    esac
done

printf 'quit\r\n' >&3
exec 3<&-

if [ -z "$identity" ]; then
    echo "FAIL — whoami did not report qix" >&2
    exit 1
fi

echo
echo "OK — bound to $identity"
