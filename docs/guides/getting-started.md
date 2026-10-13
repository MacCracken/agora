# Getting Started

> **Last Updated**: 2026-05-23 (0.9.1 doc-pass — covers the 0.9.0 surface)

Build agora, run the tests, start the listener, browse anonymously, then come back authenticated to post. Linux x86_64 or aarch64 today; macOS / Windows pending `lib/net.cyr` backends.

For the *why* behind any decision below, follow the ADR links — this guide stays prescriptive.

---

## Prerequisites

- **Cyrius toolchain — the version pinned in [`cyrius.cyml`](../../cyrius.cyml) `[package].cyrius`** (pinned in [`cyrius.cyml`](../../cyrius.cyml)). Install with:

  ```sh
  curl -sSf https://raw.githubusercontent.com/MacCracken/cyrius/main/scripts/install.sh | sh
  ```

  Confirm: `cyrius --version` matches the pin (a mismatch prints a drift warning).

- **Linux x86_64 or aarch64**, or **AGNOS** (build with `cyrius build --agnos`, served under mirshi with `--net-listen-any`; shipping since 1.5.0 — note agnos always uses the poll serve model, having no `fork`). macOS and Windows follow as cyrius `lib/net.cyr` gains backends ([ADR 0001](../adr/0001-cross-platform-listener-decoupled-from-agnos.md)).
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
cyrius test
```

Expect **0 failures** (the suite was 80 tests at 0.9.0 and has grown with every cut; `docs/development/state.md` carries the current count). The suite covers the IAC parser (t01–t24, RFCs 854 / 1143 / 1073 / 1091 / 1184), post storage + threading (t25–t49), accounts (t50–t63), the From header + per-board policy (t64–t70), and the 0.7.0 audit regressions (t71–t78). t79 + t80 are the 0.8.x audit-followup regressions (keyfile mode bits + board existence).

---

## Start the listener

```sh
./build/agora serve 2323
```

agora prints a few status lines and the listener parks on port 2323; each telnet client is greeted with the ANSI MOTD. agora serves with one of two models, chosen at startup ([ADR 0023](../adr/0023-dual-serve-model.md)). On Linux the default is **fork-per-connection** ([ADR 0007](../adr/0007-fork-per-accept-concurrency.md)) — open as many concurrent sessions as your kernel allows. Set `AGORA_SERVE=poll` for the single-process multiplex, which serves up to 64 sessions from one process and is the only model on AGNOS. **Ctrl-C (or `kill`) shuts either model down cleanly since 1.7.0** — sessions are told, drained and closed rather than cut off, and since 1.8.1 a player's in-game progress is saved on the way out (as it is on any disconnect).

Storage defaults to `./agora-data/`. Override with `--store <path>`. Custom MOTD: `--motd <path>` (4 KB ceiling).

```sh
./build/agora serve 2323 --store ./bbs --motd ./motd.txt
```

---

## Default policy: anon-read, auth-post

agora's M6 default is **anonymous reads, authenticated writes**. Unauthenticated CLI / telnet sessions can list and read every board; they cannot `post` or `reply` until they register a key and authenticate ([ADR 0006](../adr/0006-identity-model.md) § Specifics). Operators set per-board policy with `agora policy` (see [Per-board policy](#per-board-policy) below): since 1.9.2 a board can be members-only (`known` — login to read), open to anonymous posts (`anon`), or admin-only.

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

Anonymous sessions trying to `post` or `reply` get `auth required — run 'login <handle>' first`. Anonymous `enter <newname>` on a board that doesn't exist gets `auth required to create new boards` (0.8.3, audit M4). Connect, run `boards` / `list` / `read 1` to confirm read paths work, then come back authenticated.

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

   Handles are 1–32 bytes of `[a-z0-9_-]` (not `anonymous` / `system` / `admin`); the fingerprint (`fp16`) is the lowercase hex of the first 8 bytes of `sha256(pubkey)`. Registry lives at `<store>/.users/<fp16>/`.

3. Author a post from the CLI under that handle:

   ```sh
   echo "signed by qix" | ./build/agora post \
     --as qix --key ~/.agora/key --store ./bbs --subject "authored post"
   ./build/agora read 2 --store ./bbs
   # → From: qix <fp16>
   # → Subject: authored post
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

## Per-board policy

Each board can carry a `.policy` file and an `.admins` file ([ADR 0028](../adr/0028-board-policy-modes.md),
amending [ADR 0006](../adr/0006-identity-model.md)). Since 1.9.2 every mode means something:

| Mode | Who reads (`enter` / `list` / `read`) | Who posts |
|---|---|---|
| `open` (default) | anyone | any logged-in user |
| `known` | **members only** — a logged-in user | a logged-in user |
| `anon` | anyone | **anyone, anonymous sessions included** |
| `admin` | anyone | only the board's `.admins` |

No `.policy` file → `open`. A `.policy` that cannot be read, or that names no mode, **fails closed**: the
board is admin-only for posting and members-only for reading, and the server warns on stderr. `anon` is an
explicit opt-in — use it for a feedback or guest board, not for a busy one.

Set them with the operator CLI (or edit the files — the format is unchanged):

```sh
agora policy set announce admin --store ./bbs     # creates the board if needed
agora admins add announce qix --store ./bbs       # writes qix's FINGERPRINT
agora admins list announce --store ./bbs
agora policy get announce --store ./bbs
agora policy set feedback anon --store ./bbs
agora policy set staff known --store ./bbs
```

`announce` is now admin-only: non-`qix` registered users get `post denied by board policy`, anonymous
sessions `auth required`. **`.admins` entries are fingerprints** when written by `agora admins add`: the
right follows the key, so if qix's key re-registers under another handle and someone else takes `qix`, the
newcomer is not an admin. A line that is a handle still works, but carries that risk. Anonymous sessions see
a `known` board as `members only` in `boards` and cannot enter it.

Anonymous sessions cannot create new boards over telnet (0.8.3, audit M4) — `enter <newname>` returns `auth required to create new boards`.

---

## Concurrency

agora has two serve models ([ADR 0023](../adr/0023-dual-serve-model.md)): on Linux the default forks per connection ([ADR 0007](../adr/0007-fork-per-accept-concurrency.md)), capped at 64 live connections since 1.8.1; `AGORA_SERVE=poll` (the only model on AGNOS) multiplexes up to 64 sessions in one process and gives each session one command per sweep, so one client's pipelined burst cannot stall the rest. To confirm the fork model:

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
- [`docs/adr/`](../adr/) — the architecture decision records (0001–0024) — the listener, storage and identity foundations, the door / universe / chat subsystems, the wager and decode primitives, the Descent gateway, the dual serve model and the allocator decisions.
- [`CLAUDE.md`](../../CLAUDE.md) — durable agent / contributor process rules.
- [`CHANGELOG.md`](../../CHANGELOG.md) — per-tag chronology.
