# agora — Roadmap

> **Last Updated**: 2026-05-23
>
> Versioned milestones through v1.0. Per [first-party-documentation § Development Docs](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#development-docs-docsdevelopment), this file lists what's shipped, what's next, what's deferred, and the v1.0 criteria. Per-tag chronology lives in [`CHANGELOG.md`](../../CHANGELOG.md); current state in [`state.md`](state.md).

agora is the BBS userland for AGNOS — Greek ἀγορά (civic-marketplace / public-assembly). The project is **cross-platform from M1**: built on cyrius `lib/net.cyr` socket primitives + `lib/io.cyr` / `lib/fs.cyr` storage, Linux today, AGNOS becomes one target among many as the stdlib gains backends ([ADR 0001](../adr/0001-cross-platform-listener-decoupled-from-agnos.md)).

---

## Release plan

| Tag | Theme | Status |
|---|---|---|
| **0.1.0** | M0 — scaffold | ✅ 2026-05-23 |
| **0.2.0** | M1 — cross-platform telnet listener (RFC 854 / 1143 / 1073 / 1091 / 1184) | ✅ 2026-05-23 |
| **0.3.0** | M2 — ANSI BBS aesthetic (bannermanor MOTD + darshana SGR + `--motd`) | ✅ 2026-05-23 |
| **0.4.0** | M5 partial — single-board post persistence (ADRs 0002 / 0003) | ✅ 2026-05-23 |
| **0.5.0** | M5 close — boards + threads (ADRs 0004 / 0005) | ✅ 2026-05-23 |
| **0.6.0** | M6 — sigil-backed auth + per-board policy (ADR 0006) | ✅ 2026-05-23 |
| **0.7.0** | Security sweep — external CVE / 0-day research + code audit | ← next cycle |
| **0.8.0** | Hardening + v1 lockdown — ABI freeze, doc-pass, perf re-run |  |
| **1.0.0** | Iron validation on archaemenid LAN |  |

---

## In progress

### 0.7.0 — pre-1.0 security sweep

A dedicated audit cycle per CLAUDE.md's "Security Hardening" + "Closeout Pass" sections. Inputs: existing M6-close re-scan in CHANGELOG [0.6.0], ADR 0006 threat model, BSD telnetd CVE history (CVE-2020-10188 buffer overflow, CVE-2011-4862 encryption key exchange overflow), modern BBS / Matrix / Mastodon attack surface, sigil 3.1.1 known-issues review.

Audit surfaces to walk:

- **IAC parser** (`src/telnet.cyr`) — RFC 854 / 1143 / 1073 / 1091 / 1184 state machines, all byte-level paths bounds-checked, no buffer-cap violations under malformed input.
- **Post storage** (`src/board.cyr`) — `parse_post_id`, `build_post_path`, `board_name_valid`, `input_byte_ok`, header parse / format, per-board policy decision in `board_can_post`.
- **Auth surface** (`src/account.cyr` + `src/main.cyr` MODE_LOGIN_AWAIT_SIG) — challenge / nonce / sig hex validation; `From:` header injection vectors via crafted handle; `keyfile_load_seed` size checks; per-board policy bypass paths.
- **Session globals** — `g_session_fp` / `g_session_handle` / `g_login_*` initialization and reset paths; ensure no leak between connections (single-tracking accept loop today, but the audit should be concurrent-accept-aware so we're not surprised when that lands).

Output: `docs/audit/2026-XX-XX-audit.md` with severity-rated findings. CRITICAL / HIGH get fixed in 0.7.x; remaining queue for 0.8 v1-hardening.

**Deferred from M6-close (queue for 0.7.x):**

- 30 s explicit deadline on parked login challenge (currently relies on `RECV_TIMEOUT_SECS = 60` slowloris drop)
- `agora policy set <board> <mode>` + `agora admins {add,rm,list}` CLI verbs (M6-F leaves operators to edit `.policy` / `.admins` files directly)
- `docs/guides/getting-started.md` + `docs/examples/` rewrite covering the M6 surface

---

## Backlog (gates met, no current consumer)

- **M3** — Inline-image post bodies via kii 1.0.0 (ASCII-art conversion). Pulls when a consumer asks for it.
- **M4** — Stored-file deltas via sankoch 2.2.6 (compressed diff-based post-edit storage). Pulls when post-edit becomes a feature.

Both are gates-met but ship-deferred. Lots of value but no v1.0 dependency. Slated for v1.x bites if real BBS use surfaces the need.

---

## Closed milestones

Detail per release lives in [`CHANGELOG.md`](../../CHANGELOG.md); per-bite narrative in `state.md`'s "Recent shipped". Brief table here for the roadmap-skim case:

- **M0** (0.1.0) — argv dispatch, six stub verbs, 43 KB scaffold binary.
- **M1** (0.2.0) — five-bite telnet listener: IAC parser, Q-method negotiation, NAWS + TT subneg, LINEMODE, bench harness. 10 ns/byte hot path.
- **M2** (0.3.0) — three-bite ANSI aesthetic: bannermanor MOTD, darshana SGR colors, `--motd` operator override. Bannermanor patched 1.0.1 same-day for ecosystem alignment on darshana 0.5.3.
- **M5** (0.4.0 + 0.5.0) — eight-bite post persistence. Single-board (0.4.0): storage primitives, in-session command interpreter, sorted listing, RFC-822 headers, per-store flock, ingress filter. Multi-board threaded (0.5.0): boards, Reply-To threading. Four ADRs total (0002, 0003, 0004, 0005).
- **M6** (0.6.0) — six-bite sigil-backed auth + per-board policy. ADR 0006 (identity model) + `src/account.cyr` primitives (M6-B) + telnet `login` challenge/response (M6-C) + `keygen`/`register`/`whoami` CLI + telnet `whoami` (M6-D) + `From:` post header (M6-E) + per-board `.policy` / `.admins` (M6-F). Adds sigil + freelist + bigint + ct to stdlib deps; 49 → 70 tests; 140 → 375 KB binary.

---

## v1.0 criteria

A release qualifies for 1.0 when:

1. M0–M6 + security sweep + hardening have all shipped at least once.
2. `cyrius audit` passes from a clean build (lint / test / bench / doc).
3. Telnet validation on archaemenid LAN — iron NUC running AGNOS serves telnet to a second box; end-to-end exercise: connect → log in → list boards → read a thread → post a reply → log off.
4. Multi-user concurrency: simulated 8-user fanout, no message loss, no state corruption.
5. Security audit (0.7.0) findings all closed in 0.8.0 hardening.
6. RFC conformance: `src/test.cyr` covers the canonical sequences from RFCs 854 / 1143 / 1073 / 1091 / 1184.

---

## Post-v1.0 directions

Six pillars for the v2.x sovereignty layer — identity continuity (sigil-portable Ed25519), content-addressed storage, threat-level node policy (SecureYeoman vocabulary), federation by interest (topics, not platforms), self-distribution baked into the protocol, and offline-tolerant store-and-forward. Detail in [`roadmap-future.md`](roadmap-future.md). Items are **unpinned** — they pull forward into a numbered minor when consumer pressure or operator demand surfaces, not on a calendar.

---

## Companion project

**MUD userland** — separate repo, shares the telnet listener primitive but adds a real-time room/object model. Same wire-protocol substrate, different application semantics.

## Cross-references

- [`docs/development/state.md`](state.md) — live state snapshot (current version, binary size, in-flight slot, **next-session boot guide**).
- [`docs/development/roadmap-future.md`](roadmap-future.md) — v2.x sovereignty pillars (post-v1.0, unpinned).
- [`docs/adr/`](../adr/) — five ADRs as of 0.5.0 (cross-platform listener / one-file-per-post / RFC-822 headers / board layout / Reply-To threading).
- [`docs/doc-health.md`](../doc-health.md) — fresh/stale ledger across the whole doc tree.
- [`CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.
