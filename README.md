# agora

> Telnet-served BBS for AGNOS. Posts, messages, file-share. Cyrius-native.

**Status**: **v1.2.0 — 2026-06-08** lands the **Persistent Universe** ([ADR 0010](docs/adr/0010-persistent-universe.md)): shared-world multiplayer for all three door games over a `flock`'d on-disk world transaction (fork-per-accept-safe). **Port Authority** gets a shared galaxy — depletable port stock that moves the market + exclusive planet ownership + async-PvP garrisons; **Smuggler's Ledger** gets shared district heat; **The Handler** gets shared city alerts; all three feed **cross-game leaderboards** (`scores <game>`). Reach it via `play <game> universe` (login-gated). Built on **v1.1.0** (2026-06-07) — the BBS **door / games** subsystem ([ADR 0009](docs/adr/0009-door-games-subsystem.md)): three in-session text games (**Smuggler's Ledger**, **Port Authority**, **The Handler**) via `play <game> [practice|solo]`. And on **v1.0.0** (2026-05-23, iron-validated on archaemenid): a multi-user, multi-board threaded BBS with sigil-backed Ed25519 challenge/response auth, per-board posting policy, fork-per-connection concurrency, audit-hardened input, and a frozen ABI. All v1.0 criteria met (M0-M6 + security sweep + hardening shipped; `cyrius audit` clean; archaemenid telnet round-trip green; 8-user concurrent fanout green; 0.7.0 audit findings all discharged; full RFC 854 / 1143 / 1073 / 1091 / 1184 conformance). Live state in [`docs/development/state.md`](docs/development/state.md); doc currency in [`docs/doc-health.md`](docs/doc-health.md). Post-1.0 directions in [`docs/development/roadmap-future.md`](docs/development/roadmap-future.md).

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

End-to-end walkthrough in [`docs/guides/getting-started.md`](docs/guides/getting-started.md); runnable examples in [`docs/examples/`](docs/examples/) (01–06). Cyrius toolchain pinned to 6.0.1 in `cyrius.cyml`.

## Architecture

```
agora binary (~679 KB static ELF at 1.2.0)
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
├── src/handler.cyr         The Handler (door game)   (all four: ADR 0009)
└── src/test.cyr            121-test conformance suite
```

Stdlib consumed: net + io + fs + str + vec + alloc + bannermanor (MOTD) + darshana (SGR) + sigil + freelist + bigint + ct (the ed25519 call chain). No external deps beyond cyrius.

## Docs

- [`docs/development/roadmap.md`](docs/development/roadmap.md) — milestones, sub-bites, v1.0 criteria.
- [`docs/development/state.md`](docs/development/state.md) — current version, binary size, in-flight slot. Refreshed every release.
- [`docs/doc-health.md`](docs/doc-health.md) — fresh / stale / archive ledger across the whole doc tree.
- [`docs/adr/`](docs/adr/) — architecture decision records (why we chose X over Y).
- [`docs/architecture/`](docs/architecture/) — non-obvious invariants the code relies on.
- [`docs/guides/`](docs/guides/) — task-oriented how-tos (`getting-started.md` first).
- [`docs/examples/`](docs/examples/) — seven runnable smoke scripts covering build / auth / concurrency / policy / door games (`07-play-door.sh`).
- [`BENCHMARKS.md`](BENCHMARKS.md) — telnet-parser baseline (10 ns/byte hot path, unchanged across every release since M1-close).
- [`CHANGELOG.md`](CHANGELOG.md) — per-tag chronology.
- [`CLAUDE.md`](CLAUDE.md) — durable rules for agent sessions.

Full doc-tree convention: [first-party-documentation.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md).

## Companion project

**MUD userland** — separate repo, shares the telnet listener primitive but adds real-time room/object model. Same wire-protocol substrate, different application semantics. Both surface the AGNOS 1.32.x networking arc to real users.

## License

GPL-3.0-only.
