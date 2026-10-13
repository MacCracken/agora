#!/usr/bin/env python3
# 32-store-hardening.py
#
# Why: 1.9.0 — the store trusted whatever a name in it turned out to be (audit
# 1.8.1 I11). Every store open followed a symlink and blocked on a FIFO:
#
#   - a FIFO named `2.txt` HUNG THE WHOLE POLL SERVER on the next `list` or
#     `read` — the open waits for a writer that never comes, and under poll that
#     one open is every session's;
#   - a symlink `3.txt -> <any file the agora user can read>` served that file
#     to anonymous telnet users as a post.
#
# Both need write access to the store, which is not the same as being the
# operator. 1.9.0 opens every store file O_NOFOLLOW | O_NONBLOCK and refuses
# anything that is not a regular file (src/arena.cyr `store_open`). This smoke
# has TEETH: against a 1.8.2 binary the poll `list` never answers and the
# symlinked "post" is served.
#
# Self-contained: its own store under /tmp, its own servers, BOTH serve models.
# Success: "OK — ..." and exit 0.
#
# Usage: 32-store-hardening.py [port]
#        AGORA_BIN=/path/to/agora 32-store-hardening.py   (A/B an older build)

import os
import shutil
import signal
import socket
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BIN = os.environ.get("AGORA_BIN", os.path.join(ROOT, "build", "agora"))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2332
BASE = "/tmp/agora-storehard-smoke-%d" % os.getpid()
STORE = BASE + "/bbs"

fails = []


def check(cond, what):
    print("  %s  %s" % ("ok  " if cond else "FAIL", what))
    if not cond:
        fails.append(what)


def start(mode):
    # Its own session, so stop() can reap fork children too — against a pre-1.9.0
    # build one is blocked opening the FIFO for good and outlives its server.
    p = subprocess.Popen([BIN, "serve", str(PORT), "--store", STORE],
                         env=dict(os.environ, AGORA_SERVE=mode),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", PORT), timeout=1).close()
            time.sleep(0.2)
            return p
        except OSError:
            time.sleep(0.1)
    p.kill()
    return None


def stop(p):
    p.terminate()
    try:
        p.wait(8)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
    try:
        os.killpg(p.pid, signal.SIGKILL)
    except OSError:
        pass
    time.sleep(0.3)


def connect():
    s = socket.create_connection(("127.0.0.1", PORT), timeout=6)
    until(s, b"> ", 4)
    return s


def until(s, marker, t):
    """Read until `marker` or `t` seconds pass; return (got_marker, bytes)."""
    s.settimeout(0.2)
    out = b""
    end = time.time() + t
    while time.time() < end:
        try:
            d = s.recv(65536)
        except socket.timeout:
            continue
        except OSError:
            break
        if not d:
            break
        out += d
        if marker in out:
            return True, out
    return False, out


def cmd(s, line, t=3):
    s.sendall(line + b"\r\n")
    return until(s, b"> ", t)


def post_file(path, subject, body):
    with open(path, "wb") as f:
        f.write(b"Subject: " + subject + b"\r\n\r\n" + body + b"\r\n")


def build_store():
    shutil.rmtree(BASE, ignore_errors=True)
    os.makedirs(STORE + "/fifo")
    os.makedirs(STORE + "/lnk")
    post_file(STORE + "/fifo/1.txt", b"plain one", b"hello")
    os.mkfifo(STORE + "/fifo/2.txt")
    post_file(STORE + "/lnk/1.txt", b"plain lnk", b"hello")
    post_file(BASE + "/outside.txt", b"SECRET-OUTSIDE", b"secret body")
    os.symlink(BASE + "/outside.txt", STORE + "/lnk/3.txt")


# ------------------------------------------------------------- store opens
def store_open_checks(mode):
    print("A — store opens refuse FIFOs and symlinks (%s)" % mode)
    p = start(mode)
    if not p:
        check(False, "%s server started" % mode)
        return
    try:
        # The symlink first: a FIFO hangs a pre-1.9.0 poll server, and nothing
        # after that could fail on its own merits.
        a = connect()
        cmd(a, b"enter lnk")
        ok, out = cmd(a, b"list")
        check(ok and b"plain lnk" in out and b"SECRET-OUTSIDE" not in out,
              "%s: `list` does not show the symlinked file's subject" % mode)
        ok, out = cmd(a, b"read 3")
        check(ok and b"post not found" in out and b"secret body" not in out,
              "%s: `read 3` (a symlink out of the store) is 'post not found'" % mode)
        cmd(a, b"enter fifo")
        ok, out = cmd(a, b"list")
        check(ok and b"plain one" in out,
              "%s: `list` over a FIFO named 2.txt answers (the FIFO is skipped)" % mode)
        ok, out = cmd(a, b"read 2")
        check(ok and b"post not found" in out, "%s: `read 2` (the FIFO) is 'post not found'" % mode)
        try:
            v = socket.create_connection(("127.0.0.1", PORT), timeout=3)
            got, _ = until(v, b"> ", 3)
            v.close()
        except OSError:
            got = False
        check(got, "%s: a second client is still greeted" % mode)
        a.close()
    finally:
        stop(p)


def main():
    if not os.path.exists(BIN):
        print("build first: cyrius build src/main.cyr build/agora")
        return 2
    try:
        build_store()
        for mode in ("poll", "fork"):
            store_open_checks(mode)
    finally:
        shutil.rmtree(BASE, ignore_errors=True)
    if fails:
        print("FAIL — %d check(s): %s" % (len(fails), "; ".join(fails)))
        return 1
    print("OK — the store refuses FIFOs and symlinks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
