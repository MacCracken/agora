---
name: agora State
description: Live state snapshot for the agora repo — volatile data refreshed every release
type: state
---

# agora — State Snapshot

> **Last refresh**: 2026-10-13 — **1.11.0 (Descent as a session state + serve-model debt) cut**: a Descent
> visit is a session state both serve models drive (it no longer freezes the poll server), the return
> resyncs the telnet options from what the client agreed during the visit, the poll loop waits on readiness
> (accepts 50 → ~8,400/s), `AGORA_SERVE` takes `fork` | `poll` only, and fork children leave with their
> parent. ADR 0031. **Replace this paragraph each
> release — do not append to it.** History lives in [`CHANGELOG.md`](../../CHANGELOG.md) and git.

Per [first-party-documentation § CLAUDE.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#claudemd), CLAUDE.md holds **durable rules**; this file holds **volatile state**. If a claim drifts within a minor's worth of work, it belongs here, not in CLAUDE.md.

---

## Next-session boot guide

1. **Where we are**: see § Version and § In-flight slot below.
2. **Where to read first**: this file, then [`roadmap.md`](roadmap.md) — the release plan (1.8.x → 1.12.x
   slots) is the single authoritative open-work list. Then the newest file in [`docs/audit/`](../audit/).
3. **What to build / test**: `CYRIUS_DCE=1 cyrius build src/main.cyr build/agora`; `cyrius test` (every
   `tests/*.tcyr`); `cyrius fuzz fuzz/telnet_iac.fcyr` and `fuzz/term_wrap.fcyr`; `docs/examples/run.sh` (the smokes, both serve
   models); `cyrius audit` (must exit 0); `benches/serve-bench.py all`; `scripts/check-version-sync.sh` and
   `scripts/check-toolchain.sh` before a cut. CLAUDE.md § Quick Start lists them all.
4. **What NOT to do**: don't commit / push (the user owns git); don't use `gh`; don't bump versions
   unprompted; demo handles are three-letter arcade names (`qix`, `pac`, `zax`, `dig`, `jst`), never
   `alice`.
5. **Traps a next session must not relearn** (each cost a cut to find; detail in the CHANGELOG entry named):
   - **Signals differ by target** [1.7.0]: blocking is *required* on Linux and *wrong* on agnos (mirshi
     delivers `pending AND NOT blocked`), and the sigset bit convention is off by one between them. A
     fork child inherits the blocked mask — every child calls `shutdown_signals_child_reset` first.
     agora's shutdown signalfd is hand-rolled **on purpose**; darshana's would block on agnos [1.8.0].
   - **`send_buf` ignores its fd in poll mode** — a write to a second socket (Descent) must bypass it.
     `send_buf` also carries protocol commands, so IAC doubling and sanitizing live in `send_text`,
     never in `send_buf` [1.6.4, 1.8.0].
   - **A stored 0xFF now renders `?`, not `IAC IAC`** — the sanitizer runs before the IAC pass; smoke 26
     pins it [1.8.0].
   - **The ingress filter must keep TAB / CR / LF** — it runs *before* EOL detection [1.6.5]. Echo is
     gated `!= Q_NO`, never `== Q_YES` (that breaks every client that never answers our WILL) [1.6.5].
   - **Allocator discipline is per command, not per arm** — converting a command's *arm* to the arena is
     not converting the command [1.6.3]; and a bare `alloc()` inside a *vendored stdlib* function is
     invisible to a `src/`-only grep (`dir_list`, `file_write_atomic`) — read the stdlib body before
     putting it on a per-line path [1.6.7, 1.7.0].
   - **Every `flock` is on a separate `.lock` file** — required, because `file_write_atomic`'s rename
     replaces the inode [1.7.0].
   - **`main.cyr` is testable since 1.8.2** — `tests/serve.tcyr` includes it under `#define AGORA_TEST`
     (its entry point is `#ifndef AGORA_TEST`). The module suite (`tests/agora.tcyr`) still does not.
   - **Never `+` two string literals** — Cyrius has no string concatenation; `+` adds the POINTERS. Split a
     long literal into two consecutive emit/send calls (and mind a capped emitter, `emit_cstr`, which writes
     all-or-nothing).
   - **Don't edit a shell script while bash is running it** — bash reads it incrementally; the 1.8.2 runner's
     first summary line was garbled that way.
   - **Verify a toolchain snapshot against its tag** before trusting a size or bench number —
     `~/.cyrius/versions/<ver>` can be a dirty working tree [1.6.7].
   - **The arena is a budget, not a free list** [1.8.1]: past 512 KB in one command every `cmd_alloc`
     silently becomes a leaking bare `alloc()`. Never `cmd_alloc` inside a per-post / per-user loop —
     use the stack. **Prove a command bounded with a poll-mode heap A/B** on a big store; reading the
     source missed both 1.8.1 HIGHs (vendored allocations, and per-iteration arena use).
   - **The stdlib can change a primitive's blocking behaviour under you** [1.8.1]: cyrius 6.6.7 made the
     agnos socket `sys_write` retry for up to 30 s, which silently broke `session_drain`'s bound at the
     1.8.0 pin move. On a toolchain bump, re-read the bodies of the syscall wrappers the serve loops use.
   - **Poll fairness is a per-sweep line budget** [1.8.1]: `process_rx(s, start, n, budget)` parks the
     rest of a recv in the slot. Anything new that dispatches lines must count against it.
   - **Door saves happen on every close path** [1.8.1] (`session_door_checkpoint`), a finished run
     removes its save, and a per-identity play lock (`<game>.lock`) guards each saved game.
   - **This file and `roadmap.md` are refreshed by hand**, but since 1.8.2 CI fails if they do not name
     VERSION (`scripts/check-version-sync.sh`) — 1.6.6 and 1.7.1 both shipped without either recording them.
   - **Store files go through `store_open`** [1.9.0] (`arena.cyr`: `store_read_all`, `store_lock_open`,
     `store_append_locked`) — never `file_read_all` / a plain `file_open` on a store path, or a FIFO there
     hangs the poll server. A file that is *claimed* (a post, a handle) is created with `store_publish`
     (temp + fsync + `link`); one that is *replaced* (a save, the world, chat) with `store_write_atomic`.
   - **Fork-mode PSS depends on the binary's filesystem** [1.9.0]: the same build measures 54 KB per child
     from tmpfs (`/tmp`) and 62 KB from ext4. Run A/B builds from the same filesystem.
   - **`pkill -f <pattern>` can match the shell running it** — the pattern is in its own command line, and
     it kills the session's shell. Use `pgrep -a` to look, then kill by pid.
   - **Two indexes trust their own silence** [1.9.0, 1.9.1]: `.users/.by-handle/` and `<board>/.replies/`,
     each with a `.complete`. Anything written into the store by hand (a user dir, a post) is invisible to
     them until the index directory is deleted; the next `serve` rebuilds it. Both verify what they DO name.
   - **`is_dir` takes a `Str`, not a cstring** [1.9.0] (`path_str(p)`), and answers 0 for anything else —
     silently. Use `store_is_dir` / `store_name_exists` for cstring paths.
   - **A FIFO left in a test store hangs the next run** — the stdlib's directory listing opens with plain
     `O_RDONLY`. Tests unlink what they `mknod`; `t_rmtree` unlinks before it lists.
   - **A 16-hex `.admins` entry is a fingerprint, never a handle** [1.9.2] — handles may be 16 hex digits,
     and matching both ways lets anyone register an admin's fingerprint as a handle. Keep the split strict.
   - **`match` and `mod` are reserved words** — and `print(lit, N)` with a hand-counted N goes wrong silently
     (a stray byte); the 1.9.2 CLI uses `cli_put` (strlen).
   - **Echo depends on LINEMODE** [1.10.0]: with EDIT on, agora says WONT ECHO and the client echoes. Raw-socket
     smokes never agree LINEMODE, so they still see server echo — a smoke that agrees it must expect none.
   - **A subnegotiation counts only for an agreed option** [1.8.1] — a test or fuzz input that frames an SB
     without agreeing the option first is silently dropped and exercises nothing (the fuzz harness did this
     from 1.8.1 to 1.10.0).
   - **Telnet replies are queued whole or not at all** (`ts_tx_push_all`, `ts_tx_room`) [1.10.0] — never push a
     multi-byte unit byte by byte.
   - **A Descent visit is a session state** [1.11.0, ADR 0031]: while `MODE_DESCENT`, the session's receive
     buffer (`SESS_RX_OFF..SESS_RX_LEN`) holds client bytes owed to the MUD — they are NOT a parked
     remainder (the sweep must not treat them as one, or the wait spins) and never run as BBS commands. The
     readiness wait must not watch a socket the pump will not read (client while bytes are pending; MUD while
     the client's queue is full), or it spins.
   - **Fork children keep SIGINT / SIGTERM blocked on purpose** [1.11.0]: drained by their own signalfd
     (`fork_child_arm`), which every wait in a child must include. On agnos a raw `syscall(7)` is `SYS_OPEN`:
     every poll is behind an agnos guard.
   - **`send_wrapped` sanitizes its buffer in place** [1.10.1] — so the wrap measures what the reader sees. Pass it
     scratch only (a stack row, an arena copy), never a literal or a buffer read again afterwards; trusted
     wire-ready bytes (a door frame, a literal) go with `TW_RAW`, which touches nothing. A raw-socket smoke sends
     no NAWS, so it never sees wrapping — one that agrees NAWS must expect it.

---

## Version

| Field | Value |
|---|---|
| **Released** | `1.11.0` (2026-10-13) — Descent as a session state, readiness-driven serve loops, option resync, fork-child lifecycle. Previous: `1.10.1` (2026-10-13) — terminal-aware output |
| **In flight** | none — next is **1.11.1** (enforced module invariants), see § In-flight slot |
| **Toolchain pin** | cyrius `6.7.9` (`cyrius.cyml [package].cyrius`; local snapshot verified byte-identical to the tag at 1.8.0; a 1.8.1 clean `cyrius deps` regenerated an identical `lib/`) |
| **Source of truth** | `VERSION` at the repo root |

## Build artifacts

| Artifact | Size (1.11.0) | Build line |
|---|---|---|
| `build/agora` | **1,042,240 B** (+12,656 vs 1.10.1) | `CYRIUS_DCE=1 cyrius build src/main.cyr build/agora` |
| `build/agora-agnos` | 1,034,704 B | `CYRIUS_DCE=1 cyrius build --agnos src/main.cyr build/agora-agnos` |
| aarch64 | 2,483,832 B (aarch64 ELF does no DCE compaction; its segments align to 64 KB, so it grows in steps — +17,464 B of code at 1.10.1 moved the data segment one step) | `cyrius build --aarch64 …` |

The release workflow publishes all three (`agora-<ver>-x86_64-linux`, `-aarch64-linux`, `-x86_64-agnos`)
with `SHA256SUMS` since 1.8.2.

Size history worth knowing: 14.57 MB at 1.6.6 → 2.01 MB at 1.6.7 (bundled sigil dropped ~12.6 MB of
banked `.bss` — not a DCE win) → 0.97 MB at 1.7.1 onward. `CYRIUS_DCE=1` NOP-fills dead code and keeps
all `.bss`; the build still warns `large static data` (≈375 KB).

## Tests + benchmarks

| Surface | Status (1.11.0) |
|---|---|
| `tests/agora.tcyr` | **254** module tests (src/test.cyr until 1.8.2) — also 254/254 under `cyrius test --aarch64` (qemu) |
| `tests/serve.tcyr` | **12** serve-layer tests (src/main.cyr over a socketpair; new at 1.8.2, mutation-checked) — also under qemu |
| `fuzz/telnet_iac.fcyr` | green plain, `--poison` and `--poison=ab` (CI runs plain + `ab` since 1.8.2); since 1.10.0 it agrees the client options before its structured subnegotiations, checks for torn replies, and drives 656 targeted LINEMODE frames |; since 1.11.0 a sixth pass drives the Descent negotiation observer (3,000 visits in split pieces, guard band) and the return resync (invariants 24 / 25)
| `fuzz/term_wrap.fcyr` | new at 1.10.1: the word wrap — 6,000 adversarial texts (6.1 MB) each wrapped four ways, seven invariants (nothing but whitespace dropped, breaks only at whitespace, no escape sequence split — by its own parser, chunk-size independence, rows within the width, identity when everything fits, no runaway); green plain and `--poison=ab`, in CI and release |
| `docs/examples/` | **37** smokes; `run.sh`: both CI legs green at 1.11.0 (**fork 25/25, poll 36/36**); CI runs it per model |
| `benches/bench_telnet.bcyr` · `bench_term.bcyr` | 5 parser benchmarks · 4 word-wrap benchmarks (1.10.1) — [`BENCHMARKS.md`](../../BENCHMARKS.md) |
| `benches/serve-bench.py` | accept rate, per-session memory, world lock, reply (`read` with and without replies; 1.9.1 index), unknown-handle login + first-start time (1.9.0) — BENCHMARKS.md § Serve-level baselines |
| `cyrius audit` | **exit 0** since 1.8.2 — fmt, lint (0 warnings), docs (every function documented), tests, bench — and a CI gate |

## In-flight slot

**None.** 1.11.0 is cut. Next is **1.11.1 — enforced module invariants** (ADR 0022's borrowed
world-snapshot pointer, the chat-couch bot ABI, ADR 0020's per-slot smoke obligation turned into a test).
See roadmap § 1.11.1.

## Recent shipped

- **1.11.0** (2026-10-13) — the Descent as a session state (a visit no longer freezes the poll server), the
  option resync on return (window width and LINEMODE echo survive a visit), readiness-driven poll loop (accepts
  50 → ~8,400/s), `AGORA_SERVE=epoll` refused, fork children leave with their parent. 266 tests, 37 smokes.
- **1.10.1** (2026-10-13) — terminal-aware output: door frames, `list`, `read`, chat and `help` wrapped to the
  NAWS width (byte-identical without one); `src/term.cyr` + a second fuzz harness; `list` under fork 16.2 →
  4.2 ms on 300 posts. 262 tests, 36 smokes.
- **1.10.0** (2026-10-13) — telnet conformance: DO LINEMODE + MODE / SLC answered + echo hand-off, AYT, a line
  editor for character-mode clients, NVT egress; the fuzz harness drives subnegotiation payloads again and
  found an SLC stack overflow before release. 257 tests, 35 smokes.
- **1.9.2** (2026-10-13) — board policy that means something (`known` members-only, `anon` anonymous
  posting), `.admins` by fingerprint (audit I9), `agora policy` / `agora admins`, chat channel cap (I10), the
  slot risk recorded. Closes the 1.9.x line. 249 tests, 34 smokes.
- **1.9.1** (2026-10-13) — the reply index: `read` 23.7 → 0.18 ms at 4,096 posts for a post with no replies,
  29.4 → 2.5 ms for a 409-reply thread; replies older than the newest 4,096 posts listed at last; a FIFO where a
  directory belongs no longer hangs the server. 246 tests, 33 smokes.
- **1.9.0** (2026-10-13) — durable posts + store hardening: store opens refuse symlinks and non-regular
  files (audit I11 — a FIFO hung the whole poll server), crash-safe post publish (temp + fsync + `link`),
  the handle index (unknown-handle login 16.98 → 0.16 ms at 3,000 users), `.admins` read to the end.
  244 tests, 32 smokes.
- **1.8.2** (2026-10-13) — tooling: the Closeout Pass in CI (smokes under both models, aarch64, audit,
  version / toolchain checks), `tests/serve.tcyr`, generated version string, serve-level baselines, and a
  ~40 ms Nagle stall fixed under fork, and a fork child no longer outlives a non-reading client by two
  extra send timeouts. 239 tests, 31 smokes.
- **1.8.1** (2026-10-12) — code audit + repair: poll fairness (16 pipelining clients: 13.7 s → 22 ms for a
  bystander) and unauthenticated heap growth (listings, login, `list`/`read` on big boards → 0 B/command);
  fail-closed `.policy`/`.admins`; door saves on every close path + a play lock; loader bounds; Descent
  visit bugs; fork connection cap. 232 tests, 30 smokes.
- **1.8.0** (2026-10-12) — cyrius 6.6.2 → 6.7.9 + darshana 0.9.0 → 1.3.0; stored text sanitized at
  egress (C1 via the wire, anything via the CLI, reaching readers' and the operator's terminals); 225 tests.
- **1.7.1** (2026-09-11) — cyrius 6.5.34 → 6.6.2, the `Result` value-form migration.
- **1.7.0** (2026-08-22) — clean shutdown (signalfd, both serve models), crash-safe door / world / chat
  writes, both poll holes, the IAC fuzz harness.

Everything earlier: [`roadmap.md`](roadmap.md) § Shipped (one row per release line) and `CHANGELOG.md`.

## Consumers

None. agora is a binary (telnet server), not a library. The v2.x self-distribution pillar would make it a
distribution channel for the rest of AGNOS, at which point downstream verification becomes load-bearing.

## Verification hosts

| Host | Role | Status |
|---|---|---|
| Workstation (Linux x86_64) | primary dev + smokes | ✅ active |
| archaemenid (iron NUC, AGNOS) | 1.0 release-gate validation | ✅ validated 2026-05-23 (criteria #3 + #4) |
| aarch64 | cross-arch | qemu-user in CI since 1.8.2 (build + both suites); no hardware run |

## Dependencies

| Dep | Used for | Version | Notes |
|---|---|---|---|
| cyrius stdlib | everything | 6.7.9 | 25 named modules (`cyrius.cyml [deps].stdlib`); `lib/` is generated, never committed |
| **darshana** | SGR composers + egress sanitizer | **1.3.0** (git dep, frozen v1 API) | `tty_sgr_buf`, `tty_sgr_reset_buf`, `tty_sanitize_buf`; termios / signalfd surface deliberately unused |
| **sigil** | Ed25519 + SHA-256 + hex (auth) | 3.13.11 (bundled in the 6.7.9 stdlib) | vendored copy warns about `hash_file_into`'s static 256 KB buffer under 6.7.x — not agora's, flagged upstream |
| bannermanor | MOTD banners | 1.0.1 | output baked into the MOTD at M2-A; the crate is not a build dep |
| kii / sankoch | M3 inline images / M4 stored-file deltas | — | gates met, no consumer; nothing in `src/` references them |
| agnos ext4 WRITE | AGNOS-target storage | in flight upstream | not blocking (ADR 0001) |

## Source surface (1.11.0, lines)

| File | Lines | Holds |
|---|---:|---|
| `src/main.cyr` | 5,650 | argv dispatch + CLI verbs; both serve models (fork / poll; readiness waits, the fork child's signalfd + PDEATHSIG), session pool + context swap; `process_rx` line dispatch + the poll line budget; login flow; send path (`send_buf` / `send_text` / `send_wrapped` / `write_text`); door / chat glue; the Descent as a session state (`descent_begin` / `descent_pump` / `descent_leave`); door save lifecycle; N1 shutdown |
| `src/telnet.cyr` | 1,249 | RFC 854 IAC parser (AYT, EC / EL events), RFC 1143 Q-method, NAWS / TERMINAL-TYPE subnegotiation, RFC 1184 LINEMODE server side (MODE + echo hand-off, SLC, FORWARDMASK refused) — only for agreed options; the Descent negotiation observer + return resync (1.11.0) |
| `src/term.cyr` | 448 | terminal-aware output (ADR 0030): display width (UTF-8, wide / zero-width, TAB stops, escape sequences) and the resumable word-wrap state machine `send_wrapped` drives |
| `src/board.cyr` | 1,956 | post storage + RFC-822 headers (PostHeaders ABI), boards, threading + the reply index (ADR 0027), policy modes + read gate (ADR 0028) / admins (fail closed; streamed; fingerprint entries), `flock` helpers, the directory workspace (`store_dir_scan`, FIFO-guarded), egress sanitize rule (ADR 0024) |
| `src/account.cyr` | 799 | fingerprint, handle validation, user dirs, keyfiles, nonce / signature parse, From-header extraction, the register lock, the handle index (ADR 0026) |
| `src/arena.cyr` | 364 | per-command scratch arena (ADR 0021), the store file primitives: `store_write_atomic`, `store_open` / `store_read_all` / `store_lock_open` / `store_append_locked`, `store_publish` (ADR 0025) |
| `src/door.cyr` | 835 | door framework (ADR 0009): PRNG, saves (+ remove / quarantine / play lock), world transactions, leaderboards, `emit_*` render, descriptor registry (ADR 0020), `DD_FREE` (ADR 0022) |
| `src/smuggler.cyr` · `src/port_authority.cyr` · `src/handler.cyr` | 1,335 · 1,679 · 1,437 | the three 1.1.0 doors + their 1.2.0 Universe layers |
| `src/quest.cyr` · `src/olympiad.cyr` · `src/ashes.cyr` | 950 · 1,017 · 1,347 | QUEST (LORD homage), Olympiad (`compete()`), Ashes of Empire (async shared-world strategy) |
| `src/decode.cyr` · `src/decode_words.cyr` | 756 · 36 | Decode engine (Mastermind / Wordle) + the 532-word list |
| `src/wager.cyr` | 311 | shared wagering primitive (ADR 0013) |
| `src/chat.cyr` | 451 | chat area ring transcript (ADR 0011) |
| `src/eliza.cyr` · `src/parry.cyr` · `src/jabberwacky.cyr` | 903 · 522 · 559 | the three chatbots (ADR 0012, 0015) |
| `src/descent.cyr` | 286 | Descent MUD gateway (ADR 0017 / 0031): endpoint parsing + non-blocking dial / connect check / one read / one write — the pump lives in `main.cyr` |
| `tests/agora.tcyr` · `tests/serve.tcyr` | 7,741 · 872 | the module suite · the serve-layer suite (includes `main.cyr`) |

## Cross-references

- [`roadmap.md`](roadmap.md) — release plan (1.8.x → 1.12.x), blocked work, shipped lines.
- [`roadmap-future.md`](roadmap-future.md) — v2.x sovereignty pillars + long-horizon door / chatbot ideas.
- [`../doc-health.md`](../doc-health.md) — doc currency across the tree.
- [`../../CLAUDE.md`](../../CLAUDE.md) — durable rules / process / conventions.
- [`../../CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.
