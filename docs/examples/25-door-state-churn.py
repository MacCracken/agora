#!/usr/bin/env python3
# 25-door-state-churn.py
#
# Why: 1.6.3 gave every door game a DD_FREE hook (ADR 0022) so a state and the
# buffers it owns go back to the freelist when the player quits, when the `play`
# launcher replaces a live state, and when a session slot is released. That is
# the last allocation class in agora with a lifetime longer than one dispatched
# line — under AGORA_SERVE=poll, where one process serves every session for the
# life of the server, an abandoned state used to be gone forever.
#
# Freeing is also the easiest thing to get wrong: free too much and a later
# render reads dead memory; free the wrong slot's state and you corrupt another
# player's game. So this script exercises all three release paths hard, in the
# serve model where a mistake actually shows:
#
#   1. enter/quit churn — many play->quit cycles on one session, across every
#      door, so each game's *_free runs hundreds of times and the freelist
#      recycles its blocks back into the next state.
#   2. rapid alternation — quit each door with ITS OWN quit word and enter the
#      next immediately, so a state is freed and its blocks are handed straight
#      back out to the next game. (Note: the launcher's pre-install free is a
#      DEFENSIVE guard, not reachable from the wire — while you are inside a
#      door, `play <other>` is fed to the game as input, not to the launcher.)
#   3. disconnect-mid-game — connect, enter a door, drop the connection without
#      quitting, repeatedly, so session_release frees a slot's live state (and
#      the slot is then handed to a new connection).
#
# Success: every session still answers coherently at the end, the last door
# still renders, and the server is alive. A use-after-free typically shows up
# here as a hang, a dead connection, or garbage where a frame should be.
#
# Run agora first (poll is the model that matters — it is the only one on agnos):
#   AGORA_SERVE=poll ./build/agora serve 2323 --store ./bbs
#
# Usage: 25-door-state-churn.py [port] [cycles]

import socket
import sys
import time

HOST = "127.0.0.1"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 2323
CYCLES = int(sys.argv[2]) if len(sys.argv) > 2 else 40

# Practice-mode doors: no identity needed, so the churn needs no login.
DOORS = [
    ("play smuggler practice", "q"),
    ("play port practice", "q"),
    ("play handler practice", "q"),
    ("play quest practice", "q"),
    ("play eliza", "quit"),
    ("play parry", "quit"),
    ("play jabberwacky", "quit"),
    ("play olympiad practice", "q"),
    ("play decode", "q"),
]


def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    s.connect((HOST, PORT))
    time.sleep(0.35)
    drain(s)
    return s


def drain(s):
    out = b""
    s.setblocking(False)
    try:
        while True:
            d = s.recv(65536)
            if not d:
                break
            out += d
    except (BlockingIOError, socket.error):
        pass
    s.setblocking(True)
    s.settimeout(10)
    return out


def send(s, line, pause=0.06):
    s.sendall(line.encode() + b"\r\n")
    time.sleep(pause)
    return drain(s)


def phase_enter_quit(s):
    """Every door, entered and quit, CYCLES times over."""
    for i in range(CYCLES):
        enter, leave = DOORS[i % len(DOORS)]
        send(s, enter)
        send(s, leave)
    out = send(s, "help", pause=0.5)
    return b"Commands:" in out


def phase_alternate(s):
    """Quit and immediately re-enter a different door: a freed state's blocks go
    straight back out to the next game, which is where a bad free shows up."""
    for i in range(CYCLES):
        a, aq = DOORS[i % len(DOORS)]
        b, bq = DOORS[(i + 1) % len(DOORS)]
        send(s, a)
        send(s, aq)         # A's state is freed here
        send(s, b)          # B is built from the recycled blocks
        send(s, bq)
    out = send(s, "help", pause=0.5)
    return b"Commands:" in out


def phase_disconnect_midgame():
    """Drop the connection while a door is open — session_release frees it."""
    for i in range(CYCLES):
        enter, _ = DOORS[i % len(DOORS)]
        try:
            s = connect()
            send(s, enter, pause=0.05)
            s.close()               # no quit: the slot still holds a live state
        except OSError as e:
            print(f"  disconnect cycle {i}: {e}")
            return False
        time.sleep(0.02)
    return True


def main():
    print(f"=== phase 1: {CYCLES} enter/quit cycles across {len(DOORS)} doors ===")
    try:
        s = connect()
    except OSError as e:
        print(f"FAIL: cannot connect ({e})")
        return 1
    if not phase_enter_quit(s):
        print("FAIL: session incoherent after enter/quit churn")
        s.close()
        return 1
    print("  session still coherent")

    print(f"=== phase 2: {CYCLES} quit-then-enter alternation cycles ===")
    if not phase_alternate(s):
        print("FAIL: session incoherent after alternation churn")
        s.close()
        return 1
    print("  session still coherent")
    s.close()

    print(f"=== phase 3: {CYCLES} disconnects mid-game (slot release frees the state) ===")
    if not phase_disconnect_midgame():
        print("FAIL: server stopped accepting during disconnect churn")
        return 1
    print("  server kept accepting")

    print("=== final: a fresh session must still play a door end to end ===")
    try:
        s = connect()
    except OSError as e:
        print(f"FAIL: server gone after churn ({e})")
        return 1
    out = send(s, "play quest practice", pause=0.5)
    if b"QUEST" not in out and b"quest" not in out.lower():
        print(f"FAIL: door did not render after churn ({len(out)} bytes)")
        s.close()
        return 1
    send(s, "q")
    s.close()
    print("  fresh session played a door after all the churn")
    print(f"OK — door state free paths survive {CYCLES * 3} cycles with no corruption")
    return 0


if __name__ == "__main__":
    sys.exit(main())
