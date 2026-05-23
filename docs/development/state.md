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
| `build/agora` (x86_64, no DCE) | 61,152 B at M1 third-bite (59,280 second-bite; 56,064 first-bite; 43,216 v0.1.0 scaffold) | `cyrius build src/main.cyr build/agora` |
| `build/agora` (DCE) | TBD — first DCE build at M1 close | `CYRIUS_DCE=1 cyrius build src/main.cyr build/agora` |

Compile output reports `188 unreachable fns (21,861 B)` — agora consumes a thin slice of the expanded stdlib (added `net` + `result` + `tagged` at M1 first-bite); DCE will roughly cut the binary by 22 KB at the M1 close.

## Tests + benchmarks

| Surface | Status |
|---|---|
| `src/test.cyr` | **20 tests passing** at M1 third-bite — RFC 854 IAC + RFC 1143 Q-method + RFC 1073 NAWS + RFC 1091 TERMINAL_TYPE (parser conformance, announce salvo, Q transitions, NAWS 80×24 + IAC-escape variant + malformed-drop, TT IS string capture, WILL TT → SEND emit) |
| Bench harness | not yet present — earns at M1 close (parser throughput + accept-loop rate) |
| `cyrius audit` | clean (build + lint pass; tests green; bench surface empty pre-M1-close) |

## In-flight slot

**M1 — Telnet listener (RFC 854 + LINEMODE 1184)**, cross-platform via `lib/net.cyr`.

**First-bite landed 2026-05-23**: IAC parser (`src/telnet.cyr`) + naive-refuse option negotiation + listener loop in `cmd_serve` + 10-test conformance suite. Binary 56,064 B.

**Second-bite landed 2026-05-23**: RFC 1143 Q-method option negotiation (`Q_NO` / `Q_WANTYES` / `Q_YES` per option per side; per-connection 512 B of option state). `telnet_announce` sends the four-option opening salvo (`WILL ECHO`, `WILL SGA`, `DO NAWS`, `DO TT`). Slowloris defense via `sock_set_recv_timeout(cfd, 60, 0)`. Graceful close on `n == 0` / `n < 0`. Test suite grew 10 → 15. Binary 59,280 B (+3,216 B).

**Third-bite landed 2026-05-23**: NAWS (RFC 1073) + TERMINAL_TYPE (RFC 1091) subneg parsing. `telnet_handle_sb` decodes payloads into per-connection `term_cols` / `term_rows` / `term_type` fields (256-byte ASCII buffer for TT). `ts_on_him_yes` hook auto-emits `IAC SB TT SEND IAC SE` when him-TT transitions to `Q_YES`. EV_SB wired into `handle_client`. Test suite grew 15 → 20. End-to-end smoke runs the full handshake — agree to ECHO/SGA, server sends TT SEND on WILL TT, NAWS + TT IS replies consumed silently, data byte echoes clean. Binary 61,152 B (+1,872 B).

**Remaining bites for M1 close** (per [`roadmap.md`](roadmap.md#m1--telnet-listener-rfc-854--rfc-1184-linemode)):

- RFC 1184 LINEMODE — full MODE subnegotiation (EDIT / TRAPSIG / SOFT_TAB / LIT_ECHO) + SLC (Set Local Character) table. Move LINEMODE from untracked → tracked (`opt_pref_him` returns 1), add LINEMODE subneg dispatch in `telnet_handle_sb`.
- Bench harness — parser throughput per byte + accept-loop rate. First numbers go into `BENCHMARKS.md` at repo root.

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
