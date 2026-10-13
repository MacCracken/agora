# Contributing

Thanks for the interest. agora is a small, focused codebase — the contribution surface is straightforward.

## Before you start

1. Read [`CLAUDE.md`](CLAUDE.md) — the project's durable rules, conventions, and process.
2. Read [`docs/development/roadmap.md`](docs/development/roadmap.md) — what's in flight, what's next, what's deferred.
3. Skim [`docs/adr/`](docs/adr/) — decisions already made.

## Workflow

1. Fork the repo, create a branch named after the change (`m1-iac-parser`, `fix-banner-color`, etc.).
2. Build clean: `cyrius build src/main.cyr build/agora`.
3. Add tests for any new code path: module code in `tests/agora.tcyr`, serve-layer code (`src/main.cyr`: the serve loops, the session pool, the send path, door glue) in `tests/serve.tcyr`, and wire-visible behaviour as a `docs/examples/` smoke.
4. Run `cyrius test` — every `tests/*.tcyr` passes — and `docs/examples/run.sh` for the smokes.
5. Run `cyrius fuzz fuzz/telnet_iac.fcyr` if you touched `src/telnet.cyr` — it is a CI and release gate.
5. Update [`CHANGELOG.md`](CHANGELOG.md) under `[Unreleased]`.
6. If the change rewrites a doc, refresh the affected row in [`docs/doc-health.md`](docs/doc-health.md).
7. If the change is a decision worth re-arguing later, add an ADR under [`docs/adr/`](docs/adr/) (use [`docs/adr/template.md`](docs/adr/template.md)).
8. Open a PR — small, single-purpose, with a clear title and a body that explains *why*.

## Style

- Cyrius conventions per [`CLAUDE.md` § Cyrius Conventions](CLAUDE.md#cyrius-conventions).
- One change per PR. Bundling refactors with feature work makes review harder and bisect impossible.
- Default to no comments. Only add one when the *why* is non-obvious — a hidden constraint, a subtle invariant, a workaround for a specific bug.

## Reporting bugs

File an issue with:

- Cyrius version (`cyrius version`).
- agora `VERSION` and commit hash.
- Minimal reproducer — ideally a script or a telnet session transcript.
- Expected vs. actual behavior.

Security issues: see [`SECURITY.md`](SECURITY.md) — do not file publicly.

## License

By contributing, you agree your changes ship under [GPL-3.0-only](LICENSE).
