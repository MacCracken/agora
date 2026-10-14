#!/usr/bin/env python3
# 39-provably-fair.py
#
# Why: 1.12.1 (roadmap § 1.12.1, ADR 0033) — every wager draw comes from a
# server seed whose SHA-256 the player sees before betting, and every
# real-stakes wager is written to an append-only audit log, so the house's dice
# can be checked after the fact. This drives the real server, both serve
# models:
#
#   A  the betting screens (the cantina wheel, the back-alley bones, the
#      Olympiad book) show the seed commitment before the first bet;
#   B  Solo bets at all three are W lines in <store>/.games/wagers, each with
#      its draws;
#   C  `fair` shows the same commitment; `fair reveal` reveals a seed that
#      hashes to it, and writes the R line; `fair seed <text>` sets the client
#      seed and refuses a bad one;
#   D  a seed still unrevealed when the player disconnects is revealed by the
#      close path;
#   E  an anonymous Practice bet leaves no line;
#   F  scripts/verify-wagers.py — Python's own SHA-256, none of agora's code —
#      verifies every logged draw, and rejects a log with one draw altered.
#
# Self-contained: its own store under /tmp, its own servers. Success: "OK — ..."
# and exit 0. Against a 1.12.0 build every check fails but the two logins (30 of 32).
#
# Usage: 39-provably-fair.py [port]
#        AGORA_BIN=/path/to/agora 39-provably-fair.py   (A/B an older build)

import binascii
import hashlib
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BIN = os.environ.get("AGORA_BIN", os.path.join(ROOT, "build", "agora"))
VERIFY = os.path.join(ROOT, "scripts", "verify-wagers.py")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2339
BASE = "/tmp/agora-fair-smoke-%d" % os.getpid()
STORE = BASE + "/bbs"
KEY = BASE + "/qix.key"
LOG = STORE + "/.games/wagers"

fails = []


def check(cond, what):
    print("  %s  %s" % ("ok  " if cond else "FAIL", what))
    if not cond:
        fails.append(what)


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


def cmd(s, line):
    s.sendall(line.encode() + b"\r\n")
    return drain(s).decode(errors="replace")


def login(s):
    out = cmd(s, "login qix")
    m = re.search(r"challenge:\s*([0-9a-f]+)", out)
    if not m:
        return False
    tmp = tempfile.mkdtemp(dir=BASE)
    der, msg, sig = (os.path.join(tmp, n) for n in ("k.der", "m", "s"))
    with open(der, "wb") as f:
        f.write(bytes.fromhex("302e020100300506032b657004220420") + open(KEY, "rb").read())
    with open(msg, "wb") as f:
        f.write(("agora-login:" + m.group(1)).encode())
    subprocess.run(["openssl", "pkeyutl", "-sign", "-rawin", "-inkey", der,
                    "-keyform", "DER", "-in", msg, "-out", sig], capture_output=True)
    return "welcome" in cmd(s, "auth: " + binascii.hexlify(open(sig, "rb").read()).decode())


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
    time.sleep(0.4)


def lines(kind):
    if not os.path.exists(LOG):
        return []
    return [l.split("\t") for l in open(LOG).read().splitlines() if l.startswith(kind + "\t")]


def shown(frame):
    m = re.search(r"seed commitment ([0-9a-f]{16})\.\.\.", frame)
    return m.group(1) if m else None


def verify(path):
    r = subprocess.run([sys.executable, VERIFY, path], capture_output=True, text=True)
    return r.returncode, r.stdout


def run(mode):
    print("A-F — provably fair wagers (%s)" % mode)
    shutil.rmtree(os.path.join(STORE, ".games"), ignore_errors=True)
    shutil.rmtree(os.path.join(STORE, ".users"), ignore_errors=True)
    subprocess.run([BIN, "register", "--handle", "qix", "--key", KEY, "--store", STORE], capture_output=True)
    p = start(mode)
    if not p:
        check(False, "%s server started" % mode)
        return
    try:
        s = connect()
        check(login(s), "%s: qix logs in" % mode)
        cmd(s, "play port solo")
        f = cmd(s, "c")
        first = shown(f)
        check(first is not None, "A %s: the cantina shows the seed commitment before a bet" % mode)
        first = first or "(none shown)"
        for bet in ("10 1", "10 2", "10 3"):
            cmd(s, bet)
        cmd(s, "x")
        cmd(s, "q")
        cmd(s, "play smuggler solo")
        f = cmd(s, "d")
        check(shown(f) is not None and shown(f) == first, "A %s: the bones show the same commitment" % mode)
        cmd(s, "10 1")
        cmd(s, "x")
        cmd(s, "q")
        cmd(s, "play olympiad solo")
        f = cmd(s, "e")
        check(shown(f) is not None and shown(f) == first, "A %s: the book shows it too" % mode)
        cmd(s, "2 20")
        cmd(s, "")
        cmd(s, "")
        cmd(s, "q")
        w = lines("W")
        games = sorted(set(x[3] for x in w))
        check(len(w) == 5 and games == ["olympiad", "port", "smuggler"],
              "B %s: five W lines across the three tables (%s)" % (mode, ",".join(games)))
        check(w and all(x[4].startswith(first) for x in w), "B %s: each names the commitment the player saw" % mode)
        book = [x for x in w if x[3] == "olympiad"]
        check(book and len(book[0][7].split(",")) == 4, "B %s: the book's line carries the race's four draws" % mode)
        f = cmd(s, "fair")
        check(("commitment  " + first) in f, "C %s: `fair` shows the commitment" % mode)
        r = cmd(s, "fair reveal")
        m = re.search(r"seed you bet on was:\s*([0-9a-f]{64})", r)
        seed = m.group(1) if m else ""
        check(hashlib.sha256(seed.encode()).hexdigest().startswith(first),
              "C %s: the revealed seed hashes to the commitment shown before the bets" % mode)
        rl = lines("R")
        check(len(rl) == 1 and rl[0][4] == seed, "C %s: the reveal is an R line" % mode)
        check("a client seed is" in cmd(s, "fair seed no:colons"), "C %s: a bad client seed is refused" % mode)
        f = cmd(s, "fair seed qix-arcade")
        check("client seed qix-arcade" in f, "C %s: `fair seed` sets the client seed" % mode)
        cmd(s, "play port solo")
        cmd(s, "c")
        cmd(s, "10 1")
        cmd(s, "x")
        cmd(s, "q")
        s.close()                                   # leave with an unrevealed seed
        time.sleep(1.2)
        rl = lines("R")
        check(len(rl) == 2 and rl[1][5] == "qix-arcade",
              "D %s: the close path revealed the last seed (with the player's client seed)" % mode)
        a = connect()
        cmd(a, "play port")
        cmd(a, "c")
        cmd(a, "10 1")
        cmd(a, "x")
        cmd(a, "q")
        a.close()
        time.sleep(0.5)
        check(len(lines("W")) == 6, "E %s: an anonymous Practice bet left no line" % mode)
        rc, out = verify(LOG)
        check(rc == 0 and "6 wager(s) verified" in out and " 0 pending" in out,
              "F %s: the verifier checks every logged draw (%s)" % (mode, out.strip()))
        if not os.path.exists(LOG):
            check(False, "F %s: one altered draw is caught (there is no log to alter)" % mode)
            return
        bad = BASE + "/tampered"
        rows = open(LOG).read().splitlines()
        for i, row in enumerate(rows):
            cols = row.split("\t")
            if cols[0] == "W" and cols[7] != "-":
                n, r0 = cols[7].split(",")[0].split(":")
                cols[7] = ",".join(["%s:%d" % (n, (int(r0) + 1) % int(n))] + cols[7].split(",")[1:])
                rows[i] = "\t".join(cols)
                break
        open(bad, "w").write("\n".join(rows) + "\n")
        rc, out = verify(bad)
        check(rc == 1 and "is not" in out, "F %s: one altered draw is caught" % mode)
    finally:
        stop(p)


def main():
    if not os.path.exists(BIN):
        print("build first: cyrius build src/main.cyr build/agora")
        return 1
    shutil.rmtree(BASE, ignore_errors=True)
    os.makedirs(BASE)
    subprocess.run([BIN, "keygen", "--key", KEY], capture_output=True)
    try:
        for mode in ("fork", "poll"):
            run(mode)
    finally:
        shutil.rmtree(BASE, ignore_errors=True)
    if fails:
        print("FAIL — %d check(s): %s" % (len(fails), "; ".join(fails)))
        return 1
    print("OK — provably fair wagers: committed seeds, the audit log, reveals on demand and on close, verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
