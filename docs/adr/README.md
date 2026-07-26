# Architecture Decision Records

Index of ADRs for the agora repo. ADRs capture *why we chose X over Y* — the decision rationale that doesn't belong in a commit message.

## Conventions

- **Filename**: `NNNN-kebab-case-title.md`, zero-padded to four digits. **Never renumber.**
- **One decision per ADR.** Supersessions add a new ADR and mark the old one `Superseded by NNNN`.
- **Status lifecycle**: `Proposed` → `Accepted` → (optionally) `Superseded` or `Deprecated`.
- Use [`template.md`](template.md) as the starting point.

Per [first-party-documentation § ADRs](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#architecture-decision-records-adrs).

## Index

| # | Title | Status |
|---|---|---|
| 0001 | [Cross-platform listener decoupled from AGNOS](0001-cross-platform-listener-decoupled-from-agnos.md) | Accepted (2026-05-23) |
| 0002 | [One file per post for the M5 storage layout](0002-one-file-per-post-storage.md) | Accepted (2026-05-23) |
| 0003 | [RFC-822-shaped post headers (Subject + Date)](0003-rfc-822-post-headers.md) | Accepted (2026-05-23) |
| 0004 | [Board layout: flat-root = main, subdirs = named](0004-board-layout.md) | Accepted (2026-05-23) |
| 0005 | [Threading via Reply-To header](0005-threading-via-reply-to.md) | Accepted (2026-05-23) |
| 0006 | [Identity model: sigil Ed25519, `.users/<fp>`, challenge/response login](0006-identity-model.md) | Accepted (2026-05-23) |
| 0007 | [Concurrent connections via fork-per-accept](0007-fork-per-accept-concurrency.md) | Accepted (2026-05-23) |
| 0008 | [Post header parameters as a struct (pre-1.0 ABI shape)](0008-post-headers-struct.md) | Accepted (2026-05-23) |
| 0009 | [Door / games subsystem architecture](0009-door-games-subsystem.md) | Accepted (2026-06-07) |
| 0010 | [Persistent Universe (shared-world multiplayer for door games)](0010-persistent-universe.md) | Accepted (2026-06-08) — 1.2.0 |
| 0011 | [Chat area (live multi-user teleconference)](0011-chat-area.md) | Accepted (2026-06-08) — 1.3.0 |
| 0012 | [Chatbot framework (Eliza, PARRY, and the fixed-script family)](0012-chatbot-framework.md) | Accepted (2026-06-08) — 1.3.0/1.3.1 |
| 0013 | [Shared wager module + the wager-RNG fairness decision](0013-wagering-module-rng-fairness.md) | Proposed (2026-06-08) — 1.3.4 |
| 0014 | [War-game door: async shared-world strategy as the MUD on-ramp](0014-async-shared-world-strategy.md) | Proposed (2026-06-08) — 1.3.7 |
| 0015 | [Jabberwacky: the corpus-learning chatbot engine](0015-jabberwacky-corpus-learning.md) | Accepted (2026-06-08) — 1.3.3 |
| 0016 | [The Olympiad: a competition primitive on a games-owner frame](0016-olympiad-competition-primitive.md) | Accepted (2026-06-09) — 1.3.6 |
| 0017 | [Descent link: a transparent-proxy gateway to the MUD](0017-descent-link-gateway.md) | Accepted (2026-06-10) — 1.4.0 |
| 0018 | [Decode: the classify primitive and one engine for two variants](0018-decode-engine.md) | Accepted (2026-06-14) — 1.4.1/1.4.2 |
| 0019 | [Decode as a Handler gameplay lever (cross-game mechanic reuse)](0019-decode-handler-lever.md) | Accepted (2026-06-14) — 1.4.3 |
| 0020 | [Door descriptor registry (table-driven door dispatch)](0020-door-descriptor-registry.md) | Accepted (2026-06-15) — 1.4.6 |
| 0021 | [The per-command scratch arena](0021-per-command-scratch-arena.md) | Accepted (2026-07-25) — 1.6.2 |
| 0022 | [The door-state free hook (`DD_FREE`)](0022-door-state-free-hook.md) | Accepted (2026-07-26) — 1.6.3 |
