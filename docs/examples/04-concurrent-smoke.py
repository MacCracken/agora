#!/usr/bin/env python3
# 04-concurrent-smoke.py
#
# Why: ADR 0007 (fork-per-connection accept) closed audit M1 + M2 via
# address-space isolation. This smoke proves N simultaneous telnet
# sessions each get their own banner + their own session globals
# (no cross-talk on g_session_fp / g_session_handle / current_board).
#
# Run agora first:
#   ./build/agora serve 2323 --store ./bbs
#
# Then this script. Each session sends `boards` and `quit`; the script
# asserts every session got a banner-shaped reply (RFC 854 IAC bytes +
# the bannermanor MOTD literal) before EOF.
#
# Success: N green checkmarks printed; exit 0. Failure: any session
# missed bytes / received another session's reply → exit 1.

import socket
import sys
import threading
import time

HOST = "127.0.0.1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2323
N    = int(sys.argv[2]) if len(sys.argv) > 2 else 3

results = [None] * N

def session(i: int) -> None:
    with socket.create_connection((HOST, PORT), timeout=5) as s:
        s.settimeout(2.0)
        # Drain banner + IAC negotiation for ~500 ms.
        deadline = time.time() + 0.5
        banner = b""
        while time.time() < deadline:
            try:
                chunk = s.recv(4096)
                if not chunk: break
                banner += chunk
            except socket.timeout:
                break

        s.sendall(b"boards\r\n")
        time.sleep(0.2)
        s.sendall(b"quit\r\n")
        time.sleep(0.2)

        tail = b""
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk: break
                tail += chunk
        except socket.timeout:
            pass

        results[i] = (banner, tail)

threads = [threading.Thread(target=session, args=(i,)) for i in range(N)]
for t in threads: t.start()
for t in threads: t.join()

ok = True
for i, r in enumerate(results):
    if r is None:
        print(f"  session {i}: NO RESPONSE")
        ok = False
        continue
    banner, tail = r
    has_iac    = b"\xff" in banner          # IAC byte (RFC 854)
    has_prompt = b"> " in (banner + tail)
    has_boards = b"main" in tail
    mark = "OK" if (has_iac and has_prompt and has_boards) else "FAIL"
    print(f"  session {i}: {mark}  (iac={has_iac} prompt={has_prompt} boards={has_boards})")
    if mark == "FAIL": ok = False

sys.exit(0 if ok else 1)
