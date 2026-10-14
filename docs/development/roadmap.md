# agora — Roadmap

> **Last Updated**: 2026-10-13 — **1.11.1 (enforced module invariants) shipped**, closing the 1.11.x line: a
> door's free can no longer reach the session's world buffer, the chat couch and the `play` / `scores` names
> come from the door registry, and a test walks every registered door — slots, a drive, a save round trip, a
> leak check. Next slot: **1.12.0**, Olympiad events + door content. The same day: 1.11.0 (Descent as a session
> state, ADR 0031), 1.10.1 and 1.10.0 (the 1.10.x line), 1.9.2, 1.9.1, 1.9.0, 1.8.2; 1.8.1 and the re-plan into
> 1.8.x → 1.12.x slots on 2026-10-12 (per-tag detail in [`CHANGELOG.md`](../../CHANGELOG.md)).
>
> **What this file is**: what is planned next and in what order, what is blocked on someone else, and what
> is deliberately not being done. **What it is not**: a second changelog, or a record of what each closed
> item turned out to be — that lives in `CHANGELOG.md` and the [audit ledger](../audit/). The live snapshot
> lives in [`state.md`](state.md). Per [first-party-documentation § Development Docs](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#development-docs-docsdevelopment).

agora is the BBS userland for AGNOS — Greek ἀγορά (civic-marketplace / public-assembly). **Cross-platform
from M1**: built on cyrius `lib/net.cyr` socket primitives + `lib/io.cyr` / `lib/fs.cyr` storage. Linux and
AGNOS ship today; macOS and Windows follow as the stdlib gains backends
([ADR 0001](../adr/0001-cross-platform-listener-decoupled-from-agnos.md)).

**Every planned item cites its source** — a `file:line`, an ADR, an audit finding, or a CHANGELOG entry.
If an item has no citation it does not belong here. When an item ships, delete its row and let the
CHANGELOG carry it; do not leave ✅ rows behind.

---

## Release plan

Ordering: **verify and measure first** (1.8.x), then the scale work those numbers unlock (1.9.x), then the
protocol (1.10.x), then structure (1.11.x), then content (1.12.x). Version numbers are **slots, not
promises**: a toolchain cut or an urgent fix takes the next free patch number (as 1.6.1, 1.6.7 and 1.7.1
did) and the slots after it shift.

| Slot | Theme | Kind | Status |
|---|---|---|---|
| **1.9.2** | Board policy + operator CLI (closes the 1.9.x line: 1.9.0 store hardening, 1.9.1 reply index) | feature | ✅ 2026-10-13 |
| **1.10.0** | Telnet conformance | protocol | ✅ 2026-10-13 |
| **1.10.1** | Terminal-aware output (closes the 1.10.x line) | protocol / UX | ✅ 2026-10-13 |
| **1.11.0** | Descent as a poll state + serve-model debt | structure | ✅ 2026-10-13 |
| **1.11.1** | Enforced module invariants (closes the 1.11.x line) | structure | ✅ 2026-10-13 |
| **1.12.0** | Olympiad events + door content | content | planned |
| **1.12.1** | Wager audit trail | content / fairness | planned |
| 1.x | Cross-repo and toolchain-blocked work | — | blocked — see § Unscheduled |

---

## 1.12.x — doors and content

### 1.12.0 — Olympiad events + door content

| Item | Source | Effort |
|---|---|---:|
| **Olympiad's later events** (gladiators / athletics / boat crews) — thin descriptors on the `compete()` primitive, which was the whole point of building it | [ADR 0016](../adr/0016-olympiad-competition-primitive.md) | medium |
| The Olympiad race field is not tier-scaled — a flat 4 entrants at every meet | `src/olympiad.cyr` | small |
| **Decode/Words rejects most real English words** — the 532-entry list is both answer pool *and* guess dictionary; split them | [ADR 0018](../adr/0018-decode-engine.md); `src/decode_words.cyr` | small |
| **A real daily ration** — Smuggler, Port Authority and The Handler advance a day whenever the player presses the next-day key, and Olympiad's refill is free (`OL_LASTDAY` is saved, never read), though ADRs 0009 / 0010 / 0016 describe a wall-clock cadence. QUEST is the model. | audit 1.8.1 I4, I5 | medium |
| Ashes never resets after one player holds all twelve provinces — the world is closed to everyone else for good | audit 1.8.1 I6 | small |
| Every Port Authority Universe ship starts from one seed (`DD_UNI_SEED`), so combat rolls are identical for all players | audit 1.8.1 I7 | small |

### 1.12.1 — Wager audit trail

| Item | Source | Effort |
|---|---|---:|
| ADR 0013's wager audit trail and the commit-reveal provable-fairness alternative | [ADR 0013](../adr/0013-wagering-module-rng-fairness.md) | medium |

---

## Unscheduled — blocked on someone else

| Item | Where it is blocked | Effort |
|---|---|---:|
| **Sigil identity hand-off across the Descent link** — carry `g_session_fp` / handle into the MUD so a citizen does not re-authenticate. The project's long-standing named "next". | Yeoman's Descent has **no external-identity path** (name + passphrase only), so this needs MUD-side protocol work first. Open questions unchanged from [ADR 0017](../adr/0017-descent-link-gateway.md) § Decision: token format, trust model, co-located vs remote. | large |
| **macOS / Windows ports** | Gated on `lib/net.cyr` backends upstream; the gate has moved since the 1.0.0 note — re-check what actually remains. `$HOME` keyfile resolution (`/proc/self/environ`) is blocked on the same work. | large |
| **Tell a slow reader from a stalled one by delivered bytes** (fork mode) — today a write that gets no send-buffer room for 60 s drops the client; the exact test is "did the client acknowledge anything in 60 s", which keeps any reader that is still reading however full the kernel's queue | A `lib/net.cyr` primitive for the unacknowledged-byte count (`SIOCOUTQ` / `TCP_INFO`); agora does not issue raw socket syscalls. Found at 1.8.2 (CHANGELOG § Fixed). | small |
| **Accept-loop rate limiting** — the never-taken half of 0.7.0 audit M4's fix (M4's board-spam half closed at 0.8.3 with the create gate). Re-checked at 1.11.0: a per-source cap still needs the client's address, and agnos — the target that always polls — has neither `getpeername` nor a peer address from `sock_accept` (#57 returns a bare connection id), so it would protect Linux only; ADR 0023 also notes it misfires behind NAT. The operator's tools stay `MAX_SESS` and the network edge. | agnos `getpeername` (or a peer address from accept) and a stdlib `sock_accept_from`; 0.7.0 audit M4, ADR 0023 | large |
| **Close the directory guard's `stat`-then-`open` window** — `store_dir_scan` refuses a non-directory with a `stat` first, because the stdlib's `dir_list_into` opens with a plain `O_RDONLY` and a FIFO there blocks; the swap race between the two closes when the stdlib opens with `O_DIRECTORY` | cyrius `docs/development/issues/2026-10-13-dir-list-opens-directory-without-o-directory.md` (filed at 1.9.1; CHANGELOG § Security) | small |
| **Binary strip / DCE-aware emit** — promised three times as a "v1.x close-out concern" | Toolchain-side: `CYRIUS_DCE=1` NOP-fills dead code but keeps its bytes and all `.bss` (the ~375 KB static-data warning). | medium |

---

## Later — v2.x and speculative

Detail in [`roadmap-future.md`](roadmap-future.md). Unpinned by design: these pull forward when consumer
pressure or operator demand surfaces, not on a calendar.

- **The six v2.x sovereignty pillars** — identity continuity, content-addressed storage, threat-level node
  policy, federation by interest, self-distribution, offline store-and-forward. They are the blocking
  dependency for work already half-promised elsewhere: federated `Origin:` / content-addressed
  `Content-Hash:` post headers are the *stated justification* for the 0.9.0 ABI freeze
  ([ADR 0008](../adr/0008-post-headers-struct.md)) and remain unrealized.
- **Door depth** — QUEST async-PvP (the largest missing piece of the LORD homage), The Handler v2
  community layer (intercepted rival traffic, inter-section sabotage), Port Authority's deep TradeWars
  endgame.
- **Ashes turn resolution has no daemon**; its premise ("under fork-per-accept with no background
  process") is half-false since the poll model shipped ([ADR 0023](../adr/0023-dual-serve-model.md)).
- **Chatbot personalities** — ALICE / Racter on the script engine; MegaHAL as a Markov sibling to
  Jabberwacky's retrieval.
- **Protocol reach** — cross-board replies (Reply-To is same-board only); operator opt-in for raw-mode
  ESC/ANSI-art posts (now an explicit exception to [ADR 0024](../adr/0024-egress-text-sanitization.md));
  16 → 32 hex fingerprint widening; wire encryption (ADR 0006 § Negative points at a pillar that does not
  exist in roadmap-future yet).
- **M3** inline-image post bodies via kii, **M4** stored-file deltas via sankoch — gates met, no consumer.

---

## Deliberately not doing

Recorded so nobody re-opens them by accident:

- **Per-source-address session caps** — needs `sys_getpeername`, which **agnos does not have**, so it
  would protect Linux and leave the only always-poll target unprotected; it also mis-fires on a NAT'd
  LAN. Declined at 1.6.4; `MAX_SESS` remains the operator's bound.
- **Absolute session lifetime caps** — would disconnect legitimate long sessions (a QUEST run, an idle
  chat). Declined at 1.6.4.
- **Rate-limiting option re-negotiation** — toggling WILL/WONT TERMINAL-TYPE or LINEMODE yields ~2× output,
  but it returns to the client's own socket over TCP (no reflection) and the 128 KB tx queue bounds it.
  Accepted at 1.8.1 (audit I1).
- **Adopting darshana's `tty_open_signalfd`** for the N1 shutdown — its AGNOS arm blocks the signals, and
  under mirshi a blocked signal is never delivered through a signalfd. Re-checked and declined at 1.8.0.

---

## Shipped

One row per release line; per-tag narrative, numbers and findings are in [`CHANGELOG.md`](../../CHANGELOG.md).

| Line | Tags | What it delivered | Closed |
|---|---|---|---|
| M0–M6 + pre-1.0 hardening | 0.1.0 – 0.9.2 | scaffold; cross-platform telnet listener (RFC 854 / 1143 / 1073 / 1091 / 1184); ANSI MOTD; boards + threads; sigil auth + per-board policy; 0.7.0 security sweep; fork-per-accept; PostHeaders ABI freeze | 2026-05-23 |
| **v1.0** | 1.0.0 | all six criteria met; iron-validated on archaemenid (telnet round-trip + 8-user fanout) | 2026-05-23 |
| Door arc | 1.1.0 – 1.4.3 | Smuggler's Ledger, Port Authority, The Handler; Persistent Universe; chat + Eliza / PARRY / Jabberwacky; QUEST; wager + casino; Olympiad; Ashes of Empire; Descent link; Decode (Mastermind / Wordle + the Handler lever) | 2026-06-14 |
| P(-1) hardening | 1.4.4 – 1.4.6 | 2026-06-15 audit; send timeout + bounds follow-ups; door descriptor registry | 2026-06-15 |
| Targets + serve models | 1.5.0 – 1.6.7 | agnos target; single-process poll multiplex (`AGORA_SERVE`); per-command arena; `DD_FREE`; 2026-07-26 audit ledger closed; doc-truth cut; toolchain to 6.5.33 | 2026-08-22 |
| Durability + egress | 1.7.0 – 1.8.0 | clean shutdown (signalfd); crash-safe door / world / chat writes; poll holes; IAC fuzz harness; `Result` value form; darshana 1.3.0 + egress sanitization (2026-10-12 audit closed) | 2026-10-12 |
| Audit + repair, tooling | 1.8.1 – 1.8.2 | six-slice audit, 41 fixes (poll fairness, vendored-allocation leaks, fail-closed policy, door save lifecycle, loader bounds, fork caps); then the Closeout Pass in CI, serve-layer unit tests, generated version string, serve-level baselines | 2026-10-13 |
| Storage, scale, policy | 1.9.0 – 1.9.2 | store opens refuse symlinks and FIFOs (files and directories); crash-safe post publish; the handle index (unknown login O(1)); the reply index (`read` O(replies)); `.admins` read whole and keyed on fingerprints; four board modes that each mean something (members-only, anonymous posting); `agora policy` / `agora admins`; chat channel cap; the slot risk recorded (ADRs 0025–0028) | 2026-10-13 |
| The wire | 1.10.0 – 1.10.1 | RFC 854 / 1184 conformance — agora as the LINEMODE server (MODE and SLC answered, echo handed to an editing client), AYT, a line editor for character-mode clients, NVT egress; then output wrapped to the client's NAWS width (door frames, `list`, `read`, chat, `help`), byte-identical without one; a second fuzz harness (ADRs 0029–0030) | 2026-10-13 |
| Structure | 1.11.0 – 1.11.1 | the Descent as a session state (no more stalled poll server; the return resyncs the client's telnet options), readiness-driven serve loops (`AGORA_SERVE=epoll` refused), fork children that leave with their parent; then the door registry's invariants enforced — one release point that keeps a door's free off the session's world buffer, the chat couch and the command names in the registry, and a conformance test over every door (ADRs 0031, 0020 / 0022 amendments) | 2026-10-13 |

---

## Cross-references

- [`state.md`](state.md) — live snapshot: current version, binary size, in-flight slot, next-session boot guide.
- [`roadmap-future.md`](roadmap-future.md) — v2.x sovereignty pillars + long-horizon door / chatbot backlog.
- [`docs/adr/`](../adr/) — 31 ADRs (0001–0031). 0001–0008 span M1–0.9.0; 0009–0020 the 1.x door arc;
  0021–0022 the 1.6.x memory work; 0023 the dual serve model; 0024 egress text sanitization; 0025–0026
  the 1.9.0 store work (regular-file opens + crash-safe publish; the handle index); 0027 the reply index;
  0028 the board policy modes; 0029 telnet conformance; 0030 terminal-aware output; 0031 the Descent as a
  session state.
- [`docs/audit/`](../audit/) — audit ledger: 2026-05-23 (0.7.0), 2026-06-15 (1.4.4), 2026-07-26 (1.6.2,
  closed at 1.6.5), 2026-10-12 (1.8.0, closed in the same cut), 2026-10-12-audit-1.8.1 (closed in the same cut).
- [`docs/architecture/`](../architecture/) — non-obvious constraints (001 callptr, 002 lib-sync same-size skip).
- **Companion project**: [Yeoman's Descent](https://github.com/MacCracken/cyrius-yeomans-descent) — the MUD
  userland. Same telnet substrate, different application semantics; linked by the 1.4.0 gateway.
