# 0012 — Chatbot framework (Eliza, PARRY, and the fixed-script family)

> **Status**: Accepted — Eliza shipped 1.3.0, PARRY shipped 1.3.1; Jabberwacky pinned 1.3.3 as a different engine kind. Reachable two ways each (a `play <bot>` door + a private `/<bot>` chat side-channel). Pure modules, no new deps, unit-testable without a socket (`src/eliza.cyr`, `src/parry.cyr`; couch wiring in `src/main.cyr`).
> **Date**: 2026-06-08

## Context

[ADR 0011](0011-chat-area.md) built the synchronous chat surface and introduced **Eliza** as "the room's anchor inhabitant" — but deliberately scoped her as "a separate concern in the same minor" and **deferred the framework decision**: it asserted only that the engine was "factored as a reusable decomposition/reassembly core with a swappable script so PARRY can drop in at 1.3.1 with no engine rework." The *concrete* shape of that "swappable script" — a data-driven descriptor — was never settled in the ADR; it was the `eliza.cyr` header that went further, footnoting that factoring `ez_respond` / `ez_resp_none` into a descriptor was a *recommended first step* for the 1.3.1 PARRY bite, not a committed design. Building PARRY forced the actual decision. This ADR records it.

Three forces shape it:

- **The bots must not be a new subsystem.** agora already has the [ADR 0009](0009-door-games-subsystem.md) door shape — a pure module that renders to a buffer and is fed one line at a time, with no socket or disk knowledge — and the [ADR 0011](0011-chat-area.md) chat couch that pauses room tailing while you talk to a bot. A chatbot is exactly that shape. The question is the **internal reuse boundary** between bots, not the external surface.
- **PARRY is not Eliza with different strings.** Eliza (`ez_respond`) is keyword→template: normalize, reflect pronouns, rank-scan for the highest keyword, splice the reflected remainder into the keyword's next cyclic template. PARRY (`py_respond`) is **affect-gated**: it classifies each line into intent/flare flag bits (`py_scan_flags`), updates a decaying three-variable affect vector (fear / anger / mistrust, `py_apply_affect`), derives a mood, and **gates** the response on that mood — plus a story latch that, once mistrust crosses `PY_STORY_TH`, suspends mood dispatch entirely and walks an ordered delusion narrative (`py_beat`). There is no keyword→template table in PARRY at all.
- **The lineage past PARRY splits.** `docs/development/roadmap-future.md` lays out the well of further inhabitants: ALICE/Racter *extend* the fixed-script engine, but **MegaHAL and Jabberwacky** are Markov / corpus-retrieval bots that learn from a growing corpus and carry persistent state — a different engine kind, not a script swap. Jabberwacky is pinned to 1.3.3 precisely as that engine step.

The open question this ADR answers: **what, concretely, do two fixed-script chatbots share — and where does the "framework" stop?**

## Decision

**Chatbots are ADR-0009-shaped pure modules reachable two ways, sharing the engine's text primitives (not a data-driven script descriptor); the framework's reuse spans only the fixed-script family, and corpus-learning bots are a deliberately separate future engine.**

### Surface: door + private side-channel, never a room bot

Each bot exposes the door contract verbatim — `*_new` / `*_start` / `*_feed(line) → exit-flag` / `*_render(buf) → len` / `*_is_over` — so it is reachable as a **`play <bot>` door** (solo, practice-only; a conversation has no save worth persisting — `main.cyr:764-765` forces `DOOR_PRACTICE` for both bots, `*_is_over` always returns 0) *and* as a private **`/<bot>` chat side-channel** on the couch. The couch selects the active bot with one global, `g_chat_bot` (**0 none / 1 eliza / 2 parry**, `main.cyr:151`), allocated lazily on first `/eliza` or `/parry`.

The privacy guarantee is the whole reason the side-channel is acceptable inside a shared room: **while `g_chat_bot != 0`, the user's lines go only to the bot — never `chat_say`'d to the transcript — and room tailing is paused** (`main.cyr:144-150`, `1806-1817`; the empty-buffer tail flush at `1618` only fires when `g_chat_bot == 0`). The bot's reply is `send_buf`'d to the addressing user alone. This is the rejected-alternative from ADR 0011 made concrete: an always-present room bot has no write-arbitration story under fork-per-accept (who runs its turn?), pollutes scrollback, and risks feedback loops; the private couch ships the "go talk to the shrink" BBS nostalgia with none of that.

The couch reads any bot **uniformly** because every bot keeps its response buffer pointer and length at the **same struct offsets** — `EZ_RESP/EZ_RESPLEN == PY_RESP/PY_RESPLEN`, both at **8/16** (`eliza.cyr:59-71`, `parry.cyr:85-97`). `chat_bot_state` / `chat_bot_feed` / `chat_bot_name` (`main.cyr:1073-1089`) dispatch on `g_chat_bot`, and the couch then reads `bs + EZ_RESP` / `bs + EZ_RESPLEN` against whichever pointer came back (`main.cyr:1811-1814`). The shared-offset ABI is the contract a new fixed-script bot must satisfy; everything past offset 16 is the bot's own state.

### Reuse boundary: the shared text primitives, called directly

The framework is the **pure text primitives in `eliza.cyr`**, reused by `parry.cyr` as-is: `ez_normalize`, `ez_reflect`, `ez_word_is`, `ez_skip_sp`, `ez_word_end`, `ez_puts`, `ez_canned`, `ez_fill`, `ez_is_quit`. PARRY builds its classifier on the same word-walk idiom (`py_scan_flags` / `py_word_bits` call `ez_word_end` / `ez_word_is`), frames its replies with `ez_canned`, and shares the goodbye detector. That is the boundary — **primitives, called directly.**

**It is explicitly *not* a data-driven "script descriptor."** The `eliza.cyr` header recommended factoring `ez_respond` / `ez_resp_none` into a descriptor (keyword table + response-fn table + strings, passed through `ez_new`) so a new personality would be "purely a new descriptor" — and ADR 0011 left room for it under its looser "swappable script" phrasing. **Building PARRY proved that recommendation unnecessary and wrong**, and that reversal is this ADR's most load-bearing decision, so it is recorded honestly:

- A script descriptor models **keyword → template** dispatch. PARRY has none. Its dispatch is **mood-gated** (`py_mood` selects among `py_calm` / `py_wary` / `py_fearful` / `py_hostile`), with a **story latch** overriding it (`py_beat` walks ordered beats while `PY_STORYON`). The thing a descriptor would have abstracted — "look up the matched keyword, fetch its response set" — is not the operation PARRY performs.
- Forcing PARRY through a shared `ez_respond` descriptor would have meant either bending its affect engine into a keyword table (losing the character) or carrying a descriptor that only Eliza ever populates (abstraction with one user). The descriptor was speculative reuse; the [CLAUDE.md refactoring policy](../../CLAUDE.md) says wait for the third instance. The second instance disproved the abstraction instead.
- The right boundary turned out **lower** than predicted: the *primitives* compose into two very different engines, so they are the reuse unit. `ez_respond` / `ez_resp_none` stay DOCTOR-private; `py_respond` is PARRY-private; they meet only at the primitive layer and the shared-offset door ABI.

### Engine taxonomy: fixed-script vs. corpus-learning

Two engine kinds, and the framework spans only the first:

- **Fixed-script transforms** — Eliza (decomposition/reassembly) and PARRY (affect-gated). State is small and bounded (Eliza's per-keyword cycle counters + a 4-slot memory ring; PARRY's affect vector + story index + rotation counters), reset per conversation, never persisted. These are the family the primitives serve. ALICE and Racter, when they come, extend this family (AIML is a richer pattern→template grammar; Racter pushes toward generative grammar state) and reuse the same primitives + door ABI.
- **Corpus-learning bots** — MegaHAL (Markov) and **Jabberwacky (1.3.3, retrieval over a growing corpus)** — are a **different engine kind**: a learned model plus persistent, mutating state, raising a training-source / privacy / poisoning surface the fixed-script bots simply do not have. Jabberwacky is pinned to 1.3.3 as a *deliberate engine step*, not a script swap. It will reuse the door ABI and the side-channel surface, but **not** this framework's reassembly primitives — it shares the chassis, not the engine.

### Fidelity tradeoffs are explicit, not hidden

Both bots are faithful homages, and where faithfulness and clean code conflict, the homage wins and the trade is documented in-code:

- **Eliza** keeps the `am` / `are` / `you` / `can` keywords **canned** rather than splicing the reflected remainder, because their full decomposition reads ungrammatically when spliced (`eliza.cyr:38-41`) — the same call faithful ports of the 1966 CACM listing make.
- **PARRY's affect magnitudes are a reconstructed model.** Colby published the *mechanism* — three affect variables, intent valence, flare topics, the delusion, mood-driven output — but not a constants table, so the scales, baselines, deltas, and thresholds in `parry.cyr` are an engineering reconstruction; the **signs and relative sizes** are what reproduce the character, and the header says so plainly (`parry.cyr:18-26`, `217-221`).

## Consequences

- **Positive** — two finished, on-theme inhabitants with **zero new dependencies** and **zero new subsystem**: each is an ADR-0009 door, reachable in chat via the proven couch. The shared-offset ABI lets the couch read any bot with one branch, so a third fixed-script bot is a module + two `g_chat_bot` cases. Both engines are pure (no socket, no disk) and unit-tested with canned exchanges. The private side-channel delivers the room-bot nostalgia without any write-arbitration or scrollback-pollution cost.
- **Negative** — the reuse boundary is **primitives, not a config object**, so a new fixed-script bot is *code* (its own classifier/dispatch), not data — you cannot add a personality by dropping in a rule file (the operator-loadable AIML script format remains an open question, foreshadowed in ADR 0011). Two divergent `*_respond` engines mean the dispatch logic is duplicated in spirit, accepted deliberately because the descriptor that would have unified them did not fit PARRY. The shared-offset ABI is a hand-maintained convention (`RESP`/`RESPLEN` at 8/16) with no compiler enforcement; a future bot that forgets it breaks the couch silently.
- **Neutral** — chatbots are practice-only as doors (no save, no leaderboard; `*_is_over` always 0). The `play <bot>` door and the `/<bot>` couch are the same module reached two ways. The framework's reuse is scoped to the fixed-script family by design; the corpus-learning bots are a separate, later engine and will not retrofit onto these primitives.

## Alternatives considered

- **Data-driven script descriptor** (the `eliza.cyr`-header recommendation, foreshadowed by ADR 0011's looser "swappable script" note) — factor `ez_respond` into a keyword table + response-fn table + strings passed through `ez_new`, so each bot is "just a descriptor." **Rejected after building PARRY**: PARRY is affect-gated with a story latch, not keyword→template, so the descriptor models an operation it never performs. This was speculative reuse disproven by the second instance — the primitives are the real reuse unit. (This reversal is the body of the ADR.)
- **Always-present Eliza/PARRY room bot writing into the transcript** — more social, but needs a write-arbitration story under fork-per-accept (no shared memory; who runs the bot's turn?), pollutes scrollback, and risks feedback loops. Already rejected in [ADR 0011](0011-chat-area.md); the private `/<bot>` couch (input never `chat_say`'d, room tail paused) is the chosen surface.
- **Door-only, no chat side-channel** — simpler (one surface), but loses the "there's someone in the room you can pull aside" presence that motivated putting Eliza in chat at all. The couch reuses the door module verbatim, so the second surface is nearly free.
- **One unified bot engine spanning fixed-script *and* learning** — make Jabberwacky/MegaHAL share Eliza's pipeline. Rejected as a category error: Markov/retrieval over a growing corpus is a different computation with persistent mutating state and a privacy/poisoning surface. They share the door ABI and the side-channel, not the reassembly engine; the learning bots are a deliberate separate engine step (Jabberwacky pinned 1.3.3).
- **Separate response-buffer offsets per bot** (couch dispatches buffer reads per bot too) — marginally more flexible, but every bot already needs a response buffer and length, so fixing them at 8/16 lets the couch read any bot with a single offset pair. The tiny ABI convention buys uniform, branch-free reads.