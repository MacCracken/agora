# 0009 — Door / games subsystem architecture

> **Status**: Accepted
> **Date**: 2026-06-07

## Context

agora opens a "door" surface at 1.1.0: text games that run inside a telnet session, in the classic BBS-door tradition. Three games ship on it — **Smuggler's Ledger** (a buy-low/sell-high contraband run, homage to the Drug Wars/Dope Wars style with abstract goods), **Port Authority** (space trade + combat, homage to the TradeWars 2002 style with re-themed commodities), and **The Handler** (a Cold-War espionage-deduction game from its own v1.0 design spec). Each supports three play modes — **Practice** (ephemeral, anonymous-OK), **Solo** (login-gated persistent save), and **Universe** (shared multiplayer world, roadmapped/stubbed at 1.1.0).

Several forces shape the design, surfaced by a full read of the session machinery (see `docs/development/state.md` source-surface map):

1. **Where does game state live, and how does input reach a game?** The telnet loop is server-side char-at-a-time with a per-line `mode` dispatch (`SessMode`). `login` already parks a sub-mode (`MODE_LOGIN_AWAIT_SIG`) and routes the next line to a dedicated branch — the precedent for any interactive sub-flow.
2. **No seedable PRNG exists.** The stdlib offers only the kernel CSPRNG (`getrandom`/`/dev/urandom`), which is non-reproducible — wrong for games that must store a seed (replayable Solo runs) and be unit-tested with a known stream.
3. **No integer min/max/clamp/abs/pow.** `lib/math.cyr` is f64-only and not in `cyrius.cyml` deps; game economy must be pure-integer for determinism and cross-arch reproducibility.
4. **ESC is dropped at input ingress** (`input_byte_ok`), so no arrow keys / ANSI input reach a handler. Door UIs must be single-key + Enter.
5. **The Handler's spec assumes a *traditional* DOS/Mystic-style BBS** that execs external door binaries (DOOR.SYS / DORINFO1.DEF drop files, optional SQLite). agora is itself the BBS — a single in-process Cyrius telnet server — so those interop mechanisms have no counterpart here and must be adapted, not literally implemented.

## Decision

**Each game is a pure state-machine module; `main.cyr` owns all socket I/O and persistence.** A game module (`src/smuggler.cyr`, `src/port_authority.cyr`, `src/handler.cyr`) renders frames into a caller-supplied buffer and consumes one input line at a time, never calling `send_buf` or touching files itself — exactly like `render_motd`. The shared framework lives in `src/door.cyr`. Wiring into the session is a new `MODE_DOOR` sub-mode plus a `play` command, following the `login` precedent.

In scope at 1.1.0: the `door.cyr` framework, the three games' Practice + Solo experiences to full single-player feature depth, and a shared **standings file** (first use of the flock'd shared-disk pattern, for The Handler). Out of scope (roadmapped): the Universe (shared-world multiplayer) mode for all three, leaderboards beyond The Handler's standings, and The Handler's v2 community layer (inter-player sabotage, intercepted rival traffic, world-event track, legacy ranks) per its own spec cut-line.

### Specifics

- **PRNG** — xorshift64 over a single i64 cell (`rng_seed`/`rng_next`/`rng_below`/`rng_range`/`rng_chance`). Shifts + xor only, so it sidesteps signed-multiply and 64-bit-literal-range concerns. Seeded from `clock_now_ns()` for Practice; the seed is stored in the Solo save for replayable runs and pinned in tests. Not cryptographic — games only.
- **`lshr` helper** — arithmetic-shift-then-mask, correct whether cyrius `>>` is arithmetic or logical (verified by test t83).
- **Storage** — `<store>/.users/<fp16>/games/<game>.sav`, under the dot-prefixed `.users/` tree so it dodges board/post enumeration like account files. `game_name_valid` (board-name alphabet) is the *only* traversal guard on the filename; save read/write re-validate `fp16_valid` + `game_name_valid` at the boundary. Single-owner saves use plain `O_TRUNC` writes (no flock); shared world/standings state uses `file_append_locked`.
- **The Handler adaptations** — drop files → native sigil identity (`g_session_fp`/handle); SQLite → flat files; the 2400-baud slow-print + spacebar-skip teletype effect → instant render at 1.1.0 (the server's char-at-a-time + line-mode model makes mid-print skip awkward; the fixed cable *frame* carries the dread); daily turn rhythm → UTC day-rollover via `chrono` (`epoch/86400`), sysop-config 1–3 turns/day; ANSI default with a plain-text fallback. The mole/cross-reference deduction is backed by a consistent internal truth model so discrepancies are procedurally generated *and* genuinely solvable, all logged in a persistent Registry; honest-error false positives come from the Reliability stat.

## Consequences

- **Positive** — Game logic is socket-free and filesystem-free, so the whole economy/event/deduction core is unit-testable without binding a port (matches "pure is testable; I/O is wired"). New games are a new `src/<game>.cyr` + one `include` + one `MODE_DOOR` registration; no manifest change. Seedable PRNG makes Solo runs replayable and tests deterministic.
- **Negative** — A game cannot block on its own `read()`; every interactive prompt must yield back to the `handle_client` loop and resume via `MODE_DOOR`, so multi-step game flows are written as explicit sub-states, not straight-line code. No animated teletype at 1.1.0. Pure-integer economy means no fractional prices without fixed-point.
- **Neutral** — Game state hangs off one `g_door_*` pointer to a heap struct (per-connection via fork-per-accept, ADR 0007); it inherits the same "globals are per-session only because the accept loop forks" caveat as `g_session_*`. Universe mode, when pulled, must persist shared state to disk + flock — it cannot use in-memory globals (ADR 0007 § Negative).

## Alternatives considered

- **Games call `send_buf`/file I/O directly (impure modules).** Rejected — it would make the economy untestable without a socket, fight cyrius include-ordering (games would reference `main.cyr` symbols defined after their include), and scatter path-safety across modules. The pure-module split keeps the one traversal guard and all I/O in `door.cyr` + `main.cyr`.
- **Use the kernel CSPRNG for game randomness.** Rejected — non-reproducible: no replayable Solo days, no fixed-dice regression tests, no stored-seed re-simulation. A deterministic PRNG is mandatory for The Handler's solvable-mole requirement.
- **Add `lib/random.cyr` / `lib/math.cyr` to deps.** Rejected — `random.cyr` is still a CSPRNG (see above) and `math.cyr` is f64-only; both would add stdlib surface we don't use. A ~30-line in-module PRNG + integer helpers is smaller and exactly fit.
- **Literally implement DOOR.SYS / DORINFO1.DEF + SQLite for The Handler.** Rejected — agora does not exec external doors; there is no host BBS to write a drop file. Native sigil identity + flat files are the faithful adaptation. (If a *standalone* door binary runnable under other BBS software is ever wanted, that is a separate deliverable, not part of agora's in-process session.)
