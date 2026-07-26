#!/usr/bin/env python3
# 23-sigpipe-survival.py
#
# Why: every byte agora sends leaves through a flagsless write. A client that
# vanishes mid-response makes the kernel raise SIGPIPE, and SIGPIPE's default
# disposition TERMINATES the process — silently, with no error return and no
# cleanup. Under AGORA_SERVE=fork that killed one connection's child and the
# server lived. Under the 1.6.0 poll multiplex ONE process serves all 64
# sessions, so the same rude disconnect kills the whole server — and poll is the
# only model on agnos, which has no fork. 1.6.2 sets SIG_IGN for SIGPIPE in
# cmd_serve_on, so the write returns EPIPE instead; both write paths already
# treat a failed write as "close this connection".
#
# The provocation matters, and the obvious one does not work. An immediate RST
# makes the server's next write fail with ECONNRESET — an ordinary error return,
# no signal. SIGPIPE needs a SECOND write after the peer is truly gone: the
# client closes cleanly (FIN) with output still pending and never reads, the
# server's next write lands in the buffer, the peer's stack answers with RST
# because nothing is there to receive it, and the write AFTER that raises
# SIGPIPE. Pipelining many commands guarantees the server is still writing when
# that happens. (Verified: against a build without the fix, this kills the poll
# server on the 4th client; an immediate-RST version leaves it running.)
#
# Run agora first, in the model you want to prove:
#   AGORA_SERVE=poll ./build/agora serve 2323 --store ./bbs
#   AGORA_SERVE=fork ./build/agora serve 2323 --store ./bbs
#
# Success: "N rude clients survived", "server still serving", exit 0.
# Failure (unpatched, poll): the survivor connection is refused — the server
# process is gone — exit 1.
#
# Note on fork: there the blast radius is one child BY DESIGN (ADR 0007), so an
# unpatched fork server also passes this script. Poll is where it has teeth, and
# poll is the model that matters — it is the only one agnos can run.

import socket
import sys
import time

HOST = "127.0.0.1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2323
ROUNDS = int(sys.argv[2]) if len(sys.argv) > 2 else 12

# Enough pipelined commands that the server is still emitting when the peer's
# RST arrives. `help` prints the full command list — many writes' worth.
PROVOKE = b"help\r\n" * 60


def rude_client(i):
    """Pipeline a large request, then close cleanly without reading a byte."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((HOST, PORT))
    except OSError as e:
        print(f"  round {i}: connect failed — server already dead? ({e})")
        return False
    try:
        # A small receive window fills fast, so the server has plenty pending.
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024)
        s.sendall(PROVOKE)
        time.sleep(0.02)
    except OSError:
        pass  # being rude is the point; a failure here is still a rude exit
    finally:
        s.close()  # clean FIN with output still queued — the SIGPIPE setup
    return True


def survivor():
    """A well-behaved session: proof the server is still there and coherent."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    try:
        s.connect((HOST, PORT))
    except OSError as e:
        print(f"  survivor: connect REFUSED — the server is gone ({e})")
        return None
    try:
        s.sendall(b"boards\r\n")
        time.sleep(0.6)
        data = b""
        s.settimeout(2)
        try:
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
                if len(data) > 65536:
                    break
        except socket.timeout:
            pass
        return data
    finally:
        s.close()


def main():
    ok = 0
    for i in range(ROUNDS):
        if rude_client(i):
            ok += 1
        else:
            print(f"FAIL: server stopped accepting after {ok} rude clients")
            return 1
        time.sleep(0.1)
    print(f"  {ok} rude clients survived (pipelined request, clean FIN, never read)")

    data = survivor()
    if not data:
        print("FAIL: server did not answer after the rude clients — SIGPIPE killed it")
        return 1
    # 0xFF is IAC: the option announce salvo proves this is really agora talking.
    if b"\xff" not in data:
        print(f"FAIL: survivor got {len(data)} bytes but no IAC — not a healthy session")
        return 1
    print(f"  server still serving ({len(data)} bytes, IAC present)")
    print("OK — SIGPIPE ignored; rude disconnects close one session, not the server")
    return 0


if __name__ == "__main__":
    sys.exit(main())
