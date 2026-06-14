# 0018 — Decode: the classify primitive and one engine for two variants

> **Status**: Accepted
> **Date**: 2026-06-14
>
> **Update (1.4.2)**: the **Words** variant shipped on this engine — a `[n]/[w]`
> select screen, a curated 532-word 5-letter dictionary (`src/decode_words.cyr`,
> its own data module) doubling as answer pool + valid-guess set, and a per-letter
> green/yellow/gray render — exactly the "second skin on `decode_classify`" this ADR
> scoped. The dictionary lives in a dedicated source module (compile-time, pure,
> unit-testable) rather than a runtime-loaded file, keeping the Words variant
> exercisable from the unit harness with no filesystem dependency.

## Context

agora's door tree has a signature shape, proven three times: **one pure
engine, many thin variants.** The seedable door PRNG ([ADR 0009](0009-door-games-subsystem.md))
fed the `wager` casino tables ([ADR 0013](0013-wagering-module-rng-fairness.md)),
which fed the Olympiad's event-agnostic `compete()` primitive
([ADR 0016](0016-olympiad-competition-primitive.md)). Each time the win was
the same: isolate the *pure, hard, testable* kernel, then make the games
thin descriptors over it.

The next two roadmap doors — **Numbers** (Mastermind: crack a 4-long code of
colors 1..6 from exact/present feedback) and **Words** (Wordle: crack a
5-letter word, the SAME feedback shown per-letter) — are not two games. They
are one game with two skins. The thing that is genuinely subtle and worth
getting right exactly once is the **feedback scorer**: given a secret and a
guess, classify each position as exact / present / absent, *handling
duplicate symbols correctly* — the trap a naive "count matching colors"
scorer fails (a guessed color may only claim as many "present" credits as
there are unmatched copies of it left in the secret).

Mastermind's peg counts and Wordle's per-letter colors are the *same*
computation: Mastermind sums the marks (exact = black pegs, present = white
pegs); Wordle paints each position by its mark. Numbers are values 1..6;
Words are letters. The classifier never needs to know which — it operates on
raw bytes.

## Decision

**Ship a single `decode` door backed by `src/decode.cyr`, whose pure heart
is `decode_classify` — a symbol-agnostic, duplicate-correct, per-position
exact/present scorer — and grow the door from one variant to two across two
releases.**

In scope:

- **`decode_classify(code, guess, len, out_marks)`** — the injected,
  unit-pinned test seam (t209), in the lineage of `wager_pick` /
  `ol_pick_weighted`. Two passes over a 256-entry symbol tally: pass 1 fixes
  the exacts and tallies the unmatched secret symbols; pass 2 awards a
  present to each remaining guess position only while that symbol's tally
  lasts. Over raw bytes, so Numbers (1..6) and Words (letters) share it
  verbatim. From it: `decode_exact` / `decode_present` / `decode_solved`.
- **A generic `DG` state + the full door contract** (`decode_new` /
  `decode_start` / `decode_render` / `decode_feed` / `decode_is_over` /
  `decode_save_format` / `decode_load_parse` / `decode_final_score` /
  `decode_rank`), solo/practice only — no shared world (universe coerces to
  solo, like QUEST/Olympiad). The secret is minted once at `decode_new` from
  the clock-seeded door PRNG (the player cannot reconstruct it; no wager/
  CSPRNG fairness stake) and persisted in the solo save — the same
  hidden-state trust model as The Handler's mole.
- **1.4.1 — the Numbers variant** (classic Mastermind: 4 / colors 1..6 /
  10 guesses), feedback as exact/present counts.

Out of scope here (sequenced):

- **1.4.2 — the Words variant**, added to the *same* door (a `[n]/[w]`
  select screen, a curated 5-letter word table doubling as answer pool and
  guess dictionary, per-letter green/yellow/gray render). It is a second
  skin on this engine, not a new game — "Words builds on the decode
  mechanics," literally.
- **1.4.3 — the Handler decrypt lever** reuses this engine inside another
  door; that cross-game composition earns its own ADR (0019).

## Consequences

- **Positive** — the one subtle thing (duplicate scoring) is written and
  pinned once; both variants and the Handler lever inherit it. The door
  contract is a copy of the Olympiad's, so the `main.cyr` wiring is
  mechanical. Render uses only `door.cyr` `emit_*` (no darshana), so the
  whole frame is exercisable from the unit harness.
- **Negative** — the Words dictionary is a curated subset (a few hundred
  words) serving as both the answer pool and the valid-guess set, so many
  real English words are rejected as "not a word". A deliberate BBS-scale
  simplification; the list can grow without touching the engine.
- **Neutral** — `decode_classify`'s marks are never serialized; the save
  stores secret + guesses and the marks are recomputed on load, so the
  classifier stays the single source of truth for feedback.

## Alternatives considered

- **Two separate doors / two modules.** Rejected: the feedback scorer is the
  only hard part and it is identical; duplicating it would be the exact
  anti-pattern the wager/compete lineage exists to avoid.
- **A richer per-variant scorer** (Numbers returns counts; Words returns a
  position array). Rejected: the position-marks array is the common
  denominator — counts are a trivial fold over it — so one classifier
  serves both with no loss.
- **Reconstructable (seed-derived) secret** for replayable "daily" puzzles.
  Rejected for now: a code-breaking secret the player can re-derive is a
  cheat vector; the secret is hidden state minted once, like the Handler's
  mole. A shared "daily" mode could layer on later without changing the
  engine.
