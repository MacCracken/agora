#!/usr/bin/env python3
# scripts/verify-wagers.py — check an agora wager log against its revealed
# seeds, with nothing of agora's own code: Python's hashlib does the hashing.
#
# Why (1.12.1, ADR 0033): every wager and contest draw agora makes comes from a
# server seed the player was shown the SHA-256 of before betting. When the seed
# is revealed (`fair reveal`, a new client seed, or the end of the session) an
# R line records it; each settled real-stakes wager left a W line with every
# draw its contest made. This script redoes the arithmetic:
#
#   commitment == SHA-256(seed)                           (for each R line)
#   r == int(SHA-256("<seed>:<client>:<nonce>")[:15], 16) % n
#                                                         (for each draw of each W line)
#
# A player can check their own bets the same way from what `fair` shows them.
#
# Usage: scripts/verify-wagers.py [<store>/.games/wagers ...]   (default ./agora-data/.games/wagers)
# Exit 0 if every revealed draw checks out (W lines whose seed is not revealed
# yet are counted as pending, not failures); 1 on any mismatch or malformed line.

import hashlib
import sys


def draw(seed, client, nonce, n):
    """The draw agora's wager_fair_value makes: 15 hex digits of SHA-256, mod n."""
    if n <= 1:
        return 0
    h = hashlib.sha256(("%s:%s:%d" % (seed, client, nonce)).encode()).hexdigest()
    return int(h[:15], 16) % n


def main():
    paths = sys.argv[1:] or ["agora-data/.games/wagers"]
    reveals = {}
    wagers = []
    bad = []
    for path in paths:
        with open(path, encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, 1):
                cols = line.rstrip("\n").split("\t")
                where = "%s:%d" % (path, lineno)
                if cols[0] == "R" and len(cols) == 7:
                    _, _ts, _who, commit, seed, client, _draws = cols
                    if hashlib.sha256(seed.encode()).hexdigest() != commit:
                        bad.append("%s: the seed does not hash to its commitment" % where)
                    reveals[commit] = (seed, client)
                elif cols[0] == "W" and len(cols) == 13:
                    wagers.append((where, cols))
                elif line.strip():
                    bad.append("%s: not a W or R line" % where)
    verified = pending = draws = 0
    for where, cols in wagers:
        _, _ts, _who, _game, commit, client, nonce0, trace = cols[:8]
        if commit not in reveals:
            pending += 1
            continue
        seed, rclient = reveals[commit]
        if rclient != client:
            bad.append("%s: client seed differs from its reveal" % where)
            continue
        ok = True
        if trace != "-":
            for k, pair in enumerate(trace.split(",")):
                n, r = (int(x) for x in pair.split(":"))
                draws += 1
                if draw(seed, client, int(nonce0) + k, n) != r:
                    bad.append("%s: draw %d (nonce %d, range %d) is not %d"
                               % (where, k, int(nonce0) + k, n, r))
                    ok = False
        verified += ok
    print("verify-wagers: %d wager(s) verified (%d draws), %d pending a reveal, %d reveal(s), %d problem(s)"
          % (verified, draws, pending, len(reveals), len(bad)))
    for b in bad:
        print("  " + b)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
