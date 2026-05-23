# 0004 — Board layout: flat-root = "main", subdirs = named boards

> **Status**: Accepted
> **Date**: 2026-05-23

## Context

[ADR 0002](0002-one-file-per-post-storage.md) shipped single-board post storage: `<store>/<id>.txt`. M5-A through M5-G shipped on top of that — a working single-board BBS at 0.4.0. Real BBSes have **boards** (Usenet groups, FidoNet echos, modern subreddits / channels): themed posting areas that let the same node host multiple parallel discussions. Without boards, agora is a flat firehose; with boards, it's a community.

M5-E adds boards. Three load-bearing decisions need capture:

1. **On-disk layout** — where do per-board posts live?
2. **UI model** — how does a user (CLI and in-session telnet) pick a board?
3. **Lifecycle** — who creates boards, and when?

Candidate layouts:

- **(A) All boards as subdirectories**: every post lives at `<store>/<board>/<id>.txt`. The "default" board is just a board named e.g. `main` or `general`. Forces a migration of 0.4.0 stores (flat `<store>/<id>.txt`) into `<store>/main/<id>.txt`.
- **(B) Flat-root = "main", subdirs = named**: the 0.4.0 flat layout is the "main" board. Named boards live at `<store>/<name>/<id>.txt`. Free backwards compat with 0.4.0.
- **(C) Sidecar index**: a `boards.cyml` lists boards + their post-ID ranges; all posts live flat at `<store>/<id>.txt` with their board recorded in a header. Single ID space, but adds a two-file invariant.

Candidate UI models:

- **(α) Per-session current-board** with `boards` / `enter <name>` / `leave` commands. Modal — the prompt shows the current board; `post` / `list` / `read` operate on the current board. Classic BBS shape (uses since FidoNet 1984).
- **(β) Per-command flag** — `post --board art` / `list --board art`. Stateless, scriptable, no implicit mode. Modern CLI shape (uses since git's `--branch` 2005).
- **(γ) Per-connection prefix** — connect on port 23 → main board, port 24 → art board, etc. Telnet-native; user picks by which port they dial. Older BBS shape, breaks down past a few boards.

Lifecycle candidates:

- **(p) Auto-create on first post** — typing `enter art` then `post` creates `<store>/art/`. No admin step.
- **(q) Admin-create** — operator creates dirs via filesystem ahead of time; users can only enter existing boards. Operator-controlled.
- **(r) Self-service with `mkboard <name>`** — explicit creation command. In-between the two.

## Decision

**Layout (B): flat-root is "main", subdirs are named boards.** UI is **per-session current-board (α)** for the telnet side, **per-command `--board <name>` flag (β)** for the CLI side. Lifecycle is **auto-create on first post (p)** at M5-E first cut; future ADR may tighten to admin-only if board sprawl becomes a real concern.

Specifics:

- **On-disk**:
  - `<store>/<id>.txt` — posts in the implicit "main" board (backwards-compatible with 0.4.0 stores; new writes to "main" land here too)
  - `<store>/<name>/<id>.txt` — posts in named board `<name>`
  - `<store>/.lock` — main board's write lock (M5-G)
  - `<store>/<name>/.lock` — named board's write lock; each board has its own
- **Each board has its own monotonic ID counter** — `<store>/3.txt` and `<store>/art/3.txt` are distinct posts. ID isolation simplifies the M5-G lock per board (no cross-board contention).
- **Board name validation**: lowercase ASCII letters (`a-z`), digits (`0-9`), dash (`-`), underscore (`_`). 1-32 bytes. **Reject** uppercase, dot (filesystem traversal risk), slash (path-injection), and any non-printable. The name `main` is reserved (it means the flat root). The name `.lock` collides with the lock filename and is rejected.
- **Default current-board** is `"main"`. Session opens at `"main"`.
- **Prompt** shows `[board]` prefix when in a named board: `[art] >`. The `main` board's prompt is the bare `> ` (no prefix, matches 0.4.0 behavior).
- **Commands** (in-session, M5-E):
  - `boards` — list all boards with post counts (main first, then alphabetical named)
  - `enter <name>` — switch the session's current board; creates the board's dir on first use
  - `leave` — return to `main`
- **CLI** (M5-E): all three verbs grow `--board <name>` (default `main` if absent).

## Consequences

**Positive**:

- **Free backwards compat with 0.4.0 stores.** A 0.4.0 deployment that upgrades to 0.4.x with this bite reads its existing posts as "main" board content with zero migration. Operators don't run anything; they tag the new binary and restart.
- **Independent per-board lock + ID counters** — `M5-G`'s flock granularity moves from store-wide to board-wide. Concurrent writers to different boards never contend with each other. ID isolation makes the "find max ID" scan smaller per board.
- **The "main" board has the same disk footprint as before** — `cat <store>/*.txt` still shows the main posts the way it did at 0.4.0. Operators who never use named boards never see the new feature on disk.
- **Filesystem-shaped — operators understand it.** `ls <store>/art/` shows the art board's posts. `du -h <store>/art/` shows its size. Standard tooling works.
- **Telnet UX matches every BBS ever shipped.** Modal `[art] >` prompt is what users from any past 35 years of telnet BBS use will recognize on sight.
- **CLI shape matches modern operator tooling.** `agora post --board art` is scriptable and pipes-friendly; complements the modal in-session experience without imposing it on CLI users.
- **Validation rules are mechanical** — case + character class + length. No semantic disputes.

**Negative**:

- **Two equally-valid paths for main-board posts** — `<store>/<id>.txt` *and* `<store>/main/<id>.txt`. New writes go to flat-root; reads tolerate both? Decision: **new writes to main go to flat-root only.** If `<store>/main/` exists, treat it as a board literally named "main" (separate from the implicit-main flat-root). This means operators who manually create `<store>/main/` get a "literal-main subdirectory shadowing the implicit-main root" — they should not do that. Documented as a footgun in this ADR.
- **Board names can collide with filesystem-reserved names** on weird filesystems. Our validator is conservative (ASCII alphanumerics + dash + underscore + length ≤32), but case-insensitive filesystems (default macOS HFS+, default Windows NTFS) could see `Art` and `art` collide. We require lowercase to dodge that.
- **No cross-board operations** — moving a post between boards needs `cp`-then-delete + ID reassignment; not provided. Acceptable at v1.0; cross-board moves are rare BBS operations.
- **Auto-create lets users spawn boards by typing `enter newone`**. This is BBS-shaped behavior but invites board sprawl. M5-E1 ships with auto-create; tightening to admin-only is a future-ADR question if a real deployment hits the problem.

**Neutral**:

- **Pillar 4 (federation by interest, [`roadmap-future.md`](../development/roadmap-future.md))** maps cleanly onto boards — federate by board, each board's ID-set and post-store is the unit of sync. Current layout is a strict prefix of the federated shape.

## Alternatives considered

**(A) All boards as subdirs (including main).** Rejected. Forces a migration of 0.4.0 stores. Migrations introduce write-during-startup risk (interrupted mid-run = partial state) and operator churn (people running `agora migrate-boards` then realizing they should've backed up first). Free compat from (B) costs us nothing on disk; (A)'s "uniformity" win is aesthetic, not functional.

**(C) Sidecar index file (`<store>/boards.cyml`).** Rejected. Two-file invariant (post file + boards.cyml must stay consistent), exactly the pattern ADR 0002 rejected for the same reason at the per-post level. The single-ID-space promise has merit for content-addressing graduations (pillar 2), but content-addressing replaces integer IDs with hashes anyway — single-ID-space ceases to matter once that lands.

**(β) Per-command `--board` flag for the telnet UI** (no modal current-board). Rejected for the telnet side. Forces users to retype `--board art` on every command in their session. The modal current-board is the BBS-shape every user expects since FidoNet. **Accepted** for the CLI side, where statelessness matches modern tooling expectations.

**(γ) Per-port board selection.** Rejected. Doesn't scale past a few boards (each board needs a port allocation). Telnet clients can connect to any port, but operators have to manage port-board mappings out-of-band. Modal current-board on a single port is cleaner.

**(q) Admin-only board creation.** Rejected at M5-E first cut. Auto-create matches the file-system feel (a board is just a directory; `mkdir <store>/art` is one way to create one too). If real deployments hit board sprawl, an ADR amendment can promote to (q) with an `--auto-create=false` flag or similar.

**Reserving "main" as a regular subdir** (`<store>/main/<id>.txt` for main posts too). Rejected — eliminates the free backwards-compat with 0.4.0 stores. The footgun of "operator creates literal-`main`-subdir" is unlikely and documented; the compat win is real.
