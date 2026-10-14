#!/usr/bin/env python3
# 37-descent-state.py
#
# Why: 1.11.0 (roadmap § 1.11.0, ADR 0031) — a Descent visit is a session state,
# the serve loops wait on readiness, the return resyncs the telnet options, and
# fork children leave with their parent. A 1.10.1 build fails 11 of its 21 checks
# (A, E, F, G, I); the rest (B, C, D, H) pin behaviour 1.10.1 already had, which
# 1.11.0 rebuilt on the new session state:
#
#   A  poll: while one session is in the MUD, another is answered at once (it
#      used to wait for the whole visit); likewise while one dials an endpoint
#      that never answers (it used to block the sweep 4 s), and the dialler is
#      told "not answering" within the 4 s deadline;
#   B  the bytes pipelined behind `descent` reach the MUD first;
#   C  the MUD's passphrase echo dance (WILL ECHO / WONT ECHO) and the return:
#      agora takes echo back exactly once (no doubled, no missing echo);
#   D  shutdown during a visit: the player is told, the server exits 0 at once;
#   E  AGORA_SERVE=epoll (or a typo) is refused, exit 2 — it used to mean poll;
#   F  poll accepts are no longer paced: 200 sequential connections in well
#      under the 4 s the 20 ms sweep imposed;
#   G  fork: a clean shutdown tells the children (goodbye, exit in well under
#      the 5 s grace window), and a SIGKILLed parent takes its child with it
#      (PR_SET_PDEATHSIG) instead of leaving an orphan;
#   H  fork: a visit and the return work as under poll;
#   I  (when inetutils `telnet` is installed) a REAL client in a 40x24 pty keeps
#      its window width and its LINEMODE echo arrangement across a visit: `read`
#      still wraps to 39 columns afterwards, and a half-typed line is visible —
#      1.10.1 lost the width for the rest of the session and left LINEMODE
#      clients typing blind.
#
# Self-contained: its own store and keys under /tmp, its own servers, and a fake
# MUD (a few lines of Python: a name prompt, a passphrase behind WILL ECHO, a
# `quit`) — the real Yeoman's Descent is exercised by smoke 20. Needs openssl
# (Ed25519 login signing). Success: "OK — ..." and exit 0.
#
# Usage: 37-descent-state.py [port]
#        AGORA_BIN=/path/to/agora 37-descent-state.py   (A/B an older build)

import binascii
import fcntl
import os
import pty
import re
import select
import shutil
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import termios
import threading
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BIN = os.environ.get("AGORA_BIN", os.path.join(ROOT, "build", "agora"))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2337
MUDPORT = PORT + 1000
BASE = "/tmp/agora-descent-state-%d" % os.getpid()
STORE, KEYS = BASE + "/bbs", BASE + "/keys"
PKCS8 = bytes.fromhex("302e020100300506032b657004220420")
IAC, WILL, WONT = 255, 251, 252

fails = []


def check(cond, what):
    print("  %s  %s" % ("ok  " if cond else "FAIL", what))
    if not cond:
        fails.append(what)


# --- a fake MUD -------------------------------------------------------------
class FakeMud:
    """Name prompt, a passphrase behind IAC WILL ECHO, then IAC WONT ECHO and a
    room; `quit` hangs up. Records everything it receives."""

    def __init__(self, port):
        self.got = b""
        self.lst = socket.socket()
        self.lst.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.lst.bind(("127.0.0.1", port))
        self.lst.listen(8)
        threading.Thread(target=self.serve, daemon=True).start()

    def serve(self):
        while True:
            try:
                c, _ = self.lst.accept()
            except OSError:
                return
            threading.Thread(target=self.one, args=(c,), daemon=True).start()

    def one(self, c):
        try:
            c.sendall(b"By what name are you known? ")
            stage, buf = 0, b""
            while True:
                d = c.recv(4096)
                if not d:
                    return
                self.got += d
                buf += re.sub(rb"\xff[\xfb-\xfe].", b"", d)
                while b"\n" in buf or b"\r" in buf:
                    m = re.search(rb"[\r\n]", buf)
                    line, buf = buf[:m.start()].strip(b"\x00"), buf[m.end():]
                    if not line:
                        continue
                    if stage == 0:
                        c.sendall(b"\r\nWelcome, " + line + b".\r\n" + bytes([IAC, WILL, 1]) + b"Passphrase: ")
                        stage = 1
                    elif stage == 1:
                        c.sendall(b"****\r\n" + bytes([IAC, WONT, 1]) + b"\r\nYou stand in a room.\r\n> ")
                        stage = 2
                    elif line == b"quit":
                        c.sendall(b"Farewell.\r\n")
                        c.close()
                        return
                    else:
                        c.sendall(b"You " + line + b".\r\n> ")
        except OSError:
            return

    def close(self):
        self.lst.close()


# --- helpers ----------------------------------------------------------------
def start(mode, extra_env=None):
    env = dict(os.environ, AGORA_SERVE=mode)
    if extra_env:
        env.update(extra_env)
    p = subprocess.Popen([BIN, "serve", str(PORT), "--store", STORE], env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
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
    if p.poll() is None:
        p.terminate()
        try:
            p.wait(10)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
    try:
        os.killpg(p.pid, signal.SIGKILL)
    except OSError:
        pass
    time.sleep(0.3)


def drain(s, t=0.5):
    out = b""
    s.settimeout(t)
    try:
        while True:
            d = s.recv(65536)
            if not d:
                break
            out += d
    except OSError:
        pass
    return out


def until(s, needle, t=5.0):
    out, end = b"", time.time() + t
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
    drain(s, 0.4)
    return s


def sign(nonce):
    kf = tempfile.NamedTemporaryFile(delete=False, dir=BASE)
    kf.write(PKCS8 + open(KEYS + "/qix", "rb").read())
    kf.close()
    mf = tempfile.NamedTemporaryFile(delete=False, dir=BASE)
    mf.write(b"agora-login:" + nonce)
    mf.close()
    sig = subprocess.check_output(["openssl", "pkeyutl", "-sign", "-rawin", "-inkey", kf.name,
                                   "-keyform", "DER", "-in", mf.name])
    os.unlink(kf.name)
    os.unlink(mf.name)
    return binascii.hexlify(sig)


def login(s):
    s.sendall(b"login qix\r\n")
    out = until(s, b"auth:", 3.0)
    nonce = re.search(rb"challenge:\s*([0-9a-f]+)", out).group(1)
    s.sendall(b"auth: " + sign(nonce) + b"\r\n")
    # Wait for the whole greeting: "welcome, " and the handle are separate writes,
    # and in fork mode they can arrive as separate segments (1.12.1: CI read the
    # first alone on a two-core runner and called a good login a failure).
    return b"welcome, qix" in until(s, b"welcome, qix", 3.0)


def whoami_ms(s):
    drain(s, 0.2)            # a late answer to an earlier question must not count
    t = time.perf_counter()
    s.sendall(b"whoami\r\n")
    out = until(s, b"anonymous", 8.0)
    return (time.perf_counter() - t) * 1000 if b"anonymous" in out else 99999


def endpoint(text):
    with open(STORE + "/.descent", "w") as f:
        f.write(text + "\n")


# --- the checks -------------------------------------------------------------
def poll_checks(mud):
    print("— poll")
    p = start("poll")
    if not p:
        check(False, "poll server started")
        return
    try:
        a, b = connect(), connect()
        check(login(a), "poll: login")
        endpoint(str(MUDPORT))
        mud.got = b""
        a.sendall(b"descent\r\nzaxon\r\n")
        out = until(a, b"Passphrase", 4.0)
        check(b"stepping through the portal" in out and b"Welcome, zaxon" in out,
              "poll B: the pipelined name reached the MUD")
        ms = whoami_ms(b)
        check(ms < 300, "poll A: another session answered during a visit (%.0f ms)" % ms)
        a.sendall(b"secret\r\n")
        until(a, b"room", 3.0)
        a.sendall(b"quit\r\n")
        out = until(a, b"back at the agora", 4.0)
        check(b"back at the agora" in out, "poll C: back from the MUD")
        drain(a, 0.5)
        # Echo: a raw client that never answers negotiation — agora echoes it.
        a.sendall(b"w")
        echo = drain(a, 0.5)
        check(echo.count(b"w") == 1, "poll C: echo resumed once after the MUD's echo dance (%r)" % echo[-20:])
        a.sendall(b"hoami\r\n")
        drain(a, 0.5)
        # A blackholed endpoint (TEST-NET-1): the dial pends; nobody waits for it.
        time.sleep(0.2)
        endpoint("192.0.2.1:4040")
        t0 = time.time()
        a.sendall(b"descent\r\n")
        time.sleep(0.3)
        ms = whoami_ms(b)
        check(ms < 300, "poll A: another session answered during a pending dial (%.0f ms)" % ms)
        out = until(a, b"not answering", 6.0)
        el = time.time() - t0
        check(b"not answering" in out and el < 5.5, "poll A: the dialler told 'not answering' in %.1f s" % el)
        a.close()
        b.close()
    finally:
        stop(p)


def shutdown_during_visit(mud):
    print("— poll: shutdown during a visit")
    p = start("poll")
    if not p:
        check(False, "poll server started")
        return
    a = connect()
    login(a)
    endpoint(str(MUDPORT))
    a.sendall(b"descent\r\n")
    until(a, b"known?", 4.0)
    t0 = time.time()
    p.send_signal(signal.SIGTERM)
    try:
        rc = p.wait(10)
    except subprocess.TimeoutExpired:
        rc = -1
    out = drain(a, 1.0)
    check(rc == 0 and time.time() - t0 < 2.0, "poll D: SIGTERM during a visit exits 0 at once (rc %d)" % rc)
    check(b"leaving the Descent" in out, "poll D: the player was told")
    stop(p)


def model_rejected():
    print("— AGORA_SERVE")
    for bad in ("epoll", "pol"):
        p = subprocess.Popen([BIN, "serve", str(PORT), "--store", STORE], env=dict(os.environ, AGORA_SERVE=bad),
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        try:
            rc = p.wait(5)
        except subprocess.TimeoutExpired:
            rc = None                  # it started serving: the value was accepted
            stop(p)
        check(rc == 2, "E: AGORA_SERVE=%s refused (exit %s)" % (bad, rc))


def accept_pace():
    print("— poll accepts")
    p = start("poll")
    if not p:
        check(False, "poll server started")
        return
    try:
        t0 = time.time()
        for _ in range(200):
            s = socket.create_connection(("127.0.0.1", PORT), timeout=5)
            until(s, b"> ", 3.0)
            s.close()
        el = time.time() - t0
        check(el < 2.0, "poll F: 200 sequential connections in %.2f s (the 20 ms sweep made it 4 s)" % el)
    finally:
        stop(p)


def children_of(pid):
    try:
        return [int(x) for x in open("/proc/%d/task/%d/children" % (pid, pid)).read().split()]
    except OSError:
        return []


def gone(pid, secs):
    end = time.time() + secs
    while time.time() < end:
        try:
            if open("/proc/%d/stat" % pid).read().split(")")[1].split()[0] == "Z":
                return True
        except OSError:
            return True
        time.sleep(0.05)
    return False


def fork_checks(mud):
    print("— fork")
    p = start("fork")
    if not p:
        check(False, "fork server started")
        return
    a = connect()
    check(login(a), "fork: login")
    endpoint(str(MUDPORT))
    a.sendall(b"descent\r\nzaxon\r\n")
    out = until(a, b"Passphrase", 4.0)
    check(b"Welcome, zaxon" in out, "fork H: in the MUD, the pipelined name delivered")
    a.sendall(b"secret\r\n")
    until(a, b"room", 3.0)
    a.sendall(b"quit\r\n")
    check(b"back at the agora" in until(a, b"back at the agora", 4.0), "fork H: back from the MUD")
    kid = max(children_of(p.pid) or [0])
    t0 = time.time()
    p.send_signal(signal.SIGTERM)
    rc = p.wait(10)
    el = time.time() - t0
    check(rc == 0 and el < 2.0, "fork G: clean shutdown in %.2f s (rc %d)" % (el, rc))
    check(b"goodbye" in drain(a, 1.0) and gone(kid, 2.0), "fork G: the child said goodbye and left")
    stop(p)
    p = start("fork")
    a = connect()
    kid = max(children_of(p.pid) or [0])   # the newest child: `a`'s (start()'s probe may linger)
    p.send_signal(signal.SIGKILL)
    p.wait()
    check(gone(kid, 3.0), "fork G: a SIGKILLed parent took its child with it (no orphan)")
    check(b"goodbye" in drain(a, 1.0), "fork G: and the child said goodbye")
    stop(p)


def real_client(mud):
    if shutil.which("telnet") is None:
        print("  (I skipped: no `telnet` client installed)")
        return
    print("— I: a real telnet client in a 40x24 pty (poll)")
    os.makedirs(STORE + "/pub", exist_ok=True)
    with open(STORE + "/pub/1.txt", "w") as f:
        f.write("Subject: long\n\n" + "word " * 40 + "\n")
    endpoint(str(MUDPORT))
    p = start("poll")
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp("telnet", ["telnet"])
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 40, 0, 0))
    out = [b""]

    def pump(t):
        end = time.time() + t
        while time.time() < end:
            r, _, _ = select.select([fd], [], [], 0.05)
            if r:
                try:
                    out[0] += os.read(fd, 65536)
                except OSError:
                    return

    def send(b, t=0.8):
        os.write(fd, b)
        pump(t)

    # 1.12.1 — wait for what a step answers, not a fixed time: on a loaded two-core
    # runner a fixed window can close before the reply, and a missing challenge
    # crashed the nonce match. `t` is only the upper bound.
    def send_until(b, needle, t=6.0):
        m0 = len(out[0])
        os.write(fd, b)
        end = time.time() + t
        while needle not in out[0][m0:] and time.time() < end:
            pump(0.05)
        pump(0.3)                       # what follows the needle on the same reply

    def text(b):
        return re.sub(rb"\x1b\[[0-9;]*[A-Za-z]", b"", b).decode("utf-8", "replace")

    def widest(b):
        return max(len(l.rstrip("\r")) for l in text(b).split("\n"))

    try:
        pump(0.5)
        send_until(b"open 127.0.0.1 %d\r" % PORT, b"> ")
        m = len(out[0])
        send_until(b"login qix\r", b"auth:")
        nonce = re.search(rb"challenge:\s*([0-9a-f]+)", out[0][m:])
        if nonce is None:
            raise RuntimeError("no challenge from `login qix`: %r" % out[0][m:][-200:])
        send_until(b"auth: " + sign(nonce.group(1)) + b"\r", b"welcome, qix")
        send_until(b"enter pub\r", b"> ")
        m = len(out[0])
        send_until(b"read 1\r", b"> ")
        before = widest(out[0][m:])
        send_until(b"descent\r", b"known?")
        send_until(b"zaxon\r", b"Passphrase")
        send_until(b"secret\r", b"room")
        send_until(b"quit\r", b"back at the agora")
        pump(0.5)
        m = len(out[0])
        send_until(b"read 1\r", b"> ")
        after = widest(out[0][m:])
        m = len(out[0])
        send(b"whoa", 1.0)
        typed = text(out[0][m:])
        send(b"mi\r", 0.8)
        send(b"quit\r", 0.8)
    finally:
        try:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
        except OSError:
            pass
        stop(p)
    check(before <= 39 and after <= 39, "I: read wraps to 39 columns before (%d) and after (%d) a visit" % (before, after))
    check("whoa" in typed and "wwhhooaa" not in typed, "I: a half-typed line is visible, once")


def main():
    if not os.path.exists(BIN):
        print("build first: cyrius build src/main.cyr build/agora")
        return 2
    if shutil.which("openssl") is None:
        print("SKIP — needs openssl")
        return 0
    shutil.rmtree(BASE, ignore_errors=True)
    os.makedirs(KEYS)
    subprocess.run([BIN, "keygen", "--key", KEYS + "/qix"], stdout=subprocess.DEVNULL, check=True)
    subprocess.run([BIN, "register", "--handle", "qix", "--key", KEYS + "/qix", "--store", STORE],
                   stdout=subprocess.DEVNULL, check=True)
    mud = FakeMud(MUDPORT)
    try:
        poll_checks(mud)
        shutdown_during_visit(mud)
        model_rejected()
        accept_pace()
        fork_checks(mud)
        real_client(mud)
    finally:
        mud.close()
        shutil.rmtree(BASE, ignore_errors=True)
    if fails:
        print("FAIL — %d check(s): %s" % (len(fails), "; ".join(fails)))
        return 1
    print("OK — Descent visits no longer stall the BBS, the return keeps the client's options, "
          "the loops wait on readiness, and fork children leave with their parent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
