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
| **0.8.x** | Audit followups (L1 keyfile mode, M4 anon board-create, sigil version diff), ABI freeze, doc-pass | ← next cycle |
| **1.0.0** | Iron validation on archaemenid LAN |  |

---

## In progress

### 0.8.x — remaining 0.8 cycle bites

**0.8.0 shipped just bite E** (concurrent-accept) — the structural change that closes audit M1 + M2. The other bites from the 0.8 cycle plan are queued for 0.8.x patches, in recommended order:

- **0.8-A — keyfile mode warn-on-load** (audit L1). `fstat` after `keyfile_load_seed` open; warn on stderr if mode & 0o077 != 0. Don't refuse — containers legitimately use world-readable mounts.
- **0.8-C — sigil 3.1.1 → 3.4.3 release-notes diff read.** Verify `ed25519_verify` constant-time guarantee; scan for crypto fixes between bundled (3.1.1) and standalone tip (3.4.3). Bump sigil if any HIGH-or-up issue lands.
- **0.8-B — anonymous board-create gate** (audit M4). Today an unauthenticated client can spam `enter <name>` to mkdir arbitrary subdirectories under the store. Fix: require auth for `board_ensure` from the wire, OR add an accept-loop rate limit. (Both mitigations are orthogonal.)
- **0.8-D — ABI freeze decision** (likely new ADR 0008). `post_format_with_headers` is at 8 args; decide whether to freeze the current shape OR refactor to a params-struct before 1.0.
- **0.8-F — guides + examples doc-pass** (deferred from M6 close + 0.7.x). Rewrite `docs/guides/getting-started.md` + `docs/examples/` to cover the 0.8.0 surface (concurrent fork, M6 auth, the 5 0.7.0 audit-hardenings, the new ADR 0007 concurrency model).
- **0.8-G — perf re-run + final closeout sweep**. Re-capture bench numbers (parser hot path expected unchanged — fork is pre-IAC), full CLAUDE.md "Closeout Pass" §1-11 against the 0.8.x tip, prep for 1.0 cut.

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
- [`docs/adr/`](../adr/) — **seven ADRs as of 0.8.0** (cross-platform listener / one-file-per-post / RFC-822 headers / board layout / Reply-To threading / identity model / **fork-per-accept concurrency**). 0.7.0 added no new ADR (the audit doc is the record); 0.8.0 added ADR 0007.
- [`docs/audit/`](../audit/) — security audit ledger; first entry 2026-05-23 (0.7.0 sweep).
- [`docs/doc-health.md`](../doc-health.md) — fresh/stale ledger across the whole doc tree.
- [`CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.
