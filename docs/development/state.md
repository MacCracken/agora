---
name: agora State
description: Live state snapshot for the agora repo — volatile data refreshed every release
type: state
---

# agora — State Snapshot

> **Last refresh**: 2026-10-12 — **1.8.1 (code audit + repair) cut** on top of 1.8.0: a six-slice full-tree
> audit, 3 HIGH / 12 MEDIUM / 26 LOW fixed, no features ([report](../audit/2026-10-12-audit-1.8.1.md)). The
> same day this file was rebuilt as a snapshot (it had grown to 168 KB with a 49 KB "Last refresh" line) and
> the roadmap re-planned into 1.8.x → 1.12.x slots. **Replace this paragraph each release — do not append to
> it.** History lives in [`CHANGELOG.md`](../../CHANGELOG.md) and git.

Per [first-party-documentation § CLAUDE.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#claudemd), CLAUDE.md holds **durable rules**; this file holds **volatile state**. If a claim drifts within a minor's worth of work, it belongs here, not in CLAUDE.md.

---

## Next-session boot guide

1. **Where we are**: see § Version and § In-flight slot below.
2. **Where to read first**: this file, then [`roadmap.md`](roadmap.md) — the release plan (1.8.x → 1.12.x
   slots) is the single authoritative open-work list. Then the newest file in [`docs/audit/`](../audit/).
3. **What to build / test**: `CYRIUS_DCE=1 cyrius build src/main.cyr build/agora`;
   `cyrius test src/test.cyr`; `cyrius fuzz fuzz/telnet_iac.fcyr`; `cyrius build --agnos …` for the
   second target. Wire behaviour is covered only by the `docs/examples/` smokes, which have **no runner**
   yet (roadmap 1.8.2) — several are client-only and need a server started with a specific
   `AGORA_SERVE` model named in their header comment.
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
   - **`src/test.cyr` does not include `src/main.cyr`** — the serve loops and session pool are covered by
     smokes only [1.7.0].
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
   - **This file and `roadmap.md` are refreshed by hand** — there is no release hook; 1.6.6 and 1.7.1
     both shipped without either recording them.

---

## Version

| Field | Value |
|---|---|
| **Released** | `1.8.1` (2026-10-12) — code audit + repair: 3 HIGH / 12 MEDIUM / 26 LOW fixed ([audit](../audit/2026-10-12-audit-1.8.1.md)). Previous: `1.8.0` (same day) — toolchain 6.7.9, darshana 1.3.0, egress sanitization (ADR 0024) |
| **In flight** | none — next slot is **1.8.2** (mechanical gates), see § In-flight slot |
| **Toolchain pin** | cyrius `6.7.9` (`cyrius.cyml [package].cyrius`; local snapshot verified byte-identical to the tag at 1.8.0; a 1.8.1 clean `cyrius deps` regenerated an identical `lib/`) |
| **Source of truth** | `VERSION` at the repo root |

## Build artifacts

| Artifact | Size (1.8.1) | Build line |
|---|---|---|
| `build/agora` | **986,144 B** (+17,424 vs 1.8.0) | `CYRIUS_DCE=1 cyrius build src/main.cyr build/agora` |
| `build/agora-agnos` | 982,656 B | `CYRIUS_DCE=1 cyrius build --agnos src/main.cyr build/agora-agnos` |
| aarch64 | 2,415,440 B (aarch64 ELF does no DCE compaction) | `cyrius build --aarch64 …` |

Size history worth knowing: 14.57 MB at 1.6.6 → 2.01 MB at 1.6.7 (bundled sigil dropped ~12.6 MB of
banked `.bss` — not a DCE win) → 0.97 MB at 1.7.1 onward. `CYRIUS_DCE=1` NOP-fills dead code and keeps
all `.bss`; the build still warns `large static data` (≈375 KB).

## Tests + benchmarks

| Surface | Status (1.8.1) |
|---|---|
| `src/test.cyr` | **232** tests, 0 failures (also 232/232 via `cyrius test --aarch64` under qemu). The test build is now warning-free apart from vendored sigil and large static data. |
| `fuzz/telnet_iac.fcyr` | 1 harness, green — also under `--poison` and `--poison=ab` (CI runs plain only). Its Q-state invariant was vacuous until 1.8.1. |
| `docs/examples/` | **30** smokes, 30/30 (34 runs) at 1.8.1 via a throwaway harness — no runner in-repo yet (roadmap 1.8.2) |
| `benches/bench_telnet.bcyr` | 5 parser benchmarks — see [`BENCHMARKS.md`](../../BENCHMARKS.md). Accept rate and per-session memory have never been benchmarked (roadmap 1.8.3); per-command heap growth was A/B'd by hand at 1.8.1 (CHANGELOG). |
| `cyrius lint` (every `src/*.cyr`) | 176 warnings (all line length), **0 untracked deferrals** |
| `cyrius audit` | **exits 1** (it did at 1.8.0 too; this table said ✅): fmt clean, 176 lint warnings, 358 undocumented public functions, `skip: no tests/ directory`, bench green — roadmap 1.8.2 |

## In-flight slot

**None.** 1.8.1 is cut. Next is **1.8.2 — mechanical gates** (roadmap § 1.8.2): an in-repo examples runner
and CI smokes, `--poison=ab` and aarch64 in CI, the toolchain-provenance script, a slow-reader regression
smoke, a state-sync check, a generated version string, `cyrius audit` passing, and CI supply-chain pinning.

## Recent shipped

- **1.8.1** (2026-10-12) — code audit + repair: poll fairness (16 pipelining clients: 13.7 s → 22 ms for a
  bystander) and unauthenticated heap growth (listings, login, `list`/`read` on big boards → 0 B/command);
  fail-closed `.policy`/`.admins`; door saves on every close path + a play lock; loader bounds; Descent
  visit bugs; fork connection cap. 232 tests, 30 smokes.
- **1.8.0** (2026-10-12) — cyrius 6.6.2 → 6.7.9 + darshana 0.9.0 → 1.3.0; stored text sanitized at
  egress (C1 via the wire, anything via the CLI, reaching readers' and the operator's terminals); 225 tests.
- **1.7.1** (2026-09-11) — cyrius 6.5.34 → 6.6.2, the `Result` value-form migration.
- **1.7.0** (2026-08-22) — clean shutdown (signalfd, both serve models), crash-safe door / world / chat
  writes, both poll holes, the IAC fuzz harness.
- **1.6.7** (2026-08-22) — cyrius 6.4.78 → 6.5.33; `is_dir` / `dir_list` per-call leak fixed upstream;
  binary −86% from bundled sigil.

Everything earlier: [`roadmap.md`](roadmap.md) § Shipped (one row per release line) and `CHANGELOG.md`.

## Consumers

None. agora is a binary (telnet server), not a library. The v2.x self-distribution pillar would make it a
distribution channel for the rest of AGNOS, at which point downstream verification becomes load-bearing.

## Verification hosts

| Host | Role | Status |
|---|---|---|
| Workstation (Linux x86_64) | primary dev + smokes | ✅ active |
| archaemenid (iron NUC, AGNOS) | 1.0 release-gate validation | ✅ validated 2026-05-23 (criteria #3 + #4) |
| aarch64 | cross-arch | qemu-user by hand only (232/232 at 1.8.1); no CI, no hardware run (roadmap 1.8.2) |

## Dependencies

| Dep | Used for | Version | Notes |
|---|---|---|---|
| cyrius stdlib | everything | 6.7.9 | 25 named modules (`cyrius.cyml [deps].stdlib`); `lib/` is generated, never committed |
| **darshana** | SGR composers + egress sanitizer | **1.3.0** (git dep, frozen v1 API) | `tty_sgr_buf`, `tty_sgr_reset_buf`, `tty_sanitize_buf`; termios / signalfd surface deliberately unused |
| **sigil** | Ed25519 + SHA-256 + hex (auth) | 3.13.11 (bundled in the 6.7.9 stdlib) | vendored copy warns about `hash_file_into`'s static 256 KB buffer under 6.7.x — not agora's, flagged upstream |
| bannermanor | MOTD banners | 1.0.1 | output baked into the MOTD at M2-A; the crate is not a build dep |
| kii / sankoch | M3 inline images / M4 stored-file deltas | — | gates met, no consumer; nothing in `src/` references them |
| agnos ext4 WRITE | AGNOS-target storage | in flight upstream | not blocking (ADR 0001) |

## Source surface (1.8.1, lines)

| File | Lines | Holds |
|---|---:|---|
| `src/main.cyr` | 4,522 | argv dispatch + CLI verbs; both serve models (fork / poll), session pool + context swap; `process_rx` line dispatch + the poll line budget; login flow; send path (`send_buf` / `send_text` / `write_text`); door / chat / Descent glue, door save lifecycle; N1 shutdown |
| `src/telnet.cyr` | 755 | RFC 854 IAC parser, RFC 1143 Q-method, NAWS / TERMINAL-TYPE / LINEMODE subnegotiation (only for agreed options) |
| `src/board.cyr` | 1,517 | post storage + RFC-822 headers (PostHeaders ABI), boards, threading, policy / admins (fail closed), `flock` helpers, the directory workspace (`store_dir_scan`), egress sanitize rule (ADR 0024) |
| `src/account.cyr` | 611 | fingerprint, handle validation, user dirs, keyfiles, nonce / signature parse, From-header extraction, the register lock |
| `src/arena.cyr` | 162 | per-command scratch arena (ADR 0021), `store_write_atomic` |
| `src/door.cyr` | 826 | door framework (ADR 0009): PRNG, saves (+ remove / quarantine / play lock), world transactions, leaderboards, `emit_*` render, descriptor registry (ADR 0020), `DD_FREE` (ADR 0022) |
| `src/smuggler.cyr` · `src/port_authority.cyr` · `src/handler.cyr` | 1,247 · 1,543 · 1,385 | the three 1.1.0 doors + their 1.2.0 Universe layers |
| `src/quest.cyr` · `src/olympiad.cyr` · `src/ashes.cyr` | 896 · 1,009 · 1,304 | QUEST (LORD homage), Olympiad (`compete()`), Ashes of Empire (async shared-world strategy) |
| `src/decode.cyr` · `src/decode_words.cyr` | 745 · 33 | Decode engine (Mastermind / Wordle) + the 532-word list |
| `src/wager.cyr` | 311 | shared wagering primitive (ADR 0013) |
| `src/chat.cyr` | 426 | chat area ring transcript (ADR 0011) |
| `src/eliza.cyr` · `src/parry.cyr` · `src/jabberwacky.cyr` | 868 · 502 · 551 | the three chatbots (ADR 0012, 0015) |
| `src/descent.cyr` | 476 | Descent MUD gateway, TCP byte-proxy (ADR 0017) — no longer calls into `main.cyr` |
| `src/test.cyr` | 5,974 | the unit suite (does not include `main.cyr`) |

## Cross-references

- [`roadmap.md`](roadmap.md) — release plan (1.8.x → 1.12.x), blocked work, shipped lines.
- [`roadmap-future.md`](roadmap-future.md) — v2.x sovereignty pillars + long-horizon door / chatbot ideas.
- [`../doc-health.md`](../doc-health.md) — doc currency across the tree.
- [`../../CLAUDE.md`](../../CLAUDE.md) — durable rules / process / conventions.
- [`../../CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.
