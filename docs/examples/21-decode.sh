#!/usr/bin/env bash
# 21-decode.sh — Decode: the code-breaking door (1.4.1 / 1.4.2, ADR 0018).
#
# A single door whose game is "crack the hidden code from feedback", with two
# variants on one engine: NUMBERS (1.4.1, classic Mastermind — a 4-long code
# of colors 1..6, ten guesses, exact/present counts) and WORDS (1.4.2, Wordle
# — a 5-letter word, six guesses, per-letter green/yellow/gray). The pure
# heart is decode_classify (the duplicate-correct per-position scorer,
# unit-pinned t209/t214) — the same engine the Handler decrypt lever (1.4.3)
# reuses. agora's signature one-engine/many-variants pattern, a fourth time:
# door PRNG -> wager -> compete() -> DECODE.
#
# This drives both variants in PRACTICE over telnet:
#   play decode -> the [n]/[w] select screen -> [n] Numbers board -> a guess
#   reads back exact/present feedback; then again -> [w] Words board -> a real
#   dictionary word renders a colored row. The secret is random per game, so
#   this smoke verifies the MECHANIC (select / board / feedback), not a
#   scripted win; win/loss/score/save are unit-pinned (t211/t212/t213/t216).
#
# Usage: ./21-decode.sh [port]
set -euo pipefail

PORT="${1:-2323}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="$ROOT/build/agora"

[ -x "$BIN" ] || { echo "build first: cyrius build src/main.cyr build/agora"; exit 1; }

"$BIN" serve "$PORT" >/tmp/agora-decode-21.log 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT
sleep 1

python3 - "$PORT" <<'PY'
import socket, sys
port = int(sys.argv[1])

def drain(s, t=0.6):
    s.settimeout(t); buf = b""
    try:
        while True:
            d = s.recv(4096)
            if not d: break
            buf += d
    except socket.timeout:
        pass
    return buf

s = socket.create_connection(("127.0.0.1", port), timeout=3)
drain(s)
def cmd(line):
    s.sendall(line.encode() + b"\r\n"); return drain(s)

cap = b""
sel = cmd("play decode")             # the [n]/[w] variant select screen
cap += sel
cap += cmd("n")                      # pick Numbers -> the Mastermind board
cap += cmd("1 2 3 4")                # a guess -> exact/present feedback
cap += cmd("5 5 6 6")                # another guess -> guesses-left falls
cap += cmd("q")                      # leave the door (lone q)
words = cmd("play decode")           # select screen again
cap += words
wboard = cmd("w")                    # pick Words -> the Wordle board
cap += wboard
crane = cmd("crane")                 # a valid dictionary word -> a colored row
cap += crane
cap += cmd("q")                      # leave the door
cap += cmd("quit")
s.close()

t = cap.decode(errors="replace")
seltext = sel.decode(errors="replace")
checks = [
    ("select screen",     "DECODE" in seltext and "[n] Numbers" in seltext and "[w] Words" in seltext),
    ("numbers board",     "NUMBERS" in t),
    ("numbers feedback",  "exact" in t and "present" in t),
    ("countdown shown",   "Guesses left:" in t),
    ("words board",       "WORDS" in wboard.decode(errors="replace") and "green" in t and "yellow" in t and "gray" in t),
    ("word accepted",     "Not in the word list" not in crane.decode(errors="replace")),
    ("leaves clean",      "bye" in t),
]
fails = [n for n, ok in checks if not ok]
if fails:
    print("FAIL —", fails)
    sys.exit(1)
print("OK — Decode: select -> [n] Numbers (exact/present) -> [w] Words (colored row), over telnet")
PY
