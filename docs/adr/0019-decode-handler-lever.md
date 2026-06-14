# 0019 — Decode as a Handler gameplay lever (cross-game mechanic reuse)

> **Status**: Accepted
> **Date**: 2026-06-14

## Context

The decode engine ([ADR 0018](0018-decode-engine.md)) shipped as its own door
(`play decode`, Numbers + Words). The 1.4.x arc's third bite asked a different
question: can a mechanic built for one door become a *lever inside another* —
the first time agora reuses one game's engine inside a second game?

The target is **The Handler** ([ADR 0009](0009-door-games-subsystem.md)), the
espionage-deduction door. You run a network of field agents from a desk; the
game is to find the mole. A cable is *discrepant* when its routing metadata
contradicts ground truth (relay city ≠ true city, a stale date, or an
unverified cipher). The mole applies **one** discrepancy class consistently, so
its cables accumulate a pattern; honest low-reliability agents throw isolated
one-off discrepancies — the **false positives** that make the hunt hard. The
data model already carries a hidden ground-truth field, `CB_ANOM` (set only on
the mole's deliberately-forged cables, *never shown* to the player).

The user's framing: the handler never leaves the office, so the lever is a
**desk-bound cipher break** — "decoding a number or word sequence grants access
to a networked agent's communication." Two constraints fell out:

1. **It must not corrupt the existing deduction.** An unverified cipher is
   *itself* one of the three discrepancy signals, so a lever that "verifies the
   cipher" would erase a mole's tell. The reward has to be *additive* —
   information the player can't otherwise get — not a mutation of the visible
   metadata or the ground truth.
2. **It can't be free.** If you could crack every cable for its verdict, the
   false-positive fog (the whole puzzle) evaporates. The lever needs a scarce
   resource so cracking is a *choice*.

## Decision

**Reading a cable, the section chief can spend one dispatch point to BREAK ITS
CIPHER — a decode round whose secret is derived deterministically from the
cable — and a crack reveals `CB_ANOM`: whether the cable is a deliberate PLANT
(the mole) or clerical NOISE (an honest false positive).**

In scope:

- **A new `HSCR_DECRYPT` screen** hosting a decode round, and three runtime-only
  `TH` fields (`TH_DECODE` the active decode state, `TH_CRACKED` a per-session
  cracked bitset, `TH_DECRI` the cable under analysis). **All runtime-only — the
  save format does not change** (the cracked bitset resets on reload; the
  verdict is re-derivable by cracking again).
- **`th_cipher_for_cable(cb, out)` (pure)** — derives a deterministic
  `(variant, secret)` from the cable's own fields (`CB_NR`/`CB_AGENT`/`CB_DAY`/
  `CB_KIND`): **intercepts → a Words codename, paperwork → a Numbers relay
  code**. Same cable ⇒ same crackable code (replayable, unit-pinned t217), so
  it's a fair fixed puzzle, not a fresh random each open. It reuses the decode
  engine verbatim (`decode_new` → `decode_set_numbers`/`_words`, the secret
  pinned to the derivation).
- **The point cost** — `[D]` spends one `TH_POINTS` dispatch point (the same
  economy that gates Move/Extract/Fund), so cracking competes with ordering
  agents. Out of points, or already cracked → a message, no round.
- **The reward** — on a crack, the READ screen shows
  `CRYPTANALYSIS: routing DELIBERATELY FORGED -- a plant.` (`CB_ANOM == 1`) or
  `clerical noise -- no plant here.` (`CB_ANOM == 0`). This is *new* information
  (CB_ANOM is otherwise never shown) that cuts the false-positive fog: a
  discrepancy you can confirm is a plant points at the mole; one confirmed as
  noise clears an honest agent. The visible metadata and the ground-truth
  discrepancy are untouched.

Out of scope:

- Mutating any visible cable field or the discrepancy verdict (would corrupt the
  deduction — constraint 1).
- Persisting the cracked state across reloads (runtime-only keeps the save ABI
  frozen; re-cracking is cheap and the cost re-applies, which is fine).

## Consequences

- **Positive** — the first cross-game mechanic reuse: one engine, two doors. The
  composition is clean because decode is a pure state machine (render-into-buffer
  / feed-one-line) — The Handler stands up a `decode_new`, forwards lines to
  `decode_feed` while on `HSCR_DECRYPT`, and resolves on `decode_is_over`. The
  lever deepens the mole hunt (skill + a resource buys ground-truth intel)
  without touching the deduction math or the save format.
- **Negative** — the cracked bitset is per-session, so a reload re-locks ciphers
  the player already broke; they pay the dispatch point again to re-confirm.
  Accepted as the cost of not versioning the save ABI for a re-derivable hint.
- **Neutral** — the decode round during a crack is forced into its variant
  (no `[n]/[w]` select screen — the cable decides), so the embedded use and the
  standalone `play decode` door share the engine but not the entry flow.

## Alternatives considered

- **Verify the cipher (flip `CB_CIPHER`) on a crack.** Rejected: an unverified
  cipher is a discrepancy signal, so this would erase a cipher-class mole's tell
  — it corrupts the puzzle (constraint 1).
- **Free, unlimited cracking.** Rejected: revealing every cable's `CB_ANOM` for
  free removes the false-positive fog that *is* the deduction (constraint 2).
- **A go-to-the-agent's-safe / dead-drop framing** (crack to open a physical
  safe). Rejected: the handler is desk-bound — the lever is breaking intercepted
  comms at the desk, not leaving the office.
- **A fresh random cipher each time a cable is opened.** Rejected: a fair puzzle
  needs a fixed code per cable; the deterministic derivation (t217) gives that
  and stays replayable.
