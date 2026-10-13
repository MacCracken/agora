#!/usr/bin/env python3
# 34-board-policy.py
#
# Why: 1.9.2 (ADR 0028). Until 1.9.2 the board modes `open` and `known` behaved
# identically — every logged-in user is registered — so an operator could set a
# mode and observe nothing; anonymous posting (ADR 0006's promised anon-allowed)
# did not exist; `.admins` granted rights by HANDLE, so a key re-registered under
# a new name left its old handle — and the admin rights on it — free for anyone to
# register (audit 1.8.1 I9); and operators edited `.policy` / `.admins` by hand.
# This drives all of it through the real CLI and the real server:
#
#   - `agora policy set|get` and `agora admins add|list|rm`;
#   - anon: an anonymous session posts, and the post is listed as [anon];
#   - known (members only): an anonymous session cannot enter, list or read,
#     `boards` shows "members only", a logged-in member can;
#   - admin by fingerprint: the admin posts; a registered non-admin cannot; and
#     after the admin's key re-registers as a new handle and SOMEONE ELSE takes the
#     old handle, the newcomer is not an admin and the key still is.
#
# Self-contained: its own keys + store under /tmp, its own servers, BOTH serve
# models. Requires openssl >= 3.0 (Ed25519 login). Success: "OK — ..." and exit 0.
#
# Usage: 34-board-policy.py [port]
#        AGORA_BIN=/path/to/agora 34-board-policy.py   (A/B an older build)

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
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2334
BASE = "/tmp/agora-policy-smoke-%d" % os.getpid()
STORE = BASE + "/bbs"
KEYS = {n: BASE + "/%s.key" % n for n in ("qix", "pac", "jst")}

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


def connect():
    s = socket.create_connection(("127.0.0.1", PORT), timeout=6)
    time.sleep(0.4)
    drain(s)
    return s


def say(s, line, t=0.5):
    s.sendall(line + b"\r\n")
    time.sleep(0.15)
    return drain(s, t)


def login(s, handle, keyname):
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
        f.write(bytes.fromhex("302e020100300506032b657004220420") + open(KEYS[keyname], "rb").read())
    with open(msg, "wb") as f:
        f.write(("agora-login:" + chal).encode())
    subprocess.run(["openssl", "pkeyutl", "-sign", "-rawin", "-inkey", der,
                    "-keyform", "DER", "-in", msg, "-out", sig], capture_output=True)
    s.sendall(b"auth: " + binascii.hexlify(open(sig, "rb").read()) + b"\r\n")
    time.sleep(0.5)
    return b"welcome" in drain(s)


def post(s, subject, body):
    """`post` → Subject → body → '.'; returns the server's reply to the commit."""
    first = say(s, b"post")
    if b"Subject:" not in first:
        return first
    say(s, subject)
    say(s, body)
    return say(s, b".", 0.8)


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


def setup():
    shutil.rmtree(BASE, ignore_errors=True)
    os.makedirs(STORE)
    for n in ("qix", "pac", "jst"):
        run("keygen", "--key", KEYS[n])
    run("register", "--handle", "qix", "--key", KEYS["qix"], "--store", STORE)
    run("register", "--handle", "pac", "--key", KEYS["pac"], "--store", STORE)


def cli_checks():
    print("A — the operator CLI")
    rc, out = run("policy", "set", "pub", "anon", "--store", STORE)
    check(rc == 0, "policy set pub anon")
    run("policy", "set", "mem", "known", "--store", STORE)
    run("policy", "set", "ops", "admin", "--store", STORE)
    rc, out = run("policy", "get", "mem", "--store", STORE)
    check(rc == 0 and out.strip() == "mem: known", "policy get mem → known (%r)" % out.strip())
    rc, out = run("policy", "get", "main", "--store", STORE)
    check("open (default: no .policy)" in out, "policy get main → the default")
    rc, _ = run("policy", "set", "pub", "wide-open", "--store", STORE)
    check(rc == 2, "an unknown mode is a usage error")
    rc, out = run("admins", "add", "ops", "qix", "--store", STORE)
    check(rc == 0 and out.startswith("added "), "admins add ops qix")
    # An older build has no CLI: write what an operator would by hand (and what
    # 1.9.2 writes), so the wire checks below still measure that build.
    for board, mode in (("pub", "anon"), ("mem", "known"), ("ops", "admin")):
        os.makedirs(STORE + "/" + board, exist_ok=True)
        if not os.path.exists(STORE + "/%s/.policy" % board):
            open(STORE + "/%s/.policy" % board, "w").write(mode + "\n")
    if not os.path.exists(STORE + "/ops/.admins"):
        fp = run("whoami", "--key", KEYS["qix"], "--store", STORE)[1].split()[-1]
        open(STORE + "/ops/.admins", "w").write(fp + "  # qix\n")
    admins = open(STORE + "/ops/.admins").read()
    check(admins.split()[0] != "qix" and len(admins.split()[0]) == 16,
          "the entry written is qix's fingerprint, not the handle (%r)" % admins.strip())
    rc, out = run("admins", "list", "ops", "--store", STORE)
    check(rc == 0 and "qix" in out, "admins list names qix beside the fingerprint")
    rc, _ = run("admins", "add", "ops", "nobody", "--store", STORE)
    check(rc == 1, "admins add of an unknown handle fails")


def wire_checks(mode):
    print("B — the modes on the wire (%s)" % mode)
    p = start(mode)
    if not p:
        check(False, "%s server started" % mode)
        return
    try:
        a = connect()                                  # anonymous
        out = say(a, b"boards")
        check(b"mem" in out and b"members only" in out, "%s: `boards` shows mem as members only" % mode)
        check(b"members only" in say(a, b"enter mem"), "%s: anonymous cannot enter a members-only board" % mode)
        say(a, b"enter pub")
        out = post(a, b"anon hello", b"posted without an account")
        check(b"posted as #" in out, "%s: anonymous post on an anon board (%r)" % (mode, out[-60:]))
        out = say(a, b"list")
        check(b"[anon]" in out and b"anon hello" in out, "%s: the anonymous post is listed as [anon]" % mode)
        say(a, b"leave")
        out = post(a, b"x", b"y")
        check(b"auth required" in out, "%s: an open board still refuses anonymous posts" % mode)
        a.close()

        q = connect()
        check(login(q, "qix", "qix"), "%s: qix logs in" % mode)
        check(b"entered mem" in say(q, b"enter mem"), "%s: a member enters a members-only board" % mode)
        check(b"members only" not in say(q, b"list"), "%s: a member lists it" % mode)
        say(q, b"leave")
        say(q, b"enter ops")
        out = post(q, b"from the admin", b"by fingerprint")
        check(b"posted as #" in out, "%s: the fingerprint admin posts on ops" % mode)
        q.close()

        c = connect()
        check(login(c, "pac", "pac"), "%s: pac logs in" % mode)
        say(c, b"enter ops")
        check(b"denied" in say(c, b"post"), "%s: a registered non-admin cannot post on ops" % mode)
        c.close()
    finally:
        stop(p)


def rebind_checks():
    print("C — admin rights follow the key, not the handle (audit 1.8.1 I9)")
    run("register", "--handle", "qixnew", "--key", KEYS["qix"], "--store", STORE)   # qix's key renames
    rc, out = run("register", "--handle", "qix", "--key", KEYS["jst"], "--store", STORE)
    check(rc == 0, "someone else registers the freed handle qix")
    p = start("poll")
    try:
        j = connect()
        check(login(j, "qix", "jst"), "the newcomer logs in as qix")
        say(j, b"enter ops")
        check(b"denied" in say(j, b"post"), "the new qix is NOT an admin of ops")
        j.close()
        q = connect()
        check(login(q, "qixnew", "qix"), "the original key logs in as qixnew")
        say(q, b"enter ops")
        check(b"Subject:" in say(q, b"post"), "the original key is still an admin of ops")
        q.close()
    finally:
        stop(p)


def main():
    if not os.path.exists(BIN):
        print("build first: cyrius build src/main.cyr build/agora")
        return 2
    try:
        setup()
        cli_checks()
        for mode in ("poll", "fork"):
            wire_checks(mode)
        rebind_checks()
    finally:
        shutil.rmtree(BASE, ignore_errors=True)
    if fails:
        print("FAIL — %d check(s): %s" % (len(fails), "; ".join(fails)))
        return 1
    print("OK — every board mode means something, and admin rights follow the key")
    return 0


if __name__ == "__main__":
    sys.exit(main())
