#!/usr/bin/env bash
# 17-olympiad.sh — the Olympiad: a Greco-Roman games-owner sim (1.3.6, ADR 0016).
#
# You own a stable and field a chariot team across a 12-meet ladder. Each
# event is the shared compete() primitive: a form-weighted kernel-CSPRNG
# draw resolves the race AND the SAME weights price the book. This is the
# flagship of the wager module (ADR 0013) — the race result and the betting
# odds come from one set of weights.
#
# This drives the headline loop in PRACTICE over telnet:
#   the stable hub + the meet name -> train (stat up, condition down) ->
#   enter the Hippodrome (lanes + form bars + odds) -> lay a wager ->
#   loose the gates (compete() resolves) -> the finish + purse + bet settle.
# Solo persistence (the stable save) is unit-tested (t197) and rides the
# same door-save path proven by 14-quest / 15-jabberwacky.
#
# Usage: ./17-olympiad.sh [port]
set -euo pipefail

PORT="${1:-2323}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="$ROOT/build/agora"

[ -x "$BIN" ] || { echo "build first: cyrius build src/main.cyr build/agora"; exit 1; }

"$BIN" serve "$PORT" >/tmp/agora-olympiad-17.log 2>&1 &
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
cap += cmd("play olympiad")          # the stable hub + the meet
cap += cmd("1")                      # train Speed (stat up, condition down)
cap += cmd("2")                      # train Stamina
cap += cmd("r")                      # rest (condition back)
cap += cmd("n")                      # next day (actions refill)
cap += cmd("e")                      # enter the Hippodrome -> field + odds
cap += cmd("2 20")                   # lay 20 denarii on Lane 2
cap += cmd("")                       # loose the gates -> finish + settle
cap += cmd("")                       # back to the stable
cap += cmd("q")                      # leave the door
cap += cmd("quit")
s.close()

t = cap.decode(errors="replace")
checks = [
    ("hub renders",        "THE OLYMPIAD" in t),
    ("meet on the ladder", ("Next meet" in t) and ("of 12" in t)),
    ("training works",     "tire" in t),                 # "+N, but they tire"
    ("Hippodrome renders", "THE HIPPODROME" in t),
    ("odds priced",        "pays" in t and "x" in t),    # "pays N.Mx"
    ("wager accepted",     "Wager laid" in t),
    ("race resolves",      "THE FINISH" in t and "finished" in t),
    ("bet settled",        ("wager pays" in t) or ("wager loses" in t) or ("too short to profit" in t)),
    ("leaves clean",       "bye" in t),
]
fails = [n for n, ok in checks if not ok]
if fails:
    print("FAIL —", fails); sys.exit(1)
print("OK — Olympiad: train -> enter -> wager -> race -> settle, all over telnet")
PY
