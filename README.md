# agora

> Telnet-served BBS for AGNOS. Posts, messages, file-share. Cyrius-native.

**Status**: **v1.7.0 — 2026-08-22** closes the pinned roadmap. The server can finally **stop**: SIGINT/SIGTERM shut both serve models down cleanly, draining sessions instead of being killed mid-write. Door saves, the shared world and chat transcripts are now crash-safe (temp + `fsync` + `rename`), the two poll-mode holes are closed, and the IAC parser has a fuzz harness that runs in CI and at release. Toolchain cyrius 6.5.34.

Built on **v1.0.0** (2026-05-23, iron-validated on archaemenid): a multi-user, multi-board threaded BBS with sigil-backed Ed25519 challenge/response auth, per-board posting policy, and full RFC 854 / 1143 / 1073 / 1091 / 1184 conformance — since extended with door games, a persistent shared universe, a live chat area with four chatbots, a casino, a war-game, a code-breaking door, a gateway into the sibling Yeoman's Descent MUD, an AGNOS target, and a single-process poll multiplex.

**This paragraph deliberately does not narrate the release history** — it used to, and rotted fourteen releases deep. Per-tag detail is in [`CHANGELOG.md`](CHANGELOG.md); the live snapshot (version, binary size, test count, in-flight work) is [`docs/development/state.md`](docs/development/state.md); doc currency is [`docs/doc-health.md`](docs/doc-health.md); what is next is [`docs/development/roadmap.md`](docs/development/roadmap.md).

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

End-to-end walkthrough in [`docs/guides/getting-started.md`](docs/guides/getting-started.md); runnable examples in [`docs/examples/`](docs/examples/) (01–28). Cyrius toolchain pinned in `cyrius.cyml` (`[package].cyrius`).

## Architecture

```
agora binary (~874 KB static ELF at 1.3.7)
├── src/main.cyr            argv dispatch + telnet handle_client + session helpers
│                           + login flow + CLI keygen/register/whoami
│                           + dual serve model (ADR 0023): fork-per-accept
│                             (ADR 0007) and poll multiplex, AGORA_SERVE
│                           + clean shutdown via signalfd (SIGINT/SIGTERM)
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
├── src/arena.cyr           per-command scratch arena + crash-safe store write
├── src/test.cyr            conformance suite (count in docs/development/state.md)
└── fuzz/telnet_iac.fcyr    IAC-parser fuzz harness (CI + release)
```

Stdlib consumed: net + io + fs + str + vec + alloc + bannermanor (MOTD) + darshana (SGR) + sigil + freelist + bayan + ct (the ed25519 call chain; `bigint` was folded into `bayan` at cyrius 6.2.2). No external deps beyond cyrius.

## Docs

- [`docs/development/roadmap.md`](docs/development/roadmap.md) — milestones, sub-bites, v1.0 criteria.
- [`docs/development/state.md`](docs/development/state.md) — current version, binary size, in-flight slot. Refreshed every release.
- [`docs/doc-health.md`](docs/doc-health.md) — fresh / stale / archive ledger across the whole doc tree.
- [`docs/adr/`](docs/adr/) — architecture decision records (why we chose X over Y).
- [`docs/architecture/`](docs/architecture/) — non-obvious invariants the code relies on.
- [`docs/guides/`](docs/guides/) — task-oriented how-tos (`getting-started.md` first).
- [`docs/examples/`](docs/examples/) — twenty-eight runnable smoke scripts covering build / auth / concurrency / policy / door games / Universe / leaderboards / chat (`11-chat.sh`) / Eliza (`12-eliza.sh`) / PARRY (`13-parry.sh`) / QUEST (`14-quest.sh`) / Jabberwacky (`15-jabberwacky.sh`) / casino (`16-casino.sh`) / Olympiad (`17-olympiad.sh`) / Ashes of Empire (`18-ashes.sh`, `19-ashes-concurrency.sh`) / the Descent MUD gateway (`20-descent.sh`, `24-descent-serve-models.sh`) / decode (`21-decode.sh`) / the Handler decrypt lever (`22-handler-decrypt.sh`) / SIGPIPE survival (`23-sigpipe-survival.py`) / door-state churn (`25-door-state-churn.py`) / IAC + idle (`26-iac-and-idle.py`) / audit LOWs (`27-audit-lows.py`) / clean shutdown (`28-clean-shutdown.py`).
- [`BENCHMARKS.md`](BENCHMARKS.md) — telnet-parser baseline (~9 ns/byte hot path, unchanged across every release since M1-close).
- [`fuzz/`](fuzz/) — the IAC-parser fuzz harness (`cyrius fuzz`), run by CI and at release.
- [`CHANGELOG.md`](CHANGELOG.md) — per-tag chronology.
- [`CLAUDE.md`](CLAUDE.md) — durable rules for agent sessions.

Full doc-tree convention: [first-party-documentation.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md).

## Companion project

**MUD userland** — separate repo, shares the telnet listener primitive but adds real-time room/object model. Same wire-protocol substrate, different application semantics. Both surface the AGNOS 1.32.x networking arc to real users.

## License

GPL-3.0-only.
