# Examples

Runnable smoke scripts for each major agora surface. Each example begins with a top-of-file comment explaining *why* it exists (per [first-party-documentation § Examples](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#examples)) and what it should output on success.

## Running them — `run.sh`

```sh
CYRIUS_DCE=1 cyrius build src/main.cyr build/agora
docs/examples/run.sh                      # every smoke, under both serve models
docs/examples/run.sh --model poll 26 27   # just these, poll only
docs/examples/run.sh --fast --skip 01     # skip the slow halves (26's idle wait, 31's fork wait)
```

[`run.sh`](run.sh) (1.8.2) knows what each script needs: a clean `./bbs` and `./keys`, a freshly registered
`qix` (03, 05, 06, 11–13, 15, 24, 26, 27), or a server it must start itself under the requested model (the
client-only 04, 05, 23, 25, 26, 27). Scripts that start their own server inherit `AGORA_SERVE`, so
`--model fork|poll|both` covers them too; 24 and 28–33 drive both models internally and run once. 20 skips
itself unless the sibling `../cyrius-yeomans-descent` repo is present. Logs land in `build/smoke-logs/`.
**CI runs the whole set on every push, once per serve model.** The runner refuses to start if `./bbs` or
`./keys` already exist, since the scripts create and delete them (`--force` to override).

(Until 1.8.2 there was no runner, and the README's old "run them in order" contract did not hold: 09, 10,
18, 19 and 20 delete `./bbs ./keys` on exit, and the client-only scripts each needed a server started by hand
under a model named only in their header. Every release from 1.6.7 to 1.8.1 was verified with a throwaway
harness — the reason smoke 20's breakage went unnoticed for four releases.)

Running one by hand still works: each script's header says what it needs. Defaults: `./build/agora`,
a scratch store at `./bbs/`, port 2323 (11–15 use 2324–2328; 24, 28–33 pick their own).

| # | Script | Surface | Reads / writes |
|---|---|---|---|
| 01 | [`01-build-and-test.sh`](01-build-and-test.sh) | Build + unit-test suite (count in `docs/development/state.md`) | none |
| 02 | [`02-register-and-post.sh`](02-register-and-post.sh) | M6: keygen / register / post `--as` (the first writeable flow) | `./bbs/`, `./keys/qix` |
| 03 | [`03-anonymous-read.sh`](03-anonymous-read.sh) | M6 default "anon-read, auth-post" — reads succeed, anon post denied | `./bbs/` |
| 04 | [`04-concurrent-smoke.py`](04-concurrent-smoke.py) | ADR 0007 fork-per-conn: 3 simultaneous telnet sessions | `./bbs/` |
| 05 | [`05-telnet-login.sh`](05-telnet-login.sh) | M6 challenge/response over telnet (openssl-signed) | `./bbs/`, `./keys/qix` |
| 06 | [`06-board-policy.sh`](06-board-policy.sh) | M6-F `.policy` / `.admins` (open / known / admin) | `./bbs/` |
| 07 | [`07-play-door.sh`](07-play-door.sh) | 1.1.0 door games: plays Smuggler's Ledger / Port Authority / The Handler over telnet (practice mode) — ADR 0009 | none |
| 08 | [`08-world-concurrency.sh`](08-world-concurrency.sh) | 1.2.0 world-transaction framework: N processes hammer one shared world, assert no lost updates — ADR 0010 | `/tmp/agora-world-smoke-$$` |
| 09 | [`09-universe-port.sh`](09-universe-port.sh) | 1.2.0 bite 2 PA shared galaxy: two players `play port universe` — shared map, exclusive planet ownership across sessions, world persists, login-gated — ADR 0010 | `./bbs/`, `./keys/` |
| 10 | [`10-leaderboard.sh`](10-leaderboard.sh) | 1.2.0 bite 5 cross-game leaderboards: finish a Port Authority run, then `scores port` lists it — ADR 0010 | `./bbs/`, `./keys/` |
| 11 | [`11-chat.sh`](11-chat.sh) | 1.3.0 chat area: two sessions in a channel, live-tail by sequence number, no cross-talk — ADR 0011 | `./bbs/`, `./keys/` |
| 12 | [`12-eliza.sh`](12-eliza.sh) | 1.3.0 Eliza: the `play eliza` door decomposes "I am sad"; the private `/eliza` couch answers off the room transcript — ADR 0011 | `./bbs/`, `./keys/qix` |
| 13 | [`13-parry.sh`](13-parry.sh) | 1.3.1 PARRY: the `play parry` door is calm then a Mafia "flare" launches the delusion; private `/parry` off the transcript — ADR 0012 | `./bbs/`, `./keys/qix` |
| 14 | [`14-quest.sh`](14-quest.sh) | 1.3.2 QUEST: the `play quest` practice flow — town hub render, Bank screen, forest hunt, a fight resolves — ADR 0009 | none |
| 15 | [`15-jabberwacky.sh`](15-jabberwacky.sh) | 1.3.3 Jabberwacky: the door learns a pair mid-session and replays it; `/jabberwacky` answers privately; a `solo` pair survives a disconnect (per-user persistence) — ADR 0015 | `./bbs/`, `./keys/qix` |
| 16 | [`16-casino.sh`](16-casino.sh) | 1.3.5: the shared wager module across three doors — the Port Authority cantina Dabo Wheel, the Smuggler dice and the QUEST card table — ADR 0013 | `./bbs/`, `./keys/qix` |
| 17 | [`17-olympiad.sh`](17-olympiad.sh) | 1.3.6: the Olympiad stable sim — a chariot race on the `compete()` primitive, the same weights pricing the book — ADR 0016 | `./bbs/`, `./keys/qix` |
| 18 | [`18-ashes.sh`](18-ashes.sh) | 1.3.7: Ashes of Empire — login-gated; orders and diplomacy mutate ONE shared map across separate sessions — ADR 0014 | `./bbs/`, `./keys/` |
| 19 | [`19-ashes-concurrency.sh`](19-ashes-concurrency.sh) | 1.3.7: Ashes under concurrent callers — no lost updates, no colliding foundings — ADR 0014 | `./bbs/`, `./keys/` |
| 20 | [`20-descent.sh`](20-descent.sh) | 1.4.0: the Descent gateway — "No Descent linked." without config; with it, a logged-in citizen is proxied into the real sibling MUD (needs `../cyrius-yeomans-descent`) — ADR 0017 | `./bbs/`, `./keys/qix` |
| 21 | [`21-decode.sh`](21-decode.sh) | 1.4.1 / 1.4.2: Decode — Numbers (Mastermind) and Words (Wordle) on one engine — ADR 0018 | none |
| 22 | [`22-handler-decrypt.sh`](22-handler-decrypt.sh) | 1.4.3: The Handler's decrypt lever — spend a dispatch point to break a cable's cipher — ADR 0019 | none |
| 23 | [`23-sigpipe-survival.py`](23-sigpipe-survival.py) | 1.6.2: SIGPIPE — rude disconnects close one session, not the server (has teeth only under `AGORA_SERVE=poll`; kills an unpatched server at exit 141) | none |
| 24 | [`24-descent-serve-models.sh`](24-descent-serve-models.sh) | 1.6.2: the Descent byte-proxy forwards client→MUD under BOTH serve models, asserted against a fake MUD that logs what it receives | `./bbs/`, `./keys/qix` |
| 25 | [`25-door-state-churn.py`](25-door-state-churn.py) | 1.6.3: the DD_FREE release paths under churn — enter/quit across all nine practice doors, quit-then-enter alternation (freed blocks recycled straight into the next game), and repeated disconnect-mid-game so `session_release` frees a live slot | none |
| 26 | [`26-iac-and-idle.py`](26-iac-and-idle.py) | 1.6.4: IAC (0xFF) doubled on egress + dropped at ingress (RFC 854), and `IAC NOP` keepalives no longer hold a session slot (~80s; `--fast` skips the idle half) | `./bbs/` |
| 27 | [`27-audit-lows.py`](27-audit-lows.py) | 1.6.5: audit LOWs — over-long `--store` refused, BEL/BS/DEL dropped from a stored post, and echo gated correctly (kept for non-negotiating clients, suppressed after `IAC DONT ECHO`) | `./bbs/`, `./keys/qix` |
| 28 | [`28-clean-shutdown.py`](28-clean-shutdown.py) | 1.7.0 (roadmap N1): SIGINT/SIGTERM shut both serve models down cleanly (exit 0, not 143/130), a connected poll client is told before its socket closes, and **fork children do not inherit the parent's blocked signal mask** — the regression that made every connection process unkillable. Self-contained: starts and signals its own servers. | `/tmp/agora-shutdown-smoke-$$` |
| 29 | [`29-egress-sanitize.py`](29-egress-sanitize.py) | 1.8.0 (ADR 0024): stored text reaches readers with every terminal control neutralized — C1 controls (raw and UTF-8-encoded) in a wire post, ESC/BEL in a CLI post, malformed UTF-8 — each shown as `?`, while UTF-8 text, TAB and CR LF arrive byte-for-byte and the post on disk is untouched. Both serve models, plus `agora read` / `agora list` on stdout. Self-contained; `AGORA_BIN=` A/Bs an older build (1.7.1 fails 44 checks). | `/tmp/agora-sanitize-smoke-$$` |
| 30 | [`30-audit-1.8.1.py`](30-audit-1.8.1.py) | 1.8.1 (audit): `.policy` / `.admins` fail closed; CLI 64 KB body refused; `serve --store` without a value exits; poll fairness under 4 pipelining readers; a >128 KB `list` arrives whole under poll; a dropped connection saves door progress and a second session cannot play the same save (both serve models); a public key copied over another user's does not log in as them. Self-contained; `AGORA_BIN=` A/Bs an older build (1.8.0 fails all 11 checks). | `/tmp/agora-audit181-smoke-$$` |
| 31 | [`31-slow-reader.py`](31-slow-reader.py) | 1.8.2: the slow-reader close path (1.6.3 / 1.7.0 / 1.8.1) pinned — a client that asks for ~12 MB and reads nothing is disconnected: under poll promptly with a bystander unaffected, under fork within one send timeout (watched via the connection's child, since reading would un-stall the writer). Self-contained; `--fast` skips the ~70 s fork half; a 1.8.0 build fails the fork half, and so did 1.8.2's first cut (186 s — CHANGELOG [1.8.2] § Fixed). | `/tmp/agora-slowreader-smoke-$$` |
| 32 | [`32-store-hardening.py`](32-store-hardening.py) | 1.9.0 (audit 1.8.1 I11, ADR 0025): store opens refuse FIFOs and symlinks — a FIFO named `2.txt` must not hang `list` / `read` (under poll it hung the whole server, and a new client was never greeted), and `3.txt -> <a file outside the store>` must not be served as a post. Both serve models; the symlink checks run first so each fails on its own merits. A 1.8.2 build fails 9 of 10. **1.9.1 § B**: a FIFO in place of `.users/` must not hang `login` (a 1.9.0 poll server hangs). Self-contained. | `/tmp/agora-storehard-smoke-$$` |
| 33 | [`33-reply-index.py`](33-reply-index.py) | 1.9.1 (ADR 0027): the first smoke to check a `Replies:` line — a hand-written board indexed at server start, a CLI `--reply-to` listed at once, a reply added by hand NOT listed under a complete index (the scan no longer runs), and the rebuild after deleting `.replies/`. Both serve models; a 1.9.0 build fails the index checks. Self-contained (own key + store). | `/tmp/agora-replyidx-smoke-$$` |

Demo handles use three-letter old-arcade-game names (`qix`, `pac`, `zax`) to avoid colliding with real handles.

---

## What these are not

- **Not a test suite** — `cyrius test` (tests/agora.tcyr + tests/serve.tcyr) is the conformance harness, and `cyrius fuzz fuzz/telnet_iac.fcyr` is the IAC-parser fuzz harness (new at 1.7.0; both run in CI and at release). These scripts exercise the *binary* end-to-end; tests exercise the *units* in isolation.
- **Not benchmarks** — those live in [`benches/bench_telnet.bcyr`](../../benches/bench_telnet.bcyr).
- **Not a tutorial** — the prose tutorial is [`docs/guides/getting-started.md`](../guides/getting-started.md). Read that first if you've never run agora.

## When to add a new example

When a new surface earns its slot, drop a numbered script next to the others. Number monotonically (07, 08, …) — never renumber. If a script becomes obsolete (the surface changed shape), delete the file and free its number; future readers can recover history via git.
