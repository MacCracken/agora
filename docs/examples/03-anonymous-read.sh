#!/usr/bin/env bash
# 03-anonymous-read.sh
#
# Why: M6 default policy is "anon-read, auth-post" (ADR 0006). This
# script proves both halves: an unauthenticated client can list + read
# the post written by example 02, but cannot post a new message — the
# CLI returns a clear "auth required" error and exit 1.
#
# Run example 02 first to populate ./bbs/main/1.txt.
#
# Success: list shows ID 1; read 1 prints the From + body; anonymous
# post is rejected with exit 1 and a recognizable error string.

set -euo pipefail

cd "$(dirname "$0")/../.."

STORE=./bbs

if [ ! -f "$STORE/1.txt" ]; then
    echo "error: $STORE/1.txt missing — run 02-register-and-post.sh first" >&2
    exit 1
fi

echo "=== anonymous list ==="
./build/agora list --store "$STORE"

echo
echo "=== anonymous read 1 ==="
./build/agora read 1 --store "$STORE"

echo
echo "=== anonymous post (expected to fail) ==="
set +e
echo "should be denied" | ./build/agora post \
    --store "$STORE" --subject "anon attempt" 2>&1
rc=$?
set -e

if [ "$rc" -ne 1 ]; then
    echo "FAIL — expected exit 1 for anonymous post, got $rc" >&2
    exit 1
fi

echo
echo "OK — reads work without auth; posts correctly denied (exit $rc)"
