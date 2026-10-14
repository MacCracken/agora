#!/usr/bin/env python3
# 38-door-content.py
#
# Why: 1.12.0 (roadmap § 1.12.0) — the door content release. This drives the
# real server, both serve models, through each change a player can see:
#
#   A  the daily ration (ADR 0032; audit 1.8.1 I4): under `--door-days 2` a
#      Solo Port Authority run ends two days, is refused the third with a
#      message, shows what is left, and is still refused after a save and
#      re-entry; a Practice run is not rationed; `--door-days 0` lifts the cap;
#   B  Ashes ages (audit 1.8.1 I6): a 1.11 (v3) world in which one player holds
#      all twelve provinces is upgraded in place; the next turn ends the age in
#      that player's name; the victor's next visit claims it ("THE AGE IS
#      YOURS") and posts an Imperator row to `scores ashes`; a player who saw
#      the old age is founded in the new one with the news, and the victor can
#      found again. Before 1.12.0 the world stayed closed for good and the
#      victor's win never reached the leaderboard;
#   C  Decode/Words takes real words the answer pool lacks ("pizza") and still
#      refuses non-words ("roate");
#   D  the Olympiad: the market hires a runner, the stadion has its own venue,
#      words and labels, and the first meet fields four.
#
# Self-contained: its own store under /tmp, its own servers. Success: "OK — ..."
# and exit 0. Against a 1.11.1 build A, B, C and D fail.
#
# Usage: 38-door-content.py [port]
#        AGORA_BIN=/path/to/agora 38-door-content.py   (A/B an older build)

import binascii
import os
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BIN = os.environ.get("AGORA_BIN", os.path.join(ROOT, "build", "agora"))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2338
BASE = "/tmp/agora-content-smoke-%d" % os.getpid()
STORE = BASE + "/bbs"
HANDLES = ("qix", "pac", "zax")
KEYS = {h: BASE + "/" + h + ".key" for h in HANDLES}

# Ashes' snapshot geometry (src/ashes.cyr): a header of 4 words, 12 provinces x
# 2, the order count + 64 orders x 4, 32 pacts x 3 = 381 words at v3; v4 adds 3.
ASH_V3_WORDS = 4 + 12 * 2 + 1 + 64 * 4 + 32 * 3
ASH_V4_WORDS = ASH_V3_WORDS + 3
DAY_S = 86400

fails = []


def check(cond, what):
    print("  %s  %s" % ("ok  " if cond else "FAIL", what))
    if not cond:
        fails.append(what)


def run(args, timeout=20):
    return subprocess.run([BIN] + args, capture_output=True, timeout=timeout)


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


def cmd(s, line, t=0.6):
    s.sendall(line.encode() + b"\r\n")
    return drain(s, t)


def login(s, handle):
    """Ed25519 challenge/response with the handle's key."""
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
        f.write(bytes.fromhex("302e020100300506032b657004220420") + open(KEYS[handle], "rb").read())
    with open(msg, "wb") as f:
        f.write(("agora-login:" + chal).encode())
    subprocess.run(["openssl", "pkeyutl", "-sign", "-rawin", "-inkey", der,
                    "-keyform", "DER", "-in", msg, "-out", sig], capture_output=True)
    s.sendall(b"auth: " + binascii.hexlify(open(sig, "rb").read()) + b"\r\n")
    time.sleep(0.5)
    return b"welcome" in drain(s)


def session(handle):
    s = connect()
    check(login(s, handle), "%s logs in" % handle)
    return s


def start(mode, days=None):
    args = [BIN, "serve", str(PORT), "--store", STORE]
    if days is not None:
        args += ["--door-days", str(days)]
    p = subprocess.Popen(args, env=dict(os.environ, AGORA_SERVE=mode),
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


def fp_i64(handle):
    """The handle's fingerprint as Ashes stores it (hex16 -> a signed i64)."""
    out = run(["whoami", "--key", KEYS[handle], "--store", STORE]).stdout.decode().split()
    v = int(out[-1], 16)
    return v - (1 << 64) if v >= (1 << 63) else v


def setup():
    shutil.rmtree(BASE, ignore_errors=True)
    os.makedirs(BASE)
    for h in HANDLES:
        run(["keygen", "--key", KEYS[h]])
        run(["register", "--handle", h, "--key", KEYS[h], "--store", STORE])


# ------------------------------------------------------------------ A: the ration
def ration_checks(mode):
    print("A — the daily ration (%s)" % mode)
    shutil.rmtree(os.path.join(STORE, ".users"), ignore_errors=True)
    setup_users_only()
    p = start(mode, 2)
    if not p:
        check(False, "%s server started" % mode)
        return
    try:
        s = session("qix")
        f = cmd(s, "play port solo")
        check(b"Day 1/" in f and b"2 more today" in f, "A %s: a Solo run shows today's two days" % mode)
        cmd(s, "n")
        f = cmd(s, "n")
        check(b"Day 3/" in f and b"0 more today" in f, "A %s: two days ended" % mode)
        f = cmd(s, "n")
        check(b"Day 3/" in f and b"picks up again tomorrow" in f, "A %s: the third is refused, and says so" % mode)
        cmd(s, "q")
        f = cmd(s, "play port solo")
        f += cmd(s, "n")
        check(b"Day 3/" in f and b"tomorrow" in f, "A %s: still refused after a save and re-entry" % mode)
        cmd(s, "q")
        f = cmd(s, "play port")
        cmd(s, "n")
        cmd(s, "n")
        f = cmd(s, "n")
        check(b"Day 4/" in f and b"more today" not in f, "A %s: a Practice run is not rationed" % mode)
        cmd(s, "q")
        s.close()
    finally:
        stop(p)
    p = start(mode, 0)
    if not p:
        check(False, "%s server (--door-days 0) started" % mode)
        return
    try:
        s = session("qix")
        cmd(s, "play port solo")
        f = cmd(s, "n")
        check(b"Day 4/" in f and b"more today" not in f, "A %s: --door-days 0 lifts the cap" % mode)
        cmd(s, "q")
        s.close()
    finally:
        stop(p)


def setup_users_only():
    """The games tree is per user; a fresh one for each model's run."""
    for h in HANDLES:
        if not os.path.exists(KEYS[h]):
            run(["keygen", "--key", KEYS[h]])
        run(["register", "--handle", h, "--key", KEYS[h], "--store", STORE])


# ------------------------------------------------------------------ B: Ashes ages
def ash_world_path():
    return os.path.join(STORE, ".games", "ashes", "world", "snapshot")


def write_v3_world(owner, last_window):
    """A 1.11-format world: every province held by `owner`, the next turn due."""
    words = [0] * ASH_V3_WORDS
    words[0] = 3                      # version
    words[1] = 1453                   # seed
    words[2] = 5                      # turn
    words[3] = last_window
    for t in range(12):
        words[4 + t * 2] = owner
        words[4 + t * 2 + 1] = 10
    d = os.path.dirname(ash_world_path())
    os.makedirs(d, exist_ok=True)
    with open(ash_world_path(), "wb") as f:
        f.write(struct.pack("<%dq" % len(words), *words))


def world_words():
    data = open(ash_world_path(), "rb").read()
    return list(struct.unpack("<%dq" % (len(data) // 8), data))


def set_window(last_window):
    w = world_words()
    w[3] = last_window
    with open(ash_world_path(), "wb") as f:
        f.write(struct.pack("<%dq" % len(w), *w))


def ashes_checks(mode):
    print("B — Ashes ages (%s)" % mode)
    shutil.rmtree(os.path.join(STORE, ".games"), ignore_errors=True)
    shutil.rmtree(os.path.join(STORE, ".users"), ignore_errors=True)
    setup_users_only()
    now = int(time.time()) // DAY_S
    write_v3_world(fp_i64("qix"), now)        # nothing due yet
    p = start(mode)
    if not p:
        check(False, "%s server started" % mode)
        return
    try:
        # zax looks at the old age (the map is full, so no founding) and leaves
        z = session("zax")
        f = cmd(z, "play ashes")
        check(b"12/12" not in f and b"ASHES OF EMPIRE" in f, "B %s: zax sees the dominated age" % mode)
        cmd(z, "quit")
        z.close()
        time.sleep(0.3)
        w = world_words()
        check(len(w) == ASH_V4_WORDS and w[0] == 4, "B %s: the v3 world was upgraded in place to v4" % mode)
        check(w[4] == fp_i64("qix"), "B %s: the upgrade kept the map" % mode)
        set_window(now - 1)                  # the turn comes round
        q = session("qix")
        f = cmd(q, "play ashes")
        check(b"THE AGE IS YOURS" in f, "B %s: the victor's next visit claims the age" % mode)
        cmd(q, "")
        b = cmd(q, "scores ashes")
        check(b"qix" in b and b"Imperator" in b, "B %s: the claim posts an Imperator row" % mode)
        w = world_words()
        check(len(w) == ASH_V4_WORDS and w[ASH_V3_WORDS] == 2 and w[ASH_V3_WORDS + 1] == 0,
              "B %s: age 2, the laurel claimed" % mode)
        f = cmd(q, "play ashes")
        check(b"founded your empire" in f and b"THE AGE IS YOURS" not in f,
              "B %s: the laurel is claimed once; the victor founds again" % mode)
        cmd(q, "quit")
        q.close()
        z = session("zax")
        f = cmd(z, "play ashes")
        check(b"a new age has dawned" in f and b"founded your empire" in f,
              "B %s: a player who saw the old age is founded in the new one, with the news" % mode)
        cmd(z, "quit")
        z.close()
    finally:
        stop(p)


# ------------------------------------------------------------------ C, D: Decode, Olympiad
def decode_olympiad_checks(mode):
    print("C/D — Decode words, Olympiad events (%s)" % mode)
    p = start(mode)
    if not p:
        check(False, "%s server started" % mode)
        return
    try:
        s = connect()
        cmd(s, "play decode")
        cmd(s, "w")
        f = cmd(s, "pizza")
        check(b"Not in the word list" not in f, "C %s: 'pizza' is a word" % mode)
        f = cmd(s, "roate")
        check(b"Not in the word list" in f, "C %s: 'roate' is not" % mode)
        cmd(s, "q")
        f = cmd(s, "play olympiad")
        f = cmd(s, "h")
        check(b"THE MARKET" in f and b"a runner for the stadion -- 90 denarii" in f,
              "D %s: the market lists the events" % mode)
        f = cmd(s, "3")
        check(b"Hired Astylos of Croton" in f and b"Pac 8 Wnd 8 Srt 8 Grt 8" in f,
              "D %s: a runner hired and selected" % mode)
        check(b"[S]witch competitor" in f, "D %s: the stable can switch" % mode)
        f = cmd(s, "e")
        check(b"THE STADIUM" in f and b"drop the rope" in f and b"the practice track at Elis" in f,
              "D %s: the stadion has its own venue and words" % mode)
        check(b"Lane 4" in f and b"Lane 5" not in f, "D %s: the first meet fields four" % mode)
        f = cmd(s, "")
        check(b"THE FINISH" in f, "D %s: the race resolves" % mode)
        cmd(s, "")
        f = cmd(s, "s")     # (the runner may have won: the venue is not fixed, the labels are)
        check(b"> Blue the Boreads" in f and b"train Spd/Sta/Hnd/Nrv" in f,
              "D %s: switching back to the chariot team" % mode)
        cmd(s, "q")
        s.close()
    finally:
        stop(p)


def main():
    if not os.path.exists(BIN):
        print("build first: cyrius build src/main.cyr build/agora")
        return 1
    setup()
    try:
        for mode in ("fork", "poll"):
            ration_checks(mode)
            ashes_checks(mode)
            decode_olympiad_checks(mode)
    finally:
        shutil.rmtree(BASE, ignore_errors=True)
    if fails:
        print("FAIL — %d check(s): %s" % (len(fails), "; ".join(fails)))
        return 1
    print("OK — 1.12.0 door content: the daily ration, Ashes ages, Decode words, Olympiad events")
    return 0


if __name__ == "__main__":
    sys.exit(main())
