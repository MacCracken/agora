# 0016 — The Olympiad: a competition primitive (one engine, many event skins) on a games-owner frame

> **Status**: Accepted — shipped at **1.3.6** (`src/olympiad.cyr`: the owner/stable frame + the `compete()` primitive + the chariot-race event + the book + the 12-meet ladder to the tethrippon crown + solo save + `scores olympiad`). Later events (gladiators, athletics, boat crews) are thin descriptors on the same primitive. The pari-mutuel book required the `wager_payout` fractional helper added to `wager.cyr` (a favourite pays < 1× profit, inexpressible as an integer multiplier). Built across five bites; unit-tested t189–t197; smoke `docs/examples/17-olympiad.sh`.
> **Date**: 2026-06-09

## Context

The roadmap pencilled 1.3.6 in as a "training sim — fighter/horse training + competition, the cheap reskin of QUEST's daily-turn economy, and the wager module's flagship integration." In design discussion the shape grew, deliberately, into something better: an **Olympiad** — a Greco-Roman games empire in which you are not the athlete but the **owner** (a *dominus* / *lanista* / circus-faction boss) who fields a **stable** of competitors across many kinds of contest and bets on all of them.

The unlocking insight is that every event a games-owner stages is the *same shape*:

> a **field of competitors weighted by form** → **one draw picks the winner (and order)** → **the same weights book the bets**.

A chariot race, a gladiatorial bout, a foot race, a wrestling match, a trireme regatta — they differ only in their *field-builder* (who lines up) and their *flavour* (what the screen says). The validation, the draw, the odds, the settlement are identical. agora already has a name for this: the door PRNG ([ADR 0009](0009-door-games-subsystem.md)) is one xorshift under many games; the world-transaction framework ([ADR 0010](0010-persistent-universe.md)) is one lock-read-compute-write under many worlds; the wager module ([ADR 0013](0013-wagering-module-rng-fairness.md)) is one bet→draw→resolve→settle under many tables. **The competition is the next instance of that pattern** — and the Olympiad is the venue that hosts it.

This also gives the wager module ([ADR 0013](0013-wagering-module-rng-fairness.md)) its flagship. In the 1.3.5 casino integrations the module was a *side bet* bolted onto a door. Here it is **load-bearing for the core mechanic**: the race result and the betting odds are the *same* `wager.cyr` weighted draw. Training your team raises its weight, which both improves your real chance of winning *and* shortens your odds at the book — one number, two consequences.

The owner frame (rather than "be the athlete") is the right lens for three reasons: (1) it makes betting on your *own* competitor coherent — an owner backs his stable; (2) it makes betting on *others* coherent — an owner is a gambler at the Games; and (3) "**choose to train or not**" becomes the strategic core of the daily-turn economy: spend a turn sharpening a fighter, rest a spent chariot team before its race, or pocket the money and gamble on someone else's blood.

The tone is **Greco-Roman**: Rome paying its cultural debt to Greece by staging *both* the Greek athletic Games (the *stadion*, wrestling, boxing, pankration) and its own circus and arena (chariot factions, gladiatorial *munera*), with regatta boat races in the Greco-Roman style. The Greek umbrella name (Olympiad — the four-year games cycle) keeps agora's Greek naming lane crisp while the events range across the classical world.

## Decision

**Build `src/olympiad.cyr` as a games-owner management door with one event-agnostic `compete()` primitive that resolves every contest as a form-weighted kernel-CSPRNG draw and books every bet through `wager.cyr`. Ship the owner frame + the primitive + the chariot-race event at 1.3.6; add later events as thin descriptors.**

### The owner / stable frame

You own a **stable** of competitors. Each competitor is a fixed i64 block: an event type, a set of stat slots (a chariot team's Speed / Stamina / Handling / Nerve), a condition (freshness), and identity (name, circus faction). The owner holds money (denarii), a day counter, a per-day **action ration** (the QUEST daily-turn economy), and season/ladder progression toward the championship crown.

The daily economy is **allocation under scarcity**: each day grants a few actions, spent on **train** (raise a stat, at a condition cost — fatigue), **rest** (restore condition), **manage** (buy / sell / scout competitors), or simply **bet** and watch. Training has diminishing returns and a cap; over-training leaves a competitor spent on race day. This is the strategic "train or not" tension, and it is the QUEST `qu_day_tick` rationing skeleton reused.

### The `compete()` primitive (event-agnostic)

Given a **field** of N entrants and their **forms** (one i64 weight each, computed by the event's form function from its stats × condition), `compete()`:

1. **Resolves the result** — a weighted draw over the forms from the **kernel CSPRNG** picks the winner; a *sequential* weighted draw (pick ∝ form, remove, repeat) produces the full finishing **order** for place/show. The pure weight→index mapping (`ol_pick_weighted`, the injected test seam) is split from the CSPRNG read (`wager_uniform_csprng`), exactly as `wager.cyr` splits `wager_pick` from `wager_uniform_csprng`.
2. **Prices the book** — each entrant's fair odds come straight from the forms (profit fraction `(W − wᵢ) / wᵢ` for total form W), with the house vig as a documented edge. A player bet on any entrant settles through `wager.cyr`'s validated, no-negative-balance settlement.

So `compete()` is mostly a *field → odds + winner* function; `wager.cyr` remains the settlement engine. An **event** is then just: a field-builder (your entrant + generated rivals), a form function, and render/flavour text. Chariot racing is the first; gladiators, athletics, and boat crews are added the same way the casino added three tables to one module.

### The fairness split (extends ADR 0013)

The boundary the casino drew between replayable and non-replayable randomness moves up to the event level:

- **The rival field is generated from the seeded `door.cyr` PRNG** (replayable) — a save replays the *same* season's opponents and schedule, so progression is deterministic and testable.
- **The race winner is the kernel CSPRNG** (non-replayable) — the one thing the player is betting on is the one thing they cannot predict, reconstruct from a save, or replay. Training shifts your *weight*; it never makes the result a foregone, reconstructable conclusion.

This is the same "reproducible where it should be, unpredictable where money rides on it" line ADR 0013 drew for the wager draw, now applied to the contest itself.

## Consequences

- **Positive** — one competition engine makes an open-ended anthology of events cheap: each new sport is a descriptor (a field-builder + a form function + flavour), not a new game, the same way 1.3.5 added three casino tables to one module. The wager module finally earns flagship status — load-bearing for the core mechanic, not a side bet, with the result and the odds derived from one set of weights. The owner frame supports multiple competitors and a real strategic economy ("train or not") while reusing QUEST's proven daily-ration skeleton. The fairness split is the audited ADR-0013 boundary reapplied, so the betting stays honest. Real-stakes accounting (purses + bets) reuses the 1.3.4-reviewed `wager_settle` no-negative invariant.
- **Negative** — this is bigger than the 1.3.5 casino integrations: a full new door (state, economy, an event, an owner loop, save, scores), closer to a QUEST-sized cut than the "cheap reskin" the roadmap first imagined. Pari-mutuel odds are *fractional* (a strong favourite pays less than 1× profit), which `wager.cyr`'s integer-multiplier `wager_resolve` cannot express — so the book needs a small **fractional-payout helper** added to `wager.cyr` (a num/den profit with the staged-overflow-safe edge haircut), landing with the wager UI. Season balance (training curves, purse sizes, field strength by tier) is new tuning that will need play-testing.
- **Neutral** — wagering only matters where there is persistent money, so the rich loop is Solo/login-gated; a Practice owner can stake ephemeral coin. The Greco-Roman scope is broad by design; the Greek umbrella name and the shared primitive keep it coherent. The competition draw is one CSPRNG read per place resolved — negligible at human-paced play.

## Alternatives considered

- **Be the athlete (the original "training sim")** — you *are* the fighter/charioteer, training your own stats. Rejected: the owner frame is strictly richer (a stable, not a single body), it is what makes betting on your own competitor *and* on the rest of the card coherent, and "choose to train or not" only becomes a real decision when you are allocating an owner's scarce turns across competitors rather than grinding your own.
- **One bespoke door per sport** — a chariot door, a gladiator door, a regatta door. Rejected for the same reason ADR 0010 rejected per-game bespoke concurrency and ADR 0013 rejected per-game bespoke wagering: N divergent implementations of field, draw, odds, and settlement is N times the surface and N places to get the real-stakes math wrong. One `compete()` primitive, many event descriptors.
- **Reuse `wager_resolve`'s integer multipliers for the odds** — keep the casino's fixed-integer payout table for race betting. Rejected: pari-mutuel odds are continuous and favourites pay fractional profit (e.g. 3:2), which floors to a broken 0× under integer multipliers. The book needs a fractional num/den payout — a clean `wager.cyr` addition, not a reason to distort the odds into integers.
- **Seed the race winner too (fully replayable)** — let a save replay the exact results. Rejected: the result is the thing money rides on; a replayable, save-reconstructable winner is an exploitable book, exactly the failure ADR 0013 exists to avoid. The field is seeded; the winner is CSPRNG.
- **A pari-mutuel pool (bets set the odds)** — true tote betting where the odds float with how the crowd bets. Rejected for the first cut as far more machinery (a shared betting pool, live odds recomputation) than a single-player door needs; fixed form-derived odds with a documented vig is honest and sufficient. Revisit if a Universe (shared-world) Olympiad ever pools bets across callers.

### Open questions (deferred, not gaps)

- **Stable size + acquisition** — start with one chariot team; how competitors are bought/scouted/retired, and whether different event types share one stable or compartmentalize, is a 1.3.6 loop-bite decision.
- **Season structure** — the ladder of meets and the championship/crown win condition (QUEST's twelve-master spine is the reference); whether progression is per-Olympiad (four-year cycles) is flavour to settle as the loop lands.
- **Wall-clock vs turn-based day** — QUEST's daily ration is wall-clock (`clock_epoch_ns`, the "see you tomorrow" hook); a season ladder might prefer a turn-based "advance day." Decided with the loop bite.
- **Cross-event form** — a single athlete competing across events (a pentathlete) vs specialised competitors per event. The primitive is agnostic (it takes forms); the descriptor decides. Settled per event as events are added.
