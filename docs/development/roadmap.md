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
| **0.7.0** | Security sweep — external CVE / 0-day research + code audit | ✅ 2026-05-23 |
| **0.8.0** | Hardening + v1 lockdown — concurrent-accept refactor, per-conn memory arenas, ABI freeze, doc-pass, perf re-run | ← next cycle |
| **1.0.0** | Iron validation on archaemenid LAN |  |

---

## In progress

### 0.8.0 — v1 hardening + ABI freeze + concurrent-accept refactor

Per the 0.7.0 audit's deferred queue (see [`docs/audit/2026-05-23-audit.md`](../audit/2026-05-23-audit.md) § "Deferred to 0.8 v1-hardening"), this cycle closes the memory + concurrency story before the 1.0 cut:

- **Concurrent-accept refactor + per-conn memory arenas** (audit M1 + M2). `alloc()` is bump-only; long-running serve accretes ~73 KB / connection + ~100 KB / `read`. Co-scheduled work: move identity slots (`g_session_*` / `g_login_*`) and per-command working buffers into a per-connection arena freed at `sock_close`. Once concurrent-accept lands, the login-challenge slot-collision (M2) is no longer "theoretical" — same refactor closes both.
- **Anonymous board-create gate** (audit M4). Today an unauthenticated client can spam `enter <name>` to mkdir arbitrary subdirectories under the store. Fix: require auth for `board_ensure` from the wire, OR add an accept-loop rate limit. (Possibly both — they're orthogonal mitigations.)
- **Keyfile mode warn-on-load** (audit L1). `fstat` the keyfile after open; warn on stderr if mode & 0o077 != 0. Don't refuse — containers legitimately use world-readable mounts.
- **sigil 3.1.1 → 3.4.3 release-notes diff read.** Verify `ed25519_verify` constant-time guarantee; scan for crypto fixes between bundled and tip. Bump sigil if any HIGH-or-up issue lands in the diff.

Plus the doc + ABI work:

- **Guides + examples refresh** (deferred from M6 close, re-queued from 0.7.x). Rewrite `docs/guides/getting-started.md` + `docs/examples/` to cover the 0.7.0 surface (build, telnet flow, CLI verbs, the 5 audit-hardenings as security-features-not-bugs).
- **ABI freeze** — the `post_format_with_headers` signature has grown twice (M5-F Reply-To, M6-E From) and will grow once more at v1 if any header is added. Decide at 0.8 cycle-open whether to freeze the current 8-arg shape OR refactor to a params-struct.
- **Perf re-run** — re-capture bench numbers post-concurrent-accept; document any regression in BENCHMARKS.md.
- **Final closeout sweep** — CHANGELOG / state.md / roadmap.md / doc-health.md all reconciled; 1.0 criteria (below) re-checked top-to-bottom.

**Deferred from 0.7.0 (queue for 0.7.x patches if a real deployment surfaces the need, otherwise 0.8):**

- `agora policy set <board> <mode>` + `agora admins {add,rm,list}` CLI verbs (operators currently edit `.policy` / `.admins` files directly).

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
- **0.7.0 security sweep** (0.7.0) — first dedicated audit cycle. Full report at [`docs/audit/2026-05-23-audit.md`](../audit/2026-05-23-audit.md). Zero CRITICAL. 5 fixes landed: H1 CLI subject CRLF injection (`cmd_post`), H2 cmd_list/cmd_read --board path-traversal, H3 `post_from` re-validates handle + fp on read (defense vs. tampered user files), M3 `parse_post_id` 18-digit overflow guard, M6 30s explicit deadline on parked login challenge (deferred from M6-C). 4 items queued for 0.8 (concurrent-accept + per-conn memory arenas; anonymous board-create gate; keyfile mode warn-on-load; sigil 3.1.1 → 3.4.3 diff). 70 → 78 tests; 375 → 377 KB binary (+0.6%); no new stdlib deps.

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
- [`docs/adr/`](../adr/) — six ADRs as of 0.6.0 (cross-platform listener / one-file-per-post / RFC-822 headers / board layout / Reply-To threading / identity model). 0.7.0 added no new ADR — the audit doc is the record.
- [`docs/audit/`](../audit/) — security audit ledger; first entry 2026-05-23 (0.7.0 sweep).
- [`docs/doc-health.md`](../doc-health.md) — fresh/stale ledger across the whole doc tree.
- [`CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.
