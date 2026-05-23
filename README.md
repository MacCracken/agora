# agora

> Telnet-served BBS for AGNOS. Posts, messages, file-share. Cyrius-native.

**Status**: v0.1.0 scaffold shipped — argv dispatch + stub verbs. **M1 in progress**: cross-platform telnet listener on cyrius `lib/net.cyr` (Linux today; macOS / Windows / AGNOS follow). Live state in [`docs/development/state.md`](docs/development/state.md); doc currency in [`docs/doc-health.md`](docs/doc-health.md).

## Etymology

Three layers:

1. Ancient Greek **ἀγορά** *(agorá)* — the civic marketplace and public-assembly ground of the Greek city-state. Where citizens gathered to discuss news, debate, share knowledge, conduct exchange. Exact functional match for a BBS: an asynchronous public surface for posting, reading, and discussion.

2. Doja Cat **"Agora Hills"** — track 4 on *Scarlet* (2023). Drops the 'u' from the city name to land the Greek-civic-marketplace reference directly.

3. **Agoura Hills, CA** — the city literally around the corner from the project's home base in Thousand Oaks. Named after the Basque shepherd Pierre Agoure (1872 land tract), whose surname phonetically echoes the Greek root. Doja Cat's track and the city share the pronunciation; the project takes the Greek spelling to thread all three references at once.

The naming convention adds a **Greek lane** to the AGNOS ecosystem (previously Sanskrit/Hindi for system libs + English-wordplay or Polynesian for user-facing tools — see [[feedback_naming_lanes]]). The lane opens with a multi-layer convergence — like `kii` in the existing Polynesian/East-Asian/English-phonetic micro-cluster, agora threads ancient civic-marketplace + 2023 hip-hop reference + literal hyperlocal Conejo Valley geography. Three independent angles all describe the same gathering-place semantics.

## Roadmap

Full milestone table + sub-bites + v1.0 criteria in [`docs/development/roadmap.md`](docs/development/roadmap.md). Current state — M0 (0.1.0) shipped 2026-05-23; **M1 in progress**: cross-platform telnet listener (RFC 854 + LINEMODE 1184) on `lib/net.cyr`. Decoupled from the AGNOS kernel — Linux today, AGNOS becomes one target among many as `lib/net.cyr` grows platform backends ([ADR 0001](docs/adr/0001-cross-platform-listener-decoupled-from-agnos.md)).

## Build

```sh
cyrius build src/main.cyr build/agora
./build/agora help
```

Cyrius toolchain pinned to 6.0.1 in `cyrius.cyml` (see [[project_cyrius_5x_6x_boundary]]).

## Architecture (planned)

```
agora binary
├── src/main.cyr            argv dispatch
├── src/telnet.cyr (M1)     RFC 854 + RFC 1184 wire protocol
├── src/board.cyr (M5)      post / thread storage
├── src/ansi.cyr (M2)       darshana consumer (BBS color/cursor)
├── src/banner.cyr (M2)     bannermanor consumer (ASCII MOTD)
├── src/image.cyr (M3)      kii consumer (inline image posts)
├── src/auth.cyr (M6)       sigil-backed user accounts
└── src/test.cyr            test harness
```

## Docs

- [`docs/development/roadmap.md`](docs/development/roadmap.md) — milestones, sub-bites, v1.0 criteria.
- [`docs/development/state.md`](docs/development/state.md) — current version, binary size, in-flight slot. Refreshed every release.
- [`docs/doc-health.md`](docs/doc-health.md) — fresh / stale / archive ledger across the whole doc tree.
- [`docs/adr/`](docs/adr/) — architecture decision records (why we chose X over Y).
- [`docs/architecture/`](docs/architecture/) — non-obvious invariants the code relies on.
- [`docs/guides/`](docs/guides/) — task-oriented how-tos (`getting-started.md` first).
- [`CHANGELOG.md`](CHANGELOG.md) — per-tag chronology.
- [`CLAUDE.md`](CLAUDE.md) — durable rules for agent sessions.

Full doc-tree convention: [first-party-documentation.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md).

## Companion project

**MUD userland** — separate repo, shares the telnet listener primitive but adds real-time room/object model. Same wire-protocol substrate, different application semantics. Both surface the AGNOS 1.32.x networking arc to real users.

## License

GPL-3.0-only.
