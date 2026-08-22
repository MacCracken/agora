# agora — Roadmap

> **Last Updated**: 2026-08-22 (**1.7.0 — § Now is EMPTY**: N1/N2/N3/N4 all shipped, and the section
> now records what each turned out to be rather than what it asked for, because the findings outlived
> the items. Also earlier the same day: 1.6.7's toolchain cut discharged the `dir_list` cross-repo
> block and re-filed it in § Backlog rescoped to the `dir_list_into` half that survives. Prior:
> 2026-07-26, rebuilt from a full deferred-work sweep — see *Provenance* at the end)
>
> **What this file is**: what shipped, what is pinned next, what is real-but-unscheduled, and what is
> deliberately not being done. **What it is not**: a second changelog. Per-tag narrative lives in
> [`CHANGELOG.md`](../../CHANGELOG.md); the live snapshot and the current cut's detail live in
> [`state.md`](state.md). Per [first-party-documentation § Development Docs](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#development-docs-docsdevelopment).

agora is the BBS userland for AGNOS — Greek ἀγορά (civic-marketplace / public-assembly). **Cross-platform
from M1**: built on cyrius `lib/net.cyr` socket primitives + `lib/io.cyr` / `lib/fs.cyr` storage. Linux and
AGNOS ship today; macOS and Windows follow as the stdlib gains backends
([ADR 0001](../adr/0001-cross-platform-listener-decoupled-from-agnos.md)).

**Every open item below cites its source** — a `file:line`, an ADR, an audit finding, or a CHANGELOG
entry. If an item has no citation it does not belong here.

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
| **1.2.0** | **Persistent Universe** — shared-world multiplayer for all three door games (ADR 0010): flock'd world transactions, PA shared galaxy + async-PvP garrisons, Smuggler shared heat, Handler shared city alerts, cross-game leaderboards | ✅ 2026-06-08 |
| **1.3.0** | **Chat area + Eliza** — a live multi-user chat surface (the classic BBS teleconference / CB simulator, [ADR 0011](../adr/0011-chat-area.md)) with **Eliza**, a pure-module Rogerian chatbot, as its anchor inhabitant. Builds on the 1.2.0 `flock`'d shared-disk framework; Eliza is also a `play eliza` door + a private `/eliza` side-channel. No new deps. | ✅ 2026-06-08 |
| **1.3.1** | **PARRY** (Colby, 1972) — the paranoid foil to Eliza: `play parry` + `/parry`. Reuses the 1.3.0 ELIZA **text primitives** (normalize / pronoun-reflect / keyword-scan / cyclic templates) but adds PARRY's distinct **affect engine** — internal **fear / anger / mistrust** state that evolves with each input and *gates* the response — plus the Mafia/bookie **delusion narrative** it steers toward when provoked. Affect-gated dispatch, not a pure keyword→template script. | ✅ 2026-06-08 |
| **1.3.2** | **QUEST** — the LORD-homage door ("Quest of the Undying Emerald Sovereign Throne", `play quest`): the twelve-level **Great-Work** arc (Nigredo→Albedo→Citrinitas→Rubedo) + the **Emerald-Tablet** fragment spine + town hub (Healer / Bank-with-muggers / Inn) + the Sovereign ascension, on the pure-module door + daily-turn machinery. Single-player climb; async-PvP/Universe a follow-on. | ✅ 2026-06-08 |
| **1.3.3** | **Jabberwacky** (Carpenter, 1988→) — a **corpus-learning** chatbot: a *different engine* from the ELIZA/PARRY fixed-script core (word-overlap retrieval + learn-the-transition over a growing corpus), agora's first learning / persistent-state bot. `play jabberwacky` (+ `solo` per-user persistence) + `/jabberwacky`. [ADR 0015](../adr/0015-jabberwacky-corpus-learning.md). | ✅ 2026-06-08 |
| **1.3.4** | **Wager** ([ADR 0013](../adr/0013-wagering-module-rng-fairness.md)) — one shared casino/wagering module (`src/wager.cyr`), the **build-once primitive**: bet validation, payout tables, the entropy draw, house edge. A *mechanic, not a door* — the same loop (bet → draw → resolve → settle) every game calls; the "one shared abstraction under many games" pattern (cf. the door PRNG). Decision: the draw pulls from the **kernel CSPRNG** (non-replayable), distinct from the games' replayable seeded `door.cyr` PRNG. | ✅ 2026-06-08 |
| **1.3.5** | **Casino integrations** — embed the 1.3.4 wager module across the **existing** doors so it earns its keep: a cantina gambling table in **Port Authority**, a back-alley dice game in **Smuggler's Ledger**, a tavern card game in **QUEST**. Same module, many contexts — every game gets richer with no fifth thing to maintain. | ✅ 2026-06-08 |
| **1.3.6** | **Olympiad** ([ADR 0016](../adr/0016-olympiad-competition-primitive.md)) — a Greco-Roman games-**owner** sim (the training-sim grown up): field a chariot stable, train-or-rest across a daily economy, climb a 12-meet ladder to the **tethrippon crown**, wagering on every race. Keystone: the event-agnostic **`compete()` primitive** (one form-weighted CSPRNG draw resolves the race AND prices the book) — the wager module's flagship. Gladiators / athletics / boat crews become thin event descriptors later. | ✅ 2026-06-09 |
| **1.3.7** | **Ashes of Empire** — the war-game ([ADR 0014](../adr/0014-async-shared-world-strategy.md)): an **asynchronous shared-world strategy** door (a common ring map of twelve provinces, marches, alliances, turn-batched combat resolution between callers). The high-value **new-capability proof** — it deliberately exercises the shared-state-mutation-between-callers path on the 1.2.0 `flock`'d world-transaction framework ([ADR 0010](../adr/0010-persistent-universe.md)), with turn resolution **lazy on caller entry** (a resolution daemon kept open as a deferred future feature), retiring real concurrency risk as the **on-ramp to the 1.4.0 Descent/MUD** real-time world. | ✅ 2026-06-09 |
| **1.4.0** | **Descent link** — bridge a logged-in agora session into the sibling **Yeoman's Descent** MUD (`../cyrius-yeomans-descent`) as a transparent TCP-proxy door over the shared telnet substrate ([ADR 0017](../adr/0017-descent-link-gateway.md)). The BBS becomes the front door to the MUD. Sigil identity hand-off deferred (the MUD has no external-identity path — a follow-on bite). | ✅ 2026-06-10 |
| **1.4.1** | **Decode / Numbers** ([ADR 0018](../adr/0018-decode-engine.md)) — a single `play decode` code-breaking door: classic Mastermind. The pure heart `decode_classify` is the symbol-agnostic, duplicate-correct exact/present scorer (Mastermind pegs = Wordle colors); agora's one-engine/many-variants pattern a fourth time (door PRNG → wager → `compete()` → DECODE). Also migrated the toolchain 6.1.23 → **6.2.2** (stdlib reorg). | ✅ 2026-06-14 |
| **1.4.2** | **Decode / Words (Wordle)** — the Words variant added to the same `decode` door on the same engine (a `[n]/[w]` select screen, a curated 532-word 5-letter dictionary in `src/decode_words.cyr` doubling as answer pool + guess dictionary, per-letter green/yellow/gray render). | ✅ 2026-06-14 |
| **1.4.3** | **Handler decrypt lever** ([ADR 0019](../adr/0019-decode-handler-lever.md)) — the decode engine embedded in The Handler: at the desk, spend a dispatch point to crack an intercepted number/word cipher and reveal whether a cable's discrepancy is a deliberate plant (the mole) or clerical noise (`CB_ANOM`). First cross-game mechanic reuse; runtime-only state, no save-format change. | ✅ 2026-06-14 |
| **1.4.4** | **P(-1) hardening pass** (no new features) — toolchain 6.2.2 → **6.2.7**, darshana 0.5.3 → **0.7.0**; full P(-1) audit ([`docs/audit/2026-06-15-audit.md`](../audit/2026-06-15-audit.md)) fixed 6 findings: a remote `send_buf` CPU-peg DoS (T1), a handler-save heap overflow (S1/R4), two integer-overflow parser bugs (D1/D2), a dropped world-write return (R6), and 7 dead functions removed (R3). 218 → **220 tests**. | ✅ 2026-06-15 |
| **1.4.5** | **Hardening follow-up** (no new features) — closes the three defense-in-depth items 1.4.4 deferred: **T2** send-side socket timeout (`SO_SNDTIMEO`; companion additive `sock_set_send_timeout` in the cyrius stdlib `lib/net.cyr`), **T3** `TERMINAL_TYPE` buffer NUL-termination, **D3** door render-frame bounds enforcement (the `emit_*` cap + `door_send_frame` guard-band/clamp). 220 → **221 tests**. | ✅ 2026-06-15 |
| **1.4.6** | **R7 — door-dispatch refactor** ([ADR 0020](../adr/0020-door-descriptor-registry.md), no behavior change) **+ toolchain 6.2.7 → 6.2.8** — the ~130 per-game `if (game == GAME_X)` branch sites across ~16 `door_*`/launcher dispatch functions collapsed into a single per-game descriptor record (`enum DoorDesc` + `door_registry_init`), dispatched via `callptr` through `&fn` slots. Adding a door is now one registry block. The 6.2.8 stdlib now carries the 1.4.5 `sock_set_send_timeout` as stock. 221 tests; byte-identical at the bump; verified by the full example smoke suite. | ✅ 2026-06-15 |
| **1.5.0** | **agnos target** — agora builds `--agnos` and serves under mirshi (`--net-listen-any`): a telnet client connects, the banner + door/chat menu render over the socket. The Linux fork-per-accept path is unchanged; agnos serves *serially* (no fork), with the single-process event loop flagged as the follow-up. | ✅ 2026-07-02 |
| **1.6.0** | **Single-process poll multiplex** — the 1.5.0 follow-up: many players at once via descent's model, runtime-selectable with **`AGORA_SERVE={fork,poll}`** (Linux defaults to fork for per-connection crash-isolation; **agnos always polls** — it has no fork). `handle_client` becomes a driver over an extracted `process_rx`; a 64-slot session pool + context-swap keeps the door games and chat untouched (ADR 0009 pure state machines). Verified on both platforms with zero cross-session bleed; a 66-client flood on the 64-slot pool degrades gracefully. Toolchain 6.2.8 → 6.4.32. | ✅ 2026-07-09 |
| **1.6.1** | **Toolchain + dependency cut** (no features, no logic change) — cyrius **6.4.32 → 6.4.78** (46 releases; zero removals/renames/arity changes across agora's declared stdlib surface) and darshana **0.8.2 → 0.9.0**. The payload is cyrius 6.4.61's **`sock_accept` fix**: 1.6.0's `serve_poll` drains accepts on a non-blocking listener every ~20 ms and almost always gets EAGAIN, which had been allocating a fresh `Result` each time — a bump-heap leak proportional to uptime, on the model agnos always runs. Also force-refreshes six vendored stdlib files `cyrius lib sync` had silently skipped (architecture note [002](../architecture/002-lib-sync-same-size-skip.md)). 221/221 unchanged; both targets build; 11 wire smokes green (login + concurrency re-run under both `AGORA_SERVE` models). **Deferred to their own cuts**: unhandled SIGPIPE (cyrius 6.4.51's new `signal_ignore()` is the fix) and the agnos raw-syscall collisions. | ✅ 2026-07-25 |
| **1.6.2** | **The poll model pays its debts** — closes all three items 1.6.1 deferred plus two bugs the work uncovered. **SIGPIPE ignored** in the serve path (an unauthenticated whole-server kill under poll, where one process owns all 64 sessions; cyrius 6.4.51's `signal_ignore`, which arrived with the 1.6.1 pin). **A per-command scratch arena** ([ADR 0021](../adr/0021-per-command-scratch-arena.md), `src/arena.cyr`) — 252 alloc sites with zero frees was correct under ADR 0007's process-per-connection model and leaked 7,473 B/command under poll; now reset once per dispatched line (door play 3,434 → **389 B/cmd**). **agnos syscall guards** — `SYS_MKDIR = 83` (now a live GPU dispatch there), `syscall(60)` exit, and Descent's `syscall(7)` poll, which also gains a real agnos peer. Found en route: the **Descent gateway was silently broken under `AGORA_SERVE=poll`** since 1.6.0, and the pool-full message was truncated. 221/221 unchanged; two new smokes; all 21 runnable examples green. | ✅ 2026-07-25 |
| **1.6.3** | **Door states learn to die + the P(-1) audit** — every game gets a **`DD_FREE`** hook ([ADR 0022](../adr/0022-door-state-free-hook.md)) backed by the freelist, the last allocation class with a lifetime longer than one dispatched line. Growth across `play`/`quit` cycles goes from linear (720 KB @ 600 commands → 2,460 KB @ 2,400) to **flat** (208 KB → 203 KB). Ships with the fixes from a full eight-dimension audit with adversarial verification — headline: **`scores` is unauthenticated and leaked ~5 KB per call**, an unauthenticated path to heap exhaustion under poll; also the chat live-tail leaking on every idle tick, and the login path leaking per attempt. 221/221 unchanged; new churn smoke; 20 examples green. | ✅ 2026-07-26 |
| **1.6.4** | **The audit's MEDIUMs** (no new features) — **IAC (0xFF) handled per RFC 854 both ways**: doubled on egress via a new `send_text` across the nine stored-content sites, dropped at ingress, closing a path where a registered user could store raw telnet commands in a post that wedge every later reader's client. **Protocol chatter no longer counts as activity** — `IAC NOP` at ~2 bytes/minute had pinned the 64-slot pool invisibly; scoped to accounting by the user's call (a per-source cap needs `sys_getpeername`, which agnos lacks). **`BO_EXCL` → `file_create_exclusive`** (silently dropped on agnos, so `keygen` overwrote identity seeds). **`cmd_post` validates `--board` before reading `.policy`** — the 0.7.0 traversal ordering, re-opened. All HIGH + MEDIUM audit findings now closed; new smoke 26. | ✅ 2026-07-26 |
| **1.6.5** | **The audit's LOWs — the ledger closes** (no new features). `--store` bounded at its two parse points (refuses rather than truncating, since a shortened store root points at a different directory); wire posts get the CLI's control-byte filter (C0 + DEL dropped; TAB/CR/LF kept, and CR/LF are load-bearing for line dispatch); echo suppressed only after a genuine revoke (`!= Q_NO`, deliberately not `== Q_YES` — that would break every client that never answers our WILL); bytes pipelined behind `descent` now reach the MUD instead of being lost and then executed as BBS commands. **Every HIGH/MEDIUM/LOW from the [2026-07-26 audit](../audit/2026-07-26-audit.md) is fixed**; one deliberate INFO item remains. `t32` updated — its old assertion conflated editing a line with storing a byte. New smoke 27; smoke 24 extended. | ✅ 2026-07-26 |
| **1.6.6** | **Doc-truth and process** — the non-code half of the 2026-07-26 roadmap sweep, no behavior change. [ADR 0023](../adr/0023-dual-serve-model.md) written (the dual serve model had shipped at 1.6.0 with no ADR at all); **ADR 0007 amended** and the four ADRs citing its "no shared state" premise (0010/0011/0012/0014) corrected; **untracked deferrals 12 → 0 tree-wide** (`cyrius lint` is single-file, so `telnet.cyr`'s five were invisible); ~20 stale comments retired and the unreachable agnos serial-accept branch deleted; CLAUDE.md's Closeout Pass grew three allocator/deferral gates; `CYRIUS_DCE=1` added to CI + release. 221/221; 14,571,744 B. | ✅ 2026-07-26 |
| **1.6.7** | **Toolchain + dependency cut** (no features, no logic change) — cyrius **6.4.78 → 6.5.33** (42 releases; zero removals/renames/arity changes across agora's 71-function stdlib surface), darshana held at **0.9.0** (verified current). Payload: **cyrius 6.5.11's `is_dir`/`dir_list` fix** — agora's own upstream filing, now archived — ends 4,104 B/call of never-reclaimed bump scratch on a path reachable **unauthenticated** via `enter`; measured A/B **24,467 → 3,495 B/command (−85.7%)** on `boards`/`list`. Separately the bundled **sigil** dropped 46 module-level banked arrays (1,587,782 → 11,358 declared units), collapsing the binary **14,571,744 → 2,010,320 B (−86.2%)** — the ~12.6 MB of unused RSA/bignum `.bss` inherited at the 1.6.0 pin move. Found en route: the local `6.5.33` toolchain snapshot was a **dirty working tree** (two libs + `cycc` off-tag), and `docs/examples/20-descent.sh` had been failing because the sibling MUD (now 1.7.22) needs its zone data. 221/221 unchanged; 27/27 smokes green. | ✅ 2026-08-22 |
| **1.7.0** | **roadmap § Now closes** — all four pinned items plus cyrius **6.5.33 → 6.5.34**. **N1** clean shutdown on SIGINT/SIGTERM for both serve models via signalfd (neither loop could exit: both declared `stop` and nothing ever assigned it); **N2** the three `file_write_all` sites onto `file_write_atomic` (safe only because every lock is on a separate `.lock` — a rename replaces the inode); **N3** both poll holes (the silent tx-queue drop, fixed at the single `send_buf` choke point; and `session_drain`'s false "non-blocking on both platforms" comment, now **bounded** on agnos since no non-blocking send exists there); **N4** `fuzz/telnet_iac.fcyr` + a CI *and* release fuzz step, mutation-proven on two axes. Found and fixed inside the cut: arming N1 in the fork parent made every connection **child unkillable**. 221/221; **28/28** smokes (new `28-clean-shutdown.py`); 2,010,320 → **2,230,240 B** (+219,920, of which ~215,520 is 6.5.34's bayan 1.4.2 → 1.5.2 security fold). | ✅ 2026-08-22 |

---

---

## Now — pinned

**Empty for the first time since this file was rebuilt.** N1, N2, N3 and N4 all shipped at
**[1.7.0]** (2026-08-22) — see the release table above and `CHANGELOG.md` for the detail. What each
turned out to be, briefly, because the *findings* outlived the items:

| Was | Outcome |
|---|---|
| **N1** clean shutdown | Shipped via **signalfd**, both serve models. Two silent cross-target traps found on the way: blocking a signal is **required on Linux and wrong on agnos** (mirshi delivers `pending AND NOT blocked`), and the sigset **bit convention is off by one** between the targets. A third bug was created and fixed inside the same cut — arming in the fork parent made every connection **child unkillable** (`SigBlk: 0000000000004002`, survived SIGTERM). Smoke 28 pins all of it, mutation-proven. |
| **N2** durable writes | Shipped. The load-bearing question was **flock vs rename**: a temp+rename replaces the inode, so had the world lock been on `snapshot` rather than `.lock` this would have silently destroyed ADR 0010's guarantee. It is on `.lock`; smoke 08's 8×300 concurrent transactions still land exactly 2400. |
| **N3** poll holes | Both shipped. Hole B's fix needed **no call-site changes** — `send_buf` is the single choke point, and `session_drain`'s negative return is a close path both models already had. Hole A is a **bound, not a cure**: agnos has no non-blocking send to switch to, so the drain now yields after one send per sweep. |
| **N4** IAC fuzz | Shipped as `fuzz/telnet_iac.fcyr` + a CI *and* release step. `--poison` turned out to be **inapplicable** — it instruments `fl_alloc`/`fl_free` and the parser is entirely bump-allocated — so the harness carries its own invariants and is mutation-proven on two axes. |

**Nothing is pinned next.** Pull from § Backlog, or from § Cross-repo if the blocker has moved. The
long-standing named next — the **sigil identity hand-off across the Descent link** — is still blocked
MUD-side.

---


## Cross-repo — blocked on someone else

| Item | Where it is blocked | Effort |
|---|---|---:|
| **Sigil identity hand-off across the Descent link** — carry `g_session_fp`/handle into the MUD so a citizen does not re-authenticate. The project's long-standing named "next". | Yeoman's Descent has **no external-identity path** (name+passphrase only, no pre-authenticated session), so this needs MUD-side protocol work first. Open questions unchanged from [ADR 0017](../adr/0017-descent-link-gateway.md) § Decision: token format, trust model, co-located vs remote. | large |
| **macOS / Windows ports** | Gated on `lib/net.cyr` backends upstream. The gate has moved since the 1.0.0 note — re-check what actually remains. | large |
| **Descent proxy blocks the poll sweep** — a player in the MUD stalls the other 63 sessions (`src/descent.cyr:268-271`, documented not fixed). | Not blocked externally, but the real fix is making Descent a *state* in the poll loop rather than a blocking call — a structural change large enough to want the N2 ADR written first. | large |

---

## Backlog — real, unscheduled

Everything here is verified open with a citation. Grouped by kind, not priority; pull when a cut has room
or a deployment asks.

### Verification and tooling

| Item | Source | Effort |
|---|---|---:|
| Accept-loop rate and per-session memory have **never** been benchmarked — and there are now two serve models to compare. CLAUDE.md P(-1) step 2 requires this baseline. | CLAUDE.md § P(-1); BENCHMARKS.md (parser only) | medium |
| **No `tests/` split, and CI still runs no smoke.** Two halves, one now closed. *Closed at 1.7.0*: CI and the release workflow both run `cyrius fuzz fuzz/telnet_iac.fcyr`, and the release workflow — which previously built and **published** without running a single test — now runs `cyrius test` too. *Still open*: the 28 example smokes remain the only proof of the concurrency, serve-model and shutdown behaviour, and CI runs none of them; and `src/test.cyr` does not include `src/main.cyr`, so nothing in `serve_poll`, the fork loop, the session pool, `sess_tx_enqueue` or the N1 shutdown helpers can be unit-tested at all — N1 and N3 shipped covered by smoke 28 and inspection alone. `cyrius audit` still reports `skip: no tests/ directory`. | `.github/workflows/ci.yml`; `src/test.cyr:10-28` (include block); CHANGELOG [1.7.0] § Known limitations | medium |
| No regression pin for the 1.6.3 slow-reader close path — a HIGH-severity fix resting on inspection alone. | CHANGELOG [1.6.3] § Security | medium |
| Four separate ADR "measure before refining" gates can never open because the benchmarks were never written (world-lock contention is the clearest). | ADRs 0010, 0014 | medium |
| aarch64 is claimed as a supported target and nothing verifies it. | CLAUDE.md § Goal | medium |
| The ~25 sigil "undefined function" build warnings — a standing "don't re-investigate" note whose premises have changed. | build output | unknown |
| **The release post-hook that bumps `state.md` does not exist or does not run.** CLAUDE.md § CI/Release says *"the release post-hook bumps `docs/development/state.md`. If the hook doesn't, fix the hook — don't hand-maintain state."* **1.6.6 shipped and neither `state.md` nor this file recorded it** — `state.md`'s header, its Released row and the release table here all still read 1.6.5 until 1.6.7 backfilled them by hand, which is the exact failure mode that instruction exists to prevent. `release.yml` has no post-hook step at all. Either write it or retract the instruction; a rule nothing enforces is worse than no rule. | CLAUDE.md § CI/Release; `.github/workflows/release.yml`; CHANGELOG [1.6.7] | small |
| **Local toolchain provenance is unverifiable.** Two independent defects, both found at 1.6.7: `install.sh --refresh-only` overwrites `~/.cyrius/versions/<ver>/` from whatever the cyrius *working tree* currently holds (this workstation's `6.5.33` snapshot carried an unreleased `bayan.cyr`, `patra.cyr` and `cycc`, inflating the measured binary by 215,520 B), and the versioned wrapper `~/.cyrius/versions/<ver>/bin/cyrius` **does not pin `cycc`** — it invokes whatever is on `PATH` and warns about the drift it just caused. CI is exempt (fresh runner, released tarball). agora's mitigation today is a manual `git show <tag>:lib/<m>.cyr | cmp -` sweep; it should be a scripted pre-cut gate. Upstream has the wrapper half filed at `cyrius/docs/development/issues/2026-08-22-versioned-wrapper-does-not-pin-cycc.md`. | CHANGELOG [1.6.7] § Verification notes; architecture note [002](../architecture/002-lib-sync-same-size-skip.md) | small |
| **`docs/examples/` has no runner, and its stated ordering contract does not hold.** The README says *"run them in order from a fresh checkout — later examples reuse identity files from earlier ones"*, but 09, 10, 18, 19 and 20 each `rm -rf ./bbs ./keys` on exit, so a strict in-order run leaves 24, 26 and 27 with no registered qix — and six scripts (04, 05, 23, 25, 26, 27) are client-only and need a server started externally with a specific `AGORA_SERVE` model that only their header comments record. 1.6.7 verified all 27 green using a throwaway harness; nothing in the repo reproduces that. This is why smoke 20's breakage went unnoticed. | `docs/examples/README.md`; CHANGELOG [1.6.7] | small |

### The wire — RFC conformance and telnet surface

`telnet.cyr` holds the largest cluster of untracked deferrals (5 of the 12).

| Item | Source | Effort |
|---|---|---:|
| Negotiated terminal state (NAWS cols/rows, TERMINAL_TYPE, LINEMODE mask) has **zero consumers** outside `telnet.cyr` — parsed and stored, never used to size or adapt output. | M2-D deferral | medium |
| AYT (Are You There) generates no response; RFC 854 expects visible evidence. No test pins either behaviour. | `src/telnet.cyr` | small |
| `telnet_announce` never sends DO LINEMODE — the Q-method machinery only engages if the client volunteers first. | `src/telnet.cyr` | small |
| LINEMODE SLC arm describes a validation that was never written. | `src/telnet.cyr` | small |
| Unrecognised subnegotiations (STATUS, NEW_ENVIRON, …) are silently dropped "for now". | `src/telnet.cyr:677, :711` | medium |
| LINEMODE FORWARDMASK / SOFT_TAB / LIT_ECHO — parsed or enumerated, then deferred. | `src/telnet.cyr` | medium |
| BS/DEL do not **edit** the line for clients that never negotiate LINEMODE. 1.6.5 stopped them being *stored*; editing is still open. | 2026-07-26 audit § INFO | small |

### Storage, scale and policy

| Item | Source | Effort |
|---|---|---:|
| Reply enumeration is scan-on-read O(n) per read — [ADR 0005](../adr/0005-threading-via-reply-to.md) named a scale trigger that has arguably fired. | ADR 0005 | large |
| `sort_i64_asc` is an O(n²) insertion sort, run on every `list` and every reply scan. | `src/board.cyr` | small |
| `account_resolve_handle` is an O(n) directory scan with no early exit; its doc comment is orphaned 265 lines away. | `src/account.cyr` | medium |
| `boards_list` renders filesystem directory names verbatim — the one content-ish string still reaching the wire without `send_text` (1.6.4's IAC doubling). | `src/board.cyr` | small |
| The promised `anon-allowed` per-board policy ADR was never written; `open` and `known` are currently **functionally identical** — a documented no-op an operator can set and observe nothing from. | ADR 0006 | medium |
| `.admins` capped at 4 KB (~120 handles) with no continuation. | `src/board.cyr` | small |
| No operator CLI — `agora policy set <board> <mode>`, `agora admins {add,rm,list}`. Operators edit files directly. | roadmap (long-standing) | medium |
| Session-slot exhaustion by a slow-but-real typist is a knowingly-accepted risk with **no recorded acceptance**. | 1.6.4 § Changed | medium |
| Accept-loop rate limiting — the never-taken half of audit M4's fix, blocked on a syscall agnos does not have. | 0.7.0 audit M4 | large |
| cyrius 6.4.51 raised `ALLOC_MAX` 256 MiB → 2 GiB, weakening an accidental backstop on attacker-influenced lengths. Never examined. | CHANGELOG [1.6.2] | medium |
| **Migrate the four `dir_list` call sites onto `dir_list_into`** — the surviving half of agora's own upstream filing. cyrius **6.5.11** removed the fixed 4 KB `getdents` cost (shipped at the 1.6.7 pin, no agora change); **6.5.12** added the caller-owned `dir_list_into(path, scratch, scratch_len, names, names_cap, offs, max_entries)` at `lib/io`'s sibling `lib/fs.cyr:248`, which allocates **nothing** — that half needs agora-side work. Residue today ~75 B/entry (~11 KB per `list` on a 150-post board). **Not mechanical**: it returns entry count ≥ 0 or `-1` open-failed / `-2` scratch-too-small / `-3` names-full / `-4` offs-full, so truncation is a hard **error** where all three sites currently tolerate a partial listing via `max_ids`/`max_boards`/`ACCOUNT_SCAN_MAX`, and `account_resolve_handle` special-cases `entries == 0` — which becomes a live sign bug if swapped naively. Convert the three clean sites first (`src/board.cyr:402`, `:900`, `src/account.cyr:536` — each reads `str_data(entry)` and discards the `Str`, so scratch can come from `cmd_alloc` per ADR 0021). `boards_list` (`src/board.cyr:932`) goes **last**: it stores the `Str` pointer into `out_names` and `src/main.cyr:432-437` dereferences it after return, so it needs a buffer that outlives the per-command arena reset. | CHANGELOG [1.6.7]; upstream filing archived at `cyrius/docs/development/issues/archived/2026-07-26-agora-fs-dir-list-per-call-alloc.md` | medium |

### Architecture debt

| Item | Source | Effort |
|---|---|---:|
| ADR 0022's borrowed world-snapshot pointer is an **unenforced per-module invariant** — door #11 can silently leak or corrupt the session pool. | ADR 0022 | medium |
| The chat-couch bot dispatch was deliberately left out of the descriptor registry; its shared-offset ABI (PY/EZ alias) is unenforced. | ADR 0020 | small |
| ADR 0020 descriptor slots resolve at run time — every new slot carries an untracked smoke-coverage obligation. | ADR 0020 | small |
| ADR 0013's wager audit trail and the commit-reveal provable-fairness alternative remain deferred. (The per-game-vs-global edge question was closed in the ADR at 1.6.6 — 1.3.5's three different edges settled it.) | ADR 0013 | medium |
| `PR_SET_PDEATHSIG` for orphan-on-parent-crash. | ADR 0007 § Out of scope | small |
| Version literals are hand-bumped in three `main.cyr` places; the generated `version_str.cyr` was promised as a v1.0 close-out item. | CHANGELOG [0.2.0] | small |
| Binary strip / DCE-aware emit — promised three times as a "v1.x close-out concern"; the problem changed shape when the 6.4.x stdlib added ~13 MB of BSS. | CHANGELOG | medium |

### Doors and content

| Item | Source | Effort |
|---|---|---:|
| **Olympiad's later events** (gladiators / athletics / boat crews) — thin descriptors on the `compete()` primitive, which was the whole point of building it. **Not in any roadmap until now.** | ADR 0016 | medium |
| Olympiad race field is not tier-scaled — a flat 4 entrants at every meet. | `src/olympiad.cyr` | small |
| Decode/Words rejects most real English words — the 532-entry list is both answer pool *and* guess dictionary. | ADR 0018 | small |
| `AGORA_SERVE=epoll` is accepted and silently aliased to poll; a real epoll loop is "a later optimization". | `src/main.cyr` | medium |

---

## Later — v2.x and speculative

Detail in [`roadmap-future.md`](roadmap-future.md). Unpinned by design: these pull forward when consumer
pressure or operator demand surfaces, not on a calendar.

- **The six v2.x sovereignty pillars** — identity continuity, content-addressed storage, threat-level node
  policy, federation by interest, self-distribution, offline store-and-forward. These are the blocking
  dependency for work already half-promised elsewhere: federated `Origin:` / content-addressed
  `Content-Hash:` post headers are the *stated justification* for the 0.9.0 ABI freeze
  ([ADR 0008](../adr/0008-post-headers-struct.md)) and remain unrealized.
- **Door depth** — QUEST async-PvP (the largest missing piece of the LORD homage; tracked at
  roadmap-future.md:23), The Handler v2 community layer (intercepted rival traffic, inter-section
  sabotage — recorded **only** in a source comment), Port Authority's deep TradeWars endgame (multiple
  planets, alliances).
- **Ashes turn resolution has no daemon**, and its stated premise ("under fork-per-accept with no
  background process") is now half-false — see N2.
- **Chatbot personalities** — ALICE / Racter on the script engine; MegaHAL as a Markov sibling to
  Jabberwacky's retrieval.
- **Protocol reach** — cross-board replies (Reply-To is same-board only); operator opt-in for raw-mode
  ESC/ANSI-art posts; 16→32 hex fingerprint widening (recorded only in a source comment); wire encryption
  (ADR 0006 § Negative points at a pillar that does not exist in roadmap-future).
- **M3** inline-image post bodies via kii, **M4** stored-file deltas via sankoch — gates met, no consumer.
  Note CLAUDE.md asserts post-edit semantics that do not exist yet.
- **$HOME keyfile resolution** depends on `/proc/self/environ` — blocked on the same stdlib work as the
  macOS/Windows ports.

---

## Deliberately not doing

Recorded so nobody re-opens them by accident:

- **Per-source-address session caps** — needs `sys_getpeername`, which **agnos does not have**, so it
  would protect Linux and leave the only always-poll target unprotected; it also mis-fires on a NAT'd
  LAN. Declined at 1.6.4; `MAX_SESS` remains the operator's bound.
- **Absolute session lifetime caps** — would disconnect legitimate long sessions (a QUEST run, an idle
  chat). Declined at 1.6.4.
- **`board_name_valid`'s reserved `_*` prefix** for an internal namespace that will never exist — the
  comment should just go.

---

## Closed

- **v1.0** — all six criteria met and iron-validated on archaemenid, 2026-05-23 (single-session telnet
  round-trip + 8-user fanout). Criteria and evidence: [CHANGELOG](../../CHANGELOG.md) `[1.0.0]`.
- **Milestones M0–M6**, the 0.7.0–0.9.2 hardening line, the 1.1.x–1.4.x door arc, 1.5.0 agnos target,
  1.6.0 poll multiplex and the 1.6.1–1.6.5 hardening line: see the release table above and
  [`CHANGELOG.md`](../../CHANGELOG.md). *This file deliberately no longer restates them.*
- **The 2026-07-26 audit ledger is closed** — 3 HIGH + 5 MEDIUM + 4 LOW all fixed across 1.6.3–1.6.5;
  one INFO item deliberately open (listed in the backlog). [Report](../audit/2026-07-26-audit.md).

---

## Provenance

Rebuilt 2026-07-26 from an exhaustive deferred-work sweep across seven surfaces — all 21 source files,
CHANGELOG `[0.1.0]`–`[1.6.5]`, all 22 ADRs, both audit documents, the state/doc-health ledgers,
tests/examples/CI, and cross-repo commitments — with every "still open" claim verified against the tree
at `88a2387`. **68 items surfaced; ~25 stale notes were found describing work that had already shipped**
and are being retired separately rather than carried here.

Two corrections the sweep produced, worth remembering: the Olympiad's later events were believed to be in
`roadmap-future.md` and are not (they are now in the backlog above), and several items *read* as closed
because a sibling ask shipped — `file_write_atomic` is the clearest, and is now N3.

## Cross-references

- [`state.md`](state.md) — live snapshot: current version, binary size, in-flight slot, next-session boot guide.
- [`roadmap-future.md`](roadmap-future.md) — v2.x sovereignty pillars + long-horizon door/chatbot backlog.
- [`docs/adr/`](../adr/) — **23 ADRs (0001–0023)**, all Accepted/Evergreen. 0001–0008 span M1–0.9.0; the
  1.x arc adds 0009–0020 (doors, Universe, chat, chatbots, wager, war-game, Jabberwacky, Olympiad, Descent
  link, decode engine, decode-as-Handler-lever, door registry); 0021–0022 are the 1.6.x memory work
  (per-command arena, door-state free hook) and **0023 records the dual serve model** (written at 1.6.6,
  amending 0007).
- [`docs/audit/`](../audit/) — audit ledger: 2026-05-23 (0.7.0), 2026-06-15 (1.4.4), 2026-07-26 (1.6.2, closed at 1.6.5).
- [`docs/architecture/`](../architecture/) — non-obvious constraints (001 callptr, 002 lib-sync same-size skip).
- [`CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.
- **Companion project**: [Yeoman's Descent](https://github.com/MacCracken/cyrius-yeomans-descent) — the MUD
  userland. Same telnet substrate, different application semantics; linked by the 1.4.0 gateway.
