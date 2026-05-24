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

**M6 — user accounts + auth → 0.6.0** (in progress, ADR 0006 landed 2026-05-23)

**sigil** 3.1.1 (bundled in cyrius 6.0.1's lib snapshot) is the identity primitive (gate met; standalone repo tip at 3.4.3 but the bundled version provides the same ed25519/sha256/hex surface we need). Scope: login flow over telnet, `whoami`, per-board posting permissions. Out of scope: federated identity, web-of-trust — those are v2.x pillar 1 (see [`roadmap-future.md`](roadmap-future.md)).

**M6-A landed**: [ADR 0006 — identity model](../adr/0006-identity-model.md). Decisions: (A) sigil Ed25519, (X) `<store>/.users/<fp16>/` per-user dir, (p) challenge/response (server nonce → client Ed25519 sig over `"agora-login:" + nonce_hex`), (P1) anon-read + auth-post default, `From: <handle> <fp16>` header on auth posts, `~/.agora/key` as the default keyfile. Rejects ML-DSA at first cut, password hashes, sigil-managed account store, sidecar registry, federated/WoT identity (v2.x).

**M6-B landed**: `src/account.cyr` (~230 LOC) with `compute_fingerprint` / `handle_valid` / `build_users_dir|user_dir|user_file` / `account_dir_ensure` / `account_register` / `account_lookup_pubkey|handle` / `account_resolve_handle`. 7 new tests (t50-t56); 56/56 green. Sigil + freelist added to stdlib deps. Binary 140 KB → 332 KB (most NOPed under DCE — see CHANGELOG entry).

**M6-C landed**: telnet `login <handle>` + challenge/response in `src/main.cyr`. New `MODE_LOGIN_AWAIT_SIG`; per-session globals for bound identity (`g_session_fp` / `g_session_handle`) + parked challenge (`g_login_fp` / `g_login_nonce`); `nonce_random` / `nonce_to_hex` / `format_challenge_msg` / `parse_auth_sig` primitives added to account.cyr. 5 new tests (t57-t61); 61/61 green. `bigint` + `ct` added to stdlib deps (sigil's `ed25519_verify` call chain needs them — SIGILL'd at runtime without them). Binary 332 → 351 KB. End-to-end smoke via openssl 3.x's `pkeyutl -sign -rawin` confirms sigil interop; failure paths (unknown handle, wrong sig) also verified.

**M6-D landed**: keygen + register + whoami (CLI + telnet). CLI verbs `agora keygen` / `agora register` / `agora whoami` (with `--key` / `--handle` / `--store` flags). Telnet `whoami` command prints bound identity or `anonymous`. New account.cyr primitives: `keyfile_load_seed` / `seed_to_pk` / `keyfile_to_fingerprint` / `keyfile_generate` / `nonce_random_into`. ADR 0006 keyfile format finalized at 32-byte raw seed (was "96 bytes — seed||sk" in initial sketch). 2 new tests (t62-t63) using RFC 8032 test-vector-1; 63/63 green. Binary 351 → 366 KB. End-to-end smoke: keygen → register → whoami → login round-trip with openssl 3.x signing.

**M6-E landed**: `From: <handle> <fp16>` header on authenticated posts; wire-side `auth required` gate on `post` / `reply`; CLI `--as <handle>` for op-side authored posts (validates handle ↔ key binding via store registry). `post_format_with_headers` and `post_new_with_subject_reply` grew `from_handle` + `from_fp` params; `list` renders `[handle|anon]` prefix, `read` prepends `From:` line. `post_from` extractor added to account.cyr. 3 new tests (t64-t66); 66/66 green. Test fix: t49 updated for new 8-arg signature. Binary 366 → 370 KB. End-to-end smoke verified anon + authored CLI posts + telnet auth-gate.

**M6-F landed**: per-board policy via `<store>/<board>/.policy` (`open` / `known` / `admin`) + `<store>/<board>/.admins` (one handle per line). `BoardPolicy` enum + `board_policy_get` / `board_admin_check` / `board_can_post` primitives in board.cyr. Wire-side + CLI `post`/`reply` both route through `board_can_post`. Missing `.policy` → default `open` (free backwards-compat with 0.5.x). 4 new tests (t67-t70); 70/70 green. End-to-end smoke (7 cases): open allows all, known allows registered users, admin allows only handles in `.admins`, anonymous always denied, missing `.admins` under `admin` denies even registered users. **M6 cycle code-complete — only the 0.6.0 closeout remains.**

**Bite plan to 0.6.0**:

- **M6-B** — account primitives in `src/account.cyr`: `compute_fingerprint(pk)` (sha256-then-truncate to 16 hex), `build_user_path(store, fp)`, `account_register(store, fp, pk, handle)`, `account_lookup_by_fp(store, fp)`, `account_lookup_by_handle(store, handle)`. Unit tests for each.
- **M6-C** — telnet `login <handle>` command + challenge/response: new `MODE_LOGIN_AWAIT_SIG` session state; nonce via `/dev/urandom`; 30 s deadline; `ed25519_verify` against the registered pubkey; session binds (fp, handle) on pass, reverts to anon on fail.
- **M6-D** — `whoami`: telnet replies `<handle> <fp16>` (or `anonymous`); CLI `agora whoami [--key <path>] [--store <path>]` decodes the keyfile + optional store lookup.
- **M6-E** — `From: <handle> <fp16>` header on posts via extension of `post_format_with_headers`; CLI `--as <handle>` for op testing; `list` renders `<id>  [<handle>]  <subject>`.
- **M6-F** — per-board posting policy: `<store>/<board>/.policy` (open / known / admin) + `<store>/<board>/.admins`. Default open; missing policy file == open. Enforce at `session_finalize_post` + CLI ingress.
- **M6 close** — bump 0.6.0, sync VERSION + cyrius.cyml + CHANGELOG + state.md + roadmap.md + doc-health.md.

Reference reading before each bite: ADR 0006 (the rationale), sigil's `ed25519_keypair` / `ed25519_sign` / `ed25519_verify` / `sign_data` / `verify_data` / `generate_keypair` primitives in `lib/sigil.cyr`, existing `src/board.cyr` for the per-store-file conventions to mirror.

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
| **sigil** | **M6 user accounts** | **3.1.1** (bundled in cyrius 6.0.1 snapshot; standalone repo at 3.4.3 — we consume the bundled version) | **✅ — consumed at M6-B** |
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
