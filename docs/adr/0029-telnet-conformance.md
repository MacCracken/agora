# 0029 — Telnet conformance: agora as the LINEMODE server, and the line editor

> **Status**: Accepted
> **Date**: 2026-10-13 — 1.10.0

## Context

CLAUDE.md makes RFC 854 and RFC 1184 authoritative — "any deviation is a bug, not a feature" — and by 1.9.2
roadmap § 1.10.0 listed seven deviations in `src/telnet.cyr` and the egress path:

1. **AYT** produced no response. RFC 854: "Send back to the NVT some visible (i.e., printable) evidence that
   the AYT was received."
2. **DO LINEMODE** was never sent, though RFC 1184 § 2.1 says DO LINEMODE "should only be sent by the server
   side" and WILL "only by the client side". So the LINEMODE machinery ran only when a client volunteered,
   which a conforming client does not.
3. **SLC** was "parsed-and-discarded"; its comment described a validation that was never written, and a
   client's SLC export (which § 5.5 obliges a LINEMODE client to send) went unanswered.
4. **Subnegotiations for other options** were dropped "for now".
5. **FORWARDMASK / SOFT_TAB / LIT_ECHO** were "deferred". The FORWARDMASK arm was also dead code: it compared
   byte 1 of the subnegotiation with the FORWARDMASK code, but on the wire that byte is the verb (`LINEMODE DO
   FORWARDMASK …`).
6. **BS / DEL** did not edit the line for character-mode clients — 1.6.5 only stopped them being stored, so
   a typo could not be corrected at all — and IAC EC / EL were consumed and ignored.
7. **Egress newlines**: a CLI-authored post with LF-only lines (or a bare CR) went out as stored. RFC 854:
   "CR LF" for a new line, "CR NUL" for a bare carriage return, "in both directions".

Writing the RFC 1184 behaviour also surfaced a missing duty: § 2.2 requires a server that receives a MODE
*without* MODE_ACK and a different mask to **reply** — agora stored the mask and said nothing.

## Decision

**agora is the LINEMODE server: it asks for LINEMODE, answers MODE and SLC as § 2.2 and § 5.5 require, hands
echoing to an editing client, refuses what it does not use by rule, and edits the line itself for clients
that stay in character mode. Everything it sends is NVT text.**

- **AYT** → `\r\n[Yes]\r\n`, as BSD and netkit telnetd answer.
- **Announce** `IAC DO LINEMODE` (the salvo is five options). A client that agrees gets `MODE EDIT|TRAPSIG`; one
  that refuses or never answers stays in character mode.
- **MODE** (§ 2.2): with MODE_ACK the server switches and never replies; without it, the current mode is
  ignored and a different one is **agreed** — agora accepts any mode, because its own editor handles
  character mode — by switching and replying with the mask and MODE_ACK. Only the defined bits are kept.
  `SOFT_TAB` / `LIT_ECHO` are never requested (they only change how the client displays what it echoes) and are
  accepted when proposed.
- **Echo hand-off** (§ 2.2, ECHO): "When the server has negotiated WILL ECHO, the client should not echo". So
  when EDIT comes on agora says `WONT ECHO` and stops echoing — had it kept WILL ECHO, an editing client would
  not echo either and the user would type blind until Enter — and takes echoing back (`WILL ECHO`) if EDIT goes
  off.
- **SLC** (§ 5.5): agora has no special characters of its own and lets the client keep its own. An import
  request (`0 SLC_DEFAULT|SLC_VALUE 0`) is answered with every function, `func SLC_DEFAULT 0` where agora holds
  no value; an exported triplet is ignored when it equals the current setting (rule 1) or carries SLC_ACK
  (rule 2, server side), otherwise agreed and echoed with SLC_ACK (rule 3); a function past 30 is refused as
  `SLC_NOSUPPORT` (rule 4). A list that is not whole triplets is dropped. Every octet equal to IAC is doubled.
  The reply is bounded (`SLC_REPLY_MAX`, 250 bytes) and processing stops at the first triplet whose answer
  would not fit, so the table never claims a value agora did not ACK.
- **FORWARDMASK**: never used — in EDIT mode the client forwards whole lines, and nothing needs a character
  forwarded early. A client's FORWARDMASK subnegotiation is out of turn (§ 5.7: only the DO LINEMODE side
  negotiates it, and WILL / WONT answer a DO agora never sends) and is ignored.
- **Other subnegotiations** are discarded by RFC 855: they are legal only for an enabled option, and agora
  refuses STATUS, NEW-ENVIRON and the rest (the 1.8.1 gate). A rule, not a deferral.
- **Line editor** (`line_erase`, `process_rx`): BS, DEL and IAC EC erase the last *character* — a whole UTF-8
  sequence (RFC 854: "the last preceding undeleted character") — and IAC EL the line ("back to, but not
  including, the last CR LF"); while agora echoes, each erased character is wiped with BS SP BS. `input_byte_ok`
  still refuses to store BS / DEL; they are now consumed as edits before it.
- **NVT text on egress** (`text_nvt_iac`, `send_text`): a bare LF goes out as CR LF, a bare CR as CR NUL, CR LF
  unchanged — across chunk boundaries — and 0xFF as IAC IAC.
- **Replies are queued whole or not at all**: a three-byte negotiation, an AYT answer, a subnegotiation. A
  truncated `IAC SB …` with no `IAC SE` would make the peer parse later bytes as part of it.

## Consequences

**Positive**

- A real LINEMODE client (GNU inetutils `telnet` 2.8, driven in a pty by smoke 35 § G) negotiates the whole
  exchange — WILL LINEMODE, its SLC export ACKed, MODE EDIT|TRAPSIG ACKed, WONT ECHO — and edits lines locally.
- Character-mode clients (`nc`, most BBS clients) can correct typos.
- CLI-authored posts no longer staircase on a real terminal.
- The fuzz harness now drives the subnegotiation decoders (it had not since 1.8.1 — see below) and found two
  defects before release: the SLC reply buffer overflowed the stack on a long list, and function / modifier
  octets of 255 were not doubled.

**Negative**

- **Echo depends on the client's mode**: in LINEMODE EDIT agora does not echo, so a client that agrees to EDIT
  and then does not echo locally shows nothing. That is a broken client by § 2.2; character-mode clients are
  unaffected.
- **The Descent link proxies option negotiation raw.** The MUD may change the client's ECHO (and now its
  LINEMODE) state, and agora does not re-assert its own on return — pre-existing, but LINEMODE widens it.
  Recorded in roadmap § 1.11.0 (Descent as a poll state).
- Parser cost: the announce salvo is one option longer (132 → ~168 ns in `benches/bench_telnet.bcyr`); per-byte
  costs unchanged within noise.

**Neutral**

- `IP`, `AO`, `BRK` and RFC 1184's `EOF` / `SUSP` / `ABORT` are still consumed without effect: agora runs no
  process to interrupt and holds no output to abort.
- TOGGLE-FLOW-CONTROL, which § 2.2 says "should" accompany LINEMODE, is still refused.
- **Fuzz coverage gap closed**: since 1.8.1 a subnegotiation counts only for an agreed option, and the harness
  never agreed any, so pass 3 and the SLC sequence had been rejected at the gate. They now agree NAWS,
  TERMINAL-TYPE and LINEMODE first, and two invariants were added (no torn reply in the queue; the mode within
  its defined bits).

## Alternatives considered

**Insist on EDIT | TRAPSIG.** § 2.2 lets the server set those bits in its answer when a client clears them.
Rejected: agora's own editor makes character mode work, and refusing a client's choice buys nothing.

**Keep server echo in LINEMODE.** Simpler — no hand-off — but RFC 1184 § 2.2 is explicit that a client does not
echo while the server has WILL ECHO, so an EDIT-mode user would see their line only after Enter.

**Keep a full SLC table and offer agora's own special characters.** Would let agora steer the client's
editing keys; it has no reason to, and § 5.5 describes exactly the "use the client's values" case taken here.

**Request SOFT_TAB / LIT_ECHO.** Both change only the client's rendering of its own echo; nothing in agora
depends on either.
