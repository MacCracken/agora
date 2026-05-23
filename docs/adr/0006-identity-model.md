# 0006 — Identity model: sigil Ed25519, `.users/<fp>` per-store, challenge/response login

> **Status**: Accepted
> **Date**: 2026-05-23

## Context

M5 closed at 0.5.0 with a multi-board threaded BBS — but every poster on the wire is anonymous. The post file's `From:` slot is empty; the in-session prompt has no `whoami`; the per-board policy is "anyone who can open the socket can post." This is the entire 0.4.0 / 0.5.0 single-trust-zone shape: works on a LAN with one operator and friends, breaks the moment a second board needs different posting rules ("art is open, ops is admin-only") or any post needs to outlive its anonymous author for accountability.

M6 introduces **identity**. agora gains: a per-user keypair, a wire-side login flow, a session-bound author identity, and a `From:` header on posts. Per-board posting policy ships in the same cycle so the identity is actually load-bearing the day it lands.

Out of scope for M6: **federated identity** (one fingerprint, multiple agora nodes — that's v2.x pillar 1 in [`roadmap-future.md`](../development/roadmap-future.md), and requires the content-addressed-storage graduation to be coherent). Web-of-trust signatures, key revocation lists, and TOFU-pinning prompts are also v2.x — M6 is single-node authentication.

Six load-bearing decisions:

1. **Identity primitive** — what crypto, what shape, what library.
2. **On-disk account storage** — where does per-user metadata live?
3. **Wire login flow** — how does a session prove identity over telnet?
4. **Read-vs-post default policy** — does anonymous use still work?
5. **`From:` header shape** — how is author identity encoded in a post file?
6. **CLI surface** — `whoami`, `--as`, key file location.

### Candidate primitives

- **(A) Sigil Ed25519** — sigil (bundled 3.1.1 in cyrius 6.0.1's lib snapshot; standalone repo tip at 3.4.3) already ships `ed25519_keypair`, `ed25519_sign`, `ed25519_verify`, and a `generate_keypair` wrapper that returns the same 16-hex-char `key_id` shape we'd use for our fingerprint. Zero new deps; matches the AGNOS-wide crypto boundary.
- **(B) Sigil ML-DSA-65** — sigil's PQC option (FIPS 204). Future-proof against quantum but currently gated behind `-D SIGIL_PQC` and 1.2 KB signatures vs Ed25519's 64. Defer until the AGNOS-wide PQC switch.
- **(C) Password hashes** — argon2id over a passphrase + per-user salt. No keypair = no portable identity story for v2.x pillar 1 (a password is not a portable identity). Also a worse UX over telnet (typing a passphrase on every login vs `sigil sign` once).

### Candidate storage layouts

- **(X) `<store>/.users/<fingerprint>/`** — per-user directory mirrors per-board layout. `.lock` precedent (ADR 0004) shows dot-prefixed names dodge `parse_post_id`'s `.txt` filter for free.
- **(Y) Fully sigil-managed (`~/.sigil/...`)** — agora holds only the fingerprint per session; sigil owns the keystore. Smaller agora surface but per-deployment user lists are now scattered across per-user home directories — awkward for a server with N users.
- **(Z) `<store>/users.cyml` sidecar** — one file mapping fingerprint → handle. Two-file invariant (sidecar + per-board posts) — the same anti-pattern ADRs 0002 / 0003 / 0004 / 0005 rejected at every prior layer.

### Candidate login flows

- **(p) Challenge/response over Ed25519** — server sends a random nonce; client signs `"agora-login:" + nonce`; server verifies sig against the registered pubkey. Replay-resistant (nonce is single-use); no secret crosses the wire.
- **(q) Password-on-wire** — client sends fingerprint + password; server hashes and compares. Cleartext-on-wire over telnet is a non-starter (no TLS at M6) — first packet sniffer wins.
- **(r) HMAC over a shared secret** — server and client share a pre-distributed secret; client HMACs the nonce. Worse than (p) — shared secrets don't graduate to v2.x pillar 1 (portable identity), and key distribution becomes its own problem.

### Candidate default policies

- **(P1) Anon read, auth post** — connect anonymous; `read` / `list` / `boards` / `enter` work without login; `post` / `reply` require an authenticated session. Matches lurker tradition (Usenet, Reddit, every BBS since 1979).
- **(P2) Auth required for everything** — first action after MOTD must be `login`. Stronger admission control; breaks lurker UX and forces every casual visitor to have a sigil key.
- **(P3) Operator config** — both modes available; operator picks at startup. More code, more test paths.

## Decision

**(A) sigil Ed25519** for the identity primitive, **(X) `<store>/.users/<fingerprint>/`** for storage, **(p) challenge/response** for the wire flow, **(P1) anon read + auth post** as the default policy. **`From: <handle> <fingerprint16>`** header on authenticated posts; missing `From:` continues to mean anonymous (backwards-compat with M5 posts). CLI grows `agora whoami [--key <path>]` and `agora post --as <handle> [--key <path>]`.

### Specifics

**Fingerprint**:
- `fingerprint = hex(sha256(public_key))[0:16]` — 16 hex chars = 64 bits of fingerprint. Sigil's `generate_keypair` uses the same 16-hex shape (over the pubkey bytes directly, not SHA-256); we use SHA-256-then-truncate so the fingerprint is robust to any future pubkey-format change (e.g. graduation to ML-DSA pubkeys). Collision space at 2^64 is comfortable for v1.0's expected ~10s of users per deployment; if a future deployment scales past 10k users a per-deployment ADR amendment can lengthen the fingerprint.
- Stored, displayed, and used in `From:` as lowercase hex.

**Account storage layout**:
```
<store>/.users/<fp16>/
  public_key.bin     # 32 bytes raw Ed25519 pubkey (NOT the secret seed)
  handle             # 1-32 bytes UTF-8; same alphabet as board names (a-z 0-9 - _; first char letter/digit)
  created.iso8601    # registration timestamp via chrono.iso8601_now()
```
- Dot-prefix on `.users/` dodges `parse_post_id` filter (precedent: `.lock` in ADR 0004).
- Handle alphabet matches board names (reusing `board_name_valid` semantics with a different reserved set: `anonymous`, `system`, `admin` reserved; `main` is not — board names and handles are different namespaces).
- Server holds only public keys; **secret keys never touch the server**. Lost the keyfile = lost the identity, by design (no recovery flow; no shared-secret backdoor).

**Wire login flow**:
1. Client (in `MODE_COMMAND`, anonymous) sends `login <handle>` over the wire.
2. Server looks up `<store>/.users/<fp>/handle == <handle>`. If no match, replies `unknown user` and stays in `MODE_COMMAND` anonymous.
3. If match, server generates a 32-byte cryptographic random nonce via `lib/io.cyr` `/dev/urandom`, hex-encodes it (64 chars), replies `challenge: <64-hex>`. Server parks `(fp, nonce, deadline)` in per-connection state, transitions session to `MODE_LOGIN_AWAIT_SIG`.
4. Client computes `sig = ed25519_sign(secret_key, "agora-login:" + nonce_hex)`, sends `auth: <128-hex-sig>`.
5. Server hex-decodes sig, fetches `public_key.bin` for the parked fingerprint, calls `ed25519_verify(pk, "agora-login:" + nonce, 76 bytes, sig)`. On verify pass: session binds `(fp, handle)`, sends `welcome, <handle>`, transitions to `MODE_COMMAND` authenticated. On verify fail or `auth:` not received within deadline (default 30 s): session reverts to `MODE_COMMAND` anonymous, sends `login failed`.
6. **Nonces are single-use** — the parked nonce is cleared on every `auth:` attempt (pass or fail). A second `auth:` for the same login requires a new `login` round.
7. **Domain-separated signing input** — the `"agora-login:"` prefix prevents an attacker tricking the user into signing a payload that happens to be a valid nonce in some other agora protocol message. Pattern from sigil's signed-artifact convention.

**Posting policy**:
- Default: **anon read, auth post**. `read` / `list` / `boards` / `enter` / `leave` / `help` / `whoami` / `login` / `quit` run from anonymous sessions. `post` / `reply` reply with `auth required` and abort if the session is anonymous.
- Per-board operator config (M6-F): each board may carry `<store>/<board>/.policy` (one of `open` / `known` / `admin`). `open` = current default (authenticated user can post). `known` = post requires the user to be registered (any registered handle). `admin` = post requires the user's handle to be in `<store>/<board>/.admins` (one handle per line). Missing `.policy` file means `open`. Main board defaults to `open` if no `<store>/.policy` exists.
- **No anonymous-post mode at M6 first cut.** A future ADR may add `anon-allowed` to `<store>/<board>/.policy` if a real deployment wants a no-account-required board (e.g., a "feedback" board where the operator explicitly accepts unauthenticated posts).

**`From:` header on posts**:
```
Subject: <text>
Date: <iso8601>
From: <handle> <fp16>
Reply-To: <id>           (optional, ADR 0005)

<body>
```
- **Format**: `From: <handle> <space> <fp16-hex>\r\n`. Two-token value (handle + fingerprint, space-separated) is the simplest disambiguator: handles can change (future ADR may add handle-rename); the fingerprint is the durable identity.
- **Missing `From:` = anonymous**. Same backwards-compat shape as Subject / Date / Reply-To in ADRs 0003 / 0005 — old posts (M5 era) lack From, render as `anonymous` in `list` / `read`.
- **Renaming for `list`**: `list` now shows `<id>  [<handle>]  <subject>` (was `<id>  <subject>`). Anonymous posts render `[anon]`.
- **`read <id>`** prepends `From: <handle> <fp16>` (or `From: anonymous`) before the Subject in the rendered output.

**Key file format**:
- `~/.agora/key` default, override via `--key <path>` flag on any verb that needs a key.
- Format: 96 bytes raw — 32-byte seed || 64-byte secret_key (the same `secret_key` shape sigil's `ed25519_keypair` returns). No header, no checksum, no PEM — keep it dead-simple, secret material never touches the wire.
- File mode 0600 enforced at write time; warn-and-abort if the file is world / group readable at read time.
- `agora keygen` writes a new keyfile; refuses to overwrite an existing one.

**CLI surface**:
- `agora keygen [--key <path>] [--handle <handle>]` — generates a fresh Ed25519 keypair via sigil, writes the keyfile, prints `created <handle> <fp16>`. With `--handle`, also writes `<store>/.users/<fp>/` registration (requires `--store`); without `--handle`, key exists but isn't registered with any agora deployment.
- `agora register --key <path> --handle <handle> [--store <path>]` — registers an existing keyfile's pubkey under a handle in the given store. Refuses if the handle is taken.
- `agora whoami [--key <path>]` — decodes the keyfile, prints `<handle?> <fp16>`. Handle resolution requires `--store` to look up the registration; without `--store`, prints just the fingerprint.
- `agora post --as <handle> [--key <path>] [--store <path>] [...]` — op-testing flag. Same effect as wire `login` + `post`; writes `From: <handle> <fp16>` to the post file.
- Telnet `whoami` — replies `<handle> <fp16>` (authenticated session) or `anonymous` (default).

**Per-connection session state additions**:
- `g_session_fp[17]` — NUL-terminated fingerprint hex (empty cstring = anonymous).
- `g_session_handle[33]` — NUL-terminated handle (empty cstring = anonymous).
- `g_login_nonce[65]` — NUL-terminated parked challenge nonce hex (empty cstring = no login in flight).
- `g_login_deadline` — monotonic-time deadline for the parked challenge.

## Consequences

**Positive**:

- **Single crypto boundary.** sigil owns every byte of Ed25519 in the AGNOS ecosystem; agora doesn't re-implement signing. When sigil ships ML-DSA-65 outside the `-D SIGIL_PQC` gate, agora migrates by swapping the call site, not the protocol.
- **No secret material on the wire.** Telnet has no TLS at M6; passwords-on-the-wire would be trivially sniffable. Signature-over-nonce leaks nothing to a passive observer (the nonce is server-public; the sig binds the nonce to the pubkey; the secret stays on the client).
- **Free backwards compat with 0.5.0 stores.** A 0.5.0 deployment that upgrades reads its existing posts as anonymous (missing `From:`). No migration step.
- **Free backwards compat with the M5 wire commands.** The new login flow is an additive command (`login` + `auth:`); existing `boards` / `enter` / `read` / `list` / `post` / `reply` work unchanged for anonymous sessions modulo the policy gate on `post` / `reply`.
- **Filesystem-shaped account store.** `ls <store>/.users/` shows registered users. `cat <store>/.users/<fp>/handle` shows the handle. Same operator-tooling story ADR 0002 / 0004 leaned on.
- **Lurker UX preserved.** Casual visitors `telnet agora.lan 2323` and read everything; auth is only the toll booth for posting.
- **Fingerprint-as-durable-identity** survives handle renames. If we ship `agora rename <new-handle>` in M6+ polish, posts retain their original `From:` line (which records the handle-at-post-time); the fingerprint is the identity, the handle is the display name.
- **Domain-separated signing input** ("agora-login:" prefix) prevents the sigil keypair from being tricked into signing payloads for other protocols. Standard cryptographic hygiene.
- **Graduates cleanly into v2.x pillar 1.** Federated identity replaces the per-store registration with a globally-resolvable fingerprint (Nostr-shape); the `From: <handle> <fp16>` header already records the durable part. The handle becomes the user-chosen display; the fingerprint is the network-wide name.

**Negative**:

- **Lost keyfile = lost identity.** No recovery flow; no shared-secret backdoor. A user who deletes `~/.agora/key` cannot post as the old fingerprint again, even with the same handle (the server holds the pubkey; only the matching secret can sign the nonce). Users who care about continuity should back up the keyfile.
- **Single-node identity at M6.** Same fingerprint on two agora deployments requires the user to copy the keyfile to both and register the same handle on both. Federated identity (one fingerprint, N nodes auto-resolve) is v2.x pillar 1.
- **64-bit fingerprint space.** 2^64 is fine for ~10s of users per deployment, fragile at 10k+ (birthday collision at ~4 billion). A deployment-level ADR can extend the fingerprint to 32 hex chars (128-bit) when needed; the on-disk shape is forward-compatible (longer strings just truncate to 16 chars for display, full string for crypto).
- **Telnet has no TLS at M6.** The signature flow protects the secret key, but the post content + handle + fp travel cleartext over the wire. A passive observer can read every post and see who wrote it. This is the BBS-history shape (telnet was never confidential), but operators running on hostile networks should either tunnel agora over SSH or wait for v2.x for a wire-encryption pillar (not currently on the roadmap-future).
- **Per-board policy adds a fourth side-channel file** in the board layout (`.lock`, `.policy`, `.admins`, plus the M6 `.users/<fp>/` per-store). Operators reading `ls <store>/<board>/` see more dotfiles. Mitigated by the dot-prefix convention being load-bearing for all storage-private files.
- **No anonymous-post mode at M6.** Boards that want "anyone with the socket can post" require a future ADR; today's `open` policy is "any registered user can post."
- **Handle squatting.** First-come-first-served handle registration means a user who grabs `linus` blocks the actual linus from registering. Operator-side `agora unregister <handle>` is implementable but deferred — the v2.x pillar 1 web-of-trust would solve this properly.

**Neutral**:

- **Server holds public keys** (not secrets); a compromised server leaks the pubkey registry (which is public-by-design — pubkeys are the verifier input, not the secret). Worst-case server compromise lets the attacker forge `<store>/.users/<fp>/handle` to grab handles, but cannot impersonate the original user (still need the secret key to sign the nonce).
- **The `From:` header field name** is already canonical in RFC 5322 § 3.6.2 — "From: address". We're overloading it for `<handle> <fingerprint>`. Defensible: our posts are not email; the field reads naturally as "from this user"; the two-token shape is distinct from any email-address syntax.
- **The 30-second login deadline** is generous for a human-paced login (`sigil sign` is sub-second) but tight enough that a stale challenge doesn't sit on the server indefinitely. Tuneable; not a load-bearing decision.

## Alternatives considered

**(B) Sigil ML-DSA-65 for the primitive.** Rejected at M6 first cut. PQC-future-proof but gated behind `-D SIGIL_PQC` (cyrius preprocessor cap), 1.2 KB signatures vs Ed25519's 64-byte sigs (heavier on the wire). The AGNOS-wide PQC graduation will move agora together with the rest of the ecosystem — agora doesn't need to lead.

**(C) Password hashes (argon2id) instead of keypairs.** Rejected. (1) Password-on-wire over telnet has no defensible TLS-free flow — challenge-response with a passphrase-derived key just relocates the same key-management problem with worse UX. (2) Passwords are not portable identities — v2.x pillar 1 needs a public key, not a hash. (3) Sigil already ships the Ed25519 primitives; passwords would be a parallel mechanism we'd have to maintain.

**(Y) Fully sigil-managed account storage (`~/.sigil/...`).** Rejected. Conceptually clean (sigil owns identity), but per-deployment user lists scatter across per-user home directories — the operator running `ls <store>/.users/` to see "who can post here?" goes from one shell command to "find every home directory on the server." The server-side view of "registered users" is load-bearing for the per-board policy logic; centralizing it in `<store>/.users/` is the operator-shaped choice.

**(Z) `<store>/users.cyml` sidecar.** Rejected. Two-file invariant — exactly the pattern ADRs 0002 / 0003 / 0004 / 0005 rejected at every prior layer. Per-user directory keeps the registration self-contained and inspectable; the slight extra inode pressure is negligible at v1.0 scale.

**(q) Password on the wire.** Rejected. Cleartext over telnet — first packet sniffer wins. Not negotiable.

**(r) Pre-shared-secret HMAC.** Rejected. Worse than (p) on every axis: doesn't graduate to portable identity, requires key distribution out-of-band, server-side leak compromises every user (vs Ed25519 where pubkeys can leak harmlessly).

**(P2) Auth required for everything.** Rejected as default. Breaks lurker UX; forces every casual visitor to have a sigil key before they can read what's on the BBS. Operators who want this can configure it via the per-board `.policy` files (set every board to `known` and the visitor can't even `read` until they `login` — well, `read` doesn't check policy at M6 first cut; if a real operator demands read-gating, that's a future ADR with a fourth policy mode).

**(P3) Operator-configurable read-vs-post policy at startup.** Rejected as M6 first cut. Adds operator-config surface, doubled test paths, and a doc burden for a feature with no current consumer asking for it. Per-board posting policy (M6-F) covers the posting axis; read-gating earns its own ADR when a real operator hits the case.

**Federated identity at M6.** Rejected — v2.x pillar 1 in [`roadmap-future.md`](../development/roadmap-future.md). Requires the content-addressed-storage graduation (pillar 2) to be coherent (a post's `From:` field must resolve to the same identity across nodes). Premature at M6.

**Web-of-trust at M6.** Rejected — also v2.x pillar 1. M6 is single-trust-root (the operator's keyring). WoT signatures, trust scoring, and revocation lists are post-1.0.

**Storing the secret key on the server (encrypted at rest with a user passphrase).** Rejected. Reintroduces password-on-wire (the passphrase to decrypt the server-held secret). Defeats the whole point of asymmetric crypto. Users hold their secrets; servers hold the public ledger.

**`In-Reply-To` style overloading for `From:`** (e.g., a separate header `Author:` to dodge the RFC 5322 semantic mismatch). Rejected — same reasoning as ADR 0005's `Reply-To` overload: posts are not email, the user-facing reading is natural, and the field name reads correctly in `head post.txt`.
