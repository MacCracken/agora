# agora — Post-v1.0 Roadmap (v2.x sovereignty layer)

> **Last Updated**: 2026-05-23
>
> Unpinned design directions for the v2.x sovereignty layer — the federated, identity-portable, store-and-forward shape that agora grows into after v1.0 (multi-user telnet BBS) ships. Items here are **not on the v1.0 critical path**; they pull forward into a numbered minor when consumer pressure, prior-art convergence, or user direction surfaces. v1.0 milestones live in [`roadmap.md`](roadmap.md).
>
> **Frame**: v1.0 is "a BBS that works." v2.x is "a BBS that survives any single node going away." The pillars below are the six shifts that get us there, consolidated from a 2026-05-23 design session.

---

## Door games — Persistent Universe pulled into 1.2.0

The door subsystem's **shared-world multiplayer + leaderboards have graduated from "unpinned future" to the active 1.2.0 cycle** — see [`roadmap.md`](roadmap.md) § In progress and [ADR 0010](../adr/0010-persistent-universe.md). 1.2.0 covers the `flock`'d world-transaction framework, Port Authority's shared galaxy (depletable ports, player planets, deployed fighters/mines, async PvP, alliances), Smuggler's shared economy (prices + heat move with all players), The Handler's shared layer (per-city alerts, intercept pool, anonymous-tip sabotage), and leaderboards for all three games.

Still unpinned **beyond** 1.2.0:

- **The Handler — global world-event track + persistent legacy ranks** across campaigns (the slow-burn crisis layer + Probationary → Director's-Chair progression posted on the board).
- **Port Authority — deep endgame**: planet citadels + mining tiers, the full ship-upgrade tree beyond holds / fighters / shields.
- **The Handler — 2400-baud teletype effect** (slow-print cables + spacebar-skip), deferred since 1.1.0; needs a raw-mode input path (the server is char-at-a-time + line-mode today).

### QUEST — "Quest of the Undying Emerald Sovereign Throne" (a LORD homage)

> **✅ Single-player climb SHIPPED at 1.3.2** (`src/quest.cyr`, `play quest`): town hub + daily-rationed forest + the twelve Great-Work masters + the Emerald-fragment spine + the Sovereign ascension; solo save + `scores quest`. The design below stands as the full spec; **what remains unpinned is the async-PvP / shared-world Universe layer** (attack stored characters with next-login notice, on the 1.2.0 world transaction + PA garrison model) and the deeper-endgame flourishes.

A fourth door game: an homage to **Legend of the Red Dragon** (Seth Robinson, 1989) — the definitive BBS RPG. Re-themed name + cast per the style-not-copy rule (like Smuggler's abstract goods + Port Authority's re-themed commodities): **"Quest of the Undying Emerald Sovereign Throne" — `play quest`**. A strong fit, because the mechanics that made LORD *LORD* are the patterns agora's door subsystem already implements — QUEST is mostly assembly of existing machinery plus the one thing that can't be reused: voice.

**What actually makes LORD LORD (the design lessons worth stealing):**

- **Daily turn rationing is the load-bearing mechanic, not a detail.** N forest fights/day, a handful of PvP attacks, one-visit events. The rationing is *what makes a single-user-at-a-time game feel like a shared world* — nobody grinds infinitely, the world stays balanced between callers, and "see you tomorrow" is built into the loop. agora already has this exact rhythm: the wall-clock daily-turn cadence ([ADR 0010](../adr/0010-persistent-universe.md) § Decision, the LORD rhythm the games already borrow) via `chrono` rollover. QUEST leans on it directly.
- **The forest is the core grind:** random encounters scaling to level, gated by **12 named level-masters** (beat the master to advance). Linear, readable progression — a clean fit for the pure-module state machine (`*_render` / `*_feed`, ADR 0009).
- **The town hub is a menu of flavor activities, and the flavor IS the product.** Re-themed equivalents of: the Inn + the **flirt-to-romance subplot** (LORD's Violet — the "you have been kissed" / marriage arc), the bard, the Healer, the **Bank with interest** (and the infamous mugger risk if you walk around carrying cash), the tavern, and the **Slay-the-Sovereign endgame**. The town is where personality lives; combat is just the engine.
- **Async PvP that agora already ships.** You attack another player's *stored* character (persisted stats, not online); they get a notification next login. This is precisely the async-PvP model already built for Port Authority's garrisons ([ADR 0010](../adr/0010-persistent-universe.md) bite 3 — act against the assets/state a player left behind, resolved from the world snapshot, never a live duel) plus the next-login notice. Daily attack limits keep it from being grief-spam. The shared character store is a 1.2.0-style `flock`'d world transaction.
- **Tone is load-bearing — this is the real risk.** LORD's stickiness was its voice: gently comedic, self-aware, a little bawdy. A mechanically faithful clone written in dry corporate-memo prose falls flat — the writing voice is the product. The Handler already proves agora can carry a deliberate tone (its espionage desk-job register), so the transferable skill exists; QUEST must spend its budget on the prose, not just the combat math.
- **Inter-board LORD (IGM / IBBS over FidoNet-style mail)** — the deep cut: LORD characters competing *across* boards. Out of scope for a first homage, but noted because it is the asynchronous-multiplayer model taken to its logical extreme — and it rhymes with the v2.x **federation** pillar (below) and a future agora-to-agora link.

**The twelve-level arc — full skeleton (the buried reference; nothing is ever labelled).** Design principle throughout: a first-time caller reads a satisfying, slightly-grandiose fantasy climb; a hermetically-literate one reads the **Great Work** unfolding. The second reading lives entirely in structure, colour, and naming — never authorial commentary. The four stages give a colour arc — **nigredo** (blackening: death/dissolution), **albedo** (whitening: purification), **citrinitas** (yellowing: dawning illumination), **rubedo** (reddening: completion/union) — and twelve levels split cleanly into **four acts of three**, each phase getting a beginning, middle, and turn. Masters escalate in the obvious RPG sense; their names, palettes, and what they take from you track the inner process. The four **turning-point masters (levels 3 · 6 · 9 · 12)** each drop one **Emerald fragment** matching its phase's colour.

*Act I — Nigredo (1–3), the Blackening* — prima materia broken down; the world starts in mud, rot, night.
- **L1 · The Mudlark Warden** — swamp brigand in rusted iron; black / bog-brown. The tutorial; teaches you start as raw material. Drops a blank, tarnished disk (the player assumes junk — it is the unmarked tablet awaiting inscription).
- **L2 · Sister of the Black Bile** — plague-hermit fighting with rot + despair (weaken / doubt status effects); black-green / ash. Putrefaction, the necessary decay — beating her is *surviving dissolution*, not conquest.
- **L3 · The Drowned King (turn)** — waterlogged crowned corpse from a flooded barrow, a dark mirror of the Throne; black water / drowned gold. The false king, the ego that must die — closes Nigredo. **Fragment 1**: nearly black, no markings yet.

*Act II — Albedo (4–6), the Whitening* — matter cleansed; palette lifts to silver / white / lunar-pale; the feminine principle.
- **L4 · The Pale Laundress** — fights at a moonlit river washing what never comes clean; silver / white / moon-blue. Ablution — the washing of the blackened matter. Gentle-seeming, deceptively dangerous.
- **L5 · The Argent Twins** — mirror-identical duelists fought as a pair (strike one, the other answers); quicksilver / white. Sol and Luna *unreconciled*, the opposites not yet joined; teaches balance + timing. (Quietly: mercury, the twin / hermaphrodite principle.)
- **L6 · The White Queen (turn)** — serene woman in white fighting with light and clarity, not rage; pure white / pearl. The purified feminine, albedo perfected. **Fragment 2**: pale, washed clean — faint markings begin to surface; the fragments start to look like they belong together.

*Act III — Citrinitas (7–9), the Yellowing* — the historically "forgotten" stage; gold / dawn-light; the solar / illuminated principle awakening.
- **L7 · The Gilded Augur** — blind, gold-leafed prophet who "sees" by other means, fighting with foresight (dodges / predicts your moves); gold / amber. Insight arriving before understanding.
- **L8 · The Brass Alchemist** — the most on-the-nose master, disguised as a tinkerer / inventor boss (gears, reagents, bubbling apparatus) so it reads as steampunk flavour, not confession; brass / sulfur-yellow. Fights by *transmuting the battlefield* (altering your stats, swapping effects). The wink hidden in plain sight — the literal alchemist who never says the word.
- **L9 · The Sunwise Lord (turn)** — radiant solar warrior-king, the dawn made flesh; blazing gold / sunrise orange. Citrinitas perfected. **Fragment 3**: gold-green — the markings across all three collected pieces begin to align; held together they almost spell something.

*Act IV — Rubedo (10–12), the Reddening* — union of opposites, the sacred marriage, the making of the Stone; crimson / royal purple / fire-gold.
- **L10 · The Crimson Bride / the Red Groom** — a wedding turned battle, two figures (red + white) in the act of being joined; deep red and white intertwining. The chymical wedding — Sol and Luna finally united (callback to the unreconciled Argent Twins of L5). Mechanically the two enemies **fuse mid-fight** into one stronger form.
- **L11 · The Keeper of the Last Fire** — guardian of the threshold to the Throne, a being of pure refining flame; white-hot / crimson core. The final calcination / projection that fixes the Stone. The hardest gate-fight — it guards *transformation itself*, not treasure.
- **L12 · The Undying Emerald Sovereign (turn)** — the title made flesh: not a monster but the perfected King upon the Throne, the goal of the whole Work, who must be faced to take his place; emerald and royal gold, crowned in red. He is what the player is becoming — the fight is *succession*, not slaughter. **Fragment 4**: with all four, the tablet completes.

*The Emerald spine + endgame.* Four fragments, one per turning-point master (L3 / 6 / 9 / 12), each matching its phase's colour — **black → white → gold → emerald**. The player experiences a standard collect-the-MacGuffin spine, but the fragments **visibly change as they accumulate**: blank-and-dark, then surfacing markings, then aligning, then completing. With all four joined the tablet is whole and legible — and at that moment the player **ascends to the Undying Emerald Sovereign Throne** they have quested for. The **"as above, so below"** line appears **once, here**, inscribed on the completed tablet — the single moment the buried text is allowed to surface, presented as the artifact's own ancient inscription rather than authorial commentary. A caller who has never heard of the Emerald Tablet reads it as cool victory-screen flavour; a caller who has just realised the entire climb *was* the Work goes back to replay it reading everything twice.

**Fit summary:** pure-module state machine (ADR 0009) ✓ already the house pattern; daily-turn cadence ✓ already in the games; shared character store + async PvP ✓ the 1.2.0 world transaction + PA garrison model; leaderboards ✓ the `scores` surface. The genuinely new work is the **town/flavor content + the comedic voice** — i.e. writing, which is the point. **Pinned to 1.3.2** (the QUEST build-out; see [`roadmap.md`](roadmap.md) release table).

---

## Chatbot personalities — beyond Eliza / PARRY

The 1.3.0 chat area ([ADR 0011](../adr/0011-chat-area.md)) ships **Eliza** (Weizenbaum, 1966) as its anchor inhabitant, and 1.3.1 adds **PARRY** (Colby, 1972) on the same reusable pure decomposition/reassembly engine — both reachable as a `play <bot>` door and a private `/<bot>` side-channel. The historical lineage of conversational agents is a rich, on-theme well of further inhabitants. Unpinned, pull on interest:

- **A.L.I.C.E. / ALICEbot** (Richard Wallace, 1995) — AIML pattern/template matching. The closest fit to the existing decomposition/reassembly engine (AIML *is* a richer pattern→template grammar); the open question is how much AIML to support without a full parser + an external rule-file format (operator-loadable scripts, foreshadowed in ADR 0011's "Eliza script format" open question).
- **Racter** (1984) — template-driven generative prose with conjugation/agreement bookkeeping. Less a responder than a generator; would stress the engine toward grammar state rather than input reflection.
- **MegaHAL** (Jason Hutchens, 1990s) — **Markov-model** reply generation trained on prior input. A *different engine* from decomposition/reassembly (n-gram model + learned state), so it would land as a second bot-engine kind, not a script swap — and raises a learning/state-persistence question (does it train on the live chat transcript? privacy + poisoning concerns).
- **Jabberwacky** (Rollo Carpenter, 1988→) — **learning by retrieval** from a growing corpus of past conversations. Like MegaHAL, a corpus-learning engine rather than a fixed script; the most ambitious (and the one with the heaviest persistent-state + moderation story). **Pinned to 1.3.3** (see [`roadmap.md`](roadmap.md) release table) — it brings agora's first learning / persistent-state bot, so it is the deliberate engine step beyond the Eliza/PARRY fixed-script core.

The first two (ALICE, Racter) extend the existing pure-script engine; the latter two (MegaHAL, Jabberwacky) need a learning/corpus engine and so are a larger, separate build. None add external dependencies in principle — all are implementable as pure Cyrius modules — but the learning bots add a persistent-state surface the fixed-script bots do not.

---

## Pillars

Six themes, each with prior-art convergence and concrete pull-forward triggers. Order is rough dependency / value-density, not strict ranking.

### Pillar 1 — Identity continuity across nodes (sigil-portable Ed25519)

Your Ed25519 keypair is your identity on every agora node, **not** a per-node account. Sign your posts client-side; nodes relay and store. Move between nodes and you're the same person. When a node disappears, you lose its archive, not your identity.

**Prior art**:

- **Nostr** gets this right: NIP-01 signs every event with the user's secp256k1 key; relays are interchangeable; identity is the key.
- **Mastodon** gets this wrong: per-instance accounts → friction on instance death or migration; ActivityPub federation can't fully heal the discontinuity.
- **PGP web of trust** got identity-as-keypair right in 1991; the WoT discovery layer is what failed.

**Proposed shape**:

- The v1.0 M6 `whoami` verb returns a sigil-backed handle bound to *this* node's account table. v2.x replaces the bound handle with the raw Ed25519 fingerprint as the canonical identity. The per-node "account" becomes a thin local-state cache (display name, post history, last-seen) keyed by fingerprint.
- Login is a sigil challenge: `agora login` proves possession of the key, no shared secret stored on the node.
- Cross-node `whoami` returns the same fingerprint everywhere; per-node profile pages are views into the global identity.

**Dependencies**:

- **sigil** ≥ 3.4 (✅ available at 3.4.2) — identity primitives + Ed25519 key handling.
- v1.0 M6 (sigil-backed accounts) — the foundation this builds on; pillar 1 is the natural M6 → v2 graduation.

**Pull-forward triggers**:

- First request from a v1.x operator running multiple agora nodes who wants shared identity across them.
- A consumer (mela, agnoshi) wanting to script against agora as the user without bouncing through per-node tokens.
- Any sigil API expansion that makes portable-key handling cheaper than per-node-bound handles.

---

### Pillar 2 — Content-addressed storage (hash-keyed posts)

Posts are content-addressed by hash, not by `(node, sequence number)`. Mirror anywhere without breaking links. Citations become integrity-checkable. The same post on twelve nodes has the same address; the network treats it as one artifact, not twelve.

**Prior art**:

- **IPFS** built the substrate (CID, IPLD, libp2p) — useful both as interop and as a reference design.
- **Git** showed the model works at code-history scale: SHA hashes for every object, no central naming authority needed.
- **BitTorrent infohashes** showed it works at media scale: hash = identity = discovery key.

**Proposed shape**:

- Canonical post serialization (header field ordering + body bytes) produces a deterministic input; post ID = `blake3(canonical(post))` (or `sha-256` if interop pressure wins).
- v1.0 M5 (post persistence) stores posts under a `<board>/<id>` path. v2.x changes the `<id>` to the content hash; old `<board>/<seq>` paths become alias symlinks for a deprecation window.
- Cross-board citation by hash. "Reply to `7af3…`" is unambiguous and verifies on read.
- Mirror operation: any node can pull post `<hash>` from any node that has it; signature on the post (from pillar 1) is checked separately from the hash (which protects integrity, not authorship).

**Dependencies**:

- v1.0 M5 (post persistence) — content-hashing is layered onto persistence, so M5's layout decision (ADR pending) should leave room.
- A hashing primitive from cyrius stdlib — `lib/sha1.cyr` ✅ available; **blake3** would be preferred (faster) but isn't in stdlib yet. Pull-forward likely lands behind a stdlib slot for blake3.
- Optional: native IPFS bridge via sandhi (HTTP/2) — only if interop becomes an operator ask.

**Pull-forward triggers**:

- Any consumer asking "can I cite a post that might move between nodes?" — that's pillar 2's whole job.
- IPFS interop request from a downstream that already speaks CID/IPLD.
- A `lib/blake3.cyr` landing in cyrius stdlib — removes the last dependency blocker.

---

### Pillar 3 — Threat-level node policy (SecureYeoman vocabulary)

Same threat-level configuration vocabulary used in [SecureYeoman](https://github.com/MacCracken/secureyeoman), applied to *network exposure*. The agora binary is one binary; the operator's threat level selects which inbound shape it accepts.

- **`threat: hobbyist`** — open inbound, anyone with a telnet client can connect, sensible-default rate-limit only.
- **`threat: journalist`** — explicit handshake required, federation only with known-peer pubkeys (pillar 1 fingerprints), optional Tor-only mode.
- **`threat: activist`** — journalist + onion-only listener + outbound queue (pillar 6) + per-message random-pad delivery to defeat traffic analysis.
- **`threat: enterprise`** — integrates with the organization's network policy and only accepts federation from approved nodes; auditable inbound log piped to sakshi.

Same binary. Different `agora.cyml` config. One operator decision, no recompile.

**Prior art**:

- **SecureYeoman** owns this vocabulary — the threat-level configuration shape is the reference. Pulling the same words into agora keeps the AGNOS ecosystem's operator vocabulary coherent.
- **OpenSSH config tiers** (default vs. hardened) showed it works at the sysadmin level.
- **Tor's variable-difficulty PoW** (2023+) showed threat-level can be runtime-switched without restart.

**Proposed shape**:

- `cyrius.cyml` (or sibling `agora.cyml`) gains a `[node] threat = "hobbyist"` field. agora reads it at startup and selects the appropriate listener / federation / outbound shape.
- Each level is a named config preset — operator can override individual settings if they want a hybrid (e.g. journalist-level inbound + hobbyist-level outbound).
- A single `agora threat-level` verb prints the active level and the implied policy summary, for confidence-checking.

**Dependencies**:

- **secureyeoman** as the upstream that owns the vocabulary — track its threat-level definitions and stay in sync.
- **phylax** / **kavach** — kernel-side primitives for the harder levels (sandbox the listener at activist+, capability-drop at enterprise).
- **sigil** (pillar 1) — the known-peer pubkey list at journalist+ is sigil identities.

**Pull-forward triggers**:

- First operator who wants to run agora in a hostile network (rural, censored, sanctioned) and asks "what's the safer config?"
- SecureYeoman's threat-level vocabulary formalizes — at that point we mirror it.

---

### Pillar 4 — Federation by interest, not by platform (topic-shaped)

BBSes had themed boards. FidoNet had echomail areas. Modern federation lost this — Mastodon/ActivityPub federate *instances*, not *topics*. The shift: you join agora **topics**, not agora **instances**. Your node carries the topics you care about and federates with other nodes that carry those topics. Discovery is topic-driven; instances are a deployment detail.

**Prior art**:

- **FidoNet echomail** (1984–): nodes carried specific echos; messages tagged by area; gateways relayed by tag. Discovery was "which echo carries this?" not "which BBS hosts this?"
- **Usenet newsgroups** (NetNews / NNTP, 1979–): the canonical topic-federation design at internet scale; broke down on identity (anyone could post as anyone) and spam, both of which pillar 1 + pillar 3 address.
- **Matrix rooms** (2014–) come close in shape: rooms federate across homeservers; the room is the unit, not the server. Matrix shows the design works at modern scale.
- **Lobste.rs / Hacker News** show that topic-curated communities outlast platform-curated ones at the social layer.

**Proposed shape**:

- A topic is a hash (content-addressed, pillar 2) of `(topic-name, founding-charter, founder-pubkey)`. Topic IDs are global; topic names are local hints, not authoritative.
- Each node has a `~/.agora/topics.cyml` listing the topics it carries. Subscribing pulls the topic's post history from any node that carries it; unsubscribing tears down local state.
- Posts are tagged with one or more topic IDs at write time. A node receiving a post for an unknown topic drops it (default-deny — operator opts into topics, not the reverse).
- Discovery: an agora node advertises its topic list over the federation protocol (or via an out-of-band topic-registry node — see pillar 5). New users find topics by gossip, not by "which server has this?"

**Dependencies**:

- Pillar 2 (content-addressed posts) — topic IDs are content hashes too, same primitive.
- Pillar 6 (store-and-forward) — topic subscriptions naturally tolerate intermittent connectivity.
- **sandhi** — HTTP/2 + service discovery for the topic-advertisement protocol if we don't roll a custom transport.

**Pull-forward triggers**:

- First request for cross-node board federation in v1.x — that's pillar 4 by the back door.
- Any consumer asking how to discover content across multiple agora nodes.
- A v1.x user spinning up a second node and wanting one to mirror specific boards (not all) from the first.

---

### Pillar 5 — Self-distribution baked into the protocol

Every agora node carries the AGNOS installer, the SecureYeoman installer, and the AGNOS marketplace packages. Visiting any agora node lets you download the system that runs agora. The network *is* the distribution channel.

**Prior art**:

- **BitTorrent** showed self-distribution works at scale: every peer is a server; the network has no central host.
- **APT mirrors / Debian** showed it works for OS distribution at country scale; the mirror network is the distribution.
- **IPFS pinning** showed content-addressed distribution scales without a central authority.
- **Inverse**: HTTPS + CDN-based distribution makes the central host the single point of failure / control. Cloudflare blocking Sci-Hub demonstrated the failure mode. agora's design philosophy rejects it.

**Proposed shape**:

- A new `agora download <package>` verb. `agora download agnos` returns a copy of the latest AGNOS bootable installer; `agora download secureyeoman` returns the SecureYeoman binary; `agora download marketplace:<pkg>` returns a marketplace package.
- Packages are content-addressed (pillar 2) and signed (pillar 1) at release time. Operators can verify what they got by hash before installing.
- Topic-shaped distribution: `agora-distribution-snapshot` is one of the topics every node carries by default. Pulling the topic pulls the current installer set.
- Cool side-effect: blocking distribution means blocking every agora node simultaneously. Block-resistance compounds with deployment count.

**Dependencies**:

- Pillar 2 (content-addressed) — package identity.
- Pillar 1 (sigil-portable identity) — signing keys.
- Pillar 4 (topic-shaped federation) — the `agora-distribution-snapshot` topic is just another topic.
- AGNOS release pipeline emitting bootable installers; SecureYeoman release pipeline emitting standalone binaries; AGNOS marketplace having a package index.

**Pull-forward triggers**:

- First time a downstream wants to ship AGNOS to a network with no internet path to github.com.
- Any AGNOS marketplace operator asking "what's the resilient way to mirror this?"
- A v1.x operator on a rural / sanctioned / censored network ([[pillar-6-offline-tolerant]]) — distribution is meaningless if the channel is gated.

---

### Pillar 6 — Offline-tolerant, store-and-forward as first-class

Modern federation protocols assume always-on connectivity. BBSes assumed intermittent connectivity — dial in, sync, hang up. Real-world sovereignty often means working in environments without reliable connectivity. Store-and-forward as a first-class operation mode — not an afterthought — lets agora work where ActivityPub silently fails.

**Prior art**:

- **FidoNet** (1984–): store-and-forward by design; nodes sync once a day or once a week; reached every country on Earth, including USSR, Cuba, and North Korea at points the open internet hadn't.
- **UUCP** (1976–): same shape, predecessor; the original "intermittent connectivity is normal" design.
- **Briar messenger** (2014–): modern reincarnation; mesh + store-and-forward + no central server; works without internet via Bluetooth / Wi-Fi-direct.
- **Inverse**: ActivityPub assumes HTTP-now and quietly drops federation when the peer is offline.

**Proposed shape**:

- Outbound queue: every cross-node operation (federated post, distribution package fetch, topic subscription) goes through a durable outbox first. Network failures retry with backoff; success drains the entry.
- Sync-on-connect: on inbound or outbound link establishment, exchange topic-state-roots (hash-chain heads per pillar 2) and pull deltas.
- **Sneakernet-friendly**: `agora export <topic> > stick.cyml` and `agora import stick.cyml` round-trip the full state of a topic via removable media. Useful for air-gapped networks, deliberate one-way diodes, and crossing administrative boundaries.
- Federation handshakes assume the peer might disappear mid-sync — every state-pull is resumable.

**Dependencies**:

- Pillar 2 (content-addressed) — hash-chain heads are the sync primitive.
- Pillar 4 (topic-shaped) — the unit of sync is a topic, not a node.
- **patra** (cyrius stdlib storage) — the durable outbox.
- **sankoch** (cyrius stdlib compression) — delta payloads compress well.

**Pull-forward triggers**:

- First operator running agora on a rural / sanctioned / censored network — pillar 6 makes them functional, lack of it makes them silent.
- Any AGNOS deployment on a vehicle, ship, or remote installation that can't assume reliable connectivity.
- A request for air-gapped board mirroring (one-way diode from an internal network to a public one).

---

## How pillars interact

| ↓ depends on → | P1 Identity | P2 Content-addr | P3 Threat-level | P4 Topics | P5 Self-dist | P6 Offline |
|---|---|---|---|---|---|---|
| **P1 Identity**         | —    | —    | —    | —    | —    | —    |
| **P2 Content-addr**     | —    | —    | —    | —    | —    | —    |
| **P3 Threat-level**     | ✅   | —    | —    | —    | —    | —    |
| **P4 Topics**           | —    | ✅   | —    | —    | —    | —    |
| **P5 Self-dist**        | ✅   | ✅   | —    | ✅   | —    | —    |
| **P6 Offline**          | —    | ✅   | —    | ✅   | —    | —    |

Reading: row "what depends on" column. Pillars 1 and 2 are the foundation; everything else layers on. Pillar 5 (self-distribution) has the most dependencies — it pulls forward last unless an external operator-driven reason surfaces.

---

## What this file is NOT

- Not a v1.0 deliverable list — see [`roadmap.md`](roadmap.md).
- Not a binding commitment — pillars may collapse, split, or get retired as the v1.x cycle reveals what's actually needed.
- Not a TODO list — items are *unpinned*; nothing is scheduled until a pull-forward trigger surfaces.

---

## Cross-references

- [`roadmap.md`](roadmap.md) — v1.0 critical path (M0–M6).
- [`../doc-health.md`](../doc-health.md) — fresh/stale ledger across the doc tree.
- [SecureYeoman](https://github.com/MacCracken/secureyeoman) — owns the threat-level configuration vocabulary that pillar 3 mirrors.
- [sigil](https://github.com/MacCracken/sigil) — identity primitives behind pillar 1.
- [sandhi](https://github.com/MacCracken/sandhi) — HTTP/2 + service-discovery transport candidate for pillar 4.
- [patra](https://github.com/MacCracken/patra) — durable storage behind pillar 6's outbox.

---

*Initial scaffold: 2026-05-23 (M1 fourth-bite closeout — pillars consolidated from a design session covering the post-v1 sovereignty layer). Refresh in place when a pillar pulls forward into a numbered roadmap minor or when a new pillar earns its slot.*
