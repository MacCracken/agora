# Architecture Notes

Non-obvious invariants and constraints the code relies on — *how the world is*, not *what we chose*. ADRs (in `../adr/`) capture decisions; this directory captures realities a reader cannot derive from the code alone.

## Conventions

- **Filename**: `NNN-kebab-case-title.md`, zero-padded to three digits. **Never renumber.**
- Numbered chronologically in order of discovery.
- Not a decision (that's an ADR), not a how-to (that's a guide). An architecture note documents reality.

Per [first-party-documentation § Architecture Notes](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#architecture-notes).

## Index

| # | Title | Affects |
|---|---|---|

*(empty — first note lands at M1 when the IAC parser surfaces an invariant worth capturing, e.g. partial-IAC sequences buffered across `recv()` calls)*
