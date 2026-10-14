#!/usr/bin/env bash
# scripts/check-version-sync.sh — is every place that names agora's version in
# agreement with VERSION? Run by CI on every push and by the release workflow
# (with --tag) before anything is built or published; run it by hand as the
# Closeout Pass "version verify" step.
#
# Why (1.8.2): VERSION is the single source of truth, but three things repeatedly
# fell out of step with it — 1.6.6 and 1.7.1 both shipped without state.md or
# roadmap.md being refreshed, because the "release post-hook" CLAUDE.md once
# promised never existed — and until 1.8.2 the binary's version strings were
# three hand-edited literals CI only partly checked. They now come from
# CYRIUS_PKG_VERSION (cyrius.cyml `version = "${file:VERSION}"`), so this script
# also refuses a hard-coded version literal creeping back into src/.
#
# Usage: scripts/check-version-sync.sh [--tag <git-tag>] [--bin <path>]
#   --tag  also require the tag to equal VERSION (the release gate)
#   --bin  the built binary to ask (default build/agora; skipped if absent)
# Exit 0 when everything agrees; 1 with one line per disagreement otherwise.

set -u
cd "$(dirname "$0")/.." || exit 2

TAG=""
BIN="build/agora"
while [ $# -gt 0 ]; do
    case "$1" in
        --tag) TAG="${2:-}"; shift 2 ;;
        --bin) BIN="${2:-}"; shift 2 ;;
        *) echo "usage: $0 [--tag <tag>] [--bin <path>]" >&2; exit 2 ;;
    esac
done

fail=0
bad() { echo "version-sync: $*" >&2; fail=1; }

V="$(tr -d '[:space:]' < VERSION)"
echo "$V" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' || bad "VERSION is not semver: '$V'"

grep -Eq '^version *= *"\$\{file:VERSION\}"' cyrius.cyml \
    || bad "cyrius.cyml [package] version must be \"\${file:VERSION}\" (the binary's strings come from it)"

if [ -n "$TAG" ] && [ "$TAG" != "$V" ]; then
    bad "tag '$TAG' != VERSION '$V'"
fi

if [ -x "$BIN" ]; then
    got="$("$BIN" --version 2>/dev/null | head -1)"
    [ "$got" = "agora $V" ] || bad "$BIN --version says '$got', VERSION says 'agora $V'"
fi

# A literal like "v1.2.3" or "agora 1.2.3" in source is a regression to the
# hand-bumped strings 1.8.2 retired.
lit="$(grep -nE '"(v|agora )[0-9]+\.[0-9]+\.[0-9]+' src/*.cyr 2>/dev/null || true)"
[ -z "$lit" ] || bad "hard-coded version literal in src/ (use CYRIUS_PKG_VERSION):"$'\n'"$lit"

grep -Fq "## [$V]" CHANGELOG.md || bad "CHANGELOG.md has no '## [$V]' entry"

grep -Fq "| **Released** | \`$V\`" docs/development/state.md \
    || bad "docs/development/state.md: the Released row does not name \`$V\` (refreshed by hand every release)"

# 1.12.1 — the roadmap is forward-only (shipped work leaves it for the
# CHANGELOG), so it no longer carries a row for the released version. What a
# release must still do to it: name a next slot AFTER VERSION in its header, and
# delete the section that planned VERSION.
RM=docs/development/roadmap.md
next="$(grep -oE 'Next slot: \*\*[0-9]+\.[0-9]+\.[0-9]+\*\*' "$RM" | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')"
if [ -z "$next" ]; then
    bad "$RM: its header names no 'Next slot: **X.Y.Z**' (refreshed by hand every release)"
elif [ "$next" = "$V" ] || [ "$(printf '%s\n%s\n' "$V" "$next" | sort -V | tail -1)" != "$next" ]; then
    bad "$RM: the next slot ($next) is not after VERSION ($V) — refresh the roadmap for the release"
fi
grep -Eq "^### $V( |\$)" "$RM" && bad "$RM: still plans $V (### $V) — a shipped slot's section is deleted"

if [ "$fail" -eq 0 ]; then
    echo "version-sync: OK — $V agrees across VERSION, cyrius.cyml, the binary, CHANGELOG and state.md; roadmap.md plans $next next${TAG:+; tag $TAG}"
fi
exit "$fail"
