# 0034 — The output gate: page stops, the teletype, and a greeting that waits for the terminal type

> **Status**: Accepted
> **Date**: 2026-10-31 — 1.13.0; amends 0009, 0023, 0030

## Context

agora has stored two things about the client's terminal since M1 and used neither:
- the window height, from NAWS (RFC 1073);
- the terminal type, from TERMINAL-TYPE (RFC 1091).

[ADR 0030](0030-terminal-aware-output.md) consumed the window's width and left the other two for 1.13.0. Three
features wanted them, and the roadmap noted that all three share one mechanism:

- **Paging by window height.** A `--More--` stop on long output, with a key to go on or stop.
- **The Handler's 2400-baud teletype.** [ADR 0009](0009-door-games-subsystem.md) deferred it at 1.1.0 for want of
  output pacing and a mid-print key.
- **Colour by terminal type.** A terminal that names itself `DUMB` or `UNKNOWN` should get no SGR. The greeting
  carries most of agora's colour, and it went out before the type could arrive.

Each of these holds output back. Under fork, a connection child could simply wait inside the command for a key.
Under poll it cannot: one process serves every session ([ADR 0023](0023-dual-serve-model.md)), so a command that
waited would stop the whole sweep. On agnos poll is the only model.

## Decision

**A command still prints everything it has. A per-session gate decides how much of it the drain may send.**

The session's tx queue already holds every byte waiting for the socket, so it holds the waiting output too. A hold
is an offset into the queue (`SESS_TX_HOLD`). `session_drain_wait` sends up to the hold, and the bytes after it stay
queued. The gate has four states (`SESS_GATE`):

| State | Meaning |
|---|---|
| `GATE_OFF` | Everything queued may go. |
| `GATE_COUNT` | A command-mode command is running. `send_buf` counts the rows it prints (LFs: every row agora sends ends CR LF). |
| `GATE_PAGED` | Stopped at `--More--`. The rest waits for a key. |
| `GATE_TYPE` | The teletype. The hold advances with the clock. |

### Page stops

`process_rx` opens `GATE_COUNT` around each command-mode command, with a page of NAWS rows − 1.

- **When it stops.** When a page is full, the next byte stops it. The `--More-- (Enter; q to stop)` prompt is
  queued, the hold is set after it, and the prompt's erase (CR, spaces, CR: plain, for any terminal) is queued as
  the first held byte. The command prompt is sent after the command, so it is held behind the page like everything
  else.
- **Keys.** `q` or `n` drops what is held and prompts again; any other key releases the next page.
  `term_page_stop` finds where that page ends, and never stops a page on its last, unterminated row (the prompt
  alone).
- **LINEMODE EDIT.** A client in LINEMODE EDIT sends whole lines, so the end of its line decides, using the line's
  first key.
- **Which sessions.** A page needs a reported width (rows are counted after wrapping) and at least
  `PAGE_MIN_ROWS` (5) rows. `more off` turns it off for the session.
- **Leaving command mode.** A command that leaves command mode (a door, chat, the Descent, a login) lifts any
  stop, because nothing there would turn it.

### The teletype

The Handler marks where its cable starts in the frame (`g_door_type_from`). `door_send_frame` sends what comes
before the mark whole, then opens `GATE_TYPE`.

- **Rate.** `gate_tick` releases `TYPE_CPS` (240) characters a second: 2400 baud, ten bits a character.
- **Who gets it.** Only a client that reported a window. A script that never does gets its frames whole, as before.
- **Skipping.** Any key skips to the end and is consumed. It never reaches the door.

### The greeting

At accept only the option salvo goes out. The MOTD and the first prompt go out (`greet_settle`) at whichever of
these comes first:

- the client declines TERMINAL-TYPE (WONT);
- it names its type (SB IS, two round trips after our DO);
- its first typed byte arrives;
- a deadline passes: `GREET_RAW_MS` (250 ms) for a client that has sent nothing at all, `GREET_TYPE_MS` (1 s) for
  one that is negotiating.

`session_colour` is 0 for `DUMB` and `UNKNOWN` (`term_type_plain`). `emit_sgr` and `render_motd` then write no
SGR, and an operator's `--motd` file goes out with its escapes stripped (`term_strip_esc`).

### Both serve models

- **Poll.** The sweep runs the two timers (`greet_settle`, `gate_tick`) before its drain. `serve_poll_wait` asks
  for POLLOUT only for bytes the gate releases (`sess_tx_limit`), and wakes for the timers.
- **Fork.** While the gate is on, or held bytes are still queued, the child queues too and writes what the gate
  releases at once (`gate_flush`). A short write is a failure and sticky, as since 1.8.2. Otherwise it writes the
  socket directly, exactly as before. Its wait is cut to the timers, and a wait that ends for one is not idleness.

### Bounds

- **Telnet replies are not content.** `send_proto` inserts them ahead of the hold, so negotiation never waits
  behind a page nobody has turned.
- **Room before stops.** A held queue cannot drain past its hold, so a command that must make room lifts the gate
  instead of being dropped (the 1.8.1 S5 rule). The rest of that output is then neither paged nor paced.
- **Shutdown.** Both models drop held output (`gate_drop`) before the goodbye.

## Consequences

**Positive**

- One mechanism, shared by both serve models, carries all three features. Paging covers every command-mode
  command, not only `list` and `read`.
- No command changed. The gate sits in `send_buf`, the single choke point ADR 0023 already relies on.
- No allocation. Held output lives in the 128 KB queue each slot already has. The insert for the next page's
  prompt is an in-place move.
- The teletype is skippable and off for scripts, so a session that does not want it loses at most one keypress.

**Negative**

- **A raw client's first prompt comes 250 ms later.** That is a client that never negotiates: netcat, a script, a
  bare socket. Its first typed byte greets it at once. A real telnet client is greeted when its type arrives,
  within two round trips. Even a client that declines at once costs one more wake before its greeting, so poll's
  sequential accept rate is about 23 % lower (BENCHMARKS.md § Serve-level — 1.13.0). `benches/serve-bench.py` now
  declines the type as it connects, so it measures that and not the 250 ms wait.
- **Paging gives way to room.** A command whose output is larger than the 128 KB queue is paged until it fills
  the queue, then sent unpaged. A `list` of thousands of posts is the case. A cursor that regenerates output across
  sweeps would remove the limit, at the cost of making every command resumable.
- **A pipelined line after a page stop is a key.** A script that sends NAWS and pipelines commands should send
  `more off` first. Smoke 36, which reports 40x24 to test the width, does not need to: its replies are shorter
  than a page.

**Neutral**

- The idle reaper (60 s) still applies while a page is stopped, as it does at the prompt.
- The Descent forwards the client's NAWS to the MUD. A resize during a visit is still not seen by agora (ADR 0030).

## Alternatives considered

- **Block for the key inside the command.** This is the classic BBS `more`, and it is correct under fork. Under
  poll it stops every session. Even under fork the child would read the socket from inside a command, behind
  pipelined bytes `process_rx` has not run yet.
- **Make commands resumable** (a cursor per command: `list` from post N, `read` from byte K). This has no queue
  bound, but it means every command that prints much becomes a state machine, for a feature that is a convenience.
  Revisit if the 128 KB bound bites.
- **A separate held-output buffer per session.** It would double the slot's output memory for no gain: the tx
  queue already is that buffer.
- **Greet at once, in colour, and switch colour off for later output.** The greeting is where most of the colour
  is, so a DUMB terminal would still get it.
