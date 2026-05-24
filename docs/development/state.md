---
name: agora State
description: Live state snapshot for the agora repo — volatile data refreshed every release
type: state
---

# agora — State Snapshot

> **Last refresh**: 2026-05-23 (post-0.9.2 ship; final 1.0 closeout sweep — bench re-capture within noise of M1 baseline, security re-scan clean, full clean DCE build green, all six example scripts re-smoked; **only the archaemenid LAN iron validation gate remains between us and 1.0**) | **Refresh cadence**: every release; ideally bumped by the release post-hook.

Per [first-party-documentation § CLAUDE.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#claudemd), CLAUDE.md holds **durable rules**; this file holds **volatile state**. If a claim drifts within a minor's worth of work, it belongs here, not in CLAUDE.md.

---

## Next-session boot guide

**What to know after a fresh agent boot:**

1. **Where we are**: agora is a **multi-user, multi-board threaded BBS with sigil-backed auth, per-board posting policy, audit-hardened input, concurrent connection handling, keyfile mode warnings, anonymous-board-create gating, a frozen pre-1.0 ABI, a freshly rewritten guides + examples tree, and a fully-passed CLAUDE.md §1-11 closeout sweep** at v0.9.2. **Every doc-health row is Fresh**, **every 0.7.0 audit finding is closed**, **benches are within noise of the M1-close baseline**, and **all six `docs/examples/` scripts pass against the 0.9.2 binary**. The only remaining gate between this codebase and 1.0 is criterion #3 of the v1.0 list: telnet validation on the archaemenid LAN iron NUC — a user task, not codeable from here.
2. **Where to read first**: this file (state.md), then [`roadmap.md`](roadmap.md) for the release plan, then [`CLAUDE.md`](../../CLAUDE.md) for project rules. Decisions live in [`../adr/`](../adr/) — **eight ADRs** as of 0.9.0 (ADR 0007 fork-per-accept at 0.8.0; ADR 0008 PostHeaders struct at 0.9.0). Audit findings live in [`../audit/2026-05-23-audit.md`](../audit/2026-05-23-audit.md) — all closed by 0.8.3; preserved as the audit record. Guides live in [`../guides/getting-started.md`](../guides/getting-started.md); runnable example scripts live in [`../examples/`](../examples/) (six scripts, numbered 01–06).
3. **What's next**: **1.0.0 cut + archaemenid handoff.** Workstation-side tasks (VERSION bump, [1.0.0] CHANGELOG entry summarizing the M0–M6 + 0.7–0.9 arc, state.md / roadmap.md / doc-health.md final sync, three inline literals in main.cyr) are landable right now. Iron-side tasks (criterion #3 telnet validation on archaemenid LAN; criterion #4 8-user fanout concurrency check via an N=8 extension of `docs/examples/04-concurrent-smoke.py`) need a user with shell access on the NUC. The git tag itself remains a user task per CLAUDE.md "do not commit or push".
4. **What to build / test**: `cyrius build src/main.cyr build/agora` (clean → **378,440 B at 0.9.2**), `cyrius test src/test.cyr` (80/80 pass), `cyrius bench benches/bench_telnet.bcyr` (5 baselines within noise of M1-close — fork happens before the IAC byte path; first run can show transient elevation, re-run to confirm). End-to-end demos: `docs/examples/01-build-and-test.sh` through `06-board-policy.sh` — all six verified at 0.9.2. M6 CLI: `./build/agora keygen --key ./keys/qix` + `./build/agora register --handle qix --store ./bbs` + `./build/agora whoami --key ./keys/qix --store ./bbs`. Telnet login (openssl-signed): `docs/examples/05-telnet-login.sh`.
5. **What NOT to do**: don't commit / push — user owns git. Don't use `gh` CLI. Don't add unprompted version bumps (per durable CLAUDE.md rules). When inventing demo handles in smoke tests / examples, use three-letter old-arcade-game names (`qix`, `pac`, `zax`, `dig`, `jst`) — NOT `alice` (per saved memory). **Don't add SIGCHLD signal handlers** to the accept loop — ADR 0007 § Alternatives explicitly rejected sigaction-based reaping due to the x86_64 trampoline trap in cyrius. Stick with the waitpid(WNOHANG) loop. **Don't add anonymous-post paths** without a deliberate per-board policy ADR — M6 default is `anon-read, auth-post` (board_can_post returns 0 for any session_fp==0 across all three policy modes today).

---

## Version

| Field | Value |
|---|---|
| **Released** | `0.9.2` (2026-05-23) |
| **Cycle** | M0 / M1 / M2 / M5 / M6 + 0.7.0 security sweep + 0.8.0-0.8.3 audit followups + 0.9.0 ABI freeze + 0.9.1 doc-pass + **0.9.2 final closeout sweep (G)** all closed. **Every bite of the 0.8 cycle plan (A–G) shipped; every audit finding discharged; ABI frozen; benches within noise of M1-close baseline; doc-health all Fresh.** Next: 1.0.0 cut + archaemenid iron validation. |
| **Toolchain pin** | cyrius `6.0.1` (in `cyrius.cyml [package].cyrius`) |
| **Source of truth** | `VERSION` file at repo root |

## Build artifacts

| Artifact | Size | Build line |
|---|---|---|
| `build/agora` (x86_64, no DCE) | **378,440 B** at 0.9.2 | `cyrius build src/main.cyr build/agora` |
| `build/agora` (DCE) | same size — DCE NOPs unreachable fns in place rather than stripping (**666 fns / ~159 KB** NOPed at 0.9.0). Real binary strip is a v1.x close-out concern. | `CYRIUS_DCE=1 cyrius build src/main.cyr build/agora` |
| `build/test` | 80 tests | `cyrius build src/test.cyr build/test && ./build/test` |

Binary growth across cycles: 43 KB scaffold (0.1.0) → 71 KB M1 close (0.2.0) → 86 KB M2 close (0.3.0) → 129 KB M5 partial (0.4.0) → 140 KB M5 close (0.5.0) → 375 KB M6 close (0.6.0) → 377 KB 0.7.0 security sweep → 378 KB 0.8.0 concurrent-accept → 378 KB 0.8.1 keyfile warn → 378 KB 0.8.2 sigil-diff-no-bump → 379 KB 0.8.3 board-create gate → 378 KB 0.9.0 ABI freeze → 378 KB 0.9.1 doc-pass → **378 KB 0.9.2 closeout**. The 0.9.1 → 0.9.2 delta is **0 B (exact match)** — version-string length deltas were neutral this cycle; no code change.

## Tests + benchmarks

| Surface | Status |
|---|---|
| `src/test.cyr` | **78 tests passing** at 0.7.0 (+8 audit regressions). Coverage: RFC 854/1143/1073/1091/1184 IAC + Q-method + subneg conformance (M1, t01-t24); board-storage + sort + ingress filter + RFC-822 headers + board layout + Reply-To threading (M5, t25-t49); fingerprint + handle validation + .users path builders (M6-B, t50-t56); nonce/hex helpers + auth-sig parser (M6-C, t57-t61); RFC 8032 seed→pk + fp vectors (M6-D, t62-t63); From-header round-trip + anonymous handling (M6-E, t64-t66); policy path builders + anonymous-deny early-return (M6-F, t67-t70); **0.7.0 audit regressions** (t71 header_text_ok control-byte filter, t72 header_text_buf_ok CRLF injection scan, t73-t74 fp16_valid accept/reject, t75-t76 post_from rejects tampered handle/fp, t77 parse_post_id 19+ digit overflow guard, t78 parse_post_id 18-digit ceiling). Full wire integration verified via Python TCP-client + openssl smoke (not in test.cyr). |
| `benches/bench_telnet.bcyr` | **5 benchmarks** — see [`/BENCHMARKS.md`](../../BENCHMARKS.md). Hot path 10 ns/byte (plain) → ~130 ns (4-option announce salvo). All within noise of the M1-close baseline at 0.7.0 (security patches don't touch the parser hot path). |
| `cyrius audit` | clean from a fresh build at 0.7.0 (lint + build + tests green; bench baseline reproducible). |

## In-flight slot

**1.0.0 cut — handoff for archaemenid iron validation**

The workstation-side prep is complete: all bites of the 0.8 cycle plan shipped (A through G), every audit finding closed, ABI frozen, docs Fresh top-to-bottom, benches re-captured within noise of M1-close, all six `docs/examples/` scripts pass against the 0.9.2 binary, full `rm -rf build && cyrius deps && CYRIUS_DCE=1 cyrius build` green.

**Workstation tasks remaining for the 1.0 cut** (the agent landing this should do these together):

- **VERSION 0.9.2 → 1.0.0** + three inline literal bumps in `src/main.cyr` (`print_banner`, `cmd_version`, `render_motd`).
- **CHANGELOG [1.0.0] entry** as a summary of the M0–M6 + 0.7–0.9 arc — not a per-bite list (CHANGELOG already has those) but a release-narrative paragraph + the v1.0 criteria status (criteria 1, 2, 5, 6 ✅ from this side; criteria 3, 4 ✅ from iron).
- **state.md / roadmap.md / doc-health.md** final 1.0.0 sync (this file's "Released" field → 1.0.0; roadmap "1.0.0" row → ✅; doc-health bucket counts refreshed).
- **README.md status pointer** — currently points at the doc tree; at 1.0 cut, surface the milestone.

**Iron-side tasks** (user, on archaemenid NUC running AGNOS):

- **v1.0 criterion #3** — telnet validation: iron NUC serves; second LAN box connects → log in → list boards → read a thread → post a reply → log off. Confirm wire interop end-to-end. The full prose for this lives in `docs/guides/getting-started.md` § "Authenticated flow"; the canned smoke is `docs/examples/05-telnet-login.sh` (point HOST + STORE at the iron deployment).
- **v1.0 criterion #4** — 8-user fanout concurrency check. Extend `docs/examples/04-concurrent-smoke.py`'s N from 3 → 8 (the script already parameterizes both port and N); assert no message loss, no state corruption across 8 simultaneous sessions. ADR 0007 fork-per-accept architecture guarantees process isolation, so the assertion should hold trivially — but the gate wants it observed on iron.

**Git tag** is the user's call per CLAUDE.md "do not commit or push".

**Previous (0.9.2 final closeout sweep) cycle closed 2026-05-23** — see "Recent shipped" below.

### Archived 0.9.2 in-flight notes (for next-session reference)

**Bite plan**: G was a single-bite cycle — re-run benches, walk CLAUDE.md "Closeout Pass" §1-11 against the 0.9.x tip, smoke every example one final time, ship. Shipped 2026-05-23 from a single editing session.

**Closeout pass §1-11 walk** (per CLAUDE.md):
- §1 full test suite — 80/80 ✅
- §2 benchmark baseline — re-captured; all 5 within ±2 ns of M1-close (first run had `announce_salvo` elevated to 163 ns avg with min=131 ns; re-run stabilized at 134 ns — system noise on first attempt)
- §3 dead-code audit — 666 fns / 159 KB NOPed by DCE, all stdlib bloat (sigil pulls map / mutex / shake256 that agora doesn't call); no agora-source dead code
- §4 refactor pass — nothing accreted in 0.9.x worth consolidating (0.9.0 already did the post-API shape consolidation; 0.9.1 added zero code)
- §5 code review pass — diff vs. 0.9.0 is the PostHeaders refactor (already reviewed at 0.9.0 ship) + 0.9.1 doc rewrites + 0.9.2 version literals; nothing new in code
- §6 cleanup sweep — no TODO / FIXME / XXX / HACK markers in `src/*.cyr`; version comments correctly reference release-of-introduction (M6-D, 0.7.0 audit, etc.) not current
- §7 security re-scan — no `sys_system`; one `var buf[32]` in `board.cyr:931` verified bounded against 32-byte `file_read_all` cap; no new external-input paths since 0.8.3
- §8 downstream check — no consumers yet (agora is a binary, not a library); v2.x pillar 5 self-distribution would add downstream, post-1.0
- §9 doc sync — CHANGELOG / state.md / roadmap.md / doc-health.md / BENCHMARKS.md all refreshed
- §10 version verify — VERSION 0.9.2, cyrius.cyml `${file:VERSION}`, binary `agora 0.9.2`, CHANGELOG header `[0.9.2]` all match
- §11 full clean build — `rm -rf build && cyrius deps && CYRIUS_DCE=1 cyrius build src/main.cyr build/agora` → 378,440 B ✅

**Smoke re-verification**: every example script run end-to-end against the freshly-built 0.9.2 binary. Same identity (fp `bdccc7a4d1991a4d` from a fresh keygen) successfully posts, reads back with the correct From header, and completes the telnet challenge/response.

**Carried forward**: nothing — G closes the bite. The next slot is the 1.0.0 cut.

### Archived 0.9.1 in-flight notes (for next-session reference)

**Bite plan**: 3 sub-bites of F (rewrite getting-started.md → rewrite examples/README.md + write six runnable scripts → refresh doc-health.md). Shipped 2026-05-23 from a single editing session. No code changes beyond the three inline version literals in `src/main.cyr` (`print_banner`, `cmd_version`, `render_motd`).

**Verification protocol**: each example script run end-to-end against `./build/agora` immediately after writing. 01 build+test passes. 02 register+post writes `./bbs/1.txt` with `From: qix <fp16>`. 03 confirms anon-read works and anon-post correctly returns exit 1. 04 runs against a backgrounded `./build/agora serve 2323` — all 3 concurrent sessions get banner + IAC + boards reply. 05 drives the full wire challenge/response to a `welcome, qix` server confirmation. 06's 9 policy-mode × identity-class assertions all pass.

**Doc-tightening fixes caught during verification** (each landed in the same diff as the example):

- Anonymous CLI post is **denied** at M6 — `board_can_post` returns 0 for any `session_fp == 0` across all three policy modes (open / known / admin), not just on `known`/`admin`. Initial draft of `getting-started.md` showed `agora post` working without `--as`. Fixed.
- Main-board posts live at `<store>/N.txt` not `<store>/main/N.txt` (ADR 0004 flat-root). Initial example 02 grepped the wrong path. Fixed.
- Telnet auth-line format is `auth: <hex>` (colon required, optional space), not `auth <hex>`. Initial example 05 dropped the colon. Fixed.
- `openssl pkeyutl -sign -rawin` for Ed25519 is a oneshot operation and rejects stdin; needs `-in <file>`. Initial example 05 piped via stdin. Switched to a tmpfile and dropped the PEM wrapper in favor of `-keyform DER` direct.

**Carried forward**: nothing — F closes the bite. Next slot is G (0.9.2 closeout).

### Archived 0.8.0 in-flight notes (for next-session reference)

### Archived 0.8.0 in-flight notes (for next-session reference)

**Bite plan**: 5 sub-bites of E (ADR design, fork implementation, zombie reaper, smoke test, closeout). Shipped 2026-05-23 from a single editing session.

**Design decision**: fork-per-accept (option F) over thread-per-accept (option T) because M2 only closes with a shared-state refactor under threading; fork closes M2 for free via address-space isolation. Single-thread epoll (option E) also rejected — would force every byte handler in `handle_client` to be yield-aware, doubling cognitive load on the line/IAC state machine. Single-track-with-arena (option S) only closes M1; M2 stays queued. Memory model: process-exit cleanup (option X) over per-conn freelist arena (option Y) — kernel-managed reclamation is strictly stronger than `fl_free`. Zombie reaper: non-blocking `sys_waitpid(-1, NULL, WNOHANG)` loop (option p) over `SIG_IGN` (option q) or `SA_NOCLDWAIT` (option r) — avoids the x86_64 sigaction trampoline trap that cyrius `lib/darshana.cyr` documents.

**Smoke verification**: 3 simultaneous TCP sessions via `/tmp/agora-concurrent-smoke.py` — all 3 got own banner + own anonymous response (proves no global collision, M2 closed). Reaper drains zombies from previous accept iterations (verified: round-1's 3 zombies cleared at round-2's accept). Steady-state: ≤ N zombies pending between accepts, where N = children that exited since last accept.

**Carried forward**: audit M4 (anonymous `enter` board-create gate) — independent of concurrency model, queued for 0.8-B.

### Archived 0.7.0 in-flight notes (for next-session reference)

The 0.7.0 audit produced four deferred items that 0.8 has to land before the 1.0 cut:

- **M1 + M2 — concurrent-accept refactor + per-conn memory arenas.** Today the accept loop single-tracks and `alloc()` is bump-only; long-running serve accretes ~73 KB / conn + ~100 KB / `read`. Co-scheduled work: move identity slots (`g_session_*` / `g_login_*`) and per-command working buffers into a per-connection arena freed at `sock_close`. Once concurrent-accept lands, M2's login-challenge slot-collision becomes load-bearing — same refactor fixes both.
- **M4 — anonymous `enter` can auto-create boards** (storage exhaustion vector). Either require auth for `board_ensure` from the wire side, OR add an accept-loop rate limit (and revisit whether `enter` should still be anonymous-permitted).
- **L1 — `keyfile_load_seed` warn-on-mode.** `fstat` the keyfile after open; warn on stderr if mode & 0o077 != 0. Don't refuse (containers).
- **sigil 3.1.1 → 3.4.3 release-notes diff read.** Confirm `ed25519_verify` constant-time guarantee, scan for crypto fixes between bundled and tip.

Plus the doc-debt: rewrite `docs/guides/getting-started.md` + `docs/examples/` for the 0.7.0 surface (still stale per doc-health Tier 5/6), bumped from 0.7.x deferred queue.

Reference reading before the cycle: [`../audit/2026-05-23-audit.md`](../audit/2026-05-23-audit.md) (especially the M1/M2/M4/L1 detail), [ADR 0006](../adr/0006-identity-model.md) for the threat model, CLAUDE.md "Closeout Pass" for the 11-step gate.

**Previous (0.7.0 security sweep) cycle closed 2026-05-23** — see "Recent shipped" below for the bite list.

### Archived 0.7.0 in-flight notes (for next-session reference)

**Audit cycle plan**: line-by-line read of `src/telnet.cyr` (718), `src/board.cyr` (956), `src/account.cyr` (497), `src/main.cyr` (1612) against CLAUDE.md "Security Hardening" checklist + external CVE history. Output: `docs/audit/2026-05-23-audit.md` with severity rubric (CRITICAL/HIGH/MEDIUM/LOW/DOCUMENTED), per-finding repro + fix, external CVE review table.

**0.7.0 findings**: zero CRITICAL. Five actionable landed as fixes (H1 CLI subject CRLF, H2 cmd_list/cmd_read --board path-traversal, H3 post_from re-validation, M3 parse_post_id overflow guard, M6 30s login deadline — the last was the M6-close deferred item). Four items deferred to 0.8 (M1/M2/M4/L1; see In-flight slot above).

**Test coverage**: 70 → 78 (+8 regression tests). Binary 374,968 → 377,184 B (+2,216 B / +0.6%) — fits the "audit additions are small" expectation.

**Smoke verification**: each HIGH fix tested end-to-end via the CLI binary; exit codes + error messages match the audit doc's repro lines. Wire-flow smoke deferred until concurrent-accept lands (no useful new wire smoke this cycle beyond what M6 already validated).

### Archived M6 in-flight notes (for next-session reference)

**sigil** 3.1.1 (bundled in cyrius 6.0.1's lib snapshot) is the identity primitive (gate met; standalone repo tip at 3.4.3 but the bundled version provides the same ed25519/sha256/hex surface we need). Scope: login flow over telnet, `whoami`, per-board posting permissions. Out of scope: federated identity, web-of-trust — those are v2.x pillar 1 (see [`roadmap-future.md`](roadmap-future.md)).

**M6-A landed**: [ADR 0006 — identity model](../adr/0006-identity-model.md). Decisions: (A) sigil Ed25519, (X) `<store>/.users/<fp16>/` per-user dir, (p) challenge/response (server nonce → client Ed25519 sig over `"agora-login:" + nonce_hex`), (P1) anon-read + auth-post default, `From: <handle> <fp16>` header on auth posts, `~/.agora/key` as the default keyfile. Rejects ML-DSA at first cut, password hashes, sigil-managed account store, sidecar registry, federated/WoT identity (v2.x).

**M6-B landed**: `src/account.cyr` (~230 LOC) with `compute_fingerprint` / `handle_valid` / `build_users_dir|user_dir|user_file` / `account_dir_ensure` / `account_register` / `account_lookup_pubkey|handle` / `account_resolve_handle`. 7 new tests (t50-t56); 56/56 green. Sigil + freelist added to stdlib deps. Binary 140 KB → 332 KB (most NOPed under DCE — see CHANGELOG entry).

**M6-C landed**: telnet `login <handle>` + challenge/response in `src/main.cyr`. New `MODE_LOGIN_AWAIT_SIG`; per-session globals for bound identity (`g_session_fp` / `g_session_handle`) + parked challenge (`g_login_fp` / `g_login_nonce`); `nonce_random` / `nonce_to_hex` / `format_challenge_msg` / `parse_auth_sig` primitives added to account.cyr. 5 new tests (t57-t61); 61/61 green. `bigint` + `ct` added to stdlib deps (sigil's `ed25519_verify` call chain needs them — SIGILL'd at runtime without them). Binary 332 → 351 KB. End-to-end smoke via openssl 3.x's `pkeyutl -sign -rawin` confirms sigil interop; failure paths (unknown handle, wrong sig) also verified.

**M6-D landed**: keygen + register + whoami (CLI + telnet). CLI verbs `agora keygen` / `agora register` / `agora whoami` (with `--key` / `--handle` / `--store` flags). Telnet `whoami` command prints bound identity or `anonymous`. New account.cyr primitives: `keyfile_load_seed` / `seed_to_pk` / `keyfile_to_fingerprint` / `keyfile_generate` / `nonce_random_into`. ADR 0006 keyfile format finalized at 32-byte raw seed (was "96 bytes — seed||sk" in initial sketch). 2 new tests (t62-t63) using RFC 8032 test-vector-1; 63/63 green. Binary 351 → 366 KB. End-to-end smoke: keygen → register → whoami → login round-trip with openssl 3.x signing.

**M6-E landed**: `From: <handle> <fp16>` header on authenticated posts; wire-side `auth required` gate on `post` / `reply`; CLI `--as <handle>` for op-side authored posts (validates handle ↔ key binding via store registry). `post_format_with_headers` and `post_new_with_subject_reply` grew `from_handle` + `from_fp` params; `list` renders `[handle|anon]` prefix, `read` prepends `From:` line. `post_from` extractor added to account.cyr. 3 new tests (t64-t66); 66/66 green. Test fix: t49 updated for new 8-arg signature. Binary 366 → 370 KB. End-to-end smoke verified anon + authored CLI posts + telnet auth-gate.

**M6-F landed**: per-board policy via `<store>/<board>/.policy` (`open` / `known` / `admin`) + `<store>/<board>/.admins` (one handle per line). `BoardPolicy` enum + `board_policy_get` / `board_admin_check` / `board_can_post` primitives in board.cyr. Wire-side + CLI `post`/`reply` both route through `board_can_post`. Missing `.policy` → default `open` (free backwards-compat with 0.5.x). 4 new tests (t67-t70); 70/70 green. End-to-end smoke (7 cases): open allows all, known allows registered users, admin allows only handles in `.admins`, anonymous always denied, missing `.admins` under `admin` denies even registered users. **M6 cycle code-complete — only the 0.6.0 closeout remains.**

**Bite plan to 0.6.0** — all six bites + closeout shipped 2026-05-23. See "Recent shipped" below + CHANGELOG [0.6.0] for per-bite detail.

**0.6.0 closeout note**: deferred from M6 first-cut and queued for 0.7.x (these are M6-polish items, not security findings — surfacing here so they don't drop):

- **30 s deadline on parked login challenge** (M6-C ADR 0006 § Specifics, deferred at first-cut because the existing `RECV_TIMEOUT_SECS = 60` slowloris defense incidentally drops stale sockets). Wants a monotonic-clock check in MODE_LOGIN_AWAIT_SIG dispatch.
- **`agora policy set <board> <mode>` + `agora admins {add,rm,list}` CLI verbs** (M6-F first-cut leaves operators to edit `.policy` / `.admins` files directly). Earn their slots when a real deployment asks.
- **Lossless re-derivation of `getting-started.md` + `docs/examples/`** to cover the M6 surface (still stale, per doc-health Tier 5 + Tier 6).

---

## Recent shipped

- **0.9.2** (2026-05-23) — final 1.0 closeout sweep (bite G). Last release before the 1.0 cut. Full CLAUDE.md "Closeout Pass" §1-11 against the 0.9.x tip: tests 80/80, benches re-captured within noise of M1-close baseline (transient first-run noise on `announce_salvo`, second run at 134 ns matched baseline), security re-scan clean, full clean DCE build green (378,440 B exact), all 6 `docs/examples/` scripts re-smoked against the rebuilt binary. No code changes beyond three inline version literals. BENCHMARKS.md updated with a 0.9.2 row; CHANGELOG / state.md / roadmap.md / doc-health.md all refreshed. **Every bite of the 0.8 cycle plan (A–G) has now shipped.** Only criterion #3 (iron-NUC validation) and #4 (8-user fanout on iron) remain between us and 1.0.
- **0.9.1** (2026-05-23) — guides + examples doc-pass (bite F). Long-deferred Tier 5 + Tier 6 rewrite: `docs/guides/getting-started.md` (74-line 0.1.0-stub-verb walkthrough → full 0.9.0-surface walkthrough), `docs/examples/README.md` (placeholder → 6-row index), six runnable example scripts (01 build-and-test, 02 register-and-post, 03 anonymous-read, 04 concurrent-smoke.py, 05 telnet-login, 06 board-policy). Every script verified end-to-end against `./build/agora`; 5 doc-tightening fixes caught during verification (M6 auth-post default, ADR 0004 flat-root path, `auth:` colon, openssl Ed25519 oneshot quirk, `open` policy table). No code changes beyond three inline version literals. 80/80 tests; 378,440 B (+8 B / +0.002%). **Closes the last `🟡 Stale` row in `docs/doc-health.md`.**
- **0.9.0** (2026-05-23) — PostHeaders struct ABI freeze ([ADR 0008](../adr/0008-post-headers-struct.md)). `post_format_with_headers(8 args)` / `post_new_with_subject_reply(8 args)` → `post_format(ph, body, len, out, cap)` / `post_new(store, board, ph, body, len)`. Struct setters: `post_headers_set_subject` / `post_headers_set_reply_to` / `post_headers_set_from`. **Breaking** (binary, no library consumers): dead M5-A `post_new(4-arg)` + dead M5-D / M5-F shim wrappers removed. **Wire format byte-identical** — 0.4-0.8 stores keep reading. Future v1.x headers (federated Origin, content-hash) add `PH_*` offsets without changing call shape. 80/80 tests; binary 378,936 → 378,432 (−504 B / −0.13%, refactor + dead-code shrink).
- **0.8.3** (2026-05-23) — anonymous board-create gate (audit M4 closed). Wire-side `enter <name>` now denies the create case for anonymous sessions (`auth required to create new boards`); existing-board enter stays anonymous-readable. New `board_exists(store, board)` helper in `src/board.cyr` + ~12 LOC auth gate in `session_execute` enter handler. CLI path was already gated via `cmd_post`'s `board_can_post`. **All 0.7.0 audit findings now closed.** 80 tests (+1 t80 for the existence check); 378,936 B (+520 B / +0.14%).
- **0.8.2** (2026-05-23) — sigil 3.1.1 → 3.4.3 release-notes diff read (0.7.0 audit deferred item discharged). **No sigil bump needed**: 0 CRITICAL/HIGH affecting agora's consumed surface; constant-time discipline maintained; Ed25519 malleability fix already in 3.1.1; the one MEDIUM (thread-safety on module-global crypto scratch) doesn't apply to agora's fork-per-conn single-threaded use. 3.2-3.4 improvements (parallel batch, alloc-free verify, NI self-test) don't touch our call pattern. 79/79 tests unchanged; +16 B binary (version literals only).
- **0.8.1** (2026-05-23) — keyfile mode warn-on-load (audit L1 closed). `keyfile_load_seed` opens + fstats + warns to stderr if `mode & 0o077 != 0`; loads anyway (containerized deployments may legitimately use world-readable mounts). New `mode_is_loose` pure-bit helper + `keyfile_warn_loose_mode` fstat wrapper in `src/account.cyr`. 79 tests (+1 t79 for the mode-bit math); 378,400 B (+880 B / +0.23%).
- **0.8.0** (2026-05-23) — concurrent accept via fork-per-connection ([ADR 0007](../adr/0007-fork-per-accept-concurrency.md)). Audit M1 (bump-allocator memory growth) + M2 (login-challenge slot collision) both close via process isolation. Loop: drain zombies → accept → fork → child runs handle_client + exit / parent loops. **agora is now a truly multi-user telnet BBS** — open as many concurrent sessions as the kernel allows. +336 B binary (+0.09%); no new stdlib deps; tests unchanged at 78/78 (E is in the accept loop, not in unit-testable code). Audit M4 (anonymous board-create) carried forward to 0.8-B.
- **0.7.0** (2026-05-23) — pre-1.0 security sweep. First `docs/audit/` entry (2026-05-23-audit.md). 5 actionable findings fixed (H1 CLI subject CRLF injection, H2 cmd_list/cmd_read --board path-traversal, H3 post_from re-validation, M3 parse_post_id overflow guard, M6 30s login deadline). 4 deferred to 0.8 v1-hardening (M1/M2 concurrent-accept, M4 anon board-create, L1 keyfile mode). 8 new regression tests (70 → 78); binary 375 → 377 KB (+0.6%). No new stdlib deps. **agora's input layer is now hardened against the obvious wire/CLI injection vectors; the next cycle (0.8) closes the memory + concurrency story.**
- **0.6.0** (2026-05-23) — M6 close: sigil-backed auth + per-board policy. 6 bites (M6-A ADR through M6-F policy) + 1 new ADR (0006 identity model). 21 new tests (49 → 70); binary 140 → 375 KB. **agora is a multi-board threaded BBS with Ed25519 challenge/response auth and operator-configurable per-board posting policy.** New CLI: `keygen` / `register` / `whoami`. New telnet commands: `login` / `whoami`. New stdlib deps: sigil + freelist + bigint + ct.
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
| **sigil** | M6 user accounts | 3.1.1 (bundled in cyrius 6.0.1 snapshot; standalone repo at 3.4.3 — we consume the bundled version) | ✅ — shipped in 0.6.0 (Ed25519 + SHA-256 + hex consumed) |
| **freelist / bigint / ct** | sigil call-chain for ed25519_verify | bundled in cyrius 6.0.1 | ✅ — added to stdlib deps at M6-C |
| **kii** | M3 inline-image posts | 1.0.0 | ✅ (deferred — no current consumer) |
| **sankoch** | M4 stored-file deltas | 2.2.6 | ✅ (deferred) |
| **agnos** ext4 WRITE | AGNOS-target storage (Linux works today) | agnos 1.32.2 in-flight | ❌ — not blocking, AGNOS is one target among many per ADR 0001 |

## Source surface

- `src/main.cyr` — argv dispatch + verb handlers + telnet `handle_client` + session helpers + login flow + CLI keygen/register/whoami + 0.7.0 audit gates (`cmd_post` --subject C0 filter, `cmd_list`/`cmd_read` --board validation, MODE_LOGIN_AWAIT_SIG 30s deadline) + **0.8.0 fork-per-accept in `cmd_serve_on`** (waitpid reaper, sys_fork, child handle_client + sys_exit, parent loops) (~1.66k LOC at 0.8.0)
- `src/telnet.cyr` — RFC 854 IAC parser + RFC 1143 Q-method + RFC 1184 LINEMODE state machine (unchanged since 0.2.0; audit confirmed bounds-clean against CVE-2020-10188 / CVE-2011-4862)
- `src/board.cyr` — post storage + headers + threading + flock + board layout + From-header param + per-board policy + 0.7.0 audit helpers (`header_text_ok` / `header_text_buf_ok` / `header_text_cstr_ok` / `fp16_valid`; `parse_post_id` 18-digit cap) (ADRs 0002/0003/0004/0005/0006)
- `src/account.cyr` — fingerprint + handle validation + per-user dir + keyfile + nonce / sig parse + From-header extractor + 0.7.0 audit re-validation tail in `post_from` (~510 LOC at 0.7.0)
- `src/test.cyr` — 78-test conformance suite (+8 audit regressions at 0.7.0)
- `benches/bench_telnet.bcyr` — 5-bench parser harness
- `lib/` — 20 stdlib modules (added sigil + freelist + bigint + ct at M6) + lib/darshana.cyr (pinned 0.5.3 git dep)

## Cross-references

- [`roadmap.md`](roadmap.md) — release plan, in-progress cycle, backlog.
- [`../doc-health.md`](../doc-health.md) — doc currency across the tree.
- [`../../CLAUDE.md`](../../CLAUDE.md) — durable rules / process / conventions.
- [`../../CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.
- [`roadmap-future.md`](roadmap-future.md) — v2.x sovereignty pillars (post-1.0, unpinned).
