#!/usr/bin/env python3
# 41-cross-board.py
#
# Why: 1.13.1 (roadmap § 1.13.1). Two protocol limits from M5. A reply could only
# name a parent on its own board (ADR 0005); since ADR 0035 `reply <board>/<id>`
# writes `Reply-To: <board>/<id>`, the parent board's reply index records it, and
# `read <board>/<id>` follows it. And egress sanitizing turned every post's ESC
# into '?' (ADR 0024); since ADR 0036 an operator can flag a board raw for ANSI
# art, whose colour and cursor moves then reach the reader, and nothing else does.
# This drives the real server, both serve models, with raw bytes:
#
#   A  on tech, `reply pub/1` derives the parent's subject and posts on tech;
#   B  `read pub/1` from tech lists the reply as `1` (it is on the reader's board),
#      `read 1` on pub lists it as `tech/1`, and `read tech/1` shows `Reply-To: 1`;
#   C  `agora post --reply-to pub/1` from the CLI is listed too (`ops/1, tech/1`);
#   D  after `agora policy set ops known`, an anonymous reader of pub/1 does not
#      see `ops/1` and cannot `read ops/1`; a member sees both replies;
#   E  with pub's `.replies/` deleted, the next `serve` rebuilds it, and both
#      replies from the other boards are listed again;
#   F  after `agora raw set art on`, a post's SGR reaches the reader whole and its
#      OSC arrives as text; the same body on pub loses its ESC; `raw get` reports
#      it; after `raw set art off` the art's ESC shows as '?'.
#
# Self-contained: its own store under /tmp, its own servers. Success: "OK — ..."
# and exit 0. Against a 1.13.0 build A–F fail.
#
# Usage: 41-cross-board.py [port]
#        AGORA_BIN=/path/to/agora 41-cross-board.py   (A/B an older build)

import binascii
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BIN = os.environ.get("AGORA_BIN", os.path.join(ROOT, "build", "agora"))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2341
BASE = "/tmp/agora-xboard-smoke-%d" % os.getpid()
STORE = BASE + "/bbs"
KEY = BASE + "/qix.key"
ART = b"\x1b[31mred\x1b[0m and \x1b]0;title\x07 x"

fails = []


def check(cond, what):
    print("  %s  %s" % ("ok  " if cond else "FAIL", what))
    if not cond:
        fails.append(what)


def run(*args, stdin=None):
    r = subprocess.run([BIN] + list(args), input=stdin, capture_output=True, timeout=20)
    return r.returncode, r.stdout.decode(errors="replace")


def drain(s, t=0.5):
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


def until(s, needle, t):
    out = b""
    end = time.time() + t
    s.settimeout(0.1)
    while needle not in out and time.time() < end:
        try:
            d = s.recv(65536)
            if not d:
                break
            out += d
        except OSError:
            pass
    return out


def connect():
    s = socket.create_connection(("127.0.0.1", PORT), timeout=6)
    until(s, b"> ", 3.0)
    return s


def say(s, line, t=0.5):
    s.sendall(line + b"\r\n")
    time.sleep(0.15)
    return drain(s, t)


def login(s):
    s.sendall(b"login qix\r\n")
    out = until(s, b"auth:", 5.0)
    chal = None
    for line in out.split(b"\r\n"):
        if b"challenge:" in line:
            chal = line.split(b"challenge:")[1].strip().decode()
    if not chal:
        return False
    tmp = tempfile.mkdtemp(dir=BASE)
    der, msg, sig = (os.path.join(tmp, n) for n in ("k.der", "m", "s"))
    with open(der, "wb") as f:
        f.write(bytes.fromhex("302e020100300506032b657004220420") + open(KEY, "rb").read())
    with open(msg, "wb") as f:
        f.write(("agora-login:" + chal).encode())
    subprocess.run(["openssl", "pkeyutl", "-sign", "-rawin", "-inkey", der,
                    "-keyform", "DER", "-in", msg, "-out", sig], capture_output=True)
    s.sendall(b"auth: " + binascii.hexlify(open(sig, "rb").read()) + b"\r\n")
    return b"welcome" in until(s, b"welcome", 5.0)


def post(s, subject, body):
    first = say(s, b"post")
    if b"Subject:" not in first:
        return first
    say(s, subject)
    say(s, body)
    return commit(s)


def commit(s):
    """'.' ends a post. A board's first reply builds its reply index, which ends
    with a sync(2) that can take seconds on a busy host: wait for the answer."""
    s.sendall(b".\r\n")
    out = until(s, b"posted as #", 15.0)
    return out + until(s, b"> ", 2.0)


def start(mode):
    p = subprocess.Popen([BIN, "serve", str(PORT), "--store", STORE],
                         env=dict(os.environ, AGORA_SERVE=mode),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
    for _ in range(60):
        try:
            socket.create_connection(("127.0.0.1", PORT), timeout=1).close()
            time.sleep(0.2)
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
    try:
        os.killpg(p.pid, signal.SIGKILL)
    except OSError:
        pass
    time.sleep(0.3)


def replies(out):
    for line in out.split(b"\r\n"):
        if line.startswith(b"Replies: "):
            return line[len(b"Replies: "):].decode()
    return ""


def checks(mode):
    p = start(mode)
    if not p:
        check(False, "%s server started" % mode)
        return
    try:
        s = connect()
        check(login(s), "%s: qix logs in" % mode)
        say(s, b"enter pub")
        post(s, b"orig", b"the parent")
        say(s, b"enter tech")
        out = say(s, b"reply pub/1")
        check(b"Subject: Re: orig" in out, "%s A: reply pub/1 derives the parent's subject" % mode)
        say(s, b"from tech")
        out = commit(s)
        check(b"posted as #1" in out, "%s A: the reply is posted on tech" % mode)
        out = say(s, b"read pub/1")
        check(b"the parent" in out and replies(out) == "1", "%s B: read pub/1 from tech lists 1 (%r)" % (mode, replies(out)))
        say(s, b"enter pub")
        out = say(s, b"read 1")
        check(replies(out) == "tech/1", "%s B: read 1 on pub lists tech/1 (%r)" % (mode, replies(out)))
        out = say(s, b"read tech/1")
        check(b"Reply-To: 1\r\n" in out and b"from tech" in out, "%s B: read tech/1 shows its parent as 1" % mode)
        s.close()

        rc, _ = run("post", "--store", STORE, "--board", "ops", "--reply-to", "pub/1",
                    "--as", "qix", "--key", KEY, stdin=b"from the CLI\n")
        check(rc == 0, "%s C: agora post --reply-to pub/1" % mode)
        s = connect()
        say(s, b"enter pub")
        out = say(s, b"read 1")
        check(replies(out) == "ops/1, tech/1", "%s C: both other boards' replies are listed (%r)" % (mode, replies(out)))
        s.close()

        run("policy", "set", "ops", "known", "--store", STORE)
        s = connect()
        say(s, b"enter pub")
        out = say(s, b"read 1")
        check(replies(out) == "tech/1", "%s D: an anonymous reader does not see ops/1 (%r)" % (mode, replies(out)))
        out = say(s, b"read ops/1")
        check(b"members only" in out, "%s D: an anonymous read of ops/1 is refused" % mode)
        s.close()
        s = connect()
        login(s)
        say(s, b"enter pub")
        out = say(s, b"read 1")
        check(replies(out) == "ops/1, tech/1", "%s D: a member sees both (%r)" % (mode, replies(out)))
        s.close()
    finally:
        stop(p)

    shutil.rmtree(STORE + "/pub/.replies", ignore_errors=True)
    p = start(mode)
    try:
        s = connect()
        login(s)
        say(s, b"enter pub")
        out = say(s, b"read 1")
        check(replies(out) == "ops/1, tech/1", "%s E: a rebuilt index lists both again (%r)" % (mode, replies(out)))
        say(s, b"enter art")
        run("raw", "set", "art", "on", "--store", STORE)
        post(s, b"art", ART)
        out = say(s, b"read 1")
        check(b"\x1b[31mred\x1b[0m" in out, "%s F: a raw board's colour reaches the reader" % mode)
        check(b"\x1b]" not in out and b"?]0;title x" in out, "%s F: its OSC arrives as text" % mode)
        say(s, b"enter pub")
        post(s, b"plain", ART)
        out = say(s, b"read 2")
        check(b"\x1b" not in out.split(b"Subject: plain")[-1], "%s F: on pub the same body loses its ESC" % mode)
        rc, txt = run("raw", "get", "art", "--store", STORE)
        check(rc == 0 and "art: on" in txt, "%s F: raw get reports it" % mode)
        run("raw", "set", "art", "off", "--store", STORE)
        say(s, b"enter art")
        out = say(s, b"read 1")
        check(b"\x1b[31m" not in out and b"?[31mred" in out, "%s F: after raw set off the ESC shows as ?" % mode)
        s.close()
    finally:
        stop(p)


def main():
    if not os.path.exists(BIN):
        print("build first: cyrius build src/main.cyr build/agora")
        return 2
    if shutil.which("openssl") is None:
        print("SKIP — needs openssl (the login signature)")
        return 0
    try:
        for mode in ("poll", "fork"):
            print("— %s" % mode)
            shutil.rmtree(BASE, ignore_errors=True)
            os.makedirs(STORE)
            run("keygen", "--key", KEY)
            run("register", "--handle", "qix", "--key", KEY, "--store", STORE)
            checks(mode)
    finally:
        shutil.rmtree(BASE, ignore_errors=True)
    if fails:
        print("FAIL — %d check(s): %s" % (len(fails), "; ".join(fails)))
        return 1
    print("OK — replies cross boards, and a raw board carries ANSI art and nothing else")
    return 0


if __name__ == "__main__":
    sys.exit(main())
