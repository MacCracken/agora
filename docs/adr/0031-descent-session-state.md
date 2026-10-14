# 0031 — Descent as a session state, readiness-driven serve loops, and option resync on return

> **Status**: Accepted
> **Date**: 2026-10-13 — 1.11.0

## Context

[ADR 0017](0017-descent-link-gateway.md) shipped the Descent link as a blocking call: `descent_run` dials the
MUD and runs a `poll(2)` shuttle until the visit ends. That shape fit fork-per-accept and broke under the
poll model ([ADR 0023](0023-dual-serve-model.md)), where one process owns all 64 sessions. 1.8.1 bounded the
damage and documented the rest (ADR 0017's amendment); roadmap § 1.11.0 holds four problems that share one
cause. Agora's loops wait by blocking, either on one socket or on a fixed sleep, rather than on whatever is
ready:

1. **A visit stalls everyone else.** Under poll (and always on agnos), every other session is frozen for the
   whole visit. A dead or blackholed endpoint costs up to 4 s per attempt (~8 s on agnos) inside the sweep.
2. **The poll loop sleeps.** It sleeps 20 ms per sweep instead of waiting for readiness, so it accepts at most
   50 connections/s in sequence (fork: ~4,100) and adds 0–20 ms to every poll-mode command (measured at 1.8.2,
   BENCHMARKS.md). `AGORA_SERVE=epoll` is accepted and silently means `poll`.
3. **Returning from a visit leaves the telnet state wrong.** The proxy is byte-transparent, so agora does not
   see the MUD's negotiation with the client. 1.8.1 reset agora's option state on return and re-announced. Under
   RFC 1143 a client ignores `DO` for an option it already has on, so the reset leaves agora believing NAWS and
   LINEMODE are merely requested while the client has them on. Since 1.8.1, a subnegotiation counts only for an
   agreed option, so every later size report is dropped. **Reproduced with GNU `telnet` against the real MUD**:
   - `read` wraps at 39 columns before a visit and comes back 200 columns wide after it, for the rest of the
     session;
   - a LINEMODE client in EDIT mode gets `WILL ECHO` back from agora and stops echoing locally, so the user
     types blind until Enter (the bug ADR 0029's echo hand-off exists to prevent).
4. **Fork children outlive a crashed parent.** If the parent dies, its children keep serving as orphans, nothing
   can count them, and a restarted server cannot see them (ADR 0007 deferred `PR_SET_PDEATHSIG`).

## Decision

**Every serve loop waits on readiness, and the Descent link is a session state those loops drive, not a call
that owns the process. On return, agora adopts the option state the client actually holds, learned by
watching the negotiation the proxy carried.**

### Descent as `MODE_DESCENT`

- `descent` opens the connection and returns at once, leaving the session in `MODE_DESCENT` with a phase:
  - **connecting** (Linux: a non-blocking `sock_connect`, finished when `poll(2)` reports the socket writable,
    failed on error / hang-up or after 4 s);
  - **proxying**.

  The bytes the client pipelined behind the `descent` line stay parked in the session's receive buffer and are
  the first thing forwarded, which replaces 1.6.5's `g_pipe_*` hand-off.
- `descent_pump` moves bytes once, without blocking, in both directions:
  - client to MUD, through the receive buffer as a one-chunk pending queue; the client is not read again
    until the MUD has taken it;
  - MUD to client, through the session's ordinary send path, read only while the poll tx queue has room for a
    whole chunk, so a slow reader slows the MUD read instead of overflowing.

  The poll sweep calls it for a session in `MODE_DESCENT`; the fork child calls it from its own wait loop.
  **One shuttle serves both models** (and agnos, whose reads are its non-blocking `sock_recv`).
- A visit ends on MUD close or error, 30 minutes of silence, or shutdown. Ending closes the MUD socket, says
  `-- back at the agora --`, resynchronizes the options (below), and returns to `MODE_COMMAND` with a prompt.
  Client bytes still pending for the MUD are dropped, not run as BBS commands. A client that disconnects
  mid-visit releases the slot, which closes the MUD socket.

### Option resync on return

- While proxying, a **passive observer** (pure, `telnet.cyr`) parses both directions for `WILL` / `WONT` /
  `DO` / `DONT` on every option. It treats an option as on once its owner said `WILL` and the other side `DO`
  (in either order), and off on any `WONT` / `DONT` — the state RFC 1143 converges to between two conforming
  peers.
- It also records the client's `SB NAWS` (the window it has now) and every LINEMODE `MODE` the client
  acknowledges. It starts from agora's own state at the moment of the `descent`.
- On return, agora sets its Q-state for every option to what the client holds, applies the observed window
  and mode, and negotiates **only the differences**:
  - `WILL` / `DO` for what agora wants and the client has off;
  - `WONT` / `DONT` for anything the MUD enabled that agora refuses;
  - the LINEMODE echo hand-off re-applied to the current mode.

  Nothing agora already knows (terminal type, SLC values) is thrown away.

### Readiness, not sleeps

- **Poll model (Linux)**: the sweep ends in one `poll(2)` over the listener, the shutdown signalfd, every
  session socket (`POLLIN`; `POLLOUT` while its tx queue holds bytes) and every Descent socket (`POLLIN` while
  the queue has room; `POLLOUT` while connecting or holding client bytes). The timeout is the next timer due
  (a chat tick, an idle reap, a connect deadline), at most 1 s, and 0 while a session has a parked remainder.
  **agnos keeps the 20 ms paced sweep**: it has no `poll`, and its connect blocks in the kernel (~8 s), which
  the 30 s redial cooldown still bounds.
- **`AGORA_SERVE=epoll` is rejected**: `agora serve` exits 2 and names the valid models. With a readiness wait
  over at most 130 descriptors, epoll would only add registration bookkeeping.
- **Fork child**: `handle_client` waits in `poll(2)` on its socket, its own shutdown signalfd and, during a
  visit, the MUD socket — instead of a blocking `read` with `SO_RCVTIMEO` wakeups.

### Fork-child lifecycle

- Each child sets `PR_SET_PDEATHSIG` to `SIGTERM` and exits at once if its parent is already gone (the
  fork-to-`prctl` race).
- `SIGTERM` / `SIGINT` reach the child through **its own** signalfd, so it leaves the way a poll session does
  at shutdown: a goodbye line, the door checkpoint, the MUD socket closed. 1.7.0's guarantee that an operator
  can kill any connection process still holds; it now leaves cleanly instead of mid-write. `SIGKILL` is
  unchanged.
- The parent remembers its children's pids. At a clean shutdown it signals them, then reaps them within the
  existing grace window, so both models end sessions the same way.

## Consequences

**Positive**

- Under poll (and on agnos) a Descent visit no longer freezes the BBS, and on Linux a dead endpoint costs the
  sweep nothing.
- Poll-mode commands are answered when they arrive rather than at the next 20 ms tick, and sequential accepts
  are no longer capped at 50/s.
- A return from the MUD keeps the window width, the LINEMODE mode and the echo arrangement the client actually
  has, so wrapping and line editing work after a visit as before it.
- Both models end a session the same way at shutdown, and a fork child no longer outlives its parent.
- The shuttle and the observer are each written once, for both models and all targets.

**Negative**

- More moving parts in the poll loop: a per-sweep `pollfd` array (≤ 130 entries) and a timer computation.
- The observer is an approximation of RFC 1143: a peer that violates the protocol mid-visit can leave the
  resync starting from a wrong belief. RFC 1143 itself recovers from that on the next exchange.
- On agnos the connect still blocks the sweep (bounded, and only while the MUD is unreachable), and the sweep
  is still paced: the kernel offers neither a non-blocking connect nor `poll`.
- Fork children now block `SIGTERM` / `SIGINT` into a signalfd, so smoke 28's 1.7.0 check (an empty blocked
  mask) becomes "the child exits on `SIGTERM`, with a goodbye".

**Neutral**

- The sigil identity hand-off (ADR 0017's deferred bite) is unaffected; the MUD still runs its own login.
- Accept-rate limiting stays unscheduled: agnos still has neither `getpeername` nor a peer address from
  `sock_accept` (re-checked at 1.11.0), so ADR 0023's reasoning holds.

## Alternatives considered

**Run the blocking proxy in a forked helper process, even under poll.** It would keep the old shuttle and
isolate the stall. But agnos has no `fork`, and agnos is the target that always polls.

**An epoll serve model.** At 64 sessions a `poll(2)` array rebuilt each sweep costs microseconds and needs no
add / modify / delete bookkeeping as sessions come and go or enter and leave a visit. The stdlib's epoll
wrappers would also mean a third serve model to test.

**Re-announce, but drop the 1.8.1 rule that subnegotiations count only for agreed options.** It would bring the
window back, but it reopens what 1.8.1 closed (a client setting state it never agreed) and does nothing for
LINEMODE's echo.

**Bounce every option (send `DONT` then `DO`) on return.** It would force fresh reports without tracking. But
it disables and re-enables options the client already has, and a client in LINEMODE EDIT would drop out of
EDIT mid-session.

**`SIGKILL` (or the default `SIGTERM` action) for orphans.** It is simpler, but loses every door's progress
since its last save; a parent crash should not cost players their game.
