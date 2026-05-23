# 0001 — Cross-platform telnet listener, decoupled from AGNOS kernel work

> **Status**: Accepted
> **Date**: 2026-05-23

## Context

The original v0.1.0 scaffold framed M1 (telnet listener) as gated on **agnos 1.32.2 closing the DHCP gate** with `tcp_listen(23)` end-to-end-validated on the archaemenid iron NUC. As of 2026-05-23, agnos 1.32.2 is still in flight — Attempt 95 was falsified on iron with a DHCP OFFER timeout (r8169 driver post-reset hardware-filter regression; carry-forward fixes in progress). Pinning agora's M1 directly to the agnos cycle effectively stalls every milestone behind it.

But agora doesn't need to run on AGNOS to be useful. The Cyrius stdlib already exposes a portable socket layer (`lib/net.cyr` — `tcp_socket` / `sock_bind` / `sock_listen` / `sock_accept` / `sock_send` / `sock_recv`) that backs onto Linux syscalls today, and onto macOS / Windows / AGNOS as the stdlib gains backends. Telnet is a transport-layer protocol — it doesn't care which kernel is underneath as long as TCP socket primitives are available.

User direction (2026-05-23 session): *"you can develop a telnet listen regardless of agnos' kernel work right now as this project will be cross-platform."*

## Decision

**The agora telnet listener targets `lib/net.cyr` socket primitives, not agnos-specific kernel calls.** M1 ships on Linux x86_64 + aarch64 today via cyrius stdlib; macOS and Windows follow as `lib/net.cyr` grows platform backends; AGNOS becomes one target among many once its `tcp_listen` is validated on iron.

In scope:
- `src/telnet.cyr` consumes `lib/net.cyr` symbols only.
- `cmd_serve` opens a listener on a configurable port (default 23, override via argv) using `tcp_socket` + `sock_bind` + `sock_listen`.
- Linux is the day-one validation surface; CI smoke-tests against `localhost:<port>`.

Out of scope:
- Direct agnos `tcp_listen` syscall consumption from agora. Future agnos support means cyrius stdlib's `lib/net.cyr` gains an agnos backend — agora's code stays unchanged.
- TLS / WebSocket / HTTP transports. Telnet is the M1 contract.

## Consequences

**Positive**:
- M1 unblocked. We can write and ship RFC 854 + RFC 1184 protocol code today without waiting on the agnos networking arc.
- Wider validation surface — telnet clients on every major OS can smoke the server immediately, surfacing protocol bugs earlier and from more angles than an iron-only validation path.
- Per-platform support comes from `lib/net.cyr` upgrades, not agora changes. The application stays simple; the platform-abstraction concern lives in the stdlib where it belongs.
- AGNOS arrival is a non-event for agora — when `lib/net.cyr`'s agnos backend lands, the same binary serves telnet on agnos with no source change.

**Negative**:
- Until cyrius `lib/net.cyr` gains macOS / Windows backends, "cross-platform" means Linux x86_64 + aarch64 in practice. Other platforms wait on cyrius.
- The original "iron validation on archaemenid LAN" v1.0 criterion in the roadmap is now one of *several* validation surfaces, not the primary gate. Linux validation comes first.
- Telnet over the open internet is plaintext + adversarial-by-default. The cross-platform reach means more potential attack surface earlier — security audit at M6 becomes more important, not less.

**Neutral**:
- The "kernel listener" vs. "stdlib listener" question is now permanently resolved in favor of the stdlib. Future protocols (M5+ persistence over network, M6+ federated auth) follow the same pattern.

## Alternatives considered

**(A) Wait for agnos 1.32.2 to close on iron before any M1 work.** Rejected. Gates the entire roadmap (M1–M6) on an iron debugging cycle whose calendar is uncertain (Attempt 95 just fell over; how many more attempts is unknowable). Even if iron closes tomorrow, the cross-platform path is strictly more general — taking it now costs nothing extra and unlocks the rest of the roadmap.

**(B) Write a private socket abstraction inside agora and target only Linux syscalls directly.** Rejected. Re-implements work `lib/net.cyr` already does, splits the maintenance surface, and forces every new platform backend to live in agora rather than in the shared stdlib. Cross-platform support belongs in the stdlib, full stop.

**(C) Skip M1 entirely and start at M2 (ANSI aesthetic) with a stdin-driven local BBS.** Rejected. The product *is* the multi-user telnet BBS — local-only doesn't validate the wire-protocol design, doesn't exercise the connection state machine, and doesn't catch the protocol-conformance bugs that are M1's whole point. Cutting M1 cuts the project.

**(D) Adopt the `sandhi` HTTP/2 stack instead of raw `lib/net.cyr`.** Rejected for M1. Sandhi is a higher-level transport (HTTP/2 + RPC + service discovery) — using it for telnet would mean wrapping a stream protocol in a request/response abstraction, which fights the protocol shape. Sandhi may be the right fit for a future web-facing companion to agora, but it is not the right shape for telnet itself.
