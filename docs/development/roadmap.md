# agora — Roadmap

> **Last Updated**: 2026-05-23
>
> Versioned milestones through v1.0. Per [first-party-documentation § Development Docs](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#development-docs-docsdevelopment), this file lists Completed, In Progress / Backlog, Future, and v1.0 Criteria. Updated every release.

agora is the BBS userland for AGNOS — Greek ἀγορά (civic-marketplace / public-assembly). The roadmap below tracks the path from scaffold to multi-user telnet BBS on iron. **The project is cross-platform**: M1 onward runs on Linux today via cyrius `lib/net.cyr`, not gated on the AGNOS kernel — AGNOS becomes one target among many as `net.cyr` grows platform backends.

---

## Milestones

| Milestone | Scope | Gate state |
|---|---|---|
| **M0 (0.1.0)** ✅ | argv dispatch + boot banner + stub verbs | scaffold-only — shipped 2026-05-23 |
| **M1** ✅ | Telnet listener (RFC 854 + 1143 + 1073 + 1091 + 1184), cross-platform via `lib/net.cyr` | closed 2026-05-23 — five bites: IAC parser, Q-method, NAWS+TT subneg, LINEMODE, bench harness. See [`state.md`](state.md#recently-closed). |
| **M2** ✅ | ANSI BBS aesthetic — bannermanor MOTD + darshana SGR colors + `--motd` override | closed 2026-05-23 at 0.3.0 — three bites: M2-A/B/C. See [`state.md`](state.md#recently-closed). M2-D (NAWS width clamp) deferred as optional polish. |
| **M5** ← in progress | Post persistence (boards / threads / messages) | **M5-A + M5-B landed 2026-05-23** — ADR 0002 + `src/board.cyr` (one-file-per-post) + CLI verbs + in-session command interpreter over telnet (`list` / `read <id>` / `post` / `help` / `quit`). **agora is a working BBS over the wire.** Linux today via `lib/io.cyr` + `lib/fs.cyr`. Remaining bites: C (sort), D (headers), E (boards), F (threads), G (lock), H (input validation). |
| M3 | Inline-image post bodies (ASCII-art conversion) | kii 1.0.0 ✅ — gated on M5 post bodies existing first |
| M4 | Stored-file deltas + compression | sankoch 2.2.6 ✅ — gated on M5 |
| M6 | User accounts + auth | sigil-backed identity ✅ (sigil 3.4.2) — naturally follows M5 |
| **1.0.0** | All six milestones green, multi-user telnet BBS | M0–M6 + iron validation on archaemenid LAN |

---

## Completed

### M0 — 0.1.0 (2026-05-23)

Repo scaffold shipped. argv dispatch + six stub verbs (`serve` / `post` / `list` / `read` / `whoami` / `version` / `help`). 43,216 B binary. `cyrius build src/main.cyr build/agora` clean; `help` and `version` exercise the dispatch.

Notes:

- Pre-M1: no networking, no persistence, no protocol code. Stub verbs print M-tagged hints and exit non-zero (except `version` / `help`).
- Greek naming lane introduced to the AGNOS ecosystem — ancient ἀγορά + Doja Cat "Agora Hills" (Scarlet, 2023) + Agoura Hills CA (hyperlocal to project's home base in Thousand Oaks). Multi-layer convergence per `kii`'s precedent.

### M1 — Telnet listener (closed 2026-05-23)

Five bites, all wire-conformant. Cross-platform via `lib/net.cyr` (Linux x86_64 + aarch64 day one; macOS/Windows/AGNOS as stdlib gains backends — [ADR 0001](../adr/0001-cross-platform-listener-decoupled-from-agnos.md)):

1. **First-bite** — RFC 854 IAC parser (`src/telnet.cyr`) + naive-refuse negotiation + listener loop in `cmd_serve` + 10-test conformance suite. Binary 56,064 B.
2. **Second-bite** — RFC 1143 Q-method option negotiation (`Q_NO` / `Q_WANTYES` / `Q_YES` per option per side, 512 B per connection) + `telnet_announce` 4-option opening salvo + slowloris timeout (`sock_set_recv_timeout(60s)`) + graceful EOF/error close. 15 tests; 59,280 B.
3. **Third-bite** — RFC 1073 NAWS + RFC 1091 TERMINAL_TYPE subneg parsing into `term_cols`/`term_rows`/`term_type` fields; `ts_on_him_yes` hook auto-emits `IAC SB TT SEND IAC SE` when him-TT lands `Q_YES`. 20 tests; 61,152 B.
4. **Fourth-bite** — RFC 1184 LINEMODE promoted to tracked-him: peer `WILL LINEMODE` triggers `DO LINEMODE` + `IAC SB LINEMODE MODE (EDIT|TRAPSIG) IAC SE` 10-byte burst; MODE ACK mask captured; SLC parsed-and-ignored. 24 tests; 62,176 B.
5. **Close-bite** — `benches/bench_telnet.bcyr` (5 microbenchmarks via `lib/bench.cyr`) + first baseline in [`/BENCHMARKS.md`](../../BENCHMARKS.md): 10 ns plain byte, 73 ns tracked-IAC, 97 ns NAWS subneg, 132 ns announce salvo. 24 tests still green; 70,960 B (+8.8 KB from new stdlib deps).

End-to-end smoke via python TCP client runs the full handshake (announce → peer agree → server TT SEND → NAWS + TT IS + LINEMODE ACK → data echo) wire-conformant.

---

## In Progress

### M2 — ANSI BBS aesthetic

- **bannermanor** 1.0.1 ✅ — consumed at M2-A (operator-side `bnrmr "AGORA"` rendered into an embedded string constant; bannermanor patched 1.0.0 → 1.0.1 for ecosystem alignment on 2026-05-23).
- **darshana** 0.5.3 ✅ — consumed at M2-B as a pinned git dep. The functional SGR/cursor surface we need (the `_buf` primitives — `tty_sgr_buf`, `tty_sgr_reset_buf`, `tty_fg_rgb_buf`, ...) exists at 0.5.3; the original "needs ≥ 1.0" framing was a version-label restriction, not a functionality one.

Scope at this milestone: MOTD banner on connect, ANSI-colored prompt, basic cursor positioning for menu redraws. Single-color ANSI before 256-color/truecolor.

**Landed** at 0.2.0+ (un-tagged toward 0.3.0):

- **M2-A** (bannermanor): `bnrmr "AGORA"` block-font banner embedded in `src/main.cyr` as a string constant. Replaced the v0.2.0 plaintext one-line MOTD.
- **M2-B** (darshana): `render_motd(buf)` runs at connection time, wraps the banner lines in cyan (SGR 36), the version line in yellow (SGR 33), and the prompt in default fg via `tty_sgr_buf` / `tty_sgr_reset_buf`. Buffer-targeted primitives flush to the telnet socket in one `send_buf` call.
- **M2-C** (operator override): `agora serve [port] [--motd <path>]`. `load_motd_file` reads up to 4 KB via `lib/io.cyr` `file_read_all` once at startup; if loaded, `handle_client` sends those bytes verbatim, otherwise falls back to the default `render_motd`. Three failure modes warn-and-fall-back: missing path arg, read failure, zero-byte file.

**Optional remaining bite** (M2 functionally closes without it):

- **M2-D** — NAWS-aware width clamping. First concrete consumer of `term_cols` / `term_rows` from M1's subneg parser. Earned when banners wider than 80 columns enter the default set, or when a consumer reports rendering on narrow terminals.

---

## Backlog (gates met or near-met)

### M3 — Inline-image post bodies

- **kii** at 1.0.0 ✅ — image → ASCII-art conversion.

Scope: post bodies may include inline images that render as ASCII art over the telnet stream. Constrained to a max image size + terminal-width-aware downscale (consumes the NAWS data captured by M1's subneg parser) before kii dispatch.

### M4 — Stored-file deltas

- **sankoch** at 2.2.6 ✅ — lossless compression.

Scope: file attachments compressed on write, decompressed on read. Diff-based storage for post edits (only the delta against prior revision).

---

## Future

### M5 — Post persistence (in progress — promote to In Progress section above)

Boards / threads / messages stored as files. Cross-platform via `lib/io.cyr` + `lib/fs.cyr` — Linux x86_64 + aarch64 today, AGNOS becomes one target among many as the stdlib gains a backend per [ADR 0001](../adr/0001-cross-platform-listener-decoupled-from-agnos.md).

The previously-open questions resolved into [ADR 0002](../adr/0002-one-file-per-post-storage.md): **one file per post** (`<store>/<id>.txt`, monotonic-integer IDs, plaintext UTF-8); **single-writer lock** at M5-G (EXCL-flag guarantees no corruption today; lock guarantees no ID-race).

**M5-A landed 0.3.0+** (un-tagged toward 0.4.0): `src/board.cyr` + the three CLI verbs (`agora post` / `list` / `read`), each accepting `--store <path>` (default `./agora-data/`). 5 new tests covering `parse_post_id` + `build_post_path`. Full round-trip via CLI smoke. Binary 85,544 → 109,992 B.

**M5-B landed 0.3.0+** (un-tagged toward 0.4.0): in-session command interpreter over telnet. `handle_client` runs a line-buffered loop after the MOTD; supports `help` / `list` / `read <id>` / `post` (multi-line, `.`-terminated) / `quit`. `agora serve` grew `--store <path>`. agora is now a **working BBS over the wire** — connect with any telnet client, post a message, list, read. Binary 109,992 → 116,232 B.

**Remaining bites for M5 close**:

- **M5-C** — Sort post list by ID ascending (M5-A/B returns directory-iteration order).
- **M5-D** — RFC-822-shaped headers in the post file (Subject / From / Date). Header set picked once the wire-level post flow is real.
- **M5-E** — Boards (subdirectories: `<store>/<board>/<id>.txt`).
- **M5-F** — Threads (post-replies-to-post linkage).
- **M5-G** — Single-writer lock (flock-style) for concurrent-writer correctness.
- **M5-H** — Input validation hardening (binary safety, max-line-width, control-char filtering on post bodies received over the wire).

### M6 — User accounts + auth

**sigil** at 3.4.2 ✅ — sigil-backed identity. Account state stored in the post tree (M5 prerequisite). Auth via sigil's challenge / response primitives.

Scope: login (handle + sigil-derived secret), `whoami`, per-board posting permissions. Out of scope: federated identity, web-of-trust. Pre-1.0 BBS auth is admission control, not full identity.

### 1.0.0 — Multi-user telnet BBS on iron

All six milestones green. Validation surface: archaemenid LAN — iron NUC running AGNOS with the agora binary serving telnet to a second box on the LAN. End-to-end exercise: connect → log in → list boards → read a thread → post a reply with an inline image → log off.

---

## v1.0 Criteria

A release qualifies for 1.0 when:

1. All six milestones M0–M6 have shipped and verified.
2. `cyrius audit` passes (build / lint / vet / deny / test / bench / doc).
3. Telnet validation on archaemenid LAN — two-box exercise above.
4. RFC 854 + RFC 1184 conformance: `src/test.cyr` covers the canonical sequences from both RFCs.
5. Multi-user concurrency: simulated 8-user fanout, no message loss, no state corruption.
6. Security audit in `docs/audit/YYYY-MM-DD-audit.md` cleared — input validation on every IAC sequence, no buffer overflows in the protocol parser, no command injection in post storage.

---

## Post-v1.0 Directions

Six pillars for the v2.x sovereignty layer — identity continuity (sigil-portable Ed25519), content-addressed storage, threat-level node policy (SecureYeoman vocabulary), federation by interest (topics, not platforms), self-distribution baked into the protocol, and offline-tolerant store-and-forward. Consolidated from a 2026-05-23 design session and detailed in [`roadmap-future.md`](roadmap-future.md). Items are **unpinned** — they pull forward into a numbered minor when consumer pressure or operator demand surfaces, not on a calendar.

## Cross-references

- [`docs/development/state.md`](state.md) — live state snapshot (current version, binary size, in-flight slot).
- [`docs/development/roadmap-future.md`](roadmap-future.md) — v2.x sovereignty pillars (post-v1.0, unpinned).
- [`docs/adr/`](../adr/) — decisions made along the way.
- [`docs/architecture/`](../architecture/) — non-obvious invariants the code relies on.
- [`CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.

---

## Companion project

**MUD userland** — separate repo, shares the telnet listener primitive but adds real-time room/object model. Same wire-protocol substrate, different application semantics. Both surface the AGNOS 1.32.x networking arc to real users.
