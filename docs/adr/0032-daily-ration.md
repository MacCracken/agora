# 0032 — The daily ration: game days per UTC day, for runs that persist

> **Status**: Accepted
> **Date**: 2026-10-13 — 1.12.0; amends 0009, 0010, 0016

## Context

Three ADRs promise a wall-clock day. [ADR 0009](0009-door-games-subsystem.md) adapted the BBS-door rhythm for
The Handler as a "UTC day-rollover via `chrono` (`epoch/86400`), sysop-config 1–3 turns/day".
[ADR 0010](0010-persistent-universe.md) made the daily budget the Universe's fairness lever: "per-player
turn/action budgets gate how much each player changes the world per real day … so no one can monopolize the
world in one sitting". [ADR 0016](0016-olympiad-competition-primitive.md) built the Olympiad's economy on
"a per-day action ration (the QUEST daily-turn economy)" and left "wall-clock vs turn-based day" open.

Only QUEST implemented one. Its forest fights refill when `clock_epoch_ns() / QU_NS_PER_DAY` changes, checked
on entry. Smuggler's Ledger, Port Authority and The Handler advanced a game day whenever the player pressed
the next-day key (a jet, `n`, `e`). The Olympiad's `[N]ext-day` refilled its three training actions on
demand, and `OL_LASTDAY`, the field meant to hold the refill day, was saved and never read. The 1.8.1 audit
recorded both (I4, I5) and 1.8.1 added a note to each ADR saying the cadence was not enforced. This ADR
enforces it.

Two facts shape the decision. Practice runs are ephemeral: no save, and they end with the session. They also
post to the leaderboard (a 1.2.0 decision: "a practice run is a real, fresh run"). And the four games' days
differ in kind. In Smuggler, Port Authority and The Handler a game day is a step toward the end of a 30-day
run. In the Olympiad, a day is a refill of the actions that training and rest consume.

## Decision

**A Solo or Universe run of Smuggler's Ledger, Port Authority, The Handler or the Olympiad advances at most
`g_door_days` game days per UTC day. The operator sets it with `agora serve --door-days N` (default 10; 0
turns the ration off). Practice runs are not rationed.**

- **One mechanism.** `door.cyr` holds the ration: `door_ration_take(dayp, leftp, mode)` refills on a new UTC
  day, then spends a day if one is left; `door_ration_peek` reports what is left without recording anything;
  `door_emit_ration` renders "N more today" in a game's header. Each game passes its two cells — the UTC day
  of the last refill and the days left — and its mode.
- **Where it gates.** The one call that advances a day in each game: Smuggler's jet (`sl_feed_jet`, before
  `sl_travel`), Port Authority's `n`, The Handler's `e`, the Olympiad's `n`. A refused day changes nothing
  and says so: "That's all the days a run gets today -- it picks up again tomorrow (UTC)." Everything that
  does not advance a day still works: trading, the bank, reading cables, training with actions left.
- **Persistence.** The two cells are part of each game's state and save, appended after the last field, so a
  1.11 save loads them as 0 (`save_get_i64` reads 0 past the end) and starts with a fresh ration. The
  Olympiad reuses `OL_LASTDAY` for the day and appends the count. A save written by 1.12 still loads in 1.11,
  which ignores the trailing lines.
- **The clock.** Like QUEST's `qu_day_tick`: any change of day refills, including one where the clock went
  backward, so a skewed or reset clock heals rather than freezes a run. A count above the allowance (an
  operator lowered `--door-days`, or a hand-edited save) is clamped to the allowance.
- **Visibility.** `agora serve` logs the ration in force at startup. Each rationed header shows the days left.
- **Tests.** t260 (the cells, the four gates, the saves), s15 (the flag), smoke 38 A (the wire, both models).

## Consequences

- **Positive** — the ADRs' rhythm is real: a Solo run spans real days (three at the default for a 30-day
  run), and a Universe player can no longer drive a shared world through a whole run in one sitting.
- **Positive** — one knob, honest about its default: an operator who wants The Handler's original 1–3 days
  sets `--door-days 2`; one who wants no cadence sets 0, and smoke 10 does exactly that to play a whole
  quarter.
- **Negative** — the leaderboard is not protected by it. A Practice run is unrationed and still posts, so a
  player who wants a fast score plays Practice. That was already true, and rationing Practice would make it
  impossible to finish (it ends with the session); the ration's job is the persistent runs and the shared
  worlds.
- **Negative** — three save formats grew by two lines and the Olympiad's by one; three state structs grew
  by 16 bytes and the Olympiad's by 8.
- **Neutral** — QUEST keeps its own ration (forest fights per day), which predates this and differs in kind.
  Ashes' cadence is its turn window, unchanged.
- **Neutral** — the Olympiad's allowance is generous at the default (ten refills a day, thirty training
  actions), but condition still limits how often a competitor can race.

## Alternatives considered

- **Ration Practice too.** Rejected: a Practice run cannot outlive its session, so a ration would end every
  long run partway; and quitting and re-entering gives a fresh run and a fresh ration anyway.
- **A constant per game** (Handler 2, Smuggler 10, …) with no operator setting. Rejected: ADR 0009 already
  said "sysop-config", and pacing is a deployment's call (a LAN party wants no ration, a long-running board
  wants LORD's rhythm). One allowance for all four keeps the knob simple; per-game knobs can follow if anyone
  asks.
- **QUEST's shape: one refill per UTC day and no next-day key at all.** Rejected for the three 30-day games,
  where a run would take a month; kept, in effect, for anyone who sets `--door-days 1`.
- **Gate in `main.cyr`** by comparing the day counter before and after a fed line. Rejected: a day's
  effects (debt, events, overnight burns) would already have happened; the gate must sit in front of the
  advance, inside the module.
- **Bump the save headers** (`SLDG2`, …). Rejected: appending keeps 1.11 saves loading and 1.12 saves
  loadable by a rolled-back 1.11, with no version branch in four loaders.
