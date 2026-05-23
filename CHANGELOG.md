# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
