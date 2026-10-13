# 0030 — Terminal-aware output: wrap to the window the client reports

> **Status**: Accepted
> **Date**: 2026-10-13 — 1.10.1

## Context

agora has asked every client for its window size since M1 (`IAC DO NAWS`, RFC 1073) and has parsed and stored
the answer (`telnet.cyr` `TS_TERM_COLS` / `TS_TERM_ROWS`), along with the terminal type (RFC 1091) and, since
1.10.0, the LINEMODE mode. Until 1.10.1 nothing outside `telnet.cyr` read any of it (roadmap § 1.10.1, the M2-D
deferral: "NAWS-aware width clamping ... an optional polish bite"). Every line was sent as written, so a line
wider than the reader's terminal broke wherever the terminal ran out of columns, in the middle of a word:

- door frames: menu lines up to 69 columns, and Jabberwacky's learned replies, which run as long as whatever
  a user taught it;
- `list` rows, whose subjects run to 256 bytes;
- post bodies (a CLI post can hold a 64 KB line), chat lines and the `Replies:` list of a busy thread;
- `help` (its `play` line is 143 columns);
- the greeting's tagline (149 columns).

Doing this properly takes a display-width model. The `list` subject is UTF-8: an accented letter is one
column, a CJK ideograph two, a combining mark none. Door frames carry SGR colour sequences, which take no
column at all. Neither darshana nor the stdlib has a width or wrap primitive (`bayan`'s are for PDF fonts).

## Decision

**Output is wrapped to the reported window, between words, and a client that has not reported one gets
exactly the bytes it got before.**

- **Width**: NAWS columns − 1 (a terminal without the VT100 last-column flag shows a full-width row followed
  by CR LF as a row *and* a blank line), at least 1. No report, or a width of 0 (RFC 1073: "no width is being
  sent"), means do not wrap. The width is read at every send, so a resized window takes effect on the next
  command.
- **The rule**: a line that fits is sent unchanged. A line that does not fit breaks at the last space or TAB
  that keeps the row inside the width. The whitespace at the break is dropped, and the row ends with CR LF and
  a hang (continuation indent). A word wider than a whole row is **never cut**: it goes out on its own row and
  the terminal wraps it. A hard newline inside a URL would break the copy that a terminal's own soft wrap
  keeps whole.
- **Columns, not bytes**: UTF-8 counts by character, with East Asian Wide / Fullwidth and the emoji blocks as
  two and combining marks as none (an approximation of `wcwidth`; terminals disagree on that table too). A
  TAB runs to the next multiple of 8. An escape sequence takes no column and is never split. A malformed byte
  counts as one column, because the sanitizer turns it into one `?`.
- **Hangs**: `list` rows hang under the subject (`1  [qix]  `); `read`'s `Subject:` and `Replies:` lines under
  their first word; `help` under the description column (18); chat lines after the speaker's `<handle> `; the
  chat-couch bot's reply after `ELIZA: `. Door frames and post bodies keep each line's own leading whitespace,
  so an indented list item or code line stays indented. A hang is capped at half the width.
- **The greeting** goes out before any NAWS can arrive, so its tagline is laid out for 80 columns.
- **Where**: `src/term.cyr` is pure (a resumable state machine with no allocation, writing chunks of any size,
  and its output does not depend on the chunk size). `send_wrapped` in `main.cyr` connects it to the session.
  Stored and user text is sanitized (ADR 0024) **before** it is measured, so the columns counted are the
  columns the reader sees. NVT newlines and IAC doubling follow, as in `send_text`. Door frames and literals
  go out raw (`TW_RAW`).

## Consequences

**Positive**

- A narrow terminal (a phone client, a split pane) reads every door, list, post and chat line whole-word, and
  a resize applies on the next command.
- `list` composes each row and sends it once: under fork that is one `write(2)` per row instead of seven, and
  a 300-post `list` fell from 16.2 to 4.2 ms.
- A client that sends no NAWS — every raw-socket smoke, `nc`, most scripts — sees byte-identical output
  (A/B-verified against 1.10.0 for `help`, `boards`, `list`, `read`).

**Negative**

- CPU: wrapping costs a measuring pass. A door frame that fits takes ~2.9 µs (`benches/bench_term.bcyr`), and
  a line known to fit (no TAB, its bytes within the row) is copied without being measured. The largest post,
  60 KB, costs 1.0 → 1.3 ms of poll CPU per `read` when its 70-column lines fit, and 1.7–2.1 ms when they wrap.
- `send_wrapped` sanitizes its buffer **in place**: it must be the caller's scratch, never a literal or a
  stored copy read again.
- The width table is an approximation; a character it gets wrong makes a row one column too wide or too
  narrow.

**Neutral / not in this release**

- **Rows** (NAWS height) and **TERMINAL-TYPE** still have no consumer. Paging (`--More--`) would change the
  input model mid-output, and colour by terminal type would need the greeting delayed until the type is known.
  Both are recorded in `roadmap-future.md`.
- **The Descent link** forwards the client's NAWS updates to the MUD, so a window resized during a visit is
  not seen by agora until the client next reports. Folded into roadmap § 1.11.0's "re-assert options on
  return".
- The CLI viewers (`agora list` / `read` to stdout) are not wrapped; an operator's terminal has `fold`.

## Alternatives considered

**A column-tracking wrapper inside `send_text` / `send_buf`.** This would wrap everything with no call-site
changes. Rejected: a word can only be placed once its end is known, so the wrapper would hold a partial word
across calls and need a flush at every prompt and every wait for input. It would also have to tell protocol
bytes from text inside `send_buf`, the very split 1.6.4 made explicit.

**Hard-wrap (cut) long words, like `fold`.** It is simpler and bounds every row, but it puts newlines inside
URLs and hashes that a terminal's soft wrap would keep copyable. The `fmt` behaviour was chosen instead.

**Wrap at the full width.** Every modern terminal has the last-column flag, but the old Windows console does
not, and losing one column costs nothing.

**Default to 80 columns when no NAWS arrives.** That would change the bytes every scripted client sees and
wrap output for clients wider than 80 that simply did not answer. Only a reported width is acted on.

**Upstream the width table to darshana.** The right long-term home, since darshana is the terminal-output
crate. But its API is frozen, and the addition would gate this release on a cross-repo cut. `term.cyr` is
pure and can move.
