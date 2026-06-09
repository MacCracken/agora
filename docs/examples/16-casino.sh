#!/usr/bin/env bash
# 16-casino.sh — the shared wager module across three doors (1.3.5, ADR 0013).
#
# 1.3.4 built src/wager.cyr (the bet → draw → resolve → settle primitive)
# but left it unreachable. 1.3.5 embeds it as flavour-with-stakes in the
# three existing doors, so this is the FIRST user-reachable wager surface:
#   - Port Authority  — the cantina Dabo Wheel  (3 lights, 1x/2x/5x)
#   - Smuggler's Ledger — back-alley Bones       (even-money Low/High)
#   - QUEST            — the tavern Card Table    (pick the suit, 3:1)
#
# Each table draws from the KERNEL CSPRNG (non-replayable), distinct from
# the games' seeded door.cyr PRNG. Practice mode gambles ephemeral chips,
# so no login is needed. Asserts each table renders + resolves a bet.
#
# Usage: ./16-casino.sh [port]
set -euo pipefail

PORT="${1:-2323}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="$ROOT/build/agora"

[ -x "$BIN" ] || { echo "build first: cyrius build src/main.cyr build/agora"; exit 1; }

"$BIN" serve "$PORT" >/tmp/agora-casino-16.log 2>&1 &
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

# --- Port Authority cantina (starts with credits) ---
cap += cmd("play port")
cap += cmd("c")               # open the cantina
cap += cmd("100 3")           # bet 100 on Red
cap += cmd("x") + cmd("q")    # leave table, quit game

# --- Smuggler back-alley dice (starts with cash) ---
cap += cmd("play smuggler")
cap += cmd("d")               # open the bones
cap += cmd("20 1")            # call 20 on LOW
cap += cmd("x") + cmd("q")

# --- QUEST tavern card table (starts at 0 gold → grind a little first) ---
cap += cmd("play quest")
for _ in range(6):            # hunt + attack a few beasts for gold
    cmd("f"); cmd("y")
    for _ in range(8):
        cmd("a")
cap += cmd("r")               # back to town
cap += cmd("c")               # open the card table
cap += cmd("5 1")             # stake 5 on Hearts (or a funds-reject if broke)
cap += cmd("x") + cmd("q")

cap += cmd("quit")
s.close()

t = cap.decode(errors="replace")

# Each table must RENDER and produce a WAGER RESPONSE.
checks = [
    ("PA cantina renders",   "Dabo Wheel" in t),
    ("PA wheel resolves",    "wheel lands on" in t),
    ("SL bones render",      "Bones" in t),
    ("SL bones resolve",     "bones come up" in t),
    ("QUEST table renders",  "Tavern Card Table" in t),
    # a real deal, or a funds-reject if the grind got unlucky — either proves the wiring
    ("QUEST table resolves", ("deal turns up" in t) or ("much to wager" in t)),
]
fails = [name for name, ok in checks if not ok]
if fails:
    print("FAIL —", fails); sys.exit(1)
print("OK — wager module reachable across all three doors (cantina / dice / cards)")
PY
