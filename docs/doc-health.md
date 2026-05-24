---
name: agora Documentation Health
description: Living state of doc currency in the agora repo — fresh / stale / archived / open-question, refreshed as docs are touched
type: state
---

# Documentation Health — agora

> **Last refresh**: 2026-05-23 (post-0.8.3 ship — anonymous board-create gate; audit M4 closed; **all 0.7.0 audit findings now discharged**) | **Refresh cadence**: when docs are touched, update the affected row.
> **Scope**: This repo only (`agora`) — the entire `docs/` tree plus root-level files (README, CHANGELOG, CLAUDE.md, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, LICENSE, VERSION). Per-stdlib-dep docs live in their own repos and are not audited here.
>
> **Convention adopted from cyrius** (2026-05-23): pattern from `cyrius/docs/doc-health.md`, scaled down for agora's early-stage tree (~12 markdown files vs. cyrius's ~105). Per [first-party-documentation § Development Docs](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#development-docs-docsdevelopment), the doc-health ledger is technically earned past ~30 docs — agora scaffolds it early to set the convention from day one and keep drift visible while the surface is small.

This is a **ledger**, not a one-time audit. Rewrite-in-place as docs change.

---

## At a glance — 2026-05-23 inventory (post-0.8.0)

**~20 markdown files** across the doc tree (+1 since 0.7.0: `docs/adr/0007-fork-per-accept-concurrency.md`). 0.8.0 closeout synced state.md / roadmap.md / CHANGELOG / this file in lockstep. **CI/release workflows** in place since 0.2.0. Bucket counts:

| Bucket | Count | What it means |
|---|---|---|
| ✅ **Fresh / touched in current cycle** | 8 | Refreshed at 0.8.0 close: state.md, roadmap.md, CHANGELOG, this file, VERSION, plus 3 inlined version literals in main.cyr. New: `docs/adr/0007-fork-per-accept-concurrency.md` + ADR README index row. |
| 🟡 **Stale — refresh in place** | 2 | `docs/guides/getting-started.md` + `docs/examples/README.md` still 0.1.0-era. Re-queued to 0.8-F (no real-deployment pressure surfaced; will land in the doc-pass bite). |
| 🟠 **Read-through outstanding** | 0 | None. |
| 🔵 **Probably evergreen** | 7 | All seven ADRs (cross-platform listener / one-file-per-post / RFC-822 headers / board layout / Reply-To threading / identity model / fork-per-accept concurrency). 0.8.0 added ADR 0007. |
| 📦 **Archive — frozen by design** | 0 | None. |
| ❓ **Open strategic question** | 0 | 0.8.0 concurrent-accept closed via fork (ADR 0007 settled all the design candidates). Next open question opens with 0.8-D (ABI freeze decision for `post_format_with_headers`) — may earn ADR 0008. |

Numbers exact post-0.8.0; rolls up from the per-tier tables below.

**0.8.0 close pass 2026-05-23**: full closeout per CLAUDE.md "Closeout Pass" §1-11. VERSION bumped 0.7.0 → 0.8.0; inline literals in main.cyr (`print_banner`, `cmd_version`, `render_motd`) bumped in lockstep; no new stdlib deps (`sys_fork` / `sys_waitpid` / `sys_exit` were already exposed); tests unchanged at 78/78 (E is in the accept loop, not unit-testable code); concurrency verified via the `/tmp/agora-concurrent-smoke.py` 3-session smoke; binary +336 B (+0.09%); ADR 0007 filed for the concurrency design; state.md next-session boot guide updated to the 0.8.x followup-bite queue.

---

## Tier 1 — Root files

| File | Last touched | Status | Action |
|---|---|---|---|
| `README.md` | 2026-05-23 | ✅ Fresh | Landing page — etymology + status pointer + roadmap pointer + doc map. Roadmap table extracted to `docs/development/roadmap.md`. |
| `CHANGELOG.md` | 2026-05-23 | ✅ Fresh | **Source of truth per CLAUDE.md.** [0.1.0] → [0.8.3] all entered. [0.8.3] is the anonymous board-create gate (audit M4 closed; **all 0.7.0 audit findings now discharged**; full status table in the entry). |
| `BENCHMARKS.md` (root) | 2026-05-23 | ✅ Fresh | Refreshed at 0.6.0 close — 5 telnet-parser benchmarks all within noise of M1-close baseline (M2-M6 are application-layer). Per-release history table added. |
| `CLAUDE.md` | 2026-05-23 | ✅ Fresh | Durable rules. Volatile state delegated to `docs/development/state.md`. Per `example_claude.md` template. |
| `CONTRIBUTING.md` | 2026-05-23 | ✅ Fresh | Initial scaffold. Refresh when contributor workflow stabilizes post-M1. |
| `SECURITY.md` | 2026-05-23 | ✅ Fresh | Initial scaffold (reporting policy + scope). Audit findings go in `docs/audit/`. |
| `CODE_OF_CONDUCT.md` | 2026-05-23 | ✅ Fresh | Standard first-party scaffold. |
| `LICENSE` | 2026-05-23 | ✅ Fresh | GPL-3.0-only. |
| `VERSION` | 2026-05-23 | ✅ Fresh | `0.8.3`. Bumped via release flow. |
| `cyrius.cyml` | 2026-05-23 | ✅ Fresh | Toolchain pin `6.0.1`; deps list grew to 20 stdlib modules at 0.6.0 (added sigil, freelist, bigint, ct for M6 sigil consumption). |

---

## Tier 2 — Operational / Development (`docs/development/`)

> **Important framing**: `state.md` + `roadmap.md` form the **canonical operational surface**. CLAUDE.md delegates volatile state to `state.md`, and `roadmap.md` is the slot-pinning artifact. These two rotate every release; everything else in this tier rotates per-need.

| File | Last touched | Status | Action |
|---|---|---|---|
| `state.md` | 2026-05-23 | ✅ Fresh | **Rotates every release.** 0.8.0 shipped (concurrent-accept via fork-per-connection; ADR 0007 landed; audit M1 + M2 closed). 78 tests; 377,520 B. Boot guide updated: next cycle is 0.8.x followup-bites (A/C/B/D/F/G in recommended order). Archived 0.8.0 + 0.7.0 + M6 in-flight notes kept for next-session reference. |
| `roadmap.md` | 2026-05-23 | ✅ Fresh | Refreshed at 0.8.0 close: 0.8.0 row marked ✅, "In progress" rewritten as **0.8.x — remaining 0.8 cycle bites** with A/C/B/D/F/G ordering. Release plan now shows 0.8.0 ✅ → 0.8.x → 1.0 ship. |
| `roadmap-future.md` | 2026-05-23 | ✅ Fresh | **New 2026-05-23 (M1 fourth-bite closeout)** — six unpinned v2.x sovereignty pillars (identity / content-addr / threat-level / topics / self-dist / offline). Pattern adopted from `cyrius/docs/development/roadmap-future.md`. Items pull forward on consumer pressure, not by calendar. |

Added when earned: `process-notes.md` (per-repo workflow specifics), `threat-model.md` (when M6 auth is in scope), `performance.md` (when M1 close adds bench numbers worth narrating), `issues/` (one file per deferred bug).

---

## Tier 3 — ADRs (`docs/adr/`)

7 ADRs. Re-read pass per minor closeout; ADRs document decisions, not status.

| File | Last touched | Status | Notes |
|---|---|---|---|
| `README.md` (index) | 2026-05-23 | ✅ Fresh | One-line hook per ADR. Refreshed at 0.8.0 for ADR 0007. |
| `template.md` | 2026-05-23 | ✅ Fresh | Standard first-party template — status / context / decision / consequences / alternatives. |
| `0001-cross-platform-listener-decoupled-from-agnos.md` | 2026-05-23 | 🔵 Evergreen | Load-bearing — M1 listener uses `lib/net.cyr` on Linux today, not gated on agnos kernel. Decision propagated to M5 (file storage is the same shape — see ADR 0002). |
| `0002-one-file-per-post-storage.md` | 2026-05-23 | 🔵 Evergreen | **New at M5 cycle-open** — one file per post (`<store>/<id>.txt`, monotonic IDs, plaintext bodies). Rejects offset-index + WAL alternatives. Strict-prefix shape for the v2.x content-addressed graduation (pillar 2). |
| `0003-rfc-822-post-headers.md` | 2026-05-23 | 🔵 Evergreen | **New at M5-D** — RFC-822-shaped headers (Subject + Date) followed by blank line + body. Rejects JSON / CYML / TSV alternatives. Backwards-compatible with M5-A/B/C headerless posts via uppercase-first-byte sniffer. |
| `0004-board-layout.md` | 2026-05-23 | 🔵 Evergreen | **New at M5-E** — flat-root = "main", subdirs = named boards. Free backwards-compat with 0.4.0 stores. Modal current-board UI for telnet, `--board <name>` flag for CLI. Auto-create on first post. Rejects all-subdirs migration + sidecar index + per-port-board UI. |
| `0005-threading-via-reply-to.md` | 2026-05-23 | 🔵 Evergreen | **New at M5-F** — `Reply-To: <id>` header (same-board, ID-only); scan-on-read enumeration; RFC 5322 § 3.6.5 Re: subject prefix (no double). Rejects deep-threading via In-Reply-To+References, sidecar reply index, and cross-board values. |
| `0006-identity-model.md` | 2026-05-23 | 🔵 Evergreen | **New at M6 cycle-open** — sigil Ed25519 as identity primitive; `<store>/.users/<fp16>/` per-user directory; challenge/response wire flow (server nonce → client Ed25519 sig); anon-read + auth-post default; `From: <handle> <fp16>` header; `~/.agora/key` for the keyfile. Rejects ML-DSA at first cut, password hashes, sigil-managed account store, users.cyml sidecar, and federated/WoT identity (deferred to v2.x pillar 1). |
| `0007-fork-per-accept-concurrency.md` | 2026-05-23 | 🔵 Evergreen | **New at 0.8.0** — fork-per-accept concurrency; process-exit memory cleanup; non-blocking waitpid zombie reaper. Closes audit M1 (bump-allocator memory growth) + M2 (login-challenge slot collision) via address-space isolation. Rejects thread-per-accept (M2 only closes with shared-state refactor), epoll event loop (yield-point burden on every byte handler), single-track-with-arena (only closes half the audit), per-conn freelist arena (kernel exit is strictly stronger free), `SIG_IGN` / `SA_NOCLDWAIT` auto-reap (sigaction trampoline trap on x86_64). |

---

## Tier 4 — Architecture (`docs/architecture/`)

| File | Last touched | Status | Notes |
|---|---|---|---|
| `README.md` (index) | 2026-05-23 | ✅ Fresh | Empty index. Candidate first note from M5-D experience: paired-LF-after-CR session-buffer corruption (caught in M5-D smoke, fixed via the `consumed` flag in `handle_client`'s EOL detection). Worth capturing as a "this is non-obvious from the code alone" architecture note if M6 work touches the same byte-dispatch surface. |

---

## Tier 5 — Guides (`docs/guides/`)

| File | Last touched | Status | Action |
|---|---|---|---|
| `getting-started.md` | 2026-05-23 | 🟡 Stale | Predates M5 — still talks about the 0.1.0 stub `serve` verb. Wants a rewrite covering the 0.6.0 surface: build, `cyrius test` (70/70), `./build/agora serve 2323`, post / list / read / reply via telnet + CLI, plus the M6 surface (`keygen` / `register` / `whoami` / `login`). Queued for 0.7.x per state.md "deferred from M6-close" list. |

---

## Tier 6 — Examples (`docs/examples/`)

| File | Last touched | Status | Action |
|---|---|---|---|
| `README.md` | 2026-05-23 | 🟡 Stale | Placeholder text predates M5; says "first example at M1". Re-queued from 0.7.x to 0.8 — no real-deployment pressure surfaced this cycle. The smoke-test scripts written during M5-F / M6-* / 0.7.0 audit-fix verification are reusable example skeletons; promoting them happens at 0.8 doc-pass. |

---

## Tier 7 — Audit (`docs/audit/`)

| File | Last touched | Status | Notes |
|---|---|---|---|
| `2026-05-23-audit.md` | 2026-05-23 | ✅ Fresh | **New at 0.7.0 cycle-open** — first agora security audit. Full line-by-line review of `src/telnet.cyr` + `src/board.cyr` + `src/account.cyr` + `src/main.cyr` against CLAUDE.md "Security Hardening" + external CVE history (CVE-2020-10188, CVE-2011-4862). Severity rubric (CRITICAL/HIGH/MEDIUM/LOW/DOCUMENTED); 5 actionable findings fixed in 0.7.0; 4 deferred to 0.8. Cadence per CLAUDE.md = once per minor / pre-release; next audit at 0.8 close before 1.0 cut. |

---

## Refresh procedure

When docs are touched:

1. Find the affected row in the relevant tier table.
2. Update **Last touched** to the new date.
3. Update **Status** if the bucket changed.
4. Update **Action** if the next step changed.
5. If a doc moved or was archived, update its row.
6. Re-anchor "Last refresh" date in the header.

When the bucket counts at the top drift by more than ~3 in any cell, refresh the at-a-glance table.

This file's refresh cadence is **opportunistic** (touched when other docs are touched), not periodic.

---

## What this file is NOT

- Not a substitute for [`development/state.md`](development/state.md) (which holds version + in-flight slot + gate state).
- Not a CHANGELOG (which records what shipped, not what's stale).
- Not a TODO list (open work for the project lives in [`development/roadmap.md`](development/roadmap.md)).
- Not a per-doc review log (this is the ledger of where each doc stands, not the per-doc reasoning).

---

## Forward doc-policy commitments

Items that are *scheduled* doc decisions, not stale state. Surfaced here so they aren't forgotten when the trigger date arrives.

| # | Commitment | Trigger | Source | Notes |
|---|---|---|---|---|
| 1 | **State.md refresh per release** — `docs/development/state.md` bumped at every tag with new version / size / in-flight slot. | Every release | `CLAUDE.md` "Closeout Pass" §9 | Manual until a release post-hook lands. |
| 2 | **getting-started.md + examples/ rewrite** — bring both up to the 0.7.0 multi-board threaded BBS + sigil-auth + per-board-policy + audit-hardened-input shape; promote the M6-* and 0.7.0-audit-fix smoke scripts into runnable `docs/examples/` skeletons. | 0.8 doc-pass (re-queued from 0.7.x; no real-deployment pressure surfaced) | This file (Tier 5 + Tier 6) + state.md "0.8 in-flight slot" | Re-queued at 0.7.0 ship 2026-05-23. |
| 3 | **Pre-1.0 security audit (0.7.0)** — full review of input validation across the IAC parser + post-storage path + auth surface. | ✅ Completed at 0.7.0 ship (2026-05-23) | `CLAUDE.md` "Security Hardening" + roadmap.md release plan | See [`audit/2026-05-23-audit.md`](audit/2026-05-23-audit.md). 5 fixes landed; 4 deferred to 0.8. Next audit at 0.8 close per cadence (once per minor / pre-release). |
| 4 | **First architecture note** — candidate: paired-LF-after-CR session-buffer corruption fix from M5-D as a "non-obvious from code" invariant for future maintainers of the byte dispatch. | Next M6 bite that touches `handle_client`'s EOL handling, or M6 close | This file (Tier 4) | One-time; archive note here on completion. |

---

*Initial scaffold: 2026-05-23 (v0.1.0) — pattern adopted from cyrius/docs/doc-health.md per first-party-documentation.md § Development Docs. Refreshed at every release; cleanup sweeps at 0.5.0 + 0.6.0 post-ship.*
