# Examples

Runnable smoke scripts for each major agora surface. Each example begins with a top-of-file comment explaining *why* it exists (per [first-party-documentation § Examples](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#examples)) and what it should output on success.

All examples assume:

- agora is built at `./build/agora` (`cyrius build src/main.cyr build/agora`).
- A scratch store at `./bbs/` (delete between runs for a clean slate: `rm -rf ./bbs`).
- The serve examples use port **2323** (unprivileged; no root needed).

Run them in order from a fresh checkout — later examples reuse identity files from earlier ones.

| # | Script | Surface | Reads / writes |
|---|---|---|---|
| 01 | [`01-build-and-test.sh`](01-build-and-test.sh) | Build + 80-test suite | none |
| 02 | [`02-register-and-post.sh`](02-register-and-post.sh) | M6: keygen / register / post `--as` (the first writeable flow) | `./bbs/`, `./keys/qix` |
| 03 | [`03-anonymous-read.sh`](03-anonymous-read.sh) | M6 default "anon-read, auth-post" — reads succeed, anon post denied | `./bbs/` |
| 04 | [`04-concurrent-smoke.py`](04-concurrent-smoke.py) | ADR 0007 fork-per-conn: 3 simultaneous telnet sessions | `./bbs/` |
| 05 | [`05-telnet-login.sh`](05-telnet-login.sh) | M6 challenge/response over telnet (openssl-signed) | `./bbs/`, `./keys/qix` |
| 06 | [`06-board-policy.sh`](06-board-policy.sh) | M6-F `.policy` / `.admins` (open / known / admin) | `./bbs/` |
| 07 | [`07-play-door.sh`](07-play-door.sh) | 1.1.0 door games: plays Smuggler's Ledger / Port Authority / The Handler over telnet (practice mode) — ADR 0009 | none |
| 08 | [`08-world-concurrency.sh`](08-world-concurrency.sh) | 1.2.0 world-transaction framework: N processes hammer one shared world, assert no lost updates — ADR 0010 | `/tmp/agora-world-smoke-$$` |
| 09 | [`09-universe-port.sh`](09-universe-port.sh) | 1.2.0 bite 2 PA shared galaxy: two players `play port universe` — shared map, exclusive planet ownership across sessions, world persists, login-gated — ADR 0010 | `./bbs/`, `./keys/` |

Demo handles use three-letter old-arcade-game names (`qix`, `pac`, `zax`) to avoid colliding with real handles.

---

## What these are not

- **Not a test suite** — `cyrius test src/test.cyr` is the conformance harness (123 tests, t01–t123 as of 1.2.0 bite 1). These scripts exercise the *binary* end-to-end; tests exercise the *units* in isolation.
- **Not benchmarks** — those live in [`benches/bench_telnet.bcyr`](../../benches/bench_telnet.bcyr).
- **Not a tutorial** — the prose tutorial is [`docs/guides/getting-started.md`](../guides/getting-started.md). Read that first if you've never run agora.

## When to add a new example

When a new surface earns its slot, drop a numbered script next to the others. Number monotonically (07, 08, …) — never renumber. If a script becomes obsolete (the surface changed shape), delete the file and free its number; future readers can recover history via git.
