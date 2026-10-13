# 0025 — Store I/O: regular files only, and an exclusive crash-safe publish

> **Status**: Accepted
> **Date**: 2026-10-13 — 1.9.0. Amends [0002](0002-one-file-per-post-storage.md) § Consequences (crash
> consistency).

## Context

Two properties of the store were assumed and never enforced.

**What a store name is.** Every store file was opened like any other path (`file_read_all`, a plain
`file_open` for locks, `O_CREAT|O_TRUNC` for the registration files), so agora trusted whatever a name in
the store turned out to be (audit 1.8.1 I11):

- a **FIFO** named `N.txt`, `.policy`, `.admins` or a lock file blocked the open — `O_RDONLY` waits for a
  writer, `O_WRONLY` for a reader. Under `AGORA_SERVE=poll` that one open is every session's: the next
  `read`, `list` or `post` hung the whole server, and a second client was never even greeted
  (`docs/examples/32-store-hardening.py`, against a 1.8.2 build). Under fork it hung a child for good;
- a **symlink** was followed: `3.txt -> <any file the agora user can read>` was served to anonymous telnet
  users as a post, and the registration writes' `O_TRUNC` emptied and refilled whatever a planted link
  named. A dangling link at a lock file made `O_CREAT` create its target.

All of it needs write access to the store, but that is not the same as being the operator: agora runs as
one user, and the store may be shared or written by other tools.

**Whether a post survives a crash.** CLAUDE.md's "posts are durable artifacts" principle was not backed.
A post was `file_create_exclusive` + `file_write` straight into its final name, so a crash or power loss
mid-write left a truncated post under its id — listed, readable, attributed. 1.7.0 made door saves, the
shared world and chat crash-safe with `store_write_atomic` (temp, fsync, rename), and deliberately left
posts out: a rename *replaces* its target, and a post id must be claimed *exclusively* — 1.6.4 (audit M4)
exists because a create that could clobber an existing post was reachable whenever `post_max_id`
under-reports.

## Decision

**Every store file is opened as a regular file reached without a symlink, and every file that must be
created exclusively is published crash-safely — written to a temp, fsynced, then linked into place.**

1. **`store_open(path, flags)`** (`src/arena.cyr`) adds `O_NOFOLLOW` and `O_NONBLOCK` and then refuses any
   descriptor that `fstat` does not report as `S_IFREG` with `-EINVAL`. On top of it:
   `store_read_all` (replaces `file_read_all` at every store read), `store_lock_open` (every lock file),
   `store_append_locked` (the leaderboard; replaces the stdlib's `file_append_locked`). Registration's
   three files are now `store_write_atomic` writes, whose rename replaces a planted link instead of
   writing through it, and `store_write_atomic`'s own temp is unlinked and created `O_EXCL|O_NOFOLLOW`.
2. **`store_publish(dir, path, buf, len, durable)`** creates `path` exclusively and crash-safely: the
   bytes go to `<dir>/.publish.tmp` (unlinked first, created `O_EXCL`), are fsynced, and only then get
   their name by `link(2)` — which, like `O_EXCL`, refuses a name that exists. The temp is removed and
   the directory fsynced. The caller holds the lock that serializes writers in `dir` (the board lock for
   posts, `.users/.lock` for handle claims), which is why one fixed temp name per directory suffices
   and why crash debris is simply removed by the next writer. `post_new` publishes through it.

Scope: the **final** path component. Directories above it are not checked — whoever can replace those can
rewrite the store wholesale. Operator-chosen paths outside the store (`--motd`, the user's `--key` file)
keep plain opens: symlinking them is a legitimate operator choice.

## Consequences

**Positive**

- A FIFO, socket, device or directory in the store is an unreadable name, refused at once; a symlink is
  refused (`-ELOOP`). The poll server can no longer be hung through the store, and the BBS serves only
  files that are in it.
- A post is absent or whole. The exclusive id claim is unchanged — `link` refuses an existing name, so
  `t235` shows an existing post is never replaced.
- One primitive for "create exclusively, crash-safely": the 1.9.0 handle index ([0026](0026-handle-index.md))
  writes its claims with it.

**Negative**

- **One `fstat` per store open.** The reply scan (ADR 0005), which opens every post on a board on every
  `read`, measured 8–9% slower, interleaved on one machine: 3.38 → 3.71 ms at 500 posts, 13.1 → 14.2 ms
  at 2,000, 27.3 → 29.2 ms at 4,096 (~0.5 µs per post). `O_NONBLOCK` alone already removes the hang; the
  check is what makes the rule "regular files only" true rather than approximately true. Roadmap
  § 1.9.1's reply index removes the scan.
- **Two fsyncs per post** (the file and its directory). Posts are human-paced; the world-lock bench, which
  does the same per transaction, runs ~520/s.
- On a filesystem without hard links (vfat; agnos off ext2) `link` fails with the name still free and the
  publish falls back to `rename` — atomic, and safe from other agora writers because of the lock, but a
  non-agora process creating the same name in that instant would be replaced.

**Neutral**

- **agnos**: `AO_NOFOLLOW` covers the symlink. agnos has no `O_NONBLOCK`, no `fstat` (`sys_fstat` answers
  -1) and no way to create a FIFO (`mknodat` is ENOSYS), so the type check is Linux-only there.
- `store_write_atomic` (temp + rename) remains right for files that are *replaced* — saves, the world,
  chat, the registration files; `store_publish` is for files that are *claimed*.
- `store_publish`'s `durable = 0` skips both fsyncs, for a bulk writer that makes its whole batch durable
  at once (the handle-index build ends with one `sync()`); a crash can then leave a name holding an empty
  file, never a partial one, and that caller must treat empty as broken.

## Alternatives considered

**`O_NONBLOCK` + `O_NOFOLLOW` without the `fstat`.** It removes the hang and the symlink, and saves the
~0.5 µs per open. Rejected: a FIFO with a live writer would then be read as a post, and a directory or a
device node would be opened and read. Paying a measured 8% on a scan the next release removes, for a rule
that holds without exceptions, is the better trade.

**`lstat` before `open`.** Rejected on Linux: a check-then-open window an attacker with store write access
can race. `fstat` on the descriptor checks the thing that was opened. (agnos, which has no `fstat`, relies
on `AO_NOFOLLOW` and the absence of FIFOs instead.)

**Posts via `store_write_atomic` (temp + rename).** Rejected: rename replaces, and the post id claim must
be exclusive (1.6.4, audit M4). `link` is the exclusive form of the same idea.

**Per-writer temp names (`<path>.cyrtmp.<pid>.<n>`, as `store_write_atomic` uses).** Rejected for
`store_publish`: its callers already hold a directory lock, and a pid-named temp left by a crash is never
cleaned up by anyone, while a fixed name is cleaned by the next writer.
