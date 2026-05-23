# agora

> Telnet-served BBS for AGNOS. Posts, messages, file-share. Cyrius-native.

**Status**: v0.1.0 scaffold — argv dispatch + stub verbs. Waiting on agnos 1.32.2 to close the DHCP gate + iron-validate `tcp_listen` end-to-end; real protocol code lands at M1.

## Etymology

Three layers:

1. Ancient Greek **ἀγορά** *(agorá)* — the civic marketplace and public-assembly ground of the Greek city-state. Where citizens gathered to discuss news, debate, share knowledge, conduct exchange. Exact functional match for a BBS: an asynchronous public surface for posting, reading, and discussion.

2. Doja Cat **"Agora Hills"** — track 4 on *Scarlet* (2023). Drops the 'u' from the city name to land the Greek-civic-marketplace reference directly.

3. **Agoura Hills, CA** — the city literally around the corner from the project's home base in Thousand Oaks. Named after the Basque shepherd Pierre Agoure (1872 land tract), whose surname phonetically echoes the Greek root. Doja Cat's track and the city share the pronunciation; the project takes the Greek spelling to thread all three references at once.

The naming convention adds a **Greek lane** to the AGNOS ecosystem (previously Sanskrit/Hindi for system libs + English-wordplay or Polynesian for user-facing tools — see [[feedback_naming_lanes]]). The lane opens with a multi-layer convergence — like `kii` in the existing Polynesian/East-Asian/English-phonetic micro-cluster, agora threads ancient civic-marketplace + 2023 hip-hop reference + literal hyperlocal Conejo Valley geography. Three independent angles all describe the same gathering-place semantics.

## Roadmap

| Milestone | Scope | Gates |
|---|---|---|
| **M0 (0.1.0)** ← THIS | argv dispatch + boot banner + stub verbs | none (scaffold-only) |
| M1 | Telnet listener (RFC 854) + LINEMODE (RFC 1184) | agnos 1.32.2 closes (`tcp_listen(23)` on iron) |
| M2 | ANSI BBS aesthetic (color, cursor positioning, banners) | darshana stable + bannermanor stable |
| M3 | Inline-image post bodies (ASCII-art conversion) | kii 1.0.0 (✅ available 2026-05-23) |
| M4 | Stored-file deltas + compression | sankoch stable |
| M5 | Post persistence (boards / threads / messages) | **agnos 1.33.x ext4 WRITE** (Phase 1-5 read-only currently lands as of agnos 1.31.5) |
| M6 | User accounts + auth | sigil-backed identity primitives |
| **1.0.0** | All six milestones green, multi-user telnet BBS on iron | M0-M6 + iron validation on archaemenid LAN |

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
├── src/board.cyr (M5)      post / thread storage (ext4-backed)
├── src/ansi.cyr (M2)       darshana consumer (BBS color/cursor)
├── src/banner.cyr (M2)     bannermanor consumer (ASCII MOTD)
├── src/image.cyr (M3)      kii consumer (inline image posts)
├── src/auth.cyr (M6)       sigil-backed user accounts
└── src/test.cyr            test harness
```

## Companion project

**MUD userland** — separate repo, shares the telnet listener primitive but adds real-time room/object model. Same wire-protocol substrate, different application semantics. Both surface the AGNOS 1.32.x networking arc to real users.

## License

GPL-3.0-only.
