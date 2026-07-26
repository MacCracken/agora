# 0023 — The dual serve model: fork per accept, or one process polling all sessions

> **Status**: Accepted
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

- **`AGORA_SERVE=fork`** — ADR 0007's model, unchanged. The Linux default.
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
  non-blocking recv → `process_rx` → non-blocking tx drain.
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
     *everyone*. Fixed across 1.6.2–1.6.5 (SIGPIPE ignored, send returns checked, the Descent write
     bounded).
  3. **A crash cost one connection.** Under poll it costs all 64.
  The pattern is worth stating plainly for the next structural change: **ask what the old model was
  silently providing, not just what the new code does.**
- **Negative** — the Descent proxy still blocks the sweep for as long as a player is in the MUD, stalling
  the other 63 sessions. Known, documented at `src/descent.cyr`, tracked as roadmap § Cross-repo.
- **Neutral** — `AGORA_SERVE=epoll` is accepted and aliased to poll. A real epoll loop is a later
  optimisation; the sweep is a `sleep_ms(20)` tick on both platforms today.

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
