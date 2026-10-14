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
| 0002 | [One file per post for the M5 storage layout](0002-one-file-per-post-storage.md) | Accepted (2026-05-23); crash consistency amended by 0025 (1.9.0) |
| 0003 | [RFC-822-shaped post headers (Subject + Date)](0003-rfc-822-post-headers.md) | Accepted (2026-05-23) |
| 0004 | [Board layout: flat-root = main, subdirs = named](0004-board-layout.md) | Accepted (2026-05-23) |
| 0005 | [Threading via Reply-To header](0005-threading-via-reply-to.md) | Accepted (2026-05-23); reply enumeration superseded by 0027 (1.9.1) |
| 0006 | [Identity model: sigil Ed25519, `.users/<fp>`, challenge/response login](0006-identity-model.md) | Accepted (2026-05-23); storage + login lookup amended by 0026 (1.9.0), posting policy by 0028 (1.9.2) |
| 0007 | [Concurrent connections via fork-per-accept](0007-fork-per-accept-concurrency.md) | Accepted (2026-05-23) |
| 0008 | [Post header parameters as a struct (pre-1.0 ABI shape)](0008-post-headers-struct.md) | Accepted (2026-05-23) |
| 0009 | [Door / games subsystem architecture](0009-door-games-subsystem.md) | Accepted (2026-06-07) |
| 0010 | [Persistent Universe (shared-world multiplayer for door games)](0010-persistent-universe.md) | Accepted (2026-06-08) — 1.2.0 |
| 0011 | [Chat area (live multi-user teleconference)](0011-chat-area.md) | Accepted (2026-06-08) — 1.3.0 |
| 0012 | [Chatbot framework (Eliza, PARRY, and the fixed-script family)](0012-chatbot-framework.md) | Accepted (2026-06-08) — 1.3.0/1.3.1 |
| 0013 | [Shared wager module + the wager-RNG fairness decision](0013-wagering-module-rng-fairness.md) | Accepted (2026-06-08) — 1.3.4 |
| 0014 | [War-game door: async shared-world strategy as the MUD on-ramp](0014-async-shared-world-strategy.md) | Accepted (2026-06-09) — 1.3.7 |
| 0015 | [Jabberwacky: the corpus-learning chatbot engine](0015-jabberwacky-corpus-learning.md) | Accepted (2026-06-08) — 1.3.3 |
| 0016 | [The Olympiad: a competition primitive on a games-owner frame](0016-olympiad-competition-primitive.md) | Accepted (2026-06-09) — 1.3.6 |
| 0017 | [Descent link: a transparent-proxy gateway to the MUD](0017-descent-link-gateway.md) | Accepted (2026-06-10) — 1.4.0 |
| 0018 | [Decode: the classify primitive and one engine for two variants](0018-decode-engine.md) | Accepted (2026-06-14) — 1.4.1/1.4.2 |
| 0019 | [Decode as a Handler gameplay lever (cross-game mechanic reuse)](0019-decode-handler-lever.md) | Accepted (2026-06-14) — 1.4.3 |
| 0020 | [Door descriptor registry (table-driven door dispatch)](0020-door-descriptor-registry.md) | Accepted (2026-06-15) — 1.4.6 |
| 0021 | [The per-command scratch arena](0021-per-command-scratch-arena.md) | Accepted (2026-07-25) — 1.6.2 |
| 0022 | [The door-state free hook (`DD_FREE`)](0022-door-state-free-hook.md) | Accepted (2026-07-26) — 1.6.3 |
| 0023 | [The dual serve model: fork per accept, or one process polling all sessions](0023-dual-serve-model.md) | Accepted (2026-07-26) — records 1.5.0/1.6.0; amends 0007 |
| 0024 | [Stored text is sanitized at egress, in UTF-8 mode](0024-egress-text-sanitization.md) | Accepted (2026-10-12) — 1.8.0 |
| 0025 | [Store I/O: regular files only, and an exclusive crash-safe publish](0025-store-io-regular-files-and-publish.md) | Accepted (2026-10-13) — 1.9.0; amends 0002 |
| 0026 | [The handle index: one claim file per handle](0026-handle-index.md) | Accepted (2026-10-13) — 1.9.0; amends 0006 |
| 0027 | [The reply index: one verified record file per parent](0027-reply-index.md) | Accepted (2026-10-13) — 1.9.1; amends 0005 |
| 0028 | [Board policy modes that mean something: members-only, anonymous posting, admins by key](0028-board-policy-modes.md) | Accepted (2026-10-13) — 1.9.2; amends 0006 |
| 0029 | [Telnet conformance: agora as the LINEMODE server, and the line editor](0029-telnet-conformance.md) | Accepted (2026-10-13) — 1.10.0 |
| 0030 | [Terminal-aware output: wrap to the window the client reports](0030-terminal-aware-output.md) | Accepted (2026-10-13) — 1.10.1 |
| 0031 | [Descent as a session state, readiness-driven serve loops, and option resync on return](0031-descent-session-state.md) | Accepted (2026-10-13) — 1.11.0; amends 0007, 0017, 0023 |
