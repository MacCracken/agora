#!/usr/bin/env bash
# 19-ashes-concurrency.sh — Ashes of Empire shared-world concurrency
# (1.3.7, ADR 0014) — no lost updates / no colliding foundings.
#
# The generic world-transaction framework is already proven lossless under
# fanout by 08-world-concurrency.sh (PROCS×COUNT flock'd +1s). This script
# proves the Ashes-SPECIFIC shared-state path is correct across concurrent
# fork-per-accept worker processes:
#
#   N players log in and, at a release BARRIER, all enter `play ashes` at
#   once — so N foundings (ash_spawn) and N march orders race against ONE
#   shared world. Because founding + order-push run inside the flock'd world
#   transaction, the result must be exactly N DISTINCT provinces owned (no
#   two players seized the same province, no founding lost) and the snapshot
#   must be intact. A broken lock would show as < N owned provinces.
#
# Requires: openssl >= 3.0 (Ed25519 rawin signer), python3.
# Usage: ./19-ashes-concurrency.sh [port] [players]
set -euo pipefail

PORT="${1:-2323}"
PLAYERS="${2:-6}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="$ROOT/build/agora"
STORE="$ROOT/bbs"
KEYS="$ROOT/keys"

[ -x "$BIN" ] || { echo "build first: cyrius build src/main.cyr build/agora"; exit 1; }

rm -rf "$STORE" "$KEYS"
mkdir -p "$KEYS"
# three-letter arcade handles (avoid 'alice'); generate PLAYERS of them
ALL=(qix pac zax dig jst png vec trn rly bsk)
HANDLES=("${ALL[@]:0:$PLAYERS}")
for h in "${HANDLES[@]}"; do
    "$BIN" keygen  --key "$KEYS/$h" >/dev/null
    "$BIN" register --handle "$h" --key "$KEYS/$h" --store "$STORE" >/dev/null
done

"$BIN" serve "$PORT" --store "$STORE" >/tmp/agora-ashes-19.log 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT
sleep 1

python3 - "$PORT" "$KEYS" "$PLAYERS" "${HANDLES[*]}" <<'PY'
import socket, sys, subprocess, tempfile, binascii, os, re, threading

port = int(sys.argv[1]); keys = sys.argv[2]; nplayers = int(sys.argv[3])
handles = sys.argv[4].split()
PKCS8_PREFIX = bytes.fromhex("302e020100300506032b657004220420")

def drain(s, t=0.6):
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
    cmd(s, "auth: " + binascii.hexlify(sig).decode())
    os.unlink(kf.name); os.unlink(mf.name)

def my_province(frame):
    for ln in frame.splitlines():
        if "YOU" in ln:
            m = re.match(r"\s*(\d+)\)", ln)
            if m: return int(m.group(1))
    return None

barrier = threading.Barrier(nplayers)
results = [None] * nplayers
errors = [None] * nplayers

def play(idx, handle):
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=8)
        drain(s); login(s, handle)
        barrier.wait()                       # all foundings race together
        f = cmd(s, "play ashes")
        prov = my_province(f)
        results[idx] = prov
        if prov is not None:                 # march home -> neighbour (order races too)
            cmd(s, "march %d %d 3" % (prov, (prov + 1) % 12))
        cmd(s, "quit"); s.close()
    except Exception as e:
        errors[idx] = repr(e)

ts = [threading.Thread(target=play, args=(i, handles[i])) for i in range(nplayers)]
for t in ts: t.start()
for t in ts: t.join()

fails = []
for i in range(nplayers):
    if errors[i]: fails.append("player %s errored: %s" % (handles[i], errors[i]))
founded = [p for p in results if p is not None]
if len(founded) != nplayers:
    fails.append("not all founded: %r" % results)
if len(set(founded)) != len(founded):
    fails.append("COLLISION — two players seized the same province: %r" % results)

# a fresh verifier session counts owned provinces in the one shared world
sv = socket.create_connection(("127.0.0.1", port), timeout=8)
drain(sv); login(sv, handles[0])
frame = cmd(sv, "play ashes")
owned = sum(1 for ln in frame.splitlines() if ("YOU" in ln) or ("rival#" in ln))
cmd(sv, "quit"); sv.close()
if owned != nplayers:
    fails.append("shared map shows %d owned, expected %d (lost founding?)" % (owned, nplayers))

if fails:
    for f in fails: print("FAIL —", f)
    sys.exit(1)
print("OK — %d concurrent foundings, all distinct, %d provinces owned in one shared world (flock serialized correctly)" % (nplayers, owned))
PY

rm -rf "$STORE" "$KEYS"
