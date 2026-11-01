# 0036 — Raw boards: ANSI art by the operator's choice, and nothing else unsanitized

> **Status**: Accepted
> **Date**: 2026-10-31 — 1.13.1; amends 0024

## Context

[ADR 0024](0024-egress-text-sanitization.md) neutralizes every control byte and escape sequence in stored text
at egress. Ingress drops ESC too (`input_byte_ok`). That is right for a board of prose, and it rules out a BBS
staple: ANSI art, which is text plus SGR colour and cursor moves. `input_byte_ok`'s comment has carried "future
operator config may add an opt-in flag for raw-mode posts" since M5, and roadmap § 1.13.1 asked for it as "an
explicit exception to egress sanitizing".

Raw output is exactly what ADR 0024 exists to stop. Escape sequences can:

- retitle the window, or write the clipboard (OSC 52);
- make the terminal answer, with a cursor report (DSR), its identity (DA) or its title (CSI 21 t), and the
  answer arrives as the reader's input;
- switch a mode: mouse reporting, bracketed paste, the alternate screen.

None of that is art.

## Decision

**A board whose directory holds a `.raw` file keeps ESC in composed posts. Reading it lets through one class of
CSI: colour, cursor movement and erase. Everything else is sanitized as before.**

- **The flag.** `agora raw set <board> on|off` writes or removes `<board>/.raw`, and `agora raw get` reports it.
  The file is read through `store_open` (regular files only, no symlink, never a FIFO), and its contents do not
  matter. It is separate from `.policy`, whose parser fails closed on any unknown token, so an older agora reading
  a raw board's `.policy` is unaffected.
- **Ingress.** While composing a post body on a raw board (`post` / `reply` record it in `SESS_POST_RAW`),
  `process_rx` keeps ESC. Every other C0 byte, DEL and IAC are still dropped, and so is ESC in a subject.
- **Egress** (`send_art`). The allowed sequence is ESC `[`, parameters of digits and `;` only (no private marker,
  no intermediate byte), and a final byte of `m` (SGR), `A`–`G` (cursor moves), `H` / `f` (position), `J` / `K`
  (erase) or `s` / `u` (save and restore the cursor), at most 32 bytes in all (`art_csi_len`). It goes out whole.
  - Any other ESC is neutralized as ADR 0024 has it: its sequence's ESC becomes `?` and the rest is text, so an
    OSC arrives as visible characters, never a live sequence.
  - NVT newlines and IAC doubling apply as on every board.
  - The body is not wrapped, since art is drawn for its own columns.
  - An SGR reset follows the body, so its colour cannot run into the rest of the reply.
- **A terminal that takes no colour** ([ADR 0034](0034-output-gate.md): DUMB, UNKNOWN) gets the art with its
  escape sequences removed, as an ordinary post.
- **The CLI.** `agora post` already stores its stdin body unfiltered, so CLI-authored art works on a raw board
  without change. `agora read` still prints through `write_text`, sanitized: the operator's own terminal is not a
  raw board's reader.

## Consequences

**Positive**

- ANSI art works on the boards the operator chooses, with no change to any other board.
- The exception is a whitelist, so what a raw board can do is listed in one function, and every sequence that
  could act on the reader's terminal outside the art's own drawing stays neutralized.

**Negative**

- **Art can still misuse what it is allowed.** It can clear the screen (`CSI 2 J`) or move the cursor over
  agora's own output, as art does. That is the trade the operator opts into. Nothing beyond the screen is
  reachable.
- **CP437 art shows `?` where its high bytes are**, as all non-UTF-8 text does in agora (ADR 0024). Art has to be
  converted to UTF-8 first.
- Paging ([ADR 0034](0034-output-gate.md)) counts LFs, so art that positions its own cursor can stop at a place
  that is not the bottom of what it drew.

**Neutral**

- `list`, `boards` and the subjects of raw posts are unchanged: subjects never keep ESC.
- The flag is per board, not per post. A post moved to a raw board by hand is shown as art.

## Alternatives considered

- **A raw token in `.policy`.** One file instead of two, but the 1.9.2 parser fails closed, so every older agora
  would read a raw board as admin-only.
- **Pass every CSI.** That still includes DSR, DA, window reports and mode switches, which are the sequences that
  turn a reader's terminal against them.
- **Per-post raw, set by the author.** It would hand the decision to any registered user, which is what ADR 0024
  took away.
- **Strip on ingress and re-add colour from a markup** (`{red}` and the like). That is a different feature: it
  would not carry existing ANSI art, which is the point.
