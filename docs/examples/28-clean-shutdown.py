#!/usr/bin/env python3
# 28-clean-shutdown.py
#
# Why: roadmap N1 — until 1.7.0 NEITHER serve loop could exit. Both declared
# `var stop = 0;` and looped `while (stop == 0)` with nothing anywhere assigning
# `stop`, so the only way to stop agora was to kill it: the poll model never
# drained its 64 slots and the fork model never reaped. 1.7.0 routes SIGINT and
# SIGTERM to a signalfd that both loops consume.
#
# This smoke has TEETH — every assertion below fails against a pre-1.7.0 binary:
#
#   (1) exit status. A process killed by SIGTERM exits 143 (128+15) and by
#       SIGINT 130 (128+2). A process that returns from main exits 0. This is
#       the whole difference between "killed" and "shut down", and it is the one
#       signal that cannot be faked by printing a message.
#   (2) a connected client is TOLD. The poll model owns all 64 sessions in one
#       process, so it is the only thing that can say goodbye; the notice
#       arriving proves the drain ran rather than the socket just dying with the
#       process.
#   (3) fork children are KILLABLE. fork(2) inherits the blocked signal mask, so
#       arming shutdown in the parent silently made every connection child
#       immune to SIGTERM — measured during development as
#       `SigBlk: 0000000000004002` (exactly agora's mask) on a child that then
#       survived SIGTERM. Children serve untrusted clients and are precisely the
#       processes an operator most needs to kill. This is the regression this
#       script exists to prevent, and it is invisible to every other smoke.
#
# Success: 9 checks pass; exit 0.
#
# Usage: 28-clean-shutdown.py [port]

import os
import signal
import socket
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BIN = os.path.join(ROOT, "build", "agora")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2323
STORE = "/tmp/agora-shutdown-smoke-%d" % os.getpid()

fails = []


def start(mode):
    env = dict(os.environ, AGORA_SERVE=mode)
    p = subprocess.Popen([BIN, "serve", "--port", str(PORT), "--store", STORE],
                         env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for _ in range(60):
        try:
            socket.create_connection(("127.0.0.1", PORT), timeout=1).close()
            return p
        except OSError:
            time.sleep(0.2)
    p.kill()
    return None


def check_exit(mode, sig, signame):
    """(1) the server returns from main instead of dying by signal."""
    p = start(mode)
    if p is None:
        fails.append("%s: server never came up" % mode)
        return
    p.send_signal(sig)
    try:
        rc = p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
        fails.append("%s/%s: server did not exit within 20s" % (mode, signame))
        return
    # Popen reports a signal death as a NEGATIVE returncode.
    if rc != 0:
        fails.append("%s/%s: exit %d, expected 0 (negative = killed by signal, "
                     "i.e. the pre-1.7.0 behaviour)" % (mode, signame, rc))
    else:
        print("  OK  %-4s %-7s exited cleanly (0)" % (mode, signame))


def check_client_notified():
    """(2) poll mode tells a connected client before closing it."""
    p = start("poll")
    if p is None:
        fails.append("poll: server never came up")
        return
    s = socket.create_connection(("127.0.0.1", PORT), timeout=5)
    s.settimeout(8)
    time.sleep(0.6)
    try:                       # drain the banner
        s.recv(65536)
    except OSError:
        pass
    p.send_signal(signal.SIGTERM)
    tail = b""
    try:
        while True:
            c = s.recv(65536)
            if not c:
                break
            tail += c
    except OSError:
        pass
    s.close()
    try:
        rc = p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill(); rc = -9
    if b"shutting down" not in tail:
        fails.append("poll: connected client got no shutdown notice (saw %r)" % tail[-120:])
    else:
        print("  OK  poll live client received the shutdown notice")
    if rc != 0:
        fails.append("poll: exit %d with a client attached, expected 0" % rc)
    else:
        print("  OK  poll exited cleanly with a client attached")


def check_child_killable():
    """(3) fork children must NOT inherit the parent's blocked signal mask."""
    p = start("fork")
    if p is None:
        fails.append("fork: server never came up")
        return
    s = socket.create_connection(("127.0.0.1", PORT), timeout=5)
    time.sleep(1.0)
    kids = subprocess.run(["pgrep", "-P", str(p.pid)],
                          capture_output=True, text=True).stdout.split()
    if not kids:
        fails.append("fork: no child process for the live connection")
        s.close(); p.send_signal(signal.SIGTERM); p.wait(timeout=20)
        return
    child = int(kids[0])

    # The mask itself, read straight from the kernel — the direct evidence.
    blk = ""
    try:
        with open("/proc/%d/status" % child) as f:
            for line in f:
                if line.startswith("SigBlk:"):
                    blk = line.split()[1]
    except OSError:
        pass
    if blk and int(blk, 16) != 0:
        fails.append("fork: child inherited a blocked signal mask (SigBlk=%s); "
                     "SIGINT/SIGTERM are blocked with nothing draining them" % blk)
    else:
        print("  OK  fork child has no blocked signals (SigBlk=%s)" % (blk or "?"))

    os.kill(child, signal.SIGTERM)
    time.sleep(1.0)
    alive = True
    try:
        os.kill(child, 0)
    except OSError:
        alive = False
    if alive:
        fails.append("fork: child SURVIVED SIGTERM — unkillable connection process")
        try:
            os.kill(child, signal.SIGKILL)
        except OSError:
            pass
    else:
        print("  OK  fork child died on SIGTERM")

    s.close()
    p.send_signal(signal.SIGTERM)
    try:
        rc = p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill(); rc = -9
    if rc != 0:
        fails.append("fork: parent exit %d after a child session, expected 0" % rc)
    else:
        print("  OK  fork parent exited cleanly after serving a session")


def main():
    if not os.access(BIN, os.X_OK):
        print("build first: cyrius build src/main.cyr build/agora")
        return 1
    os.makedirs(STORE, exist_ok=True)
    print("=== clean shutdown (roadmap N1) ===")
    check_exit("fork", signal.SIGTERM, "SIGTERM")
    check_exit("fork", signal.SIGINT, "SIGINT")
    check_exit("poll", signal.SIGTERM, "SIGTERM")
    check_exit("poll", signal.SIGINT, "SIGINT")
    check_client_notified()
    check_child_killable()

    subprocess.run(["rm", "-rf", STORE])
    if fails:
        for f in fails:
            print("FAIL —", f)
        return 1
    print("\nOK — both serve models shut down cleanly on SIGINT/SIGTERM; "
          "sessions notified; fork children remain killable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
