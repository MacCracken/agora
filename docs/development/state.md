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
| **Released** | `0.2.0` (2026-05-23) |
| **Cycle** | M0 + **M1 closed at 0.2.0** (2026-05-23) — cross-platform telnet listener wire-conformant; M2 (ANSI BBS aesthetic) next, gated on darshana ≥ 1.0 |
| **Toolchain pin** | cyrius `6.0.1` (in `cyrius.cyml [package].cyrius`) |
| **Source of truth** | `VERSION` file at repo root |

## Build artifacts

| Artifact | Size | Build line |
|---|---|---|
| `build/agora` (x86_64, no DCE) | 70,960 B at M1 close (62,176 fourth-bite; 61,152 third; 59,280 second; 56,064 first; 43,216 v0.1.0 scaffold) | `cyrius build src/main.cyr build/agora` |
| `build/agora` (DCE) | TBD — first DCE build at M1 close | `CYRIUS_DCE=1 cyrius build src/main.cyr build/agora` |

Compile output reports `220 unreachable fns (26,707 B NOPed)` — the M1-close addition of `vec` + `fnptr` + `bench` (for the bench harness) grew the surface; DCE NOPs the bench-only paths but doesn't strip them from the file. Release-binary optimization (strip + DCE-aware emit) is a v1.x close-out concern.

## Tests + benchmarks

| Surface | Status |
|---|---|
| `src/test.cyr` | **24 tests passing** at M1 close — RFC 854 IAC + RFC 1143 Q-method + RFC 1073 NAWS + RFC 1091 TERMINAL_TYPE + RFC 1184 LINEMODE (parser conformance, announce salvo, Q transitions, NAWS/TT subneg capture, LINEMODE DO+MODE-request burst, MODE ACK mask parse, SLC parsed-ignored, malformed-MODE drop) |
| `benches/bench_telnet.bcyr` | **5 benchmarks** — see [`/BENCHMARKS.md`](../../BENCHMARKS.md). Hot path 10 ns/byte (plain) → 132 ns (4-option announce salvo). |
| `cyrius audit` | clean (build + lint pass; tests green; first bench baseline captured at M1 close) |

## Recently closed

**M1 closed 2026-05-23** — five bites, all wire-conformant:

1. **First-bite**: IAC parser + naive-refuse negotiation + listener loop (10 tests; 56,064 B)
2. **Second-bite**: RFC 1143 Q-method (Q_NO/WANTYES/YES per option per side) + announce salvo + slowloris timeout + graceful close (15 tests; 59,280 B, +3,216 B)
3. **Third-bite**: RFC 1073 NAWS + RFC 1091 TERMINAL_TYPE subneg parsing + TT SEND auto-emit on him-Q_YES (20 tests; 61,152 B, +1,872 B)
4. **Fourth-bite**: RFC 1184 LINEMODE tracked-him + DO+MODE-request burst + MODE ACK mask capture + SLC parsed-ignored (24 tests; 62,176 B, +1,024 B)
5. **Close-bite**: 5-bench parser harness ([`/BENCHMARKS.md`](../../BENCHMARKS.md)) — 10 ns/plain-byte, 73 ns tracked-IAC, 97 ns NAWS subneg, 132 ns announce salvo (24 tests; 70,960 B, +8,784 B from new stdlib deps for bench)

End-to-end handshake via python TCP client wire-conformant: announce → peer agree → server TT SEND → peer NAWS + TT IS + LINEMODE ACK → data echo. Slowloris defense at 60s; graceful EOF/error close; cross-platform via `lib/net.cyr` per [ADR 0001](../adr/0001-cross-platform-listener-decoupled-from-agnos.md).

## In-flight slot

**M2 — ANSI BBS aesthetic** (color, cursor positioning, banners).

Gate state (per [`roadmap.md`](roadmap.md)):

- **bannermanor** 1.0.0 ✅ — ready to consume for ASCII MOTD banners.
- **darshana** 0.5.3 ❌ — needs ≥ 1.0.0 stable for ANSI escape sequences (color, cursor positioning). Likely waiting on darshana's own 1.0 cut.

**Likely first M2 bite**: bannermanor MOTD on connect, replacing the current plaintext "agora 0.1.0 — telnet BBS (M1 protocol smoke)" string. bannermanor consumption is the path with the gate met today.

**Second bite gated on darshana 1.0**: ANSI-colored prompt + basic cursor positioning for menu redraws (NAWS-aware via the term_cols/term_rows already captured by M1's subneg parser — first concrete consumer of the NAWS data).

## Recent shipped

- **0.2.0** (2026-05-23) — M1 close: cross-platform telnet listener. 5-bite cycle (IAC parser, Q-method, NAWS+TT subneg, LINEMODE, bench harness). 24 tests; 70,960 B; first parser baseline at 10 ns/byte hot path. See [`CHANGELOG.md`](../../CHANGELOG.md#020--2026-05-23-m1-close-cross-platform-telnet-listener).
- **0.1.0** (2026-05-23) — Scaffold ship. argv dispatch + boot banner + 6 stub verbs. 43,216 B binary.

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
