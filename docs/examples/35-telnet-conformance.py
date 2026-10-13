#!/usr/bin/env python3
# 35-telnet-conformance.py
#
# Why: 1.10.0 (roadmap § 1.10.0, ADR 0029) — RFC 854 and RFC 1184 are
# authoritative for agora (CLAUDE.md: "a deviation is a bug"), and until 1.10.0
# seven were open. This drives each fix through the real server, both serve
# models, with raw bytes:
#
#   A  the opening salvo asks IAC DO LINEMODE (RFC 1184 § 2.1: the server asks);
#   B  IAC AYT gets visible evidence — "[Yes]" (RFC 854: "send back ... some
#      visible (i.e., printable) evidence");
#   C  character mode edits the line: DEL / BS erase a character, IAC EC a
#      character, IAC EL the line (RFC 854) — a typo used to be uncorrectable;
#   D  LINEMODE: WILL LINEMODE draws the EDIT|TRAPSIG request; once the client
#      ACKs it agora says WONT ECHO and stops echoing — the client edits and
#      echoes the line (RFC 1184 § 2.2, ECHO);
#   E  an SLC import request (0 SLC_DEFAULT 0) is answered with all 30 functions
#      (RFC 1184 § 5.5);
#   F  NVT newlines on egress: a CLI-authored post with LF-only lines and a bare
#      CR reads back as CR LF / CR NUL (RFC 854; audit 1.8.1 I12);
#   G  (when inetutils `telnet` is installed) a REAL client in a pty negotiates
#      LINEMODE end to end — WILL LINEMODE, its SLC export ACKed, MODE
#      EDIT|TRAPSIG ACKed, agora's WONT ECHO — and a line it edited locally
#      (`whoamx<DEL>i`) arrives as `whoami`. Skipped, with a note, otherwise.
#
# Self-contained: its own store under /tmp, its own servers. Success: "OK — ..."
# and exit 0. Against a 1.9.2 build every section fails.
#
# Usage: 35-telnet-conformance.py [port]
#        AGORA_BIN=/path/to/agora 35-telnet-conformance.py   (A/B an older build)

import os
import pty
import select
import shutil
import signal
import socket
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BIN = os.environ.get("AGORA_BIN", os.path.join(ROOT, "build", "agora"))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2335
BASE = "/tmp/agora-telnet-smoke-%d" % os.getpid()
STORE = BASE + "/bbs"

IAC, SB, SE, WILL, WONT, DO, AYT, EC, EL = 255, 250, 240, 251, 252, 253, 246, 247, 248
LINEMODE, ECHO = 34, 1

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


def drain(s, t=0.6):
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


def connect():
    s = socket.create_connection(("127.0.0.1", PORT), timeout=6)
    time.sleep(0.4)
    return s, drain(s)


def send(s, data, t=0.6):
    s.sendall(data)
    time.sleep(0.15)
    return drain(s, t)


def checks(mode):
    print("— %s" % mode)
    p = start(mode)
    if not p:
        check(False, "%s server started" % mode)
        return
    try:
        s, greet = connect()
        check(bytes([IAC, DO, LINEMODE]) in greet, "%s A: the greeting asks DO LINEMODE" % mode)
        out = send(s, bytes([IAC, AYT]))
        check(b"[Yes]" in out, "%s B: AYT is answered with [Yes]" % mode)
        out = send(s, b"whoamx\x7fi\r")
        check(b"anonymous" in out and b"unknown" not in out, "%s C: DEL corrects a typo (whoamx<DEL>i)" % mode)
        # The erased character must matter: commands match by prefix, so a
        # trailing typo ("whoamix") would run `whoami` with or without the erase.
        out = send(s, b"whoamj" + bytes([IAC, EC]) + b"i\r")
        check(b"anonymous" in out and b"unknown" not in out, "%s C: IAC EC erases a character" % mode)
        out = send(s, b"rubbish" + bytes([IAC, EL]) + b"whoami\r")
        check(b"anonymous" in out and b"unknown" not in out, "%s C: IAC EL erases the line" % mode)
        s.close()

        s, _ = connect()
        out = send(s, bytes([IAC, WILL, LINEMODE]))
        check(bytes([IAC, SB, LINEMODE, 1, 3, IAC, SE]) in out, "%s D: WILL LINEMODE draws MODE EDIT|TRAPSIG" % mode)
        # E needs LINEMODE agreed: a subnegotiation for an option not enabled is
        # ignored by rule (RFC 855).
        out = send(s, bytes([IAC, SB, LINEMODE, 3, 0, 3, 0, IAC, SE]))
        check(out.startswith(bytes([IAC, SB, LINEMODE, 3, 1, 3, 0])) and len(out) >= 96,
              "%s E: an SLC import gets the 30-function table" % mode)
        out = send(s, bytes([IAC, SB, LINEMODE, 1, 7, IAC, SE]))
        check(bytes([IAC, WONT, ECHO]) in out, "%s D: the ACK hands echoing over (WONT ECHO)" % mode)
        out = send(s, b"whoami\r")
        check(b"anonymous" in out and b"whoami" not in out, "%s D: in LINEMODE agora no longer echoes the line" % mode)
        s.close()

        s, _ = connect()
        send(s, b"enter pub\r")
        out = send(s, b"read 1\r", 0.8)
        body = out[out.find(b"one"):]
        check(b"one\r\ntwo\r\x00three\r\n" in body, "%s F: LF → CR LF and a bare CR → CR NUL on egress" % mode)
        s.close()
    finally:
        stop(p)


def real_client():
    """G: inetutils telnet in a pty, its option trace on; returns its output."""
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp("telnet", ["telnet"])
    out = b""

    def pump(t):
        nonlocal out
        end = time.time() + t
        while time.time() < end:
            r, _, _ = select.select([fd], [], [], 0.1)
            if r:
                try:
                    out += os.read(fd, 65536)
                except OSError:
                    return

    pump(0.5)
    for line, t in ((b"toggle options\r", 0.6), (b"open 127.0.0.1 %d\r" % PORT, 2.0),
                    (b"whoamx\x7fi\r", 1.5), (b"quit\r", 0.8)):
        os.write(fd, line)
        pump(t)
    try:
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
    except OSError:
        pass
    return out


def real_client_checks():
    if shutil.which("telnet") is None:
        print("  (G skipped: no `telnet` client installed)")
        return
    print("— G: a real telnet client (poll)")
    p = start("poll")
    try:
        out = real_client()
    finally:
        stop(p)
    check(b"SENT WILL LINEMODE" in out, "G: the client agreed LINEMODE")
    check(b"SLC" in out and b"ACK" in out, "G: its SLC export was ACKed")
    check(b"RCVD WONT ECHO" in out, "G: agora handed echoing to it")
    check(b"anonymous" in out, "G: a line it edited locally ran as `whoami`")


def main():
    if not os.path.exists(BIN):
        print("build first: cyrius build src/main.cyr build/agora")
        return 2
    try:
        for mode in ("poll", "fork"):
            shutil.rmtree(BASE, ignore_errors=True)
            os.makedirs(STORE + "/pub")
            # A CLI-authored post with LF-only lines and a bare CR — the egress case.
            with open(STORE + "/pub/1.txt", "wb") as f:
                f.write(b"Subject: nvt\n\none\ntwo\rthree\n")
            checks(mode)
        real_client_checks()
    finally:
        shutil.rmtree(BASE, ignore_errors=True)
    if fails:
        print("FAIL — %d check(s): %s" % (len(fails), "; ".join(fails)))
        return 1
    print("OK — AYT, line editing, LINEMODE, SLC and NVT newlines follow RFC 854 / 1184")
    return 0


if __name__ == "__main__":
    sys.exit(main())
