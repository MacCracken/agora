# Getting Started

> **Last Updated**: 2026-05-23 (0.9.1 doc-pass — covers the 0.9.0 surface)

Build agora, run the tests, start the listener, post a message anonymously, then come back authenticated. Linux x86_64 or aarch64 today; macOS / Windows pending `lib/net.cyr` backends.

For the *why* behind any decision below, follow the ADR links — this guide stays prescriptive.

---

## Prerequisites

- **Cyrius toolchain ≥ 6.0.1** (pinned in [`cyrius.cyml`](../../cyrius.cyml)). Install with:

  ```sh
  curl -sSf https://raw.githubusercontent.com/MacCracken/cyrius/main/scripts/install.sh | sh
  ```

  Confirm: `cyrius version` reports `6.0.1` or newer.

- **Linux x86_64 or aarch64.** macOS and Windows follow as cyrius `lib/net.cyr` gains backends ([ADR 0001](../adr/0001-cross-platform-listener-decoupled-from-agnos.md)).
- **A telnet client.** `telnet`, `nc`, or `socat - TCP:host:port` all work; agora speaks RFC 854 + 1143 + 1073 + 1091 + 1184.
- **(Optional)** `openssl` ≥ 3.0 if you want to script telnet authentication — see [Authenticated telnet](#authenticated-telnet) below.

---

## Build

```sh
cd agora
cyrius build src/main.cyr build/agora
```

A clean build at 0.9.0 produces a **~378 KB** static ELF. For a DCE pass (NOPs out unreachable functions in place — same size today, real strip is a v1.x concern):

```sh
CYRIUS_DCE=1 cyrius build src/main.cyr build/agora
```

Live binary size lives in [`docs/development/state.md`](../development/state.md).

---

## Run the tests

```sh
cyrius test src/test.cyr
```

Expect **80 tests, 0 failures** at 0.9.0. The suite covers the IAC parser (t01–t24, RFCs 854 / 1143 / 1073 / 1091 / 1184), post storage + threading (t25–t49), accounts (t50–t63), the From header + per-board policy (t64–t70), and the 0.7.0 audit regressions (t71–t78). t79 + t80 are the 0.8.x audit-followup regressions (keyfile mode bits + board existence).

---

## Start the listener

```sh
./build/agora serve 2323
```

You'll see the bannermanor MOTD render to stderr and the listener parks on port 2323. agora forks one process per accepted connection ([ADR 0007](../adr/0007-fork-per-accept-concurrency.md)) — open as many concurrent telnet sessions as your kernel allows.

Storage defaults to `./agora-data/`. Override with `--store <path>`. Custom MOTD: `--motd <path>` (4 KB ceiling).

```sh
./build/agora serve 2323 --store ./bbs --motd ./motd.txt
```

---

## Default policy: anon-read, auth-post

agora's M6 default is **anonymous reads, authenticated writes**. Unauthenticated CLI / telnet sessions can list and read every board; they cannot `post` or `reply` until they register a key and authenticate ([ADR 0006](../adr/0006-identity-model.md) § Specifics). Operators tighten the read side per board with `.policy` (see [Per-board posting policy](#per-board-posting-policy) below).

The in-session commands (mirroring `help`):

| Command | Effect | Anon? |
|---|---|---|
| `boards` | list main + named boards with post counts | ✅ |
| `enter <name>` | switch to a named board | ✅ existing only |
| `leave` | return to main | ✅ |
| `list` | list post IDs in the current board | ✅ |
| `read <id>` | print a post (with replies) | ✅ |
| `post` | compose; terminate with `.` on a line by itself | ❌ |
| `reply <id>` | compose a reply (auto-prefixes `Re:`) | ❌ |
| `login <handle>` | start a sigil Ed25519 challenge/response | ✅ |
| `whoami` | print bound identity or `anonymous` | ✅ |
| `quit` | close the session | ✅ |

Anonymous sessions trying to `post` or `reply` get `post denied by board policy (admin-only or unregistered)`. Anonymous `enter <newname>` on a board that doesn't exist gets `auth required to create new boards` (0.8.3, audit M4). Connect, run `boards` / `list` / `read 1` to confirm read paths work, then come back authenticated.

---

## Authenticated flow

agora's identity model is Ed25519 challenge/response via sigil ([ADR 0006](../adr/0006-identity-model.md)). The setup is the same for both CLI authoring (`--as <handle>`) and telnet `login <handle>`:

1. Generate a keyfile (32-byte raw seed, mode 0600):

   ```sh
   ./build/agora keygen --key ~/.agora/key
   ```

   agora warns to stderr if it later loads a keyfile whose mode lets group / other read it (0.8.1, audit L1 — doesn't refuse, since containerized deployments may legitimately mount world-readable secrets).

2. Register the keyfile's pubkey under a handle in the store:

   ```sh
   ./build/agora register --handle qix --key ~/.agora/key --store ./bbs
   ./build/agora whoami --key ~/.agora/key --store ./bbs
   # → qix <fp16>
   ```

   Handles are 1–24 bytes of `[a-z0-9_-]`; the fingerprint (`fp16`) is the lowercase hex of the first 8 bytes of `sha256(pubkey)`. Registry lives at `<store>/.users/<fp16>/`.

3. Author a post from the CLI under that handle:

   ```sh
   echo "signed by qix" | ./build/agora post \
     --as qix --key ~/.agora/key --store ./bbs --subject "authored post"
   ./build/agora read 2 --store ./bbs
   # → Subject: authored post
   # → From: qix <fp16>
   # →
   # → signed by qix
   ```

4. Log in over telnet:

   ```
   > login qix
   challenge: <nonce_hex>
   reply with: auth: <128-hex-ed25519-sig over "agora-login:" + challenge>
   ```

   Sign the literal string `agora-login:<nonce_hex>` with the keyfile's Ed25519 seed and reply with `auth: <hex>`. The full scripted flow lives at [`docs/examples/05-telnet-login.sh`](../examples/05-telnet-login.sh) — it wraps the 32-byte seed in a PKCS#8 envelope so `openssl pkeyutl -sign -rawin` accepts it, then drives the wire from bash.

   Server validates with `ed25519_verify` (sigil); on success the session binds `g_session_fp` + `g_session_handle` and subsequent posts pick up the `From:` header automatically.

   The parked challenge expires after 30 seconds (0.7.0 audit M6 — independent of the 60 s slowloris socket timeout).

---

## Per-board posting policy

Each board can carry a `.policy` file (`open` / `known` / `admin`) and an `.admins` file (one handle per line) ([ADR 0006](../adr/0006-identity-model.md) § Specifics, M6-F):

| Mode | Anon | Registered | Admin |
|---|---|---|---|
| `open` (default) | ❌ | ✅ | ✅ |
| `known` | ❌ | ✅ | ✅ |
| `admin` | ❌ | ❌ | ✅ |

Anonymous is denied across every mode at M6 (auth-post default; per-board anon override is queued as a future ADR per [ADR 0006](../adr/0006-identity-model.md) § Negative). `open` and `known` are functionally identical today — `known` exists to carry future semantics (cross-store federation / web-of-trust per the v2.x roadmap). No `.policy` file → `open` (backwards-compat with 0.5.x stores). The operator edits the files directly today (`agora policy set` / `agora admins {add,rm,list}` are queued as future CLI verbs).

```sh
mkdir -p ./bbs/announce
echo admin > ./bbs/announce/.policy
echo qix >  ./bbs/announce/.admins
```

`announce` is now admin-only; non-`qix` registered users get `post denied by board policy`; anonymous sessions get `auth required`.

Anonymous sessions cannot create new boards over telnet (0.8.3, audit M4) — `enter <newname>` returns `auth required to create new boards`.

---

## Concurrency

agora forks per connection ([ADR 0007](../adr/0007-fork-per-accept-concurrency.md)). To confirm:

```sh
# In one terminal:
./build/agora serve 2323 --store ./bbs

# In three more:
nc localhost 2323
nc localhost 2323
nc localhost 2323
```

Each session sees its own banner, its own `g_session_*` slots, and its own bump-allocator arena. A non-blocking `waitpid(-1, NULL, WNOHANG)` loop at the top of every accept iteration drains zombies. See [`docs/examples/04-concurrent-smoke.py`](../examples/04-concurrent-smoke.py) for a scripted version.

---

## Where to go next

- [`docs/development/roadmap.md`](../development/roadmap.md) — what's shipped, what's next, what's deferred.
- [`docs/development/state.md`](../development/state.md) — live state snapshot (version / size / in-flight slot / boot guide).
- [`docs/examples/`](../examples/) — runnable smoke scripts for each major surface.
- [`docs/adr/`](../adr/) — eight architecture decisions (cross-platform listener / post storage / RFC-822 headers / board layout / Reply-To threading / identity model / fork concurrency / PostHeaders ABI).
- [`CLAUDE.md`](../../CLAUDE.md) — durable agent / contributor process rules.
- [`CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.
