#!/usr/bin/env bash
# 09-universe-port.sh — Port Authority shared Universe (1.2.0, ADR 0010 bite 2).
#
# Proves the shared galaxy is real, persistent, and exclusive across
# separate logged-in sessions under fork-per-accept:
#
#   1. Two players who log in separately see the SAME deterministic
#      galaxy (identical warps out of sector 0) — one shared world.
#   2. Planet ownership is contested + exclusive: qix claims a sector;
#      pac, arriving at the same sector in a later session, is DENIED —
#      so qix's claim was written to the shared world on disk and pac
#      read it back (the flock'd world transaction, ADR 0010 bite 1).
#   3. The world snapshot persists at <store>/.games/port/world/snapshot.
#   4. Universe play is login-gated (anonymous is refused).
#
# The market economics (buying depletes stock + moves the next price)
# are unit-tested (t130-t135); this script proves the on-disk shared
# state + cross-session persistence the units can't reach.
#
# Requires: openssl >= 3.0 (Ed25519 rawin signer), python3.
# Usage: ./09-universe-port.sh [port]
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

"$BIN" serve "$PORT" --store "$STORE" >/tmp/agora-universe-09.log 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT
sleep 1

python3 - "$PORT" "$KEYS" <<'PY'
import socket, sys, subprocess, tempfile, binascii, os

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

def warps_of(frame):
    for ln in frame.splitlines():
        if "Warps:" in ln:
            return ln.strip()
    return ""

fails = []

# (4) login gating: anonymous universe play is refused
sa = session(); drain(sa)
anon = cmd(sa, "play port universe")
if "log in first" not in anon:
    fails.append("anonymous universe NOT gated: %r" % anon[-100:])
sa.close()

# (1) two players see the same deterministic galaxy
s1 = session(); drain(s1); login(s1, "qix")
f1 = cmd(s1, "play port universe")
w1 = warps_of(f1)

s2 = session(); drain(s2); login(s2, "pac")
f2 = cmd(s2, "play port universe")
w2 = warps_of(f2)

if not w1 or w1 != w2:
    fails.append("galaxy not shared: qix=%r pac=%r" % (w1, w2))

# (2) qix moves one warp and claims a planet there
cmd(s1, "m"); cmd(s1, "1")            # move along warp #1
cmd(s1, "p")                          # planet menu
claim1 = cmd(s1, "e")                 # establish
if "claimed" not in claim1.lower():
    fails.append("qix claim failed: %r" % claim1[-160:])
cmd(s1, "q")                          # leave (persists ship + world already persisted per-action)
s1.close()

# pac, in a fresh session, walks to the SAME sector and is denied
cmd(s2, "m"); cmd(s2, "1")
cmd(s2, "p")
claim2 = cmd(s2, "e")
# qix already owns it -> pa_establish_planet returns -1 -> "already hold"/denied
if "claimed" in claim2.lower():
    fails.append("pac claimed an owned sector (no exclusion!): %r" % claim2[-160:])
cmd(s2, "q")
s2.close()

if fails:
    for f in fails: print("FAIL —", f)
    sys.exit(1)
print("OK — shared galaxy, login-gated, planet ownership exclusive across sessions")
PY

# (3) the shared world snapshot persisted on disk
SNAP="$STORE/.games/port/world/snapshot"
if [ ! -s "$SNAP" ]; then
    echo "FAIL — world snapshot missing/empty at $SNAP" >&2
    exit 1
fi
echo "OK — world snapshot persisted ($(stat -c%s "$SNAP") B at $SNAP)"
rm -rf "$STORE" "$KEYS"
