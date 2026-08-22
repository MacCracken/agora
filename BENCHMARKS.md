# agora — Benchmarks

> **Last Updated**: 2026-08-22 (1.7.0 re-run on cyrius **6.5.34**; 1.6.7's 6.5.33 row kept for comparison. All four parser paths remain within noise of the 0.9.2 baseline — the parser source is untouched since M1 — and `subneg_naws` + `announce_salvo` each recovered a few ns against 1.6.7) | **Host**: Linux x86_64 (workstation; benched on Cyrius 6.0.1 at the 0.9.2 baseline, 6.4.78 at 1.6.1, 6.5.33 at 1.6.7) | **Regen**: `cyrius bench benches/bench_telnet.bcyr`

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

† **1.6.7 rows are net of a measured clock floor; every earlier row is gross.** cyrius **6.5.19** taught `lib/bench.cyr` to subtract the timer's own overhead. At this suite's `batch_size = 10,000` the correction is **under 1 ns** — inside the ±2 ns these columns have always carried — so the columns remain comparable, but **do not read a 1–2 ns drop across this row as a win**.

(**1.6.7** re-benched on cyrius 6.5.33 over **eight runs**, reported as the observed range with the median in parentheses: `plain_byte` 8–9 (9), `iac_untracked` 61–69 (63), `iac_tracked_agree` 71–75 (73), `subneg_naws` 98–111 (100), `announce_salvo` 122–132 (129). **The four parser paths are within noise of both the 0.9.2 and the 1.6.1 baselines — i.e. unchanged**, which is the expected result: the parser source has not moved since M1. The one real change is `announce_salvo` giving back 1.6.1's −7%: 134 (0.9.2) → 124 (1.6.1) → **~129 (1.6.7)**, roughly back to the pre-6.4.x codegen. Not investigated — it is one-time-per-connection work, ~5 ns on a path that runs once per `accept()`.

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

## Notes on what's NOT in this baseline

- **Accept-loop rate** — not benched for either serve model. Since 1.7.0 `AGORA_SERVE=fork` (the Linux default) waits in `poll(2)` over {listener, signalfd} on a non-blocking listener rather than blocking in `accept`; `AGORA_SERVE=poll` drains accepts non-blocking once per ~20 ms sweep. Benching it requires a paired client process and is deferred to its own dedicated bench file (`benches/bench_accept.bcyr` or a shell harness). Plausible target: > 10k accepts/sec on this host based on raw socket cost.
- **End-to-end echo latency** — wall-clock from client send to client receive over `127.0.0.1`. Requires a paired process; meaningful target is < 1 ms p99.
- **Memory pressure** — each telnet parser draws ~1.7 KB of heap (a 128 B `TelnetState` plus tx 256 + sb 512 + opt_us 256 + opt_him 256 + term_type 257). Under fork that is per child; under poll it is **per slot, allocated once for all 64 and reused** ([ADR 0023](docs/adr/0023-dual-serve-model.md)), so the poll model's parser memory is bounded at ~107 KB regardless of churn. Not exercised here — per-session memory has never been benchmarked, which is a roadmap item.
- **DCE-built variants** — all numbers above are `cyrius bench` defaults (non-DCE). The release path is `CYRIUS_DCE=1 cyrius build` which should shave the parser code path slightly via dead-call elimination but not change the hot paths measured.

## Regeneration

```sh
cyrius bench benches/bench_telnet.bcyr
```

For ongoing tracking across releases, append the output to `bench-history.csv` (not yet scaffolded — earns a slot at the v1.0 close-out alongside any other ongoing perf surfaces). The cyrius repo's `scripts/bench-history.sh` is the reference auto-gen pattern for when this file outgrows hand-maintenance.

## Cross-references

- [`benches/bench_telnet.bcyr`](benches/bench_telnet.bcyr) — the source of these numbers.
- [`docs/development/state.md`](docs/development/state.md) — current version + binary size + in-flight slot.
- [first-party-documentation § Benchmarks and Performance Docs](https://github.com/MacCracken/agnosticos/blob/main/docs/development/planning/first-party-documentation.md#benchmarks-and-performance-docs) — convention for `BENCHMARKS.md` (root-level summary) vs. `docs/development/performance.md` (prose) vs. `docs/benchmarks.md` (history).
