# 0010 — Persistent Universe (shared-world multiplayer for door games)

> **Status**: Accepted — **fully implemented in 1.2.0 (cut 2026-06-08)**. All six bites shipped: (1) world-transaction framework, (2) PA shared galaxy (depletable stock + exclusive planet ownership), (3) PA async-PvP garrisons, (4) Smuggler shared district heat + Handler shared city alerts, (5) cross-game leaderboards, (6) closeout. 141/141 tests; smokes `08`/`09`/`10`. The array-in-loop codegen bug that reverted the first bite-2 attempt is cleared on cyrius 6.1.5 (t129 probes it on the real code).
> **Date**: 2026-06-07 (bites 2-6: 2026-06-08)

## Context

The 1.1.0 door subsystem ([ADR 0009](0009-door-games-subsystem.md)) shipped two play modes for all three games — **Practice** (ephemeral, anonymous) and **Solo** (login-gated per-player save). The third mode, **Universe** (shared-world multiplayer), is stubbed: `play <game> universe` prints a roadmap notice. 1.2.0 takes it up.

Universe is the soul of two of the three games — TradeWars 2002 *is* a shared galaxy with PvP, and the Dope-Wars/Handler lineage gains a lot from rival players moving the same economy — so it is worth doing properly. But agora's architecture imposes a hard constraint that shapes every part of the design:

- **Fork-per-accept ([ADR 0007](0007-fork-per-accept-concurrency.md)) means no shared memory across sessions.** Each connection is its own process; the `g_*` session globals are private per child. The *only* way two players touch the same state is **on disk**, serialized with `flock`.
- We already have the two building blocks: the post store's `O_EXCL`-claim + per-board `flock` (ADR 0002/0004), and the 1.1.0 Handler **standings file** (`file_append_locked` — agora's first deliberately-shared-disk artifact). Universe generalizes that pattern from one append-only file to a mutable shared world.
- The games are **pure modules** (ADR 0009): `render → buffer`, `feed(one line) → state`. That purity is the most valuable thing we have and must survive into Universe.

The open question 1.2.0 answers: **how does a shared, concurrently-mutated game world live on disk under fork-per-accept, without losing the pure-module testability or corrupting state under contention?**

## Decision

**A per-game shared world directory under the store, mutated through a lock-read-compute-write "world transaction", with the game logic staying a pure transform.** Universe requires login.

- **Storage split.** Per-player state stays where Solo put it: `<store>/.users/<fp16>/games/<game>.sav` (your ship, your coat, your section). The *contested* state moves to a shared per-game world tree: `<store>/.games/<game>/world/`. A player's save references shared entities by id (sector, district, planet); the world owns the bits everyone shares.
- **World transaction (the core pattern).** Any action that touches shared state runs:
  1. `flock` the world lock (`<store>/.games/<game>/world/.lock`);
  2. read the current world snapshot from disk;
  3. compute the next world + the player's result with a **pure transform** `(world, player, action) → (world', result)`;
  4. write the world back under the held lock (the 1.2.0 bite-1 framework does an in-place `O_TRUNC` write, correct against cooperating lock-holders — proven by `08-world-concurrency.sh`; a temp-file + `rename` or event-log upgrade for crash-during-*write* safety is deferred, see Alternatives);
  5. release the lock.
  The lock/read/write I/O lives in new `door.cyr` world helpers + `main.cyr`; the transform is pure game code, unit-testable exactly like the 1.1.0 `*_feed` functions.
- **Coarse lock first.** One lock per game-world for the first cut — correct and simple at human-paced BBS scale (and fork-per-accept already serializes heavily). Per-sector / per-record locks are a later optimization if contention shows up; they bring lock-ordering hazards, so they wait for evidence.
- **Daily-turn cadence stays.** Per-player turn/action budgets gate how much each player changes the world per real day (wall-clock rollover via `chrono`, the LORD rhythm already used in the games), so no one can monopolize the world in one sitting. The world itself evolves continuously as players act.
- **Indirect / asynchronous PvP**, not real-time. TradeWars-style interaction is mostly async anyway: you act against the *state another player left behind* (a deployed fighter screen, a depleted port, a claimed planet), resolved at your turn from the world snapshot — never a live socket-to-socket duel.

### Per-game shape

- **Port Authority** — the flagship shared galaxy: ports with depletable stock (your buying raises the price the next player sees), player-owned planets, sector-deployed fighters/mines that damage passers, async ship-vs-deployment combat, alliances. (The 1.1.0 galaxy is already deterministic from a seed — the Universe galaxy is generated once into the world dir and then mutated.)
- **Smuggler's Ledger** — a shared metro economy: district prices move with aggregate player buying/selling; a bust raises shared "heat" in that district for everyone for a while.
- **The Handler** — rival sections of one service: shared per-city alert levels (one player's botched op raises heat for all), an **intercept pool** (fragments of other players' cables surface in your queue), anonymous-tip **sabotage** (spend budget to raise a rival's audit risk — costly, deniable, traceable if sloppy), and the existing weekly **standings** as the scoreboard.

### Phasing (1.2.0 bites)

1. **World-transaction framework** in `door.cyr` — world dir + `flock` lock + read/write-snapshot + the transaction wrapper + a multi-process concurrency smoke (two clients hammering one world, assert no lost updates / no corruption). Prove the pattern before any game uses it. **✅ shipped 2026-06-07.**
2. **Port Authority shared galaxy** — generated-once world, depletable port stock, planet ownership (the canonical Universe slice). **✅ shipped 2026-06-08.** Snapshot = a flat-i64 buffer (version + seed + per-(sector,commodity) stock + per-sector planet-owner fp), persisted verbatim by the bite-1 `world_read`/`world_write`. The galaxy *structure* regenerates deterministically from a fixed `PA_UNIVERSE_SEED`; only the contested stock + ownership live in the snapshot. Pure transforms `paw_buy`/`paw_sell` (stock moves the next player's price via `paw_price`) + `paw_claim_planet` (exclusive by sigil fp); the ship-side glue (`pa_buy_u`/`pa_sell_u`, `pa_is_universe`) routes the existing PA screen machine through the world while the per-player ship stays in a `portu` Solo-style save. `main.cyr` wraps every fed line in lock→read→`pa_feed`→write→unlock. Unit-tested t128–t135 (incl. t129, the distinct-write-readback that re-cleared the reverted-attempt codegen bug on cyrius 6.1.5); cross-session shared-world + login-gating + exclusive ownership proven by `docs/examples/09-universe-port.sh`.
3. **PA deployments + async PvP** — **✅ shipped 2026-06-08.** Deploy ship fighters as a sector **garrison** (`paw_deploy` + the `[G]arrison` action); transiting a rival's garrison auto-resolves a fighter clash on arrival (`pa_arrival_universe` + pure `pa_clash_loss`) — combat against the assets the defender left behind, never a live duel. World snapshot bumped to v2. t136-t138. (Mines + multi-player alliances remain a deeper, unpinned follow-on.)
4. **Smuggler's shared economy** + **Handler shared alert / intercepts / sabotage** — **✅ shipped 2026-06-08** (core mechanic each). Smuggler: shared per-district **heat** (`slw_*`) — busts/dealing raise it, high heat raises the next arrival's cop odds. Handler: shared per-city **alerts** (`thw_*`) — burns/false-accusations raise them, high total alert drains confidence faster daily. The per-line world transaction is generalized to dispatch by game. t139-t140. (Smuggler aggregate price pressure, Handler intercept pool + anonymous-tip sabotage remain unpinned follow-ons.)
5. **Leaderboards** generalized from the Handler standings file to all three games — **✅ shipped 2026-06-08.** Finished runs append to `<store>/.games/<game>/leaderboard`; `scores <game>` shows the top-10. t141; `10-leaderboard.sh`.
6. Closeout — **✅ 2026-06-08.** VERSION → 1.2.0; three inline `main.cyr` literals; full clean DCE build (678,776 B); 141/141; docs synced.

Start narrow (framework + one depletable-stock slice) and get a concurrency smoke green before layering PvP.

## Consequences

- **Positive** — real multiplayer, the TW2002 soul, sticky community play; reuses the proven `flock` + atomic-claim patterns from posts and standings; the pure-transform rule survives, so world logic stays unit-testable; world state is operator-visible flat files (debuggable, backup-able).
- **Negative** — genuine new complexity: concurrency, atomicity, snapshot staleness, and **world-format versioning** that's now load-bearing across releases. A coarse world lock contends under high fanout. Concurrency itself isn't unit-testable — it needs multi-process integration smokes (the per-turn transform stays a unit test; the *interleaving* gets a smoke, mirroring how ADR 0007's fork loop is smoke-tested, not unit-tested).
- **Neutral** — Universe requires login (a persistent actor needs an identity); anonymous players keep Practice/Solo. The daily-turn budget becomes a fairness lever, not just flavor. The per-player Solo save and the shared world are separate artifacts with separate lifecycles.

## Alternatives considered

- **In-memory shared state** — rejected outright; fork-per-accept gives each session a private address space (ADR 0007 § Negative: "no shared state across sessions"). Non-starter.
- **A long-lived coordinator/daemon holding the world in memory, players talking to it over IPC/socket** — powerful (real-time, no per-turn disk churn, fine-grained concurrency), but it adds a major moving part with its own lifecycle, crash-recovery, and supervision story, and breaks the "agora is one fork-per-accept binary" simplicity. Deferred to a potential v2 if the flat-file + `flock` model hits a real contention or latency wall. The disk-transaction model is the right *first* cut.
- **SQLite / an embedded DB for world state** — no cyrius stdlib support; flat files + `flock` are agora's whole storage idiom (ADR 0002). A DB would be a new external dependency for marginal gain at BBS scale.
- **Per-game bespoke concurrency** — rejected; three divergent locking implementations is three times the surface for race bugs. One shared world-transaction framework in `door.cyr`, three games on top.
- **Event-log world (append-only events + periodic snapshot)** instead of a locked snapshot file — more crash-resilient and audit-friendly, but more machinery than the first cut needs. The temp-file + `rename` snapshot is atomic enough; revisit the event log if world history/rollback becomes a feature.
