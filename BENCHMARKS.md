# agora — Benchmarks

> **Last Updated**: 2026-10-13 (1.10.1: § Word wrap — `benches/bench_term.bcyr` and `read` / `list` end to end. 1.10.0: § Parser. 2026-10-12: 1.8.1 re-run, six runs, A/B'd same-day against the 1.8.0 tree: unchanged except `subneg_naws`, whose bench body changed — see §. Prior: 1.8.0 re-run on cyrius **6.7.9**, A/B against the 1.7.1 tree on cyrius 6.6.2 — within noise of each other) | **Host**: Linux x86_64 (workstation; benched on Cyrius 6.0.1 at the 0.9.2 baseline, 6.4.78 at 1.6.1, 6.5.33 at 1.6.7) | **Regen**: `cyrius bench benches/bench_telnet.bcyr`

Top-level performance baseline for the agora telnet protocol layer. Numbers measured with `lib/bench.cyr`'s `bench_run_batch` (10 rounds × 10,000 iterations per measurement; per-iteration averages with min/max bracketing). Each `work_*` function in [`benches/bench_telnet.bcyr`](benches/bench_telnet.bcyr) resets only the parser fields it touches between iterations — the `TelnetState` itself is allocated once outside the timed region.

Numbers are per-iteration (one full exchange-of-interest), not per-byte.

## 0.9.2 closeout — 2026-05-23 (pre-1.0 baseline)

| Benchmark | Avg | Min | Max | What's exercised |
|---|---:|---:|---:|---|
| **`telnet/plain_byte`** | **10 ns** | 9 ns | 15 ns | Single ASCII byte through the ST_DATA path. Hot path for in-band data. |
| **`telnet/iac_untracked`** | **64 ns** | 63 ns | 65 ns | `IAC WILL OPT_STATUS` — 3 bytes through ST_DATA → ST_IAC → ST_OPT → naive-refuse, with a 3-byte `IAC DONT STATUS` reply queued. |
| **`telnet/iac_tracked_agree`** | **75 ns** | 73 ns | 87 ns | `IAC WILL SUPPRESS_GO_AHEAD` — 3 bytes through the Q machine's Q_NO → Q_YES agree path, with a 3-byte `IAC DO SGA` reply queued. |
| **`telnet/subneg_naws`** | **99 ns** | 98 ns | 100 ns | Full NAWS subnegotiation (9 bytes: `IAC SB NAWS w_hi w_lo h_hi h_lo IAC SE`) plus `telnet_handle_sb` decoding the 4-byte payload into `TS_TERM_COLS`/`TS_TERM_ROWS`. |
| **`telnet/announce_salvo`** | **134 ns** | 131 ns | 141 ns | One-time-per-connection: four `ts_emit_iac3` calls plus four `opt_set_us`/`opt_set_him` writes. Issued from `telnet_announce` after `accept()`. |

**All numbers within noise of the M1-close baseline.** M2 (ANSI MOTD), M5 (post storage / boards / threads), M6 (sigil auth / per-board policy), 0.7.0 (CLI input validation), 0.8.0 (fork-per-accept in `cmd_serve_on`), 0.8.1 (keyfile fstat), 0.8.3 (board-create gate), 0.9.0 (PostHeaders struct) and 0.9.1 (doc-pass, no code) are all off-hot-path additions. The auth surface adds one `ed25519_verify` call per login (sub-millisecond, one-shot per session) that is not in this telnet-parser baseline; a future `bench_auth.bcyr` earns its slot post-1.0 alongside accept-rate + end-to-end latency.

## Per-release history

| Tag | plain_byte | iac_untracked | iac_tracked_agree | subneg_naws | announce_salvo |
|---|---:|---:|---:|---:|---:|
| 0.2.0 (M1 close) | 10 ns | 63 ns | 73 ns | 97 ns | 132 ns |
| 0.5.0 (M5 close) | 11 ns | 63 ns | 73 ns | 107 ns | 132 ns |
| 0.6.0 (M6 close) | 10 ns | 64 ns | 74 ns | 99 ns | 132 ns |
| **0.9.2 (1.0 closeout)** | **10 ns** | **64 ns** | **75 ns** | **99 ns** | **134 ns** |
| **1.6.1 (toolchain 6.4.78)** | **9–11 ns** | **63 ns** | **72–75 ns** | **100–101 ns** | **124 ns** |
| **1.6.7 (toolchain 6.5.33)** † | **8–9 ns** | **61–69 ns** | **71–75 ns** | **98–111 ns** | **122–132 ns** |
| **1.7.0 (toolchain 6.5.34)** † | **9–10 ns** | **58–68 ns** | **68–76 ns** | **95–100 ns** | **121–128 ns** |
| 1.7.1 (toolchain 6.6.2) ‡ | 10–11 ns | 68–74 ns | 77–89 ns | 110–132 ns | 140–166 ns |
| **1.8.0 (toolchain 6.7.9)** ‡ | **8–14 ns** | **66–86 ns** | **77–89 ns** | **103–116 ns** | **137–142 ns** |
| **1.8.1 (toolchain 6.7.9)** § | **8–9 ns** | **60–62 ns** | **70–74 ns** | **102–103 ns** § | **126–127 ns** |

† **1.6.7 rows are net of a measured clock floor; every earlier row is gross.** cyrius **6.5.19** taught `lib/bench.cyr` to subtract the timer's own overhead. At this suite's `batch_size = 10,000` the correction is **under 1 ns** — inside the ±2 ns these columns have always carried — so the columns remain comparable, but **do not read a 1–2 ns drop across this row as a win**.

(**1.6.7** re-benched on cyrius 6.5.33 over **eight runs**, reported as the observed range with the median in parentheses: `plain_byte` 8–9 (9), `iac_untracked` 61–69 (63), `iac_tracked_agree` 71–75 (73), `subneg_naws` 98–111 (100), `announce_salvo` 122–132 (129). **The four parser paths are within noise of both the 0.9.2 and the 1.6.1 baselines — i.e. unchanged**, which is the expected result: the parser source has not moved since M1. The one real change is `announce_salvo` giving back 1.6.1's −7%: 134 (0.9.2) → 124 (1.6.1) → **~129 (1.6.7)**, roughly back to the pre-6.4.x codegen. Not investigated — it is one-time-per-connection work, ~5 ns on a path that runs once per `accept()`.

§ **1.8.1 `subneg_naws` is not 1:1 with earlier rows.** 1.8.1 accepts a subnegotiation only for an option the client has enabled (RFC 855, audit L20), so the bench now marks NAWS agreed (`opt_set_him`) on every iteration — otherwise it would time the new early rejection. Same-day A/B against a `git archive` of 1.8.0, six runs each: `plain_byte` 8–9 / 8–9, `iac_untracked` 60–62 / 61, `iac_tracked_agree` 70–74 / 71–72, `announce_salvo` 126–127 / 126–127 — **unchanged** — and `subneg_naws` 102–103 vs 94–95 for the old bench body: the extra store in the bench plus the gate's load + compare, on a path that runs once or twice per connection. (Both rows here are ~10% under the 1.8.0 row measured at the 1.8.0 cut, on every path including untouched ones: that is workstation state between sessions, not code.)

‡ **1.7.1 was never benched at its own cut**; this row was measured at the 1.8.0 cut from a `git archive` of the 1.7.1 tree on cyrius 6.6.2, run back to back with the 1.8.0 runs on the same workstation, six runs each.

(**1.8.0** re-benched on cyrius 6.7.9 over **six runs**, range with median in parentheses: `plain_byte` 8–14 (9), `iac_untracked` 66–86 (67.5), `iac_tracked_agree` 77–89 (78), `subneg_naws` 103–116 (106), `announce_salvo` 137–142 (140.5); one run was a high outlier on every path. **Same-day A/B, 1.7.1 on cyrius 6.6.2**: 10–11 (10), 68–74 (68), 77–89 (78.5), 110–132 (112), 140–166 (143). So **6.6.2 → 6.7.9 moves nothing outside noise** (if anything `subneg_naws` 112 → 106 and `announce_salvo` 143 → 140.5 in 1.8.0's favour) — expected, since 1.8.0 does not touch `src/telnet.cyr`. **Both** read ~5–15% above the August 1.7.0 row (e.g. `announce_salvo` 122 → 140, `subneg_naws` 96 → ~106). That gap cannot be attributed from here: it is either the 6.5.34 → 6.6.2 codegen change that 1.7.1 shipped unmeasured, or workstation drift over seven weeks, and no 6.5.x toolchain is installed on this machine to re-run 1.7.0 and tell them apart. Recorded as unattributed, not as a regression of this cut. 1.8.0's new egress sanitizing is off this harness — it runs once per stored string sent, not per parsed byte.)

(**1.7.0** re-benched on cyrius 6.5.34 over **six runs**, range with median in parentheses: `plain_byte` 9–10 (9), `iac_untracked` 58–68 (62), `iac_tracked_agree` 68–76 (71), `subneg_naws` 95–100 (96), `announce_salvo` 121–128 (122). Two paths moved slightly in agora's favour against 1.6.7 — `subneg_naws` 100 → 96 median and `announce_salvo` 129 → 122 — and the other three are indistinguishable. **This is codegen, not agora**: 1.7.0 added clean shutdown, atomic writes and a tx-overflow flag, none of which the parser touches, and `src/telnet.cyr` is unchanged in this cut. Both moved figures sit inside the range the 1.6.7 row already spans, so the honest reading is "no regression, possibly a small win" rather than a claimed improvement. N4's `fuzz/telnet_iac.fcyr` drives the same functions but is not a benchmark and is not timed here.)

**Recorded because it nearly went in wrong**: the first two runs of this cut read 8/61/71/98/122 and would have published as "every path at or below 1.6.1, best numbers ever". Six further runs showed that pair was the low tail, not the centre. Two runs is not a sample. The same correction retires a second claim this cut briefly held: an earlier pass measured 104 / 131 ns under a compiler built from a *dirty* cyrius working tree, and restoring the snapshot appeared to move those to 98 / 122. **With eight runs in hand, 104 and 131 both sit inside the ordinary range, so that was noise, not the dirty toolchain.** The dirty snapshot was real and mattered for **binary size** — 2,225,840 vs 2,010,320 B, a difference no amount of re-running changes — but there is **no measured evidence it affected speed**, and this file should not imply otherwise. See CHANGELOG [1.6.7] § Verification notes.)

(**1.6.1** is the first re-bench since the 1.0 closeout — the 1.1.x–1.6.0 cycles were all off-hot-path [door games, chat, world transactions, the poll serve model] and the parser itself is untouched since M1. Two dedicated runs on cyrius **6.4.78** [after the 6.2.8 → 6.4.32 → 6.4.78 pin moves]: `plain_byte` 9/11 ns, `iac_untracked` 63/63 ns, `iac_tracked_agree` 72/75 ns, `subneg_naws` 100/101 ns, `announce_salvo` 125/124 ns. The four parser paths are within ±2 ns of the 0.9.2 baseline — i.e. unchanged. `announce_salvo` is the one real move: **134 → ~124 ns (−7%)**, reproduced across three runs including one under `cyrius audit` [123 ns], and attributable to 6.4.x codegen since the function is byte-for-byte the same source. Both runs on the same workstation class as the baseline.)

(0.3.0 / 0.4.0 weren't benched separately — M2 / M5-partial cycles didn't touch the parser. 0.7.0–0.9.1 likewise — every release between M6 and 0.9.2 added off-hot-path code (CLI input validation, fork-per-accept in `cmd_serve_on`, keyfile fstat, sigil-version diff, board-create gate, PostHeaders struct, doc-pass) — confirmed by the 0.9.2 re-run landing within ±2 ns of the M6 baseline. The first 0.9.2 run showed `announce_salvo` at 163 ns avg with min=131 ns — re-run stabilized at 134 ns; the elevated avg was system noise.)

## Derived throughput (M1 close)

| Workload shape | Theoretical max throughput |
|---|---:|
| Pure ASCII data through the parser | ~100 M bytes/s |
| IAC option exchanges (untracked, naive-refuse) | ~16 M exchanges/s |
| IAC option exchanges (tracked, Q-agree) | ~14 M exchanges/s |
| NAWS subneg roundtrips | ~10 M subnegs/s |

A real BBS connection mixes ~99% plain bytes with sporadic IAC events. Even sustained-IAC adversarial load (every byte triggers a full exchange) caps below 16M ops/s per core — orders of magnitude above any plausible BBS load.

## Parser — 1.10.0

`cyrius bench benches/bench_telnet.bcyr`, the same harness, after the RFC 854 / 1184 conformance work (ADR 0029):

| Benchmark | 1.9.2 | 1.10.0 |
|---|---:|---:|
| `plain_byte` | 9 ns | 9 ns |
| `iac_untracked` | 65 ns | ~66 ns |
| `iac_tracked_agree` | 75 ns | ~75 ns |
| `subneg_naws` | 105 ns | ~104 ns |
| `announce_salvo` | 132 ns | ~168 ns — five options now (DO LINEMODE), 33.6 ns each as before |

A first cut that staged every three-byte reply through a buffer to make it atomic cost ~10 ns per negotiation
(74 / 85 ns); a room check before pushing does the same job at the old cost.

## Word wrap — 1.10.1

`cyrius bench benches/bench_term.bcyr`: the cost of `term_wrap_chunk` ([ADR 0030](docs/adr/0030-terminal-aware-output.md)),
which every door frame, `list` row, post body and chat line goes through once a client has reported a window
width. A line with no TAB whose bytes fit the row is copied without being measured, which is most of what a
door or an ordinary post holds.

| Benchmark | First cut | 1.10.1 | What's exercised |
|---|---:|---:|---|
| `term/frame_fits_80` | 8.7 µs | **2.9 µs** | A Smuggler-sized door frame (18 rows, ~600 B, SGR), 80 columns: nothing breaks |
| `term/frame_wrap_40` | 8.9 µs | **3.8 µs** | The same frame at 40 columns: its long rows break |
| `term/body4k_fits_80` | 63 µs | **19 µs** | A 4 KB body of 60-column lines at 80 columns |
| `term/body4k_wrap_40` | 64 µs | **40 µs** | A 4 KB paragraph at 40 columns (~10 ns/byte) |

"First cut" measured a function call per character. 1.10.1 inlines printable ASCII and adds the whole-line fast
path.

End to end, `read` of a 60 KB post (poll-server CPU per command, 150 reads, from `/proc/<pid>/stat`):

| Post shape | No NAWS | 80 columns | 40 columns |
|---|---:|---:|---:|
| 70-column lines | 1.0 ms | 1.3 ms | 2.1 ms |
| 950-column paragraphs | 1.0 ms | 1.7 ms | 1.7 ms |

Without NAWS, `send_wrapped` takes `send_text`'s path: the same bytes at the same cost. A fork child measures
1.6 → 1.7 ms wall for the paragraph post: it sends in 2 KB chunks instead of 504-byte ones, so it makes fewer
`write(2)` calls.

**`list` got cheaper**: each row is composed and sent once (it was seven sends). Under fork every send is a
`write(2)`, so a 300-post `list` went from **16.1 ms to 4.3 ms** wall (median of 40), with or without NAWS.
Under poll the sends only fill the queue: ~23.2 ms either way, inside one 20 ms sweep.

## Serve-level baselines — 1.8.2 (first measured)

`benches/serve-bench.py` (1.8.2) — the accept-rate half of CLAUDE.md § P(-1) step 2 that was asked for since
0.2.0 and never taken, per-session memory, world-lock contention and the reply scan. Workstation, Linux x86_64, ext4 on
`/dev/sda2`, `CYRIUS_DCE=1` build, three runs each (world lock: five), medians with the runs in parentheses.

| Measurement | `AGORA_SERVE=fork` | `AGORA_SERVE=poll` |
|---|---:|---:|
| accept → greeting → close, **sequential** | **4,077 conn/s** (4,091 / 4,077 / 4,008) | **50 conn/s** (50 / 50 / 50) |
| … **8 concurrent** connectors | **11,431 conn/s** (11,723 / 11,210 / 11,431) | **520 conn/s** (548 / 513 / 520) |
| resident memory per idle, greeted session (THP off) | **62.0 KB** PSS per child (66 / 62 / 62), 32 sessions | **12.6 KB** server RSS growth (12.6 ×3), 64 sessions |

- **Poll's accept rate is the sweep's sleep, not the work.** Sequential connections land at exactly one per
  20 ms sweep (`POLL_MS`): the loop paces itself with a fixed `sleep_ms(20)` rather than waiting in
  `poll(2)` for readiness, so a new connection waits out the rest of the sleep. Concurrent connectors are
  accepted ~10 per sweep. Irrelevant at human pace (a 20 ms greeting delay), but it is the first
  measurement behind roadmap § 1.11.0's epoll row: a readiness wait would remove the floor.
- **Fork costs ~5× the memory per session** — a process per connection (~62 KB PSS of private pages per
  child) against a pooled slot whose 128 KB tx queue and 64 KB compose buffer are only touched when used.
- **Method (found at 1.9.0): fork PSS depends on the binary's filesystem.** The same build measures **54 KB**
  per child run from tmpfs (`/tmp`) and **62 KB** from ext4 — file-backed text and data pages fault in
  differently; private dirty memory is identical. Run every A/B build from the same filesystem (the 1.9.0
  numbers were briefly misread as a 12 KB regression this way).

| Concurrent world writers (ADR 0010 `flock` → read → write temp → fsync → rename), 200 transactions each | txn/s |
|---|---:|
| 1 | **525** (521 / 523 / 525 / 525 / 525) |
| 2 | **525** (534 / 524 / 525 / 519 / 534) |
| 4 | **520** (91 / 510 / 524 / 520 / 522) |
| 8 | **496** (484 / 496 / 521 / 522 / 458) |
| 16 | **487** (516 / 487 / 462 / 465 / 493) |

- **The world lock is fsync-bound, not contention-bound.** Throughput is flat at ~520 transactions/s
  (≈1.9 ms each — one fsync on this disk) from one writer to eight, and gives back only ~7% at sixteen. Every
  run's final count was exact: **no lost update at any concurrency.** The occasional slow run (91 at four
  writers; a 52 and a 214 in an earlier sample) is disk-latency spikes, not the lock. **ADR 0010 / 0014's
  "measure before refining" gate therefore stays closed**: per-sector or per-territory locks would remove
  contention the system does not have, and buy lock-ordering hazards; the ceiling is the durability write,
  ~520 universe-door lines per second for the whole server. (The bench world is 8 bytes; Ashes' 3,048-byte
  map adds one page to each write, which cannot move a ~1.9 ms fsync-bound transaction materially —
  inferred, not separately measured.)

| `read 1` on a board of N one-KB posts (fork, so no poll-sweep wait; 1 in 10 posts a reply) | ms per read |
|---|---:|
| 500 posts | **3.39** (3.43 / 3.35 / 3.39) |
| 2,000 posts | **12.96** (13.33 / 12.96 / 12.85) |
| 4,096 posts | **27.67** (27.67 / 27.86 / 27.13) |

- **The reply scan is linear at ~6.7 µs per post** (ADR 0005 scan-on-read: open, 2 KB header read, close,
  for every post on the board). Imperceptible on a few hundred posts, tens of milliseconds past two
  thousand — and under poll that time is the whole server's, one `read` per session per sweep since 1.8.1's
  line budget. This is the measurement roadmap § 1.9.1's index-vs-scan decision was waiting on.
- **1.9.0: ~0.5 µs more per post** — every store open now `fstat`s the descriptor to refuse a non-regular
  file (ADR 0025). Interleaved A/B on one machine, 1.8.2 → 1.9.0: **3.38 → 3.71 ms** at 500 posts,
  **13.1 → 14.2 ms** at 2,000, **27.3 → 29.2 ms** at 4,096 (load average 4–6 during the run, so the absolute
  numbers sit a little above the 1.8.2 table; the A/B is what holds).
- **1.9.1 — the reply index (ADR 0027) ends the scan.** `read` now opens one index file and verifies each
  listed reply; the bench times `read 2` (no replies) beside `read 1` (a tenth of the board replies to it).
  Interleaved A/B, load average < 1:

  | Board | `read 2` (no replies), 1.9.0 → 1.9.1 | `read 1` (n/10 replies), 1.9.0 → 1.9.1 |
  |---|---:|---:|
  | 500 posts | 2.83 → **0.18 ms** | 3.73 → **0.49 ms** |
  | 2,000 posts | 10.99 → **0.18 ms** | 14.11 → **1.30 ms** |
  | 4,096 posts | 23.74 → **0.18 ms** | 29.39 → **2.46 ms** |

  Flat in board size; ~5.6 µs per listed reply (its verification read). Part of the `read 1` win is the
  `Replies:` line itself: it went out one `write(2)` per id under fork (~5.6 ms for 409 ids) and is now composed
  in 2 KB pieces — the bytes unchanged.
- **Found by this bench and fixed in 1.8.2: a ~40 ms Nagle stall on every multi-part response under
  fork.** The first run read a flat ~41 ms per `read` at every board size: a fork worker writes a response
  as several small sends, and Nagle held each one after the first until the client's delayed (~40 ms) ACK.
  With the client acknowledging immediately (`TCP_QUICKACK`) the same read took 2.6 ms. agora now sets
  `TCP_NODELAY` on every accepted socket; the table above is after the fix (500 posts: 41.0 → 3.4 ms).
  Poll was barely affected — it drains a session's queued output in one write — but sets it too.

| `login <unknown handle>` against N registered users (fork) | 1.8.2 (scan) | 1.9.0 (handle index) | first start, 1.9.0 |
|---|---:|---:|---:|
| 300 users | 1.78 ms (1.78 / 1.71 / 2.02) | **0.16 ms** (0.16 / 0.15 / 0.16) | 301 ms (vs 251) |
| 3,000 users | 16.98 ms (17.62 / 16.98 / 16.56) | **0.16 ms** (0.16 / 0.18 / 0.16) | 552 ms (vs 251) |

- **1.9.0 — an unknown handle is one failed open** (ADR 0026): `.users/.by-handle/<handle>` is absent and
  `.complete` vouches for the index. Before, every `login` read every user's `handle` file and a miss —
  the attacker's choice — could never stop early: linear, ~5.7 µs per user. "First start" is
  start-to-listening on a store that predates the index (the one-time build, in a child process: one
  claim per user, then one `sync()`); later starts check `.complete` and nothing else. The start figures
  include the bench's fixed 0.2 s settle and 50 ms connect polling.
- Allocator gate, same release: a poll server on a 300-post, 300-user store grew **0 KB** across 3,000
  pipelined `login`s, 300 `list`s and 2,000 `read`s (VmRSS and VmData before and after).

Regenerate: `benches/serve-bench.py all` (`accept`, `memory`, `world`, `reply`, `login` individually;
`--runs N`; `AGORA_BIN=` to A/B a build).

## Notes on what's NOT in this baseline

- **End-to-end echo latency** — wall-clock from client send to client receive over `127.0.0.1`. Requires a paired process; meaningful target is < 1 ms p99.
- **Memory pressure (parser)** — each telnet parser draws ~1.7 KB of heap (a 128 B `TelnetState` plus tx 256 + sb 512 + opt_us 256 + opt_him 256 + term_type 257). Under fork that is per child; under poll it is **per slot, allocated once for all 64 and reused** ([ADR 0023](docs/adr/0023-dual-serve-model.md)). Whole-session memory is measured above (1.8.2).
- **DCE-built variants** — all numbers above are `cyrius bench` defaults (non-DCE). The release path is `CYRIUS_DCE=1 cyrius build` which should shave the parser code path slightly via dead-call elimination but not change the hot paths measured.

## Regeneration

```sh
cyrius bench benches/bench_telnet.bcyr      # parser (this table)
cyrius bench benches/bench_term.bcyr        # word wrap (§ Word wrap — 1.10.1)
benches/serve-bench.py all                  # accept rate, per-session memory, world lock, reply scan, login
```

For ongoing tracking across releases, append the output to `bench-history.csv` (not yet scaffolded — earns a slot at the v1.0 close-out alongside any other ongoing perf surfaces). The cyrius repo's `scripts/bench-history.sh` is the reference auto-gen pattern for when this file outgrows hand-maintenance.

## Cross-references

- [`benches/bench_telnet.bcyr`](benches/bench_telnet.bcyr) — the source of these numbers.
- [`benches/bench_term.bcyr`](benches/bench_term.bcyr) — the word-wrap numbers (1.10.1).
- [`docs/development/state.md`](docs/development/state.md) — current version + binary size + in-flight slot.
- [first-party-documentation § Benchmarks and Performance Docs](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#benchmarks-and-performance-docs) — convention for `BENCHMARKS.md` (root-level summary) vs. `docs/development/performance.md` (prose) vs. `docs/benchmarks.md` (history).
