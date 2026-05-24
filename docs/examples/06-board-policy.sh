#!/usr/bin/env bash
# 06-board-policy.sh
#
# Why: M6-F per-board policy (.policy + .admins) is operator-facing
# config that has to be edited as files today. This example walks
# through all three modes (open / known / admin) and confirms each
# denial path triggers the expected error message.
#
# Success: every assert line prints OK; exit 0.

set -euo pipefail

cd "$(dirname "$0")/../.."

STORE=./bbs
KEY_QIX=./keys/qix
KEY_PAC=./keys/pac

if [ ! -f "$KEY_QIX" ]; then
    echo "error: $KEY_QIX not found — run 03-authenticated-post.sh first" >&2
    exit 1
fi

# Make sure pac is also registered.
if [ ! -f "$KEY_PAC" ]; then
    ./build/agora keygen --key "$KEY_PAC"
    ./build/agora register --handle pac --key "$KEY_PAC" --store "$STORE"
fi

assert_exit() {
    local want="$1" got="$2" label="$3"
    if [ "$want" = "$got" ]; then
        echo "  OK    $label (exit $got)"
    else
        echo "  FAIL  $label (want exit $want, got $got)" >&2
        exit 1
    fi
}

run_post() {
    set +e
    echo "$1" | ./build/agora post \
        --board "$2" --store "$STORE" \
        ${3:+--as "$3"} ${4:+--key "$4"} \
        --subject "policy test" > /dev/null 2>&1
    rc=$?
    set -e
    echo "$rc"
}

echo "=== open board (default — no .policy file) ==="
# `open` = any authenticated user. Anonymous is denied at M6 across
# every mode (auth-post default); per-board override is a future ADR.
mkdir -p "$STORE/openish"
rc=$(run_post "anon attempt"  openish "" "")
assert_exit 1 "$rc" "anon → open DENIED"
rc=$(run_post "qix ok"   openish qix "$KEY_QIX")
assert_exit 0 "$rc" "qix  → open OK"
rc=$(run_post "pac ok"   openish pac "$KEY_PAC")
assert_exit 0 "$rc" "pac  → open OK"

echo
echo "=== known board ==="
# At M6 `open` and `known` behave identically (every authenticated
# session is locally-registered through .users/). `known` exists to
# carry future semantics (e.g. cross-store federation, web-of-trust).
mkdir -p "$STORE/knownish"
echo known > "$STORE/knownish/.policy"
rc=$(run_post "anon"  knownish "" "")
assert_exit 1 "$rc" "anon → known DENIED"
rc=$(run_post "qix"   knownish qix "$KEY_QIX")
assert_exit 0 "$rc" "qix  → known OK"
rc=$(run_post "pac"   knownish pac "$KEY_PAC")
assert_exit 0 "$rc" "pac  → known OK"

echo
echo "=== admin board ==="
mkdir -p "$STORE/announce"
echo admin > "$STORE/announce/.policy"
echo qix  > "$STORE/announce/.admins"
rc=$(run_post "anon" announce "" "")
assert_exit 1 "$rc" "anon → admin DENIED"
rc=$(run_post "pac"  announce pac "$KEY_PAC")
assert_exit 1 "$rc" "pac  → admin DENIED (registered but not in .admins)"
rc=$(run_post "qix"  announce qix "$KEY_QIX")
assert_exit 0 "$rc" "qix  → admin OK"

echo
echo "OK — all three policy modes behave per ADR 0006 / M6-F"
