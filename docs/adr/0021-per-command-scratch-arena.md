# 0021 — The per-command scratch arena

> **Status**: Accepted
> **Date**: 2026-07-25

## Context

Cyrius `alloc()` is a bump allocator with no free. agora leaned on that
completely: 252 `alloc()` call sites outside `test.cyr`, and **zero** calls to
`free` or `fl_free` anywhere in `src/`.

Until 1.6.0 that was not a bug, it was the design. [ADR
0007](0007-fork-per-accept-concurrency.md) made every connection its own
process, so the arena died with the child at disconnect — "process exit is the
free list" was the memory model, and it closed two audit findings on purpose.

The 1.6.0 poll multiplex removed the premise without removing the pattern. One
process now serves every connection for the life of the server, so each
per-command buffer accumulates forever. Measured on 1.6.1, driving a mixed
command stream through a poll-mode server:

| Commands | RSS growth | Per command |
|---:|---:|---:|
| 400 | 2,988 KB | 7,649 B |
| 1,600 | 11,676 KB | 7,473 B |

Dead linear, and the shape is worse than the average suggests: a single door
line rendered a fresh `DOOR_FRAME_CAP + DOOR_FRAME_GUARD` (8 KB+) frame buffer,
and `read` allocated `POST_MAX_BYTES + 1024` (66 KB). A busy board leaks a
megabyte every few minutes and eventually NULL-faults — and poll is the **only**
serve model on agnos, which has no fork.

The upstream toolchain hit the same class of bug on its own side of the boundary
in the same window: cyrius 6.4.61 stopped `sock_accept` boxing a fresh
`Err(EAGAIN)` on every poll, a fix filed naming agora. That repaired the
stdlib's 40 B/poll share. This ADR is about agora's own.

## Decision

**One arena, reset once per dispatched line.** `src/arena.cyr` owns a 256 KB
region allocated once, a bump offset into it, and two functions:

- `cmd_alloc(n)` — hand out `n` bytes of command-lifetime scratch, 8-byte
  aligned. Falls back to plain `alloc()` if the arena is exhausted.
- `cmd_scratch_reset()` — set the offset back to zero.

`process_rx` calls `cmd_scratch_reset()` at the single point that dominates
every line dispatch — inside `if (eol != 0)`, before the mode switch — so it
covers command, door, chat, login and posting lines, in **both** serve models
(the fork worker drives `process_rx` too).

In scope: every buffer whose lifetime is one dispatched line. 60 call sites
converted across `main.cyr`, `board.cyr`, `account.cyr`, `chat.cyr` and
`door.cyr`.

Out of scope, and deliberately still on `alloc()`:

- Anything that outlives the line — the session pool, the per-session telnet
  buffers, the door descriptor registry, the operator MOTD, the CLI verbs.
- The ten door-game state objects and the three chat-bot states, which live
  across many lines and are freed by neither mechanism. They are a per-`play`
  residue, bounded by how fast a human re-enters doors rather than by traffic,
  and they need a `DD_FREE` hook per game — deferred to 1.6.3.

Two buffers that leaked per *session* rather than per command —
`g_uni_world` (8 KB) and `g_reply_subject` (264 B) — moved into `session_alloc`
instead. They were lazily allocated behind an `== 0` guard on a **process**
global, but `sess_load`/`sess_save` swap that global per session, so every new
session saw 0 and allocated again. Owning them in the pooled slot makes it 64
allocations total, ever.

`src/arena.cyr` is its own module because both entry points need it: `main.cyr`
and `test.cyr`, and the latter links `board.cyr` / `account.cyr` **without**
`main.cyr`.

## Consequences

- **Positive** — the per-line leak is gone, measured on the same store,
  back-to-back, 600–1,600 commands per run:

  | Workload | Before | After |
  |---|---:|---:|
  | `help` / `whoami` (no filesystem) | 34 B/cmd | 27 B/cmd |
  | door play (`quest`, a frame render per line) | 3,434 B/cmd | 389 B/cmd |
  | Eliza door (per-line render + bot state) | 4,035 B/cmd | 1,229 B/cmd |
  | `boards` / `list` (30-post store) | 13,343 B/cmd | 4,838 B/cmd |

- **Positive** — one invariant to check at review time ("does this buffer
  outlive the line?") instead of 250 free-site pairings.
- **Positive** — nothing persists across a dispatch by construction, which is
  the property the poll model needs: `sess_load`/`sess_save` bracket the whole
  dispatch, so a static holding state across one would silently cross sessions.
- **Negative** — a misclassified site is a use-after-reset rather than a leak,
  and Cyrius gives no compiler help. The mitigation is that the rule is
  mechanical and local: assigned to a `g_*` global or a session field → keep
  `alloc()`; a `var` consumed within the call → `cmd_alloc`.
- **Negative** — 256 KB of address space reserved for the arena whether or not a
  given deployment needs it. It is allocated lazily on first use, so CLI verbs
  that never call `cmd_alloc` never pay it.
- **Neutral** — the remaining growth on filesystem commands is **not agora's**.
  `dir_list` (`lib/fs.cyr:153`) allocates a 4 KB `getdents` buffer, a vec, and
  one `Str` per directory entry on every call, from the vendored stdlib where
  agora cannot redirect it. That is the whole of the 4,838 B/cmd residue above,
  and it scales with directory size. The fix is a cyrius-side `dir_list`
  variant that writes into a caller-supplied buffer — an upstream ask, the same
  shape as 1.4.5's `sock_set_send_timeout`.

## Alternatives considered

- **`fl_alloc` / `fl_free` at each site.** The freelist module is already
  declared in `cyrius.cyml` and CLAUDE.md prescribes it for "data with
  individual lifetimes". Rejected: every one of these buffers has the *same*
  lifetime, so pairing each with an explicit free adds 250 opportunities to get
  it wrong — a missed free leaks exactly as before, an early free is a
  use-after-free — for no expressive gain. It also introduces a two-allocator
  invariant (never pass an `alloc()` pointer to `fl_free`) that Cyrius cannot
  enforce.
- **Function-scope fixed arrays (`var path[512]`) at each site.** Genuinely
  attractive for the ~32 path buffers, and there is in-repo precedent
  (`wager.cyr` `var buf[8]`, `door.cyr` `var tmp[24]`). Rejected as the primary
  mechanism because it does not scale to the large buffers — a `var
  buf[66560]` per `read` arm is exactly the "heap-allocate large buffers"
  warning in CLAUDE.md — so it would have meant two mechanisms and a
  size-threshold judgment at every site instead of one rule.
- **Dedicated lazily-filled file-scope statics per call site.** Equivalent
  memory behavior, but each new static is process-lifetime state that must be
  proven never live across a dispatch, and there would be ~30 of them. The
  arena gets the same result with one object whose reset point is explicit.
- **Do nothing under fork, refuse `poll` for long-running servers.** Rejected:
  poll is not optional on agnos, and 1.6.0 already shipped it as the
  concurrency story.
