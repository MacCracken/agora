#!/usr/bin/env bash
# 02-register-and-post.sh
#
# Why: the simplest happy-path post round-trip — generate a key,
# register a handle, post --as that handle, then list + read it back.
# Anonymous CLI posts are denied at M6 (auth-post default), so this
# is the first writeable flow.
#
# Success: ./keys/qix is mode 0600; ./bbs/.users/<fp16>/ exists;
# read 1 prints `From: qix <fp16>` above the body.

set -euo pipefail

cd "$(dirname "$0")/../.."

STORE=./bbs
KEY=./keys/qix
mkdir -p ./keys
rm -rf "$STORE" "$KEY"

echo "=== keygen ==="
./build/agora keygen --key "$KEY"
ls -l "$KEY"

echo
echo "=== register qix ==="
./build/agora register --handle qix --key "$KEY" --store "$STORE"

echo
echo "=== whoami ==="
./build/agora whoami --key "$KEY" --store "$STORE"
fp=$(./build/agora whoami --key "$KEY" --store "$STORE" | awk '{print $2}')

echo
echo "=== post --as qix ==="
echo "this is signed by qix" | ./build/agora post \
    --as qix --key "$KEY" --store "$STORE" --subject "authored post"

echo
echo "=== list ==="
./build/agora list --store "$STORE"

echo
echo "=== read 1 ==="
./build/agora read 1 --store "$STORE"

echo
echo "=== confirm From header on disk ==="
# main board is the flat root per ADR 0004; named boards live in subdirs.
grep '^From:' "$STORE/1.txt"

echo
echo "OK — authored post round-trip works; fp $fp"
