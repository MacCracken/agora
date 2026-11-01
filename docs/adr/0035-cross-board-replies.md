# 0035 — Cross-board replies: `Reply-To: <board>/<id>`, recorded where the parent lives

> **Status**: Accepted
> **Date**: 2026-10-31 — 1.13.1; amends 0005, 0008, 0027

## Context

[ADR 0005](0005-threading-via-reply-to.md) chose same-board threading: `Reply-To: <id>` names a parent on the
reply's own board. It recorded cross-board replies as a non-breaking later change, "`Reply-To` becomes
`Reply-To: <board>/<id>` for cross-board, plain `<id>` continues to mean same-board". Roadmap § 1.13.1 asked
for exactly that, with the parent's replies found through the reply index
([ADR 0027](0027-reply-index.md)) of the board the parent lives on.

Three things constrain it.

- **The index is per board and verified.** `.replies/<parent>` holds the ids that reply to `<parent>`. Every
  listed child is checked against its own `Reply-To:` before it is shown, and a complete index's silence is
  trusted.
- **A record must be written before its post** (ADR 0027), under the lock of the board whose index it is.
- **A board can be members-only** ([ADR 0028](0028-board-policy-modes.md)). A reply on such a board must not be
  readable, or even visible, through a public parent.

## Decision

**A reply names a parent on another board as `Reply-To: <board>/<id>`. Its record goes in the parent board's
index as `<board>/<child>`. A reference is shown relative to the reader's board.**

- **The syntax.** A reference is `<id>` or `<board>/<id>`, where the board is a valid board name or `main` (the
  flat root). `reply_ref_parse` is the single parser for a post's header, an index record, and what a user or
  the CLI types. A board name must pass `board_ref_name_ok` before it is copied anywhere, so no reference can
  reach a path unchecked. Every post written before 1.13.1 is a plain `<id>` and means what it always meant. A
  self-qualified `tech/7` on tech is the same parent as `7`.
- **Commands.**
  - `reply <board>/<id>` writes the reply on the session's current board. The session must be allowed to read
    the parent's board, because the parent's subject is copied into the reply's. The post policy checked is the
    current board's, as for any post.
  - `read <board>/<id>` reads a post on another board, gated by that board's read policy.
  - The CLI takes `agora post --reply-to <board>/<id>`.
- **What `read` shows.**
  - A reply now shows its parent, as a `Reply-To:` line after the subject.
  - `Replies:` lists this board's replies, then other boards' replies sorted by board and id.
  - Every reference is written as the reader would type it from where they are: a plain id for a post on the
    reader's current board, `<board>/<id>` elsewhere.
  - A reply on a board the session may not read is left out.
- **Writing** (`post_new`). A reply to another board's post takes both boards' locks, always in board-name order.
  Two writers replying across the same two boards in opposite directions would otherwise deadlock. Its record is
  appended, fsynced, to the parent board's index before the post is published, exactly as ADR 0027 orders a
  same-board record.
- **Reading** (`reply_index_read_x`). A record is `<id>` or `<board>/<id>`, and anything else, a torn record
  included, is dropped. A cross-board child is verified by opening it on its own board. Its `Reply-To:` must name
  this board and this parent, so a ghost, a forgery or a record naming a board that does not exist is never
  listed. The same-board API (`replies_to`, `reply_index_read`) is unchanged.
- **Rebuilding** (`reply_index_ensure`). Besides the board's own posts, the build reads every other board's
  posts once, and records those whose `Reply-To:` names this board. Without that, a rebuilt index would miss the
  cross-board replies, and `.complete` would vouch for an index that is wrong.
- **PostHeaders** ([ADR 0008](0008-post-headers-struct.md)) gains `PH_REPLY_BOARD` and its setter. The change is
  additive: existing callers and their wire output are unchanged.

## Consequences

**Positive**

- Threads can cross themed boards, and every reference on screen can be typed back as it is shown.
- No migration. Old posts, old index files and the old API all mean what they meant. An index built before 1.13.1
  is still complete, because no cross-board reply could be written through agora before it.
- A reply on a members-only board stays invisible to anyone who cannot open that board, through its parent too.

**Negative**

- **A rebuild reads every post in the store**, not just the board's. It happens on a board's first index, or
  after an operator deletes `.replies/`, not per command. A store of many boards with many fresh ones pays it once
  per fresh board at the next `serve`.
- **The index alone knows cross-board replies.** While a board's index is not complete, `read` falls back to the
  scan of that board (ADR 0005), which cannot see replies on other boards.
- **A reply to another board takes two board locks.** Ordering them makes this deadlock-free, but a writer can now
  wait on a board it is not writing to.
- Each listed cross-board reply costs a policy lookup for its board (once per run of the same board) and a header
  read on its board.

**Neutral**

- At most 512 cross-board replies per parent are parsed (`XREPLY_MAX`), oldest first, beside the 8,192
  same-board ones.
- A hand-written post is still unseen by a complete index until it is rebuilt (ADR 0027).

## Alternatives considered

- **Record the reply in its own board's index as well.** That gives two records for one fact, and the parent's
  board would still have to find it. Rejected for the two-file problem ADR 0005 rejected.
- **A store-wide log of cross-board replies.** One file to read on a rebuild instead of every post, but it is a
  second source the posts would have to agree with, and it needs its own rebuild.
- **Absolute references everywhere** (`<board>/<id>` even on the same board). Simpler to parse, but it changes
  every same-board reply's header and every `Replies:` line agora has ever printed.
- **Write the reply on the parent's board.** It is what a mailing list does with a cross-post, but it puts a
  post on a board its author is not on and may not be allowed to post to.
