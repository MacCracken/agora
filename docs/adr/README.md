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
