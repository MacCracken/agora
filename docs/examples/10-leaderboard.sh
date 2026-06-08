#!/usr/bin/env bash
# 10-leaderboard.sh — cross-game leaderboards (1.2.0 bite 5, ADR 0010).
#
# Every door game appends "<handle>\t<score>\t<rank>" to a shared,
# flock'd per-game file <store>/.games/<game>/leaderboard on a finished
# run (solo OR universe). `scores <game>` reads it back, top-10 by score.
#
# This script logs a player in, plays Port Authority solo to the close
# of the quarter (end-day until OVER), leaves (which posts the score),
# then asserts `scores port` lists the run.
#
# Requires: openssl >= 3.0, python3.
# Usage: ./10-leaderboard.sh [port]
set -euo pipefail

PORT="${1:-2323}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="$ROOT/build/agora"
STORE="$ROOT/bbs"
KEYS="$ROOT/keys"

[ -x "$BIN" ] || { echo "build first: cyrius build src/main.cyr build/agora"; exit 1; }

rm -rf "$STORE" "$KEYS"; mkdir -p "$KEYS"
"$BIN" keygen  --key "$KEYS/qix" >/dev/null
"$BIN" register --handle qix --key "$KEYS/qix" --store "$STORE" >/dev/null

"$BIN" serve "$PORT" --store "$STORE" >/tmp/agora-leaderboard-10.log 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null || true' EXIT
sleep 1

python3 - "$PORT" "$KEYS" <<'PY'
import socket, sys, subprocess, tempfile, binascii, os
port = int(sys.argv[1]); keys = sys.argv[2]
PK = bytes.fromhex("302e020100300506032b657004220420")
s = socket.create_connection(("127.0.0.1", port), timeout=5)
def drain(t=0.4):
    s.settimeout(t); b=b""
    try:
        while True:
            d=s.recv(4096)
            if not d: break
            b+=d
    except socket.timeout: pass
    return b.decode(errors="replace")
def cmd(l): s.sendall(l.encode()+b"\r\n"); return drain()
drain()
out = cmd("login qix")
nonce = [x.split("challenge:")[1].strip() for x in out.splitlines() if "challenge:" in x][0]
seed = open(os.path.join(keys,"qix"),"rb").read()
kf=tempfile.NamedTemporaryFile(delete=False); kf.write(PK+seed); kf.close()
mf=tempfile.NamedTemporaryFile(delete=False); mf.write(b"agora-login:"+nonce.encode()); mf.close()
sig=subprocess.check_output(["openssl","pkeyutl","-sign","-rawin","-inkey",kf.name,"-keyform","DER","-in",mf.name])
r=cmd("auth: "+binascii.hexlify(sig).decode())
assert "welcome, qix" in r, "login failed: %r" % r[-120:]
cmd("play port solo")
for _ in range(31):
    cmd("n")            # end-day until the quarter closes
cmd("")                 # press Enter on the close screen -> leave -> posts score
board = cmd("scores port")
os.unlink(kf.name); os.unlink(mf.name); s.close()
if "leaderboard" not in board or "qix" not in board:
    print("FAIL — qix not on the board:\n" + board); sys.exit(1)
print("OK — finished run posted to the leaderboard; scores port lists qix")
PY

rm -rf "$STORE" "$KEYS"
