# 0002 — One file per post for the M5 storage layout

> **Status**: Accepted
> **Date**: 2026-05-23

## Context

M5 (post persistence) needs an on-disk format for the boards / threads / messages that the v1.0 BBS will serve. The format choice is **load-bearing**: it ripples into how `agora post` / `list` / `read` work today (M5-A), how the telnet wire layer surfaces those operations (M5-B), how concurrent writes are coordinated (M5-G), and how the v2.x post-pillar-2 content-addressed-storage graduation (see [`roadmap-future.md`](../development/roadmap-future.md)) replaces the post ID with a content hash without breaking external references.

Three candidate shapes:

- **(A) One file per post** — `<store>/<id>.txt` (with subdirectories for boards in a later bite). Read a post → `read(<store>/<id>.txt)`. Write a post → `O_CREAT | O_EXCL | O_WRONLY` on the next monotonic ID.
- **(B) One file per thread with offset index** — `<store>/<thread>.log` (append-only thread log) plus `<store>/<thread>.idx` (post offsets within the log). Read a post → seek to offset, read N bytes. Write a post → append + update index.
- **(C) SQLite-style WAL** — embedded relational store with WAL journaling. `agora-data.db` holds all posts; SQL queries handle list / read / pagination.

Other choices in scope of the decision:

- **Post ID assignment**: monotonic integers (read max existing, +1) vs. UUID vs. content hash.
- **Storage root**: hardcoded path (`/var/agora`) vs. user-relative (`~/.agora/posts`) vs. cwd-relative configurable (`./agora-data` with `--store <path>` override).
- **File format inside each post**: plaintext UTF-8 body only vs. RFC-822-shaped headers (Subject / Author / Date) + body.

## Decision

**Layout: (A) — one file per post**, stored as `<store>/<id>.txt` with monotonic-integer IDs.

In scope at M5-A (first bite):

- **Storage root** — operator-configurable via `agora --store <path>`, default `./agora-data/` (cwd-relative). Mirrors the M2-C `--motd <path>` pattern; same trust boundary (operator owns where posts go).
- **File format** — plaintext UTF-8, no headers at M5-A. Headers (`Subject:` / `From:` / `Date:`) land at M5-D once we know what the wire-level post-creation flow actually needs.
- **Post ID assignment** — monotonic integers via "read highest existing filename, +1". O(n) per post creation but trivially correct under single-writer; concurrent-write coordination lands at M5-G.

Out of scope at M5-A (deferred to later bites in the same cycle):

- Boards / threads (subdirectories) — M5-E and M5-F.
- Locking for concurrent writers — M5-G.
- Telnet-wire integration (`post` / `list` / `read` verbs over the connected client loop) — M5-B.

## Consequences

**Positive**:

- **Simplest possible model.** The on-disk shape is `ls <store>` for listing, `cat <store>/<id>.txt` for reading, append-with-EXCL-flag for posting. Any tool that handles files handles posts — `grep`, `find`, `tar`, `rsync`, `git`.
- **Content-addressing graduation is mechanical.** The v2.x pillar-2 design swaps `<id>.txt` for `<hash>.txt` and the rest of the schema is unchanged. The hash is computed from the canonical post body at write time, replacing the monotonic counter. External references that pointed at `<id>` get migrated by a one-shot rewrite pass that's just a file rename. The current shape is a strict prefix of the eventual shape.
- **No write coordination needed for monotonic-but-not-strictly-sequential IDs.** `O_CREAT | O_EXCL` makes "claim the next ID" atomic at the filesystem level — concurrent writers may race and one loses, but neither corrupts the other's post or returns a fake ID. Single-writer lock (M5-G) tightens this; the EXCL guarantee is correct without it.
- **No new dependency.** `lib/io.cyr` already has `file_read_all` (used by M2-C `--motd`), `file_open`, `file_write`, `dir_list` (in `lib/fs.cyr`). Zero new stdlib surface.
- **Easy to migrate to boards.** When M5-E adds boards, the layout extends to `<store>/<board>/<id>.txt` — no rewrite of M5-A code, just a path-join change in `post_new` / `post_list` / `post_read`.
- **Backup / restore is `cp -r`.** Operators who understand directories understand the BBS storage.

**Negative**:

- **O(n) post listing.** `dir_list` returns every file in the store; for a 100k-post BBS that's still under 10 ms on any disk, but it bounds the architecture. Pagination at the application layer (only read the directory listing once per session) mitigates.
- **Inode pressure at high post counts.** Each post is one inode; 1M posts = 1M inodes. ext4 handles this fine but ZFS or filesystem-per-board would be better at extreme scale. Pre-v1.0 we're not at extreme scale; M5-E (boards) naturally shards the inode load.
- **No transactional cross-post operations.** "Move thread between boards" or "merge two threads" are not atomic. Deferred to a v2.x graduation if and when the use case is real; the BBS-shaped use cases don't require it.
- **Filesystem case-sensitivity matters.** On case-insensitive FS (default macOS HFS+, default Windows NTFS), `1.txt` and `1.TXT` collide. We use lowercase-only `.txt` extensions — operator running on case-insensitive FS gets the same behavior as case-sensitive. Documented in `architecture/`.

**Neutral**:

- **Crash consistency is filesystem-level.** A crash mid-write leaves either a complete post or no post (the EXCL flag means the rename-on-close is atomic from the reader's perspective; partial writes show as truncated files which fail the post-read-validate step). Higher-level transaction support would belong to a v2.x cycle and is not required for BBS-shaped use cases.

## Alternatives considered

**(B) One file per thread with offset index.** Rejected at M5-A. The win is dense storage (no per-post inode), the cost is a two-file invariant (log + index must stay consistent) and a custom on-disk format that no Unix tool understands without a parser. For human-paced BBS traffic the inode cost is irrelevant; for extreme-scale we'd shard via M5-E boards before reaching for this. We retain (B) as a future option if a specific perf or operator concern makes it the only path; switching from (A) → (B) is a one-shot conversion (read all `<id>.txt`, write `<thread>.log`+`.idx`) so deferring is safe.

**(C) SQLite-style WAL / embedded relational store.** Rejected. Adds a substantial new dependency surface (SQLite is C, not Cyrius; AGNOS-native re-implementation is its own multi-thousand-LOC project). The schema-flexibility argument is real but not at the v1.0 BBS scale — posts are append-only and rarely cross-referenced at the storage layer. Patra (cyrius stdlib storage) may grow a SQLite-shaped backend in the future, in which case (C) reopens.

**Hashed IDs at M5-A (content addressing now, not at v2.x).** Rejected. Forces a decision on canonical post serialization (header field ordering, encoding, normalization) before we know what fields a post needs. M5-A's plaintext-body posts have a trivially canonical form (the bytes are the canonical form); when M5-D adds headers, we'll choose canonicalization with the field set in front of us. The monotonic-integer interim is content-hash-ready — same `<id>.txt` shape, swap the ID assignment fn.

**Hardcoded storage root.** Rejected. `/var/agora` requires root privileges that we don't want; `~/.agora/posts` couples to the running user's HOME (CI runs as different users); cwd-relative `./agora-data` with `--store` override gives operators control without surprising filesystem semantics. Same trust boundary as M2-C's `--motd`.

**RFC-822-shaped headers at M5-A.** Rejected. We don't yet know the field set the wire-level post-creation flow surfaces. Adding headers at M5-A risks designing the wrong header set; deferring to M5-D once the telnet `post` verb shape is real picks the headers from concrete need.
