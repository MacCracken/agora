#!/usr/bin/env bash
# scripts/check-toolchain.sh — is the local cyrius toolchain the one the pin
# names? A pre-cut gate (CLAUDE.md § Closeout Pass); run it before trusting any
# binary size or benchmark number.
#
# Why (1.8.2): two independent defects found at 1.6.7 made a local toolchain's
# provenance unverifiable, and both fail silently:
#   - `install.sh --refresh-only` fills ~/.cyrius/versions/<ver>/ from whatever
#     the cyrius WORKING TREE holds — the 6.5.33 snapshot here carried an
#     unreleased bayan.cyr / patra.cyr / cycc and inflated the measured binary by
#     215,520 B;
#   - the versioned wrapper did not pin `cycc` and could run whatever was on PATH
#     (upstream: cyrius/docs/development/issues/2026-08-22-versioned-wrapper-does-not-pin-cycc.md).
# Until now the check was a manual `git show <tag>:lib/<m> | cmp -` sweep.
#
# Checks, for the pin in cyrius.cyml:
#   1. the snapshot ~/.cyrius/versions/<pin>/ exists, and its SOURCE_COMMIT names
#      the tag's commit and says the tree matched it;
#   2. every snapshot lib/*.cyr is byte-identical to `git show <pin>:lib/<file>`
#      in a cyrius checkout (needs one: $CYRIUS_REPO, default ../cyrius);
#   3. every vendored lib/*.cyr in this repo that came from the stdlib is
#      byte-identical to the snapshot's (a stale `cyrius deps` / `lib sync`;
#      architecture note 002);
#   4. `cyrius build -v` resolves the compiler inside the snapshot.
# Usage: scripts/check-toolchain.sh [--no-repo]   (--no-repo: skip 1's commit match and 2)
# Exit 0 = verified; 1 = a mismatch; 2 = could not verify.

set -u
cd "$(dirname "$0")/.." || exit 2
NOREPO=0
[ "${1:-}" = "--no-repo" ] && NOREPO=1

PIN="$(grep -E '^cyrius *= *"' cyrius.cyml | head -1 | sed 's/.*"\(.*\)"/\1/')"
SNAP="$HOME/.cyrius/versions/$PIN"
REPO="${CYRIUS_REPO:-$(cd .. && pwd)/cyrius}"
fail=0
bad() { echo "toolchain: $*" >&2; fail=1; }

[ -n "$PIN" ] || { echo "toolchain: no cyrius pin in cyrius.cyml" >&2; exit 2; }
[ -d "$SNAP/lib" ] || { echo "toolchain: no snapshot at $SNAP (install cyrius $PIN)" >&2; exit 2; }
echo "toolchain: pin $PIN, snapshot $SNAP"

# 1 + 2 — the snapshot against the tag
if [ "$NOREPO" -eq 0 ]; then
    if ! git -C "$REPO" rev-parse --verify -q "$PIN^{commit}" >/dev/null 2>&1; then
        echo "toolchain: no cyrius checkout with tag $PIN at $REPO (set CYRIUS_REPO, or --no-repo)" >&2
        exit 2
    fi
    want="$(git -C "$REPO" rev-parse "$PIN^{commit}")"
    have="$(head -1 "$SNAP/SOURCE_COMMIT" 2>/dev/null)"
    [ "$have" = "$want" ] || bad "SOURCE_COMMIT is '$have', tag $PIN is $want"
    grep -q 'tree-matches-tag: yes' "$SNAP/SOURCE_COMMIT" 2>/dev/null \
        || bad "SOURCE_COMMIT does not attest 'tree-matches-tag: yes' (built from a dirty tree?)"
    n=0
    for f in "$SNAP"/lib/*.cyr; do
        b="$(basename "$f")"
        if ! git -C "$REPO" cat-file -e "$PIN:lib/$b" 2>/dev/null; then
            bad "snapshot lib/$b is not in tag $PIN"
        elif ! git -C "$REPO" show "$PIN:lib/$b" | cmp -s - "$f"; then
            bad "snapshot lib/$b differs from tag $PIN"
        fi
        n=$((n + 1))
    done
    echo "toolchain: $n snapshot stdlib files compared against tag $PIN"
fi

# 3 — vendored lib/ against the snapshot
v=0; other=""
for f in lib/*.cyr; do
    [ -e "$f" ] || { echo "toolchain: no vendored lib/ (run cyrius deps)" >&2; exit 2; }
    b="$(basename "$f")"
    if [ -e "$SNAP/lib/$b" ]; then
        cmp -s "$f" "$SNAP/lib/$b" || bad "vendored lib/$b differs from the snapshot (stale cyrius deps?)"
        v=$((v + 1))
    else
        other="$other $b"
    fi
done
echo "toolchain: $v vendored stdlib files compared against the snapshot${other:+ (not from the stdlib:$other)}"

# 4 — the compiler the build actually runs
tmpo="$(mktemp)"
comp="$(cyrius build -v src/main.cyr "$tmpo" 2>&1 | grep -o 'compiler: [^ ]*' | head -1 | cut -d' ' -f2)"
rm -f "$tmpo"
case "$comp" in
    "$SNAP"/bin/cycc*) echo "toolchain: compiler $comp" ;;
    "") bad "could not read the compiler from 'cyrius build -v'" ;;
    *) bad "the build runs $comp, not the pinned snapshot's cycc" ;;
esac

[ "$fail" -eq 0 ] && echo "toolchain: OK — cyrius $PIN verified"
exit "$fail"
