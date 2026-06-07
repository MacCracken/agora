#!/usr/bin/env bash
# 07-play-door.sh — launch a door game over telnet (1.1.0, ADR 0009).
#
# Starts the listener, connects a scripted client, and plays a few
# turns of each of the three door games in PRACTICE mode (ephemeral,
# no login required), asserting each game's screen renders. Solo mode
# (`play <game> solo`) additionally persists progress under
# <store>/.users/<fp16>/games/ — that needs a logged-in session
# (see 05-telnet-login.sh for the sigil challenge/response).
#
# Usage: ./07-play-door.sh [port]
set -euo pipefail

PORT="${1:-2323}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="$ROOT/build/agora"

[ -x "$BIN" ] || { echo "build first: cyrius build src/main.cyr build/agora"; exit 1; }

"$BIN" serve "$PORT" >/tmp/agora-door-07.log 2>&1 &
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

cap  = cmd("play handler")        # espionage deduction
cap += cmd("c") + cmd("1") + cmd("x") + cmd("x")   # read a cable
cap += cmd("x") + cmd("z")        # cross-reference, back
cap += cmd("q")                   # leave (main-screen 'q')
cap += cmd("play smuggler")       # contraband run
cap += cmd("b") + cmd("x") + cmd("q")
cap += cmd("play port")           # space trade
cap += cmd("m") + cmd("x") + cmd("q")
cap += cmd("quit")
s.close()

t = cap.decode(errors="replace")
need = ["THE HANDLER", "CABLE QUEUE", "CROSS-REFERENCE",
        "SMUGGLER'S LEDGER", "PORT AUTHORITY", "bye"]
missing = [n for n in need if n not in t]
if missing:
    print("FAIL — missing:", missing); sys.exit(1)
print("OK — all three door games played over telnet (practice mode)")
PY
