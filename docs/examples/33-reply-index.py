#!/usr/bin/env python3
# 33-reply-index.py
#
# Why: 1.9.1 — `read <id>` lists the post's replies ("Replies: 2, 4"), and until
# 1.9.1 it found them by opening EVERY post on the board (ADR 0005's scan): O(n)
# per `read`, the whole server's time under poll, and blind to replies older than
# the newest 4,096 posts. The reply index (`<board>/.replies/`, ADR 0027) answers
# from one file per parent, verified against the posts themselves. No smoke had
# ever checked a `Replies:` line, so this one pins threading end to end:
#
#   - a board written by hand (what a pre-1.9.1 store holds) is indexed when the
#     server starts, and `read` lists the same replies the scan did;
#   - a reply made with `agora post --reply-to` is listed at once;
#   - a reply written into the board behind the index's back is NOT listed (the
#     complete index is trusted — the scan no longer runs) until `.replies/` is
#     deleted and the server restarted, which rebuilds it: the documented
#     procedure for hand edits.
#
# Self-contained: its own key + store under /tmp, its own servers, BOTH serve
# models. Success: "OK — ..." and exit 0.
#
# Usage: 33-reply-index.py [port]
#        AGORA_BIN=/path/to/agora 33-reply-index.py   (A/B an older build)

import os
import shutil
import signal
import socket
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BIN = os.environ.get("AGORA_BIN", os.path.join(ROOT, "build", "agora"))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2333
BASE = "/tmp/agora-replyidx-smoke-%d" % os.getpid()
STORE = BASE + "/bbs"
KEY = BASE + "/qix.key"

fails = []


def check(cond, what):
    print("  %s  %s" % ("ok  " if cond else "FAIL", what))
    if not cond:
        fails.append(what)


def start(mode):
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


def until(s, marker, t):
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
            return out
    return out


def read_replies(mode, pid):
    """`read <pid>` over the wire; returns the Replies line's ids as a list."""
    s = socket.create_connection(("127.0.0.1", PORT), timeout=6)
    until(s, b"> ", 4)
    s.sendall(b"read %d\r\n" % pid)
    out = until(s, b"\r\n> ", 4)
    s.close()
    for line in out.split(b"\r\n"):
        if line.startswith(b"Replies: "):
            return [int(x) for x in line[9:].split(b", ")]
    return []


def post_file(n, reply_to):
    with open("%s/%d.txt" % (STORE, n), "wb") as f:
        f.write(b"Subject: post %d\r\n" % n)
        if reply_to:
            f.write(b"Reply-To: %d\r\n" % reply_to)
        f.write(b"\r\nbody %d\r\n" % n)


def cli(*args, stdin=None):
    return subprocess.run([BIN] + list(args), input=stdin, capture_output=True, timeout=20)


def main():
    if not os.path.exists(BIN):
        print("build first: cyrius build src/main.cyr build/agora")
        return 2
    shutil.rmtree(BASE, ignore_errors=True)
    os.makedirs(STORE)
    try:
        # A hand-written (pre-1.9.1) board: 2 and 4 reply to 1, 5 replies to 2.
        for n, r in ((1, 0), (2, 1), (3, 0), (4, 1), (5, 2)):
            post_file(n, r)
        cli("keygen", "--key", KEY)
        cli("register", "--handle", "qix", "--key", KEY, "--store", STORE)

        print("A — a board written by hand is indexed when the server starts")
        p = start("poll")
        try:
            check(os.path.exists(STORE + "/.replies/.complete"), "poll: the startup built .replies/.complete")
            check(read_replies("poll", 1) == [2, 4], "poll: read 1 lists 2, 4")
            check(read_replies("poll", 2) == [5], "poll: read 2 lists 5")
            check(read_replies("poll", 3) == [], "poll: read 3 lists none")
            r = cli("post", "--as", "qix", "--key", KEY, "--store", STORE, "--subject", "cli reply",
                    "--reply-to", "1", stdin=b"a reply from the CLI\n")
            check(r.returncode == 0, "the CLI reply to 1 was posted")
            check(read_replies("poll", 1) == [2, 4, 6], "poll: read 1 lists the CLI reply (6) at once")
        finally:
            stop(p)

        print("B — the same store under fork, index already built")
        p = start("fork")
        try:
            check(read_replies("fork", 1) == [2, 4, 6], "fork: read 1 lists 2, 4, 6")
            post_file(7, 1)              # written behind the index's back
            check(read_replies("fork", 1) == [2, 4, 6],
                  "fork: a reply added by hand is not listed (the complete index is trusted)")
        finally:
            stop(p)

        print("C — deleting .replies/ and restarting rebuilds it")
        shutil.rmtree(STORE + "/.replies", ignore_errors=True)
        p = start("poll")
        try:
            check(read_replies("poll", 1) == [2, 4, 6, 7], "poll: after the rebuild read 1 lists 2, 4, 6, 7")
        finally:
            stop(p)
    finally:
        shutil.rmtree(BASE, ignore_errors=True)
    if fails:
        print("FAIL — %d check(s): %s" % (len(fails), "; ".join(fails)))
        return 1
    print("OK — replies are listed from the reply index, built at start and kept at post time")
    return 0


if __name__ == "__main__":
    sys.exit(main())
