# 0005 — Threading via `Reply-To` header (same-board, ID-only)

> **Status**: Accepted
> **Date**: 2026-05-23

## Context

[ADR 0004](0004-board-layout.md) shipped boards. With multi-board storage in place, the next missing BBS feature is **threading** — the ability to read a post and see which posts reply to it, and to compose a reply that's linked to its parent. Without threading, a board is a flat chronological log; with threading, it's a conversation.

Threading needs three load-bearing decisions:

1. **How is the reply relationship encoded on disk?**
2. **Cross-board threading: yes or no?**
3. **How are replies-to-a-post enumerated at `read` time?**

Candidate encodings:

- **(A) `Reply-To: <id>` header** in the reply's file, per RFC-822 conventions (ADR 0003 established the header format). One header field per post.
- **(B) `In-Reply-To` + `References` headers** per RFC 5322 § 3.6.4 — `In-Reply-To` is the immediate parent, `References` is the chain of ancestors. Lets a reader display deep threading (e.g. tree views).
- **(C) Sidecar reply index** — `<store>/<board>/.replies` mapping parent-id → list of child-ids. Single read per parent, no scanning.

Cross-board threading candidates:

- **(α) Same-board only** — `Reply-To` value is an integer post ID, parent must live in the same board as the reply.
- **(β) Fully-qualified `<board>/<id>`** — reply value is `<board>/<id>` cstring; reply can target any board.

Reply enumeration candidates:

- **(p) Scan-on-read** — when `read <id>` runs, walk the board's directory, read each post's header, list IDs whose `Reply-To` matches `<id>`. O(n) per read.
- **(q) Lazy-built index** — first `read` after startup walks once, caches in memory; subsequent reads use the cache. Cache invalidates on post.
- **(r) Maintained sidecar index** — write-through, update on every post + reply. Same two-file invariant cost ADR 0002 / 0004 rejected.

## Decision

**(A) `Reply-To: <id>` header, (α) same-board only, (p) scan-on-read.**

Specifics:

- **Reply relationship**: each reply post has a header line `Reply-To: <integer>\r\n` in its RFC-822 header block (ADR 0003). The value is the integer ID of the parent post in the same board.
- **Cross-board threading is not in scope.** Cross-board replies are rare in BBS practice (boards are themed; cross-board conversation is a sign the boards are mis-scoped). Adding it later is a non-breaking change — `Reply-To` becomes `Reply-To: <board>/<id>` for cross-board, plain `<id>` continues to mean same-board. The parser changes; existing posts stay valid.
- **Deep threading (`References` chain) is not in scope.** Single-parent `Reply-To` is sufficient for the BBS flat-thread shape. Tree-view rendering can be reconstructed by transitively following `Reply-To` if a future bite needs it.
- **Reply enumeration scans the board's directory on every `read`.** For each post in the board, parse the header for `Reply-To: <id>` and accumulate matches. O(n) in the board's post count per read; negligible at v1.0 scale (boards with < 1000 posts read in well under 100 ms on any modern disk).
- **`Re:` subject prefix** per RFC 5322 § 3.6.5: when composing a reply, if the parent's Subject starts with `Re: ` (case-insensitive) the reply subject keeps it as-is; otherwise prepend `Re: `. **Never doubled.** "Re: Re: foo" is a sign the parser is broken.
- **In-session `reply <id>`** command: validates parent exists in current board, computes Re-prefixed subject, **skips the Subject prompt** (uses derived subject directly), transitions to MODE_POSTING for body capture. Body ends with `.` as usual; `post_new_with_subject_reply` writes the file with both headers.
- **CLI `--reply-to <id>`** flag on `agora post`: same behavior as in-session reply, with subject from `--subject` or empty.
- **`read <id>` display** appends a line `Replies: N, M, ...` after the body if any posts in the board have `Reply-To: <id>`. Missing replies (post deleted, parent never had children) silently surface as empty.

## Consequences

**Positive**:

- **No schema changes to the post file shape.** ADR 0003's RFC-822 header block already accommodates new header fields — `Reply-To` joins `Subject` + `Date` without breaking older readers (which would silently ignore an unknown header). Existing 0.4.x posts without Reply-To headers continue to work as orphan posts.
- **Single source of truth.** The reply graph lives in the post files themselves. No sidecar to keep consistent; `cp -r <store>/<board>` copies the entire thread structure.
- **Cross-board upgrade path is non-breaking.** When the future ADR adds cross-board threading, the value syntax grows to `<board>/<id>` while plain `<id>` continues meaning same-board. No data migration.
- **`grep -l "Reply-To: 7" <store>/<board>/*.txt`** lists every reply to post 7 from the shell. Standard Unix tooling continues to work — same property ADR 0002 § Positive consequences listed for the storage layout.
- **Scan-on-read perf is plenty for v1.0 BBS scale.** Even a 10k-post board reads in well under a second; real BBS deployments are 100s of posts per board.
- **Re: subject deduplication matches user expectation.** Mail clients have done this for 40 years; users notice when it doesn't work.

**Negative**:

- **Reply lookup is O(n) per `read`** — scales with the board's post count, not the depth of the thread. For a 100k-post board the scan becomes ~10 seconds, which would be a real problem. Mitigations available when it earns its place: lazy in-memory index (q), or sidecar with strict-write-coordination (r). Today's scale doesn't justify either.
- **Orphan replies are silently tolerated.** If post 5 has `Reply-To: 99` and post 99 never existed (or was deleted), the reply lists in the void. `read 99` returns "post not found"; `read 5` shows the body but no parent context unless the read command also shows the parent (which it doesn't at this bite — future polish if needed).
- **The reply graph is one-deep on display.** `read 7` shows post 7's replies but doesn't transitively show replies-of-replies. Users can `read <reply-id>` to walk one level at a time. Tree-view UI is deferred to a future bite.
- **No cross-board threading** — answered above; non-issue at BBS-shape boards.

**Neutral**:

- **The `Reply-To` header field name** is already canonical in RFC 5322 — but RFC 5322's semantic is "Reply-To: <address>" (an email address to which replies should be sent), not "Reply-To: <message-id>". We're overloading the field name for an integer-ID-in-same-board reference. Defensible because (a) our posts are not email (no "send a reply to this address" semantic exists), (b) the field name reads naturally for users typing `reply 5`, (c) integers vs. addresses are textually unambiguous. The alternative — `In-Reply-To` per RFC 5322 § 3.6.4 — would technically be more correct, but the field name is less self-explanatory to users browsing post files. Decision: `Reply-To` for the user-facing shape; a future RFC-5322-strict mode can rename if real interop pressure surfaces.

## Alternatives considered

**(B) `In-Reply-To` + `References` headers.** Rejected at M5-F first cut. RFC-5322-strict, supports deep threading natively, but adds complexity (parsing a space-separated chain) without a current consumer needing it. M5-F first cut supports one-deep reply graphs; deeper threading earns its own bite if a real consumer requests it.

**(C) Sidecar reply index (`<store>/<board>/.replies`).** Rejected. Two-file invariant — exactly the pattern ADRs 0002 / 0003 / 0004 rejected at every prior layer. The performance win (O(1) reply lookup vs. O(n) scan) doesn't pay for the consistency cost at v1.0 scale.

**(β) Fully-qualified `<board>/<id>` Reply-To values.** Rejected at M5-F first cut. BBS-shape boards are themed; cross-board replies are conceptually rare. Adding it later is a non-breaking parser change. Shipping it now would force the value syntax + the parser to grow before we know if the use case is real.

**(q) Lazy in-memory reply index.** Rejected at M5-F first cut. Adds startup-time scan + cache invalidation logic for a perf problem we don't have. Reopens if a real consumer reports slow `read` on a large board.

**Tree-view display in `read`.** Rejected at M5-F first cut. Deeper than one-level adds rendering complexity (indentation, line wrapping, NAWS-awareness) that isn't shippable as a small bite. One-level "Replies: N, M, ..." after the body lets users navigate the tree manually with successive `read` commands.

**Storing the parent's subject in the reply's headers** (e.g. an extra `Re-Subject: ...` field) for fast `list` display without reading the parent. Rejected. Adds a field that duplicates information already retrievable via `Reply-To`. If the parent's subject changes (which we don't currently support but might in a future bite), the duplicate goes stale. Better to read the parent file when needed.
