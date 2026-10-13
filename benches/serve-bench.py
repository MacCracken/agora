#!/usr/bin/env python3
# benches/serve-bench.py — the serve-level baselines the parser harness
# (benches/bench_telnet.bcyr) cannot take: accept-loop rate, per-session memory,
# and world-lock contention.
#
# Why (1.8.2): CLAUDE.md § P(-1) step 2 has asked for "parser throughput +
# accept-loop rate" since 0.2.0, and only the parser half ever existed — through
# a 1.6.0 change of serve model, nobody had measured what either model costs per
# connection. Four ADR "measure before refining" gates (ADR 0010's world lock,
# ADR 0014's lazy turn resolution, ADR 0005's reply scan) were waiting on numbers
# that were never taken. Results go in BENCHMARKS.md § Serve-level baselines.
#
#   accept  connections/s through connect -> greeting -> close, sequential and
#           with 8 concurrent connectors, per serve model
#   memory  resident memory per idle session: poll = the server's RSS growth
#           per session; fork = PSS per connection child (THP disabled in the
#           server, or RSS moves in 2 MB steps)
#   world   world-lock transactions/s with 1..16 concurrent writers (the ADR
#           0010 flock + read + write-temp + fsync + rename), and no lost update
#   reply   milliseconds per `read`, whose reply scan (ADR 0005) opens every post
#           on the board — the number roadmap § 1.9.1's index decision waits on
#
# Usage: benches/serve-bench.py {accept,memory,world,reply,all} [--runs N] [--store DIR]
#        AGORA_BIN=/path/to/agora benches/serve-bench.py ...   (A/B a build)
# Default store: build/bench-store (a real disk: tmpfs would flatter fsync).

import argparse
import ctypes
import os
import shutil
import socket
import statistics
import subprocess
import sys
import threading
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BIN = os.environ.get("AGORA_BIN", os.path.join(ROOT, "build", "agora"))
PORT = 34850


def no_thp():
    """preexec: PR_SET_THP_DISABLE, so RSS is measured in 4 KB pages."""
    try:
        ctypes.CDLL(None, use_errno=True).prctl(41, 1, 0, 0, 0)
    except Exception:
        pass


def start(mode, store, thp_off=False):
    p = subprocess.Popen([BIN, "serve", str(PORT), "--store", store],
                         env=dict(os.environ, AGORA_SERVE=mode),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         preexec_fn=no_thp if thp_off else None)
    for _ in range(100):
        try:
            socket.create_connection(("127.0.0.1", PORT), timeout=1).close()
            time.sleep(0.2)
            return p
        except OSError:
            time.sleep(0.05)
    p.kill()
    raise SystemExit("server did not start")


def stop(p):
    p.terminate()
    try:
        p.wait(10)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()


def greet_once():
    """connect, read until the first prompt, close."""
    s = socket.create_connection(("127.0.0.1", PORT), timeout=10)
    buf = b""
    while b"> " not in buf:
        d = s.recv(65536)
        if not d:
            break
        buf += d
    s.close()


def kb(pid, field):
    for line in open("/proc/%d/status" % pid):
        if line.startswith(field):
            return int(line.split()[1])
    return 0


def pss_kb(pid):
    try:
        for line in open("/proc/%d/smaps_rollup" % pid):
            if line.startswith("Pss:"):
                return int(line.split()[1])
    except OSError:
        pass
    return 0


def children(pid):
    out = subprocess.run(["pgrep", "-P", str(pid)], capture_output=True, text=True).stdout
    return [int(x) for x in out.split()]


def bench_accept(store, runs):
    print("accept — connect, read the greeting to the first prompt, close")
    for mode in ("fork", "poll"):
        seq, par = [], []
        for _ in range(runs):
            p = start(mode, store)
            try:
                n = 300
                t0 = time.time()
                for _ in range(n):
                    greet_once()
                seq.append(n / (time.time() - t0))
                errs = []

                def worker():
                    try:
                        for _ in range(60):
                            greet_once()
                    except OSError as e:
                        errs.append(e)
                ts = [threading.Thread(target=worker) for _ in range(8)]
                t0 = time.time()
                for t in ts:
                    t.start()
                for t in ts:
                    t.join()
                par.append(480 / (time.time() - t0))
                if errs:
                    print("  (%s: %d connector errors)" % (mode, len(errs)))
            finally:
                stop(p)
            time.sleep(0.5)
        print("  %-4s  sequential %6.0f conn/s (runs %s)   8 concurrent %6.0f conn/s (runs %s)" % (
            mode, statistics.median(seq), "/".join("%.0f" % x for x in seq),
            statistics.median(par), "/".join("%.0f" % x for x in par)))


def bench_memory(store, runs):
    print("memory — resident cost of an idle, greeted session (THP off)")
    for mode, n in (("poll", 64), ("fork", 32)):
        per = []
        for _ in range(runs):
            p = start(mode, store, thp_off=True)
            try:
                time.sleep(0.3)
                base = kb(p.pid, "VmRSS:")
                socks = []
                for _ in range(n):
                    s = socket.create_connection(("127.0.0.1", PORT), timeout=10)
                    buf = b""
                    while b"> " not in buf:
                        buf += s.recv(65536)
                    socks.append(s)
                time.sleep(0.8)
                if mode == "poll":
                    per.append((kb(p.pid, "VmRSS:") - base) / n)
                else:
                    kids = children(p.pid)
                    per.append(sum(pss_kb(k) for k in kids) / max(1, len(kids)))
                for s in socks:
                    s.close()
            finally:
                stop(p)
            time.sleep(0.5)
        what = "server RSS growth per session" if mode == "poll" else "PSS per connection child"
        print("  %-4s  %6.1f KB  %s, %d sessions (runs %s)" % (
            mode, statistics.median(per), what, n, "/".join("%.1f" % x for x in per)))


def bench_world(store, runs):
    print("world — flock'd world transactions (ADR 0010): P writers x 200 each")
    wstore = os.path.join(store, "world")
    for procs in (1, 2, 4, 8, 16):
        rates = []
        for _ in range(runs):
            shutil.rmtree(wstore, ignore_errors=True)
            os.makedirs(wstore)
            each = 200
            t0 = time.time()
            ps = [subprocess.Popen([BIN, "worldbench", "bench", str(each), "--store", wstore],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                  for _ in range(procs)]
            for x in ps:
                x.wait()
            dt = time.time() - t0
            got = subprocess.run([BIN, "worldread", "bench", "--store", wstore],
                                 capture_output=True, text=True).stdout.strip()
            if got != str(procs * each):
                raise SystemExit("LOST UPDATE: %d writers x %d -> %s" % (procs, each, got))
            rates.append(procs * each / dt)
        print("  %2d writer(s)  %7.0f txn/s  (runs %s)  — no lost updates" % (
            procs, statistics.median(rates), "/".join("%.0f" % x for x in rates)))


def bench_reply(store, runs):
    print("reply — `read 1` latency vs board size (ADR 0005 scan-on-read; 1 KB posts; fork, so no poll-sweep wait)")
    for nposts in (500, 2000, 4096):
        rstore = os.path.join(store, "reply-%d" % nposts)
        shutil.rmtree(rstore, ignore_errors=True)
        os.makedirs(rstore)
        body = "x" * 1000
        for i in range(1, nposts + 1):
            with open(os.path.join(rstore, "%d.txt" % i), "w") as f:
                rt = "Reply-To: 1\r\n" if i % 10 == 0 else ""
                f.write("Subject: post %d\r\n%s\r\n%s\r\n" % (i, rt, body))
        per = []
        for _ in range(runs):
            p = start("fork", rstore)
            try:
                s = socket.create_connection(("127.0.0.1", PORT), timeout=30)
                buf = b""
                while b"> " not in buf:
                    buf += s.recv(65536)
                n = 20
                t0 = time.time()
                for _ in range(n):
                    s.sendall(b"read 1\r\n")
                    buf = b""
                    while not buf.endswith(b"> "):
                        d = s.recv(1 << 20)
                        if not d:
                            break
                        buf += d
                per.append((time.time() - t0) * 1000 / n)
                s.close()
            finally:
                stop(p)
        print("  %4d posts  %7.2f ms per read (runs %s)" % (
            nposts, statistics.median(per), "/".join("%.2f" % x for x in per)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["accept", "memory", "world", "reply", "all"])
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--store", default=os.path.join(ROOT, "build", "bench-store"))
    a = ap.parse_args()
    if not os.path.exists(BIN):
        raise SystemExit("build first: CYRIUS_DCE=1 cyrius build src/main.cyr build/agora")
    shutil.rmtree(a.store, ignore_errors=True)
    os.makedirs(a.store)
    print("agora serve-level baselines — %s, %d run(s) each, store %s" % (
        subprocess.run([BIN, "--version"], capture_output=True, text=True).stdout.strip(), a.runs, a.store))
    try:
        if a.what in ("accept", "all"):
            bench_accept(a.store, a.runs)
        if a.what in ("memory", "all"):
            bench_memory(a.store, a.runs)
        if a.what in ("world", "all"):
            bench_world(a.store, a.runs)
        if a.what in ("reply", "all"):
            bench_reply(a.store, a.runs)
    finally:
        shutil.rmtree(a.store, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
