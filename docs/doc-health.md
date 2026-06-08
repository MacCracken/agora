---
name: agora Documentation Health
description: Living state of doc currency in the agora repo — fresh / stale / archived / open-question, refreshed as docs are touched
type: state
---

# Documentation Health — agora

> **Last refresh**: 2026-06-08 (**1.3.1 PARRY CUT** — Colby's 1972 paranoid chatbot as Eliza's foil [`src/parry.cyr`, affect engine + Mafia/bookie delusion story]; `play parry` + private `/parry` [chat couch generalized to `g_chat_bot`]. VERSION → 1.3.1; three inline main.cyr literals; CHANGELOG [1.3.1]; state.md + roadmap.md synced; 160 tests; 752,240 B; **new smoke 13-parry.sh**. Pre-cut review verified the affect model faithful + fixed one rotation defect. Next: **1.3.2 QUEST**, **1.3.3 Jabberwacky**. Earlier same day: **1.3.0 Chat area + Eliza CUT** — all 3 ADR 0011 bites: the chat surface [`src/chat.cyr`, `MODE_CHAT`, seq-number live-tail], Eliza [`src/eliza.cyr`, `play eliza` door + private `/eliza` side-channel], closeout. VERSION → 1.3.0; three inline main.cyr literals; CHANGELOG [1.3.0]; **new ADR 0011**; toolchain pin 6.1.5 → 6.1.9; state.md + roadmap.md + roadmap-future.md synced; 155 tests; 730,792 B; **new smokes 11**[chat]**/12**[eliza]. Pre-cut multi-agent adversarial review fixed 3 defects. Roadmap: **1.3.1 PARRY**, **1.4.0 Descent link**, **QUEST** [LORD homage door] all queued. Earlier same day: **1.2.0 Persistent Universe** [ADR 0010]). Prior: 2026-06-07 (**1.1.0 — door / games**; ADR 0009). | **Refresh cadence**: when docs are touched, update the affected row.
> **Scope**: This repo only (`agora`) — the entire `docs/` tree plus root-level files (README, CHANGELOG, CLAUDE.md, CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md, LICENSE, VERSION). Per-stdlib-dep docs live in their own repos and are not audited here.
>
> **Convention adopted from cyrius** (2026-05-23): pattern from `cyrius/docs/doc-health.md`, scaled down for agora's early-stage tree (~12 markdown files vs. cyrius's ~105). Per [first-party-documentation § Development Docs](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#development-docs-docsdevelopment), the doc-health ledger is technically earned past ~30 docs — agora scaffolds it early to set the convention from day one and keep drift visible while the surface is small.

This is a **ledger**, not a one-time audit. Rewrite-in-place as docs change.

---

## At a glance — 2026-05-23 inventory (post-0.9.1)

**~27 markdown / script files** across the doc tree (+7 since 0.8.0: ADR 0008 + the six runnable example scripts; +1 since 0.9.0 if you count just the doc-pass narrative). **CI/release workflows** in place since 0.2.0. Bucket counts:

| Bucket | Count | What it means |
|---|---|---|
| ✅ **Fresh / touched in current cycle** | 11 | Refreshed at 0.9.1: this file, state.md, roadmap.md, CHANGELOG, VERSION, three inlined literals in main.cyr, **rewritten** `docs/guides/getting-started.md`, **rewritten** `docs/examples/README.md`, plus **six new runnable example scripts** (01 build-and-test, 02 register-and-post, 03 anonymous-read, 04 concurrent-smoke.py, 05 telnet-login, 06 board-policy). Every example verified end-to-end against `./build/agora`. |
| 🟡 **Stale — refresh in place** | 0 | **Closed at 0.9.1.** The two long-deferred rows (getting-started.md from M6-close → 0.7.x → 0.8.x; examples/README.md same trajectory) have both shipped fresh content. |
| 🟠 **Read-through outstanding** | 0 | None. |
| 🔵 **Probably evergreen** | 11 | All eleven ADRs (cross-platform listener / one-file-per-post / RFC-822 headers / board layout / Reply-To threading / identity model / fork-per-accept concurrency / PostHeaders ABI / door-games subsystem / persistent universe / **chat area**). 1.1.0 added ADR 0009; 1.2.0 added ADR 0010; **1.3.0 added ADR 0011**. |
| 📦 **Archive — frozen by design** | 0 | None. |
| ❓ **Open strategic question** | 0 | All design candidates settled through 0.9.0 (ADR 0008 closed the ABI question that opened in the 0.8-D slot). Next open question will surface when v1.x post-iron-validation work begins (deferred CLI verbs for policy / admins management may warrant an ADR if scope expands). |

Numbers exact post-0.9.1; rolls up from the per-tier tables below.

**1.0.0 cut 2026-05-23**: iron-validated on archaemenid. All six v1.0 criteria met (M0-M6 + cyrius audit ✅ + archaemenid telnet ✅ via `05-telnet-login.sh` + 8-user fanout ✅ via `04-concurrent-smoke.py 2323 8` + 0.7.0 audit closed ✅ + RFC conformance ✅). VERSION → 1.0.0; three inline literals in `src/main.cyr` bumped; full clean DCE build green at 378,456 B; CHANGELOG [1.0.0] release-narrative entry; README status pointer rewritten from "v0.1.0 scaffold + M1 in progress" → "v1.0.0 shipped, iron-validated"; state.md / roadmap.md fully synced; doc-health (this file) refreshed. Cosmetic fix caught during iron run: `05-telnet-login.sh` IAC drain rewritten as drain-and-print to preserve the top row of the bannermanor MOTD.

**1.1.0 door / games 2026-06-07**: a BBS door subsystem ([ADR 0009](adr/0009-door-games-subsystem.md)) with three text games on a shared pure-module framework — `src/door.cyr`, `src/smuggler.cyr`, `src/port_authority.cyr`, `src/handler.cyr` — wired into `main.cyr` via a `play` verb + `MODE_DOOR`. 80 → 121 unit tests (t81-t121); clean DCE build 484,184 B; verified playable over telnet (`07-play-door.sh`, the seventh example script). Docs synced: ADR 0009 (evergreen), CHANGELOG [1.1.0], VERSION → 1.1.0, three inline main.cyr version literals, state.md (version / artifacts / tests / in-flight / recent-shipped / source-surface), roadmap.md (1.1.0 row + in-progress), roadmap-future.md (door Persistent Universe + leaderboards section), README (status + architecture tree + examples count). Door **Persistent Universe** (shared multiplayer) + **leaderboards** remain the open door-subsystem question — they earn an ADR when a deployment pulls them forward.

**0.9.1 doc-pass 2026-05-23**: long-deferred Tier 5 / Tier 6 rewrite, finally landed. `docs/guides/getting-started.md` rewritten from 74-line 0.1.0 stub-verb walkthrough to a full 0.9.0 surface walkthrough (build → tests → listener → anon-read → keygen/register/post `--as` → telnet `login` → per-board policy → concurrency). `docs/examples/README.md` rewritten from 6-line placeholder to a 6-row example index. Six runnable example scripts written and each verified against the binary: 01 build+test passes; 02 register+post writes ./bbs/1.txt with `From: qix <fp16>`; 03 confirms anon-read works and anon-post correctly returns exit 1; 04 confirms 3 concurrent telnet sessions get independent banners + state; 05 drives the openssl-signed challenge/response flow to a `welcome, qix` from the server; 06 walks all three policy modes. Two doc-tightening fixes caught during verification: anonymous CLI post is **denied** at M6 (board_can_post returns 0 for session_fp==0, not just on `known`/`admin`), and main-board posts live at `<store>/N.txt` not `<store>/main/N.txt` (ADR 0004 flat-root). Both corrections propagated to guide + examples + policy table.

**0.8.0 close pass 2026-05-23**: full closeout per CLAUDE.md "Closeout Pass" §1-11. VERSION bumped 0.7.0 → 0.8.0; inline literals in main.cyr (`print_banner`, `cmd_version`, `render_motd`) bumped in lockstep; no new stdlib deps (`sys_fork` / `sys_waitpid` / `sys_exit` were already exposed); tests unchanged at 78/78 (E is in the accept loop, not unit-testable code); concurrency verified via the `/tmp/agora-concurrent-smoke.py` 3-session smoke; binary +336 B (+0.09%); ADR 0007 filed for the concurrency design; state.md next-session boot guide updated to the 0.8.x followup-bite queue.

---

## Tier 1 — Root files

| File | Last touched | Status | Action |
|---|---|---|---|
| `README.md` | 2026-05-23 | ✅ Fresh | **Rewritten at 1.0 cut.** Status pointer: "v1.0.0 shipped, iron-validated on archaemenid; all v1.0 criteria met". Planned-architecture box replaced with the actual 4-source-file architecture; examples + benchmarks links added. |
| `CHANGELOG.md` | 2026-06-08 | ✅ Fresh | **Source of truth per CLAUDE.md.** [0.1.0] → **[1.3.1]** entered. [1.3.1] = PARRY (affect-engine chatbot) + couch generalization + review-fix; [1.3.0] Chat area + Eliza (ADR 0011) + toolchain 6.1.5→6.1.9; [1.2.0] Persistent Universe (ADR 0010); [1.1.x] door games; [1.0.0] release-narrative. |
| `BENCHMARKS.md` (root) | 2026-05-23 | ✅ Fresh | Refreshed at 0.9.2 closeout — 5 telnet-parser benchmarks all within ±2 ns of M1-close baseline (every release between M6 and 0.9.2 was off-hot-path). 0.9.2 row added to per-release history. |
| `CLAUDE.md` | 2026-05-23 | ✅ Fresh | Durable rules. Volatile state delegated to `docs/development/state.md`. Per `example_claude.md` template. |
| `CONTRIBUTING.md` | 2026-05-23 | ✅ Fresh | Initial scaffold. Refresh when contributor workflow stabilizes post-M1. |
| `SECURITY.md` | 2026-05-23 | ✅ Fresh | Initial scaffold (reporting policy + scope). Audit findings go in `docs/audit/`. |
| `CODE_OF_CONDUCT.md` | 2026-05-23 | ✅ Fresh | Standard first-party scaffold. |
| `LICENSE` | 2026-05-23 | ✅ Fresh | GPL-3.0-only. |
| `VERSION` | 2026-06-08 | ✅ Fresh | `1.3.1`. Bumped via release flow. |
| `cyrius.cyml` | 2026-06-08 | ✅ Fresh | Toolchain pin **`6.1.9`** (realigned 6.1.5 → 6.1.9 at the 1.3.0 cut; earlier lifted from the 6.0.52 sigil-SIGILL cap; see state.md Version table). Deps list = 20 stdlib modules (no new deps at 1.3.0 — chat + Eliza are pure). |

---

## Tier 2 — Operational / Development (`docs/development/`)

> **Important framing**: `state.md` + `roadmap.md` form the **canonical operational surface**. CLAUDE.md delegates volatile state to `state.md`, and `roadmap.md` is the slot-pinning artifact. These two rotate every release; everything else in this tier rotates per-need.

| File | Last touched | Status | Action |
|---|---|---|---|
| `state.md` | 2026-06-08 | ✅ Fresh | **Rotates every release.** **1.3.1 CUT** — PARRY (160 tests; 752,240 B). Refresh line / Released / Build-artifacts / Tests / In-flight (PARRY summary + 1.3.2 QUEST / 1.3.3 Jabberwacky next) / Recent-shipped / Source-surface (+parry.cyr) rows synced. |
| `roadmap.md` | 2026-06-08 | ✅ Fresh | Release table: **1.3.1 ✅ PARRY**, **new 1.3.2 QUEST** + **1.3.3 Jabberwacky** (planned), 1.4.0 Descent link. "In progress" → 1.3.2 QUEST next. |
| `roadmap-future.md` | 2026-06-08 | ✅ Fresh | **Touched at 1.3.0** — added § **Chatbot personalities** (ALICE / Racter / MegaHAL / Jabberwacky beyond Eliza+PARRY) and the **QUEST** LORD-homage door spec under § Door games (full 12-level Great-Work arc + Emerald-Tablet spine). Plus the original six unpinned v2.x sovereignty pillars. |

Added when earned: `process-notes.md` (per-repo workflow specifics), `threat-model.md` (when M6 auth is in scope), `performance.md` (when M1 close adds bench numbers worth narrating), `issues/` (one file per deferred bug).

---

## Tier 3 — ADRs (`docs/adr/`)

11 ADRs. Re-read pass per minor closeout; ADRs document decisions, not status.

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
| `0008-post-headers-struct.md` | 2026-05-23 | 🔵 Evergreen | **New at 0.9.0** — pre-1.0 ABI freeze. `PostHeaders` struct (PH_SUBJECT / PH_REPLY_TO / PH_FROM_HANDLE / PH_FROM_FP at i64 offsets) replaces the M5-D → M5-F → M6-E positional-arg accretion (5 → 6 → 8 args). New v1.0 surface: `post_format(ph, body, body_len, out, cap)` + `post_new(store, board, ph, body, body_len)`. Future headers (federated Origin, content-hash) add `PH_*` offset + setter without changing call shape. Rejects freeze-8-arg-as-is (variant-fn proliferation), heap-buffer + offset table (pushes formatting up), varargs emulation (no win), shim retention (CLAUDE.md anti-pattern). |
| `0009-door-games-subsystem.md` | 2026-06-07 | 🔵 Evergreen | **New at 1.1.0** — the door / games subsystem. Three pure-module text games (`*_render` into a buffer, `*_feed` one line → 0 stay / 1 exit) on a shared `door.cyr` framework; `play <game>` + `MODE_DOOR`; main.cyr owns all socket I/O + persistence. Practice (ephemeral) + Solo (login-gated save). |
| `0010-persistent-universe.md` | 2026-06-08 | 🔵 Evergreen | **New at 1.2.0** — shared-world multiplayer. Per-game world dir mutated through a `flock`'d lock → read → pure-transform → write "world transaction"; the game logic stays pure. PA shared galaxy + async-PvP garrisons, Smuggler heat, Handler alerts, cross-game leaderboards. Rejects in-memory shared state (fork-per-accept forbids it), a coordinator daemon, SQLite, per-game bespoke locking. |
| `0011-chat-area.md` | 2026-06-08 | 🔵 Evergreen | **New at 1.3.0** — the live chat area. Per-channel `flock`'d **ring transcript**, live-tailed **by absolute sequence number** (rotation-safe vs a byte offset; no stdlib lseek) on the recv-timeout poll tick (`-EAGAIN` flushes rather than disconnects). Login-gated. Eliza as a private `/eliza` side-channel (not an always-present room bot — no write-arbitration, no transcript noise). Rejects poll-on-input-only, byte-offset tail, unbounded transcript, a chat daemon, char-at-a-time chat. |

---

## Tier 4 — Architecture (`docs/architecture/`)

| File | Last touched | Status | Notes |
|---|---|---|---|
| `README.md` (index) | 2026-05-23 | ✅ Fresh | Empty index. Candidate first note from M5-D experience: paired-LF-after-CR session-buffer corruption (caught in M5-D smoke, fixed via the `consumed` flag in `handle_client`'s EOL detection). Worth capturing as a "this is non-obvious from the code alone" architecture note if M6 work touches the same byte-dispatch surface. |

---

## Tier 5 — Guides (`docs/guides/`)

| File | Last touched | Status | Action |
|---|---|---|---|
| `getting-started.md` | 2026-05-23 | ✅ Fresh | **Rewritten at 0.9.1 doc-pass; iron-validated against 1.0.0.** Walks the 1.0 surface end-to-end: prereqs, build, tests (80/80), `agora serve 2323`, anon-read commands, identity setup (keygen + register), authored CLI post via `--as`, telnet `login` challenge/response, per-board `.policy` / `.admins` table, fork-per-conn concurrency check. Cross-links to all 8 ADRs and the 6 runnable example scripts. |

---

## Tier 6 — Examples (`docs/examples/`)

| File | Last touched | Status | Action |
|---|---|---|---|
| `README.md` | 2026-05-23 | ✅ Fresh | **Rewritten at 0.9.1 doc-pass.** 6-row example index with surface coverage and `./bbs/` + `./keys/` writeability columns. Run order, "what these are not" framing, monotonic-numbering convention for future additions. |
| `01-build-and-test.sh` | 2026-05-23 | ✅ Fresh | **New at 0.9.1.** Build, version-sanity vs `VERSION`, run `src/test.cyr`. Verified green against 0.9.0. |
| `02-register-and-post.sh` | 2026-05-23 | ✅ Fresh | **New at 0.9.1.** First writeable flow: keygen → register `qix` → post `--as` → list → read → assert `From: qix <fp16>` on disk. |
| `03-anonymous-read.sh` | 2026-05-23 | ✅ Fresh | **New at 0.9.1.** Proves M6 default policy: anon list + read succeed against the post written by 02; anon post is denied with exit 1. |
| `04-concurrent-smoke.py` | 2026-05-23 | ✅ Fresh | **New at 0.9.1** (skeleton lifted from `/tmp/agora-concurrent-smoke.py` referenced in state.md). Threads N (default 3) telnet sessions, asserts each gets banner + IAC bytes + `boards` reply with no cross-talk — proves ADR 0007 process isolation. |
| `05-telnet-login.sh` | 2026-05-23 | ✅ Fresh | **New at 0.9.1; iron-validated on archaemenid at 1.0 cut.** Drives the wire challenge/response: telnet → `login qix` → read challenge → wrap seed in PKCS#8 DER → `openssl pkeyutl -sign -rawin` → reply `auth: <hex>` → assert `whoami` reports `qix`. Drain logic rewritten at 1.0 cut: drain-and-print loop with 200ms quiet timeout replaces two blind `read` calls (preserves top row of bannermanor MOTD in stdout). |
| `06-board-policy.sh` | 2026-05-23 | ✅ Fresh | **New at 0.9.1.** Walks all three policy modes (open / known / admin) × three identity classes (anon / pac / qix), asserts each cell's expected exit code. 9/9 assertions pass against 0.9.0. Run after `02` (shares `./bbs` + `./keys`). |
| `07-play-door.sh` | 2026-06-07 | ✅ Fresh | **New at 1.1.0.** Launches all three door games over telnet in practice mode, asserts each renders (THE HANDLER / CABLE QUEUE / SMUGGLER'S LEDGER / PORT AUTHORITY). |
| `08-world-concurrency.sh` | 2026-06-07 | ✅ Fresh | **New at 1.2.0 bite 1.** Hammers one `flock`'d world with N concurrent processes × M `world_txn_add`s; asserts the final counter equals N×M (no lost updates). Proves the ADR 0010 transaction framework race-free. |
| `09-universe-port.sh` | 2026-06-08 | ✅ Fresh | **New at 1.2.0 bite 2.** Two players log in (sigil challenge/response) and `play port universe`: asserts a shared deterministic galaxy, exclusive planet ownership across sessions, world-snapshot persistence, and login-gating. Proves the PA shared galaxy end-to-end over telnet. |
| `10-leaderboard.sh` | 2026-06-08 | ✅ Fresh | **New at 1.2.0 bite 5.** Logs in, plays Port Authority solo to the close of the quarter, leaves (posting the score), then asserts `scores port` lists the run. Proves the cross-game leaderboard end-to-end. |
| `11-chat.sh` | 2026-06-08 | ✅ Fresh | **New at 1.3.0 bite 1.** Two logged-in sessions (sigil challenge/response) join `#lobby`: asserts session B sees A's line in **scrollback** (cross-session delivery via the `flock`'d transcript) AND A sees B's line via the **live-tail poll tick**. Proves the ADR 0011 chat interleaving over the wire. |
| `12-eliza.sh` | 2026-06-08 | ✅ Fresh | **New at 1.3.0 bite 2.** Drives both Eliza surfaces: the `play eliza` door (no login) decomposes "I am sad" → "How long have you been sad?"; the private `/eliza` side-channel answers in-chat AND the private line is asserted **absent** from the room transcript (privacy guarantee). |
| `13-parry.sh` | 2026-06-08 | ✅ Fresh | **New at 1.3.1.** Drives both PARRY surfaces: the `play parry` door answers a neutral line calmly, then a Mafia "flare" launches the delusion story (affect-gated); the private `/parry` side-channel answers in-chat AND off the room transcript. |

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
| 2 | **getting-started.md + examples/ rewrite** — bring both up to the 0.7.0 multi-board threaded BBS + sigil-auth + per-board-policy + audit-hardened-input shape; promote the M6-* and 0.7.0-audit-fix smoke scripts into runnable `docs/examples/` skeletons. | ✅ Completed at 0.9.1 doc-pass (2026-05-23) | This file (Tier 5 + Tier 6) | Landed against the 0.9.0 surface; six runnable scripts verified against the binary. See Tier 5 + Tier 6 rows above. |
| 3 | **Pre-1.0 security audit (0.7.0)** — full review of input validation across the IAC parser + post-storage path + auth surface. | ✅ Completed at 0.7.0 ship (2026-05-23) | `CLAUDE.md` "Security Hardening" + roadmap.md release plan | See [`audit/2026-05-23-audit.md`](audit/2026-05-23-audit.md). 5 fixes landed; 4 deferred to 0.8. Next audit at 0.8 close per cadence (once per minor / pre-release). |
| 4 | **First architecture note** — candidate: paired-LF-after-CR session-buffer corruption fix from M5-D as a "non-obvious from code" invariant for future maintainers of the byte dispatch. | Next M6 bite that touches `handle_client`'s EOL handling, or M6 close | This file (Tier 4) | One-time; archive note here on completion. |

---

*Initial scaffold: 2026-05-23 (v0.1.0) — pattern adopted from cyrius/docs/doc-health.md per first-party-documentation.md § Development Docs. Refreshed at every release; cleanup sweeps at 0.5.0 + 0.6.0 post-ship.*
