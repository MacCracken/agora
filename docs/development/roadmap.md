# agora — Roadmap

> **Last Updated**: 2026-06-09
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

---

## In progress

**1.4.0 Descent link shipped 2026-06-10.** The gateway door (`src/descent.cyr`, [ADR 0017](../adr/0017-descent-link-gateway.md)) bridges a logged-in agora citizen into the sibling **Yeoman's Descent** MUD (`../cyrius-yeomans-descent`) over the shared telnet substrate — the BBS is now the front door to the MUD. A transparent TCP byte-proxy: the `descent` verb (login-gated) reads an operator endpoint from `<store>/.descent`, dials it (`net_connect_nb`), and shuttles bytes both ways via a `poll`-multiplexed loop until either side closes; the MUD's own telnet negotiation + login flow through verbatim. **Sigil identity hand-off is deferred** — the MUD has no external-identity path, so a true hand-off is a two-repo follow-on bite (ADR 0017 § Decision); for now the citizen re-authenticates inside the MUD. Toolchain pin 6.1.17 → **6.1.23**. 206 → **208 tests** (t207/t208 endpoint parsing); 874,168 → **880,256 B**; wire smoke `20-descent.sh`. **Next**: the deferred identity hand-off, the Olympiad's later events (gladiators/athletics/boat crews), and deeper-Universe work — all unpinned.

**Prior — 1.3.7 Ashes of Empire shipped 2026-06-09.** The war-game (`src/ashes.cyr`, [ADR 0014](../adr/0014-async-shared-world-strategy.md)) — an asynchronous shared-world strategy door, agora's deliberate rehearsal of shared-state mutation between concurrent callers before the MUD. Twelve provinces on a ring; found an empire, `march <src> <dst> <n>` (one order, three intents) queued to a shared snapshot, `ally`/`break` diplomacy (allied armies reinforce / coalition together; betrayal falls out of re-checking alliance at resolution). Turn-batch combat resolves **lazily on the next caller's entry** (mirroring `qu_day_tick`, no daemon); the batch transform is a pure, order-independent function — the most complex in the door tree. Built across five bites; login-gated, inherently universe-mode. 197 → **206 tests** (t198-t206); 841,824 → **874,168 B**; pin 6.1.15 → **6.1.17**; wire smokes `18-ashes.sh` + `19-ashes-concurrency.sh` (N concurrent foundings, all distinct under the `flock`).

**Prior — 1.3.6 Olympiad shipped 2026-06-09.** A Greco-Roman games-**owner** sim (`src/olympiad.cyr`, [ADR 0016](../adr/0016-olympiad-competition-primitive.md)) — agora's biggest door and the wager module's flagship. You own a chariot stable, **train or rest** it across a daily-action economy, and climb a 12-meet ladder (Veii → the Circus Maximus) to the **tethrippon crown**, wagering on every race. The keystone is the event-agnostic **`compete()` primitive**: a form-weighted **kernel-CSPRNG draw resolves the race AND the same weights price the book** (`wager.cyr`'s new `wager_payout` fractional helper settles the pari-mutuel bet — a favourite pays < 1×). The fairness split moves up a level: the rival field is seeded/replayable, the winner is CSPRNG/non-replayable. Built across five bites; solo-saveable + `scores olympiad`. Later events (gladiators, athletics, boat crews) are thin descriptors on the primitive. 188 → **197 tests** (t189-t197); 812,528 → **841,824 B**; smoke `17-olympiad.sh`.

**Prior — 1.3.5 Casino integrations shipped 2026-06-08.** The shipped 1.3.4 wager module (`src/wager.cyr`) embedded across the three existing doors — the **first user-reachable wager surface**: a cantina **Dabo Wheel** in Port Authority (`PSCR_GAMBLE`, weighted 3-light 1×/2×/5×, 3% edge), back-alley **Bones** in Smuggler's Ledger (`SCR_DICE`, even-money, 6% edge), a tavern **Card Table** in QUEST (`QSCR_CARDS`, 4-suit 3:1, 4% edge). Three distinct table shapes, one shared module; each bets the game's existing gold field within a single feed call, so no save-format change. Shared `door_parse_2int` + `wager_reason`; per-game table builders unit-pinned (t186-t188). The three integrations chose *different* edges for tone, validating ADR 0013's per-game-edge decision. 185 → **188 tests**; 801,288 → **812,528 B** (wager now reachable, not NOPed); pin 6.1.14 → **6.1.15**; smoke `16-casino.sh`.

**Prior — 1.3.4 Wager shipped 2026-06-08.** The shared casino/wagering primitive (`src/wager.cyr`, [ADR 0013](../adr/0013-wagering-module-rng-fairness.md) → Accepted): bet validation + per-game payout tables + an explicit per-table basis-point house edge + the kernel-CSPRNG entropy draw (the one deliberately non-replayable point, distinct from the games' seeded PRNG) + pure resolve/settle with a structural no-negative-balance invariant. Built **ahead of its consumers** (DCE-NOPed until 1.3.5 wires it), the same way the 1.2.0 world-transaction framework preceded its games. A pre-cut multi-agent adversarial review (11 confirmed / 1 refuted, no critical/high) hardened the gold-accounting edges (edge-haircut overflow → staged divide-before-multiply; `wager_resolve` seam guards; negative-edge clamp; settle overflow guard; the `wager_pick` zero-total-vs-residual contract). 178 → **184 tests** (t179–t184); 797,640 → **801,288 B**; pin 6.1.12 → **6.1.14**.

**Prior — 1.3.3 Jabberwacky shipped 2026-06-08.** agora's first corpus-learning / persistent-state bot (`src/jabberwacky.cyr`, [ADR 0015](../adr/0015-jabberwacky-corpus-learning.md)): word-overlap retrieval over a `(stimulus, response)` corpus + a learn-the-transition rule (previous line → current line). A baked-in seed personality (shared) + a per-user **learned layer** that persists across sessions via `play jabberwacky solo` (`.users/<fp16>/games/jabberwacky.sav`) — no global corpus, so no cross-user poisoning/privacy surface (the risk [ADR 0012](../adr/0012-chatbot-framework.md) flagged). Also `play jabberwacky` (ephemeral practice) + `/jabberwacky` couch. A pre-cut multi-agent adversarial review (11 confirmed / 10 refuted, no critical/high) fixed an overlap double-count, two save/load robustness gaps, a mid-word truncation, a couch-reentry bridge, and a pronoun tie-break. 166 → **178 tests** (t167-t178); 782,064 → **797,640 B**; pin 6.1.10 → **6.1.12**; smoke `15-jabberwacky.sh`.

**Prior — 1.3.2 QUEST shipped 2026-06-08.** The LORD-homage door (`src/quest.cyr`, `play quest`): town hub + daily-rationed forest grind + the twelve Great-Work masters + the Emerald-fragment spine + the Sovereign ascension; solo-saveable + `scores quest`. Single-player climb (async-PvP/Universe deferred). A pre-cut adversarial review caught + fixed a critical `play quest universe` worker-crash, a monotonic-clock daily-reset soft-lock, and an unmapped `scores quest`. 160 → **166 tests** (t161-t166); 752,240 → **782,064 B**; pin 6.1.9 → **6.1.10**; smoke `14-quest.sh`.

**Prior — 1.3.1 PARRY shipped 2026-06-08.** Colby's 1972 paranoid chatbot as a sibling to Eliza (`src/parry.cyr`): reuses the 1.3.0 ELIZA text primitives but adds an **affect engine** (fear/anger/mistrust state, per-turn input classification, mood-gated dispatch, the Mafia/bookie delusion story arc) — reachable as `play parry` + a private `/parry` side-channel (the chat couch generalized to host both bots). A pre-cut adversarial review verified the affect model faithful and fixed one rotation defect. 155 → **160 tests** (t156-t160); 730,792 → **752,240 B**; smoke `13-parry.sh`.

**Prior — 1.3.0 Chat area + Eliza shipped 2026-06-08.** All three bites landed ([ADR 0011](../adr/0011-chat-area.md)): (1) the chat surface — per-channel `flock`'d **ring transcript** under `<store>/.chat/<channel>/`, a new `MODE_CHAT` with **live-tail by sequence number** on the `CHAT_POLL_SECS` recv-timeout tick (a `-EAGAIN` read in chat flushes new lines instead of disconnecting), `chat [channel]` / `/leave` / `/help`, login-gated; (2) **Eliza** (`src/eliza.cyr`) — the Weizenbaum 1966 DOCTOR as a pure decomposition/reassembly engine, reachable as a `play eliza` door + a private `/eliza` side-channel (replies only to the asker, never the room); (3) closeout. A pre-cut multi-agent adversarial review caught + fixed three real defects (Eliza `you`→`me` / `you are`→`I am` reflection grammar; a chat live-tail watermark drop under burst). 141 → **155 tests** (t142-t155); 678,776 → **730,792 B** (on cyrius 6.1.5 → **6.1.9**); cross-session + live-tail proven by `11-chat.sh`, both Eliza surfaces + privacy by `12-eliza.sh`. Detail: [ADR 0011](../adr/0011-chat-area.md) + CHANGELOG [1.3.0] + [`state.md`](state.md).

**Next planned (see *Planned* below):** **1.4.0 Descent link** (BBS → MUD gateway) — the whole 1.3.x door arc (Chat+Eliza → PARRY → QUEST → Jabberwacky → Wager → casino integrations → Olympiad → Ashes of Empire) has shipped, with the 1.3.7 war-game deliberately retiring the shared-state-mutation-between-callers concurrency risk on the way. Deeper Universe (PA alliances/mines, Handler intercepts/sabotage, Smuggler aggregate price pressure), the Olympiad's later events (gladiators/athletics/boat crews), and further chatbot personalities (ALICE/Racter on the script engine; MegaHAL Markov generation as a sibling to Jabberwacky's retrieval) stay unpinned until pulled ([`roadmap-future.md`](roadmap-future.md)).

**Deferred (pull when a deployment asks):**

- `agora policy set <board> <mode>` + `agora admins {add,rm,list}` CLI verbs (operators currently edit `.policy` / `.admins` files directly).
- Door directions still unpinned beyond 1.2.0 (Handler world-event track + legacy ranks, PA citadels/mining deep endgame, the 2400-baud teletype effect) live in [`roadmap-future.md`](roadmap-future.md) § Door games.

---

## Planned

> The 1.3.x door arc — Chat+Eliza ([ADR 0011](../adr/0011-chat-area.md)), PARRY, QUEST, Jabberwacky ([ADR 0015](../adr/0015-jabberwacky-corpus-learning.md)), Wager ([ADR 0013](../adr/0013-wagering-module-rng-fairness.md)), casino integrations, Olympiad ([ADR 0016](../adr/0016-olympiad-competition-primitive.md)), and Ashes of Empire ([ADR 0014](../adr/0014-async-shared-world-strategy.md)) — has all shipped (see the release table + *In progress* above; full rationale in each ADR + [`CHANGELOG.md`](../../CHANGELOG.md)). The only pinned item remaining is the Descent link.

### 1.4.0 — Descent link (BBS → MUD gateway)

agora and **Yeoman's Descent** ([`../cyrius-yeomans-descent`](https://github.com/MacCracken/cyrius-yeomans-descent) — a Cyrius-native, gritty techno-feudal MUD with its own TCP server) are the two halves of the AGNOS public-assembly surface: same telnet substrate, different application semantics (async boards/games vs. a real-time room/object world). 1.4.0 makes the BBS the **front door to the MUD** — a logged-in agora citizen can step through a portal into the Descent without dialing a second address.

**Shape (for its ADR when it pulls forward):**

- **A `descent` (or `mud`) door/portal** in the agora session: rather than a pure-module game, this door **bridges the socket** to the running Yeoman's Descent server (the MUD owns its own world loop; agora does not re-implement it). Likely a transparent TCP proxy — agora dials the MUD's listener and shuttles bytes both ways until the player exits back to the BBS.
- **Identity hand-off** — carry the agora **sigil identity** (`g_session_fp` / handle) across the link so the MUD can bind the same citizen (a shared-identity story, adjacent to v2.x Pillar 1 *identity continuity*), instead of a second login. Mechanism TBD: a signed hand-off token vs. a trusted local socket.
- **Operator config** — the MUD endpoint (host:port or local socket) is operator-set, like `.policy`; absent config → the door reports "no Descent linked."
- **Boundary discipline** — agora stays the BBS; it does not absorb MUD semantics. The link is a *gateway*, so the two projects keep independent release cycles and the wire-proxy is the only coupling.

**Open questions:** proxy vs. launch-a-client model under fork-per-accept; the identity-token format + trust model; whether the MUD runs co-located (same host) or remote; graceful teardown when either side drops. Earns a dedicated ADR (and possibly a small shared-protocol note in the genesis repo) when the link is cut.

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
- [`docs/adr/`](../adr/) — **sixteen ADRs (0001–0016)**, all Accepted/Evergreen. 0001-0008 land across M1–0.9.0 (cross-platform listener / one-file-per-post / RFC-822 headers / board layout / Reply-To threading / identity model / fork-per-accept concurrency / PostHeaders struct ABI); the 1.x door arc adds 0009 (door subsystem), 0010 (Persistent Universe), 0011 (chat area), 0012 (chatbot framework), 0013 (wager/RNG fairness), 0014 (async shared-world war-game — Accepted at 1.3.7), 0015 (Jabberwacky corpus-learning), 0016 (Olympiad competition primitive).
- [`docs/audit/`](../audit/) — security audit ledger; first entry 2026-05-23 (0.7.0 sweep).
- [`docs/doc-health.md`](../doc-health.md) — fresh/stale ledger across the whole doc tree.
- [`CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.
