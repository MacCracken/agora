# agora — Benchmarks

> **Last Updated**: 2026-05-23 (M1 close — first baseline) | **Host**: Linux x86_64 (workstation; Cyrius 6.0.1) | **Regen**: `cyrius bench benches/bench_telnet.bcyr`

Top-level performance baseline for the agora telnet protocol layer. Numbers measured with `lib/bench.cyr`'s `bench_run_batch` (10 rounds × 10,000 iterations per measurement; per-iteration averages with min/max bracketing). Each `work_*` function in [`benches/bench_telnet.bcyr`](benches/bench_telnet.bcyr) resets only the parser fields it touches between iterations — the `TelnetState` itself is allocated once outside the timed region.

Numbers are per-iteration (one full exchange-of-interest), not per-byte.

## M1 close — 2026-05-23

| Benchmark | Avg | Min | Max | What's exercised |
|---|---:|---:|---:|---|
| **`telnet/plain_byte`** | **10 ns** | 9 ns | 13 ns | Single ASCII byte through the ST_DATA path. Hot path for in-band data. |
| **`telnet/iac_untracked`** | **63 ns** | 62 ns | 64 ns | `IAC WILL OPT_STATUS` — 3 bytes through ST_DATA → ST_IAC → ST_OPT → naive-refuse, with a 3-byte `IAC DONT STATUS` reply queued. |
| **`telnet/iac_tracked_agree`** | **73 ns** | 72 ns | 75 ns | `IAC WILL SUPPRESS_GO_AHEAD` — 3 bytes through the Q machine's Q_NO → Q_YES agree path, with a 3-byte `IAC DO SGA` reply queued. |
| **`telnet/subneg_naws`** | **97 ns** | 97 ns | 98 ns | Full NAWS subnegotiation (9 bytes: `IAC SB NAWS w_hi w_lo h_hi h_lo IAC SE`) plus `telnet_handle_sb` decoding the 4-byte payload into `TS_TERM_COLS`/`TS_TERM_ROWS`. |
| **`telnet/announce_salvo`** | **132 ns** | 129 ns | 143 ns | One-time-per-connection: four `ts_emit_iac3` calls plus four `opt_set_us`/`opt_set_him` writes. Issued from `telnet_announce` after `accept()`. |

## Derived throughput (M1 close)

| Workload shape | Theoretical max throughput |
|---|---:|
| Pure ASCII data through the parser | ~100 M bytes/s |
| IAC option exchanges (untracked, naive-refuse) | ~16 M exchanges/s |
| IAC option exchanges (tracked, Q-agree) | ~14 M exchanges/s |
| NAWS subneg roundtrips | ~10 M subnegs/s |

A real BBS connection mixes ~99% plain bytes with sporadic IAC events. Even sustained-IAC adversarial load (every byte triggers a full exchange) caps below 16M ops/s per core — orders of magnitude above any plausible BBS load.

## Notes on what's NOT in this baseline

- **Accept-loop rate** — `cmd_serve` opens `sock_accept` in a blocking loop. Benching it requires a paired client process and is deferred to its own dedicated bench file (`benches/bench_accept.bcyr` or a shell harness). Plausible target: > 10k accepts/sec on this host based on raw socket cost.
- **End-to-end echo latency** — wall-clock from client send to client receive over `127.0.0.1`. Requires a paired process; meaningful target is < 1 ms p99.
- **Memory pressure** — every connection allocates ~1.4 KB of `TelnetState` plus its buffers (256 + 512 + 256 + 256 + 256 + 256 B). 1,000 concurrent connections = ~1.4 MB. Not exercised here.
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
