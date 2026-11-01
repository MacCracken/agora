# 0023 — The dual serve model: fork per accept, or one process polling all sessions

> **Status**: Accepted — **amended by [ADR 0031](0031-descent-session-state.md) (1.11.0)**; the agnos drain
> amended at 1.12.3 (§ Decision, the sweep: a no-wait send on agnos ≥ 1.57.13) and measured on agnos at 1.12.4,
> when the Descent's write to the MUD stopped waiting too; at 1.13.0 the drain sends only up to the output gate's
> hold ([ADR 0034](0034-output-gate.md))
> **Date**: 2026-07-26 (recorded retroactively — the decision shipped at 1.5.0 / 1.6.0)
> **Amends**: [ADR 0007](0007-fork-per-accept-concurrency.md) — see § Relationship to ADR 0007.

## Context

This ADR is late. The decision it records shipped in **1.5.0** (the agnos target) and **1.6.0** (the poll
multiplex), and the five hardening cuts that followed — 1.6.1 through 1.6.5 — were almost entirely about
consequences of it. Two later ADRs, [0021](0021-per-command-scratch-arena.md) (the per-command arena) and
[0022](0022-door-state-free-hook.md) (the door-state free hook), each open by retroactively narrating
1.6.0 because there was nothing to cite. The 2026-07-26 deferred-work sweep flagged the gap; this closes
it.

**What forced the change.** [ADR 0007](0007-fork-per-accept-concurrency.md) chose fork-per-accept: one
process per connection, the kernel reclaiming memory at child exit. That is a good decision on Linux and
it still ships there. It cannot work on **agnos**, which has no `fork`: its process model is `spawn#3`
from an in-memory ELF (which cannot inherit an accepted socket fd) plus a blocking per-pid `waitpid#4`.

1.5.0 shipped agnos support by serving **serially** — handle one connection to completion, then accept
the next. That made agora run under mirshi, and it made agora a single-user BBS on its own target. 1.6.0
replaced it with a single-process multiplex.

## Decision

**Two serve models, selected at runtime, sharing one dispatch core.**

- **`AGORA_SERVE=fork`** — ADR 0007's concurrency and memory model, unchanged: one process per
  connection, kernel reclaim at child exit, non-blocking `waitpid` reaper. The Linux default. **Its
  accept path did change at 1.7.0**: the parent now waits in `poll(2)` over {listener, signalfd} on a
  non-blocking listener so SIGINT/SIGTERM can reach it, and each child restores the default signal
  disposition before serving (see § Clean shutdown).
- **`AGORA_SERVE=poll`** — one process serves every connection. Linux opt-in; **the only model on
  agnos**, which selects it regardless of what the variable says (`serve_mode_from_env`, `src/main.cyr`).

The poll model is built from four pieces:

- A **pre-allocated session pool** — `MAX_SESS = 64` reusable slots, each a heap struct holding the
  connection's full state plus a non-blocking tx queue. No per-connection alloc/free churn.
- A **context swap** — `sess_load` / `sess_save` move ~19 deep session globals between the slot and the
  globals the dispatch functions read. This is what let the door games, chat and `session_execute` stay
  **completely untouched**: they are pure state machines per [ADR 0009](0009-door-games-subsystem.md), so
  they neither know nor care which model is running.
- A **sweep** — each ~20 ms tick drains pending accepts (non-blocking), then services every active slot:
  non-blocking recv → `process_rx` → tx drain. ⚠ **The drain is genuinely non-blocking only on Linux.**
  `session_drain`'s comment claimed both platforms until 1.7.0; on agnos `sock_set_nonblocking` is a
  no-op and `sys_write` on a socket fd routes to `SYS_SOCK_SEND`, which blocks — so on the one target
  that *always* polls, a slow reader stalled the whole sweep. agnos has no non-blocking send to switch
  to, so 1.7.0 (roadmap N3) **bounds** it to one send attempt per drain rather than removing it.
  > **1.8.1 amendment (audit M12).** That bound broke silently at the 1.8.0 pin move: since cyrius 6.6.7
  > the agnos `sys_write` on a socket is `_agnos_sock_send_all`, which retries "no progress" until a 30 s
  > stall deadline re-armed on any byte — so one zero-window peer froze the agnos sweep for 30 s+, a
  > trickling one indefinitely. `session_drain` now makes ONE raw `sock_send#48` per drain on agnos,
  > which restores the bound described here (one send, which the kernel may itself hold ~8 s).
  >
  > **1.12.3 amendment — hole A is cured on agnos ≥ 1.57.13.** agnos 1.57.13 added `sock_send_dl` #109
  > (wrapped since cyrius 6.7.11): #48 with a caller ceiling, where a **negative** ceiling means no wait at
  > all — it commits what can go out now and returns the count, possibly 0 — and -1 still means the conn is
  > gone or not the caller's. That is the kernel-side non-blocking send this bullet said was missing. On a
  > kernel that has it, `session_drain` sends with no wait until the queue is empty or a call commits 0
  > (partial, kept for the next sweep), so **the sweep's drain never waits on a slow reader**. A kernel
  > before 1.57.13 keeps the 1.7.0 bound exactly, one #48 per drain; which kernel it is comes from the
  > stdlib's own cached probe (`_agnos_sock_send_left`). Three consequences, all recorded above `session_drain_wait`:
  > - **Pacing.** The agnos kernel keeps one segment in flight per conn and sends the next only once the
  >   last is ACKed (`tcp_send_ex`), so a no-wait drain moves at most one segment per sweep: about 1,460 B
  >   per 20 ms (~73 KB/s; ~27 KB/s at agnos' 536-byte default segment). #48 sent at line rate, and held
  >   every other session while it did. That figure is arithmetic: no agnos kernel run has measured it.
  > - **Two drains may still wait, bounded.** A command that prints more than `SESS_TX_CAP` needs the peer
  >   to take bytes before the command can go on. Linux absorbs that in its kernel send buffer; agnos has
  >   none beyond the segment in flight, so a no-wait make-room drain would bring back the 1.8.1 S5 bug
  >   (a big `list` drops the session). That drain, and the shutdown goodbye, make ONE send with a
  >   `SESS_DRAIN_WAIT_US` (250 ms) ceiling, measured once from entry and never re-armed by an ACK, so a
  >   trickling peer cannot stretch it as it could #48's 8 s window. A command bigger than the queue can
  >   still cost the sweep one such wait each time the queue fills: that cost is set by the command's size
  >   and the peer's pace, because there is nowhere else on agnos to put the bytes.
  > - **Make-room compacts first.** An agnos queue is now usually part-sent, so `sess_tx_enqueue` reclaims
  >   the sent prefix before it drains, and drains (and may wait) only if that is not enough (`s17`).
  >
  > **1.12.4 amendment — measured on an agnos kernel, and the Descent's write.** `scripts/agnos-smoke.py`
  > boots agnos 1.57.14 in QEMU and serves agora from it ([BENCHMARKS.md](../../BENCHMARKS.md) § agnos).
  > - **The cure holds.** While a client with a 4 KB receive buffer asks for ~12 MB and reads nothing
  >   (smoke 31's), a bystander's worst keystroke echo over 60 s is 26–31 ms. 1.12.2's raw #48 drain held
  >   the same bystander for 23.8 s, with stalls 6–8 s apart before that, under both TCG and KVM.
  > - **The pacing above was half right.** One segment per sweep is the case when the peer's ACK is not
  >   back within the drain, and a sweep is `POLL_MS` rounded up to the kernel's tick, about 30 ms: a 61 KB
  >   `read 1` ran at 48 KB/s under KVM. Under TCG, QEMU's ACK can land inside the drain, so 48–192 KB/s.
  >   #48 sent the same read at 2,680 KB/s (KVM) and 673 KB/s (TCG). **The cure costs a single healthy
  >   reader most of its bulk throughput on agnos**: a 64 KB post takes about 1.3 s to arrive. Recorded as a
  >   known limitation in the CHANGELOG; not changed here.
  > - **The Descent's write to the MUD** (`descent_mud_write`) was the stdlib's `sys_write`: a 30 s stall
  >   deadline, re-armed on progress, inside the sweep. A MUD that stopped reading held a bystander for the
  >   full 30 s (measured with 1.12.3's write against a stub MUD). It is now one `_agnos_sock_send_left`
  >   with no wait, like the drain, and the same bystander's worst echo is 28–30 ms.
  > - **What the harness cannot see**: the #48 fallback on a kernel before 1.57.13 (only a current kernel
  >   is booted), and the shutdown goodbye (no signal reaches the guest). It also showed that the agnos
  >   kernel declares a zero-window peer dead after five unanswered resends (~31 s) and sends it neither
  >   FIN nor RST, so a dropped non-reader never sees its connection close.
  >   *(Corrected at 1.13.0, from the kernel source: the resends are answered. agora's close turns the conn
  >   into a held FIN slot, which the persist cap does not cover, so the kernel gives up on it after five
  >   resends, about 47 s; it then drops every later segment from the peer without the RST RFC 9293
  >   § 3.10.7.1 requires. Filed as agnos issue 2026-10-31.)*
  >
  > **Capacity note (audit I13):** agnos' stdlib socket table holds 8 sockets, so the real ceiling there
  > is ~8 sessions (a Descent visit uses one more), not `MAX_SESS` = 64.
- **A per-sweep line budget** (added 1.8.1, audit H2). `process_rx` runs at most `POLL_LINE_BUDGET`
  (one) *counted* line per session per sweep and parks the rest of the recv in the slot
  (`SESS_RX_OFF`/`LEN`); the sweep skips its sleep while anything is parked. Before it, one anonymous
  client pipelining 585 `read 1` per packet held every other session for seconds (13.7 s with 16 such
  clients). Compose lines do not count, so pasting a post is not throttled.
- **`send_buf` is model-aware** — under poll it enqueues to the active session's tx queue; under fork it
  writes. Every `send_str` call site is unchanged.

**Both models funnel through `process_rx`.** That is the single most useful property of the design: a fix
to line dispatch, or to the arena reset, or to a send-failure path, applies to both by construction.

## Consequences

- **Positive** — agnos gets real concurrency; it was a one-user-at-a-time BBS between 1.5.0 and 1.6.0.
- **Positive** — Linux keeps per-connection crash isolation as the default. A door-game bug still costs
  one connection there.
- **Positive** — the dispatch core has one implementation, not two.
- **Negative, and this is the important one** — **the poll model removed three things fork was silently
  providing**, and nothing in the code said it depended on them:
  1. **Process exit was the free list.** Cyrius `alloc()` has no free; the child's death reclaimed
     everything. Under poll it reclaims nothing. Measured at 1.6.2: **7,473 bytes leaked per command**,
     dead linear. Re-closed by [ADR 0021](0021-per-command-scratch-arena.md) (per-line arena) and
     [ADR 0022](0022-door-state-free-hook.md) (door-state free hook).
  2. **A child's death bounded a bad connection.** A slow reader parked one worker; under poll it parks
     *everyone*. **Mitigated**, not fixed, across 1.6.2–1.7.0: SIGPIPE ignored, send returns checked,
     the Descent write bounded (1.6.2–1.6.5); an over-cap tx queue now closes the session instead of
     going mute-but-open, and the agnos drain yields after one send (1.7.0, roadmap N3). 1.8.1 adds
     the per-sweep line budget (one client's pipeline can no longer monopolise the sweep), a drain
     before the tx queue is declared overflowed (a big `list` is not a slow reader), and, under fork,
     a sticky send failure plus a 64-child cap (`MAX_SESS` is now the operator's bound in both
     models). Two stalls remain by construction — the agnos blocking send has no non-blocking peer,
     and `descent_proxy` holds the sweep for a player's whole MUD session (since 1.8.1 it at least
     watches the shutdown signalfd, and a failed connect is not redialled for 30 s). **Since 1.12.3**
     the first has a peer on agnos ≥ 1.57.13 (#109 with no wait; see the sweep's amendment above),
     and what is left of it is the bounded make-room wait. The Descent's write to the MUD, which went
     through the stdlib's 30 s `sys_write` route on agnos, sends without waiting since 1.12.4; its
     connect still blocks there (`sock_connect` #47, ~8 s, bounded by the redial cooldown). The second went at 1.11.0
     ([ADR 0031](0031-descent-session-state.md): the Descent is a session state now).
  3. **A crash cost one connection.** Under poll it costs all 64.
- **Accepted risk, recorded at 1.9.2 — a slow-but-real typist holds a slot.** Every model caps
  connections at `MAX_SESS` (64: the poll pool, and since 1.8.1 the fork child cap), and a session is
  reaped after `SESS_IDLE_MS` (60 s) without a data byte. A client that sends one real data byte every
  50 s therefore holds a slot indefinitely, and 64 of them hold the server. 1.6.4 closed the cheap
  version of this (an `IAC NOP` keepalive refreshed the idle timer; now only `EV_DATA` does) and
  deliberately stopped there. What remains is **indistinguishable from a legitimate very slow typist**,
  and both bounds that would catch it were weighed and **not taken**:
  - *a session-lifetime cap* also disconnects the legitimate long sessions a BBS exists for — a QUEST
    run, an idle chat, a reader working through a board;
  - *a per-source cap* needs `getpeername`, which **agnos does not have** — it would protect Linux and
    leave the target that *only* runs poll unprotected — and it mis-fires behind NAT, where a LAN's
    users share one address.
  The cost of the attack is 64 TCP connections kept alive by a byte a minute each — a deliberate,
  sustained, visible effort against a LAN BBS, not a drive-by. The operator's tools are `MAX_SESS` and
  the network edge (rate-limiting or filtering by address is a firewall's job). Revisit if agnos gains
  `getpeername` (a per-source cap becomes possible on both targets) or a deployment reports it.
### Clean shutdown (added 1.7.0)

Neither model could exit. Both loops declared `var stop = 0;` and looped `while (stop == 0)` with
nothing anywhere assigning `stop`, so the only way to stop agora was to kill it — the poll model never
drained its 64 slots and the fork model never reaped. That is a third thing fork was silently providing
that nobody had written down: under fork the operator's `kill` at least ended one process cleanly per
connection, and under poll it ends everything at once, mid-write.

Both models now route SIGINT/SIGTERM to a **signalfd**, armed once in `cmd_serve_on` *before the
listener exists* — the same placement, and for the same reason, as `signal_ignore(SIGPIPE)`. A handler
was rejected: it would need the `rt_sigaction` `sa_restorer` trampoline [ADR 0007](0007-fork-per-accept-concurrency.md)
already refused, and would import async-signal-safety constraints an fd does not.

- **poll** tests the fd once per sweep, then notifies and drains every live session before closing the
  listener.
- **fork** waits on `poll(2)` over {listener, signalfd}; on shutdown it closes the listener first so no
  new client can connect, then reaps children for a bounded grace window before exiting anyway. Bounded
  because a player parked in a door game would otherwise hold the operator's shutdown open forever.

Two things this cost, both worth recording because neither is obvious:
1. **`fork(2)` inherits the blocked signal mask.** Arming in the parent made every connection child
   unkillable (`SigBlk` carrying agora's mask, surviving SIGTERM) until the child branch learned to
   unblock and close the inherited fd.
2. **Blocking the signals is required on Linux and wrong on agnos** — mirshi delivers
   `pending AND NOT blocked`, so a blocked signal is the one it will never report.

  The pattern is worth stating plainly for the next structural change: **ask what the old model was
  silently providing, not just what the new code does.**
- **Negative** — the Descent proxy still blocks the sweep for as long as a player is in the MUD, stalling
  the other 63 sessions. Known, documented at `src/descent.cyr`, tracked as roadmap § 1.11.0 — **fixed at 1.11.0** ([ADR 0031](0031-descent-session-state.md)).
- **Neutral** — `AGORA_SERVE=epoll` is accepted and aliased to poll. A real epoll loop is a later
  optimisation; the sweep is a `sleep_ms(20)` tick on both platforms today.
- **Measured at 1.8.2** (`benches/serve-bench.py`; BENCHMARKS.md § Serve-level baselines): poll accepts
  **50 connections/s sequentially** — exactly one per 20 ms sweep, because the loop sleeps instead of
  waiting for readiness — and ~520/s with 8 concurrent connectors, against fork's ~4,100 / ~11,400. An idle
  session costs **12.6 KB** resident under poll and **~62 KB** PSS as a fork child. The same bench found
  every multi-part fork response stalled ~40 ms by Nagle against the client's delayed ACK; agora sets
  `TCP_NODELAY` on accepted sockets since 1.8.2 (a `read` on 500 posts: 41 → 3.4 ms). Under fork, a client
  that stops reading is disconnected within **two** send timeouts (the first timed-out write usually
  reports a partial count as success), pinned by smoke 31.

### Readiness and the fork child's lifecycle (added 1.11.0)

[ADR 0031](0031-descent-session-state.md) changes how both models wait. The poll loop no longer sleeps 20 ms per
sweep: on Linux it waits in one `poll(2)` over the listener, the shutdown signalfd and every session and MUD socket,
with a timeout of the next timer due (agnos, which has no `poll`, keeps the paced sweep). Sequential accepts went
from 50/s to ~8,400/s, and the 0–20 ms added to every command is gone. `AGORA_SERVE` now accepts `fork` and `poll`
only: `epoll`, silently an alias of `poll` until 1.11.0, is refused with exit 2, as is any other value. A fork
child waits in `poll(2)` on its socket and a signalfd of its own, so SIGTERM ends it cleanly (goodbye, door
checkpoint), and `PR_SET_PDEATHSIG` ends it if the parent dies; the parent signals its children at a clean
shutdown instead of leaving them to finish as orphans. The per-source cap weighed above was re-checked at 1.11.0:
agnos still has neither `getpeername` nor a peer address from `sock_accept`, so the reasoning stands (roadmap
§ Unscheduled).

## Relationship to ADR 0007

0007 is **not superseded** — its model still ships and is still the Linux default. But three of its
statements are now conditional, and one is load-bearing far beyond its own file:

1. **§ Alternatives rejected "(E) single-thread epoll event loop"** on the grounds that "every byte
   handler in `handle_client` would need a yield point." That refactor is exactly what 1.6.0 performed
   (`handle_client` became a driver over an extracted `process_rx`), and it cost one cut. The objection
   was reasonable at 0.8.0 and is now answered.
2. **§ Positive claimed audit findings M1 (bump-allocator growth) and M2 (global collision) closed "via
   address-space isolation."** Under poll that mechanism is gone: M1 regressed and was re-closed by ADRs
   0021/0022; M2 is re-closed differently, by the `sess_load`/`sess_save` context swap rather than by
   separate address spaces.
3. **§ Negative: "No shared state across sessions. Cannot, e.g., implement an in-memory who's-online list
   without IPC."** This is the load-bearing one. It is cited — often verbatim — by
   [ADR 0010](0010-persistent-universe.md), [ADR 0011](0011-chat-area.md),
   [ADR 0012](0012-chatbot-framework.md) and [ADR 0014](0014-async-shared-world-strategy.md) as the reason
   a feature was deferred, and echoed in `src/chat.cyr` and `src/ashes.cyr`.

   **Under poll, that premise is false** — all 64 sessions live in one address space — and on agnos it is
   *always* false. Nothing is broken by this: disk + `flock` remains correct, is still required for the
   fork path, and is what makes state survive a restart. But a deferral justified by "fork forbids it"
   now rests on a premise that holds on only one of two models, and each of those four ADRs deserves a
   re-read before its deferred feature is either built or re-declined. **A feature may not assume shared
   memory** while fork remains supported — but it may now be *considered*.

## Alternatives considered

- **Threads.** Rejected: agnos has no thread story agora can rely on, and it would put every door-game
  state machine under a concurrency contract it was explicitly designed not to need (ADR 0009).
- **Keep agnos serial, poll only on Linux.** Rejected — backwards. agnos is the target that most needs
  multiplexing (it cannot fork at all), and Linux is the one that already had a working answer.
- **Poll everywhere, drop fork.** Rejected: fork's crash isolation is genuinely valuable on the platform
  that can do it, and dropping it would have made 1.6.0 a much riskier cut. Keeping both is what allowed
  every 1.6.x regression to be diagnosed by comparing models — which is how the poll-mode Descent routing
  bug was found at 1.6.2.
- **A real epoll reactor instead of a 20 ms sweep.** Deferred, not rejected. The sweep is simple and its
  cost is negligible at 64 slots; epoll earns its slot when a deployment shows the latency matters.
