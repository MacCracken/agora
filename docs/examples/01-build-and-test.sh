#!/usr/bin/env bash
# 01-build-and-test.sh
#
# Why: prove the toolchain is wired and the conformance suite green
# before any of the later examples touch the binary. If this script
# fails, nothing downstream will work — fix the build before reading on.
#
# Success: build/agora exists; `agora version` matches VERSION; 80/80
# tests pass; exit 0.

set -euo pipefail

cd "$(dirname "$0")/../.."

echo "=== build ==="
cyrius build src/main.cyr build/agora

echo
echo "=== version sanity ==="
expected=$(cat VERSION)
got=$(./build/agora version | awk '{print $2}')
if [ "$expected" != "$got" ]; then
    echo "VERSION mismatch: file says $expected, binary says $got" >&2
    exit 1
fi
echo "agora $got — matches VERSION"

echo
echo "=== test suite ==="
cyrius test src/test.cyr

echo
echo "OK — build + tests green at $got"
