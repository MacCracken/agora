# 0033 — Provably fair wagers: committed seeds, and an audit trail anyone can check

> **Status**: Accepted
> **Date**: 2026-10-14 — 1.12.1; amends 0013, 0016

## Context

[ADR 0013](0013-wagering-module-rng-fairness.md) split agora's randomness in two:
- The games keep a seeded, replayable PRNG.
- The wager draw comes fresh from the kernel CSPRNG, because a player betting against the house is an
  adversary, and a reconstructable draw makes the house edge fiction.

It left two open questions: whether wagers need an audit trail, and whether to adopt commit-reveal provable
fairness. Both were rejected for the first cut as "more machinery than a BBS door needs", to be revisited "if a
wager ever needs a player-verifiable audit trail".

By 1.12.0 wagers carry real stakes in four places:
- the cantina wheel (Port Authority);
- the back-alley bones (Smuggler's Ledger);
- the tavern cards (QUEST);
- the Olympiad's book, where the race order itself is the draw ([ADR 0016](0016-olympiad-competition-primitive.md)).

All four settle into persisted gold in Solo and Universe runs, and two run inside shared worlds. A fresh kernel
read is unpredictable, but it leaves nothing behind. A player who suspects the house can be told only "trust
the code". An operator facing a dispute has no record of what was bet, what was drawn, or what it cost. The
operator can't show the server was honest, and can't catch it if it wasn't.

## Decision

**Every wager and contest draw comes from a session seed whose SHA-256 the player sees before betting and
which is revealed afterwards; every real-stakes wager leaves a line in an append-only audit log; and an
independent script checks the log against the reveals.**

### The draw

- Each session holds a fairness context: a **server seed** of 32 bytes from the kernel CSPRNG, kept as 64 hex
  characters; its **commitment**, SHA-256 of those 64 characters; the **next** seed and its commitment,
  committed in advance; a **client seed**; and a **nonce**.
- Draw *k* on the seed is `SHA-256("<seed>:<client>:<k>")`, its first 15 hex digits (60 bits) read as a number,
  mod the range. Any SHA-256 tool can redo it. The 60 bits keep the arithmetic in i64, and the modulo bias for
  any range a game uses is below 2⁻⁴⁰.
- Everything that settled on `wager_uniform_csprng` now calls `wager_uniform`: the three casino tables (through
  `wager_draw`) and the Olympiad's race order. The seed comes from the CSPRNG, so a player still cannot predict
  a draw; they only ever see the seed hashed. ADR 0013's line between replayable game randomness and
  unpredictable wager randomness stands. What changes is that the wager side can now be **checked after the
  fact**.
- The context is created per session slot and reset for each connection. It is seeded lazily: by the first
  draw, by the first betting screen (the commitment must be on screen before the first bet), or by `fair`.
  With no context, as in the unit harness, a draw falls back to the plain kernel read.

### What the player sees and does

- Every betting screen shows `Provably fair: seed commitment <16 hex>..., draw #<nonce>`.
- `fair` at the BBS prompt shows the full commitment, the next seed's commitment, the client seed, the draws
  made on the current seed, and the last revealed seed with its hash.
- `fair reveal` reveals the current seed and moves to the next.
- `fair seed <text>` does the same and sets the client seed: 1 to 32 letters, digits, `.`, `_` or `-`.
  Because the next seed was committed before the player chose a client seed, the server cannot have picked a
  seed to suit it. That is the standard reason commit-reveal schemes take a player seed.

### The audit trail

`<store>/.games/wagers` is one append-only file, written with `store_append_locked` with each line fsync'd,
and tab-separated:
- `W <time> <handle> <game> <commitment> <client> <first nonce> <n:r,...> <stake> <bet> <outcome> <delta>
  <balance>` for each settled real-stakes wager, carrying every draw its contest made;
- `R <time> <handle> <commitment> <seed> <client> <draws>` when a seed that a logged wager used is revealed.

Reveals are written on `fair reveal`, on `fair seed`, and on **every session close path** (the same hook that
checkpoints door saves). A seed that bets were logged against is always revealed, even if the player simply
disconnects.

**Real stakes** means a Solo or Universe run, so the player is always logged in. A Practice wager is ephemeral
chips and leaves no line.

The game modules stay pure:
- `wager_audit` records the settled wager in the session's context;
- `main.cyr` writes it after the line (`door_feed_line` → `door_wager_flush`), as it writes worlds and saves.

`scripts/verify-wagers.py` checks a log using Python's own `hashlib`, sharing no code with agora:
- each R line's seed must hash to its commitment;
- each W line's draws must recompute from the revealed seed;
- W lines whose seed is not revealed yet are reported as pending.

Tests: t261 (the draw against Python vectors, the trace, rotation, client seeds), t262 (all four settlement
sites), s16 (the log, the reveal on close, `fair`), and smoke 39 (the wire, both models, a tampered log
caught).

## Consequences

- **Positive** — a bet can be checked, not merely trusted. The commitment on screen before the first bet, the
  reveal after it, and a public recipe let a player verify their own bets. The log plus the verifier lets an
  operator settle a dispute or audit the whole house. A tampered draw is caught (smoke 39 alters one result).
- **Positive** — the audit trail is crash-safe (each line fsync'd) and complete: a seed a logged wager used is
  revealed on every close path, so no logged draw is left unverifiable.
- **Positive** — the fsync on each real-stakes wager also paces how fast a logged-in player can grow the log
  (one write per bet, about 2 ms each), and practice play costs nothing.
- **Negative** — the log grows without bound: about 150 bytes per real-stakes wager, by logged-in players only.
  It is the operator's to rotate (move the file; the next wager starts a new one). This is the same class as the
  leaderboard and the boards themselves. A rotated file must stay beside its successor for the verifier, since
  a seed's reveal may land in the next file.
- **Negative** — each session slot holds a 704-byte context (64 slots under poll: 45 KB once), and each draw
  costs a SHA-256 instead of a single `getrandom`. That is negligible at betting pace.
- **Neutral** — the Olympiad's race draws come from the committed seed too, so a race run without a bet still
  advances the nonce. Only wagers are logged, and a W line names its own first nonce, so gaps are expected.
- **Neutral** — a client seed a player never sets defaults to 16 random hex characters chosen by the server.
  Full assurance against a server picking seeds to suit a client seed needs the player to set their own;
  `fair` says how.

## Alternatives considered

- **A fresh kernel read per draw, plus a log** (ADR 0013 unchanged, with an audit file). Rejected: the log
  would record the outcomes, but nothing would let anyone check them. The server would be auditing itself.
- **A per-bet seed revealed in the bet's own result.** Rejected: it shows the player nothing before the bet
  that binds the server. The commitment has to come before the stake.
- **Commit to a whole session's outcomes in advance** (a hash chain of draws). Rejected as unneeded: the seed
  commitment binds the same thing with one hash, and the nonce keeps draws independent.
- **Log Practice wagers too.** Rejected: ephemeral chips leave nothing to dispute, and an anonymous client
  could fill the disk with them.
- **An in-binary verifier (`agora wagers verify`).** Rejected for now: a verifier that shares agora's
  SHA-256 code proves less than one that doesn't. `scripts/verify-wagers.py` is the one, and the recipe is
  short enough to redo by hand.
- **Rotate the log inside agora.** Rejected: renaming under the append lock would strand waiting writers on
  the old file, and an operator's rotation tool already exists for logs.
