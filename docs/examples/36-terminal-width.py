#!/usr/bin/env python3
# 36-terminal-width.py
#
# Why: 1.10.1 (roadmap § 1.10.1, ADR 0030) — agora has stored the client's
# window size since M1 (NAWS, RFC 1073) and until 1.10.1 nothing read it, so any
# line wider than the reader's terminal broke wherever the terminal ran out of
# columns, mid-word. Output is now wrapped to the reported width. This drives
# the real server, both serve models, with raw bytes:
#
#   A  without NAWS nothing changes: a long body line arrives whole;
#   B  after WILL NAWS + a 40x24 report, `read` and `list` fit 39 columns (one is
#      left free), the subject's continuation hangs under it, an indented line
#      keeps its indent, a URL longer than a row arrives whole (never cut), and
#      every newline is CR LF;
#   C  a resize to 60 columns takes effect on the next command;
#   D  a door frame (Smuggler's Ledger) fits the window too;
#   E  the greeting — sent before any NAWS can arrive — fits 80 columns;
#   F  a NAWS width of 0 ("no width is being sent", RFC 1073) means no wrap;
#   G  (when inetutils `telnet` is installed) a REAL client in a 40x24 pty sends
#      NAWS itself, and `read` comes back fitted to its 40 columns. Skipped,
#      with a note, otherwise.
#
# Self-contained: its own store under /tmp, its own servers. Success: "OK — ..."
# and exit 0. Against a 1.10.0 build B, C, D, E and G fail.
#
# Usage: 36-terminal-width.py [port]
#        AGORA_BIN=/path/to/agora 36-terminal-width.py   (A/B an older build)

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
import termios
import time
import unicodedata

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BIN = os.environ.get("AGORA_BIN", os.path.join(ROOT, "build", "agora"))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2336
BASE = "/tmp/agora-width-smoke-%d" % os.getpid()
STORE = BASE + "/bbs"

IAC, SB, SE, WILL = 255, 250, 240, 251
NAWS = 31
URL = "https://example.com/a/very/long/path/that/must/never/be/cut/in/two"
LONG = ("the quick brown fox jumps over the lazy dog while the slow green turtle "
        "watches from the bank and wonders why anyone would hurry at all")

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


def naws(cols, rows=24):
    """WILL NAWS (an SB counts only for an agreed option, RFC 855) + the report."""
    return bytes([IAC, WILL, NAWS, IAC, SB, NAWS, cols >> 8, cols & 255, rows >> 8, rows & 255, IAC, SE])


def text_rows(raw):
    """The display rows of a server reply: telnet commands and SGR removed."""
    b = re.sub(rb"\xff[\xfb-\xfe].", b"", raw)
    b = re.sub(rb"\xff\xfa.*?\xff\xf0", b"", b, flags=re.S)
    b = re.sub(rb"\x1b\[[0-9;]*[A-Za-z]", b"", b)
    t = b.decode("utf-8", "replace").replace("\x00", "")
    return [r.rstrip("\r") for r in t.split("\n")]


def cols(row):
    c = 0
    for ch in row:
        if ch == "\t":
            c = (c // 8 + 1) * 8
        elif unicodedata.combining(ch) or ord(ch) < 32:
            continue
        else:
            c += 2 if unicodedata.east_asian_width(ch) in "WF" else 1
    return c


def widest(raw, skip=()):
    return max([cols(r) for r in text_rows(raw) if r not in skip] or [0])


def bare_lf(raw):
    return len(re.findall(rb"(?<!\r)\n", raw))


def checks(mode):
    print("— %s" % mode)
    p = start(mode)
    if not p:
        check(False, "%s server started" % mode)
        return
    try:
        s, greet = connect()
        check(widest(greet) <= 79, "%s E: the greeting fits 80 columns" % mode)
        send(s, b"enter pub\r")
        out = send(s, b"read 1\r", 0.8)
        check(LONG.encode() in out, "%s A: without NAWS a long line arrives whole" % mode)

        send(s, naws(40))
        out = send(s, b"read 1\r", 0.8)
        check(widest(out, skip=(URL,)) <= 39, "%s B: read fits 39 columns" % mode)
        check(URL.encode() in out, "%s B: a URL longer than a row arrives whole" % mode)
        check(b"\r\n         " in out, "%s B: the subject's continuation hangs under it" % mode)
        rows = text_rows(out)
        # A continuation row of the indented line: four spaces, then text that
        # is not where the line itself starts.
        check(any(r.startswith("    ") and not r.startswith("     ") and not r.startswith("    an indented")
                  for r in rows),
              "%s B: an indented line keeps its indent when it wraps" % mode)
        check(bare_lf(out) == 0, "%s B: every newline is CR LF" % mode)
        out = send(s, b"list\r")
        check(widest(out) <= 39 and b"\r\n           " in out, "%s B: list fits 39, the subject hanging" % mode)

        out = send(s, naws(60) + b"read 1\r", 0.8)
        w = widest(out, skip=(URL,))
        check(40 <= w <= 59, "%s C: a resize to 60 takes effect (widest row %d)" % (mode, w))

        send(s, naws(0))
        out = send(s, b"read 1\r", 0.8)
        check(LONG.encode() in out, "%s F: a NAWS width of 0 means no wrap" % mode)
        s.close()

        s, _ = connect()
        send(s, naws(40))
        out = send(s, b"play smuggler practice\r", 0.8)
        check(b"SMUGGLER" in out and widest(out) <= 39, "%s D: a door frame fits 39 columns" % mode)
        s.close()
    finally:
        stop(p)


def real_client():
    """G: inetutils telnet in a 40x24 pty; returns what it showed."""
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp("telnet", ["telnet"])
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 40, 0, 0))
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
    mark = len(out)
    for line, t in ((b"open 127.0.0.1 %d\r" % PORT, 2.0), (b"enter pub\r", 0.8)):
        os.write(fd, line)
        pump(t)
    mark = len(out)
    os.write(fd, b"read 1\r")
    pump(1.5)
    shown = out[mark:]
    os.write(fd, b"quit\r")
    pump(0.6)
    try:
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
    except OSError:
        pass
    return shown


def real_client_checks():
    if shutil.which("telnet") is None:
        print("  (G skipped: no `telnet` client installed)")
        return
    print("— G: a real telnet client in a 40x24 pty (poll)")
    p = start("poll")
    try:
        shown = real_client()
    finally:
        stop(p)
    check(b"quick brown" in shown, "G: the post was shown")
    check(widest(shown, skip=(URL,)) <= 39, "G: the client's own NAWS (40) fitted the post to 39 columns")


def main():
    if not os.path.exists(BIN):
        print("build first: cyrius build src/main.cyr build/agora")
        return 2
    try:
        for mode in ("poll", "fork"):
            shutil.rmtree(BASE, ignore_errors=True)
            os.makedirs(STORE + "/pub")
            with open(STORE + "/pub/1.txt", "w") as f:
                f.write("Subject: a subject that is long enough to need a second row on a narrow window\n\n")
                f.write(LONG + "\n")
                f.write("    an indented line that is also long enough to need wrapping on forty columns\n")
                f.write(URL + "\nshort\n")
            checks(mode)
        real_client_checks()
    finally:
        shutil.rmtree(BASE, ignore_errors=True)
    if fails:
        print("FAIL — %d check(s): %s" % (len(fails), "; ".join(fails)))
        return 1
    print("OK — output fits the window the client reports (NAWS), and nothing changes without one")
    return 0


if __name__ == "__main__":
    sys.exit(main())
