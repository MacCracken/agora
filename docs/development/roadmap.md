# agora — Roadmap

> **Last Updated**: 2026-10-12 — **1.8.1 (code audit + repair) shipped**: 3 HIGH / 12 MEDIUM / 26 LOW fixed
> ([audit](../audit/2026-10-12-audit-1.8.1.md)). It also closed two rows planned for 1.9.0 (the `dir_list_into`
> migration and the O(n²) sort — both turned out to be security fixes); the audit's open INFO items are
> scheduled below with their IDs. Earlier the same day: re-planned into release slots — the backlog that
> accumulated since the 2026-07-26 sweep was scheduled into the **1.8.x → 1.12.x** minors, and shipped work
> collapsed to one row per release line (per-tag detail lives in [`CHANGELOG.md`](../../CHANGELOG.md)).
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
| **1.8.1** | Code audit + repair | hardening, no features | ✅ 2026-10-12 |
| **1.8.2** | Mechanical gates — CI runs what the cut checklist runs | tooling | planned |
| **1.8.3** | Measure — `tests/` split + serve-model benchmarks | tooling | planned |
| **1.9.0** | Storage residue + durable posts | correctness / memory | planned |
| **1.9.1** | Reply index | scale | planned — gated on 1.8.3 numbers |
| **1.9.2** | Board policy + operator CLI | feature | planned |
| **1.10.0** | Telnet conformance | protocol | planned |
| **1.10.1** | Terminal-aware output | protocol / UX | planned |
| **1.11.0** | Descent as a poll state + serve-model debt | structure | planned |
| **1.11.1** | Enforced module invariants | structure | planned |
| **1.12.0** | Olympiad events + door content | content | planned |
| **1.12.1** | Wager audit trail | content / fairness | planned |
| 1.x | Cross-repo and toolchain-blocked work | — | blocked — see § Unscheduled |

---

## 1.8.x — hardening and verification (no new features)

### 1.8.1 — Code audit + repair ✅

Shipped 2026-10-12: a six-slice full-tree audit, every finding verified and A/B'd against 1.8.0 — **3 HIGH,
12 MEDIUM, 26 LOW fixed**, 14 INFO recorded (the open ones are rows below, tagged with their audit ID).
Report: [`docs/audit/2026-10-12-audit-1.8.1.md`](../audit/2026-10-12-audit-1.8.1.md); summary in CHANGELOG
`[1.8.1]`. Delete this section when the 1.8.x line closes.

### 1.8.2 — Mechanical gates

Everything the cut checklist asks a human to do by hand that a script or CI step can do instead.

| Item | Source | Effort |
|---|---|---:|
| **Examples runner.** The README's "run them in order" contract does not hold: 09, 10, 18, 19 and 20 `rm -rf ./bbs ./keys` on exit, and six scripts (04, 05, 23, 25, 26, 27) are client-only and need an externally started server with a specific `AGORA_SERVE` model recorded only in their header comments. One runner that gives each smoke its own store/keys and the server it needs. | `docs/examples/README.md`; CHANGELOG [1.6.7] | small |
| **CI runs the smokes** through that runner, under both serve models. Today the 29 smokes are the only proof of the concurrency, serve-model and shutdown behaviour, and CI runs none of them. | `.github/workflows/ci.yml`; CHANGELOG [1.7.0] § Known limitations | medium |
| `cyrius fuzz --poison=ab` in CI and release (green by hand at 1.8.0; doubles the fuzz step's runtime) | CHANGELOG [1.8.0] § Verification | small |
| **aarch64 in CI**: `cyrius build --aarch64` + `cyrius test --aarch64` under qemu. 225/225 by hand at 1.8.0; only smoke 29 has ever run against an aarch64 binary, and nothing has run on aarch64 hardware. | CLAUDE.md § Goal; CHANGELOG [1.8.0] | small |
| **Toolchain-provenance pre-cut script** — `cmp` the local `~/.cyrius/versions/<ver>/lib` against `git show <tag>:lib/…`. Two defects found at 1.6.7: `install.sh --refresh-only` copies the cyrius *working tree*, and the versioned wrapper does not pin `cycc` (upstream: `cyrius/docs/development/issues/2026-08-22-versioned-wrapper-does-not-pin-cycc.md`). | CHANGELOG [1.6.7] § Verification notes; architecture note [002](../architecture/002-lib-sync-same-size-skip.md) | small |
| **Slow-reader close-path regression smoke** — a HIGH-severity 1.6.3 fix resting on inspection alone | CHANGELOG [1.6.3] § Security | medium |
| **State-sync check** — a CI/release step that fails when `state.md` or this file does not name `VERSION`. 1.6.6 and 1.7.1 both shipped without either recording them. | CLAUDE.md § CI / Release; CHANGELOG [1.6.7], [1.8.0] | small |
| Generated version string — the three version literals in `src/main.cyr` are hand-bumped every cut (since 1.8.1 CI at least checks all three); the generated `version_str.cyr` was promised as a v1.0 close-out item | CHANGELOG [0.2.0]; audit 1.8.1 hygiene H13 | small |
| **`cyrius audit` exits 1** — 176 lint warnings (all line length) and 358 undocumented public functions; the gate CLAUDE.md § P(-1) lists has never actually passed. Wrap the lines and document the functions, or record which checks are waived and why. | audit 1.8.1 I14 | medium |
| **CI supply chain** — the installer is fetched from cyrius `main` (unpinned), actions are pinned by tag rather than SHA, and `ci.yml` has no `permissions:` block. (The `curl \| sh` that could fail green was fixed at 1.8.1.) | audit 1.8.1 hygiene H18 | small |

### 1.8.3 — Measure

The numbers that four ADR "measure before refining" gates and the 1.9.1 reply-index decision are waiting on.

| Item | Source | Effort |
|---|---|---:|
| **`tests/` split.** `src/test.cyr` does not include `src/main.cyr`, so nothing in the serve loops, the session pool, `sess_tx_enqueue` or the N1 shutdown helpers can be unit-tested; N1 and N3 shipped covered by smoke 28 and inspection alone. Also clears `cyrius audit`'s `skip: no tests/ directory` and the test build's `undefined function 'send_str'` warning. | `src/test.cyr` include block; CHANGELOG [1.7.0] § Known limitations, [1.8.0] § Known limitations | medium |
| **Accept-loop rate and per-session memory**, both serve models — never benchmarked; CLAUDE.md P(-1) step 2 requires the baseline | CLAUDE.md § P(-1); [`BENCHMARKS.md`](../../BENCHMARKS.md) (parser only) | medium |
| **World-lock contention** benchmark — opens the ADR 0010 / 0014 "measure before refining" gates | ADRs 0010, 0014 | medium |

---

## 1.9.x — storage and scale

### 1.9.0 — Durable posts + store hardening

(The `dir_list_into` migration and the O(n²) `sort_i64_asc` planned here shipped early, in 1.8.1 — audit H1
and L5: the listing residue was an unauthenticated memory-exhaustion path, not a cleanup.)

| Item | Source | Effort |
|---|---|---:|
| **Crash-safe post writes.** CLAUDE.md's "posts are durable artifacts" principle is not yet backed — door saves, the shared world and chat went through atomic writes at 1.7.0, but a post is still `file_create_exclusive` + `file_write`. Since 1.8.1 a *short* write is cleaned up (audit L2); a *crash* mid-write still leaves a truncated post under its final id. Temp file + `link()` keeps the exclusive id claim. | CLAUDE.md § Key Principles; [ADR 0002](../adr/0002-one-file-per-post-storage.md); `src/board.cyr` `post_new` | medium |
| **Store opens follow symlinks and block on FIFOs** — a FIFO named `N.txt`, `.policy` or `.admins` hangs the whole poll server on the next `read` / `list` / `post`. Needs store write access. `O_NOFOLLOW` + `O_NONBLOCK` + an `S_ISREG` check on every store open. | audit 1.8.1 I11 | medium |
| **A handle index** — `account_resolve_handle` reads every user's `handle` file on every `login` (no early exit is possible for an unknown handle); at 301 users one 4 KB packet of `login x` held a 1.8.0 poll sweep 626 ms (1.8.1's line budget now contains the cross-session effect). `.users/.by-handle/<handle>` claim files created `O_EXCL` would also make registration atomic without the 1.8.1 lock. | audit 1.8.1 H1 / L4; `src/account.cyr` | medium |
| `.admins` stops at 4 KB (~120 handles) with no continuation — since 1.8.1 it at least fails closed (only whole lines are trusted, with a warning) | `src/board.cyr`; audit 1.8.1 M4 | small |

### 1.9.1 — Reply index

| Item | Source | Effort |
|---|---|---:|
| Reply enumeration is scan-on-read, O(n) per `read`. [ADR 0005](../adr/0005-threading-via-reply-to.md) named a scale trigger that has arguably fired; decide index-vs-scan on the 1.8.3 numbers, not by feel. | ADR 0005 | large |

### 1.9.2 — Board policy + operator CLI

| Item | Source | Effort |
|---|---|---:|
| **`open` and `known` are functionally identical** — a documented policy an operator can set and observe nothing from. Write the promised `anon-allowed` policy ADR and make the modes mean something (or collapse them). | [ADR 0006](../adr/0006-identity-model.md) | medium |
| **Operator CLI** — `agora policy set <board> <mode>`, `agora admins {add,rm,list}`. Operators edit `.policy` / `.admins` by hand today. | long-standing (0.6.0 closeout) | medium |
| Session-slot exhaustion by a slow-but-real typist is a knowingly accepted risk with **no recorded acceptance** — record it in ADR 0023 or bound it | CHANGELOG [1.6.4] § Changed | small |
| **`.admins` grants by handle**, and a key re-registered under a new handle frees the old one for anyone — key admin rights on the fingerprint (or accept both forms) | audit 1.8.1 I9 | small |
| Chat channel directories have no cap — any logged-in user can create unlimited `<store>/.chat/<name>/` | audit 1.8.1 I10 | small |

---

## 1.10.x — the wire

### 1.10.0 — Telnet conformance

RFC 854 and RFC 1184 are authoritative; each row is a deviation, and per CLAUDE.md a deviation is a bug.

| Item | Source | Effort |
|---|---|---:|
| **AYT** (Are You There) generates no response; RFC 854 expects visible evidence. No test pins either behaviour. | `src/telnet.cyr` | small |
| `telnet_announce` never sends **DO LINEMODE** — the Q-method machinery only engages if the client volunteers first | `src/telnet.cyr` | small |
| The LINEMODE **SLC** arm describes a validation that was never written | `src/telnet.cyr` | small |
| Unrecognised subnegotiations (STATUS, NEW_ENVIRON, …) are silently dropped "for now" | `src/telnet.cyr` | medium |
| LINEMODE **FORWARDMASK / SOFT_TAB / LIT_ECHO** — parsed or enumerated, then deferred | `src/telnet.cyr` | medium |
| **BS/DEL do not edit the line** for clients that never negotiate LINEMODE. 1.6.5 stopped them being *stored*; editing is still open, and will move `t32` again. | 2026-07-26 audit § INFO | small |
| **NVT newlines on egress** — a CLI-authored body keeps a bare CR or LF-only lines and goes out that way (RFC 854 wants CR LF / CR NUL); wire-authored bodies are always CR LF. Normalize in `send_text`, carrying CR state across chunks. | audit 1.8.1 I12 | small |

### 1.10.1 — Terminal-aware output

| Item | Source | Effort |
|---|---|---:|
| Negotiated terminal state (NAWS cols/rows, TERMINAL-TYPE, the LINEMODE mask) has **zero consumers** outside `telnet.cyr` — parsed and stored, never used to size or adapt output. First consumer: door frames and `list` wrapped to NAWS cols. | M2-D deferral | medium |

---

## 1.11.x — structure

### 1.11.0 — Descent as a poll state + serve-model debt

| Item | Source | Effort |
|---|---|---:|
| **The Descent proxy blocks the poll sweep** — a player in the MUD stalls the other 63 sessions for the whole visit, and a blackholed endpoint still costs up to 4 s per connect (1.8.1 added a 30 s redial cooldown and has the proxy watch the shutdown signalfd — audit L19). The fix is making Descent a session *state* in the poll loop rather than a blocking call; write the ADR first. | `src/descent.cyr` (documented, not fixed); [ADR 0017](../adr/0017-descent-link-gateway.md), [ADR 0023](../adr/0023-dual-serve-model.md) | large |
| `AGORA_SERVE=epoll` is accepted and silently aliased to `poll`; implement it or reject the value | `src/main.cyr` | medium |
| `PR_SET_PDEATHSIG` for orphan-on-parent-crash under the fork model | ADR 0007 § Out of scope | small |
| Accept-loop rate limiting — the never-taken half of 0.7.0 audit M4's fix. Blocked on a syscall agnos does not have; re-check before scheduling. | 0.7.0 audit M4 | large |

### 1.11.1 — Enforced module invariants

| Item | Source | Effort |
|---|---|---:|
| ADR 0022's borrowed world-snapshot pointer is an **unenforced per-module invariant** — door #11 can silently leak or corrupt the session pool | [ADR 0022](../adr/0022-door-state-free-hook.md) | medium |
| The chat-couch bot dispatch was left out of the descriptor registry; its shared-offset ABI (PY/EZ alias) is unenforced | [ADR 0020](../adr/0020-door-descriptor-registry.md) | small |
| ADR 0020 descriptor slots resolve at run time, so every new slot carries an untracked smoke-coverage obligation — turn it into a test | ADR 0020 | small |

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
| Audit + repair | 1.8.1 | six-slice audit, 41 fixes: poll fairness + vendored-allocation leaks, fail-closed policy, door save lifecycle, loader bounds, Descent visit bugs, fork caps | 2026-10-12 |

---

## Cross-references

- [`state.md`](state.md) — live snapshot: current version, binary size, in-flight slot, next-session boot guide.
- [`roadmap-future.md`](roadmap-future.md) — v2.x sovereignty pillars + long-horizon door / chatbot backlog.
- [`docs/adr/`](../adr/) — 24 ADRs (0001–0024). 0001–0008 span M1–0.9.0; 0009–0020 the 1.x door arc;
  0021–0022 the 1.6.x memory work; 0023 the dual serve model; 0024 egress text sanitization.
- [`docs/audit/`](../audit/) — audit ledger: 2026-05-23 (0.7.0), 2026-06-15 (1.4.4), 2026-07-26 (1.6.2,
  closed at 1.6.5), 2026-10-12 (1.8.0, closed in the same cut), 2026-10-12-audit-1.8.1 (closed in the same cut).
- [`docs/architecture/`](../architecture/) — non-obvious constraints (001 callptr, 002 lib-sync same-size skip).
- **Companion project**: [Yeoman's Descent](https://github.com/MacCracken/cyrius-yeomans-descent) — the MUD
  userland. Same telnet substrate, different application semantics; linked by the 1.4.0 gateway.
