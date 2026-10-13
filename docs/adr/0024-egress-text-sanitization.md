# 0024 — Stored text is sanitized at egress, in UTF-8 mode

> **Status**: Accepted
> **Date**: 2026-10-12 — 1.8.0

## Context

A BBS prints other people's text. Every post body, subject and author handle that a reader sees was
written by someone else, and whatever control sequences that text holds, the reader's terminal executes:
a CSI repaints or clears the screen, an OSC retitles the window or (OSC 52) writes the clipboard, a DCS is
acted on by some terminals.

agora defended this at **ingress** only, and per byte. `input_byte_ok` (board.cyr) drops C0 except
TAB / CR / LF, DEL and IAC from wire input; `header_text_ok` refuses C0 in subjects. Two gaps survived,
both demonstrated end to end by `docs/examples/29-egress-sanitize.py` against the 1.7.1 binary:

1. **C1 controls.** The filters pass every byte 0x80–0xFE so non-ASCII text can be posted. That range
   holds the C1 controls, raw (0x9B is the 8-bit CSI, 0x9D OSC, 0x9C ST) and UTF-8-encoded (`C2 9B` is
   U+009B, a CSI to any terminal that honours C1 controls). A registered user's post of `C2 9B 2 J`
   reached each reader verbatim — a screen clear on such a terminal; `C2 9D 52;c;… C2 9C` an OSC 52
   clipboard write where OSC 52 is honoured. A per-byte filter cannot separate these
   from text: `9B` is also a UTF-8 continuation byte.
2. **Bytes no filter ever saw.** `agora post` stores its stdin body with **no** filter (the comment on
   `input_byte_ok` claimed the CLI refused these bytes; only `--subject` is checked). A CLI-authored body
   carried a plain `ESC [2J` and BEL to every wire reader. Posts written before a filter existed, and
   files edited on disk, are the same case. `agora read` / `agora list` printed all of it raw into the
   operator's own terminal.

`send_text`, the one function every stored string leaves the server through, only doubled IAC (1.6.4).

darshana 1.2.0 shipped `tty_sanitize_buf(buf, pos, src, len, mode, keep)`: the ecosystem's one audited
output sanitizer ([darshana ADR 0004](https://github.com/MacCracken/darshana/blob/main/docs/adr/0004-output-sanitization.md)),
frozen by digest. Every neutralized byte or sequence becomes one `?`; ESC can never be kept; the output is
never longer than the input; it is pure and allocation-free. It has two modes, because raw 0x80–0x9F are
C1 controls to a Latin-1 terminal and ordinary continuation bytes to a UTF-8 one.

## Decision

**Stored text is neutralized at egress with `tty_sanitize_buf` in `TTY_SANITIZE_UTF8` mode, keeping
TAB, LF and CR; the stored artifact is never rewritten.**

- **Where**: inside `send_text` (main.cyr) — every wire egress of stored or user-derived text — before the
  existing IAC pass, and in its stdout twin `write_text`, which `agora read` / `agora list` now use.
  1.8.0 also routes the two stored-string sites that bypassed `send_text` through it: `boards`
  (directory names read off the disk) and leaderboard rows. The rule lives in one pure function,
  `text_sanitize` (board.cyr), so `src/test.cyr` can pin it.
- **Mode: UTF-8.** An agora session is UTF-8 by construction: agora negotiates no CHARSET option
  (RFC 2066), and its own output — the MOTD's em dash, the help text — is UTF-8. UTF-8 mode passes every
  well-formed UTF-8 sequence byte-for-byte, so posts with accents, `€` or emoji read exactly as before,
  and it neutralizes C1 in both forms: encoded C1 as one `?`, and a raw 0x80–0x9F byte, which in UTF-8
  can only be a stray continuation byte, as malformed input.
- **Kept C0**: TAB, and CR + LF together, because CR LF is the NVT newline (RFC 854) every stored body is
  written with. darshana names `TTY_KEEP_TAB` / `TTY_KEEP_LF`; agora adds bit 13 (`TEXT_KEEP_CR`).
- **Chunking**: both writers sanitize in bounded stack chunks (`TEXT_CHUNK_MAX` = 504 bytes in), so the
  per-line path allocates nothing ([ADR 0021](0021-per-command-scratch-arena.md)). `text_chunk_end`
  never cuts a UTF-8 sequence, which makes chunked output byte-identical to one-shot output (t224).
- **IAC doubling stays**, after sanitizing. In UTF-8 mode no 0xFF can survive (it is never valid
  UTF-8), so the pass is defence in depth against a later change of mode.

Out of scope: text a user sees only from themselves (their own echo, a chatbot reflecting their own line,
`whoami`) — self-only, not cross-user; the operator's `--motd` file, which is deliberately raw ANSI art;
and the Descent proxy, which carries the MUD's own (legitimately ANSI) stream byte-transparently
([ADR 0017](0017-descent-link-gateway.md)).

## Consequences

- **Positive** — one rule covers every stored string, whatever wrote it and whenever: wire posts, CLI
  posts, pre-filter posts, hand-edited files. Old posts are fixed without migrating anything.
- **Positive** — the stored post stays exactly what its author wrote, so the "posts are durable
  artifacts" principle holds, and the raw bytes remain on disk for an operator who needs them.
- **Positive** — the rule is darshana's, frozen by digest; agora owns only the mode, the keep set and
  the chunking.
- **Negative** — a reader on a **Latin-1 / 8-bit-C1** terminal is not fully protected: a well-formed
  UTF-8 character can contain a byte such a terminal reads as C1 (`€` is `E2 82 AC`; U+20DB is
  `E2 83 9B`). That terminal already misrenders agora's own UTF-8 output, so agora does not serve it
  correctly today; protecting it would mean per-session charset negotiation, not a second rule here.
- **Negative** — a byte the sanitizer neutralizes is shown as `?`, so a post containing malformed UTF-8
  (or Latin-1 text typed on a Latin-1 client) displays with `?` where those bytes were.
- **Neutral** — sanitizing costs a pass over each stored string per read; posts are at most 64 KB, and
  it adds no allocation.

## Alternatives considered

- **Sanitize at ingress, store clean.** Covers neither CLI-authored nor already-stored posts, rewrites
  the artifact, and cannot be done by `input_byte_ok`, which sees one byte at a time with no UTF-8 state.
- **Latin-1 mode.** Turns the continuation bytes of most non-ASCII characters into `?` (`€` → `?` `?`),
  breaking the UTF-8 text agora otherwise carries intact.
- **Per-session mode from TERMINAL_TYPE.** A terminal-type string does not state a charset, and agora
  has no other signal; guessing would make one user's post render differently per reader for no
  security gain on UTF-8 terminals.
- **Reject posts that contain controls (`tty_has_ctl`).** Blocks new wire posts only — the same gaps as
  ingress — and turns a display problem into a lost post.
- **Fold the pass into `send_buf`.** `send_buf` also carries the telnet layer's own command bytes; the
  1.6.4 split (protocol bytes via `send_buf`, content via `send_text`) is exactly the line this decision
  needs.
