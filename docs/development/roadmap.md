# agora — Roadmap

> **Last Updated**: 2026-10-14 — rebuilt at 1.12.1 as the single, forward-only plan. `roadmap-future.md` is
> folded in: its door, terminal and chatbot backlog and the six v2.x pillars now sit in the arcs below. The
> shipped history left with it: [`CHANGELOG.md`](../../CHANGELOG.md) is the record of what is done, and
> [`state.md`](state.md) says where agora stands today. Next slot: **1.13.0**.
>
> **What this file is**: everything agora means to build, in order, from the next release to 2.0 and past it,
> grouped into release arcs. **What it is not**: a history. When an item ships, delete its row (the CHANGELOG
> carries it); when an arc empties, delete the arc.
>
> **Rules**: every item cites its source (an ADR, an audit finding, a code comment, or a design section in this
> file). Version numbers are **slots, not promises** — a toolchain cut or an urgent fix takes the next free
> patch number (as 1.6.1, 1.6.7 and 1.7.1 did) and the slots after it shift. Work that waits on someone else
> sits in § Blocked with the arc it would join.

agora is the BBS userland for AGNOS — Greek ἀγορά (civic marketplace, public assembly). **Cross-platform from
M1**: built on cyrius `lib/net.cyr` socket primitives + `lib/io.cyr` / `lib/fs.cyr` storage
([ADR 0001](../adr/0001-cross-platform-listener-decoupled-from-agnos.md)).

---

## The road to 2.0

**1.x is "a BBS that works":** boards, keys, doors, chat and the Descent link, on a conformant wire, under two
serve models. **2.0 is the format break that makes "a BBS that survives any single node going away"
possible:** an identity is its key everywhere, and a post is addressed by the hash of its content. **2.x builds
the network on that:** node policy, topic federation, store-and-forward, self-distribution.

The order serves people on a single board first: the terminal, then the doors, then the bots. The additive
groundwork for 2.0 follows, and every breaking change waits for one cut. So each 1.x release ships on the v1
formats and upgrades in place.

| Arc | Slots | Theme | Delivers |
|---|---|---|---|
| **1.13.x** | 1.13.0 – 1.13.1 | The terminal and the protocol | paging by window height, the Handler's teletype, colour by terminal type; cross-board replies, opt-in ANSI-art posts |
| **1.14.x** | 1.14.0 – 1.14.3 | Door depth | QUEST async PvP, The Handler v2, Port Authority's endgame, shared worlds on a clock |
| **1.15.x** | 1.15.0 – 1.15.1 | Bots and media | ALICE, Racter, MegaHAL; inline images (kii), stored-file deltas (sankoch) |
| **1.16.x** | 1.16.0 – 1.16.2 | The road to 2.0 | content hashes and signed posts (additive), wide fingerprints, the migration tool and the 2.0 pre-flight |
| **2.0.0** | 2.0.0 | The format break | the key is the identity; posts are addressed by content |
| **2.1.x** | — | Node policy (pillar 3) | threat levels, an encrypted wire |
| **2.2.x** | — | Federation by interest (pillar 4) | topics, `Origin:`, inter-board doors |
| **2.3.x** | — | Offline-first (pillar 6) | the outbox, sync on connect, sneakernet |
| **2.4.x** | — | Self-distribution (pillar 5) | the network carries the system that runs it |

---

## 1.13.x — the terminal and the protocol

1.10.x made agora a conformant telnet server and fitted its output to the window's width. Nothing yet uses what
else it negotiates (the window height, the terminal type), and two protocol limits date from M5.

### 1.13.0 — the terminal, beyond the width

All three items park output across poll sweeps and take a key to continue, so they share one mechanism.

| Item | Source | Effort |
|---|---|---:|
| **Paging by window height** (NAWS rows): a `--More--` stop on a long `list` or `read`. It changes the input model in the middle of output (a key continues or quits), and under poll it means parking a command's output across sweeps. | [ADR 0030](../adr/0030-terminal-aware-output.md) § Consequences (rows unconsumed) | medium |
| **The Handler's 2400-baud teletype**: slow-printed cables with a spacebar skip. Deferred since 1.1.0 for want of output pacing and a mid-print key, which paging builds. | [ADR 0009](../adr/0009-door-games-subsystem.md) § Specifics ("instant render at 1.1.0") | small |
| **Colour by terminal type** (TERMINAL-TYPE, RFC 1091): no SGR for a terminal that names itself `DUMB` or `UNKNOWN`. The greeting carries most of agora's colour and goes out before the type can arrive, so the greeting waits until negotiation settles, as many BBSes do. | ADR 0030 § Consequences (TERMINAL-TYPE unconsumed) | medium |

### 1.13.1 — the protocol, beyond one board

| Item | Source | Effort |
|---|---|---:|
| **Cross-board replies**: `Reply-To:` reaches only the same board today. A reply names its parent's board, and the reply index ([ADR 0027](../adr/0027-reply-index.md)) records it where the parent lives. | [ADR 0005](../adr/0005-threading-via-reply-to.md) | medium |
| **Operator opt-in raw-mode posts** (ESC / ANSI art) on a board flagged for it, an explicit exception to egress sanitizing. | [ADR 0024](../adr/0024-egress-text-sanitization.md) § Consequences | medium |

---

## 1.14.x — door depth

The doors shipped complete for one player. The originals kept people coming back because of the other
players, and agora's versions do not have them yet.

### 1.14.0 — QUEST async PvP

| Item | Source | Effort |
|---|---|---:|
| **Attack another player's stored character** (persisted stats, not online), with a notice at their next login. This is the async-PvP shape Port Authority's garrisons already use ([ADR 0010](../adr/0010-persistent-universe.md) bite 3), on a `flock`'d shared character store, with daily attack limits so it is not grief-spam ([ADR 0032](../adr/0032-daily-ration.md)'s ration is the model). It is the largest missing piece of the LORD homage. | QUEST's design (`src/quest.cyr` header; `roadmap-future.md` § Door games until 1.12.1) | large |
| **The Inn**: the flirt-to-romance subplot and the bard, from the original spec. | same | medium |

### 1.14.1 — The Handler v2

| Item | Source | Effort |
|---|---|---:|
| **A global world-event track and persistent legacy ranks** across campaigns: the slow-burn crisis layer, and Probationary → Director's Chair posted on the board. | ADR 0009 § Decision ("the v2 community layer … per its own spec cut-line") | large |
| **The community layer**: intercepted rival traffic, inter-section sabotage, and the intercept pool and anonymous tips on the shared city alerts. | ADR 0009; ADR 0010 § Bites, item 4 ("intercept pool + anonymous-tip sabotage remain unpinned follow-ons") | large |

### 1.14.2 — Port Authority's endgame

| Item | Source | Effort |
|---|---|---:|
| **Planet citadels and mining tiers, alliances, and the full ship-upgrade tree** beyond holds / fighters / shields: TradeWars' long game. | ADR 0010 bites 2–3 (the galaxy, planets and garrisons it builds on) | large |
| **Smuggler's aggregate price pressure**: every player's trades move the shared district prices, as heat already does. | `src/smuggler.cyr` § Universe ("aggregate price pressure … is not built"); ADR 0010 item 4 | medium |

### 1.14.3 — shared worlds on a clock

| Item | Source | Effort |
|---|---|---:|
| **Ashes resolves its turns on time, not when the next visitor arrives**: today an idle world catches up only when someone enters. ADR 0014 kept a resolution daemon open and deferred it because agora had no long-lived process. The poll model is one, so a sweep timer can run the turn tick; fork mode keeps the lazy path. | [ADR 0014](../adr/0014-async-shared-world-strategy.md) § Alternatives; [ADR 0023](../adr/0023-dual-serve-model.md) | medium |
| **More than one Ashes laurel**: a second age ending before the first victor returns replaces the first laurel. A queue of unclaimed laurels needs a snapshot section of its own. | ADR 0014 § 1.12.0 amendment ("one laurel cell") | small |

---

## 1.15.x — bots and media

### 1.15.0 — three more chatbots

| Item | Source | Effort |
|---|---|---:|
| **A.L.I.C.E.** (Wallace, 1995): AIML pattern → template matching with operator-loadable rule files. It is the closest fit to the decomposition / reassembly engine, and the data-driven script dispatch `src/eliza.cyr` was waiting for lands here. | [ADR 0012](../adr/0012-chatbot-framework.md); [ADR 0011](../adr/0011-chat-area.md) (the script-format open question); `src/eliza.cyr` header | large |
| **Racter** (1984): template-driven generative prose with conjugation / agreement bookkeeping, a generator rather than a responder. | ADR 0012 § Context ("ALICE/Racter extend the fixed-script engine") | medium |
| **MegaHAL** (Hutchens): Markov-model replies trained on prior input, a second learning engine beside Jabberwacky's retrieval. It faces the training-source questions [ADR 0015](../adr/0015-jabberwacky-corpus-learning.md) settled (the live transcript, privacy, poisoning). | ADR 0012; ADR 0015 | medium |

### 1.15.1 — media in posts

| Item | Source | Effort |
|---|---|---:|
| **M3 — inline images in post bodies** via kii: sixel / ANSI block art where the terminal can take it, a link where it cannot. | the M3 milestone (its gates met since 1.0) | large |
| **M4 — stored-file deltas** via sankoch: a board's file area keeps revisions as compressed deltas. | the M4 milestone (its gates met since 1.0) | large |

---

## 1.16.x — the road to 2.0

This arc lands everything 2.0 needs that will not break a v1 store. New headers and fields are written beside
the old ones and read when present, so the format break itself is a conversion, not a redesign.

### 1.16.0 — content hashes and signed posts

| Item | Source | Effort |
|---|---|---:|
| **A canonical post serialization and a `Content-Hash:` header** on every new post: SHA-256 over the canonical form (blake3 if the stdlib gains it), verified on read and shown by `read`. The 0.9.0 ABI freeze was justified by headers like this one. | [ADR 0008](../adr/0008-post-headers-struct.md); § Pillar 2 below | medium |
| **Signed posts**: a client signs the canonical form with its key (`agora post --sign`, and a wire form), the node stores and checks the signature, and `read` shows it verified. Authorship stops depending on trust in the node. | § Pillar 1 below; [ADR 0006](../adr/0006-identity-model.md) | large |
| **Citation by hash**: `read <hash-prefix>`, and a reply that names its parent by hash, alongside the numeric id. | § Pillar 2 | small |

### 1.16.1 — wide fingerprints

| Item | Source | Effort |
|---|---|---:|
| **16 → 32 hex fingerprints, read both ways**: new registrations, `.admins` entries and `From:` headers carry 32 hex digits. Every lookup accepts either form, so a v1 store keeps working. | ADR 0006 (16 hex chosen for M6); [ADR 0026](../adr/0026-handle-index.md) | medium |

### 1.16.2 — the 2.0 pre-flight

| Item | Source | Effort |
|---|---|---:|
| **`agora migrate --to 2`**: converts a store (posts to content addresses with id aliases, identities to wide fingerprints), with a dry run and a report. It refuses a store it cannot convert whole. | § 2.0.0 below | large |
| **The P(-1) pass for a major**: an audit, external research, benchmarks against 1.x, and the migration guide. | CLAUDE.md § Process P(-1) ("at minor / v1.0 cuts") | large |

---

## 2.0.0 — the format break

After this one cut, an identity is a key and a post is its content. Both changes are breaking: stores, indexes
and saves change shape, and `agora migrate` (1.16.2) converts them.

| Item | Source | Effort |
|---|---|---:|
| **The key is the identity**: the wide fingerprint is canonical in posts, indexes, `.admins`, door saves and leaderboards, and a handle is a local display name. The per-node account becomes a cache keyed by fingerprint, so the same key is the same person on any agora node. | § Pillar 1 | large |
| **Posts are addressed by content**: `<board>/<hash>` is the post, and numeric ids remain as aliases for a deprecation window. The same post on twelve nodes is one artifact. | § Pillar 2; [ADR 0002](../adr/0002-one-file-per-post-storage.md) | large |
| **The Descent carries the identity**: the session's key reaches the MUD, so a citizen does not log in twice. This lands only if the MUD has gained an external-identity path by then (§ Blocked). | [ADR 0017](../adr/0017-descent-link-gateway.md) § Decision | large |

**2.0 is cut when** all of these hold:
- a 1.x store converts with `agora migrate` and nothing is lost: posts, replies, accounts, door saves, leaderboards;
- every post `read` shows a verified content hash;
- a signed post verifies on a second node that has never seen its author;
- both serve models and all three targets pass the Closeout Pass;
- the 2.0 migration guide is in the CHANGELOG's **Breaking** section.

---

## 2.x — the network

Six pillars came out of the 2026-05-23 design session. Pillars 1 and 2 are 2.0 itself; the other four are the
2.x arcs, in dependency order. Each can still pull forward early if its trigger fires.

| ↓ depends on → | P1 Identity | P2 Content | P3 Policy | P4 Topics | P5 Self-dist | P6 Offline |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| **P3 Policy** | ✓ | | | | | |
| **P4 Topics** | | ✓ | | | | |
| **P5 Self-dist** | ✓ | ✓ | | ✓ | | |
| **P6 Offline** | | ✓ | | ✓ | | |

### Pillar 1 — identity continuity across nodes (2.0.0)

Your Ed25519 keypair is your identity on every agora node, not a per-node account. Posts are signed client-side,
and nodes relay and store them. Moving between nodes keeps you the same person, and a node that disappears takes
its archive with it, not your identity.

- **Prior art**: Nostr (the key is the identity; relays are interchangeable), as against Mastodon's per-instance
  accounts. PGP had identity-as-keypair right in 1991 and failed at discovery.
- **Depends on**: sigil (≥ 3.4, present).
- **Pulls forward on**: an operator running several nodes who wants one identity across them, or a consumer
  (mela, agnoshi) scripting agora as the user.

### Pillar 2 — content-addressed storage (2.0.0)

A post is addressed by the hash of its canonical form, not by `(node, sequence)`. It can be mirrored anywhere
without breaking links, and citations check their own integrity. The signature (pillar 1) protects authorship;
the hash protects integrity.

- **Prior art**: IPFS (CID / IPLD), git, BitTorrent infohashes.
- **Depends on**: a hash in the stdlib (SHA-256 via sigil today; blake3 preferred).
- **Pulls forward on**: a consumer asking to cite a post that may move between nodes, or IPFS interop.

### 2.1.x — node policy (pillar 3)

| Item | Source | Effort |
|---|---|---:|
| **Threat-level node policy**: `[node] threat = "hobbyist" \| "journalist" \| "activist" \| "enterprise"` selects the inbound shape. One binary and one setting, overridable per field; `agora threat-level` prints the active policy. The levels are below this table. | Pillar 3 (SecureYeoman's vocabulary); phylax / kavach for sandboxing at the higher levels | large |
| **An encrypted wire**: telnet carries handles, fingerprints and post text in the clear (the signature flow protects only the key). TLS, or a transport the threat level selects. | ADR 0006 § Negative ("Telnet has no TLS at M6") | large |
| **Per-source admission at the edge**, where the platform can name the source (§ Blocked: agnos). | 0.7.0 audit M4; ADR 0023 | medium |

The threat levels:
- **hobbyist**: open inbound, sensible rate limits.
- **journalist**: an explicit handshake, federation only with known keys, optional Tor-only.
- **activist**: onion-only, the outbox, padded delivery against traffic analysis.
- **enterprise**: approved peers only, an inbound audit log to sakshi.

**Pulls forward on**: the first operator in a hostile network asking for the safer configuration, or
SecureYeoman formalizing its threat-level vocabulary.

### 2.2.x — federation by interest (pillar 4)

| Item | Source | Effort |
|---|---|---:|
| **Topics, not instances**: a topic is the hash of (name, charter, founder key). A node lists the topics it carries and syncs them with peers that carry them. Posts are tagged with topic ids, and an unknown topic is dropped (operators opt in). Boards map onto topics directly. | Pillar 4; [ADR 0004](../adr/0004-board-layout.md) § Neutral | large |
| **`Origin:`**: the post header naming the node a post entered the network at, forecast by the 0.9.0 ABI freeze (a setter and one offset). | ADR 0008 § Consequences | small |
| **Inter-board doors**: QUEST characters competing across boards (LORD's IGM / IBBS), and Universe worlds shared between nodes. | QUEST's design (`roadmap-future.md` § Door games until 1.12.1) | large |

- **Prior art**: FidoNet echomail; Usenet, which failed on identity and spam (the gaps pillars 1 and 3 fill);
  Matrix rooms.
- **Depends on**: pillar 2; sandhi for the advertisement transport.
- **Pulls forward on**: the first request to federate boards between two nodes.

### 2.3.x — offline-first (pillar 6)

| Item | Source | Effort |
|---|---|---:|
| **The outbox**: every cross-node operation goes through a durable queue first and is retried with backoff (patra). | Pillar 6 | large |
| **Sync on connect**: peers exchange topic state roots (hash-chain heads) and pull the deltas, resumably (sankoch for the payloads). | Pillar 6 | large |
| **Sneakernet**: `agora export <topic>` / `agora import` round-trip a topic through removable media, for air-gapped networks and one-way diodes. | Pillar 6 | medium |

- **Prior art**: FidoNet, UUCP, Briar.
- **Pulls forward on**: an operator on a rural, sanctioned or censored network, or an AGNOS deployment without
  reliable connectivity.

### 2.4.x — self-distribution (pillar 5)

| Item | Source | Effort |
|---|---|---:|
| **`agora download <package>`**: every node carries the AGNOS installer, SecureYeoman and the marketplace packages, content-addressed and signed, distributed as a topic every node carries. Blocking the distribution would mean blocking every node. | Pillar 5 | large |

- **Depends on**: pillars 1, 2 and 4; the AGNOS and SecureYeoman release pipelines.
- **Pulls forward on**: a downstream that must ship AGNOS to a network with no path to github.com.

---

## Blocked — waiting on someone else

| Item | Waiting on | Joins |
|---|---|---|
| **Sigil identity hand-off across the Descent link**: carry the session's identity into the MUD. Open questions from [ADR 0017](../adr/0017-descent-link-gateway.md) § Decision: token format, trust model, co-located vs remote. | Yeoman's Descent has no external-identity path (name + passphrase only) | 2.0.0 |
| **macOS / Windows ports**, and `$HOME` keyfile resolution (`/proc/self/environ` today) | `lib/net.cyr` backends upstream (re-check what remains) | the next 1.x slot once unblocked |
| **Tell a slow reader from a stalled one by delivered bytes** (fork mode): today a write with no send-buffer room for 60 s drops the client; the exact test is "did the client acknowledge anything in 60 s". | a `lib/net.cyr` primitive for unacknowledged bytes (`SIOCOUTQ` / `TCP_INFO`); found at 1.8.2 | the next 1.x slot once unblocked |
| **Accept-loop rate limiting** per source (0.7.0 audit M4's untaken half). agnos, the target that always polls, has neither `getpeername` nor a peer address from `sock_accept`, so this would protect Linux only, and it misfires behind NAT. `MAX_SESS` and the network edge remain the operator's tools. | agnos `getpeername` and a stdlib `sock_accept_from`; ADR 0023 | 2.1.x |
| **Close the directory guard's `stat`-then-`open` window** in `store_dir_scan` | the stdlib's `dir_list_into` opening with `O_DIRECTORY` (cyrius issue 2026-10-13, filed at 1.9.1) | the next toolchain cut |
| **Binary strip / DCE-aware emit**: `CYRIUS_DCE=1` NOP-fills dead code but keeps its bytes and all `.bss` (the ~375 KB static-data warning) | the toolchain | the next toolchain cut |

---

## Deliberately not doing

Recorded so nobody re-opens them by accident:

- **Per-source session caps on agnos or behind NAT**: agnos has no `getpeername`, and on a NAT'd LAN every
  client shares one address. Declined at 1.6.4; `MAX_SESS` remains the operator's bound (2.1.x revisits it only
  where the platform can name the source).
- **Absolute session lifetime caps**: they would disconnect legitimate long sessions (a QUEST run, an idle
  chat). Declined at 1.6.4.
- **Rate-limiting option re-negotiation**: toggling WILL / WONT TERMINAL-TYPE or LINEMODE yields ~2× output,
  but it returns to the client's own socket over TCP (no reflection), and the 128 KB tx queue bounds it.
  Accepted at 1.8.1 (audit I1).
- **Adopting darshana's `tty_open_signalfd`** for clean shutdown: its AGNOS arm blocks the signals, and under
  mirshi a blocked signal is never delivered through a signalfd. Re-checked and declined at 1.8.0.
- **Rationing Practice door runs**: a Practice run ends with its session, so a ration would only make it
  impossible to finish. Decided at 1.12.0 ([ADR 0032](../adr/0032-daily-ration.md)).

---

## Cross-references

- [`state.md`](state.md) — where agora stands: version, sizes, test counts, the next-session boot guide.
- [`CHANGELOG.md`](../../CHANGELOG.md) — everything that has shipped, per tag.
- [`docs/adr/`](../adr/) — the architecture decisions (0001–0033); [`docs/audit/`](../audit/) — the audit
  ledger; [`docs/architecture/`](../architecture/) — non-obvious constraints.
- [SecureYeoman](https://github.com/MacCracken/secureyeoman) (pillar 3's vocabulary) ·
  [sigil](https://github.com/MacCracken/sigil) (pillar 1) · [sandhi](https://github.com/MacCracken/sandhi)
  (pillar 4's transport) · [patra](https://github.com/MacCracken/patra) (pillar 6's outbox).
- **Companion project**: [Yeoman's Descent](https://github.com/MacCracken/cyrius-yeomans-descent) — the MUD
  userland, linked by the 1.4.0 gateway.
