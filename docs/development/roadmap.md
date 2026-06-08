# agora — Roadmap

> **Last Updated**: 2026-05-23
>
> Versioned milestones through v1.0. Per [first-party-documentation § Development Docs](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#development-docs-docsdevelopment), this file lists what's shipped, what's next, what's deferred, and the v1.0 criteria. Per-tag chronology lives in [`CHANGELOG.md`](../../CHANGELOG.md); current state in [`state.md`](state.md).

agora is the BBS userland for AGNOS — Greek ἀγορά (civic-marketplace / public-assembly). The project is **cross-platform from M1**: built on cyrius `lib/net.cyr` socket primitives + `lib/io.cyr` / `lib/fs.cyr` storage, Linux today, AGNOS becomes one target among many as the stdlib gains backends ([ADR 0001](../adr/0001-cross-platform-listener-decoupled-from-agnos.md)).

---

## Release plan

| Tag | Theme | Status |
|---|---|---|
| **0.1.0** | M0 — scaffold | ✅ 2026-05-23 |
| **0.2.0** | M1 — cross-platform telnet listener (RFC 854 / 1143 / 1073 / 1091 / 1184) | ✅ 2026-05-23 |
| **0.3.0** | M2 — ANSI BBS aesthetic (bannermanor MOTD + darshana SGR + `--motd`) | ✅ 2026-05-23 |
| **0.4.0** | M5 partial — single-board post persistence (ADRs 0002 / 0003) | ✅ 2026-05-23 |
| **0.5.0** | M5 close — boards + threads (ADRs 0004 / 0005) | ✅ 2026-05-23 |
| **0.6.0** | M6 — sigil-backed auth + per-board policy (ADR 0006) | ✅ 2026-05-23 |
| **0.7.0** | Security sweep — external CVE / 0-day research + code audit | ✅ 2026-05-23 |
| **0.8.0** | Concurrent accept via fork-per-connection (ADR 0007) — audit M1 + M2 closed | ✅ 2026-05-23 |
| **0.8.1** | Keyfile mode warn-on-load (audit L1 closed) | ✅ 2026-05-23 |
| **0.8.2** | Sigil 3.1.1 → 3.4.3 release-notes diff (no bump; 0.7.0 deferred item discharged) | ✅ 2026-05-23 |
| **0.8.3** | Anonymous board-create gate (audit M4 closed — all 0.7.0 audit findings now discharged) | ✅ 2026-05-23 |
| **0.9.0** | PostHeaders struct ABI freeze (ADR 0008) | ✅ 2026-05-23 |
| **0.9.1** | Guides + examples doc-pass (F) — long-deferred Tier 5 + Tier 6 rewrite + 6 runnable example scripts | ✅ 2026-05-23 |
| **0.9.2** | Perf re-run + final 1.0 closeout sweep (G) — CLAUDE.md "Closeout Pass" §1-11 | ✅ 2026-05-23 |
| **1.0.0** | Iron-validated on archaemenid LAN — criterion #3 telnet round-trip + criterion #4 8-user fanout both green | ✅ 2026-05-23 |
| **1.1.0** | Door / games subsystem — Smuggler's Ledger + Port Authority + The Handler (ADR 0009); `play` verb + MODE_DOOR | ✅ 2026-06-07 |
| **1.1.1** | The Handler **field pressure** (single-player depth: cover erosion + agent burnout + mole-local leak; Extract/Fund now load-bearing) + **toolchain unblock** cyrius 6.0.52 → 6.1.5 (sigil SIGILL cleared) | ✅ 2026-06-08 |
| **1.2.0** | **Persistent Universe** — shared-world multiplayer for the door games (ADR 0010): flock'd world transactions, PA shared galaxy + PvP, shared economy, Handler intercepts/sabotage, leaderboards | 🚧 **bites 1-2 done** (world-txn framework + PA shared galaxy, `play port universe`); bites 3-6 remain — see In progress |
| **1.3.0** | **Chat area + Eliza** — a live multi-user chat surface (the classic BBS teleconference / CB simulator) with **Eliza**, a pure-module Rogerian chatbot, as its anchor inhabitant. Builds on the 1.2.0 `flock`'d shared-disk framework; Eliza is also a `play eliza` door. No new deps. | 📋 planned |

---

## In progress

**1.2.0 — Persistent Universe (bites 1-2 shipped; bite 3 next).** Shared-world multiplayer for the three door games. **Everything before 1.2.0 is shipped history** (the 0.x line → the 1.0.0 BBS cut → the 1.1.0 door / games subsystem → 1.1.1 Handler field pressure — see *Closed milestones* + [`CHANGELOG.md`](../../CHANGELOG.md)).

> **▶ Active — both original blockers retired.** The cyrius toolchain issues that had deferred this are cleared on 6.1.5: (1) the **sigil/crypto SIGILL on ≥ 6.0.53** (pin lifted 6.0.52 → 6.1.5; verified by 135/135 + crypto round-trip + telnet login), and (2) the **array-in-loop codegen bug** — bite 2's real shared-galaxy code (not just a synthetic probe) compiles and passes, with t129 a distinct-write-readback over the stock array that specifically exercised it. Bite 1 (world-transaction framework) and bite 2 (PA shared galaxy) are both shipped + smoke-green; bites 3-6 remain.

Design: [ADR 0010](../adr/0010-persistent-universe.md) — a per-game shared world dir under `<store>/.games/<game>/world/`, mutated through a `flock`'d **lock → read → compute → write** "world transaction" with the game logic staying a **pure transform** (the ADR 0009 pure-module rule survives; the I/O lives in `door.cyr` + `main.cyr`). Universe requires login; Practice + Solo (shipped 1.1.0) are unchanged. Async/indirect PvP (act against the state another player left behind), not real-time. Daily-turn budgets keep it fair.

**1.2.0 bite plan** (ADR 0010 § Phasing — bites 1-2 ✅; bites 3-6 remain):

1. **World-transaction framework** in `door.cyr` ✅ (2026-06-07) — world dir + `flock` lock + snapshot read/write + `world_txn_add` + diagnostic `worldbench`/`worldread` verbs. Concurrency smoke green: 16 procs × 500 txns → exactly 8000, no lost updates (`08-world-concurrency.sh`); t122/t123 unit. Snapshot write is in-place `O_TRUNC` under the held lock; temp+rename/event-log crash-hardening deferred (ADR 0010).
2. **Port Authority shared galaxy** ✅ (2026-06-08) — generated-once deterministic galaxy (`PA_UNIVERSE_SEED`), **depletable port stock** that moves the next player's quoted price (`paw_buy`/`paw_sell`/`paw_price`), **exclusive planet ownership** by sigil fp (`paw_claim_planet`); `play port universe` (login-gated) with the per-line `flock`'d world transaction in `main.cyr`; per-player ship in the `portu` save. t128-t135 (135/135; t129 re-cleared the codegen bug on the real code); cross-session shared-world smoke `09-universe-port.sh`. The canonical Universe slice.
3. **PA deployments + async PvP** — sector-deployed fighters/mines, combat vs left-behind assets, alliances.
4. **Smuggler's shared economy** (district prices + heat move with all players) + **The Handler shared layer** (per-city alerts, intercept pool, anonymous-tip sabotage).
5. **Leaderboards** — generalize the 1.1.0 Handler standings file to all three games.
6. **Closeout** — VERSION → 1.2.0, docs, `08-*` example, clean DCE build.

**Deferred (pull when a deployment asks):**

- `agora policy set <board> <mode>` + `agora admins {add,rm,list}` CLI verbs (operators currently edit `.policy` / `.admins` files directly).
- Door directions still unpinned beyond 1.2.0 (Handler world-event track + legacy ranks, PA citadels/mining deep endgame, the 2400-baud teletype effect) live in [`roadmap-future.md`](roadmap-future.md) § Door games.

---

## Planned

### 1.3.0 — Chat area + Eliza

A **chat area** is the public-assembly surface agora hasn't built yet: the classic BBS *teleconference* / CB-simulator where logged-in citizens talk in shared, named channels in (near) real time — distinct from the asynchronous post boards. **Eliza** — a faithful pure-module port of Weizenbaum's 1966 Rogerian psychotherapist chatbot — is its anchor inhabitant: a nostalgic BBS staple, a zero-dependency pure transform, and a low-risk first thing to put *in* the room.

**Design fit (why it slots cleanly into agora):**

- **Eliza is a pure module** (`src/eliza.cyr`), exactly the [ADR 0009](../adr/0009-door-games-subsystem.md) shape the games already use: a deterministic, side-effect-free `(input line) → (reflected response)` transform — keyword-ranked decomposition + reassembly-rule templates + pronoun reflection (I↔you, my↔your). Unit-testable without a socket (canned exchanges → fixed replies), no external deps, no RNG required (or a seeded `door.cyr` PRNG for reply variety, keeping replays reproducible). She's reachable two ways: as a `play eliza` **door** (solo, immediately), and as a **bot participant** in the chat area.
- **The chat area is a new shared surface** that builds directly on the **1.2.0 `flock`'d shared-disk framework** (the world-transaction pattern, generalized): a per-channel append-only, `flock`'d transcript that connected sessions tail — the same fork-per-accept-safe, on-disk-is-the-only-shared-state discipline ([ADR 0007](../adr/0007-fork-per-accept-concurrency.md)) the Universe work establishes. So it is **gated behind 1.2.0** for the shared-state machinery, not a from-scratch concurrency build.
- **Login-gated, like Universe** — a chat presence is a persistent-ish actor, so it needs a sigil identity; anonymous users can still read/post on boards.
- **No new dependencies** — pattern-matching + flat-file transcripts are agora's existing idioms.

**Open questions for its ADR (when 1.3.0 pulls forward):** live-tail delivery model (poll-on-input vs. a notify mechanism under fork-per-accept), channel lifecycle + scrollback retention, whether Eliza runs as an always-present bot writing into the transcript or a private `/eliza` side-channel, and an Eliza script format (built-in DOCTOR script vs. operator-loadable rule files). Earns a dedicated ADR when the chat surface is cut.

---

## Backlog (gates met, no current consumer)

- **M3** — Inline-image post bodies via kii 1.0.0 (ASCII-art conversion). Pulls when a consumer asks for it.
- **M4** — Stored-file deltas via sankoch 2.2.6 (compressed diff-based post-edit storage). Pulls when post-edit becomes a feature.

Both are gates-met but ship-deferred. Lots of value but no v1.0 dependency. Slated for v1.x bites if real BBS use surfaces the need.

---

## Closed milestones

Detail per release lives in [`CHANGELOG.md`](../../CHANGELOG.md); per-bite narrative in `state.md`'s "Recent shipped". Brief table here for the roadmap-skim case:

- **M0** (0.1.0) — argv dispatch, six stub verbs, 43 KB scaffold binary.
- **M1** (0.2.0) — five-bite telnet listener: IAC parser, Q-method negotiation, NAWS + TT subneg, LINEMODE, bench harness. 10 ns/byte hot path.
- **M2** (0.3.0) — three-bite ANSI aesthetic: bannermanor MOTD, darshana SGR colors, `--motd` operator override. Bannermanor patched 1.0.1 same-day for ecosystem alignment on darshana 0.5.3.
- **M5** (0.4.0 + 0.5.0) — eight-bite post persistence. Single-board (0.4.0): storage primitives, in-session command interpreter, sorted listing, RFC-822 headers, per-store flock, ingress filter. Multi-board threaded (0.5.0): boards, Reply-To threading. Four ADRs total (0002, 0003, 0004, 0005).
- **M6** (0.6.0) — six-bite sigil-backed auth + per-board policy. ADR 0006 (identity model) + `src/account.cyr` primitives (M6-B) + telnet `login` challenge/response (M6-C) + `keygen`/`register`/`whoami` CLI + telnet `whoami` (M6-D) + `From:` post header (M6-E) + per-board `.policy` / `.admins` (M6-F). Adds sigil + freelist + bigint + ct to stdlib deps; 49 → 70 tests; 140 → 375 KB binary.
- **0.7.0 security sweep** (0.7.0) — first dedicated audit cycle. Full report at [`docs/audit/2026-05-23-audit.md`](../audit/2026-05-23-audit.md). Zero CRITICAL. 5 fixes landed: H1 CLI subject CRLF injection (`cmd_post`), H2 cmd_list/cmd_read --board path-traversal, H3 `post_from` re-validates handle + fp on read (defense vs. tampered user files), M3 `parse_post_id` 18-digit overflow guard, M6 30s explicit deadline on parked login challenge (deferred from M6-C). 4 items queued for 0.8 (concurrent-accept + per-conn memory arenas; anonymous board-create gate; keyfile mode warn-on-load; sigil 3.1.1 → 3.4.3 diff). 70 → 78 tests; 375 → 377 KB binary (+0.6%); no new stdlib deps.
- **0.8.0 concurrent-accept** (0.8.0) — fork-per-connection accept loop via [ADR 0007](../adr/0007-fork-per-accept-concurrency.md). Audit M1 (bump-allocator memory growth) + M2 (login-challenge slot collision) both close via process isolation — kernel reclaims per-child memory at `sys_exit`; globals are per-process post-fork. Loop: `sys_waitpid(-1, NULL, WNOHANG)` reaper → `sock_accept` → `sys_fork` → child runs handle_client + `sys_exit(0)` / parent loops. Audit M4 (anonymous board-create) carried forward to 0.8-B — independent of concurrency model. 78 tests unchanged (E is in the accept loop, not unit-testable code); 377 → 378 KB binary (+0.09%); no new stdlib deps.
- **1.0.0 v1 cut** (2026-05-23) — all six v1.0 criteria met, iron-validated on archaemenid (single-session telnet round-trip #3 + 8-user fanout #4). Closes the 0.x line (0.8.x audit followups + 0.9.0 ABI freeze [ADR 0008] + 0.9.1 doc-pass + 0.9.2 closeout). 80 tests; 378,456 B.
- **1.1.0 door / games** (2026-06-07) — door subsystem ([ADR 0009](../adr/0009-door-games-subsystem.md)): three pure-module text games (Smuggler's Ledger, Port Authority, The Handler) + `play` verb + `MODE_DOOR`; Practice + Solo modes; Handler standings (first shared-disk feature). The solvable-mole deduction (t114) is the novel core. 80 → 121 tests; 378,456 → 484,184 B. Universe mode stubbed → **taken up by 1.2.0** (this is the work now in progress above).

---

## v1.0 criteria — ✅ all met (2026-05-23)

A release qualifies for 1.0 when:

1. **M0–M6 + security sweep + hardening have all shipped at least once.** ✅ — shipped across 0.1.0 → 0.9.2 (eighteen tags).
2. **`cyrius audit` passes from a clean build (lint / test / bench / doc).** ✅ — 80/80 tests; 5 benches within noise of M1-close baseline; clean DCE build at 378,456 B.
3. **Telnet validation on archaemenid LAN — iron NUC running AGNOS serves telnet to a second box; end-to-end exercise: connect → log in → list boards → read a thread → post a reply → log off.** ✅ — `docs/examples/05-telnet-login.sh 2323` ran on archaemenid 2026-05-23: `login qix` → openssl-signed `auth:` → server `welcome, qix` → `whoami` reports `qix 878873ab607321a5`.
4. **Multi-user concurrency: simulated 8-user fanout, no message loss, no state corruption.** ✅ — `docs/examples/04-concurrent-smoke.py 2323 8` ran on archaemenid 2026-05-23: 8/8 sessions OK (each got banner + IAC + boards reply with no cross-talk; ADR 0007 fork-per-accept process isolation confirmed at fanout).
5. **Security audit (0.7.0) findings all closed in 0.8.0 hardening.** ✅ — H1/H2/H3 + M3 + M6 at 0.7.0; M1+M2 at 0.8.0; L1 at 0.8.1; M4 at 0.8.3. All discharged; sigil 3.1.1 → 3.4.3 diff at 0.8.2 found no upgrade-warranted findings.
6. **RFC conformance: `src/test.cyr` covers the canonical sequences from RFCs 854 / 1143 / 1073 / 1091 / 1184.** ✅ — t01–t24 (IAC parser + Q-method + NAWS + TT + LINEMODE conformance suite); 56 additional tests for storage + auth + policy + audit regressions.

---

## Post-v1.0 directions

Six pillars for the v2.x sovereignty layer — identity continuity (sigil-portable Ed25519), content-addressed storage, threat-level node policy (SecureYeoman vocabulary), federation by interest (topics, not platforms), self-distribution baked into the protocol, and offline-tolerant store-and-forward. Detail in [`roadmap-future.md`](roadmap-future.md). Items are **unpinned** — they pull forward into a numbered minor when consumer pressure or operator demand surfaces, not on a calendar.

---

## Companion project

**MUD userland** — separate repo, shares the telnet listener primitive but adds a real-time room/object model. Same wire-protocol substrate, different application semantics.

## Cross-references

- [`docs/development/state.md`](state.md) — live state snapshot (current version, binary size, in-flight slot, **next-session boot guide**).
- [`docs/development/roadmap-future.md`](roadmap-future.md) — v2.x sovereignty pillars (post-v1.0, unpinned).
- [`docs/adr/`](../adr/) — **eight ADRs as of 0.9.0** (cross-platform listener / one-file-per-post / RFC-822 headers / board layout / Reply-To threading / identity model / fork-per-accept concurrency / **PostHeaders struct ABI**). 0.7.0 added no new ADR (the audit doc is the record); 0.8.0 added ADR 0007; 0.9.0 added ADR 0008.
- [`docs/audit/`](../audit/) — security audit ledger; first entry 2026-05-23 (0.7.0 sweep).
- [`docs/doc-health.md`](../doc-health.md) — fresh/stale ledger across the whole doc tree.
- [`CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.
