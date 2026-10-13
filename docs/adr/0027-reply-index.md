# 0027 — The reply index: one verified record file per parent

> **Status**: Accepted
> **Date**: 2026-10-13 — 1.9.1. Amends [0005](0005-threading-via-reply-to.md) § Decision (reply enumeration
> (p) scan-on-read → an index) and answers its § Alternatives (C) / (r).

## Context

`read <id>` ends with `Replies: 2, 4, …`. ADR 0005 chose **scan-on-read**: open every post on the board, parse
its `Reply-To:`, keep the matches — "negligible at v1.0 scale", with an index deferred until it earned its
place. 1.8.2 and 1.9.0 measured it (`benches/serve-bench.py reply`, fork, 1 KB posts):

- **Every `read` paid for the whole board**, replies or not: a post with **no** replies cost 2.8 ms at 500
  posts, 11.0 ms at 2,000, 23.7 ms at 4,096 (1.9.0, interleaved A/B) — and under `AGORA_SERVE=poll` that is
  the whole server's time, once per session per sweep.
- **It was blind past 4,096 posts**: the scan walked `post_list`, which keeps a board's newest 4,096 ids, so
  a reply older than that was never listed.

ADR 0005 rejected a sidecar ((C), and (r) "maintained sidecar index") for one reason: the **two-file
invariant** — two places that must agree, and nothing to say which is right when they do not.

## Decision

**Each board keeps `.replies/<parent>`, an append-only file of the ids that reply to `<parent>`, and
`.replies/.complete` once the board is fully indexed; the post files stay the only source of truth — every
child an index file names is verified against its own `Reply-To:` before it is listed.**

```
<board path>/.replies/<parent>     "\n<child>\n" per reply — framed so a torn record cannot merge with the next
<board path>/.replies/.complete    every post on the board is indexed
```

- **Read** (`replies_to` → `reply_index_read`): with `.complete` present, read `<parent>`'s file, sort, drop
  duplicates, and keep each child whose own header says `Reply-To: <parent>`. A missing file is "no replies"
  — the complete index is trusted for absence. Without `.complete`, or with an unreadable file, scan as
  before.
- **Write** (`post_new`, under the board lock): a reply's record is appended **and fsynced before the post
  is published**. A crash in between leaves a record naming a post that does not exist, or whose id is later
  reused by an unrelated post — a *ghost*, which verification drops. It can never leave a reply missing from a
  complete index. If the record cannot be written, `.complete` is removed (reads scan again) rather than
  leaving a complete index that is silently wrong.
- **Build** (`reply_index_ensure`, under the board lock): every post on the board — not `post_list`'s
  newest 4,096 — is read once and its record appended (no fsync), then one `sync()`, then `.complete`. It
  runs for every board in `serve`'s startup child (alongside the handle index, [0026](0026-handle-index.md)),
  and for a board on its next reply.

This answers the two-file objection the way the handle index did: the second file is a **derived, verified
cache**. It may hold ghosts (verified away) and duplicates (removed); by construction it cannot omit a reply
written through agora.

## Consequences

**Positive**

- A post with no replies costs **0.18 ms at any board size** (was 2.8 / 11.0 / 23.7 ms at 500 / 2,000 /
  4,096 posts); a thread with a tenth of the board replying, **0.49 / 1.30 / 2.46 ms** (was 3.73 / 14.11 /
  29.39). `read` is O(replies of that post), ~5.6 µs each (the verification open), no longer O(posts).
- Replies older than the newest 4,096 posts are listed: the build indexes every post.
- `grep` still works — the records are text — and `rm -r .replies` is a complete, safe reset.

**Negative**

- **A post written into a board by hand is not listed as a reply** until the index is rebuilt — a complete
  index's silence is trusted, or `read` would have to scan. Documented procedure: delete `<board>/.replies/`;
  the next `serve` or reply rebuilds it. (Every agora writer goes through `post_new`; a pre-1.9.1 agora
  writing to the same store would also bypass it.)
- **A reply costs one more fsync** (the record) plus a directory fsync — four in all, with the post's two.
  Posts are human-paced.
- One more file per replied-to post. Ghost records accumulate only on failed or crashed publishes.

**Neutral**

- Verification reads each listed child's header block, so a very long thread costs proportionally (~2.4 ms at
  409 replies); the list is capped at 4,096 ids as before. One parent's records are read up to 128 KB
  (~8,000 replies; the oldest kept).
- The `Replies:` line is now composed in 2 KB pieces: under fork every `send_buf` is a `write(2)`, and
  sending it id by id cost more than finding the replies. The bytes on the wire are unchanged (byte-compared
  against 1.9.0 on a 400-reply thread, which crosses a piece boundary).

## Alternatives considered

**Keep the scan (ADR 0005 (p)).** The measurements above are the case against it: every `read` paid for the
whole board, the poll server paid it for everyone, and it could not see past 4,096 posts.

**A lazy in-memory index (ADR 0005 (q)).** Under fork each connection is its own process, so every child would
rebuild it — the scan again, once per connection; under poll it must be invalidated by writes from other
processes (the CLI, fork children). Rejected again.

**One `.replies` log for the whole board (`child parent` lines).** One file, but a `read` must parse all of
it: linear again, only cheaper. Per-parent files make the read proportional to the answer.

**Trust the index without verifying.** Saves an open per listed reply. Rejected: a ghost (a failed publish
whose id was reused by an unrelated post) would be listed as a reply to the wrong parent — the two-file
invariant ADR 0005 rejected, unguarded.

**Append the record after the post is published.** No ghosts — but a crash between the two would leave a
reply missing from a complete index, which nothing would ever notice. A ghost is detectable; an omission is
not.
