# 0017 — Descent link: a transparent-proxy gateway to the MUD

> **Status**: Accepted
> **Date**: 2026-06-10

## Context

agora (the BBS) and **Yeoman's Descent** (`../cyrius-yeomans-descent`, a Cyrius-native techno-feudal MUD with its own raw-TCP/telnet server) are the two halves of the AGNOS public-assembly surface: the same telnet substrate, different application semantics (async boards/games vs. a real-time room/object world). The 1.4.0 roadmap item makes the BBS the **front door to the MUD** — a logged-in agora citizen steps through a portal into the Descent without dialing a second address. The 1.3.7 war-game (Ashes of Empire, [ADR 0014](0014-async-shared-world-strategy.md)) was deliberately sequenced just before this to retire the shared-state-between-callers concurrency risk first.

Two forces shape the decision:

1. **The MUD owns its own world.** It runs a single-threaded event loop, its own RFC 1143 negotiation, its own combat tick, and its own Ed25519-from-passphrase login (its ADR 0004). agora must not re-implement or absorb any of that — the two projects keep independent release cycles.
2. **The MUD has no external-identity path.** Every connection types a name + passphrase; there is no pre-authenticated-session concept, no handoff token, no trusted-source bypass. Carrying agora's sigil identity across the link the way the roadmap envisions would require *MUD-side* protocol work, not just agora work.

agora's session model is line-buffered and turn-based (`MODE_DOOR` feeds a completed line to a pure game module and repaints a frame). A live MUD instead pushes output asynchronously (room events, combat ticks) — it does not fit the line-feed-then-render shape.

## Decision

**1.4.0 ships the gateway as a transparent TCP byte-proxy, and explicitly DEFERS sigil identity hand-off to a follow-on bite that needs an MUD-side protocol.**

In scope (agora-only, this release):

- A `descent` verb (login-gated, like `chat`). It reads an **operator-set** endpoint from `<store>/.descent` (`host:port`, or a bare port → `127.0.0.1` for a co-located MUD), dials it with a bounded non-blocking connect (`net_connect_nb`), and shuttles bytes both ways via a `poll(2)`-multiplexed loop until either side closes (or a 30-minute pure-silence bound trips). Absent/empty config → "No Descent linked."; unreachable endpoint → a soft message; both leave the citizen at the BBS prompt.
- The shuttle is **byte-transparent**: the MUD's own telnet negotiation (WILL ECHO / SGA, passphrase echo suppression) and all world output flow to the client verbatim. The MUD authenticates the player itself.
- The endpoint is **operator config only**, never client-supplied — so there is no SSRF surface (a citizen cannot point the proxy at an arbitrary host).

Out of scope (deferred):

- **Sigil identity hand-off.** The MUD cannot accept an external identity today; a real hand-off (signed token vs. trusted local socket) is a two-repo change with its own ADR (and likely a shared-protocol note in the genesis repo). Until then the citizen re-authenticates inside the MUD; agora prints a one-line courtesy note saying so.
- A resolution/launch-a-client model, remote-vs-co-located policy, and graceful-teardown niceties beyond close-on-either-side.

## Consequences

- **Positive** — the BBS becomes the front door to the MUD with zero coupling beyond the wire: agora carries no MUD semantics, the MUD needs no agora awareness, and both keep independent release cycles. The transparent proxy means the MUD's telnet/login Just Works through the link. The pure endpoint parser is unit-tested (t207/t208); the wired proxy is wire-smoke covered (`20-descent.sh`).
- **Negative** — no single-sign-on yet: a citizen logs in twice (once to agora, once to the MUD). The proxy holds a forked worker for the whole MUD session (acceptable under fork-per-accept; bounded by the idle timeout). `poll` is invoked via the same raw `syscall(7, …)` convention `net_connect_nb` already uses — an x86_64-Linux assumption that rides along with the existing listener (cross-arch parity is a `lib/net.cyr` task, per [ADR 0001](0001-cross-platform-listener-decoupled-from-agnos.md)).
- **Neutral** — the proxy bypasses agora's telnet state machine while active (by design — transparency requires it); on return, the session resumes at the BBS prompt with its original recv timeout intact. The deferred identity hand-off is the natural next bite and is adjacent to the v2.x *identity continuity* pillar.

## Alternatives considered

- **Full identity hand-off now (two repos).** Add a trusted local-socket / signed-token path to the MUD so an agora citizen lands pre-authenticated. Rejected for 1.4.0: it is a much larger change touching a deliberately-frozen 1.0 MUD surface ([its ADR 0007](../../../cyrius-yeomans-descent/docs/adr/0007-frozen-1.0-surface.md)), and the gateway delivers user value without it. Kept as the explicit next bite.
- **Reuse `MODE_DOOR` / line-buffered feed.** Rejected: a live MUD pushes output asynchronously; a turn-based feed-then-render loop cannot surface server-driven events. The `poll`-multiplexed shuttle is the correct shape (closer to `MODE_CHAT`'s recv-timeout tick than to a door).
- **Launch a separate telnet client per session.** Rejected: spawning an external process per player is heavier and less portable than an in-process socket proxy, and agora already owns the client socket.
- **Operator endpoint via a CLI flag instead of a file.** Rejected for parity with the existing `.policy` / `.admins` operator-config pattern (a file the operator edits), and so the endpoint can change without restarting the server.
