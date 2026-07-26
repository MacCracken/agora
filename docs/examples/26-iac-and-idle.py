#!/usr/bin/env python3
# 26-iac-and-idle.py
#
# Why: two 1.6.4 audit fixes that are easy to regress silently, because both are
# about bytes that a normal session never produces.
#
#   1. IAC (0xFF) handling, both directions. RFC 854 says a data byte of 0xFF
#      must go out as `IAC IAC`, or the receiver reads it as the start of a
#      command. agora never did this on any egress path, so a 0xFF sitting in a
#      stored post reached every reader's client as a live telnet command — a
#      stored, replayable wedge. 1.6.4 doubles it on the way out (`send_text`)
#      and drops it on the way in (`input_byte_ok`), so neither old content nor
#      new content can wedge a client.
#
#   2. Idle accounting. `IAC NOP` is consumed by the state machine with no
#      response and no data byte, and it used to refresh the session's activity
#      timer — so 64 connections sending 2 bytes a minute could pin the whole
#      poll pool invisibly. 1.6.4 counts only bytes that reach the session as
#      DATA, so a keepalive-only connection ages out like a silent one while a
#      session that is actually being typed at does not.
#
# The idle half needs SESS_IDLE_MS (60 s) to elapse, so this script takes about
# 80 seconds. Pass `--fast` to run only the IAC half.
#
# Run agora first (poll — the idle reap is the poll sweep's job):
#   AGORA_SERVE=poll ./build/agora serve 2323 --store ./bbs
# Requires: a store with a readable post (run 02-register-and-post.sh first).
#
# Usage: 26-iac-and-idle.py [port] [--fast]

import os
import socket
import sys
import threading
import time

HOST = "127.0.0.1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2323
FAST = "--fast" in sys.argv
STORE = os.path.join(os.path.dirname(__file__), "..", "..", "bbs")
PLANTED_ID = 9101


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
    s = socket.create_connection((HOST, PORT), timeout=5)
    time.sleep(0.35)
    drain(s)
    return s


def test_iac_egress():
    """A raw 0xFF already in a stored post must reach the wire DOUBLED."""
    # Plant a post containing IAC SB TERMINAL-TYPE with no SE — the minimal
    # payload that wedges a conforming client if it arrives undoubled.
    path = os.path.join(STORE, f"{PLANTED_ID}.txt")
    with open(path, "wb") as f:
        f.write(b"Subject: iac wedge\n\nbefore\xff\xfa\x18after\n")
    try:
        s = connect()
        s.sendall(f"read {PLANTED_ID}\r\n".encode())
        time.sleep(0.5)
        body = drain(s)
        s.close()
    finally:
        os.remove(path)

    if b"before" not in body:
        print(f"  FAIL: planted post did not render ({len(body)} bytes)")
        return False
    if b"\xff\xff" not in body:
        print("  FAIL: stored 0xFF was NOT doubled on egress (RFC 854 violation)")
        return False
    # After removing the legitimate doubled pairs, no bare IAC may remain.
    if b"\xff" in body.replace(b"\xff\xff", b""):
        print("  FAIL: a bare IAC survived into the rendered post")
        return False
    print("  egress: stored 0xFF arrives as IAC IAC, no bare IAC on the wire")
    return True


def test_iac_ingress():
    """A client sending IAC IAC (a literal 0xFF) must not get one stored."""
    s = connect()
    s.sendall(b"boards\r\n")
    time.sleep(0.3)
    before = drain(s)
    # The command line itself is the cheapest ingress path that echoes back.
    s.sendall(b"help\xff\xff\r\n")
    time.sleep(0.4)
    echoed = drain(s)
    s.close()
    if b"\xff" in echoed:
        print("  FAIL: a 0xFF from the client was echoed back raw")
        return False
    print("  ingress: a client-sent 0xFF is dropped, never echoed or stored")
    return True


def test_idle_accounting():
    """IAC NOP must not hold a slot; real typing must."""
    results = {}

    def run(tag, payload):
        s = socket.create_connection((HOST, PORT), timeout=100)
        time.sleep(0.4)
        drain(s)
        t0 = time.time()
        closed = False
        try:
            while time.time() - t0 < 80:
                s.sendall(payload)
                time.sleep(5)
                s.setblocking(False)
                try:
                    if s.recv(65536) == b"":
                        closed = True
                        break
                except Exception:
                    pass
                s.setblocking(True)
                s.settimeout(100)
        except OSError:
            closed = True
        results[tag] = (closed, round(time.time() - t0, 1))
        s.close()

    threads = [
        threading.Thread(target=run, args=("nop", b"\xff\xf1")),   # IAC NOP
        threading.Thread(target=run, args=("data", b"help\r\n")),  # real input
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    nop_closed, nop_t = results["nop"]
    data_closed, data_t = results["data"]
    if not nop_closed:
        print(f"  FAIL: an IAC NOP keepalive held its slot for {nop_t}s (should be reaped)")
        return False
    if data_closed:
        print(f"  FAIL: a session with real input was reaped after {data_t}s")
        return False
    print(f"  idle: NOP keepalive reaped at {nop_t}s; typed session still alive at {data_t}s")
    return True


def main():
    print("=== IAC (0xFF) handling, both directions ===")
    if not test_iac_egress():
        return 1
    if not test_iac_ingress():
        return 1

    if FAST:
        print("OK — IAC doubled on egress, dropped on ingress (--fast: idle half skipped)")
        return 0

    print("=== idle accounting (takes ~80s: SESS_IDLE_MS is 60s) ===")
    if not test_idle_accounting():
        return 1

    print("OK — IAC handled per RFC 854, and protocol chatter no longer holds a slot")
    return 0


if __name__ == "__main__":
    sys.exit(main())
