#!/usr/bin/env python3
# 27-audit-lows.py
#
# Why: three of the four LOW findings from the 2026-07-26 audit, fixed in 1.6.5.
# All three concern input a normal session never produces, which is exactly how
# they went unnoticed — and exactly how they would regress unnoticed.
#
#   L1 — the operator's `--store` was memcpy'd into a 512-byte path buffer with
#        no bound, and every storage path is built on top of it. Operator error
#        rather than an attack, but since the 1.6.2 arena the overflow lands in
#        a SHARED buffer, so it can corrupt another allocation in the same
#        command. Now bounded once, at the single parse point each entry uses.
#
#   L2 — wire-side posts bypassed the control-byte filter the CLI applies, so
#        BEL / BS / FF / DEL persisted into stored posts and every later reader
#        got them. `input_byte_ok` now drops the C0 set (keeping TAB/CR/LF,
#        which are load-bearing for line dispatch) and DEL.
#
#   L3 — agora announces WILL ECHO at connect. A client that answered
#        `IAC DONT ECHO` got a correct `WONT ECHO` back and then kept being
#        echoed at anyway — double characters for anyone doing local echo. The
#        gate is `!= Q_NO`, deliberately NOT `== Q_YES`: a client that never
#        answers our WILL sits in Q_WANTYES forever, and gating on Q_YES would
#        kill echo for netcat, raw sockets and every scripted client. Both
#        directions are asserted here for that reason.
#
# (L4 — pipelined bytes behind `descent` — is covered by 24-descent-serve-models.sh,
# which already has the fake-MUD harness needed to assert it.)
#
# Run agora first:
#   AGORA_SERVE=poll ./build/agora serve 2323 --store ./bbs
# Requires: a registered qix (run 02-register-and-post.sh first) and openssl >= 3.0.
#
# Usage: 27-audit-lows.py [port]

import binascii
import os
import socket
import subprocess
import sys
import tempfile
import time

HOST = "127.0.0.1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2323
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
AGORA = os.path.join(ROOT, "build", "agora")


def drain(s, t=0.6):
    out = b""
    s.settimeout(t)
    try:
        while True:
            d = s.recv(65536)
            if not d:
                break
            out += d
    except Exception:
        pass
    return out


def connect():
    s = socket.create_connection((HOST, PORT), timeout=6)
    time.sleep(0.4)
    drain(s)
    return s


def login(s, keypath):
    """Ed25519 challenge/response, as in 05-telnet-login.sh."""
    s.sendall(b"login qix\r\n")
    time.sleep(0.4)
    r = drain(s)
    chal = None
    for line in r.split(b"\r\n"):
        if b"challenge:" in line:
            chal = line.split(b"challenge:")[1].strip().decode()
    if not chal:
        return False
    key = open(keypath, "rb").read()
    der = tempfile.NamedTemporaryFile(suffix=".der", delete=False)
    der.write(bytes.fromhex("302e020100300506032b657004220420") + key)
    der.close()
    msg = tempfile.NamedTemporaryFile(delete=False)
    msg.write(("agora-login:" + chal).encode())
    msg.close()
    sig = tempfile.NamedTemporaryFile(delete=False)
    sig.close()
    subprocess.run(["openssl", "pkeyutl", "-sign", "-rawin", "-inkey", der.name,
                    "-keyform", "DER", "-in", msg.name, "-out", sig.name],
                   capture_output=True)
    s.sendall(b"auth: " + binascii.hexlify(open(sig.name, "rb").read()) + b"\r\n")
    time.sleep(0.5)
    return b"welcome" in drain(s)


def test_l1_store_bound():
    """An over-long --store is refused; a normal one still works."""
    long_store = "/tmp/" + "a" * 460
    r = subprocess.run([AGORA, "list", "--store", long_store], capture_output=True)
    if r.returncode != 2 or b"too long" not in r.stdout:
        print(f"  FAIL(L1): over-long --store not refused (rc={r.returncode})")
        return False
    ok_store = "/tmp/" + "a" * 80
    r = subprocess.run([AGORA, "list", "--store", ok_store], capture_output=True)
    if r.returncode != 0:
        print(f"  FAIL(L1): a normal --store was rejected (rc={r.returncode})")
        return False
    print("  L1: over-long --store refused with exit 2; a normal one still works")
    return True


def test_l2_control_bytes(keypath):
    """BEL / BS / DEL typed into a post body must not reach storage."""
    s = connect()
    if not login(s, keypath):
        print("  FAIL(L2): could not log in")
        s.close()
        return False
    s.sendall(b"post\r\n")
    time.sleep(0.4)
    drain(s)
    s.sendall(b"control byte test\r\n")
    time.sleep(0.4)
    drain(s)
    s.sendall(b"a\x07b\x08c\x7fd\r\n")   # BEL, BS, DEL between the letters
    time.sleep(0.3)
    s.sendall(b".\r\n")
    time.sleep(0.6)
    reply = drain(s)
    s.close()

    pid = None
    for tok in reply.replace(b"#", b" ").split():
        if tok.isdigit():
            pid = int(tok)
    if pid is None:
        print(f"  FAIL(L2): could not find the new post id in {reply[:60]!r}")
        return False
    stored = open(os.path.join(ROOT, "bbs", f"{pid}.txt"), "rb").read()
    for b, name in ((0x07, "BEL"), (0x08, "BS"), (0x7F, "DEL")):
        if bytes([b]) in stored:
            print(f"  FAIL(L2): {name} survived into the stored post")
            return False
    if b"abcd" not in stored:
        print(f"  FAIL(L2): the printable text did not survive ({stored[-20:]!r})")
        return False
    print("  L2: BEL / BS / DEL dropped from the stored body, printable text intact")
    return True


def test_l3_echo_gate():
    """Echo stays on for a client that never negotiates; off after a revoke."""
    a = connect()
    a.sendall(b"hel")
    time.sleep(0.35)
    echoed = drain(a)
    a.sendall(b"p\r\n")
    time.sleep(0.3)
    drain(a)
    a.close()
    if b"hel" not in echoed:
        print("  FAIL(L3): a client that never negotiates lost its echo")
        return False

    b = connect()
    b.sendall(b"\xff\xfe\x01")      # IAC DONT ECHO
    time.sleep(0.35)
    drain(b)
    b.sendall(b"hel")
    time.sleep(0.35)
    echoed2 = drain(b)
    b.close()
    if b"hel" in echoed2:
        print("  FAIL(L3): still echoing after the client revoked ECHO")
        return False
    print("  L3: echo kept for non-negotiating clients, suppressed after IAC DONT ECHO")
    return True


def main():
    keypath = os.path.join(ROOT, "keys", "qix")
    if not os.path.exists(keypath):
        print("run 02-register-and-post.sh first (need a registered qix)")
        return 1
    if not test_l1_store_bound():
        return 1
    if not test_l2_control_bytes(keypath):
        return 1
    if not test_l3_echo_gate():
        return 1
    print("OK — audit LOWs L1/L2/L3 hold (L4 is covered by 24-descent-serve-models.sh)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
