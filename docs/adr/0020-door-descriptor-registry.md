# 0020 — Door descriptor registry (table-driven door dispatch)

> **Status**: Accepted
> **Date**: 2026-06-15

## Context

By 1.4.5 the door subsystem hosted **ten** games (Smuggler, Port Authority, The
Handler, Eliza, PARRY, QUEST, Jabberwacky, Olympiad, Ashes, Decode). Every
cross-cutting door operation was a per-game `if (game == GAME_X)` chain, and
those chains were smeared across **~16 dispatch functions** in `src/main.cyr`
(`door_game_name`, `door_world_bytes`, `door_world_valid`, `door_world_fresh_into`,
`door_set_world`, `door_universe_slot`, `door_world_begin`, `door_universe_feed`,
`door_universe_save`, `door_send_frame`, `door_feed_line`, `door_is_over`,
`door_post_score`, `door_save_on_exit`, plus the `play` launcher's new/load/start
clusters) — **~130 `== GAME_` branch sites in total**.

Adding the eleventh door would mean editing all eighteen of those places, in
lockstep, with nothing but discipline keeping them consistent. The 2026-06-15
P(-1) audit flagged this as finding **R7** (well past the project's "third
instance" refactoring threshold) and deferred it to its own cut so a large
mechanical change would not ride in a correctness-focused hardening release.

This is that cut (1.4.6).

## Decision

Replace the per-game dispatch chains with a single **per-game descriptor
record** keyed by `GAME_*` id, held in a registry array built once per worker
process (`door_registry_init`, guarded in `handle_client`). Each descriptor
(`enum DoorDesc` offsets) holds the game's identity (name, Universe save slot),
its behavior as **function addresses** (`&xx_render`, `&xx_feed`, `&xx_is_over`,
`&xx_save_format`, `&xx_new`, `&xx_load_parse`, `&xx_start`, world ctors/validators,
the lazy turn-tick, the leaderboard score/rank fns, the Universe "busy" notice),
and the data those need (default day-count, world byte-size/seed/field-offset,
fp-store offset, Universe seed override). Dispatch is a `callptr` through the
slot, with a `0` slot meaning "capability absent" (a chatbot has no save and no
`is_over`; Olympiad has no `start`).

**In scope**: all ~16 dispatch functions + the `play` launcher's new / load /
start / fp-store clusters, the per-game **mode-coercion** policy
(`DD_MODE_POLICY`: chatbots force practice, solo-only games downgrade a
`universe` request, Ashes forces universe), and the universe **on-entry** hook
(`DD_ON_ENTRY`, Ashes founding). The `== GAME_` branch count drops from ~130 to
**3** — and those three are not dispatch: two are `GAME_NONE` parse-validation
guards (unknown `play`/`scores` name) and one is a comment.
**Out of scope**: the per-game game logic itself (untouched — only how `main.cyr`
*selects* it changed); the name→id mapping in the `play`/`scores` parser
(inherent to parsing a command word); the chat-couch bot dispatch (`chat_bot_*`,
a separate 3-way switch on `g_chat_bot`, left as-is — only three bots, not the
door fleet).

Adding a door is now **one registry block** (plus the inherent enum id + the
parser's name→id line) — not an edit to eighteen scattered functions.

## Consequences

- **Positive** — a new door is a single self-contained descriptor block; the
  eighteen dispatch functions never change again. The "did I update all of them?"
  class of bug is gone structurally. Each dispatcher shrank to a guarded
  `callptr` (the ~130 branch sites collapsed to ~10 table lookups).
- **Positive** — capability gaps are explicit data (a `0` slot) instead of
  implicit "this game just isn't in that particular if-chain."
- **Negative** — one indirection layer: reading a dispatcher now means knowing
  the descriptor layout. The function addresses are resolved at run time
  (`callptr`), not statically, so a mis-wired slot fails at run time, not compile
  time — mitigated by the full example-smoke suite (all 13 door/universe/chat
  scripts) exercising every slot end-to-end.
- **Neutral** — the registry lives in heap built per forked child (a few hundred
  bytes, freed on process exit); function addresses are valid across `fork` (same
  binary image). Binary `+1,120 B` over 1.4.5 (the registry machinery net of the
  removed if-chains). Test count unchanged at 221 — the registry is dispatch glue
  validated by the smoke suite, not unit-testable from `src/test.cyr` (which does
  not link `main.cyr`).

## Alternatives considered

- **Leave the if-chains.** Rejected: R7 is past the third-instance threshold and
  every new door already pays the eighteen-edit tax. The audit called it.
- **A `switch`-like macro / codegen.** Cyrius has no macro facility that would
  collapse these without a language change; out of scope for an agora cut.
- **Parallel per-field global arrays** (`g_render[]`, `g_feed[]`, …) instead of a
  contiguous descriptor. Rejected: a contiguous record per game is the literal
  "one entry per door" the goal calls for; N parallel arrays re-scatter the very
  thing we're consolidating.
- **Static/compile-time table.** Cyrius address-valued globals exist, but a
  function-built registry keeps the per-game blocks readable and co-located, and
  the per-process build cost is negligible. See [001-cyrius-callptr-constraints](../architecture/001-cyrius-callptr-constraints.md)
  for the language constraints that shaped the implementation.
