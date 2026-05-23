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
| **Released** | `0.4.0` (2026-05-23) |
| **Cycle** | M0 + M1 (0.2.0) + M2 (0.3.0) + M5 partial (0.4.0) + **M5 close ready** — ADRs 0004 + 0005 + M5-E + M5-F landed 2026-05-23: agora is now a **multi-board threaded BBS over telnet**. Next release tag = 0.5.0 (M5 close). Release plan: 0.6 M6 sigil auth, 0.7 security sweep + CVE research, 0.8 v1 hardening, 1.0 ship on archaemenid iron. |
| **Toolchain pin** | cyrius `6.0.1` (in `cyrius.cyml [package].cyrius`) |
| **Source of truth** | `VERSION` file at repo root |

## Build artifacts

| Artifact | Size | Build line |
|---|---|---|
| `build/agora` (x86_64, no DCE) | 140,152 B at M5-F (135,064 M5-E; 129,096 M5-G; 128,352 M5-D; 116,904 M5-H; 116,232 M5-B; 109,992 M5-A; 85,544 M2 close; 70,960 M1 close; 43,216 v0.1.0 scaffold). M5-F adds +5,088 B for threading primitives + reply command + Replies-list rendering + --reply-to flag. | `cyrius build src/main.cyr build/agora` |
| `build/agora` (DCE) | TBD — first DCE build at M1 close | `CYRIUS_DCE=1 cyrius build src/main.cyr build/agora` |

Compile output reports `220 unreachable fns (26,707 B NOPed)` — the M1-close addition of `vec` + `fnptr` + `bench` (for the bench harness) grew the surface; DCE NOPs the bench-only paths but doesn't strip them from the file. Release-binary optimization (strip + DCE-aware emit) is a v1.x close-out concern.

## Tests + benchmarks

| Surface | Status |
|---|---|
| `src/test.cyr` | **49 tests passing** at M5-F — adds 6 M5-F threading tests (`subject_reply_prefix` add/no-double/case-insensitive, `post_reply_to` extract/missing, `post_format_with_headers` round-trip). Full wire integration verified via Python TCP-client smoke. |
| `benches/bench_telnet.bcyr` | **5 benchmarks** — see [`/BENCHMARKS.md`](../../BENCHMARKS.md). Hot path 10 ns/byte (plain) → 132 ns (4-option announce salvo). |
| `cyrius audit` | clean (build + lint pass; tests green; first bench baseline captured at M1 close) |

## Recently closed

**M1 closed 0.2.0 (2026-05-23)** — cross-platform telnet listener; 5 bites (IAC parser, RFC 1143 Q-method, RFC 1073 NAWS + RFC 1091 TERMINAL_TYPE subneg, RFC 1184 LINEMODE, bench harness). 24 tests; 70,960 B; first parser baseline at 10 ns/byte hot path. End-to-end python-client smoke wire-conformant. Cross-platform via `lib/net.cyr` per [ADR 0001](../adr/0001-cross-platform-listener-decoupled-from-agnos.md). See [`CHANGELOG.md`](../../CHANGELOG.md#020--2026-05-23-m1-close-cross-platform-telnet-listener).

**M2 closed 0.3.0 (2026-05-23)** — ANSI BBS aesthetic; 3 bites (M2-A bannermanor-rendered "AGORA" MOTD, M2-B darshana SGR coloring via `_buf` primitives, M2-C `--motd <path>` operator override). Bannermanor patched 1.0.0 → 1.0.1 the same day for ecosystem alignment on darshana `0.5.3`. M2-D (NAWS-aware width clamping) optional, deferred. 24 tests; 85,544 B. See [`CHANGELOG.md`](../../CHANGELOG.md#030--2026-05-23-m2-close-ansi-bbs-aesthetic).

## In-flight slot

**M5 — Post persistence**. ADR 0002 captures the storage layout: one file per post (`<store>/<id>.txt`), monotonic integer IDs, plaintext UTF-8 bodies. Cross-platform via `lib/io.cyr` + `lib/fs.cyr` (Linux today; macOS/Windows/AGNOS as the stdlib gains backends). No AGNOS-specific gate (ext4 WRITE is for the AGNOS target only; Linux works today via libc/syscalls).

**M5-A landed 2026-05-23**: `src/board.cyr` + CLI verbs (`post`/`list`/`read`) + 5 tests + end-to-end CLI round-trip. Binary 109,992 B.

**M5-B landed 2026-05-23**: in-session command interpreter over telnet. `handle_client` runs a line-buffered loop after the MOTD; supports `help` / `list` / `read <id>` / `post` (with `.`-terminated multi-line body) / `quit`. `agora serve` grew `--store <path>` (default `./agora-data/`). Session helpers factored into ~250 LOC. **agora is now a working BBS over telnet.** Binary 116,232 B.

**M5-C landed 2026-05-23**: `post_list` returns IDs ascending via `sort_i64_asc` (in-place insertion sort, O(n²), fine for v1.0 scale). Two new tests. Wire smoke confirms `list` returns `1 2 3 4 5`.

**M5-H landed 2026-05-23**: input filter on post bodies — `input_byte_ok` drops NUL (cstring-tooling poison) and ESC (terminal-control injection in stored posts read by other users). Lives at the storage-policy layer in `src/board.cyr`; enforced at ingress in `handle_client`. One new test plus wire-smoke proves a malicious post containing `\x1b[31m` and `\x00` lands on disk with the dangerous bytes stripped.

**M5-D landed 2026-05-23**: RFC-822-shaped headers per [ADR 0003](../adr/0003-rfc-822-post-headers.md). Each post file gets `Subject: ...\r\nDate: ISO-8601\r\n\r\n<body>`. New `post_body_offset` + `header_get` + `post_subject` primitives in `board.cyr`. Wire flow grew `MODE_POSTING_SUBJECT` between `MODE_COMMAND` and `MODE_POSTING` — typing `post` prompts `Subject:` first. `list` shows `<id>  <subject>`; `read` shows `Subject: ...\r\n\r\n<body>`. CLI `agora post` grew `--subject <text>` flag. Backwards compatible with M5-A/B/C headerless posts (sniffer rejects non-uppercase first bytes, falls back to whole-file-is-body). **Plus a session-buffer corruption bug fix**: paired LF after CR was being appended to the line buffer at position 0 (broke every command after the first). 38 tests; binary 128,352 B.

**M5-G landed 2026-05-23**: per-store flock around `post_max_id` + EXCL-claim + write critical section. Concurrent writers serialize; no ID race. Binary 129,096 B.

**M5-E landed 2026-05-23** ([ADR 0004](../adr/0004-board-layout.md)): boards. Flat-root = "main", subdirs = named (free backwards-compat with 0.4.0). Per-board ID counter + lockfile + post-extraction. New telnet commands: `boards`, `enter <name>`, `leave`. CLI grew `--board <name>` flag on post/list/read. 5 new tests; binary 135,064 B.

**M5-F landed 2026-05-23** ([ADR 0005](../adr/0005-threading-via-reply-to.md)): threading via `Reply-To: <id>` header (same-board, ID-only, scan-on-read). Telnet `reply <id>` derives Re: subject from parent, skips Subject prompt, writes Reply-To header on commit. Telnet `read <id>` appends `Replies: N, M, ...` after body. CLI `--reply-to <id>` flag on `agora post`; auto-derives Re: when --subject absent. 6 new tests (49 total). Binary 140,152 B (+5,088 B).

**M5 cycle complete** — six bites + two ADRs (0002, 0003, 0004, 0005). Next release tag is **0.5.0** (M5 close).

## Recent shipped

- **0.4.0** (2026-05-23) — M5 partial: post persistence. 6-bite cycle (M5-A storage primitives, M5-B in-session command interpreter, M5-C sorted listing, M5-D RFC-822 headers, M5-G store-write flock, M5-H ingress input filter) + 2 ADRs (0002 one-file-per-post, 0003 RFC-822 headers). 38 tests; 129,096 B (+43.5 KB from M2 close, mostly DCE-eligible). **agora is a working single-board BBS over telnet.** See [`CHANGELOG.md`](../../CHANGELOG.md#040--2026-05-23-m5-partial--post-persistence-with-metadata--concurrent-writer-correctness).
- **0.3.0** (2026-05-23) — M2 close: ANSI BBS aesthetic. 3-bite cycle (bannermanor MOTD, darshana SGR colors, `--motd` operator override). 24 tests still green; 85,544 B (+14.6 KB from M1 close, most DCE-eligible). bannermanor patched 1.0.1 the same day for ecosystem alignment on darshana 0.5.3.
- **0.2.0** (2026-05-23) — M1 close: cross-platform telnet listener. 5-bite cycle (IAC parser, Q-method, NAWS+TT subneg, LINEMODE, bench harness). 24 tests; 70,960 B; first parser baseline at 10 ns/byte hot path.
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
| **bannermanor** | M2 ASCII banners | 1.0.1 | ✅ consumed at M2-A |
| **darshana** | M2 ANSI escapes | 0.5.3 (pinned git dep) | ✅ consumed at M2-B (functionality, not version label, was the gate) |
| **kii** | M3 inline-image posts | 1.0.0 | ✅ |
| **sankoch** | M4 stored-file deltas | 2.2.6 | ✅ |
| **sigil** | M6 user accounts | 3.4.2 | ✅ |
| **agnos** ext4 WRITE | AGNOS-target M5 (Linux M5 lands sooner) | agnos 1.32.2 in-flight | ❌ pending agnos 1.33.x |

## Bootstrap chain / source surface

- `src/main.cyr` — argv dispatch + verb handlers + telnet `handle_client` (~400 LOC at M5-A)
- `src/telnet.cyr` — RFC 854 IAC parser + RFC 1143 Q-method + RFC 1184 LINEMODE state machine (M1, 0.2.0)
- `src/board.cyr` — post storage primitives per ADR 0002 (M5-A, 2026-05-23)
- `src/test.cyr` — 29-test conformance suite (M1 IAC/Q/subneg + M5-A board)
- `benches/bench_telnet.bcyr` — 5-bench parser harness (M1 close, 0.2.0)
- `lib/` — resolved deps (15 stdlib modules + darshana git dep): string, fmt, alloc, io, syscalls, assert, args, net, result, tagged, vec, fnptr, bench, str, fs + lib/darshana.cyr (pinned 0.5.3)

## Cross-references

- [`roadmap.md`](roadmap.md) — milestones + sub-bites + v1.0 criteria (durable).
- [`../doc-health.md`](../doc-health.md) — doc currency across the tree.
- [`../../CLAUDE.md`](../../CLAUDE.md) — durable rules.
- [`../../CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.
