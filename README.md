# agora

> Telnet-served BBS for AGNOS. Posts, messages, file-share. Cyrius-native.

**Status**: **v1.3.7 — 2026-06-09** adds **Ashes of Empire** ([ADR 0014](docs/adr/0014-async-shared-world-strategy.md)) — the war-game and agora's first genuinely **shared-world** game: logged-in citizens act on one common ring map of twelve provinces, found an empire, `march <src> <dst> <n>` armies between neighbours (one order, three intents — move / attack / reinforce), and forge or betray alliances (allied armies reinforce or merge into coalitions that fight as one bloc; betrayal falls out of re-checking alliance at resolution). Turn-batch combat resolves **lazily on the next caller's entry** (mirroring QUEST's `qu_day_tick`, no daemon) — the deliberate rehearsal of shared-state mutation between concurrent callers on the proven 1.2.0 `flock`'d world-transaction framework, the on-ramp to the planned 1.4.0 Descent/MUD link. The batch-resolution combat transform is a pure, order-independent function (the most complex in the door tree). Built on **v1.3.6** (2026-06-09) — **Olympiad** ([ADR 0016](docs/adr/0016-olympiad-competition-primitive.md)), a Greco-Roman games-**owner** sim on the event-agnostic `compete()` primitive (a form-weighted kernel-CSPRNG draw resolves the contest AND prices the book). Built on **v1.3.5** (2026-06-08) — **casino integrations** (the shared wager module embedded as a cantina Dabo Wheel, back-alley Bones, and a tavern Card Table across the existing doors). Built on **v1.3.4** (2026-06-08) — **Wager** ([ADR 0013](docs/adr/0013-wagering-module-rng-fairness.md)), the shared casino/wagering primitive (`bet → draw → resolve → settle`, a kernel-CSPRNG draw). Built on **v1.3.3** (2026-06-08) — **Jabberwacky** (Rollo Carpenter, 1988→, [ADR 0015](docs/adr/0015-jabberwacky-corpus-learning.md)) — agora's first corpus-**learning** chatbot and a different engine kind from the fixed-script Eliza/PARRY: it remembers what people say and replays it (word-overlap retrieval over a growing `(stimulus, response)` corpus + a learn-the-transition rule). A baked-in shared seed personality plus a per-user **learned layer that persists across sessions** via `play jabberwacky solo` (`.users/<fp16>/games/jabberwacky.sav`) — no global corpus, so no cross-user poisoning/privacy surface. Also `play jabberwacky` (ephemeral practice) and a private `/jabberwacky` chat side-channel. No new dependencies. Built on **v1.3.2** (2026-06-08) — **QUEST** ("Quest of the Undying Emerald Sovereign Throne", `play quest`) — a **Legend of the Red Dragon** homage door RPG: a town hub + LORD's daily-rationed forest grind + twelve level-masters that secretly trace the alchemical Great Work + an Emerald-Tablet fragment spine + the Sovereign ascension; solo-saveable with a leaderboard. Built on **v1.3.1** (2026-06-08) — **PARRY** (Kenneth Colby, 1972), the paranoid foil to Eliza and agora's first **affect-driven** chatbot: internal fear/anger/mistrust that decays, spikes when provoked, and gates its replies, with a Mafia/bookie delusion story it steers toward; reachable as a `play parry` door and a private `/parry` chat side-channel. Built on **v1.3.0** (2026-06-08) — the **chat area + Eliza** ([ADR 0011](docs/adr/0011-chat-area.md)): the synchronous public-assembly surface — a live, multi-user, login-gated teleconference on a per-channel `flock`'d ring transcript, live-tailed **by sequence number** on the recv-timeout poll tick (fork-per-accept-safe, no daemon), reachable via `chat [channel]` — plus **Eliza** (Weizenbaum's 1966 DOCTOR) as a pure-module chatbot, reachable as a `play eliza` door and a private `/eliza` side-channel. No new dependencies. Built on **v1.2.0** (2026-06-08) — the **Persistent Universe** ([ADR 0010](docs/adr/0010-persistent-universe.md)): shared-world multiplayer for all three door games over a `flock`'d on-disk world transaction (fork-per-accept-safe). **Port Authority** gets a shared galaxy — depletable port stock that moves the market + exclusive planet ownership + async-PvP garrisons; **Smuggler's Ledger** gets shared district heat; **The Handler** gets shared city alerts; all three feed **cross-game leaderboards** (`scores <game>`). Reach it via `play <game> universe` (login-gated). Built on **v1.1.0** (2026-06-07) — the BBS **door / games** subsystem ([ADR 0009](docs/adr/0009-door-games-subsystem.md)): three in-session text games (**Smuggler's Ledger**, **Port Authority**, **The Handler**) via `play <game> [practice|solo]`. And on **v1.0.0** (2026-05-23, iron-validated on archaemenid): a multi-user, multi-board threaded BBS with sigil-backed Ed25519 challenge/response auth, per-board posting policy, fork-per-connection concurrency, audit-hardened input, and a frozen ABI. All v1.0 criteria met (M0-M6 + security sweep + hardening shipped; `cyrius audit` clean; archaemenid telnet round-trip green; 8-user concurrent fanout green; 0.7.0 audit findings all discharged; full RFC 854 / 1143 / 1073 / 1091 / 1184 conformance). Live state in [`docs/development/state.md`](docs/development/state.md); doc currency in [`docs/doc-health.md`](docs/doc-health.md). Post-1.0 directions in [`docs/development/roadmap-future.md`](docs/development/roadmap-future.md).

## Etymology

Three layers:

1. Ancient Greek **ἀγορά** *(agorá)* — the civic marketplace and public-assembly ground of the Greek city-state. Where citizens gathered to discuss news, debate, share knowledge, conduct exchange. Exact functional match for a BBS: an asynchronous public surface for posting, reading, and discussion.

2. Doja Cat **"Agora Hills"** — track 4 on *Scarlet* (2023). Drops the 'u' from the city name to land the Greek-civic-marketplace reference directly.

3. **Agoura Hills, CA** — the city literally around the corner from the project's home base in Thousand Oaks. Named after the Basque shepherd Pierre Agoure (1872 land tract), whose surname phonetically echoes the Greek root. Doja Cat's track and the city share the pronunciation; the project takes the Greek spelling to thread all three references at once.

The naming convention adds a **Greek lane** to the AGNOS ecosystem (previously Sanskrit/Hindi for system libs + English-wordplay or Polynesian for user-facing tools — see [[feedback_naming_lanes]]). The lane opens with a multi-layer convergence — like `kii` in the existing Polynesian/East-Asian/English-phonetic micro-cluster, agora threads ancient civic-marketplace + 2023 hip-hop reference + literal hyperlocal Conejo Valley geography. Three independent angles all describe the same gathering-place semantics.

## Roadmap

Full milestone table + sub-bites + v1.0 criteria in [`docs/development/roadmap.md`](docs/development/roadmap.md). M0–M6 + 0.7.0 security sweep + 0.8.x audit followups + 0.9.0 ABI freeze + 0.9.1 doc-pass + 0.9.2 closeout sweep all shipped 2026-05-23. **v1.0.0 cut after archaemenid iron validation, same day.** Post-1.0 directions live in [`docs/development/roadmap-future.md`](docs/development/roadmap-future.md) — six unpinned v2.x sovereignty pillars, pulled forward on consumer pressure rather than calendar.

## Build

```sh
cyrius build src/main.cyr build/agora
./build/agora help
./build/agora serve 2323     # telnet on localhost:2323
```

End-to-end walkthrough in [`docs/guides/getting-started.md`](docs/guides/getting-started.md); runnable examples in [`docs/examples/`](docs/examples/) (01–14). Cyrius toolchain pinned in `cyrius.cyml` (`[package].cyrius`).

## Architecture

```
agora binary (~874 KB static ELF at 1.3.7)
├── src/main.cyr            argv dispatch + telnet handle_client + session helpers
│                           + login flow + CLI keygen/register/whoami
│                           + fork-per-accept loop (ADR 0007)
├── src/telnet.cyr          RFC 854 IAC + RFC 1143 Q-method + RFC 1073 NAWS
│                           + RFC 1091 TT + RFC 1184 LINEMODE
├── src/board.cyr           post storage + threading + flock + board layout
│                           + per-board policy (ADRs 0002 / 0003 / 0004 / 0005)
│                           + PostHeaders struct (ADR 0008)
├── src/account.cyr         sigil Ed25519 + fingerprint + handle validation
│                           + keyfile + nonce / sig parse + From-header
│                           (ADR 0006, M6)
├── src/door.cyr            door framework: PRNG + int helpers + save IO
├── src/smuggler.cyr        Smuggler's Ledger (door game)
├── src/port_authority.cyr  Port Authority (door game)
├── src/handler.cyr         The Handler (door game)   (all three: ADR 0009)
│                           + Persistent Universe shared worlds (ADR 0010)
├── src/chat.cyr            live chat area: flock'd ring transcript (ADR 0011)
├── src/eliza.cyr           ELIZA DOCTOR chatbot: play eliza + /eliza (ADR 0011)
├── src/parry.cyr           PARRY affect-engine chatbot: play parry + /parry
├── src/quest.cyr           QUEST: a LORD-homage door RPG (play quest)
├── src/jabberwacky.cyr     Jabberwacky: corpus-learning chatbot (ADR 0015)
├── src/wager.cyr           shared casino/wagering primitive (ADR 0013)
├── src/olympiad.cyr        Olympiad: games-owner sim + compete() (ADR 0016)
├── src/ashes.cyr           Ashes of Empire: async shared-world war-game (ADR 0014)
└── src/test.cyr            206-test conformance suite
```

Stdlib consumed: net + io + fs + str + vec + alloc + bannermanor (MOTD) + darshana (SGR) + sigil + freelist + bigint + ct (the ed25519 call chain). No external deps beyond cyrius.

## Docs

- [`docs/development/roadmap.md`](docs/development/roadmap.md) — milestones, sub-bites, v1.0 criteria.
- [`docs/development/state.md`](docs/development/state.md) — current version, binary size, in-flight slot. Refreshed every release.
- [`docs/doc-health.md`](docs/doc-health.md) — fresh / stale / archive ledger across the whole doc tree.
- [`docs/adr/`](docs/adr/) — architecture decision records (why we chose X over Y).
- [`docs/architecture/`](docs/architecture/) — non-obvious invariants the code relies on.
- [`docs/guides/`](docs/guides/) — task-oriented how-tos (`getting-started.md` first).
- [`docs/examples/`](docs/examples/) — nineteen runnable smoke scripts covering build / auth / concurrency / policy / door games / Universe / leaderboards / chat (`11-chat.sh`) / Eliza (`12-eliza.sh`) / PARRY (`13-parry.sh`) / QUEST (`14-quest.sh`) / Jabberwacky (`15-jabberwacky.sh`) / casino (`16-casino.sh`) / Olympiad (`17-olympiad.sh`) / Ashes of Empire (`18-ashes.sh`, `19-ashes-concurrency.sh`).
- [`BENCHMARKS.md`](BENCHMARKS.md) — telnet-parser baseline (10 ns/byte hot path, unchanged across every release since M1-close).
- [`CHANGELOG.md`](CHANGELOG.md) — per-tag chronology.
- [`CLAUDE.md`](CLAUDE.md) — durable rules for agent sessions.

Full doc-tree convention: [first-party-documentation.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md).

## Companion project

**MUD userland** — separate repo, shares the telnet listener primitive but adds real-time room/object model. Same wire-protocol substrate, different application semantics. Both surface the AGNOS 1.32.x networking arc to real users.

## License

GPL-3.0-only.
