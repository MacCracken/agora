# 0007 — Concurrent connections via fork-per-accept

> **Status**: Accepted
> **Date**: 2026-05-23

## Context

agora 0.7.0 ships with a single-tracking accept loop: `cmd_serve_on` calls `handle_client(cfd)` synchronously, so only one telnet client can be served at a time. The 0.7.0 security audit ([`docs/audit/2026-05-23-audit.md`](../audit/2026-05-23-audit.md)) raised two related MEDIUM findings that v1.0 cannot ship without closing:

- **M1 — bump-allocator memory growth in long-running serve.** Cyrius `alloc()` is bump-only (no `free()`); every connection accretes ~73 KB of session-scoped state (rxbuf 4 KB + line 4 KB + post 64 KB + subject + current_board + identity slots) and every `read` inside that connection adds ~100 KB (post_read scratch + replies_to ID array + reply scratch). 8 connections / hour reading 4 posts each leaks ~4.3 MB / hour; an internet-reachable deployment with steady traffic hits OOM in weeks.
- **M2 — `g_login_*` and `g_session_*` are globals.** The single-tracking loop makes them de facto per-session today, but any concurrent-accept story collides: client A's `login alice` writes `g_login_fp = alice_fp`, then client B's `login bob` overwrites before A replies with sig over A's nonce. Silent auth-bypass surface.

The audit explicitly co-scheduled M1 + M2 because the natural fix — concurrent accept — also forces the per-conn-state refactor.

Three load-bearing decisions:

1. **Concurrency primitive** — how do we fan out to many simultaneous connections?
2. **Memory model** — how do per-connection allocations get cleaned up?
3. **Zombie / signal handling** — once children exist, how do we keep the process table clean?

### Candidate concurrency primitives

- **(F) fork-per-accept** — kernel-isolated processes. Classical telnetd shape (BSD, GNU inetutils). Per-conn state inherits via copy-on-write; child exit returns everything to the kernel. Simple, well-understood by ops.
- **(T) thread-per-accept** — `thread_create` via cyrius `lib/thread.cyr` (SYS_CLONE-backed). Lower per-conn overhead (no exec, no CoW page faults), but every global needs explicit synchronization (M2's collision survives unless we refactor every shared slot anyway). Larger surface for concurrency bugs.
- **(E) single-thread event loop** — epoll + non-blocking sockets, one kernel thread multiplexes all connections. Lowest per-conn overhead. But adds an event-machine layer to every byte path; the M1 EOL / IAC state machine is already a state machine, stacking event-loop state on top doubles the surface.
- **(S) single-track + per-conn arena** — keep the accept loop sequential; switch handle_client locals to `fl_alloc`/`fl_free` for per-conn lifetime. Closes M1 only; M2 remains theoretical because no concurrency landed. Half a fix.

### Candidate memory models

- **(X) process exit handles cleanup** — pairs with (F). Children fork, do their work, `sys_exit`; the kernel reclaims everything atomically. No per-allocation tracking.
- **(Y) per-connection freelist arena** — explicit `fl_alloc` for per-conn-lifetime data + a tracked list freed at `sock_close`. Required if we go with (T) or (E); not needed for (F).
- **(Z) bump allocator with per-conn reset** — would require teaching cyrius `lib/alloc.cyr` to save / restore the brk watermark, which is a per-process invariant. Cross-cutting upstream change; out of scope.

### Candidate zombie reapers

- **(p) `waitpid(-1, NULL, WNOHANG)` loop before each accept** — explicit, portable, no signal-handler complexity. Drains any zombies that accumulated since the last accept iteration.
- **(q) `signal(SIGCHLD, SIG_IGN)` via `sys_rt_sigaction`** — Linux kernel auto-reaps. Smaller code surface but requires the sigaction trampoline, which cyrius has historically gotten wrong (per `lib/darshana.cyr` § "Avoids the rt_sigaction x86_64 sa_restorer trampoline trap"). Out of scope for this bite.
- **(r) `SA_NOCLDWAIT` flag on sigaction** — same sigaction surface as (q); same trampoline concern.

## Decision

**(F)** fork-per-accept for concurrency, **(X)** process-exit for memory cleanup, **(p)** non-blocking waitpid for zombie reaping. The accept loop becomes:

```
loop:
  while waitpid(-1, NULL, WNOHANG) > 0: continue   # drain zombies
  cfd = accept()
  pid = sys_fork()
  if pid == 0:                # child
    sock_close(sfd)           # don't hold listening fd
    handle_client(cfd)
    sys_exit(0)
  # parent
  sock_close(cfd)
  continue
```

Per-connection state stays in globals (`g_session_fp` / `g_session_handle` / `g_login_*` / `g_reply_*`) — fork makes them per-process automatically, no struct refactor. Per-call working buffers (post_read scratch, replies_to ID array) stay on the bump allocator inside the child — they get reclaimed at `sys_exit`.

**In scope**: fork-per-accept, waitpid reaper, child closes inherited listening fd, parent closes accepted cfd, child exits after handle_client returns.

**Out of scope**: per-arena allocators (not needed — kernel does the work), thread-per-accept (rejected — see Alternatives), epoll event loop (rejected — same), refactoring per-conn globals into a struct (not needed — fork isolates them), `prctl(PR_SET_PDEATHSIG, SIGTERM)` for orphan-on-parent-death (defer; the v1.0 deployment shape is "operator runs `agora serve` under a process supervisor").

## Consequences

### Positive

- **M1 audit finding closed.** Per-conn memory is owned by the child process and reclaimed atomically at `sys_exit`. Long-running deployments no longer accrete RSS.
- **M2 audit finding closed.** Globals are per-process post-fork. Two clients running `login` simultaneously each get their own `g_login_*` slots; no slot-collision surface.
- **No source refactor needed for the audit fix.** `handle_client` is unchanged; only the accept loop and zombie reaper grow new code. Smallest possible diff for the audit close.
- **Strong isolation by construction.** A bug in child A cannot crash child B or the parent (modulo kernel resource exhaustion). Aligns with the telnetd / classical-BBS deployment model that v1.0 targets.
- **Matches CLAUDE.md "trust boundary" framing.** Each connection is its own trust domain; isolating it at the process boundary is the natural shape.

### Negative

- **Per-connection fork cost.** ~1 ms on modern Linux for a 380 KB binary with CoW page tables. At v1.0 LAN scale (8-user fanout per the criteria) this is invisible; at 1000s of connections/sec it would matter. **Documented**: agora's v1.0 use is per-LAN small-N.
- **No shared state across sessions.** Cannot, e.g., implement an in-memory "who's online" list without IPC. Acceptable for v1.0 (no such feature is on the roadmap); v2.x pillar 4 (federation) introduces IPC concerns regardless.
- **Process supervision becomes more relevant.** Operator should run `agora serve` under systemd / runit / supervisord so that the parent crash kills all children. Acceptable — the v1.0 deployment story already assumes a supervisor.
- **CLI verbs (`post` / `list` / `read` / etc.) unchanged.** They run as a single process and don't benefit from concurrency. By design — they're operator scripts, not server paths.

### Neutral

- **Per-board `.lock` (`file_lock` / `flock`) is process-level on Linux**, so the M5-G claim+write critical section continues to serialize correctly across forked children. No change needed.
- **`O_EXCL` in `post_new` still de-dupes** the (rare) case where the flock is dropped and two children race for the same ID.
- **`g_motd_buf` / `g_store_buf` are read-only after startup**, so they share via copy-on-write across all children — no per-conn copy cost.
- The 0.7.0 audit's M4 finding (anonymous `enter` can spam-create boards) is **not closed by this ADR**. M4 needs an auth gate or rate limit; that's a separate bite. Filing as audit-followup.

## Alternatives considered

- **(T) thread-per-accept**: rejected because M2 only closes if we also refactor every shared global into a per-thread struct. fork closes M2 for free via address-space isolation. Threading also adds mutex bugs to the surface; we'd have to audit every global read/write for race-safety. fork avoids the whole class.
- **(E) single-thread epoll event loop**: rejected because every byte handler in `handle_client` would need a yield point. The M1 IAC parser is already a state machine over bytes; nesting an event-loop state machine over the line-buffer state machine doubles the cognitive load on every future bite. fork keeps `handle_client` as straight-line code.
- **(S) single-track + per-conn arena**: rejected because it only closes M1, not M2. The audit was explicit that both were co-scheduled. Doing half the work means we ship 0.8 with M2 still queued — and the moment any later cycle introduces real concurrency (1.x scaling work?), M2 reopens.
- **(Y) per-connection freelist arena instead of (X)**: not needed when paired with (F) — process exit is a strictly stronger free than `fl_free`. Would re-enter consideration if we ever switched to (T).
- **(q) `SIG_IGN` / (r) `SA_NOCLDWAIT`** auto-reap: rejected because cyrius's `lib/darshana.cyr` already documents the rt_sigaction trampoline trap on x86_64. Using `sys_waitpid(-1, NULL, WNOHANG)` from the accept-loop avoids the sigaction surface entirely and stays cross-arch-clean for the eventual aarch64 / macOS / Windows backends.

## Specifics

- **Fork point**: in `cmd_serve_on` (`src/main.cyr`), after `sock_accept` succeeds, before the child runs `handle_client`.
- **Child responsibilities**: close the parent's listening fd (`sock_close(sfd)`) so a child crash doesn't leak fds to grandchildren; run `handle_client(cfd)`; `sys_exit(0)` regardless of return value (the parent doesn't care).
- **Parent responsibilities**: close the accepted cfd (`sock_close(cfd)` — child has its own dup via fork); continue the accept loop.
- **Zombie reaper**: at the top of each iteration, loop `sys_waitpid(0 - 1, 0, WNOHANG)` until it returns ≤ 0. Drains any zombies that accumulated since the last accept. Non-blocking, so the loop exits immediately if no zombies are ready.
- **Error handling**: if `sys_fork` returns < 0 (resource exhaustion), parent closes cfd, logs the failure on stderr, and continues. Connection is dropped from the client's perspective; no recovery attempt.

## Followups

- **Audit M4** — anonymous `enter` can still spam-create boards in this model (each fork can mkdir). Needs an auth gate at `enter` or accept-loop rate limit. Not closed by this ADR.
- **Per-conn `g_login_started_ms` initialization** — currently a global initialized to 0 at process start. Post-fork, the child inherits 0, which is correct (no login in flight at connection open). No change needed.
- **`PR_SET_PDEATHSIG`** for orphan handling — defer until a real deployment hits the orphan-on-parent-crash scenario (process supervisor mitigates today).
- **Benchmark** — re-run `benches/bench_telnet.bcyr` after the change. Parser hot path is unaffected (fork happens before any IAC byte flows), so expect baseline-matching numbers.
