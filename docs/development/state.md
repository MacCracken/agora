---
name: agora State
description: Live state snapshot for the agora repo — volatile data refreshed every release
type: state
---

# agora — State Snapshot

> **Last refresh**: 2026-05-23 (v0.1.0 scaffold ship) | **Refresh cadence**: every release; ideally bumped by the release post-hook.

Per [first-party-documentation § CLAUDE.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#claudemd), CLAUDE.md holds **durable rules**; this file holds **volatile state**. If a claim drifts within a minor's worth of work, it belongs here, not in CLAUDE.md.

---

## Version

| Field | Value |
|---|---|
| **Released** | `0.1.0` (2026-05-23) |
| **Cycle** | M0 closed; **M1 in progress** (cross-platform telnet listener) |
| **Toolchain pin** | cyrius `6.0.1` (in `cyrius.cyml [package].cyrius`) |
| **Source of truth** | `VERSION` file at repo root |

## Build artifacts

| Artifact | Size | Build line |
|---|---|---|
| `build/agora` (x86_64, no DCE) | 56,064 B at M1 first-bite (was 43,216 B at v0.1.0 scaffold) | `cyrius build src/main.cyr build/agora` |
| `build/agora` (DCE) | TBD — first DCE build at M1 close | `CYRIUS_DCE=1 cyrius build src/main.cyr build/agora` |

Compile output reports `190 unreachable fns (22,412 B)` — agora consumes a thin slice of the now-expanded stdlib (added `net` + `result` + `tagged` for M1); DCE will roughly cut the binary by 22 KB at the M1 close.

## Tests + benchmarks

| Surface | Status |
|---|---|
| `src/test.cyr` | **10 tests passing** at M1 first-bite — RFC 854 IAC sequences (plain data, IAC IAC literal, WILL/DO refusal, NOP, subneg collect, escaped IAC in SB, malformed-SB recovery, tx drain) |
| Bench harness | not yet present — earns at M1 close (parser throughput + accept-loop rate) |
| `cyrius audit` | clean (build + lint pass; tests green; bench surface empty pre-M1-close) |

## In-flight slot

**M1 — Telnet listener (RFC 854 + LINEMODE 1184)**, cross-platform via `lib/net.cyr`.

**First-bite landed 2026-05-23**: IAC parser (`src/telnet.cyr`) + naive-refuse option negotiation + listener loop in `cmd_serve` + 10-test conformance suite. End-to-end smoke green — python TCP client receives banner, server refuses options in RFC-conformant order, plain data bytes echo. Binary 56,064 B.

**Remaining bites for M1 close** (per [`roadmap.md`](roadmap.md#m1--telnet-listener-rfc-854--rfc-1184-linemode)):

- Real option negotiation per RFC 1143 (Q method) — agree to `WILL SUPPRESS_GO_AHEAD`, `WILL ECHO`, request `DO TERMINAL_TYPE` + `DO NAWS`.
- RFC 1184 LINEMODE state machine — MODE subnegotiation (EDIT / TRAPSIG / SOFT_TAB / LIT_ECHO), SLC table.
- Connection lifecycle — graceful close on EOF, slowloris defense via `sock_set_recv_timeout`.
- Bench harness — parser throughput + accept-loop rate.

## Recent shipped

- **0.1.0** (2026-05-23) — Scaffold ship. argv dispatch + boot banner + 6 stub verbs. 43,216 B binary. See [`CHANGELOG.md`](../../CHANGELOG.md#010--2026-05-23-scaffold).

## Consumers

None yet. agora is a binary (telnet server), not a library. Future consumers will arrive at M5+ when external tools start scripting against the post storage layer.

## Verification hosts

| Host | Role | Status |
|---|---|---|
| Workstation (Linux x86_64) | primary dev + smoke | ✅ active |
| archaemenid (iron NUC, AGNOS) | 1.0 release-gate validation | pending M5 + agnos 1.33.x ext4 WRITE |
| Raspberry Pi 4 (Linux aarch64) | cross-arch CI | pending M1 close |

## Gate state for downstream milestones

| Dep | Required for | Live version | Gate met? |
|---|---|---|---|
| cyrius | self | 6.0.1 (pinned) | ✅ |
| `lib/net.cyr` (cyrius stdlib) | M1 socket loop | x86_64 + aarch64 Linux | ✅ Linux; macOS / Windows backends pending in cyrius |
| **bannermanor** | M2 ASCII banners | 1.0.0 | ✅ |
| **darshana** | M2 ANSI escapes | 0.5.3 | ❌ needs ≥ 1.0.0 |
| **kii** | M3 inline-image posts | 1.0.0 | ✅ |
| **sankoch** | M4 stored-file deltas | 2.2.6 | ✅ |
| **sigil** | M6 user accounts | 3.4.2 | ✅ |
| **agnos** ext4 WRITE | AGNOS-target M5 (Linux M5 lands sooner) | agnos 1.32.2 in-flight | ❌ pending agnos 1.33.x |

## Bootstrap chain / source surface

- `src/main.cyr` — argv dispatch (~100 LOC)
- `src/telnet.cyr` (M1, not yet present) — RFC 854 IAC parser + RFC 1184 LINEMODE state machine
- `src/test.cyr` (M1, not yet present) — parser conformance against RFC sequences
- `lib/` — resolved deps (7 stdlib modules: string, fmt, alloc, io, syscalls, assert, args); M1 adds `net`

## Cross-references

- [`roadmap.md`](roadmap.md) — milestones + sub-bites + v1.0 criteria (durable).
- [`../doc-health.md`](../doc-health.md) — doc currency across the tree.
- [`../../CLAUDE.md`](../../CLAUDE.md) — durable rules.
- [`../../CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.
