#!/usr/bin/env python3
# 30-audit-1.8.1.py
#
# Why: 1.8.1 is a code audit + repair cut (docs/audit/2026-10-12-audit-1.8.1.md),
# and most of what it fixed lives in src/main.cyr — the serve loops, the door
# glue, the CLI — which the unit suite cannot reach (src/test.cyr does not
# include main.cyr). This smoke pins the wire- and CLI-visible fixes. It has
# TEETH: against a 1.8.0 binary (AGORA_BIN=...) every check below fails.
#
#   A  `.policy` FAILS CLOSED      an unrecognised policy ("Admin") used to mean
#                                  OPEN; it now means admin-only (audit S1)
#   B  `.admins` past 4 KB         the line cut at byte 4096 matched as a whole
#                                  handle: `qixbert` admitted `qix` (audit S2)
#   C  CLI body over 64 KB         was stored truncated, exit 0 (audit S12)
#   D  `serve --store` (no value)  spun at 100% CPU forever (audit S13)
#   E  poll fairness               4 anonymous clients pipelining `read 1`
#                                  stalled every other session for seconds (H2)
#   F  big `list` under poll       >128 KB of output dropped the session (S5/P3)
#   G  disconnect saves            a dropped connection discarded solo progress,
#                                  so losses could be undone (audit D1)
#   H  one game, one session       two sessions under one identity could play the
#                                  same save against each other (audit D1)
#   I  pubkey bound to its fp      a key copied over another user's
#                                  `public_key.bin` logged in AS them (audit S4)
#
# G and H run under BOTH serve models; E and F are poll-only by nature.
# Self-contained: makes its own keys + store under /tmp, starts and stops its own
# servers. Requires openssl >= 3.0 (Ed25519 login).
#
# Success: "OK — ..." and exit 0.
#
# Usage: 30-audit-1.8.1.py [port]
#        AGORA_BIN=/path/to/agora 30-audit-1.8.1.py   (A/B an older build)

import binascii
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BIN = os.environ.get("AGORA_BIN", os.path.join(ROOT, "build", "agora"))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2330
BASE = "/tmp/agora-audit181-smoke-%d" % os.getpid()
STORE = BASE + "/bbs"
KEYS = {"qix": BASE + "/qix.key", "pac": BASE + "/pac.key"}

fails = []


def check(cond, what):
    print("  %s  %s" % ("ok  " if cond else "FAIL", what))
    if not cond:
        fails.append(what)


def run(args, stdin=None, timeout=20):
    return subprocess.run([BIN] + args, input=stdin, capture_output=True, timeout=timeout)


def drain(s, t=0.6):
    out = b""
    s.settimeout(t)
    try:
        while True:
            d = s.recv(1 << 20)
            if not d:
                break
            out += d
    except OSError:
        pass
    return out


def connect():
    s = socket.create_connection(("127.0.0.1", PORT), timeout=6)
    time.sleep(0.4)
    drain(s)
    return s


def login(s, handle, keyname=None):
    """Ed25519 challenge/response, signing with KEYS[keyname] (default: handle's)."""
    s.sendall(b"login " + handle.encode() + b"\r\n")
    time.sleep(0.4)
    chal = None
    for line in drain(s).split(b"\r\n"):
        if b"challenge:" in line:
            chal = line.split(b"challenge:")[1].strip().decode()
    if not chal:
        return False
    tmp = tempfile.mkdtemp(dir=BASE)
    der, msg, sig = (os.path.join(tmp, n) for n in ("k.der", "m", "s"))
    with open(der, "wb") as f:
        f.write(bytes.fromhex("302e020100300506032b657004220420")
                + open(KEYS[keyname or handle], "rb").read())
    with open(msg, "wb") as f:
        f.write(("agora-login:" + chal).encode())
    subprocess.run(["openssl", "pkeyutl", "-sign", "-rawin", "-inkey", der,
                    "-keyform", "DER", "-in", msg, "-out", sig], capture_output=True)
    s.sendall(b"auth: " + binascii.hexlify(open(sig, "rb").read()) + b"\r\n")
    time.sleep(0.5)
    return b"welcome" in drain(s)


def start(mode):
    env = dict(os.environ, AGORA_SERVE=mode)
    p = subprocess.Popen([BIN, "serve", str(PORT), "--store", STORE],
                         env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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


def fp_of(handle):
    out = run(["whoami", "--key", KEYS[handle], "--store", STORE]).stdout.decode().split()
    return out[-1] if out else ""


# --------------------------------------------------------------------------- CLI
def cli_checks():
    print("A/B/C/D — CLI")
    ops = os.path.join(STORE, "ops")
    os.makedirs(ops, exist_ok=True)

    def post_ops():
        return run(["post", "--as", "qix", "--key", KEYS["qix"], "--store", STORE,
                    "--board", "ops", "--subject", "t"], stdin=b"hello\n").returncode

    with open(os.path.join(ops, ".policy"), "w") as f:
        f.write("Admin\n")
    check(post_ops() != 0, "A: an unrecognised .policy ('Admin') refuses a non-admin")
    with open(os.path.join(ops, ".policy"), "w") as f:
        f.write("admin   # ops only\n")
    with open(os.path.join(ops, ".admins"), "w") as f:
        f.write("qix\n")
    check(post_ops() == 0, "A: 'admin  # comment' parses, and a listed admin may post")

    with open(os.path.join(ops, ".admins"), "w") as f:
        line = "#" * 62 + "\n"
        f.write(line * 66)                      # 4,158 bytes of comments...
        f.seek(4093)
        f.write("qixbert\npacman\n")            # ...cut so byte 4096 lands inside qixbert
    check(post_ops() != 0, "B: '.admins' cut mid-line at 4 KB does not admit a prefix handle")

    before = len(os.listdir(STORE))
    r = run(["post", "--as", "qix", "--key", KEYS["qix"], "--store", STORE, "--subject", "big"],
            stdin=b"x" * 70000)
    check(r.returncode != 0 and len(os.listdir(STORE)) == before,
          "C: a CLI body over 64 KB is refused, nothing stored")

    t0 = time.time()
    try:
        r = subprocess.run([BIN, "serve", "--store"], capture_output=True, timeout=5)
        check(r.returncode == 2 and time.time() - t0 < 4, "D: `serve --store` with no value exits 2")
    except subprocess.TimeoutExpired:
        check(False, "D: `serve --store` with no value exits 2 (it hung)")


# --------------------------------------------------------------------- poll only
def make_board():
    """701 posts, 700 of them with 200-byte subjects and 2 KB bodies: `list` is
    > 128 KB, and each `read` re-scanned every post before 1.8.1."""
    subj = "s" * 200
    body = "b" * 2048
    # Post 1 is tiny, so 500 pipelined `read 1` replies fit the 128 KB tx queue:
    # the readers must stay connected for the fairness check to mean anything.
    with open(os.path.join(STORE, "1.txt"), "w") as f:
        f.write("Subject: one\r\n\r\nhi\r\n")
    for i in range(2, 702):
        with open(os.path.join(STORE, "%d.txt" % i), "w") as f:
            f.write("Subject: %s %d\r\n\r\n%s\r\n" % (subj, i, body))


def poll_checks():
    print("E/F — poll fairness + big list")
    p = start("poll")
    if not p:
        check(False, "poll server started")
        return
    try:
        s = connect()
        s.sendall(b"list\r\n")
        out = b""
        s.settimeout(4)
        closed = False
        try:
            while True:
                d = s.recv(1 << 20)
                if not d:
                    closed = True
                    break
                out += d
        except OSError:
            pass
        rows = sum(1 for l in out.split(b"\r\n") if l[:1].isdigit())
        check(rows >= 700 and not closed, "F: a %d-byte `list` arrives whole (%d rows), session open" % (len(out), rows))
        s.close()

        stopflag = threading.Event()

        def attacker():
            a = socket.create_connection(("127.0.0.1", PORT), timeout=6)
            a.settimeout(0.05)
            burst = b"read 1\r\n" * 500
            while not stopflag.is_set():
                try:
                    a.sendall(burst)
                except OSError:
                    break
                try:
                    while a.recv(1 << 20):
                        pass
                except OSError:
                    pass
            a.close()

        threads = [threading.Thread(target=attacker, daemon=True) for _ in range(4)]
        for t in threads:
            t.start()
        time.sleep(0.5)
        v = connect()
        worst = 0.0
        for _ in range(15):
            t0 = time.time()
            v.sendall(b"x")
            v.settimeout(10)
            try:
                v.recv(64)
            except OSError:
                pass
            worst = max(worst, time.time() - t0)
            time.sleep(0.1)
        stopflag.set()
        v.close()
        check(worst < 1.0, "E: a bystander's echo stays prompt under 4 pipelining readers (worst %.0f ms)" % (worst * 1000))
    finally:
        stop(p)


# ------------------------------------------------------------------ both models
def door_checks(mode):
    print("G/H — door saves + play lock (%s)" % mode)
    shutil.rmtree(os.path.join(STORE, ".users", fp_of("qix"), "games"), ignore_errors=True)
    p = start(mode)
    if not p:
        check(False, "%s server started" % mode)
        return
    try:
        a = connect()
        check(login(a, "qix"), "%s: qix logs in" % mode)
        a.sendall(b"play port solo\r\n")
        time.sleep(0.6)
        drain(a)
        a.sendall(b"n\r\n")                     # next day -> Day 2
        time.sleep(0.6)
        check(b"Day 2/" in drain(a), "%s: in-game day advanced to 2" % mode)

        b = connect()
        check(login(b, "qix"), "%s: a second qix session logs in" % mode)
        b.sendall(b"play port solo\r\n")
        time.sleep(0.6)
        check(b"already playing" in drain(b), "H %s: the same game in a second session is refused" % mode)

        a.close()                               # drop WITHOUT quitting
        time.sleep(1.5)
        b.sendall(b"play port solo\r\n")
        time.sleep(0.8)
        check(b"Day 2/" in drain(b), "G %s: progress survived the dropped connection" % mode)
        b.sendall(b"q\r\n")
        time.sleep(0.3)
        b.close()
    finally:
        stop(p)


def pubkey_check():
    print("I — public key bound to its fingerprint")
    qdir = os.path.join(STORE, ".users", fp_of("qix"))
    pdir = os.path.join(STORE, ".users", fp_of("pac"))
    saved = open(os.path.join(qdir, "public_key.bin"), "rb").read()
    shutil.copy(os.path.join(pdir, "public_key.bin"), os.path.join(qdir, "public_key.bin"))
    p = start("poll")
    try:
        s = connect()
        check(not login(s, "qix", keyname="pac"),
              "I: pac's key copied over qix's public_key.bin does not log in as qix")
        s.close()
    finally:
        stop(p)
        with open(os.path.join(qdir, "public_key.bin"), "wb") as f:
            f.write(saved)


def main():
    if not os.path.exists(BIN):
        print("build first: cyrius build src/main.cyr build/agora")
        return 2
    shutil.rmtree(BASE, ignore_errors=True)
    os.makedirs(BASE)
    for h, k in KEYS.items():
        run(["keygen", "--key", k])
        run(["register", "--handle", h, "--key", k, "--store", STORE])
    try:
        cli_checks()
        make_board()
        poll_checks()
        door_checks("poll")
        door_checks("fork")
        pubkey_check()
    finally:
        shutil.rmtree(BASE, ignore_errors=True)
    if fails:
        print("FAIL — %d check(s): %s" % (len(fails), "; ".join(fails)))
        return 1
    print("OK — policy/admins fail closed, CLI limits, poll fairness + big list, "
          "disconnect saves, one-session play lock, pubkey bound to its fingerprint")
    return 0


if __name__ == "__main__":
    sys.exit(main())
