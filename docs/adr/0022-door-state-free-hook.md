# 0022 — The door-state free hook (`DD_FREE`)

> **Status**: Accepted
> **Date**: 2026-07-26

## Context

[ADR 0021](0021-per-command-scratch-arena.md) closed the per-*line* allocation
leak that the 1.6.0 poll multiplex exposed: a scratch arena reset once per
dispatched line. It explicitly left one class out, because the arena cannot own
it — **the door-game state objects and the three chat-bot couch states**. Those
live across many lines: a QUEST run spans a whole session, a Jabberwacky corpus
grows as you talk to it, and an Ashes empire persists between marches.

Under [ADR 0007](0007-fork-per-accept-concurrency.md)'s fork model that was
fine. Each connection was its own process, so a state abandoned at `quit` or at
disconnect died with the child; process exit *was* the free list. The 1.6.0 poll
model removed that: one process serves every session for the life of the server,
so every abandoned state stayed allocated. Measured at 1.6.2, driving
`play <door>` / `quit` cycles through a poll-mode server:

| Workload | Growth |
|---|---:|
| `play eliza` / quit cycles | 1,229 B per command, **linear** |
| `play jabberwacky` / quit cycles | 8,998 B per command, **linear** |

Linear in commands, forever. A Jabberwacky state alone owns seven buffers — the
learned corpus is the bulk — and the Handler's cable register is the largest
single state buffer in the tree.

The blocker was never the hook, it was the allocator. Cyrius `alloc()` is a bump
allocator with **no free**; a `DD_FREE` slot calling into it would have nothing
to call. The freelist module (`fl_alloc` / `fl_free`) has been declared in
`cyrius.cyml` since M6 and was, until this cut, called exactly zero times.

## Decision

**Door states move to the freelist, and the descriptor grows a `DD_FREE` slot.**

Three parts, all of them mechanical once stated:

1. **Ownership is explicit and per-module.** Every game's state block *and every
   buffer that block owns* is allocated with `fl_alloc` in that game's own
   module, and released by a `<prefix>_free(st)` written directly beneath its
   constructor in the same file. Ten games, ten free functions: `sl_free`,
   `pa_free`, `th_free`, `ez_free`, `py_free`, `qu_free`, `jw_free`, `ol_free`,
   `ash_free`, `decode_free`.

2. **`DD_FREE = 208`** on the door descriptor ([ADR
   0020](0020-door-descriptor-registry.md)), `DD_SIZE` 208 → 216. All ten games
   register one; `0` means "not freeable" and is honored at the call site like
   every other optional slot.

3. **Three release points**, which together cover every way a state is dropped:
   - `door_state_free()` — the `quit` path in `process_rx`, called *after*
     `door_save_on_exit` (which reads the state).
   - `session_door_free(s)` — from `session_release` and defensively from
     `session_reset`, for a player who **disconnects mid-game**. This one reads
     the state and game id **out of the slot, not out of the globals**: under
     poll the `g_*` globals belong to whichever session was last `sess_load`ed,
     so freeing through them would free another player's game.
   - the `play` launcher, before installing a replacement (a defensive guard —
     while you are inside a door, `play <other>` is fed to the *game*, so this
     is not reachable from the wire today).

The same pass moved the three chat-couch bot states (`SESS_ELIZA`,
`SESS_PARRY`, `SESS_JABBER`) onto the same footing — they are built by the same
constructors and were leaking identically.

**What deliberately stays on `alloc()`**: the shared world snapshot. A state's
`SL_WORLD` / `PA_WORLD` / `TH_WORLD` / `AE_WORLD` field points at the *session
slot's* buffer, not at memory the state owns, so every `*_free` steps around it.
Freeing it would corrupt the pool.

## Consequences

- **Positive** — the leak is not merely smaller, it is **bounded**. Total RSS
  growth across a run of `play eliza` / quit cycles:

  | Cycles | 1.6.2 | 1.6.3 |
  |---:|---:|---:|
  | 600 commands | 720 KB | 208 KB |
  | 2,400 commands | 2,460 KB | 203 KB |

  1.6.2 grows linearly; 1.6.3 is flat — the ~205 KB is one-time arena and
  freelist setup, not per-command. Jabberwacky, the worst case, went from
  8,998 B/command to 478 B/command before flattening.
- **Positive** — freed blocks are *recycled*: the next state is built out of the
  previous one's blocks, which is also what makes a bad free show up fast
  rather than lurking.
- **Negative** — agora now runs two allocators, and the invariant "a pointer
  from `alloc()` must never reach `fl_free`" is not enforceable by the compiler.
  The mitigation is structural: a game's construction and its free live in the
  same file, and every `*_free` is a flat list mirroring its constructor. A
  scan for mixed allocators across all ten modules is part of the release check.
- **Negative** — `DD_SIZE` grew by 8 bytes. The descriptor is built once per
  process, so this is noise.
- **Neutral** — freed memory returns to the freelist, not to the OS, so RSS
  plateaus rather than falling. That is the correct shape for a server.

## Alternatives considered

- **Extend the ADR 0021 arena to cover door states.** Rejected outright: the
  arena is reset every line, and a door state must survive thousands of them.
  This would have been a use-after-free on the second line of every game.
- **Reference-count the states.** Rejected: there is exactly one owner (the
  session), and the lifetime is already explicit at three call sites. Counting
  would add a field and a discipline to buy nothing.
- **Leave it, and cap sessions instead.** Rejected: the residue is bounded by
  how fast a player re-enters doors, but "bounded by human behavior" is not
  bounded — a script can `play`/`quit` in a loop, and the only model on agnos is
  the one that leaks.
- **Free at `session_reset` only** (when a slot is *reused*) rather than at
  release. Rejected: it holds every abandoned state until the pool wraps, which
  on a lightly-loaded server can be hours. Releasing promptly is strictly
  better, and reset keeps a defensive call anyway.
- **A single generic `door_free_state` in `main.cyr` that frees a state's
  pointer fields by walking the descriptor.** Rejected: it would need a
  per-game map of which offsets are owned pointers versus borrowed ones (the
  world pointer), i.e. exactly the per-game knowledge a `*_free` already
  encodes — but stored one file away from the constructor it must mirror.
