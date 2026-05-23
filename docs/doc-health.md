---
name: agora Documentation Health
description: Living state of doc currency in the agora repo — fresh / stale / archived / open-question, refreshed as docs are touched
type: state
---

# Documentation Health — agora

> **Last refresh**: 2026-05-23 (v0.1.0 + M1 fourth-bite — initial scaffold + doc-tree adoption per first-party-documentation.md; updated through M1 LINEMODE bite) | **Refresh cadence**: when docs are touched, update the affected row.
> **Scope**: This repo only (`agora`) — the entire `docs/` tree plus root-level files (README, CHANGELOG, CLAUDE.md, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, LICENSE, VERSION). Per-stdlib-dep docs live in their own repos and are not audited here.
>
> **Convention adopted from cyrius** (2026-05-23): pattern from `cyrius/docs/doc-health.md`, scaled down for agora's early-stage tree (~12 markdown files vs. cyrius's ~105). Per [first-party-documentation § Development Docs](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#development-docs-docsdevelopment), the doc-health ledger is technically earned past ~30 docs — agora scaffolds it early to set the convention from day one and keep drift visible while the surface is small.

This is a **ledger**, not a one-time audit. Rewrite-in-place as docs change.

---

## At a glance — 2026-05-23 inventory (v0.1.0 doc-tree adoption)

**~12 markdown files** across the repo. First-party doc tree scaffolded today; everything fresh by construction. Bucket counts:

| Bucket | Count | What it means |
|---|---|---|
| ✅ **Fresh / touched in current cycle** | 12 | Whole tree written or refreshed at v0.1.0 doc-adoption pass. |
| 🟡 **Stale — refresh in place** | 0 | None — repo too young for drift. |
| 🟠 **Read-through outstanding** | 0 | None. |
| 🔵 **Probably evergreen** | 1 | ADR 0001 (cross-platform listener decoupled from AGNOS) — load-bearing principle for M1+. |
| 📦 **Archive — frozen by design** | 0 | None. |
| ❓ **Open strategic question** | 1 | When does M5's persistence layer earn its own ADR? Default: when the on-disk layout decision is made (one-file-per-post vs. one-file-per-thread + offset index). |

Numbers exact at v0.1.0; rolls up from the per-tier tables below.

**Why scaffolded now**: at v0.1.0 the surface is small enough that a doc-health pass is trivial; setting the convention early means no retroactive sweep is needed when the tree grows past the ~30-doc earn-threshold. Adopted from cyrius doc-health pattern (2026-05-19 reference) per the [user direction on 2026-05-23](#) (this session) — same shape as cyrius, scaled down for agora's stage.

---

## Tier 1 — Root files

| File | Last touched | Status | Action |
|---|---|---|---|
| `README.md` | 2026-05-23 | ✅ Fresh | Landing page — etymology + status pointer + roadmap pointer + doc map. Roadmap table extracted to `docs/development/roadmap.md`. |
| `CHANGELOG.md` | 2026-05-23 | ✅ Fresh | **Source of truth per CLAUDE.md.** v0.1.0 scaffold + [Unreleased] entries for all four M1 bites (cross-platform listener / Q-method / NAWS+TT subneg / RFC 1184 LINEMODE). |
| `CLAUDE.md` | 2026-05-23 | ✅ Fresh | Durable rules. Volatile state delegated to `docs/development/state.md`. Per `example_claude.md` template. |
| `CONTRIBUTING.md` | 2026-05-23 | ✅ Fresh | Initial scaffold. Refresh when contributor workflow stabilizes post-M1. |
| `SECURITY.md` | 2026-05-23 | ✅ Fresh | Initial scaffold (reporting policy + scope). Audit findings go in `docs/audit/`. |
| `CODE_OF_CONDUCT.md` | 2026-05-23 | ✅ Fresh | Standard first-party scaffold. |
| `LICENSE` | 2026-05-23 | ✅ Fresh | GPL-3.0-only. |
| `VERSION` | 2026-05-23 | ✅ Fresh | `0.1.0`. Bumped via release flow. |
| `cyrius.cyml` | 2026-05-23 | ✅ Fresh | Toolchain pin `6.0.1`; deps list reflects current src surface. |

---

## Tier 2 — Operational / Development (`docs/development/`)

> **Important framing**: `state.md` + `roadmap.md` form the **canonical operational surface**. CLAUDE.md delegates volatile state to `state.md`, and `roadmap.md` is the slot-pinning artifact. These two rotate every release; everything else in this tier rotates per-need.

| File | Last touched | Status | Action |
|---|---|---|---|
| `state.md` | 2026-05-23 | ✅ Fresh | **Rotates every release.** Tracks four M1 bites — binary 43,216 → 56,064 → 59,280 → 61,152 → 62,176 B; test count 0 → 10 → 15 → 20 → 24; only bench harness remains before M1 close. |
| `roadmap.md` | 2026-05-23 | ✅ Fresh | M0–M6 + v1.0 criteria. Extracted from `README.md` at v0.1.0 doc-tree adoption. |

Added when earned: `process-notes.md` (per-repo workflow specifics), `threat-model.md` (when M6 auth is in scope), `performance.md` (when M1 close adds bench numbers worth narrating), `issues/` (one file per deferred bug).

---

## Tier 3 — ADRs (`docs/adr/`)

1 ADR. Re-read pass per minor closeout; ADRs document decisions, not status.

| File | Last touched | Status | Notes |
|---|---|---|---|
| `README.md` (index) | 2026-05-23 | ✅ Fresh | One-line hook per ADR. |
| `template.md` | 2026-05-23 | ✅ Fresh | Standard first-party template — status / context / decision / consequences / alternatives. |
| `0001-cross-platform-listener-decoupled-from-agnos.md` | 2026-05-23 | 🔵 Evergreen | Load-bearing — M1 listener uses `lib/net.cyr` on Linux today, not gated on agnos kernel. Decision propagates to M5+ (file storage is the same shape). |

**Open question** — none open. Next decision likely lands when M5's on-disk layout is chosen (one file per post vs. one file per thread).

---

## Tier 4 — Architecture (`docs/architecture/`)

| File | Last touched | Status | Notes |
|---|---|---|---|
| `README.md` (index) | 2026-05-23 | ✅ Fresh | Empty index — first note lands at M1 when the IAC parser has an invariant worth capturing (e.g., partial-IAC buffering across `recv()` calls). |

---

## Tier 5 — Guides (`docs/guides/`)

| File | Last touched | Status | Action |
|---|---|---|---|
| `getting-started.md` | 2026-05-23 | ✅ Fresh | Build / run / smoke for the v0.1.0 scaffold. Refresh at M1 when `serve` becomes real. |

---

## Tier 6 — Examples (`docs/examples/`)

| File | Last touched | Status | Action |
|---|---|---|---|
| `README.md` | 2026-05-23 | ✅ Fresh | Placeholder. First runnable example earns its slot at M1 (telnet client smoke against agora). |

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
| 2 | **First architecture note at M1 close** — capture the partial-IAC-across-`recv()` buffering invariant when the parser lands. | M1 close | This file (Tier 4) | One-time; archive note here on completion. |
| 3 | **First security audit before M6 ship** — full review of input validation across the IAC parser + post-storage path. File in `docs/audit/YYYY-MM-DD-audit.md`. | Before M6 release | `CLAUDE.md` "Security Hardening" | Telnet is adversarial-by-default — any internet-reachable user can send arbitrary IAC sequences. |

---

*Initial scaffold: 2026-05-23 (v0.1.0) — pattern adopted from cyrius/docs/doc-health.md per first-party-documentation.md § Development Docs. Refresh in place when docs are touched.*
