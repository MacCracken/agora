# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
