#!/usr/bin/env python3
# 29-egress-sanitize.py
#
# Why: 1.8.0 — a BBS prints OTHER USERS' text, and until 1.8.0 a stored post
# could carry live terminal control sequences into every reader's session.
# Two paths put them on disk, and `send_text` only ever doubled IAC:
#
#   (a) the wire. `input_byte_ok` drops C0, DEL and IAC at ingress, but every
#       byte 0x80-0xFE passes — including the C1 controls, raw (0x9B is the
#       8-bit CSI) and UTF-8-encoded (C2 9B is U+009B, a CSI to any terminal that
#       honours C1). A registered user could post `C2 9B 2 J` and, on such a
#       terminal, clear every reader's screen, or `C2 9D 52;c;… C2 9C` and write their clipboard (OSC 52).
#   (b) the CLI. `agora post` stores its stdin body with NO filter at all, so a
#       CLI-authored body could carry a plain ESC sequence to every wire reader
#       — and `agora read` / `agora list` printed stored bytes raw into the
#       operator's own terminal.
#
# 1.8.0 neutralizes stored text at EGRESS (darshana `tty_sanitize_buf`, UTF-8
# mode, keeping TAB / LF / CR — ADR 0024): every control byte or sequence
# becomes one '?', well-formed UTF-8 passes byte-for-byte, and the stored post
# is left exactly as it was written. This smoke has TEETH: against a 1.7.x
# binary the reader receives the raw C2 9B / C2 9D / 9B / ESC bytes and every
# "neutralized" check below fails.
#
# Self-contained: makes its own key + store under /tmp, starts and stops its own
# server under BOTH serve models. Requires openssl >= 3.0 (Ed25519 login).
#
# Success: "OK — ..." and exit 0.
#
# Usage: 29-egress-sanitize.py [port]
#        AGORA_BIN=/path/to/agora 29-egress-sanitize.py   (A/B an older build)

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
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2329
BASE = "/tmp/agora-sanitize-smoke-%d" % os.getpid()
STORE = BASE + "/bbs"
KEY = BASE + "/qix.key"

# --- the payload: one line per class, plus text that must survive intact ---
GOOD = b"utf8 ok: caf\xc3\xa9 \xe2\x82\xac \xe2\x80\x94 end"   # é, €, em dash
TABL = b"tab\there"                                            # TAB is kept
SUBJECT = b"subj \xc2\x9b31m red"                              # encoded CSI in a header
BODY = [
    GOOD,
    TABL,
    b"c1 csi: \xc2\x9b2J",                     # U+009B CSI + "2J" = clear screen
    b"osc52: \xc2\x9d52;c;cHduZWQ=\xc2\x9c",   # U+009D OSC ... U+009C ST = clipboard write
    b"raw c1: \x9b31m",                        # raw 8-bit CSI (a stray continuation byte)
    b"bad utf8: \xc3\x28 \xed\xa0\x80 \xf8",   # truncated lead, surrogate, invalid lead
]
# What a reader must see instead (each neutralized byte / sequence -> one '?').
WANT = [
    GOOD,
    TABL,
    b"c1 csi: ?2J",
    b"osc52: ?52;c;cHduZWQ=?",
    b"raw c1: ?31m",
    b"bad utf8: ?( ??? ?",
]
WANT_SUBJECT = b"subj ?31m red"
# CLI-authored body: a plain ESC sequence, which only the CLI path can store.
CLI_BODY = b"cli \x1b[2Jesc\x07bel\r\nline two\r\n"
CLI_WANT = b"cli ?[2Jesc?bel\r\nline two\r\n"
FORBIDDEN = [b"\xc2\x9b", b"\xc2\x9d", b"\xc2\x9c", b"\x9b31m", b"\x1b", b"\x07"]

fails = []


def run(args, stdin=None):
    return subprocess.run([BIN] + args, input=stdin, capture_output=True)


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
    drain(s)
    return s


def login(s):
    """Ed25519 challenge/response, as in 05-telnet-login.sh / 27-audit-lows.py."""
    s.sendall(b"login qix\r\n")
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
        f.write(bytes.fromhex("302e020100300506032b657004220420") + open(KEY, "rb").read())
    with open(msg, "wb") as f:
        f.write(("agora-login:" + chal).encode())
    subprocess.run(["openssl", "pkeyutl", "-sign", "-rawin", "-inkey", der,
                    "-keyform", "DER", "-in", msg, "-out", sig], capture_output=True)
    s.sendall(b"auth: " + binascii.hexlify(open(sig, "rb").read()) + b"\r\n")
    time.sleep(0.5)
    return b"welcome" in drain(s)


def start(mode):
    env = dict(os.environ, AGORA_SERVE=mode)
    p = subprocess.Popen([BIN, "serve", "--port", str(PORT), "--store", STORE],
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
    p.send_signal(signal.SIGTERM)
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()


def check_clean(tag, out):
    for bad in FORBIDDEN:
        if bad in out:
            fails.append("%s: raw control bytes %r reached the reader" % (tag, bad))


def wire_post():
    """Post the payload over the wire as qix; return its id."""
    s = connect()
    if not login(s):
        fails.append("wire: could not log in as qix")
        s.close()
        return None
    s.sendall(b"post\r\n"); time.sleep(0.3); drain(s)
    s.sendall(SUBJECT + b"\r\n"); time.sleep(0.3); drain(s)
    for line in BODY:
        s.sendall(line + b"\r\n")
        time.sleep(0.15)
    drain(s)
    s.sendall(b".\r\n"); time.sleep(0.6)
    reply = drain(s)
    s.close()
    for tok in reply.replace(b"#", b" ").split():
        if tok.isdigit():
            return int(tok)
    fails.append("wire: no post id in %r" % reply[:80])
    return None


def wire_read(mode, pid, cli_pid):
    """A second, ANONYMOUS session reads both posts and lists the board."""
    s = connect()
    s.sendall(b"read %d\r\n" % pid); time.sleep(0.6)
    out = drain(s)
    s.sendall(b"read %d\r\n" % cli_pid); time.sleep(0.6)
    cli_out = drain(s)
    s.sendall(b"list\r\n"); time.sleep(0.6)
    lst = drain(s)
    s.close()
    tag = "%s/read" % mode
    check_clean(tag, out)
    check_clean("%s/read-cli-post" % mode, cli_out)
    check_clean("%s/list" % mode, lst)
    for want in WANT:
        if want + b"\r\n" not in out:
            fails.append("%s: expected line %r not received" % (tag, want))
    if b"Subject: " + WANT_SUBJECT + b"\r\n" not in out:
        fails.append("%s: subject not neutralized (%r)" % (tag, out[:200]))
    if CLI_WANT not in cli_out:
        fails.append("%s: CLI-authored ESC/BEL not neutralized (%r)" % (tag, cli_out[-120:]))
    if b"[qix]  " + WANT_SUBJECT not in lst:
        fails.append("%s/list: subject not neutralized (%r)" % (mode, lst[-200:]))
    if not [f for f in fails if f.startswith(mode)]:
        print("  OK  %-4s reader got '?' for every control, UTF-8 + TAB + CRLF intact" % mode)


def main():
    shutil.rmtree(BASE, ignore_errors=True)
    os.makedirs(BASE)
    try:
        if run(["keygen", "--key", KEY]).returncode != 0:
            print("FAIL: keygen"); return 1
        if run(["register", "--handle", "qix", "--key", KEY, "--store", STORE]).returncode != 0:
            print("FAIL: register"); return 1
        # (b) the CLI path: stdin body is stored with no filter at all.
        r = run(["post", "--as", "qix", "--key", KEY, "--store", STORE,
                 "--subject", "cli post"], stdin=CLI_BODY)
        cli_pid = int(r.stdout.split()[0]) if r.returncode == 0 else None
        if cli_pid is None:
            print("FAIL: CLI post (%r)" % r.stdout); return 1

        pid = None
        for mode in ("poll", "fork"):
            p = start(mode)
            if p is None:
                fails.append("%s: server never came up" % mode)
                continue
            try:
                if pid is None:
                    pid = wire_post()
                if pid is not None:
                    wire_read(mode, pid, cli_pid)
            finally:
                stop(p)
        if pid is None:
            print("FAIL:", *fails, sep="\n  "); return 1

        # The stored artifact is NOT rewritten — sanitization is egress-only.
        stored = open(os.path.join(STORE, "%d.txt" % pid), "rb").read()
        if b"\xc2\x9b2J" not in stored or GOOD not in stored:
            fails.append("store: the post on disk was altered (egress-only rule broken)")
        else:
            print("  OK  the stored post is byte-for-byte what was typed")

        # The operator's terminal: `agora read` / `agora list` on stdout.
        rr = run(["read", str(pid), "--store", STORE]).stdout
        check_clean("cli/read", rr)
        for want in WANT:
            if want not in rr:
                fails.append("cli/read: expected %r" % want)
        rc = run(["read", str(cli_pid), "--store", STORE]).stdout
        check_clean("cli/read-cli-post", rc)
        if CLI_WANT not in rc:
            fails.append("cli/read: CLI-authored ESC/BEL not neutralized (%r)" % rc)
        rl = run(["list", "--store", STORE]).stdout
        check_clean("cli/list", rl)
        if WANT_SUBJECT not in rl:
            fails.append("cli/list: subject not neutralized (%r)" % rl)
        if not [f for f in fails if f.startswith("cli")]:
            print("  OK  agora read / agora list neutralize controls on stdout too")
    finally:
        shutil.rmtree(BASE, ignore_errors=True)

    if fails:
        print("FAIL (%d):" % len(fails))
        for f in fails:
            print("  - " + f)
        return 1
    print("OK — stored user text reaches readers with every control neutralized")
    return 0


if __name__ == "__main__":
    sys.exit(main())
