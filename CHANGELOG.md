# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.8.0] — 2026-05-23 (concurrent accept — fork-per-connection)

agora becomes a **truly multi-user telnet BBS**. The accept loop now forks per connection ([ADR 0007](docs/adr/0007-fork-per-accept-concurrency.md)); each client runs in its own process with isolated identity slots, isolated session state, and kernel-managed memory cleanup at `sys_exit`. The two co-scheduled MEDIUM findings from the 0.7.0 audit — **M1** (bump-allocator memory growth in long-running serve) and **M2** (`g_login_*` slot collision under concurrent accept) — both close via process isolation: kernel reclaims per-child memory atomically at exit, and globals are per-process post-fork so two clients running `login` simultaneously cannot collide.

### Added

- **[ADR 0007 — Concurrent connections via fork-per-accept](docs/adr/0007-fork-per-accept-concurrency.md)** — decision rationale: rejects thread-per-accept (M2 only closes with shared-state refactor; concurrency bug surface), epoll event loop (forces every byte handler to be yield-aware), and single-track-with-arena (only closes half the audit). Picks fork because the kernel address-space boundary closes M1 + M2 simultaneously with the smallest source-level diff.

### Changed

- `cmd_serve_on` (`src/main.cyr`) is now fork-per-accept. Loop shape:
  1. Drain zombies via `sys_waitpid(-1, NULL, WNOHANG)` until it returns ≤ 0.
  2. `sock_accept` for the next client.
  3. `sys_fork`: child closes the listening fd and runs `handle_client(cfd)` + `sys_exit(0)`; parent closes the accepted cfd and continues.
- Per-connection state (`g_session_fp` / `g_session_handle` / `g_login_fp` / `g_login_nonce` / `g_login_started_ms` / `g_reply_*`) stays in globals — fork makes them per-process automatically; no struct refactor needed. This was a deliberate decision in ADR 0007 (smallest possible diff for the audit close).
- Banner / version literals bumped 0.7.0 → 0.8.0 in `print_banner`, `cmd_version`, `render_motd`.

### Verified

- **78/78 tests pass** from a clean `rm -rf build && cyrius deps && cyrius build`. No new tests for E itself — the change is in the accept loop, exercised end-to-end by smoke testing (see below).
- **Concurrent-accept smoke** (3 simultaneous sessions): each gets its own MOTD + banner + prompt + independent `whoami` (anonymous, no cross-session state). Test driver: `python3 /tmp/agora-concurrent-smoke.py 23456 3` against `./build/agora serve 23456`. 3/3 sessions OK.
- **Zombie reaper smoke**: round 1 of 3 connections leaves 3 zombies (`ps -eo ... ZN`); round 2 of 1 connection triggers the waitpid drain at top of accept loop, clearing all 3 round-1 zombies. Round 2's own child becomes the new pending zombie (reaped at next accept). Steady-state behavior matches ADR 0007's "drained at next iteration" model.
- Binary size 377,184 B (0.7.0) → 377,520 B (0.8.0), +336 B (+0.09%) for the fork wrapper + waitpid reaper loop. DCE same.
- 5 telnet-parser benchmarks unchanged from M1-close baseline — fork happens before any IAC byte flows, so the parser hot path is unaffected.

### Security

- **Audit M1 closed** (bump-allocator memory growth). Each connection's bump-allocated memory is reclaimed atomically by the kernel at child `sys_exit`. The parent's per-loop allocations (Result wrappers from `sock_accept`) are minimal and bounded by the accept rate.
- **Audit M2 closed** (login-challenge slot collision). Post-fork, every child has its own copy of `g_login_*` / `g_session_*` / `g_login_started_ms` via the kernel's address-space isolation. Two clients running `login alice` and `login bob` simultaneously cannot poison each other's parked challenge.
- **Audit M4 NOT closed** (anonymous `enter` can spam-create boards). Independent of the concurrency model; explicit auth gate or accept-loop rate limit needed. Carried forward to 0.8.x patches.

### Operator notes

- Run `agora serve` under a process supervisor (systemd, runit, supervisord) so the parent crash kills all children. Standard for any forking server; called out explicitly because the v0.7.x single-track model didn't surface this concern.
- Zombies persist between accept iterations — visible as `ZN` rows in `ps` against the parent's PID. This is expected: the waitpid reaper runs at the top of each accept loop iteration. On a busy server, zombies are drained within ms of each new connection. On an idle server, zombies wait until the next connection arrives. Not a leak; bounded by N children since last accept.

## [0.7.0] — 2026-05-23 (pre-1.0 security sweep)

agora's first dedicated security audit cycle per CLAUDE.md "Security Hardening" and the roadmap release plan. Full line-by-line read of the IAC parser (`src/telnet.cyr`), post storage + ingress (`src/board.cyr`), M6 auth surface (`src/account.cyr`), and the wire dispatch in `src/main.cyr`, against the CLAUDE.md security checklist + external CVE history (CVE-2020-10188 telnetd IAC overflow, CVE-2011-4862 telnetd AUTHENTICATION overflow). Full findings in [`docs/audit/2026-05-23-audit.md`](docs/audit/2026-05-23-audit.md).

**No CRITICAL findings.** The bounded IAC buffers, fresh single-use nonces over `/dev/urandom`, and per-board flock + `O_EXCL` claim path all held up. **5 actionable findings** landed as fixes this cycle (3 HIGH, 2 MEDIUM); 4 deferred to 0.8 v1-hardening (concurrent-accept refactor + per-conn memory arenas, accept-loop rate-limit / `enter` auth gate, keyfile mode warn-on-load, sigil 3.1.1 → 3.4.3 release-notes diff read).

### Security — fixed this cycle

- **H1 — CLI subject CRLF injection** (`cmd_post`). `--subject $'foo\r\nReply-To: 42'` previously wrote forged headers into the stored post, parsed as real headers by `post_reply_to` / `post_from` on every subsequent read. New helpers `header_text_ok` / `header_text_buf_ok` / `header_text_cstr_ok` in `src/board.cyr` reject CR/LF/NUL/ESC and other C0 control bytes (except TAB) from header-context values; `cmd_post` calls the validator at entry.
- **H2 — `cmd_list` + `cmd_read` accept path-traversal `--board`** (`src/main.cyr`). `--board "../../etc"` previously resolved through `board_path` to a parent-of-store directory. Now both verbs run `board_name_valid` whenever `board != "main"`, mirroring `cmd_post`'s existing check.
- **H3 — `post_from` does not re-validate handle / fp on read** (`src/account.cyr`). A tampered `.users/<fp>/handle` file (operator-side or a future federated-import path) could smuggle ESC sequences into every reader's terminal via the `send_buf(cfd, hbuf, strlen(hbuf))` render path. `post_from` now re-runs `handle_valid` on the extracted handle and a new `fp16_valid` helper on the extracted fingerprint; invalid → return 0 / clear outputs / render as anonymous.
- **M3 — `parse_post_id` digit-prefix overflow** (`src/board.cyr`). `n = n * 10 + (c - 48)` on a 19+ digit filename overflows i64. Now capped at 18 digits (i64 holds 18 full digits at 9.22e18) — anything longer is rejected as not-a-post-id.
- **M6 — explicit 30 s deadline on parked login challenge** (`src/main.cyr` MODE_LOGIN_AWAIT_SIG). M6-C deferred this; relied on `RECV_TIMEOUT_SECS = 60` idle drop, which a heartbeat-sending client can defeat. New `g_login_started_ms` + `LOGIN_DEADLINE_MS = 30000` enforce the ADR 0006 § Specifics deadline at the top of the auth-line dispatch — uses `clock_now_ms()` from `lib/chrono.cyr`.

### Security — deferred to 0.8 v1-hardening

- **M1 — bump-allocator memory growth in long-running serve.** `alloc()` is bump-only; each connection accretes ~73 KB and each `read` adds ~100 KB. Will rework in the concurrent-accept refactor (per-connection arenas freed at `sock_close`).
- **M2 — `g_login_*` slots become per-connection** at the same refactor (today's single-tracking accept loop makes them de facto per-session).
- **M4 — anonymous `enter` can auto-create boards** (storage exhaustion vector). Fix: require auth for board creation OR add accept-loop rate limiting.
- **L1 — `keyfile_load_seed` does not warn on world-readable mode.** Defense-in-depth `fstat` check at load time.

### Verified

- **78/78 tests pass** from a clean `rm -rf build && cyrius deps && cyrius build` (+8 regression tests for the 5 fixes: t71 header_text_ok control-byte filter, t72 header_text_buf_ok CRLF injection scan, t73 fp16_valid accepts, t74 fp16_valid rejects, t75 post_from rejects invalid handle, t76 post_from rejects invalid fp, t77 parse_post_id 19+ digit overflow guard, t78 parse_post_id 18-digit ceiling).
- **End-to-end smoke** for each HIGH fix: `agora post --subject $'foo\r\nReply-To: 1'` exits 2 with the C0-control error; `agora list --board "../../etc"` exits 2 with the invalid-name error; `agora read 1 --board "../../tmp"` exits 2 with the invalid-name error.
- Binary size 374,968 B (0.6.0) → 377,184 B (0.7.0), +2,216 B (+0.6%) for the validator helpers + login-deadline check + test surface. DCE same.
- 5 telnet-parser benchmarks unchanged from M1-close baseline (security patches don't touch the parser hot path).
- `cyrius audit` clean.

### Changed

- `VERSION` bumped 0.6.0 → 0.7.0.
- `print_banner` / `cmd_version` / `render_motd` version literals bumped to 0.7.0 in lockstep.
- `src/board.cyr` grew `header_text_ok` / `header_text_buf_ok` / `header_text_cstr_ok` / `fp16_valid` (4 helpers, ~40 LOC); `parse_post_id` grew the 18-digit cap.
- `src/account.cyr` `post_from` grew the re-validate tail (handle_valid + fp16_valid; on fail → clear outputs + return 0).
- `src/main.cyr` `cmd_post` grew the `--subject` C0-control gate; `cmd_list` + `cmd_read` grew the `--board` validation; new globals `g_login_started_ms` + `AgoraLogin.LOGIN_DEADLINE_MS`; `login` command sets the timestamp; MODE_LOGIN_AWAIT_SIG dispatch checks the deadline before signature work.
- `src/test.cyr` grew 8 regression tests (t71-t78).

### Documentation

- New `docs/audit/2026-05-23-audit.md` — full audit report. Severity rubric (CRITICAL/HIGH/MEDIUM/LOW/DOCUMENTED), per-finding repro/fix, external CVE review table, 0.7.x fix slate, 0.8 deferred items. First entry in the `docs/audit/` ledger; cadence per CLAUDE.md § Security Hardening = once per minor / pre-release.

## [0.6.0] — 2026-05-23 (M6 close — sigil-backed auth + per-board policy)

agora is now a **multi-board threaded BBS with sigil-backed identity and operator-configurable per-board posting policy**. The full M6 cycle ships: six bites + one ADR landed between 0.5.0 and 0.6.0. Authenticated users can post under their handle (with a `From: <handle> <fp16>` header on disk); anonymous users can still read freely but cannot post (default policy `open` still requires auth); operators can tighten any board to `known` (registered-users-only) or `admin` (handles listed in `<board>/.admins` only).

### Bites + ADR in this release

- **M6-A** + [ADR 0006](docs/adr/0006-identity-model.md) — identity model: sigil Ed25519, `<store>/.users/<fp16>/` per-user dir, challenge/response wire flow (`"agora-login:" + nonce_hex` signed payload), anon-read + auth-post default, `From: <handle> <fp16>` header, 32-byte raw seed keyfile at `~/.agora/key`.
- **M6-B** — account primitives in `src/account.cyr` (~230 LOC): fingerprint computation, handle validation, path builders, `account_register` / `account_lookup_*` / `account_resolve_handle`.
- **M6-C** — telnet `login <handle>` + `MODE_LOGIN_AWAIT_SIG` + challenge/response wire flow + `parse_auth_sig` / `format_challenge_msg` / `nonce_random` / `nonce_to_hex` helpers.
- **M6-D** — `agora keygen` / `agora register` / `agora whoami` CLI verbs + telnet `whoami` command + keyfile primitives (`keyfile_generate` / `keyfile_load_seed` / `seed_to_pk` / `keyfile_to_fingerprint`).
- **M6-E** — `From:` header on authenticated posts; CLI `--as <handle>`; wire-side auth-post gate; `post_from` extractor; `list` and `read` rendering across CLI + telnet show `[handle|anon]` / `From:` lines.
- **M6-F** — per-board posting policy via `<store>/<board>/.policy` (`open` / `known` / `admin`) + `<store>/<board>/.admins`; `BoardPolicy` enum + `board_policy_get` / `board_admin_check` / `board_can_post` decision-point primitive.

### Changed

- `VERSION` bumped 0.5.0 → 0.6.0.
- `print_banner` / `cmd_version` / `render_motd` version line all bumped to 0.6.0 (CI's drift check verifies the inline literals match `VERSION`).
- `cyrius.cyml [deps].stdlib` grew **three modules**: `sigil` (Ed25519 / SHA-256 / hex), `freelist` (sigil's heap-context primitives), `bigint` + `ct` (sigil's Ed25519 verify call chain needs the u256 + constant-time primitives — would SIGILL at runtime without them). 16 modules at 0.5.0 → 20 at 0.6.0.
- `post_format_with_headers` signature grew `from_handle` + `from_fp` params (8 args at 0.6.0; was 6 at 0.5.0). `post_new_with_subject_reply` likewise grew the two params. Backwards-compat wrappers (`post_format_with_subject`, `post_new_with_subject`) pass 0/0 for both.
- New session modes / globals in `src/main.cyr`: `MODE_LOGIN_AWAIT_SIG = 3`, `g_session_fp`, `g_session_handle`, `g_login_fp`, `g_login_nonce`.

### Verified

- **70/70 tests pass** from a clean `rm -rf build && cyrius deps && cyrius build` (was 49 at 0.5.0; +21 tests for M6-B/C/D/E/F: fingerprint, handle validation, path builders, nonce/hex helpers, auth-sig parser, RFC 8032 test-vector-1, From-header round-trip, policy paths, anonymous-deny early-return).
- **Bench baseline unchanged** (parser hot path is content-agnostic — M6 is application-layer):
  | Benchmark | 0.5.0 | 0.6.0 |
  |---|---:|---:|
  | `telnet/plain_byte` | 10–11 ns | **10 ns** |
  | `telnet/iac_untracked` | 63 ns | **64 ns** |
  | `telnet/iac_tracked_agree` | 73 ns | **74 ns** |
  | `telnet/subneg_naws` | 97–107 ns | **99 ns** |
  | `telnet/announce_salvo` | 132 ns | **132 ns** |
- **Security re-scan** (M6 surfaces, per CLAUDE.md Security Hardening §1-7):
  - **No `sys_system`** — zero command-injection surface.
  - **Buffer sizes**: all M6 `var buf[N]` allocations match their fill size (32 for pk/seed/digest, 64 for sig, 24 for fmt_int_buf, 76 for the LOGIN_MSG_LEN message, etc.).
  - **Path resolution**: every path constructed via builders (`build_user_dir`, `build_user_file`, `board_policy_path`, `board_admins_path`) whose user-controlled tokens (`handle`, `board`) are pre-validated by `handle_valid` / `board_name_valid` at ingress. Fingerprints are derived from `sha256(pk)` and always-16-lowercase-hex by construction. File-name component is always a hard-coded literal.
  - **Sig hex validated**: `hex_is_valid` + length check before `hex_decode` in `parse_auth_sig`. Malformed bytes → `login failed (malformed auth)`.
  - **Keyfile**: `O_CREAT | O_EXCL` (refuses to overwrite existing) + mode 0o600 at creation. Server holds only public keys; secret material never crosses the wire.
  - **Domain-separated signing input**: `"agora-login:"` prefix prevents the sigil keypair being tricked into signing payloads for other protocols.
  - **Single-use nonces**: cleared on every `auth:` attempt (pass or fail), preventing replay.
- **Dead-code audit**: DCE NOPs **675 unreachable fns** (~160 KB) — entirely sigil's PQC / keccak / hashmap_fast / thread paths we never call. None of agora's own code is unreachable from the entry points.
- **Full clean rebuild** (`rm -rf build && cyrius deps && cyrius build`) passes clean.
- **Version verify**: `VERSION` = `cat VERSION` = `./build/agora --version | head -1` = intended git tag `0.6.0` (manual; CI's drift-check workflow enforces this).
- **End-to-end smoke** across every M6 bite — see per-bite entries below for the verified scenarios (keygen + register + login + post + reply + whoami + policy enforcement, both CLI and telnet sides, openssl 3.x ↔ sigil 3.1.1 Ed25519 interop confirmed).

### Binary growth

| Tag | Size | Cycle |
|---|---:|---|
| 0.1.0 | 43 KB | M0 scaffold |
| 0.2.0 | 71 KB | M1 close |
| 0.3.0 | 86 KB | M2 close |
| 0.4.0 | 129 KB | M5 partial |
| 0.5.0 | 140 KB | M5 close |
| **0.6.0** | **375 KB** | **M6 close** |

+235 KB across the M6 cycle. ~165 KB of that is sigil's unreachable PQC / keccak / hashmap_fast / thread surface (NOPed under DCE); the actual M6 code adds ~70 KB across `src/account.cyr` (~280 LOC including login + keyfile + From helpers + policy primitives) and the wire/CLI integration in `src/main.cyr`. Real binary strip remains a v1.x close-out concern per state.md.

### Added — M6-F: per-board posting policy (`open` / `known` / `admin`) (2026-05-23)

- **New on-disk policy files** per ADR 0006 § Specifics:
  - **`<store>/<board>/.policy`** — one of literal `open` / `known` / `admin` (trailing CR/LF/whitespace tolerated). Missing file defaults to `open`. `<store>/.policy` for the main board.
  - **`<store>/<board>/.admins`** — one handle per line; blank lines and `#`-comment lines ignored; leading + trailing whitespace trimmed per line. Only consulted when `.policy == admin`.
  - Operator sets both by editing the files directly (`echo known > <store>/<board>/.policy`). No CLI verb at first cut; a future bite earns `agora policy set <board> <mode>` if real deployments demand it.
- **New primitives in `src/board.cyr`** (~150 LOC):
  - `BoardPolicy` enum: `POLICY_OPEN = 0`, `POLICY_KNOWN = 1`, `POLICY_ADMIN = 2`.
  - `board_policy_path(store, board, out)` / `board_admins_path(store, board, out)` — path builders mirroring the `board_path` + dotfile-suffix shape (precedent: `.lock`, `.users/`).
  - `board_policy_get(store, board)` — reads `.policy`, trims trailing whitespace, parses one of `open` / `known` / `admin`. Missing / unparseable → `POLICY_OPEN`.
  - `board_admin_check(store, board, handle)` — reads `.admins` (up to 4 KB), scans line-by-line, trims per-line whitespace, skips blank + `#`-comment lines, returns 1 if `handle` matches any entry. Up to 4 KB of `.admins` = ~120 handles of typical length; lift the ceiling when a deployment hits it.
  - `board_can_post(store, board, session_fp, session_handle)` — single decision point. Anonymous (NUL / empty `session_fp`) always denied. `open` allows any auth. `known` re-verifies the fingerprint via `account_lookup_pubkey` (guards against stale sessions whose user was unregistered out-of-band). `admin` requires non-empty handle in `.admins`.
- **`open` vs `known` at M6** are functionally identical (every authenticated session at M6 has a locally-registered handle — `login` resolves through `<store>/.users/`). The distinction is forward-compat for federation (v2.x pillar 1): `open` would also accept federated identities not registered locally.
- **Wire-side enforcement** in `session_execute`: `post` / `reply` commands replace the bare `g_session_fp` check with `board_can_post(...)`. Policy-aware error messages — `auth required — run 'login <handle>' first` for anonymous, `post denied by board policy (admin-only or unregistered)` for authenticated-but-denied.
- **CLI enforcement** in `cmd_post`: same `board_can_post(...)` gate using `--as`-derived identity (or 0/0 for anonymous CLI posts). Anonymous CLI posts continue to work on `open`-policy boards (default = `open` = backwards-compat with 0.5.x); tightening the operator surface is what policy is for.
- **Tests grew 66 → 70**: `t67_board_policy_path_main` / `t68_board_policy_path_named` / `t69_board_admins_path_named` (path builders verbatim with NUL terminators), `t70_can_post_anonymous_denied` (NUL ptr + empty cstring both reject without touching the filesystem — early-return correctness check).
- **End-to-end smoke** (7 cases, 2 keypairs alice/bob in one store with `main` open / `closed` known / `ops` admin-with-alice-only):
  1. alice → main (open) → allow.
  2. bob → closed (known) → allow (bob registered).
  3. bob → ops (admin, not listed) → DENY ("denies this post").
  4. alice → ops (admin, listed) → allow.
  5. Anonymous CLI → closed (known) → DENY ("requires authentication").
  6. Tighten main to admin with no .admins file → even alice DENY (no one is admin).
  7. Wire-side: bob logged in via challenge/response, enters ops, tries `post` → `post denied by board policy (admin-only or unregistered)`. **PASS.**
- **Binary growth**: 370,528 B (M6-E) → final M6 size (see closeout).
- **Backwards compat**: existing 0.5.x stores with no `.policy` files behave exactly as before (default `open`). Operators upgrade in place with zero data migration; tightening is opt-in per-board.

### Added — M6-E: `From:` header on posts + CLI `--as` + auth-post gate (2026-05-23)

- **`post_format_with_headers` signature grew** `from_handle` + `from_fp` parameters (both cstrings; either-null = no header / anonymous post). Worst-case header overhead bumped to ~140 bytes accounting for the `From: <32-byte-handle> <16-hex-fp>\r\n` line. `post_new_with_subject_reply` got the same two new params; `post_format_with_subject` and `post_new_with_subject` wrappers pass 0/0 for both. Per ADR 0006 § Specifics — `From: <handle> <space> <fp16-hex>` two-token format.
- **New helper `post_from(buf, len, handle_out, h_max, fp_out, fp_max)`** in `src/account.cyr` — extracts `From:` value, splits on first space, NUL-terminates handle + fp into caller buffers. Returns 1 on success, 0 if no From header / malformed (no space) — caller renders "[anon]" / "anonymous".
- **Wire-side auth gate**: `post` and `reply` commands in `session_execute` check `g_session_fp`; if anonymous, reply `auth required — run 'login <handle>' first\r\n` and stay in `MODE_COMMAND`. ADR 0006 § P1 default-policy fulfillment.
- **`session_finalize_post` reads `g_session_handle` + `g_session_fp`** when the session is authenticated, passes them through to `post_new_with_subject_reply`. Anonymous sessions can't reach this path (auth gate above) but the function still tolerates 0/0 for backward-compat with future CLI-driven flows.
- **CLI `agora post --as <handle> [--key <path>]`** — when `--as` is given, the CLI loads the keyfile (default `~/.agora/key`), derives the fingerprint via `keyfile_to_fingerprint`, looks up the handle in the store (`account_resolve_handle`), and refuses if the handle isn't registered or is registered to a different fingerprint. Anonymous CLI posts (no `--as`) keep the 0.5.x shape — no `From:` header on disk.
- **`list` rendering** (CLI + telnet) updated to `<id>  [<handle>]  <subject>` — `[anon]` for posts with no `From:` header (legacy 0.4/0.5 posts + anonymous new posts).
- **`read <id>` rendering** (CLI + telnet) prepends `From: <handle> <fp16>\r\n` (or `From: anonymous\r\n` when no header) before the existing `Subject:` line.
- **New CLI helper `parse_as_flag`** mirrors the `--store` / `--subject` / `--key` / `--handle` parsers. `first_positional_after_verb` already skips any `--*` pair generically, so the new flag doesn't shadow `read <id>`.
- **Tests grew 63 → 66**: `t64_format_with_from_header` (formatter writes the literal `From: alice deadbeef12345678` line), `t65_post_from_extracts` (round-trip: format with handle+fp → parse handle+fp out), `t66_post_from_absent_is_anonymous` (no-header case zeroes both out buffers + returns 0).
- **Test fix**: `t49_format_with_reply_to_header` updated for the new 8-param signature of `post_format_with_headers` (passes 0,0 for from_handle/from_fp). t49 was crashing with SIGSEGV on the old 6-arg call site before the fix — caught by the test suite before the bite was claimed done.
- **End-to-end smoke** (8 cases): keygen + register `alice` → CLI anon post (id 1, no `From:` on disk) → CLI `--as alice --key …` post (id 2, `From: alice 8a708167937a0a86` on disk) → CLI `--as bob` rejected (`handle is not registered`) → `list` shows `1  [anon]  anon post` / `2  [alice]  alice post` → `read 1` shows `From: anonymous` → `read 2` shows `From: alice 8a708167937a0a86` → telnet anonymous-session `post` blocked with `auth required — run 'login <handle>' first`. **PASS.**
- **Binary growth**: 366,080 B (M6-D) → 370,528 B (this bite, +4.4 KB).
- **Backwards compat**: existing 0.4 / 0.5 posts and 0.5/0.4 stores transparent — missing `From:` continues to mean anonymous; `list` shows `[anon]` and `read` shows `From: anonymous` exactly as if the post were freshly anonymous. No data migration.

### Added — M6-D: keygen / register / whoami (CLI + telnet) (2026-05-23)

- **New CLI verbs**:
  - **`agora keygen [--key <path>]`** — generates a fresh 32-byte Ed25519 seed via `/dev/urandom`, writes to `<path>` (default `$HOME/.agora/key`, fallback `./agora.key`) with `O_CREAT | O_EXCL` and mode `0o600`. Refuses to overwrite. Auto-mkdir's the parent (`ensure_parent_dir`). Prints `wrote keyfile <path> (fp <fp16>)`.
  - **`agora register --handle <h> [--key <path>] [--store <path>]`** — loads the keyfile seed, derives the pubkey via `seed_to_pk` (sigil `ed25519_keypair`), validates the handle (lowercase + digit alphabet, 1-32 bytes, not `anonymous`/`system`/`admin`), checks via `account_resolve_handle` that the handle isn't squatted by a different fingerprint (idempotent re-register OK if same fp), then `account_register`. Prints `registered <handle> <fp16>`.
  - **`agora whoami [--key <path>] [--store <path>]`** — decodes the keyfile, derives the fingerprint, optionally looks up the handle in `<store>`. Prints `<handle?> <fp16>` (handle omitted when no `--store` or no registration). Returns 1 if the keyfile cannot be read.
- **New telnet command** `whoami` in `session_execute` — prints `<handle> <fp16>` for an authenticated session, or `anonymous` for an unauthenticated one. Help text updated.
- **New account-side primitives in `src/account.cyr`**:
  - `keyfile_load_seed(path, seed_out)` — reads exactly 32 bytes; -1 on missing / wrong-size / read error.
  - `seed_to_pk(seed_buf, pk_out)` — wraps sigil's `ed25519_keypair`, writes only the 32-byte pubkey (caller doesn't usually need the sk).
  - `keyfile_to_fingerprint(path, fp_out)` — convenience: keyfile path → 16-hex fingerprint.
  - `keyfile_generate(path)` — `nonce_random_into` → 32-byte seed → `O_WRONLY|O_CREAT|O_EXCL` write with mode `0o600`. Refuses to overwrite existing files.
  - `nonce_random_into(out, want)` — generalized `/dev/urandom` reader; `nonce_random` now wraps this with `want = ACCOUNT_NONCE_BYTES`.
- **New constants** in `AccountCap` / `AccountLogin` / etc.: `ACCOUNT_PERM_KEYFILE = 0x180` (0o600).
- **ADR 0006 update** — keyfile format clarified to **32 bytes (raw seed)** instead of the original "96 bytes — seed || sk" sketch. sk is derived on load via `ed25519_keypair`; the seed is the minimum canonical form (also what `ssh-keygen -t ed25519` stores internally). Backwards-compat note added.
- **Tests grew 61 → 63**: `t62_seed_to_pk_rfc8032_v1` (RFC 8032 test-vector-1: seed `9d61b19d…7f60` → pubkey `d75a9801…511a`), `t63_fingerprint_of_rfc8032_v1_pk` (fp = `21fe31dfa154a261`). Added inline `t_hex2` / `t_hex_load` helpers so test files can carry hex-literal vectors without depending on `hex_decode`.
- **End-to-end smoke** — 8 CLI cases + 3 telnet whoami cases:
  1. `keygen` writes a 32-byte file mode 0600.
  2. `keygen` again refuses to overwrite (rc 1).
  3. `whoami --key <path>` (no `--store`) prints just the fingerprint.
  4. `register --handle alice --store /tmp/m6d_store` writes `.users/<fp>/` with all three files.
  5. `whoami --key <path> --store /tmp/m6d_store` prints `alice <fp>`.
  6. `register` again with same key+handle is idempotent (rc 0, same fp).
  7. `register --handle Bad-Caps` rejected (rc 2, invalid).
  8. `register --handle admin` rejected (rc 2, reserved).
  9. Telnet `whoami` from anonymous session → `anonymous\r\n`.
  10. `login alice` + auth round-trip (re-using openssl pkeyutl pipeline from M6-C, with the 32-byte seed wrapped in the standard Ed25519 PrivateKeyInfo DER prefix to feed openssl: `30 2e 02 01 00 30 05 06 03 2b 65 70 04 22 04 20 || seed`) → `welcome, alice`.
  11. Telnet `whoami` post-login → `alice <fp16>\r\n`. **PASS.**
- **Binary growth**: 351,248 B (M6-C) → 366,080 B (this bite, +14.8 KB for the three new CLI verbs + helpers + getenv path).
- **`default_key_path` honors `$HOME`** via `lib/io.cyr`'s `getenv` (reads `/proc/self/environ`); falls back to `./agora.key` if unset. Operators on macOS / non-Linux platforms with HOME set still resolve via the standard fallback once `getenv` lands on those platforms.

### Added — M6-C: telnet `login` + challenge/response wire flow (2026-05-23)

- **New session mode `MODE_LOGIN_AWAIT_SIG = 3`** in `src/main.cyr` — parked-challenge state between `login <handle>` and the client's `auth: <hex>` reply.
- **Per-session globals**: `g_session_fp` / `g_session_handle` (bound identity, empty cstring = anonymous); `g_login_fp` / `g_login_nonce` (parked challenge state, cleared on every auth attempt + session start). Allocated per-connection in `handle_client`, mirrors the single-tracking caveat documented on `g_reply_to`.
- **`login <handle>` command** in `session_execute`:
  - Resolve `<handle>` → fingerprint via `account_resolve_handle` (M6-B). Unknown handle → "unknown user", session stays anonymous.
  - Generate 32-byte random nonce via `/dev/urandom` (`nonce_random` in account.cyr).
  - Hex-encode nonce (`nonce_to_hex`); send `challenge: <64-hex>\r\n` + reply-format hint.
  - Park `(fp, nonce_hex)` in `g_login_fp` / `g_login_nonce`; return `MODE_LOGIN_AWAIT_SIG`.
- **`MODE_LOGIN_AWAIT_SIG` branch in `handle_client`** (eol-dispatch chain):
  - `parse_auth_sig(line, line_pos, sig_raw)` extracts 64-byte sig from `auth: <128-hex>` (tolerates the optional single space after colon).
  - `account_lookup_pubkey(store, g_login_fp, pk_buf)` fetches the 32-byte registered pubkey.
  - `format_challenge_msg(g_login_nonce, msg)` writes the 76-byte signed payload (`"agora-login:" + nonce_hex`, ADR 0006's domain-separation prefix).
  - `ed25519_verify(pk, msg, 76, sig)` decides pass/fail.
  - Pass: bind `g_session_fp` + `g_session_handle` from the parked fp + lookup, send `welcome, <handle>`, return to `MODE_COMMAND`.
  - Fail (malformed auth / pubkey lookup error / signature mismatch): clear parked state, send specific failure message, return to `MODE_COMMAND` anonymous.
  - **Single-use nonce**: `g_login_nonce` cleared on every auth attempt, pass or fail.
- **New account-side primitives in `src/account.cyr`**:
  - `nonce_random(out_buf)` — 32 bytes from `/dev/urandom` (entropy failure returns -1, mirrors sigil's `generate_keypair` shape).
  - `nonce_to_hex(in_buf, out_buf)` — 32 raw bytes → 64 hex chars + NUL.
  - `format_challenge_msg(nonce_hex, out_buf)` — `"agora-login:" + nonce_hex` (76 bytes, NOT NUL-terminated; caller passes length to `ed25519_*`).
  - `parse_auth_sig(line, line_len, sig_out)` — validates `auth:` prefix + optional space + exact 128-hex chars + hex-decode; returns 64 on success, -1 on malformed.
  - New constants: `LOGIN_PREFIX_LEN = 12`, `LOGIN_MSG_LEN = 76`.
- **`cyrius.cyml [deps].stdlib`** — added `bigint` + `ct` (sigil's Ed25519 verify needs the u256 + constant-time primitives from bigint/ct.cyr; without them the verify call hit unimplemented-function SIGILL at runtime). 18 modules at M6-B → 20 at this bite.
- **Tests grew 56 → 61**: `t57_nonce_to_hex_known` (input bytes 0x00..0x1F → expected hex), `t58_format_challenge_msg` (prefix + nonce tail), `t59_parse_auth_sig_valid` (128-hex round-trip), `t60_parse_auth_sig_rejects` (NUL ptr / empty / too short / wrong prefix / 127 hex / non-hex char), `t61_parse_auth_sig_no_space` (tolerates `auth:00...` without space).
- **End-to-end smoke (CLI + openssl + python)**:
  1. `openssl genpkey -algorithm ed25519` → 32-byte raw pubkey extracted from DER output.
  2. Fingerprint = `sha256(pk)[:8]` hex; pre-registered `<store>/.users/<fp>/{public_key.bin, handle, created.iso8601}`.
  3. Connect → `login alice` → server emits `challenge: <64-hex>\r\n`.
  4. Client signs `"agora-login:" + nonce_hex` via `openssl pkeyutl -sign -rawin`.
  5. Send `auth: <128-hex>\r\n` → server replies `welcome, alice\r\n> `. **PASS.**
  - Failure paths verified: `login nobody` → `unknown user`; `auth: <128-hex of wrong sig>` → `login failed (signature)`.
- **Sigil interop**: openssl 3.x's pure-Ed25519 sign output (`-rawin`) verifies cleanly with sigil's `ed25519_verify` — confirms both implement RFC 8032 PureEdDSA correctly.
- **Help text** updated to document `login <handle>`.
- **Binary growth**: 332,552 B (M6-B) → 351,248 B (this bite). +18.6 KB for the login dispatch path + bigint/ct surface that sigil's ed25519_verify call chain pulls in.
- **Deferred to a polish follow-up**: 30 s deadline on the parked challenge. Today's `sock_set_recv_timeout(60s)` slowloris defense kills idle sockets, which incidentally drops any stale parked nonce — the explicit deadline is hardening, not correctness.

### Added — M6-B: account primitives in `src/account.cyr` (2026-05-23)

- **`src/account.cyr`** (~230 LOC) — per-user identity primitives per ADR 0006:
  - `compute_fingerprint(pk_buf, out_buf)` — `hex(sha256(pk))[0:16]` via sigil's `sha256` + inline hex encoder. Writes 16 lowercase hex chars + NUL.
  - `handle_valid(name)` — same alphabet as `board_name_valid` (lowercase ASCII / digits / `-` / `_`, first char letter or digit, 1-32 bytes) but different reserved set (`anonymous`, `system`, `admin`).
  - `build_users_dir(store, out_buf)` / `build_user_dir(store, fp16, out_buf)` / `build_user_file(store, fp16, file_name, out_buf)` — path builders mirroring `board_path` / `build_post_path` shape.
  - `account_dir_ensure(store, fp16)` — mkdir `<store>` + `<store>/.users` + `<store>/.users/<fp16>` (EEXIST as success at every level).
  - `account_register(store, pk_buf, handle, fp_out)` — writes `public_key.bin` (32 bytes raw) + `handle` (UTF-8 + LF) + `created.iso8601` (chrono now + LF). Computes fp from pk; caller pre-checks handle uniqueness via `account_resolve_handle`.
  - `account_lookup_pubkey(store, fp16, pk_out)` — reads `public_key.bin` into pk_out.
  - `account_lookup_handle(store, fp16, out_buf, out_max)` — reads `handle` file, strips trailing CR/LF (flag-driven trim per CLAUDE.md no-`break`-with-`var` rule), NUL-terminates.
  - `account_resolve_handle(store, handle, fp_out)` — O(n) scan of `<store>/.users/`, returns 1 + writes fingerprint on match, 0 on not-found. Same scan-on-read shape as `replies_to` (ADR 0005).
- **`cyrius.cyml [deps].stdlib`** — added `sigil` (bundled 3.1.1 from the cyrius 6.0.1 snapshot; ed25519 + sha256 + hex are the surface we consume) and `freelist` (`fl_alloc` / `fl_free` are sigil's `sha256_init` / `sha256_finalize` heap-ctx primitives). 16 modules at 0.5.0 → 18 at this bite.
- **Tests grew 49 → 56**: `t50_compute_fingerprint_known_pk` (sha256(zeros32) prefix == `66687aadf862bd77`), `t51_compute_fingerprint_deterministic` (two calls on same pk match), `t52_handle_valid_accepts` (canonical alphabet incl. 32-char ceiling), `t53_handle_valid_rejects` (NUL ptr, empty, reserved set, uppercase, dot, slash, leading dash/underscore, space, 33-char overflow), `t54_build_users_dir_shape` / `t55_build_user_dir_shape` / `t56_build_user_file_shape` (path formats verbatim with NUL terminators).
- **Note on bundled sigil version**: state.md cited sigil 3.4.3 (the standalone repo's tip) as the gate target; the cyrius 6.0.1 toolchain snapshot bundles 3.1.1, which provides the same Ed25519 + SHA-256 + hex surface we need for M6. Updated state.md gate row to reflect the bundled version.
- **Binary growth**: `build/agora` 140,160 B (0.5.0) → 332,552 B (this bite). +192 KB for sigil + freelist; ~165 KB of that is unreachable-but-NOPed (PQC / keccak / hashmap_fast / thread paths sigil declares but we never call). Real binary strip is a v1.x close-out concern per state.md. Net cost for actually-used code: ~27 KB for ed25519 + sha256 + hex + account.cyr.
- **Sigil-imported warnings**: build emits ~25 "undefined function" warnings for sigil's PQC + keccak + hashmap_fast + thread call sites; all are unreachable from the agora-side call graph (ed25519_sign / ed25519_verify / sha256 / hex_encode are the only sigil entry points we invoke). Documented here so future bites don't re-investigate.

### Added — M6-A: ADR 0006 — identity model (2026-05-23)

- **[ADR 0006](docs/adr/0006-identity-model.md)** — opens the M6 cycle. Captures six load-bearing decisions: (A) sigil Ed25519 as the identity primitive; (X) `<store>/.users/<fp16>/` per-user directory (public_key.bin + handle + created.iso8601); (p) challenge/response wire flow (server emits 32-byte nonce, client signs `"agora-login:" + nonce_hex`, server verifies via `ed25519_verify` against the registered pubkey); (P1) anon-read + auth-post default; `From: <handle> <fp16>` header on authenticated posts (missing From == anonymous, backwards-compat with M5 posts); CLI gains `agora whoami` + `agora keygen` + `agora register` + `agora post --as` with `~/.agora/key` as the default keyfile location.
- Rejects five alternatives with concrete reasoning: ML-DSA-65 at first cut (gated behind `-D SIGIL_PQC`, 1.2 KB sigs), password hashes (cleartext-on-wire over telnet has no defensible flow), fully sigil-managed account store (per-deployment user lists scatter across home dirs), `users.cyml` sidecar (two-file invariant — anti-pattern rejected at every prior ADR layer), federated identity at M6 (v2.x pillar 1, requires content-addressing graduation to be coherent).
- Fingerprint: `hex(sha256(public_key))[0:16]` — 64 bits, comfortable at ~10s of users per deployment; lengthening to 32 hex chars is a non-breaking forward-compatible change if a future deployment needs it.
- Per-board posting policy ships in M6-F: per-board `.policy` file (one of `open` / `known` / `admin`), per-board `.admins` for the admin mode. Missing `.policy` defaults to `open` (any authenticated user can post).
- No code in this bite — ADR-only. Subsequent bites (M6-B through M6-F) implement the decisions.

## [0.5.0] — 2026-05-23 (M5 close — boards + threads)

agora is now a **multi-board threaded BBS over telnet**. The full M5 cycle ships: six bites + four ADRs landed between 0.4.0 and 0.5.0. Single-board posting (0.4.0) becomes multi-board threaded conversation (0.5.0) without any user-visible data migration — the 0.4.0 flat-root layout is the implicit "main" board.

### Bites + ADRs in this release

- **M5-E (boards)** + [ADR 0004](docs/adr/0004-board-layout.md) — flat-root = "main", subdirs = named. Telnet `boards` / `enter <name>` / `leave` + CLI `--board <name>`. Per-board ID counter + lockfile.
- **M5-F (threads)** + [ADR 0005](docs/adr/0005-threading-via-reply-to.md) — `Reply-To: <id>` header, same-board, scan-on-read. Telnet `reply <id>` (auto Re: subject) + `read <id>` shows `Replies: N, M, ...`. CLI `--reply-to <id>`.

### Changed

- `print_banner` / `cmd_version` / `render_motd` version line bumped to 0.5.0.
- `cyrius.cyml [deps].stdlib` unchanged at 16 modules (M5-E/F added no new deps).

### Verified

- 49/49 tests pass from a clean build.
- Bench baseline (telnet/plain_byte 11 ns, telnet/subneg_naws 107 ns) consistent with 0.4.0 — M5-E/F is content-layer work, doesn't touch the IAC parser hot path.
- Security re-scan: board name validator + Reply-To parser bound external input; scan-on-read replies enumeration bounded by `DIRENT_ID_MAX`; no command injection; no orphans.
- End-to-end smoke (CLI + telnet): post + reply chain; on-disk file shows Reply-To header; `read 1` shows `Replies: 2, 3`; `reply 1` derives Re: subject and writes Reply-To.

### Added — ADR 0005 + M5-F: threading via Reply-To (2026-05-23) — **M5 close**

This bite closes M5. agora is now a **multi-board threaded BBS over telnet** — the post storage cycle that opened with ADR 0002 / M5-A / 0.4.0 reaches feature completeness with same-board reply linkage. Next release tag will be **0.5.0** (M5 close + roadmap restructure documented under 0.4.0).

- **[ADR 0005](docs/adr/0005-threading-via-reply-to.md)** — captures three load-bearing decisions: (A) reply relationship encoded as a `Reply-To: <id>` header in the RFC-822 block from ADR 0003; (α) same-board only (cross-board upgrade path documented as non-breaking); (p) scan-on-read for enumeration (O(n) per read, fine at v1.0 scale; mitigations available if scale grows). Rejects deep-threading via `In-Reply-To`+`References`, sidecar reply index, and fully-qualified `<board>/<id>` Reply-To values with concrete reasoning.
- **`src/board.cyr` additions**:
  - `post_format_with_headers(subject, reply_to, body, body_len, out, cap)` — extends ADR 0003's header block with an optional `Reply-To: <id>\r\n` line when `reply_to > 0`. The original `post_format_with_subject` becomes a thin wrapper passing `reply_to == 0`.
  - `post_new_with_subject_reply(store, board, subject, reply_to, body, body_len)` — wraps `post_format_with_headers` + the M5-G EXCL+flock claim. Same critical-section shape as M5-D's `post_new_with_subject`.
  - `post_reply_to(buf, len)` — extract parent ID from a post file's `Reply-To` header. Returns 0 when absent / unparseable / headerless.
  - `replies_to(store, board, parent_id, out_ids, max)` — scan the board's posts, accumulate IDs whose `Reply-To` matches `parent_id`. Returns sorted-ascending count.
  - `subject_reply_prefix(parent_subject, parent_len, out, max)` — RFC 5322 § 3.6.5 Re: rule: prepend "Re: " unless already present (case-insensitive on the letters). Never doubled.
- **Telnet `reply <id>`** command — validates parent exists in current board, derives Re-prefixed subject, **skips the Subject prompt**, transitions straight to MODE_POSTING. Parked state in globals (`g_reply_to`, `g_reply_subject`, `g_reply_subject_len`) is read by `session_finalize_post` on '.' commit and cleared after each post.
- **Telnet `read <id>`** appends `Replies: N, M, ...` after the body when any posts in the current board target this post. Silent when no replies.
- **CLI `agora post --reply-to <id>`** flag. When `--reply-to` is given without `--subject`, the CLI auto-derives the Re: subject from the parent (matching the wire-side reply UX).
- **Tests 43 → 49** (6 new): `t44_subject_reply_prefix_adds_re`, `t45_subject_reply_prefix_no_double_re` (RFC 5322 no-double rule), `t46_subject_reply_prefix_case_insensitive` (lowercase + mixed-case `re:`), `t47_post_reply_to_extracts_id`, `t48_post_reply_to_missing_returns_zero` (absent header + headerless), `t49_format_with_reply_to_header` (round-trip via `post_format_with_headers` ↔ `post_reply_to`).
- **End-to-end smoke** — CLI: `post`/`post --reply-to 1` chain; on-disk file shows Reply-To header. Telnet: `read 1` shows `Replies: 2, 3`; `reply 1` derives `Subject: Re: ...` automatically and writes Reply-To header; `list` displays the new reply; `read 1` reflects the new reply count.
- **Binary**: 135,064 B (M5-E) → 140,152 B (+5,088 B for the threading primitives, reply command, replies-list rendering, and CLI --reply-to plumbing).

**M5 cycle summary** (six bites + two ADRs, ready for 0.5.0 tag):
- M5-A storage primitives (ADR 0002)
- M5-B in-session command interpreter
- M5-C sorted listing
- M5-D RFC-822 headers (ADR 0003)
- M5-G per-store flock
- M5-H ingress input filter
- M5-E boards (ADR 0004)
- M5-F threading (ADR 0005)

### Added — ADR 0004 + M5-E: boards (2026-05-23)

agora is now a **multi-board BBS over telnet**. New session model: every connection opens at the implicit "main" board (flat `<store>/` per 0.4.0 layout); `enter <name>` switches to a named board (`<store>/<name>/`); `leave` returns to main. The prompt shows `[name] >` when in a named board so the user always knows which board their next command targets.

- **[ADR 0004](docs/adr/0004-board-layout.md)** — captures three load-bearing decisions: layout (flat-root = "main", subdirs = named — free backwards compat with 0.4.0 stores), UI (modal current-board for telnet, `--board` flag for CLI), lifecycle (auto-create on first post). Rejects three alternatives (all-boards-as-subdirs migration, sidecar index, per-port-board UI) with concrete reasoning.
- **`src/board.cyr` refactor** (~150 LOC):
  - `board_path(store, board, out)` — resolves to `<store>` for "main", `<store>/<board>` for named.
  - `board_name_valid(name)` — validates per ADR 0004 (1-32 bytes, lowercase ASCII + digits + '-' / '_', first byte letter or digit, "main" reserved).
  - `board_ensure(store, board)` — mkdir the per-board subdir (and `<store>` itself) treating EEXIST as success.
  - `boards_list(store, out, max)` — enumerate named subdirectory-shaped boards; filters post files + lockfile + hidden entries.
  - **Every existing primitive grew a `board` parameter** — `post_new`, `post_new_with_subject`, `post_read`, `post_list`, `post_max_id`, `store_lock_acquire`, `build_post_path`. Each board has its own ID counter + its own lockfile.
- **`src/main.cyr` wire integration** (~200 LOC):
  - New session state `current_board` (per-connection NUL-terminated cstring buffer, default "main").
  - New commands: `boards` (list main + named, with per-board post counts), `enter <name>` (switch board; auto-creates), `leave` (return to main).
  - `send_prompt` helper — bare `> ` in main, `[name] > ` in a named board.
  - `help` text updated; `session_execute` signature grew `current_board` parameter; `session_finalize_post` grew `current_board` parameter.
- **CLI `--board <name>` flag** on all three verbs (`post` / `list` / `read`). Default `main`. `parse_board()` helper mirrors the `--store` / `--subject` shape. `first_positional_after_verb` updated to skip any `--<flag> <value>` pair so the positional ID arg in `read` doesn't get shadowed.
- **Per-board lock + ID counter granularity** — concurrent writers to different boards never contend with each other. `<store>/<board>/.lock` per board (and `<store>/.lock` for main).
- **Tests grew 38 → 43**: `t39_build_post_path_named_board` (subdirectory path shape), `t40_board_name_valid_accepts` (canonical alphabet), `t41_board_name_valid_rejects` (uppercase, dot, slash, leading dash/underscore, reserved "main", over-length), `t42_board_path_main_is_flat`, `t43_board_path_named`.
- **End-to-end smoke** — five-case verification:
  1. Backwards-compat: legacy 0.4.0 flat store reads `list` + `read` correctly via the `main` resolution
  2. CLI `--board art` posts land in `<store>/art/` with their own ID counter
  3. Invalid board name (`BAD-Caps`) rejected at CLI ingress
  4. On-disk layout matches ADR (main posts at root, art posts in subdir, per-board lockfiles)
  5. Telnet session: `boards` shows counts, `enter art` switches prompt + scope, `read 2` reads from art (not main), `leave` restores main, all `list` / `read` reflect the current board
- **Roadmap restructured** to reflect the new release plan (per user direction 2026-05-23): **0.5.0** = M5 close (M5-E shipped, M5-F remaining), **0.6.0** = M6 sigil-backed auth, **0.7.0** = security sweep with CVE / 0-day web research, **0.8.0** = hardening + v1 lockdown, **1.0.0** = complete with iron validation on archaemenid LAN.

## [0.4.0] — 2026-05-23 (M5 partial — post persistence with metadata + concurrent-writer correctness)

agora is now a **working BBS over telnet**. Six bites landed across the M5 cycle: post storage primitives (M5-A), in-session command interpreter (M5-B), sorted listing (M5-C), RFC-822 headers per [ADR 0003](docs/adr/0003-rfc-822-post-headers.md) (M5-D), per-store flock (M5-G), and ingress input filter (M5-H). Two ADRs land: 0002 (one file per post, monotonic IDs) and 0003 (RFC-822 headers). 38 tests; 129,096 B; bench baseline unchanged. **M5 is partial** — boards (M5-E) and threads (M5-F) defer to a later release. Single-board single-thread BBS is the 0.4.0 shipping shape.

### Changed

- `print_banner` / `cmd_version` / connection MOTD / `render_motd` version line bumped to 0.4.0.
- `cyrius.cyml [deps].stdlib` grew `str` + `fs` (M5-A: storage primitives) + `chrono` (M5-D: ISO-8601 Date header). 13 stdlib modules at 0.3.0 → 16 at 0.4.0; darshana git dep unchanged at pin 0.5.3.
- **Closeout note**: security re-scan surfaced a latent stack-overrun in `t30_sort_i64_asc_basic` — `var expected[8]` allocated 8 bytes but stored 8 i64s (64 bytes). The layout silently tolerated the overrun on this host; fixed to `var expected[64]` with a comment citing the CLAUDE.md "buffer is N **bytes**, not N entries" rule. No production code affected.

### Added — M5-G: per-store flock for the post-claim critical section (2026-05-23)

- **New primitives in `src/board.cyr`**:
  - `store_lock_acquire(store)` — opens `<store>/.lock` (`O_WRONLY | O_CREAT`, 0o644), takes a blocking `LOCK_EX` flock via `lib/io.cyr` `file_lock`, returns the lockfile fd
  - `store_lock_release(fd)` — `file_close` (kernel releases the lock implicitly)
- **`post_new` and `post_new_with_subject` now serialize claim+write** through the lock. The `post_max_id` + `O_CREAT | O_EXCL` open + `write` triple runs inside the locked region; format-with-subject (pure per-call work) runs outside to shorten the critical section.
- **Lockfile naming dodges `parse_post_id`** — `.lock` doesn't end in `.txt` so it's filtered out by `post_list` / `post_max_id`. No new exclusion needed.
- **What this changes**: pre-M5-G, two concurrent writers reading the same `post_max_id` and racing on the EXCL claim would result in one writer succeeding and the other returning `-1` (EEXIST). The EXCL guarantee meant no corruption — just a dropped post. M5-G upgrades to "both writers serialize, both succeed, distinct IDs." Correctness improvement for high-fanout deployments (CLI + telnet concurrent, multiple CLI processes, future thread-per-conn accept loop).
- **Smoke**: 50 parallel `agora post` invocations under M5-G all return distinct IDs and produce 50 files on disk; zero errors. (Pre-M5-G the race window is narrow enough on this host that 50 also succeed by luck — the lock makes it a guarantee instead of probabilistic.)
- **Binary**: 128,352 → 129,096 B (+744 B for the lock helpers).
- **Tests still 38/38 green** — the lock is invisible to test.cyr's single-process pure-function suite. The "two-writer correctness" property is verified by the parallel CLI smoke harness in this CHANGELOG entry; an automated parallel-process test belongs in `tests/` once a multi-process harness exists (deferred).

### Added — ADR 0003 + M5-D: RFC-822-shaped post headers (Subject + Date) (2026-05-23)

- **[ADR 0003](docs/adr/0003-rfc-822-post-headers.md)** — captures the header-format decision: per-post file gets `Subject: <single-line>\r\n` + `Date: <ISO-8601-UTC>\r\n\r\n` block, then body. Rejects three alternatives (JSON, CYML front matter, TSV) with concrete reasoning. Backwards-compat with M5-A/B/C headerless posts is built into the parser (first byte not ASCII uppercase → treat whole file as body).
- **`src/board.cyr` additions** (~180 LOC):
  - `post_body_offset(buf, len)` — returns 0 (no headers) or offset past the blank line that terminates headers. Handles `\r\n\r\n` AND `\n\n` separators (mixed line endings tolerated within headers).
  - `header_get(buf, len, name, out, max)` — finds `Name: value` at start of any line in the header block; skips optional single space after `:`; returns value length copied or `-1` if not found.
  - `post_format_with_subject(subject, body, body_len, out, cap)` — composes `Subject: <s>\r\nDate: <iso8601_now>\r\n\r\n<body>`.
  - `post_new_with_subject(store, subject, body, body_len)` — formats + writes via the same EXCL-claim path as the M5-A `post_new`. Empty subject is allowed (writes `Subject: \r\n` so `header_get` returns 0-length instead of `-1`).
  - `post_subject(buf, len, out, max)` — convenience: `header_get` "Subject" but normalize the missing-header case to 0 (so `list` always renders an empty subject row instead of an error).
- **Wire integration in `src/main.cyr`**:
  - New session mode `MODE_POSTING_SUBJECT` between `MODE_COMMAND` and `MODE_POSTING`. Typing `post` now prompts `Subject: ` first; the next line is captured into a per-connection subject buffer; then the `Compose post.` prompt + body capture continues unchanged.
  - In-session `list` now shows `<id>  <subject>` per row (was bare `<id>`).
  - In-session `read <id>` now shows `Subject: ...\r\n\r\n<body>` (was raw file content).
  - CLI `agora post` grew `--subject <text>` flag (and an empty default).
  - CLI `agora list` and `agora read` updated for the same body-only / subject-prefix behavior as the wire.
- **`stdlib` deps** grew `chrono` for `iso8601_now` (Date header generation).
- **Fixed a session-buffer corruption bug surfaced during M5-D smoke**: when the EOL-paired LF arrived after CR, the previous code path fell through to the printable-byte branch and appended the LF to the line buffer at position 0 — corrupting every subsequent command's first byte. Added explicit `consumed` flag in the EOL detection that drops paired-LF entirely instead. Two-list-in-a-row reproduces the original bug; now passes clean.
- **Tests grew 32 → 38** — six new tests: `t33_post_body_offset_headerless` (sniffer-rejects-lowercase-start), `t34_post_body_offset_crlf` (CRLF blank-line separator), `t35_post_body_offset_lf` (LF-only separator), `t36_header_get_subject` (extract Subject value), `t37_header_get_missing` (absent header returns -1), `t38_post_subject_headerless_returns_zero` (normalization for `list` UX).
- **End-to-end CLI + telnet smoke** — CLI `post --subject "Hello"` + `list` shows `1  Hello`; `read 1` shows `Subject: Hello\n\nbody`. Telnet `post` prompts `Subject: `, captures the line, transitions to body capture, period-ends, writes file with both headers. Headerless legacy file dropped manually into the store renders as `4  ` (no subject) in `list` and prints body verbatim under `read`.
- **Binary delta**: 116,904 B (M5-H close) → 128,352 B (+11.4 KB for `lib/chrono.cyr` + header primitives + new session mode + CLI flag).

### Added — M5-C: sorted post listing (2026-05-23)

- **`post_list` now returns IDs in ascending order**. M5-A/B returned directory-iteration order which is non-deterministic and unfriendly to the `list` UX (and to anyone diff-checking output across runs).
- **`sort_i64_asc(arr, count)`** — in-place insertion sort over an i64 array. O(n²); appropriate for the v1.0 scale (`DIRENT_ID_MAX = 4096`, real post counts well below). Bumping the algorithm earns a bite only if a consumer reports perf concerns.
- Two new tests: `t30_sort_i64_asc_basic` (8-element unsorted array → ascending) and `t31_sort_i64_asc_empty_and_single` (edge cases). Wire smoke with 5 posts confirms `list` returns `1 2 3 4 5`.

### Added — M5-H: input filter on post bodies (2026-05-23)

- **`input_byte_ok(b)`** in `src/board.cyr` — drops NUL (`0x00`) and ESC (`0x1B`) from incoming post bodies; passthrough for everything else (TAB / CR / LF / printable ASCII / UTF-8 high bytes / BEL / BS / DEL). Applied in `handle_client`'s byte dispatch *before* the byte reaches the line buffer.
- **Threat model** documented inline:
  - **NUL** terminates cstring tooling downstream (`cat`, `grep`, `agora read`'s byte writer, `fmt_int_buf`); a post containing NUL would render as truncated everywhere.
  - **ESC** = terminal-control injection. A post containing `\x1b[2J` (clear screen), `\x1b[10;1H` (cursor to row 10), `\x1b]0;evil\x07` (set window title), or 70s-era VT keyboard-remapping sequences executes in the *viewer's* terminal when another user runs `read N` over telnet. Classic chat-attack vector — strip at ingress.
- **Living at the storage-policy layer** — `input_byte_ok` lives in `src/board.cyr` because it expresses what the post storage system accepts, not what the wire protocol allows. main.cyr's `handle_client` enforces it at ingress. Future operator-config may add an opt-in for raw-mode posts (useful if an operator wants to allow ANSI art in posts on a known-friendly LAN).
- **One new test**: `t32_input_byte_ok_filters_nul_esc` exercises both rejected bytes + 9 passthrough cases including UTF-8 lead/continuation bytes.
- **Wire smoke**: a malicious post containing `Hello\x1b[31mRED\x1b[0m and NUL\x00here` lands on disk as `Hello[31mRED[0m and NULhere\r\n` — both ESC bytes and the NUL byte stripped; the harmless `[31m` / `[0m` text bytes remain as inert content. `grep -c -P "\x1b" 6.txt` and `grep -c -P "\x00" 6.txt` both return 0.

### Added — M5-B: in-session command interpreter over telnet (2026-05-23)

- **Connected-client command loop** — `handle_client` now runs a line-buffered command interpreter after the MOTD instead of the echo-only loop. Supported commands (typed at the `>` prompt):
  - `help` — list available commands
  - `list` — print post IDs (one per line)
  - `read <id>` — print one post body, trailing-CRLF-normalized
  - `post` — enter compose mode; multi-line input ends with `.` on a line by itself; assigned ID is returned ("posted as #N")
  - `quit` / `exit` / `bye` — close the session ("bye" then disconnect)
- **`agora serve` grew `--store <path>`** — same shape and default (`./agora-data/`) as the CLI verbs. Passed through to `handle_client` via the new `g_store_buf` global (set-once-at-startup, parallel to `g_motd_*`).
- **Session helpers in `src/main.cyr`** (~250 LOC added):
  - `send_str(cfd, s)` / `echo_byte(cfd, b)` — wire-output convenience
  - `line_has_prefix(line, len, prefix)` — command dispatch by leading token
  - `line_parse_int(line, off, len)` — parse `<id>` argument; skips leading whitespace, stops at first non-digit, rejects zero / no-digits
  - `session_execute(cfd, line, len, quit_out)` — dispatch on the typed line; returns the new mode (`MODE_COMMAND` or `MODE_POSTING`)
  - `session_finalize_post(cfd, body, len)` — commit the composed body via `post_new`, send "posted as #N" or "post failed (storage error)"
- **CR/LF discipline per telnet NVT (RFC 854)** — CR is the canonical line terminator; the LF that often follows is paired and silently absorbed via a `last_cr` flag; lone LF also terminates (raw-`nc` clients). Each typed printable byte is echoed (we announced `WILL ECHO` at M2-B). Backspace handling is deferred — typed text isn't editable in-line at M5-B.
- **Two-mode state machine**:
  - `MODE_COMMAND` (default): each complete line dispatches to a command
  - `MODE_POSTING`: each complete line is appended to the post body (with CRLF); a line that's exactly `.` ends the compose flow and commits
- **End-to-end smoke** — Python TCP client walks every command path:
  `help` shows the list, empty `list` returns "(no posts)", `post` + multi-line body + `.` returns "posted as #1", `list` reflects the new ID, `read 1` returns the body bytes, `read 99` returns "post not found", `badcmd` returns "unknown command", `quit` returns "bye" + disconnects. Files land in `--store` per ADR 0002 shape.
- **24-test parser suite + 5-test board suite still green** — this bite is integration-layer code; the IAC state machine and post storage primitives are untouched. Binary 109,992 → 116,232 B (+6,240 B for the command interpreter).

### Added — M5 ADR 0002 + M5-A: post storage primitives (2026-05-23)

- **`docs/adr/0002-one-file-per-post-storage.md`** — captures the M5 storage-layout decision: one file per post (`<store>/<id>.txt`, monotonic-integer IDs), operator-configurable storage root via `--store <path>` (default `./agora-data/`), plaintext UTF-8 body bytes only. Rejects two alternatives — one-file-per-thread-with-offset-index and SQLite-style WAL — with concrete reasoning. The shape is a strict prefix of the eventual v2.x content-addressed-storage layout (pillar 2 in `roadmap-future.md`): swap the ID-assignment fn, schema stays.
- **`src/board.cyr`** (~165 LOC) — `store_ensure` (mkdir, EEXIST-as-success), `build_post_path` (path formatter), `parse_post_id` (filename → integer or 0), `post_max_id` (O(n) dir scan), `post_new` (write with `O_CREAT | O_EXCL` for atomic ID claim), `post_read` (file_read_all by ID), `post_list` (iterate dir, parse valid IDs). All bounded by named caps (`POST_MAX_BYTES = 64 KB`, `PATH_MAX_BYTES = 512`, `DIRENT_ID_MAX = 4096`).
- **CLI verbs now real** — `cmd_post` reads stdin into a 64 KB buffer (multi-read loop until EOF) → `post_new` → prints assigned ID. `cmd_list` walks the store directory, prints valid post IDs. `cmd_read <id>` validates the ID, opens the file, writes body bytes to stdout. All three accept `--store <path>` (order-insensitive parse, same shape as M2-C's `--motd`).
- **`stdlib` deps grew**: added `str` (for `dir_list`'s Str interop) and `fs` (the `dir_list` primitive itself).
- **Tests grew 24 → 29** — `t25_parse_post_id_valid` (1.txt / 42.txt / 9999.txt round-trip), `t26_parse_post_id_rejects_non_txt` (`1.log` / `1.tx` / bare-int), `t27_parse_post_id_rejects_non_digits` (`foo.txt` / `1a.txt` / `1.2.txt`), `t28_parse_post_id_rejects_zero` (IDs are 1-indexed), `t29_build_post_path_shape` (verbatim path construction). The cyrius "continue without incrementing i = infinite loop" trap surfaced + got fixed during the first test run.
- **End-to-end CLI smoke** — empty store → `no posts` exit 0; three posts written round-trip via stdin → file IDs 1/2/3 on disk under 0644; `list` returns IDs (directory order; sort is M5-A-deferred); `read 2` returns the body verbatim; `read 99` reports `post not found` exit 1; `read foo` reports `invalid post ID` exit 2.
- **Binary delta**: 85,544 B (0.3.0) → 109,992 B (+24.4 KB for board.cyr + str + fs stdlib surface; most DCE-eligible).
- **Out of scope at M5-A** (per ADR 0002): boards (M5-E), threads (M5-F), concurrent-write lock (M5-G), telnet-wire integration (M5-B), RFC-822 headers in the post file (M5-D).

## [0.3.0] — 2026-05-23 (M2 close: ANSI BBS aesthetic)

M2 cycle landed end-to-end across three bites — `bnrmr`-rendered AGORA banner embedded as the connection MOTD (M2-A), darshana SGR coloring wrapped around the banner / version / prompt at connection time (M2-B), and `agora serve [port] [--motd <path>]` operator override (M2-C). bannermanor patched 1.0.0 → 1.0.1 the same day so every AGNOS consumer of darshana is on the same `0.5.3` pin. M2-D (NAWS-aware width clamping) remains an optional polish bite — M2 is functionally closed without it.

24-test parser conformance still green. Binary 70,960 B (M1 close) → 85,544 B (M2 close); the +14.6 KB is mostly `lib/darshana.cyr` consumption surface (most DCE-eligible — 243 unreachable fns NOPed at 31,515 B). Bench baseline unchanged from M1 (`telnet/plain_byte` ~10 ns, `subneg_naws` ~100 ns).

### Changed

- `cyrius.cyml [deps]` — added `[deps.darshana]` git dep pinned at `0.5.3` (M2-B). Bannermanor pins the same `0.5.3` at 1.0.1.
- `src/main.cyr` — version literals (`print_banner` / `cmd_version` / `render_motd` version line) bumped to 0.3.0. Inline-version-string drift remains the known technical-debt item flagged in [0.2.0]; CI's drift-check step (added in 0.2.0) caught us if we'd forgotten.
- `print_help` updated to document the `--motd` flag.

### Added — M2-C: `agora serve --motd <path>` operator override (2026-05-23)

- **New flag**: `agora serve [port] [--motd <path>]`. Order-insensitive argv parse — positive-integer positionals still take the port, `--motd` consumes the next arg as a filesystem path.
- **`load_motd_file(path)`** — reads up to 4 KB from `path` once at startup via `lib/io.cyr` `file_read_all`, parks the buffer + length in two globals (`g_motd_buf`, `g_motd_len`). Three failure modes warn-and-fall-back to the default MOTD: missing path arg (returns exit 2), `read` failure (open error or read error), and zero-byte file. Set-once-at-startup state — no per-connection re-read.
- **`handle_client` MOTD dispatch** — if `g_motd_buf` is non-null, sends those bytes verbatim; otherwise allocates a per-connection 1 KB buffer and runs the M2-B `render_motd` path. The override is verbatim — operator is responsible for CRLF line endings (telnet NVT, RFC 854) and any ANSI escapes they want to embed.
- **Smoke** — three cases verified end-to-end against a python TCP client:
  1. No flag → default cyan-wrapped AGORA banner via `render_motd`
  2. `--motd /tmp/operator-motd.txt` → file content delivered verbatim
  3. `--motd /nonexistent` → stderr warning, server continues with default MOTD
- **Help text updated** in `print_help` to document the flag.
- 24-test parser suite still green (this bite is content-layer, doesn't touch the IAC state machine). Binary 84,488 → 85,544 B (+1,056 B).

### Added — M2-B: darshana SGR-colored MOTD (2026-05-23)

- **`[deps.darshana]`** — added to `cyrius.cyml` as a git dep pinned at `0.5.3`. Functional surface (`tty_sgr_buf`, `tty_sgr_reset_buf`, `tty_fg_rgb_buf`, cursor primitives) is present at 0.5.3 even though darshana itself is pre-1.0 — the "needs ≥ 1.0" gate in the original roadmap was a version-label restriction, not a functionality one. Bannermanor 1.0.1 re-pinned to the same `0.5.3` the same day so every AGNOS consumer of darshana is on one version.
- **`render_motd(buf)`** — new function in `src/main.cyr` that composes the bannermanor-derived AGORA banner with darshana SGR coloring directly into a caller-allocated 1 KB buffer. The `_buf` variants (`tty_sgr_buf` / `tty_sgr_reset_buf`) target a buffer instead of fd 1, which is exactly what we need to send bytes back over the telnet socket via `send_buf`.
- **Color scheme**:
  - AGORA ASCII banner (5 lines) — cyan (`SGR 36`)
  - Version line ("agora 0.2.0 — telnet BBS") — yellow (`SGR 33`)
  - Prompt line ("Type anything; Ctrl+] then 'quit' to exit.") — default fg
- **`handle_client`** — static `banner` string variable replaced with a `motd = alloc(1024); render_motd(motd); send_buf(...)` pattern. Per-connection allocation is one `alloc` + one render pass + one `send_buf` — sub-microsecond on this host; immaterial vs the human-paced BBS workload.
- **Wire smoke** — python TCP client receives the 12-byte announce salvo followed by 4 ANSI ESC sequences (cyan-on, reset, yellow-on, reset) wrapping the banner content. Real telnet clients render the AGORA in cyan and the version in yellow.
- **Binary delta**: 71,120 → 84,488 B (+13,368 B for `lib/darshana.cyr` consumption surface; 248 unreachable fns / 32,371 B DCE-eligible, most of the darshana surface we don't call yet — gets reclaimed when the v1.x close-out adds strip + DCE-aware emit).
- 24-test parser conformance still green — `render_motd` is content-layer code that doesn't touch the IAC state machine.
- **Remaining M2 work**: M2-C (`--motd <path>` operator override) is optional, lands when operator demand surfaces. NAWS-aware reflow (using `term_cols` / `term_rows` from M1 to clamp banner width) is a natural M2-D when consumer tooling needs it.

### Added — M2-A: bannermanor MOTD on connect (2026-05-23)

- **Connection MOTD upgraded** from a plaintext `agora 0.2.0 — telnet BBS` line to a bannermanor-rendered ASCII-art `AGORA` banner (block font, 5×5) followed by the version line and the input-prompt help. Pre-rendered via `bnrmr "AGORA"` and embedded as a string constant in `src/main.cyr` — no runtime subprocess shellout, no dep on `bnrmr` being installed at runtime, no per-connection latency for re-rendering static content.
- **Provenance documented in code** — the embed site carries a comment block citing bannermanor v1.0.0 (frozen CLI surface) and the regeneration recipe (`bnrmr "AGORA"`) so future label / version / banner-text changes are reproducible. `#` bytes inside the string use `\x23` escapes to dodge cyrius's line-comment lexer.
- **Binary delta**: 70,960 → 71,120 B (+160 B for the ~470-byte rendered banner string).
- **End-to-end smoke**: python TCP client receives the 12-byte announce IAC salvo as before, followed by the multi-line banner; existing 24-test parser conformance suite still green.
- M2's second bite (ANSI color via darshana SGR + cursor positioning + NAWS-aware width) waits on darshana ≥ 1.0 (currently 0.5.3).

## [0.2.0] — 2026-05-23 (M1 close: cross-platform telnet listener)

Multi-bite M1 cycle landed end-to-end: RFC 854 IAC parser + RFC 1143 Q-method option negotiation + RFC 1073 NAWS + RFC 1091 TERMINAL_TYPE + RFC 1184 LINEMODE, all wire-conformant via paired python TCP client smoke. Cross-platform via `lib/net.cyr` (Linux x86_64 + aarch64 today; macOS / Windows / AGNOS as the stdlib gains backends — see [ADR 0001](docs/adr/0001-cross-platform-listener-decoupled-from-agnos.md)). 24 tests passing; 5-benchmark parser baseline captured in [`BENCHMARKS.md`](BENCHMARKS.md). Binary 43,216 B (v0.1.0 scaffold) → 70,960 B at 0.2.0 close.

### Changed

- `cmd_serve` upgraded from M1 stub to a real cross-platform telnet listener (default port 2323; configurable via `agora serve <port>`).
- `print_banner` / `cmd_version` / connection-MOTD strings bumped to 0.2.0. (Note: version strings remain inlined in `src/main.cyr` — `cyrius` has no source-level `${file:VERSION}` interpolation yet, only `.cyml`-level. Embedded version constant via a generated `version_str.cyr` is a v1.0 close-out item.)
- `cyrius.cyml` `[deps].stdlib` grew from 7 modules (scaffold) to 13 modules across the M1 cycle: added `net` + `result` + `tagged` (first-bite, socket primitives + Result type), `vec` + `fnptr` + `bench` (close-bite, bench harness dependencies).

### Added — CI / Release workflows (2026-05-23)

Pattern adopted from [kii](https://github.com/MacCracken/kii) + [bannermanor](https://github.com/MacCracken/bannermanor), the first-party reference implementations:

- **`.github/workflows/ci.yml`** — push / PR / `workflow_call` triggers. Concurrency: `cancel-in-progress` per-ref so only the latest push tests. Steps: checkout → install cyrius toolchain (version read from `cyrius.cyml [package].cyrius` — single source of truth) → `cyrius deps` → `cyrius build src/main.cyr build/agora` → **version drift check** (compares `./build/agora --version | head -1` against `VERSION`; catches inline-literal drift in `src/main.cyr` since cyrius lacks source-level `${file:VERSION}`) → `cyrius test` (auto-picks `[build].test`, runs the 24-test conformance suite).
- **`.github/workflows/release.yml`** — tag-triggered on `tags: ['[0-9]*']` (semver-only filter per CLAUDE.md). `permissions: contents: write`. CI gate via `uses: ./.github/workflows/ci.yml` (re-runs the full CI matrix before the release artifact builds). **Version verify**: `VERSION` file must equal the git tag, or the run fails. Then install + build + `softprops/action-gh-release@v2` with `files: build/*` and auto-generated release notes from the GitHub API.
- **What's NOT in CI yet** (deferred until earned): fuzz harness (a `tests/agora.fcyr` driving telnet_feed against random byte streams — adversarial-by-default protocol, fuzz earns its spot at M2+ when the input surface widens with NAWS/TT consumption), bench step (`BENCHMARKS.md` is hand-maintained at 0.2.0; CI bench gates land alongside `scripts/bench-history.sh` at v1.0 close-out), aarch64 cross build (waits on cyrius cross-toolchain availability in the CI runner image), `CYRIUS_DCE=1` builds (CLAUDE.md mentions but kii / bannermanor don't enforce yet — match the reference implementations until the convention formalizes).

### Added — M1 close: bench harness + first parser baseline (2026-05-23)

- **`benches/bench_telnet.bcyr`** (~115 LOC) — five parser microbenchmarks via `lib/bench.cyr` `bench_run_batch` (10 rounds × 10,000 iterations each):
  - `telnet/plain_byte` — single byte through ST_DATA path
  - `telnet/iac_untracked` — `IAC WILL OPT_STATUS` (3 bytes, naive-refuse + 3-byte reply)
  - `telnet/iac_tracked_agree` — `IAC WILL SGA` (3 bytes, Q machine agree + 3-byte reply)
  - `telnet/subneg_naws` — full NAWS subneg (9 bytes + payload decode)
  - `telnet/announce_salvo` — 4-option opening salvo (one-time-per-connection cost)
- **`BENCHMARKS.md` at repo root** — first baseline captured per [first-party-documentation § Benchmarks](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#benchmarks-and-performance-docs). Numbers on Linux x86_64 workstation, Cyrius 6.0.1:
  | Benchmark | Avg |
  |---|---:|
  | `telnet/plain_byte` | **10 ns** |
  | `telnet/iac_untracked` | **63 ns** |
  | `telnet/iac_tracked_agree` | **73 ns** |
  | `telnet/subneg_naws` | **97 ns** |
  | `telnet/announce_salvo` | **132 ns** |

  Derived throughput: ~100 M plain-bytes/s through the parser; ~14 M tracked option-exchanges/s; ~10 M NAWS subnegs/s. Orders of magnitude above any plausible BBS load.
- **`cyrius.cyml` `[deps]`** — added `vec`, `fnptr`, `bench` to stdlib list (needed for the bench harness). Binary grew 62,176 → 70,960 B (+8,784 B from the larger stdlib surface); DCE NOPs 26,707 B of the bench-only paths leaving them unreachable but allocated. Acceptable cost for the M1 close — release-build optimization is a v1.x close-out concern, not blocking.
- **What's NOT in the baseline** (deferred to follow-up bench files): accept-loop rate (needs paired client process), end-to-end echo latency over loopback, memory pressure under N concurrent connections, DCE-stripped binary perf.

### M1 closed (2026-05-23) — cross-platform telnet listener

All four protocol bites + bench harness now landed. M1 close summary:

- **Protocol surface**: RFC 854 (IAC parser), RFC 1143 (Q-method negotiation), RFC 1073 (NAWS), RFC 1091 (TERMINAL_TYPE), RFC 1184 (LINEMODE) — all wire-conformant.
- **Tests**: 24/24 green, RFC sequences + state transitions + malformed-payload defense.
- **Smoke**: end-to-end handshake (announce → peer agree → server TT SEND → peer NAWS+TT IS+LINEMODE ACK → data echo) wire-conformant via python TCP client.
- **Bench**: parser at 10 ns/byte hot path, ~100 ns for full option exchanges. First baseline captured.
- **Lifecycle**: slowloris timeout (60 s default) + graceful EOF/error close.
- **Cross-platform**: built on `lib/net.cyr` per [ADR 0001](docs/adr/0001-cross-platform-listener-decoupled-from-agnos.md) — Linux x86_64 + aarch64 today, macOS/Windows/AGNOS as stdlib gains backends.

**Next in-flight slot: M2** — ANSI BBS aesthetic. Consumes `bannermanor` 1.0.0 ✅ (for ASCII MOTD banners) + darshana ≥ 1.0 ❌ (currently 0.5.3 — likely gated on darshana's own 1.0 cut). Likely first M2 bite: bannermanor MOTD on connect ahead of the existing plaintext banner.

### Added — Post-v1.0 roadmap: v2.x sovereignty pillars (2026-05-23)

- **`docs/development/roadmap-future.md`** — new file consolidating six unpinned design directions for the v2.x sovereignty layer:
  1. **Identity continuity across nodes** — Ed25519 keypair as portable identity (Nostr-shaped, sigil-backed); replaces per-node accounts with global fingerprints. Graduates from v1.0 M6 sigil-backed auth.
  2. **Content-addressed storage** — posts keyed by `blake3(canonical(post))`; mirror anywhere without breaking links; citations integrity-checkable. Layered onto v1.0 M5 persistence.
  3. **Threat-level node policy** — mirror the SecureYeoman threat-level vocabulary (`hobbyist` / `journalist` / `activist` / `enterprise`) and apply it to network exposure. Same binary, different config.
  4. **Federation by interest, not platform** — topic-shaped federation (FidoNet echomail / Usenet / Matrix-rooms heritage); nodes carry topics, not "your account on this server."
  5. **Self-distribution baked-in** — every node carries AGNOS / SecureYeoman / marketplace installers; the network is the distribution channel. Block-resistance compounds with deployment count.
  6. **Offline-tolerant store-and-forward** — durable outbox + sync-on-connect + sneakernet-friendly export/import; FidoNet/UUCP-shape; works where ActivityPub silently fails (rural, censored, sanctioned, air-gapped).
- Cross-linked from `roadmap.md` ("Post-v1.0 Directions" section), `docs/doc-health.md` (Tier 2 row + bucket count), and this CHANGELOG.
- Pattern adopted from [cyrius/docs/development/roadmap-future.md](https://github.com/MacCracken/cyrius/blob/main/docs/development/roadmap-future.md): unpinned items, pull-forward triggers documented per pillar, no calendar commitment.

### Added — M1 fourth-bite: RFC 1184 LINEMODE (2026-05-23)

- **LINEMODE promoted to tracked** — `opt_pref_him(OPT_LINEMODE)` now returns 1. Peer's `WILL LINEMODE` lands him-state on `Q_YES` via the `Q_NO → Q_YES` transition; server replies `IAC DO LINEMODE` (3 bytes) and immediately follows with the MODE-establishment request (7 bytes) for a total 10-byte burst.
- **`ts_emit_linemode_request`** — composes `IAC SB LINEMODE MODE (LM_EDIT | LM_TRAPSIG) IAC SE`. Mask 0x03 is the BBS default: client buffers a line locally and forwards on Enter; client traps signal characters (Ctrl+C → IP, Ctrl+\ → BRK, Ctrl+] → AYT) as IAC commands. `ts_on_him_yes` dispatches to this on `Q_YES` transition for OPT_LINEMODE (alongside the existing TT SEND emit).
- **`telnet_handle_sb` LINEMODE dispatch** — sub-command MODE stores the peer's acknowledged mask byte into a new `TS_LM_MODE` field; sub-command SLC is parsed-and-ignored (RFC 1184 § Set Local Character — peer's local-character table doesn't drive server behavior yet); FORWARDMASK deferred. Malformed MODE (not exactly 1 mask byte) silently dropped.
- **TelnetState grew 1 field** — `TS_LM_MODE` (i64, holds the active LINEMODE mask after peer ACK). Total struct size 120 B → 128 B; per-connection allocation unchanged otherwise.
- **`telnet_linemode_mask` accessor** — exposes the current LINEMODE mask to consumers; 0 until peer confirms via `IAC SB LINEMODE MODE <mask> IAC SE`.
- **Tests grew to 24** (was 20) — `t21_will_linemode_emits_mode_request` (10-byte burst: DO LINEMODE + MODE-request), `t22_linemode_mode_ack_parse` (mask 0x07 stored from peer ACK), `t23_linemode_slc_ignored` (SLC parsed-and-ignored, parser recovers to DATA), `t24_linemode_mode_malformed_dropped` (zero-mask-byte MODE silently dropped).
- **End-to-end smoke** — python TCP client sends `WILL LINEMODE`, server replies with the exact 10-byte burst; client ACKs `MODE 0x07`, server captures silently; subsequent data byte 'L' echoes through cleanly. Binary 61,152 → **62,176 B** (+1,024 B for LINEMODE).

### Added — M1 third-bite: NAWS + TERMINAL_TYPE subneg parsing (2026-05-23)

- **NAWS payload parser** (RFC 1073) — `telnet_handle_sb` decodes the 4-byte BE-encoded window-size payload into per-connection `term_cols` / `term_rows` fields. IAC-escaped 0xFF bytes inside the payload pass through correctly (already handled by the SB-IAC state). Malformed lengths (not exactly 4 payload bytes) are silently dropped.
- **TERMINAL_TYPE handshake** (RFC 1091) — when peer's `WILL TERMINAL_TYPE` lands him-state on `Q_YES` (via the new `ts_on_him_yes` hook), the server immediately queues the 6-byte SEND request `IAC SB TT SEND IAC SE`. Peer's `IAC SB TT IS <ascii> IAC SE` reply is parsed into a 256-byte per-connection `term_type` buffer.
- **TelnetState grew 4 fields** — `TS_TERM_COLS` / `TS_TERM_ROWS` / `TS_TERM_TYPE` / `TS_TERM_TLEN`. Total struct size 88 B → 120 B; per-connection allocation gains the 256-byte term-type buffer (zero-initialized via `memset`).
- **`handle_client` consumes `EV_SB`** — when `telnet_feed` returns `EV_SB`, the per-byte loop calls `telnet_handle_sb(ts)`. Replies it queues (e.g. a second TT SEND) flush on the next tx-drain in the same loop iteration.
- **Tests grew to 20** (was 15) — `t16_naws_parse` (80×24 from canonical VT subneg), `t17_naws_iac_escape` (width=255 with IAC IAC escape correctly unescapes), `t18_terminal_type_is` ("XTERM" string captured), `t19_will_tt_emits_send` (peer WILL TT triggers 6-byte SEND reply + him-TT lands Q_YES), `t20_naws_malformed_dropped` (3-byte NAWS payload silently rejected, term_cols stays 0).
- **End-to-end smoke** — python client agrees to ECHO/SGA, sends WILL NAWS + WILL TT, server replies with IAC SB TT SEND IAC SE; client sends NAWS subneg (120×40) + TT IS XTERM subneg; server consumes both silently and the next data byte 'K' echoes through cleanly. Binary 59,280 B → **61,152 B** (+1,872 B for subneg parser + 256 B per-conn term buffer).

### Added — M1 second-bite: RFC 1143 Q-method option negotiation (2026-05-23)

- **`telnet_handle_negotiation`** (~75 LOC in `src/telnet.cyr`) — three-state Q machine (`Q_NO` / `Q_WANTYES` / `Q_YES`) per option per side, replacing the first-bite naive-refuse-everything path. Untracked options still naive-refuse; tracked options run full RFC 1143 transitions with no on-wire WILL/WONT loops.
- **Per-connection option state** — `TelnetState` grew two 256-byte arrays (`opt_us`, `opt_him`), accessed via `opt_us(ts, opt)` / `opt_him(ts, opt)` and their setters. `telnet_state_new` zero-initializes both via `memset` so every option starts in `Q_NO` until activity moves it.
- **Server preferences** — `opt_pref_us(opt)` returns 1 for `ECHO` and `SUPPRESS_GO_AHEAD`; `opt_pref_him(opt)` returns 1 for `SUPPRESS_GO_AHEAD`, `NAWS`, `TERMINAL_TYPE`. Drives both `telnet_announce` and the per-event Q transitions.
- **`telnet_announce`** — replaces the first-bite no-op stub. Queues the four-byte salvo onto `tx_buf` (`IAC WILL ECHO`, `IAC WILL SGA`, `IAC DO NAWS`, `IAC DO TT`) and parks each option in `Q_WANTYES` on the relevant side. `handle_client` calls it after `telnet_state_new` and flushes before the banner.
- **Slowloris defense** — `sock_set_recv_timeout(cfd, 60, 0)` per connection. A quiet client (no traffic for 60s) drops cleanly via the `n <= 0` branch in the recv loop. Tuned for human-paced BBS use; trim `RECV_TIMEOUT_SECS` for higher fanout.
- **Graceful close** — comment-documented the EOF (`n == 0`) and error/timeout (`n < 0`) paths in `handle_client` so the disconnect intent is explicit.
- **Tests grew to 15** (was 10) — added `t10_announce_salvo` (exact byte sequence + WANTYES parking), `t11_announce_then_do_silent` (peer agrees, no on-wire reply), `t12_announce_then_dont_silent` (peer refuses, silent), `t13_untracked_option_refused` (STATUS still naive-refused), `t14_announce_then_will_silent` (peer-side WILL agreement). Updated `t04_do_sga_agreed` (was `t04_do_sga_refused` — DO SGA now triggers `WILL SGA` per `us_SGA=YES` preference).
- **End-to-end smoke** — python TCP client confirms the announce salvo arrives in exact order, peer `DO ECHO` reply produces silent agreement (us-ECHO `WANTYES → YES`), and plain data bytes echo through. Binary 56,064 B → **59,280 B** (+3,216 B for the Q machine + 512 B of per-connection option state).

### Added — M1 first-bite: cross-platform telnet listener (2026-05-23)

- **`src/telnet.cyr`** (~280 LOC) — RFC 854 IAC parser + RFC 1184 LINEMODE scaffolding. `TelnetState` struct + per-byte feed function `telnet_feed(ts, b)` returns one of `EV_DATA` / `EV_NONE` / `EV_SB`. Naive-refuse option-negotiation policy: every `DO` replies `WONT`, every `WILL` replies `DONT` (RFC 1143 § Q method — refuses safely, never agrees by accident).
- **`src/main.cyr`** — `cmd_serve` opens a listener via `lib/net.cyr` (`tcp_socket` / `sock_bind` / `sock_listen` / `sock_accept`). Default port 2323 (unprivileged); override via `agora serve <port>`. Per-connection IAC-aware echo loop wires the parser to the socket — refused-option replies flush onto the wire in temporal order before the next data byte echoes.
- **`src/test.cyr`** (10 unit tests, all passing) — RFC 854 conformance: plain data passthrough, `IAC IAC` literal escape, `WILL ECHO` → `DONT ECHO` refusal, `DO SUPPRESS_GO_AHEAD` → `WONT SGA` refusal, `NOP` consumed silently, subnegotiation collection (`IAC SB ... IAC SE`) with `EV_SB` event, escaped IAC inside subneg, mixed data/IAC byte streams, malformed-SB recovery, `tx_buf` drain/consume cycle.
- **`cyrius.cyml` [deps]** — added `net`, `result`, `tagged` to `stdlib` list. Resolved via `cyrius lib sync` from 6.0.1 snapshot.
- **End-to-end smoke** — python TCP client connects, receives banner, sends `IAC WILL ECHO` + `IAC DO LINEMODE` + `IAC NOP` + plain bytes; server replies in exact RFC-conformant order: `IAC DONT ECHO`, `IAC WONT LINEMODE`, then echoes plain bytes.

### Added — Docs scaffold per first-party standards (2026-05-23)

- `CLAUDE.md` per [example_claude.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/example_claude.md) template — durable rules; volatile state delegated to `docs/development/state.md`.
- `docs/development/roadmap.md` — extracted from `README.md`; full milestone table + sub-bites + v1.0 criteria.
- `docs/development/state.md` — live state snapshot (version, binary size, in-flight slot, gate state for downstream milestones).
- `docs/doc-health.md` — fresh / stale / archive ledger; pattern adapted from [cyrius/docs/doc-health.md](https://github.com/MacCracken/cyrius/blob/main/docs/doc-health.md).
- `docs/adr/` — README + template + `0001-cross-platform-listener-decoupled-from-agnos.md` (the load-bearing M1 decision).
- `docs/architecture/README.md` — index placeholder; first note earns its slot at M1 close.
- `docs/guides/getting-started.md` — build / smoke / run on Linux x86_64 + aarch64.
- `docs/examples/README.md` — placeholder.
- `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` — required root files per first-party scaffold.
- `README.md` — slimmed, points at `docs/development/roadmap.md` + the new doc tree.

### Changed

- `cmd_serve` upgraded from M1 stub to a real listener — exits stub-mode at the protocol level.
- Binary size 43,216 B (v0.1.0 scaffold) → 56,064 B (M1 first-bite, non-DCE) — +12.8 KB for the IAC parser, listener loop, and `lib/net.cyr` consumption surface.

## [0.1.0] — 2026-05-23 (Scaffold)

### Added

- Repo scaffold: `VERSION`, `cyrius.cyml` (toolchain pin 6.0.1), `src/main.cyr` (argv dispatch + boot banner + stub verbs), `README.md` (etymology + roadmap), `CHANGELOG.md`, `LICENSE` (GPL-3.0-only), `.gitignore`.
- Six stub verbs: `serve` (M1 telnet listener), `post` / `list` / `read` (M5 persistence), `whoami` (M6 auth), `version`, `help`.
- Build verified: `cyrius build src/main.cyr build/agora` → 43,216 B binary; `./build/agora help` + `version` exercise the dispatch.

### Notes

- Pre-M1 release — no networking, no persistence, no protocol code. Verbs print stubs and exit non-zero (except `version` / `help`).
- M1 (telnet listener) is gated on agnos 1.32.2 cycle closing — `tcp_listen(23)` must validate end-to-end on archaemenid iron first.
- M5 (post persistence) is gated on agnos 1.33.x ext4 WRITE landing (Phase 1-5 currently read-only).
- Naming convention: introduces a Greek lane to the AGNOS ecosystem alongside the existing Sanskrit/Hindi (system libs) + English-wordplay / Polynesian (user-facing tools) lanes — see [[feedback_naming_lanes]]. The name threads three independent layers — ancient Greek ἀγορά + Doja Cat "Agora Hills" (Scarlet, 2023) + Agoura Hills CA (literally adjacent to the project's home base in Thousand Oaks). Multi-layer convergence in the spirit of `kii`'s Polynesian/East-Asian/English-phonetic precedent.
