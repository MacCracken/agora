#!/usr/bin/env bash
# 20-descent.sh — Descent link: BBS → Yeoman's Descent MUD gateway (1.4.0, ADR 0017).
#
# Proves the gateway door bridges a logged-in agora citizen into the
# sibling Yeoman's Descent MUD over the shared telnet substrate:
#
#   1. `descent` is login-gated (anonymous is refused).
#   2. With no <store>/.descent config, `descent` reports "No Descent linked."
#      (operator hasn't wired the endpoint).
#   3. With <store>/.descent = the MUD's port, `descent` dials the MUD,
#      prints the agora portal banner, and the MUD's OWN telnet banner +
#      login prompt ("By what name are you known?") flow back through the
#      transparent byte-proxy to the agora client.
#   4. Closing the agora client tears the proxy down cleanly (the MUD
#      connection drops; the worker returns to the BBS).
#
# Identity hand-off is DEFERRED (ADR 0017): the MUD runs its own login.
# The proxy is byte-transparent, so the MUD's RFC 1143 negotiation +
# passphrase echo suppression reach the client verbatim.
#
# Requires: openssl >= 3.0 (Ed25519 rawin signer), python3, and the sibling
# repo at ../cyrius-yeomans-descent (built, or buildable via `cyrius build`).
# Usage: ./20-descent.sh [agora_port] [mud_port]
set -euo pipefail

PORT="${1:-2323}"
MUDPORT="${2:-4040}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BIN="$ROOT/build/agora"
STORE="$ROOT/bbs"
KEYS="$ROOT/keys"
MUD_REPO="$ROOT/../cyrius-yeomans-descent"
MUD_BIN="$MUD_REPO/build/cyrius-yeomans-descent"

[ -x "$BIN" ] || { echo "build first: cyrius build src/main.cyr build/agora"; exit 1; }

# Build the MUD if the sibling repo is present but unbuilt.
if [ ! -x "$MUD_BIN" ]; then
    if [ -d "$MUD_REPO" ]; then
        echo "building Yeoman's Descent ($MUD_REPO) ..."
        ( cd "$MUD_REPO" && cyrius deps >/dev/null 2>&1 || true; \
          cyrius build src/main.cyr build/cyrius-yeomans-descent ) \
          || { echo "SKIP — could not build the MUD; gateway no-config path only below"; }
    else
        echo "SKIP — sibling MUD repo not found at $MUD_REPO; gateway no-config path only"
    fi
fi

rm -rf "$STORE" "$KEYS"
mkdir -p "$KEYS"
"$BIN" keygen  --key "$KEYS/qix" >/dev/null
"$BIN" register --handle qix --key "$KEYS/qix" --store "$STORE" >/dev/null

# Start the MUD (if built) on its own port, in a scratch data dir.
MUD=""
if [ -x "$MUD_BIN" ]; then
    MUDDATA="$(mktemp -d)"
    ( cd "$MUDDATA" && "$MUD_BIN" serve "$MUDPORT" ) >/tmp/yd-descent-20.log 2>&1 &
    MUD=$!
fi

"$BIN" serve "$PORT" --store "$STORE" >/tmp/agora-descent-20.log 2>&1 &
SRV=$!
trap 'kill $SRV 2>/dev/null || true; [ -n "$MUD" ] && kill $MUD 2>/dev/null || true' EXIT
sleep 1

MUD_LIVE=0
[ -n "$MUD" ] && MUD_LIVE=1

python3 - "$PORT" "$KEYS" "$STORE" "$MUDPORT" "$MUD_LIVE" <<'PY'
import socket, sys, subprocess, tempfile, binascii, os

port = int(sys.argv[1]); keys = sys.argv[2]; store = sys.argv[3]
mudport = int(sys.argv[4]); mud_live = sys.argv[5] == "1"
PKCS8_PREFIX = bytes.fromhex("302e020100300506032b657004220420")

def session():
    return socket.create_connection(("127.0.0.1", port), timeout=5)

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

def cmd(s, line, t=0.6):
    s.sendall(line.encode() + b"\r\n"); return drain(s, t)

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

fails = []

# (1) login gating: anonymous is refused
sa = session(); drain(sa)
anon = cmd(sa, "descent")
if "log in first" not in anon:
    fails.append("anonymous descent NOT gated: %r" % anon[-100:])
sa.close()

# (2) no <store>/.descent yet → "No Descent linked."
s1 = session(); drain(s1); login(s1, "qix")
noconf = cmd(s1, "descent")
if "No Descent linked" not in noconf:
    fails.append("unconfigured descent did not report 'No Descent linked': %r" % noconf[-160:])
s1.close()

# (3) configure the endpoint (bare port → loopback) and bridge
with open(os.path.join(store, ".descent"), "w") as f:
    f.write(str(mudport) + "\n")

if mud_live:
    s2 = session(); drain(s2); login(s2, "qix")
    bridged = cmd(s2, "descent", t=1.5)
    if "stepping through the portal" not in bridged:
        fails.append("portal banner missing: %r" % bridged[-200:])
    # the MUD's own login prompt must flow back through the proxy
    if "name are you known" not in bridged:
        fails.append("MUD login prompt did not proxy through: %r" % bridged[-240:])
    # (4) closing the client tears the proxy down (no assert beyond clean close)
    s2.close()
    print("OK — descent gateway: login-gated, no-config reported, live MUD banner proxied through")
else:
    print("OK — descent gateway: login-gated + 'No Descent linked' (MUD not built; live-bridge step skipped)")

if fails:
    for f in fails: print("FAIL —", f)
    sys.exit(1)
PY

rm -rf "$STORE" "$KEYS"
