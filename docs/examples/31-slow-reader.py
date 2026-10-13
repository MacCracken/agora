#!/usr/bin/env python3
# 31-slow-reader.py
#
# Why: the slow-reader close path has been a HIGH-severity fix three times —
# 1.6.3 (a failed send became a dead peer instead of being ignored), 1.7.0 (the
# poll tx queue's sticky overflow) and 1.8.1 (a failed fork-mode send became
# sticky, audit M10) — and until 1.8.2 it rested on inspection alone. This pins
# it: a client that asks for ~12 MB and reads NOTHING must be disconnected,
#
#   poll — promptly, once the kernel buffers and the 128 KB queue are full,
#          and without stalling a bystander session meanwhile;
#   fork — within one 60 s send timeout: the first write that times out —
#          whether or not it copied a few bytes first — latches, and the child
#          stops. Watched from OUTSIDE (the connection's child process exiting),
#          because reading the socket is exactly what un-stalls the writer.
#          Before 1.8.1 every later send waited out its own 60 s and the child
#          lived for hours; 1.8.1 latched only a write that gained NO bytes, and
#          on a zero-window peer Linux can still take a few KB into the send
#          queue on a probe's ACK — the child lived 186 s (three timeouts), as
#          the first CI run of this smoke found. The bound is per WRITE, not per
#          post: a slow reader that keeps freeing room (2400 baud) is not dropped.
#
# Self-contained: its own store under /tmp, its own servers. --fast skips the
# fork half (~70 s). Success: "OK — ..." and exit 0.
#
# Usage: 31-slow-reader.py [port] [--fast]
#        AGORA_BIN=/path/to/agora 31-slow-reader.py   (A/B an older build)

import os
import shutil
import socket
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BIN = os.environ.get("AGORA_BIN", os.path.join(ROOT, "build", "agora"))
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
PORT = int(ARGS[0]) if ARGS else 2331
FAST = "--fast" in sys.argv
BASE = "/tmp/agora-slowreader-smoke-%d" % os.getpid()
STORE = BASE + "/bbs"
READS = 200                                      # x ~61 KB of reply each
FORK_BOUND = 90                                  # SEND_TIMEOUT_SECS (60) + margin
FORK_GIVE_UP = 240                               # stop watching; report what was measured

fails = []


def check(cond, what):
    print("  %s  %s" % ("ok  " if cond else "FAIL", what))
    if not cond:
        fails.append(what)


def start(mode):
    p = subprocess.Popen([BIN, "serve", str(PORT), "--store", STORE],
                         env=dict(os.environ, AGORA_SERVE=mode),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            socket.create_connection(("127.0.0.1", PORT), timeout=1).close()
            return p
        except OSError:
            time.sleep(0.2)
    p.kill()
    return None


def stop(p):
    p.terminate()
    try:
        p.wait(8)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
    time.sleep(0.3)


def attacker():
    a = socket.socket()
    a.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
    a.connect(("127.0.0.1", PORT))
    a.sendall(b"read 1\r\n" * READS)
    return a


def drained_to_eof(a, t=3):
    """Read everything the server handed over; True if it then closed the link."""
    a.settimeout(t)
    total = 0
    try:
        while True:
            d = a.recv(1 << 20)
            if not d:
                return True, total
            total += len(d)
    except ConnectionResetError:
        return True, total
    except OSError:
        return False, total


def echo_ms(v):
    t0 = time.time()
    v.sendall(b"x")
    v.settimeout(10)
    try:
        v.recv(64)
    except OSError:
        return 10000
    return (time.time() - t0) * 1000


def poll_half():
    print("poll — the non-reader is closed, the bystander is not stalled")
    p = start("poll")
    if not p:
        check(False, "poll server started")
        return
    try:
        a = attacker()
        v = socket.create_connection(("127.0.0.1", PORT), timeout=6)
        time.sleep(0.4)
        v.recv(65536)
        worst = 0.0
        for _ in range(20):
            worst = max(worst, echo_ms(v))
            time.sleep(0.2)
        closed, got = drained_to_eof(a)
        check(closed and got < READS * 61000,
              "the non-reading client was disconnected (%d of ~%d bytes handed over)" % (got, READS * 61000))
        check(worst < 1000, "a bystander's echo stayed prompt meanwhile (worst %.0f ms)" % worst)
        v.close()
    finally:
        stop(p)


def children(pid):
    """pids whose parent is `pid`, from /proc (field 4 of stat follows the comm's ')')."""
    kids = []
    for d in os.listdir("/proc"):
        if d.isdigit():
            try:
                with open("/proc/%s/stat" % d) as f:
                    if int(f.read().rsplit(")", 1)[1].split()[1]) == pid:
                        kids.append(int(d))
            except (OSError, ValueError, IndexError):
                pass
    return kids


def fork_half():
    print("fork — the non-reader's child stops within one send timeout")
    p = start("fork")
    if not p:
        check(False, "fork server started")
        return
    try:
        t0 = time.time()
        while children(p.pid) and time.time() - t0 < 10:   # start()'s probe connection
            time.sleep(0.1)
        a = attacker()
        t0 = time.time()
        while not children(p.pid) and time.time() - t0 < 10:
            time.sleep(0.1)
        while children(p.pid) and time.time() - t0 < FORK_GIVE_UP:
            time.sleep(0.5)
        took = time.time() - t0
        closed, got = drained_to_eof(a)
        check(closed and took < FORK_BOUND,
              "the fork child closed the non-reading client after %.0f s (bound %d s: one 60 s send timeout + margin)" % (took, FORK_BOUND))
        v = socket.create_connection(("127.0.0.1", PORT), timeout=6)
        time.sleep(0.4)
        check(len(v.recv(65536)) > 0, "the server still accepts and greets")
        v.close()
    finally:
        stop(p)


def main():
    if not os.path.exists(BIN):
        print("build first: cyrius build src/main.cyr build/agora")
        return 2
    shutil.rmtree(BASE, ignore_errors=True)
    os.makedirs(STORE)
    with open(os.path.join(STORE, "1.txt"), "w") as f:
        f.write("Subject: big\r\n\r\n" + ("x" * 100 + "\r\n") * 600)
    try:
        poll_half()
        if FAST:
            print("  (fork half skipped: --fast)")
        else:
            fork_half()
    finally:
        shutil.rmtree(BASE, ignore_errors=True)
    if fails:
        print("FAIL — %d check(s): %s" % (len(fails), "; ".join(fails)))
        return 1
    print("OK — slow readers are disconnected (poll: promptly, bystander unaffected; fork: within one send timeout)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
