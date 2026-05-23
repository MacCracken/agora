---
name: agora State
description: Live state snapshot for the agora repo — volatile data refreshed every release
type: state
---

# agora — State Snapshot

> **Last refresh**: 2026-05-23 (post-0.5.0 ship; M5 closed; doc-tree cleanup pre-handoff) | **Refresh cadence**: every release; ideally bumped by the release post-hook.

Per [first-party-documentation § CLAUDE.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#claudemd), CLAUDE.md holds **durable rules**; this file holds **volatile state**. If a claim drifts within a minor's worth of work, it belongs here, not in CLAUDE.md.

---

## Next-session boot guide

**What to know after a fresh agent boot:**

1. **Where we are**: agora is a working **multi-board threaded BBS over telnet** at v0.5.0. M5 cycle closed. The clean slate is ready for **M6** (sigil-backed auth).
2. **Where to read first**: this file (state.md), then [`roadmap.md`](roadmap.md) for the release plan, then [`CLAUDE.md`](../../CLAUDE.md) for project rules. Decisions live in [`../adr/`](../adr/) — five ADRs as of 0.5.0.
3. **What's next**: M6 → 0.6.0 (sigil-backed identity, login flow, `whoami`, per-board posting permissions). First bite is likely **ADR 0006 — identity model**: where account metadata lives, how the wire-side login works, how `Subject:` headers grow a `From: <handle>` field. See the "In-flight slot" section below for the sketch.
4. **What to build / test**: `cyrius build src/main.cyr build/agora` (clean), `cyrius test src/test.cyr` (49/49 pass), `cyrius bench benches/bench_telnet.bcyr` (5 baselines), `./build/agora serve 2323` (telnet to localhost:2323).
5. **What NOT to do**: don't commit / push — user owns git. Don't use `gh` CLI. Don't add unprompted version bumps (per durable CLAUDE.md rules).

---

## Version

| Field | Value |
|---|---|
| **Released** | `0.5.0` (2026-05-23) |
| **Cycle** | M0 / M1 / M2 / M5 all closed. **M6 (auth) is the next cycle → 0.6.0.** Release plan after that: 0.7 security sweep + CVE research, 0.8 v1 hardening + ABI freeze, 1.0 ship on archaemenid iron. |
| **Toolchain pin** | cyrius `6.0.1` (in `cyrius.cyml [package].cyrius`) |
| **Source of truth** | `VERSION` file at repo root |

## Build artifacts

| Artifact | Size | Build line |
|---|---|---|
| `build/agora` (x86_64, no DCE) | **140,160 B** at 0.5.0 | `cyrius build src/main.cyr build/agora` |
| `build/agora` (DCE) | same size — DCE NOPs unreachable fns in place rather than stripping (313 fns / ~49 KB NOPed at 0.5.0). Real binary strip is a v1.x close-out concern. | `CYRIUS_DCE=1 cyrius build src/main.cyr build/agora` |
| `build/test` | 49 tests | `cyrius build src/test.cyr build/test && ./build/test` |

Binary growth across cycles: 43 KB scaffold (0.1.0) → 71 KB M1 close (0.2.0) → 86 KB M2 close (0.3.0) → 129 KB M5 partial (0.4.0) → 140 KB M5 close (0.5.0).

## Tests + benchmarks

| Surface | Status |
|---|---|
| `src/test.cyr` | **49 tests passing** at 0.5.0. Coverage: RFC 854/1143/1073/1091/1184 IAC + Q-method + subneg conformance (M1), board-storage primitives (M5-A), sort (M5-C), ingress filter (M5-H), RFC-822 headers + body-offset (M5-D), board-name validator + path resolution (M5-E), Re: subject + Reply-To round-trip (M5-F). Full wire integration verified via Python TCP-client smoke (not in test.cyr). |
| `benches/bench_telnet.bcyr` | **5 benchmarks** — see [`/BENCHMARKS.md`](../../BENCHMARKS.md). Hot path 10 ns/byte (plain) → ~130 ns (4-option announce salvo). |
| `cyrius audit` | clean from a fresh build at 0.5.0 (lint + build + tests green; bench baseline reproducible). |

## In-flight slot

**M6 — user accounts + auth → 0.6.0**

**sigil** 3.4.2 is the identity primitive (gate met). Scope: login flow over telnet, `whoami`, per-board posting permissions. Out of scope: federated identity, web-of-trust — those are v2.x pillar 1 (see [`roadmap-future.md`](roadmap-future.md)).

**Likely first bite — [ADR 0006](../adr/) (TBD): identity model.** Open questions:

- **Storage**: where do per-user metadata files live? `<store>/.users/<fingerprint>` matches the existing per-board layout; alternative is fully sigil-managed. Pick before code.
- **Wire login**: `login` command → server challenge → client sigil-signs → server verifies fingerprint → session bound. Idle-session anonymous reads stay supported (operator config — `auth: required | optional`).
- **Subject grows `From:`**: posts now carry author identity. RFC-822 `From: <handle>` header at the existing block; backwards-compat with M5-A/B/C/D/E/F posts (no From → anonymous).
- **Per-board posting**: open / known-only / admin-only as operator config; not per-user-pair-board (that's M6+ polish).
- **CLI**: `agora whoami` (decode sigil fingerprint), `agora post --as <handle>` (op testing). Sigil-key location TBD — `~/.agora/key` or sigil-default.

Reference reading before the bite: existing ADRs 0001-0005 establish the project's decision-record voice (each lists alternatives + their rejection reasoning); sigil 3.4.2 README + API surface for the challenge primitives.

---

## Recent shipped

- **0.5.0** (2026-05-23) — M5 close: boards + threads. 2 new bites (M5-E boards, M5-F threading) + 2 new ADRs (0004 board layout, 0005 Reply-To threading). 49 tests; 140,160 B. **agora is a multi-board threaded BBS.**
- **0.4.0** (2026-05-23) — M5 partial: post persistence. 6-bite cycle + 2 ADRs (0002 one-file-per-post, 0003 RFC-822 headers). 38 tests; 129 KB. **agora is a single-board BBS over telnet.**
- **0.3.0** (2026-05-23) — M2 close: ANSI BBS aesthetic. bannermanor MOTD + darshana SGR + `--motd`. Bannermanor patched 1.0.1 the same day for ecosystem alignment.
- **0.2.0** (2026-05-23) — M1 close: cross-platform telnet listener. RFCs 854 / 1143 / 1073 / 1091 / 1184. First parser baseline (10 ns/byte).
- **0.1.0** (2026-05-23) — Scaffold ship.

Per-bite narrative for each release lives in [`CHANGELOG.md`](../../CHANGELOG.md).

## Consumers

None yet. agora is a binary (telnet server), not a library. Future consumers may arrive at M5+ once tools script against the post storage layer; the v2.x pillar 5 (self-distribution) would make agora a distribution channel for the rest of AGNOS, at which point downstream verification becomes load-bearing.

## Verification hosts

| Host | Role | Status |
|---|---|---|
| Workstation (Linux x86_64) | primary dev + smoke | ✅ active |
| archaemenid (iron NUC, AGNOS) | 1.0 release-gate validation | pending v1.0 cut |
| Raspberry Pi 4 (Linux aarch64) | cross-arch CI | pending CI runner config |

## Gate state for downstream milestones

| Dep | Required for | Live version | Gate met? |
|---|---|---|---|
| cyrius | self | 6.0.1 (pinned) | ✅ |
| `lib/net.cyr` (cyrius stdlib) | M1 socket loop | x86_64 + aarch64 Linux | ✅ Linux; macOS / Windows backends pending in cyrius |
| **bannermanor** | M2 ASCII banners | 1.0.1 | ✅ consumed at M2-A |
| **darshana** | M2 ANSI escapes | 0.5.3 (pinned git dep) | ✅ consumed at M2-B |
| **sigil** | **M6 user accounts** | **3.4.2** | **✅ — next-cycle dep** |
| **kii** | M3 inline-image posts | 1.0.0 | ✅ (deferred — no current consumer) |
| **sankoch** | M4 stored-file deltas | 2.2.6 | ✅ (deferred) |
| **agnos** ext4 WRITE | AGNOS-target storage (Linux works today) | agnos 1.32.2 in-flight | ❌ — not blocking, AGNOS is one target among many per ADR 0001 |

## Source surface

- `src/main.cyr` — argv dispatch + verb handlers + telnet `handle_client` + session helpers (~1.1k LOC at 0.5.0)
- `src/telnet.cyr` — RFC 854 IAC parser + RFC 1143 Q-method + RFC 1184 LINEMODE state machine
- `src/board.cyr` — post storage + headers + threading + flock + board layout (ADRs 0002/0003/0004/0005)
- `src/test.cyr` — 49-test conformance suite
- `benches/bench_telnet.bcyr` — 5-bench parser harness
- `lib/` — 16 stdlib modules + lib/darshana.cyr (pinned 0.5.3 git dep)

## Cross-references

- [`roadmap.md`](roadmap.md) — release plan, in-progress cycle, backlog.
- [`../doc-health.md`](../doc-health.md) — doc currency across the tree.
- [`../../CLAUDE.md`](../../CLAUDE.md) — durable rules / process / conventions.
- [`../../CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.
- [`roadmap-future.md`](roadmap-future.md) — v2.x sovereignty pillars (post-1.0, unpinned).
