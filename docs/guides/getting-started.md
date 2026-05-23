# Getting Started

> **Last Updated**: 2026-05-23

Build, smoke-test, and run agora in under a minute on Linux x86_64 or aarch64.

## Prerequisites

- Cyrius toolchain ≥ 6.0.1 — installed via:

  ```sh
  curl -sSf https://raw.githubusercontent.com/MacCracken/cyrius/main/scripts/install.sh | sh
  ```

  Confirm: `cyrius version` reports `6.0.1` or newer.

- Linux x86_64 or aarch64. macOS and Windows follow as cyrius `lib/net.cyr` gains backends — see [ADR 0001](../adr/0001-cross-platform-listener-decoupled-from-agnos.md).

## Build

```sh
cd agora
cyrius build src/main.cyr build/agora
```

At v0.1.0 this produces a ~43 KB static ELF. Live size in [`docs/development/state.md`](../development/state.md).

For a release-shaped (dead-code-eliminated) build:

```sh
CYRIUS_DCE=1 cyrius build src/main.cyr build/agora
```

## Smoke test

```sh
./build/agora help
./build/agora version
```

Both should print and exit 0. At v0.1.0 the other verbs (`serve`, `post`, `list`, `read`, `whoami`) print M-tagged stub messages and exit 1 — they earn real implementations at M1+.

## Run the listener (M1+)

> v0.1.0 stub — telnet listener not yet implemented. Section will fill in when M1 lands.

```sh
./build/agora serve              # listen on default port 23
./build/agora serve --port 2323  # unprivileged port (no root needed)
```

In another shell:

```sh
telnet localhost 2323
```

You should see the agora MOTD banner and a prompt. Exit telnet with `Ctrl+]` then `quit`.

## Tests

```sh
cyrius test src/test.cyr
```

v0.1.0: `src/test.cyr` not yet present — first lands at M1 with RFC 854 IAC parser conformance.

## Where to go next

- [`docs/development/roadmap.md`](../development/roadmap.md) — what's done, next, and future.
- [`docs/adr/`](../adr/) — why the project is shaped the way it is.
- [`CLAUDE.md`](../../CLAUDE.md) — agent / contributor process notes.
- [`CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.
