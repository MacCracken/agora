---
name: agora Documentation Health
description: Living state of doc currency in the agora repo — fresh / stale / archived / open-question, refreshed as docs are touched
type: state
---

# Documentation Health — agora

> **Last refresh**: 2026-05-23 (post-0.5.0 ship — M5 closed; pre-handoff cleanup of roadmap + state.md; next cycle is M6 → 0.6.0 sigil-backed auth) | **Refresh cadence**: when docs are touched, update the affected row.
> **Scope**: This repo only (`agora`) — the entire `docs/` tree plus root-level files (README, CHANGELOG, CLAUDE.md, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, LICENSE, VERSION). Per-stdlib-dep docs live in their own repos and are not audited here.
>
> **Convention adopted from cyrius** (2026-05-23): pattern from `cyrius/docs/doc-health.md`, scaled down for agora's early-stage tree (~12 markdown files vs. cyrius's ~105). Per [first-party-documentation § Development Docs](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#development-docs-docsdevelopment), the doc-health ledger is technically earned past ~30 docs — agora scaffolds it early to set the convention from day one and keep drift visible while the surface is small.

This is a **ledger**, not a one-time audit. Rewrite-in-place as docs change.

---

## At a glance — 2026-05-23 inventory (post-0.5.0)

**~17 markdown files** across the doc tree (+3 since v0.1.0: `roadmap-future.md`, `/BENCHMARKS.md`, three new ADRs 0003 / 0004 / 0005). Doc-tree cleanup pre-handoff: roadmap.md rewritten lean (release-tag table + actionable in-flight + backlog), state.md gained a **Next-session boot guide** for fresh agent reboots. **CI/release workflows** in place since 0.2.0. Bucket counts:

| Bucket | Count | What it means |
|---|---|---|
| ✅ **Fresh / touched in current cycle** | 10 | Refreshed at 0.5.0 ship + post-ship cleanup; ADR 0006 landed at M6 cycle-open. |
| 🟡 **Stale — refresh in place** | 2 | `docs/guides/getting-started.md` + `docs/examples/README.md` both predate M5 and read as 0.1.0-era. Earned but deferred; lands at M6 close or when a downstream first reads them. |
| 🟠 **Read-through outstanding** | 0 | None. |
| 🔵 **Probably evergreen** | 6 | All six ADRs (cross-platform listener / one-file-per-post / RFC-822 headers / board layout / Reply-To threading / identity model). |
| 📦 **Archive — frozen by design** | 0 | None. |
| ❓ **Open strategic question** | 0 | M6 identity model resolved by ADR 0006 (2026-05-23). Next open question opens with the 0.7.0 security-sweep cycle. |

Numbers exact post-0.5.0; rolls up from the per-tier tables below.

**Cleanup pass 2026-05-23**: roadmap.md trimmed 156 → 91 lines (removed bite-by-bite prose for closed cycles, which lives in CHANGELOG); state.md restructured to lead with the **Next-session boot guide** + M6 sketch (so a fresh agent boot picks up cleanly without re-deriving context). doc-health.md tier tables refreshed for the post-0.5.0 shape.

---

## Tier 1 — Root files

| File | Last touched | Status | Action |
|---|---|---|---|
| `README.md` | 2026-05-23 | ✅ Fresh | Landing page — etymology + status pointer + roadmap pointer + doc map. Roadmap table extracted to `docs/development/roadmap.md`. |
| `CHANGELOG.md` | 2026-05-23 | ✅ Fresh | **Source of truth per CLAUDE.md.** [0.1.0] scaffold + [0.2.0] M1 close + [0.3.0] M2 close + [0.4.0] M5 partial + [0.5.0] M5 close. [Unreleased] empty — next bite opens M6 cycle. |
| `BENCHMARKS.md` (root) | 2026-05-23 | ✅ Fresh | **New 2026-05-23 (M1 close)** — first parser baseline (5 microbenchmarks via `lib/bench.cyr`). Hand-maintained; `scripts/bench-history.sh` auto-gen pattern is the v1.x close-out goal. |
| `CLAUDE.md` | 2026-05-23 | ✅ Fresh | Durable rules. Volatile state delegated to `docs/development/state.md`. Per `example_claude.md` template. |
| `CONTRIBUTING.md` | 2026-05-23 | ✅ Fresh | Initial scaffold. Refresh when contributor workflow stabilizes post-M1. |
| `SECURITY.md` | 2026-05-23 | ✅ Fresh | Initial scaffold (reporting policy + scope). Audit findings go in `docs/audit/`. |
| `CODE_OF_CONDUCT.md` | 2026-05-23 | ✅ Fresh | Standard first-party scaffold. |
| `LICENSE` | 2026-05-23 | ✅ Fresh | GPL-3.0-only. |
| `VERSION` | 2026-05-23 | ✅ Fresh | `0.5.0`. Bumped via release flow. |
| `cyrius.cyml` | 2026-05-23 | ✅ Fresh | Toolchain pin `6.0.1`; deps list reflects current src surface. |

---

## Tier 2 — Operational / Development (`docs/development/`)

> **Important framing**: `state.md` + `roadmap.md` form the **canonical operational surface**. CLAUDE.md delegates volatile state to `state.md`, and `roadmap.md` is the slot-pinning artifact. These two rotate every release; everything else in this tier rotates per-need.

| File | Last touched | Status | Action |
|---|---|---|---|
| `state.md` | 2026-05-23 | ✅ Fresh | **Rotates every release.** 0.5.0 shipped (M5 closed). 49 tests; 140,160 B. **Restructured 2026-05-23 post-ship**: now leads with a "Next-session boot guide" + M6 sketch for fresh-agent handoff. Recent-shipped reduced to release-line summaries; per-bite narrative kept in CHANGELOG. |
| `roadmap.md` | 2026-05-23 | ✅ Fresh | **Trimmed 156 → 91 lines 2026-05-23 post-ship**: closed-cycle bite-by-bite prose removed (lives in CHANGELOG); now leads with the release-tag table + M6 in-progress + backlog. Release plan: 0.6 auth → 0.7 security sweep → 0.8 hardening → 1.0 ship. |
| `roadmap-future.md` | 2026-05-23 | ✅ Fresh | **New 2026-05-23 (M1 fourth-bite closeout)** — six unpinned v2.x sovereignty pillars (identity / content-addr / threat-level / topics / self-dist / offline). Pattern adopted from `cyrius/docs/development/roadmap-future.md`. Items pull forward on consumer pressure, not by calendar. |

Added when earned: `process-notes.md` (per-repo workflow specifics), `threat-model.md` (when M6 auth is in scope), `performance.md` (when M1 close adds bench numbers worth narrating), `issues/` (one file per deferred bug).

---

## Tier 3 — ADRs (`docs/adr/`)

6 ADRs. Re-read pass per minor closeout; ADRs document decisions, not status.

| File | Last touched | Status | Notes |
|---|---|---|---|
| `README.md` (index) | 2026-05-23 | ✅ Fresh | One-line hook per ADR. |
| `template.md` | 2026-05-23 | ✅ Fresh | Standard first-party template — status / context / decision / consequences / alternatives. |
| `0001-cross-platform-listener-decoupled-from-agnos.md` | 2026-05-23 | 🔵 Evergreen | Load-bearing — M1 listener uses `lib/net.cyr` on Linux today, not gated on agnos kernel. Decision propagated to M5 (file storage is the same shape — see ADR 0002). |
| `0002-one-file-per-post-storage.md` | 2026-05-23 | 🔵 Evergreen | **New at M5 cycle-open** — one file per post (`<store>/<id>.txt`, monotonic IDs, plaintext bodies). Rejects offset-index + WAL alternatives. Strict-prefix shape for the v2.x content-addressed graduation (pillar 2). |
| `0003-rfc-822-post-headers.md` | 2026-05-23 | 🔵 Evergreen | **New at M5-D** — RFC-822-shaped headers (Subject + Date) followed by blank line + body. Rejects JSON / CYML / TSV alternatives. Backwards-compatible with M5-A/B/C headerless posts via uppercase-first-byte sniffer. |
| `0004-board-layout.md` | 2026-05-23 | 🔵 Evergreen | **New at M5-E** — flat-root = "main", subdirs = named boards. Free backwards-compat with 0.4.0 stores. Modal current-board UI for telnet, `--board <name>` flag for CLI. Auto-create on first post. Rejects all-subdirs migration + sidecar index + per-port-board UI. |
| `0005-threading-via-reply-to.md` | 2026-05-23 | 🔵 Evergreen | **New at M5-F** — `Reply-To: <id>` header (same-board, ID-only); scan-on-read enumeration; RFC 5322 § 3.6.5 Re: subject prefix (no double). Rejects deep-threading via In-Reply-To+References, sidecar reply index, and cross-board values. |
| `0006-identity-model.md` | 2026-05-23 | 🔵 Evergreen | **New at M6 cycle-open** — sigil Ed25519 as identity primitive; `<store>/.users/<fp16>/` per-user directory; challenge/response wire flow (server nonce → client Ed25519 sig); anon-read + auth-post default; `From: <handle> <fp16>` header; `~/.agora/key` for the keyfile. Rejects ML-DSA at first cut, password hashes, sigil-managed account store, users.cyml sidecar, and federated/WoT identity (deferred to v2.x pillar 1). |

---

## Tier 4 — Architecture (`docs/architecture/`)

| File | Last touched | Status | Notes |
|---|---|---|---|
| `README.md` (index) | 2026-05-23 | ✅ Fresh | Empty index. Candidate first note from M5-D experience: paired-LF-after-CR session-buffer corruption (caught in M5-D smoke, fixed via the `consumed` flag in `handle_client`'s EOL detection). Worth capturing as a "this is non-obvious from the code alone" architecture note if M6 work touches the same byte-dispatch surface. |

---

## Tier 5 — Guides (`docs/guides/`)

| File | Last touched | Status | Action |
|---|---|---|---|
| `getting-started.md` | 2026-05-23 | 🟡 Stale | Last refresh predates M5 — still talks about the 0.1.0 stub `serve` verb. Needs a rewrite covering: build, `cyrius test`, `./build/agora serve 2323`, post / list / read / reply via telnet + CLI. Earned-but-deferred; lands at the M6 close (0.6.0) or as a standalone bite when an external contributor first reads it. |

---

## Tier 6 — Examples (`docs/examples/`)

| File | Last touched | Status | Action |
|---|---|---|---|
| `README.md` | 2026-05-23 | 🟡 Stale | Placeholder text predates M5; says "first example at M1". M5 close is the natural point to add a runnable Python TCP-client smoke (the same pattern that's been verifying every release in this session). Earned-but-deferred; lands when a downstream first asks how to script agora. |

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
| 2 | **getting-started.md + examples/ rewrite** — bring both up to the 0.5.0 multi-board threaded BBS shape; add a runnable Python TCP-client smoke as the first example. | M6 close (0.6.0) or first external-contributor read, whichever comes first | This file (Tier 5 + Tier 6) | Deferred 2026-05-23 post-ship; not blocking M6 work. |
| 3 | **Pre-1.0 security audit (0.7.0)** — full review of input validation across the IAC parser + post-storage path + auth surface. File in `docs/audit/YYYY-MM-DD-audit.md`. Web research on telnet/BBS CVEs (CVE-2020-10188, CVE-2011-4862, Mastodon/Matrix vulnerabilities). | 0.7.0 cycle (per release plan) | `CLAUDE.md` "Security Hardening" + roadmap.md release plan | Telnet is adversarial-by-default — any internet-reachable user can send arbitrary IAC sequences + posts. Audit surface widens at M6 (auth) and again at M5+ if any cross-board features land post-1.0. |
| 4 | **First architecture note** — candidate: paired-LF-after-CR session-buffer corruption fix from M5-D as a "non-obvious from code" invariant for future maintainers of the byte dispatch. | Next M6 bite that touches `handle_client`'s EOL handling, or M6 close | This file (Tier 4) | One-time; archive note here on completion. |

---

*Initial scaffold: 2026-05-23 (v0.1.0) — pattern adopted from cyrius/docs/doc-health.md per first-party-documentation.md § Development Docs. Refreshed at every release; cleanup sweep at 0.5.0 post-ship.*
