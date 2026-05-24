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
| **0.8.0** | Concurrent accept via fork-per-connection (ADR 0007) — audit M1 + M2 closed | ✅ 2026-05-23 |
| **0.8.1** | Keyfile mode warn-on-load (audit L1 closed) | ✅ 2026-05-23 |
| **0.8.2** | Sigil 3.1.1 → 3.4.3 release-notes diff (no bump; 0.7.0 deferred item discharged) | ✅ 2026-05-23 |
| **0.8.3** | Anonymous board-create gate (audit M4 closed — all 0.7.0 audit findings now discharged) | ✅ 2026-05-23 |
| **0.9.0** | PostHeaders struct ABI freeze (ADR 0008) | ✅ 2026-05-23 |
| **0.9.1** | Guides + examples doc-pass (F) — long-deferred Tier 5 + Tier 6 rewrite + 6 runnable example scripts | ✅ 2026-05-23 |
| **0.9.2** | Perf re-run + final 1.0 closeout sweep (G) — CLAUDE.md "Closeout Pass" §1-11 | ✅ 2026-05-23 |
| **1.0.0** | Iron-validated on archaemenid LAN — criterion #3 telnet round-trip + criterion #4 8-user fanout both green | ✅ 2026-05-23 |

---

## In progress

**No active cycle.** agora 1.0.0 shipped 2026-05-23 — iron-validated on archaemenid; all six v1.0 criteria met. The git tag itself is the user's call per CLAUDE.md "do not commit or push". Post-1.0 directions live below + in [`roadmap-future.md`](roadmap-future.md), all unpinned.

**Deferred from 0.7.0 (still queued; pull when a deployment asks):**

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
- **0.8.0 concurrent-accept** (0.8.0) — fork-per-connection accept loop via [ADR 0007](../adr/0007-fork-per-accept-concurrency.md). Audit M1 (bump-allocator memory growth) + M2 (login-challenge slot collision) both close via process isolation — kernel reclaims per-child memory at `sys_exit`; globals are per-process post-fork. Loop: `sys_waitpid(-1, NULL, WNOHANG)` reaper → `sock_accept` → `sys_fork` → child runs handle_client + `sys_exit(0)` / parent loops. Audit M4 (anonymous board-create) carried forward to 0.8-B — independent of concurrency model. 78 tests unchanged (E is in the accept loop, not unit-testable code); 377 → 378 KB binary (+0.09%); no new stdlib deps.

---

## v1.0 criteria — ✅ all met (2026-05-23)

A release qualifies for 1.0 when:

1. **M0–M6 + security sweep + hardening have all shipped at least once.** ✅ — shipped across 0.1.0 → 0.9.2 (eighteen tags).
2. **`cyrius audit` passes from a clean build (lint / test / bench / doc).** ✅ — 80/80 tests; 5 benches within noise of M1-close baseline; clean DCE build at 378,456 B.
3. **Telnet validation on archaemenid LAN — iron NUC running AGNOS serves telnet to a second box; end-to-end exercise: connect → log in → list boards → read a thread → post a reply → log off.** ✅ — `docs/examples/05-telnet-login.sh 2323` ran on archaemenid 2026-05-23: `login qix` → openssl-signed `auth:` → server `welcome, qix` → `whoami` reports `qix 878873ab607321a5`.
4. **Multi-user concurrency: simulated 8-user fanout, no message loss, no state corruption.** ✅ — `docs/examples/04-concurrent-smoke.py 2323 8` ran on archaemenid 2026-05-23: 8/8 sessions OK (each got banner + IAC + boards reply with no cross-talk; ADR 0007 fork-per-accept process isolation confirmed at fanout).
5. **Security audit (0.7.0) findings all closed in 0.8.0 hardening.** ✅ — H1/H2/H3 + M3 + M6 at 0.7.0; M1+M2 at 0.8.0; L1 at 0.8.1; M4 at 0.8.3. All discharged; sigil 3.1.1 → 3.4.3 diff at 0.8.2 found no upgrade-warranted findings.
6. **RFC conformance: `src/test.cyr` covers the canonical sequences from RFCs 854 / 1143 / 1073 / 1091 / 1184.** ✅ — t01–t24 (IAC parser + Q-method + NAWS + TT + LINEMODE conformance suite); 56 additional tests for storage + auth + policy + audit regressions.

---

## Post-v1.0 directions

Six pillars for the v2.x sovereignty layer — identity continuity (sigil-portable Ed25519), content-addressed storage, threat-level node policy (SecureYeoman vocabulary), federation by interest (topics, not platforms), self-distribution baked into the protocol, and offline-tolerant store-and-forward. Detail in [`roadmap-future.md`](roadmap-future.md). Items are **unpinned** — they pull forward into a numbered minor when consumer pressure or operator demand surfaces, not on a calendar.

---

## Companion project

**MUD userland** — separate repo, shares the telnet listener primitive but adds a real-time room/object model. Same wire-protocol substrate, different application semantics.

## Cross-references

- [`docs/development/state.md`](state.md) — live state snapshot (current version, binary size, in-flight slot, **next-session boot guide**).
- [`docs/development/roadmap-future.md`](roadmap-future.md) — v2.x sovereignty pillars (post-v1.0, unpinned).
- [`docs/adr/`](../adr/) — **eight ADRs as of 0.9.0** (cross-platform listener / one-file-per-post / RFC-822 headers / board layout / Reply-To threading / identity model / fork-per-accept concurrency / **PostHeaders struct ABI**). 0.7.0 added no new ADR (the audit doc is the record); 0.8.0 added ADR 0007; 0.9.0 added ADR 0008.
- [`docs/audit/`](../audit/) — security audit ledger; first entry 2026-05-23 (0.7.0 sweep).
- [`docs/doc-health.md`](../doc-health.md) — fresh/stale ledger across the whole doc tree.
- [`CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.
