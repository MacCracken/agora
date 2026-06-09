# 0015 — Jabberwacky: the corpus-learning chatbot engine

> **Status**: Accepted — shipped 1.3.3. `src/jabberwacky.cyr`; wiring in `src/main.cyr` + `src/door.cyr`; tests t167-t175; smoke `15-jabberwacky.sh`.
> **Date**: 2026-06-08

## Context

[ADR 0012](0012-chatbot-framework.md) settled the chatbot framework for the **fixed-script family** (ELIZA, PARRY) and drew an explicit line: corpus-learning bots are "a **different engine kind** — a learned model plus persistent, mutating state, raising a training-source / privacy / poisoning surface the fixed-script bots simply do not have," pinned to 1.3.3 as "a *deliberate engine step*, not a script swap … it shares the **chassis**, not the **engine**." This ADR is that engine step. It records what the new engine *is*, and — because ADR 0012 flagged it as the defining new risk — how the **persistence / privacy / poisoning** surface is contained.

Three forces shape it:

- **Jabberwacky is retrieval, not transformation.** Rollo Carpenter's Jabberwacky (1988→) does not parse grammar (ELIZA) or model affect (PARRY). It **remembers what people say and replays it**: given the current context it finds the most similar thing said before and answers with the human reply that once followed — case-based reasoning over a *growing* corpus. The bot "gets smarter" (or stranger) the more it is talked to. The engine is therefore a corpus + a similarity scorer + a learning rule, none of which the ADR-0012 reassembly primitives provide.
- **Learning means persistent, mutating, per-actor state.** Unlike the stateless bots (forced `DOOR_PRACTICE`, no save), a learning bot's value *is* its accumulated corpus. That state has to live somewhere across turns and ideally across sessions — which immediately raises the question ADR 0012 deferred: **whose corpus, and who can read or poison it?**
- **On a multi-user BBS, a shared learned corpus is a live abuse surface.** The authentic Jabberwacky learned globally (from millions of web chats). On a LAN BBS, a single global corpus means any caller can teach the bot to replay slurs, secrets, or terminal-escape payloads to the *next* caller — a poisoning + privacy + injection vector with no analog in the fixed-script bots. The wire is adversarial by default (CLAUDE.md); a learning store multiplies that.

## Decision

**Jabberwacky is an ADR-0009-shaped pure door module whose engine is word-overlap corpus retrieval with a learn-the-transition rule, and whose learned state is a per-user private layer over a shared baked-in seed — never a global corpus.** It reuses the door chassis and ELIZA's *text* primitives, but none of the reassembly engine, exactly as ADR 0012 predicted.

### Engine: overlap retrieval + transition learning

- **Corpus** = an array of `(stimulus, response)` pairs. The stimulus is `ez_normalize`'d (matching key); the response is `jw_sanitize`'d display text (printable ASCII 32–126 only). Two layers: a **seed** region `[0, JW_SEEDN)` (baked-in personality, ~24 pairs) and a **learned ring** `[JW_SEEDN, JW_COUNT)` capped at `JW_MAXPAIRS=64` — when full the *oldest learned* pair evicts; seeds never evict.
- **Retrieve** (`jw_best_match` / `jw_overlap`): the reply is the response of the pair whose stimulus shares the most distinct **content words** with the normalized input (whole-word matches; 1-char words and a small stop-list ignored). **Ties go to the latest pair** (`>=`) so a freshly-learned pair beats an older seed — the "replay what I just taught you" behaviour. Zero overlap → a rotating generic deflection (`jw_fallback`), so the bot is never mute.
- **Learn** (`jw_respond`): answer **first** (with the corpus as it stands, so a turn never matches the pair it is recording), **then** record `(previous line → this line)` — stimulus = the prior user line, response = the current user line — **then** remember this line as the next stimulus. Empty normalized/sanitized strings are dropped. The bot only ever learns *human* utterances as responses (never its own output), which is faithful and avoids feedback degeneration.
- **Reuse boundary (per ADR 0012)**: reuses `ez_normalize`, `ez_word_end`, `ez_word_is`, `ez_puts`, `ez_is_quit`; uses **none** of `ez_reflect` / `ez_fill` / `ez_scan` (the DOCTOR reassembly engine). Shares the chassis, not the engine.

### Persistence: hybrid (shared seed + per-user learned layer), not global

Jabberwacky is **not** force-practiced (unlike ELIZA/PARRY); it is a real solo/practice door on the QUEST model:

- **`play jabberwacky`** (practice, anon-OK) — seed corpus only; learns in-session; **ephemeral** (never written).
- **`play jabberwacky solo`** (login-gated) — loads + saves **only the learned layer** at `<store>/.users/<fp16>/games/jabberwacky.sav` through the existing ADR-0009 door SOLO-save path (`jw_save_format` / `jw_load_parse`). The seed is re-baked on load, never serialized (so it can't double). `jw_is_over` **always returns 0**, which keeps `door_save_on_exit` on the *checkpoint* branch (it saves when `is_over==0`) and off the score branch — the learned layer persists on every clean exit, and a chatbot never posts a leaderboard score.
- **`/jabberwacky` couch** — ephemeral, seed-only, like `/eliza` and `/parry`; the persistent surface is the solo door.

The save record is `"<stimulus>\t<response>\n"`. Because the stimulus is normalized and the response sanitized, **neither can contain TAB or LF** — the delimited format is unforgeable and carries no terminal escape.

### Containment of the poisoning / privacy / injection surface

The hybrid model is the mitigation, not a footnote:

- **Per-user isolation kills cross-user poisoning and privacy leakage.** A citizen's learned corpus is keyed on their own sigil fingerprint and is read back only by them; one caller's lessons never reach another's bot. There is **no global shared corpus** anywhere in the design.
- **Sanitization kills escape injection and delimiter forgery.** Every stored response passes `jw_sanitize` (32–126 only, dropping ESC/control/TAB/LF), so a malicious teacher cannot store an ANSI payload that replays into a later session, nor a TAB/LF that splits the save record.
- **The ring kills unbounded growth.** The learned corpus is hard-capped (`JW_MAXPAIRS`) and the save is bounded (whole-file, capped, the stdlib has no `lseek`).

## Consequences

- **Positive** — agora's first **learning / persistent-state** inhabitant, on the proven door chassis + chat couch with **zero new dependencies** and **zero new subsystem**. The privacy/poisoning surface ADR 0012 warned about is *designed out* (per-user isolation) rather than policed. The engine is pure and fully unit-tested (retrieval, learn-replay, eviction, save/load round-trip — t167-t175) with no socket; the wire surfaces are smoke-proven (`15-jabberwacky.sh`: door learn-replay, couch privacy, cross-session persistence).
- **Negative** — per-user isolation is *less* authentic than the real Jabberwacky's global learning: your bot only learns from you, so the "collective hive-mind that has talked to everyone" flavour is absent. Cross-session learning only persists on a **clean exit** (a hard disconnect mid-session loses that session's learning) — the same checkpoint-on-exit behaviour QUEST has, accepted for consistency. The couch is deliberately ephemeral, so the two persistent/ephemeral surfaces of the same bot behave differently (documented, but a sharp edge).
- **Neutral** — Jabberwacky is wired into the SOLO save/load/render/feed/`is_over`/`game_name` chains (like QUEST) but **excluded** from `door_post_score` and the `scores` command (no leaderboard). Match quality is word-overlap, not NLU — adequate and deterministic for a homage, not a conversational marvel. A future global-but-moderated corpus, or a learning couch, remain open (and would each need their own ADR for the abuse surface they reopen).

## Alternatives considered

- **Global shared learned corpus (the authentic Jabberwacky).** One corpus everyone teaches and draws from, `flock`'d like the chat ring. Most faithful and most interesting, but it is precisely the poisoning + privacy + escape-injection surface ADR 0012 flagged — any caller can teach the bot to replay slurs/secrets/ANSI payloads at the next. **Rejected** for a multi-user BBS without a moderation story; the per-user hybrid keeps the learning while removing the cross-user blast radius. (Decided with the operator; revisitable behind its own ADR if moderation lands.)
- **Per-user-only, no shared seed.** Safest, simplest — but a brand-new user meets a mute bot with nothing to say until they have taught it, killing the first-impression. **Rejected** in favour of hybrid: the baked-in seed gives instant personality; the per-user layer gives private learning.
- **Force `DOOR_PRACTICE` like ELIZA/PARRY (ephemeral only).** Mechanically simplest (no save path), but then "the first learning / persistent-state bot" wouldn't actually persist — the milestone's whole point. **Rejected**: Jabberwacky takes the QUEST stateful-door shape so its learned layer survives sessions.
- **Markov generation (MegaHAL-style) instead of retrieval.** Also a learning engine, but it *generates* novel text from n-gram statistics rather than replaying remembered human lines — a different (and noisier, harder-to-contain) computation. **Deferred**: retrieval is the more faithful Jabberwacky model and has a cleaner sanitization story (you replay sanitized whole lines, you don't synthesize bytes). MegaHAL remains a future, separate engine.
- **A SHA-256 / hashed word index for matching.** sigil's `sha256` is callable from a door module, but per-word crypto hashing is overkill and slower than a direct whole-word `memeq` walk over a 64-pair corpus. **Rejected**: linear overlap scoring is simpler, dependency-free at the call site, and fast at this corpus size.
