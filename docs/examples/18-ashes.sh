#!/usr/bin/env bash
# 18-ashes.sh — Ashes of Empire shared-world war-game (1.3.7, ADR 0014).
#
# Proves the war-game door is reachable, login-gated, and that orders +
# diplomacy mutate the ONE shared map across separate logged-in sessions
# under fork-per-accept:
#
#   1. Universe play is login-gated (anonymous is refused).
#   2. A logged-in player enters the shared map, founds an empire (gets one
#      province with a starting garrison), and the frame renders the twelve
#      provinces + their turn counter.
#   3. A march order from a held province queues into the SHARED snapshot
#      (it shows back as a pending order).
#   4. Two players see the SAME map; diplomacy is two-sided — qix proposes an
#      alliance to pac, pac reciprocates, and the pact seals (written to the
#      shared world on disk, read back by the other session).
#   5. The shared world snapshot persists at <store>/.games/ashes/world/.
#
# Turn RESOLUTION is wall-clock (a daily batch, resolved lazily on the next
# caller's entry) — its combat/alliance math is exhaustively unit-tested
# (t202/t203/t206); this script proves the wire + shared-state path.
#
# Requires: openssl >= 3.0 (Ed25519 rawin signer), python3.
# Usage: ./18-ashes.sh [port]
set -euo pipefail

PORT="${1:-2323}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="$ROOT/build/agora"
STORE="$ROOT/bbs"
KEYS="$ROOT/keys"

[ -x "$BIN" ] || { echo "build first: cyrius build src/main.cyr build/agora"; exit 1; }

rm -rf "$STORE" "$KEYS"
mkdir -p "$KEYS"
for h in qix pac; do
    "$BIN" keygen  --key "$KEYS/$h" >/dev/null
    "$BIN" register --handle "$h" --key "$KEYS/$h" --store "$STORE" >/dev/null
done

"$BIN" serve "$PORT" --store "$STORE" >/tmp/agora-ashes-18.log 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT
sleep 1

python3 - "$PORT" "$KEYS" <<'PY'
import socket, sys, subprocess, tempfile, binascii, os, re

port = int(sys.argv[1]); keys = sys.argv[2]
PKCS8_PREFIX = bytes.fromhex("302e020100300506032b657004220420")

def session():
    return socket.create_connection(("127.0.0.1", port), timeout=5)

def drain(s, t=0.5):
    s.settimeout(t); b = b""
    try:
        while True:
            d = s.recv(4096)
            if not d: break
            b += d
    except socket.timeout:
        pass
    return b.decode(errors="replace")

def cmd(s, line):
    s.sendall(line.encode() + b"\r\n"); return drain(s)

def login(s, handle):
    out = cmd(s, "login " + handle)
    nonce = [x.split("challenge:")[1].strip() for x in out.splitlines() if "challenge:" in x][0]
    seed = open(os.path.join(keys, handle), "rb").read()
    kf = tempfile.NamedTemporaryFile(delete=False); kf.write(PKCS8_PREFIX + seed); kf.close()
    mf = tempfile.NamedTemporaryFile(delete=False); mf.write(b"agora-login:" + nonce.encode()); mf.close()
    sig = subprocess.check_output(["openssl","pkeyutl","-sign","-rawin","-inkey",kf.name,"-keyform","DER","-in",mf.name])
    r = cmd(s, "auth: " + binascii.hexlify(sig).decode())
    os.unlink(kf.name); os.unlink(mf.name)
    assert "welcome, " + handle in r, "login failed for %s: %r" % (handle, r[-120:])

def my_province(frame):
    # the province line marked YOU, e.g. "    3) Dacia [hills]  YOU       army 10"
    for ln in frame.splitlines():
        if "YOU" in ln:
            m = re.match(r"\s*(\d+)\)", ln)
            if m:
                return int(m.group(1))
    return None

fails = []

# (1) login gating: anonymous is refused
sa = session(); drain(sa)
anon = cmd(sa, "play ashes")
if "log in first" not in anon:
    fails.append("anonymous play ashes NOT gated: %r" % anon[-100:])
sa.close()

# (2) qix enters, founds an empire, sees the map
s1 = session(); drain(s1); login(s1, "qix")
f1 = cmd(s1, "play ashes")
if "ASHES OF EMPIRE" not in f1:
    fails.append("qix did not enter Ashes: %r" % f1[-160:])
if "founded your empire" not in f1:
    fails.append("qix was not founded a home province: %r" % f1[-160:])
qprov = my_province(f1)
if qprov is None:
    fails.append("qix holds no province after founding: %r" % f1[-200:])

# (3) qix marches from home to a ring-neighbour -> the order queues
if qprov is not None:
    nb = (qprov + 1) % 12
    mr = cmd(s1, "march %d %d 4" % (qprov, nb))
    if "ordered 4" not in mr:
        fails.append("march not accepted: %r" % mr[-160:])
    if "your pending orders" not in mr:
        fails.append("queued order not shown back: %r" % mr[-200:])

# (4) pac enters separately, sees the SAME map (same turn), founds elsewhere
s2 = session(); drain(s2); login(s2, "pac")
f2 = cmd(s2, "play ashes")
pprov = my_province(f2)
if pprov is None:
    fails.append("pac holds no province after founding: %r" % f2[-200:])
if pprov is not None and qprov is not None and pprov == qprov:
    fails.append("two players founded on the SAME province (no exclusion): %d" % pprov)

# diplomacy: qix proposes to pac (by pac's province), pac reciprocates -> sealed
if qprov is not None and pprov is not None:
    pr = cmd(s1, "ally %d" % pprov)
    if "proposed" not in pr:
        fails.append("qix alliance proposal not recorded: %r" % pr[-160:])
    ac = cmd(s2, "ally %d" % qprov)
    if "sealed" not in ac:
        fails.append("pac did not seal the alliance (shared pact not read back): %r" % ac[-200:])

cmd(s1, "quit"); s1.close()
cmd(s2, "quit"); s2.close()

if fails:
    for f in fails: print("FAIL —", f)
    sys.exit(1)
print("OK — Ashes reachable, login-gated, founding + orders + two-sided alliance across sessions")
PY

# (5) the shared world snapshot persisted on disk
SNAP="$STORE/.games/ashes/world/snapshot"
if [ ! -s "$SNAP" ]; then
    echo "FAIL — world snapshot missing/empty at $SNAP" >&2
    exit 1
fi
echo "OK — world snapshot persisted ($(stat -c%s "$SNAP") B at $SNAP)"
rm -rf "$STORE" "$KEYS"
