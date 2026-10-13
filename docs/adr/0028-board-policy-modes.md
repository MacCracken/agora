# 0028 — Board policy modes that mean something: members-only, anonymous posting, admins by key

> **Status**: Accepted
> **Date**: 2026-10-13 — 1.9.2. Amends [0006](0006-identity-model.md) § Specifics (posting policy) and
> fulfils its deferred `anon-allowed` ADR.

## Context

ADR 0006 gave each board a `.policy` of `open` / `known` / `admin` and an `.admins` list of handles. By 1.9.1
three things about it were not true or not finished:

1. **`known` was `open` under another name.** `open` admitted any logged-in session, `known` "a registered
   user" — but every login resolves through `.users/`, so every logged-in user is registered. An operator
   could set `known` and observe nothing (roadmap § 1.9.2).
2. **Anonymous posting was promised and never decided.** ADR 0006 § Specifics: "A future ADR may add
   `anon-allowed` … if a real deployment wants a no-account-required board (e.g., a feedback board)". Its §
   Alternatives also imagined `known` gating *reading* ("set every board to `known` and the visitor can't
   even `read` until they login — well, `read` doesn't check policy at M6").
3. **`.admins` granted rights by handle** (audit 1.8.1 I9). A handle is a name, not an identity: when a key
   re-registers under a new handle, the old one is free for anyone to register — and an `.admins` line naming
   it hands that newcomer the board.

And operators edited `.policy` / `.admins` by hand; the CLI verbs had been "future" since the 0.6.0
closeout.

## Decision

**Four modes, each observable; `.admins` entries keyed on the fingerprint; an operator CLI for both.**
(Chosen by the project owner at 1.9.2 over collapsing `known` into `open`.)

| Mode | Reads (`enter` / `list` / `read`) | Posts (`post` / `reply`) |
|---|---|---|
| `open` (default — no `.policy`) | anyone | a logged-in user |
| `known` | **a logged-in user whose key is still registered** (members only) | the same |
| `anon` | anyone | **anyone, anonymous sessions included** |
| `admin` | anyone | a session listed in `.admins` |

- **`known` becomes members-only** (`board_can_read`): an anonymous session gets `members only` from `enter`,
  `list` and `read` (checked on each, not only at `enter` — the policy can change, and `main` is where every
  session starts), and `boards` shows `members only` in place of the post count. A tightening, so it fails
  safe for any board already set to `known`.
- **`anon` is ADR 0006's `anon-allowed`**: `board_can_post` admits an anonymous session on that board only.
  Its posts carry no `From:` and render `[anon]`, as pre-M6 posts do. The CLI `agora post` without `--as`
  follows the same rule.
- **Fail closed, both ways.** An unreadable or unparseable `.policy` is admin-only for posting (1.8.1) and,
  now, members-only for reading — a broken `known` board must not become world-readable.
- **`.admins`**: one entry per line, an optional inline `# comment`. An entry of exactly 16 lowercase hex
  digits is a **fingerprint** and matches **only** the session's key; anything else is a handle. The split is
  strict because a handle may itself be 16 hex digits: matching fingerprint-shaped entries against handles
  would let someone register an admin's fingerprint as their handle. Handle entries keep working (with the
  I9 risk); `agora admins add` writes the fingerprint (`<fp>  # <handle>`).
- **Operator CLI** (`main.cyr`): `agora policy get|set <board> [<mode>]`, `agora admins list|add|rm <board>
  [<handle|fingerprint>]`. They validate the board name and the mode, take the board lock, and replace the
  file with `store_write_atomic` (ADR 0025). `admins add` resolves a handle through the handle index (ADR
  0026) and refuses an unknown one; `admins rm` removes the fingerprint entry and any handle entry for the
  target.

## Consequences

**Positive**

- A mode an operator sets now changes what users can do, and `agora policy get` says which applies.
- Members-only boards and guest/feedback boards exist without code, per board.
- Admin rights survive handle changes and cannot be inherited by registering a freed handle.
- `.policy` / `.admins` are edited with validation and atomically; hand edits keep working.

**Negative**

- **`anon` invites abuse** on a telnet port: no account, no rate limit beyond the per-session line budget and
  `MAX_SESS`. It is an explicit per-board opt-in, and the guide says so; nothing is anonymous-writable by
  default.
- **`known` changed meaning.** A board an operator set to `known` before 1.9.2 now hides its posts from
  anonymous sessions. Recorded as a breaking change in the CHANGELOG; it only ever restricts.
- A handle entry in `.admins` that happens to be 16 hex digits stops matching that handle (it is read as a
  fingerprint). No agora tool ever wrote one; the CLI lists entries so an operator can see what each is.

**Neutral**

- Reading is still never gated for the CLI viewers (`agora list` / `read`): they are the operator's, and
  read the files directly.
- `.policy` / `.admins` formats are unchanged except for `anon`, fingerprint entries and inline comments, so
  a 1.9.1 server reading a 1.9.2 store sees `anon` as invalid (admin-only — fails closed) and fingerprint
  entries as handles no one has.

## Alternatives considered

**Collapse `known` into `open`** (a documented alias). The smallest change and no behaviour change; rejected
by the owner in favour of making the mode useful — members-only boards are a long-standing BBS feature, and
ADR 0006 had already sketched `known` as the read gate.

**A fifth mode for members-only, keeping `known` = `open`.** Leaves the meaningless mode in place and adds
another name to learn.

**Reject anonymous posting outright.** Safer, but ADR 0006 explicitly reserved it for operator opt-in, and a
board that is anonymous-writable only when the operator says so is the narrowest form of it.

**Match fingerprint-shaped `.admins` entries against handles too.** Rejected: it is exactly the impersonation
above. A dedicated prefix (`fp:…`) would also disambiguate, but a bare fingerprint is what `agora whoami`
prints and what an operator will paste.

**Forbid 16-hex handles at registration.** Would also close the ambiguity, but changes the handle alphabet
for every deployment to protect a file only admin boards have.
