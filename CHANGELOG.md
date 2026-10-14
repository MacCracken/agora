# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.12.0] — 2026-10-13 (Olympiad events + door content)

The doors get their missing content. The Olympiad gains the three events its competition engine was built for:
- the gladiatorial bout, the stadion foot race and the regatta, beside the chariot race;
- a market to hire a competitor for each, and a race field that grows from four entrants to eight up the ladder.

Elsewhere:
- Decode/Words accepts real English words (8,636 of them) instead of only its 532 answers.
- Smuggler's Ledger, Port Authority, The Handler and the Olympiad get the wall-clock daily ration their ADRs
  described: a saved run advances at most `--door-days` game days per UTC day (ADR
  [0032](docs/adr/0032-daily-ration.md)).
- Ashes of Empire no longer closes for good when one player takes the map: the age turns, and the victor's win
  is posted.
- Each Port Authority Universe ship rolls its own dice.

The six rows of roadmap § 1.12.0, closing audit 1.8.1 I4–I7.

**274** tests (259 module + 15 serve-layer), also on aarch64 under qemu; both fuzz harnesses plain and
`--poison=ab`; **38** example smokes (new: 38), both CI legs green; `cyrius audit` exit 0. `build/agora`
**1,041,936 → 1,109,304 B** (about 43 KB of it the guess dictionary); `--agnos` 1,038,496 → 1,101,768 B;
`--aarch64` 2,483,528 → 2,530,408 B. Closeout Pass run (minor bump).

### Breaking

- **Saved door runs are rationed by default.** A Solo or Universe run of Smuggler's Ledger, Port Authority, The
  Handler or the Olympiad now advances at most 10 game days per UTC day: a jet, `n`, `e` or `[N]ext-day` past
  that is refused with "That's all the days a run gets today -- it picks up again tomorrow (UTC)", and the
  header shows "N more today". Practice runs are not rationed. **Migration:** `agora serve --door-days 0`
  restores the old behaviour; any other number from 0 to 1000 sets the allowance (`--door-days 2` is ADR 0009's
  original BBS rhythm). Smoke 10, which plays a whole quarter in one sitting, now runs with `--door-days 0`.

### Fixed

- **Ashes of Empire closed for good after a domination** (audit 1.8.1 I6). Once one player held all twelve
  provinces their run was over on every visit, and no one else could found an empire (no neutral province
  was left). The victor's win reached `scores ashes` only if they were connected when the turn resolved: a
  domination found by the resolution their own entry ran was counted as "already over" and never posted. Now
  the turn that completes a domination ends the age (ADR 0014 amendment):
  - the map is re-minted from the next seed, with new terrain and neutral garrisons;
  - orders and pacts are swept away;
  - the victor's fingerprint is left as a laurel. They claim it on their next visit or line, whenever that is:
    "THE AGE IS YOURS", an Imperator row (1,200) on the leaderboard, once;
  - everyone else is founded in the new age, with the news if they saw the old one.

  The launcher now takes "over at entry" before the world opens, so a claim on entry posts.
- **Every Port Authority Universe ship rolled the same dice** (audit 1.8.1 I7). The launcher seeded each new
  Universe ship with the galaxy seed (`DD_UNI_SEED`), so their combat / event PRNGs started identical. `pa_new`
  keeps the galaxy seed for the shared map in Universe mode and seeds the ship from the launcher's clock. The
  descriptor slot is gone (ADR 0010 / 0020 notes). Existing ships keep the PRNG cell they have.

### Added

- **The Olympiad's later events** (ADR 0016 amendment), each one descriptor block in `ol_events_init` with no
  change to `compete()`, the book, the ladder or the save format:

  | Event | Stats | Contest costs | Purse | Venues |
  |---|---|---:|---:|---|
  | the gladiatorial bout | Strength / Endurance / Skill / Courage | 35 | 130% | Fidenae → the Flavian Amphitheatre |
  | the stadion | Pace / Wind / Start / Grit | 12 | 70% | Elis → Olympia |
  | the regatta | Oarpower / Stamina / Helm / Timing | 25 | 110% | Ostia → the Naumachia of Augustus |

  - Each event's form weights its four stats differently (they sum to 8; the chariot's even weights are the
    old plain sum). Each has its own rivals and crown ("the wooden sword", "the olive wreath", "the naval
    crown").
  - **The market** (`h`) hires one competitor per event for denarii (90 to 220); `s` switches between them.
    The twelve-meet ladder is the owner's standing, shared by the whole stable: a win in any event climbs
    it, and a win at the last meet takes that event's crown.
- **The field grows with the meet**: four entrants at the first meet, then 5, 6, 7 and eight at the last
  (`ol_field_size`). It was a flat four.
- **Decode/Words' guess dictionary** (ADR 0018 amendment): every five-letter ENABLE word plus every answer,
  8,636 words, sorted, checked by binary search. The 532-word answer pool is unchanged word for word and in
  order, so seeded games and the Handler's decrypt lever replay the same secrets; t258 pins it with a hash.
  `scripts/gen-decode-guesses.py` regenerates the list and records its source, checksum and rule.
- **The daily ration** (ADR [0032](docs/adr/0032-daily-ration.md)), in `door.cyr`:
  - `door_ration_take` / `_peek` / `door_emit_ration`, with two cells per game: the UTC day of the last refill
    and the days left.
  - Gated at the one call that advances a day in each of the four doors. The Olympiad's `OL_LASTDAY`, saved
    but never read until now, is its ration day.
  - The cells are appended to each save, so a 1.11 save loads with a fresh ration and a 1.12 save still loads
    in 1.11.
  - A new UTC day refills; so does a clock that went backward.
  - `agora serve --door-days N` (digits only, 0 to 1000, anything else exits 2) sets the allowance, and the
    startup lines show it.
- Tests: **t256** (Port Authority dice), **t257** (Ashes ages, the v3 upgrade, the laurel), **t258** (the guess
  dictionary), **t259** (the Olympiad events), **t260** (the ration in all four doors and their saves), **s15**
  (`--door-days`). **Smoke `38-door-content.py`**: all four changes over the wire, both serve models,
  including a crafted v3 Ashes world turned and claimed.

### Changed

- **Ashes' world snapshot is v4** (3,048 → 3,072 bytes): it appends the age, the unclaimed laurel and the last
  victor. A v3 snapshot is **upgraded in place** rather than set aside, so running worlds keep their empires; a
  corrupt v3 is still refused and left untouched. The frame's header shows the age. The per-player save
  appends the last age seen.
- The Olympiad loader refuses a save that names an event that does not exist (an event indexes the descriptor
  table), and clamps stats and condition into range.
- `ol_form` replaces `ol_chariot_form`, `ol_build_field` replaces `ol_build_chariot_field`, and
  `decode_word_index` left `src/` (only the tests asked it once the guess dictionary existed). `OL_RACE_FIELD` /
  `OL_RACE_COND` became `OL_FIELD_BASE` and the per-event costs.
- README: the source tree lists `decode.cyr`, `decode_words.cyr` and `descent.cyr`, and the smoke list names
  32–37, which it had left out.
- CLAUDE.md's allocator gate lists the Olympiad's event table among the deliberate once-per-process
  allocations; `--door-days` is in `agora help` and the getting-started guide.

### Verification

- `cyrius test`: **259/259** + **15/15**, the same under `cyrius test --aarch64`. Both fuzz harnesses plain and
  `--poison=ab`. `cyrius audit` **exit 0**. `scripts/check-version-sync.sh --tag 1.12.0` OK;
  `scripts/check-toolchain.sh` OK.
- `docs/examples/run.sh`, both CI legs as CI runs them: **fork 25/25, poll 37/37**.
- **Mutation-checked, 35 mutants, all caught**: the galaxy not shared, the ship's dice from the galaxy seed;
  domination never ending the age, eleven provinces dominating, the laurel not cleared, a v3 not upgraded, a
  corrupt order count accepted, the pacts kept, a claimed laurel not over, an online player not refounded, and
  "over at entry" taken after the claim (smoke 38); the search missing the last word or going the wrong way,
  the answer pool reordered, no dictionary check; the munus weights, a flat field, rivals all chariots, purse and
  cost ignoring the event, a second hire per event, a free hire, an unknown event loaded, the crown event
  unrecorded; no refill on a new day, Practice rationed, a lowered allowance ignored, a take that does not
  count, each of the four gates removed, the ration cells dropped from two saves; `--door-days` taking a
  letter.
- **A/B against a `git archive` 1.11.1 build**: smoke 38 fails 24 checks there (§ A cannot start; every
  § B–D change), and passes here twice running under both models.
- Benchmarks: `benches/serve-bench.py all`, A/B with 1.11.1 in the same session, unchanged within noise
  (BENCHMARKS.md § Serve-level — 1.12.0); `bench_telnet.bcyr` unchanged. The parser and the serve loops are
  untouched.
- Closeout: the dead-code floor is the same 10 test-only accessors. The tree-wide deferral lint shows the same
  4 known false positives. The security re-scan found one new bare `alloc()`, the Olympiad's event table: once
  per process, built with the door registry. There are no new plain store opens. `ol_emit_item` honours the
  door emitter cap. `s13`'s 200-drive leak check passes for every door with the new events, the market and the
  ration in place. Full build from clean, all three targets.

## [1.11.1] — 2026-10-13 (enforced module invariants)

The door registry (ADR 0020) and the door-state free hook (ADR 0022) each rested on rules that only discipline
kept:
- a door's free function must step around the session's world buffer;
- every buffer a door state owns must come from the freelist and go back;
- the chat couch must find every bot's reply at Eliza's struct offsets;
- every descriptor slot must point at the right function, which only a smoke would notice if it didn't.

Door #11 could have broken any of them silently. Each is now enforced by code or by a test that walks the whole
registry, so a new door is checked simply by being added. Closes the 1.11.x line. No player-visible change:
`help`, `play`, `scores` and a full chat-couch session are byte-identical to 1.11.0.

**268** tests (254 module + 14 serve-layer), also on aarch64 under qemu; both fuzz harnesses plain and
`--poison=ab`; **37** example smokes, both CI legs green; `cyrius audit` exit 0. `build/agora` **1,042,240 →
1,041,936 B**; `--agnos` 1,034,704 → 1,038,496 B; `--aarch64` 2,483,832 → 2,483,528 B.

### Changed

- **One release point for door states.** `door_release_state` is now the only place a door's `DD_FREE` runs: on
  quit, on a disconnect and for the chat couch. It first clears a Universe state's world field (`DD_WORLD_OFF`),
  which points at the session slot's `alloc()` buffer rather than memory the state owns. Before 1.11.1 a door's
  `*_free` that forgot to step around it would have put that buffer on the freelist and corrupted the pool.
  Now the most it can free through the field is 0 (ADR 0022 amendment).
- **The chat couch is in the registry.**
  - A bot is any door with a `DD_COUCH_CMD`; its reply prefix, `/help` blurb and opening note are descriptor
    data, and its reply comes from a new `DD_REPLY` function (`ez_reply`, `py_reply`, `jw_reply`).
  - This retires ADR 0012's shared-offset ABI: PARRY's and Jabberwacky's reply had to sit at Eliza's offsets
    8 / 16, kept true only by "== EZ_RESP" comments.
  - The three hand-written `/eliza` / `/parry` / `/jabberwacky` blocks and the 3-way `chat_bot_*` switches are
    gone, and the three per-session state fields became one table indexed by game id (`SESS_COUCH`).
  - `g_chat_bot` holds the bot's game id.
- **Names come from the registry.** `play` and `scores` look a name up in the registry (`door_game_by_name`;
  `scores` matches only a door with a leaderboard). Their usage lines and the `help` door list are generated
  from it. That removes two hand-kept chains of the ten names. `GAME_LAST` bounds every walk over the fleet.
- CLAUDE.md's release-check allocator gate ("mixed-allocator scan") now cites `s13` / `s14`, which enforce it
  for every door.

### Added

- `tests/serve.tcyr` **`s13` registry conformance**. It walks every id up to `GAME_LAST`:
  - **Registration:** a descriptor must exist, under a name the parser finds.
  - **Capability slots:** a save needs a load, a score a rank, a Universe game its whole world set (with a fresh
    world its own validator accepts), and a couch bot its reply.
  - **The drive:** render, five input lines, is-over, reply, score / rank, and a save round-tripped byte for byte
    through its load.
  - **Leaks:** another 200 drives after a warm-up must move neither the bump heap (an `alloc()` that belonged on
    the freelist), nor the freelist arena (a buffer the door's free misses), nor the data segment.
- **`s14` world-pointer guard**: a hostile `DD_FREE` on every Universe door, through all three release paths, is
  never handed the session's world pointer.
- Mutation-checked: 11 mutants, all caught:
  - a door left unregistered; a load slot mis-wired; a save slot, a rank slot or a couch reply missing; a couch
    reply pointing at the wrong function; a world validator crossed between doors;
  - `jw_free` missing one buffer; PARRY's counters on `alloc()`; the release keeping the world field; the
    `scores` lookup ignoring the leaderboard requirement.

### Verification

- `cyrius test`: **254/254** + **14/14**, the same under `cyrius test --aarch64`. Both fuzz harnesses plain and
  `--poison=ab`. `cyrius audit` **exit 0**. `scripts/check-version-sync.sh --tag 1.11.1` OK.
- `docs/examples/run.sh`, both CI legs as CI runs them: **fork 25/25, poll 36/36**; the couch smokes (12 Eliza,
  13 PARRY, 15 Jabberwacky) pass in both models.
- **No visible change**: `help`, `play nosuch`, `scores` (with no name, a door without a leaderboard and an
  unknown name) and a 14-step chat session are byte-identical to a `git archive` 1.11.0 build. The session
  covers `/help`, each bot, switching between bots, `bye`, an unknown command and `/leave`.
- Dead-code audit: the same 10 test-only accessors. Full build from clean, all three targets.

## [1.11.0] — 2026-10-13 (Descent as a session state + serve-model debt)

A player in the Descent no longer freezes everyone else, and comes back with a working terminal. Until now a
visit to the MUD was a blocking call that owned the process. Under the poll model (and always on agnos), every
other session stopped for the whole visit, and a dead endpoint cost the sweep 4 s per attempt. On return,
agora reset its telnet options and re-announced them. A client ignores `DO` for an option it already has on, so
agora was left believing NAWS and LINEMODE were merely requested: wrapping stopped for the rest of the session,
and LINEMODE clients typed blind. Both problems were reproduced with GNU `telnet` against the real MUD.

1.11.0 makes a visit a session state that both serve models drive. It resyncs the options from what the client
actually agreed during the visit. The poll loop now waits on readiness instead of a 20 ms tick, and fork children
leave with their parent. ADR [0031](docs/adr/0031-descent-session-state.md), amending 0007, 0017 and 0023.

**266** tests (254 module + 12 serve-layer), also on aarch64 under qemu; both fuzz harnesses plain and
`--poison=ab` (the IAC harness gains a sixth pass: the Descent observer and the resync); **37** example smokes
(new: 37), both CI legs green; `cyrius audit` exit 0. `build/agora` **1,029,584 → 1,042,240 B**; `--agnos`
1,026,096 → 1,034,704 B; `--aarch64` 2,483,464 → 2,483,832 B. Closeout Pass run (minor bump).

### Breaking

- **`AGORA_SERVE` accepts `fork` and `poll` only.** Any other value is refused before anything binds: `agora
  serve` exits 2 and says why. `epoll` used to be accepted and silently mean `poll`, and a typo silently meant
  the default, so an operator who asked for a model could get another one without a word. **Migration:**
  `AGORA_SERVE=epoll` → `AGORA_SERVE=poll`. Behaviour is unchanged, and since this release `poll` waits on
  readiness.

### Fixed

- **A Descent visit froze the poll server.** Every other session waited for the whole visit; another session's
  `whoami` timed out after 8 s in the 1.10.1 A/B. Now it is answered in 0.1 ms, and in 0.2 ms while someone
  dials an endpoint that never answers (it used to take 3.5 s). The dialler is still told "not answering" at
  the 4 s deadline.
- **Returning from the Descent broke the window width and LINEMODE echo for the rest of the session.**
  - **What happened:** after any visit, `read` came back 200 columns wide instead of 39, and a LINEMODE client's
    typed line was invisible until Enter. agora reset its option state and re-announced. The client, which still
    had NAWS and LINEMODE on, ignored the `DO`s. Its fresh window report then arrived for an option agora
    believed only requested, and since 1.8.1 a subnegotiation counts only for an agreed option, so it was
    dropped. agora also took echo back from a client still in EDIT mode.
  - **The fix:** a passive observer watches the negotiation the proxy carries. On return agora adopts what the
    client holds and negotiates only the differences. Verified with GNU `telnet` in LINEMODE and character
    mode, under both models, through the MUD's passphrase echo toggle.
- **Fork connection children outlived their parent.** At a clean shutdown the parent waited 5 s and exited,
  leaving live children running as orphans. A crashed or SIGKILLed parent left them all. Now the parent signals
  its children, and each says goodbye and saves its door before leaving: shutdown takes 0.5 s instead of 5.
  `PR_SET_PDEATHSIG` ends a child whose parent dies (ADR 0007 had left this open).
- **The poll loop slept 20 ms per sweep.** It accepted at most 50 sequential connections a second, and every
  poll-mode command waited 0–20 ms for the next tick. On Linux it now waits in `poll(2)` on what is ready.
  agnos has no `poll` and keeps the paced sweep.
- **Found before release by the new fuzz pass:** when the reply queue had no room for a refusal, the resync left
  an option agora refuses held *on*, so the RFC 855 gate would accept subnegotiations for it. A refused option
  is now always recorded off (fuzz invariant 17; `t255` § G).
- **Two subnegotiation requests could be torn**: TERMINAL-TYPE `SEND` and the LINEMODE `MODE` request were
  pushed byte by byte. They are now queued whole or not at all, like every other reply since 1.10.0.

### Changed

- **The Descent link is `MODE_DESCENT`.**
  - `descent` dials and returns at once. On Linux the connect is non-blocking (the stdlib's `sock_connect`, with
    no raw socket syscall), finished by a zero-timeout `poll` and abandoned after 4 s.
  - `descent_pump` moves bytes once per sweep (poll) or wakeup (fork) in both directions. Client bytes wait in
    the receive buffer until the MUD takes them, and the MUD is read only while the client's queue has room for
    a whole read.
  - The bytes pipelined behind `descent` are parked as the first bytes for the MUD, replacing 1.6.5's `g_pipe_*`
    globals.
  - Every line to the client goes through the session's own queue in order, so 1.8.1's `session_flush_now` is
    gone.
  - agnos still connects with the kernel's blocking call (about 8 s), behind the existing 30 s redial cooldown.
- **Fork children** wait in `poll(2)` on their socket, their own shutdown signalfd and, during a visit, the MUD
  socket. They keep SIGINT / SIGTERM blocked on purpose, routed to that signalfd; 1.7.0 unblocked them. Smoke 28
  now checks "blocked only with a signalfd draining them" and that the child says goodbye.
- **Accept-loop rate limiting** moved to roadmap § Unscheduled after a re-check. agnos still has neither
  `getpeername` nor a peer address from `sock_accept`, so ADR 0023's reasoning holds.

### Added

- `telnet.cyr`: the negotiation observer (`tobs_init` / `tobs_feed` / `tobs_on`) and `telnet_resync`.
  - The observer treats an option as on once its owner said `WILL` and the other side `DO`, and off on any
    `WONT` / `DONT`.
  - It keeps the client's window report and any acknowledged LINEMODE mode, starts from agora's own state, and
    remembers what was on before the visit, so an option the client had refused is not asked for again.
- `docs/examples/37-descent-state.py`: 21 checks under both models, with a built-in fake MUD, plus a real
  inetutils `telnet` in a 40x24 pty. A 1.10.1 build fails 11 of them.
- Fuzz pass 6 (`fuzz/telnet_iac.fcyr`): 3,000 simulated visits feeding about 860 KB to the observer in split
  pieces, from both directions. A guard band checks the observer's bounds, and the resync runs against a reply
  queue already partly full. New invariants 24 (the observer's ranges) and 25 (the resync's replies whole).
- Tests: `t254` the observer, `t255` the resync (scenarios A–G); serve `s11` the Descent state against a
  loopback fake MUD, `s12` a fork child's lifecycle (its signalfd sees SIGTERM; PDEATHSIG is SIGTERM; the pid
  table). Mutation-checked:
  - 14 + 2 observer / resync mutants, all caught by the module suite (the 2 also by the fuzz harness);
  - 4 fuzz-pass mutants;
  - 9 Descent-wiring mutants and 4 fork-lifecycle mutants, all caught by the serve suite.

### Performance

- `benches/serve-bench.py all`, the new build and 1.10.1 in the same session:
  - **poll accepts: sequential 50 → 8,386 conn/s, 8 concurrent 618 → 10,534** (fork unchanged, ~3,700 /
    ~7,700);
  - per-session memory: poll 12.7 → 12.6 KB; fork 54 → 56 KB PSS, measured from the same filesystem and within
    its 4 KB run-to-run spread;
  - world lock ~510 txn/s; `read` 0.62 / 1.43 / 2.52 ms against 0.71 / 1.42 / 2.53 for 1.10.1; unknown login
    0.20–0.25 ms on both. All unchanged.
- `bench_telnet.bcyr` (9 / 64 / 74 / 103 / 167 ns) and `bench_term.bcyr` (3.1 / 4.0 / 19.4 / 40.4 µs):
  unchanged.

### Verification

- `cyrius test`: **254/254** + **12/12**, the same under `cyrius test --aarch64`. Both fuzz harnesses plain and
  `--poison=ab`. `cyrius audit` **exit 0**. `scripts/check-version-sync.sh --tag 1.11.0` and
  `scripts/check-toolchain.sh` OK.
- `docs/examples/run.sh`, both CI legs as CI runs them, on 4 CPUs: **fork 25/25, poll 36/36**. Smoke 20 (the
  real Yeoman's Descent MUD) and 24 (a fake MUD logging every byte) pass under both models.
- Allocator gate, poll server: 300 back-to-back Descent visits grew the data segment by **0 KB**. The
  observer is allocated once per slot, on its first visit. The readiness wait and the pump stay idle at 0 ms
  CPU, including while a client floods a MUD that never reads (5 MB held back, no spin).
- Full build from clean (`rm -rf build && cyrius deps && CYRIUS_DCE=1 cyrius build`), all three targets.
- Dead-code audit: the same 10 test-only accessors as 1.10.1.

### Known limitations (recorded, not fixed)

- On agnos a Descent connect still blocks the sweep (the kernel's `sock_connect` has no non-blocking form, about
  8 s), bounded by the 30 s redial cooldown, and the sweep is still paced at 20 ms (no `poll`).
- A fork child parked in a 60 s blocking write to a stalled client sees SIGTERM only after the write gives up.
- If a visit ends while the client is in the middle of a telnet command, the rest of that command reaches
  agora's parser as data.

## [1.10.1] — 2026-10-13 (terminal-aware output)

agora has asked every client for its window size since M1 (NAWS, RFC 1073) and stored the answer, and until now
nothing read it. Every line went out as written, so anything wider than the reader's terminal broke wherever
the terminal ran out of columns, mid-word. That covered door menus, `list` subjects, long post lines, chat,
`help` (143 columns) and the greeting (149). Output is now wrapped to the reported width, between words. A client
that reports no width gets exactly the bytes it got before. Closes the 1.10.x line. ADR
[0030](docs/adr/0030-terminal-aware-output.md).

**262** tests (252 module + 10 serve-layer), also on aarch64 under qemu; **two** fuzz harnesses (new:
`fuzz/term_wrap.fcyr`), each plain and `--poison=ab`; **36** example smokes (new: 36), both CI legs green;
`cyrius audit` exit 0. `build/agora` **1,017,104 → 1,029,584 B**; `--agnos` 1,013,616 → 1,026,096 B;
`--aarch64` 2,417,728 → 2,483,464 B (+17,464 B of code; the rest is the data segment moving to the next 64 KB
alignment step).

### Added

- **Output wrapped to the client's window.** Once a client reports a width (`WILL NAWS` + `SB NAWS`), lines wider
  than width − 1 break at the last space or TAB that fits. The whitespace at the break is dropped, and each
  continuation row starts with CR LF and a hang:
  - door frames: each line's own indent;
  - `list`: under the subject (`1  [qix]  `);
  - `read`: the `Subject:` line under itself, the body keeping each line's indent, the `Replies:` list between
    ids under the first id;
  - chat, scrollback and live tail: after `<handle> `;
  - the chat-couch bots: after `ELIZA: `;
  - `help`: under the description column.

  A word wider than a whole row (a URL, a hash) is never cut: it goes out on a row of its own and the terminal
  wraps it, so a copy of it stays whole. A resized window applies on the next command. A width of 0 ("no width
  is being sent", RFC 1073) means no wrap. One column is left free for terminals without the VT100 last-column
  flag.
- **`src/term.cyr`** — pure display width and word wrap. Widths are counted in characters: UTF-8 as one column,
  East Asian Wide / Fullwidth and emoji as two, combining marks as none, TAB to the next multiple of 8, escape
  sequences as none and never split. The wrap is a resumable state machine with no allocation, writing chunks of
  any size. `send_wrapped` (`main.cyr`) drives it; stored and user text is sanitized (ADR 0024) **before** it is
  measured, then gets NVT newlines and IAC doubling as in `send_text`.
- **The greeting fits 80 columns.** Its 149-column tagline is laid out for 80, because it goes out before any
  NAWS can arrive (+3 bytes).
- `fuzz/term_wrap.fcyr` — 6,000 adversarial texts (6.1 MB: words, TABs, CR / LF / CR LF, SGR, a CSI with a space
  inside, lone ESC, 2–4-byte and wide UTF-8, malformed bytes), each wrapped four ways at random widths, hangs,
  start columns and chunk sizes. Seven invariants: nothing but whitespace dropped and breaks only at whitespace
  (an input/output alignment walk); no escape sequence split (by the harness's own CSI parser, not term.cyr's);
  output independent of the chunk size; rows within the width unless one unbreakable word; identity when
  everything fits; no chunk past its cap; no runaway. In CI and the release workflow beside the IAC harness.
- `benches/bench_term.bcyr`; `docs/examples/36-terminal-width.py`. Smoke 36 drives the real server under both
  models with raw bytes (§ A–F) and a **real inetutils `telnet` in a 40x24 pty** whose own NAWS fits `read` to
  39 columns (§ G). A 1.10.0 build fails 15 of its 24 checks.
- Tests: `t250` display columns, `t251` row ends, `t252` the wrap byte for byte in chunks of 1 / 3 / 7 / 4096;
  serve `s09` (wrapping on a live session over the wire: `read`, `list`, a door frame, the reply list, chat,
  `help`, a resize; still sanitized and CR LF) and `s10` (the greeting at 80 columns). Mutation-checked:
  25 `term.cyr` mutants, all caught by the module suite; 13 wiring mutants in `main.cyr`, all caught by the
  serve suite.

### Changed

- **`list` composes each row and sends it once** (it was seven sends: id, `  [`, handle, `]  `, subject, CR LF).
  The bytes are unchanged. Under fork it is one `write(2)` per row instead of seven (see § Performance).
- CI and release run both fuzz harnesses; CLAUDE.md's Quick Start and Closeout Pass name both.
- The getting-started guide says what a window-reporting client gets.

### Performance

- `cyrius bench benches/bench_term.bcyr`: a door frame that fits takes **2.9 µs**, wrapped at 40 columns
  **3.8 µs**; a 4 KB body that fits **19 µs**, wrapped **40 µs**. A line with no TAB whose bytes fit is copied
  without being measured; the first cut, which measured every character through a call, took 8.7 / 8.9 / 63 /
  64 µs.
- `read` of a 60 KB post, poll-server CPU per command: no NAWS 1.0 ms (unchanged — the old path);
  70-column lines 1.3 ms at 80 columns, 2.1 ms at 40; 950-column paragraphs 1.7 ms at either width.
- **`list` of 300 posts under fork: 16.1 → 4.3 ms** (median of 40), with or without NAWS. Poll: ~23.2 ms
  either way (one sweep).
- `bench_telnet.bcyr` unchanged (`src/telnet.cyr` is untouched): 8 / ~64 / ~73 / ~102 / ~165 ns.

### Verification

- `cyrius test`: **252/252** + **10/10**, the same under `cyrius test --aarch64`. Both fuzz harnesses plain and
  `--poison=ab`. `cyrius audit` **exit 0** (fmt, lint 0 warnings, docs, tests, bench).
  `scripts/check-version-sync.sh --tag 1.10.1` and `scripts/check-toolchain.sh` OK.
- `docs/examples/run.sh`, both CI legs as CI runs them, on 4 CPUs: **fork 25/25, poll 35/35**.
- **No NAWS, no change**: one session's `help`, `boards`, `enter`, `list`, `read` (UTF-8 and CJK subject, TABs,
  a bare CR, 40 replies) and an unknown command are byte-identical to a `git archive` 1.10.0 build. Only the
  greeting differs, as intended.
- Allocator gate, poll server with a 40-column window: 1,500 pipelined `read`s of a long post, 600 `list`s and
  2,000 `help`s grew the data segment by **0 KB**. Smuggler moves add 64 KB once, on the first door session, the
  same as 1.10.0; a run four times longer adds 0.
- Buffer review of the new path: `send_wrapped` (stack: state 104 B, chunk 2,048, NVT output 4,096 = 2 × chunk);
  the `list` row (316 B max in 320: the handle clamped to 32, the subject to 256); the `Replies:` composer (flush
  at 2,000 of 2,048; one id + its break ≤ 32 B); the read subject (267 in 272); `help`'s `play` line (143 in
  192); the greeting's tagline (~153 in 256). `term.cyr` reads only inside `[0, n)` and checks every multi-byte
  sequence against its end.
- Full build from clean (`rm -rf build && cyrius deps && CYRIUS_DCE=1 cyrius build`), all three targets.
- Dead-code audit: **10** test-only accessors, down from 11 — `telnet_term_cols` has its first caller.
  `telnet_term_rows` / `_type` / `_type_len` and `telnet_linemode_mask` remain test-only (below).

### Known limitations (recorded, not fixed)

- **NAWS rows and TERMINAL-TYPE still have no consumer**: no paging, and colour regardless of terminal type.
  Unscheduled, in `roadmap-future.md` § Terminal awareness.
- **A resize during a Descent visit** is reported to the MUD, not agora, so agora wraps to the stale width until
  the client next reports. Folded into roadmap § 1.11.0's "re-assert options on return".
- The width table approximates `wcwidth` by Unicode block (terminals do not agree on it either), so a character
  it gets wrong makes a row one column too wide or too narrow.
- The CLI viewers (`agora list` / `read` on stdout) are not wrapped.

## [1.10.0] — 2026-10-13 (telnet conformance)

RFC 854 and RFC 1184 are authoritative for agora; by 1.9.2 the roadmap listed seven places it deviated, and
writing the fixes against the RFC text found more. agora is now the LINEMODE server the RFCs describe — it
asks for LINEMODE, answers the MODE and SLC negotiations it owes, and hands echoing to an editing client —
and, for clients that stay in character mode, it edits the line itself. ADR [0029](docs/adr/0029-telnet-conformance.md).

**257** tests (249 module + 8 serve-layer), also on aarch64 under qemu; fuzz plain and `--poison=ab` (with
two new invariants and 656 new targeted LINEMODE frames); **35** example smokes (new: 35), both CI legs green;
`cyrius audit` exit 0. `build/agora` **1,008,768 → 1,017,104 B**; `--agnos` 1,005,280 → 1,013,616 B;
`--aarch64` 2,417,584 → 2,417,728 B. Closeout Pass run (minor bump).

### Security

- **An SLC list overflowed a stack buffer** (MEDIUM — reachable before login, once a client has agreed
  LINEMODE, which 1.10.0's announce invites). Found by this release's fuzz pass before it shipped: the SLC
  reply was built in a 256-byte buffer sized for 30 triplets, but a list may hold ~170 (the 512-byte
  subnegotiation cap), each needing an answer, and every import request appended the 120-byte table again —
  `SIGSEGV` in the harness. The reply is now bounded (`SLC_REPLY_MAX`, 250 bytes, so it also fits the reply
  queue whole); processing stops at the first triplet whose answer would not fit, and an import is answered
  once per list. Never in a release: the SLC answering it guards is new in 1.10.0.

### Added

- **AYT** is answered `\r\n[Yes]\r\n` (RFC 854: "visible (i.e., printable) evidence"); it was silently consumed.
- **IAC DO LINEMODE** joins the opening salvo (RFC 1184 § 2.1: the server asks). A client that agrees gets
  `MODE EDIT|TRAPSIG`; one that refuses or never answers stays in character mode.
- **LINEMODE MODE** per § 2.2: a client's request for a different mode is agreed and **answered** with the
  mask + MODE_ACK (agora used to store it and reply nothing, leaving the client's request hanging); the current
  mode is ignored; a MODE_ACK is switched to and never answered; undefined bits are dropped. `SOFT_TAB` /
  `LIT_ECHO` are accepted when proposed, never requested.
- **Echo hand-off**: when EDIT comes on agora sends `WONT ECHO` and stops echoing — the client edits and echoes
  the line (§ 2.2: a client does not echo while the server has WILL ECHO, so the user would have typed blind) —
  and takes echoing back with `WILL ECHO` if EDIT goes off.
- **SLC** per § 5.5 — the validation the code described and never had: a list must be whole triplets; an import
  request gets every function as `func SLC_DEFAULT 0`; an exported value is agreed with SLC_ACK, ignored when
  unchanged or already ACKed, refused `SLC_NOSUPPORT` past function 30; every IAC octet is doubled.
- **A line editor for character-mode clients**: BS, DEL and IAC EC erase the last character — a whole UTF-8
  sequence — and IAC EL the line (RFC 854), each wiped on screen with BS SP BS while agora echoes. A typo could
  not be corrected at all before: 1.6.5 only stopped BS / DEL being stored.
- **NVT text on egress** (audit 1.8.1 I12): `send_text` now sends a bare LF as CR LF and a bare CR as CR NUL
  (RFC 854: "in both directions"), across chunk boundaries — a CLI-authored post no longer staircases.
- `docs/examples/35-telnet-conformance.py` — every item above through the real server, raw bytes, both serve
  models; plus § G, a **real GNU inetutils `telnet` 2.8 in a pty** that negotiates the whole LINEMODE exchange
  and edits `whoamx<DEL>i` into `whoami` (skipped where no `telnet` is installed). A 1.9.2 build fails 18 of 20
  raw checks.
- Tests: `t243` AYT (and never a torn reply), `t244` EC / EL events, `t245` MODE negotiation + the echo
  hand-off, `t246` SLC (import, ACK rules, IAC doubling, a ragged list, function 255, a 170-triplet list),
  `t247` FORWARDMASK and unagreed subnegotiations refused, `t248` NVT newlines, `t249` UTF-8 erase; serve `s08`
  the line editor on a live session and the subnegotiation reply drain. Mutation-checked: 11 mutants (the 9
  reverted fixes and the 2 fuzz finds), 11 caught.

### Fixed

- **A subnegotiation's reply waited for the next byte.** `process_rx` drained the reply queue *before* handling
  a completed subnegotiation, so a reply it queued (a MODE answer, an SLC ACK) sat unsent until another byte
  arrived — or for good, if the subnegotiation ended the packet. `s08` pins the order.
- **The FORWARDMASK arm was dead**: it compared the subnegotiation's second byte with the FORWARDMASK code,
  but on the wire that byte is the verb (`LINEMODE DO FORWARDMASK …`). A client's FORWARDMASK is now ignored by
  rule (§ 5.7: only the server negotiates it, and agora — in EDIT mode — never needs one).
- **A three-byte negotiation reply could be torn**: pushed byte by byte, a full queue kept `IAC <verb>` and
  dropped the option, and the peer would read the next byte as the option code. Every multi-byte reply is now
  queued whole or not at all.
- **The fuzz harness had stopped fuzzing subnegotiation payloads.** Since 1.8.1 a subnegotiation counts only
  for an agreed option, and the harness never agreed any, so its structured-SB pass and its SLC sequence were
  rejected at the gate. It now agrees NAWS / TERMINAL-TYPE / LINEMODE first, adds invariants 22 (no torn unit in
  the reply queue) and 23 (the mode within its defined bits), and drives 400 whole-triplet SLC lists and every
  MODE byte — which is how the overflow above, and the undoubled function / modifier octets, were found.

### Changed

- Unrecognised subnegotiations (STATUS, NEW-ENVIRON, …) are discarded by rule — RFC 855 allows one only for an
  enabled option, and agora refuses those — rather than "for now".
- The LINEMODE mode is stored without its MODE_ACK bit (`telnet_linemode_mask`; `t22` updated).
- `text_iac_double` is replaced by `text_nvt_iac` (IAC doubling and NVT newlines in one pass; output still
  ≤ 2 bytes per input byte).
- The getting-started guide says how line editing works for each kind of client.
- **Smoke 27 (1.6.5, audit L2) moved with the line editor**: it types `a BEL b BS c DEL d` into a post and
  expected `abcd` stored, because BS and DEL were dropped; they now edit (erasing `b` and `c`), so the stored
  line is `ad`. Its guarantee — none of BEL / BS / DEL reaches storage — is unchanged and still checked.

### Performance

- `cyrius bench benches/bench_telnet.bcyr`: `announce_salvo` 132 → ~168 ns (five options instead of four);
  `plain_byte` 9, `iac_untracked` ~66, `iac_tracked_agree` ~75, `subneg_naws` ~104 ns — unchanged within noise.
- `benches/serve-bench.py all` (the Closeout baseline): accept fork 4,031 / 11,122 conn/s, poll 50 / 512;
  per-session memory poll 12.7 KB, fork 63 KB; world lock ~520 txn/s; reply 0.49 / 1.27 / 2.48 ms (0.2 ms with
  no replies); unknown login 0.16 ms — all as at 1.9.x.

### Verification

- `cyrius test`: **249/249** + **8/8**, the same under `cyrius test --aarch64`. Fuzz plain and `--poison=ab`.
  `cyrius audit` **exit 0**. `scripts/check-version-sync.sh` and `scripts/check-toolchain.sh` OK.
- `docs/examples/run.sh`, both CI legs exactly as CI runs them, on 4 CPUs: **fork 25/25, poll 34/34** — smoke
  27 failed in both on its first run (below) and passes since; 35 smokes, 20 against the sibling MUD.
- Allocator gate, poll server: 5,000 pipelined AYTs, 3,000 edited lines and 800 SLC + MODE exchanges grew the
  data segment by **0 KB** (VmData; RSS +24 KB under the AYT flood is the session's preallocated tx queue
  being touched by 45 KB of `[Yes]` replies).
- Full build from clean (`rm -rf build && cyrius deps && CYRIUS_DCE=1 cyrius build`), all three targets.
- Dead-code audit: the same 11 test-only accessors as 1.9.0 (the four `telnet_term_*` and `telnet_linemode_mask`
  among them — roadmap § 1.10.1 gives them a consumer); `text_iac_double` removed.

### Known limitations (recorded, not fixed)

- Returning from a Descent session does not re-assert agora's telnet options: the MUD's ECHO (and now LINEMODE)
  negotiation is proxied raw. Roadmap § 1.11.0.
- `IP`, `AO`, `BRK`, `EOF`, `SUSP` and `ABORT` are consumed without effect; TOGGLE-FLOW-CONTROL is still
  refused although RFC 1184 says it "should" accompany LINEMODE.

## [1.9.2] — 2026-10-13 (board policy + operator CLI)

Closes the 1.9.x line. Every board mode now changes what users can do, admin rights follow the key instead of
the handle, operators get CLI verbs for `.policy` / `.admins`, chat channels are capped, and the one
knowingly accepted serve-model risk is written down. ADR [0028](docs/adr/0028-board-policy-modes.md) (amending
0006); ADR 0023 amended.

**249** tests (242 module + 7 serve-layer), also on aarch64 under qemu; fuzz plain and `--poison=ab`; **34**
example smokes (new: 34), both CI legs green; `cyrius audit` exit 0. `build/agora` **998,552 → 1,008,768 B**;
`--agnos` 995,064 → 1,005,280 B; `--aarch64` 2,415,568 → 2,417,584 B.

### Breaking

- **`known` now means members-only.** It meant "a registered user may post", which every logged-in user is,
  so it behaved exactly like `open`. Since 1.9.2 a `known` board is **read** by logged-in members only:
  anonymous sessions get `members only` from `enter` / `list` / `read`, and `boards` shows `members only`
  instead of the post count. Posting is unchanged. **Migration:** a board set to `known` that should stay
  anonymously readable → `agora policy set <board> open` (identical posting rules).
- **A 16-hex `.admins` line is a fingerprint** and matches only that key, never a handle — even a handle that
  is itself 16 hex digits (that would let anyone register an admin's fingerprint as a handle). No agora tool
  wrote such a handle line; `agora admins list` shows how each entry is read.

### Security

- **`.admins` granted rights by handle (audit 1.8.1 I9; MEDIUM).** When a key re-registered under a new
  handle, the old handle was free for anyone to register — with the admin rights an `.admins` line gave it.
  Fingerprint entries match the key; `agora admins add` writes them (`<fp>  # <handle>`). Smoke 34 § C: after
  qix's key renames itself and someone else registers `qix`, the newcomer is refused and the key still posts.
  Handle entries keep working, with that risk, and are labelled so by `agora admins list`.
- **Chat channels were uncapped (audit 1.8.1 I10; LOW).** Any logged-in user could create unlimited
  `<store>/.chat/<name>/`. Joining a *new* channel past 64 is refused (`too many chat channels`); existing ones
  stay joinable. A cap, not an exact count: two joins racing for the last slot can both create one.
- **An unreadable `.policy` now fails closed for reading too** — members-only, alongside 1.8.1's admin-only
  for posting — so a broken `known` board cannot become world-readable.

### Added

- **Board modes** (ADR 0028): `open` (default: anyone reads, logged-in users post), `known` (members only),
  `anon` (**anyone posts, anonymous sessions included** — ADR 0006's promised anon-allowed, an explicit
  per-board opt-in for feedback / guest boards; posts render `[anon]`), `admin`. `board_can_read` gates the
  wire's `enter`, `list` and `read` (each time, not only at `enter`), and `boards`.
- **Operator CLI**: `agora policy get|set <board> [open|known|anon|admin]` and `agora admins list|add|rm <board>
  [<handle|fingerprint>]`. They validate the board and the mode, take the board lock, and write with
  `store_write_atomic` (ADR 0025); `admins add` resolves a handle through the handle index (ADR 0026) and
  refuses an unknown one; `admins rm` drops the fingerprint and any handle entry for the target. The formats
  are unchanged apart from `anon`, fingerprint entries and an inline `# comment` — hand edits still work.
- `docs/examples/34-board-policy.py` — the CLI, every mode on the wire under both serve models, and the I9
  rebinding. Against a 1.9.1 build it fails 17 of 35 checks (no CLI; `anon` read as invalid; fingerprint
  entries never matched).
- Tests: `t240` the four modes (anonymous / member / unregistered key, and an unreadable `.policy` closed both
  ways), `t241` `.admins` entries (fingerprints match only keys — a fingerprint-shaped HANDLE included; inline
  comments; a two-word line is no entry), `t242` the chat cap. Mutation-checked: 6 mutants, 6 caught.

### Changed

- **ADR 0023 records the accepted slow-typist risk** (roadmap § 1.9.2; CHANGELOG [1.6.4] argued it and never
  recorded it): a client sending one real byte every 50 s holds a slot like a slow typist, and 64 of them hold
  the server. A lifetime cap would cut legitimate long sessions and a per-source cap needs `getpeername`,
  which agnos lacks; `MAX_SESS` and the network edge are the operator's tools; revisit if agnos gains it.
- `board_admins_scan` is built on `board_admins_line_entry`, which the CLI shares, so `agora admins` edits
  exactly the entries the server matches.
- The getting-started guide's policy section is rewritten (it said `known` = `open` and that the CLI verbs
  were future).

### Verification

- `cyrius test`: **242/242** + **7/7**, the same under `cyrius test --aarch64`. Fuzz plain and `--poison=ab`.
  `cyrius audit` **exit 0**. `scripts/check-version-sync.sh` and `scripts/check-toolchain.sh` OK.
- `docs/examples/run.sh`, both CI legs exactly as CI runs them, on 4 CPUs: **fork 25/25, poll 33/33** (34
  smokes; 20 ran against the sibling MUD).

## [1.9.1] — 2026-10-13 (the reply index)

`read` stops paying for the whole board. The replies a post lists ("Replies: 2, 4") came from opening every
post on the board on every `read` (ADR 0005's scan); now they come from one index file per parent, verified
against the posts themselves (ADR [0027](docs/adr/0027-reply-index.md), amending 0005). Along the way the
store's FIFO hardening (1.9.0, ADR 0025) got its directory half.

**246** tests (239 module + 7 serve-layer), also on aarch64 under qemu; fuzz plain and `--poison=ab`; **33**
example smokes (new: 33; 32 extended), both CI legs green; `cyrius audit` exit 0. `build/agora` **990,320 →
998,552 B**; `--agnos` 986,832 → 995,064 B; `--aarch64` 2,415,528 → 2,415,568 B.

### Security

- **A FIFO where a directory belongs hung the server (MEDIUM — needs write access to the store; the
  directory half of audit 1.8.1 I11).** The stdlib's `dir_list_into` opens a directory with a plain `O_RDONLY`
  on Linux, so a FIFO in place of `.users/` (or a board) blocked the listing: with `.users` replaced, a
  `login` that fell back to scanning the users hung, and under poll so did every session —
  `32-store-hardening.py` § B, against 1.9.0: `login` never answers and a second client is never greeted.
  `store_dir_scan` now `stat`s the path and refuses anything that is not a directory before listing it
  (`store_is_dir`; Linux — agnos has no FIFOs, and its listing already opens with `AO_DIRECTORY`). The residual — a swap between the `stat` and the `open` — closes when the stdlib opens with
  `O_DIRECTORY`: filed upstream as cyrius
  `docs/development/issues/2026-10-13-dir-list-opens-directory-without-o-directory.md`. ADR 0025 amended.

### Added

- **The reply index** (ADR 0027) — `<board>/.replies/<parent>` holds one `\n<child>\n` record per reply, and
  `.replies/.complete` marks a board fully indexed. A `read` opens that one file and verifies each child it
  names against the child's own `Reply-To:`; the scan remains only for a board not yet indexed.
  - **Ordering**: a reply's record is appended and fsynced *before* the post is published, so a crash leaves
    a ghost record (verified away — a failed publish's id may be reused by an unrelated post) and never a reply
    missing from a complete index, whose silence `read` trusts. If the record cannot be written, `.complete`
    is removed and reads scan again.
  - **Build**: every post on the board — not `post_list`'s newest 4,096, so **replies older than that are
    listed now, which the scan never did** — at `serve` start (in the startup child, with the handle index) and
    for a board on its next reply. A board written by hand needs `.replies/` deleted to be re-read.
  - Records are framed so a torn one cannot merge with the next; duplicates (a rebuild over a crashed build)
    are removed at read.
- `docs/examples/33-reply-index.py` — the first smoke that checks a `Replies:` line at all: a hand-written
  board indexed at start, a CLI `--reply-to` listed at once, a hand-added reply NOT listed under a complete
  index, the rebuild after deleting `.replies/`; both serve models. A 1.9.0 build fails the index checks.
- `32-store-hardening.py` § B — the directory FIFO above, both serve models.
- `benches/serve-bench.py reply` now times `read 2` (no replies) beside `read 1` (a tenth of the board).
- Tests: `t238` the reply index (scan before the build, the build, a complete index's silence trusted,
  duplicates, ghosts, a torn record, `post_new` indexing a reply, an unreadable index file falling back, the
  directory guard, no per-post arena use in the build or the read), `t239` the startup build (every board;
  never creates a missing store). Mutation-checked: 8 mutants, 7 caught — the directory-guard mutant by
  hanging (exit 124 under `timeout`; CI's 300 s test limit fails it); the survivor removes `reply_index_prepare`'s
  store-exists guard, which is redundant (the board-lock open cannot create a missing store either).

### Changed

- **The `Replies:` line is composed in 2 KB pieces**: under fork every `send_buf` is a `write(2)`, and sending
  it id by id (~800 writes for a 409-reply thread) cost more than finding the replies. The wire bytes are
  identical — byte-compared against 1.9.0 on a 400-reply thread (a 2,038-byte line, across a piece boundary).
- `store_append_locked` takes a `durable` flag (the reply records are fsynced; the leaderboard passes 0).
- The test suite's `t_rmtree` unlinks before it lists, so it never opens a FIFO a test left behind.

### Performance

- `benches/serve-bench.py reply`, fork, 1 KB posts, interleaved A/B (load average < 1):

  | Board | `read 2` (no replies), 1.9.0 → 1.9.1 | `read 1` (a tenth of the board replies), 1.9.0 → 1.9.1 |
  |---|---|---|
  | 500 posts | 2.83 → **0.18 ms** | 3.73 → **0.49 ms** |
  | 2,000 posts | 10.99 → **0.18 ms** | 14.11 → **1.30 ms** |
  | 4,096 posts | 23.74 → **0.18 ms** | 29.39 → **2.46 ms** |

  A post with no replies costs the same at any board size; a thread costs ~5.6 µs per reply (one header read
  each, the verification). Under poll each of those milliseconds was every session's.
- A reply costs one more fsync (its record) and a directory fsync; the first `serve` of a store that predates
  the index reads every post once.

### Verification

- `cyrius test`: **239/239** + **7/7**, the same under `cyrius test --aarch64`. Fuzz plain and `--poison=ab`.
  `cyrius audit` **exit 0**. `scripts/check-version-sync.sh` and `scripts/check-toolchain.sh` OK.
- `docs/examples/run.sh`, both CI legs exactly as CI runs them, on 4 CPUs: **fork 25/25, poll 32/32** (33
  smokes; 20 ran against the sibling MUD).

### Known limitations (recorded, not fixed)

- A post added to a board by hand is not listed as a reply until `<board>/.replies/` is deleted and rebuilt
  (ADR 0027) — the same rule as the handle index (ADR 0026).
- The directory guard's `stat`-then-`open` window, until the stdlib's `dir_list_into` opens with `O_DIRECTORY`.

## [1.9.0] — 2026-10-13 (durable posts + store hardening)

The first release of the 1.9.x storage-and-scale line: the store stops trusting what its names turn out to
be, a post is finally either absent or whole, `login` no longer reads every account to say "unknown user",
and `.admins` is read to the end. Four roadmap rows, four sources: audit 1.8.1 I11, CLAUDE.md's "posts are
durable artifacts", audit 1.8.1 H1 / L4, audit 1.8.1 M4.

**244** tests (237 module + 7 serve-layer), also on aarch64 under qemu; fuzz plain and `--poison=ab`; **32**
example smokes (new: 32), both CI legs green; `cyrius audit` exit 0. `build/agora` **986,152 → 990,320 B**;
`--agnos` 982,664 → 986,832 B; `--aarch64` 2,415,456 → 2,415,528 B. Two new ADRs: [0025](docs/adr/0025-store-io-regular-files-and-publish.md)
(amends 0002) and [0026](docs/adr/0026-handle-index.md) (amends 0006).

### Security

- **The store refused nothing (audit 1.8.1 I11; MEDIUM — needs write access to the store).** Every store
  file was opened like any path, so:
  - a **FIFO** named `N.txt`, `.policy`, `.admins` or a lock file blocked its open, and under
    `AGORA_SERVE=poll` that was the whole server — the next `list` / `read` / `post` hung every session, and
    a new client was never greeted (under fork it hung a child for good);
  - a **symlink** was followed: `3.txt -> <any file the agora user can read>` was served to anonymous users
    as a post; registration's `O_TRUNC` writes emptied and refilled a planted link's target; a dangling
    link at a lock file made `O_CREAT` create its target.
  Now every store open goes through `store_open` (`src/arena.cyr`): `O_NOFOLLOW | O_NONBLOCK`, then an
  `fstat` that refuses anything but a regular file (`-EINVAL`). Reads use `store_read_all`, locks
  `store_lock_open`, the leaderboard `store_append_locked`; registration's three files are
  `store_write_atomic` writes (a rename replaces a planted link), and that function's own temp is unlinked
  and created `O_EXCL | O_NOFOLLOW`. agnos: `AO_NOFOLLOW` covers the link; it has no FIFOs, no
  `O_NONBLOCK` and no `fstat`. Directories above the final name are out of scope (ADR 0025).
  `docs/examples/32-store-hardening.py` drives both serve models; against a 1.8.2 build it fails 9 of 10
  checks — the symlinked file is served, and the poll server never answers again.

### Added

- **Crash-safe post writes** — the "posts are durable artifacts" principle is now backed. A post was
  created and written straight into `<id>.txt`, so a crash or power loss mid-write left a truncated post
  under its id. `store_publish` (ADR 0025) writes `<board>/.publish.tmp`, fsyncs it, and `link(2)`s it to
  `<id>.txt` — which, like `O_EXCL`, refuses an existing name, so the exclusive id claim of 1.6.4 (audit M4)
  stays — then fsyncs the directory. Crash debris at the temp name is removed by the next post (every
  writer holds the board lock); a filesystem without hard links falls back to `rename`, still under the lock.
- **The handle index** — `.users/.by-handle/<handle>` holds the owning fingerprint, and `.complete` marks it
  whole (ADR 0026). `login` read every user's `handle` file, and an unknown handle — the attacker's choice —
  always read all of them (audit 1.8.1 H1 / L4). Now an unknown handle is **one failed open**:
  `benches/serve-bench.py login`, fork mode, **0.16 ms per unknown login at 300 users and at 3,000 — was
  1.78 and 16.98 ms**. A claim is trusted only after the user it names is verified to hold the handle; a
  stale or broken one falls back to the scan. A store that predates the index gets it on its first `serve`
  (in a short-lived child) or `register`: ~50 ms at 300 users, ~300 ms at 3,000, once. Registration claims
  the new handle before writing and releases the old one after, so a crash leaves a detectable stale claim,
  never a missing one. Handles are validated before any path is built (the wire `login` passed raw bytes).
- **`.admins` is read to the end** — streamed in 4 KB windows instead of stopping at 4 KB (~120 handles);
  1.8.1 (audit S2 / M4) had made the cut fail closed, so later admins simply could not post. A line
  straddling a window is never matched by its cut-off prefix (`qixbert` is not `qix`, the S2 bug); a line
  longer than a window is skipped; past 1 MiB the rest is ignored, with a warning.
- `docs/examples/32-store-hardening.py` (above); `benches/serve-bench.py login` (unknown-login latency and
  first-start time vs registered users).
- Tests: `t233` store opens (symlink, FIFO, directory, dangling link, planted temp), `t234` registration
  replaces planted links, `t235` the crash-safe publish (debris, planted link, an existing id never
  replaced), `t236` the handle index (authoritative miss, fallback scan, re-registration, stale claims,
  invalid handles, the build matching the scan on a duplicate, a crashed build's empty claim), `t237`
  `serve`'s index preparation (a store with no users is left untouched — a starting server must not create
  the store — and one with users is indexed); `t227` rewritten for the streaming `.admins` reader. Every one
  mutation-checked: each guarded behaviour, broken, turns its test red — 18 mutants, none surviving, none
  hanging (the FIFO case holds both ends itself, so a regression fails instead of blocking).

### Changed

- `board_admins_whole` is removed — the streaming reader keeps whole lines by construction
  (`board_admins_lines`); `BOARD_ADMINS_MAX_BYTES` becomes `BOARD_ADMINS_CHUNK` + `BOARD_ADMINS_FILE_CAP`.
- Registration's `created.iso8601` uses the allocation-free `iso8601_into` (1.8.1 H1's formatter) instead
  of chrono's `iso8601_now`.
- `docs/examples/run.sh` waits for any process still serving `./bbs` before deleting it: a fork-mode
  connection child outlives its stopped server long enough to run its 1.8.1 close-path checkpoint, and a
  `jabberwacky.sav` landed after a clean, so the next run refused to start. Smoke 32 runs its servers in
  their own session and reaps the group, so an A/B against an old build does not leave a child blocked on
  the FIFO.
- ADRs 0002 and 0006 carry amendment notes pointing at 0025 / 0026; CLAUDE.md's "posts are durable
  artifacts" principle no longer carries its ⚠.

### Performance

- **The reply scan is ~8–9% slower** — one `fstat` per store open, and ADR 0005's scan opens every post on
  the board on every `read`: 3.38 → 3.71 ms at 500 posts, 13.1 → 14.2 ms at 2,000, 27.3 → 29.2 ms at
  4,096 (interleaved A/B, one machine, ~0.5 µs per post). `O_NONBLOCK` alone removes the hang; the check
  makes "regular files only" true. Roadmap § 1.9.1's reply index replaces the scan.
- Two fsyncs per post (the file and its board directory).
- Unchanged, measured: per-command heap growth under poll **0 KB** for 3,000 pipelined `login`s, 300
  `list`s and 2,000 `read`s on a 300-post, 300-user store (allocator gate); accept rates, poll session
  memory (12.6 KB), world-lock throughput (~520 txn/s); fork connection children measure the same as
  1.8.2 (building the index in the parent instead of a child would have added 4–12 KB to every one).
- **Benchmark method note**: fork-mode PSS per child depends on where the binary lives — the same build
  measures 54 KB run from tmpfs and 62 KB from ext4 (file-backed pages fault in differently). Compare
  builds from the same filesystem; BENCHMARKS.md now says so.

### Verification

- `cyrius test`: **237/237** + **7/7**, the same under `cyrius test --aarch64`. Fuzz 1/1 plain and
  `--poison=ab`. `cyrius audit` **exit 0**. `scripts/check-version-sync.sh` and
  `scripts/check-toolchain.sh` OK.
- `docs/examples/run.sh`, both CI legs exactly as CI runs them, on 4 CPUs: **fork 25/25, poll 31/31**
  (32 smokes; 20 ran against the sibling MUD). Final binary re-checked from a clean `build/` (02, 03, 11,
  13, 32 under both models).
- Dead-code audit: 11 agora functions are unreachable from `main` — all accessors only `tests/agora.tcyr`
  calls (`iabs`, `ipow`, `ol_compete_winner`, `pa_warp_count`, `paw_seed`, `telnet_linemode_mask`,
  `telnet_term_cols` / `_rows` / `_type` / `_type_len`, `th_registry_count`); none new. `board_admins_whole`
  removed.

### Known limitations (recorded, not fixed)

- Directory components above a store file are not checked (ADR 0025 § Decision): whoever can replace a
  board directory can rewrite the store.
- A user directory copied into `.users/` by hand is unknown to a complete handle index until
  `.users/.by-handle/` is deleted and rebuilt (ADR 0026).
- Registration writes its three files one by one: a crash between them leaves an account with an old
  handle or no `created.iso8601` — each file whole, the set not atomic.

## [1.8.2] — 2026-10-13 (tooling: the checklist runs itself, and the serve layer is measured)

The roadmap's two tooling slots — 1.8.2 *mechanical gates* and 1.8.3 *measure* — cut as one release. Every
step of the Closeout Pass that a person used to perform by hand now runs in CI, the serve layer in
`src/main.cyr` is unit-tested for the first time, and the serve-level numbers four ADRs were waiting on exist.
Two user-visible fixes rode along, each found by the new tooling: a ~40 ms Nagle stall on every multi-part
response under the default fork model (a new benchmark), and a fork child that a non-reading client held for
three send timeouts instead of one (a new smoke, on its first GitHub run).

**239** tests (232 module + 7 serve-layer), also on aarch64 under qemu; fuzz plain and `--poison=ab`;
**31/31** example smokes, **52/52 runs** under both serve models through the new runner; **`cyrius audit`
exits 0** for the first time. `build/agora` **986,144 → 986,152 B**; `--agnos` 982,656 → 982,664 B; `--aarch64`
2,415,440 → 2,415,456 B.

### Added

- **`docs/examples/run.sh` — the examples runner.** Each smoke gets a clean `./bbs` / `./keys`, a registered
  `qix` when it needs one, and — for the client-only scripts — the server it needs under the requested model;
  scripts that start their own server inherit `AGORA_SERVE`, so `--model fork|poll|both` covers them too.
  Every release from 1.6.7 to 1.8.1 was verified with a throwaway harness, and the README's "run them in
  order" contract never held. It refuses to start if `./bbs` or `./keys` already exist.
- **`tests/serve.tcyr` — `src/main.cyr`'s first unit tests.** `main.cyr` runs its entry point only when
  `AGORA_TEST` is undefined, so a test can include it. Seven tests over a real socketpair: the tx queue's
  drain-compact-overflow (1.8.1 M8), the per-sweep line budget (H2), compose lines not budgeted, the
  fork-mode sticky send failure (M10), door checkpoint-on-close plus the play lock (M1), the shutdown
  signalfd round trip (1.7.0 N1), and a short fork-mode write failing after one timeout (see Fixed). Each is mutation-checked (breaking the guarded behaviour turns it red).
  Also passes under qemu-aarch64.
- **`docs/examples/31-slow-reader.py`** — the slow-reader close path (1.6.3 / 1.7.0 / 1.8.1), a HIGH fix three
  times over, pinned at last: a client that asks for ~12 MB and reads nothing is disconnected — under poll at
  once, with a bystander's echo unaffected; under fork within one send timeout, watched from outside (the
  connection's child exiting) because reading the socket would un-stall the writer. A 1.8.0 build fails the
  fork half, and so did this release's own first cut (see Fixed). `--fast` skips it.
- **`benches/serve-bench.py`** — accept rate, per-session memory, world-lock contention and reply-scan latency,
  per serve model (BENCHMARKS.md § Serve-level baselines). Headlines: fork accepts ~4,100 connections/s
  sequentially, poll exactly 50 (one per 20 ms sweep — it sleeps rather than waiting for readiness); an idle
  session costs 12.6 KB under poll and ~62 KB as a fork child; the world lock is **fsync-bound, not
  contention-bound** (~520 txn/s flat from 1 to 8 writers, no lost update), so ADR 0010 / 0014's "measure
  before refining" gate stays closed; a `read`'s reply scan is linear at ~6.7 µs per post (27.7 ms at 4,096).
- **`scripts/check-version-sync.sh`** — VERSION against cyrius.cyml, the built binary, the CHANGELOG header,
  `state.md`'s Released row and the roadmap's release row (and, with `--tag`, the git tag); refuses a
  hard-coded version literal in `src/`. CI runs it on every push and the release workflow before publishing —
  the "post-hook" CLAUDE.md once promised, whose absence let 1.6.6 and 1.7.1 ship unrecorded.
- **`scripts/check-toolchain.sh`** — the pre-cut provenance gate: the local snapshot's SOURCE_COMMIT and
  every stdlib file against the cyrius tag, the vendored `lib/` against the snapshot, and the compiler the
  build actually runs — compared by resolved identity plus `cycc --version`, not by path: a fresh install
  where the pin is the active version (every CI runner) reaches the pinned `cycc` as `~/.cyrius/bin/cycc`,
  a symlink into `versions/<pin>/bin`, and a path match rejected it on the first GitHub run.
  Mutation-checked with a doctored snapshot, a substituted `cycc`, and a reproduction of the runner layout.
  (1.6.7 found a dirty snapshot inflating a measured binary by 215,520 B; the check was a manual `cmp`
  sweep until now.)

### Changed

- **The version string is generated.** `print_banner`, `cmd_version` and the MOTD read `CYRIUS_PKG_VERSION`,
  which `cyrius build` derives from cyrius.cyml's `version = "${file:VERSION}"`; VERSION is now the only file a
  release bumps (promised as a generated `version_str.cyr` since 0.2.0). Output is byte-identical.
- **`src/test.cyr` → `tests/agora.tcyr`**, and `cyrius.cyml` drops `[build] test`: a bare `cyrius test` runs
  every `tests/*.tcyr`. `cyrius audit` now finds and runs the tests (it reported `skip: no tests/ directory`).
- **`cyrius audit` passes** — 176 over-long lines wrapped and ~378 undocumented functions documented across
  `src/`, `tests/`, `fuzz/` and `benches/` (each function's comment written from its body). No behaviour change:
  every file was diffed comment- and whitespace-blind against its pre-edit copy; strings split for length are
  emitted by consecutive calls, and a scripted session, `help` and `--version` were A/B'd byte-identical. Two
  lines carry lint's per-line `#skip-lint`: the 2,660-byte word table in `decode_words.cyr` (a fixed-stride
  blob cannot be split) and Ashes' 158-byte help line (`ash_msg` overwrites, so it cannot be emitted in two).
  One test helper builds four 128-hex auth lines (`t_auth_line`), byte-compared with the literals it replaced.
- **CI** (`ci.yml`): least-privilege `permissions: contents: read`; actions pinned by commit SHA; the cyrius
  installer fetched from the tag matching the pin instead of `main`; new steps — toolchain provenance, version
  sync, fuzz `--poison=ab`, `cyrius audit`; a **smoke job per serve model** (logs uploaded on failure); an
  **aarch64 job** (build + both suites under qemu-user). **Release** (`release.yml`): gates on all of CI, runs
  the version sync with `--tag`, and publishes x86_64 Linux, aarch64 Linux and x86_64 AGNOS binaries with
  `SHA256SUMS` (it published only x86_64, unsigned and unsummed).
- CLAUDE.md: Quick Start, Closeout Pass steps 1/2/7/11/12 and § CI / Release rewritten around the new tools.
- ADRs 0005, 0010, 0014, 0023 record the measurements; roadmap re-scoped (1.8.2 + 1.8.3 shipped as 1.8.2;
  the 1.9.1 reply-index and 1.11.0 epoll rows carry their numbers).

### Fixed

- **A ~40 ms stall on every multi-part response in the default (fork) serve model** — found by the reply-scan
  bench, which read a flat ~41 ms per `read` at every board size. A fork worker writes a reply as several small
  sends, and Nagle held each one after the first until the client's delayed (~40 ms) ACK; with the client
  acknowledging immediately the same read took 2.6 ms. Accepted sockets now get `TCP_NODELAY` (both models; a
  no-op decline on agnos): `read` on 500 posts **41.0 → 3.4 ms**, fork accept rate 3,771 → 4,077 conn/s.
- **A fork child outlived a non-reading client by two extra send timeouts** — 186 s, not the 60 s the
  1.8.1 sticky-send fix (M10) meant. `send_buf` treated a SHORT write as success and retried the rest; on a
  blocking socket a short write means `SO_SNDTIMEO` expired after copying part of the buffer, so the latch
  fired only on a write that gained no bytes at all. A zero-window TCP peer does not guarantee that: on a
  probe's ACK Linux still took 2 KB more into a 2.86 MB send queue while the client had acknowledged 4,521 B,
  and that "progress" bought the writer another 60 s (deterministic: 6/6 trials, 186.0 s, Linux 7.2). A short
  write now fails and latches like a failed one — the rule `send_buf`'s header comment always stated. The
  bound is per write, not per post: a slow reader that keeps freeing room is not dropped (one that leaves
  the kernel no room for 60 s was already dropped by the zero-byte case). Found by smoke 31 on the first
  GitHub run of the new smoke job; pinned by `s07`, which fails on the old retry loop.
- `docs/examples/run.sh` waits for the smoke port to be free before starting a server: a self-starting smoke
  still tearing down its own server on 2323 made a failed bind look like a started server (found on its own
  first full run).

### Verification

- `cyrius test`: **232/232** (tests/agora.tcyr) + **7/7** (tests/serve.tcyr), the same under
  `cyrius test --aarch64` (qemu). Fuzz 1/1 plain, `--poison`, `--poison=ab`. `cyrius audit` **exit 0** (fmt,
  lint, docs, tests, bench). `scripts/check-version-sync.sh` and `scripts/check-toolchain.sh` OK.
- `docs/examples/run.sh`: **52 passed, 0 failed, 0 skipped** (31 smokes; 20 ran against the sibling MUD), on
  the build before the `TCP_NODELAY` change; after it, the connection-heavy subset (04, 05, 07, 11, 15, 20,
  23–28, 30, 31) re-run under both models.
- The new workflows' first GitHub run (the untagged `2c543ea` push): the aarch64 job and the fork smoke leg
  passed; the toolchain-provenance step and the poll smoke leg failed, both fixed above (the provenance
  check's path match; smoke 31 finding the short-write retry). Both legs then re-run locally exactly as CI
  runs them, on 4 CPUs: **fork 25/25, poll 30/30**. The build-and-test steps after provenance (build, version
  sync, tests, fuzz, audit) were skipped on that run and have passed only locally so far.

### Known limitations (recorded, not fixed)

- Poll-mode latency floor of 0–20 ms per command and 50 sequential accepts/s — the sweep sleeps rather than
  waiting for readiness (roadmap § 1.11.0).
- aarch64 runs under qemu-user only; still nothing on aarch64 hardware. The wire smokes do not run under qemu.
- Under fork, "slow" and "stalled" are told apart by whether the KERNEL frees send-buffer room within 60 s,
  not by whether the client acknowledged anything. The exact test needs the socket's unacknowledged-byte
  count (`SIOCOUTQ` / `TCP_INFO`), which `lib/net.cyr` does not expose and agora does not call raw — roadmap
  § Unscheduled.

## [1.8.1] — 2026-10-12 (code audit + repair: one client can no longer starve or exhaust the server)

A full-tree audit of 1.8.0 in six parallel slices — the wire; storage and identity; serve loops and
memory; the door framework and trade doors; the RPG/war doors, chat, chatbots and the Descent link; the
closeout gates and doc-vs-code truth — with every finding re-verified, fixed one at a time, and A/B'd
against a `git archive` build of 1.8.0 using the auditors' own repros. **3 HIGH, 12 MEDIUM, 26 LOW fixed;
14 INFO recorded, the open ones scheduled in the roadmap.** No CRITICAL. No new features. Full report:
[`docs/audit/2026-10-12-audit-1.8.1.md`](docs/audit/2026-10-12-audit-1.8.1.md).

**232/232** tests (+7: t226–t232), also **232/232 on aarch64** under qemu; fuzz green plain, `--poison` and
`--poison=ab`; **30/30** example smokes, 34 runs (new: `30-audit-1.8.1.py`, which fails all 11 of its
checks against 1.8.0). `build/agora` **968,720 → 986,144 B** (+17,424); `--agnos` 965,280 → 982,656 B;
`--aarch64` 2,348,864 → 2,415,440 B. Toolchain unchanged (cyrius 6.7.9, darshana 1.3.0).

### Security

The headline numbers, 1.8.0 → 1.8.1, poll model (the only one on agnos):

| Attack (anonymous unless noted) | 1.8.0 | 1.8.1 |
|---|---:|---:|
| bystander echo latency, 16 clients pipelining `read 1` | 13,701 ms | **22 ms** |
| … pipelining `list` / `login x` | 1,077 / 200 ms | **23 / 19 ms** |
| heap per `login nobody` / per `login` + `auth:` | 223 / 287 B | **0 / 0 B** |
| heap per `list` or `read`, ~1,500-post board | ~400 KB (masked by a dropped session) | **0 B** |
| heap per Handler decrypt / per `descent` (logged in) | 737 / 647 B | **0 / 0 B** |
| fork children from 200 idle connections | 200 | **64** |

- **HIGH — vendored allocations on per-line paths leaked without login** (audit H1). `dir_list`,
  `str_from`, sigil's `hex_decode` and chrono's `iso8601_now` allocate on the bump heap, which the
  per-command arena never reclaims; `login x`, `list`, `read`, `boards` and `enter` reached them with no
  login, pipelinable: +2.5 MB/s from one connection on an empty store, +15 MB/s with 301 users. **Fixed**:
  every listing goes through `dir_list_into` into one process-lifetime workspace that grows only by
  doubling (`store_dir_scan`); `Str` headers in the arena; `hex_decode_into`; an allocation-free
  `iso8601_into` (byte-identical to chrono's, t229).
- **HIGH — one client could stall every session** (H2). Every line of a 4 KB recv ran before the sweep
  moved on, and each `read` re-read up to 66 KB of every post. **Fixed**: a per-sweep line budget
  (`POLL_LINE_BUDGET` = 1) with the remainder parked in the slot; the sweep skips its sleep while anything
  is parked, so a lone client keeps full speed; compose lines don't count; `replies_to` reads a 2 KB
  header scan.
- **HIGH — per-post arena allocations spilled the arena** (H3, found re-measuring H1). `post_read`,
  `post_from` and `account_lookup_handle` took `cmd_alloc` memory on every call inside per-post /
  per-user loops; past 512 KB every allocation falls back to a bare, leaking `alloc()`. **Fixed**: stack
  buffers; t232 pins all three (mutation-checked).
- **MEDIUM — door saves** (M1): a dropped connection saved nothing while the shared world saved every
  line — garrisons duplicated (29 → 145, ship unchanged), lost bets erased (Port Authority 2,000 →
  893,641 credits), finished runs replayed to the leaderboard forever. **Fixed**: every close path
  checkpoints like `q`; a finished run removes its save; a save that loads already over starts fresh; a
  per-identity play lock (`<game>.lock`) refuses a second session on the same save.
- **MEDIUM — damaged saves / snapshots wrote out of bounds** (M2): unchecked `PA_SECTOR`, `PA_PLANET`,
  `TH_MOLEIDX`, `AG_CITY`, cable indexes, Decode `MAXTRIES`, Ashes `norders`. **Fixed** in the loaders
  and in the shared-world accessors (t230).
- **MEDIUM — `.policy` failed open; `.admins` past 4 KB matched a cut-off prefix** (M3, M4). An
  unrecognised or unreadable policy now means admin-only (with a warning); only whole `.admins` lines
  count (t226, t227).
- **MEDIUM** — Handler decrypt leaked a Decode state per attempt (M5); `descent` leaked bare heap per call
  (M6); a poll player was reaped on returning from any MUD visit over 60 s (M7); any poll command printing
  > 128 KB dropped the session — a busy board could not be listed (M8); fork mode had no connection cap and
  an IAC NOP held a child forever (M9); a non-reading client pinned a fork child for hours (M10); one NUL
  byte bypassed 1.6.4's idle reap (M11); and on agnos the stdlib's 6.6.7 send-retry loop silently undid the
  one-send-per-drain bound (M12) — all fixed.
- **LOW** (26, detail in the audit): wire login now requires `public_key.bin` to hash to its fingerprint
  (L1 — a store-writer could log in as another user); short post writes are cleaned up (L2); board names
  off the disk are bounded (L3); `register` is serialized (L4 — 30/30 → 0/30 duplicate handles); `list`
  keeps the newest 4,096 posts, sorted (L5); bodies over 64 KB are refused, not truncated (L6); `serve
  --store` with no value no longer spins (L7); leaderboards no longer freeze after 256 finishes (L8); an
  unreadable world is not re-minted (L9); failed world writes are reported (L10); the Handler save honours
  its cap (L11); the decrypt lever stops calling innocent agents' errors "a plant" (L12, 875 → 0); Descent
  visit boundaries (L13, L14, L16, L22); Ashes order-queue griefing (L15); chat transcript render bound
  (L17); greet arena reset (L18); SIGTERM honoured during a Descent visit (L19, mitigated); subnegotiation
  only for agreed options (L20); id digit cap (L21); leaderboard score parse (L23); tick-length guard
  (L24); fsync checked (L25); handle re-validation, policy re-check at commit, CLI reply parent (L26).

### Changed

- **Behaviour an operator or player can see**: `.policy` files that are not exactly `open` / `known` /
  `admin` (after a `#` comment) make a board admin-only; a second session playing the same saved game is
  refused; a dropped connection keeps door progress (and losses); a finished run starts fresh next time;
  `boards` lists only directories with valid board names; a board over 4,096 posts lists its newest 4,096;
  under fork, a 65th simultaneous connection gets "server full"; returning from the Descent re-sends the
  telnet option salvo.
- `sort_i64_asc` is a heapsort (O(n log n)); `post_list` sorts the whole board.
- CLAUDE.md's allocator gate: the `descent_proxy` exception is retired, and a new rule records that **the
  arena is a budget, not a free list** — no per-iteration `cmd_alloc` in loops; prove boundedness by a
  poll-mode heap A/B, not by reading `src/`.
- ADRs 0005, 0006, 0009, 0010, 0013, 0017, 0021, 0022 and 0023 amended where 1.8.1 changed or falsified a
  statement (ADR 0006's "a store compromise cannot impersonate" was false until L1).
- CI: the installer step runs with `pipefail` (a failed `curl | sh` went green); the version-drift check
  covers all three literals; a stale comment corrected. `benches/bench_telnet.bcyr`'s NAWS bench marks
  the option agreed, so it still times the decode path (L20 would otherwise make it time a rejection).
- Roadmap rebuilt around release slots (1.8.x → 1.12.x); `state.md` rewritten as a snapshot (it had grown
  to 168 KB of superseded slot notes); `roadmap-future.md` trimmed of shipped door / chatbot work.

### Added

- `docs/examples/30-audit-1.8.1.py`; tests t226–t232; the fuzz harness's Q-state invariant now checks
  something (I2 — it range-checked an already-masked byte; mutation-proven).

### Verification

- Tests **232/232** (x86_64) and **232/232** via `cyrius test --aarch64` under qemu. Fuzz 1/1, also under
  `--poison` and `--poison=ab`. Example smokes **30/30**, 34 runs (04/05/23/25 under both serve models) via
  a throwaway harness. Full clean build (`rm -rf build lib cyrius.lock && cyrius deps && CYRIUS_DCE=1
  cyrius build`; the regenerated `lib/` is byte-identical). `cyrius capacity --check` ok. `cyrius lint`
  tree-wide: **176 warnings** (178 at 1.8.0; all line length) / **0 untracked deferrals**; `cyrfmt --check`
  clean. **`cyrius audit` exits 1** — as it did at 1.8.0, unrecorded: 176 lint warnings and 358
  undocumented public functions (roadmap 1.8.2).
- Benchmarks, six runs each, A/B'd same-day against the 1.8.0 tree: `plain_byte` 8–9 / 8–9 ns,
  `iac_untracked` 60–62 / 61, `iac_tracked_agree` 70–74 / 71–72, `announce_salvo` 126–127 / 126–127 —
  unchanged. `subneg_naws` 102–103 vs 94–95: the bench now also marks NAWS agreed each iteration, and the
  RFC 855 gate (L20) adds a load + compare; it runs once or twice per connection. See
  [`BENCHMARKS.md`](BENCHMARKS.md).
- Slow-reader defense re-checked under poll: a client that stops reading is still closed (now once the
  kernel's buffers are full — 1.8 MB handed over — rather than at 128 KB of queued output), and a
  bystander stays responsive meanwhile.

### Known limitations (recorded, not fixed)

- The Descent proxy still holds the poll sweep for a whole MUD visit; a blackholed endpoint costs up to
  4 s per connect, at most once per 30 s (roadmap 1.11.0).
- Store opens follow symlinks and block on FIFOs (needs store write access; roadmap 1.9.0). A crash —
  not a short write — mid-post still leaves a truncated post (roadmap 1.9.0).
- agnos' stdlib socket table holds 8 sockets, so the real session ceiling there is ~8 (ADR 0023 note).
- The agnos fixes (M12, the signalfd watch in L19) are verified by reading the vendored stdlib and by the
  `--agnos` build; nothing ran under mirshi this cut.

## [1.8.0] — 2026-10-12 (toolchain 6.7.9 + darshana 1.3.0: other people's text stops driving your terminal)

cyrius **6.6.2 → 6.7.9** and darshana **0.9.0 → 1.3.0** — the last consumer off a pre-freeze darshana, onto
its frozen v1 API. The two pins had to move together: darshana 1.3.0's bundle declares private constants
with `const`, which cyrius gained in 6.7.2. The payload is a **security fix** the darshana bump made cheap:
stored text — every post body, subject, author handle, board name and leaderboard row — now leaves the
server through darshana's `tty_sanitize_buf`, so a terminal control sequence written by one user can no
longer execute in another user's (or the operator's) terminal ([ADR 0024](docs/adr/0024-egress-text-sanitization.md),
[audit 2026-10-12](docs/audit/2026-10-12-audit.md)). Everything else a user sees is byte-identical.

**225/225** tests (+4), also **225/225 on aarch64** under qemu; fuzz green, including `--poison` and
`--poison=ab`; **29/29** example smokes (new: `29-egress-sanitize.py`; 04/05/23 run under both serve
models, 32 runs). `build/agora` **968,880 → 968,720 B** (1.7.1 on 6.6.2 → 1.8.0 on 6.7.9, both
`CYRIUS_DCE=1`); `--agnos` **965,280 B**; `--aarch64` **2,348,864 B**.

### Security

- **Stored text carried live terminal control sequences to every reader** (audit **M1**, MEDIUM).
  agora filtered ingress only, per byte, and `send_text` only doubled IAC. Two classes got through:
  **C1 controls** — `input_byte_ok` passes 0x80–0xFE so UTF-8 can be posted, which also passes the raw
  8-bit CSI/OSC/ST (`9B` / `9D` / `9C`) and their UTF-8 encodings (`C2 9B` = U+009B, a CSI to any terminal
  that honours C1) in bodies and subjects; and **anything the CLI stored** — `agora post` writes its stdin body
  with no filter at all, ESC included (the `input_byte_ok` comment claimed otherwise), as do pre-filter
  posts and hand-edited files. `agora read` / `agora list` printed it all raw into the operator's
  terminal. **Repro**: `AGORA_BIN=<1.7.1 build> docs/examples/29-egress-sanitize.py` — an anonymous
  reader receives `Subject: subj \xc2\x9b31m red`, `c1 csi: \xc2\x9b2J` (clear screen),
  `osc52: \xc2\x9d52;c;…\xc2\x9c` (clipboard write) and, from a CLI post, `cli \x1b[2Jesc\x07bel`;
  **44 failed checks** under both serve models and the CLI. **Fixed**: `send_text` (every wire egress of
  stored text) and its new stdout twin `write_text` run each chunk through `text_sanitize` —
  `tty_sanitize_buf` in **UTF-8 mode, keeping TAB / CR / LF** — before the IAC pass. Every control byte
  or sequence becomes one `?`; well-formed UTF-8 passes byte-for-byte; the post on disk is not rewritten.
  UTF-8 rather than Latin-1 because an agora session is UTF-8 by construction (no CHARSET negotiation;
  agora's own MOTD and help are UTF-8) — the reasoning and the Latin-1-terminal limit are in ADR 0024.
- **Leaderboard rows were copied into a 320-byte buffer with no bound** (audit **L1**, LOW) —
  `door_render_leaderboard`. agora's own rows are ~50 bytes, but a damaged or hand-edited leaderboard
  with a long line overran the arena allocation on `scores`, which needs no login. Clamped to
  `LB_ROW_CAP`; the row now also leaves through `send_text`.
- **`boards` sent directory names read off the disk raw** (audit **L2**, LOW). `boards_list` keeps any
  non-dot directory, and only names made through `enter` are known valid; they now go through
  `send_text`. Closes the roadmap row of the same name.

### Changed

- **Toolchain `6.6.2` → `6.7.9`** (`cyrius.cyml`; `build -v` reports
  `~/.cyrius/versions/6.7.9/bin/cycc`; the local snapshot's 113 stdlib files were checked byte-identical
  to `git show 6.7.9:lib/…` and its `SOURCE_COMMIT` matches the tag). `lib/` re-vendored from scratch
  (`rm -rf lib cyrius.lock && cyrius deps`): 53 → 56 files (`alloc_cx`, `poison`, `sys` added by the
  snapshot's own include graph). **No source change was needed to compile** — agora uses none of the
  6.7 reserved words (`const`, `true`, `false`, `do`, `dyn`, `trait`), has no lone `!`, no compound
  assignment, no `~` / unary `-` on a constant and no typed narrow pointer, all checked by grep with
  strings and comments stripped. What the move did surface, all fixed: **cyrlint's stricter deferral
  check** now flags four comments the 6.6.2 checker passed (`board.cyr:72`, `descent.cyr:15`,
  `bench_telnet.bcyr:50-51`) — two real deferrals given a same-line roadmap citation, two false
  positives ("follow-up subneg") reworded — so the tree-wide count stays **0 untracked**; and one
  6.6.2 `note:` became a located `warning:` in vendored sigil (see Known limitations). Other named
  deps: none moved.
- **darshana `0.9.0` → `1.3.0`** — no API change for agora (the freeze guarantees it), and the SGR bytes
  are unchanged: a scripted session (IAC salvo, MOTD, `help`, `boards`, `list`, a `play decode` frame,
  `quit`) is **byte-identical, 3,750 B, under both serve models**, between the released 1.7.1 build and
  this tree before the version bump. In passing it removes 0.9.0's `var SYS_IOCTL = 16`, which shadowed
  the stdlib's arch-aware constant program-wide (every `--aarch64` agora build warned
  `duplicate symbol 'SYS_IOCTL'`; latent, since nothing agora reaches issues an ioctl, but 16 is
  `fremovexattr` on aarch64). The `[deps.darshana]` comment is rewritten: it described the 0.9.0 pin
  and a surface agora no longer has.
- **`emit_sgr` (door.cyr) encodes through `tty_sgr_buf`**, keeping agora's own [D3] capacity gate —
  darshana's composers take no capacity argument, so the escape is composed into a stack scratch and
  copied only if it fits, the same shape as `emit_int`. **Byte-identical for every code 0..999** (t222
  compares against the 1.7.x encoder). Two deliberate differences, neither reachable from a call site
  today: an out-of-range code is dropped instead of formatted (`ESC[-5m`, or a digit-less `ESC[m` for a
  huge value), and the cap check is exact instead of a 16-byte over-estimate.
- **`render_motd` uses `TTY_FG_CYAN` / `TTY_FG_YELLOW`** (same values, same bytes), and its chain is now
  **-1-safe**: `motd_emit_cstr` passes a negative `pos` through without writing, as darshana's composers
  do since 0.9.3, so a -1 anywhere yields an empty MOTD rather than a write below the buffer. The audit
  result for the 0.9.3 `-1` (the roadmap row's open question): **no agora call site can produce one** —
  `pos` starts at 2 and only grows, the codes are in-range constants, and `emit_sgr` checks its return.
- **The shutdown signalfd stays hand-rolled — re-checked, not adopted.** darshana's AGNOS
  `tty_open_signalfd` blocks the signals first, and under mirshi a blocked signal is never delivered
  through a signalfd (darshana's own docstring; filed with mirshi), so adopting it would arm a shutdown
  that cannot fire on the target that always polls. `TTY_SIGMASK_EXIT` also adds SIGHUP. The roadmap
  row's premise ("agora calls `tty_open_signalfd`") was wrong — it never did — and agora's arm already
  had both fixes darshana 0.9.3 shipped (unblock on failure; exactly -1). **Child signal-block check**:
  every fork child calls `shutdown_signals_child_reset` first (closes the inherited signalfd, unblocks
  INT|TERM); agora has no exec / spawn anywhere; smoke 28 on 1.8.0 reads the child's
  `SigBlk: 0000000000000000` and kills it with SIGTERM. Recorded in the N1 comment block.
- `src/test.cyr` includes `lib/darshana.cyr` explicitly, as `main.cyr` does (the manifest already
  prepended it). `door.cyr`'s header claimed the unit harness "does not include darshana" — false.
- **CLAUDE.md**: the Closeout Pass said a bare `cyrius test` exits 1; since cyrius 6.6.17 it runs the
  `[build] test` entry (verified, exit 0). The explicit `src/test.cyr` path stays canonical.

### Added

- `text_sanitize`, `text_sanitize_keep`, `text_chunk_end`, `text_iac_double` (board.cyr) — the pure
  egress rule, unit-testable; `write_text` (main.cyr) for the CLI viewers.
- **Tests t222–t225** (221 → **225**): `emit_sgr` vs the 1.7.x encoder over 0..999 + drop + exact cap;
  the sanitize rule case by case; chunked sanitizing byte-identical to one-shot for every cap 4–12 and
  504 over a corpus and 4 KB of pseudo-random bytes; the IAC pass. Mutation-checked: removing the UTF-8
  boundary rule, dropping CR from the keep set, Latin-1 mode, or the old 16-byte cap each turns the suite
  red.
- **`docs/examples/29-egress-sanitize.py`** — self-contained, both serve models plus the CLI; asserts
  the stored artifact is untouched. `AGORA_BIN=` A/Bs an older build.
- [ADR 0024](docs/adr/0024-egress-text-sanitization.md); [docs/audit/2026-10-12-audit.md](docs/audit/2026-10-12-audit.md)
  (1 MEDIUM, 2 LOW, 4 INFO — closed).

### Behaviour changes (bytes a user sees)

- Stored text with a control byte, a C1 control (raw or UTF-8-encoded) or malformed UTF-8 shows `?` in
  its place — over the wire and in `agora read` / `agora list`. Clean text, including all well-formed
  UTF-8, TAB and CR LF, is unchanged.
- **A stored 0xFF now arrives as `?`, not `IAC IAC`.** It is never valid UTF-8, so the sanitizer
  neutralizes it before the IAC pass sees it. Smoke 26 was **updated** to pin this: it planted
  `FF FA 18` (IAC SB TERMINAL-TYPE, no SE) and asserted `FF FF` on the wire; it now asserts no 0xFF at
  all and `???`. The doubling is still in `send_text` as defence in depth (t225).

### Fixed

- `src/test.cyr`'s output had three wrong literal lengths: the header dropped its newline (52 of 53
  bytes), both rules wrote their trailing NUL (56 of 55 — the stray byte before `PASS: t01…` and
  ` tests:`), and `test_fail`'s ` — ` lost its trailing space (4 of 5).

### Verification

- Tests **225/225** (x86_64) and **225/225** via `cyrius test --aarch64` under qemu-aarch64; smoke 29
  also passes against the `--aarch64` binary under qemu-user (both serve models + CLI) — the first wire
  smoke ever run on an aarch64 agora. `cyrius fuzz fuzz/telnet_iac.fcyr` **1 passed / 0 failed**, and the same
  under `--poison` and `--poison=ab` — the N4 re-evaluation moved here from cyrius's roadmap (applicable
  since 6.6.18; CI unchanged).
- Example smokes **29/29** (32 runs) via a throwaway harness, with smoke 26 re-run in full after its
  update. Version-drift check green. Full clean build (`rm -rf build lib cyrius.lock && cyrius deps &&
  CYRIUS_DCE=1 cyrius build`). `cyrius capacity --check` ok (all caps under 85%).
- `cyrius lint`, every `src/*.cyr` + fuzz + bench: **178 warnings / 0 untracked deferrals** — the same
  178 the HEAD tree gets under the 6.7.9 linter (all `line exceeds 120` plus one double blank line);
  `cyrfmt --check` clean.
- Benchmarks re-run six times and A/B'd against the 1.7.1 tree on 6.6.2 the same day — within noise of
  each other; see [`BENCHMARKS.md`](BENCHMARKS.md), which also records an unattributed ~5–15% gap to
  the August 1.7.0 row.

### Known limitations (recorded, not fixed)

- **cyrius 6.7.x warns on vendored sigil**: `lib/sigil.cyr:28103:12: array local over the per-fn frame
  budget gets STATIC storage` — `hash_file_into`'s deliberately static, per-thread-banked 256 KB buffer.
  agora never calls it and must not edit `lib/`; every sigil consumer sees it. Flagged to the owner as
  a cyrius/sigil item.
- `warning: large static data` (≈375 KB) is unchanged in kind from 6.6.2 (374,576 → 375,552 B).
- The test build's `warning: undefined function 'send_str'` is agora's own and pre-existing:
  `src/test.cyr` compiles `descent.cyr` without `main.cyr` (roadmap § Backlog, the `tests/` split).
- A **Latin-1 / 8-bit-C1 terminal** is not fully protected — a well-formed UTF-8 character can contain
  a byte such a terminal reads as C1 (ADR 0024 § Consequences). It already misrenders agora's own output.

## [1.7.1] - 2026-09-11

### Changed

- **Toolchain `6.5.34` → `6.6.2`.** Migrated to the `Result` value form:
  2 first-party file(s) changed. Every surface re-verified — build, tests, and any
  bench/fuzz/distlib target the repo ships.


## [1.7.0] — 2026-08-22 (roadmap § Now closes: the server can finally stop)

**All four pinned roadmap items — N1, N2, N3, N4 — are done**, plus cyrius **6.5.33 → 6.5.34**.
`docs/development/roadmap.md` § Now is empty for the first time since it was rebuilt. 221/221 tests,
both targets build, **28/28** example smokes green (new: `28-clean-shutdown.py`), and the IAC parser
now has a fuzz harness that is mutation-proven on two axes.

**2,010,320 → 2,230,240 B**; `--agnos` **2,209,976 B**. **+219,920 B, and ~215,520 B of that is not
agora**: 6.5.34 folds **bayan 1.4.2 → 1.5.2**, which carries two heap buffer overflows in `csv`
(CWE-787), a one-byte remote crash in `base64`, an unchecked allocation in `yaml`, an out-of-bounds
read in `cyml`, a remote memory-exhaustion DoS in `json`, dropped carries in `u256_mul`, and a
`bayan_u64_mulmod` that took **SIGFPE on ordinary inputs**. agora reaches only `u256_from_hex` (via
sigil's `ed25519_init`), but the growth is the price of a dependency that is now correct — and it is
exactly the 215,520 B that 1.6.7 removed by pinning the *released* bayan instead of the unreleased one
that had been sitting in the local snapshot. The remaining ~4.4 KB is N1–N4.

### Added

- **N1 — clean shutdown on SIGINT / SIGTERM, both serve models.** Until now **neither loop could
  exit**: both declared `var stop = 0;` and looped `while (stop == 0)` with **nothing anywhere
  assigning `stop`**. agora could only be killed — the poll model never drained its 64 slots, the fork
  model never reaped. The mechanism is a **signalfd**, not a handler: a handler would need the
  `rt_sigaction` `sa_restorer` trampoline that [ADR 0007](docs/adr/0007-fork-per-connection.md)
  rejected, and would drag in async-signal-safety; an fd is the shape both loops already consume.
  Poll tests it once per sweep; the fork parent, whose `accept` blocks, waits on `poll(2)` over
  `{listener, signalfd}` — descent's established pollfd idiom, and safe unguarded here because fork
  mode is Linux-only by construction. On shutdown poll notifies and drains every live session, and the
  fork parent closes the listener then reaps children for a bounded 5 s grace before exiting anyway
  (unbounded would let one player in a door game hold the operator's shutdown open forever).
- **N4 — `fuzz/telnet_iac.fcyr`, and a fuzz step in both CI and release.** CLAUDE.md § Key Principles
  has demanded *"fuzz every parser path — IAC sequences are adversarial-by-default"* since **0.2.0**
  with no harness behind it; the 2026-07-26 audit said so under *"What this audit did not cover"*.
  The harness drives ~1.2M bytes through `telnet_feed` / `telnet_handle_sb` across five passes —
  uniform random, IAC-dense, well-formed subnegotiations with payloads spanning past `SB_BUF_CAP`,
  hand-picked adversarial frames, and a state-reset check — asserting **its own invariants** with a
  distinct exit code per violation. That matters: random bytes into a bounds-checked machine will not
  crash on their own, and `cyrius fuzz --poison` cannot help because it instruments `fl_alloc`/`fl_free`
  while the parser is entirely bump-allocated. **Mutation-proven on two independent axes**: deleting
  the `TERM_TYPE_CAP` clamp (the CVE-2020-10188 shape) or the subneg accumulator bound each turns it
  RED. The PRNG seed is fixed so a CI failure reproduces locally byte for byte.
- **`docs/examples/28-clean-shutdown.py`** — 9 checks, self-contained, itself mutation-proven.

### Fixed

- **N2 — crash-safe durable writes.** Three sites moved off `file_write_all`, whose `O_TRUNC` empties
  the target *at open*: `door_save_write` (a player's save), `world_write` (the shared world — the
  highest-value of the three, since one crash loses it for every player at once) and `chat_log_write`
  (rewritten on **every** `say`, so the most frequently executed). `file_write_atomic` writes a temp,
  fsyncs, and renames.
  - ⚠ **The return convention differs and does so silently** — `file_write_all` returns the byte
    count, `file_write_atomic` returns **0**. All three guards were `n != len`; keeping them would
    have treated every successful write as a failure.
  - ⚠ **Safe only because the locks are on different files.** A rename replaces the inode, and flock
    binds to an inode, not a path. Had the world lock been held on `snapshot` itself this would have
    silently destroyed [ADR 0010](docs/adr/0010-persistent-universe.md)'s no-lost-updates guarantee
    with nothing failing visibly. Verified: `world_lock_acquire` locks `<world>/.lock` and
    `chat_lock_acquire` locks `<channel>/.lock`. **Proven, not assumed** — smoke 08 runs 8 concurrent
    processes × 300 transactions and still lands exactly 2400.
  - ⚠ **The obvious implementation reopened the leak class two previous cuts closed, so agora writes
    its own.** Calling the stdlib's `file_write_atomic` directly would have been a one-word change —
    and it builds its temp name with a bare `alloc()` (`_io_tmp_name`) that is never freed.
    **Measured: 64 B of permanent bump heap per call** on a 14-byte path (`file_write_all` costs 0),
    so ~96-112 B on agora's real store paths. Two of the three sites fire **per dispatched line** —
    `chat_log_write` on every `say`, `world_write` on every universe-door line via
    `door_world_commit` — and under `AGORA_SERVE=poll` one process serves for the life of the server,
    so that is linear permanent growth on the hottest path in the chat subsystem: precisely what
    [ADR 0021](docs/adr/0021-per-command-scratch-arena.md) and
    [ADR 0022](docs/adr/0022-door-state-free-hook.md) each spent a whole cut eliminating. The arena
    cannot reclaim it because the allocation is inside a vendored lib — which is also why CLAUDE.md's
    *"no bare `alloc()` reachable from `process_rx`"* closeout gate cannot see it: that gate greps
    agora's own source. **`store_write_atomic` (`src/arena.cyr`)** performs the identical I/O sequence
    with the temp name taken from `cmd_alloc`. Re-measured after the change: **0 B per call.**

    This was **not** caught by review. It was caught by the post-cut doc sweep reading the ADRs the
    change was supposed to respect, which is an argument for running that sweep before calling a cut
    done rather than after.
- **N3 — both poll-mode holes.**
  - **Hole B, the silent drop.** `sess_tx_enqueue`'s over-cap arm returned 1 *without copying*, and
    **158 of 159 send sites discard that return** (the sole exception being the 1.6.3 telnet-tx
    drain). So the "slow-reader defense" its own comment advertised did not exist: an over-cap session
    lost bytes silently and stayed open holding one of 64 slots, mute forever. The refusal is now
    recorded on the session and consumed by `session_drain`, whose negative return **both serve models
    already close on** — so no call site changed, and no future send site can forget to check.
    `send_buf` is the single choke point that makes this possible.
  - **Hole A, the false doc comment.** `session_drain` claimed *"sys_write is non-blocking on both
    platforms (agnos socket / Linux O_NONBLOCK)"*. Linux is true. **agnos is not**:
    `sock_set_nonblocking` is a literal `return 0;` there, and `sys_write` on a tagged socket fd routes
    to `SYS_SOCK_SEND = 48`, whose own table entry says `BLOCKS`. So on **the only target that always
    polls**, one slow reader stalled the shared sweep for all 64 sessions, and the `EWOULDBLOCK` arm
    was unreachable. There is **no non-blocking send on agnos to switch to** — no `MSG_DONTWAIT`, no
    flags argument, no peer to `sock_recv`'s would-block return — so this **bounds** the exposure
    rather than pretending to remove it: one send attempt per drain, remainder to the next sweep via
    the partial path that already existed. A mitigation, recorded as one; the real fix is kernel-side.

### Security

- **Fork children were about to become unkillable, and the fix is in the same cut as the cause.**
  `fork(2)` inherits the thread's signal mask, so arming N1 in the parent silently gave every
  connection child a blocked SIGINT+SIGTERM with no signalfd being read. Measured during development:
  a child's `/proc/<pid>/status` read `SigBlk: 0000000000004002` — exactly agora's mask — and it
  survived SIGTERM. Children serve untrusted clients and are precisely the processes an operator most
  needs to kill. `shutdown_signals_child_reset` unblocks and closes the inherited fd first thing in the
  child branch; smoke 28 asserts both the mask and the kill, and is mutation-proven against it.
- **A half-armed state could have made the whole server unkillable.** If `signalfd` failed *after*
  `sigprocmask` succeeded, SIGINT and SIGTERM stayed blocked with nothing draining them — strictly
  worse than the pre-1.7.0 behaviour the failure path is meant to degrade to. It now unblocks before
  returning failure.
- **The arming window: a signal arriving during startup still killed the server.** The first shape of
  this patch armed inside each serve loop. But `cmd_serve_on` binds and listens *first*, so the port
  was already accepting while `serve_poll` was still running `session_pool_init` +
  `door_registry_init` — and a SIGTERM landing in that window met the default disposition and killed
  the process. Arming now happens in `cmd_serve_on` beside `signal_ignore(SIGPIPE)`, **before the
  socket is created**, for exactly the reason that call sits there.
  **This is the one finding that came from the smoke rather than from review**: it reproduced on
  roughly one run in three under the full suite while passing standalone every single time, which is
  precisely the shape hand-testing does not catch. Now 0 failures in 10 consecutive runs.

### Changed

- **Toolchain pin `6.5.33` → `6.5.34`.** Verified: `lib/` is **101/101 byte-identical to tag 6.5.34**
  and both `cycc` binaries match the tag — checked before trusting any number, per the 1.6.7 lesson.
  The release's headline (three `CYRIUS_IR=3` miscompiles) cannot reach agora, which never sets
  `CYRIUS_IR`; the live payload is the bayan fold above.
- **The release workflow now runs the tests.** It built and *published* without running a single one —
  CI ran them on push, but a tag can be cut from any commit, so nothing structurally prevented shipping
  a red tree. The Closeout Pass's "full test suite" gate existed only as CLAUDE.md prose. `cyrius test`
  and `cyrius fuzz` now gate the release.

### Known limitations (recorded, not fixed)

- **A player inside the Descent MUD delays poll shutdown.** `descent_proxy` blocks the sweep for as
  long as the session is in the MUD (documented since 1.6.0 at `src/descent.cyr`), bounded only by
  `DESCENT_IDLE_MS` = 30 minutes. The shutdown check is in that same sweep, so it does not run until
  the proxy returns. Making Descent a *state* in the poll loop is the standing fix; it is
  roadmap-tracked and larger than this cut.
- **N1's agnos arm is unverified on hardware.** It is written to mirshi's documented semantics — and
  those differ from Linux in a way that matters (below) — but agora's smokes run the Linux binary.
- **`src/test.cyr` does not include `src/main.cyr`**, so none of N1's or N3's functions can be
  unit-tested; they are covered by smoke 28 and by inspection. The `tests/` split that would fix this
  is already in the backlog.

### Notes for the next reader — two places the targets disagree

Both were found by reading the other side's source, not by testing, and both fail **silently**:

1. **Blocking a signal is required on Linux and wrong on agnos.** Linux needs the block or the default
   terminate action runs before the fd can be read. mirshi computes `deliverable = pending AND NOT
   blocked` (`mirshi/src/children.cyr:163`, consumed by the signalfd path in `dispatch.cyr`), so a
   blocked signal is exactly the one agnos will never report — and blocking is unnecessary there
   because `_do_kill` only ORs a pending bit and nothing terminates the guest. agora therefore blocks
   **only** on Linux. One arm for both compiles cleanly and arms a shutdown that can never fire.
2. **The sigset bit convention is off by one between targets.** Linux numbers bits from zero
   (bit = signum − 1); agnos numbers them from one (bit = signum). SIGINT|SIGTERM is `0x4002` on Linux
   and `0x8004` on agnos. darshana carries the identical split — `TTY_SIGMASK_EXIT` is `0x4003` /
   `0x8006` — which is what agora's mask was derived from.

## [1.6.7] — 2026-08-22 (toolchain + dependency cut: the binary loses 86% of itself)

**No features, no logic change, no agora source change beyond three version literals and one smoke
script.** cyrius **6.4.78 → 6.5.33** (42 releases) and a full `lib/` re-vendor; darshana holds at
**0.9.0** (verified current — latest tag, tip of main, and `VERSION`, with the lockfile commit matching
`git rev-parse 0.9.0`). 221/221 tests unchanged, both targets build, 27/27 example smokes green.

**14,571,744 → 2,010,320 B (−12,561,424 B, −86.2%)**; `--agnos` **1,994,240 B**.

### The two payloads

- **cyrius 6.5.11 fixed `is_dir` / `dir_list`** — agora's own upstream filing, now archived. `lib/fs.cyr`
  was burning **4,104 B of never-reclaimed bump-heap scratch per call**, on both arms of both functions.
  agora hits it once per directory entry inside `boards_list` ([src/board.cyr:961](src/board.cyr:961))
  and on the **unauthenticated** `enter` path ([src/main.cyr:497](src/main.cyr:497) → `board_exists` →
  `is_dir`). Bounded by the child's lifetime under the default `AGORA_SERVE=fork`; **process-lifetime
  under `poll`, and on agnos, which always polls** — i.e. an anonymous client could force permanent
  per-command heap growth that ADR 0021's arena never sees, because the allocation is inside a vendored
  lib rather than agora's own source. This is the same shape as 1.6.1's `sock_accept` payload.
  **Measured A/B on this workstation** (same compiler, libs varied; 3 boards × 50 posts, alternating
  `boards` + `list general`, 600 commands after warmup, RSS-sampled):
  **24,467 → 3,495 B/command (−85.7%)**. No agora code change.
- **The size collapse is sigil, not the compiler.** Nothing in the 42 releases changes DCE or global
  emission — `CYRIUS_DCE=1` still only NOP-fills code and *keeps* `.bss`, and cycc says so in its own
  build hint. The drop is the bundled **sigil** deleting 46 module-level banked arrays: **59 → 13**
  declarations, **1,587,782 → 11,358** declared array units (×8 B ≈ 12.6 MB, which is the whole delta).
  agora had been carrying ~12.6 MB of zero-filled RSA/bignum `.bss` it never called, inherited at the
  1.6.0 pin move and recorded then as "the 6.4.x stdlib's large static-BSS reservation".

### Fixed

- **`docs/examples/20-descent.sh` had been failing on the far side of the gateway.** The sibling
  Yeoman's Descent MUD is now **1.7.22** (it was 1.0.1 when this smoke was written) and refuses to boot
  without `data/zones/hub.rooms.cyml` relative to its CWD — *"world: FATAL — the room table was
  rejected"*, because a roomless server never loads the object table and the next disconnect would write
  an emptied inventory back. The smoke starts it in an empty `mktemp -d`, so the MUD was dead and step
  (3) was asserting against agora's honest *"The Descent is not answering (operator may have it
  offline)"*. The scratch dir is now seeded with the MUD's `data/`, which keeps the original isolation
  intent (player saves land in the scratch dir, never in the MUD repo). **agora's gateway was never
  broken** — this is the only source change in the cut outside the version literals.

### Verification notes — the toolchain snapshot on this workstation was not the released 6.5.33

Recorded because the numbers above are only meaningful against a known toolchain, and the first set
measured here were wrong by 215,520 B.

- `~/.cyrius/versions/6.5.33/` had been clobbered by an `install.sh --refresh-only` run out of the
  **dirty cyrius working tree** (that tree's `VERSION` reads **6.5.34**). Two vendored libs did not match
  the tag they were filed under — `bayan.cyr` (tag 215,533 B vs installed 641,083 B) and `patra.cyr`
  (264,731 vs 265,603) — and `bin/cycc` was the 6.5.34 build. Restoring all three from `git show
  6.5.33:…` makes the snapshot **101/101 byte-identical to its own tag**, and the binary drops
  2,225,840 → **2,010,320 B**. The published tag is correct; only the local install was dirty.
- **The binary is byte-identical whether compiled by 6.5.33 or 6.5.34**, verified directly, so
  2,010,320 B is compiler-independent and safe as the release metric.
- **The versioned wrapper does not pin `cycc`** — `~/.cyrius/versions/6.5.33/bin/cyrius build` still
  invokes whatever `cycc` is on `PATH`, and says so in its own drift warning. CI is exempt (it installs
  the released tarball into a fresh runner), but no local build is self-certifying. Upstream has this
  filed as `cyrius/docs/development/issues/2026-08-22-versioned-wrapper-does-not-pin-cycc.md`.

### Inherited fixes (no agora change; recorded so the next reader knows they are in)

- **`fmt_int` / `fmt_int_buf` / `print_num` emitted a bare `-` at `i64::MIN`** (6.5.8). `save_put_i64`
  formats raw xorshift64 PRNG state, whose orbit includes `0x8000…0`, so this was a silent loss of save
  PRNG continuity. All ten `fmt_int_buf` call sites already declare `var …[24]`, so the now-longer
  output cannot overflow.
- **`fl_alloc` / `fl_free` are documented thread-safe** behind a CAS spinlock gated on `_threads_active`
  (6.5.19), after five races were found upstream. agora spawns no threads and takes the two-load fast
  path — but ADR 0022's freelist no longer carries an undocumented thread-safety caveat.
- **`cyrius fuzz --poison`** arms freelist redzones and quarantine (6.5.28/6.5.29). Noted against
  roadmap **N4** with its limit: it instruments only `fl_alloc`/`fl_free`, and the IAC parser is entirely
  bump-allocated, so a `--poison` run against the parser reports zero violations no matter how far it
  overruns. It is useful for the door-state half, not the parser.
- **Main-source diagnostics are line-accurate again** (6.5.3 / 6.5.19 / 6.5.24) — the known limitation
  6.5.0 shipped with. Compile-error line numbers therefore move relative to 6.4.78; that is the fix
  landing, not drift.
- **`cyrius build` now reports every unresolved symbol** instead of dying on the first (6.5.23), and
  **syntax errors in never-called functions are no longer skipped** (6.5.17).
- **6.4.80 fixed a CRITICAL constant-fold bug** that was present in our 6.4.78 pin (`1 - 2 + 3` folding
  to 5 in the PEXPR tier). Verified agora had **zero** instances of the affected shape.

### Changed

- **Toolchain pin `6.4.78` → `6.5.33`** (`cyrius.cyml [package].cyrius`). Verified non-breaking against
  agora's real consumption surface — **71 stdlib functions across the 25 declared modules**: zero
  removals, zero renames, zero arity changes. The `gvar_toks` counting rule, the constant folder and the
  **4,096-slot limit are all untouched** across the span, so CLAUDE.md § Cyrius Conventions needs no
  amendment (agora declares 41 top-level `var`s — three orders of magnitude of headroom).
- **`lib/` re-vendored and verified byte-identical to tag 6.5.33.** A clean `rm -rf build lib && cyrius
  deps` resolves **50 files + darshana**, and drops the orphaned `lib/agnosys.cyr` — no cyrius has
  shipped it since 6.2.35 and agora declares it nowhere.
- **cyrius 6.5.32 made bare negative literals legal in enums** (`enum E { X = -1; }`). Verified at
  6.5.33 that the house `(0 - N)` form **still compiles**, so CLAUDE.md's "no negative literals"
  convention stands as written and no conversion is forced.

### Security

- The `is_dir` / `dir_list` fix above closes an **unauthenticated** path to unbounded heap growth under
  `AGORA_SERVE=poll` and on agnos. No CVE; found by agora and filed upstream at 1.6.6, fixed at cyrius
  6.5.11. Recorded here because the reachability — anonymous `enter`, pre-auth — is the same class the
  1.6.3 audit's `scores` finding was rated HIGH for.

## [1.6.6] — 2026-07-26 (doc-truth and process: the non-code half of the roadmap sweep)

**No behavior change. This closes the paperwork the 1.6.x line ran up.** The 2026-07-26 deferred-work
sweep produced 68 open items; this cut does every one that is documentation, process or a comment, and
leaves the four that change the running server on the roadmap. The theme is the same one the sweep
found: *most of the open work was verification and doc-truth, not features.* 221/221 tests, both targets
build, all smokes green. 14,571,688 → **14,571,744 B** (the deleted dead branch nets against three
new comments).

### Added

- **[ADR 0023 — the dual serve model](docs/adr/0023-dual-serve-model.md).** The largest architecture
  change since ADR 0007 — one process for all 64 sessions, `AGORA_SERVE={fork,poll}`, the session pool,
  the `sess_load`/`sess_save` context swap, agnos always polling — **had no ADR**. The index jumped 0020
  (1.4.6) → 0021 (1.6.2), and ADRs 0021 and 0022 both opened by retroactively narrating 1.6.0 because
  there was nothing to cite. 0023 records it, including the 1.5.0 agnos serial-accept decision, and states
  the lesson plainly: *ask what the old model was silently providing, not just what the new code does* —
  fork was providing the free list, a bound on bad connections, and crash isolation, and the poll model
  removed all three without a line of code saying so.
- **Three allocator/deferral gates in CLAUDE.md's Closeout Pass** (new step 8). Each was a mitigation an
  **Accepted ADR already relies on** while existing only as a sentence inside that ADR: *no bare
  `alloc()` reachable from `process_rx`* (ADR 0021 — would have caught both halves of the 1.6.2 arena
  miss), the *mixed-allocator scan* (ADR 0022 — an `alloc()` pointer reaching `fl_free` is heap
  corruption), and the *tree-wide deferral check*.

### Fixed

- **ADR 0007 amended, and the four ADRs that reason from it corrected.** 0007 still ships and is still
  the Linux default, but three of its statements are now conditional: its § Alternatives **rejects** the
  single-thread event loop that 1.6.0 built; its § Positive claims audit M1/M2 closed "via address-space
  isolation", which ADR 0021 measured as regressed under poll; and its § Negative — *"no shared state
  across sessions"* — is cited **verbatim** by ADRs 0010/0011/0012/0014 as the reason a feature was
  deferred. Under poll that premise is false, and on agnos it is *always* false. Each of the four now
  carries a note pointing at ADR 0023 § Relationship to ADR 0007. Nothing is broken — disk + `flock`
  remains correct and required while fork is supported — but *"fork forbids it"* is no longer a
  sufficient reason to defer a feature, and four deferrals are now honestly re-evaluable.
- **Untracked deferrals: 12 → 0, tree-wide.** `cyrius lint` reported **2**; it takes one file, and only
  `main.cyr` was ever linted by habit, so `telnet.cyr`'s five were invisible. Each of the twelve got the
  treatment it deserved: genuine ones now cross-reference a real roadmap entry (the gate is per-line, so
  the citation must sit on the deferral's own line), stale ones were retired, and three **false
  positives** are marked `#skip-lint` — `telnet.cyr`'s "follow-up subneg" means the subneg that *follows*
  agreement, and two are string literals inside `test_fail(...)` calls.
- **The unreachable agnos serial-accept branch is deleted** (`src/main.cyr`). `serve_mode_from_env`
  returns `SERVE_POLL` on **every** agnos path — the default, an explicit `"poll"`, and an explicit
  `"fork"` — so `cmd_serve_on` dispatches to `serve_poll` long before that loop. It had been dead since
  1.6.0, and its comment still announced the poll multiplex as pending work that the same cut shipped.
- **~20 stale comments retired.** The worst: `src/main.cyr`'s milestone map still marked **"M1 ← active"**
  (every milestone closed at 1.0.0); three separate comments claimed *"the accept loop single-tracks"*,
  false since 0.8.0 and doubly so since 1.6.0; `src/door.cyr` called `DOOR_UNIVERSE` "stubbed at 1.1.0"
  (wired since 1.2.0) and said shared world state "lands later" 200 lines above the framework that
  implements it; `src/ashes.cyr` said the victory condition would be "decided in a later bite" next to
  `ash_is_over`; `src/board.cyr`'s header still described the M5-A no-headers format four milestones
  after RFC-822 headers landed.
- **ADR index and statuses.** 0013 and 0014 were listed **Proposed** in `docs/adr/README.md` though both
  files and doc-health say Accepted; 0011 and 0014 carried in-file "in progress" statuses for releases
  that shipped in June. Two long-open ADR questions are closed with their answers: **0014's
  alliance/diplomacy model** (answered by 1.3.7's pact edge-list, union-find coalitions, and betrayal that
  needed no code — the question outlived its answer by four months) and **0013's per-game vs global house
  edge** (1.3.5's three deliberately different edges settled it).
- **`CYRIUS_DCE=1` in CI and release.** CLAUDE.md states it as current practice; it was in **neither**
  workflow, so CI had been measuring a different artifact than the one the docs describe — and binary
  size is a tracked release metric.
- **`state.md`'s orientation block** was five releases stale (it still opened with 1.6.0) even though its
  header was current — the release post-hook is only half working. Rewritten, and pointed at
  `roadmap.md` § Now as the single authoritative open-work list.

### Notes

- **What is deliberately still open**: roadmap § Now is now four items, **all code** — clean shutdown
  (N1: no SIGINT/SIGTERM anywhere, and both `stop` flags are provably never assigned, so the server can
  only be killed), crash-safe durable writes (N2), the two poll-mode holes (N3), and the fuzz harness
  (N4). Plus § Cross-repo and a 28-row backlog.

## [1.6.5] — 2026-07-26 (the audit's LOWs — and the audit ledger closes)

**Closes the last four findings from the 2026-07-26 audit.** With this cut **every HIGH, MEDIUM and LOW
is fixed**; only the one INFO item remains, and it is deliberate. No new features. 221/221 tests (one
updated — see below); both targets build; all 19 sequential smokes plus the both-model set green; **new
smoke [`27-audit-lows.py`](docs/examples/27-audit-lows.py)** and `24-descent-serve-models.sh` extended.
14,571,568 → **14,571,688 B**.

### Security

- **The operator's `--store` is bounded** (`src/main.cyr`, **L1**, long-standing). `board_path` memcpy's
  it into a 512-byte buffer with no check and every storage path builds on that, so an over-long
  `--store` overflowed. Operator error rather than an attack — but since the 1.6.2 arena the overflow
  lands in a **shared** buffer, so it can corrupt another allocation in the same command rather than an
  isolated one. Bounded once at each of the two parse points (`cmd_serve`'s own, and `parse_store`, which
  is the single `--store` parse for *every* CLI verb) rather than at ~30 builders. Over-long **refuses**
  rather than truncating: a silently shortened store root would point at a *different* directory, which
  is worse than an error. Verified: exit 2 with a clear message; normal paths unaffected.
- **Wire-side posts get the control-byte filter the CLI always had** (`src/board.cyr`, **L2**,
  long-standing). BEL, BS, FF and DEL persisted into stored posts from the wire — the CLI refused them,
  telnet did not — and every later reader got them. `input_byte_ok` now drops the C0 set and DEL. **TAB,
  CR and LF stay**, and CR/LF are load-bearing: this filter runs *before* EOL detection in `process_rx`,
  so dropping them would break line dispatch entirely. Verified: `a<BEL>b<BS>c<DEL>d` is stored as
  `abcd`.

### Fixed

- **Echo stops when a client actually revokes it** (`src/main.cyr`, **L3**, long-standing). agora
  announces `WILL ECHO` at connect; a client answering `IAC DONT ECHO` got a correct `WONT ECHO` back and
  then **kept being echoed at** — double characters for anyone doing local echo. The gate is
  `opt_us(ts, OPT_ECHO) != Q_NO`, deliberately **not** `== Q_YES`: a client that never answers our WILL
  sits in `Q_WANTYES` forever, so gating on `Q_YES` would kill echo for netcat, raw sockets and every
  scripted client — including agora's own smokes. Both directions are asserted in the new smoke for
  exactly that reason: echo survives for a non-negotiating client, and stops after a real revoke.
- **Bytes pipelined behind `descent` now reach the MUD** (`src/descent.cyr`, `src/main.cyr`, **L4**,
  long-standing). `process_rx` dispatches every complete line in one recv buffer, so a client sending
  `descent\r\nnorth\r\n` in a single segment (a script, a paste, any client that coalesces) had `north`
  **lost to the MUD and then executed as a BBS command** once the proxy exited. `process_rx` now publishes
  the remainder of the buffer before each dispatch and `descent_run` claims it, forwarding it to the MUD
  before the shuttle starts; a claimed tail is not re-executed. The publish/claim pair lives in
  `descent.cyr` beside its only consumer (and because `test.cyr` links that module without `main.cyr`).
  Verified with a fake MUD that logs what it receives: the pre-1.6.5 binary loses `north`, this one
  delivers it — under **both** serve models.

### Changed

- **`t32_input_byte_ok_filters_nul_esc` updated to the widened contract.** It asserted *"DEL should pass
  (BS handling is M5-B+ polish)"*, which conflated two separate questions: whether BS/DEL should **edit
  the line** (still open — the audit's INFO item) and whether they should be **stored in a post**. The
  answer to the second is no. The audit predicted this test would move; it now asserts BEL/BS/FF/DEL and
  IAC are all dropped, and TAB/CR/LF still pass.

### Added

- **New smoke [`27-audit-lows.py`](docs/examples/27-audit-lows.py)** — L1 (over-long `--store` refused,
  normal one still works), L2 (BEL/BS/DEL dropped from a stored post, printable text intact) and L3 (echo
  kept for non-negotiating clients, suppressed after `IAC DONT ECHO`).
- **`24-descent-serve-models.sh` extended for L4** — it already had the fake-MUD harness, so it now sends
  `descent` and a follow-on command in one segment and asserts the MUD received **both** the typed and
  the pipelined bytes.

### Notes

- **The audit ledger is closed except for one deliberate INFO item**: BS/DEL are still not *edited out*
  for clients that never negotiate LINEMODE. 1.6.5 stops them being **stored**; making them **edit** is
  roadmap polish that would change a passing test, and the audit recorded it as deliberate.

## [1.6.4] — 2026-07-26 (the audit's MEDIUMs: the wire contract, admission, and two ordering bugs)

**Closes the four MEDIUM findings the 1.6.3 audit recorded rather than fixed.** No new features. The
theme is that three of the four were *ordering or accounting* mistakes — the right check existed but ran
too late, or the wrong bytes counted as activity — and the fourth was a wire-contract violation agora had
carried since M1. 221/221 tests unchanged; both targets build; all 19 sequential smokes plus the
both-model set green; **new smoke [`26-iac-and-idle.py`](docs/examples/26-iac-and-idle.py)**.
14,571,552 → **14,571,568 B**.

### Security

- **IAC (0xFF) is now handled per RFC 854 in both directions** (**MEDIUM**, long-standing since M1).
  0xFF is IAC on the wire, and a *data* byte of that value must be sent as `IAC IAC` or the receiver reads
  it as the start of a command. agora did this on **no** egress path, and `input_byte_ok` admitted 0xFF at
  ingress — so a registered user could put raw telnet commands into a post (`FF FA 18` is `IAC SB
  TERMINAL-TYPE` with no `IAC SE`, which wedges a conforming client) and **every later reader** got them,
  with no removal path short of the operator editing the file. CLAUDE.md settles which side is correct:
  *"the wire is the contract — RFC 854 ... any deviation is a bug, not a feature."* Both halves:
  - **Egress** — new `send_text` doubles 0xFF and now carries the nine stored-content sites (post body,
    subject, From handle + fingerprint, derived reply subject, chat scrollback and live tail). It is
    deliberately **not** folded into `send_buf`: that is the funnel for every byte agora sends *including
    the telnet layer's own command sequences*, which must not be doubled. The split is by intent —
    protocol bytes via `send_buf`, content bytes via `send_text`.
  - **Ingress** — `input_byte_ok` drops 0xFF, so nothing new can be stored. 0xFF is never valid in
    well-formed UTF-8, so no legitimate text is affected.
  Verified end to end: a planted post containing `before FF FA 18 after` renders on the wire as
  `before FF FF FA 18 after` — the 0xFF doubled, the following bytes inert — with no bare IAC anywhere;
  and a client sending `IAC IAC` gets nothing stored or echoed.
- **`keygen` can no longer overwrite an existing identity on agnos** (`src/account.cyr`, `src/board.cyr`,
  **MEDIUM**, long-standing, agnos-only). The local `enum BoardOpen { BO_EXCL = 128; }` hardcoded the
  **Linux** O_EXCL bit; agnos has no exclusive-create flag, so `file_open` dropped it silently and both
  callers degraded to a plain create — `keygen` would overwrite a user's Ed25519 seed (silent,
  unrecoverable) and `post_new` could clobber an existing post file. Both sites now use the stdlib's
  `file_create_exclusive` (cyrius 6.4.57, new since the 1.6.1 pin), which is genuinely exclusive on
  Linux/macOS and does a best-effort existence check on agnos — not atomic there, but a refusal instead of
  data loss. The local enum is deleted, the same shape as 1.6.2's `SYS_MKDIR` removal. Verified: a second
  `keygen` against an existing keyfile now refuses and leaves the key byte-identical.
- **`cmd_post` validates `--board` before touching the filesystem** (`src/main.cyr`, **MEDIUM**,
  long-standing). `board_can_post` assembles `<store>/<board>/.policy` and `.admins` and reads them, and it
  ran **nine lines before** the name was validated — so `--board ../../../../etc` reached the filesystem
  first. The 0.7.0 audit fixed exactly this ordering for `list` and `read`; `post` had quietly re-opened
  it. Nothing between the two depends on the policy result, so this is a pure reorder. Verified: the
  traversal is refused with the invalid-name message and nothing is created outside the store.

### Changed

- **Protocol chatter no longer counts as activity** (`src/main.cyr`, **MEDIUM**, the poll pool's admission
  gap). `IAC NOP` is two bytes, consumed by the state machine with no response and no data byte — and it
  refreshed the session's idle timer, so 64 connections sending one every 50 s pinned every slot in the
  pool **invisibly**, at ~2 bytes/minute each, with nothing ever typed. The idle refresh moves out of the
  poll sweep (which fired on *any* bytes arriving) and into `process_rx`'s `EV_DATA` arm, so only a byte
  that actually reaches the session as data counts. A keepalive-only connection now ages out exactly like
  a silent one. Verified: an `IAC NOP` keepalive is reaped at 60.0 s (`SESS_IDLE_MS`) while a session
  sending real input is still alive at 80 s.
  **Scope, deliberately**: this fixes the cheap attack, not every attack. A client that sends a real data
  byte every 50 s still holds a slot, which is indistinguishable from a very slow typist without a
  session-lifetime or per-source cap. Both were considered and **not** taken: a lifetime cap also
  disconnects legitimate long sessions (a QUEST run, an idle chat), and a per-source cap needs
  `sys_getpeername`, which **agnos does not have** — it would protect Linux and leave the target that
  *only* runs poll unprotected, while also mis-firing on a NAT'd LAN. `MAX_SESS` remains the operator's
  bound.

### Added

- **New smoke [`26-iac-and-idle.py`](docs/examples/26-iac-and-idle.py)** — pins both fixes, because both
  concern bytes a normal session never produces: it plants a post containing a raw `IAC SB` and asserts the
  wire copy is doubled with no bare IAC surviving, asserts a client-sent 0xFF is never echoed, and races an
  `IAC NOP` keepalive against a real-input session to assert only the first is reaped. (~80 s for the idle
  half; `--fast` runs the IAC half alone.)

## [1.6.3] — 2026-07-26 (the door states learn to die: DD_FREE, and what the audit found)

**agora's memory is now bounded.** 1.6.2 fixed the per-line leak and named what it could not reach: the
ten door-game state objects and the three chat-bot couch states, which live across many lines and so
cannot belong to the per-command arena. This cut gives every game a **`DD_FREE` hook**
([ADR 0022](docs/adr/0022-door-state-free-hook.md)) backed by the freelist — the module CLAUDE.md has
prescribed since M6 and that agora had never once called. Running `play`/`quit` cycles through a poll-mode
server, total RSS growth goes from **720 KB at 600 commands and 2,460 KB at 2,400** (linear, forever) to
**208 KB and 203 KB** — flat, one-time setup, no per-command component.

It also carries the fixes from a **full P(-1) audit** ([`docs/audit/2026-07-26-audit.md`](docs/audit/2026-07-26-audit.md)):
eight dimensions swept in parallel, every finding put to an independent skeptic instructed to refute it.
The headline is one the arena work had missed entirely — **`scores` is unauthenticated and leaked
~5 KB per invocation**, so any client that can reach the port could exhaust the server's heap without
logging in. 221/221 tests unchanged; both targets build; all 20 example smokes green plus a new churn
smoke; 14,567,424 → **14,571,552 B**.

### Security

- **Unauthenticated heap exhaustion via `scores`** (`src/main.cyr` `door_render_leaderboard` /
  `door_leaderboard_path` / `door_post_score`, **HIGH**). The 1.6.2 arena conversion covered
  `session_execute`'s own arms but never reached the leaderboard helpers they call, and unlike `post` /
  `reply` / `chat` / `play`, **`scores` needs no login**. Every invocation permanently burned a path
  buffer, a 16 KB read buffer, three index arrays and a per-row buffer allocated *inside* the ranking
  loop — measured at **5,140 B per command**, and the early-out for an absent leaderboard fires *after*
  most of it. Under poll that is one process's heap, so a client pipelining `scores` in a loop walks the
  server toward the point where `alloc()` returns 0 and the next store faults — taking all 64 sessions
  with it. All nine sites now use `cmd_alloc`, and the per-row buffer is hoisted out of the loop:
  **5,140 → 31 B per command**.
- **The chat live-tail leaked on every idle tick** (`src/main.cyr` `chat_flush_tail`, **HIGH**). It
  allocated `CHAT_LOG_BUF + CHAT_TAIL_CAP + 8` per call, and it is called on the **idle poll tick**, not
  just after a typed line — so a session that merely *sits* in a channel leaked every `CHAT_TICK_MS`
  with no input at all. Because the tick is not bracketed by the per-line arena reset, the fix is three
  dedicated process-lifetime buffers rather than `cmd_alloc`: dispatch is single-threaded and neither
  buffer outlives the call, so sharing them is safe where arena scratch would not be.
- **No send return was checked anywhere in the tree** (`src/main.cyr` `process_rx`, **HIGH**,
  long-standing). A tree-wide grep for a tested send return finds **zero hits across ~164 call sites** —
  and two of them sit inside the per-byte ingress loop. Under fork, a client that stops reading makes every
  `sys_write` park for the full 60 s `SEND_TIMEOUT_SECS` and return 1; the loop discarded that and moved to
  the **next byte**, so one 4 KB recv could pin a forked child for hours while children are unbounded.
  Under poll, `sess_tx_enqueue` refuses an over-cap write and returns 1 without copying, and nobody closed
  the session — it stayed open but permanently mute, holding a slot: exactly the "slow-reader defense" its
  own comment claims and never implemented. Worse, this silently disarmed the SO_SNDTIMEO mitigation the
  2026-06-15 audit closed **T2** with — the timeout fired and the result was thrown away. Both sites now
  set `quit` and leave the loop, which both serve models already turn into a close. *Fix verified by
  inspection and no-regression; the trigger itself could not be staged end to end — a non-reading client's
  kernel absorbs enough that the server never stalls.*
- **`descent_write_all`'s EAGAIN retry was an unbounded busy-spin** (`src/descent.cyr`, **HIGH**, **a bug
  1.6.2 introduced**). The client fd is `O_NONBLOCK` under poll, so a peer that stops reading returns
  EAGAIN forever and the retry was a bare `continue` — no sleep, no deadline. That function runs inside the
  process owning **all 64 sessions**, so one wedged Descent player pegged a core and froze every other
  session permanently. Now paced at 20 ms (the sweep cadence) with a 10 s deadline, after which the peer is
  treated as dead. Worth recording plainly: the 1.6.2 cut fixed a class of bug and introduced a fresh
  instance of it one function away, which is the argument for auditing *after* a hardening cut.
- **`account_register` wrote the user files without `O_TRUNC`** (`src/account.cyr`, **MEDIUM**,
  long-standing). Re-registering the **same key** under a shorter handle left the tail of the previous
  value behind. Reproduced end to end: `register --handle averylonghandle` then `register --handle qix`
  left `handle` containing `qix\nylonghandle\n`, and `whoami` reported the wrong handle from then on.
  Registration is idempotent by design, so overwriting in place is intended — it just has to overwrite the
  whole file.
- **The unauthenticated login path leaked per attempt** (`src/main.cyr` `process_rx`, **MEDIUM**) — the
  signature, public-key and verify-message buffers on the `auth:` arm, plus the per-connection greet
  buffer and the per-line chat sanitizer buffer. All are inside the per-line dispatch, so they move to
  `cmd_alloc`. An attacker could previously drive them with `login x` / `auth: …` repeatedly.

### Added

- **`DD_FREE` (descriptor slot 208; `DD_SIZE` 208 → 216)** and ten `*_free` functions —
  `sl_free`, `pa_free`, `th_free`, `ez_free`, `py_free`, `qu_free`, `jw_free`, `ol_free`, `ash_free`,
  `decode_free` — each written directly beneath its game's constructor so the pairing stays honest. Every
  game's state block **and the buffers it owns** now come from `fl_alloc`: Port Authority's galaxy and its
  two tables, the Handler's agent roster and cable register, Jabberwacky's seven corpus buffers,
  Olympiad's five, Decode's four, Eliza's four. The shared world snapshot is deliberately **not** freed —
  `SL_WORLD` / `PA_WORLD` / `TH_WORLD` / `AE_WORLD` point at the session slot's buffer, not at state-owned
  memory.
- **Three release points**: `door_state_free()` on the `quit` path (after `door_save_on_exit`, which reads
  the state); `session_door_free(s)` from `session_release` and defensively from `session_reset`, for a
  player who **disconnects mid-game**; and the `play` launcher before installing a replacement. The
  slot-based variant exists because under poll the `g_*` globals belong to whichever session was last
  `sess_load`ed — freeing through them at release time would free **another player's game**.
- **The three chat-couch bot states** (`SESS_ELIZA` / `SESS_PARRY` / `SESS_JABBER`) are freed on the same
  paths; they are built by the same constructors and were leaking identically.
- **New smoke [`25-door-state-churn.py`](docs/examples/25-door-state-churn.py)** — the regression pin for
  the free paths, and deliberately hostile to them: enter/quit churn across all nine practice doors,
  quit-then-immediately-enter alternation (so a freed state's blocks are handed straight back out to the
  next game, which is where a bad free shows up), and repeated **disconnect-mid-game** so
  `session_release` frees a live slot. Green on both serve models at 360 cycles.

### Changed

- **61 per-line scratch buffers inside the game modules move to `cmd_alloc`** (`ashes` 22, `smuggler` 7,
  `port_authority` 7, `eliza` 6, `quest` 5, `handler` 4, `jabberwacky` 3, `olympiad` 3, `decode` 3,
  `parry` 1). These are the per-feed working buffers — normalizers, weight tables, the Ashes combat
  resolver's coalition arrays — with a one-line lifetime that ADR 0021's arena already covers. This is
  what takes Jabberwacky from 8,998 to **478 B/command** and Eliza from 1,229 to **348**.
- **`CMD_ARENA_BYTES` 256 KB → 512 KB, and the 1.6.2 sizing note corrected.** That note claimed the `read`
  path peaked at ~100 KB and that the fallback "is not expected to fire in practice". Wrong, and
  measurable: `read` allocates its own id list + post + header buffers (~166 KB) and then calls
  `replies_to`, which allocates a **second** id list and post buffer (~98 KB) to scan for children —
  ~264 KB against a 256 KB arena, so on a 150-post board every `read` pushed ~15 KB into the `alloc()`
  fallback (**30,133 → 14,828 B/command**; the remainder is `dir_list`). The lesson is in the header now:
  a nested call can double a command's footprint without any single function looking expensive.
- **`boards_list`'s per-entry path buffer** and **the leaderboard's per-row buffer** are hoisted out of
  their loops.

### Fixed (tests)

- **`16-casino.sh` was flaky, and had been for a long time** — measured **3/6 runs failing** on the 1.6.2
  binary. Its QUEST section farmed gold with a *fixed* attack budget, but monster HP comes from the seeded
  PRNG, so a tougher-than-average beast left the player mid-fight when the script pressed `c` and the card
  table never rendered; the mugger check on returning to town could end the run outright too. The grind is
  gone entirely — the assertion already accepts a funds-reject as proof of the wager wiring, so there was
  never a reason to farm first. **8/8 runs pass.** Worth stating plainly because it cost real time: the
  failure first looked exactly like a 1.6.3 regression, and only a pass-rate comparison against the 1.6.2
  binary (6/6 vs 3/6) showed it was pre-existing.

### Notes

- **`dir_list` remains the one unfixed residue** and it is not agora's to fix: `lib/fs.cyr:153` allocates
  a 4 KB `getdents` buffer, a vec, and one `Str` per directory entry on every call, from the vendored
  stdlib. That is the whole of the ~6.9 KB/command that `boards` / `list` still show, and it scales with
  directory size. The fix is a cyrius-side variant writing into a caller-supplied buffer — same shape as
  the 1.4.5 `sock_set_send_timeout` ask, which shipped upstream and returned in a later pin.
- **Where the audit's remaining findings went** — see the audit document for the full list with severities
  and the refuted ones. Items not fixed here are recorded there with a disposition rather than silently
  carried.

## [1.6.2] — 2026-07-25 (the poll model pays its debts: SIGPIPE, the arena, and the agnos syscalls)

**1.6.1 listed three deferred items; this cut closes all three, and two more the work uncovered.**
Every one of them is the same story: 1.6.0 moved agora from a process per connection to *one process for
all 64 sessions*, and three assumptions that were true under fork quietly stopped being true under poll.
An unhandled SIGPIPE went from killing one child to killing the server. A bump allocator with no free
went from "the arena dies at child exit" to "the arena grows until it faults". And two Linux syscall
numbers that agnos assigns to other calls became reachable on a target that only runs the poll model.
Along the way the Descent gateway turned out to be **silently broken under `AGORA_SERVE=poll`** since
1.6.0, and the pool-exhaustion message had been going out truncated. 221/221 tests unchanged, both
targets build, all 21 runnable example smokes green (the Descent one now against a real MUD *and* a fake
one, per serve model). 14,567,408 → **14,567,424 B**.

### Security

- **SIGPIPE is ignored before the listener opens** (`src/main.cyr` `cmd_serve_on`). agora had no signal
  disposition anywhere in `src/`, and every byte it sends leaves through a flagsless `sys_write`
  (`send_buf`'s fork branch, `session_drain`'s poll branch, the Descent proxy, and the pool-full reply).
  A peer that closes mid-write raises SIGPIPE, whose default disposition **terminates the process** — no
  error return, no cleanup. Under fork that cost one connection's child. Under the 1.6.0 poll multiplex
  it costs **the whole 64-session server**, unauthenticated, from a client that merely disconnects
  rudely — and poll is the only model on agnos. `signal_ignore(SIGPIPE)` (cyrius **6.4.51**, which did
  not exist at the 6.4.32 pin 1.6.1 moved off) converts it to an EPIPE return, which both write paths
  already handle correctly: `send_buf` returns 1 on any `n <= 0` (the 1.4.4 T1 fix) and `session_drain`
  returns the negative errno, which its callers test with `< 0` — EWOULDBLOCK keeps its own arm, so a
  slow reader still just retries next sweep. Placed before the model dispatch so it dominates poll, the
  fork parent, its children (dispositions survive `fork`, and agora never `exec`s), and the agnos serial
  loop; deliberately **not** in `main()`, so CLI verbs keep the default disposition and `agora list |
  head` still terminates like a Unix filter. [ADR 0007](docs/adr/0007-fork-per-accept-concurrency.md)
  rejected `sigaction` over the `rt_sigaction` `sa_restorer` trampoline; `signal_ignore` builds the
  32-byte SIG_IGN act itself and needs no trampoline, so that objection is retired. **Regression-pinned
  by the new smoke [`23-sigpipe-survival.py`](docs/examples/23-sigpipe-survival.py)**, which had to earn
  its teeth: an immediate RST is *not* enough (the next write fails with ECONNRESET, an ordinary error),
  so the smoke pipelines a large request, closes cleanly with output still pending, and never reads —
  the server's next write lands, the peer's stack answers RST, and the write after that raises SIGPIPE.
  Against a build without the fix it kills the poll server on the 4th client (**exit 141 = 128 + 13**);
  against this build both serve models survive 12 rounds and keep serving.

### Fixed

- **The Descent gateway was broken under `AGORA_SERVE=poll`** (`src/descent.cyr` `descent_proxy`) — a
  1.6.0 regression, silent until now. In poll mode `send_buf` **ignores its fd argument** and enqueues to
  the active session's tx queue, which is right for BBS output and wrong for a proxy: the client→MUD
  direction (`send_buf(mfd, ...)`) put the player's keystrokes on the player's *own* outbound queue, so
  **the MUD received nothing at all**. The gateway looked alive — the MUD's banner still reached the
  client — but no input ever arrived. The MUD→client direction was wrong for a second reason: it queued
  bytes that only `session_drain` can flush, and `session_drain` cannot run while the proxy loop is
  running, so MUD output would sit there until it overflowed `SESS_TX_CAP`. The shuttle now uses its own
  direct full-write (`descent_write_all`) on both fds, treating EAGAIN as a retry since the client fd is
  `O_NONBLOCK` in poll mode. Verified with a fake MUD that logs what it receives: before, the log stays
  empty under poll and fills under fork; after, both fill. **New smoke
  [`24-descent-serve-models.sh`](docs/examples/24-descent-serve-models.sh)**; `20-descent.sh` against the
  real Yeoman's Descent still passes.
- **The pool-exhaustion message was truncated on the wire** (`src/main.cyr` `serve_poll`). The write said
  33 bytes; the literal `"server full — try again shortly\r\n"` is **35** — the dash is an em dash
  (U+2014, three bytes in UTF-8) — so the short count cut off exactly the trailing CRLF and the one
  message a client gets when all 64 slots are full arrived unterminated. Verified by filling the pool:
  before, 33 bytes and no CRLF; after, 35 and terminated. This is also the only socket write in agora
  that does not go through `send_buf`, so a `send_buf`-based audit misses it.
- **`store_ensure` no longer dispatches a GPU matmul on agnos** (`src/board.cyr`). agora declared its own
  `enum BoardSys { SYS_MKDIR = 83; }` — mkdir's number on Linux x86_64 — which collided *by name* with
  the stdlib's agnos `SYS_MKDIR = 9`, so an `--agnos` build warned `duplicate symbol 'SYS_MKDIR'
  redefined with conflicting value (last definition wins)` and one of the two callers got the wrong
  number. 1.6.1 flagged that the cyrius 6.4.6x GPU syscall band had made agnos 83
  `SYS_GPU_DISPATCH_F64` (its own table comment reads "MKDIR on Linux"). The local enum is deleted and
  `store_ensure` routes through the stdlib `sys_mkdir`, with an `#ifdef` for the one genuine
  incompatibility: Linux/macOS take `(path, mode)`, agnos takes `(path, pathlen)` — passing `PERM_DIR`
  as a length would ask agnos to read 493 bytes of path. The duplicate-symbol warning is gone from the
  `--agnos` build.
- **The top-level exits are portable** (`src/main.cyr`, `src/test.cyr`) — `syscall(60, exit_code)` →
  `sys_exit(exit_code)`. 60 is exit only on Linux x86_64; on agnos exit is **0** and 60 is `SYS_WINSIZE`
  (nullary), so an agnos build queried the console grid, discarded the answer, and fell off the end of
  the program instead of terminating. The fork child already used the portable `sys_exit` — these two
  were the outliers. Exit codes verified unchanged on Linux (2 for an unknown command, 0 for success).
- **The Descent proxy's `poll(2)` is guarded and has an agnos peer** (`src/descent.cyr`). The raw
  `syscall(7, pfds, 2, ...)` was unguarded; 7 is poll only on Linux/macOS — on agnos it is `SYS_OPEN`, so
  the pollfd array was being opened as a path. The Linux/macOS branch keeps the raw call (the cyrius
  stdlib exposes no poll wrapper, only epoll — `lib/net.cyr`'s own `net_connect_sa_nb` does exactly the
  same thing) but now lives under the target guard, and agnos gets a real peer rather than a stub:
  non-blocking `sys_sock_recv` on both sockets paced by `sys_sleep_ms`, the same pattern `serve_poll` /
  `sess_recv_nonblock` already use there.

### Changed

- **Per-command allocations go through a scratch arena** (`src/arena.cyr`, new;
  [ADR 0021](docs/adr/0021-per-command-scratch-arena.md)). agora has 252 `alloc()` sites outside
  `test.cyr` and called `free`/`fl_free` **zero** times — correct under [ADR
  0007](docs/adr/0007-fork-per-accept-concurrency.md), where process exit *was* the free list, and a leak
  under 1.6.0's one-process-for-everyone poll model. Measured on 1.6.1: **7,473 B leaked per command**,
  dead linear (400 commands → 2,988 KB; 1,600 → 11,676 KB). `cmd_alloc` hands out 8-byte-aligned scratch
  from a 256 KB region and `cmd_scratch_reset` reclaims all of it, called once per dispatched line from
  `process_rx` — the single point that dominates command, door, chat, login and posting lines in **both**
  serve models. 60 call sites converted; anything that outlives the line (the session pool, the door
  registry, the telnet buffers, the CLI verbs) deliberately stays on `alloc()`. Oversize requests fall
  back to `alloc()` rather than failing. Same store, back-to-back:

  | Workload | Before | After |
  |---|---:|---:|
  | `help` / `whoami` (no filesystem) | 34 B/cmd | 27 B/cmd |
  | door play (`quest` — a frame render per line) | 3,434 B/cmd | 389 B/cmd |
  | Eliza door (per-line render + bot state) | 4,035 B/cmd | 1,229 B/cmd |
  | `boards` / `list` (30-post store) | 13,343 B/cmd | 4,838 B/cmd |

- **`g_uni_world` and `g_reply_subject` are owned by the session slot** (`src/main.cyr` `session_alloc` /
  `session_reset`). Both were lazily allocated behind an `== 0` guard on a *process* global — but
  `sess_load`/`sess_save` swap those globals per session, so every new session saw 0 and allocated again:
  an 8 KB + 264 B leak for each session that entered a Universe door or replied to a post, bounded by
  sessions **served**. They now allocate once per pooled slot (64 total, ever, +541 KB one-time) and
  `session_reset` clears their contents instead of nulling the pointer.
- **`boards_list`'s path buffer is hoisted out of its loop** (`src/board.cyr`) — it allocated a fresh
  512-byte buffer per directory entry, so listing a store burned 512 B × entries every time anyone typed
  `boards`. It is pure scratch, so one buffer reused across iterations is equivalent.

### Deferred

- **The ten door-game state objects and three chat-bot states** (`handler.cyr`, `quest.cyr`,
  `port_authority.cyr`, `smuggler.cyr`, `olympiad.cyr`, `ashes.cyr`, `jabberwacky.cyr`, …). These live
  across many lines, so the arena cannot own them; freeing them needs a `DD_FREE` hook on the door
  descriptor plus a `*_free` per game — ten modules and an ABI change, which does not belong in the same
  cut as a signal fix and a syscall sweep. What remains is a per-`play` residue bounded by how fast a
  human re-enters doors, not by traffic (it is the whole difference between the Eliza row's 1,229 B/cmd
  and the door row's 389 B/cmd above). Scheduled as the 1.6.3 headline.
- **`dir_list`'s per-call allocation is upstream, not agora's** (`lib/fs.cyr:153`). It allocates a 4 KB
  `getdents` buffer, a vec, and one `Str` per directory entry on every call, from the vendored stdlib
  where agora cannot redirect it — that is the entire 4,838 B/cmd residue on filesystem commands, and it
  scales with directory size. The fix is a cyrius-side variant writing into a caller-supplied buffer,
  the same shape as the 1.4.5 `sock_set_send_timeout` ask.
- **The Descent proxy still blocks the poll sweep** for as long as a player is in the MUD, stalling other
  sessions. Making Descent a state in the poll loop rather than a blocking call is a larger change than
  this cut takes on; the byte-routing bug above is fixed independently of it.

## [1.6.1] — 2026-07-25 (toolchain 6.4.78 + darshana 0.9.0 — the poll loop stops leaking)

**A dependency cut, and the one that repairs a live leak in the 1.6.0 serve loop.** No new features and
no agora logic change — the pin moves **cyrius 6.4.32 → 6.4.78** (46 releases) and the one git dep
**darshana 0.8.2 → 0.9.0**, and the only source edits are the three inlined version literals. The reason
it matters is one stdlib fix: **cyrius 6.4.61 stopped `sock_accept` allocating a fresh `Err(EAGAIN)`
`Result` on every call** — and the 1.6.0 poll multiplex calls it in an accept-drain loop on a
non-blocking listener every ~20 ms sweep, where it almost always returns EAGAIN. That was a bump-heap
arena leak proportional to *uptime*, on the model agnos always runs; the upstream fix names agora as an
affected consumer. This cut also re-vendors `lib/` correctly for the first time in two bumps: six stdlib
files had been silently skipped by `cyrius lib sync` (**four of them stale since the 1.6.0 cut** — see
new architecture note **[002](docs/architecture/002-lib-sync-same-size-skip.md)**). 221/221 tests
unchanged, no source change required to compile; both targets build; 11 wire smokes green — with the
Ed25519-login and 3-way-concurrency smokes re-run under **both** `AGORA_SERVE` models. 14,118,456 → **14,567,408 B** (+448,952 B — the wider 6.4.78 stdlib surface, not
agora code). First re-bench since the 1.0 closeout: the four telnet-parser paths are within ±2 ns of the
0.9.2 baseline, `announce_salvo` **134 → 124 ns (−7%)**.

### Changed

- **Toolchain pin 6.4.32 → 6.4.78** (`cyrius.cyml [package].cyrius`) — closes the wrapper/manifest drift
  (the installed `cycc` had advanced to 6.4.78, so every build carried a pin-drift warning). Verified
  non-breaking against agora's actual consumption surface: zero public functions removed or renamed and
  zero arities changed across all 25 declared stdlib modules; 15 of them are byte-identical. The bulk of
  the 46-release span cannot reach agora — the `lib/async.cyr` epoll-reactor arc (6.4.33–6.4.45, agora
  does not declare `async`), the Windows/IOCP and cx-bytecode/SIMD slots, and the scalar-float language
  work. Every release in 6.4.59–6.4.68 verifies x86-64 Linux self-host byte-identity, so the codegen
  agora emits is unchanged there; the one codegen-affecting change in range is 6.4.56's SESTYPE
  normalization, which touches ordinary call expressions (agora is call-heavy and table-dispatch-heavy —
  this is part of the binary delta above, and is why the delta is not zero).
- **`sock_accept` no longer leaks per poll** (cyrius **6.4.61**, `lib/net.cyr` — the only change in that
  file across the whole bump) — two fixes in one: the WOULD_BLOCK path now returns a lazily-boxed shared
  `_net_eagain()` singleton instead of a freshly-allocated `Err(_NET_EAGAIN)` `Result`, and the POSIX
  path calls `accept(NULL, NULL)`, dropping a 20 B/call peer-address allocation that was written but
  never read. Measured upstream at **40 B/poll → 0**. agora's two accept sites are `serve_poll`'s inner
  drain loop (`src/main.cyr:2167`, which spins until EAGAIN on *every* ~20 ms sweep) and the fork-model
  accept (`:2676`); both only `is_ok()` / `result_unwrap()` the Result and never write through it, so the
  shared-singleton contract holds. agora never reads the peer address, so `accept(NULL, NULL)` is
  transparent — but note that if it ever wants the client IP (per-IP throttling, audit logging),
  `sock_accept` no longer produces a `sockaddr` on any path and the new `sys_getpeername` (6.4.64) is the
  supported route. No agora edit — the fix arrives with the pin.
- **sigil folded 3.10.1 → 3.12.1** (bundled in the toolchain snapshot) — agora's consumed crypto surface
  (`sha256`, `ed25519_keypair`, `ed25519_sign`, `ed25519_verify`) is signature- and behavior-identical;
  3.12.1 routes its hash bank through the runtime `thread_local_alloc()` added in cyrius 6.4.65 instead
  of a hardcoded slot. **Co-vendoring constraint**: `lib/sigil.cyr` and `lib/thread_local.cyr` must be
  re-vendored together — a new `sigil.cyr` against a stale `thread_local.cyr` dies on an undefined
  symbol. Verified live end-to-end, not just linked: `keygen` → `register` → fingerprint round-trip
  (`02`/`03`) and the wire Ed25519 challenge/response login (`05`) bind `qix` on **both** serve models.
- **darshana 0.8.2 → 0.9.0** (`cyrius.cyml [deps.darshana]`) — additive AGNOS parity work on the
  termios/signalfd surface (`tty_open_signalfd` / `tty_close_signalfd` + `TTY_SIGMASK_*` agnos peers).
  agora consumes only `tty_sgr_buf` / `tty_sgr_reset_buf` (`src/main.cyr:1785,1791,1798,1800`), whose
  signatures are unchanged across 0.5.3 → 0.9.0. The stale manifest comment (which still described the
  0.7.0 pin) is rewritten to match.
- **Version literals → 1.6.1** — `VERSION`, plus the three inlined strings in `src/main.cyr`
  (`print_banner` :188, the connection MOTD :1799, `cmd_version` :3368). The five other `1.6.0` mentions
  in `src/` are historical provenance comments and are deliberately left alone.

### Fixed

- **Six vendored stdlib files were stale — four of them since the 1.6.0 cut** (`lib/niyama.cyr`,
  `yantra.cyr`, `pam.cyr`, `regression.cyr`, `shadow.cyr`, `ws.cyr`). `cyrius lib sync --full` reports
  the whole snapshot as copied, but `_dep_copy_file` short-circuits whenever source and destination have
  the **same byte size** — and a regenerated dist module routinely changes without changing length (the
  `# Version: 1.0.5` → `1.0.6` stamp is the canonical case). So `pam` / `regression` / `shadow` / `ws`
  were still serving **6.2.8-era** content under a 6.4.32 pin, invisibly, because `lib/` is
  `.gitignore`d. Force-refreshed against the pinned snapshot and verified byte-for-byte with a `cmp`
  sweep over all 99 files. cycc ≥ 6.4.7x's new per-lib shadow warning caught two of the six (the two
  carrying a parseable `# Version:` line) — the `cmp` sweep is the authoritative check, and is now the
  documented post-bump step.

### Added

- **Architecture note [002](docs/architecture/002-lib-sync-same-size-skip.md)** — the same-size-skip trap
  above, its detection (`cmp` sweep + the partial compiler warning), the mandatory five-step post-bump
  procedure, and why a second `lib sync` can never fix it.
- **Benchmark row for 1.6.1** in [`BENCHMARKS.md`](BENCHMARKS.md) — the first re-bench since the 0.9.2
  closeout (the 1.1.x–1.6.0 cycles were all off-hot-path; the parser is untouched since M1). Two
  dedicated runs on 6.4.78; `announce_salvo` is the one real move at −7%, reproduced across three runs.

### Deferred (found during the bump, not changed here — each earns its own cut)

- **SIGPIPE is unhandled and the poll model widened the blast radius** (`src/main.cyr` `send_buf` /
  `session_drain`). agora has no SIGPIPE disposition anywhere in `src/`, and `sock_send` is still a
  flagsless `sys_write`, so a peer that vanishes mid-write raises SIGPIPE — whose default disposition
  terminates the process. Under fork that killed one child; **under the 1.6.0 poll model it kills the
  whole 64-session server**, unauthenticated and trivially remote. cyrius **6.4.51** added the
  `signal_ignore(signum)` primitive (`lib/syscalls.cyr:98`) that fixes this — it did **not** exist at the
  6.4.32 pin, so this bump is what makes the fix available. Deferred only because it is a runtime-behavior
  change that deserves its own verification, not because it can wait.
- **Raw `syscall(N, …)` sites collide with agnos syscall numbers** — `syscall(60, exit_code)`
  (`src/main.cyr:3401`, agnos 60 = `SYS_WINSIZE`), `syscall(7, pfds, …)` in the Descent proxy
  (`src/descent.cyr:181`, agnos 7 = `SYS_OPEN`), and `enum BoardSys { SYS_MKDIR = 83 }`
  (`src/board.cyr:21`, used unguarded at `:242`). All are Linux-shaped numbers in files with no
  `#ifdef CYRIUS_TARGET_AGNOS` guard; Linux is unaffected. The `SYS_MKDIR` one also collides *by name*
  with the stdlib's agnos `SYS_MKDIR = 9`, which is why the `--agnos` build has long warned
  `duplicate symbol 'SYS_MKDIR' redefined with conflicting value (last definition wins)` (the diagnostic
  itself dates to cyrius 6.2.11). **This bump raises its severity**: the 6.4.32 agnos table had *no*
  `SYS_GPU*` entries at all, the 6.4.78 table has 22 — including `SYS_GPU_DISPATCH_F64 = 83` (its own
  comment reads "MKDIR on Linux"). So on agnos, `store_ensure` no longer dispatches a harmless unknown,
  it dispatches a GPU matmul with a path pointer. (agnos's real `mkdir` is number 9 *and* a different
  arity — `mkdir(path, pathlen)`, not `(path, mode)` — so this path never worked on agnos; it merely
  used to fail harmlessly.) `src/board.cyr`, `src/account.cyr` and `src/descent.cyr` carry zero
  `#ifdef CYRIUS_TARGET_AGNOS` guards between them, while `src/main.cyr` carries 13 — the fix is to bring
  the first three under the same discipline, or route through the stdlib wrappers. Pre-existing; the
  agnos target still builds clean.
- **agora's own arena still grows without bound under `AGORA_SERVE=poll`** — the 6.4.61 fix removes the
  *stdlib's* 40 B/poll share of the leak, not agora's. `src/` calls `alloc()` at **267 sites outside
  `test.cyr`** and calls `free` / `fl_free` **zero** times. Under fork that is sound — each connection is
  its own process and the arena dies at child exit — but the 1.6.0 poll model serves every connection
  from one long-lived process, so per-command allocations (e.g. the 512 B `PATH_MAX_BYTES` scratch in the
  board/world/chat path helpers) accumulate for the life of the server, and that is the **only** model on
  agnos. agora already declares the `freelist` module CLAUDE.md prescribes for exactly this and calls
  neither of its functions. Compounding it slightly, cyrius 6.4.51 raised `ALLOC_MAX` 256 MiB → 2 GiB,
  which lifts the single-allocation cap and weakens an accidental backstop on any path where an
  attacker-influenced length reaches `alloc()`.
- **Durable writes are not crash-safe, and the fix is now in the stdlib** — cyrius **6.4.57** added
  `file_write_atomic` (unique sibling temp → write-all → `xfsync` → atomic rename, original left intact
  on any failure) alongside `file_create_exclusive` / `file_rename` / `xfsync`; neither existed at the
  6.4.32 pin. agora's three durable-state writes still use `file_write_all`, whose `O_TRUNC` empties the
  target at open — `src/door.cyr:277` (door save), `src/door.cyr:592` (`world_write`, the shared-world
  snapshot for Ashes/Universe) and `src/chat.cyr:378` (chat transcript). A crash or short write mid-save
  truncates a player's save or a channel's log, which sits badly with CLAUDE.md's "posts are durable
  artifacts" principle. `file_create_exclusive` is also the portable replacement for the hand-rolled
  `BO_EXCL` at `src/board.cyr:686` / `src/account.cyr:417`, and would retire the now-false comment at
  `src/board.cyr:26` ("lib/io.cyr exposes O_CREAT but not O_EXCL").

## [1.6.0] — 2026-07-09 (single-process poll multiplex — concurrent players on agnos)

**agora now serves many connections at once.** The 1.5.0 agnos path was *serial* (one telnet user at
a time); this cut adds descent's **single-process poll multiplex** so multiple players connect
concurrently — the epoll-model follow-up 1.5.0 flagged. The serve model is selectable at runtime via
**`AGORA_SERVE={fork,poll}`**: Linux defaults to **fork** (classic per-connection crash-isolation),
**agnos always polls** (it has no fork). Verified end-to-end on **both** platforms (Linux poll +
agnos-via-mirshi): two clients — one deep in the Eliza door, one in the BBS — interleaved commands,
**zero cross-session bleed**; the Linux fork path is unchanged (regression-green); a 66-client flood
against the 64-slot pool greets 64 and returns "server full" to the rest without crashing.

### Added
- **`serve_poll` single-process multiplex** (`src/main.cyr`). One process serves all connections: each
  ~20 ms sweep drains pending accepts (non-blocking), then services every active slot —
  non-blocking recv → `process_rx` → non-blocking tx drain, swapping the active session's deep state
  in/out around each dispatch. agnos reads via `sys_sock_recv#49` (inverted would-block sense) + paces
  with `sys_sleep_ms`; Linux reads `O_NONBLOCK` sockets + paces with the portable `sleep_ms`.
- **Runtime serve-model switch `AGORA_SERVE={fork,poll}`** (`serve_mode_from_env`). Default fork on
  Linux, poll on agnos (no fork). `cmd_serve_on` prints the chosen model and dispatches.
- **Pre-allocated session pool** (`MAX_SESS = 64` reusable slots; `session_alloc` / `session_pool_init`
  / `session_acquire` / `session_reset` / `session_release`). Each slot is a heap struct snapshotting
  the connection's full state + a non-blocking tx queue — no per-connection alloc/free churn. Pool
  overflow returns a graceful "server full" and closes, never crashes.

### Changed
- **`handle_client` refactored into a driver over `process_rx`.** The byte-decode + line-dispatch loop
  (telnet decode, mode-aware command dispatch) is extracted verbatim into `process_rx(s, n)`; the door
  games, `session_execute`, and chat are **untouched** (ADR 0009: pure state machines). Per-session
  state that was stack-local + process-global now rides in the session slot; the deep session globals
  are swapped in/out (`sess_load` / `sess_save`) around each dispatch so those functions see exactly
  the globals they always have. Fork/serial behaviour is byte-identical.
- **`send_buf` is serve-model-aware.** In poll mode it enqueues to the active session's non-blocking tx
  queue (drained by `session_drain`); in fork mode it blocking-writes as before. All `send_str` call
  sites are unchanged.
- **Toolchain pin `6.3.32` → `6.4.32`** (`cyrius.cyml`; `lib/` re-vendored via `cyrius lib sync --full`).

### Notes
- **epoll on Linux is deferred.** The poll path uses a `sleep_ms(20)`-paced sweep on both platforms; at
  BBS/MUD scale the ~50 Hz idle wakeup is negligible CPU and the added latency is imperceptible. An
  `epoll_wait`-driven Linux loop (descent already does this) is a later optimization — and since fork
  stays the Linux default, the poll path carries no default-path cost.

## [1.5.0] — 2026-07-02 (agnos target — agora runs on AGNOS)

**agora now builds `--agnos` and serves under mirshi.** The BBS was Linux-only (fork-per-accept);
this cut makes it run on the sovereign target. Verified end-to-end: `agora_agnos serve` under mirshi
(`--net-listen-any`) accepts a telnet client and renders the banner + door/chat menu over the socket.

### Added
- **agnos serial-accept concurrency path** (`cmd_serve_on`, `src/main.cyr`). agnos has **no fork** —
  its process model is `spawn#3` (from an in-memory ELF, which can't inherit the accepted socket fd)
  + a blocking per-pid `waitpid#4`, and there is no `WNOHANG`. Under `#ifdef CYRIUS_TARGET_AGNOS` the
  accept loop drops the zombie-reaper and the `sys_fork` split, and instead serves **serially** —
  `handle_client(cfd)` to completion in-process, then loop. Linux keeps fork-per-accept
  (`#ifndef CYRIUS_TARGET_AGNOS`), unchanged. A single-process **epoll** event loop (descent's model,
  for real agnos concurrency) is the follow-up.

### Changed
- **Toolchain pin `6.2.8` → `6.3.32`** — brings the agnos target + the freelist agnos-mmap fix
  (cyrius 6.3.31) + `spawn#3`/`waitpid#4`. Host battery unchanged at **221/0**; `--agnos` builds clean.
- **darshana dep `0.7.0` → `0.8.2`** (SGR/cursor `_buf` composers; the surface agora uses is stable).
- **`[deps].stdlib` += `random`** — sigil's Ed25519 auth RNG (`random_bytes`, challenge nonces) is a
  reachable transitive leaf on 6.3.32; declaring `random` (before `sigil`) resolves it (was an
  undefined-function warning on the bump).

## [1.4.6] — 2026-06-15 (R7: table-driven door dispatch — the descriptor registry)

**One registry block per door, not eighteen edits.** This closes the last open item from the 2026-06-15 audit — finding **R7**, the per-game door-dispatch refactor ([ADR 0020](docs/adr/0020-door-descriptor-registry.md)). The ~130 `if (game == GAME_X)` branch sites that were smeared across ~16 dispatch functions in `src/main.cyr` (name, world bytes/valid/fresh/set/slot, world-begin tick, universe feed/save, render, feed, is_over, post-score, save-on-exit, and the `play` launcher's new/load/start clusters) collapse into a **single per-game descriptor record** keyed by `GAME_*` id, dispatched via `callptr` through function-address slots (`&xx_render`, `&xx_feed`, …). Adding the eleventh door is now one self-contained block in `door_registry_init` and nothing else. No behavior change — pure structural refactor; verified by the full example-smoke suite (all 13 door/universe/chat scripts green end-to-end). Also realigns the toolchain **6.2.7 → 6.2.8** (the active wrapper had advanced; the 6.2.8 stdlib snapshot already carries the 1.4.5 `sock_set_send_timeout` addition, so the bridge is now upstream). 221 tests (unchanged); 1,374,240 B → **1,375,360 B** (+1,120 B, the registry machinery net of the removed if-chains; the 6.2.7→6.2.8 codegen is byte-identical).

### Changed

- **Toolchain pin 6.2.7 → 6.2.8** (`cyrius.cyml [package].cyrius`) — closes the wrapper/manifest drift; `cyrius lib sync` refreshes `lib/` to the 6.2.8 snapshot, which already includes the additive `sock_set_send_timeout` (the 1.4.5 T2 stdlib change is now part of the stock toolchain, no longer a local bridge). Clean DCE build byte-identical at the bump (1,375,360 B), 221/221 green on 6.2.8 with no source change.
- **Door dispatch is table-driven** (`src/main.cyr`, [ADR 0020](docs/adr/0020-door-descriptor-registry.md)) — new `enum DoorDesc` + `door_registry_init` (built once per worker, guarded in `handle_client`) + `door_desc_for`. Every door-cross-cutting function (`door_game_name`, `door_world_bytes`/`_valid`/`_fresh_into`/`_set_world`, `door_universe_slot`, `door_world_begin`, `door_universe_feed`/`_save`, `door_send_frame`, `door_feed_line`, `door_is_over`, `door_post_score`, `door_save_on_exit`) and the `play` launcher's new/load/start/fp-store clusters now read the active game's descriptor and `callptr` the relevant slot; a `0` slot means "capability absent" (chatbots have no save / no `is_over`; Olympiad has no `start`). The lazy Universe turn-tick (Ashes) is generalized to a `DD_WORLD_TICK` fp + `DD_TICK_NS`. The per-game game logic is untouched — only how `main.cyr` selects it changed.

### Added

- **ADR 0020** (door descriptor registry) and **architecture note [001](docs/architecture/001-cyrius-callptr-constraints.md)** — the latter records two Cyrius constraints this work surfaced (both undocumented): a bare `callptr(...)` statement does not parse (bind the result to a var even when unused; errors cascade to a misleading line), and `0` is a valid struct-field offset so an optional offset must be stored `+1`-biased (the Ashes fp field `AE_FP` is at offset 0 — the bug the bias fixes).

## [1.4.5] — 2026-06-15 (Hardening follow-up: the 1.4.4 deferred items)

**Closes the three defense-in-depth items 1.4.4 deferred.** No new features — this finishes the hardening the audit ([`docs/audit/2026-06-15-audit.md`](docs/audit/2026-06-15-audit.md)) recorded for later: **T2** (the send-side socket timeout), **T3** (the `TERMINAL_TYPE` buffer), and **D3** (the door render-frame bound). The only remaining audit item is **R7** (the ~47-arm door-dispatch refactor), now scheduled as its own dedicated cut, **1.4.6**. 220 → **221 tests**; 1,373,424 B → **1,374,240 B**.

### Security

- **T2 — send-side socket timeout (slowloris-read)** (`src/main.cyr` `handle_client`; cyrius stdlib `lib/net.cyr`, MEDIUM). `handle_client` set `SO_RCVTIMEO` but had no send-side bound: a peer that connects and never drains its receive window fills the kernel send buffer and parks a forked worker inside a blocking `write()` — the recv timeout never fires because the worker is in `write`, not `read`. Now `sock_set_send_timeout(cfd, SEND_TIMEOUT_SECS, 0)` (60 s) is set alongside the recv timeout; an `SO_SNDTIMEO` fire returns ≤0 from `write`, which `send_buf` already treats as a short-write error (the 1.4.4 T1 fix) → the connection closes. **Companion cyrius stdlib change**: added the additive `sock_set_send_timeout` + `SO_SNDTIMEO` constants (Linux 21 / Darwin 0x1005) to `lib/net.cyr` — the send-side counterpart to the existing `sock_set_recv_timeout`, mirroring its per-target struct-timeval dispatch. Per CLAUDE.md the listener uses `lib/net.cyr` primitives, not raw syscalls, so the timeout lives in the stdlib; it lands in the next toolchain snapshot and is bridged into the pinned 6.2.7 `lib/` for this release.

### Changed

- **T3 — `TERMINAL_TYPE` subneg buffer NUL-terminated** (`src/telnet.cyr`, LOW, defense-in-depth). The RFC 1091 type buffer was exactly `TERM_TYPE_CAP` (256) bytes with no terminator, so a consumer treating it as a cstring could read past the stored length (and a shorter type following a longer one left stale tail bytes). The buffer is now `TERM_TYPE_CAP + 1` and the IS handler writes a NUL at `payload_len` (always in-bounds, ≤ index 256). The boundary was already non-overflowing (the agora analogue of CVE-2020-10188 stays defended); this is the cstring-safety hardening flagged for the v1.0 freeze.
- **D3 — door render frames are bounds-enforced** (`src/door.cyr` emit helpers + `src/main.cyr` `door_send_frame`, LOW, defense-in-depth). The per-game `*_render` functions accepted a `cap` but never checked it; every current frame fits under `DOOR_FRAME_CAP` (8192), but the invariant was unenforced against future row-count growth. The shared `emit_cstr`/`emit_int`/`emit_sgr`/`emit_crlf` helpers (the bulk of every frame, 800+ call sites) now refuse to write past a module-level `g_door_emit_cap` (dropping the fragment, returning `pos` unchanged); `door_send_frame` lowers the cap to `DOOR_FRAME_CAP` around the render, renders into a guard-banded allocation (`+ DOOR_FRAME_GUARD`) so any raw-`store8` tail lands in our own memory, and clamps the send to the cap — so a frame that outgrows 8192 truncates cleanly instead of overrunning the heap. Regression-pinned by **t221**.

## [1.4.4] — 2026-06-15 (P(-1) hardening: toolchain 6.2.7, darshana 0.7.0, security sweep)

**A hardening / refactor / security / optimization pass, no new features.** 1.4.4 realigns the toolchain (cyrius **6.2.2 → 6.2.7**) and the one git dependency (**darshana 0.5.3 → 0.7.0**, darshana's own pre-freeze hardening cut — agora is unaffected by its breaking renames since it only consumes the unchanged `tty_sgr_buf` / `tty_sgr_reset_buf` composers), then runs the full P(-1) audit ([`docs/audit/2026-06-15-audit.md`](docs/audit/2026-06-15-audit.md), four parallel line-by-line reads against the Security Hardening checklist + CVE-2020-10188 / CVE-2011-4862 parity). Six findings fixed (1 remote-DoS, 1 heap-overflow, 2 integer-overflow, 1 dead-return, plus a 7-function dead-code sweep); two LOW defense-in-depth items and one send-timeout finding recorded as deferred. No remote-compromise path found. 218 → **220 tests**; 1,371,808 B → **1,373,424 B** (net of the toolchain/darshana bump minus the dead-code removal); worldbench steady at ~42k flock'd txn/s (476 → 458 ms / 20k, within noise).

### Security

- **`send_buf` infinite busy-loop on partial-write error** (`src/main.cyr`, finding **T1**, HIGH) — a short/failed `sys_write` after a partial send left the loop spinning forever (`off < len` still true, the `done` flag only suppressed work, never terminated), pegging a CPU core. Remotely triggerable from the normal handshake by RST-ing mid-send; reachable from every ingress path (IAC drain, echo, MOTD/prompt). Fixed by `return`-ing on a short write instead of the broken flag+continue. No CVE (agora-specific I/O-layer bug), but the *class* is the same DoS surface BSD telnetd guards against.
- **`th_load_parse` heap overflow from a tampered save** (`src/handler.cyr`, finding **S1/R4**, HIGH) — the cable count was read from the save file and used as the write-loop bound with no clamp, driving `th_cable_at` past the `TH_REG_MAX*CB_SIZE` (20,480 B) allocation by attacker-controlled i64 data. The lone divergence from the project's load-clamp discipline (`ol_load_parse`/`decode_load_parse`/`jw_load_parse` already clamp). Fixed by clamping the count to `[0, TH_REG_MAX]` before the loop. Regression-pinned by **t219**.
- **Integer-overflow in the shared door parsers** (`src/door.cyr` `door_parse_int`/`door_parse_2int`, finding **D2**, MEDIUM; `src/ashes.cyr` `ash_scan_ints`, finding **D1**, MEDIUM) — unbounded `val*10+digit` accumulation let a long all-digit quantity wrap i64 negative and slip a downstream guard (`sl_buy`'s `cost = price*qty` → buy goods while cash *increases*). Fixed by pinning the accumulator at the new `DOOR_INT_MAX` (1e9) in all three parsers — well above any real figure, and `1e9*1e9 < i64 max` so no single downstream multiply can wrap. Regression-pinned by **t220**.

### Changed

- **Toolchain pin 6.2.2 → 6.2.7** (`cyrius.cyml [package].cyrius`) — closes the wrapper/manifest drift (the active `cycc` had advanced to 6.2.7). `cyrius lib sync` refreshes `lib/` to the 6.2.7 snapshot. 218/218 pre-fix tests green on 6.2.7 with no source change.
- **darshana 0.5.3 → 0.7.0** (`cyrius.cyml [deps.darshana]`) — darshana's pre-freeze hardening sweep carries breaking renames (`tty_cooked`/`tty_itoa`/`tty_clear_to_end`/`tty_apply_raw_flags`) that agora does not touch; the only consumed functions (`tty_sgr_buf` / `tty_sgr_reset_buf`) are signature-identical across the bump.
- **`door_world_commit` propagates its `world_write` result** (`src/main.cyr`, finding **R6**, LOW) — a failed shared-world snapshot write under the held lock was silently dropped; the status is now returned (lock still released on either path).

### Removed

- **7 dead functions** (finding **R3**): `ez_is_over` (`src/eliza.cyr`), `py_is_over` (`src/parry.cyr`), `qu_clampv` (`src/quest.cyr`, also a dup of `iclamp`), `rng_seed_from_clock` (`src/door.cyr`), `th_format_standing` + `th_has_mole` (`src/handler.cyr`), `paw_stock_cells` (`src/port_authority.cyr`) — all with zero non-definition references in source or tests. Binary −720 B; unreachable-fn count 1492 → 1485.

### Deferred (recorded in the audit, not changed)

- **T2 (MEDIUM) — no send-side socket timeout** (slowloris-read parks a forked worker in a blocking `sys_write`). The fix needs `SO_SNDTIMEO` in `lib/net.cyr`, which is a toolchain-synced module — a net-stdlib task, not an agora edit (CLAUDE.md: "the listener uses `lib/net.cyr` primitives, not raw syscalls").
- **T3 / D3 (LOW)** — defense-in-depth only: the `TERMINAL_TYPE` subneg buffer is correctly in-bounds today but un-terminated; the door `*_render` functions don't check their `cap` (all current frames fit under 8192). Recorded for the v1.0 freeze.
- **R7 (refactor)** — the ~47-arm per-game door dispatch in `main.cyr` is past the refactor threshold but stable and additive; a descriptor-table collapse is deferred per the no-speculative-refactor policy until the next door lands.

## [1.4.3] — 2026-06-14 (The Handler decrypt lever: decode as a cross-game mechanic)

**One engine, two doors.** The decode engine ([ADR 0018](docs/adr/0018-decode-engine.md)) is embedded inside **The Handler** as a desk-bound cryptanalysis lever ([ADR 0019](docs/adr/0019-decode-handler-lever.md)) — agora's **first cross-game mechanic reuse**. Reading a cable, the section chief can spend one dispatch point to **break its cipher**: a decode round (a Numbers relay code for paperwork, a Words codename for an intercept) whose secret is derived *deterministically from the cable itself*. Cracking it reveals the one fact the cable UI never shows — `CB_ANOM`, the hidden planted-anomaly ground truth: whether the cable's discrepancy is a **deliberate PLANT** (the mole's forged routing) or mere **clerical NOISE** (an honest agent's false positive). That cuts the false-positive fog that *is* the mole hunt — and the dispatch-point cost keeps it from being brute-forced across every cable (which would trivialize the puzzle). The reward is purely *additive* (CB_ANOM is otherwise never shown); the visible metadata, the discrepancy verdict, and the **save format** are all untouched (the lever's state is runtime-only). 216 → **218 tests**; 1,367,728 B → **1,371,808 B**.

### Added

- **The Handler decrypt lever** (`src/handler.cyr`, the `[D]` action on the cable-read screen) — a new `HSCR_DECRYPT` screen hosts a decode round (rendered + fed by the decode engine verbatim: `decode_new` → `decode_set_numbers`/`_words`, the secret pinned to the cable's derivation; `decode_feed` while decrypting; resolved on `decode_is_over`). A crack marks the cable and surfaces the plant/noise verdict; a burn or a quit costs the dispatch point with no reveal. Three runtime-only `TH` fields (`TH_DECODE` / `TH_CRACKED` per-session bitset / `TH_DECRI`) — **no save-format change**. Wire smoke `docs/examples/22-handler-decrypt.sh`.
- **`th_cipher_for_cable`** ([ADR 0019](docs/adr/0019-decode-handler-lever.md)) — the pure, deterministic `(variant, secret)` derivation from a cable's own fields (`CB_NR`/`CB_AGENT`/`CB_DAY`/`CB_KIND`): intercepts → a Words codename, paperwork → a Numbers relay code; the same cable always presents the same crackable code (replayable, a fair fixed puzzle). Unit-pinned t217 (determinism + intercept→dictionary-word + numbers-in-range), t218 (the full begin → win → cracked → return flow, and the quit → uncracked path).

### Changed

- **The cable-read screen** gains a `CRYPTANALYSIS:` verdict line once a cable is cracked (`routing DELIBERATELY FORGED -- a plant.` / `clerical noise -- no plant here.`) and a `[D] break the cipher (1 dispatch pt)` prompt before; the `HSCR_READ` action bar adds `[D]ecrypt`. `th_feed` gains the `HSCR_DECRYPT` arm; `th_render` early-returns the decode frame during a crack. The dispatch-point cost reuses the existing `TH_POINTS` economy (the same one that gates Move/Extract/Fund).

## [1.4.2] — 2026-06-14 (Decode: the Words / Wordle variant)

**Words builds on the decode mechanics — literally.** The Words (Wordle) variant is added to the *same* `play decode` door on the *same* `decode_classify` engine ([ADR 0018](docs/adr/0018-decode-engine.md)) — a second skin, not a new game. `play decode` now opens on a `[n]/[w]` select screen; pick Words and you crack a hidden 5-letter word in six guesses, the feedback rendered per-letter (green = right spot, yellow = in the word, gray = absent) from the exact-same per-position scorer that drives Numbers' exact/present pegs. The dictionary is a curated **532-word** 5-letter table in its own data module (`src/decode_words.cyr`, a 5-byte-stride blob) that doubles as the answer pool and the valid-guess set — a deliberate BBS-scale simplification (compile-time, pure, unit-testable; no runtime file I/O). 213 → **216 tests**; 1,358,848 B → **1,367,728 B** (the word table + Words paths).

### Added

- **Decode / Words** (the `[w]` variant of `play decode`) — Wordle over telnet: a 5-letter word, six guesses, per-letter green/yellow/gray feedback (`decode_emit_word_row`); a guess must be a real dictionary word (`decode_parse_words` → `decode_word_index`, rejecting wrong-length and not-in-list). A Words crack carries a +200 difficulty bonus on the `scores decode` board (26-letter alphabet, only six tries). Solo save round-trips the variant (the `DECO1` format already carried `variant` + `wordid`). Unit-pinned t214 (the classifier over letters — the SASSY/SWISS duplicate trap → 2 exact / 1 present), t215 (the dictionary + parser: membership, lowercasing, every reject path), t216 (the select → Words → crack-with-bonus flow + the lone-`q` quit test).
- **The 5-letter dictionary** (`src/decode_words.cyr`) — 532 curated, deduplicated, validated words as one 5-byte-stride blob; `decode_word(i)` / `decode_word_count()`. Its own compile-time data module so `src/decode.cyr` (the engine) stays clean and the Words variant stays exercisable from the unit harness.
- **The `[n]/[w]` select screen** (`DSCR_SELECT`) — a fresh `play decode` opens here; `n`/`w` pick the variant and mint the secret. A loaded solo save skips straight to its in-progress board. Quit detection is a **lone-`q`** test (`decode_is_lone_q`), not "first char is q", so Words guesses like QUEEN / QUICK / QUIET / QUITE are not misread as quit. Smoke `docs/examples/21-decode.sh` extended to drive both variants.

## [1.4.1] — 2026-06-14 (Decode: the code-breaking door — Numbers)

**Crack the code.** Decode ([ADR 0018](docs/adr/0018-decode-engine.md)) is a single `play decode` door whose game is "crack the hidden code from feedback". It lands agora's signature one-engine/many-variants pattern a **fourth** time — door PRNG → wager tables ([ADR 0013](docs/adr/0013-wagering-module-rng-fairness.md)) → `compete()` events ([ADR 0016](docs/adr/0016-olympiad-competition-primitive.md)) → **DECODE**. The pure heart is `decode_classify`: the symbol-agnostic, duplicate-correct, per-position exact/present scorer — the Mastermind black/white pegs and the Wordle green/yellow/gray are the *same* computation, and getting the duplicate-handling right exactly once is the whole point. 1.4.1 ships the **Numbers** variant (classic Mastermind: a 4-long code of colors 1..6, ten guesses, feedback as exact/present counts); the **Words** (Wordle) variant lands in 1.4.2 on the same engine, and the Handler decrypt lever reuses it in 1.4.3. Solo/practice only (no shared world; universe coerces to solo). The secret is minted once from the seeded door PRNG and persisted in the solo save — the same hidden-state trust model as The Handler's mole.

This release also folds in the **toolchain migration 6.1.23 → 6.2.2** (the active compiler had drifted ahead of the pin; 6.2.2 reorganized the stdlib). 208 → **213 tests**; 880,288 B → **1,358,848 B** (the jump is the broader 6.2.2 stdlib surface, not Decode).

### Added

- **Decode / Numbers** (`src/decode.cyr`, `play decode`) — classic Mastermind over telnet: the board renders the code rules + the guess history with `[N exact, M present]` feedback per row, a guesses-left countdown, and a crack/burn banner; `q` quits. Solo saves progress (header `DECO1`; config + seed + secret + guess history, marks recomputed on load via `decode_classify` so feedback is never stale); a finished run posts to the `scores decode` leaderboard (`Cryptanalyst` / `Codebreaker` / `Cipher Clerk` / `Cadet`). Wired through the `MODE_DOOR` dispatch exactly like the Olympiad. Wire smoke `docs/examples/21-decode.sh`.
- **The `decode_classify` primitive** ([ADR 0018](docs/adr/0018-decode-engine.md)) — the injected, unit-pinned test seam (in the `wager_pick` / `ol_pick_weighted` lineage): two passes over a 256-entry symbol tally, exact-first then present-while-tally-lasts, over raw bytes so digits and letters share it verbatim. Unit-pinned t209 (the duplicate traps: `1223` vs `2242` → 1 exact/1 present, a full permutation → 0/4, repeated-symbol rows), plus t210 (the Numbers parser — spaced + packed digits, every reject path), t211 (new + win + score), t212 (exhaust → burn → score 0), t213 (save/load round-trip with marks recomputed).

### Changed

- **Toolchain pin 6.1.23 → 6.2.2** (`cyrius.cyml [package].cyrius`) — realigns the manifest with the active compiler. 6.2.2 reorganized the stdlib: `bigint` is no longer a standalone module (folded into the crypto surface), so the `[deps].stdlib` list drops `bigint` and adds `bayan` (u256), `thread_local`, `keccak`, `hashmap`, `thread` to keep sigil's Ed25519/SHA path fully linked (an unlinked `u256_*` previously SIGILL'd the fingerprint tests). `cyrius lib sync` refreshes `lib/` to the 6.2.2 snapshot. 208/208 pre-Decode tests green on 6.2.2.
- **`help`** and the `play` / `scores` usage strings gain `decode`; `src/main.cyr` door dispatch gains the `GAME_DECODE` (=10) arm across `door_game_name` / `door_send_frame` / `door_feed_line` / `door_is_over` / `door_post_score` / `door_save_on_exit`.

## [1.4.0] — 2026-06-10 (Descent link: the BBS becomes the front door to the MUD)

**Step through the portal.** The Descent link ([ADR 0017](docs/adr/0017-descent-link-gateway.md)) bridges a logged-in agora citizen into the sibling **Yeoman's Descent** MUD (`../cyrius-yeomans-descent`) over the shared telnet substrate — the BBS becomes the front door to the MUD. agora stays the BBS: this is a *gateway*, not an absorption of MUD semantics. The 1.3.7 war-game retired the shared-state-between-callers concurrency risk on agora's own framework on purpose, exactly so those lessons fed this link. **Model**: a transparent TCP byte-proxy — agora dials the operator-configured endpoint and shuttles bytes both ways via a `poll(2)`-multiplexed loop until either side closes; the MUD owns its world loop, its own telnet negotiation, and its own login, all of which flow through to the client verbatim. **Identity hand-off is deferred** ([ADR 0017](docs/adr/0017-descent-link-gateway.md) § Decision): the MUD has no external-identity path, so a true sigil hand-off needs an MUD-side protocol (a follow-on bite); for now the citizen re-authenticates inside the MUD. Toolchain pin **6.1.17 → 6.1.23**. No new dependencies. 206 → **208 tests**; 874,168 B → **880,288 B**.

### Added

- **Descent gateway** (`src/descent.cyr`, `descent` verb) — login-gated like `chat`. Reads an operator-set endpoint from `<store>/.descent` (`host:port`, or a bare port → `127.0.0.1` for a co-located MUD), dials it with a bounded non-blocking connect (`net_connect_nb`, 4 s), and runs a transparent `poll`-multiplexed byte-shuttle between the client and the MUD until either side closes (or a 30-minute pure-silence slowloris bound trips). Absent/empty config → "No Descent linked."; a misconfigured endpoint or an unreachable MUD → a soft message; every failure path leaves the citizen at the BBS prompt. The endpoint is **operator config only**, never client-supplied — no SSRF surface. Wire smoke `docs/examples/20-descent.sh` (builds + starts the MUD, logs into agora, and proves the MUD's own login banner proxies through).
- **Pure endpoint parser** (`descent_parse_endpoint` / `descent_parse_ipv4` / `descent_dec`) split from the wired proxy per the "pure parsing is testable; socket I/O is wired" principle. Unit-pinned t207 (decimal + IPv4 packing, fail-closed on junk) + t208 (bare-port → loopback, explicit host:port, whitespace/CRLF trim, and every reject path: empty / blank / non-numeric / empty-host / short-IP / port 0 / port > 65535). A misread endpoint must fail closed, never silently dial the wrong host.

### Changed

- **Toolchain pin 6.1.17 → 6.1.23** (`cyrius.cyml [package].cyrius`) — closes the wrapper/manifest drift. Clean DCE build byte-identical at the bump (874,168 B before the Descent module), 206/206 green on 6.1.23 with no source change.
- **`help`** gains a `descent` line; `src/main.cyr` session dispatch gains the `descent` verb (login-gated, calls `descent_run`, returns to `MODE_COMMAND`).

## [1.3.7] — 2026-06-09 (Ashes of Empire: the async shared-world war-game — the MUD on-ramp)

**The provinces of a fallen empire lie in ashes — seize them.** Ashes of Empire ([ADR 0014](docs/adr/0014-async-shared-world-strategy.md)) is agora's first genuinely *shared-world* game: logged-in citizens act on one common map, raise armies, forge and betray alliances, and grind the map between them turn by turn. It is sequenced last of the 1.3.x door arc and immediately before the 1.4.0 Descent/MUD link **on purpose** — it is the deliberate rehearsal of shared-state mutation between concurrent callers, the one thing agora's architecture had never exercised. It runs on the proven 1.2.0 `flock`'d world-transaction framework ([ADR 0010](docs/adr/0010-persistent-universe.md)) with turn-batch combat resolved **lazily on the next caller's entry** (mirroring QUEST's `qu_day_tick`, no daemon) — so building it retires the concurrency risk the MUD is about to take on for real. The batch-resolution combat transform stays a pure, unit-testable function — the most complex one in the door tree. No new dependencies. 197 → **206 tests**; 841,824 B → **874,168 B**.

### Added

- **Ashes of Empire** (`src/ashes.cyr`, `play ashes`) — an asynchronous shared-world strategy door, login-gated (a persistent territory is a persistent actor) and inherently universe-mode. **The map**: twelve provinces of a fallen empire form a ring (you may march only to a neighbour); terrain (plains / hills / forest / fortress) is regenerated deterministically from the world seed and confers a defender bonus, so only the mutable owner/army bits live in the snapshot (PA's discipline). **Founding**: a new (or wiped-out) player seizes a free neutral province with a starting garrison. **Orders**: `march <src> <dst> <n>` queues into the shared snapshot — one order type, three intents (move into your own/empty land, attack a rival, or reinforce), decided by the destination's owner at resolution. **Diplomacy**: `ally <prov>` / `break <prov>` against the province's holder — propose, reciprocate-to-seal, betray. **Resolution**: a daily turn window, resolved lazily on the next caller's entry; the async "while you were away, N turns resolved" notice surfaces what changed. Wire smokes `docs/examples/18-ashes.sh` + `19-ashes-concurrency.sh`.
- **The batch-resolution combat transform** ([ADR 0014](docs/adr/0014-async-shared-world-strategy.md)) — resolved simultaneously from the window-start snapshot, so the outcome is **independent of order-processing sequence** (the property that makes concurrent multi-player resolution correct, unit-tested t203). Departures debit their source (over-commit capped in queue order); each destination is a pure contest over the multiset of forces there (incumbent army + terrain power vs. attacker armies), the strongest power taking the province and losing bodies equal to the runner-up's — a winner ground below zero leaves the province as neutral *ash*. Unit-tested t202.
- **Alliances** ([ADR 0014](docs/adr/0014-async-shared-world-strategy.md)) — a pact edge-list in the snapshot (propose → reciprocate-to-ally → break). Folded into the resolver: a defender's allies *reinforce* instead of attacking, and allied attackers merge into coalitions (union-find) that fight as one bloc, the largest member taking a won province. **Betrayal needs no special code** — breaking a pact re-evaluates a queued march as an attack at the next resolution. Unit-tested t205 (diplomacy verbs) + t206 (cooperative combat + the betrayal contrast).
- **The lazy turn-window helper** (`ashw_window_tick`, mirroring QUEST's `qu_day_tick`) — the entering caller, already holding the world lock, resolves any overdue daily windows from `clock_epoch_ns`; a backward clock or a restart self-heals rather than freezing. Unit-tested t200.
- **`docs/examples/19-ashes-concurrency.sh`** — N players race a release barrier into `play ashes` at once; the result must be N **distinct** foundings owned in the one shared world (founding + order-push run inside the `flock`'d transaction). Proves the Ashes-specific shared-state path is lossless under real fork-per-accept concurrency, complementing the generic framework smoke `08-world-concurrency.sh`.

### Changed

- **`src/door.cyr`** gains `GAME_ASHES`; the `play` + `scores` dispatch, the world-transaction helpers (`door_world_bytes` / `door_world_valid` / `door_world_fresh_into` / `door_set_world` / `door_universe_slot` / `door_universe_feed` / `door_universe_save` / `door_send_frame` / `door_is_over` / `door_post_score`) in `main.cyr` all learn the new game. The lazy resolve-on-entry hook lives in `door_world_begin` (Ashes ticks its overdue turns on every world-open). Connect banner + help advertise the new door.
- **[ADR 0014](docs/adr/0014-async-shared-world-strategy.md)** flipped Proposed → **Accepted**.
- **Toolchain pin 6.1.15 → 6.1.17** (`cyrius.cyml`). The local wrapper advanced twice mid-cut (6.1.15 → 6.1.16 → 6.1.17); the suite + clean DCE build stay green on 6.1.17, no source change required.

## [1.3.6] — 2026-06-09 (Olympiad: the games-owner sim + the competition primitive)

**You own the stable; the Games are yours to win.** Olympiad ([ADR 0016](docs/adr/0016-olympiad-competition-primitive.md)) is agora's biggest door yet and the flagship of the wager module — a Greco-Roman games empire where you are the **owner** (a *dominus* / circus‑faction boss), not the athlete. You field a chariot team, **train it or rest it** across a rationed daily economy, and climb a twelve‑meet ladder from a provincial dirt track to the Circus Maximus for the **tethrippon crown** — wagering on every race along the way. The keystone is a new shared abstraction: every event is the same `compete()` primitive — a **form‑weighted kernel‑CSPRNG draw resolves the contest AND the same weights price the book**. Training raises your team's weight, which both improves your real chance of winning and shortens your odds at the book; one number, two consequences. This is agora's signature "one abstraction, many skins" a third time (door PRNG → wager → **competition**), so gladiators / athletics / boat crews become thin event descriptors later, not new games. No new dependencies. 196 → **197 tests**; 812,528 B → **841,824 B**.

### Added

- **Olympiad** (`src/olympiad.cyr`, `play olympiad [practice|solo]`) — a games‑owner management door on QUEST's daily‑turn skeleton. **The owner/stable**: you hold denarii, a per‑day action ration, and a founding Blue chariot team (Speed / Stamina / Handling / Nerve + condition). **The economy**: spend each day's actions to **train** (a stat up, at a condition cost — fatigue, with diminishing returns past two‑thirds of the cap) or **rest** (condition back) — the strategic "train or not" core; over‑training without rest sends your team to the gates spent, and the odds show it. **The race** (the Hippodrome): your team plus a generated field of rival factions scaled by meet, rendered with form bars and live odds; `[Enter]` looses the gates. **The book**: type `<lane> <stake>` to wager on any lane (your team or a rival) at the shown odds — `compete()` resolves the finishing order off the kernel CSPRNG and `wager.cyr` settles the bet, independent of your own placing. **The ladder**: win a meet to climb; purses scale with prestige (100 denarii at Veii → 1,200 at the Circus); winning the twelfth meet takes the **tethrippon crown** and ends the campaign. Solo‑saveable (the whole stable persists, header `OLYM1`) + a `scores olympiad` leaderboard (crowns dominate, denarii break ties). Unit‑tested t189–t197; smoke `docs/examples/17-olympiad.sh`.
- **The `compete()` primitive** ([ADR 0016](docs/adr/0016-olympiad-competition-primitive.md)) — event‑agnostic competition resolution: `ol_pick_weighted` (the pure weight→entrant seam, with a taken‑mask), `ol_compete_winner` (one CSPRNG draw), and `ol_compete_order` (a sequential weighted draw for the full finishing order — place/show). It only reads *forms*, so every future event is a field‑builder + a form function + flavour. The pure/impure split mirrors `wager.cyr` (pure mapping vs. the one `wager_uniform_csprng` read), exercised for distribution by t192's 600 live draws.
- **`wager_payout`** (`src/wager.cyr`) — the fractional (pari‑mutuel) profit helper: odds as a num:den profit (3:2, a 5:1 longshot, a 4‑to‑5 favourite) with the staged‑overflow‑safe edge haircut. A favourite pays *less* than 1× profit, which the casino's integer multipliers couldn't express. The racetrack companion to the table‑based `wager_resolve`. Unit‑tested t195.
- **The fairness split, at the event level** ([ADR 0016](docs/adr/0016-olympiad-competition-primitive.md) extends [ADR 0013](docs/adr/0013-wagering-module-rng-fairness.md)) — the rival **field** is generated from the seeded `door.cyr` PRNG (replayable; a save replays the season's opponents), but the race **winner** is the kernel CSPRNG (non‑replayable). The one thing money rides on is the one thing a player cannot reconstruct from a save.

### Changed

- **`src/door.cyr`** gains `GAME_OLYMPIAD` + `door_parse_2int` was already shared at 1.3.5; `door_game_name` / the `play` + `scores` dispatch / the solo save‑load + save‑on‑exit paths in `main.cyr` all learn the new game. Connect banner + MOTD advertise the Olympiad.
- Toolchain pin unchanged at **6.1.15** (cycc held steady across this cut; no realign needed).

## [1.3.5] — 2026-06-08 (Casino integrations: the wager module earns its keep)

**One module, three tables.** 1.3.4 built `src/wager.cyr` (the `bet → draw → resolve → settle` primitive) but left it unreachable — built ahead of its consumers. 1.3.5 embeds that *same* module as flavour-with-stakes across the three existing doors, so this is the **first user-reachable wager surface**: a cantina Dabo Wheel in **Port Authority**, back-alley Bones in **Smuggler's Ledger**, and a tavern Card Table in **QUEST**. No fifth door to maintain — three skins over one reviewed primitive, each a different table shape (a weighted 3-light wheel, an even-money binary, a 4-suit uniform draw) drawing from the kernel CSPRNG. Each table debits/credits only the game's existing gold field, so no save-format changes. No new dependencies. 185 → **188 tests**; 801,288 B → **812,528 B** (the wager module is now reachable code, not DCE-NOPed).

### Added

- **Port Authority — the cantina Dabo Wheel** (`PSCR_GAMBLE`, key `[C]`). Three lights on a weighted draw: Green 3/6 → 1×, Amber 2/6 → 2×, Red 1/6 → 5× (fair odds, then a 3% house edge). One bet per line, `<stake> <1-3>`; min 5 credits, no ceiling. Debits/credits `PA_CREDITS`.
- **Smuggler's Ledger — back-alley Bones** (`SCR_DICE`, key `[D]`). An even-money Low/High call (two equal outcomes, 1× each) with a steeper 6%-edge haircut — the fixer's bones run hot. `<stake> <1-2>`; min 5 cash. Debits/credits `SL_CASH`.
- **QUEST — the tavern Card Table** (`QSCR_CARDS`, town key `[C]`). "Pick the suit", a 4-outcome uniform draw paying 3:1 with a 4% edge. `<stake> <1-4>` (Hearts/Diamonds/Clubs/Spades); min 5 gold. Bets `QU_GOLD` (gold on hand — the muggable purse, never the banked vault, thematically right).
- **`door_parse_2int`** (`src/door.cyr`) — the shared `<stake> <choice>` bet-line parser (first int returned, second written out, `(0-1)` for an absent field). Unit-tested t185.
- **`wager_reason`** (`src/wager.cyr`) — maps a `WAGER_E_*` reject code to a shared human-readable string, so every table surfaces the same vocabulary.
- **Per-game table builders** (`pa_dabo_table` / `sl_dice_table` / `qu_cards_table`) — each game's payout table extracted into a named function so its tuning (weights / multipliers / edge / minimum) is unit-tested against accidental change (t186–t188 pin the edge-floored payouts: a 100-credit Red win pays 485, an even-money bones win pays 94, a suit hit pays 288).
- **`docs/examples/16-casino.sh`** — drives all three tables over telnet (cantina + dice + cards), asserting each renders and resolves a bet. The first wager wire-smoke (1.3.4 had no user surface).

### Changed

- **Toolchain pin 6.1.14 → 6.1.15** (`cyrius.cyml`). The local wrapper advanced again mid-cut; suite + clean DCE build stay green, no source change required.
- **`src/wager.cyr` include moved** ahead of the game modules (right after `door.cyr`) in both `main.cyr` and `test.cyr`, since the games now call into it.
- Connect banner + MOTD now advertise the casino tables.
- **ADR 0013** gains a 1.3.5 implementation note recording the three integrations.

## [1.3.4] — 2026-06-08 (Wager: the shared casino primitive)

**A casino is a mechanic, not a door.** Strip the skin off roulette, craps, a card hand, or a fighter bout and the loop is identical — **bet → draw → resolve → settle** — so agora builds it **once**, as a shared module ([ADR 0013](docs/adr/0013-wagering-module-rng-fairness.md)), the same "one abstraction under many games" pattern the door PRNG and the world-transaction framework already use. `src/wager.cyr` owns bet validation, per-game payout tables, an explicit per-table house edge, the entropy draw, and settlement. This cut ships the **primitive ahead of its consumers**: nothing calls it yet (DCE NOPs it in the binary), exactly as the 1.2.0 world-transaction framework was built before the games used it. The **1.3.5** integrations wire it into Port Authority / Smuggler / QUEST; the **1.3.6** training-sim flagships it (bet on your own fighter). No new dependencies — the entropy source is a syscall agora already has. 178 → **184 tests**; 797,640 B → **801,288 B**.

### Added

- **Wager module** (`src/wager.cyr`) — the content-free wagering loop as a pure-majority module. **Bet validation** (`wager_validate`) is a pure transform → `WAGER_OK` or a specific reason code (stake ≤ 0 / insufficient funds / below table min / above table max / illegal choice); on OK it structurally guarantees `0 < stake ≤ balance`, which is what makes the no-negative-balance invariant load-bearing rather than hoped-for. **Payout tables** (`wager_table_init` + `wager_weight_total`) are pure i64-slot data: per-outcome relative draw weights + gross profit multipliers, plus stake bounds and an **explicit house edge in basis points** — a named field, not a magic constant (ADR 0013). **Resolve + settle** (`wager_resolve` / `wager_settle`) are pure: the signed gold delta for a bet given the drawn outcome (edge applied as a floored haircut on gross winnings, staged divide-before-multiply so the intermediate never overflows), then a clamp-and-apply with no path below zero. Unit-tested t179–t184.
- **The fairness split** ([ADR 0013](docs/adr/0013-wagering-module-rng-fairness.md), the core decision) — the games deliberately use `door.cyr`'s **seeded, replayable** xorshift (a save stores its seed, a test pins the stream). A casino inverts that: here there *is* an adversary, so a reconstructable draw makes the house edge fiction. The wager draw therefore pulls from the **kernel CSPRNG** (`wager_uniform_csprng` → `sys_getrandom(buf, 8, 0)`), fresh per draw, never seeded, never stored — the one deliberately non-deterministic point in the whole games subsystem. The module never calls `rng_*`; the games' determinism is untouched. A short/failed entropy read returns the `(0-1)` sentinel so the caller **refuses the bet and never settles on a bad draw**.
- **The pure/impure seam** — the ONLY non-deterministic point is the entropy read, so the weight→outcome mapping is split out as the pure `wager_pick` (the injected test seam: tests pass a fixed `r` for a known outcome) from `wager_uniform_csprng` (the impure read), composed by `wager_draw_csprng`. The impure path is exercised only for **distribution** (t183: 3000 live kernel draws assert in-range + termination + full outcome coverage, never an exact value); everything else is pinned to exact values (t179–t182, t184). Same shape as ADR 0009's pure-render / wired-I/O split and ADR 0010's pure-transform / wired-lock split.

### Changed

- **Toolchain pin 6.1.12 → 6.1.14** (`cyrius.cyml`). The local toolchain advanced (twice, mid-cut) to 6.1.14; suite + crypto stay green, no source change required (same realign precedent as 1.3.3's 6.1.10 → 6.1.12). No new user-facing surface this cut, so the connect banner / MOTD feature lists are unchanged (the casino becomes visible at 1.3.5) — only the version stamp moved.
- **ADR 0013 Proposed → Accepted** — the shared-module decision and the wager-RNG fairness split are realized in `src/wager.cyr` as specified.

### Fixed

- Pre-release adversarial review (multi-agent, 5 dimensions, each finding independently verified — **11 confirmed, 1 refuted; no critical/high**) hardened the real-stakes accounting before the cut, the harder review ADR 0013 § Consequences calls for: **(medium)** the edge haircut formed `gross * kept` (× up to 10000) *before* dividing, overflowing i64 on a large win against an uncapped (`WT_MAX ≤ 0`) table and — masked by the settle floor-clamp — silently paying 0; now staged divide-before-multiply (identical floored result, no `×10000` intermediate) plus a `stake*mult` wrap guard that nets a push rather than garbage gold. **(low)** `wager_resolve` had no self-guards, so a future consumer that passed the CSPRNG-refusal sentinel `(0-1)` would *debit* the player (settle a bad draw) and an out-of-range `choice` would index `mults[]` out of bounds — now `outcome < 0` nets zero (a push) and an illegal `choice` loses before any deref, making the function self-contained. **(low)** a negative `edge_bps` (a sign-typo in a hand-built table) made the house overpay above the gross multiplier — now `kept` is clamped high-side to `WAGER_EDGE_DENOM`. **(low)** `wager_settle` clamped only the floor, so a winning delta that wrapped i64 would zero a rich balance — now a positive wrap leaves the balance unchanged. **(medium)** `wager_pick`'s documented "zero-total → outcome 0" contract actually returned the *last* index (the jackpot slot) for multi-outcome tables, and the test only covered `nout == 1` where the two coincide — now a genuinely degenerate table resolves to outcome 0 (the safe slot) while an out-of-range `r` residual returns `n-1`, both pinned. Regression tests t180 (multi-outcome zero-total + residual), t181 (negative-edge clamp + seam guards), t182 (settle overflow), t184 (degenerate draw determinism) added. The one **refuted** finding (CSPRNG bad-read path "unacknowledged") was correctly rejected — the t183 comment already documents it.

## [1.3.3] — 2026-06-08 (Jabberwacky: the first corpus-learning bot)

**The bots start to learn.** Jabberwacky (Rollo Carpenter, 1988→) joins as agora's third chatbot — and the first of a different **engine kind** ([ADR 0012](docs/adr/0012-chatbot-framework.md) § Engine taxonomy, designed in [ADR 0015](docs/adr/0015-jabberwacky-corpus-learning.md)). Eliza decomposes-and-reassembles; PARRY models affect; Jabberwacky neither — it **remembers what people say and replays it**. Each turn it finds the stored stimulus most similar to your line (word-overlap retrieval) and answers with the human reply that once followed, then **learns** the transition (your previous line → your current line) so it can replay your words later. It gets stranger the more it is talked to. Reachable three ways: a `play jabberwacky` door (practice; learns in-session, ephemeral), a `play jabberwacky solo` door (login-gated; the learned layer **persists per-user across sessions** — agora's first persistent-state bot), and a private `/jabberwacky` chat side-channel. No new dependencies. 166 → **178 tests**; 782,064 B → **797,640 B**.

### Added

- **Jabberwacky** (`src/jabberwacky.cyr`) — a corpus-learning chatbot as a pure ADR-0009 door module. **Engine**: a `(stimulus, response)` corpus with `jw_overlap` word-overlap scoring (distinct content words; 1-char + stop-words skipped), `jw_best_match` retrieval (ties go to the **latest** pair so a freshly-learned answer beats an older seed), and a learn-the-transition rule (`jw_respond` answers first, then records previous→current, so a turn never matches the pair it is recording). **Corpus**: a baked-in **seed** layer (~24 pairs of glib house personality, shared, never persisted) + a **learned ring** capped at 64 pairs (oldest learned evicts; seeds never do). Reuses ELIZA's text primitives (`ez_normalize` / `ez_word_end` / `ez_word_is` / `ez_puts` / `ez_is_quit`) but **none** of its reassembly engine — it shares the chassis, not the engine ([ADR 0012](docs/adr/0012-chatbot-framework.md)). Unit-tested t167–t178; all three wire surfaces + cross-session learning proven by `15-jabberwacky.sh`.
- **Hybrid per-user persistence** ([ADR 0015](docs/adr/0015-jabberwacky-corpus-learning.md)) — unlike the stateless Eliza/PARRY (forced practice-only), Jabberwacky takes the QUEST stateful-door shape. `play jabberwacky solo` loads + saves **only the learned layer** under `<store>/.users/<fp16>/games/jabberwacky.sav` via the existing door SOLO-save path (`jw_save_format` / `jw_load_parse`; `jw_is_over ≡ 0` keeps it on the checkpoint branch, never the score branch). The seed is re-baked on load, never serialized. There is deliberately **no global shared corpus** — per-user isolation removes the cross-user poisoning / privacy / escape-injection surface that ADR 0012 flagged as the defining new risk of a learning bot; stored responses are ASCII-sanitised (dropping ESC / TAB / control / high bytes) so nothing un-printable can replay into a terminal.
- **Couch third bot** — the private chat side-channel now hosts `g_chat_bot == 3` (`/jabberwacky`, "the mimic") alongside `/eliza` and `/parry`, ephemeral and seed-only. [ADR 0015](docs/adr/0015-jabberwacky-corpus-learning.md) records the engine, the hybrid persistence, and the poisoning/privacy containment.

### Changed

- **Toolchain pin 6.1.10 → 6.1.12** (`cyrius.cyml`). The local toolchain advanced; suite + crypto stay green, no source change required (same realign precedent as 1.3.2's 6.1.9 → 6.1.10).
- Connect banner + MOTD feature lists now advertise Jabberwacky alongside Eliza/PARRY + QUEST.

### Fixed

- Pre-release adversarial review (multi-agent, 5 dimensions, each finding independently verified — 11 confirmed, 10 refuted; no critical/high) caught and fixed real defects before the cut: **(medium)** `jw_overlap` double-counted a repeated query word ("no no no"), inflating a single-match candidate's score and overriding the documented recency tie-break — now counts each distinct content word once; **(low)** `jw_load_parse` tab-scan had no LF stop, so a mid-file tab-less record could bleed across the newline and swallow the next pair — now stops on LF and skips the malformed record; **(low)** `jw_save_format` wrote the full learned count even if the cap-guard truncated the record loop — now pre-counts records that fit by actual size and writes an honest header; **(low)** a stored stimulus truncated mid-word at the 160-byte slot could never match its own whole-word query — now backs up to a whole-word boundary; **(low)** `jw_start` didn't reset the conversation cursor, so re-entering the `/jabberwacky` couch could learn a spurious cross-session pair — now clears it; **(low)** the ubiquitous pronouns `you`/`your` weren't stop-listed, so a bare "do you think so" drove the tie-break to an inapt goodbye seed — now stop-listed (greetings still route correctly); **(nit)** `jw_load_parse` iterated to the buffer length on a crafted oversized header — now capped at the learned-ring capacity. Regression tests t169 (distinct), t176 (load-time sanitisation), t177 (couch re-entry), t178 (malformed record) added.

## [1.3.2] — 2026-06-08 (QUEST: a Legend of the Red Dragon homage door)

**The BBS gets an RPG.** QUEST — "Quest of the Undying Emerald Sovereign Throne" — is a homage to **Legend of the Red Dragon** (Seth Robinson, 1989), the definitive BBS RPG: re-themed cast, original prose. Its load-bearing mechanic is LORD's **daily turn rationing** — a fixed number of forest fights per real day, so "see you tomorrow" is built into the loop. Underneath the fantasy climb runs a buried structure that is never labelled: the twelve level-masters trace the alchemical **Great Work** in four acts of three (Nigredo → Albedo → Citrinitas → Rubedo), and four **Emerald fragments** assemble into the Tablet — beat the Level-12 Sovereign and "as above, so below" surfaces exactly once. No new dependencies. 160 → **166 tests**; 752,240 B → **782,064 B**.

### Added

- **QUEST** (`src/quest.cyr`) — a full pure-module door RPG in the ADR 0009 shape (town hub + forest grind + turn-based combat + 12 masters + endgame), solo-saveable (`QUST1` positional save) with a cross-game leaderboard. **Town hub**: Forest, Healer, Bank, Inn, reflection, save+quit. **Daily-rationed forest** (wall-clock reset, 15 fights/day) → scaling beasts → the named **level-master** gating each advance. **The twelve masters** across the four Great-Work acts, palette-tracked (grey → white → gold → red; the Sovereign emerald). **The Emerald-fragment spine** — a fragment at masters L3 / 6 / 9 / 12, the tablet's look changing as it assembles (dark → washed → gilded → whole). **Town services**: the Healer (pay-to-mend), the Bank (10%/day interest + a real **mugger risk** on carrying gold — the bank's whole point), the Inn (a flirt-to-romance NPC). **Ascension endgame** — beat the Level-12 Undying Emerald Sovereign, the tablet completes, and you take the Throne. Reachable via `play quest [practice|solo]`; finished runs post to `scores quest`. Async-PvP / shared-world Universe is a roadmapped follow-on; this cut is the single-player climb. Unit-tested t161–t166; smoke `14-quest.sh`.

### Changed

- **Toolchain pin 6.1.9 → 6.1.10** (`cyrius.cyml`). Suite + crypto stay green; no source change required.

### Fixed

- Pre-release adversarial review (multi-agent, each finding verified) caught three real defects before the cut: **(critical)** `play quest universe` reached the unwired Universe branch, left `g_door_state` NULL, and segfaulted the forked worker — QUEST is now coerced to its supported solo mode (mirroring how the chatbots are coerced to practice); **(high)** the daily ration reset used the *monotonic* clock against a persisted day index, so a server reboot permanently soft-locked the refill — now uses the realtime (epoch) clock and self-heals a backward clock; **(low)** `scores quest` was unmapped, so QUEST leaderboard entries were written but never displayable — now mapped.

## [1.3.1] — 2026-06-08 (PARRY: the paranoid foil to Eliza)

**Eliza gets a sparring partner.** PARRY (Kenneth Colby, 1972) joins as agora's second chatbot — and where Eliza is stateless input→template reflection, PARRY is **affect-driven**: it carries internal **fear / anger / mistrust** that decays toward a wary baseline, spikes when provoked, and *gates* which response it gives. Touch one of its delusion "flare" topics (the Mafia, his bookie, the gambling debt, being watched, the police) and it stops answering and starts telling its paranoid story. Reachable the same two ways as Eliza: a `play parry` door and a private `/parry` chat side-channel. No new dependencies. 155 → **160 tests**; 730,792 B → **752,240 B**.

### Added

- **PARRY** (`src/parry.cyr`) — Colby's 1972 paranoid chatbot as a pure module. It **reuses the ELIZA text primitives** (`ez_normalize` / `ez_word_is` / `ez_skip_sp` / `ez_word_end` / `ez_puts` / `ez_canned` / `ez_fill` / `ez_is_quit`) and adds the machinery ELIZA lacks: an **affect-state struct** (fear/anger/mistrust, sticky nonzero mistrust), a per-turn **input classifier** (benevolent / neutral / malevolent, with insult / threat / probe / mock / control sub-signals and HOT/WARM delusion "flare" topics), **decay-then-delta** affect dynamics, **mood-gated dispatch** (calm / wary / fearful / hostile), and an **8-beat delusion story** (debt → bookie → mob connection → threat → surveillance → seeking help → crooked cops → confinement) with a latch + a steer-back that resists topic changes without losing its place. Reachable as a `play parry` **door** (practice-only) and a private **`/parry`** chat side-channel. Unit-tested t156–t160; both wire surfaces proven by `13-parry.sh`.
- **Chat couch generalized** — the private chatbot side-channel was generalized from a single `g_chat_eliza` flag to a `g_chat_bot` id (0 none / 1 Eliza / 2 Parry) with `chat_bot_state` / `chat_bot_feed` / `chat_bot_name` helpers and a `/parry` command, so `/eliza` and `/parry` coexist on one couch (both bots keep their response buffer at the same struct offset, so the couch reads either uniformly). The privacy guarantee (couch input never reaches the room transcript) is preserved for both.

### Fixed

- Pre-release adversarial review (multi-agent, each finding verified; the affect model itself was checked and confirmed faithful) caught one real rotation defect: PARRY's probe-deflect gate advanced its `SLOT_PROBE` cycle counter twice per turn and tested a different value than it used to select the phrasing. Now a single counter tick gates and selects.

## [1.3.0] — 2026-06-08 (Chat area + Eliza: the synchronous public-assembly surface)

**agora gets a live multi-user chat room and its first inhabitant.** [ADR 0011](docs/adr/0011-chat-area.md) adds the *synchronous* public-assembly surface the BBS was missing — the classic teleconference / CB-simulator — built entirely on the 1.2.0 `flock`'d shared-disk discipline (no new concurrency model, no new dependencies). **Eliza** (Weizenbaum's 1966 DOCTOR) lands as a pure-module chatbot reachable two ways: a `play eliza` door and a private `/eliza` side-channel inside chat. 141 → **155 tests**; 678,776 B → **730,792 B** (clean DCE; on the cyrius 6.1.5 → 6.1.9 toolchain — the bump is the chat + Eliza source plus the toolchain codegen delta).

### Added

- **Chat area** (`src/chat.cyr`, [ADR 0011](docs/adr/0011-chat-area.md)) — a live, multi-user, login-gated teleconference. Per-channel append-only **ring transcript** at `<store>/.chat/<channel>/log` (32 KB cap; whole-line front-trim), mutated through the same `flock`'d lock → read → trim → append → write transaction the Universe established. `chat [channel]` (default `lobby`) joins; `/leave` `/help` `/quit` are the in-room commands; anything else is said to the room. A new `MODE_CHAT` in `handle_client` **live-tails by absolute sequence number** (not byte offset — the front-trim shifts bytes but never a seq, so a reader's position survives rotation), polled on the recv-timeout tick: while in chat the socket recv timeout drops to `CHAT_POLL_SECS` (2 s) and an `-EAGAIN` read flushes new lines instead of disconnecting (only when the input line is empty, so a half-typed line isn't garbled); pure silence is bounded by `CHAT_IDLE_SECS` (15 min). Message text is sanitised to printable ASCII (no tab/CR/LF/ESC), so it can neither break the `<seq>\t<handle>\t<text>` line format nor inject terminal escapes into another viewer. Pure transcript helpers (format / parse-seq / render / sanitise / ring-trim / tail-since) are unit-tested t142–t148; the cross-session interleaving is wire-proven by `11-chat.sh` (two logged-in sessions: scrollback delivery + live-tail tick).
- **Eliza** (`src/eliza.cyr`) — a faithful pure-module port of Weizenbaum's 1966 ELIZA DOCTOR script: normalize → whole-word pronoun reflection → ranked keyword scan (COMPUTER 50 · NAME 15 · LIKE 10 · REMEMBER 5 · DREAM 4 · IF 3 · WAS/MY/EVERYONE/FAMILY 2 · ALWAYS 1) → cyclic reassembly templates → a memory ring (`my X` stashes "your X", resurfaced on a later no-keyword turn as "Earlier you said your X.") → NONE deflections. Decomposition handles `i am/feel/want/can't/don't X`; object-position `you` reflects to `me` and the subject clauses `you are`/`you were` to `I am`/`I was`. Reachable as a `play eliza` **door** (practice-only — a conversation has no save state) and a private **`/eliza` side-channel** inside chat (toggle on the couch: replies go only to the asker, never to the room transcript; room tailing pauses). The engine's parsing/reflection/scan/memory primitives are written to be reused by **PARRY** (1.3.1). Unit-tested t149–t155; both wire surfaces + the privacy guarantee proven by `12-eliza.sh`.

### Changed

- **Toolchain pin lifted 6.1.5 → 6.1.9** (`cyrius.cyml [package].cyrius`). The crypto/sigil surface and the full suite stay green; no source changes required by the bump.

### Fixed

- Pre-release adversarial review (multi-agent, each finding independently verified) caught and fixed three real defects before the cut: Eliza reflected object-position `you` to the subject form `I` ("hate you" → "hate **I**"), and spelled-out `you are` to `I are`, instead of `me` / `I am`; and the chat live-tail advanced its seq watermark past lines dropped when the per-tick render buffer filled, silently losing them under burst (> ~27 messages in one 2 s tick). Regression-guarded by t155.

## [1.2.0] — 2026-06-08 (Persistent Universe: shared-world multiplayer for the door games)

**The door games go multiplayer.** [ADR 0010](docs/adr/0010-persistent-universe.md) lands in full: a shared, persistent, contested world per game lives on disk under `<store>/.games/<game>/world/`, mutated through a `flock`'d **lock → read → compute → write** transaction with the game logic staying a **pure transform** (the ADR 0009 pure-module rule survives). All three games now have a Universe; finished runs post to cross-game leaderboards. Built on the unblocked cyrius 6.1.5 toolchain — the array-in-loop codegen bug that reverted the first attempt is cleared (t129 probes it on the real code). 121 → **141 tests**; 484,184 B (1.1.0) → **678,776 B** clean DCE.

### Added

- **World-transaction framework** (bite 1, `door.cyr`) — per-game world dir + `flock` lock + snapshot read/write + the `world_txn_add` primitive. Race-proven: 16 procs × 500 → exactly 8000, no lost updates (`08-world-concurrency.sh`); t122/t123.
- **Port Authority shared galaxy** (bite 2) — the canonical Universe slice. Depletable **port stock** that moves the next player's quoted price (`paw_buy`/`paw_sell`/`paw_price`, clamped `[base/3, base*2]`); **exclusive planet ownership** by sigil fp (`paw_claim_planet`). One deterministic galaxy from a fixed `PA_UNIVERSE_SEED`; only the mutable stock + ownership live in the ~3 KB flat-i64 snapshot. `play port universe` is login-gated; the per-player ship persists in a `portu` save. The existing PA screen machine is untouched — `pa_buy`/`pa_sell`/`pa_establish_planet` detect Universe mode and route through the world. t128–t135; `09-universe-port.sh`.
- **PA deployments + async PvP** (bite 3) — drop ship fighters as a sector **garrison** (`[G]arrison`, `paw_deploy`); transiting a rival's garrison auto-resolves a fighter clash on arrival (`pa_arrival_universe` + the pure `pa_clash_loss`) — you fight the assets the defender left behind, never a live duel. A wiped garrison clears the sector; a hopeless transit destroys the ship. World snapshot v2. t136–t138.
- **Smuggler shared heat + Handler shared alerts** (bite 4) — all three games now have a Universe. Smuggler: a shared per-district **police heat** (`slw_*`) — a bust raises heat for everyone, dealing nudges it up, and high heat raises the next arrival's cop odds (`sl_heat_chance`). The Handler: shared per-city **alert levels** (`thw_*`) — burning an agent or fingering an innocent lights up the cities for all sections, and high total alert drains supervisor confidence faster at each rollover (`th_alert_drain`), cooling off daily. t139–t140. The per-line world transaction in `main.cyr` is generalized to dispatch by game (`door_world_begin`/`door_world_commit`/`door_universe_feed`/`door_universe_save`).
- **Cross-game leaderboards** (bite 5) — every game appends `<handle>\t<score>\t<rank>` to a shared, `flock`'d `<store>/.games/<game>/leaderboard` on a finished run (solo or universe), generalizing the 1.1.0 Handler standings. New `scores <game>` telnet command shows the top-10 by score (`lb_line_score` parses the score field; t141). `10-leaderboard.sh`.

### Changed

- The Handler's finished-run result now posts to the unified `leaderboard` file (was a Handler-only `standings` file at 1.1.0); all three games share the same leaderboard shape and the `scores` command.

### Added — roadmap

- **Eliza + a chat area** penciled as planned **1.3.0** (release table + a *Planned* design section in [`roadmap.md`](docs/development/roadmap.md)): a live multi-user chat surface with Eliza, a pure-module Rogerian chatbot, as anchor. Builds on the 1.2.0 shared-disk framework; no new deps.

## [1.1.1] — 2026-06-08 (The Handler: field pressure; toolchain unblocked 6.0.52 → 6.1.5)

**The Handler grows stakes, and the crypto blocker is gone.** This release deepens The Handler's single-player loop with a **field-pressure** system and lifts the cyrius toolchain cap that had deferred 1.2.0 bite 2+.

### Added

- **The Handler — field pressure** (`src/handler.cyr`). Three mechanics that were modeled in the save format since 1.1.0 (`AG_STRESS`, `AG_COVER`, the `AGS_DEAD` status) are now live gameplay, so the `THDG1` save format is **unchanged and forward/backward compatible**:
  - **Cover erosion + burnout.** Each day, active agents gain stress (field fatigue) and lose cover. When an agent's cover hits 0 they are **BURNED** (`AGS_DEAD`) — removed from play — and supervisor confidence takes an 8-point hit. A full network collapse can now end a campaign in recall.
  - **The mole gets people killed.** An unflagged mole compromises the honest agents **sharing its city** (the leak is local): +6 cover wear per day on co-located colleagues. The mole's danger is no longer only the slow confidence bleed — dithering burns your network. If you never catch it, the mole can self-burn (threat ends, but uncaught: no accusation surge).
  - **Extraction and funding gain teeth.** **Extract** now genuinely *saves* an agent from an impending burn (extracted agents are out of the field and still score half-trust); **Authorize funds** now relieves stress (morale) alongside lifting trust — a second purpose for the budget.
  - **Roster telemetry.** The roster shows each agent's **cover** and a **HOT** marker at high stress, so burns are foreseeable and the Extract/Fund decision is informed. Dead agents render `[BURNED]`.
- 4 new unit tests (t124–t127): pure cover-wear math (`th_cover_loss`), mole-co-located burn vs. distant survival + confidence hit, funding stress-relief, and extraction-saves-from-burn-and-still-scores. **123 → 127 tests.**

### Changed

- **Toolchain pin lifted `6.0.52` → `6.1.5`** (`cyrius.cyml [package].cyrius`). The cap at 6.0.52 existed because cyrius **≥ 6.0.53 SIGILL'd the sigil/sha256 crypto path** (fingerprint onward) — the gating dependency for 1.2.0 Persistent Universe bite 2+. **That blocker is resolved on 6.1.x**: the full crypto surface is green — 127/127 unit tests, runtime `keygen`→`register`→`whoami` fingerprint round-trip, and the end-to-end telnet Ed25519 challenge/response login (`welcome, qix` → bound `whoami`) all pass. Concurrency + door smokes re-verified (`08-world-concurrency` no lost updates; all three door games over telnet; board-policy across open/known/admin). Binary grew with the toolchain codegen: clean DCE build **484,184 B (6.0.52) → 654,592 B (6.1.5)** (+170,136 B / +35.2%) — a codegen change across the toolchain span, not an agora source change.

### Notes

- 1.2.0 bite 2+ (Persistent Universe / PA shared galaxy) is now **codegen-unblocked** — the sigil SIGILL is cleared. Resuming it is a fresh re-authoring of the reverted PA-world code per [ADR 0010](docs/adr/0010-persistent-universe.md), with a re-check of the context-dependent array-in-loop codegen on 6.1.x (a faithful minimal probe does not reproduce it).

## [1.1.0] — 2026-06-07 (door games: Smuggler's Ledger, Port Authority, The Handler)

**agora grows a door.** The classic BBS tradition of in-session text games arrives as a first-class subsystem ([ADR 0009](docs/adr/0009-door-games-subsystem.md)): three games reachable from any telnet session via `play <game> [practice|solo]`. Each game is a **pure state machine** (renders into a buffer, consumes one input line at a time) — `main.cyr` owns all socket I/O and persistence — so the entire economy / combat / deduction core is unit-tested without binding a port. 80 → **121 tests**; binary 378,456 → **484,184 B** (+105,728 B for the three games + framework). End-to-end telnet smoke drives all three games launch → play → exit.

### Added

- **Door framework** (`src/door.cyr`) — a seedable **xorshift64 PRNG** (solo runs are replayable, tests pin a known stream; the stdlib only ships a non-reproducible CSPRNG), integer helpers (`imin`/`imax`/`iclamp`/`iabs`/`ipow` + an arithmetic-safe logical-shift), `game_name_valid` (the save-slot path-traversal guard), per-user save path builders + dir-ensure + read/write under `<store>/.users/<fp16>/games/<game>.sav`, self-contained ANSI render helpers, and newline-positional save serialization.
- **Smuggler's Ledger** (`src/smuggler.cyr`) — a buy-low/sell-high contraband run across eight gritty metro districts over 30 days. Homage to the Dope Wars *style*, not a copy: **abstract smuggling goods, no real drug names**. Deterministic daily market with spike/crash events, a compounding loanshark debt, a bank vault, cops (fight/run), muggings, lucky finds, the fixer (capacity / guns / clinic), and net-worth rank tiers.
- **Port Authority** (`src/port_authority.cyr`) — a dark-sci-fi space-trade-and-combat run, homage to the TradeWars 2002 *style*. Deterministic galaxy (50 sectors, warp graph, port classes), four **re-themed** commodities on the classic buy/sell spread, warp navigation with turns-per-day, raider combat (fight/flee), the HQ upgrade dock (holds / fighters / shields), a planet credit-vault, and rank tiers.
- **The Handler** (`src/handler.cyr`) — a Cold-War espionage-deduction game from a user-supplied v1.0 spec. Run a five-agent network: daily cable traffic whose routing metadata *is* the gameplay, and a **mole whose paperwork leaves a consistent, genuinely-solvable discrepancy pattern** (relay city / stale date / cipher) while honest low-reliability agents only throw isolated clerical errors. Daily turn loop; dispatch actions (move / extract / authorize-funds / cross-reference / accuse); supervisor confidence + audit risk; recall/finish end states; and a shared **standings file** (`<store>/.games/handler/standings`, `flock`'d append — agora's first shared-disk feature).
- **`play <game> [practice|solo]`** telnet command + a new `MODE_DOOR` session sub-mode. Practice = ephemeral, anonymous-OK; Solo = login-gated persistent save. Universe (shared multiplayer) prints a roadmap stub.
- **[ADR 0009](docs/adr/0009-door-games-subsystem.md)** — door subsystem architecture: the pure-module split, the PRNG choice, the `.users/<fp16>/games/` storage layout, and The Handler's platform adaptations (sigil identity in place of DOS drop files, flat files in place of SQLite, instant render in place of the 2400-baud teletype, all per its own spec cut-line).
- 41 new unit tests (t81–t121) + `docs/examples/07-play-door.sh`.

### Roadmapped

- **Persistent Universe** (shared-world multiplayer) for all three games and **leaderboards** beyond The Handler's standings ([`docs/development/roadmap-future.md`](docs/development/roadmap-future.md)). Plus The Handler's v2 community layer (intercepted rival traffic, inter-section sabotage, world-event track, legacy ranks) and Port Authority's deep TW endgame (multiple planets, citadels, mining, deployed fighters/mines, alliances).

## [1.0.0] — 2026-05-23 (civic-marketplace BBS for AGNOS; iron-validated on archaemenid)

**agora 1.0.0.** The Greek **ἀγορά** — civic-marketplace, public assembly — open as the BBS userland for AGNOS deployments. Cross-platform telnet listener, multi-user concurrent sessions via fork-per-accept, sigil-backed Ed25519 challenge/response auth, multi-board threaded posts, per-board operator policy, audit-hardened input across both wire and CLI, frozen pre-1.0 ABI. Iron-validated on **archaemenid** (the project's reference AGNOS NUC): single-session telnet login round-trip (criterion #3) and 8-user concurrent fanout (criterion #4) both green at this tag.

### The arc

Eighteen tags from scaffold (0.1.0) to here, all shipped 2026-05-23:

- **M0 (0.1.0)** — six-stub argv dispatch; 43 KB scaffold.
- **M1 (0.2.0)** — cross-platform telnet listener via `lib/net.cyr`; RFC 854 IAC + RFC 1143 Q-method + RFC 1073 NAWS + RFC 1091 TT + RFC 1184 LINEMODE conformance; 10 ns/byte hot path (the baseline this tag re-validates against). [ADR 0001](docs/adr/0001-cross-platform-listener-decoupled-from-agnos.md).
- **M2 (0.3.0)** — bannermanor MOTD + darshana SGR + `--motd`.
- **M5 (0.4.0 → 0.5.0)** — post persistence: single-board (0.4.0) then multi-board threaded (0.5.0). [ADR 0002](docs/adr/0002-one-file-per-post-storage.md), [ADR 0003](docs/adr/0003-rfc-822-post-headers.md), [ADR 0004](docs/adr/0004-board-layout.md), [ADR 0005](docs/adr/0005-threading-via-reply-to.md).
- **M6 (0.6.0)** — sigil-backed Ed25519 identity: `keygen` / `register` / `whoami` / telnet `login`; `From:` header on authored posts; per-board `.policy` (open / known / admin) + `.admins`. Adds sigil + freelist + bigint + ct to stdlib deps. [ADR 0006](docs/adr/0006-identity-model.md).
- **0.7.0** — pre-1.0 security sweep ([`docs/audit/2026-05-23-audit.md`](docs/audit/2026-05-23-audit.md)): zero CRITICAL; 5 actionable fixes (H1 CLI subject CRLF, H2 cmd_list/cmd_read --board path-traversal, H3 post_from re-validation, M3 parse_post_id 18-digit overflow, M6 30s login deadline); 4 deferred to 0.8.
- **0.8.0 → 0.8.3** — closes every 0.7.0 deferred finding. 0.8.0 fork-per-accept concurrency ([ADR 0007](docs/adr/0007-fork-per-accept-concurrency.md)) — audit M1 + M2 both close via address-space isolation. 0.8.1 keyfile mode warn (L1). 0.8.2 sigil 3.1.1 → 3.4.3 diff read (no bump needed). 0.8.3 anonymous board-create gate (M4).
- **0.9.0** — pre-1.0 ABI freeze via PostHeaders struct ([ADR 0008](docs/adr/0008-post-headers-struct.md)). `post_format(ph, body, body_len, out, cap)` + `post_new(store, board, ph, body, body_len)` as the v1.0 public surface. Wire format byte-identical.
- **0.9.1** — guides + examples doc-pass: `docs/guides/getting-started.md` rewritten for the 0.9.0 surface; `docs/examples/README.md` + six runnable scripts (01 build+test, 02 register+post, 03 anon-read, 04 concurrent-smoke.py, 05 telnet-login.sh, 06 board-policy.sh); every script verified end-to-end against the binary.
- **0.9.2** — final closeout: CLAUDE.md "Closeout Pass" §1-11 walked end-to-end; benches re-captured within noise of M1-close; security re-scan clean; full clean DCE build green.
- **1.0.0 (this tag)** — version bump, release narrative, iron-validation confirmation.

### v1.0 criteria

Per [`docs/development/roadmap.md`](docs/development/roadmap.md) § v1.0 criteria:

| # | Criterion | Status |
|---|---|---|
| 1 | M0–M6 + security sweep + hardening all shipped at least once | ✅ |
| 2 | `cyrius audit` passes from a clean build (lint / test / bench / doc) | ✅ |
| 3 | Telnet validation on archaemenid LAN — connect → login → list → read → reply → quit | ✅ **`05-telnet-login.sh` green on archaemenid; fp `878873ab607321a5`** |
| 4 | Multi-user concurrency: simulated 8-user fanout, no message loss, no state corruption | ✅ **`04-concurrent-smoke.py 2323 8` → 8/8 sessions OK with banner + IAC + boards reply, no cross-talk** |
| 5 | Security audit (0.7.0) findings all closed in 0.8.0 hardening | ✅ — H1/H2/H3 + M3 + M6 at 0.7.0; M1+M2 at 0.8.0; L1 at 0.8.1; M4 at 0.8.3 |
| 6 | RFC conformance: `src/test.cyr` covers RFCs 854 / 1143 / 1073 / 1091 / 1184 | ✅ — 80 tests (t01–t24 IAC suite plus 56 storage / auth / policy / audit regressions) |

### Verified at 1.0.0

- **80/80 tests pass** (`cyrius test src/test.cyr`).
- **Clean DCE build** (`rm -rf build && cyrius deps && CYRIUS_DCE=1 cyrius build src/main.cyr build/agora`) → 378,456 B.
- **Iron validation on archaemenid (Linux x86_64, AGNOS):**
  - `02-register-and-post.sh` — keygen → register `qix` → post `--as` → list → read → `From: qix 878873ab607321a5` round-trip ✅
  - `05-telnet-login.sh 2323` — `login qix` → challenge → openssl-signed `auth:` → server `welcome, qix` → `whoami` reports bound identity ✅
  - `04-concurrent-smoke.py 2323 8` — 8 simultaneous TCP sessions, each gets its own banner + IAC negotiation + `boards` reply with no cross-talk ✅
- **Workstation re-smoke** of all 6 example scripts against the rebuilt 1.0.0 binary (01–06) — full green.
- `cyrius audit` clean.

### Changed

- `VERSION` 0.9.2 → 1.0.0.
- `src/main.cyr` — three inline version literals bumped (`print_banner`, `cmd_version`, `render_motd`).
- `docs/examples/05-telnet-login.sh` — banner drain now drain-and-print instead of two blind `read` calls (preserves the top row of the bannermanor MOTD in script output; cosmetic fix caught during iron validation).
- `docs/development/state.md` / `roadmap.md` / `doc-health.md` / `README.md` — all synced for the 1.0.0 ship.

### Followups queued for post-1.0

- **v2.x sovereignty pillars** ([`docs/development/roadmap-future.md`](docs/development/roadmap-future.md)) — six unpinned directions: identity continuity (portable sigil keys), content-addressed storage, threat-level node policy, federation by interest, self-distribution baked into the protocol, offline-tolerant store-and-forward. Items pull forward on consumer pressure, not by calendar.
- **Backlogged milestones** — M3 (inline-image post bodies via kii) and M4 (stored-file deltas via sankoch) are gate-met but ship-deferred; pull when a real consumer asks.
- **Operator CLI** — `agora policy set <board> <mode>` and `agora admins {add,rm,list}` (operators currently edit `.policy` / `.admins` files directly). Earn their slot when a real deployment asks.
- **macOS / Windows ports** — pending `lib/net.cyr` backends in cyrius; agora carries no platform-specific code today.

### Naming

agora opens the **Greek naming lane** in the AGNOS ecosystem, alongside the existing Sanskrit/Hindi lane (system libs: darshana, kybernet, sankoch, sit) and the English-wordplay / Polynesian lane (user-facing tools: bannermanor, kii). Three convergent layers behind the name: ancient ἀγορά (civic-marketplace, public assembly) + Doja Cat's *Agora Hills* (Scarlet, 2023) + Agoura Hills CA (adjacent to project home base).

## [0.9.2] — 2026-05-23 (final 1.0 closeout sweep)

Bite G of the 0.8 cycle plan, finally landed. The last release before the 1.0 cut. Full CLAUDE.md "Closeout Pass" §1-11 executed against the 0.9.x tip: tests + benchmarks re-captured (within noise of M1-close baseline; parser hot path unchanged across every release since M6), full clean build from `rm -rf build && cyrius deps && CYRIUS_DCE=1 cyrius build` green, security re-scan clean (no `sys_system`, no unbounded buffers, no new external-input paths since 0.8.3), all six `docs/examples/` scripts re-verified end-to-end. No code changes beyond the version-literal bumps. After 0.9.2 the only remaining 1.0 gate is criterion #3 — telnet validation on archaemenid LAN.

### Verified

- **80/80 tests pass** (`cyrius test src/test.cyr`) — unchanged from 0.9.1.
- **Benchmarks re-captured** (`cyrius bench benches/bench_telnet.bcyr`) — all 5 within ±2 ns of the M1-close baseline. The first run showed `announce_salvo` elevated to 163 ns avg with min=131 ns; re-run stabilized at 134 ns; the elevated avg was system noise. `BENCHMARKS.md` updated with the 0.9.2 row.
- **Full clean build** (`rm -rf build && cyrius deps && CYRIUS_DCE=1 cyrius build src/main.cyr build/agora`) → 378,440 B (identical to 0.9.1; version-string length deltas neutral).
- **Security re-scan**: no `sys_system` / `system(` anywhere; one `var buf[32]` in `board.cyr:931` (`board_policy_get` file read) verified bounded against the 32-byte `file_read_all` cap; no TODO / FIXME / XXX / HACK markers anywhere in `src/*.cyr`.
- **Dead-code audit**: 666 unreachable fns / 158,837 bytes NOPed by DCE — all stdlib bloat (sigil pulls map / mutex / shake256 surfaces that agora doesn't call); no agora-source dead code. Function counts: main.cyr 34, board.cyr 36, account.cyr 22, telnet.cyr 31 (123 total).
- **Examples**: 01–06 all green against the 0.9.2 binary. 01 build+test passes. 02 register-and-post writes the From header (fp `bdccc7a4d1991a4d` on this re-run). 03 confirms anon-read works + anon-post denied. 04 3-session smoke shows no cross-talk. 05 telnet-login completes the openssl-signed challenge/response to `welcome, qix` + `whoami` confirmation. 06 all 9 policy assertions pass.
- **Version-verify**: `VERSION` = 0.9.2, `cyrius.cyml [package].version = ${file:VERSION}`, binary reports `agora 0.9.2`, CHANGELOG header matches.

### Changed

- `VERSION` 0.9.1 → 0.9.2.
- `src/main.cyr` — three inline version literals bumped (`print_banner`, `cmd_version`, `render_motd`).
- `BENCHMARKS.md` — 0.9.2 row added to per-release history; main table refreshed; "Last Updated" stamp bumped.
- `docs/development/state.md` / `roadmap.md` / `doc-health.md` — refreshed for the 0.9.2 ship; in-flight slot now reads "1.0.0 cut — handoff for archaemenid iron validation".

### Followups queued for 1.0.0

- **VERSION 0.9.2 → 1.0.0** + final CHANGELOG entry summarizing the M0–M6 + 0.7–0.9 arc.
- **Telnet validation on archaemenid LAN** (v1.0 criterion #3) — iron NUC running AGNOS serves telnet to a second box; end-to-end: connect → log in → list boards → read a thread → post a reply → log off. User task on iron; not codeable from the workstation.
- **8-user fanout concurrency check** (v1.0 criterion #4) — extend `docs/examples/04-concurrent-smoke.py` from N=3 to N=8 once on iron; assert no message loss / state corruption.

## [0.9.1] — 2026-05-23 (guides + examples doc-pass)

The long-deferred Tier 5 + Tier 6 doc-pass — `docs/guides/getting-started.md` (74-line 0.1.0-stub-verb walkthrough) and `docs/examples/README.md` (6-line placeholder) both rewritten to cover the 0.9.0 surface, plus six runnable example scripts added. Every script verified end-to-end against `./build/agora`. No code changes beyond the version-literal bumps. Bite F from the 0.8 cycle plan; closes the last `🟡 Stale` row in `docs/doc-health.md`.

### Added

- **`docs/guides/getting-started.md` (rewrite)** — full walkthrough: prereqs, build, tests (80/80), `agora serve 2323`, anon-read commands, M6 default policy, keygen + register + post `--as`, telnet `login` challenge/response, per-board `.policy` / `.admins` table, fork-per-conn concurrency check, cross-links to all 8 ADRs and the 6 runnable examples.
- **`docs/examples/README.md` (rewrite)** — 6-row example index with surface + writeability columns, run order, monotonic-numbering convention for future additions.
- **`docs/examples/01-build-and-test.sh`** — build, version-sanity vs `VERSION`, run `src/test.cyr` (80/80).
- **`docs/examples/02-register-and-post.sh`** — first writeable flow: keygen → register `qix` → post `--as` → list → read → assert `From: qix <fp16>` on disk.
- **`docs/examples/03-anonymous-read.sh`** — proves M6 default policy: anon list + read succeed against 02's post; anon post denied with exit 1.
- **`docs/examples/04-concurrent-smoke.py`** — threads N (default 3) telnet sessions, asserts each gets independent banner + IAC bytes + `boards` reply (proves ADR 0007 process isolation).
- **`docs/examples/05-telnet-login.sh`** — drives the wire challenge/response: `login qix` → wraps the 32-byte seed in PKCS#8 DER → `openssl pkeyutl -sign -rawin` → replies `auth: <hex>` → asserts `whoami` reports `qix`. Verified against openssl 3.6.2.
- **`docs/examples/06-board-policy.sh`** — walks all three policy modes (open / known / admin) × three identity classes (anon / pac / qix), asserts every cell's expected exit code. 9/9 assertions pass.

### Changed

- `VERSION` 0.9.0 → 0.9.1.
- `src/main.cyr` — three inline version literals bumped (`print_banner`, `cmd_version`, `render_motd`).
- `docs/doc-health.md` — Tier 5 + Tier 6 rows moved from 🟡 Stale → ✅ Fresh; at-a-glance bucket counts refreshed (Stale: 2 → 0); commitment #2 closed.

### Fixed (caught during example verification — doc-only)

- **`getting-started.md` anonymous-post claim** — earlier draft showed `agora post` working without `--as`. M6 default is `anon-read, **auth-post**`; `board_can_post` returns 0 for any `session_fp == 0`, so anonymous CLI posts return exit 1 with `board policy requires authentication`. Guide now lists the in-session command table with per-command anon eligibility.
- **`getting-started.md` policy-mode table** — `open` was shown as anon-permitted. Anonymous is denied across all three modes at M6 (open / known / admin); per-board anon override is queued as a future ADR per ADR 0006 § Negative.
- **`getting-started.md` main-board path** — examples referenced `<store>/main/N.txt`; per ADR 0004 the main board is the flat store root (`<store>/N.txt`); named boards live in subdirs. Corrected.
- **`05-telnet-login.sh` wire format** — initial draft sent `auth <hex>`; server's `parse_auth_sig` expects `auth: <hex>` (with the colon, optional space). Corrected.
- **`05-telnet-login.sh` openssl invocation** — Ed25519 `pkeyutl -sign -rawin` is a oneshot op and rejects stdin (`unable to determine file size`). Switched to `-in <tmpfile>` and dropped the PEM conversion in favor of `-keyform DER` directly.

### Verified

- **80/80 tests pass** (`cyrius test src/test.cyr`).
- **Clean build green** (`cyrius build src/main.cyr build/agora` → 378,440 B, +8 B from version-string length deltas).
- **All 6 examples verified end-to-end** against the rebuilt 0.9.1 binary; 04 and 05 verified against a running `./build/agora serve 2323`.
- `cyrius audit` clean.

### Followups queued for 0.9.x → 1.0.0

- **G / 0.9.2** — perf re-run + final 1.0 closeout sweep. CLAUDE.md "Closeout Pass" §1-11 against the 0.9.x tip.
- **1.0.0** — archaemenid LAN iron validation (criterion 3 of the v1.0 gate).

## [0.9.0] — 2026-05-23 (PostHeaders struct — pre-1.0 ABI freeze)

The pre-1.0 ABI freeze. `post_format_with_headers` and `post_new_with_subject_reply` have grown from 5 → 6 → 8 positional args across M5-D / M5-F / M6-E, and the v1.x roadmap forecasts more (federated `Origin:`, content-addressed `Content-Hash:`). 0.9.0 replaces both with a single `PostHeaders` struct ptr per [ADR 0008](docs/adr/0008-post-headers-struct.md) — future headers earn a new `PH_*` offset + setter; call sites that don't use the new field don't change. Wire format is byte-identical; this is purely a call-shape refactor.

### Added

- **[ADR 0008 — Post header parameters as a struct](docs/adr/0008-post-headers-struct.md)** — decision rationale for the freeze. Rejects (A) freeze-8-arg-as-is (variant-fn proliferation), (C) flat heap-buffer + offset table (pushes formatting up), (D) varargs emulation (no readability win), (E) keep-shims-alongside-struct (CLAUDE.md "avoid backwards-compatibility hacks"). Picks (B) PostHeaders struct as the v1.0 freeze shape.
- **`PostHeaders` struct + setters in `src/board.cyr`** — `PH` enum with 4 offsets (PH_SUBJECT, PH_REPLY_TO, PH_FROM_HANDLE, PH_FROM_FP) + `PH_SIZE`. New fns: `post_headers_new()` (zero-init alloc), `post_headers_set_subject(ph, cstr)`, `post_headers_set_reply_to(ph, parent_id)`, `post_headers_set_from(ph, handle_cstr, fp_cstr)`.
- **`post_format(ph, body, body_len, out_buf, out_cap)`** (5 args, was 8) — primary formatter.
- **`post_new(store, board, ph, body, body_len)`** (5 args, was 8) — primary post writer.

### Breaking

- **`post_format_with_headers(subject, reply_to, from_handle, from_fp, body, body_len, out_buf, out_cap)` REMOVED.** Replaced by `post_format(ph, body, body_len, out_buf, out_cap)`. Migration: construct a `PostHeaders` struct via `post_headers_new()` + the three setters; pass it as the first arg.
- **`post_new_with_subject_reply(store, board, subject, reply_to, from_handle, from_fp, body, body_len)` REMOVED.** Replaced by `post_new(store, board, ph, body, body_len)`. Same migration.
- **`post_format_with_subject(subject, body, body_len, out_buf, out_cap)` REMOVED** (was a dead M5-D backwards-compat shim — zero production callers since M5-F).
- **`post_new_with_subject(store, board, subject, body, body_len)` REMOVED** (same — dead shim).
- **`post_new(store, board, body_buf, body_len)` (4-arg legacy form) REMOVED** — replaced by the new 5-arg struct-based variant. Old form was dead M5-A code unused since M5-D's header layer landed. CLAUDE.md "delete unused" hygiene.

Migration is mechanical:

```
// Before (0.8.x)
var flen = post_format_with_headers(subj, parent, handle, fp, body, body_len, out, cap);

// After (0.9.0)
var ph = post_headers_new();
post_headers_set_subject(ph, subj);
if (parent > 0) { post_headers_set_reply_to(ph, parent); }
if (handle != 0) { post_headers_set_from(ph, handle, fp); }
var flen = post_format(ph, body, body_len, out, cap);
```

agora is a binary, not a library — no external consumers. The shim removal is hygiene, not a real-world break.

### Changed

- `src/board.cyr` — `post_format_with_headers` rewritten as `post_format(ph, ...)`; `post_new_with_subject_reply` rewritten as `post_new(store, board, ph, ...)`. Dead M5-A `post_new` (4-arg body-only writer, unused since M5-D) removed.
- `src/main.cyr` — `session_finalize_post` (telnet `post` / `reply` commit) + `cmd_post` (CLI) rewritten to construct `PostHeaders` and call `post_new`. `from_handle` / `from_fp` resolution unchanged; just plumbed through `post_headers_set_from` instead of as positional args.
- `src/test.cyr` — t49 / t64 / t65 / t66 rewritten to use `post_headers_new` + setters + `post_format`. Test semantics unchanged; only call shape.

### Verified

- **80/80 tests pass** from a clean `rm -rf build && cyrius deps && cyrius build`. Wire format byte-identical — t49 Reply-To round-trip, t64 From-header presence, t65 post_from extraction, t66 anonymous-no-From all pass with the new shape.
- **End-to-end smoke**: `agora keygen` → `register --handle qix` → `post --subject "ABI freeze test" --as qix --key ./key` → `list` shows `1  [qix]  ABI freeze test` → `read 1` shows correct From / Subject / body. Raw `./store/1.txt` byte-for-byte matches the 0.8.x format (Subject / Date / From / blank / body).
- Binary 378,936 B (0.8.3) → 378,432 B (0.9.0), **−504 B (−0.13%)** — refactor + dead-`post_new`-removal net-shrunk the binary even after adding the struct + 3 setters.
- 5 telnet-parser benchmarks unchanged from M1-close baseline (post-format work is offline-of-hot-path).
- `cyrius audit` clean.

### Followups queued for 0.9.x

- **F / 0.9.1** — guides + examples doc-pass (deferred from M6 close + 0.7.x + 0.8.x). Rewrite `docs/guides/getting-started.md` + `docs/examples/` for the 0.9.0 surface: build, telnet flow, CLI verbs, ADR 0007 fork-per-conn, ADR 0008 PostHeaders, all 5 0.7.0 audit-hardenings as security features.
- **G / 0.9.2** — perf re-run + final 1.0 closeout sweep. CLAUDE.md "Closeout Pass" §1-11 against the 0.9.x tip.
- **1.0.0** — archaemenid LAN iron validation.

### Future v1.x extensions (no work this cycle — flagged for ADR 0008's followups)

- Federated `Origin:` header (per ADR 0006 § Negative + roadmap-future.md pillar 1): `post_headers_set_origin(ph, origin_cstr)` adds one PH offset + one setter; call sites unchanged.
- Content-addressed `Content-Hash:` header (v2.x pillar 2): same shape.

## [0.8.3] — 2026-05-23 (anonymous board-create gate — audit M4)

Closes the last audit-deferred finding from the 0.7.0 security sweep ([`docs/audit/2026-05-23-audit.md`](docs/audit/2026-05-23-audit.md) § M4). Anonymous wire sessions can no longer `enter <new-board>` to spam-create directories under the store. Existing boards stay anonymous-readable; only the **create** path is auth-gated. Matches the M6 "anon-read, auth-post" default policy shape.

### Security

- **Audit M4 closed** — anonymous board-create gate. In `session_execute` enter handler: if `board_exists(store, name) == 0` AND the session is anonymous (`g_session_fp` empty), reject with `auth required to create new boards — run 'login <handle>' first` instead of proceeding to `board_ensure` / `mkdir`. CLI path was already gated (`cmd_post` runs `board_can_post` before `post_new_with_subject_reply`'s `board_ensure`, and `board_can_post` denies anon for any policy mode).

### Changed

- `src/board.cyr` — new `board_exists(store, board)` helper: returns 1 for `"main"` (the implicit flat root, always counts as existing) or any named board whose directory is present via `is_dir`; 0 otherwise.
- `src/main.cyr` — `session_execute` enter handler grew the audit-M4 gate. ~12 LOC: anon detection (`g_session_fp` empty cstring) + `board_exists` lookup + early-return error on the create case. Existing-board enter unaffected.
- `src/test.cyr` — new `t80_board_exists_main_and_missing` (80 tests total): covers `main` always-existing, missing named board under nonexistent store, missing named board under `/tmp` (a definitely-existing dir).

### Verified

- **80/80 tests pass** from a clean `rm -rf build && cyrius deps && cyrius build` (+1 test for the existence check).
- **End-to-end smoke** (`/tmp/agora-m4-smoke.sh`): (1) anon `enter qixboard` → "auth required to create new boards" ✓; (2) post-login `enter zaxboard` → "entered zaxboard" + dir actually created on disk ✓. Uses openssl 3.6 `pkeyutl -sign -rawin` to generate the Ed25519 sig against the parked challenge (same shape as the M6-C / M6-D smokes).
- Binary 378,416 B (0.8.2) → 378,936 B (0.8.3), +520 B (+0.14%) for the `board_exists` helper + the auth gate + t80 test scaffolding.
- 5 telnet-parser benchmarks unchanged from M1-close baseline (gate only runs on `enter`, never on byte-path).
- `cyrius audit` clean.

### Audit status (0.7.0 sweep)

All actionable findings now closed:

| Severity | Finding | Status |
|---|---|---|
| HIGH | H1 — CLI subject CRLF injection | ✅ 0.7.0 |
| HIGH | H2 — cmd_list/cmd_read --board path-traversal | ✅ 0.7.0 |
| HIGH | H3 — `post_from` re-validate handle/fp | ✅ 0.7.0 |
| MEDIUM | M1 — bump-allocator memory growth | ✅ 0.8.0 (ADR 0007 fork-per-accept) |
| MEDIUM | M2 — login-challenge slot collision | ✅ 0.8.0 (ADR 0007 fork-per-accept) |
| MEDIUM | M3 — parse_post_id overflow guard | ✅ 0.7.0 |
| MEDIUM | M4 — anonymous board-create gate | ✅ **0.8.3** |
| MEDIUM | M6 — 30s parked-login deadline | ✅ 0.7.0 |
| LOW | L1 — keyfile mode warn-on-load | ✅ 0.8.1 |
| — | sigil 3.1.1 → 3.4.3 diff (deferred research) | ✅ 0.8.2 (no bump) |

Next bite (0.9.0) opens the ABI freeze decision (D — likely new ADR 0008 on `post_format_with_headers` signature shape).

## [0.8.2] — 2026-05-23 (sigil 3.1.1 → 3.4.3 release-notes diff — audit-followup, no bump)

Audit-followup release discharging the "sigil 3.1.1 → 3.4.3 release-notes diff read" item from the 0.7.0 audit's `Deferred to 0.8 v1-hardening` queue ([`docs/audit/2026-05-23-audit.md`](docs/audit/2026-05-23-audit.md) § "Deferred"). **No sigil bump needed**; bundled 3.1.1 stays pinned through cyrius 6.0.1's lib snapshot.

### Security

- **0.7.0 deferred item closed**: full diff read of `~/Repos/sigil/CHANGELOG.md` from 3.1.2 through 3.4.3 (13 releases). Findings:
  - **Zero CRITICAL/HIGH** in any release affecting agora's consumed surface (`ed25519_verify`, `ed25519_keypair`, `sha256`).
  - **Constant-time discipline maintained** through the diff window — explicit note at sigil 3.2.1: "Constant-time discipline maintained for the scalar-mul primitive even though verify inputs are public — preserves the 'no timing side-channels on any future secret-data caller' invariant."
  - **Ed25519 signature malleability fix** (sigil HIGH H3 — RFC 8032 §5.1.7 / §8.4 S < L check) — landed at sigil 2.1.0 (April 2026), already in 3.1.1, already in agora.
  - **One MEDIUM** flagged in sigil 3.0.0 → 3.1.x (thread-safety on module-global crypto scratch — `_sha_*`, `_ed_*` etc.) — **does not apply to agora**. ADR 0007 fork-per-conn makes every child process single-threaded; sigil primitives are never called concurrently from multiple threads within a single agora process. Sigil 3.3.0 closed it anyway via "per-call working state" rewrite, so even if a future agora consumer goes multi-thread within one process, the bundled-3.1.1 limitation is bounded by the documented mitigation (`_sigil_batch_mutex`) which agora never invokes.
  - **3.2.x — 3.4.x improvements** (parallel `sv_verify_batch`, `VerifyScratch` alloc-free, NI self-test gate, X.509 / ECDSA P-256 / TEE attestation surface, `secret var` adoption for zeroization) all add new surface area that agora doesn't consume. The bundled 3.1.1 has every fix relevant to our call pattern.

### Verdict

- **NO sigil version bump.** Bundled `sigil` (in cyrius 6.0.1 stdlib lib snapshot, 3.1.1) is sufficient through agora 1.0.
- **No `cyrius.cyml` change.** stdlib pin stays at cyrius 6.0.1 / sigil 3.1.1.
- **No code change in agora.** All five 0.7.0 HIGH fixes (H1-H3, M3, M6) plus the 0.8.0 fork-per-conn refactor plus the 0.8.1 keyfile-mode-warn all stay in place.

### Verified

- 79/79 tests pass (no change from 0.8.1 — this release is documentation only).
- Binary 378,400 B (0.8.1) → 378,416 B (0.8.2), +16 B from the version-literal string-length deltas only (one banner line picked up a longer suffix). No functional code change.
- `cyrius audit` clean.

### Changed

- Version literals bumped 0.8.1 → 0.8.2 in `print_banner` (cites the diff-read decision), `cmd_version`, `render_motd`.

### Followup queued for 0.8.3

- **B / audit M4** — anonymous `enter <name>` board-create gate. Independent of concurrency model + sigil; next bite in the 0.8.x sequence.

## [0.8.1] — 2026-05-23 (keyfile mode warn-on-load — audit L1)

Smallest possible patch closing audit L1 from the 0.7.0 security sweep ([`docs/audit/2026-05-23-audit.md`](docs/audit/2026-05-23-audit.md) § L1). `keyfile_load_seed` now `fstat`s the open keyfile and warns to stderr if any group / other permission bit is set (mode & 0o077 != 0). Doesn't refuse the load — containerized deployments may legitimately use world-readable mounts; the operator notices the warning on next `register` / `whoami` / `--as` invocation and decides whether to tighten.

### Security

- **Audit L1 closed** — keyfile mode warn-on-load. Same shape as `ssh`'s `-i` permission check, minus the refuse-on-loose behavior. The warning surfaces on every load (not cached) so a `chmod 644` mid-deployment trips immediately.

### Changed

- `src/account.cyr` — new `mode_is_loose(mode)` pure-bit helper (returns 1 iff `mode & 0o077 != 0`); new `keyfile_warn_loose_mode(path, fd)` that fstats + warns on stderr; `keyfile_load_seed` rewritten from one-shot `file_read_all` to explicit open + fstat + read + close so the warning hook can run between open and read.
- `src/test.cyr` — new `t79_mode_is_loose` (79 tests total): 10 fixed-mode cases covering tight (0o600 / 0o700 / 0o400 / 0o000) → 0, loose (0o644 / 0o660 / 0o604 / 0o666 / 0o601 / 0o610) → 1, and `S_IFREG | 0o600` (high type bits don't trigger) → 0.

### Verified

- **79/79 tests pass** from a clean `rm -rf build && cyrius deps && cyrius build` (+1 test for the mode-bit math).
- **End-to-end smoke**: `agora keygen --key ./key` produces 0o600 silently; `chmod 644 ./key && agora whoami --key ./key` emits `agora: warning: keyfile ./key has loose permissions (group/other readable); recommend chmod 600` on stderr and continues; `chmod 666` likewise; `chmod 600` returns to silent.
- Binary 377,520 B (0.8.0) → 378,400 B (0.8.1), +880 B (+0.23%) for the fstat call + mode check + warn-emit + the test scaffolding for t79.
- 5 telnet-parser benchmarks unchanged from M1-close baseline (this patch only touches the keyfile-load path; never on the hot path).
- `cyrius audit` clean.

## [0.8.0] — 2026-05-23 (concurrent accept — fork-per-connection)

agora becomes a **truly multi-user telnet BBS**. The accept loop now forks per connection ([ADR 0007](docs/adr/0007-fork-per-accept-concurrency.md)); each client runs in its own process with isolated identity slots, isolated session state, and kernel-managed memory cleanup at `sys_exit`. The two co-scheduled MEDIUM findings from the 0.7.0 audit — **M1** (bump-allocator memory growth in long-running serve) and **M2** (`g_login_*` slot collision under concurrent accept) — both close via process isolation: kernel reclaims per-child memory atomically at exit, and globals are per-process post-fork so two clients running `login` simultaneously cannot collide.

### Added

- **[ADR 0007 — Concurrent connections via fork-per-accept](docs/adr/0007-fork-per-accept-concurrency.md)** — decision rationale: rejects thread-per-accept (M2 only closes with shared-state refactor; concurrency bug surface), epoll event loop (forces every byte handler to be yield-aware), and single-track-with-arena (only closes half the audit). Picks fork because the kernel address-space boundary closes M1 + M2 simultaneously with the smallest source-level diff.

### Changed

- `cmd_serve_on` (`src/main.cyr`) is now fork-per-accept. Loop shape:
  1. Drain zombies via `sys_waitpid(-1, NULL, WNOHANG)` until it returns ≤ 0.
  2. `sock_accept` for the next client.
  3. `sys_fork`: child closes the listening fd and runs `handle_client(cfd)` + `sys_exit(0)`; parent closes the accepted cfd and continues.
- Per-connection state (`g_session_fp` / `g_session_handle` / `g_login_fp` / `g_login_nonce` / `g_login_started_ms` / `g_reply_*`) stays in globals — fork makes them per-process automatically; no struct refactor needed. This was a deliberate decision in ADR 0007 (smallest possible diff for the audit close).
- Banner / version literals bumped 0.7.0 → 0.8.0 in `print_banner`, `cmd_version`, `render_motd`.

### Verified

- **78/78 tests pass** from a clean `rm -rf build && cyrius deps && cyrius build`. No new tests for E itself — the change is in the accept loop, exercised end-to-end by smoke testing (see below).
- **Concurrent-accept smoke** (3 simultaneous sessions): each gets its own MOTD + banner + prompt + independent `whoami` (anonymous, no cross-session state). Test driver: `python3 /tmp/agora-concurrent-smoke.py 23456 3` against `./build/agora serve 23456`. 3/3 sessions OK.
- **Zombie reaper smoke**: round 1 of 3 connections leaves 3 zombies (`ps -eo ... ZN`); round 2 of 1 connection triggers the waitpid drain at top of accept loop, clearing all 3 round-1 zombies. Round 2's own child becomes the new pending zombie (reaped at next accept). Steady-state behavior matches ADR 0007's "drained at next iteration" model.
- Binary size 377,184 B (0.7.0) → 377,520 B (0.8.0), +336 B (+0.09%) for the fork wrapper + waitpid reaper loop. DCE same.
- 5 telnet-parser benchmarks unchanged from M1-close baseline — fork happens before any IAC byte flows, so the parser hot path is unaffected.

### Security

- **Audit M1 closed** (bump-allocator memory growth). Each connection's bump-allocated memory is reclaimed atomically by the kernel at child `sys_exit`. The parent's per-loop allocations (Result wrappers from `sock_accept`) are minimal and bounded by the accept rate.
- **Audit M2 closed** (login-challenge slot collision). Post-fork, every child has its own copy of `g_login_*` / `g_session_*` / `g_login_started_ms` via the kernel's address-space isolation. Two clients running `login alice` and `login bob` simultaneously cannot poison each other's parked challenge.
- **Audit M4 NOT closed** (anonymous `enter` can spam-create boards). Independent of the concurrency model; explicit auth gate or accept-loop rate limit needed. Carried forward to 0.8.x patches.

### Operator notes

- Run `agora serve` under a process supervisor (systemd, runit, supervisord) so the parent crash kills all children. Standard for any forking server; called out explicitly because the v0.7.x single-track model didn't surface this concern.
- Zombies persist between accept iterations — visible as `ZN` rows in `ps` against the parent's PID. This is expected: the waitpid reaper runs at the top of each accept loop iteration. On a busy server, zombies are drained within ms of each new connection. On an idle server, zombies wait until the next connection arrives. Not a leak; bounded by N children since last accept.

## [0.7.0] — 2026-05-23 (pre-1.0 security sweep)

agora's first dedicated security audit cycle per CLAUDE.md "Security Hardening" and the roadmap release plan. Full line-by-line read of the IAC parser (`src/telnet.cyr`), post storage + ingress (`src/board.cyr`), M6 auth surface (`src/account.cyr`), and the wire dispatch in `src/main.cyr`, against the CLAUDE.md security checklist + external CVE history (CVE-2020-10188 telnetd IAC overflow, CVE-2011-4862 telnetd AUTHENTICATION overflow). Full findings in [`docs/audit/2026-05-23-audit.md`](docs/audit/2026-05-23-audit.md).

**No CRITICAL findings.** The bounded IAC buffers, fresh single-use nonces over `/dev/urandom`, and per-board flock + `O_EXCL` claim path all held up. **5 actionable findings** landed as fixes this cycle (3 HIGH, 2 MEDIUM); 4 deferred to 0.8 v1-hardening (concurrent-accept refactor + per-conn memory arenas, accept-loop rate-limit / `enter` auth gate, keyfile mode warn-on-load, sigil 3.1.1 → 3.4.3 release-notes diff read).

### Security — fixed this cycle

- **H1 — CLI subject CRLF injection** (`cmd_post`). `--subject $'foo\r\nReply-To: 42'` previously wrote forged headers into the stored post, parsed as real headers by `post_reply_to` / `post_from` on every subsequent read. New helpers `header_text_ok` / `header_text_buf_ok` / `header_text_cstr_ok` in `src/board.cyr` reject CR/LF/NUL/ESC and other C0 control bytes (except TAB) from header-context values; `cmd_post` calls the validator at entry.
- **H2 — `cmd_list` + `cmd_read` accept path-traversal `--board`** (`src/main.cyr`). `--board "../../etc"` previously resolved through `board_path` to a parent-of-store directory. Now both verbs run `board_name_valid` whenever `board != "main"`, mirroring `cmd_post`'s existing check.
- **H3 — `post_from` does not re-validate handle / fp on read** (`src/account.cyr`). A tampered `.users/<fp>/handle` file (operator-side or a future federated-import path) could smuggle ESC sequences into every reader's terminal via the `send_buf(cfd, hbuf, strlen(hbuf))` render path. `post_from` now re-runs `handle_valid` on the extracted handle and a new `fp16_valid` helper on the extracted fingerprint; invalid → return 0 / clear outputs / render as anonymous.
- **M3 — `parse_post_id` digit-prefix overflow** (`src/board.cyr`). `n = n * 10 + (c - 48)` on a 19+ digit filename overflows i64. Now capped at 18 digits (i64 holds 18 full digits at 9.22e18) — anything longer is rejected as not-a-post-id.
- **M6 — explicit 30 s deadline on parked login challenge** (`src/main.cyr` MODE_LOGIN_AWAIT_SIG). M6-C deferred this; relied on `RECV_TIMEOUT_SECS = 60` idle drop, which a heartbeat-sending client can defeat. New `g_login_started_ms` + `LOGIN_DEADLINE_MS = 30000` enforce the ADR 0006 § Specifics deadline at the top of the auth-line dispatch — uses `clock_now_ms()` from `lib/chrono.cyr`.

### Security — deferred to 0.8 v1-hardening

- **M1 — bump-allocator memory growth in long-running serve.** `alloc()` is bump-only; each connection accretes ~73 KB and each `read` adds ~100 KB. Will rework in the concurrent-accept refactor (per-connection arenas freed at `sock_close`).
- **M2 — `g_login_*` slots become per-connection** at the same refactor (today's single-tracking accept loop makes them de facto per-session).
- **M4 — anonymous `enter` can auto-create boards** (storage exhaustion vector). Fix: require auth for board creation OR add accept-loop rate limiting.
- **L1 — `keyfile_load_seed` does not warn on world-readable mode.** Defense-in-depth `fstat` check at load time.

### Verified

- **78/78 tests pass** from a clean `rm -rf build && cyrius deps && cyrius build` (+8 regression tests for the 5 fixes: t71 header_text_ok control-byte filter, t72 header_text_buf_ok CRLF injection scan, t73 fp16_valid accepts, t74 fp16_valid rejects, t75 post_from rejects invalid handle, t76 post_from rejects invalid fp, t77 parse_post_id 19+ digit overflow guard, t78 parse_post_id 18-digit ceiling).
- **End-to-end smoke** for each HIGH fix: `agora post --subject $'foo\r\nReply-To: 1'` exits 2 with the C0-control error; `agora list --board "../../etc"` exits 2 with the invalid-name error; `agora read 1 --board "../../tmp"` exits 2 with the invalid-name error.
- Binary size 374,968 B (0.6.0) → 377,184 B (0.7.0), +2,216 B (+0.6%) for the validator helpers + login-deadline check + test surface. DCE same.
- 5 telnet-parser benchmarks unchanged from M1-close baseline (security patches don't touch the parser hot path).
- `cyrius audit` clean.

### Changed

- `VERSION` bumped 0.6.0 → 0.7.0.
- `print_banner` / `cmd_version` / `render_motd` version literals bumped to 0.7.0 in lockstep.
- `src/board.cyr` grew `header_text_ok` / `header_text_buf_ok` / `header_text_cstr_ok` / `fp16_valid` (4 helpers, ~40 LOC); `parse_post_id` grew the 18-digit cap.
- `src/account.cyr` `post_from` grew the re-validate tail (handle_valid + fp16_valid; on fail → clear outputs + return 0).
- `src/main.cyr` `cmd_post` grew the `--subject` C0-control gate; `cmd_list` + `cmd_read` grew the `--board` validation; new globals `g_login_started_ms` + `AgoraLogin.LOGIN_DEADLINE_MS`; `login` command sets the timestamp; MODE_LOGIN_AWAIT_SIG dispatch checks the deadline before signature work.
- `src/test.cyr` grew 8 regression tests (t71-t78).

### Documentation

- New `docs/audit/2026-05-23-audit.md` — full audit report. Severity rubric (CRITICAL/HIGH/MEDIUM/LOW/DOCUMENTED), per-finding repro/fix, external CVE review table, 0.7.x fix slate, 0.8 deferred items. First entry in the `docs/audit/` ledger; cadence per CLAUDE.md § Security Hardening = once per minor / pre-release.

## [0.6.0] — 2026-05-23 (M6 close — sigil-backed auth + per-board policy)

agora is now a **multi-board threaded BBS with sigil-backed identity and operator-configurable per-board posting policy**. The full M6 cycle ships: six bites + one ADR landed between 0.5.0 and 0.6.0. Authenticated users can post under their handle (with a `From: <handle> <fp16>` header on disk); anonymous users can still read freely but cannot post (default policy `open` still requires auth); operators can tighten any board to `known` (registered-users-only) or `admin` (handles listed in `<board>/.admins` only).

### Bites + ADR in this release

- **M6-A** + [ADR 0006](docs/adr/0006-identity-model.md) — identity model: sigil Ed25519, `<store>/.users/<fp16>/` per-user dir, challenge/response wire flow (`"agora-login:" + nonce_hex` signed payload), anon-read + auth-post default, `From: <handle> <fp16>` header, 32-byte raw seed keyfile at `~/.agora/key`.
- **M6-B** — account primitives in `src/account.cyr` (~230 LOC): fingerprint computation, handle validation, path builders, `account_register` / `account_lookup_*` / `account_resolve_handle`.
- **M6-C** — telnet `login <handle>` + `MODE_LOGIN_AWAIT_SIG` + challenge/response wire flow + `parse_auth_sig` / `format_challenge_msg` / `nonce_random` / `nonce_to_hex` helpers.
- **M6-D** — `agora keygen` / `agora register` / `agora whoami` CLI verbs + telnet `whoami` command + keyfile primitives (`keyfile_generate` / `keyfile_load_seed` / `seed_to_pk` / `keyfile_to_fingerprint`).
- **M6-E** — `From:` header on authenticated posts; CLI `--as <handle>`; wire-side auth-post gate; `post_from` extractor; `list` and `read` rendering across CLI + telnet show `[handle|anon]` / `From:` lines.
- **M6-F** — per-board posting policy via `<store>/<board>/.policy` (`open` / `known` / `admin`) + `<store>/<board>/.admins`; `BoardPolicy` enum + `board_policy_get` / `board_admin_check` / `board_can_post` decision-point primitive.

### Changed

- `VERSION` bumped 0.5.0 → 0.6.0.
- `print_banner` / `cmd_version` / `render_motd` version line all bumped to 0.6.0 (CI's drift check verifies the inline literals match `VERSION`).
- `cyrius.cyml [deps].stdlib` grew **three modules**: `sigil` (Ed25519 / SHA-256 / hex), `freelist` (sigil's heap-context primitives), `bigint` + `ct` (sigil's Ed25519 verify call chain needs the u256 + constant-time primitives — would SIGILL at runtime without them). 16 modules at 0.5.0 → 20 at 0.6.0.
- `post_format_with_headers` signature grew `from_handle` + `from_fp` params (8 args at 0.6.0; was 6 at 0.5.0). `post_new_with_subject_reply` likewise grew the two params. Backwards-compat wrappers (`post_format_with_subject`, `post_new_with_subject`) pass 0/0 for both.
- New session modes / globals in `src/main.cyr`: `MODE_LOGIN_AWAIT_SIG = 3`, `g_session_fp`, `g_session_handle`, `g_login_fp`, `g_login_nonce`.

### Verified

- **70/70 tests pass** from a clean `rm -rf build && cyrius deps && cyrius build` (was 49 at 0.5.0; +21 tests for M6-B/C/D/E/F: fingerprint, handle validation, path builders, nonce/hex helpers, auth-sig parser, RFC 8032 test-vector-1, From-header round-trip, policy paths, anonymous-deny early-return).
- **Bench baseline unchanged** (parser hot path is content-agnostic — M6 is application-layer):
  | Benchmark | 0.5.0 | 0.6.0 |
  |---|---:|---:|
  | `telnet/plain_byte` | 10–11 ns | **10 ns** |
  | `telnet/iac_untracked` | 63 ns | **64 ns** |
  | `telnet/iac_tracked_agree` | 73 ns | **74 ns** |
  | `telnet/subneg_naws` | 97–107 ns | **99 ns** |
  | `telnet/announce_salvo` | 132 ns | **132 ns** |
- **Security re-scan** (M6 surfaces, per CLAUDE.md Security Hardening §1-7):
  - **No `sys_system`** — zero command-injection surface.
  - **Buffer sizes**: all M6 `var buf[N]` allocations match their fill size (32 for pk/seed/digest, 64 for sig, 24 for fmt_int_buf, 76 for the LOGIN_MSG_LEN message, etc.).
  - **Path resolution**: every path constructed via builders (`build_user_dir`, `build_user_file`, `board_policy_path`, `board_admins_path`) whose user-controlled tokens (`handle`, `board`) are pre-validated by `handle_valid` / `board_name_valid` at ingress. Fingerprints are derived from `sha256(pk)` and always-16-lowercase-hex by construction. File-name component is always a hard-coded literal.
  - **Sig hex validated**: `hex_is_valid` + length check before `hex_decode` in `parse_auth_sig`. Malformed bytes → `login failed (malformed auth)`.
  - **Keyfile**: `O_CREAT | O_EXCL` (refuses to overwrite existing) + mode 0o600 at creation. Server holds only public keys; secret material never crosses the wire.
  - **Domain-separated signing input**: `"agora-login:"` prefix prevents the sigil keypair being tricked into signing payloads for other protocols.
  - **Single-use nonces**: cleared on every `auth:` attempt (pass or fail), preventing replay.
- **Dead-code audit**: DCE NOPs **675 unreachable fns** (~160 KB) — entirely sigil's PQC / keccak / hashmap_fast / thread paths we never call. None of agora's own code is unreachable from the entry points.
- **Full clean rebuild** (`rm -rf build && cyrius deps && cyrius build`) passes clean.
- **Version verify**: `VERSION` = `cat VERSION` = `./build/agora --version | head -1` = intended git tag `0.6.0` (manual; CI's drift-check workflow enforces this).
- **End-to-end smoke** across every M6 bite — see per-bite entries below for the verified scenarios (keygen + register + login + post + reply + whoami + policy enforcement, both CLI and telnet sides, openssl 3.x ↔ sigil 3.1.1 Ed25519 interop confirmed).

### Binary growth

| Tag | Size | Cycle |
|---|---:|---|
| 0.1.0 | 43 KB | M0 scaffold |
| 0.2.0 | 71 KB | M1 close |
| 0.3.0 | 86 KB | M2 close |
| 0.4.0 | 129 KB | M5 partial |
| 0.5.0 | 140 KB | M5 close |
| **0.6.0** | **375 KB** | **M6 close** |

+235 KB across the M6 cycle. ~165 KB of that is sigil's unreachable PQC / keccak / hashmap_fast / thread surface (NOPed under DCE); the actual M6 code adds ~70 KB across `src/account.cyr` (~280 LOC including login + keyfile + From helpers + policy primitives) and the wire/CLI integration in `src/main.cyr`. Real binary strip remains a v1.x close-out concern per state.md.

### Added — M6-F: per-board posting policy (`open` / `known` / `admin`) (2026-05-23)

- **New on-disk policy files** per ADR 0006 § Specifics:
  - **`<store>/<board>/.policy`** — one of literal `open` / `known` / `admin` (trailing CR/LF/whitespace tolerated). Missing file defaults to `open`. `<store>/.policy` for the main board.
  - **`<store>/<board>/.admins`** — one handle per line; blank lines and `#`-comment lines ignored; leading + trailing whitespace trimmed per line. Only consulted when `.policy == admin`.
  - Operator sets both by editing the files directly (`echo known > <store>/<board>/.policy`). No CLI verb at first cut; a future bite earns `agora policy set <board> <mode>` if real deployments demand it.
- **New primitives in `src/board.cyr`** (~150 LOC):
  - `BoardPolicy` enum: `POLICY_OPEN = 0`, `POLICY_KNOWN = 1`, `POLICY_ADMIN = 2`.
  - `board_policy_path(store, board, out)` / `board_admins_path(store, board, out)` — path builders mirroring the `board_path` + dotfile-suffix shape (precedent: `.lock`, `.users/`).
  - `board_policy_get(store, board)` — reads `.policy`, trims trailing whitespace, parses one of `open` / `known` / `admin`. Missing / unparseable → `POLICY_OPEN`.
  - `board_admin_check(store, board, handle)` — reads `.admins` (up to 4 KB), scans line-by-line, trims per-line whitespace, skips blank + `#`-comment lines, returns 1 if `handle` matches any entry. Up to 4 KB of `.admins` = ~120 handles of typical length; lift the ceiling when a deployment hits it.
  - `board_can_post(store, board, session_fp, session_handle)` — single decision point. Anonymous (NUL / empty `session_fp`) always denied. `open` allows any auth. `known` re-verifies the fingerprint via `account_lookup_pubkey` (guards against stale sessions whose user was unregistered out-of-band). `admin` requires non-empty handle in `.admins`.
- **`open` vs `known` at M6** are functionally identical (every authenticated session at M6 has a locally-registered handle — `login` resolves through `<store>/.users/`). The distinction is forward-compat for federation (v2.x pillar 1): `open` would also accept federated identities not registered locally.
- **Wire-side enforcement** in `session_execute`: `post` / `reply` commands replace the bare `g_session_fp` check with `board_can_post(...)`. Policy-aware error messages — `auth required — run 'login <handle>' first` for anonymous, `post denied by board policy (admin-only or unregistered)` for authenticated-but-denied.
- **CLI enforcement** in `cmd_post`: same `board_can_post(...)` gate using `--as`-derived identity (or 0/0 for anonymous CLI posts). Anonymous CLI posts continue to work on `open`-policy boards (default = `open` = backwards-compat with 0.5.x); tightening the operator surface is what policy is for.
- **Tests grew 66 → 70**: `t67_board_policy_path_main` / `t68_board_policy_path_named` / `t69_board_admins_path_named` (path builders verbatim with NUL terminators), `t70_can_post_anonymous_denied` (NUL ptr + empty cstring both reject without touching the filesystem — early-return correctness check).
- **End-to-end smoke** (7 cases, 2 keypairs alice/bob in one store with `main` open / `closed` known / `ops` admin-with-alice-only):
  1. alice → main (open) → allow.
  2. bob → closed (known) → allow (bob registered).
  3. bob → ops (admin, not listed) → DENY ("denies this post").
  4. alice → ops (admin, listed) → allow.
  5. Anonymous CLI → closed (known) → DENY ("requires authentication").
  6. Tighten main to admin with no .admins file → even alice DENY (no one is admin).
  7. Wire-side: bob logged in via challenge/response, enters ops, tries `post` → `post denied by board policy (admin-only or unregistered)`. **PASS.**
- **Binary growth**: 370,528 B (M6-E) → final M6 size (see closeout).
- **Backwards compat**: existing 0.5.x stores with no `.policy` files behave exactly as before (default `open`). Operators upgrade in place with zero data migration; tightening is opt-in per-board.

### Added — M6-E: `From:` header on posts + CLI `--as` + auth-post gate (2026-05-23)

- **`post_format_with_headers` signature grew** `from_handle` + `from_fp` parameters (both cstrings; either-null = no header / anonymous post). Worst-case header overhead bumped to ~140 bytes accounting for the `From: <32-byte-handle> <16-hex-fp>\r\n` line. `post_new_with_subject_reply` got the same two new params; `post_format_with_subject` and `post_new_with_subject` wrappers pass 0/0 for both. Per ADR 0006 § Specifics — `From: <handle> <space> <fp16-hex>` two-token format.
- **New helper `post_from(buf, len, handle_out, h_max, fp_out, fp_max)`** in `src/account.cyr` — extracts `From:` value, splits on first space, NUL-terminates handle + fp into caller buffers. Returns 1 on success, 0 if no From header / malformed (no space) — caller renders "[anon]" / "anonymous".
- **Wire-side auth gate**: `post` and `reply` commands in `session_execute` check `g_session_fp`; if anonymous, reply `auth required — run 'login <handle>' first\r\n` and stay in `MODE_COMMAND`. ADR 0006 § P1 default-policy fulfillment.
- **`session_finalize_post` reads `g_session_handle` + `g_session_fp`** when the session is authenticated, passes them through to `post_new_with_subject_reply`. Anonymous sessions can't reach this path (auth gate above) but the function still tolerates 0/0 for backward-compat with future CLI-driven flows.
- **CLI `agora post --as <handle> [--key <path>]`** — when `--as` is given, the CLI loads the keyfile (default `~/.agora/key`), derives the fingerprint via `keyfile_to_fingerprint`, looks up the handle in the store (`account_resolve_handle`), and refuses if the handle isn't registered or is registered to a different fingerprint. Anonymous CLI posts (no `--as`) keep the 0.5.x shape — no `From:` header on disk.
- **`list` rendering** (CLI + telnet) updated to `<id>  [<handle>]  <subject>` — `[anon]` for posts with no `From:` header (legacy 0.4/0.5 posts + anonymous new posts).
- **`read <id>` rendering** (CLI + telnet) prepends `From: <handle> <fp16>\r\n` (or `From: anonymous\r\n` when no header) before the existing `Subject:` line.
- **New CLI helper `parse_as_flag`** mirrors the `--store` / `--subject` / `--key` / `--handle` parsers. `first_positional_after_verb` already skips any `--*` pair generically, so the new flag doesn't shadow `read <id>`.
- **Tests grew 63 → 66**: `t64_format_with_from_header` (formatter writes the literal `From: alice deadbeef12345678` line), `t65_post_from_extracts` (round-trip: format with handle+fp → parse handle+fp out), `t66_post_from_absent_is_anonymous` (no-header case zeroes both out buffers + returns 0).
- **Test fix**: `t49_format_with_reply_to_header` updated for the new 8-param signature of `post_format_with_headers` (passes 0,0 for from_handle/from_fp). t49 was crashing with SIGSEGV on the old 6-arg call site before the fix — caught by the test suite before the bite was claimed done.
- **End-to-end smoke** (8 cases): keygen + register `alice` → CLI anon post (id 1, no `From:` on disk) → CLI `--as alice --key …` post (id 2, `From: alice 8a708167937a0a86` on disk) → CLI `--as bob` rejected (`handle is not registered`) → `list` shows `1  [anon]  anon post` / `2  [alice]  alice post` → `read 1` shows `From: anonymous` → `read 2` shows `From: alice 8a708167937a0a86` → telnet anonymous-session `post` blocked with `auth required — run 'login <handle>' first`. **PASS.**
- **Binary growth**: 366,080 B (M6-D) → 370,528 B (this bite, +4.4 KB).
- **Backwards compat**: existing 0.4 / 0.5 posts and 0.5/0.4 stores transparent — missing `From:` continues to mean anonymous; `list` shows `[anon]` and `read` shows `From: anonymous` exactly as if the post were freshly anonymous. No data migration.

### Added — M6-D: keygen / register / whoami (CLI + telnet) (2026-05-23)

- **New CLI verbs**:
  - **`agora keygen [--key <path>]`** — generates a fresh 32-byte Ed25519 seed via `/dev/urandom`, writes to `<path>` (default `$HOME/.agora/key`, fallback `./agora.key`) with `O_CREAT | O_EXCL` and mode `0o600`. Refuses to overwrite. Auto-mkdir's the parent (`ensure_parent_dir`). Prints `wrote keyfile <path> (fp <fp16>)`.
  - **`agora register --handle <h> [--key <path>] [--store <path>]`** — loads the keyfile seed, derives the pubkey via `seed_to_pk` (sigil `ed25519_keypair`), validates the handle (lowercase + digit alphabet, 1-32 bytes, not `anonymous`/`system`/`admin`), checks via `account_resolve_handle` that the handle isn't squatted by a different fingerprint (idempotent re-register OK if same fp), then `account_register`. Prints `registered <handle> <fp16>`.
  - **`agora whoami [--key <path>] [--store <path>]`** — decodes the keyfile, derives the fingerprint, optionally looks up the handle in `<store>`. Prints `<handle?> <fp16>` (handle omitted when no `--store` or no registration). Returns 1 if the keyfile cannot be read.
- **New telnet command** `whoami` in `session_execute` — prints `<handle> <fp16>` for an authenticated session, or `anonymous` for an unauthenticated one. Help text updated.
- **New account-side primitives in `src/account.cyr`**:
  - `keyfile_load_seed(path, seed_out)` — reads exactly 32 bytes; -1 on missing / wrong-size / read error.
  - `seed_to_pk(seed_buf, pk_out)` — wraps sigil's `ed25519_keypair`, writes only the 32-byte pubkey (caller doesn't usually need the sk).
  - `keyfile_to_fingerprint(path, fp_out)` — convenience: keyfile path → 16-hex fingerprint.
  - `keyfile_generate(path)` — `nonce_random_into` → 32-byte seed → `O_WRONLY|O_CREAT|O_EXCL` write with mode `0o600`. Refuses to overwrite existing files.
  - `nonce_random_into(out, want)` — generalized `/dev/urandom` reader; `nonce_random` now wraps this with `want = ACCOUNT_NONCE_BYTES`.
- **New constants** in `AccountCap` / `AccountLogin` / etc.: `ACCOUNT_PERM_KEYFILE = 0x180` (0o600).
- **ADR 0006 update** — keyfile format clarified to **32 bytes (raw seed)** instead of the original "96 bytes — seed || sk" sketch. sk is derived on load via `ed25519_keypair`; the seed is the minimum canonical form (also what `ssh-keygen -t ed25519` stores internally). Backwards-compat note added.
- **Tests grew 61 → 63**: `t62_seed_to_pk_rfc8032_v1` (RFC 8032 test-vector-1: seed `9d61b19d…7f60` → pubkey `d75a9801…511a`), `t63_fingerprint_of_rfc8032_v1_pk` (fp = `21fe31dfa154a261`). Added inline `t_hex2` / `t_hex_load` helpers so test files can carry hex-literal vectors without depending on `hex_decode`.
- **End-to-end smoke** — 8 CLI cases + 3 telnet whoami cases:
  1. `keygen` writes a 32-byte file mode 0600.
  2. `keygen` again refuses to overwrite (rc 1).
  3. `whoami --key <path>` (no `--store`) prints just the fingerprint.
  4. `register --handle alice --store /tmp/m6d_store` writes `.users/<fp>/` with all three files.
  5. `whoami --key <path> --store /tmp/m6d_store` prints `alice <fp>`.
  6. `register` again with same key+handle is idempotent (rc 0, same fp).
  7. `register --handle Bad-Caps` rejected (rc 2, invalid).
  8. `register --handle admin` rejected (rc 2, reserved).
  9. Telnet `whoami` from anonymous session → `anonymous\r\n`.
  10. `login alice` + auth round-trip (re-using openssl pkeyutl pipeline from M6-C, with the 32-byte seed wrapped in the standard Ed25519 PrivateKeyInfo DER prefix to feed openssl: `30 2e 02 01 00 30 05 06 03 2b 65 70 04 22 04 20 || seed`) → `welcome, alice`.
  11. Telnet `whoami` post-login → `alice <fp16>\r\n`. **PASS.**
- **Binary growth**: 351,248 B (M6-C) → 366,080 B (this bite, +14.8 KB for the three new CLI verbs + helpers + getenv path).
- **`default_key_path` honors `$HOME`** via `lib/io.cyr`'s `getenv` (reads `/proc/self/environ`); falls back to `./agora.key` if unset. Operators on macOS / non-Linux platforms with HOME set still resolve via the standard fallback once `getenv` lands on those platforms.

### Added — M6-C: telnet `login` + challenge/response wire flow (2026-05-23)

- **New session mode `MODE_LOGIN_AWAIT_SIG = 3`** in `src/main.cyr` — parked-challenge state between `login <handle>` and the client's `auth: <hex>` reply.
- **Per-session globals**: `g_session_fp` / `g_session_handle` (bound identity, empty cstring = anonymous); `g_login_fp` / `g_login_nonce` (parked challenge state, cleared on every auth attempt + session start). Allocated per-connection in `handle_client`, mirrors the single-tracking caveat documented on `g_reply_to`.
- **`login <handle>` command** in `session_execute`:
  - Resolve `<handle>` → fingerprint via `account_resolve_handle` (M6-B). Unknown handle → "unknown user", session stays anonymous.
  - Generate 32-byte random nonce via `/dev/urandom` (`nonce_random` in account.cyr).
  - Hex-encode nonce (`nonce_to_hex`); send `challenge: <64-hex>\r\n` + reply-format hint.
  - Park `(fp, nonce_hex)` in `g_login_fp` / `g_login_nonce`; return `MODE_LOGIN_AWAIT_SIG`.
- **`MODE_LOGIN_AWAIT_SIG` branch in `handle_client`** (eol-dispatch chain):
  - `parse_auth_sig(line, line_pos, sig_raw)` extracts 64-byte sig from `auth: <128-hex>` (tolerates the optional single space after colon).
  - `account_lookup_pubkey(store, g_login_fp, pk_buf)` fetches the 32-byte registered pubkey.
  - `format_challenge_msg(g_login_nonce, msg)` writes the 76-byte signed payload (`"agora-login:" + nonce_hex`, ADR 0006's domain-separation prefix).
  - `ed25519_verify(pk, msg, 76, sig)` decides pass/fail.
  - Pass: bind `g_session_fp` + `g_session_handle` from the parked fp + lookup, send `welcome, <handle>`, return to `MODE_COMMAND`.
  - Fail (malformed auth / pubkey lookup error / signature mismatch): clear parked state, send specific failure message, return to `MODE_COMMAND` anonymous.
  - **Single-use nonce**: `g_login_nonce` cleared on every auth attempt, pass or fail.
- **New account-side primitives in `src/account.cyr`**:
  - `nonce_random(out_buf)` — 32 bytes from `/dev/urandom` (entropy failure returns -1, mirrors sigil's `generate_keypair` shape).
  - `nonce_to_hex(in_buf, out_buf)` — 32 raw bytes → 64 hex chars + NUL.
  - `format_challenge_msg(nonce_hex, out_buf)` — `"agora-login:" + nonce_hex` (76 bytes, NOT NUL-terminated; caller passes length to `ed25519_*`).
  - `parse_auth_sig(line, line_len, sig_out)` — validates `auth:` prefix + optional space + exact 128-hex chars + hex-decode; returns 64 on success, -1 on malformed.
  - New constants: `LOGIN_PREFIX_LEN = 12`, `LOGIN_MSG_LEN = 76`.
- **`cyrius.cyml [deps].stdlib`** — added `bigint` + `ct` (sigil's Ed25519 verify needs the u256 + constant-time primitives from bigint/ct.cyr; without them the verify call hit unimplemented-function SIGILL at runtime). 18 modules at M6-B → 20 at this bite.
- **Tests grew 56 → 61**: `t57_nonce_to_hex_known` (input bytes 0x00..0x1F → expected hex), `t58_format_challenge_msg` (prefix + nonce tail), `t59_parse_auth_sig_valid` (128-hex round-trip), `t60_parse_auth_sig_rejects` (NUL ptr / empty / too short / wrong prefix / 127 hex / non-hex char), `t61_parse_auth_sig_no_space` (tolerates `auth:00...` without space).
- **End-to-end smoke (CLI + openssl + python)**:
  1. `openssl genpkey -algorithm ed25519` → 32-byte raw pubkey extracted from DER output.
  2. Fingerprint = `sha256(pk)[:8]` hex; pre-registered `<store>/.users/<fp>/{public_key.bin, handle, created.iso8601}`.
  3. Connect → `login alice` → server emits `challenge: <64-hex>\r\n`.
  4. Client signs `"agora-login:" + nonce_hex` via `openssl pkeyutl -sign -rawin`.
  5. Send `auth: <128-hex>\r\n` → server replies `welcome, alice\r\n> `. **PASS.**
  - Failure paths verified: `login nobody` → `unknown user`; `auth: <128-hex of wrong sig>` → `login failed (signature)`.
- **Sigil interop**: openssl 3.x's pure-Ed25519 sign output (`-rawin`) verifies cleanly with sigil's `ed25519_verify` — confirms both implement RFC 8032 PureEdDSA correctly.
- **Help text** updated to document `login <handle>`.
- **Binary growth**: 332,552 B (M6-B) → 351,248 B (this bite). +18.6 KB for the login dispatch path + bigint/ct surface that sigil's ed25519_verify call chain pulls in.
- **Deferred to a polish follow-up**: 30 s deadline on the parked challenge. Today's `sock_set_recv_timeout(60s)` slowloris defense kills idle sockets, which incidentally drops any stale parked nonce — the explicit deadline is hardening, not correctness.

### Added — M6-B: account primitives in `src/account.cyr` (2026-05-23)

- **`src/account.cyr`** (~230 LOC) — per-user identity primitives per ADR 0006:
  - `compute_fingerprint(pk_buf, out_buf)` — `hex(sha256(pk))[0:16]` via sigil's `sha256` + inline hex encoder. Writes 16 lowercase hex chars + NUL.
  - `handle_valid(name)` — same alphabet as `board_name_valid` (lowercase ASCII / digits / `-` / `_`, first char letter or digit, 1-32 bytes) but different reserved set (`anonymous`, `system`, `admin`).
  - `build_users_dir(store, out_buf)` / `build_user_dir(store, fp16, out_buf)` / `build_user_file(store, fp16, file_name, out_buf)` — path builders mirroring `board_path` / `build_post_path` shape.
  - `account_dir_ensure(store, fp16)` — mkdir `<store>` + `<store>/.users` + `<store>/.users/<fp16>` (EEXIST as success at every level).
  - `account_register(store, pk_buf, handle, fp_out)` — writes `public_key.bin` (32 bytes raw) + `handle` (UTF-8 + LF) + `created.iso8601` (chrono now + LF). Computes fp from pk; caller pre-checks handle uniqueness via `account_resolve_handle`.
  - `account_lookup_pubkey(store, fp16, pk_out)` — reads `public_key.bin` into pk_out.
  - `account_lookup_handle(store, fp16, out_buf, out_max)` — reads `handle` file, strips trailing CR/LF (flag-driven trim per CLAUDE.md no-`break`-with-`var` rule), NUL-terminates.
  - `account_resolve_handle(store, handle, fp_out)` — O(n) scan of `<store>/.users/`, returns 1 + writes fingerprint on match, 0 on not-found. Same scan-on-read shape as `replies_to` (ADR 0005).
- **`cyrius.cyml [deps].stdlib`** — added `sigil` (bundled 3.1.1 from the cyrius 6.0.1 snapshot; ed25519 + sha256 + hex are the surface we consume) and `freelist` (`fl_alloc` / `fl_free` are sigil's `sha256_init` / `sha256_finalize` heap-ctx primitives). 16 modules at 0.5.0 → 18 at this bite.
- **Tests grew 49 → 56**: `t50_compute_fingerprint_known_pk` (sha256(zeros32) prefix == `66687aadf862bd77`), `t51_compute_fingerprint_deterministic` (two calls on same pk match), `t52_handle_valid_accepts` (canonical alphabet incl. 32-char ceiling), `t53_handle_valid_rejects` (NUL ptr, empty, reserved set, uppercase, dot, slash, leading dash/underscore, space, 33-char overflow), `t54_build_users_dir_shape` / `t55_build_user_dir_shape` / `t56_build_user_file_shape` (path formats verbatim with NUL terminators).
- **Note on bundled sigil version**: state.md cited sigil 3.4.3 (the standalone repo's tip) as the gate target; the cyrius 6.0.1 toolchain snapshot bundles 3.1.1, which provides the same Ed25519 + SHA-256 + hex surface we need for M6. Updated state.md gate row to reflect the bundled version.
- **Binary growth**: `build/agora` 140,160 B (0.5.0) → 332,552 B (this bite). +192 KB for sigil + freelist; ~165 KB of that is unreachable-but-NOPed (PQC / keccak / hashmap_fast / thread paths sigil declares but we never call). Real binary strip is a v1.x close-out concern per state.md. Net cost for actually-used code: ~27 KB for ed25519 + sha256 + hex + account.cyr.
- **Sigil-imported warnings**: build emits ~25 "undefined function" warnings for sigil's PQC + keccak + hashmap_fast + thread call sites; all are unreachable from the agora-side call graph (ed25519_sign / ed25519_verify / sha256 / hex_encode are the only sigil entry points we invoke). Documented here so future bites don't re-investigate.

### Added — M6-A: ADR 0006 — identity model (2026-05-23)

- **[ADR 0006](docs/adr/0006-identity-model.md)** — opens the M6 cycle. Captures six load-bearing decisions: (A) sigil Ed25519 as the identity primitive; (X) `<store>/.users/<fp16>/` per-user directory (public_key.bin + handle + created.iso8601); (p) challenge/response wire flow (server emits 32-byte nonce, client signs `"agora-login:" + nonce_hex`, server verifies via `ed25519_verify` against the registered pubkey); (P1) anon-read + auth-post default; `From: <handle> <fp16>` header on authenticated posts (missing From == anonymous, backwards-compat with M5 posts); CLI gains `agora whoami` + `agora keygen` + `agora register` + `agora post --as` with `~/.agora/key` as the default keyfile location.
- Rejects five alternatives with concrete reasoning: ML-DSA-65 at first cut (gated behind `-D SIGIL_PQC`, 1.2 KB sigs), password hashes (cleartext-on-wire over telnet has no defensible flow), fully sigil-managed account store (per-deployment user lists scatter across home dirs), `users.cyml` sidecar (two-file invariant — anti-pattern rejected at every prior ADR layer), federated identity at M6 (v2.x pillar 1, requires content-addressing graduation to be coherent).
- Fingerprint: `hex(sha256(public_key))[0:16]` — 64 bits, comfortable at ~10s of users per deployment; lengthening to 32 hex chars is a non-breaking forward-compatible change if a future deployment needs it.
- Per-board posting policy ships in M6-F: per-board `.policy` file (one of `open` / `known` / `admin`), per-board `.admins` for the admin mode. Missing `.policy` defaults to `open` (any authenticated user can post).
- No code in this bite — ADR-only. Subsequent bites (M6-B through M6-F) implement the decisions.

## [0.5.0] — 2026-05-23 (M5 close — boards + threads)

agora is now a **multi-board threaded BBS over telnet**. The full M5 cycle ships: six bites + four ADRs landed between 0.4.0 and 0.5.0. Single-board posting (0.4.0) becomes multi-board threaded conversation (0.5.0) without any user-visible data migration — the 0.4.0 flat-root layout is the implicit "main" board.

### Bites + ADRs in this release

- **M5-E (boards)** + [ADR 0004](docs/adr/0004-board-layout.md) — flat-root = "main", subdirs = named. Telnet `boards` / `enter <name>` / `leave` + CLI `--board <name>`. Per-board ID counter + lockfile.
- **M5-F (threads)** + [ADR 0005](docs/adr/0005-threading-via-reply-to.md) — `Reply-To: <id>` header, same-board, scan-on-read. Telnet `reply <id>` (auto Re: subject) + `read <id>` shows `Replies: N, M, ...`. CLI `--reply-to <id>`.

### Changed

- `print_banner` / `cmd_version` / `render_motd` version line bumped to 0.5.0.
- `cyrius.cyml [deps].stdlib` unchanged at 16 modules (M5-E/F added no new deps).

### Verified

- 49/49 tests pass from a clean build.
- Bench baseline (telnet/plain_byte 11 ns, telnet/subneg_naws 107 ns) consistent with 0.4.0 — M5-E/F is content-layer work, doesn't touch the IAC parser hot path.
- Security re-scan: board name validator + Reply-To parser bound external input; scan-on-read replies enumeration bounded by `DIRENT_ID_MAX`; no command injection; no orphans.
- End-to-end smoke (CLI + telnet): post + reply chain; on-disk file shows Reply-To header; `read 1` shows `Replies: 2, 3`; `reply 1` derives Re: subject and writes Reply-To.

### Added — ADR 0005 + M5-F: threading via Reply-To (2026-05-23) — **M5 close**

This bite closes M5. agora is now a **multi-board threaded BBS over telnet** — the post storage cycle that opened with ADR 0002 / M5-A / 0.4.0 reaches feature completeness with same-board reply linkage. Next release tag will be **0.5.0** (M5 close + roadmap restructure documented under 0.4.0).

- **[ADR 0005](docs/adr/0005-threading-via-reply-to.md)** — captures three load-bearing decisions: (A) reply relationship encoded as a `Reply-To: <id>` header in the RFC-822 block from ADR 0003; (α) same-board only (cross-board upgrade path documented as non-breaking); (p) scan-on-read for enumeration (O(n) per read, fine at v1.0 scale; mitigations available if scale grows). Rejects deep-threading via `In-Reply-To`+`References`, sidecar reply index, and fully-qualified `<board>/<id>` Reply-To values with concrete reasoning.
- **`src/board.cyr` additions**:
  - `post_format_with_headers(subject, reply_to, body, body_len, out, cap)` — extends ADR 0003's header block with an optional `Reply-To: <id>\r\n` line when `reply_to > 0`. The original `post_format_with_subject` becomes a thin wrapper passing `reply_to == 0`.
  - `post_new_with_subject_reply(store, board, subject, reply_to, body, body_len)` — wraps `post_format_with_headers` + the M5-G EXCL+flock claim. Same critical-section shape as M5-D's `post_new_with_subject`.
  - `post_reply_to(buf, len)` — extract parent ID from a post file's `Reply-To` header. Returns 0 when absent / unparseable / headerless.
  - `replies_to(store, board, parent_id, out_ids, max)` — scan the board's posts, accumulate IDs whose `Reply-To` matches `parent_id`. Returns sorted-ascending count.
  - `subject_reply_prefix(parent_subject, parent_len, out, max)` — RFC 5322 § 3.6.5 Re: rule: prepend "Re: " unless already present (case-insensitive on the letters). Never doubled.
- **Telnet `reply <id>`** command — validates parent exists in current board, derives Re-prefixed subject, **skips the Subject prompt**, transitions straight to MODE_POSTING. Parked state in globals (`g_reply_to`, `g_reply_subject`, `g_reply_subject_len`) is read by `session_finalize_post` on '.' commit and cleared after each post.
- **Telnet `read <id>`** appends `Replies: N, M, ...` after the body when any posts in the current board target this post. Silent when no replies.
- **CLI `agora post --reply-to <id>`** flag. When `--reply-to` is given without `--subject`, the CLI auto-derives the Re: subject from the parent (matching the wire-side reply UX).
- **Tests 43 → 49** (6 new): `t44_subject_reply_prefix_adds_re`, `t45_subject_reply_prefix_no_double_re` (RFC 5322 no-double rule), `t46_subject_reply_prefix_case_insensitive` (lowercase + mixed-case `re:`), `t47_post_reply_to_extracts_id`, `t48_post_reply_to_missing_returns_zero` (absent header + headerless), `t49_format_with_reply_to_header` (round-trip via `post_format_with_headers` ↔ `post_reply_to`).
- **End-to-end smoke** — CLI: `post`/`post --reply-to 1` chain; on-disk file shows Reply-To header. Telnet: `read 1` shows `Replies: 2, 3`; `reply 1` derives `Subject: Re: ...` automatically and writes Reply-To header; `list` displays the new reply; `read 1` reflects the new reply count.
- **Binary**: 135,064 B (M5-E) → 140,152 B (+5,088 B for the threading primitives, reply command, replies-list rendering, and CLI --reply-to plumbing).

**M5 cycle summary** (six bites + two ADRs, ready for 0.5.0 tag):
- M5-A storage primitives (ADR 0002)
- M5-B in-session command interpreter
- M5-C sorted listing
- M5-D RFC-822 headers (ADR 0003)
- M5-G per-store flock
- M5-H ingress input filter
- M5-E boards (ADR 0004)
- M5-F threading (ADR 0005)

### Added — ADR 0004 + M5-E: boards (2026-05-23)

agora is now a **multi-board BBS over telnet**. New session model: every connection opens at the implicit "main" board (flat `<store>/` per 0.4.0 layout); `enter <name>` switches to a named board (`<store>/<name>/`); `leave` returns to main. The prompt shows `[name] >` when in a named board so the user always knows which board their next command targets.

- **[ADR 0004](docs/adr/0004-board-layout.md)** — captures three load-bearing decisions: layout (flat-root = "main", subdirs = named — free backwards compat with 0.4.0 stores), UI (modal current-board for telnet, `--board` flag for CLI), lifecycle (auto-create on first post). Rejects three alternatives (all-boards-as-subdirs migration, sidecar index, per-port-board UI) with concrete reasoning.
- **`src/board.cyr` refactor** (~150 LOC):
  - `board_path(store, board, out)` — resolves to `<store>` for "main", `<store>/<board>` for named.
  - `board_name_valid(name)` — validates per ADR 0004 (1-32 bytes, lowercase ASCII + digits + '-' / '_', first byte letter or digit, "main" reserved).
  - `board_ensure(store, board)` — mkdir the per-board subdir (and `<store>` itself) treating EEXIST as success.
  - `boards_list(store, out, max)` — enumerate named subdirectory-shaped boards; filters post files + lockfile + hidden entries.
  - **Every existing primitive grew a `board` parameter** — `post_new`, `post_new_with_subject`, `post_read`, `post_list`, `post_max_id`, `store_lock_acquire`, `build_post_path`. Each board has its own ID counter + its own lockfile.
- **`src/main.cyr` wire integration** (~200 LOC):
  - New session state `current_board` (per-connection NUL-terminated cstring buffer, default "main").
  - New commands: `boards` (list main + named, with per-board post counts), `enter <name>` (switch board; auto-creates), `leave` (return to main).
  - `send_prompt` helper — bare `> ` in main, `[name] > ` in a named board.
  - `help` text updated; `session_execute` signature grew `current_board` parameter; `session_finalize_post` grew `current_board` parameter.
- **CLI `--board <name>` flag** on all three verbs (`post` / `list` / `read`). Default `main`. `parse_board()` helper mirrors the `--store` / `--subject` shape. `first_positional_after_verb` updated to skip any `--<flag> <value>` pair so the positional ID arg in `read` doesn't get shadowed.
- **Per-board lock + ID counter granularity** — concurrent writers to different boards never contend with each other. `<store>/<board>/.lock` per board (and `<store>/.lock` for main).
- **Tests grew 38 → 43**: `t39_build_post_path_named_board` (subdirectory path shape), `t40_board_name_valid_accepts` (canonical alphabet), `t41_board_name_valid_rejects` (uppercase, dot, slash, leading dash/underscore, reserved "main", over-length), `t42_board_path_main_is_flat`, `t43_board_path_named`.
- **End-to-end smoke** — five-case verification:
  1. Backwards-compat: legacy 0.4.0 flat store reads `list` + `read` correctly via the `main` resolution
  2. CLI `--board art` posts land in `<store>/art/` with their own ID counter
  3. Invalid board name (`BAD-Caps`) rejected at CLI ingress
  4. On-disk layout matches ADR (main posts at root, art posts in subdir, per-board lockfiles)
  5. Telnet session: `boards` shows counts, `enter art` switches prompt + scope, `read 2` reads from art (not main), `leave` restores main, all `list` / `read` reflect the current board
- **Roadmap restructured** to reflect the new release plan (per user direction 2026-05-23): **0.5.0** = M5 close (M5-E shipped, M5-F remaining), **0.6.0** = M6 sigil-backed auth, **0.7.0** = security sweep with CVE / 0-day web research, **0.8.0** = hardening + v1 lockdown, **1.0.0** = complete with iron validation on archaemenid LAN.

## [0.4.0] — 2026-05-23 (M5 partial — post persistence with metadata + concurrent-writer correctness)

agora is now a **working BBS over telnet**. Six bites landed across the M5 cycle: post storage primitives (M5-A), in-session command interpreter (M5-B), sorted listing (M5-C), RFC-822 headers per [ADR 0003](docs/adr/0003-rfc-822-post-headers.md) (M5-D), per-store flock (M5-G), and ingress input filter (M5-H). Two ADRs land: 0002 (one file per post, monotonic IDs) and 0003 (RFC-822 headers). 38 tests; 129,096 B; bench baseline unchanged. **M5 is partial** — boards (M5-E) and threads (M5-F) defer to a later release. Single-board single-thread BBS is the 0.4.0 shipping shape.

### Changed

- `print_banner` / `cmd_version` / connection MOTD / `render_motd` version line bumped to 0.4.0.
- `cyrius.cyml [deps].stdlib` grew `str` + `fs` (M5-A: storage primitives) + `chrono` (M5-D: ISO-8601 Date header). 13 stdlib modules at 0.3.0 → 16 at 0.4.0; darshana git dep unchanged at pin 0.5.3.
- **Closeout note**: security re-scan surfaced a latent stack-overrun in `t30_sort_i64_asc_basic` — `var expected[8]` allocated 8 bytes but stored 8 i64s (64 bytes). The layout silently tolerated the overrun on this host; fixed to `var expected[64]` with a comment citing the CLAUDE.md "buffer is N **bytes**, not N entries" rule. No production code affected.

### Added — M5-G: per-store flock for the post-claim critical section (2026-05-23)

- **New primitives in `src/board.cyr`**:
  - `store_lock_acquire(store)` — opens `<store>/.lock` (`O_WRONLY | O_CREAT`, 0o644), takes a blocking `LOCK_EX` flock via `lib/io.cyr` `file_lock`, returns the lockfile fd
  - `store_lock_release(fd)` — `file_close` (kernel releases the lock implicitly)
- **`post_new` and `post_new_with_subject` now serialize claim+write** through the lock. The `post_max_id` + `O_CREAT | O_EXCL` open + `write` triple runs inside the locked region; format-with-subject (pure per-call work) runs outside to shorten the critical section.
- **Lockfile naming dodges `parse_post_id`** — `.lock` doesn't end in `.txt` so it's filtered out by `post_list` / `post_max_id`. No new exclusion needed.
- **What this changes**: pre-M5-G, two concurrent writers reading the same `post_max_id` and racing on the EXCL claim would result in one writer succeeding and the other returning `-1` (EEXIST). The EXCL guarantee meant no corruption — just a dropped post. M5-G upgrades to "both writers serialize, both succeed, distinct IDs." Correctness improvement for high-fanout deployments (CLI + telnet concurrent, multiple CLI processes, future thread-per-conn accept loop).
- **Smoke**: 50 parallel `agora post` invocations under M5-G all return distinct IDs and produce 50 files on disk; zero errors. (Pre-M5-G the race window is narrow enough on this host that 50 also succeed by luck — the lock makes it a guarantee instead of probabilistic.)
- **Binary**: 128,352 → 129,096 B (+744 B for the lock helpers).
- **Tests still 38/38 green** — the lock is invisible to test.cyr's single-process pure-function suite. The "two-writer correctness" property is verified by the parallel CLI smoke harness in this CHANGELOG entry; an automated parallel-process test belongs in `tests/` once a multi-process harness exists (deferred).

### Added — ADR 0003 + M5-D: RFC-822-shaped post headers (Subject + Date) (2026-05-23)

- **[ADR 0003](docs/adr/0003-rfc-822-post-headers.md)** — captures the header-format decision: per-post file gets `Subject: <single-line>\r\n` + `Date: <ISO-8601-UTC>\r\n\r\n` block, then body. Rejects three alternatives (JSON, CYML front matter, TSV) with concrete reasoning. Backwards-compat with M5-A/B/C headerless posts is built into the parser (first byte not ASCII uppercase → treat whole file as body).
- **`src/board.cyr` additions** (~180 LOC):
  - `post_body_offset(buf, len)` — returns 0 (no headers) or offset past the blank line that terminates headers. Handles `\r\n\r\n` AND `\n\n` separators (mixed line endings tolerated within headers).
  - `header_get(buf, len, name, out, max)` — finds `Name: value` at start of any line in the header block; skips optional single space after `:`; returns value length copied or `-1` if not found.
  - `post_format_with_subject(subject, body, body_len, out, cap)` — composes `Subject: <s>\r\nDate: <iso8601_now>\r\n\r\n<body>`.
  - `post_new_with_subject(store, subject, body, body_len)` — formats + writes via the same EXCL-claim path as the M5-A `post_new`. Empty subject is allowed (writes `Subject: \r\n` so `header_get` returns 0-length instead of `-1`).
  - `post_subject(buf, len, out, max)` — convenience: `header_get` "Subject" but normalize the missing-header case to 0 (so `list` always renders an empty subject row instead of an error).
- **Wire integration in `src/main.cyr`**:
  - New session mode `MODE_POSTING_SUBJECT` between `MODE_COMMAND` and `MODE_POSTING`. Typing `post` now prompts `Subject: ` first; the next line is captured into a per-connection subject buffer; then the `Compose post.` prompt + body capture continues unchanged.
  - In-session `list` now shows `<id>  <subject>` per row (was bare `<id>`).
  - In-session `read <id>` now shows `Subject: ...\r\n\r\n<body>` (was raw file content).
  - CLI `agora post` grew `--subject <text>` flag (and an empty default).
  - CLI `agora list` and `agora read` updated for the same body-only / subject-prefix behavior as the wire.
- **`stdlib` deps** grew `chrono` for `iso8601_now` (Date header generation).
- **Fixed a session-buffer corruption bug surfaced during M5-D smoke**: when the EOL-paired LF arrived after CR, the previous code path fell through to the printable-byte branch and appended the LF to the line buffer at position 0 — corrupting every subsequent command's first byte. Added explicit `consumed` flag in the EOL detection that drops paired-LF entirely instead. Two-list-in-a-row reproduces the original bug; now passes clean.
- **Tests grew 32 → 38** — six new tests: `t33_post_body_offset_headerless` (sniffer-rejects-lowercase-start), `t34_post_body_offset_crlf` (CRLF blank-line separator), `t35_post_body_offset_lf` (LF-only separator), `t36_header_get_subject` (extract Subject value), `t37_header_get_missing` (absent header returns -1), `t38_post_subject_headerless_returns_zero` (normalization for `list` UX).
- **End-to-end CLI + telnet smoke** — CLI `post --subject "Hello"` + `list` shows `1  Hello`; `read 1` shows `Subject: Hello\n\nbody`. Telnet `post` prompts `Subject: `, captures the line, transitions to body capture, period-ends, writes file with both headers. Headerless legacy file dropped manually into the store renders as `4  ` (no subject) in `list` and prints body verbatim under `read`.
- **Binary delta**: 116,904 B (M5-H close) → 128,352 B (+11.4 KB for `lib/chrono.cyr` + header primitives + new session mode + CLI flag).

### Added — M5-C: sorted post listing (2026-05-23)

- **`post_list` now returns IDs in ascending order**. M5-A/B returned directory-iteration order which is non-deterministic and unfriendly to the `list` UX (and to anyone diff-checking output across runs).
- **`sort_i64_asc(arr, count)`** — in-place insertion sort over an i64 array. O(n²); appropriate for the v1.0 scale (`DIRENT_ID_MAX = 4096`, real post counts well below). Bumping the algorithm earns a bite only if a consumer reports perf concerns.
- Two new tests: `t30_sort_i64_asc_basic` (8-element unsorted array → ascending) and `t31_sort_i64_asc_empty_and_single` (edge cases). Wire smoke with 5 posts confirms `list` returns `1 2 3 4 5`.

### Added — M5-H: input filter on post bodies (2026-05-23)

- **`input_byte_ok(b)`** in `src/board.cyr` — drops NUL (`0x00`) and ESC (`0x1B`) from incoming post bodies; passthrough for everything else (TAB / CR / LF / printable ASCII / UTF-8 high bytes / BEL / BS / DEL). Applied in `handle_client`'s byte dispatch *before* the byte reaches the line buffer.
- **Threat model** documented inline:
  - **NUL** terminates cstring tooling downstream (`cat`, `grep`, `agora read`'s byte writer, `fmt_int_buf`); a post containing NUL would render as truncated everywhere.
  - **ESC** = terminal-control injection. A post containing `\x1b[2J` (clear screen), `\x1b[10;1H` (cursor to row 10), `\x1b]0;evil\x07` (set window title), or 70s-era VT keyboard-remapping sequences executes in the *viewer's* terminal when another user runs `read N` over telnet. Classic chat-attack vector — strip at ingress.
- **Living at the storage-policy layer** — `input_byte_ok` lives in `src/board.cyr` because it expresses what the post storage system accepts, not what the wire protocol allows. main.cyr's `handle_client` enforces it at ingress. Future operator-config may add an opt-in for raw-mode posts (useful if an operator wants to allow ANSI art in posts on a known-friendly LAN).
- **One new test**: `t32_input_byte_ok_filters_nul_esc` exercises both rejected bytes + 9 passthrough cases including UTF-8 lead/continuation bytes.
- **Wire smoke**: a malicious post containing `Hello\x1b[31mRED\x1b[0m and NUL\x00here` lands on disk as `Hello[31mRED[0m and NULhere\r\n` — both ESC bytes and the NUL byte stripped; the harmless `[31m` / `[0m` text bytes remain as inert content. `grep -c -P "\x1b" 6.txt` and `grep -c -P "\x00" 6.txt` both return 0.

### Added — M5-B: in-session command interpreter over telnet (2026-05-23)

- **Connected-client command loop** — `handle_client` now runs a line-buffered command interpreter after the MOTD instead of the echo-only loop. Supported commands (typed at the `>` prompt):
  - `help` — list available commands
  - `list` — print post IDs (one per line)
  - `read <id>` — print one post body, trailing-CRLF-normalized
  - `post` — enter compose mode; multi-line input ends with `.` on a line by itself; assigned ID is returned ("posted as #N")
  - `quit` / `exit` / `bye` — close the session ("bye" then disconnect)
- **`agora serve` grew `--store <path>`** — same shape and default (`./agora-data/`) as the CLI verbs. Passed through to `handle_client` via the new `g_store_buf` global (set-once-at-startup, parallel to `g_motd_*`).
- **Session helpers in `src/main.cyr`** (~250 LOC added):
  - `send_str(cfd, s)` / `echo_byte(cfd, b)` — wire-output convenience
  - `line_has_prefix(line, len, prefix)` — command dispatch by leading token
  - `line_parse_int(line, off, len)` — parse `<id>` argument; skips leading whitespace, stops at first non-digit, rejects zero / no-digits
  - `session_execute(cfd, line, len, quit_out)` — dispatch on the typed line; returns the new mode (`MODE_COMMAND` or `MODE_POSTING`)
  - `session_finalize_post(cfd, body, len)` — commit the composed body via `post_new`, send "posted as #N" or "post failed (storage error)"
- **CR/LF discipline per telnet NVT (RFC 854)** — CR is the canonical line terminator; the LF that often follows is paired and silently absorbed via a `last_cr` flag; lone LF also terminates (raw-`nc` clients). Each typed printable byte is echoed (we announced `WILL ECHO` at M2-B). Backspace handling is deferred — typed text isn't editable in-line at M5-B.
- **Two-mode state machine**:
  - `MODE_COMMAND` (default): each complete line dispatches to a command
  - `MODE_POSTING`: each complete line is appended to the post body (with CRLF); a line that's exactly `.` ends the compose flow and commits
- **End-to-end smoke** — Python TCP client walks every command path:
  `help` shows the list, empty `list` returns "(no posts)", `post` + multi-line body + `.` returns "posted as #1", `list` reflects the new ID, `read 1` returns the body bytes, `read 99` returns "post not found", `badcmd` returns "unknown command", `quit` returns "bye" + disconnects. Files land in `--store` per ADR 0002 shape.
- **24-test parser suite + 5-test board suite still green** — this bite is integration-layer code; the IAC state machine and post storage primitives are untouched. Binary 109,992 → 116,232 B (+6,240 B for the command interpreter).

### Added — M5 ADR 0002 + M5-A: post storage primitives (2026-05-23)

- **`docs/adr/0002-one-file-per-post-storage.md`** — captures the M5 storage-layout decision: one file per post (`<store>/<id>.txt`, monotonic-integer IDs), operator-configurable storage root via `--store <path>` (default `./agora-data/`), plaintext UTF-8 body bytes only. Rejects two alternatives — one-file-per-thread-with-offset-index and SQLite-style WAL — with concrete reasoning. The shape is a strict prefix of the eventual v2.x content-addressed-storage layout (pillar 2 in `roadmap-future.md`): swap the ID-assignment fn, schema stays.
- **`src/board.cyr`** (~165 LOC) — `store_ensure` (mkdir, EEXIST-as-success), `build_post_path` (path formatter), `parse_post_id` (filename → integer or 0), `post_max_id` (O(n) dir scan), `post_new` (write with `O_CREAT | O_EXCL` for atomic ID claim), `post_read` (file_read_all by ID), `post_list` (iterate dir, parse valid IDs). All bounded by named caps (`POST_MAX_BYTES = 64 KB`, `PATH_MAX_BYTES = 512`, `DIRENT_ID_MAX = 4096`).
- **CLI verbs now real** — `cmd_post` reads stdin into a 64 KB buffer (multi-read loop until EOF) → `post_new` → prints assigned ID. `cmd_list` walks the store directory, prints valid post IDs. `cmd_read <id>` validates the ID, opens the file, writes body bytes to stdout. All three accept `--store <path>` (order-insensitive parse, same shape as M2-C's `--motd`).
- **`stdlib` deps grew**: added `str` (for `dir_list`'s Str interop) and `fs` (the `dir_list` primitive itself).
- **Tests grew 24 → 29** — `t25_parse_post_id_valid` (1.txt / 42.txt / 9999.txt round-trip), `t26_parse_post_id_rejects_non_txt` (`1.log` / `1.tx` / bare-int), `t27_parse_post_id_rejects_non_digits` (`foo.txt` / `1a.txt` / `1.2.txt`), `t28_parse_post_id_rejects_zero` (IDs are 1-indexed), `t29_build_post_path_shape` (verbatim path construction). The cyrius "continue without incrementing i = infinite loop" trap surfaced + got fixed during the first test run.
- **End-to-end CLI smoke** — empty store → `no posts` exit 0; three posts written round-trip via stdin → file IDs 1/2/3 on disk under 0644; `list` returns IDs (directory order; sort is M5-A-deferred); `read 2` returns the body verbatim; `read 99` reports `post not found` exit 1; `read foo` reports `invalid post ID` exit 2.
- **Binary delta**: 85,544 B (0.3.0) → 109,992 B (+24.4 KB for board.cyr + str + fs stdlib surface; most DCE-eligible).
- **Out of scope at M5-A** (per ADR 0002): boards (M5-E), threads (M5-F), concurrent-write lock (M5-G), telnet-wire integration (M5-B), RFC-822 headers in the post file (M5-D).

## [0.3.0] — 2026-05-23 (M2 close: ANSI BBS aesthetic)

M2 cycle landed end-to-end across three bites — `bnrmr`-rendered AGORA banner embedded as the connection MOTD (M2-A), darshana SGR coloring wrapped around the banner / version / prompt at connection time (M2-B), and `agora serve [port] [--motd <path>]` operator override (M2-C). bannermanor patched 1.0.0 → 1.0.1 the same day so every AGNOS consumer of darshana is on the same `0.5.3` pin. M2-D (NAWS-aware width clamping) remains an optional polish bite — M2 is functionally closed without it.

24-test parser conformance still green. Binary 70,960 B (M1 close) → 85,544 B (M2 close); the +14.6 KB is mostly `lib/darshana.cyr` consumption surface (most DCE-eligible — 243 unreachable fns NOPed at 31,515 B). Bench baseline unchanged from M1 (`telnet/plain_byte` ~10 ns, `subneg_naws` ~100 ns).

### Changed

- `cyrius.cyml [deps]` — added `[deps.darshana]` git dep pinned at `0.5.3` (M2-B). Bannermanor pins the same `0.5.3` at 1.0.1.
- `src/main.cyr` — version literals (`print_banner` / `cmd_version` / `render_motd` version line) bumped to 0.3.0. Inline-version-string drift remains the known technical-debt item flagged in [0.2.0]; CI's drift-check step (added in 0.2.0) caught us if we'd forgotten.
- `print_help` updated to document the `--motd` flag.

### Added — M2-C: `agora serve --motd <path>` operator override (2026-05-23)

- **New flag**: `agora serve [port] [--motd <path>]`. Order-insensitive argv parse — positive-integer positionals still take the port, `--motd` consumes the next arg as a filesystem path.
- **`load_motd_file(path)`** — reads up to 4 KB from `path` once at startup via `lib/io.cyr` `file_read_all`, parks the buffer + length in two globals (`g_motd_buf`, `g_motd_len`). Three failure modes warn-and-fall-back to the default MOTD: missing path arg (returns exit 2), `read` failure (open error or read error), and zero-byte file. Set-once-at-startup state — no per-connection re-read.
- **`handle_client` MOTD dispatch** — if `g_motd_buf` is non-null, sends those bytes verbatim; otherwise allocates a per-connection 1 KB buffer and runs the M2-B `render_motd` path. The override is verbatim — operator is responsible for CRLF line endings (telnet NVT, RFC 854) and any ANSI escapes they want to embed.
- **Smoke** — three cases verified end-to-end against a python TCP client:
  1. No flag → default cyan-wrapped AGORA banner via `render_motd`
  2. `--motd /tmp/operator-motd.txt` → file content delivered verbatim
  3. `--motd /nonexistent` → stderr warning, server continues with default MOTD
- **Help text updated** in `print_help` to document the flag.
- 24-test parser suite still green (this bite is content-layer, doesn't touch the IAC state machine). Binary 84,488 → 85,544 B (+1,056 B).

### Added — M2-B: darshana SGR-colored MOTD (2026-05-23)

- **`[deps.darshana]`** — added to `cyrius.cyml` as a git dep pinned at `0.5.3`. Functional surface (`tty_sgr_buf`, `tty_sgr_reset_buf`, `tty_fg_rgb_buf`, cursor primitives) is present at 0.5.3 even though darshana itself is pre-1.0 — the "needs ≥ 1.0" gate in the original roadmap was a version-label restriction, not a functionality one. Bannermanor 1.0.1 re-pinned to the same `0.5.3` the same day so every AGNOS consumer of darshana is on one version.
- **`render_motd(buf)`** — new function in `src/main.cyr` that composes the bannermanor-derived AGORA banner with darshana SGR coloring directly into a caller-allocated 1 KB buffer. The `_buf` variants (`tty_sgr_buf` / `tty_sgr_reset_buf`) target a buffer instead of fd 1, which is exactly what we need to send bytes back over the telnet socket via `send_buf`.
- **Color scheme**:
  - AGORA ASCII banner (5 lines) — cyan (`SGR 36`)
  - Version line ("agora 0.2.0 — telnet BBS") — yellow (`SGR 33`)
  - Prompt line ("Type anything; Ctrl+] then 'quit' to exit.") — default fg
- **`handle_client`** — static `banner` string variable replaced with a `motd = alloc(1024); render_motd(motd); send_buf(...)` pattern. Per-connection allocation is one `alloc` + one render pass + one `send_buf` — sub-microsecond on this host; immaterial vs the human-paced BBS workload.
- **Wire smoke** — python TCP client receives the 12-byte announce salvo followed by 4 ANSI ESC sequences (cyan-on, reset, yellow-on, reset) wrapping the banner content. Real telnet clients render the AGORA in cyan and the version in yellow.
- **Binary delta**: 71,120 → 84,488 B (+13,368 B for `lib/darshana.cyr` consumption surface; 248 unreachable fns / 32,371 B DCE-eligible, most of the darshana surface we don't call yet — gets reclaimed when the v1.x close-out adds strip + DCE-aware emit).
- 24-test parser conformance still green — `render_motd` is content-layer code that doesn't touch the IAC state machine.
- **Remaining M2 work**: M2-C (`--motd <path>` operator override) is optional, lands when operator demand surfaces. NAWS-aware reflow (using `term_cols` / `term_rows` from M1 to clamp banner width) is a natural M2-D when consumer tooling needs it.

### Added — M2-A: bannermanor MOTD on connect (2026-05-23)

- **Connection MOTD upgraded** from a plaintext `agora 0.2.0 — telnet BBS` line to a bannermanor-rendered ASCII-art `AGORA` banner (block font, 5×5) followed by the version line and the input-prompt help. Pre-rendered via `bnrmr "AGORA"` and embedded as a string constant in `src/main.cyr` — no runtime subprocess shellout, no dep on `bnrmr` being installed at runtime, no per-connection latency for re-rendering static content.
- **Provenance documented in code** — the embed site carries a comment block citing bannermanor v1.0.0 (frozen CLI surface) and the regeneration recipe (`bnrmr "AGORA"`) so future label / version / banner-text changes are reproducible. `#` bytes inside the string use `\x23` escapes to dodge cyrius's line-comment lexer.
- **Binary delta**: 70,960 → 71,120 B (+160 B for the ~470-byte rendered banner string).
- **End-to-end smoke**: python TCP client receives the 12-byte announce IAC salvo as before, followed by the multi-line banner; existing 24-test parser conformance suite still green.
- M2's second bite (ANSI color via darshana SGR + cursor positioning + NAWS-aware width) waits on darshana ≥ 1.0 (currently 0.5.3).

## [0.2.0] — 2026-05-23 (M1 close: cross-platform telnet listener)

Multi-bite M1 cycle landed end-to-end: RFC 854 IAC parser + RFC 1143 Q-method option negotiation + RFC 1073 NAWS + RFC 1091 TERMINAL_TYPE + RFC 1184 LINEMODE, all wire-conformant via paired python TCP client smoke. Cross-platform via `lib/net.cyr` (Linux x86_64 + aarch64 today; macOS / Windows / AGNOS as the stdlib gains backends — see [ADR 0001](docs/adr/0001-cross-platform-listener-decoupled-from-agnos.md)). 24 tests passing; 5-benchmark parser baseline captured in [`BENCHMARKS.md`](BENCHMARKS.md). Binary 43,216 B (v0.1.0 scaffold) → 70,960 B at 0.2.0 close.

### Changed

- `cmd_serve` upgraded from M1 stub to a real cross-platform telnet listener (default port 2323; configurable via `agora serve <port>`).
- `print_banner` / `cmd_version` / connection-MOTD strings bumped to 0.2.0. (Note: version strings remain inlined in `src/main.cyr` — `cyrius` has no source-level `${file:VERSION}` interpolation yet, only `.cyml`-level. Embedded version constant via a generated `version_str.cyr` is a v1.0 close-out item.)
- `cyrius.cyml` `[deps].stdlib` grew from 7 modules (scaffold) to 13 modules across the M1 cycle: added `net` + `result` + `tagged` (first-bite, socket primitives + Result type), `vec` + `fnptr` + `bench` (close-bite, bench harness dependencies).

### Added — CI / Release workflows (2026-05-23)

Pattern adopted from [kii](https://github.com/MacCracken/kii) + [bannermanor](https://github.com/MacCracken/bannermanor), the first-party reference implementations:

- **`.github/workflows/ci.yml`** — push / PR / `workflow_call` triggers. Concurrency: `cancel-in-progress` per-ref so only the latest push tests. Steps: checkout → install cyrius toolchain (version read from `cyrius.cyml [package].cyrius` — single source of truth) → `cyrius deps` → `cyrius build src/main.cyr build/agora` → **version drift check** (compares `./build/agora --version | head -1` against `VERSION`; catches inline-literal drift in `src/main.cyr` since cyrius lacks source-level `${file:VERSION}`) → `cyrius test` (auto-picks `[build].test`, runs the 24-test conformance suite).
- **`.github/workflows/release.yml`** — tag-triggered on `tags: ['[0-9]*']` (semver-only filter per CLAUDE.md). `permissions: contents: write`. CI gate via `uses: ./.github/workflows/ci.yml` (re-runs the full CI matrix before the release artifact builds). **Version verify**: `VERSION` file must equal the git tag, or the run fails. Then install + build + `softprops/action-gh-release@v2` with `files: build/*` and auto-generated release notes from the GitHub API.
- **What's NOT in CI yet** (deferred until earned): fuzz harness (a `tests/agora.fcyr` driving telnet_feed against random byte streams — adversarial-by-default protocol, fuzz earns its spot at M2+ when the input surface widens with NAWS/TT consumption), bench step (`BENCHMARKS.md` is hand-maintained at 0.2.0; CI bench gates land alongside `scripts/bench-history.sh` at v1.0 close-out), aarch64 cross build (waits on cyrius cross-toolchain availability in the CI runner image), `CYRIUS_DCE=1` builds (CLAUDE.md mentions but kii / bannermanor don't enforce yet — match the reference implementations until the convention formalizes).

### Added — M1 close: bench harness + first parser baseline (2026-05-23)

- **`benches/bench_telnet.bcyr`** (~115 LOC) — five parser microbenchmarks via `lib/bench.cyr` `bench_run_batch` (10 rounds × 10,000 iterations each):
  - `telnet/plain_byte` — single byte through ST_DATA path
  - `telnet/iac_untracked` — `IAC WILL OPT_STATUS` (3 bytes, naive-refuse + 3-byte reply)
  - `telnet/iac_tracked_agree` — `IAC WILL SGA` (3 bytes, Q machine agree + 3-byte reply)
  - `telnet/subneg_naws` — full NAWS subneg (9 bytes + payload decode)
  - `telnet/announce_salvo` — 4-option opening salvo (one-time-per-connection cost)
- **`BENCHMARKS.md` at repo root** — first baseline captured per [first-party-documentation § Benchmarks](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#benchmarks-and-performance-docs). Numbers on Linux x86_64 workstation, Cyrius 6.0.1:
  | Benchmark | Avg |
  |---|---:|
  | `telnet/plain_byte` | **10 ns** |
  | `telnet/iac_untracked` | **63 ns** |
  | `telnet/iac_tracked_agree` | **73 ns** |
  | `telnet/subneg_naws` | **97 ns** |
  | `telnet/announce_salvo` | **132 ns** |

  Derived throughput: ~100 M plain-bytes/s through the parser; ~14 M tracked option-exchanges/s; ~10 M NAWS subnegs/s. Orders of magnitude above any plausible BBS load.
- **`cyrius.cyml` `[deps]`** — added `vec`, `fnptr`, `bench` to stdlib list (needed for the bench harness). Binary grew 62,176 → 70,960 B (+8,784 B from the larger stdlib surface); DCE NOPs 26,707 B of the bench-only paths leaving them unreachable but allocated. Acceptable cost for the M1 close — release-build optimization is a v1.x close-out concern, not blocking.
- **What's NOT in the baseline** (deferred to follow-up bench files): accept-loop rate (needs paired client process), end-to-end echo latency over loopback, memory pressure under N concurrent connections, DCE-stripped binary perf.

### M1 closed (2026-05-23) — cross-platform telnet listener

All four protocol bites + bench harness now landed. M1 close summary:

- **Protocol surface**: RFC 854 (IAC parser), RFC 1143 (Q-method negotiation), RFC 1073 (NAWS), RFC 1091 (TERMINAL_TYPE), RFC 1184 (LINEMODE) — all wire-conformant.
- **Tests**: 24/24 green, RFC sequences + state transitions + malformed-payload defense.
- **Smoke**: end-to-end handshake (announce → peer agree → server TT SEND → peer NAWS+TT IS+LINEMODE ACK → data echo) wire-conformant via python TCP client.
- **Bench**: parser at 10 ns/byte hot path, ~100 ns for full option exchanges. First baseline captured.
- **Lifecycle**: slowloris timeout (60 s default) + graceful EOF/error close.
- **Cross-platform**: built on `lib/net.cyr` per [ADR 0001](docs/adr/0001-cross-platform-listener-decoupled-from-agnos.md) — Linux x86_64 + aarch64 today, macOS/Windows/AGNOS as stdlib gains backends.

**Next in-flight slot: M2** — ANSI BBS aesthetic. Consumes `bannermanor` 1.0.0 ✅ (for ASCII MOTD banners) + darshana ≥ 1.0 ❌ (currently 0.5.3 — likely gated on darshana's own 1.0 cut). Likely first M2 bite: bannermanor MOTD on connect ahead of the existing plaintext banner.

### Added — Post-v1.0 roadmap: v2.x sovereignty pillars (2026-05-23)

- **`docs/development/roadmap-future.md`** — new file consolidating six unpinned design directions for the v2.x sovereignty layer:
  1. **Identity continuity across nodes** — Ed25519 keypair as portable identity (Nostr-shaped, sigil-backed); replaces per-node accounts with global fingerprints. Graduates from v1.0 M6 sigil-backed auth.
  2. **Content-addressed storage** — posts keyed by `blake3(canonical(post))`; mirror anywhere without breaking links; citations integrity-checkable. Layered onto v1.0 M5 persistence.
  3. **Threat-level node policy** — mirror the SecureYeoman threat-level vocabulary (`hobbyist` / `journalist` / `activist` / `enterprise`) and apply it to network exposure. Same binary, different config.
  4. **Federation by interest, not platform** — topic-shaped federation (FidoNet echomail / Usenet / Matrix-rooms heritage); nodes carry topics, not "your account on this server."
  5. **Self-distribution baked-in** — every node carries AGNOS / SecureYeoman / marketplace installers; the network is the distribution channel. Block-resistance compounds with deployment count.
  6. **Offline-tolerant store-and-forward** — durable outbox + sync-on-connect + sneakernet-friendly export/import; FidoNet/UUCP-shape; works where ActivityPub silently fails (rural, censored, sanctioned, air-gapped).
- Cross-linked from `roadmap.md` ("Post-v1.0 Directions" section), `docs/doc-health.md` (Tier 2 row + bucket count), and this CHANGELOG.
- Pattern adopted from [cyrius/docs/development/roadmap-future.md](https://github.com/MacCracken/cyrius/blob/main/docs/development/roadmap-future.md): unpinned items, pull-forward triggers documented per pillar, no calendar commitment.

### Added — M1 fourth-bite: RFC 1184 LINEMODE (2026-05-23)

- **LINEMODE promoted to tracked** — `opt_pref_him(OPT_LINEMODE)` now returns 1. Peer's `WILL LINEMODE` lands him-state on `Q_YES` via the `Q_NO → Q_YES` transition; server replies `IAC DO LINEMODE` (3 bytes) and immediately follows with the MODE-establishment request (7 bytes) for a total 10-byte burst.
- **`ts_emit_linemode_request`** — composes `IAC SB LINEMODE MODE (LM_EDIT | LM_TRAPSIG) IAC SE`. Mask 0x03 is the BBS default: client buffers a line locally and forwards on Enter; client traps signal characters (Ctrl+C → IP, Ctrl+\ → BRK, Ctrl+] → AYT) as IAC commands. `ts_on_him_yes` dispatches to this on `Q_YES` transition for OPT_LINEMODE (alongside the existing TT SEND emit).
- **`telnet_handle_sb` LINEMODE dispatch** — sub-command MODE stores the peer's acknowledged mask byte into a new `TS_LM_MODE` field; sub-command SLC is parsed-and-ignored (RFC 1184 § Set Local Character — peer's local-character table doesn't drive server behavior yet); FORWARDMASK deferred. Malformed MODE (not exactly 1 mask byte) silently dropped.
- **TelnetState grew 1 field** — `TS_LM_MODE` (i64, holds the active LINEMODE mask after peer ACK). Total struct size 120 B → 128 B; per-connection allocation unchanged otherwise.
- **`telnet_linemode_mask` accessor** — exposes the current LINEMODE mask to consumers; 0 until peer confirms via `IAC SB LINEMODE MODE <mask> IAC SE`.
- **Tests grew to 24** (was 20) — `t21_will_linemode_emits_mode_request` (10-byte burst: DO LINEMODE + MODE-request), `t22_linemode_mode_ack_parse` (mask 0x07 stored from peer ACK), `t23_linemode_slc_ignored` (SLC parsed-and-ignored, parser recovers to DATA), `t24_linemode_mode_malformed_dropped` (zero-mask-byte MODE silently dropped).
- **End-to-end smoke** — python TCP client sends `WILL LINEMODE`, server replies with the exact 10-byte burst; client ACKs `MODE 0x07`, server captures silently; subsequent data byte 'L' echoes through cleanly. Binary 61,152 → **62,176 B** (+1,024 B for LINEMODE).

### Added — M1 third-bite: NAWS + TERMINAL_TYPE subneg parsing (2026-05-23)

- **NAWS payload parser** (RFC 1073) — `telnet_handle_sb` decodes the 4-byte BE-encoded window-size payload into per-connection `term_cols` / `term_rows` fields. IAC-escaped 0xFF bytes inside the payload pass through correctly (already handled by the SB-IAC state). Malformed lengths (not exactly 4 payload bytes) are silently dropped.
- **TERMINAL_TYPE handshake** (RFC 1091) — when peer's `WILL TERMINAL_TYPE` lands him-state on `Q_YES` (via the new `ts_on_him_yes` hook), the server immediately queues the 6-byte SEND request `IAC SB TT SEND IAC SE`. Peer's `IAC SB TT IS <ascii> IAC SE` reply is parsed into a 256-byte per-connection `term_type` buffer.
- **TelnetState grew 4 fields** — `TS_TERM_COLS` / `TS_TERM_ROWS` / `TS_TERM_TYPE` / `TS_TERM_TLEN`. Total struct size 88 B → 120 B; per-connection allocation gains the 256-byte term-type buffer (zero-initialized via `memset`).
- **`handle_client` consumes `EV_SB`** — when `telnet_feed` returns `EV_SB`, the per-byte loop calls `telnet_handle_sb(ts)`. Replies it queues (e.g. a second TT SEND) flush on the next tx-drain in the same loop iteration.
- **Tests grew to 20** (was 15) — `t16_naws_parse` (80×24 from canonical VT subneg), `t17_naws_iac_escape` (width=255 with IAC IAC escape correctly unescapes), `t18_terminal_type_is` ("XTERM" string captured), `t19_will_tt_emits_send` (peer WILL TT triggers 6-byte SEND reply + him-TT lands Q_YES), `t20_naws_malformed_dropped` (3-byte NAWS payload silently rejected, term_cols stays 0).
- **End-to-end smoke** — python client agrees to ECHO/SGA, sends WILL NAWS + WILL TT, server replies with IAC SB TT SEND IAC SE; client sends NAWS subneg (120×40) + TT IS XTERM subneg; server consumes both silently and the next data byte 'K' echoes through cleanly. Binary 59,280 B → **61,152 B** (+1,872 B for subneg parser + 256 B per-conn term buffer).

### Added — M1 second-bite: RFC 1143 Q-method option negotiation (2026-05-23)

- **`telnet_handle_negotiation`** (~75 LOC in `src/telnet.cyr`) — three-state Q machine (`Q_NO` / `Q_WANTYES` / `Q_YES`) per option per side, replacing the first-bite naive-refuse-everything path. Untracked options still naive-refuse; tracked options run full RFC 1143 transitions with no on-wire WILL/WONT loops.
- **Per-connection option state** — `TelnetState` grew two 256-byte arrays (`opt_us`, `opt_him`), accessed via `opt_us(ts, opt)` / `opt_him(ts, opt)` and their setters. `telnet_state_new` zero-initializes both via `memset` so every option starts in `Q_NO` until activity moves it.
- **Server preferences** — `opt_pref_us(opt)` returns 1 for `ECHO` and `SUPPRESS_GO_AHEAD`; `opt_pref_him(opt)` returns 1 for `SUPPRESS_GO_AHEAD`, `NAWS`, `TERMINAL_TYPE`. Drives both `telnet_announce` and the per-event Q transitions.
- **`telnet_announce`** — replaces the first-bite no-op stub. Queues the four-byte salvo onto `tx_buf` (`IAC WILL ECHO`, `IAC WILL SGA`, `IAC DO NAWS`, `IAC DO TT`) and parks each option in `Q_WANTYES` on the relevant side. `handle_client` calls it after `telnet_state_new` and flushes before the banner.
- **Slowloris defense** — `sock_set_recv_timeout(cfd, 60, 0)` per connection. A quiet client (no traffic for 60s) drops cleanly via the `n <= 0` branch in the recv loop. Tuned for human-paced BBS use; trim `RECV_TIMEOUT_SECS` for higher fanout.
- **Graceful close** — comment-documented the EOF (`n == 0`) and error/timeout (`n < 0`) paths in `handle_client` so the disconnect intent is explicit.
- **Tests grew to 15** (was 10) — added `t10_announce_salvo` (exact byte sequence + WANTYES parking), `t11_announce_then_do_silent` (peer agrees, no on-wire reply), `t12_announce_then_dont_silent` (peer refuses, silent), `t13_untracked_option_refused` (STATUS still naive-refused), `t14_announce_then_will_silent` (peer-side WILL agreement). Updated `t04_do_sga_agreed` (was `t04_do_sga_refused` — DO SGA now triggers `WILL SGA` per `us_SGA=YES` preference).
- **End-to-end smoke** — python TCP client confirms the announce salvo arrives in exact order, peer `DO ECHO` reply produces silent agreement (us-ECHO `WANTYES → YES`), and plain data bytes echo through. Binary 56,064 B → **59,280 B** (+3,216 B for the Q machine + 512 B of per-connection option state).

### Added — M1 first-bite: cross-platform telnet listener (2026-05-23)

- **`src/telnet.cyr`** (~280 LOC) — RFC 854 IAC parser + RFC 1184 LINEMODE scaffolding. `TelnetState` struct + per-byte feed function `telnet_feed(ts, b)` returns one of `EV_DATA` / `EV_NONE` / `EV_SB`. Naive-refuse option-negotiation policy: every `DO` replies `WONT`, every `WILL` replies `DONT` (RFC 1143 § Q method — refuses safely, never agrees by accident).
- **`src/main.cyr`** — `cmd_serve` opens a listener via `lib/net.cyr` (`tcp_socket` / `sock_bind` / `sock_listen` / `sock_accept`). Default port 2323 (unprivileged); override via `agora serve <port>`. Per-connection IAC-aware echo loop wires the parser to the socket — refused-option replies flush onto the wire in temporal order before the next data byte echoes.
- **`src/test.cyr`** (10 unit tests, all passing) — RFC 854 conformance: plain data passthrough, `IAC IAC` literal escape, `WILL ECHO` → `DONT ECHO` refusal, `DO SUPPRESS_GO_AHEAD` → `WONT SGA` refusal, `NOP` consumed silently, subnegotiation collection (`IAC SB ... IAC SE`) with `EV_SB` event, escaped IAC inside subneg, mixed data/IAC byte streams, malformed-SB recovery, `tx_buf` drain/consume cycle.
- **`cyrius.cyml` [deps]** — added `net`, `result`, `tagged` to `stdlib` list. Resolved via `cyrius lib sync` from 6.0.1 snapshot.
- **End-to-end smoke** — python TCP client connects, receives banner, sends `IAC WILL ECHO` + `IAC DO LINEMODE` + `IAC NOP` + plain bytes; server replies in exact RFC-conformant order: `IAC DONT ECHO`, `IAC WONT LINEMODE`, then echoes plain bytes.

### Added — Docs scaffold per first-party standards (2026-05-23)

- `CLAUDE.md` per [example_claude.md](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/example_claude.md) template — durable rules; volatile state delegated to `docs/development/state.md`.
- `docs/development/roadmap.md` — extracted from `README.md`; full milestone table + sub-bites + v1.0 criteria.
- `docs/development/state.md` — live state snapshot (version, binary size, in-flight slot, gate state for downstream milestones).
- `docs/doc-health.md` — fresh / stale / archive ledger; pattern adapted from [cyrius/docs/doc-health.md](https://github.com/MacCracken/cyrius/blob/main/docs/doc-health.md).
- `docs/adr/` — README + template + `0001-cross-platform-listener-decoupled-from-agnos.md` (the load-bearing M1 decision).
- `docs/architecture/README.md` — index placeholder; first note earns its slot at M1 close.
- `docs/guides/getting-started.md` — build / smoke / run on Linux x86_64 + aarch64.
- `docs/examples/README.md` — placeholder.
- `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` — required root files per first-party scaffold.
- `README.md` — slimmed, points at `docs/development/roadmap.md` + the new doc tree.

### Changed

- `cmd_serve` upgraded from M1 stub to a real listener — exits stub-mode at the protocol level.
- Binary size 43,216 B (v0.1.0 scaffold) → 56,064 B (M1 first-bite, non-DCE) — +12.8 KB for the IAC parser, listener loop, and `lib/net.cyr` consumption surface.

## [0.1.0] — 2026-05-23 (Scaffold)

### Added

- Repo scaffold: `VERSION`, `cyrius.cyml` (toolchain pin 6.0.1), `src/main.cyr` (argv dispatch + boot banner + stub verbs), `README.md` (etymology + roadmap), `CHANGELOG.md`, `LICENSE` (GPL-3.0-only), `.gitignore`.
- Six stub verbs: `serve` (M1 telnet listener), `post` / `list` / `read` (M5 persistence), `whoami` (M6 auth), `version`, `help`.
- Build verified: `cyrius build src/main.cyr build/agora` → 43,216 B binary; `./build/agora help` + `version` exercise the dispatch.

### Notes

- Pre-M1 release — no networking, no persistence, no protocol code. Verbs print stubs and exit non-zero (except `version` / `help`).
- M1 (telnet listener) is gated on agnos 1.32.2 cycle closing — `tcp_listen(23)` must validate end-to-end on archaemenid iron first.
- M5 (post persistence) is gated on agnos 1.33.x ext4 WRITE landing (Phase 1-5 currently read-only).
- Naming convention: introduces a Greek lane to the AGNOS ecosystem alongside the existing Sanskrit/Hindi (system libs) + English-wordplay / Polynesian (user-facing tools) lanes — see [[feedback_naming_lanes]]. The name threads three independent layers — ancient Greek ἀγορά + Doja Cat "Agora Hills" (Scarlet, 2023) + Agoura Hills CA (literally adjacent to the project's home base in Thousand Oaks). Multi-layer convergence in the spirit of `kii`'s Polynesian/East-Asian/English-phonetic precedent.
