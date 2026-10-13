# 0026 — The handle index: one claim file per handle

> **Status**: Accepted
> **Date**: 2026-10-13 — 1.9.0. Amends [0006](0006-identity-model.md) § Specifics (account storage
> layout; wire login step 2).

## Context

ADR 0006 stores each account as `.users/<fp16>/` and resolves a handle by scanning: read every user's
`handle` file until one matches. That was sized for "~10s of users per deployment", and it is the
unauthenticated path — `login <handle>` needs no account.

- **A miss cannot stop early.** An unknown handle — the case an attacker chooses — always reads every
  user's file. At 301 users one 4 KB packet of `login x` lines held a 1.8.0 poll sweep for 626 ms (audit
  1.8.1 H1); 1.8.1's per-sweep line budget contains the effect on other sessions, not the cost.
  `benches/serve-bench.py login` measured **1.78 ms per unknown login at 300 users and 16.98 ms at 3,000**
  — linear.
- **Uniqueness was a check-then-write.** Two concurrent `agora register`s of one handle both passed the
  scan (28 of 30 trials); 1.8.1 (audit L4 / S8) serialized them with `.users/.lock`.

## Decision

**Each registered handle has a claim file, `.users/.by-handle/<handle>`, holding the fingerprint that owns
it; `.users/.by-handle/.complete` marks the index as covering every user. The user's own `handle` file
stays the source of truth: a claim is trusted only after the user it names is verified to hold the
handle.**

```
<store>/.users/.by-handle/
  <handle>       "<fp16>\n" — written by store_publish (ADR 0025): whole or absent, never replaced in place
  .complete      the index covers every user registered before it was written
```

- **Lookup** (`account_resolve_handle`): validate the handle with `handle_valid` first — it becomes a file
  name, and the wire `login` passes the client's raw bytes. Then read its claim. A claim whose user
  holds the handle is the answer. No claim, with `.complete` present, is an **authoritative unknown** —
  one failed open. Anything else (no `.complete` yet, a stale or unreadable claim) falls back to the scan.
- **Build** (`account_index_ensure`, under `.users/.lock`): a store that predates the index gets it on
  the first `serve` or `register` after the upgrade — one claim per user in scan order, so the first
  directory listing a duplicated handle keeps it, exactly as the scan answered — then one `sync()`, then
  `.complete`. `serve` runs it in a short-lived child process so the server's own heap is untouched.
- **Maintenance** (`account_register`, under the same lock): claim the new handle **before** writing the
  user's files and release the old one **after**. A crash in between leaves a stale claim, which a lookup
  detects and does not trust; it never leaves a missing claim, which a complete index would trust.

## Consequences

**Positive**

- Unknown-handle login is O(1): **0.16 ms at 300 users and at 3,000** (fork mode, so no poll-sweep wait;
  1.78 → 0.16 and 16.98 → 0.16 ms). A known handle costs two opens (the claim and the user's `handle`).
- Claims are created exclusively, so the index is also a uniqueness record; registration keeps the 1.8.1
  lock because a handle change claims one name and releases another.
- A malformed handle is refused before any path exists, closing a path oracle the scan never had.

**Negative**

- **The first start after the upgrade builds the index**: measured ~50 ms at 300 users and ~300 ms at
  3,000 (start-to-listening 251 → 301 and 251 → 552 ms); later starts only check `.complete`.
- **A hand-edited `.users/` is not seen until the index is rebuilt.** A user directory copied in without
  a claim is unknown to a complete index — by design, or a miss could not be authoritative. The operator
  deletes `.users/.by-handle/`; the next `serve` or `register` rebuilds it.
- Two files now describe one fact; the verification step is what keeps the second from being trusted
  over the first.

**Neutral**

- The fingerprint stays the identity; handles remain names. Audit 1.8.1 I9 (`.admins` grants by handle,
  and a re-registered handle frees the old one for anyone) is unchanged and stays roadmap § 1.9.2.

## Alternatives considered

**One index file (`handle fp` lines) rewritten per registration.** A miss would still read and parse the
whole file — linear again, only with a smaller constant — and every registration would rewrite it.

**Claims as symlinks (`.by-handle/qix -> ../<fp16>`).** One `readlink` per lookup, no file body. Rejected:
1.9.0 makes the store refuse symlinks at every open ([0025](0025-store-io-regular-files-and-publish.md)),
and a link would be the one sanctioned exception.

**Fall back to the scan on every miss.** Keeps hand edits visible without a rebuild, and keeps the attack
exactly as cheap as it was. Rejected: the authoritative miss is the point.

**Key the user directory by handle** (`.users/<handle>/`). Rejected: the
directory name is the identity (ADR 0006: a handle is a mutable name, the key is the account), and
renaming a user's directory on a handle change would break every fingerprint reference in `From:` lines.
