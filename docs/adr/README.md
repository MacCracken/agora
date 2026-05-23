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
