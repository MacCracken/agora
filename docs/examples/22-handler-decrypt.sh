#!/usr/bin/env bash
# 22-handler-decrypt.sh — The Handler's decode decrypt lever (1.4.3, ADR 0019).
#
# The decode engine (ADR 0018) embedded inside The Handler as a desk-bound
# cryptanalysis action: reading a cable, the section chief can spend a dispatch
# point to BREAK ITS CIPHER — a decode round (a Numbers relay code for
# paperwork, a Words codename for an intercept) whose secret is derived
# deterministically from the cable itself. Cracking it reveals the one fact the
# cable UI never shows: whether the cable's discrepancy is a DELIBERATE PLANT
# (the mole's forged routing) or mere clerical NOISE (an honest false positive)
# — the planted-anomaly ground truth (CB_ANOM). The point cost keeps it from
# being brute-forced across every cable (which would trivialize the mole hunt).
#
# This drives the lever in PRACTICE over telnet:
#   play handler -> [c]ables -> read a cable -> the "[D] break the cipher"
#   prompt -> [d] enters a decode round (the DECODE board) -> back out.
# The decode secret is derived per cable, so this smoke verifies the MECHANIC
# (the prompt, the round entry, the return); the crack -> plant/noise verdict
# is unit-pinned (t217 derivation determinism, t218 the full win/quit flow).
#
# Usage: ./22-handler-decrypt.sh [port]
set -euo pipefail

PORT="${1:-2323}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="$ROOT/build/agora"

[ -x "$BIN" ] || { echo "build first: cyrius build src/main.cyr build/agora"; exit 1; }

"$BIN" serve "$PORT" >/tmp/agora-handler-decrypt-22.log 2>&1 &
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
cap += cmd("play handler")           # the section-chief desk
cap += cmd("c")                      # the cable queue
read = cmd("1")                      # read the first cable -> the decrypt prompt
cap += read
board = cmd("d")                     # break the cipher -> a decode round
cap += board
back = cmd("q")                      # abandon the round -> back to the cable
cap += back
cap += cmd("x")                      # back to the cable queue
cap += cmd("x")                      # back to the desk
cap += cmd("q")                      # leave the door
cap += cmd("quit")
s.close()

t = cap.decode(errors="replace")
rtext = read.decode(errors="replace")
btext = board.decode(errors="replace")
ktext = back.decode(errors="replace")
checks = [
    ("handler desk",    "THE HANDLER" in t),
    ("cable queue",     "CABLE QUEUE" in t),
    ("decrypt prompt",  "break the cipher" in rtext),
    ("decode round",    "DECODE" in btext and "Guesses left:" in btext),
    ("returns to cable","cipher holds" in ktext),
    ("leaves clean",    "bye" in t),
]
fails = [n for n, ok in checks if not ok]
if fails:
    print("FAIL —", fails)
    sys.exit(1)
print("OK — Handler decrypt: read cable -> [D] break cipher -> decode round -> return, over telnet")
PY
