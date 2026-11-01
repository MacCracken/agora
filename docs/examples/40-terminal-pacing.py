#!/usr/bin/env python3
# 40-terminal-pacing.py
#
# Why: 1.13.0 (roadmap § 1.13.0, ADR 0034). agora has stored the window height
# (NAWS) and the terminal type (RFC 1091) since M1 and used neither. Output now
# stops a screenful at a time, the Handler slow-prints its cables, and a
# terminal that names itself DUMB gets no colour. All three hold output back,
# and under poll one process serves everyone, so none of them can wait inside a
# command: the output gate holds queued bytes instead. This drives the real
# server, both serve models, with raw bytes:
#
#   A  after a 80x10 window report, `help` stops at `--More--` after nine rows,
#      with the command prompt still held; Enter turns the page until the help
#      is out, each line exactly once, and the prompt comes last;
#   B  `q` at the stop drops the rest of the help and prompts again;
#   C  `more off` sends the help whole;
#   D  the greeting waits for the terminal type: a client that agrees
#      TERMINAL-TYPE and names itself DUMB gets a greeting with no escape byte,
#      one that declines (WONT) is greeted at once and in colour, and one that
#      says nothing is greeted within a second, in colour;
#   E  reading a Handler cable with a window reported comes over at 2400 baud
#      (240 characters a second), and a key skips to its end;
#      without a window report the frame arrives whole and at once;
#   F  (when inetutils `telnet` is installed) a REAL client in an 80x12 pty
#      stops at `--More--` on `help`, and `q` brings the prompt back.
#
# Self-contained: its own store under /tmp, its own servers. Success: "OK — ..."
# and exit 0. Against a 1.12.4 build A, B, D and E fail.
#
# Usage: 40-terminal-pacing.py [port]
#        AGORA_BIN=/path/to/agora 40-terminal-pacing.py   (A/B an older build)

import fcntl
import os
import pty
import select
import shutil
import signal
import socket
import struct
import subprocess
import sys
import termios
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BIN = os.environ.get("AGORA_BIN", os.path.join(ROOT, "build", "agora"))
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2340
BASE = "/tmp/agora-pacing-smoke-%d" % os.getpid()
STORE = BASE + "/bbs"

IAC, SB, SE, WILL, WONT, DO = 255, 250, 240, 251, 252, 253
TTYPE, NAWS = 24, 31
MORE = b"--More-- (Enter; q to stop)"
LAST_HELP = b"close the session"

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


def until(s, needle, t):
    """Read until `needle` arrives or `t` seconds pass; returns (bytes, seconds)."""
    out = b""
    t0 = time.time()
    s.settimeout(0.1)
    while needle not in out and time.time() - t0 < t:
        try:
            d = s.recv(65536)
            if not d:
                break
            out += d
        except OSError:
            pass
    return out, time.time() - t0


def connect():
    s = socket.create_connection(("127.0.0.1", PORT), timeout=6)
    out, _ = until(s, b"> ", 3.0)
    return s, out


def send(s, data, t=0.6):
    s.sendall(data)
    time.sleep(0.15)
    return drain(s, t)


def naws(cols, rows):
    """WILL NAWS (an SB counts only for an agreed option, RFC 855) + the report."""
    return bytes([IAC, WILL, NAWS, IAC, SB, NAWS, cols >> 8, cols & 255, rows >> 8, rows & 255, IAC, SE])


def paging(mode):
    s, _ = connect()
    send(s, naws(80, 10))
    out = send(s, b"help\r")
    check(out.endswith(MORE), "%s A: help stops at --More--" % mode)
    rows = out.split(b"\n")
    check(len(rows) == 11, "%s A: nine rows of help before the stop (%d rows)" % (mode, len(rows) - 2))
    check(b"\r\n> " not in out, "%s A: the command prompt is held" % mode)
    seen = out
    turns = 0
    while turns < 10 and seen.rstrip().endswith(MORE):
        seen += send(s, b"\r\n")
        turns += 1
    check(seen.count(LAST_HELP) == 1 and seen.count(b"this message") == 1,
          "%s A: every help line arrived once (%d turns)" % (mode, turns))
    check(seen.endswith(b"\r\n> "), "%s A: the prompt comes after the last page" % mode)

    out = send(s, b"help\r")
    out += send(s, b"q")
    check(LAST_HELP not in out and out.endswith(b"> "), "%s B: q drops the rest and prompts" % mode)

    send(s, b"more off\r")
    out = send(s, b"help\r")
    check(MORE not in out and out.count(LAST_HELP) == 1, "%s C: more off sends the help whole" % mode)
    s.close()


def greeting(mode):
    # DUMB: answer DO TTYPE with WILL, and the SEND with IS DUMB.
    s = socket.create_connection(("127.0.0.1", PORT), timeout=6)
    s.sendall(bytes([IAC, WILL, TTYPE]))
    first, _ = until(s, bytes([IAC, SB, TTYPE, 1, IAC, SE]), 2.0)
    s.sendall(bytes([IAC, SB, TTYPE, 0]) + b"DUMB" + bytes([IAC, SE]))
    out, _ = until(s, b"> ", 3.0)
    greet = first + out
    check(b"Type anything" in greet and b"\x1b" not in greet,
          "%s D: a DUMB terminal's greeting has no escape byte" % mode)
    out = send(s, b"play handler practice\r")
    check(b"HANDLER" in out and b"\x1b" not in out, "%s D: nor do its door frames" % mode)
    s.close()

    s = socket.create_connection(("127.0.0.1", PORT), timeout=6)
    t0 = time.time()
    s.sendall(bytes([IAC, WONT, TTYPE]))
    out, _ = until(s, b"> ", 3.0)
    took = time.time() - t0
    check(b"\x1b[" in out and took < 0.2, "%s D: WONT is greeted at once, in colour (%.0f ms)" % (mode, took * 1000))
    s.close()

    s = socket.create_connection(("127.0.0.1", PORT), timeout=6)
    out, took = until(s, b"> ", 3.0)
    check(b"\x1b[" in out and 0.15 < took < 1.0,
          "%s D: a silent client is greeted within a second, in colour (%.0f ms)" % (mode, took * 1000))
    s.close()


def teletype(mode):
    s, _ = connect()
    send(s, b"play handler practice\r")
    send(s, b"c\r")
    s.sendall(b"1\r")
    out, took = until(s, b"[N]ext", 3.0)
    check(b"[N]ext" in out and took < 0.5, "%s E: without a window the cable arrives at once (%.0f ms)" % (mode, took * 1000))
    send(s, b"x\r")
    send(s, naws(80, 24))
    s.sendall(b"1\r")
    out, took = until(s, b"[N]ext", 5.0)
    # 240 characters a second; the status line before the cable goes out whole.
    paced = len(out) / 240.0
    check(b"[N]ext" in out and took > 0.6 and took >= 0.7 * paced,
          "%s E: with a window it comes at 2400 baud (%d B in %.2f s)" % (mode, len(out), took))
    send(s, b"x\r")
    s.sendall(b"1\r")
    time.sleep(0.3)
    t0 = time.time()
    s.sendall(b" ")
    out, _ = until(s, b"[N]ext", 3.0)
    took = time.time() - t0
    check(b"[N]ext" in out and took < 0.5, "%s E: a key skips to the end (%.0f ms)" % (mode, took * 1000))
    out = send(s, b"x\r")
    check(b"CABLE QUEUE" in out, "%s E: the skip key was not a door command" % mode)
    s.close()


def real_client():
    """F: inetutils telnet in an 80x12 pty; returns what it showed."""
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp("telnet", ["telnet"])
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 12, 80, 0, 0))
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
    os.write(fd, b"open 127.0.0.1 %d\r" % PORT)
    pump(2.5)
    mark = len(out)
    os.write(fd, b"help\r")
    pump(1.0)
    stopped = out[mark:]
    mark = len(out)
    os.write(fd, b"q\r")
    pump(1.0)
    after = out[mark:]
    os.write(fd, b"quit\r")
    pump(0.6)
    try:
        os.kill(pid, signal.SIGKILL)
        os.waitpid(pid, 0)
    except OSError:
        pass
    return stopped, after


def real_client_checks():
    if shutil.which("telnet") is None:
        print("  (F skipped: no `telnet` client installed)")
        return
    print("— F: a real telnet client in an 80x12 pty (poll)")
    p = start("poll")
    try:
        stopped, after = real_client()
    finally:
        stop(p)
    check(b"--More--" in stopped and LAST_HELP not in stopped, "F: help stopped at --More--")
    check(b"> " in after and LAST_HELP not in after, "F: q brought the prompt back")


def main():
    if not os.path.exists(BIN):
        print("build first: cyrius build src/main.cyr build/agora")
        return 2
    try:
        for mode in ("poll", "fork"):
            shutil.rmtree(BASE, ignore_errors=True)
            os.makedirs(STORE)
            print("— %s" % mode)
            p = start(mode)
            if not p:
                check(False, "%s server started" % mode)
                continue
            try:
                paging(mode)
                greeting(mode)
                teletype(mode)
            finally:
                stop(p)
        real_client_checks()
    finally:
        shutil.rmtree(BASE, ignore_errors=True)
    if fails:
        print("FAIL — %d check(s): %s" % (len(fails), "; ".join(fails)))
        return 1
    print("OK — output stops a screenful at a time, cables come at 2400 baud, and DUMB terminals get no colour")
    return 0


if __name__ == "__main__":
    sys.exit(main())
